#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13551.

This bundle consumes NO `@ContractOnly` axiom: the changed operation (the
fingerprint derivation that now incorporates the contact-email address) is
modelled DEEPLY as a sequence concatenation in model.py
(`effective_address` + the trailing-concatenation postcondition). G-AX
therefore validates that deep model == the REAL derivation the gold patch
performs (an A-reference), on boundary + randomized fuzz inputs.

The real derivation (gold `_make_hash_value`, django/contrib/auth/tokens.py):

    login_timestamp = '' if user.last_login is None else \
        user.last_login.replace(microsecond=0, tzinfo=None)
    email_field = user.get_email_field_name()
    email = getattr(user, email_field, '') or ''
    return f'{user.pk}{user.password}{login_timestamp}{timestamp}{email}'

i.e. the in-order concatenation pk ++ password ++ login_timestamp ++ timestamp
++ email, where `email` is the contact attribute coerced to '' when absent,
None, or empty (the `getattr(..., '') or ''` chain). The two model-side facts
under check, expressed at the code-point level:

  (1) effective_address(addr): the email contributes the empty sequence when
      the contact attribute is absent/None/empty, otherwise its own sequence.
      This is exactly `getattr(user, email_field, '') or ''` rendered as a
      string then to code points.

  (2) derived_value: the whole fingerprint equals the in-order concatenation of
      the five string components rendered to code points.

Imports nothing repo-specific (the real construction is plain Python string
formatting + getattr + `get_email_field_name`'s `EMAIL_FIELD`-or-'email'
fallback, all reproduced faithfully with the standard library). Exit 0 iff
every observation matches the model.
"""
import random
import sys


# --- faithful re-creation of the REAL unchanged callee + changed derivation ---

class _Account:
    """Minimal stand-in exposing exactly the attributes the gold derivation
    reads.  `EMAIL_FIELD` mirrors AbstractBaseUser subclasses that rename the
    contact field (e.g. CustomEmailField -> 'email_address'); when unset, the
    real `get_email_field_name()` falls back to 'email'."""

    EMAIL_FIELD = 'email'

    def __init__(self, pk, password, login_repr, email_field='email',
                 email_value=None, has_attr=True):
        self.pk = pk
        self.password = password
        self._login_repr = login_repr
        self.EMAIL_FIELD = email_field
        # The contact attribute lives under the configured field name; it may
        # be absent (has_attr=False -> getattr falls back to '').
        if has_attr:
            setattr(self, email_field, email_value)

    # mirrors AbstractBaseUser.get_email_field_name (base_user.py:143)
    def get_email_field_name(self):
        try:
            return self.EMAIL_FIELD
        except AttributeError:
            return 'email'


def real_make_hash_value(user, login_timestamp, timestamp):
    """Byte-for-byte the gold `_make_hash_value` body (sans the microsecond
    truncation, which is unrelated to the modelled change and supplied here as
    a pre-rendered `login_timestamp` string)."""
    email_field = user.get_email_field_name()
    email = getattr(user, email_field, '') or ''
    return f'{user.pk}{user.password}{login_timestamp}{timestamp}{email}'


# --- model.py deep-model references (kept in lock-step with model.py) ----------

def effective_address(addr):
    """model.py `effective_address`: '' when absent/None/empty, else the
    address, rendered as code points."""
    if addr is None:
        return []
    if len(addr) == 0:
        return []
    return [ord(ch) for ch in addr]


def derived_value(pk, password, login_repr, timestamp, addr):
    """model.py `derived_value`: in-order concatenation of the five components
    as code points, the resolved email last."""
    out = []
    for part in (pk, password, login_repr, timestamp):
        out.extend(ord(ch) for ch in part)
    out.extend(effective_address(addr))
    return out


def _cp(s):
    return [ord(ch) for ch in s]


# --- the checks ---------------------------------------------------------------

def check_one(pk, password, login_repr, timestamp, email_field,
              email_value, has_attr):
    """Assert deep model == real derivation, at the code-point level, AND that
    the email's presence/absence is reflected exactly (no double-mask)."""
    user = _Account(pk, password, login_repr, email_field=email_field,
                    email_value=email_value, has_attr=has_attr)
    real = _cp(real_make_hash_value(user, login_repr, timestamp))

    # The resolved email string the real code uses, independently recomputed.
    resolved = getattr(user, user.get_email_field_name(), '') or ''
    model = derived_value(pk, password, login_repr, timestamp, resolved)
    assert model == real, (
        "deep model != real derivation:\n  inputs pk=%r pw=%r login=%r ts=%r "
        "field=%r value=%r has_attr=%r\n  model=%r\n  real =%r"
        % (pk, password, login_repr, timestamp, email_field, email_value,
           has_attr, model, real))

    # (Index-level, no double-mask) the trailing segment after the four fixed
    # components is exactly the resolved-email contribution -- asserted on the
    # REAL output, not via a predicate the model itself decides.
    prefix_len = len(pk) + len(password) + len(login_repr) + len(timestamp)
    assert real[prefix_len:] == effective_address(resolved), (
        "email contribution mismatch on real output: tail=%r expected=%r"
        % (real[prefix_len:], effective_address(resolved)))

    # Discriminator that the F2P test demands: changing ONLY the email changes
    # the real fingerprint whenever the resolved email actually differs.
    other_value = (email_value or '') + 'X'
    user2 = _Account(pk, password, login_repr, email_field=email_field,
                     email_value=other_value, has_attr=True)
    real2 = _cp(real_make_hash_value(user2, login_repr, timestamp))
    resolved2 = getattr(user2, user2.get_email_field_name(), '') or ''
    if resolved2 != resolved:
        assert real2 != real, (
            "fingerprint failed to change when only the email changed: "
            "%r -> %r" % (resolved, resolved2))


def main():
    # --- boundary cases -------------------------------------------------------
    boundary = [
        # (pk, password, login_repr, timestamp, field, value, has_attr)
        ("1", "pw", "", "abc", "email", "a@b.com", True),
        ("1", "pw", "", "abc", "email", None, True),       # None -> ''
        ("1", "pw", "", "abc", "email", "", True),         # '' -> ''
        ("1", "pw", "", "abc", "email", None, False),      # missing attr -> ''
        ("42", "argon2$x", "2001-01-01 00:00:00", "ckl3", "email_address",
         "test4@example.com", True),                       # renamed field
        ("42", "argon2$x", "2001-01-01 00:00:00", "ckl3", "email_address",
         None, True),                                      # renamed, None
        ("uuid-abc", "", "", "", "email", "x", True),      # empty components
        ("", "", "", "", "email", "", True),               # all empty
        ("é•", "pé", "l", "t", "email", "üni@☃.io",
         True),                                            # non-ASCII
        ("1", "pw", "L", "T", "email", "a@b.com", True),
    ]
    for row in boundary:
        check_one(*row)

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(13551)
    alphabet = "abc012@. <>&'\"é•-_"
    fields = ["email", "email_address", "contact"]
    for _ in range(20000):
        def rs(maxn):
            n = rng.randint(0, maxn)
            return "".join(rng.choice(alphabet) for _ in range(n))
        pk = rs(6)
        password = rs(10)
        login_repr = rng.choice(["", rs(19)])
        timestamp = rs(6)
        field = rng.choice(fields)
        # value: a string, the empty string, or None; attribute may be absent
        kind = rng.randint(0, 3)
        if kind == 0:
            value, has_attr = None, True
        elif kind == 1:
            value, has_attr = "", True
        elif kind == 2:
            value, has_attr = None, False
        else:
            value, has_attr = rs(12), True
        check_one(pk, password, login_repr, timestamp, field, value, has_attr)

    print("G-AX OK: deep model (effective_address + derived_value) == real "
          "_make_hash_value derivation on %d boundary + 20000 fuzz inputs; "
          "email-change discriminator holds" % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
