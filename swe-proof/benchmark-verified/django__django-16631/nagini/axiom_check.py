#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16631.

Executes the REAL callees the bundle relies on and asserts every observation
meets the model's contract, as encoded in model.py.

  (A-consumed) `token_for_secret(password, secret)` stands for
      `salted_hmac(key_salt, password, secret=secret, algorithm="sha256").hexdigest()`
      keyed exactly as `AbstractBaseUser._get_session_auth_hash` keys it. The
      proof consumes ONLY functional determinism (equal (password, secret) ⇒
      equal token). We additionally check secret-sensitivity (distinct secrets
      give distinct tokens) -- the rotation premise the F2P test exercises --
      and never assert any exact digest value (no over-claim).

  (A-reference) `constant_time_compare(a, b)` == byte equality of the two hex
      digests, i.e. `constant_time_compare(a, b) == (a == b)`, which is how
      model.py models the compare (PSeq equality). Checked on equal and unequal
      digest pairs.

The REAL callees live in `django.utils.crypto`; this script imports them when a
Django environment is present (the G-AX container), and otherwise reconstructs
`salted_hmac`'s exact algorithm from the standard library (`hashlib`/`hmac`) and
`compare_digest` from `secrets`, so the check is self-contained and stdlib-only
importable. Exit 0 iff every obligation holds.
"""
import hashlib
import hmac
import random
import secrets
import sys

KEY_SALT = "django.contrib.auth.models.AbstractBaseUser.get_session_auth_hash"


# --- the REAL callees (Django when available; stdlib reconstruction else) ----

def _force_bytes(s):
    return s.encode("utf-8") if isinstance(s, str) else bytes(s)


def _stdlib_salted_hmac_hexdigest(key_salt, value, secret):
    """Byte-identical reconstruction of
    django.utils.crypto.salted_hmac(..., algorithm='sha256').hexdigest()."""
    ks = _force_bytes(key_salt)
    sec = _force_bytes(secret)
    key = hashlib.sha256(ks + sec).digest()
    return hmac.new(key, msg=_force_bytes(value), digestmod=hashlib.sha256).hexdigest()


def _stdlib_constant_time_compare(a, b):
    return secrets.compare_digest(_force_bytes(a), _force_bytes(b))


try:
    from django.conf import settings as _settings
    if not _settings.configured:
        _settings.configure(SECRET_KEY="axiomcheck-secret")
    from django.utils.crypto import salted_hmac as _dj_salted_hmac
    from django.utils.crypto import constant_time_compare as _dj_cct

    def token_for_secret(password, secret):
        return _dj_salted_hmac(
            KEY_SALT, password, secret=secret, algorithm="sha256"
        ).hexdigest()

    constant_time_compare = _dj_cct
    BACKEND = "django.utils.crypto (real callee)"
except Exception:  # pragma: no cover - exercised only outside the container
    def token_for_secret(password, secret):
        return _stdlib_salted_hmac_hexdigest(KEY_SALT, password, secret)

    constant_time_compare = _stdlib_constant_time_compare
    BACKEND = "stdlib reconstruction of salted_hmac (no Django on path)"


# --- the checks --------------------------------------------------------------

def check_determinism(password, secret):
    """A-consumed: equal (password, secret) ⇒ identical token (purity)."""
    t1 = token_for_secret(password, secret)
    t2 = token_for_secret(password, secret)
    assert t1 == t2, (
        "token_for_secret NOT deterministic for password=%r secret=%r: %r vs %r"
        % (password, secret, t1, t2))
    return t1


def check_secret_sensitivity(password, secret_a, secret_b):
    """Rotation premise: distinct secrets give distinct tokens (so a session
    keyed by the old secret does NOT match the current token, but DOES match the
    previous token). Never asserts an exact value."""
    if secret_a == secret_b:
        return
    ta = token_for_secret(password, secret_a)
    tb = token_for_secret(password, secret_b)
    assert ta != tb, (
        "token collision across distinct secrets %r/%r for password=%r"
        % (secret_a, secret_b, password))


def check_compare_is_equality(a, b):
    """A-reference: constant_time_compare(a, b) == (a == b)."""
    observed = bool(constant_time_compare(a, b))
    expected = (a == b)
    assert observed == expected, (
        "constant_time_compare(%r, %r) = %r but byte equality = %r"
        % (a, b, observed, expected))


def main():
    passwords = [
        "", "testpw", "pbkdf2_sha256$390000$abc$deadbeef==",
        "p@ss w0rd!", "Ω-π-é", "x" * 128, "Joe's Crab Shack",
    ]
    secrets_pool = [
        "newsecret", "oldsecret", "django-insecure-aaa", "django-insecure-bbb",
        "", "k", "k2", "Ω-secret", "x" * 64,
    ]

    # --- A-consumed: determinism + secret-sensitivity (boundary) ----------
    for pw in passwords:
        for sec in secrets_pool:
            check_determinism(pw, sec)
        for i in range(len(secrets_pool)):
            for j in range(i + 1, len(secrets_pool)):
                check_secret_sensitivity(pw, secrets_pool[i], secrets_pool[j])

    # Concrete rotation scenario mirroring the F2P test: the stored hash was
    # keyed by the OLD secret; after rotation the current secret is NEW.
    pw = "testpw"
    old_secret, new_secret = "oldsecret", "newsecret"
    stored = token_for_secret(pw, old_secret)        # the cookie before rotation
    current = token_for_secret(pw, new_secret)        # current token after rotation
    previous = [token_for_secret(pw, old_secret)]     # fallback tokens (old secret)
    assert stored != current, "rotation premise broken: stored == current"
    assert any(constant_time_compare(stored, fb) for fb in previous), (
        "stored token does not match any previous token under rotation")
    # after upgrade the stored token is rewritten to `current`; with the
    # fallback removed it must verify against the current token directly.
    assert constant_time_compare(current, token_for_secret(pw, new_secret))

    # --- A-reference: constant_time_compare == byte equality (boundary) ---
    digests = [token_for_secret(p, s) for p in passwords[:4] for s in secrets_pool[:4]]
    for a in digests:
        check_compare_is_equality(a, a)               # equal
    for i in range(len(digests)):
        for j in range(len(digests)):
            if i != j:
                check_compare_is_equality(digests[i], digests[j])
    # equal-length but differing, and unequal-length hex strings
    check_compare_is_equality("a" * 64, "b" * 64)
    check_compare_is_equality("a" * 64, "a" * 63)
    check_compare_is_equality("", "")

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(16631)
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEF0123456789@!$ ΩπéΣ"
    for _ in range(20000):
        pw = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 20)))
        sa = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 16)))
        sb = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 16)))
        check_determinism(pw, sa)
        check_secret_sensitivity(pw, sa, sb)
        ta = token_for_secret(pw, sa)
        tb = token_for_secret(pw, sb)
        check_compare_is_equality(ta, ta)
        check_compare_is_equality(ta, tb)

    print("G-AX OK [%s]: token_for_secret deterministic + secret-sensitive and "
          "constant_time_compare == byte equality over %d boundary + 20000 fuzz "
          "cases" % (BACKEND, len(passwords) * len(secrets_pool)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
