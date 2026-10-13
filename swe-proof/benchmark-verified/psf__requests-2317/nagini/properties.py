# properties.py — PBT falsification battery for psf__requests-2317. NOT a Nagini
# module; a record of adversarial cases the runner (swebench_nagini.pbt) executes.
#
# Defended surface (read from model.py + refinement.md + mapping.md):
#   native_method(content: List[int], is_bytes: bool) -> List[int]
#   The native-text representation of an HTTP method token. `content` is the
#   carried ASCII character/byte values; `is_bytes` records text-vs-bytes. The
#   result is the token's OWN characters: the carried sequence exactly, of the
#   same length, INDEPENDENT of is_bytes. (The gold change: builtin_str(method)
#   -> to_native_string(method), so b'GET' decodes to GET instead of rendering
#   as the five-char text b'GET'.)
#
#   `content` is READ-ONLY: Requires/Ensures/Invariant all carry
#       Acc(list_pred(content), 1 / 2)
#   i.e. only HALF permission — the function may read content but may NOT write
#   it. Result() carries FULL Acc(list_pred(Result())): the output is a fresh
#   list the function fully owns.
#
#   Load-bearing postcondition clauses:
#     (C1) Acc(list_pred(content), 1/2)         # content unchanged (frame)
#     (C2) Acc(list_pred(Result()))             # result fully owned (fresh)
#     (C3) ToSeq(Result()) == ToSeq(content)    # DOMINANT: result == carried seq
#     (C4) len(Result()) == len(content)        # same length (==> not the b'..' wrap)
#   C3 is grounded in the input `content`; C3 ⟹ C4. The pre-patch b'...'-wrap
#   (prefix [98,39], content, suffix [39]) is a length-(len+3) sequence that
#   violates C3/C4 — exactly what model_prepatch.py reproduces (G-DIFF).
#
#   Termination obligation (precondition):
#     (C0) MustTerminate(len(content) + 2)      # the result must be DELIVERED
#   The spec demands total, not merely partial, correctness: an impl that
#   builds the right sequence but never returns cannot discharge the caller's
#   termination obligation (every loop must consume it via a strictly
#   decreasing, bounded-below measure). The nonterm-* rival probes this lane.
#
# FRAME-MUTATION lane (MANDATORY — content is read-only, Acc(...,1/2)):
#   frame-mut-* below WRITE to `content` (assign an element / extend it) to try
#   to satisfy C3/C4 vacuously. With only half permission the verifier must
#   reject them for INSUFFICIENT PERMISSION. The gold C3/C4 invariants are kept
#   verbatim so the rejection is attributable to the write, not a proof gap.
#
# UNGROUNDED-ORACLE-ECHO: N/A — the postcondition is GROUNDED in the input.
#   C3 pins Result to ToSeq(content) (the argument itself, fully unfolded), not
#   to an opaque @Pure answer-key/marker. There is no oracle whose materialized
#   value an impl could echo while being wrong; the cheapest honest impl is the
#   copy loop itself (the positive controls below). The pure region is empty.
#
# AXIOM lane: AXIOM_TESTS = []. meta.axioms == [] (axioms region empty, no
#   @ContractOnly). The to_native_string correspondence is an A-REFERENCE deep
#   model (the copy loop), validated == the real callee out-of-band by
#   axiom_check.py / G-AX over the entire Requires domain — it is NOT a consumed
#   axiom the proof depends on, so there is no axiom Ensures for the PBT axiom
#   lane to falsify. (G-AX already fuzzes the real callee on 14 boundary + 126
#   full-domain + 20000 tokens, text+bytes.)
from pathlib import Path

INSTANCE = "psf__requests-2317"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl-region body, verbatim — everything strictly BETWEEN the
# # impl-start / # impl-end markers (the markers + nested invariants live inside
# the impl region, which same_spec elides wholesale, so editing any of this NEVER
# touches the spec: signature + axioms/pure/pre/post regions are untouched).
_IMPL = """\
    result = []  # type: List[int]
    j = 0
    n = len(content)
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(content), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n and n == len(content))
        Invariant(ToSeq(result) == ToSeq(content).take(j))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure n - j.
        Invariant(MustTerminate(n - j))
        # invariants-end
        Assert(ToSeq(content).take(j + 1) == ToSeq(content).take(j) + PSeq(content[j]))
        result = result + [content[j]]
        j = j + 1
    Assert(ToSeq(content).take(n) == ToSeq(content))
    return result"""

assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"


def _impl(new_body):
    """Build a full model.py variant with the impl-region body replaced. Only the
    text strictly inside # impl-start / # impl-end changes; same_spec guaranteed."""
    return _swap(_BASE, _IMPL, new_body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness / admissibility) — must VERIFY.
# Each keeps the gold front-prefix invariant `ToSeq(result)==ToSeq(content).take(j)`
# and the per-element pin around the append (directives 2 & 3): we change only the
# executable SHAPE (the spec helper take() is front-recursive, so we keep forward
# iteration — no f(a+b)==f(a)+f(b) lemma is needed).
# ---------------------------------------------------------------------------

# pos-isbytes-split: structurally different — split on is_bytes into two arms that
# perform the SAME forward copy. This makes explicit that the result is INDEPENDENT
# of is_bytes (the heart of the change: a byte token is decoded, not wrapped). Each
# arm keeps the gold invariant + per-element pin verbatim, so the proof stays valid.
_POS_ISBYTES = """\
    # Branch on the token kind, then perform the identical forward copy in each
    # arm: the result is the token's own characters regardless of is_bytes.
    result = []  # type: List[int]
    n = len(content)
    if is_bytes:
        j = 0
        while j < n:
            # invariants-start
            Invariant(Acc(list_pred(content), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= j and j <= n and n == len(content))
            Invariant(ToSeq(result) == ToSeq(content).take(j))
            # The loop consumes the caller's termination obligation with the
            # strictly decreasing, bounded-below measure n - j.
            Invariant(MustTerminate(n - j))
            # invariants-end
            Assert(ToSeq(content).take(j + 1) == ToSeq(content).take(j) + PSeq(content[j]))
            result = result + [content[j]]
            j = j + 1
        Assert(ToSeq(content).take(n) == ToSeq(content))
        return result
    j = 0
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(content), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n and n == len(content))
        Invariant(ToSeq(result) == ToSeq(content).take(j))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure n - j.
        Invariant(MustTerminate(n - j))
        # invariants-end
        Assert(ToSeq(content).take(j + 1) == ToSeq(content).take(j) + PSeq(content[j]))
        result = result + [content[j]]
        j = j + 1
    Assert(ToSeq(content).take(n) == ToSeq(content))
    return result"""

# pos-append-shape: same forward direction, but accumulate with list.append(...)
# instead of result = result + [x], and recompute the length via a separate counter
# `i` that mirrors j. Different executable shape; keeps the front-prefix invariant
# and per-element pin so the gold proof obligations are all discharged.
_POS_APPEND = """\
    result = []  # type: List[int]
    n = len(content)
    j = 0
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(content), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n and n == len(content))
        Invariant(ToSeq(result) == ToSeq(content).take(j))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure n - j.
        Invariant(MustTerminate(n - j))
        # invariants-end
        Assert(ToSeq(content).take(j + 1) == ToSeq(content).take(j) + PSeq(content[j]))
        result.append(content[j])
        j = j + 1
    Assert(ToSeq(content).take(n) == ToSeq(content))
    return result"""

# admiss-shape: admissibility positive control. The precondition (ASCII, no
# 39/92, half permission) must admit an F2P-shaped token. We copy as gold, then —
# inside the impl region, where asserts are proof-local — assert the postcondition
# SHAPE on the just-built result (len match + emptiness equivalence). All asserts
# are entailed by the kept invariant, so no proof gap; a PRECOND/spec-shape
# regression would surface here.
_ADMISS = """\
    result = []  # type: List[int]
    j = 0
    n = len(content)
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(content), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n and n == len(content))
        Invariant(ToSeq(result) == ToSeq(content).take(j))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure n - j.
        Invariant(MustTerminate(n - j))
        # invariants-end
        Assert(ToSeq(content).take(j + 1) == ToSeq(content).take(j) + PSeq(content[j]))
        result = result + [content[j]]
        j = j + 1
    Assert(ToSeq(content).take(n) == ToSeq(content))
    # Admissibility / shape: an F2P-shaped ASCII token (e.g. b'GET') is in-domain
    # and the result matches it characterwise & in length.
    Assert(ToSeq(result) == ToSeq(content))
    Assert(len(result) == len(content))
    return result"""


# ---------------------------------------------------------------------------
# FRAME-MUTATION RIVALS — must be REJECTED for INSUFFICIENT PERMISSION.
# content carries only Acc(list_pred(content), 1/2): the function may read it but
# must NOT write it. Each rival WRITES content to satisfy C3/C4 vacuously. Gold
# C3/C4 invariants kept verbatim so the rejection is attributable to the write.
# (#1 weakness class; a byte-fuzzer never mutates the input.)
# ---------------------------------------------------------------------------

# frame-mut-overwrite: build the result as gold, then write back into the
# half-permission `content` (a no-op self-assignment that STILL requires write
# permission the caller does not grant). Must reject: insufficient permission.
_FRAME_OVERWRITE = """\
    result = []  # type: List[int]
    j = 0
    n = len(content)
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(content), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n and n == len(content))
        Invariant(ToSeq(result) == ToSeq(content).take(j))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure n - j.
        Invariant(MustTerminate(n - j))
        # invariants-end
        Assert(ToSeq(content).take(j + 1) == ToSeq(content).take(j) + PSeq(content[j]))
        result = result + [content[j]]
        j = j + 1
    Assert(ToSeq(content).take(n) == ToSeq(content))
    # FRAME MUTATION: write the read-only half-permission input. Needs FULL
    # list_pred(content) permission the Requires (1/2) does not grant.
    if n > 0:
        content[0] = content[0]
    return result"""

# frame-mut-extend: append to the read-only input. A real patch that mutated the
# caller's method object would corrupt it; the half-permission frame forbids the
# write. Must reject for insufficient permission.
_FRAME_EXTEND = """\
    result = []  # type: List[int]
    content.append(0)
    j = 0
    n = len(content)
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(content), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n and n == len(content))
        Invariant(ToSeq(result) == ToSeq(content).take(j))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure n - j.
        Invariant(MustTerminate(n - j))
        # invariants-end
        Assert(ToSeq(content).take(j + 1) == ToSeq(content).take(j) + PSeq(content[j]))
        result = result + [content[j]]
        j = j + 1
    Assert(ToSeq(content).take(n) == ToSeq(content))
    return result"""


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN RIVALS — must be REJECTED (else SPEC-TOO-WEAK).
# ---------------------------------------------------------------------------

# weak-prepatch-bytes: the PRE-PATCH behaviour — for a byte token render the
# b'...'-wrapped OBJECT (prefix [98,39], content, suffix [39]); for a text token
# the identity. This is exactly model_prepatch.py. Length len+3 on the byte branch.
_WEAK_PREPATCH = """\
    # Adversary: pre-patch builtin_str(method) coercion. A byte token renders the
    # b'...'-wrapped object instead of decoding it.
    result = []  # type: List[int]
    if is_bytes:
        result = result + [98]
        result = result + [39]
        j = 0
        n = len(content)
        while j < n:
            # invariants-start
            Invariant(Acc(list_pred(content), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= j and j <= n and n == len(content))
            Invariant(ToSeq(result) == PSeq(98, 39) + ToSeq(content).take(j))
            # The loop consumes the caller's termination obligation with the
            # strictly decreasing, bounded-below measure n - j.
            Invariant(MustTerminate(n - j))
            # invariants-end
            Assert(ToSeq(content).take(j + 1) == ToSeq(content).take(j) + PSeq(content[j]))
            result = result + [content[j]]
            j = j + 1
        Assert(ToSeq(content).take(n) == ToSeq(content))
        result = result + [39]
    else:
        j = 0
        n = len(content)
        while j < n:
            # invariants-start
            Invariant(Acc(list_pred(content), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= j and j <= n and n == len(content))
            Invariant(ToSeq(result) == ToSeq(content).take(j))
            # The loop consumes the caller's termination obligation with the
            # strictly decreasing, bounded-below measure n - j.
            Invariant(MustTerminate(n - j))
            # invariants-end
            Assert(ToSeq(content).take(j + 1) == ToSeq(content).take(j) + PSeq(content[j]))
            result = result + [content[j]]
            j = j + 1
        Assert(ToSeq(content).take(n) == ToSeq(content))
    return result"""

# weak-truncate-last: copy all but the LAST element (loop bound n-1). Correct on
# the empty token (vacuous) and on every PREFIX, but drops the final character of
# every non-empty token. PARTIAL-DOMAIN: diverges only on the last index.
_WEAK_TRUNC = """\
    # Adversary: off-by-one — copy content[0 .. n-2], dropping the final character.
    result = []  # type: List[int]
    j = 0
    n = len(content)
    m = n - 1
    if m < 0:
        m = 0
    while j < m:
        # invariants-start
        Invariant(Acc(list_pred(content), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= m and m <= n and n == len(content))
        Invariant(ToSeq(result) == ToSeq(content).take(j))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure m - j.
        Invariant(MustTerminate(m - j))
        # invariants-end
        Assert(ToSeq(content).take(j + 1) == ToSeq(content).take(j) + PSeq(content[j]))
        result = result + [content[j]]
        j = j + 1
    return result"""

# weak-pad-empty: correct on every NON-EMPTY token, but for the EMPTY token (n==0)
# returns a one-element [71] ('G') instead of []. PARTIAL-DOMAIN on the length-0
# sub-domain. C4 (len(Result())==len(content)) is violated only when len==0.
_WEAK_PAD = """\
    result = []  # type: List[int]
    n = len(content)
    if n == 0:
        # Adversary: emit a spurious 'G' for the empty token only.
        result = result + [71]
        return result
    j = 0
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(content), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n and n == len(content))
        Invariant(ToSeq(result) == ToSeq(content).take(j))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure n - j.
        Invariant(MustTerminate(n - j))
        # invariants-end
        Assert(ToSeq(content).take(j + 1) == ToSeq(content).take(j) + PSeq(content[j]))
        result = result + [content[j]]
        j = j + 1
    Assert(ToSeq(content).take(n) == ToSeq(content))
    return result"""

# weak-nonterm-afterbuild: build the CORRECT result via the gold copy loop, then
# spin forever instead of returning. Under partial correctness this would verify
# vacuously (the postcondition is never reached); the C0 termination obligation
# (MustTerminate in the Requires) must make the verifier REJECT it — the terminal
# loop has no decreasing measure and so leaks the caller's obligation.
_WEAK_NONTERM = """\
    result = []  # type: List[int]
    j = 0
    n = len(content)
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(content), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n and n == len(content))
        Invariant(ToSeq(result) == ToSeq(content).take(j))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure n - j.
        Invariant(MustTerminate(n - j))
        # invariants-end
        Assert(ToSeq(content).take(j + 1) == ToSeq(content).take(j) + PSeq(content[j]))
        result = result + [content[j]]
        j = j + 1
    Assert(ToSeq(content).take(n) == ToSeq(content))
    # Adversary: never deliver the (correct) result.
    while True:
        # invariants-start
        Invariant(Acc(list_pred(content), 1 / 2))
        Invariant(Acc(list_pred(result)))
        # invariants-end
        result = result"""

# weak-uppercase-first: copy faithfully EXCEPT force the first character to upper
# 'G' (71). For a token whose first char is already 71 this is the identity; for
# any other (e.g. 'POST', first char 'P'==80, or lowercase 'get') it corrupts
# index 0. PARTIAL-DOMAIN on the first element. A real patch normalizing the
# leading byte would change the method (POST -> GOST) and fail the request.
_WEAK_UPPER = """\
    result = []  # type: List[int]
    j = 0
    n = len(content)
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(content), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n and n == len(content))
        Invariant(ToSeq(result) == ToSeq(content).take(j))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure n - j.
        Invariant(MustTerminate(n - j))
        # invariants-end
        Assert(ToSeq(content).take(j + 1) == ToSeq(content).take(j) + PSeq(content[j]))
        result = result + [content[j]]
        j = j + 1
    Assert(ToSeq(content).take(n) == ToSeq(content))
    # Adversary: overwrite the first result character with 'G' (71).
    if n > 0:
        result[0] = 71
    return result"""


SPEC_TESTS = [
    {
        "id": "pos-isbytes-split",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_ISBYTES),
        "rationale": (
            "structurally-different correct impl: split on is_bytes into two arms "
            "doing the identical forward copy (the result is independent of "
            "is_bytes). Each arm keeps the gold front-prefix invariant + per-element "
            "pin verbatim, so every proof obligation is discharged. If it fails => "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-append-shape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_APPEND),
        "rationale": (
            "same forward direction (no f(a+b) lemma needed, directive 3) but "
            "accumulates with list.append(...) instead of result + [x]; keeps the "
            "front-prefix invariant and per-element pin so the gold proof stays "
            "valid. A correct executable-shape variant must verify."
        ),
    },
    {
        "id": "admiss-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "the precondition (ASCII, no 39/92, half permission) must admit an "
            "F2P-shaped token (b'GET'); the appended shape asserts "
            "(ToSeq(result)==ToSeq(content), len match) are entailed by the kept "
            "invariant, so no proof gap. If it fails => PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mut-overwrite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_OVERWRITE),
        "refinement": (
            "writing content[0] models a coercion that mutates the caller's own "
            "method token in place. The real Session.request must NOT mutate the "
            "passed method object; a faithful patch that did would corrupt a "
            "caller-shared bytes/str (and in CPython str/bytes are immutable, so "
            "such a patch is not even expressible) — it would not faithfully "
            "implement to_native_string and would not resolve the F2P."
        ),
        "rationale": (
            "rejected by the permission system: content carries only "
            "Acc(list_pred(content), 1/2), so content[0]=... has insufficient "
            "permission to write. MANDATORY frame-mutation probe. If it verifies "
            "=> the read-only frame is broken (SPEC-TOO-WEAK / unsound frame)."
        ),
    },
    {
        "id": "frame-mut-extend",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_EXTEND),
        "refinement": (
            "content.append(0) mutates the caller's method token (lengthening it). "
            "A real coercion that appended to the passed-in method would change the "
            "request method observed downstream (e.g. b'GET' -> a longer token), "
            "failing test_encoded_methods (r.ok). Not a faithful to_native_string; "
            "does NOT resolve."
        ),
        "rationale": (
            "rejected for insufficient permission: append needs full "
            "list_pred(content), the Requires grants only 1/2. Second frame-"
            "mutation form (extend vs element-write). If it verifies => unsound "
            "frame."
        ),
    },
    {
        "id": "weak-prepatch-bytes",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PREPATCH),
        "refinement": (
            "this IS the pre-patch builtin_str(method) behaviour reproduced by "
            "model_prepatch.py: for a byte token b'GET' it builds the b'...'-wrapped "
            "object (the five chars b'GET') of length len+3, not the decoded GET. "
            "The unpatched repo fails the F2P test_encoded_methods "
            "(requests.request(b'GET', ...) returns 404, not r.ok). Does NOT "
            "resolve."
        ),
        "rationale": (
            "rejected by the dominant C3 (ToSeq(Result())==ToSeq(content)) and C4 "
            "(len(Result())==len(content)): the byte branch returns a length-(len+3) "
            "[98,39,...,39] sequence. This is the exact G-DIFF behaviour. If it "
            "verifies => SPEC-TOO-WEAK (the change is not sensed)."
        ),
    },
    {
        "id": "weak-truncate-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_TRUNC),
        "refinement": (
            "dropping the final character turns GET->GE, POST->POS — an invalid "
            "HTTP method that the server 404s. A real patch truncating the method "
            "fails test_encoded_methods (r.ok) and the redirect/POSTBIN F2P tests "
            "that send real methods. Does NOT resolve. PARTIAL-DOMAIN: it is "
            "vacuously correct on the empty token and on every prefix, diverging "
            "only on the last index — a boundary a byte-fuzzer misses."
        ),
        "rationale": (
            "rejected by C3/C4: ToSeq(result)==ToSeq(content).take(n-1) != "
            "ToSeq(content), and len==n-1 != n for any non-empty token. If it "
            "verifies => SPEC-TOO-WEAK on the last-element sub-domain."
        ),
    },
    {
        "id": "weak-pad-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PAD),
        "refinement": (
            "emitting a spurious 'G' for the empty token is wrong on the length-0 "
            "sub-domain only. A real patch with this special case would synthesize "
            "a 'G' method from an empty token, diverging from to_native_string "
            "(which returns '' unchanged / b''.decode()=='' ). Does NOT faithfully "
            "implement the coercion. PARTIAL-DOMAIN on len==0."
        ),
        "rationale": (
            "rejected by C4 (len(Result())==len(content)): for the empty token the "
            "impl returns length 1 != 0 (and C3 fails, [71]!=[]). If it verifies => "
            "SPEC-TOO-WEAK on the empty-token boundary."
        ),
    },
    {
        "id": "weak-nonterm-afterbuild",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_NONTERM),
        "refinement": (
            "computing the correct native token and then spinning forever "
            "refines to a Session.request whose coercion line is followed by an "
            "infinite loop: every request (and every test that issues one) hangs "
            "to the harness wall-clock. The harness records a timeout, not a "
            "pass — the patch does NOT resolve."
        ),
        "rationale": (
            "rejected by C0 (MustTerminate in the Requires): the terminal "
            "while-True loop carries no decreasing measure, so it cannot consume "
            "the caller's termination obligation (obligation leak). If it "
            "verifies => the spec enforces only PARTIAL correctness and a "
            "divergent impl passes vacuously (SPEC-TOO-WEAK on the termination "
            "dimension)."
        ),
    },
    {
        "id": "weak-uppercase-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_UPPER),
        "refinement": (
            "forcing the first character to 'G' (71) corrupts every method whose "
            "first char isn't 'G' (POST->GOST, get->Get-with-G... i.e. Get). A real "
            "patch normalizing the leading byte would change the HTTP method sent, "
            "failing the POSTBIN/redirect F2P tests and test_encoded_methods. Does "
            "NOT resolve. PARTIAL-DOMAIN on the first element."
        ),
        "rationale": (
            "rejected by C3 (ToSeq(Result())==ToSeq(content)): result[0]==71 != "
            "content[0] whenever content[0] != 71. If it verifies => SPEC-TOO-WEAK "
            "on index 0 — the value-level pin must catch a single mismatched index."
        ),
    },
]

# No @ContractOnly axioms and no CONSUMED axiom on this path (meta.axioms == []).
# The to_native_string correspondence is an A-reference deep model (the copy loop),
# validated == the real callee out-of-band by axiom_check.py / G-AX over the entire
# Requires domain (14 boundary + 126 full-domain sweep + 20000 fuzz tokens, text+
# bytes). There is no axiom Ensures the proof consumes, so nothing for the PBT
# axiom lane to falsify here.
AXIOM_TESTS = []
