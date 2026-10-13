#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-13551.

The bundle models ONE function: `PasswordResetTokenGenerator._make_hash_value`.
Its Lean implementation (`implementation_tokenState`) assembles the password-reset
token state string as the ordered concatenation of five already-stringified
components — the user's primary key, password, last-login timestamp, token
timestamp, and the (normalized) email contribution:

    email = emailRaw if emailRaw is not None else ""   # Lean `emailPart` = getD ""
    result = pk + password + loginTs + ts + email

This script transliterates that R/I impl into Python (`shadow_state`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
post-patch behavior of `_make_hash_value` (`django/contrib/auth/tokens.py`):

    email_field = user.get_email_field_name()
    email = getattr(user, email_field, '') or ''
    return f'{user.pk}{user.password}{login_timestamp}{timestamp}{email}'

We do NOT stand up a Django user model / ORM (heavy, and the modeled value is a
pure string assembly). Instead we feed both sides the SAME observable inputs the
real function consumes (mapping.md): the four pre-stringified components and the
account's email value (`None` when the account carries none). The oracle
reproduces the patched f-string assembly INCLUDING the `... or ''` falsy
normalization; the shadow reaches the same result via Lean's `emailPart`
(`Option.getD ""`). They must agree for every input — in particular when the
email is present (the suffix the patch adds) and when it is absent/empty (the
"user need not have an email" case the patch normalizes).

The downstream HMAC fingerprint is an injective function of this string and is
not part of the modeled function, so the differential is on the state string
itself (equal state strings ⟺ equal tokens).

stdlib-only; pinned seed 13551 (also recorded in mapping.md).
"""
import sys

SEED = 13551
N = 120_000

ALPHABET = ["", "a", "b", "ab", "1", "0", "x@y", "foo@example.com", "@", "12"]


# --- ORACLE: the post-patch behavior, faithful in-process replica ------------
# `email_raw` is the account's email value: None when absent, else a str.
# The patched code: email = getattr(user, field, '') or ''  (falsy -> '');
# return f'{pk}{password}{login_ts}{ts}{email}'.
def oracle_state(pk, password, login_ts, ts, email_raw):
    email = (email_raw or "")  # None or '' -> '', non-empty -> itself
    return f"{pk}{password}{login_ts}{ts}{email}"


# --- shadow of implementation_tokenState (the R/I leg) -----------------------
# Mirrors Solution.lean: email := emailPart emailRaw  (Option.getD "");
# result := pk ++ password ++ loginTs ++ ts ++ email.
def shadow_state(pk, password, login_ts, ts, email_raw):
    email = email_raw if email_raw is not None else ""  # Option.getD ""
    s = pk
    s = s + password
    s = s + login_ts
    s = s + ts
    s = s + email
    return s


def disagree(args):
    got = oracle_state(*args)
    want = shadow_state(*args)
    if got != want:
        return (args, got, want)
    return None


# --- input corpus ------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_edge():
    """Hand-picked cases exercising the email contribution."""
    cases = []
    base = ("1", "pw", "", "100")
    # absent email (None) and empty email -- the 'no email' case the patch
    # normalizes to '' (must NOT change the prefix-only string):
    cases.append(("1", "pw", "", "100", None))
    cases.append(("1", "pw", "", "100", ""))
    # present email -- the suffix the patch adds:
    cases.append(("1", "pw", "", "100", "test4@example.com"))
    cases.append(("1", "pw", "", "100", "test4new@example.com"))
    # components that could collide if order/normalization were wrong:
    cases.append(("", "", "", "", None))
    cases.append(("", "", "", "", "x"))
    cases.append(("a", "b", "c", "d", "e"))
    return cases


def main() -> int:
    checked = 0

    for args in _enumerate_edge():
        d = disagree(args)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        def pick():
            return ALPHABET[next(rnd) % len(ALPHABET)]
        pk = pick()
        password = pick()
        login_ts = pick()
        ts = pick()
        # email_raw: None ~1/3 of the time, else a string (possibly '')
        r = next(rnd) % 3
        email_raw = None if r == 0 else pick()
        d = disagree((pk, password, login_ts, ts, email_raw))
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
