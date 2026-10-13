# properties.py — PBT manifest for sympy__sympy-14711. NOT a Nagini module; a
# record of adversarial falsification cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT.
#
# Each SPEC_TESTS["module"] is a FULL model.py built by region-surgery: we read
# the frozen model.py and _swap text ONLY inside the # impl-start / # impl-end
# region (which includes the nested # invariants-start/# invariants-end block),
# so the spec (axioms / pure / pre / post-conditions / class decls) is provably
# untouched (markers.same_spec stays True). AXIOM_TESTS probes execute the REAL
# sympy callees in the instance Docker image (apply_gold=True).
#
# Defended surface (read model.py + refinement.md + mapping.md + instance.json +
# axiom_check.py + the gold patch + F2P test_Vector):
#   vec_add(self: Vec, other: Operand) -> Vec  -- the modeled Vector.__add__.
#   The gold change is `if other == 0: return self` prepended before the
#   unconditional `_check_vector(other)` / `Vector(self.args + other.args)`.
#
#   READ-ONLY inputs (frame-mutation surface, directive 5 / MANDATORY):
#     - self.terms at Acc(...,1/2) in Requires, downgraded to Acc(...,1/4) in
#       Ensures. READ-ONLY: an impl that WRITES self.terms needs full permission
#       it does not hold, and cannot re-establish the Ensures frame. ATTACKED.
#     - other.is_scalar_zero / other.is_vector / other.terms all at Acc(...,1/2)
#       (held read-only across Requires/Ensures). Writing any of them is an
#       insufficient-permission reject. ATTACKED (is_vector flip).
#
#   LOAD-BEARING postcondition clauses:
#     (1) Implies(other.is_scalar_zero, ToSeq(Result().terms)==ToSeq(self.terms))
#         AND the Exsures is guarded by `not other.is_scalar_zero and not
#         other.is_vector` -> the scalar zero must return self NORMALLY, never
#         raise. This is the discriminating content of the gold fix (G-DIFF:
#         the prepatch reaches vector_guard on a possibly-scalar-zero operand and
#         cannot establish `not other.is_scalar_zero`, so clause (1) is unprovable).
#     (2) Implies(other.is_vector, ToSeq(Result().terms) ==
#         normal_form(ToSeq(self.terms) + ToSeq(other.terms))) -- the
#         content-bearing clause. normal_form is @Pure @ContractOnly, but the
#         post applies it to the concatenation of BOTH input carriers, so it is
#         GROUNDED in the inputs (NOT an answer-key oracle). The drop-other echo
#         attacks (return self / Vec(self.terms) / Vec([])) produce normal_form of
#         a DIFFERENT sequence, which the opaque function does not let the
#         verifier equate with normal_form(self ++ other) -> rejected.
#     (3) Exsures(NotAVector, ... not other.is_scalar_zero and not other.is_vector)
#         -- a neither-zero-nor-vector operand raises.
#     (3a) Ensures(other.is_scalar_zero or other.is_vector) -- the raise is
#         MANDATORY: a NORMAL return is only possible for the scalar zero or a
#         genuine vector. Closes the G-PANEL-1 atk_2 hole (swallowing `return
#         self` on the neither state used to verify: both Implies vacuous,
#         Exsures merely permissive). Attacked (swallow-neither-sharp).
#
#   ORACLE-GROUNDING NOTE: clause (2) is NOT an ungrounded answer-key. Its
#   argument `ToSeq(self.terms) + ToSeq(other.terms)` is an expressible
#   structural relation on the two actual inputs; there is no constant marker to
#   echo. The genuine "echo without doing the work" attacks are the drop-other
#   impls (they echo normal_form of a SUBSET of the inputs); each is included as
#   a uniqueness reject with a real F2P refinement. (See 'assessment'.)
#
#   AXIOMS: vector_guard (A-consumed, == _check_vector) and normal_form/normalise
#   (A-reference, == Vector.__init__ frame-merging constructor). Probes port
#   axiom_check.py: identity-on-Vector / raise-on-non-Vector for the guard;
#   never-grows length bound + determinism + the F2P distinguisher
#   normal_form(self++other) != normal_form(self) for the constructor.

from pathlib import Path

INSTANCE = "sympy__sympy-14711"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The frozen gold impl region (verbatim from model.py, strictly between the
# # impl-start and # impl-end markers, INCLUDING the nested invariants block).
_GOLD_IMPL = """    if other.is_scalar_zero:
        return self
    checked = vector_guard(other)  # type: Vec
    combined = list(self.terms)  # type: List[int]
    j = 0
    while j < len(checked.terms):
        # invariants-start
        Invariant(Acc(self.terms, 1 / 2) and Acc(list_pred(self.terms), 1 / 2))
        Invariant(Acc(checked.terms, 1 / 2) and Acc(list_pred(checked.terms), 1 / 2))
        Invariant(Acc(other.is_scalar_zero, 1 / 2))
        Invariant(not other.is_scalar_zero)
        Invariant(Acc(other.is_vector, 1 / 2))
        Invariant(other.is_vector)
        Invariant(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
        Invariant(ToSeq(checked.terms) == ToSeq(other.terms))
        Invariant(Acc(list_pred(combined)))
        Invariant(0 <= j and j <= len(checked.terms))
        Invariant(ToSeq(combined) == ToSeq(self.terms) + ToSeq(checked.terms).take(j))
        # `j` rises by one per pass and the bound len(checked.terms) is fixed
        # (checked.terms is held read-only at 1/2 and never written), so
        # len(checked.terms) - j + 1 strictly decreases and stays >= 1 while
        # j < len(checked.terms).
        Invariant(MustTerminate(len(checked.terms) - j + 1))
        # invariants-end
        combined.append(checked.terms[j])
        Assert(ToSeq(checked.terms).take(j + 1)
               == ToSeq(checked.terms).take(j) + PSeq(checked.terms[j]))
        j = j + 1
    Assert(ToSeq(checked.terms).take(len(checked.terms)) == ToSeq(checked.terms))
    Assert(ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms))
    result = Vec(combined)  # type: Vec
    # Vec.__init__ pins ToSeq(result.terms) == normal_form(ToSeq(combined)), and
    # ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms); normal_form is a
    # function, so this is exactly clause (2).
    Assert(ToSeq(result.terms)
           == normal_form(ToSeq(self.terms) + ToSeq(other.terms)))
    return result"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not in base")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _impl(new_body: str) -> str:
    """Return a full model.py source with the impl region body replaced.
    Only text strictly between the impl markers changes => same_spec holds."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


# ---------------------------------------------------------------------------
# SPEC LANE
# ---------------------------------------------------------------------------

SPEC_TESTS = [

    # === 6. ADMISSIBILITY ===================================================
    # The precondition must admit a normal F2P-shaped input. The cleanest
    # admissibility witness is the frozen gold impl itself: if the Requires
    # (Acc 1/2 on self.terms / other fields, Implies(is_scalar_zero, not
    # is_vector)) were too strong, the gold body could not verify. The F2P
    # exercises A.x + 0 (scalar zero) and v1 + v2 (vector) -- both operand
    # shapes are reachable under this precondition.
    {
        "id": "admiss-gold",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_GOLD_IMPL),  # identity: the frozen gold impl
        "rationale": "the frozen gold impl must verify against its own frozen "
                     "spec; if it did not the precondition (Acc 1/2 on "
                     "self.terms and the operand fields, Implies(is_scalar_zero, "
                     "not is_vector)) would be PRECOND-TOO-STRONG. Identity "
                     "positive control / admissibility witness for the F2P "
                     "operand shapes (scalar zero + genuine vector).",
    },

    # === 5. POSITIVE CONTROL (soundness) ====================================
    # A structurally-DIFFERENT but behaviourally CORRECT impl. The gold body
    # writes `combined = list(self.terms)` then appends each checked.terms[j]
    # in a forward index loop. This variant RESHAPES the local construction:
    # it starts from the EMPTY list, first appends every self.terms element,
    # then every checked.terms element (two sequential forward loops over the
    # SAME front-recursive ToSeq fold), proving the same
    #   ToSeq(combined) == ToSeq(self.terms) + ToSeq(checked.terms)
    # by index folds. Both loops are forward-append against the front-recursive
    # ToSeq.take() helper -- the SAME shape the gold proof uses (so NO new
    # f(a+b)==f(a)+f(b) lemma is needed; pilot-bug #3 avoided), with every gold
    # framing Assert kept. MUST verify; else SPEC-TOO-STRONG.
    {
        "id": "pos-two-loops",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if other.is_scalar_zero:\n"
            "        return self\n"
            "    checked = vector_guard(other)  # type: Vec\n"
            "    # RESHAPE: build `combined` from the empty list in two forward\n"
            "    # append loops (self first, then checked) instead of seeding\n"
            "    # with list(self.terms). Same final ToSeq, gold framing kept.\n"
            "    combined = []  # type: List[int]\n"
            "    i = 0\n"
            "    while i < len(self.terms):\n"
            "        Invariant(Acc(self.terms, 1 / 2) and Acc(list_pred(self.terms), 1 / 2))\n"
            "        Invariant(Acc(checked.terms, 1 / 2) and Acc(list_pred(checked.terms), 1 / 2))\n"
            "        Invariant(Acc(other.is_scalar_zero, 1 / 2))\n"
            "        Invariant(not other.is_scalar_zero)\n"
            "        Invariant(Acc(other.is_vector, 1 / 2))\n"
            "        Invariant(other.is_vector)\n"
            "        Invariant(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))\n"
            "        Invariant(ToSeq(checked.terms) == ToSeq(other.terms))\n"
            "        Invariant(Acc(list_pred(combined)))\n"
            "        Invariant(0 <= i and i <= len(self.terms))\n"
            "        Invariant(ToSeq(combined) == ToSeq(self.terms).take(i))\n"
            "        Invariant(MustTerminate(len(self.terms) - i + 1))\n"
            "        combined.append(self.terms[i])\n"
            "        Assert(ToSeq(self.terms).take(i + 1)\n"
            "               == ToSeq(self.terms).take(i) + PSeq(self.terms[i]))\n"
            "        i = i + 1\n"
            "    Assert(ToSeq(self.terms).take(len(self.terms)) == ToSeq(self.terms))\n"
            "    Assert(ToSeq(combined) == ToSeq(self.terms))\n"
            "    j = 0\n"
            "    while j < len(checked.terms):\n"
            "        Invariant(Acc(self.terms, 1 / 2) and Acc(list_pred(self.terms), 1 / 2))\n"
            "        Invariant(Acc(checked.terms, 1 / 2) and Acc(list_pred(checked.terms), 1 / 2))\n"
            "        Invariant(Acc(other.is_scalar_zero, 1 / 2))\n"
            "        Invariant(not other.is_scalar_zero)\n"
            "        Invariant(Acc(other.is_vector, 1 / 2))\n"
            "        Invariant(other.is_vector)\n"
            "        Invariant(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))\n"
            "        Invariant(ToSeq(checked.terms) == ToSeq(other.terms))\n"
            "        Invariant(Acc(list_pred(combined)))\n"
            "        Invariant(0 <= j and j <= len(checked.terms))\n"
            "        Invariant(ToSeq(combined) == ToSeq(self.terms) + ToSeq(checked.terms).take(j))\n"
            "        Invariant(MustTerminate(len(checked.terms) - j + 1))\n"
            "        combined.append(checked.terms[j])\n"
            "        Assert(ToSeq(checked.terms).take(j + 1)\n"
            "               == ToSeq(checked.terms).take(j) + PSeq(checked.terms[j]))\n"
            "        j = j + 1\n"
            "    Assert(ToSeq(checked.terms).take(len(checked.terms)) == ToSeq(checked.terms))\n"
            "    Assert(ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms))\n"
            "    result = Vec(combined)  # type: Vec\n"
            "    Assert(ToSeq(result.terms)\n"
            "           == normal_form(ToSeq(self.terms) + ToSeq(other.terms)))\n"
            "    return result"
        ),
        "rationale": "a correct impl with a different local construction (empty "
                     "list + two sequential forward-append loops, self then "
                     "checked) that proves the SAME ToSeq(combined) == "
                     "ToSeq(self.terms) + ToSeq(other.terms) and feeds the same "
                     "Vec(combined). Uses only the front-recursive ToSeq.take() "
                     "fold the gold proof already uses (no new distributivity "
                     "lemma) and keeps every gold framing Assert. MUST verify; "
                     "else SPEC-TOO-STRONG.",
    },

    # === 1. FRAME-MUTATION (MANDATORY: self.terms is read-only Acc(...,1/2)) =
    # A rival that WRITES the read-only left operand to satisfy the
    # postcondition vacuously. self.terms is held at Acc(...,1/2) in Requires
    # (downgraded to 1/4 in Ensures); appending to it via the list predicate
    # needs FULL permission the caller does not grant. The append corrupts the
    # frame and cannot re-establish the Ensures Acc. Must be rejected for
    # INSUFFICIENT PERMISSION. The rest of the body is the gold construction,
    # so the rejection is attributable to the write, not a value error.
    {
        "id": "frame-write-self-terms",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if other.is_scalar_zero:\n"
            "        return self\n"
            "    checked = vector_guard(other)  # type: Vec\n"
            "    # ATTACK: mutate the READ-ONLY left operand in place (append the\n"
            "    # other operand's components onto self.terms), then construct\n"
            "    # from it -- only Acc(self.terms, 1/2) held, so this append needs\n"
            "    # permission the caller does not grant.\n"
            "    j = 0\n"
            "    while j < len(checked.terms):\n"
            "        Invariant(Acc(self.terms) and Acc(list_pred(self.terms)))\n"
            "        Invariant(Acc(checked.terms, 1 / 2) and Acc(list_pred(checked.terms), 1 / 2))\n"
            "        Invariant(Acc(other.is_scalar_zero, 1 / 2))\n"
            "        Invariant(Acc(other.is_vector, 1 / 2))\n"
            "        Invariant(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))\n"
            "        Invariant(0 <= j and j <= len(checked.terms))\n"
            "        Invariant(MustTerminate(len(checked.terms) - j + 1))\n"
            "        self.terms.append(checked.terms[j])\n"
            "        j = j + 1\n"
            "    result = Vec(self.terms)  # type: Vec\n"
            "    return result"
        ),
        "refinement": "the real Vector.__add__ never mutates self.args; it builds "
                      "a fresh `self.args + other.args` and passes it to the "
                      "Vector constructor. SymPy Vectors are treated as "
                      "immutable -- mutating self.args in place would corrupt "
                      "every earlier reference to self (e.g. v1 reused after "
                      "v3 = v1 + v2 in test_Vector) and produce wrong dot "
                      "products, so a mutating patch would NOT resolve test_Vector.",
        "rationale": "rejected by the PERMISSION SYSTEM: appending to self.terms "
                     "requires Acc(list_pred(self.terms), 1) but Requires grants "
                     "only Acc(...,1/2); the Ensures(Acc(self.terms, 1/4)) frame "
                     "also cannot be re-established after an in-place mutation. A "
                     "byte-fuzzer never constructs this -- directive 5 / the #1 "
                     "weakness class.",
    },

    # === 1b. FRAME-MUTATION on the read-only operand flag (supporting) ======
    # A rival that WRITES other.is_vector (held at Acc(...,1/2)) to dodge the
    # scalar-zero / vector dispatch. Writing the flag needs full permission the
    # caller does not grant, and breaks the Ensures(Acc(other.is_vector, 1/2))
    # frame. Supporting frame-mutation case on the operand object.
    {
        "id": "frame-write-is-vector",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # ATTACK: overwrite the read-only operand discriminator so the\n"
            "    # scalar-zero short-circuit always fires. Needs full permission\n"
            "    # on other.is_scalar_zero (only Acc(...,1/2) held).\n"
            "    other.is_scalar_zero = True\n"
            "    return self"
        ),
        "refinement": "the operand kind (`other == 0` / isinstance(other, "
                      "Vector)) is a property of the actual addend, not "
                      "something __add__ assigns; a patch that forced every "
                      "operand to be treated as the scalar zero would return "
                      "self for v1 + v2 and FAIL test_Vector's dot(v3, A.x) == "
                      "x**2 + x (it would give x, dropping v2), so it would NOT "
                      "resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: assigning "
                     "other.is_scalar_zero requires Acc(other.is_scalar_zero, 1) "
                     "but Requires grants only Acc(...,1/2), and the "
                     "Ensures(Acc(other.is_scalar_zero, 1/2)) frame cannot be "
                     "re-established after a full write. Supporting "
                     "frame-mutation case on the operand object.",
    },

    # === 3. PARTIAL-DOMAIN / UNGROUNDED-ECHO: drop the other operand ========
    # The cheapest impl that satisfies the LENGTH bound of clause (2) without
    # doing the work: `return self`. It echoes normal_form(self.terms) instead
    # of normal_form(self ++ other). Under the content-bearing clause (2) this
    # is NOT provably equal to normal_form(self.terms + other.terms) for an
    # arbitrary other (the opaque @Pure function distinguishes the two args;
    # G-AX exhibits the F2P distinguisher). This is exactly the historical
    # 2nd-pass hole (ATK2). Must be rejected; else SPEC-TOO-WEAK.
    {
        "id": "drop-other-return-self",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if other.is_scalar_zero:\n"
            "        return self\n"
            "    checked = vector_guard(other)  # type: Vec\n"
            "    # ATTACK: drop the other operand entirely; return self for the\n"
            "    # vector branch too. Result is normal_form(self.terms), NOT\n"
            "    # normal_form(self.terms + other.terms).\n"
            "    return self"
        ),
        "refinement": "the gold patch is `return Vector(self.args + other.args)` "
                      "for a vector operand -- it genuinely combines both. F2P "
                      "test_Vector: v3 = v1 + v2 then asserts dot(v3, A.x) == "
                      "x**2 + x. `return self` gives v3 == v1, so dot(v3, A.x) == "
                      "x (drops v2's x**2 term) and the assertion FAILS -- a "
                      "patch that returned self would NOT resolve test_Vector.",
        "rationale": "rejected by the content-bearing clause (2) "
                     "Implies(other.is_vector, ToSeq(Result().terms) == "
                     "normal_form(ToSeq(self.terms) + ToSeq(other.terms))) "
                     "(model.py:177-179): `return self` yields "
                     "normal_form(ToSeq(self.terms)), which the opaque @Pure "
                     "normal_form does not let the verifier equate with "
                     "normal_form(self ++ other) for arbitrary other. This is the "
                     "exact verify-not-correct hole the 2nd-pass fix closed.",
    },

    # === 3b. PARTIAL-DOMAIN / UNGROUNDED-ECHO: rebuild from self only ========
    # A subtler drop-other: construct Vec(self.terms) (re-normalise self alone).
    # Still echoes normal_form(self.terms), distinct from normal_form(self ++
    # other). Mirrors ATK4/ATK8. Must be rejected.
    {
        "id": "drop-other-vec-self",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if other.is_scalar_zero:\n"
            "        return self\n"
            "    checked = vector_guard(other)  # type: Vec\n"
            "    # ATTACK: rebuild from self.terms ONLY (re-normalise self),\n"
            "    # dropping the other operand's components.\n"
            "    combined = list(self.terms)  # type: List[int]\n"
            "    result = Vec(combined)  # type: Vec\n"
            "    return result"
        ),
        "refinement": "Vec(self.terms) re-normalises self alone; the gold patch "
                      "constructs from self.args + other.args. On F2P v3 = v1 + "
                      "v2 this yields v1's normal form (dropping v2), so "
                      "dot(v3, A.x) == x instead of x**2 + x and test_Vector "
                      "FAILS -- a patch dropping other would NOT resolve.",
        "rationale": "rejected by clause (2): Vec(combined) with combined == "
                     "self.terms pins ToSeq(Result().terms) == "
                     "normal_form(ToSeq(self.terms)), not "
                     "normal_form(ToSeq(self.terms) + ToSeq(other.terms)); the "
                     "opaque @Pure normal_form distinguishes the two arguments. "
                     "Mirrors the historical ATK4/ATK8 drop-other hole.",
    },

    # === 3c. PARTIAL-DOMAIN / UNGROUNDED-ECHO: empty result =================
    # The most degenerate echo: Vec([]) -> normal_form(empty), independent of
    # both operands. Cheap supporting case (ATK3). Must be rejected.
    {
        "id": "drop-other-vec-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if other.is_scalar_zero:\n"
            "        return self\n"
            "    checked = vector_guard(other)  # type: Vec\n"
            "    # ATTACK: ignore both operands; construct from the empty list.\n"
            "    combined = []  # type: List[int]\n"
            "    result = Vec(combined)  # type: Vec\n"
            "    return result"
        ),
        "refinement": "Vec([]) is the zero vector regardless of the inputs; the "
                      "gold patch returns Vector(self.args + other.args). On F2P "
                      "v3 = v1 + v2 this gives the zero vector, so dot(v3, A.x) "
                      "== 0 instead of x**2 + x and test_Vector FAILS -- a patch "
                      "returning the empty vector would NOT resolve.",
        "rationale": "rejected by clause (2): ToSeq(Result().terms) == "
                     "normal_form(empty) (an empty PSeq), which the opaque @Pure "
                     "normal_form does not equate with normal_form(self ++ "
                     "other) for non-cancelling operands. Degenerate ATK3 "
                     "drop-other case; cheap supporting reject.",
    },

    # === 2 / CONTROL-FLOW-EFFECT: scalar zero raises (the PREPATCH bug) ======
    # The discriminating content of the gold change: a scalar-zero operand must
    # return self NORMALLY. A rival that omits the short-circuit and runs the
    # guard unconditionally reaches vector_guard(other) on a possibly-scalar-
    # zero operand. By vector_guard's Exsures, that path raises NotAVector when
    # not other.is_vector -- but clause (1) demands a NORMAL self-returning
    # result for the scalar zero (the Exsures is guarded by `not
    # other.is_scalar_zero`). This is EXACTLY model_prepatch.py: it cannot
    # establish `not other.is_scalar_zero` after the unconditional guard. Must
    # be rejected; a verifying rival here is the prepatch crash on A.x + 0.
    {
        "id": "prepatch-no-shortcircuit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # ATTACK: omit `if other.is_scalar_zero: return self` -- the\n"
            "    # PREPATCH body. The guard is reached on a possibly-scalar-zero\n"
            "    # operand; clause (1) then cannot be established (the scalar\n"
            "    # zero is rejected by the guard, contradicting a normal return).\n"
            "    checked = vector_guard(other)  # type: Vec\n"
            "    combined = list(self.terms)  # type: List[int]\n"
            "    j = 0\n"
            "    while j < len(checked.terms):\n"
            "        Invariant(Acc(self.terms, 1 / 2) and Acc(list_pred(self.terms), 1 / 2))\n"
            "        Invariant(Acc(checked.terms, 1 / 2) and Acc(list_pred(checked.terms), 1 / 2))\n"
            "        Invariant(Acc(other.is_scalar_zero, 1 / 2))\n"
            "        Invariant(Acc(other.is_vector, 1 / 2))\n"
            "        Invariant(other.is_vector)\n"
            "        Invariant(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))\n"
            "        Invariant(ToSeq(checked.terms) == ToSeq(other.terms))\n"
            "        Invariant(Acc(list_pred(combined)))\n"
            "        Invariant(0 <= j and j <= len(checked.terms))\n"
            "        Invariant(ToSeq(combined) == ToSeq(self.terms) + ToSeq(checked.terms).take(j))\n"
            "        Invariant(MustTerminate(len(checked.terms) - j + 1))\n"
            "        combined.append(checked.terms[j])\n"
            "        Assert(ToSeq(checked.terms).take(j + 1)\n"
            "               == ToSeq(checked.terms).take(j) + PSeq(checked.terms[j]))\n"
            "        j = j + 1\n"
            "    Assert(ToSeq(checked.terms).take(len(checked.terms)) == ToSeq(checked.terms))\n"
            "    Assert(ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms))\n"
            "    result = Vec(combined)  # type: Vec\n"
            "    return result"
        ),
        "refinement": "this IS the prepatch body (no `if other == 0: return "
                      "self`). The real prepatch `_check_vector(0)` raises "
                      "TypeError('A Vector must be supplied'), so A.x + 0 CRASHES "
                      "instead of returning A.x. The F2P assertion `A.x + 0 == "
                      "A.x` (test_vector.py, the added line) raises and "
                      "test_Vector FAILS -- the prepatch does NOT resolve. This "
                      "is the documented G-DIFF discriminator.",
        "rationale": "rejected at the scalar-zero state: after the unconditional "
                     "vector_guard(other) the impl cannot establish `not "
                     "other.is_scalar_zero` (the guard's Exsures raises on a "
                     "non-vector, and a scalar zero is non-vector), so clause "
                     "(1) Implies(other.is_scalar_zero, ToSeq(Result().terms) == "
                     "ToSeq(self.terms)) -- a NORMAL self-return -- is unprovable. "
                     "Same failure point as model_prepatch.py (Assert(not "
                     "other.is_scalar_zero)).",
    },

    # === 2b. CONTROL-FLOW-EFFECT: scalar zero rebuilt instead of returned ====
    # A rival that handles the scalar zero but RE-NORMALISES self
    # (Vec(self.terms)) instead of returning self. normal_form is not provably
    # idempotent against the IDENTITY in the model (clause (1) demands
    # ToSeq(Result().terms) == ToSeq(self.terms), NOT == normal_form(self.terms)).
    # Since self.terms need not already be a normal form (it is an arbitrary
    # in-domain List[int]), Vec(self.terms) yields normal_form(self.terms) which
    # the verifier cannot equate with self.terms. Must be rejected; pins that
    # clause (1) demands the UNCHANGED list, the identity operation of the fix.
    {
        "id": "scalar-zero-renormalise",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if other.is_scalar_zero:\n"
            "        # ATTACK: re-normalise self instead of returning it. clause\n"
            "        # (1) demands ToSeq(Result) == ToSeq(self), not\n"
            "        # normal_form(self); self.terms need not be a normal form.\n"
            "        rebuilt = list(self.terms)  # type: List[int]\n"
            "        result = Vec(rebuilt)  # type: Vec\n"
            "        return result\n"
            "    checked = vector_guard(other)  # type: Vec\n"
            "    combined = list(self.terms)  # type: List[int]\n"
            "    j = 0\n"
            "    while j < len(checked.terms):\n"
            "        Invariant(Acc(self.terms, 1 / 2) and Acc(list_pred(self.terms), 1 / 2))\n"
            "        Invariant(Acc(checked.terms, 1 / 2) and Acc(list_pred(checked.terms), 1 / 2))\n"
            "        Invariant(Acc(other.is_scalar_zero, 1 / 2))\n"
            "        Invariant(not other.is_scalar_zero)\n"
            "        Invariant(Acc(other.is_vector, 1 / 2))\n"
            "        Invariant(other.is_vector)\n"
            "        Invariant(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))\n"
            "        Invariant(ToSeq(checked.terms) == ToSeq(other.terms))\n"
            "        Invariant(Acc(list_pred(combined)))\n"
            "        Invariant(0 <= j and j <= len(checked.terms))\n"
            "        Invariant(ToSeq(combined) == ToSeq(self.terms) + ToSeq(checked.terms).take(j))\n"
            "        Invariant(MustTerminate(len(checked.terms) - j + 1))\n"
            "        combined.append(checked.terms[j])\n"
            "        Assert(ToSeq(checked.terms).take(j + 1)\n"
            "               == ToSeq(checked.terms).take(j) + PSeq(checked.terms[j]))\n"
            "        j = j + 1\n"
            "    Assert(ToSeq(checked.terms).take(len(checked.terms)) == ToSeq(checked.terms))\n"
            "    Assert(ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms))\n"
            "    result = Vec(combined)\n"
            "    Assert(ToSeq(result.terms)\n"
            "           == normal_form(ToSeq(self.terms) + ToSeq(other.terms)))\n"
            "    return result"
        ),
        "refinement": "the gold patch is `if other == 0: return self` -- it "
                      "returns the SAME object unchanged. Re-running the "
                      "normalising Vector constructor on a vector that is "
                      "already its own args list is a different operation; the "
                      "gold fix is specifically the cheap identity return, and "
                      "the F2P asserts `A.x + 0 == A.x` on the actual A.x object. "
                      "(A faithful patch that rebuilt would only coincidentally "
                      "resolve; the modeled clause (1) pins the identity list.)",
        "rationale": "rejected by clause (1) Implies(other.is_scalar_zero, "
                     "ToSeq(Result().terms) == ToSeq(self.terms)): Vec(rebuilt) "
                     "with rebuilt == self.terms pins ToSeq(Result().terms) == "
                     "normal_form(ToSeq(self.terms)), and self.terms is an "
                     "arbitrary in-domain list (NOT provably already a normal "
                     "form), so the opaque normal_form does not let the verifier "
                     "prove normal_form(self.terms) == self.terms. The spec pins "
                     "the UNCHANGED list -- the identity operation of the fix.",
    },

    # === 2c. CONTROL-FLOW-EFFECT: swallow the neither-operand (SHARP) ========
    # The sharpest swallow: an impl that is CORRECT on the scalar-zero branch
    # (return self) and never reaches the vector branch wrongly, but on a
    # neither-zero-nor-vector operand returns self NORMALLY instead of raising.
    # Before clause (3a) (`Ensures(other.is_scalar_zero or other.is_vector)`)
    # this VERIFIED: both Implies postconditions are vacuous on the neither
    # state and Exsures only PERMITS the raise, it never REQUIRES one -- the
    # exact G-PANEL-1 hole (audit atk_2). Clause (3a) makes a normal return on
    # the neither state a postcondition violation. Must be rejected.
    {
        "id": "swallow-neither-sharp",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if other.is_scalar_zero:\n"
            "        return self\n"
            "    if not other.is_vector:\n"
            "        # ATTACK: silently accept a neither-zero-nor-vector operand\n"
            "        # and return self NORMALLY instead of raising NotAVector.\n"
            "        return self\n"
            "    checked = vector_guard(other)  # type: Vec\n"
            "    combined = list(self.terms)  # type: List[int]\n"
            "    j = 0\n"
            "    while j < len(checked.terms):\n"
            "        Invariant(Acc(self.terms, 1 / 2) and Acc(list_pred(self.terms), 1 / 2))\n"
            "        Invariant(Acc(checked.terms, 1 / 2) and Acc(list_pred(checked.terms), 1 / 2))\n"
            "        Invariant(Acc(other.is_scalar_zero, 1 / 2))\n"
            "        Invariant(not other.is_scalar_zero)\n"
            "        Invariant(Acc(other.is_vector, 1 / 2))\n"
            "        Invariant(other.is_vector)\n"
            "        Invariant(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))\n"
            "        Invariant(ToSeq(checked.terms) == ToSeq(other.terms))\n"
            "        Invariant(Acc(list_pred(combined)))\n"
            "        Invariant(0 <= j and j <= len(checked.terms))\n"
            "        Invariant(ToSeq(combined) == ToSeq(self.terms) + ToSeq(checked.terms).take(j))\n"
            "        Invariant(MustTerminate(len(checked.terms) - j + 1))\n"
            "        combined.append(checked.terms[j])\n"
            "        Assert(ToSeq(checked.terms).take(j + 1)\n"
            "               == ToSeq(checked.terms).take(j) + PSeq(checked.terms[j]))\n"
            "        j = j + 1\n"
            "    Assert(ToSeq(checked.terms).take(len(checked.terms)) == ToSeq(checked.terms))\n"
            "    Assert(ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms))\n"
            "    result = Vec(combined)  # type: Vec\n"
            "    Assert(ToSeq(result.terms)\n"
            "           == normal_form(ToSeq(self.terms) + ToSeq(other.terms)))\n"
            "    return result"
        ),
        "refinement": "the real (patched) __add__ short-circuits ONLY on other "
                      "== 0 and otherwise calls _check_vector(other), which "
                      "RAISES TypeError('A Vector must be supplied') on any "
                      "non-Vector non-zero operand (A.x + 5, A.x + 'foo'). An "
                      "impl that silently returned self would change the "
                      "library's guaranteed error behaviour: e.g. "
                      "cross(A.x + 5, A.y) would silently compute cross(A.x, "
                      "A.y) instead of raising -- a wrong-result behaviour "
                      "change, not the gold patch.",
        "rationale": "rejected by clause (3a) Ensures(other.is_scalar_zero or "
                     "other.is_vector): a NORMAL return on the neither state is "
                     "a postcondition violation, so the raise obligation of "
                     "clause (3) cannot be dodged. Before (3a) this attack "
                     "VERIFIED (both Implies clauses vacuous, Exsures merely "
                     "permissive) -- the closed G-PANEL-1 atk_2 hole.",
    },

    # === SUPPORTING near-miss: drop the not-a-vector reject (Exsures) ========
    # A rival that, on a neither-zero-nor-vector operand, returns self instead
    # of raising NotAVector. The Exsures(NotAVector, ...) clause (3) plus the
    # vector_guard Exsures pin that such an operand must raise. This skips the
    # guard's raise by short-circuiting on a fabricated condition. Cheap
    # supporting control-flow reject (carries a real refinement).
    {
        "id": "swallow-not-a-vector",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if other.is_scalar_zero:\n"
            "        return self\n"
            "    # ATTACK: treat ANY non-zero operand as acceptable and return\n"
            "    # self, never invoking vector_guard -- so a non-vector operand\n"
            "    # is silently accepted instead of raising NotAVector.\n"
            "    return self"
        ),
        "refinement": "the real __add__ calls _check_vector(other), which raises "
                      "TypeError on a non-Vector non-zero operand (e.g. A.x + "
                      "'foo' or A.x + 5). Silently returning self would change "
                      "the error behaviour the library guarantees, and -- worse "
                      "for the F2P -- on a genuine vector operand v1 + v2 it "
                      "returns v1, dropping v2, so dot(v3, A.x) == x not x**2 + x "
                      "and test_Vector FAILS. NOT resolving.",
        "rationale": "rejected on the genuine-vector branch by clause (2) "
                     "(returning self gives normal_form(self), not "
                     "normal_form(self ++ other)); and it abandons clause (3)'s "
                     "Exsures obligation since it never raises NotAVector for a "
                     "non-vector. Supporting control-flow / drop-other reject.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE
# ---------------------------------------------------------------------------
# Two axiomatized callees:
#   vector_guard (A-consumed) == sympy.physics.vector.vector._check_vector;
#   normal_form / normalise (A-reference) == Vector.__init__ (the frame-merging
#   constructor that __add__ calls on self.args + other.args).
# Probes port axiom_check.py logic, EXECUTING the real callees in the instance
# Docker image (apply_gold=True; the change is in __add__, the callees are
# patch-invariant, so gold-applied or not the callees behave identically -- we
# apply_gold for consistency with the post-patch caller config). Each probe
# imports only sympy + stdlib, prints a diagnostic, and sys.exit(0) iff the
# obligation holds. flag_dependency is "none" for all three axioms (single
# positional arg; isinstance / frame-key only), so no runtime-config setup.

AXIOM_TESTS = [

    # --- vector_guard : AXIOM-SOUNDNESS (== _check_vector) ------------------
    # Ensures: a Vector operand is returned UNCHANGED (is-identity), is_vector.
    # Exsures: a non-Vector operand raises (TypeError -> NotAVector). In
    # particular the scalar zero 0 / S(0) is NOT a Vector and MUST raise --
    # exactly why the prepatch crashed on A.x + 0. Fuzz boundaries + sentinels +
    # 2000 randomized non-vectors. Any disagreement is AXIOM-UNSOUND.
    {
        "id": "ax-sound-vector-guard",
        "axiom": "vector_guard",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": (
            "import sys, random\n"
            "from sympy import symbols, S, sqrt, Integer, Float, sympify\n"
            "from sympy.physics.vector import ReferenceFrame, Vector\n"
            "from sympy.physics.vector.vector import _check_vector\n"
            "x, y, z = symbols('x y z')\n"
            "N = ReferenceFrame('N')\n"
            "A = N.orientnew('A', 'Axis', [x, N.x])\n"
            "# (a) genuine Vectors must be returned UNCHANGED (is-identity)\n"
            "vectors = [N.x, N.y, N.z, A.x, A.y, A.z, x*N.x,\n"
            "           x*N.x + y*N.y + z*N.z, 0*N.x, N.x - N.x,\n"
            "           Vector(0), Vector([]), sqrt(2)*N.z,\n"
            "           (x**2)*N.x + (y**2)*N.y]\n"
            "for v in vectors:\n"
            "    assert isinstance(v, Vector), 'setup: %r not a Vector' % (v,)\n"
            "    out = _check_vector(v)\n"
            "    assert out is v, ('vector_guard UNSOUND: _check_vector did not "
            "return the operand unchanged for %r (got %r)' % (v, out))\n"
            "# (b) the scalar zero is NOT a Vector and MUST raise (TypeError)\n"
            "scalar_zeros = [0, S(0), S.Zero, Integer(0), sympify(0), 0.0, Float(0)]\n"
            "for zero in scalar_zeros:\n"
            "    assert not isinstance(zero, Vector), 'setup: %r is a Vector' % (zero,)\n"
            "    raised = False\n"
            "    try:\n"
            "        _check_vector(zero)\n"
            "    except TypeError:\n"
            "        raised = True\n"
            "    assert raised, ('vector_guard UNSOUND: _check_vector did NOT "
            "raise on the scalar zero %r -- the prepatch crash on A.x + 0 would "
            "not be modeled' % (zero,))\n"
            "# (c) a spread of other non-Vector objects must raise\n"
            "nonvectors = [1, -1, 2, 100, S(1), Integer(5), sympify(3), 1.5,\n"
            "              -2.0, Float(3.14), x, y, x + y, x*y, x**2, sqrt(x),\n"
            "              'vector', '', '0', [], [1, 2, 3], (1, 2), {}, {'a': 1},\n"
            "              set(), None, True, False, complex(1, 2)]\n"
            "for obj in nonvectors:\n"
            "    if isinstance(obj, Vector):\n"
            "        continue\n"
            "    raised = False\n"
            "    try:\n"
            "        _check_vector(obj)\n"
            "    except TypeError:\n"
            "        raised = True\n"
            "    assert raised, ('vector_guard UNSOUND: _check_vector did NOT "
            "raise on non-Vector %r' % (obj,))\n"
            "# (d) randomized fuzz over non-Vector objects\n"
            "rng = random.Random(14711)\n"
            "syms = [x, y, z]\n"
            "checked = 0\n"
            "for _ in range(2000):\n"
            "    c = rng.randint(0, 6)\n"
            "    if c == 0:\n"
            "        obj = rng.randint(-1000, 1000)\n"
            "    elif c == 1:\n"
            "        obj = rng.uniform(-1000.0, 1000.0)\n"
            "    elif c == 2:\n"
            "        obj = S(rng.randint(-1000, 1000))\n"
            "    elif c == 3:\n"
            "        obj = rng.choice(syms) ** rng.randint(0, 5)\n"
            "    elif c == 4:\n"
            "        obj = rng.choice(syms) * rng.randint(-10, 10)\n"
            "    elif c == 5:\n"
            "        obj = [rng.randint(0, 9) for _ in range(rng.randint(0, 4))]\n"
            "    else:\n"
            "        obj = ''.join(rng.choice('abc0&<> ') for _ in range(rng.randint(0, 6)))\n"
            "    if isinstance(obj, Vector):\n"
            "        continue\n"
            "    raised = False\n"
            "    try:\n"
            "        _check_vector(obj)\n"
            "    except TypeError:\n"
            "        raised = True\n"
            "    assert raised, ('vector_guard UNSOUND: fuzz non-Vector %r did "
            "NOT raise' % (obj,))\n"
            "    checked += 1\n"
            "print('AX-SOUND vector_guard ok: %d Vector inputs returned "
            "unchanged, %d scalar zeros raise, %d boundary non-Vectors + %d "
            "fuzz raise (== real _check_vector)' % (len(vectors), "
            "len(scalar_zeros), len(nonvectors), checked))\n"
            "sys.exit(0)\n"
        ),
        "rationale": "vector_guard (A-consumed) is the weakest contract the "
                     "proof needs: identity on a Vector, raise on a non-Vector. "
                     "The proof CONSUMES its Ensures (ToSeq(Result)==ToSeq(other), "
                     "is_vector) and Exsures (the not-a-vector raise -> clause "
                     "(3)). If the real _check_vector returned a non-Vector "
                     "unchanged or failed to raise on the scalar zero, the axiom "
                     "would be AXIOM-UNSOUND and the prepatch discriminator "
                     "(A.x + 0 crash) would be misvalidated.",
    },

    # --- normal_form / normalise : AXIOM-SOUNDNESS (== Vector.__init__) ------
    # Three directions ported from axiom_check.py:
    #   (i)  faithfulness: len(Vector(a.args + b.args).args) <= len(a.args) +
    #        len(b.args) on boundary pairs (>=3 strict merges) + 500 fuzz;
    #   (ii) tightness: the naive length-preservation over-claim is FALSIFIED by
    #        a same-frame merge (x*A.x + y*A.y collapses 2 -> 1);
    #   (iii) determinism + the F2P distinguisher: Vector is a function of its
    #        arg list, and Vector(v1.args + v2.args).args != Vector(v1.args).args
    #        for the F2P merge -- so normal_form(self ++ other) differs from
    #        normal_form(self) alone, which is exactly why the drop-other attacks
    #        fail clause (2). Any violation is AXIOM-UNSOUND.
    {
        "id": "ax-sound-normal-form",
        "axiom": "normal_form",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": (
            "import sys, random\n"
            "from sympy import symbols, S, sqrt\n"
            "from sympy.physics.vector import ReferenceFrame, Vector\n"
            "x, y, z = symbols('x y z')\n"
            "N = ReferenceFrame('N')\n"
            "A = N.orientnew('A', 'Axis', [x, N.x])\n"
            "zero = N.x - N.x\n"
            "def never_grows(a, b):\n"
            "    r = Vector(a.args + b.args)\n"
            "    assert len(r.args) <= len(a.args) + len(b.args), (\n"
            "        'normal_form UNSOUND: Vector(a.args+b.args) GREW (%d > %d + "
            "%d)' % (len(r.args), len(a.args), len(b.args)))\n"
            "    return len(r.args) < len(a.args) + len(b.args)\n"
            "def deterministic(a, b):\n"
            "    al = a.args + b.args\n"
            "    assert Vector(list(al)).args == Vector(list(al)).args, (\n"
            "        'normal_form UNSOUND: Vector not a function of its arg list')\n"
            "def distinguishes(a, b):\n"
            "    return Vector(a.args + b.args).args != Vector(list(a.args)).args\n"
            "base_pairs = [\n"
            "    (x*A.x + y*A.y + z*A.z, x**2*A.x + y**2*A.y + z**2*A.z),\n"
            "    (A.x, 0*A.x), (x*A.x, x**2*A.x), (x*A.x, (-x)*A.x),\n"
            "    (N.x, A.y), (N.x + N.y, A.z), (zero, zero), (N.x, N.x),\n"
            "    (x*N.x + y*N.y, x*N.x), (sqrt(2)*N.z, N.z)]\n"
            "n_merge = 0\n"
            "n_dist = 0\n"
            "for a, b in base_pairs:\n"
            "    assert isinstance(a, Vector) and isinstance(b, Vector)\n"
            "    if never_grows(a, b):\n"
            "        n_merge += 1\n"
            "    deterministic(a, b)\n"
            "    if distinguishes(a, b):\n"
            "        n_dist += 1\n"
            "# tightness: the naive length-preservation over-claim must be FALSE\n"
            "merged = Vector((x*A.x).args + (y*A.y).args)\n"
            "assert len(merged.args) < len((x*A.x).args) + len((y*A.y).args), (\n"
            "    'setup: expected a same-frame merge to strictly shrink')\n"
            "assert n_merge >= 3, ('setup: expected >=3 strict merges, saw %d; "
            "the <= bound would be vacuously == ' % n_merge)\n"
            "# the F2P distinguisher: combined != self-only on the F2P merge\n"
            "v1 = x*A.x + y*A.y + z*A.z\n"
            "v2 = x**2*A.x + y**2*A.y + z**2*A.z\n"
            "assert Vector(v1.args + v2.args).args != Vector(list(v1.args)).args, (\n"
            "    'normal_form UNSOUND: constructor did NOT distinguish v1+v2 from "
            "v1 alone -- the pinned post would admit return self')\n"
            "assert n_dist >= 3, ('setup: expected >=3 distinguishing pairs, saw "
            "%d' % n_dist)\n"
            "# randomized fuzz\n"
            "frames = [N, A]\n"
            "basis = {N: [N.x, N.y, N.z], A: [A.x, A.y, A.z]}\n"
            "coeffs = [x, y, z, S(1), S(2), S(-1), sqrt(2), x**2]\n"
            "rng = random.Random(20180512)\n"
            "def rand_vec():\n"
            "    v = zero\n"
            "    for _ in range(rng.randint(0, 4)):\n"
            "        fr = rng.choice(frames)\n"
            "        v = v + rng.choice(coeffs) * rng.choice(basis[fr])\n"
            "    return v\n"
            "for _ in range(500):\n"
            "    a, b = rand_vec(), rand_vec()\n"
            "    never_grows(a, b)\n"
            "    deterministic(a, b)\n"
            "print('AX-SOUND normal_form ok: never-grows on %d pairs (>=%d "
            "strict merges) + 500 fuzz; length-preservation over-claim falsified "
            "by a same-frame merge; constructor deterministic; "
            "normal_form(self++other) != normal_form(self) on %d pairs incl. the "
            "F2P merge (== real Vector.__init__)' % (len(base_pairs), n_merge, "
            "n_dist))\n"
            "sys.exit(0)\n"
        ),
        "rationale": "normal_form / normalise (A-reference) model Vector.__init__, "
                     "the frame-merging constructor. The content-bearing clause "
                     "(2) leans on (i) len(result) <= len(input) -- never invents "
                     "a component -- and (ii) determinism / the distinguisher "
                     "normal_form(self ++ other) != normal_form(self) that makes "
                     "the drop-other attacks fail. If the real constructor GREW "
                     "the arg list, or were non-deterministic, or did NOT "
                     "distinguish v1+v2 from v1, the axiom would be AXIOM-UNSOUND "
                     "and clause (2) would be misvalidated.",
    },

    # --- normal_form / normalise : caller-domain CONTAINMENT ----------------
    # The model passes normal_form / normalise exactly the sequence
    # ToSeq(self.terms) + ToSeq(other.terms) (the raw concatenation of two
    # in-domain component-family lists). normal_form's Requires is
    # unconstrained (any PSeq[int]); normalise's Requires is Acc(list_pred(terms),
    # 1/2) (any well-formed list). So every concatenation of two finite lists is
    # in-domain -- there is NO sub-domain the caller can reach that the axiom
    # excludes. We confirm the real Vector.__init__ ACCEPTS (never raises on)
    # every such concatenated argument list across boundary + fuzz pairs,
    # including the empty list and single-frame and mixed-frame concatenations.
    {
        "id": "ax-contain-normal-form",
        "axiom": "normal_form",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": (
            "import sys, random\n"
            "from sympy import symbols, S, sqrt\n"
            "from sympy.physics.vector import ReferenceFrame, Vector\n"
            "x, y, z = symbols('x y z')\n"
            "N = ReferenceFrame('N')\n"
            "A = N.orientnew('A', 'Axis', [x, N.x])\n"
            "zero = N.x - N.x\n"
            "# The model only ever constructs from a concatenation of two\n"
            "# in-domain term lists (ToSeq(self.terms) + ToSeq(other.terms)), plus\n"
            "# the empty list (Vec([]) edge). normal_form's domain is any PSeq; we\n"
            "# verify the REAL constructor accepts every such concatenated arg\n"
            "# list (never raises) -- so no caller-reachable input is outside the\n"
            "# axiom's Requires domain (AXIOM-TOO-WEAK-FOR-CALLER would be a raise).\n"
            "pairs = [\n"
            "    (x*A.x + y*A.y + z*A.z, x**2*A.x + y**2*A.y + z**2*A.z),\n"
            "    (A.x, 0*A.x), (x*A.x, x**2*A.x), (x*A.x, (-x)*A.x),\n"
            "    (N.x, A.y), (N.x + N.y, A.z), (zero, zero), (N.x, N.x),\n"
            "    (x*N.x + y*N.y, x*N.x), (sqrt(2)*N.z, N.z),\n"
            "    (zero, A.x), (A.x, zero)]\n"
            "raised = []\n"
            "# the empty-list edge (Vec([]) in the drop-other attack family,\n"
            "# and the zero-vector concatenation)\n"
            "try:\n"
            "    Vector([])\n"
            "except Exception as ex:\n"
            "    raised.append(('[]', type(ex).__name__))\n"
            "for a, b in pairs:\n"
            "    try:\n"
            "        Vector(a.args + b.args)\n"
            "        Vector(list(a.args))\n"
            "    except Exception as ex:\n"
            "        raised.append((repr(a), repr(b), type(ex).__name__))\n"
            "frames = [N, A]\n"
            "basis = {N: [N.x, N.y, N.z], A: [A.x, A.y, A.z]}\n"
            "coeffs = [x, y, z, S(1), S(2), S(-1), sqrt(2), x**2]\n"
            "rng = random.Random(147110)\n"
            "def rand_vec():\n"
            "    v = zero\n"
            "    for _ in range(rng.randint(0, 4)):\n"
            "        fr = rng.choice(frames)\n"
            "        v = v + rng.choice(coeffs) * rng.choice(basis[fr])\n"
            "    return v\n"
            "checked = 0\n"
            "for _ in range(500):\n"
            "    a, b = rand_vec(), rand_vec()\n"
            "    try:\n"
            "        Vector(a.args + b.args)\n"
            "    except Exception as ex:\n"
            "        raised.append(('fuzz', type(ex).__name__))\n"
            "    checked += 1\n"
            "assert not raised, ('caller-reachable arg list OUTSIDE normal_form "
            "domain (real Vector.__init__ raised): %r => AXIOM-TOO-WEAK-FOR-CALLER' "
            "% raised[:5])\n"
            "print('AX-CONTAIN normal_form ok: every caller-reachable arg list "
            "(concatenation of two in-domain term lists + the empty edge) is "
            "accepted by the real Vector.__init__ across %d boundary pairs + %d "
            "fuzz -- no reachable input outside the axiom domain' % (len(pairs), "
            "checked))\n"
            "sys.exit(0)\n"
        ),
        "rationale": "containment, not whole-domain coverage: the model passes "
                     "normal_form / normalise exactly ToSeq(self.terms) + "
                     "ToSeq(other.terms) (and the empty list for the Vec([]) "
                     "edge), all finite int-tag sequences, which lie in "
                     "normal_form's unconstrained PSeq domain / normalise's "
                     "list_pred domain. The real Vector.__init__ accepts every "
                     "such concatenation (never raises). A caller-reachable arg "
                     "list the constructor rejected would be "
                     "AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
