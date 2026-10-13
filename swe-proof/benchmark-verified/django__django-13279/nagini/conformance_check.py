#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13279 (nagini).

SHADOW: the impl region of model.py, copied VERBATIM below with the contract
calls (Requires / Ensures) stripped -- ``serialize`` (the regime branch) and
``Frame.__init__`` (the three field assignments). The @Pure helpers of the
pure region (``empty_payload`` / ``legacy_read``) copy over on top of a small
immutable-tuple PSeq shim and serve as an internal cross-check of the shadow's
legacy branch. The two @ContractOnly callees are delegated to the REAL repo
functions the model maps them to (mapping.md section 3):

  * ``keyed_digest``     -> ``SessionBase._hash`` (salted keyed hash, hex);
  * ``modern_serialize`` -> ``django.core.signing.dumps`` with the session's
    salt/serializer/compress arguments; the resulting wire string is lowered
    to abstract ``Frame`` fields per mapping.md section 2 (tag = whether the
    legacy reader's acceptance shape matches; payload = the serialized octets
    the modern reader recovers from it; mac = the carried signature field).

ORACLE: the REAL patched repo function the model models per mapping.md
section 1 -- ``SessionBase.encode`` on a signed-cookies session store. The
gate applies patch.diff to /testbed and sets PYTHONPATH=/testbed before this
script runs, so the import resolves to the patched module.

TYPE BRIDGE (mapping.md section 2): a session record (small dict) lowers to
``List[int]`` of its serializer-dumped octets (the unchanged serializer round
trip is an invertible identity layer folded into the carrier); the regime
selector lowers 'sha1' <-> ALGO_LEGACY and 'sha256' (the default / any other
value) <-> ALGO_MODERN; the transportable encoded ``str`` lowers to
``Frame{tag, mac, payload}`` via the base64/split wrapper for legacy frames
and via the modern reader for modern frames. The carried signature of a
modern frame folds the wrapper's timestamp component (mapping.md section 2),
so modern macs are compared through the modern reader's acceptance (the
signature verifies and the carried record round-trips), not as raw octets;
legacy frames are additionally compared WIRE-EXACT (the reconstructed base64
string must equal the oracle's output byte-for-byte).

INPUT PLAN (>= 1e5 Requires-satisfying inputs): boundary records (empty,
single-key, colon-heavy values, unicode, nested containers, long values,
int/bool/None values) plus 50000 fuzz records over mixed key/value shapes,
each crossed with BOTH regime selector values (>= 100060 serialize calls).
Pinned fuzz seed: 13279. Exit 0 iff zero disagreements; on disagreement
prints the input and both outputs and exits 1. Imports only Django + stdlib.
"""
import base64
import json
import random
import sys

SEED = 13279
N_FUZZ = 50000

# Frame format tags / regime selector values (model.py constants).
FMT_LEGACY = 0
FMT_MODERN = 1
ALGO_LEGACY = 0
ALGO_MODERN = 1


# --- PSeq shim: immutable sequence, the operations the model uses ------------

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __repr__(self):
        return "PSeq%r" % (self._t,)


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- Django environment (in-container: /testbed, patched) --------------------

_SESSION = None  # set in main() after settings are configured


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=False,
            SECRET_KEY='conf-check-secret-key-django-13279',
            DEFAULT_HASHING_ALGORITHM='sha256',
            SESSION_SERIALIZER='django.contrib.sessions.serializers.JSONSerializer',
            SESSION_COOKIE_AGE=1209600,
            INSTALLED_APPS=[],
            USE_TZ=True,
        )
    django.setup()


def _make_session():
    from django.contrib.sessions.backends.signed_cookies import SessionStore
    return SessionStore()


# --- @ContractOnly callees: the REAL repo functions (mapping.md section 3) ---

def keyed_digest(payload):
    """Real SessionBase._hash on the payload octets, lifted to code points."""
    digest = _SESSION._hash(bytes(bytearray(payload._t)))
    return PSeq._wrap(ord(c) for c in digest)


def modern_serialize(payload):
    """Real django.core.signing.dumps on the record the payload octets carry,
    with the wire string lowered to abstract Frame fields per mapping.md
    section 2: tag from the legacy reader's acceptance shape (a modern frame
    is not a legacy frame), payload as the serialized octets the modern
    reader (signing.loads) recovers, mac as the carried signature field."""
    from django.core import signing
    record = _SESSION.serializer().loads(bytes(bytearray(payload._t)))
    wire = signing.dumps(record, salt=_SESSION.key_salt,
                         serializer=_SESSION.serializer, compress=True)
    tag, _, _ = alpha(wire)
    # the modern reader must accept the wire and recover the carried record
    carried = signing.loads(wire, salt=_SESSION.key_salt,
                            serializer=_SESSION.serializer)
    carried_octets = PSeq._wrap(_SESSION.serializer().dumps(carried))
    sig = wire.rsplit(':', 1)[-1]
    f = Frame(tag, PSeq._wrap(ord(c) for c in sig), carried_octets)
    f.wire = wire
    return f


# --- pure region of model.py, contracts stripped (internal cross-check) ------

def empty_payload():
    return PSeq(0).take(0)


def legacy_read(tag, mac, payload):
    if tag == FMT_LEGACY and mac == keyed_digest(payload):
        return payload
    return empty_payload()


# --- the impl region of model.py, verbatim, contract calls stripped ----------

class Frame:
    def __init__(self, tag, mac, payload):
        self.tag = tag
        self.mac = mac
        self.payload = payload


def serialize(payload, algorithm):
    if algorithm == ALGO_LEGACY:
        body = ToSeq(payload)
        return Frame(FMT_LEGACY, keyed_digest(body), body)
    return modern_serialize(ToSeq(payload))


# --- abstraction: lower a real encoded string to Frame fields ----------------

def alpha(encoded):
    """(tag, mac, payload) of a real encoded string per mapping.md section 2.
    Legacy acceptance shape: base64-decode, split on the first b':', carried
    digest equals the freshly recomputed keyed digest of the trailing octets.
    Anything else is a modern frame (mac/payload lowered via the modern
    reader by the caller, since they are timestamp-wrapped)."""
    from django.utils.crypto import constant_time_compare
    try:
        raw = base64.b64decode(encoded.encode('ascii'))
        hash_, serialized = raw.split(b':', 1)
        if constant_time_compare(hash_.decode(), _SESSION._hash(serialized)):
            return (FMT_LEGACY,
                    PSeq._wrap(ord(c) for c in hash_.decode()),
                    PSeq._wrap(serialized))
    except Exception:
        pass
    return (FMT_MODERN, None, None)


# --- differential driver ------------------------------------------------------

def check(record, algorithm):
    """Run shadow serialize and the real patched encode on one record under
    one regime; return an error string on disagreement, else None."""
    from django.core import signing
    payload = list(bytearray(_SESSION.serializer().dumps(record)))
    frame = serialize(payload, algorithm)          # shadow
    encoded = _SESSION.encode(record)              # oracle (patched repo)
    o_tag, o_mac, o_payload = alpha(encoded)

    if algorithm == ALGO_LEGACY:
        if frame.tag != FMT_LEGACY:
            return _err(record, algorithm, "shadow tag", frame.tag, FMT_LEGACY)
        if o_tag != FMT_LEGACY:
            return _err(record, algorithm,
                        "oracle frame kind (legacy acceptance shape)",
                        o_tag, FMT_LEGACY)
        if frame.mac != o_mac:
            return _err(record, algorithm, "mac field", frame.mac, o_mac)
        if frame.payload != o_payload:
            return _err(record, algorithm, "payload field",
                        frame.payload, o_payload)
        # wire-exact: the shadow frame re-wraps to the oracle's exact string
        wire = base64.b64encode(
            bytes(bytearray(frame.mac._t)) + b':' +
            bytes(bytearray(frame.payload._t))).decode('ascii')
        if wire != encoded:
            return _err(record, algorithm, "wire string", wire, encoded)
        # postcondition realization: the legacy reader inverts both sides
        if legacy_read(frame.tag, frame.mac, frame.payload) != ToSeq(payload):
            return _err(record, algorithm, "shadow legacy round trip",
                        legacy_read(frame.tag, frame.mac, frame.payload),
                        ToSeq(payload))
        if _SESSION._legacy_decode(encoded) != record:
            return _err(record, algorithm, "real legacy-reader round trip",
                        _SESSION._legacy_decode(encoded), record)
    else:
        if frame.tag != FMT_MODERN:
            return _err(record, algorithm, "shadow tag", frame.tag, FMT_MODERN)
        if o_tag != FMT_MODERN:
            return _err(record, algorithm,
                        "oracle frame kind (must not be a legacy frame)",
                        o_tag, FMT_MODERN)
        # carried payload: the shadow frame carries exactly the input octets
        if frame.payload != ToSeq(payload):
            return _err(record, algorithm, "shadow carried payload",
                        frame.payload, ToSeq(payload))
        # postcondition realization: the modern reader inverts the oracle's
        # wire to the record, and its re-serialized octets match the input
        got = signing.loads(encoded, salt=_SESSION.key_salt,
                            serializer=_SESSION.serializer)
        if got != record:
            return _err(record, algorithm, "real modern-reader round trip",
                        got, record)
        carried = list(bytearray(_SESSION.serializer().dumps(got)))
        if carried != payload:
            return _err(record, algorithm, "oracle carried payload octets",
                        carried, payload)
    return None


def _err(record, algorithm, what, shadow_val, oracle_val):
    return ("DISAGREEMENT on record %r (algorithm=%d) [%s]:\n"
            "  shadow (impl region)       = %r\n"
            "  real (patched repo encode) = %r"
            % (record, algorithm, what, shadow_val, oracle_val))


def boundary_records():
    return [
        {},
        {'a test key': 'a test value'},
        {'k': 'v'},
        {'n': 0},
        {'n': -1},
        {'big': 10 ** 18},
        {'flag': True, 'flag2': False, 'none': None},
        {'list': [1, 2, 3], 'nested': {'x': 'y'}},
        {'deep': {'a': {'b': {'c': [None, {'d': 1}]}}}},
        {'unicode': 'na\xefve • caf\xe9'},
        {'colon': 'a:b:c', 'amp': 'x&y'},
        {':': ':', '::': '::'},
        {'sep': ':' * 50},
        {'b64ish': 'YWJjOmRlZg=='},
        {'ws': ' \t\n\r '},
        {'quote': '"\'', 'backslash': '\\\\'},
        {'empty': ''},
        {'long': 'z' * 500},
        {'many': dict(('k%d' % i, i) for i in range(40))},
        {'zero': '\x00ok'},
    ]


def fuzz_records(rng):
    keychars = 'abcdefghijklmnopqrstuvwxyz_0123456789'
    valchars = keychars + ' :&<>"\'\xe9•.,=+-/'
    out = []
    for _ in range(N_FUZZ):
        n = rng.randint(0, 6)
        d = {}
        for _ in range(n):
            klen = rng.randint(1, 8)
            k = ''.join(rng.choice(keychars) for _ in range(klen))
            kind = rng.randint(0, 3)
            if kind == 0:
                vlen = rng.randint(0, 16)
                v = ''.join(rng.choice(valchars) for _ in range(vlen))
            elif kind == 1:
                v = rng.randint(-10 ** 6, 10 ** 6)
            elif kind == 2:
                v = rng.choice([True, False, None])
            else:
                v = [rng.randint(0, 99) for _ in range(rng.randint(0, 3))]
            d[k] = v
        out.append(d)
    return out


def main():
    global _SESSION
    _configure_django()
    _SESSION = _make_session()
    from django.test import override_settings

    records = boundary_records() + fuzz_records(random.Random(SEED))

    checked = 0
    for algorithm, setting in ((ALGO_LEGACY, 'sha1'), (ALGO_MODERN, 'sha256')):
        with override_settings(DEFAULT_HASHING_ALGORITHM=setting):
            for record in records:
                try:
                    err = check(record, algorithm)
                except Exception as e:
                    err = ("EXCEPTION on record %r (algorithm=%d): %r"
                           % (record, algorithm, e))
                if err:
                    print(err)
                    return 1
                checked += 1

    print("G-CONF OK: shadow impl == real patched encode on %d inputs "
          "(%d records x both regime selectors, %d fuzz, seed %d); legacy "
          "frames wire-exact; both readers invert their own frames; "
          "0 disagreements." % (checked, len(records), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
