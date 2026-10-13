#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16631 (nagini).

SHADOW: the impl regions of model.py's two modeled functions, copied verbatim
below with the contract calls stripped and PSeq realized as an immutable tuple
shim. The @Pure helper `matches_any` copies over as a plain function
(`tokens_under` is contracts-only vocabulary and is not needed by the impl).
The single @Pure @ContractOnly callee `token_for_secret` (the keyed-hash
primitive) is realized by calling the REAL repo callee —
`django.utils.crypto.salted_hmac(key_salt, password, secret=secret,
algorithm="sha256").hexdigest()` with the session-auth key salt, per
mapping.md section 3.1.

ORACLE: the REAL patched repo functions per mapping.md section 1 —
site A: the session-verification block of `django.contrib.auth.get_user`,
driven through a real request/session (cache-backed session store, stub auth
backend returning the user object); site B:
`AbstractBaseUser.get_session_auth_fallback_hash` on a real user object.
The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed resolves the patched modules.

Type bridge (mapping.md section 2): str tokens/secrets/passwords map to
List[int]/PSeq[int] of code points (ord per char); an absent or empty stored
session value maps to the empty list; the previous-token sequence is a
PSeq of PSeq. Site A's abstract outcome code maps back to the observable
post-state of the real drive: 0 <-> the returned principal is anonymous and
the session was discarded; 1 <-> the user is kept with the session key and
stored hash untouched; 2 <-> the user is kept, the session key is cycled and
the stored hash is rewritten to the current token.

Input domain: both Requires demand only read-only list carriers, i.e. any
token/secret material. Scenarios draw a password, an active secret, 0..3
previous secrets, and a stored value chosen among: the current token, each
previous-secret token, a token under an unrelated secret or password, random
garbage, a truncated token, the empty string, and absent. Boundary cases
cover all three outcomes, the empty fallback list, a fallback equal to the
active secret (current-outcome priority), duplicate fallbacks, and empty password / empty
fallback-secret strings (the ACTIVE secret stays non-empty: the settings
machinery rejects an empty active secret, so that is outside the callee's
operating domain).

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz scenarios,
each exercising BOTH modeled functions against their real counterparts.
Pinned fuzz seed: 16631.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib only (Django is the system under test).
"""
import json
import random
import string
import sys
import types

SEED = 16631
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence, the operations the impl regions use -------

class PSeq:
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

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)

    def __repr__(self):
        return "PSeq%r" % (self._t,)


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- @Pure @ContractOnly callee bridged to the REAL keyed-hash primitive ------

KEY_SALT = "django.contrib.auth.models.AbstractBaseUser.get_session_auth_hash"

_salted_hmac = None  # bound to the real repo callee in main()


def _codes(s):
    return [ord(c) for c in s]


def _str(seq):
    return "".join(chr(seq[i]) for i in range(len(seq)))


def token_for_secret(password, secret):
    digest = _salted_hmac(KEY_SALT, _str(password), secret=_str(secret),
                          algorithm="sha256").hexdigest()
    return PSeq._wrap(_codes(digest))


# --- pure helper from model.py, contracts stripped -----------------------------

def matches_any(token, candidates):
    if len(candidates) == 0:
        return False
    return candidates[0] == token or matches_any(token, candidates.drop(1))


# --- the impl regions of model.py, verbatim, contract calls stripped ----------

def session_outcome(session_token, current_token, previous_tokens):
    if len(session_token) == 0:
        return 0
    if ToSeq(session_token) == ToSeq(current_token):
        return 1
    if matches_any(ToSeq(session_token), previous_tokens):
        return 2
    return 0


def fallback_auth_hashes(password, default_secret, fallback_secrets):
    result = PSeq(PSeq(0)).take(0)
    i = len(fallback_secrets)
    while i > 0:
        s = fallback_secrets[i - 1]
        result = PSeq(token_for_secret(ToSeq(password), s)) + result
        i = i - 1
    return result


def main():
    global _salted_hmac
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes",
                            "django.contrib.auth",
                            "django.contrib.sessions"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            CACHES={"default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
            SESSION_ENGINE="django.contrib.sessions.backends.cache",
            SECRET_KEY="placeholder",
            SECRET_KEY_FALLBACKS=[],
            AUTHENTICATION_BACKENDS=["confbackend.Backend"],
        )
    django.setup()

    from django.utils.crypto import salted_hmac
    _salted_hmac = salted_hmac

    from importlib import import_module
    from django.contrib.auth import (get_user, SESSION_KEY,
                                     BACKEND_SESSION_KEY, HASH_SESSION_KEY)
    from django.contrib.auth.models import User, AnonymousUser
    from django.http import HttpRequest

    # Stub backend: returns the in-memory user object without DB access.
    mod = types.ModuleType("confbackend")

    class Backend:
        user = None

        def get_user(self, user_id):
            return Backend.user

    mod.Backend = Backend
    sys.modules["confbackend"] = mod
    engine = import_module(settings.SESSION_ENGINE)

    def drive_real(password, secret, fallbacks, stored):
        """Run the REAL patched get_user; return (outcome, stored_hash_after)
        with the outcome decoded from the observable post-state."""
        settings.SECRET_KEY = secret
        settings.SECRET_KEY_FALLBACKS = list(fallbacks)
        user = User(username="u", password=password)
        Backend.user = user
        store = engine.SessionStore()
        store[SESSION_KEY] = "1"
        store[BACKEND_SESSION_KEY] = "confbackend.Backend"
        if stored is not None:
            store[HASH_SESSION_KEY] = stored
        store.create()
        key0 = store.session_key
        req = HttpRequest()
        req.session = store
        principal = get_user(req)
        if not isinstance(principal, User) or isinstance(principal, AnonymousUser):
            return 0, None
        if store.session_key == key0:
            return 1, store.get(HASH_SESSION_KEY)
        return 2, store.get(HASH_SESSION_KEY)

    checked = [0]

    def check_one(password, secret, fallbacks, stored):
        settings.SECRET_KEY = secret
        settings.SECRET_KEY_FALLBACKS = list(fallbacks)
        user = User(username="u", password=password)

        # --- site B: previous-token sequence ---------------------------------
        real_prev = list(user.get_session_auth_fallback_hash())
        shadow_prev = fallback_auth_hashes(
            _codes(password), _codes(secret),
            PSeq._wrap(PSeq._wrap(_codes(s)) for s in fallbacks))
        real_prev_seq = PSeq._wrap(PSeq._wrap(_codes(t)) for t in real_prev)
        if shadow_prev != real_prev_seq:
            return ("DISAGREEMENT (previous-token sequence) password=%r "
                    "secret=%r fallbacks=%r\n  shadow=%r\n  real=%r"
                    % (password, secret, fallbacks, shadow_prev, real_prev))

        # --- site A: the session-verification decision -----------------------
        current = user.get_session_auth_hash()
        stored_codes = _codes(stored) if stored else []
        shadow_out = session_outcome(stored_codes, _codes(current),
                                     real_prev_seq)
        real_out, hash_after = drive_real(password, secret, fallbacks, stored)
        if shadow_out != real_out:
            return ("DISAGREEMENT (outcome) password=%r secret=%r "
                    "fallbacks=%r stored=%r\n  shadow outcome=%d\n"
                    "  real outcome=%d" % (password, secret, fallbacks,
                                           stored, shadow_out, real_out))
        if real_out == 1 and hash_after != stored:
            return ("DISAGREEMENT (kept-session hash) stored=%r changed to %r"
                    % (stored, hash_after))
        if real_out == 2 and hash_after != current:
            return ("DISAGREEMENT (rewritten hash) password=%r secret=%r "
                    "fallbacks=%r stored=%r\n  expected the current token %r, "
                    "session holds %r" % (password, secret, fallbacks, stored,
                                          current, hash_after))
        checked[0] += 1
        return None

    def run(*args):
        err = check_one(*args)
        if err:
            print(err)
            sys.exit(1)

    def tok(password, secret):
        return salted_hmac(KEY_SALT, password, secret=secret,
                           algorithm="sha256").hexdigest()

    # --- boundary inputs -------------------------------------------------------
    boundary = [
        ("pw", "s1", ["s0"], tok("pw", "s1")),        # outcome 1
        ("pw", "s1", ["s0"], tok("pw", "s0")),        # outcome 2 (rotation)
        ("pw", "s1", ["s0"], "0" * 64),               # outcome 0 (garbage)
        ("pw", "s1", ["s0"], None),                    # absent -> 0
        ("pw", "s1", ["s0"], ""),                      # empty -> 0
        ("pw", "s1", [], tok("pw", "s1")),             # no fallbacks, 1
        ("pw", "s1", [], tok("pw", "s0")),             # no fallbacks, 0
        ("pw", "s1", ["s1"], tok("pw", "s1")),         # fallback == active: 1
        ("pw", "s1", ["s0", "s0"], tok("pw", "s0")),   # duplicate fallbacks: 2
        ("pw", "s1", ["sA", "sB", "sC"], tok("pw", "sC")),  # last fallback: 2
        ("pw", "s1", ["s0"], tok("pw", "s1")[:32]),    # truncated token: 0
        ("pw", "s1", ["s0"], tok("other", "s1")),      # other password: 0
        ("", "s1", ["s0"], tok("", "s0")),             # empty password: 2
        ("pw", "s1", [""], tok("pw", "")),             # empty fallback secret: 2
    ]
    for args in boundary:
        run(*args)

    # --- fuzz -------------------------------------------------------------------
    rng = random.Random(SEED)
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"

    def rand_s(rng, lo=0, hi=16):
        return "".join(rng.choice(alphabet) for _ in range(rng.randint(lo, hi)))

    for _ in range(N_FUZZ):
        password = rand_s(rng, 1, 12)
        secret = rand_s(rng, 1, 12)
        fallbacks = [rand_s(rng, 0, 12) for _ in range(rng.randint(0, 3))]
        roll = rng.random()
        if roll < 0.30:
            stored = tok(password, secret)                       # current
        elif roll < 0.55 and fallbacks:
            stored = tok(password, rng.choice(fallbacks))        # previous
        elif roll < 0.65:
            stored = tok(password, rand_s(rng, 1, 12))           # unrelated secret
        elif roll < 0.75:
            stored = tok(rand_s(rng, 1, 12), secret)             # other password
        elif roll < 0.85:
            stored = rand_s(rng, 0, 64)                          # garbage
        elif roll < 0.92:
            stored = tok(password, secret)[:rng.randint(0, 63)]  # truncated
        else:
            stored = None                                        # absent
        run(password, secret, fallbacks, stored)

    print("G-CONF OK: shadow impls == real session check + fallback token "
          "sequence on %d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked[0], len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked[0], "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
