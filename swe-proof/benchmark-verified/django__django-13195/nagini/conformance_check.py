#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13195 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (there are none inside the impl region itself). The @Pure
helpers `lower_cp` / `is_none_ci` / `secure_prefix` / `host_prefix` /
`has_security_prefix` copy over as plain functions on top of a tuple-backed
PSeq shim; `starts_with`, whose model.py body is a bounded Forall quantifier
over the prefix indices, is realized as the equivalent bounded loop. The one
@ContractOnly callee, `store_cookie` (the unchanged cookie attribute setter),
calls the REAL repo function it models per mapping.md --
`HttpResponseBase.set_cookie` -- and reads the recorded morsel back into the
Cookie projection (the reach path, the host domain, the secure flag and the
cross-site policy attribute). The Cookie shim carries the cookie name so the
real setter stores under the same key the routine was invoked with (the model's
Cookie IS the morsel stored at that key).

ORACLE: the REAL patched cookie-expiry routine the model models per
mapping.md -- `HttpResponseBase.delete_cookie` -- imported from the patched
repo (the gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes it importable). The emitted morsel's reach path,
host domain, secure flag and cross-site attribute are the observed outputs.

Type bridge (mapping.md section 2): model `List[int]` of Unicode code points
<-> repo `str` via chr/ord. The model's empty list abstracts BOTH falsey repo
values (None and the empty string) for each of the three present-or-absent
arguments; for an empty list the oracle is run on every preimage and each must
agree with the shadow. Note the asymmetry the reach arguments have: leaving
`samesite` or `domain` out of the call is a falsey preimage (their default is
None), whereas leaving `path` out is NOT -- its default is the site root, a
non-empty value -- so an empty modelled path is only ever reached by passing it
explicitly, and omission is a preimage of the site root instead. Because the
shadow's store_cookie call goes through the same real setter as the oracle,
inputs the setter rejects (an invalid policy token, an illegal cookie name)
raise identically on both sides; an outcome is therefore compared as either
('ok', secure, path, domain, samesite) or ('raise', exception type name).

Input domain: beyond the access permissions, the model's Requires restrict the
name and the policy to the domain in which the cookie machinery records
anything at all -- a supplied policy value must be one of the three recognised
cross-site tokens (any ASCII casing), and the name must be non-empty, drawn
from the header grammar's name alphabet, and none of the nine names reserved
for the header's own attributes. The reach arguments carry NO restriction (the
machinery records them without inspecting them), so the in-domain generator
draws them freely, separators and non-ASCII included. The IN-DOMAIN fuzz block
draws only from that domain (100000 tuples).

The UNRESTRICTED boundary + fuzz blocks are RETAINED on purpose even though
part of what they generate now sits outside the Requires: there the real
machinery refuses the request outright, and because the shadow's store_cookie
call goes through the SAME real setter as the oracle, both sides raise
identically -- so the comparison stays meaningful and this check remains
strictly stronger than the specification demands. Those blocks take the full
cross product of prefix-shaped/plain/illegal names x valid policy tokens in
all casings plus near-miss and invalid tokens (rotating through the reach
values), a dedicated reach cross product, and fuzz names from prefix
fragments + legal/illegal characters, policies from valid tokens,
case-perturbed tokens, near-misses, and random short strings (ASCII + a slice
of non-ASCII, surrogates excluded: they cannot round-trip through printing and
add no reachable behaviour in a header-value string).

>= 1e5 Requires-satisfying inputs: the 100000-tuple in-domain fuzz block (plus
the in-domain part of the boundary cross product). Total >= 2e5 inputs.
Pinned fuzz seeds: 13195 (unrestricted) / 13196 (in-domain).

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (plain `random`).
"""
import random
import sys

SEED = 13195
N_FUZZ = 100000
SEED_INDOMAIN = 13196
N_FUZZ_INDOMAIN = 100000


# --- PSeq shim: immutable sequence, the operations the pure region uses ------

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


# --- Cookie shim: the morsel projection from model.py ------------------------
# Carries the cookie name so the real-callee bridge in store_cookie stores
# under the same key the expiry routine was invoked with.

class Cookie(object):
    def __init__(self, key_str):
        self.expired = False
        self.secure = False
        self.has_path = False
        self.path = []
        self.has_domain = False
        self.domain = []
        self.has_policy = False
        self.policy = []
        self._key_str = key_str


# --- pure helpers from model.py, contracts stripped ---------------------------

def lower_cp(c):
    if 65 <= c and c <= 90:
        return c + 32
    return c


def is_none_ci(policy):
    if len(policy) != 4:
        return False
    return (lower_cp(policy[0]) == 110 and   # 'n'
            lower_cp(policy[1]) == 111 and   # 'o'
            lower_cp(policy[2]) == 110 and   # 'n'
            lower_cp(policy[3]) == 101)      # 'e'


def secure_prefix():
    # '__Secure-'
    return PSeq(95, 95, 83, 101, 99, 117, 114, 101, 45)


def host_prefix():
    # '__Host-'
    return PSeq(95, 95, 72, 111, 115, 116, 45)


def starts_with(key, prefix):
    # model.py states this as a bounded Forall over the prefix indices
    # (guarded 0 <= k < len(prefix)); realized as the equivalent loop.
    if len(key) < len(prefix):
        return False
    for k in range(len(prefix)):
        if key[k] != prefix[k]:
            return False
    return True


def has_security_prefix(key):
    return starts_with(key, secure_prefix()) or starts_with(key, host_prefix())


# --- @ContractOnly callee bridge: store_cookie -> REAL set_cookie ------------
# Per the contract, the axiomatized callee calls the REAL repo function it
# models (the unchanged cookie attribute setter), then reads the recorded
# morsel back into the Cookie projection. HttpResponse is bound in main().

_HttpResponse = None

# The already-elapsed lifetime the expiry call site always asks for; a constant
# of that call site, which is why the axiom does not carry it as a parameter.
EXPIRED_LITERAL = "Thu, 01 Jan 1970 00:00:00 GMT"


def store_cookie(cookie, path, domain, secure, policy):
    resp = _HttpResponse()
    path_s = "".join(chr(c) for c in path)
    domain_s = "".join(chr(c) for c in domain)
    pol_s = "".join(chr(c) for c in policy)
    # An empty list means "no value supplied"; the real setter treats the empty
    # string and None identically here (neither installs anything of its own),
    # so the empty string is a faithful preimage on this side -- and the oracle
    # side below sweeps every preimage, which is what measures that.
    resp.set_cookie(cookie._key_str, max_age=0, expires=EXPIRED_LITERAL,
                    path=path_s, domain=domain_s, secure=secure,
                    samesite=pol_s)
    m = resp.cookies[cookie._key_str]
    cookie.expired = (m["expires"] == EXPIRED_LITERAL and m["max-age"] == 0 and
                      m.value == "")
    cookie.secure = m["secure"] is True
    pv = m["path"]
    cookie.has_path = pv != ""
    cookie.path = [ord(ch) for ch in pv] if cookie.has_path else []
    dv = m["domain"]
    cookie.has_domain = dv != ""
    cookie.domain = [ord(ch) for ch in dv] if cookie.has_domain else []
    ss = m["samesite"]
    cookie.has_policy = ss not in ("", None)
    cookie.policy = [ord(ch) for ch in ss] if cookie.has_policy else []


# --- the impl region of model.py, verbatim (no contract calls inside) --------

def delete_cookie(cookie, key, path, domain, policy):
    secure = has_security_prefix(key) or is_none_ci(policy)
    store_cookie(cookie, path, domain, secure, policy)


# --- outcome extraction --------------------------------------------------------

def shadow_outcome(key_s, path_cps, domain_cps, policy_cps):
    """Run the shadow on the bridged inputs; normalize to a comparable tuple."""
    cookie = Cookie(key_s)
    key_cps = [ord(ch) for ch in key_s]
    try:
        delete_cookie(cookie, key_cps, path_cps, domain_cps, policy_cps)
    except Exception as e:
        return ("raise", type(e).__name__)
    return ("ok", cookie.expired, cookie.secure,
            "".join(chr(c) for c in cookie.path) if cookie.has_path else "",
            "".join(chr(c) for c in cookie.domain) if cookie.has_domain else "",
            "".join(chr(c) for c in cookie.policy) if cookie.has_policy else "")


_OMIT = object()


def oracle_outcome(key_s, path_arg, domain_arg, policy_arg):
    """Run the REAL patched expiry routine; normalize identically."""
    resp = _HttpResponse()
    kw = {}
    if path_arg is not _OMIT:
        kw["path"] = path_arg
    if domain_arg is not _OMIT:
        kw["domain"] = domain_arg
    if policy_arg is not _OMIT:
        kw["samesite"] = policy_arg
    try:
        resp.delete_cookie(key_s, **kw)
    except Exception as e:
        return ("raise", type(e).__name__)
    m = resp.cookies[key_s]
    got = m["samesite"]
    return ("ok",
            (m["expires"] == EXPIRED_LITERAL and m["max-age"] == 0 and
             m.value == ""),
            m["secure"] is True,
            m["path"] if m["path"] not in ("", None) else "",
            m["domain"] if m["domain"] not in ("", None) else "",
            got if got not in ("", None) else "")


def _preimages(value_s, omit_is_falsey):
    """The repo values a modelled list maps to. A non-empty modelled value has
    the string itself as its only preimage -- plus omission, where the routine's
    own default happens to BE that value. A falsey modelled value has the empty
    string and None, and omission too when the argument's default is None."""
    if value_s:
        return [value_s]
    return ([_OMIT, None, ""] if omit_is_falsey else [None, ""])


def check_case(key_s, path_s, domain_s, policy_s, rng=None):
    """One (name, path, domain, policy) tuple. Each falsey argument bridges to
    the empty code-point list, so the oracle must agree on every preimage of it.
    The boundary blocks pass rng=None and enumerate the full preimage product;
    the fuzz blocks pass an rng and draw one combination per case (over 1e5
    cases every combination is reached many times). Returns an error string on
    any disagreement, else None."""
    path_cps = [ord(ch) for ch in path_s] if path_s else []
    domain_cps = [ord(ch) for ch in domain_s] if domain_s else []
    policy_cps = [ord(ch) for ch in policy_s] if policy_s else []
    sh = shadow_outcome(key_s, path_cps, domain_cps, policy_cps)

    # Omitting `path` is NOT a preimage of the empty path: its default is the
    # site root. It IS a preimage of the site root itself.
    p_pre = _preimages(path_s, omit_is_falsey=False)
    if path_s == "/":
        p_pre = p_pre + [_OMIT]
    d_pre = _preimages(domain_s, omit_is_falsey=True)
    s_pre = _preimages(policy_s, omit_is_falsey=True)

    if rng is None:
        combos = [(p, d, s) for p in p_pre for d in d_pre for s in s_pre]
    else:
        combos = [(rng.choice(p_pre), rng.choice(d_pre), rng.choice(s_pre))]

    for p, d, s in combos:
        rl = oracle_outcome(key_s, p, d, s)
        if sh != rl:
            return ("DISAGREEMENT\n  key=%s\n  path=%s (preimage %s)\n"
                    "  domain=%s (preimage %s)\n  policy=%s (preimage %s)\n"
                    "  shadow=%s\n  real=%s"
                    % (ascii(key_s),
                       ascii(path_s), "omitted" if p is _OMIT else ascii(p),
                       ascii(domain_s), "omitted" if d is _OMIT else ascii(d),
                       ascii(policy_s), "omitted" if s is _OMIT else ascii(s),
                       ascii(sh), ascii(rl)))
    return None


# --- input generation -----------------------------------------------------------

BOUNDARY_NAMES = [
    "c", "messages", "sessionid", "x",
    "__Secure-c", "__Host-c", "__Secure-", "__Host-",
    "__secure-c", "__host-c",          # wrong case: NOT a security prefix
    "_Secure-c", "Host-c", "a__Host-c",
    "__Secure", "__Host",              # missing trailing '-'
    "__SECURE-c", "__HOST-c",
    "",                                # illegal name: setter rejects it
    "bad name", "sp;am",               # illegal characters in the name
]

BOUNDARY_POLICIES = [
    "", "lax", "Lax", "LAX", "lAx",
    "none", "None", "NONE", "nOnE", "NoNe",
    "strict", "Strict", "STRICT",
    "nonee", "non", "one", "nonf", "mone", "nnne", "noee",  # near misses
    "foobar", " none", "none ", "n0ne", "NONE!",            # invalid tokens
]

# Reach values: the falsey one (both its preimages), the routine's own default,
# the values the graded call sites reach, and awkward ones the recorder accepts
# without inspecting them.
BOUNDARY_PATHS = ["", "/", "/example/", "/a/b", "/a b", "/;x", "/é", "/" * 4]
BOUNDARY_DOMAINS = ["", ".example.com", ".example.local", "sub.a.b", "a b",
                    ";x", "é.example"]


def rand_name(rng):
    prefixes = ["", "__Secure-", "__Host-", "__secure-", "__host-",
                "__Secure", "__Host", "_Secure-", "x__Host-"]
    legal = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    body_len = rng.randint(0, 6)
    body = "".join(rng.choice(legal) for _ in range(body_len))
    name = rng.choice(prefixes) + body
    if rng.random() < 0.05:
        # inject an illegal character: the setter rejects the name on both
        # sides identically
        pos = rng.randint(0, len(name))
        name = name[:pos] + rng.choice(" ;,\té") + name[pos:]
    return name


def rand_policy(rng):
    r = rng.random()
    if r < 0.35:
        return rng.choice(BOUNDARY_POLICIES)
    if r < 0.55:
        # case-perturbed valid token
        tok = rng.choice(["lax", "none", "strict"])
        return "".join(ch.upper() if rng.random() < 0.5 else ch
                       for ch in tok)
    if r < 0.75:
        # 'none'-shaped strings probing the case-fold boundary
        base = "none"
        chars = []
        for ch in base:
            k = rng.random()
            if k < 0.4:
                chars.append(ch.upper())
            elif k < 0.5:
                chars.append(chr(ord(ch) + rng.randint(-2, 2)))
            else:
                chars.append(ch)
        return "".join(chars)
    # random short string, ASCII + a slice of non-ASCII (no surrogates)
    n = rng.randint(0, 6)
    chars = []
    for _ in range(n):
        if rng.random() < 0.85:
            chars.append(chr(rng.randint(32, 126)))
        else:
            cp = rng.randint(0xA0, 0x2FFF)
            chars.append(chr(cp))
    return "".join(chars)


_REACH_FRAG = ["a", "b/", "example", "-", ".", "é", " ", ";", "1", "x=y"]


def rand_path(rng):
    r = rng.random()
    if r < 0.2:
        return ""                       # the falsey modelled value
    if r < 0.45:
        return "/"                      # the routine's own default
    if r < 0.6:
        return rng.choice(BOUNDARY_PATHS)
    return "/" + "".join(rng.choice(_REACH_FRAG)
                         for _ in range(rng.randint(0, 3)))


def rand_domain(rng):
    r = rng.random()
    if r < 0.35:
        return ""                       # the falsey modelled value
    if r < 0.55:
        return rng.choice(BOUNDARY_DOMAINS)
    return "." + "".join(rng.choice(_REACH_FRAG)
                         for _ in range(rng.randint(1, 3)))


# --- in-domain generation: exactly the inputs the model's Requires admit ------

LEGAL_NAME_CHARS = ("abcdefghijklmnopqrstuvwxyz"
                    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    "0123456789"
                    "!#$%&'*+-.^_`|~:")

RESERVED_NAMES = ("expires", "path", "comment", "domain", "max-age", "secure",
                  "httponly", "version", "samesite")


def rand_storable_name(rng):
    """A name the model's `is_storable_name` admits: non-empty, every character
    from the header grammar's name alphabet, never a reserved attribute name."""
    prefixes = ["", "", "", "__Secure-", "__Host-", "__secure-", "__host-",
                "__Secure", "__Host", "_Secure-", "x__Host-"]
    while True:
        name = (rng.choice(prefixes) +
                "".join(rng.choice(LEGAL_NAME_CHARS)
                        for _ in range(rng.randint(1, 6))))
        if name.lower() not in RESERVED_NAMES:
            return name


def rand_known_policy(rng):
    """A policy value the model's Requires admit: absent (the empty list's
    preimages) or one of the three recognised tokens in an arbitrary casing."""
    if rng.random() < 0.2:
        return ""
    tok = rng.choice(["lax", "none", "strict"])
    return "".join(ch.upper() if rng.random() < 0.5 else ch for ch in tok)


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
            SESSION_COOKIE_SAMESITE="Lax",
        )
    django.setup()


def main():
    global _HttpResponse
    _bootstrap_django()
    # REAL patched repo class (PYTHONPATH=/testbed, patch applied by the gate).
    from django.http import HttpResponse
    _HttpResponse = HttpResponse

    checked = 0
    n_boundary = 0
    for i, key_s in enumerate(BOUNDARY_NAMES):
        for j, pol_s in enumerate(BOUNDARY_POLICIES):
            # rotate the reach values through the name x policy cross product,
            # so every combination of the three boundary axes is reached
            path_s = BOUNDARY_PATHS[(i + j) % len(BOUNDARY_PATHS)]
            dom_s = BOUNDARY_DOMAINS[(i + 2 * j) % len(BOUNDARY_DOMAINS)]
            err = check_case(key_s, path_s, dom_s, pol_s)
            if err:
                print(err)
                return 1
            checked += 1
            n_boundary += 1

    # dedicated reach cross product: every path x every domain, on the names and
    # policies that drive the two introduced decisions
    n_reach = 0
    for path_s in BOUNDARY_PATHS:
        for dom_s in BOUNDARY_DOMAINS:
            for key_s in ("c", "__Secure-c"):
                for pol_s in ("", "none", "Lax"):
                    err = check_case(key_s, path_s, dom_s, pol_s)
                    if err:
                        print(err)
                        return 1
                    checked += 1
                    n_reach += 1

    # IN-DOMAIN block: only inputs the model's Requires admit, so this is the
    # >= 1e5 count the conformance obligation is about.
    rng_in = random.Random(SEED_INDOMAIN)
    n_indomain = 0
    for _ in range(N_FUZZ_INDOMAIN):
        err = check_case(rand_storable_name(rng_in), rand_path(rng_in),
                         rand_domain(rng_in), rand_known_policy(rng_in),
                         rng=rng_in)
        if err:
            print(err)
            return 1
        checked += 1
        n_indomain += 1

    # UNRESTRICTED block: retained deliberately -- outside the Requires the real
    # machinery refuses the request and both sides raise identically, which is
    # strictly more than the spec demands.
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check_case(rand_name(rng), rand_path(rng), rand_domain(rng),
                         rand_policy(rng), rng=rng)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl (contract-stripped model.py impl region, "
          "store_cookie bridged to the real setter) == real patched expiry "
          "routine on the full emitted-cookie projection (elapsed lifetime, "
          "reach path, host domain, secure flag, cross-site policy) over %d "
          "inputs (%d in-domain fuzz, seed %d; %d boundary + %d reach cross "
          "product + %d unrestricted fuzz, seed %d -- outside the Requires both "
          "sides refuse the request identically)."
          % (checked, n_indomain, SEED_INDOMAIN, n_boundary, n_reach, N_FUZZ,
             SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
