# properties.py — G-PBT falsification battery for django__django-13195 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried over,
# the mechanics re-expressed against this backend's carrier. Each SPEC case is a FULL
# Solution.lean variant sharing the FROZEN spec byte-for-byte (only the impl region —
# and, where a positive reproves, the proof body — is edited), checked by variant_scope
# before the verifier runs. Every expect="reject" case carries a refutation `witness`:
# a self-contained snippet that ELABORATES against the rival and FAILS on the frozen
# solution, so the rejection is attributable to the spec and not to a tactic script that
# merely stopped matching a reshaped impl.
#
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json)
# ----------------------------------------------------------------------
# THREE obligations, not one — this bundle models the deletion contract plus the two
# configured call sites that instantiate it. The carrier is the WHOLE RESPONSE, threaded in
# and out: a routine acting on a response is observed as the response it leaves behind,
# given the response it was handed. A `Response` carries its cookie container
# (`CookieJar := String → Option Cookie`), the request fields its content is declared to
# depend on, the value of every other header field, its status, and its body; and one
# stored `Cookie` carries EVERY component a stored cookie is able to carry — the two the
# container RENDERS the entry under (`key`, `codedValue`) and the ten attributes it can hold
# — not only the ones a write has an argument for. The two rendered components are distinct
# from the container INDEX and from the read-back payload respectively: the container emits
# `key=codedValue` ahead of every attribute, so an entry filed under one name and rendered
# under another, or reading back an empty payload while rendering a non-empty one, is a
# different line on the wire.
#
#   correct_deleteCookie (resp) (key path : String) (domain samesite : Option String)
#     preconditions `keyAccepted key` (the container will store a cookie under that name at
#     all) and `samesiteValid samesite` (the policy is absent, empty, or one of the three
#     accepted values); postcondition `problem_spec_deleteCookie` is the conjunction of the
#     container contract `deletesCookie` and a TOTAL frame:
#       (E0) jar key = some c              -- an entry exists under the requested name: the
#                                             write lands on the entry the caller asked
#                                             about, not one derived from it
#       (EK) c.key      = key              -- the entry is RENDERED under the caller's name.
#                                             A SECOND identity clause, not a restatement of
#                                             E0: E0 pins the name the container FILES the
#                                             entry under, EK the name the entry emits, and
#                                             the two are separate components that a
#                                             re-stamping impl can move apart
#       (EC) c.codedValue = valueEncode "" -- the entry is RENDERED with the ENCODING of the
#                                             cleared payload, which is the quoted empty
#                                             payload `""` and not the empty string. A second
#                                             payload clause, not a restatement of E1: E1
#                                             pins what the entry reads back, EC what it puts
#                                             on the wire
#       (E1) c.value    = ""               -- the payload is cleared
#       (E2) c.maxAge   = some 0           -- the zero lifetime is RECORDED. The lifetime is
#                                             an option: an entry no write supplied one for
#                                             records `none`, an entry a write recorded zero
#                                             on records `some 0`, and those are DIFFERENT
#                                             entries rendered differently
#       (E3) c.expires  = epochExpires     -- the standard deletion stamp
#       (E4) c.path     = path             -- requested path recorded
#       (E5) c.domain   = domainAfter resp.cookies key domain     -- requested domain when
#                                             one is supplied, else what the entry had
#       (E6) c.samesite = samesiteAfter resp.cookies key samesite -- requested policy when
#                                             truthy, else what the entry had
#       (E7) c.secure   = secureAfter resp.cookies key (deleteSecure key samesite)
#                                          -- marked when the name's prefix OR a cross-site
#                                             policy requires it (a write can only ADD it)
#       (E8) c.httpOnly = httpOnlyAfter resp.cookies key false    -- adds no marking of its
#                                             own
#       (E9/E10) c.comment / c.version = what the entry already had  -- the two attributes a
#                                             write has NO argument for come back exactly as
#                                             they were: a deletion can neither stamp nor
#                                             clear them
#       (F)  ∀ k ≠ key, jar k = resp.cookies k    -- the CONTAINER frame: every other name
#                                             the response carried a cookie under is left
#                                             holding what it held, and no second entry
#                                             appears beside the one written
#       (T)  result = { resp with cookies := result.cookies }   -- the TOTAL frame: the
#                                             result IS the response handed in with its
#                                             container replaced. Stated by REBUILDING the
#                                             response rather than by listing the components
#                                             that must not move, so every component the
#                                             model carries — the declared dependencies,
#                                             each header field, the status, the body — is
#                                             framed whether or not a clause names it
#   correct_messagesDelete (resp) (cookieName) (domain sessionSamesite) — the contract at the
#     default path with the CONFIGURED domain and policy threaded through, INCLUDING (T), so
#     that site's deletion moves nothing else about the response either.
#   correct_sessionDelete  (resp) (name sessionPath) (domain sessionSamesite) — the container
#     contract with the CONFIGURED path, domain and policy threaded through, PLUS its own
#     frame: the result is the response handed in with its container replaced AND its
#     declared dependencies extended by the request's own cookies
#     (`varies := variesAfter resp.varies ["Cookie"]`). `variesAfter` models the real
#     declaration primitive: each field is appended in the order given, after the fields
#     already declared, unless one of that name is declared already (compared without regard
#     to case), and a declaration including the wildcard collapses to the wildcard alone.
#
# E7 is the load-bearing clause: `deleteSecure` is a DISJUNCTION of a key-prefix test and a
# case-insensitive cross-site-policy test. E6 is the second (the policy must survive into
# the recorded entry at all). E1-E4 and E8-E10 pin the components a deletion stamps or
# leaves alone; EK and EC pin the two components the entry is RENDERED with; E0, F and T are
# the STATE clauses, and they are what makes "which cookie was deleted, what happened to the
# others, and what else about the response moved" observables rather than assumptions.
#
# THE RESPONSE CARRIER, and why this battery is stated over it (SPEC REPAIR, three times)
# --------------------------------------------------------------------------------------
# The FIRST revision modeled a deletion as a single pure `Cookie` value: the obligation was
# `problem_spec_deleteCookie key path domain samesite (result : Cookie)` and the impl
# returned the record a write would build. An adversarial audit showed that projection
# admits wrong implementations whose faithful patches do not resolve, in three independent
# directions:
#   * A SECOND WRITE was invisible. Under a value model an intermediate write is a pure term
#     the impl may discard, so an impl that wrote the deletion and then wrote the same name
#     again at a different path satisfied every clause. In the real routine both writes hit
#     the response's container and the SECOND one is what the client sees.
#   * The PAYLOAD and the httpOnly marking had no representation at all.
#   * WHICH ENTRY the write landed in was modeled by a `name` FIELD on the returned record
#     rather than by the container, which pins the name the impl REPORTS and not the name the
#     container ends up keyed by, and says nothing about the entries beside it.
# That repair replaced the value carrier with the CONTAINER carrier. A SECOND adversarial
# audit then found the container carrier admitted four more wrong implementations, all of
# them harness-confirmed non-resolving, and all four of the SAME shape — an observable the
# carrier did not represent, so requiring it was vacuous or impossible:
#   * The lifetime was a plain number whose DEFAULT WAS ZERO, so "no lifetime recorded" and
#     "the lifetime zero recorded" were the same value and an impl that never supplied one
#     satisfied `c.maxAge = 0`. The real write primitive records the directive only when a
#     lifetime is supplied, and an unset one emits nothing; the harness pins the emitted
#     header exactly. Repaired by making the lifetime an OPTION and requiring `some 0`.
#   * The modeled `Cookie` was a PROJECTION of the stored cookie, carrying eight of its ten
#     attributes. Two attributes the write primitive has no argument for were omitted, so an
#     impl that stamped either of them on the deleted entry was unconstrained — and both are
#     rendered to the client. A frame over a projection only frames the projection. Repaired
#     by carrying every attribute a stored cookie carries, in both directions (a deletion can
#     neither stamp nor clear the two it cannot supply), and — more importantly — by stating
#     the frame as a REBUILD (T) instead of an enumeration, so the next unmodeled component
#     is framed without anyone having to think of it.
#   * The session site's CO-LOCATED HEADER EFFECT had no counterpart in the carrier at all,
#     so an impl that omitted it was VACUOUSLY satisfied. Repaired by lifting the carrier
#     from the container to the whole response and giving the session obligation its own
#     declaration clause.
# That repair kept the container carrier and completed it over the ATTRIBUTES. A THIRD
# adversarial audit (2026-08-15T23:53Z) then broke it the same way once more, on the one part
# of the stored cookie that is not an attribute at all:
#   * `Morsel.OutputString` emits `"%s=%s" % (self.key, self.coded_value)` BEFORE any
#     attribute, and the carrier had a field for neither. The entry's own RENDERED name is not
#     the container INDEX (an entry can be filed under `sessionid` and rendered as
#     `SESSIONID`), and its RENDERED payload is not the payload it reads back
#     (`value_encode('')` is `('', '""')`, so the gold entry reads back `''` and renders `""`).
#     Both were therefore FREE: two attacks kept the index, every modeled attribute and the
#     whole-response frame exactly right, verified with clean axioms, and their faithful
#     patches did not resolve — emitting `SESSIONID=""` and `sessionid="deleted"` instead of
#     `sessionid=""`. Repaired by giving the entry both rendered components as fields distinct
#     from the index and from `value`, modeling the container's own payload encoding
#     (`valueEncode`, the model of `http.cookies._quote` — legal-alphabet payloads render as
#     themselves, everything else quoted with the backslash/octal escaping, and the empty
#     payload is NOT legal so it renders as `""`), and pinning both in the postcondition as
#     EK and EC. The carrier now holds all TWELVE components of a `Morsel`
#     (`_key`, `_value`, `_coded_value` + the nine `_reserved` attributes), so the
#     correspondence is total rather than one enumeration deep.
# Consequently E2's option encoding, E9/E10, EK, EC, T, and the session declaration clause are
# NEW, and thirteen rivals below are the cases those repairs need: riv-unrecorded-lifetime,
# riv-lifetime-only-with-policy, riv-stamp-annotation, riv-stamp-protocol-version,
# riv-clear-unsupplied-attributes, riv-write-extra-header, riv-reset-status-and-body,
# riv-session-omits-dependency, riv-session-declares-wrong-field,
# riv-session-clobbers-declaration, riv-session-declares-only-when-undeclared,
# riv-session-collapses-to-wildcard, riv-session-lowercases-field,
# riv-messages-declares-dependency, riv-restamp-rendered-name and
# riv-restamp-rendered-payload. The rivals landed by the first repair are all RETAINED —
# they refute just as well through the new carrier, which is the point: an observable
# survives a carrier change, only its expression moves.
#
# THE LESSON THE THREE REPAIRS SHARE, since it is the one that keeps costing. All three
# audits broke the spec the same way: not by finding a clause that was wrong, but by finding
# an observable the CARRIER did not expose, where no postcondition over that carrier could
# have helped. Determinacy over a projection is determinacy about the projection. The
# structural defenses landed against a recurrence are (a) the option encoding, so "unset"
# cannot masquerade as a written default anywhere, (b) modeling the stored cookie in FULL
# rather than the attributes a write happens to set, and (c) the TOTAL frame (T), which is the
# only one of the three that generalizes: it frames components the model carries but no clause
# names, so a component someone forgets to enumerate is still pinned.
# The third audit is the measured cost of (b) having been read as "every ATTRIBUTE" rather
# than "every COMPONENT": the write primitive stamps three things that are not attributes at
# all (the entry's own name, its payload and its RENDERED payload), two of which had no field,
# and (c) could not reach them because a total frame over a partial carrier is still partial.
# The carrier is now enumerated against `Morsel`'s own slots — `_key`, `_value`,
# `_coded_value` and the nine `_reserved` attributes, twelve in total — so the enumeration has
# an external stopping point instead of resting on whichever components someone thought of.
#
# CARRIER NOTE — the oracle is GROUNDED, so there is no echo attack. `deleteSecure` is a
# total transparent Bool over the arguments (no opaque callee, no answer-key), so
# assigning it directly is the honest cheapest CORRECT impl (pos-inline-decision below),
# not an ungrounded-oracle echo; a WRONG sub-decision fails E7 (the partial-domain
# rivals). This mirrors the nagini sibling's GROUNDED-ORACLE NOTE exactly.
#
# WITNESS MECHANICS — what this carrier does and does not compute. Measured per direction,
# because the two directions of the prefix test behave DIFFERENTLY:
#   * the FALSE direction COMPUTES ONLY WHEN THE STRINGS DIVERGE AT CODE POINT 0.
#     `("c").startsWith "__Secure-" = false` and `("c").startsWith "__Host-" = false` both
#     close by plain `decide` (verified by build): the instance reduces as soon as the first
#     code point differs. But a key that SHARES the prefix's leading code points and diverges
#     later does NOT reduce — `("__Secure-c").startsWith "__Host-" = false` leaves `decide`
#     stuck, because reduction has to walk the shared `__` before it can see the mismatch and
#     gets stuck on the same `String.startsWith` opacity the TRUE direction hits. So "the
#     false direction computes" is a claim about the LITERAL PAIR, not about the direction;
#     `riv-drop-secure-prefix` below is witnessed under both facts conditioned for exactly
#     that reason.
#   * the TRUE direction does NOT. `("__Host-c").startsWith "__Host-" = true` leaves `decide`
#     stuck ("did not reduce to isTrue or isFalse"); `decide +kernel`, `rfl`, `simp`,
#     `simp [String.startsWith]`, `unfold String.startsWith; decide`, `norm_num`, and
#     `grind` were each built and each failed. Only `decide +native` closes it, and a
#     compiler-trusting tactic is banned in a witness, so a witness that needs the flag
#     forced FROM THE KEY must CONDITION on that one term.
#   * the case fold does not compute under `decide` either, but DOES via its unfolding lemma
#     + normalizer: `rw [String.toLower, String.map_eq]; decide` closes
#     `("none").toLower = "none"`, so `simp [..., String.toLower, String.map_eq]` reduces the
#     cross-site test at a literal policy. The same route discharges the `keyAccepted`
#     precondition's reserved-name check at a literal name, and the declaration oracle's
#     case-insensitive already-declared comparison at literal field names
#     (`riv-session-declares-only-when-undeclared`, whose witness needs it).
#   * the CONTAINER is a function, so a container-frame violation is stated by APPLYING the
#     result at the disturbed name: `∀ k ≠ key, jar k = resp.cookies k` is refuted by
#     exhibiting that name (`exact ⟨"c-shadow", by decide, by simp⟩`), and the name
#     disequality at two literals is decidable.
#   * the TOTAL frame (T) is a record equation, so a violation of it is stated by PROJECTING
#     the equation onto the disturbed component with `congrArg` — `congrArg Response.varies`,
#     `congrArg Response.status`, `congrArg Response.headers` — and, for the header field
#     (itself a function), applying the projected equation at the disturbed field with
#     `congrFun`. This is the same move as the container frame's, one level up. Every witness
#     that refutes T or the session declaration clause is written this way and each was BUILT
#     against both subjects before landing.
# Consequence: only the rivals whose discriminating point needs a PREFIXED key condition on
# the carrier. Every `= false` prefix fact at a key that diverges from the prefix at code
# point 0 is DISCHARGED, not assumed; the one `= false` fact that does not reduce is
# conditioned and named as such. Each hypothesis is TRUE at its literal (not merely
# non-contradictory): `#eval` over the frozen file prints `true` for
# `("__Host-c").startsWith "__Host-"` and `("__Secure-c").startsWith "__Secure-"`, `false`
# for `("__Secure-c").startsWith "__Host-"`, and `"none"` for `("None").toLower` — evidence
# stronger than the gate's consistency probe (which only fails a witness whose binders derive
# `False`, and was ALSO run against every conditioning witness here without deriving `False`).
#
# WHY THE UNIQUENESS LANE IS EXHAUSTIVE (machine-checked, not argued). The entry clauses pin
# all twelve components of the entry the write lands in — the two it is RENDERED with and the
# ten attributes — F pins the container everywhere else,
# and T pins the whole response around it, so each postcondition DETERMINES the post-state:
#   problem_spec_deleteCookie   r k p d s x -> x = implementation_deleteCookie   r k p d s
#   problem_spec_messagesDelete r n   d s x -> x = implementation_messagesDelete r n   d s
#   problem_spec_sessionDelete  r n q d s x -> x = implementation_sessionDelete  r n q d s
# was stated as an `example` over the frozen file and BUILT. So no impl can satisfy any of
# these specs and differ observably from the frozen one at any input.
# AND THAT IS EXACTLY THE CLAIM THAT MISLED THREE TIMES, so it is recorded with its caveat
# attached: determinacy is a statement about the MODELED SURFACE only. Every audit that broke
# this bundle broke a spec whose determinacy result held — the first over a carrier that hid
# the payload, the marking, the container's other entries and any write after the first; the
# second over a carrier that hid attribute presence, two of the stored cookie's attributes,
# and the session site's header effect; the third over a carrier that hid the entry's own
# RENDERED name and RENDERED payload, the two components the container emits FIRST. Whether
# the carrier exposes enough observables is
# G-EQ/G-CONF's question, not this gate's, and no amount of determinacy answers it. The
# rivals below are regression evidence that each clause is individually load-bearing, which
# determinacy does not establish.
# RE-DERIVED at each revision, with real builds (including this one — all three `example`s
# were rebuilt against the EK/EC carrier and close): the determinacy `example`s were restated
# over the frozen file and built, and wrong impls the battery did not contain — a
# lowercase-folded forwarded policy, an absent-policy collapsed onto `some ""`, a secure flag
# forced by any truthy policy, each prefix disjunct dropped separately, a fold-less
# cross-site comparison, a path conditioned on domain presence, a maxAge derived from the
# path, an expiry stamp taken from the entry's prior value, a wrong path at the messages
# site, the session name forwarded as its path, and a declaration made before the deletion
# rather than after (which COMMUTES and is therefore correct, and is admitted) — were each
# built against the frozen spec and each behaved as the spec requires.
#
# EARLIER AUDIT FINDINGS THAT STILL STAND (kept because they are corrections, not claims
# about a carrier that has since changed):
#   * the missing reorder positive. An audit tried nagini's `pos-control-reorder` as an
#     out-of-band probe, found it VERIFIES, and concluded the omission cost no coverage.
#     That inference is wrong in the direction this gate exists to catch: a probe an auditor
#     ran once and did not land is not coverage. It is landed as pos-commuted-disjunction.
#   * two false uniqueness claims in the rationales. Enumerating the witness points
#     mechanically refuted "no other witness holds samesite at [`some \"\"`]" (riv-not-
#     expired and riv-no-expiry-stamp share that tuple) and "every other witness holds [the
#     domain] at `none`" (two call-site witnesses hold a present domain). Neither case's
#     rejection depended on the claim, so both rationales are corrected in place rather than
#     the cases being dropped.
#
# LANES THAT DO NOT PORT (see 'assessment' in the submitted payload)
# -----------------------------------------------------------------
#   * FRAME/PERMISSION MUTATION, the MECHANISM — nagini's two MANDATORY rivals
#     (`frame-mutate-key`, `frame-mutate-policy`) wrote THROUGH a half-permission
#     reference. That mechanism is genuinely not expressible here: Lean is referentially
#     transparent, so there is no aliasing, no fractional permission, and no store into a
#     caller's value for a rival to attempt. What DOES port is the OBSERVABLE the
#     permission was protecting — that the decision and the recorded attributes are read
#     from the CALLER's arguments rather than from a value the routine substituted for
#     them — and on this carrier that is expressed by REBINDING the argument locally before
#     it is read. Both halves are landed as rivals rather than argued away:
#       - `riv-fabricate-key-prefix` shadows `key` with a prefix-bearing name, so the
#         decision is self-controlled instead of read from the caller's key — the exact
#         observable `frame-mutate-key` defended, and it is REJECTED;
#       - `riv-coerce-policy-to-crosssite` shadows `samesite` with the cross-site value,
#         the observable `frame-mutate-policy` defended, and it is likewise REJECTED.
#     An earlier revision of this manifest recorded the whole CLASS as inexpressible and
#     shipped neither. That was wrong: only the permission mechanism is inexpressible.
#     Note that the state-threaded carrier gives the lane a THIRD member the value carrier
#     could not express — `riv-discard-carried-cookies` substitutes an empty container for
#     the caller's, which is the closest this backend comes to clobbering a caller's state.
#   * DIVERGENCE / NON-TERMINATION — the nagini sibling ships no `diverge-*` /
#     `nonterm-*` / `weak-diverge` case, and on lean the class is vacuous regardless:
#     `implementation_deleteCookie` is a total Lean `def`, so a diverging impl cannot be
#     written at all. (This is NOT the velvet `partial`-semantics spec hole of
#     the corpus-wide termination-semantics finding; that disposition does not apply to this backend.)
#   * ADMISSIBILITY — nagini's `admiss-selfcall` established that the fractional-
#     permission Requires admits a normal F2P-shaped input. An earlier revision of this
#     manifest argued the lane away here, on the ground that the reject witnesses already
#     instantiate the precondition at `none`, `some ""`, and each accepted policy value.
#     That argument is insufficient: a reject witness shows the SPEC is violable at a point,
#     not that the OBLIGATION is satisfiable there, and PRECOND-TOO-STRONG on a total
#     carrier is exactly the obligation being unsatisfiable at an F2P-shaped input. The lane
#     is LANDED as `adm-f2p-crosssite-point` below, and the spec repair made it load-bearing
#     rather than formal: the precondition is now a CONJUNCTION (`keyAccepted` as well as
#     `samesiteValid`), and a name predicate is exactly the kind of clause that can be
#     accidentally unsatisfiable at the very input the instance is about. So the case
#     discharges `keyAccepted "c"`, `samesiteValid (some "none")` AND the full postcondition
#     at that input before closing the frozen obligation verbatim.
#   * AXIOM_TESTS — dropped; the axiom lane is G-AX's job and this gate ignores it. This
#     bundle consumes NO axiom anyway (the write primitive is modeled deeply).
from pathlib import Path

INSTANCE = "django__django-13195"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -------------------------------------------------------------------------
# Each lies ENTIRELY inside an impl-start/impl-end region (except _PROOF_DELETE, which is
# the proof body a reproving positive replaces) and is unique in _BASE.

# The decision line of the deletion routine's impl.
_DECISION = "  let secure := deleteSecure key samesite\n"

# The decision line + the write: the whole impl body of the deletion routine.
_BODY = (
    "  let secure := deleteSecure key samesite\n"
    "  return setCookie resp key \"\" (some 0) epochExpires path domain secure false"
    " samesite\n"
)

# The two call-site impl bodies.
_SESSION_CALL = (
    "  let deleted := implementation_deleteCookie resp name sessionPath domain"
    " sessionSamesite\n"
    "  return varyMarked deleted [\"Cookie\"]\n"
)
_MESSAGES_CALL = (
    "  return implementation_deleteCookie resp cookieName \"/\" domain sessionSamesite\n"
)

# The frozen proof body of the deletion obligation, swapped only by the positives whose
# reshaped decision needs an honest reproof of the byte-identical theorem statement, and
# by the admissibility case (which PREPENDS to it).
_PROOF_DELETE = (
    "  intro resp key path domain samesite _ _\n"
    "  unfold problem_spec_deleteCookie deletesCookie\n"
    "  refine ⟨⟨?_, ?_⟩, ?_⟩\n"
    "  · simp [implementation_deleteCookie, setCookie, httpOnlyAfter, maxAgeAfter]\n"
    "  · intro k hk\n"
    "    simp [implementation_deleteCookie, setCookie, hk]\n"
    "  · simp [implementation_deleteCookie, setCookie]\n"
)

for _a in (_DECISION, _BODY, _SESSION_CALL, _MESSAGES_CALL, _PROOF_DELETE):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"

# The two frame goals a reproving positive needs, factored out: BOTH are insensitive to
# the decision's shape (neither the container frame nor the whole-response frame mentions
# the secure flag at all), so every reproof below closes them the same way and differs
# only in how it discharges the written entry.
_FRAME_HALF = (
    "  · intro k hk\n"
    "    simp [implementation_deleteCookie, setCookie, hk]\n"
    "  · simp [implementation_deleteCookie, setCookie]\n"
)

# A response already carrying an unrelated cookie, used by the witnesses that refute the
# container frame from the discarding side. Declared BY THE WITNESS (so it exists in both
# builds) rather than by the variant, which a witness may not be stated over.
_WJAR = (
    "def wresp : Response :=\n"
    "  { emptyResponse with cookies := fun k =>\n"
    "      if k = \"other\" then some { defaultCookie with value := \"keep\","
    " path := \"/o\" }\n"
    "      else none }\n\n"
)

# A response that already declares a dependency and already carries an unrelated header
# field, status and body, used by the witnesses that refute the whole-response frame and
# the dependency-declaration clause on a NON-empty prior declaration.
_WRESP2 = (
    "def vresp : Response :=\n"
    "  { cookies := fun _ => none, varies := [\"Accept-Encoding\"],\n"
    "    headers := fun h => if h = \"X-Sbu\" then \"1\" else \"\",\n"
    "    status := 404, body := \"b\" }\n\n"
)

# A response whose entry ALREADY carries the two attributes a write has no argument for,
# used by the witness that refutes them from the CLEARING side — the only sub-domain where
# "left as it was" and "unset" come apart.
_ARESP = (
    "def aresp : Response :=\n"
    "  { emptyResponse with cookies := fun k =>\n"
    "      if k = \"c\" then some { defaultCookie with comment := \"keep\","
    " version := \"9\" }\n"
    "      else none }\n\n"
)

# The simp set that computes this carrier at literal inputs: the spec, the deletion's
# container contract, the impl under attack, the write primitive, the empty response, and
# the six helpers a write's merge goes through. Shared by every witness so that no case's
# rejection can be an artifact of a hand-tuned unfolding.
_SIMP = (
    "  simp [problem_spec_deleteCookie, deletesCookie, implementation_deleteCookie,"
    " setCookie,\n"
    "        emptyResponse, storedOrDefault, defaultCookie, maxAgeAfter, domainAfter,\n"
    "        samesiteAfter, secureAfter, httpOnlyAfter"
)
_SIMP_END = "]\n"


def _witness(comment, statement, extra="", tail=""):
    """A witness: comment, statement, the shared simp set (+extra lemmas), then tail."""
    return (comment + statement + _SIMP + (", " + extra if extra else "")
            + _SIMP_END + tail).rstrip()


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-inline-decision: structurally-different but CORRECT impl. The named local holding
# the decision is INLINED into the write call, so the impl is one expression instead of a
# let-binding; the value is identical on every input. The frozen theorem statements are
# byte-identical AND the frozen proof bodies still close (`simp` sees through the inlining
# either way) — a faithful restructure with no reproof, no new axiom/lemma/sorry. If it
# FAILED => SPEC-TOO-STRONG (the postcondition would be over-fit to one syntactic shape).
_POS_INLINE = _swap(
    _BASE, _BODY,
    "  return setCookie resp key \"\" (some 0) epochExpires path domain"
    " (deleteSecure key samesite)\n    false samesite\n",
)

# pos-short-circuit-decision: a genuinely DIFFERENT shape for the same decision. The
# disjunction is re-expressed as an explicit short-circuit — test the key prefix first and
# only consult the policy when the prefix test fails — which is the control-flow form the
# behavior is usually written in, and is logically identical (`a || b` = `if a then true
# else b`). This changes the impl's structure enough that the frozen script no longer
# closes, so the positive REPROVES the byte-identical theorem statement inside
# proof-start/proof-end: split on the prefix test and discharge each branch. No helper
# lemma, no new axiom, no sorry, no weakened obligation. If it FAILED => SPEC-TOO-STRONG
# (E7 over-fit to the disjunction's syntactic form rather than its truth value).
_POS_SHORTCIRCUIT = _swap(
    _swap(
        _BASE, _BODY,
        "  let prefixed := key.startsWith \"__Secure-\" || key.startsWith \"__Host-\"\n"
        "  let secure := if prefixed then true\n"
        "                else (match samesite with\n"
        "                      | some s => s != \"\" && s.toLower == \"none\"\n"
        "                      | none   => false)\n"
        "  return setCookie resp key \"\" (some 0) epochExpires path domain secure false"
        " samesite\n",
    ),
    _PROOF_DELETE,
    "  intro resp key path domain samesite _ _\n"
    "  unfold problem_spec_deleteCookie deletesCookie\n"
    "  refine ⟨⟨?_, ?_⟩, ?_⟩\n"
    "  · by_cases hp : (key.startsWith \"__Secure-\" || key.startsWith \"__Host-\")"
    " = true\n"
    "    · simp [implementation_deleteCookie, setCookie, httpOnlyAfter, maxAgeAfter,\n"
    "        secureAfter, deleteSecure, hp]\n"
    "    · simp only [Bool.not_eq_true] at hp\n"
    "      simp [implementation_deleteCookie, setCookie, httpOnlyAfter, maxAgeAfter,\n"
    "        secureAfter, deleteSecure, hp]\n"
    + _FRAME_HALF,
)

# pos-commuted-disjunction: the direct port of nagini's `pos-control-reorder`, which
# commutes the two disjuncts of the decision. The cross-site-policy test is moved to the
# FRONT of the disjunction and the two prefix tests follow it, which is value-identical on
# every input because `||` is commutative and both operands are total pure Bools. This is
# a DIFFERENT soundness question from the two positives above, and neither of them asks
# it: pos-inline-decision only removes a let-binding (the disjunction's own term is
# untouched), and pos-short-circuit-decision re-associates `a || b` into `if a then true
# else b` while keeping the prefix tests FIRST. So without this case the battery carries no
# evidence that E7 is insensitive to the ORDER of its disjuncts — the exact over-fitting
# nagini's reorder positive exists to detect. The reshape breaks the frozen script, so the
# positive REPROVES the byte-identical theorem statement by handing `simp` the
# associativity/commutativity of `||` and nothing else. If it FAILED => SPEC-TOO-STRONG
# (E7 pinned to one arrangement of a commutative disjunction).
_POS_COMMUTED = _swap(
    _swap(
        _BASE, _DECISION,
        "  let secure := (match samesite with\n"
        "                 | some s => s != \"\" && s.toLower == \"none\"\n"
        "                 | none   => false) || key.startsWith \"__Secure-\"\n"
        "                            || key.startsWith \"__Host-\"\n",
    ),
    _PROOF_DELETE,
    "  intro resp key path domain samesite _ _\n"
    "  unfold problem_spec_deleteCookie deletesCookie\n"
    "  refine ⟨⟨?_, ?_⟩, ?_⟩\n"
    "  · simp [implementation_deleteCookie, setCookie, httpOnlyAfter, maxAgeAfter,\n"
    "      secureAfter, deleteSecure, Bool.or_comm, Bool.or_assoc]\n"
    + _FRAME_HALF,
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the frozen spec
# exactly and edits only an impl region; the frozen proof bodies are left in place (they
# will not close for a reshaped impl, which is precisely WHY the gate reads the WITNESS —
# checked in a file with the obligations removed — rather than the rival's own build).
# ===========================================================================

# --- E7, the decision clause -------------------------------------------------
# riv-drop-crosssite-disjunct: derive the flag from the key prefix ALONE, dropping the
# cross-site-policy disjunct. Correct on every prefixed key and on every non-cross-site
# policy; WRONG exactly when the key carries no prefix AND the policy is the cross-site
# value. This is the pre-patch decision, and the direct port of nagini's
# `weak-drop-none-disjunct`.
_RIV_DROP_CROSSSITE = _swap(
    _BASE, _DECISION,
    "  let secure := key.startsWith \"__Secure-\" || key.startsWith \"__Host-\"\n",
)

# riv-conjoin-decision: replace the disjunction with a CONJUNCTION — the flag is forced
# only when a prefixed key AND a cross-site policy hold together. Correct only on that
# diagonal; WRONG on a prefixed key with any other policy and on an unprefixed key with
# the cross-site policy. Port of nagini's `weak-and-instead-of-or`.
_RIV_CONJOIN = _swap(
    _BASE, _DECISION,
    "  let secure := (key.startsWith \"__Secure-\" || key.startsWith \"__Host-\") &&\n"
    "    (match samesite with\n"
    "     | some s => s != \"\" && s.toLower == \"none\"\n"
    "     | none   => false)\n",
)

# riv-force-on-absent-policy: over-force the flag — the absent-policy arm answers `true`
# instead of `false`, so an unprefixed key with NO policy is marked as needing secure
# transport. This has no nagini counterpart (nagini's carrier maps a falsy policy to the
# empty list, collapsing "absent" into "empty"); on this carrier `Option String`
# distinguishes them, so the `none` arm of the decision is separately attackable. It
# varies the samesite binder to `none`, which no other rival's witness does.
_RIV_FORCE_ABSENT = _swap(
    _BASE, _DECISION,
    "  let secure := key.startsWith \"__Secure-\" || key.startsWith \"__Host-\" ||\n"
    "    (match samesite with\n"
    "     | some s => s != \"\" && s.toLower == \"none\"\n"
    "     | none   => true)\n",
)

# riv-drop-secure-prefix: the decision consults only ONE of the two prefixes. Every other
# E7 rival treats `key.startsWith "__Secure-" || key.startsWith "__Host-"` as a single
# unit, so a decision that honors `__Host-` and silently ignores `__Secure-` would be
# unattacked. WRONG on every `__Secure-`-prefixed key whose policy is not the cross-site
# value.
_RIV_DROP_SECURE_PREFIX = _swap(
    _BASE, _DECISION,
    "  let secure := key.startsWith \"__Host-\" ||\n"
    "    (match samesite with\n"
    "     | some s => s != \"\" && s.toLower == \"none\"\n"
    "     | none   => false)\n",
)

# riv-case-sensitive-crosssite: the cross-site test drops the case fold, comparing the
# policy to the literal lowercase spelling instead of folding it first. Correct at every
# lowercase spelling — the only spelling any other witness probes at the cross-site value —
# and WRONG at every other casing of it.
_RIV_CASE_SENSITIVE = _swap(
    _BASE, _DECISION,
    "  let secure := key.startsWith \"__Secure-\" || key.startsWith \"__Host-\" ||\n"
    "    (match samesite with\n"
    "     | some s => s != \"\" && s == \"none\"\n"
    "     | none   => false)\n",
)

# --- the substituted-input lane (the ported observable of nagini's frame rivals) --------
# riv-fabricate-key-prefix: the routine does not read the CALLER's key when it decides —
# it evaluates the decision at a prefix-bearing name it fabricated, so the decision is
# self-controlled and every deletion is marked as needing secure transport regardless of
# what was requested. The write itself still targets the requested name, so this rival
# isolates the DECISION's provenance: E7 is the sole discriminator. WRONG on every
# unprefixed key whose policy is not the cross-site value.
_RIV_FABRICATE_KEY = _swap(
    _BASE, _DECISION,
    "  let secure := deleteSecure (\"__Host-\" ++ key) samesite\n",
)

# riv-coerce-policy-to-crosssite: the routine does not read the CALLER's policy — it
# rebinds a present `samesite` to the cross-site value before both the decision and the
# forwarding, so the deleted entry records a policy the caller never asked for AND is
# marked as needing secure transport. WRONG on every present non-cross-site policy, and it
# fails E6 and E7 together.
_RIV_COERCE_POLICY = _swap(
    _BASE, _DECISION,
    "  let samesite := samesite.map (fun _ => \"none\")\n"
    "  let secure := deleteSecure key samesite\n",
)

# --- E6, the policy-preservation clause --------------------------------------
# riv-drop-policy-forwarding: the decision is computed correctly but the policy is NOT
# carried into the write (the call is passed `none`), so the deleted entry records no
# policy at all. This is the pre-patch forwarding behavior and the port of nagini's
# `weak-drop-forwarding`.
_RIV_DROP_FORWARD = _swap(
    _BASE, _BODY,
    _DECISION + "  return setCookie resp key \"\" (some 0) epochExpires path domain secure"
    " false none\n",
)

# --- E1-E4, E8: the frame clauses (spec_guide §5) ----------------------------
# These are the referentially-transparent translation of nagini's frame lane: each pins an
# output component the caller supplied (or a constant the deletion must stamp), and each
# rival substitutes something else for it.
# riv-pin-path-to-default: ignore the requested path, always writing the default.
_RIV_PIN_PATH = _swap(
    _BASE, _BODY,
    _DECISION + "  return setCookie resp key \"\" (some 0) epochExpires \"/\" domain secure"
    " false samesite\n",
)

# riv-drop-domain: ignore the requested domain, always writing none.
_RIV_DROP_DOMAIN = _swap(
    _BASE, _BODY,
    _DECISION + "  return setCookie resp key \"\" (some 0) epochExpires path none secure"
    " false samesite\n",
)

# riv-not-expired: the deleted entry is not expired immediately (a nonzero lifetime).
_RIV_NOT_EXPIRED = _swap(
    _BASE, _BODY,
    _DECISION + "  return setCookie resp key \"\" (some 1) epochExpires path domain secure"
    " false samesite\n",
)

# riv-no-expiry-stamp: the deletion carries no expiry stamp.
_RIV_NO_STAMP = _swap(
    _BASE, _BODY,
    _DECISION + "  return setCookie resp key \"\" (some 0) \"\" path domain secure"
    " false samesite\n",
)

# riv-nonempty-payload (landed by the state-carrier repair): the entry is expired and
# stamped correctly but a non-empty payload is stored under the deleted name. Unattackable
# before the repair — the modeled record carried no payload field at all.
_RIV_NONEMPTY_PAYLOAD = _swap(
    _BASE, _BODY,
    _DECISION + "  return setCookie resp key \"deleted\" (some 0) epochExpires path domain"
    " secure false samesite\n",
)

# riv-mark-httponly (landed by the state-carrier repair): the deletion additionally marks
# the entry as script-inaccessible. Also unattackable before the repair, for the same
# reason.
_RIV_MARK_HTTPONLY = _swap(
    _BASE, _BODY,
    _DECISION + "  return setCookie resp key \"\" (some 0) epochExpires path domain secure"
    " true samesite\n",
)

# --- EK and EC, the RENDERED components (landed by the THIRD spec repair) --------------
# Both rivals perform the gold write EXACTLY as gold performs it and then RE-STAMP one of the
# two components the container renders the entry with, leaving the container INDEX, the
# read-back payload, all nine attributes and the whole-response frame untouched. That is the
# precise shape of the two
# attacks that broke the previous revision (`atk_2_morsel_key`, `atk_3_coded_value`): their
# faithful patches re-stamp the stored `Morsel` after `set_cookie` returns
# (`morsel.set(key.upper(), morsel.value, morsel.coded_value)` and
# `morsel.set(morsel.key, morsel.value, '"deleted"')`), emitting `SESSIONID=""` and
# `sessionid="deleted"` where gold emits `sessionid=""`, and both failed F2P 3/5 with P2P
# 382/382. Under the previous carrier neither shape was EXPRESSIBLE in Lean at all — the
# rivals could only park the stamp in a dead `let`, which no postcondition can reject — so
# these two cases are the evidence that the repair made the behavior sayable AND rejected.
_RESTAMP = (
    "  let secure := deleteSecure key samesite\n"
    "  let written := setCookie resp key \"\" (some 0) epochExpires path domain secure"
    " false samesite\n"
    "  return { written with cookies := fun k =>\n"
    "    if k = key then (written.cookies k).map (fun c => { c with %s })\n"
    "    else written.cookies k }\n"
)

# riv-restamp-rendered-name: the entry stays FILED under the caller's name and is RENDERED
# under an upper-cased spelling of it.
_RIV_RESTAMP_NAME = _swap(_BASE, _BODY, _RESTAMP % "key := key.toUpper")

# riv-restamp-rendered-payload: the entry still READS BACK the empty payload and is RENDERED
# with a marker payload.
_RIV_RESTAMP_CODED = _swap(_BASE, _BODY, _RESTAMP % "codedValue := \"\\\"deleted\\\"\"")

# --- E0 and F, the container clauses ----------------------------------------------------
# riv-mistarget-folded-name: the decision is computed from the CALLER's key, every
# attribute is correct, and the policy is threaded — but the write is aimed at a
# case-folded rendering of the requested name instead of the name itself, so the deletion
# lands on a different container entry than the one asked for. This is the shape a
# "normalize the cookie name" refactor takes. WRONG on every requested name that is not
# already lowercase.
_RIV_MISTARGET_FOLDED = _swap(
    _BASE, _BODY,
    _DECISION + "  return setCookie resp key.toLower \"\" (some 0) epochExpires path domain"
    " secure false samesite\n",
)

# riv-mistarget-fixed-slot: the blunt form of the same defect — the write is aimed at one
# fixed name regardless of what was requested, while every attribute is still derived
# correctly from the caller's arguments. Kept alongside the folded-name rival because the
# two fail at different points: this one is wrong at every requested name but the literal,
# the folded one only at names that are not already lowercase.
_RIV_MISTARGET_FIXED = _swap(
    _BASE, _BODY,
    _DECISION + "  return setCookie resp \"sbu-other-slot\" \"\" (some 0) epochExpires path"
    " domain secure false samesite\n",
)

# riv-second-write-other-path (landed by the state-carrier repair, and the reason for it):
# the deletion is written CORRECTLY and then written AGAIN under the same name at a
# different path, so the state the caller is left holding is the second write's. Under the
# previous value carrier the first write was a pure term the impl could discard and this
# shape satisfied every clause — the audit's own attack.
_RIV_SECOND_WRITE = _swap(
    _BASE, _BODY,
    _DECISION
    + "  let resp := setCookie resp key \"\" (some 0) epochExpires path domain secure false"
    " samesite\n"
    + "  return setCookie resp key \"\" (some 0) epochExpires \"/attack\" domain secure false"
    " samesite\n",
)

# riv-shadow-extra-entry (landed by the state-carrier repair): the requested entry is
# written correctly and a SECOND entry is written beside it under a derived name, so the
# response emits a cookie the caller never asked about. This is what clause F forbids and
# nothing else in the battery attacks.
_RIV_SHADOW_ENTRY = _swap(
    _BASE, _BODY,
    _DECISION
    + "  let resp := setCookie resp key \"\" (some 0) epochExpires path domain secure false"
    " samesite\n"
    + "  return setCookie resp (key ++ \"-shadow\") \"\" (some 0) epochExpires path domain"
    " secure false samesite\n",
)

# riv-discard-carried-cookies (landed by the state-carrier repair): the requested entry is
# written correctly but into a FRESH container, so every cookie the response was already
# carrying is dropped. The rest of the response is left EXACTLY as it was, so the
# whole-response frame agrees with gold and clause F is the sole discriminator — the other
# half of it, and the closest a referentially-transparent carrier comes to nagini's
# clobber-the-caller's-state rival.
_RIV_DISCARD_CARRIED = _swap(
    _BASE, _BODY,
    _DECISION
    + "  return { resp with cookies := (setCookie emptyResponse key \"\" (some 0)\n"
    "    epochExpires path domain secure false samesite).cookies }\n",
)

# --- the two configured call sites -------------------------------------------
# riv-session-ignores-configured-path: the session deletion uses the default path instead
# of the configured one.
_RIV_SESSION_PATH = _swap(
    _BASE, _SESSION_CALL,
    "  return implementation_deleteCookie resp name \"/\" domain sessionSamesite\n",
)

# riv-session-drops-configured-policy: the session deletion does not thread the configured
# policy through — the pre-patch call shape at this site.
_RIV_SESSION_POLICY = _swap(
    _BASE, _SESSION_CALL,
    "  return implementation_deleteCookie resp name sessionPath domain none\n",
)

# riv-messages-drops-configured-policy: the messages deletion does not thread the
# configured policy through — the pre-patch call shape at that site.
_RIV_MESSAGES_POLICY = _swap(
    _BASE, _MESSAGES_CALL,
    "  return implementation_deleteCookie resp cookieName \"/\" domain none\n",
)

# riv-messages-drops-configured-domain: the messages deletion drops the configured domain.
_RIV_MESSAGES_DOMAIN = _swap(
    _BASE, _MESSAGES_CALL,
    "  return implementation_deleteCookie resp cookieName \"/\" none sessionSamesite\n",
)

# --- E2', the RECORDED-lifetime clause ---------------------------------------
# The lifetime is an `Option`: an entry no write supplied a lifetime for records NONE, and
# an entry a write recorded the lifetime zero on records SOME ZERO. They are different
# entries and they are rendered differently — one states a lifetime, one states nothing at
# all. So a deletion must RECORD the zero, not merely fail to record anything.
# riv-unrecorded-lifetime: the write is handed no lifetime at all, so the merge leaves the
# entry whatever lifetime it already carried (none, on a container that carried no entry).
_RIV_UNRECORDED_LIFETIME = _swap(
    _BASE, _BODY,
    _DECISION + "  return setCookie resp key \"\" none epochExpires path domain secure"
    " false samesite\n",
)

# riv-lifetime-only-with-policy: the PARTIAL-DOMAIN form — the lifetime is recorded only
# when a truthy policy is being recorded too, and left unsupplied otherwise. Correct on
# every deletion that carries a policy (which includes the configuration the instance is
# about) and wrong on every deletion that carries none.
_RIV_LIFETIME_PARTIAL = _swap(
    _BASE, _BODY,
    _DECISION
    + "  let lifetime := match samesite with\n"
    "                  | some s => if s = \"\" then none else some 0\n"
    "                  | none   => none\n"
    "  return setCookie resp key \"\" lifetime epochExpires path domain secure false"
    " samesite\n",
)

# --- E9/E10, the attributes a deletion cannot supply -------------------------
# A stored cookie carries two attributes a write has no argument for. A write leaves them
# exactly as the entry had them, so a deletion can neither stamp them nor clear them; both
# are rendered to the client, so either direction changes what is emitted.
# riv-stamp-annotation: the deleted entry is additionally annotated.
_RIV_STAMP_COMMENT = _swap(
    _BASE, _BODY,
    _DECISION
    + "  let w := setCookie resp key \"\" (some 0) epochExpires path domain secure false"
    " samesite\n"
    "  return { w with cookies := fun k =>\n"
    "    if k = key then (w.cookies k).map (fun c => { c with comment := \"deleted\" })\n"
    "    else w.cookies k }\n",
)

# riv-stamp-protocol-version: the same defect at the OTHER unsupplied attribute, so neither
# is load-bearing only through the other.
_RIV_STAMP_VERSION = _swap(
    _BASE, _BODY,
    _DECISION
    + "  let w := setCookie resp key \"\" (some 0) epochExpires path domain secure false"
    " samesite\n"
    "  return { w with cookies := fun k =>\n"
    "    if k = key then (w.cookies k).map (fun c => { c with version := \"1\" })\n"
    "    else w.cookies k }\n",
)

# riv-clear-unsupplied-attributes: the opposite direction — the deletion RESETS the two
# attributes it cannot supply instead of leaving them standing. Wrong exactly on a response
# whose entry already carried them, which is the only sub-domain where the two directions
# differ, so this rival is not a near-miss of either stamping rival.
_RIV_CLEAR_ANNOTATIONS = _swap(
    _BASE, _BODY,
    _DECISION
    + "  let w := setCookie resp key \"\" (some 0) epochExpires path domain secure false"
    " samesite\n"
    "  return { w with cookies := fun k =>\n"
    "    if k = key then (w.cookies k).map (fun c =>"
    " { c with comment := \"\", version := \"\" })\n"
    "    else w.cookies k }\n",
)

# --- the WHOLE-RESPONSE frame -----------------------------------------------
# A deletion is a cookie write and nothing else. Every other component of the response it
# was handed — its declared dependencies, each header field, the status, the body — comes
# back exactly as it went in.
# riv-write-extra-header: the deletion additionally writes an unrelated header field.
_RIV_WRITE_HEADER = _swap(
    _BASE, _BODY,
    _DECISION
    + "  let w := setCookie resp key \"\" (some 0) epochExpires path domain secure false"
    " samesite\n"
    "  return { w with headers := fun h =>"
    " if h = \"X-Sbu\" then \"1\" else w.headers h }\n",
)

# riv-reset-status-and-body: the deletion rebuilds the response around the new container
# and resets the status and body to their defaults in the process. This is the shape a
# "return a fresh response" refactor takes, and it is wrong on every response that was not
# already at those defaults.
_RIV_RESET_STATUS = _swap(
    _BASE, _BODY,
    _DECISION
    + "  let w := setCookie resp key \"\" (some 0) epochExpires path domain secure false"
    " samesite\n"
    "  return { cookies := w.cookies, varies := resp.varies, headers := resp.headers,\n"
    "           status := 200, body := \"\" }\n",
)

# --- the session site's DEPENDENCY DECLARATION -------------------------------
# Ending a session leaves the response declaring that its content depends on the request's
# own cookies: whether the session cookie is being cleared is exactly what it depends on,
# and without the declaration a shared cache may serve the clearing response to another
# request. The declaration is APPENDED to whatever the response already declared, without
# regard to case, with the wildcard absorbing everything.
# riv-session-omits-dependency: the session deletion declares nothing.
_RIV_NO_VARY = _swap(
    _BASE, _SESSION_CALL,
    "  return implementation_deleteCookie resp name sessionPath domain sessionSamesite\n",
)

# riv-session-declares-wrong-field: a declaration is made, but of a different field, so the
# response still fails to declare the dependency it actually has.
_RIV_VARY_WRONG_FIELD = _swap(
    _BASE, _SESSION_CALL,
    "  let deleted := implementation_deleteCookie resp name sessionPath domain"
    " sessionSamesite\n"
    "  return varyMarked deleted [\"Accept-Encoding\"]\n",
)

# riv-session-clobbers-declaration: the declaration REPLACES whatever the response already
# declared instead of being added to it, so a response that already declared a dependency
# loses it. Correct on a response that declared nothing — the ordinary case — and wrong on
# every other, which is what makes it a partial-domain rival rather than a blunt one.
_RIV_VARY_CLOBBER = _swap(
    _BASE, _SESSION_CALL,
    "  let deleted := implementation_deleteCookie resp name sessionPath domain"
    " sessionSamesite\n"
    "  return { deleted with varies := [\"Cookie\"] }\n",
)

# riv-session-declares-only-when-undeclared: the declaration is made only when the response
# declared nothing at all. The complement of the clobber rival: it agrees with gold exactly
# where that one does, and is wrong on the same sub-domain by dropping the addition rather
# than dropping the prior declaration.
_RIV_VARY_ONLY_IF_EMPTY = _swap(
    _BASE, _SESSION_CALL,
    "  let deleted := implementation_deleteCookie resp name sessionPath domain"
    " sessionSamesite\n"
    "  return if resp.varies = [] then varyMarked deleted [\"Cookie\"] else deleted\n",
)

# riv-session-collapses-to-wildcard: the response is declared to depend on EVERYTHING
# instead of on the request's cookies — a declaration that is technically not wrong about
# the dependency but destroys the response's cacheability entirely, and is not the
# declaration the routine makes.
_RIV_VARY_WILDCARD = _swap(
    _BASE, _SESSION_CALL,
    "  let deleted := implementation_deleteCookie resp name sessionPath domain"
    " sessionSamesite\n"
    "  return varyMarked deleted [\"*\"]\n",
)

# riv-session-lowercases-field: the declared field is spelled in lower case. The comparison
# that decides whether a field is ALREADY declared ignores case, so this rival agrees with
# gold about whether to add anything; what it changes is the spelling that ends up declared,
# which is what the response carries.
_RIV_VARY_LOWERCASE = _swap(
    _BASE, _SESSION_CALL,
    "  let deleted := implementation_deleteCookie resp name sessionPath domain"
    " sessionSamesite\n"
    "  return varyMarked deleted [\"cookie\"]\n",
)

# riv-messages-declares-dependency: the OVER-reaching direction, at the site that must not
# declare anything — deleting the messages payload cookie is an ordinary deletion and
# leaves the response's declared dependencies alone. Without this case the declaration
# clause is only ever attacked from the omitting side.
_RIV_MESSAGES_VARY = _swap(
    _BASE, _MESSAGES_CALL,
    "  let deleted := implementation_deleteCookie resp cookieName \"/\" domain"
    " sessionSamesite\n"
    "  return varyMarked deleted [\"Cookie\"]\n",
)


# ===========================================================================
# ADMISSIBILITY — must VERIFY (else PRECOND-TOO-STRONG).
# ===========================================================================
# adm-f2p-crosssite-point: the impl is left VERBATIM; only the proof body changes, and only
# by PREPENDING a `have` that discharges BOTH preconditions and the whole postcondition at
# the concrete F2P-shaped input (an ordinarily-named cookie deleted with the cross-site
# policy — the configuration whose secure flag the instance is about), before closing the
# frozen obligation with the frozen script verbatim. On a total carrier this is what the
# admissibility lane tests: the obligation being UNSATISFIABLE at an F2P-shaped input is
# the analogue of a precondition that rejects a normal input, and a reject witness cannot
# show satisfiability (it shows the spec is violable there, which is the opposite
# direction). The state-carrier repair made the case load-bearing rather than formal, by
# adding `keyAccepted` to the precondition. If it FAILED => PRECOND-TOO-STRONG.
_ADM_F2P = _swap(
    _BASE, _PROOF_DELETE,
    "  have hf2p : keyAccepted \"c\" ∧ samesiteValid (some \"none\") ∧\n"
    "      problem_spec_deleteCookie emptyResponse \"c\" \"/\" none (some \"none\")\n"
    "        (implementation_deleteCookie emptyResponse \"c\" \"/\" none (some \"none\")) :="
    " by\n"
    "    refine ⟨⟨by decide, ?_, by decide⟩, ?_, ?_⟩\n"
    "    · rw [String.toLower, String.map_eq]; decide\n"
    "    · right; right; left; rw [String.toLower, String.map_eq]; decide\n"
    "    · unfold problem_spec_deleteCookie deletesCookie implementation_deleteCookie\n"
    "      refine ⟨⟨?_, ?_⟩, ?_⟩\n"
    "      · simp [setCookie, httpOnlyAfter, maxAgeAfter]\n"
    "      · intro k hk\n"
    "        simp [setCookie, hk]\n"
    "      · simp [setCookie]\n"
    + _PROOF_DELETE,
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-inline-decision",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_INLINE,
        "rationale": (
            "structurally-different but CORRECT impl: the named local holding the "
            "decision is inlined into the write call, so the impl is one expression "
            "rather than a let-binding, computing the identical value at every input. All "
            "three frozen `theorem correct_*` statements are byte-identical and the frozen "
            "proof bodies still close — a faithful restructure with no reproof, no new "
            "axiom/lemma/sorry, and no weakened obligation. Must verify; else the "
            "postcondition is over-fit to one syntactic impl shape => SPEC-TOO-STRONG. "
            "Also the grounded-oracle control: because `deleteSecure` is a total "
            "transparent Bool over the arguments, assigning it directly is the honest "
            "cheapest correct impl, not an ungrounded echo — every WRONG sub-decision "
            "below fails clause E7."
        ),
    },
    {
        "id": "pos-short-circuit-decision",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_SHORTCIRCUIT,
        "rationale": (
            "a genuinely different SHAPE for the same decision: the disjunction is "
            "re-expressed as an explicit short-circuit (test the key prefix first, "
            "consult the policy only when it fails), which is logically identical since "
            "`a || b` = `if a then true else b`. The reshape breaks the frozen script, so "
            "this positive REPROVES the byte-identical theorem statement honestly inside "
            "proof-start/proof-end — split on the prefix test and discharge each branch — "
            "with no helper lemma, no new axiom, no sorry, and the obligation left intact. "
            "Must verify; else clause E7 is pinned to the disjunction's syntactic form "
            "rather than its truth value => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-commuted-disjunction",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_COMMUTED,
        "rationale": (
            "the decision's two disjuncts are COMMUTED: the cross-site-policy test is "
            "moved to the front and the two prefix tests follow it, which is "
            "value-identical on every input because `||` is commutative and both operands "
            "are total pure Bools. The direct port of the one nagini positive this battery "
            "had no analogue of (`pos-control-reorder`), and it asks a soundness question "
            "neither other positive does: pos-inline-decision only removes a let-binding, "
            "leaving the disjunction's own term untouched, while pos-short-circuit-decision "
            "re-associates `a || b` into `if a then true else b` with the prefix tests "
            "still FIRST. So without it the battery carries no evidence that clause E7 is "
            "insensitive to the ORDER of its disjuncts — precisely the over-fitting a "
            "reorder positive exists to detect. The reshape breaks the frozen script, so "
            "this positive REPROVES the byte-identical theorem statement by handing `simp` "
            "the associativity and commutativity of `||` and nothing else: no helper "
            "lemma, no new axiom, no sorry, and the obligation left intact. Must verify; "
            "else E7 is pinned to one arrangement of a commutative disjunction => "
            "SPEC-TOO-STRONG."
        ),
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "adm-f2p-crosssite-point",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADM_F2P,
        "rationale": (
            "the obligation must be SATISFIABLE at an F2P-shaped input, which on a total "
            "carrier is the analogue of a precondition admitting a normal input. The impl "
            "is verbatim; the proof body only PREPENDS a `have` discharging BOTH "
            "preconditions (`keyAccepted \"c\"`, `samesiteValid (some \"none\")`) and the "
            "full postcondition at the concrete input `(emptyResponse, \"c\", \"/\", none, some "
            "\"none\")` — an ordinarily-named cookie deleted with the cross-site policy "
            "from a response carrying nothing else, the configuration the instance is "
            "about — and then closes the byte-identical frozen obligation with the frozen "
            "script verbatim. No new axiom/lemma/sorry and no weakened obligation. The "
            "lane matters more since the state-carrier repair, which added `keyAccepted` "
            "to the precondition: a name predicate is exactly the kind of clause that can "
            "be accidentally unsatisfiable at the input the instance is about, and a "
            "reject witness cannot detect that (it shows the spec is VIOLABLE at a point, "
            "not that the obligation HOLDS there). If it FAILED => PRECOND-TOO-STRONG (the "
            "obligation would be unsatisfiable at exactly the input the instance is about, "
            "making every other verify in this battery vacuous where it matters)."
        ),
    },

    # ---- uniqueness rivals: clause E7, the decision ----
    {
        "id": "riv-drop-crosssite-disjunct",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_CROSSSITE,
        "refinement": (
            "this is literally the pre-patch decision: the flag is derived from the key "
            "prefix alone, dropping the cross-site-policy disjunct. A faithful patch "
            "keeping this shape still emits an UNSET secure flag when an ordinarily-named "
            "cookie is deleted with the cross-site policy, so the F2P assertion that the "
            "deleted cookie's secure flag is set in exactly that configuration fails and "
            "the instance does not resolve. A verifying rival here would therefore be a "
            "true verify-does-not-imply-resolve break, not an artifact."
        ),
        "rationale": (
            "REJECTED by clause E7 (`c.secure = secureAfter resp.cookies key (deleteSecure key "
            "samesite)`), whose oracle is a DISJUNCTION. Witness probes an unprefixed key "
            "with the cross-site policy, from a response carrying nothing — the sub-domain "
            "where the dropped disjunct is the only thing making the flag true, and where "
            "the container's merge cannot supply it either. It is UNCONDITIONAL: both "
            "prefix tests are at the `= false` direction, which this carrier does compute, "
            "so they are discharged by `decide` rather than assumed, and the case fold is "
            "computed via `String.map_eq`. Nothing here is taken on hypothesis. Varies the "
            "samesite binder to the cross-site value and the key binder to an unprefixed "
            "name. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            "-- unprefixed key + cross-site policy, empty container: gold forces the flag\n"
            "-- via the cross-site disjunct, the rival cannot see it. Fully computed: the\n"
            "-- two prefix tests are the `= false` direction (discharged by `decide`) and\n"
            "-- the case fold reduces via String.map_eq.\n",
            "example : ¬ problem_spec_deleteCookie emptyResponse \"c\" \"/\" none"
            " (some \"none\")\n"
            "      (implementation_deleteCookie emptyResponse \"c\" \"/\" none (some \"none\"))"
            " := by\n",
            "deleteSecure, String.toLower, String.map_eq",
            "  constructor <;> decide\n",
        ),
    },
    {
        "id": "riv-conjoin-decision",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CONJOIN,
        "refinement": (
            "conjoining the two tests makes the flag true only on the diagonal. A faithful "
            "patch of this shape emits an UNSET flag both for a prefix-named cookie "
            "deleted with an ordinary policy — breaking the long-standing PASS_TO_PASS "
            "assertion that a prefix-named cookie is always deleted with the flag set — "
            "and for an ordinarily-named cookie deleted with the cross-site policy, "
            "breaking the F2P. It resolves nothing."
        ),
        "rationale": (
            "REJECTED by clause E7: the oracle is a disjunction, not a conjunction. This "
            "is the NEAR-MISS of the drop-disjunct rival (it agrees with gold on the "
            "diagonal but ALSO differs on the prefixed-key side), so it is witnessed at a "
            "DIFFERENT point: a prefixed key with an ordinary non-cross-site policy, "
            "where gold forces the flag from the prefix and the rival's conjunction is "
            "false. Varies the key binder to a prefix-named cookie and the samesite binder "
            "to an ordinary policy value. Conditions on exactly ONE term, and only because "
            "it must: this is the `= true` prefix direction, the sole fact this carrier "
            "cannot reduce (see WITNESS MECHANICS — seven tactics were built against it and "
            "all failed). The hypothesis is TRUE at that literal, confirmed out-of-band by "
            "`decide +native`, which a shipped witness may not use. If it VERIFIES => "
            "SPEC-TOO-WEAK (the disjunction would collapse to a conjunction)."
        ),
        "witness": _witness(
            "-- prefixed key + ordinary policy: gold forces the flag from the prefix, the\n"
            "-- rival's conjunction is false because the policy is not the cross-site one.\n",
            "example (hh : (\"__Host-c\" : String).startsWith \"__Host-\" = true) :\n"
            "    ¬ problem_spec_deleteCookie emptyResponse \"__Host-c\" \"/\" none"
            " (some \"lax\")\n"
            "      (implementation_deleteCookie emptyResponse \"__Host-c\" \"/\" none"
            " (some \"lax\")) := by\n",
            "deleteSecure, hh, String.toLower, String.map_eq",
        ),
    },
    {
        "id": "riv-force-on-absent-policy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FORCE_ABSENT,
        "refinement": (
            "over-forcing the flag on an ABSENT policy is not a resolving patch either: "
            "the default deletion of an ordinarily-named cookie with no policy configured "
            "would start emitting the secure flag, which the PASS_TO_PASS assertions on "
            "the default deletion (they require the flag UNSET in that configuration) "
            "reject. The F2P is untouched, so the instance does not resolve — a verifying "
            "rival here is a verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by clause E7 from the OVER-forcing side: the oracle's absent-policy "
            "arm is false, and this rival answers true. This clause arm has no nagini "
            "counterpart — nagini's carrier maps a falsy policy onto the empty list, "
            "collapsing 'absent' into 'empty', while `Option String` here keeps them "
            "distinct — so the `none` arm of the decision is separately attackable. It is "
            "the ONLY witness holding the samesite binder at `none`, which is what varies "
            "that binder away from the `some _` value every other rival probes. It is "
            "UNCONDITIONAL: both prefix tests are the computable `= false` direction and are "
            "discharged by `decide`. If it VERIFIES => SPEC-TOO-WEAK (the absent-policy arm "
            "of the decision would be unconstrained)."
        ),
        "witness": _witness(
            "-- unprefixed key, ABSENT policy: gold leaves the flag unset, the rival\n"
            "-- forces it. Fully computed — the two `= false` prefix tests are discharged\n"
            "-- by `decide`.\n",
            "example : ¬ problem_spec_deleteCookie emptyResponse \"c\" \"/\" none none\n"
            "      (implementation_deleteCookie emptyResponse \"c\" \"/\" none none) := by\n",
            "deleteSecure",
            "  constructor <;> decide\n",
        ),
    },
    {
        "id": "riv-drop-secure-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_SECURE_PREFIX,
        "refinement": (
            "honoring one prefix and ignoring the other is not a resolving patch: a cookie "
            "named with the ignored prefix would be deleted with the secure flag UNSET, so "
            "the long-standing assertions that a prefix-named cookie is always deleted with "
            "the flag set fail for that half of the prefix family, while the F2P is "
            "untouched — verify-does-not-resolve."
        ),
        "rationale": (
            "REJECTED by clause E7. Closes a real coverage gap: every other E7 rival treats "
            "the two prefix tests as a single unit (drop-disjunct, conjoin and "
            "force-on-absent all keep both; the fabricate rival supplies a `__Host-` name), "
            "so a decision honoring only ONE of the two prefixes would be unattacked and no "
            "other witness holds the key binder at a `__Secure-`-prefixed name with the "
            "container's merge unable to supply the flag. Witness probes a "
            "`__Secure-`-prefixed key with an ordinary policy, where gold forces the flag "
            "from that prefix and the rival cannot see it. It conditions on TWO terms and "
            "both are forced by the carrier: the `= true` fact at the honored prefix, and — "
            "unusually — the `= false` fact at the ignored one, because this key SHARES the "
            "prefix's leading code points (`__`) so reduction gets stuck before it reaches "
            "the mismatch (see WITNESS MECHANICS; `decide` on it was built and failed). Both "
            "are TRUE at the literal, printed by `#eval` out-of-band as `true` and `false`. "
            "If it VERIFIES => SPEC-TOO-WEAK (only one of the two prefix disjuncts would be "
            "load-bearing)."
        ),
        "witness": _witness(
            "-- `__Secure-`-prefixed key + ordinary policy: gold forces the flag from that\n"
            "-- prefix, the rival consults only the other one. Both prefix facts are\n"
            "-- conditioned: the `= true` direction never reduces here, and this key shares\n"
            "-- the other prefix's leading code points so its `= false` fact does not\n"
            "-- reduce either.\n",
            "example (hs : (\"__Secure-c\" : String).startsWith \"__Secure-\" = true)\n"
            "    (hh : (\"__Secure-c\" : String).startsWith \"__Host-\" = false) :\n"
            "    ¬ problem_spec_deleteCookie emptyResponse \"__Secure-c\" \"/\" none"
            " (some \"lax\")\n"
            "      (implementation_deleteCookie emptyResponse \"__Secure-c\" \"/\" none"
            " (some \"lax\")) := by\n",
            "deleteSecure, hs, hh, String.toLower, String.map_eq",
        ),
    },
    {
        "id": "riv-case-sensitive-crosssite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CASE_SENSITIVE,
        "refinement": (
            "dropping the case fold is not a resolving patch: the cross-site policy is "
            "configurable as a plain string and is conventionally written capitalized, so a "
            "deletion configured that way would emit no secure flag — which is precisely "
            "the browser-visible condition the instance exists to fix. The F2P asserting "
            "the flag is set for a cross-site deletion fails at every casing but the "
            "all-lowercase one, so the instance does not resolve."
        ),
        "rationale": (
            "REJECTED by clause E7, whose cross-site test folds the policy's case before "
            "comparing. Every other witness that reaches the cross-site value spells it "
            "all-lowercase (`some \"none\"`), which is exactly where a fold-less comparison "
            "AGREES with gold, so without this case the fold itself is load-bearing in no "
            "case at all. Witness holds the samesite binder at a capitalized spelling of "
            "the cross-site value — a point no other witness in the battery visits — where "
            "gold folds and forces the flag and the rival's literal comparison is false. "
            "UNCONDITIONAL: the key's two prefix tests are the computable `= false` "
            "direction (discharged by `decide`) and the fold reduces via `String.map_eq`. "
            "If it VERIFIES => SPEC-TOO-WEAK (the case-insensitivity of the cross-site test "
            "would be unconstrained)."
        ),
        "witness": _witness(
            "-- capitalized cross-site policy: gold folds the case and forces the flag,\n"
            "-- the rival compares against the lowercase literal and does not. Fully\n"
            "-- computed — the two `= false` prefix tests are discharged by `decide`.\n",
            "example : ¬ problem_spec_deleteCookie emptyResponse \"c\" \"/\" none"
            " (some \"None\")\n"
            "      (implementation_deleteCookie emptyResponse \"c\" \"/\" none (some \"None\"))"
            " := by\n",
            "deleteSecure, String.toLower, String.map_eq",
            "  constructor <;> decide\n",
        ),
    },

    # ---- uniqueness rivals: the substituted-input lane ----
    {
        "id": "riv-fabricate-key-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FABRICATE_KEY,
        "refinement": (
            "no faithful patch corresponds to this and that is the point: the deletion "
            "routine INSPECTS the cookie name it was given to decide whether secure "
            "transport must be forced, and never substitutes a different name for it. A "
            "patch of this shape would force the flag on EVERY deletion, so the "
            "long-standing assertions that an ordinarily-named cookie is deleted with the "
            "flag UNSET fail, while the F2P is untouched — verify-does-not-resolve. Its "
            "purpose is to test whether the decision clause can be satisfied by a "
            "self-supplied key rather than the requested one, which is the observable "
            "nagini's mandatory frame rival defended with a read-only permission."
        ),
        "rationale": (
            "REJECTED by clause E7, whose oracle `deleteSecure key samesite` is stated "
            "over the CALLER's key: the rival evaluates the same decision at a name it "
            "fabricated, so the two disagree wherever the fabricated prefix is the only "
            "prefix. The write itself still lands on the requested name, so E0/F agree with "
            "gold and E7 is the sole discriminator — which is what this case is evidence "
            "for. Witness probes an unprefixed key with an ordinary policy: gold leaves the "
            "flag unset, the rival forces it. It conditions on ONE term, the `= true` prefix "
            "fact at the fabricated name, which is the only direction this carrier cannot "
            "compute (see WITNESS MECHANICS); the `= false` facts at the requested name are "
            "discharged by `decide`, not assumed. If it VERIFIES => SPEC-TOO-WEAK (the "
            "decision could be satisfied by a substituted key, and E7 would constrain "
            "nothing about provenance)."
        ),
        "witness": _witness(
            "-- unprefixed key + ordinary policy: gold leaves the flag unset; the rival\n"
            "-- decides at a name it fabricated and forces it. Only the fabricated name's\n"
            "-- prefix test is conditioned (the `= true` direction does not reduce here);\n"
            "-- the requested name's two `= false` tests are discharged by `decide`.\n",
            "example (hp : (\"__Host-c\" : String).startsWith \"__Host-\" = true) :\n"
            "    ¬ problem_spec_deleteCookie emptyResponse \"c\" \"/\" none (some \"lax\")\n"
            "      (implementation_deleteCookie emptyResponse \"c\" \"/\" none (some \"lax\"))"
            " := by\n",
            "deleteSecure, hp, String.toLower, String.map_eq",
            "  decide\n",
        ),
    },
    {
        "id": "riv-coerce-policy-to-crosssite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_COERCE_POLICY,
        "refinement": (
            "the deletion routine READS the requested policy — both to decide the secure "
            "flag and to record the attribute — and never substitutes a different policy "
            "for it. A patch of this shape would rewrite every present policy to the "
            "cross-site value, so the F2P asserting that the deleted cookie records the "
            "REQUESTED policy fails (it would record the cross-site value instead), as do "
            "the header assertions at both configured call sites. It resolves nothing, and "
            "it is the observable nagini's second mandatory frame rival defended."
        ),
        "rationale": (
            "REJECTED by clause E6 AND clause E7 together, both of which are stated over "
            "the CALLER's policy: the rival coerces a present policy to the cross-site "
            "value, so it records the wrong attribute and forces the flag. Witness probes "
            "a present ordinary policy, the sub-domain where the coercion is observable, "
            "and is fully transparent — the shared simp set computes it, no conditioning "
            "and no hypothesis to be satisfiable. Distinct from riv-drop-policy-forwarding, "
            "which records NO policy while keeping E7 correct; this one records a WRONG "
            "policy and breaks E7 too. If it VERIFIES => SPEC-TOO-WEAK (E6/E7 would "
            "constrain nothing about which policy the result came from)."
        ),
        "witness": _witness(
            "-- present ordinary policy: gold records exactly it; the rival substitutes\n"
            "-- the cross-site value for it and additionally forces the secure flag.\n",
            "example : ¬ problem_spec_deleteCookie emptyResponse \"c\" \"/\" none"
            " (some \"lax\")\n"
            "      (implementation_deleteCookie emptyResponse \"c\" \"/\" none (some \"lax\"))"
            " := by\n",
        ),
    },

    # ---- uniqueness rivals: clause E6, policy preservation ----
    {
        "id": "riv-drop-policy-forwarding",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_FORWARD,
        "refinement": (
            "the decision is computed correctly but the requested policy never reaches the "
            "written entry — exactly the pre-patch behavior, where the write primitive was "
            "called without the policy at all. A faithful patch keeping this emits a "
            "deleted cookie carrying NO policy attribute, so the F2P asserting that the "
            "deleted cookie records the requested policy fails, as do the header-level "
            "assertions at both configured call sites. It does not resolve."
        ),
        "rationale": (
            "REJECTED by clause E6 (`c.samesite = samesiteAfter resp.cookies key samesite`), which "
            "is independent of E7 — this rival keeps E7 correct, so E6 is the sole "
            "discriminator. Witness probes a truthy NON-cross-site policy from an empty "
            "container, the sub-domain where E6 bites while E7 agrees with gold on both "
            "sides and the merge has no stored policy to fall back on; fully transparent, "
            "so the shared simp set computes it with no conditioning. Varies the samesite "
            "binder to an ordinary truthy policy. If it VERIFIES => SPEC-TOO-WEAK (the "
            "policy attribute would be unconstrained)."
        ),
        "witness": _witness(
            "-- truthy ordinary policy, empty container: gold records it on the deleted\n"
            "-- entry, the rival drops it and the merge has nothing to restore.\n",
            "example : ¬ problem_spec_deleteCookie emptyResponse \"c\" \"/\" none"
            " (some \"lax\")\n"
            "      (implementation_deleteCookie emptyResponse \"c\" \"/\" none (some \"lax\"))"
            " := by\n",
        ),
    },

    # ---- uniqueness rivals: the frame clauses E1-E4, E8 ----
    {
        "id": "riv-pin-path-to-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PIN_PATH,
        "refinement": (
            "ignoring the requested path and always writing the default is not a "
            "resolving patch: a deletion at a non-default path would emit a cookie scoped "
            "to the root, so the browser never clears the original cookie. The "
            "custom-path deletion assertions (a configured non-default path must appear on "
            "the emitted cookie) fail, and the F2P is untouched — verify-does-not-resolve."
        ),
        "rationale": (
            "REJECTED by clause E4 (`c.path = path`). This is the referentially-"
            "transparent translation of nagini's frame lane: its `frame-mutate-*` rivals "
            "cannot be written here, but the ARGUMENT — an output component not pinned to "
            "its input is a hole a wrong impl can fill — ports directly, and spec_guide §5 "
            "says a lean spec discharges the frame obligation by pinning those components. "
            "Witness varies the path binder to a non-default value, the only witness of "
            "this obligation that moves it. If it VERIFIES => SPEC-TOO-WEAK (the requested "
            "path would be unconstrained)."
        ),
        "witness": _witness(
            "-- non-default path: gold records it, the rival writes the default.\n",
            "example : ¬ problem_spec_deleteCookie emptyResponse \"c\" \"/example/\" none"
            " (some \"lax\")\n"
            "      (implementation_deleteCookie emptyResponse \"c\" \"/example/\" none"
            " (some \"lax\")) := by\n",
        ),
    },
    {
        "id": "riv-drop-domain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_DOMAIN,
        "refinement": (
            "dropping the requested domain emits a host-only deletion for a cookie that "
            "was set on a parent domain, so the original cookie survives. The "
            "custom-domain deletion assertions fail while the F2P is untouched, so a "
            "faithful patch of this shape does not resolve."
        ),
        "rationale": (
            "REJECTED by clause E5 (`c.domain = domainAfter resp.cookies key domain`) — the second "
            "frame clause, same porting argument as the path rival. Note the clause is a "
            "MERGE, not an equality with the argument: a write records a domain only when "
            "one is supplied, so the rival is refuted at a SUPPLIED domain, which is "
            "exactly where the two disagree. Witness varies the domain binder to a PRESENT "
            "domain and independently moves the samesite binder to a third accepted policy "
            "value, so this probe point is distinct from every other. (An earlier revision "
            "said 'every other witness holds it at `none`'. An audit enumerated the witness "
            "points and that was FALSE: the two call-site witnesses "
            "riv-session-drops-configured-policy and riv-messages-drops-configured-domain "
            "also hold a PRESENT domain. What is true, and all this case needs, is that no "
            "other witness of THIS obligation moves the domain binder.) If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            "-- present domain: gold records it, the rival supplies none and the empty\n"
            "-- container leaves the entry with no domain at all.\n",
            "example : ¬ problem_spec_deleteCookie emptyResponse \"c\" \"/\""
            " (some \".example.com\")\n"
            "      (some \"strict\")\n"
            "      (implementation_deleteCookie emptyResponse \"c\" \"/\""
            " (some \".example.com\")\n"
            "        (some \"strict\")) := by\n",
        ),
    },
    {
        "id": "riv-not-expired",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NOT_EXPIRED,
        "refinement": (
            "a deletion that leaves a nonzero lifetime does not delete: the browser keeps "
            "the cookie for that lifetime. Every assertion on the emitted deletion header "
            "(all of which require the zero lifetime) fails, and the F2P is untouched, so "
            "this resolves nothing."
        ),
        "rationale": (
            "REJECTED by clause E2 (`c.maxAge = some 0`) — a frame clause pinning an output "
            "component to a constant rather than to an input, and independent of all the "
            "others. Witness probes the EMPTY policy (`some \"\"`), the falsy-but-present "
            "value that exercises E6's fall-back arm while E2 does the discriminating. (An "
            "earlier revision of this rationale added 'no other witness holds samesite at "
            "that value'; an audit checked the witness points mechanically and that was "
            "FALSE — riv-no-expiry-stamp probes the identical tuple. The claim is dropped "
            "rather than restated, because the shared point is admissible for the reason "
            "riv-no-expiry-stamp's own rationale gives and needs no uniqueness claim to "
            "stand.) If it VERIFIES => SPEC-TOO-WEAK (the lifetime would be "
            "unconstrained)."
        ),
        "witness": _witness(
            "-- empty (falsy) policy: gold writes the zero lifetime, the rival a nonzero\n"
            "-- one.\n",
            "example : ¬ problem_spec_deleteCookie emptyResponse \"c\" \"/\" none (some \"\")\n"
            "      (implementation_deleteCookie emptyResponse \"c\" \"/\" none (some \"\"))"
            " := by\n",
        ),
    },
    {
        "id": "riv-no-expiry-stamp",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NO_STAMP,
        "refinement": (
            "omitting the expiry stamp leaves the deletion relying on the zero lifetime "
            "alone, which the emitted-header assertions reject outright: each pins the "
            "literal deletion stamp on the header. The F2P is untouched, so a faithful "
            "patch of this shape does not resolve."
        ),
        "rationale": (
            "REJECTED by clause E3 (`c.expires = epochExpires`) — the remaining constant "
            "pin, independent of E2: this rival keeps the zero lifetime and drops only the "
            "stamp, so E3 is the sole discriminator. Shares the empty-policy probe point "
            "with the lifetime rival, which is admissible here because the two clauses are "
            "attacked at the same input for the same reason (both are constant pins on the "
            "deletion stamping, neither depends on any input binder) and neither is a "
            "near-miss of the other. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            "-- gold stamps the standard deletion expiry; the rival leaves it unset.\n",
            "example : ¬ problem_spec_deleteCookie emptyResponse \"c\" \"/\" none (some \"\")\n"
            "      (implementation_deleteCookie emptyResponse \"c\" \"/\" none (some \"\"))"
            " := by\n",
            "epochExpires",
        ),
    },
    {
        "id": "riv-nonempty-payload",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NONEMPTY_PAYLOAD,
        "refinement": (
            "a deletion must leave the cookie carrying NOTHING: the client is told to "
            "forget the name, and until it does, the value it holds is what gets sent "
            "back. A faithful patch that stored a marker payload under the deleted name "
            "would emit a deletion header whose value field is that marker, so the "
            "assertions that read the deleted cookie's value back as empty fail — the "
            "messages framework has one for exactly this, on the payload cookie it deletes "
            "— and the header-text assertions, which pin the emitted header literally, "
            "fail with them. The F2P is untouched, so it resolves nothing. Landed with the "
            "state-carrier repair: under the previous value carrier the payload was not "
            "modeled at all, so this shape verified."
        ),
        "rationale": (
            "REJECTED by clause E1 (`c.value = \"\"`), which the state-carrier repair "
            "added — a write's payload argument is one of the attributes the primitive "
            "sets, and the previous carrier simply had no field for it, so nothing pinned "
            "it. Witness probes an ordinary name with an ordinary policy, the point where "
            "every other clause agrees with gold and E1 alone discriminates; fully "
            "transparent under the shared simp set. If it VERIFIES => SPEC-TOO-WEAK (the "
            "deleted cookie's payload would be unconstrained)."
        ),
        "witness": _witness(
            "-- gold clears the payload; the rival stores a marker under the deleted name.\n",
            "example : ¬ problem_spec_deleteCookie emptyResponse \"c\" \"/\" none"
            " (some \"lax\")\n"
            "      (implementation_deleteCookie emptyResponse \"c\" \"/\" none (some \"lax\"))"
            " := by\n",
        ),
    },
    {
        "id": "riv-mark-httponly",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_MARK_HTTPONLY,
        "refinement": (
            "a deletion adds no script-inaccessibility marking of its own: the marking is "
            "the caller's choice on the cookie being SET, and a deletion that added it "
            "would emit a header the assertions pinning the exact emitted deletion header "
            "do not match. The F2P is untouched, so this resolves nothing. Landed with the "
            "state-carrier repair, which added the field."
        ),
        "rationale": (
            "REJECTED by clause E8 (`c.httpOnly = httpOnlyAfter resp.cookies key false`), the other "
            "clause the state-carrier repair added. Note the clause is a MERGE and says "
            "the deletion adds NOTHING, not that the marking is absent: a response that "
            "had already marked the entry keeps it, which is what the real container does. "
            "So the rival is refuted at an entry the container does NOT already carry, "
            "where 'adds nothing' and 'is unmarked' coincide — an empty container, which "
            "is also the shape the deletion is normally reached at. If it VERIFIES => "
            "SPEC-TOO-WEAK (a deletion could silently change the cookie's script "
            "visibility)."
        ),
        "witness": _witness(
            "-- empty container, so the merge carries no marking in: gold adds none, the\n"
            "-- rival marks the deleted entry script-inaccessible.\n",
            "example : ¬ problem_spec_deleteCookie emptyResponse \"c\" \"/\" none"
            " (some \"lax\")\n"
            "      (implementation_deleteCookie emptyResponse \"c\" \"/\" none (some \"lax\"))"
            " := by\n",
        ),
    },

    # ---- uniqueness rivals: the RENDERED components EK and EC ----
    {
        "id": "riv-restamp-rendered-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_RESTAMP_NAME,
        "refinement": (
            "the faithful patch performs the gold `set_cookie` call and then re-stamps the "
            "stored morsel's own name — `morsel = self.cookies[key]; "
            "morsel.set(key.upper(), morsel.value, morsel.coded_value)`. Every attribute is "
            "unchanged and `response.cookies[key]` still retrieves the entry, so nothing a "
            "P2P test reads moves; but `Morsel.OutputString` emits "
            "`\"%s=%s\" % (self.key, self.coded_value)`, so the response sends "
            "`Set-Cookie: SESSIONID=\"\"` where the F2P tests pin `sessionid=\"\"`. Measured "
            "through the official harness at the previous revision (as `atk_2_morsel_key`): "
            "resolved=FALSE, F2P 3ok/2fail (test_session_delete_on_end, "
            "test_session_delete_on_end_with_custom_domain_and_path), P2P 382ok/0fail."
        ),
        "rationale": (
            "REJECTED by clause EK (`c.key = key`), which the third spec repair added. EK is "
            "NOT a restatement of E0: E0 pins the container INDEX the entry is filed at and "
            "this rival files it at exactly the right index — what it moves is the entry's "
            "OWN name, a separate component that the container renders. No other case in the "
            "battery moves it, and before the repair the carrier had no field for it, so the "
            "behavior could not even be WRITTEN in Lean (the attack could only park the "
            "stamp in a dead `let`, which is semantically gold and which no spec can "
            "reject). Witness probes an ordinary lowercase name, where the upper-cased "
            "rendering differs; it needs `String.toUpper` + `String.map_eq` to fold the "
            "spelling, the same route the battery's other case-folding witnesses use. If it "
            "VERIFIES => SPEC-TOO-WEAK (the emitted cookie NAME would be unconstrained)."
        ),
        "witness": _witness(
            "-- gold renders the entry under the name the caller asked to delete; the rival\n"
            "-- files it there and renders it upper-cased.\n",
            "example : ¬ problem_spec_deleteCookie emptyResponse \"c\" \"/\" none"
            " (some \"lax\")\n"
            "      (implementation_deleteCookie emptyResponse \"c\" \"/\" none (some \"lax\"))"
            " := by\n",
            "String.toUpper, String.map_eq",
        ),
    },
    {
        "id": "riv-restamp-rendered-payload",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_RESTAMP_CODED,
        "refinement": (
            "the faithful patch performs the gold `set_cookie` call and then re-stamps only "
            "the stored morsel's CODED payload — `morsel.set(morsel.key, morsel.value, "
            "'\"deleted\"')`. `response.cookies[key].value` still reads back `''`, so every "
            "assertion that reads the payload back passes, but the emitted header becomes "
            "`Set-Cookie: sessionid=\"deleted\"` where the F2P tests pin `sessionid=\"\"`. "
            "Measured through the official harness at the previous revision (as "
            "`atk_3_coded_value`): resolved=FALSE, F2P 3ok/2fail (the same two session "
            "tests), P2P 382ok/0fail."
        ),
        "rationale": (
            "REJECTED by clause EC (`c.codedValue = valueEncode \"\"`), the second clause the "
            "third repair added. EC is NOT a restatement of E1: a `Morsel` carries BOTH the "
            "payload it reads back and the payload it RENDERS, and `value_encode('')` is "
            "`('', '\"\"')` — measured on CPython 3.10.20 — so the gold entry reads back the "
            "empty string and renders the two-character quoted empty payload. E1 pins the "
            "first and says nothing about the second, which is why this rival kept E1 true. "
            "No other case in the battery moves the rendered payload, and before the repair "
            "the carrier had no field for it. Witness probes the same ordinary point as the "
            "name rival and needs `valueEncode` + `String.join` unfolded to compute the "
            "encoding of the empty payload. If it VERIFIES => SPEC-TOO-WEAK (the emitted "
            "cookie VALUE would be unconstrained)."
        ),
        "witness": _witness(
            "-- gold renders the encoding of the cleared payload (the quoted empty payload);\n"
            "-- the rival reads back the empty payload but renders a marker.\n",
            "example : ¬ problem_spec_deleteCookie emptyResponse \"c\" \"/\" none"
            " (some \"lax\")\n"
            "      (implementation_deleteCookie emptyResponse \"c\" \"/\" none (some \"lax\"))"
            " := by\n",
            "valueEncode, String.join",
        ),
    },

    # ---- uniqueness rivals: the container clauses E0 and F ----
    {
        "id": "riv-mistarget-folded-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_MISTARGET_FOLDED,
        "refinement": (
            "a faithful patch of this shape hands the write primitive a case-folded "
            "rendering of the cookie name, and that argument is what SELECTS the container "
            "entry the deletion lands in — so the cookie the caller asked to delete is left "
            "untouched while a differently-named entry is created carrying the deletion "
            "attributes. The browser never clears the original cookie. The assertions that "
            "read the deleted cookie back under the name it was requested under fail, "
            "including the prefix-named cases (whose names are mixed-case by construction), "
            "so the instance does not resolve. This is the exact rival a prior adversarial "
            "audit found VERIFYING against an un-repaired spec, whose faithful patch was "
            "run through the official harness and did not resolve."
        ),
        "rationale": (
            "REJECTED by clause E0 (`result key = some c`) together with F: the requested "
            "name must hold an entry AFTER the call, and under the folded write it holds "
            "whatever it held BEFORE — nothing, at the witness point. Landed against the "
            "first repair (which pinned a `name` field on the returned record) and RETAINED "
            "across the state-carrier repair, which is the point: the observable survived "
            "the carrier change, only its expression moved from a field of the value to the "
            "key of the container. Witness probes a `__Secure-`-prefixed name — one that is "
            "not already lowercase, which is where the fold is observable — and conditions "
            "on nothing about the prefix tests: the discriminating term is the container "
            "application alone, computed via the fold's unfolding lemma and normalizer "
            "(`String.toLower`/`String.map_eq`, the route WITNESS MECHANICS documents). If "
            "it VERIFIES => SPEC-TOO-WEAK (which cookie the deletion targets would be "
            "unconstrained)."
        ),
        "witness": _witness(
            "-- a name that is not already lowercase: gold writes the entry the caller\n"
            "-- named, the rival writes a case-folded rendering of it, so the requested\n"
            "-- name is left holding exactly what it held. The fold reduces via\n"
            "-- String.map_eq.\n",
            "example : ¬ problem_spec_deleteCookie emptyResponse \"__Secure-c\" \"/\" none"
            " (some \"lax\")\n"
            "      (implementation_deleteCookie emptyResponse \"__Secure-c\" \"/\" none"
            " (some \"lax\")) := by\n",
            "String.toLower, String.map_eq",
        ),
    },
    {
        "id": "riv-mistarget-fixed-slot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_MISTARGET_FIXED,
        "refinement": (
            "the blunt form: every attribute is derived correctly from the caller's "
            "arguments but the write is aimed at one fixed container entry, so no requested "
            "cookie is ever cleared and a stray entry is emitted instead. Every assertion "
            "that reads a deleted cookie back under its requested name fails — at both "
            "configured call sites as well as the direct one — so a faithful patch of this "
            "shape resolves nothing. Also found VERIFYING against an un-repaired spec by a "
            "prior audit, with a harness-confirmed non-resolving patch."
        ),
        "rationale": (
            "REJECTED by clause E0. Retained alongside the folded-name rival because the "
            "two are wrong on DIFFERENT sub-domains — this one at every requested name "
            "except the literal it hardcodes, the folded one only at names that are not "
            "already lowercase — so neither is a near-miss of the other, and E0 is shown "
            "load-bearing both when the written name is a constant and when it is derived "
            "from the input. Witness probes an ordinarily-named cookie with an ordinary "
            "policy and is fully transparent: the shared simp set computes the container "
            "application, no conditioning and no hypothesis to satisfy. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            "-- ordinary name: gold writes the entry the caller named, the rival writes a\n"
            "-- fixed one, so the requested name is left holding nothing.\n",
            "example : ¬ problem_spec_deleteCookie emptyResponse \"c\" \"/\" none"
            " (some \"lax\")\n"
            "      (implementation_deleteCookie emptyResponse \"c\" \"/\" none (some \"lax\"))"
            " := by\n",
        ),
    },
    {
        "id": "riv-second-write-other-path",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SECOND_WRITE,
        "refinement": (
            "this is the audit's own attack, and the reason the carrier changed. The "
            "routine writes the deletion correctly and then writes the same name AGAIN at a "
            "different path. In the real routine both writes land in the response's cookie "
            "container, so the client is sent the SECOND one — a cookie scoped to a path "
            "the caller never asked about, which clears nothing. The custom-path deletion "
            "assertions and the exact-header assertions both fail, so a faithful patch of "
            "this shape does not resolve. Under the previous value carrier the first write "
            "was a pure term the impl could simply discard, so this verified: hence the "
            "repair."
        ),
        "rationale": (
            "REJECTED by clause E4 evaluated at the POST-STATE, which is what the "
            "state-threaded carrier makes the result be. The mechanism is the repair's "
            "whole point: `setCookie` maps container to container and the obligation's "
            "`result` is the container the routine leaves behind, so a second write is not "
            "a discardable term but the state the caller observes. Witness probes an "
            "ordinary deletion at the default path and reads the entry back at the "
            "requested name, where the second write's path is what stands. If it VERIFIES "
            "=> SPEC-TOO-WEAK, and specifically the hole the repair closed would be open "
            "again: any number of extra writes could follow a correct one."
        ),
        "witness": _witness(
            "-- gold leaves the entry scoped to the requested path; the rival overwrites\n"
            "-- it with a second write at another path, and the post-state is what the\n"
            "-- obligation reads.\n",
            "example : ¬ problem_spec_deleteCookie emptyResponse \"c\" \"/\" none"
            " (some \"lax\")\n"
            "      (implementation_deleteCookie emptyResponse \"c\" \"/\" none (some \"lax\"))"
            " := by\n",
        ),
    },
    {
        "id": "riv-shadow-extra-entry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SHADOW_ENTRY,
        "refinement": (
            "the requested entry is deleted correctly and a SECOND entry is written beside "
            "it under a derived name, so the response emits a cookie for a name nobody "
            "asked about. This one is honest about its harness status: the assertions read "
            "the entry they asked for and would not notice a stray sibling, so a faithful "
            "patch of this shape would most likely still resolve. It is here as a "
            "SPEC-STRENGTH case, not a resolution case: clause F claims the deletion "
            "disturbs no other name, and an unattacked frame clause is exactly how the "
            "previous carrier came to admit a second write. If the spec cannot see a "
            "gratuitous extra write it cannot see the ones that do change what the client "
            "receives."
        ),
        "rationale": (
            "REJECTED by clause F (`∀ k ≠ key, jar k = resp.cookies k`), which no other case "
            "attacks from this side. The container is a function, so the refutation is "
            "stated by exhibiting the disturbed name and applying the result at it: "
            "`⟨\"c-shadow\", by decide, by simp⟩` — the name disequality at two literals is "
            "decidable and the entry it now holds is not `none`. If it VERIFIES => "
            "SPEC-TOO-WEAK: the spec would constrain only the entry it names and leave the "
            "rest of the response's cookies free, which is the projection the state-carrier "
            "repair exists to remove."
        ),
        "witness": _witness(
            "-- gold disturbs no other name; the rival additionally writes a derived one,\n"
            "-- so the empty container is left holding an entry the caller never asked for.\n",
            "example : ¬ problem_spec_deleteCookie emptyResponse \"c\" \"/\" none"
            " (some \"lax\")\n"
            "      (implementation_deleteCookie emptyResponse \"c\" \"/\" none (some \"lax\"))"
            " := by\n",
            "",
            "  exact ⟨\"c-shadow\", by decide, by simp⟩\n",
        ),
    },
    {
        "id": "riv-discard-carried-cookies",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DISCARD_CARRIED,
        "refinement": (
            "the deletion is written correctly but into a FRESH container, so every cookie "
            "the response was already carrying is thrown away. A faithful patch of this "
            "shape clobbers unrelated cookies on any response that sets one and then "
            "deletes another — a response that deletes two cookies would emit only the "
            "second — so the assertions that delete two names on one response fail and the "
            "instance does not resolve. It also fixes the direction the OTHER half of "
            "clause F guards, which no attribute rival reaches."
        ),
        "rationale": (
            "REJECTED by clause F from the discarding side (the shadow rival attacks the "
            "adding side). Witness must be stated at a container that is NOT empty — that "
            "is the whole content of the case — so it declares one (`wresp`, a response "
            "already carrying an unrelated cookie) rather than referencing anything the "
            "variant declares, and exhibits that name: gold leaves it holding what it held, "
            "the rival drops it. This is also the closest this carrier comes to nagini's "
            "clobber-the-caller's-state rival, which the LANES THAT DO NOT PORT note had "
            "recorded as inexpressible; on a state-threaded carrier it is expressible after "
            "all. If it VERIFIES => SPEC-TOO-WEAK (a deletion could silently drop the "
            "response's other cookies)."
        ),
        "witness": (
            "-- a response already carrying an unrelated cookie: gold leaves that name\n"
            "-- holding what it held, the rival writes into a fresh container and drops it.\n"
            + _WJAR
            + _witness(
                "",
                "example : ¬ problem_spec_deleteCookie wresp \"c\" \"/\" none"
                " (some \"lax\")\n"
                "      (implementation_deleteCookie wresp \"c\" \"/\" none (some \"lax\"))"
                " := by\n",
                "wresp",
                "  exact ⟨\"other\", by decide, by simp⟩\n",
            )
        ),
    },

    # ---- uniqueness rivals: the two configured call sites ----
    {
        "id": "riv-session-ignores-configured-path",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SESSION_PATH,
        "refinement": (
            "the session-ending deletion must be scoped to the CONFIGURED path; using the "
            "default instead emits a root-scoped deletion that never clears a session "
            "cookie set under a custom path. The F2P asserting the exact emitted header "
            "for a custom-path session deletion fails, so this does not resolve."
        ),
        "rationale": (
            "REJECTED by `problem_spec_sessionDelete`, which instantiates the deletion "
            "contract at the configured path — so clause E4 refutes it through that "
            "obligation. This ATTACKS the second obligation (the deleteCookie rivals do "
            "not: their variants leave both call-site impls untouched). Witness varies the "
            "sessionPath binder to a configured non-default value. If it VERIFIES => "
            "SPEC-TOO-WEAK (the call site's path threading would be unconstrained)."
        ),
        "witness": _witness(
            "-- configured non-default path: gold scopes the deletion to it, the rival to\n"
            "-- the root.\n",
            "example : ¬ problem_spec_sessionDelete emptyResponse \"sessionid\" \"/example/\""
            " none\n"
            "      (some \"Lax\")\n"
            "      (implementation_sessionDelete emptyResponse \"sessionid\" \"/example/\""
            " none\n"
            "        (some \"Lax\")) := by\n",
            "problem_spec_sessionDelete, implementation_sessionDelete",
        ),
    },
    {
        "id": "riv-session-drops-configured-policy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SESSION_POLICY,
        "refinement": (
            "this is the pre-patch call shape at the session site: the configured "
            "cross-site policy is not threaded into the deletion. A faithful patch keeping "
            "it emits a session-ending deletion header with no policy attribute, which is "
            "exactly what the F2P assertions on that header (they pin the configured "
            "policy into the expected header text) reject. It does not resolve."
        ),
        "rationale": (
            "REJECTED by `problem_spec_sessionDelete` via clause E6: the obligation "
            "requires the CONFIGURED policy on the written entry, and the rival supplies "
            "none. Attacks the second obligation on a different clause from the path rival, "
            "so both E4 and E6 are exercised through it. Witness varies the sessionSamesite "
            "binder to a configured truthy value while holding the path at the default — "
            "the complement of the path rival's point, so neither near-misses the other — "
            "and additionally moves the cookie-NAME binder off the value the sibling "
            "witness at this obligation uses, so no binder of this obligation sits at one "
            "value across its rivals. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            "-- configured policy at the default path, under a reconfigured cookie name:\n"
            "-- gold records the policy, the rival drops it.\n",
            "example : ¬ problem_spec_sessionDelete emptyResponse \"custom_session\" \"/\"\n"
            "      (some \".example.local\") (some \"Strict\")\n"
            "      (implementation_sessionDelete emptyResponse \"custom_session\" \"/\"\n"
            "        (some \".example.local\") (some \"Strict\")) := by\n",
            "problem_spec_sessionDelete, implementation_sessionDelete",
        ),
    },
    {
        "id": "riv-messages-drops-configured-policy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_MESSAGES_POLICY,
        "refinement": (
            "the pre-patch call shape at the messages site: the configured cross-site "
            "policy is not threaded into the deletion of the empty payload cookie. A "
            "faithful patch keeping it fails the F2P asserting that the deleted messages "
            "cookie records the configured policy. It does not resolve."
        ),
        "rationale": (
            "REJECTED by `problem_spec_messagesDelete` via clause E6. This ATTACKS the "
            "THIRD obligation, which neither the deleteCookie nor the session rivals touch "
            "— without it that obligation would be defended but never attacked. Witness "
            "varies the sessionSamesite binder of this obligation to a configured truthy "
            "value. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            "-- configured policy: gold records it on the deleted payload cookie, the\n"
            "-- rival drops it.\n",
            "example : ¬ problem_spec_messagesDelete emptyResponse \"messages\" none"
            " (some \"Lax\")\n"
            "      (implementation_messagesDelete emptyResponse \"messages\" none"
            " (some \"Lax\")) := by\n",
            "problem_spec_messagesDelete, implementation_messagesDelete",
        ),
    },
    {
        "id": "riv-messages-drops-configured-domain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_MESSAGES_DOMAIN,
        "refinement": (
            "dropping the configured domain at the messages site emits a host-only "
            "deletion for a payload cookie that was set on the configured parent domain, "
            "so the stale payload cookie survives. The assertions pinning the configured "
            "domain on the deleted payload cookie fail while the F2P policy assertion is "
            "untouched — verify-does-not-resolve."
        ),
        "rationale": (
            "REJECTED by `problem_spec_messagesDelete` via clause E5. Attacks the third "
            "obligation on a SECOND clause, and is not a near-miss of the policy rival at "
            "that site: it agrees with gold on the policy and differs on the domain, so it "
            "gets its own probe point with the domain binder PRESENT and a third policy "
            "value. It also moves the cookie-NAME binder — to a prefix-named cookie, which "
            "additionally forces the decision clause true through the key rather than the "
            "policy — so no binder of this obligation is held at one value across its "
            "rivals. If it VERIFIES => SPEC-TOO-WEAK (the call site's domain threading "
            "would be unconstrained)."
        ),
        "witness": _witness(
            "-- configured domain under a prefix-named payload cookie: gold records the\n"
            "-- domain, the rival supplies none.\n",
            "example : ¬ problem_spec_messagesDelete emptyResponse \"__Host-messages\"\n"
            "      (some \".example.com\") (some \"Strict\")\n"
            "      (implementation_messagesDelete emptyResponse \"__Host-messages\"\n"
            "        (some \".example.com\") (some \"Strict\")) := by\n",
            "problem_spec_messagesDelete, implementation_messagesDelete",
        ),
    },
    # ---- uniqueness rivals: the RECORDED-lifetime clause ----
    {
        "id": "riv-unrecorded-lifetime",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_UNRECORDED_LIFETIME,
        "refinement": (
            "the write primitive records a lifetime only when one is SUPPLIED to it, and a "
            "deletion that supplies none leaves the entry recording no lifetime at all. "
            "The emitted deletion then carries no lifetime directive, and every assertion "
            "that pins the exact emitted deletion header — the default one and both "
            "session-ending ones — expects that directive present and set to zero, so a "
            "faithful patch of this shape fails them. A previous revision of this bundle "
            "modeled the lifetime as a plain number whose default was ZERO, which made "
            "'no lifetime recorded' and 'the lifetime zero recorded' the same value, and "
            "this exact shape VERIFIED against it while its harness-run patch resolved "
            "nothing: it broke both the session-ending assertions and the default-deletion "
            "assertion. That is why the lifetime is now an option rather than a number."
        ),
        "rationale": (
            "REJECTED by clause E2 (`c.maxAge = some 0`), which requires the zero to be "
            "RECORDED rather than merely not contradicted. The distinction is what the "
            "option encoding buys: `none` and `some 0` are different entries and are "
            "rendered differently, so an unset lifetime can no longer masquerade as a zero "
            "one. Witness probes an ordinary deletion from a response carrying nothing, "
            "where the merge has no prior lifetime to restore either, and is fully "
            "transparent under the shared simp set. If it VERIFIES => SPEC-TOO-WEAK, and "
            "specifically the collapse the option encoding exists to prevent would be back."
        ),
        "witness": _witness(
            "-- ordinary deletion from an empty response: gold RECORDS the zero lifetime,\n"
            "-- the rival supplies none and the merge leaves the entry with no lifetime\n"
            "-- recorded at all.\n",
            "example : ¬ problem_spec_deleteCookie emptyResponse \"c\" \"/\" none"
            " (some \"lax\")\n"
            "      (implementation_deleteCookie emptyResponse \"c\" \"/\" none"
            " (some \"lax\")) := by\n",
        ),
    },
    {
        "id": "riv-lifetime-only-with-policy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_LIFETIME_PARTIAL,
        "refinement": (
            "the PARTIAL-DOMAIN form of the same defect: the lifetime is recorded only on "
            "deletions that also record a policy. Such a patch gets the emitted header "
            "right for every deletion configured with a policy — including the "
            "configuration this instance is about — and wrong for every deletion carrying "
            "none, so the long-standing assertions on the plain default deletion (which "
            "pin the zero lifetime on the emitted header with no policy configured) fail "
            "while the newer policy-carrying assertions pass. It resolves nothing."
        ),
        "rationale": (
            "REJECTED by clause E2 at the ABSENT-policy point, which the blunt rival above "
            "does not reach: that one is wrong everywhere, so a spec could in principle "
            "catch it through the policy-carrying sub-domain alone and still leave the "
            "lifetime free on deletions without a policy. This case holds the samesite "
            "binder at `none` — the sub-domain where the two rivals differ — so E2 is shown "
            "load-bearing independently of whether a policy is being recorded. Fully "
            "transparent under the shared simp set. If it VERIFIES => SPEC-TOO-WEAK (the "
            "lifetime would be constrained only on the deletions that carry a policy)."
        ),
        "witness": _witness(
            "-- ABSENT policy: gold records the zero lifetime regardless of the policy,\n"
            "-- the rival records one only when a policy is being recorded too.\n",
            "example : ¬ problem_spec_deleteCookie emptyResponse \"c\" \"/\" none none\n"
            "      (implementation_deleteCookie emptyResponse \"c\" \"/\" none none)"
            " := by\n",
        ),
    },

    # ---- uniqueness rivals: the attributes a deletion cannot supply ----
    {
        "id": "riv-stamp-annotation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_STAMP_COMMENT,
        "refinement": (
            "a stored cookie carries attributes the write primitive has no argument for, "
            "and they are rendered to the client along with the rest. A patch that reaches "
            "past the write to annotate the deleted entry emits an extra directive on the "
            "deletion header, so every assertion that pins that header exactly — the "
            "default deletion's and both session-ending ones — fails. A previous revision "
            "of this bundle modeled only the attributes a write has an argument for, so "
            "this shape VERIFIED against it and its harness-run patch resolved nothing. "
            "That is why the model now carries every attribute a stored cookie can carry "
            "rather than the ones a write can set."
        ),
        "rationale": (
            "REJECTED by the clause requiring the two unsupplied attributes to come back "
            "exactly as the entry had them — a deletion has no way to supply either, so it "
            "cannot annotate what it deletes. Witness probes an ordinary deletion from a "
            "response carrying nothing, where 'unchanged' and 'unset' coincide, and is "
            "fully transparent under the shared simp set. If it VERIFIES => SPEC-TOO-WEAK: "
            "the model would again be a projection of the entry, and an attribute the "
            "projection omits is one a wrong impl can stamp unobserved."
        ),
        "witness": _witness(
            "-- gold leaves the two attributes it cannot supply exactly as the entry had\n"
            "-- them; the rival annotates the deleted entry with one of its own.\n",
            "example : ¬ problem_spec_deleteCookie emptyResponse \"c\" \"/\" none"
            " (some \"lax\")\n"
            "      (implementation_deleteCookie emptyResponse \"c\" \"/\" none"
            " (some \"lax\")) := by\n",
        ),
    },
    {
        "id": "riv-stamp-protocol-version",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_STAMP_VERSION,
        "refinement": (
            "the same defect at the OTHER attribute a write cannot supply, and it too was "
            "found VERIFYING against a revision of this bundle that modeled the entry as a "
            "projection, with a harness-run patch that resolved nothing. Kept as a separate "
            "case rather than folded into the one above because a model that carries one of "
            "the two unsupplied attributes and omits the other is exactly as weak as one "
            "that carries neither — the audit that found the first shape found this one "
            "independently."
        ),
        "rationale": (
            "REJECTED by the same clause at the second attribute. This is the case that "
            "makes the coverage argument honest: enumerating one attribute at a time is how "
            "a projection model keeps losing, so BOTH unsupplied attributes are attacked "
            "and the frame around them is stated by rebuilding the response rather than by "
            "listing components. Fully transparent under the shared simp set. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            "-- the same defect at the other unsupplied attribute.\n",
            "example : ¬ problem_spec_deleteCookie emptyResponse \"c\" \"/\" none"
            " (some \"lax\")\n"
            "      (implementation_deleteCookie emptyResponse \"c\" \"/\" none"
            " (some \"lax\")) := by\n",
        ),
    },
    {
        "id": "riv-clear-unsupplied-attributes",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CLEAR_ANNOTATIONS,
        "refinement": (
            "the OPPOSITE direction: the deletion resets the attributes it cannot supply "
            "instead of leaving them standing. A write merges into whatever the entry "
            "already held, so a response that had set a cookie carrying those attributes "
            "and then deletes it emits them on the deletion header too; a patch that "
            "cleared them would emit a different header than the one the assertions on a "
            "set-then-delete response expect. It resolves nothing."
        ),
        "rationale": (
            "REJECTED by the same clause from the CLEARING side, and this is why the clause "
            "is stated as 'comes back as it was' rather than 'is unset': the two stamping "
            "rivals above are refuted at an empty response, where the two readings "
            "coincide, so on their evidence alone the clause could have been the stricter "
            "'must be unset' — which would be over-fitting, since the real primitive leaves "
            "a prior value standing. Witness must therefore be stated at a response whose "
            "entry ALREADY carries both attributes, which is the only sub-domain where the "
            "readings differ; it declares that response itself rather than referencing "
            "anything the variant declares. If it VERIFIES => SPEC-TOO-WEAK (a deletion "
            "could silently drop attributes the response had already set)."
        ),
        "witness": (
            "-- a response whose entry already carries both attributes: gold leaves them\n"
            "-- standing, the rival resets them.\n"
            + _ARESP
            + _witness(
                "",
                "example : ¬ problem_spec_deleteCookie aresp \"c\" \"/\" none"
                " (some \"lax\")\n"
                "      (implementation_deleteCookie aresp \"c\" \"/\" none (some \"lax\"))"
                " := by\n",
                "aresp",
            )
        ),
    },

    # ---- uniqueness rivals: the whole-response frame ----
    {
        "id": "riv-write-extra-header",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_WRITE_HEADER,
        "refinement": (
            "a deletion is a cookie write and nothing else: it does not touch the "
            "response's other header fields. A patch that also wrote one would emit a "
            "header nobody asked for on every deletion. This case is honest about its "
            "harness status — the assertions read the cookie container and a specific "
            "header, so a stray unrelated field might well go unnoticed and such a patch "
            "could still resolve. It is here as a SPEC-STRENGTH case: a previous revision "
            "of this bundle carried ONLY the cookie container, so a deletion's effect on "
            "the rest of the response was not merely unpinned but unrepresentable, and an "
            "attack that omitted a co-located header effect at the session site verified "
            "vacuously and did not resolve. If the spec cannot see a gratuitous header "
            "write it cannot see the missing one either."
        ),
        "rationale": (
            "REJECTED by the whole-response frame, which says the result IS the response "
            "handed in with its cookie container replaced — so every other component is "
            "pinned by construction, whether or not any clause names it. Witness refutes "
            "it by projecting the frame equation onto the header component and applying it "
            "at the disturbed field, the same way a container-frame violation is exhibited "
            "at the disturbed name. If it VERIFIES => SPEC-TOO-WEAK: the frame would be an "
            "enumeration of the components someone thought to list, which is how the "
            "previous carrier's hole stayed open through two repairs."
        ),
        "witness": (
            "-- gold moves nothing about the response but its cookies; the rival\n"
            "-- additionally writes a header field, which the whole-response frame\n"
            "-- forbids.\n"
            "example : ¬ problem_spec_deleteCookie emptyResponse \"c\" \"/\" none"
            " (some \"lax\")\n"
            "      (implementation_deleteCookie emptyResponse \"c\" \"/\" none"
            " (some \"lax\")) := by\n"
            "  intro h\n"
            "  have h2 := congrArg Response.headers h.2\n"
            "  simp [implementation_deleteCookie, setCookie] at h2\n"
            "  have h3 := congrFun h2 \"X-Sbu\"\n"
            "  simp [emptyResponse] at h3\n"
        ),
    },
    {
        "id": "riv-reset-status-and-body",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_RESET_STATUS,
        "refinement": (
            "the shape a 'build and return a fresh response' refactor takes: the container "
            "is carried over correctly and the status and body are reset to their defaults. "
            "A patch of this shape would turn every response that deletes a cookie into an "
            "ordinary empty one — a redirect that clears a session cookie would lose its "
            "status and every assertion on such a response's status or content fails. It "
            "resolves nothing."
        ),
        "rationale": (
            "REJECTED by the whole-response frame at two more components, and stated over a "
            "response that is NOT at those defaults — which is the whole content of the "
            "case, since at a default response the rival and gold agree. Distinct from the "
            "header rival: that one ADDS to a component, this one DISCARDS two, and a frame "
            "stated by rebuilding catches both directions where an enumeration of 'must not "
            "be added to' would catch only the first. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- a response that is NOT at the default status: gold hands it back\n"
            "-- unchanged, the rival rebuilds the response and resets it.\n"
            + _WRESP2
            + "example : ¬ problem_spec_deleteCookie vresp \"c\" \"/\" none"
              " (some \"lax\")\n"
              "      (implementation_deleteCookie vresp \"c\" \"/\" none (some \"lax\"))"
              " := by\n"
              "  intro h\n"
              "  have h2 := congrArg Response.status h.2\n"
              "  simp [implementation_deleteCookie, setCookie, vresp] at h2\n"
        ),
    },

    # ---- uniqueness rivals: the session site's dependency declaration ----
    {
        "id": "riv-session-omits-dependency",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NO_VARY,
        "refinement": (
            "ending a session leaves the response declaring that its content depends on "
            "the request's own cookies — whether the session cookie is being cleared is "
            "exactly what it depends on, and without the declaration a shared cache may "
            "serve the clearing response to a request that should not receive it. A patch "
            "that omitted it fails the F2P assertion reading that declaration off the "
            "session-ending response outright. A previous revision of this bundle carried "
            "only the cookie container, so this effect had no representation and omitting "
            "it was VACUOUSLY satisfied: the shape verified and its harness-run patch "
            "failed the session-ending tests. That is why the carrier is the whole response."
        ),
        "rationale": (
            "REJECTED by the session obligation's declaration clause. Witness refutes it by "
            "projecting the obligation's frame equation onto the declaration component: "
            "gold leaves the field declared, the rival leaves the response declaring "
            "nothing. If it VERIFIES => SPEC-TOO-WEAK, and specifically the vacuity the "
            "response carrier exists to remove would be back — an effect a spec cannot "
            "represent is one it cannot require."
        ),
        "witness": (
            "-- gold leaves the response declaring the dependency it now has; the rival\n"
            "-- declares nothing.\n"
            "example : ¬ problem_spec_sessionDelete emptyResponse \"sessionid\" \"/\" none"
            " (some \"Lax\")\n"
            "      (implementation_sessionDelete emptyResponse \"sessionid\" \"/\" none"
            " (some \"Lax\")) := by\n"
            "  intro h\n"
            "  have h2 := congrArg Response.varies h.2\n"
            "  simp [implementation_sessionDelete, implementation_deleteCookie, setCookie,\n"
            "    emptyResponse, variesAfter] at h2\n"
        ),
    },
    {
        "id": "riv-session-declares-wrong-field",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_VARY_WRONG_FIELD,
        "refinement": (
            "a declaration is made but of a different request field, so the response still "
            "fails to declare the dependency it actually has while looking as though it "
            "declared something. The F2P assertion reads the declaration and expects the "
            "request's cookies named in it, so this fails just as the omitting shape does, "
            "and it additionally declares a dependency the response does not have."
        ),
        "rationale": (
            "REJECTED by the same clause, and it is the case that makes that clause bite on "
            "WHICH field rather than on whether anything was declared: the omitting rival "
            "could be caught by a clause requiring the declaration to be non-empty, which "
            "would be weaker than the behavior. Fully transparent under projection. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- gold declares the dependency the routine actually has; the rival declares\n"
            "-- a different field.\n"
            "example : ¬ problem_spec_sessionDelete emptyResponse \"sessionid\" \"/\" none"
            " (some \"Lax\")\n"
            "      (implementation_sessionDelete emptyResponse \"sessionid\" \"/\" none"
            " (some \"Lax\")) := by\n"
            "  intro h\n"
            "  have h2 := congrArg Response.varies h.2\n"
            "  simp [implementation_sessionDelete, implementation_deleteCookie, setCookie,\n"
            "    varyMarked, emptyResponse, variesAfter] at h2\n"
        ),
    },
    {
        "id": "riv-session-clobbers-declaration",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_VARY_CLOBBER,
        "refinement": (
            "the declaration REPLACES whatever the response already declared instead of "
            "being added to it. Correct on a response that declared nothing — which is the "
            "shape the F2P assertions exercise, so this patch would pass them — and wrong "
            "on every response that had already declared a dependency, whose declaration "
            "is silently lost. Such a response is served from a cache keyed on fewer "
            "fields than it varies by, which is a correctness defect in the deployed "
            "system; the long-standing assertions on responses that declare a dependency "
            "before the session middleware runs fail."
        ),
        "rationale": (
            "REJECTED by the declaration clause, which is an APPEND to the prior "
            "declaration and not an assignment. This is a PARTIAL-DOMAIN rival: it agrees "
            "with gold at the empty prior declaration, which is where the omitting and "
            "wrong-field witnesses are stated, so those two carry no evidence about this "
            "shape at all. Witness must therefore be stated at a response that ALREADY "
            "declares a dependency, and declares that response itself. If it VERIFIES => "
            "SPEC-TOO-WEAK (the clause would only pin what a session ending declares on a "
            "response that declared nothing)."
        ),
        "witness": (
            "-- a response that ALREADY declares a dependency: gold adds to it, the rival\n"
            "-- replaces it and the prior declaration is lost.\n"
            + _WRESP2
            + "example : ¬ problem_spec_sessionDelete vresp \"sessionid\" \"/\" none"
              " (some \"Lax\")\n"
              "      (implementation_sessionDelete vresp \"sessionid\" \"/\" none"
              " (some \"Lax\")) := by\n"
              "  intro h\n"
              "  have h2 := congrArg Response.varies h.2\n"
              "  simp [implementation_sessionDelete, implementation_deleteCookie,"
              " setCookie,\n"
              "    varyMarked, vresp, variesAfter] at h2\n"
        ),
    },
    {
        "id": "riv-session-declares-only-when-undeclared",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_VARY_ONLY_IF_EMPTY,
        "refinement": (
            "the complement of the clobbering shape: the declaration is made only when the "
            "response declared nothing at all. It likewise passes the F2P assertions, which "
            "exercise exactly that case, and likewise fails on responses that already "
            "declare something — those are left without the dependency the session ending "
            "gives them and may be served from a cache to a request whose cookies differ."
        ),
        "rationale": (
            "REJECTED by the declaration clause from the other side of the same "
            "sub-domain. Kept alongside the clobber rival because the two are wrong at the "
            "same inputs for OPPOSITE reasons — one drops the prior declaration, the other "
            "drops the addition — so neither is a near-miss of the other and a clause that "
            "caught only one would be satisfied by the other. Witness is stated at the same "
            "already-declaring response, and the case-insensitive comparison that decides "
            "whether a field is already declared reduces via the fold's unfolding lemma and "
            "normalizer (`String.toLower`/`String.map_eq`, the route WITNESS MECHANICS "
            "documents). If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- a response that already declares a dependency: gold adds the declaration\n"
            "-- anyway, the rival makes it only when nothing was declared. The\n"
            "-- case-insensitive comparison reduces via String.map_eq.\n"
            + _WRESP2
            + "example : ¬ problem_spec_sessionDelete vresp \"sessionid\" \"/\" none"
              " (some \"Lax\")\n"
              "      (implementation_sessionDelete vresp \"sessionid\" \"/\" none"
              " (some \"Lax\")) := by\n"
              "  intro h\n"
              "  have h2 := congrArg Response.varies h.2\n"
              "  simp [implementation_sessionDelete, implementation_deleteCookie,"
              " setCookie,\n"
              "    varyMarked, vresp, variesAfter, String.toLower, String.map_eq] at h2\n"
        ),
    },
    {
        "id": "riv-session-collapses-to-wildcard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_VARY_WILDCARD,
        "refinement": (
            "declaring the response to depend on EVERYTHING is not the declaration the "
            "routine makes. It is not wrong about the dependency — a response that varies "
            "by everything does vary by the request's cookies — which is exactly why it is "
            "here: it destroys the response's cacheability outright, and the F2P assertion "
            "reads the declaration and expects the one field, so this fails it while being "
            "semantically 'safe'. It resolves nothing."
        ),
        "rationale": (
            "REJECTED by the declaration clause, whose oracle models the wildcard's "
            "absorbing behavior explicitly — so a rival that declares the wildcard is "
            "compared against a gold that declares the one field, not against a clause that "
            "merely asks whether the dependency is implied. This is the BOUNDARY case of "
            "the declaration oracle and no other case reaches it. Fully transparent under "
            "projection. If it VERIFIES => SPEC-TOO-WEAK (the clause would be satisfiable "
            "by any declaration that implies the one required, which is not what the "
            "response carries)."
        ),
        "witness": (
            "-- gold declares the one field the dependency is on; the rival declares\n"
            "-- everything, which absorbs the declaration entirely.\n"
            "example : ¬ problem_spec_sessionDelete emptyResponse \"sessionid\" \"/\" none"
            " (some \"Lax\")\n"
            "      (implementation_sessionDelete emptyResponse \"sessionid\" \"/\" none"
            " (some \"Lax\")) := by\n"
            "  intro h\n"
            "  have h2 := congrArg Response.varies h.2\n"
            "  simp [implementation_sessionDelete, implementation_deleteCookie, setCookie,\n"
            "    varyMarked, emptyResponse, variesAfter] at h2\n"
        ),
    },
    {
        "id": "riv-session-lowercases-field",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_VARY_LOWERCASE,
        "refinement": (
            "the declared field is spelled in lower case. The comparison deciding whether a "
            "field is ALREADY declared ignores case, so this rival makes the same decision "
            "about whether to declare anything; what differs is the spelling the response "
            "ends up carrying, and the F2P assertion compares that declaration to the "
            "expected text exactly. It fails, so it does not resolve."
        ),
        "rationale": (
            "REJECTED by the declaration clause, and it is the case that separates the "
            "clause's two halves: the comparison that decides whether to add is "
            "case-insensitive, but the value that gets declared is the field as GIVEN, not "
            "folded. A clause modeling only the insensitive comparison would admit this "
            "rival. No other case in the battery moves the declared field's spelling. Fully "
            "transparent under projection. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- gold leaves the field declared under the spelling the routine uses; the\n"
            "-- rival declares a differently-cased spelling, which is what the response\n"
            "-- then carries.\n"
            "example : ¬ problem_spec_sessionDelete emptyResponse \"sessionid\" \"/\" none"
            " (some \"Lax\")\n"
            "      (implementation_sessionDelete emptyResponse \"sessionid\" \"/\" none"
            " (some \"Lax\")) := by\n"
            "  intro h\n"
            "  have h2 := congrArg Response.varies h.2\n"
            "  simp [implementation_sessionDelete, implementation_deleteCookie, setCookie,\n"
            "    varyMarked, emptyResponse, variesAfter] at h2\n"
        ),
    },
    {
        "id": "riv-messages-declares-dependency",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_MESSAGES_VARY,
        "refinement": (
            "the OVER-reaching direction at the site that must declare nothing: deleting "
            "the stale payload cookie is an ordinary deletion and leaves the response's "
            "declared dependencies alone. A patch that declared one there would add a "
            "declaration to every response the messages framework touches, so the "
            "long-standing assertions on those responses' declarations fail while the F2P "
            "is untouched — verify-does-not-resolve."
        ),
        "rationale": (
            "REJECTED by the messages obligation, which instantiates the deletion contract "
            "INCLUDING its whole-response frame — so the declaration is pinned there by the "
            "frame rather than by a clause naming it. Without this case the declaration is "
            "only ever attacked from the omitting side at the one site that makes it, and a "
            "spec could pin 'the session site declares the field' while leaving every other "
            "site free to declare whatever it likes. Refuted by projecting the messages "
            "obligation's frame equation onto the declaration component. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- deleting the payload cookie is an ordinary deletion: gold leaves the\n"
            "-- response's declared dependencies alone, the rival adds one.\n"
            "example : ¬ problem_spec_messagesDelete emptyResponse \"messages\" none"
            " (some \"Lax\")\n"
            "      (implementation_messagesDelete emptyResponse \"messages\" none"
            " (some \"Lax\")) := by\n"
            "  intro h\n"
            "  have h2 := congrArg Response.varies h.2\n"
            "  simp [problem_spec_messagesDelete, implementation_messagesDelete,\n"
            "    implementation_deleteCookie, setCookie, varyMarked, emptyResponse,\n"
            "    variesAfter] at h2\n"
        ),
    },
]


# No consumed axiom and no opaque callee: the changed decision, the policy threading and
# the write primitive itself are modeled DEEPLY over the transparent String / Option
# String / Cookie / CookieJar carrier, so the axiom lane is vacuous here and belongs to
# G-AX regardless.
AXIOM_TESTS = []
