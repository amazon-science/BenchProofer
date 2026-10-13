#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11451 (nagini).

SHADOW: the impl region of model.py's ``authenticate``, copied verbatim below
with the contract calls (Requires/Ensures) stripped, plus the ``Checker``
carrier of the two cost counters. The two @ContractOnly callees
(``directory_recognises``, ``secret_verifies``) call the REAL repo functions
they model per mapping.md section 3: the directory-lookup decision is the real
``UserModel._default_manager.get_by_natural_key`` raising / not raising
``DoesNotExist``, and the verification-and-permission decision is the real
``user.check_password(...) and backend.user_can_authenticate(user)``.

ORACLE: the REAL patched ``ModelBackend.authenticate`` (the gate applies the
gold patch to /testbed before this script runs), driven against a live
in-memory auth database. Per mapping.md section 2 the model's observables
bridge as:

  * result:              ``Optional[int]`` account code  <->  returned user /
                          ``None`` (a non-None shadow result must name exactly
                          the account the oracle returned);
  * ``lookups``      +1  <->  one database query during the oracle call
                          (counted via the connection's debug-cursor query
                          log, cleared per trial — NOT CaptureQueriesContext,
                          whose index arithmetic silently breaks once the
                          bounded queries_log deque saturates over 1e5 trials);
  * ``verifications`` +1 <->  one password-hasher run during the oracle call
                          (counted by instrumenting the active hasher's
                          ``encode``).

TYPE BRIDGE (mapping.md section 2): identifier / secret / fallback_identifier
are ``Optional[int]`` opaque codes; ``None`` <-> absent, a present identifier
code ``i`` <-> the natural key ``"u<i>"``, a present secret code ``j`` <-> the
password string for ``j`` (one secret code maps to the empty string, which is
present-but-falsy in the repo's ``str`` carrier — a boundary the bridge must
cover). The fixture user model deliberately uses a USERNAME_FIELD distinct
from the ``username`` parameter name, so the keyword side channel that
``fallback_identifier`` models (``kwargs.get(UserModel.USERNAME_FIELD)``) is
genuinely exercised through ``**kwargs``: with the default field name the
keyword would bind to the named parameter and the recovery step would be
unreachable. The fixture app lives in a temp dir (a real importable package,
so the auth app's ready() can resolve the swapped user model during setup).

Directory fixture: codes 0..4 are recognised accounts (code 3 is not permitted
to authenticate, code 4 stores the empty-string secret), codes 5..11 are
unrecognised. Secret codes 0..4 are the stored secrets of accounts 0..4; codes
5..8 match no stored secret; code 9 is the empty string.

INPUT DOMAIN: the precondition only demands the two counters exist and are
non-negative, so every (identifier, secret, fallback_identifier) triple over
``Optional[int]`` is Requires-satisfying. Boundary: the full cross product of
the code pools including None (both-absent / one-absent / recognised-correct /
recognised-wrong / not-permitted / unrecognised / empty-string cells, each
with every fallback choice). Fuzz: 100000 random triples over the same pools.
Pinned seed: 11451.

>= 1e5 Requires-satisfying inputs total. Exit 0 iff zero disagreements; on
disagreement prints the input and both outputs and exits 1. stdlib + Django
(the framework under test, present in the image) only.
"""
import json
import os
import random
import sys
import tempfile

SEED = 11451
N_FUZZ = 100000

_APP_MODELS = '''\
from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager


class CodeUserManager(BaseUserManager):
    def create_account(self, code_name, password):
        u = self.model(code_name=code_name)
        u.set_password(password)
        u.save(using=self._db)
        return u


class CodeUser(AbstractBaseUser):
    code_name = models.CharField(max_length=64, unique=True)
    is_active = models.BooleanField(default=True)
    objects = CodeUserManager()
    USERNAME_FIELD = "code_name"
'''


def _configure_django():
    """Configure a minimal live auth environment whose user model has a
    USERNAME_FIELD different from the ``username`` parameter name (see the
    type-bridge note in the module docstring). Returns the user model."""
    base = tempfile.mkdtemp(prefix="sbu_conf_app_")
    pkg = os.path.join(base, "conf_app")
    os.mkdir(pkg)
    with open(os.path.join(pkg, "__init__.py"), "w") as f:
        f.write("")
    with open(os.path.join(pkg, "models.py"), "w") as f:
        f.write(_APP_MODELS)
    sys.path.insert(0, base)

    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=False,
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
                "conf_app",
            ],
            AUTH_USER_MODEL="conf_app.CodeUser",
            PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
            USE_TZ=True,
        )
    django.setup()

    from conf_app.models import CodeUser
    return CodeUser


# --- the bridge: Optional[int] codes <-> repo strings -------------------------

RECOGNISED_CODES = [0, 1, 2, 3, 4]     # accounts that exist in the directory
UNRECOGNISED_CODES = [5, 6, 7, 8, 9, 10, 11]
NOT_PERMITTED_CODE = 3                 # exists but may not authenticate
EMPTY_SECRET_ACCOUNT = 4               # its stored secret is the empty string
SECRET_CODES = list(range(10))
EMPTY_SECRET_CODE = 9                  # the empty-string secret


def uname(code):
    """Identifier-code -> natural-key string (injective)."""
    return "u%d" % code


def pw(code):
    """Secret-code -> password string (injective)."""
    if code == EMPTY_SECRET_CODE:
        return ""
    return "p%d" % code


def stored_secret_code(account_code):
    """The secret code stored for a recognised account (fixture layout)."""
    if account_code == EMPTY_SECRET_ACCOUNT:
        return EMPTY_SECRET_CODE
    return account_code


# --- shadow: the impl region of model.py, verbatim, contracts stripped --------

class Checker(object):
    def __init__(self):
        self.lookups = 0
        self.verifications = 0


def shadow_authenticate(self, identifier, secret, fallback_identifier,
                        directory_recognises, secret_verifies):
    # impl region of model.py's ``authenticate``; the two @ContractOnly callee
    # decisions are passed in, bound to the REAL repo functions (see main()).
    eff = identifier  # type: ignore
    if eff is None:
        eff = fallback_identifier
    if eff is None or secret is None:
        return None
    self.lookups = self.lookups + 1
    # The verification primitive runs exactly once on every both-present path:
    # on the recognised path it is the secret check; on the unrecognised path
    # it is the timing-defence invocation.
    self.verifications = self.verifications + 1
    if not directory_recognises(eff):
        return None
    else:
        if secret_verifies(eff, secret):
            return eff
        return None


# --- differential driver -------------------------------------------------------

def main():
    CodeUser = _configure_django()

    from django.db import connection
    from django.contrib.auth.backends import ModelBackend
    from django.contrib.auth import hashers

    # Build only the table the checker touches.
    with connection.schema_editor() as editor:
        editor.create_model(CodeUser)

    # Fixture: the directory described by the bridge above.
    for code in RECOGNISED_CODES:
        u = CodeUser.objects.create_account(uname(code),
                                            pw(stored_secret_code(code)))
        if code == NOT_PERMITTED_CODE:
            u.is_active = False
            u.save()

    # Instrument the active hasher so oracle-side verification runs are
    # observable (bridge: one hasher run <-> +1 verifications).
    hasher_calls = {"n": 0}
    _real_encode = hashers.MD5PasswordHasher.encode

    def _counting_encode(hself, *a, **k):
        hasher_calls["n"] += 1
        return _real_encode(hself, *a, **k)

    hashers.MD5PasswordHasher.encode = _counting_encode

    # Per-trial query counting: debug cursor on, clear the bounded log before
    # each oracle call and read its length after.
    connection.force_debug_cursor = True

    backend = ModelBackend()
    UserModel = CodeUser

    # ---- the @ContractOnly callees, bound to the REAL repo functions --------
    def directory_recognises(identifier):
        try:
            UserModel._default_manager.get_by_natural_key(uname(identifier))
        except UserModel.DoesNotExist:
            return False
        return True

    def secret_verifies(identifier, secret):
        user = UserModel._default_manager.get_by_natural_key(uname(identifier))
        return bool(user.check_password(pw(secret))
                    and backend.user_can_authenticate(user))

    # ---- oracle runner -------------------------------------------------------
    def run_oracle(identifier, secret, fallback_identifier):
        """Run the real patched authenticate; return (result_user, nq, nh).
        The fallback identifier travels through **kwargs under the model's
        USERNAME_FIELD — the keyword side channel the model's recovery step
        corresponds to."""
        username = None if identifier is None else uname(identifier)
        password = None if secret is None else pw(secret)
        kwargs = {}
        if fallback_identifier is not None:
            kwargs[UserModel.USERNAME_FIELD] = uname(fallback_identifier)
        hasher_calls["n"] = 0
        connection.queries_log.clear()
        result = backend.authenticate(None, username=username,
                                      password=password, **kwargs)
        return result, len(connection.queries_log), hasher_calls["n"]

    def check(identifier, secret, fallback_identifier):
        """One differential trial; return an error string on disagreement."""
        real_user, nq, nh = run_oracle(identifier, secret, fallback_identifier)
        c = Checker()
        shadow = shadow_authenticate(c, identifier, secret, fallback_identifier,
                                     directory_recognises, secret_verifies)
        inp = ("identifier=%r secret=%r fallback_identifier=%r"
               % (identifier, secret, fallback_identifier))
        # result presence + identity (bridge: account code <-> natural key)
        if (shadow is None) != (real_user is None):
            return ("DISAGREEMENT on %s:\n  shadow result = %r\n"
                    "  real result   = %r" % (inp, shadow, real_user))
        if shadow is not None and real_user.get_username() != uname(shadow):
            return ("DISAGREEMENT on %s:\n  shadow result = %r (natural key %r)\n"
                    "  real result natural key = %r"
                    % (inp, shadow, uname(shadow), real_user.get_username()))
        # lookups counter <-> database queries during the oracle call
        if c.lookups != nq:
            return ("DISAGREEMENT on %s:\n  shadow lookups delta = %d\n"
                    "  real query count     = %d" % (inp, c.lookups, nq))
        # verifications counter <-> hasher runs during the oracle call
        if c.verifications != nh:
            return ("DISAGREEMENT on %s:\n  shadow verifications delta = %d\n"
                    "  real hasher-run count      = %d"
                    % (inp, c.verifications, nh))
        return None

    # ---- boundary: full cross product over the pools incl. absent -----------
    id_pool = [None] + RECOGNISED_CODES + UNRECOGNISED_CODES
    secret_pool = [None] + SECRET_CODES
    checked = 0
    for identifier in id_pool:
        for secret in secret_pool:
            for fallback in id_pool:
                err = check(identifier, secret, fallback)
                if err:
                    print(err)
                    return 1
                checked += 1
    n_boundary = checked

    # ---- fuzz: pinned-seed random triples over the same pools ---------------
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        identifier = rng.choice(id_pool)
        secret = rng.choice(secret_pool)
        fallback = rng.choice(id_pool)
        err = check(identifier, secret, fallback)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched authenticate on %d inputs "
          "(%d boundary cross product + %d fuzz, seed %d); result identity, "
          "query count and hasher-run count all agree; 0 disagreements."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "@ContractOnly callees bound to the real "
                                "repo decisions)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
