# properties.py — PBT manifest for django__django-16642. NOT a Nagini module;
# a record of adversarial cases. The runner (swebench_nagini.pbt) executes each
# and stamps RESULT.
#
# Defended surface (read from model.py / refinement.md / mapping.md):
#   select_content_type(content_type: List[int], encoding: List[int]) -> List[int]
#   models the post-patch table lookup
#     content_type = {"br":"application/x-brotli", "bzip2":"application/x-bzip",
#                     "compress":"application/x-compress", "gzip":"application/gzip",
#                     "xz":"application/x-xz"}.get(encoding, content_type)
#   inside FileResponse.set_headers.
#
#   BOTH inputs are READ-ONLY:  Requires(Acc(list_pred(content_type), 1/2))
#                               Requires(Acc(list_pred(encoding),     1/2))
#   so a frame-mutation rival (write to a half-permission input) is MANDATORY.
#
#   The load-bearing postcondition is the conjunction of
#     (a) ToSeq(Result()) == resolved_type(ToSeq(content_type), ToSeq(encoding))
#     (b) five Implies clauses pinning each recognised scheme to its EXACT
#         dedicated content type (the two NEW keys "br","compress" carry the fix)
#     (c) Implies(not is_known_encoding(...), ToSeq(Result()) == ToSeq(content_type))
#         — the passthrough of the guessed type for any other encoding.
#
#   The @Pure oracle resolved_type/dedicated_type/is_known_encoding is FULLY
#   GROUNDED in the inputs (a finite, fully-unfolded case split over PSeq literal
#   equality of enc against the five literal tokens). It is NOT an opaque
#   answer-key: there is no "wrong value" to echo — any value equal to
#   resolved_type(...) IS the correct output. So there is no ungrounded-oracle
#   echo break here; instead an honest cheapest-impl positive control is given
#   (echo-grounded), see pos-echo-grounded. (Stated again in assessment.)
#
#   No @ContractOnly axioms, no A-reference deep models (meta.axioms == []),
#   so AXIOM_TESTS == [].
from pathlib import Path

INSTANCE = "django__django-16642"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The frozen impl region (everything between # impl-start and # impl-end). All
# variants are produced by editing ONLY text inside this region, so same_spec
# is preserved (spec_view elides the whole impl block, invariants included).
# ---------------------------------------------------------------------------

_IMPL = '''    enc = ToSeq(encoding)
    if enc == tok_br():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 114, 111, 116, 108, 105]
    if enc == tok_bzip2():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 122, 105, 112]
    if enc == tok_compress():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115]
    if enc == tok_gzip():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 103, 122, 105, 112]
    if enc == tok_xz():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 120, 122]
    result = []  # type: List[int]
    i = 0
    while i < len(content_type):
        # invariants-start
        Invariant(Acc(list_pred(content_type), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(content_type))
        Invariant(ToSeq(result) == ToSeq(content_type).take(i))
        Invariant(MustTerminate(len(content_type) - i + 1))
        # invariants-end
        result = result + [content_type[i]]
        Assert(ToSeq(content_type).take(i) + PSeq(content_type[i])
               == ToSeq(content_type).take(i + 1))
        i = i + 1
    Assert(ToSeq(content_type).take(len(content_type)) == ToSeq(content_type))
    return result'''

# Sanity: the frozen impl text must appear verbatim in model.py (guards drift).
assert _IMPL in _BASE, "drift: frozen _IMPL not found verbatim in model.py"


def _with_impl(new_impl):
    return _swap(_BASE, _IMPL, new_impl)


# ===========================================================================
# 1. FRAME-MUTATION  (MANDATORY — both inputs are Acc(...,1/2) read-only)
# ===========================================================================
# A rival that WRITES to the read-only input `content_type` to build the
# passthrough result in place. The gold postcondition keeps every Ensures
# verbatim (it lives in the frozen spec view); the write must be rejected for
# INSUFFICIENT PERMISSION (the impl holds only 1/2 of list_pred(content_type),
# which does not permit mutation). If it verified, the read-only frame would be
# unenforced. Refinement: a real set_headers that mutated the guessed
# content_type list in place would corrupt the shared (content_type, encoding)
# pair guess_type returned — observably wrong for any later reader of that pair
# and not what the gold one-line dict.get patch does — so it would not be a
# faithful resolving patch.
_FRAME_MUT = '''    enc = ToSeq(encoding)
    if enc == tok_br():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 114, 111, 116, 108, 105]
    if enc == tok_bzip2():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 122, 105, 112]
    if enc == tok_compress():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115]
    if enc == tok_gzip():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 103, 122, 105, 112]
    if enc == tok_xz():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 120, 122]
    # FRAME VIOLATION: mutate the read-only half-permission input in place.
    i = 0
    while i < len(content_type):
        # invariants-start
        Invariant(Acc(list_pred(content_type)))
        Invariant(0 <= i and i <= len(content_type))
        Invariant(MustTerminate(len(content_type) - i + 1))
        # invariants-end
        content_type[i] = content_type[i]
        i = i + 1
    return content_type'''


# ===========================================================================
# 2. PARTIAL-DOMAIN — drop the NEW "br" key  (the discriminating fix #1)
# ===========================================================================
# Removes the tok_br() branch so a "br" encoding falls through to the
# content_type passthrough loop — returning the guessed type instead of
# application/x-brotli. This is EXACTLY the pre-patch bug for *.br. Must be
# rejected by Ensures(Implies(ToSeq(encoding)==tok_br(), Result==ct_brotli()))
# and by the resolved_type clause. Refinement: a real patch that omitted the
# "br" key is model_prepatch.py's behaviour; the F2P test_compressed_response
# row (".tar.br" -> "application/x-brotli") fails, so it does NOT resolve.
_DROP_BR = '''    enc = ToSeq(encoding)
    if enc == tok_bzip2():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 122, 105, 112]
    if enc == tok_compress():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115]
    if enc == tok_gzip():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 103, 122, 105, 112]
    if enc == tok_xz():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 120, 122]
    result = []  # type: List[int]
    i = 0
    while i < len(content_type):
        # invariants-start
        Invariant(Acc(list_pred(content_type), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(content_type))
        Invariant(ToSeq(result) == ToSeq(content_type).take(i))
        Invariant(MustTerminate(len(content_type) - i + 1))
        # invariants-end
        result = result + [content_type[i]]
        Assert(ToSeq(content_type).take(i) + PSeq(content_type[i])
               == ToSeq(content_type).take(i + 1))
        i = i + 1
    Assert(ToSeq(content_type).take(len(content_type)) == ToSeq(content_type))
    return result'''


# ===========================================================================
# 3. PARTIAL-DOMAIN — drop the NEW "compress" key  (the discriminating fix #2)
# ===========================================================================
# Removes the tok_compress() branch so a "compress" encoding (from *.Z) falls
# through to the guessed type. Must be rejected by Ensures(Implies(
# ToSeq(encoding)==tok_compress(), Result==ct_compress())). Refinement: omitting
# the "compress" key is the other half of the pre-patch bug; the F2P row
# (".tar.Z" -> "application/x-compress") fails, so it does NOT resolve.
_DROP_COMPRESS = '''    enc = ToSeq(encoding)
    if enc == tok_br():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 114, 111, 116, 108, 105]
    if enc == tok_bzip2():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 122, 105, 112]
    if enc == tok_gzip():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 103, 122, 105, 112]
    if enc == tok_xz():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 120, 122]
    result = []  # type: List[int]
    i = 0
    while i < len(content_type):
        # invariants-start
        Invariant(Acc(list_pred(content_type), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(content_type))
        Invariant(ToSeq(result) == ToSeq(content_type).take(i))
        Invariant(MustTerminate(len(content_type) - i + 1))
        # invariants-end
        result = result + [content_type[i]]
        Assert(ToSeq(content_type).take(i) + PSeq(content_type[i])
               == ToSeq(content_type).take(i + 1))
        i = i + 1
    Assert(ToSeq(content_type).take(len(content_type)) == ToSeq(content_type))
    return result'''


# ===========================================================================
# 4. VALUE-SWAP — return the wrong dedicated type for "br"
# ===========================================================================
# Returns ct_bzip()'s bytes for a "br" encoding instead of ct_brotli(). Wrong
# only on the "br" sub-domain. Must be rejected by Ensures(Implies(
# ToSeq(encoding)==tok_br(), Result==ct_brotli())) (the bytes differ:
# .../x-brotli vs .../x-bzip). Refinement: a real patch mapping "br" to
# "application/x-bzip" serves a brotli payload under the bzip content type; the
# F2P row (".tar.br" -> "application/x-brotli") fails, so it does NOT resolve.
_SWAP_BR_VALUE = '''    enc = ToSeq(encoding)
    if enc == tok_br():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 122, 105, 112]
    if enc == tok_bzip2():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 122, 105, 112]
    if enc == tok_compress():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115]
    if enc == tok_gzip():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 103, 122, 105, 112]
    if enc == tok_xz():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 120, 122]
    result = []  # type: List[int]
    i = 0
    while i < len(content_type):
        # invariants-start
        Invariant(Acc(list_pred(content_type), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(content_type))
        Invariant(ToSeq(result) == ToSeq(content_type).take(i))
        Invariant(MustTerminate(len(content_type) - i + 1))
        # invariants-end
        result = result + [content_type[i]]
        Assert(ToSeq(content_type).take(i) + PSeq(content_type[i])
               == ToSeq(content_type).take(i + 1))
        i = i + 1
    Assert(ToSeq(content_type).take(len(content_type)) == ToSeq(content_type))
    return result'''


# ===========================================================================
# 5. PASSTHROUGH CORRUPTION — return the encoding instead of the guessed type
# ===========================================================================
# For an unrecognised encoding, returns a copy of `encoding` rather than a copy
# of `content_type`. Must be rejected by Ensures(Implies(
# not is_known_encoding(ToSeq(encoding)), Result==ToSeq(content_type))) and the
# resolved_type clause (which returns content_type on the default branch).
# Refinement: a real dict.get(encoding, encoding) returns the encoding token as
# the content type for every non-compressed file — every P2P content-type test
# (e.g. test_content_type_file expecting "text/plain") would fail, so it does
# NOT resolve.
_PASSTHROUGH_ENC = '''    enc = ToSeq(encoding)
    if enc == tok_br():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 114, 111, 116, 108, 105]
    if enc == tok_bzip2():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 122, 105, 112]
    if enc == tok_compress():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115]
    if enc == tok_gzip():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 103, 122, 105, 112]
    if enc == tok_xz():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 120, 122]
    result = []  # type: List[int]
    i = 0
    while i < len(encoding):
        # invariants-start
        Invariant(Acc(list_pred(encoding), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(encoding))
        Invariant(ToSeq(result) == ToSeq(encoding).take(i))
        Invariant(MustTerminate(len(encoding) - i + 1))
        # invariants-end
        result = result + [encoding[i]]
        Assert(ToSeq(encoding).take(i) + PSeq(encoding[i])
               == ToSeq(encoding).take(i + 1))
        i = i + 1
    Assert(ToSeq(encoding).take(len(encoding)) == ToSeq(encoding))
    return result'''


# ===========================================================================
# 6. POSITIVE CONTROL (soundness) — structurally-different CORRECT impl
# ===========================================================================
# Reorders the branch chain (xz, gzip, compress, bzip2, br — the reverse of the
# gold order) and reshapes the passthrough loop (count-down construction of the
# prefix is NOT used; instead a forward index but with a local-variable reshape
# `n = len(content_type)` and the SAME gold loop invariants/asserts kept
# verbatim). Branch order is irrelevant to the disjoint-key case split, so this
# is observationally identical to gold and MUST verify (else SPEC-TOO-STRONG).
# The gold prefix-preservation invariant and the per-element append Assert are
# preserved exactly so the loop proof still discharges.
_POS_CONTROL = '''    enc = ToSeq(encoding)
    if enc == tok_xz():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 120, 122]
    if enc == tok_gzip():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 103, 122, 105, 112]
    if enc == tok_compress():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115]
    if enc == tok_bzip2():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 122, 105, 112]
    if enc == tok_br():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 114, 111, 116, 108, 105]
    out = []  # type: List[int]
    n = len(content_type)
    j = 0
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(content_type), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(n == len(content_type))
        Invariant(0 <= j and j <= len(content_type))
        Invariant(ToSeq(out) == ToSeq(content_type).take(j))
        Invariant(MustTerminate(n - j + 1))
        # invariants-end
        out = out + [content_type[j]]
        Assert(ToSeq(content_type).take(j) + PSeq(content_type[j])
               == ToSeq(content_type).take(j + 1))
        j = j + 1
    Assert(ToSeq(content_type).take(len(content_type)) == ToSeq(content_type))
    return out'''


# ===========================================================================
# 7. POSITIVE CONTROL (cheapest grounded "echo") — return resolved_type via the
#    same case split but built positively from the oracle's structure
# ===========================================================================
# Honest cheapest-impl control (the oracle is GROUNDED, so the "echo" is the
# correct value, not a wrong answer-key). Builds the result for the five
# recognised schemes by returning the dedicated content type code points
# directly (same as gold) and for the default branch copies content_type with
# the gold loop. This is the gold impl with the five recognised branches
# rewritten to use the exact same byte literals but is otherwise a trivially
# correct variant kept to confirm the spec ADMITS the straightforward impl
# (else SPEC-TOO-STRONG). Identical loop shape, kept invariants.
_POS_ECHO = '''    enc = ToSeq(encoding)
    if is_known_encoding(enc):
        if enc == tok_br():
            return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                    47, 120, 45, 98, 114, 111, 116, 108, 105]
        if enc == tok_bzip2():
            return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                    47, 120, 45, 98, 122, 105, 112]
        if enc == tok_compress():
            return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                    47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115]
        if enc == tok_gzip():
            return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                    47, 103, 122, 105, 112]
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 120, 122]
    result = []  # type: List[int]
    i = 0
    while i < len(content_type):
        # invariants-start
        Invariant(Acc(list_pred(content_type), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(content_type))
        Invariant(ToSeq(result) == ToSeq(content_type).take(i))
        Invariant(MustTerminate(len(content_type) - i + 1))
        # invariants-end
        result = result + [content_type[i]]
        Assert(ToSeq(content_type).take(i) + PSeq(content_type[i])
               == ToSeq(content_type).take(i + 1))
        i = i + 1
    Assert(ToSeq(content_type).take(len(content_type)) == ToSeq(content_type))
    return result'''


# ===========================================================================
# 8. ADMISSIBILITY — confirm the precondition admits an F2P-shaped input
# ===========================================================================
# A self-call caller exercising the modeled function on a concrete F2P-shaped
# input: encoding == "br" (code points [98,114]) and content_type == "text/html"
# (the regressing case from the problem statement). It establishes the two
# Acc(...,1/2) Requires for freshly-built lists and asserts the result equals
# the brotli content type. If the Requires could not be established for this
# normal input => PRECOND-TOO-STRONG.
_ADMISS = '''    enc = ToSeq(encoding)
    if enc == tok_br():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 114, 111, 116, 108, 105]
    if enc == tok_bzip2():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 122, 105, 112]
    if enc == tok_compress():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115]
    if enc == tok_gzip():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 103, 122, 105, 112]
    if enc == tok_xz():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 120, 122]
    result = []  # type: List[int]
    i = 0
    while i < len(content_type):
        # invariants-start
        Invariant(Acc(list_pred(content_type), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(content_type))
        Invariant(ToSeq(result) == ToSeq(content_type).take(i))
        Invariant(MustTerminate(len(content_type) - i + 1))
        # invariants-end
        result = result + [content_type[i]]
        Assert(ToSeq(content_type).take(i) + PSeq(content_type[i])
               == ToSeq(content_type).take(i + 1))
        i = i + 1
    Assert(ToSeq(content_type).take(len(content_type)) == ToSeq(content_type))
    return result


def _admiss_caller() -> None:
    # content_type "text/html" = [116,101,120,116,47,104,116,109,108]
    # encoding "br" = [98, 114]
    ct = [116, 101, 120, 116, 47, 104, 116, 109, 108]  # type: List[int]
    enc = [98, 114]  # type: List[int]
    Assert(ToSeq(enc) == tok_br())
    r = select_content_type(ct, enc)
    Assert(ToSeq(r) == ct_brotli())'''


SPEC_TESTS = [
    {
        "id": "frame-mut-write-input",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_FRAME_MUT),
        "refinement": (
            "Mutating the read-only guessed content_type list in place corrupts "
            "the (content_type, encoding) pair guess_type returned and is not the "
            "gold one-line dict.get patch; any later reader of that pair observes "
            "the corruption, so it is not a faithful resolving patch."
        ),
        "rationale": (
            "The impl holds only Acc(list_pred(content_type), 1/2); writing "
            "content_type[i] requires full permission, so Nagini rejects this for "
            "INSUFFICIENT PERMISSION. Comes from the permission system on the "
            "read-only Requires (frame condition)."
        ),
    },
    {
        "id": "drop-br-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_DROP_BR),
        "refinement": (
            "Omitting the 'br' key is the pre-patch behaviour (model_prepatch.py); "
            "the F2P test_compressed_response row '.tar.br' -> "
            "'application/x-brotli' fails, so a real patch like this does NOT "
            "resolve."
        ),
        "rationale": (
            "Rejected by Ensures(Implies(ToSeq(encoding)==tok_br(), "
            "ToSeq(Result())==ct_brotli())) and the resolved_type clause: for 'br' "
            "the impl returns the content_type copy but the postcondition demands "
            "ct_brotli()."
        ),
    },
    {
        "id": "drop-compress-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_DROP_COMPRESS),
        "refinement": (
            "Omitting the 'compress' key is the other half of the pre-patch bug; "
            "the F2P row '.tar.Z' -> 'application/x-compress' fails, so a real "
            "patch like this does NOT resolve."
        ),
        "rationale": (
            "Rejected by Ensures(Implies(ToSeq(encoding)==tok_compress(), "
            "ToSeq(Result())==ct_compress())): for 'compress' the impl returns the "
            "content_type copy but the postcondition demands ct_compress()."
        ),
    },
    {
        "id": "swap-br-value-to-bzip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_SWAP_BR_VALUE),
        "refinement": (
            "Mapping 'br' to 'application/x-bzip' serves a brotli payload under "
            "the bzip content type; the F2P row '.tar.br' -> "
            "'application/x-brotli' fails, so a real patch like this does NOT "
            "resolve."
        ),
        "rationale": (
            "Rejected by Ensures(Implies(ToSeq(encoding)==tok_br(), "
            "ToSeq(Result())==ct_brotli())): ct_brotli() (.../x-brotli) and "
            "ct_bzip() (.../x-bzip) differ byte-for-byte."
        ),
    },
    {
        "id": "passthrough-returns-encoding",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_PASSTHROUGH_ENC),
        "refinement": (
            "Returning the encoding token instead of the guessed content type for "
            "non-compressed files (dict.get(encoding, encoding)) breaks every "
            "P2P content-type test (e.g. test_content_type_file expecting "
            "'text/plain'), so a real patch like this does NOT resolve."
        ),
        "rationale": (
            "Rejected by Ensures(Implies(not is_known_encoding(ToSeq(encoding)), "
            "ToSeq(Result())==ToSeq(content_type))) and the resolved_type default "
            "branch: the impl returns a copy of encoding, not content_type."
        ),
    },
    {
        "id": "pos-reorder-branches-reshape-loop",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(_POS_CONTROL),
        "rationale": (
            "Reversed branch order (disjoint literal keys, so order is irrelevant) "
            "plus a local-variable reshape of the passthrough loop (n=len(...)), "
            "keeping the gold prefix-preservation invariant and per-element append "
            "Assert verbatim. Observationally identical to gold; must verify, else "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-echo-grounded-oracle",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(_POS_ECHO),
        "rationale": (
            "Honest cheapest grounded-oracle control: gates the five recognised "
            "branches behind is_known_encoding(enc) (the same grounded @Pure "
            "predicate the postcondition uses) and returns the exact dedicated "
            "byte literals; passthrough loop unchanged. The oracle is grounded so "
            "this returns the CORRECT value; must verify, else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-br-text-html",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl(_ADMISS),
        "rationale": (
            "A self-call caller invokes select_content_type on the F2P-shaped "
            "input content_type='text/html', encoding='br' and asserts the result "
            "is ct_brotli(); the two Acc(...,1/2) Requires are established for "
            "freshly-built lists. If the precondition rejected this normal input "
            "=> PRECOND-TOO-STRONG."
        ),
    },
]

# No @ContractOnly axioms, no A-reference deep models (meta.axioms == [],
# deep_model_references == []): the changed operation is a finite literal table
# modeled directly. The axiom lane is vacuous.
AXIOM_TESTS = []
