# Step 2: competitive landscape (Precision Agriculture)

Team 38, Innovation Management 2026/27, client John Deere.

Notebook: `notebooks/Step2_competitive_landscape.ipynb`. It is the course notebook `11_competitive_landscape` (course repo, `tutorial_1/`) with the sector families replaced by our Step 0 `selected_families`, plus a few cells for applicant names. Outputs are cleared on purpose.

Working log with tables, charts and sources: https://claude.ai/artifact/CPRqV781KTn6kYrAnDH5St

## How to run

Run it on TIP, against PATSTAT PROD.

- It needs `notebooks/Step0_validation.ipynb` and `config/sector_PA_FINAL.yaml` from this repo. Section 5.0 executes the Step 0 notebook, unchanged, up to the cell that defines `selected_families`. It does so in a separate namespace so that Step 0 functions do not overwrite the course ones, and it checks that both use the same environment and years.
- Do not use Run All. Skip section 2.4 (gold-standard exercise) and all of section 4 (fuel-cell replication: heavy on PROD and not needed here). Run everything else from top to bottom.
- Expect 10 to 20 minutes, mostly the Step 0 query. The first run saves the 5,181 family ids to `notebooks/outputs/step2/step0_families.csv` and later runs read that file. The `outputs/` folder is not in the repo.
- If an interrupted query makes the next one fail with `PendingRollbackError`, run `db.rollback()` and re-run the cell.

## Settings (configuration cell)

- `ENV = "PROD"`, years 2000 to 2022.
- `LAST_COMPLETE_YEAR = 2022`. The course default window ends in 2025 and treats the last three years as incomplete, so 2022 is its last complete year. The 2022 count is 11% below 2021, which may be partly publication lag.
- `SPLIT_YEAR = 2013`. Families grow about 4% a year until 2012 and about 27% a year from 2013 to 2019.
- `NAME_METHOD = "cleanco"`, `WINDOW = 3`, `TOP_N = 15`.
- `SECTOR_CPC_PREFIXES`: the 31 CPC main groups used as subfields (16 agricultural, 15 enabling technologies), with a trailing slash so that G05D1/ does not also catch G05D16.
- `GOLD_STANDARD_FILE` points to the course repo in the home folder. It is only used in section 2.4, which we do not run.

## What differs from the course notebook

Cells are identified by their first comment line.

1. Configuration cell: the values above.
2. `# Step 0 families` (top of 5.0): loads `selected_families` from the Step 0 notebook.
3. `# 1. sector families` (5.0), replaced: families come from `selected_families`. Applicants and CPC codes are fetched with a fixed list of family ids, because using `selected_families` inside the joins re-ran the whole Step 0 query each time.
4. `# Fix 1`, `# Fix 2`, `# Fix 3`: applicant names, see below.
5. The course cell after `# 4. the first patent ever`: its first line (`links = prepare_applicants(...)`) is commented out, because it rebuilds `links` and loses the group type.
6. 5.1, replaced: individuals are excluded, the group type is recomputed, and HH, 1/HH, CR4, CR8 and Gini are computed on 3-year windows. The course text announces the windows but has no code for them.
7. Cell above 5.2: defines `answer_box` (called by the course but never defined) and sets three missing countries by hand.
8. 5.3: a subfield is the CPC main group (e.g. G05D1) instead of the first two digits after the slash.
9. `# 5.3 Subfield growth map, deck version`: saves `outputs/step2/subfield_growth_map.png`.
10. Read-only check cells: `# Diagnostic before the group rules`, `# Check: renamed or split applicants`, `# Check: what are Lely's families about?`, `# Diagnostic for task 6`, `# Robustness check`.

## Applicant names

- Names come from `psn_name`, cleaned with cleanco and the course rules, plus: Unicode normalisation (accents, full-width letters); a manual map for Chinese, Japanese, Korean and Cyrillic names of Western firms (e.g. 迪尔公司 is Deere), which otherwise became one empty applicant with 189 families; typo fixes; and group rules for Deere, CNH, Kubota, Yanmar, AGCO, Bayer, Claas, Trimble, BASF, Bosch, ZF and Mitsubishi Mahindra.
- Ownership rules use today's owner for all years: Blue River and Bear Flag to Deere, Raven to CNH, Precision Planting and PTx Trimble to AGCO, AgJunction to Kubota, Climate and Monsanto to Bayer. `APPLY_OWNERSHIP = False` switches them off. Sources are in the working log.
- `consolidated_names` returns the group. `entity_links` keeps the single companies, for scouting.
- A group is a firm if any of its companies is a firm.

## Results

- 5,181 families (same as Step 0); 4,865 have at least one organisation as applicant.
- Concentration, all organisations: HH 0.024 (about 41 equal-sized applicants), CR4 28.1%. The top 4 hold between 26% and 34% in every 3-year window.
- Concentration, firms only: HH 0.047, CR4 39.3%. By window the top 4 go from 32.6% (2014-2016) to 41.4% (2017-2019) and 52.0% (2020-2022). The recent dispersion seems to come from applicants that are not firms; this is still to be checked.
- Largest applicants: Deere 503 families, CNH 457, Kubota 436, Yanmar 202, AGCO 189. 14 of the top 15 filed before 2013. The only entrant in the top 15 is Autonomous Solutions (45 families, none after 2018).
- Families with a new applicant fall from about 80% (2007-2011) to 30% (2022).
- Fastest subfields between 2013-2017 and 2018-2022: G06V10 image recognition +729%, G01S17 lidar +691%, G06N3 neural networks +483%, G06V20 scene recognition +457%, G06T7 image analysis +447%; the whole sector grows +118%.

## Known limitations

- Current owner for all years (ownership rules).
- 587 applicants of type UNKNOWN stay in the concentration measures; some are individuals.
- Entry and exit include individuals, as in the course notebook.
- 11 non-Latin names (one family each) could not be identified and keep their original name.
- 383 families have no CPC code and do not appear in the subfields; 13 families have no applicant.
- "First patent ever" shows 1900 for some firms: it is the lower bound of the course query.
- G06V was created in 2022, so its early counts depend on reclassification.
- One Lely family (2019, feeding animals) is livestock and passed the Step 0 exclusions.
- The Step 1 notebook may use its own family definition and years: to be aligned with `selected_families` and 2022.

## Status

Done: 5.1 concentration, 5.2 incumbents and entrants, 5.3 subfields, robustness check.

To do: 5.4 PEST table with sources, follow-up on firm concentration in 2020-2022, check of the CPC titles of the 31 subfields.
