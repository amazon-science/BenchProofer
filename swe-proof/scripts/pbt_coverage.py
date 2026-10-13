#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Report what a ported G-PBT battery actually DEFENDS, not how much it costs.

A G-PBT pass says every case behaved as declared. It does NOT say the battery
covers the spec: a manifest with two cases passes exactly as loudly as one with
twelve. That gap matters most on the Lean-family backends, because a port can
shrink for two very different reasons and the gate cannot tell them apart:

  * LEGITIMATE — the Lean-family backends model only the purely functional core,
    so a nagini case attached to an unmodeled behavior has no counterpart.
    Case-count parity is therefore the WRONG target: chasing it would push an
    author to fabricate cases for behaviors that do not exist here.
  * NOT LEGITIMATE — the modeled surface is under-attacked.

So the invariant this reports is per-OBLIGATION and per-BINDER, both measured
against the frozen spec rather than against the nagini case count:

  1. every obligation is DEFENDED (>=1 expect="verify") and ATTACKED
     (>=1 expect="reject");
  2. every spec binder is DISCRIMINATED — some reject case's witness varies it
     while the rest are held fixed, or the case's variant edits a region whose
     value depends on it. A binder no witness ever moves is a binder no rival
     was ever built to abuse.
  3. every top-level spec CLAUSE (a conjunct / implication arm of the
     postcondition) is named by some reject case's rationale.

Advisory by design: it reads artifacts, records nothing, and exits 0 unless
--strict. A thin cell is a queue entry for a follow-up wave, not a gate error —
the gate's job is that no case LIES, and this measures whether enough cases
were built.

Usage:
  SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=benchmark-verified \
    python scripts/pbt_coverage.py --backend lean [--instances ...] [--strict]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from swebench_unified.corpus_root import default_benchmark_dir  # noqa: E402

# The backend whose battery a port reads from, so also the one whose KIND LANES a
# ported battery is expected to still carry (check 3 below).
REFERENCE_BACKEND = "nagini"

# lean: `theorem correct_foo : ∀ (a b : T) (c : U), ...`, but some obligations bind
# before the colon (`theorem correct_foo (a : T) : ...`), and a `[^:]*` guard would
# break on the colon INSIDE those binders. Only the name is needed here — the
# binders are read off the `problem_spec_*` def — so do not require the colon at
# all, or those obligations go unchecked entirely.
_LEAN_THM = re.compile(r"^theorem\s+(correct_\w+)(?![A-Za-z0-9_'])", re.M)
_LEAN_SPEC = re.compile(r"^def\s+(problem_spec_\w+)\s*(.*?):\s*Prop\s*:=(.*?)"
                        r"(?=^def|\Z)", re.M | re.S)
# velvet: `method name (a : T) (b : U) return (out : V)`. Signatures wrap, so the
# name is matched here and the rest is read off the method BLOCK with re.S — a
# `(.*?)` without DOTALL stops at the first newline and matches nothing, silently
# reporting the whole bundle as obl=0 rather than as a finding.
_VELVET_METHOD = re.compile(r"^method\s+(\w+)(?![A-Za-z0-9_'])", re.M)
_VELVET_RETURN = re.compile(r"\breturn\s*\(", re.S)
# `do` on its own line ends the spec region and begins the impl. Every method in
# the corpus has one; clauses must be read only from above it, or an `ensures`
# spelled inside a nested proof/impl comment would count as a spec clause.
_VELVET_DO = re.compile(r"^\s*do\s*$", re.M)
# A comment line inside the spec region, always on a line of its own (no inline
# `--` occurs in any spec region), so dropping whole comment lines is safe. It
# stops prose from being absorbed into whichever wrapped `ensures` it follows —
# where its identifiers would make an unattacked clause look referenced.
_VELVET_COMMENT_LINE = re.compile(r"^[ \t]*--.*$\n?", re.M)
# A precondition that PINS a binder to a literal (`require operandPresent =
# true`). No admissible input moves such a binder, so no rival can be built to
# abuse it — "pinned across all rivals" is the spec, not a gap, and reporting it
# sends the cell back for a repair that cannot be made.
_VELVET_REQUIRE_PIN = re.compile(
    r"^[ \t]*require[ \t]+(?:¬\s*)?\(?\s*(\w+)\s*=\s*(?:true|false)\s*\)?[ \t]*$",
    re.M)
# The lean counterpart: a hypothesis binder fixing a boolean input
# (`(h : flag = true)`). The exemption belongs to the concept rather than to
# velvet: no spec should be reported for a binder its own precondition forbids
# varying.
_LEAN_HYP_PIN = re.compile(r"\(\s*\w+\s*:\s*(\w+)\s*=\s*(?:true|false)\s*\)")
# An `ensures` continues onto the following lines until the next spec keyword.
# They wrap, and truncating at the newline drops exactly the half of the clause a
# rival would be built to violate.
_VELVET_ENSURES = re.compile(
    r"^[ \t]*ensures[ \t]+(.*?)(?=^[ \t]*(?:ensures|requires|invariant|"
    r"decreases|return)\b|\Z)", re.M | re.S)


def _load(props: Path):
    name = "pbtcov_" + re.sub(r"\W", "_", str(props))
    spec = importlib.util.spec_from_file_location(name, props)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {props}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _split_args(text: str) -> list[str]:
    """Top-level argument atoms of a Lean application, brackets respected.

    `(some (-1)) (some 100000) none (implementation_f ...)` ->
    ['(some (-1))', '(some 100000)', 'none', '(implementation_f ...)'].

    Stops at the `:=` / `by` that ends the statement, and at any top-level
    RELATION — `recordErrorCodeTester (some "a") = false` must yield one
    argument, not three. A relation at depth 0 is never an argument, because
    application only accepts atoms and parenthesized groups.
    """
    args: list[str] = []
    cur: list[str] = []
    depth = 0
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if depth == 0:
            if text.startswith(":=", i):
                break
            if ch in ",⟩=<>≠≤≥∧∨" or any(text.startswith(t, i) for t in
                                          ("→", "↔", "==", "!=")):
                break
            if (ch.isspace() or ch == "\n") and cur:
                args.append("".join(cur))
                cur = []
                i += 1
                continue
            # A KEYWORD ends the application. Velvet witnesses use `match
            # <base>Exec a b c with | ...`, and without this the match arms are
            # read as further arguments — which either fails to align (a false
            # never-named gap) or aligns by coincidence and reports a garbage
            # held value.
            if not cur and re.match(
                    r"(by|with|then|else|do|from|at|using|fun|match|if)"
                    r"(?![A-Za-z0-9_'])", text[i:]):
                break
            if ch == "|":
                break
        if ch in "([{⟨":
            depth += 1
        elif ch in ")]}⟩":
            if depth == 0:      # the closing paren of an enclosing group
                break
            depth -= 1
        if not ch.isspace() or depth or cur:
            cur.append(ch)
        i += 1
    if cur:
        args.append("".join(cur))
    return [a for a in (x.strip() for x in args) if a]


_EX_HEAD = re.compile(r"^[ \t]*(?:example|theorem[ \t]+\S+)", re.M)


def _head_bound_names(witness: str) -> set[str]:
    """Names the `example` / `theorem` head itself binds.

    A witness may quantify over its input instead of naming a value and CONSTRAIN
    it by hypothesis (`example (call : Int) (h1 : coreUfunc call = Except.ok 0) :
    ...`). That probes a real point — the one where the wrapped computation
    succeeds — but the point lives in `h1`, not in the argument list. Read
    positionally the argument is just the variable, identical across every such
    witness, so a battery that discriminates several outcomes reads as pts=1.
    Naming a head-bound variable therefore means UNREADABLE, exactly as an
    explicit `∀` does, and the caller falls back to the by-name signal.
    """
    out: list[str] = []
    for m in _EX_HEAD.finditer(witness):
        # Balanced binder groups run from the keyword up to the statement colon.
        i, n = m.end(), len(witness)
        head_end = i
        while i < n:
            while i < n and witness[i] in " \t\n":
                i += 1
            if i >= n or witness[i] not in "({[":
                break
            depth, j = 0, i
            while j < n:
                if witness[j] in "([{":
                    depth += 1
                elif witness[j] in ")]}":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            if depth:
                break
            i = head_end = j + 1
        out.extend(_binders(witness[m.end():head_end]))
    return set(out)


def _spec_args(witness: str, base: str) -> list[str]:
    """The arguments a witness applies to the spec predicate for `base`.

    Three head forms, tried in this order:
      * `<base>Tester ...`   — velvet, via `derive_tester_for`. Takes the method
        inputs only: the tester runs the program itself, so there is no result
        argument to strip.
      * `problem_spec_<base> ...` — lean.
      * `<base> ...` — a spec predicate written without the prefix. LAST because
        a velvet witness names the bare method in its `derive_tester_for <base>`
        preamble, and matching there would parse the following DIRECTIVE as an
        argument.

    Returns [] when the witness does not apply the predicate in a shape this can
    read (implicit args, a `∀`-quantified statement, a helper indirection).
    Callers must treat [] as "unknown", never as "no coverage".
    """
    for head in (f"{base}Tester", f"{base}Exec", f"problem_spec_{base}", base):
        for m in re.finditer(
                rf"(?<![A-Za-z0-9_']){re.escape(head)}(?![A-Za-z0-9_'])",
                witness):
            # A `<name>_for <base>` DIRECTIVE names the method without applying
            # it (velvet witnesses open with `extract_program_for <base>`), so the
            # tokens after it are the next line of the preamble, not arguments:
            # parsing there yields punctuation that can align against a
            # same-length binder list and report a nonsense held value. Skip the
            # occurrence, not the witness — the real application usually follows.
            if re.search(r"\b\w+_for\s*$", witness[:m.start()]):
                continue
            # A quantified witness applies the predicate to BOUND VARIABLES, so
            # its argument atoms are names, not values. Reading them as values
            # would report every binder as pinned to its own variable name.
            if re.search(r"[∀Π]|\bforall\b", witness[:m.start()]):
                return []
            args = _split_args(witness[m.end():])
            # An argument that is a name the HEAD binds is a bound variable, not
            # a probed value — the point it stands for is stated in a hypothesis
            # the reader cannot evaluate. Treat the whole witness as unreadable
            # rather than compare variable names across witnesses, which reports
            # pts=1 on a battery that discriminates several outcomes.
            if args and (set(args) & _head_bound_names(witness)):
                return []
            if args:
                return args
    return []


def _align(args: list[str], binders: list[str]) -> list[str] | None:
    """Drop the RESULT position so args line up with the input binders.

    `binders` is the def's FULL binder list, result included, and which position
    carries the result is per-bundle: `problem_spec_f a b c (implementation_f a b
    c)` puts it last, `problem_spec_count (r : Nat) (x : Nat)` first. Locating the
    `implementation_*` application is convention-agnostic and drops the SAME index
    from both lists, so alignment survives a result binder named for its domain
    (`objs`, `fields`, `toks`) rather than `result` — a name-based guess would
    silently shift every later position onto the wrong binder.

    Returns None when the shapes do not correspond, so an unreadable witness is
    never reported as a coverage gap.
    """
    # NO arguments is the unreadable signal, never a shape. On a ONE-binder spec it
    # otherwise matches the "result already dropped upstream" arm and aligns as the
    # empty tuple, so a cell whose every witness is unreadable reports
    # `binders=0 pts=1 ok` — "nothing to cover" on a real input — and the by-name
    # fallback never runs.
    if not args:
        return None
    idx = [i for i, a in enumerate(args) if "implementation_" in a]
    if len(idx) == 1 and len(args) == len(binders):
        return args[:idx[0]] + args[idx[0] + 1:]
    if len(args) == len(binders):      # no result argument (velvet tester)
        return args
    if len(args) == len(binders) - 1:  # result already dropped upstream
        return args
    return None


def _drop_result(binders: list[str], args: list[str]) -> list[str]:
    """`binders` minus the position the result occupies in `args`."""
    idx = [i for i, a in enumerate(args) if "implementation_" in a]
    if len(idx) == 1 and len(args) == len(binders):
        return binders[:idx[0]] + binders[idx[0] + 1:]
    return binders


def _binders(sig: str) -> list[str]:
    """Binder names from a signature, in declaration order.

    Scans BALANCED groups rather than regex-matching them: a type may itself be
    parenthesized (`(result : List (List Int))`, `(f : Nat → (Nat → Nat))`) and a
    `\\([^()]+\\)` pattern silently skips those groups entirely. Silently is the
    problem — a dropped INPUT binder reads as a spec with fewer inputs, so a
    real coverage gap on it can never be reported.

    Implicit and instance binders (`{α : Type}`, `[Inhabited α]`) are skipped:
    nothing a witness passes positionally corresponds to them.

    A LEADING `mut` is velvet's mutability modifier, not a name
    (`(mut data : Array Int)`), and reading it as one shifts every later position
    onto the wrong binder — so a pinned-binder finding is attributed to the wrong
    input. Stripped only in leading position, because `ref` and friends are real
    binder names elsewhere and `mut` could be too.
    """
    out: list[str] = []
    i, n = 0, len(sig)
    while i < n:
        if sig[i] != "(":
            i += 1
            continue
        depth, j = 0, i
        while j < n:
            if sig[j] in "([{⟨":
                depth += 1
            elif sig[j] in ")]}⟩":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if j >= n:
            break
        inner = sig[i + 1:j]
        # split at the group's OWN `:`, not one nested in the type
        d, cut = 0, -1
        for k, ch in enumerate(inner):
            if ch in "([{⟨":
                d += 1
            elif ch in ")]}⟩":
                d -= 1
            elif ch == ":" and d == 0:
                cut = k
                break
        if cut > 0:
            names = inner[:cut].split()
            if len(names) > 1 and names[0] == "mut":
                names = names[1:]
            out.extend(names)
        i = j + 1
    return out


def spec_surface(frozen: str, backend: str) -> dict[str, dict]:
    """{obligation: {"binders": [...], "clauses": [...]}} from the frozen spec.

    `binders` on lean is the def's FULL list, result included: the result
    position is identified per-witness by `_align`/`_drop_result` rather than by
    name, since a spec may name its result for its domain. Velvet method
    signatures list inputs only — the result is declared separately in
    `return (...)`.
    """
    surface: dict[str, dict] = {}
    if backend == "lean":
        specs = {m.group(1): (m.group(2), m.group(3))
                 for m in _LEAN_SPEC.finditer(frozen)}
        for m in _LEAN_THM.finditer(frozen):
            name = m.group(1)
            base = name[len("correct_"):]
            sig, body = specs.get(f"problem_spec_{base}", (None, None))
            if sig is None:
                # A specialized corollary (`correct_f_isNone` alongside
                # `correct_f`) states its own binders and its own conclusion,
                # with no `problem_spec_f_isNone` to read. Treating one as an
                # empty surface reports it as having no binders to cover, so a
                # coverage gap on it could never be raised.
                head = frozen[m.end():].split("\ntheorem ")[0].split(":= by")[0]
                sig, body = head, head
            # top-level conjuncts / implication arms of the postcondition
            clauses = [c.strip() for c in re.split(r"∧", body) if c.strip()]
            surface[name] = {"binders": _binders(sig), "clauses": clauses,
                             "pinned_by_spec": set(_LEAN_HYP_PIN.findall(sig))}
    else:
        for m in _VELVET_METHOD.finditer(frozen):
            name = m.group(1)
            block = frozen[m.end():].split("\nmethod ")[0]
            ret = _VELVET_RETURN.search(block)
            # No `return (` would mean the block is not a method signature at
            # all; report zero binders rather than reading the impl as one.
            sig = block[:ret.start()] if ret else ""
            do = _VELVET_DO.search(block)
            spec = _VELVET_COMMENT_LINE.sub(
                "", block[:do.start()] if do else block)
            surface[name] = {"binders": _binders(sig),
                             "clauses": [" ".join(c.split())
                                         for c in _VELVET_ENSURES.findall(spec)
                                         if c.strip()],
                             "pinned_by_spec":
                                 set(_VELVET_REQUIRE_PIN.findall(spec))}
    return surface


# Which direction each kind lane is the ONLY detector of, so a missing-lane
# finding says what stopped being tested rather than just naming a string.
VERDICT_FOR = {
    "uniqueness": "SPEC-TOO-WEAK (a wrong impl the spec accepts)",
    "soundness": "SPEC-TOO-STRONG (a correct impl the spec rejects)",
    "admissibility": "PRECOND-TOO-STRONG (an obligation unsatisfiable at an "
                     "F2P-shaped input)",
}


def _case_text(case: dict) -> str:
    return " ".join(str(case.get(k, "")) for k in
                    ("rationale", "refinement", "witness", "id"))


def audit_cell(bundle: Path, backend: str) -> dict:
    from swebench_unified.backends import get_backend
    frozen = (bundle / get_backend(backend).language.solution_filename).read_text()
    props = bundle / "properties.py"
    if not props.is_file():
        return {"error": "no properties.py"}
    tests = list(_load(props).SPEC_TESTS)
    surface = spec_surface(frozen, backend)
    rejects = [c for c in tests if c.get("expect") == "reject"]
    verifies = [c for c in tests if c.get("expect") == "verify"]

    findings: list[str] = []
    # 1. every obligation defended and attacked. With a single obligation the
    # attribution is unambiguous; with several, attribute by name mention.
    for name in surface:
        base = name[len("correct_"):] if name.startswith("correct_") else name
        if len(surface) == 1:
            d, a = len(verifies), len(rejects)
        else:
            d = sum(1 for c in verifies if base in c.get("module", ""))
            a = sum(1 for c in rejects if base in _case_text(c)
                    or base in c.get("module", ""))
        if not d:
            findings.append(f"{name}: no expect='verify' case defends it")
        if not a:
            findings.append(f"{name}: no expect='reject' case attacks it")

    # 2. every binder VARIED across the reject witnesses. A witness applies the
    # spec positionally (`problem_spec_f (some (-1)) (some 100000) none ...`),
    # so a by-name search finds nothing and would report every binder as
    # uncovered. Parse each witness's argument list instead and ask whether the
    # set of reject witnesses ever moves that position: a position pinned to one
    # value across every rival is a binder no rival was built to abuse.
    all_reject_text = " ".join(_case_text(c) for c in rejects)
    probe_points: dict[str, int] = {}
    inputs: dict[str, int] = {}
    for name, info in surface.items():
        all_binders = info["binders"]
        if not all_binders:
            continue
        base = name[len("correct_"):] if name.startswith("correct_") else name
        # Binders the SPEC ITSELF fixes (`require operandPresent = true`) are not
        # attackable: no admissible input moves them, so a rival "mishandling"
        # one is outside the spec's domain and there is no repair to make. The
        # exemption is deliberately narrow — only a literal equality, never a
        # relational precondition (`year <= 9999` still leaves 10000 values a
        # rival can abuse).
        fixed = info.get("pinned_by_spec") or set()
        # Parse every reject witness, then keep the readable ones ALONGSIDE the
        # binder list they align to: the result position is located per-witness,
        # so binder names and argument positions must be derived together.
        tuples: list[list[str]] = []
        binders = all_binders
        for c in rejects:
            raw = _spec_args(str(c.get("witness", "")), base)
            aligned = _align(raw, all_binders)
            if aligned is None:
                continue
            if not tuples:
                binders = _drop_result(all_binders, raw)[:len(aligned)]
            if len(aligned) != len(binders):
                continue      # a differently-shaped witness cannot be compared
            tuples.append(aligned)
        n_parsed = len(tuples)
        seen: list[set[str]] = [{t[i] for t in tuples}
                                for i in range(len(binders))]
        if not n_parsed:
            # No witness applied the predicate in a readable shape. Fall back to
            # the by-name signal, which is weak but not wrong: if the binder is
            # not even NAMED anywhere in the battery, nothing attacked it.
            for b in binders:
                if b in fixed:
                    continue
                if not re.search(rf"(?<![A-Za-z0-9_']){re.escape(b)}"
                                 rf"(?![A-Za-z0-9_'])", all_reject_text):
                    findings.append(
                        f"{name}: binder {b!r} is never named by any reject "
                        "case (witnesses unreadable, so this is by-name only)")
            continue
        # Distinct INPUT POINTS the battery probes. One point means every binder
        # is trivially pinned, which is a different (and blunter) fact than "the
        # battery moves three binders but never the fourth".
        probe_points[name] = n_points = len({tuple(t) for t in tuples})
        inputs[name] = len(binders)
        pinned = [i for i in range(len(binders))
                  if len(seen[i]) <= 1 and binders[i] not in fixed]
        # Only binders the battery COULD have varied count toward the degenerate
        # case; a spec that fixes every input but one is not thin coverage.
        free = [b for b in binders if b not in fixed]
        if pinned and n_points <= 1 and free:
            # Degenerate: the whole obligation is attacked at ONE input point,
            # so EVERY binder is trivially pinned and naming them individually
            # says the same thing N times. Each rival is still genuinely
            # refuted; what is thin is the spec coverage, so report the shape.
            findings.append(
                f"{name}: all {n_parsed} reject witness(es) probe the SAME "
                f"input point, so the battery says nothing about the spec's "
                f"dependence on any of {', '.join(repr(b) for b in free)}")
        else:
            # Index, not name: several binders may share a name-free position
            # and `.index()` would report the first one repeatedly.
            for i in pinned:
                held = ", ".join(sorted(seen[i])) or "?"
                findings.append(
                    f"{name}: binder {binders[i]!r} is pinned to {held} across "
                    f"all {n_parsed} reject witness(es) (which do vary others), "
                    "so a rival mishandling it would not be caught")

    # 3. every KIND LANE the nagini sibling carries is still represented. The
    # three lanes are the three directions this gate tests, and they are not
    # interchangeable: `uniqueness` finds SPEC-TOO-WEAK, `soundness`
    # SPEC-TOO-STRONG, `admissibility` PRECOND-TOO-STRONG. A port that keeps two
    # of three still passes as loudly as one that keeps all three, and the checks
    # above cannot see it -- they measure how well the obligation is attacked, not
    # which questions are being asked at all.
    #
    # `admissibility` is the lane a port drops, on the reading that a frozen
    # obligation with no explicit precondition has nothing to attack. But on a
    # total carrier the analogue is the obligation being UNSATISFIABLE at an
    # F2P-shaped input, and the sibling cells that do carry one show the shape. So
    # a missing lane is a queue entry, not a verdict: the reporter is advisory and
    # a genuinely vacuous lane is a legitimate omission the author must argue.
    nag = bundle.parent / REFERENCE_BACKEND / "properties.py"
    if nag.is_file():
        try:
            nag_kinds = {c.get("kind") for c in _load(nag).SPEC_TESTS
                         if isinstance(c, dict)}
        except Exception:            # a broken sibling is not this cell's finding
            nag_kinds = set()
        ours = {str(c.get("kind")) for c in tests if isinstance(c, dict)}
        for lane in ("uniqueness", "soundness", "admissibility"):
            if lane in nag_kinds and lane not in ours:
                findings.append(
                    f"kind lane {lane!r} is in the nagini sibling but in no case "
                    "here, so this battery tests "
                    f"{sorted(ours)} and not "
                    f"{VERDICT_FOR.get(lane, lane)}")

    # 4. every spec clause named by some reject case
    for name, info in surface.items():
        if len(info["clauses"]) < 2:
            continue
        for i, cl in enumerate(info["clauses"]):
            # a clause is "reached" if any reject rationale shares a
            # distinctive identifier with it
            idents = set(re.findall(r"[A-Za-z_][A-Za-z0-9_.']{3,}", cl))
            if idents and not any(t in all_reject_text for t in idents):
                findings.append(f"{name}: clause {i} unreferenced by any "
                                f"reject rationale: {cl[:60]!r}")
    return {
        "obligations": len(surface),
        "cases": len(tests),
        "verify": len(verifies),
        "reject": len(rejects),
        # INPUT binders only: the result is what a rival produces, not something
        # a reject case can be built to vary. The fallback (no witness parsed, so
        # `inputs` has no entry) subtracts the result position on lean, where the
        # spec def binds it, and NOT on velvet, where the signature lists inputs
        # only and `return (...)` declares the result separately — subtracting
        # there shows a one-input method as `binders=0`, i.e. "nothing to cover".
        "binders": sum(inputs.get(n, len(v["binders"]) - (backend == "lean")
                                  if v["binders"] else 0)
                       for n, v in surface.items()),
        "probe_points": probe_points,
        "findings": findings,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", required=True, choices=["velvet", "lean"])
    ap.add_argument("--benchmark-dir", default=default_benchmark_dir())
    ap.add_argument("--instances", nargs="*", default=None)
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if any cell has a coverage finding")
    ap.add_argument("--json", dest="as_json", action="store_true")
    args = ap.parse_args()

    root = ROOT / args.benchmark_dir
    ids = args.instances or sorted(
        p.parent.parent.name
        for p in root.glob(f"*/{args.backend}/properties.py"))
    rows = {}
    for iid in ids:
        try:
            rows[iid] = audit_cell(root / iid / args.backend, args.backend)
        except Exception as e:  # a broken manifest is itself the finding
            rows[iid] = {"error": f"{type(e).__name__}: {e}"}

    if args.as_json:
        print(json.dumps(rows, indent=2))
    else:
        thin = 0
        for iid, r in rows.items():
            if r.get("error"):
                print(f"{iid:<44} ERROR {r['error']}")
                thin += 1
                continue
            tag = "ok" if not r["findings"] else f"{len(r['findings'])} finding(s)"
            pts = r.get("probe_points") or {}
            pt = f" pts={min(pts.values())}-{max(pts.values())}" if pts else ""
            print(f"{iid:<44} obl={r['obligations']} cases={r['cases']} "
                  f"(+{r['verify']}/-{r['reject']}) binders={r['binders']}"
                  f"{pt}  {tag}")
            for f in r["findings"]:
                print(f"    - {f}")
            thin += bool(r["findings"])
        print(f"# {len(rows)} cell(s), {thin} with coverage findings")
    bad = sum(1 for r in rows.values() if r.get("findings") or r.get("error"))
    return 1 if (args.strict and bad) else 0


if __name__ == "__main__":
    sys.exit(main())
