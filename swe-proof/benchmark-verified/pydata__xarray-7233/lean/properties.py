# properties.py — PBT falsification battery for pydata__xarray-7233 (lean).
#
# NOT a Lean module: a record of adversarially-reasoned cases the G-PBT runner
# executes and stamps with a recorded verdict. Each spec case is a full
# Solution.lean variant built by region-surgery — it edits ONLY the impl region
# (and, for the soundness positive, the proof body), so the frozen spec
# (axioms / pure / post-conditions) stays byte-identical, same_spec holds by
# construction, and the `theorem correct_retainedCoordNames` STATEMENT is
# preserved verbatim. No case introduces sorry/admit/native_decide/axiom or any
# new theorem/lemma.
#
# PORT NOTE — carrier narrowing vs the nagini sibling.
# The nagini battery contracts the whole imperative rebuild loop over two
# read-only 0/1 arrays, with a per-position promotion helper, a termination
# obligation, and fractional-permission frame obligations on both inputs. This
# Lean bundle models only the purely functional core the patch actually changes:
# a single value — the collection of names reported as coordinates of the
# reshaped result — as a function of two name collections (the names of the
# dimensions being reshaped, `reshapedDims`, and the names that were coordinates
# beforehand, `priorCoordNames`). The sole load-bearing clause is
#     ∀ name, name ∈ result ↔ name ∈ priorCoordNames
# i.e. membership of the result is pinned to `priorCoordNames` EXACTLY — every
# prior coordinate name is retained and no other name is introduced, INDEPENDENT
# of `reshapedDims`. That independence (the set identity (W ∩ C) ∪ C = C) is the
# whole content of the fix, so it is where every rival is aimed.
#
# DEFENDED SURFACE (what every rival attacks): the membership equivalence, in
# both directions —
#   * BACKWARD (⊇): a prior coordinate name must be in the result. A rival that
#     keeps only the names common to the reshaped dimensions (or that drops a
#     prior coordinate name) loses a prior coordinate that is unrelated to any
#     reshaped dimension — the exact failure the issue reports.
#   * FORWARD (⊆): only prior coordinate names may be in the result. A rival that
#     also reports a reshaped-dimension name introduces a name that was never a
#     coordinate.
# Input binders of the spec predicate: `reshapedDims` and `priorCoordNames`. The
# six reject witnesses vary BOTH across distinct points — a reshaped dimension
# that is not a prior coordinate, a fully disjoint singleton pair, a two-name pair
# whose lists OVERLAP (so the common-names filter is non-empty at the refutation
# point), an empty reshaped list against a two-name prior list, a single-name
# sub-domain inside a two-name prior list, and a point whose refutation name is
# one the common-names filter ITSELF produces — so neither binder is held fixed
# and both directions of the equivalence are demonstrated.
#
# AUDIT NOTE (first pass: independent re-derivation of every witness, real
# builds). Two defects were found and repaired; see the case comments.
#   * `weak-over-promote-reshaped` originally refuted at reshapedDims=["x"],
#     priorCoordNames=["y"] — a fully DISJOINT singleton pair, i.e. the same
#     input SHAPE as `weak-reshaped-names-echoed`'s ["a"]/["b"] under a different
#     spelling. Every one of the four original points had an empty intersection,
#     so the common-names filter contributed `[]` at every refutation point and
#     no witness discriminated at a point where it computed anything. Repaired to
#     an OVERLAPPING two-name pair (common = one name, non-empty).
#   * The recorded reason for dropping the nagini non-termination rival ("a
#     diverging implementation cannot be written at all") is FALSE on this
#     carrier: `partial def implementation_retainedCoordNames … := implementation_
#     retainedCoordNames …` is writable and passes the variant scope check. It is
#     still not landable, but for a different reason, now stated below.
#
# AUDIT NOTE (second, INDEPENDENT pass — 122 real builds; three defects found and
# repaired, each with the exit codes that established it).
#   1. WITNESS SHAPE, all four backward-direction cases. The `_wit_bwd` helper
#      closed with `simp at this`, whose gold-side failure is `unsolved goals …
#      this : True ⊢ False` — a message that does not name the refuted claim.
#      Forgery-tested per attack B′ and it FAILED the whole-claim half: the same
#      statement with the `¬` dropped (i.e. asserting gold is CORRECT at that
#      point) BUILDS CLEAN on gold, exit 0, while failing on the rival, exit 1.
#      The gate would not have recorded that as a refutation, but the shipped
#      shape's gold exit was carried by a script-exhaustion message rather than by
#      an evaluated claim, and a type-revealing probe (`exact (hm : Nat)`) was
#      needed to show `simp` had proved the equation on gold (`h2 has type True`)
#      and not on the rival (`No goals to be solved`). Repaired BOTH helpers to
#      `exact absurd hm (by decide)`, which states the refutation as a decidable
#      proposition the kernel evaluates: every gold_signature is now a plain
#      evaluation that quotes the claim, and the `.mpr`/`.mp`-flipped forgery
#      evaluates a DIFFERENT proposition on each side. Re-measured all six: rival
#      exit 0, gold exit 1.
#   2. `weak-name-keyed-single-drop` refuted at the BYTE-IDENTICAL point as
#      `weak-common-names-only` (["time"]/["day"]) and recorded the identical
#      gold_signature. At that point its rival returns [] exactly as #1's does, so
#      the "narrowest sub-domain the spec must still catch" claim in its rationale
#      was asserted and never demonstrated. Repaired to ["time"]/["lat","day"],
#      where the rival returns ["lat"] — a strict non-empty subset. Verified by
#      evaluation that the rival RETAINS "lat" (exit 0 on both sides), which is
#      what makes it a near-miss rather than a second copy of #1.
#   3. The ADMISSIBILITY lane was dropped for a reason the brief names as
#      insufficient ("the frozen obligation has no precondition"). Landed as
#      `admissibility-f2p-shaped-input`; it verifies (exit 0).
# Also re-derived and left unchanged: the omission of the non-termination rival,
# whose recorded reason the second pass CONFIRMED by build — see below.
#
# OMITTED nagini cases and why (see `assessment` too):
#   * The two FRAME / permission-mutation rivals are VACUOUS on this backend:
#     Lean is referentially transparent, there is no aliasing or fractional
#     permission to violate, so there is no counterpart rival to author.
#   * The NON-TERMINATION rival is INEXPRESSIBLE here, but NOT because a
#     diverging impl cannot be written — it can (`partial def implementation_*
#     … := implementation_* …`, which passes the variant scope check). It is
#     inexpressible because such a rival cannot carry a WITNESS, which this
#     backend requires of every reject case. Measured: the diverging rival is
#     rejected (exit 1) with `Tactic 'unfold' failed to unfold
#     implementation_retainedCoordNames`, i.e. a `partial def` has no equation
#     lemmas, so its result is opaque to the kernel and no `decide`-based witness
#     can state a concrete refutation against it. The rejection is therefore an
#     UNFOLDING failure, not a semantic one — exactly the non-discriminating
#     shape the witness requirement exists to exclude — so the case would land as
#     `witness-unproven`, which is an inconclusive test rather than a pass.
#     (Distinct from the velvet `partial`-semantics spec hole, which is recorded
#     in the corpus-wide termination-semantics finding and is not re-litigated here: on lean the
#     obligation is a total `def` and the diverging rival does not verify.)
#     SECOND-PASS CONFIRMATION, by build, including the escape the brief warns is
#     usually wrong ("the carrier is opaque, so no witness can be built"): the
#     HYPOTHESIS-CONDITIONED form was tried, not just the decide form. A witness
#     stating its refutation at a point described by hypothesis
#     (`example (h : implementation_… ["time"] ["day"] = []) : ¬ problem_spec_… `)
#     ELABORATES against the diverging rival (exit 0) — but it also elaborates
#     against the FROZEN SOLUTION (exit 0), because the hypothesis is false of
#     gold and the script derives the refutation from it. Both halves succeed, so
#     the gate records `witness-vacuous`: the conditioned form does not
#     discriminate here. Unlike an `opaque` callee, `implementation_*` is the very
#     symbol the rival REPLACES, so conditioning on its value is conditioning on
#     the thing under test rather than on an external carrier. That is why this
#     omission stands where the brief's five overturned ones did not: the escape
#     was attempted and measured, and both available witness shapes fail — the
#     decide form as an unfolding failure (exit 1 on the rival, so
#     `witness-unproven`), the conditioned form as vacuity.
#     Divergence disposition per attack F′: this bundle sets NO
#     `loom.semantics.termination` option (the frozen impl is a total `def`, no
#     recursion), so the "total" branch's shippable-reject reading does not apply
#     — there is no termination obligation for a measure-less loop to fail. The
#     class is a KNOWN HOLE, not vacuous: a diverging rival is writable and is
#     rejected, but cannot carry a discriminating witness on this carrier.
#   * The ADMISSIBILITY positive was originally recorded as having "no
#     counterpart" because `correct_retainedCoordNames` is an UNCONDITIONAL
#     `∀ reshapedDims priorCoordNames` with no precondition hypothesis. AUDIT
#     (second pass): that is the reason the brief names as insufficient, and it is
#     insufficient here — the total-carrier analogue of PRECOND-TOO-STRONG is the
#     obligation being unsatisfiable at an F2P-shaped input, which is testable
#     with no precondition at all. The lane is now LANDED as
#     `admissibility-f2p-shaped-input` below (verifies, exit 0), so this is no
#     longer an omission.
#   * AXIOM_TESTS are dropped: the axiom lane is G-AX's job and this bundle ships
#     no consumed axiom (the value is modeled structurally as a filter followed
#     by a union, not over an opaque callee).
from pathlib import Path

INSTANCE = "pydata__xarray-7233"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors — all strictly INSIDE the impl / proof regions of the frozen
# Solution.lean, each unique in the file.
# ---------------------------------------------------------------------------

# The result-binding line of the frozen impl (union of the common names with the
# prior coordinate names). Uniquely identifies the value the impl returns.
_GOLD_RESULT = "  let result := common ++ priorCoordNames\n"

# The full frozen impl body (used by the soundness positive, which reshapes the
# value computation and therefore needs a proof that closes for the new shape).
_GOLD_IMPL = """  -- the names common to the reshaped dimensions and the prior coordinates
  let common := reshapedDims.filter (fun d => priorCoordNames.contains d)
  -- together with every prior coordinate name
  let result := common ++ priorCoordNames
  return result"""

# The frozen proof body (only touched by the soundness positive).
_GOLD_PROOF = """  intro reshapedDims priorCoordNames
  unfold problem_spec_retainedCoordNames implementation_retainedCoordNames
  intro name
  simp only [Id.run, pure, List.mem_append,
    List.mem_filter, List.elem_eq_mem, decide_eq_true_eq]
  constructor
  · rintro (⟨_, hc⟩ | h)
    · exact hc
    · exact h
  · intro h
    exact Or.inr h"""


# ---------------------------------------------------------------------------
# SOUNDNESS POSITIVE — structurally different but CORRECT.
# Drops the common-names prefix entirely and returns the prior coordinate names
# directly. This is value-equivalent to gold (the common names are a subset of
# the prior coordinate names, so (W ∩ C) ∪ C = C), but a genuinely different
# computation shape — no filter, no append. The proof reduces the `do` block; the
# membership equivalence then holds by reflexivity of `∈` on the same list. Must
# verify; if a faithful correct reshape could not satisfy the membership clause,
# the spec would be SPEC-TOO-STRONG.
_POS_IMPL = """  -- every prior coordinate name is a coordinate of the result; the common-names
  -- prefix is redundant, so the result is exactly the prior coordinate names.
  let result := priorCoordNames
  return result"""

_POS_PROOF = """  intro reshapedDims priorCoordNames
  unfold problem_spec_retainedCoordNames implementation_retainedCoordNames
  intro name
  simp only [Id.run, pure]"""


# ---------------------------------------------------------------------------
# ADMISSIBILITY POSITIVE — the frozen impl and the frozen proof, PRECEDED by a
# discharge of the obligation at one concrete F2P-shaped input. The impl region
# is untouched; only the proof body gains a prefix, and the frozen script itself
# is appended byte-identically so the general obligation is still closed the
# frozen way. The two `have`s are `clear`ed so they cannot be load-bearing for
# it: the case fails if and only if the obligation is unsatisfiable at that
# input, which is the total-carrier reading of PRECOND-TOO-STRONG.
_ADM_PROOF = """  -- ADMISSIBILITY: before closing the general obligation, discharge it at one
  -- CONCRETE input of the shape the failing scenario uses — a reshaped dimension
  -- name together with a prior coordinate name that is NOT itself a reshaped
  -- dimension. Both `have`s go through by kernel EVALUATION of the impl, so this
  -- exhibits an input at which the obligation is actually satisfiable rather than
  -- vacuously quantified. They are cleared before the frozen script runs.
  have h_eval : implementation_retainedCoordNames ["time"] ["day"] = ["day"] := by
    decide
  have h_sat : problem_spec_retainedCoordNames ["time"] ["day"]
      (implementation_retainedCoordNames ["time"] ["day"]) := by
    unfold problem_spec_retainedCoordNames
    rw [h_eval]
    intro name
    exact Iff.rfl
  clear h_eval h_sat
""" + _GOLD_PROOF


# ---------------------------------------------------------------------------
# Witnesses. The spec predicate quantifies over `name : String`, which cannot be
# `decide`d directly (String is infinite). Each witness therefore INSTANTIATES
# the universal at one concrete name where the rival and gold disagree, and
# derives `False` from that single equivalence. Every witness holds of its rival
# (verified: build succeeds) and fails on gold (verified: build fails) at a
# DISTINCT (reshapedDims, priorCoordNames) point. Neither helper binds anything
# in its head, so `consistency_probe` is None and no prove-from-a-contradiction
# forgery is reachable: every refutation is stated at literal inputs.
#
# AUDIT NOTE — why both helpers close with `absurd … (by decide)` and not
# `simp at this`. The two are NOT interchangeable as gold-side evidence, and the
# difference was measured with real builds rather than reasoned about.
#
# The original backward helper closed with `simp at this`. On the RIVAL that
# works: `simp` reduces the membership obtained via `.mpr` to `False` and closes
# the goal. But on GOLD the same script fails with
#     error: unsolved goals   h : ∀ (name : String), … ⊢ False
# because `simp` REDUCED the hypothesis to `True` (gold really does contain the
# name) and then had nothing to contradict. That error is about the SCRIPT
# running out of goals, not about the claim, so it had to be forgery-tested. It
# fails that test in the direction that matters: replacing the final step with a
# deliberate type ascription (`exact (hm : Nat)`) prints
#     Type mismatch: h2 has type True … but is expected to have type ℕ
# on GOLD and `No goals to be solved` on the RIVAL — i.e. the hypothesis really
# was `True` on gold — but a WHOLE-CLAIM forgery (the same statement with the `¬`
# dropped, closed by `simp [Id.run, pure]`) BUILDS CLEAN on gold (exit 0) and
# fails on the rival (exit 1). So the old shape's gold-side exit code was
# carrying information only through an `unsolved goals` message whose text does
# not name the refuted claim at all.
#
# `exact absurd hm (by decide)` states the refutation as a concrete decidable
# proposition instead, so the kernel EVALUATES it and the error names the claim:
#     Tactic `decide` proved that the proposition
#       "day" ∉ (have common := … ; have result := common ++ ["day"]; pure result).run
#     is false
# Measured for all four such cases: rival exit 0, gold exit 1 with that plain
# evaluation, and the forgery (the same witness with `.mpr` swapped for `.mp`,
# i.e. claiming the name was never a prior coordinate) fails on BOTH sides with a
# DIFFERENT evaluated proposition — the error text tracks the claim, which is
# exactly what the old shape did not do.
# ---------------------------------------------------------------------------

def _wit_bwd(reshaped, prior, name):
    """Backward-direction refutation: `name ∈ result` fails though it was a
    prior coordinate. Uses `.mpr` to get `name ∈ result`, then refutes it by
    KERNEL EVALUATION (`absurd … (by decide)`) so the failure names the claim."""
    return (
        "example : ¬ problem_spec_retainedCoordNames\n"
        f"    {reshaped} {prior}\n"
        f"    (implementation_retainedCoordNames {reshaped} {prior}) := by\n"
        "  unfold problem_spec_retainedCoordNames implementation_retainedCoordNames\n"
        "  intro h\n"
        f'  have hm := (h "{name}").mpr (by decide)\n'
        "  exact absurd hm (by decide)")


def _wit_fwd(reshaped, prior, name):
    """Forward-direction refutation: `name ∈ result` although it was never a
    prior coordinate. Uses `.mp` to get `name ∈ priorCoordNames`, then refutes it
    by kernel evaluation for the same reason as `_wit_bwd`."""
    return (
        "example : ¬ problem_spec_retainedCoordNames\n"
        f"    {reshaped} {prior}\n"
        f"    (implementation_retainedCoordNames {reshaped} {prior}) := by\n"
        "  unfold problem_spec_retainedCoordNames implementation_retainedCoordNames\n"
        "  intro h\n"
        f'  have hm := (h "{name}").mp (by decide)\n'
        "  exact absurd hm (by decide)")


# ===========================================================================
# SPEC_TESTS
# ===========================================================================
SPEC_TESTS = [

    # --- SOUNDNESS POSITIVE ----------------------------------------------
    {
        "id": "pos-control-prior-names-directly",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _GOLD_IMPL, _POS_IMPL),
                        _GOLD_PROOF, _POS_PROOF),
        "rationale": (
            "A structurally-different but CORRECT impl: it drops the common-names "
            "prefix and returns the prior coordinate names directly. This is "
            "value-equivalent to the frozen impl (the common names are a subset of "
            "the prior coordinate names, so their union is just the prior "
            "coordinate names), but a genuinely different computation — no filter, "
            "no append. The proof reduces the `do` block and the membership "
            "equivalence holds definitionally on the same list. It must verify "
            "against the clause `∀ name, name ∈ result ↔ name ∈ priorCoordNames`; "
            "if a faithful correct reshape could not satisfy it, the spec would be "
            "SPEC-TOO-STRONG (rejecting a correct output)."
        ),
    },

    # --- UNIQUENESS #1: common-names only (backward direction) -----------
    {
        "id": "weak-common-names-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_RESULT, "  let result := common\n"),
        "refinement": (
            "Reports only the names common to BOTH the reshaped dimensions and the "
            "prior coordinates — the exact behavior the issue reports as the bug. A "
            "faithful patch keeping this would drop every prior coordinate name "
            "that is not itself a reshaped dimension; the failing test builds an "
            "input with precisely such a name and asserts it is still a coordinate "
            "of the result. So the patch would NOT resolve, and a verifying rival "
            "here would be a true verify-does-not-resolve break."
        ),
        "rationale": (
            "Rejected by the BACKWARD direction of the membership clause: at a name "
            "that was a prior coordinate but is not among the reshaped dimensions, "
            "the clause demands `name ∈ result` but this rival omits it. Witness at "
            "reshapedDims=[\"time\"], priorCoordNames=[\"day\"] — \"day\" is a prior "
            "coordinate, is not a reshaped dimension, and is dropped."
        ),
        # Holds of the rival ("day" ∉ result=[]), fails on gold ("day" ∈ result).
        "witness": _wit_bwd('["time"]', '["day"]', "day"),
    },

    # --- UNIQUENESS #2: reshaped names echoed (both directions wrong) ----
    {
        "id": "weak-reshaped-names-echoed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_RESULT, "  let result := reshapedDims\n"),
        "refinement": (
            "Reports the reshaped-dimension names instead of the prior coordinate "
            "names — keying coordinate status off which dimensions are reshaped "
            "rather than off prior status. A faithful patch doing this drops any "
            "prior coordinate that is not a reshaped dimension AND promotes any "
            "reshaped dimension that was not a coordinate, so the coordinate set of "
            "the result no longer matches the prior coordinate set and the failing "
            "test does NOT resolve."
        ),
        "rationale": (
            "Rejected by the FORWARD direction: at a reshaped-dimension name that "
            "was never a prior coordinate, the clause forbids `name ∈ result` but "
            "this rival includes it. Witness at reshapedDims=[\"a\"], "
            "priorCoordNames=[\"b\"] — \"a\" is reshaped, was not a coordinate, yet "
            "is reported. This point is disjoint from every other rival's point."
        ),
        # Holds of the rival ("a" ∈ result, "a" ∉ prior), fails on gold.
        "witness": _wit_fwd('["a"]', '["b"]', "a"),
    },

    # --- UNIQUENESS #3: over-promotion (forward direction) ---------------
    {
        "id": "weak-over-promote-reshaped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_RESULT,
                        "  let result := common ++ priorCoordNames ++ reshapedDims\n"),
        "refinement": (
            "Retains every prior coordinate (so it is correct on the backward "
            "direction) but ALSO appends the reshaped-dimension names, promoting "
            "names that were never coordinates. A faithful patch adding the "
            "reshaped dimensions to the coordinate set would introduce extra "
            "coordinates absent from the input; the failing test asserts the "
            "coordinate list is preserved EXACTLY, so the extra names make it "
            "diverge and the patch does NOT resolve."
        ),
        "rationale": (
            "Rejected by the FORWARD direction, at a point structurally DISTINCT "
            "from rival #2: this rival is correct on every prior coordinate, so it "
            "is refuted only by a reshaped name that was not a prior coordinate. "
            "Witness at reshapedDims=[\"time\", \"x\"], "
            "priorCoordNames=[\"time\", \"day\"] — the two lists OVERLAP at "
            "\"time\", so the common-names filter is NON-EMPTY here (common = "
            "[\"time\"]), and the refutation is at \"x\": a reshaped dimension "
            "that is not a prior coordinate, introduced though it was never a "
            "coordinate. This is the only reject point at which the filter clause "
            "contributes anything, so it is what distinguishes this case from #2 "
            "rather than a second spelling of the same disjoint-singleton shape. "
            "(AUDIT: the original point reshapedDims=[\"x\"], "
            "priorCoordNames=[\"y\"] was a disjoint singleton pair — the same "
            "input shape as #2's [\"a\"]/[\"b\"] — leaving the filter unexercised "
            "at every refutation point in the battery.)"
        ),
        # Holds of the rival ("x" ∈ result, "x" ∉ prior), fails on gold with a
        # semantic `decide` refutation over a NON-EMPTY common-names filter.
        "witness": _wit_fwd('["time", "x"]', '["time", "day"]', "x"),
    },

    # --- UNIQUENESS #4: drops a leading prior coordinate -----------------
    {
        "id": "weak-drop-leading-prior-coord",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_RESULT,
                        "  let result := common ++ priorCoordNames.tail\n"),
        "refinement": (
            "Retains the common names and all-but-the-first prior coordinate name, "
            "so it is correct except when the first prior coordinate is not itself "
            "a reshaped dimension. A faithful patch that special-cased the first "
            "coordinate name (dropping it) would lose that coordinate from the "
            "result whenever the input's first coordinate is a non-dimensional one; "
            "the failing test's first coordinate is exactly such a name, so the "
            "patch does NOT resolve."
        ),
        "rationale": (
            "Rejected by the BACKWARD direction at a point that also varies BOTH "
            "binders (empty reshaped list, two-name prior list): the leading prior "
            "coordinate name is demanded in the result but this rival drops it. "
            "Witness at reshapedDims=[], priorCoordNames=[\"lat\", \"lon\"] — "
            "\"lat\" is a prior coordinate dropped by `.tail`."
        ),
        # Holds of the rival ("lat" ∉ tail=["lon"]), fails on gold.
        "witness": _wit_bwd('[]', '["lat", "lon"]', "lat"),
    },

    # --- UNIQUENESS #5: name-keyed near-miss (added by audit) -------------
    # Closes a threat class the other four rivals leave unattacked: each of them
    # is wrong on a whole CLASS of inputs, so any test with a non-degenerate
    # input catches them. This one is wrong at exactly ONE name and correct on
    # every input that does not mention it — the weakest rival the spec must
    # still reject, and what makes the ∀ over `name` load-bearing rather than
    # merely present.
    {
        "id": "weak-name-keyed-single-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_RESULT,
                        "  let result := priorCoordNames.filter "
                        "(fun n => n != \"day\")\n"),
        "refinement": (
            "Retains every prior coordinate EXCEPT one specific name, and is "
            "otherwise exactly right — it is not a class-wide error but a "
            "single-name exclusion. A faithful patch that special-cased one "
            "coordinate name this way would preserve the coordinate set on almost "
            "every input and still drop that one name whenever it is present; the "
            "failing test's input carries a coordinate of exactly that name, so "
            "the coordinate list is not preserved and the patch does NOT resolve. "
            "It is the narrowest sub-domain break the spec must still catch."
        ),
        "rationale": (
            "Rejected by the BACKWARD direction at a single-name sub-domain: the "
            "clause is universally quantified over `name`, so it is violated by a "
            "rival that is wrong at one name only. Witness at "
            "reshapedDims=[\"time\"], priorCoordNames=[\"lat\", \"day\"] — the "
            "prior coordinate list carries TWO names and this rival retains "
            "\"lat\" while dropping only \"day\", so the refutation point exhibits "
            "the near-miss directly: the rival's output (["
            "\"lat\"]) differs from gold's by exactly the one excluded name rather "
            "than being empty. The refutation must be stated at THAT name: at "
            "\"lat\" this rival agrees with the frozen impl, which is precisely "
            "why a class-wide rival does not subsume it. (AUDIT: the original "
            "point was reshapedDims=[\"time\"], priorCoordNames=[\"day\"] — the "
            "BYTE-IDENTICAL point, and the identical recorded gold_signature, as "
            "case #1 `weak-common-names-only`. At that single-name point this "
            "rival returns [] exactly as #1's rival does, so the witness "
            "discriminated nothing #1 had not already discriminated and the "
            "'narrowest sub-domain' claim above was asserted but never "
            "demonstrated. Repaired to a two-name prior list, where the rival's "
            "output is a strict non-empty subset.)"
        ),
        # Holds of the rival ("day" ∉ result=["lat"]), fails on gold ("day" ∈
        # result). Measured: rival exit 0, gold exit 1 with a plain kernel
        # evaluation; and "lat" IS retained by the rival (exit 0 both sides),
        # which is what makes this a near-miss rather than a second #1.
        "witness": _wit_bwd('["time"]', '["lat", "day"]', "day"),
    },

    # --- UNIQUENESS #6: wrong POLARITY, refuted INSIDE the common names ----
    # Added by audit. Every other rival is refuted at a name that the frozen
    # impl's `common` filter does NOT contribute: four of the five are refuted at
    # a name outside `reshapedDims` entirely, and #3's overlap only makes `common`
    # non-empty — its refutation point ("x") is still not in it. So no case in the
    # battery refuted at a name the LEFT operand of the modeled identity
    # (W ∩ C) ∪ C = C actually produces. This rival keeps exactly the prior
    # coordinates that are NOT reshaped dimensions — the COMPLEMENT of the
    # intersection — so it can only be refuted at a name that is both a prior
    # coordinate and a reshaped dimension, i.e. one `common` does contribute.
    {
        "id": "weak-drop-reshaped-coords",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_RESULT,
                        "  let result := priorCoordNames.filter "
                        "(fun n => ! reshapedDims.contains n)\n"),
        "refinement": (
            "Inverts the polarity of the membership test: it retains a prior "
            "coordinate only when that name is NOT one of the reshaped "
            "dimensions. A faithful patch written this way keeps the "
            "non-dimensional coordinates the issue is about but now DROPS every "
            "coordinate that is itself a reshaped dimension — the opposite "
            "sub-domain from the reported bug, and still not a preserved "
            "coordinate set. The failing test asserts the coordinate list is "
            "preserved EXACTLY, and its input carries a coordinate that is also a "
            "reshaped dimension, so that name goes missing and the patch does NOT "
            "resolve."
        ),
        "rationale": (
            "Rejected by the BACKWARD direction at the sub-domain no other case "
            "reaches: a name that is BOTH a prior coordinate and a reshaped "
            "dimension. Witness at reshapedDims=[\"day\", \"x\"], "
            "priorCoordNames=[\"day\", \"lat\"] — the refutation is at \"day\", "
            "which the frozen impl's common-names filter itself produces (measured "
            "by evaluation: the filter returns [\"day\"] at this point), so this is "
            "the only case whose refutation point is a name the filter clause "
            "CONTRIBUTES rather than merely a point at which the filter happens to "
            "be non-empty. The rival still retains \"lat\", so it is a near-miss "
            "on the complementary sub-domain rather than a class-wide error."
        ),
        # Holds of the rival ("day" ∉ result=["lat"]), fails on gold ("day" ∈
        # result). Measured: rival exit 0, gold exit 1 with a plain kernel
        # evaluation naming the claim; the `.mp`-flipped forgery evaluates a
        # DIFFERENT proposition, so the gold exit code tracks the claim.
        "witness": _wit_bwd('["day", "x"]', '["day", "lat"]', "day"),
    },

    # --- ADMISSIBILITY (added by audit) -----------------------------------
    # The port recorded this lane as having "no counterpart" because the frozen
    # obligation is unconditional. That reason is the one the audit brief names as
    # NOT sufficient: on a total carrier the analogue of PRECOND-TOO-STRONG is the
    # obligation being UNSATISFIABLE at an F2P-shaped input, which is a real
    # failure mode even with no precondition hypothesis — the spec could be
    # contradictory at exactly the input the scenario exercises while remaining
    # provable nowhere, and a battery of rejects plus one reshaped positive would
    # not notice. This case discharges the obligation at that concrete input, BY
    # EVALUATION, as a `have`, before closing the frozen obligation verbatim.
    {
        "id": "admissibility-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_PROOF, _ADM_PROOF),
        "rationale": (
            "Non-vacuity at an F2P-shaped input. The proof first evaluates the "
            "frozen impl at reshapedDims=[\"time\"], priorCoordNames=[\"day\"] — a "
            "reshaped dimension together with a prior coordinate that is NOT "
            "itself a reshaped dimension, the shape of the reported scenario — "
            "obtaining `= [\"day\"]` by `decide`, then discharges "
            "`problem_spec_retainedCoordNames` AT that input from the evaluated "
            "value. Only after that does it close the frozen obligation with the "
            "byte-identical frozen script. So the obligation is shown SATISFIABLE "
            "at the concrete input the failing scenario uses, not merely provable "
            "as a universally quantified statement: if the spec's membership "
            "clause were unsatisfiable there — the total-carrier analogue of a "
            "precondition that excludes a legitimate input — the `have` would not "
            "discharge and the case would be rejected as PRECOND-TOO-STRONG. The "
            "two `have`s are `clear`ed before the frozen script runs, so they "
            "cannot contribute to it and the positive is not weakened by them."
        ),
    },
]


# ===========================================================================
# AXIOM_TESTS
# ===========================================================================
# Dropped: the axiom lane is G-AX's job and this bundle ships no consumed axiom.
# The modeled value is computed structurally (a filter followed by a union) over
# the two observable name collections; the proof reasons about no opaque callee.
AXIOM_TESTS = []
