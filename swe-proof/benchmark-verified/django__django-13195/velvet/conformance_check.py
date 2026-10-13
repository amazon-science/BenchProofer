#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13195.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing the THIRTEEN observable cookie
morsel fields (which cookie is addressed AND the name the entry announces on the
wire, the body handed over and the form it is transmitted in, the granted
lifetime and announced expiry, secure, httponly, samesite, path, domain, and the
note and version a directive could add):

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo types: `secureForClear` /
              `hasSecurePrefix` / `crossSiteUnrestricted` and the field-wise
              `mkCookie`. There are NO A-consumed callees, so nothing is stubbed;
              the one A-reference callee (`set_cookie`) is exercised live by the
              ORACLE side, and the shadow predicts its thirteen observed fields.
  * ORACLE  — patch.diff's behaviour: the patched `HttpResponseBase.delete_cookie`
              applied at base_commit (the harness git-applies patch.diff before
              this runs), read back from the resulting cookie morsel.

They must agree on every accepted-policy input. Exit 0 iff zero disagreements;
any disagreement is a mechanical R/I-fidelity counterexample. Stdlib + Django
only; the fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEFAULT_CHARSET="utf-8",
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_DOMAIN=None,
        SESSION_COOKIE_PATH="/",
    )
django.setup()

from django.http import HttpResponse

SEED = 13195
N_FUZZ = 100_000

# accepted cross-site-policy domain (set_cookie raises ValueError otherwise)
ACCEPTED = [None, "Lax", "lax", "None", "none", "Strict", "strict"]


# --- the R/I shadow: Solution.lean ops transliterated ------------------------

def has_secure_prefix(key):                 # hasSecurePrefix
    return key.startswith(("__Secure-", "__Host-"))


def cross_site_unrestricted(samesite):      # crossSiteUnrestricted
    return bool(samesite) and samesite.lower() == "none"


def secure_for_clear(key, samesite):        # secureForClear
    return has_secure_prefix(key) or cross_site_unrestricted(samesite)


EPOCH_EXPIRY = "Thu, 01 Jan 1970 00:00:00 GMT"   # epochExpiry
CLEARED_MAX_AGE = 0                              # clearedMaxAge
QUOTED_EMPTY_BODY = '""'                         # quotedEmptyBody


def shadow_delete(key, path, domain, samesite):
    """The R/I shadow of deleteCookie: the directive is addressed to the very
    cookie it was asked to clear; derive secure, then the field-wise mkCookie
    image (name, value, the body's transmitted form, max-age, expires, secure,
    httponly, samesite, path, domain, comment, version) with absent
    policy/domain left unset (None). The emptied body plus the spent lifetime and
    epoch expiry are what make the entry a CLEARING directive rather than an
    ordinary assignment; the transmitted body form is what a recipient actually
    reads for it; and the note/version attributes a clearing directive never
    states are observed so a directive that adds one is a different one."""
    secure = secure_for_clear(key, samesite)
    model_samesite = samesite if samesite else None
    model_domain = domain if domain is not None else None
    # the addressee and the name the entry announces on the wire are the same name
    # here: handing a body over for a cookie is what fixes the name the resulting
    # entry announces.
    return (key, key, "", QUOTED_EMPTY_BODY, CLEARED_MAX_AGE, EPOCH_EXPIRY,
            bool(secure), False, model_samesite, path, model_domain, None, None)


# --- the oracle: patch.diff's patched delete_cookie --------------------------

def oracle_delete(key, path, domain, samesite):
    resp = HttpResponse()
    resp.delete_cookie(key, path=path, domain=domain, samesite=samesite)  # patched
    # read WHICH cookie the directive was filed under rather than assuming `key`:
    # a routine clearing some other cookie must be observably different here.
    (obs_name,) = tuple(resp.cookies.keys())
    m = resp.cookies[obs_name]
    obs_secure = (m["secure"] is True) or bool(m["secure"])
    obs_httponly = (m["httponly"] is True) or bool(m["httponly"])
    obs_samesite = m["samesite"] if m["samesite"] != "" else None
    obs_path = m["path"]
    obs_domain = m["domain"] if m["domain"] != "" else None
    # '' is the unset sentinel for both lifetime attributes, so an omitted one is
    # observably different from a stated one.
    obs_max_age = m["max-age"] if m["max-age"] != "" else None
    obs_expires = m["expires"] if m["expires"] != "" else None
    # the wire form of the body, and the two attributes a clearing directive
    # never states ('' is the unset sentinel for both).
    obs_coded = m.coded_value
    obs_comment = m["comment"] if m["comment"] != "" else None
    obs_version = m["version"] if m["version"] != "" else None
    # the name the entry ANNOUNCES on the wire, read off the morsel itself: the
    # emitted header's name half comes from the entry's own name, not from the key
    # it is filed under, so the two are separate observables and an entry filed
    # correctly can still announce another name or none at all.
    obs_transmitted = m.key if m.key is not None else ""
    return (obs_name, obs_transmitted, m.value, obs_coded, obs_max_age,
            obs_expires, obs_secure,
            obs_httponly, obs_samesite, obs_path, obs_domain, obs_comment,
            obs_version)


def fuzz_inputs(n, rng):
    keys = ["c", "messages", "sessionid", "__Secure-c", "__Host-c", "x" * 40,
            # the punctuation the name alphabet admits, and near-misses of the
            # names reserved for a directive's own attributes: all recordable, so
            # all inside the domain the spec declares.
            "!#$%&'*+-.^_`|~:", "a.b", "A", "0", "maxage", "max_age", "pathx",
            "xpath", "Comments", "versionx", "0expires"]
    paths = ["/", "/example/", "/a/b/c"]
    domains = [None, ".example.com", ".example.local"]
    # boundary grid first
    for key in keys:
        for path in paths:
            for domain in domains:
                for samesite in ACCEPTED:
                    yield (key, path, domain, samesite)
    # randomized fuzz over the WHOLE alphabet a recordable name admits — the
    # region the spec's `recordableKey` require declares. A safe subset would
    # leave part of the declared domain uncovered.
    keychars = ("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
                "0123456789!#$%&'*+-.^_`|~:")
    prefixes = ["", "__Secure-", "__Host-"]
    pathchars = "abcXYZ0_/"
    for _ in range(n):
        key = rng.choice(prefixes) + "".join(
            rng.choice(keychars) for _ in range(rng.randint(1, 12)))
        # keep the draw inside the declared domain: a name that IS one of the
        # reserved attribute names is outside it (the callee records nothing and
        # fails there), so it is not an input this shadow claims anything about.
        if key.lower() in ("comment", "domain", "expires", "httponly", "max-age",
                           "path", "samesite", "secure", "version"):
            continue
        path = "/" + "".join(rng.choice(pathchars) for _ in range(rng.randint(0, 8)))
        domain = rng.choice([None, "." + "".join(rng.choice("abc.") for _ in range(rng.randint(1, 6)))])
        samesite = rng.choice(ACCEPTED)
        yield (key, path, domain, samesite)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for (key, path, domain, samesite) in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_delete(key, path, domain, samesite)
        oracle = oracle_delete(key, path, domain, samesite)
        if shadow != oracle:
            disagreements.append((key, path, domain, samesite, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for k, p, d, s, sh, orc in disagreements:
            print("  key=%r path=%r domain=%r samesite=%r shadow=%r oracle=%r"
                  % (k, p, d, s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of deleteCookie agrees with patch.diff behaviour "
          "on %d inputs (seed=%d), 0 disagreements, over name/value/coded-value/"
          "max-age/expires/secure/httponly/samesite/path/domain/comment/version."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
