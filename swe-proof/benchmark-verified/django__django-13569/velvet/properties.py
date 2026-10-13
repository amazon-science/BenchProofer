"""properties.py — G-PBT falsification battery for django__django-13569 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct groupingColumns`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  groupingColumns (e : Expr) return (out : List Expr)
    require e.isNondetGenerator = true       -- the receiver is a nondet generator
    ensures out = groupingContribution e     -- load-bearing clause
    ensures out = []                          -- the concrete image on this domain

``groupingContribution`` is a fully unfolded ``def`` in the ``pure`` region
(``if e.isNondetGenerator then [] else [e]``) — there is NO opaque answer key to
echo. The sole INPUT BINDER is ``e : Expr``, a structure whose only field is the
Bool ``isNondetGenerator``. The ``require`` clause pins that field to ``true``,
so the modeled admissible domain is the SINGLE value
``{ isNondetGenerator := true }`` — a value-level leaf whose value is freshly
drawn per row, which therefore denotes no stable grouping column and must
contribute NONE. On that domain both ``ensures`` clauses collapse to the same
demand, ``out = []`` (``groupingContribution`` on a generator IS ``[]``).

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME-MUTATION / PERMISSION — VACUOUS here. The nagini sibling carries a
    MANDATORY frame-mutation rival (write a read-only carrier held at
    ``Acc(list_pred(.), 1/2)``, rejected for insufficient permission). Lean and
    Velvet are referentially transparent: ``e`` is an immutable value, this
    bundle declares NO ``mut`` binder, there is no heap and no aliasing — so
    there is no read-only input to overwrite and no substitute probe. Not
    fabricated (per the porting map, this class is vacuous on Lean/Velvet).
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is a total, fully unfolded
    function of the method's own input (``groupingContribution`` is a concrete
    ``def``; the ``axioms`` region is empty), so there is no answer key to echo.
    The cheapest correct impl returns the empty contribution, covered honestly by
    the positive controls.
  * PARTIAL-DOMAIN / VALUE — APPLIES. The headline defect on this modeled domain
    is the pre-change inherited behaviour: a value-level leaf that falls through
    to the generic non-aggregate rule and contributes ITSELF (``[self]``, length
    1) instead of the empty list. It is NOT the only landable rival, though: the
    admissible domain being a single point bounds the INPUTS a rival can be
    refuted at, not the wrong ANSWERS it can give there. Three further rivals
    attack the same point by distinct routes — inverting the discrimination
    rule, sign-flipping a selection predicate, and contributing a node the
    input never mentions — and each is refuted by the same witness. See the
    footer.

WITNESS PLACEMENT. Every reject rival carries a machine-checked refutation
``witness`` — a Velvet tester statement at the ONE admissible concrete input,
checked in a file whose obligation has been stripped so no tactic script can mask
the verdict. The witness binds no hypothesis (the carrier is fully transparent
and the input is a concrete literal), so there is no joint-satisfiability
obligation. Each ELABORATES against its rival and FAILS against the frozen
solution, with the gold-side failure a SEMANTIC refutation (``decide`` evaluates
the tester and reports the proposition false), not a stuck reduction — confirmed
by building the complementary claim, which inverts both exit codes. Because all
four rivals give a wrong answer at the same single admissible input, they share
one witness statement; the discriminating work is done per rival by the two
builds, not by varying the probed point (which the ``require`` clause fixes).

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom``; the changed
behaviour is modeled DEEPLY as ``groupingContribution``, an A-reference validated
== the real callee by conformance_check.py — G-CONF's job, not this gate's). The
gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13569"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The entire executable body of the method is the
# ---- single line `return []`. It lies wholly inside the one
# ---- `-- impl-start`/`-- impl-end` region and is unique in Solution.lean (both
# ---- facts asserted at load by _swap). Editing only this keeps
# ---- markers.same_spec True and the `prove_correct groupingColumns` statement
# ---- byte-identical. The frozen proof body (`loom_solve`) closes every variant
# ---- below with no retune (each keeps the returned value equal to the empty
# ---- contribution, so no loop reasoning is introduced), so no proof-region
# ---- surgery is needed.
_IMPL = "    return []\n"

assert _BASE.count(_IMPL) == 1, "function impl region drifted from expected text"


def _impl(new_body: str) -> str:
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `groupingColumnsTester { isNondetGenerator := true } = false` says the
# ---- extracted program's result violates the method's postcondition at that
# ---- concrete input. Checked in a file whose `prove_correct` block has been
# ---- stripped, so no tactic script can mask the verdict. The probed input
# ---- satisfies the `require` clause (`isNondetGenerator = true`), so the tester
# ---- reaches the postcondition rather than vacuously passing on an excluded
# ---- input.
_TESTER = (
    "extract_program_for groupingColumns\n"
    "prove_precondition_decidable_for groupingColumns\n"
    "prove_postcondition_decidable_for groupingColumns\n"
    "derive_tester_for groupingColumns\n\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — the honest grounded impl, which MUST verify
    # (else SPEC-TOO-STRONG). `groupingContribution e` is GROUNDED in the input
    # (a total function of `e`, no opaque answer key), so returning it is a
    # correct fully-grounded implementation, not an ungrounded-oracle echo. It
    # also shows the spec is not echo-vulnerable: any WRONG constant/echo fails
    # `out = groupingContribution e`. The value is still `[]` under the
    # precondition, so the frozen `loom_solve` closes the (byte-identical)
    # obligation with no retune.
    # =====================================================================
    {
        "id": "pos-control-grounded",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl("    return (groupingContribution e)\n"),
        "rationale": "the post-image `groupingContribution e` is GROUNDED in the "
                     "input (a total function of `e`, no opaque answer key), so "
                     "returning it is the honest grounded CORRECT impl. It MUST "
                     "verify — the clause is literally `out = groupingContribution "
                     "e` — else the postcondition is SPEC-TOO-STRONG. Also shows "
                     "the spec is not echo-vulnerable: any wrong constant/echo "
                     "would fail `out = groupingContribution e`.",
    },
    {
        "id": "pos-control-branch",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different but CORRECT: dispatch on the generator flag
        # explicitly and build the empty result in the generator arm, the
        # self-contribution in the (precondition-excluded) other arm. On the
        # admissible domain (`isNondetGenerator = true`) the value is `[]`,
        # identical to gold; the executable SHAPE differs (a branch vs. a bare
        # constant). The frozen proof still closes.
        "module": _impl(
            "    let out := (if e.isNondetGenerator then ([] : List Expr) else [e])\n"
            "    return out\n"),
        "rationale": "structurally different CORRECT reshape: dispatch on the "
                     "generator flag and build the empty contribution in the "
                     "generator arm (the self-contribution in the "
                     "precondition-excluded arm). On the admissible domain the "
                     "value is `[]`, so `out = groupingContribution e` and "
                     "`out = []` both hold; a faithful reshape MUST verify, else "
                     "the clause is over-fit to the bare-constant FORM => "
                     "SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY (verify) — the nagini sibling's positive-control self-call
    # establishes that the precondition ADMITS a normal F2P-shaped input. This
    # bundle DOES carry a `require` clause (`isNondetGenerator = true`), so the
    # probe is live here: an in-region assertion that the F2P-shaped node (a
    # non-deterministic value generator — the exact receiver the failing test
    # exercises) satisfies the precondition AND that the post-image is
    # non-degenerate there (it demands exactly the empty contribution, not
    # something an unsatisfiable spec would admit). The assert is LIVE, not
    # decoration: replacing the claimed contribution with a wrong one leaves an
    # unsolved goal (verified out-of-band). The frozen body follows the assert, so
    # the method's own `ensures` obligation still discharges under `loom_solve`.
    # =====================================================================
    {
        "id": "admiss-generator-precondition-admits",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    assert (with_name_prefix `admiss\n"
            "      (({ isNondetGenerator := true } : Expr).isNondetGenerator = true\n"
            "       ∧ groupingContribution ({ isNondetGenerator := true } : Expr) = []))\n"
            "    return []\n"),
        "rationale": "the precondition admits the F2P-shaped receiver (a "
                     "non-deterministic value generator) AND the post-image is "
                     "non-degenerate there: it demands exactly the empty "
                     "contribution, not the self-inclusion an unsatisfiable / "
                     "pre-change spec would give. The in-region assert must "
                     "discharge (else PRECOND-TOO-STRONG or an unsatisfiable "
                     "obligation) and the frozen body keeps the ensures obligation "
                     "intact, so the module verifies.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rival — the pre-change inherited behaviour, which
    # MUST be rejected, with a machine-checked refutation witness at the sole
    # admissible input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-self-contribution",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-change behaviour: a value-level leaf contributes ITSELF (length
        # 1) instead of the empty list — the generic non-aggregate rule with no
        # special case for a non-deterministic value generator.
        "module": _impl("    return [e]\n"),
        "refinement": "contributing the node itself is exactly the pre-change "
                      "behaviour: with no special case, a non-deterministic value "
                      "generator used for ordering falls through to the generic "
                      "non-aggregate rule and contributes ITSELF as a grouping "
                      "column (length 1). A faithful counterpart that kept that "
                      "generic rule would inject the freshly-drawn value generator "
                      "into the grouping, so rows are not grouped and the failing "
                      "test (grouping must ignore an ordering value generator) "
                      "still FAILS -> would NOT resolve.",
        "rationale": "REJECT from `out = groupingContribution e` (equivalently "
                     "`out = []`): under the precondition the contribution is the "
                     "EMPTY list, but the rival returns a length-1 list, so the "
                     "two differ. Refuted at the sole admissible input "
                     "`{ isNondetGenerator := true }`. If it verified, "
                     "SPEC-TOO-WEAK (the empty-contribution requirement "
                     "unenforced).",
        "witness": _TESTER +
                   "example : groupingColumnsTester { isNondetGenerator := true } "
                   "= false := by\n  decide\n",
    },

    # =====================================================================
    # UNIQUENESS rivals added by the adversarial audit. The battery previously
    # asserted the pre-change `[e]` rival was the ONLY landable one, on the
    # reasoning that a single admissible input leaves nowhere else to refute.
    # That conflates the INPUT the spec is probed at with the ANSWER a rival
    # gives there: the domain is one point, but the wrong values AT that point
    # are unbounded, and a rival reaching the wrong value by a different route
    # exercises a different part of the `ensures` reduction. Each of the three
    # below was landed with two real builds (witness elaborates against the
    # rival, fails against the frozen solution) and each fails with a SEMANTIC
    # unsolved goal on the returned value, not a tactic mismatch.
    # =====================================================================
    {
        "id": "weak-inverted-rule",
        "kind": "uniqueness",
        "expect": "reject",
        # Reads the SAME field the spec discriminates on, and dispatches on it,
        # but assigns the two legs backwards: contribute self for a generator,
        # nothing for a genuine column. Unlike `return [e]` this rival is a
        # branch, so its rejection turns on the guard reducing under the
        # `require` clause rather than on a bare constant mismatch.
        "module": _impl(
            "    return (if e.isNondetGenerator then [e] else ([] : List Expr))\n"),
        "refinement": "inverting the rule is strictly worse than the pre-change "
                      "behaviour: it injects the freshly-drawn value generator "
                      "into the grouping (exactly the reported defect) AND drops "
                      "the genuine column a stable leaf must contribute, so both "
                      "the failing test and the previously-passing aggregation "
                      "behaviour break -> would NOT resolve.",
        "rationale": "REJECT from `out = groupingContribution e` / `out = []`: "
                     "under the precondition the guard is `true`, so this rival "
                     "returns the length-1 `[e]` where the contribution is "
                     "EMPTY. Distinct from weak-self-contribution in ROUTE (a "
                     "live branch on the discriminating field, not a constant), "
                     "so it probes the guard's reduction. If it verified, "
                     "SPEC-TOO-WEAK.",
        "witness": _TESTER +
                   "example : groupingColumnsTester { isNondetGenerator := true } "
                   "= false := by\n  decide\n",
    },
    {
        "id": "weak-selection-predicate-flipped",
        "kind": "uniqueness",
        "expect": "reject",
        # Selects from the singleton with the predicate's SIGN flipped: keeps the
        # generator instead of discarding it. This is the shape a real selection
        # rule takes, so its rejection attests that the spec pins the polarity of
        # the discrimination and not merely the presence of one.
        "module": _impl(
            "    return (List.filter (fun x => x.isNondetGenerator) [e])\n"),
        "refinement": "a selection rule that KEEPS non-deterministic value "
                      "generators rather than discarding them retains the "
                      "generator in the grouping, so rows are not grouped and the "
                      "failing test (grouping must ignore an ordering value "
                      "generator) still FAILS -> would NOT resolve. The correct "
                      "polarity is the whole content of the change.",
        "rationale": "REJECT from `out = groupingContribution e`: the flipped "
                     "predicate retains `e` under the precondition, giving a "
                     "length-1 list where the contribution is EMPTY. Pins the "
                     "POLARITY of the selection, which a rival returning a bare "
                     "constant cannot test. If it verified, SPEC-TOO-WEAK (the "
                     "spec would admit either sign of the rule).",
        "witness": _TESTER +
                   "example : groupingColumnsTester { isNondetGenerator := true } "
                   "= false := by\n  decide\n",
    },
    {
        "id": "weak-unrelated-node",
        "kind": "uniqueness",
        "expect": "reject",
        # Contributes a node the INPUT never mentions. Attacks the grounding of
        # the clause rather than its polarity: a spec that only bounded the
        # result's LENGTH or only demanded "some list" would admit this.
        "module": _impl("    return [{ isNondetGenerator := false }]\n"),
        "refinement": "contributing a fabricated stable column the query never "
                      "ordered by groups over a column that is not in the "
                      "query's own expressions, so the emitted grouping does not "
                      "match the selected columns and aggregation results differ "
                      "from gold -> the failing test still FAILS and the "
                      "previously-passing aggregation behaviour breaks too -> "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = groupingContribution e` / `out = []`: a "
                     "length-1 list of an unrelated node is neither the empty "
                     "contribution nor grounded in `e` at all. Distinct target: "
                     "it attacks the clause's GROUNDING in the input (a spec "
                     "demanding merely `∃ l, out = l`, or only a length bound "
                     "with the wrong bound, would admit it). If it verified, "
                     "SPEC-TOO-WEAK.",
        "witness": _TESTER +
                   "example : groupingColumnsTester { isNondetGenerator := true } "
                   "= false := by\n  decide\n",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases across TWO
# contracted functions, `random_group_by_cols` (3 cases) and
# `group_by_columns_for_ordering` (4 cases), plus an empty AXIOM lane. This bundle
# models ONLY the purely-functional core — a single method `groupingColumns`,
# the per-leaf grouping contribution of a non-deterministic value generator —
# corresponding to the sibling's `random_group_by_cols`. The entire
# `group_by_columns_for_ordering` gather-loop family is UNMODELED here (this bundle
# carries exactly one contracted method), so every sibling case attached to that
# function has NO counterpart at all — carrier narrowing, not an omission of
# convenience. Every sibling case is accounted for below.
#
#   sibling case             -> here                                  disposition
#   ---------------------------------------------------------------------------
#   rgbc-pos-control         -> pos-control-grounded                  RE-SHAPED
#                               (+ pos-control-branch ADDED)
#   rgbc-admiss              -> admiss-generator-precondition-admits  PORTED
#   rgbc-self-prepatch       -> weak-self-contribution               PORTED
#   gbco-pos-control         -> (none)                                UNMODELED FN
#   gbco-frame-mutation      -> (none)                                UNMODELED FN
#   gbco-include-random      -> weak-selection-predicate-flipped      RE-TARGETED
#   gbco-drop-last-term      -> (none)                                UNMODELED FN
#   AXIOM_TESTS (empty)      -> (none)                                N/A
#   (audit-added rivals)     -> weak-inverted-rule                    ADDED
#                            -> weak-unrelated-node                   ADDED
#
# 2 ported, 1 re-shaped, 1 re-targeted, 3 added, 3 unmodeled = 7 SPEC cases
# (2 soundness, 1 admissibility, 4 uniqueness).
#
# RE-TARGETED (gbco-include-random -> weak-selection-predicate-flipped): the
#   sibling's "include the generator's column in the loop" bug has no gathering
#   loop to attach to here, but its BEHAVIOURAL content — a selection rule that
#   retains a non-deterministic value generator instead of discarding it — is
#   expressible at the single-leaf level as a sign-flipped `List.filter`
#   predicate. That is a re-targeting onto the modeled carrier, not a fabricated
#   rival: the wrong answer it produces is the sibling's wrong answer. Landed
#   with two real builds.
#
# RE-SHAPED (rgbc-pos-control -> pos-control-grounded): the sibling's positive
#   control branches on `colid` sign and builds the empty result both ways. The
#   equivalent grounded reshape here returns `groupingContribution e` directly (a
#   total function of the input); the value is still `[]` under the precondition,
#   so the frozen `loom_solve` closes it. Verified to build.
# ADDED (1): pos-control-branch — a second structurally-different correct impl
#   that dispatches on the generator flag explicitly (an `if`-ladder vs. a bare
#   constant), keeping the value `[]` on the admissible domain, so the soundness
#   surface is defended by two distinct reshapes. Verified to build.
# PORTED (admiss): the sibling asserts a normal F2P-shaped input satisfies the
#   gathering length precondition. This bundle carries a real `require` clause
#   (`isNondetGenerator = true`), so the probe is live and is expressed directly
#   as an in-region assertion that the F2P-shaped receiver (a non-deterministic
#   value generator) satisfies the precondition AND that the post-image is
#   non-degenerate there (the empty contribution, not the pre-change
#   self-inclusion). The assert is live (a false contribution claim leaves an
#   unsolved goal — verified out-of-band); the frozen body follows it so the
#   ensures obligation still discharges. Verified to build.
# PORTED (rgbc-self-prepatch -> weak-self-contribution): the sibling's pre-patch
#   echo returns `[colid]` (the inherited `[self]`, length 1). It re-expresses
#   directly as `return [e]` onto the single `out = groupingContribution e`
#   clause. Its witness ELABORATES against the rival and FAILS against the frozen
#   solution (verified with two real builds). The refinement argument carries
#   over: a faithful counterpart keeping the generic non-aggregate rule injects
#   the value generator into the grouping, so the failing test still fails and it
#   would NOT resolve.
# UNMODELED FN (three gbco-* cases): the sibling's `group_by_columns_for_ordering`
#   is the order-by gathering loop over three equal-length carriers. This bundle
#   models only the single-leaf contribution `groupingColumns`; there is no
#   gathering method here, and a variant may NOT introduce one (adding a second
#   `method` changes the spec view, so `same_spec` fails — checked mechanically
#   during the audit). So gbco-pos-control (branch-reorder over the loop),
#   gbco-frame-mutation (write a read-only carrier — nagini-only fractional
#   permission) and gbco-drop-last-term (a loop-bound off-by-one) have NO carrier
#   to attach to: each is a statement about ITERATION ORDER or LOOP BOUNDS, which
#   needs a sequence input to be observable, and the sole binder here is one
#   `Expr`. Chasing parity would require fabricating rivals for a behaviour this
#   bundle does not model; per the porting map, that is forbidden. (The
#   frame-mutation class is doubly vacuous here: even were the loop modeled, this
#   backend is referentially transparent with no `mut` binder and no permission
#   system.) gbco-include-random is the exception — its wrong ANSWER is
#   expressible per-leaf, so it was re-targeted rather than dropped; see above.
#
# BINDER / CLAUSE COVERAGE. The obligation has a single input binder,
#   `e : Expr`, whose only field `isNondetGenerator` the `require` clause PINS to
#   `true`. The modeled admissible domain is therefore the SINGLE value
#   `{ isNondetGenerator := true }`, so pts=1 is INHERENT to the precondition, not
#   a coverage gap: there is no second admissible INPUT at which to refute a
#   rival, and the two independent `ensures` clauses
#   (`out = groupingContribution e`, `out = []`) collapse to the same demand
#   (`out = []`) on that domain. The binder IS varied to the extent the
#   precondition permits (the sole admissible point); a rival that mishandled
#   only some OTHER value of `isNondetGenerator` is out of the modeled domain by
#   the `require` clause and cannot be a spec-strength defect here — measured:
#   an impl correct on the generator leg and wrong on the excluded leg VERIFIES
#   (exit 0), which is correct behaviour for a guarded spec, not a hole.
#   What pts=1 does NOT bound is the number of distinct WRONG ANSWERS at that
#   point, and the battery's earlier claim that one rival was therefore the only
#   possible one was false. Four rivals now attack the point by distinct routes:
#   a bare wrong constant (weak-self-contribution), a live branch on the
#   discriminating field with its legs swapped (weak-inverted-rule), a selection
#   predicate with its sign flipped (weak-selection-predicate-flipped), and a
#   result not grounded in the input at all (weak-unrelated-node). The coverage
#   reporter's "all reject witnesses probe the SAME input point" finding is
#   therefore accurate and expected, and is a property of the `require` clause.
# WITNESS DISCRIMINATION (re-derived by the adversarial audit with real builds,
#   not merely restated): for every reject case the witness ELABORATES against the
#   rival (exit 0) and FAILS against the frozen solution (exit 1). The gold-side
#   failure is SEMANTIC, not a stuck reduction or a missing name — `decide`
#   evaluates the tester and reports `Tactic `decide` proved that the proposition
#   ... = false is false`. That `decide` genuinely REDUCES on both sides (rather
#   than being stuck for every claim, the hollow-pass mode this corpus has
#   measured elsewhere) was confirmed by building the exact OPPOSITE claim
#   (`... = true`): it inverts cleanly — exit 0 against the frozen solution and
#   exit 1 against the rival — so the exit codes carry real information. The
#   witness binds no hypothesis (the carrier is fully transparent and the input is
#   a concrete literal), so there is no joint-satisfiability obligation. No
#   `sorry`/`admit`/`native_decide`/`axiom` appears.
# SPEC STRENGTH (audit attacks D and E, real builds): six further WRONG impls
#   beyond the shipped rivals were tried against the frozen spec — a duplicated
#   self-contribution, a `List.replicate 1`, the default node, a `DecidableEq`
#   comparison, and the rivals now shipped — and ALL were rejected with a
#   semantic unsolved goal on the returned value. Seven CORRECT reshapes were
#   tried — `List.filter` on the negated predicate, `List.filterMap`, a nested
#   guard, an `[] ++` append, `List.tail`, `List.drop 1`, `List.take 0` — and ALL
#   verified under the frozen `loom_solve` with no retune. So the obligation is
#   neither too weak nor over-fit to the bare-constant form on this domain.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
#   consumed axiom (the change is modeled deeply as `groupingContribution`, an
#   A-reference validated by conformance_check.py / G-CONF), and the gate ignores
#   AXIOM_TESTS regardless.
AXIOM_TESTS = []
