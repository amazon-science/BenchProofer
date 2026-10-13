"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-12585 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct copyRoute`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  copyRoute (isCollection exposesParams isClassObject strict : Bool)
      return (out : Route)
    ensures out = route isCollection exposesParams isClassObject strict

The method chooses which of FOUR mutually-exclusive actions to take for one
incoming value while a configured object is being reproduced, as a total
function of three independent boolean observations of the value plus the
caller's strictness flag. The single load-bearing ``ensures`` pins ``out`` to
the deep, fully-unfolded ``route`` (the ``axioms`` region is empty — no opaque
answer key to echo). ``route`` composes FOUR independently-attackable outcomes:

  * mapElements — the value is a recognized homogeneous collection (checked
    FIRST, before either other observation); each element is reproduced.
  * reconstruct — the value both advertises the declared-parameter interface AND
    is a genuine instance; it is rebuilt from its declared parameters.
  * refuse      — the value is NOT reconstructable and the caller is strict.
  * deepCopy    — the value is NOT reconstructable and the caller is lenient.

The load-bearing distinction the desired behaviour turns on: a value that
advertises the parameter interface but is itself a class (not an instance) is
NOT reconstructable — it must fall through to the deepCopy / refuse branch
alongside ordinary non-configurable values, never to reconstruction.

FOUR INPUT BINDERS, all load-bearing: ``isCollection`` (selects mapElements
first), ``exposesParams`` and ``isClassObject`` (jointly select
reconstruct vs the non-configurable branch), ``strict`` (selects refuse vs
deepCopy within the non-configurable branch). The reject witnesses drive the
tuple to FOUR distinct input points (pts=4), varying every binder and attacking
every one of the four outcomes.

REACHABILITY OF THE BINDER TUPLE (established by the adversarial audit; bounds
what the reject lane can honestly attack). The four binders are independent as
Lean ``Bool``s, but the carrier's abstraction is not surjective onto all 16
tuples: ``isCollection`` is an EXACT type test against four builtin collection
kinds, none of which advertises the declared-parameter interface, and a subclass
that did advertise it would fail the exact type test. So on real values
``isCollection`` implies NOT ``exposesParams``, and the four tuples with both set
are UNREACHABLE. Consequence for this battery: a rival that reorders the
collection test after the reconstruct test differs from ``route`` ONLY at
(isCollection, exposesParams) = (true, true), so although the spec correctly
REJECTS it (checked: rejected, and a witness at that point discriminates cleanly
— rival exit 0, gold exit 1), its faithful real counterpart is
behaviour-preserving on every value the real dispatch can receive and WOULD
resolve the failing scenario. It therefore fails the refinement requirement and
is deliberately NOT shipped as a reject case. Each of the four shipped witness
points, by contrast, was confirmed to be realized by an actual value: a
param-advertising class object, a plain non-configurable value under a strict
caller, a genuine collection, and a genuine configurable instance.

CARRIER NOTE — THE DECIDABLE BOUNDARY. A witness reaches the post-image through
Velvet's tester machinery (``copyRouteTester isCollection exposesParams
isClassObject strict = false`` says the extracted program's result violates the
postcondition at that concrete input) and closes by ``decide``, checked in a
file whose ``prove_correct`` block has been stripped so no tactic script can
mask the verdict. Unlike the loop-based velvet bundles, this carrier is FULLY
TRANSPARENT: the impl is a finite boolean dispatch, so the extracted program
reduces to ``isTrue``/``isFalse`` under the kernel for every concrete boolean
literal — both against a rival (where the postcondition is violated, so the
tester is ``false`` and ``= false`` elaborates by ``decide``) and against the
frozen solution (where it holds, the tester is ``true``, and ``= false`` fails
by ``decide``, the required FAIL-on-gold half). Every witness's four arguments
are concrete boolean literals, so no conditioning on an opaque term is needed
and the witnesses declare NO head binders (pts is measured on the literal
tuples). Both halves were checked with ``scripts/lean_verify.sh`` during
authoring — every witness elaborates green against its rival and fails
(``decide``) against the frozen solution.

ADVERSARIAL READ of the sibling's classes on this carrier (full accounting in
the footer):
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl (the reconstruction test restructured via De
    Morgan and handled first; the non-configurable predicate rewritten as an
    equivalent boolean) must verify, else the spec is SPEC-TOO-STRONG on the
    shape of the dispatch.
  * ADMISSIBILITY — the method declares no ``require`` clause, so the sibling's
    "a normal input satisfies the precondition" probe is vacuous here. The
    residual admissibility risk on a total domain is a DEGENERATE post-image;
    ``admiss-nondegenerate`` discharges an in-region ``assert`` pinning all FOUR
    outcomes at concrete inputs (including the class-object-under-lenient →
    deepCopy point the desired behaviour turns on), keeping the impl verbatim so
    the method's own obligation still discharges.
  * FRAME-MUTATION — VACUOUS on this backend. The sibling carries a mandatory
    frame-mutation rival because its read-only input is held at a fractional
    heap permission an impl can illegally overwrite. Lean/Velvet are
    referentially transparent: the four inputs are immutable ``Bool`` values
    (none ``mut``), there is no heap, no aliasing, and no permission system, so
    there is no read-only input to overwrite. The class has no carrier analogue;
    NOT ported (fabricating a substitute would test nothing).
  * DIVERGENCE / NON-TERMINATION - CLOSED BY THE SEMANTICS, measured rather than
    argued, and NOT ported as a case. This bundle sets
    ``loom.semantics.termination "total"`` (line 4) and opens
    ``TotalCorrectness`` (line 7), so the verifier discharges a real termination
    obligation and BOTH shapes a diverging rival can take are refused:
      - NO measure: a ``while`` prefix carrying no ``decreasing`` clause fails
        with ``Decreasing annotations are required in total correctness
        semantics``, raised on the ``method`` itself.
      - WITH a measure that does not decrease, which is the shape that cannot be
        dismissed as a missing annotation: ``decreasing spin`` over
        ``spin := spin + 1`` (strictly INCREASING), on the reconstruct arm and
        returning a wrong ``Route``, is REJECTED at exit 1 on the MEASURE's own
        descent goal, ``unsolved goals case «decreasing_1: spin» ... ⊢ spin + 1 <
        spin``. A CONSTANT measure fares the same way: ``decreasing (0 : Nat)``
        leaves ``case «decreasing_1: (0 : Nat)» ... ⊢ 0 < 0``.
    RETRACTION. An earlier revision of this note recorded the second shape as
    VERIFYING at exit 0 and escalated it as a corpus-wide spec hole ("the
    obligation is discharged by ANY measure expression; the strict-decrease side
    condition is never proven"), citing an unreachable-exit isolation. On
    re-measurement that is FALSE on this bundle and the escalation is withdrawn:
    the side condition IS proven, and the goal above is exactly it. Nothing from
    this class is escalated here.
    THE MECHANISM, so a reader need not take the measurement on faith:
    ``set_option loom.semantics.termination "total"`` itself opens the
    ``TotalCorrectness`` scope (Loom, ``MonadAlgebras/WP/Options.lean``, the
    ``openScope `TotalCorrectness`` arm), line 7 opens it again explicitly, and
    ``TotalCorrectness.WPGen.forWithInvariantLoop`` takes the ``measure`` and
    emits ``⌜measure b' < measure b⌝`` as a goal the proof must discharge. Only
    the ``PartialCorrectness`` twin takes a measure and drops it, which is why
    the two lines have to move together and do here.
    Still not shipped as a reject case, now for a WITNESS reason rather than a
    semantic one: a velvet reject case needs a witness that ELABORATES against
    the rival, but the rejection lands on the ``method`` declaration, which the
    witness file retains after the ``prove_correct`` block is stripped, so the
    rival's own module does not compile and no appended witness can elaborate.
    The gate would record ``witness-unproven`` => MALFORMED-TESTS. Reported here
    rather than faked.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is pinned to
    ``route isCollection exposesParams isClassObject strict``, a fully-unfolded
    ``def`` over the method's own arguments; there is no answer-key term a wrong
    impl could echo. The cheapest correct impl computes ``route`` honestly,
    which the positive controls cover.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival gets most of the
    domain right yet diverges on one sub-domain (a class object mis-routed to
    reconstruction, the strictness flag ignored, the collection branch dropped,
    or a genuine instance denied reconstruction).
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-12585"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the WHOLE gold impl block (between and INCLUDING the markers): a single
# ---- anchor lying wholly inside the impl region and unique in the file (both
# ---- facts asserted at load). Every rival and every reshaped positive swaps on
# ---- this block, so the edit is confined to the impl region and same_spec holds.
_IMPL = """    -- impl-start
    if isCollection then
      return Route.mapElements
    else
      -- A configured object must advertise the parameter interface AND be a
      -- genuine instance; a class object is excluded from reconstruction here.
      let nonConfigurable : Bool := (!exposesParams) || isClassObject
      if nonConfigurable then
        if strict then
          return Route.refuse
        else
          return Route.deepCopy
      else
        return Route.reconstruct
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- the impl-start marker line (unique); the admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view). A
# ---- reject rival keeps it verbatim (the impl has no loop, so the same generic
# ---- script applies — and for a wrong impl it simply fails to close, which is
# ---- the rejection); the admissibility case retunes it to also clear the extra
# ---- assert goal, without touching the spec or dropping the obligation header.
_PROOF_GOLD = "prove_correct copyRoute by\n  loom_solve <;> simp_all [route]"
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"


def _rewrite_impl(new_block):
    """Full variant: whole impl block replaced; proof kept as the frozen script."""
    return _swap(_BASE, _IMPL, new_block)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `copyRouteTester isCollection exposesParams isClassObject strict = false`
# ---- says the extracted program's result violates the method's postcondition at
# ---- that concrete input. Checked in a file whose `prove_correct` block has been
# ---- stripped. Every argument is a concrete boolean literal so `decide` reduces
# ---- the extracted program without getting stuck.
def _tester(body):
    return ("\n"
            "extract_program_for copyRoute\n"
            "prove_precondition_decidable_for copyRoute\n"
            "prove_postcondition_decidable_for copyRoute\n"
            "derive_tester_for copyRoute\n\n" + body)


def _b(x):
    return "true" if x else "false"


def _witness(isCollection, exposesParams, isClassObject, strict):
    return _tester(
        "example : copyRouteTester %s %s %s %s = false := by\n  decide\n"
        % (_b(isCollection), _b(exposesParams), _b(isClassObject), _b(strict)))


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-demorgan-reconstruct-first",
        "kind": "soundness",
        "expect": "verify",
        # Restructured control flow: after the collection test, the RECONSTRUCT
        # case is identified positively and handled FIRST (a value that advertises
        # the parameter interface AND is a genuine instance), with the
        # non-configurable branch in the trailing `else`. This is the De Morgan
        # dual of the frozen `nonConfigurable := (!exposesParams) || isClassObject`
        # test with the two arms swapped — observationally identical on every
        # input, maximally different control-flow shape.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    if isCollection then\n"
            "      return Route.mapElements\n"
            "    else\n"
            "      if exposesParams && (!isClassObject) then\n"
            "        return Route.reconstruct\n"
            "      else\n"
            "        if strict then\n"
            "          return Route.refuse\n"
            "        else\n"
            "          return Route.deepCopy\n"
            "    -- impl-end"),
        "rationale": (
            "identifies the reconstruct case positively (`exposesParams && "
            "(!isClassObject)`, the De Morgan dual of the frozen non-configurable "
            "test with arms swapped) and handles it first; the collection branch "
            "stays first so a collection still routes to mapElements. `out = route "
            "…` holds on the whole domain. If this fails to verify the spec is "
            "over-fit to the frozen dispatch shape (SPEC-TOO-STRONG). (Sibling: "
            "pos-control-reordered — a structurally-different correct impl.)"
        ),
    },
    {
        "id": "pos-control-equiv-boolean",
        "kind": "soundness",
        "expect": "verify",
        # Keeps the frozen branch structure but names the non-configurable
        # predicate with an equivalent boolean expression: `if exposesParams then
        # isClassObject else true` equals `(!exposesParams) || isClassObject` on
        # every input. Minimal edit inside the frozen shape.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    if isCollection then\n"
            "      return Route.mapElements\n"
            "    else\n"
            "      let nonConfigurable : Bool := if exposesParams then isClassObject else true\n"
            "      if nonConfigurable then\n"
            "        if strict then\n"
            "          return Route.refuse\n"
            "        else\n"
            "          return Route.deepCopy\n"
            "      else\n"
            "        return Route.reconstruct\n"
            "    -- impl-end"),
        "rationale": (
            "the non-configurable predicate is written as `if exposesParams then "
            "isClassObject else true`, equal to `(!exposesParams) || isClassObject` "
            "on every input, so the same arm fires for every tuple and `out = route "
            "…` still holds. A correct reshape must verify, else the postcondition "
            "is SPEC-TOO-STRONG (rejects a faithful impl over the shape of the "
            "predicate). (Sibling: pos-control-reordered, reshaped to a "
            "structure-preserving form.)"
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the method declares no `require` clause, so the sibling's
    # "a normal input satisfies the precondition" probe is vacuous. The residual
    # admissibility risk on a total domain is a DEGENERATE post-image — a spec no
    # impl distinguishes reads exactly like one every impl meets. This case
    # discharges an in-region `assert`, at four fully concrete inputs, that the
    # post-image is NON-DEGENERATE: a collection → mapElements, a class object
    # advertising params under a lenient caller → deepCopy (the point the desired
    # behaviour turns on), a plain non-configurable value under a strict caller →
    # refuse, and a genuine instance advertising params → reconstruct — four
    # genuinely distinct outcomes. The surrounding impl is kept verbatim so the
    # method's own obligation still discharges; the proof gains a `decide` arm to
    # clear the assert goal.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (\n"
                  "      route true false false false = Route.mapElements ∧\n"
                  "      route false true true false = Route.deepCopy ∧\n"
                  "      route false false false true = Route.refuse ∧\n"
                  "      route false true false false = Route.reconstruct))\n"),
            _PROOF_GOLD,
            "prove_correct copyRoute by\n"
            "  loom_solve <;> first\n"
            "    | decide\n"
            "    | simp_all [route]"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at four concrete "
            "inputs: a collection must give mapElements, a class object that "
            "advertises the parameter interface under a lenient caller must give "
            "deepCopy (NOT reconstruct — the distinction the desired behaviour "
            "turns on), a plain non-configurable value under a strict caller must "
            "give refuse, and a genuine instance advertising params must give "
            "reconstruct — four distinct outcomes. The in-region assert must "
            "discharge (else the obligation is degenerate); the impl is kept "
            "verbatim so `out = route …` still verifies. (Sibling: "
            "admiss-class-object-input, re-aimed from precondition admissibility "
            "to post-image non-degeneracy since this backend declares no "
            "`require` and has no permission surface.)"
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. The frozen spec is
    # untouched; each rival keeps the frozen proof script (which, for a wrong
    # impl, simply fails to close — the rejection), and the witness attributes
    # that rejection to the spec.
    # =====================================================================
    {
        "id": "weak-class-object-misroute",
        "kind": "uniqueness",
        "expect": "reject",
        # The exact pre-change shape: a value is treated as non-configurable
        # solely by whether it advertises the parameter interface, dropping the
        # is-class-object exclusion. A class object that advertises the interface
        # then falls through to reconstruction instead of the deepCopy/refuse
        # branch. Correct on every other input; diverges only when a value both
        # advertises params AND is a class object.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    if isCollection then\n"
            "      return Route.mapElements\n"
            "    else\n"
            "      let nonConfigurable : Bool := (!exposesParams)\n"
            "      if nonConfigurable then\n"
            "        if strict then\n"
            "          return Route.refuse\n"
            "        else\n"
            "          return Route.deepCopy\n"
            "      else\n"
            "        return Route.reconstruct\n"
            "    -- impl-end"),
        "refinement": (
            "this is the pre-change behaviour verbatim: a class object that "
            "advertises the parameter interface is routed to parameter-based "
            "reconstruction instead of the deep-copy branch. Reconstructing a "
            "class through its parameter interface calls the interface unbound and "
            "raises — exactly the failing scenario the desired behaviour fixes "
            "(a configured object holding a class-valued parameter can no longer "
            "be reproduced). It would NOT resolve. Correct on every value that is "
            "not a param-advertising class object."
        ),
        "rationale": (
            "REJECT from `out = route …` via the reconstruct/deepCopy boundary: "
            "when a value both advertises params and is a class object under a "
            "lenient caller the spec pins `Route.deepCopy`, but this returns "
            "`Route.reconstruct`. Verifying would be SPEC-TOO-WEAK (the "
            "class-object exclusion unpinned). Refuted at the param-advertising "
            "class-object point (`isClassObject` true, `exposesParams` true, "
            "lenient) — the sub-domain no other rival's witness reaches."
        ),
        "witness": _witness(False, True, True, False),
    },
    {
        "id": "weak-ignore-strict",
        "kind": "uniqueness",
        "expect": "reject",
        # The non-configurable branch ignores the caller's strictness and always
        # deep-copies, never refusing. Correct on mapElements, reconstruct, and on
        # the lenient sub-domain of the non-configurable branch; diverges only
        # when a non-configurable value meets a strict caller.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    if isCollection then\n"
            "      return Route.mapElements\n"
            "    else\n"
            "      let nonConfigurable : Bool := (!exposesParams) || isClassObject\n"
            "      if nonConfigurable then\n"
            "        return Route.deepCopy\n"
            "      else\n"
            "        return Route.reconstruct\n"
            "    -- impl-end"),
        "refinement": (
            "a faithful counterpart that deep-copied a non-configurable value "
            "under a strict caller instead of refusing would silently reproduce a "
            "value the caller demanded be reproduced only if configurable; the "
            "scenarios that assert a strict caller is refused a non-configurable "
            "value would get a silent deep copy instead of the refusal — it would "
            "NOT resolve. Correct on every lenient input and on every "
            "reconstructable value."
        ),
        "rationale": (
            "REJECT from `out = route …` via the refuse outcome: when a value is "
            "non-configurable and the caller is strict the spec pins "
            "`Route.refuse`, but this returns `Route.deepCopy`. Verifying would be "
            "SPEC-TOO-WEAK (the strictness flag unpinned on the non-configurable "
            "branch). Refuted at a plain non-configurable value under a STRICT "
            "caller (`strict` true) — the sole binder distinguishing this witness "
            "from the others, proving `strict` load-bearing."
        ),
        "witness": _witness(False, False, False, True),
    },
    {
        "id": "weak-drop-collection",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the collection test entirely, so a recognized collection is routed
        # by the parameter/class observations like any other value. A collection
        # advertises no parameter interface, so it becomes non-configurable and is
        # deep-copied (lenient) rather than having each element reproduced.
        # Correct on every non-collection value.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    let nonConfigurable : Bool := (!exposesParams) || isClassObject\n"
            "    if nonConfigurable then\n"
            "      if strict then\n"
            "        return Route.refuse\n"
            "      else\n"
            "        return Route.deepCopy\n"
            "    else\n"
            "      return Route.reconstruct\n"
            "    -- impl-end"),
        "refinement": (
            "a faithful counterpart that dropped the recognized-collection branch "
            "would deep-copy a homogeneous collection wholesale instead of "
            "reproducing each element and rebuilding a like collection; the "
            "elements would not themselves be reproduced, so the scenarios that "
            "reproduce a configured object holding a collection of sub-values "
            "would get shared (un-reproduced) elements — it would NOT resolve. "
            "Correct on every non-collection value."
        ),
        "rationale": (
            "REJECT from `out = route …` via the mapElements outcome: a recognized "
            "collection must give `Route.mapElements` regardless of the other "
            "observations, but this rival (dropping the collection test) routes it "
            "to `Route.deepCopy`. Verifying would be SPEC-TOO-WEAK (the "
            "collection-first branch unpinned). Refuted at a collection value "
            "(`isCollection` true) — the sole binder distinguishing this witness, "
            "proving `isCollection` load-bearing."
        ),
        "witness": _witness(True, False, False, False),
    },
    {
        "id": "weak-deny-reconstruct",
        "kind": "uniqueness",
        "expect": "reject",
        # Denies parameter-based reconstruction entirely: every non-collection
        # value is treated as non-configurable (deep-copied when lenient, refused
        # when strict). A genuine instance advertising the parameter interface is
        # deep-copied instead of rebuilt from its declared parameters. Correct on
        # collections and on every genuinely non-configurable value.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    if isCollection then\n"
            "      return Route.mapElements\n"
            "    else\n"
            "      if strict then\n"
            "        return Route.refuse\n"
            "      else\n"
            "        return Route.deepCopy\n"
            "    -- impl-end"),
        "refinement": (
            "a faithful counterpart that deep-copied a genuine configurable object "
            "instead of rebuilding it from its declared parameters would hand back "
            "a structural copy that carries the source's fitted state, rather than "
            "a fresh reconstruction whose derived attributes are absent; the "
            "scenarios that assert a reproduced configured object is a fresh "
            "unfitted rebuild would get a state-carrying copy — it would NOT "
            "resolve. Correct on collections and on every non-configurable value."
        ),
        "rationale": (
            "REJECT from `out = route …` via the reconstruct outcome: a value that "
            "advertises the parameter interface AND is a genuine instance must give "
            "`Route.reconstruct`, but this rival (denying reconstruction) returns "
            "`Route.deepCopy`. Verifying would be SPEC-TOO-WEAK (the reconstruct "
            "branch unpinned). Refuted at a genuine instance advertising params "
            "(`exposesParams` true, `isClassObject` false, lenient) — distinct "
            "from the class-object misroute point (`isClassObject` true), so the "
            "two do NOT share a witness."
        ),
        "witness": _witness(False, True, False, False),
    },
]

AXIOM_TESTS = []
