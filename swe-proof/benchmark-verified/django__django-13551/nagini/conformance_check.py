#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13551 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped, PSeq realized as an
immutable tuple shim and ToSeq as list->PSeq. The @Pure helper
`effective_address` copies over as a plain function. There are no
@ContractOnly callees in this bundle (the derivation is modelled deeply).

ORACLE: the REAL patched repo function the model models per mapping.md —
`django.contrib.auth.tokens.PasswordResetTokenGenerator._make_hash_value`,
called on a minimal user stand-in whose contact-field-name resolution IS the
real repo classmethod (`AbstractBaseUser.get_email_field_name`). The gate
applies patch.diff to /testbed before this script runs; PYTHONPATH=/testbed
makes the patched modules importable. Django settings are configured
in-process (no database access happens on this code path).

Type bridge (mapping.md section 2): each string component maps to a
List[int] of Unicode code points. The model takes the components
already rendered:
  - pk        -> code points of the pk value rendered as a string,
  - password  -> code points of the stored verifier string,
  - login_repr-> code points of the truncated last-sign-in rendering
                 ('' when the account never signed in — the rendering the
                 oracle itself derives from `last_login`),
  - timestamp -> code points of the issuing instant rendered as a string,
  - address   -> Optional[List[int]]: None when the contact attribute is
                 absent or None, else the code points of its value
                 ([] for the empty string).
The shadow's List[int] output compares against the oracle's str output
lifted to code points.

Input domain: Requires demands only the structural typing above (lists of
code points, address optional), so any str-rendered component tuple is
Requires-satisfying. Generation covers int/str/uuid pk values, hasher-like
and empty verifier strings, None/naive/aware/microsecond datetimes for the
last sign-in, int and str issuing instants, and the full contact-value
lattice: absent attribute, class without the field-name hook attribute,
None, empty string, ASCII and non-ASCII values, renamed contact field.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz tuples.
Pinned fuzz seed: 13551.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import datetime
import json
import random
import sys
import uuid

SEED = 13551
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence, the operations the impl region uses ------

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


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure helper from model.py, contracts stripped -----------------------------

def effective_address(addr):
    """The contact-address contribution to the fingerprint: the address itself
    when present and non-empty, otherwise the empty sequence."""
    if addr is None:
        return PSeq(0).take(0)
    if len(addr) == 0:
        return PSeq(0).take(0)
    return ToSeq(addr)


# --- minimal Account from model.py ---------------------------------------------

class Account:
    def __init__(self):
        self.pk = []
        self.password = []
        self.login_repr = []
        self.address = None


# --- the impl region of model.py, verbatim, contract calls stripped ------------

def make_hash_value(user, timestamp):
    # Ghost snapshots of the component sequences, so the loop invariants read
    # only locals (each field's fractional permission is held by the frame).
    pk_s = ToSeq(user.pk)
    pw_s = ToSeq(user.password)
    lr_s = ToSeq(user.login_repr)
    ts_s = ToSeq(timestamp)

    result = []  # type: list
    i = 0
    while i < len(user.pk):
        result.append(user.pk[i])
        i = i + 1

    i = 0
    while i < len(user.password):
        result.append(user.password[i])
        i = i + 1

    i = 0
    while i < len(user.login_repr):
        result.append(user.login_repr[i])
        i = i + 1

    i = 0
    while i < len(timestamp):
        result.append(timestamp[i])
        i = i + 1

    addr = user.address
    if addr is not None:
        addr_s = ToSeq(addr)
        j = 0
        while j < len(addr):
            result.append(addr[j])
            j = j + 1
    return result


# --- bridge helpers -------------------------------------------------------------

def _cp(s):
    return [ord(ch) for ch in s]


def _render_login(last_login):
    # The truncated last-sign-in rendering the oracle derives internally;
    # the model takes it as an already-rendered component (mapping.md sec. 2).
    if last_login is None:
        return ""
    return str(last_login.replace(microsecond=0, tzinfo=None))


def check_one(gefn_cm, generator, pk, password, last_login, timestamp,
              email_field, email_value, has_attr, has_field_hook):
    """Build a stand-in user, run oracle and shadow, return an error string on
    disagreement, else None."""
    attrs = {"get_email_field_name": gefn_cm}
    if has_field_hook:
        attrs["EMAIL_FIELD"] = email_field
    U = type("StandInUser", (), attrs)
    user = U()
    user.pk = pk
    user.password = password
    user.last_login = last_login
    if has_attr:
        setattr(user, email_field, email_value)

    real = generator._make_hash_value(user, timestamp)
    real_cp = _cp(real)

    # Shadow inputs per the type bridge.
    acct = Account()
    acct.pk = _cp(str(pk))
    acct.password = _cp(password)
    acct.login_repr = _cp(_render_login(last_login))
    resolved = getattr(user, user.get_email_field_name(), None)
    acct.address = None if resolved is None else _cp(resolved)
    ts_l = _cp(str(timestamp))

    shadow = make_hash_value(acct, ts_l)
    if shadow != real_cp:
        return ("DISAGREEMENT\n  pk=%r password=%r last_login=%r timestamp=%r "
                "field=%r value=%r has_attr=%r has_field_hook=%r\n"
                "  shadow=%r\n  real  =%r (str %r)"
                % (pk, password, last_login, timestamp, email_field,
                   email_value, has_attr, has_field_hook, shadow, real_cp,
                   real))
    return None


def boundary_cases():
    dt = datetime.datetime
    tz = datetime.timezone
    naive = dt(2001, 1, 1, 12, 34, 56)
    micro = dt(2020, 6, 15, 8, 9, 10, 987654)
    aware = dt(2019, 3, 2, 1, 0, 0, 5, tzinfo=tz.utc)
    offset = dt(2019, 3, 2, 1, 0, 0, tzinfo=tz(datetime.timedelta(hours=5)))
    return [
        # (pk, password, last_login, timestamp, field, value, has_attr, hook)
        (1, "pw", None, 123, "email", "a@b.com", True, True),
        (1, "pw", None, 123, "email", None, True, True),        # None value
        (1, "pw", None, 123, "email", "", True, True),          # empty value
        (1, "pw", None, 123, "email", None, False, True),       # absent attr
        (1, "pw", None, 123, "email", "a@b.com", True, False),  # no hook attr
        (42, "argon2$x", naive, "ckl3-abc", "email_address",
         "test4@example.com", True, True),                      # renamed field
        (42, "argon2$x", naive, "ckl3-abc", "email_address",
         None, True, True),
        (uuid.UUID("12345678-1234-5678-1234-567812345678"), "", None, 0,
         "email", "x", True, True),                             # uuid pk
        ("", "", None, "", "email", "", True, True),            # all empty
        ("kéy", "pé", micro, 7, "email",
         "üni@☃.io", True, True),                     # non-ASCII
        (5, "pbkdf2$sha256$x", aware, 2**31, "email",
         "a@b.com", True, True),                                # aware dt
        (5, "pbkdf2$sha256$x", offset, -1, "email",
         "a@b.com", True, True),                                # offset dt
        (0, "pw", micro, 999999, "contact", "c@d.org", True, True),
    ]


def rand_case(rng):
    alphabet = "abc012@. <>&'\"é•-_{}"

    def rs(maxn):
        n = rng.randint(0, maxn)
        return "".join(rng.choice(alphabet) for _ in range(n))

    kind = rng.randint(0, 3)
    if kind == 0:
        pk = rng.randint(0, 10**9)
    elif kind == 1:
        pk = rs(8)
    elif kind == 2:
        pk = uuid.UUID(int=rng.getrandbits(128))
    else:
        pk = -rng.randint(1, 1000)
    password = rs(14)
    lk = rng.randint(0, 3)
    if lk == 0:
        last_login = None
    else:
        base = datetime.datetime(2000 + rng.randint(0, 30),
                                 rng.randint(1, 12), rng.randint(1, 28),
                                 rng.randint(0, 23), rng.randint(0, 59),
                                 rng.randint(0, 59), rng.randint(0, 999999))
        if lk == 2:
            base = base.replace(tzinfo=datetime.timezone.utc)
        elif lk == 3:
            base = base.replace(tzinfo=datetime.timezone(
                datetime.timedelta(minutes=rng.randint(-720, 720))))
        last_login = base
    timestamp = rng.randint(0, 2**33) if rng.random() < 0.7 else rs(7)
    field = rng.choice(["email", "email_address", "contact", "mail"])
    has_field_hook = rng.random() < 0.9
    if not has_field_hook:
        field = "email"  # the fallback resolution reads this attribute
    vk = rng.randint(0, 4)
    if vk == 0:
        value, has_attr = None, True
    elif vk == 1:
        value, has_attr = "", True
    elif vk == 2:
        value, has_attr = None, False
    else:
        value, has_attr = rs(12), True
    return (pk, password, last_login, timestamp, field, value, has_attr,
            has_field_hook)


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            SECRET_KEY="conformance-check-secret-key",
            INSTALLED_APPS=["django.contrib.contenttypes",
                            "django.contrib.auth"],
        )
        django.setup()

    # REAL patched callee (the modeled changed function) + the real
    # contact-field-name resolution classmethod for the stand-in user.
    from django.contrib.auth.base_user import AbstractBaseUser
    from django.contrib.auth.tokens import PasswordResetTokenGenerator

    gefn_cm = classmethod(AbstractBaseUser.get_email_field_name.__func__)
    generator = PasswordResetTokenGenerator()

    checked = 0
    for case in boundary_cases():
        err = check_one(gefn_cm, generator, *case)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check_one(gefn_cm, generator, *rand_case(rng))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real fingerprint derivation on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary_cases()), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
