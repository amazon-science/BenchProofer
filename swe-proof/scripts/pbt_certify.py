#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Is every G-PBT record in the corpus one we would still stand behind?

`green_check.py` answers "is the cell green", which is not the same question. A
recorded pass attests to the harness that judged it, and this gate gained checks
repeatedly while the corpus was built -- the witness rule, the consistency probe,
the scope screen, the gold-side stuck-reduction screen -- each of which turned some
previously-passing cell into a defect. A corpus of green records is only as good as
the OLDEST harness any of them was judged by.

Reading the same meta.json records, this asks four things a green status cannot:

  1. was the cell judged by a harness at least as strict as the current one?
     (`code_version`, against the last commit that changed how a verdict is reached
     -- not against HEAD, which moves on every corpus checkpoint)
  2. does the battery have a reject lane at all, and did every reject case's witness
     actually get CHECKED (`witness_checked`)?
  3. which impl earned each rejection (`witness_subject`)? Where the frozen impl
     cannot decide anything that is the whole substance of the attestation; a backend
     whose verifier discharges the postcondition itself has no witness to check, so
     (2)'s witness half and (3) are skipped there and the rest of the audit still
     applies (_NO_WITNESS_BACKENDS).
  4. is the verdict one that certifies anything (SOUND), rather than an error that
     happens to be recorded?

Exit 0 only if every cell in scope clears all four. No verifier runs and no bundle
is loaded, so this is safe while waves are in flight, though a cell being re-gated
reads at whatever its last completed run said: a manifest-changed report on a cell
whose `.pbt_port.lock` is HELD is an agent mid-edit rather than corruption, and
`--only-quiescent` skips locked cells. A mismatch on an UNLOCKED cell is the real
signal, an edit that no re-gate ever followed.

Usage:
  python scripts/pbt_certify.py [--dir DIR] [--backend velvet] [--since REV]
                               [--list] [--json OUT]
"""
from __future__ import annotations

import argparse
import collections
import fcntl
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from swebench_unified.corpus_root import default_benchmark_dir  # noqa: E402

BACKENDS = ("velvet", "lean", "nagini")

# Backends whose reject cases carry no witness, so condition (3) does not apply.
#
# Nagini is the case: Viper discharges the postcondition itself, so a rejection is the
# verifier's own refusal and there is no tactic script for a reshaped impl to break.
# Reporting its reject cases against the witness rule would be a fleet of false defects.
#
# Skipping the backend is NOT the same as skipping the rule: conditions (1) harness age,
# (2) a reject lane exists at all, and (4) the record describes the manifest that ships
# are backend-independent, so nagini is in scope for those three and exempt only from
# (3). The summary says so explicitly rather than leaving a reader to infer it from an
# absent tally.
_NO_WITNESS_BACKENDS = ("nagini",)


def _rev_parse(rev: str, _cache: dict = {}) -> str | None:
    """The full hash `rev` names, or None if it names nothing.

    `--verify` matters: plain `git rev-parse <junk>` ECHOES its argument on stdout and
    only complains on stderr, so reading stdout alone reports every unresolvable revision
    as successfully resolved -- and since a version that resolves to something absent
    from the "before" set reads as CURRENT, that turns the staleness check into a rubber
    stamp.

    Memoised, because `HarnessAge.unexplained` resolves one revision per RECORD and
    `_relaxation` resolves every listed key for every judgment commit newer than it, which
    over a corpus this size is the whole cost of the check.
    """
    if rev in _cache:
        return _cache[rev]
    _cache[rev] = _rev_parse_uncached(rev)
    return _cache[rev]


def _rev_parse_uncached(rev: str) -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", "--verify", "--quiet",
                              f"{rev}^{{commit}}"], capture_output=True,
                             text=True, cwd=str(ROOT), timeout=10)
    except Exception:
        return None
    if out.returncode != 0:
        return None
    full = out.stdout.strip()
    return full if len(full) == 40 and all(c in "0123456789abcdef" for c in full) \
        else None


# The code that decides a G-PBT verdict, which is narrower than the whole gate package
# the record's content digest covers. Requiring the last commit to ANY gate would make
# every G-PBT record stale whenever an unrelated gate is edited -- a G-HYGIENE fix does
# not change what a battery proved -- and report defects no re-gate could ever clear.
#
# Split by backend, because charging a shared set to every cell fails both ways: a change
# confined to one backend's `check()` reports every other backend's cells stale, while
# leaving the backend modules OUT leaves the code that decides what a rejection IS
# uncovered -- on nagini `_no_verdict` in `backends/nagini.py` is the whole difference
# between "the spec turned this impl down" and "the front end never reached Viper".
_SHARED_JUDGMENT_PATHS = (
    "src/swebench_unified/gates/pbt.py",
    "src/swebench_unified/gates/base.py",
    "src/swebench_unified/pbt_witness.py",
    "src/swebench_unified/variant_scope.py",
    # `VerifyResult.success`, `.crashed` and `.summary`: whether a run reached a
    # verdict at all, which every reject case's outcome is read off.
    "src/swebench_unified/verify.py",
    # `no_verdict` / `no_verdict_reason`: the one home for that policy, consulted
    # by `_run_case` before it attributes a rejection to the spec.
    "src/swebench_unified/gates/_common.py",
)

# Each backend's own checker. `check()` decides accept/reject and, on nagini,
# whether the exit code means anything at all.
_BACKEND_JUDGMENT_PATHS: dict[str, tuple[str, ...]] = {
    "velvet": ("src/swebench_unified/backends/velvet.py",),
    "lean": ("src/swebench_unified/backends/lean.py",),
    "nagini": ("src/swebench_unified/backends/nagini.py",),
}


def judgment_paths(backend: str | None = None) -> tuple[str, ...]:
    """The paths that can move a G-PBT verdict for `backend`.

    With no backend, every path for every backend -- used only where the answer has to
    be backend-independent (the missing-path warning), never to age a record, since
    that is what the split exists to avoid.
    """
    if backend is None:
        every: tuple[str, ...] = ()
        for extra in _BACKEND_JUDGMENT_PATHS.values():
            every += extra
        return _SHARED_JUDGMENT_PATHS + every
    return _SHARED_JUDGMENT_PATHS + _BACKEND_JUDGMENT_PATHS.get(backend, ())

# Symbols in the paths above that decide what a run RECORDS rather than what it
# CONCLUDES, listed per file and compared per symbol.
#
# The list above is right about which files can move a G-PBT verdict, but `gates/base.py`
# is shared plumbing -- GateResult, Bundle's path accessors, the provenance stamp -- so
# whole-file comparison charges every edit to it against every G-PBT record in the corpus.
# One added `elif` branch in `Bundle.source_paths` is enough to report most of the corpus
# as "judged by an older harness" with nothing substantive behind any of it, hiding real
# staleness in the same list.
#
# The membership test is narrow: could a difference in this symbol turn a pass into a
# fail, or the reverse? A digest, a stamp field, or the set of files whose hashes are
# recorded cannot; those describe a run that has already reached its verdict. Whether a
# stamp still describes the artifact on disk is a real question, but it belongs to
# `check_stamp_freshness.py`, which answers it by content rather than by history.
#
# Everything not named here invalidates, including a symbol added later: the default has
# to be "this could matter", because the point of the check is to certify positively.
_PROVENANCE_ONLY: dict[str, frozenset[str]] = {
    "src/swebench_unified/gates/base.py": frozenset({
        "Bundle.source_paths",       # which files' digests get recorded
        "source_digests",
        "_harness_digest",
        "_cached_harness_digest",
        "_code_version",
        "stamp",                     # writes mode/version onto a finished result
        "GateResult.to_json",        # serialisation of a decided verdict
        "_HARNESS_FILES",            # which files feed the harness digest
        "Sequence",                  # imported for an annotation, never called
    }),
    "src/swebench_unified/gates/pbt.py": frozenset({
        "reads",                     # which bundle files get digested into the record
        # The gold-side signature and everything that shapes it. This family produces
        # exactly one thing: the `gold_signature` string on a case ALREADY decided, and
        # nothing reads it back to decide anything (`_stuck_screen`, which does decide,
        # scans the whole log with its own patterns and shares no state with these). So
        # no difference here can turn a pass into a fail, the membership test above.
        #
        # It is listed because the field is one an audit READS, so it gets improved --
        # the signature window has been widened more than once, to keep the `⊢` line an
        # `unsolved goals` context would otherwise push out of the record. Without this
        # entry each improvement charges itself against every passing reject case in the
        # corpus as "judged by an older harness".
        "_gold_signature",
        "_first_goal",
        "_capped",
        "_DIAGNOSTIC_HEAD",
        "_SIGNATURE_MAX_LINES",
        "_SIGNATURE_MAX_CHARS",
        "_GOAL_LINE",
        "_GOAL_SCAN_LINES",
    }),
}

# How far back to look for a behavioural change before giving up and requiring
# the newest touching commit. Generous: the cost is a few `git show` calls.
_HISTORY_LIMIT = 80


def _code_only(src: str) -> str | None:
    """`src` normalised to its executable content: no comments, no docstrings.

    Two revisions with equal normalisations cannot reach different verdicts, so a
    commit that only moves prose is not a change in the judgment rule. None if the
    source does not parse, which is treated as a change.
    """
    import ast
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef,
                                 ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body = node.body
        if (body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            node.body = body[1:] or [ast.Pass()]
    return ast.dump(ast.fix_missing_locations(tree))


def _cap_independent(data: dict, _backend: str | None = None) -> bool:
    """True when no case in this record could have been decided by the CAP.

    A case that reached `verified` or `rejected` reached a verdict, and raising the
    verifier's time limit cannot change it; anything inconclusive, undecided or malformed
    might have gone either way with more time, so it is not exempt.
    """
    cases = data.get("cases") or []
    if not cases:
        return False
    return all(str(c.get("outcome") or "").startswith(("verified", "rejected"))
               for c in cases)


def _no_loop_unification(data: dict, _backend: str | None = None) -> bool:
    """True when no case in this record hit the shape a widened screen caught.

    The screen fires only when a gold-side log carries the un-normalised loop term BELOW,
    and it is the term rather than the headline that makes the shape specific, so a record
    no case of which mentions it cannot have been read differently.

    LIMIT, stated because it bounds the strength of the exemption: a record keeps the FIRST
    diagnostic of gold's failure (see `_gold_signature` in gates/pbt.py) while the screen
    reads the whole log, so a log carrying the term only in a later diagnostic is invisible
    here. For this shape the term and the mismatch headline appear together in the first
    diagnostic.
    """
    cases = data.get("cases") or []
    if not cases:
        return False
    return not any("forIn Lean.Loop.mk" in json.dumps(c) for c in cases)


def _every_case_judged(data: dict, _backend: str | None = None) -> bool:
    """True when every case in this record reached a verdict.

    Distinct from `_cap_independent` despite testing the same thing, because the property
    claimed differs: the commit this serves re-LABELS the lane where NO verdict was reached,
    so a record with nothing in that lane is not describable by it. A case that came back
    `verified` or `rejected` reached a verdict, and the re-labelling is unreachable from
    there -- `_run_case` returns at the no-verdict branch before any of it.
    """
    cases = data.get("cases") or []
    if not cases:
        return False
    return all(str(c.get("outcome") or "").startswith(("verified", "rejected"))
               for c in cases)


def _not_nagini(_: dict, backend: str | None = None) -> bool:
    """True for a backend a nagini-only screen cannot have judged differently.

    Distinct from `_always`: the commit this serves IS a real strictening, just not for
    every backend. Where it does bite there is no exemption, and an unknown backend gets
    none either -- `None` means the caller did not say, and "cannot tell" has to fail.
    """
    return backend in ("velvet", "lean")


def _always(_: dict, _backend: str | None = None) -> bool:
    """A commit whose own diff is the evidence: it moves no verdict for any record.

    Reserved for a pure refactor -- code moved between functions with the calls composed
    back to the same sequence of the same rules. No record could distinguish the two
    revisions, so there is nothing for a record to exhibit and the entry's reason has to name
    the mechanical fact and be re-checkable from the diff it cites. Anything with an
    observable behaviour change wants a real predicate instead.
    """
    return True


# Judgment-code commits a pre-existing verdict survives, with the property that makes
# it survive.
#
# Recency is not strictness, and this check asks about strictness: a commit that RAISES a
# resource cap makes the harness more permissive, so a pass measured under the smaller cap
# was measured under a stricter rule and still stands. The exemption is not taken on the
# operator's word -- each entry carries a predicate over the RECORD's own data, so a cell
# claims it only by exhibiting the evidence. The one exception is `_always`, for a refactor
# no record could distinguish; read its docstring first.
#
# What does NOT belong here is a real strictening. A rule that turns a verdict a weaker
# harness reached into a defect can only be answered by re-running the gate, and an entry
# that waved one through would make every green cell downstream of it green on the strength
# of this comment. `7528fffd3` (a checker that reached no verdict is not a rejection) is
# exactly that, which is why it is absent: the records that predate it need a G-PBT
# re-gate, not an exemption.
#
# Keys are whatever `git rev-parse` resolves; abbreviated is fine.
_RELAXATIONS: dict[str, tuple[str, Callable[..., bool]]] = {
    "02d313c2c": (
        "G-PBT honours the cell's declared verifier cap, and only ever raises "
        "it (max() against the env value), so a record whose every case reached "
        "a verdict cannot have been decided by the cap",
        _cap_independent,
    ),
    "03aec8250": (
        "widens the loop-unification stuck screen to Lean's second headline for "
        "the same shape; the screen still requires the loop term, so a record no "
        "case of which mentions it reads identically under both",
        _no_loop_unification,
    ),
    "e39159f8d": (
        "adds `no_verdict_reason` and `worst_no_verdict` to `gates/_common.py` so "
        "that G-DIFF, G-GOLD and G-MUT can say WHY a check reached no verdict. "
        "The diff to `_common.py` is purely additive -- it appends two functions "
        "after `no_verdict` and deletes no line of any existing one (git show "
        "e39159f8d -- src/swebench_unified/gates/_common.py) -- and `gates/pbt.py` "
        "at that revision imports `check_bundle_source, env_int, no_verdict` and "
        "names neither new helper (git show e39159f8d:src/swebench_unified/gates/"
        "pbt.py), so no G-PBT judgment can read differently across it. `_common.py` "
        "is in `_PBT_JUDGMENT_PATHS` because a change to a function G-PBT DOES call "
        "moves its verdicts, and that stays the rule; this commit changes no such "
        "function. The lane that this commit does re-decide is the three gates it "
        "names, and their records are certified elsewhere. Unconditional: the "
        "argument is about which code exists, not about what any record contains",
        _always,
    ),
    "43c6680f6": (
        "a nagini front-end failure stops reading as a verification rejection. "
        "The whole screen is `no_verdict_detail`, which `VerifyResult` defaults "
        "empty and only `backends/nagini.py` ever sets, so on velvet and lean "
        "`.crashed` and `.summary` return exactly what they returned before "
        "(git diff 43c6680f6^ 43c6680f6 -- src/swebench_unified/verify.py). "
        "NAGINI GETS NO EXEMPTION and none is available: pre-fix the summary "
        "was 'verification failed' whether or not Viper had announced anything, "
        "so no field in the record distinguishes the two. Those 488 records need "
        "a G-PBT re-gate",
        _not_nagini,
    ),
    "04f40c77e": (
        "extract-method only: `unsound_evasions` is lifted out of "
        "`variant_problems`, which now calls it between the same same_spec check "
        "and the same new-declaration rule, in that order, with the rule bodies "
        "moved verbatim -- so the composed function is the one that judged these "
        "records (git diff 04f40c77e^ 04f40c77e -- src/swebench_unified/"
        "variant_scope.py). The split exists so the AUDIT lane can allow a helper "
        "lemma a battery variant may not, and that caller is not this gate",
        _always,
    ),
    "7a7f4fdad": (
        "splits the no-verdict lane in two: a verifier that REFUSED to judge is "
        "spelled `no-verdict` and verdict NO-VERDICT instead of `inconclusive` "
        "and TIMED-OUT, so the record stops prescribing a cap raise for something "
        "no cap can fix. Every edit is inside that lane -- the four `no_verdict(r)` "
        "branches, which return before any case can be called verified or "
        "rejected -- and both spellings remain `not ok`, in `_INCONCLUSIVE`, and "
        "an error rather than SOUND, so a record whose every case reached a "
        "verdict reads identically under both revisions. NO exemption for a record "
        "that HAS an unjudged case: whether that case was a cap hit or a "
        "front-end failure is what the commit re-decides, and the pre-fix detail "
        "string is the harness's own guess at it, so the record cannot answer for "
        "itself. Those need a G-PBT re-gate",
        _every_case_judged,
    ),
    "1a7cf00d8": (
        "adds `VerifyResult.front_end_refusal` so that an ATTACK the checker could "
        "not translate stops being scored as a rejection the spec performed. The "
        "diff to the only judgment path it touches is purely ADDITIVE -- 32 "
        "insertions, zero deletions, one new property appended after `crashed` "
        "(git show 1a7cf00d8 -- src/swebench_unified/verify.py) -- so `success`, "
        "`timed_out`, `crashed`, `sorry_only`, `summary` and `no_verdict_detail`, "
        "which are the fields every reject case's outcome is read off, are the "
        "same code that judged these records. No file in any judgment path names "
        "the new property (checked over gates/, pbt_witness.py, variant_scope.py "
        "and all three backends), so no G-PBT judgment can consult it. The lane "
        "the commit does re-decide is `adversary.check_attack`, which is the "
        "G-EQ / G-PANEL-1 primitive and is not in `judgment_paths` at all; those "
        "records were re-derived instead, and say so in the record: the 29 "
        "affected captions read `not a counterexample (the checker could not "
        "translate this ...)` rather than the pre-fix rejection. "
        "Unconditional: the argument is about which code exists, not about what "
        "any record contains",
        _always,
    ),
    "120317cd9": (
        "adds a flavor dispatch guard to `variant_scope.py` and edits prose "
        "everywhere else. The three other judgment paths it touches change no "
        "executable line at all -- `gates/pbt.py`, `gates/_common.py` and "
        "`backends/nagini.py` are docstring and comment text only (git diff "
        "120317cd9^ 120317cd9 -- src/swebench_unified/gates/pbt.py "
        "src/swebench_unified/gates/_common.py "
        "src/swebench_unified/backends/nagini.py). In `variant_scope.py` the "
        "guard raises for a flavor outside `_KNOWN_FLAVORS = ('lean', 'python', "
        "'ears')`, where falling through used to return the empty list that means "
        "ADMISSIBLE; for each of those three flavors the rewritten dispatches "
        "compose back to the same answer -- `_decl_names` and `_axiom_names` "
        "return the same lean scan and the same `set()` for python and ears that "
        "`flavor != 'lean'` returned, and `unsound_evasions` gains only the "
        "membership test it passes -- so no bundle in any corpus this repo builds "
        "can read differently (git diff 120317cd9^ 120317cd9 -- "
        "src/swebench_unified/variant_scope.py). The lane the commit does "
        "re-decide is a FOURTH flavor, which no record has. Unconditional: the "
        "argument is about which flavors exist, not about what any record contains",
        _always,
    ),
    "84cb32576": (
        "adds `frozen_dataset_complaint` to `gates/base.py` so that a run over a "
        "corpus whose frozen dataset was never fetched refuses with the reason "
        "instead of degrading one row at a time. The diff to the only judgment "
        "path it touches is purely ADDITIVE -- 26 insertions, zero deletions, one "
        "new function appended after `load_frozen_row` (git show --numstat "
        "84cb32576 -- src/swebench_unified/gates/base.py) -- and no file in any "
        "judgment path names it at that revision (checked over gates/, "
        "pbt_witness.py, variant_scope.py, verify.py and all three backends: the "
        "only mention anywhere is its own definition). Its callers are "
        "`release_gate.py` and `check_stamp_freshness.py`, neither of which is a "
        "judgment path, so no G-PBT judgment can consult it. NOT eligible for "
        "`_PROVENANCE_ONLY` instead: a precondition that refuses to run is not a "
        "provenance field, and exempting the symbol by name would keep exempting "
        "it if a judgment path ever did call it. Unconditional: the argument is "
        "about which code exists, not about what any record contains",
        _always,
    ),
    "49a48fd3f": (
        "moves the default SCRATCH DIRECTORY of `verify_source_via` from "
        "`PROJECT_ROOT / \"experiments\" / \"scratch\"` to `EXPERIMENTS_ROOT / "
        "\"scratch\"`. That one line, plus the name added to the `.paths` import, "
        "is its only executable edit to any judgment path (git show 49a48fd3f -- "
        "src/swebench_unified/verify.py). `paths.EXPERIMENTS_ROOT` IS "
        "`PROJECT_ROOT / \"experiments\"` unless SBU_EXPERIMENTS_DIR is set, so "
        "with the variable unset -- which is how every record in this corpus was "
        "produced -- both revisions build the same string and no run can tell "
        "them apart. Where a check runs is also not a rule it applies: the file "
        "is written, checked and read the same way from either directory, "
        "measured on all three backends against pydata__xarray-3305 with "
        "SBU_EXPERIMENTS_DIR pointed outside the checkout (lean, velvet and "
        "nagini each `verified`). Unconditional: the argument is about which path "
        "the code builds, not about what any record contains",
        _always,
    ),
}


def _symbol_bodies(src: str) -> dict[str, str] | None:
    """`src` split into one normalised body per named symbol.

    Keys are `func`, `Class`, `Class.method`; the class key covers the class's own
    statements only, so a method edit does not read as an edit to every sibling. Bodies
    are normalised the way `_code_only` normalises a file -- docstrings and comments
    stripped -- so a prose scrub is not a change.

    A module-level statement that BINDS A NAME is keyed by that name, and an `import` is
    split one key per alias so that adding a name to a shared import line does not read as
    a change to the names already on it. `"<module>"` holds what is left -- loose
    expressions, conditionals, `sys.path` surgery -- in one lump deliberately: an unnamed
    statement cannot be excluded by name, so it always invalidates.

    None if the source does not parse, which the caller treats as a change.
    """
    import ast

    def strip_prose(node):
        for n in ast.walk(node):
            if not isinstance(n, (ast.Module, ast.FunctionDef,
                                  ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            body = n.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                n.body = body[1:] or [ast.Pass()]
        return node

    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    _DEF = (ast.FunctionDef, ast.AsyncFunctionDef)
    out: dict[str, str] = {}
    loose: list = []
    for node in tree.body:
        if isinstance(node, _DEF):
            out[node.name] = ast.dump(strip_prose(node))
        elif isinstance(node, ast.ClassDef):
            own = []
            for sub in node.body:
                if isinstance(sub, _DEF):
                    out[f"{node.name}.{sub.name}"] = ast.dump(strip_prose(sub))
                else:
                    own.append(sub)
            # The class shorn of its methods: bases, decorators, class-level
            # assignments. A dataclass field added here is a real change.
            shell = ast.ClassDef(name=node.name, bases=node.bases,
                                 keywords=node.keywords, body=own or [ast.Pass()],
                                 decorator_list=node.decorator_list)
            # `type_params` only exists from 3.12, and ast.dump reads whatever the
            # node carries -- so copy it across when the running interpreter has
            # it rather than passing it to a constructor that may not accept it.
            if hasattr(node, "type_params"):
                setattr(shell, "type_params", getattr(node, "type_params"))
            out[node.name] = ast.dump(strip_prose(ast.fix_missing_locations(shell)))
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            base = getattr(node, "module", None) or ""
            level = getattr(node, "level", 0) or 0
            for alias in node.names:
                bound = alias.asname or alias.name.split(".")[0]
                out[bound] = f"import {'.' * level}{base}:{alias.name}"
        else:
            named = _bound_names(node)
            if named:
                dump = ast.dump(strip_prose(node))
                for nm in named:
                    out[nm] = dump
            else:
                loose.append(node)
    mod = ast.Module(body=loose, type_ignores=[])
    out["<module>"] = ast.dump(strip_prose(ast.fix_missing_locations(mod)))
    return out


def _bound_names(node) -> list[str]:
    """The plain top-level names a module-level statement binds, if any.

    Only simple `Name` targets count. A subscript or attribute target (`TABLE["k"] = ...`)
    mutates something declared elsewhere and so is left in the `<module>` lump, where it
    always invalidates -- the conservative side.
    """
    import ast
    targets: list = []
    if isinstance(node, ast.Assign):
        targets = list(node.targets)
    elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
        targets = [node.target]
    else:
        return []
    out: list[str] = []
    for t in targets:
        if isinstance(t, ast.Name):
            out.append(t.id)
        elif isinstance(t, (ast.Tuple, ast.List)):
            for el in t.elts:
                if isinstance(el, ast.Name):
                    out.append(el.id)
                else:
                    return []      # unpacking into a subscript: not nameable
        else:
            return []
    return out


def _verdict_relevant_change(path: str, old: str | None, new: str | None) -> bool:
    """Did `path` change in a way that could move a G-PBT verdict?

    A file with no per-symbol exclusions is compared whole, keeping the common case as strict
    as before. For a file that has them the changed symbols are computed and the excluded ones
    dropped; anything left -- including an unparseable revision, on either side -- invalidates.
    """
    exclude = _PROVENANCE_ONLY.get(path)
    if not exclude:
        return _code_only(new or "") != _code_only(old or "")
    a, b = _symbol_bodies(old or ""), _symbol_bodies(new or "")
    if a is None or b is None:
        return True
    changed = {k for k in set(a) | set(b) if a.get(k) != b.get(k)}
    return bool(changed - exclude)


def _blob(rev: str, path: str) -> str | None:
    out = subprocess.run(["git", "show", f"{rev}:{path}"], capture_output=True,
                         text=True, cwd=str(ROOT), timeout=20)
    return out.stdout if out.returncode == 0 else None


def _last_harness_commit(backend: str | None = None) -> str:
    """The newest commit that changed how a G-PBT verdict is REACHED, for `backend`.

    Each qualification below closes a false-alarm channel that makes the check
    unusable at corpus scale:

    * not `HEAD`, which moves every time a driver checkpoints a gate stamp -- the corpus
      is committed on a timer while the fleet runs -- so requiring it reports every
      record as stale minutes after it was written, the checkpoint's own record included.
    * not every gate. Only the paths above can move a G-PBT verdict, and charging an edit
      to a sibling gate flags records no re-gate could clear, since re-gating does not
      change the commit history.
    * not every edit to those paths: a commit that only rewrites comments and docstrings
      cannot change a verdict. Commits are walked newest-first and the first with a real
      code difference wins.
    * not every code edit either. `gates/base.py` is shared plumbing, and an edit to the
      part of it that decides what a run RECORDS cannot change what the run concluded;
      those symbols are named in `_PROVENANCE_ONLY` and compared individually.
    * not one answer for every backend. `backend` selects the path set
      (`judgment_paths`), so a change to one checker ages that backend's records and
      leaves the others alone.

    Falls back to the newest touching commit (then `HEAD`) when the question cannot be
    answered, because the failure direction that matters is reporting a stale record as
    current.
    """
    paths = judgment_paths(backend)
    missing = [p for p in paths if not (ROOT / p).exists()]
    if missing:                      # the list drifted; do not silently narrow
        print(f"# warning: judgment path(s) missing, staleness may be "
              f"understated: {missing}")
    revs = _judgment_commits(paths)
    if revs is None:
        return "HEAD"
    if revs:
        return revs[0]
    touched = _touching_commits(paths)
    if not touched:
        return "HEAD"
    print(f"# note: no behavioural change to the judgment code in the last "
          f"{len(touched)} commit(s) that touched it; requiring {touched[-1][:9]}")
    return touched[-1]


def _touching_commits(paths: tuple[str, ...]) -> list[str]:
    """Commits touching the judgment paths at all, newest first."""
    try:
        out = subprocess.run(["git", "log", f"-{_HISTORY_LIMIT}", "--format=%H",
                              "--", *paths], capture_output=True,
                             text=True, cwd=str(ROOT), timeout=30)
    except Exception:
        return []
    return out.stdout.split() if out.returncode == 0 else []


def _judgment_commits(paths: tuple[str, ...],
                      _cache: dict = {}) -> list[str] | None:
    """Every commit that changed how a G-PBT verdict is reached, newest first.

    The whole list rather than only the newest, because a record is certified against the
    changes that landed AFTER it, and some of those may be relaxations it provably survives
    (see `_RELAXATIONS`). None when git cannot be consulted at all, which the caller turns
    into requiring HEAD.

    Memoised per path set, not globally: the backends ask different questions and a single
    cache would answer all of them with whichever ran first -- silently, and in the
    direction that certifies records no one checked.
    """
    key = paths
    if key in _cache:
        return _cache[key]
    touched = _touching_commits(paths)
    if not touched:
        _cache[key] = None if not _rev_parse("HEAD") else []
        return _cache[key]
    found: list[str] = []
    for rev in touched:              # newest first
        for path in paths:
            new, old = _blob(rev, path), _blob(f"{rev}^", path)
            if new == old:
                continue             # untouched by this commit
            if _verdict_relevant_change(path, old, new):
                found.append(rev)
                break
    _cache[key] = found
    return found


def _ancestors(rev: str) -> set[str]:
    """Full hashes of every commit reachable from `rev`."""
    try:
        out = subprocess.run(["git", "rev-list", rev], capture_output=True,
                             text=True, cwd=str(ROOT), timeout=60)
    except Exception:
        return set()
    return set(out.stdout.split())


def _ancestors_of(rev: str, _cache: dict = {}) -> set[str]:
    """`_ancestors`, memoised: a handful of distinct stamped versions, 1000 cells."""
    if rev not in _cache:
        _cache[rev] = _ancestors(rev)
    return _cache[rev]


class HarnessAge:
    """Whether a record's `code_version` predates a required harness revision.

    `code_version` is `git describe --always --dirty`, an ABBREVIATED hash, while
    `rev-list` prints full ones, so the two cannot be compared directly -- doing so
    silently reports every record as current, the failure direction that matters. Each
    distinct stamped version is resolved through `git rev-parse` once and then tested for
    membership in the set of commits STRICTLY BEFORE the required revision. An
    unresolvable version (a commit from a rebased branch, say) is treated as stale: the
    point of the check is to certify positively, so "cannot tell" has to fail.
    """

    def __init__(self, since: str, backend: str | None = None) -> None:
        self.required = _rev_parse(since)
        self.usable = bool(self.required)
        self.backend = backend
        self.paths = judgment_paths(backend)
        self._before: set[str] = set()
        if self.required and _rev_parse(f"{self.required}^"):
            self._before = _ancestors(f"{self.required}^")
        self._cache: dict[str, bool] = {}

    def is_stale(self, version: str) -> bool:
        if not self.usable or not self._before:
            return False
        short = version.split("-")[0].strip()
        if not short:
            return True
        if short not in self._cache:
            full = _rev_parse(short)
            self._cache[short] = (full in self._before) if full else True
        return self._cache[short]

    def unexplained(self, version: str, data: dict) -> list[str]:
        """Judgment changes newer than `version` that this record does not survive.

        Empty means the record is as good as one judged today: every change that landed
        after it is a listed relaxation whose predicate the record's own data satisfies.
        A record whose version cannot be resolved gets no exemption, because the set of
        changes newer than it is unknown.
        """
        commits = _judgment_commits(self.paths) or []
        short = version.split("-")[0].strip()
        full = _rev_parse(short) if short else None
        if not full:
            return [c for c in commits] or ["(unresolvable version)"]
        newer = [c for c in commits if c not in _ancestors_of(full)]
        out = []
        for c in newer:
            entry = self._relaxation(c)
            if entry is None or not entry[1](data, self.backend):
                out.append(c)
        return out

    @staticmethod
    def _relaxation(full_rev: str):
        for key, entry in _RELAXATIONS.items():
            if _rev_parse(key) == full_rev:
                return entry
        return None


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def held(bundle: Path) -> bool:
    """Whether a driver holds this cell's port/audit lock right now.

    Non-blocking, and it releases immediately: this only asks, it never waits, so it
    cannot make a live wave contend on a cell. A cell with no lock file has never been
    worked, which is not held.
    """
    lock = bundle / ".pbt_port.lock"
    if not lock.is_file():
        return False
    try:
        with lock.open("r+") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return False
    except BlockingIOError:
        return True
    except OSError:
        return False


def audit_cell(meta: Path, age: HarnessAge | None) -> list[str]:
    """Every reason this cell's G-PBT record does not certify its battery."""
    try:
        m = json.loads(meta.read_text())
    except (OSError, ValueError) as e:
        return [f"meta.json unreadable: {type(e).__name__}"]
    g = (m.get("gates") or {}).get("G-PBT")
    if not isinstance(g, dict) or not g.get("checked_at"):
        return ["no G-PBT record"]
    if g.get("status") != "pass":
        data = g.get("data") or {}
        return [f"not passing: {data.get('verdict') or g.get('status')}"]

    problems: list[str] = []
    data = g.get("data") or {}
    # (1) judged by a harness that predates the current rule -- unless every rule
    # change since is one this record provably survives.
    version = str(g.get("code_version") or "")
    if age is not None and age.is_stale(version):
        unexplained = age.unexplained(version, data)
        if unexplained:
            problems.append(f"judged by an older harness ({version or 'unstamped'}"
                            f"), superseded by {unexplained[0][:9]}")

    cases = data.get("cases") or []
    if not cases:
        problems.append("passing record with no cases")
        return problems

    # (2) a battery with no reject lane certifies nothing about spec STRENGTH.
    # The gate refuses these itself (NO-REJECT-LANE), so a passing record with no
    # reject case means the record predates that rule.
    rejects = [c for c in cases if c.get("expect") == "reject"]
    if not rejects:
        problems.append("no expect='reject' case (cannot certify spec strength)")

    # (4) the record must describe the manifest that SHIPS: the audit lane edits
    # properties.py, so a record written before an edit describes cases that no longer
    # exist. Records predating the digest are left to the harness-version check above.
    recorded = str(data.get("manifest_sha256") or "")
    if recorded:
        actual = _sha256(meta.parent / "properties.py")
        if not actual:
            problems.append("record judged a manifest that is no longer present")
        elif actual != recorded:
            problems.append("properties.py changed after the gate ran "
                            f"(judged {recorded[:12]}, on disk {actual[:12]})")

    # (3) every rejection must have been earned by a CHECKED witness -- on the
    # backends that have witnesses at all (see _NO_WITNESS_BACKENDS). The failing-
    # case clause is NOT part of that exemption: "a passing record that contains a
    # case which did not pass" is incoherent whatever discharges the obligation.
    witnessed = meta.parent.name not in _NO_WITNESS_BACKENDS
    for c in rejects:
        if not c.get("ok"):
            problems.append(f"{c.get('id')}: recorded pass with a failing case")
        elif witnessed and not c.get("witness_checked"):
            problems.append(f"{c.get('id')}: rejection with no witness check")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=default_benchmark_dir(),
                    help="corpus root (default: SBU_BENCHMARK_DIR, else benchmark/)")
    ap.add_argument("--backend", action="append", choices=BACKENDS,
                    help="repeatable; default every backend in BACKENDS")
    ap.add_argument("--since", default=None,
                    help="a revision whose harness changes every record must "
                         "have been judged by (default: the last commit that "
                         "touched the judgment code)")
    ap.add_argument("--no-version-check", action="store_true",
                    help="audit only the record CONTENT, ignoring which harness "
                         "produced it")
    ap.add_argument("--list", action="store_true",
                    help="name every cell that does not certify")
    ap.add_argument("--only-quiescent", action="store_true",
                    help="skip cells a driver holds right now, so the report is "
                         "about the corpus rather than the fleet's timing")
    ap.add_argument("--json", default=None, help="write the full report here")
    args = ap.parse_args()

    root = Path(args.dir)
    if not root.is_dir():
        print(f"no such benchmark dir: {root}")
        return 2

    def age_for(backend: str) -> HarnessAge | None:
        """This backend's required revision.

        One per backend, because `judgment_paths` differs: a change to one checker must
        age that backend's records and leave the others alone. A shared age would either
        charge every cell for a one-backend screen or miss it entirely.
        """
        if args.no_version_check:
            return None
        since = args.since or _last_harness_commit(backend)
        a = HarnessAge(since, backend)
        if not a.usable:
            print(f"# warning: cannot resolve {since!r} for {backend}; "
                  "skipping the harness-version check there")
            return None
        print(f"# {backend:8s} harness revision required: {str(a.required)[:9]}"
              f"{'' if args.since else ' (last judgment-code change for it)'}")
        return a

    report: dict = {"required_rev": {}, "backends": {}}
    rc = 0
    requested = args.backend or list(BACKENDS)
    empty = []
    for backend in requested:
        metas = sorted(root.glob(f"*/{backend}/meta.json"))
        if not metas:
            # A corpus legitimately holds only some backends (a port often starts
            # with one), so an absent backend is a note. Every requested backend
            # absent is not: the default root is `benchmark/`, which ships empty,
            # and silence plus exit 0 there reads as "certified" over a corpus
            # the caller never named. Refused below.
            empty.append(backend)
            continue
        age = age_for(backend)
        report["required_rev"][backend] = age.required if age else None
        bad: dict[str, list[str]] = {}
        subjects: collections.Counter = collections.Counter()
        busy = 0
        for meta in metas:
            iid = meta.parent.parent.name
            if args.only_quiescent and held(meta.parent):
                busy += 1
                continue
            problems = audit_cell(meta, age)
            if problems:
                bad[iid] = problems
            try:
                g = (json.loads(meta.read_text()).get("gates") or {})["G-PBT"]
                for c in (g.get("data") or {}).get("cases") or []:
                    if c.get("witness_checked"):
                        subjects[c.get("witness_subject") or "(unrecorded)"] += 1
            except Exception:
                pass
        # A skipped cell is NOT a certified one. Folding `busy` into `ok` would
        # make the number go UP as more of the corpus became unreadable, which is
        # the direction this tool must never fail in.
        ok = len(metas) - len(bad) - busy
        print(f"{backend:8s} {ok}/{len(metas)} certified"
              + (f"   {len(bad)} NOT certified" if bad else "")
              + (f"   {busy} skipped (held by a driver)" if busy else ""))
        if backend in _NO_WITNESS_BACKENDS:
            # Said out loud, because an empty witness tally on this backend would
            # otherwise read as "no rejection was witnessed" -- a defect -- when
            # it means "this backend's rejections are not witness-shaped".
            print(f"           (witness rule not applicable: {backend} rejections "
                  f"are discharged by the verifier, not by a tactic script)")
        for subj, n in subjects.most_common():
            print(f"           {n:5d} rejection(s) refuted against {subj}")
        if args.list:
            for iid, problems in sorted(bad.items()):
                print(f"  {iid:38s} {problems[0]}")
                for p in problems[1:]:
                    print(f"  {'':38s} {p}")
        report["backends"][backend] = {"cells": len(metas), "certified": ok,
                                       "skipped_busy": busy,
                                       "not_certified": bad,
                                       "subjects": dict(subjects)}
        if bad:
            rc = 1
    if empty == requested:
        print(f"no {'/'.join(requested)} bundle(s) under {root}: nothing was "
              f"certified. Name the corpus with --dir or SBU_BENCHMARK_DIR "
              f"(the shipped corpora are benchmark-verified/ and benchmark-pro/)")
        return 2
    for backend in empty:
        print(f"# {backend:8s} no bundles under {root}; not certified, not judged")
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2, sort_keys=True))
        print(f"# report -> {args.json}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
