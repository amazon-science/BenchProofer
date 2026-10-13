# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""G-PBT — property-based falsification of the SPEC via the verifier
(docs/architecture.md §7).

Executes the bundle's `properties.py` manifest of adversarial cases. Each
SPEC_TESTS case is a full solution-file variant that must share the frozen
spec byte-for-byte AND stay inside the admissible variant scope
(variant_scope.variant_problems: same_spec, plus the proof obligation
preserved and no newly introduced axiom / sorry / @ContractOnly / theorem —
the spec view elides the impl and proof regions, so same_spec alone would
admit a variant that neuters the obligation it is meant to test);
pass/fail is whether the verifier's accept/reject matches `expect`:

  kind=uniqueness    expect=reject  wrong impl verifies   => SPEC-TOO-WEAK
  kind=soundness     expect=verify  correct impl rejected => SPEC-TOO-STRONG
  kind=admissibility expect=verify  normal input rejected => PRECOND-TOO-STRONG

Contracts are not runtime-executable (Nagini contracts are static Viper
markers; Lean specs are Props), so the spec lane's only oracle is the
verifier itself. The axiom lane (runtime fuzz of @ContractOnly axioms
against the real callee) is G-AX's job, NOT duplicated in this gate: a manifest
may carry AXIOM_TESTS, and this gate ignores them so that one artifact is never
judged twice by two gates with different oracles.

On velvet and lean an expect="reject" case must ALSO carry a refutation
`witness`. "Did not verify" is the default outcome of reshaping an impl on a
tactic-proof backend — the frozen script is tuned to the frozen impl's form —
so a rival that is merely RESHAPED fails identically to one that is WRONG, and
the rejection alone attributes nothing to the spec. The witness must hold of
the rival and fail on gold; see swebench_unified.pbt_witness. Nagini is exempt
(no tactic script to break, and Viper discharges the postcondition itself).

Gold cannot always serve as that second subject. A witness closes by `decide`,
and against an impl whose loop elaborates through `Classical.choice` the kernel
cannot reduce the claim at all, so the build fails for EVERY claim regardless of
truth and its exit code discriminates nothing (`witness-undecided`). Such a case
may name a `witness_reference` instead: another impl of the same spec, loop-free
so that it reduces, which the gate checks shares the frozen spec and VERIFIES
before refuting the witness against it. An impl the verifier accepts cannot
violate its own spec, so a genuine witness must still fail there.

Missing properties.py => explicit skip (mid-construction and un-migrated
bundles legitimately lack one), mirroring G-CONF's conf_missing_script
convention. For lean, variants are verified strictly: a variant whose proof no
longer closes counts as rejected — matching the source-repo semantics where
"verifies" means the whole obligation discharges.

Inconclusive cases (a verifier TIMEOUT, a malformed case dict, a case that
changed the spec, or a reject case whose witness did not discriminate) never
count as a pass: a timed-out expect="reject" case must not read as a correct
rejection and mask a weak spec. Such cases force a MALFORMED-TESTS verdict
(=> gate error), UNLESS a real finding is also present, in which case the
finding stands.

A battery with NO expect="reject" case at all is NO-REJECT-LANE, also an error:
SPEC-TOO-WEAK is detectable only by a rival that verifies, so with no rivals
"every case behaved as expected" degenerates to "every correct impl verified",
one level up from the witness-less rejection this gate already refuses.
"""
from __future__ import annotations

import hashlib
import re
import time

from ..pbt_witness import (WITNESS_REQUIRED, consistency_probe, witness_file,
                           witness_anchor_problems, witness_problems,
                           witness_scope_problems)
from ..variant_scope import variant_problems
from .base import Bundle, GateResult
from ._common import (check_bundle_source, env_int, no_verdict,
                      no_verdict_reason)

name = "G-PBT"
applies_to = ("nagini", "velvet", "lean")
needs_docker = False
agentic = False
# Bundle files this gate's verdict depends on; digested into the record
# so a stamp can be checked against the artifact it describes (base.source_digests).
reads = ("properties", "solution")

VERIFY_TIMEOUT_DEFAULT = 300
WORKERS_DEFAULT = 8

VERDICT_BY_KIND = {
    "uniqueness": "SPEC-TOO-WEAK",
    "soundness": "SPEC-TOO-STRONG",
    "admissibility": "PRECOND-TOO-STRONG",
}
_VERDICT_ORDER = ("SPEC-TOO-WEAK", "SPEC-TOO-STRONG", "PRECOND-TOO-STRONG")

# outcomes that are neither a valid pass nor a real finding: they force
# MALFORMED-TESTS (=> gate error), never a silent SOUND. witness-unproven,
# witness-vacuous and witness-inconsistent belong here rather than with the
# findings: they say "this reject case proved nothing", which is a defective
# TEST, not a defective spec.
_INCONCLUSIVE = ("malformed", "spec-changed", "inconclusive", "no-verdict",
                 "witness-unproven", "witness-vacuous",
                 "witness-inconsistent", "witness-undecided",
                 "witness-reference-invalid")

# A gold-side `decide` that gets STUCK rather than deciding. The witness check
# reads "the witness fails against the frozen solution" as evidence that it
# discriminates, but a failure the kernel never evaluated is evidence of nothing:
# the identical error comes back for the real witness, for its exact negation and
# for a trivially true claim. So a FORGERY asserting the rival is CORRECT at an
# agreement point clears both halves (rival 0, gold 1) and would be recorded as
# `rejected`. Screened by MESSAGE rather than by exit code, because the exit code
# is precisely what carries no information here. Same defect class
# `witness_scope_problems` screens for on the rival side, arriving as a stuck
# reduction instead of as an unknown name.
#
# Four arrival shapes, one row each:
#
#   1. stuck `decide`: the term never reduces to `isTrue`/`isFalse`.
#   2. a CONDITIONED witness (`example (out) (h : fExec a = DivM.res out) : ...`)
#      destructs its hypothesis instead of deciding a Prop, so an irreducible
#      loop swallows it in the equation compiler rather than in the kernel:
#      `Dependent elimination failed: Failed to solve equation ... forIn`.
#   3. a witness stated as a Hoare TRIPLE puts the loop-bearing program inside
#      the proposition, so `decide` never gets as far as reducing: the elaborator
#      cannot synthesize `Decidable ¬{True}do let r ← forIn Lean.Loop.mk ...` at
#      all, and a forgery dropping the `¬` fails with the identical error.
#   4. a witness that projects the carrier with `DivM.res.inj` fails UNIFICATION
#      on the un-normalised loop term rather than failing to decide.
#
# Rows 1-2 are one constant, 3 and 4 need their own because each has to be PAIRED
# with the loop term or the instance class; see below.
#
# Two causes, and they need different repairs, so both are named in the
# `witness-undecided` detail: a `while` loop under `loom.semantics.choice
# "demonic"` elaborates through `Classical.choice`, which the kernel cannot
# unfold; and an arithmetic operation that does not reduce in the kernel
# (`Rat.inv`, hence any `Rat` division) stalls a LOOP-FREE impl just as hard.
# Diagnosing either as "the loop" aims the repair at the wrong target -- the
# property a reference impl needs is kernel-reducibility, not loop-freeness.
_STUCK_REDUCTION = ("did not reduce to `isTrue` or `isFalse`",
                    "did not reduce to isTrue or isFalse",
                    "failed to reduce to a decidable proposition",
                    "Dependent elimination failed")

# Row 3, paired rather than screened on `failed to synthesize` alone: that
# message covers every missing instance in Lean, most of which are ordinary
# authoring errors that SHOULD fail. It is specifically a missing `Decidable`
# that means nothing was decided.
_STUCK_INSTANCE = ("failed to synthesize", "Decidable")

# Row 4. Lean prints TWO headlines for this one shape: `Application type
# mismatch` when the offending term sits in an argument position, and a plain
# `Type mismatch` when it is a hypothesis handed to `exact`. Both are required to
# co-occur with the loop term, for the same reason as `Decidable` above -- a type
# mismatch on its own is the most ordinary Lean error there is and usually means
# the witness is simply wrong.
_STUCK_UNIFICATION_HEADS = ("Application type mismatch", "Type mismatch")
_STUCK_UNIFICATION_TERM = "forIn Lean.Loop.mk"


def _stuck_screen(res) -> str:
    """Which stuck-reduction screen this build's log matches, or "".

    Deliberately scans the WHOLE log rather than just the first diagnostic, and
    the asymmetry with `_gold_signature` (which reads the first error only) is on
    purpose. The two failure directions do not cost the same thing:

      - a screen that fires on an unrelated late message turns a real refutation
        into `witness-undecided`, i.e. the battery FAILS the gate and a human
        looks at it;
      - a screen that MISSES a genuinely stuck build records a refutation that
        the kernel never performed, which mints a false SOUND and ships.

    So the conservative reading is the whole log, and narrowing this to the first
    diagnostic to match the signature would be the unsafe direction. `_run_case`
    records the screen name and the signature on that path, so "did this screen
    fire on the message that mattered?" is answerable from the artifact.
    """
    text = f"{getattr(res, 'stdout', '')}\n{getattr(res, 'stderr', '')}"
    if any(m in text for m in _STUCK_REDUCTION):
        return "reduction"
    if all(m in text for m in _STUCK_INSTANCE):
        return "decidable-instance"
    if _STUCK_UNIFICATION_TERM in text and any(h in text for h in _STUCK_UNIFICATION_HEADS):
        return "loop-unification"
    return ""


def _stuck(res) -> bool:
    """Whether a build failed by stuck reduction rather than by a real verdict."""
    return bool(_stuck_screen(res))


# `<path>:<line>:<col>: error|warning|info: ...` -- where one Lean diagnostic ends
# and the next begins. Anchored on the position triple rather than on the severity
# word, so a message whose BODY happens to contain "error:" (a witness quoting an
# error string, say) does not end the signature early.
_DIAGNOSTIC_HEAD = re.compile(r"^\S*:\d+:\d+: (?:error|warning|info):")

# Room for the longest diagnostic shape below, bounded so a tactic that dumps a
# whole goal state cannot put a megabyte of context into every meta.json.
_SIGNATURE_MAX_LINES = 12

# The turnstile line of an `unsolved goals` residue, which is the ONE line of a
# goal dump that decides what the failure attests. Lean prints the hypothesis
# context first and the goal last, so for a conjunctive spec at a concrete input
# both bounds above close before the `⊢` is reached and the record holds a context
# with no claim in it -- `pbt_signature_tiers.classify` files that as `truncated`,
# its own name for "the deciding bytes are not in the record at all".
#
# So the goal is kept out of band: scan past the head window, within the SAME
# diagnostic, for the first turnstile and append it after an elision mark. Only
# when the head does not already carry one, so a signature that already exhibits
# its goal is byte-identical before and after.
_GOAL_LINE = "⊢"

# How far past the head window to look for it. Generous, because the whole point
# is a long hypothesis dump, and cheap: it walks lines of one already-captured
# build log and stops at the diagnostic's end.
_GOAL_SCAN_LINES = 400

# The record's own bound. Applied so the GOAL survives it (see `_capped`): a cap
# that drops the tail would reproduce exactly the blank this fix exists to close.
_SIGNATURE_MAX_CHARS = 400


def _capped(head: str, goal: str) -> str:
    """`head` truncated to the record's bound, with `goal` kept whole.

    The goal is the part that carries the meaning, so it is the part that must not
    be what the cap eats. When both do not fit, the head is cut and the join
    keeps the elision mark, so a reader (and a tier rule) can see that the middle
    is missing rather than read a spliced line as contiguous bytes.
    """
    if not goal:
        return head[:_SIGNATURE_MAX_CHARS]
    room = _SIGNATURE_MAX_CHARS - len(goal) - 4       # 4 for the " ... " join
    if room < 40:
        # A goal long enough to crowd out the head entirely: keep the goal, which
        # is the claim, and enough of the head to name the tactic that failed.
        return f"{head[:40]} ... {goal}"[:_SIGNATURE_MAX_CHARS + len(goal)]
    return f"{head[:room]} ... {goal}" if len(head) > room else f"{head} ... {goal}"


def _gold_signature(res) -> str:
    """The first error diagnostic of a gold-side failure, for the record.

    Recorded so gold-side failure modes stay queryable from the artifact rather
    than by rebuilding the cell. One line per reject case, and it changes no
    verdict.

    The CONTINUATION lines are what carry the meaning, so they are kept: Lean
    breaks its errors immediately after the headline, leaving a first line that is
    often a useless prefix (`Application type mismatch: The argument`) while the
    next lines say `hcon.left has type True but is expected to have type ...` --
    i.e. `simp` reduced the witness's hypothesis to `True`, PROVING the equation
    for gold where it could not for the rival. That is the strongest gold-side
    evidence there is, and the truncated form is indistinguishable from a hollow
    tactic mismatch. Whitespace is collapsed so the shape stays greppable on one
    line.

    The continuation is delimited by a blank line or the next diagnostic header,
    NOT by indentation: Lean puts its `has type` / `but is expected to have type`
    connectives at column 0, so an indentation rule cuts the message at its first
    useful line.

    A bounded window has one blind spot: `unsolved goals` prints the hypothesis
    context BEFORE the goal, so a conjunctive spec at a concrete input runs the
    window out before the `⊢` and the record keeps a context with no claim in it.
    See `_GOAL_LINE`: when the window is what stopped the head, the goal is
    fetched out of band and appended after an elision mark, and `_capped` spends
    the character budget on it.
    """
    text = f"{getattr(res, 'stdout', '')}\n{getattr(res, 'stderr', '')}"
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if "error:" not in line:
            continue
        # Drop the leading `<path>:<line>:<col>: ` so the signature is comparable
        # across cells and across runs, then take the message's own body.
        parts = [line.split("error:", 1)[1].strip()]
        j = i + 1
        end = i + 1 + _SIGNATURE_MAX_LINES
        ended = False                      # the DIAGNOSTIC ended, not the window
        while j < min(end, len(lines)):
            if not lines[j].strip() or _DIAGNOSTIC_HEAD.match(lines[j]):
                ended = True
                break
            parts.append(lines[j].strip())
            j += 1
        head = " ".join(" ".join(parts).split())
        # Only look further when the WINDOW is what stopped the head, never when
        # the diagnostic did: past its end the next turnstile belongs to another
        # error, and splicing it in would give two cells that failed identically
        # different signatures depending on what else the build said. That is the
        # property the stops-at-the-next-diagnostic test pins down, and it has to
        # hold of this scan too.
        goal = ""
        if not ended and _GOAL_LINE not in head:
            goal = _first_goal(lines[j:i + 1 + _GOAL_SCAN_LINES])
        return _capped(head, goal) or "error"
    return ""


def _first_goal(rest: list[str]) -> str:
    """The first turnstile line of the diagnostic `rest` continues, or "".

    Same delimiters as the head window, for the same reason.
    """
    for ln in rest:
        if not ln.strip() or _DIAGNOSTIC_HEAD.match(ln):
            return ""
        if _GOAL_LINE in ln:
            return " ".join(ln.split())
    return ""

# `inconclusive` is the one member of the set above that says nothing about the
# BATTERY: it is what a verifier timeout produces, and a timeout is usually the
# machine rather than the case -- concurrency alone is enough, so a cap sized
# against sequential timings truncates the tail. A timed-out cell therefore needs
# a re-run at a higher cap or lower concurrency, NOT a re-authored battery, and
# the verdict has to say which: TIMED-OUT keeps the gate failing closed (still an
# error, still not SOUND) while saying the battery was never actually judged.
TIMED_OUT = "TIMED-OUT"

# The OTHER way a case reaches no verdict, and the remedy is the opposite one, so
# it cannot share TIMED-OUT's spelling: the verifier came back fast and refused to
# judge at all. On nagini that is the front end -- an untranslatable construct
# exits 1 with `Translation failed` and no Viper banner -- and no cap increase can
# ever fix it. Filing that as a timeout is not merely imprecise: a timeout is read
# as a statement about the HOST, so a crash filed that way is routed to a re-gate
# that can never repair it and its red record becomes eligible to be undone as a
# load artifact. NO-VERDICT says the battery is defective and the rival must be
# re-expressed. Still an error, still not SOUND: both fail closed.
NO_VERDICT = "NO-VERDICT"


def manifest_digest(bundle: Bundle) -> str:
    """sha256 of the manifest bytes this run judged, or "" if there is none.

    Recorded so a passing record is bound to the battery it actually ran. Without
    it a record attests only that SOME manifest passed at that path: the audit
    lane EDITS properties.py, and an edit that lands after the gate leaves a green
    record describing cases that no longer exist. Re-gating after such an edit is
    a caller's convention; the digest is what a reader holding only the bundle can
    check.
    """
    p = bundle.root / "properties.py"
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return ""


def load_manifest(bundle: Bundle) -> list[dict] | None:
    """SPEC_TESTS from the bundle's properties.py, or None if absent.

    The manifest is evaluated as a restricted literal module: SPEC_TESTS
    must be assignable by literal_eval after inlining the frozen-source
    convention (`_BASE = <solution text>`, `_swap(...)` region surgery).
    The manifest is data, not code: restricting it to a literal means a battery
    cannot influence its own verdict, and the gate itself stays read-only."""
    p = bundle.root / "properties.py"
    if not p.is_file():
        return None
    src = p.read_text()
    namespace: dict = {"__file__": str(p), "__name__": f"pbt_{bundle.instance_id}"}
    exec(compile(src, str(p), "exec"), namespace)  # noqa: S102 — bundle-trusted
    tests = namespace.get("SPEC_TESTS", [])
    if not isinstance(tests, list):
        raise ValueError("properties.py: SPEC_TESTS is not a list")
    return tests


def _reference_ok(bundle: Bundle, frozen: str, reference: str, timeout: int,
                  cache: dict | None) -> str:
    """"" if `reference` is a machine-checked correct impl of the frozen spec.

    Otherwise the reason it is not. Memoised on the source text: a manifest's
    reject cases share one reference, and re-verifying it per case would pay the
    most expensive build in the battery N times over.
    """
    key = reference
    if cache is not None and key in cache:
        return cache[key]
    scope = variant_problems(frozen, reference, bundle.backend.language)
    if scope:
        why = ("the reference does not share the frozen spec, so refuting the "
               f"witness against it says nothing about THIS spec: {'; '.join(scope)}")
    else:
        rv = check_bundle_source(bundle, reference, timeout)
        if no_verdict(rv):
            why = (f"the reference impl's build reached no verdict at {timeout}s: "
                   f"{rv.summary}")
        elif not rv.success:
            why = ("the reference impl does not VERIFY, so it is not known to "
                   "satisfy the spec and a witness refuted against it may simply "
                   f"be refuted against another wrong impl: {rv.summary}")
        else:
            why = ""
    if cache is not None:
        cache[key] = why
    return why


"""How many of the battery's own positives to try as a fallback reference.

Bounds the failing path's cost. Ordered by the manifest, so which one is used is
deterministic and reproducible from the artifact.
"""
_MAX_FALLBACKS = 3


def _no_verdict_case(where: str, r, timeout: int) -> dict:
    """The row for a build that came back without judging anything.

    Same split as `_run_case`: a cap hit is a statement about the host and wants
    the same battery re-gated with more budget; a verifier that refused to judge
    is a statement about the FILE and wants it re-expressed, which no cap can do.
    Quoting the cap in that second case is worse than vague — it names a remedy
    that provably cannot work (see NO_VERDICT).
    """
    crashed = no_verdict_reason(r) != "timeout"
    return {"outcome": "no-verdict" if crashed else "inconclusive",
            "detail": (f"{where} reached no verdict ({r.summary})" if crashed
                       else f"{where} reached no verdict at {timeout}s: "
                            f"{r.summary}")}


def _check_witness(bundle: Bundle, frozen: str, module: str, witness: str,
                   timeout: int, reference: object = None,
                   refcache: dict | None = None,
                   fallbacks: tuple[str, ...] = ()) -> dict:
    """Two builds deciding whether a rejection is attributable to the spec.

    The witness must hold of the RIVAL (so the rival provably contradicts the
    spec at a concrete input) and fail on the FROZEN solution (so it is a real
    discriminator and not a tautology that any impl would satisfy). Anything
    else is inconclusive, never a pass: a vacuous reject case would otherwise
    report SOUND while testing nothing.

    `reference` replaces the frozen solution as the second half's subject, for
    the cells where the frozen solution cannot serve as one: a `decide` against an
    impl whose loop elaborates through `Classical.choice` is stuck for every claim
    (see _STUCK_REDUCTION), so its exit code discriminates nothing. Sound for the
    same reason gold was -- a witness says "the spec is violated at this input",
    and an impl the verifier accepts cannot violate its own spec -- and checked
    rather than trusted (the reference must share the frozen spec and must VERIFY),
    because a reference that merely FAILED everything would refute every witness,
    honest or forged.
    """
    tables = bundle.backend.language
    if reference is not None and (not isinstance(reference, str)
                                 or not reference.strip()):
        return {"outcome": "malformed",
                "detail": "'witness_reference' is present but not a source string"}
    rival = check_bundle_source(bundle, witness_file(module, witness, tables),
                               timeout)
    if no_verdict(rival):
        return _no_verdict_case("witness build on the rival", rival, timeout)
    if not rival.success:
        return {"outcome": "witness-unproven",
                "detail": ("the witness does not hold of the rival, so the "
                           "rejection is not attributable to the spec (it is "
                           f"most likely a proof/tactic gap): {rival.summary}")}
    subject, side = frozen, "the frozen solution"
    if isinstance(reference, str) and reference.strip():
        why = _reference_ok(bundle, frozen, reference, timeout, refcache)
        if why:
            return {"outcome": "witness-reference-invalid", "detail": why}
        subject, side = reference, "the reference impl"
    gold = check_bundle_source(bundle, witness_file(subject, witness, tables),
                               timeout)
    if no_verdict(gold):
        return _no_verdict_case(f"witness build on {side}", gold, timeout)
    if gold.success:
        return {"outcome": "witness-vacuous",
                "detail": (f"the witness also holds of {side}, so "
                           "it does not discriminate the rival — it asserts "
                           "something true of any impl")}
    gold_stuck = _stuck_screen(gold)
    if gold_stuck and reference is None and fallbacks:
        # The frozen impl cannot decide anything, but the battery may already
        # contain an impl that can: its own expect="verify" positives are, by
        # construction, alternative impls of this same spec, and each is
        # independently required to VERIFY for the battery to pass at all. So try
        # them as the subject rather than failing a case whose witness may be
        # perfectly good. Same contract as an explicit witness_reference and
        # enforced by the same code -- shares the frozen spec, and verifies --
        # because a positive that does NOT verify would refute every witness.
        for cand in fallbacks[:_MAX_FALLBACKS]:
            if _reference_ok(bundle, frozen, cand, timeout, refcache):
                continue
            alt = check_bundle_source(bundle, witness_file(cand, witness, tables),
                                      timeout)
            if no_verdict(alt) or _stuck(alt):
                continue          # this positive does not reduce either
            if alt.success:
                return {"outcome": "witness-vacuous",
                        "detail": ("the witness also holds of a VERIFYING "
                                   "alternative impl of the same spec, so it "
                                   "does not discriminate the rival")}
            gold, subject = alt, cand
            side = "a verifying positive from this battery (gold cannot decide)"
            break
    if screen := _stuck_screen(gold):
        # gold FAILED, but not by deciding anything: the kernel never evaluated
        # the claim, so this exit code would attest to a refutation that was
        # never performed. See _STUCK_REDUCTION.
        #
        # The screen name AND gold's first error both go into the record, because
        # they answer different questions: `_stuck` reads the whole log while the
        # signature reads the first diagnostic, so without both, a cell that failed
        # here cannot be told apart from one whose FIRST error was the stuck one
        # without rebuilding it. See `_stuck_screen`.
        return {"outcome": "witness-undecided",
                "stuck_screen": screen,
                "gold_signature": _gold_signature(gold),
                "detail": (f"the witness's build against {side} failed by stuck "
                           "reduction, not by refutation, so it discriminates "
                           "nothing: the same error appears for a TRUE claim "
                           "about that impl, because an irreducible term blocks "
                           "`decide` for every claim. Two causes, and they need "
                           "different fixes: (a) a `while` loop under "
                           "loom.semantics.choice \"demonic\" elaborates through "
                           "Classical.choice, which the kernel cannot unfold; "
                           "(b) an arithmetic operation that does not reduce in "
                           "the kernel — `Rat.inv`, hence any `Rat` division — "
                           "which stalls a LOOP-FREE impl just as hard. So "
                           "loop-freeness alone is not the property you need; "
                           "kernel-reducibility is. State the refutation over a "
                           "computable projection, supply the blocked steps as "
                           "`decide +kernel` rewrites before deciding, or give "
                           "the case a 'witness_reference': a VERIFYING impl of "
                           "the same spec that DOES reduce, for the witness to "
                           f"be refuted against instead: {gold.summary}")}
    # A witness that CONDITIONS on the carrier (the only way to attack an opaque
    # callee: state the refutation at a point described by hypothesis rather than
    # computed) must also show its hypotheses can jointly hold. If they cannot,
    # the refutation follows from a contradiction and the counterexample input
    # does not exist. That forgery passes both halves above -- the contradiction
    # closes the goal for the rival's impl, so gold still fails -- which is why it
    # needs its own probe. Costs a third build only for the witnesses that bind
    # anything, a small minority of them.
    probe = consistency_probe(witness)
    if probe:
        # Against the same SUBJECT the refutation was checked on: the probe asks
        # whether the witness's hypotheses can hold, and on a
        # `witness_reference` cell those hypotheses are about the reference's
        # vocabulary.
        pr = check_bundle_source(bundle, witness_file(subject, probe, tables),
                                 timeout)
        if no_verdict(pr):
            return _no_verdict_case("consistency probe", pr, timeout)
        if pr.success:
            return {"outcome": "witness-inconsistent",
                    "detail": ("`False` follows from the witness's own "
                               "hypotheses, so the input it refutes the rival "
                               "at does not exist and the rejection attributes "
                               "nothing to the spec")}
    # `witness_subject` so a reader of the record can tell WHICH impl the
    # refutation was checked against: on the cells where gold cannot decide, that
    # is the whole substance of the attestation.
    out = {"ok": True, "outcome": "rejected (witness refutes the rival)",
           "witness_checked": True, "witness_subject": side,
           # See _gold_signature.
           "gold_signature": _gold_signature(gold)}
    if gold_stuck:
        # Reached only via the fallback: gold could not decide, a verifying
        # positive of the same spec did. Which screen sent it there is recorded so
        # the fallback population stays queryable per screen.
        out["gold_stuck_screen"] = gold_stuck
    return out


def _run_case(bundle: Bundle, frozen: str, case: dict, timeout: int,
              refcache: dict | None = None,
              fallbacks: tuple[str, ...] = ()) -> dict:
    cid = str(case.get("id", "?")) if isinstance(case, dict) else "?"
    kind = case.get("kind") if isinstance(case, dict) else None
    expect = case.get("expect") if isinstance(case, dict) else None
    module = case.get("module") if isinstance(case, dict) else None
    out = {"id": cid, "kind": kind, "expect": expect, "ok": False,
           "outcome": "", "wall_s": 0.0}
    # Schema validation: coercing typos (expect="verfiy" -> reject branch,
    # unknown kind -> SPEC-TOO-WEAK) could mint a false SOUND or mislabel a
    # defect, so a bad case is malformed, never silently defaulted.
    if not isinstance(case, dict):
        out["outcome"] = "malformed"
        out["detail"] = "case is not a dict"
        return out
    if expect not in ("verify", "reject"):
        out["outcome"] = "malformed"
        out["detail"] = f"expect must be 'verify'|'reject', got {expect!r}"
        return out
    if kind not in VERDICT_BY_KIND:
        out["outcome"] = "malformed"
        out["detail"] = f"kind must be one of {tuple(VERDICT_BY_KIND)}, got {kind!r}"
        return out
    if not isinstance(module, str) or not module.strip():
        out["outcome"] = "malformed"
        out["detail"] = "no 'module' source"
        return out
    # Scope check BEFORE the verifier: same_spec compares spec VIEWS, which
    # elide the impl region (and, on lean, the whole proof region including the
    # `theorem correct_<name>` statement). A variant that guts the obligation
    # (`theorem correct_X : True := trivial`) or injects an axiom therefore
    # passes same_spec and elaborates cleanly — an expect="verify" case would
    # record a pass for a reason unrelated to the spec. variant_scope closes
    # that: see swebench_unified.variant_scope.
    scope = variant_problems(frozen, module, bundle.backend.language)
    if scope:
        out["outcome"] = "spec-changed"
        out["detail"] = ("case is out of scope — malformed test, not a "
                         f"finding: {'; '.join(scope)}")
        out["scope_problems"] = scope
        return out
    t0 = time.monotonic()
    r = check_bundle_source(bundle, module, timeout)
    out["wall_s"] = round(time.monotonic() - t0, 1)
    # A verifier timeout or infra failure is INCONCLUSIVE — it must not pass
    # as a rejection (the soundness hole: a timed-out expect="reject" case
    # would otherwise read as a correct rejection and mask a weak spec).
    #
    # Which of the two it was decides the remedy, so they get separate outcomes:
    # a cap hit wants the same battery re-gated with more budget, a verifier that
    # refused to judge wants the case re-expressed. One shared outcome would also
    # make the detail report a cap that was never reached, since a crash returns
    # well inside it. `no_verdict_reason` already distinguishes them.
    if no_verdict(r):
        crashed = no_verdict_reason(r) != "timeout"
        out["outcome"] = "no-verdict" if crashed else "inconclusive"
        out["detail"] = (f"{r.summary} after {out['wall_s']}s (no verdict)"
                         if crashed else
                         f"{r.summary} at {timeout}s (no verdict)")
        return out
    verifies = r.success
    if expect == "verify":
        out["ok"] = verifies
        out["outcome"] = "verified" if verifies else f"rejected ({r.summary})"
        return out

    # expect == "reject"
    if verifies:
        out["outcome"] = "VERIFIED (admits wrong impl!)"
        return out
    # The rival did not verify — but on a tactic-proof backend that is the
    # DEFAULT outcome of reshaping an impl, correct or not: the frozen script
    # is tuned to the frozen impl's syntactic form. So "did not verify" alone
    # does not attribute the rejection to the spec. The witness does; see
    # swebench_unified.pbt_witness.
    if bundle.backend.name not in WITNESS_REQUIRED:
        out["ok"] = True
        out["outcome"] = "rejected"
        return out
    wp = witness_problems(case.get("witness"))
    # Also cheap, also before any build: the witness must be stated in the
    # vocabulary gold and the rival SHARE. A variant may legitimately add an
    # impl-region helper `def` (same_spec elides that region), and a witness
    # stated over it fails on gold as an UNKNOWN NAME while holding of the
    # rival — passing both halves of the discrimination check while asserting a
    # tautology. See pbt_witness.witness_scope_problems.
    wp = wp or witness_scope_problems(frozen, module, case.get("witness"))
    # And the claim must be ABOUT THE SPEC. The two builds establish that it
    # holds of the rival and fails of gold, which is a difference between two
    # impls; a difference is not a violation. See
    # pbt_witness.witness_anchor_problems.
    wp = wp or witness_anchor_problems(frozen, case.get("witness"))
    if wp:
        out["outcome"] = "malformed"
        out["detail"] = ("expect='reject' needs a refutation witness on this "
                         f"backend: {'; '.join(wp)}")
        return out
    wr = _check_witness(bundle, frozen, module, str(case["witness"]), timeout,
                        reference=case.get("witness_reference"),
                        refcache=refcache, fallbacks=fallbacks)
    out.update(wr)
    return out


def _positive_sources(tests: list[dict]) -> tuple[str, ...]:
    """The battery's own expect="verify" variant sources, manifest order.

    Candidate subjects for a reject case whose witness cannot be decided against
    the frozen impl. Every one of these is an impl the battery ITSELF asserts
    verifies against the frozen spec, and the gate independently checks that
    before using one; see _check_witness. Deduplicated on text, so a battery that
    reuses one source across positives does not pay for it twice.
    """
    seen: dict[str, None] = {}
    for c in tests:
        if not isinstance(c, dict) or c.get("expect") != "verify":
            continue
        src = c.get("module")
        if isinstance(src, str) and src.strip():
            seen.setdefault(src, None)
    return tuple(seen)


def _lanes(tests: list[dict]) -> dict[str, int]:
    """How many cases each kind lane contributes, for the record.

    The three lanes are the three directions this gate tests and they are not
    interchangeable: `uniqueness` is the only detector of SPEC-TOO-WEAK,
    `soundness` of SPEC-TOO-STRONG, `admissibility` of PRECOND-TOO-STRONG. A
    battery keeping two of three passes exactly as loudly as one keeping all
    three, so without the counts a released record shows no trace of which
    questions were asked -- only that every case asked behaved as declared.

    NO-REJECT-LANE already fails a battery with no uniqueness lane, since
    positives alone cannot certify soundness; the other two lanes stay advisory
    here (`scripts/pbt_coverage.py` queues them) because a genuinely vacuous lane
    is a legitimate omission the author must argue, not something a gate can
    adjudicate. What the gate can do is make the omission visible.
    """
    out: dict[str, int] = {}
    for c in tests:
        if isinstance(c, dict) and isinstance(c.get("kind"), str):
            out[c["kind"]] = out.get(c["kind"], 0) + 1
    return dict(sorted(out.items()))


def _verdict(cases: list[dict]) -> str:
    bad = [c for c in cases if not c["ok"]]
    inconclusive = [c for c in bad if c["outcome"] in _INCONCLUSIVE]
    real = [c for c in bad if c["outcome"] not in _INCONCLUSIVE]
    if not real and not inconclusive:
        # A battery with no expect="reject" case cannot certify spec strength in
        # the direction that matters most, so it must not be spelled SOUND: see
        # the module docstring on NO-REJECT-LANE.
        if not any(c.get("expect") == "reject" for c in cases):
            return "NO-REJECT-LANE"
        return "SOUND"
    if not real:
        # only inconclusive cases (malformed/spec-changed/timeout): no valid
        # finding, but we cannot certify SOUND either — surface as error.
        # The three spellings are all errors and none is SOUND, so nothing about
        # failing closed changes; what changes is the remedy. MALFORMED-TESTS
        # means the battery is defective and must be re-authored; TIMED-OUT means
        # no case was judged at all and the SAME battery needs re-gating at a
        # higher cap. Re-authoring on a timeout discards a battery that may be
        # perfectly sound, which is the more expensive mistake.
        #
        # NO-VERDICT sits between them: like a timeout nothing was judged, but
        # unlike a timeout the cause is IN the battery, so it is checked first —
        # a battery holding one crash and one cap hit must not be filed under the
        # remedy that cannot fix the crash.
        if any(c["outcome"] == "no-verdict" for c in inconclusive):
            if all(c["outcome"] in ("no-verdict", "inconclusive")
                   for c in inconclusive):
                return NO_VERDICT
            return "MALFORMED-TESTS"
        if all(c["outcome"] == "inconclusive" for c in inconclusive):
            return TIMED_OUT
        return "MALFORMED-TESTS"
    # a real finding stands even if other cases were inconclusive; kinds have
    # been validated in _run_case, so the map is total.
    verdicts = {VERDICT_BY_KIND[c["kind"]] for c in real}
    for v in _VERDICT_ORDER:
        if v in verdicts:
            return v
    return "DEFECT"


def run(bundle: Bundle, *, mode: str = "strict") -> GateResult:
    src = bundle.solution_src()
    if not src:
        return GateResult(name, "skip", "no solution file (blocked bundle)")
    try:
        tests = load_manifest(bundle)
    except Exception as e:  # manifest is agent-authored; a broken one is an error
        return GateResult(name, "error",
                          f"properties.py failed to load: {type(e).__name__}: {e}")
    if tests is None:
        return GateResult(name, "skip",
                          "no properties.py (not yet constructed)",
                          {"pbt_missing_manifest": True})
    if not tests:
        return GateResult(name, "skip", "properties.py has no SPEC_TESTS",
                          {"pbt_empty_manifest": True})

    # Honour the CELL's declared cap, as G-VERIFY and G-MUT already do via
    # bundle.verify_timeout(). Without this, a spec whose proofs genuinely need
    # longer than the default has no way to say so: raising its own
    # timeout_seconds fixes its sibling gates and leaves this one timing out at
    # 300s forever, so every re-gate re-measures the identical TIMED-OUT stamp.
    # The env var still wins when it asks for MORE, so a caller can raise the cap
    # for a whole run without touching every bundle, but it cannot silently lower
    # a cap the cell recorded a need for.
    timeout = max(env_int("SBU_PBT_VERIFY_TIMEOUT", VERIFY_TIMEOUT_DEFAULT),
                  bundle.verify_timeout())
    workers = env_int("SBU_PBT_WORKERS", WORKERS_DEFAULT)
    # Shared across the battery's cases: a `witness_reference` is one impl the
    # whole reject lane is refuted against, and verifying it is the most
    # expensive build here. Reads and writes happen under the GIL on whole dict
    # entries, so concurrent cases may duplicate the build but cannot corrupt the
    # cache -- the cost of a lock is not worth a rare duplicate.
    refcache: dict[str, str] = {}
    fallbacks = _positive_sources(tests)
    if workers > 1 and len(tests) > 1:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(workers, len(tests))) as ex:
            cases = list(ex.map(
                lambda c: _run_case(bundle, src, c, timeout, refcache,
                                    fallbacks), tests))
    else:
        cases = [_run_case(bundle, src, c, timeout, refcache, fallbacks)
                 for c in tests]

    verdict = _verdict(cases)
    n_bad = sum(1 for c in cases if not c["ok"])
    data = {"verdict": verdict, "n_cases": len(cases), "n_failed": n_bad,
            "manifest_sha256": manifest_digest(bundle),
            "lanes": _lanes(tests), "cases": cases}
    if verdict == "SOUND":
        return GateResult(name, "pass",
                          f"SOUND: {len(cases)} spec case(s) behaved as expected",
                          data)
    if verdict == "MALFORMED-TESTS":
        return GateResult(name, "error",
                          f"MALFORMED-TESTS: {n_bad} case(s) malformed "
                          f"(no valid finding)", data)
    if verdict == TIMED_OUT:
        # `pbt_timed_out` so a driver can select these cells without parsing the
        # message: they want the SAME battery re-gated at a higher
        # SBU_PBT_VERIFY_TIMEOUT, not a new one authored.
        data["pbt_timed_out"] = True
        return GateResult(name, "error",
                          f"TIMED-OUT: {n_bad} case(s) hit the {timeout}s "
                          "verifier cap, so nothing was judged — re-gate this "
                          "battery at a higher cap rather than re-authoring it",
                          data)
    if verdict == NO_VERDICT:
        # `no_verdict="crash"` is the spelling G-DIFF/G-GOLD/G-MUT already use,
        # and `restamp_gate.is_timeout` reads it: a crash is NOT a wall clock, so
        # this record must not be undone as a load artifact.
        data["pbt_no_verdict"] = True
        data["no_verdict"] = "crash"
        worst = [c for c in cases if c["outcome"] == "no-verdict"]
        detail = "; ".join(f"{c['id']}: {c['detail']}" for c in worst[:3])
        return GateResult(name, "error",
                          f"NO-VERDICT: {len(worst)} case(s) got no verdict from "
                          "the verifier at all (it refused to judge, it did not "
                          "run out of time), so nothing was judged — re-express "
                          f"the case; a higher cap cannot help. {detail}", data)
    if verdict == "NO-REJECT-LANE":
        # An error, not a fail: nothing here says the SPEC is defective. It says
        # the BATTERY cannot decide the question, which is the same category as
        # MALFORMED-TESTS. A port that judges the uniqueness lane genuinely
        # inexpressible on its carrier (opaque callees with no constraining
        # axiom, so no rival's violation is a theorem) is a real situation, but
        # it has to surface as an unresolved cell rather than as a soundness
        # certificate.
        return GateResult(name, "error",
                          f"NO-REJECT-LANE: {len(cases)} case(s), none "
                          "expect='reject' — cannot certify spec strength",
                          data)
    failing = "; ".join(f"{c['id']}: {c['outcome']}"
                        for c in cases if not c["ok"])[:400]
    return GateResult(name, "fail", f"{verdict}: {failing}", data)
