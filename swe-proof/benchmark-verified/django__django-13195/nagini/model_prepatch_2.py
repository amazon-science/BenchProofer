"""Twin-artifact model for django__django-13195.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Expiring a cookie in an HTTP response must carry the same cross-site policy
  attribute that the live cookie carried, so a browser that would otherwise
  reject the expiry header still honours it. The expiry routine therefore
  accepts an explicit cross-site policy value and:

    (1) forwards that policy value onto the emitted expiry cookie verbatim:
        if a non-empty policy value is supplied the emitted cookie carries
        exactly that value as its cross-site attribute; otherwise the cookie
        carries no cross-site attribute; and

    (2) marks the emitted expiry cookie as transport-secure when EITHER the
        cookie name uses one of the two reserved security-prefix forms
        ("__Secure-" / "__Host-") OR the supplied cross-site policy value is
        the unrestricted policy "none" (compared case-insensitively). Browsers
        ignore an unrestricted-policy cookie that is not transport-secure, so
        without this the expiry header would be dropped.

  When no (non-empty) policy value is supplied and the name carries no security
  prefix, the emitted cookie is NOT marked transport-secure and carries no
  cross-site attribute (the pre-existing default expiry behaviour is preserved).

  Both additions ride ALONGSIDE the pre-existing expiry behaviour rather than
  replacing it, and that pre-existing behaviour is what makes the emitted cookie
  an expiry a browser will act on at all. All of it is stated here:

    (a) the emitted cookie always carries the already-elapsed lifetime that
        tells the browser to drop it at once; and

    (b) the emitted cookie is delivered for exactly the REACH the expiry was
        asked for — the request path it applies to, and the host it belongs to.
        A browser drops a live cookie only when the expiry it receives reaches
        the same way, so an expiry that reached differently (or reached nowhere,
        carrying no path of its own) would leave the live cookie in place no
        matter which attributes it carried. The routine is asked for a reach on
        every call: it applies to the site root unless the caller names a
        narrower path, and it is host-wide unless the caller names a domain.

  Each of the four attributes the emitted cookie carries is set on its stated
  ground ONLY. The cookie machinery records them cumulatively — it has a set
  branch but no clearing branch, and it writes into whatever record the cookie
  of that name already carries — so an attribute switched on for any other
  reason could never be taken back off, and an expiry that switched one on
  spuriously would emit a cookie permanently carrying it.

  A supplied policy value is one the machinery recognises; it refuses any other
  value outright rather than recording it. It is equally particular about the
  cookie NAME: a cookie is recorded only under a non-empty name drawn from the
  name alphabet the header grammar allows, and never under one of the names the
  machinery reserves for the header's own attributes ("expires", "path",
  "comment", "domain", "max-age", "secure", "httponly", "version", "samesite").
  A name outside that domain is refused outright: no cookie of any kind is
  recorded and the expiry raises instead of returning, so there is no emitted
  expiry cookie there to carry any attribute. The path and the domain are values
  the machinery records without inspecting them, so they are unrestricted.

The cookie name, the path, the domain and the policy value are character
strings, modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). An absent / falsey value (the real ``None`` or the empty string) is
modelled as the empty list: for each of these three attributes the two real
values are observationally identical on the emitted cookie — neither is carried
and neither is the "none" policy. The emitted cookie is a minimal object
exposing exactly the attributes it carries: a boolean transport-secure flag, the
already-elapsed lifetime, and the path / domain / cross-site policy values
(present-or-absent). The attribute-store primitive the expiry routine builds on
(the unchanged cookie setter) is axiomatized as `store_cookie`; it is validated
against its real behaviour out-of-band by axiom_check.py (G-AX). The two
decisions the change introduces — forwarding the policy value and deriving the
secure flag from the "none" policy — are modelled DEEPLY (spelled-out predicates
over the code-point strings), never behind an axiom about the operation that
changed.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Cookie:
    """The emitted cookie morsel, exposing the attributes it carries.

    `secure` is the transport-secure flag. `has_policy` records whether a
    cross-site policy attribute is present at all, and `policy` is its value
    (the code-point string) when present. `has_path` / `path` and `has_domain` /
    `domain` record the reach of the emitted cookie the same way: the request
    path it applies to and the host it belongs to, present-or-absent. `expired`
    records whether the cookie carries the already-elapsed lifetime that tells a
    browser to drop it at once — the whole point of an expiry cookie, and the
    thing that distinguishes it from an ordinary live cookie carrying the same
    attributes.
    """

    def __init__(self) -> None:
        # The morsel constructor is a straight-line field initialiser: it
        # terminates, and it must SAY so, or no obligated caller can build one.
        Requires(MustTerminate(2))
        Ensures(Acc(self.secure))                       # type: ignore
        Ensures(Acc(self.has_policy))                   # type: ignore
        Ensures(Acc(self.policy) and Acc(list_pred(self.policy)))  # type: ignore
        Ensures(Acc(self.expired))                      # type: ignore
        Ensures(Acc(self.has_path))                     # type: ignore
        Ensures(Acc(self.path) and Acc(list_pred(self.path)))      # type: ignore
        Ensures(Acc(self.has_domain))                   # type: ignore
        Ensures(Acc(self.domain) and Acc(list_pred(self.domain)))  # type: ignore
        Ensures(self.secure is False)                   # type: ignore
        Ensures(self.has_policy is False)               # type: ignore
        Ensures(len(self.policy) == 0)                  # type: ignore
        Ensures(self.expired is False)                  # type: ignore
        Ensures(self.has_path is False)                 # type: ignore
        Ensures(len(self.path) == 0)                    # type: ignore
        Ensures(self.has_domain is False)               # type: ignore
        Ensures(len(self.domain) == 0)                  # type: ignore
        self.secure = False         # type: bool
        self.has_policy = False     # type: bool
        self.policy = []            # type: List[int]
        self.expired = False        # type: bool
        self.has_path = False       # type: bool
        self.path = []              # type: List[int]
        self.has_domain = False     # type: bool
        self.domain = []            # type: List[int]


# axioms-start
@ContractOnly
def store_cookie(cookie: Cookie, path: List[int], domain: List[int],
                 secure: bool, policy: List[int]) -> None:
    """The unchanged cookie attribute setter, as the expiry routine invokes it
    (after computing the two values, and always with the already-elapsed
    lifetime an expiry carries — that lifetime is a constant of this call site,
    unchanged by the behaviour under specification, which is why it is not a
    parameter here).

    Weakest contract the proof needs about the unchanged setter. It records the
    attributes CUMULATIVELY rather than by overwriting, because it has only a
    set branch and no clearing branch, and it writes into whatever record the
    cookie of that name already has: a request to mark the cookie
    transport-secure turns that flag on and nothing turns it off; a non-empty
    path, domain or policy value replaces that attribute while an empty one
    installs nothing of its own. It also refuses a policy value it does not
    recognise instead of recording it, so its domain admits only recognised
    values; the path and the domain it records without inspecting them.

    The name the cookie is recorded under is not a parameter here — the Cookie
    IS the record held under that name — and the setter likewise refuses a name
    it records nothing under. The caller's precondition confines the name to the
    recorded domain (`is_storable_name`), so every invocation this contract
    speaks about is one the setter accepts.
    Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX).
    """
    Requires(Acc(cookie.secure) and Acc(cookie.has_policy))
    Requires(Acc(cookie.policy) and Acc(list_pred(cookie.policy)))
    Requires(Acc(cookie.expired))
    Requires(Acc(cookie.has_path))
    Requires(Acc(cookie.path) and Acc(list_pred(cookie.path)))
    Requires(Acc(cookie.has_domain))
    Requires(Acc(cookie.domain) and Acc(list_pred(cookie.domain)))
    Requires(Acc(list_pred(path), 1 / 2))
    Requires(Acc(list_pred(domain), 1 / 2))
    Requires(Acc(list_pred(policy), 1 / 2))
    # The setter only accepts the recognised cross-site policy tokens: handed a
    # value it does not recognise it rejects the request outright rather than
    # recording anything, so a caller may only offer a recognised value (or none
    # at all).
    Requires(Implies(len(policy) > 0, is_known_policy(policy)))
    Requires(MustTerminate(6))
    Ensures(Acc(cookie.secure) and Acc(cookie.has_policy))
    Ensures(Acc(cookie.policy) and Acc(list_pred(cookie.policy)))
    Ensures(Acc(cookie.expired))
    Ensures(Acc(cookie.has_path))
    Ensures(Acc(cookie.path) and Acc(list_pred(cookie.path)))
    Ensures(Acc(cookie.has_domain))
    Ensures(Acc(cookie.domain) and Acc(list_pred(cookie.domain)))
    Ensures(Acc(list_pred(path), 1 / 2))
    Ensures(Acc(list_pred(domain), 1 / 2))
    Ensures(Acc(list_pred(policy), 1 / 2))
    # Storing through this setter is what stamps the already-elapsed lifetime
    # onto the cookie, so a cookie stored through it always carries it.
    Ensures(cookie.expired)
    # The read-only values are returned untouched.
    Ensures(ToSeq(path) == Old(ToSeq(path)))
    Ensures(ToSeq(domain) == Old(ToSeq(domain)))
    Ensures(ToSeq(policy) == Old(ToSeq(policy)))
    # The transport-secure flag ACCUMULATES: a request to mark the cookie
    # transport-secure turns the flag on, and no request turns it off again.
    Ensures(cookie.secure == (Old(cookie.secure) or secure))
    # A non-empty path value installs itself verbatim as the reach of the stored
    # cookie.
    Ensures(Implies(len(path) > 0, cookie.has_path))
    Ensures(Implies(len(path) > 0, ToSeq(cookie.path) == ToSeq(path)))
    # Handed no path value, the setter installs none of its own: any path the
    # stored cookie carries afterwards is one it already carried, unchanged.
    # (This is the weakest statement true of BOTH falsey values: the absent one
    # leaves the recorded path alone, the empty one leaves the cookie carrying
    # no path at all — see mapping.md.)
    Ensures(Implies(len(path) == 0,
                    Implies(cookie.has_path,
                            Old(cookie.has_path) and
                            ToSeq(cookie.path) == Old(ToSeq(cookie.path)))))
    # The host the stored cookie belongs to is recorded the same way.
    Ensures(Implies(len(domain) > 0, cookie.has_domain))
    Ensures(Implies(len(domain) > 0, ToSeq(cookie.domain) == ToSeq(domain)))
    Ensures(Implies(len(domain) == 0,
                    Implies(cookie.has_domain,
                            Old(cookie.has_domain) and
                            ToSeq(cookie.domain) == Old(ToSeq(cookie.domain)))))
    # A non-empty cross-site policy value installs itself verbatim as the
    # cookie's policy attribute; an empty one changes nothing at all, so a
    # policy attribute the cookie already carries also survives.
    Ensures(cookie.has_policy == (Old(cookie.has_policy) or len(policy) > 0))
    Ensures(Implies(len(policy) > 0, ToSeq(cookie.policy) == ToSeq(policy)))
    Ensures(Implies(len(policy) == 0,
                    ToSeq(cookie.policy) == Old(ToSeq(cookie.policy))))
# axioms-end


# pure-start
@Pure
def lower_cp(c: int) -> int:
    """Lower-case a single code point under ASCII case folding (the only
    folding that can make a value equal the literal "none")."""
    if 65 <= c and c <= 90:
        return c + 32
    return c


@Pure
def is_none_ci(policy: List[int]) -> bool:
    Requires(Acc(list_pred(policy), 1 / 4))
    """The cross-site policy value is the unrestricted policy, compared
    case-insensitively: it is exactly four code points spelling n,o,n,e under
    ASCII case folding ("none", "NONE", "None", ...)."""
    if len(policy) != 4:
        return False
    return (lower_cp(policy[0]) == 110 and   # 'n'
            lower_cp(policy[1]) == 111 and   # 'o'
            lower_cp(policy[2]) == 110 and   # 'n'
            lower_cp(policy[3]) == 101)      # 'e'


@Pure
def is_relaxed_ci(policy: List[int]) -> bool:
    Requires(Acc(list_pred(policy), 1 / 4))
    """The cross-site policy value is the relaxed policy, compared
    case-insensitively: exactly three code points spelling l,a,x under ASCII
    case folding."""
    if len(policy) != 3:
        return False
    return (lower_cp(policy[0]) == 108 and   # 'l'
            lower_cp(policy[1]) == 97 and    # 'a'
            lower_cp(policy[2]) == 120)      # 'x'


@Pure
def is_restrictive_ci(policy: List[int]) -> bool:
    Requires(Acc(list_pred(policy), 1 / 4))
    """The cross-site policy value is the restrictive policy, compared
    case-insensitively: exactly six code points spelling s,t,r,i,c,t under ASCII
    case folding."""
    if len(policy) != 6:
        return False
    return (lower_cp(policy[0]) == 115 and   # 's'
            lower_cp(policy[1]) == 116 and   # 't'
            lower_cp(policy[2]) == 114 and   # 'r'
            lower_cp(policy[3]) == 105 and   # 'i'
            lower_cp(policy[4]) == 99 and    # 'c'
            lower_cp(policy[5]) == 116)      # 't'


@Pure
def is_known_policy(policy: List[int]) -> bool:
    Requires(Acc(list_pred(policy), 1 / 4))
    """Whether the cross-site policy value is one the cookie machinery
    recognises: the unrestricted, the relaxed, or the restrictive policy, in any
    ASCII casing. A value outside this set is not a cross-site policy at all and
    is refused rather than recorded."""
    return (is_none_ci(policy) or is_relaxed_ci(policy) or
            is_restrictive_ci(policy))


@Pure
def secure_prefix() -> PSeq[int]:
    # '__Secure-'
    return PSeq(95, 95, 83, 101, 99, 117, 114, 101, 45)


@Pure
def host_prefix() -> PSeq[int]:
    # '__Host-'
    return PSeq(95, 95, 72, 111, 115, 116, 45)


@Pure
def starts_with(key: List[int], prefix: PSeq[int]) -> bool:
    Requires(Acc(list_pred(key), 1 / 4))
    """Whether the code-point string `key` begins with the literal `prefix`."""
    return (len(key) >= len(prefix) and
            Forall(int, lambda k: (Implies(0 <= k and k < len(prefix),
                                           ToSeq(key)[k] == prefix[k]),
                                   [[ToSeq(key)[k]]])))


@Pure
def has_security_prefix(key: List[int]) -> bool:
    Requires(Acc(list_pred(key), 1 / 4))
    """Whether the cookie name begins with one of the two reserved
    security-prefix forms "__Secure-" or "__Host-"."""
    return starts_with(key, secure_prefix()) or starts_with(key, host_prefix())


@Pure
def is_name_char(c: int) -> bool:
    """Whether a single code point may appear in a cookie name: a digit, an
    ASCII letter, or one of the punctuation marks the header grammar permits
    (! # $ % & ' * + - . : ^ _ ` | ~). Everything else — a space, a separator
    such as ';' ',' '=' '"', or any non-ASCII code point — makes the name one
    the cookie machinery will not record under."""
    return ((48 <= c and c <= 57) or        # 0-9
            (65 <= c and c <= 90) or        # A-Z
            (97 <= c and c <= 122) or       # a-z
            c == 33 or                      # !
            c == 35 or                      # #
            c == 36 or                      # $
            c == 37 or                      # %
            c == 38 or                      # &
            c == 39 or                      # '
            c == 42 or                      # *
            c == 43 or                      # +
            c == 45 or                      # -
            c == 46 or                      # .
            c == 58 or                      # :
            c == 94 or                      # ^
            c == 95 or                      # _
            c == 96 or                      # `
            c == 124 or                     # |
            c == 126)                       # ~


@Pure
def all_name_chars(key: List[int]) -> bool:
    Requires(Acc(list_pred(key), 1 / 4))
    """Whether every code point of the cookie name is one a name may contain."""
    return Forall(int, lambda k: (Implies(0 <= k and k < len(key),
                                          is_name_char(ToSeq(key)[k])),
                                  [[ToSeq(key)[k]]]))


@Pure
def equals_ci(key: List[int], word: PSeq[int]) -> bool:
    Requires(Acc(list_pred(key), 1 / 4))
    """Whether the cookie name is the literal lower-case `word`, compared under
    ASCII case folding (the folding the machinery applies before checking a name
    against the names it reserves)."""
    return (len(key) == len(word) and
            Forall(int, lambda k: (Implies(0 <= k and k < len(word),
                                           lower_cp(ToSeq(key)[k]) == word[k]),
                                   [[ToSeq(key)[k]]])))


@Pure
def is_reserved_name(key: List[int]) -> bool:
    Requires(Acc(list_pred(key), 1 / 4))
    """Whether the cookie name is one of the names the cookie machinery keeps
    for the header's own attributes, in any ASCII casing. Such a name never
    names a cookie: asked to record one, the machinery refuses outright."""
    return (equals_ci(key, PSeq(101, 120, 112, 105, 114, 101, 115)) or
            # 'expires'
            equals_ci(key, PSeq(112, 97, 116, 104)) or
            # 'path'
            equals_ci(key, PSeq(99, 111, 109, 109, 101, 110, 116)) or
            # 'comment'
            equals_ci(key, PSeq(100, 111, 109, 97, 105, 110)) or
            # 'domain'
            equals_ci(key, PSeq(109, 97, 120, 45, 97, 103, 101)) or
            # 'max-age'
            equals_ci(key, PSeq(115, 101, 99, 117, 114, 101)) or
            # 'secure'
            equals_ci(key, PSeq(104, 116, 116, 112, 111, 110, 108, 121)) or
            # 'httponly'
            equals_ci(key, PSeq(118, 101, 114, 115, 105, 111, 110)) or
            # 'version'
            equals_ci(key, PSeq(115, 97, 109, 101, 115, 105, 116, 101)))
            # 'samesite'


@Pure
def is_storable_name(key: List[int]) -> bool:
    Requires(Acc(list_pred(key), 1 / 4))
    """Whether the cookie machinery records a cookie under this name at all: the
    name is non-empty, every code point is one a name may contain, and it is not
    one of the names reserved for the header's own attributes. Every other name
    is refused outright — no cookie is recorded under it, and an expiry asked to
    use one raises instead of returning."""
    return len(key) > 0 and all_name_chars(key) and not is_reserved_name(key)


@Pure
def expiry_secure(key: List[int], policy: List[int]) -> bool:
    Requires(Acc(list_pred(key), 1 / 4))
    Requires(Acc(list_pred(policy), 1 / 4))
    """The transport-secure decision for an expiry cookie: secure iff the name
    carries a reserved security prefix OR the cross-site policy is the
    unrestricted "none"."""
    return has_security_prefix(key) or is_none_ci(policy)
# pure-end


def delete_cookie(cookie: Cookie, key: List[int], path: List[int],
                  domain: List[int], policy: List[int]) -> None:
    # pre-conditions-start
    # The freshly-keyed cookie morsel the expiry writes into is fully owned.
    Requires(Acc(cookie.secure) and Acc(cookie.has_policy))
    Requires(Acc(cookie.policy) and Acc(list_pred(cookie.policy)))
    Requires(Acc(cookie.expired))
    Requires(Acc(cookie.has_path))
    Requires(Acc(cookie.path) and Acc(list_pred(cookie.path)))
    Requires(Acc(cookie.has_domain))
    Requires(Acc(cookie.domain) and Acc(list_pred(cookie.domain)))
    # The name, the reach values and the policy value are read-only inputs:
    # fractional permission.
    Requires(Acc(list_pred(key), 1 / 2))
    Requires(Acc(list_pred(path), 1 / 2))
    Requires(Acc(list_pred(domain), 1 / 2))
    Requires(Acc(list_pred(policy), 1 / 2))
    # A supplied cross-site policy value is one the cookie machinery recognises,
    # and the cookie name is one it records a cookie under at all (non-empty, in
    # the name alphabet, not a name reserved for the header's own attributes).
    # Outside EITHER set no expiry cookie is emitted — the value or the name is
    # refused outright and the routine raises rather than returning — so the
    # emitted-cookie obligations below are stated exactly where an expiry cookie
    # exists to be observed. Both are domain restrictions of the same kind: they
    # say where the emitted cookie is observable, and nothing about how the
    # expiry decides the attributes it carries there. The path and the domain
    # are unrestricted: the machinery records them without inspecting them.
    Requires(Implies(len(policy) > 0, is_known_policy(policy)))
    Requires(is_storable_name(key))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(cookie.secure) and Acc(cookie.has_policy))
    Ensures(Acc(cookie.policy) and Acc(list_pred(cookie.policy)))
    Ensures(Acc(cookie.expired))
    Ensures(Acc(cookie.has_path))
    Ensures(Acc(cookie.path) and Acc(list_pred(cookie.path)))
    Ensures(Acc(cookie.has_domain))
    Ensures(Acc(cookie.domain) and Acc(list_pred(cookie.domain)))
    # Read-only inputs returned untouched at the same fractional permission.
    Ensures(Acc(list_pred(key), 1 / 2))
    Ensures(Acc(list_pred(path), 1 / 2))
    Ensures(Acc(list_pred(domain), 1 / 2))
    Ensures(Acc(list_pred(policy), 1 / 2))

    # (0) Expiring a cookie always hands it to the browser with an
    # already-elapsed lifetime, whatever the name and whatever the policy: that
    # is what makes it an expiry at all, and it is the pre-existing behaviour
    # that the added attributes must ride along with rather than replace. An
    # expiry that merely set the two attributes below would leave the cookie
    # live.
    Ensures(cookie.expired)

    # (0b) ... and it hands it over with exactly the reach it was asked for.
    # A browser drops a live cookie only when the expiry it receives applies to
    # the same path and the same host, so the emitted cookie carries the path
    # the expiry was asked for verbatim, and the host likewise. An expiry that
    # produced the right lifetime and the right attributes but reached somewhere
    # else — or, having been given a path, carried none at all — would be
    # ignored by the browser and the live cookie would stay.
    Ensures(Implies(len(path) > 0, cookie.has_path))
    Ensures(Implies(len(path) > 0, ToSeq(cookie.path) == ToSeq(path)))
    # Asked for no path, the expiry installs none of its own: any path the
    # emitted cookie carries is one it already carried, unchanged.
    Ensures(Implies(len(path) == 0,
                    Implies(cookie.has_path,
                            Old(cookie.has_path) and
                            ToSeq(cookie.path) == Old(ToSeq(cookie.path)))))
    Ensures(Implies(len(domain) > 0, cookie.has_domain))
    Ensures(Implies(len(domain) > 0, ToSeq(cookie.domain) == ToSeq(domain)))
    Ensures(Implies(len(domain) == 0,
                    Implies(cookie.has_domain,
                            Old(cookie.has_domain) and
                            ToSeq(cookie.domain) == Old(ToSeq(cookie.domain)))))

    # (2) The expiry marks the emitted cookie transport-secure exactly when the
    # name carries a reserved security prefix OR the policy is the unrestricted
    # "none", and on no other ground: since the flag accumulates and nothing
    # clears it, an expiry that asked for it for any other reason would leave a
    # cookie permanently transport-secure that must not be.
    Ensures(cookie.secure == (Old(cookie.secure) or expiry_secure(key, policy)))

    # (1) The cross-site policy attribute forwarded is the supplied one and
    # nothing else: a non-empty value supplied becomes the emitted cookie's
    # policy attribute verbatim, and when no value is supplied the expiry
    # installs no policy attribute of its own and leaves the cookie's policy
    # exactly as it stood.
    Ensures(cookie.has_policy == (Old(cookie.has_policy) or len(policy) > 0))
    Ensures(Implies(len(policy) > 0, ToSeq(cookie.policy) == ToSeq(policy)))
    Ensures(Implies(len(policy) == 0,
                    ToSeq(cookie.policy) == Old(ToSeq(cookie.policy))))
    # post-conditions-end
    # impl-start
    # Variant isolating the transport-secure decision: the cross-site policy
    # value IS forwarded onto the emitted cookie (forwarding behaviour restored),
    # but the transport-secure flag is still derived from the reserved name
    # prefix ALONE — the unrestricted "none" policy does not force it on.
    secure = has_security_prefix(key)
    store_cookie(cookie, path, domain, secure, policy)
    # impl-end
