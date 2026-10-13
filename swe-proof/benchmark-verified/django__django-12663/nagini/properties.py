"""properties.py — PBT falsification battery for django__django-12663.

NOT a Nagini module: a manifest of adversarial cases the runner
(swebench_nagini.pbt) executes. Each SPEC_TEST is a FULL model.py variant built
by region-surgery (editing ONLY text inside the # impl-start / # impl-end block),
so the frozen spec is never touched and `same_spec(base, variant)` holds for
every case. Spec cases are checked by Nagini verify on the host; expect="verify"
passes iff (same_spec AND verifies), expect="reject" passes iff (same_spec AND
does NOT verify).

DEFENDED SURFACE (what this spec actually pins):

  output_field_identity(sel: Selection) -> int
    deep model of Query.output_field's `len(self.select) == 1` branch
    (gold: `select = self.select[0]; return getattr(select, 'target', None)
    or select.field`). `sel` carries two int field identities:
      * sel.source == Col.target, sentinel 0 == "no usable source field"
        (target absent OR falsy);
      * sel.field  == Expression.field/output_field, always usable (!= 0).

    READ-ONLY input: Requires(Acc(sel.source, 1/2) and Acc(sel.field, 1/2)).
    => the FRAME-MUTATION probe is MANDATORY (a rival that WRITES sel.source or
    sel.field to satisfy the postcondition vacuously must be rejected for
    INSUFFICIENT PERMISSION; the half-permission cannot back a field store).

    LOAD-BEARING postcondition clauses:
      (F1) sel.source == Old(sel.source)        read-only frame
      (F2) sel.field  == Old(sel.field)         read-only frame
      (S1) Implies(sel.source != 0, Result() == sel.source)   prefer source
      (S2) Implies(sel.source == 0, Result() == sel.field)    else field
    S1 is the DISCRIMINATING clause: on a selection whose source is nonzero and
    differs from field, the result MUST be the source. model_prepatch.py
    (`return sel.field`) is exactly the pre-patch bug and FAILS S1 (G-DIFF).

  ORACLE GROUNDEDNESS: the postcondition is grounded entirely in the args
  (sel.source, sel.field, Result()); there is NO @Pure answer-key oracle to
  echo. The "ungrounded-oracle echo" class is therefore N/A (see assessment);
  it is replaced by an honest cheapest-impl positive control (pos-ternary).

  CONTROL-FLOW-EFFECT: output_field_identity is a pure-value int chooser with no
  raise/return/side-effect path (no Exsures, single normal return). That class
  is N/A here (see assessment).

  AXIOMS: meta.json axioms == []; the choose-one-of-two is modelled DEEPLY (no
  @ContractOnly consumed). The deep_model_references entry is an A-reference
  validated out-of-band by axiom_check.py / G-AX (real getattr/or + real
  Query.output_field), which is NOT a PBT obligation. There is no caller-domain
  containment or axiom-soundness obligation in the PBT sense (no consumed
  Requires/Ensures axiom). => AXIOM_TESTS = [].
"""
from pathlib import Path

INSTANCE = "django__django-12663"
FLOAT_ENCODING = None  # meta.json float_encoding is null; behaviour is pure int choice

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the gold impl block (UNIQUE; every replacement keeps the spec verbatim
#      and edits ONLY the executable body between # impl-start / # impl-end) ----
_GOLD_IMPL = (
    "    # impl-start\n"
    "    # select = self.select[0]\n"
    "    # return getattr(select, 'target', None) or select.field\n"
    "    source = sel.source\n"
    "    if source != 0:\n"
    "        return source\n"
    "    return sel.field\n"
    "    # impl-end"
)


def _impl(body):
    """Wrap a new executable body in the impl markers (spec never touched)."""
    return "    # impl-start\n" + body + "\n    # impl-end"


# ===========================================================================
# SPEC TESTS
# ===========================================================================
SPEC_TESTS = [

    # -------------------------------------------------------------------
    # POSITIVE CONTROLS (soundness): structurally-different CORRECT impls
    # must verify; else the postcondition over-constrains (SPEC-TOO-STRONG).
    # No loop/lemma is needed (a 2-branch chooser), so a branch-reorder /
    # ternary / local reshape keeps every proof obligation discharged.
    # -------------------------------------------------------------------
    {
        "id": "pos-reorder-source-zero-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            _impl(
                "    # Branch-reorder: test the fallback (source == 0) FIRST,\n"
                "    # return source otherwise. Same value choice, mirror shape.\n"
                "    if sel.source == 0:\n"
                "        return sel.field\n"
                "    return sel.source"
            ),
        ),
        "rationale": "Choosing field when source==0 and source otherwise is exactly "
                     "the gold choice with the two branches reordered. It must satisfy "
                     "S1 (source!=0 -> Result()==source) and S2 (source==0 -> "
                     "Result()==field) and reads nothing, so the frame clauses hold "
                     "trivially. If a faithful correct impl cannot verify, the "
                     "postcondition is SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-ternary-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            _impl(
                "    # Local-variable reshape: bind both candidates, pick via a\n"
                "    # ternary. Cheapest honest chooser; reads, never writes.\n"
                "    s = sel.source\n"
                "    f = sel.field\n"
                "    chosen = s if s != 0 else f  # type: int\n"
                "    return chosen"
            ),
        ),
        "rationale": "A ternary over locals bound from the two read-only fields is the "
                     "cheapest correct chooser and is grounded entirely in the inputs "
                     "(no oracle to echo). It must verify against S1/S2; a failure "
                     "would be SPEC-TOO-STRONG. Doubles as the honest positive control "
                     "standing in for the N/A ungrounded-oracle class.",
    },

    # -------------------------------------------------------------------
    # ADMISSIBILITY: the precondition must accept a normal F2P-shaped input.
    # A new module-level def would change the spec view and break same_spec,
    # so the witness is injected INSIDE the impl region (elided from the spec
    # view): construct a concrete Selection (its __init__ Ensures give
    # source==0, field==1, i.e. full Acc on both fields), and Assert the
    # function's Requires is establishable for it (Acc at 1/2 and field != 0).
    # The real impl then runs unchanged over the actual `sel`. If the Requires
    # could not be established for this legitimate input the Assert fails =>
    # PRECOND-TOO-STRONG.
    # -------------------------------------------------------------------
    {
        "id": "admiss-fresh-selection",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            _impl(
                "    # --- admissibility witness for an F2P-shaped input (elided from\n"
                "    #     the spec view) ---\n"
                "    adm = Selection()\n"
                "    # The constructor Ensures full Acc(adm.source) and Acc(adm.field);\n"
                "    # the function's Requires asks only Acc(.., 1/2) and field != 0,\n"
                "    # which is establishable here (adm.field == 1 != 0).\n"
                "    Assert(Acc(adm.source, 1 / 2) and Acc(adm.field, 1 / 2))\n"
                "    Assert(adm.field != 0)\n"
                "    # --- end witness; the real impl follows unchanged ---\n"
                "    source = sel.source\n"
                "    if source != 0:\n"
                "        return source\n"
                "    return sel.field"
            ),
        ),
        "rationale": "A freshly constructed Selection (source==0, field==1) is a normal "
                     "F2P-shaped selected item; the Requires (Acc at 1/2 + field != 0) "
                     "is establishable for it, witnessed by the two asserts. If this "
                     "cannot verify, the precondition rejects a legitimate input "
                     "(PRECOND-TOO-STRONG).",
    },

    # -------------------------------------------------------------------
    # FRAME-MUTATION (MANDATORY — sel.source/sel.field are read-only at
    # Acc(.., 1/2)). A rival that WRITES a field to satisfy a postcondition
    # clause vacuously must be REJECTED for INSUFFICIENT PERMISSION: a half-
    # permission to a field cannot back a store. The gold spec (incl. the
    # frame clauses F1/F2) is kept verbatim so the rejection is attributable
    # to the write, not a proof gap.
    # -------------------------------------------------------------------
    {
        "id": "frame-mutate-source-to-field",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            _impl(
                "    # WRONG: overwrite the read-only source to the field, then return\n"
                "    # field unconditionally. This would make S1 (source!=0 ->\n"
                "    # Result()==source) hold vacuously by collapsing source onto field.\n"
                "    sel.source = sel.field\n"
                "    return sel.field"
            ),
        ),
        "refinement": "The faithful real patch — assigning self.select[0].target = "
                      "select.field inside Query.output_field — mutates the shared Col "
                      "of a live query, destroying the relation-aware target every "
                      "downstream consumer reads. The subquery-by-lazy comparison would "
                      "then resolve against the bare resolved field, the SimpleLazyObject "
                      "could not be coerced via the related field, and "
                      "test_subquery_filter_by_lazy would still FAIL (plus it corrupts "
                      "every other reader of that Col).",
        "rationale": "Rejected by the permission system: sel.source is held at "
                     "Acc(sel.source, 1/2); a field store `sel.source = ...` needs the "
                     "FULL permission, so the write is INSUFFICIENT-PERMISSION (and "
                     "would also break frame clause F1 sel.source==Old(sel.source)). If "
                     "it verified, the read-only frame is unguarded (SPEC-TOO-WEAK).",
    },
    {
        "id": "frame-mutate-field-to-source",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            _impl(
                "    # WRONG: when a usable source exists, overwrite the read-only field\n"
                "    # with it and return field — satisfying S1 by clobbering field\n"
                "    # rather than choosing source.\n"
                "    source = sel.source\n"
                "    if source != 0:\n"
                "        sel.field = source\n"
                "        return sel.field\n"
                "    return sel.field"
            ),
        ),
        "refinement": "Writing self.select[0].field (the resolved output_field) to the "
                      "target inside the property mutates a shared Col attribute; later "
                      "annotation/output-field reads would observe the clobbered field, "
                      "corrupting unrelated query compilation. Such a patch does not "
                      "faithfully choose the target and would not resolve the F2P while "
                      "keeping the P2P suite green.",
        "rationale": "Rejected by the permission system: sel.field is held at "
                     "Acc(sel.field, 1/2); the store `sel.field = source` needs FULL "
                     "permission => INSUFFICIENT-PERMISSION (also violates frame clause "
                     "F2 sel.field==Old(sel.field)). A verify here would mean the "
                     "read-only frame is unguarded (SPEC-TOO-WEAK).",
    },

    # -------------------------------------------------------------------
    # PARTIAL-DOMAIN (uniqueness): rivals correct on a sub-domain of the
    # F2P/P2P input space but diverging on the discriminating sub-domain.
    # -------------------------------------------------------------------
    {
        "id": "weak-always-field-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            _impl(
                "    # WRONG (pre-patch): always return the resolved field, ignoring a\n"
                "    # usable source. Correct only on the source==0 sub-domain.\n"
                "    return sel.field"
            ),
        ),
        "refinement": "This is model_prepatch.py verbatim — the original `return "
                      "self.select[0].field`. On a Col with an explicit output_field "
                      "differing from target (the issue's nested-subquery case), it "
                      "returns the relation-unaware resolved field, so the "
                      "SimpleLazyObject RHS cannot be coerced via the related field. "
                      "test_subquery_filter_by_lazy FAILS (confirmed by G-DIFF).",
        "rationale": "Rejected by S1 Implies(sel.source != 0, Result() == sel.source): "
                     "for a selection with source != 0 and source != field it returns "
                     "field != source. Correct on source==0 (S2) but wrong on the "
                     "discriminating sub-domain. SPEC-TOO-WEAK if it verified.",
    },
    {
        "id": "weak-always-source",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            _impl(
                "    # WRONG: always return source, even when it is the unusable\n"
                "    # sentinel 0. Correct on the source!=0 sub-domain only.\n"
                "    return sel.source"
            ),
        ),
        "refinement": "An impl that returns Col.target even when there is no usable "
                      "target (`return getattr(select, 'target', None)` with no `or "
                      "select.field` fallback) returns None/a falsy value for a non-Col "
                      "or target-less selection. Query.output_field would then yield a "
                      "non-field object, breaking single-selection queries whose item "
                      "carries no usable target — the P2P suite over plain expressions "
                      "would FAIL (the fallback is load-bearing).",
        "rationale": "Rejected by S2 Implies(sel.source == 0, Result() == sel.field): "
                     "for source==0 it returns 0, but field != 0 is required by the "
                     "precondition, so Result()==field is violated. SPEC-TOO-WEAK if it "
                     "verified.",
    },
    {
        "id": "weak-equal-only-pin",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            _impl(
                "    # WRONG value-proxy: return source only when it ALREADY equals\n"
                "    # field; otherwise fall back to field. Correct on the coinciding\n"
                "    # sub-domain (Col built without an explicit output_field, where\n"
                "    # target == field) but it DROPS the discriminating case where\n"
                "    # source != 0 and source != field.\n"
                "    source = sel.source\n"
                "    if source != 0 and source == sel.field:\n"
                "        return source\n"
                "    return sel.field"
            ),
        ),
        "refinement": "Returning the target only when it already equals the resolved "
                      "field is a no-op disguised as a fix: it preserves the gold answer "
                      "exactly on the coinciding case (Col without an explicit "
                      "output_field) but reverts to the bug on the discriminating "
                      "nested-subquery Col where target != output_field. The "
                      "SimpleLazyObject comparison still hits the resolved field, so "
                      "test_subquery_filter_by_lazy FAILS.",
        "rationale": "Rejected by S1 Implies(sel.source != 0, Result() == sel.source): "
                     "on the discriminating input source != 0 and source != field, the "
                     "impl returns field != source. This is the value-proxy that drops "
                     "exactly the disagreeing sub-domain S1 pins. SPEC-TOO-WEAK if it "
                     "verified.",
    },
]

# ===========================================================================
# AXIOM TESTS — none.
# meta.json: axioms == []. The single-selection output-field choice is modelled
# DEEPLY (the `if source != 0: return source; return sel.field` skeleton spells
# out `getattr(select, 'target', None) or select.field`); there is no
# @ContractOnly axiom the Nagini proof consumes, hence no axiom-soundness or
# caller-domain containment obligation in the PBT sense. The lone
# deep_model_references entry is an A-reference validated out-of-band by
# axiom_check.py / G-AX (the pure getattr/or truthy semantics over 20000 fuzz
# cases + the real post-patch Query.output_field on single-Col selections), and
# that A-reference check is a separate gate, not a PBT axiom probe.
# ===========================================================================
AXIOM_TESTS = []
