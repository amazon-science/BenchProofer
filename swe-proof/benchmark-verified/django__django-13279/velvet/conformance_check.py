#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13279 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo types. The impl is a single flag
              dispatch (the CHANGED operation, an R/I leg):

                  encode(d, legacy_mode) =
                      legacyEncoding(d)            if legacy_mode
                      else standardEncoding(d)

              `legacyEncoding(d)` is the deep model spelled out in Solution.lean
              — wrap(hashOf(serialize d), serialize d) — transliterated here as
              the exact composition of base callees (serializer / _hash / base64
              packaging). `standardEncoding` is the A-tagged unchanged callee
              `signing.dumps(...)`, left as the REAL repo callee (G-AX owns its
              roundtrip). `legacy_mode` is the mapping.md bijection of
              `DEFAULT_HASHING_ALGORITHM == 'sha1'`.

  * ORACLE  — patch.diff's behaviour: the patched `SessionBase.encode` applied at
              base_commit (the real correctness oracle, G-RESOLVE), evaluated
              under each DEFAULT_HASHING_ALGORITHM setting.

They must agree on every input. Both the standard signed form and the chosen
signer algorithm depend on DEFAULT_HASHING_ALGORITHM, so it is set on the global
settings BEFORE computing each of shadow and oracle; the standard form embeds a
timestamp, so `time.time` is frozen to a fixed instant for a byte-exact
comparison; the legacy form carries no timestamp. Exit 0 iff zero disagreements
over the fuzz corpus.

Runs in-container (prebuilt SWE-Bench instance image, patch.diff applied),
stdlib + django only. The fuzz seed is pinned (mapping.md §4).
"""
import base64
import os
import random
import sys
import time

SEED = 13279
N_FUZZ = int(os.environ.get("CONF_FUZZ", "100000"))
_FROZEN = 1_600_000_000.0  # fixed instant so the timestamped standard form is stable


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            SECRET_KEY="g-conf-fixed-secret-key-for-django-13279",
            INSTALLED_APPS=["django.contrib.sessions"],
            DATABASES={},
            USE_TZ=False,
            SESSION_SERIALIZER="django.contrib.sessions.serializers.JSONSerializer",
        )
        django.setup()


def _freeze_time():
    time.time = lambda: _FROZEN  # noqa: E731 — deterministic timestamp signer


def _set_alg(alg):
    from django.conf import settings
    settings.DEFAULT_HASHING_ALGORITHM = alg


def shadow_encode(session, d, legacy_mode):
    """The R/I flag dispatch of Solution.lean's impl, transliterated.

    Legacy branch: the deep model legacyEncoding = wrap(hashOf(serialize d),
    serialize d), built from base callees. Standard branch: the A-tagged
    unchanged callee signing.dumps (left as the real repo callee). The caller has
    already set DEFAULT_HASHING_ALGORITHM, on which the standard signer depends."""
    if legacy_mode:
        serialized = session.serializer().dumps(d)          # serialize
        hash_str = session._hash(serialized)                # hashOf (unchanged _hash)
        return base64.b64encode(                            # wrap
            hash_str.encode() + b':' + serialized).decode('ascii')
    from django.core import signing
    return signing.dumps(                                   # standardEncoding (real callee)
        d, salt=session.key_salt, serializer=session.serializer, compress=True,
    )


def oracle_encode(session, d):
    """patch.diff's behaviour: the patched SessionBase.encode under the
    currently-set DEFAULT_HASHING_ALGORITHM."""
    return session.encode(d)                                # patched dispatch


def fuzz_session_dicts(n, rng):
    yield {}
    yield {"a test key": "a test value"}
    yield {"_auth_user_id": "1"}
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
    _setup_django()
    _freeze_time()
    from django.contrib.sessions.backends.signed_cookies import SessionStore
    session = SessionStore()

    rng = random.Random(SEED)
    disagreements = []
    count = 0
    # mapping.md bijection: DEFAULT_HASHING_ALGORITHM=='sha1' <-> legacy_mode=True
    modes = [("sha1", True), ("sha256", False)]
    for d in fuzz_session_dicts(N_FUZZ, rng):
        for alg, legacy_mode in modes:
            count += 1
            # Set the algorithm BEFORE both legs: the standard signer's HMAC
            # algorithm (and thus its signature) depends on it.
            _set_alg(alg)
            shadow = shadow_encode(session, d, legacy_mode)
            _set_alg(alg)
            oracle = oracle_encode(session, d)
            if shadow != oracle:
                disagreements.append((d, alg, shadow, oracle))
                if len(disagreements) >= 5:
                    break
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for d, alg, sh, orc in disagreements:
            print("  input=%r alg=%r shadow=%r oracle=%r" % (d, alg, sh, orc))
        return 1
    print("G-CONF OK: R/I dispatch shadow of encodeSession agrees with "
          "patch.diff behaviour on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
