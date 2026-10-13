#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-13195.

The bundle models the cookie-DELETION routine `HttpResponseBase.delete_cookie`
(mapping.md) and its two delegating call sites. The modeled value is the
container entry the routine leaves behind, in FULL: the index it is filed at,
the two components the container RENDERS it with (`Morsel.key` and
`Morsel.coded_value`, which `Morsel.OutputString` emits first as
`"%s=%s" % (self.key, self.coded_value)`), the payload it reads back, and all
nine attributes `Morsel._reserved` holds. Twelve components, which is exactly
what `Cookie` in Solution.lean carries — a `Morsel` has no thirteenth slot, so
the two sides are compared over the whole entry and not over a projection of it.

  ORACLE  = a faithful in-process replica of the POST-PATCH `delete_cookie`,
            whose `set_cookie` leg performs its container write against the REAL
            `http.cookies.SimpleCookie` the response uses. Every component is
            READ BACK off the resulting `Morsel` — nothing about the entry is
            asserted by this file, so a component the model gets wrong is a
            disagreement rather than an agreement by construction.
  SHADOW  = the op-for-op transliteration of `implementation_deleteCookie` and
            the pure helpers it calls (`deleteSecure`, `setCookie`, `valueEncode`,
            `quoteChar`, `cookieNameChar`, `cookieUnescapedChar`) from the
            Solution.lean impl/pure regions, per refinement.md. It computes the
            entry from the model's own definitions, reading nothing from
            `http.cookies`.

Standing up the full `HttpResponse` is unnecessary — the modeled value is this
pure decision over the arguments the real function reads — but standing up the
real `SimpleCookie` is NOT: the rendered name and the coded payload are produced
by `Morsel.set` and `SimpleCookie.value_encode`, so deriving them means calling
them. An earlier revision of this file hardcoded `"name": key` on BOTH sides,
which made the two agree on the rendered identity whatever either one believed
about it; that is why two impls re-stamping the rendered components went
undetected here.

Two legs, one disagreement count:

  1. the deletion itself, over fuzzed `(key, path, domain, samesite)` AND over a
     fuzzed PRE-EXISTING entry at the same index — the state the four guarded
     attribute writes and the two parameterless attributes are carried across,
     which is what the model's `*After` helpers and its `comment` / `version`
     carry-over describe.
  2. the payload encoder alone, over fuzzed payload strings: the oracle is
     `SimpleCookie.value_encode`, the shadow is the transliteration of Lean's
     `valueEncode`. A deletion only ever encodes the empty payload, so leg 1
     pins the encoder at one point; this leg exercises the whole alphabet
     (legal characters, the unescaped punctuation, `"` and `\\`, the octal
     escapes for the remaining bytes, and the codepoints at or above 256 the
     translation table does not reach).

This genuinely exercises the soundness-critical clause: a deletion with
`samesite='none'` must force `secure`, and the requested `samesite` policy must
be recorded (unset only when falsy) — matching the F2P expectations.

Imports nothing beyond the stdlib and `django.http.cookie` — the one repo module
`django/http/response.py` gets its container from, which is where the `samesite`
attribute comes from at all on the container's Python. Pinned seed: 13195 (also
in mapping.md / meta.json).
"""
import json
import random
import string
import sys

# `django/http/response.py:16` is `from django.http.cookie import SimpleCookie`,
# so this is the container the routine under test actually writes into. Which
# module it comes from is load-bearing rather than cosmetic: `django/http/cookie.py`
# also runs `cookies.Morsel._reserved.setdefault('samesite', 'SameSite')`, and the
# container's interpreter is CPython 3.6.13, whose stdlib table has only EIGHT
# reserved attributes (no `samesite`). Importing `http.cookies` directly would make
# `morsel['samesite'] = …` raise `CookieError`, and modeling only those eight would
# make `reservedCookieNames` and the carrier both wrong by one attribute. Measured
# in-container: eight before the import, nine after.
from django.http.cookie import SimpleCookie
from http.cookies import Morsel

assert "samesite" in Morsel._reserved, "django.http.cookie did not register samesite"
assert len(Morsel._reserved) == 9, sorted(Morsel._reserved)

SEED = 13195
N = 150_000
M = 60_000

EPOCH = "Thu, 01 Jan 1970 00:00:00 GMT"
SAMESITE_VALUES = [None, "", "lax", "Lax", "LAX", "none", "None", "NONE",
                   "strict", "Strict"]
KEYS = ["c", "messages", "sessionid", "__Secure-x", "__Host-y", "__secure-x",
        "x__Host-", "", "a", "A", "__Secure-", "__Host-", "a.b", "x|y", "z9",
        "path", "9"]
PATHS = ["/", "/example/", "/app"]
DOMAINS = [None, ".example.com", ".example.local", "example.org"]

# The nine attributes `Morsel._reserved` holds, as `set_cookie`'s vocabulary
# spells them. `expires` / `max-age` / `path` are re-written by every
# `set_cookie` call; the other six are what an entry can carry ACROSS a call.
PRIOR_DOMAINS = ["", ".old.example.com"]
PRIOR_SAMESITE = ["", "Strict", "lax", "none"]
PRIOR_COMMENTS = ["", "annotated"]
PRIOR_VERSIONS = ["", "1"]
PRIOR_VALUES = ["", "old", "old value", 'q"uote']

# The payload alphabet for leg 2. Legal-name characters, the punctuation
# `_UnescapedChars` adds, the two characters with their own escape, characters
# that must become an octal escape (control bytes, the comma and semicolon a
# header would otherwise split on, the high Latin-1 range), and two codepoints
# at or above 256, which the translation table does not cover.
PAYLOAD_CHARS = (list("abzAZ09") + list("!#$%&'*+-.^_`|~:")
                 + list(" ()/<=>?@[]{}") + ['"', "\\"]
                 + ["\x00", "\x09", "\x1f", "\x7f", ",", ";", " "]
                 + ["é", "ÿ"] + ["中", "€"])

# `keyAccepted` (Solution.lean pure region): the domain `Morsel.set` files a
# cookie under. The nine reserved attribute names, and the alphabet
# `_is_legal_key` matches.
RESERVED_COOKIE_NAMES = ("comment", "domain", "expires", "httponly", "max-age",
                         "path", "samesite", "secure", "version")
_NAME_CHARS = frozenset(string.ascii_letters + string.digits
                        + "!#$%&'*+-.^_`|~:")
_UNESCAPED_EXTRA = frozenset(" ()/<=>?@[]{}")


# --------------------------------------------------------------------------
# SHADOW: the transliteration of Solution.lean. Reads nothing from the stdlib.
# --------------------------------------------------------------------------

def _key_accepted(key):
    """keyAccepted."""
    return (key != "" and key.lower() not in RESERVED_COOKIE_NAMES
            and all(c in _NAME_CHARS for c in key))


def _cookie_name_char(c):
    """cookieNameChar. `Char.isAlphanum` is ASCII-only, hence the explicit set."""
    return c in _NAME_CHARS


def _cookie_unescaped_char(c):
    """cookieUnescapedChar."""
    return c in _NAME_CHARS or c in _UNESCAPED_EXTRA


def _octal_digit(n):
    """octalDigit."""
    return chr(48 + n % 8)


def _octal_escape(n):
    """octalEscape."""
    return "\\" + _octal_digit(n // 64) + _octal_digit(n // 8) + _octal_digit(n)


def _quote_char(c):
    """quoteChar."""
    if c == '"':
        return '\\"'
    if c == "\\":
        return "\\\\"
    if _cookie_unescaped_char(c) or ord(c) >= 256:
        return c
    return _octal_escape(ord(c))


def _value_encode(v):
    """valueEncode."""
    if v != "" and all(_cookie_name_char(c) for c in v):
        return v
    return '"' + "".join(_quote_char(c) for c in v) + '"'


def _shadow_set_cookie(prior, key, value, max_age, expires, path, domain,
                       secure, httponly, samesite):
    """setCookie: the entry the write leaves at index `key`.

    `prior` is the entry the index already held (`None` for an index that held
    nothing), i.e. what `storedOrDefault resp.cookies key` returns; the six
    `*After` / carry-over components read it.
    """
    stored = prior if prior is not None else {
        "name": "", "value": "", "coded_value": "", "max-age": None,
        "expires": "", "path": "", "domain": "", "secure": False,
        "httponly": False, "samesite": "", "comment": "", "version": "",
    }
    return {
        # `cookies := fun k => if k = key then some { … }` — the index written.
        "index": key,
        # `key := key` — the name the entry is RENDERED under, re-stamped by
        # this write whatever the index already held.
        "name": key,
        # `value := value` and `codedValue := valueEncode value`.
        "value": value,
        "coded_value": _value_encode(value),
        # written for every call
        "max-age": max_age,
        "expires": expires,
        "path": path,
        # `domainAfter` / `secureAfter` / `httpOnlyAfter` / `samesiteAfter`:
        # a write may ADD these but never CLEAR them.
        "domain": domain if domain is not None else stored["domain"],
        "secure": bool(secure) or bool(stored["secure"]),
        "httponly": bool(httponly) or bool(stored["httponly"]),
        "samesite": samesite if samesite else stored["samesite"],
        # no `set_cookie` parameter reaches these two
        "comment": stored["comment"],
        "version": stored["version"],
    }


def shadow(prior, key, path, domain, samesite):
    """implementation_deleteCookie."""
    # deleteSecure: prefix OR (samesite truthy && lower == none)
    secure = (
        key.startswith("__Secure-")
        or key.startswith("__Host-")
        or (bool(samesite) and samesite.lower() == "none")
    )
    return _shadow_set_cookie(prior, key, "", 0, EPOCH, path, domain, secure,
                              False, samesite)


# --------------------------------------------------------------------------
# ORACLE: the post-patch Python, writing into a real `SimpleCookie`.
# --------------------------------------------------------------------------

def _read_morsel(jar, key):
    """The twelve components of the entry at `key`, read off the real Morsel."""
    morsel = jar[key]
    return {
        "index": key,
        "name": morsel.key,
        "value": morsel.value,
        "coded_value": morsel.coded_value,
        "max-age": morsel["max-age"] if morsel["max-age"] != "" else None,
        "expires": morsel["expires"],
        "path": morsel["path"],
        "domain": morsel["domain"],
        "secure": bool(morsel["secure"]),
        "httponly": bool(morsel["httponly"]),
        "samesite": morsel["samesite"],
        "comment": morsel["comment"],
        "version": morsel["version"],
    }


def _real_set_cookie(jar, key, value, max_age, expires, path, domain, secure,
                     httponly, samesite):
    """Replica of `HttpResponseBase.set_cookie` (django/http/response.py).

    Branch for branch, against the real container: the unconditional index
    write, the `expires` / `max-age` / `path` writes, the four guarded attribute
    writes, and the `samesite` validation.
    """
    jar[key] = value
    if expires is not None:
        jar[key]["expires"] = expires
    else:
        jar[key]["expires"] = ""
    if max_age is not None:
        jar[key]["max-age"] = int(max_age)
        if not expires:
            raise AssertionError("unreachable: delete_cookie supplies expires")
    if path is not None:
        jar[key]["path"] = path
    if domain is not None:
        jar[key]["domain"] = domain
    if secure:
        jar[key]["secure"] = True
    if httponly:
        jar[key]["httponly"] = True
    if samesite:
        if samesite.lower() not in ("lax", "none", "strict"):
            raise ValueError('samesite must be "lax", "none", or "strict".')
        jar[key]["samesite"] = samesite
    return jar


def oracle(prior, key, path, domain, samesite):
    """Post-patch `delete_cookie` (gold patch.diff), on a real container."""
    jar = SimpleCookie()
    if prior is not None:
        _seed_prior(jar, key, prior)
    secure = (
        key.startswith(("__Secure-", "__Host-"))
        or (samesite and samesite.lower() == "none")
    )
    _real_set_cookie(jar, key, "", 0, EPOCH, path, domain, secure, False,
                     samesite)
    return _read_morsel(jar, key)


def _seed_prior(jar, key, prior):
    """Put the fuzzed pre-existing entry into the real container."""
    jar[key] = prior["value"]
    for attr in ("domain", "samesite", "comment", "version"):
        if prior[attr]:
            jar[key][attr] = prior[attr]
    for flag in ("secure", "httponly"):
        if prior[flag]:
            jar[key][flag] = True


# --------------------------------------------------------------------------

def main():
    rng = random.Random(SEED)
    disagreements = 0
    examples = []
    checked = 0

    for _ in range(N):
        key = rng.choice(KEYS)
        path = rng.choice(PATHS)
        domain = rng.choice(DOMAINS)
        samesite = rng.choice(SAMESITE_VALUES)
        if rng.random() < 0.5:
            prior = None
        else:
            prior = {
                "value": rng.choice(PRIOR_VALUES),
                "domain": rng.choice(PRIOR_DOMAINS),
                "samesite": rng.choice(PRIOR_SAMESITE),
                "comment": rng.choice(PRIOR_COMMENTS),
                "version": rng.choice(PRIOR_VERSIONS),
                "secure": rng.random() < 0.5,
                "httponly": rng.random() < 0.5,
            }
        # Preconditions (keyAccepted, samesiteValid): skip inputs the container
        # or `set_cookie` would reject — the modeled `correct_*` carries both as
        # hypotheses, so they bound the declared domain rather than the impl.
        if not _key_accepted(key):
            continue
        if samesite and samesite.lower() not in ("lax", "none", "strict"):
            continue
        checked += 1
        o = oracle(prior, key, path, domain, samesite)
        s = shadow(prior, key, path, domain, samesite)
        if o != s:
            disagreements += 1
            if len(examples) < 10:
                examples.append({"leg": "delete_cookie",
                                 "in": [prior, key, path, domain, samesite],
                                 "oracle": o, "shadow": s})

    enc = SimpleCookie()
    for _ in range(M):
        payload = "".join(rng.choice(PAYLOAD_CHARS)
                          for _ in range(rng.randrange(0, 6)))
        checked += 1
        o_enc = enc.value_encode(payload)[1]
        s_enc = _value_encode(payload)
        if o_enc != s_enc:
            disagreements += 1
            if len(examples) < 10:
                examples.append({"leg": "value_encode", "in": [payload],
                                 "oracle": o_enc, "shadow": s_enc})

    result = {
        "status": "pass" if disagreements == 0 else "fail",
        "instance": "django__django-13195",
        "checked": checked,
        "disagreements": disagreements,
        "examples": examples,
        "seed": SEED,
    }
    print(json.dumps(result))
    sys.exit(0 if disagreements == 0 else 1)


if __name__ == "__main__":
    main()
