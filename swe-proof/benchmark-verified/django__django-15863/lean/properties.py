"""properties.py — G-PBT falsification battery for django__django-15863 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and every ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with every obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total behavior over an exact-value carrier):

  coerceDecimal (text : Rat) : Rat        result = text

  The single modeled behavior coerces an incoming exact value into the working
  value that will be handed to the formatting step. The load-bearing (and only)
  postcondition clause is the exact-value identity ``result = text``: the
  working value equals the input value EXACTLY, so every significant digit is
  retained no matter how many there are. This is the whole guarantee the issue
  and the F2P precision case turn on — a request for many fractional places can
  only reproduce all of them if none were lost in the coercion.

ADVERSARIAL READ of the classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. This backend is referentially
    transparent: the input carries no heap permission, there is no read-only
    half-permission to overwrite and no aliasing to exploit. The nagini
    frame-mutation rival (a no-op write-back into a read-only input) has no
    expressible instance here, and no substitute is fabricated for it.

  * UNGROUNDED-ORACLE ECHO — VACUOUS as a WRONG echo. The postcondition is
    GROUNDED in the argument (an equality of the result against the input value
    itself, fully unfolded). There is one ``opaque`` callee (the binary
    approximation fallback), but the postcondition never references it, so there
    is no answer key an implementation could echo without doing the work. The
    unique satisfier of ``result = text`` IS the input, so the honest control is
    the cheapest faithful implementation (the positive controls below), not a
    wrong echo.

  * OPAQUE-ROUTE / STAGE-SELECTION — LIVE, and NOT vacuous, contrary to what an
    earlier read of this carrier concluded. The ``opaque`` fallback carries no
    value-preservation property, so an implementation that hands the value to it
    instead of to the exact read-back cannot satisfy ``result = text``. Nothing
    has to COMPUTE the opaque term to show this: the refutation is stated at a
    point described by HYPOTHESIS (``floatFallback v ≠ v``), and the gate's own
    consistency probe then confirms those hypotheses are satisfiable — which an
    opaque term makes easy, since no tactic can derive ``False`` from it. This is
    the ``weak-fallback-route`` rival below, and it is the class closest to the
    behavior the issue reports (a value routed through a bounded-precision
    representation rather than carried exactly).

  * DIVERGENCE / NON-TERMINATION — a KNOWN HOLE, not a vacuous class. This is
    vanilla Lean with no ``loom.semantics.termination`` setting; a total ``def``
    must be accepted by the elaborator, and a rival written as a ``partial def``
    self-call is in variant scope and IS rejected. But it cannot be shipped: a
    ``partial def`` is opaque to reduction, so the only witness shape available
    is conditioned on the impl's own value, and such a witness ELABORATES against
    the frozen solution too (measured: exit 0), i.e. it is a tautology that
    discriminates nothing. No discriminating witness exists for this class on
    this carrier, so the class is recorded as an unclosed hole rather than
    fabricated into a case the gate would read as inconclusive.

  * CONTROL-FLOW-EFFECT — VACUOUS. The modeled behavior is a single
    straight-line value coercion; the surrounding try/except is UNCHANGED
    control flow that the modeled delta does not touch, and the postcondition is
    a total value identity, so there is no effect invisible to the value
    abstraction to discriminate.

  * PARTIAL-DOMAIN / VALUE — the live class, and where the bug lives. A rival
    can be correct on a coarse sub-domain (values expressible at low precision)
    yet diverge on the high-precision sub-domain the F2P pins. Three rivals
    attack the identity from that angle: collapse the value to a constant, drop
    all sub-integer precision, and drop precision past a fixed number of
    fractional places (the truncate-past-a-budget shape — the closest analogue
    on this carrier of the nagini binary-significand truncation bug).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script (``intro; unfold …; rfl``) is
tuned to the frozen form — so a rejection alone attributes nothing to the spec.
Every ``expect="reject"`` case therefore carries a Lean snippet proving the
rival CONTRADICTS the spec at one concrete input. Each is stated directly
against the spec predicate at a ``decide``/``norm_num``-able rational literal,
and each was checked to hold of its rival and to FAIL on the frozen solution (so
it discriminates rather than asserting a tautology).

Witness inputs are spread across the domain rather than fixed at one convenient
point: the constant-collapse rival is refuted at a nonzero integer (where a
constant-0 result diverges), the drop-all-precision rival at a value with a
nonzero fractional part (an integer would not catch it), the
truncate-past-a-budget rival at a value whose precision runs one place PAST the
budget (a value inside the budget would not catch it — that is exactly the
near-miss point), and the fallback-route rival at a value carrying far more
significant digits than a bounded-precision representation holds. The single spec
binder ``text`` therefore takes four distinct values across the reject witnesses,
so the battery demonstrates the spec's dependence on the input rather than
probing one point.

Each witness's gold-side failure was additionally FORGERY-tested: a second file
differing from the witness only in what it CLAIMS (the ``¬`` dropped, so it
asserts the frozen solution is CORRECT at that input) was built against the
frozen solution and ELABORATES (exit 0) where the witness FAILS (exit 1). The
gold-side exit code therefore tracks the claim rather than a tactic mismatch, so
each rejection is attributable to the spec.

The truncate-past-a-budget rival is a genuine NEAR-MISS of the
drop-all-precision rival: it agrees with the spec over strictly more of the
domain (every value expressible in the budget, not only the integers), so it is
refuted at its OWN divergent point (a value one place past the budget) rather
than sharing the coarser rival's witness.

AXIOM lane: EMPTY here by construction. The bundle declares one ``opaque``
callee (the binary-approximation fallback) with NO value-preservation property —
it is deliberately un-pinned, being exactly the lossy path the bug used — so it
carries no axiom-soundness / axiom-containment obligation for this gate to probe
(the axiom lane is G-AX's job in any case).
"""
from pathlib import Path

INSTANCE = "django__django-15863"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL body of the single impl region (everything strictly between the
# `-- impl-start` / `-- impl-end` markers), and the FULL tactic body of the
# single proof region, so every replacement lands entirely inside the region it
# means to edit.
_I_IMPL = (
    "  -- The primary stage renders the value as a decimal literal and reads it back.\n"
    "  -- For an exact decimal value that literal is always a valid decimal, so the\n"
    "  -- primary read succeeds.\n"
    "  let primaryReadSucceeds : Bool := true\n"
    "  if primaryReadSucceeds then\n"
    "    -- read back the exact same value\n"
    "    return text\n"
    "  -- Fallback stage (reached only if the primary read fails to yield a decimal):\n"
    "  -- route the value through a binary floating-point approximation.\n"
    "  return floatFallback text"
)
assert _BASE.count(_I_IMPL) == 1, "impl region drifted from expected text"

_P_PROOF = (
    "  intro\n"
    "  unfold problem_spec_coerceDecimal implementation_coerceDecimal\n"
    "  rfl"
)
assert _BASE.count(_P_PROOF) == 1, "proof region drifted from expected text"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Each
    # keeps the `theorem correct_coerceDecimal` statement byte-identical; the
    # frozen tactic body still closes for these reshapes (the reduction reaches
    # the same normal form), so no new declaration, axiom, or assumption token
    # is introduced.
    # =====================================================================
    {
        "id": "pos-negated-guard",
        "kind": "soundness",
        "expect": "verify",
        # Branch reorder: handle the fallback under a negated guard and fall
        # through to the exact read-back. Same coercion value on every input.
        "module": _swap(
            _BASE, _I_IMPL,
            "  -- The primary stage renders the value as a decimal literal and reads it back.\n"
            "  -- For an exact decimal value that literal is always a valid decimal, so the\n"
            "  -- primary read succeeds.\n"
            "  let primaryReadSucceeds : Bool := true\n"
            "  if !primaryReadSucceeds then\n"
            "    -- route the value through a binary floating-point approximation\n"
            "    return floatFallback text\n"
            "  -- read back the exact same value\n"
            "  return text",
        ),
        "rationale": "reordering the two exits behind a negated guard preserves "
                     "the exact coercion value, so `result = text` still holds; "
                     "must verify (else SPEC-TOO-STRONG on the single identity "
                     "clause). Proof: the frozen tactic body (`intro; unfold …; "
                     "rfl`) still closes — the reshaped `if !true` reduces to the "
                     "same read-back.",
    },
    {
        "id": "pos-carried-local",
        "kind": "soundness",
        "expect": "verify",
        # Local-binding reshape: bind the value to a fresh local before reading
        # it back. Same value flows out of the primary stage.
        "module": _swap(
            _BASE, _I_IMPL,
            "  -- The primary stage renders the value as a decimal literal and reads it back.\n"
            "  -- For an exact decimal value that literal is always a valid decimal, so the\n"
            "  -- primary read succeeds.\n"
            "  let primaryReadSucceeds : Bool := true\n"
            "  if primaryReadSucceeds then\n"
            "    -- read back the exact same value, via a fresh local\n"
            "    let carried := text\n"
            "    return carried\n"
            "  -- Fallback stage (reached only if the primary read fails to yield a decimal):\n"
            "  -- route the value through a binary floating-point approximation.\n"
            "  return floatFallback text",
        ),
        "rationale": "binding the coerced value to a local before returning it "
                     "keeps `result = text`; a correct reshape must verify. "
                     "Proof: the frozen tactic body still closes (the local is "
                     "zeta-reduced, so `rfl` reaches the same value).",
    },
    {
        "id": "pos-loop-carried",
        "kind": "soundness",
        "expect": "verify",
        # A reshape that is NOT definitionally equal to the frozen impl. The two
        # positives above are: `rfl` alone proves `negatedGuard t = frozenImpl t`
        # and `carriedLocal t = frozenImpl t` for every `t` (measured, exit 0),
        # because `if !true` and a zeta-reducible `let` both reduce away. So they
        # exercise the obligation only up to definitional unfolding. This one
        # carries the value through an accumulator and a bounded loop, whose
        # `forIn`/`ForInStep.yield` term is NOT definitionally equal to the frozen
        # body (`rfl` on the two impls FAILS: "loopCarried t is not definitionally
        # equal to frozenImpl t"), so the frozen `rfl` script no longer closes and
        # the proof region must genuinely re-derive the identity via `simp`. That
        # is what makes this a real soundness control rather than a restatement.
        "module": _swap(
            _swap(
                _BASE, _I_IMPL,
                "  -- Accumulate the coerced value through a single carrying step instead\n"
                "  -- of returning it directly from the guarded branch.\n"
                "  let mut carried := text\n"
                "  for _ in [0:1] do\n"
                "    carried := carried\n"
                "  return carried",
            ),
            _P_PROOF,
            "  intro\n"
            "  unfold problem_spec_coerceDecimal implementation_coerceDecimal\n"
            "  simp",
        ),
        "rationale": "carrying the coerced value through an accumulator and a "
                     "bounded loop preserves it, so `result = text` still holds "
                     "and a faithful correct reshape must verify (else "
                     "SPEC-TOO-STRONG). Unlike the two positives above — each of "
                     "which `rfl` alone proves equal to the frozen impl pointwise, "
                     "so they test the obligation only up to definitional "
                     "unfolding — this impl is NOT definitionally equal to the "
                     "frozen one (`rfl` between the two impls fails), so the "
                     "identity is re-derived by `simp` over the loop term rather "
                     "than restated. Verified with the real verifier (exit 0).",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at a normal, F2P-shaped input rather than only
    # provable in the abstract. The frozen theorem carries NO precondition
    # hypothesis (the modeled behavior is total, so `∀` is unguarded), so the
    # nagini precondition-admission probe has no binder to attack here; the
    # honest analogue is to discharge the spec predicate at a concrete
    # exact-value input by evaluation, inside the proof region, alongside the
    # frozen obligation. If that ground instance could not be discharged, the
    # modeled behavior would be unsatisfiable at exactly the shape the F2P
    # exercises (the PRECOND-TOO-STRONG analogue).
    # =====================================================================
    {
        "id": "admiss-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        # The ground instance is taken at an input of the SHAPE the precision case
        # exercises — a value with more than twenty significant digits — not at a
        # small integer. At `3` the `have` is discharged by `decide` and says only
        # that the obligation is satisfiable at a point the frozen `rfl` already
        # reaches; the whole force of this lane is that it is satisfiable at the
        # high-precision shape, which is where an unsatisfiable obligation would
        # bite. (`decide` is NOT usable at that input: the `Decidable` instance
        # gets stuck on `Rat.inv`, "did not reduce to `isTrue` or `isFalse`" —
        # measured. `rfl` discharges it, so the evaluation is real, not assumed.)
        "module": _swap(
            _BASE, _P_PROOF,
            "  have _ground : problem_spec_coerceDecimal\n"
            "      (123456123456789012345678901 / 1000000000000000000000 : Rat)\n"
            "      (implementation_coerceDecimal\n"
            "        (123456123456789012345678901 / 1000000000000000000000 : Rat)) := by\n"
            "    unfold problem_spec_coerceDecimal implementation_coerceDecimal\n"
            "    rfl\n"
            "  intro\n"
            "  unfold problem_spec_coerceDecimal implementation_coerceDecimal\n"
            "  rfl",
        ),
        "rationale": "the identity obligation is discharged by evaluation at a "
                     "concrete input carrying more than twenty significant digits "
                     "— the shape the precision case exercises — and only then is "
                     "the frozen obligation closed verbatim. Verifies (else the "
                     "spec is unsatisfiable at exactly that shape, the analogue of "
                     "PRECOND-TOO-STRONG). Nothing is assumed: no new declaration, "
                     "the theorem statement is byte-identical, and the ground "
                     "instance is a `have` inside the existing tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at
    # one concrete input. Each keeps the frozen proof body, which the reshaped
    # impl no longer satisfies — the witness, not the tactic break, is what
    # attributes the rejection to the spec.
    # =====================================================================
    {
        "id": "weak-collapse-constant",
        "kind": "uniqueness",
        "expect": "reject",
        # Collapses the coerced value to a constant: the working value no longer
        # depends on the input at all (correct only at that constant).
        "module": _swap(
            _BASE, _I_IMPL,
            "  -- Collapse the coerced value to a constant, ignoring the input.\n"
            "  let primaryReadSucceeds : Bool := true\n"
            "  if primaryReadSucceeds then\n"
            "    return 0\n"
            "  return floatFallback text",
        ),
        "refinement": "a coercion that produces a fixed value regardless of the "
                      "input renders every distinct value identically; it fails "
                      "the F2P precision case (which expects the input value back "
                      "in full) and every P2P formatting case whose input is not "
                      "that constant. It would NOT resolve.",
        "rationale": "REJECT from `result = text`: at any input other than the "
                     "constant the rival returns the constant where the spec "
                     "requires the input. Refuted at a nonzero integer, the "
                     "coarsest divergence point, distinct from the other rivals' "
                     "fractional witnesses.",
        "witness": (
            "-- A nonzero integer input: the coerced value must be the input\n"
            "-- itself, so a constant-0 result already diverges here.\n"
            "example : ¬ problem_spec_coerceDecimal 1 (implementation_coerceDecimal 1) := by\n"
            "  unfold problem_spec_coerceDecimal implementation_coerceDecimal\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-drop-fraction",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops ALL sub-integer precision: keeps the integer part only. Correct
        # on integer-valued inputs, wrong on any value with a fractional part.
        "module": _swap(
            _BASE, _I_IMPL,
            "  -- Keep only the integer part of the value, dropping sub-integer precision.\n"
            "  let primaryReadSucceeds : Bool := true\n"
            "  if primaryReadSucceeds then\n"
            "    return (⌊text⌋ : Rat)\n"
            "  return floatFallback text",
        ),
        "refinement": "discarding sub-integer precision loses every fractional "
                      "digit of the input; the F2P precision case pins a value "
                      "with a long fractional part and expects all of it back, so "
                      "it fails, as does any P2P case whose input is not "
                      "integer-valued. It would NOT resolve.",
        "rationale": "REJECT from `result = text`: on any value with a nonzero "
                     "fractional part the rival returns the integer part where "
                     "the spec requires the exact value. Refuted at a value with a "
                     "nonzero fractional part (an integer input would not catch "
                     "it), distinct from the other rivals' points.",
        "witness": (
            "-- A value with a nonzero fractional part: dropping sub-integer\n"
            "-- precision diverges from the exact value here.\n"
            "example : ¬ problem_spec_coerceDecimal (3/2) (implementation_coerceDecimal (3/2)) := by\n"
            "  unfold problem_spec_coerceDecimal implementation_coerceDecimal\n"
            "  simp only [Id.run]; norm_num [pure]\n"
        ),
    },
    {
        "id": "weak-truncate-budget",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS: keeps precision only up to a fixed number of fractional
        # places (a budget), dropping anything finer. Correct on every value
        # expressible within the budget — strictly more of the domain than
        # weak-drop-fraction — and wrong only on the higher-precision sub-domain.
        # This is the closest analogue on this carrier of the binary-significand
        # truncation bug (keep the leading budget of precision, lose the rest).
        "module": _swap(
            _BASE, _I_IMPL,
            "  -- Keep precision only up to a fixed number of fractional places.\n"
            "  let primaryReadSucceeds : Bool := true\n"
            "  if primaryReadSucceeds then\n"
            "    return ((⌊text * 100⌋ : Rat) / 100)\n"
            "  return floatFallback text",
        ),
        "refinement": "truncating precision past a fixed budget is exactly the "
                      "bug: the input is preserved only up to the budget and "
                      "everything finer is dropped. Its faithful real patch is "
                      "the coarse-precision path the issue reports; the F2P "
                      "precision case pins a value whose precision runs well past "
                      "any small budget and expects all of it back, so it fails. "
                      "It would NOT resolve — this is the precise divergence the "
                      "spec senses (G-DIFF).",
        "rationale": "REJECT from `result = text`: for a value whose precision "
                     "runs PAST the budget the rival emits a truncated value "
                     "where the spec requires the exact value. NEAR-MISS of "
                     "weak-drop-fraction: it agrees with the spec over strictly "
                     "more of the domain (every value inside the budget, not only "
                     "the integers), so it is refuted at its OWN divergent point — "
                     "a value one place past the budget — rather than sharing that "
                     "rival's fractional witness. If it VERIFIES => SPEC-TOO-WEAK "
                     "(precision past the budget is not pinned).",
        "witness": (
            "-- A value whose precision runs one place PAST the budget: within\n"
            "-- the budget this rival would AGREE with the spec (that is the\n"
            "-- near-miss), so it must be refuted here, on its own divergent\n"
            "-- sub-domain, not at a coarser point.\n"
            "example : ¬ problem_spec_coerceDecimal (1/8) (implementation_coerceDecimal (1/8)) := by\n"
            "  unfold problem_spec_coerceDecimal implementation_coerceDecimal\n"
            "  simp only [Id.run]; norm_num [pure]\n"
        ),
    },
    {
        "id": "weak-fallback-route",
        "kind": "uniqueness",
        "expect": "reject",
        # The stage-selection rival: hand the value to the bounded-precision
        # route instead of reading back the exact decimal literal. This is the
        # class the three value-level rivals above leave unattacked — they all
        # keep the exact-read-back stage and corrupt its value arithmetically,
        # whereas this one selects the OTHER stage, whose result carries no
        # value-preservation property at all.
        "module": _swap(
            _BASE, _I_IMPL,
            "  -- Route the value through the bounded-precision approximation\n"
            "  -- instead of reading back the exact decimal literal.\n"
            "  let primaryReadSucceeds : Bool := false\n"
            "  if primaryReadSucceeds then\n"
            "    return text\n"
            "  return floatFallback text",
        ),
        "refinement": "a coercion that always routes the value through a "
                      "bounded-precision binary representation preserves only as "
                      "many significant digits as that representation holds. The "
                      "precision case pins a value with far more digits than that "
                      "and expects every one of them back, so it fails; the issue "
                      "MWE is the same shape. It would NOT resolve.",
        "rationale": "REJECT from `result = text`: the fallback route carries NO "
                     "value-preservation property (it is deliberately un-pinned), "
                     "so the coerced value is not known to equal the input and the "
                     "identity cannot be discharged. Refuted at a value with more "
                     "than twenty significant digits — the shape the precision case "
                     "pins, and a fourth distinct witness point. If it VERIFIES => "
                     "SPEC-TOO-WEAK (the spec would not distinguish the exact "
                     "read-back stage from the lossy one, which is the entire "
                     "distinction it exists to make).",
        # Stated at a point described by HYPOTHESIS rather than computed: the route
        # is `opaque`, so no literal input decides it. That is sound here because
        # the gate's consistency probe confirms the hypothesis is satisfiable — no
        # tactic can derive `False` from `floatFallback v ≠ v` (measured: probe
        # exit 1 on both gold and the rival). Machine-checked: elaborates against
        # the rival (exit 0), FAILS on the frozen solution (exit 1), and the
        # flipped claim — the same file asserting the frozen solution is CORRECT
        # here — ELABORATES on gold (exit 0), so gold's exit code tracks the claim.
        "witness": (
            "-- A value carrying far more significant digits than a bounded-precision\n"
            "-- representation can hold, so the two coercion stages disagree there.\n"
            "example (h : floatFallback (123456123456789012345678901 / 1000000000000000000000 : Rat)\n"
            "      ≠ (123456123456789012345678901 / 1000000000000000000000 : Rat)) :\n"
            "    ¬ problem_spec_coerceDecimal\n"
            "      (123456123456789012345678901 / 1000000000000000000000 : Rat)\n"
            "      (implementation_coerceDecimal\n"
            "        (123456123456789012345678901 / 1000000000000000000000 : Rat)) := by\n"
            "  unfold problem_spec_coerceDecimal implementation_coerceDecimal\n"
            "  simpa using h\n"
        ),
    },
]
