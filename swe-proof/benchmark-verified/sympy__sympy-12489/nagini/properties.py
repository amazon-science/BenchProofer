# properties.py — PBT manifest for sympy__sympy-12489. NOT a Nagini module; a
# record of adversarial falsification cases. The runner (swebench_nagini.pbt)
# parses SPEC_TESTS / AXIOM_TESTS, executes each, and stamps RESULT.
#
# Defended surface (read from model.py / refinement.md / mapping.md):
#   * make(kind, array)  models Permutation._af_new — the internal builder.
#       LOAD-BEARING post: Result().kind == kind     (family propagation; the
#       pre-patch bug minted onto a fixed family 0 — model_prepatch.py)
#                          Result().array is array    (content identity)
#       READ-ONLY input:  Acc(list_pred(array), 1/2)
#   * combine(self, other, product) models Permutation.__mul__ — a binary
#       combination minted through the LEFT operand's family.
#       LOAD-BEARING post: Result().kind == self.kind (the headline F2P
#       discriminator type(p*q)==CustomPermutation; pre-patch minted through a
#       fixed family — model_prepatch_2.py)
#                          Result().array is product   (content identity)
#       READ-ONLY inputs: Acc(self.kind,1/2) Acc(self.array,1/2)
#                         Acc(other.kind,1/2) Acc(other.array,1/2)
#                         Acc(list_pred(product),1/2)
#
# There is NO @ContractOnly axiom (meta.axioms == []); the family-propagating
# construction is an A-reference deep model validated against the REAL callee by
# axiom_check.py / G-AX. AXIOM_TESTS re-runs that real-callee soundness check
# in-container (gold applied) as a persisted regression of the A-reference.
from pathlib import Path

INSTANCE = "sympy__sympy-12489"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The two impl-region bodies, verbatim from the frozen model.py. Region-surgery:
# we _swap ONLY these (everything between # impl-start/# impl-end) so same_spec
# is guaranteed — the frozen axioms/pure/pre/post-conditions are never touched.
_MAKE_IMPL = "    result = Arrangement(kind, array)  # type: Arrangement\n    return result"
_COMBINE_IMPL = "    result = make(self.kind, product)  # type: Arrangement\n    return result"


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _make(impl):
    return _swap(_BASE, _MAKE_IMPL, impl)


def _combine(impl):
    return _swap(_BASE, _COMBINE_IMPL, impl)


SPEC_TESTS = [

    # ----------------------------------------------------------------- #
    # POSITIVE CONTROLS (soundness) — a structurally-different but CORRECT
    # impl MUST verify, else SPEC-TOO-STRONG. Construction-only artifact:
    # the only structural freedom is local-variable reshape / inlining,
    # which keeps every gold proof obligation intact (no loop/lemma).
    # ----------------------------------------------------------------- #
    {
        "id": "pos-make-inline",
        "kind": "soundness",
        "expect": "verify",
        "module": _make(
            "    # structurally different: construct and return in one expression\n"
            "    # (no intermediate local). Still mints exactly `kind`/`array`.\n"
            "    return Arrangement(kind, array)"
        ),
        "rationale": "a correct make that drops the intermediate local must still "
                     "verify; Result().kind==kind and Result().array is array hold "
                     "from Arrangement's Ensures. If it rejects => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-combine-inline",
        "kind": "soundness",
        "expect": "verify",
        "module": _combine(
            "    # structurally different: inline the make() call into the return.\n"
            "    return make(self.kind, product)"
        ),
        "rationale": "a correct combine that inlines the builder call must verify; "
                     "make's Ensures gives Result().kind==self.kind and "
                     ".array is product. If it rejects => SPEC-TOO-STRONG.",
    },

    # ----------------------------------------------------------------- #
    # ADMISSIBILITY — the precondition must admit a normal, F2P-shaped input.
    # The impl exercises the full Requires chain (half-perm self/other/product,
    # the make call) and asserts the family is propagated for a derived-family
    # operand — confirming the precondition is satisfiable, not vacuous.
    # expect=verify; if it rejects => PRECOND-TOO-STRONG.
    # ----------------------------------------------------------------- #
    {
        "id": "admiss-combine",
        "kind": "admissibility",
        "expect": "verify",
        "module": _combine(
            "    result = make(self.kind, product)  # type: Arrangement\n"
            "    # admissibility: a normal F2P-shaped operand (any family self.kind,\n"
            "    # incl. a derived family) is admitted and propagated by the spec.\n"
            "    Assert(result.kind == self.kind)\n"
            "    return result"
        ),
        "rationale": "the precondition (half-perm self/other/product) admits a normal "
                     "combination and the family propagates; the Assert is discharged "
                     "from make's Ensures. If it rejects => PRECOND-TOO-STRONG.",
    },

    # ----------------------------------------------------------------- #
    # FRAME-MUTATION (MANDATORY — all inputs are read-only Acc(...,1/2)).
    # A rival that satisfies the postcondition VACUOUSLY by overwriting a
    # read-only input must REJECT for INSUFFICIENT PERMISSION. Mechanical
    # fuzzers never think to mutate the input — this is the #1 weakness class.
    # ----------------------------------------------------------------- #
    {
        # The textbook cheat: combine mints onto the FIXED base family (the
        # pre-patch bug, make(0, ...)), then tries to satisfy
        # Result().kind == self.kind by OVERWRITING the read-only self.kind to 0.
        "id": "frame-combine-self-kind-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _combine(
            "    # FRAME-MUTATION cheat: mint onto the fixed base family (wrong),\n"
            "    # then overwrite the read-only self.kind to make the postcondition\n"
            "    # Result().kind == self.kind hold VACUOUSLY. self.kind is only\n"
            "    # Acc(self.kind, 1/2) -> writing it is insufficient permission.\n"
            "    self.kind = 0\n"
            "    result = make(self.kind, product)  # type: Arrangement\n"
            "    return result"
        ),
        "refinement": "its faithful real patch keeps __mul__ minting through the FIXED "
                      "base family (Perm._af_new) and merely relabels self's class to "
                      "the base — i.e. it does NOT propagate the left family, so "
                      "type(p*q) would be Permutation, not CustomPermutation. The F2P "
                      "test_Permutation_subclassing asserts type(p*q)==CustomPermutation "
                      "=> it would NOT resolve.",
        "rationale": "REJECT comes from the permission system: self.kind is Acc(...,1/2) "
                     "(read-only). Writing it is insufficient permission. If it verified, "
                     "the spec would admit a vacuous postcondition => SPEC-TOO-WEAK.",
    },
    {
        # Supporting frame case: make tries to write into the read-only array's
        # elements (full list_pred write) before returning. array is only
        # Acc(list_pred(array), 1/2) -> the element write is insufficient perm.
        "id": "frame-make-array-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _make(
            "    # FRAME-MUTATION cheat: attempt to write into the read-only array\n"
            "    # (list_pred only at 1/2). A mutating builder would need full perm.\n"
            "    array[0] = 0\n"
            "    result = Arrangement(kind, array)  # type: Arrangement\n"
            "    return result"
        ),
        "refinement": "a faithful real _af_new that mutated perm in place would corrupt "
                      "the shared array form across aliasing call sites (the F2P reuses "
                      "the same array object for p and q via [1,2,3,0]); test_Permutation "
                      "/ test_mul P2P checks exact array_form values => it would NOT "
                      "resolve.",
        "rationale": "REJECT comes from the permission system: list_pred(array) held at "
                     "1/2 grants read-only; writing array[0] needs full permission. The "
                     "builder must not mutate its read-only input.",
    },

    # ----------------------------------------------------------------- #
    # PARTIAL-DOMAIN — a rival correct on most of the F2P/P2P domain but
    # diverging on a sub-domain. Pins the load-bearing family clause to a
    # subset of `kind`. expect=reject.
    # ----------------------------------------------------------------- #
    {
        # make is correct for every family EXCEPT the derived family kind==1 (the
        # F2P's CustomPermutation), where it collapses onto the base family 0.
        "id": "partial-make-collapse-kind1",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _make(
            "    # PARTIAL-DOMAIN: honour the family for every kind EXCEPT the\n"
            "    # specific derived family 1 (the F2P CustomPermutation), which is\n"
            "    # collapsed onto the base family 0.\n"
            "    actual = kind  # type: int\n"
            "    if kind == 1:\n"
            "        actual = 0\n"
            "    result = Arrangement(actual, array)  # type: Arrangement\n"
            "    return result"
        ),
        "refinement": "its faithful real patch would propagate the family for all "
                      "subclasses except the one mirroring kind==1 (the F2P's "
                      "CustomPermutation), which it still mints as base Permutation. "
                      "test_Permutation_subclassing constructs exactly that subclass and "
                      "asserts type(p*q)==CustomPermutation => it would NOT resolve.",
        "rationale": "REJECT comes from postcondition Result().kind==kind: at kind==1 "
                     "the impl returns kind 0 != 1. If it verified => SPEC-TOO-WEAK "
                     "(spec failed to pin the whole family domain).",
    },
    {
        # combine mints through the WRONG (right) operand's family instead of the
        # left's — correct only when self.kind==other.kind.
        "id": "partial-combine-right-family",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _combine(
            "    # PARTIAL-DOMAIN / wrong-reference: reach the builder through the\n"
            "    # RIGHT operand's family (other.kind) instead of the LEFT's. Correct\n"
            "    # only on the sub-domain self.kind == other.kind.\n"
            "    result = make(other.kind, product)  # type: Arrangement\n"
            "    return result"
        ),
        "refinement": "its faithful real patch reaches _af_new through type(other) "
                      "(self._af_new -> other._af_new). On the F2P p*q (p custom, q base) "
                      "it yields type(q)==Permutation, not CustomPermutation; the test "
                      "asserts type(p*q)==CustomPermutation => it would NOT resolve.",
        "rationale": "REJECT comes from postcondition Result().kind==self.kind: with "
                     "other.kind the result family equals other.kind, which differs from "
                     "self.kind whenever the operands are of different families. If it "
                     "verified => SPEC-TOO-WEAK.",
    },
    {
        # combine collapses content: returns a value whose array is NOT `product`
        # (drops the content-identity clause Result().array is product). A
        # different (but well-permissioned) array object cannot be `is product`.
        "id": "partial-combine-content-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _combine(
            "    # CONTENT cheat: mint the correct family but on a fresh empty array\n"
            "    # instead of the supplied product, dropping Result().array is product.\n"
            "    fresh = []  # type: List[int]\n"
            "    result = make(self.kind, fresh)  # type: Arrangement\n"
            "    return result"
        ),
        "refinement": "a faithful real __mul__ that returned a permutation of empty "
                      "array form (not the computed product) would fail every value "
                      "check in test_mul / test_Permutation (which compare the product's "
                      "array form), so it would NOT resolve.",
        "rationale": "REJECT comes from postcondition Result().array is product: a fresh "
                     "list is not identical to product. If it verified => SPEC-TOO-WEAK "
                     "(content clause hollow).",
    },
]


# ===================================================================== #
# AXIOM LANE — no @ContractOnly axiom is consumed (meta.axioms == []); the
# family-propagating construction is an A-REFERENCE deep model. We persist the
# G-AX real-callee soundness check (axiom_check.py) as an axiom-soundness probe:
# run the REAL patched Permutation._af_new / __mul__ in-container and assert the
# observed class-identity matches the model's claims. This is the A-reference
# == real-callee obligation (PBT_PLAN §2.4 / §4 A-reference deep models). The
# probe embeds axiom_check.py's logic; it imports only sympy + stdlib.
# ===================================================================== #

# Read the bundle's audited oracle on the HOST at load time and embed its source
# (the runner mounts ONLY the probe at /work; axiom_check.py is NOT in-container).
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-ref-af_new-mul-soundness",
        "axiom": "make/combine family-propagation (A-reference deep model)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,  # the A-reference describes POST-gold behaviour
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "the deep model claims make(kind,array).kind==kind / "
                     "combine(self,other,product).kind==self.kind. This runs the REAL "
                     "patched Permutation._af_new and __mul__ on a genuine subclass "
                     "(mirroring the F2P CustomPermutation) over exhaustive sizes 0..5 "
                     "(builder) / 1..4 (combination) + 3000 fuzz each + the F2P "
                     "witnesses type(p*q) is CustomPermutation, type(q*p) is "
                     "Permutation, p==q. Exit 0 iff every observation meets the model's "
                     "claims; any divergence is AXIOM-UNSOUND for the A-reference.",
    },
]
