"""PBT manifest for django__django-13195 (NOT a Nagini module; a record of
adversarial cases the runner swebench_nagini.pbt executes + stamps RESULT).

Defended surface (frozen spec in model.py; see refinement.md / mapping.md):

  delete_cookie(cookie: Cookie, key: List[int], path: List[int],
                domain: List[int], policy: List[int]) -> None
    Requires (frame):
        Acc(cookie.secure) and Acc(cookie.has_policy)            -- morsel owned
        Acc(cookie.policy) and Acc(list_pred(cookie.policy))     -- morsel owned
        Acc(cookie.expired)                                      -- morsel owned
        Acc(cookie.has_path)  and Acc(cookie.path)  + list_pred  -- morsel owned
        Acc(cookie.has_domain) and Acc(cookie.domain) + list_pred -- morsel owned
        Acc(list_pred(key),    1/2)   -- key    is READ-ONLY (1/2 fractional perm)
        Acc(list_pred(path),   1/2)   -- path   is READ-ONLY (1/2 fractional perm)
        Acc(list_pred(domain), 1/2)   -- domain is READ-ONLY (1/2 fractional perm)
        Acc(list_pred(policy), 1/2)   -- policy is READ-ONLY (1/2 fractional perm)
        Implies(len(policy) > 0, is_known_policy(policy))  -- recognised token only
        is_storable_name(key)         -- a name a cookie is recorded under (below)
        MustTerminate(10)             -- the routine must TERMINATE (see below)
      (the reach values carry NO restriction: the cookie machinery records them
       without inspecting them, measured in axiom_check.py)
    Ensures (frame): the morsel perms + ALL FOUR 1/2 read-only perms are returned
    Ensures (DECISIONS, load-bearing):
        (expired)  cookie.expired
        (reach)    Implies(len(path) > 0, cookie.has_path)
                   Implies(len(path) > 0, ToSeq(cookie.path) == ToSeq(path))
                   Implies(len(path) == 0,
                           Implies(cookie.has_path,
                                   Old(cookie.has_path) and
                                   ToSeq(cookie.path) == Old(ToSeq(cookie.path))))
                   ... and the same three clauses for `domain`
        (secure)   cookie.secure == (Old(cookie.secure) or expiry_secure(key, policy))
        (present)  cookie.has_policy == (Old(cookie.has_policy) or len(policy) > 0)
        (verbatim) Implies(len(policy) > 0, ToSeq(cookie.policy) == ToSeq(policy))
        (no-op)    Implies(len(policy) == 0,
                           ToSeq(cookie.policy) == Old(ToSeq(cookie.policy)))

  expiry_secure(key, policy) = has_security_prefix(key) or is_none_ci(policy)
    has_security_prefix(key): key starts with '__Secure-' or '__Host-'
    is_none_ci(policy):       policy is exactly 4 code points spelling n,o,n,e
                              under ASCII case fold ("none"/"NONE"/"None"/...)
    All three are @Pure helpers fully computable from the args.
  is_known_policy(policy) = is_none_ci or is_relaxed_ci ('lax') or
                            is_restrictive_ci ('strict'), each ASCII-case-folded.
  is_storable_name(key) = len(key) > 0 and all_name_chars(key) and
                          not is_reserved_name(key): the name domain the cookie
    machinery records a cookie under at all -- non-empty, every code point in the
    header grammar's name alphabet (letters/digits and ! # $ % & ' * + - . : ^ _
    ` | ~), and not one of the nine names reserved for the header's own
    attributes (expires/path/comment/domain/max-age/secure/httponly/version/
    samesite, any casing). Outside it the machinery refuses the request outright:
    NO cookie is recorded and the expiry raises instead of returning, so there is
    no emitted cookie for the Ensures above to be about. This is a DOMAIN
    restriction of the same kind as the policy one, and it is confirmed
    executable (not merely argued) by ax-containment below: over the full
    single-char ASCII sweep, the nine reserved names in five casings, a non-ASCII
    sample and 20k fuzz names, `is_storable_name` agrees with whether the real
    patched delete_cookie returns or raises on EVERY case.

CUMULATIVE-ATTRIBUTE LANE (the observable the earlier spec left free). The
attribute setter this routine builds on has a SET branch and no clearing branch,
and it writes into whatever record a cookie of that name already carries, so both
touched attributes ACCUMULATE across calls rather than being overwritten. An
earlier form of this spec stated the two decisions as equalities on the FINAL
state only (cookie.secure == expiry_secure(...), has_policy == (len(policy)>0))
and never bounded how many times the setter could be invoked. Under that form a
rival could make an EXTRA leading store with a value of its choosing -- secure
True, or a policy token like 'lax' -- and the model erased it, because the second
store's equality overwrote it; in the real cookie machinery that leading value
STICKS and permanently contaminates the emitted header. The postconditions now
read as accumulation against Old(...), which is what the real setter satisfies and
what such a rival does not: the leading store makes the accumulated value differ
from the specified one. `weak-extra-secure-store` / `weak-extra-policy-store`
below are exactly those rivals, and both VERIFIED under the equality form.

EXPIRY LANE (the second freed observable). The routine's whole purpose is to hand
the browser a cookie whose lifetime has already elapsed; the two attributes it now
also carries are additions that ride ALONGSIDE that, not replacements for it. The
earlier spec projected the cookie onto the two touched attributes ONLY, so nothing
observed the expiry itself, and a rival that assigned the two attributes directly
-- never routing through the setter that stamps the elapsed lifetime -- satisfied
every clause while emitting a LIVE cookie (measured: it verified). `Cookie.expired`
plus `Ensures(cookie.expired)` on both the routine and the setter axiom makes that
observable; `weak-live-cookie` is the rival.

REACH LANE (the third freed observable, and the one an audit refuted this spec on).
An expiry cookie only does its job if the browser matches it against the cookie it
is meant to drop, and matching is by REACH as well as by name: the request path the
cookie applies to and the host it belongs to. The routine is handed a reach on every
call -- the site root unless the caller names a narrower path, and host-wide unless
the caller names a domain -- and the emitted cookie must carry it. An earlier form of
this spec modelled the cookie as the elapsed lifetime plus the two touched attributes
ONLY, leaving the reach unmodelled on the argument that the change did not touch it.
That is a wrong modelling boundary, not a harmless omission: `expired` is an ordinary
assignable field, so a rival could satisfy every clause on the SLICE of the domain
where the two attributes are trivial (no policy supplied) by forging the elapsed
lifetime directly and never invoking the setter that installs the reach. The emitted
cookie then reaches nowhere and the browser keeps the live one. Measured: such a
rival VERIFIED under that form, and its faithful patch passes every graded test of
the change while breaking the pre-existing default-path behaviour. The reach clauses
above close it; `weak-forged-expiry-default`, `weak-drop-path-forwarding`,
`weak-drop-domain-forwarding` and `weak-hardcode-root-reach` are the rivals, and
`pos-control-reimplemented-recorder` is the control that keeps the obligation about
the OBSERVABLE cookie rather than about routing through a particular callee.

This models the gold patch's two introduced decisions in HttpResponseBase.delete_cookie:
  -  secure = key.startswith(('__Secure-','__Host-'))
  +  secure = key.startswith(('__Secure-','__Host-')) or (samesite and samesite.lower()=='none')
  +  self.set_cookie(..., samesite=samesite)   # was: no samesite kwarg
plus two pure call-site wirings (sessions/middleware, messages/storage/cookie)
that thread settings.SESSION_COOKIE_SAMESITE into the now-samesite-aware routine.

TERMINATION LANE: delete_cookie's precondition carries Requires(MustTerminate(10))
and Cookie.__init__ carries Requires(MustTerminate(2)) (strictly below, so an
obligated caller may build a morsel), making the proof TOTAL rather than partial.
The model is loop-free, so no loop invariant is needed; what the obligation buys
is the rejection of a NON-RETURNING implementation. The `diverge-selfcall` rival
below is exactly that, and it is the case that changed lane when the obligation
landed: it was authored as an accept-lane admissibility self-call against a spec
that demanded no termination, it is unbounded recursion, and it CANNOT be made to
terminate (unconditional call, constant arguments, no measure exists). Measured:
WITHOUT the obligation it VERIFIES; WITH it Nagini rejects it. So it is now a
reject-lane uniqueness case, which is a strictly stronger claim, and the
admissibility lane is preserved by `admiss-fresh-f2p-input`, which asks the same
precondition-admits-a-normal-input question without recursing.

GROUNDED-ORACLE NOTE: the secure postcondition oracle `expiry_secure(key,policy)`
is GROUNDED in the arguments -- it is a @Pure disjunction of two helpers fully
computable from `key` and `policy`, with NO opaque answer-key / exact marker. So
there is NO *wrong* echo a rival can return that still verifies: `secure =
expiry_secure(key, policy)` is the honest cheapest impl and is a CORRECT positive
control (pos-direct below), not an ungrounded-oracle attack. A wrong constant or a
wrong sub-decision FAILS the postcondition (the partial-domain rivals below). The
uniqueness lane is therefore: (a) the MANDATORY frame-mutation attacks against the
two read-only (1/2) inputs, and (b) partial-domain rivals that satisfy the secure
or forwarding decision on most of the domain but diverge on a discriminating
sub-domain (no prefix + policy "none"; non-empty policy not forwarded; AND vs OR).

AXIOM LANE: this bundle has ONE consumed @ContractOnly axiom, `store_cookie`
(A-consumed, models the UNCHANGED set_cookie callee), AND a deep-model A-reference
(`expiry_secure` + verbatim forwarding, models the CHANGED post-patch
delete_cookie). Both are validated == their real callees out-of-band by
axiom_check.py (G-AX). PBT re-runs that real-callee equivalence as the axiom lane:
axiom_check.py is read on the HOST at load time (the runner mounts ONLY the probe
at /work) and embedded verbatim into a self-contained Docker probe (Django only;
no bundle files needed in-container). A containment probe is added below: it
asserts every (key, policy) the MODEL can reach lies inside both callees' Requires
domains.

REGION-SURGERY: every spec variant is built by _swap on _BASE editing ONLY text
inside # impl-start/# impl-end (the impl region is just the two lines `secure =
...` and `store_cookie(...)`). The frozen spec (axioms/pure/pre/post-conditions/
signatures) is never touched, so same_spec holds for every spec case. The three
partial-domain rivals are lifted verbatim from the bundle's own proven-reject
model_prepatch*.py variants (G-DIFF: all share the spec byte-identically and FAIL
verification).
"""
from pathlib import Path

INSTANCE = "django__django-13195"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_DIR = Path(__file__).parent
_BASE = (_DIR / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Stable anchors inside the impl region (each present exactly once in _BASE).
# The impl region is exactly these two lines.
# ---------------------------------------------------------------------------
_SECURE = "    secure = has_security_prefix(key) or is_none_ci(policy)\n"
_STORE = "    store_cookie(cookie, path, domain, secure, policy)\n"
# The whole impl region, for rivals that replace BOTH lines at once.
_IMPL = _SECURE + _STORE

for _a in (_SECURE, _STORE, _IMPL):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"


# ===========================================================================
# POSITIVE CONTROLS / ADMISSIBILITY  (expect "verify")
# ===========================================================================

# (5a) POSITIVE CONTROL -- disjunction reorder. expiry_secure is
# `has_security_prefix(key) or is_none_ci(policy)`; computing the secure flag as
# the COMMUTED disjunction `is_none_ci(policy) or has_security_prefix(key)` is
# logically identical (OR is commutative) and a structurally-different impl form.
# No extra proof obligation is introduced (both disjuncts are @Pure, side-effect
# free). MUST verify; else the postcondition is over-fit to the disjunct ORDER
# => SPEC-TOO-STRONG.
_POS_REORDER = _swap(
    _BASE, _SECURE,
    "    secure = is_none_ci(policy) or has_security_prefix(key)\n",
)

# (5b) POSITIVE CONTROL -- the cheapest HONEST impl. The secure oracle
# expiry_secure(key, policy) is GROUNDED in the arguments (a @Pure disjunction),
# so assigning it directly is a correct, fully-grounded implementation, not an
# ungrounded-oracle echo. MUST verify (the postcondition is literally
# cookie.secure == expiry_secure(key, policy)); else SPEC-TOO-STRONG. Also
# demonstrates the spec is not echo-vulnerable: a WRONG secure value (constant or
# wrong sub-decision) fails the postcondition (see the partial-domain rivals).
_POS_DIRECT = _swap(
    _BASE, _SECURE,
    "    secure = expiry_secure(key, policy)\n",
)

# (6) ADMISSIBILITY -- construct a fresh, F2P-shaped input and drive the
# specified decisions on it. Build a fresh Cookie morsel and the F2P input key
# "__Host-c" with samesite "none" (test_delete_cookie_secure_samesite_none / the
# secure-prefix tests), establish the precondition frame on it (fresh Cookie()
# gives full morsel perms; fresh list literals carry list_pred so 1/2 is
# splittable), run the SPECIFIED expiry decisions on that input via the same
# grounded oracle + the same unchanged setter the gold body uses, then assert the
# secure / present / reach postconditions hold of the result -- INCLUDING their
# concrete values for this input ("__Host-" prefix => secure True; a 4-code-point
# policy => forwarded verbatim; the site-root reach the routine is reached with by
# default => carried verbatim, while the host-wide default installs no domain). The gold body then runs on the actual
# cookie/key/policy. MUST verify; else the precondition rejects a normal F2P
# input => PRECOND-TOO-STRONG.
#
# TERMINATION NOTE (why this is not a self-call). This case used to invoke
# `delete_cookie(probe_cookie, probe_key, probe_policy)` from inside
# delete_cookie's OWN impl region, unconditionally. That is unbounded recursion:
# the probe call re-enters the same body, which calls itself again, and the
# routine never reaches its return. Under the pre-obligation spec that rival
# VERIFIED (measured), because a postcondition is only claimed of runs that
# reach the return -- the precise partial-correctness hole
# Requires(MustTerminate(10)) exists to close. It is now a reject-lane case
# (diverge-selfcall, below) rather than an accept-lane one, and the
# admissibility question it was meant to ask -- "does the precondition admit a
# normal F2P input?" -- is asked here WITHOUT recursion, so the lane is
# preserved and the claim is strictly stronger.
#
# The two concrete-value Asserts also keep this case non-vacuous: it is checking
# reachable state, not an infeasible context. Control: appending Assert(False) to
# this body must FAIL (measured: "Assertion False might not hold"), so the probe
# is genuinely exercised rather than verifying under an unsatisfiable guard.
_POS_ADMISS = _swap(
    _BASE, _SECURE,
    "    probe_cookie = Cookie()\n"
    "    probe_key = [95, 95, 72, 111, 115, 116, 45, 99]  # type: List[int]\n"
    "    probe_policy = [110, 111, 110, 101]  # type: List[int]\n"
    "    probe_path = [47]  # type: List[int]\n"
    "    probe_domain = []  # type: List[int]\n"
    "    store_cookie(probe_cookie, probe_path, probe_domain,\n"
    "                 expiry_secure(probe_key, probe_policy), probe_policy)\n"
    "    Assert(probe_cookie.secure == expiry_secure(probe_key, probe_policy))\n"
    "    Assert(probe_cookie.has_policy == (len(probe_policy) > 0))\n"
    "    Assert(probe_cookie.secure)\n"
    "    Assert(len(probe_cookie.policy) == 4)\n"
    "    Assert(probe_cookie.expired)\n"
    "    Assert(probe_cookie.has_path)\n"
    "    Assert(ToSeq(probe_cookie.path) == ToSeq(probe_path))\n"
    "    Assert(not probe_cookie.has_domain)\n"
    "    secure = has_security_prefix(key) or is_none_ci(policy)\n",
)

# (5c) POSITIVE CONTROL -- accumulation-aware secure flag. The cumulative form of
# the secure postcondition (cookie.secure == (Old(cookie.secure) or
# expiry_secure(key,policy))) is satisfied just as well by an impl that reads the
# flag the cookie already carries and ORs it in before storing: with a set-only
# setter that is the SAME final state, and it is what a real implementation that
# wanted to be explicit about the accumulation would write. MUST verify; else the
# cumulative clauses have been written as an equality in disguise and are over-fit
# to storing a freshly-computed value => SPEC-TOO-STRONG. This control is what
# distinguishes the honest repair (state the accumulation the real setter has) from
# the dishonest one (require a fresh morsel, which would reject this impl too).
_POS_MONOTONE = _swap(
    _BASE, _SECURE,
    "    secure = cookie.secure or has_security_prefix(key) or is_none_ci(policy)\n",
)

# (5d) POSITIVE CONTROL -- the name-domain precondition is INFORMATIVE and it
# EXCLUDES the names the cookie machinery refuses. Three assertions inside the
# impl region, all discharged from `Requires(is_storable_name(key))` alone:
#   * len(key) > 0                  -- the empty name is out of the domain;
#   * not is_reserved_name(key)     -- so is any casing of the nine reserved
#                                      attribute names;
#   * not is_storable_name([101,120,112,105,114,101,115])  -- 'expires', the
#     witness input: the verifier PROVES the precondition rules it out, rather
#     than the spec merely being silent about it.
# MUST verify. It fails if the precondition is dropped or weakened to something
# that does not actually bound the name (the first two assertions lose their
# only justification), and it fails if the name predicate is written so loosely
# that a reserved name satisfies it (the third). Non-vacuity control for the same
# region: replacing these with Assert(False) must FAIL -- measured, "Assertion
# False might not hold" in 12.2s -- so the precondition is satisfiable and this
# case is checking reachable state, not an infeasible context. (That control also
# answers the standing question about a domain restriction: an unsatisfiable
# precondition would make every rival below verify vacuously; all eight are still
# rejected.)
_POS_NAME_DOMAIN = _swap(
    _BASE, _SECURE,
    "    Assert(len(key) > 0)\n"
    "    Assert(not is_reserved_name(key))\n"
    "    refused = [101, 120, 112, 105, 114, 101, 115]  # type: List[int]\n"
    "    Assert(not is_storable_name(refused))\n"
    "    secure = has_security_prefix(key) or is_none_ci(policy)\n",
)

# (7) UNIQUENESS / DIVERGENCE -- the unconditional self-call, kept as a rival.
# `delete_cookie` calls ITSELF from inside its own impl region with no guard and
# no decreasing argument, so the call re-enters the same body forever and the
# routine never reaches its return. This is a WRONG implementation of the expiry
# routine -- a faithful patch shaped like it hangs the very F2P test it is
# supposed to fix -- and the specification must reject it. It is only rejectable
# because delete_cookie's precondition now demands MustTerminate(10): a callee
# must sit STRICTLY BELOW its caller's level, and a method cannot be strictly
# below itself, so Nagini refuses the self-call. Measured both ways: without
# Requires(MustTerminate(10)) this rival VERIFIES; with it, Nagini reports
# "Obligation leak check failed. Callee delete_cookie might not take all
# unsatisfied obligations from the caller."
_RIVAL_DIVERGE_SELFCALL = _swap(
    _BASE, _SECURE,
    "    probe_cookie = Cookie()\n"
    "    probe_key = [95, 95, 72, 111, 115, 116, 45, 99]  # type: List[int]\n"
    "    probe_policy = [110, 111, 110, 101]  # type: List[int]\n"
    "    probe_path = [47]  # type: List[int]\n"
    "    probe_domain = []  # type: List[int]\n"
    "    delete_cookie(probe_cookie, probe_key, probe_path, probe_domain,\n"
    "                  probe_policy)\n"
    "    Assert(probe_cookie.secure == expiry_secure(probe_key, probe_policy))\n"
    "    Assert(probe_cookie.has_policy == (len(probe_policy) > 0))\n"
    "    secure = has_security_prefix(key) or is_none_ci(policy)\n",
)


# ===========================================================================
# UNIQUENESS RIVALS  (spec-too-weak probes -- expect "reject")
# ===========================================================================

# (1a) FRAME MUTATION -- MANDATORY (#1 weakness class). `key` is read-only at 1/2.
# This rival WRITES `key[0] = 95` ('_') before computing the secure flag,
# attempting to normalize the name so it looks like a security prefix and the
# secure decision is vacuously controllable. Under Acc(list_pred(key),1/2) a store
# needs FULL permission, so it MUST be rejected for INSUFFICIENT PERMISSION (not a
# value mismatch). The gold secure-disjunction + forwarding call are kept verbatim
# so the rejection is attributable solely to the write.
_RIVAL_FRAME_KEY = _swap(
    _BASE, _SECURE,
    "    key[0] = 95\n"
    "    secure = has_security_prefix(key) or is_none_ci(policy)\n",
)

# (1b) FRAME MUTATION -- MANDATORY. `policy` is read-only at 1/2. This rival WRITES
# `policy[0] = 110` ('n') before reading it, attempting to coerce the policy value
# (e.g. toward "none") so the secure/forwarding decisions are vacuously
# controllable. Under Acc(list_pred(policy),1/2) the store needs FULL permission,
# so it MUST be rejected for INSUFFICIENT PERMISSION. The gold logic is kept
# verbatim so the rejection is attributable solely to the write.
_RIVAL_FRAME_POLICY = _swap(
    _BASE, _SECURE,
    "    policy[0] = 110\n"
    "    secure = has_security_prefix(key) or is_none_ci(policy)\n",
)

# (3a) PARTIAL-DOMAIN -- drop the "none" disjunct (secure derived from the name
# prefix ALONE). == model_prepatch_2.py (bundle-proven reject). Correct on every
# name carrying a security prefix and on every non-"none" policy, but WRONG when
# the name has no prefix AND the policy is the unrestricted "none" (secure must be
# True, this gives False). Verbatim lift of the bundle's own differential witness.
_RIVAL_DROP_NONE = _swap(
    _BASE, _SECURE,
    "    secure = has_security_prefix(key)\n",
)

# (3b) PARTIAL-DOMAIN -- AND instead of OR in the secure decision. A subtler form
# of (3a): secure is True only when BOTH a security prefix AND a "none" policy
# hold. Correct only on the diagonal; WRONG on a prefixed name with a non-"none"
# policy (secure must be True, gives False) and on a non-prefixed "none" policy
# (secure must be True, gives False). Forwarding is kept correct, so the only
# discriminator is the secure postcondition.
_RIVAL_AND = _swap(
    _BASE, _SECURE,
    "    secure = has_security_prefix(key) and is_none_ci(policy)\n",
)

# (3c) PARTIAL-DOMAIN -- drop the policy forwarding (an empty value reaches the
# unchanged setter). == model_prepatch_3.py (bundle-proven reject). The secure
# decision is kept correct, but the cross-site policy is NOT forwarded: WRONG
# whenever a non-empty policy is supplied (has_policy must be True, gives False;
# and the verbatim-value clause is violated). Verbatim lift of the bundle's own
# differential witness for the forwarding behaviour. The empty list is bound to a
# typed local first (a bare `[]` literal carries list_pred; the # type comment
# attaches to the assignment target).
_RIVAL_DROP_FWD = _swap(
    _BASE, _STORE,
    "    dropped = []  # type: List[int]\n"
    "    store_cookie(cookie, path, domain, secure, dropped)\n",
)


# (4a) LEAKED-ATTRIBUTE -- an extra leading store that asks for transport-secure
# unconditionally. The gold secure disjunction and the gold forwarding store are
# both kept VERBATIM afterwards, so every decision the change introduces is
# computed correctly; the rival's only deviation is one additional store made
# first, with secure True and no policy value. Because the real setter has a set
# branch and no clearing branch, that True STICKS: every expiry cookie comes out
# transport-secure regardless of name and policy. MUST be rejected. Under the
# earlier equality form of the secure postcondition (cookie.secure ==
# expiry_secure(key,policy)) this rival VERIFIED (measured), because the second
# store's equality erased the first store's effect in the model while the real
# cookie keeps it -- the exact verify-not-resolve hole the cumulative form closes.
_RIVAL_EXTRA_SECURE = _swap(
    _BASE, _SECURE,
    "    presecure = []  # type: List[int]\n"
    "    prepath = []  # type: List[int]\n"
    "    predomain = []  # type: List[int]\n"
    "    store_cookie(cookie, prepath, predomain, True, presecure)\n"
    "    secure = has_security_prefix(key) or is_none_ci(policy)\n",
)

# (4b) LEAKED-ATTRIBUTE -- an extra leading store carrying a DIFFERENT recognised
# policy value ("Lax") before the correct forwarding store. Both gold decisions are
# again kept verbatim afterwards. The extra store is admissible (its value is a
# recognised policy), so it is not excluded by any domain restriction; it is wrong
# because a policy attribute installed once cannot be un-installed, so an expiry
# called with NO policy value still emits a cookie carrying SameSite=Lax. MUST be
# rejected. Under the earlier equality form of the presence postcondition
# (has_policy == (len(policy) > 0)) this rival VERIFIED (measured): with an empty
# policy the second store re-asserted has_policy False in the model, while the real
# cookie still carries the leaked attribute.
_RIVAL_EXTRA_POLICY = _swap(
    _BASE, _SECURE,
    "    lax = [76, 97, 120]  # type: List[int]\n"
    "    laxpath = []  # type: List[int]\n"
    "    laxdomain = []  # type: List[int]\n"
    "    secure = has_security_prefix(key) or is_none_ci(policy)\n"
    "    store_cookie(cookie, laxpath, laxdomain, secure, lax)\n",
)

# (4c) LIVE-COOKIE BYPASS -- compute BOTH attributes correctly but never route
# through the attribute setter, assigning the fields directly instead. Every value
# this rival produces for the two attributes the change touches is exactly right
# (the secure disjunction inlined and accumulated; the policy value copied element
# by element so it is genuinely verbatim, not aliased). It is wrong because
# expiring a cookie means handing the browser an already-elapsed lifetime, and the
# only thing that stamps that lifetime is the store this rival skips: the emitted
# cookie is LIVE. MUST be rejected. Under the earlier spec -- which projected the
# cookie onto the two touched attributes only and never observed the expiry -- this
# rival VERIFIED (measured). Rejection source: Ensures(cookie.expired).
_RIVAL_LIVE = _swap(
    _BASE, _IMPL,
    "    cookie.secure = cookie.secure or has_security_prefix(key) or is_none_ci(policy)\n"
    "    if len(policy) > 0:\n"
    "        cookie.has_policy = True\n"
    "        copied = []  # type: List[int]\n"
    "        i = 0\n"
    "        while i < len(policy):\n"
    "            Invariant(Acc(list_pred(copied)))\n"
    "            Invariant(Acc(list_pred(policy), 1 / 4))\n"
    "            Invariant(0 <= i and i <= len(policy))\n"
    "            Invariant(ToSeq(copied) == ToSeq(policy).take(i))\n"
    "            Invariant(MustTerminate(len(policy) - i + 1))\n"
    "            copied.append(policy[i])\n"
    "            i = i + 1\n"
    "        cookie.policy = copied\n",
)


# (4d) FORGED-EXPIRY ON THE DEFAULT SLICE -- the rival an audit refuted the
# earlier spec with, and the sharpest shape in this cell. It routes through the
# unchanged setter EXACTLY where the change's two attributes are non-trivial (a
# policy value was supplied) and forges the result directly on the complementary
# slice, where the pre-patch and post-patch routines agree: no policy, so the
# only thing to produce is an elapsed lifetime and, for a security-prefixed name,
# the secure flag. Both are ordinary assignable fields, so the forge satisfies
# every clause the earlier spec stated. It is wrong because the reach comes from
# the setter too: the emitted cookie carries no path, so the browser -- which
# matches an expiry against the live cookie by path as well as by name -- never
# drops the cookie the caller asked to delete. MUST be rejected.
_RIVAL_FORGED_DEFAULT = _swap(
    _BASE, _IMPL,
    "    if len(policy) > 0:\n"
    "        secure = has_security_prefix(key) or is_none_ci(policy)\n"
    "        store_cookie(cookie, path, domain, secure, policy)\n"
    "    else:\n"
    "        cookie.expired = True\n"
    "        if has_security_prefix(key):\n"
    "            cookie.secure = True\n",
)

# (4e) REACH DROPPED -- every decision the change introduces is computed and
# stored exactly as the gold body does, and the elapsed lifetime is stamped by
# the same setter; the rival's only deviation is that it hands the setter NO path
# where it was given one. The emitted expiry then applies to no particular path,
# so a browser holding the cookie under the path it was set with does not drop
# it. MUST be rejected.
_RIVAL_DROP_PATH = _swap(
    _BASE, _STORE,
    "    nopath = []  # type: List[int]\n"
    "    store_cookie(cookie, nopath, domain, secure, policy)\n",
)

# (4f) HOST DROPPED -- the same shape on the other reach argument: the domain the
# caller named is not forwarded, so the expiry is emitted host-wide and the
# browser does not match it against a cookie held for the named host. MUST be
# rejected.
_RIVAL_DROP_DOMAIN = _swap(
    _BASE, _STORE,
    "    nodomain = []  # type: List[int]\n"
    "    store_cookie(cookie, path, nodomain, secure, policy)\n",
)

# (4g) REACH HARD-CODED TO THE SITE ROOT -- subtler than (4e), and the rival that
# distinguishes the honest obligation from the tempting wrong one. The routine's
# reach DEFAULT is the site root, and the overwhelming majority of calls (and of
# the graded tests) leave it at the default, so a rival that ignores its path
# argument and always stores the root is right on all of them. It is wrong
# exactly where a caller names a narrower path -- the session teardown with a
# custom path, for instance -- and there the emitted expiry reaches the wrong
# place. MUST be rejected. This is why the obligation is stated as "the reach it
# was ASKED for" and NOT as "the reach is the site root": the latter would
# verify this rival while rejecting the gold routine's own behaviour on a
# custom path.
_RIVAL_ROOT_REACH = _swap(
    _BASE, _STORE,
    "    root = [47]  # type: List[int]\n"
    "    store_cookie(cookie, root, domain, secure, policy)\n",
)


# (5e) POSITIVE CONTROL -- the work split across TWO stores. A faithful
# implementation is free to reach the same emitted cookie in more than one step:
# this one stores the reach and the policy first and the computed secure flag
# second. Every attribute of the emitted cookie ends up exactly as the gold body
# leaves it (the setter accumulates, so the order does not matter here). MUST
# verify; else the spec has acquired an "exactly one store" obligation nobody can
# read off the repo -- a counter or a witness in disguise -- and correct
# implementations are rejected => SPEC-TOO-STRONG.
_POS_TWO_STORE = _swap(
    _BASE, _IMPL,
    "    store_cookie(cookie, path, domain, False, policy)\n"
    "    secure = has_security_prefix(key) or is_none_ci(policy)\n"
    "    empty = []  # type: List[int]\n"
    "    store_cookie(cookie, path, domain, secure, empty)\n",
)

# (5f) POSITIVE CONTROL -- the recorder re-implemented in place. This rival never
# calls the setter at all: it assigns the elapsed lifetime, the secure flag, and
# copies the policy and BOTH reach values element by element into the emitted
# cookie. It is the extreme case of "same emitted cookie, different route", and
# it MUST verify, because the obligations are about the cookie the browser
# receives and not about which callee produced it. Measured on the real tree: a
# patch shaped like this emits byte-identical headers to the gold patch on every
# input shape the graded tests reach, and passes all of
# responses.test_cookie / sessions_tests.tests / messages_tests.test_cookie --
# so admitting it is correct, and rejecting it would be SPEC-TOO-STRONG (the spec
# would be demanding a call, which is a structural demand, not a behavioural
# one). It is also the control for the reach obligation specifically: it shows
# the reach clauses are satisfiable WITHOUT the setter, so the reason
# `weak-forged-expiry-default` above is rejected is that its emitted cookie
# reaches nowhere -- not that it declined to make a call.
_POS_REIMPL_RECORDER = _swap(
    _BASE, _IMPL,
    "    cookie.expired = True\n"
    "    if has_security_prefix(key) or is_none_ci(policy):\n"
    "        cookie.secure = True\n"
    "    if len(policy) > 0:\n"
    "        cpol = []  # type: List[int]\n"
    "        i_cpol = 0\n"
    "        while i_cpol < len(policy):\n"
    "            Invariant(Acc(list_pred(cpol)))\n"
    "            Invariant(Acc(list_pred(policy), 1 / 4))\n"
    "            Invariant(0 <= i_cpol and i_cpol <= len(policy))\n"
    "            Invariant(ToSeq(cpol) == ToSeq(policy).take(i_cpol))\n"
    "            Invariant(MustTerminate(len(policy) - i_cpol + 1))\n"
    "            cpol.append(policy[i_cpol])\n"
    "            i_cpol = i_cpol + 1\n"
    "        cookie.has_policy = True\n"
    "        cookie.policy = cpol\n"
    "    if len(path) > 0:\n"
    "        cpat = []  # type: List[int]\n"
    "        i_cpat = 0\n"
    "        while i_cpat < len(path):\n"
    "            Invariant(Acc(list_pred(cpat)))\n"
    "            Invariant(Acc(list_pred(path), 1 / 4))\n"
    "            Invariant(0 <= i_cpat and i_cpat <= len(path))\n"
    "            Invariant(ToSeq(cpat) == ToSeq(path).take(i_cpat))\n"
    "            Invariant(MustTerminate(len(path) - i_cpat + 1))\n"
    "            cpat.append(path[i_cpat])\n"
    "            i_cpat = i_cpat + 1\n"
    "        cookie.has_path = True\n"
    "        cookie.path = cpat\n"
    "    if len(domain) > 0:\n"
    "        cdom = []  # type: List[int]\n"
    "        i_cdom = 0\n"
    "        while i_cdom < len(domain):\n"
    "            Invariant(Acc(list_pred(cdom)))\n"
    "            Invariant(Acc(list_pred(domain), 1 / 4))\n"
    "            Invariant(0 <= i_cdom and i_cdom <= len(domain))\n"
    "            Invariant(ToSeq(cdom) == ToSeq(domain).take(i_cdom))\n"
    "            Invariant(MustTerminate(len(domain) - i_cdom + 1))\n"
    "            cdom.append(domain[i_cdom])\n"
    "            i_cdom = i_cdom + 1\n"
    "        cookie.has_domain = True\n"
    "        cookie.domain = cdom\n",
)


SPEC_TESTS = [
    # ---- positive controls / admissibility (must VERIFY) ----
    {"id": "pos-control-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "structurally-different but CORRECT impl: the secure flag is "
                  "computed as the COMMUTED disjunction is_none_ci(policy) or "
                  "has_security_prefix(key) (OR is commutative, both disjuncts @Pure "
                  "side-effect-free), identical to expiry_secure. Introduces no new "
                  "proof obligation. Must verify; else the secure postcondition is "
                  "over-fit to the disjunct ORDER => SPEC-TOO-STRONG."},
    {"id": "pos-control-direct", "kind": "soundness", "expect": "verify",
     "module": _POS_DIRECT,
     "rationale": "the secure oracle expiry_secure(key,policy) is GROUNDED in the "
                  "arguments (a @Pure disjunction), so `secure = expiry_secure(key, "
                  "policy)` is the honest cheapest CORRECT impl, not an ungrounded "
                  "echo. Must verify (postcondition is literally cookie.secure == "
                  "expiry_secure(key,policy)); else SPEC-TOO-STRONG. Also shows the "
                  "spec is NOT echo-vulnerable: a WRONG secure value fails the "
                  "postcondition (see the partial-domain rivals)."},
    {"id": "pos-control-accumulate", "kind": "soundness", "expect": "verify",
     "module": _POS_MONOTONE,
     "rationale": "the attribute setter records cumulatively (set branch, no clearing "
                  "branch, writing into the record the cookie already carries), so an "
                  "impl that reads the flag the cookie already has and ORs the expiry "
                  "decision into it reaches the SAME final state as storing the freshly "
                  "computed value, and is what an implementation being explicit about the "
                  "accumulation would write. Must verify; else the cumulative "
                  "postconditions are an equality in disguise, over-fit to storing a "
                  "fresh value => SPEC-TOO-STRONG. This is also the control separating "
                  "the honest strengthening (state the accumulation the real setter has) "
                  "from the dishonest one (demand a pristine morsel in the precondition, "
                  "which would reject this correct impl as well)."},
    {"id": "pos-control-two-store", "kind": "soundness", "expect": "verify",
     "module": _POS_TWO_STORE,
     "rationale": "a faithful implementation may reach the same emitted cookie in "
                  "more than one step: this one makes two calls to the unchanged "
                  "setter, the first carrying the reach and the policy, the second "
                  "the computed secure flag. Because the setter accumulates, the "
                  "emitted cookie is exactly the one the gold body leaves. Must "
                  "verify; else the spec has acquired an 'exactly one store' "
                  "obligation -- a store counter or a witness in disguise, readable "
                  "nowhere in the repo -- and rejects correct implementations => "
                  "SPEC-TOO-STRONG. This is the control that rules out the tempting "
                  "wrong repair for the reach hole (count the stores) in favour of "
                  "the right one (state what the emitted cookie carries)."},
    {"id": "pos-control-reimplemented-recorder", "kind": "soundness",
     "expect": "verify",
     "module": _POS_REIMPL_RECORDER,
     "rationale": "the recorder re-implemented in place: no call to the setter at "
                  "all -- the elapsed lifetime and the secure flag assigned "
                  "directly, and the policy and BOTH reach values copied element by "
                  "element into the emitted cookie. The obligations are about the "
                  "cookie the browser receives, not about which callee produced it, "
                  "so this must verify. Measured on the real tree: a patch shaped "
                  "like this emits byte-identical Set-Cookie headers to the gold "
                  "patch on every input shape the graded tests reach and passes all "
                  "of responses.test_cookie / sessions_tests.tests / "
                  "messages_tests.test_cookie, so it is genuinely admissible; "
                  "rejecting it would be SPEC-TOO-STRONG (a structural demand for a "
                  "call in place of a behavioural one). It is also the control for "
                  "the reach clauses specifically: they are satisfiable WITHOUT the "
                  "setter, so weak-forged-expiry-default below is rejected because "
                  "its emitted cookie reaches nowhere, not because it declined to "
                  "make a call."},
    {"id": "precond-name-domain", "kind": "soundness", "expect": "verify",
     "module": _POS_NAME_DOMAIN,
     "rationale": "the name-domain precondition Requires(is_storable_name(key)) "
                  "must be INFORMATIVE, and it must exclude exactly the names the "
                  "cookie machinery refuses. Three assertions discharged from it "
                  "alone: len(key) > 0; not is_reserved_name(key); and -- the "
                  "witness -- not is_storable_name('expires' as code points), i.e. "
                  "the verifier PROVES the precondition rules out the name on which "
                  "the real routine raises CookieError and emits no cookie. Must "
                  "verify; if the precondition were dropped the first two "
                  "assertions have no justification, and if the name predicate were "
                  "written loosely enough to admit a reserved name the third fails. "
                  "Non-vacuity control (measured): Assert(False) in the same "
                  "position FAILS, so the restricted domain is satisfiable and this "
                  "case observes reachable state -- and the eight rivals below are "
                  "still rejected, which no vacuous precondition would allow."},
    {"id": "admiss-fresh-f2p-input", "kind": "admissibility", "expect": "verify",
     "module": _POS_ADMISS,
     "rationale": "a fresh Cookie() morsel and the F2P-shaped input key \"__Host-c\" "
                  "with policy \"none\" (test_delete_cookie_secure_samesite_none / the "
                  "secure-prefix tests) must establish the precondition (fresh Cookie() "
                  "=> full morsel perms, and its own Requires(MustTerminate(2)) sits "
                  "strictly below delete_cookie's level 10 so an obligated caller may "
                  "build one; fresh list literals => list_pred so the 1/2 read-only perm "
                  "is splittable) and then satisfy the secure/has_policy postconditions "
                  "on that input, including their concrete values ('__Host-' => secure "
                  "True; 4-code-point policy => forwarded verbatim). If the precondition "
                  "rejects this normal F2P input => PRECOND-TOO-STRONG. Non-vacuity "
                  "control: appending Assert(False) to this body must fail (measured)."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "diverge-selfcall", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DIVERGE_SELFCALL,
     "refinement": "no faithful real patch corresponds to this: HttpResponseBase."
                   "delete_cookie computes the secure flag and calls set_cookie; it "
                   "never re-enters itself. A patch shaped like this rival recurses "
                   "unboundedly and never returns, so delete_cookie('c', "
                   "samesite='none') HANGS -- it fails the F2P "
                   "test_delete_cookie_secure_samesite_none by timing out rather than "
                   "by asserting the wrong value. It is the purest possible "
                   "verify-not-resolve artifact: the postconditions are all satisfied "
                   "vacuously because control never reaches the return.",
     "rationale": "DIVERGENCE probe. This was formerly an accept-lane admissibility "
                  "case, and it is here because it CANNOT be made to terminate: the "
                  "self-call is unconditional and its arguments are fresh constants, "
                  "so there is no decreasing measure to find -- the rival genuinely "
                  "never returns. Rejection source: the TERMINATION OBLIGATION. "
                  "delete_cookie requires MustTerminate(10) and a callee must sit "
                  "strictly below its caller's level; a method cannot be strictly below "
                  "itself, so Nagini reports 'Obligation leak check failed. Callee "
                  "delete_cookie might not take all unsatisfied obligations from the "
                  "caller.' Measured both ways: WITHOUT the obligation this rival "
                  "VERIFIES (partial correctness admits a diverging impl); WITH it the "
                  "verifier rejects it. If it verified => SPEC-TOO-WEAK (the spec would "
                  "prove only PARTIAL correctness and admit an implementation that "
                  "hangs)."},
    {"id": "frame-mutate-key", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME_KEY,
     "refinement": "no faithful real patch corresponds to this: HttpResponseBase."
                   "delete_cookie inspects the cookie name `key` (a str, immutable) "
                   "with key.startswith(...); it NEVER rewrites the name. The rival "
                   "exists solely to test whether the read-only (1/2) precondition on "
                   "`key` can be subverted by overwriting it to fabricate a security "
                   "prefix. There is no resolving patch that mutates its `key` argument, "
                   "so a verifying rival here would be a pure verify-not-resolve artifact "
                   "(vacuous control of the secure decision via self-normalization).",
     "rationale": "MANDATORY frame-mutation probe. `key[0] = 95` writes through a 1/2 "
                  "(read-only) reference and MUST fail for INSUFFICIENT PERMISSION (a "
                  "store needs full Acc(list_pred(key))), NOT a value mismatch; the gold "
                  "secure-disjunction + forwarding call are kept verbatim so the "
                  "rejection is attributable to the write. Rejection source: the "
                  "PERMISSION SYSTEM. If it verified => SPEC-TOO-WEAK (key frame "
                  "protection hollow)."},
    {"id": "frame-mutate-policy", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME_POLICY,
     "refinement": "no faithful real patch corresponds to this: delete_cookie reads the "
                   "samesite value (a str) to compute `samesite.lower()=='none'` and to "
                   "forward it; it NEVER mutates the caller's samesite argument. The "
                   "rival exists solely to test whether the read-only (1/2) precondition "
                   "on `policy` can be subverted by overwriting it (e.g. toward 'none') "
                   "to control the secure/forwarding decisions. There is no resolving "
                   "patch that rewrites its samesite argument, so a verifying rival here "
                   "would be a verify-not-resolve artifact.",
     "rationale": "MANDATORY frame-mutation probe. `policy[0] = 110` writes through a "
                  "1/2 (read-only) reference and MUST fail for INSUFFICIENT PERMISSION (a "
                  "store needs full Acc(list_pred(policy))), NOT a value mismatch; the "
                  "gold logic is kept verbatim so the rejection is attributable to the "
                  "write. Rejection source: the PERMISSION SYSTEM. If it verified => "
                  "SPEC-TOO-WEAK (policy frame protection hollow)."},
    {"id": "weak-drop-none-disjunct", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_NONE,
     "refinement": "this is the EXACT pre-patch secure decision (== bundle's proven-"
                   "reject model_prepatch_2.py): secure = key.startswith(('__Secure-',"
                   "'__Host-')) only, dropping the `or (samesite and samesite.lower()=="
                   "'none')` disjunct the gold patch introduces. A faithful patch keeping "
                   "this still emits secure='' for delete_cookie('c', samesite='none') "
                   "and FAILS the F2P test_delete_cookie_secure_samesite_none (which "
                   "asserts response.cookies['c']['secure'] is True) -- verify-not-resolve.",
     "rationale": "rejection source: the postcondition cookie.secure == "
                  "expiry_secure(key,policy). For a name with no security prefix and "
                  "policy 'none', expiry_secure is True but has_security_prefix(key) is "
                  "False, so the verifier cannot close the secure clause. (Bundle G-DIFF "
                  "already proves this same-spec variant FAILS verification.) If it "
                  "verified => SPEC-TOO-WEAK."},
    {"id": "weak-and-instead-of-or", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_AND,
     "refinement": "secure = prefix AND none-policy is True only on the diagonal "
                   "(prefixed name with a 'none' policy). A faithful patch using AND "
                   "still emits secure='' for delete_cookie('__Host-c') with no/lax "
                   "samesite -- FAILING the P2P test_delete_cookie_secure_prefix (asserts "
                   "secure is True for a __Host-/__Secure- name regardless of samesite) "
                   "AND for delete_cookie('c', samesite='none') -- FAILING the F2P "
                   "test_delete_cookie_secure_samesite_none. verify-not-resolve.",
     "rationale": "rejection source: the postcondition cookie.secure == "
                  "expiry_secure(key,policy) (= OR, not AND). On a prefixed name with a "
                  "non-'none' policy, expiry_secure is True but `prefix and none` is "
                  "False; the verifier cannot close the secure clause. If it verified => "
                  "SPEC-TOO-WEAK (the disjunction would collapse to a conjunction)."},
    {"id": "weak-drop-forwarding", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_FWD,
     "refinement": "this drops the verbatim samesite forwarding (== bundle's proven-"
                   "reject model_prepatch_3.py): an empty value reaches the unchanged "
                   "set_cookie, so the emitted cookie carries no samesite -- exactly the "
                   "pre-patch behaviour (no samesite= kwarg). A faithful patch keeping "
                   "this still emits no SameSite for delete_cookie('c', samesite='lax') "
                   "and FAILS the F2P test_delete_cookie_samesite (asserts "
                   "response.cookies['c']['samesite'] == 'lax'), test_cookie_setings, and "
                   "test_session_delete_on_end* (assert SameSite=Lax in the header) -- "
                   "verify-not-resolve.",
     "rationale": "rejection source: the postconditions cookie.has_policy == "
                  "(len(policy) > 0) and Implies(len(policy)>0, ToSeq(cookie.policy)=="
                  "ToSeq(policy)). With store_cookie passed an empty list, the axiom "
                  "gives has_policy == (0 > 0) == False and no value, but the "
                  "postcondition requires has_policy == (len(policy) > 0); on any "
                  "non-empty policy the verifier cannot close it. (Bundle G-DIFF proves "
                  "this same-spec variant FAILS exactly here.) If it verified => "
                  "SPEC-TOO-WEAK."},
    {"id": "weak-extra-secure-store", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EXTRA_SECURE,
     "refinement": "a faithful patch shaped like this computes the secure flag exactly as "
                   "the gold one does and forwards the policy exactly as the gold one "
                   "does, but calls set_cookie an extra time first with secure=True. "
                   "set_cookie's secure handling is `if secure: self.cookies[key]"
                   "['secure'] = True` -- there is no else that clears it -- and "
                   "BaseCookie.__set does `M = self.get(key, Morsel())`, reusing the "
                   "morsel already stored under that name. So the leading True is never "
                   "undone: response.delete_cookie('c') emits Secure for an ordinary name "
                   "with no samesite, breaking the P2P DeleteCookieTests.test_default "
                   "(asserts the emitted cookie is not secure) while still passing every "
                   "F2P test. Classic verify-not-resolve: right final decision, extra "
                   "irreversible effect.",
     "rationale": "LEAKED-ATTRIBUTE probe -- the family that broke the earlier spec. "
                  "Rejection source: the cumulative secure postcondition cookie.secure == "
                  "(Old(cookie.secure) or expiry_secure(key,policy)). After the leading "
                  "store the flag is unconditionally on, so the final state is "
                  "(Old or True) = True, which cannot equal (Old or expiry_secure) when "
                  "expiry_secure is False. Measured both ways: under the earlier equality "
                  "form (cookie.secure == expiry_secure(key,policy)) this rival VERIFIES, "
                  "because that clause constrains only the FINAL value and the second "
                  "store was modelled as overwriting; with the cumulative form the "
                  "verifier rejects it. If it verified => SPEC-TOO-WEAK (intermediate "
                  "writes to an accumulating attribute would be unobservable)."},
    {"id": "weak-extra-policy-store", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EXTRA_POLICY,
     "refinement": "a faithful patch shaped like this forwards the caller's samesite "
                   "correctly, but first calls set_cookie with samesite='Lax'. That value "
                   "is a legal samesite token, so nothing refuses it; and set_cookie's "
                   "samesite handling is `if samesite: ...['samesite'] = samesite` with no "
                   "clearing else, over a REUSED morsel. The Lax therefore sticks: "
                   "response.delete_cookie('c') with no samesite emits SameSite=Lax, "
                   "breaking DeleteCookieTests.test_default, while every F2P samesite test "
                   "still passes because the caller's value overwrites Lax when supplied. "
                   "verify-not-resolve.",
     "rationale": "LEAKED-ATTRIBUTE probe, presence variant. Rejection source: the "
                  "cumulative presence postcondition cookie.has_policy == "
                  "(Old(cookie.has_policy) or len(policy) > 0) together with the "
                  "empty-policy no-op clause. The leading store installs a policy "
                  "attribute, so on an empty policy the final has_policy is True while the "
                  "postcondition demands Old(cookie.has_policy) -- and the policy VALUE is "
                  "Lax where the no-op clause demands the value the cookie came in with. "
                  "Measured both ways: under the earlier equality form (has_policy == "
                  "(len(policy) > 0)) this rival VERIFIES. If it verified => SPEC-TOO-WEAK."},
    {"id": "weak-live-cookie", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_LIVE,
     "refinement": "a faithful patch shaped like this reaches into "
                   "self.cookies[key] and sets ['secure'] and ['samesite'] itself "
                   "instead of calling set_cookie. Both attributes come out with exactly "
                   "the values the gold patch produces, so every samesite/secure assertion "
                   "in the F2P set passes -- but set_cookie is also what writes "
                   "expires='Thu, 01 Jan 1970 00:00:00 GMT' and max_age=0, so the cookie "
                   "is emitted with no expiry at all. It is a LIVE cookie: "
                   "delete_cookie no longer deletes. That fails "
                   "DeleteCookieTests.test_default (asserts the Max-Age/expires of the "
                   "emitted cookie) and the session teardown tests. The most instructive "
                   "verify-not-resolve shape in this cell: every value the change "
                   "introduces is right, and the routine still does not do its job.",
     "rationale": "EXPIRY-BYPASS probe. Rejection source: Ensures(cookie.expired), "
                  "which this rival establishes nowhere -- it assigns the two touched "
                  "attributes and nothing else -- and the reach clauses, which it "
                  "likewise leaves unestablished on any call that names a path. Note "
                  "what this rejection does NOT rest on: `expired` is an ordinary "
                  "assignable field, so a rival is free to assign it and thereby "
                  "satisfy that clause without the setter (pos-control-reimplemented-"
                  "recorder does exactly that, correctly). The expiry clause alone is "
                  "therefore not a barrier to a bypass; it is the REACH clauses that "
                  "close the bypass family, which is why weak-forged-expiry-default "
                  "below is in the battery. Measured both ways: under the earlier "
                  "spec, which observed only the two touched attributes and never the "
                  "expiry, this rival VERIFIES; with the expiry obligation the "
                  "verifier rejects it. If it verified => SPEC-TOO-WEAK (the spec "
                  "would constrain the two ADDED attributes while leaving the "
                  "routine's pre-existing purpose unobserved, so a rival could "
                  "satisfy the addition by abandoning the original behaviour)."},
    {"id": "weak-forged-expiry-default", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FORGED_DEFAULT,
     "refinement": "a faithful patch shaped like this keeps the gold body whenever a "
                   "samesite value was supplied, and on the complementary slice -- no "
                   "samesite, where the pre-patch and post-patch routines agree -- "
                   "writes into self.cookies[key] itself: an expiry date in the past "
                   "and, for a __Host-/__Secure- name, ['secure'] = True. Every graded "
                   "test of the change supplies a samesite value or asserts only the "
                   "secure flag, so all five FAIL_TO_PASS tests pass. What the slice "
                   "loses is the reach: set_cookie is also what writes Path, so "
                   "response.delete_cookie('c') emits an expiry with no path at all "
                   "and the browser never matches it against the cookie set at the "
                   "site root. Measured: a patch of exactly this shape passes 5/5 "
                   "FAIL_TO_PASS and breaks DeleteCookieTests.test_default, which "
                   "asserts the emitted cookie's path is the site root. The canonical "
                   "verify-not-resolve shape for this cell.",
     "rationale": "REACH-BYPASS probe -- the rival an audit refuted the earlier form of "
                  "this spec with. Rejection source: the reach postcondition "
                  "Implies(len(path) > 0, cookie.has_path) (measured message: "
                  "'Postcondition of delete_cookie might not hold. Assertion "
                  "Implies((len(path) > 0), cookie.has_path) might not hold.'). On the "
                  "forged slice the emitted cookie carries no path, while the routine "
                  "was asked for one. Measured both ways: WITHOUT the reach clauses "
                  "this rival VERIFIES (and its patch does not resolve); WITH them the "
                  "verifier rejects it. If it verified => SPEC-TOO-WEAK: the spec would "
                  "pin the behaviour the change ADDS while leaving the routine's "
                  "pre-existing default-path behaviour free, so a rival could satisfy "
                  "the addition on the interesting slice and abandon the original "
                  "behaviour on the rest."},
    {"id": "weak-drop-path-forwarding", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_PATH,
     "refinement": "a faithful patch shaped like this computes the secure flag and "
                   "forwards the samesite value exactly as the gold one does, and calls "
                   "the same setter, but drops `path=path` from the call. set_cookie's "
                   "path handling is `if path is not None: ...['path'] = path`, so the "
                   "emitted expiry carries no Path attribute. That breaks "
                   "DeleteCookieTests.test_default (asserts the emitted cookie's path "
                   "is '/') and every session/message teardown test that expects the "
                   "expiry to reach the path the cookie was set with.",
     "rationale": "rejection source: the reach postconditions Implies(len(path) > 0, "
                  "cookie.has_path) and the verbatim clause. The setter axiom, handed "
                  "an empty path, installs no path, so on any call that names one the "
                  "verifier cannot close the clause. If it verified => SPEC-TOO-WEAK "
                  "(the emitted cookie's reach would be unconstrained)."},
    {"id": "weak-drop-domain-forwarding", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_DOMAIN,
     "refinement": "the same shape on the other reach argument: `domain=domain` is "
                   "dropped from the setter call, so the emitted expiry is host-wide "
                   "instead of belonging to the host the caller named. A browser holding "
                   "the cookie for that host does not match a host-wide expiry against "
                   "it. Measured on the graded set: this is what "
                   "test_session_delete_on_end_with_custom_domain_and_path and "
                   "test_cookie_setings observe (the emitted expiry's domain must be "
                   "the configured one).",
     "rationale": "rejection source: the reach postconditions Implies(len(domain) > 0, "
                  "cookie.has_domain) and the verbatim clause. If it verified => "
                  "SPEC-TOO-WEAK. Kept alongside the path rival because closing only "
                  "the path leg would leave a forging rival free to drop the host: the "
                  "hole would persist on two of the five FAIL_TO_PASS tests."},
    {"id": "weak-hardcode-root-reach", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ROOT_REACH,
     "refinement": "a faithful patch shaped like this ignores its `path` argument and "
                   "always calls the setter with path='/'. Since the routine's own "
                   "default IS the site root, it is right on every call that leaves the "
                   "default -- which is most of the graded set -- and wrong exactly "
                   "where a caller names a narrower path: the emitted expiry then "
                   "reaches the site root instead of that path and the cookie held "
                   "under it is not dropped. That breaks "
                   "test_session_delete_on_end_with_custom_domain_and_path, which sets "
                   "the session cookie at a custom path and expects the teardown expiry "
                   "to reach it.",
     "rationale": "rejection source: the verbatim reach clause Implies(len(path) > 0, "
                  "ToSeq(cookie.path) == ToSeq(path)) (measured message: 'Assertion "
                  "Implies((len(path) > 0), (ToSeq(cookie.path) == ToSeq(path))) might "
                  "not hold'). This rival is the reason the obligation is stated as "
                  "'the emitted cookie carries the reach it was ASKED for' rather than "
                  "the tempting 'the emitted cookie reaches the site root': the latter "
                  "would ADMIT this rival and simultaneously reject the gold routine on "
                  "a custom path, i.e. it would be both too weak and too strong. If it "
                  "verified => SPEC-TOO-WEAK."},
]


# ===========================================================================
# AXIOM LANE
#   ax-real-callees-sound (axiom-soundness): re-runs axiom_check.py verbatim in
#     the gold-patched instance image. It validates BOTH (a) the A-consumed
#     `store_cookie` axiom == the real UNCHANGED set_cookie and (b) the
#     A-reference deep model (expiry_secure + verbatim forwarding) == the real
#     CHANGED post-patch delete_cookie, over the names x valid-policies cross
#     product + 4000 fuzz (4360 + 4180 cases). If the real callee ever disagrees
#     with the axiom Ensures / deep model, the axiom is UNSOUND.
#   ax-containment (axiom-containment): asserts every (key, policy) the MODEL can
#     reach lies INSIDE both callees' Requires domains, over BOTH dimensions the
#     cookie machinery can refuse a request on.
#       policy: the model passes `policy` straight through to store_cookie's
#         `Acc(list_pred(policy),1/2)` and reads it via the @Pure helpers; the
#         domain constraint the store_cookie axiom does NOT cover is the
#         set_cookie ValueError raise path for an INVALID samesite token (not in
#         lax/none/strict). We assert the only policy values the caller flows are
#         the VALID tokens (the F2P/P2P + call-site values), so the raise path is
#         unreachable from the model.
#       name: the machinery records a cookie ONLY under a name in the header
#         grammar's alphabet that is not one of its nine reserved attribute names;
#         under any other name Morsel.set raises CookieError and NOTHING is
#         emitted. `Requires(is_storable_name(key))` is the model's statement of
#         that domain, so containment here is an EQUIVALENCE to check, not an
#         argument to make: the probe runs the real patched delete_cookie and
#         asserts `is_storable_name` agrees with return-vs-raise on every name it
#         tries, and that every name the real call sites reach is inside it.
#
# axiom_check.py is read on the HOST at load time and embedded verbatim (the
# runner mounts ONLY the probe at /work; the bundle's model.py/axiom_check.py are
# NOT in-container). It imports only stdlib + Django, both present in the image.
# ===========================================================================

_AXIOM_CHECK_SRC = (_DIR / "axiom_check.py").read_text()

# Containment probe, over the TWO dimensions on which the cookie machinery can
# refuse an expiry request outright:
#   (1) POLICY. Enumerate the samesite tokens the MODEL/caller can reach and
#       assert each is falsey or a VALID token, so set_cookie's ValueError raise
#       path -- the part of set_cookie's domain the store_cookie axiom does not
#       cover -- is unreachable from delete_cookie. The caller-reachable tokens
#       are the F2P/P2P literals + the call-site value
#       settings.SESSION_COOKIE_SAMESITE (Django's system check restricts it to
#       {None,'Lax','Strict','None'}).
#   (2) NAME. Morsel.set refuses a name outside the header grammar's alphabet and
#       any casing of the nine names reserved for the header's own attributes, so
#       under such a name NOTHING is recorded and delete_cookie raises CookieError
#       instead of returning. The model states that domain as
#       Requires(is_storable_name(key)), so this leg RUNS the real patched
#       delete_cookie and checks the predicate against it in both directions --
#       every in-domain name returns (the Ensures are about a cookie that exists)
#       and every out-of-domain name raises (nothing outside is claimed) -- plus
#       that every name the real call sites and the F2P/P2P tests reach is in the
#       domain, so the restriction excludes no input the change is about.
_CONTAINMENT_PROBE = r'''
import random
import sys

# --- (1) the POLICY dimension ------------------------------------------------
# The policy/samesite tokens the model (delete_cookie) can actually flow to the
# store_cookie axiom / set_cookie callee. From the F2P/P2P tests and the two
# call sites (settings.SESSION_COOKIE_SAMESITE; Django system check forces it
# into {None,'Lax','Strict','None'}), plus the falsey None/'' that map to the
# empty list in the model:
caller_reachable = [None, "", "lax", "Lax", "LAX", "none", "None", "NONE",
                    "nOnE", "strict", "Strict", "STRICT"]

# set_cookie's ONLY domain restriction beyond the store_cookie axiom's coverage
# is the ValueError raised when a NON-empty samesite is not in (lax,none,strict)
# (case-insensitive). Containment requires every caller-reachable token to be
# either falsey (not forwarded) or a valid token (no raise).
VALID_LOWER = {"lax", "none", "strict"}
bad = []
for tok in caller_reachable:
    if tok in (None, ""):
        continue  # falsey -> empty list in the model -> not forwarded, no raise
    if tok.lower() not in VALID_LOWER:
        bad.append(tok)

if bad:
    print("CONTAINMENT VIOLATION: caller-reachable samesite token(s) outside "
          "the set_cookie no-raise domain (would hit the ValueError path the "
          "store_cookie axiom does not model): %r" % bad)
    sys.exit(1)

# --- (2) the NAME dimension --------------------------------------------------
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, SECRET_KEY="x" * 50, ALLOWED_HOSTS=["*"],
                       DATABASES={}, INSTALLED_APPS=[],
                       SESSION_COOKIE_SAMESITE="Lax")
django.setup()
from django.http import HttpResponse   # noqa: E402  (also installs SameSite)

# model.py's is_storable_name, transcribed on the code-point carrier.
LEGAL_CP = set(range(48, 58)) | set(range(65, 91)) | set(range(97, 123)) | set(
    [33, 35, 36, 37, 38, 39, 42, 43, 45, 46, 58, 94, 95, 96, 124, 126])
RESERVED = ("expires", "path", "comment", "domain", "max-age", "secure",
            "httponly", "version", "samesite")


def lower_cp(c):
    return c + 32 if 65 <= c <= 90 else c


def is_storable_name(name):
    cps = [ord(ch) for ch in name]
    if len(cps) == 0:
        return False
    for c in cps:
        if c not in LEGAL_CP:
            return False
    folded = "".join(chr(lower_cp(c)) for c in cps)
    return folded not in RESERVED


def real_returns(name):
    """Does the REAL patched expiry routine RETURN (emitting a cookie) on this
    name, or refuse the request outright?"""
    resp = HttpResponse()
    try:
        resp.delete_cookie(name, samesite="none")
    except Exception:
        return False
    return name in resp.cookies


# 2a. every name the real call sites / tests reach must be INSIDE the domain,
# else the precondition would exclude an input the change is about.
call_site_names = [settings.SESSION_COOKIE_NAME, "messages", "sessionid", "c",
                   "__Secure-c", "__Host-c", "__Secure-", "__Host-", "x",
                   "cookie_name", "csrftoken", "__Secure-sessionid"]
outside = [n for n in call_site_names if not is_storable_name(n)]
if outside:
    print("CONTAINMENT VIOLATION: caller-reachable cookie name(s) OUTSIDE the "
          "model's Requires(is_storable_name(key)) domain -- the precondition "
          "would reject an input the change is about: %r" % outside)
    sys.exit(1)

# 2b. is_storable_name == "the real routine returns", both directions, over the
# full single-character ASCII sweep, the nine reserved names in five casings,
# the empty name, a non-ASCII sample, and 20k fuzz names.
mismatch = []
n_names = 0


def probe(name):
    global n_names
    n_names += 1
    if real_returns(name) != is_storable_name(name):
        mismatch.append(name)


for cp in range(0x20, 0x7f):
    for nm in (chr(cp), "a" + chr(cp), chr(cp) + "a"):
        probe(nm)
for r in RESERVED:
    for nm in (r, r.upper(), r.capitalize(), r + "x", "x" + r):
        probe(nm)
probe("")
for cp in (0xE9, 0x131, 0x130, 0x212A, 0x17F, 0x1E9E, 0x3B1, 0x5D0, 0x4E2D):
    for nm in (chr(cp), "a" + chr(cp)):
        probe(nm)
rng = random.Random(13195)
alpha = [chr(c) for c in range(0x20, 0x7f)] + ["é", "K", "İ"]
for _ in range(20000):
    probe("".join(rng.choice(alpha) for _ in range(rng.randint(0, 6))))

if mismatch:
    print("CONTAINMENT VIOLATION: is_storable_name disagrees with the real "
          "patched delete_cookie's accept/refuse decision on %d name(s) "
          "(first 10: %r) -- the model's name domain is not the domain in which "
          "an expiry cookie exists" % (len(mismatch), mismatch[:10]))
    sys.exit(1)

# --- (3) the REACH dimension -------------------------------------------------
# The store_cookie axiom puts NO restriction on the path and the domain, so
# containment there is a claim that the real setter has no refusal path on those
# values at all -- it records them without inspecting them. If it DID refuse some
# value, the model would be reaching outside the axiom's domain on it. Measured
# directly on the real patched routine: it must return, and the emitted cookie
# must carry the value verbatim, for every reach value probed.
reach_fixed = ["", "/", "/example/", "/a/b", "/a b", "/;x", "/,y", '/"q"',
               "/x=y", "/" * 8, "/\u00e9", "/\u4e2d"]
dom_fixed = ["", ".example.com", ".example.local", "sub.a.b", "a b", ";x",
             "=v", ".\u00e9xample"]
reach_bad = []
n_reach = 0
frag = ["a", "b/", "example", "-", ".", "\u00e9", " ", ";", "1", "x=y"]
rng_r = random.Random(131953)
reach_cases = [(pp, dd) for pp in reach_fixed for dd in dom_fixed]
for _ in range(5000):
    pp = "/" + "".join(rng_r.choice(frag) for _ in range(rng_r.randint(0, 3)))
    dd = "." + "".join(rng_r.choice(frag) for _ in range(rng_r.randint(1, 3)))
    reach_cases.append((pp, dd))
for pp, dd in reach_cases:
    n_reach += 1
    resp = HttpResponse()
    try:
        resp.delete_cookie("c", path=pp, domain=dd)
    except Exception as exc:          # a refusal path the axiom does not model
        reach_bad.append((pp, dd, type(exc).__name__))
        continue
    mm = resp.cookies["c"]
    if (pp and mm["path"] != pp) or (dd and mm["domain"] != dd):
        reach_bad.append((pp, dd, (mm["path"], mm["domain"])))

if reach_bad:
    print("CONTAINMENT VIOLATION: the real cookie machinery does NOT record every "
          "reach value verbatim -- the store_cookie axiom claims the path and the "
          "domain are recorded without inspection, so an unrestricted reach in the "
          "model would be reaching outside the axiom's domain on %d value(s) "
          "(first 5: %r)" % (len(reach_bad), reach_bad[:5]))
    sys.exit(1)

print("CONTAINMENT OK: every caller-reachable samesite token (%d) is falsey or "
      "a valid {lax,none,strict} value -- the set_cookie ValueError raise path "
      "(the only part of set_cookie's domain outside the store_cookie axiom) is "
      "UNREACHABLE from delete_cookie; and the name domain is EXACT: "
      "is_storable_name agrees with the real patched delete_cookie's "
      "return-vs-CookieError decision on all %d names probed (full ASCII sweep, "
      "the 9 reserved names x 5 casings, the empty name, non-ASCII, 20k fuzz), "
      "with all %d call-site/test names inside it; and the reach dimension needs "
      "no restriction because the machinery has no refusal path on it: the real "
      "patched routine returned and recorded the value verbatim on all %d "
      "(path, domain) pairs probed (separators, spaces, quotes and non-ASCII "
      "included)."
      % (len(caller_reachable), n_names, len(call_site_names), n_reach))
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-real-callees-sound",
        "axiom": "store_cookie + expiry_secure",  # A-consumed axiom + A-reference deep model
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "runs axiom_check.py verbatim in the GOLD-PATCHED image (Django "
                     "only, stdlib). It validates (a) the A-consumed store_cookie axiom "
                     "== the real UNCHANGED set_cookie AS THE EXPIRY INVOKES IT (the "
                     "elapsed lifetime stamped; secure accumulated; the reach path, the "
                     "host domain and the samesite attribute each installed verbatim "
                     "when non-empty and installing nothing of their own when empty) and "
                     "(b) the A-reference deep model expiry_secure + verbatim forwarding "
                     "+ the reach the routine was asked for == the real CHANGED "
                     "post-patch delete_cookie, over the names x {None,'',lax/Lax/LAX,"
                     "none/None/NONE/nOnE,strict/Strict/STRICT} x reach x {secure} cross "
                     "product + 4000 fuzz (10240 axiom + 7300 reference cases), fuzzing "
                     "case folding, the missing-prefix boundary, wrong-case prefixes and "
                     "both falsey preimages of each present-or-absent argument. The "
                     "CUMULATIVE clauses (the ones stated against Old(...)) are measured "
                     "where they say something: a block of cases gives the morsel a "
                     "PRE-EXISTING record through the same real setter first, so the "
                     "secure accumulation, the policy survival and the "
                     "installs-nothing-of-its-own reach clauses are checked against an "
                     "observed pre-state rather than only from a fresh morsel. Exit 0 "
                     "iff every observation agrees; any disagreement => AXIOM-UNSOUND.",
    },
    {
        "id": "ax-containment",
        "axiom": "store_cookie",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _CONTAINMENT_PROBE,
        "rationale": "containment over BOTH dimensions on which the cookie machinery "
                     "refuses a request outright, neither of which the store_cookie "
                     "axiom models. (1) POLICY: the axiom does not model set_cookie's "
                     "ValueError raise path for an invalid samesite token (mapping.md "
                     "S3.1: 'the raise path is out of the consumed domain'), so the "
                     "probe asserts every samesite token the model/caller can actually "
                     "reach (the F2P/P2P literals + the call-site settings.SESSION_"
                     "COOKIE_SAMESITE, which Django's system check restricts to {None,"
                     "'Lax','Strict','None'}) is falsey or a valid {lax,none,strict} "
                     "value, so the raise path is UNREACHABLE from delete_cookie. "
                     "(2) NAME: Morsel.set records nothing under a name outside the "
                     "header grammar's alphabet or under any casing of the nine "
                     "reserved attribute names -- delete_cookie raises CookieError and "
                     "emits no cookie -- which is what Requires(is_storable_name(key)) "
                     "states. That makes this leg an EQUIVALENCE to measure, not an "
                     "argument to make: the probe RUNS the real patched delete_cookie "
                     "and asserts is_storable_name agrees with its return-vs-raise "
                     "decision in both directions over the full 0x20-0x7e sweep in "
                     "three shapes, the 9 reserved names x 5 casings, the empty name, "
                     "9 non-ASCII code points and 20k seeded fuzz names (20349 total), "
                     "and that all 12 call-site/F2P/P2P names are INSIDE the domain, so "
                     "the precondition excludes no input the change is about. "
                     "(3) REACH: the axiom restricts the path and the domain NOT AT ALL, "
                     "which is itself a containment claim -- that the machinery records "
                     "them without inspecting them and so has no refusal path there. The "
                     "probe measures it, running the real patched routine on 5096 "
                     "(path, domain) pairs including separators, spaces, quotes and "
                     "non-ASCII, and asserting it returns and records each value "
                     "verbatim. A caller-reachable token or name outside the consumed "
                     "domain => AXIOM-TOO-WEAK-FOR-CALLER; a name on which the predicate "
                     "and the real routine disagree => the model's domain is not the "
                     "domain in which an expiry cookie exists; a reach value the "
                     "machinery refuses => the unrestricted reach is not contained.",
    },
]
