#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13279.

IMPORTANT — this runs at base_commit WITHOUT the patch applied. Therefore it may
only touch callees that exist at base. The patch-introduced method
`_legacy_encode` is NOT axiomatized and NOT called here: it is the operation
under spec, modeled DEEPLY in Solution.lean as the composition
`legacyEncoding d = wrap (hashOf (serialize d)) (serialize d)`. G-AX validates
the *building blocks* of that composition and the *unchanged* readers, all of
which exist at base:

  (A-reference / unchanged building blocks)
      serialize d         := self.serializer().dumps(d)          # serializer
      hashOf serialized   := self._hash(serialized)              # _hash (base)
      wrap hash serial    := b64encode(hash.encode()+b':'+serial)  # base64 pack
      standardEncoding d  := signing.dumps(d, salt, serializer, compress=True)

  The two soundness obligations the deep model relies on, both checked against
  REAL base-commit callees:

  (1) legacy composition is read back by the UNCHANGED legacy reader:
          self._legacy_decode( wrap(hashOf(serialize d), serialize d) ) == d
      `_legacy_decode` predates the patch (present at base_commit). This is the
      property the public report demands (data written in legacy mode must be
      decodable during the transition), and it is what makes `legacyEncoding`
      the *right* deep model of the patch's `_legacy_encode`: indeed the gold
      `_legacy_encode` IS exactly this composition (mapping.md §3), so checking
      the composition is equivalent to checking the new method, but using only
      base-commit code.

  (2) standard encoding is read back by the UNCHANGED standard loader:
          self.decode( signing.dumps(d, ...) ) == d
      Both `decode` and `signing.dumps`/`loads` are unchanged by the patch.

Neither obligation pins an output to a free-floating oracle: each ties the
modeled composition to the inverse performed by a genuinely unchanged reader
(directive 8). Drives the REAL Django callees in-container over fuzzed JSON
session dictionaries plus boundary cases. stdlib + django only. Exit 0 iff every
obligation holds.
"""
import base64
import os
import random
import sys


def _setup_django(hashing_algorithm):
    """Minimal Django settings sufficient to drive SessionBase, with the chosen
    DEFAULT_HASHING_ALGORITHM."""
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            SECRET_KEY="g-ax-fixed-secret-key-for-django-13279",
            INSTALLED_APPS=["django.contrib.sessions"],
            DATABASES={},
            USE_TZ=False,
            SESSION_SERIALIZER="django.contrib.sessions.serializers.JSONSerializer",
        )
        django.setup()
    settings.DEFAULT_HASHING_ALGORITHM = hashing_algorithm


def _make_session():
    """A concrete SessionBase instance. The signed-cookie backend is a thin
    SessionBase subclass with no DB/file needs."""
    from django.contrib.sessions.backends.signed_cookies import SessionStore
    return SessionStore()


# --- unchanged building blocks (exist at base_commit) -----------------------

def serialize(session, d):
    """serialize := self.serializer().dumps(d)  (bytes)."""
    return session.serializer().dumps(d)


def hash_of(session, serialized):
    """hashOf := self._hash(serialized)  (hex str). `_hash` is present at base."""
    return session._hash(serialized)


def wrap(hash_str, serialized):
    """wrap := base64.b64encode(hash.encode() + b':' + serialized).decode('ascii').
    This is the exact reversible packaging the legacy reader splits back apart."""
    return base64.b64encode(hash_str.encode() + b':' + serialized).decode('ascii')


def legacy_encoding(session, d):
    """The deep model legacyEncoding d = wrap (hashOf (serialize d)) (serialize d),
    built ONLY from base-commit callees (no patch-introduced method)."""
    serialized = serialize(session, d)
    return wrap(hash_of(session, serialized), serialized)


# --- the two soundness checks ------------------------------------------------

def check_legacy_decodable(session, d):
    """(1) self._legacy_decode(legacy_encoding(d)) == d, using the UNCHANGED
    legacy reader on the composition that models the new _legacy_encode."""
    encoded = legacy_encoding(session, d)          # deep model (base callees)
    decoded = session._legacy_decode(encoded)      # UNCHANGED reader (base)
    assert decoded == d, (
        "legacy deep model unsound on %r: _legacy_decode(legacyEncoding(d)) "
        "gave %r" % (d, decoded))


def check_standard_roundtrip(session, d):
    """(2) self.decode(signing.dumps(d, ...)) == d, the UNCHANGED standard path."""
    from django.core import signing
    encoded = signing.dumps(                       # standardEncoding (unchanged)
        d, salt=session.key_salt, serializer=session.serializer, compress=True,
    )
    decoded = session.decode(encoded)              # UNCHANGED loader (base)
    assert decoded == d, (
        "standard roundtrip unsound on %r: decode(signing.dumps(d)) gave %r"
        % (d, decoded))


def fuzz_session_dicts(n, rng):
    """JSON-serializable session payloads (the only values these backends carry,
    since SESSION_SERIALIZER is the JSON serializer)."""
    yield {}
    yield {"a test key": "a test value"}
    yield {"_auth_user_id": "1"}
    yield {"k": ""}
    yield {"unicode": "héllo • wörld", "n": 0}
    yield {"nested": {"x": [1, 2, 3], "y": True}, "z": None}
    yield {str(i): i for i in range(20)}
    keys = ["a", "b", "c", "key", "_auth_user_id", "csrftoken", "msg", "é"]
    vals = ["", "v", "a test value", "1", "héllo", "•", "x" * 50]
    for _ in range(n):
        m = rng.randint(0, 6)
        d = {}
        for _ in range(m):
            k = rng.choice(keys)
            t = rng.randint(0, 4)
            if t == 0:
                v = rng.choice(vals)
            elif t == 1:
                v = rng.randint(-(10 ** 6), 10 ** 6)
            elif t == 2:
                v = rng.choice([True, False, None])
            elif t == 3:
                v = [rng.randint(0, 9) for _ in range(rng.randint(0, 5))]
            else:
                v = {rng.choice(keys): rng.choice(vals)}
            d[k] = v
        yield d


def main():
    n_fuzz = int(os.environ.get("AX_FUZZ", "5000"))

    # The legacy composition + legacy reader: validated under 'sha1' (the legacy
    # mode the patch routes through _legacy_encode) — _hash/serializer/_legacy_decode
    # are all present and unchanged at base_commit.
    _setup_django("sha1")
    session = _make_session()
    legacy_corpus = list(fuzz_session_dicts(n_fuzz, random.Random(13279)))
    for d in legacy_corpus:
        check_legacy_decodable(session, d)

    # The standard path: signing.dumps read back by decode, both unchanged.
    from django.conf import settings
    settings.DEFAULT_HASHING_ALGORITHM = "sha256"
    std_corpus = list(fuzz_session_dicts(n_fuzz, random.Random(972))) + legacy_corpus
    for d in std_corpus:
        check_standard_roundtrip(session, d)

    print("G-AX OK: legacy deep model decodable by unchanged _legacy_decode on "
          "%d payloads; standard roundtrip sound on %d payloads."
          % (len(legacy_corpus), len(std_corpus)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
