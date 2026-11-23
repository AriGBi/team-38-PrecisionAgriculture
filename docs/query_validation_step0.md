
# Step 0 Precision Agriculture Patent Retrieval - Methodological Decisions and Rationale

## 1. Objective and Sector Definition

The objective of Step 0 is to construct a reproducible patent retrieval strategy identifying innovations related to **Precision Agriculture (PA)**, with a focus on crop production.

The search strategy should capture technologies that directly implement or support precision-agriculture functions, while minimizing the inclusion of generic agricultural machinery and unrelated technological applications.

The sector definition was informed by three scientific references:

- Tey et al. (2024), *Evolution of precision agricultural technologies: a patent network analysis*.
- Avola et al. (2024), *Precision agriculture and patented innovation: State of the art and current trends*.
- Rejeb et al. (2024), *Precision agriculture: A bibliometric analysis and research agenda*.

### Scope decisions

**Included:**
- Precision crop monitoring and management.
- Variable-rate application technologies.
- Precision irrigation, seeding, and spraying.
- Agricultural guidance, navigation, and automation.
- Sensors, robotics, AI, and data-driven technologies applied to precision-agriculture functions.
- Technologies directly supporting precision-agriculture operations.

**Excluded:**
- Generic agricultural machinery improvements without an identifiable precision-agriculture function.
- Livestock and animal husbandry.
- Forestry and logging.
- Lawn, turf, and golf maintenance.
- Ornamental gardening and other unrelated applications.


## 2. Query Construction

### 2.1 Three complementary retrieval routes

The final query combines three retrieval routes using a logical OR:

`FINAL_QUERY = R1 OR R2 OR R3`

The routes are designed to identify different types of evidence of relevance to Precision Agriculture.

### R1 — Specific patent classifications

Patents are retrieved when their representative application contains a specific CPC/IPC classification associated with Precision Agriculture.

Specific CPC codes:

- `A01B79/005` --> Precision Agriculture
- `A01B69/008` --> Automatic steering or guiding of agricultural vehicles

**Rationale:**

The first code directly identifies Precision Agriculture and therefore represents a strong indicator of technological relevance.
The second code was included to capture agricultural automatic guidance technologies, which represent one of the core technological pillars of Precision Agriculture.


### R2 — Explicit Precision Agriculture terminology

Patents are retrieved when their representative application's English title or abstract contains at least one explicitly PA-related expression.

The final list contains seven expressions:

- Precision agriculture
- Precision farming
- Site specific crop management
- Site specific farming
- Site specific agriculture
- Variable rate technology
- Precision irrigation

**Rationale:**
- Some patents explicitly describe PA concepts even when they do not belong to the selected agricultural classifications.
- This route complements classification-based retrieval and captures patents using recognizable sector terminology.
- The list was kept relatively specific to limit false positives.


### R3 — Agricultural context + enabling technology + PA function

The third route retrieves patents satisfying all three conditions:

`R3 = (Agricultural CPC OR Agricultural IPC) AND Enabling Technology AND PA Function`

Agricultural classifications:

- `A01B` — Soil working and agricultural operations.
- `A01C` — Planting and sowing.
- `A01D` — Harvesting.
- `A01G25/` — Watering and irrigation.
- `A01M7/` — Spraying-related applications.

The enabling-technology group contains 51 terms, including:
- GPS, GNSS, RTK.
- Sensors and remote sensing.
- Drones and UAVs.
- Robotics and autonomous vehicles.
- Machine learning and computer vision.
- Control systems and agricultural communication technologies.
- Variable-rate and site-specific technologies.

The PA-function group contains 46 terms, including:
- Crop monitoring.
- Weed and disease detection.
- Yield mapping and prediction.
- Soil moisture and nutrient monitoring.
- Variable-rate seeding, fertilization, and spraying.
- Agricultural navigation and guidance.
- Implement control and communication.

**Rationale:**

A patent should not be considered Precision Agriculture solely because it mentions a general-purpose technology, such as sensors, robotics, or machine learning. These technologies are used in many sectors and can also appear in conventional agricultural machinery.
Similarly, agricultural classifications alone are too broad.

Requiring the simultaneous presence of:
1. An agricultural classification,
2. An enabling technology,
3. A PA-specific function,

creates a stronger indication that the invention concerns a precision-agriculture application.


## 3. Alternative Strategies and Noise Reduction

This section records the methodological alternatives considered when designing the query.

The explanations below describe the reasons for preferring the final architecture.

### 3.1 Agricultural classifications alone

**Alternative:** Retrieve all patents belonging to agricultural CPC/IPC classes.

**Problem:** Agricultural classifications contain many inventions unrelated to Precision Agriculture, including mechanical components, conventional agricultural implements, and general equipment improvements.

**Final decision:** Use broad agricultural classifications only as contextual evidence within R3, requiring both an enabling-technology term and a PA-function term.


### 3.2 Enabling technologies without PA functions

**Alternative:** Combine agricultural context with enabling-technology keywords, without requiring a specific PA function.

**Problem:** Terms such as `sensor*`, `robot*`, `control system*`, `GPS`, and `machine learn*` are generic. For example, a sensor-equipped tractor or an electronically controlled machine is not necessarily implementing Precision Agriculture.

**Final decision:** Require the presence of a PA-function keyword alongside the enabling technology and agricultural classification.

**Expected effect:** Avoid allowing ambiguous phrases to retrieve patents without contextual evidence.


## 4. Exclusion Strategy

Two types of exclusions are implemented.

### 4.1 Classification-based exclusions

The final YAML specifies the following excluded CPC prefixes:

- `A01K` — Animal husbandry.
- `C12N` — Microorganisms, enzymes, and genetic engineering-related technologies.


**Rationale:** The project focuses on Precision Agriculture in crop production, rather than livestock or unrelated biological and chemical technologies.

**Implementation decision:** Classification-based exclusions apply to R3 only.
 They do not automatically eliminate inventions retrieved independently through R1 or R2. This avoids overriding stronger direct relevance signals from specific PA classifications or terminology.

### 4.2 Topical exclusions

The query includes 23 exclusion terms covering:
- Forestry and timber.
- Lawn, golf, and turf maintenance.
- Livestock and animal production.
- Ornamental gardening and related applications.
- Rainwater.

These terms are matched against the English title of the representative application. The topical filter applies to all three routes, except for families protected by the specific CPC `A01B79/005`.

### 4.3 Protected classification: A01B79/005

Families whose representative application contains `A01B79/005` are protected from topical keyword exclusions.

**Rationale:** This classification is treated as a strong PA relevance signal, which should not be overridden by potentially ambiguous title terms.

**Important distinction:** The protection applies to topical exclusions, not to the definition of the complete study population or the application-selection procedure.


## 5. Unit of Analysis and Representative Application

### 5.1 DOCDB patent families

The analysis uses **DOCDB patent families** rather than individual patent applications.

**Rationale:** The same invention can be represented by multiple applications filed across jurisdictions. Counting individual applications would risk overrepresenting inventions receiving broader geographical protection.

### 5.2 Temporal scope

The study covers 2000–2022. A family is assigned a year using the minimum `earliest_filing_year` across its applications.
Only families whose family year falls within the specified period are eligible.
The search is restricted to PATSTAT records with `ipr_type = PI`, and invalid or missing family identifiers are excluded.

**Rationale:** The earliest filing year is intended to approximate the initial timing of the invention rather than subsequent geographical filing activity.


### 5.3 Representative-application selection

For each eligible DOCDB family, the notebook selects:

**The earliest-filed application with a non-empty English abstract.**

Applications are ranked by:
1. Application filing date (ascending).
2. Application ID (ascending), as a deterministic tie-breaker.

Families without an eligible English abstract are excluded from retrieval.



## 6. Keyword and Classification Matching

Keyword matching is performed on the concatenation of the representative application's English title and abstract.

The notebook uses case-insensitive regular-expression matching. The asterisk (`*`) is interpreted as a word-ending wildcard. Spaces, hyphens, and underscores can be matched as alternative separators.

Terms within the same keyword group are combined into one regular expression.

**Rationale:**
- Capture variations in word endings.
- Account for spelling and formatting variations.
- Keep keyword matching consistent across groups.
- Reduce the number of separate search conditions.



## 7. Retrieval Results

The executed final query retrieved:

**5,181 unique DOCDB patent families.**

The route combinations were:

| R1 | R2 | R3 | Families | Share |
|---|---|---|---:|---:|
| Yes | No | No | 3,062 | 59.1% |
| No | No | Yes | 1,419 | 27.4% |
| No | Yes | No | 305 | 5.9% |
| Yes | No | Yes | 287 | 5.5% |
| No | Yes | Yes | 52 | 1.0% |
| Yes | Yes | No | 48 | 0.9% |
| Yes | Yes | Yes | 8 | 0.2% |

### Route totals

| Route | Total families | Route-exclusive families |
|---|---:|---:|
| R1 | 3,405 | 3,062 |
| R2 | 413 | 305 |
| R3 | 1,766 | 1,419 |

**Interpretation:**

R1 accounts for the largest number of retrieved families, confirming the importance of specific patent classifications in the retrieval architecture.

R3 contributes 1,419 families not identified by R1 or R2, showing that the technology-and-function route substantially expands the retrieved population.

R2 contributes 305 exclusive families, indicating that explicit terminology provides additional coverage beyond classification and technological-function matching.

The routes are complementary rather than mutually exclusive.



## 8. Validation Strategy

### 8.1 Validation objective

Manual validation is designed to assess the relevance of the retrieved patent families to Precision Agriculture.

The goal is to identify false positives: patents retrieved by the query that do not belong to the defined sector.

A random sample from retrieved patents can support an estimate of retrieval precision.


### 8.2 Sampling design

A simple random sample is drawn from the 5,181 retrieved families.

Configuration:
- Sample size: `100`
- Random seed: `38`
- Sampling unit: DOCDB family
- Sampling method: Simple random sampling without replacement

Before sampling, family identifiers are deduplicated and sorted.

**Rationale:**

Simple random sampling gives each retrieved family the same probability of selection.

The fixed seed supports reproducibility, provided the underlying retrieved population and sampling procedure remain unchanged.

A sample of 100 families provides a manageable workload for manual assessment.


### 8.3 Manual labeling categories

Each sampled family is assigned one of three categories.

**A — Core Precision Agriculture**

Innovations directly implementing precision-agriculture functions. Examples may include variable-rate application, site-specific agricultural management, crop monitoring, or precision guidance.

**B — Supporting Precision Agriculture**

Technologies directly supporting PA functions, although their contribution may concern an enabling component rather than the entire agricultural operation. Examples may include specialized sensing, control, communication, or data-processing technologies with a clear PA application.

**C — Out of scope**

Generic agricultural machinery improvements or inventions unrelated to the defined PA sector.

### 8.4 Binary relevance definition

The three categories were used to support the final binary relevance assessment:

| Category | Binary label |
|---|---|
| A — Core PA | 1 |
| B — Supporting PA | Case-by-case assessment |
| C — Out of scope | 0 |

**Rationale:** While patents classified as A were considered directly relevant to Precision Agriculture, those falling into category B required a more careful assessment. For these patents, relevance was not assumed solely because they involved technologies potentially applicable to agriculture. Instead, each patent had to be evaluated individually to determine whether the invention had a sufficiently direct and identifiable connection to Precision Agriculture operations.



### 8.5 Validation output

The notebook exports the sample to:

`notebooks/outputs/step0/hand_validation_PA_FINAL_representative.csv`

The execution confirms:
- 100 families sampled.
- 100 representative applications retrieved.
- Unique family identifiers.
- Route indicators attached to all sampled records.


## 9. Evaluation Metrics

### 9.1 Estimated precision

Precision was estimated as:
`Precision = Relevant sampled families / Total sampled families`

The validation produced the following results:

| Classification | Number of families |
|---|---:|
| Relevant | 84 |
| Out of scope | 16 |
| **Total** | **100** |


`Precision = 84 / 100 = 84%`

The resulting **estimated precision is 84%**, indicating that the retrieval strategy successfully identified relevant Precision Agriculture patents in the majority of sampled cases.

The remaining 16% were classified as false positives, primarily reflecting the difficulty of distinguishing Precision Agriculture innovations from generic agricultural technologies.






