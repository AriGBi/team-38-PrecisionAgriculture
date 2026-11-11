"""
Precision Agriculture (PA) patent-family retrieval from PATSTAT.

Usage
-----
    from pa_patents import gather_patents

    sel = gather_patents()                      # nothing is downloaded yet
    sel = gather_patents(year_max=2024)         # override the config's year_max
    sel = gather_patents(year_min=2000, year_max=2024)   # override both
    families = sel.families_df()                # family-level flags + routes -> pandas
    counts   = sel.route_counts_df()            # route-combination summary -> pandas

    # Joins stay possible, either in pandas ...
    merged = families.merge(my_other_df, on="fam_id")

    # ... or inside PATSTAT (SQL), using the lazy subqueries:
    sf = sel.selected_families
    q = (
        sel.db.query(sf.c.fam_id, sf.c.family_year, TLS201_APPLN.appln_id)
        .join(TLS201_APPLN, TLS201_APPLN.docdb_family_id == sf.c.fam_id)
    )
    df = sel.patstat.df(q)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union

import pandas as pd
import yaml
from sqlalchemy import and_, or_, func, false, true

from epo.tipdata.patstat import PatstatClient
from epo.tipdata.patstat.database.models import (
    TLS201_APPLN,
    TLS202_APPLN_TITLE,
    TLS203_APPLN_ABSTR,
    TLS209_APPLN_IPC,
    TLS224_APPLN_CPC,
)

DEFAULT_CONFIG_NAME = "sector_PA_FINAL.yaml"
ROUTES = ["route_1", "route_2", "route_3"]


# --------------------------------------------------------------------------
# Return object
# --------------------------------------------------------------------------
@dataclass
class PatentSelection:
    """
    Lazy result of `gather_patents`.

    The SQLAlchemy objects are NOT materialised, so you can join / filter /
    extend them before pulling anything into pandas.

    Attributes
    ----------
    patstat, db        : the client and ORM session (needed to run follow-up queries)
    selected_families  : subquery, one row per selected DOCDB family
                         (fam_id, family_year, 7 evidence flags, route_1/2/3)
    flags              : subquery, evidence flags for ALL families in scope
                         (before the R1/R2/R3 selection)
    representative_apps: subquery (fam_id, appln_id, filing_date), the earliest-filed
                         application with an English abstract per family
    family_scope       : subquery (fam_id, family_year) of families in the period
    sector_query       : the un-wrapped Query behind `selected_families`
    config, params     : raw YAML config and the resolved parameters
    """

    patstat: Any
    db: Any
    selected_families: Any
    flags: Any
    representative_apps: Any
    family_scope: Any
    sector_query: Any
    config: dict
    params: dict

    def families_df(self) -> pd.DataFrame:
        """Run the query and return one row per selected family."""
        return self.patstat.df(self.sector_query)

    def route_counts_df(self) -> pd.DataFrame:
        """Unique-family counts per route combination (with share_pct)."""
        sf = self.selected_families
        n = func.count(func.distinct(sf.c.fam_id)).label("n_families")
        query = (
            self.db.query(sf.c.route_1, sf.c.route_2, sf.c.route_3, n)
            .select_from(sf)
            .group_by(sf.c.route_1, sf.c.route_2, sf.c.route_3)
            .order_by(n.desc())
        )
        counts = self.patstat.df(query)
        if counts.empty:
            raise ValueError("No patent families retrieved")
        total = int(counts["n_families"].sum())
        counts["share_pct"] = (100 * counts["n_families"] / total).round(1)
        return counts


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def term_to_regex(term: str) -> str:
    """Convert a YAML keyword into a word-bounded regex ('*' = word-ending wildcard)."""
    term = term.strip().lower()
    if not term:
        raise ValueError("Search terms cannot be empty.")

    parts = re.split(r"[\s\-_]+", term)
    patterns = [
        re.escape(part).replace(r"\*", r"[a-zA-Z0-9]*")
        for part in parts
        if part
    ]
    return r"(?:\b|_)" + r"[\s\-_/]+".join(patterns) + r"(?:\b|_)"


def _patterns(terms) -> dict:
    return {term: term_to_regex(term) for term in terms}


def _keyword_condition(patterns: dict):
    """Match any keyword in the combined English title + abstract."""
    if not patterns:
        return false()

    doc_text = func.lower(
        func.concat(
            func.coalesce(TLS202_APPLN_TITLE.appln_title, ""),
            " ",
            func.coalesce(TLS203_APPLN_ABSTR.appln_abstract, ""),
        )
    )
    combined = "|".join(f"(?:{p})" for p in patterns.values())
    return func.regexp_contains(doc_text, combined)


def _symbol_prefix_condition(column, prefixes):
    """Match CPC/IPC prefixes after removing spaces."""
    if not prefixes:
        return false()

    symbol = func.upper(func.replace(column, " ", ""))
    return or_(*[
        symbol.like(prefix.replace(" ", "").upper() + "%")
        for prefix in prefixes
    ])


def _locate_config(config_path: Optional[Union[str, Path]]) -> Path:
    if config_path is not None:
        path = Path(config_path).expanduser().resolve()
    else:
        root = Path.cwd().resolve()
        if not (root / "config" / DEFAULT_CONFIG_NAME).exists():
            root = root.parent
        path = root / "config" / DEFAULT_CONFIG_NAME

    if not path.exists():
        raise FileNotFoundError(f"Configuration not found: {path}")
    return path


def _load_params(
    config: dict,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
) -> dict:
    """Resolve parameters; `year_min` / `year_max` (if given) override the YAML."""
    kw, cpc, ipc = config["keywords"], config["cpc"], config["ipc"]
    params = {
        "env": config["patstat"]["environment"],
        "ipr_type": config["patstat"]["ipr_type"],
        "year_min": int(year_min if year_min is not None else config["analysis"]["year_min"]),
        "year_max": int(year_max if year_max is not None else config["analysis"]["year_max"]),
        "family_time_column": config["analysis"]["family_time_column"],
        "specific_phrases": kw["specific"],
        "agricultural_terms": kw["agricultural"],
        "enabling_terms": kw["enabling_technologies"],
        "pa_function_terms": kw["pa_functions"],
        "exclusion_terms": kw.get("exclusion_terms", []),
        "specific_cpc": cpc["specific"],
        "agricultural_cpc": cpc["agricultural_context"],
        "specific_ipc": ipc.get("specific", []),
        "agricultural_ipc": ipc["agricultural_context"],
        "exclude_cpc": cpc.get("exclude", []),
        "exclude_ipc": ipc.get("exclude", []),
    }
    if params["year_min"] > params["year_max"]:
        raise ValueError("Invalid year range.")
    if params["family_time_column"] != "earliest_filing_year":
        raise ValueError("Expected earliest_filing_year.")
    return params


# --------------------------------------------------------------------------
# Main entry point
# --------------------------------------------------------------------------
def gather_patents(
    config_path: Optional[Union[str, Path]] = None,
    *,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    patstat: Optional[PatstatClient] = None,
    verbose: bool = True,
) -> PatentSelection:
    """
    Build the PA patent-family selection (routes R1 OR R2 OR R3).

    Parameters
    ----------
    config_path : path to the YAML config. If None, looks for
                  ``config/sector_PA_FINAL.yaml`` from the cwd or its parent.
    year_min    : optional first family year (earliest filing year); overrides
                  ``analysis.year_min`` in the config. None = use the config.
    year_max    : optional last family year; overrides ``analysis.year_max`` in
                  the config. None = use the config.
    patstat     : an existing PatstatClient to reuse (otherwise one is created
                  using the environment from the config).
    verbose     : print a short summary.

    Returns
    -------
    PatentSelection
        A lazy container (SQLAlchemy subqueries + helpers), not a dataframe.
        Call ``.families_df()`` / ``.route_counts_df()`` to materialise, or
        join on ``.selected_families`` first.
    """
    config_file = _locate_config(config_path)
    with config_file.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    p = _load_params(config, year_min=year_min, year_max=year_max)

    # Keyword regexes
    specific_patterns = _patterns(p["specific_phrases"])
    enabling_patterns = _patterns(p["enabling_terms"])
    pa_function_patterns = _patterns(p["pa_function_terms"])
    exclusion_patterns = _patterns(p["exclusion_terms"])

    if patstat is None:
        patstat = PatstatClient(env=p["env"])
    db = patstat.orm()

    ipr_type, year_min, year_max = p["ipr_type"], p["year_min"], p["year_max"]

    # ---- Family population: DOCDB families within the period -------------
    family_year = func.min(TLS201_APPLN.earliest_filing_year)

    family_scope = (
        db.query(
            TLS201_APPLN.docdb_family_id.label("fam_id"),
            family_year.label("family_year"),
        )
        .filter(TLS201_APPLN.ipr_type == ipr_type, TLS201_APPLN.docdb_family_id > 0)
        .group_by(TLS201_APPLN.docdb_family_id)
        .having(family_year.between(year_min, year_max))
        .subquery()
    )

    # ---- Representative application: earliest filed with English abstract
    english_abstract_available = and_(
        TLS203_APPLN_ABSTR.appln_abstract_lg == "en",
        func.length(
            func.trim(func.coalesce(TLS203_APPLN_ABSTR.appln_abstract, ""))
        ) > 0,
    )

    ranked_english_apps = (
        db.query(
            TLS201_APPLN.docdb_family_id.label("fam_id"),
            TLS201_APPLN.appln_id.label("appln_id"),
            TLS201_APPLN.appln_filing_date.label("filing_date"),
            func.row_number().over(
                partition_by=TLS201_APPLN.docdb_family_id,
                order_by=[
                    TLS201_APPLN.appln_filing_date.asc(),
                    TLS201_APPLN.appln_id.asc(),
                ],
            ).label("rn"),
        )
        .select_from(TLS201_APPLN)
        .join(family_scope, TLS201_APPLN.docdb_family_id == family_scope.c.fam_id)
        .join(
            TLS203_APPLN_ABSTR,
            and_(
                TLS201_APPLN.appln_id == TLS203_APPLN_ABSTR.appln_id,
                english_abstract_available,
            ),
        )
        .filter(
            TLS201_APPLN.ipr_type == ipr_type,
            TLS201_APPLN.appln_filing_date.isnot(None),
        )
        .subquery()
    )

    representative_apps = (
        db.query(
            ranked_english_apps.c.fam_id,
            ranked_english_apps.c.appln_id,
            ranked_english_apps.c.filing_date,
        )
        .filter(ranked_english_apps.c.rn == 1)
        .subquery()
    )

    # ---- Keyword evidence (representative application only) --------------
    keyword_flags = (
        db.query(
            TLS201_APPLN.docdb_family_id.label("fam_id"),
            func.logical_or(_keyword_condition(specific_patterns)).label("specific_phrase"),
            func.logical_or(_keyword_condition(enabling_patterns)).label("enabling_technology"),
            func.logical_or(_keyword_condition(pa_function_patterns)).label("pa_function"),
        )
        .select_from(TLS201_APPLN)
        .join(representative_apps, TLS201_APPLN.appln_id == representative_apps.c.appln_id)
        .outerjoin(
            TLS202_APPLN_TITLE,
            and_(
                TLS201_APPLN.appln_id == TLS202_APPLN_TITLE.appln_id,
                TLS202_APPLN_TITLE.appln_title_lg == "en",
            ),
        )
        .join(
            TLS203_APPLN_ABSTR,
            and_(
                TLS201_APPLN.appln_id == TLS203_APPLN_ABSTR.appln_id,
                TLS203_APPLN_ABSTR.appln_abstract_lg == "en",
            ),
        )
        .filter(TLS201_APPLN.ipr_type == ipr_type)
        .group_by(TLS201_APPLN.docdb_family_id)
        .subquery()
    )

    # ---- CPC / IPC evidence (representative application only) ------------
    cpc_flags = (
        db.query(
            TLS201_APPLN.docdb_family_id.label("fam_id"),
            func.logical_or(
                _symbol_prefix_condition(TLS224_APPLN_CPC.cpc_class_symbol, p["specific_cpc"])
            ).label("specific_cpc"),
            func.logical_or(
                _symbol_prefix_condition(TLS224_APPLN_CPC.cpc_class_symbol, p["agricultural_cpc"])
            ).label("agricultural_cpc"),
        )
        .select_from(TLS201_APPLN)
        .join(representative_apps, TLS201_APPLN.appln_id == representative_apps.c.appln_id)
        .join(TLS224_APPLN_CPC, TLS201_APPLN.appln_id == TLS224_APPLN_CPC.appln_id)
        .filter(TLS201_APPLN.ipr_type == ipr_type)
        .group_by(TLS201_APPLN.docdb_family_id)
        .subquery()
    )

    ipc_flags = (
        db.query(
            TLS201_APPLN.docdb_family_id.label("fam_id"),
            func.logical_or(
                _symbol_prefix_condition(TLS209_APPLN_IPC.ipc_class_symbol, p["specific_ipc"])
            ).label("specific_ipc"),
            func.logical_or(
                _symbol_prefix_condition(TLS209_APPLN_IPC.ipc_class_symbol, p["agricultural_ipc"])
            ).label("agricultural_ipc"),
        )
        .select_from(TLS201_APPLN)
        .join(representative_apps, TLS201_APPLN.appln_id == representative_apps.c.appln_id)
        .join(TLS209_APPLN_IPC, TLS201_APPLN.appln_id == TLS209_APPLN_IPC.appln_id)
        .filter(TLS201_APPLN.ipr_type == ipr_type)
        .group_by(TLS201_APPLN.docdb_family_id)
        .subquery()
    )

    # ---- Exclusions -------------------------------------------------------
    # CPC/IPC classification exclusions (constrain R3 only)
    excluded_queries = []
    if p["exclude_cpc"]:
        excluded_queries.append(
            db.query(representative_apps.c.fam_id.label("fam_id"))
            .select_from(representative_apps)
            .join(TLS224_APPLN_CPC, representative_apps.c.appln_id == TLS224_APPLN_CPC.appln_id)
            .filter(_symbol_prefix_condition(TLS224_APPLN_CPC.cpc_class_symbol, p["exclude_cpc"]))
        )
    if p["exclude_ipc"]:
        excluded_queries.append(
            db.query(representative_apps.c.fam_id.label("fam_id"))
            .select_from(representative_apps)
            .join(TLS209_APPLN_IPC, representative_apps.c.appln_id == TLS209_APPLN_IPC.appln_id)
            .filter(_symbol_prefix_condition(TLS209_APPLN_IPC.ipc_class_symbol, p["exclude_ipc"]))
        )

    if excluded_queries:
        excluded_query = excluded_queries[0]
        for q in excluded_queries[1:]:
            excluded_query = excluded_query.union(q)
        excluded_families = excluded_query.distinct().subquery()
    else:
        excluded_families = None

    # Title-only thematic exclusions (apply to all routes)
    if exclusion_patterns:
        title_exclusion_pattern = "|".join(f"(?:{x})" for x in exclusion_patterns.values())
        topical_exclusions = (
            db.query(representative_apps.c.fam_id.label("fam_id"))
            .select_from(representative_apps)
            .join(
                TLS202_APPLN_TITLE,
                and_(
                    representative_apps.c.appln_id == TLS202_APPLN_TITLE.appln_id,
                    TLS202_APPLN_TITLE.appln_title_lg == "en",
                ),
            )
            .filter(
                func.regexp_contains(
                    func.lower(func.coalesce(TLS202_APPLN_TITLE.appln_title, "")),
                    title_exclusion_pattern,
                )
            )
            .distinct()
            .subquery()
        )
    else:
        topical_exclusions = None

    # Protected CPC A01B79/005: never removed by topical exclusions
    protected_families = (
        db.query(representative_apps.c.fam_id.label("fam_id"))
        .select_from(representative_apps)
        .join(TLS224_APPLN_CPC, representative_apps.c.appln_id == TLS224_APPLN_CPC.appln_id)
        .filter(_symbol_prefix_condition(TLS224_APPLN_CPC.cpc_class_symbol, ["A01B79/005"]))
        .distinct()
        .subquery()
    )

    # ---- Combine all evidence at family level (missing -> False) ---------
    flags = (
        db.query(
            family_scope.c.fam_id,
            family_scope.c.family_year,
            func.coalesce(keyword_flags.c.specific_phrase, False).label("specific_phrase"),
            func.coalesce(keyword_flags.c.enabling_technology, False).label("enabling_technology"),
            func.coalesce(keyword_flags.c.pa_function, False).label("pa_function"),
            func.coalesce(cpc_flags.c.specific_cpc, False).label("specific_cpc"),
            func.coalesce(cpc_flags.c.agricultural_cpc, False).label("agricultural_cpc"),
            func.coalesce(ipc_flags.c.specific_ipc, False).label("specific_ipc"),
            func.coalesce(ipc_flags.c.agricultural_ipc, False).label("agricultural_ipc"),
        )
        .select_from(family_scope)
        .outerjoin(keyword_flags, family_scope.c.fam_id == keyword_flags.c.fam_id)
        .outerjoin(cpc_flags, family_scope.c.fam_id == cpc_flags.c.fam_id)
        .outerjoin(ipc_flags, family_scope.c.fam_id == ipc_flags.c.fam_id)
        .subquery()
    )

    # ---- Three-route selection -------------------------------------------
    R1 = or_(flags.c.specific_cpc, flags.c.specific_ipc)
    R2 = flags.c.specific_phrase

    agricultural_class = or_(flags.c.agricultural_cpc, flags.c.agricultural_ipc)
    r3_base = and_(agricultural_class, flags.c.enabling_technology, flags.c.pa_function)

    if excluded_families is not None:
        R3 = and_(r3_base, ~flags.c.fam_id.in_(db.query(excluded_families.c.fam_id)))
    else:
        R3 = r3_base

    if topical_exclusions is not None:
        topical_allowed = or_(
            ~flags.c.fam_id.in_(db.query(topical_exclusions.c.fam_id)),
            flags.c.fam_id.in_(db.query(protected_families.c.fam_id)),
        )
    else:
        topical_allowed = true()

    sector_query = (
        db.query(
            *flags.c,
            R1.label("route_1"),
            R2.label("route_2"),
            R3.label("route_3"),
        )
        .select_from(flags)
        .filter(and_(or_(R1, R2, R3), topical_allowed))
    )

    selection = PatentSelection(
        patstat=patstat,
        db=db,
        selected_families=sector_query.subquery(),
        flags=flags,
        representative_apps=representative_apps,
        family_scope=family_scope,
        sector_query=sector_query,
        config=config,
        params=p,
    )

    if verbose:
        print(f"Configuration: {config_file}")
        print(f"Environment: {p['env']} | Period: {year_min}-{year_max}")
        print("Selection built (lazy): call .families_df() or join on .selected_families")

    return selection
