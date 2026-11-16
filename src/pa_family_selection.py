"""Precision Agriculture family selection using the Step 0 rules."""

import re
from sqlalchemy import and_, or_, func, false

from epo.tipdata.patstat.database.models import (
    TLS201_APPLN,
    TLS202_APPLN_TITLE,
    TLS203_APPLN_ABSTR,
    TLS209_APPLN_IPC,
    TLS224_APPLN_CPC,)


def build_selected_families(db, config):
    """Build the Step 0 selection without executing its notebook."""
    ipr_type = config["patstat"]["ipr_type"]
    year_min = int(config["analysis"]["year_min"])
    year_max = int(config["analysis"]["year_max"])

    if config["analysis"]["family_time_column"] != "earliest_filing_year":
        raise ValueError("Expected earliest_filing_year.")

    if year_min > year_max:
        raise ValueError("Invalid year range.")

    def term_to_regex(term):
        term = term.strip().lower()
        if not term:
            raise ValueError("Search terms cannot be empty.")
        parts = re.split(r"[\s\-_]+", term)
        patterns = [
            re.escape(part).replace(r"\*", r"[a-zA-Z0-9]*")
            for part in parts
            if part]
        return (r"(?:\b|_)" + r"[\s\-_/]+".join(patterns) + r"(?:\b|_)")

    
    def keyword_condition(terms):
        if not terms:
            return false()
        text = func.lower(
            func.concat(
                func.coalesce(TLS202_APPLN_TITLE.appln_title, ""),
                " ", func.coalesce(TLS203_APPLN_ABSTR.appln_abstract, ""),))
        pattern = "|".join(f"(?:{term_to_regex(term)})" for term in terms)
        return func.regexp_contains(text, pattern)

        
    def symbol_condition(column, prefixes):
        if not prefixes:
            return false()
        symbol = func.upper(func.replace(column, " ", ""))
        return or_(*[
            symbol.like(prefix.replace(" ", "").upper() + "%") for prefix in prefixes])

    # Family population and earliest filing year.
    family_year = func.min(TLS201_APPLN.earliest_filing_year)
    family_scope = (
        db.query(
            TLS201_APPLN.docdb_family_id.label("fam_id"),
            family_year.label("family_year"),)
        .filter(
            TLS201_APPLN.ipr_type == ipr_type,
            TLS201_APPLN.docdb_family_id > 0,)
        .group_by(TLS201_APPLN.docdb_family_id)
        .having(family_year.between(year_min, year_max))
        .subquery())

    # Earliest-filed application with a non-empty English abstract.
    english_abstract_available = and_(
        TLS203_APPLN_ABSTR.appln_abstract_lg == "en",
        func.length(func.trim(func.coalesce(TLS203_APPLN_ABSTR.appln_abstract, ""))) > 0,)

    ranked_apps = (
        db.query(
            TLS201_APPLN.docdb_family_id.label("fam_id"),
            TLS201_APPLN.appln_id.label("appln_id"),
            func.row_number().over(
                partition_by=TLS201_APPLN.docdb_family_id,
                order_by=[
                    TLS201_APPLN.appln_filing_date.asc(),
                    TLS201_APPLN.appln_id.asc(),],).label("rn"),)
        .select_from(TLS201_APPLN)
        .join(
            family_scope,
            TLS201_APPLN.docdb_family_id == family_scope.c.fam_id,)
        .join(
            TLS203_APPLN_ABSTR,
            and_(
                TLS201_APPLN.appln_id == TLS203_APPLN_ABSTR.appln_id,
                english_abstract_available,),)
        .filter(
            TLS201_APPLN.ipr_type == ipr_type,
            TLS201_APPLN.appln_filing_date.isnot(None),)
        .subquery())

    representative_apps = (
        db.query(
            ranked_apps.c.fam_id,
            ranked_apps.c.appln_id, )
        .filter(ranked_apps.c.rn == 1)
        .subquery())

    # Keyword evidence from the representative application.
    keywords = config["keywords"]

    keyword_flags = (
        db.query(
            TLS201_APPLN.docdb_family_id.label("fam_id"),
            func.logical_or(
                keyword_condition(keywords["specific"])).label("specific_phrase"),
            func.logical_or(
                keyword_condition(keywords["enabling_technologies"])).label("enabling_technology"),
            func.logical_or(
                keyword_condition(keywords["pa_functions"])).label("pa_function"),)
        .select_from(TLS201_APPLN)
        .join(
            representative_apps,
            TLS201_APPLN.appln_id == representative_apps.c.appln_id,)
        .outerjoin(
            TLS202_APPLN_TITLE,
            and_(
                TLS201_APPLN.appln_id == TLS202_APPLN_TITLE.appln_id,
                TLS202_APPLN_TITLE.appln_title_lg == "en",),)
        .join(
            TLS203_APPLN_ABSTR,
            and_(
                TLS201_APPLN.appln_id == TLS203_APPLN_ABSTR.appln_id,
                TLS203_APPLN_ABSTR.appln_abstract_lg == "en",),)
        .filter(TLS201_APPLN.ipr_type == ipr_type)
        .group_by(TLS201_APPLN.docdb_family_id)
        .subquery())

# CPC/IPC evidence from the same representative application.
    def classification_flags(model, column, settings, prefix):
        return (
            db.query(
                TLS201_APPLN.docdb_family_id.label("fam_id"),
                func.logical_or(
                    symbol_condition(column, settings.get("specific", []))).label(f"specific_{prefix}"),
                func.logical_or(
                    symbol_condition(column, settings["agricultural_context"])).label(f"agricultural_{prefix}"),)
            .select_from(TLS201_APPLN)
            .join(
                representative_apps,
                TLS201_APPLN.appln_id == representative_apps.c.appln_id,)
            .join(model, TLS201_APPLN.appln_id == model.appln_id)
            .filter(TLS201_APPLN.ipr_type == ipr_type)
            .group_by(TLS201_APPLN.docdb_family_id)
            .subquery())

    cpc_flags = classification_flags(
        TLS224_APPLN_CPC,
        TLS224_APPLN_CPC.cpc_class_symbol,
        config["cpc"],"cpc",)

    ipc_flags = classification_flags(
        TLS209_APPLN_IPC,
        TLS209_APPLN_IPC.ipc_class_symbol,
        config["ipc"],"ipc",)

    # Classification exclusions.
    exclusion_queries = []
    for model, column, prefixes in [
        (
            TLS224_APPLN_CPC,
            TLS224_APPLN_CPC.cpc_class_symbol,
            config["cpc"].get("exclude", []),),
        (
            TLS209_APPLN_IPC,
            TLS209_APPLN_IPC.ipc_class_symbol,
            config["ipc"].get("exclude", []),),]:
        if prefixes:
            exclusion_queries.append(
                db.query(representative_apps.c.fam_id.label("fam_id"))
                .select_from(representative_apps)
                .join(
                    model,
                    representative_apps.c.appln_id == model.appln_id,)
                .filter(symbol_condition(column, prefixes)))

    excluded_families = None
    if exclusion_queries:
        query = exclusion_queries[0]
        for additional_query in exclusion_queries[1:]:
            query = query.union(additional_query)
        excluded_families = query.distinct().subquery()

    # Title-only exclusions.
    exclusion_terms = keywords.get("exclusion_terms", [])
    topical_exclusions = None

    if exclusion_terms:
        title_pattern = "|".join(f"(?:{term_to_regex(term)})" for term in exclusion_terms)
        topical_exclusions = (
            db.query(representative_apps.c.fam_id.label("fam_id"))
            .select_from(representative_apps)
            .join(
                TLS202_APPLN_TITLE,
                and_(
                    representative_apps.c.appln_id
                    == TLS202_APPLN_TITLE.appln_id,
                    TLS202_APPLN_TITLE.appln_title_lg == "en",),)
            .filter(
                func.regexp_contains(
                    func.lower(
                        func.coalesce(TLS202_APPLN_TITLE.appln_title, "")
                    ),title_pattern,)).distinct().subquery())

    protected_families = (
        db.query(representative_apps.c.fam_id.label("fam_id"))
        .select_from(representative_apps)
        .join(
            TLS224_APPLN_CPC,
            representative_apps.c.appln_id == TLS224_APPLN_CPC.appln_id,)
        .filter(
            symbol_condition(
                TLS224_APPLN_CPC.cpc_class_symbol,
                ["A01B79/005"],)).distinct().subquery())

    # Combine evidence and preserve the original route definitions.
    flags = (
        db.query(
            family_scope.c.fam_id,
            family_scope.c.family_year,
            func.coalesce(
                keyword_flags.c.specific_phrase, False).label("specific_phrase"),
            func.coalesce(
                keyword_flags.c.enabling_technology, False).label("enabling_technology"),
            func.coalesce(
                keyword_flags.c.pa_function, False).label("pa_function"),
            func.coalesce(
                cpc_flags.c.specific_cpc, False).label("specific_cpc"),
            func.coalesce(
                cpc_flags.c.agricultural_cpc, False).label("agricultural_cpc"),
            func.coalesce(
                ipc_flags.c.specific_ipc, False).label("specific_ipc"),
            func.coalesce(
                ipc_flags.c.agricultural_ipc, False).label("agricultural_ipc"),)
        .select_from(family_scope)
        .outerjoin(
            keyword_flags,
            family_scope.c.fam_id == keyword_flags.c.fam_id,)
        .outerjoin(
            cpc_flags,
            family_scope.c.fam_id == cpc_flags.c.fam_id,)
        .outerjoin(
            ipc_flags,
            family_scope.c.fam_id == ipc_flags.c.fam_id,).subquery())

    route_1 = or_(flags.c.specific_cpc, flags.c.specific_ipc)
    route_2 = flags.c.specific_phrase

    route_3 = and_(
        or_(flags.c.agricultural_cpc, flags.c.agricultural_ipc),
        flags.c.enabling_technology,
        flags.c.pa_function, )

    if excluded_families is not None:
        route_3 = and_(
            route_3,
            ~flags.c.fam_id.in_(
                db.query(excluded_families.c.fam_id)),)

    topical_allowed = True
    if topical_exclusions is not None:
        topical_allowed = or_(
            ~flags.c.fam_id.in_(
                db.query(topical_exclusions.c.fam_id) ),
            flags.c.fam_id.in_(
                db.query(protected_families.c.fam_id)),)

    return (
        db.query(
            *flags.c,
            route_1.label("route_1"),
            route_2.label("route_2"),
            route_3.label("route_3"),)
        .select_from(flags)
        .filter(
            and_(
                or_(route_1, route_2, route_3),
                topical_allowed,
            )).subquery())