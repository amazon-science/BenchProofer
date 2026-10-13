#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13551 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`makeHashInput`,
              routed through the deep model `hashInput`/`emailValue`)
              transliterated to Python over the real repo types (`str`,
              `Option str`), via the mapping.md §2 bijection. There are NO
              A-tagged callees in the impl region (no axioms), so the shadow is
              pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched
              `PasswordResetTokenGenerator._make_hash_value` applied at
              base_commit (the harness applies the gold patch before this runs).
              The function reads only `user.pk`, `user.password`,
              `user.last_login`, `user.get_email_field_name()` and the email
              attribute, so a duck-typed user object drives the actual patched
              code path (no DB / app registry needed).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import string
import sys
from datetime import datetime

SEED = 13551
N_FUZZ = 100_000

# Minimal settings so importing django.contrib.auth.tokens is safe: the module
# constructs `default_token_generator = PasswordResetTokenGenerator()` at import
# time, whose __init__ reads SECRET_KEY and DEFAULT_HASHING_ALGORITHM. No DB or
# app registry is touched by _make_hash_value, so django.setup() is avoided.
from django.conf import settings
if not settings.configured:
    settings.configure(
        SECRET_KEY="conf-check-secret-key",
        DEFAULT_HASHING_ALGORITHM="sha256",
    )

from django.contrib.auth.tokens import PasswordResetTokenGenerator

_GEN = PasswordResetTokenGenerator()


class DuckUser:
    """A minimal stand-in for the `user` argument carrying exactly the fields
    `_make_hash_value` reads. Models the mapping.md §1 user slice."""

    def __init__(self, pk, password, last_login, email_field, email_attr):
        self.pk = pk
        self.password = password
        self.last_login = last_login
        self._email_field = email_field
        # set the email under its model-specific attribute name; omit entirely
        # when email_attr is the sentinel _MISSING to exercise getattr's default.
        if email_attr is not _MISSING:
            setattr(self, email_field, email_attr)

    def get_email_field_name(self):
        return self._email_field


_MISSING = object()


# --- the R/I shadow: Solution.lean hashInput / emailValue, transliterated -----

def shadow(pk, password, login_str, timestamp, email_model):
    """The full R/I shadow: pk ++ password ++ loginTimestamp ++ timestamp ++ email."""
    return pk + password + login_str + timestamp + email_model


def oracle(user, timestamp):
    """patch.diff's behaviour: the REAL patched _make_hash_value."""
    return _GEN._make_hash_value(user, timestamp)


# --- fuzzing ------------------------------------------------------------------

def rand_str(rng, n):
    alphabet = string.ascii_letters + string.digits + " @.+-_'<>&"
    return "".join(rng.choice(alphabet) for _ in range(n))


def gen_case(rng):
    """Produce one fuzz case as the primitive field values + the user object."""
    # pk: int (default User) or str (e.g. UUID-style); both stringify via str().
    if rng.random() < 0.5:
        pk = rng.randint(0, 10 ** 9)
    else:
        pk = rand_str(rng, rng.randint(1, 12))
    password = rand_str(rng, rng.randint(0, 30))
    # last_login: None, or a naive datetime with microseconds (truncation tested)
    if rng.random() < 0.4:
        last_login = None
    else:
        last_login = datetime(
            2000 + rng.randint(0, 40), rng.randint(1, 12), rng.randint(1, 28),
            rng.randint(0, 23), rng.randint(0, 59), rng.randint(0, 59),
            rng.randint(0, 999999))
    # email field name: default User vs custom email-field model
    email_field = rng.choice(["email", "email_address"])
    # email attribute: present-nonempty, empty string, None, or missing entirely
    r = rng.random()
    if r < 0.55:
        email_attr = rand_str(rng, rng.randint(1, 24))
    elif r < 0.7:
        email_attr = ''
    elif r < 0.85:
        email_attr = None
    else:
        email_attr = _MISSING
    return pk, password, last_login, email_field, email_attr


def fixed_cases():
    """Boundary cases from the F2P scenario (plan §4.1 step 4): the default User
    with and without an email, and a custom email-field model with None."""
    yield (1, "pbkdf2$hash", None, "email", "test4@example.com")
    yield (1, "pbkdf2$hash", None, "email", "")
    yield (1, "pbkdf2$hash", None, "email", None)
    yield (1, "pbkdf2$hash", None, "email_address", None)
    yield (1, "pbkdf2$hash", None, "email_address", "test4@example.com")
    yield (1, "pbkdf2$hash", None, "email_address", _MISSING)
    yield (42, "pw", datetime(2020, 1, 1, 12, 0, 0, 123456), "email",
           "user@example.com")


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    def check(pk, password, last_login, email_field, email_attr, timestamp):
        nonlocal count
        count += 1
        user = DuckUser(pk, password, last_login, email_field, email_attr)
        orc = oracle(user, timestamp)
        # build the shadow from the mapping.md §2 bijection images
        pk_str = str(pk)
        login_str = '' if last_login is None else str(
            last_login.replace(microsecond=0, tzinfo=None))
        email_model = email_attr if (email_attr not in (None, _MISSING, '')) else ''
        sh = shadow(pk_str, password, login_str, str(timestamp), email_model)
        if sh != orc:
            disagreements.append((pk, password, last_login, email_field,
                                  email_attr, timestamp, sh, orc))

    for case in fixed_cases():
        check(*case, timestamp=123456789)

    for _ in range(N_FUZZ):
        pk, password, last_login, email_field, email_attr = gen_case(rng)
        timestamp = rng.randint(0, 10 ** 9)
        check(pk, password, last_login, email_field, email_attr, timestamp)
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for d in disagreements:
            print("  pk=%r password=%r last_login=%r email_field=%r "
                  "email_attr=%r ts=%r shadow=%r oracle=%r" % d)
        return 1
    print("G-CONF OK: R/I shadow of makeHashInput agrees with patch.diff "
          "behaviour (real _make_hash_value) on %d inputs (seed=%d), 0 "
          "disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
