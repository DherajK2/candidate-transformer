# Multi-Source Candidate Data Transformer

A production-quality Python backend application that accepts heterogeneous candidate data sources, parses them, transforms them into a canonical candidate profile, normalizes attributes, merges duplicate records, resolves conflicts deterministically, scores field and overall confidence, preserves complete provenance logs, validates schema shapes, and outputs custom dynamic projections.

---

## Architecture Diagram

```
       Heterogeneous Sources
+---------------------------------+
| Recruiter CSV  |   ATS JSON     |
| Resume PDF     |   Resume TXT   |
+-------+--------+-------+--------+
        |                |
        v                v
+---------------------------------+
|             Parsers             |
|  - CSV/JSON Structural Readers  |
|  - PDF/TXT Text & Regex Parsers |
+----------------+----------------+
                 | (Extracts attributes with local provenance/confidence)
                 v
+---------------------------------+
|        Canonical Mapper         |
|  - Maps raw maps into Canonical |
|    data models (Base Profiles)  |
+----------------+----------------+
                 |
                 v
+---------------------------------+
|           Normalizer            |
|  - E.164 phone formatting       |
|  - YYYY-MM date normalization   |
|  - Canonical skills mapping     |
|  - ISO-3166-1 alpha-2 countries |
|  - URL scrubbing & cleaning     |
+----------------+----------------+
                 |
                 v
+---------------------------------+
|          Merge Engine           |
|  - Groups profiles by match key |
|  - Selects attributes across    |
|    sources via Conflict Rules   |
+----------------+----------------+
                 |
                 v
+---------------------------------+
|        Confidence Engine        |
|  - Evaluates field confidence   |
|  - Boosts on source consensus   |
|  - Penalizes on failures        |
|  - Computes profile score       |
+----------------+----------------+
                 | (Produces complete Canonical Candidate Profile)
                 v
+---------------------------------+
|        Projection Layer         |
|  - Field selection & renaming   |
|  - Provenance/Confidence toggle  |
|  - Missing values strategy      |
+----------------+----------------+
                 | (Emits Projected JSON)
                 v
+---------------------------------+
|         Validation Layer        |
|  - Validates against JSON Schema|
+----------------+----------------+
                 |
                 v
            Final Output
```

---

## Features
- **Heterogeneous Parsers**: Support for structured (CSV, JSON) and unstructured (PDF, TXT) candidate source files.
- **Robust Normalizers**: Normalizes phones to E.164, country names/codes to ISO-3166-1 alpha-2, dates to ISO `YYYY-MM`, skills to canonical terminology, and sanitizes profile URLs.
- **Deterministic Merge Engine**: Merges multiple candidate source profiles by key, resolving details using configurable conflict priority rules (Contact Details: CSV > Resume; Job Details: Resume > CSV) and longest-string description matching.
- **Consensus & Penalty Confidence Engine**: Computes overall and field confidence. Agreement across sources boosts confidence score, while parsing/normalization warnings penalize it.
- **Complete Ingestion Provenance**: Tracks source name, timestamp, extraction method, and field-level confidence for every value resolved.
- **JSON Configuration-driven Projection Layer**: Renames, extracts, subsets, and shape-shifts canonical profiles (e.g. `emails[0]` -> `primary_email`) while managing missing value fallbacks (`null`, `omit`, `error`).
- **Validation**: Enforces canonical format integrity using JSON Schema validators.
- **Command-line Interface**: Beautiful terminal user interface with custom banners, escape styling, and verbose logging levels.

---

## Folder Structure
```
candidate_transformer/
├── README.md
├── requirements.txt
├── main.py                    # CLI Ingestion Entrypoint
├── generate_abstract.py       # One-page Abstract PDF Generator
├── src/
│   ├── __init__.py
│   ├── models.py              # Canonical dataclasses & schemas
│   ├── pipeline.py            # End-to-end pipeline coordinator
│   ├── parsers/               # CSV, JSON, TXT, PDF parsers
│   ├── normalizer/            # Value formatting normalizers
│   ├── merger/                # Conflict resolvers & Merge engine
│   ├── confidence/            # Scoring & consensus evaluators
│   ├── projection/            # JSON-driven dynamic projections
│   ├── validator/             # JSON Schema validator
│   └── utils/                 # Logging formats and setup
├── config/                    # Ingestion projection configurations
├── input/                     # Mock structured & unstructured inputs
├── output/                    # Generated profile outcomes
└── tests/                     # Test package (100% pass verification)
```

---

## Installation
1. Clone this repository to your system workspace.
2. Initialize virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
4. Generate the mock PDF Resume:
   ```bash
   python input/generate_pdf_resume.py
   ```

---

## CLI Usage

### Command-line Options
```bash
python main.py --help
```

### Run End-to-End Pipeline
```bash
python main.py \
  --csv input/recruiter.csv \
  --json input/ats_profile.json \
  --resume input/resume_john_doe.pdf \
  --config config/default_config.json \
  --output output/profile_default.json
```

### Run with Custom Dynamic Projection Config
```bash
python main.py \
  --csv input/recruiter.csv \
  --json input/ats_profile.json \
  --resume input/resume_john_doe.pdf \
  --config config/custom_projection.json \
  --output output/profile_custom.json
```

---

## Testing
Run the test suite using `pytest`:
```bash
pytest
```

---

## Design Decisions & Trade-offs
- **Regex vs. LLMs**: Standard regex rules and keyword matches are used for parsing resumes instead of heavy deep learning pipelines. While LLMs excel on highly volatile layouts, regex parses execute in milliseconds, cost zero API tokens, run offline, and are 100% deterministic (essential for candidate auditing).
- **In-Memory Pipeline**: The pipeline processes data records in-memory via type-safe dataclasses rather than writing intermediate staging records to database tables. This makes parsing extremely quick, although memory must be sized appropriately if transforming thousands of candidate documents concurrently (handled by batch streaming).
- **Loose Coupling**: Components have no direct dependencies on each other and are linked through the `CandidatePipeline` coordinator. This makes them easily swap-able (e.g. replacing the regex parser with an LLM parser).

---

## Scalability & Production Readiness
To move this system into a high-scale production stack:
1. **Queue-Based Ingestion**: Place incoming candidate documents on an SQS/RabbitMQ queue and process jobs via isolated worker threads (Celery).
2. **Distributed Merging**: Use a search engine like Elasticsearch/OpenSearch to match incoming candidates against existing profiles using phone/email indexes before triggering merge operations.
3. **Blob Storage**: Save raw documents (PDFs, JSONs) to secure S3 storage, keeping only canonical JSONs in structured DB rows.
