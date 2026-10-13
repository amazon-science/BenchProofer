"""properties.py — G-PBT falsification battery for django__django-13516 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_flush`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file elaborates
with the obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

DEFENDED SURFACE (one modeled behavior; a single spec predicate over ONE input
binder that matters plus one frame binder). A thin wrapper forwards a single
flush request to the stream it wraps, and the spec pins the underlying stream's
observable state after that request:

  problem_spec_flush (s : OutStream) (result : OutStream) : Prop
    (A)  result.hasFlush = s.hasFlush                          -- FRAME clause
    (B)  result.flushCount =
           if s.hasFlush then s.flushCount + 1 else s.flushCount  -- FORWARD clause

``s`` is an ``OutStream`` with two observed fields — ``hasFlush`` (whether the
underlying stream supports flushing at all) and ``flushCount`` (how many times
the underlying stream's own flush has been invoked). There is NO opaque answer
key to echo: both clauses ground the result in actual input fields (spec_guide
directive 8). The behavior pinned is a CONDITIONAL forward: when the underlying
stream supports flushing, its flush is invoked EXACTLY once (count +1); when it
does not, nothing happens to it (count unchanged); and either way whether the
stream supports flushing is itself untouched.

BINDER STRUCTURE (read this before judging binder coverage). The postcondition
depends on BOTH fields:

  * ``hasFlush`` — selects the branch of clause (B) AND is itself pinned by the
    frame clause (A). Every reject witness varies it ({true, false}).
  * ``flushCount`` — the observable side-effect counter; clause (B) pins its exact
    magnitude (+1, not merely ">0", on the flushable arm). Witnesses vary it
    across {0, 2, 3, 5} so no rival is refuted only at a pinned count.

Both TOP-LEVEL clauses are independent and each is attacked ON BOTH ARMS of the
guard:

  * clause (A) — the frame (support flag unchanged) — on the NON-FLUSHABLE arm by
    ``frame-flip-support`` (flag set) and on the FLUSHABLE arm by
    ``frame-clear-on-flushable`` (flag cleared while the count is advanced
    correctly, so the frame is the sole source of the rejection);
  * clause (B) — the conditional forward — on the FLUSHABLE arm by
    ``noop-prepatch`` (advances by 0, must be +1), ``over-forward`` (advances
    by 2, must be exactly +1) and ``fabricate-count-not-derive`` (does not derive
    the count from the prior count at all), and on the NON-FLUSHABLE arm by
    ``unconditional-forward`` (advances when it must not).

Note the two DISTINCT properties clause (B) carries, which need distinct rivals:
the OFFSET (exactly +1 — probed by over-forward and noop-prepatch, both of which
do read ``s.flushCount``) and the GROUNDING (the result is a function of
``s.flushCount`` at all — probed by fabricate-count-not-derive, which is the only
rival a spec phrased merely as "the count ends up positive" would fail to catch).

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — the nagini sibling holds the wrapper at a
    half-permission (``Acc(.,1/2)``) over TWO read-only fields — the capability
    BIT and the wrapped-stream REFERENCE — and makes a store to each fail for
    INSUFFICIENT PERMISSION. Lean is referentially transparent: ``s`` is an
    immutable value with no heap footprint, no ``mut`` binder, no aliasing, so
    there is no permission system and no rejection-by-store. The capability-bit
    probe RE-EXPRESSES as a VALUE rival: a rival that overwrites ``hasFlush``
    violates the frame clause (A) at a concrete input, refuted by the witness
    (``frame-flip-support``). The wrapped-stream-REFERENCE probe is VACUOUS here:
    this bundle models only the stream's two observables, carrying NO separate
    immutable reference field to overwrite — there is nothing to store to and no
    clause it could violate. See ``assessment``.

  * UNGROUNDED-ORACLE ECHO (nagini's directive-8 field-write) — the REJECTION
    MECHANISM is vacuous here, but the rival class is NOT, and it is ported. On the
    nagini carrier the invocation count is folded behind a @Predicate and read only
    via a @Pure, so a bare field write has no permission and that carrier rejects
    the echo on PERMISSION grounds. This backend has no predicate/permission
    machinery, so there is no permission to violate. What survives the carrier
    change is the actual defect the nagini rival models: an impl that produces the
    observable WITHOUT DERIVING IT from the input observable. That is expressible
    here as a value-level rival — pin ``flushCount`` to a literal instead of
    computing it from ``s.flushCount`` — and it is defended by
    ``fabricate-count-not-derive``, refuted at a concrete input. It is the sharpest
    rival on this surface, since it agrees with the faithful behavior on exactly the
    starting state the failing test observes and diverges everywhere else. Clause
    (B)'s magnitude is separately pinned by ``over-forward`` (+2) and
    ``noop-prepatch`` (+0), which DO derive from the prior count but with the wrong
    offset; the grounding requirement is a distinct property from the offset one.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``by_cases … <;> simp`` is tuned to the
frozen do-block — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS the spec at one concrete input. Each was checked (two real
``lake env lean`` builds) to ELABORATE against its rival and to FAIL against the
frozen solution (so it discriminates rather than asserting a tautology).
``OutStream`` derives ``DecidableEq`` and the literals are ground, so the snippets
``unfold`` the spec + impl and ``decide`` a concrete (in)equality; against gold the
same ``decide`` proves the negated spec FALSE and errors, which is the required
failure.

ADMISSIBILITY lane: PRESENT (``admiss-discriminating-input``). The frozen ``∀ s``
is unguarded, so there is no precondition to establish; on a total carrier the
PRECOND-TOO-STRONG analogue is instead the obligation being UNSATISFIABLE or BLIND
at an F2P-shaped input, which that case tests by discharging the spec at the
concrete flushable/never-yet-advanced configuration — admitting the advanced state
and REFUTING the unadvanced one — before the frozen script runs verbatim.

AXIOM lane: EMPTY. meta.json ``axioms == []`` and ``deep_model_references == []``;
the modeled behavior is a structural forward over two input observables, so there
is no axiom-soundness obligation to probe here (that lane is G-AX's).
``AXIOM_TESTS`` is therefore empty.
"""
from pathlib import Path

INSTANCE = "django__django-13516"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The whole impl def is the load-bearing shape of the impl region; every impl
# reshape lands entirely inside `-- impl-start`/`-- impl-end`.
_IMPL = (
    "def implementation_flush (s : OutStream) : OutStream := Id.run do\n"
    "  if s.hasFlush then\n"
    "    return { s with flushCount := s.flushCount + 1 }\n"
    "  return s"
)
assert _BASE.count(_IMPL) == 1, "impl body anchor drifted"


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec + proof view intact)."""
    return _swap(_BASE, _IMPL, new_impl)


# The first line of the frozen proof body. Prefixing `have`s here keeps the
# `theorem correct_flush` STATEMENT byte-identical and leaves the frozen script
# (`intro s; unfold …; by_cases … <;> simp …`) running verbatim afterwards, so an
# admissibility probe adds obligations without weakening the one under test.
_PROOF_INTRO = "  intro s\n"
assert _BASE.count(_PROOF_INTRO) == 1, "proof intro anchor drifted"


def _with_proof_haves(haves: str) -> str:
    """Solution.lean, gold impl, with `haves` discharged BEFORE the frozen script."""
    return _swap(_BASE, _PROOF_INTRO, haves + _PROOF_INTRO)


# ---- witness scaffold. The spec is a bare predicate, so a witness states it
# ---- directly at a ground `OutStream` literal: `¬ problem_spec_flush s
# ---- (implementation_flush s)`. Checked in a file whose frozen obligation is
# ---- elided by the gate, so no tactic script can mask the verdict. `OutStream`
# ---- derives DecidableEq and the literal is ground, so `decide` settles the
# ---- (in)equality after unfolding. ----
def _witness(has_flush: str, count: int) -> str:
    s = "{ hasFlush := %s, flushCount := %d }" % (has_flush, count)
    return (
        "example : ¬ problem_spec_flush\n"
        f"    {s}\n"
        f"    (implementation_flush {s}) := by\n"
        "  unfold problem_spec_flush implementation_flush\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_flush` statement byte-identical; each was confirmed to
    # close under the FROZEN proof body (no proof authoring, no helper lemma,
    # no assumption token) with a real build.
    # =====================================================================
    {
        "id": "pos-direct-functional",
        "kind": "soundness",
        "expect": "verify",
        # Functional reshape: drop the `Id.run do` scaffold and express the
        # conditional forward as a pure `if … then … else …`. Semantically
        # identical; advancing `flushCount` directly IS the modeled work (there is
        # no opaque callee this could "echo" instead of running). The frozen
        # `by_cases h : s.hasFlush <;> simp [Id.run, pure, bind, h]` still closes
        # both branches (verified with a real build).
        "module": _with_impl(
            "def implementation_flush (s : OutStream) : OutStream :=\n"
            "  if s.hasFlush then { s with flushCount := s.flushCount + 1 } else s"),
        "rationale": "correct reshape of the mutable-do forward into a pure "
                     "conditional; it computes the same OutStream on every input, so "
                     "it must satisfy both clauses (A) frame and (B) conditional "
                     "forward — else SPEC-TOO-STRONG. Carries the nagini "
                     "'honest inline work' argument onto this carrier: advancing the "
                     "count directly (no opaque primitive to invoke by name) still "
                     "verifies, so the spec is not over-fit to any particular call "
                     "shape. Proof: the frozen `by_cases <;> simp` closes both arms.",
    },
    {
        "id": "pos-guard-invert-early-return",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different CORRECT reshape: invert the capability guard and
        # early-return on the NON-flushable path, then advance the count on the
        # flushable path. Semantically identical to the gold if/return: not-flushable
        # returns `s` unchanged (clauses A+B hold, forward vacuous), flushable
        # advances the count exactly once (clause B). Branch-reorder / early-return
        # reshape only; no field beyond `flushCount` is touched, so the frame clause
        # (A) still holds. The frozen `by_cases <;> simp` closes both arms (verified).
        "module": _with_impl(
            "def implementation_flush (s : OutStream) : OutStream := Id.run do\n"
            "  if !s.hasFlush then\n"
            "    return s\n"
            "  return { s with flushCount := s.flushCount + 1 }"),
        "rationale": "structurally different CORRECT reshape (guard inverted + early "
                     "return on the non-flushable arm, then unconditional advance) — "
                     "semantically identical to the gold conditional forward: "
                     "not-flushable returns `s` (clauses A+B hold), flushable advances "
                     "the count once (clause B). A faithful branch reshape MUST verify, "
                     "else SPEC-TOO-STRONG. Proof: the frozen `by_cases <;> simp` "
                     "closes both collapsed arms; no new axiom/lemma, statement "
                     "unchanged.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation must be SATISFIABLE, and satisfiable
    # non-degenerately at the input the failing observation is shaped like. On a
    # total carrier the frozen `∀ s` carries no precondition hypothesis, so
    # PRECOND-TOO-STRONG cannot arrive as "a guard rejects a normal input"; its
    # analogue is the obligation being UNSATISFIABLE (or blind) at exactly that
    # input, which discharging the spec there by evaluation tests directly.
    # =====================================================================
    {
        "id": "admiss-discriminating-input",
        "kind": "admissibility",
        "expect": "verify",
        # Three `have`s, discharged by evaluation BEFORE the frozen script runs
        # verbatim on the real `s`. The impl stays gold; the statement is
        # byte-identical; no new top-level declaration, axiom or lemma.
        #   hF2P     — at the flushable, never-yet-flushed configuration the failing
        #              observation is shaped like, the spec ADMITS the advanced state.
        #   hF2POnly — and REFUTES the unadvanced one, so it is not blind there
        #              (a spec satisfied by both answers at that input would pin
        #              nothing exactly where the modeled behavior changes).
        #   hInert   — on the non-flushable arm the spec admits the untouched
        #              stream, so the other branch is satisfiable too and the
        #              obligation is not vacuously narrow to one arm.
        "module": _with_proof_haves(
            "  have hF2P : problem_spec_flush\n"
            "      { hasFlush := true, flushCount := 0 }\n"
            "      { hasFlush := true, flushCount := 1 } := by\n"
            "    unfold problem_spec_flush\n"
            "    decide\n"
            "  have hF2POnly : ¬ problem_spec_flush\n"
            "      { hasFlush := true, flushCount := 0 }\n"
            "      { hasFlush := true, flushCount := 0 } := by\n"
            "    unfold problem_spec_flush\n"
            "    decide\n"
            "  have hInert : problem_spec_flush\n"
            "      { hasFlush := false, flushCount := 7 }\n"
            "      { hasFlush := false, flushCount := 7 } := by\n"
            "    unfold problem_spec_flush\n"
            "    decide\n"),
        "rationale": "the frozen obligation is an unguarded `∀ s`, so admissibility "
                     "is carried as SATISFIABILITY + NON-DEGENERACY at the "
                     "discriminating input rather than as a precondition being "
                     "establishable. At (hasFlush=true, flushCount=0) — the flushable, "
                     "never-yet-advanced configuration the failing observation is "
                     "shaped like — the spec ADMITS the advanced result (count 1) and "
                     "REFUTES the unadvanced one (count 0), so it is both satisfiable "
                     "and sharp exactly where the modeled behavior changes; and at "
                     "(hasFlush=false, flushCount=7) it admits the untouched stream, so "
                     "the non-flushable arm is satisfiable too. If any `have` failed the "
                     "spec would be unsatisfiable or blind at an in-domain input — the "
                     "PRECOND-TOO-STRONG analogue on a total carrier. Discharged by "
                     "evaluation; statement byte-identical, impl gold, frozen "
                     "`by_cases <;> simp` runs verbatim afterwards.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing F2P test. The four witnesses
    # probe four DISTINCT input tuples; across them hasFlush takes {true,false}
    # and flushCount takes {2,3,0,5}. Both top-level clauses are attacked, and
    # clause (B) is attacked on both branches.
    # =====================================================================
    {
        "id": "noop-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # The PRE-PATCH behaviour: never forward — return the stream untouched. This
        # is the inherited no-op the fix replaces. Correct on the non-flushable
        # sub-domain (nothing should happen), wrong on the FLUSHABLE sub-domain where
        # the count must advance by one.
        "module": _with_impl(
            "def implementation_flush (s : OutStream) : OutStream := Id.run do\n"
            "  return s"),
        "refinement": "returning the stream untouched is the literal pre-patch "
                      "behaviour: the wrapper's flush request never reaches the "
                      "underlying stream, so on a flushable stream its flush is never "
                      "invoked and the invocation count stays at its prior value. The "
                      "F2P test wraps a flushable stream, requests one flush, and "
                      "asserts the underlying flush WAS invoked; under this impl it was "
                      "not, so the test FAILS — this is the exact bug the fix removes "
                      "and it does NOT resolve.",
        "rationale": "REJECT from clause (B) on the flushable arm: the spec demands "
                     "`flushCount = s.flushCount + 1` when `hasFlush` is true, but the "
                     "rival leaves the count unchanged. Refuted at "
                     "(hasFlush=true, flushCount=2): spec wants 3, rival gives 2. "
                     "Discrimination comes from the flushCount forward on the "
                     "flushable branch.",
        "witness": _witness("true", 2),
    },
    {
        "id": "unconditional-forward",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the capability guard: advance the count UNCONDITIONALLY. Correct on
        # the flushable sub-domain (count +1), but on the NON-flushable sub-domain it
        # advances a count that must stay put.
        "module": _with_impl(
            "def implementation_flush (s : OutStream) : OutStream := Id.run do\n"
            "  return { s with flushCount := s.flushCount + 1 }"),
        "refinement": "forwarding without first checking whether the underlying stream "
                      "supports flushing invokes a flush operation on a stream that has "
                      "none — the exact case the capability guard exists for. On the "
                      "non-flushable sub-domain the faithful behaviour is a harmless "
                      "no-op; an unguarded forward diverges (it would raise on a stream "
                      "with no flush attribute in the real code), so no faithful "
                      "resolving patch drops the guard — a verifying rival is a pure "
                      "verify-not-resolve artifact.",
        "rationale": "REJECT from clause (B) on the non-flushable arm: the spec demands "
                     "`flushCount = s.flushCount` when `hasFlush` is false, but the "
                     "rival advances it. Refuted at (hasFlush=false, flushCount=3): "
                     "spec wants 3, rival gives 4. Discrimination comes from the "
                     "non-flushable branch of the forward — a distinct input from "
                     "noop-prepatch's flushable-arm refutation.",
        "witness": _witness("false", 3),
    },
    {
        "id": "frame-flip-support",
        "kind": "uniqueness",
        "expect": "reject",
        # RE-EXPRESSION of the nagini capability-bit frame-mutation rival. On the
        # non-flushable path this rival overwrites the support flag (sets hasFlush to
        # true) instead of leaving the stream untouched. On the referentially
        # transparent carrier there is no permission to violate, so it fails as a
        # VALUE violation of the frame clause (A) rather than an insufficient-
        # permission rejection.
        "module": _with_impl(
            "def implementation_flush (s : OutStream) : OutStream := Id.run do\n"
            "  if s.hasFlush then\n"
            "    return { s with flushCount := s.flushCount + 1 }\n"
            "  return { s with hasFlush := true }"),
        "refinement": "a flush request never changes WHETHER the underlying stream "
                      "supports flushing — that support is a fixed property of the "
                      "stream, only ever read (never rewritten) by a forward. No "
                      "faithful patch mutates it, so a rival that does is a pure "
                      "verify-not-resolve artifact: it happens to advance the count "
                      "correctly on the flushable F2P case while corrupting a frame the "
                      "spec pins, which no resolving patch would.",
        "rationale": "REJECT from the FRAME clause (A) `result.hasFlush = s.hasFlush`: "
                     "on the non-flushable arm the rival returns a stream whose support "
                     "flag has flipped to true. Refuted at "
                     "(hasFlush=false, flushCount=0): the spec pins result.hasFlush to "
                     "false, the rival reports true. This is the only rival attacking "
                     "clause (A), and it exercises the non-flushable branch that the "
                     "count-forward rivals also touch — but discriminates on the frame, "
                     "not the count.",
        "witness": _witness("false", 0),
    },
    {
        "id": "over-forward",
        "kind": "uniqueness",
        "expect": "reject",
        # Right branch, wrong MAGNITUDE: on the flushable path advance the count by
        # two instead of one. Correct shape and correct branch selection, but the
        # forward count is wrong — pins that clause (B) demands EXACTLY +1, not merely
        # a positive advance. Carries the substance of the nagini echo rival (the
        # observable must reflect the RIGHT amount of work) onto this carrier.
        "module": _with_impl(
            "def implementation_flush (s : OutStream) : OutStream := Id.run do\n"
            "  if s.hasFlush then\n"
            "    return { s with flushCount := s.flushCount + 2 }\n"
            "  return s"),
        "refinement": "a single wrapper flush request must invoke the underlying "
                      "stream's flush EXACTLY once; advancing the invocation count by "
                      "two models forwarding twice (or a double-flush), which no "
                      "faithful single-forward patch does. The F2P test asserts the "
                      "underlying flush was called, and the deeper conformance check "
                      "pins the count delta to exactly one per request; a rival that "
                      "over-forwards diverges from the real wrapper and does NOT "
                      "resolve — a verify-not-resolve artifact.",
        "rationale": "REJECT from clause (B) MAGNITUDE on the flushable arm: the spec "
                     "demands `flushCount = s.flushCount + 1`, the rival produces "
                     "`+ 2`. Refuted at (hasFlush=true, flushCount=5): spec wants 6, "
                     "rival gives 7. Distinct from noop-prepatch (which advances by 0): "
                     "this near-miss selects the right branch and advances, so it needs "
                     "its own input pinning the exact +1, which a spec that only "
                     "required 'count increases' would miss.",
        "witness": _witness("true", 5),
    },
    {
        "id": "fabricate-count-not-derive",
        "kind": "uniqueness",
        "expect": "reject",
        # The DIRECT port of the nagini echo rival's substance, which the earlier
        # accounting had written off as vacuous here. This rival does not DERIVE the
        # observable from the stream's prior state at all: on the flushable arm it
        # PINS the count to the literal 1, discarding `s.flushCount`. That is the
        # ungrounded-oracle shape (directive 8) expressed at the value level — and it
        # is the sharpest verify-not-resolve trap this surface has, because it exactly
        # reproduces the ONE observation the failing test makes (a stream whose count
        # starts at 0 ends at 1) while being wrong at every other prior count.
        # Refuted at a count the F2P never reaches.
        "module": _with_impl(
            "def implementation_flush (s : OutStream) : OutStream :=\n"
            "  { s with flushCount := if s.hasFlush then 1 else s.flushCount }"),
        "refinement": "a flush request INVOKES the underlying stream's flush, which "
                      "advances that stream's own invocation count from whatever it "
                      "already was; it does not assign the count an absolute value. On a "
                      "stream that had already been flushed twice, one further request "
                      "must leave the count at three, not reset it to one — so this "
                      "rival disagrees with the real wrapper on every stream whose count "
                      "is not already zero, and the deeper conformance comparison (which "
                      "seeds the underlying stream at an arbitrary initial count and "
                      "demands initial+1) fails on it. It agrees with the faithful "
                      "behaviour ONLY on a freshly-created stream, which is precisely "
                      "why it is a verify-not-resolve artifact rather than a fix: it is "
                      "tuned to the single starting state the failing test happens to "
                      "observe.",
        "rationale": "REJECT from clause (B) as a GROUNDING requirement, not merely a "
                     "magnitude one: the spec demands the result count be "
                     "`s.flushCount + 1`, a function OF the input observable, so an impl "
                     "that fabricates a constant cannot satisfy it. Refuted at "
                     "(hasFlush=true, flushCount=4): spec wants 5, rival gives 1. "
                     "Distinct from over-forward (which derives from s.flushCount but "
                     "with the wrong offset) and from noop-prepatch (which derives it "
                     "with a zero offset): this one severs the dependence on the prior "
                     "count entirely, so it is the case that would survive a spec "
                     "phrased as 'the count ends up positive when flushable'.",
        "witness": _witness("true", 4),
    },
    {
        "id": "frame-clear-on-flushable",
        "kind": "uniqueness",
        "expect": "reject",
        # Clause (A) on the OTHER arm. `frame-flip-support` corrupts the support flag
        # on the non-flushable path only; this rival corrupts it on the FLUSHABLE path
        # — where it simultaneously gets clause (B) exactly right, so the rejection is
        # attributable to the frame clause alone and at an input the other frame rival
        # never reaches.
        "module": _with_impl(
            "def implementation_flush (s : OutStream) : OutStream := Id.run do\n"
            "  if s.hasFlush then\n"
            "    return { hasFlush := false, flushCount := s.flushCount + 1 }\n"
            "  return s"),
        "refinement": "forwarding a flush does not consume or revoke the underlying "
                      "stream's ability to flush — support for flushing is a fixed "
                      "property of that stream, read by the forward and never rewritten, "
                      "so it reads the same before and after. A rival that clears the "
                      "flag once it has forwarded would make every subsequent request on "
                      "the same stream a silent no-op, so buffered output would again be "
                      "held back after the first request; no faithful patch does this, "
                      "and the conformance comparison checks the support-flag frame on "
                      "the flushable configuration as well as the count.",
        "rationale": "REJECT from the FRAME clause (A) on the FLUSHABLE arm, which no "
                     "other case attacks: the rival advances the count correctly "
                     "(clause (B) holds at this input) but reports "
                     "`result.hasFlush = false` where the spec pins it to `s.hasFlush = "
                     "true`. Refuted at (hasFlush=true, flushCount=1). Complements "
                     "frame-flip-support, which violates (A) only on the non-flushable "
                     "arm — together they pin clause (A) on BOTH branches, so a spec "
                     "that framed the flag on one branch only would be caught here.",
        "witness": _witness("true", 1),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 6 SPEC cases (2 soundness
# positives, 1 admissibility, 2 frame-mutation rivals, 3 partial/echo rivals —
# 8 SPEC dicts total) plus a 2-case AXIOM lane. This bundle models a NARROWER
# surface: nagini contracts `drain_buffer` over a wrapper holding a heap stream at
# fractional permission with the invocation count folded behind a @Predicate,
# whereas lean models only the pure functional forward — two plain observables
# (`hasFlush`, `flushCount`) with no heap, no permission, no predicate. Every
# sibling case is recorded below.
#
#   sibling case                     -> here
#   ---------------------------------------------------------------------
#   pos-early-return  (soundness)    -> pos-guard-invert-early-return  PORTED
#   pos-inline-drain  (soundness)    -> pos-direct-functional          RE-EXPRESSED
#   admiss-fresh-wrapper (admiss)    -> admiss-discriminating-input    RE-EXPRESSED
#   frame-mutate-capability-bit      -> frame-flip-support             RE-EXPRESSED
#   frame-mutate-out-ref             -> (none)                         VACUOUS (no ref)
#   weak-echo-fieldwrite             -> fabricate-count-not-derive     RE-EXPRESSED
#   (no sibling; audit-added)        -> frame-clear-on-flushable       ADDED
#   weak-drop-guard-unconditional    -> unconditional-forward          PORTED
#   weak-noop-prepatch               -> noop-prepatch                  PORTED
#   AXIOM_TESTS (2)                  -> (none)                         DROPPED (G-AX)
#
# PORTED (partial-domain rivals): weak-noop-prepatch ports directly as
#   `noop-prepatch` (never forward — the literal pre-patch, wrong on the flushable
#   arm of clause B). weak-drop-guard-unconditional ports directly as
#   `unconditional-forward` (advance regardless — wrong on the non-flushable arm of
#   clause B).
# RE-EXPRESSED (positive control): the sibling's pos-inline-drain performs the
#   Unfold/+1/Fold predicate work "by hand" to show clause (4) is dischargeable
#   without calling the drain primitive by name. There is no predicate/permission
#   on this carrier; the analogous "do the work directly" reshape is
#   `pos-direct-functional`, a pure conditional that advances the count inline.
#   pos-early-return ports as `pos-guard-invert-early-return` (the same guard-invert
#   + early-return reshape). Both close under the FROZEN proof body.
# RE-EXPRESSED (frame-mutation, capability bit): the sibling relies on the
#   PERMISSION SYSTEM (a store through Acc(.,1/2) fails). Lean has no permissions,
#   so the same wrong impl (overwrite `hasFlush`) is re-expressed as a VALUE
#   violation of the frame clause (A), refuted by a concrete witness
#   (`frame-flip-support`). The ARGUMENT — the support flag is read-only and no
#   faithful patch rewrites it — is carried over; only the rejection MECHANISM
#   changes (postcondition value, not permission).
# RE-EXPRESSED (echo rival): the sibling's weak-echo-fieldwrite exploits that the
#   count is folded behind a @Predicate so a bare write "echoes" the observable
#   without running the primitive. That permission/abstraction MECHANISM does not
#   exist here (the count is a plain field, so there is no permission to violate),
#   but the DEFECT it models does: an impl that yields the observable without
#   deriving it from the input observable. `fabricate-count-not-derive` is that
#   rival at the value level — it pins the count to a literal instead of computing
#   it from `s.flushCount` — and it is refuted by a concrete witness at
#   (hasFlush=true, flushCount=4). An earlier revision of this accounting recorded
#   the whole class as VACUOUS on the grounds that "`flushCount + 1` IS the work, so
#   the observable cannot advance without doing it"; that reasoning conflated the
#   rejection mechanism with the rival, and it is wrong — the ungrounded rival is
#   expressible here and lands. It is also the most valuable rival on this surface,
#   since it matches the faithful behavior on exactly the initial state the failing
#   test exercises and diverges on every other, which is what a verify-not-resolve
#   artifact looks like. `over-forward` and `noop-prepatch` pin the OFFSET; this
#   pins the GROUNDING.
# ADDED (no sibling): `frame-clear-on-flushable` attacks clause (A) on the FLUSHABLE
#   arm, which the sibling's two frame rivals do not reach (both fire before the
#   guard, and the nagini rejection is by permission rather than by arm). Here the
#   frame is a value clause with two independently violable branches, so the
#   flushable-arm violation is a real and separate obligation; the rival advances the
#   count correctly at its witness input, making clause (A) the sole source of the
#   rejection.
# VACUOUS (frame-mutation, wrapped-stream reference): the sibling's frame-mutate-
#   out-ref writes the OTHER half-permission field — the immutable wrapped-stream
#   REFERENCE. This bundle models only the stream's two observables and carries no
#   separate reference field, so there is nothing to overwrite and no clause it
#   could violate. Not fabricated (porting map: this class is vacuous on a
#   referentially transparent carrier).
# RE-EXPRESSED (admissibility): the sibling self-constructs an F2P-shaped wrapper
#   and asserts drain_buffer's FULL precondition is establishable on it. An earlier
#   revision of this accounting recorded the whole LANE as VACUOUS here, reasoning
#   that `correct_flush`'s `∀ s` is unguarded so "there is no precondition to
#   admit". The premise is true and the conclusion does not follow: on a TOTAL
#   carrier the PRECOND-TOO-STRONG analogue is not a guard rejecting an input, it is
#   the obligation being UNSATISFIABLE or BLIND at exactly an F2P-shaped input — and
#   that is directly testable by discharging the spec at that concrete input, by
#   evaluation, as a `have`, before closing the frozen obligation verbatim. Landed as
#   `admiss-discriminating-input`: the spec ADMITS the advanced state at
#   (hasFlush=true, flushCount=0) and REFUTES the unadvanced one there (so it is
#   sharp, not merely satisfiable), and admits the untouched stream at
#   (hasFlush=false, flushCount=7) (so the other arm is satisfiable too). Dropping
#   this lane silently removes one of the three directions this gate exists to test,
#   which is why the "no precondition" reason is not sufficient on its own.
#
#   The six reject witnesses probe six DISTINCT input tuples; across them hasFlush
#   takes {true,false} and flushCount takes {0,1,2,3,4,5}. Both top-level clauses of
#   the postcondition are attacked on BOTH arms of the guard — clause (A) by
#   frame-flip-support (non-flushable) and frame-clear-on-flushable (flushable);
#   clause (B) by noop-prepatch (+0), over-forward (+2) and
#   fabricate-count-not-derive (ungrounded) on the flushable arm and by
#   unconditional-forward on the non-flushable arm. Each rival carries a
#   machine-checked witness that ELABORATES against the rival and FAILS (decide
#   proves the negated spec false) against the frozen solution.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no axiom
# (meta.json axioms == [], deep_model_references == []), so there is nothing to
# probe and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
