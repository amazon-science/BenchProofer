# properties.py — PBT falsification battery for django__django-11133. NOT a Nagini
# module; a record of adversarial cases the runner (swebench_nagini.pbt) executes.
# Spec cases are full model.py variants (same FROZEN spec, swapped impl region)
# checked by Nagini verify + same_spec; axiom cases are real-callee probes in Docker.
#
# ---------------------------------------------------------------------------
# Defended surface (read from model.py + refinement.md + mapping.md + instance.json)
# ---------------------------------------------------------------------------
#   coerce_to_octets(v: Value) -> Value
#     The single modeled changed function == HttpResponseBase.make_bytes (the gold
#     patch widens the buffer guard isinstance(value, bytes) ->
#     isinstance(value, (bytes, memoryview))). v is a minimal carrier:
#       kind : int   in {KIND_OCTETS=0, KIND_VIEW=1, KIND_TEXT=2, KIND_OTHER=3}
#       buf  : PSeq[int]   raw octets (meaningful for the two buffer kinds)
#       cps  : PSeq[int]   code points charset-encoded for text/other kinds
#       data : PSeq[int]   output octets (meaningful on the RESULT)
#
#   PRECONDITION (READ-ONLY heap input — frame-mutation MANDATORY):
#       Requires(Acc(v.kind,1/2) and Acc(v.buf,1/2) and Acc(v.cps,1/2)
#                and Acc(v.data,1/2))     # every field held at HALF permission
#
#   POSTCONDITION (load-bearing clauses):
#     (F) Ensures(Acc(v.kind,1/2) and Acc(v.buf,1/2) and Acc(v.cps,1/2)
#                 and Acc(v.data,1/2))    # FRAME: input returned UNWRITTEN at 1/2
#     (P) Ensures(Acc(Result().kind/buf/cps/data))                # owns the result
#     (C1) Ensures(Implies(is_buffer_kind(v.kind), Result().data == v.buf))
#                  # buffer kinds (OCTETS *and* VIEW) -> octets VERBATIM  (the FIX)
#     (C2) Ensures(Implies(not is_buffer_kind(v.kind),
#                          Result().data == charset_encode(v.cps)))
#                  # text/other -> charset encoding of the code points (unchanged)
#     is_buffer_kind(k) := (k == KIND_OCTETS or k == KIND_VIEW)   # @Pure, inlined
#
# The discriminating change (F2P test_memoryview_content): a memoryview (KIND_VIEW)
#   must be carried through VERBATIM (b'memoryview'), not rendered as its repr.
#   model_prepatch.py reverts the buffer guard to KIND_OCTETS-only, so a KIND_VIEW
#   value falls through to charset_encode — exactly the pre-patch bug — and FAILS
#   clause C1. That is the partial-domain rival weak-prepatch-view below.
#
# ---------------------------------------------------------------------------
# Why the UNGROUNDED-ORACLE-ECHO class does NOT apply here (per directive 2):
#   The only @Pure reference in the postcondition is charset_encode(v.cps), an
#   A-CONSUMED axiom (@ContractOnly, Ensures(True)). It is GROUNDED in the input:
#   a pure function of v.cps, the same code-point argument the impl passes. There
#   is NO opaque answer-key / exact-marker an impl could echo to satisfy C2 with a
#   WRONG value — the only value that satisfies C2 IS charset_encode(v.cps), which
#   is what the gold impl returns. So an "echo" here is simply correct and there
#   is no wrong-echo to build. We instead include an honest cheapest-impl positive
#   control that routes the non-buffer branch through that grounded oracle
#   (pos-oracle-grounded, expect verify). Stated in 'assessment'.
# ---------------------------------------------------------------------------
from pathlib import Path

INSTANCE = "django__django-11133"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen `coerce_to_octets` impl region body, VERBATIM (everything strictly
# BETWEEN its # impl-start / # impl-end markers — NOT the Value.__init__ impl).
# Every variant _swap's this single unique block, so edits never touch the spec
# (axioms/pure/pre/post regions + signatures) nor the constructor impl, and
# same_spec is guaranteed.
_IMPL = """\
    if v.kind == KIND_OCTETS or v.kind == KIND_VIEW:
        return Value(KIND_OCTETS, v.buf, v.cps, v.buf)
    return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.cps))"""

assert _BASE.count(_IMPL) == 1, "coerce_to_octets impl region drifted from expected text"


def _impl(new_body):
    """Build a full model.py variant with ONLY the coerce_to_octets impl body
    replaced (text strictly inside its # impl-start / # impl-end)."""
    return _swap(_BASE, _IMPL, new_body)


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — must VERIFY.
# ===========================================================================

# pos-helper-reorder: structurally different but behaviourally identical. Uses the
# @Pure helper is_buffer_kind(v.kind) directly (instead of spelling the two-arm
# disjunction) AND inverts the branch order — the non-buffer (encode) arm is
# tested first. No loop, no @Pure fold, so the gold proof obligations are intact;
# this is a pure branch-reorder/local-reshape (per directive 5/pilot bug #2,3).
_POS_REORDER = """\
    # Branch-reordered, helper-driven: encode the non-buffer kinds first, fall
    # through to the verbatim-octet passthrough for the two buffer kinds. Same
    # behaviour as the gold dispatch, different executable shape.
    if not is_buffer_kind(v.kind):
        return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.cps))
    return Value(KIND_OCTETS, v.buf, v.cps, v.buf)"""

# pos-oracle-grounded: the honest grounded-oracle positive control (directive 2).
# Route the non-buffer branch through charset_encode(v.cps) — the SAME @Pure
# reference C2 pins. The oracle is grounded in v.cps, so this is CORRECT and must
# verify; there is no wrong echo to build. (Identical-in-spirit to the gold impl
# but separated into explicit per-kind dispatch via the helper.)
_POS_ORACLE = """\
    # Grounded-oracle dispatch: a buffer kind carries octets verbatim; every
    # other kind is the charset encoding of its code points, sourced from the
    # @Pure charset_encode reference that the postcondition itself uses.
    if is_buffer_kind(v.kind):
        return Value(KIND_OCTETS, v.buf, v.cps, v.buf)
    return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.cps))"""

# admiss-shape: an admissibility positive control. The precondition holds every
# field of v at HALF permission; this impl READS each field of v (so the 1/2
# reads must succeed for a normal F2P/P2P-shaped input) and asserts the dispatch
# shape for all four representation tags the tests exercise (memoryview=KIND_VIEW
# is the F2P; bytes/str/other are the P2P siblings). Asserts are over the @Pure
# is_buffer_kind on local integer constants — no heap write, no proof gap. If the
# precondition could not be established for an in-domain input => PRECOND-TOO-STRONG.
_ADMISS = """\
    # Admissibility / shape control: read v at its 1/2 permission and confirm the
    # four F2P/P2P-shaped kinds are in-domain and dispatch as specified.
    Assert(is_buffer_kind(KIND_OCTETS))       # bytes  (P2P)
    Assert(is_buffer_kind(KIND_VIEW))         # memoryview  (the F2P case)
    Assert(not is_buffer_kind(KIND_TEXT))     # str  (P2P)
    Assert(not is_buffer_kind(KIND_OTHER))    # any other value, e.g. 12345 (P2P)
    if is_buffer_kind(v.kind):
        Assert(v.kind == KIND_OCTETS or v.kind == KIND_VIEW)
        return Value(KIND_OCTETS, v.buf, v.cps, v.buf)
    return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.cps))"""


# ===========================================================================
# FRAME-MUTATION RIVALS (MANDATORY — v is a READ-ONLY half-permission input).
# Each WRITES through a 1/2-permission field of v; it must FAIL for INSUFFICIENT
# PERMISSION (a heap write needs full perm) and the Ensures(Acc(v.<f>,1/2)) frame
# could never be re-established afterwards. A byte-fuzzer never thinks to do this.
# Gold invariants kept verbatim so the rejection is attributable to the write.
# ===========================================================================

# frame-mutate-data: overwrite v.data (the input's output-octet field, held at
# 1/2) to v.buf, then return v itself dressed as the result. A WRITE through
# Acc(v.data,1/2) needs full permission.
_FRAME_DATA = """\
    # ADVERSARY (frame mutation): write the answer back into the read-only input's
    # data field instead of building a fresh result. v.data is held at 1/2, so
    # this assignment needs full permission it does not have.
    v.data = v.buf
    if v.kind == KIND_OCTETS or v.kind == KIND_VIEW:
        return Value(KIND_OCTETS, v.buf, v.cps, v.buf)
    return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.cps))"""

# frame-mutate-kind: coerce the input into a buffer kind by writing v.kind, so the
# verbatim branch is taken for everything. The write through Acc(v.kind,1/2)
# needs full permission; it also destroys the C2 obligation for the original kind.
_FRAME_KIND = """\
    # ADVERSARY (frame mutation): rewrite the read-only input's kind tag to force
    # the buffer branch. v.kind is held at 1/2, so the assignment needs full
    # permission it does not have.
    v.kind = KIND_OCTETS
    return Value(KIND_OCTETS, v.buf, v.cps, v.buf)"""


# ===========================================================================
# UNIQUENESS / PARTIAL-DOMAIN / VALUE-MASK RIVALS — must be REJECTED.
# Each shares the FROZEN spec exactly and changes only the impl region.
# ===========================================================================

# weak-prepatch-view: the PRE-PATCH behaviour (== model_prepatch.py). The buffer
# branch matches KIND_OCTETS ONLY; a KIND_VIEW value falls through to
# charset_encode(v.cps). Violates C1 on the KIND_VIEW sub-domain.
_WEAK_PREPATCH = """\
    # Adversary: keep the un-widened guard (KIND_OCTETS only). A KIND_VIEW
    # (memoryview) value falls through to the encode branch — the pre-patch bug.
    if v.kind == KIND_OCTETS:
        return Value(KIND_OCTETS, v.buf, v.cps, v.buf)
    return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.cps))"""

# weak-view-encodes: the OTHER half of the pre-patch surface — KIND_OCTETS is
# handled verbatim, but KIND_VIEW alone is special-cased to the encode branch.
# Isolates the single discriminating sub-domain (KIND_VIEW). Violates C1 for
# KIND_VIEW only; correct on every other kind. PARTIAL-DOMAIN attack.
_WEAK_VIEW = """\
    # Adversary: bytes pass through verbatim, but a memoryview (KIND_VIEW) is
    # encoded as if it were text/other — diverging only on the one F2P sub-domain.
    if v.kind == KIND_OCTETS:
        return Value(KIND_OCTETS, v.buf, v.cps, v.buf)
    if v.kind == KIND_VIEW:
        return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.cps))
    return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.cps))"""

# weak-always-encode: ignore the buffer kinds entirely; always return the charset
# encoding of v.cps. Satisfies C2 but violates C1 for BOTH buffer kinds.
_WEAK_ALWAYS_ENCODE = """\
    # Adversary: always charset-encode the code points, never carry octets
    # through (drops the whole buffer passthrough the fix introduces).
    return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.cps))"""

# weak-always-buf: the mirror — always return v.buf as the output octets. Satisfies
# C1 but violates C2 for the text/other kinds (their output must be the charset
# encoding of the code points, NOT the raw buf, which is empty/meaningless there).
_WEAK_ALWAYS_BUF = """\
    # Adversary: always carry v.buf through as the output, never encode. A text or
    # other value would emit its (empty/meaningless) buf instead of its encoding.
    return Value(KIND_OCTETS, v.buf, v.cps, v.buf)"""

# weak-encode-buffer: a value-mask near-miss. For the buffer branch, return
# charset_encode(v.buf) instead of v.buf — same SHAPE (an octet PSeq derived from
# v), but the wrong function. C1 requires Result().data == v.buf exactly, not the
# charset re-encoding of the octets. Catches a spec that pinned only "some PSeq of
# the buffer" rather than the verbatim octets.
_WEAK_ENCODE_BUF = """\
    # Adversary: on the buffer branch, re-encode the octets through the charset
    # encoder rather than carrying them verbatim. Right shape, wrong value.
    if v.kind == KIND_OCTETS or v.kind == KIND_VIEW:
        return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.buf))
    return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.cps))"""

# weak-swap-arms: route buffer kinds to the encode branch and non-buffer kinds to
# the verbatim-buf branch. Violates BOTH C1 (buffer -> encode != buf) and C2
# (non-buffer -> buf != encode). Supporting near-miss with a real refinement.
_WEAK_SWAP = """\
    # Adversary: swap the arms — buffer kinds get encoded, non-buffer kinds get
    # the raw buf. Inverts the entire dispatch.
    if v.kind == KIND_OCTETS or v.kind == KIND_VIEW:
        return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.cps))
    return Value(KIND_OCTETS, v.buf, v.cps, v.buf)"""


SPEC_TESTS = [
    # ---- positive controls -------------------------------------------------
    {
        "id": "pos-helper-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": (
            "structurally-different but behaviourally-identical impl: dispatches "
            "via the @Pure is_buffer_kind helper with the encode arm tested first. "
            "No loop/@Pure-fold => the gold proof obligations stay valid (pilot "
            "bug #2/#3 avoided). Both C1 (buffer->v.buf) and C2 (else->"
            "charset_encode(v.cps)) hold. If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-oracle-grounded",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_ORACLE),
        "rationale": (
            "honest grounded-oracle positive control (directive 2): the non-buffer "
            "branch returns charset_encode(v.cps), the SAME @Pure reference C2 "
            "pins, and it is grounded in v.cps. Correct => must verify; there is "
            "no wrong echo to construct because the oracle is a function of the args."
        ),
    },
    {
        "id": "admiss-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "the precondition (every v field at 1/2) must admit a normal "
            "F2P/P2P-shaped input: the impl reads v at 1/2 and asserts the four "
            "representation tags (VIEW=F2P; OCTETS/TEXT/OTHER=P2P) dispatch as "
            "specified via the @Pure is_buffer_kind on integer constants — no heap "
            "write, no proof gap. If it fails => PRECOND-TOO-STRONG."
        ),
    },
    # ---- frame-mutation (MANDATORY: v is read-only at 1/2) -----------------
    {
        "id": "frame-mutate-data",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_DATA),
        "refinement": (
            "writing v.data has NO repo counterpart: make_bytes never mutates its "
            "`value` argument — it returns a freshly built bytestring. A faithful "
            "real patch cannot 'write the answer into the input', so this rival "
            "has no resolving real implementation; it is a pure verification "
            "artifact that the permission system must block."
        ),
        "rationale": (
            "MANDATORY frame-mutation probe. `v.data = v.buf` writes through "
            "Acc(v.data,1/2); a heap write needs FULL permission, so it MUST fail "
            "for INSUFFICIENT PERMISSION, and the Ensures(Acc(v.data,1/2)) frame "
            "(clause F) could never be re-established after the write. Rejection "
            "comes from the PERMISSION SYSTEM. If it verified => SPEC-TOO-WEAK "
            "(frame protection hollow)."
        ),
    },
    {
        "id": "frame-mutate-kind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_KIND),
        "refinement": (
            "rewriting v.kind to force the buffer branch has no repo counterpart "
            "either: make_bytes does not (and cannot) change the runtime type of "
            "its argument to pick a branch. Its faithful real patch would have to "
            "mutate the caller's value object's identity, which it never does; no "
            "resolving real implementation exists."
        ),
        "rationale": (
            "MANDATORY frame-mutation probe. `v.kind = KIND_OCTETS` writes through "
            "Acc(v.kind,1/2) => INSUFFICIENT PERMISSION (heap write needs full "
            "perm), and the Ensures(Acc(v.kind,1/2)) frame cannot be "
            "re-established. Rejection comes from the PERMISSION SYSTEM. If it "
            "verified => SPEC-TOO-WEAK."
        ),
    },
    # ---- uniqueness / partial-domain / value-mask --------------------------
    {
        "id": "weak-prepatch-view",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PREPATCH),
        "refinement": (
            "this IS the pre-patch code (== model_prepatch.py): the un-widened "
            "guard isinstance(value, bytes). Its faithful real patch is the "
            "unpatched repo, where HttpResponse(memoryview(b'memoryview')).content "
            "renders the repr b'<memory at 0x...>' instead of b'memoryview' — the "
            "F2P test_memoryview_content assertion fails. Does NOT resolve."
        ),
        "rationale": (
            "rejected by C1 (Implies(is_buffer_kind(v.kind), Result().data == "
            "v.buf)) on the KIND_VIEW sub-domain: is_buffer_kind(KIND_VIEW) is "
            "True, so the result must be v.buf, but this impl returns "
            "charset_encode(v.cps). PARTIAL-DOMAIN on exactly the discriminating "
            "input. If it verifies => SPEC-TOO-WEAK (the fix would be unobserved)."
        ),
    },
    {
        "id": "weak-view-encodes",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_VIEW),
        "refinement": (
            "special-casing only the memoryview arm to encode corresponds to a "
            "real patch that explicitly routes memoryview through "
            "str(value).encode(charset) — yielding the repr bytes b'<memory at "
            "0x...>' for HttpResponse(memoryview(b'memoryview')). The F2P assertion "
            "assertEqual(r.content, b'memoryview') fails. Does NOT resolve."
        ),
        "rationale": (
            "rejected by C1 on the single KIND_VIEW sub-domain (correct on every "
            "other kind): is_buffer_kind(KIND_VIEW) is True so Result().data must "
            "== v.buf, but this impl returns charset_encode(v.cps) for KIND_VIEW. "
            "PARTIAL-DOMAIN attack isolating the one discriminating value. If it "
            "verifies => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-always-encode",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ALWAYS_ENCODE),
        "refinement": (
            "always encoding drops the buffer passthrough entirely — the real "
            "patch would be `return str(value).encode(self.charset)` for every "
            "value, so BOTH bytes and memoryview render as repr / re-encode. The "
            "F2P (memoryview) and the bytes P2P (test_non_string_content sibling) "
            "fail. Does NOT resolve."
        ),
        "rationale": (
            "rejected by C1 for both buffer kinds (Result().data must == v.buf for "
            "is_buffer_kind(v.kind), but returns charset_encode(v.cps)). If it "
            "verifies => SPEC-TOO-WEAK (buffer branch unconstrained)."
        ),
    },
    {
        "id": "weak-always-buf",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ALWAYS_BUF),
        "refinement": (
            "always carrying v.buf through corresponds to a real patch that "
            "returns bytes(value) for str/other too — which raises (str has no "
            "buffer protocol) or emits wrong octets. The str/other P2P cases "
            "(test_non_string_content: r.content = 'abc' / 12345) would NOT yield "
            "their charset encoding. Does NOT resolve."
        ),
        "rationale": (
            "rejected by C2 (Implies(not is_buffer_kind(v.kind), Result().data == "
            "charset_encode(v.cps))): for KIND_TEXT/KIND_OTHER the result must be "
            "the encoding, but this impl returns v.buf. If it verifies => "
            "SPEC-TOO-WEAK (non-buffer branch unconstrained)."
        ),
    },
    {
        "id": "weak-encode-buffer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ENCODE_BUF),
        "refinement": (
            "re-encoding the octets through the charset encoder on the buffer "
            "branch corresponds to a real patch like `return bytes(value).decode("
            "...).encode(self.charset)` — for non-utf-8 charsets or non-text "
            "octets (e.g. b'\\x80\\x81') this changes or corrupts the bytes, so "
            "HttpResponse(memoryview(b'...')).content != the underlying octets. "
            "The F2P (and binary-bytes P2P) fail. Does NOT resolve."
        ),
        "rationale": (
            "VALUE-MASK near-miss: same shape (an octet PSeq derived from v), wrong "
            "value. C1 requires Result().data == v.buf EXACTLY (verbatim octets), "
            "not charset_encode(v.buf). If it verifies => SPEC-TOO-WEAK (C1 "
            "pinned only 'a function of the buffer', not the buffer itself)."
        ),
    },
    {
        "id": "weak-swap-arms",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_SWAP),
        "refinement": (
            "swapping the arms is an inverted dispatch (encode the buffers, carry "
            "the raw buf for text/other). The real patch would render bytes as "
            "repr/re-encode and emit a meaningless buf for strings — failing both "
            "the memoryview F2P and the str/other P2P cases. Does NOT resolve."
        ),
        "rationale": (
            "rejected by BOTH C1 (buffer kinds -> charset_encode != v.buf) and C2 "
            "(non-buffer kinds -> v.buf != charset_encode(v.cps)). Supporting "
            "near-miss carrying a real refinement. If it verifies => SPEC-TOO-WEAK."
        ),
    },
]

# ===========================================================================
# AXIOM lane — charset_encode (A-consumed; @Pure @ContractOnly, Ensures(True)).
# ===========================================================================
# The proof consumes ONLY purity/determinism of charset_encode (it never relies on
# any specific octet the encoder produces). Two obligations to falsify on the REAL
# callee, run in the instance Docker image (apply_gold=True: the post-patch body):
#   (1) axiom-soundness: str.encode(charset) is a deterministic pure function of
#       its code-point argument (same code points + same charset -> same outcome,
#       value OR raised-exception-type). Fuzz boundaries + sentinels + raise paths.
#       AND the discriminating model content: a buffer-bearing value (bytes OR the
#       memoryview over the same octets) coerces to those octets VERBATIM, and the
#       two agree — make_bytes(memoryview(b)) == make_bytes(b) == b — which is what
#       the F2P demands and what C1 (Result().data == v.buf) models.
#   (2) axiom-containment: the ONLY callee-inputs the model can reach on the
#       non-buffer branch are charset_encode(v.cps) where v.cps is a PSeq[int] of
#       code points; charset_encode's Requires domain is unrestricted (PSeq[int],
#       Ensures(True)) so every reachable input is trivially in-domain. The buffer
#       branch never calls the encoder (it carries octets verbatim) — so the
#       encoder is never reached on a buffer kind, the input class the fix touches.
#       We verify containment by EXECUTING the real make_bytes and confirming the
#       encoder is invoked on exactly the non-buffer kinds (never on bytes /
#       memoryview), so no buffer octets are pushed through the charset encoder.
#
# Probes import only the stdlib and reproduce make_bytes verbatim from the patched
# source (matches axiom_check.py); they CALL the real callee (str.encode), never
# scrape source (pilot bug #4); files opened utf-8 if any (pilot bug #5); no bundle
# file is assumed in-container (pilot bug #6) — everything is inlined.

_AX_SOUND_PROBE = r'''
import random, sys

# --- the REAL changed function, reproduced verbatim from the patched source ---
# django/http/response.py  HttpResponseBase.make_bytes (post-gold-patch body).
def real_make_bytes(value, charset):
    if isinstance(value, (bytes, memoryview)):   # the gold-patched guard
        return bytes(value)
    if isinstance(value, str):
        return bytes(value.encode(charset))
    return str(value).encode(charset)

# charset_encode reference == str.encode(charset) on a list of code points.
def charset_encode(cps, charset):
    return list("".join(chr(c) for c in cps).encode(charset))

def encode_outcome(cps, charset):
    # determinism includes a deterministic raise (still a pure function).
    try:
        return ("ok", charset_encode(list(cps), charset))
    except Exception as e:                       # noqa: BLE001
        return ("raise", type(e).__name__)

charsets = ["utf-8", "latin-1", "ascii", "utf-16"]
fails = 0

# (A-content) buffer passthrough: bytes == memoryview == underlying octets verbatim
boundary_buffers = [
    b"", b"memoryview", b"My Content",
    b"\x00\x01\x02\xfe\xff", bytes(range(256)),
    b"\x80\x81\x82", b"a" * 257,
]
for raw in boundary_buffers:
    b = bytes(raw)
    for cs in charsets:
        fb = real_make_bytes(b, cs)
        fv = real_make_bytes(memoryview(b), cs)
        if not (fb == b and fv == b and fv == fb):
            print("UNSOUND buffer passthrough on %r/%s: bytes->%r view->%r"
                  % (b, cs, fb, fv)); fails += 1

# (A-consumed) charset_encode determinism on boundary + sentinel code points
sentinel_cps = [[], [104, 105], [0, 255], list(range(0, 128)),
                [0x80, 0x81], [0x10FFFF], [0xD800]]  # incl. a lone surrogate (raises)
for cps in sentinel_cps:
    for cs in charsets:
        a = encode_outcome(cps, cs)
        c = encode_outcome(cps, cs)
        if a != c:
            print("NON-DETERMINISTIC charset_encode on %r/%s: %r vs %r"
                  % (cps, cs, a, c)); fails += 1

# (A-consumed + R) text and other branches == charset_encode of their code points
for s in ["", "My Content", "abcdef", "x" * 200]:
    for cs in charsets:
        obs = list(real_make_bytes(s, cs)); exp = charset_encode([ord(ch) for ch in s], cs)
        if obs != exp:
            print("UNSOUND text branch on %r/%s: %r vs %r" % (s, cs, obs, exp)); fails += 1
for s in ["café", "naïve", "日本語", "\U0001F600"]:
    obs = list(real_make_bytes(s, "utf-8")); exp = charset_encode([ord(ch) for ch in s], "utf-8")
    if obs != exp:
        print("UNSOUND text branch on %r/utf-8: %r vs %r" % (s, obs, exp)); fails += 1
for val in [12345, 0, -7, 3.5, True, None, [1, 2, 3], {"k": "v"}, (1,)]:
    for cs in ["utf-8", "latin-1"]:
        obs = list(real_make_bytes(val, cs)); exp = charset_encode([ord(ch) for ch in str(val)], cs)
        if obs != exp:
            print("UNSOUND other branch on %r/%s: %r vs %r" % (val, cs, obs, exp)); fails += 1

# randomized fuzz: buffers + ascii text + others
rng = random.Random(11133)
for _ in range(20000):
    n = rng.randint(0, 32); raw = bytes(rng.randint(0, 255) for _ in range(n)); cs = rng.choice(charsets)
    b = bytes(raw)
    fb = real_make_bytes(b, cs); fv = real_make_bytes(memoryview(b), cs)
    if not (fb == b and fv == b and fv == fb):
        print("UNSOUND fuzz buffer on %r/%s" % (b, cs)); fails += 1
for _ in range(20000):
    n = rng.randint(0, 32); s = "".join(chr(rng.randint(32, 126)) for _ in range(n)); cs = rng.choice(charsets)
    a = encode_outcome([ord(ch) for ch in s], cs); c = encode_outcome([ord(ch) for ch in s], cs)
    if a != c:
        print("NON-DETERMINISTIC fuzz text on %r/%s" % (s, cs)); fails += 1

if fails:
    print("AXIOM-UNSOUND: %d violation(s)" % fails); sys.exit(1)
print("AX-SOUND OK: buffer passthrough verbatim (bytes==memoryview==octets) + "
      "charset_encode deterministic over boundary+sentinel+fuzz; no encoder "
      "dependence on any specific octet value.")
sys.exit(0)
'''

_AX_CONTAIN_PROBE = r'''
import sys

# Containment: the model reaches charset_encode ONLY on the non-buffer branch
# (KIND_TEXT / KIND_OTHER), passing a PSeq[int] of code points. The axiom's
# Requires domain is unrestricted (cps: PSeq[int], Ensures(True)), so every
# reachable input is in-domain. The KEY containment fact to falsify: the encoder
# is NEVER invoked on a buffer kind (bytes/memoryview) — those carry octets
# verbatim and never push buffer octets through str.encode. We instrument the
# REAL make_bytes (patched body) with a tracing encoder to record exactly which
# inputs reach the charset encoder.

ENCODER_CALLS = []  # records the code-point argument str(value) reached the encoder

class TracingStr(str):
    pass

def real_make_bytes(value, charset):
    if isinstance(value, (bytes, memoryview)):
        return bytes(value)            # buffer branch: NO encoder call
    if isinstance(value, str):
        ENCODER_CALLS.append(("text", value))
        return bytes(value.encode(charset))
    rendered = str(value)
    ENCODER_CALLS.append(("other", rendered))
    return rendered.encode(charset)

charset = "utf-8"
fails = 0

# Buffer kinds (the input class the FIX touches): encoder must NOT be reached.
for value in [b"", b"memoryview", b"\x80\x81\x82", bytes(range(256)),
              memoryview(b"memoryview"), memoryview(b"\x00\xff")]:
    before = len(ENCODER_CALLS)
    real_make_bytes(value, charset)
    if len(ENCODER_CALLS) != before:
        print("CONTAINMENT VIOLATION: buffer value %r reached the charset encoder"
              % (value,)); fails += 1

# Non-buffer kinds: encoder IS reached, and every argument is a real str whose
# code points form a valid PSeq[int] in the axiom's (unrestricted) Requires domain.
for value in ["", "My Content", "café", 12345, 0, 3.5, None, [1, 2], {"k": 1}]:
    before = len(ENCODER_CALLS)
    real_make_bytes(value, charset)
    if len(ENCODER_CALLS) != before + 1:
        print("EXPECTED an encoder call for non-buffer %r" % (value,)); fails += 1
    else:
        kind, arg = ENCODER_CALLS[-1]
        cps = [ord(ch) for ch in arg]
        if not all(isinstance(c, int) and 0 <= c <= 0x10FFFF for c in cps):
            print("OUT-OF-DOMAIN code points for %r: %r" % (value, cps)); fails += 1

if fails:
    print("AXIOM-TOO-WEAK-FOR-CALLER / containment: %d issue(s)" % fails); sys.exit(1)
print("AX-CONTAIN OK: charset_encode reached on exactly the non-buffer kinds "
      "(text/other), never on a buffer kind (bytes/memoryview); every reached "
      "argument is a PSeq[int] of code points inside the axiom's (unrestricted) "
      "Requires domain. No buffer octets are pushed through the encoder.")
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-sound-charset-encode",
        "axiom": "charset_encode",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "charset_encode stands in for str.encode(self.charset); the proof "
            "consumes only its purity/determinism. The probe runs the REAL patched "
            "make_bytes + str.encode on boundary + sentinel (incl. lone-surrogate "
            "raise) + 40000 fuzz inputs and asserts (a) the buffer branch carries "
            "octets verbatim (bytes==memoryview==underlying octets, the F2P "
            "behaviour) and (b) charset_encode is a deterministic pure function of "
            "its code points. Any violation => AXIOM-UNSOUND. No flag dependency "
            "(meta: str.encode defaults irrelevant; the buffer branch never encodes)."
        ),
    },
    {
        "id": "ax-contain-charset-encode",
        "axiom": "charset_encode",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": (
            "containment, not whole-domain coverage: the model reaches "
            "charset_encode ONLY on the non-buffer branch (KIND_TEXT/KIND_OTHER) "
            "with a PSeq[int] of code points, all inside the axiom's unrestricted "
            "Requires domain (Ensures(True)). The probe instruments the real "
            "make_bytes and confirms the encoder is NEVER invoked on a buffer kind "
            "(bytes/memoryview — the input class the fix touches) and IS invoked on "
            "exactly the non-buffer kinds with in-domain code points. A buffer "
            "octet reaching the encoder => AXIOM-TOO-WEAK-FOR-CALLER."
        ),
    },
]
