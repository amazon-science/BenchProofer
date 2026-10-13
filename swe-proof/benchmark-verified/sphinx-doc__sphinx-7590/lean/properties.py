"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-7590 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and every ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled total function over a ``List Char`` head-of-input
carrier). ``literalId s : Option String`` decides the mangled id of the literal
at the head of ``s``. The recognisers that measure how much of the head is a
float / a standard suffix / an integer of each shape / a trailing identifier are
modeled as opaque length-returning callees (they appear IDENTICALLY in the spec
and the impl, so they cancel); the behaviour under test is the CONTROL FLOW that
recombines them into the mangled id, together with the three mangling formulas
it composes:

  * a bare literal of source text ``data`` -> ``"L" data "E"``;
  * a literal carrying a recognised standard suffix keeps the suffix inside its
    source text -> again ``"L" data "E"`` over the extended text;
  * a bare literal (with NO standard suffix) directly followed by an identifier
    is a user-defined literal, mangled as a call of the identifier on the
    literal: ``"clL_Zli" (id ident) "E" (inner) "E"``, where ``(id ident)`` is
    the reserved namespace abbreviation for the reserved name and otherwise the
    identifier's length in decimal followed by its text. A standard suffix takes
    precedence over a trailing identifier.

The postcondition equates ``result`` to exactly this recombination, fully
GROUNDED in the inputs (the opaque recognisers, the concrete mangling formulas,
and total list ``take``/``drop``) — there is no ungrounded answer-key oracle to
echo.

ADVERSARIAL READ of the nagini classes on THIS carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini bundle held ``lit`` /
    ``ident`` / ``ident_id`` at a fractional (read-only) permission and its
    MANDATORY frame probes wrote through that half-permission to fake a
    postcondition match. Lean is referentially transparent: the input carries no
    heap permission, there is no read-only half-permission to overwrite and no
    aliasing to exploit. That whole class (nagini ``frame-mutate-ident_id``,
    ``frame-mutate-lit``, ``c-frame-mutate-lit``) has no expressible instance
    here and no substitute is fabricated for it.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Every nagini value rival (never build a
    UDL, ignore the suffix flag, raw identifier text without the length prefix,
    drop a framing ``E``, mangle the suffix wrongly) re-expresses as a control- or
    value-level deviation in the recombination and is carried over below.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is grounded in the
    inputs (see above), so there is no answer key to echo. The honest analogues
    are the POSITIVE CONTROLS (``pos-*``) that must verify.

The two nagini modeled functions collapse to one here. The nagini bundle modeled
``number_literal_id`` (the UDL dialect) and ``c_number_literal_id`` (the simpler
suffix-vs-not dialect) as two separate functions; this carrier folds both into
the single ``literalId`` recombination (a recognised suffix is kept in the text,
an unrecognised trailing run becomes a UDL identifier or is left bare). The
c-domain rivals therefore re-express as suffix-vs-UDL deviations on the same
function rather than a second function; see ``assessment`` in the payload.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet proving the rival CONTRADICTS the spec at one
concrete input. Because the recognisers are opaque, a witness cannot ``decide``
a raw input; each instead fixes the relevant recogniser outputs by hypothesis at
a concrete float-branch head (so ``take``/``drop`` and the mangling formulas all
compute) and refutes the spec predicate there. Each was checked to hold of its
rival and to FAIL on the frozen solution (so it discriminates rather than
asserting a tautology). The reject rivals carry the FROZEN proof body verbatim
(introducing a ``sorry`` would violate the variant scope), so their rejection is
the frozen script failing to close against the reshaped impl — exactly why the
witness is what attributes the rejection to the spec.

AXIOM lane: dropped (the axiom lane belongs to G-AX). meta.json declares only
opaque recogniser signatures and no consumed ``axiom … _prop``, so there is no
axiom-soundness / axiom-containment obligation for this gate anyway.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7590"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each is the FULL body of the impl region, or the FULL tactic
# body of the proof region, so every replacement lands entirely inside the
# region it means to edit and same_spec is preserved by construction.
# ---------------------------------------------------------------------------

_I_GOLD = (
    "def implementation_literalId (s : List Char) : Option String := Id.run do\n"
    "  let fl := floatMatch s\n"
    "  if fl > 0 then\n"
    "    return some (finishLiteral fl s floatSuffixMatch)\n"
    "  for m in [binMatch, hexMatch, decMatch, octMatch] do\n"
    "    let il := m s\n"
    "    if il > 0 then\n"
    "      return some (finishLiteral il s intSuffixMatch)\n"
    "  return none"
)

_P_GOLD = (
    "  intro s\n"
    "  unfold problem_spec_literalId implementation_literalId intMatchLen\n"
    "  simp only [Id.run, List.forIn_cons, List.forIn_nil, bind, pure]\n"
    "  by_cases hf : floatMatch s > 0\n"
    "  · simp only [hf, if_true]\n"
    "  · simp only [hf, if_false]\n"
    "    by_cases hb : binMatch s > 0\n"
    "    · simp [hb]\n"
    "    · by_cases hh : hexMatch s > 0\n"
    "      · simp [hb, hh]\n"
    "      · by_cases hd : decMatch s > 0\n"
    "        · simp [hb, hh, hd]\n"
    "        · by_cases ho : octMatch s > 0 <;> simp [hb, hh, hd, ho]"
)

# fail loud at import if the frozen bundle ever drifts from these anchors
assert _BASE.count(_I_GOLD) == 1, "gold impl anchor drifted from Solution.lean"
assert _BASE.count(_P_GOLD) == 1, "gold proof anchor drifted from Solution.lean"


SPEC_TESTS = [

    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_literalId` statement byte-identical; none introduces a
    # helper lemma, axiom, or assumption token.
    # =====================================================================

    # -- reshape #1: bind the recogniser list to a local before iterating. Same
    # value flow into the loop, so the frozen proof body still closes.
    {
        "id": "pos-recogniser-list-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _I_GOLD,
            "def implementation_literalId (s : List Char) : Option String := Id.run do\n"
            "  let fl := floatMatch s\n"
            "  if fl > 0 then\n"
            "    return some (finishLiteral fl s floatSuffixMatch)\n"
            "  let recognisers := [binMatch, hexMatch, decMatch, octMatch]\n"
            "  for m in recognisers do\n"
            "    let il := m s\n"
            "    if il > 0 then\n"
            "      return some (finishLiteral il s intSuffixMatch)\n"
            "  return none"),
        "rationale": "naming the integer-recogniser list as a local before the "
                     "loop is a pure reshape: the same recognisers are tried in "
                     "the same order and the same mangled id is produced on every "
                     "input, so `result = <the recombination>` still holds. Must "
                     "verify (else SPEC-TOO-STRONG). Proof: the frozen tactic body "
                     "is retained (the local is zeta-reduced before the case "
                     "split).",
    },

    # -- reshape #2: bind the produced id to a local before wrapping in `some`.
    # Same value flow into every `return`.
    {
        "id": "pos-result-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _I_GOLD,
            "def implementation_literalId (s : List Char) : Option String := Id.run do\n"
            "  let fl := floatMatch s\n"
            "  if fl > 0 then\n"
            "    let r := finishLiteral fl s floatSuffixMatch\n"
            "    return some r\n"
            "  for m in [binMatch, hexMatch, decMatch, octMatch] do\n"
            "    let il := m s\n"
            "    if il > 0 then\n"
            "      let r := finishLiteral il s intSuffixMatch\n"
            "      return some r\n"
            "  return none"),
        "rationale": "binding each produced id to a local before wrapping it in "
                     "`some` keeps the exact value returned on every branch, so "
                     "`result = <the recombination>` is unchanged; a correct "
                     "reshape must verify. Proof: frozen tactic body retained (the "
                     "locals zeta-reduce).",
    },

    # -- reshape #3: negate the float guard and swap the two exit paths. Same
    # float-then-integers semantics reached by the opposite control path; the
    # frozen script no longer applies, so the obligation is RE-PROVED (statement
    # byte-identical) with a mirror case split.
    {
        "id": "pos-negated-float-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _I_GOLD,
                "def implementation_literalId (s : List Char) : Option String := Id.run do\n"
                "  let fl := floatMatch s\n"
                "  if fl = 0 then\n"
                "    for m in [binMatch, hexMatch, decMatch, octMatch] do\n"
                "      let il := m s\n"
                "      if il > 0 then\n"
                "        return some (finishLiteral il s intSuffixMatch)\n"
                "    return none\n"
                "  return some (finishLiteral fl s floatSuffixMatch)"),
            _P_GOLD,
            "  intro s\n"
            "  unfold problem_spec_literalId implementation_literalId intMatchLen\n"
            "  simp only [Id.run, List.forIn_cons, List.forIn_nil, bind, pure]\n"
            "  by_cases hf : floatMatch s = 0\n"
            "  · simp only [hf, if_true, Nat.lt_irrefl, gt_iff_lt]\n"
            "    by_cases hb : binMatch s > 0\n"
            "    · simp [hb]\n"
            "    · by_cases hh : hexMatch s > 0\n"
            "      · simp [hb, hh]\n"
            "      · by_cases hd : decMatch s > 0\n"
            "        · simp [hb, hh, hd]\n"
            "        · by_cases ho : octMatch s > 0 <;> simp [hb, hh, hd, ho]\n"
            "  · simp only [hf, if_false]\n"
            "    have : floatMatch s > 0 := Nat.pos_of_ne_zero hf\n"
            "    simp [this]"),
        "rationale": "handling the no-float case in the guard and falling through "
                     "to the float exit preserves the exact float-takes-precedence "
                     "then integer-order semantics and the same mangled id on "
                     "every input, so `result = <the recombination>` still holds; "
                     "must verify (else SPEC-TOO-STRONG). Re-proved because the "
                     "frozen script is tuned to the frozen guard shape: the mirror "
                     "case split on `floatMatch s = 0` closes it, using only core "
                     "lemmas (`Nat.pos_of_ne_zero`), no new declaration.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control that the obligation is SATISFIABLE at a
    # normal, F2P-shaped input rather than only in the abstract. The frozen
    # theorem carries no precondition hypothesis (the modeled behaviour is
    # total), so the nagini precondition-admission probe has no binder to attack;
    # the honest analogue discharges the spec predicate at a ground UDL-shaped
    # input (a bare float literal with no standard suffix and a trailing
    # identifier — the shape of the issue's `6.62607015e-34q_J`) inside the proof
    # region, alongside the frozen obligation. If that ground instance could not
    # be discharged, the modeled behaviour would be unsatisfiable at exactly the
    # input the F2P exercises (the analogue of PRECOND-TOO-STRONG).
    # =====================================================================
    {
        "id": "admiss-udl-reachable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_GOLD,
            "  have _reachable :\n"
            "      floatMatch \"5x\".toList = 1 →\n"
            "      floatSuffixMatch ((\"5x\".toList).drop 1) = 0 →\n"
            "      udlMatch ((\"5x\".toList).drop 1) = 1 →\n"
            "      problem_spec_literalId \"5x\".toList\n"
            "        (implementation_literalId \"5x\".toList) := by\n"
            "    intro hf hs hu\n"
            "    unfold problem_spec_literalId implementation_literalId\n"
            "    simp only [Id.run, List.forIn_cons, List.forIn_nil, bind, pure, hf]\n"
            "    simp [hf]\n"
            + _P_GOLD),
        "rationale": "the obligation is discharged at a ground UDL-shaped input (a "
                     "bare float literal with no standard suffix followed by a "
                     "trailing identifier — the shape of the issue repro) as a "
                     "`have` inside the existing tactic body, then the frozen "
                     "obligation is closed verbatim. Verifies (else the modeled "
                     "behaviour is unsatisfiable at the normal input, the analogue "
                     "of PRECOND-TOO-STRONG). Nothing is assumed: no new "
                     "declaration, the theorem statement is byte-identical.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement argument
    # that its faithful real patch would NOT resolve the F2P, so a verifying rival
    # would be a true verify-does-not-imply-resolve break rather than an artifact,
    # and (b) a refutation witness pinning the violation at one concrete input.
    # Each reject rival ships the FROZEN proof body verbatim (a `sorry` would
    # violate the variant scope), so its rejection is the frozen script failing to
    # close against the reshaped impl — which is exactly why the witness, not the
    # rejection, attributes the failure to the spec.
    # =====================================================================

    # -- PARTIAL #1: the PRE-PATCH rival — never folds a trailing identifier ----
    # Keeps a standard suffix but omits the UDL fold, so a bare literal followed
    # by an identifier mangles to just the bare id (the identifier is dropped).
    # This IS the pre-patch behaviour.
    {
        "id": "weak-prepatch-no-udl",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_GOLD,
            "def implementation_literalId (s : List Char) : Option String := Id.run do\n"
            "  let fl := floatMatch s\n"
            "  if fl > 0 then\n"
            "    let sfx := floatSuffixMatch (s.drop fl)\n"
            "    return some (numId (s.take (fl + sfx)))\n"
            "  for m in [binMatch, hexMatch, decMatch, octMatch] do\n"
            "    let il := m s\n"
            "    if il > 0 then\n"
            "      let sfx := intSuffixMatch (s.drop il)\n"
            "      return some (numId (s.take (il + sfx)))\n"
            "  return none"),
        "refinement": "this IS the pre-patch behaviour: a base literal followed by "
                      "an identifier (with no standard suffix) is never folded into "
                      "a user-defined literal, so the issue's `6.62607015e-34q_J` "
                      "leaves the `q_J` unconsumed and the parse fails ('Expected "
                      "end of definition'); test_expressions would NOT resolve.",
        "rationale": "REJECT from the postcondition's UDL clause: on a bare literal "
                     "with no standard suffix and a trailing identifier the result "
                     "must be the `clL_Zli…` UDL mangling, not the bare `L…E`. If "
                     "it verified, the discriminating fix is unpinned "
                     "(SPEC-TOO-WEAK).",
        "witness": (
            "example\n"
            "    (hf : floatMatch \"5x\".toList = 1)\n"
            "    (hs : floatSuffixMatch ((\"5x\".toList).drop 1) = 0)\n"
            "    (hu : udlMatch ((\"5x\".toList).drop 1) = 1) :\n"
            "    ¬ problem_spec_literalId \"5x\".toList\n"
            "        (implementation_literalId \"5x\".toList) := by\n"
            "  unfold problem_spec_literalId implementation_literalId finishLiteral\n"
            "  simp only [Id.run, hf, hs, hu]\n"
            "  decide\n"
        ),
    },

    # -- PARTIAL #2: ignore the standard suffix, always try to fold a UDL --------
    # Even when a recognised suffix is present, folds a trailing identifier into a
    # UDL instead of keeping the suffix in the literal text. Correct on the
    # no-suffix subdomain, diverges on the suffixed subdomain.
    {
        "id": "weak-ignores-suffix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_GOLD,
            "def implementation_literalId (s : List Char) : Option String := Id.run do\n"
            "  let fl := floatMatch s\n"
            "  if fl > 0 then\n"
            "    let rest := s.drop fl\n"
            "    let baseId := numId (s.take fl)\n"
            "    let u := udlMatch rest\n"
            "    if u > 0 then\n"
            "      return some (udlId (rest.take u) baseId)\n"
            "    return some baseId\n"
            "  for m in [binMatch, hexMatch, decMatch, octMatch] do\n"
            "    let il := m s\n"
            "    if il > 0 then\n"
            "      return some (finishLiteral il s intSuffixMatch)\n"
            "  return none"),
        "refinement": "in the real parser a recognised standard suffix consumes "
                      "into the literal text and the literal is a plain suffixed "
                      "number, never a user-defined literal; treating a suffixed "
                      "literal as a UDL mismangles it (it emits the `clL_Zli…` call "
                      "form instead of the plain `L…E` over the suffixed text), so "
                      "the suffixed rows of test_expressions would NOT resolve.",
        "rationale": "REJECT from the postcondition's suffix-precedence: on a bare "
                     "literal WITH a recognised standard suffix and a trailing "
                     "identifier the result must keep the suffix in the text (bare "
                     "`L…E`), not build the UDL mangling. If it verified, the "
                     "suffix discriminator is unpinned (SPEC-TOO-WEAK).",
        "witness": (
            "example\n"
            "    (hf : floatMatch \"5x\".toList = 1)\n"
            "    (hs : floatSuffixMatch ((\"5x\".toList).drop 1) = 1)\n"
            "    (hu : udlMatch ((\"5x\".toList).drop 1) = 1) :\n"
            "    ¬ problem_spec_literalId \"5x\".toList\n"
            "        (implementation_literalId \"5x\".toList) := by\n"
            "  unfold problem_spec_literalId implementation_literalId finishLiteral\n"
            "  simp only [Id.run, hf, hs, hu]\n"
            "  decide\n"
        ),
    },

    # -- PARTIAL #3: raw identifier text, missing the length prefix --------------
    # Builds the UDL mangling but embeds the raw identifier text instead of its
    # id fragment (which prefixes the length in decimal). The strongest reasoned
    # attack: correct except for the missing length prefix.
    {
        "id": "weak-raw-ident-no-length-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_GOLD,
            "def implementation_literalId (s : List Char) : Option String := Id.run do\n"
            "  let fl := floatMatch s\n"
            "  if fl > 0 then\n"
            "    let rest := s.drop fl\n"
            "    let sfx := floatSuffixMatch rest\n"
            "    if sfx > 0 then\n"
            "      return some (numId (s.take (fl + sfx)))\n"
            "    let baseId := numId (s.take fl)\n"
            "    let u := udlMatch rest\n"
            "    if u > 0 then\n"
            "      return some (\"clL_Zli\" ++ String.mk (rest.take u) ++ \"E\" ++ baseId ++ \"E\")\n"
            "    return some baseId\n"
            "  for m in [binMatch, hexMatch, decMatch, octMatch] do\n"
            "    let il := m s\n"
            "    if il > 0 then\n"
            "      return some (finishLiteral il s intSuffixMatch)\n"
            "  return none"),
        "refinement": "the real identifier id fragment is its length in decimal "
                      "followed by its text (e.g. `4_udl`), not the raw text "
                      "(`_udl`); emitting the raw text yields `clL_Zli_udlE…` "
                      "instead of the expected `clL_Zli4_udlE…`, so every UDL row "
                      "of test_expressions would NOT resolve.",
        "rationale": "REJECT from the postcondition's UDL clause, which embeds the "
                     "identifier's id fragment (length-prefixed text), not its raw "
                     "text. If it verified, the length-prefix component is unpinned "
                     "(SPEC-TOO-WEAK).",
        "witness": (
            "example\n"
            "    (hf : floatMatch \"5x\".toList = 1)\n"
            "    (hs : floatSuffixMatch ((\"5x\".toList).drop 1) = 0)\n"
            "    (hu : udlMatch ((\"5x\".toList).drop 1) = 1) :\n"
            "    ¬ problem_spec_literalId \"5x\".toList\n"
            "        (implementation_literalId \"5x\".toList) := by\n"
            "  unfold problem_spec_literalId implementation_literalId finishLiteral\n"
            "    udlId identId numId\n"
            "  simp only [Id.run, hf, hs, hu]\n"
            "  decide\n"
        ),
    },

    # -- PARTIAL #4: drop the framing `E` after the identifier id ----------------
    # Off-by-one: omits the `E` between the identifier id and the inner mangling,
    # so the UDL id is `clL_Zli<id><inner>E` instead of `clL_Zli<id>E<inner>E`.
    {
        "id": "weak-drop-mid-E",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_GOLD,
            "def implementation_literalId (s : List Char) : Option String := Id.run do\n"
            "  let fl := floatMatch s\n"
            "  if fl > 0 then\n"
            "    let rest := s.drop fl\n"
            "    let sfx := floatSuffixMatch rest\n"
            "    if sfx > 0 then\n"
            "      return some (numId (s.take (fl + sfx)))\n"
            "    let baseId := numId (s.take fl)\n"
            "    let u := udlMatch rest\n"
            "    if u > 0 then\n"
            "      return some (\"clL_Zli\" ++ identId (rest.take u) ++ baseId ++ \"E\")\n"
            "    return some baseId\n"
            "  for m in [binMatch, hexMatch, decMatch, octMatch] do\n"
            "    let il := m s\n"
            "    if il > 0 then\n"
            "      return some (finishLiteral il s intSuffixMatch)\n"
            "  return none"),
        "refinement": "the real UDL mangling frames the identifier id with an `E` "
                      "before the inner literal mangling; dropping it gives "
                      "`clL_Zli4_udlL5EE` instead of `clL_Zli4_udlEL5EE`, a "
                      "non-conformant mangling that every UDL row of "
                      "test_expressions rejects.",
        "rationale": "REJECT from the exact UDL clause: the mangling has an "
                     "explicit `E` between the identifier id and the inner "
                     "mangling, absent here. Off-by-one byte layout (SPEC-TOO-WEAK "
                     "if admitted).",
        "witness": (
            "example\n"
            "    (hf : floatMatch \"5x\".toList = 1)\n"
            "    (hs : floatSuffixMatch ((\"5x\".toList).drop 1) = 0)\n"
            "    (hu : udlMatch ((\"5x\".toList).drop 1) = 1) :\n"
            "    ¬ problem_spec_literalId \"5x\".toList\n"
            "        (implementation_literalId \"5x\".toList) := by\n"
            "  unfold problem_spec_literalId implementation_literalId finishLiteral\n"
            "    udlId identId numId\n"
            "  simp only [Id.run, hf, hs, hu]\n"
            "  decide\n"
        ),
    },

    # -- PARTIAL #5: bare-literal mangling missing the trailing `E` --------------
    # The base id is built as `"L" ++ text` (no closing `E`). Diverges on every
    # branch that emits a bare literal id.
    {
        "id": "weak-numid-drop-E",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_GOLD,
            "def implementation_literalId (s : List Char) : Option String := Id.run do\n"
            "  let fl := floatMatch s\n"
            "  if fl > 0 then\n"
            "    let rest := s.drop fl\n"
            "    let sfx := floatSuffixMatch rest\n"
            "    if sfx > 0 then\n"
            "      return some (\"L\" ++ String.mk (s.take (fl + sfx)))\n"
            "    let baseId := \"L\" ++ String.mk (s.take fl)\n"
            "    let u := udlMatch rest\n"
            "    if u > 0 then\n"
            "      return some (udlId (rest.take u) baseId)\n"
            "    return some baseId\n"
            "  for m in [binMatch, hexMatch, decMatch, octMatch] do\n"
            "    let il := m s\n"
            "    if il > 0 then\n"
            "      return some (finishLiteral il s intSuffixMatch)\n"
            "  return none"),
        "refinement": "the real bare-literal mangling is `L` + source text + `E`; "
                      "returning `L` + text (no trailing `E`) mismangles every "
                      "plain number literal and the inner mangling of every UDL, so "
                      "the expected `…L5EE` / `…EL6.62607015e-34EE` strings fail.",
        "rationale": "REJECT from the postcondition's bare-literal formula "
                     "(`L` + text + `E`): the missing `E` breaks the equality on "
                     "every bare-id branch. Off-by-one byte layout (SPEC-TOO-WEAK "
                     "if admitted).",
        "witness": (
            "example\n"
            "    (hf : floatMatch \"5\".toList = 1)\n"
            "    (hs : floatSuffixMatch ((\"5\".toList).drop 1) = 0)\n"
            "    (hu : udlMatch ((\"5\".toList).drop 1) = 0) :\n"
            "    ¬ problem_spec_literalId \"5\".toList\n"
            "        (implementation_literalId \"5\".toList) := by\n"
            "  unfold problem_spec_literalId implementation_literalId finishLiteral numId\n"
            "  simp only [Id.run, hf, hs, hu]\n"
            "  decide\n"
        ),
    },

    # -- PARTIAL #6: fold the trailing identifier into the literal TEXT ----------
    # (the nagini c-domain always-fold defect, re-expressed). Instead of building
    # a UDL, extends the bare literal's source text over the trailing run. Correct
    # on the no-trailing-run subdomain, diverges when an identifier follows.
    {
        "id": "weak-fold-udl-as-text",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_GOLD,
            "def implementation_literalId (s : List Char) : Option String := Id.run do\n"
            "  let fl := floatMatch s\n"
            "  if fl > 0 then\n"
            "    let rest := s.drop fl\n"
            "    let sfx := floatSuffixMatch rest\n"
            "    if sfx > 0 then\n"
            "      return some (numId (s.take (fl + sfx)))\n"
            "    let u := udlMatch rest\n"
            "    return some (numId (s.take (fl + u)))\n"
            "  for m in [binMatch, hexMatch, decMatch, octMatch] do\n"
            "    let il := m s\n"
            "    if il > 0 then\n"
            "      return some (finishLiteral il s intSuffixMatch)\n"
            "  return none"),
        "refinement": "this is the pre-patch maximal-run behaviour re-expressed: a "
                      "trailing identifier is folded into the literal's source text "
                      "rather than recognised as a user-defined literal, so e.g. "
                      "`5_udl` mangles to `L5_udlE` instead of the UDL "
                      "`clL_Zli4_udlEL5EE`; every UDL row of test_expressions would "
                      "NOT resolve.",
        "rationale": "REJECT from the postcondition's UDL clause: on a bare literal "
                     "with no standard suffix and a trailing identifier the result "
                     "must be the `clL_Zli…` mangling, not the bare id over the "
                     "extended text. If it verified, the UDL-vs-text discriminator "
                     "is unpinned (SPEC-TOO-WEAK).",
        "witness": (
            "example\n"
            "    (hf : floatMatch \"5x\".toList = 1)\n"
            "    (hs : floatSuffixMatch ((\"5x\".toList).drop 1) = 0)\n"
            "    (hu : udlMatch ((\"5x\".toList).drop 1) = 1) :\n"
            "    ¬ problem_spec_literalId \"5x\".toList\n"
            "        (implementation_literalId \"5x\".toList) := by\n"
            "  unfold problem_spec_literalId implementation_literalId finishLiteral\n"
            "    udlId identId numId\n"
            "  simp only [Id.run, hf, hs, hu]\n"
            "  decide\n"
        ),
    },

    # -- PARTIAL #7: drop the recognised standard suffix from the text -----------
    # (the nagini c-domain never-fold defect, re-expressed). Ignores the suffix
    # recogniser: the base literal text stops at the base length even when a
    # suffix is recognised. Correct on the no-suffix subdomain, diverges on the
    # suffixed subdomain.
    {
        "id": "weak-drop-standard-suffix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_GOLD,
            "def implementation_literalId (s : List Char) : Option String := Id.run do\n"
            "  let fl := floatMatch s\n"
            "  if fl > 0 then\n"
            "    let rest := s.drop fl\n"
            "    let baseId := numId (s.take fl)\n"
            "    let u := udlMatch rest\n"
            "    if u > 0 then\n"
            "      return some (udlId (rest.take u) baseId)\n"
            "    return some baseId\n"
            "  for m in [binMatch, hexMatch, decMatch, octMatch] do\n"
            "    let il := m s\n"
            "    if il > 0 then\n"
            "      return some (finishLiteral il s intSuffixMatch)\n"
            "  return none"),
        "refinement": "a recognised standard suffix is part of the literal's "
                      "source text in the real parser (the slice spans it); "
                      "dropping it gives `L5E` / `L5.0E` instead of the gold "
                      "`L5ulE` / `L5.0fE`, so the suffixed rows of "
                      "test_expressions would NOT resolve.",
        "rationale": "REJECT from the postcondition's suffix clause: when a "
                     "standard suffix is recognised the result text must include "
                     "it. If it verified, the suffix-folding is unpinned "
                     "(SPEC-TOO-WEAK).",
        "witness": (
            "example\n"
            "    (hf : floatMatch \"5f\".toList = 1)\n"
            "    (hs : floatSuffixMatch ((\"5f\".toList).drop 1) = 1)\n"
            "    (hu : udlMatch ((\"5f\".toList).drop 1) = 0) :\n"
            "    ¬ problem_spec_literalId \"5f\".toList\n"
            "        (implementation_literalId \"5f\".toList) := by\n"
            "  unfold problem_spec_literalId implementation_literalId finishLiteral numId\n"
            "  simp only [Id.run, hf, hs, hu]\n"
            "  decide\n"
        ),
    },
]
