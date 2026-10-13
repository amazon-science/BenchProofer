#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13195.

The ONLY kind-A construct in this bundle is the A-reference deep model
`mkCookie`, which stands for the UNCHANGED low-level attribute-setter
`HttpResponseBase.set_cookie` (django/http/response.py:158) AS A CLEARING
DIRECTIVE INVOKES IT, on the THIRTEEN cookie fields the requested behavior
observes (the addressee, the name the entry announces on the wire, the body and
the form that body is transmitted in, max-age, expires, secure, httponly,
samesite, path, domain, comment, version).

This check runs the REAL `set_cookie` callee in-container (NO gold patch applied
— `set_cookie` is unchanged by the patch) on boundary + fuzzed inputs and
asserts that the resulting cookie morsel equals the field-wise model `mkCookie`:

    set_cookie(key, '', max_age=0, path=path, domain=domain, secure=secure,
               expires='Thu, 01 Jan 1970 00:00:00 GMT', httponly=False,
               samesite=samesite)
  ==>  the morsel is filed under key        (which cookie is addressed)
       morsel.key      == key               (the name the entry ANNOUNCES on the
                                             wire, read off the entry itself)
       morsel.value    == ''                (an emptied body)
       morsel.coded_value == '""'           (the form that body is transmitted in)
       morsel['max-age'] == 0               (the spent lifetime)
       morsel.expires  == the epoch moment  (the announced past expiry)
       morsel.secure   == secure            (else '')
       morsel.httponly is unset             (the directive marks no such flag)
       morsel.samesite == samesite          (only set when samesite truthy)
       morsel.path      == path
       morsel.domain    == domain           (only set when domain not None)
       morsel.comment / morsel.version are unset (the directive states neither)

The announced name is a SECOND observable, not a restatement of the addressee:
the emitted `Set-Cookie: <name>=...` header takes its name half from the entry's
own name, while the addressee is the key the entry is filed under in the
response's container. The two can disagree — an entry can sit under exactly the
right cookie and announce another name, or none — so this probe reads the
announced name off the entry rather than off the container.

The lifetime pair (max-age / expires) is part of the A-reference's projection
because it is what makes the emitted entry a CLEARING directive rather than an
ordinary cookie assignment: a morsel carrying neither is kept by the browser for
the rest of the session, so a routine that omits them has not cleared anything.
An earlier revision of this probe compared only the five flag/scope fields, which
left that distinction outside everything the bundle could observe.

The probe also runs a CONTROL-CHARACTER census on `path` and `domain` (the 33 C0
codepoints \x00-\x1F and \x7F, in each parameter and in both at once). The spec
puts no character bound on `path` and excludes only the EMPTY scope for `domain`,
so that region is in-domain and the postcondition demands the morsel carry the
character verbatim; the boundary grid and the fuzz below both draw paths from a
safe alphabet, so without the census G-AX would pass vacuously over it. The answer
moves with the INTERPRETER rather than the repository — the pinned image's CPython
3.6.13 `Morsel.__setitem__` does no such screening, a later CPython adds
`_has_control_character` and raises — and the pinned image is the reference,
because it is where the FAIL_TO_PASS/PASS_TO_PASS oracle runs. See mapping.md §3.1.

There are NO consumed axioms in this bundle, so no axiom Ensures to validate
beyond this A-reference. Imports only Django (the repo under test). Exit 0 iff
sound.
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

EXPIRES = "Thu, 01 Jan 1970 00:00:00 GMT"
# `quotedEmptyBody`: the wire form an EMPTIED body goes out in.
QUOTED_EMPTY_BODY = '""'
ACCEPTED = [None, "Lax", "lax", "None", "none", "Strict", "strict"]


def morsel_fields(key, path, domain, secure, samesite):
    """Run the REAL unchanged set_cookie callee exactly as the clearing routine
    does, and read back the thirteen observed morsel fields. The cookie the
    directive is ADDRESSED to is read as the key the morsel is actually filed
    under, so a directive filed elsewhere is observably a different cookie; the
    name the entry ANNOUNCES on the wire is read separately off the morsel
    itself, because the emitted header is built from that name and not from the
    key the morsel is filed under, so an entry filed correctly can still announce
    another name or none."""
    resp = HttpResponse()
    resp.set_cookie(
        key, "", max_age=0, path=path, domain=domain, secure=secure,
        expires=EXPIRES, httponly=False, samesite=samesite,
    )
    # the only key present is the cookie the directive was addressed to
    (obs_name,) = tuple(resp.cookies.keys())
    m = resp.cookies[obs_name]
    # morsel stores '' for unset boolean/flag attributes; True for set secure.
    obs_secure = (m["secure"] is True) or (m["secure"] == "True") or bool(m["secure"])
    obs_httponly = (m["httponly"] is True) or bool(m["httponly"])
    obs_samesite = m["samesite"] if m["samesite"] != "" else None
    obs_path = m["path"]
    obs_domain = m["domain"] if m["domain"] != "" else None
    # the lifetime pair: '' is the unset sentinel for both, mapped to None so an
    # omitted attribute is observably different from a stated one.
    obs_max_age = m["max-age"] if m["max-age"] != "" else None
    obs_expires = m["expires"] if m["expires"] != "" else None
    # the form the body is TRANSMITTED in: the cookie machinery encodes a body
    # before it goes on the wire, and an emptied body does not encode to nothing.
    obs_coded = m.coded_value
    # the two attributes a clearing directive never states; '' is unset.
    obs_comment = m["comment"] if m["comment"] != "" else None
    obs_version = m["version"] if m["version"] != "" else None
    # the name the entry ANNOUNCES on the wire: the emitted header's name half is
    # built from the morsel's OWN name, which is a different observable from the
    # key it is filed under. An entry never handed its body through the container
    # carries no name of its own at all, and announces nothing.
    obs_transmitted = m.key if m.key is not None else ""
    return (obs_name, obs_transmitted, m.value, obs_coded, obs_max_age,
            obs_expires, obs_secure,
            obs_httponly, obs_samesite, obs_path, obs_domain, obs_comment,
            obs_version)


def mk_cookie_model(name, secure, samesite, path, domain):
    """The Lean deep model `mkCookie`: records exactly these thirteen fields — the
    addressee AND the name the entry announces on the wire (the same name: handing
    a body over for a cookie is what fixes the name the entry announces), an
    emptied body AND the form that body is transmitted in, the
    spent lifetime and the epoch expiry a clearing directive announces, the two
    flags, the policy/scope with an absent (falsy) samesite/domain left unset
    (None), and neither a note nor a version of its own."""
    model_samesite = samesite if samesite else None
    model_domain = domain if domain is not None else None
    return (name, name, "", QUOTED_EMPTY_BODY, 0, EXPIRES, bool(secure), False,
            model_samesite, path, model_domain, None, None)


def check(key, path, domain, secure, samesite):
    observed = morsel_fields(key, path, domain, secure, samesite)
    expected = mk_cookie_model(key, secure, samesite, path, domain)
    assert observed == expected, (
        "mkCookie A-reference unsound for key=%r path=%r domain=%r secure=%r "
        "samesite=%r: real set_cookie morsel=%r, deep model=%r"
        % (key, path, domain, secure, samesite, observed, expected))


def main():
    keys = ["c", "messages", "sessionid", "__Secure-c", "__Host-c", "x" * 40,
            # names built from the punctuation the alphabet admits, and
            # near-misses of the reserved attribute names (one character off, or
            # a different separator) — all recordable, so all in the domain.
            "!#$%&'*+-.^_`|~:", "a.b", "A", "0", "maxage", "max_age", "pathx",
            "xpath", "secures", "Comments", "versionx", "domain-", "0expires"]
    paths = ["/", "/example/", "/a/b/c", ""]
    domains = [None, ".example.com", ".example.local", "example.org"]

    # --- boundary grid over the five observed fields ------------------------
    n = 0
    for key in keys:
        for path in paths:
            for domain in domains:
                for samesite in ACCEPTED:
                    for secure in (True, False):
                        check(key, path, domain, secure, samesite)
                        n += 1

    # --- CONTROL-CHARACTER census on `path` and `domain` --------------------
    # The spec puts NO character bound on `path`, and `domainStated` excludes only
    # the EMPTY scope, so every C0 control character (\x00-\x1F plus \x7F, 33
    # codepoints, '\n' and '\t' among them) is in-domain for both parameters and
    # the postcondition demands the morsel carry it VERBATIM. The grid above and
    # the fuzz below both draw paths from a safe alphabet ("abcXYZ0_/"), so
    # without this block that whole region of the declared domain would go
    # unmeasured and G-AX would pass vacuously over it.
    #
    # It is measured rather than argued because the answer moves with the
    # INTERPRETER, not with the repository: `http.cookies.Morsel.__setitem__` is
    # `dict.__setitem__` after the reserved-key test on the pinned image's CPython
    # 3.6.13, while a LATER CPython adds `_has_control_character` and raises
    # `CookieError` on exactly these codepoints. The pinned image is the reference
    # (it is where the FAIL_TO_PASS/PASS_TO_PASS oracle runs), so this block reads
    # the answer off the interpreter the bundle actually ships against instead of
    # inheriting a host's.
    ctrl = [chr(i) for i in list(range(0x00, 0x20)) + [0x7F]]
    assert len(ctrl) == 33, len(ctrl)
    nc = 0
    for c in ctrl:
        for key in ("c", "__Host-c"):
            for samesite in ACCEPTED:
                for secure in (True, False):
                    # the control character alone as a path; embedded in a
                    # domain; and in both at once.
                    for path, domain in ((c, None), ("/", "a" + c + "b"), (c, c)):
                        check(key, path, domain, secure, samesite)
                        n += 1
                        nc += 1

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(13195)
    # The WHOLE alphabet a recordable cookie name admits, not a safe subset: the
    # spec's `recordableKey` require declares this entire region, so the probe
    # has to cover it or it passes vacuously over part of what the spec claims.
    keychars = ("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
                "0123456789!#$%&'*+-.^_`|~:")
    prefixes = ["", "__Secure-", "__Host-"]
    pathchars = "abcXYZ0_/"
    for _ in range(20000):
        key = rng.choice(prefixes) + "".join(
            rng.choice(keychars) for _ in range(rng.randint(1, 12)))
        path = "/" + "".join(rng.choice(pathchars) for _ in range(rng.randint(0, 8)))
        domain = rng.choice([None, "." + "".join(rng.choice("abc.") for _ in range(rng.randint(1, 8)))])
        samesite = rng.choice(ACCEPTED)
        secure = rng.choice([True, False])
        check(key, path, domain, secure, samesite)
        n += 1

    # --- the DECLARED DOMAIN is exactly the region the callee records ------
    # The spec bounds the behaviour to names the attribute-setter will actually
    # record (`recordableKey`) for the same reason it bounds the policy value:
    # outside it the callee records NOTHING and fails outright, so there is no
    # filed directive to describe. Both directions are checked here, so the
    # boundary is measured rather than asserted: every name the predicate admits
    # is recorded, and every name it excludes raises.
    reserved = ("comment", "domain", "expires", "httponly", "max-age", "path",
                "samesite", "secure", "version")
    legal = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
                "0123456789!#$%&'*+-.^_`|~:")

    def recordable(k):
        return (k != "" and all(c in legal for c in k)
                and k.lower() not in reserved)

    excluded = ["", "a b", "a;b", "a=b", 'a"b', "a,b", "a/b", "a(b", "a\tb",
                "\u00e9", "k\u00f8", "A\u0301"]
    excluded += [r for r in reserved]
    excluded += [r.upper() for r in reserved]
    excluded += [r.capitalize() for r in reserved]
    excluded += ["SaMeSiTe", "Max-Age", "MAX-AGE", "Path", "Secure"]
    nb = 0
    for k in excluded:
        assert not recordable(k), "predicate admits %r but it is listed excluded" % (k,)
        resp = HttpResponse()
        try:
            resp.set_cookie(k, "", max_age=0, path="/", expires=EXPIRES)
        except Exception:
            nb += 1
            continue
        raise AssertionError(
            "name %r is EXCLUDED by the spec's declared domain but the real "
            "attribute-setter records it, so the domain excludes reachable "
            "behaviour" % (k,))
    # ...and nothing the predicate ADMITS raises (the grid+fuzz above already
    # ran only admitted names, and every one of them was recorded).
    for k in keys:
        assert recordable(k), "boundary name %r is outside the declared domain" % (k,)

    print("G-AX OK: mkCookie deep model (== real unchanged set_cookie) sound on "
          "%d (boundary + %d control-character path/domain census + 20000 fuzz) "
          "inputs over name/value/coded-value/"
          "max-age/expires/secure/httponly/samesite/path/domain/comment/version; "
          "declared-domain boundary confirmed both ways on %d excluded names "
          "(each records nothing and fails) and %d admitted boundary names."
          % (n, nc, nb, len(keys)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
