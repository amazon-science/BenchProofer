"""properties.py — G-PBT falsification battery for astropy__astropy-14539 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is
changed, both of which the consumer spec view elides — so ``markers.same_spec``
holds and the ``prove_correct`` obligation survives) and swaps in a candidate
implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method over a single obligation).

  diffVLAColumn (fmt, col, rows)   ensures out = diffSpec fmt col rows

A column is CLASSIFIED by its format descriptor (``isVLA fmt`` — does the
descriptor carry a variable-length marker) and the comparison is ROUTED
accordingly: a classified-variable-length column is compared row by row
(``rowWiseOutcome``), every other column by the generic element-wise route
(``genericOutcome``). Each route produces the per-row difference verdict when it
can run on the column's ACTUAL element kind and otherwise lets a failure escape:

  * the generic route fails on a column whose elements are themselves
    variable-length sequences with some multi-element row
    (``col.varLength && anyMulti rows``);
  * the row-wise numeric route fails on a column whose elements are not
    numerically comparable (``col.numComparable = false``, e.g. a text column).

The single load-bearing clause ``out = diffSpec fmt col rows`` pins the WHOLE
routing decision AND the completing/escaping outcome of the chosen route. The
three inputs are all read-only (no ``mut`` binder anywhere): ``fmt`` selects the
route, and ``col`` (its two intrinsic kind flags) and ``rows`` decide whether
the chosen route completes.

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The class exists on nagini because
    a read-only input may carry a fractional heap permission an impl can
    overwrite. Lean and Velvet are referentially transparent: every parameter is
    an immutable value (this bundle declares no ``mut`` binder), there is no heap
    and no aliasing, so there is no read-only input to mutate and no substitute
    probe to build. Reported as an omission (module footer), not fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image ``diffSpec`` is a total, fully
    unfolded function of the method's own arguments (``diffSpec``, ``isVLA``,
    ``rowWiseOutcome``, ``genericOutcome``, ``anyMulti``, ``rowResult`` are all
    concrete ``def``s in the ``pure`` region; the ``axioms`` region declares no
    ``axiom`` — there is no opaque answer key to echo). So there is no WRONG echo
    to build; instead we carry honest cheapest-reshape POSITIVE CONTROLS.
  * ROUTING / CONTROL-FLOW-EFFECT — the heart of this surface. The observable is
    which route a column is sent down, and whether that route completes on the
    column's element kind. The rivals below misclassify a sub-domain of columns
    and thereby send them down a route their element kind does not support, so
    the chosen route lets a failure escape where the post-image demands a
    completed verdict.
  * PARTIAL-DOMAIN / VALUE — a rival right on part of the format domain but
    diverging on a sub-domain (recognising one variable-length marker but not
    the other; recognising none; recognising too many).

WITNESS PLACEMENT. Rivals do not share a refutation point unless they fail there
for the same reason. The two marker-specific rivals are refuted at MIRROR points
(one at the marker each recognises but the other does not) so neither pins the
format input; the always-one-route rivals are refuted on the sub-domains that
separate them — one at a variable-length column with a multi-element row (where
the generic route escapes), the other at a not-numerically-comparable column
(where the row-wise route escapes). The three input binders — the format
descriptor, the column's two intrinsic kind flags, and the rows — are all moved
across the reject witnesses rather than held fixed.

AXIOM lane: DROPPED. The axiom lane is G-AX's job and the gate ignores
``AXIOM_TESTS`` regardless. The nagini sibling's three A-reference probes
(is-vla soundness/containment, row-granular-count soundness, element-wise
applicability) are exactly what axiom_check.py / G-AX check here; nothing in
that lane belongs in this spec-lane manifest.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-14539"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the routing block, wholly inside the one impl region
# ---- and unique in Solution.lean (the `let result`/`return result` wrapper does
# ---- not occur in the `pure` region's `diffSpec` def). Both facts asserted at
# ---- load by _swap. ----
_A_IMPL = (
    "    let result : Except DiffErr (List Bool) :=\n"
    "      if isVLA fmt then\n"
    "        rowWiseOutcome col rows\n"
    "      else\n"
    "        genericOutcome col rows\n"
    "    return result\n"
)

# ---- proof-body anchor. The `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view (only the header survives), so a positive control that
# ---- reshapes the impl may retune its tactic script without touching the spec
# ---- or dropping the obligation. ----
_T_PROOF = (
    "prove_correct diffVLAColumn by\n"
    "  loom_solve\n"
    "  simp_all [diffSpec]\n"
)


def _swap2(a_new, t_new):
    """Reshape the impl region AND retune the tactic body in one variant."""
    return _swap(_swap(_BASE, _A_IMPL, a_new), _T_PROOF, t_new)


# ---- witness preamble. The spec here is a `method` CONTRACT, not a bare
# ---- predicate, so a witness reaches it through Velvet's own tester machinery:
# ---- `diffVLAColumnTester args = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped, so no tactic script
# ---- can mask the verdict. `prove_postcondition_decidable_for` needs equality
# ---- of the report carrier `Except DiffErr (List Bool)` to be decidable, so the
# ---- preamble derives that instance first — an instance, not an assumption (no
# ---- `axiom`/`sorry`/`native_decide`), and the frozen solution rejects the
# ---- witnesses all the same.
_PREAMBLE = (
    "deriving instance DecidableEq for Except\n\n"
    "extract_program_for diffVLAColumn\n"
    "prove_precondition_decidable_for diffVLAColumn\n"
    "prove_postcondition_decidable_for diffVLAColumn\n"
    "derive_tester_for diffVLAColumn\n\n"
)


def _wit(example):
    return _PREAMBLE + example


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the obligation and reshapes only the
    # executable surface; the contract is point-wise, so each reproof stays a
    # branch-split away from the frozen script.
    # =====================================================================
    {
        "id": "pos-route-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: negate the classifier and swap the two routes. The SAME route
        # handles each column kind with the SAME arguments, so the outcome is
        # unchanged on both arms of the classification. The tactic body gains one
        # `cases` on the classifier to reconcile the reordered `if`.
        "module": _swap2(
            "    let result : Except DiffErr (List Bool) :=\n"
            "      if !isVLA fmt then\n"
            "        genericOutcome col rows\n"
            "      else\n"
            "        rowWiseOutcome col rows\n"
            "    return result\n",
            "prove_correct diffVLAColumn by\n"
            "  loom_solve\n"
            "  simp_all [diffSpec]\n"
            "  cases isVLA fmt <;> simp_all\n",
        ),
        "rationale": "negating the classifier and swapping the two routes sends "
                     "each column kind down the SAME route with the SAME "
                     "arguments, so `out = diffSpec fmt col rows` holds on both "
                     "arms of the classification; a correct reshape must verify, "
                     "else SPEC-TOO-STRONG on branch order.",
    },
    {
        "id": "pos-route-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the classification to a local boolean, keep the route
        # order. Same value flow, so the frozen tactic script still closes.
        "module": _swap(
            _BASE, _A_IMPL,
            "    let vla := isVLA fmt\n"
            "    let result : Except DiffErr (List Bool) :=\n"
            "      if vla then\n"
            "        rowWiseOutcome col rows\n"
            "      else\n"
            "        genericOutcome col rows\n"
            "    return result\n"),
        "rationale": "binding the classifier to a typed local before routing "
                     "leaves the route choice and each route's outcome "
                     "unchanged, so `out = diffSpec fmt col rows` still holds; a "
                     "correct reshape must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — no method here has a `require` clause, so the usual
    # "a normal input satisfies the precondition" probe is vacuous: nothing
    # could exclude an F2P-shaped column. The residual admissibility risk on a
    # total domain is that the post-image is UNSATISFIABLE / DEGENERATE at the
    # interesting point — a spec no impl can meet reads exactly like a spec every
    # impl meets. So this case discharges an in-region `assert` at two F2P-shaped
    # points: a classified-variable-length, numerically-comparable column with a
    # multi-element row (routed row-wise, completes with the per-row verdict) and
    # a not-classified, not-numerically-comparable column (routed generic,
    # completes). The verifier must establish that the post-image really does
    # demand a COMPLETED verdict on each — not the escaping failure. The
    # surrounding impl is kept verbatim so the method's own obligation still
    # discharges; the assert is live, not decoration (a false claim about the
    # same points leaves an unsolved goal).
    # =====================================================================
    {
        "id": "admiss-routes-complete",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap2(
            "    assert (with_name_prefix `assert\n"
            "      (diffSpec ['Q'] { varLength := true, numComparable := true } "
            "[{ differs := true, multiElem := true }]\n"
            "         = Except.ok [true] ∧\n"
            "       diffSpec ['A'] { varLength := false, numComparable := false } "
            "[{ differs := true, multiElem := false }]\n"
            "         = Except.ok [true]))\n" + _A_IMPL,
            "prove_correct diffVLAColumn by\n"
            "  loom_solve\n"
            "  all_goals\n"
            "    first\n"
            "    | exact ⟨rfl, rfl⟩\n"
            "    | simp_all [diffSpec]\n",
        ),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped points: for a classified-variable-length, "
                     "numerically-comparable column routed row-wise and for a "
                     "not-classified, not-numerically-comparable column routed "
                     "generic, it demands a COMPLETED per-row verdict on each — "
                     "not the escaping failure. The in-region assert must "
                     "discharge (else the obligation is unsatisfiable at the "
                     "interesting point); the impl is kept verbatim so "
                     "`out = diffSpec fmt col rows` still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "weak-route-first-marker-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Recognises only the FIRST variable-length marker, missing the second.
        # A column marked only by the second descriptor is then routed generic;
        # if its elements are variable-length with a multi-element row the
        # generic route escapes where the post-image demands a completed verdict.
        "module": _swap(_BASE, _A_IMPL,
                        "    let result : Except DiffErr (List Bool) :=\n"
                        "      if fmt.contains 'P' then\n"
                        "        rowWiseOutcome col rows\n"
                        "      else\n"
                        "        genericOutcome col rows\n"
                        "    return result\n"),
        "refinement": "this is the pre-patch classification (it recognises only "
                      "one of the two variable-length descriptors). The failing "
                      "tests add a column marked by the OTHER descriptor: its "
                      "elements are variable-length sub-arrays, so the generic "
                      "route it is misrouted to raises on its multi-element rows "
                      "and crashes the comparison — the identical-inputs test "
                      "(which must register no difference on that column) and the "
                      "differing-data test (which must count that column's "
                      "differing rows) both still fail. A faithful counterpart "
                      "that recognises only one marker does NOT resolve.",
        "rationale": "REJECT from `out = diffSpec fmt col rows`: on a column "
                     "marked only by the second variable-length descriptor "
                     "`isVLA fmt` is true (the spec routes it row-wise, which "
                     "completes) yet the impl routes it generic, which escapes on "
                     "its multi-element rows. Refuted at that descriptor, the "
                     "sub-domain the other marker-rival handles correctly.",
        "witness": _wit(
            "example : diffVLAColumnTester ['Q'] "
            "{ varLength := true, numComparable := true } "
            "[{ differs := true, multiElem := true }] = false := by\n  decide\n"),
    },
    {
        "id": "weak-route-second-marker-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Symmetric near-miss: recognises only the SECOND marker, missing the
        # first. Refuted at the MIRROR point of the rival above — a column marked
        # only by the FIRST descriptor — so neither rival pins the format input.
        "module": _swap(_BASE, _A_IMPL,
                        "    let result : Except DiffErr (List Bool) :=\n"
                        "      if fmt.contains 'Q' then\n"
                        "        rowWiseOutcome col rows\n"
                        "      else\n"
                        "        genericOutcome col rows\n"
                        "    return result\n"),
        "refinement": "the mirror of the pre-patch classification: it recognises "
                      "only the OTHER variable-length descriptor. A column marked "
                      "by the first descriptor (a variable-length column present "
                      "in the failing tests) is misrouted to the generic route, "
                      "which raises on its multi-element rows and crashes the "
                      "comparison, so the identical-inputs and differing-data "
                      "tests still fail. A faithful counterpart recognising only "
                      "one marker does NOT resolve.",
        "rationale": "REJECT from `out = diffSpec fmt col rows`: on a column "
                     "marked only by the first variable-length descriptor "
                     "`isVLA fmt` is true (spec routes row-wise, completes) yet "
                     "the impl routes it generic, which escapes on its "
                     "multi-element rows. Refuted at the MIRROR of the rival "
                     "above (the markers exchanged), so the two near-misses carry "
                     "distinct refutation inputs and the format input is varied.",
        "witness": _wit(
            "example : diffVLAColumnTester ['P'] "
            "{ varLength := true, numComparable := true } "
            "[{ differs := true, multiElem := true }] = false := by\n  decide\n"),
    },
    {
        "id": "weak-route-always-generic",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the classification entirely: always the generic route. On any
        # variable-length column with a multi-element row the generic route
        # escapes where the post-image demands a completed verdict.
        "module": _swap(_BASE, _A_IMPL,
                        "    let result : Except DiffErr (List Bool) :=\n"
                        "      genericOutcome col rows\n"
                        "    return result\n"),
        "refinement": "always using the generic element-wise route is the "
                      "maximally-broken classification: every variable-length "
                      "column reaches the generic route and raises on its "
                      "multi-element rows — the exact pre-patch failure, "
                      "generalised — so both failing tests crash. A faithful "
                      "counterpart that never routes row-wise does NOT resolve.",
        "rationale": "REJECT from `out = diffSpec fmt col rows`: the classifier "
                     "is ignored, so a classified-variable-length column with a "
                     "multi-element row (routed row-wise by the spec, completing) "
                     "is instead routed generic and escapes. Refuted at a "
                     "two-row column so the rows input is moved off the "
                     "single-row witnesses above.",
        "witness": _wit(
            "example : diffVLAColumnTester ['Q'] "
            "{ varLength := true, numComparable := true } "
            "[{ differs := false, multiElem := true }, "
            "{ differs := true, multiElem := true }] = false := by\n  decide\n"),
    },
    {
        "id": "weak-route-always-rowwise",
        "kind": "uniqueness",
        "expect": "reject",
        # The dual maximally-broken classification: always the row-wise numeric
        # route. On a column whose elements are NOT numerically comparable (a
        # text column) the row-wise numeric route cannot run and escapes, where
        # the post-image (which routes such a column generic) demands a completed
        # verdict. This rival exercises the `numComparable` half of the surface
        # the marker-rivals never touch, so the column-kind input is moved.
        "module": _swap(_BASE, _A_IMPL,
                        "    let result : Except DiffErr (List Bool) :=\n"
                        "      rowWiseOutcome col rows\n"
                        "    return result\n"),
        "refinement": "always using the row-wise numeric-closeness route sends a "
                      "column whose elements are not numerically comparable (a "
                      "text column, present in the identical-inputs test) down a "
                      "route that cannot run on it and raises, crashing the "
                      "comparison, so that test still fails. A faithful "
                      "counterpart that routes every column row-wise does NOT "
                      "resolve — the route choice exists precisely because a text "
                      "column must take the generic route.",
        "rationale": "REJECT from `out = diffSpec fmt col rows`: the classifier "
                     "is ignored, so a not-classified, not-numerically-comparable "
                     "column (routed generic by the spec, completing) is instead "
                     "routed row-wise and escapes. Refuted at a "
                     "not-numerically-comparable column — moving BOTH intrinsic "
                     "kind flags of the column input off the values the other "
                     "rivals hold them at.",
        "witness": _wit(
            "example : diffVLAColumnTester ['A'] "
            "{ varLength := false, numComparable := false } "
            "[] = false := by\n  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 SPEC cases (2 soundness
# positives — one doubling as admissibility — and 4 uniqueness rivals). This
# bundle models the SAME behaviour (choose a comparison route by the format
# descriptor and produce the routed outcome) as ONE method with one obligation,
# so every case maps directly:
#
#   sibling case                       -> here
#   ---------------------------------------------------------------------
#   pos-control-branch-reorder         -> pos-route-branch-reorder      PORTED
#   pos-control-local-reshape-admiss   -> pos-route-local-reshape       PORTED
#                                         + admiss-routes-complete       RE-AIMED
#   frame-mutation-write-readonly      -> (none)                        OMITTED
#   route-p-only-misses-Q              -> weak-route-first-marker-only  PORTED
#   route-q-only-misses-P              -> weak-route-second-marker-only PORTED
#   route-always-elementwise           -> weak-route-always-generic     PORTED
#
# CARRIER NOTE. On nagini both comparators yielded the same row-granular count
# and the element-wise comparator carried an APPLICABILITY PRECONDITION
# (Requires not-VLA) that Viper discharged; a misroute was rejected by that
# precondition. This velvet carrier makes the SAME discrimination the object of
# the single ensures clause: each route is modeled deeply as an `Except` outcome
# that COMPLETES or lets a failure ESCAPE depending on the column's element kind,
# so a misroute is rejected because the escaping outcome differs from the
# completed one the spec demands at that input. The nagini "applicability
# precondition violated" argument and this "escaping vs completed outcome"
# argument are the same fact on the two carriers.
#
# RE-AIMED (admissibility): the sibling folds admissibility into the local-reshape
#   positive (that a normal F2P-shaped column is admitted by the applicable
#   comparator's precondition). No method here has a `require` clause, so that
#   probe is vacuous. It is re-aimed at the residual admissibility risk on a total
#   domain — that the post-image is unsatisfiable / degenerate at the interesting
#   point — via an in-region assert that both an F2P-shaped row-wise-routed VLA
#   column and a generic-routed column yield a COMPLETED verdict.
#
# OMITTED (1): frame-mutation-write-readonly. On nagini `row_mismatches` carries a
#   half `Acc` permission an impl can write, and the rival is rejected for
#   INSUFFICIENT PERMISSION. This backend is referentially transparent, has no
#   heap and no aliasing, and this bundle declares no `mut` binder, so there is no
#   read-only input to overwrite and no discriminating witness could exist. Omitted
#   because the class collapses on this carrier, not because it was hard; no
#   substitute fabricated.
#
# ADDED (1): weak-route-always-rowwise. The nagini carrier collapsed both
#   comparators onto the same count and treated the row-wise comparator as
#   applicable to ANY column, so "always compare row-wise" was not a distinct
#   rival there. This carrier models the row-wise numeric route's OWN failure — it
#   cannot run on a not-numerically-comparable (text) column — so the dual
#   maximally-broken classification is a genuine, machine-checked rival here. It is
#   also what moves the column-kind input: without it every reject witness would
#   hold `col.numComparable` at true, and a rival mishandling a text column would
#   go uncaught. Its faithful counterpart (compare every column row-wise) crashes
#   the text column present in the failing identical-inputs test, so it too would
#   NOT resolve.
#
# WITNESS DISTINCTNESS. The two marker-rivals are refuted at MIRROR format points
#   (each at the marker it misses), so neither pins the format input and each
#   demonstrates the exact sub-domain it gets wrong. The two always-one-route
#   rivals are refuted on the sub-domains that separate them — a variable-length
#   multi-element column (generic route escapes) and a not-numerically-comparable
#   column (row-wise route escapes). Across the four witnesses the format
#   descriptor, both intrinsic column-kind flags, and the row list are all varied.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; the gate ignores this list.
# The sibling's three A-reference probes are the obligations axiom_check.py / G-AX
# already discharge for this bundle.
AXIOM_TESTS = []
