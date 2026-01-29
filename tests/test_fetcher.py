"""Tests for the PyPI fetcher module."""

import pytest

from docstore.fetcher import PyPIFetcher


class TestLlmsContentValidation:
    """Tests for the _is_valid_llms_content validation method."""

    @pytest.fixture
    def fetcher(self):
        return PyPIFetcher()

    def test_rejects_html_doctype(self, fetcher):
        """HTML pages starting with doctype should be rejected."""
        content = """<!DOCTYPE html>
<html lang="en">
<head><title>Page</title></head>
<body>Some content</body>
</html>"""
        assert fetcher._is_valid_llms_content(content) is False

    def test_rejects_html_tag(self, fetcher):
        """HTML pages starting with html tag should be rejected."""
        content = """<html>
<head><title>Test</title></head>
<body>Content</body>
</html>"""
        assert fetcher._is_valid_llms_content(content) is False

    def test_rejects_script_tag(self, fetcher):
        """Pages starting with script tags should be rejected."""
        content = """<script>window.location = '/redirect';</script>"""
        assert fetcher._is_valid_llms_content(content) is False

    def test_rejects_json_object(self, fetcher):
        """JSON objects should be rejected."""
        content = """{"error": "not found", "status": 404}"""
        assert fetcher._is_valid_llms_content(content) is False

    def test_rejects_json_array(self, fetcher):
        """JSON arrays should be rejected."""
        content = """[{"id": 1}, {"id": 2}]"""
        assert fetcher._is_valid_llms_content(content) is False

    def test_rejects_javascript_with_window(self, fetcher):
        """JavaScript code with window references should be rejected."""
        content = """Some text
window.dataLayer = [];
More text here."""
        assert fetcher._is_valid_llms_content(content) is False

    def test_rejects_javascript_function(self, fetcher):
        """JavaScript code with function calls should be rejected."""
        content = """Some wrapper
function(arg) { return arg; }
End of content."""
        assert fetcher._is_valid_llms_content(content) is False

    def test_accepts_markdown_with_headers(self, fetcher):
        """Valid markdown with headers should be accepted."""
        content = """# Package Documentation

This is a Python package that does useful things.

## Installation

Install with pip:

```bash
pip install package
```
"""
        assert fetcher._is_valid_llms_content(content) is True

    def test_accepts_markdown_with_code_blocks(self, fetcher):
        """Valid markdown with code blocks should be accepted."""
        content = """Package Name

Some description of the package.

```python
from package import Module
result = Module.do_something()
```

More documentation here.
"""
        assert fetcher._is_valid_llms_content(content) is True

    def test_accepts_plain_text_with_paragraphs(self, fetcher):
        """Plain text with multiple paragraphs should be accepted."""
        content = """Package Documentation

This is the first paragraph explaining the package purpose.

This is the second paragraph with more details.

This is the third paragraph with usage examples.

And finally some closing remarks.
"""
        assert fetcher._is_valid_llms_content(content) is True

    def test_rejects_minimal_content_without_structure(self, fetcher):
        """Minimal content without documentation structure should be rejected."""
        content = "Just a single line of text."
        assert fetcher._is_valid_llms_content(content) is False

    def test_case_insensitive_html_detection(self, fetcher):
        """HTML detection should be case insensitive."""
        content = """<!DOCTYPE HTML>
<HTML><HEAD></HEAD><BODY></BODY></HTML>"""
        assert fetcher._is_valid_llms_content(content) is False
