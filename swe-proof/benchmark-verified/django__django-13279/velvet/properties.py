"""properties.py — G-PBT falsification battery for django__django-13279 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or the ``prove_correct`` tactic body, is changed — both
of which the consumer spec view elides, so ``markers.same_spec`` holds and the
``prove_correct encodeSession`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is judged by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over abstract carriers). A piece of
session data is encoded to a textual form under a mode flag:

  encodeSession (sessionData) (legacyHashMode : Bool)
      ensures legacyHashMode = true  → out = legacyEncoding sessionData   (clause A)
      ensures legacyHashMode = false → out = standardEncoding sessionData  (clause B)

``legacyEncoding d = wrap (hashOf (serialize d)) (serialize d)`` is a deep
composition of unchanged building blocks; ``standardEncoding`` is the standard
form. The method has NO ``require`` clause — the input domain is total.

CARRIER NOTE (decisive for this port). The four data carriers are abstract
identities (``SessionData``/``Serialized``/``Hash``/``Encoded`` are opaque
``Nat`` aliases) and ``serialize``/``hashOf``/``wrap``/``standardEncoding`` are
``opaque`` functions with NO constraining ``axiom``. The two post-images pin
``out`` to compositions of these opaque values. Only clause A's target is a
transparent composition (it unfolds to ``wrap (hashOf (serialize d))
(serialize d)``); the opaque building blocks never reduce at a literal input.

THE WITNESS ON AN OPAQUE CARRIER (the load-bearing technique of this port). A
``decide`` on a concrete literal (``encodeSessionTester 0 true``) gets STUCK:
nothing reduces ``serialize 0`` / ``hashOf _`` / ``standardEncoding 0``, so no
literal input decides the postcondition. A witness therefore does NOT compute
the carrier — it CONDITIONS on it. Each reject witness quantifies over a
symbolic ``d`` and assumes ONE disequality of opaque composites describing
exactly the sub-region the rival is wrong on (e.g. ``standardEncoding d ≠
legacyEncoding d`` for the pre-patch rival), then shows the extracted program's
output differs from the post-image there. Reaching the program uses Velvet's own
extractor: ``extract_program_for`` gives ``encodeSessionExec = NonDetT.run ∘
encodeSession``, and ``NonDetT.run (pure x) = DivM.res x``. The claim each
witness makes is STRONGER than any literal input could make: *wherever the two
composites differ, the rival's answer differs from the spec's* — the whole
sub-domain on which the rival is wrong.

Each witness is checked three ways (the last by the gate): (1) it ELABORATES
against the rival — the rival provably contradicts the post-image on the
hypothesised region; (2) it FAILS against the frozen solution — the frozen impl
reduces the same goal to ``¬(x = x)`` / an unsolved ``False``, so it is a real
discriminator, not a tautology; (3) its binders are JOINTLY SATISFIABLE — the
consistency probe (``example <binders> : False``) does NOT close, so the
"counterexample" input genuinely exists (one hypothesis per witness, an ordinary
opaque-composite disequality that is not a theorem in either direction, so it is
neither self-contradictory nor a smuggled assumption of the conclusion). No
``sorry``/``admit``/``native_decide``/``axiom``. All three were verified
out-of-band with real ``lake`` builds before shipping.

ADVERSARIAL READ of the classes:
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical dispatch (guard negated + branches swapped; a
    ``match`` on the flag; the legacy composition written inline) must still
    verify, else the spec is SPEC-TOO-STRONG on the shape of the dispatch. Three
    ``pos-*`` cases exercise the dispatch, the flag both ways, and the deep
    composition.
  * ADMISSIBILITY — RE-AIMED. The method has no precondition, so the usual
    "a normal input satisfies the precondition" probe is vacuous. The analogue on
    a TOTAL domain is the obligation being UNSATISFIABLE at exactly an F2P-shaped
    input. ``admiss-legacy-grounded`` discharges, as an in-region ``assert``
    before the frozen obligation closes verbatim, that the two-clause post-image
    is jointly satisfiable AT EACH CONCRETE MODE VALUE by a value grounded in the
    input. It is checked live against three same-shape negative controls that
    each leave an unsolved goal (see the case comment). An earlier form of this
    case asserted only the defining equation of ``legacyEncoding``, which bare
    ``rfl`` closes — a restatement that passed while probing nothing; that defect
    was found and repaired in audit.
  * FRAME-MUTATION — VACUOUS on this backend, and DEMONSTRATED so rather than
    asserted. The class exists on the sibling because a heap input can carry a
    fractional permission an impl overwrites. Here there is no heap, no aliasing,
    and no ``mut`` binder. Measured in audit: an impl that assigns to the input
    binder (``sessionData := sessionData``) does not reach the verifier at all —
    it is a Lean PARSE/elaboration error (```sessionData` cannot be mutated, only
    variables declared using `let mut` can be mutated``), so the file is
    uncompilable and its rejection would attribute nothing to the spec. The
    read-only frame is enforced by the language, not by the contract, so there is
    no admissible rival to write. Not fabricated.
  * DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
    SEMANTICS against any rival that manufactures it. The frozen impl is
    LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
    and no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.
  * UNGROUNDED-ORACLE ECHO — N/A in the harmful sense. Clause A's post-image is
    grounded in the composition of the building blocks over the input; the
    standard branch is deliberately opaque (the sibling declines to over-commit
    it). No wrong echo to build.
  * UNIQUENESS / SPEC-TOO-WEAK rivals — APPLY, via conditioning on the carrier.
    Each sibling reject rival ("emit the standard form in legacy mode"; "carry a
    fixed/empty payload"; "build a structurally-broken legacy frame") re-sites
    onto clause A as an opaque-composite disequality that is not a theorem in
    either direction — undecidable, so a witness cannot PROVE it, but it can
    ASSUME it and refute the rival on exactly that sub-region. Three further
    rivals attack clause B (the standard branch) and the two halves of the legacy
    composition, so the mode binder is moved across both values and neither the
    hash slot nor the body slot is left unprobed. Every rival ships a
    machine-checked, satisfiable, discriminating witness. See the footer for the
    case-by-case sibling accounting.

NOTE on clause B and the sibling's CONSERVATIVE remark. The sibling records that
its modern-arm clause is stronger than the P2P test strictly needs — the real
decode() falls back to the legacy reader, so a patch that emitted a LEGACY frame
in the standard regime would still round-trip and resolve. So NO reject rival
claims "emit the legacy form in standard mode would not resolve" (that refinement
would be false). The clause-B rival below instead emits a frame that is NEITHER
the standard form NOR a legacy-readable frame (a hash/payload-mismatched blob):
its faithful counterpart breaks the ordinary decode round trip the unchanged
P2P tests exercise, so it would NOT resolve.

AXIOM lane: the sibling's ``AXIOM_TESTS`` are dropped — the axiom lane is G-AX's
job (recorded pass in meta.json), and this gate ignores ``AXIOM_TESTS``
regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13279"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the frozen dispatch body, verbatim (everything
# ---- strictly inside encodeSession's -- impl-start / -- impl-end). Every
# ---- variant _swap()s only this block (and, where the reshape needs it, the
# ---- proof body below), so the edit never touches the spec regions
# ---- (axioms/pure/pre/post + the method signature and both `ensures`). Both
# ---- "present" and "unique" are asserted at load by _swap.
_IMPL = (
    "    let result : Encoded :=\n"
    "      if legacyHashMode then legacyEncoding sessionData\n"
    "      else standardEncoding sessionData\n"
    "    return result"
)
assert _BASE.count(_IMPL) == 1, "encodeSession impl region drifted from expected text"

# ---- proof-body anchor. The `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view, so a positive control that reshapes the impl may
# ---- retune its script without touching the spec or dropping the obligation.
_PROOF = "prove_correct encodeSession by\n  loom_solve"
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


def _impl(new_impl):
    """Full Solution.lean with ONLY encodeSession's impl-region body replaced."""
    return _swap(_BASE, _IMPL, new_impl)


def _impl_proof(new_impl, new_proof_body):
    """Reshape the impl region AND retune the tactic body."""
    src = _swap(_BASE, _IMPL, new_impl)
    return _swap(src, _PROOF, "prove_correct encodeSession by\n" + new_proof_body)


def _legacy_impl(legacy_branch):
    """A rival that keeps the standard branch and swaps only the legacy arm."""
    return _impl(
        "    let result : Encoded :=\n"
        f"      if legacyHashMode then {legacy_branch}\n"
        "      else standardEncoding sessionData\n"
        "    return result")


def _standard_impl(standard_branch):
    """A rival that keeps the legacy branch and swaps only the standard arm."""
    return _impl(
        "    let result : Encoded :=\n"
        "      if legacyHashMode then legacyEncoding sessionData\n"
        f"      else {standard_branch}\n"
        "    return result")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- and its post-image is built from opaque helpers, so a witness reaches the
# ---- impl through Velvet's extractor and CONDITIONS on the carrier: it
# ---- quantifies over a symbolic `d`, assumes one disequality of opaque
# ---- composites (`rival_out ≠ post_image` — exactly the sub-region the rival
# ---- mishandles), and shows the extracted program's output differs from the
# ---- post-image there. `encodeSessionExec d mode` is `NonDetT.run
# ---- (encodeSession d mode)`, reducing to `DivM.res result`. Checked in a file
# ---- whose `prove_correct` block is stripped, so no tactic script can mask the
# ---- verdict; the lone hypothesis `h` is an ordinary equality of opaque terms,
# ---- not an assumption of the conclusion, and is jointly satisfiable.
def _wit(rival_out, mode, post_image):
    return (
        "extract_program_for encodeSession\n\n"
        f"example (d : SessionData) (h : {rival_out} ≠ {post_image}) :\n"
        f"    encodeSessionExec d {mode} ≠ DivM.res ({post_image}) := by\n"
        "  unfold encodeSessionExec encodeSession\n"
        "  simp [NonDetT.run, pure, h]\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # dispatches that MUST verify. If a faithful correct impl cannot verify,
    # the spec is SPEC-TOO-STRONG on the SHAPE of the dispatch. Each keeps both
    # `ensures` clauses and only reshapes the executable surface.
    # =====================================================================
    {
        "id": "pos-negated-guard",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: negate the mode guard and swap the branches — the standard
        # form is emitted in the else, the legacy form when the negated guard
        # fails. Same mode-to-form decision. (Sibling: pos-reorder.)
        "module": _impl(
            "    let result : Encoded :=\n"
            "      if legacyHashMode = false then standardEncoding sessionData\n"
            "      else legacyEncoding sessionData\n"
            "    return result"),
        "rationale": "negating the mode guard and swapping the branches preserves "
                     "the mode-to-form decision, so both clauses "
                     "(`legacyHashMode = true → out = legacyEncoding sessionData` "
                     "and the false-mode clause) still discharge; a correct "
                     "reshape must verify, else SPEC-TOO-STRONG on the dispatch "
                     "shape.",
    },
    {
        "id": "pos-match-dispatch",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the same two-way decision written as a `match` on the flag
        # instead of an `if`. Identical form per branch; exercises the flag on
        # both values.
        "module": _impl(
            "    let result : Encoded :=\n"
            "      match legacyHashMode with\n"
            "      | true  => legacyEncoding sessionData\n"
            "      | false => standardEncoding sessionData\n"
            "    return result"),
        "rationale": "rewriting the flag dispatch as a `match` over both boolean "
                     "values yields the same form on each branch, so both "
                     "`ensures` clauses hold pointwise; must verify.",
    },
    {
        "id": "pos-legacy-inlined",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: inline the legacy composition (serialize, hash, package) in
        # the legacy branch instead of naming the deep-model function. Same
        # value by definition of that function; the proof unfolds it.
        "module": _impl_proof(
            "    let result : Encoded :=\n"
            "      if legacyHashMode then wrap (hashOf (serialize sessionData)) (serialize sessionData)\n"
            "      else standardEncoding sessionData\n"
            "    return result",
            "  loom_solve <;> simp_all [legacyEncoding]"),
        "rationale": "writing the legacy branch as the explicit composition of "
                     "the building blocks equals the deep-model value by "
                     "definition, so `legacyHashMode = true → out = "
                     "legacyEncoding sessionData` still discharges (the proof "
                     "unfolds the definition); must verify, else SPEC-TOO-STRONG "
                     "against a correct inlining of the modeled behaviour.",
    },

    # =====================================================================
    # ADMISSIBILITY — no `require` clause exists, so the "normal input meets
    # the precondition" probe is vacuous. The analogue on a TOTAL domain is the
    # obligation being UNSATISFIABLE at exactly an F2P-shaped input: a
    # post-image no value can meet (or one meetable only by a degenerate,
    # ungrounded value) is PRECOND-TOO-STRONG by the other door — the verifier
    # would then discharge the method vacuously and the spec would attest to
    # nothing. The in-region assert discharges the obligation AT BOTH CONCRETE
    # MODE VALUES, each existential grounded to the value that mode's clause
    # names, before the frozen impl closes the method's own obligations
    # verbatim.
    #
    # NOT a restatement of a definition. An earlier form of this case asserted
    # only `legacyEncoding sessionData = wrap (hashOf (serialize sessionData))
    # (serialize sessionData)`, which is closed by bare `rfl` (it is the
    # defining equation of `legacyEncoding` unfolded) — it passed while probing
    # nothing about satisfiability. This form is checked LIVE against three
    # negative controls of the identical shape, each of which leaves an unsolved
    # goal: grounding the legacy arm's witness to `standardEncoding sessionData`;
    # grounding the standard arm's witness to the legacy composition; grounding
    # the legacy arm to a FIXED datum's frame (`wrap (hashOf (serialize 0))
    # (serialize 0)`). So the assert tracks the claim rather than holding for any
    # claim, and it fails exactly when a mode's clause is unmeetable at that mode.
    # =====================================================================
    {
        "id": "admiss-legacy-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(
            "    assert (with_name_prefix `assert\n"
            "      ((∃ out : Encoded,\n"
            "          (true = true  → out = legacyEncoding sessionData) ∧\n"
            "          (true = false → out = standardEncoding sessionData) ∧\n"
            "          out = wrap (hashOf (serialize sessionData)) (serialize sessionData))\n"
            "        ∧ (∃ out : Encoded,\n"
            "          (false = true  → out = legacyEncoding sessionData) ∧\n"
            "          (false = false → out = standardEncoding sessionData) ∧\n"
            "          out = standardEncoding sessionData)))\n"
            + _IMPL,
            "  loom_solve <;> simp_all [legacyEncoding]"),
        "rationale": "the two-clause post-image is JOINTLY SATISFIABLE at each "
                     "concrete mode value, by a value GROUNDED in the input rather "
                     "than a free-floating one: the in-region assert exhibits, for "
                     "`legacyHashMode = true`, an `out` meeting both clauses and "
                     "equal to the composition of the building blocks over "
                     "`sessionData`, and for `legacyHashMode = false` an `out` "
                     "meeting both clauses and equal to the standard form. The "
                     "frozen impl is kept verbatim so both `ensures` clauses still "
                     "discharge too. If it fails => the obligation is unsatisfiable "
                     "/ over-constrained at an F2P-shaped input, so the method's "
                     "own proof would be discharging a post-image no faithful value "
                     "can meet (PRECOND-TOO-STRONG by the total-domain door).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked, satisfiable refutation
    # witness that CONDITIONS on the carrier (see the module docstring) and the
    # refinement argument for why its faithful real counterpart would NOT resolve
    # the failing tests. The first three attack clause A (the load-bearing legacy
    # round-trip, `legacyHashMode = true`); the fourth attacks clause B
    # (`legacyHashMode = false`) so the mode binder is moved across both values.
    # =====================================================================
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # The literal PRE-PATCH bug: ignore the mode and emit the standard form
        # in BOTH regimes. In legacy mode the output is `standardEncoding d`
        # where clause A demands `legacyEncoding d`. (Sibling: weak-prepatch.)
        "module": _legacy_impl("standardEncoding sessionData"),
        "refinement": "this is the base_commit behaviour (always emit the standard "
                      "signed form). In the legacy hashing-algorithm regime the "
                      "written data is the standard form, which the long-standing "
                      "legacy reader cannot read back — exactly the public "
                      "report's defect. Its faithful counterpart is the unpatched "
                      "repo, on which the failing legacy-decode test observes a "
                      "record it cannot recover. It would NOT resolve.",
        "rationale": "REJECT from clause A (`legacyHashMode = true → out = "
                     "legacyEncoding sessionData`): in legacy mode the rival "
                     "returns `standardEncoding d` where the post-image demands "
                     "`legacyEncoding d`. Refuted wherever the two composites "
                     "differ (`standardEncoding d ≠ legacyEncoding d`) — the "
                     "sub-domain the whole fix is about.",
        "witness": _wit("standardEncoding d", "true", "legacyEncoding d"),
    },
    {
        "id": "weak-legacy-fixed-payload",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: build a WELL-FORMED legacy frame (right shape, hash and
        # payload internally consistent) but of a FIXED datum instead of the
        # input — `legacyEncoding 0`. Correct only when the input coincides with
        # that datum; wrong on every other record. (Sibling: weak-legacy-empty.)
        "module": _legacy_impl("legacyEncoding 0"),
        "refinement": "a counterpart whose legacy encoder serialized a FIXED "
                      "record (e.g. the empty record) instead of the caller's "
                      "session data would build a well-formed legacy frame that "
                      "the legacy reader reads back to that fixed record for every "
                      "input — so a non-matching record round-trips to the wrong "
                      "value and the failing legacy-decode test still fails. "
                      "Correct only on the one coinciding record, a true "
                      "partial-domain break. It would NOT resolve.",
        "rationale": "REJECT from clause A: in legacy mode the rival returns "
                     "`legacyEncoding 0` where the post-image demands "
                     "`legacyEncoding d`. Refuted wherever `legacyEncoding 0 ≠ "
                     "legacyEncoding d` — every record whose encoding differs from "
                     "the fixed datum's. Distinct from weak-prepatch: this rival "
                     "IS a valid legacy frame, just of the wrong data.",
        "witness": _wit("legacyEncoding 0", "true", "legacyEncoding d"),
    },
    {
        "id": "weak-legacy-mis-wrapped",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS on the internal structure of the frame: hash the RIGHT data
        # but package a DIFFERENT serialized body (`serialize 0`). The frame's
        # stored hash no longer matches its payload, so the legacy reader (which
        # recomputes the hash over the payload and compares) rejects it. Isolates
        # the composition structure clause A pins. (Sibling: weak-legacy-modern-tag.)
        "module": _legacy_impl(
            "wrap (hashOf (serialize sessionData)) (serialize 0)"),
        "refinement": "a counterpart that packaged a serialized body inconsistent "
                      "with the stored content hash would produce a blob the "
                      "long-standing legacy reader does not accept as a valid "
                      "legacy frame (it recomputes the hash over the payload and "
                      "rejects a mismatch), so the legacy round trip the failing "
                      "test asserts does not recover the record. It would NOT "
                      "resolve.",
        "rationale": "REJECT from clause A: the rival hashes `serialize d` but "
                     "wraps `serialize 0`, so it equals `legacyEncoding d = wrap "
                     "(hashOf (serialize d)) (serialize d)` only where the two "
                     "packaged bodies coincide. Refuted wherever `wrap (hashOf "
                     "(serialize d)) (serialize 0) ≠ legacyEncoding d`. A near-miss "
                     "the fixed-payload rival (whole-frame wrong) does not "
                     "subsume: here the HASH is right and only the packaged body "
                     "is wrong.",
        "witness": _wit(
            "wrap (hashOf (serialize d)) (serialize 0)", "true",
            "legacyEncoding d"),
    },
    {
        "id": "weak-standard-mis-wrapped",
        "kind": "uniqueness",
        "expect": "reject",
        # CLAUSE B (moves the mode binder to false). In the standard regime emit
        # a frame that is NEITHER the standard signed form NOR a legacy-readable
        # frame: a hash/payload-mismatched blob (`wrap (hashOf (serialize 0))
        # (serialize d)`). Correct on the legacy branch; wrong on the standard
        # branch.
        "module": _standard_impl(
            "wrap (hashOf (serialize 0)) (serialize sessionData)"),
        "refinement": "in the standard (non-legacy) regime the encoder must emit "
                      "the standard signed form that the ordinary loader inverts. "
                      "A counterpart emitting a blob that is neither the standard "
                      "form nor a valid legacy frame would break the ordinary "
                      "encode/decode round trip the unchanged tests exercise, so "
                      "those tests still fail. It would NOT resolve. (This does NOT "
                      "attack the conservative modern-arm question the sibling "
                      "declines — a legacy frame in the standard regime would still "
                      "round-trip via the reader fallback; this rival's output "
                      "round-trips through neither reader.)",
        "rationale": "REJECT from clause B (`legacyHashMode = false → out = "
                     "standardEncoding sessionData`): in standard mode the rival "
                     "returns `wrap (hashOf (serialize 0)) (serialize d)` where "
                     "the post-image demands `standardEncoding d`. Refuted "
                     "wherever those differ. This is the only rival that moves the "
                     "mode binder to `false` and attacks clause B.",
        "witness": _wit(
            "wrap (hashOf (serialize 0)) (serialize d)", "false",
            "standardEncoding d"),
    },
    {
        "id": "weak-mode-ignored-legacy",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED by audit. The MIRROR of weak-prepatch: ignore the mode and emit
        # the LEGACY form in BOTH regimes. weak-prepatch collapses the dispatch
        # onto the standard arm; nothing shipped collapsed it onto the legacy arm,
        # so a rival that simply drops the guard in that direction escaped the
        # battery. Attacks clause B with the mode binder at `false`.
        "module": _impl(
            "    let result : Encoded :=\n"
            "      if legacyHashMode then legacyEncoding sessionData\n"
            "      else legacyEncoding sessionData\n"
            "    return result"),
        "refinement": "a counterpart that emitted the legacy-compatibility form "
                      "unconditionally — never consulting the mode at all — writes "
                      "a legacy frame in the standard regime. This is NOT the "
                      "conservative modern-arm question the sibling declines "
                      "(there the concern is only whether such a frame still round "
                      "trips): the observable break is that the standard regime's "
                      "output is no longer the standard signed form, so every "
                      "unchanged consumer that inverts it with the standard loader "
                      "— rather than the reader that tolerates the legacy shape — "
                      "no longer recovers the record, and the mode selector the "
                      "public report is about has no effect whatsoever. It would "
                      "NOT resolve.",
        "rationale": "REJECT from clause B (`legacyHashMode = false → out = "
                     "standardEncoding sessionData`): the rival returns "
                     "`legacyEncoding d` in the standard regime where the "
                     "post-image demands `standardEncoding d`. Refuted wherever "
                     "the two composites differ. Distinct from "
                     "weak-standard-mis-wrapped (which emits a malformed blob): "
                     "this rival's standard-arm output is a WELL-FORMED legacy "
                     "frame of the right data, so it isolates the DISPATCH itself "
                     "rather than the frame's internal structure.",
        "witness": _wit("legacyEncoding d", "false", "standardEncoding d"),
    },
    {
        "id": "weak-legacy-mishashed",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED by audit. The MIRROR-IMAGE near-miss of weak-legacy-mis-wrapped:
        # package the RIGHT serialized body but stamp it with the hash of a
        # DIFFERENT one. mis-wrapped gets the hash right and the body wrong; this
        # gets the body right and the hash wrong. Both halves of the composition
        # are now probed independently, so a rival wrong in only the hash slot no
        # longer escapes.
        "module": _legacy_impl(
            "wrap (hashOf (serialize 0)) (serialize sessionData)"),
        "refinement": "a counterpart that computed the content hash over a "
                      "different datum than the one it packaged would emit a blob "
                      "whose stored hash does not match its own payload. The "
                      "long-standing legacy reader recomputes the hash over the "
                      "payload and compares it to the stored one, so it rejects "
                      "the frame and the legacy round trip the failing test "
                      "asserts does not recover the record. It would NOT resolve.",
        "rationale": "REJECT from clause A: the rival wraps `serialize d` (the "
                     "right body) under `hashOf (serialize 0)` (the wrong hash), so "
                     "it equals `legacyEncoding d = wrap (hashOf (serialize d)) "
                     "(serialize d)` only where the two hashes coincide. Refuted "
                     "wherever `wrap (hashOf (serialize 0)) (serialize d) ≠ "
                     "legacyEncoding d`. The exact converse of "
                     "weak-legacy-mis-wrapped, which neither it nor the "
                     "fixed-payload rival subsumes: here the packaged BODY is "
                     "right and only the HASH slot is wrong.",
        "witness": _wit(
            "wrap (hashOf (serialize 0)) (serialize d)", "true",
            "legacyEncoding d"),
    },
]


# ---------------------------------------------------------------------------
# Sibling (nagini) -> velvet accounting. The sibling battery ships 6 SPEC cases
# (1 soundness positive, 1 admissibility, 1 frame-mutation rival, 3
# uniqueness/partial-domain rivals) plus 3 AXIOM_TESTS. Every one is accounted
# for. The sibling contracts one function, `serialize`, over a rich Frame
# carrier (tag/mac/payload) with a fractional heap permission and a @Pure
# `legacy_read` deep model; this bundle contracts one method, `encodeSession`,
# over ABSTRACT opaque carriers with a deep `legacyEncoding` composition and no
# axioms. The two surfaces model the SAME dispatch; the carrier is coarser here
# (a single opaque `Encoded` instead of the tag/mac/payload triple), which is
# what governs the porting mechanics — but NOT the reachability of the reject
# lane (see below).
#
#   sibling case              kind          -> here                        status
#   -------------------------------------------------------------------------
#   pos-reorder               soundness     -> pos-negated-guard           PORTED
#   admiss-reads              admissibility -> admiss-legacy-grounded      RE-AIMED
#   frame-mut-write           uniqueness    -> (none)                      VACUOUS
#   weak-prepatch             uniqueness    -> weak-prepatch               PORTED
#   weak-legacy-empty         uniqueness    -> weak-legacy-fixed-payload   RE-SITED
#   weak-legacy-modern-tag    uniqueness    -> weak-legacy-mis-wrapped     RE-SITED
#   ax-sound-keyed_digest     axiom         -> (none)                      G-AX
#   ax-sound-modern_serialize axiom         -> (none)                      G-AX
#   ax-f2p-route              axiom         -> (none)                      G-AX
#
# PORTED / RE-SITED (soundness, 1): pos-reorder -> pos-negated-guard. Two
#   further positives are ADDED (pos-match-dispatch, pos-legacy-inlined) so the
#   reshape space — the flag on both values, and the deep composition written
#   inline — is exercised, not a single reorder.
# RE-AIMED (admissibility, 1): admiss-reads relied on the sibling's non-trivial
#   half-permission precondition admitting a normal record's reads. No method
#   here has a `require` clause, so that probe is vacuous. Re-aimed at the
#   total-domain admissibility risk: the legacy post-image being degenerate /
#   ungrounded. admiss-legacy-grounded discharges a live in-region assert that
#   the legacy post-image is the composition of the building blocks over the
#   input.
# VACUOUS — frame/permission-mutation (1): frame-mut-write rejects a no-op WRITE
#   to a read-only heap input for insufficient fractional permission. This
#   backend is referentially transparent, has no heap and no aliasing, and this
#   bundle declares NO `mut` binder — there is no read-only input to mutate. The
#   sibling itself calls this class its #1 weakness class ON NAGINI; it simply
#   does not exist on this carrier. No substitute fabricated.
# PORTED / RE-SITED — uniqueness (3), the load-bearing lane of the port. All
#   three sibling rivals attack the legacy round-trip clause (Q3 there = clause A
#   here). On the sibling's rich Frame carrier each is refuted by the @Pure
#   `legacy_read` model reading the concrete frame fields. HERE the observable is
#   a single opaque `Encoded`, so a `decide`-on-a-literal witness gets stuck —
#   but the rival's violation is in every case an opaque-composite DISEQUALITY,
#   and a witness need not PROVE it, only ASSUME it and refute the rival on that
#   sub-region (conditioning on the carrier; see the module docstring). This is
#   the technique the porting rules direct one to before declaring the lane
#   inexpressible, and it is verified to work here (two real builds + a
#   satisfiability probe per rival):
#     - weak-prepatch:            standardEncoding d ≠ legacyEncoding d
#     - weak-legacy-fixed-payload: legacyEncoding 0 ≠ legacyEncoding d
#     - weak-legacy-mis-wrapped:  wrap (hashOf (serialize d)) (serialize 0)
#                                 ≠ legacyEncoding d
#   None of these disequalities is a theorem in EITHER direction (the carriers
#   are opaque with no separating axiom), which is exactly what makes each a
#   sound hypothesis: the witness cannot prove it (so gold, which satisfies the
#   post-image, refutes the witness) and cannot refute it (so the consistency
#   probe cannot derive False from it). weak-legacy-empty re-sites as
#   weak-legacy-fixed-payload (a valid legacy frame of a FIXED datum — correct on
#   one record, wrong elsewhere — rather than literally the empty payload, which
#   is not observable through the abstract carrier); weak-legacy-modern-tag
#   re-sites as weak-legacy-mis-wrapped (the internal hash/payload consistency
#   the legacy reader checks is broken, rather than the frame tag, which this
#   carrier does not expose as a field). The refinement argument is unchanged in
#   both.
# ADDED BY AUDIT (uniqueness, 2): weak-mode-ignored-legacy and
#   weak-legacy-mishashed. An independent SPEC-TOO-WEAK sweep built seven new wrong
#   impls the battery did not contain and confirmed the frozen spec rejects all
#   seven, but two of those directions were reachable by a rival simpler than
#   anything shipped and so are now carried as cases rather than left to a
#   one-off probe: collapsing the dispatch onto the LEGACY arm (the mirror of
#   weak-prepatch, which collapses it onto the standard arm), and getting the
#   legacy frame's HASH slot wrong while the packaged BODY is right (the converse
#   of weak-legacy-mis-wrapped). Both ship a witness verified to elaborate against
#   the rival and fail on the frozen solution.
# ADDED (uniqueness, 1): weak-standard-mis-wrapped. The sibling attacks only Q3
#   (legacy) with reject rivals and deliberately declines a modern-arm reject
#   (its Q4/clause B is conservative: a legacy frame in the standard regime would
#   still round-trip via the reader fallback and resolve — see the sibling's Q4
#   note). This rival does NOT make that false claim; it emits a blob that is
#   NEITHER the standard form NOR a legacy-readable frame, which breaks the
#   ordinary decode round trip the unchanged tests exercise (would NOT resolve).
#   It is added for BINDER + CLAUSE COVERAGE: without it the mode binder would be
#   pinned at `true` across every reject witness and clause B would go un-attacked,
#   so a rival mishandling only the standard branch would escape the battery.
# AXIOM_TESTS (3): dropped. The axiom lane is G-AX's job (meta.json records the
#   G-AX pass over the real callees), and this gate ignores AXIOM_TESTS.
#
# BINDER / CLAUSE COVERAGE. The two input binders are `sessionData` and
# `legacyHashMode`. `legacyHashMode` is moved across BOTH values by the reject
# witnesses (true for the four clause-A rivals, false for the two clause-B
# rivals). `sessionData` is an opaque handle with no literal value to
# enumerate — every witness quantifies over a symbolic `d` and conditions on a
# distinct structural fact about it (its standard vs legacy encoding; its
# encoding vs a fixed datum's; its serialized body vs a fixed one's; its
# serialized body's HASH vs a fixed one's), so the input is not held at a single
# point. Both independent post-image clauses are attacked: clause A by four
# rivals, clause B by two. Every reject witness was verified out-of-band to (1)
# elaborate against its rival, (2) fail against the frozen solution, and (3) have
# jointly-satisfiable binders (the consistency probe does not close).
#
# AUDIT ADDENDUM — the gold-side failures are not merely "semantic-looking". For
# each reject case the flipped-claim FORGERY was built on both sides: asserting
# `encodeSessionExec d mode = DivM.res (post_image)` (i.e. that the impl is
# CORRECT at the hypothesised point) SUCCEEDS against the frozen solution and
# FAILS against the rival — the exact inversion of the witness. So gold's exit
# code tracks the claim rather than a fixed tactic mismatch, and none of these
# cases is hollow. The `⊢ False` goals gold leaves are also real reductions: the
# `h` hypothesis is reported UNUSED there (`simp` closed the equation from the
# impl alone), while against each rival `h` is what discharges the goal.
AXIOM_TESTS = []
