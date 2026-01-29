"""Convert various documentation formats to Markdown."""

import re
import subprocess
from pathlib import Path

from bs4 import BeautifulSoup
from markdownify import markdownify as md
from rich.console import Console

console = Console()


class DocConverter:
    """Converts documentation files to clean Markdown."""

    def convert_file(self, file_path: Path) -> str | None:
        """Convert a file to Markdown based on its extension."""
        suffix = file_path.suffix.lower()

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            console.print(f"[yellow]Could not read {file_path}: {e}[/yellow]")
            return None

        if suffix == ".md":
            return self._clean_markdown(content)
        elif suffix == ".rst":
            return self._convert_rst(content, file_path)
        elif suffix == ".html":
            return self._convert_html(content)
        elif suffix == ".txt":
            # Might be llms.txt or plain text docs
            return self._clean_text(content)
        else:
            return None

    def _clean_markdown(self, content: str) -> str:
        """Clean up markdown content."""
        # Remove excessive blank lines
        content = re.sub(r"\n{3,}", "\n\n", content)

        # Remove HTML comments
        content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)

        return content.strip()

    def _convert_rst(self, content: str, file_path: Path) -> str:
        """Convert RST to Markdown using pandoc if available, else basic conversion."""
        # Try pandoc first
        try:
            result = subprocess.run(
                ["pandoc", "-f", "rst", "-t", "markdown", "--wrap=none"],
                input=content,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return self._clean_markdown(result.stdout)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Fallback to basic RST conversion
        return self._basic_rst_to_md(content)

    def _basic_rst_to_md(self, content: str) -> str:
        """Basic RST to Markdown conversion without pandoc."""
        lines = content.split("\n")
        result = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # RST title underlines
            if i + 1 < len(lines) and lines[i + 1] and re.match(r"^[=\-~^\"\'`]+$", lines[i + 1]):
                underline_char = lines[i + 1][0]
                level = {"=": 1, "-": 2, "~": 3, "^": 4}.get(underline_char, 2)
                result.append("#" * level + " " + line)
                i += 2
                continue

            # Code blocks
            if line.strip().startswith(".. code-block::") or line.strip().startswith("::"):
                lang_match = re.search(r"code-block::\s*(\w+)", line)
                lang = lang_match.group(1) if lang_match else ""
                result.append(f"```{lang}")
                i += 1
                # Collect indented content
                while i < len(lines) and (not lines[i].strip() or lines[i].startswith("   ")):
                    result.append(lines[i].removeprefix("   "))
                    i += 1
                result.append("```")
                continue

            # Inline code
            line = re.sub(r"``(.+?)``", r"`\1`", line)

            # Bold/italic
            line = re.sub(r"\*\*(.+?)\*\*", r"**\1**", line)
            line = re.sub(r"\*(.+?)\*", r"*\1*", line)

            # Links: `text <url>`_
            line = re.sub(r"`([^`]+)\s+<([^>]+)>`_", r"[\1](\2)", line)

            # Remove RST directives we can't convert
            if re.match(r"^\.\.\s+\w+::", line):
                i += 1
                # Skip directive content
                while i < len(lines) and (not lines[i].strip() or lines[i].startswith("   ")):
                    i += 1
                continue

            result.append(line)
            i += 1

        return self._clean_markdown("\n".join(result))

    def _convert_html(self, content: str) -> str:
        """Convert HTML to Markdown."""
        # Parse HTML
        soup = BeautifulSoup(content, "html.parser")

        # Remove script, style, nav elements
        for tag in soup.find_all(["script", "style", "nav", "header", "footer"]):
            tag.decompose()

        # Try to find main content
        main = soup.find("main") or soup.find("article") or soup.find(class_=re.compile(r"content|main|body"))
        if main:
            html_content = str(main)
        else:
            # Use body if available
            body = soup.find("body")
            html_content = str(body) if body else content

        # Convert to markdown
        markdown = md(html_content, heading_style="ATX", code_language="python")

        return self._clean_markdown(markdown)

    def _clean_text(self, content: str) -> str:
        """Clean plain text content."""
        # Remove excessive whitespace
        content = re.sub(r"[ \t]+$", "", content, flags=re.MULTILINE)
        content = re.sub(r"\n{3,}", "\n\n", content)
        return content.strip()

    def extract_title(self, content: str, file_path: Path) -> str | None:
        """Try to extract a title from the content."""
        # Try markdown heading
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()

        # Try first non-empty line if it looks like a title
        for line in content.split("\n"):
            line = line.strip()
            if line and len(line) < 100 and not line.startswith(("```", "import", "from", "#!")):
                return line

        # Fall back to filename
        return file_path.stem.replace("_", " ").replace("-", " ").title()
