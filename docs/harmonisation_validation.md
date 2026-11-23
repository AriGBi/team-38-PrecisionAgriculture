
# Step 2 Applicant Harmonisation and Validation - Methodological Decisions and Rationale

## 1. Objective

The objective of the harmonisation procedure is to identify and consolidate different applicant names referring to the same entity, in order to obtain a more reliable representation of the competitive landscape in Precision Agriculture.

PATSTAT provides standardised applicant names (`psn_name`), but the same organisation may still appear under multiple names. Without harmonisation, a single organisation could be counted as several independent applicants, leading to an overestimation of the number of competitors and an underestimation of patent portfolio concentration.

However, overly aggressive harmonisation could produce the opposite problem, merging distinct organisations and artificially increasing concentration.


## 2. Data and Unit of Analysis

The harmonisation procedure uses the same patent-family population selected in Step 0.

### 2.1 Initial data coverage

| Indicator | Count |
|---|---:|
| Patent families selected in Step 0 | 5,181 |
| Families with applicant records | 5,168 |
| Family-person records | 9,898 |
| Distinct original applicant names | 3,728 |

The 13 families without applicant records are not represented in applicant-level analyses.


## 3. Harmonisation Strategy

The final harmonisation procedure consists of four main stages:

1. General name cleaning.
2. Country-name removal.
3. Prefix-based linking.
4. Explicit sector-specific mappings.

These stages are applied sequentially.

### 3.1 General name cleaning

The first stage standardises the written form of applicant names.

The following transformations are performed:

- Unicode normalisation and removal of accents.
- Conversion to uppercase.
- Removal of balanced parentheses and their contents.
- Removal of recognised legal forms using `cleanco`.
- Removal of remaining legal-form tokens at name boundaries.
- Standardisation of punctuation and whitespace.
- Removal of selected non-informative tokens.

Examples:

| Original name | Cleaned name |
|---|---|
| KUBOTA CORPORATION | KUBOTA |
| YANMAR HOLDINGS CO., LTD. | YANMAR |
| CNH (CASE NEW HOLLAND) BELGIUM | CNH BELGIUM |

The procedure reduced the number of distinct names from 3,728 to 3,371.

**Rationale:** Formatting differences and legal suffixes do not generally indicate different applicants. Removing these elements enables the identification of equivalent names before applying more specific linking rules.

Non-Latin characters are preserved rather than discarded, and the original name is retained if cleaning would otherwise produce an empty result.

### 3.2 Country-name removal

After general cleaning, some names still contain geographical qualifiers.

For example: `CNH BELGIUM → CNH`

The procedure removes recognised country expressions appearing at the end of cleaned names.  Country expressions are obtained from `pycountry` and supplemented with selected linguistic variants and geographical expressions.

Examples include:
- BELGIUM
- ITALIA
- BRASIL
- UNITED KINGDOM
- NORTH AMERICA

**Decision:** Apply country-suffix removal only to applicants classified as firms. Removing geographical expressions from universities, research institutions, or individual applicants could incorrectly merge distinct entities.
Country expressions appearing elsewhere in the name are preserved, and cities and provinces are not included in the removal rule.


### 3.3 Prefix-based linking

After removing country suffixes, longer firm names are linked to shorter firm names already present in the dataset.

For example:

- `CNH INDUSTRIAL → CNH`
- `YANMAR POWER TECHNOLOGY → YANMAR`
- `TRIMBLE NAVIGATION → TRIMBLE`

The automatic linking procedure follows several conditions:

1. The shorter name must already exist among the cleaned firm names.
2. It must contain at least three characters.
3. It must form a complete-word prefix of the longer name.
4. It cannot consist entirely of generic terms --> For example: RESEARCH, INDUSTRIAL, ENGINEERING, GROUP
5. Both names must be classified as firms.

When multiple eligible prefixes exist, the shortest eligible prefix is selected.
The procedure changed 61 original-name records.

**Rationale:** Large organisations frequently appear under extended names describing subsidiaries, business units, or geographical divisions. Prefix-based linking allows these variants to be consolidated without requiring a predefined mapping for every company.



### 3.5 Explicit sector-specific mappings

Automatic cleaning and prefix linking cannot resolve every naming variation.

Therefore, a final set of explicit mappings was introduced for the Precision Agriculture dataset.

These mappings address:

- Non-Latin company names.
- Alternative spellings.
- Typographical errors.
- Corporate name variants not captured by prefix linking.
- Selected unintended transformations produced by automatic cleaning.

Examples include:

| Original or intermediate name | Final applicant |
|---|---|
| 迪尔公司 | JOHN DEERE |
| ROBERT BOSCH | BOSCH |
| ZAHNRADFABRIK FRIEDRICHSHAFEN | ZF |
| RAVEN INDUDSTRIES | RAVEN INDUSTRIES |


**Rationale:**
 Some naming relationships require knowledge that cannot be inferred reliably from textual similarity alone.
Explicit mappings allow these cases to be handled without making the general automatic rules excessively aggressive.


### 3.6 Treatment of Acquisitions and Corporate Ownership Changes

An important methodological decision was **not to automatically merge companies based solely on acquisitions or changes in corporate ownership**.

The harmonisation procedure primarily aims to consolidate alternative names referring to the same applicant, rather than reconstructing corporate groups by aggregating all their subsidiaries and acquired companies.

**Rationale:** Automatically assigning an acquired company's entire patent portfolio to the acquiring firm would distort the historical evolution of the competitive landscape.

In particular, it could:
- Hide the original entry of an independent company into the Precision Agriculture sector.
- Underestimate the number of new entrants.
- Artificially increase the historical patent portfolio of acquiring companies.
- Misrepresent the timing of technological entry and competitive dynamics.


## 4. Final Harmonised Applicant Dataset

After applying the complete procedure, the final dataset contains:

| Indicator | Count |
|---|---:|
| Distinct original applicant names | 3,728 |
| Harmonised applicants | 3,262 |
| Patent families represented | 5,168 |

The reduction from 3,728 original names to 3,262 final applicants reflects the consolidation of naming variants and selected organisational relationships.

It should not be interpreted as proof that all remaining names correspond to completely independent economic entities.



## 4. Validation Strategy

The harmonisation procedure was evaluated using three complementary approaches:

1. Comparison against an existing gold standard.
2. Sector-specific review of predicted links.
3. Sector-specific audit of potentially missed links.

These approaches evaluate different sources of harmonisation error.

In particular, it is important to distinguish:

- **False positive links:** Different entities incorrectly assigned to the same applicant.
- **False negative links:** Equivalent names incorrectly kept as separate applicants.

Both errors affect the interpretation of the competitive landscape.

## 6. Gold Standard Validation

### 6.1 Validation procedure

The complete harmonisation pipeline was applied to company names contained in the reference file: `PATSTAT_500_label_datav4.csv`


### 6.2 Evaluation metrics

Three metrics were calculated:

**Pairwise precision**

`Precision = TP / (TP + FP)`

Measures the reliability of the links created by harmonisation.

**Pairwise recall**

`Recall = TP / (TP + FN)`

Measures the proportion of reference links recovered by harmonisation.

**F1-score**

`F1 = 2 × Precision × Recall / (Precision + Recall)`

Summarises the balance between precision and recall.

### 6.3 Results

| Metric | Result |
|---|---:|
| Reference groups | 481 |
| Predicted groups | 815 |
| Pairwise precision | 96.9% |
| Pairwise recall | 90.2% |
| F1-score | 93.5% |

The results indicate that the procedure identifies most of the expected equivalences while maintaining a relatively low rate of incorrect links.

The higher precision relative to recall suggests a tendency towards preserving separate names when their equivalence is not sufficiently established.


## 7. Sector-Specific Precision Review

### 7.1 Objective

The gold-standard evaluation was complemented by a review based directly on applicant names appearing in the Precision Agriculture dataset. The objective was to identify incorrectly merged applicants in the final harmonised population.

### 7.2 Sampling procedure

A random sample of 50 pairs of distinct original names assigned to the same final applicant was generated.

The sampling procedure uses reservoir sampling to draw uniformly from eligible name pairs without storing every possible pair.

Configuration:

- Sample size: 50 pairs.
- Random seed: 24.
- Candidate population: Distinct original-name pairs assigned to the same harmonised applicant.

Each pair was reviewed using a binary criterion:
- `1` — The names refer to the same applicant.
- `0` — The names should remain separate.

### 7.3 Results

The review produced:

| Outcome | Number of pairs |
|---|---:|
| Correct links | 48 |
| Incorrect links | 2 |
| Total reviewed | 50 |

**Estimated precision:**

`Precision = 48 / 50 = 96%`

The result supports the reliability of the linking procedure on the sector-specific sample.

However, the two incorrect links are informative.

Both concern the consolidation of names within the HITACHI group:

- HITACHI KOKI COMPANY / HITACHI SOLUTIONS.
- HITACHI / HITACHI KOKI COMPANY.

These cases are particularly interesting because the companies were historically part of the same corporate group, but their ownership structures subsequently changed. In particular, Hitachi Koki was acquired by KKR in 2017, becoming independent from the Hitachi group.


## 8. Sector-Specific Missed-Link Audit

### 8.1 Objective

The precision review focuses on names that were merged. A complementary procedure was introduced to identify potential false negatives: names that might refer to the same applicant but remained separated.

### 8.2 Candidate identification

The procedure compares cleaned names assigned to different final applicants.

Textual similarity is calculated using RapidFuzz's normalised Indel similarity (`fuzz.ratio`), on a scale from 0 to 100.

Only pairs satisfying: `Similarity >= 85` are considered candidates for review.

The similarity threshold is used to identify potentially missed links, not to merge names automatically.
A random sample of up to 50 eligible pairs is selected using reservoir sampling.

Configuration:

- Similarity threshold: 85.
- Sample size: 50 pairs.
- Random seed: 43.

### 8.3 Why similarity was used for validation rather than automatic merging

High textual similarity does not necessarily imply applicant identity.

For example, two universities can have very similar names while representing completely different institutions.

Automatically merging names above a similarity threshold would risk introducing false positive links.

**Decision:** Use fuzzy similarity to identify suspicious pairs for review rather than as a general automatic harmonisation rule.

**Rationale:** This approach makes it possible to investigate missed equivalences without compromising the conservative nature of the final harmonisation strategy.

### 8.4 Results

| Outcome | Number of pairs |
|---|---:|
| Confirmed missed links | 12 |
| Correctly separated pairs | 38 |
| Total reviewed | 50 |

The proportion of missed links among the reviewed similar pairs was: `Missed-link rate = 12 / 50 = 24%`

**Interpretation:** The audit identifies remaining equivalent names that were not consolidated by the final harmonisation procedure. This indicates that some under-consolidation remains, despite the combination of automatic cleaning and explicit mappings.



