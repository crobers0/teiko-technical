# Teiko Technical Assessment: Cell Population Analysis Dashboard

A Python-based data analysis and visualization platform for exploring immunological cell population data across clinical projects and subjects. This project demonstrates data pipeline automation, relational database design, and interactive web-based analytics.

**Author:** Colin Roberson 
[**Email**](mailto:colinroberson969@gmail.com)
**Date:** March 7th, 2026

---

## Quick Start

### Prerequisites
- Python 3.8+
- Virtual environment activated (recommended)

### Installation and Running

1. **Install dependencies:**
   ```bash
   make setup
   ```

2. **Run the complete pipeline (data loading + analysis + dashboard):**
   ```bash
   make dashboard
   ```

3. **Access the dashboard:**
   - The Flask server will start on `http://127.0.0.1:5000`
   - Open this URL in your browser

4. **Clean up generated files:**
   ```bash
   make clean
   ```

### Individual Commands
- `python load_data.py` — Load CSV data into SQLite database
- `python initial_analysis.py` — Generate cell frequency analysis
- `python statistical_analysis.py` — Perform statistical comparisons
- `python subset_analysis.py` — Extract and analyze baseline samples
- `python dashboard.py` — Start the interactive dashboard

---

## Database Schema

The data is stored in SQLite with a normalized star-schema design optimized for both analytical queries and scalability.

### Design Overview

```
subjects (central entity)
  ├── conditions (subject → conditions mapping)
  ├── treatments (subject → treatments & responses)
  └── samples (subject → biological samples & cell counts)
```

### Tables

**subjects** (Primary Key: subject)
- `subject` (VARCHAR 255): Unique subject identifier
- `project` (VARCHAR 50): Project name for grouping
- `age` (INT): Subject age
- `sex` (VARCHAR 10): Biological sex

**conditions** (Primary Key: condition_id)
- `subject` (FK): Link to subjects table
- `condition` (VARCHAR 50): Medical condition (e.g., melanoma)
- UNIQUE constraint on (subject, condition) prevents duplicates per subject

**treatments** (Primary Key: treatment_id)
- `subject` (FK): Link to subjects table
- `treatment` (VARCHAR 50): Treatment type (e.g., miraclib)
- `response` (VARCHAR 10): Treatment response (yes/no/null)
- UNIQUE constraint on (subject, treatment) ensures one treatment record per subject

**samples** (Primary Key: sample)
- `subject` (FK): Link to subjects table
- `sample_type` (VARCHAR 50): Sample category (e.g., PBMC)
- `time_from_treatment_start` (INT): Timepoint in days/hours
- Cell population counts: `b_cell`, `cd8_t_cell`, `cd4_t_cell`, `nk_cell`, `monocyte` (all INT)

### Indexes
```sql
idx_subjects_project    — Fast filtering by project
idx_samples_subject     — Fast sample lookup by subject
idx_treatments_subject  — Fast treatment lookup by subject
idx_conditions_subject  — Fast condition lookup by subject
idx_samples_time        — Fast temporal filtering
```

### Design Rationale

1. **Normalization for Data Integrity**
   - Separates concerns: subjects, conditions, treatments, samples
   - Eliminates redundancy (subject metadata stored once)
   - UNIQUE constraints prevent accidental duplicates
   - Foreign keys maintain referential integrity

2. **Support for Complex Medical Data**
   - Subjects can have **multiple conditions** (comorbidities)
   - Subjects can have **multiple treatments** (sequential or parallel)
   - Each treatment can have a single response outcome
   - Samples are time-indexed for longitudinal analysis

3. **Scalability to Hundreds of Projects & Millions of Samples**
   - **Vertical keys (VARCHAR 255)**: Subject/sample IDs are strings to handle large ID spaces
   - **Indexes on foreign keys**: Fast direct filtering by project, subject, or timepoint
   - **No redundant aggregation**: Raw cell counts stored; aggregation done at query-time in application
   - **Efficient joins**: Star schema enables fast multi-table queries without cross joins

4. **Analytical Query Performance**
   - Project-level filtering: `idx_subjects_project` enables fast project isolation
   - Subject-level analysis: `idx_treatment_subject` enables per-subject response tracking
   - Timeline analysis: `idx_samples_time` enables temporal comparisons
   - Complex filtering: Parametrized SQL queries in dashboard prevent full-scan filters

5. **Extensibility**
   - New conditions/treatments can be added without schema changes
   - Additional cell populations can be inserted as new columns
   - Multi-project analytics can be performed via GROUP BY project

---

## Code Structure

### Directory Layout
```
├── load_data.py              # CSV → SQLite pipeline
├── initial_analysis.py       # Cell frequency analysis
├── statistical_analysis.py   # Mann-Whitney U tests, responder comparison
├── subset_analysis.py        # Baseline sample extraction & summary
├── dashboard.py              # Flask web application (main entry point)
├── schema.sql                # Database schema definition
├── requirements.txt          # Python dependencies
├── Makefile                  # Automation commands
├── static/
│   ├── dashboard.js          # Tab switching, iframe responsiveness, nav highlighting
│   └── styles.css            # UI styling
└── templates/
    ├── base.html             # Navigation & layout
    ├── index.html            # Home page with summary stats
    ├── initial_analysis.html # Cell frequency visualization
    ├── data_table.html       # Data browser with filtering
    ├── subset_analysis.html  # Filtered subset analysis
    └── visuals.html          # Statistical analysis results
```

### Module Descriptions

**load_data.py**
- Parses input CSV file
- Creates SQLite schema
- Populates subjects, conditions, treatments, samples tables
- Handles duplicate prevention with TRY/CATCH

**initial_analysis.py**
- Queries cell frequency data from SQLite
- Calculates percentages for each cell population per sample
- Generates interactive Plotly table visualization
- Exports to `cell_frequencies.csv`

**statistical_analysis.py**
- Filters for melanoma patients treated with miraclib
- Compares responders vs. non-responders
- Performs Mann-Whitney U tests with Bonferroni correction
- Generates boxplot visualizations and CSV of statistics

**subset_analysis.py**
- Extracts baseline PBMC samples (time_from_treatment_start = 0)
- Computes summary statistics (samples per project, responder counts, sex distribution)
- Exports to `baseline_miraclib_melanoma_samples.csv`

**dashboard.py** (Flask Application)
- **Routes:**
  - `/` — Home page with dataset summary
  - `/initial_analysis` — Cell frequency table
  - `/data` — Data Browser: filter & explore all samples
  - `/visuals` — Statistical Analysis: responder comparisons
  - `/subset_analysis` — Subset Analysis: baseline sample exploration
  - `/api/samples` — JSON API for sample search
  - `/download/<filename>` — CSV download endpoint
  - `/health` — Health check endpoint

- **Key Features:**
  - **SQL-based filtering**: All search/filter operations happen in SQLite
  - **Dynamic filters**: Numeric ranges, select dropdowns, and text search
  - **Pagination**: Efficient browsing of large datasets (50 rows per page, configurable)
  - **Summary statistics**: Per-filtered-dataset project breakdown, response counts, sex distribution
  - **Tab switching**: Client-side view toggling between data table and summary stats

### Design Decisions

1. **SQLite instead of in-memory filtering**
   - Enables scalability to large datasets
   - Queries run at database level
   - Reduces memory footprint of dashboard process

2. **Parametrized SQL queries**
   - Prevents SQL injection
   - Query caching by database engine
   - Maintains data separation per request

3. **Separate analysis scripts + Flask app**
   - Pipeline scripts can be run offline for reproducibility
   - Dashboard only serves pre-generated results and live filtering
   - Separation of concerns: data processing vs. presentation

4. **Client-side tab switching with `display: none`**
   - No page reloads needed
   - Faster UX than server-side routing for tabs
   - JavaScript handles button state management

5. **Responsive iframe styling**
   - Plotly visualizations automatically scale to viewport
   - Injected CSS into iframes ensures mobile compatibility

---

## Dashboard Features

### Navigation
- **Home** — Overview of dataset volume
- **Initial Analysis: Data Overview** — Cell frequency table visualization
- **Data Browser** — Full dataset explorer with filtering & summary statistics
- **Statistical Analysis** — Responder vs. non-responder comparisons
- **Data Subset Analysis** — Baseline melanoma/miraclib patient analysis

### Filtering
- **Numeric filters**: Min/max range selection (e.g., age 18–65)
- **Select filters**: Dropdown for categorical columns with ≤20 unique values
- **Text filters**: Free-text search with LIKE matching

### Summary Statistics
- Samples per project
- Subjects by treatment response
- Subjects by biological sex

All statistics update dynamically based on active filters.

---

## Accessing the Dashboard

Once running, visit: **http://127.0.0.1:5000**

---

## Stack

- **Backend**: Flask (Python web framework)
- **Database**: SQLite3 (serverless relational database)
- **Data Processing**: pandas, numpy
- **Statistics**: scipy (Mann-Whitney U tests)
- **Visualization**: Plotly (interactive HTML charts)
- **Frontend**: HTML5, CSS3, vanilla JavaScript

---

## Future Enhancements

1. **Multi-project comparisons**: Side-by-side responder analysis across projects
2. **Export templates**: Automated report generation (PDF)
3. **Real-time data additions**: API endpoint to add new samples
4. **Advanced statistics**: Logistic regression, survival analysis
5. **Authentication**: User roles for restricted project access
6. **Caching layer**: Redis for frequently-accessed query results
