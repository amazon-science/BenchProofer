"""PBT manifest for django__django-16263.

NOT a Nagini module: a record of adversarially-reasoned falsification cases the
runner (swebench_nagini.pbt) executes and stamps RESULT onto. Spec cases are
full model.py variants that share the FROZEN spec byte-for-byte (region surgery:
ONLY the text inside an # impl-start / # impl-end block is edited — the spec
view, and therefore markers.same_spec, is never touched). They are checked by
Nagini verify + markers.same_spec. Axiom cases here are A-reference probes: this
bundle consumes NO @ContractOnly axiom (meta.axioms == []); the one non-R/I
element is the deep model `collect_refs == real get_refs()`. The probes execute
real Django in the instance image (apply_gold=True, post-patch) and assert the
deep model + decision discriminators agree — embedding the bundle's own
axiom_check.py logic so each probe stands alone in-container.

Defended surface (read from model.py / refinement.md / mapping.md / patch):
  TWO modeled functions, BOTH with read-only (Acc(...,1/2)) carrier inputs.

  (1) existing_summary_forces_derived(selected, summ, filter_summary)
      Requires/Ensures Acc(list_pred(selected),1/2) and Acc(list_pred(summ),1/2)
      — selected and summ are READ-ONLY; filter_summary is a plain int.
      Load-bearing postcondition (the whole decision-#1 spec):
          Result() == (any_selected_summary(ToSeq(selected), ToSeq(summ))
                       or filter_summary != 0)
      i.e. the derived (subquery) form is forced exactly when some column is
      BOTH selected AND a row-summary, OR a retained filter exists. The two
      axes the gold flips (source self.annotations->annotation_select, and
      predicate truthiness->contains_aggregate/over_clause) live in the
      CONJUNCTION s!=0 AND m!=0. The discriminating subdomains (the three F2P):
        selected=[1],summ=[0] -> False  (a SELECTED non-aggregate column;
                                          test_non_aggregate_annotation_pruned)
        selected=[0],summ=[1] -> False  (an ALIAS-ONLY aggregate;
                                          test_unused_aliased_aggregate_pruned)
        selected=[1],summ=[1] -> True   (a SELECTED aggregate; wraps)

  (2) inner_column_kept(alias, added, ref_tree)
      Requires/Ensures Acc(list_pred(added),1/2) and Acc(list_pred(ref_tree),1/2)
      — added and ref_tree are READ-ONLY; alias is a plain int.
      Load-bearing postcondition (the whole decision-#2 mask spec):
          Result() == (seq_contains(ToSeq(added), alias)
                       or seq_contains(collect_refs(ToSeq(ref_tree)), alias))
      i.e. a pre-existing annotated column survives the inner selection iff it
      is one of the pushed-out summary names OR is referenced (transitively, via
      the get_refs fold) by a pushed-out summary. The discriminating F2P:
        unreferenced authors_count -> pruned (test_unreferenced_aggregate_annotation_pruned)
        referenced  authors_count -> kept   (test_referenced_aggregate_annotation_kept)

  The postconditions are GROUNDED in the inputs (every @Pure helper —
  any_selected_summary / seq_contains / collect_refs — fully unfolds over the
  arg carriers; there is no opaque answer-key oracle the impl could echo without
  doing the work). So the ungrounded-oracle-echo class is N/A (see assessment);
  the faithful structural reshape IS the gold decision and serves as the
  positive control instead. Both functions take read-only inputs, so the
  FRAME-MUTATION probe is MANDATORY for each (cases fm-esfd-* and fm-ick-*).

  Both contracts additionally carry Requires(MustTerminate(2)) (TOTAL
  correctness: the decision must actually ANSWER), discharged in each gold loop
  by the strictly decreasing measure Invariant(MustTerminate(i)) /
  Invariant(MustTerminate(j)). Nagini verifies partial correctness by default,
  so without the obligation a same-spec body that diverges before returning
  satisfies every Ensures vacuously — the audit's P1 witness class. The
  weak-nonterm-esfd / weak-nonterm-ick rivals below pin the rejection.
"""
from pathlib import Path

INSTANCE = "django__django-16263"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each is a contiguous slice that lives ENTIRELY inside ONE impl
# region (between # impl-start and # impl-end), so every _swap keeps same_spec.
# Verified unique against model.py at authoring time.
# ---------------------------------------------------------------------------

# --- existing_summary_forces_derived impl region ---
# the per-step carrier reads (unique: `s = selected[i - 1]`)
_ESFD_READ = "        s = selected[i - 1]\n        m = summ[i - 1]\n"
# the per-step update branch + decrement (unique: the conjunction guard)
_ESFD_UPDATE = (
    "        if s != 0 and m != 0:\n"
    "            found = True\n"
    "        i = i - 1"
)
# the return line (unique)
_ESFD_RETURN = "    return found or filter_summary != 0"

# --- inner_column_kept impl region ---
# the first-loop carrier read (unique: `c = added[i - 1]`)
_ICK_ADDED_READ = (
    "        c = added[i - 1]\n"
    "        Assert(ToSeq(added).drop(i - 1)[0] == c)\n"
)
# the first-loop set branch + decrement (unique: `if c == alias:`)
_ICK_ADDED_SET = (
    "        if c == alias:\n"
    "            in_added = True\n"
    "        i = i - 1"
)
# the second-loop set branch + decrement (unique: `if node != 0 and node == alias:`)
_ICK_REFS_SET = (
    "        if node != 0 and node == alias:\n"
    "            in_refs = True\n"
    "        j = j - 1"
)
# the return line (unique)
_ICK_RETURN = "    return in_added or in_refs"


# ===========================================================================
# SPEC LANE
# ===========================================================================
SPEC_TESTS = [

    # -- 1. POSITIVE CONTROL (soundness) — decision #1 -----------------------
    # Structurally-different but CORRECT impl of existing_summary_forces_derived:
    # replace the branch `if s != 0 and m != 0: found = True` with the
    # accumulate reshape `found = found or (s != 0 and m != 0)`. The HEAD BIT
    # (s != 0 and m != 0) is byte-identical, so the gold linking Assert
    #   any_selected_summary(drop(i-1)) == ((s!=0 and m!=0) or any_..(drop(i)))
    # still applies directly and the loop invariant
    #   found == any_selected_summary(ToSeq(selected).drop(i))
    # is re-established by found_new = found_old or head. No new induction lemma
    # is introduced (directives 2/3): same backward loop, same front-recursive
    # unfold the verifier already discharges. MUST verify.
    {
        "id": "pos-control-esfd-accumulate",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _ESFD_UPDATE,
            "        found = found or (s != 0 and m != 0)\n"
            "        i = i - 1",
        ),
        "rationale": "a structurally-different but correct impl (the if-branch "
                     "reshaped to a boolean accumulate, gold invariant + linking "
                     "Assert kept verbatim) MUST verify; else decision #1's "
                     "postcondition is SPEC-TOO-STRONG. found stays == "
                     "any_selected_summary(ToSeq(selected).drop(i)), so the "
                     "front-recursive unfold still discharges.",
    },

    # -- 2. POSITIVE CONTROL (soundness) — decision #2 -----------------------
    # inner_column_kept first loop: reshape `if c == alias: in_added = True` to
    # `in_added = in_added or (c == alias)`. The first loop's only invariant is
    #   in_added == seq_contains(ToSeq(added).drop(i), alias)
    # and the gold per-step Asserts (head==c, tail==drop(i)) are kept, so the
    # seq_contains unfold links in_added_new = in_added_old or (c==alias) to
    # seq_contains(drop(i-1)). Same shape, no extra lemma. MUST verify.
    {
        "id": "pos-control-ick-accumulate",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _ICK_ADDED_SET,
            "        in_added = in_added or (c == alias)\n"
            "        i = i - 1",
        ),
        "rationale": "a structurally-different but correct impl of decision #2's "
                     "added-membership loop (if-branch -> boolean accumulate, gold "
                     "invariant + Asserts kept) MUST verify; else SPEC-TOO-STRONG. "
                     "in_added stays == seq_contains(ToSeq(added).drop(i), alias).",
    },

    # -- 3. ADMISSIBILITY — decision #1 --------------------------------------
    # The Requires is only Acc(list_pred(selected),1/2) + Acc(list_pred(summ),
    # 1/2) + len(selected)==len(summ); there is no value-domain restriction, so
    # the gold impl already proves admissibility for any equal-length pair. We
    # confirm it by keeping the gold impl verbatim and adding, BEFORE the loop
    # (inside the impl region), asserts that the half-permission grants are held
    # and the lengths are readable+equal under them — i.e. the Requires is
    # establishable for a concrete F2P-shaped input. No self-call is added (that
    # would leave the impl region); the Acc/len asserts are the admissibility
    # witness the verifier discharges from the precondition alone.
    {
        "id": "admiss-esfd-read-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE,
            "    # impl-start\n    found = False\n    i = len(selected)\n",
            "    # impl-start\n"
            "    Assert(Acc(list_pred(selected), 1 / 2))   # read-only grant held\n"
            "    Assert(Acc(list_pred(summ), 1 / 2))       # read-only grant held\n"
            "    Assert(len(selected) == len(summ))        # equal lengths readable\n"
            "    found = False\n    i = len(selected)\n",
        ),
        "rationale": "the precondition (Acc(...,1/2) on both carriers + equal "
                     "lengths) must admit a normal F2P-shaped input: the read-only "
                     "grants are held and the lengths are readable+equal under "
                     "them. If this cannot be established, PRECOND-TOO-STRONG. "
                     "Gold impl otherwise verbatim (asserts added inside impl "
                     "region only).",
    },

    # -- 4. FRAME-MUTATION (MANDATORY: selected/summ are Acc(...,1/2)) -------
    # Decision-#1 rival that WRITES to the read-only input to satisfy the
    # postcondition vacuously: overwrite selected[i-1] = 0 so every column reads
    # as not-selected and `found` stays False — a wrong "never wrap" decision
    # that an impl could only reach by mutating the input it was handed. With
    # only 1/2 permission this write is ILLEGAL; Nagini rejects for INSUFFICIENT
    # PERMISSION (need full Acc(list_pred(selected)) to mutate selected[i-1]).
    # The gold invariants + linking Assert are kept verbatim so the rejection is
    # attributable solely to the write.
    {
        "id": "fm-esfd-overwrite-selected",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ESFD_READ,
            "        selected[i - 1] = 0   # ILLEGAL write to read-only input\n"
            "        s = selected[i - 1]\n        m = summ[i - 1]\n",
        ),
        "refinement": "the real get_aggregation reads self.annotation_select / the "
                     "annotation attributes; it never REWRITES which columns are "
                     "selected. A patch that zeroed the selected set to force "
                     "has_existing_aggregation=False would skip the wrapping "
                     "subquery even for a SELECTED aggregate (selected=[1],summ="
                     "[1]) and produce a wrong GROUP-BY count — it would NOT "
                     "resolve the F2P (it breaks the kept-wrapping P2P aggregates). "
                     "Mutating the carrier is a pure spec-bypass with no real "
                     "counterpart.",
        "rationale": "REJECT comes from the PERMISSION SYSTEM: Acc(list_pred("
                     "selected),1/2) grants read-only access; `selected[i-1] = 0` "
                     "needs full Acc(list_pred(selected)), so it fails for "
                     "insufficient permission. If it verified, the read-only frame "
                     "guarantee on the selected-carrier would be hollow.",
    },

    # -- 5. FRAME-MUTATION (MANDATORY: added/ref_tree are Acc(...,1/2)) ------
    # Decision-#2 rival that WRITES to the read-only ref_tree to satisfy the
    # postcondition vacuously: overwrite ref_tree[j-1] = alias so the second loop
    # finds `alias` as a reference of EVERY pushed-out summary and returns
    # in_refs=True (a wrong "keep everything" mask) without observing the real
    # references. Needs full Acc(list_pred(ref_tree)); only 1/2 granted -> reject
    # for insufficient permission. Gold invariants/asserts kept verbatim.
    {
        "id": "fm-ick-overwrite-reftree",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            "        node = ref_tree[j - 1]\n"
            "        Assert(ToSeq(ref_tree).drop(j - 1)[0] == node)\n",
            "        ref_tree[j - 1] = alias   # ILLEGAL write to read-only input\n"
            "        node = ref_tree[j - 1]\n"
            "        Assert(ToSeq(ref_tree).drop(j - 1)[0] == node)\n",
        ),
        "refinement": "the real get_aggregation reads inner_query.annotations[name]"
                     ".get_refs(); it never REWRITES the expression tree. A patch "
                     "that injected `alias` into every pushed-out summary's refs "
                     "would keep EVERY pre-existing annotation in the inner select "
                     "(the pre-patch set_annotation_mask(self.annotation_select) "
                     "behaviour) — exactly what test_unreferenced_aggregate_"
                     "annotation_pruned forbids (authors_count would reappear in "
                     "the inner SQL) — so it would NOT resolve the F2P. Mutating "
                     "the ref tree is a pure spec-bypass with no real counterpart.",
        "rationale": "REJECT comes from the PERMISSION SYSTEM: Acc(list_pred("
                     "ref_tree),1/2) is read-only; `ref_tree[j-1] = alias` needs "
                     "full Acc(list_pred(ref_tree)), so it fails for insufficient "
                     "permission. If it verified, the read-only frame guarantee on "
                     "the reference-tree carrier would be hollow.",
    },

    # -- 6. PARTIAL-DOMAIN — decision #1 PREDICATE axis (prepatch) -----------
    # Rival that forces the derived form on the mere PRESENCE of a SELECTED
    # column, ignoring whether it summarises: `found = found or (s != 0)`
    # (drops the m!=0 conjunct). This IS model_prepatch.py (the pre-patch
    # predicate). It diverges on selected=[1],summ=[0] (a lone SELECTED
    # non-aggregate column): the rival's found becomes True, the postcondition
    # requires Result()==(any_selected_summary([1],[0]) or 0!=0)==False. The
    # loop invariant found==any_selected_summary(drop(i)) is then unprovable
    # (the body set found for a non-summary column). MUST be rejected.
    {
        "id": "partial-domain-esfd-presence-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ESFD_UPDATE,
            "        found = found or (s != 0)   # prepatch: presence forces wrapping\n"
            "        i = i - 1",
        ),
        "refinement": "this is the pre-patch predicate (model_prepatch.py): the "
                     "mere presence of any SELECTED pre-existing annotation forces "
                     "the wrapping subquery. Its faithful real patch is the "
                     "UNCHANGED buggy `if (... or existing_annotations ...)` which "
                     "still wraps for a selected non-aggregate Lower() column -> 2 "
                     "SELECTs where 1 is expected, so it does NOT resolve "
                     "test_non_aggregate_annotation_pruned.",
        "rationale": "REJECT from the postcondition Result()==(any_selected_summary"
                     "(ToSeq(selected),ToSeq(summ)) or filter_summary!=0): on "
                     "selected=[1],summ=[0] the rival returns True but the spec "
                     "requires False (summ=0 -> not a summary). The loop invariant "
                     "found==any_selected_summary(drop(i)) breaks because the body "
                     "set found ignoring the m!=0 conjunct.",
    },

    # -- 7. PARTIAL-DOMAIN — decision #1 SOURCE axis (prepatch_3) ------------
    # Rival that forces the derived form on any column that summarises,
    # IGNORING whether it is selected: `found = found or (m != 0)` (drops the
    # s!=0 conjunct). This IS model_prepatch_3.py (built from self.annotations,
    # all annotations incl. alias-only). It diverges on selected=[0],summ=[1]
    # (an ALIAS-ONLY aggregate): rival's found becomes True, the postcondition
    # requires Result()==(any_selected_summary([0],[1]) or 0)==False. MUST be
    # rejected.
    {
        "id": "partial-domain-esfd-source-all",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ESFD_UPDATE,
            "        found = found or (m != 0)   # prepatch_3: built from ALL annotations\n"
            "        i = i - 1",
        ),
        "refinement": "this is the pre-patch source axis (model_prepatch_3.py): the "
                     "decision is built from self.annotations (ALL pre-existing "
                     "annotations, incl. alias-only ones) rather than "
                     "self.annotation_select. Its faithful real patch still wraps "
                     "for an alias()-only aggregate -> 2 SELECTs where 1 is "
                     "expected, so it does NOT resolve "
                     "test_unused_aliased_aggregate_pruned.",
        "rationale": "REJECT from the postcondition: on selected=[0],summ=[1] the "
                     "rival returns True but the spec requires False (selected=0 -> "
                     "the column does not participate). The loop invariant "
                     "found==any_selected_summary(drop(i)) breaks because the body "
                     "set found ignoring the s!=0 conjunct.",
    },

    # -- 8. PARTIAL-DOMAIN — decision #2 mask (prepatch_2) -------------------
    # Rival that keeps EVERY pre-existing annotation in the inner select:
    # `return in_added or in_refs or True` (i.e. unconditional keep). This IS
    # model_prepatch_2.py (the pre-patch set_annotation_mask(self.annotation_
    # select)). It diverges when alias is neither pushed-out nor referenced
    # (e.g. alias not in added and not in collect_refs(ref_tree)): the rival
    # returns True, the spec requires False. MUST be rejected.
    {
        "id": "partial-domain-ick-keep-all",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ICK_RETURN,
            "    return in_added or in_refs or True   # prepatch_2: keep every annotation",
        ),
        "refinement": "this is the pre-patch inner mask (model_prepatch_2.py): "
                     "set_annotation_mask(self.annotation_select) kept every "
                     "pre-existing annotation in the inner selection regardless of "
                     "references. Its faithful real patch leaves an UNREFERENCED "
                     "aggregate (authors_count) in the inner SQL -> "
                     "test_unreferenced_aggregate_annotation_pruned fails "
                     "(authors_count must NOT appear inside), so it does NOT "
                     "resolve the F2P.",
        "rationale": "REJECT from the postcondition Result()==(seq_contains(ToSeq("
                     "added),alias) or seq_contains(collect_refs(ToSeq(ref_tree)),"
                     "alias)): when alias is neither pushed-out nor referenced the "
                     "rival returns True (`or True`) but the spec requires False. "
                     "The pinned Result() value is contradicted on that subdomain.",
    },

    # -- 9. PARTIAL-DOMAIN — decision #2 drop the reference channel ----------
    # Rival that keeps a column ONLY when it is a pushed-out name, ignoring the
    # reference channel: `return in_added` (drops `or in_refs`). It is correct
    # whenever an alias is pushed-out or unreferenced, but diverges on a
    # REFERENCED-but-not-pushed-out alias (the test_referenced_aggregate_
    # annotation_kept subdomain: authors_count is referenced by the pushed-out
    # Avg(Ref('authors_count'))). The rival returns False, the spec requires
    # True. MUST be rejected.
    {
        "id": "partial-domain-ick-drop-refs",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ICK_RETURN,
            "    return in_added   # drops the reference channel (or in_refs)",
        ),
        "refinement": "an impl that masks by pushed-out names only (annotation_mask "
                     "= added_aggregate_names, never |= get_refs()) would DROP a "
                     "referenced pre-existing annotation. Its faithful real patch "
                     "removes authors_count from the inner select even though the "
                     "pushed-out Avg(Ref('authors_count')) references it -> the "
                     "outer Ref resolves to nothing -> test_referenced_aggregate_"
                     "annotation_kept fails (authors_count must appear twice). So "
                     "it does NOT resolve the F2P/P2P.",
        "rationale": "REJECT from the postcondition: on a referenced-but-not-"
                     "pushed-out alias (in_added False, in_refs True) the rival "
                     "returns False but the spec requires True (seq_contains("
                     "collect_refs(ref_tree),alias) is True). The second loop's "
                     "result is discarded, contradicting the pinned Result() value.",
    },

    # -- 10a. VACUITY / CONTROL-FLOW-EFFECT — decision #1 diverges ------------
    # The audit's P1 witness class: empty the loop body of ALL progress (i is
    # never decremented, found never changes), so `while i > 0` never exits on
    # any non-empty carrier; every Ensures then holds only vacuously (no normal
    # exit) and the value/frame invariants are trivially preserved by the no-op
    # body. Under the PRE-FIX contract (no MustTerminate) this rival VERIFIED —
    # the hole the audit exhibited. It must now be REJECTED by the termination
    # obligation: the function carries Requires(MustTerminate(2)) and the
    # no-progress loop cannot re-establish the strictly decreasing measure
    # Invariant(MustTerminate(i)).
    {
        "id": "weak-nonterm-esfd",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ESFD_UPDATE,
            "        # NO PROGRESS: i never decreases — the loop spins forever\n"
            "        # on any non-empty carrier; the postconditions hold only\n"
            "        # vacuously.\n"
            "        found = found",
        ),
        "refinement": "a get_aggregation whose wrapping decision loops forever "
                     "instead of answering hangs every count()/aggregate() call; "
                     "its faithful real patch times out ALL F2P/P2P aggregation "
                     "tests and resolves nothing. Divergence is a pure "
                     "spec-bypass with no real counterpart (the real "
                     "has_existing_aggregation any(...) always completes).",
        "rationale": "REJECT comes from the TERMINATION OBLIGATION: the contract "
                     "carries Requires(MustTerminate(2)) and the loop's measure "
                     "Invariant(MustTerminate(i)) must strictly decrease each "
                     "iteration; the no-progress body leaves i unchanged, so the "
                     "obligation cannot be discharged. If it verified, every "
                     "Ensures would be satisfiable vacuously by divergence.",
    },

    # -- 10b. VACUITY / CONTROL-FLOW-EFFECT — decision #2 diverges ------------
    # Same class on inner_column_kept's second loop: j is never decremented, so
    # `while j > 0` spins forever on any non-empty ref_tree and the
    # postcondition holds only vacuously. Must be REJECTED by the termination
    # obligation (measure Invariant(MustTerminate(j)) cannot decrease).
    {
        "id": "weak-nonterm-ick",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ICK_REFS_SET,
            "        # NO PROGRESS: j never decreases — the loop spins forever\n"
            "        # on any non-empty ref_tree; the postcondition holds only\n"
            "        # vacuously.\n"
            "        in_refs = in_refs",
        ),
        "refinement": "a get_aggregation whose annotation-mask computation loops "
                     "forever never emits the inner query; its faithful real "
                     "patch hangs every aggregation over an annotated queryset "
                     "and resolves nothing. Divergence is a pure spec-bypass "
                     "with no real counterpart (the real mask loop over "
                     "added_aggregate_names always completes).",
        "rationale": "REJECT comes from the TERMINATION OBLIGATION: the contract "
                     "carries Requires(MustTerminate(2)) and the second loop's "
                     "measure Invariant(MustTerminate(j)) must strictly decrease; "
                     "the no-progress body leaves j unchanged, so the obligation "
                     "cannot be discharged and Nagini rejects.",
    },

    # -- 10. SUPPORTING near-miss: invert decision #1 (cheap mechanical) -----
    # A wrong impl that returns the NEGATION of the wrapping decision. Mechanical,
    # but carries a real refinement: it wraps exactly when it should not and vice
    # versa — the opposite of the gold decision, resolving nothing. Confirms the
    # postcondition pins the polarity of Result().
    {
        "id": "support-esfd-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ESFD_RETURN,
            "    return not (found or filter_summary != 0)   # inverted decision",
        ),
        "refinement": "returning the inverse forces the derived subquery exactly "
                     "when the gold would NOT and skips it when the gold WOULD; it "
                     "wraps a bare non-aggregate query (extra SELECT) and fails to "
                     "wrap a selected aggregate (wrong GROUP-BY count). Its "
                     "faithful real patch resolves no F2P/P2P.",
        "rationale": "REJECT from Result()==(any_selected_summary(...) or "
                     "filter_summary!=0): `not (...)` contradicts the pinned value "
                     "on every input where the gold decision is determinate.",
    },
]


# ===========================================================================
# AXIOM LANE  (A-reference only — meta.axioms == []; no @ContractOnly axiom)
# ===========================================================================
#
# This bundle's single non-R/I trust point is the deep model
#   collect_refs  ==  the real recursive get_refs() the gold patch ADDS
#     (BaseExpression.get_refs union over sources; Ref.get_refs == {self.refs}
#      a LEAF; WhereNode.get_refs union over children).
# Each probe is self-contained, imports Django + stdlib only, opens nothing on
# disk (no codec concern — directive 5), needs no bundle file in-container
# (directive 6), and CALLS the real callee (never regex-scrapes — directive 4).
# apply_gold=True: get_refs only exists post-patch. Exit 0 iff the obligation
# holds. The probes EMBED axiom_check.py's flatten/collect_refs logic so they
# stand alone.

# ---- ax-ref-collect-refs: the A-reference soundness check.
# Build real Django expression trees (incl. Refs whose source is itself a
# Ref-bearing subtree — the leaf-vs-recurse divergent region), run the REAL
# get_refs(), and assert set(collect_refs(flatten(tree))) == get_refs(tree) and
# per-alias membership. A source-recursing flatten that over-collects refs
# nested inside a Ref's source (which real Ref.get_refs never reports) is caught.
_AX_REF_COLLECT = r'''
import os, random, sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        USE_TZ=False,
    )
    django.setup()
from django.db.models import Value
from django.db.models.expressions import Ref, ExpressionWrapper
from django.db.models.functions import Concat
from django.db.models.aggregates import Sum, Avg
from django.db.models.fields import IntegerField, CharField

def collect_refs(tree):
    # front-recursive transcription of model.py @Pure collect_refs
    if len(tree) == 0:
        return []
    if tree[0] != 0:
        return [tree[0]] + collect_refs(tree[1:])
    return collect_refs(tree[1:])

def _collect_refs_iter(tree):
    return [n for n in tree if n != 0]

def seq_contains(seq, x):
    if len(seq) == 0:
        return False
    return seq[0] == x or seq_contains(seq[1:], x)

def _code_for(refs, codes):
    if refs not in codes:
        codes[refs] = len(codes) + 1
    return codes[refs]

def _source_expressions(expr):
    g = getattr(expr, "get_source_expressions", None)
    return g() if g is not None else []

def flatten_expr(expr, codes):
    # Ref is a LEAF: referent code only, NO descent into its source (matches
    # Ref.get_refs() == {self.refs}). Other nodes contribute 0 + folded children.
    if isinstance(expr, Ref):
        return [_code_for(expr.refs, codes)]
    out = [0]
    for sub in _source_expressions(expr):
        if sub is not None:
            out.extend(flatten_expr(sub, codes))
    return out

def real_codes(expr, codes):
    return {_code_for(r, codes) for r in expr.get_refs()}

def check(expr):
    codes = {}
    flat = flatten_expr(expr, codes)
    real = real_codes(expr, codes)
    if collect_refs(flat) != _collect_refs_iter(flat):
        print("collect_refs transcription drifted from model fold on", repr(expr)); sys.exit(1)
    model_set = set(collect_refs(flat))
    if model_set != real:
        print("A-REFERENCE UNSOUND on", repr(expr), "real", real, "model", model_set); sys.exit(1)
    for code in list(codes.values()):
        if seq_contains(collect_refs(flat), code) != (code in real):
            print("membership mismatch on code", code, "for", repr(expr)); sys.exit(1)

src = Sum("x")
boundary = [
    Ref("a", src),
    ExpressionWrapper(Ref("a", src), output_field=IntegerField()),
    ExpressionWrapper(Value(1), output_field=IntegerField()),
    Concat(Ref("a", src), Value(" "), Ref("b", src)),
    Concat(Value("x"), Value("y")),
    Avg(Ref("authors_count", src)),
    ExpressionWrapper(Concat(Ref("a", src), Concat(Ref("b", src), Ref("a", src))),
                      output_field=CharField()),
    Ref("outer", Ref("inner", src)),                          # real get_refs == {outer}
    Ref("outer", Concat(Ref("inner1", src), Ref("inner2", src))),  # == {outer}
    Avg(Ref("outer", Sum(Ref("inner", src)))),                # == {outer}
    Concat(Ref("a", Ref("b", src)), Ref("c", src)),           # == {a, c}
    ExpressionWrapper(Ref("outer", ExpressionWrapper(Ref("inner", src),
                      output_field=IntegerField())), output_field=IntegerField()),
]
for e in boundary:
    check(e)

rng = random.Random(16263)
names = ["a", "b", "c", "d", "outer", "inner", "authors_count", "name_lower"]
def build(depth):
    if depth <= 0 or rng.random() < 0.35:
        r = rng.random()
        if r < 0.5:
            return Ref(rng.choice(names), build(depth - 1))
        elif r < 0.7:
            return Ref(rng.choice(names), src)
        return Value(rng.randint(0, 9))
    kids = [build(depth - 1) for _ in range(rng.randint(1, 3))]
    return Concat(*kids) if len(kids) >= 2 else ExpressionWrapper(
        kids[0], output_field=IntegerField())
for _ in range(5000):
    check(build(rng.randint(0, 4)))

print("ax-ref-collect-refs OK: collect_refs deep model == real get_refs "
      "(Ref-as-leaf) on 12 boundary (incl. nested Ref-in-source) + 5000 fuzz "
      "trees whose Ref sources are themselves Ref-bearing; transcription "
      "mirrors the model fold.")
sys.exit(0)
'''

# ---- ax-decisions: ground the two decision discriminators against real Django
# expression semantics on all F2P scenarios. The `selected` bit is grounded via
# a real Query's annotation_select (annotate -> select=True; alias -> select=
# False); the `summ` bit via contains_aggregate/contains_over_clause; the mask
# via real get_refs() of the pushed-out summary. Mirrors axiom_check.check_decisions.
_AX_DECISIONS = r'''
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        USE_TZ=False,
    )
    django.setup()
from django.db.models import Value
from django.db.models.expressions import Ref
from django.db.models.functions import Lower
from django.db.models.aggregates import Count, Sum, Avg
from django.db.models.sql.query import Query

def collect_refs(tree):
    if len(tree) == 0:
        return []
    if tree[0] != 0:
        return [tree[0]] + collect_refs(tree[1:])
    return collect_refs(tree[1:])

def seq_contains(seq, x):
    if len(seq) == 0:
        return False
    return seq[0] == x or seq_contains(seq[1:], x)

def _code_for(refs, codes):
    if refs not in codes:
        codes[refs] = len(codes) + 1
    return codes[refs]

def _source_expressions(expr):
    g = getattr(expr, "get_source_expressions", None)
    return g() if g is not None else []

def flatten_expr(expr, codes):
    if isinstance(expr, Ref):
        return [_code_for(expr.refs, codes)]
    out = [0]
    for sub in _source_expressions(expr):
        if sub is not None:
            out.extend(flatten_expr(sub, codes))
    return out

def esfd(selected, summ, filter_summary):
    return any(s != 0 and m != 0 for s, m in zip(selected, summ)) or filter_summary != 0

def ick(alias, added, flat):
    return seq_contains(added, alias) or seq_contains(collect_refs(flat), alias)

def _selected_bit(q, alias):
    return 1 if alias in q.annotation_select else 0

def _summary_bit(ann):
    return 1 if (getattr(ann, "contains_aggregate", True)
                 or getattr(ann, "contains_over_clause", True)) else 0

errs = []
# GROUND the selected bit: annotate() -> select=True -> in annotation_select.
q_sel = Query(None)
q_sel.add_annotation(Count(Value(1)), "authors_count", select=True)
if _selected_bit(q_sel, "authors_count") != 1:
    errs.append("annotate()d column must be SELECTED")
q_alias = Query(None)
q_alias.add_annotation(Count(Value(1)), "authors_count", select=False)
if _selected_bit(q_alias, "authors_count") != 0:
    errs.append("alias()-only column must NOT be selected (the source switch)")

cnt = Count(Value(1))
if cnt.contains_aggregate is not True:
    errs.append("Count(Value(1)).contains_aggregate must be True")
lower = Lower(Value("name"))
if lower.contains_aggregate is not False or lower.contains_over_clause is not False:
    errs.append("Lower(Value('name')) must be a non-summary")

# Decision #1 over the three F2P scenarios + supporting cases.
if esfd([0], [_summary_bit(cnt)], 0) is not False:
    errs.append("alias-only aggregate must NOT force wrapping (source axis)")
if esfd([1], [_summary_bit(lower)], 0) is not False:
    errs.append("selected non-aggregate must NOT force wrapping (predicate axis)")
if esfd([1], [_summary_bit(cnt)], 0) is not True:
    errs.append("selected aggregate must force wrapping")
if esfd([1], [0], 1) is not True:
    errs.append("retained filter alone must force wrapping")
if esfd([1, 0], [0, 0], 0) is not False:
    errs.append("no selected summary + no filter must NOT wrap")
if esfd([0, 0], [1, 1], 0) is not False:
    errs.append("all-unselected summaries must NOT wrap")
if esfd([], [], 0) is not False:
    errs.append("empty must NOT wrap")

# Decision #2 over the two F2P scenarios, grounded via real get_refs().
src = Sum("x")
count_star = Count("*")
codes = {}
flat = flatten_expr(count_star, codes)
ac = _code_for("authors_count", codes)
cstar = _code_for("__count", codes)
if ick(cstar, [cstar], flat) is not True:
    errs.append("pushed-out summary name must be kept")
if ick(ac, [cstar], flat) is not False:
    errs.append("unreferenced aggregate annotation must be pruned")
if count_star.get_refs() != set():
    errs.append("Count('*').get_refs() must be empty")

avg = Avg(Ref("authors_count", src))
codes2 = {}
flat2 = flatten_expr(avg, codes2)
ac2 = _code_for("authors_count", codes2)
avg_name = _code_for("__aggr", codes2)
if ick(ac2, [avg_name], flat2) is not True:
    errs.append("referenced aggregate annotation must be kept")
if "authors_count" not in avg.get_refs():
    errs.append("Avg(Ref('authors_count')).get_refs() must contain authors_count")

if errs:
    print("AX-DECISIONS FAIL:", errs); sys.exit(1)
print("ax-decisions OK: decision #1 (selected-AND-summary, grounded in real "
      "annotation_select) and decision #2 (added-or-get_refs) agree with real "
      "Django Count/Lower/Avg/Ref semantics on all F2P scenarios incl. the "
      "alias-only-aggregate source case.")
sys.exit(0)
'''

# ---- ax-cover: caller-domain containment for the deep model collect_refs.
# The MODEL passes to collect_refs EXACTLY the flattened ref-tree carrier (a
# List[int] of reference leaf codes, 0 for non-ref nodes). The deep model has
# NO Requires restricting its PSeq[int] argument — its domain is every finite
# int sequence. The caller (inner_column_kept) only ever builds such a carrier
# from a finite expression tree (codes >= 0). So every callee-input the model
# can reach is inside the deep model's domain (containment is vacuous: the model
# may legitimately cover MORE than the caller reaches — float-vs-int rule). The
# A-reference soundness (collect_refs == real get_refs) is checked separately by
# ax-ref-collect-refs; this case confirms there is no reachable tree shape OUT of
# the modelled domain.
_AX_COVER = r'''
import sys
# collect_refs(tree: PSeq[int]) has NO Requires; dom = every finite int sequence.
# inner_column_kept reads node = ref_tree[j-1] over ref_tree: List[int]; the
# flatten encodes a Ref leaf as a positive code and any other node as 0, so the
# carrier is always a finite sequence of non-negative ints — a subset of the
# unrestricted PSeq[int] domain. There is no tree the caller can build whose
# flattened carrier falls outside dom(collect_refs).
reachable_carriers = [[], [0], [5], [0, 5, 0], [3, 3, 0, 7], [0, 0, 0]]
for c in reachable_carriers:
    assert isinstance(c, list) and all(isinstance(x, int) for x in c), (
        "the model only passes finite int sequences to collect_refs")
print("ax-cover OK: collect_refs has NO Requires (domain = every finite int "
      "sequence); the caller only ever builds finite int carriers from an "
      "expression tree, so every caller-reachable input is in-domain "
      "(containment holds; no AXIOM-TOO-WEAK-FOR-CALLER).")
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-ref-collect-refs",
        "axiom": "collect_refs",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_REF_COLLECT,
        "rationale": "the A-reference deep model collect_refs must equal the real "
                     "recursive get_refs() (Ref-as-leaf) at the level the decision "
                     "observes (set membership) on every tree, incl. nested "
                     "Ref-in-source where a source-recursing flatten would "
                     "over-collect; any mismatch means decision #2's reference "
                     "channel misrepresents the gold get_refs (A-reference UNSOUND).",
    },
    {
        "id": "ax-decisions",
        "axiom": "existing_summary_forces_derived / inner_column_kept",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_DECISIONS,
        "rationale": "the two decision discriminators must agree with real Django "
                     "expression semantics on all F2P scenarios: the selected bit "
                     "grounded in real annotation_select (the source switch), the "
                     "summ bit in contains_aggregate/over_clause, the mask in real "
                     "get_refs(); a disagreement means the modelled decision does "
                     "not match the gold's runtime behaviour.",
    },
    {
        "id": "ax-cover-collect-refs-domain",
        "axiom": "collect_refs",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER,
        "rationale": "collect_refs has no Requires (domain = every finite int "
                     "sequence); the caller only ever builds finite int carriers "
                     "from an expression tree, so every caller-reachable input is "
                     "in-domain (containment). Covering more than the caller "
                     "reaches is SOUND (float-vs-int rule), not "
                     "AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
