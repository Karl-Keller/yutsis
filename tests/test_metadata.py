"""Release metadata must not drift.

CITATION.cff sat at 0.6.0 while the package moved on -- exactly the rot
the release ritual in CLAUDE.md exists to prevent. Pinned here so the
ritual is enforced by CI rather than by memory.

CITATION.cff is read with a line scan rather than a YAML parser: the two
fields are flat top-level scalars, and this avoids adding a dependency
for one assertion.
"""
from pathlib import Path

import yutsis

ROOT = Path(__file__).resolve().parent.parent


def _scalar(path: Path, key: str) -> str:
    for line in path.read_text().splitlines():
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    raise AssertionError(f"{key} not found in {path.name}")


def _toml_scalar(path: Path, key: str) -> str:
    for line in path.read_text().splitlines():
        if line.replace(" ", "").startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise AssertionError(f"{key} not found in {path.name}")


def test_version_agrees_across_package_and_pyproject():
    assert _toml_scalar(ROOT / "pyproject.toml",
                        "version") == yutsis.__version__


def test_citation_version_tracks_the_package():
    assert _scalar(ROOT / "CITATION.cff", "version") == yutsis.__version__


def test_citation_has_a_release_date():
    date = _scalar(ROOT / "CITATION.cff", "date-released")
    assert len(date) == 10 and date.count("-") == 2
