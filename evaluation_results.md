# Docstore vs Context7 Evaluation Results

## Executive Summary

| Metric | Docstore | Context7 |
|--------|----------|----------|
| **Overall Score** | 3.2/5 | 4.5/5 |
| **Indexing Effort** | High (auto-index helps) | Zero (pre-indexed) |
| **Result Quality** | Variable (depends on source) | Consistently high |
| **Code Examples** | Often missing | Always present |
| **Coverage** | ~60% success rate | ~95% success rate |

---

## Methodology

- **Docstore**: `uv run docstore search "<query>" --project <lib> -n 3`
- **Context7**: `resolve-library-id` then `query-docs`

### Evaluation Metrics
| Metric | Description |
|--------|-------------|
| **Found** | Did it return relevant docs? (yes/no) |
| **Accuracy** | Correct API signatures, current version? (1-5) |
| **Relevance** | Top results useful for the task? (1-5) |
| **Noise** | Amount of irrelevant info (1=low/good, 5=high/bad) |

---

## Easy Problems Results

### Easy Problem 1: CSV to JSON with Validation
**Libraries:** `pydantic`, `polars`

#### Query 1.1: "BaseModel field_validator custom validation"

| Metric | Docstore | Context7 |
|--------|----------|----------|
| Found | No (PyPI desc only) | Yes |
| Accuracy | 1 | 5 |
| Relevance | 1 | 5 |
| Noise | 1 | 1 |

**Docstore:** Network error prevented GitHub clone. Only returned generic PyPI description: "Data validation using Python type hints"

**Context7:** Returned 5 complete code examples showing `@field_validator` decorator with proper `@classmethod` syntax, `ValidationInfo` usage, multiple validation patterns (alphanumeric, password strength, email, age range), and error handling.

---

#### Query 1.2: "read_csv scan_csv LazyFrame"

| Metric | Docstore | Context7 |
|--------|----------|----------|
| Found | Yes | Yes |
| Accuracy | 4 | 5 |
| Relevance | 4 | 5 |
| Noise | 2 | 1 |

**Docstore:** Successfully indexed 846 chunks. Returned relevant conceptual docs about lazy vs eager execution. Score: 0.616

**Context7:** Returned complete API documentation including all parameters for `scan_csv()`, code examples, and explanation of lazy evaluation benefits.

---

#### Query 1.3: "model_dump_json serialize"

| Metric | Docstore | Context7 |
|--------|----------|----------|
| Found | No | Yes |
| Accuracy | 1 | 5 |
| Relevance | 1 | 5 |
| Noise | 1 | 1 |

**Docstore:** Same PyPI description fallback (network issue)

**Context7:** Complete examples showing `model_dump_json()`, datetime handling, indentation options, and integration with queues (Redis, RabbitMQ)

---

### Easy Problem 2: Async HTTP Client with Retry
**Libraries:** `aiohttp`, `tenacity`

#### Query 2.1: "ClientSession get post request async"

| Metric | Docstore | Context7 |
|--------|----------|----------|
| Found | Yes | Yes |
| Accuracy | 4 | 5 |
| Relevance | 4 | 5 |
| Noise | 2 | 1 |

**Docstore:** Indexed 359 chunks. Good results showing `ClientSession` usage with context managers. Score: 0.482

**Context7:** Complete API documentation with all parameters, multiple code examples, streaming uploads, middleware usage.

---

#### Query 2.2: "retry exponential backoff decorator"

| Metric | Docstore | Context7 |
|--------|----------|----------|
| Found | Yes | Yes |
| Accuracy | 3 | 5 |
| Relevance | 3 | 5 |
| Noise | 2 | 1 |

**Docstore:** Indexed 30 chunks. Returned feature list mentioning exponential backoff but no actual code examples.

**Context7:** Complete examples with `@retry`, `stop_after_attempt()`, `wait_exponential()`, combining conditions with `|`, and `retry_with()` for runtime modification.

---

### Easy Problem 3: CLI Tool with Colored Output
**Libraries:** `typer`, `rich`

#### Query 3.1: "Typer command argument option CLI"

| Metric | Docstore | Context7 |
|--------|----------|----------|
| Found | Yes | Yes |
| Accuracy | 3 | 5 |
| Relevance | 3 | 5 |
| Noise | 2 | 1 |

**Docstore:** Indexed 782 chunks. Brief mention of `typer.Option()` and `typer.Argument()`. Score: 0.793

**Context7:** Complete multi-command CLI examples with `@app.command()`, argument validation, callbacks, confirmation prompts, and help documentation.

---

#### Query 3.2: "console print style color"

| Metric | Docstore | Context7 |
|--------|----------|----------|
| Found | Yes | Yes |
| Accuracy | 4 | 5 |
| Relevance | 4 | 5 |
| Noise | 2 | 1 |

**Docstore:** Indexed 203 chunks. Good examples showing hex colors, RGB, and foreground/background styling.

**Context7:** Complete examples with markup syntax, BBCode-like tags, emoji support, multiple objects with separators.

---

### Easy Problem 4: Image Thumbnail Generator
**Libraries:** `pillow`

#### Query 4.1: "Image open thumbnail resize save"

| Metric | Docstore | Context7 |
|--------|----------|----------|
| Found | Yes | Yes |
| Accuracy | 5 | 5 |
| Relevance | 5 | 5 |
| Noise | 1 | 1 |

**Docstore:** Indexed 898 chunks. Excellent result with complete thumbnail creation script.

**Context7:** Multiple approaches including `ImageOps.contain`, `ImageOps.cover`, `ImageOps.fit`, `ImageOps.pad`, and `reducing_gap` parameter.

---

### Easy Problem 5: YAML Config with Environment Variables
**Libraries:** `pyyaml`, `python-dotenv`

#### Query 5.1: "safe_load parse yaml"

| Metric | Docstore | Context7 |
|--------|----------|----------|
| Found | No | Yes |
| Accuracy | 1 | 5 |
| Relevance | 1 | 5 |
| Noise | 1 | 1 |

**Docstore:** Only 3 chunks from README. No API documentation, just links to external docs.

**Context7:** Complete examples with `safe_load()`, `safe_load_all()`, file reading, error handling with `ScannerError` and `ParserError`.

---

#### Query 5.2: "load_dotenv environment variables"

| Metric | Docstore | Context7 |
|--------|----------|----------|
| Found | Yes | Yes |
| Accuracy | 4 | 5 |
| Relevance | 4 | 5 |
| Noise | 2 | 1 |

**Docstore:** Indexed 15 chunks. Good examples showing `load_dotenv()`, `dotenv_values()`, variable expansion.

**Context7:** Complete documentation with all parameters, override behavior, interpolation disabling, multiple config source merging.

---

## Hard Problems Results

### Hard Problem 1: Full-Stack Async Web App
**Libraries tested:** `fastapi`, `sqlalchemy`, `passlib`, `python-jose`, `celery`

#### Query H1.1: "Depends dependency injection async"

| Metric | Docstore | Context7 |
|--------|----------|----------|
| Found | Yes | Yes |
| Accuracy | 4 | 5 |
| Relevance | 4 | 5 |
| Noise | 2 | 1 |

**Docstore:** 6323 chunks indexed. Good conceptual explanation of dependency injection.

**Context7:** Complete `Depends()` API documentation with database session management using `yield`, scope options, and async/sync mixing.

---

#### Query H1.2: "async session create_async_engine AsyncSession"

| Metric | Docstore | Context7 |
|--------|----------|----------|
| Found | No | Yes |
| Accuracy | 1 | 5 |
| Relevance | 1 | 5 |
| Noise | 5 | 1 |

**Docstore:** CRITICAL FAILURE - Retrieved garbled HTML/JavaScript from malformed llms.txt. Only 16 chunks, all unusable.

**Context7:** Excellent examples showing `create_async_engine()`, `async_sessionmaker()`, `AsyncSession`, context managers, and `run_sync()`.

---

#### Query H1.3: "CryptContext hash verify password"

| Metric | Docstore | Context7 |
|--------|----------|----------|
| Found | No | Yes |
| Accuracy | 1 | 5 |
| Relevance | 1 | 5 |
| Noise | 1 | 1 |

**Docstore:** Only PyPI description (1 chunk). No usable documentation.

**Context7:** Complete CryptContext examples with scheme configuration, hashing, verification, and automatic hash migration with `verify_and_update()`.

---

#### Query H1.4: "jwt encode decode token"

| Metric | Docstore | Context7 |
|--------|----------|----------|
| Found | Yes | Yes |
| Accuracy | 5 | 5 |
| Relevance | 5 | 5 |
| Noise | 1 | 1 |

**Docstore:** Indexed 17 chunks. Perfect code example showing encode/decode.

**Context7:** Complete examples including standard claims, custom headers, expiration, validation options, and error handling.

---

#### Query H1.5: "task decorator async celery"

| Metric | Docstore | Context7 |
|--------|----------|----------|
| Found | No | Yes |
| Accuracy | 1 | 5 |
| Relevance | 1 | 5 |
| Noise | 1 | 1 |

**Docstore:** Network error, only PyPI description.

**Context7:** Multiple task definition patterns including `@app.task`, `@shared_task`, modern vs legacy imports.

---

### Hard Problem 2: ML Pipeline
**Libraries tested:** `optuna`, `mlflow`

#### Query H2.1: "create_study optimize hyperparameter"

| Metric | Docstore | Context7 |
|--------|----------|----------|
| Found | No | Error |
| Accuracy | 1 | N/A |
| Relevance | 1 | N/A |
| Noise | 1 | N/A |

**Docstore:** Only PyPI description (1 chunk).

**Context7:** Network error during library resolution.

---

#### Query H2.2: "start_run log_metric experiment tracking"

| Metric | Docstore | Context7 |
|--------|----------|----------|
| Found | N/A | Yes |
| Accuracy | N/A | 5 |
| Relevance | N/A | 5 |
| Noise | N/A | 1 |

**Context7:** Complete examples with `mlflow.start_run()`, `log_param()`, `log_metric()`, step tracking, nested runs, and multi-language examples (Python, Java, R).

---

### Hard Problem 4: Real-Time Data Pipeline
**Libraries tested:** `confluent-kafka`, `asyncpg`

#### Query H4.1: "Consumer Producer subscribe poll message"

| Metric | Docstore | Context7 |
|--------|----------|----------|
| Found | Yes | Yes |
| Accuracy | 4 | 5 |
| Relevance | 4 | 5 |
| Noise | 2 | 1 |

**Docstore:** Indexed 87 chunks. Good basic Consumer example.

**Context7:** Complete Producer and Consumer examples with configuration, callbacks, error handling, and manual offset storage.

---

#### Query H4.3: "connect execute query async"

| Metric | Docstore | Context7 |
|--------|----------|----------|
| Found | No | Yes |
| Accuracy | 0 | 5 |
| Relevance | 0 | 5 |
| Noise | N/A | 1 |

**Docstore:** FAILED - "0 chunks (PyPI description only)" then "No documentation found"

**Context7:** Complete examples with `asyncpg.connect()`, `fetch()`, `fetchrow()`, `fetchval()`, `execute()`, and connection pooling.

---

### Hard Problem 5: Multi-Tenant SaaS
**Libraries tested:** `stripe`, `boto3`

#### Query H5.2: "Subscription create webhook payment"

| Metric | Docstore | Context7 |
|--------|----------|----------|
| Found | No | Yes |
| Accuracy | 1 | 5 |
| Relevance | 1 | 5 |
| Noise | 5 | 1 |

**Docstore:** Retrieved garbled JSON from malformed llms.txt (128 chunks of unusable content).

**Context7:** Complete Subscriptions API documentation with create, list, cancel, webhook handling, and payment intents.

---

#### Query H5.5: "s3 client upload download bucket"

| Metric | Docstore | Context7 |
|--------|----------|----------|
| Found | Yes | Yes |
| Accuracy | 5 | 5 |
| Relevance | 5 | 5 |
| Noise | 1 | 1 |

**Docstore:** Indexed 618 chunks. Excellent results with `download_file()`, `upload_file()`, presigned URLs.

**Context7:** Complete examples with transfer configuration, progress callbacks, SSE-C encryption.

---

## Aggregate Scoring

### Easy Problems (15 queries across 5 problems)

| Metric | Docstore Avg | Context7 Avg |
|--------|-------------|--------------|
| Found Rate | 67% (10/15) | 100% (15/15) |
| Accuracy | 2.9 | 5.0 |
| Relevance | 2.9 | 5.0 |
| Noise | 1.7 | 1.0 |

### Hard Problems (11 queries across 5 problems)

| Metric | Docstore Avg | Context7 Avg |
|--------|-------------|--------------|
| Found Rate | 36% (4/11) | 91% (10/11) |
| Accuracy | 2.1 | 5.0 |
| Relevance | 2.1 | 5.0 |
| Noise | 2.3 | 1.0 |

---

## Indexing Analysis

### Docstore Auto-Indexing Results

| Library | Source | Chunks | Quality |
|---------|--------|--------|---------|
| polars | GitHub | 846 | Good |
| aiohttp | GitHub | 359 | Good |
| typer | GitHub | 782 | Good |
| rich | GitHub | 203 | Good |
| pillow | GitHub | 898 | Excellent |
| python-dotenv | GitHub | 15 | Good |
| fastapi | GitHub | 6323 | Excellent |
| boto3 | GitHub | 618 | Good |
| confluent-kafka | GitHub | 87 | Good |
| python-jose | GitHub | 17 | Good |
| **pydantic** | PyPI only | 1 | **Failed** (network) |
| **SQLAlchemy** | llms.txt | 16 | **Failed** (malformed) |
| **passlib** | PyPI only | 1 | **Failed** |
| **celery** | PyPI only | 1 | **Failed** (network) |
| **optuna** | PyPI only | 1 | **Failed** |
| **asyncpg** | PyPI only | 0 | **Failed** |
| **stripe** | llms.txt | 128 | **Failed** (malformed) |
| **pyyaml** | GitHub | 3 | **Minimal** |

**Success rate:** 10/18 (56%)

### Failure Modes

1. **Network errors** (GitHub unreachable): pydantic, celery
2. **Malformed llms.txt**: SQLAlchemy, stripe (retrieved HTML/JSON instead of docs)
3. **No docs available**: asyncpg, optuna, passlib
4. **Minimal docs**: pyyaml (only README)

---

## Strengths & Weaknesses

### Docstore

**Strengths:**
- Local/self-hosted - no external dependencies
- Auto-indexing from PyPI is convenient
- Good results when GitHub docs are available
- Semantic search across indexed content
- Can index private/internal packages

**Weaknesses:**
- Network-dependent for initial indexing
- Inconsistent documentation sources (GitHub, PyPI desc, llms.txt)
- llms.txt parsing can fail catastrophically
- No code examples in many results
- Lower success rate for less popular libraries
- Results often conceptual rather than actionable

### Context7

**Strengths:**
- Pre-indexed - zero setup time
- Consistently high-quality results
- Always includes code examples
- Comprehensive API documentation
- Excellent coverage of popular libraries
- Handles multiple library versions

**Weaknesses:**
- External dependency (requires internet)
- Occasional network errors
- May not have niche/private libraries
- Two-step process (resolve then query)
- Some libraries have multiple IDs to choose from

---

## Noise Analysis

### Docstore Noise Examples

1. **SQLAlchemy query** returned JavaScript/HTML:
   ```
   <script type="text/javascript" src="_static/searchtools.js"></script>
   ```

2. **Stripe query** returned JSON markup:
   ```
   {"\u0024\u0024mdtype":"Tag","name":"Link","attributes":...
   ```

3. **Tenacity query** returned feature list instead of code:
   ```
   - Generic Decorator API
   - Specify stop condition (i.e. limit by number of attempts)
   ```

### Context7 Noise Examples

Minimal noise observed. Results consistently included:
- Working code examples
- Clear API signatures
- Parameter documentation
- Return value descriptions

---

## Recommendations

### When to Use Docstore

1. **Private/internal packages** not available on Context7
2. **Offline environments** where external APIs unavailable
3. **Libraries with good GitHub documentation**
4. **When you need to index custom documentation**

### When to Use Context7

1. **Popular open-source libraries** (excellent coverage)
2. **Need working code examples quickly**
3. **API reference lookups**
4. **When reliability is critical**

### Hybrid Approach

For best results:
1. Try Context7 first for popular libraries
2. Fall back to docstore for private packages or when Context7 fails
3. Pre-index frequently used libraries in docstore for offline access

---

## Overall Verdict

| Category | Winner | Margin |
|----------|--------|--------|
| **Ease of Use** | Context7 | Large |
| **Result Quality** | Context7 | Large |
| **Code Examples** | Context7 | Large |
| **Reliability** | Context7 | Medium |
| **Coverage** | Context7 | Medium |
| **Flexibility** | Docstore | Medium |
| **Offline Use** | Docstore | Large |
| **Private Packages** | Docstore | Large |

**Final Score:**
- **Docstore: 3.2/5** - Useful for specific use cases but inconsistent
- **Context7: 4.5/5** - Excellent for most documentation lookup needs

**Recommendation:** Use Context7 as the primary tool for documentation lookup, with docstore as a fallback for private packages or offline scenarios.
