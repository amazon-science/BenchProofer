"""properties.py — G-PBT falsification battery for django__django-11119 (lean),
PORTED from the nagini sibling. NOT a Lean source file: a record of adversarial
cases the G-PBT gate executes. Each SPEC_TESTS case is a full ``Solution.lean``
variant that shares the FROZEN spec byte-for-byte (region surgery: only text
inside ``-- impl-start``/``-- impl-end``, or inside the ``-- proof-start``/
``-- proof-end`` tactic body, is changed — both regions the consumer spec view
elides, so ``markers.same_spec`` holds by construction and the ``theorem
correct_renderToString`` STATEMENT survives byte-identically). ``expect:"verify"``
passes iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND
does NOT verify AND its refutation ``witness`` discriminates: elaborates against
the rival, FAILS against the frozen solution).

===========================================================================
DEFENDED SURFACE ON THIS CARRIER (Solution.lean + mapping.md)
===========================================================================
ONE modeled function and ONE obligation:

    problem_spec_renderToString
        (renderValue : Bool → String → String)
        (engineAutoescape suppliedIsContext suppliedCtxAutoescape : Bool)
        (leading value trailing : String) (result : String) : Prop :=
      let eff := if suppliedIsContext then suppliedCtxAutoescape
                 else engineAutoescape
      result = leading ++ renderValue eff value ++ trailing

    theorem correct_renderToString : ∀ (all seven inputs), problem_spec … (impl …)

There is NO precondition: the obligation is universally quantified over all
seven inputs with no hypothesis arrow.

The single postcondition equation carries two independently attackable parts:

  (S) FLAG SELECTION — the escaping flag that reaches the value-rendering step
      is ``eff``: the supplied rendering context's OWN flag when a ready-made
      context is given, and the engine's configured flag when plain data is
      given. This is the DISCRIMINATING part, the whole subject of the change:
      the pre-change behavior built the rendering context for plain data without
      threading the engine's configured flag, so the hard-wired escaping default
      was used and an engine configured with escaping OFF was ignored.
      ``Solution_prepatch.lean`` reproduces exactly that (the plain-data arm
      assigns the literal ``true``) and fails this part (G-DIFF). The sole F2P
      witness is precisely that input: escaping configured OFF, plain data, a
      value containing markup, required verbatim.
  (F) OUTPUT FRAME — the output is ``leading ++ <rendered value> ++ trailing``:
      the leading literal text, then the value-rendering step applied to the
      selected flag AND TO THE VALUE, then the trailing literal text. No output
      component is free. This is the referentially-transparent analogue of the
      frame obligation (SPEC_GUIDE §0.5): both literals and the argument handed
      to the rendering step are pinned to their inputs.

GROUNDEDNESS. ``renderValue`` is a universally-quantified FUNCTION PARAMETER,
not an ``opaque`` callee and not an answer-key oracle: the equation must hold for
EVERY value-renderer, so nothing can be echoed and the whole carrier is
TRANSPARENT. Every refutation below is therefore stated at concrete literals
(including a concrete instantiation of ``renderValue``) and closed by ``decide``
— no conditioning on an opaque term is needed anywhere, and consequently no
witness binds a hypothesis, so no joint-satisfiability question arises.

===========================================================================
PORT ACCOUNTING — nagini case -> here
===========================================================================
  nagini case                     -> here                          disposition
  -------------------------------------------------------------------------
  pos-control-reordered           -> pos-branch-reorder            RE-AIMED
  pos-control-seg-local           -> pos-render-local              PORTED
  echo-attempt-honest             -> pos-select-expression         RE-EXPRESSED
  admiss-f2p-witness              -> admiss-total-domain           RE-AIMED
  frame-mutate-value              -> (none)                        VACUOUS
  rival-force-escape-true         -> uniq-hardwire-default-flag     PORTED
  rival-invert-policy             -> uniq-swap-flag-arms            RE-AIMED
  partial-domain-verbatim-first   -> uniq-frame-drop-leading /      RE-AIMED
                                     uniq-frame-drop-trailing
  rival-drop-quot                 -> (none)                        NO CARRIER
  (no sibling)                    -> pos-early-return               ADDED
  (no sibling)                    -> pos-boolean-select             ADDED
  (no sibling)                    -> uniq-drop-flag-guard           ADDED
  (no sibling)                    -> uniq-render-wrong-argument     ADDED
  AXIOM_TESTS (3)                 -> (none)                        DROPPED (G-AX)

CARRIER NARROWING, in detail — the nagini sibling models
``render_value(value: List[int], engine_autoescape: bool)``: it models the
DOWNSTREAM per-code-point escaper deeply (a backward fold with an entity table)
and takes the flag as a plain boolean. The lean bundle models the OPPOSITE half
of the same behavior: the value-rendering step is abstracted to an arbitrary
``renderValue`` parameter, and what is modeled instead is HOW the escaping flag
is SELECTED (the ready-made-context arm vs the plain-data arm) and how the
literal text frames the rendered value. So:

  * every nagini case whose subject is the ESCAPER's per-code-point behavior has
    NO counterpart here, because the escaper is not modeled — it is universally
    quantified away. ``rival-drop-quot`` (drop the double-quote entity in the
    escape branch) is exactly that case and is OMITTED as inexpressible: on this
    carrier the escaper is a parameter, so "a wrong per-character map" is not a
    writable impl edit and no witness could discriminate it. The nagini escaper
    surface is defended in this backend family by the velvet sibling's E1
    obligation, not here.
  * conversely this carrier exposes the flag SELECTION as two arms plus a literal
    FRAME, none of which nagini's single-boolean surface could attack. Hence the
    ADDED rivals (``uniq-drop-flag-guard`` on the caller-shape guard,
    ``uniq-render-wrong-argument`` on the rendering step's argument) and the two
    frame rivals below: they are not fabricated wrongness, they are the parts of
    the modeled surface nagini had no binder for. The two ADDED positives
    (``pos-early-return``, ``pos-boolean-select``) exist for the same reason —
    they reshape the flag selection in ways nagini's carrier had no room for, and
    ``pos-boolean-select`` is the one shape measured NOT definitionally equal to
    the frozen impl, so it forces the obligation to be reproven.
  * nagini's ``partial-domain-verbatim-first`` (verbatim output correct except at
    index 0) is a partial-domain attack on the OUTPUT-SHAPE half of the contract.
    Its per-code-point mechanics are unavailable (the escaper is a parameter), so
    the class is RE-AIMED at the frame: a rival correct on every input whose
    trailing (resp. leading) literal is empty and wrong on all others. Same
    argument — pins only a sub-domain of the output equation — with mechanics
    this carrier can state.
  * FRAME/PERMISSION-MUTATION (``frame-mutate-value``): VACUOUS. The nagini rival
    writes through a read-only ``1/2``-permission reference and is rejected by the
    permission system. Lean is referentially transparent: every input is an
    immutable value, there is no heap, no aliasing and no permission system to
    subvert, so there is no read-only input to overwrite. No substitute
    fabricated. (The frame OBLIGATION is not vacuous and is attacked — see part
    (F) and the two ``uniq-frame-*`` rivals — but that is the §0.5 pinning
    obligation, not permission mutation.)
  * DIVERGENCE / NON-TERMINATION: the nagini sibling carries NO ``diverge-*`` /
    ``nonterm-*`` / ``weak-diverge`` case, so there is nothing to port and
    nothing is claimed dropped. Independently, on lean the class is genuinely
    vacuous rather than a hole: ``implementation_renderToString`` is a total Lean
    ``def``, so a diverging implementation cannot be written at all. (The
    termination-semantics spec hole recorded in ``the corpus-wide termination-semantics finding``
    is velvet-only; that document measures lean as unaffected. It is not
    re-derived here.)
  * nagini ``admiss-f2p-witness`` established the read-only fractional-permission
    precondition on an F2P-shaped input under both flag settings. The lean
    obligation has NO precondition at all (no hypothesis in the
    ``correct_renderToString`` binder), so PRECOND-TOO-STRONG is unreachable and
    the classic "a normal input is admitted" probe is vacuous. RE-AIMED at the
    total-carrier analogue: the obligation being SATISFIABLE at exactly an
    F2P-shaped input, and DISCRIMINATING there. ``admiss-total-domain`` states
    both as ``have``s closed by EVALUATION at that concrete point (the
    postcondition holds of the output the changed behavior produces, and fails of
    the output the pre-change behavior produces) before closing the frozen
    obligation verbatim. AUDIT NOTE: this case originally carried ``module =
    _BASE`` — the frozen file unchanged — which passed honestly while testing
    nothing beyond what the frozen bundle already proves. The evaluated ``have``s
    are what make the lane non-vacuous.
  * AXIOM_TESTS: DROPPED. The axiom lane is G-AX's job and this gate ignores
    ``AXIOM_TESTS`` regardless. This bundle additionally consumes no callee axiom
    (mapping.md: the downstream value-rendering step is a parameter, not an
    ``opaque`` + ``axiom`` pair, and ``axiom_check.py`` is a skip stub).

===========================================================================
WITNESS MECHANICS
===========================================================================
Every reject case carries a witness of the shape

    example : ¬ problem_spec_renderToString <7 concrete inputs>
        (implementation_renderToString <the same 7 inputs>) := by
      unfold problem_spec_renderToString implementation_renderToString
      decide

checked in a file whose ``proof`` region has been emptied, so no tactic script
can mask the verdict. It ELABORATES against the rival (the rival's output at that
point provably differs from the pinned right-hand side) and FAILS against the
frozen solution (``decide`` reports the proposition is false, since gold
satisfies the equation everywhere) — the two halves the gate requires. Each was
checked out of band with ``scripts/lean_verify.sh``: rival build exit 0, gold
build fails on ``decide``. No witness uses a banned token
(sorry/admit/native_decide/axiom/opaque) and none binds a hypothesis.

SPEC-TOO-STRONG PROBES BEYOND THIS BATTERY (audit, measured). Four further
CORRECT reshapes of the flag selection and the output frame were built against the
byte-identical obligation: a ``match`` on the caller-shape flag, ``cond``, the
guard written with reversed polarity, and the frame re-associated to the right —
all VERIFY. Two of them (the re-associated frame, and a selection built from
``xor``) are NOT closed by the frozen tactic body and needed their own proof of
the same statement (``simp [String.append_assoc]`` and an exhaustive three-flag
``cases … <;> rfl`` respectively); both then verify. So no faithful correct impl
was found that the frozen spec rejects, and the ``rfl``-sensitivity is a property
of the frozen TACTIC, not of the obligation.

BINDER / POINT COVERAGE (what the gate does NOT check). The six reject witnesses
probe SIX DISTINCT input points, each SEEN (audit) to elaborate against its own
rival and to FAIL against the frozen solution by a plain ``decide`` evaluation —
and, for the two near-misses on the plain-data arm, each seen to fail against the
OTHER near-miss's rival, so neither witness is a duplicate of the other. No input
binder is held at one value across them: ``renderValue`` takes four distinct
concrete renderers;
``engineAutoescape``, ``suppliedIsContext`` and ``suppliedCtxAutoescape`` each
take both ``true`` and ``false``; ``leading``, ``value`` and ``trailing`` each
take several distinct strings including the empty one. Part (S) is attacked on
BOTH arms (the plain-data arm by ``uniq-hardwire-default-flag`` and
``uniq-drop-flag-guard``, the ready-made-context arm by ``uniq-swap-flag-arms``);
part (F) is attacked on all three of its positions (leading literal, trailing
literal, and the value handed to the rendering step).

No leakage: behavior is described abstractly, as the frozen spec does; no
patched file, symbol or bug→fix mechanism is named.
"""
from pathlib import Path

INSTANCE = "django__django-11119"
BACKEND = "lean"
FLOAT_ENCODING = None

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors — each lies ENTIRELY inside the impl region (or, for _PROOF_BODY, the
# proof region) and is unique in the frozen file, so drift fails loudly at load.
# ---------------------------------------------------------------------------

# The whole flag-selection block: initialize from the supplied context's flag,
# then override with the engine's configured flag when plain data was given.
_SELECT = """  let mut autoescape := suppliedCtxAutoescape
  if !suppliedIsContext then
    autoescape := engineAutoescape"""
assert _BASE.count(_SELECT) == 1, "flag-selection block drifted"

# The plain-data arm alone (the assignment the pre-change behavior hard-wires).
_PLAIN_ARM = "    autoescape := engineAutoescape"
assert _BASE.count(_PLAIN_ARM) == 1, "plain-data arm drifted"

# The output-assembly return: leading literal, rendered value, trailing literal.
_RETURN = "  return leading ++ renderValue autoescape value ++ trailing"
assert _BASE.count(_RETURN) == 1, "output-assembly return drifted"

# The frozen tactic body. A positive whose impl is not definitionally equal to
# the frozen one replaces THIS (never the theorem statement).
_PROOF_BODY = """  intro renderValue engineAutoescape suppliedIsContext suppliedCtxAutoescape
        leading value trailing
  unfold problem_spec_renderToString implementation_renderToString
  cases suppliedIsContext <;> rfl"""
assert _BASE.count(_PROOF_BODY) == 1, "frozen proof body drifted"


# ---------------------------------------------------------------------------
# Witness builder. The carrier is fully transparent (`renderValue` is a
# universally-quantified parameter, instantiated here at a concrete renderer),
# so each refutation is stated at concrete literals and closed by `decide`.
# ---------------------------------------------------------------------------
def _witness(rv, eng, isctx, ctxflag, leading, value, trailing):
    args = f'{rv} {eng} {isctx} {ctxflag} "{leading}" "{value}" "{trailing}"'
    return (
        "example : ¬ problem_spec_renderToString " + args + "\n"
        "    (implementation_renderToString " + args + ") := by\n"
        "  unfold problem_spec_renderToString implementation_renderToString\n"
        "  decide\n"
    )


# `if the flag is on then bracket the value else emit it verbatim` — a renderer
# that distinguishes the two flag settings, which is what a flag-selection
# refutation needs.
_RV_BRACKET = '(fun b s => if b then "[" ++ s ++ "]" else s)'
# a second flag-sensitive renderer with a different shape
_RV_MARK = '(fun b s => if b then "E" else s)'
# flag-INSENSITIVE renderers: a frame refutation must not depend on the flag
_RV_ID = "(fun _ s => s)"
_RV_BANG = '(fun _ s => s ++ "!")'


# ===========================================================================
# POSITIVE CONTROLS (soundness / verify) — structurally different but CORRECT
# impls that MUST verify against the byte-identical obligation. A rejection here
# would mean the postcondition is over-fit to the frozen code form
# (SPEC-TOO-STRONG). Each was built with scripts/lean_verify.sh.
# ===========================================================================

# pos-branch-reorder: the SAME selection written with the arms exchanged —
# initialize from the engine's configured flag and override with the supplied
# context's own flag when a ready-made context was given. Behaviorally identical
# (the flag each caller shape gets is unchanged), different branch polarity and
# a different initializer. Ports the nagini pos-control-reordered onto the one
# branch this carrier has.
_POS_BRANCH_REORDER = _swap(_BASE, _SELECT, """  let mut autoescape := engineAutoescape
  if suppliedIsContext then
    autoescape := suppliedCtxAutoescape""")

# pos-select-expression: drop the mutable local entirely and select the flag with
# a single conditional expression. This is the honest CHEAPEST correct impl —
# the re-expression of the nagini echo-attempt-honest control. There is no
# answer-key to echo here (`renderValue` is universally quantified, so the
# right-hand side is a function OF the inputs for every renderer), and the
# cheapest impl that satisfies the equation is therefore one that really does
# select the flag correctly and assemble the frame correctly.
_POS_SELECT_EXPRESSION = _swap(
    _BASE, _SELECT,
    "  let autoescape :=\n"
    "    if suppliedIsContext then suppliedCtxAutoescape else engineAutoescape")

# pos-render-local: keep the frozen selection but bind the rendered value to a
# local before assembling the output frame. Same value flow, different control
# shape. Direct port of the nagini pos-control-seg-local (which bound the
# per-code-point bytes to a local before prepending).
_POS_RENDER_LOCAL = _swap(
    _BASE, _RETURN,
    "  let rendered := renderValue autoescape value\n"
    "  return leading ++ rendered ++ trailing")

# pos-early-return: replace the mutable flag and single exit with ONE EARLY
# RETURN PER CALLER SHAPE, each assembling the frame with the flag that shape
# supplies. A different `Id.run` control-flow shape (two exits, no mutable
# local); measured to still be closed by the frozen tactic body, so it is carried
# with the frozen proof unchanged.
_POS_EARLY_RETURN = _swap(
    _BASE, _SELECT + "\n" + _RETURN,
    "  if suppliedIsContext then\n"
    "    return leading ++ renderValue suppliedCtxAutoescape value ++ trailing\n"
    "  return leading ++ renderValue engineAutoescape value ++ trailing")

# pos-boolean-select: select the flag with a BOOLEAN COMBINATOR rather than a
# conditional — the disjunction of "a ready-made context was supplied and its own
# flag is set" and "plain data was supplied and the engine's configured flag is
# set". Equivalent for every input, but measured NOT definitionally equal to the
# frozen impl: the frozen tactic body fails on it (`rfl` reports the combinator
# is not definitionally the conditional), so this case carries its own proof of
# the BYTE-IDENTICAL theorem statement. That makes it the strongest soundness
# probe here — the obligation is RE-ESTABLISHED for a genuinely new impl shape
# rather than inherited from the frozen one.
_POS_BOOLEAN_SELECT = _swap(
    _swap(_BASE, _SELECT,
          "  let autoescape :=\n"
          "    (suppliedIsContext && suppliedCtxAutoescape)\n"
          "      || (!suppliedIsContext && engineAutoescape)"),
    _PROOF_BODY,
    """  intro renderValue engineAutoescape suppliedIsContext suppliedCtxAutoescape
        leading value trailing
  unfold problem_spec_renderToString implementation_renderToString
  cases suppliedIsContext <;> cases suppliedCtxAutoescape <;>
    cases engineAutoescape <;> rfl""")


# ===========================================================================
# ADMISSIBILITY (verify). The frozen obligation has NO precondition, so the
# classic "a normal input is admitted" probe is unavailable — but the analogue on
# a total carrier is that the obligation is SATISFIABLE at exactly an F2P-shaped
# input, and that the satisfying output there is the one the changed behavior
# produces rather than the pre-change one. Both are discharged BY EVALUATION as
# `have`s, at the concrete F2P-shaped point (escaping configured OFF, plain data,
# a value carrying markup), BEFORE the frozen obligation is closed verbatim. The
# second `have` is the part that is not vacuous: it evaluates the postcondition to
# FALSE at the pre-change output, so the obligation genuinely pins that point
# instead of being satisfiable by either output there.
_ADMISS_F2P = _swap(
    _BASE, _PROOF_BODY,
    '  have _satisfiable_at_f2p : problem_spec_renderToString\n'
    '      (fun b s => if b then "[" ++ s ++ "]" else s) false false false\n'
    '      "obj:" "s&t" ";" "obj:s&t;" := by\n'
    "    unfold problem_spec_renderToString\n"
    "    decide\n"
    '  have _unsatisfiable_at_prechange_output : ¬ problem_spec_renderToString\n'
    '      (fun b s => if b then "[" ++ s ++ "]" else s) false false false\n'
    '      "obj:" "s&t" ";" "obj:[s&t];" := by\n'
    "    unfold problem_spec_renderToString\n"
    "    decide\n"
    + _PROOF_BODY)


# ===========================================================================
# UNIQUENESS RIVALS (reject) — wrong impls sharing the frozen spec exactly.
# Each MUST be rejected; a verifying rival would be a real
# verify-does-not-imply-resolve break (SPEC-TOO-WEAK). Each ships a witness SEEN
# to discriminate.
# ===========================================================================

# uniq-hardwire-default-flag: THE CHANGE ITSELF, inverted. On the plain-data arm
# use the hard-wired escaping default instead of the engine's configured flag —
# exactly what Solution_prepatch.lean does, i.e. the pre-change behavior.
_UNIQ_HARDWIRE = _swap(_BASE, _PLAIN_ARM, "    autoescape := true")

# uniq-drop-flag-guard: drop the caller-shape guard altogether and always use the
# supplied context's own flag, even when no ready-made context was supplied.
_UNIQ_DROP_GUARD = _swap(_BASE, _SELECT,
                         "  let autoescape := suppliedCtxAutoescape")

# uniq-swap-flag-arms: keep both arms but EXCHANGE which flag each one uses — the
# engine's configured flag when a ready-made context is supplied, the supplied
# context's flag when plain data is given.
_UNIQ_SWAP_ARMS = _swap(_BASE, _SELECT, """  let mut autoescape := engineAutoescape
  if !suppliedIsContext then
    autoescape := suppliedCtxAutoescape""")

# uniq-frame-drop-trailing: select the flag correctly and render the value
# correctly, but omit the trailing literal text from the assembled output.
_UNIQ_DROP_TRAILING = _swap(_BASE, _RETURN,
                            "  return leading ++ renderValue autoescape value")

# uniq-frame-drop-leading: the companion on the other side — omit the leading
# literal text from the assembled output.
_UNIQ_DROP_LEADING = _swap(_BASE, _RETURN,
                           "  return renderValue autoescape value ++ trailing")

# uniq-render-wrong-argument: select the flag correctly and keep the frame, but
# hand the value-rendering step the wrong argument (the leading literal text
# instead of the interpolated value).
_UNIQ_WRONG_ARG = _swap(
    _BASE, _RETURN,
    "  return leading ++ renderValue autoescape leading ++ trailing")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY, else SPEC-TOO-STRONG) ----
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_BRANCH_REORDER,
        "rationale": "structurally-different CORRECT impl: the same flag "
                     "selection written with the arms exchanged (initialize "
                     "from the engine's configured flag, override with the "
                     "supplied context's own flag when a ready-made context is "
                     "given). Each caller shape still receives the flag part "
                     "(S) demands and the frame (F) is untouched, so the "
                     "postcondition still holds and the frozen tactic body "
                     "closes it. Ports the nagini pos-control-reordered onto "
                     "the one branch this carrier has. If a faithful correct "
                     "impl with the opposite branch polarity cannot verify => "
                     "SPEC-TOO-STRONG (the equation is over-fit to one branch "
                     "order).",
    },
    {
        "id": "pos-select-expression",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_SELECT_EXPRESSION,
        "rationale": "the honest CHEAPEST correct impl: drop the mutable local "
                     "and select the flag with a single conditional expression. "
                     "Re-expresses the nagini echo-attempt-honest control on "
                     "this carrier — `renderValue` is universally quantified, "
                     "so the pinned right-hand side is a function OF the inputs "
                     "for EVERY renderer and there is no answer-key to echo; "
                     "the cheapest impl satisfying the equation therefore still "
                     "selects the flag and assembles the frame for real. Must "
                     "verify (else SPEC-TOO-STRONG), and demonstrates the spec "
                     "is not echo-vulnerable: no wrong impl can satisfy the "
                     "equation, which is what the reject lane below exhibits.",
    },
    {
        "id": "pos-render-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_RENDER_LOCAL,
        "rationale": "a correct impl with a DIFFERENT control shape: bind the "
                     "rendered value to a local before assembling the output "
                     "frame. Direct port of the nagini pos-control-seg-local. "
                     "Value flow is unchanged, so both (S) and (F) still "
                     "discharge and the frozen tactic body closes it. If it "
                     "cannot verify => SPEC-TOO-STRONG (over-fit to the "
                     "inline-assembly code form).",
    },
    {
        "id": "pos-early-return",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_EARLY_RETURN,
        "rationale": "a correct impl with a different CONTROL-FLOW shape: "
                     "replace the mutable flag and single exit with one early "
                     "return per caller shape, each assembling the frame with "
                     "the flag that shape supplies. Two exits, no mutable local; "
                     "measured to still be closed by the frozen tactic body, so "
                     "it is carried with the frozen proof unchanged. If it "
                     "cannot verify => SPEC-TOO-STRONG (over-fit to the "
                     "single-exit code form).",
    },
    {
        "id": "pos-boolean-select",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_BOOLEAN_SELECT,
        "rationale": "the strongest soundness probe available here: select the "
                     "flag with a BOOLEAN COMBINATOR rather than a conditional — "
                     "the disjunction of 'a ready-made context was supplied and "
                     "its own flag is set' and 'plain data was supplied and the "
                     "engine's configured flag is set'. Equivalent for every "
                     "input, but measured NOT definitionally equal to the frozen "
                     "impl: the frozen tactic body FAILS on it (`rfl` reports "
                     "the combinator is not definitionally the conditional), so "
                     "this case carries its own proof of the BYTE-IDENTICAL "
                     "theorem statement. Part (S) is therefore RE-ESTABLISHED "
                     "for a genuinely new impl shape rather than inherited from "
                     "the frozen one. If it cannot verify => SPEC-TOO-STRONG.",
    },

    # ---- admissibility (re-aimed; must VERIFY) ----
    {
        "id": "admiss-total-domain",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS_F2P,
        "rationale": "RE-AIMED from the nagini admiss-f2p-witness, whose subject "
                     "(a read-only fractional-permission precondition "
                     "establishable for an F2P-shaped input) has no counterpart "
                     "here: `correct_renderToString` is universally quantified "
                     "over all seven inputs with NO hypothesis arrow, so there "
                     "is no precondition that could be too strong and "
                     "PRECOND-TOO-STRONG is unreachable. The analogue on a total "
                     "carrier is the obligation being SATISFIABLE at exactly an "
                     "F2P-shaped input, so this case does not merely re-run the "
                     "frozen impl: it discharges TWO `have`s BY EVALUATION at the "
                     "concrete F2P-shaped point (escaping configured OFF, plain "
                     "data, a value carrying markup, with a renderer that "
                     "distinguishes the flag settings) before closing the frozen "
                     "obligation verbatim. The first evaluates the postcondition "
                     "to TRUE at the output the changed behavior produces there; "
                     "the second evaluates it to FALSE at the output the "
                     "pre-change behavior produces there. Together they show the "
                     "obligation is both satisfiable AND discriminating at that "
                     "input, which is what would be hollow if the postcondition "
                     "were satisfiable by either output there. If either `have` "
                     "failed, the obligation would be unsatisfiable — or "
                     "indifferent — at the one input the change is about.",
    },

    # ---- uniqueness rivals (must be REJECTED, else SPEC-TOO-WEAK) ----
    {
        "id": "uniq-hardwire-default-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _UNIQ_HARDWIRE,
        "refinement": "THIS IS THE PRE-CHANGE BEHAVIOR. On the plain-data arm it "
                      "uses the hard-wired escaping default instead of the "
                      "engine's configured flag, so an engine configured with "
                      "escaping OFF is ignored and the value is escaped anyway. "
                      "Its faithful real patch is the UNCHANGED pre-change code "
                      "(Solution_prepatch.lean is byte-identical to this rival "
                      "in the impl region), which is precisely what FAILS the "
                      "sole F2P: escaping configured off, plain data, a value "
                      "containing markup, which the test requires verbatim but "
                      "this escapes. It would NOT resolve.",
        "rationale": "REJECT from part (S) on the plain-data arm: `eff` must be "
                      "the engine's configured flag when no ready-made context "
                      "is supplied, and a hard-wired `true` is not that binder. "
                      "Refuted at engineAutoescape=false, suppliedIsContext="
                      "false with a renderer that distinguishes the two flag "
                      "settings — the exact F2P-shaped point. If it verified => "
                      "SPEC-TOO-WEAK (the spec would admit the very behavior "
                      "the change corrects; mirrors G-DIFF).",
        "witness": _witness(_RV_BRACKET, "false", "false", "false",
                            "obj:", "s&t", ";"),
    },
    {
        "id": "uniq-drop-flag-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _UNIQ_DROP_GUARD,
        "refinement": "drops the caller-shape guard and always uses the supplied "
                      "context's own flag. When plain data was given there IS no "
                      "supplied rendering context, so 'its flag' degenerates to "
                      "the hard-wired construction default (escaping on) — "
                      "behaviorally the pre-change construction on exactly the "
                      "path the F2P exercises. Its faithful real patch therefore "
                      "escapes a markup-containing value under an engine "
                      "configured with escaping off and FAILS the sole F2P; it "
                      "would NOT resolve. NEAR-MISS distinct from "
                      "uniq-hardwire-default-flag: that rival is wrong for every "
                      "plain-data caller whose engine has escaping off, while "
                      "this one is wrong only where the two flags disagree — so "
                      "the two rivals' wrong-sets are neither nested nor equal, "
                      "and this case is refuted inside the DIFFERENCE (the "
                      "sub-domain where this rival is wrong and the hard-wiring "
                      "rival is CORRECT: a plain-data caller whose engine has "
                      "escaping ON while the supplied-context flag binder is "
                      "off). MEASURED (audit): this witness elaborates against "
                      "this rival and FAILS against the hard-wiring rival, so it "
                      "is a discriminator between the two near-misses and not "
                      "merely a second copy of the previous refutation.",
        "rationale": "REJECT from part (S): with no ready-made context supplied, "
                      "`eff` is pinned to the engine's configured flag, and this "
                      "rival reports the OTHER flag binder instead. Refuted at "
                      "engineAutoescape=TRUE, suppliedIsContext=false, "
                      "suppliedCtxAutoescape=false — the point that separates the "
                      "two flag binders in the direction that is this rival's "
                      "ALONE, and it varies engineAutoescape away from the value "
                      "uniq-hardwire-default-flag holds it at. (The mirrored "
                      "point engineAutoescape=false/suppliedCtxAutoescape=true "
                      "also refutes this rival, but was measured to refute the "
                      "hard-wiring rival as well, so it would have attributed "
                      "nothing this battery does not already establish.) If it "
                      "verified => SPEC-TOO-WEAK (the plain-data arm would not "
                      "actually be pinned to the engine's flag).",
        "witness": _witness(_RV_MARK, "true", "false", "false", "p", "v", "q"),
    },
    {
        "id": "uniq-swap-flag-arms",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _UNIQ_SWAP_ARMS,
        "refinement": "EXCHANGES the two arms: the engine's configured flag is "
                      "used when a ready-made context is supplied, and the "
                      "supplied context's flag when plain data is given. Its "
                      "faithful real patch is wrong on BOTH caller shapes. On "
                      "the plain-data path it reads a flag off a rendering "
                      "context that was never supplied, which is the hard-wired "
                      "construction default (escaping on) — so it escapes a "
                      "markup-containing value under an engine configured with "
                      "escaping off and FAILS the sole F2P exactly as the "
                      "pre-change behavior does. On the ready-made-context path "
                      "it overrides a caller's explicit escaping choice with the "
                      "engine's, silently re-escaping content in a context "
                      "deliberately built with escaping off — the same defect "
                      "class in the opposite direction. It would NOT resolve. "
                      "Ports the nagini rival-invert-policy argument (the flag's "
                      "direction/source is unconstrained) onto the two arms this "
                      "carrier exposes.",
        "rationale": "REJECT from part (S) on the READY-MADE-CONTEXT arm: when a "
                      "context is supplied, `eff` is pinned to that context's "
                      "own flag, and this rival reports the engine's instead. "
                      "Refuted at suppliedIsContext=TRUE, "
                      "suppliedCtxAutoescape=false, engineAutoescape=true — the "
                      "sub-domain that is this rival's alone: the two rivals "
                      "above are both correct there, so this witness is not "
                      "shared with them, and it is the only case that varies "
                      "suppliedIsContext to true on the flag-selection lane. If "
                      "it verified => SPEC-TOO-WEAK (which caller shape supplies "
                      "which flag would be unconstrained).",
        "witness": _witness(_RV_MARK, "true", "true", "false", "A", "v", "B"),
    },
    {
        "id": "uniq-frame-drop-trailing",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _UNIQ_DROP_TRAILING,
        "refinement": "selects the flag correctly and renders the value "
                      "correctly, but omits the trailing literal text from the "
                      "assembled output. Its faithful real patch drops the "
                      "template's literal text after the interpolated value, and "
                      "BOTH observed renders compare the FULL output string "
                      "against an expectation that ends in literal text — so it "
                      "FAILS the sole F2P and the basic-render check alike. It "
                      "would NOT resolve. RE-AIMS the nagini "
                      "partial-domain-verbatim-first attack: like it, this rival "
                      "is correct on a whole sub-domain (every input whose "
                      "trailing literal is empty) and wrong outside it, so the "
                      "spec must pin the WHOLE output and not merely the rendered "
                      "value portion.",
        "rationale": "REJECT from part (F): the output is pinned to `leading ++ "
                      "renderValue eff value ++ trailing`, so the trailing "
                      "literal binder is not free. Refuted at a point with an "
                      "EMPTY leading literal and a non-empty trailing one, using "
                      "a flag-insensitive renderer — so the refutation is "
                      "attributable to the frame alone and not to a flag "
                      "mis-selection, and it is a point where "
                      "uniq-frame-drop-leading is correct. If it verified => "
                      "SPEC-TOO-WEAK (an output component would be free, the "
                      "referentially-transparent analogue of the "
                      "full-permission hole).",
        "witness": _witness(_RV_ID, "true", "true", "true", "", "v", "!"),
    },
    {
        "id": "uniq-frame-drop-leading",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _UNIQ_DROP_LEADING,
        "refinement": "the companion on the other side: omits the leading "
                      "literal text from the assembled output. Its faithful real "
                      "patch drops the template's literal text before the "
                      "interpolated value; both observed renders expect an "
                      "output that BEGINS with literal text, so it FAILS them "
                      "and would NOT resolve. Correct on every input whose "
                      "leading literal is empty — a genuine partial-domain "
                      "break on the complementary sub-domain to "
                      "uniq-frame-drop-trailing, which is why it is refuted at "
                      "the mirrored point rather than sharing that witness.",
        "rationale": "REJECT from part (F): the leading literal binder is pinned "
                      "too. Refuted at a NON-EMPTY leading literal with an EMPTY "
                      "trailing one — the mirror of the previous witness, where "
                      "uniq-frame-drop-trailing is correct — using a "
                      "flag-insensitive renderer of a different shape, so both "
                      "the `leading`/`trailing` binders and the `renderValue` "
                      "binder are varied. If it verified => SPEC-TOO-WEAK.",
        "witness": _witness(_RV_BANG, "false", "true", "true", "L", "v", ""),
    },
    {
        "id": "uniq-render-wrong-argument",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _UNIQ_WRONG_ARG,
        "refinement": "selects the flag correctly and keeps both literals in "
                      "place, but hands the value-rendering step the WRONG "
                      "ARGUMENT — the leading literal text instead of the "
                      "interpolated value. Its faithful real patch renders "
                      "something other than the caller's data value into the "
                      "output, so the interpolated data never appears: both "
                      "observed renders assert the data value appears between "
                      "the literals, so it FAILS them and would NOT resolve. "
                      "Correct only where the two strings coincide.",
        "rationale": "REJECT from part (F) on its third position: the argument "
                      "handed to the value-rendering step is pinned to the "
                      "`value` binder. Refuted at a point where the leading "
                      "literal and the value differ, with a flag-insensitive "
                      "renderer — so neither the flag selection nor the literal "
                      "positions can account for the divergence — and it is the "
                      "only witness that varies `value` against a non-empty "
                      "leading literal AND a non-empty trailing literal at once. "
                      "If it verified => SPEC-TOO-WEAK (the rendering step's "
                      "argument would be free, so an impl could render anything "
                      "at all into the value position).",
        "witness": _witness(_RV_ID, "true", "false", "false", "A", "B", "C"),
    },
]

AXIOM_TESTS = []
