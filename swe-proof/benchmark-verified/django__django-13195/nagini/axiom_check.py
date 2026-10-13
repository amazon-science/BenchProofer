#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13195.

Runs the REAL callees in-container and asserts every observation meets the
contracts encoded in model.py.

  (A-consumed)  the `store_cookie` axiom (model.py axioms region) models the
      unchanged cookie attribute setter `HttpResponseBase.set_cookie`, AS THE
      EXPIRY ROUTINE INVOKES IT (the already-elapsed lifetime is a constant of
      that call site, so the check passes it exactly as the call site does). For
      every (path, domain, secure, policy) tuple the axiom claims the emitted
      morsel records:
        - the already-elapsed lifetime that makes the cookie an expiry;
        - the transport-secure flag CUMULATIVELY (a request turns it on, nothing
          turns it off);
        - a request path and a domain: a non-empty value installs itself
          verbatim, and an empty one installs nothing of its own, so any value
          the morsel carries afterwards is the one it already carried; and
        - a cross-site ('samesite') attribute present iff a non-empty policy was
          given, equal to that value verbatim, and otherwise left as it stood.
      We exercise the REAL `set_cookie` (boundary + fuzz), from a FRESH morsel
      and from a morsel that already carries attributes — the cumulative clauses
      are claims about the second case, so they are measured there.

  (A-reference)  the changed expiry routine `delete_cookie`, whose two introduced
      decisions are modelled DEEPLY in model.py (`expiry_secure` = security
      prefix OR case-insensitive "none"; and verbatim forwarding of the policy).
      We exercise the REAL post-patch `delete_cookie` and check that every
      postcondition model.py states of the emitted cookie holds of the real
      morsel: the elapsed lifetime, the secure flag == the deep model, the
      verbatim policy forwarding, and the reach (path / domain) the routine was
      asked for. This is NOT a consumed axiom; it validates the deep model ==
      real callee.

  (A-domain)  the DOMAIN both of the above speak about. The cookie machinery
      records a cookie only under a name in the header grammar's alphabet that is
      not one of the nine names it reserves for the header's own attributes;
      handed any other name it refuses the request outright, records nothing, and
      the expiry raises instead of returning. model.py states that domain as
      `is_storable_name` (a precondition of the expiry, and the standing
      assumption of the `store_cookie` axiom, whose morsel is the record held
      under the name). We exercise the REAL setter and the REAL expiry over an
      exhaustive ASCII sweep + the reserved names in several casings + the empty
      name + non-ASCII + fuzz, and check the predicate agrees with
      records-vs-refuses in BOTH directions. A name inside the predicate on which
      the real machinery refuses would make the spec demand a cookie that does
      not exist; a name outside it on which the real machinery records would make
      the domain narrower than the change it is about. The path and the domain
      carry NO restriction in the spec, because the machinery records them
      without inspecting them: that too is measured here, over a value set that
      includes separators, spaces and non-ASCII.

Imports Django (the package the gold patch lives in); available in the
evaluation container. Exit 0 iff every obligation holds.
"""
import random
import sys

from http.cookies import CookieError

# The already-elapsed lifetime the expiry call site always asks for. It is a
# constant of that call site, not a parameter of the axiom, so the check passes
# it exactly as the call site does.
EXPIRED_LITERAL = "Thu, 01 Jan 1970 00:00:00 GMT"


def _bootstrap_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            SECRET_KEY="x" * 50,
            ALLOWED_HOSTS=["*"],
            DATABASES={},
            INSTALLED_APPS=[],
            # Pin the cross-site default the patch's call sites read; the
            # callee-level checks pass samesite explicitly so this is only a
            # backstop for any default-driven path.
            SESSION_COOKIE_SAMESITE="Lax",
        )
    django.setup()


# --- model.py reference encodings (kept in lock-step with the spec) ----------

def _lower_cp(c):
    if 65 <= c <= 90:
        return c + 32
    return c


def is_none_ci(policy):
    """Reference of model.py `is_none_ci`: case-insensitive == 'none'."""
    if policy is None:
        return False
    cps = [ord(ch) for ch in policy]
    if len(cps) != 4:
        return False
    return (_lower_cp(cps[0]) == 110 and _lower_cp(cps[1]) == 111 and
            _lower_cp(cps[2]) == 110 and _lower_cp(cps[3]) == 101)


def has_security_prefix(key):
    """Reference of model.py `has_security_prefix`."""
    return key.startswith(("__Secure-", "__Host-"))


def expiry_secure(key, policy):
    """Reference of model.py `expiry_secure`."""
    return has_security_prefix(key) or is_none_ci(policy)


def truthy(value):
    """model.py's 'non-empty value'; in the repo, a truthy str argument. None
    and '' both map to the empty list in the model -> nothing is installed."""
    return value is not None and len(value) > 0


# The name alphabet and the reserved attribute names, as model.py's `is_name_char`
# and `is_reserved_name` encode them (code points; kept in lock-step with the
# spec text, NOT read out of http.cookies -- reading the implementation's own
# tables would make this check vacuous).
LEGAL_NAME_CP = frozenset(
    list(range(48, 58)) + list(range(65, 91)) + list(range(97, 123)) +
    [33, 35, 36, 37, 38, 39, 42, 43, 45, 46, 58, 94, 95, 96, 124, 126])

RESERVED_NAMES = ("expires", "path", "comment", "domain", "max-age", "secure",
                  "httponly", "version", "samesite")


def is_name_char(c):
    """Reference of model.py `is_name_char`."""
    return c in LEGAL_NAME_CP


def all_name_chars(key):
    """Reference of model.py `all_name_chars`."""
    return all(is_name_char(ord(ch)) for ch in key)


def is_reserved_name(key):
    """Reference of model.py `is_reserved_name`: any ASCII casing of one of the
    nine names kept for the header's own attributes."""
    folded = "".join(chr(_lower_cp(ord(ch))) for ch in key)
    return folded in RESERVED_NAMES


def is_storable_name(key):
    """Reference of model.py `is_storable_name`: the domain in which a cookie is
    recorded under this name at all."""
    return len(key) > 0 and all_name_chars(key) and not is_reserved_name(key)


# --- helpers to read what the real morsel recorded ---------------------------

def observe(morsel):
    """The model's Cookie projection of a real morsel: the fields model.py's
    Cookie exposes, read off http.cookies' record. An attribute the record does
    not carry reads back as '' (falsey), which is what 'absent' means here."""
    return {
        "secure": morsel["secure"] is True,
        # The already-elapsed lifetime: the emitted cookie carries the elapsed
        # expiry date AND the zero lifetime AND an empty value.
        "expired": (morsel["expires"] == EXPIRED_LITERAL and
                    morsel["max-age"] == 0 and morsel.value == ""),
        "has_path": morsel["path"] != "",
        "path": morsel["path"],
        "has_domain": morsel["domain"] != "",
        "domain": morsel["domain"],
        "has_policy": morsel["samesite"] not in ("", None),
        "policy": morsel["samesite"],
    }


def _check_reach_clauses(what, old, new, path, domain, policy, ctx):
    """The clauses model.py states about the three present-or-absent attributes
    (reach path, domain, cross-site policy), in the cumulative form the real
    recorder has. Shared by the axiom check and the reference check because
    model.py states the same clauses on both."""
    for label, arg, has_key, val_key in (
            ("path", path, "has_path", "path"),
            ("domain", domain, "has_domain", "domain")):
        if truthy(arg):
            assert new[has_key], (
                "%s unsound: %s=%r was not recorded at all (%s)"
                % (what, label, arg, ctx))
            assert new[val_key] == arg, (
                "%s unsound: %s=%r recorded as %r (%s)"
                % (what, label, arg, new[val_key], ctx))
        else:
            # Handed no value, the recorder installs none of its own: any value
            # carried afterwards is the pre-existing one, unchanged. True of
            # BOTH falsey preimages (absent leaves it alone; empty clears it).
            if new[has_key]:
                assert old[has_key] and new[val_key] == old[val_key], (
                    "%s unsound: %s=%r installed %r over a record that carried "
                    "%r (%s)" % (what, label, arg, new[val_key],
                                 old[val_key] if old[has_key] else "nothing",
                                 ctx))
    # The cross-site policy attribute: present iff it was present before or a
    # non-empty value was supplied; the supplied value verbatim; untouched when
    # nothing was supplied.
    assert new["has_policy"] == (old["has_policy"] or truthy(policy)), (
        "%s unsound: samesite=%r left the attribute %s (was %s) (%s)"
        % (what, policy, "present" if new["has_policy"] else "absent",
           "present" if old["has_policy"] else "absent", ctx))
    if truthy(policy):
        assert new["policy"] == policy, (
            "%s unsound: samesite=%r recorded as %r (%s)"
            % (what, policy, new["policy"], ctx))
    else:
        assert new["policy"] == old["policy"], (
            "%s unsound: empty/absent samesite %r changed the attribute from "
            "%r to %r (%s)" % (what, policy, old["policy"], new["policy"], ctx))


def _apply_pre_state(resp, key, pre):
    """Give the morsel a pre-existing record, so the CUMULATIVE clauses (which
    are claims about `Old(...)`) are measured on a state where they say
    something. `pre` is a (secure, path, domain, policy) tuple recorded through
    the same real setter."""
    p_secure, p_path, p_domain, p_policy = pre
    resp.set_cookie(key, max_age=0, expires=EXPIRED_LITERAL, secure=p_secure,
                    path=p_path, domain=p_domain, samesite=p_policy)
    return observe(resp.cookies[key])


FRESH = {"secure": False, "expired": False, "has_path": False, "path": "",
         "has_domain": False, "domain": "", "has_policy": False, "policy": ""}


# --- (A-consumed) store_cookie axiom == real set_cookie ----------------------

def check_set_cookie_axiom(HttpResponse, key, path, domain, secure, policy,
                           pre=None):
    resp = HttpResponse()
    old = _apply_pre_state(resp, key, pre) if pre is not None else dict(FRESH)

    # The setter exactly as the expiry call site invokes it.
    resp.set_cookie(key, max_age=0, expires=EXPIRED_LITERAL, secure=secure,
                    path=path, domain=domain, samesite=policy)
    new = observe(resp.cookies[key])
    ctx = ("key=%r path=%r domain=%r secure=%r policy=%r pre=%r"
           % (key, path, domain, secure, policy, pre))

    # Storing through the setter stamps the already-elapsed lifetime.
    assert new["expired"], (
        "store_cookie axiom unsound: the stored cookie does not carry the "
        "already-elapsed lifetime (%s)" % ctx)

    # The transport-secure flag ACCUMULATES.
    assert new["secure"] == (old["secure"] or bool(secure)), (
        "store_cookie axiom unsound: set_cookie(secure=%r) over secure=%r gave "
        "secure=%r (%s)" % (secure, old["secure"], new["secure"], ctx))

    _check_reach_clauses("store_cookie axiom", old, new, path, domain, policy,
                         ctx)


# --- (A-reference) deep model == real post-patch delete_cookie ---------------

def check_delete_cookie_reference(HttpResponse, key, path, domain, policy,
                                  omit_path=False, pre=None):
    resp = HttpResponse()
    old = _apply_pre_state(resp, key, pre) if pre is not None else dict(FRESH)

    # The post-patch delete_cookie signature accepts samesite=. `omit_path`
    # exercises the routine as the tests reach it most often -- with the reach
    # left to the routine's own default -- which is NOT a falsey preimage: the
    # default is the site root, so the emitted cookie must carry it.
    if omit_path:
        resp.delete_cookie(key, domain=domain, samesite=policy)
        path = "/"
    else:
        resp.delete_cookie(key, path=path, domain=domain, samesite=policy)
    new = observe(resp.cookies[key])
    ctx = ("key=%r path=%r domain=%r policy=%r omit_path=%r pre=%r"
           % (key, path, domain, policy, omit_path, pre))

    # (0) the emitted cookie is an expiry at all.
    assert new["expired"], (
        "spec postcondition unsound: the emitted expiry cookie does not carry "
        "the already-elapsed lifetime (%s)" % ctx)

    # (2) secure flag == expiry_secure(key, policy), accumulated (the deep
    # decision the change introduces).
    want_secure = old["secure"] or expiry_secure(key, policy)
    assert new["secure"] == want_secure, (
        "deep model `expiry_secure` unsound: real secure=%r, model=%r (%s)"
        % (new["secure"], want_secure, ctx))

    # (1) the policy forwarded verbatim, and (0b) the reach the routine was
    # asked for.
    _check_reach_clauses("deep model", old, new, path, domain, policy, ctx)


# --- (A-domain) model name domain == the domain the machinery records under ---

def check_name_domain(HttpResponse, key):
    """`is_storable_name(key)` must be exactly 'the machinery records a cookie
    under this name', measured on BOTH real routines: the unchanged setter the
    `store_cookie` axiom speaks about, and the changed expiry whose emitted-cookie
    obligations are stated under this precondition."""
    storable = is_storable_name(key)

    resp = HttpResponse()
    try:
        resp.set_cookie(key, max_age=0, secure=True, samesite="none")
        set_recorded = key in resp.cookies
    except CookieError:
        set_recorded = False
    assert set_recorded == storable, (
        "store_cookie axiom domain wrong on key=%r: the real set_cookie %s a "
        "cookie under it, model is_storable_name=%r"
        % (key, "records" if set_recorded else "refuses to record", storable))

    resp = HttpResponse()
    try:
        resp.delete_cookie(key, samesite="none")
        del_returned = key in resp.cookies
    except CookieError:
        del_returned = False
    assert del_returned == storable, (
        "spec name domain wrong on key=%r: the real post-patch delete_cookie %s, "
        "model is_storable_name=%r -- the emitted-expiry-cookie obligations are "
        "stated exactly where the predicate holds"
        % (key, "emits an expiry cookie" if del_returned
           else "refuses the request and emits nothing", storable))


def check_reach_unrestricted(HttpResponse, key, path, domain):
    """The spec puts NO restriction on the reach values, because the machinery
    records them without inspecting them. Measured: the real expiry returns and
    records the value verbatim for every reach value probed, including ones a
    validating recorder would refuse."""
    resp = HttpResponse()
    resp.delete_cookie(key, path=path, domain=domain)
    obs = observe(resp.cookies[key])
    if truthy(path):
        assert obs["path"] == path, (
            "reach domain wrong: path=%r recorded as %r" % (path, obs["path"]))
    if truthy(domain):
        assert obs["domain"] == domain, (
            "reach domain wrong: domain=%r recorded as %r"
            % (domain, obs["domain"]))


def main():
    _bootstrap_django()
    from django.http import HttpResponse

    names = [
        "c", "messages", "sessionid", "x",
        "__Secure-c", "__Host-c", "__Secure-", "__Host-",
        "__secure-c", "__host-c",          # wrong case: NOT a security prefix
        "_Secure-c", "Host-c", "a__Host-c",
        "__Secure", "__Host",              # missing trailing '-'
    ]
    policies = [None, "", "lax", "Lax", "LAX",
                "none", "None", "NONE", "nOnE",
                "strict", "Strict", "STRICT"]
    # Reach values: the two falsey preimages (both map to the model's empty
    # list), the routine's own default, the call-site values the graded tests
    # reach, and awkward ones the recorder still accepts.
    paths = [None, "", "/", "/example/", "/a b", "/é"]
    domains = [None, "", ".example.com", ".example.local", "sub.a.b"]
    # Pre-existing records, so the cumulative clauses are measured where they
    # say something rather than only from a fresh morsel.
    pres = [None,
            (False, "/old", ".old.example", None),
            (True, "/old", None, "Lax"),
            (False, None, ".old.example", "Strict"),
            (True, "", "", None)]

    # --- (A-domain) the name domain, before anything is claimed about the
    # emitted cookie: the cross-product names below must all be IN the model's
    # domain (else the checks under them would speak about a cookie the real
    # machinery never records), and the predicate must agree with the real
    # machinery's record-vs-refuse decision on every name probed.
    n_domain = 0
    for key in names:
        assert is_storable_name(key), (
            "boundary name %r is OUTSIDE the model's is_storable_name domain: "
            "the cross-product checks below would be about a cookie the real "
            "machinery does not record" % (key,))

    domain_names = []
    for cp in range(0x20, 0x7f):           # every printable ASCII code point
        ch = chr(cp)
        domain_names += [ch, "a" + ch, ch + "a"]
    for r in RESERVED_NAMES:               # reserved, in several casings
        domain_names += [r, r.upper(), r.capitalize(), r + "x", "x" + r]
    domain_names.append("")                # the empty name
    for cp in (0xE9, 0x131, 0x130, 0x212A, 0x17F, 0x1E9E, 0x3B1, 0x5D0, 0x4E2D):
        domain_names += [chr(cp), "a" + chr(cp)]
    rng_d = random.Random(131950)
    alpha_d = ([chr(c) for c in range(0x20, 0x7f)] +
               ["\xe9", "K", "İ"])  # e-acute, Kelvin sign, I-with-dot
    for _ in range(4000):
        domain_names.append("".join(rng_d.choice(alpha_d)
                                    for _ in range(rng_d.randint(0, 6))))
    for key in names + domain_names:
        check_name_domain(HttpResponse, key)
        n_domain += 1

    # The reach values carry no restriction: measured over an awkward set.
    n_reach = 0
    reach_probe = paths + ["/;x", "/,y", '/"q"', "/x=y", "/中", "/" * 8]
    dom_probe = domains + [";x", "a b", "é.example", "=v"]
    for path in reach_probe:
        for dom in dom_probe:
            check_reach_unrestricted(HttpResponse, "c", path, dom)
            n_reach += 1

    # --- boundary: names x policies x reach x secure, fresh and over a
    # pre-existing record ----------------------------------------------------
    n_axiom = 0
    n_ref = 0
    for key in names:
        for pol in policies:
            for path in paths:
                for dom in (None, ".example.com"):
                    for sec in (True, False):
                        check_set_cookie_axiom(HttpResponse, key, path, dom,
                                               sec, pol)
                        n_axiom += 1
                    check_delete_cookie_reference(HttpResponse, key, path, dom,
                                                  pol)
                    n_ref += 1
            # the routine's own default reach (what most graded tests reach)
            check_delete_cookie_reference(HttpResponse, key, None, None, pol,
                                          omit_path=True)
            n_ref += 1

    # --- cumulative block: the same clauses over a morsel that already carries
    # a record (this is where Old(...) is not trivial) ------------------------
    for key in ("c", "__Host-c", "sessionid", "__Secure-x"):
        for pre in pres[1:]:
            for pol in (None, "", "lax", "none", "Strict"):
                for path in (None, "", "/", "/example/"):
                    for dom in (None, "", ".example.com"):
                        for sec in (True, False):
                            check_set_cookie_axiom(HttpResponse, key, path, dom,
                                                   sec, pol, pre=pre)
                            n_axiom += 1
                        check_delete_cookie_reference(HttpResponse, key, path,
                                                      dom, pol, pre=pre)
                        n_ref += 1

    # --- fuzz: random reach + valid samesite values + prefixed/plain names --
    rng = random.Random(13195)
    prefixes = ["", "__Secure-", "__Host-", "__secure-", "__host-", "x"]
    bodies = ["c", "messages", "id", "ab12", "z"]
    frag = ["/", "a", "b/", "-", ".", "é", " ", "example"]
    for _ in range(4000):
        key = rng.choice(prefixes) + rng.choice(bodies)
        pol = rng.choice(policies)
        sec = rng.choice((True, False))
        pre = rng.choice(pres)
        path = rng.choice([None, "", "/",
                           "/" + "".join(rng.choice(frag)
                                         for _ in range(rng.randint(0, 3)))])
        dom = rng.choice([None, "", "." + "".join(rng.choice(frag)
                                                  for _ in range(2))])
        check_set_cookie_axiom(HttpResponse, key, path, dom, sec, pol, pre=pre)
        check_delete_cookie_reference(HttpResponse, key, path, dom, pol,
                                      omit_path=rng.random() < 0.25, pre=pre)
        n_axiom += 1
        n_ref += 1

    print("G-AX OK: name domain (is_storable_name == 'the real setter/expiry "
          "records a cookie under this name') exact on %d names; reach values "
          "unrestricted and recorded verbatim on %d probes; store_cookie axiom "
          "(== set_cookie as the expiry invokes it, cumulative clauses measured "
          "over pre-existing records) sound on %d cases; deep model "
          "(expiry_secure + forwarding + reach == real delete_cookie) sound on "
          "%d cases." % (n_domain, n_reach, n_axiom, n_ref))
    return 0


if __name__ == "__main__":
    sys.exit(main())
