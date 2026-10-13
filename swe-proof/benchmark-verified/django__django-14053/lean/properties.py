# properties.py — PBT falsification battery for django__django-14053 (lean).
#
# NOT a Lean module: a manifest the G-PBT runner parses. Each SPEC_TESTS entry
# is a FULL Solution.lean variant built by region-surgery over the frozen file.
# A verify/reject case edits ONLY the `impl` region and (for the reproven
# positives) the `proof` region, so `markers.same_spec(base, module)` holds by
# construction and the frozen obligation statement is preserved byte-for-byte.
# Any verify/reject outcome is therefore attributable to the postcondition, not
# to a tampered spec.
#
# Defended surface (see Solution.lean / mapping.md):
#   The single modeled obligation describes what one invocation hands to its
#   caller. Its load-bearing postcondition is an EXACT equality against a model
#   whose value is a PAIR, split at the one instant the caller can distinguish —
#   the moment the run's accumulated name mapping is committed to the shared
#   store:
#     `.1` the items handed over BEFORE the commit — every non-adjustable file
#          and every signalled error of the first pass, in first-pass order, then
#          the terminal item when the last further pass was still rewriting;
#     `.2` the items held back until after every pass has ended and the mapping
#          has been committed — each adjustable file EXACTLY ONCE, in order of
#          first appearance, carrying the stored name it ends with.
#   So the equality pins four separable things:
#     (i)   no file is handed over more than once (multiplicity),
#     (ii)  every collected file is handed over, none dropped (completeness),
#     (iii) each collected file carries its FINAL stored name (freshness),
#     (iv)  each item falls on the correct side of the commit (staging), and the
#           terminal item exists exactly when the run was still moving as the
#           allowance of passes ran out — no more often (its guard is the LAST
#           executed pass's flag, not "some pass rewrote") — and carries exactly
#           the fixed payload `allowanceItem`, whose reported name the caller
#           prints verbatim into its error stream.
#   The precondition admits every input with at least one further pass.
#
# The F2P only checks (a) no duplicate name in the reported stats and (b)
# membership of specific names; it does NOT check the reported ORDER. So a rival
# that merely permutes plain-vs-collected order WOULD resolve — we therefore do
# NOT submit an order-swap as a uniqueness break (its faithful patch resolves,
# making it a verify-does-not-resolve artifact, not a real defect). By the same
# standard the staging cases below are restricted to rivals that move an item
# whose position relative to the commit is OBSERVED: an error item or the
# terminal item, either of which makes the consumer abandon the report, so a
# consumer that sees it only after the commit observes a store the aborted run
# has already written. A rival that merely hands the collected files over
# EARLIER than the commit is not submitted, for the same reason as the
# order-swap: its faithful patch resolves.
# Every reject case below carries a refinement argument that its faithful real
# patch would NOT resolve the tests, plus a witness that has been SEEN to hold
# of the rival and fail on the frozen solution.
#
# One nagini case has no counterpart on this carrier and is omitted, not because
# it was hard but because the carrier makes it vacuous:
#   * FRAME-MUTATION (write a read-only input) — nagini fractional-permission
#     machinery. Lean is referentially transparent: inputs cannot be mutated,
#     so there is no permission to violate. VACUOUS here.
#
# ADMISSIBILITY is NOT vacuous here and is carried below in TWO regimes
# (`admiss-f2p-input`, `admiss-allowance-exhausted-input`). The obligation binds
# one antecedent (at least one further pass ran), so PRECOND-TOO-STRONG has two
# shapes: the antecedent excluding a realistic input, and the obligation being
# UNSATISFIABLE at exactly such an input. Each positive discharges the
# obligation at a concrete admissible input BY EVALUATION before closing the
# frozen obligation verbatim, so it tests both directly.

from pathlib import Path

INSTANCE = "django__django-14053"
FLOAT_ENCODING = None

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors that lie ENTIRELY inside the impl region (each unique in Solution.lean).
# ---------------------------------------------------------------------------

# The first-pass branch block: non-adjustable/error handed over now, adjustable
# set aside in the keyed collection.
_IMPL_FIRST = (
    "    if (! adjustable.contains r.name) || r.isError then\n"
    "      early := early ++ [r.toItem]\n"
    "    else\n"
    "      collected := upsertItem collected r.name r.toItem\n"
)

# The further-pass nested loop: this pass's rewriting flag replaces the previous
# one, and each record is folded into the keyed collection.
_IMPL_LATER = (
    "  for pass in laterPasses do\n"
    "    unsettled := pass.any (fun r => r.rewrote)\n"
    "    for r in pass do\n"
    "      collected := upsertItem collected r.name r.toItem\n"
)

# The terminal return: the pre-commit stream (plus the terminal item when the
# run was still moving) paired with the held-back collection.
_IMPL_EMIT = (
    "  return (early ++ (if unsettled then [allowanceItem] else []),"
    " collected.map (·.2))\n"
)

# The declaration of the keyed collection, so a rival that needs a third
# accumulator can introduce one without touching any other region.
_IMPL_DECL = "  let mut collected : List (String × OutItem) := []\n"

# The frozen proof's intro line (proof region, unique in the file), so the
# admissibility positives can prepend a ground `have` without touching the
# theorem STATEMENT or the spec view.
_P_INTRO = "  intro adjustable firstPass laterPasses _\n"

# The frozen further-pass lemma and the tactic line that applies it, so positive
# control A can restate the SAME lemma name for its reshaped loops.
_P_LATER_LEMMA = """theorem later_loops_eq_foldl (laterPasses : List (List PassRecord))
    (c : List (String × OutItem)) (b : Bool) :
    List.foldl
        (fun (st : MProd (List (String × OutItem)) Bool) (pass : List PassRecord) =>
          ⟨pass.foldl (fun d r => upsertItem d r.name r.toItem) st.fst,
            pass.any (fun r => r.rewrote)⟩)
        ⟨c, b⟩ laterPasses
      = ⟨(laterPasses.foldl laterStep (c, b)).1,
          (laterPasses.foldl laterStep (c, b)).2⟩ := by
  induction laterPasses generalizing c b with
  | nil => rfl
  | cons pass rest ih =>
    simp only [List.foldl_cons, laterStep]
    exact ih _ _
"""

_P_APPLY = "    first_loop_eq_foldl, later_loops_eq_foldl]\n  rfl\n"


# ===========================================================================
# 1. POSITIVE CONTROL A (soundness) — flatten the further-pass record stream
# ===========================================================================
# Structurally different but CORRECT, and deliberately the CORRECT sibling of
# the restructure that a wrong impl reaches for: the collection is folded over
# the flattened record stream in one loop, and the rewriting flag is read off the
# passes in a loop of its own. Semantically identical (folding `upsertItem` over
# `pass₀ ++ pass₁ ++ …` equals folding over each pass in turn, and the flag after
# the last pass is that pass's own either way) — crucially it keeps the STAGING:
# what it hands over before the commit and what it holds back are unchanged. So
# the obligation still closes; the reproof restates the further-pass lemma (same
# name) as the equality between the flat pair and the per-pass fold. Must verify;
# if a faithful correct reshape cannot verify this would be SPEC-TOO-STRONG, and
# it is the case that would catch a staging clause over-fitted to the frozen
# loop shape rather than stated over the commit.
_POS_FLATTEN = _swap(
    _BASE,
    _IMPL_LATER,
    "  for pass in laterPasses do\n"
    "    unsettled := pass.any (fun r => r.rewrote)\n"
    "  for r in laterPasses.flatten do\n"
    "    collected := upsertItem collected r.name r.toItem\n",
)
_POS_FLATTEN = _swap(
    _POS_FLATTEN,
    _P_LATER_LEMMA,
    """theorem later_loops_eq_foldl (laterPasses : List (List PassRecord))
    (c : List (String × OutItem)) (b : Bool) :
    (laterPasses.flatten.foldl (fun d r => upsertItem d r.name r.toItem) c,
        laterPasses.foldl (fun (_ : Bool) (pass : List PassRecord) =>
          pass.any (fun r => r.rewrote)) b)
      = laterPasses.foldl laterStep (c, b) := by
  induction laterPasses generalizing c b with
  | nil => rfl
  | cons pass rest ih =>
    simp only [List.foldl_cons, List.flatten_cons, List.foldl_append, laterStep]
    exact ih _ _
""",
)
_POS_FLATTEN = _swap(
    _POS_FLATTEN,
    _P_APPLY,
    "    first_loop_eq_foldl, ← later_loops_eq_foldl]\n  rfl\n",
)


# ===========================================================================
# 2. POSITIVE CONTROL B (soundness) — reorder the first-pass branches
# ===========================================================================
# The if/else of the first pass is reordered (the set-aside case tested first,
# handed-over case in the else). Semantically identical — each record lands in
# exactly one branch — so both components of the report are unchanged and the
# obligation still closes. The reproof mirrors the branch order in the first-loop
# lemma and splits both conditionals. Must verify; if not -> SPEC-TOO-STRONG.
_POS_REORDER = _swap(
    _BASE,
    _IMPL_FIRST,
    "    if !((! adjustable.contains r.name) || r.isError) then\n"
    "      collected := upsertItem collected r.name r.toItem\n"
    "    else\n"
    "      early := early ++ [r.toItem]\n",
)
_POS_REORDER = _swap(
    _POS_REORDER,
    "          if (!adjustable.contains r.name || r.isError) = true then\n"
    "            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)\n"
    "          else\n"
    "            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :\n"
    "        Id (MProd (List (String × OutItem)) (List OutItem)))\n"
    "      = ⟨(firstPass.foldl (firstStep adjustable) ([], [])).2,\n"
    "          (firstPass.foldl (firstStep adjustable) ([], [])).1⟩ := by\n"
    "  have key : ∀ (o : List OutItem) (d : List (String × OutItem)),\n"
    "      (forIn firstPass (⟨d, o⟩ : MProd (List (String × OutItem)) (List OutItem))\n"
    "        (fun r r_1 =>\n"
    "          if (!adjustable.contains r.name || r.isError) = true then\n"
    "            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)\n"
    "          else\n"
    "            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)) :\n",
    "          if (!(!adjustable.contains r.name || r.isError)) = true then\n"
    "            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)\n"
    "          else\n"
    "            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)) :\n"
    "        Id (MProd (List (String × OutItem)) (List OutItem)))\n"
    "      = ⟨(firstPass.foldl (firstStep adjustable) ([], [])).2,\n"
    "          (firstPass.foldl (firstStep adjustable) ([], [])).1⟩ := by\n"
    "  have key : ∀ (o : List OutItem) (d : List (String × OutItem)),\n"
    "      (forIn firstPass (⟨d, o⟩ : MProd (List (String × OutItem)) (List OutItem))\n"
    "        (fun r r_1 =>\n"
    "          if (!(!adjustable.contains r.name || r.isError)) = true then\n"
    "            pure (ForInStep.yield ⟨upsertItem r_1.fst r.name r.toItem, r_1.snd⟩)\n"
    "          else\n"
    "            pure (ForInStep.yield ⟨r_1.fst, r_1.snd ++ [r.toItem]⟩)) :\n",
)
_POS_REORDER = _swap(
    _POS_REORDER,
    "      simp only [List.forIn_cons, List.foldl_cons, firstStep]\n"
    "      split <;> simp_all",
    "      simp only [List.forIn_cons, List.foldl_cons, firstStep]\n"
    "      split <;> split <;> simp_all",
)


# ===========================================================================
# 2b. ADMISSIBILITY A — SATISFIABLE at an F2P-shaped input (run settles)
# ===========================================================================
# Discharges `problem_spec_postProcess` BY EVALUATION at a concrete admissible
# input carrying every feature the modeled behavior has to accommodate at once —
# two files needing adjustment (one of them revisited in TWO further passes, so
# the final stored value must win over two earlier ones), one file needing none,
# one signalled error, and a last further pass that rewrote nothing (the run
# settled, so NO terminal item) — as a ground `have` prepended to the frozen
# tactic body, which then closes verbatim. Nothing is assumed: no new top-level
# declaration, the theorem statement stays byte-identical, and the `have` is
# discharged by `rfl` (evaluation), not by citing the obligation. Confirmed to be
# real work rather than a vacuous `rfl`: the same `have` with the result replaced
# by `(([], []) : OutReport)` FAILS to elaborate.
_ADMISS = _swap(
    _BASE,
    _P_INTRO,
    "  have _f2p : problem_spec_postProcess [\"r1\", \"r2\"]\n"
    "      [{ name := \"r1\", storedName := some \"r1.aaaa\", outcome := Except.ok true, rewrote := true },\n"
    "       { name := \"r2\", storedName := some \"r2.bbbb\", outcome := Except.ok true, rewrote := true },\n"
    "       { name := \"p1\", storedName := some \"p1\", outcome := Except.ok false, rewrote := false },\n"
    "       { name := \"r3\", storedName := none, outcome := Except.error \"signalled\", rewrote := false }]\n"
    "      [[{ name := \"r1\", storedName := some \"r1.cccc\", outcome := Except.ok true, rewrote := true }],\n"
    "       [{ name := \"r1\", storedName := some \"r1.dddd\", outcome := Except.ok true, rewrote := false },\n"
    "        { name := \"r2\", storedName := some \"r2.eeee\", outcome := Except.ok true, rewrote := false }]]\n"
    "      (implementation_postProcess [\"r1\", \"r2\"]\n"
    "        [{ name := \"r1\", storedName := some \"r1.aaaa\", outcome := Except.ok true, rewrote := true },\n"
    "         { name := \"r2\", storedName := some \"r2.bbbb\", outcome := Except.ok true, rewrote := true },\n"
    "         { name := \"p1\", storedName := some \"p1\", outcome := Except.ok false, rewrote := false },\n"
    "         { name := \"r3\", storedName := none, outcome := Except.error \"signalled\", rewrote := false }]\n"
    "        [[{ name := \"r1\", storedName := some \"r1.cccc\", outcome := Except.ok true, rewrote := true }],\n"
    "         [{ name := \"r1\", storedName := some \"r1.dddd\", outcome := Except.ok true, rewrote := false },\n"
    "          { name := \"r2\", storedName := some \"r2.eeee\", outcome := Except.ok true, rewrote := false }]]) := by\n"
    "    simp only [problem_spec_postProcess]\n"
    "    rfl\n"
    + _P_INTRO,
)


# ===========================================================================
# 2c. ADMISSIBILITY B — SATISFIABLE when the allowance runs out mid-flight
# ===========================================================================
# The second regime, and the one the modeled terminal item exists for: the last
# further pass STILL rewrote a reference, so the run had not settled when the
# allowance of passes was used up. The obligation must be satisfiable there too —
# with the terminal item handed over BEFORE the commit, ahead of the held-back
# collection. Same construction as A (ground `have`, discharged by evaluation,
# frozen body unchanged). If this fails, the terminal-item leg of the model has
# no solution and the three staging cases below are reasoning over an empty
# domain.
_ADMISS_ALLOWANCE = _swap(
    _BASE,
    _P_INTRO,
    "  have _exhausted : problem_spec_postProcess [\"r1\"]\n"
    "      [{ name := \"r1\", storedName := some \"r1.aaaa\", outcome := Except.ok true, rewrote := true },\n"
    "       { name := \"p1\", storedName := some \"p1\", outcome := Except.ok false, rewrote := false }]\n"
    "      [[{ name := \"r1\", storedName := some \"r1.bbbb\", outcome := Except.ok true, rewrote := true }],\n"
    "       [{ name := \"r1\", storedName := some \"r1.cccc\", outcome := Except.ok true, rewrote := true }]]\n"
    "      (implementation_postProcess [\"r1\"]\n"
    "        [{ name := \"r1\", storedName := some \"r1.aaaa\", outcome := Except.ok true, rewrote := true },\n"
    "         { name := \"p1\", storedName := some \"p1\", outcome := Except.ok false, rewrote := false }]\n"
    "        [[{ name := \"r1\", storedName := some \"r1.bbbb\", outcome := Except.ok true, rewrote := true }],\n"
    "         [{ name := \"r1\", storedName := some \"r1.cccc\", outcome := Except.ok true, rewrote := true }]]) := by\n"
    "    simp only [problem_spec_postProcess]\n"
    "    rfl\n"
    + _P_INTRO,
)


# ===========================================================================
# 3. UNIQUENESS — collected file handed over TWICE (first pass)
# ===========================================================================
# The pre-fix multiplicity defect: a set-aside file is BOTH handed over during
# the first pass AND kept in the collection for after the commit, so it appears
# twice in the report. Violates (i) multiplicity. Must REJECT.
_DUP_FIRST = _swap(
    _BASE,
    _IMPL_FIRST,
    "    if (! adjustable.contains r.name) || r.isError then\n"
    "      early := early ++ [r.toItem]\n"
    "    else\n"
    "      -- WRONG: hand the set-aside file over now AND keep it for the end.\n"
    "      early := early ++ [r.toItem]\n"
    "      collected := upsertItem collected r.name r.toItem\n",
)

# ===========================================================================
# 4. UNIQUENESS — collected file also handed over during a further pass
# ===========================================================================
# A second, distinct locus of the same multiplicity defect: each record seen in a
# FURTHER pass is handed over immediately AND kept in the collection, so any file
# revisited across passes is reported once per revisit plus once at the end.
# Attacks the same clause (i) but through the further-pass loop rather than the
# first pass, and its witness moves the `laterPasses` binder off the
# nothing-observed case. Must REJECT.
_DUP_LATER = _swap(
    _BASE,
    _IMPL_LATER,
    "  for pass in laterPasses do\n"
    "    unsettled := pass.any (fun r => r.rewrote)\n"
    "    for r in pass do\n"
    "      -- WRONG: hand each revisited file over now AND keep it for the end.\n"
    "      early := early ++ [r.toItem]\n"
    "      collected := upsertItem collected r.name r.toItem\n",
)

# ===========================================================================
# 5. PARTIAL-DOMAIN — drops ALL collected files
# ===========================================================================
# Correct on the sub-domain with no set-aside file (the collection stays empty),
# but on any input containing one it never hands the collection over, dropping
# every collected file. Violates (ii) completeness whenever a file is set aside.
# Must REJECT.
_DROP_ALL = _swap(
    _BASE,
    _IMPL_EMIT,
    "  -- WRONG (partial-domain): the set-aside files are collected but never\n"
    "  -- handed over. Correct only when nothing is set aside.\n"
    "  return (early ++ (if unsettled then [allowanceItem] else []), [])\n",
)

# ===========================================================================
# 6. PARTIAL-DOMAIN (boundary) — drops exactly the FIRST collected file
# ===========================================================================
# A subtler near-miss than case 5: hand over the collection EXCEPT its first
# entry. Correct whenever 0 or 1 file is set aside, but on any input with >=2
# distinct set-aside files it omits the first — diverging from completeness only
# on that sub-domain. Its witness therefore probes a two-set-aside input, a
# strictly more discriminating point than case 5's single-file input. Must
# REJECT.
_DROP_FIRST = _swap(
    _BASE,
    _IMPL_EMIT,
    "  -- WRONG (partial-domain, boundary): drop the first collected file.\n"
    "  -- Equals the correct report only when fewer than two files are set aside.\n"
    "  return (early ++ (if unsettled then [allowanceItem] else []),\n"
    "    (collected.map (·.2)).tail)\n",
)


# ===========================================================================
# 7. STALE VALUE — a revisited file keeps its FIRST stored name, not its final one
# ===========================================================================
# The one clause the length-based cases above CANNOT see. A further pass refuses
# to overwrite a value already held, so the file is still handed over EXACTLY
# ONCE, on the right side of the commit, in the right position, and nothing is
# dropped — (i), (ii) and (iv) all hold, and EVERY length projection agrees with
# the frozen result. Only the reported stored name differs: the file carries the
# value from its first appearance instead of its most recent. Measured: a
# length-projection witness at this input FAILS against this rival as well as
# against gold (exit 1 both sides — it is not a discriminator here), while the
# storedName projection separates them (rival exit 0, gold exit 1). That is why
# this case's witness projects `(·.2.1)` of the held-back component rather than a
# length. Must REJECT.
_STALE_VALUE = _swap(
    _BASE,
    _IMPL_LATER,
    "  for pass in laterPasses do\n"
    "    unsettled := pass.any (fun r => r.rewrote)\n"
    "    for r in pass do\n"
    "      -- WRONG: keep the value already held; never replace it with the\n"
    "      -- later one, so a revisited file reports a superseded stored name.\n"
    "      if !(collected.any (fun p => p.1 == r.name)) then\n"
    "        collected := upsertItem collected r.name r.toItem\n",
)


# ===========================================================================
# 8. STAGING — nothing is handed over until after the commit
# ===========================================================================
# The whole report is buffered and handed over as one block AFTER the run's
# mapping has been committed: the item VALUES and their order are exactly the
# frozen ones — (i), (ii) and (iii) all hold and every projection of the
# concatenation agrees — but the signalled errors of the first pass, which a
# consumer abandons the report on, now arrive too late. Violates (iv) staging.
# This is the shape a wrong impl reaches for on this obligation (buffer
# everything, emit once), and the reason the model's value is a pair. Must
# REJECT.
_STAGE_ALL_DEFERRED = _swap(
    _BASE,
    _IMPL_EMIT,
    "  -- WRONG (staging): hold EVERYTHING back and hand it over as one block\n"
    "  -- after the mapping has been committed. Same items, same order, but a\n"
    "  -- consumer that stops at the first signalled error sees it only once the\n"
    "  -- run's results are already committed.\n"
    "  return ([], early ++ (if unsettled then [allowanceItem] else [])\n"
    "    ++ collected.map (·.2))\n",
)

# ===========================================================================
# 9. TERMINAL ITEM — never reported at all
# ===========================================================================
# The run's last further pass was still rewriting references, so the allowance
# ran out before it settled; this rival hands over no terminal item, so the
# caller is never told and treats an unsettled run as a completed one. Correct on
# every input whose last further pass rewrote nothing, wrong on every input where
# it did — a partial-domain break of the terminal-item leg of (iv). Must REJECT.
_NO_ALLOWANCE = _swap(
    _BASE,
    _IMPL_EMIT,
    "  -- WRONG (partial-domain): never report that the allowance of further\n"
    "  -- passes ran out with the run still moving.\n"
    "  return (early, collected.map (·.2))\n",
)

# ===========================================================================
# 10. TERMINAL ITEM — reported, but only after the commit
# ===========================================================================
# The sharpest staging case: the terminal item IS reported, with the right value,
# and the concatenation of the two components is exactly the frozen report — only
# its side of the commit is different. A consumer abandons the report on it, so
# reporting it after the commit means an unsettled run has already written its
# results to the store. Everything else — multiplicity, completeness, freshness,
# and the staging of the first pass's own items — is untouched, so this case is
# what separates "the terminal item exists" from "the terminal item is handed
# over in time". Must REJECT.
_ALLOWANCE_DEFERRED = _swap(
    _BASE,
    _IMPL_EMIT,
    "  -- WRONG (staging): hold the terminal item back until after the mapping\n"
    "  -- has been committed, ahead of the collection.\n"
    "  return (early, (if unsettled then [allowanceItem] else [])\n"
    "    ++ collected.map (·.2))\n",
)


# ===========================================================================
# 11. STAGING (partial-domain) — only the ERROR items are held back
# ===========================================================================
# A strictly sharper variant of case 8, and a partial-domain break: the
# non-adjustable files are still handed over as the first pass encounters them,
# and the collection is still held back, so on every input with no signalled
# error this rival is EXACTLY the frozen behavior. It diverges only on inputs
# where a file fails — precisely the inputs where the staging is observable,
# because the error is the item the consumer abandons the report on. The terminal
# item is left exactly where the frozen model puts it, so nothing the two
# terminal-item cases rely on refutes this one. Must REJECT.
_STAGE_ERRORS_WITHHELD = _swap(
    _BASE,
    _IMPL_DECL,
    _IMPL_DECL + "  let mut late : List OutItem := []\n",
)
_STAGE_ERRORS_WITHHELD = _swap(
    _STAGE_ERRORS_WITHHELD,
    _IMPL_FIRST,
    "    if (! adjustable.contains r.name) || r.isError then\n"
    "      -- WRONG (staging, partial-domain): a signalled error is held back\n"
    "      -- until after the mapping has been committed; all else unchanged.\n"
    "      if r.isError then\n"
    "        late := late ++ [r.toItem]\n"
    "      else\n"
    "        early := early ++ [r.toItem]\n"
    "    else\n"
    "      collected := upsertItem collected r.name r.toItem\n",
)
_STAGE_ERRORS_WITHHELD = _swap(
    _STAGE_ERRORS_WITHHELD,
    _IMPL_EMIT,
    "  return (early ++ (if unsettled then [allowanceItem] else []),\n"
    "    late ++ collected.map (·.2))\n",
)

# ===========================================================================
# 12. STAGING — the two sides of the commit are exchanged
# ===========================================================================
# Both components are non-empty and carry the frozen items, but each is on the
# wrong side: the adjustable files are handed over before the mapping is
# committed and the non-adjustable files and errors after it. Probes clause (iv)
# from the opposite direction to cases 8 and 11 — nothing is emptied, dropped,
# duplicated or staled, so both components keep their frozen LENGTHS and only
# which items sit on which side differs. Must REJECT.
_STAGE_SWAPPED = _swap(
    _BASE,
    _IMPL_EMIT,
    "  -- WRONG (staging): exchange the two sides of the commit — the collected\n"
    "  -- files go out before the mapping is committed and the immediate items\n"
    "  -- after it.\n"
    "  return (collected.map (·.2),\n"
    "    early ++ (if unsettled then [allowanceItem] else []))\n",
)

# ===========================================================================
# 13. TERMINAL ITEM — OVER-reported: the rewriting flag is never reset
# ===========================================================================
# The mirror image of case 9, and the case a spec that only forbade DROPPING the
# terminal item would accept. The flag is accumulated across the further passes
# instead of being replaced by each pass's own, so the item is reported whenever
# ANY pass rewrote a reference rather than only when the LAST executed one did —
# i.e. it is reported for runs that DID settle. `substitutions = False` sits at
# the top of the pass loop body (storage.py:244 post-patch), inside it, which is
# exactly what makes the frozen `unsettled := pass.any …` a replacement and not
# an accumulation. Must REJECT.
_ALLOWANCE_ACCUMULATED = _swap(
    _BASE,
    "    unsettled := pass.any (fun r => r.rewrote)\n",
    "    -- WRONG (over-approximation): accumulate the rewriting flag across the\n"
    "    -- passes instead of replacing it with this pass's own, so a run that\n"
    "    -- settled is still reported as having run out of passes.\n"
    "    unsettled := unsettled || pass.any (fun r => r.rewrote)\n",
)

# ===========================================================================
# 14. TERMINAL ITEM — right place, right time, wrong reported name
# ===========================================================================
# The terminal item is present exactly when the frozen model reports it and on
# the correct side of the commit; only the name it is reported under differs
# ("all" for "All"). That name is not decoration: the caller writes it verbatim
# into its error stream ("Post-processing '%s' failed!" % original_path,
# collectstatic.py:130) and a P2P test compares that stream literally. A boundary
# token swap of exactly the kind an equality against `allowanceItem` is there to
# catch, and one no length projection can see. Must REJECT.
_ALLOWANCE_MISNAMED = _swap(
    _BASE,
    _IMPL_EMIT,
    "  -- WRONG (payload): the terminal item is reported at the right time and on\n"
    "  -- the right side of the commit, under a different reported name.\n"
    "  return (early ++ (if unsettled then\n"
    "      [((\"all\", none, Except.error \"Max post-process passes exceeded.\")\n"
    "        : OutItem)] else []),\n"
    "    collected.map (·.2))\n",
)


# ---------------------------------------------------------------------------
# Witnesses. Each states ¬ (spec … (impl …)) at a CONCRETE admissible input (at
# least one further pass, as the antecedent requires) and refutes it over a
# DECIDABLE PROJECTION of the reported pair (the item type carries an `Except`
# with no DecidableEq, so a direct value `decide` is impossible). The
# multiplicity/completeness/staging cases project the LENGTH of the component
# they move an item out of or into; the stale-value case projects the stored-name
# component of the held-back list, because at its input every length agrees with
# the frozen result and only the reported value differs. Each has been built
# against the rival (elaborates, exit 0) and against the frozen solution (fails,
# exit 1), and the frozen-side failure is in every case a `decide` refutation of
# the concrete claim: flipping the claim (asserting the spec HOLDS there)
# elaborates against the frozen solution at exit 0 and fails against the rival,
# so the frozen-side exit code tracks what is claimed.
# ---------------------------------------------------------------------------

_W_DUP_FIRST = (
    'example : ¬ problem_spec_postProcess ["a"]\n'
    '    [{ name := "a", storedName := some "x", outcome := Except.ok true,\n'
    '       rewrote := false }] [[]]\n'
    '    (implementation_postProcess ["a"]\n'
    '      [{ name := "a", storedName := some "x", outcome := Except.ok true,\n'
    '         rewrote := false }] [[]]) := by\n'
    "  simp only [problem_spec_postProcess]\n"
    "  intro h\n"
    "  have hl := congrArg (fun r => (Prod.fst r).length) h\n"
    "  revert hl\n"
    "  decide"
)

_W_DUP_LATER = (
    'example : ¬ problem_spec_postProcess ["b"]\n'
    '    [{ name := "b", storedName := some "y", outcome := Except.ok true,\n'
    '       rewrote := true }]\n'
    '    [[{ name := "b", storedName := some "z", outcome := Except.ok false,\n'
    '        rewrote := false }]]\n'
    '    (implementation_postProcess ["b"]\n'
    '      [{ name := "b", storedName := some "y", outcome := Except.ok true,\n'
    '         rewrote := true }]\n'
    '      [[{ name := "b", storedName := some "z", outcome := Except.ok false,\n'
    '          rewrote := false }]]) := by\n'
    "  simp only [problem_spec_postProcess]\n"
    "  intro h\n"
    "  have hl := congrArg (fun r => (Prod.fst r).length) h\n"
    "  revert hl\n"
    "  decide"
)

_W_DROP_ALL = (
    'example : ¬ problem_spec_postProcess ["c"]\n'
    '    [{ name := "c", storedName := some "p", outcome := Except.ok true,\n'
    '       rewrote := false }] [[]]\n'
    '    (implementation_postProcess ["c"]\n'
    '      [{ name := "c", storedName := some "p", outcome := Except.ok true,\n'
    '         rewrote := false }] [[]]) := by\n'
    "  simp only [problem_spec_postProcess]\n"
    "  intro h\n"
    "  have hl := congrArg (fun r => (Prod.snd r).length) h\n"
    "  revert hl\n"
    "  decide"
)

_W_DROP_FIRST = (
    'example : ¬ problem_spec_postProcess ["d", "e"]\n'
    '    [{ name := "d", storedName := some "p", outcome := Except.ok true,\n'
    '       rewrote := false },\n'
    '     { name := "e", storedName := some "q", outcome := Except.ok true,\n'
    '       rewrote := false }] [[]]\n'
    '    (implementation_postProcess ["d", "e"]\n'
    '      [{ name := "d", storedName := some "p", outcome := Except.ok true,\n'
    '         rewrote := false },\n'
    '       { name := "e", storedName := some "q", outcome := Except.ok true,\n'
    '         rewrote := false }] [[]]) := by\n'
    "  simp only [problem_spec_postProcess]\n"
    "  intro h\n"
    "  have hl := congrArg (fun r => (Prod.snd r).length) h\n"
    "  revert hl\n"
    "  decide"
)


_W_STALE_VALUE = (
    'example : ¬ problem_spec_postProcess ["a"]\n'
    '    [{ name := "a", storedName := some "v1", outcome := Except.ok true,\n'
    '       rewrote := true }]\n'
    '    [[{ name := "a", storedName := some "v2", outcome := Except.ok true,\n'
    '        rewrote := false }]]\n'
    '    (implementation_postProcess ["a"]\n'
    '      [{ name := "a", storedName := some "v1", outcome := Except.ok true,\n'
    '         rewrote := true }]\n'
    '      [[{ name := "a", storedName := some "v2", outcome := Except.ok true,\n'
    '          rewrote := false }]]) := by\n'
    "  simp only [problem_spec_postProcess]\n"
    "  intro h\n"
    "  have hl := congrArg (fun r => (Prod.snd r).map (·.2.1)) h\n"
    "  revert hl\n"
    "  decide"
)

# One non-adjustable file (handed over before the commit) plus one adjustable
# file (held back). The frozen report is ([non-adjustable], [adjustable]); the
# all-deferred rival's first component is empty.
_W_STAGE_ALL_DEFERRED = (
    'example : ¬ problem_spec_postProcess ["a"]\n'
    '    [{ name := "a", storedName := some "a.hh", outcome := Except.ok true,\n'
    '       rewrote := false },\n'
    '     { name := "e", storedName := none, outcome := Except.error "signalled",\n'
    '       rewrote := false }] [[]]\n'
    '    (implementation_postProcess ["a"]\n'
    '      [{ name := "a", storedName := some "a.hh", outcome := Except.ok true,\n'
    '         rewrote := false },\n'
    '       { name := "e", storedName := none, outcome := Except.error "signalled",\n'
    '         rewrote := false }] [[]]) := by\n'
    "  simp only [problem_spec_postProcess]\n"
    "  intro h\n"
    "  have hl := congrArg (fun r => (Prod.fst r).length) h\n"
    "  revert hl\n"
    "  decide"
)

# A single further pass that STILL rewrote a reference: the allowance ran out
# with the run moving, so the frozen report's first component is exactly the
# terminal item. Both terminal-item rivals leave it empty (one drops the item,
# the other moves it past the commit), so the same projection refutes both.
# Two files, neither adjustable: one processed normally, one signalled error.
# Both belong to the pre-commit component, so the frozen report is
# ([plain, error], []) — the errors-held-back rival moves only the error, leaving
# a pre-commit component of length 1. A witness with the error alone would not
# separate this rival from case 8's, which is why this one keeps a plain item.
# The single further pass rewrote nothing, so no terminal item is involved and
# the projection isolates the staging of the error alone.
_W_STAGE_ERRORS_WITHHELD = (
    'example : \u00ac problem_spec_postProcess []\n'
    '    [{ name := "p", storedName := some "p.hh", outcome := Except.ok false,\n'
    '       rewrote := false },\n'
    '     { name := "e", storedName := none, outcome := Except.error "signalled",\n'
    '       rewrote := false }] [[]]\n'
    '    (implementation_postProcess []\n'
    '      [{ name := "p", storedName := some "p.hh", outcome := Except.ok false,\n'
    '         rewrote := false },\n'
    '       { name := "e", storedName := none, outcome := Except.error "signalled",\n'
    '         rewrote := false }] [[]]) := by\n'
    "  simp only [problem_spec_postProcess]\n"
    "  intro h\n"
    "  have hl := congrArg (fun r => (Prod.fst r).length) h\n"
    "  revert hl\n"
    "  decide"
)

# One adjustable file and one signalled error, so BOTH components of the frozen
# report have length 1 and no length projection can see the exchange. The names
# of the pre-commit component do: frozen ["e"], rival ["a"].
_W_STAGE_SWAPPED = (
    'example : \u00ac problem_spec_postProcess ["a"]\n'
    '    [{ name := "a", storedName := some "a.hh", outcome := Except.ok true,\n'
    '       rewrote := false },\n'
    '     { name := "e", storedName := none, outcome := Except.error "signalled",\n'
    '       rewrote := false }] [[]]\n'
    '    (implementation_postProcess ["a"]\n'
    '      [{ name := "a", storedName := some "a.hh", outcome := Except.ok true,\n'
    '         rewrote := false },\n'
    '       { name := "e", storedName := none, outcome := Except.error "signalled",\n'
    '         rewrote := false }] [[]]) := by\n'
    "  simp only [problem_spec_postProcess]\n"
    "  intro h\n"
    "  have hl := congrArg (fun r => (Prod.fst r).map (\u00b7.1)) h\n"
    "  revert hl\n"
    "  decide"
)

_W_TERMINAL = (
    'example : ¬ problem_spec_postProcess ["a"] []\n'
    '    [[{ name := "a", storedName := some "a.hh", outcome := Except.ok true,\n'
    '        rewrote := true }]]\n'
    '    (implementation_postProcess ["a"] []\n'
    '      [[{ name := "a", storedName := some "a.hh", outcome := Except.ok true,\n'
    '          rewrote := true }]]) := by\n'
    "  simp only [problem_spec_postProcess]\n"
    "  intro h\n"
    "  have hl := congrArg (fun r => (Prod.fst r).length) h\n"
    "  revert hl\n"
    "  decide"
)

# TWO further passes: the first still rewrote a reference, the second (the last
# executed one) rewrote nothing — so the run SETTLED and the frozen report's
# pre-commit component is empty. The over-reporting rival puts the terminal item
# there, length 1 vs 0. This input is the one case 9's witness cannot use: there
# the last pass is the rewriting one, and both rivals agree with the model on it.
_W_TERMINAL_OVER = (
    'example : ¬ problem_spec_postProcess ["a"] []\n'
    '    [[{ name := "a", storedName := some "a.h1", outcome := Except.ok true,\n'
    '        rewrote := true }],\n'
    '     [{ name := "a", storedName := some "a.h2", outcome := Except.ok true,\n'
    '        rewrote := false }]]\n'
    '    (implementation_postProcess ["a"] []\n'
    '      [[{ name := "a", storedName := some "a.h1", outcome := Except.ok true,\n'
    '          rewrote := true }],\n'
    '       [{ name := "a", storedName := some "a.h2", outcome := Except.ok true,\n'
    '          rewrote := false }]]) := by\n'
    "  simp only [problem_spec_postProcess]\n"
    "  intro h\n"
    "  have hl := congrArg (fun r => (Prod.fst r).length) h\n"
    "  revert hl\n"
    "  decide"
)

# Case 9's input (a single further pass that still rewrote), where both the frozen
# model and the misnaming rival report exactly one pre-commit item, so only the
# reported NAME separates them: frozen ["All"], rival ["all"].
_W_TERMINAL_NAME = (
    'example : ¬ problem_spec_postProcess ["a"] []\n'
    '    [[{ name := "a", storedName := some "a.hh", outcome := Except.ok true,\n'
    '        rewrote := true }]]\n'
    '    (implementation_postProcess ["a"] []\n'
    '      [[{ name := "a", storedName := some "a.hh", outcome := Except.ok true,\n'
    '          rewrote := true }]]) := by\n'
    "  simp only [problem_spec_postProcess]\n"
    "  intro h\n"
    "  have hl := congrArg (fun r => (Prod.fst r).map (·.1)) h\n"
    "  revert hl\n"
    "  decide"
)


SPEC_TESTS = [
    {
        "id": "pos-control-flatten-later-passes",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FLATTEN,
        "rationale": (
            "structurally-different but CORRECT impl, and the correct sibling of "
            "the buffering restructure a wrong impl reaches for: the further-pass "
            "collection is folded over the FLATTENED record stream in one loop "
            "and the rewriting flag is read off the passes in a loop of its own. "
            "Folding the keyed insert over the concatenation equals folding over "
            "each pass in turn, and the flag after the last pass is that pass's "
            "own either way; the STAGING is untouched. So the exact report "
            "equality still holds and the obligation closes (the further-pass "
            "lemma is restated as the flat-pair equality). Must verify; if not -> "
            "SPEC-TOO-STRONG. This is the case that would catch a staging clause "
            "over-fitted to the frozen loop shape instead of stated over the "
            "commit."
        ),
    },
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": (
            "structurally-different but CORRECT impl: the first-pass if/else is "
            "reordered (set-aside case tested first). Each record still lands in "
            "exactly one branch, so both components of the report are unchanged "
            "and the obligation closes (the first-loop lemma mirrors the branch "
            "order). Must verify; if not -> SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-f2p-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "the obligation is SATISFIABLE at a realistic F2P-shaped input, "
            "discharged by EVALUATION as a ground `have` before the frozen "
            "obligation is closed verbatim. The antecedent (at least one further "
            "pass ran) holds at this input, so the case tests both halves of "
            "PRECOND-TOO-STRONG: that the antecedent admits a realistic input, "
            "and that the exact-report equality has a solution there. The input "
            "carries every feature the modeled behavior must accommodate at once: "
            "two files needing adjustment (one revisited in TWO further passes, "
            "so the final stored value must win over two superseded ones), one "
            "file needing none, one signalled error, and a last pass that rewrote "
            "nothing — the run settled, so no terminal item. It evaluates to a "
            "pair: the non-adjustable file and the error handed over before the "
            "commit, the two adjusted files held back for after it, each exactly "
            "once and carrying its most recent stored name. Nothing is assumed: "
            "no new declaration, statement byte-identical. Must verify; if not, "
            "the modeled behavior is unsatisfiable at a normal input and every "
            "other case is reasoning over an empty domain. Not a vacuous `rfl`: "
            "the same `have` with the result replaced by `(([], []) : OutReport)` "
            "fails."
        ),
    },
    {
        "id": "admiss-allowance-exhausted-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS_ALLOWANCE,
        "rationale": (
            "the second admissible regime, and the one the terminal item exists "
            "for: the last further pass STILL rewrote a reference, so the "
            "allowance of passes ran out with the run unsettled. Discharged by "
            "EVALUATION at a concrete input of that shape — the terminal item "
            "handed over before the commit, after the first pass's "
            "non-adjustable file, with the revisited adjustable file held back "
            "carrying its final stored name. If this fails, the terminal-item leg "
            "of the model has no solution at any input that reaches it and the "
            "three staging/terminal cases below are reasoning over an empty "
            "domain. Must verify; if not -> PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "uniqueness-first-pass-reported-twice",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _DUP_FIRST,
        "witness": _W_DUP_FIRST,
        "refinement": (
            "this is the pre-fix multiplicity defect: a set-aside file is "
            "yielded in the first pass AND yielded again at the end, so its name "
            "appears twice in the reported stats. The F2P's no-duplicate check "
            "fails on exactly this. It would NOT resolve."
        ),
        "rationale": (
            "a set-aside file is pushed to BOTH the pre-commit stream and the "
            "collection, so it appears twice in the report — the first component "
            "is one longer than the spec's. Rejection source: (i) multiplicity. "
            "Witness discriminates at a single set-aside file with one further "
            "pass (first component length 1 vs required 0)."
        ),
    },
    {
        "id": "uniqueness-subsequent-pass-reported-twice",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _DUP_LATER,
        "witness": _W_DUP_LATER,
        "refinement": (
            "the same multiplicity defect at a different locus: each record seen "
            "in a further pass is yielded immediately AND kept for the end, so a "
            "file revisited across passes appears once per revisit plus once at "
            "the end. The F2P's no-duplicate check fails. It would NOT resolve."
        ),
        "rationale": (
            "attacks (i) multiplicity through the further-pass loop rather than "
            "the first pass. Its witness puts a record in the further pass (a "
            "file revisited after the first pass), so the battery exercises that "
            "input; first component length 1 vs required 0."
        ),
    },
    {
        "id": "partial-domain-drop-all-collected",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _DROP_ALL,
        "witness": _W_DROP_ALL,
        "refinement": (
            "the faithful real patch omits the terminal `yield from` of the "
            "collected files entirely: they are set aside but never yielded, so "
            "their names never reach the stats. The F2P membership assertions "
            "for the post-processed files fail. It would NOT resolve."
        ),
        "rationale": (
            "report omits the whole held-back collection: correct on the "
            "no-set-aside sub-domain but drops every set-aside file otherwise. "
            "Rejection source: (ii) completeness (second component length 0 vs "
            "required 1 at a single set-aside file)."
        ),
    },
    {
        "id": "partial-domain-drop-first-collected",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _DROP_FIRST,
        "witness": _W_DROP_FIRST,
        "refinement": (
            "the faithful real patch yields all-but-one of the collected files "
            "(e.g. dropping the first). The dropped name never reaches the "
            "stats, so the F2P membership assertions fail on any fixture with "
            "two or more set-aside files. It would NOT resolve."
        ),
        "rationale": (
            "boundary near-miss of the completeness clause: hand over the "
            "collection except its first entry. Correct with <2 set-aside files, "
            "wrong with >=2, so its witness probes a strictly more discriminating "
            "TWO-set-aside input (second component length 1 vs required 2) than "
            "the drop-all case. Rejection source: (ii) completeness."
        ),
    },
    {
        "id": "stale-value-first-not-final-stored-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _STALE_VALUE,
        "witness": _W_STALE_VALUE,
        "refinement": (
            "the faithful real patch keys the collection correctly (so each file "
            "is still yielded exactly once) but never replaces the value already "
            "held, so a file revisited on a further pass is reported with a "
            "superseded stored name instead of the one it ended up under. The F2P "
            "asserts membership of the FINAL stored name; the superseded one it "
            "reports instead is not that value, so the membership assertion fails. "
            "It would NOT resolve."
        ),
        "rationale": (
            "the clause the length-based cases above cannot see. This rival "
            "satisfies (i) multiplicity, (ii) completeness AND (iv) staging — the "
            "file is handed over exactly once, after the commit, in the right "
            "position, nothing dropped — and every length projection of its "
            "report agrees with the frozen one. It differs ONLY in the reported "
            "stored name: the value from the file's first appearance rather than "
            "its most recent. Measured: a length-projection witness at this input "
            "fails against this rival AND against the frozen solution (exit 1 "
            "both sides — no discrimination), so this case's witness projects the "
            "stored-name component instead, which separates them (rival exit 0, "
            "frozen exit 1). Rejection source: (iii) freshness, which no other "
            "case in this battery demonstrates."
        ),
    },
    {
        "id": "staging-everything-deferred-past-the-commit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _STAGE_ALL_DEFERRED,
        "witness": _W_STAGE_ALL_DEFERRED,
        "refinement": (
            "the faithful real patch buffers every item — including the first "
            "pass's signalled errors — and yields them all after "
            "`self.hashed_files.update(hashed_files)`. The item sequence is "
            "IDENTICAL to gold's, so the F2P (no duplicates, membership) still "
            "passes; but collectstatic raises on the first Exception item, so with "
            "the errors yielded late the run has already written its accumulated "
            "mapping to the shared store before the caller ever sees the error. "
            "The P2P test that asserts what the store holds after a failed run "
            "fails. It would NOT resolve — measured on this instance: this is the "
            "construction that broke it (PASS_TO_PASS 30/31, F2P 1/1), and the "
            "isolation control differing ONLY in where the mapping is committed "
            "resolves 31/31."
        ),
        "rationale": (
            "the staging break, and the reason the model's value is a pair rather "
            "than one list: same items, same order, same values — (i), (ii) and "
            "(iii) all satisfied and the concatenation of the two components is "
            "exactly the frozen report — but NOTHING is handed over before the "
            "mapping is committed. Rejection source: (iv) staging (first "
            "component length 0 vs required 1 at an input with one signalled "
            "error). A spec whose value modelled only the item sequence cannot "
            "reject this rival at all, which is what makes it the case this "
            "battery is built around."
        ),
    },
    {
        "id": "terminal-item-never-reported",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _NO_ALLOWANCE,
        "witness": _W_TERMINAL,
        "refinement": (
            "the faithful real patch drops the terminal yield guarded by the still-rewriting flag, "
            "so a run whose last further pass was still rewriting references "
            "reports nothing about it and collectstatic exits successfully. The "
            "P2P test that drives the passes past their allowance and asserts the "
            "run raises fails outright (no exception raised). It would NOT "
            "resolve."
        ),
        "rationale": (
            "partial-domain break of the terminal-item leg of (iv): correct on "
            "every input whose last further pass rewrote nothing (the common "
            "case), wrong on every input where it did. Rejection source: the "
            "terminal item is absent from the pre-commit component (length 0 vs "
            "required 1) at an input whose single further pass still rewrote a "
            "reference."
        ),
    },
    {
        "id": "terminal-item-deferred-past-the-commit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ALLOWANCE_DEFERRED,
        "witness": _W_TERMINAL,
        "refinement": (
            "the faithful real patch keeps the terminal yield but moves it below "
            "`self.hashed_files.update(hashed_files)`, ahead of the collected "
            "files. The yielded sequence is IDENTICAL to gold's, so the F2P still "
            "passes and the run still raises; but the mapping of a run that never "
            "settled has already been committed to the shared store by the time "
            "the caller aborts, so the P2P test asserting what the store holds "
            "after that failure fails. It would NOT resolve."
        ),
        "rationale": (
            "the sharpest staging case: the terminal item is present, with the "
            "right value, and the concatenation of the two components is exactly "
            "the frozen report — only its side of the commit differs. Separates "
            "'the terminal item exists' from 'the terminal item is handed over in "
            "time', which case 9 alone cannot. Rejection source: (iv) staging "
            "(pre-commit component length 0 vs required 1). Shares case 9's "
            "witness input by design — the two rivals differ from gold in "
            "different ways at the same point, and the same projection refutes "
            "both, which is what shows the clause is about the commit rather than "
            "about the item's presence."
        ),
    },
    {
        "id": "staging-partial-domain-errors-withheld",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _STAGE_ERRORS_WITHHELD,
        "witness": _W_STAGE_ERRORS_WITHHELD,
        "refinement": (
            "the faithful real patch yields the non-adjustable files inline as "
            "before but collects the Exception items into the same end-of-run "
            "buffer as the adjustable ones, so they are yielded after the "
            "accumulated mapping has been written to the shared store. On any "
            "fixture where no file fails it is byte-for-byte gold; where one "
            "fails the caller raises only after the mapping has been committed, "
            "and the test asserting what the store holds after a failed run "
            "fails for the same measured reason as the all-deferred rival. It "
            "would NOT resolve."
        ),
        "rationale": (
            "a partial-domain staging break that is EXACTLY the frozen behavior "
            "on every input with no signalled error, and diverges only on the "
            "inputs where the staging is observable at all (an error is the item "
            "the consumer abandons the report on). It keeps the plain items early, "
            "the collection held back, and the terminal item exactly where the "
            "frozen model puts it, so nothing case 8 or the two terminal-item "
            "cases rely on refutes it. Rejection source: (iv) staging (pre-commit "
            "length 1 vs required 2 at a plain item plus an error). Its witness "
            "deliberately keeps a plain item so the projection separates it from "
            "case 8's rival rather than merely from gold."
        ),
    },
    {
        "id": "staging-sides-of-the-commit-exchanged",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _STAGE_SWAPPED,
        "witness": _W_STAGE_SWAPPED,
        "refinement": (
            "the faithful real patch yields the collected adjustable files BEFORE "
            "the accumulated mapping is written to the shared store and the "
            "non-adjustable files and Exception items after it. The error item is "
            "again seen by the caller only once the mapping has been committed, so "
            "the same test fails for the same measured reason; the reported order "
            "also changes, though the F2P does not check order. It would NOT "
            "resolve."
        ),
        "rationale": (
            "probes clause (iv) from the opposite direction to cases 8 and 11: "
            "nothing is emptied, dropped, duplicated or staled — both components "
            "keep their frozen LENGTHS — and only which items sit on which side "
            "of the commit differs. That is why its witness projects the NAMES of "
            "the pre-commit component (frozen [\"e\"], rival [\"a\"]) rather than "
            "a length: it is the case that shows the clause pins membership of "
            "each side and not merely how much each side holds."
        ),
    },
    {
        "id": "terminal-item-over-reported-across-passes",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ALLOWANCE_ACCUMULATED,
        "witness": _W_TERMINAL_OVER,
        "refinement": (
            "the faithful real patch keeps the per-pass flag that decides whether "
            "to run a further pass, but reports the terminal item off a second, "
            "run-wide flag that is never reset (`any_substitutions = "
            "any_substitutions or substitutions` inside the pass loop, tested in "
            "place of `substitutions` at the `if substitutions:` guard). Which "
            "passes execute, what every item holds and which side of the commit it "
            "falls on are all gold's; the ONLY difference is that a run which "
            "needed a rewriting pass and then settled is reported as having "
            "exhausted its allowance. collectstatic raises on that item, so a "
            "normal collectstatic run over a fixture with any adjustable reference "
            "at all dies with RuntimeError('Max post-process passes exceeded.') "
            "instead of reporting its stats. Measured on this instance: NOT "
            "resolved, 3/3 attempts, consistent (not flaky) — F2P 0/1 and "
            "PASS_TO_PASS 6/31, the widest break any rival in this battery causes."
        ),
        "rationale": (
            "the mirror image of case 9 and the reason clause (iv) is an "
            "exact-equality rather than a lower bound on the terminal item: a spec "
            "that only forbade DROPPING the item accepts this rival, which reports "
            "it too often. It is also the only case that turns on the further-pass "
            "flag being REPLACED rather than accumulated, which is what the frozen "
            "`unsettled := pass.any …` says and what `substitutions = False` at the "
            "top of the real pass loop makes true. Rejection source: (iv), "
            "pre-commit component length 1 vs required 0. Its witness needs TWO "
            "further passes — one rewriting, then one that settles — which is "
            "exactly the input cases 9 and 10 cannot use, since on their "
            "single-rewriting-pass input this rival agrees with the model."
        ),
    },
    {
        "id": "terminal-item-reported-under-another-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ALLOWANCE_MISNAMED,
        "witness": _W_TERMINAL_NAME,
        "refinement": (
            "the faithful real patch yields the terminal item in exactly gold's "
            "place, guarded by exactly gold's flag, carrying gold's exception and "
            "message, under the reported name 'all' instead of 'All'. The caller "
            "writes that name verbatim into its error stream "
            "(\"Post-processing '%s' failed!\" % original_path, "
            "collectstatic.py:130) and the P2P test that drives the passes past "
            "their allowance compares that stream literally against "
            "\"Post-processing 'All' failed!\\n\\n\" (test_storage.py:176), so it "
            "fails on the string. Measured on this instance: NOT resolved, 3/3 "
            "attempts, consistent (not flaky) — F2P 1/1 (the F2P never exhausts "
            "the allowance) and PASS_TO_PASS 30/31, the single failure being that "
            "test. The narrowest measured break in the battery, and one only a "
            "clause pinning the item's payload can reject."
        ),
        "rationale": (
            "a boundary token swap: presence, guard, side of the commit, position "
            "within the component, and every other item are frozen, and the two "
            "components keep their frozen lengths — so every length projection in "
            "this battery agrees with the model here. Only the reported name "
            "differs, which is why the witness projects the NAMES of the "
            "pre-commit component (frozen [\"All\"], rival [\"all\"]). It is the "
            "case that shows the equality against `allowanceItem` pins the item's "
            "payload and not merely that some item is reported at that instant, "
            "and it shares case 9's input by design so the same input separates "
            "three different terminal-item defects."
        ),
    },
]


# ===========================================================================
# AXIOM lane — NONE. The bundle declares no callee axiom (axioms region empty);
# the axiom lane is G-AX's job and this gate ignores AXIOM_TESTS.
# ===========================================================================
AXIOM_TESTS = []
