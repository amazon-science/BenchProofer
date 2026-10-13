# properties.py — PBT falsification battery for pydata__xarray-4966.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
# model.py variants that share the FROZEN spec (region-surgery: edits live ONLY
# inside the # impl-start / # impl-end region, which spec_view elides — so
# same_spec holds by construction) and are checked by Nagini verify; axiom cases
# are real-callee probes checked in Docker.
#
# DEFENDED SURFACE (what this spec protects — see model.py / refinement.md):
#
#   reconcile_signedness(data: List[int], kind, unsigned, modulus,
#                        has_fill, fill) -> List[int]
#     Requires Acc(list_pred(data), 1/2)               <-- READ-ONLY input (half perm)
#     Requires kind in {KIND_SIGNED(0), KIND_UNSIGNED(1)}
#     Requires unsigned in {ATTR_FALSE(0), ATTR_TRUE(1), ATTR_OTHER(2)}
#     Requires modulus >= 2
#     Ensures  Acc(list_pred(data), 1/2)               <-- frame: caller keeps its half
#     Ensures  Acc(list_pred(Result()))
#     Ensures  Implies(transform_to_signed(kind,unsigned),                 <-- LOAD-BEARING
#                 ToSeq(Result()) == reinterpret_seq(ToSeq(data), modulus, True))
#     Ensures  Implies(transform_to_unsigned(kind,unsigned),               <-- LOAD-BEARING
#                 ToSeq(Result()) == reinterpret_seq(ToSeq(data), modulus, False))
#     Ensures  Implies(not is_transformed(kind,unsigned),                  <-- LOAD-BEARING
#                 ToSeq(Result()) == ToSeq(data))
#     Ensures  three fill clauses (fill_out == reinterpret(fill,...) / fill)
#
#   reinterpret / reinterpret_seq / fill_out are @Pure folds GROUNDED ENTIRELY in
#   the inputs (fully unfoldable; NOT an opaque answer-key oracle). The
#   load-bearing equalities are checked against reinterpret_seq of the actual
#   `data` argument, so there is no "wrong ungrounded-oracle echo" to build: any
#   value an impl returns must equal reinterpret_seq of its own `data`. The
#   ungrounded-oracle class is therefore N/A (see 'assessment'); the cheapest
#   honest impl IS the gold per-element fold, so its positive control is a
#   branch-reorder (NOT a loop-direction flip — reinterpret_seq is front-recursive
#   and the gold proof is a backward fold; flipping would need an
#   f(a+b)==f(a)+f(b) lemma Nagini will not auto-discharge, pilot bug #3).
#
#   The three fill clauses are postconditions ABOUT fill_out (a @Pure spec-region
#   function); they reduce to fill_out's own definition and hold for ANY impl
#   (the impl never touches `fill`). They are spec-internal pins, not an impl
#   obligation, so there is no impl-level fill rival to build (see 'assessment').
#
#   BEHAVIOURAL DISCRIMINATOR (the bug fix, issue: signed-bytes-from-OPeNDAP):
#   an UNSIGNED-stored array (kind == "u") requested as SIGNED (_Unsigned ==
#   "false") must be reinterpreted to its signed view (the F2P witness: the
#   unsigned max iinfo.max -> -1, e.g. u8 255 -> -1). Pre-patch xarray lacked the
#   `elif data.dtype.kind == "u":` branch, so such an array fell through to the
#   warning/pass-through arm UNCHANGED. transform_to_signed + reinterpret_seq pin
#   that signed reinterpretation; model_prepatch.py reproduces the pass-through
#   miss and FAILS that clause (G-DIFF). The partial-domain rivals below ARE that
#   pre-patch / boundary-wrong behaviour.
#
#   No @ContractOnly axioms (meta.axioms == []). The element transform
#   (np.asarray(dtype=...) / dtype.type(...)) is the *changed* callee, modelled
#   DEEPLY (reinterpret / fill_out, an A-reference) and validated == the real
#   numpy callee out-of-band by axiom_check.py (G-AX): exhaustive 8+16 bit both
#   directions + boundaries 8/16/32/64 + 80000 fuzz + F2P max->-1 witnesses,
#   211636 checks, 0 violations. That established real-callee check IS the axiom
#   lane; re-encoding it as a Docker probe would duplicate, not strengthen, it.
#   Hence AXIOM_TESTS = []. See 'assessment'.
from pathlib import Path

INSTANCE = "pydata__xarray-4966"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ===========================================================================
# Anchor INSIDE the impl region (between # impl-start / # impl-end). Editing
# only this keeps spec_view (hence same_spec) byte-identical. The WHOLE impl
# body of reconcile_signedness is the unique anchor.
# ===========================================================================
_IMPL_GOLD = """    result = []  # type: List[int]
    if transform_to_signed(kind, unsigned):
        # unsigned-stored array, requested signed -> signed view of each element
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) ==
                      reinterpret_seq(ToSeq(data).drop(i), modulus, True))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [reinterpret(data[i - 1], modulus, True)] + result
            i = i - 1
    elif transform_to_unsigned(kind, unsigned):
        # signed-stored array, requested unsigned -> unsigned view of each elem
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) ==
                      reinterpret_seq(ToSeq(data).drop(i), modulus, False))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [reinterpret(data[i - 1], modulus, False)] + result
            i = i - 1
    else:
        # request matches storage or is absent/uninterpretable: pass through
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) == ToSeq(data).drop(i))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [data[i - 1]] + result
            i = i - 1
    return result"""

assert _IMPL_GOLD in _BASE, "impl anchor drift: reconcile_signedness body not verbatim"


# ===========================================================================
# (1) POSITIVE CONTROL — structurally different but CORRECT (verify).
# Reorder the dispatch branches: test transform_to_unsigned FIRST, then
# transform_to_signed, then the else pass-through. Each branch's backward loop,
# invariants and framing Asserts are kept VERBATIM (only the order of the three
# arms is swapped). The branch predicates transform_to_signed / transform_to_
# unsigned are mutually exclusive (a kind is either 0 or 1; a kind==0 array can
# only transform_to_unsigned, a kind==1 array only transform_to_signed), so the
# reorder is observationally identical. No loop-direction flip / fold lemma is
# introduced (pilot bug #3 avoided). If a faithful correct impl could NOT verify
# against this spec => SPEC-TOO-STRONG.
# ===========================================================================
_IMPL_POS = """    result = []  # type: List[int]
    if transform_to_unsigned(kind, unsigned):
        # signed-stored array, requested unsigned -> unsigned view of each elem
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) ==
                      reinterpret_seq(ToSeq(data).drop(i), modulus, False))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [reinterpret(data[i - 1], modulus, False)] + result
            i = i - 1
    elif transform_to_signed(kind, unsigned):
        # unsigned-stored array, requested signed -> signed view of each element
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) ==
                      reinterpret_seq(ToSeq(data).drop(i), modulus, True))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [reinterpret(data[i - 1], modulus, True)] + result
            i = i - 1
    else:
        # request matches storage or is absent/uninterpretable: pass through
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) == ToSeq(data).drop(i))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [data[i - 1]] + result
            i = i - 1
    return result"""

# ===========================================================================
# (2) ADMISSIBILITY — the precondition admits a normal F2P-shaped input (verify).
# Cannot add a top-level caller (that leaves the impl region and breaks
# same_spec). Instead, in-region: re-derive that the half-permission `data` input
# is usable (read its length and ToSeq) and that a normal (non-raising) return is
# reachable for an in-domain input, then run the gold body verbatim. If the
# Requires were vacuous / over-strong the impl could not both consume the
# half-permission and return => PRECOND-TOO-STRONG. The F2P scenario (kind ==
# KIND_UNSIGNED, unsigned == ATTR_FALSE, modulus a power of two >= 2, single
# element) satisfies every Requires conjunct, which the gold body then handles.
# ===========================================================================
_IMPL_ADMISS = """    # admissibility: the half-permission `data` input is readable and a normal
    # non-raising return is reachable for an in-domain (F2P-shaped) input.
    Assert(len(data) >= 0)                 # data half-perm readable
    Assert(ToSeq(data) == ToSeq(data))     # ToSeq(data) usable under Acc(.,1/2)
    Assert(modulus >= 2)                   # width precondition admitted
    Assert(kind == KIND_SIGNED or kind == KIND_UNSIGNED)
    Assert(unsigned == ATTR_FALSE or unsigned == ATTR_TRUE or
           unsigned == ATTR_OTHER)
    result = []  # type: List[int]
    if transform_to_signed(kind, unsigned):
        # unsigned-stored array, requested signed -> signed view of each element
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) ==
                      reinterpret_seq(ToSeq(data).drop(i), modulus, True))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [reinterpret(data[i - 1], modulus, True)] + result
            i = i - 1
    elif transform_to_unsigned(kind, unsigned):
        # signed-stored array, requested unsigned -> unsigned view of each elem
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) ==
                      reinterpret_seq(ToSeq(data).drop(i), modulus, False))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [reinterpret(data[i - 1], modulus, False)] + result
            i = i - 1
    else:
        # request matches storage or is absent/uninterpretable: pass through
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) == ToSeq(data).drop(i))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [data[i - 1]] + result
            i = i - 1
    return result"""

# ===========================================================================
# (3) FRAME-MUTATION — write to the read-only input `data` (reject). MANDATORY:
# reconcile_signedness holds only Acc(list_pred(data), 1/2). Inside the signed
# loop the index data[i-1] is known in-bounds (0 < i <= len(data)), so a WRITE
# data[i-1] = data[i-1] is well-typed and VALUE-NEUTRAL — yet a list write needs
# FULL permission. With only the half-permission the Requires grants, Nagini
# rejects for INSUFFICIENT PERMISSION. The gold invariants/asserts are kept
# VERBATIM so the rejection is attributable to the write, not to a spec change.
# A byte-fuzzer never thinks to mutate the input; this is the project's #1
# weakness class.
# ===========================================================================
_IMPL_FRAME = """    result = []  # type: List[int]
    if transform_to_signed(kind, unsigned):
        # unsigned-stored array, requested signed -> signed view of each element
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) ==
                      reinterpret_seq(ToSeq(data).drop(i), modulus, True))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            # FRAME MUTATION: write back into the read-only half-permission input.
            data[i - 1] = data[i - 1]
            result = [reinterpret(data[i - 1], modulus, True)] + result
            i = i - 1
    elif transform_to_unsigned(kind, unsigned):
        # signed-stored array, requested unsigned -> unsigned view of each elem
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) ==
                      reinterpret_seq(ToSeq(data).drop(i), modulus, False))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [reinterpret(data[i - 1], modulus, False)] + result
            i = i - 1
    else:
        # request matches storage or is absent/uninterpretable: pass through
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) == ToSeq(data).drop(i))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [data[i - 1]] + result
            i = i - 1
    return result"""

# ===========================================================================
# (4) PARTIAL-DOMAIN / boundary off-by-one (reject). In the signed branch,
# inline a reinterpretation with a STRICT `>` half-range test
# (v - modulus if v > modulus // 2 else v) instead of the gold `>=`. This agrees
# with reinterpret on every value EXCEPT the exact half-range value
# v == modulus // 2, which the gold folds to v - modulus (the signed minimum,
# e.g. u8 128 -> -128) but this leaves UNCHANGED at +modulus//2. On any array
# whose element equals modulus//2 the per-step invariant
# ToSeq(result) == reinterpret_seq(ToSeq(data).drop(i), modulus, True) can no
# longer be re-established, so the load-bearing transform_to_signed postcondition
# fails => Nagini rejects. A pure value-domain miss a byte-fuzzer (which only
# corrupts structure) never targets.
# ===========================================================================
_IMPL_BOUNDARY = """    result = []  # type: List[int]
    if transform_to_signed(kind, unsigned):
        # unsigned-stored array, requested signed -> signed view of each element
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) ==
                      reinterpret_seq(ToSeq(data).drop(i), modulus, True))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            # BOUNDARY OFF-BY-ONE: strict `>` instead of `>=` at the half-range.
            if data[i - 1] > modulus // 2:
                folded = data[i - 1] - modulus  # type: int
            else:
                folded = data[i - 1]
            result = [folded] + result
            i = i - 1
    elif transform_to_unsigned(kind, unsigned):
        # signed-stored array, requested unsigned -> unsigned view of each elem
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) ==
                      reinterpret_seq(ToSeq(data).drop(i), modulus, False))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [reinterpret(data[i - 1], modulus, False)] + result
            i = i - 1
    else:
        # request matches storage or is absent/uninterpretable: pass through
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) == ToSeq(data).drop(i))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [data[i - 1]] + result
            i = i - 1
    return result"""

# ===========================================================================
# (5) PARTIAL-DOMAIN / first-element pass-through (reject). In the signed branch,
# leave the element at index 0 UNCHANGED (when i == 1, push data[0] not its
# signed view); every other element is reinterpreted correctly. This is the
# pre-patch miss restricted to the leading element: the F2P arrays are
# single-element [iinfo.max] at index 0, so the one element that decides the test
# is exactly the one this rival fails to fold (max stays max instead of -> -1).
# At loop exit ToSeq(result) != reinterpret_seq(ToSeq(data), modulus, True) on any
# array whose element 0 needs folding, so the load-bearing transform_to_signed
# postcondition fails => Nagini rejects.
# ===========================================================================
_IMPL_FIRSTELT = """    result = []  # type: List[int]
    if transform_to_signed(kind, unsigned):
        # unsigned-stored array, requested signed -> signed view of each element
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) ==
                      reinterpret_seq(ToSeq(data).drop(i), modulus, True))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            # FIRST-ELEMENT PASS-THROUGH: leave index 0 unfolded.
            if i == 1:
                folded = data[i - 1]  # type: int
            else:
                folded = reinterpret(data[i - 1], modulus, True)
            result = [folded] + result
            i = i - 1
    elif transform_to_unsigned(kind, unsigned):
        # signed-stored array, requested unsigned -> unsigned view of each elem
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) ==
                      reinterpret_seq(ToSeq(data).drop(i), modulus, False))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [reinterpret(data[i - 1], modulus, False)] + result
            i = i - 1
    else:
        # request matches storage or is absent/uninterpretable: pass through
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) == ToSeq(data).drop(i))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [data[i - 1]] + result
            i = i - 1
    return result"""

# ===========================================================================
# (6) PASS-THROUGH-COLLAPSE / the actual pre-patch bug (reject). Replace the
# signed-transform branch body with a verbatim PASS-THROUGH (return the elements
# unchanged), exactly what pre-patch xarray did for an unsigned-stored array
# (it had no `kind == "u"` branch and fell through to the warning arm). This is
# the model_prepatch.py behaviour. The transform_to_signed postcondition demands
# ToSeq(Result()) == reinterpret_seq(ToSeq(data), modulus, True), but the impl
# yields ToSeq(data); identity != signed reinterpretation whenever any element
# needs folding (the F2P witness max -> -1), so Nagini rejects.
# ===========================================================================
_IMPL_PREPATCH = """    result = []  # type: List[int]
    if transform_to_signed(kind, unsigned):
        # PRE-PATCH MISS: unsigned-stored, requested signed left UNCHANGED.
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) == ToSeq(data).drop(i))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [data[i - 1]] + result
            i = i - 1
    elif transform_to_unsigned(kind, unsigned):
        # signed-stored array, requested unsigned -> unsigned view of each elem
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) ==
                      reinterpret_seq(ToSeq(data).drop(i), modulus, False))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [reinterpret(data[i - 1], modulus, False)] + result
            i = i - 1
    else:
        # request matches storage or is absent/uninterpretable: pass through
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) == ToSeq(data).drop(i))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [data[i - 1]] + result
            i = i - 1
    return result"""

# ===========================================================================
# (7) DIRECTION-SWAP (reject). Keep the dispatch but produce the WRONG view:
# in the transform_to_signed branch produce the UNSIGNED view
# (reinterpret(..., False)) instead of the signed view. This passes the spec only
# for arrays already in the signed range; on the F2P witness (max -> must be -1)
# the unsigned view is the identity, so ToSeq(Result()) == ToSeq(data) !=
# reinterpret_seq(..., True). The load-bearing transform_to_signed postcondition
# (which pins the to_signed=True fold) fails => Nagini rejects.
# ===========================================================================
_IMPL_DIRSWAP = """    result = []  # type: List[int]
    if transform_to_signed(kind, unsigned):
        # DIRECTION SWAP: produce the UNSIGNED view in the signed branch.
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) ==
                      reinterpret_seq(ToSeq(data).drop(i), modulus, False))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [reinterpret(data[i - 1], modulus, False)] + result
            i = i - 1
    elif transform_to_unsigned(kind, unsigned):
        # signed-stored array, requested unsigned -> unsigned view of each elem
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) ==
                      reinterpret_seq(ToSeq(data).drop(i), modulus, False))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [reinterpret(data[i - 1], modulus, False)] + result
            i = i - 1
    else:
        # request matches storage or is absent/uninterpretable: pass through
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) == ToSeq(data).drop(i))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [data[i - 1]] + result
            i = i - 1
    return result"""


SPEC_TESTS = [
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_POS),
        "rationale": "Structurally different but correct: the three dispatch arms "
                     "are reordered (transform_to_unsigned tested first, then "
                     "transform_to_signed, then else). transform_to_signed and "
                     "transform_to_unsigned are mutually exclusive (kind is 0 xor 1), "
                     "so the reorder is observationally identical; each branch's "
                     "backward loop, invariants and framing Asserts are kept verbatim. "
                     "No loop-direction flip / fold lemma is introduced (reinterpret_seq "
                     "is front-recursive and the proof is a backward fold). Must verify, "
                     "else SPEC-TOO-STRONG.",
    },
    {
        "id": "admissibility-readonly-data",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_ADMISS),
        "rationale": "Re-derives in-region that the half-permission `data` input is "
                     "usable (read via len / ToSeq under Acc(.,1/2)) and that every "
                     "Requires conjunct (kind, unsigned, modulus>=2) is satisfiable for "
                     "an F2P-shaped input, then runs the gold body to a normal return. "
                     "If any Requires were vacuous or over-strong the impl could not "
                     "both consume the permission and return => PRECOND-TOO-STRONG. "
                     "Source: the four Requires conjuncts + the Acc(.,1/2) on data.",
    },
    {
        "id": "frame-mutation-write-data",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_FRAME),
        "refinement": "A faithful real patch in which the decode wrote back into the "
                      "incoming numpy array in place (e.g. data[...] = view instead of "
                      "data = lazy_elemwise_func(data, transform, signed_dtype)) would "
                      "mutate the caller's original array. The F2P test "
                      "test_decode_signed_from_unsigned holds `original_values` and "
                      "asserts `decoded.values == original_values` for the UNSIGNED-"
                      "stored encode side; the gold patch builds a NEW lazy array and "
                      "never touches the stored array, so an in-place mutating helper "
                      "would corrupt the array the test reuses and would not faithfully "
                      "resolve the F2P.",
        "rationale": "reconcile_signedness holds only Acc(list_pred(data), 1/2). The "
                     "write data[i-1] = data[i-1] (value-neutral, in-bounds via the "
                     "loop bound) needs FULL permission => Nagini rejects for "
                     "INSUFFICIENT PERMISSION. Source: the permission system + the "
                     "Acc(list_pred(data), 1/2) Requires/Ensures frame. Gold "
                     "invariants/asserts kept verbatim so the rejection is attributable "
                     "to the write, not a spec change.",
    },
    {
        "id": "partial-domain-boundary-off-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_BOUNDARY),
        "refinement": "A faithful real patch whose signed reinterpretation used a "
                      "strict `>` half-range test would map the exact half-range value "
                      "modulus//2 to itself instead of to the signed minimum "
                      "-modulus//2 (e.g. for u8, value 128 stays 128 instead of "
                      "becoming -128, which is what np.asarray(dtype='i1') produces). "
                      "Any decoded array containing the half-range value would then "
                      "disagree with numpy's real fixed-width reinterpretation, so the "
                      "patch does not faithfully resolve (the values would be wrong on "
                      "that sub-domain).",
        "rationale": "Inlining `data[i-1] - modulus if data[i-1] > modulus // 2 else "
                     "data[i-1]` diverges from reinterpret at v == modulus//2; the "
                     "per-step invariant ToSeq(result) == reinterpret_seq(..., True) "
                     "can no longer be re-established, so the load-bearing "
                     "transform_to_signed postcondition fails => reject. Source: the "
                     "transform_to_signed postcondition clause via reinterpret_seq.",
    },
    {
        "id": "partial-domain-first-element",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_FIRSTELT),
        "refinement": "A faithful real patch that folded every element except the "
                      "first would leave element 0 unsigned. The F2P arrays are "
                      "single-element ([iinfo.max] -> must decode to -1), so the one "
                      "element deciding the test is exactly the one left unfolded: the "
                      "decoded value would be iinfo.max, not -1, and "
                      "test_decode_signed_from_unsigned would FAIL — the patch does not "
                      "resolve.",
        "rationale": "When i == 1 the index-0 element is pushed unchanged "
                     "(data[i-1]) instead of reinterpret(data[i-1], modulus, True); at "
                     "loop exit ToSeq(result) != reinterpret_seq(ToSeq(data), modulus, "
                     "True) whenever element 0 needs folding, so the load-bearing "
                     "transform_to_signed postcondition fails => reject. Source: the "
                     "transform_to_signed postcondition clause.",
    },
    {
        "id": "prepatch-passthrough-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_PREPATCH),
        "refinement": "This IS the pre-patch behaviour (model_prepatch.py): xarray had "
                      "no `elif data.dtype.kind == 'u':` branch, so an unsigned-stored "
                      "array requested signed (_Unsigned == 'false') fell through to the "
                      "SerializationWarning arm and was returned UNCHANGED (still "
                      "unsigned). The F2P test_decode_signed_from_unsigned reads "
                      "decoded.values and asserts the signed view (max -> -1); a "
                      "pass-through leaves the unsigned bit pattern, so the test FAILS "
                      "and the patch does not resolve. This is exactly the spec sensing "
                      "the change (G-DIFF).",
        "rationale": "The transform_to_signed branch is replaced by a pass-through "
                     "(invariant ToSeq(result) == ToSeq(data).drop(i)); the "
                     "load-bearing postcondition demands ToSeq(Result()) == "
                     "reinterpret_seq(ToSeq(data), modulus, True), and identity != "
                     "signed reinterpretation whenever any element needs folding => "
                     "reject. Source: the transform_to_signed postcondition clause.",
    },
    {
        "id": "direction-swap-unsigned-in-signed-branch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_DIRSWAP),
        "refinement": "A faithful real patch that, in the new kind=='u' / "
                      "unsigned=='false' branch, reinterpreted to the UNSIGNED dtype "
                      "(np.asarray(dtype='u%s')) instead of the signed dtype would be a "
                      "no-op on the already-unsigned stored array, leaving the values "
                      "unchanged (max stays max). decoded.values would not be the signed "
                      "view (-1), so test_decode_signed_from_unsigned FAILS and the "
                      "patch does not resolve. (It also produces the wrong "
                      "decoded.dtype, but the value abstraction already catches the "
                      "element divergence.)",
        "rationale": "The signed branch produces reinterpret(..., False) (unsigned "
                     "view) but the postcondition for transform_to_signed pins "
                     "reinterpret_seq(..., True) (signed view); these disagree whenever "
                     "an element is >= modulus//2 (the F2P witness), so the load-bearing "
                     "transform_to_signed postcondition fails => reject. Source: the "
                     "to_signed direction of the transform_to_signed postcondition.",
    },
]

# No Docker AXIOM_TESTS: meta.axioms == [] (no @ContractOnly axiom; the axioms
# region is empty). The element transform (numpy.asarray(dtype=...) /
# np.dtype(...).type(fill)) is the *changed* callee, modelled DEEPLY as an
# A-reference (reinterpret / reinterpret_seq / fill_out in the pure region) and
# already validated == the real numpy callee out-of-band by axiom_check.py
# (G-AX): exhaustive 8+16 bit both directions + boundaries 8/16/32/64 + 80000
# fuzz + F2P max->-1 witnesses, 211636 checks, 0 violations, numpy-only imports,
# exit 0. That established real-callee check IS the axiom lane for this instance;
# re-encoding it as a Docker probe would duplicate, not strengthen, it. See
# 'assessment' in the structured return.
AXIOM_TESTS = []
