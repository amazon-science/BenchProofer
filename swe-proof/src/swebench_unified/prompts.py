# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Prompt registry: every agent prompt lives under prompts/, swappable without
touching code (docs/adapting_a_benchmark.md §6). Lookup order: <override>/<backend>,
<override>/shared, prompts/<backend>, prompts/shared, where <override> is
$SBU_PROMPTS_DIR. Templates use strict str.format {placeholder} substitution —
a missing field raises rather than shipping a literal "{iid}" to an agent.
"""
from __future__ import annotations

import os
from pathlib import Path

from .paths import PROMPTS_ROOT


class PromptNotFound(KeyError):
    pass


class PromptRenderError(KeyError):
    """A prompt file that str.format cannot render — almost always an undoubled
    literal brace read as a field name. Kept a KeyError so existing handlers
    (which caught the bare KeyError str.format raised) still see it."""


def _candidates(name: str, backend: str | None) -> list[Path]:
    roots: list[Path] = []
    override = os.environ.get("SBU_PROMPTS_DIR")
    if override:
        roots.append(Path(override))
    roots.append(PROMPTS_ROOT)
    out = []
    for root in roots:
        if backend:
            out.append(root / backend / f"{name}.md")
        out.append(root / "shared" / f"{name}.md")
    return out


def prompt_path(name: str, backend: str | None = None) -> Path:
    for p in _candidates(name, backend):
        if p.exists():
            return p
    tried = "\n  ".join(str(p) for p in _candidates(name, backend))
    raise PromptNotFound(f"no prompt file for {name!r} (backend={backend}); tried:\n  {tried}")


def load_prompt(name: str, backend: str | None = None, **subs) -> str:
    """Load a prompt template and substitute {placeholder} fields
    (str.format rules; literal braces are {{ }}).

    A file that cannot be rendered raises PromptRenderError NAMING THE FILE.
    str.format's own KeyError says only which field was missing, and this failure
    surfaces inside an agent subprocess where it looks like a model that never
    submitted (one wave lost 52 cells to exactly that) — so the message has to
    point at the file to edit, which for an SBU_PROMPTS_DIR override is not a
    file this repo ships.
    """
    path = prompt_path(name, backend)
    text = path.read_text()
    if not subs:
        return text
    try:
        return text.format(**subs)
    except (KeyError, IndexError, ValueError) as e:
        raise PromptRenderError(
            f"{path} is rendered with str.format (fields: {sorted(subs)}), and "
            f"failed with {type(e).__name__}: {e}. A literal brace in a rendered "
            f"prompt is read as a FIELD NAME — double it ({{{{ }}}}).") from e
