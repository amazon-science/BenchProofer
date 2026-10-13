"""properties.py — G-PBT falsification battery for django__django-16485 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for the admissibility case, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_floatformat`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (one total function selecting between two renderings):

  floatformat (d : DecVal) (p : Int) : Option String
      result = (if decIsWhole d && decide (p ≤ 0)
                then some (numberFormat (toString (decIntPart d)) 0)
                else (decimalDigits d p).map (fun s => numberFormat s p.natAbs))

  The postcondition is a single top-level equation whose right-hand side is a
  two-armed ``if``. Its transparent, refutable structure has three independent
  facets, one per input binder of the selector plus the arm bodies:

    * SELECTOR (branch predicate) — ``decIsWhole d && decide (p ≤ 0)``: the
      "whole value AND non-positive place count" test. Two binders:
        - the ``decide (p ≤ 0)`` sub-term is the boundary the instance moved
          (``p < 0`` → ``p ≤ 0``); it changes which arm fires at ``p == 0``;
        - the ``decIsWhole d`` conjunct gates on the value being whole; dropping
          it fires the plain-integer arm on non-whole values too.
    * THEN-ARM — ``some (numberFormat (toString (decIntPart d)) 0)``: the plain
      integer rendering. Its argument is ``decIntPart d`` (the whole part) and a
      fixed place count ``0``.
    * ELSE-ARM — ``(decimalDigits d p).map (fun s => numberFormat s p.natAbs)``:
      the general rendering, ``none``-propagating, formatted at ``p.natAbs``
      places.

CARRIER NARROWING vs the nagini sibling. Nagini pins the ENTIRE output sequence
element-by-element to a fully-UNFOLDED grounded oracle ``rendered`` (digits,
sign, separator, every fractional zero), because it models the value-builder
concretely as a ``List[int]``. This Lean bundle models the fix at a different,
narrower altitude: the value's whole/fractional structure and the two
sub-renderings are UNCHANGED sub-computations, carried as ``opaque`` callees
(``decIsWhole`` / ``decIntPart`` / ``decimalDigits`` / ``numberFormat``), and the
spec pins only the branch SELECTION and the ARGUMENTS handed to each arm. So the
nagini cases that attack the *digit content* of the rendering — ``uniq-const-
zero-bare`` (wrong bare digits) and ``uniq-wrong-frac-fill`` (fractional field
'1' vs '0') — have no element-level counterpart here: the digit string is
``numberFormat``'s opaque output, not a transparent sequence. Their ARGUMENT-
level shadow IS ported (``weak-const-intpart-arg`` attacks the ``decIntPart d``
argument to the then-arm; ``weak-wrong-placecount`` attacks the ``p.natAbs``
argument to the else-arm), which is the strongest refutable form on this carrier.
The axiom-lane cases (``ax-sound-rendered`` / ``ax-cover-rendered``) are dropped:
the axiom lane is G-AX's job and this gate ignores it (``AXIOM_TESTS = []``).

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION (nagini directive 1) — VACUOUS here. Nagini's own
    docstring already records this class N/A (all inputs pass-by-value primitives,
    no read-only fractional-permission reference). Lean is additionally
    referentially transparent: ``d``/``p`` are immutable values, there is no
    half-permission to violate and no aliasing to exploit. No substitute is
    fabricated.

  * CONTROL-FLOW / DIVERGENCE — a KNOWN HOLE in the shippable sense (no case can
    be landed), but NOT for the reason "a non-terminating implementation cannot be
    written". It can: this bundle sets NO
    ``set_option loom.semantics.termination`` at all, and a ``partial def``
    helper in the impl region is an admissible same-spec variant
    (``variant_scope`` reports IN SCOPE for one, re-measured during this audit).
    Such a rival is genuinely WRONG and genuinely REJECTED — it returns one
    constant at every input, so it cannot equal a two-armed ``if`` — and it does
    fail every proof attempt (frozen tactic body, ``simp``, ``trivial``: exit 1
    each). What cannot be landed is a WITNESS for it, and the reason is
    mechanical rather than a proof difficulty: ``partial def`` compiles to an
    opaque constant with no equation lemma, so nothing in the shared vocabulary
    reduces ``implementation_floatformat d p``. The strongest form found refutes
    the CONJUNCTION of the obligation at two inputs the spec separates
    (``p = 0`` whole vs ``p = 1`` with ``decimalDigits d 1 = none``), since the
    rival must return the same value at both while the spec demands ``some`` and
    ``none``; that witness ELABORATES against the rival (exit 0) but its
    gold-side build fails with an *Application type mismatch* on
    ``Eq.trans (Eq.symm h0) h1`` — a unification failure on two DISTINCT
    ``implementation_floatformat`` applications, not a semantic refutation — and
    nine tactic variants were tried (``rw``/``simp_all``/``Option.noConfusion``/
    ``absurd``, both rewrite directions). A gold-side type error is not evidence
    the spec is satisfied there, so shipping it would be exactly the hollow case
    this battery's witness discipline exists to refuse. Recorded as a hole, not as
    a vacuous class. The velvet ``partial``-semantics spec hole
    (``the corpus-wide termination-semantics finding``) is scoped to velvet bundles and does not
    reach lean; it is cited, not re-reported. (The general-branch partiality the
    real filter exhibits is modeled honestly as ``decimalDigits d p = none`` — an
    ordinary ``Option`` value, not divergence.)

  * UNGROUNDED-ORACLE ECHO — the spec's arm bodies ARE opaque callees, but there
    is no single answer-key the result could echo without doing the branch
    selection: the two arms are DISTINCT terms and the selector is transparent, so
    an implementation must still pick the right arm and pass the right arguments.
    The honest analogue is the cheapest-correct POSITIVE CONTROL below.

  * PARTIAL-DOMAIN on the patch-changed boundary (nagini ``uniq-prepatch-guard``)
    — APPLIES, load-bearing. Reverting the selector to ``p < 0`` misroutes the
    boundary class {whole ∧ p == 0} into the general arm. Refuted by conditioning
    on the carrier at that boundary (see WITNESSES).

  * SELECTOR-CONJUNCT drop (nagini ``uniq-drop-fraczero``) — APPLIES. Dropping the
    ``decIsWhole d`` conjunct fires the plain-integer arm on non-whole values at
    ``p ≤ 0``.

  * ARM-SWAP / dropped separator (nagini ``uniq-drop-separator``) — APPLIES as
    ``weak-then-arm-both`` (return the then-arm rendering in BOTH branches, i.e.
    never use the general rendering).

WITNESSES — conditioning on the carrier. The arm bodies are opaque, so a witness
cannot COMPUTE the rendered string; it QUANTIFIES over the callee at a described
point instead (spec_guide "Conditioning on the carrier"). Each witness assumes
the WEAKEST separation its refutation needs — one hypothesis per opaque term,
never two about the same term (which the gate flags ``witness-inconsistent``) —
and was built BOTH ways with ``scripts/lean_verify.sh``: it ELABORATES against the
rival and FAILS against the frozen solution, so it discriminates rather than
asserting a tautology.

BINDER / CLAUSE COVERAGE. The two input binders of the selector are both varied
across the reject witnesses:
  * ``p`` — witnesses probe ``p = 0`` (prepatch boundary), ``p = -2`` (strictly
    negative, twice: drop-conjunct and then-arm place count), ``p = 1``
    (positive, arm-swap), ``p = 2`` (else-arm place count).
  * ``d`` — witnesses hold ``decIsWhole d`` at BOTH ``true`` (prepatch, then-arm
    argument, then-arm place count) and ``false`` (drop-conjunct, arm-swap,
    else-arm place count), so no rival that mishandled only one whole/non-whole
    class would slip through.
Every independent facet is attacked: the SELECTOR's ``p``-boundary by
``weak-prepatch-guard``, its ``decIsWhole`` conjunct by ``weak-drop-whole-
conjunct``, the arm SELECTION by ``weak-then-arm-both``, the THEN-arm's two
arguments by ``weak-const-intpart-arg`` (the digit source) and
``weak-then-arm-placecount`` (the fixed 0 place count), and the ELSE-arm
place-count argument by ``weak-wrong-placecount``. ``pts`` = 4 distinct input
points (p ∈ {0, -2, 1, 2}).

The place-count facets are genuinely independent and BOTH are needed: the then
arm's count is a constant 0 and the else arm's is ``p.natAbs``, so a rival that
swaps one leaves the other correct. The then-arm rival additionally AGREES with
the spec at p = 0, so it is refutable only strictly inside {whole ∧ p < 0} — no
witness stated at p = 0 discriminates it, which is why it carries its own at
p = -2.

WITNESS ROBUSTNESS. Every reject witness closes with a tactic whose failure
against the frozen solution is a SEMANTIC one: gold reduces the claim to
``⊢ False`` and no tactic closes it, which is exactly "gold satisfies the spec
here". Two witnesses originally ended with ``intro heq; exact hv
(Option.some.inj heq).symm``; on gold the goal reduces to ``¬True``, so
``heq : True`` and the build failed with an *Application type mismatch* rather
than an unsolved semantic goal. Same exit code, but a type error is not a
refutation-shaped failure, and it would have masked a genuine unfolding break.
Both now end in ``simp [hv.symm]`` and fail on gold with ``⊢ False``.

A later audit closed the same gap on the other three. ``weak-prepatch-guard``,
``weak-drop-whole-conjunct`` and ``weak-then-arm-both`` originally closed with a
bare ``simp [hw, hd, Id.run]``, which leaves the ``Id.run`` monadic residual
un-normalised: gold's goal stalled at ``⊢ ¬pure none = none`` /
``⊢ ¬pure X = X`` rather than reducing to ``⊢ False``. That is one ``simp``
lemma short of a refutation, and the FORGERY test says so — dropping the ``¬``
and rebuilding against gold produced the byte-identical ``unsolved goals ⊢ pure
none = none``, i.e. gold's exit code was the same whether the witness claimed
the spec was violated there or satisfied there, so it carried no information
about the claim. Adding ``pure, bind`` to the rewrite set (and the ground
``decide`` facts the selector needs) fixes it: gold now reduces to ``⊢ False``
while the flipped claim is PROVED against gold (exit 0 with ``rfl``, and ``No
goals to be solved`` for the un-normalised variant), so the two directions now
give opposite exit codes and the gold-side failure tracks the claim. The three
other witnesses were already in the reduced form and were re-measured
unchanged. Independently confirmed non-vacuous the stronger way as well: each of
the six witnesses was built against all four of this battery's verifying impls
(the three positives + the admissibility case) and against a fifth
audit-authored correct reshape (a ``match``-on-selector impl), 30 builds, and
FAILED every one — so no witness holds of any impl that satisfies this spec.

AXIOM lane: EMPTY (``AXIOM_TESTS = []``). The four callees are unchanged
sub-computations carried as ``opaque`` signatures with NO consumed ``_prop``
axiom (mapping.md: the proof case-splits on the selector and both arms use the
same callees in spec and impl, so the callees cancel). There is no in-model axiom
for the PBT axiom lane to re-discharge; nagini's A-reference probes are G-AX's
responsibility, not this gate's.
"""
from pathlib import Path

INSTANCE = "django__django-16485"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body, verbatim, so an impl replacement lands entirely
# inside the impl region.
_IMPL_GOLD = (
    "def implementation_floatformat (d : DecVal) (p : Int) : Option String := Id.run do\n"
    "  if decIsWhole d && decide (p ≤ 0) then\n"
    "    return some (numberFormat (toString (decIntPart d)) 0)\n"
    "  return (decimalDigits d p).map (fun s => numberFormat s p.natAbs)"
)

# Head of the frozen proof body (inside proof-start/proof-end): a legitimate
# ground-instance `have` is spliced in front of it for the admissibility case.
_PROOF_HEAD = (
    "  intro d p\n"
    "  unfold problem_spec_floatformat implementation_floatformat\n"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_HEAD) == 1, "proof region drifted; update _PROOF_HEAD"


def _impl(body):
    """Full Solution.lean variant with a replaced impl body (spec + theorem
    STATEMENT + frozen proof body untouched)."""
    return _swap(_BASE, _IMPL_GOLD, body)


# The frozen proof body IN FULL (inside proof-start/proof-end). A positive whose
# reshape is not definitionally equal to the frozen impl needs its own tactic
# body; only the proof REGION changes, so the theorem STATEMENT stays
# byte-identical and `same_spec` still holds.
_PROOF_GOLD = (
    "  intro d p\n"
    "  unfold problem_spec_floatformat implementation_floatformat\n"
    "  by_cases h : decIsWhole d && decide (p ≤ 0) <;>\n"
    "    simp only [h, Id.run, bind] <;> rfl\n"
)

assert _BASE.count(_PROOF_GOLD) == 1, "proof region drifted; update _PROOF_GOLD"


def _impl_proof(body, proof):
    """Variant replacing BOTH the impl body and the frozen tactic body."""
    return _swap(_swap(_BASE, _IMPL_GOLD, body), _PROOF_GOLD, proof)


# ---------------------------------------------------------------------------
# Rival impl bodies (each a full impl region; only the impl changes, so the
# spec and the theorem STATEMENT stay byte-identical). The frozen proof body is
# tuned to the frozen impl's form; it does NOT close for any of these reshaped
# impls, which is why every rejection is corroborated by a discriminating
# witness rather than by tactic breakage alone.
# ---------------------------------------------------------------------------

# POSITIVE — let-hoisted selector: bind the branch predicate to a local `bare`
# and branch on it. The `Id.run do` term is definitionally equal to the frozen
# impl, so the frozen proof closes unchanged (no new lemma/axiom/token).
_POS_LET = (
    "def implementation_floatformat (d : DecVal) (p : Int) : Option String := Id.run do\n"
    "  let bare := decIsWhole d && decide (p ≤ 0)\n"
    "  if bare then\n"
    "    return some (numberFormat (toString (decIntPart d)) 0)\n"
    "  return (decimalDigits d p).map (fun s => numberFormat s p.natAbs)"
)

# POSITIVE — branch reorder: guard on the De-Morgan complement `!(...)` and put
# the general arm in the `if`, the plain-integer arm in the fall-through. Same
# values; definitionally equal, so the frozen proof closes unchanged.
_POS_REORDER = (
    "def implementation_floatformat (d : DecVal) (p : Int) : Option String := Id.run do\n"
    "  if !(decIsWhole d && decide (p ≤ 0)) then\n"
    "    return (decimalDigits d p).map (fun s => numberFormat s p.natAbs)\n"
    "  return some (numberFormat (toString (decIntPart d)) 0)"
)

# REJECT — PREPATCH boundary: revert the selector to `p < 0`. On {whole ∧ p == 0}
# this now fires the general (else) arm instead of the plain-integer arm.
_PREPATCH = (
    "def implementation_floatformat (d : DecVal) (p : Int) : Option String := Id.run do\n"
    "  if decIsWhole d && decide (p < 0) then\n"
    "    return some (numberFormat (toString (decIntPart d)) 0)\n"
    "  return (decimalDigits d p).map (fun s => numberFormat s p.natAbs)"
)

# REJECT — drop the `decIsWhole d` conjunct: selector becomes `decide (p ≤ 0)`,
# so a NON-whole value at p ≤ 0 wrongly takes the plain-integer arm.
_DROP_WHOLE = (
    "def implementation_floatformat (d : DecVal) (p : Int) : Option String := Id.run do\n"
    "  if decide (p ≤ 0) then\n"
    "    return some (numberFormat (toString (decIntPart d)) 0)\n"
    "  return (decimalDigits d p).map (fun s => numberFormat s p.natAbs)"
)

# REJECT — arm-swap / never use the general rendering: return the plain-integer
# arm in BOTH branches (drops the general-rendering arm, the "separator" path).
_THEN_BOTH = (
    "def implementation_floatformat (d : DecVal) (p : Int) : Option String := Id.run do\n"
    "  if decIsWhole d && decide (p ≤ 0) then\n"
    "    return some (numberFormat (toString (decIntPart d)) 0)\n"
    "  return some (numberFormat (toString (decIntPart d)) 0)"
)

# REJECT — constant then-arm argument: feed the fixed string "0" to the
# plain-integer rendering instead of `toString (decIntPart d)`.
_CONST_INTPART = (
    "def implementation_floatformat (d : DecVal) (p : Int) : Option String := Id.run do\n"
    "  if decIsWhole d && decide (p ≤ 0) then\n"
    "    return some (numberFormat \"0\" 0)\n"
    "  return (decimalDigits d p).map (fun s => numberFormat s p.natAbs)"
)

# REJECT — wrong THEN-arm place count: format the plain-integer rendering at
# `p.natAbs` places instead of the fixed 0. Found by the audit: no ported case
# attacked the then-arm's SECOND argument (the fixed `0`), only its first
# (`decIntPart d`, `weak-const-intpart-arg`). The two arms' place-count arguments
# are independent facets — the else arm's is `p.natAbs`, the then arm's is
# the constant 0 — and swapping the then arm's for `p.natAbs` diverges on every
# {whole ∧ p < 0} input while agreeing at p = 0 (where `natAbs 0 = 0`), so it is
# a strictly-off-boundary near-miss the pre-existing witnesses all miss.
_THEN_PLACECOUNT = (
    "def implementation_floatformat (d : DecVal) (p : Int) : Option String := Id.run do\n"
    "  if decIsWhole d && decide (p ≤ 0) then\n"
    "    return some (numberFormat (toString (decIntPart d)) p.natAbs)\n"
    "  return (decimalDigits d p).map (fun s => numberFormat s p.natAbs)"
)

# POSITIVE — commuted selector conjunction: `decide (p ≤ 0) && decIsWhole d`.
# Bool `&&` is NOT commutative by `rfl`, so unlike the two ported positives this
# reshape is NOT closed by the frozen tactic body verbatim — it needs
# `Bool.and_comm` first. Added by the audit: it is the cheapest positive whose
# proof does real work, so a spec that only tolerated definitionally-equal
# reshapes would be caught here.
_POS_COMMUTED = (
    "def implementation_floatformat (d : DecVal) (p : Int) : Option String := Id.run do\n"
    "  if decide (p ≤ 0) && decIsWhole d then\n"
    "    return some (numberFormat (toString (decIntPart d)) 0)\n"
    "  return (decimalDigits d p).map (fun s => numberFormat s p.natAbs)"
)
_POS_COMMUTED_PROOF = (
    "  intro d p\n"
    "  unfold problem_spec_floatformat implementation_floatformat\n"
    "  by_cases h : decIsWhole d && decide (p ≤ 0) <;>\n"
    "    simp only [Bool.and_comm (decide (p ≤ 0)) (decIsWhole d), h, Id.run,\n"
    "      bind] <;> rfl\n"
)

# REJECT — wrong else-arm place count: format the general digits at 0 places
# instead of `p.natAbs` places.
_WRONG_PLACECOUNT = (
    "def implementation_floatformat (d : DecVal) (p : Int) : Option String := Id.run do\n"
    "  if decIsWhole d && decide (p ≤ 0) then\n"
    "    return some (numberFormat (toString (decIntPart d)) 0)\n"
    "  return (decimalDigits d p).map (fun s => numberFormat s 0)"
)


# ---------------------------------------------------------------------------
# Admissibility: discharge the obligation ALSO at the F2P-shaped ground class
# {decIsWhole d = true, p = 0} (the floatformat("0.00", 0) instance the sole F2P
# exercises) as a `have` in front of the frozen tactic body. Conditioned on the
# carrier (`d` is opaque): assume `decIsWhole d = true` and show the spec holds
# for the plain-integer outcome at p = 0. Then the frozen obligation is closed
# verbatim. Theorem STATEMENT byte-identical; no new declaration/axiom/token.
# ---------------------------------------------------------------------------
_ADM_GROUND = (
    "  have _adm : ∀ (d : DecVal), decIsWhole d = true →\n"
    "      problem_spec_floatformat d 0\n"
    "        (some (numberFormat (toString (decIntPart d)) 0)) := by\n"
    "    intro d hw\n"
    "    have hle : decide ((0:Int) ≤ 0) = true := by decide\n"
    "    unfold problem_spec_floatformat\n"
    "    simp only [hw, hle, Bool.true_and, ite_true]\n"
    + _PROOF_HEAD
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different CORRECT impls that
    # MUST verify (else SPEC-TOO-STRONG). The first two port nagini
    # `pos-bare-local` (let-hoist) and `pos-branch-reorder` (guard complement);
    # both are definitionally equal to the frozen impl, so the frozen proof closes
    # unchanged — which also means they exercise no REASONING. The third
    # (`pos-commuted-selector`, added by the audit) is not definitionally equal
    # and needs its own tactic body, so it is the one that would catch a spec
    # tolerant only of `rfl`-equal reshapes.
    # =====================================================================
    {
        "id": "pos-let-hoisted-selector",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_LET),
        "rationale": (
            "local-variable reshape: hoist the branch selector into a local "
            "`bare := decIsWhole d && decide (p ≤ 0)` and branch on it. Identical "
            "control flow + arm bodies; the honest cheapest impl that does the "
            "work (the two arms are distinct opaque renderings, so there is no "
            "single answer-key to echo). The `Id.run do` term is definitionally "
            "equal to the frozen impl, so the frozen proof (case-split + `rfl`) "
            "closes with the theorem STATEMENT byte-identical and no new "
            "lemma/axiom/assumption token. If a faithful correct reshape could "
            "not verify => SPEC-TOO-STRONG. Ports nagini `pos-bare-local`."
        ),
    },
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": (
            "invert the selector so the general-rendering arm is the `if` "
            "(predicate `!(decIsWhole d && decide (p ≤ 0))`) and the plain-integer "
            "arm is the fall-through. The two arms are mutually exclusive + "
            "exhaustive, so this returns identical values; definitionally equal to "
            "the frozen impl, so the frozen proof closes unchanged. If a faithful "
            "correct reordering could not verify => SPEC-TOO-STRONG. Ports nagini "
            "`pos-branch-reorder`."
        ),
    },
    {
        "id": "pos-commuted-selector",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(_POS_COMMUTED, _POS_COMMUTED_PROOF),
        "rationale": (
            "commute the selector's conjunction to `decide (p ≤ 0) && decIsWhole "
            "d`. Bool `&&` evaluates left-to-right, so this is NOT definitionally "
            "equal to the frozen impl — unlike the two reshapes above, the frozen "
            "tactic body does NOT close it; the variant supplies its own body "
            "(`Bool.and_comm` then the frozen case-split), inside the proof REGION, "
            "with the theorem STATEMENT byte-identical and no new "
            "declaration/axiom/`sorry`. Added by the audit: the ported positives "
            "are both definitionally equal to the frozen impl, so they exercise no "
            "reasoning; this one is the cheapest faithful correct reshape whose "
            "proof does real work. If it could not verify => SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is discharged ALSO at the F2P-shaped ground
    # class {whole value, p == 0} inside the proof region, confirming the modeled
    # behavior is SATISFIABLE at exactly the input the F2P exercises rather than
    # only provable in the abstract. The frozen theorem carries no precondition
    # hypothesis (behavior is total), so nagini's precondition-admission probe
    # (`admiss-f2p-zero`) has no binder to attack; discharging the F2P ground
    # class (conditioned on the opaque `d` via `decIsWhole d = true`) is the
    # faithful analogue.
    # =====================================================================
    {
        "id": "admiss-f2p-whole-zero",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_HEAD, _ADM_GROUND),
        "rationale": (
            "the obligation is discharged at the F2P-shaped ground class "
            "{decIsWhole d = true, p = 0} — the exact floatformat(\"0.00\", 0) "
            "instance the sole F2P test asserts is fixed (renders as the plain "
            "integer, not the general path). As a `have` in front of the frozen "
            "obligation it shows the spec holds for the plain-integer outcome "
            "there (selector fires: whole AND 0 ≤ 0), then closes the frozen "
            "obligation verbatim. Verifies (else the spec would be unsatisfiable "
            "at exactly the F2P input — the analogue of PRECOND-TOO-STRONG). "
            "Nothing is assumed: theorem STATEMENT byte-identical, no new "
            "declaration/axiom/`sorry`. Ports nagini `admiss-f2p-zero`."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected. Each carries (a) the refinement argument that its faithful
    # real patch would NOT resolve the F2P/P2P, and (b) a carrier-conditioned
    # refutation witness (built both ways: elaborates on the rival, fails on gold).
    # =====================================================================
    {
        "id": "weak-prepatch-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PREPATCH),
        "refinement": (
            "this IS the pre-patch behaviour the instance flags: the real guard "
            "routes the boundary class {whole value ∧ place count == 0} into the "
            "precision-computing general path. For floatformat(\"0.00\", 0) that "
            "path computes a precision of 0 and raises `ValueError: valid range "
            "for prec is [1, MAX_PREC]` — the exact crash the issue reports and "
            "the sole F2P (test_zero_values: floatformat(\"0.00\", 0) == \"0\", "
            "floatformat(Decimal(\"0.00\"), 0) == \"0\") asserts is fixed. The "
            "faithful real patch (the unchanged strict-less-than guard) does NOT "
            "resolve the F2P. Ports nagini `uniq-prepatch-guard`."
        ),
        "rationale": (
            "REJECT from the SELECTOR's `p`-boundary: on the boundary class "
            "{decIsWhole d = true, p = 0} the frozen selector fires the plain-"
            "integer arm, but with `p < 0` the rival fires the general arm "
            "instead. Refuted at p = 0 with the value whole — the single class "
            "the boundary token `<` vs `≤` moves."
        ),
        "witness": (
            "-- Boundary class {whole value, p = 0}: the frozen spec selects the\n"
            "-- plain-integer arm, but a `p < 0` guard fires the general arm. Where\n"
            "-- the general digit computation rejects its inputs (`decimalDigits d 0\n"
            "-- = none`) the rival yields `none`, contradicting the spec. Two\n"
            "-- hypotheses about DISTINCT opaque terms (`decIsWhole d`,\n"
            "-- `decimalDigits d 0`), jointly satisfiable.\n"
            "-- The `pure, bind` rewrites are load-bearing, not cosmetic: without\n"
            "-- them the `Id.run` residual survives and gold's goal stalls at\n"
            "-- `¬pure X = X` instead of reducing to `False` (see WITNESS\n"
            "-- ROBUSTNESS above for the forgery measurement that forced them).\n"
            "example (d : DecVal) (hw : decIsWhole d = true)\n"
            "    (hd : decimalDigits d 0 = none) :\n"
            "    ¬ problem_spec_floatformat d 0 (implementation_floatformat d 0) := by\n"
            "  unfold problem_spec_floatformat implementation_floatformat\n"
            "  have hle : decide ((0:Int) ≤ 0) = true := by decide\n"
            "  have hlt : decide ((0:Int) < 0) = false := by decide\n"
            "  simp only [hw, hle, hlt, Bool.true_and, Bool.and_false, Id.run, pure,\n"
            "    bind, ite_true, if_false, Bool.false_eq_true, hd, Option.map_none]\n"
            "  simp\n"
        ),
    },
    {
        "id": "weak-drop-whole-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_WHOLE),
        "refinement": (
            "dropping the whole-value conjunct routes a NON-whole value at a "
            "non-positive place count into the plain-integer early return. The "
            "P2P suite asserts floatformat(6.200000, -3) == \"6.200\", "
            "floatformat(13.1031, -3) == \"13.103\", floatformat(11.1197, -2) == "
            "\"11.12\" — all non-whole values at negative place counts that MUST "
            "keep their fractional digits. A faithful patch with the conjunct "
            "dropped would render them as the bare integers \"6\", \"13\", \"11\", "
            "failing those P2P assertions; it does NOT resolve. Ports nagini "
            "`uniq-drop-fraczero`."
        ),
        "rationale": (
            "REJECT from the SELECTOR's `decIsWhole d` conjunct: on "
            "{decIsWhole d = false, p = -2} the frozen selector fires the general "
            "arm, but the rival (guard `decide (p ≤ 0)` only) fires the plain-"
            "integer arm. The general arm's `none`-propagation is the "
            "discriminator: where `decimalDigits d (-2) = none` the spec demands "
            "`none` but the rival returns `some (...)`."
        ),
        "witness": (
            "-- Non-whole value at p = -2: the frozen spec selects the general\n"
            "-- arm; dropping the whole conjunct fires the plain-integer arm. Where\n"
            "-- the general digit computation rejects (`decimalDigits d (-2) =\n"
            "-- none`) the spec's result is `none` but the rival returns `some`.\n"
            "-- Two hypotheses on DISTINCT opaque terms, jointly satisfiable.\n"
            "-- `pure, bind` are load-bearing: they normalize the `Id.run` residual\n"
            "-- so gold's goal reduces to `False` rather than stalling at\n"
            "-- `¬pure none = none` (see WITNESS ROBUSTNESS above).\n"
            "example (d : DecVal) (hw : decIsWhole d = false)\n"
            "    (hd : decimalDigits d (-2) = none) :\n"
            "    ¬ problem_spec_floatformat d (-2) (implementation_floatformat d (-2)) := by\n"
            "  unfold problem_spec_floatformat implementation_floatformat\n"
            "  have hle : decide ((-2:Int) ≤ 0) = true := by decide\n"
            "  simp only [hw, hle, Bool.false_and, Id.run, pure, bind, ite_true,\n"
            "    Bool.false_eq_true, if_false, hd, Option.map_none]\n"
            "  simp\n"
        ),
    },
    {
        "id": "weak-then-arm-both",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_THEN_BOTH),
        "refinement": (
            "returning the plain-integer rendering in BOTH branches never uses the "
            "general rendering — i.e. a patch that emitted the whole part alone "
            "even for values with a fractional part or a positive place count. The "
            "P2P suite asserts floatformat(7.7, 3) == \"7.700\", "
            "floatformat(5555.555, 2) == \"5555.56\", floatformat(0.7) == \"0.7\"; "
            "the F2P/P2P also asserts floatformat(0, 6) == \"0.000000\". Emitting "
            "only the whole part yields \"7\"/\"5555\"/\"0\"/\"0\", failing those "
            "assertions; it does NOT resolve. Ports nagini `uniq-drop-separator` "
            "(the general-rendering arm is the separator-bearing path)."
        ),
        "rationale": (
            "REJECT from the arm SELECTION: on {decIsWhole d = false, p = 1} the "
            "frozen spec selects the general arm "
            "`(decimalDigits d 1).map (numberFormat · 1)`, but the rival returns "
            "the plain-integer arm `some (numberFormat (toString (decIntPart d)) "
            "0)`. Where `decimalDigits d 1 = none` the spec demands `none` while "
            "the rival returns `some`."
        ),
        "witness": (
            "-- Non-whole value with a positive place count (p = 1): the frozen\n"
            "-- spec selects the general arm; returning the plain-integer arm in\n"
            "-- both branches yields `some` where the general computation rejects\n"
            "-- (`decimalDigits d 1 = none` => spec result `none`). Two hypotheses\n"
            "-- on DISTINCT opaque terms, jointly satisfiable.\n"
            "-- `pure, bind` are load-bearing: they normalize the `Id.run` residual\n"
            "-- so gold's goal reduces to `False` rather than stalling at\n"
            "-- `¬pure none = none` (see WITNESS ROBUSTNESS above).\n"
            "example (d : DecVal) (hw : decIsWhole d = false)\n"
            "    (hd : decimalDigits d 1 = none) :\n"
            "    ¬ problem_spec_floatformat d 1 (implementation_floatformat d 1) := by\n"
            "  unfold problem_spec_floatformat implementation_floatformat\n"
            "  simp only [hw, Bool.false_and, Id.run, pure, bind,\n"
            "    Bool.false_eq_true, if_false, hd, Option.map_none]\n"
            "  simp\n"
        ),
    },
    {
        "id": "weak-const-intpart-arg",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_CONST_INTPART),
        "refinement": (
            "feeding the fixed string \"0\" to the plain-integer rendering instead "
            "of the value's whole part corresponds to a patch whose integer early "
            "return emitted a constant \"0\" regardless of the value. The P2P "
            "suite asserts floatformat(11.0000, -2) == \"11\", "
            "floatformat(Decimal(\"09.000\")) == \"9\", and "
            "floatformat(-1.323297138040798e35, -2) == "
            "\"-132329713804079800000000000000000000\"; a constant \"0\" fails "
            "every non-zero whole case, so it does NOT resolve. Ports the "
            "ARGUMENT-level shadow of nagini `uniq-const-zero-bare` (nagini pins "
            "the digit sequence directly; here the digits are `numberFormat`'s "
            "opaque output, so the refutable target is its ARGUMENT `decIntPart "
            "d` vs the constant \"0\")."
        ),
        "rationale": (
            "REJECT from the THEN-arm ARGUMENT: on {decIsWhole d = true, p = 0} "
            "both spec and rival fire the plain-integer arm, but the spec formats "
            "`toString (decIntPart d)` while the rival formats the constant \"0\". "
            "Where these two renderings differ (`numberFormat (toString "
            "(decIntPart d)) 0 ≠ numberFormat \"0\" 0`) the outputs differ. One "
            "hypothesis on the selector term, one separating the two renderings — "
            "distinct terms, jointly satisfiable."
        ),
        "witness": (
            "-- Whole value at p = 0: both fire the plain-integer arm, but the spec\n"
            "-- formats the value's whole part while a constant-\"0\" rival formats\n"
            "-- \"0\". At any value whose rendering differs from that of \"0\" the\n"
            "-- outputs differ. `hw` describes the selector; `hv` separates the two\n"
            "-- opaque renderings (distinct terms), jointly satisfiable.\n"
            "example (d : DecVal) (hw : decIsWhole d = true)\n"
            "    (hv : numberFormat (toString (decIntPart d)) 0 ≠ numberFormat \"0\" 0) :\n"
            "    ¬ problem_spec_floatformat d 0 (implementation_floatformat d 0) := by\n"
            "  unfold problem_spec_floatformat implementation_floatformat\n"
            "  have hle : decide ((0:Int) ≤ 0) = true := by decide\n"
            "  simp only [hw, hle, Bool.true_and, Id.run, ite_true, pure, bind]\n"
            "  simp [hv.symm]\n"
        ),
    },
    {
        "id": "weak-then-arm-placecount",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_THEN_PLACECOUNT),
        "refinement": (
            "the plain-integer rendering is fed a FIXED zero place count; feeding "
            "it |p| instead corresponds to a patch that reused the general path's "
            "precision for the integer early return. The P2P suite asserts "
            "floatformat(11.0000, -2) == \"11\" and "
            "floatformat(-1.323297138040798e35, -2) == "
            "\"-132329713804079800000000000000000000\" — whole values at a negative "
            "place count whose rendering carries NO fractional field. Formatting "
            "them at |p| = 2 places instead of 0 appends one, so it does NOT "
            "resolve. Added by the audit: no ported case attacked this argument."
        ),
        "rationale": (
            "REJECT from the THEN-arm's PLACE-COUNT argument — the facet the other "
            "cases leave unattacked (`weak-const-intpart-arg` attacks the then "
            "arm's FIRST argument, `weak-wrong-placecount` the ELSE arm's second). "
            "On {decIsWhole d = true, p = -2} both spec and rival fire the "
            "plain-integer arm, but the spec formats at the fixed 0 places while "
            "the rival formats at `p.natAbs = 2`. Note the rival AGREES with the "
            "spec at p = 0 (`natAbs 0 = 0`), so it is refutable only strictly "
            "inside the negative-p sub-domain — which is why p = -2 is the "
            "witness point and why no existing witness catches it."
        ),
        "witness": (
            "-- Whole value at p = -2: both fire the plain-integer arm, but the\n"
            "-- spec formats at the fixed 0 places while the rival formats at\n"
            "-- |p| = 2. At any whole part whose 0-place and 2-place renderings\n"
            "-- differ, the outputs differ. `hw` describes the selector; `hv`\n"
            "-- separates the two place-count formattings of the SAME digit string\n"
            "-- (distinct terms), jointly satisfiable.\n"
            "example (d : DecVal) (hw : decIsWhole d = true)\n"
            "    (hv : numberFormat (toString (decIntPart d)) 0\n"
            "            ≠ numberFormat (toString (decIntPart d)) 2) :\n"
            "    ¬ problem_spec_floatformat d (-2) (implementation_floatformat d (-2)) := by\n"
            "  unfold problem_spec_floatformat implementation_floatformat\n"
            "  have hle : decide ((-2:Int) ≤ 0) = true := by decide\n"
            "  have hn : ((-2:Int)).natAbs = 2 := by decide\n"
            "  simp only [hw, hle, Bool.true_and, Id.run, ite_true, pure, bind, hn]\n"
            "  simp [hv.symm]\n"
        ),
    },
    {
        "id": "weak-wrong-placecount",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WRONG_PLACECOUNT),
        "refinement": (
            "formatting the general digits at 0 places instead of |p| places "
            "corresponds to a patch that fed the wrong precision to the final "
            "formatting step for the general path. The P2P suite asserts "
            "floatformat(7.7, 3) == \"7.700\" and floatformat(5555.555, 2) == "
            "\"5555.56\"; the F2P method additionally asserts "
            "floatformat(0, 6) == \"0.000000\" — the trailing "
            "fractional field width is exactly the place count. Formatting at 0 "
            "places drops that field, failing those assertions; it does NOT "
            "resolve. Ports the ARGUMENT-level shadow of nagini "
            "`uniq-wrong-frac-fill` (the fractional field width, not its fill "
            "character, is what is transparent on this carrier)."
        ),
        "rationale": (
            "REJECT from the ELSE-arm ARGUMENT: on {decIsWhole d = false, p = 2} "
            "both fire the general arm, but the spec formats at `p.natAbs = 2` "
            "places while the rival formats at 0. Where these differ for the "
            "produced digit string (`numberFormat \"x\" 2 ≠ numberFormat \"x\" 0`) "
            "the outputs differ. `hd` fixes the produced digits, `hv` separates "
            "the two place counts — distinct terms, jointly satisfiable."
        ),
        "witness": (
            "-- Non-whole value at p = 2: both fire the general arm, but the spec\n"
            "-- formats the produced digits at 2 places while the rival uses 0. At\n"
            "-- any produced string whose 2-place and 0-place formattings differ,\n"
            "-- the outputs differ. `hd` fixes the produced digit string; `hv`\n"
            "-- separates the two place-count formattings (distinct terms).\n"
            "example (d : DecVal) (hw : decIsWhole d = false)\n"
            "    (hd : decimalDigits d 2 = some \"x\")\n"
            "    (hv : numberFormat \"x\" 2 ≠ numberFormat \"x\" 0) :\n"
            "    ¬ problem_spec_floatformat d 2 (implementation_floatformat d 2) := by\n"
            "  unfold problem_spec_floatformat implementation_floatformat\n"
            "  have hn : ((2:Int)).natAbs = 2 := by decide\n"
            "  simp only [hw, hd, Bool.false_and, Id.run, Bool.false_eq_true, if_false,\n"
            "    Option.map_some, pure, bind, hn]\n"
            "  simp [hv.symm]\n"
        ),
    },
]


# No consumed axioms and no deep-model references for THIS gate: the four callees
# are unchanged sub-computations carried as `opaque` signatures with no `_prop`
# axiom the proof consumes (mapping.md: the case-split cancels them). The nagini
# A-reference soundness/containment probes are G-AX's responsibility, not this
# gate's, so the axiom lane is empty here.
AXIOM_TESTS = []
