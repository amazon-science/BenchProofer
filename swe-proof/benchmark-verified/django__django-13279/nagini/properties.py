# properties.py — PBT falsification battery for django__django-13279. NOT a Nagini
# module; a record of adversarial cases the runner (swebench_nagini.pbt) executes.
#
# Defended surface (read from model.py + refinement.md + mapping.md + the gold patch):
#   serialize(payload: List[int], algorithm: int) -> Frame
#   The session serializer (SessionBase.encode) that gained a compatibility-regime
#   branch: when DEFAULT_HASHING_ALGORITHM == 'sha1' (ALGO_LEGACY) it must emit a
#   LEGACY frame the unchanged legacy reader (_legacy_decode) can read back to the
#   record; otherwise it emits the modern signed frame (signing.dumps). The record's
#   serialized payload is carried as List[int]/PSeq[int]; the encoded string is the
#   minimal Frame{tag, mac, payload} carrier.
#
#   Precondition (ONE input, READ-ONLY):
#     (P1) Requires(Acc(list_pred(payload), 1 / 2))        # HALF permission => no write
#   Postcondition (five clauses):
#     (Q1) Ensures(Acc(list_pred(payload), 1 / 2))         # returns the read perm
#     (Q2) Ensures(Acc(Result().tag) and Acc(Result().mac) and Acc(Result().payload))
#     (Q3) Ensures(Implies(algorithm == ALGO_LEGACY,       # <-- LOAD-BEARING (F2P)
#             legacy_read(Result().tag, Result().mac, Result().payload) == ToSeq(payload)))
#     (Q4) Ensures(Implies(algorithm != ALGO_LEGACY, Result().tag == FMT_MODERN))
#     (Q5) Ensures(Implies(algorithm != ALGO_LEGACY,       # <-- LOAD-BEARING (P2P)
#             modern_read(Result().tag, Result().mac, Result().payload) == ToSeq(payload)))
#
#   legacy_read(tag, mac, payload) := payload if (tag==FMT_LEGACY and
#     mac==keyed_digest(payload)) else empty_payload()   (a @Pure deep model).
#   modern_read(tag, mac, payload) := payload if (tag==FMT_MODERN and
#     mac==modern_digest(payload)) else empty_payload()  (a @Pure deep model).
#   Q5 pins the modern arm's CARRIED RECORD to the input (the default-regime
#   round trip every session test exercises), so a modern-tagged frame carrying
#   a different record (empty / constant / truncated) is rejected.
#
# FRAME-MUTATION lane is MANDATORY: payload is Acc(...,1/2) (read-only). A rival
#   that WRITES to payload (here a no-op store payload[0]=payload[0]) must be
#   rejected for INSUFFICIENT PERMISSION (the project's #1 weakness class; a
#   byte-fuzzer never tries to mutate the input). The gold body is kept verbatim so
#   the rejection is attributable solely to the write.
#
# UNGROUNDED-ORACLE-ECHO: there is NO wrong echo here. Q3 is pinned through the
#   @Pure deep model legacy_read, which is GROUNDED entirely in the Result's own
#   fields and the input payload: legacy_read(t,m,p) returns a NON-EMPTY value
#   (== ToSeq(payload)) ONLY when t==FMT_LEGACY AND m==keyed_digest(p) AND
#   p==ToSeq(payload). keyed_digest is an opaque @ContractOnly @Pure digest — a
#   rival cannot fabricate a mac that matches keyed_digest(p) for a wrong p, and
#   legacy_read of a modern-tagged frame is empty_payload(). The unique satisfier is
#   a genuine legacy frame carrying the actual payload and its true digest. So the
#   honest control is the cheapest CORRECT impl (the branch-reorder positive
#   control below), not a wrong echo. See 'assessment'.
#
# PARTIAL-DOMAIN lane: the strong attacks all target Q3 (the F2P-pinned legacy
#   round trip) on a non-empty record while staying correct on the empty record {}:
#   emit a legacy frame carrying the EMPTY payload (weak-legacy-empty); emit the
#   MODERN frame in the legacy regime (weak-prepatch, the literal G-DIFF pre-patch);
#   build the legacy frame with a non-legacy tag (weak-legacy-modern-tag). Each is
#   rejected by Q3 and each faithful real patch fails the F2P legacy round trip.
#
# CONTROL-FLOW-EFFECT lane: N/A. serialize is a pure value-returning frame builder;
#   there is no raise / return-vs-fallthrough / side-effect difference invisible to
#   the Frame value abstraction. The only genuine control-flow point — the regime
#   branch (legacy vs modern) — is fully captured by Q3/Q4 as VALUES (the emitted
#   tag and the round-trip identity), so a capability-token rival adds nothing.
#
# NOTE on Q4/Q5 (modern regime): Q4 pins the modern arm to FMT_MODERN and Q5 pins
#   the modern round trip (the carried record must be the input record). Q4 is
#   slightly CONSERVATIVE relative to the test suite (the P2P test_decode only
#   requires decode(encode(x))==x, and decode() falls back to _legacy_decode, so a
#   patch that emitted legacy frames in BOTH regimes would still round-trip). A
#   stronger-than-needed spec stays SOUND (verify still implies resolve); so we do
#   NOT author a "legacy-frame-in-modern-regime" REJECT case claiming it would not
#   resolve (that refinement would be false). Q4's correctness is exercised by the
#   positive control's modern arm instead. Q5 is NOT conservative: a modern frame
#   carrying a different record corrupts every default-regime session (the
#   round-trip P2P observable) and its faithful patch does not resolve.
#
# AXIOM lane: TWO @ContractOnly consumed axioms (keyed_digest, modern_serialize)
#   plus a deep_model_reference (legacy_read). Both axioms have NO Requires domain
#   restriction (keyed_digest: Ensures(True); modern_serialize: Ensures only the
#   modern tag), so caller-domain CONTAINMENT is trivially satisfied — every
#   PSeq[int] payload the model reaches is in-domain (documented; no vacuous probe).
#   The SOUNDNESS obligations the proof actually consumes are checked against the
#   REAL Django callees in-container (reusing axiom_check.py's logic):
#     - keyed_digest <-> SessionBase._hash: deterministic + ':'-free hex digest;
#     - modern_serialize <-> signing.dumps: its output fed to _legacy_decode never
#       recovers the record (the FMT_MODERN tag fact);
#     - (bonus, gold-only) the F2P route: with sha1, _legacy_decode(encode(d))==d.
from pathlib import Path

INSTANCE = "django__django-13279"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen `serialize` impl-region body, verbatim (everything strictly BETWEEN
# serialize's `# impl-start` / `# impl-end`). Every spec variant _swap()s ONLY this
# block, so the edit never touches the spec (axioms/pure/pre-/post-conditions
# regions + signatures, INCLUDING the separate Frame.__init__ impl region).
# same_spec is computed over the spec_view, which elides every impl region, so
# swapping inside here is guaranteed same_spec.
_IMPL = """\
    if algorithm == ALGO_LEGACY:
        body = ToSeq(payload)
        return Frame(FMT_LEGACY, keyed_digest(body), body)
    return modern_serialize(ToSeq(payload))"""

assert _BASE.count(_IMPL) == 1, "serialize impl region drifted from expected text"


def _impl(new_body):
    """Full model.py variant with ONLY serialize's impl-region body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness / admissibility) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-reorder: structurally DIFFERENT but behaviourally identical. The modern
# (non-legacy) regime is handled FIRST via the negated guard `algorithm !=
# ALGO_LEGACY`, then the legacy frame is built. No loop, no induction lemma — Q3
# unfolds to body == ToSeq(payload) i.e. ToSeq(payload)==ToSeq(payload) and Q4 to
# modern_serialize(..).tag == FMT_MODERN, both held by the reordered shape exactly
# as by the gold. If it fails => SPEC-TOO-STRONG (a faithful correct impl rejected).
_POS_REORDER = """\
    if algorithm != ALGO_LEGACY:
        return modern_serialize(ToSeq(payload))
    body = ToSeq(payload)
    return Frame(FMT_LEGACY, keyed_digest(body), body)"""

# admiss-reads: an admissibility positive control. The precondition is the
# non-trivial heap permission Acc(list_pred(payload), 1/2); this control confirms
# it ADMITS the reads a normal F2P-shaped (non-empty) record needs — it reads
# len(payload) and ToSeq(payload) under the half-permission and asserts those reads
# succeed, before running the gold frame-builder body. No write, so no permission
# demand beyond the spec. If the half-permission rejected a legitimate record =>
# PRECOND-TOO-STRONG.
_ADMISS = """\
    Assert(len(payload) >= 0)
    Assert(ToSeq(payload) == ToSeq(payload))  # read admitted under Acc(...,1/2)
    if algorithm == ALGO_LEGACY:
        body = ToSeq(payload)
        return Frame(FMT_LEGACY, keyed_digest(body), body)
    return modern_serialize(ToSeq(payload))"""


# ---------------------------------------------------------------------------
# FRAME-MUTATION RIVAL (MANDATORY — payload is Acc(...,1/2) read-only).
# Must be REJECTED for INSUFFICIENT PERMISSION.
# ---------------------------------------------------------------------------

# frame-mut-write: keeps the gold frame-builder body VERBATIM (so the rejection is
# attributable solely to the added write, not to a value mismatch), then WRITES
# BACK into the read-only input: payload[0] = payload[0]. A no-op store, but a
# STORE — it demands FULL list_pred(payload) write permission, which the caller
# only granted at 1/2. The verifier must reject for insufficient permission.
_FRAME_MUT = """\
    if algorithm == ALGO_LEGACY:
        body = ToSeq(payload)
        if len(payload) > 0:
            payload[0] = payload[0]  # FRAME VIOLATION: write to read-only input
        return Frame(FMT_LEGACY, keyed_digest(body), body)
    return modern_serialize(ToSeq(payload))"""


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN RIVALS — must be REJECTED (else SPEC-TOO-WEAK).
# Each shares the frozen spec exactly and changes only serialize's impl region.
# ---------------------------------------------------------------------------

# weak-prepatch: the literal PRE-PATCH bug (model_prepatch.py) — emit the MODERN
# frame regardless of the regime. In the legacy regime the result has
# tag==FMT_MODERN, so legacy_read(FMT_MODERN, ..) == empty_payload(), which is !=
# ToSeq(payload) for a non-empty record. Rejected by Q3. This is exactly what
# G-DIFF senses.
_WEAK_PREPATCH = """\
    return modern_serialize(ToSeq(payload))"""

# weak-legacy-empty: PARTIAL-DOMAIN. Build a genuine legacy frame (right tag, a
# matching digest) but carry the EMPTY payload. legacy_read(FMT_LEGACY,
# keyed_digest(empty), empty) == empty, which == ToSeq(payload) ONLY when the
# record is empty ({}). Correct on the empty record, wrong on every non-empty one
# (incl. the F2P record {'a test key':'a test value'}). Rejected by Q3.
_WEAK_LEGACY_EMPTY = """\
    if algorithm == ALGO_LEGACY:
        empty = empty_payload()
        return Frame(FMT_LEGACY, keyed_digest(empty), empty)
    return modern_serialize(ToSeq(payload))"""

# weak-legacy-modern-tag: PARTIAL-DOMAIN on the frame TAG. Build the legacy frame
# carrying the real payload and its true digest, but stamp it with FMT_MODERN.
# legacy_read of a non-legacy tag is empty_payload(), so Q3 fails for a non-empty
# record (correct only for the empty record). A near-miss supporting case isolating
# exactly the tag field that distinguishes a legacy-readable frame.
_WEAK_LEGACY_MODERN_TAG = """\
    if algorithm == ALGO_LEGACY:
        body = ToSeq(payload)
        return Frame(FMT_MODERN, keyed_digest(body), body)
    return modern_serialize(ToSeq(payload))"""

# weak-modern-empty: PARTIAL-DOMAIN on the MODERN arm. Correct in the legacy
# regime, but in the modern regime hand the modern serializer the EMPTY payload
# instead of the record. The emitted frame is genuinely modern-tagged (Q4 holds)
# yet carries the empty record, so modern_read returns empty != ToSeq(payload)
# for a non-empty record. Rejected by Q5.
_WEAK_MODERN_EMPTY = """\
    if algorithm == ALGO_LEGACY:
        body = ToSeq(payload)
        return Frame(FMT_LEGACY, keyed_digest(body), body)
    return modern_serialize(empty_payload())"""


SPEC_TESTS = [
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": (
            "structurally-different CORRECT impl: the modern regime is handled "
            "first via the negated guard (algorithm != ALGO_LEGACY), then the "
            "legacy frame is built. No loop / no induction lemma; Q3 still unfolds "
            "to ToSeq(payload)==ToSeq(payload) and Q4 to modern tag, both held. If "
            "it fails => SPEC-TOO-STRONG (a faithful correct impl rejected)."
        ),
    },
    {
        "id": "admiss-reads",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "the non-trivial precondition Acc(list_pred(payload), 1/2) must admit "
            "the reads a normal (non-empty) record needs. The control reads "
            "len(payload) and ToSeq(payload) under the half-permission and asserts "
            "those reads succeed before the gold frame builder. If it fails => "
            "PRECOND-TOO-STRONG (the half-permission would reject a legitimate "
            "record)."
        ),
    },
    {
        "id": "frame-mut-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUT),
        "refinement": (
            "the gold encode/_legacy_encode reads the caller's session_dict and "
            "serializes it; it NEVER writes back into the caller's serialized "
            "payload buffer. A faithful real patch that mutated the shared payload "
            "in place (e.g. rewrote the serialized bytes the caller still holds) "
            "would corrupt the caller's record and diverge from the gold's "
            "read-only serialization — it would not be the gold patch and would "
            "not faithfully resolve. The store here is a no-op only by coincidence; "
            "the spec must forbid ANY write to the read-only input."
        ),
        "rationale": (
            "REJECTED by the permission system: payload is granted at "
            "Acc(list_pred(payload), 1/2) (P1); the store payload[0]=payload[0] "
            "demands FULL write permission, unavailable at 1/2, so the verifier "
            "rejects for INSUFFICIENT PERMISSION. The gold frame-builder body is "
            "kept verbatim so the rejection is attributable solely to the write. "
            "If it verifies => the read-only frame is not enforced (the #1 "
            "weakness class)."
        ),
    },
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PREPATCH),
        "refinement": (
            "this is the literal PRE-PATCH behaviour (model_prepatch.py / the "
            "unpatched encode): always `return signing.dumps(...)`, ignoring the "
            "regime selector. Its faithful real patch is the unpatched repo, which "
            "under DEFAULT_HASHING_ALGORITHM='sha1' emits a modern signed frame; "
            "_legacy_decode(encode({'a test key':'a test value'})) returns {} (the "
            "modern frame is not a legacy frame), != the record — failing the F2P "
            "test_default_hashing_algorith_legacy_decode. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q3: in the legacy regime the result has tag==FMT_MODERN "
            "(the modern_serialize axiom), so legacy_read(FMT_MODERN, ..) == "
            "empty_payload() != ToSeq(payload) for the non-empty F2P record. This "
            "is exactly the clause G-DIFF flags on the pre-patch model. If it "
            "verifies => SPEC-TOO-WEAK (the legacy round trip would not be "
            "enforced)."
        ),
    },
    {
        "id": "weak-legacy-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_LEGACY_EMPTY),
        "refinement": (
            "a real patch whose _legacy_encode serialized the EMPTY record instead "
            "of session_dict (serialized = serializer().dumps({})) would build a "
            "well-formed legacy frame that _legacy_decode reads back to {} for "
            "every input — so _legacy_decode(encode({'a test key':'a test value'})) "
            "== {} != the record, failing the F2P. Correct ONLY on the empty record "
            "{}, so it is a true PARTIAL-DOMAIN break (not a blanket wrong impl). "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q3: legacy_read(FMT_LEGACY, keyed_digest(empty), empty) == "
            "empty (the carried digest matches the empty payload, so the legacy "
            "reader returns it), and empty == ToSeq(payload) holds only for the "
            "empty record. For the non-empty F2P record Q3 fails. The divergence is "
            "confined to the non-empty sub-domain. If it verifies => SPEC-TOO-WEAK "
            "(the round trip would be pinned only on the empty record)."
        ),
    },
    {
        "id": "weak-legacy-modern-tag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_LEGACY_MODERN_TAG),
        "refinement": (
            "a real patch that, in the sha1 regime, emitted a frame the legacy "
            "reader does not accept as a legacy frame (e.g. produced a structurally "
            "non-legacy / wrongly-tagged string) would make "
            "_legacy_decode(encode(data)) fail to recover data — exactly the bug "
            "the patch fixes. Correct only on the empty record (legacy_read returns "
            "empty for a non-legacy tag). PARTIAL-DOMAIN on the frame format tag. "
            "Does NOT resolve. Supporting near-miss isolating the tag field, still "
            "carrying a real refinement."
        ),
        "rationale": (
            "REJECTED by Q3: legacy_read(FMT_MODERN, keyed_digest(body), body) == "
            "empty_payload() (legacy_read accepts only FMT_LEGACY), which != "
            "ToSeq(payload) for the non-empty F2P record. If it verifies => "
            "SPEC-TOO-WEAK (the legacy frame format would not be pinned)."
        ),
    },
    {
        "id": "weak-modern-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_MODERN_EMPTY),
        "refinement": (
            "a real patch whose modern arm serialized the EMPTY record instead of "
            "session_dict (signing.dumps({}) with only the modern argument "
            "changed) would emit a well-formed modern signed frame that the "
            "modern reader (signing.loads inside decode) reads back to {} for "
            "every input — corrupting every default-regime session and failing "
            "the P2P round-trip suite (test_decode/test_save/test_cycle/"
            "test_store). Correct ONLY on the empty record, so a true "
            "PARTIAL-DOMAIN break on the modern arm. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q5: modern_serialize(empty) carries the empty payload "
            "with modern_digest(empty), so modern_read returns empty, which != "
            "ToSeq(payload) for a non-empty record. Q4 alone would NOT reject it "
            "(the tag IS modern) — Q5 is the clause that pins the carried record. "
            "If it verifies => SPEC-TOO-WEAK (the modern round trip would not be "
            "enforced)."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE — soundness of the two @ContractOnly consumed axioms against the REAL
# Django callees (run in-container, gold applied). Containment is trivial (neither
# axiom has a Requires domain restriction), so we only run soundness probes that
# reproduce axiom_check.py's logic. Probes import only Django + stdlib, configure
# Django themselves, and exit 0 iff the obligation holds.
# ---------------------------------------------------------------------------

_PROBE_KEYED_DIGEST = r'''
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        SECRET_KEY="axiom-check-secret-key-django-13279",
        DEFAULT_HASHING_ALGORITHM="sha256",
        SESSION_SERIALIZER="django.contrib.sessions.serializers.JSONSerializer",
        SESSION_COOKIE_AGE=1209600,
        INSTALLED_APPS=[],
        USE_TZ=True,
    )
django.setup()
from django.contrib.sessions.backends.signed_cookies import SessionStore
session = SessionStore()
serializer = session.serializer()
# Caller-reachable inputs to keyed_digest are arbitrary serialized payloads.
samples = [
    b"",
    serializer.dumps({}),
    serializer.dumps({"a test key": "a test value"}),
    serializer.dumps({"k": "v", "n": 12345, "b": True}),
    serializer.dumps({"unicode": "na\xefve • caf\xe9 \U0001f600"}),
    serializer.dumps({"colon": "a:b:c", "amp": "x&y"}),
    serializer.dumps({"long": "z" * 500}),
]
for s in samples:
    h1 = session._hash(s)
    h2 = session._hash(s)
    if h1 != h2:
        print("AXIOM-UNSOUND: keyed_digest not deterministic on %r" % (s,))
        sys.exit(1)
    if ":" in h1:
        print("AXIOM-UNSOUND: keyed_digest digest contains ':': %r" % (h1,))
        sys.exit(1)
print("AXIOM OK keyed_digest: deterministic + ':'-free over %d samples" % len(samples))
sys.exit(0)
'''

_PROBE_MODERN_SERIALIZE = r'''
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        SECRET_KEY="axiom-check-secret-key-django-13279",
        DEFAULT_HASHING_ALGORITHM="sha256",
        SESSION_SERIALIZER="django.contrib.sessions.serializers.JSONSerializer",
        SESSION_COOKIE_AGE=1209600,
        INSTALLED_APPS=[],
        USE_TZ=True,
    )
django.setup()
from django.contrib.sessions.backends.signed_cookies import SessionStore
from django.core import signing
session = SessionStore()
# Caller-reachable inputs to modern_serialize are arbitrary records. The axiom's
# consumed property: the modern frame is NOT a legacy frame, so feeding it to the
# legacy reader (_legacy_decode) never recovers the original (non-empty) record.
records = [
    {},
    {"a test key": "a test value"},
    {"k": "v"},
    {"n": 0},
    {"n": -1},
    {"flag": True, "flag2": False, "none": None},
    {"list": [1, 2, 3], "nested": {"x": "y"}},
    {"unicode": "na\xefve • caf\xe9 \U0001f600"},
    {"colon": "a:b:c", "amp": "x&y"},
    {"long": "z" * 500},
]
for data in records:
    modern = signing.dumps(
        data, salt=session.key_salt, serializer=session.serializer, compress=True)
    # Carried payload + matching signature: the modern reader recovers exactly
    # the record handed to the modern serializer (modern_read(modern_serialize(p))
    # == p).
    loaded = signing.loads(
        modern, salt=session.key_salt, serializer=session.serializer)
    if loaded != data:
        print("AXIOM-UNSOUND: modern round trip broken on %r: signing.loads "
              "gave %r" % (data, loaded))
        sys.exit(1)
    try:
        decoded = session._legacy_decode(modern)
    except Exception:
        continue  # could not be parsed as a legacy frame: not == data. OK.
    if decoded == data and data != {}:
        print("AXIOM-UNSOUND: modern frame for %r read back by the legacy reader "
              "as the original record %r" % (data, decoded))
        sys.exit(1)
print("AXIOM OK modern_serialize: modern frame never round-trips through the "
      "legacy reader to a non-empty record, and always round-trips through the "
      "modern reader to the record (%d records)" % len(records))
sys.exit(0)
'''

_PROBE_F2P_ROUTE = r'''
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        SECRET_KEY="axiom-check-secret-key-django-13279",
        DEFAULT_HASHING_ALGORITHM="sha256",
        SESSION_SERIALIZER="django.contrib.sessions.serializers.JSONSerializer",
        SESSION_COOKIE_AGE=1209600,
        INSTALLED_APPS=[],
        USE_TZ=True,
    )
django.setup()
from django.contrib.sessions.backends.signed_cookies import SessionStore
from django.test import override_settings
import inspect
session = SessionStore()
src = ""
try:
    src = inspect.getsource(session.encode)
except (OSError, TypeError):
    src = ""
if "DEFAULT_HASHING_ALGORITHM" not in src:
    print("F2P route: patched encode branch not present on this tree (skipped)")
    sys.exit(0)
records = [
    {"a test key": "a test value"},
    {},
    {"k": "v", "n": 12345, "b": True},
    {"unicode": "na\xefve • caf\xe9 \U0001f600"},
]
with override_settings(DEFAULT_HASHING_ALGORITHM="sha1"):
    s2 = SessionStore()
    for data in records:
        encoded = s2.encode(data)
        decoded = s2._legacy_decode(encoded)
        if decoded != data:
            print("F2P route broken: with sha1, _legacy_decode(encode(%r)) gave %r"
                  % (data, decoded))
            sys.exit(1)
print("F2P route OK: with sha1, _legacy_decode(encode(d)) == d on %d records"
      % len(records))
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-keyed_digest",
        "axiom": "keyed_digest",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_KEYED_DIGEST,
        "rationale": (
            "keyed_digest <-> SessionBase._hash / salted_hmac().hexdigest(). The "
            "proof consumes that it is a DETERMINISTIC function of its argument "
            "(equal payloads -> equal digests; closes the legacy round trip) and "
            "relies on the digest being ':'-free (the structural Frame split). The "
            "probe runs the REAL _hash on boundary+sentinel serialized payloads and "
            "asserts both. Any violation => AXIOM-UNSOUND. Containment is trivial "
            "(keyed_digest has no Requires domain; every PSeq[int] is in-domain)."
        ),
    },
    {
        "id": "ax-sound-modern_serialize",
        "axiom": "modern_serialize",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_MODERN_SERIALIZE,
        "rationale": (
            "modern_serialize <-> signing.dumps. The proof consumes that its "
            "output is NOT a legacy frame (Result().tag == FMT_MODERN), i.e. the "
            "legacy reader never recovers the record from it, AND that it carries "
            "exactly the given record with its own modern signature so the modern "
            "reader recovers it (Result().payload == p, Result().mac == "
            "modern_digest(p) => modern_read round trip). The probe builds the "
            "REAL modern signed frame, asserts signing.loads recovers the record, "
            "and feeds it to the REAL _legacy_decode for a range of records, "
            "asserting it never returns the original non-empty record. Any "
            "violation => AXIOM-UNSOUND. Containment is trivial "
            "(modern_serialize has no Requires domain restriction)."
        ),
    },
    {
        "id": "ax-f2p-route",
        "axiom": "legacy_read",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_F2P_ROUTE,
        "rationale": (
            "deep-model fidelity / F2P closure: with DEFAULT_HASHING_ALGORITHM="
            "'sha1' the (gold-patched) encode routes through _legacy_encode so the "
            "REAL _legacy_decode(encode(d)) == d — confirming the legacy_read deep "
            "model and the legacy-framing branch equal the real round trip the F2P "
            "asserts. Skips cleanly (exit 0) if the patched branch is absent. Any "
            "mismatch => deep-model unsound."
        ),
    },
]
