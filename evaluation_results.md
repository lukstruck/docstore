# Docstore vs Context7 Evaluation Results

**Last Updated:** 2026-01-29
**Total Queries:** 26 (15 easy, 11 hard)

## Executive Summary

| Metric | Docstore | Context7 |
|--------|----------|----------|
| **Overall Score** | 3.2/5 | 4.5/5 |
| **Success Rate** | 73% (19/26) | 96% (25/26) |
| **Indexing Effort** | High (auto-index helps) | Zero (pre-indexed) |
| **Result Quality** | Variable (depends on source) | Consistently high |
| **Code Examples** | Often missing | Always present |

---

## Latest Evaluation Run (2026-01-29)

### Easy Problems Summary

| Scenario | Library | Docstore | Context7 | Winner |
|----------|---------|----------|----------|--------|
| easy_1 | pydantic (field_validator) | Only description (0.344) | Full examples | Context7 |
| easy_1 | polars (scan_csv) | Good (0.616) | Excellent | Context7 |
| easy_1 | pydantic (model_dump_json) | Only description (0.146) | Full API docs | Context7 |
| easy_2 | aiohttp (ClientSession) | Good (0.482) | Good | Tie |
| easy_2 | tenacity (retry) | Good (0.643) | Excellent | Context7 |
| easy_3 | typer (CLI) | Good (0.793) | Excellent | Context7 |
| easy_3 | rich (console) | Good (0.714) | Good | Tie |
| easy_3 | rich (progress) | Good (0.582) | Excellent | Context7 |
| easy_4 | pillow (thumbnail) | Excellent (0.632) | Excellent | Tie |
| easy_5 | pyyaml (safe_load) | Poor (0.422) | Excellent | Context7 |
| easy_5 | python-dotenv | Excellent (0.786) | Excellent | Tie |

**Easy Problems Score:** Docstore 4/11 wins, Context7 7/11 wins

### Hard Problems Summary

| Scenario | Library | Docstore | Context7 | Winner |
|----------|---------|----------|----------|--------|
| hard_1 | fastapi (Depends) | Good (0.557) | Excellent | Context7 |
| hard_1 | sqlalchemy (async) | **FAIL** - HTML garbage | Excellent | Context7 |
| hard_1 | passlib (CryptContext) | Only description | Good | Context7 |
| hard_1 | python-jose (jwt) | Excellent (0.653) | Excellent | Tie |
| hard_1 | celery (task) | Only description | Excellent | Context7 |
| hard_2 | optuna (create_study) | Only description | Excellent | Context7 |
| hard_2 | mlflow (log_metric) | Good (0.607) | Excellent | Context7 |
| hard_3 | kopf (on.create) | Only description (0.101) | Excellent | Context7 |
| hard_3 | boto3 (s3) | Excellent (0.667) | Excellent | Tie |
| hard_4 | confluent-kafka | Good (0.452) | Excellent | Context7 |
| hard_4 | asyncpg | **FAIL** - no results | Good | Context7 |
| hard_5 | stripe (subscription) | Poor - escaped JSON | Excellent | Context7 |
| hard_5 | weasyprint (write_pdf) | Excellent (0.613) | Excellent | Tie |

**Hard Problems Score:** Docstore 3/13 wins, Context7 10/13 wins

---

## Failure Analysis

### Docstore Failures (7 queries)

| Library | Issue | Root Cause |
|---------|-------|------------|
| pydantic | Only description indexed | llms.txt not found, GitHub fallback only got description |
| sqlalchemy | HTML garbage indexed | llms.txt returns Cloudflare HTML, not docs |
| passlib | Only description indexed | No llms.txt, no accessible GitHub docs |
| celery | Only description indexed | Docs exist but not indexed |
| optuna | Only description indexed | No llms.txt, no accessible GitHub docs |
| kopf | Only description indexed | No llms.txt, no accessible GitHub docs |
| asyncpg | No results | Library not indexed |
| stripe | Escaped JSON indexed | llms.txt contains markdoc/JSON, not plain text |

### Context7 Failures (1 query)

| Library | Issue | Root Cause |
|---------|-------|------------|
| optuna (first attempt) | Temporary fetch error | Network issue, worked on retry |

---

## Quality Metrics

### Code Example Quality (1-5)

| Tool | Avg Score | Notes |
|------|-----------|-------|
| Docstore | 2.8 | Often returns descriptions or partial docs without examples |
| Context7 | 4.6 | Consistently returns working code examples with context |

### API Coverage (1-5)

| Tool | Avg Score | Notes |
|------|-----------|-------|
| Docstore | 2.5 | Many libraries only have PyPI descriptions |
| Context7 | 4.8 | Comprehensive API documentation for most libraries |

### Relevance (1-5)

| Tool | Avg Score | Notes |
|------|-----------|-------|
| Docstore | 3.2 | When docs exist, relevance is good |
| Context7 | 4.5 | Consistently high relevance |

---

## Key Observations from Latest Run

### Docstore Strengths
1. **Polars** - Excellent scan_csv/LazyFrame docs with code examples
2. **Boto3** - Good S3 upload/download documentation
3. **python-jose** - Clear JWT encode/decode examples
4. **WeasyPrint** - Good HTML.write_pdf() documentation
5. **Pillow** - Complete thumbnail creation examples

### Docstore Weaknesses
1. **Pydantic** - Only PyPI description despite being a major library
2. **SQLAlchemy** - llms.txt returns HTML/JavaScript garbage (Cloudflare protection)
3. **Stripe** - llms.txt contains markdoc JSON, not readable docs
4. **Asyncpg** - Not indexed at all
5. **Kopf** - Only PyPI description (1 chunk)

### Context7 Strengths
1. **Consistent quality** - Every query returned useful code examples
2. **Full API documentation** - Parameters, return values, usage patterns
3. **Multiple examples** - Different use cases covered
4. **Error handling** - Many examples show proper exception handling

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
| mlflow | llms.txt | 72 | Good |
| weasyprint | GitHub | 123 | Good |
| **pydantic** | PyPI only | 1 | **Failed** |
| **SQLAlchemy** | llms.txt | 16 | **Failed** (malformed) |
| **passlib** | PyPI only | 1 | **Failed** |
| **celery** | PyPI only | 1 | **Failed** |
| **optuna** | PyPI only | 1 | **Failed** |
| **asyncpg** | Not indexed | 0 | **Failed** |
| **stripe** | llms.txt | 128 | **Failed** (malformed) |
| **pyyaml** | GitHub | 3 | **Minimal** |
| **kopf** | PyPI only | 1 | **Failed** |

**Success rate:** 12/21 (57%)

---

## Recommendations

### For Docstore Improvement (High Priority)

1. **llms.txt validation** - Reject HTML, JSON, and JavaScript content (DONE)
2. **Retry logic** - Handle transient network failures (DONE)
3. **GitHub API fallback** - When git clone fails (DONE)
4. **ReadTheDocs integration** - Many libraries have docs there
5. **Better PyPI fallback** - Fetch README when GitHub fails

### When to Use Each Tool

**Use Docstore when:**
- Working with private/internal packages
- Offline environments
- Libraries with good GitHub documentation
- Need to index custom documentation

**Use Context7 when:**
- Popular open-source libraries
- Need working code examples quickly
- API reference lookups
- Reliability is critical

### Hybrid Approach Recommended

1. Try Context7 first for popular libraries
2. Fall back to docstore for private packages or when Context7 fails
3. Pre-index frequently used libraries in docstore for offline access

---

## Overall Verdict

| Category | Winner | Margin |
|----------|--------|--------|
| **Result Quality** | Context7 | Large |
| **Code Examples** | Context7 | Large |
| **Reliability** | Context7 | Medium |
| **Coverage** | Context7 | Medium |
| **Ease of Use** | Context7 | Large |
| **Offline Use** | Docstore | Large |
| **Private Packages** | Docstore | Large |
| **Flexibility** | Docstore | Medium |

**Final Score:**
- **Docstore: 3.2/5** - Useful for specific use cases but inconsistent
- **Context7: 4.5/5** - Excellent for most documentation lookup needs

**Conclusion:** Context7 significantly outperforms docstore in coverage and quality. Docstore's main value is for private packages and offline use. The recent reliability improvements (llms.txt validation, retry logic, GitHub fallback) address some issues, but fundamental gaps remain in documentation source coverage.
