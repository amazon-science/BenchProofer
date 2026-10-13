# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Pinned dataset downloads.

Every remote dataset is named by repository *and revision*, and the bytes are
digested after download. A benchmark that silently gains, loses, or edits a row
upstream would otherwise change what a bundle was built from without changing
anything visible in the bundle.

Downloads land in the run's cache directory, so a second run over the same
benchmark performs no network access, and `--offline` refuses to perform any.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..core.plugin import Availability
from ..errors import BenchmarkError
from ..util.digest import digest_file

__all__ = ["DatasetSpec", "fetch", "hub_availability", "read_rows"]


@dataclass(frozen=True, slots=True)
class DatasetSpec:
    """A Hugging Face dataset repository, pinned to one revision.

    Attributes:
        repo_id: Dataset repository, for example ``openai/openai_humaneval``.
        revision: Commit id of that repository. A branch name is not a pin.
        files: Files to download, relative to the repository root.
        license: Upstream license, reported by ``benchproofer catalog``.
        url: Human-readable landing page.
        digests: Optional expected SHA-256 per file, with or without a ``sha256:``
            prefix. When present it is enforced.
    """

    repo_id: str
    revision: str
    files: tuple[str, ...]
    license: str = ""
    url: str = ""
    digests: dict[str, str] = field(default_factory=dict)

    @property
    def pin(self) -> str:
        """A short human-readable pin, used in reports."""
        return f"{self.repo_id}@{self.revision[:12]}"


def hub_availability() -> Availability:
    """Report whether the Hugging Face client is importable."""
    try:
        import huggingface_hub  # noqa: F401
    except ImportError:  # pragma: no cover - declared as a core dependency
        return Availability.missing("huggingface_hub is not installed", hint="pip install -e .")
    return Availability.ok()


def fetch(spec: DatasetSpec, cache_dir: Path, *, offline: bool = False) -> list[Path]:
    """Download a pinned dataset, or return the cached copy.

    Raises:
        BenchmarkError: The download failed, is unavailable offline, or a file's
            digest does not match the pin.
    """
    target = Path(cache_dir) / "datasets" / spec.repo_id.replace("/", "__") / spec.revision
    paths: list[Path] = []
    for name in spec.files:
        local = target / name
        if not local.exists():
            if offline:
                raise BenchmarkError(
                    f"{spec.pin}: {name} is not cached and offline mode forbids downloading it"
                )
            local = _download(spec, name, target)
        _verify(spec, name, local)
        paths.append(local)
    return paths


def _download(spec: DatasetSpec, name: str, target: Path) -> Path:
    from huggingface_hub import hf_hub_download
    from huggingface_hub.errors import HfHubHTTPError

    target.mkdir(parents=True, exist_ok=True)
    try:
        downloaded = hf_hub_download(
            repo_id=spec.repo_id,
            filename=name,
            repo_type="dataset",
            revision=spec.revision,
            local_dir=str(target),
        )
    except (HfHubHTTPError, OSError) as exc:
        raise BenchmarkError(f"{spec.pin}: cannot download {name}: {exc}") from exc
    return Path(downloaded)


def _verify(spec: DatasetSpec, name: str, path: Path) -> None:
    declared = spec.digests.get(name)
    if declared is None:
        return
    expected = declared.removeprefix("sha256:")
    actual = digest_file(path)
    if actual != expected:
        raise BenchmarkError(
            f"{spec.pin}: {name} has digest {actual}, expected {expected}. "
            "The pin and the bytes disagree; do not build bundles from this copy."
        )


def read_rows(path: Path) -> Iterator[dict[str, Any]]:
    """Read a dataset file as a stream of rows.

    Parquet and JSON Lines are supported, which covers how the built-in
    benchmarks publish their data.
    """
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        yield from _read_parquet(path)
    elif suffix in (".jsonl", ".json"):
        yield from _read_jsonl(path)
    else:
        raise BenchmarkError(f"unsupported dataset file type: {path.name}")


def _read_parquet(path: Path) -> Iterator[dict[str, Any]]:
    import pyarrow.parquet as pq

    table = pq.read_table(path)
    for batch in table.to_batches():
        yield from batch.to_pylist()


def _read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except json.JSONDecodeError as exc:
                raise BenchmarkError(f"{path}:{number}: {exc}") from exc
            if not isinstance(row, dict):
                raise BenchmarkError(f"{path}:{number}: expected a JSON object")
            yield row
