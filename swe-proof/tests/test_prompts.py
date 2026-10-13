# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Every prompt template must survive `str.format`.

`load_prompt` substitutes with strict `str.format`, so ANY brace in the file is
a format field. A prompt that documents a JSON payload shape inevitably writes
`{id, verdict, evidence}`, and `str.format` reads that as a field named
"id, verdict, evidence" and raises `KeyError` at load time -- inside the agent
subprocess, where the driver sees only a missing payload.

A whole batch of cells can be lost to exactly this, every row recorded as
`no-payload` ("no verdict in submission"), which is indistinguishable from an
agent that ran and failed to submit. The braces have to be doubled, and nothing
was checking.

So: render every template with a permissive mapping and assert it does not
raise. This needs no agent, no verifier and no network -- it is a parse check
over the files that ship.
"""
from __future__ import annotations

import re
from pathlib import Path
from string import Formatter

import pytest

from swebench_unified.paths import PROMPTS_ROOT

# The registry's own index: it DOCUMENTS which placeholders each prompt takes,
# so it is full of `{iid}` written as prose and is never itself loaded.
NOT_A_PROMPT = {"README.md"}
PROMPTS = sorted(p for p in PROMPTS_ROOT.rglob("*.md")
                 if str(p.relative_to(PROMPTS_ROOT)) not in NOT_A_PROMPT)
# `{name}`, `{name.attr}`, `{name[0]}`, with the optional !conversion and :spec
PLACEHOLDER = re.compile(r"\w+(?:[.\[][^{}]*)?")

# Sentinel for a brace run `str.format` itself rejects, e.g. a lone `}`.
UNPARSEABLE = "\x00unparseable"


def fields(text: str) -> list[str]:
    """Every field name `str.format` would look up in this text.

    Delegated to `string.Formatter().parse`, which IS the parser `str.format`
    runs, because every hand-rolled approximation of it has been wrong here in
    one direction or the other:

      - scanning raw text for `{...}` reads the inner pair of an already-correct
        `{{gate, verdict, notes}}` as a field and flags six healthy prompts;
      - stripping `{{`/`}}` first, then scanning, mis-reads a placeholder that
        ABUTS an escaped brace -- `..._in_{scratch}}}` is `{scratch}` followed by
        a literal `}`, but the strip leaves `{scratch\\x01}` and reports the field
        as `scratch\\x01`. That one flagged a prompt that renders correctly, which
        is the worse direction: a false alarm on a healthy file teaches the next
        person to edit the test rather than the prompt.

    A brace run the real parser rejects (a lone `}`) yields UNPARSEABLE, since
    that is a genuine defect and not something to swallow.
    """
    try:
        return [f for _, f, _, _ in Formatter().parse(text) if f is not None]
    except ValueError:
        return [UNPARSEABLE]


def is_formatted(text: str) -> bool:
    """Whether this prompt is a format TARGET.

    `load_prompt` skips `.format` entirely when the caller passes no
    substitutions, so a pure-documentation prompt may legally contain a bare
    JSON brace -- the three `judge_*_schema` prompts do, and are loaded with no
    subs. The signal that separates them is whether the file uses any real
    placeholder at all: one `{iid}` means somebody renders this file, and from
    then on EVERY brace in it has to be doubled.
    """
    return any(PLACEHOLDER.fullmatch(f) for f in fields(text) if f)


# Prompts whose LOADER passes substitutions unconditionally, so they are format
# targets no matter what they contain. `is_formatted` cannot see this: it infers
# "somebody renders this file" from the file using a placeholder, and
# `eval/prompts.py::_mode_task` renders EVERY mode file with {workdir} whether or
# not that mode's file mentions it. The three `eval_mode_11.md` are exactly that
# case -- no placeholder today, rendered anyway -- so without this the first
# literal brace added to one of them passes CI and then raises KeyError inside
# every mode-11 run, which is the 52-cell failure this file was written for.
ALWAYS_RENDERED = re.compile(r"(?:^|/)eval_(?:common_rules|mode_\d+)\.md$")


def is_rendered(path: Path) -> bool:
    """Whether `test_a_prompt_renders` must check this file: it declares a
    placeholder, or its loader renders it regardless."""
    return (bool(ALWAYS_RENDERED.search(str(path.relative_to(PROMPTS_ROOT))))
            or is_formatted(path.read_text()))


def test_there_are_prompts_to_check():
    """Guard against the glob silently matching nothing."""
    assert len(PROMPTS) > 50


def offending(text: str) -> list[str]:
    """The brace groups `test_a_prompt_renders` would report. Shared so the
    checker's behaviour can be pinned on synthetic text as well as on the files
    that ship."""
    return [f for f in fields(text) if not f or not PLACEHOLDER.fullmatch(f)]


def test_the_undoubled_payload_brace_that_lost_52_cells_is_still_caught():
    """The defect this file exists for. If a rewrite of `fields` ever stops
    catching this, the check has gone quiet rather than green."""
    assert offending("render {iid}\npayload {gate, verdict, evidence}\n") == [
        "gate, verdict, evidence"]


def test_correctly_doubled_braces_are_not_a_defect():
    assert offending("render {iid}\npayload {{gate, verdict, evidence}}\n") == []


def test_a_placeholder_abutting_an_escaped_brace_is_not_a_defect():
    """`..._in_{scratch}}}` is `{scratch}` then a literal `}`. A checker that
    strips `}}` before scanning reads the field as `scratch\\x01` and fails a
    prompt that renders fine -- which is how a healthy ears prompt got flagged.
    """
    assert offending("path {scratch}}}\nid {iid}\n") == []


def test_a_brace_run_the_real_parser_rejects_is_reported_not_swallowed():
    """A lone `}` makes `str.format` itself raise, so it must not read as clean."""
    assert offending("render {iid} then } alone\n") == [UNPARSEABLE]


def test_the_prompt_that_lost_the_wave_is_a_format_target():
    """Pins the classification against the file that actually broke."""
    assert is_formatted((PROMPTS_ROOT / "shared" / "pbt_audit.md").read_text())


# Both PBT agent prompts hand the agent a shell and tell it to build probe
# modules, so both have to say WHERE. The audit prompt originally forbade scratch
# only inside the bundle, and agents duly left `.audit_scratch_<pid>/` probe files
# and a bare `w1.lean` in the repo root, one `git add -A` away from being
# released as benchmark artifacts. The bundle rule is enforced by G-INTEGRITY;
# the repo-root rule has nothing behind it but the prompt, so pin the prompt.
SCRATCH_PROMPTS = ["shared/pbt_port.md", "shared/pbt_audit.md"]


@pytest.mark.parametrize("rel", SCRATCH_PROMPTS)
def test_a_scratch_rule_names_the_repo_root(rel: str):
    text = re.sub(r"\s+", " ", (PROMPTS_ROOT / rel).read_text())
    assert "/tmp" in text, f"{rel} must name the directory scratch belongs in"
    assert "repo root" in text or "anywhere in the repository" in text, (
        f"{rel} tells the agent to write probe files; it must forbid the repo "
        f"root explicitly, because nothing mechanical catches a stray file there")


@pytest.mark.parametrize("rel", SCRATCH_PROMPTS)
def test_the_write_side_of_git_is_forbidden(rel: str):
    """Both PBT agents get a shell in the live working tree, which has many other
    cells mid-write in it at any moment. `git checkout .` or `git stash`
    from one agent would discard every one of them -- unrecoverable, since the
    manifests are hours of agent work that was never committed. Nothing
    mechanical stops it (the agent has Bash), so the prompt is the only control.
    """
    text = re.sub(r"\s+", " ", (PROMPTS_ROOT / rel).read_text())
    assert "git command that WRITES" in text, (
        f"{rel} must forbid write-side git: an agent running `git checkout .` "
        f"in the shared working tree destroys the other cells in flight")
    for cmd in ("checkout", "stash", "reset", "clean", "commit"):
        assert f"`{cmd}`" in text, f"{rel} should name `{cmd}` among the bans"


def test_a_mode_prompt_with_no_placeholder_is_still_checked():
    """The gap ALWAYS_RENDERED closes, pinned on the files that had it.

    `eval_mode_11.md` carries no placeholder on any backend, so the
    placeholder-inference rule skipped all three while `_mode_task` rendered them
    on every mode-11 run.
    """
    eleven = [p for p in PROMPTS if p.name == "eval_mode_11.md"]
    assert len(eleven) == 3, "expected one mode-11 prompt per verifier backend"
    for p in eleven:
        assert not is_formatted(p.read_text()), (
            "if this file now uses a placeholder the inference rule covers it "
            "and this test has stopped pinning anything -- pick another "
            "unrendered-looking mode file, do not delete the check")
        assert is_rendered(p)


@pytest.mark.parametrize("path", PROMPTS, ids=lambda p: str(p.relative_to(PROMPTS_ROOT)))
def test_a_prompt_renders(path: Path):
    text = path.read_text()
    if not is_rendered(path):
        pytest.skip("not a format target: no placeholders, so never .format'ed")
    bad = [f for f in fields(text) if not f or not PLACEHOLDER.fullmatch(f)]
    assert not bad, (
        f"{path.relative_to(PROMPTS_ROOT)} is rendered with str.format, so these "
        f"braces are read as FIELD NAMES and raise KeyError inside the agent "
        f"subprocess -- double them ({{{{ }}}}): {bad}")

