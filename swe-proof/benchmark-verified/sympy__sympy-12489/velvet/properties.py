"""properties.py — G-PBT falsification battery for sympy__sympy-12489 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
every ``prove_correct`` header survives) and swaps in a candidate impl; it is
checked by the real verifier. ``expect:"verify"`` passes iff (in scope AND
verifies); ``expect:"reject"`` passes iff (in scope AND does NOT verify AND its
refutation ``witness`` discriminates: elaborates against the rival, FAILS against
the frozen solution).

DEFENDED SURFACE. One shared construction primitive threads through a whole
family of construction operations. The primitive ``buildVia (builtOn) (value)``
mints a fresh result object; its two behaviours are

  ensures out.classId = builtOn      -- the result is an instance of the class
                                        it was dispatched on (the load-bearing
                                        observable-under-change)
  ensures out.contents = value       -- its ordered contents are exactly the
                                        value handed to it

Every other modeled operation builds its result BY invoking this primitive,
passing the class it is dispatched on, and its own postcondition therefore holds
ONLY if it threads that dispatch class correctly:

  * instance-dispatched sites (``composeProduct``, ``powerSelf``,
    ``reverseSelf``) — ``ensures out.classId = self.classId`` — must thread the
    LEFT operand's class;
  * target-dispatched sites (``fromUnit``, ``extentFor``, ``generateFor``,
    ``rankedFor``, ``rankedAltFor``, ``scheduleFor``) — ``ensures out.classId =
    cls`` — must thread the invoked-on class ``cls``;
  * the two PARTIAL instance-dispatched successor sites (``stepSelf``,
    ``stepAltSelf``) — same dispatch obligation, but stated on the branch where a
    successor EXISTS (``ensures <pred> self.contents = true → out.map (·.classId)
    = some self.classId``) plus ``ensures <pred> self.contents = false → out =
    none``: an operand that is last in that order has no successor and the
    operation produces NOTHING, not an object carrying other contents. The two
    orders have their own definedness predicate and their own value map.
  * the six REFUSING sites (``conjugateSelf``, ``bracketSelf``, ``divideSelf``,
    ``fromVectorFor``, ``foldOver``, ``rankedThirdFor``) — same dispatch
    obligation on the branch where the operation ACCEPTS its input, plus
    ``ensures <guard> = false → out = none``: each of these refuses a sub-domain
    outright and produces nothing at all for it. Two refuse a PAIR whose extents
    differ (``sameExtent``, a transparent ``def`` of the two operands' contents);
    the left-divide refuses a right operand that does not fit within the left
    (``fitsWithin``, also transparent, and ASYMMETRIC — it is not the same test as
    ``sameExtent``); the remaining three refuse an ill-formed offset vector
    (``vectorValid``), a sequence the fold cannot compose (``foldDefined``) and an
    out-of-range index (``rankedThirdDefined``), all opaque. See the CLOSED notes
    for SPEC DEFECT #3 and #4 at the foot of this file.

    The two OTHER index variants (``rankedFor``, ``rankedAltFor``) stay TOTAL, and
    that asymmetry is measured, not assumed: their real counterparts reduce the
    index into range first (``rank % new_psize`` / ``r % ifac(n)``) while this one
    does not, so flattening all three the same way would be unfaithful in the
    opposite direction.

``generateFor`` takes a second value binder (``entropy``) besides the extent, and
its contents clause is stated over ``generatedContents n entropy``: the value it
constructs is drawn from the ambient generator state, so it is NOT a function of
the extent alone, and an impl that ignores the state is a rival
(``weak-generateFor-ignores-entropy``) rather than an admissible reshape.

The contents clauses are stated over ``opaque`` per-site value maps (the value
computations the behaviour-under-change does NOT touch): only that the SAME map
feeds both sides is pinned, never a concrete value. Each map serves EXACTLY ONE
obligation: the two successor sites are bound to two DIFFERENT real successor
orders, so they carry two different maps (``stepContents`` / ``stepAltContents``)
— see the CLOSED note at the foot of this file for the audit that forced the
split and the rivals it made refutable.

CARRIER NOTE — the nagini→velvet carrier is WIDENED, not narrowed. The nagini
sibling contracts two functions (``make`` ≙ the primitive, ``combine`` ≙ the
binary product). This bundle models the SAME primitive plus every construction
site the fix threads (18 methods sharing ONE primitive), because the failing
scenario re-runs an interacting set of sites and depends on threading at many of
them. So the two nagini obligations map onto the primitive + the family of
sites; the nagini cases are re-expressed against the primitive and a
representative instance-site (``composeProduct``, ≙ ``combine``) and
target-site (``foldOver``), which is where each nagini rival's clause lives here.

DECIDABILITY OF WITNESSES. A witness reaches a method contract through Velvet's
tester machinery (``<name>Tester args = false`` says the extracted program
violates the postcondition at that input) and is checked in a file whose
``prove_correct`` blocks are stripped. The CLASS clause is fully transparent
(``ClassTag`` is ``Nat``), so a class-attacking witness closes at concrete
literal inputs after unfolding the tester. The primitive's CONTENTS clause is
transparent too (``value`` is the literal passed). A CONTENTS clause of a
non-primitive site routes through an ``opaque`` value map, which ``decide``
cannot reduce — so a content-attacking witness on such a site is CONDITIONED on
the carrier (``h : composeContents [1] [2] ≠ []``), refuting the rival exactly on
the sub-domain where the opaque map is non-empty. Its single hypothesis is
satisfiable (one assumption about one opaque term), which the gate's consistency
probe confirms.

The six REFUSING sites split by the transparency of their guard. Two are
transparent ``def``\ s — the symmetric extent test (``sameExtent a b :=
a.length == b.length``) and the asymmetric fit test (``fitsWithin inner outer :=
inner.length ≤ outer.length``) — so a witness against one of those three sites
closes at literal operand contents after unfolding it, and the ACCEPTED and
REFUSED branches are each reached by choosing the literals (``[1]``/``[2]`` vs
``[1]``/``[2,3]``). The other three guards are opaque (``vectorValid``,
``foldDefined``, ``rankedThirdDefined``), so a witness against those sites is
CONDITIONED on the branch it attacks (``h : vectorValid [0,1] = true`` /
``h : vectorValid [0,2] = false``, ``h : foldDefined [[0]] = true`` /
``h : foldDefined [] = false``, ``h : rankedThirdDefined 4 2 = true`` /
``h : rankedThirdDefined 2 7 = false``), one assumption about one opaque
predicate, which the gate's consistency probe confirms is satisfiable (probe exit
1). Every one of those six hypotheses is TRUE of the real callee at that input,
re-derived by executing it: the empty sequence composes to nothing, the fold of
``[[0]]`` succeeds, and the third index variant accepts ``(4, 2)`` but refuses
``(2, 7)``.

The two PARTIAL sites are conditioned for a second reason: their clauses are
GUARDED by an opaque definedness predicate, so every witness against one of them
names the branch it attacks (``h : stepDefined [1] = true`` for the class/contents
clauses, ``h : stepDefined [4] = false`` for the ``out = none`` clause), and the
delegation witness additionally assumes the two orders disagree at its input
(``hne : stepContents [1] ≠ stepAltContents [1]``) — which is exactly what the
two maps being unrelated permits, and what the real orders do at that operand.
Each such hypothesis set is satisfiable and the gate's consistency probe confirms
it (probe exit 1: ``False`` is NOT derivable from the binders).

ADVERSARIAL READ of the nagini classes:
  * FRAME-MUTATION (nagini's #1 class, ``self.kind = 0`` / ``array[0] = 0`` under
    fractional ``Acc(...,1/2)``) — VACUOUS here. This backend is referentially
    transparent, has no heap and no aliasing, and this bundle declares no ``mut``
    binder: there is no read-only input to overwrite and no substitute probe to
    fabricate. The nagini frame rivals' UNDERLYING wrong behaviour (minting onto
    the fixed base family) is still attacked — by the value-level primitive drop
    (``weak-primitive-drops-class``) and the site-unthreaded rivals — just not
    via the permission mechanism, which does not exist on this carrier.
  * PARTIAL-DOMAIN — APPLIES: a rival correct on most of the domain but
    collapsing the derived family on a sub-domain (``weak-primitive-collapse-one``,
    ≙ nagini ``partial-make-collapse-kind1``).
  * WRONG-REFERENCE — APPLIES: a site reaching the primitive through the WRONG
    dispatch class (``weak-site-right-operand``, ≙ nagini
    ``partial-combine-right-family``).
  * CONTENT-DROP — APPLIES: a site minting the correct class but on the wrong
    contents (``weak-primitive-drops-content`` on the primitive's transparent
    clause; ``weak-site-content-drop`` on a site's opaque clause, ≙ nagini
    ``partial-combine-content-drop``).
  * DIVERGENCE / NON-TERMINATION: nagini has none for this instance, so there
    is nothing to PORT. The disposition is REJECTED-BY-SPEC, not a hole and not a
    vacuous class, and the reason is NOT the one earlier revisions of this file
    recorded. Three earlier reasons are now measured false:

      - "a diverging impl cannot be written on this carrier": false; the loop
        elaborates.
      - "the bundle is ``partial``, so divergence is a known hole here": false of
        the frozen file this battery is stated against, which sets
        ``loom.semantics.termination "total"``. It is false of every velvet bundle:
        all 500 set ``"total"`` and open ``TotalCorrectness``, none sets
        ``"partial"``, so there is no ``partial`` lane anywhere in this corpus.
      - "the class is a KNOWN HOLE": false, and this is the retraction that
        matters. Under ``total`` a postcondition is claimed of ALL runs rather
        than only terminating ones, so both writable shapes of the class are
        REJECTED, as measured below.

    Under ``total`` the disposition splits by HOW the loop is written, and the two
    halves were measured separately:

      - a bare ``while True do pure ()`` prefix (no measure annotation) is
        REJECTED — but the rejection is a hard elaboration error on the METHOD
        (``Decreasing annotations are required in total correctness semantics``),
        so the whole file is uncompilable and no witness can hold of the rival.
        The gate's own witness check returns ``witness-unproven`` on it, which is
        an inconclusive outcome, not a pass. So this shape is a TOOLING
        non-starter, not a shippable reject case.
      - a loop carrying a measure annotation that never decreases
        (``decreasing i`` with a body that leaves ``i`` alone) is ALSO REJECTED,
        and on the descent obligation itself rather than on any value clause:
        ``unsolved goals case «decreasing_1: i» ... ⊢ 1 < 1``, with the frozen
        spec view intact and each proof reduced to a bare ``loom_solve`` so no
        tactic script can mask the verdict. The increasing variant
        (``i := i + 1``) is refused the same way, ``⊢ i + 1 < i``. An earlier
        revision of this file recorded this shape as a frozen-spec hole that
        VERIFIES; that claim is retracted with its measurement at the foot of
        this file.

    So the class is REJECTED-BY-SPEC in both shapes. It is inexpressible as a
    reject case, but the reason DIFFERS between the two shapes, and a fourth
    earlier claim — that the module "never compiles" so that not even
    ``example : True := trivial`` elaborates against either rival — is measured
    false of the shape that matters. Re-derived per shape:

      - NO-MEASURE shape: here the earlier claim HOLDS, and it is the whole
        story. The rejection really does land before the obligations
        (``Decreasing annotations are required in total correctness semantics``
        at the ``method``, or a parse error ``unexpected do-element of kind
        choice`` if the ``invariant``/``done_with`` clauses are omitted too), so
        the module is uncompilable and ``example : True := trivial`` FAILS
        against it (exit 1) exactly as claimed. Any witness would return
        ``witness-unproven``, an inconclusive outcome forcing MALFORMED-TESTS.
        A TOOLING non-starter.
      - MEASURE-BEARING shape: the claim is FALSE here. The method elaborates
        fine — the sole error is at the ``prove_correct`` line, on the descent
        obligation (``⊢ 1 < 1``), and nowhere else in the file. Accordingly
        ``example : True := trivial`` DOES elaborate against this rival (exit 0,
        both with and without the tester preamble), so the module compiles far
        enough to host a witness. What blocks the case is narrower and is the
        real wall: the loop's residual term (``forIn Lean.Loop.mk`` /  ``rep``
        under ``NonDetT.run``) is kernel-irreducible, so every DISCRIMINATING
        claim about the derived tester stalls on it rather than reducing. Eight
        witness shapes were built against this rival and all eight fail (exit
        1): plain ``simp`` on the tester, ``decide +kernel``, a gadget-lemma
        ``simp``, ``unfold`` + ``rfl``, the negated form
        ``¬ (… = true)``, an ``Exec``-level ``≠ DivM.res …``, a
        ``simp_all`` with the loop constants supplied, and the same shapes over
        a TERMINATING loop with a constant measure. The residual goal is the
        unreduced ``match NonDetT.run (… forIn Lean.Loop.mk …)`` itself
        (``_STUCK_REDUCTION``); the ``Exec`` form does not even get that far
        (``failed to synthesize Decidable``, on the frozen solution equally, so
        it is not rival-specific). ``native_decide`` is the one shape that
        genuinely separates the two subjects — and it separates them by
        DIVERGING: it evaluates on the frozen solution (reporting the
        proposition false, exit 1) and never terminates against the rival (still
        running when killed at 10 minutes), which is the expected behaviour of
        compiling and running a non-terminating program and is not a witness the
        gate could ever record. So this shape is blocked because no claim about
        the rival is kernel-decidable, NOT because the module fails to compile.

    In both shapes the disposition is the same and neither is a spec weakness or
    a battery gap; only the recorded REASON for the measure-bearing half is
    corrected here, from "the module never compiles" to "the loop term is
    kernel-irreducible, so no discriminating claim reduces".
  * AXIOM lane — dropped. This bundle consumes NO ``axiom`` (the ``opaque`` value
    maps are G-AX A-references, not consumed contracts); the axiom lane is
    G-AX's job and this gate ignores ``AXIOM_TESTS`` regardless.

WITNESS PLACEMENT. Rivals do not share a refutation point unless they fail there
for the same reason. Across the reject witnesses the primitive's ``builtOn`` is
moved over {5, 1, 7} and its ``value`` over {[1], [2]}; the instance site's
``self.classId`` over {2, 3, 5}, ``other.classId`` over {0, 2, 3, 5} and its
``contents`` pair over {([1],[2]), ([1],[3]), ([4],[3])}; the target site's
``cls`` over {5, 7} and its ``items`` over {[[1]], [[1],[2]]} — so every input
binder of every attacked obligation is varied by some witness, at distinct input
points. (Re-derived from the shipped witnesses by the audit rather than trusted;
two earlier revisions of this inventory understated the ``other.classId`` and
``contents`` ranges.) On the two PARTIAL successor sites the operand is moved over
{({contents := [1]}, classId 3), ({contents := [1]}, classId 5),
({contents := [4]}, classId 2)} AND over both branches of each order's definedness
predicate (``= true`` for the class/contents clauses, ``= false`` for the
``out = none`` clause), so no two of the four successor-site rivals are refuted at
the same point or on the same branch. On the six REFUSING sites the operand
pair is moved over {([1],[2]) at classId 3, ([1],[2,3]) at classId 2, ([3],[4])
at classId 7} for the first, {([1],[2]) at classId 3, ([4],[2,3]) at classId 6}
for the second, {([1],[2]) at classId 4, ([1],[2,3]) at classId 5} for the
left-divide, the vector site over {(cls 2, [0,1]), (cls 3, [0,2])}, the fold site
over {(cls 5, [[0]]), (cls 7, [[0],[0]]), (cls 3, [])} and the third index site
over {(cls 3, 4, 2), (cls 5, 2, 7)} — and across each site's rivals BOTH branches
of its guard are reached (an accepted input for the class and refuses-everything
rivals, a refused one for the refusal-dropping rival), so no two rivals on one
refusing site are refuted at the same point or on the same branch. ``generateFor``'s two rivals are refuted at
distinct points too (``9 2 1`` for the class clause, ``7 3 1`` for the
state-dependence clause).

AUDIT STATUS. Independently re-derived with the real verifier, three times — once
when the frozen file was ``partial``, again after it became ``total``, and again
after the successor sites were split and made partial (the G-PANEL-2 repair). In
the ``total`` re-derivation: all 24 reject witnesses of the then-shipped set
rebuilt against both subjects (rival exit 0, frozen solution exit 1, no stuck
reduction), both conditioned witnesses' consistency probes fail as required (exit
1), and five representative shapes additionally checked against a FORGED opposite
claim, which elaborates on the frozen solution (exit 0) and fails on the rival
(exit 1) — confirming the gold-side exit code carries real information rather than
reflecting a syntactic or reducibility failure. Seven new correct reshapes verify
(so the spec is not too strong), including two that bypass the shared primitive
entirely and build the result object directly. Fifteen new wrong impls are all
rejected.

In the successor-split re-derivation, the four cases that live on the repaired
obligations were each measured on all three legs: modules rejected (exit 1 with
``unsolved goals``) for ``weak-site-stepSelf``, ``weak-site-stepAltSelf``,
``weak-step-alt-delegates``, ``weak-stepSelf-fabricates-when-exhausted`` and
``weak-stepAltSelf-fabricates-when-exhausted``; each witness elaborates against
its rival (exit 0) and FAILS against the frozen solution (exit 1, ``⊢ False``
unsolved under its own hypotheses); each consistency probe fails (exit 1), so no
hypothesis set is contradictory. ``pos-step-partial-reshaped`` verifies (exit 0),
so the three-clause partial contract is jointly satisfiable by a correct impl
that bypasses the shared primitive.

In the refusing-site re-derivation (the second G-PANEL-2 repair), each of the
nine cases on the reshaped obligations was measured on all three legs: modules
rejected (exit 1, ``unsolved goals`` naming the intended clause — ``ensures_3``
for the three class rivals, the ``= false → out = none`` clause for the three
refusal-dropping rivals, the accepted-branch contents clause for
``weak-conjugateSelf-refuses-everything``, and ``out.contents = generatedContents
n entropy`` for ``weak-generateFor-ignores-entropy``); each witness elaborates
against its rival (exit 0) and FAILS against the frozen solution (exit 1); each
of the three conditioned witnesses' consistency probes fails (exit 1).
``pos-refusing-reshaped`` verifies (exit 0), so the three refusal contracts are
jointly satisfiable by a correct impl that bypasses the shared primitive at all
three sites.

In the second refusing-site re-derivation (SPEC DEFECT #4 — the left-divide, the
fold and the third index variant), the same three legs were measured for each of
the six cases on the newly reshaped obligations, and the accept/refuse decision of
each new guard was first re-derived by EXECUTING the real callee rather than
reasoned about: the left-divide refuses exactly when the right operand is longer
than the left (0 mismatches over all extent pairs 0..5), while the fold's and the
third index variant's accepted sets are NOT any plain comparison of their
parameters (the fold accepts ``[[1,0],[0]]`` but refuses ``[[0],[1,0]]``; the
third variant accepts every index at extents 0, 1 and 5 but only 0..3 at extent 2
and 0..14 at extent 3, i.e. neither ``rank < extent!`` nor a monotone bound), which
is why the first is a transparent ``def`` and the other two are opaque.

All four escapes earlier escalated from this file are now settled and NONE is
open: the two-obligations-over-one-map defect is CLOSED by the frozen-spec repair
(see the CLOSED note for SPEC DEFECT #1 at the end of this file, with the rivals
it made shippable), both total-refusing-sites defects are CLOSED the same way
(SPEC DEFECT #3 and #4), and the loop-measure claim is RETRACTED (rebuilt here,
that shape is rejected on the descent goal itself). Every record is kept at the
foot of this file rather than deleted.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-12489"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl anchors: each lies WHOLLY inside one `-- impl-start`/`-- impl-end`
# ---- region and is unique in the file (both asserted at load by _swap). ----

# The shared primitive's body: the one place the produced object's class is
# decided.
_PRIMITIVE = "    return { contents := value, classId := builtOn }"
assert _BASE.count(_PRIMITIVE) == 1, "primitive impl anchor drift"

# A representative instance-dispatched site (the binary product) — the direct
# counterpart of the nagini `combine`.
_INST_SITE = (
    "    let r ← buildVia self.classId (composeContents self.contents other.contents)\n"
    "    return r")
assert _BASE.count(_INST_SITE) == 1, "instance-site impl anchor drift"

# A representative target-dispatched (classmethod) site. It is ALSO one of the
# six refusing sites (the fold refuses a sequence it cannot compose), so the
# anchor is the guarded three-branch body and the two rivals aimed at it below
# keep the guard and attack only the dispatch class — their witnesses therefore
# carry the accepted-branch hypothesis.
_TGT_SITE = (
    "    if foldDefined items then\n"
    "      let r ← buildVia cls (foldContents items)\n"
    "      return some r\n"
    "    else\n"
    "      return none")
assert _BASE.count(_TGT_SITE) == 1, "target-site impl anchor drift"


def _tester(name):
    """Velvet tester preamble: reach a method contract as a decidable predicate.

    Appended to BOTH the rival and the frozen file, so the derived
    `<name>Tester` / `<name>Exec` names exist on both sides by construction.
    """
    return (f"extract_program_for {name}\n"
            f"prove_precondition_decidable_for {name}\n"
            f"prove_postcondition_decidable_for {name}\n"
            f"derive_tester_for {name}\n\n")


def _class_witness(name, targs):
    """A class-clause reject witness for site `name` at tester args `targs`.

    The class clause (`out.classId = self.classId` / `= cls`) is fully
    transparent (`ClassTag` is `Nat`), so the tester reduces after unfolding.
    """
    return (_tester(name) +
            f"example : {name}Tester {targs} = false := by\n"
            f"  simp [{name}Tester, {name}Exec, NonDetT.run, {name}, buildVia]\n")


# ---- Per-site class-clause rivals (carrier WIDENING). Each of the 16 other
# ---- construction sites is an INDEPENDENT obligation whose class clause is the
# ---- behaviour-under-change; mapping.md records that several (the index/random/
# ---- inversion-vector sites and the operator sites) are individually required
# ---- by the failing scenario, so a rival un-threading only one of them would
# ---- verify against a battery that attacked only composeProduct/foldOver yet
# ---- fail the F2P. Each rival dispatches the base-bound factory at its site;
# ---- its witness refutes it at a derived-class input (class tag 3, or cls 2-9).
#
# ---- The two successor sites (`stepSelf`, `stepAltSelf`) are the PARTIAL ones:
# ---- each returns `Option Obj`, each is stated over its OWN value map
# ---- (`stepContents` / `stepAltContents`) and its OWN definedness predicate
# ---- (`stepDefined` / `stepAltDefined`), so each impl block is unique in the
# ---- file and the anchor stays wholly inside the impl region. Their class
# ---- clause is now CONDITIONAL (`... = true → out.map (·.classId) = some
# ---- self.classId`), so a class-attacking witness on them must carry the
# ---- definedness hypothesis or the tester cannot reduce.
def _step_impl(pred, vmap, dispatch="self.classId"):
    return (f"    if {pred} self.contents then\n"
            f"      let r ← buildVia {dispatch} ({vmap} self.contents)\n"
            "      return some r\n"
            "    else\n"
            "      return none")


# (method, definedness predicate, value map, tester args, guard literal)
_STEP_SPECS = [
    ("stepSelf", "stepDefined", "stepContents",
     "{ contents := [1], classId := 3 }", "[1]"),
    ("stepAltSelf", "stepAltDefined", "stepAltContents",
     "{ contents := [1], classId := 3 }", "[1]"),
]

for _pred, _vmap in (("stepDefined", "stepContents"),
                     ("stepAltDefined", "stepAltContents")):
    assert _BASE.count(_step_impl(_pred, _vmap)) == 1, \
        f"step-site impl anchor drift ({_pred})"


_SITE_SPECS = [
    # instance-dispatched sites (dispatch = self.classId); refuted at classId 3
    ("reverseSelf",
     "    let r ← buildVia self.classId (reverseContents self.contents)\n    return r",
     "self.classId", "{ contents := [1], classId := 3 }"),
    ("powerSelf",
     "    let r ← buildVia self.classId (powerContents self.contents n)\n    return r",
     "self.classId", "{ contents := [1], classId := 3 } 2"),
    # target-dispatched (classmethod) sites (dispatch = cls); refuted at cls 2-9
    ("fromUnit",
     "    let r ← buildVia cls (fromUnitContents a b)\n    return r",
     "cls", "4 [1] [2]"),
    ("extentFor",
     "    let r ← buildVia cls (extentContents extent)\n    return r",
     "cls", "6 3"),
    ("generateFor",
     "    let r ← buildVia cls (generatedContents n entropy)\n    return r",
     "cls", "9 2 1"),
    ("rankedFor",
     "    let r ← buildVia cls (rankedContents extent rank)\n    return r",
     "cls", "8 3 1"),
    ("rankedAltFor",
     "    let r2 ← buildVia cls (rankedAltContents n r)\n    return r2",
     "cls", "9 3 1"),
    ("scheduleFor",
     "    let r ← buildVia cls (scheduleContents m n s)\n    return r",
     "cls", "4 2 3 1"),
]

_DISPATCH_ROLE = {"self.classId": "self.classId", "cls": "cls"}


def _site_case(name, orig, dispatch, targs):
    role = _DISPATCH_ROLE[dispatch]
    return {
        "id": f"weak-site-{name}",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, orig, orig.replace(f"buildVia {dispatch}",
                                                  "buildVia 0", 1)),
        "refinement": f"the faithful counterpart dispatches the base-bound factory "
                      f"at this construction site rather than its own {role}, so a "
                      f"derived-class result is minted as the base class. The failing "
                      f"scenario reaches this site on the derived class and asserts "
                      f"the result is of it => it would NOT resolve.",
        "rationale": f"REJECT from `out.classId = {role}`: base dispatch gives result "
                     f"class 0, ≠ {role} whenever it is a derived class. Refuted at a "
                     f"derived-class input.",
        "witness": _class_witness(name, targs),
    }


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps every obligation and the frozen proof
    # scripts (the post-image is a pointwise equality; no reshape here needs a
    # new lemma). ≙ nagini pos-make-inline / pos-combine-inline.
    # =====================================================================
    {
        "id": "pos-primitive-reshaped",
        "kind": "soundness",
        "expect": "verify",
        # Name the result in a local (fields reordered) before returning, instead
        # of the anonymous constructor. Same object, same two fields.
        "module": _swap(
            _BASE, _PRIMITIVE,
            "    let o : Obj := { classId := builtOn, contents := value }\n"
            "    return o"),
        "rationale": "a correct primitive that names the result in a local (with "
                     "the fields written in the other order) still mints exactly "
                     "`out.classId = builtOn` and `out.contents = value`, so both "
                     "ensures hold; if it rejects => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-site-inlined",
        "kind": "soundness",
        "expect": "verify",
        # Inline the primitive-call bind into the return instead of naming `r`.
        # Same value/class flow through the primitive dispatched on self's class.
        "module": _swap(
            _BASE, _INST_SITE,
            "    return (← buildVia self.classId (composeContents self.contents other.contents))"),
        "rationale": "a correct instance site that inlines the primitive call must "
                     "verify; the primitive's ensures give `out.classId = "
                     "self.classId` and `out.contents = composeContents ...`. If it "
                     "rejects => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — no method here has a `require` clause, so the nagini
    # "a normal half-permission input is admitted" probe is vacuous: nothing
    # could exclude an F2P-shaped input. Re-aimed (as the astropy sibling was) at
    # the residual admissibility risk on a total domain: that class propagation
    # is NON-DEGENERATE at the interesting point — a derived-family operand really
    # is carried to a non-base class, not silently coerced to the base. The
    # in-region assert discharges at a concrete derived tag (1); the impl is kept
    # verbatim so the method's own ensures still discharge and the frozen proof
    # (`loom_solve`) clears the extra goal. The assert is LIVE — machine-checked
    # by the audit, not "verified by hand": two deliberately FALSE variants of the
    # same claim (`derived.classId ≠ 1`; `derived.classId = 0`) each leave an
    # unsolved goal `case «admiss_1: ...»` (exit 1), and the TRUE counterpart
    # (`= 1`) verifies (exit 0). ≙ nagini admiss-combine.
    #
    # STRENGTHENED by audit. The original form asserted only `derived.classId ≠ 0`
    # — true, live, but a one-sided disequality that a spec pinning the class to
    # any non-zero constant would also satisfy. The shipped form below discharges
    # the obligation AT A CONCRETE F2P-SHAPED INPUT and pins BOTH clauses jointly:
    # a construction dispatched on the derived tag 1 over concrete operand
    # contents yields exactly class 1 (not 0) AND exactly the composed contents.
    # That is the total-carrier analogue the admissibility lane asks for — the
    # obligation is satisfiable, by evaluation, at exactly the point the failing
    # scenario reaches. Also machine-checked live: negating either half
    # (claiming class 0, or the operands composed in the other order) leaves an
    # unsolved goal (exit 1), while the shipped claim verifies (exit 0).
    # =====================================================================
    {
        "id": "admiss-family-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _INST_SITE,
            "    let r ← buildVia self.classId (composeContents self.contents other.contents)\n"
            "    let fp ← buildVia (1 : ClassTag) (composeContents [1] [2])\n"
            "    assert (with_name_prefix `admiss (fp.classId = (1 : ClassTag)\n"
            "      ∧ fp.classId ≠ (0 : ClassTag)\n"
            "      ∧ fp.contents = composeContents [1] [2]))\n"
            "    return r"),
        "rationale": "the obligation is SATISFIABLE at a concrete F2P-shaped input, "
                     "discharged by evaluation before the frozen obligation closes "
                     "verbatim: a construction dispatched on the derived tag 1 over "
                     "concrete operand contents really is carried to class 1 — not "
                     "silently coerced to the base class 0 — and carries exactly the "
                     "composed contents. Both halves come from the primitive's "
                     "`out.classId = builtOn` / `out.contents = value`, so a "
                     "base-collapsing or content-dropping primitive could not "
                     "discharge it. The site impl is kept verbatim so its own ensures "
                     "discharge too. If it rejects => PRECOND/ADMISSIBILITY-TOO-STRONG.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness and
    # the refinement argument that its faithful real counterpart would NOT resolve
    # the FAIL_TO_PASS scenario (which asserts the constructed result's runtime
    # class is the dispatched-on (possibly derived) class).
    # =====================================================================
    {
        "id": "weak-primitive-drops-class",
        "kind": "uniqueness",
        "expect": "reject",
        # The primitive ignores its dispatch class and mints the fixed base class
        # (tag 0) — the pre-patch behaviour, and the underlying wrong behaviour
        # behind BOTH nagini frame-mutation rivals (which reach base-family
        # minting via a permission cheat that does not exist on this carrier).
        "module": _swap(
            _BASE, _PRIMITIVE,
            "    return { contents := value, classId := 0 }"),
        "refinement": "the faithful counterpart is the pre-patch factory that always "
                      "builds the fixed base class regardless of the class it is "
                      "dispatched on. The failing scenario constructs a derived-class "
                      "operand and asserts the constructed result is of the derived "
                      "class; a base-minting factory yields the base class => it would "
                      "NOT resolve.",
        "rationale": "REJECT from `out.classId = builtOn`: at builtOn=5 the impl "
                     "returns classId 0 ≠ 5. Refuted at `builtOn=5, value=[1]`.",
        "witness": _tester("buildVia") +
                   "example : buildViaTester 5 [1] = false := by\n"
                   "  simp [buildViaTester, buildViaExec, NonDetT.run, buildVia]\n",
    },
    {
        "id": "weak-primitive-collapse-one",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: honour the dispatch class for every tag EXCEPT the
        # specific derived tag 1 (the failing scenario's derived class), collapsed
        # onto the base class 0. ≙ nagini partial-make-collapse-kind1.
        "module": _swap(
            _BASE, _PRIMITIVE,
            "    return { contents := value, classId := if builtOn == 1 then 0 else builtOn }"),
        "refinement": "the faithful counterpart propagates the class for every "
                      "subclass except the one mirroring tag 1 (the failing "
                      "scenario's derived class), which it still mints as the base "
                      "class. That scenario constructs exactly that subclass and "
                      "asserts the result is of it => it would NOT resolve.",
        "rationale": "REJECT from `out.classId = builtOn`: at builtOn=1 the impl "
                     "returns classId 0 ≠ 1. Refuted at `builtOn=1, value=[2]` — the "
                     "sub-domain point, distinct from the other primitive witnesses.",
        "witness": _tester("buildVia") +
                   "example : buildViaTester 1 [2] = false := by\n"
                   "  simp [buildViaTester, buildViaExec, NonDetT.run, buildVia]\n",
    },
    {
        "id": "weak-primitive-drops-content",
        "kind": "uniqueness",
        "expect": "reject",
        # CONTENT-DROP on the primitive's transparent contents clause: mint the
        # correct class but append a spurious element, so the contents are not the
        # value handed in. ≙ the content-identity half of nagini
        # partial-combine-content-drop, on the one clause that is `decide`-able.
        "module": _swap(
            _BASE, _PRIMITIVE,
            "    return { contents := value ++ [0], classId := builtOn }"),
        "refinement": "the faithful counterpart binds a corrupted array form onto "
                      "the result. The PASS_TO_PASS value checks compare exact array "
                      "forms of constructed objects, so a factory that alters the "
                      "contents fails them => it would NOT resolve.",
        "rationale": "REJECT from `out.contents = value`: the impl returns "
                     "`value ++ [0] ≠ value`. Refuted at `builtOn=7, value=[1]`, "
                     "where `[1,0] ≠ [1]`.",
        "witness": _tester("buildVia") +
                   "example : buildViaTester 7 [1] = false := by\n"
                   "  simp [buildViaTester, buildViaExec, NonDetT.run, buildVia]\n",
    },
    {
        "id": "weak-site-unthreaded",
        "kind": "uniqueness",
        "expect": "reject",
        # An instance-dispatched site that reaches the primitive through the fixed
        # base class (tag 0) instead of threading its own operand class — the
        # pre-patch site behaviour (calling the base-bound module factory). This is
        # the direct counterpart of the nagini combine minting onto the fixed base.
        "module": _swap(
            _BASE, _INST_SITE,
            "    let r ← buildVia 0 (composeContents self.contents other.contents)\n"
            "    return r"),
        "refinement": "the faithful counterpart dispatches the base-bound factory at "
                      "this site rather than the operand's own class, so a "
                      "derived-class product is minted as the base class. The failing "
                      "scenario asserts the product of a derived operand is of the "
                      "derived class => it would NOT resolve.",
        "rationale": "REJECT from `out.classId = self.classId`: with base dispatch "
                     "the result class is 0, ≠ self.classId whenever self is a "
                     "derived operand. Refuted at `self.classId=2` (`other.classId=2`).",
        "witness": _tester("composeProduct") +
                   "example : composeProductTester { contents := [4], classId := 2 } "
                   "{ contents := [3], classId := 2 } = false := by\n"
                   "  simp [composeProductTester, composeProductExec, NonDetT.run, "
                   "composeProduct, buildVia]\n",
    },
    {
        "id": "weak-site-right-operand",
        "kind": "uniqueness",
        "expect": "reject",
        # WRONG-REFERENCE: reach the primitive through the RIGHT operand's class
        # instead of the LEFT's. Correct only on the sub-domain
        # self.classId == other.classId. ≙ nagini partial-combine-right-family.
        "module": _swap(
            _BASE, _INST_SITE,
            "    let r ← buildVia other.classId (composeContents self.contents other.contents)\n"
            "    return r"),
        "refinement": "the faithful counterpart reaches the factory through the RIGHT "
                      "operand's class. On the failing scenario's product of a "
                      "derived left operand with a base right operand it yields the "
                      "base class, not the derived class the test asserts => it would "
                      "NOT resolve.",
        "rationale": "REJECT from `out.classId = self.classId`: the result class "
                     "equals other.classId, which differs from self.classId when the "
                     "operands are of different classes. Refuted at `self.classId=5, "
                     "other.classId=0` — moving the `other.classId` binder off the "
                     "value the unthreaded witness holds it at.",
        "witness": _tester("composeProduct") +
                   "example : composeProductTester { contents := [1], classId := 5 } "
                   "{ contents := [3], classId := 0 } = false := by\n"
                   "  simp [composeProductTester, composeProductExec, NonDetT.run, "
                   "composeProduct, buildVia]\n",
    },
    {
        "id": "weak-site-content-drop",
        "kind": "uniqueness",
        "expect": "reject",
        # CONTENT-DROP on a site's OPAQUE contents clause: mint the correct class
        # but on the empty contents instead of the computed composition. The
        # contents map is opaque, so `decide` cannot reduce it — the witness is
        # CONDITIONED on the carrier (the composition is non-empty at [1]/[2]),
        # refuting the rival exactly where the opaque map is non-empty. ≙ the
        # content half of nagini partial-combine-content-drop, on a site clause.
        "module": _swap(
            _BASE, _INST_SITE,
            "    let r ← buildVia self.classId []\n"
            "    return r"),
        "refinement": "the faithful counterpart returns a product of empty array form "
                      "rather than the computed composition, failing every value "
                      "check in the PASS_TO_PASS product tests => it would NOT "
                      "resolve.",
        "rationale": "REJECT from `out.contents = composeContents self.contents "
                     "other.contents`: the impl returns `[]`, which differs from the "
                     "composition wherever that map is non-empty. Refuted at "
                     "`self.contents=[1], other.contents=[2]` under the single "
                     "hypothesis `composeContents [1] [2] ≠ []` (satisfiable — one "
                     "assumption about one opaque term).",
        "witness": _tester("composeProduct") +
                   "example (h : composeContents [1] [2] ≠ []) :\n"
                   "    composeProductTester { contents := [1], classId := 5 } "
                   "{ contents := [2], classId := 5 } = false := by\n"
                   "  simp [composeProductTester, composeProductExec, NonDetT.run, "
                   "composeProduct, buildVia]\n"
                   "  intro hc\n"
                   "  exact h hc\n",
    },
    {
        "id": "weak-site-operand-order",
        "kind": "uniqueness",
        "expect": "reject",
        # WRONG-REFERENCE on the CONTENTS clause of an instance site: mint the
        # correct class, apply the correct map, but feed it the operands in the
        # REVERSED order. Added by audit: the other content rival on this site
        # (`weak-site-content-drop`) replaces the contents with `[]`, so nothing
        # in the battery pinned the ARGUMENT ORDER of the value map — the clause
        # is stated in operand order and a rival that transposes it was uncaught.
        "module": _swap(
            _BASE, _INST_SITE,
            "    let r ← buildVia self.classId (composeContents other.contents self.contents)\n"
            "    return r"),
        "refinement": "the faithful counterpart combines the two operands in the "
                      "opposite order. The binary product is not commutative, so the "
                      "PASS_TO_PASS product value checks compare an array form this "
                      "impl does not produce => it would NOT resolve.",
        "rationale": "REJECT from `out.contents = composeContents self.contents "
                     "other.contents`: the impl returns `composeContents "
                     "other.contents self.contents`, which differs wherever the map "
                     "is not symmetric in its two arguments. Refuted at "
                     "`self.contents=[1], other.contents=[2]` under the single "
                     "hypothesis `composeContents [1] [2] ≠ composeContents [2] [1]` "
                     "(satisfiable — one assumption relating two distinct "
                     "applications of one opaque map; the gate's consistency probe "
                     "confirms it, exit 1).",
        "witness": _tester("composeProduct") +
                   "example (h : composeContents [1] [2] ≠ composeContents [2] [1]) :\n"
                   "    composeProductTester { contents := [1], classId := 3 } "
                   "{ contents := [2], classId := 3 } = false := by\n"
                   "  simp [composeProductTester, composeProductExec, NonDetT.run, "
                   "composeProduct, buildVia]\n"
                   "  intro hc\n"
                   "  exact h hc.symm\n",
    },
    {
        "id": "weak-target-site-payload-dispatch",
        "kind": "uniqueness",
        "expect": "reject",
        # WRONG-REFERENCE on the TARGET clause: reach the primitive through a
        # class derived from the PAYLOAD rather than through `cls`. Added by
        # audit: the wrong-reference shape was attacked only on the instance
        # clause (`weak-site-right-operand`); on the target clause the battery
        # carried only the drop-to-base-tag shape, so a rival that computes a
        # plausible-but-wrong dispatch class was uncaught. Also moves the
        # `items` binder, which no other target-site witness varies.
        "module": _swap(
            _BASE, _TGT_SITE,
            "    if foldDefined items then\n"
            "      let r ← buildVia items.length (foldContents items)\n"
            "      return some r\n"
            "    else\n"
            "      return none"),
        "refinement": "the faithful counterpart dispatches the factory on a class "
                      "chosen from the operand sequence it folds rather than on the "
                      "invoked-on class. The failing scenario invokes this site on "
                      "the derived class and asserts the result is of it; the class "
                      "this impl picks is unrelated to the invoked-on one => it would "
                      "NOT resolve.",
        "rationale": "REJECT from `out.classId = cls`: the result class is the operand "
                     "count, which differs from `cls` whenever they disagree. Refuted "
                     "at `cls=7, items=[[0],[0]]` (count 2 ≠ 7) — a two-element "
                     "payload, moving the `items` binder off the singleton every "
                     "other target witness holds it at. The witness carries the "
                     "accepted-branch hypothesis because the site's class clause is "
                     "now conditional; `[[0],[0]]` is a sequence the real fold "
                     "genuinely accepts (it composes to `[0]`), so the hypothesis is "
                     "true of the callee and not merely consistent.",
        "witness": _tester("foldOver") +
                   "example (h : foldDefined [[0],[0]] = true) :\n"
                   "    foldOverTester 7 [[0],[0]] = false := by\n"
                   "  simp [foldOverTester, foldOverExec, NonDetT.run, foldOver, "
                   "buildVia, h]\n",
    },
    {
        "id": "weak-target-site-unthreaded",
        "kind": "uniqueness",
        "expect": "reject",
        # A target-dispatched (classmethod) site that reaches the primitive through
        # the fixed base class (tag 0) instead of threading its target class `cls`.
        # Covers the SECOND site shape (`out.classId = cls`), which the nagini pair
        # (both instance-shaped) never exercises but the failing scenario's
        # classmethod construction sites depend on.
        "module": _swap(
            _BASE, _TGT_SITE,
            "    if foldDefined items then\n"
            "      let r ← buildVia 0 (foldContents items)\n"
            "      return some r\n"
            "    else\n"
            "      return none"),
        "refinement": "the faithful counterpart dispatches the base-bound factory at "
                      "a classmethod construction site rather than the invoked-on "
                      "class, so the built object is the base class. The failing "
                      "scenario invokes such sites on the derived class and asserts "
                      "the result is of it => it would NOT resolve.",
        "rationale": "REJECT from `foldDefined items = true → out.map (·.classId) = "
                     "some cls`: with base dispatch the result class is 0, ≠ cls "
                     "whenever cls is a derived class. Refuted at `cls=5, "
                     "items=[[0]]`, a sequence the real fold accepts. This is the "
                     "class rival for the fold site (the `_REFUSE_SPECS` loop below "
                     "therefore does not generate a second one for it).",
        "witness": _tester("foldOver") +
                   "example (h : foldDefined [[0]] = true) :\n"
                   "    foldOverTester 5 [[0]] = false := by\n"
                   "  simp [foldOverTester, foldOverExec, NonDetT.run, foldOver, "
                   "buildVia, h]\n",
    },
]

# The remaining 8 always-constructing sites, each attacked on its own class
# clause (carrier widening — see _SITE_SPECS above). The six REFUSING sites
# carry the same class-clause rival under the same case id, built below against
# their guarded impl shape.
SPEC_TESTS += [_site_case(*s) for s in _SITE_SPECS]

# The two PARTIAL successor sites, attacked on their (conditional) class clause.
# The witness carries the definedness hypothesis: off the defined sub-domain the
# spec pins `out = none` and the class clause says nothing, so an unconditioned
# witness would not reduce. The hypothesis is satisfiable (one assumption about
# one opaque predicate), which the gate's consistency probe confirms.
for _step, _pred, _vmap, _targs, _lit in _STEP_SPECS:
    SPEC_TESTS.append({
        "id": f"weak-site-{_step}",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _step_impl(_pred, _vmap), _step_impl(_pred, _vmap, "0")),
        "refinement": "the faithful counterpart dispatches the base-bound factory at "
                      "this successor construction site rather than the operand's own "
                      "class, so a derived-class result is minted as the base class; "
                      "the failing scenario reaches it on the derived class => it "
                      "would NOT resolve.",
        "rationale": "REJECT from `out.classId = self.classId` on the defined branch: "
                     "base dispatch gives result class 0, ≠ self.classId for a derived "
                     "operand. Refuted at a derived-class input (classId 3) where the "
                     "successor exists.",
        "witness": _tester(_step) +
                   f"example (h : {_pred} {_lit} = true) :\n"
                   f"    {_step}Tester {_targs} = false := by\n"
                   f"  simp [{_step}Tester, {_step}Exec, NonDetT.run, {_step}, "
                   f"buildVia, h]\n",
    })

# ---- The two obligations the successor sites' SEPARATION buys (each was
# ---- unrefutable before the frozen spec distinguished the two orders and made
# ---- them partial; see the CLOSED note at the end of this file).
SPEC_TESTS += [
    {
        "id": "weak-step-alt-delegates",
        "kind": "uniqueness",
        "expect": "reject",
        # The alternative-order site simply hands back the LEXICAL successor.
        "module": _swap(
            _BASE, _step_impl("stepAltDefined", "stepAltContents"),
            "    let r ← stepSelf self\n"
            "    return r"),
        "refinement": "the faithful counterpart computes the LEXICAL successor at the "
                      "alternative-order site — one order's successor served where the "
                      "other's is asked for. The repo's own PASS_TO_PASS scenario "
                      "advances one operand by each rule and requires the two orders "
                      "to enumerate the operands differently (they disagree on 4 of "
                      "6 operands at extent 3, 19 of 24 at extent 4, 105 of 120 at "
                      "extent 5, re-derived against the patched worktree) => it would "
                      "NOT resolve.",
        "rationale": "REJECT from `stepAltDefined ... = true → out.map (·.contents) = "
                     "some (stepAltContents self.contents)`: delegating yields "
                     "`stepContents self.contents`, and nothing relates the two maps. "
                     "Refuted where both successors exist and the two maps differ.",
        "witness": _tester("stepAltSelf") +
                   "example (hd : stepDefined [1] = true) (ha : stepAltDefined [1] = true)\n"
                   "    (hne : stepContents [1] ≠ stepAltContents [1]) :\n"
                   "    stepAltSelfTester { contents := [1], classId := 5 } = false := by\n"
                   "  simp [stepAltSelfTester, stepAltSelfExec, NonDetT.run, stepAltSelf, "
                   "stepSelf,\n"
                   "        buildVia, hd, ha, hne]\n",
    },
]

# Each successor order RUNS OUT, and a site that ignores that fabricates an
# object for an operand that has no successor. One rival per order, so both
# `... = false → out = none` clauses are attacked.
for _step, _pred, _vmap in (("stepSelf", "stepDefined", "stepContents"),
                            ("stepAltSelf", "stepAltDefined", "stepAltContents")):
    SPEC_TESTS.append({
        "id": f"weak-{_step}-fabricates-when-exhausted",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the guard: always build, so the last operand in the order gets a
        # fabricated successor instead of nothing.
        "module": _swap(
            _BASE, _step_impl(_pred, _vmap),
            f"    let r ← buildVia self.classId ({_vmap} self.contents)\n"
            "    return some r"),
        "refinement": "the faithful counterpart returns a constructed object for an "
                      "operand that is LAST in this order, where the real operation "
                      "produces nothing at all. The scenario walks the order to "
                      "exhaustion and stops on the absence of a successor; a "
                      "fabricated one makes that walk run past the end => it would "
                      "NOT resolve.",
        "rationale": f"REJECT from `{_pred} self.contents = false → out = none`: the "
                     "unguarded impl returns `some _` there. Refuted at an operand "
                     "whose successor in this order does not exist.",
        "witness": _tester(_step) +
                   f"example (h : {_pred} [4] = false) :\n"
                   f"    {_step}Tester {{ contents := [4], classId := 2 }} = false := by\n"
                   f"  simp [{_step}Tester, {_step}Exec, NonDetT.run, {_step}, buildVia, h]\n",
    })

# Positive control for the PARTIAL shape (soundness): both successor sites
# re-expressed without the shared primitive — the definedness decision named in a
# local and the result object built directly. Still correct, so it must verify;
# if it rejects, the partiality obligations are SPEC-TOO-STRONG.
SPEC_TESTS.append({
    "id": "pos-step-partial-reshaped",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(
        _swap(_BASE, _step_impl("stepDefined", "stepContents"),
              "    let ok := stepDefined self.contents\n"
              "    if ok then\n"
              "      return some { classId := self.classId, "
              "contents := stepContents self.contents }\n"
              "    else\n"
              "      return none"),
        _step_impl("stepAltDefined", "stepAltContents"),
        "    let ok := stepAltDefined self.contents\n"
        "    if ok then\n"
        "      return some { classId := self.classId, "
        "contents := stepAltContents self.contents }\n"
        "    else\n"
        "      return none"),
    "rationale": "a correct partial site that names its definedness decision in a "
                 "local and builds the result object directly (bypassing the shared "
                 "primitive) still returns `some` exactly where the successor exists, "
                 "with the operand's own class and this order's successor contents, "
                 "and `none` elsewhere — so all three ensures of both sites hold. If "
                 "it rejects => SPEC-TOO-STRONG (and in particular the `out = none` "
                 "clause would be unsatisfiable jointly with the other two).",
})


# ---- The three REFUSING sites. Each of these operations produces NO object at
# ---- all for a sub-domain of its inputs, rather than one carrying substitute
# ---- contents, so each returns `Option Obj` under a three-clause contract:
# ----
# ----     ensures <guard> = true  → out.map (·.classId) = some <dispatch>
# ----     ensures <guard> = true  → out.map (·.contents) = some (<map> <args>)
# ----     ensures <guard> = false → out = none
# ----
# ---- Three of them refuse on a TRANSPARENT test of the operands' extents, so
# ---- their witnesses need no hypothesis: two on the symmetric `sameExtent` (a
# ---- pair of differing extents), one on the ASYMMETRIC `fitsWithin` (a right
# ---- operand longer than the left). The other three refuse on an OPAQUE
# ---- predicate (`vectorValid`, `foldDefined`, `rankedThirdDefined`), so their
# ---- witnesses name the branch they attack. Each site carries its class rival
# ---- (SAME case id as before the reshape) AND a rival that DROPS the refusal —
# ---- the shape that was unrefutable while these sites were total, and the one
# ---- the failing scenario reaches. See the CLOSED notes for SPEC DEFECT #3 and
# ---- #4 at the foot of this file.
def _refuse_impl(pred, vmap, args, dispatch="self.classId"):
    return (f"    if {pred} then\n"
            f"      let r ← buildVia {dispatch} ({vmap} {args})\n"
            "      return some r\n"
            "    else\n"
            "      return none")


_PAIR_GUARD = "sameExtent self.contents other.contents"
_PAIR_ARGS = "self.contents other.contents"
# The left-divide's guard is NOT `_PAIR_GUARD`: its value indexes the LEFT
# operand's inverse at the RIGHT operand's entries, so it accepts a shorter right
# operand and refuses only a longer one. Stating it with the symmetric test would
# be wrong in BOTH directions (it would refuse pairs the real operation accepts
# and accept none it refuses), so the asymmetry is stated as its own predicate,
# applied in the site's own argument order.
_DIV_GUARD = "fitsWithin other.contents self.contents"

# (method, guard, value map, map args, dispatch, guard-unfold token,
#  (accepted-input tester args, hypothesis), (refused-input tester args, hypothesis),
#  class-rival case id — None where that rival is shipped explicitly above)
_REFUSE_SPECS = [
    ("conjugateSelf", _PAIR_GUARD, "conjugateContents", _PAIR_ARGS, "self.classId",
     "sameExtent",
     ("{ contents := [1], classId := 3 } { contents := [2], classId := 3 }", None),
     ("{ contents := [1], classId := 2 } { contents := [2,3], classId := 2 }", None),
     "weak-site-conjugateSelf"),
    ("bracketSelf", _PAIR_GUARD, "bracketContents", _PAIR_ARGS, "self.classId",
     "sameExtent",
     ("{ contents := [1], classId := 3 } { contents := [2], classId := 3 }", None),
     ("{ contents := [4], classId := 6 } { contents := [2,3], classId := 6 }", None),
     "weak-site-bracketSelf"),
    # The left-divide: transparent but ASYMMETRIC guard. The refused point has the
    # RIGHT operand longer than the left — the direction the real `_af_rmul` walks
    # off the end of.
    ("divideSelf", _DIV_GUARD, "divideContents", _PAIR_ARGS, "self.classId",
     "fitsWithin",
     ("{ contents := [1], classId := 4 } { contents := [2], classId := 4 }", None),
     ("{ contents := [1], classId := 5 } { contents := [2,3], classId := 5 }", None),
     "weak-site-divideSelf"),
    ("fromVectorFor", "vectorValid vec", "fromVectorContents", "vec", "cls", None,
     ("2 [0,1]", "h : vectorValid [0,1] = true"),
     ("3 [0,2]", "h : vectorValid [0,2] = false"),
     "weak-site-fromVectorFor"),
    # The fold: the EMPTY sequence is the refused point (nothing to compose), and
    # `[[0]]` is accepted. Its class rival ships above as
    # `weak-target-site-unthreaded` at the same accepted point, so none is
    # generated here.
    ("foldOver", "foldDefined items", "foldContents", "items", "cls", None,
     ("5 [[0]]", "h : foldDefined [[0]] = true"),
     ("3 []", "h : foldDefined [] = false"),
     None),
    # The third index variant: `(4, 2)` is accepted and `(2, 7)` refused — both
    # re-derived by executing the real unranking, whose accepted set is a prefix
    # that is neither `rank < extent!` nor monotone in the extent.
    ("rankedThirdFor", "rankedThirdDefined extent rank", "rankedThirdContents",
     "extent rank", "cls", None,
     ("3 4 2", "h : rankedThirdDefined 4 2 = true"),
     ("5 2 7", "h : rankedThirdDefined 2 7 = false"),
     "weak-site-rankedThirdFor"),
]

for _r in _REFUSE_SPECS:
    assert _BASE.count(_refuse_impl(_r[1], _r[2], _r[3], _r[4])) == 1, \
        f"refusing-site impl anchor drift ({_r[0]})"


def _pos_refusing():
    """All six refusing sites reshaped at once (positive control)."""
    src = _BASE
    for (_nm, _guard, _map, _args, _disp, _unfold, _acc, _ref, _cid) in _REFUSE_SPECS:
        src = _swap(src, _refuse_impl(_guard, _map, _args, _disp),
                    f"    let ok := {_guard}\n"
                    "    if ok then\n"
                    f"      return some {{ classId := {_disp}, contents := {_map} {_args} }}\n"
                    "    else\n"
                    "      return none")
    return src

def _refuse_witness(name, targs, hyp, unfold):
    """A reject witness against refusing site `name` at tester args `targs`.

    Unconditioned where the guard is the transparent extent test (the simp set
    unfolds it); conditioned on the attacked branch where the guard is opaque.
    """
    head = f"example ({hyp}) :\n    " if hyp else "example : "
    return (_tester(name) + head +
            f"{name}Tester {targs} = false := by\n"
            f"  simp [{name}Tester, {name}Exec, NonDetT.run, {name}, buildVia, "
            f"{'h' if hyp else unfold}]\n")


for (_nm, _guard, _map, _args, _disp, _unfold, _acc, _ref, _cid) in _REFUSE_SPECS:
    _impl = _refuse_impl(_guard, _map, _args, _disp)
    _role = _DISPATCH_ROLE[_disp]
    # (a) the class clause on the ACCEPTED branch — same obligation, same case id
    #     as before this site was reshaped, re-aimed at the guarded impl. Skipped
    #     for the one site whose class rival is shipped explicitly above under its
    #     own historical id (`weak-target-site-unthreaded`), so no site carries two
    #     byte-identical class rivals.
    if _cid is not None:
      SPEC_TESTS.append({
        "id": _cid,
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _impl,
                        _impl.replace(f"buildVia {_disp}", "buildVia 0", 1)),
        "refinement": f"the faithful counterpart dispatches the base-bound factory at "
                      f"this construction site rather than its own {_role}, so a "
                      f"derived-class result is minted as the base class on every input "
                      f"the operation accepts. The failing scenario reaches this site on "
                      f"the derived class with an accepted input and asserts the result "
                      f"is of that class => it would NOT resolve.",
        "rationale": f"REJECT from `<guard> = true → out.map (·.classId) = some "
                     f"{_role}`: base dispatch gives result class 0, ≠ {_role} whenever "
                     f"it is a derived class. Refuted at a derived-class input the "
                     f"operation ACCEPTS.",
        "witness": _refuse_witness(_nm, _acc[0], _acc[1], _unfold),
      })
    # (b) the refusal DROPPED: an object minted for an input this operation
    #     refuses outright. This is the rival the round-2 repair made refutable —
    #     while the site was total, this impl WAS the frozen spec's own shape.
    SPEC_TESTS.append({
        "id": f"weak-{_nm}-builds-refused-input",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _impl,
                        f"    let r ← buildVia {_disp} ({_map} {_args})\n"
                        "    return some r"),
        "refinement": "the faithful counterpart drops the guard and constructs an object "
                      "for an input the real operation refuses outright, substituting a "
                      "value for the refusal. Both the FAIL_TO_PASS scenario and the "
                      "PASS_TO_PASS scenario reach this site on exactly such an input "
                      "and require the refusal (they assert it, and the assertion is "
                      "what stops the walk); an impl that produces an object there "
                      "fails them => it would NOT resolve.",
        "rationale": "REJECT from `<guard> = false → out = none`: the unguarded impl "
                     "returns `some _` on the refused sub-domain. Refuted at an input "
                     "the operation refuses (differing extents / an ill-formed vector).",
        "witness": _refuse_witness(_nm, _ref[0], _ref[1], _unfold),
    })

# (c) The opposite failure on the same clause pair: refuse EVERYTHING, so an
#     accepted input gets nothing. Attacks the accepted-branch clauses from the
#     other side, so the two directions of the guard are both pinned and a
#     vacuously-refusing impl cannot pass by never constructing anything.
SPEC_TESTS.append({
    "id": "weak-conjugateSelf-refuses-everything",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _refuse_impl(_PAIR_GUARD, "conjugateContents",
                                        _PAIR_ARGS, "self.classId"),
                    "    return none"),
    "refinement": "the faithful counterpart refuses every input, including the ones the "
                  "real operation accepts — it raises (or returns nothing) instead of "
                  "constructing the combination. The scenario combines two operands of "
                  "equal extent and asserts an object of the derived class comes back "
                  "=> it would NOT resolve.",
    "rationale": "REJECT from `sameExtent ... = true → out.map (·.contents) = some "
                 "(conjugateContents ...)`: the impl returns `none` there, and `none.map "
                 "_ = none ≠ some _`. Refuted at an ACCEPTED pair (equal extents), at a "
                 "third operand point (contents [3]/[4], classId 7).",
    "witness": _refuse_witness("conjugateSelf",
                               "{ contents := [3], classId := 7 } "
                               "{ contents := [4], classId := 7 }", None, "sameExtent"),
})

# (d) `generateFor` constructs from the ambient generator state as well as the
#     extent. An impl that ignores the state models a generator that returns the
#     same value for every draw of a given extent.
SPEC_TESTS.append({
    "id": "weak-generateFor-ignores-entropy",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE,
        "    let r ← buildVia cls (generatedContents n entropy)\n    return r",
        "    let r ← buildVia cls (generatedContents n 0)\n    return r"),
    "refinement": "the faithful counterpart ignores the generator state and constructs "
                  "the same value for every draw of a given extent — a deterministic "
                  "generator. The scenario draws repeatedly at one extent and requires "
                  "the draws to range over the whole family, which a state-independent "
                  "generator cannot do => it would NOT resolve.",
    "rationale": "REJECT from `out.contents = generatedContents n entropy`: the impl "
                 "returns `generatedContents n 0`, which differs wherever the state "
                 "matters. Refuted at `cls=7, n=3, entropy=1` under the single "
                 "hypothesis `generatedContents 3 1 ≠ generatedContents 3 0` "
                 "(satisfiable — one assumption relating two applications of one opaque "
                 "map; the gate's consistency probe confirms it, exit 1).",
    "witness": _tester("generateFor") +
               "example (h : generatedContents 3 1 ≠ generatedContents 3 0) :\n"
               "    generateForTester 7 3 1 = false := by\n"
               "  simp [generateForTester, generateForExec, NonDetT.run, generateFor, "
               "buildVia]\n"
               "  intro hc\n"
               "  exact h hc.symm\n",
})

# Positive control for the REFUSING shape (soundness): all three sites
# re-expressed without the shared primitive — the guard named in a local and the
# result object built directly. Still correct, so it must verify; if it rejects,
# the three refusal contracts are SPEC-TOO-STRONG (in particular the `out = none`
# clause would not be jointly satisfiable with the accepted-branch clauses).
SPEC_TESTS.append({
    "id": "pos-refusing-reshaped",
    "kind": "soundness",
    "expect": "verify",
    "module": _pos_refusing(),
    "rationale": "a correct refusing site that names its guard in a local and builds the "
                 "result object directly (bypassing the shared primitive) still returns "
                 "`some` with the dispatch class and this site's value map exactly on the "
                 "accepted inputs, and `none` exactly on the refused ones — so all three "
                 "ensures of all SIX refusing sites hold simultaneously. If it rejects => "
                 "SPEC-TOO-STRONG.",
})

# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases over TWO
# contracted functions (make ≙ the shared primitive; combine ≙ the binary
# product), plus an AXIOM lane. This bundle WIDENS the carrier: it models the
# same primitive PLUS every construction site the fix threads (18 methods over
# one primitive), because the failing scenario re-runs an interacting set of
# sites. The two nagini functions therefore map onto {the primitive, a
# representative instance site (composeProduct ≙ combine), a representative
# target site (foldOver)}, and each nagini rival is re-aimed at the corresponding
# clause here.
#
#   nagini case                         -> here
#   ---------------------------------------------------------------------
#   pos-make-inline                     -> pos-primitive-reshaped        PORTED
#   pos-combine-inline                  -> pos-site-inlined              PORTED
#   admiss-combine                      -> admiss-family-nondegenerate   RE-AIMED
#   frame-combine-self-kind-write       -> (mechanism vacuous; behaviour
#                                          attacked by weak-primitive-drops-class
#                                          + weak-site-unthreaded)       RE-AIMED
#   frame-make-array-write              -> (mechanism vacuous; content behaviour
#                                          attacked by weak-primitive-drops-content
#                                          + weak-site-content-drop)     RE-AIMED
#   partial-make-collapse-kind1         -> weak-primitive-collapse-one   PORTED
#   partial-combine-right-family        -> weak-site-right-operand       PORTED
#   partial-combine-content-drop        -> weak-primitive-drops-content
#                                          + weak-site-content-drop      PORTED (split)
#   AXIOM ax-ref-af_new-mul-soundness   -> (none)                        DROPPED (G-AX)
#
# ADDED (2, by audit — gaps the ported set left unattacked):
#   weak-site-operand-order            argument order of a site's value map
#   weak-target-site-payload-dispatch  wrong-reference on the TARGET clause
#   Both were confirmed with the real verifier (module rejected; witness holds of
#   the rival, fails on the frozen solution, consistency probe fails).
#
# ADDED (4, by the G-PANEL-2 spec repair — these are the cases the repaired
#   successor obligations make expressible; before it, the first was UNREFUTABLE
#   and the other two attacked a clause that did not exist):
#   weak-step-alt-delegates                     one order's successor served
#                                               where the other's is asked for
#   weak-stepSelf-fabricates-when-exhausted     an object produced for an operand
#   weak-stepAltSelf-fabricates-when-exhausted  that has no successor (per order)
#   pos-step-partial-reshaped                   soundness control for the partial
#                                               shape (must verify)
#   Each was confirmed with the real verifier on all three legs (module rejected;
#   witness holds of the rival and fails on the frozen solution; consistency
#   probe fails), and the positive control verifies.
#
# ADDED (9, by the SECOND G-PANEL-2 spec repair — the refusing sites and the
#   generator state. Before it, the first three rivals were the frozen spec's OWN
#   impl shape (so unrefutable), the fourth attacked a clause that did not exist,
#   and the fifth was inexpressible because the value binder was absent):
#   weak-conjugateSelf-builds-refused-input   an object minted for an input the
#   weak-bracketSelf-builds-refused-input     operation refuses outright (one per
#   weak-fromVectorFor-builds-refused-input   refusing site)
#   weak-conjugateSelf-refuses-everything     nothing produced for an ACCEPTED
#                                             input (the other direction)
#   weak-generateFor-ignores-entropy          a state-independent generator
#   pos-refusing-reshaped                     soundness control for the refusing
#                                             shape (must verify)
#   plus the three `weak-site-{conjugateSelf,bracketSelf,fromVectorFor}` class
#   rivals RE-AIMED at the reshaped impl: same case id, same clause, same intent,
#   now stated on the accepted branch. No case id was dropped by the reshape.
#   Each was confirmed with the real verifier on all three legs (module rejected;
#   witness holds of the rival and fails on the frozen solution; each conditioned
#   witness's consistency probe fails), and the positive control verifies.
#
# ADDED (3, by the THIRD G-PANEL-2 spec repair — the left-divide, the fold and
#   the third index variant. Before it these three sites were modeled as TOTAL, so
#   each of these rivals WAS the frozen spec's own impl shape and was therefore
#   unrefutable):
#   weak-divideSelf-builds-refused-input      an object minted for an input the
#   weak-foldOver-builds-refused-input        operation refuses outright (one per
#   weak-rankedThirdFor-builds-refused-input  newly-partial site)
#   plus the three class rivals RE-AIMED at the reshaped impls under their existing
#   ids (`weak-site-divideSelf`, `weak-site-rankedThirdFor`, and the fold's
#   `weak-target-site-unthreaded` / `weak-target-site-payload-dispatch`, whose
#   witnesses now carry the accepted-branch hypothesis), and `pos-refusing-reshaped`
#   widened to reshape all SIX refusing sites at once. No case id was dropped.
#
# ADDED (1, carrier widening): weak-target-site-unthreaded. Both nagini rivals
#   are instance-shaped (`out.classId = self.classId`). This carrier also carries
#   the target-dispatched clause (`out.classId = cls`), on which the failing
#   scenario's classmethod construction sites depend; without a rival attacking
#   it, that entire second site shape would be defended (by the positive controls
#   verifying) but never attacked, and a rival un-threading only a classmethod
#   site would go uncaught.
#
# RE-AIMED (frame-mutation, ×2): the sibling writes a read-only half-permission
#   input (`self.kind = 0`, `array[0] = 0`) to trip INSUFFICIENT PERMISSION. This
#   backend is referentially transparent, has no heap or aliasing, and declares
#   no `mut` binder — there is no read-only input to overwrite and no substitute
#   probe to fabricate, so the PERMISSION MECHANISM is vacuous. The UNDERLYING
#   wrong behaviour each frame rival relies on (minting onto the fixed base class;
#   corrupting the contents) is still attacked directly — via the value-level
#   primitive drop / site-unthreaded rivals and the content-drop rivals — so no
#   wrong behaviour goes untested; only the (non-existent) mechanism is dropped.
#   Not fabricated as a permission case.
#
# RE-AIMED (admissibility): the sibling establishes the read-only half-permission
#   inputs are usable and a normal return reachable. No permissions and no
#   `require` clause here, so that probe is vacuous; re-aimed at the residual
#   total-domain risk (post-image non-degenerate at the derived family), exactly
#   as the astropy sibling was.
#
# DROPPED (AXIOM lane): this bundle consumes no `axiom` (the opaque value maps are
#   G-AX A-references, not consumed contracts). The axiom lane is G-AX's job; this
#   gate ignores AXIOM_TESTS regardless.
#
# DIVERGENCE / NON-TERMINATION: the sibling carries no such case for this
#   instance, so there is nothing to port. The disposition is REJECTED-BY-SPEC
#   and NOT EXPRESSIBLE as a witnessed case. Two earlier claims in this block are
#   both corrected: "a diverging impl cannot be written (every method's impl is a
#   total `do` block that must return)" is false, since a `while` loop does
#   elaborate in an impl region; and "a loop with a measure annotation verifies"
#   is also false: under the total scope the loop owes a descent obligation, and a measure
#   that does not decrease leaves it unsolved (`case «decreasing_1: i» ... ⊢
#   1 < 1`). A THIRD earlier claim is corrected by the audit: the inexpressibility
#   was recorded as "the rejection lands at the `method`, so the rival's module
#   never compiles and no witness can elaborate against it". That is true only of
#   the NO-MEASURE shape. On the MEASURE-BEARING shape the method elaborates (the
#   sole error is at `prove_correct`) and `example : True := trivial` DOES elaborate
#   against the rival; what blocks a case there is that the loop's residual
#   `forIn Lean.Loop.mk` / `rep` term is kernel-irreducible, so every
#   discriminating claim stalls (eight shapes built, all fail; `native_decide` is
#   the one shape that separates the subjects, and it does so by diverging). See
#   the DIVERGENCE bullet in the module docstring for the two shapes and their
#   measured outcomes, and the RETRACTED note at the end of this file for the build
#   that withdrew the escalation. This block previously contradicted the docstring
#   on the same question; both now say the same measured thing.
#
# COVERAGE. Every one of the 18 methods is now DEFENDED (the four positive
#   controls verify the whole file, discharging every method's proof) and
#   ATTACKED (every non-primitive site carries a class-clause reject rival; the
#   primitive carries class + contents rivals; each of the two PARTIAL successor
#   sites carries a class rival AND a rival against its own `out = none` clause,
#   and the alternative order additionally carries the delegation rival against
#   its own value map; each of the six REFUSING sites carries a class rival on
#   its accepted branch AND a rival that drops its refusal, one of them also a
#   rival that refuses everything, and `generateFor` additionally carries a rival
#   that ignores the generator state). Binders varied by the reject
#   witnesses on the multi-rival obligations: buildVia.builtOn {5,1,7},
#   buildVia.value {[1],[2]}; composeProduct.self.classId {2,3,5}, .other.classId
#   {0,2,3,5}; the successor sites' operand over classId {2,3,5} × contents
#   {[1],[4]} and over both definedness branches. Across sites the dispatch-class
#   binder ranges over {2,3,4,5,6,7,8,9}.
#
# pts=1 per single-rival site — a DELIBERATE, not-a-gap disposition. The
#   coverage tool flags each narrow site obligation ("says nothing about the
#   dependence on 'self'/'n'/'extent'/…") because it carries exactly one reject
#   witness, so no binder moves WITHIN that obligation. But each such site's SOLE
#   behaviour-under-change is its class clause (`out.classId = self.classId` /
#   `= cls`), whose only load-bearing binder is the dispatch class — which the
#   rival drops to the base tag 0 and the witness discriminates at a derived tag.
#   The site's OTHER binders (contents, and the numeric/vector parameters `n`,
#   `extent`, `rank`, `vec`, `m`, `s`, …) feed ONLY the opaque `*Contents` value
#   clause, which is an A-REFERENCE (same map on both sides, value never pinned),
#   NOT the behaviour the fix changes: a rival mishandling one of them models a
#   value-computation bug the spec deliberately does not pin, and directive 3
#   forbids modeling a different algorithm. The contents clause IS attacked, once
#   per shape, on the primitive (`weak-primitive-drops-content`, transparent) and
#   on `composeProduct` (`weak-site-content-drop`, opaque + conditioned) — since
#   every site's contents passthrough is the identical `buildVia _ value`
#   structure, that is representative. So the flagged value binders are genuinely
#   irrelevant to each site's modeled behaviour; per the coverage rubric this is
#   the "binder genuinely irrelevant to the modeled behavior" exemption, stated
#   here rather than papered over with value-corrupting rivals that would test a
#   bug outside the defended surface.
#
#   That exemption is a claim about RELEVANCE, not about spec strength, and the
#   audit checked the two do not get confused. The spec is NOT weak on those
#   binders: rivals that mishandle exactly the flagged value parameters were built
#   and every one is REJECTED (exit 1, `unsolved goals`) — `fromUnit` with its two
#   payload args transposed, `rankedThirdFor` with its two numeric params
#   transposed, `scheduleFor` with its three params rotated, `extentFor` ignoring
#   `extent`, `powerSelf` ignoring its exponent, `fromVectorFor` reversing `vec`,
#   the instance site substituting `self.contents` for the composition and another
#   truncating it. So declining to ship those 8 as cases is a scope decision about
#   what the modeled behaviour IS (directive 3), not a gap the spec would miss;
#   they are recorded here as measured rather than left as an argument.
#
#   AUDIT CORRECTION — that exemption is sound for the DISPATCH-class behaviour
#   but was overstated as "no wrong impl of the modeled behaviour escapes". Two
#   escapes were found and closed by adding rivals: the ARGUMENT ORDER of a
#   site's value map (`weak-site-operand-order`, an instance-clause content rival
#   that transposes the two operands — the pre-existing content rival replaced
#   the contents wholesale, so order was unpinned) and a payload-derived DISPATCH
#   class on the target clause (`weak-target-site-payload-dispatch` — the
#   wrong-reference shape existed only on the instance clause).
#
#   A further escape was escalated from here as a FROZEN SPEC defect (`stepSelf`
#   and `stepAltSelf` carried BYTE-IDENTICAL contracts, both stating their
#   contents over the SAME opaque map `stepContents`) and is now CLOSED by the
#   spec repair: the alternative order has its own map, both sites are partial,
#   and the escape ships here as `weak-step-alt-delegates` plus the two
#   `...-fabricates-when-exhausted` rivals. See the CLOSED note at the end of
#   this file. A second escape was escalated by an earlier revision (a loop whose
#   declared `decreasing` measure is never checked, letting a non-terminating
#   impl discharge every clause vacuously) and is RETRACTED: that shape is
#   rejected on the descent goal itself. See the RETRACTED note at the end of
#   this file for the build.
#
# ---------------------------------------------------------------------------
# CLOSED: "SPEC DEFECT #1" (two obligations stated over the same opaque map).
# Escalated from this file when the repair was outside this lane; the frozen spec
# has since been repaired, and the escape now ships as three reject cases. Kept
# as a record, with what was measured on both sides of the repair.
#
# WHAT WAS WRONG. Two modeled obligations were the SAME obligation: `stepSelf`
# and `stepAltSelf` had byte-identical contracts modulo the method name,
#
#     ensures out.classId = self.classId
#     ensures out.contents = stepContents self.contents      <-- the SAME symbol
#
# while mapping.md/refinement.md bind the two sites to DIFFERENT repo
# computations (the two distinct successor orders). The repo's own PASS_TO_PASS
# scenario asserts they are different functions — it advances one operand by each
# rule and requires the two orders to enumerate the operands differently. So one
# symbol stood in for two computations the tests distinguish, and the spec
# entailed that the two orders agree everywhere. Re-derived against the worktree
# at `base_commit` with `patch.diff` applied: the two orders disagree on 4 of 6
# operands at extent 3, 19 of 24 at extent 4, 105 of 120 at extent 5 — e.g. the
# operand [0,2,1] has lexical successor [1,0,2] but alternative-order successor
# [2,0,1]. Each order is also PARTIAL, on different operands: the lexically last
# operand ([2,1,0] at extent 3) has no lexical successor, while [1,0,2] is the
# one with no alternative-order successor; the real callees return nothing there
# rather than an object.
#
# Consequence, measured against the pre-repair spec: a variant whose
# `stepAltSelf` simply DELEGATES to `stepSelf` (`let r ← stepSelf self; return
# r`) VERIFIED (exit 0), though it models a site computing the wrong successor
# order, so a `verify` stamp did not imply the P2P scenario passes. It could not
# be shipped as a reject case — it was not rejected, and a witness refuting it
# would have had to distinguish two terms the spec said were equal.
#
# Isolated to the shared symbol, not to delegation, by three controls that
# delegate BACKWARDS (so no forward-reference artifact) to a site whose map
# DIFFERS — each rejects semantically with `unsolved goals`:
#   conjugateSelf -> reverseSelf   exit 1
#   rankedAltFor  -> rankedFor     exit 1
#   bracketSelf   -> stepSelf      exit 1
# and by the same delegation in the other direction (`stepSelf` -> `stepAltSelf`,
# exit 1, but only for the unrelated `WPGen sorry` forward-reference reason, so
# it is not counted as evidence).
#
# THE REPAIR (in the frozen spec, region-identical across all four variants, so
# `markers.same_spec` still holds pairwise). Two obligations were ADDED and none
# was relaxed:
#   * a second opaque value map `stepAltContents`, over which `stepAltSelf`'s
#     contents clause is now stated — the two orders are no longer asserted equal;
#   * per-order opaque definedness predicates `stepDefined` / `stepAltDefined`,
#     and `Option Obj` results, so each site must return `none` exactly where its
#     order runs out (`ensures <pred> self.contents = false → out = none`) — a
#     clause that did not exist before and that no earlier rival could violate.
# The class obligation is unchanged in content, now stated on the branch where a
# successor exists. `Obj` additionally derives `DecidableEq`, which the tester
# machinery needs to decide `out = none` / `out.map _ = some _`.
#
# WHAT THE REPAIR BUYS, measured (all serialized, real verifier):
#   * `weak-step-alt-delegates` — the escape above — is now REJECTED (exit 1),
#     and its witness discriminates (rival exit 0; frozen solution exit 1 with
#     `⊢ False` unsolved under `hd`, `ha`, `hne`; consistency probe exit 1).
#   * `weak-stepSelf-fabricates-when-exhausted` and
#     `weak-stepAltSelf-fabricates-when-exhausted` attack the new `out = none`
#     clause on each order: modules rejected (exit 1), witnesses discriminate
#     (rival 0 / frozen 1 / probe 1).
#   * the two class rivals are unchanged in intent and still rejected, with their
#     witnesses now conditioned on the definedness branch they attack.
#   * `pos-step-partial-reshaped` verifies (exit 0), so the added clauses are not
#     too strong: a correct impl that names the definedness decision in a local
#     and builds the result object directly still satisfies all three.
#   * the pre-patch variants still FAIL (exit 1): `Solution_prepatch.lean`
#     (`⊢ 0 = builtOn`), `Solution_prepatch_classmethod.lean`
#     (`ensures_2 : x.classId = 0 ⊢ x.classId = cls`),
#     `Solution_prepatch_instance.lean` (`⊢ x.classId = self.classId`).
#   * non-vacuity of the new symbols: probes asserting `False` from
#     `stepContents [1] ≠ stepAltContents [1]`, from `stepDefined [1] = true`,
#     from `stepDefined [4] = false`, and from all six re-derived repo facts at
#     once each leave `⊢ False` unsolved (exit 1) — the hypotheses the witnesses
#     use are satisfiable, so no case is refuting a rival on an empty domain.
# ---------------------------------------------------------------------------
#
# ---------------------------------------------------------------------------
# RETRACTED: "SPEC DEFECT #2" (a declared loop measure is not checked to
# decrease). An earlier revision of this file escalated this as a second frozen
# spec defect. It does NOT reproduce, and the retraction is measured, not
# argued. Kept as a retraction rather than deleted, because the claim is the
# kind a reader would otherwise carry forward from an earlier copy.
#
# The claim was that this loop, spliced into the shared primitive's impl region,
# VERIFIES while returning a value that violates both of the primitive's
# `ensures` clauses:
#
#     let mut i : Nat := 1
#     while i > 0
#       invariant True
#       done_with i = 0
#       decreasing i
#     do
#       pure ()                          -- `i` is never modified
#     return { contents := [], classId := 0 }     -- both clauses violated
#
# Rebuilt, with the frozen spec view intact and each `prove_correct` reduced to
# a bare `loom_solve` so no tactic script can mask the verdict: it is REJECTED,
# exit 1, on the descent obligation itself.
#
#     unsolved goals
#     case «decreasing_1: i» ...
#     ⊢ 1 < 1
#
# and the increasing variant (`i := i + 1` in the body) is likewise REJECTED
# with `case «decreasing_1: i» ... ⊢ i + 1 < i`. So the strict-decrease side
# condition IS generated and IS left unsolved. A `decreasing` annotation is not
# a way to silence the check; it is the thing the check is about.
#
# Mechanism, from the Loom source rather than inferred. `set_option
# loom.semantics.termination "total"` does not merely record an option: its
# elaborator opens the matching scope (`Loom/MonadAlgebras/WP/Options.lean`,
# `| `("total") => openScope `TotalCorrectness`). This file additionally writes
# `open TotalCorrectness`, so both lines agree. `TotalCorrectness`'s
# `WPGen.forWithInvariantLoop` takes `measure : β → Nat` and emits the
# `measure b' < measure b` conjunct on the yield branch; the
# `PartialCorrectness` twin is the one that takes a measure and never mentions
# it, and nothing in this file opens that scope. The earlier measurement was
# taken when the corpus was mid-flip and a bundle could read `"total"` while a
# later `open` re-selected partial scope; both lines now move together.
#
# Consequence for this battery: nothing to escalate for this class, and nothing
# to ship. A diverging rival is REJECTED, so it is not a hole; it is also not
# expressible as a G-PBT reject case, because the rejection lands at the
# `method` itself and the rival's module never compiles, so no witness can
# ELABORATE against it (the gate's own `_check_witness` returns
# `witness-unproven` even for `example : True := trivial`, which forces
# MALFORMED-TESTS rather than a pass). That is the DIVERGENCE class note above,
# and it is a property of the witness contract, not of the spec.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# CLOSED: "SPEC DEFECT #3" (three operations modeled as TOTAL that the real ones
# REFUSE on a test-reached sub-domain, and one modeled as a function of its
# extent alone that the real one draws from the generator state). Escalated by
# the G-PANEL-2 faithfulness audit against the previous frozen bytes; the frozen
# spec has since been repaired and the escape now ships as the nine cases listed
# in the ADDED block above. Kept as a record, with what was measured.
#
# WHAT WAS WRONG. `conjugateSelf`, `bracketSelf` and `fromVectorFor` returned a
# plain `Obj`, so the spec asserted an object is produced for EVERY input,
# including the ones their real counterparts refuse outright:
#
#     conjugateSelf / bracketSelf : a PAIR whose extents differ is refused
#     fromVectorFor               : an ill-formed offset vector is refused
#
# Re-derived against the worktree at `base_commit` with `patch.diff` applied, on
# the derived class the failing scenario uses: combining an operand of extent 7
# with one of extent 0 refuses (both sites), and the offset vector [0,2] refuses.
# Those are the LITERAL inputs the tests reach — the scenario asserts the refusal
# at each of the three sites, and it is BOTH a PASS_TO_PASS test and the body the
# FAIL_TO_PASS test re-runs under its subclass. Making one of those sites total in
# the way the old spec permitted (drop the guard, pad the shorter operand, keep
# the threaded construction) satisfies every frozen `ensures` yet makes that test
# FAIL. So `verify ⟹ resolved` did not hold: an implementation could satisfy the
# frozen spec and not resolve the instance. The battery could not catch it either,
# because the totality WAS the frozen shape: the three
# `...-builds-refused-input` rivals below are byte-identical to what the frozen
# impl regions used to contain.
#
# Separately, `generateFor` was `(cls) (n) → Obj` with `out.contents =
# generatedContents n` — a function of the extent ALONE, which entails that two
# constructions of the same extent carry the SAME contents. Its real counterpart
# draws from the ambient generator state, so successive draws of one extent
# differ; the spec-permitted deterministic generator is a different function.
#
# THE REPAIR (in the frozen spec, region-identical across all four variants, so
# `markers.same_spec` still holds pairwise). Obligations were ADDED and none was
# relaxed:
#   * a transparent extent test `sameExtent (a b : List Nat) : Bool` and an opaque
#     `vectorValid : List Nat → Bool`, and the three sites now return
#     `Option Obj` under the three-clause contract, so each must produce NOTHING
#     exactly where its real counterpart refuses (`<guard> = false → out = none`)
#     — a clause that did not exist before;
#   * `generateFor` gains the `entropy` binder and its contents clause is stated
#     over `generatedContents n entropy`, so the value may depend on the
#     generator state and an impl ignoring it no longer satisfies the clause.
# The class obligations are unchanged in content, now stated on the branch where
# the operation accepts its input.
#
# WHAT THE REPAIR BUYS, measured (all serialized, real verifier, exit codes as
# recorded by `scripts/lean_verify.sh <file> 600`):
#   * the frozen solution VERIFIES (exit 0) and all three pre-patch variants still
#     FAIL (exit 1) with `same_spec=True` against it: `Solution_prepatch.lean`
#     (`⊢ 0 = builtOn`), `Solution_prepatch_classmethod.lean`
#     (`⊢ x.classId = cls`), `Solution_prepatch_instance.lean`
#     (`⊢ x.classId = self.classId`).
#   * the three `...-builds-refused-input` rivals — the old frozen shape — are now
#     REJECTED (exit 1) on the `out = none` clause; the three class rivals are
#     rejected on the accepted-branch class clause (`ensures_3`);
#     `weak-conjugateSelf-refuses-everything` on the accepted-branch contents
#     clause; `weak-generateFor-ignores-entropy` on `out.contents =
#     generatedContents n entropy`.
#   * every one of those nine witnesses elaborates against its own rival (exit 0)
#     and FAILS against the frozen solution (exit 1), and the three conditioned
#     witnesses' consistency probes each leave `⊢ False` unsolved (exit 1), so no
#     rival is refuted on an empty domain.
#   * `pos-refusing-reshaped` VERIFIES (exit 0) — the three refusal contracts are
#     jointly satisfiable by a correct impl that names each guard in a local and
#     builds the result object directly, bypassing the shared primitive. So the
#     added clauses are not too strong.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# CLOSED: "SPEC DEFECT #4" (the SAME defect shape as #3, at three FURTHER sites
# the #3 repair did not reach). Escalated by the G-PANEL-2 faithfulness audit
# against the post-#3 frozen bytes; the frozen spec has since been repaired and
# the escape now ships as the three `...-builds-refused-input` cases listed in the
# ADDED block above. Kept as a record, with what was measured.
#
# WHAT WAS WRONG. `divideSelf`, `foldOver` and `rankedThirdFor` returned a plain
# `Obj`, so the spec asserted an object is produced for EVERY input, including the
# ones their real counterparts refuse:
#
#     divideSelf     <- mul_inv                : `_af_rmul(_af_invert(a), b)`
#                                                indexes `a` at `b`'s entries, so a
#                                                RIGHT operand of greater extent
#                                                raises IndexError
#     foldOver       <- rmul_with_af           : `_af_rmuln` raises ValueError on
#                                                the EMPTY sequence and IndexError
#                                                on a sequence it cannot compose
#     rankedThirdFor <- unrank_trotterjohnson  : assigns `perm[k]` without reducing
#                                                the index into range first, so an
#                                                out-of-range index raises IndexError
#
# Re-derived by EXECUTING the worktree at `base_commit` with `patch.diff` applied,
# on both `Permutation` and a subclass (an exhaustive per-site sweep over the same
# operand pool the conformance check uses):
#   * `divideSelf` refused 71 of 100 pairs, and its refusal predicate is EXACTLY
#     `len(other) > len(self)` — 0 mismatches over all extent pairs 0..5, which is
#     why it is modeled with a TRANSPARENT `fitsWithin` rather than an opaque one.
#   * `foldOver` refused 581 of 1111 sequences (1 ValueError on the empty one, 529
#     IndexError). Its accepted set is NOT "non-empty with non-increasing extents"
#     (48 mismatches of 1111 — e.g. the extent pattern [0,1,0] is accepted), so it
#     is modeled OPAQUELY.
#   * `rankedThirdFor` refused 56 of 65 index pairs, and its accepted set is NOT
#     `rank < extent!` (33 mismatches): every index is accepted at extents 0, 1 and
#     5, but only 0..3 at extent 2, 0..14 at extent 3 and 0..71 at extent 4. Not a
#     plain comparison of the two parameters, so it too is modeled OPAQUELY.
# The two OTHER index variants were checked in the same sweep and are TOTAL
# (`unrank_lex` reduces by `rank % new_psize`, `unrank_nonlex` by `r % ifac(n)`),
# so `rankedFor` and `rankedAltFor` were deliberately LEFT total: the asymmetry
# between the three is real and flattening it would be unfaithful the other way.
#
# Consequence, measured against the pre-repair spec: exactly as for #3, an impl
# could pad or truncate to make one of these sites total, satisfy every frozen
# `ensures`, and fail the scenario that requires the refusal — so `verify ⟹
# resolved` did not hold. And the battery could not catch it, because the totality
# WAS the frozen shape: each `...-builds-refused-input` rival below is
# byte-identical to what the frozen impl region used to contain.
#
# THE REPAIR (in the frozen spec, region-identical across all four variants, so
# `markers.same_spec` still holds pairwise). Obligations were ADDED and none was
# relaxed: a transparent `fitsWithin (inner outer : List Nat) : Bool` and two
# opaque predicates `foldDefined` / `rankedThirdDefined`, and the three sites now
# return `Option Obj` under the same three-clause contract the other three
# refusing sites use, so each must produce NOTHING exactly where its real
# counterpart refuses. The class obligations are unchanged in content, now stated
# on the branch where the operation accepts its input — which is what keeps the
# repair from weakening the spec: the behaviour-under-change (the dispatch class)
# is still pinned on every input the real operation accepts, and the previously
# passing G-PANEL-1 attack set still re-runs against it.
# ---------------------------------------------------------------------------

# AXIOM_TESTS: dropped (see above).
AXIOM_TESTS = []
