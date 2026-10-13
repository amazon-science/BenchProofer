# properties.py — PBT falsification battery for django__django-12193.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# (axioms/pure/pre/post-conditions regions untouched) and swaps ONLY text inside
# the # impl-start/# impl-end region; the runner checks each with Nagini verify
# + markers.same_spec. AXIOM_TESTS entries are self-contained probes run in the
# instance Docker image.
#
# Defended surface (read from model.py + refinement.md + mapping.md + meta.json):
#   prepare_attrs(value: int, attrs: Dict[int, bool]) -> Dict[int, bool]
#   models CheckboxInput.get_context's attribute-mapping construction. It must
#   return a FRESH mapping (the gold fix: stop mutating the caller's dict). Two
#   pinned observations, gated by the GROUNDED predicate counts_as_selected(value)
#   (= not one of the three empty sentinels — a deep @Pure function of `value`,
#   NOT an opaque oracle, so there is no wrong echo to build; see 'assessment'):
#     SELECTED     => Result()[attr_selected()] == True, every OTHER caller key
#                     carried through, NO spurious key beyond attr_selected().
#     NOT-SELECTED => Result() holds EXACTLY the caller's keys/values (both
#                     directions); no selection attribute forced on.
#   plus, in BOTH branches, the load-bearing frame guarantees:
#     Acc(dict_pred(attrs), 1/2)  Required AND Ensured  => attrs is READ-ONLY
#     Ensures(Result() is not attrs)                    => the prepared map is fresh
#
#   The #1 defended property is no-mutation: `attrs` is held at HALF permission
#   (Acc(dict_pred(attrs), 1/2)), so ANY write to it is unprovable (insufficient
#   permission). This is the exact bug (model_prepatch.py writes
#   attrs[attr_selected()]=True and fails) and the heart of the gold patch.
#
#   The two callees are @ContractOnly A-consumed axioms over UNCHANGED Python
#   language primitives:
#     mapping_with(base,key,flag) == {**base, key: flag}   (the gold merge)
#     mapping_copy(base)          == {**base}              (the pass-through copy)
#   both validated against real CPython by axiom_check.py / G-AX.
#
# F2P: test_get_context_does_not_mutate_attrs (CheckboxInput) — attrs={'checked':
#      False}; after get_context('name', True, attrs) the caller's
#      attrs['checked'] must STILL be False (no mutation).
#   +  test_checkbox_get_context_attrs (SplitArrayWidget, values [True, False]) —
#      subwidget attrs must be [{'checked': True}, {}]: the first widget selected,
#      the second NOT inheriting checked from a shared/mutated mapping.

from pathlib import Path

INSTANCE = "django__django-12193"
FLOAT_ENCODING = None  # meta.json float_encoding == null


_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The frozen impl body (model.py lines 172-177, BETWEEN the markers). Every
# rival edits ONLY this block, so spec_view (and hence markers.same_spec) is
# preserved.
# ---------------------------------------------------------------------------
_BODY = """    if counts_as_selected(value):
        # Fresh mapping: every caller attribute, with the selection flag forced
        # on. The caller's mapping is read, never written.
        return mapping_with(attrs, attr_selected(), True)
    # Pass-through: a fresh copy of exactly the caller's attributes.
    return mapping_copy(attrs)"""


# ===========================================================================
# POSITIVE CONTROL (soundness) — expect "verify"
# ===========================================================================

# (S1) Branch-reorder: handle the NOT-selected case first, fall through to the
# selected merge last. Semantically identical, no loop / no fold, so no
# auto-undischargeable lemma is needed (directive-3 safe). It calls exactly the
# same two axiomatized callees on the same arguments; only the top-level branch
# order changes. If this CANNOT verify, the postcondition is over-fit to the
# gold branch order => SPEC-TOO-STRONG.
_POS_REORDER = _swap(_BASE, _BODY,
    "    if not counts_as_selected(value):\n"
    "        # Pass-through: a fresh copy of exactly the caller's attributes.\n"
    "        return mapping_copy(attrs)\n"
    "    # Fresh mapping: every caller attribute, with the selection flag on.\n"
    "    return mapping_with(attrs, attr_selected(), True)")


# (S2) Local-variable reshape: stage the prepared mapping through a typed local
# in each branch instead of returning inline. Identical behaviour and identical
# callees; confirms the spec admits a different local-binding shape, not just the
# gold spelling. If it fails to verify => SPEC-TOO-STRONG (over-fit to the
# inline-return form).
_POS_LOCAL = _swap(_BASE, _BODY,
    "    if counts_as_selected(value):\n"
    "        prepared = mapping_with(attrs, attr_selected(), True)  # type: Dict[int, bool]\n"
    "        return prepared\n"
    "    passthrough = mapping_copy(attrs)  # type: Dict[int, bool]\n"
    "    return passthrough")


# ===========================================================================
# ADMISSIBILITY — expect "verify"
# ===========================================================================

# An F2P-shaped input probe: the F2P scenario passes a present dict (e.g.
# {'checked': False}) with a selected value. A separate top-level helper would
# break same_spec (spec_view elides only the impl region), so the probe lives
# INSIDE the impl: build a fresh full-permission dict and establish, in the
# verifier, that it satisfies prepare_attrs' precondition -- then run the gold
# body unchanged on the real `attrs`. If a normal present-dict input cannot
# establish Requires(Acc(dict_pred(attrs), 1/2)) => PRECOND-TOO-STRONG.
#
# WHY THIS PROBE IS ASSERTION-SHAPED AND NOT A SELF-CALL. It used to be
# `_self = prepare_attrs(value, probe)`. That spelling is unavailable once the
# spec carries a termination obligation, and NOT because the obligation is too
# strong: `prepare_attrs` Requires MustTerminate(10), and Nagini discharges a
# call only when the callee's level is STRICTLY BELOW the caller's. For a
# self-call caller and callee are the same method at the same level, so the
# side condition is 10 < 10 -- unsatisfiable at EVERY level, since raising the
# annotation raises both sides together. An UNGUARDED self-call on every input
# is simply non-terminating recursion, and the old probe only ever verified
# because the pre-obligation spec asked nothing of termination (measured: it
# VERIFIES with the Requires(MustTerminate(10)) line removed). That divergence
# is preserved as a first-class reject-lane case below (W8) rather than
# discarded; here the same admissibility question is asked in the form that
# survives it -- the precondition's own predicate is asserted of the F2P-shaped
# dict, and the dict is then handed to an obligated callee, which shows the
# level leaves real room beneath it (mapping_with is level 2 < 10).
# Non-vacuity was checked: `Assert(False)` in this region FAILS, so the probe
# region is reachable and the asserts are discharged, not skipped.
_ADMISS = _swap(_BASE, "    # impl-start",
    "    # impl-start\n"
    "    # ADMISSIBILITY PROBE: a fresh present dict (the F2P shape: a caller\n"
    "    # mapping already holding the selection key) establishes the Requires\n"
    "    # predicate that prepare_attrs' precondition demands of a caller.\n"
    "    probe = {attr_selected(): False}  # type: Dict[int, bool]\n"
    "    Assert(attr_selected() in probe)\n"
    "    Assert(Acc(dict_pred(probe), 1 / 2))\n"
    "    _probe = mapping_with(probe, attr_selected(), True)  "
    "# type: Dict[int, bool]")


# ===========================================================================
# UNIQUENESS / FRAME / PARTIAL-DOMAIN RIVALS — expect "reject"
# ===========================================================================

# (W1) FRAME-MUTATION (MANDATORY — the #1 weakness class and the literal bug).
# On the selected branch, write the selection flag into the CALLER's own mapping
# in place and hand that same object on — exactly the pre-patch behaviour the
# gold fix removes. `attrs` is held at HALF permission (Acc(dict_pred(attrs),
# 1/2)), so the WRITE `attrs[attr_selected()] = True` is unprovable: the rival
# fails for INSUFFICIENT PERMISSION (it would also violate Result() is not attrs,
# but the permission failure fires first). Gold invariants kept verbatim so the
# rejection is attributable to the write.
# refinement: this is model_prepatch.py — the real pre-patch get_context
# (`attrs['checked'] = True; return ... attrs`). The F2P
# test_get_context_does_not_mutate_attrs asserts attrs['checked'] stays False
# AFTER the call, and the SplitArray F2P expects the 2nd widget's attrs == {};
# the mutating patch leaves attrs['checked']==True (and the shared map polluted)
# — it does NOT resolve (it IS the bug).
# rejection source: the read-only HALF permission Acc(dict_pred(attrs), 1/2) on
# the input (insufficient permission for the write).
_W1_FRAME = _swap(_BASE, _BODY,
    "    if counts_as_selected(value):\n"
    "        # FRAME-MUTATION RIVAL (the pre-patch bug): write the selection flag\n"
    "        # into the CALLER's mapping in place and return that same object.\n"
    "        # attrs is half-permission -> this write is insufficient-permission.\n"
    "        attrs[attr_selected()] = True\n"
    "        return attrs\n"
    "    return mapping_copy(attrs)")


# (W2) FRAME-MUTATION, write-then-return-fresh flavour. Mutate the caller's
# mapping in place but then return a FRESH copy (so Result() is not attrs holds).
# Isolates the rejection to the WRITE alone: the only illegal step is the in-place
# `attrs[attr_selected()] = True`, still unprovable under the half-permission
# input. A byte-fuzzer never thinks to mutate a read-only input.
# refinement: a real patch that did `attrs['checked'] = True` (polluting the
# caller's shared dict) and then ALSO returned a fresh dict would still fail the
# F2P test_get_context_does_not_mutate_attrs (the caller's attrs['checked'] is
# now True) and the SplitArray test (later widgets inherit checked) — NOT resolve.
# rejection source: insufficient permission for the write (Acc(.,1/2) on attrs);
# the no-mutation guarantee. Returning fresh does not license the write.
_W2_FRAME_FRESH = _swap(_BASE, _BODY,
    "    if counts_as_selected(value):\n"
    "        # FRAME-MUTATION RIVAL #2: pollute the caller's mapping, THEN return\n"
    "        # a fresh one. The write itself is insufficient-permission.\n"
    "        attrs[attr_selected()] = True\n"
    "        return mapping_with(attrs, attr_selected(), True)\n"
    "    return mapping_copy(attrs)")


# (W3) PARTIAL-DOMAIN — always-selected. Force the selection flag on for EVERY
# value (drop the not-selected branch). Correct on the selected sub-domain;
# diverges on the not-selected sub-domain (value in {False, None, ''}), where the
# spec pins Result() to hold EXACTLY the caller's keys with NO selection forced.
# refinement: a real patch that unconditionally did `attrs = {**(attrs or {}),
# 'checked': True}` (dropping the `if self.check_test(value)` guard) would render
# a checkbox checked for a False/None/'' value. P2P test_render_false /
# test_render_none / test_render_empty expect the rendered checkbox WITHOUT
# `checked`, and the SplitArray F2P expects the second subwidget attrs == {} (not
# {'checked': True}) — it would FAIL them and NOT resolve.
# rejection source: postcondition (2) — Implies(not counts_as_selected(value),
# Forall k: k in Result() <=> k in attrs ...): a forced-on attr_selected() that
# attrs lacks violates the both-directions equality on the not-selected branch.
_W3_ALWAYS_SEL = _swap(_BASE, _BODY,
    "    # PARTIAL-DOMAIN RIVAL: force the selection flag on for EVERY value,\n"
    "    # ignoring the not-selected sentinels. Correct when selected; wrong on\n"
    "    # the not-selected sub-domain (must carry NO selection attribute).\n"
    "    return mapping_with(attrs, attr_selected(), True)")


# (W4) PARTIAL-DOMAIN — never-selected. Always pass through a plain copy (drop
# the selected branch). Correct on the not-selected sub-domain; diverges on the
# selected sub-domain, where the spec pins attr_selected() present with True.
# Only WRONG when attrs does not already carry attr_selected()==True (the F2P
# input {'checked': False} and the empty {} both fail it).
# refinement: a real patch that dropped the merge entirely (`return
# super().get_context(name, value, attrs)` always) would never set 'checked';
# P2P test_render_true / test_render_int / test_render_value (selected values)
# expect a CHECKED checkbox and the SplitArray F2P expects the first subwidget
# attrs == {'checked': True} — it would FAIL them and NOT resolve.
# rejection source: postcondition (1) — Implies(counts_as_selected(value),
# attr_selected() in Result() and Result()[attr_selected()] == True): a plain
# copy of attrs={..., attr_selected(): False / absent} cannot prove it.
_W4_NEVER_SEL = _swap(_BASE, _BODY,
    "    # PARTIAL-DOMAIN RIVAL: never set the selection flag; just copy attrs.\n"
    "    # Correct on the not-selected sub-domain; wrong on selected values.\n"
    "    return mapping_copy(attrs)")


# (W5) WRONG-FLAG. On the selected branch, set the selection attribute to False
# instead of True. Fresh, no mutation, every other key carried — but the pinned
# value is wrong.
# refinement: a real patch writing `{**(attrs or {}), 'checked': False}` for a
# selected value would render an UNCHECKED checkbox for a truthy value; P2P
# test_render_true / test_render_value expect `checked` present and the SplitArray
# F2P expects the first subwidget attrs == {'checked': True} — it would FAIL and
# NOT resolve.
# rejection source: postcondition (1) clause Result()[attr_selected()] == True
# (the flag value is pinned to True on the selected branch).
_W5_WRONG_FLAG = _swap(_BASE, _BODY,
    "    if counts_as_selected(value):\n"
    "        # WRONG-FLAG RIVAL: selection attribute set to False, not True.\n"
    "        return mapping_with(attrs, attr_selected(), False)\n"
    "    return mapping_copy(attrs)")


# (W6) SPURIOUS-KEY. On the selected branch, build the correct merge then add a
# SECOND, unrelated key (val_false() == -1, a distinct attribute-name token). The
# prepared mapping then carries a key the caller never had and which is not
# attr_selected() — violating the "no key outside attrs ∪ {attr_selected()}"
# clause whenever -1 ∉ attrs.
# refinement: a real patch that injected a stray HTML attribute (e.g.
# `{**(attrs or {}), 'checked': True, 'data-x': True}`) would render an extra
# attribute the rendering step never expected; the SplitArray F2P pins the first
# subwidget attrs EXACTLY to {'checked': True} (== comparison) — an extra key
# makes the dict unequal and the test FAILS; it would NOT resolve.
# rejection source: postcondition (1) clause Forall k: k in Result() => (k ==
# attr_selected() or k in attrs) — the spurious key -1 (∉ attrs) breaks it.
_W6_SPURIOUS = _swap(_BASE, _BODY,
    "    if counts_as_selected(value):\n"
    "        # SPURIOUS-KEY RIVAL: add an extra attribute (val_false() == -1)\n"
    "        # beyond attr_selected(); not present in attrs in general.\n"
    "        merged = mapping_with(attrs, attr_selected(), True)  # type: Dict[int, bool]\n"
    "        return mapping_with(merged, val_false(), True)\n"
    "    return mapping_copy(attrs)")


# (W7) DROP-A-KEY on the not-selected branch (supporting near-miss). On the
# not-selected branch, instead of passing every caller attribute through, force
# the selection key on (mapping_with) — i.e. on a NOT-selected value the prepared
# mapping gains attr_selected()==True that the caller did not have. This is the
# both-directions failure of postcondition (2) from the other side: an extra key
# is introduced when none should be.
# refinement: a real patch that built `{**(attrs or {}), 'checked': True}` even
# in the else branch (e.g. by indenting the merge wrong) marks unchecked widgets
# checked — the SplitArray F2P expects the second subwidget attrs == {} (empty),
# but it would be {'checked': True}; FAIL, NOT resolve.
# rejection source: postcondition (2) clause Forall k: k in Result() => k in
# attrs (the prepared map may not introduce attr_selected() when not selected).
_W7_ELSE_SETS = _swap(_BASE, _BODY,
    "    if counts_as_selected(value):\n"
    "        return mapping_with(attrs, attr_selected(), True)\n"
    "    # DROP/EXTRA RIVAL: even when NOT selected, force the selection key on.\n"
    "    return mapping_with(attrs, attr_selected(), True)")


# (W8) NON-TERMINATION. Prefix the gold body with an UNGUARDED self-call on the
# same `value`: `prepare_attrs` re-enters itself on every input before reaching
# any return, so no call ever returns. Every postcondition is then claimed only
# of runs that REACH the return, of which there are none -- the rival satisfies
# all of them vacuously. This case is the direct descendant of the old
# `admiss-present-dict` self-call probe, which sat in the ACCEPT lane; the
# obligation is what moved it, and the move is a strictly stronger claim than
# the one it replaces (that the spec REJECTS a diverging impl, not merely that
# it tolerates a probe).
# refinement: an infinitely-recursing get_context returns no context at all --
# every CheckboxInput test (the F2P test_get_context_does_not_mutate_attrs and
# the SplitArray F2P included) hangs or blows the stack instead of asserting;
# it resolves NOTHING.
# rejection source: the TERMINATION obligation Requires(MustTerminate(10)) on
# prepare_attrs. Nagini discharges a call only when the callee's level is
# STRICTLY BELOW the caller's; a self-call puts the same method at the same
# level on both sides, so the side condition is 10 < 10 and fails as
# "Obligation leak check failed. Callee prepare_attrs might not take all
# unsatisfied obligations from the caller." No level makes it provable --
# raising the annotation raises both sides together, which is exactly why
# unguarded recursion is unprovable rather than under-annotated.
# MEASURED: with the Requires(MustTerminate(10)) line deleted this rival
# VERIFIES. It is the concrete partial-correctness hole the obligation closes.
_W8_NONTERMINATION = _swap(_BASE, "    # impl-start",
    "    # impl-start\n"
    "    # NON-TERMINATION RIVAL: recurse on every input before any return, so\n"
    "    # no call ever returns and every Ensures holds vacuously.\n"
    "    _diverge = prepare_attrs(value, attrs)  # type: Dict[int, bool]")


SPEC_TESTS = [
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": "structurally-different CORRECT impl (not-selected branch "
        "handled first, selected merge last); same axiomatized callees, only the "
        "branch order changes — must verify, else SPEC-TOO-STRONG. Branch reorder "
        "only (no loop/fold, directive-3 safe).",
    },
    {
        "id": "pos-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LOCAL,
        "rationale": "CORRECT impl staging each prepared mapping through a typed "
        "local instead of returning inline (local-variable reshape). Same "
        "behaviour and callees; confirms the spec is not over-fit to the inline "
        "return spelling. If it fails => SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-present-dict",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "a positive control on an F2P-shaped input (a fresh present "
        "dict {attr_selected(): False}): the Requires(Acc(dict_pred(attrs), 1/2)) "
        "must admit a normal caller mapping, else PRECOND-TOO-STRONG. Full "
        "permission on the probe grants the half permission the precondition "
        "needs, and handing the probe to the obligated callee mapping_with "
        "(level 2 < 10) shows the termination level leaves real room beneath it. "
        "Asserted rather than self-called: a self-call needs the callee's level "
        "STRICTLY BELOW the caller's, which is 10 < 10 for the same method and so "
        "is unsatisfiable at every level -- unguarded self-recursion does not "
        "terminate, and it is now carried as the reject-lane case "
        "'nonterminating-self-recursion' instead of hiding in this lane. "
        "Non-vacuity confirmed: Assert(False) here FAILS.",
    },
    {
        "id": "frame-mutate-return-self",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W1_FRAME,
        "refinement": "this is model_prepatch.py / the real pre-patch get_context "
        "(`attrs['checked'] = True; return ... attrs`). F2P "
        "test_get_context_does_not_mutate_attrs asserts attrs['checked'] stays "
        "False after the call; the SplitArray F2P expects the 2nd subwidget attrs "
        "== {}. The in-place mutation leaves attrs['checked']==True and pollutes a "
        "shared mapping — it does NOT resolve (it IS the bug the patch fixes).",
        "rationale": "FRAME-MUTATION (MANDATORY). Rejected by the read-only HALF "
        "permission Acc(dict_pred(attrs), 1/2) on the input: the write "
        "attrs[attr_selected()]=True is unprovable for INSUFFICIENT PERMISSION. "
        "(It would also violate Result() is not attrs, but the permission failure "
        "fires first.) Gold invariants kept verbatim so the rejection is "
        "attributable to the write.",
    },
    {
        "id": "frame-mutate-return-fresh",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W2_FRAME_FRESH,
        "refinement": "a real patch that wrote `attrs['checked'] = True` (polluting "
        "the caller's shared dict) and ALSO returned a fresh mapping would still "
        "fail F2P test_get_context_does_not_mutate_attrs (caller's attrs['checked'] "
        "is now True) and the SplitArray F2P (later widgets inherit checked) — NOT "
        "resolve.",
        "rationale": "FRAME-MUTATION isolated to the WRITE: the returned object is "
        "fresh (Result() is not attrs holds), so the ONLY illegal step is the "
        "in-place attrs[attr_selected()]=True — still insufficient permission under "
        "the half-permission input. Returning fresh does not license the write.",
    },
    {
        "id": "always-selected",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W3_ALWAYS_SEL,
        "refinement": "a real patch that unconditionally did `attrs = {**(attrs or "
        "{}), 'checked': True}` (dropping the check_test guard) renders a checkbox "
        "checked for a False/None/'' value. P2P test_render_false / test_render_none "
        "/ test_render_empty expect NO `checked`, and the SplitArray F2P expects the "
        "2nd subwidget attrs == {} — it FAILS them and does NOT resolve.",
        "rationale": "PARTIAL-DOMAIN (not-selected sub-domain). Rejected by "
        "postcondition (2): Implies(not counts_as_selected(value), Forall k: k in "
        "Result() <=> k in attrs ...) — a forced-on attr_selected() that attrs "
        "lacks breaks the both-directions key equality.",
    },
    {
        "id": "never-selected",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W4_NEVER_SEL,
        "refinement": "a real patch that dropped the merge entirely (always `return "
        "super().get_context(name, value, attrs)`) never sets 'checked'; P2P "
        "test_render_true / test_render_int / test_render_value (selected values) "
        "expect a CHECKED checkbox and the SplitArray F2P expects the 1st subwidget "
        "attrs == {'checked': True} — it FAILS them and does NOT resolve.",
        "rationale": "PARTIAL-DOMAIN (selected sub-domain). Rejected by "
        "postcondition (1): Implies(counts_as_selected(value), attr_selected() in "
        "Result() and Result()[attr_selected()] == True) — a plain copy of attrs "
        "(which need not carry attr_selected()==True) cannot prove it.",
    },
    {
        "id": "wrong-flag-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W5_WRONG_FLAG,
        "refinement": "a real patch writing `{**(attrs or {}), 'checked': False}` "
        "for a selected value renders an UNCHECKED checkbox for a truthy value; P2P "
        "test_render_true / test_render_value expect `checked` and the SplitArray "
        "F2P expects the 1st subwidget attrs == {'checked': True} — it FAILS and "
        "does NOT resolve.",
        "rationale": "value-level. Rejected by postcondition (1) clause "
        "Result()[attr_selected()] == True — the flag value is pinned to True on "
        "the selected branch; False cannot satisfy it.",
    },
    {
        "id": "spurious-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W6_SPURIOUS,
        "refinement": "a real patch injecting a stray HTML attribute (e.g. "
        "`{**(attrs or {}), 'checked': True, 'data-x': True}`) renders an extra "
        "attribute the rendering step never expected; the SplitArray F2P pins the "
        "1st subwidget attrs EXACTLY to {'checked': True} (== comparison) — an "
        "extra key makes the dicts unequal and the test FAILS; it does NOT resolve.",
        "rationale": "Rejected by postcondition (1) clause Forall k: k in Result() "
        "=> (k == attr_selected() or k in attrs): the injected key val_false() "
        "(== -1), absent from a general attrs, is a forbidden spurious key.",
    },
    {
        "id": "else-sets-checked",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W7_ELSE_SETS,
        "refinement": "a real patch that built `{**(attrs or {}), 'checked': True}` "
        "even in the not-selected branch (e.g. mis-indented merge) marks unchecked "
        "widgets checked — the SplitArray F2P expects the 2nd subwidget attrs == {} "
        "but it would be {'checked': True}; FAIL, does NOT resolve.",
        "rationale": "PARTIAL-DOMAIN (supporting). Rejected by postcondition (2) "
        "clause Forall k: k in Result() => k in attrs — the prepared map may not "
        "introduce attr_selected() when the value is not selected.",
    },
    {
        "id": "nonterminating-self-recursion",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W8_NONTERMINATION,
        "refinement": "an infinitely-recursing get_context never returns a context: "
        "the F2P test_get_context_does_not_mutate_attrs and the SplitArray F2P both "
        "hang (or blow the stack) instead of asserting. It resolves NOTHING — a "
        "widget that never renders is not a fixed widget.",
        "rationale": "NON-TERMINATION / VACUOUS-POSTCONDITION. This rival DIVERGES: "
        "it re-enters prepare_attrs on every input before reaching any return, so "
        "every Ensures is claimed only of runs that reach the return — of which "
        "there are none — and all of them hold vacuously. It is rejected by the "
        "TERMINATION obligation Requires(MustTerminate(10)): Nagini discharges a "
        "call only when the callee's level is STRICTLY BELOW the caller's, and a "
        "self-call puts the same method at the same level on both sides (10 < 10), "
        "so it fails 'Obligation leak check failed. Callee prepare_attrs might not "
        "take all unsatisfied obligations from the caller.' No level repairs it — "
        "raising the annotation raises both sides together. MEASURED: with that one "
        "Requires line deleted this rival VERIFIES, so this case is the concrete "
        "partial-correctness hole the obligation closes, and it is the reason the "
        "admissibility probe above is assertion-shaped rather than a self-call.",
    },
]


# ===========================================================================
# AXIOM LANE — mapping_with / mapping_copy are @ContractOnly A-consumed axioms
# over UNCHANGED Python language primitives ({**base, key: flag} and {**base}).
# Probes execute the REAL primitive (per directive 4 — CALL it, never scrape
# source) and assert every Ensures clause / containment property. They import
# only stdlib (the merge/copy are language primitives — no repo import needed),
# open nothing on disk, and exit 0 iff the obligation holds. apply_gold=True
# because the merge is the post-gold construction (harmless for a pure
# primitive). The host-side axiom_check.py logic is mirrored inline (directive 6:
# nothing of the bundle is mounted in-container).
# ===========================================================================

_PROBE_SOUND_WITH = r'''
import random, sys

def real_mapping_with(base, key, flag):
    return {**base, key: flag}   # the EXACT gold construction

def check(base, key, flag):
    snap = dict(base)
    res = real_mapping_with(base, key, flag)
    assert base == snap, "AXIOM-UNSOUND mapping_with: base mutated %r -> %r" % (snap, base)
    assert res is not base, "AXIOM-UNSOUND mapping_with: result IS base (not fresh)"
    assert res is not None, "AXIOM-UNSOUND mapping_with: result is None"
    assert key in res and res[key] == flag, \
        "AXIOM-UNSOUND mapping_with: key %r not == %r in %r" % (key, flag, res)
    for k, v in snap.items():
        if k != key:
            assert k in res and res[k] == v, \
                "AXIOM-UNSOUND mapping_with: other base key %r=%r lost in %r" % (k, v, res)
    for k in res:
        assert k == key or k in snap, \
            "AXIOM-UNSOUND mapping_with: spurious key %r in %r" % (k, res)

# Boundary bases: empty (None-coalesced), the F2P {'checked': False}, unrelated
# attrs, the selection key already present (both flags), the SplitArray shared {}.
for base in [{}, {"checked": False}, {"checked": True},
             {"id": "x", "class": "y"}, {"id": "x", "checked": False},
             {"a": 1, "b": 2, "c": 3}]:
    check(base, "checked", True)
# integer-keyed carrier (the model's Dict[int, bool]; 0 == attr_selected()).
for base in [{}, {0: False}, {0: True}, {1: True, 2: False}, {0: False, 5: True}]:
    check(base, 0, True)
# SplitArray scenario: one shared base, values [True, False] -> [{checked}, {}].
shared = {}
sub0 = real_mapping_with(shared, "checked", True)
assert shared == {}, "AXIOM-UNSOUND: SplitArray shared base mutated: %r" % shared
assert sub0 == {"checked": True}, "AXIOM-UNSOUND: SplitArray sub0 wrong: %r" % sub0
# Fuzz: boundary + sentinel keys/values, integer carrier.
rng = random.Random(12193)
for _ in range(20000):
    n = rng.randint(0, 8)
    base = {rng.randint(-3, 12): bool(rng.getrandbits(1)) for _ in range(n)}
    check(base, rng.randint(-3, 12), bool(rng.getrandbits(1)))
print("OK mapping_with sound: fresh, base unmutated, key set, others carried, "
      "no spurious key - over boundary + SplitArray + integer carrier + 20000 fuzz")
sys.exit(0)
'''

_PROBE_SOUND_COPY = r'''
import random, sys

def real_mapping_copy(base):
    return {**base}   # the EXACT pass-through copy

def check(base):
    snap = dict(base)
    res = real_mapping_copy(base)
    assert base == snap, "AXIOM-UNSOUND mapping_copy: base mutated %r -> %r" % (snap, base)
    assert res is not base, "AXIOM-UNSOUND mapping_copy: result IS base (not fresh)"
    assert res is not None, "AXIOM-UNSOUND mapping_copy: result is None"
    for k, v in snap.items():
        assert k in res and res[k] == v, \
            "AXIOM-UNSOUND mapping_copy: base key %r=%r lost in %r" % (k, v, res)
    for k in res:
        assert k in snap and res[k] == snap[k], \
            "AXIOM-UNSOUND mapping_copy: spurious/changed key %r in %r" % (k, res)

for base in [{}, {"checked": False}, {"checked": True},
             {"id": "x", "class": "y"}, {"id": "x", "checked": False},
             {"a": 1, "b": 2, "c": 3}]:
    check(base)
for base in [{}, {0: False}, {0: True}, {1: True, 2: False}, {0: False, 5: True}]:
    check(base)
# SplitArray not-selected pass-through: a fresh empty copy of the shared base.
shared = {}
sub1 = real_mapping_copy(shared)
assert shared == {}, "AXIOM-UNSOUND: SplitArray shared base mutated: %r" % shared
assert sub1 == {}, "AXIOM-UNSOUND: SplitArray sub1 (not-selected) wrong: %r" % sub1
rng = random.Random(20193)
for _ in range(20000):
    n = rng.randint(0, 8)
    base = {rng.randint(-3, 12): bool(rng.getrandbits(1)) for _ in range(n)}
    check(base)
print("OK mapping_copy sound: fresh, base unmutated, same keys/values both "
      "directions - over boundary + SplitArray + integer carrier + 20000 fuzz")
sys.exit(0)
'''

# Containment: enumerate EXACTLY the callee-inputs the MODEL can reach and assert
# each lies in the axiom's Requires domain. The model's only call sites are:
#   mapping_with(attrs, attr_selected(), True)  — base=any dict satisfying
#       dict_pred (the prepare_attrs Requires domain), key = attr_selected() (=0),
#       flag = True (the literal).
#   mapping_copy(attrs)                          — base=any dict satisfying dict_pred.
# Both axioms' Requires is exactly Acc(dict_pred(base), 1/2): the ONLY constraint
# is that base is a valid mapping; key/flag are unconstrained (int / bool by type).
# So EVERY model-reachable base (any Dict[int, bool], from {} to many keys) is in
# the axiom domain, with the single key/flag the model uses. The probe witnesses
# that the real callee accepts and satisfies its Ensures on these reachable inputs
# (a reachable input the axiom did NOT cover would be AXIOM-TOO-WEAK-FOR-CALLER).
_PROBE_COVER = r'''
import random, sys

def real_mapping_with(base, key, flag):
    return {**base, key: flag}
def real_mapping_copy(base):
    return {**base}

# attr_selected() == 0 in the model; the model only ever passes key=0, flag=True
# to mapping_with, and base = the caller's attrs (any dict satisfying dict_pred).
MODEL_KEY = 0
MODEL_FLAG = True

def reachable_in_domain(base):
    # The axiom Requires is dict_pred(base): base must be a valid mapping. The
    # model never constructs base outside dict_pred (it is the prepare_attrs
    # `attrs` parameter, a Dict[int, bool]). Witness: the real callee accepts it
    # and meets its Ensures (so the caller-reachable input is IN the domain).
    assert isinstance(base, dict), "containment: model base not a dict: %r" % (base,)
    r1 = real_mapping_with(base, MODEL_KEY, MODEL_FLAG)
    assert r1 is not base and MODEL_KEY in r1 and r1[MODEL_KEY] is MODEL_FLAG
    r2 = real_mapping_copy(base)
    assert r2 is not base and r2 == base
    return True

# Enumerate the model-reachable bases: empty (the None-coalesced case), the F2P
# present dict, multi-key, the integer carrier, plus randomized dicts. There is
# NO base the model can reach that lies outside dict_pred (any dict is in-domain),
# so containment holds; key/flag are the fixed (0, True) the model uses.
for base in [{}, {0: False}, {0: True}, {1: True}, {0: False, 1: True, 2: False}]:
    assert reachable_in_domain(base)
rng = random.Random(112193)
for _ in range(5000):
    n = rng.randint(0, 10)
    base = {rng.randint(-5, 20): bool(rng.getrandbits(1)) for _ in range(n)}
    assert reachable_in_domain(base)
print("OK containment: every model-reachable callee base (any dict_pred mapping) "
      "with key=attr_selected()=0, flag=True lies in the axiom Requires domain "
      "(Acc(dict_pred(base),1/2)); no reachable input is outside it.")
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-mapping_with",
        "axiom": "mapping_with",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_SOUND_WITH,
        "rationale": "the real dict-display merge {**base, key: flag} must meet "
        "every mapping_with Ensures (fresh / base-not-mutated — the load-bearing "
        "freshness clause that is the fix; key set; others carried; no spurious "
        "key) on boundary + SplitArray + integer carrier + 20000 fuzz inputs. Any "
        "violation => AXIOM-UNSOUND.",
    },
    {
        "id": "ax-sound-mapping_copy",
        "axiom": "mapping_copy",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_SOUND_COPY,
        "rationale": "the real dict copy {**base} must meet every mapping_copy "
        "Ensures (fresh / base-not-mutated; same keys+values both directions) on "
        "boundary + SplitArray + integer carrier + 20000 fuzz inputs. Any "
        "violation => AXIOM-UNSOUND.",
    },
    {
        "id": "ax-cover-callsites",
        "axiom": "mapping_with",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _PROBE_COVER,
        "rationale": "the model's only callee inputs are base = the caller's attrs "
        "(any dict satisfying dict_pred, the prepare_attrs Requires domain), key = "
        "attr_selected() = 0, flag = True (and base alone for mapping_copy). The "
        "axioms' Requires is exactly dict_pred(base) — any valid mapping is "
        "in-domain — so every caller-reachable input lies inside it. A reachable "
        "base outside the domain would be AXIOM-TOO-WEAK-FOR-CALLER; none exists.",
    },
]
