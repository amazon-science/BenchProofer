# properties.py — PBT falsification battery for psf__requests-2931.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TEST is a FULL model.py source that shares the frozen spec EXACTLY and
# differs only inside an `# impl-start`/`# impl-end` region (region-surgery via
# _swap GUARANTEES same_spec). Each AXIOM_TEST is a self-contained probe run in
# the instance Docker image against the REAL callee.
#
# Defended surface (read model.py):
#   serialize_request_body(v):  v is READ-ONLY (Acc(v.is_bytes,1/2),Acc(v.data,1/2)).
#       Load-bearing post: Result().is_bytes == v.is_bytes  AND  Result().data == v.data.
#       This is the F2P discriminator (test_binary_put: a binary body stays bytes).
#   normalize_query_string(v):  v is READ-ONLY, plus Requires(Implies(v.is_bytes, is_ascii(v.data))).
#       Load-bearing post: Result().is_bytes == False  AND  Result().data == v.data.
#       The P2P query-normalization behaviour (params=b'test=foo' => '?test=foo').
#   to_native:  @Pure @ContractOnly axiom (A-consumed by site B); the real callee
#       is requests.utils.to_native_string(encoding='ascii'), Python-3 branch.
#
# NOTE on the oracle: the postconditions are GROUNDED in the input (== v.data,
# == v.is_bytes, == False) — NOT pinned to an opaque to_native(...) answer-key —
# so there is no "echo a wrong oracle and verify" attack at the postcondition.
# to_native is only consumed in site B's PROOF; the result is re-pinned to v.data.
# We therefore replace the ungrounded-oracle-echo class with an honest grounded
# positive control, and document this in 'assessment'.

from pathlib import Path

INSTANCE = "psf__requests-2931"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ----- exact impl-region anchors (the ONLY text any variant may touch) -------
_SERIALIZE_IMPL = "    r = Value(v.is_bytes, v.data)\n    return r"
_NORMALIZE_IMPL = ("    nd = to_native(v.is_bytes, v.data)\n"
                   "    r = Value(False, nd)\n"
                   "    return r")


# =============================================================================
# SPEC LANE
# =============================================================================
SPEC_TESTS = [

    # -------------------------------------------------------------------------
    # 1. FRAME-MUTATION (MANDATORY — v is read-only at 1/2 in BOTH functions).
    #    A rival that WRITES v's field to make the postcondition trivially true.
    #    Must REJECT for insufficient permission (only 1/2 held on v.data/is_bytes).
    # -------------------------------------------------------------------------
    {
        "id": "frame-mut-serialize-data",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SERIALIZE_IMPL,
            # try to satisfy Result().data==v.data by clobbering the input first;
            # writing v.data needs FULL permission but only 1/2 is held.
            "    v.data = v.data\n"
            "    r = Value(v.is_bytes, v.data)\n"
            "    return r",
        ),
        "refinement": (
            "A faithful real patch that re-assigns the incoming body/params value "
            "in place is not what the gold patch does (gold `return data` / "
            "`params = to_native_string(params)` rebinds a local, never mutates the "
            "caller's object); but more importantly the spec must forbid this — the "
            "input is read-only. If it verified despite writing the read-only input, "
            "the permission discipline would be hollow."),
        "rationale": (
            "REJECT comes from the permission system: Requires only "
            "Acc(v.data, 1/2); a write to v.data needs full permission, so Nagini "
            "rejects for INSUFFICIENT PERMISSION before any postcondition is even "
            "considered."),
    },
    {
        "id": "frame-mut-serialize-tag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SERIALIZE_IMPL,
            "    v.is_bytes = v.is_bytes\n"
            "    r = Value(v.is_bytes, v.data)\n"
            "    return r",
        ),
        "refinement": (
            "Mutating the caller's type tag is not the gold behaviour and would be "
            "an observable side effect on the source value; the spec must reject the "
            "write outright."),
        "rationale": (
            "REJECT from the permission system: Acc(v.is_bytes, 1/2) is read-only; "
            "assigning v.is_bytes needs full permission."),
    },
    {
        "id": "frame-mut-normalize-data",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _NORMALIZE_IMPL,
            "    v.data = v.data\n"
            "    nd = to_native(v.is_bytes, v.data)\n"
            "    r = Value(False, nd)\n"
            "    return r",
        ),
        "refinement": (
            "The query coercion `params = to_native_string(params)` rebinds a local; "
            "it never writes back into the caller's value. A patch that mutated the "
            "source value in place would be an unintended side effect; the read-only "
            "input forbids it at the spec level."),
        "rationale": (
            "REJECT from the permission system: only Acc(v.data, 1/2) is held in "
            "normalize_query_string; the write needs full permission."),
    },

    # -------------------------------------------------------------------------
    # 2. PARTIAL-DOMAIN / TYPE-SWAP on serialize (the ACTUAL F2P bug, prepatch).
    #    Native-decode the body instead of preserving it. Correct on native-text
    #    input (is_bytes already False) but WRONG on a binary body: forces the
    #    native-text tag, violating Result().is_bytes == v.is_bytes, AND for a
    #    NON-ASCII binary body has no way to discharge to_native's Requires.
    # -------------------------------------------------------------------------
    {
        "id": "weak-serialize-native-decode",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SERIALIZE_IMPL,
            # the pre-patch body path: route the body through the native decoder.
            "    nd = to_native(v.is_bytes, v.data)\n"
            "    r = Value(False, nd)\n"
            "    return r",
        ),
        "refinement": (
            "This is the pre-patch body path (`return to_native_string(data)`). On "
            "the F2P input u'ööö'.encode('utf-8') (all octets >= 128, is_bytes=True) "
            "the real to_native_string raises UnicodeDecodeError and, even where it "
            "wouldn't, the body comes back as a native str so isinstance(body, bytes) "
            "is False — test_binary_put FAILS. Its faithful real patch does NOT "
            "resolve the F2P."),
        "rationale": (
            "REJECT from TWO clauses: (a) Result().is_bytes == v.is_bytes is violated "
            "for a binary input (the impl forces Value(False, ...)); (b) to_native's "
            "Requires(Implies(v_is_bytes, is_ascii(v_data))) is UNESTABLISHED — "
            "serialize_request_body has no ASCII precondition, so a binary body need "
            "not be ASCII. Either is fatal."),
    },
    {
        "id": "weak-serialize-flip-tag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SERIALIZE_IMPL,
            # keep content but force the tag to a constant: violates is_bytes==v.is_bytes
            # on whichever sub-domain disagrees with the constant.
            "    r = Value(True, v.data)\n"
            "    return r",
        ),
        "refinement": (
            "Always tagging the body as binary resolves test_binary_put (its only "
            "assertion is isinstance(body, bytes)) but is NOT a faithful patch: a "
            "native-text (str) body would be mis-reported as bytes, breaking every "
            "P2P that sends a str body. The corresponding real patch (`return "
            "bytes(data)` unconditionally) would not resolve the P2P suite."),
        "rationale": (
            "REJECT from Result().is_bytes == v.is_bytes: for a native-text input "
            "(v.is_bytes == False) the impl returns is_bytes == True, contradicting "
            "the postcondition. Partial-domain: correct only on binary inputs."),
    },

    # -------------------------------------------------------------------------
    # 3. NORMALIZE TAG-SWAP — preserve the tag instead of normalizing to native.
    #    Violates Result().is_bytes == False on a binary query value.
    # -------------------------------------------------------------------------
    {
        "id": "weak-normalize-preserve-tag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _NORMALIZE_IMPL,
            # body-style identity packaging at the query site: keeps the binary tag.
            "    r = Value(v.is_bytes, v.data)\n"
            "    return r",
        ),
        "refinement": (
            "Skipping the to_native_string coercion at the query site (leaving a "
            "bytes params as bytes) reproduces the pre-patch query handling for a "
            "bytes value; _encode_params would then receive bytes where the gold path "
            "feeds it native str, changing the query-building path. The faithful patch "
            "(omit the `params = to_native_string(params)` line) is NOT the gold "
            "behaviour the P2P test_params_bytes_are_encoded pins."),
        "rationale": (
            "REJECT from Result().is_bytes == False: a binary query value "
            "(v.is_bytes == True) is returned with is_bytes == True, contradicting "
            "the normalization postcondition."),
    },
    {
        "id": "weak-normalize-drop-content",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _NORMALIZE_IMPL,
            # right tag, wrong content: return native text with EMPTY content.
            "    empty = PSeq()  # type: PSeq[int]\n"
            "    r = Value(False, empty)\n"
            "    return r",
        ),
        "refinement": (
            "Returning native text whose characters are dropped (empty content) would "
            "turn params=b'test=foo' into an empty query string '?', so "
            "test_params_bytes_are_encoded ('?test=foo') FAILS. Its faithful patch "
            "does not resolve the P2P."),
        "rationale": (
            "REJECT from Result().data == v.data: an empty PSeq does not equal a "
            "non-empty input content. Content-dropping is sensed by the content clause."),
    },

    # -------------------------------------------------------------------------
    # 4. POSITIVE CONTROL (soundness) — a structurally-DIFFERENT but CORRECT impl
    #    that MUST verify (else SPEC-TOO-STRONG). Reshape via local variables and
    #    reordering; keep the gold proof obligations (identity packaging) intact.
    # -------------------------------------------------------------------------
    {
        "id": "pos-serialize-locals",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _SERIALIZE_IMPL,
            # bind the tag and content into locals first, then construct — same value,
            # different executable shape. Value.__init__'s Ensures pins the post-state.
            "    tag = v.is_bytes\n"
            "    content = v.data\n"
            "    r = Value(tag, content)\n"
            "    return r",
        ),
        "rationale": (
            "A correct identity-packaging impl with a different local-variable shape "
            "must verify: Value.__init__ Ensures pins is_bytes==tag==v.is_bytes and "
            "data==content==v.data, discharging both serialize postconditions. If this "
            "could not verify, the spec would be SPEC-TOO-STRONG."),
    },
    {
        "id": "pos-normalize-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _NORMALIZE_IMPL,
            # inline the to_native call into the constructor argument — same value,
            # no intermediate `nd`. Proof still consumes to_native's Ensures.
            "    r = Value(False, to_native(v.is_bytes, v.data))\n"
            "    return r",
        ),
        "rationale": (
            "Structurally different (inlined call, no `nd` local) but correct: the "
            "precondition Implies(v.is_bytes, is_ascii(v.data)) discharges to_native's "
            "Requires, and to_native's Ensures(Result()==v_data) gives Result().data "
            "== v.data; the constant False tag gives Result().is_bytes == False. Must "
            "verify (else SPEC-TOO-STRONG)."),
    },

    # -------------------------------------------------------------------------
    # 5. ADMISSIBILITY — confirm the precondition admits a normal F2P-shaped input
    #    by self-calling each function from a fresh in-domain Value and asserting
    #    the post-state. If a legitimate input can't establish Requires =>
    #    PRECOND-TOO-STRONG. (Body path: a binary, NON-ASCII payload — the F2P
    #    shape. Query path: a binary ASCII payload — the P2P shape.)
    # -------------------------------------------------------------------------
    {
        "id": "admiss-serialize-binary-nonascii",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _SERIALIZE_IMPL,
            "    r = Value(v.is_bytes, v.data)\n"
            "    return r\n"
            "\n"
            "\n"
            "def _admiss_serialize() -> None:\n"
            "    # F2P-shaped input: a binary body with a non-ASCII octet (0xc3=195).\n"
            "    payload = PSeq(195, 182, 195, 182)  # type: PSeq[int]\n"
            "    src = Value(True, payload)\n"
            "    out = serialize_request_body(src)\n"
            "    # the body stays binary with identical content (test_binary_put).\n"
            "    Assert(out.is_bytes == True)\n"
            "    Assert(out.data == payload)",
        ),
        "rationale": (
            "serialize_request_body's Requires (just Acc(v,1/2)) admits a freshly "
            "built binary, non-ASCII Value — exactly the F2P shape. The call site "
            "verifies and the asserted post-state (binary tag preserved, content "
            "preserved) holds. If this failed, the precondition would be "
            "PRECOND-TOO-STRONG (rejecting the very input the fix targets)."),
    },
    {
        "id": "admiss-normalize-binary-ascii",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _NORMALIZE_IMPL,
            "    nd = to_native(v.is_bytes, v.data)\n"
            "    r = Value(False, nd)\n"
            "    return r\n"
            "\n"
            "\n"
            "def _admiss_normalize() -> None:\n"
            "    # P2P-shaped input: a binary ASCII query value b'test=foo'.\n"
            "    content = PSeq(116, 101, 115, 116, 61, 102, 111, 111)  # type: PSeq[int]\n"
            "    Assert(is_ascii(content))\n"
            "    src = Value(True, content)\n"
            "    out = normalize_query_string(src)\n"
            "    Assert(out.is_bytes == False)\n"
            "    Assert(out.data == content)",
        ),
        "rationale": (
            "normalize_query_string's Requires (Acc(v,1/2) plus binary=>ASCII) admits "
            "a binary ASCII query value 'test=foo' — exactly the P2P shape. The ASCII "
            "precondition is establishable (Assert(is_ascii(content)) discharges it) "
            "and the call verifies with the normalized post-state. If this failed, "
            "PRECOND-TOO-STRONG."),
    },
]


# =============================================================================
# AXIOM LANE  — to_native is @Pure @ContractOnly (A-consumed), models the REAL
# requests.utils.to_native_string(encoding='ascii'). Both soundness (real callee
# matches Ensures on the Requires domain) and containment (every callee-input the
# MODEL can reach lies in the Requires domain) apply. Probes import the REAL
# callee installed in the instance image; gold patch is applied (it adds the site
# B call). Logic mirrors / strengthens tasks/.../axiom_check.py.
# =============================================================================
AXIOM_TESTS = [
    {
        "id": "ax-sound-to_native",
        "axiom": "to_native",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": r'''
"""AXIOM-SOUNDNESS for to_native.

Runs the REAL requests.utils.to_native_string(encoding='ascii') (Python-3 branch
is what the eval image runs) over the axiom's Requires domain and asserts the
Ensures(Result() == v_data) AND that the result is native text (str), as the
caller (site B) relies on by dropping the binary tag. Domain (axiom Requires):
  - native-text (str) inputs: any code points (identity branch);
  - binary (bytes) inputs whose octets are ALL ASCII (< 128).
Fuzzes boundaries + sentinels + the full ASCII octet range; additionally confirms
the decoder REJECTS non-ASCII binary (outside Requires) — exactly why the body
path must NOT route through it. Exit 0 iff every obligation holds.
"""
import random
import sys

try:
    from requests.utils import to_native_string as callee
    label = "requests.utils.to_native_string (real callee, gold applied)"
except Exception as e:  # pragma: no cover - real callee must exist in image
    print("FAIL: could not import requests.utils.to_native_string:", e)
    sys.exit(1)


def check_native(value, content):
    if isinstance(value, bytes):
        assert all(b < 128 for b in value), "bad test input: not ASCII"
    out = callee(value)
    assert isinstance(out, str), (
        "AXIOM-UNSOUND on %r: result %r not native str" % (value, out))
    observed = [ord(ch) for ch in out]
    assert observed == content, (
        "AXIOM-UNSOUND on %r: callee content %r != axiom Ensures %r"
        % (value, observed, content))


def check_rejects(value):
    raised = False
    try:
        callee(value)
    except Exception:
        raised = True
    assert raised, "decoder did NOT reject non-ASCII binary %r" % (value,)


# --- boundary: native-text identity ---
text_boundary = ["", "test=foo", "a", "ABC xyz", "0123456789",
                 "!$&'()*+,;=~:@,", "x=1&y=2", "key=value&k2=v2",
                 chr(0), chr(127)]
for s in text_boundary:
    check_native(s, [ord(c) for c in s])

# --- boundary: ASCII binary decodes to identical content ---
bytes_boundary = [b"", b"test=foo", b"A", b"0123456789", b"x=1&y=2",
                  b"!$&'()*+,;=~:@,", bytes([0]), bytes([127])]
for b in bytes_boundary:
    check_native(b, list(b))

# --- fuzz the full ASCII octet domain (str and bytes) ---
rng = random.Random(2931)
ascii_codes = list(range(0, 128))
for _ in range(20000):
    n = rng.randint(0, 24)
    codes = [rng.choice(ascii_codes) for _ in range(n)]
    check_native("".join(chr(c) for c in codes), codes)
    check_native(bytes(codes), codes)

# --- sentinels OUTSIDE Requires: non-ASCII binary must be rejected ---
non_ascii = [b"\xc3\xb6\xc3\xb6\xc3\xb6", b"\x80", b"\xff",
             b"caf\xc3\xa9", b"\xe2\x80\xa2", bytes([128]), bytes([200])]
for b in non_ascii:
    check_rejects(b)

print("AXIOM-SOUND [%s]: Ensures(Result()==v_data) holds on %d text + %d bytes "
      "boundary + 40000 ASCII fuzz; rejects %d non-ASCII binary"
      % (label, len(text_boundary), len(bytes_boundary), len(non_ascii)))
sys.exit(0)
''',
        "rationale": (
            "If the real to_native_string violated Ensures(Result()==v_data) or "
            "returned non-str anywhere in the Requires domain, the A-consumed axiom "
            "would be AXIOM-UNSOUND and site B's proof of Result().data==v.data would "
            "rest on a false premise. Flag-dependency: encoding='ascii' (the function "
            "default and requests' call site), per meta.axioms[].flag_dependency."),
    },
    {
        "id": "ax-cover-to_native",
        "axiom": "to_native",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": r'''
"""AXIOM-CONTAINMENT for to_native.

Every callee-input the MODEL can reach must lie inside the axiom's Requires
domain (Implies(v_is_bytes, is_ascii(v_data))). to_native is reached ONLY from
normalize_query_string (site B); site A's body path does NOT call it. The model
passes (v.is_bytes, v.data) straight through, and normalize_query_string's OWN
precondition is Requires(Implies(v.is_bytes, is_ascii(v.data))) — IDENTICAL to
to_native's Requires. So the reachable callee-input set is, by construction, a
SUBSET of the axiom's domain.

This probe makes the containment claim concrete on the real callee: it enumerates
the model-reachable inputs (native text with ANY content; binary with ASCII-only
octets — never non-ASCII binary, which the model's precondition forbids) and
asserts the real to_native_string is DEFINED (does not raise) on each — i.e. each
reachable input genuinely sits in the callee's defined domain that the axiom
Requires carves out. It also asserts the model NEVER reaches a non-ASCII binary
input by construction: the one place that could (a binary query value) is gated
by normalize_query_string's ASCII precondition. Exit 0 iff every reachable input
is covered (callee defined) and the excluded region is exactly the non-ASCII
binary the model cannot reach.
"""
import random
import sys

try:
    from requests.utils import to_native_string as callee
except Exception as e:
    print("FAIL: could not import requests.utils.to_native_string:", e)
    sys.exit(1)


def reachable_defined(value):
    # a model-reachable callee-input: must be in the callee's defined domain.
    try:
        out = callee(value)
    except Exception as e:
        print("AXIOM-TOO-WEAK-FOR-CALLER: model-reachable input %r raised %r "
              "but the axiom Requires claims it is in-domain" % (value, e))
        sys.exit(1)
    assert isinstance(out, str)


# (1) native text — model passes is_bytes=False with ANY content. The callee's
#     identity branch is total over str, so every reachable text input is covered.
for s in ["", "test=foo", "a", "ABC", chr(0), chr(127), "ö", "•", "𝄞",
          "high\U0001F600cp"]:
    reachable_defined(s)

# (2) binary — model passes is_bytes=True ONLY when is_ascii(v.data) (site B
#     precondition). Enumerate ASCII-octet binary across the full domain; each is
#     covered (callee defined).
rng = random.Random(7)
for _ in range(5000):
    n = rng.randint(0, 32)
    codes = [rng.randint(0, 127) for _ in range(n)]
    reachable_defined(bytes(codes))

# (3) the EXCLUDED region (non-ASCII binary) is NOT model-reachable: site B's
#     precondition Implies(v.is_bytes, is_ascii(v.data)) forbids it, and site A
#     never calls to_native at all. Demonstrate the callee is UNDEFINED there, so
#     containment matters: if the model could reach it, the axiom would be too
#     weak. The model cannot, so this is sound (containment, not full coverage).
excluded_unreachable = [b"\xc3\xb6", b"\x80", b"\xff", b"\xe2\x80\xa2"]
for b in excluded_unreachable:
    raised = False
    try:
        callee(b)
    except Exception:
        raised = True
    assert raised, ("callee unexpectedly defined on %r; this would not affect "
                    "containment but indicates a domain-model drift" % (b,))

print("AXIOM-COVERED: every model-reachable to_native input (native text any "
      "content + ASCII-octet binary) lies in the callee's defined domain; the "
      "non-ASCII binary region the axiom excludes is unreachable by the model "
      "(site B ASCII precondition; site A never calls to_native).")
sys.exit(0)
''',
        "rationale": (
            "Containment, not whole-domain coverage: normalize_query_string's own "
            "precondition is byte-identical to to_native's Requires, so the reachable "
            "callee-input set is a subset of the axiom domain by construction. A "
            "reachable input outside the domain (e.g. if site B could pass a non-ASCII "
            "binary) would be AXIOM-TOO-WEAK-FOR-CALLER; the probe shows none exists."),
    },
]
