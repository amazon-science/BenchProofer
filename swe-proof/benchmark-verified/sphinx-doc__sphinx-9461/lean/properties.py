"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-9461 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, where a case legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_propertyPrefix`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (one behavior over two boolean toggles):

  propertyPrefix (isAbstract isClassLevel : Bool) : String
      result = the present modifier words joined by single spaces, with a single
      trailing space, in a fixed order: the "abstract" word first (iff the
      abstract toggle is set), then the "class-level" word (iff that toggle is
      set), then the base word, which is always present and always last.

  The load-bearing clause is the exact word SET, ORDER and JOIN FORMAT as a
  function of the two toggles:
      result = String.intercalate " " (prefixWords isAbstract isClassLevel) ++ " "
  with prefixWords = (abstract?) ++ (class?) ++ [base]. It decomposes into three
  independently attackable components:
      (i)   presence — each toggle controls its own word, in BOTH directions:
            the word appears when the toggle is set and is ABSENT when it is not;
      (ii)  order — abstract word, then class-level word, then base word last;
      (iii) format — single-space join plus exactly one trailing space.
  The class-level word is the NEW modifier, so (i) on that toggle is the
  discriminating behavior; but (i) is a two-sided claim, and a rendering that
  emits the class-level word REGARDLESS of its toggle satisfies the
  class-level-set half while breaking the class-level-absent half.

INPUT DOMAIN COVERAGE. The spec's whole input domain is the 2x2 toggle grid, so
the reject witnesses are placed to probe all four points — every combination is
demonstrated, and each toggle is exercised at BOTH of its values:

      (isAbstract, isClassLevel)   refuted rival                  clause
      (false, false)               weak-prefix-always-class        (i) over-emit
      (false, false)               weak-prefix-no-trailing-space   (iii) format
      (false, true )               weak-prefix-no-class            (i) under-emit
      (true,  false)               weak-prefix-no-abstract         (i) under-emit
      (true,  true )               weak-prefix-swap-order          (ii) order

  Two rivals are refuted at (false, false) but for DIFFERENT reasons — one
  renders an extra modifier word there, the other renders the right words with
  the wrong separator tail — and each is checked against its own variant, so
  neither borrows the other's evidence. (false, false) is the point where the
  format defect is isolated: it is the only input at which nothing but the
  trailing separator can differ.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent:
    no input carries a heap permission, there is no read-only half-permission
    to overwrite and no aliasing to exploit. This class has no expressible
    instance here and no substitute is fabricated for it.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED in the two
    toggles (an equality against a term built only from the inputs, fully
    unfolded); the bundle declares no ``opaque``/``axiom``, so there is no
    answer key an implementation could echo without doing the work. In its
    place the battery carries honest structural-reshape POSITIVE CONTROLS
    (``pos-*``) that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES to propertyPrefix, and is the bulk of the
    battery. Five rivals attack it: one omits the class-level word entirely
    (correct on the class-level-absent sub-domain, wrong when it is present),
    one emits the class-level word unconditionally (correct on the
    class-level-set sub-domain, wrong when it is absent — the mirror image, and
    the reason a one-sided battery is not enough), one omits the abstract word
    entirely, one emits the two modifier words in the wrong relative order
    (correct unless both are present), and one renders the right words with the
    wrong trailing separator (wrong everywhere, refuted at the point where that
    is the ONLY possible difference).

  * SOUNDNESS POSITIVES — three, deliberately spanning different carriers for
    the same value, because the obligation is a total equality over a 4-point
    domain and a single positive shape attests very little about what the spec
    ADMITS: an accumulator replaced by explicit list locals; an exhaustive
    case analysis on the toggle pair returning the four rendered literals; and
    a build with no word list at all (direct string concatenation of the
    per-toggle fragments). Each keeps the frozen tactic body; all three close.

  * ADMISSIBILITY — APPLIES, contrary to what this battery first recorded, and
    is carried by ``admiss-prefix-f2p-points``. The obligation is unconditional,
    but "no precondition binder" does not retire the lane on a total carrier
    (every obligation here is unconditional by construction). The testable
    analogue is the obligation being unsatisfiable at exactly an F2P-shaped
    input, which a positive that discharges it at that concrete input — by
    evaluation, as a ``have``, before closing the frozen obligation verbatim —
    tests directly. Nor is such a case "indistinguishable from a soundness
    positive": the soundness positives vary the IMPL and leave the proof alone,
    while this one keeps the impl frozen and adds evaluated obligations at named
    inputs, so it fails on a different defect (unsatisfiability at a normal
    input, not over-constraint of the carrier).

NAGINI CASES NOT PORTED. The nagini battery defends five modeled functions
across three behaviors; only the first — the toggle→prefix rendering — is
expressible on this carrier (the discovery / emission / retention behaviors
depend on the live CPython object model and are not modeled here, per
mapping.md). Per-case verdict against nagini's 17:

  PORTED (they attack the rendering this bundle models):
    - ``pos-prefix-reshape``      -> ``pos-prefix-list-locals`` (plus two
      further positives with no nagini counterpart, added because this
      obligation's domain is only four points).
    - ``weak-prefix-no-class``    -> same id here.
    - ``weak-prefix-swap-order``  -> same id here.

  ADDED HERE with no nagini counterpart (the nagini battery attacks the word
  presence clause only in the under-emit direction, and never the join format;
  on a 4-point domain those gaps leave half the grid unprobed):
    - ``weak-prefix-always-class``, ``weak-prefix-no-abstract``,
      ``weak-prefix-no-trailing-space``.

  LEGITIMATELY OMITTED — each is attached to a behavior this bundle does not
  model, so it has no counterpart on this carrier (NOT dropped for being hard):
    - ``pos-disc-branch-reorder``, ``weak-disc-property-only``,
      ``weak-disc-and-not-or``, ``cflow-disc-no-establish``,
      ``cflow-disc-wrong-member`` — the discovery decision and its per-member
      capability gate. There is no capability predicate, no member identity and
      no control-flow effect in this model: the modeled behavior is a total
      function of two booleans.
    - ``pos-popt-reshape``, ``weak-popt-no-classline``,
      ``weak-popt-swap-order``, ``weak-wopt-no-classline`` — the gated option
      emission. Not modeled here (it is reached only through runtime
      introspection of the live object model).
    - ``pos-retain-reshape``, ``weak-retain-drop-classlevel``,
      ``cflow-retain-no-establish`` — the retention decision and its gate. Same
      reason; also unmodeled.
    - ``admiss-gated-emit``, ``admiss-walk-emit`` — admissibility of the two
      capability preconditions. The capability PREDICATES are unmodeled (they
      belong to the introspection sites), so those two cases have no literal
      counterpart. Their LANE does, and it is carried: see
      ``admiss-prefix-f2p-points`` below. [Corrected by audit: this entry
      previously recorded the whole admissibility class as "vacuous, because the
      frozen obligation has no precondition". That is not the right test on a
      total carrier — a total-carrier obligation is unconditional by
      construction, so "no precondition binder" would retire the lane for every
      bundle on this backend. The analogue of PRECOND-TOO-STRONG here is the
      obligation being UNSATISFIABLE at exactly an F2P-shaped input, which is
      directly testable by discharging it at that concrete input BY EVALUATION,
      and the audit landed exactly that. The lane was underported, not vacuous.]
    - ``AXIOM_TESTS`` — dropped by design; the axiom lane is G-AX's.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form —
so a rejection alone attributes nothing to the spec. Every ``expect="reject"``
case therefore carries a Lean snippet proving the rival CONTRADICTS the spec at
one concrete input. Each is stated directly against the spec predicate at
``decide``-able literals, and each was checked to hold of its rival and to FAIL
on the frozen solution (so it discriminates rather than asserting a tautology).

AXIOM lane: EMPTY. No ``opaque``/``axiom`` is consumed; the behavior is a total
computation over the two toggles, so there is no axiom-soundness /
axiom-containment obligation to probe here (that lane belongs to G-AX in any
case, and the nagini AXIOM_TESTS are dropped by design).
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9461"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchor (the FULL body of the single impl region, unique in file) ----
_I_PREFIX = (
    "  let mut words : List String := []\n"
    "  if isAbstract then\n"
    "    words := words ++ [\"abstract\"]\n"
    "  if isClassLevel then\n"
    "    words := words ++ [\"class\"]\n"
    "  words := words ++ [\"property\"]\n"
    "  return String.intercalate \" \" words ++ \" \"\n"
)


# ---- the FULL frozen tactic body (unique in file); anchor for the admissibility
# ---- case, which prepends `have`s to it and then closes the obligation verbatim.
_P_PREFIX = (
    "  intro isAbstract isClassLevel\n"
    "  unfold problem_spec_propertyPrefix implementation_propertyPrefix prefixWords\n"
    "  cases isAbstract <;> cases isClassLevel <;> rfl\n"
)


def _witness(isAbstract, isClassLevel):
    """Refutation witness: the spec FAILS of the variant's own output at one
    concrete toggle pair. Stated against the spec predicate directly (no helper
    indirection) at literals, so `decide` settles it after unfolding."""
    a, c = str(isAbstract).lower(), str(isClassLevel).lower()
    return (
        f"example : ¬ problem_spec_propertyPrefix {a} {c}\n"
        f"    (implementation_propertyPrefix {a} {c}) := by\n"
        "  unfold problem_spec_propertyPrefix implementation_propertyPrefix prefixWords\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. The obligation is a total equality over
    # a FOUR-point domain, so a single positive shape says very little about
    # what the spec admits; these three reach the same value over three
    # different carriers (mutable accumulator -> explicit list locals; ->
    # exhaustive case analysis on the toggle pair; -> no word list at all).
    # If a faithful correct reshape could not satisfy the frozen obligation the
    # spec would be SPEC-TOO-STRONG. No helper lemma, axiom, or assumption
    # token is introduced; the theorem statement is byte-identical in each.
    # =====================================================================
    {
        "id": "pos-prefix-list-locals",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _I_PREFIX,
            "  let abstractWords : List String := if isAbstract then [\"abstract\"] else []\n"
            "  let classWords : List String := if isClassLevel then [\"class\"] else []\n"
            "  let words : List String := abstractWords ++ classWords ++ [\"property\"]\n"
            "  return String.intercalate \" \" words ++ \" \"\n",
        ),
        "rationale": "a correct reshape of the prefix build (the two optional "
                     "modifier words bound as explicit locals and concatenated "
                     "in the fixed abstract-then-class-then-base order) must "
                     "satisfy `result = String.intercalate \" \" (prefixWords "
                     "isAbstract isClassLevel) ++ \" \"`; if it cannot, the "
                     "postcondition is SPEC-TOO-STRONG. Proof: the frozen tactic "
                     "body is retained (`cases isAbstract <;> cases isClassLevel "
                     "<;> rfl` still closes — the reshaped locals reduce "
                     "definitionally to the same word list).",
    },

    # A correct impl that does NOT build a word list incrementally at all: it
    # decides the whole 2x2 toggle grid up front and returns the corresponding
    # rendered literal. This is the strongest available statement that the spec
    # admits the intended rendering at EVERY point of its domain — the four
    # literals are exactly the four strings the spec pins — and it is the shape
    # furthest from the frozen accumulator, so it is the sharpest
    # SPEC-TOO-STRONG probe available on this carrier.
    {
        "id": "pos-prefix-case-literals",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _I_PREFIX,
            "  return match isAbstract, isClassLevel with\n"
            "    | false, false => \"property \"\n"
            "    | false, true => \"class property \"\n"
            "    | true, false => \"abstract property \"\n"
            "    | true, true => \"abstract class property \"\n",
        ),
        "rationale": "exhaustive case analysis on the toggle pair returning the "
                     "four rendered literals. Each literal is what "
                     "`String.intercalate \" \" (prefixWords isAbstract "
                     "isClassLevel) ++ \" \"` evaluates to at that point, so the "
                     "postcondition must hold at all four inputs of its domain; "
                     "if this were rejected the spec would be SPEC-TOO-STRONG "
                     "(it would pin an output no faithful rendering can produce). "
                     "Proof: the frozen tactic body is retained — after `cases` "
                     "on both toggles each branch is `rfl` between the literal "
                     "and the reduced join.",
    },

    # A correct impl with no intermediate list value anywhere: the per-toggle
    # fragments are concatenated as strings directly, so the `List String` /
    # `String.intercalate` carrier of the spec is never mirrored by the impl.
    # The spec must still admit it, since only the RESULT string is constrained.
    {
        "id": "pos-prefix-string-concat",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _I_PREFIX,
            "  return (if isAbstract then \"abstract \" else \"\")\n"
            "    ++ (if isClassLevel then \"class \" else \"\")\n"
            "    ++ \"property \"\n",
        ),
        "rationale": "a correct rendering that never constructs a word list: "
                     "each present modifier contributes its word plus its "
                     "separator directly, in the fixed order, and the base word "
                     "carries the trailing separator. The postcondition "
                     "constrains only the result STRING, so it must admit this; "
                     "if it rejected an impl whose output is the pinned string "
                     "the spec would be SPEC-TOO-STRONG (over-constraining the "
                     "carrier rather than the behavior). Proof: the frozen "
                     "tactic body is retained.",
    },

    # =====================================================================
    # ADMISSIBILITY (kind="admissibility", expect="verify") — added by audit.
    # The frozen obligation is an unconditional `∀ isAbstract isClassLevel`, so
    # there is no precondition BINDER to attack; on this total carrier the
    # analogue of PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at
    # exactly an F2P-shaped input. That is what this case tests, directly: it
    # keeps the frozen impl VERBATIM and prepends, inside the existing tactic
    # body, `have`s that discharge the obligation BY EVALUATION (`decide`) at the
    # two toggle points the F2P prefix assertions pin — the class-level-only
    # attribute and the abstract-only one — and only then closes the frozen
    # obligation verbatim with the frozen three-line body.
    #
    # It cannot pass by the obligation being trivially true: each admissibility
    # `have` is paired with an `_outcome` `have` that pins the rendered string at
    # that input to a concrete literal, so the case exhibits the exact witness
    # value rather than merely asserting satisfiability. Audited by CONTROL: the
    # same shape with the class-level `_outcome` pinned to the WRONG literal (the
    # bare base word, i.e. what the pre-existing rendering produced there) does
    # NOT close — `decide` reports the proposition false — so these steps really
    # evaluate the rendering at these inputs rather than discharging anything put
    # in front of them.
    #
    # Statement byte-identical; no new declaration, axiom, lemma or `sorry`. If
    # this FAILS, the modeled behavior is unsatisfiable at a normal, F2P-shaped
    # input => PRECOND-TOO-STRONG.
    # =====================================================================
    {
        "id": "admiss-prefix-f2p-points",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_PREFIX,
            "  have _admissible_class : problem_spec_propertyPrefix false true\n"
            "      (implementation_propertyPrefix false true) := by\n"
            "    unfold problem_spec_propertyPrefix implementation_propertyPrefix prefixWords\n"
            "    decide\n"
            "  have _outcome_class : implementation_propertyPrefix false true\n"
            "      = \"class property \" := by\n"
            "    unfold implementation_propertyPrefix\n"
            "    decide\n"
            "  have _admissible_abstract : problem_spec_propertyPrefix true false\n"
            "      (implementation_propertyPrefix true false) := by\n"
            "    unfold problem_spec_propertyPrefix implementation_propertyPrefix prefixWords\n"
            "    decide\n"
            "  have _outcome_abstract : implementation_propertyPrefix true false\n"
            "      = \"abstract property \" := by\n"
            "    unfold implementation_propertyPrefix\n"
            "    decide\n" + _P_PREFIX,
        ),
        "rationale": "PRECOND-TOO-STRONG probe. The obligation is unconditional, "
                     "so the testable analogue on this total carrier is whether "
                     "it is SATISFIABLE at an F2P-shaped input rather than only "
                     "at degenerate ones. The two `_admissible_*` `have`s "
                     "discharge `problem_spec_propertyPrefix` by evaluation at "
                     "the two toggle points the F2P prefix assertions pin (the "
                     "class-level attribute and the abstract one), and the two "
                     "`_outcome_*` `have`s pin the rendered string there to the "
                     "concrete literals `\"class property \"` and `\"abstract "
                     "property \"`, so the case exhibits the witness values "
                     "instead of asserting mere satisfiability. The frozen impl "
                     "and the frozen tactic body are both retained verbatim; only "
                     "`have`s are prepended. If this failed, the pinned rendering "
                     "would be unsatisfiable at a normal input.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at
    # one concrete, decide-able input. Between them the witnesses probe all
    # four points of the toggle grid (see INPUT DOMAIN COVERAGE above).
    # =====================================================================

    # ---- PARTIAL-DOMAIN: never emits the class-level modifier word ----
    {
        "id": "weak-prefix-no-class",
        "kind": "uniqueness",
        "expect": "reject",
        # Seeds the base word and only ever contributes the abstract modifier;
        # the class-level toggle is ignored entirely. Correct when the
        # class-level toggle is absent, wrong when it is set.
        "module": _swap(
            _BASE, _I_PREFIX,
            "  let mut words : List String := []\n"
            "  if isAbstract then\n"
            "    words := words ++ [\"abstract\"]\n"
            "  words := words ++ [\"property\"]\n"
            "  return String.intercalate \" \" words ++ \" \"\n",
        ),
        "refinement": "this is the pre-existing rendering: the class-level "
                      "modifier word is never contributed, so a class-level "
                      "read-only attribute renders identically to a plain one. "
                      "The F2P prefix assertion pins the rendered annotation for "
                      "the class-level case to include the new modifier word "
                      "before the base word; a rendering that omits it produces "
                      "the bare base word and the assertion fails. It would NOT "
                      "resolve — this is the leg's prepatch.",
        "rationale": "REJECT from `result = String.intercalate \" \" (prefixWords "
                     "isAbstract isClassLevel) ++ \" \"`: on isClassLevel = true "
                     "the spec's word list contains the class-level word and the "
                     "rival's does not, so the rendered strings differ. Witness "
                     "at (isAbstract = false, isClassLevel = true) — the "
                     "class-level toggle set with the other clear, which isolates "
                     "the missing word.",
        "witness": _witness(False, True),
    },

    # ---- PARTIAL-DOMAIN, MIRROR IMAGE: emits the class-level word always ----
    # The presence clause is TWO-SIDED, and this rival satisfies exactly the
    # half the previous one breaks: it renders the class-level word whether or
    # not its toggle is set. Refuted at isClassLevel = FALSE, so the battery
    # discriminates that toggle at both of its values rather than pinning it.
    {
        "id": "weak-prefix-always-class",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_PREFIX,
            "  let mut words : List String := []\n"
            "  if isAbstract then\n"
            "    words := words ++ [\"abstract\"]\n"
            "  words := words ++ [\"class\"]\n"
            "  words := words ++ [\"property\"]\n"
            "  return String.intercalate \" \" words ++ \" \"\n",
        ),
        "refinement": "this contributes the class-level modifier word "
                      "unconditionally, ignoring its toggle. Every plain "
                      "read-only attribute — including one carrying only the "
                      "abstract toggle — then renders with the class-level word "
                      "inserted before the base word. The F2P prefix assertions "
                      "pin BOTH renderings in the same test: the attribute with "
                      "only the abstract toggle must render as the abstract word "
                      "followed by the base word, and the class-level one must "
                      "render with the class-level word; a rendering that always "
                      "emits the class-level word produces the wrong annotation "
                      "for the first and the assertion fails (and every "
                      "already-passing plain-attribute rendering regresses with "
                      "it). It would NOT resolve.",
        "rationale": "REJECT from `result = String.intercalate \" \" (prefixWords "
                     "isAbstract isClassLevel) ++ \" \"`: on isClassLevel = false "
                     "the spec's word list has no class-level word and the "
                     "rival's does. Witness at (isAbstract = false, isClassLevel "
                     "= false) — both toggles clear, where the spec pins the bare "
                     "base word, so the extra word is the only difference. This "
                     "is the input the other presence rivals cannot reach: they "
                     "are all CORRECT there.",
        "witness": _witness(False, False),
    },

    # ---- PARTIAL-DOMAIN: never emits the abstract modifier word ----
    # The other toggle's presence clause, attacked in the under-emit direction
    # and refuted at isClassLevel = false (so the witness set moves both
    # toggles) — the remaining corner of the grid.
    {
        "id": "weak-prefix-no-abstract",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_PREFIX,
            "  let mut words : List String := []\n"
            "  if isClassLevel then\n"
            "    words := words ++ [\"class\"]\n"
            "  words := words ++ [\"property\"]\n"
            "  return String.intercalate \" \" words ++ \" \"\n",
        ),
        "refinement": "this drops the abstract modifier word entirely: an "
                      "abstract read-only attribute renders exactly like a "
                      "non-abstract one. The F2P prefix assertion pins the "
                      "rendered annotation for the abstract case to the abstract "
                      "word followed by the base word; with the word dropped it "
                      "renders the bare base word and the assertion fails. It "
                      "would NOT resolve — and this defect is independent of the "
                      "class-level behavior, so no amount of correct class-level "
                      "handling repairs it.",
        "rationale": "REJECT from `result = String.intercalate \" \" (prefixWords "
                     "isAbstract isClassLevel) ++ \" \"`: on isAbstract = true "
                     "the spec's word list opens with the abstract word and the "
                     "rival's does not. Witness at (isAbstract = true, "
                     "isClassLevel = false) — the abstract toggle set with the "
                     "class-level one clear, which isolates the missing word from "
                     "any class-level effect and probes the fourth corner of the "
                     "toggle grid.",
        "witness": _witness(True, False),
    },

    # ---- PARTIAL-DOMAIN / ORDER: emits the modifiers in the wrong order ----
    {
        "id": "weak-prefix-swap-order",
        "kind": "uniqueness",
        "expect": "reject",
        # Contributes the class-level word BEFORE the abstract word (the two
        # optional blocks swapped). Correct unless both toggles are set; on both
        # it renders class-then-abstract where the spec pins abstract-then-class.
        "module": _swap(
            _BASE, _I_PREFIX,
            "  let mut words : List String := []\n"
            "  if isClassLevel then\n"
            "    words := words ++ [\"class\"]\n"
            "  if isAbstract then\n"
            "    words := words ++ [\"abstract\"]\n"
            "  words := words ++ [\"property\"]\n"
            "  return String.intercalate \" \" words ++ \" \"\n",
        ),
        "refinement": "this emits the class-level modifier before the abstract "
                      "modifier. The pinned rendering places the abstract word "
                      "first and the class-level word second; for an attribute "
                      "carrying both toggles the rendered annotation would differ "
                      "in word order from the asserted output, so the F2P prefix "
                      "assertion observing that ordering diverges. It would NOT "
                      "resolve.",
        "rationale": "REJECT from `result = String.intercalate \" \" (prefixWords "
                     "isAbstract isClassLevel) ++ \" \"`: on isAbstract = true and "
                     "isClassLevel = true the spec renders abstract-then-class "
                     "and the rival renders class-then-abstract, so the strings "
                     "differ. Witness at (true, true) — the ONLY input at which "
                     "this rival differs from the pinned rendering, so it is the "
                     "input its partial-domain claim requires.",
        "witness": _witness(True, True),
    },

    # ---- FORMAT: right words, wrong separator tail ----
    # The join format is the third component of the load-bearing clause and no
    # presence/order rival touches it: this one emits exactly the pinned word
    # list, in the pinned order, and still violates the spec at every input.
    {
        "id": "weak-prefix-no-trailing-space",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_PREFIX,
            "  let mut words : List String := []\n"
            "  if isAbstract then\n"
            "    words := words ++ [\"abstract\"]\n"
            "  if isClassLevel then\n"
            "    words := words ++ [\"class\"]\n"
            "  words := words ++ [\"property\"]\n"
            "  return String.intercalate \" \" words\n",
        ),
        "refinement": "this selects and orders the words correctly but renders "
                      "them without the trailing separator. The F2P prefix "
                      "assertions compare the rendered annotation to an exact "
                      "string that ends in a single space — for the plain, the "
                      "abstract and the class-level attribute alike — so a "
                      "rendering that stops after the base word produces a "
                      "different annotation for every one of them and each "
                      "assertion fails. It would NOT resolve, and it regresses "
                      "the renderings that already passed.",
        "rationale": "REJECT from `result = String.intercalate \" \" (prefixWords "
                     "isAbstract isClassLevel) ++ \" \"`: the rival omits the "
                     "`++ \" \"`, so its result is a strict prefix of the pinned "
                     "string at every input — the word SET and ORDER agree, only "
                     "the join format differs. Witness at (false, false), the "
                     "input where the word list is the single base word: there "
                     "nothing but the trailing separator CAN differ, so the "
                     "witness attributes the rejection to the format component "
                     "alone rather than to any word-presence effect.",
        "witness": _witness(False, False),
    },
]
