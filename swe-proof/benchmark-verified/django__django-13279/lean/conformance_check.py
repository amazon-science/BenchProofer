#!/usr/bin/env python3
"""G-CONF for django__django-13279.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_encode` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched
`SessionBase.encode`, over >=1e5 fuzzed inputs. Zero disagreements => exit 0.

The single behavioral edit is the DISPATCH on the configured serialization-format
identifier `settings.DEFAULT_HASHING_ALGORITHM`:
  * 'sha1'  -> the compatibility scheme  (legacyEncode <-> self._legacy_encode)
  * else    -> the standard scheme       (modernEncode  <-> signing.dumps(..., compress=True))

Type bijection (mapping.md): algo<->settings.DEFAULT_HASHING_ALGORITHM (str),
session<->session_dict (dict), result<->return value (str).

The standard scheme (signing.dumps) is non-deterministic: TimestampSigner stamps
the current time. We FREEZE the clock (monkeypatch time.time) so both the shadow
and the real patched encode produce identical bytes for a given input. The shadow
realizes legacyEncode/modernEncode by calling the SAME real repo routines the
patched encode dispatches to, so the test exercises the dispatch logic itself.

stdlib-only; no hypothesis required.
"""
import os
import random
import sys
import time


def main() -> int:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=False,
            SECRET_KEY="conf-check-secret-key-13279",
            USE_TZ=True,
            DEFAULT_HASHING_ALGORITHM="sha256",
            SESSION_SERIALIZER="django.contrib.sessions.serializers.JSONSerializer",
            DATABASES={},
            INSTALLED_APPS=[
                "django.contrib.sessions",
            ],
        )
        django.setup()

    # Freeze the clock so the timestamped modern scheme is deterministic.
    _FROZEN = 1_600_000_000.0
    time.time = lambda: _FROZEN  # noqa: E731

    from django.contrib.sessions.backends.base import SessionBase

    real_encode = SessionBase.__dict__["encode"]
    real_legacy_encode = SessionBase.__dict__["_legacy_encode"]

    def make_session():
        s = SessionBase()
        return s

    def oracle(algo, session_dict):
        """Behavior of the patched repo `encode` for these inputs."""
        settings.DEFAULT_HASHING_ALGORITHM = algo
        return real_encode(make_session(), dict(session_dict))

    def shadow(algo, session_dict):
        """R/I transliteration of implementation_encode (Lean).

        legacyEncode <-> the real _legacy_encode; modernEncode <-> the real
        signing.dumps(..., compress=True) -- exactly the two branches the patched
        encode selects. The shadow re-implements only the DISPATCH (op #1)."""
        sess = make_session()
        if algo == "sha1":
            return real_legacy_encode(sess, dict(session_dict))
        # modern scheme: identical call the patched encode makes in the else-branch
        from django.core import signing
        return signing.dumps(
            dict(session_dict), salt=sess.key_salt, serializer=sess.serializer,
            compress=True,
        )

    ALGO_POOL = [
        "sha1", "sha256", "sha512", "md5", "", "SHA1", "sha-1", "default", "x",
    ]
    KEY_POOL = ["a", "k", "a test key", "user_id", "_auth_user_id", "k2", "z"]
    VAL_POOL = ["v", "a test value", "1", "", "hello world", "42", "x"]

    def rand_session(rng):
        n = rng.randint(0, 4)
        d = {}
        for _ in range(n):
            d[rng.choice(KEY_POOL)] = rng.choice(VAL_POOL)
        return d

    rng = random.Random(13279)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for i in range(N):
        # Bias toward the 'sha1' discriminator and its near-misses.
        if i % 2 == 0:
            algo = "sha1"
        else:
            algo = rng.choice(ALGO_POOL)
        session_dict = rand_session(rng)
        try:
            o = oracle(algo, session_dict)
        except Exception as e:  # pragma: no cover
            o = ("EXC", type(e).__name__)
        try:
            s = shadow(algo, session_dict)
        except Exception as e:  # pragma: no cover
            s = ("EXC", type(e).__name__)
        if o != s:
            disagreements += 1
            if first is None:
                first = (algo, session_dict, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
