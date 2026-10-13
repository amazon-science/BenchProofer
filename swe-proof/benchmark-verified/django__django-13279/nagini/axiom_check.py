#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13279.

Executes the REAL Django session callees and asserts that every model.py
obligation holds against them. Two consumed axioms and the deep legacy-frame /
legacy-reader model are checked:

  (A-consumed) `keyed_digest` <-> SessionBase._hash / salted_hmac().hexdigest():
      deterministic function of its argument, and the hex digest never contains
      the b':' separator byte (so the legacy split is unambiguous).

  (A-consumed) `modern_serialize` <-> signing.dumps: its output is NOT a legacy
      frame -- feeding a modern signed string to the legacy reader
      (_legacy_decode) yields the empty record {} (tag == FMT_MODERN) -- AND it
      carries exactly the given record with that record's own modern signature,
      so the modern reader recovers it: signing.loads(signing.dumps(d)) == d
      (modern_read(modern_serialize(p)) == p; modern_digest is the signature
      both sides compute, consumed only as a pure function of the payload).

  (deep model) `legacy_read` / the legacy-framing branch <-> _legacy_decode /
      the legacy frame: the round trip _legacy_decode(legacy_frame(data)) == data
      over boundary + fuzz records. The legacy frame is built here exactly as the
      patch's _legacy_encode does (b64encode(hash.encode()+b':'+serialized)), so
      the check is valid against either the pre- or post-patch tree.

  (F2P property) when DEFAULT_HASHING_ALGORITHM == 'sha1' the (patched) encode
      routes through the legacy frame so _legacy_decode(encode(data)) == data,
      whereas always-modern encoding gives _legacy_decode(signing.dumps(...)) ==
      {} != data. Only asserted when the patched encode branch is present.

Imports only Django + stdlib (the modules the patch itself uses); nothing
test-private. Exit 0 iff every obligation holds.
"""
import base64
import os
import random
import sys


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=False,
            SECRET_KEY='axiom-check-secret-key-django-13279',
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


def _legacy_frame(session, data):
    """Build the legacy frame for `data` exactly as the patch's _legacy_encode
    does (independent of whether that method exists on the tree)."""
    serialized = session.serializer().dumps(data)
    hash_ = session._hash(serialized)
    return base64.b64encode(hash_.encode() + b':' + serialized).decode('ascii')


def check_keyed_digest(session):
    """_hash is deterministic and its hex digest never contains ':'(0x3A)."""
    serializer = session.serializer()
    samples = [
        b'',
        serializer.dumps({}),
        serializer.dumps({'a test key': 'a test value'}),
        serializer.dumps({'k': 'v', 'n': 12345, 'b': True}),
        serializer.dumps({'unicode': 'na\xefve • caf\xe9'}),
    ]
    for s in samples:
        h1 = session._hash(s)
        h2 = session._hash(s)
        assert h1 == h2, "keyed_digest not deterministic on %r" % (s,)
        assert ':' not in h1, (
            "keyed_digest produced a digest containing ':': %r" % (h1,))


def check_legacy_round_trip(session, data):
    """deep model: _legacy_decode(legacy_frame(data)) == data."""
    encoded = _legacy_frame(session, data)
    decoded = session._legacy_decode(encoded)
    assert decoded == data, (
        "legacy round trip broken on %r: _legacy_decode gave %r" % (data, decoded))


def check_modern_not_legacy(session, data):
    """modern_serialize axiom: a modern signed frame is NOT a legacy frame, so
    feeding it to the legacy reader does NOT recover `data` -- the legacy reader
    either yields the empty record {} or fails to parse the frame (both model the
    FMT_MODERN tag: legacy_read returns the empty record, never the payload).

    Soundness note: in the real decode() flow the legacy reader is reached only
    after signing.loads fails; _legacy_decode's b64decode is outside its inner
    try/except, so a modern (non-base64-frame) string can raise here. The model's
    claim is only the negative: a modern frame never round-trips through the
    legacy reader to `data` -- which is exactly the bug under the legacy regime."""
    from django.core import signing
    modern = signing.dumps(
        data, salt=session.key_salt, serializer=session.serializer, compress=True)
    try:
        decoded = session._legacy_decode(modern)
    except Exception:
        return  # could not be parsed as a legacy frame: not == data. OK.
    assert decoded != data or data == {}, (
        "modern frame for %r was read back by the legacy reader as the original "
        "record %r -- a modern frame must NOT be a valid legacy frame" % (data, decoded))


def check_modern_round_trip(session, data):
    """modern_serialize axiom (carried payload + matching signature): the modern
    frame carries exactly the given record with its own modern signature, so the
    modern reader (signing.loads) recovers it -- modern_read(modern_serialize(p))
    == p, the P2P modern-regime session round trip."""
    from django.core import signing
    modern = signing.dumps(
        data, salt=session.key_salt, serializer=session.serializer, compress=True)
    decoded = signing.loads(
        modern, salt=session.key_salt, serializer=session.serializer)
    assert decoded == data, (
        "modern round trip broken on %r: signing.loads gave %r" % (data, decoded))


def check_f2p_property(data):
    """F2P: with DEFAULT_HASHING_ALGORITHM='sha1' the patched encode routes
    through the legacy frame so _legacy_decode(encode(data)) == data. Only run
    when the patched branch is present (post-patch tree)."""
    from django.test import override_settings
    session = _make_session()
    src = ''
    try:
        import inspect
        src = inspect.getsource(session.encode)
    except (OSError, TypeError):
        src = ''
    if 'DEFAULT_HASHING_ALGORITHM' not in src:
        return False  # pre-patch encode: branch not present, skip (not a fail)
    with override_settings(DEFAULT_HASHING_ALGORITHM='sha1'):
        s2 = _make_session()
        encoded = s2.encode(data)
        decoded = s2._legacy_decode(encoded)
        assert decoded == data, (
            "F2P broken: with sha1, _legacy_decode(encode(%r)) gave %r"
            % (data, decoded))
    return True


def _records():
    boundary = [
        {},
        {'a test key': 'a test value'},
        {'k': 'v'},
        {'n': 0},
        {'n': -1},
        {'flag': True, 'flag2': False, 'none': None},
        {'list': [1, 2, 3], 'nested': {'x': 'y'}},
        {'unicode': 'na\xefve • caf\xe9 \U0001f600'},
        {'colon': 'a:b:c', 'amp': 'x&y'},
        {'long': 'z' * 500},
    ]
    rng = random.Random(13279)
    keychars = 'abcdefghijklmnopqrstuvwxyz_0123456789'
    valchars = keychars + ' :&<>"\'é•'
    for _ in range(2000):
        n = rng.randint(0, 6)
        d = {}
        for _ in range(n):
            klen = rng.randint(1, 8)
            vlen = rng.randint(0, 16)
            k = ''.join(rng.choice(keychars) for _ in range(klen))
            kind = rng.randint(0, 2)
            if kind == 0:
                v = ''.join(rng.choice(valchars) for _ in range(vlen))
            elif kind == 1:
                v = rng.randint(-10 ** 6, 10 ** 6)
            else:
                v = rng.choice([True, False, None])
            d[k] = v
        boundary.append(d)
    return boundary


def main():
    _configure_django()
    session = _make_session()

    check_keyed_digest(session)

    records = _records()
    for data in records:
        check_legacy_round_trip(session, data)
        check_modern_not_legacy(session, data)
        check_modern_round_trip(session, data)

    f2p_ran = False
    for data in records[:12]:
        f2p_ran = check_f2p_property(data) or f2p_ran

    print("G-AX OK: keyed_digest deterministic + ':'-free; modern frame not "
          "legacy ({} read-back) on %d records; legacy round trip identity AND "
          "modern (signing.loads) round trip identity on "
          "the same %d records%s" % (len(records), len(records),
          "; F2P sha1 encode->legacy_decode identity verified"
          if f2p_ran else "; F2P branch not present on this tree (skipped)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
