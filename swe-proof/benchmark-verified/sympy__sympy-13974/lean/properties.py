"""properties.py — G-PBT falsification manifest for sympy__sympy-13974 (lean).

NOT a Lean module: a record of adversarial cases the G-PBT spec lane executes
against the frozen `Solution.lean`. Ported from the nagini sibling's battery
(`../nagini/properties.py`), re-expressed over THIS backend's carrier.

DEFENDED SURFACE
----------------
The single modeled obligation is

    theorem correct_tensorPow :
        ∀ e : QExpr, problem_spec_tensorPow e (implementation_tensorPow e)

over the one-constructor-per-shape expression carrier `QExpr` (`atom` / `tp` /
`pow`). The postcondition is a single top-level clause,

    result = specTensorPow e

where `specTensorPow` is a TRANSPARENT total `def` that recurses on the actual
input:

    .pow (.tp args) exp => .tp (args.map (fun b => QExpr.pow b exp))
    e                   => e

so the pin is GROUNDED in the input rather than pinned to an opaque answer-key.
Because the whole carrier is a `deriving Repr` inductive with no `opaque`
callee, every rival's violation is a decidable statement at a literal input and
`simp` closes it — no conditioning on the carrier is needed anywhere in this
battery.

AUDIT NOTE (admissibility). An earlier revision of this manifest recorded the
admissibility lane as having NO counterpart here, on the ground that a total
obligation has no precondition that could be too strong to admit a normal input.
That reason was wrong, and the lane is now carried by `admiss-f2p-shaped-ground`:
the analogue on a total carrier is the obligation being UNSATISFIABLE at exactly
an F2P-shaped input, which a positive that discharges the obligation at that
concrete input by evaluation tests directly. It was landed and measured, along
with `pos-control-foldr-assembly`, whose reshape the frozen tactic script does
not close and which therefore probes SPEC-TOO-STRONG harder than the two
`rfl`-range positives it joins.

The obligation is TOTAL (`∀ e : QExpr`, no hypothesis binder), which is what
this bundle's spec buys over the nagini sibling's guarded contract, and it
carries three independently attackable behaviours packed into that one clause:

  * SHAPE — a power over a tensor-product base must come back as a tensor
    product, not as the untouched power node;
  * PER-FACTOR WORK — every factor must carry the exponent, and the exponent it
    carries must be the one the input supplied, applied to that factor's OWN
    base;
  * ORDER + ROUTING — the factors must keep their input positions, and the
    branch decision must send each input shape to the right arm.

Each of the three is attacked by its own rival below, and the seven reject
witnesses probe seven DISTINCT input points (one-, two- and three-factor bases
at four different exponents), so no rival is refuted at a point another one
already covers.

Every reject case's `refinement` argument here is MEASURED, not argued: each
rival's corresponding real patch was applied to the repo at `base_commit` on top
of gold + test_patch, and the F2P plus all four P2P tests were run. All seven
shipped rivals fail the F2P and pass every P2P test. That measurement also cost
this battery a case — see the DROPPED RIVAL note at the foot of the file, where a
well-formed rival with a discriminating witness turned out to have a real patch
that RESOLVES, so shipping it would have attached a false refinement argument to
a passing case.

AUTHORING MECHANICS
-------------------
Every variant is built by region surgery (`_swap`) anchored on a substring that
lies ENTIRELY inside `-- impl-start`/`-- impl-end`, so `markers.same_spec` holds
by construction and a rejection is attributable to the postcondition rather than
to a tampered spec. The `theorem correct_tensorPow` STATEMENT is byte-identical
in every variant, and no variant adds an `axiom`, a helper lemma, a `sorry` or a
`native_decide`. The three `rfl`-range soundness positives close the frozen
obligation with the frozen tactic script, unmodified; the two cases that cannot
(`pos-control-foldr-assembly`, whose distributing arm no longer reduces, and
`admiss-f2p-shaped-ground`, which prepends a ground `have`) edit only the proof
region, which the spec view elides — so `same_spec` still holds, the STATEMENT is
still byte-identical, and `variant_scope` still passes.

Each `expect="reject"` case additionally carries a `witness`: a Lean `example`
proving the rival contradicts the spec at one concrete input. On a tactic-proof
backend the rival's build failure alone attributes NOTHING to the spec (the
frozen script is tuned to the frozen impl's syntactic form, so reshaping the
impl breaks it whether or not the reshape is wrong). Every witness here was
built both ways before shipping: it elaborates against its rival and fails
against the frozen solution with `unsolved goals ⊢ False`.

CASES PORTED FROM NAGINI, AND CASES DROPPED — see `assessment` in the handoff
payload for the full accounting. In brief: the frame-mutation rival is VACUOUS
here (Lean is referentially transparent — there is no aliasing and no fractional
permission, so an impl cannot write to its input); and the divergence lane is
likewise vacuous, since `implementation_tensorPow` is a total Lean `def` and a
diverging implementation cannot be written at all. The nagini sibling's second
modeled
function (the routing decision over one factor of a product) is not modeled by
this bundle at all — this is the carrier narrowing the port guide describes, so
its three routing rivals have no counterpart here except insofar as the branch
decision inside the single modeled function is attacked by
`inverted-branch-decision`. `AXIOM_TESTS` are dropped: the axiom lane is G-AX's
job, and this bundle consumes no axiom (the evaluation is modeled structurally).
"""
from pathlib import Path

INSTANCE = "sympy__sympy-13974"
BACKEND = "lean"

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (Solution.lean edited) fails loudly at
    load rather than producing a variant that no longer attacks anything."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks — all strictly INSIDE the impl region.
# ---------------------------------------------------------------------------

# The distributing branch. Unique in the file: the reference evaluation in the
# `pure` region spells the same map WITHOUT the `return`, so anchoring on the
# `return` keeps this edit inside the impl region.
_DIST = "      | .tp args => return .tp (args.map (fun b => QExpr.pow b exp))"

# The distributing branch together with its sibling fallthrough, for rivals that
# reshape the branch DECISION rather than the branch body.
_DIST_PAIR = """      | .tp args => return .tp (args.map (fun b => QExpr.pow b exp))
      | _        => return e"""

# The whole dispatch, for a positive control that flattens the nested match.
_IMPL_BODY = """  match e with
  | .pow base exp =>
      match base with
      | .tp args => return .tp (args.map (fun b => QExpr.pow b exp))
      | _        => return e
  | _ => return e"""

# The outermost fallthrough — every input that is not a power. Unique at this
# indentation (the inner fallthrough is indented six spaces).
_OUTER_FALLTHROUGH = "  | _ => return e"

# The frozen proof's `intro` line (inside the proof region, unique in the file),
# so the admissibility positive can prepend a ground `have` while leaving the
# `theorem correct_tensorPow` STATEMENT byte-identical and the spec view
# untouched.
_P_INTRO = "  intro e\n"

# The inner distributing branch's proof step — the one `rfl` that discharges the
# tensor-product-base arm. A reshaped-but-correct impl whose distributing arm no
# longer reduces by `rfl` re-proves exactly here; the statement is untouched.
_P_DIST_RFL = "      | tp args => rfl"


def _witness(input_expr: str) -> str:
    """A refutation witness: the spec predicate DENIED at one concrete input.

    States `¬ problem_spec_tensorPow i (implementation_tensorPow i)` — i.e. the
    rival's answer at `i` is not the reference evaluation of `i`. The whole
    carrier is a plain inductive with no opaque callee, so unfolding the three
    definitions leaves a constructor disequality that `simp` decides; no
    hypothesis binder is needed, hence nothing that could be inconsistent.

    Checked both ways for every case below: elaborates against the rival,
    fails against the frozen solution (`unsolved goals ⊢ False`).
    """
    return (f"example : ¬ problem_spec_tensorPow\n"
            f"    ({input_expr})\n"
            f"    (implementation_tensorPow ({input_expr})) := by\n"
            f"  unfold problem_spec_tensorPow implementation_tensorPow "
            f"specTensorPow\n"
            f"  simp\n")


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify"
# ===========================================================================

# (P1) Structurally different, CORRECT: the raised factors are bound to a local
# before the tensor product is assembled. Semantically identical to the frozen
# impl, different source. Closes the frozen obligation with the frozen tactic
# script. If it failed, the postcondition would be over-fit to the exact gold
# spelling => SPEC-TOO-STRONG.
_POS_LOCAL = _swap(_BASE, _DIST, """      | .tp args =>
          let raised := args.map (fun b => QExpr.pow b exp)
          return .tp raised""")

# (P2) Structurally different, CORRECT: the two-level dispatch (match the power,
# then match its base) is FLATTENED into a single nested-pattern match with one
# catch-all. Same behaviour on every input, a genuinely different control-flow
# shape — the branch decision is taken in one step instead of two.
_POS_FLAT = _swap(_BASE, _IMPL_BODY, """  match e with
  | .pow (.tp args) exp => return .tp (args.map (fun b => QExpr.pow b exp))
  | _                   => return e""")

# (P3) The ECHO control, and the one place this carrier differs from the nagini
# sibling's in a way worth recording. There, the reference fold had no
# executable materialization, so "echo the oracle" was IMPOSSIBLE and the
# cheapest honest impl still had to do the per-factor work. Here the reference
# evaluation is a transparent total `def`, so an impl CAN delegate to it
# outright — and that is sound rather than a hole, precisely because the
# reference evaluation is grounded in the input: it recurses on the actual
# factors and applies the actual exponent, so delegating to it performs exactly
# the per-factor work the pin demands. There is no opaque answer-key to echo,
# and hence no wrong echo that could verify (UNGROUNDED-ORACLE is N/A here).
# This control demonstrates that.
_POS_ECHO = _swap(_BASE, _IMPL_BODY, "  return specTensorPow e")

# (P4) Structurally different, CORRECT: the per-factor list is built by an
# explicit `foldr` that conses each raised factor onto the accumulator, instead
# of by `List.map`. This is a reshape the frozen tactic script does NOT close —
# the distributing arm no longer reduces by `rfl` — so the case re-proves that
# one arm by induction on the factor list (statement byte-identical, no new
# declaration, no assumption token). It is the strongest available
# SPEC-TOO-STRONG probe in this battery: the other two positives stay inside
# `rfl`-range of the frozen impl, so this is the only positive that shows the
# clause admits a genuinely different way of ASSEMBLING the factor list rather
# than merely a different way of spelling the same reduction.
_POS_FOLDR = _swap(
    _swap(_BASE, _DIST,
          "      | .tp args => return .tp (args.foldr "
          "(fun b acc => QExpr.pow b exp :: acc) [])"),
    _P_DIST_RFL,
    """      | tp args =>
          induction args with
          | nil => rfl
          | cons a t ih => simp [List.map_cons, ih]""")


# ===========================================================================
# ADMISSIBILITY — expect "verify"
# ===========================================================================

# (A1) The obligation is SATISFIABLE at an F2P-shaped input. The frozen
# obligation is total (`∀ e : QExpr`, no precondition binder), so the nagini
# sibling's precondition-admission self-call has no literal counterpart — but
# the analogue on a total carrier is NOT vacuous: what PRECOND-TOO-STRONG
# becomes here is the obligation being unsatisfiable at exactly the input shape
# the real failing test exercises, i.e. a power whose base is a MULTI-FACTOR
# tensor product at a concrete exponent. This case discharges the spec predicate
# at that input by EVALUATION, as a `have` prepended to the frozen tactic body,
# and then closes the frozen obligation verbatim. Nothing is assumed: the
# statement is byte-identical, no new declaration appears, and the `have` is
# proved by `unfold` + `simp` rather than by a hypothesis.
#
# It is a real test, not a decoration: the same shape with the `have` asserting a
# WRONG result at that same input FAILS (measured — `unsolved goals ⊢ False`), so
# `simp` is deciding the ground instance rather than closing anything put in
# front of it.
_ADMISS_GROUND = _swap(
    _BASE, _P_INTRO,
    "  have _ground : problem_spec_tensorPow\n"
    "      (.pow (.tp [.atom 0, .atom 1]) (.atom 2))\n"
    "      (implementation_tensorPow "
    "(.pow (.tp [.atom 0, .atom 1]) (.atom 2))) := by\n"
    "    unfold problem_spec_tensorPow implementation_tensorPow specTensorPow\n"
    "    simp\n"
    + _P_INTRO)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (R1) THE PREPATCH SHAPE. A power over a tensor-product base is returned
# UNCHANGED — the exponent is never pushed onto the factors and the result is
# still a power node, not a tensor product. Attacks the SHAPE behaviour.
_R_IDENTITY = _swap(_BASE, _DIST, "      | .tp _    => return e")

# (R2) SHAPE RIGHT, WORK SKIPPED. The tensor product is re-assembled from the
# input factors, so the result has the right outer shape and the right factor
# count and order — but no factor carries the exponent. A strictly closer miss
# than R1: it satisfies everything about the clause except the per-factor power
# itself, so it isolates the PER-FACTOR WORK behaviour from the shape.
_R_UNRAISED = _swap(_BASE, _DIST, "      | .tp args => return .tp args")

# (R3) PARTIAL DOMAIN — every factor but the LAST. The exponent is distributed
# correctly across all leading factors and the final factor is passed through
# bare. Pins only part of the domain: on a one-factor base it is wrong, on a
# multi-factor base it agrees with the reference evaluation everywhere except
# the last position. Witnessed at THREE factors, so the witness exhibits two
# positions handled exactly like gold and only the third deviating — the
# sub-domain the rationale claims is the one the witness demonstrates.
_R_DROP_LAST = _swap(_BASE, _DIST, """      | .tp args =>
          return .tp (args.dropLast.map (fun b => QExpr.pow b exp)
                      ++ args.drop (args.length - 1))""")

# (R4) WRONG EXPONENT. Every factor is raised, and to a well-formed exponent —
# but a FIXED one, ignoring the exponent the input supplied. Agrees with the
# reference evaluation exactly when the input's exponent happens to be that
# constant, so the witness is stated at a different exponent. Attacks the
# per-factor work via the exponent argument specifically.
_R_CONST_EXP = _swap(
    _BASE, _DIST,
    "      | .tp args => return .tp (args.map (fun b => "
    "QExpr.pow b (QExpr.atom 2)))")

# (R5) WRONG BASE — first-factor broadcast. The right exponent is applied the
# right number of times, in the right order, but always to the FIRST factor's
# base instead of to each position's own factor. Agrees with gold on a
# one-factor base; witnessed at three factors, where positions two and three
# both lose their grounding. Attacks the per-factor work via the base argument.
_R_BROADCAST = _swap(
    _BASE, _DIST,
    "      | .tp args => return .tp (args.map (fun _ => "
    "QExpr.pow (args.headD (QExpr.atom 0)) exp))")

# (R6) ORDER. Every factor is raised to the correct exponent — the multiset of
# result factors is exactly right — but the factors come back in REVERSED
# positions. The tensor product being modeled is non-commutative, so factor
# position is observable content of the clause, not presentation. This rival has
# no nagini counterpart as a standalone case (the sequence-equality pin covered
# order implicitly there); it is added here because order is an independently
# attackable part of the one clause this bundle models. Agrees with gold on any
# base of fewer than two factors, so the witness uses two.
_R_REVERSE = _swap(
    _BASE, _DIST,
    "      | .tp args => return .tp (args.reverse.map "
    "(fun b => QExpr.pow b exp))")

# (R7) INVERTED BRANCH DECISION. The base test is inverted: a tensor-product
# base is passed through untouched, while a NON-tensor-product base is wrapped
# into a single-factor tensor product carrying the exponent. Both directions of
# the decision are wrong, so this attacks the SHAPE behaviour and the
# PASSTHROUGH behaviour at once. Witnessed on the non-tensor-product base — the
# arm no other rival in this battery reaches.
_R_INVERTED = _swap(_BASE, _DIST_PAIR, """      | .tp _    => return e
      | _        => return .tp [QExpr.pow base exp]""")

SPEC_TESTS = [
    # ---- positive controls (must verify) ----
    {"id": "pos-control-local-binding", "kind": "soundness", "expect": "verify",
     "module": _POS_LOCAL,
     "rationale":
        "structurally different but CORRECT: the raised factors are bound to a "
        "local before the tensor product is assembled. Semantically identical "
        "to the frozen impl on every input, so the single postcondition clause "
        "`result = specTensorPow e` must still hold and the frozen tactic "
        "script still closes `correct_tensorPow` (verified). If this were "
        "rejected, the clause would be over-fit to the exact gold spelling "
        "rather than to the behaviour => SPEC-TOO-STRONG."},
    {"id": "pos-control-flat-dispatch", "kind": "soundness", "expect": "verify",
     "module": _POS_FLAT,
     "rationale":
        "structurally different but CORRECT: the two-step dispatch (match the "
        "power, then match its base) is flattened into one nested-pattern "
        "match with a single catch-all, so the branch decision is taken in one "
        "step instead of two. A genuinely different control-flow shape with "
        "identical behaviour; it must verify, or the clause is pinned to the "
        "gold dispatch structure rather than to the input/output relation."},
    {"id": "echo-attempt-honest", "kind": "soundness", "expect": "verify",
     "module": _POS_ECHO,
     "rationale":
        "the ECHO control. The postcondition's right-hand side is a "
        "transparent total `def` that recurses on the ACTUAL input — it "
        "destructures the real factors and applies the real exponent — so an "
        "impl that delegates to it straight is doing exactly the per-factor "
        "work the clause demands, and must verify. Its purpose is to show the "
        "pin is GROUNDED in the input rather than tied to an opaque "
        "answer-key: there is no oracle here whose value an impl could echo "
        "without performing the distribution, so UNGROUNDED-ORACLE is N/A. "
        "Note the carrier difference from the nagini sibling, where the "
        "reference fold had no executable materialization at all and this "
        "control instead demonstrated that the cheapest satisfying impl still "
        "had to do the work."},
    {"id": "pos-control-foldr-assembly", "kind": "soundness",
     "expect": "verify",
     "module": _POS_FOLDR,
     "rationale":
        "structurally different but CORRECT: the raised factors are assembled "
        "by an explicit `foldr` that conses each one onto the accumulator "
        "instead of by `List.map`. Unlike the other two positives this reshape "
        "is NOT within `rfl`-range of the frozen impl — the distributing arm no "
        "longer reduces — so the case re-proves that one arm by induction on "
        "the factor list, leaving the `correct_tensorPow` STATEMENT "
        "byte-identical and adding no declaration. It must verify: the clause "
        "pins the RESULT, so any impl that produces the same factor list "
        "satisfies it however that list was built. If it were rejected, the "
        "clause would be pinned to `List.map` as the assembly primitive rather "
        "than to the input/output relation => SPEC-TOO-STRONG."},

    # ---- admissibility (must verify) ----
    {"id": "admiss-f2p-shaped-ground", "kind": "admissibility",
     "expect": "verify",
     "module": _ADMISS_GROUND,
     "rationale":
        "the obligation must be SATISFIABLE at an F2P-shaped input. This "
        "obligation is total (`∀ e : QExpr`, no precondition binder), so the "
        "nagini sibling's precondition-admission self-call has no literal "
        "counterpart — but the analogue on a total carrier is the obligation "
        "being unsatisfiable at exactly the shape the failing test exercises, "
        "so this case discharges the spec predicate by EVALUATION at a power "
        "over a two-factor tensor product at a concrete exponent, as a `have` "
        "prepended to the frozen tactic body, before closing the frozen "
        "obligation verbatim. If that ground instance could not be discharged, "
        "the spec would be unsatisfiable exactly where it is consumed => "
        "PRECOND-TOO-STRONG. Non-vacuous by measurement: the identically-shaped "
        "case whose `have` asserts a WRONG result at the same input fails with "
        "`unsolved goals ⊢ False`, so `simp` is deciding the ground instance "
        "rather than closing whatever is put in front of it."},

    # ---- uniqueness rivals (must reject) ----
    {"id": "undistributed-prepatch", "kind": "uniqueness", "expect": "reject",
     "module": _R_IDENTITY,
     "witness": _witness(".pow (.tp [.atom 0, .atom 1]) (.atom 7)"),
     "refinement":
        "this IS the pre-patch behaviour: a power whose base is a tensor "
        "product is left as a power, the exponent never reaching the factors. "
        "Its faithful real patch leaves the reported defect unfixed. Measured "
        "against the real repo: the F2P FAILS, with all four of its "
        "power-of-a-tensor-product assertions returning the input untouched, "
        "while all four P2P tests pass. Definitively non-resolving, so a "
        "verifying rival here would be a true verify-does-not-imply-resolve "
        "break.",
     "rationale":
        "rejection from the postcondition `result = specTensorPow e`, SHAPE "
        "behaviour: at the witness input the reference evaluation is a `tp` "
        "node whose factors are `pow` nodes, while the rival returns the "
        "original `pow` node. Distinct constructors at the top level, so the "
        "equation is refutable by `simp` after unfolding — the witness "
        "elaborates against this rival and fails on the frozen solution."},
    {"id": "shape-right-work-skipped", "kind": "uniqueness", "expect": "reject",
     "module": _R_UNRAISED,
     "witness": _witness(".pow (.tp [.atom 3]) (.atom 4)"),
     "refinement":
        "a real patch that recognises the power-of-a-tensor-product shape and "
        "rebuilds the tensor product from the base's factors, but forgets to "
        "raise them, drops the exponent entirely. Measured against the real "
        "repo at base_commit (gold + test_patch, this body substituted): the "
        "F2P FAILS — the four assertions over a power-of-a-tensor-product input "
        "all come back with the exponent silently gone — while all four P2P "
        "tests pass. Faithful but non-resolving.",
     "rationale":
        "rejection from the postcondition, PER-FACTOR WORK behaviour, isolated "
        "from shape: the rival gets the outer `tp` node, the factor count and "
        "the factor order all right, so the only disagreement with "
        "`specTensorPow` is that each factor is the input factor rather than "
        "its power. Witnessed on a ONE-factor base — the smallest input that "
        "separates them — where the reference evaluation is a `pow` factor and "
        "the rival's is an `atom`."},
    {"id": "partial-domain-last-factor", "kind": "uniqueness",
     "expect": "reject",
     "module": _R_DROP_LAST,
     "witness": _witness(".pow (.tp [.atom 1, .atom 2, .atom 3]) (.atom 5)"),
     "refinement":
        "a real patch that distributes the exponent across every factor of the "
        "base EXCEPT the last one produces a tensor product whose final factor "
        "is unraised, while the F2P requires EVERY factor raised. Measured "
        "against the real repo: the F2P FAILS on all four of its "
        "power-of-a-tensor-product assertions, each returning a result whose "
        "leading factors are correct and whose last factor is bare, while all "
        "four P2P tests pass. Faithful but non-resolving.",
     "rationale":
        "rejection from the postcondition on a PARTIAL sub-domain: this rival "
        "agrees with `specTensorPow` at every leading factor position and "
        "differs only at the last. Witnessed at three factors so the witness "
        "exhibits exactly that — two positions matching gold, the third bare — "
        "which is the sub-domain the refinement claims, rather than a coarser "
        "input where more than one position happens to be wrong."},
    {"id": "wrong-exponent-const", "kind": "uniqueness", "expect": "reject",
     "module": _R_CONST_EXP,
     "witness": _witness(".pow (.tp [.atom 0]) (.atom 9)"),
     "refinement":
        "a real patch that raises every factor to a FIXED exponent instead of "
        "to the one the input supplied resolves only those inputs whose "
        "exponent happens to equal the constant. Measured against the real "
        "repo: the F2P FAILS, and instructively it fails on exactly the "
        "assertions whose exponent is symbolic while PASSING the two whose "
        "exponent coincides with the hardcoded constant — a real partial-domain "
        "rival, not a uniformly wrong one. All four P2P tests pass. Faithful "
        "but non-resolving.",
     "rationale":
        "rejection from the postcondition via the EXPONENT argument of the "
        "per-factor power: the clause ties each result factor to "
        "`QExpr.pow b exp` for the input's own `exp`, and the rival supplies a "
        "literal. Witnessed at an exponent different from that literal — the "
        "sub-domain where the rival is wrong — since at the constant itself it "
        "agrees with gold."},
    {"id": "wrong-factor-broadcast", "kind": "uniqueness", "expect": "reject",
     "module": _R_BROADCAST,
     "witness": _witness(".pow (.tp [.atom 0, .atom 1, .atom 2]) (.atom 6)"),
     "refinement":
        "a real patch that raises the base's FIRST factor once per position, "
        "instead of raising each position's own factor, emits a tensor product "
        "whose factors are all the same power, where the F2P requires them to "
        "stay distinct and positionally grounded. Measured against the real "
        "repo: the F2P FAILS on all four of its power-of-a-tensor-product "
        "assertions, each returning the first factor's power duplicated across "
        "the positions, while all four P2P tests pass. Faithful but "
        "non-resolving.",
     "rationale":
        "rejection from the postcondition via the BASE argument of the "
        "per-factor power: the clause ties result position k to the power of "
        "input factor k, and the rival uses input factor 0 everywhere. Agrees "
        "with gold on a one-factor base, so it is witnessed at three factors, "
        "where positions two and three both lose their grounding while the "
        "exponent, factor count and order all stay correct."},
    {"id": "factor-order-reversed", "kind": "uniqueness", "expect": "reject",
     "module": _R_REVERSE,
     "witness": _witness(".pow (.tp [.atom 0, .atom 1]) (.atom 8)"),
     "refinement":
        "a real patch that raises every factor correctly but assembles them in "
        "reversed order produces a DIFFERENT expression, because the product "
        "being modeled is non-commutative. Measured against the real repo: the "
        "F2P FAILS on all four of its power-of-a-tensor-product assertions, "
        "each returning the right factors in the wrong positions, while all "
        "four P2P tests pass. The reversal was additionally confirmed to "
        "survive construction — the assembled object keeps the order it was "
        "given and compares unequal to the correctly-ordered one — so this is a "
        "real observable difference and not something the carrier normalizes "
        "away. Faithful but non-resolving.",
     "rationale":
        "rejection from the postcondition, ORDER behaviour: the multiset of "
        "raised factors is exactly right, so every other part of the clause is "
        "satisfied and only the positions differ. This is the part of the "
        "clause no other rival here attacks — factor order is observable "
        "content because the modeled product does not commute. Witnessed on a "
        "two-factor base, the smallest input where reversal is observable."},
    {"id": "inverted-branch-decision", "kind": "uniqueness", "expect": "reject",
     "module": _R_INVERTED,
     "witness": _witness(".pow (.tp [.atom 5, .atom 6]) (.atom 3)"),
     "refinement":
        "a real patch with the base test inverted leaves untouched exactly the "
        "shape it must distribute over, so every power-of-a-tensor-product F2P "
        "assertion fails with the input coming back unchanged — measured "
        "against the real repo, this patch fails the F2P and its four "
        "assertions over that shape while passing all four P2P tests. Faithful "
        "but non-resolving.",
     "rationale":
        "rejection from the postcondition via the branch DECISION rather than "
        "the branch body: the distributing arm's code is untouched, and what "
        "changes is which input reaches it. Witnessed on the tensor-product "
        "base — the arm whose mishandling is what actually drives the real "
        "patch's F2P failure, so the witness demonstrates the same sub-domain "
        "the refinement argues over. This rival also deviates on the other arm "
        "(a power over a non-tensor-product base is wrapped into a fabricated "
        "single-factor tensor product), which the spec likewise forbids; that "
        "second deviation is not what the witness turns on, because measurement "
        "shows no F2P or P2P test ever reaches that arm."},
    # A ninth rival was built, witnessed and then DROPPED — see `_R_PASSTHRU`
    # above and the note beneath this list.
]

# ---------------------------------------------------------------------------
# DROPPED RIVAL — recorded, not shipped.
# ---------------------------------------------------------------------------
# `_R_PASSTHRU` (below) attacks the remaining arm of the postcondition: an input
# that is not a power at all must come back unchanged, and this rival fabricates
# an exponent onto the factors of a bare tensor product instead. It is a
# well-formed same-spec variant, and its refutation witness
# (`_witness(".tp [.atom 0, .atom 1]")`) was built and SEEN to discriminate —
# it elaborates against the rival and fails on the frozen solution.
#
# It is not shipped because its `refinement` obligation cannot be met honestly.
# The manifest contract requires each reject case to argue why its faithful real
# patch would NOT resolve the F2P, so that a rival which verified would be a
# true verify-does-not-imply-resolve break. Measured against the real repo at
# `base_commit` (gold + test_patch applied, the corresponding real patch
# substituted, both the F2P and all four P2P tests run): that patch RESOLVES —
# it passes the F2P and every P2P test, with all five F2P assertion values
# byte-identical to gold, and the whole surrounding test directory reporting the
# same counts. Instrumenting the arm shows why: across the entire test file the
# evaluation is entered four times and every one of them is a power over a
# tensor-product base, so this arm is never reached and the behaviour change is
# real but unobserved.
#
# So the honest disposition is a KNOWN GAP rather than a case: the spec pins
# this arm (correctly — gold does return such an input unchanged), but no rival
# confined to it can be refinement-justified, because no F2P or P2P test
# observes it. Shipping the case anyway would have attached a false refinement
# argument to a passing case, which is the corrupt-artifact failure mode this
# battery exists to avoid. The neighbouring arm — a power whose base is NOT a
# tensor product — IS attacked, by `inverted-branch-decision`, whose witness
# probes exactly that input.
_R_PASSTHRU = _swap(_BASE, _OUTER_FALLTHROUGH, """  | .tp args =>
      return .tp (args.map (fun b => QExpr.pow b (QExpr.atom 2)))
  | _ => return e""")
