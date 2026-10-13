"""properties.py — G-PBT falsification battery for django__django-12308 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes and
stamps with a recorded verdict. Each SPEC case is a full ``Solution.lean``
variant that shares the FROZEN spec byte-for-byte (region surgery: only text
inside the ``-- impl-start`` / ``-- impl-end`` region — and, for the soundness
positive, inside the ``-- proof-start`` / ``-- proof-end`` region — is changed,
so ``markers.same_spec`` holds and the single ``theorem correct_displayForField``
STATEMENT stays byte-identical). ``expect="verify"`` passes iff (in scope AND the
file elaborates with the obligation closed); ``expect="reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
contracts a whole recursive interchange serialiser and its list fold
(``serialize`` / ``serialize_list`` / ``append_all``) plus the dispatch
(``display_structured_value``), and pins the RENDERED BYTES down to individual
delimiter code points (double-quote U+0022 vs single-quote U+0027), the ``", "``
sibling separator, and the surrounding brackets/braces. This Lean bundle models
only the purely-functional CORE of the fix: the value-rendering DECISION — which
of two pre-existing renderers is selected for the field's value. The two
renderers themselves (the JSON serialiser and the generic textual renderer) are
UNCHANGED callees, modeled as ``opaque`` and never spelled out. Consequently the
nagini cases that attack the serialiser's INTERNAL bytes (the delimiter, the
separator, the brackets, the recursive fold) have NO counterpart here: those
bytes live inside an opaque callee this bundle does not model. What ports is the
attack on the DISPATCH — which renderer is chosen in each case. See the submitted
``assessment`` for the case-by-case mapping and every principled omission.

DEFENDED SURFACE (one modeled obligation). ``problem_spec_displayForField value
empty result`` pins ``result`` with THREE independent top-level clauses, one per
input class, partitioning the domain:

  * CLAUSE 1 — absent: ``isNull value = true → result = empty``. An absent value
    shows the placeholder text unchanged.
  * CLAUSE 2 — present & non-empty (the CHANGED clause): ``isNull value = false →
    truthy value = true → result = (match jsonSerialize value with | .ok s => s |
    .error _ => genericDisplay value empty)``. A present, non-empty value is
    rendered by the JSON serialiser, falling back to the generic renderer only on
    a serialisation failure. This is the discriminator the fix introduces: the
    pre-fix code sent such a value straight to the generic renderer, so a
    JSON-representable value was displayed by the generic renderer instead of as
    JSON.
  * CLAUSE 3 — present & empty: ``isNull value = false → truthy value = false →
    result = genericDisplay value empty``. A present-but-empty value uses the
    generic renderer. This behaviour is UNCHANGED by the fix (it matches both the
    pre- and post-fix cascade), so it is not independently F2P-observable — but
    it IS independently attackable, and is attacked directly by
    ``empty-through-placeholder`` below rather than being left to the positive
    control.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent:
    inputs carry no heap permission, there is no read-only half-permission to
    overwrite, no aliasing to exploit. The nagini frame-mutation rival (which
    mutated the read-only placeholder in place) has no expressible instance. Its
    behavioural CONCERN — the not-present branch must return the placeholder
    UNCHANGED — re-expresses here as clause 1, attacked by
    ``null-drops-placeholder`` below; no permission-specific substitute is
    fabricated.

  * DIVERGENCE / NON-TERMINATION — a KNOWN HOLE in the witness lane, NOT a
    vacuous class. AUDIT NOTE: the previous revision of this bullet said the
    class was VACUOUS because "a diverging implementation cannot be written at
    all", and that "the nagini sibling carries no divergence case regardless;
    nothing to port". BOTH halves were false, and both were disproven with real
    builds rather than re-argued:

      - the nagini sibling carries THREE divergence rivals
        (``diverging-dispatch-selfcall``, ``diverging-dispatch-unfalsifiable-
        guard``, ``diverging-serialiser``), each rejected there by a
        ``MustTerminate`` obligation. There WAS something to port;
      - a diverging impl IS writable in the impl region, three ways, and each
        passes ``variant_scope.variant_problems`` clean (no axiom, no sorry, no
        new theorem, obligation statement byte-identical):
        ``partial def implementation_displayForField … := implementation_display
        ForField value empty``; a ``while true`` loop whose result is DISCARDED
        before the frozen returns; and a ``while true`` loop whose result IS
        CONSUMED as the clause-2 text.

    This bundle carries no ``set_option loom.semantics.termination`` line — the
    lean backend has no termination-semantics switch — so neither disposition of
    the F′ directive applies verbatim, and what the class actually is had to be
    measured. It is NOT a spec hole: the consumed-loop rival is REJECTED by the
    frozen obligation (exit 1) and stays rejected under a stronger
    per-constructor script and under an ``aesop`` close (exit 1 each), so no
    diverging impl was found that the spec ADMITS. What blocks the case is the
    WITNESS half:

      - ``partial def`` compiles to an opaque constant and generates NO equation
        lemmas, so every computing witness shape fails on the RIVAL side — the
        half that must succeed (``simp [implementation_displayForField]`` reports
        "`simp` made no progress"; ``implementation_displayForField.eq_def`` is
        an unknown constant);
      - the loop shapes elaborate to a ``forIn Lean.Loop.mk`` term that does not
        reduce, so a witness cannot compute the rival's value either. A refutation
        stated over two distinct probed points (the clause-2 branch ignores
        ``value``, so the rival's result must coincide at ``PyVal.str "a"`` and
        ``PyVal.str "b"`` while the spec pins each to its own JSON text) fails on
        BOTH sides at exit 1, because even the coincidence step needs the loop
        term to reduce;
      - the hypothesis-conditioned shape the opaque-carrier technique recommends
        (``example (h : implementation_displayForField … ≠ s) : ¬ problem_spec …``)
        DOES elaborate — but it elaborates against the FROZEN SOLUTION too
        (rival 0, gold 0), because the hypothesis does all the work and is stated
        over a name both files declare. That is ``witness-vacuous``, an
        inconclusive gate outcome, not a refutation.

    So the class is expressible and its rivals are genuinely rejected, but no
    witness shape tried here attributes that rejection to the spec — hence a
    recorded HOLE rather than a shipped case or a claim of vacuity. Recorded
    because a vacuous class says the battery is complete, while a hole says it
    is not.

    ONE MEASUREMENT THAT LOOKS LIKE A SPEC HOLE AND IS NOT, recorded so the next
    reader does not re-raise it: the DISCARDED-loop rival (``while true do i :=
    i + 1`` placed before the frozen clause-2 returns) VERIFIES at exit 0 under
    the frozen script. It is not a hole — it is definitionally the frozen impl. A
    standalone copy of that body closes against ``implementation_displayForField``
    by a bare ``rfl`` at function level AND pointwise (exit 0 both), i.e. the
    unused loop is erased and the term is gold. By attack C that rival is
    observably identical to gold on this carrier, so it is vacuous as a rival
    rather than admitted as a wrong one.

  * SERIALISER-INTERNAL BYTE ATTACKS — PARTLY EXPRESSIBLE, and now attacked
    (``rendered-text-outer-delimiters-stripped``). FOUR nagini rivals sit in this
    class, not two: ``wrong-delimiter-single-quote`` (``"`` vs ``'``),
    ``single-token-no-brackets`` (the ``[ ]`` brackets), ``delimiter-only-escape``
    (escapes only the delimiter, leaving the escape character raw), and
    ``hex-digits-reversed`` (the six-code-point form's digit order). Each perturbs
    a specific byte of the recursive interchange serialisation.

    AUDIT NOTE. The previous revision recorded the WHOLE class as NOT MODELED and
    called that "DEMONSTRATED rather than asserted": any impl altering those bytes
    "would have to replace ``jsonSerialize`` itself", and substituting a concrete
    ``def jsonSerialize`` for the ``opaque`` one is indeed rejected by the scope
    check with ``spec view differs (same_spec failed)``, so the class was said to
    be "closed by ``variant_scope``, not merely unattempted". The substitution
    measurement REPRODUCES — but the inference from it was wrong, and wrong in the
    direction that overstates an omission. Altering the rendered text does NOT
    require replacing the callee: an impl can leave ``jsonSerialize`` untouched and
    POST-PROCESS the ``String`` it returns, which is ordinary code inside the
    ``-- impl-start``/``-- impl-end`` region. Two such rivals were written and both
    pass ``variant_scope.variant_problems`` clean (=[]): one rewriting the
    interchange delimiter in the result text to the host-language quote
    (``s.replace "\"" "'"``), one stripping the result text's outer two code points
    (``(s.drop 1).dropRight 1``). So the class was closed by an argument about the
    callee's DEFINITION, not by the scope checker, and what the scope checker
    actually closes is only the substitution route.

    The bracket/delimiter shape is therefore LANDED below rather than recorded as
    inexpressible. Its witness needs no counterfactual: it conditions on the
    serialiser's REAL text at the probed point (``jsonSerialize (PyVal.str "a") =
    Except.ok "\"a\""``, i.e. ``json.dumps('a') == '"a"'``, and the composite point
    ``["a", "b"]``), which is a fact about the unchanged callee rather than an
    assumption about how two renderings compare, and the refutation then COMPUTES.

    TWO of the four remain genuinely out of reach, and for a different reason than
    the bullet used to give — not that no impl can alter the bytes, but that these
    two rivals' distinguishing INPUTS cannot be exhibited. ``delimiter-only-escape``
    and ``hex-digits-reversed`` differ from gold only at a value whose token carries
    the escape character, a control position, or a non-ASCII code point; a witness
    would have to state the serialiser's real text at such a value, and the
    serialiser is ``opaque``, so that text is available only by an assumption that
    the consistency probe cannot check against the real operation. Conditioning on
    it would be exactly the satisfiable-but-false hypothesis the
    ``null-drops-placeholder`` AUDIT NOTE records as a defect. Recorded as a KNOWN
    HOLE in the witness lane, not as vacuity.

    What all four share — "the wrong text is displayed for a present, non-empty
    value" — is clause 2, attacked by ``no-json-render`` (the pre-fix defect:
    generic instead of JSON), by ``partial-domain-scalar-only`` (correct at a
    scalar, wrong at a composite), by ``error-fallback-wrap`` (a perturbation on
    the serialisation-failure arm), and now by
    ``rendered-text-outer-delimiters-stripped`` (the serialiser IS selected and its
    text is then perturbed — a route no other case takes).

  * PARTIAL DOMAIN — EXPRESSIBLE, and now attacked (``partial-domain-scalar-
    only``). AUDIT NOTE: the first port folded nagini's
    ``partial-domain-drop-separator`` into the bullet above and dropped it, on
    the reasoning that the ``", "`` separator is a byte inside the opaque
    serialiser. Half right: the BYTE is indeed inexpressible, but what makes
    that nagini case its own class is not the byte, it is the SHAPE — an impl
    that is CORRECT on part of the input domain and wrong on the rest, so a
    battery probing only one representative per clause can miss it. That shape
    is fully expressible on this carrier by branching clause 2 on the value's
    own constructor: JSON-render a bare scalar, generic-render every other
    present, non-empty value. Such a rival agrees with the frozen impl at
    ``PyVal.str "a"`` — the exact point ``no-json-render`` is probed at — and
    diverges only at a present, non-empty COMPOSITE. It is landed below, and its
    witness is stated at ``PyVal.list [...]`` for that reason.

  * UNGROUNDED-ORACLE ECHO — N/A in the harmful direction. ``result`` is pinned by
    an explicit ``match`` over the actual callee results, not equated to a hidden
    answer key an impl could echo; the two callees appear IDENTICALLY in the spec
    and the impl, so the proof consumes no property of them.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen ``Id.run
do`` form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet that instantiates the
frozen spec predicate at one concrete input, extracts the relevant clause, and
derives ``False``. Because BOTH renderers are ``opaque``, a literal input does
not always compute to a value, so a witness may CONDITION ON THE CARRIER: it
assumes just enough about the opaque callee at the probed input to separate the
rival from gold (e.g. "when the JSON text differs from the generic rendering …").
Each witness's head hypotheses are kept jointly satisfiable — every assumption is
about a DISTINCT opaque term, never two about the same term — so the gate's
consistency probe cannot derive ``False`` from them (a contradictory witness is
``witness-inconsistent`` and forces MALFORMED-TESTS).

A SATISFIABLE hypothesis is not automatically a TRUE one, and the consistency
probe cannot tell the difference: the probe asks only whether the opaque
signature admits the assumption, and an opaque term admits nearly anything. So
where a refutation can be made to COMPUTE instead, it is — a witness that
assumes nothing cannot be refuting the rival under a counterfactual about an
unchanged callee. ``null-drops-placeholder`` is stated that way (see its AUDIT
NOTE for the case where this mattered: its predecessor's hypothesis was
satisfiable on the signature and false of the operation being modeled, which
made the rival observably equal to gold at the probed point). The remaining
conditional witnesses assume only that two renderings of the SAME value differ
(or, on the ``.error`` arm, that the serialiser fails at the tuple-keyed value),
which is the distinction the modeled decision exists to make. Each such witness
was independently confirmed to track its CLAIM rather than merely to fail: for
every reject case, the FLIPPED claim — asserting the spec HOLDS at the probed
point, the exact opposite of the witness — builds at exit 0 against the frozen
solution and exit 1 against the rival, the mirror image of the witness's own
0/1. So the gold-side exit code carries information about what is claimed, and
none of these cases is a case whose error is the same whatever it asserts.

Each witness below was built BOTH ways with ``scripts/lean_verify.sh`` and its
consistency probe run: it ELABORATES against the rival (exit 0), FAILS on the
frozen solution (exit 1), and its binders admit no ``False`` (probe exit 1) — so
it discriminates rather than asserting a tautology from a phantom input.
Additionally, and not checked by the gate: the frozen impl's value at each
probed point was proven directly (e.g. ``implementation_displayForField
PyVal.null "?" = "?"`` by ``rfl``), confirming each gold-side failure is the spec
being SATISFIED there rather than a tactic or unfolding accident.

ADMISSIBILITY lane: PRESENT (``admiss-f2p-three-clauses``). The frozen
obligation carries no precondition — both binders are universally quantified on
a total carrier — so the nagini sibling's ``admissibility-f2p-string-node``,
which established ``Requires(Acc(j_pred(node), 1/2))`` for a real F2P value by a
self-call, has no permission-shaped counterpart here. Its underlying question
does port, and "the frozen obligation has no precondition" is NOT a reason to
drop the lane: the analogue on a total carrier is the obligation being
UNSATISFIABLE at exactly an F2P-shaped input, which would leave every uniqueness
rival still failing while the spec pinned an empty set of behaviours at the
points the differential checks exercise. The ported case discharges the spec
predicate at FOUR concrete points, each pinned to a concrete result value,
before closing the frozen obligation verbatim. See its comment block for the
three re-pinnings that FAIL, which is what shows it is not a tautology.

AUDIT NOTE on the COUNT. The previous revision discharged THREE points and
described them, here and in the case's own rationale, as "one per clause". That
was false, and falsely in the direction that overstates the lane: the three
points were clause 1, clause 2 on its ``.ok`` arm, and clause 2 on its ``.error``
arm — so TWO of the three were the same clause and CLAUSE 3 (present but empty)
was never discharged at all. The admissibility lane therefore attested to a
per-clause satisfiability it had not measured on the one input class the reject
lane reaches only through ``empty-through-placeholder``. The clause-3 point was
landed rather than the prose weakened: the four-point ``have`` builds at exit 0,
and re-pinning the new point to the placeholder text instead of the generic
rendering FAILS (exit 1), so the added conjunct tracks the value it names.

BINDER / POINT SPREAD. The obligation has two input binders, ``value`` and
``empty``. The reject witnesses move BOTH: ``value`` ranges over ``PyVal.str "a"``
(a present, JSON-serialisable scalar), ``PyVal.list [PyVal.str "a", PyVal.str
"b"]`` (a present, JSON-serialisable COMPOSITE), a tuple-keyed ``PyVal.dict`` (a
present value the serialiser rejects), ``PyVal.null`` (absent), and ``PyVal.dict
[]`` (a present but EMPTY container); ``empty`` ranges over ``"-"`` and ``"?"``.
All THREE clauses are attacked, and clause 2 on BOTH of its arms — the ``.ok``
arm (``no-json-render`` at a scalar and ``partial-domain-scalar-only`` at a
composite), the ``.error`` arm (``error-fallback-wrap``), clause 1
(``null-drops-placeholder``), and clause 3 (``empty-through-placeholder``). The
five reject witnesses probe five distinct input points.

The scalar/composite SPLIT inside clause 2 is deliberate and was added by audit,
not by the original port: with a single representative per clause, a rival that
JSON-renders scalars and generic-renders composites agrees with the frozen impl
at every probed point, so the battery would have attested to a clause-2 strength
it never measured on a composite. Both points are now probed independently.

AXIOM lane: EMPTY. The bundle declares two ``opaque`` callees but consumes no
``axiom`` (the proof is pure case analysis; the callees appear identically on
both sides). The axiom lane belongs to G-AX; this gate ignores it, and the nagini
``AXIOM_TESTS`` (also empty there) are dropped.
"""
from pathlib import Path

INSTANCE = "django__django-12308"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The gold impl (exactly the text strictly inside -- impl-start/-- impl-end).
# Every variant is a _swap of this whole block; the markers, signature, spec,
# pure helpers, the two opaque callees, and the theorem statement are never
# touched -> same_spec holds by construction and the rejection (or the verify)
# is attributable to the postcondition, not to a tampered spec.
# ---------------------------------------------------------------------------
_GOLD_IMPL = (
    "def implementation_displayForField (value : PyVal) (empty : String) : String := Id.run do\n"
    "  -- An absent value shows the placeholder.\n"
    "  if isNull value then\n"
    "    return empty\n"
    "  -- A present, non-empty value is rendered as JSON; if it cannot be represented\n"
    "  -- as JSON, fall back to the generic rendering.\n"
    "  if truthy value then\n"
    "    match jsonSerialize value with\n"
    "    | .ok s => return s\n"
    "    | .error _ => return genericDisplay value empty\n"
    "  -- A present but empty value uses the generic rendering.\n"
    "  return genericDisplay value empty\n"
)


# ===========================================================================
# (P1) POSITIVE CONTROL (soundness) — structurally DIFFERENT but CORRECT.
# The mutable `Id.run do` / early-return dispatch is re-expressed as a pure
# functional `if / else if / else` selecting the SAME renderer in every case,
# producing the identical value on every input. All three clauses of
# problem_spec_displayForField still hold. The frozen proof body closes it
# verbatim (case analysis on isNull / truthy / the serialisation result reduces
# identically for the pure form) — no new lemma, no axiom, no sorry. If a
# faithful correct impl of this shape cannot verify the spec is SPEC-TOO-STRONG.
# Ports nagini's positive controls (pos-serialize-reorder / pos-dsv-copyloop-
# reshape): a structurally-different-but-correct reshape of the modeled core.
#
# AUDIT NOTE on the STRENGTH of this positive. Measured, not assumed: stripping
# the `Id.run do` wrapper leaves a term the frozen impl is DEFINITIONALLY EQUAL
# to — a standalone copy of this body is closed against
# `implementation_displayForField` by a bare `rfl`, both pointwise and at
# function level (exit 0). So `Id.run`/`pure` on the identity monad are pure
# notation here and this reshape changes no reduction behaviour: it is an honest
# positive but a WEAK one, since the frozen proof script cannot tell it from
# gold. It is kept (a syntactic reshape is still the thing nagini's positives
# port to) and is JOINED by (P3) below, whose body `rfl` does NOT identify with
# the frozen impl, so a proof that reduces the two differently is actually
# required. Without (P3) the soundness lane would rest entirely on a
# definitional no-op.
# ===========================================================================
_pos = _swap(
    _BASE,
    _GOLD_IMPL,
    "def implementation_displayForField (value : PyVal) (empty : String) : String :=\n"
    "  -- pure functional dispatch: the same renderer is selected in every case as\n"
    "  -- the mutable form, so the produced text is identical on every input\n"
    "  if isNull value then empty\n"
    "  else if truthy value then\n"
    "    match jsonSerialize value with\n"
    "    | .ok s => s\n"
    "    | .error _ => genericDisplay value empty\n"
    "  else genericDisplay value empty\n",
)


# ===========================================================================
# (P3) POSITIVE CONTROL, NOT DEFINITIONALLY GOLD — the serialisation result is
# consumed through `Except.toOption` + `Option.getD` instead of a `match` on the
# two arms. Same value on every input: `.ok s` gives `some s |>.getD _ = s`, and
# `.error _` gives `none |>.getD (genericDisplay value empty)`. But the TERM is
# different in a way `rfl` does not see through — a standalone copy of this body
# is NOT closed against the frozen impl by `rfl` (exit 1, `Tactic 'rfl' failed`,
# where the (P1) reshape closes at exit 0). So this positive genuinely exercises
# the spec against an impl the frozen proof must reduce DIFFERENTLY, which is
# what a soundness control is for: it cannot pass merely because the checker
# cannot distinguish it from gold.
#
# The frozen `refine`/`simp_all`/`cases jsonSerialize value`/`rfl` script closes
# it because the case split on the serialisation result is exactly what turns
# `toOption.getD` into each arm's value. If a faithful correct impl of this shape
# could NOT be proven, the postcondition would be SPEC-TOO-STRONG — pinning one
# syntactic route to the result rather than the result itself.
# ===========================================================================
_pos_getd = _swap(
    _BASE,
    _GOLD_IMPL,
    "def implementation_displayForField (value : PyVal) (empty : String) : String :=\n"
    "  -- Same selection as the mutable form, but the serialisation result is\n"
    "  -- consumed through toOption/getD rather than matched arm by arm: the\n"
    "  -- success text if there is one, else the generic rendering.\n"
    "  if isNull value then empty\n"
    "  else if truthy value then\n"
    "    (jsonSerialize value).toOption.getD (genericDisplay value empty)\n"
    "  else genericDisplay value empty\n",
)


# ===========================================================================
# (R1) NO-JSON-RENDER — the pre-fix defect. A present value is sent straight to
# the generic renderer; the dedicated JSON rendering is never selected. This is
# the Solution_prepatch skeleton verbatim. Attacks CLAUSE 2 on the .ok arm.
# Ports nagini's central discriminator (wrong-delimiter-single-quote and the
# whole "present & encodable must render as interchange, not the host-language
# printout" family): here the wrong renderer is chosen wholesale rather than one
# delimiter byte being wrong, because the serialiser's bytes are opaque.
# ===========================================================================
_r_no_json = _swap(
    _BASE,
    _GOLD_IMPL,
    "def implementation_displayForField (value : PyVal) (empty : String) : String := Id.run do\n"
    "  if isNull value then\n"
    "    return empty\n"
    "  return genericDisplay value empty\n",
)

# ===========================================================================
# (R2) ERROR-FALLBACK-WRAP — on the serialisation-FAILURE arm the rival appends
# an extra delimiter to the generic rendering instead of returning it unchanged.
# Attacks CLAUSE 2 on the .error arm. Ports nagini's wrong-fallback-extra-wrap:
# the non-encodable fallback must pass the generic text through UNCHANGED; any
# added delimiter contradicts the clause.
# ===========================================================================
_r_wrap = _swap(
    _BASE,
    _GOLD_IMPL,
    "def implementation_displayForField (value : PyVal) (empty : String) : String := Id.run do\n"
    "  if isNull value then\n"
    "    return empty\n"
    "  if truthy value then\n"
    "    match jsonSerialize value with\n"
    "    | .ok s => return s\n"
    '    | .error _ => return genericDisplay value empty ++ "\'"\n'
    "  return genericDisplay value empty\n",
)

# ===========================================================================
# (R3) NULL-DROPS-PLACEHOLDER — the absent value yields the EMPTY STRING
# instead of the placeholder text. Attacks CLAUSE 1. This is the
# referentially-transparent analogue of nagini's frame-mutation rival, whose
# behavioural concern was that the not-present branch must yield the
# placeholder UNCHANGED; here the rival returns a different string for the
# absent input.
#
# AUDIT NOTE (why this rival and not the obvious one). The first port of this
# case routed the absent value through the generic renderer
# (``return genericDisplay value empty``) and called that "a different string
# for the absent input". On the REAL carrier that is not a different string:
# the generic renderer's own first test is the absent test, and it returns the
# placeholder for an absent value — the bundle's own conformance replica of it
# opens with ``if value is None: return empty``. So that rival is
# OBSERVABLY EQUAL to the frozen impl at the only input it was probed at, and
# its rejection attested to the frozen proof script's tuning (the ``rfl`` leg
# no longer reduced), not to the spec. Its witness had to ASSUME
# ``genericDisplay PyVal.null "?" ≠ "?"`` — a hypothesis the opaque signature
# leaves satisfiable, so the consistency probe could not refute it, but one
# that is FALSE of the operation being modeled. The witness therefore refuted
# the rival only under a counterfactual about an unchanged callee. Replaced
# with a rival that is wrong on the real carrier: returning "" for the absent
# value drops the placeholder outright, which no reading of the generic
# renderer produces, and its witness needs NO hypothesis at all (it computes,
# so there is nothing left to be counterfactual about).
# ===========================================================================
_r_null = _swap(
    _BASE,
    _GOLD_IMPL,
    "def implementation_displayForField (value : PyVal) (empty : String) : String := Id.run do\n"
    "  if isNull value then\n"
    '    return ""\n'
    "  if truthy value then\n"
    "    match jsonSerialize value with\n"
    "    | .ok s => return s\n"
    "    | .error _ => return genericDisplay value empty\n"
    "  return genericDisplay value empty\n",
)

# ===========================================================================
# (R4) EMPTY-THROUGH-PLACEHOLDER — the presence test is written as a
# TRUTHINESS test rather than an absence test, so a value that is present but
# empty is treated as absent and shows the placeholder instead of its generic
# rendering. Attacks CLAUSE 3, which no other case in this battery reaches.
# ===========================================================================
_r_empty = _swap(
    _BASE,
    _GOLD_IMPL,
    "def implementation_displayForField (value : PyVal) (empty : String) : String := Id.run do\n"
    "  if !truthy value then\n"
    "    return empty\n"
    "  match jsonSerialize value with\n"
    "  | .ok s => return s\n"
    "  | .error _ => return genericDisplay value empty\n",
)


# ===========================================================================
# (R5) PARTIAL-DOMAIN-SCALAR-ONLY — clause 2 is honoured only for a bare scalar.
# A present, non-empty COMPOSITE (a list or a mapping) is sent to the generic
# renderer even though the serialiser succeeds on it. Attacks CLAUSE 2 on the
# .ok arm at a COMPOSITE, the point no other case reaches.
#
# This is the ported shape of nagini's ``partial-domain-drop-separator``: an
# impl CORRECT on part of the input domain and wrong on the rest. It agrees with
# the frozen impl at ``PyVal.str "a"`` — the exact point ``no-json-render`` is
# probed at — and diverges only at a present, non-empty composite, so it is the
# rival that would survive a battery carrying one representative per clause.
# Measured (audit): its witness at ``PyVal.list ["a","b"]`` elaborates against
# this rival (exit 0) and fails on the frozen solution (exit 1), while the
# frozen impl's value at that same point is the serialiser's text, not the
# generic rendering (``... = genericDisplay (PyVal.list [...]) "-"`` closes by
# ``rfl`` against THIS rival at exit 0 and fails on gold at exit 1). So the
# divergence is observable on this carrier, not a reshape.
# ===========================================================================
_r_partial = _swap(
    _BASE,
    _GOLD_IMPL,
    "def implementation_displayForField (value : PyVal) (empty : String) : String := Id.run do\n"
    "  if isNull value then\n"
    "    return empty\n"
    "  if truthy value then\n"
    "    match value with\n"
    "    | .str _ =>\n"
    "      match jsonSerialize value with\n"
    "      | .ok s => return s\n"
    "      | .error _ => return genericDisplay value empty\n"
    "    | _ => return genericDisplay value empty\n"
    "  return genericDisplay value empty\n",
)


# ===========================================================================
# (R6) RENDERED-TEXT-OUTER-DELIMITERS-STRIPPED — the serialiser IS selected for a
# present, non-empty value, but its result TEXT is then perturbed: the outer two
# code points are dropped before the text is displayed. Attacks CLAUSE 2 on the
# .ok arm through a route no other case takes — every other clause-2 rival gets
# the wrong text by choosing the wrong RENDERER, this one chooses the right
# renderer and corrupts what it produced.
#
# This is the ported shape of nagini's ``single-token-no-brackets`` (and of
# ``wrong-delimiter-single-quote``, which perturbs the same rendered text one
# code point at a time): for the composite value the JSON text is ``["a", "b"]``
# and the rival displays ``"a", "b"`` — the bracketless form, exactly the nagini
# rival's rendering. Landed by AUDIT: the docstring bullet above recorded the
# whole byte-attack class as inexpressible on the reasoning that altering those
# bytes requires replacing the ``opaque`` callee (which same_spec does reject).
# It does not: post-processing the callee's returned ``String`` is ordinary impl
# -region code, and this variant passes variant_problems clean (=[]).
#
# Its witness conditions on the serialiser's REAL text at the probed point
# (``json.dumps('a') == '"a"'``), which is a fact about the UNCHANGED callee, not
# an assumption about how two renderings compare — so the refutation computes by
# ``decide`` from there and nothing is left to be counterfactual about.
# ===========================================================================
_r_strip = _swap(
    _BASE,
    _GOLD_IMPL,
    "def implementation_displayForField (value : PyVal) (empty : String) : String := Id.run do\n"
    "  if isNull value then\n"
    "    return empty\n"
    "  if truthy value then\n"
    "    match jsonSerialize value with\n"
    "    | .ok s => return (s.drop 1).dropRight 1\n"
    "    | .error _ => return genericDisplay value empty\n"
    "  return genericDisplay value empty\n",
)


# Tuple-keyed dict: a present, non-empty value the JSON serialiser rejects (the
# F2P's {('a','b'): 'c'} case). Used at the .error arm.
_D = 'PyVal.dict [(PyVal.tuple [PyVal.str "a", PyVal.str "b"], PyVal.str "c")]'

# A present, non-empty COMPOSITE the serialiser SUCCEEDS on — the clause-2 .ok
# point a scalar-only rival gets wrong while agreeing with gold at PyVal.str.
_L = 'PyVal.list [PyVal.str "a", PyVal.str "b"]'


# ===========================================================================
# (P2) ADMISSIBILITY — the obligation is SATISFIABLE at the concrete input
# points the differential checks exercise, one per clause.
#
# The frozen obligation carries no precondition hypothesis (`value` and `empty`
# are universally quantified over a total carrier), so the PRECOND-TOO-STRONG
# direction cannot be tested by weakening a `Requires`. Its analogue here is the
# obligation being UNSATISFIABLE at exactly an F2P-shaped input: a spec whose
# three clauses overlapped, or whose clause-2 `match` could not be met by any
# string, would still be provable of nothing while every uniqueness rival kept
# failing — the battery would read SOUND with the spec pinning an empty set of
# behaviours at the points that matter.
#
# The probe discharges `problem_spec_displayForField` at FOUR concrete points,
# covering all THREE clauses and both arms of clause 2, each pinned to a
# CONCRETE result value: the absent value to the placeholder text (clause 1), the
# present serialisable scalar to the JSON text (clause 2, .ok arm), the
# tuple-keyed dict to the generic rendering (clause 2, .error arm), and the EMPTY
# mapping to the generic rendering (clause 3). It is stated as a `have` and the
# frozen tactic script then closes the frozen obligation VERBATIM below it (the
# anchor `intro value empty` is re-appended), so the case only ADDS an
# obligation.
#
# AUDIT NOTE on the fourth point. The first version of this case carried only the
# first three and called them "one per clause" — but two of the three were
# clause 2 (its .ok and .error arms) and CLAUSE 3 was never discharged, so the
# lane claimed a per-clause satisfiability it had not measured. The clause-3
# point was added rather than the claim softened, since it is the one input class
# only `empty-through-placeholder` otherwise reaches.
#
# NOT A TAUTOLOGY, and this was checked rather than asserted. The probe names
# concrete result values, never `implementation_displayForField` applied, so it
# cannot reduce to a definitional identity. Re-pinning the absent point to ""
# instead of the placeholder FAILS to build (exit 1, `rfl` failed: "" is not
# definitionally equal to "-"), re-pinning the clause-2 point to the generic
# rendering rather than the JSON text FAILS as well (exit 1, unsolved goal under
# the hypothesis that the two renderings differ), and re-pinning the new clause-3
# point to the placeholder text rather than the generic rendering FAILS (exit 1).
# So the probe's success tracks the result values it names.
#
# One control worth recording, because it shows what the concreteness buys:
# re-pinning a point to `implementation_displayForField` APPLIED does build (exit
# 0) — it is then a definitional identity that would hold of any impl whatsoever,
# which is exactly the tautology this case's value-level pinning avoids.
#
# Ports nagini's `admissibility-f2p-string-node`, whose self-call established
# `Requires(Acc(j_pred(node), 1/2))` for a real F2P value; the permission
# precondition has no counterpart on an immutable carrier, but the
# satisfiable-at-a-normal-input question does.
# ===========================================================================
_PROOF_ANCHOR = "  intro value empty"

_ADM_HAVE = (
    '  -- ADMISSIBILITY at the F2P-shaped input points. Before the general\n'
    '  -- obligation is closed, the spec predicate is discharged at four\n'
    '  -- concrete inputs covering all THREE clauses (and both arms of clause\n'
    '  -- 2), each pinned to a CONCRETE result value rather than to\n'
    '  -- `implementation_displayForField` applied -- so this is a\n'
    '  -- satisfiability claim about the SPEC, not a definitional identity that\n'
    '  -- would hold of any result whatsoever.\n'
    '  have _f2p : ∀ (jsonText : String),\n'
    '      jsonSerialize (PyVal.str "a") = Except.ok jsonText →\n'
    f'      jsonSerialize ({_D}) = Except.error () →\n'
    '      problem_spec_displayForField (PyVal.str "a") "-" jsonText\n'
    '        ∧ problem_spec_displayForField PyVal.null "-" "-"\n'
    f'        ∧ problem_spec_displayForField ({_D}) "-"\n'
    f'            (genericDisplay ({_D}) "-")\n'
    '        ∧ problem_spec_displayForField (PyVal.dict []) "-"\n'
    '            (genericDisplay (PyVal.dict []) "-") := by\n'
    '    intro jsonText hok herr\n'
    '    refine ⟨⟨?_, ?_, ?_⟩, ⟨?_, ?_, ?_⟩, ⟨?_, ?_, ?_⟩, ⟨?_, ?_, ?_⟩⟩\n'
    '    · intro h; exact absurd h (by decide)\n'
    '    · intro _ _; rw [hok]\n'
    '    · intro _ h; exact absurd h (by decide)\n'
    '    · intro _; rfl\n'
    '    · intro h; exact absurd h (by decide)\n'
    '    · intro h; exact absurd h (by decide)\n'
    '    · intro h; exact absurd h (by decide)\n'
    '    · intro _ _; rw [herr]\n'
    '    · intro _ h; exact absurd h (by decide)\n'
    '    · intro h; exact absurd h (by decide)\n'
    '    · intro _ h; exact absurd h (by decide)\n'
    '    · intro _ _; rfl\n'
)

_adm = _swap(_BASE, _PROOF_ANCHOR, _ADM_HAVE + _PROOF_ANCHOR)


_W_NO_JSON = (
    'example (s : String)\n'
    '    (h1 : jsonSerialize (PyVal.str "a") = Except.ok s)\n'
    '    (h2 : genericDisplay (PyVal.str "a") "-" ≠ s) :\n'
    '    ¬ problem_spec_displayForField (PyVal.str "a") "-"\n'
    '        (implementation_displayForField (PyVal.str "a") "-") := by\n'
    '  intro h\n'
    '  have hb := h.2.1 (by decide) (by decide)\n'
    '  rw [h1] at hb\n'
    '  simp only [implementation_displayForField, Id.run, isNull] at hb\n'
    '  exact h2 hb\n'
)

# CLAUSE 2, .ok arm, at a present non-empty COMPOSITE. Same shape as _W_NO_JSON
# but at a list rather than a scalar: this is the point that separates a
# scalar-only rival from the frozen impl, since both agree at PyVal.str "a".
# Conditions only on two renderings of the SAME value differing, which is the
# distinction the modeled decision exists to make; the two hypotheses are about
# DISTINCT opaque terms, so they stay jointly satisfiable (probe exit 1).
_W_PARTIAL = (
    f'example (s : String)\n'
    f'    (h1 : jsonSerialize ({_L}) = Except.ok s)\n'
    f'    (h2 : genericDisplay ({_L}) "-" ≠ s) :\n'
    f'    ¬ problem_spec_displayForField ({_L}) "-"\n'
    f'        (implementation_displayForField ({_L}) "-") := by\n'
    '  intro h\n'
    '  have hb := h.2.1 (by decide) (by decide)\n'
    '  rw [h1] at hb\n'
    '  simp only [implementation_displayForField, Id.run, isNull] at hb\n'
    '  exact h2 hb\n'
)

_W_WRAP = (
    f'example\n'
    f'    (h1 : jsonSerialize ({_D}) = Except.error ()) :\n'
    f'    ¬ problem_spec_displayForField ({_D}) "-"\n'
    f'        (implementation_displayForField ({_D}) "-") := by\n'
    '  intro h\n'
    '  have hb := h.2.1 (by decide) (by decide)\n'
    f'  have hval : implementation_displayForField ({_D}) "-"\n'
    f'      = genericDisplay ({_D}) "-" ++ "\'" := by\n'
    '    simp only [implementation_displayForField, Id.run, isNull, truthy, bind, pure]\n'
    '    rw [h1]; rfl\n'
    '  rw [hval, h1] at hb\n'
    '  simp only [] at hb\n'
    '  have hlen := congrArg String.length hb\n'
    '  rw [String.length_append] at hlen\n'
    '  have hq : ("\'").length = 1 := by decide\n'
    '  rw [hq] at hlen\n'
    '  omega\n'
)

# CLAUSE 1 at the absent input. Binds NOTHING: the rival's result at
# PyVal.null is the literal "", and the clause demands the placeholder "?", so
# the refutation COMPUTES and needs no assumption about either opaque callee.
# (That is what makes it a strictly better discriminator than a conditional
# refutation whose hypothesis is satisfiable-but-false of the modeled operation;
# with no binders there is no consistency probe to run and nothing to assume.)
_W_NULL = (
    'example :\n'
    '    ¬ problem_spec_displayForField PyVal.null "?"\n'
    '        (implementation_displayForField PyVal.null "?") := by\n'
    '  intro h\n'
    '  have ha := h.1 (by decide)\n'
    '  simp only [implementation_displayForField, Id.run, isNull] at ha\n'
    '  exact absurd ha (by decide)\n'
)

# CLAUSE 3 at a present-but-empty input (the empty mapping). The clause pins the
# result to the generic rendering; the rival returns the placeholder. Conditions
# on the generic rendering of the empty mapping differing from the placeholder —
# true of the real operation (it renders an empty mapping as its own text, not as
# the placeholder, since the placeholder is reserved for the ABSENT value) and
# satisfiable on the opaque signature.
_W_EMPTY = (
    'example\n'
    '    (h2 : genericDisplay (PyVal.dict []) "-" ≠ "-") :\n'
    '    ¬ problem_spec_displayForField (PyVal.dict []) "-"\n'
    '        (implementation_displayForField (PyVal.dict []) "-") := by\n'
    '  intro h\n'
    '  have hc := h.2.2 (by decide) (by decide)\n'
    '  simp only [implementation_displayForField, Id.run, isNull, truthy] at hc\n'
    '  exact h2 hc.symm\n'
)


# CLAUSE 2, .ok arm, at a present non-empty COMPOSITE whose JSON text is named
# CONCRETELY. Unlike _W_NO_JSON / _W_PARTIAL this binds no `s` and assumes
# nothing about how the two renderings COMPARE: it states the serialiser's own
# real text at the probed value (`json.dumps(['a','b']) == '["a", "b"]'`), which
# is a fact about the unchanged callee, and the clause then pins the result to
# that text while the rival's is it minus its two outer code points. From there
# the contradiction is decided on string literals, so the refutation COMPUTES.
# The single hypothesis is about one opaque term, so it stays satisfiable
# (probe exit 1).
_W_STRIP = (
    f'example\n'
    f'    (h1 : jsonSerialize ({_L}) = Except.ok "[\\"a\\", \\"b\\"]") :\n'
    f'    ¬ problem_spec_displayForField ({_L}) "-"\n'
    f'        (implementation_displayForField ({_L}) "-") := by\n'
    '  intro h\n'
    '  have hb := h.2.1 (by decide) (by decide)\n'
    '  rw [h1] at hb\n'
    '  simp only [implementation_displayForField, Id.run, isNull, truthy] at hb\n'
    '  rw [h1] at hb\n'
    '  exact absurd hb (by decide)\n'
)


SPEC_TESTS = [
    {
        "id": "pos-control-pure-dispatch",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos,
        "rationale": (
            "A structurally-different but CORRECT impl: the mutable Id.run do / "
            "early-return dispatch is re-expressed as a pure functional "
            "if / else-if / else that selects the SAME renderer in every case, so "
            "the produced text is identical on every input and all three clauses "
            "of problem_spec_displayForField still hold. The frozen proof body "
            "closes it verbatim (the case analysis on isNull / truthy / the "
            "serialisation result reduces identically for the pure form); no new "
            "lemma, no axiom, no sorry. If it cannot verify, the postcondition is "
            "SPEC-TOO-STRONG. Ports nagini's structurally-different-correct "
            "positive controls to the single modeled core."
        ),
    },
    {
        "id": "pos-control-getd-consume",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_getd,
        "rationale": (
            "A CORRECT reshape that is NOT definitionally equal to the frozen "
            "impl: the serialisation result is consumed through Except.toOption "
            "and Option.getD instead of a match on the .ok / .error arms. It "
            "produces the same text on every input (`.ok s` -> `some s |>.getD _ "
            "= s`; `.error _` -> `none |>.getD (genericDisplay value empty)`), so "
            "all three clauses still hold, and the frozen proof body closes it "
            "verbatim because its `cases jsonSerialize value` split is exactly "
            "what reduces toOption/getD to each arm's value. This case exists "
            "because the other soundness positive was MEASURED to be a "
            "definitional no-op — a standalone copy of its body is closed against "
            "implementation_displayForField by a bare `rfl` (exit 0), so the "
            "checker cannot distinguish it from gold — whereas the same `rfl` on "
            "this body FAILS (exit 1). A positive the verifier must actually "
            "reduce differently is what makes the SPEC-TOO-STRONG direction "
            "testable: if this faithful impl could not be proven, the "
            "postcondition would be pinning one syntactic route to the result "
            "rather than the result itself."
        ),
    },
    {
        "id": "admiss-f2p-three-clauses",
        "kind": "admissibility",
        "expect": "verify",
        "module": _adm,
        "rationale": (
            "The obligation is SATISFIABLE at the concrete input points the "
            "differential checks exercise. `value` and `empty` are universally "
            "quantified with NO precondition hypothesis on a total carrier, so "
            "PRECOND-TOO-STRONG cannot be tested by weakening a guard; its "
            "analogue is the obligation being unsatisfiable at exactly an "
            "F2P-shaped input, which would leave every uniqueness rival still "
            "failing while the spec pinned an empty set of behaviours at the "
            "points that matter. The probe discharges "
            "problem_spec_displayForField at FOUR points covering all three "
            "clauses and both arms of clause 2 — the absent value pinned to the "
            "placeholder text (clause 1), a present serialisable scalar pinned "
            "to the JSON text (clause 2 .ok arm), a value the serialiser rejects "
            "pinned to the generic rendering (clause 2 .error arm), and the "
            "present-but-EMPTY mapping pinned to the generic rendering "
            "(clause 3) — as a `have`, after which the frozen obligation is "
            "closed VERBATIM (the `intro value empty` anchor is re-appended, so "
            "the case only ADDS an obligation). The clause-3 point was added by "
            "audit: the first three points were described as \"one per clause\" "
            "but two of them were clause 2, so clause 3's satisfiability was "
            "claimed and never measured. It is not a definitional identity: it "
            "names concrete result values and never mentions "
            "implementation_displayForField applied, and re-pinning the absent "
            "point to \"\", the clause-2 point to the generic rendering, or the "
            "clause-3 point to the placeholder text each FAIL to build. Ports "
            "nagini's admissibility-f2p-string-node, "
            "whose permission precondition has no counterpart on an immutable "
            "carrier but whose satisfiable-at-a-normal-input question does."
        ),
    },
    {
        "id": "no-json-render",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _r_no_json,
        "rationale": (
            "REJECT from clause 2 (present & non-empty) on the .ok arm: a present, "
            "non-empty value is sent straight to genericDisplay, so whenever the "
            "JSON text differs from the generic rendering the result is not the "
            "match's .ok branch. Attacks the `value` binder at a present, "
            "JSON-serialisable scalar (PyVal.str \"a\")."
        ),
        "refinement": (
            "This IS the pre-fix defect (Solution_prepatch: after the absent "
            "check, `return genericDisplay value empty`): a JSON-valued field's "
            "value was never given its dedicated JSON rendering and fell through "
            "to the generic renderer, so a JSON-representable value was displayed "
            "by the generic renderer (e.g. as a host-language object printout) "
            "instead of as JSON. Its faithful real patch is the unpatched code, "
            "which is exactly what test_json_display_for_field forbids (its four "
            "subtests expect the JSON text '\"a\"', '[\"a\", \"b\"]', "
            "'{\"a\": {\"b\": \"c\"}}'). It does NOT resolve, so a verifying rival "
            "here would be a true verify-does-not-imply-resolve break."
        ),
        "witness": _W_NO_JSON,
    },
    {
        "id": "partial-domain-scalar-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _r_partial,
        "rationale": (
            "REJECT from clause 2 (present & non-empty) on the .ok arm at a "
            "COMPOSITE value: the rival honours the clause only for a bare "
            "scalar, sending every other present, non-empty value to "
            "genericDisplay even though the serialiser succeeds on it. Attacks "
            "the `value` binder at PyVal.list [\"a\", \"b\"] — a present, "
            "JSON-serialisable composite, which is a FIFTH input point and the "
            "one every other case leaves unprobed. This is the PARTIAL-DOMAIN "
            "shape: the rival is CORRECT at PyVal.str \"a\", the exact point "
            "no-json-render is probed at, and wrong only at a composite, so a "
            "battery carrying one representative per clause would not "
            "distinguish it from gold at any point it checks."
        ),
        "refinement": (
            "A faithful real patch that gave the dedicated JSON rendering only "
            "to a scalar value and left every composite on the generic "
            "fall-through would display a list or a mapping by the generic "
            "renderer: display_for_field(['a', 'b'], JSONField(), empty_value) "
            "would give the generic rendering rather than the JSON text, and "
            "likewise for {'a': {'b': 'c'}}. That contradicts three of "
            "test_json_display_for_field's four subtests (the two composite "
            "expectations '[\"a\", \"b\"]' and '{\"a\": {\"b\": \"c\"}}', while "
            "the scalar subtest '\"a\"' would still pass — which is exactly what "
            "makes it a PARTIAL-domain rival rather than the pre-fix defect). It "
            "does NOT resolve. Ports nagini's partial-domain-drop-separator, "
            "whose separator byte is inexpressible here but whose "
            "correct-on-part-of-the-domain SHAPE is not."
        ),
        "witness": _W_PARTIAL,
    },
    {
        "id": "rendered-text-outer-delimiters-stripped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _r_strip,
        "rationale": (
            "REJECT from clause 2 (present & non-empty) on the .ok arm, through a "
            "route no other case takes: the rival SELECTS the JSON rendering "
            "correctly and then corrupts the text it produced, dropping its outer "
            "two code points before displaying it. Every other clause-2 rival "
            "gets the wrong text by choosing the wrong RENDERER; this one chooses "
            "the right renderer and perturbs its RESULT, so it is the only case "
            "that attacks the identity of the displayed text against a "
            "correctly-dispatched serialisation. Attacks the `value` binder at "
            "PyVal.list [\"a\", \"b\"], where the clause pins the result to the "
            "serialiser's own text and the rival's is that text minus its "
            "brackets."
        ),
        "refinement": (
            "A faithful real patch that handed the value to the JSON preparation "
            "step and then trimmed the first and last characters off the returned "
            "text would display a composite without its surrounding structure: "
            "display_for_field(['a', 'b'], JSONField(), empty_value) would give "
            "'\"a\", \"b\"' rather than the expected '[\"a\", \"b\"]', and "
            "{'a': {'b': 'c'}} would give '\"a\": {\"b\": \"c\"}' rather than "
            "'{\"a\": {\"b\": \"c\"}}'; the scalar 'a' would give 'a' rather than "
            "'\"a\"'. That contradicts three of test_json_display_for_field's four "
            "subtests. It does NOT resolve. Ports nagini's "
            "single-token-no-brackets (and the rendered-text half of "
            "wrong-delimiter-single-quote): the byte is not a literal in this "
            "bundle, but the perturbation of the SERIALISED TEXT is expressible "
            "without touching the opaque callee, by post-processing its result."
        ),
        "witness": _W_STRIP,
    },
    {
        "id": "error-fallback-wrap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _r_wrap,
        "rationale": (
            "REJECT from clause 2 (present & non-empty) on the .error arm: when "
            "the serialiser fails, the fallback must return genericDisplay value "
            "empty UNCHANGED, but the rival appends an extra delimiter, so the "
            "result is one character longer than the clause demands. Attacks the "
            "`value` binder at a present value the serialiser rejects "
            "(a tuple-keyed dict) — the arm the no-json-render rival never reaches."
        ),
        "refinement": (
            "A faithful real patch that wrapped the serialisation-failure fallback "
            "in an extra delimiter pair (rather than returning the generic "
            "rendering as-is) would render the F2P's tuple-keyed dict "
            "{('a', 'b'): 'c'} with spurious outer quotes, contradicting the F2P "
            "expected \"{('a', 'b'): 'c'}\" (no added delimiter). It does NOT "
            "resolve. Ports nagini's wrong-fallback-extra-wrap."
        ),
        "witness": _W_WRAP,
    },
    {
        "id": "null-drops-placeholder",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _r_null,
        "rationale": (
            "REJECT from clause 1 (absent): an absent value must yield the "
            "placeholder text `empty`, but the rival returns the empty string, so "
            "the placeholder is dropped outright. Attacks the `value` binder at "
            "PyVal.null and moves the `empty` binder to \"?\" — the only reject "
            "case to touch clause 1. The witness COMPUTES the contradiction (\"\" "
            "vs \"?\") and assumes nothing about either opaque callee, so the "
            "refutation does not rest on a hypothesis about an unchanged "
            "operation."
        ),
        "refinement": (
            "A faithful real patch that returned the empty string for an absent "
            "value instead of the configured placeholder would make "
            "display_for_field(None, JSONField(), empty_value) return '' rather "
            "than empty_value, so test_null_display_for_field (which asserts the "
            "placeholder is returned) FAILS. It does NOT resolve. This is the "
            "referentially-transparent analogue of nagini's frame-mutation rival, "
            "whose concern was that the not-present branch must yield the "
            "placeholder unchanged."
        ),
        "witness": _W_NULL,
    },
    {
        "id": "empty-through-placeholder",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _r_empty,
        "rationale": (
            "REJECT from clause 3 (present & empty), which no other case in this "
            "battery reaches: the rival collapses the absence test into the "
            "truthiness test, so a present-but-empty value is treated as absent "
            "and shows the placeholder instead of its generic rendering. Attacks "
            "the `value` binder at a present, empty container (the empty mapping) "
            "— a fourth input point, in the one input class the other three "
            "rivals leave unprobed."
        ),
        "refinement": (
            "A faithful real patch that tested the value's truthiness where the "
            "cascade tests absence would return the placeholder for every "
            "present-but-empty value: display_for_field({}, JSONField(), "
            "empty_value) would give the placeholder instead of the empty "
            "mapping's own rendering, and likewise for '' / 0 / False. The "
            "present-but-empty value's rendering is fixed by the pre-existing "
            "final fall-through of the cascade, which both the pre- and post-fix "
            "code reach, so this rival breaks behaviour the change was required "
            "to preserve. It does NOT resolve."
        ),
        "witness": _W_EMPTY,
    },
]

# No AXIOM lane: the bundle consumes no `axiom` (the two opaque callees appear
# identically in the spec and the impl, so the proof needs no contract for
# them). The nagini AXIOM_TESTS were also empty; dropped.
AXIOM_TESTS = []
