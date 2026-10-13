# properties.py — PBT manifest for django__django-15916. NOT a Nagini module;
# a record of adversarial cases the runner (swebench_nagini.pbt) executes and
# stamps RESULT onto. Spec cases are full model.py variants that share the
# frozen spec (only the impl region is edited) and are checked by Nagini verify;
# axiom cases are real-callee probes (none here — no @ContractOnly axiom).
#
# Defended surface (read from model.py / refinement.md):
#   declared_form_callback(meta_own, meta_inherited) -> int
#     load-bearing postcond:  Result() == resolve_attr(meta_own, meta_inherited)
#       (+ own!=0 -> ==meta_own ; own==0 -> ==meta_inherited ; own!=0 -> !=0)
#   factory_form_callback(passed, base_meta_own, base_meta_inherited) -> int
#     load-bearing postcond:
#       Result() == resolve_attr(passed, resolve_attr(base_meta_own, base_meta_inherited))
#       (+ passed!=0 -> ==passed ; passed==0 -> ==resolve_attr(base..) ;
#        passed==0 & base_own!=0 -> ==base_own ;
#        passed==0 & base_own==0 & base_inh!=0 -> ==base_inh)
#
#   resolve_attr is a @Pure helper FULLY UNFOLDED over the inputs
#   (own if own!=0 else inherited) — it is GROUNDED in the args, not an opaque
#   answer-key oracle. So "echoing resolve_attr(...)" IS the correct answer;
#   there is no WRONG echo to build (ungrounded-oracle-echo class N/A — see the
#   honest cheapest-impl positive controls instead).
#
#   Both modeled functions take only pass-by-value `int` params (Nagini ints are
#   immutable values, NOT heap objects under Acc(...,1/2)). There is NO read-only
#   heap input, so the FRAME-MUTATION class does not apply (justified in the
#   construct return 'assessment').
from pathlib import Path

INSTANCE = "django__django-15916"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- exact impl-region bodies in the frozen model.py (edit ONLY these) -------

# declared_form_callback impl region body (between its # impl-start / # impl-end)
_DECL_IMPL = (
    "    # The options object stores its resolved builder; the constructor reads it\n"
    "    # straight from there to drive field construction.\n"
    "    stored = resolve_attr(meta_own, meta_inherited)\n"
    "    return stored\n"
)

# factory_form_callback impl region body
_FACT_IMPL = (
    "    # The factory records the passed builder on the produced options object\n"
    "    # only when one was given; it never injects an overriding \"no builder\".\n"
    "    # The produced options object therefore resolves (passed shadows the\n"
    "    # inherited base builder), and the constructor reads that resolved value.\n"
    "    produced_inherited = resolve_attr(base_meta_own, base_meta_inherited)\n"
    "    produced_own = passed  # 0 when nothing was passed -> inherited is seen\n"
    "    stored = resolve_attr(produced_own, produced_inherited)\n"
    "    return stored\n"
)


SPEC_TESTS = [
    # ---------------------------------------------------------------------
    # POSITIVE CONTROLS (soundness) — structurally-different CORRECT impls.
    # Must VERIFY; if not, SPEC-TOO-STRONG. resolve_attr is a 2-branch select
    # with no recursion/fold, so a branch-reorder / explicit-if reshape keeps
    # the gold proof valid (no induction lemma needed).
    # ---------------------------------------------------------------------
    {
        "id": "pos-declared-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _DECL_IMPL,
            "    # Correct, structurally different: test the absence case first\n"
            "    # and fall through to the own builder. Same selection, inverted\n"
            "    # branch order; no use of resolve_attr in the executable body.\n"
            "    selected = 0  # type: int\n"
            "    if meta_own == 0:\n"
            "        selected = meta_inherited\n"
            "    else:\n"
            "        selected = meta_own\n"
            "    return selected\n",
        ),
        "rationale": "a correct but branch-reordered, inlined impl of the same "
                     "own-shadows-inherited selection must verify (else "
                     "SPEC-TOO-STRONG). resolve_attr unfolds to exactly this "
                     "2-way select, so each Ensures clause is discharged.",
    },
    {
        "id": "pos-factory-explicit-if",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _FACT_IMPL,
            "    # Correct, structurally different: spell out the two-level\n"
            "    # resolution with explicit nested ifs instead of composing\n"
            "    # resolve_attr. passed shadows the base-resolved builder, which\n"
            "    # itself is base_meta_own shadowing base_meta_inherited.\n"
            "    selected = 0  # type: int\n"
            "    if passed != 0:\n"
            "        selected = passed\n"
            "    elif base_meta_own != 0:\n"
            "        selected = base_meta_own\n"
            "    else:\n"
            "        selected = base_meta_inherited\n"
            "    return selected\n",
        ),
        "rationale": "a correct impl that inlines the nested resolution must "
                     "verify (else SPEC-TOO-STRONG). The three branches are "
                     "exactly resolve_attr(passed, resolve_attr(base_own, "
                     "base_inh)) case-split, so every Ensures clause holds.",
    },

    # ---------------------------------------------------------------------
    # ADMISSIBILITY — a positive-control caller proving the Requires admits a
    # normal F2P-shaped input. Must VERIFY; if not, PRECOND-TOO-STRONG.
    # F2P shapes: declared meta_own=1,meta_inherited=0 (test_custom_callback_in_meta);
    # factory passed=0,base_own=2,base_inh=0 (test_custom_callback_from_base_form_meta).
    # We assert the Requires (all params >= 0) hold for these shapes via a
    # self-call inside the impl, keeping the gold selection as the return.
    # ---------------------------------------------------------------------
    {
        "id": "admiss-declared-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _DECL_IMPL,
            "    # Admissibility: the F2P-shaped input (own builder declared,\n"
            "    # nothing inherited) satisfies the precondition (>=0). Assert it,\n"
            "    # then return the gold selection.\n"
            "    f2p_own = 1    # type: int\n"
            "    f2p_inh = 0    # type: int\n"
            "    Assert(f2p_own >= 0)\n"
            "    Assert(f2p_inh >= 0)\n"
            "    stored = resolve_attr(meta_own, meta_inherited)  # type: int\n"
            "    return stored\n",
        ),
        "rationale": "the precondition (meta_own>=0, meta_inherited>=0) must "
                     "admit the F2P shape (own=1, inherited=0) of "
                     "test_custom_callback_in_meta (else PRECOND-TOO-STRONG).",
    },
    {
        "id": "admiss-factory-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _FACT_IMPL,
            "    # Admissibility: the F2P-shaped factory input (no builder passed,\n"
            "    # base form's Meta carries one) satisfies the precondition (>=0).\n"
            "    f2p_passed = 0    # type: int\n"
            "    f2p_base_own = 2  # type: int\n"
            "    f2p_base_inh = 0  # type: int\n"
            "    Assert(f2p_passed >= 0)\n"
            "    Assert(f2p_base_own >= 0)\n"
            "    Assert(f2p_base_inh >= 0)\n"
            "    produced_inherited = resolve_attr(base_meta_own, base_meta_inherited)  # type: int\n"
            "    produced_own = passed  # type: int\n"
            "    stored = resolve_attr(produced_own, produced_inherited)  # type: int\n"
            "    return stored\n",
        ),
        "rationale": "the precondition (all params >=0) must admit the F2P shape "
                     "(passed=0, base_own=2, base_inh=0) of "
                     "test_custom_callback_from_base_form_meta (else "
                     "PRECOND-TOO-STRONG).",
    },

    # ---------------------------------------------------------------------
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls that share the spec.
    # Each MUST be rejected; if any verifies the spec admits a wrong impl.
    # ---------------------------------------------------------------------

    # (1) PARTIAL-DOMAIN, declared site — the PRE-PATCH bug itself.
    # Correct whenever meta_own==0 (returns inherited) but drops the own
    # builder: returns inherited unconditionally, i.e. 0 on the F2P witness.
    {
        "id": "weak-declared-drop-own",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _DECL_IMPL,
            "    # WRONG (= the pre-patch metaclass): read only a *base form's*\n"
            "    # options builder (the inherited value), never the current\n"
            "    # options object's own builder. Drops meta_own.\n"
            "    stored = meta_inherited\n"
            "    return stored\n",
        ),
        "refinement": "this is model_prepatch.py's behaviour: the faithful real "
                      "patch (metaclass reads attrs.pop('formfield_callback', "
                      "base_formfield_callback), never opts.formfield_callback) "
                      "fails test_custom_callback_in_meta — a builder declared "
                      "only on the form's own Meta (meta_own!=0, meta_inherited=0) "
                      "is dropped, so the widget is the model default, not Textarea. "
                      "It does NOT resolve the F2P.",
        "rationale": "fails Ensures(Implies(meta_own!=0, Result()==meta_own)) and "
                     "Ensures(Implies(meta_own!=0, Result()!=0)) on the witness "
                     "meta_own>0, meta_inherited==0 (postcondition clause).",
    },

    # (2) VALUE double-mask / wrong-shadow, declared site — own SWAPPED with
    # inherited (inherited shadows own). Correct only when exactly one of the
    # two is nonzero AND they pick the same? No: diverges when both nonzero
    # and on the own-only witness. Different wrong impl from (1).
    {
        "id": "weak-declared-inverted-shadow",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _DECL_IMPL,
            "    # WRONG: inverted shadowing — the inherited builder shadows the\n"
            "    # own one (inherited wins whenever present). Diverges when the\n"
            "    # own builder is declared (meta_own!=0).\n"
            "    if meta_inherited != 0:\n"
            "        stored = meta_inherited\n"
            "    else:\n"
            "        stored = meta_own\n"
            "    return stored\n",
        ),
        "refinement": "a real patch where an inherited base-Meta builder shadows "
                      "the form's own Meta builder would build the field with the "
                      "base builder's widget when both are present — but Django "
                      "attribute resolution has the own attribute shadow the "
                      "inherited one. test_custom_callback_in_meta declares the "
                      "builder on the own Meta with no base builder; here that "
                      "case happens to agree (inherited==0), but the F2P pins "
                      "own-shadows-inherited and a base-form subclass test "
                      "(P2P attribute-resolution tests) would observe the wrong "
                      "widget when both levels carry a builder. Faithful patch "
                      "does not match Django semantics.",
        "rationale": "fails Ensures(Result()==resolve_attr(meta_own, "
                     "meta_inherited)) on a witness with meta_own!=0 and "
                     "meta_inherited!=0 (resolve_attr returns meta_own; this "
                     "rival returns meta_inherited) — master postcondition clause.",
    },

    # (3) PARTIAL-DOMAIN, factory site — the PRE-PATCH bug itself.
    # Returns `passed` unconditionally (the injected possibly-0 value always
    # wins), overriding the base-Meta builder with 0 when none is passed.
    {
        "id": "weak-factory-passed-wins",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _FACT_IMPL,
            "    # WRONG (= the pre-patch factory): inject the passed builder as\n"
            "    # a class-level attribute UNCONDITIONALLY (0 when none) and let\n"
            "    # it always win, overriding the base form's options builder.\n"
            "    stored = passed\n"
            "    return stored\n",
        ),
        "refinement": "this is model_prepatch_2.py's behaviour: the faithful real "
                      "patch (modelform_factory keeps form_class_attrs["
                      "'formfield_callback'] = formfield_callback, =None here, and "
                      "the metaclass attrs.pop reads it) fails "
                      "test_custom_callback_from_base_form_meta — the base form's "
                      "Meta builder is overridden by the injected None, so the "
                      "produced form's widget is the model default, not Textarea. "
                      "It does NOT resolve the F2P.",
        "rationale": "fails Ensures(Implies(passed==0 and base_meta_own!=0, "
                     "Result()==base_meta_own)) on the witness passed==0, "
                     "base_meta_own>0 (this rival returns 0) — discriminating "
                     "postcondition clause for the factory site.",
    },

    # (4) PARTIAL-DOMAIN, factory site — drops the base_meta_inherited fallback.
    # Correct on the F2P (base_own present) and whenever base_own!=0, but
    # diverges when the base builder is itself only inherited
    # (passed==0, base_own==0, base_inh!=0): returns 0 instead of base_inh.
    {
        "id": "weak-factory-drop-base-inherited",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _FACT_IMPL,
            "    # WRONG: resolve the produced builder against only the base's\n"
            "    # OWN builder, dropping the base's inherited fallback. Agrees on\n"
            "    # the F2P (base_meta_own present) but loses a builder the base\n"
            "    # form itself only inherits.\n"
            "    produced_own = passed\n"
            "    stored = resolve_attr(produced_own, base_meta_own)\n"
            "    return stored\n",
        ),
        "refinement": "a real patch that read only the base form's directly-set "
                      "Meta builder and ignored a builder the base form ITSELF "
                      "inherited (grand-base Meta) would drop that builder for the "
                      "produced class. A faithful patch with this gap fails the "
                      "deeper-inheritance attribute-resolution P2P scenarios "
                      "(model_forms FormFieldCallbackTests exercise inherited "
                      "Meta chains) — getattr over the full MRO sees the "
                      "inherited builder, this rival does not. Does NOT resolve "
                      "the full F2P/P2P attribute-resolution surface.",
        "rationale": "fails Ensures(Implies(passed==0 and base_meta_own==0 and "
                     "base_meta_inherited!=0, Result()==base_meta_inherited)) on "
                     "the witness passed==0, base_meta_own==0, base_meta_inherited>0 "
                     "(this rival returns 0) — the two-level-resolution clause.",
    },

    # (5) SUPPORTING near-miss, factory — return the inner resolution only,
    # ignoring `passed` entirely (always inherit the base builder). Diverges
    # when a builder IS passed (passed!=0).
    {
        "id": "weak-factory-ignore-passed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _FACT_IMPL,
            "    # WRONG: ignore the passed builder entirely and always inherit\n"
            "    # the base form's resolved builder. Diverges when one is passed.\n"
            "    stored = resolve_attr(base_meta_own, base_meta_inherited)\n"
            "    return stored\n",
        ),
        "refinement": "a real factory that ignored its formfield_callback argument "
                      "and always used the base form's builder would fail any "
                      "test passing an explicit callback to modelform_factory "
                      "(the produced form must use the passed builder's widget); "
                      "modelform_factory's documented contract and existing P2P "
                      "tests pass an explicit callback. A faithful patch with "
                      "this behaviour does NOT resolve those cases.",
        "rationale": "fails Ensures(Implies(passed!=0, Result()==passed)) on the "
                     "witness passed>0 with base_meta_own/inherited differing "
                     "from passed (postcondition clause).",
    },
]

# No @ContractOnly axioms and no consumed axiom in this bundle: resolve_attr is
# a deep model (A-reference) fully unfolded in the pure region, validated ==
# real CPython getattr/MRO resolution by axiom_check.py (G-AX, 40002 fuzz
# resolutions, 0 mismatch). There is no callee to probe in Docker.
AXIOM_TESTS = []
