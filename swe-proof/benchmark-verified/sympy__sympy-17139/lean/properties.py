# properties.py — G-PBT spec-lane manifest for sympy__sympy-17139 (lean backend).
# NOT a Lean file; a record of adversarial falsification cases the gate executes
# and stamps with a verdict.
#
# Each SPEC_TESTS["module"] is a FULL Solution.lean built by region surgery: we
# read the frozen Solution.lean and _swap text ONLY inside the -- impl-start /
# -- impl-end region (and, for the soundness positives, inside
# -- proof-start / -- proof-end, since a reshaped implementation must be
# REPROVEN rather than have its obligation weakened). The spec regions
# (axioms / pure / post-conditions) are therefore untouched by construction, so
# markers.same_spec holds and every rejection is attributable to the
# postcondition rather than to a tampered spec. The `theorem correct_powerRewrite`
# STATEMENT is byte-identical in every case; only tactic bodies differ.
#
# DEFENDED SURFACE (read Solution.lean + mapping.md + refinement.md + instance.json)
#
#   problem_spec_powerRewrite (rv : Expr) (result : Expr) : Prop
#
# is a three-conjunct, mutually exclusive dispatch keyed on two boolean queries
# of the input expression, and it pins the result on EVERY input — there is no
# free output component (SPEC_GUIDE directive 5) and no ungrounded oracle to echo
# (directive 8): the result is always exactly `rv` or exactly `transform rv`,
# selected by the two queries.
#
#   C1  isMatchingPow rv = false                        → result = rv
#   C2  isMatchingPow rv = true → expIsReal rv = false   → result = rv
#   C3  isMatchingPow rv = true → expIsReal rv = true    → result = transform rv
#
# C2 is the load-bearing clause: it is the one an implementation that skips the
# realness query cannot satisfy, and the one whose faithful real counterpart is
# the difference between the two artifacts in this bundle.
#
# THE CARRIER IS OPAQUE, and that shapes every witness here. `Expr` is a `Nat`
# tag and all three callees (`isMatchingPow`, `expIsReal`, `transform`) are
# `opaque` with NO constraining axiom, so `decide` gets stuck on the opaque term
# and no rival's violation is a closed theorem over literal inputs alone. The
# uniqueness lane is nevertheless fully expressible, by CONDITIONING on the
# carrier instead of computing it: each witness fixes a concrete tag, states by
# hypothesis which branch that tag selects (one hypothesis per query, both about
# DIFFERENT terms so they are jointly satisfiable), assumes only that the rewrite
# actually moves the expression, and derives the contradiction from the clause
# the rival violates. That claim is stronger than any literal input could make:
# whenever the rewrite is not the identity at that point, the rival's answer
# differs from the one the spec mandates. Each witness has been built against the
# rival (elaborates) and against the frozen solution (fails), and its binders
# probed for joint satisfiability (`False` does NOT follow).
#
# AND THE GOLD-SIDE FAILURE IS A REFUTATION, NOT A TACTIC GAP — checked by the
# two experiments that tell those apart, because "the error looks semantic" is
# not evidence. Each witness fails on gold with an application type mismatch
# rather than a plain evaluation, so both were run for every reject case:
#
#   * REVEAL THE TYPE. Replace only the final `exact ht h` with `exact (h : Nat)`
#     so Lean prints what the witness's hypothesis actually IS after the `simp
#     only`. On the frozen solution it prints `h has type True` — `simp` PROVED
#     the clause's equation there, which is why nothing remains to contradict. On
#     each rival it prints the concrete unproven equation instead: `transform 5 =
#     5`, `transform 3 = 3`, `7 = transform 7`, `transform (transform 11) =
#     transform 11`, `13 = transform 13`, `transform 9 = 9`, and for the
#     one-tag rival the un-reduced `(if (4 == 4) = true then transform 4 else 4)
#     = 4`. True-versus-a-live-equation is the refutation.
#
#   * FLIP THE CLAIM. Drop the `¬` and assert instead that the implementation
#     SATISFIES the spec at the witness's own tag, under the witness's own
#     hypotheses. Against the frozen solution that flipped claim ELABORATES (exit
#     0) for all seven tags; against every rival it FAILS (exit 1), leaving goals
#     like `⊢ pure (transform 5) = 5` where gold left `⊢ pure 5 = 5`. So the
#     gold-side exit code tracks the claim rather than being constant, which is
#     exactly what a hollow case cannot show: a witness asserting gold is correct
#     at these points is accepted, and one asserting it is wrong is refused.
#
# WHAT PORTED, AND WHAT DID NOT — see `assessment` in the submitted payload. In
# brief: nagini contracts a five-argument branch-tag function whose whole
# sign/magnitude/parity/perfect-power sub-dispatch is, on this carrier, folded
# into the single opaque `transform`. So nagini's FIVE partial-domain rivals
# (odd-parity, even-parity, ignore-the-flag, the squared boundary magnitude, and
# the over-maximum magnitude), which each flip one magnitude sub-case, have NO
# counterpart here: the sub-cases live inside `transform` and are not modeled, so
# the analogous edits are not expressible. What IS modeled — the guarded
# three-way branch — is attacked seven ways below. nagini's two frame-mutation
# rivals are vacuous on this backend (Lean is referentially transparent: there
# are no fractional permissions and no writable input), and its AXIOM_TESTS are
# the G-AX lane's business, which this gate ignores.
#
# One further nagini rival is dropped with a MACHINE-CHECKED reason rather than
# an argued one, because it is a control-flow rival of exactly the class ported
# below and so deserves more than prose. nagini's `guard-after-ordering` moves the
# realness query to AFTER the rewrite tail instead of before it; on nagini that is
# rejected, because the tail's own precondition demands realness at the point it
# is entered. Here it is VACUOUS, and demonstrably so: `transform` is a pure total
# function, so computing it and then discarding it on the not-real branch is
# invisible. The corresponding rival (`let t := transform rv` hoisted above the
# realness test, returning `t` only on the real branch) was built and is
# DEFINITIONALLY EQUAL to the frozen implementation — `example (rv : Expr) :
# rivalAfter rv = implementation_powerRewrite rv := rfl` elaborates, exit 0. An
# observably-identical rival is a vacuous case by attack C, so it is dropped
# rather than shipped. The distinction nagini keeps (evaluation ORDER being
# observable through a callee precondition) is one a total pure carrier does not
# have; recovering it would need `transform` to be partial or effectful, which
# would change the frozen spec.
#
# NO DIVERGENCE LANE EXISTS TO PORT, and the precise reason matters because two
# nearby reasons are wrong. The frozen file sets no termination semantics option
# at all: `implementation_powerRewrite` is a total Lean `def`, so this is the
# `total` disposition, under which a diverging rival is genuinely rejected. Such
# a rival IS expressible — a self-calling `def` was built and IS rejected (exit
# 1, `fail to show termination for implementation_powerRewrite`), so it is NOT
# true that the carrier admits no such rival. What it admits no WITNESS for: the
# rival's own impl region fails to elaborate, so every witness build against it
# fails on the RIVAL side, which is the half that must succeed. Measured: a
# refutation witness against it exits 1, and so does a TRIVIALLY TRUE witness
# (`(1:Nat) + 1 = 2`, exit 1, same termination error) — the file simply does not
# compile, so no claim can be stated over it. Spelling the rival `partial def`
# makes the file compile but then no witness DECIDES: the claim goes stuck
# (`decide ... did not reduce to isTrue or isFalse`), which the gate records as
# `witness-undecided`, an inconclusive outcome that FAILS the battery rather than
# passing it. `witness_reference` does not help, since it substitutes for the GOLD
# side and the rival side is what is blocked. So the class is not shippable here
# on the gate's own rules, and the nagini sibling carries no diverge-*/nonterm-*
# case to port either. The corpus-level divergence question is settled and
# recorded in the corpus-wide termination-semantics finding, which measures it as a real spec hole
# on the velvet `partial` bundles; that finding is cited, not re-derived, and no
# new spec_holes entry is claimed for it.
#
# WHY THE UNIQUENESS LANE IS COMPLETE, as a proof rather than as a sample. The
# three clauses are mutually exclusive and jointly exhaustive over the two
# boolean queries, and they pin the result on every input, so the spec is
# FUNCTIONAL: it determines `result` uniquely. That was machine-checked against
# the frozen file (exit 0) rather than asserted —
#
#   theorem spec_functional (rv r1 r2 : Expr)
#       (h1 : problem_spec_powerRewrite rv r1)
#       (h2 : problem_spec_powerRewrite rv r2) : r1 = r2
#   theorem spec_pins_gold (rv r : Expr)
#       (h : problem_spec_powerRewrite rv r) : r = implementation_powerRewrite rv
#
# — the second following from the first plus `correct_powerRewrite`. So ANY
# implementation that differs from the frozen one at even one input is rejected,
# which closes SPEC-TOO-WEAK for the whole binder rather than for the tags the
# rivals below happen to name. The rivals still earn their keep: they are what
# makes each individual clause's rejection attributable and witnessed. (These two
# lemmas are audit scaffolding, not shipped cases: `variant_scope` bans a new
# top-level theorem in a variant, correctly, so they live outside the battery.)

from pathlib import Path

INSTANCE = "sympy__sympy-17139"
FLOAT_ENCODING = None  # meta.json carries no float_encoding

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl BODY (the lines strictly inside the impl markers, after the
# `def` header). Anchored on a substring that lies entirely within the impl
# region and occurs exactly once in the file.
_GOLD_BODY = """  if !(isMatchingPow rv) then
    return rv
  if !(expIsReal rv) then
    return rv
  return transform rv"""

# The header + body, for the one variant that replaces the whole definition.
_GOLD_DEF_HEADER = "def implementation_powerRewrite (rv : Expr) : Expr := Id.run do\n"

# The frozen tactic body, strictly inside the proof markers. Only a soundness
# positive touches this, and only to REPROVE the identical obligation for its
# reshaped implementation — never to weaken it.
_GOLD_PROOF = """  intro rv
  unfold problem_spec_powerRewrite implementation_powerRewrite
  refine ⟨?_, ?_, ?_⟩
  · intro h
    simp only [Id.run, h, Bool.not_false, if_true, pure]
  · intro h1 h2
    simp only [Id.run, h1, h2, Bool.not_true, Bool.not_false, if_true, bind, pure,
      Bool.false_eq_true, if_false]
  · intro h1 h2
    simp only [Id.run, h1, h2, Bool.not_true, bind, pure, Bool.false_eq_true, if_false]"""


def _impl(body: str) -> str:
    """Full Solution.lean with the impl BODY replaced; proof left frozen."""
    return _swap(_BASE, _GOLD_BODY, body)


def _impl_def(whole_def: str) -> str:
    """Full Solution.lean with the whole impl DEFINITION replaced."""
    return _swap(_BASE, _GOLD_DEF_HEADER + _GOLD_BODY, whole_def)


def _reproved(module: str, proof: str) -> str:
    """Replace the tactic body only. The `theorem correct_powerRewrite`
    statement is outside the swapped text, so it stays byte-identical."""
    return _swap(module, _GOLD_PROOF, proof)


# ---------------------------------------------------------------------------
# Witness template
# ---------------------------------------------------------------------------
# Every reject witness has the same shape, because every rival is refuted the
# same way: name a concrete tag, pin the two branch queries at that tag by
# hypothesis (they are hypotheses about two DIFFERENT opaque terms, so nothing
# forces them into conflict — verified: `False` does not follow), assume the
# rewrite is not the identity there, take the clause of the spec the rival
# violates, reduce the rival's control flow under the two pinned queries, and
# close. `simp only` with an explicit lemma list keeps the reduction from
# accidentally discharging the goal by any other route.

def _witness(tag: int, matching: str, real: str, clause: str, moves: str) -> str:
    return (
        f"example (hm : isMatchingPow {tag} = {matching}) "
        f"(hr : expIsReal {tag} = {real})\n"
        f"    (ht : {moves}) :\n"
        f"    ¬ problem_spec_powerRewrite {tag} "
        f"(implementation_powerRewrite {tag}) := by\n"
        f"  intro hspec\n"
        f"  have h := hspec{clause}\n"
        f"  simp only [implementation_powerRewrite, Id.run, hm, hr, Bool.not_true,\n"
        f"    Bool.not_false, if_true, if_false, bind, pure, Bool.false_eq_true] at h\n"
        f"  exact ht h\n")


# ---------------------------------------------------------------------------
# SPEC LANE
# ---------------------------------------------------------------------------

SPEC_TESTS = [

    # === ADMISSIBILITY ======================================================
    # On a TOTAL carrier the obligation carries no hypothesis binder — it is
    # `∀ (rv : Expr)`, so there is no precondition whose strength could exclude
    # an input. That is NOT a reason to skip this lane: the analogue of
    # PRECOND-TOO-STRONG here is the obligation being UNSATISFIABLE at exactly
    # the input shape the reported failure occurs at, which an identity
    # re-verification of the frozen file cannot detect (it asserts only that the
    # frozen proof still closes, a fact the other eight cases already rest on).
    #
    # So this case does the thing an identity restatement does not: it discharges
    # the three clauses AT the concrete branch point of interest — a matching
    # expression whose exponent is NOT a real quantity, the corner where the
    # rewrite must be skipped — as an explicit `have` proved before the frozen
    # obligation is closed VERBATIM after it. The concrete point is described by
    # hypothesis rather than computed (the two queries are opaque, so no literal
    # decides them), and the `have` is proved by REDUCING the frozen impl's
    # control flow at that point, not by citing the frozen theorem.
    #
    # It is load-bearing rather than decorative, and that was measured, not
    # argued: the identical `have` was built against a rival that reaches the
    # rewrite without consulting the realness query, and it FAILS there with
    # `unsolved goals ... ⊢ transform 2 = 2` while elaborating against the frozen
    # implementation. So this case's verification is evidence about the frozen
    # decision at that input, and not merely that some proof script ran.
    {
        "id": "admiss-nonreal-branch-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _reproved(
            _impl(_GOLD_BODY),
            "  have _ground : isMatchingPow 2 = true → expIsReal 2 = false →\n"
            "      problem_spec_powerRewrite 2 (implementation_powerRewrite 2) := by\n"
            "    intro hm hr\n"
            "    unfold problem_spec_powerRewrite implementation_powerRewrite\n"
            "    refine ⟨?_, ?_, ?_⟩\n"
            "    · intro h; rw [hm] at h; exact absurd h (by decide)\n"
            "    · intro _ _\n"
            "      simp only [Id.run, hm, hr, Bool.not_true, Bool.not_false, "
            "if_true,\n"
            "        bind, pure, Bool.false_eq_true, if_false]\n"
            "    · intro _ h2; rw [hr] at h2; exact absurd h2 (by decide)\n"
            + _GOLD_PROOF),
        "rationale": "admissibility at the input shape that matters, not an "
                     "identity restatement. The obligation binds `∀ (rv : Expr)` "
                     "with no hypothesis, so no precondition can be too strong in "
                     "the literal sense; the live question is whether the three "
                     "clauses are JOINTLY dischargeable at the concrete corner "
                     "the reported failure arises at — a matching expression "
                     "whose exponent is not a real quantity, where C1's guard is "
                     "false, C2 fires, and C3's guard is false. This case proves "
                     "exactly that as a `have` at tag 2 (the point described by "
                     "hypothesis, since the two queries are opaque and no literal "
                     "decides them) and only then closes the frozen obligation "
                     "verbatim. Were the clauses unsatisfiable there — C2 "
                     "demanding the input while C3 demanded the rewrite at one "
                     "and the same point — the `have` would not close and the "
                     "whole bundle would be a vacuous obligation. Measured to be "
                     "load-bearing: the same `have` FAILS against a rival that "
                     "skips the realness query (`unsolved goals ⊢ transform 2 = "
                     "2`), so it is a claim about the frozen decision rather than "
                     "about the proof script.",
    },

    # === SOUNDNESS 1: the guards fused into one boolean test =================
    # Structurally different from the frozen cascade: no `Id.run do`, no early
    # returns, no imperative shape at all — a single conditional whose test is
    # the CONJUNCTION of the two queries. Behaviourally identical on every input
    # (`&&` is exactly the sequential short-circuit the cascade performs), so it
    # must verify. Its proof closes the SAME obligation with `simp [h...]` per
    # conjunct — no new lemma, no induction, one cheap build.
    {
        "id": "pos-fused-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _reproved(
            _impl_def(
                "def implementation_powerRewrite (rv : Expr) : Expr :=\n"
                "  if isMatchingPow rv && expIsReal rv then transform rv else rv"),
            "  intro rv\n"
            "  unfold problem_spec_powerRewrite implementation_powerRewrite\n"
            "  refine ⟨?_, ?_, ?_⟩\n"
            "  · intro h\n"
            "    simp [h]\n"
            "  · intro h1 h2\n"
            "    simp [h1, h2]\n"
            "  · intro h1 h2\n"
            "    simp [h1, h2]"),
        "rationale": "a CORRECT implementation with a structurally different "
                     "shape: the two-step early-return cascade is replaced by a "
                     "single conditional on the conjunction of the two branch "
                     "queries, dropping the imperative do-block entirely. On "
                     "every input it agrees with the frozen implementation (the "
                     "conjunction is precisely what the sequential short-circuit "
                     "computes), so all three clauses C1/C2/C3 hold and it must "
                     "verify; a rejection would be SPEC-TOO-STRONG — the spec "
                     "pinning an incidental syntactic shape rather than the "
                     "input→output relation. Reproved honestly (the obligation "
                     "statement is byte-identical; only the tactic body differs, "
                     "no helper lemma, no new axiom).",
    },

    # === SOUNDNESS 2: the two branch tests in the opposite order =============
    # The frozen cascade tests the structural query FIRST and the realness query
    # second. This variant nests them the other way round: realness outermost,
    # structural test inside. Still correct, because the two unchanged-result
    # branches return the same value — reordering two guards that share an
    # outcome is observationally invisible. This is the closest expressible
    # counterpart to nagini's `pos-reordered` (branch-order permutation).
    {
        "id": "pos-swapped-guard-order",
        "kind": "soundness",
        "expect": "verify",
        "module": _reproved(
            _impl(
                "  if expIsReal rv then\n"
                "    if isMatchingPow rv then\n"
                "      return transform rv\n"
                "    return rv\n"
                "  return rv"),
            "  intro rv\n"
            "  unfold problem_spec_powerRewrite implementation_powerRewrite\n"
            "  refine ⟨?_, ?_, ?_⟩\n"
            "  · intro h\n"
            "    simp [Id.run, pure, h]\n"
            "    try rfl\n"
            "  · intro h1 h2\n"
            "    simp [Id.run, pure, h1, h2]\n"
            "    try rfl\n"
            "  · intro h1 h2\n"
            "    simp [Id.run, pure, h1, h2]\n"
            "    try rfl"),
        "rationale": "a CORRECT implementation that permutes the two branch "
                     "tests: the realness query becomes the outer test and the "
                     "structural query the inner one, with the unchanged-result "
                     "arm duplicated. Since C1 and C2 mandate the SAME result "
                     "(`rv`), swapping two guards that share an outcome cannot "
                     "change any input's answer, so it must verify. The reject "
                     "cases below establish that the spec DOES pin which branch "
                     "each input takes; this case establishes that it does not "
                     "over-pin the syntactic order in which the queries are "
                     "asked. A rejection would be SPEC-TOO-STRONG.",
    },

    # === UNIQUENESS 1: C2 — the query is never asked (attacks the guard) =====
    # The load-bearing rival: an implementation that keeps the structural test
    # and then rewrites unconditionally. This is exactly the shape the frozen
    # bundle's prepatch carries, and it is the one C2 exists to refute.
    {
        "id": "reject-drop-realness-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  if !(isMatchingPow rv) then\n"
            "    return rv\n"
            "  -- ATTACK: the realness query is never asked; every matching\n"
            "  -- expression is fed to the rewrite regardless of its exponent.\n"
            "  return transform rv"),
        "witness": _witness(5, "true", "false", ".2.1 hm hr",
                            "transform 5 ≠ 5"),
        "refinement": "the faithful real counterpart of this variant is the "
                      "pre-fix source: a matching power whose exponent is not a "
                      "real quantity falls straight into the exponent-ordering "
                      "body, and ordering an exponent that is not real raises "
                      "instead of returning a value. Both F2P tests exercise "
                      "exactly that input — the reported reproducer and the "
                      "assertions pinning a matching power with a non-real "
                      "exponent to itself — so this variant's real patch does "
                      "not merely return a wrong expression, it raises, and "
                      "neither test_issue_17137 nor test__TR56 would pass. A "
                      "verifying rival here would therefore be a genuine "
                      "verify-does-not-imply-resolve break.",
        "rationale": "rejected by clause C2 (`isMatchingPow rv = true → "
                      "expIsReal rv = false → result = rv`): at an input where "
                      "the structural query holds and the realness query does "
                      "NOT, the spec mandates the input itself while the rival "
                      "returns the rewrite. The witness conditions on the "
                      "carrier — it fixes tag 5, pins `isMatchingPow 5 = true` "
                      "and `expIsReal 5 = false` (hypotheses about two distinct "
                      "opaque terms, jointly satisfiable), assumes only that the "
                      "rewrite moves that tag, and derives the contradiction "
                      "from C2. This is the binder-and-clause pair the whole "
                      "bundle turns on.",
    },

    # === UNIQUENESS 2: C2 again, but the guard is only PARTIALLY skipped =====
    # A NEAR-MISS of the case above: the realness guard is present and correct
    # for every input EXCEPT one distinguished tag, which is short-circuited into
    # the rewrite before the guard is ever reached. It therefore agrees with the
    # frozen implementation on strictly more of the domain than the rival above,
    # and it gets its own witness at the one input that distinguishes it — the
    # tag it special-cases — rather than sharing the witness above, which would
    # claim a sub-domain this rival does not actually get wrong.
    {
        "id": "reject-partial-one-tag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  if !(isMatchingPow rv) then\n"
            "    return rv\n"
            "  -- ATTACK: one distinguished expression bypasses the realness\n"
            "  -- query and is rewritten unconditionally; every other input is\n"
            "  -- handled exactly as the frozen implementation handles it.\n"
            "  if rv == 4 then\n"
            "    return transform rv\n"
            "  if !(expIsReal rv) then\n"
            "    return rv\n"
            "  return transform rv"),
        "witness": _witness(4, "true", "false", ".2.1 hm hr",
                            "transform 4 ≠ 4"),
        "refinement": "a real patch guarding the exponent for all inputs but "
                      "one still raises on that one: the excluded expression "
                      "reaches the ordering comparison with a non-real exponent, "
                      "which is precisely the failure the F2P tests were written "
                      "to catch. Because the rewrite is applied by a bottom-up "
                      "traversal that visits every sub-expression, an exception "
                      "on a single node aborts the whole simplification, so the "
                      "F2P assertions do not merely get a wrong answer for that "
                      "node — they raise. It would not resolve.",
        "rationale": "rejected by C2 at the ONE input it mishandles. Kept "
                      "distinct from reject-drop-realness-guard because it is a "
                      "strict near-miss: it satisfies C2 everywhere except at "
                      "the tag it special-cases, so its witness must sit AT that "
                      "tag (4) to demonstrate the sub-domain the rationale "
                      "claims. Its witness therefore probes a different input "
                      "point than every other case, which is what makes the "
                      "battery's evidence about C2 depend on the `rv` binder "
                      "rather than on one lucky tag.",
    },

    # === UNIQUENESS 3: C1 — the structural test is dropped ===================
    {
        "id": "reject-ignore-structural",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  -- ATTACK: the structural test is dropped; the realness query\n"
            "  -- alone decides, so a non-matching expression is rewritten.\n"
            "  if !(expIsReal rv) then\n"
            "    return rv\n"
            "  return transform rv"),
        "witness": _witness(3, "false", "true", ".1 hm",
                            "transform 3 ≠ 3"),
        "refinement": "the rewrite tail is only defined for the shape the "
                      "structural test recognises — it reads the exponent and "
                      "the base's argument. Applying it to an expression that is "
                      "not of that shape does not produce a wrong expression, it "
                      "fails on a missing attribute, and since the traversal "
                      "visits every sub-expression of every input, that fires on "
                      "essentially every case in both F2P tests and across the "
                      "P2P rewrite suite. It would not resolve.",
        "rationale": "rejected by clause C1 (`isMatchingPow rv = false → "
                      "result = rv`): at a tag where the structural query fails "
                      "but the realness query holds, the spec mandates the input "
                      "unchanged and the rival returns the rewrite. The witness "
                      "pins tag 3 into exactly that corner (`isMatchingPow 3 = "
                      "false`, `expIsReal 3 = true`) and closes from C1. This "
                      "case is what stops the battery from testing only the "
                      "realness query: it varies the FIRST query independently, "
                      "at a value no other witness holds it at.",
    },

    # === UNIQUENESS 4: C2 and C3 both — the realness query is INVERTED =======
    {
        "id": "reject-invert-realness-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  if !(isMatchingPow rv) then\n"
            "    return rv\n"
            "  -- ATTACK: the realness query's sense is inverted, so the two\n"
            "  -- branches it selects are exchanged.\n"
            "  if expIsReal rv then\n"
            "    return rv\n"
            "  return transform rv"),
        "witness": _witness(7, "true", "true", ".2.2 hm hr",
                            "(7 : Expr) ≠ transform 7"),
        "refinement": "inverting the sense of the guard is wrong in both "
                      "directions at once. A matching power whose exponent IS a "
                      "real quantity would be left untouched, so the F2P "
                      "assertions that pin such a power to its REWRITTEN form "
                      "fail outright; and a matching power whose exponent is not "
                      "real would still be fed to the ordering comparison, so "
                      "the reported reproducer still raises. Neither F2P test "
                      "would pass.",
        "rationale": "rejected by clause C3 (`isMatchingPow rv = true → "
                      "expIsReal rv = true → result = transform rv`): at a tag "
                      "where both queries hold, the spec mandates the rewrite "
                      "and the rival returns the input. The witness pins tag 7 "
                      "with both queries TRUE — the branch no other reject "
                      "witness probes — and closes from C3. Together with the "
                      "two C2 cases and the C1 case, this means every one of the "
                      "spec's three independent clauses is attacked, and the "
                      "`expIsReal` binder is varied (false at tags 4 and 5, true "
                      "at tags 3, 7, 11, 13) rather than held fixed.",
    },

    # === UNIQUENESS 5: C3 — the rewrite is applied, but not once =============
    # The result-VALUE attack rather than a branch-selection attack: the right
    # branch is chosen for every input, and the answer on that branch is still
    # wrong. This is what pins C3 to `transform rv` exactly, rather than to "some
    # application of transform".
    {
        "id": "reject-double-rewrite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  if !(isMatchingPow rv) then\n"
            "    return rv\n"
            "  if !(expIsReal rv) then\n"
            "    return rv\n"
            "  -- ATTACK: the correct branch is taken but the rewrite is applied\n"
            "  -- twice, so the value returned is not the rewrite of the input.\n"
            "  return transform (transform rv)"),
        "witness": _witness(11, "true", "true", ".2.2 hm hr",
                            "transform (transform 11) ≠ transform 11"),
        "refinement": "the rewrite tail is not idempotent: it re-expresses a "
                      "power of one function as a power of another, so applying "
                      "it a second time re-expresses the result again and yields "
                      "an expression of a different shape from the one the tests "
                      "pin. The P2P rewrite assertions and the F2P equalities "
                      "compare against the SINGLE-application form literally, so "
                      "a doubling patch produces unequal expressions and would "
                      "not resolve. (It also cannot be dismissed as harmless "
                      "re-normalisation: the traversal already visits every node "
                      "to fixpoint, so the second application is pure "
                      "corruption, not extra simplification.)",
        "rationale": "rejected by clause C3, on the VALUE rather than on the "
                      "branch: this rival selects the correct branch for every "
                      "input and still violates the spec, because C3 pins the "
                      "result to `transform rv` and not merely to something "
                      "reachable by rewriting. Without this case the battery "
                      "would only ever have attacked which branch fires, and a "
                      "rival that combined the callee's result wrongly on the "
                      "correct branch would pass unnoticed. The witness pins tag "
                      "11 with both queries true and assumes only that the "
                      "rewrite is not idempotent at that point.",
    },

    # === UNIQUENESS 6: C3 — nothing is ever rewritten ========================
    # The degenerate total-identity rival. Cheap, and it closes the last hole a
    # branch-selection-only battery would leave: an implementation that satisfies
    # both unchanged-result clauses perfectly and simply never does the work.
    {
        "id": "reject-never-rewrite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_def(
            "-- ATTACK: no query is asked and no rewrite is ever applied; every\n"
            "-- expression is returned unchanged.\n"
            "def implementation_powerRewrite (rv : Expr) : Expr := rv"),
        "witness": _witness(13, "true", "true", ".2.2 hm hr",
                            "(13 : Expr) ≠ transform 13"),
        "refinement": "a real patch that returned every expression untouched "
                      "would indeed stop the reported crash, and this is exactly "
                      "why the case matters: it is the cheapest way to make the "
                      "reported reproducer succeed while breaking the behavior "
                      "the rule exists for. The F2P test that pins matching "
                      "powers with real exponents to their rewritten forms fails "
                      "immediately, as does the P2P rewrite suite, so it would "
                      "not resolve even though the crash is gone. That "
                      "asymmetry — fixing the raise without preserving the "
                      "rewrite — is the failure mode C3 has to exclude.",
        "rationale": "rejected by clause C3: the identity satisfies C1 and C2 "
                      "vacuously well and violates C3 at any input where both "
                      "queries hold and the rewrite is not the identity. The "
                      "witness pins tag 13 there. Included because the spec must "
                      "be shown to demand the WORK, not just the guard — a "
                      "battery of guard-placement rivals alone would leave the "
                      "do-nothing implementation unexamined.",
    },

    # === UNIQUENESS 7: C1 at the query pair no other witness reaches ==========
    # Added by audit. The six rivals above jointly pin three of the four
    # (isMatchingPow, expIsReal) query pairs — (true,false) at tags 4 and 5,
    # (false,true) at tag 3, (true,true) at tags 7, 11, 13 — but NOT (false,
    # false). That corner is not redundant: C1 fires on a non-matching
    # expression regardless of the realness query, so an implementation may
    # satisfy C1 wherever the realness query holds and break it precisely where
    # it does not. Such a rival passes every witness above (each pins the
    # realness query somewhere it is not wrong) while violating C1. This case
    # is that rival, refuted at the missing pair, so the battery's evidence
    # covers the query product rather than three of its four cells.
    {
        "id": "reject-nonmatching-nonreal",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  if !(isMatchingPow rv) then\n"
            "    -- ATTACK: on a non-matching expression the realness query is\n"
            "    -- consulted anyway, and the rewrite is applied when it fails.\n"
            "    -- Every input on which the realness query HOLDS is handled\n"
            "    -- exactly as the frozen implementation handles it.\n"
            "    if !(expIsReal rv) then\n"
            "      return transform rv\n"
            "    return rv\n"
            "  if !(expIsReal rv) then\n"
            "    return rv\n"
            "  return transform rv"),
        "witness": _witness(9, "false", "false", ".1 hm",
                            "transform 9 ≠ 9"),
        "refinement": "the rewrite tail reads the exponent and the base's "
                      "argument, so it is only defined for the shape the "
                      "structural test recognises; applying it to an expression "
                      "of another shape fails on a missing attribute rather than "
                      "returning a wrong expression. The traversal visits every "
                      "sub-expression of every input, and a sub-expression that "
                      "is not a matching power and whose exponent query does not "
                      "return a definite affirmative is ordinary — a bare symbol "
                      "reaches this branch. So this fires broadly across both "
                      "F2P tests and the P2P rewrite suite, and it would not "
                      "resolve.",
        "rationale": "rejected by clause C1 (`isMatchingPow rv = false → "
                      "result = rv`) at the query pair no other case reaches: "
                      "both queries FALSE. reject-ignore-structural also attacks "
                      "C1, but only where the realness query holds, so a rival "
                      "wrong exclusively on the other side of that query "
                      "survives it — this rival is exactly that, agreeing with "
                      "the frozen implementation on every input whose realness "
                      "query holds. Its witness therefore sits at tag 9 with both "
                      "hypotheses false, which is what makes the battery's C1 "
                      "evidence independent of the `expIsReal` value rather than "
                      "conditional on it.",
    },
]
