#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Check that every recorded gate verdict still describes the files it judged.

A gate record carries `sources`: the sha256 of each bundle file the gate read
(`gates/base.source_digests`). This script recomputes them. A mismatch means the
artifact was edited after the gate ran, so the recorded verdict -- including a green
one -- is about a file that no longer exists in that form. Timestamps cannot answer
that: any tree-wide operation (a merge, a checkout) rewrites mtimes without changing a
byte, and a driver that rewrites a file with identical content bumps the mtime too.
Content is the only honest evidence.

Records written before digests existed have no `sources`, and are reported as
UNVERIFIABLE rather than silently accepted: "we cannot check this one" is a different
claim from "this one is fine". Some can still be decided BY CONTENT, because G-HYGIENE
records the sha256 of every marked region and of the spec view and a mechanized audit
role retains its positive control, so recomputing from the solution on disk asks the
same question the digests ask. Those come out as mismatches rather than as
unverifiable: a recomputed hash that disagrees is proof, not an absence of proof.

`--certify-unchanged` answers the same question a second way for the rest, the
alternative being to re-run an audit agent over most of the corpus to obtain digests for
bytes nobody has edited: a record with no digests still describes the shipped bytes if
nothing has written those bytes since, and `certify_cell` holds the independent ways to
establish that. Note the direction -- a timestamp is only ever used to show that nothing
happened, and a record that fails every proof is UNCERTIFIED, which means "not shown"
and never "changed". Certification is also per gate, against what that gate declares it
reads, so a faithfulness verdict is not questioned by a battery it never looked at; and
it is reported rather than stamped, because `sources` must keep meaning "the gate
computed these".

WHAT THIS FILE DOES NOT DECIDE. Every proof here answers "are these the same bytes",
the right question for a gate whose verdict is about the bytes it ran and the wrong one
for an audit, whose conclusion is about the SPECIFICATION those bytes carry. So audit
records (`_AUDIT_GATES`) are DEFERRED to `scripts/audit_freshness.py`, which decides
them by `markers.spec_signature`. Deferred is not silence: the release gate runs that
tool as a required check, this one prints how many records it deferred, and the two
findings a content check CAN make about an audit -- a positive control that lost a
clause, a recorded artifact that is gone -- are still reported here.

TWO PRECONDITIONS, both measured rather than assumed. The frozen dataset must be
fetched and must be the one this corpus was built from, because it is the only proof
for `instance.json` and `patch.diff`; without it a fresh checkout loses ~900 of the
verified corpus's records to a fallback that cannot carry them, so this exits 2 with
that reason instead of printing a count. And of the two timestamp proofs, mtime is
HOST-LOCAL: `git clone` resets every mtime, so a record that rests on it alone is
certified here and uncertified for anybody else. That count is printed, with the
re-gate that turns those records into digest-carrying ones.

WHICH REPOSITORY THE GIT PROOF COMES FROM: the one that CONTAINS the corpus, resolved
from the corpus path (`GitDates.for_corpus`), never this checkout. `--benchmark-dir`
and `SBU_BENCHMARK_DIR` both accept a corpus anywhere on disk and a published corpus
is its own repository, so anchoring here would date the artifacts of one tree while
reading another. A corpus no repository holds has NO history to offer, which is an
answer rather than an error and is fail-closed: those records lose the git proof and
come out `uncertified`, never certified by an absence of commits.

    python scripts/check_stamp_freshness.py --benchmark-dir <corpus> --strict
    python scripts/check_stamp_freshness.py --certify-unchanged --out cells.tsv

Exit 0 iff no record MISMATCHES; with --strict, iff none mismatch and none are
unverifiable, which is what `--certify-unchanged` makes achievable on a corpus
whose older records carry no digests. Exit 2 if a precondition fails.
"""
from __future__ import annotations

import argparse
import collections
import dataclasses
import functools
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from swebench_unified.corpus_root import default_benchmark_dir  # noqa: E402


def digest(p: Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None


def locate(cell: Path, fname: str) -> Path | None:
    """The file a `sources` key names, or None if it is really gone.

    `source_digests` keys by BASENAME, and not every file a gate reads lives in the
    cell: the task record is shared by all backends and sits one level up. Looking only
    in the cell would report that shared record as VANISHED for every cell whose gates
    read it.
    """
    for base in (cell, cell.parent):
        p = base / fname
        if p.is_file():
            return p
    return None


def check_cell(cell: Path, gates: set[str] | None) -> list[tuple[str, str, str]]:
    """(gate, filename, kind) for every record whose sources no longer match.

    kind: "changed" (digest differs), "vanished" (recorded file is gone),
    "unverifiable" (a real verdict carrying no digests at all).
    """
    try:
        meta = json.loads((cell / "meta.json").read_text())
    except (OSError, ValueError):
        return []
    out: list[tuple[str, str, str]] = []
    for name, rec in sorted((meta.get("gates") or {}).items()):
        if gates and name not in gates:
            continue
        if not isinstance(rec, dict) or rec.get("status") not in ("pass", "fail", "relaxed"):
            continue
        srcs = rec.get("sources")
        if not isinstance(srcs, dict) or not srcs:
            # No digests, but a record can still bind itself to content: G-HYGIENE by
            # its region hashes, a mechanized audit role by the positive control it
            # retained. Either one makes the record decidable rather than unverifiable.
            moved = region_mismatch(cell, rec)
            if not moved and name in _CONTROL_GATES:
                moved = control_weakened(cell, name)
            if moved:
                out.append((name, moved, "changed"))
            else:
                out.append((name, "-", "deferred" if name in _AUDIT_GATES
                            else "unverifiable"))
            continue
        for fname, want in sorted(srcs.items()):
            found = locate(cell, fname)
            got = digest(found) if found is not None else None
            if got is None:
                # A recorded file that is GONE is a finding for any gate: no argument
                # about what a verdict was about survives the artifact it cited not
                # being in the bundle.
                out.append((name, fname, "vanished"))
            elif got != want:
                out.append((name, fname,
                            "deferred" if name in _AUDIT_GATES else "changed"))
    return out


def _moment(iso: str):
    """An ISO instant, or None when there is nothing comparable there.

    Parsed rather than compared as text: both sides are UTC with the same precision
    today (`gates/base.stamp` and git's `%cI`), so string order would agree, but would
    stop agreeing the moment either emitted a different offset -- silently, in the
    direction that certifies a record it should not.
    """
    from datetime import datetime
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return None


def work_tree(inside: Path) -> Path | None:
    """The root of the git repository that CONTAINS `inside`, or None if none does.

    Asked of the corpus instead of assumed to be this checkout, which is the whole
    portability of the git proof: `--benchmark-dir` and `SBU_BENCHMARK_DIR` both accept a
    corpus anywhere on disk, and a published corpus is its own repository. Anchoring on
    this checkout dated the artifacts of one tree while reading another -- for a corpus
    outside it, not with a wrong answer but with a ValueError from `relative_to`, which
    is how three of the eight release checks came to work for exactly the two corpora
    that sit inside this repository.

    None is an answer, not a failure: a corpus in no repository has no history to offer.
    Every caller here reads it as "the git proof is unavailable", which is the
    fail-closed direction -- the record ends up uncertified, never certified by the
    absence of a commit that would have dated it.

    `audit_freshness.History` resolves its own anchor through this function, so the
    three release checks that ask git anything ask it of the same repository.
    """
    try:
        out = subprocess.run(["git", "-C", str(inside), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.SubprocessError):
        return None
    top = out.stdout.strip()
    return Path(top).resolve() if out.returncode == 0 and top else None


@dataclasses.dataclass(frozen=True)
class GitDates:
    """What git can say about the artifacts under one corpus: the work tree, the dates
    and the paths it cannot date, as ONE value.

    They travel together because they only mean anything together: `last` and `dirty`
    are keyed by paths relative to `top`, so a caller holding the dates of one
    repository while naming paths against another gets MISSES rather than an error, and
    a miss reads as "undated" -- the direction that refuses a record it should have
    certified, silently. Bundling the anchor with the tables it keys makes that
    unspellable, and puts the two questions a proof asks ("name this path", "when did
    git last change it") on the value that knows the answer.

    An empty instance is the honest state for a corpus no repository holds: `top` is
    None, so `name` answers None for every artifact and nothing is dated. Certification
    then rests on the content proofs and on mtime, and a record with neither comes out
    uncertified.
    """

    top: Path | None = None
    last: dict[str, str] = dataclasses.field(default_factory=dict)
    dirty: frozenset[str] = frozenset()

    @classmethod
    def for_corpus(cls, bench: Path) -> GitDates:
        """One `git log` pass over `bench`, in whichever repository contains it.

        One pass, not one per file: a commit's `--name-only` list is exactly the paths
        whose content differs from its parent, so walking the log newest-first and
        keeping the FIRST date seen for each path dates every artifact's last content
        change in a single process.

        `dirty` is what git cannot date: paths modified, added or untracked right now. A
        live fleet always has some, and a record whose artifact is dirty cannot be
        certified, because the bytes on disk are the bytes of no commit.
        """
        top = work_tree(bench)
        if top is None:
            return cls()
        try:
            rel = str(bench.resolve().relative_to(top))
        except ValueError:              # `--show-toplevel` disowned its own argument
            return cls()
        last: dict[str, str] = {}
        when = ""
        log = subprocess.run(
            ["git", "-C", str(top), "log", "--format=\x01%cI", "--name-only",
             "--", rel], capture_output=True, text=True, timeout=1800)
        for line in log.stdout.splitlines():
            if line.startswith("\x01"):
                when = line[1:].strip()
            elif line.strip():
                last.setdefault(line.strip(), when)
        st = subprocess.run(
            ["git", "-C", str(top), "status", "--porcelain", "--untracked-files=all",
             "--", rel], capture_output=True, text=True, timeout=1800)
        dirty = {ln[3:].strip().strip('"').split(" -> ")[-1]
                 for ln in st.stdout.splitlines() if ln[3:].strip()}
        return cls(top, last, frozenset(dirty))

    def name(self, p: Path) -> str | None:
        """`p` as the repository holding the corpus names it, or None when none can.

        None is the honest answer for an artifact no repository holds -- a corpus
        unpacked from a tarball, or a bundle outside the corpus's own work tree -- and it
        has to be an answer rather than an exception: a caller pointed at a bundle
        elsewhere on disk loses the git proof for it, and does not crash.
        """
        if self.top is None:
            return None
        try:
            return str(p.resolve().relative_to(self.top))
        except ValueError:
            return None

    def changed_at(self, p: Path) -> str | None:
        """When git last changed `p`'s CONTENT, or None when it cannot say."""
        rel = self.name(p)
        return self.last.get(rel) if rel is not None else None

    def uncommitted(self, p: Path) -> bool:
        """True when the bytes on disk are the bytes of no commit.

        Both ways that happens are one fact for a certifier: an artifact git cannot name
        and an artifact git names as modified are equally undated.
        """
        rel = self.name(p)
        return rel is None or rel in self.dirty


@functools.lru_cache(maxsize=None)
def gate_reads(gate: str) -> tuple[str, ...]:
    """What the gate that owns this record key declares it reads.

    Per-key, not a corpus-wide superset: `properties.py` is re-authored far more often
    than a solution is, so certifying every record against every artifact would refuse
    the faithfulness and leakage records of roles that never look at a battery, because
    a battery moved.

    `GATES` covers the gate modules; `G-PANEL-<n>` are record keys under one module,
    which publishes their narrower reads itself.
    """
    import sys
    if str(ROOT / "src") not in sys.path:
        sys.path.insert(0, str(ROOT / "src"))
    from swebench_unified.gates import GATES
    from swebench_unified.gates.panel import SUBGATE_READS
    mod = GATES.get(gate)
    if mod is not None:
        return tuple(getattr(mod, "reads", ()))
    return tuple(SUBGATE_READS.get(gate, ()))


def artifact_paths(cell: Path, reads: tuple[str, ...]) -> list[Path]:
    """The files `reads` names, resolved the way the gate resolved them.

    Through `Bundle.source_paths`, so this cannot drift from what the gates consume; a
    filename fallback covers a cell whose instance is not in the loaded benchmark.
    `meta.json` and `verdict.md` never appear either way, which is the point -- they are
    the record, they change on every re-gate, and no gate reads them.
    """
    try:
        import sys
        sys.path.insert(0, str(ROOT / "src"))
        from swebench_unified.backends import get_backend
        from swebench_unified.gates.base import Bundle
        b = Bundle(cell.parent.name, get_backend(cell.name))
        out = b.source_paths(reads)
        if out:
            return out
    except Exception:
        pass
    names = {"solution": ("model.py", "Solution.lean"),
             "prepatches": ("model_prepatch.py", "Solution_prepatch.lean"),
             "properties": ("properties.py",),
             "axiom_check": ("axiom_check.py",),
             "conformance_check": ("conformance_check.py",),
             "relaxed_leakage_doc": ("RELAXED_LEAKAGE.md",)}
    out = [cell / n for r in reads for n in names.get(r, ())]
    if "instance" in reads:
        out.append(cell.parent / "instance.json")
    if "patch" in reads:
        out.append(cell.parent / "patch.diff")
    return [p for p in out if p.is_file()]


def region_mismatch(cell: Path, rec: dict) -> str:
    """The regions whose recorded hash no longer reproduces from the solution.

    G-HYGIENE records `markers.region_hashes` -- the sha256 of each marked region plus
    the spec view -- so recomputing them from the file on disk decides "is this record
    about these bytes" by content, with no appeal to an mtime or a commit date. It calls
    the function that WROTE them rather than reimplementing the convention, since a
    reproduction that guesses wrong reports tampering at corpus scale. Empty string
    means "nothing to say" -- no recorded hashes, or a solution that cannot be read or
    projected -- never "verified", so a record this cannot speak for stays unverifiable
    rather than quietly certified.
    """
    want = (rec.get("data") or {}).get("region_hashes")
    if not isinstance(want, dict) or not want:
        return ""
    try:
        import sys
        if str(ROOT / "src") not in sys.path:
            sys.path.insert(0, str(ROOT / "src"))
        from swebench_unified.backends import get_backend
        from swebench_unified.markers import region_hashes
        sol = artifact_paths(cell, ("solution",))
        if not sol:
            return ""
        got = region_hashes(sol[0].read_text(), get_backend(cell.name).language)
    except Exception:
        return ""
    bad = sorted(k for k in set(want) | set(got) if want.get(k) != got.get(k))
    return "region_hashes[" + ",".join(bad) + "]" if bad else ""


# The audit roles that retain a POSITIVE CONTROL. `panel_2`/`panel_3` submit a
# prose judgment and no control, so there is nothing to recompute for them.
_CONTROL_GATES = ("G-EQ", "G-PANEL-1")
# Records whose verdict is about the SPECIFICATION rather than about bytes, and which
# this file therefore cannot decide.
#
# Every proof here -- a digest, an mtime, a commit date -- answers "are these the same
# bytes", which is right for a mechanical gate, whose verdict IS about the bytes it ran.
# An audit role's conclusion is about the spec those bytes carry, and the two come apart
# in both directions: every attack the audit ran rewrote the implementation on purpose,
# so a changed file need not move the spec, and a spec that GAINED obligations keeps the
# conclusion a fortiori because it rejects strictly more. Answering the question here
# anyway is not a stricter check but a wrong one -- and most of these records carry no
# `checked_at` either, because the audit stage began stamping long after it began
# auditing. So these rows are DEFERRED; the module docstring says why that is not
# silence.
_AUDIT_GATES = ("G-EQ", "G-PANEL", "G-PANEL-1", "G-PANEL-2", "G-PANEL-3")
# A lost line that is one half of a known hardening swap. Both directions of the
# swap appear because the comparison is per-line: the `partial` line disappearing
# IS the `total` line arriving.
_HARDENING = ("loom.semantics.termination", "PartialCorrectness",
              "TotalCorrectness")


def _parse_verdict_cached(vd: Path) -> dict:
    """`parse_verdict(vd)` memoised on (path, mtime, size).

    A verdict file runs to a hundred kilobytes and both questions asked of a control are
    asked per RECORD, so parsing per question turns a corpus walk into minutes of
    re-parsing one file. Keyed on mtime and size, not the path alone, because this runs
    while drivers are appending to those files.
    """
    try:
        st = vd.stat()
    except OSError:
        return {}
    key = (str(vd), st.st_mtime_ns, st.st_size)
    hit = _VERDICT_CACHE.get(key)
    if hit is None:
        import sys
        for p in (ROOT / "src", ROOT / "scripts"):
            if str(p) not in sys.path:
                sys.path.insert(0, str(p))
        from audit_recheck import parse_verdict
        try:
            hit = parse_verdict(vd.read_text())
        except Exception:
            hit = {}
        _VERDICT_CACHE.clear()          # one file at a time; this is a walk
        _VERDICT_CACHE[key] = hit
    return hit


_VERDICT_CACHE: dict[tuple, dict] = {}


def _retained_control(cell: Path, gate: str):
    """`(control, solution_on_disk, language)` if `gate` retains a usable control.

    Shared by the two questions asked of a control -- "does it show the spec was
    weakened" and "does it certify this record" -- because they have to agree on what
    counts as usable: for an unusable control the first answers "nothing to report" and
    the second "not shown", which are the same fact, and a checker holding two notions
    of usable would get the certifier wrong.
    """
    try:
        import re
        import sys
        for p in (ROOT / "src", ROOT / "scripts"):
            if str(p) not in sys.path:
                sys.path.insert(0, str(p))
        from swebench_unified.backends import get_backend
        vd = cell / "verdict.md"
        sol = artifact_paths(cell, ("solution",))
        if not (vd.is_file() and sol):
            return None
        sec = (_parse_verdict_cached(vd).get(gate) or {})
        ctl = sec.get("control")
        if not ctl or not str(ctl[1]).strip():
            return None
        src = str(ctl[1])
        # A retained block carrying diff hunk headers is a PATCH the verdict parser
        # attributed to the control slot, not a solution; deciding freshness from it
        # would publish a false weakening.
        if re.search(r"^@@ -\d+(,\d+)? \+\d+(,\d+)? @@", src, re.M):
            return None
        lang = get_backend(cell.name).language
        # This proof needs a backend whose solution carries MARKED REGIONS, so that a
        # spec view is separable from an implementation. A backend with
        # `region_names = ()` ships a requirements DOCUMENT and a test script as its
        # control, so `spec_view` returns each whole file and comparing them reports
        # every test the reviewer wrote as a lost clause.
        if not getattr(lang, "region_names", ()):
            return None
        return src, sol[0].read_text(), lang
    except Exception:
        return None


# The instance-root artifacts that are DERIVED from the benchmark row rather than
# authored, and so can be checked against a source outside the corpus.
_FROZEN = ("instance.json", "patch.diff")


def frozen_certifies(cell: Path, p: Path) -> bool:
    """True when `p` reproduces from the immutable benchmark row.

    The only proof here that appeals to something OUTSIDE the corpus, and the one the
    timestamp proofs lose most reliably: nobody authors `instance.json` or `patch.diff`,
    the builder derives them from the frozen dataset row, so their only commit is the
    bulk checkpoint that first added the cell -- dated after the build-time gates that
    read them, so the git proof refuses every one.

    Comparing to the row settles the question rather than moving it: for these two files
    "the gate read different bytes" would mean the corpus once shipped an instance record
    disagreeing with the dataset, which is what G-INTEGRITY fails on. G-INTEGRITY's own
    record is certified by this same comparison rather than by the verdict it published,
    so no record certifies itself.
    """
    if p.name not in _FROZEN:
        return False
    try:
        from swebench_unified.gates.base import load_frozen_row
        row = load_frozen_row(cell.parent.name)
        if not row:
            return False
        if p.name == "instance.json":
            return json.loads(p.read_text()) == row
        return p.read_text() == row.get("patch", "")
    except Exception:
        return False


def manifest_certifies(cell: Path, rec: dict) -> bool:
    """True when a record's own `manifest_sha256` reproduces from the battery on disk.

    G-PBT records the sha256 of the `properties.py` it judged, which is not weaker
    evidence than a digest: it is precisely the digest `sources` would carry, computed by
    the same gate over the same bytes, under an older key because it predates `sources`.
    It speaks for the BATTERY only -- G-PBT also reads the solution, and a manifest hash
    says nothing whatever about that file.
    """
    want = (rec.get("data") or {}).get("manifest_sha256")
    if not isinstance(want, str) or len(want) != 64:
        return False
    props = artifact_paths(cell, ("properties",))
    return bool(props) and digest(props[0]) == want


def region_certifies(cell: Path, rec: dict) -> bool:
    """True when a record's own `region_hashes` reproduce from the solution on disk.

    The certifying direction of `region_mismatch`, which cannot be had by negating it:
    that function looks for a DRIFTED record, so it returns "" both for "the hashes
    reproduce" and for "there are no hashes to read", and a certifier must not accept the
    second. Like the retained control it decides by CONTENT, so it holds for a record
    carrying no timestamp, and unlike the control it needs nothing retained in prose
    because G-HYGIENE writes these hashes on every run.

    What it pins: the hashes cover each marked region plus the spec view, and the spec
    view is the whole file with only the impl bodies elided, so together they fix every
    byte outside an implementation and the concatenation of the implementations. The one
    freedom left -- moving a line between two impl bodies while keeping their
    concatenation and start lines fixed -- cannot change what G-HYGIENE decides, whose
    verdict is about imports, markers, region structure and solver flags. Hence it is
    offered to G-HYGIENE, not as a general solution-freshness proof.
    """
    want = (rec.get("data") or {}).get("region_hashes")
    if not isinstance(want, dict) or not want:
        return False
    # The spec view is the half that pins everything OUTSIDE the impl bodies. A
    # record carrying only impl hashes would otherwise certify a file whose
    # contracts had been rewritten, which is the one edit that must never pass.
    if "spec_view" not in want:
        return False
    try:
        import sys
        if str(ROOT / "src") not in sys.path:
            sys.path.insert(0, str(ROOT / "src"))
        from swebench_unified.backends import get_backend
        from swebench_unified.markers import region_hashes
        sol = artifact_paths(cell, ("solution",))
        if not sol:
            return False
        got = region_hashes(sol[0].read_text(), get_backend(cell.name).language)
    except Exception:
        return False
    return bool(got) and got == want


def control_certifies(cell: Path, gate: str) -> bool:
    """True when the retained control proves this record still judges the shipped
    spec -- the certifying direction of `control_weakened`.

    Not that function's negation: it returns "" both for "the control reproduces" and for
    "there is no control to read", because its caller wants evidence of a DEFECT and
    silence answers both. A certifier cannot accept silence, so this requires a usable
    control first and only then asks whether anything was lost. It certifies the SOLUTION
    only -- the control is a copy of the spec and nothing in it speaks for
    `properties.py` -- so a role that also reads the battery needs another proof.
    """
    return _retained_control(cell, gate) is not None and not control_weakened(cell, gate)


def control_weakened(cell: Path, gate: str) -> str:
    """The spec clauses a passing audit saw that the shipped spec no longer has.

    The proof that reaches furthest, because a mechanized audit role retains its positive
    control -- the audited solution, verbatim -- in `verdict.md`, so its record binds
    itself to the spec it judged even with no `sources` digests at all, the class most
    undigested audit records fall in. It decides them with no verifier and no agent.

    Only a LOST clause is reported, because only a lost clause can weaken a spec: a spec
    that GAINED obligations rejects strictly more, so every attack the audited spec
    rejected is still rejected. Occurrences are counted as a MULTISET, so relocating a
    clause is not read as deleting it, and an obligation LEVEL is excused when the count
    holds -- raising `MustTerminate(2)` to `MustTerminate(6)` leaves the obligation in
    place.

    Empty string means "nothing to report", never "verified": a control that reproduces
    proves the SPEC VIEW is unchanged, and a role may read more than the solution. It
    over-reports rather than under-reports on purpose -- a `#`/`--` comment is filtered
    out, but prose inside a docstring is not distinguished from a clause -- because a
    missed deletion is a spec that admits a wrong implementation, while a spurious report
    costs a read.
    """
    got = _retained_control(cell, gate)
    if got is None:
        return ""
    src, cur, lang = got
    try:
        from swebench_unified.markers import same_spec, spec_view
        if same_spec(cur, src, lang):
            return ""
        a = [ln.strip() for ln in spec_view(src, lang).splitlines() if ln.strip()]
        c = [ln.strip() for ln in spec_view(cur, lang).splitlines() if ln.strip()]
    except Exception:
        return ""
    ca, cc = collections.Counter(a), collections.Counter(c)
    lost = [k for k in ca if ca[k] > cc.get(k, 0)]
    # A comment carries no obligation, so rewording one cannot weaken a spec. Left in,
    # this reports every cell whose spec prose was edited after its audit, none of it
    # evidence.
    lost = [k for k in lost if not k.startswith(("#", "--"))]
    keep = [k for k in lost if not any(h in k for h in _HARDENING)]
    if keep and "MustTerminate" in "".join(keep):
        # The obligation is what matters, not the level it was given. Excused
        # only when the shipped spec carries at least as many of them.
        na = sum(v for k, v in ca.items() if "MustTerminate" in k)
        nc = sum(v for k, v in cc.items() if "MustTerminate" in k)
        if nc >= na:
            keep = [k for k in keep if "MustTerminate" not in k]
    if not keep:
        return ""
    return "control:lost[" + ",".join(sorted(keep)[:3]) + "]"


def certify_cell(cell: Path, gates: set[str] | None, git: GitDates,
                 proofs: collections.Counter | None = None) -> list[tuple[str, str]]:
    """`(gate, why)` for each digest-less record that CANNOT be shown current.

    Independent proofs, and a record needs only one of them per artifact because each is
    sound on its own in this one direction:

    * the retained control (`control_certifies`) and the recorded region hashes
      (`region_certifies`), by CONTENT, so these are the ones that work on a record
      carrying no timestamp -- most audit-role records, since the audit stage began
      stamping long after it began auditing. Both speak for the solution alone, so a role
      that also reads the battery still needs another proof for that file.
    * the frozen benchmark row (`frozen_certifies`), by content against a source outside
      the corpus, for the two instance-root artifacts nobody authors.
    * mtime: nothing has written the file since the gate ran, so the gate read these bytes.
    * git: the last commit that CHANGED the path predates `checked_at`, which catches what
      mtime cannot -- a merge or a checkout that reset mtimes across the tree without
      touching content. `git` carries the repository that dated it, resolved from the
      corpus rather than from this checkout, and an empty `GitDates` is the honest state
      for a corpus no repository holds: the git proof is then simply not on offer, and
      whatever the other proofs cannot settle stays uncertified.

    Neither timestamp proof is used in reverse: a later mtime proves nothing, since a
    checkout or an identical rewrite produces one, and a commit is only a lower bound on
    when content was written. So failing every proof yields "uncertified", which means
    "not shown" and never "stale". An empty return means every digest-less record in the
    cell describes the bytes on disk; records that carry digests are decided by content
    in `check_cell`.

    `proofs` counts WHICH proof carried each certified record, because they are not
    equally durable: content and git travel with the repository, mtime does not
    survive a clone. Counting it is what makes that dependency a number in the
    report rather than a difference between two hosts nobody measured.
    """
    try:
        meta = json.loads((cell / "meta.json").read_text())
    except (OSError, ValueError):
        return []
    out: list[tuple[str, str]] = []
    for name, rec in sorted((meta.get("gates") or {}).items()):
        if gates and name not in gates:
            continue
        if not isinstance(rec, dict) or rec.get("status") not in (
                "pass", "fail", "relaxed"):
            continue
        if isinstance(rec.get("sources"), dict) and rec["sources"]:
            continue
        arts = artifact_paths(cell, gate_reads(name))
        if not arts:
            out.append((name, "gate declares no readable artifact"))
            continue
        # The control proof is by CONTENT, so it is tried BEFORE a timestamp is asked
        # for: an audit role recorded before the audit stage stamped anything has no
        # `checked_at`, and refusing it for want of a clock it never carried rejects the
        # one class of record that retains its own evidence.
        done = set()
        if (name in _CONTROL_GATES and control_certifies(cell, name)) \
                or region_certifies(cell, rec):
            done = {str(p) for p in artifact_paths(cell, ("solution",))}
        if manifest_certifies(cell, rec):
            done |= {str(p) for p in artifact_paths(cell, ("properties",))}
        arts = [p for p in arts
                if str(p) not in done and not frozen_certifies(cell, p)]
        if not arts:
            if proofs is not None:
                proofs["content"] += 1
            continue
        if name in _AUDIT_GATES:
            # Whatever the control could not settle is a question about the spec,
            # and the timestamp proofs below cannot answer it. See _AUDIT_GATES.
            out.append((name, "deferred to audit_freshness.py"))
            continue
        at = _moment(str(rec.get("checked_at") or ""))
        if at is None:
            out.append((name, "record carries no usable checked_at"))
            continue
        bad, host_local = "", False
        for p in arts:
            # git is asked FIRST even though mtime is the cheaper stat: either proof
            # settles the record, but only git's travels with the repository, so
            # trying mtime first would tally a durable proof as a host-local one.
            raw = git.changed_at(p)
            when = _moment(raw or "")
            if not git.uncommitted(p) and when is not None and when < at:
                continue                      # git proof: no commit changed it since
            if p.stat().st_mtime <= at.timestamp():
                host_local = True             # mtime proof: nothing wrote it
                continue
            if git.uncommitted(p):
                # In no repository, or committed-but-modified: either way git has no
                # dated content for these bytes to offer.
                bad = f"uncommitted artifact {p.name}"
            elif when is None:
                bad = f"undated artifact {p.name}"
            else:
                bad = f"artifact {p.name} changed at {raw}"
            break
        if bad:
            out.append((name, bad))
        elif proofs is not None:
            proofs["mtime" if host_local else "git"] += 1
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark-dir", default=default_benchmark_dir())
    ap.add_argument("--gates", default="", help="comma-separated subset")
    ap.add_argument("--certify-unchanged", "--certify-from-git",
                    dest="certify_unchanged", action="store_true",
                    help="for records with no digests, accept mtime's or git's "
                         "proof that nothing wrote the artifacts the gate reads "
                         "after checked_at")
    ap.add_argument("--out", default="", help="write mismatching cells as iid\\tbackend")
    ap.add_argument("--strict", action="store_true",
                    help="also fail when a verdict carries no digests")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    gates = {g.strip() for g in args.gates.split(",") if g.strip()} or None
    bench = Path(args.benchmark_dir)
    if not bench.is_absolute():
        bench = ROOT / bench

    # `frozen_certifies` is the only proof for `instance.json` and `patch.diff`, and it
    # reads the fetched dataset, which no checkout commits. Refused up front rather than
    # reported one record at a time: without that input the run spends minutes to end in
    # a count of "uncertified" that is about the missing input and says nothing about the
    # corpus. Asked only when it can matter -- a `--gates G-HYGIENE` run opens neither
    # file, and certification is what calls the proof at all.
    if args.certify_unchanged and (gates is None or any(
            {"instance", "patch"} & set(gate_reads(g)) for g in gates)):
        from swebench_unified.gates.base import frozen_dataset_complaint
        complaint = frozen_dataset_complaint(bench)
        if complaint:
            print(f"cannot certify: {complaint}")
            return 2

    git = GitDates()
    if args.certify_unchanged:
        git = GitDates.for_corpus(bench)
        if git.top is None:
            # Said out loud rather than left to a count of `uncertified`: a corpus in
            # no repository loses one of the four proofs, and a reader who cannot see
            # which proof is missing reads the refusals as a corpus defect.
            # The same phrasing the other two checks print, so one grep over a
            # release report finds every check that lost its history.
            print(f"# no git repository contains {bench}; no artifact here can be "
                  f"dated by a commit, so records fall to the content and mtime "
                  f"proofs and whatever those cannot settle is uncertified")
        else:
            print(f"# git: {len(git.last)} corpus path(s) dated, {len(git.dirty)} dirty in "
                  f"the working tree")

    kinds: collections.Counter[str] = collections.Counter()
    by_gate: collections.Counter[str] = collections.Counter()
    why: collections.Counter[str] = collections.Counter()
    proofs: collections.Counter[str] = collections.Counter()
    bad: set[tuple[str, str]] = set()
    cells = 0
    for meta_p in sorted(bench.glob("*/*/meta.json")):
        cell = meta_p.parent
        cells += 1
        rows = check_cell(cell, gates)
        # Certification replaces the `unverifiable` rows and only those: a record WITH
        # digests was already decided against the bytes, and git could only be a weaker
        # second opinion on it.
        undigested = {g for g, _f, k in rows if k in ("unverifiable", "deferred")}
        if args.certify_unchanged and undigested:
            unc = dict(certify_cell(cell, gates, git, proofs))
            rows = [r for r in rows if r[2] not in ("unverifiable", "deferred")]
            rows += [(g, "-", "deferred" if g in _AUDIT_GATES else "uncertified")
                     for g in sorted(unc)]
            kinds["certified"] += len(undigested - set(unc))
            for g, reason in unc.items():
                if g not in _AUDIT_GATES:
                    why[reason.split(" at ")[0].split(" artifact ")[0]] += 1
        for gate, fname, kind in rows:
            kinds[kind] += 1
            # Only `changed`/`vanished` say "the bytes moved" and so reach the re-stamp
            # lane; see the exit status below for `uncertified`.
            if kind in ("changed", "vanished"):
                by_gate[gate] += 1
                bad.add((cell.parent.name, cell.name))
                if not args.quiet:
                    print(f"  {kind:12s} {cell.parent.name}/{cell.name} "
                          f"{gate} :: {fname}")
            elif kind not in ("certified", "deferred") and args.strict:
                bad.add((cell.parent.name, cell.name))

    print(f"\n{cells} cell(s) checked")
    for k in ("changed", "vanished", "uncertified", "unverifiable", "certified"):
        if kinds[k]:
            print(f"  {kinds[k]:6d}  {k}")
    if kinds["deferred"]:
        print(f"  {kinds['deferred']:6d}  deferred -- an audit record's verdict is "
              f"about the spec, not the bytes; decided by scripts/audit_freshness.py "
              f"(a required release-gate check), not here")
    if proofs:
        print("  certified by: "
              + ", ".join(f"{k}={proofs[k]}" for k in ("content", "git", "mtime")
                          if proofs[k]))
    if proofs["mtime"]:
        # The one number that differs between this host and a fresh clone, so it is
        # printed even on a passing run: mtime is not committed, and a consumer who
        # re-runs this check gets `uncertified` for exactly these records.
        print(f"  note: {proofs['mtime']} record(s) rest on mtime alone, which does "
              f"not survive `git clone`. Re-run those gates "
              f"(`swebench-unified gates --backend B --gates G ID`) to record the "
              f"digests that travel with the corpus.")
    if why:
        print("  why uncertified: "
              + ", ".join(f"{r}={n}" for r, n in why.most_common(6)))
    if by_gate:
        print("  mismatches by gate: "
              + ", ".join(f"{g}={n}" for g, n in by_gate.most_common()))
    print(f"  cells needing a re-stamp: {len(bad)}")
    if args.out:
        Path(args.out).write_text("".join(f"{i}\t{b}\n" for i, b in sorted(bad)))
        print(f"  -> {args.out}")
    # `uncertified` counts with `unverifiable`, not with the mismatches: both mean "this
    # record cannot be checked", a weaker and different claim from "this record describes
    # files that have changed". Only --strict treats either as a failure, and that is the
    # mode a release check runs in.
    hard = kinds["changed"] + kinds["vanished"]
    soft = kinds["unverifiable"] + kinds["uncertified"]
    return 1 if hard or (args.strict and soft) else 0


if __name__ == "__main__":
    raise SystemExit(main())
