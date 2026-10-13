"""PBT manifest for django__django-11532 (NOT a Nagini module; a record of
adversarial cases the runner swebench_nagini.pbt executes + stamps RESULT).

Defended surface (frozen spec in model.py; see refinement.md / mapping.md):

  ascii_compatible_domain(domain: List[int]) -> List[int]     # models punycode()
    Requires: Acc(list_pred(domain), 1/2)         -- domain is READ-ONLY (1/2 perm)
              (NO valid_label precondition: EVERY label is admissible input)
    Ensures:  Acc(list_pred(domain), 1/2)         -- the 1/2 perm is RETURNED (frame)
              Acc(list_pred(Result()))            -- owns a fresh result
              valid_label(ToSeq(domain))    -- LOAD-BEARING: a value comes back ONLY
                                               for a label that HAS an ACE
              ToSeq(Result()) == ace_seq(ToSeq(domain))   -- LOAD-BEARING value pin
              all_ascii(ToSeq(Result()))                  -- defining property
    Exsures(LabelNotEncodable):
              Acc(list_pred(domain), 1/2) and ToSeq(domain) unchanged
              and not valid_label(ToSeq(domain))
                                            -- LOAD-BEARING: the out-of-band
                                               condition is signalled on EXACTLY
                                               the labels with no ACE
    impl:     return ace_encode(domain)

  cached_host_name(platform_name: List[int]) -> List[int]     # models get_fqdn()
    Requires: Acc(list_pred(platform_name), 1/2)  -- platform_name is READ-ONLY
              (NO valid_label precondition)
    Ensures:  Acc(list_pred(platform_name), 1/2)
              Acc(list_pred(Result()))
              valid_label(ToSeq(platform_name))                  -- LOAD-BEARING
              ToSeq(Result()) == ace_seq(ToSeq(platform_name))    -- LOAD-BEARING
              all_ascii(ToSeq(Result()))                         -- the F2P property
    Exsures(LabelNotEncodable):
              Acc(list_pred(platform_name), 1/2) and ToSeq unchanged
              and not valid_label(ToSeq(platform_name))          -- LOAD-BEARING
    impl:     return ascii_compatible_domain(platform_name)

TOTALITY NOTE (why the value-yielding domain is itself an observable). The
transform is defined on EVERY label, not only on the ones that have an ACE. Both
outcomes are pinned and they partition the input: a value comes back exactly for
the labels valid_label admits, and every other label is reported to the CALLER
out of band with the label untouched. Neither outcome is at the implementation's
discretion. Without that partition an implementation is free to answer a label
that has no ACE with a value of its own choosing (an empty result, a stand-in
host name) while still satisfying every pin on the value-yielding side, because
those pins would be scoped away by a precondition -- and a real caller that
branches on the out-of-band condition would silently take the wrong branch. The
reject cases oob-swallow-acd / oob-swallow-chn / oob-unconditional exercise
exactly that.

This is the F2P-tested function: get_fqdn now caches punycode(socket.getfqdn())
so the Message-ID domain is the all-ASCII ACE 'xn--p8s937b' for the mocked
non-ASCII host '漢字', not the raw name that crashed iso-8859-1 header
serialisation (test_non_ascii_dns_non_unicode_email).

The F2P input '漢字' HAS an ACE, so it takes the value-yielding side of that
partition and the F2P observation is unchanged by the totality note above.

GROUNDED-ORACLE NOTE: the load-bearing postcondition pin
`ToSeq(Result()) == ace_seq(ToSeq(domain))` is GROUNDED in the ARGUMENT --
ace_seq is a function of `domain` (the @ContractOnly face of the unchanged stdlib
str.encode('idna').decode('ascii')), NOT an opaque answer-key constant. The ONLY
constant the spec exposes is the witness value seq_ace_witness() ('xn--p8s937b'),
and the contract pins it CONDITIONALLY: `Implies(domain==seq_host_witness(),
Result()==seq_ace_witness())`. So there is NO unconditional wrong echo: a rival
that returns the witness ACE constant only satisfies the value pin when the input
IS the witness; for any other valid label the verifier cannot close
ToSeq(Result())==ace_seq(ToSeq(domain)). That echo is therefore a PARTIAL-DOMAIN
attack (witness-only), included below as a reject case -- not a true ungrounded
echo. The honest cheapest CORRECT impl (calling the ace_encode face) is the
positive control.

AXIOM LANE: the bundle CONSUMES an @ContractOnly axiom (ace_seq / ace_encode /
valid_label) modelling the unchanged stdlib callee str.encode('idna').decode
('ascii') (RFC 3490 ToASCII). We re-run the bundle's own executable soundness
check (axiom_check.py, read on the HOST at load time and embedded verbatim into
the probe -- the runner mounts only the probe at /work) as an axiom-soundness
case: the REAL callee must be all-ASCII on every label it returns a value for and
map the witness '漢字' -> 'xn--p8s937b', with valid_label characterising exactly
that value-yielding set (a label the codec rejects must be reported out of band,
not answered).
A caller-domain containment probe is also included: the PURE axiom ace_seq is
guarded by Requires(valid_label(domain)) and the model only ever evaluates it
where that predicate is established -- in the postconditions, under the
value-yielding case, and in ace_encode's own normal-return Ensures. The
impl-callable face ace_encode is TOTAL (no valid_label precondition), matching a
real callee that accepts every label and signals out of band; so the model can
pass it any label and the axiom is still in-domain by construction.

REGION-SURGERY: every spec variant is built by _swap on _BASE editing ONLY text
inside one of the two # impl-start/# impl-end regions. The frozen spec
(axioms/pure/pre/post-conditions/signatures) is never touched, so same_spec holds.
"""
from pathlib import Path

INSTANCE = "django__django-11532"
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
# Stable anchors -- the two single-line impl bodies (each present once in _BASE).
# ---------------------------------------------------------------------------
_IMPL_ACD = "    return ace_encode(domain)\n"                       # ascii_compatible_domain
_IMPL_CHN = "    return ascii_compatible_domain(platform_name)\n"   # cached_host_name

for _a in (_IMPL_ACD, _IMPL_CHN):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"


# ===========================================================================
# POSITIVE CONTROLS / ADMISSIBILITY  (expect "verify")
# ===========================================================================

# (5a) POSITIVE CONTROL -- local-variable reshape of ascii_compatible_domain.
# Instead of `return ace_encode(domain)` directly, bind the fresh ACE list to a
# typed local then return it. Structurally different (an extra binding), but
# semantically identical and keeps every gold proof obligation; the ace_encode
# Ensures (fresh ASCII list == ace_seq, all_ascii via ace_seq's Ensures) still
# discharges the postcondition. MUST verify; else SPEC-TOO-STRONG (postcondition
# over-fit to the exact return FORM).
_POS_ACD_RESHAPE = _swap(
    _BASE, _IMPL_ACD,
    "    out = ace_encode(domain)  # type: List[int]\n"
    "    return out\n",
)

# (5b) POSITIVE CONTROL -- structurally-different cached_host_name. The gold impl
# composes via the helper `ascii_compatible_domain(platform_name)`; this rival
# calls the ace_encode FACE directly (ace_encode and ascii_compatible_domain
# satisfy IDENTICAL contracts -- both: fresh ASCII list == ace_seq of input, plus
# all_ascii). The proof carries the all-ASCII / ace_seq value pin from ace_encode's
# Ensures exactly as the helper would. A genuinely different call shape that is
# CORRECT. MUST verify; else SPEC-TOO-STRONG.
_POS_CHN_DIRECT = _swap(
    _BASE, _IMPL_CHN,
    "    return ace_encode(platform_name)\n",
)

# (6) ADMISSIBILITY -- a self-call on a FRESH, F2P-shaped input: the worked
# witness label '漢字' (code points 28450, 23383). The constructed list
# w owns full list_pred; ToSeq(w) == seq_host_witness(), so valid_label(ToSeq(w))
# holds (the valid_label axiom Ensures Implies(domain==seq_host_witness(),
# Result())) and Acc(list_pred(w),1/2) is establishable -- i.e. the precondition
# of ascii_compatible_domain ADMITS a normal F2P input. The asserted value pin
# (ace == seq_ace_witness via the conditional ace_seq witness clause) confirms the
# F2P-observed result. The gold body then runs on the actual platform_name. MUST
# verify; else the precondition rejects a normal input => PRECOND-TOO-STRONG.
# (The successful CALL on w is the admissibility demonstration; we do not assert
# the result value here to avoid coupling admissibility to the conditional ace_seq
# witness clause firing through the helper's postcondition -- a proof-trigger risk,
# not a spec property. The value pin is exercised by the positive controls.)
_POS_ADMISS = _swap(
    _BASE, _IMPL_CHN,
    "    w = [28450, 23383]  # type: List[int]\n"
    "    Assert(ToSeq(w) == seq_host_witness())\n"
    "    Assert(valid_label(ToSeq(w)))\n"
    "    probe = ascii_compatible_domain(w)  # type: List[int]\n"
    "    return ascii_compatible_domain(platform_name)\n",
)


# ===========================================================================
# UNIQUENESS RIVALS  (spec-too-weak probes -- expect "reject")
# ===========================================================================

# (1a) FRAME MUTATION -- MANDATORY (#1 weakness class). platform_name is read-only
# at 1/2. This rival WRITES `platform_name[0] = 120` ('x') before composing,
# attempting to coerce the input toward an all-ASCII value so the postcondition is
# vacuously satisfiable. Under Acc(list_pred(platform_name),1/2) a store needs FULL
# permission, so it MUST be rejected for INSUFFICIENT PERMISSION (not a value
# mismatch). The gold composition is kept verbatim after the write, so the
# rejection is attributable solely to the mutation.
_RIVAL_FRAME_CHN = _swap(
    _BASE, _IMPL_CHN,
    "    platform_name[0] = 120\n"
    "    return ascii_compatible_domain(platform_name)\n",
)

# (1b) FRAME MUTATION on the other read-only input. ascii_compatible_domain's
# `domain` is held at 1/2; writing domain[0] = 120 before the transform must fail
# for INSUFFICIENT PERMISSION. Same #1 weakness class, second site.
_RIVAL_FRAME_ACD = _swap(
    _BASE, _IMPL_ACD,
    "    domain[0] = 120\n"
    "    return ace_encode(domain)\n",
)

# (3a) PARTIAL-DOMAIN -- witness-only constant (the "echo" that is really a
# partial-domain attack; see GROUNDED-ORACLE NOTE). cached_host_name returns a
# fresh list of the eleven witness-ACE code points 'xn--p8s937b'. This is CORRECT
# exactly on the F2P witness input (platform_name == seq_host_witness(), where the
# ace_seq witness clause pins ace_seq == seq_ace_witness()), and all_ascii holds
# trivially. But the load-bearing pin ToSeq(Result()) == ace_seq(ToSeq(
# platform_name)) cannot be closed for a GENERAL valid label (the verifier has no
# fact tying the constant to ace_seq of an arbitrary input). MUST reject.
_RIVAL_WITNESS_CONST = _swap(
    _BASE, _IMPL_CHN,
    "    ace = [120, 110, 45, 45, 112, 56, 115, 57, 51, 55, 98]  # type: List[int]\n"
    "    return ace\n",
)

# (3b) PARTIAL-DOMAIN -- identity / raw-name passthrough (== the pre-patch bug,
# model_prepatch.py). Returns a verbatim copy of the platform name. all_ascii would
# require every code point < 128 -- false for the non-ASCII witness '漢字'
# (28450, 23383 both >= 128) -- and the value pin ToSeq(Result()) == ace_seq(...)
# fails (the raw name is not its own ACE for a non-ASCII label). Correct only on
# already-ASCII labels; wrong on the F2P input. MUST reject. (We build a fresh copy
# so there is no frame issue -- the rejection is the VALUE/postcondition, distinct
# from case 1a's permission rejection.)
_RIVAL_RAW_PASSTHROUGH = _swap(
    _BASE, _IMPL_CHN,
    "    copy = list(platform_name)  # type: List[int]\n"
    "    return copy\n",
)

# (4a) SWALLOWED OUT-OF-BAND CONDITION at the transform site. A label with no ACE
# is answered with a value of the implementation's own choosing (an empty result)
# instead of being reported to the caller. Every pin on the value-yielding side
# still holds -- the rival keeps the gold body verbatim there -- so this case is
# rejected by the totality partition alone: the normal-return postcondition
# valid_label(ToSeq(domain)) cannot be closed when the rival returns on a label
# it has just tested as having no ACE. MUST reject.
_RIVAL_OOB_SWALLOW_ACD = _swap(
    _BASE, _IMPL_ACD,
    "    if not valid_label(ToSeq(domain)):\n"
    "        junk = []  # type: List[int]\n"
    "        return junk\n"
    "    return ace_encode(domain)\n",
)

# (4b) SWALLOWED OUT-OF-BAND CONDITION at the cached-host-name site, with a
# plausible stand-in rather than an empty value: a platform name with no ACE is
# answered with the nine ASCII code points spelling 'localhost'. all_ascii holds,
# and the value-yielding path is the gold composition verbatim, so again only the
# totality partition rejects it. MUST reject.
_RIVAL_OOB_SWALLOW_CHN = _swap(
    _BASE, _IMPL_CHN,
    "    if not valid_label(ToSeq(platform_name)):\n"
    "        fallback = [108, 111, 99, 97, 108, 104, 111, 115, 116]  # type: List[int]\n"
    "        return fallback\n"
    "    return ascii_compatible_domain(platform_name)\n",
)

# (4c) OVER-SIGNALLED OUT-OF-BAND CONDITION -- the mirror image of 4a/4b, and the
# case that stops the totality partition from being satisfiable by simply never
# returning. This rival reports the out-of-band condition UNCONDITIONALLY, so a
# platform name that HAS an ACE never gets its cached value. MUST reject.
_RIVAL_OOB_UNCONDITIONAL = _swap(
    _BASE, _IMPL_CHN,
    "    raise LabelNotEncodable()\n",
)


SPEC_TESTS = [
    # ---- positive controls / admissibility (must VERIFY) ----
    {"id": "pos-control-acd-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_ACD_RESHAPE,
     "rationale": "structurally-different but CORRECT ascii_compatible_domain: the "
                  "fresh ACE list is bound to a typed local before return (extra "
                  "binding, same semantics). ace_encode's Ensures (fresh ASCII list "
                  "== ace_seq, all_ascii via ace_seq) discharges every postcondition "
                  "clause exactly as the direct return. Must verify; else the spec is "
                  "over-fit to the return FORM => SPEC-TOO-STRONG."},
    {"id": "pos-control-chn-direct", "kind": "soundness", "expect": "verify",
     "module": _POS_CHN_DIRECT,
     "rationale": "structurally-different but CORRECT cached_host_name: instead of "
                  "composing via the helper ascii_compatible_domain, it calls the "
                  "ace_encode FACE directly (both satisfy identical contracts -- fresh "
                  "ASCII list == ace_seq of the input, plus all_ascii). A genuinely "
                  "different call shape that proves the same postcondition. Must verify; "
                  "else SPEC-TOO-STRONG."},
    {"id": "admiss-witness-selfcall", "kind": "admissibility", "expect": "verify",
     "module": _POS_ADMISS,
     "rationale": "a self-call on a FRESH F2P-shaped witness label '漢字' "
                  "([28450,23383]) must establish the precondition: Acc(list_pred(w),1/2) "
                  "from the constructed full-perm list, and valid_label(ToSeq(w)) via the "
                  "valid_label axiom witness clause (ToSeq(w)==seq_host_witness() => "
                  "Result()). The SUCCESSFUL call ascii_compatible_domain(w) is the "
                  "admissibility demonstration. If the precondition rejected this normal "
                  "input => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutate-platform-name", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME_CHN,
     "refinement": "no faithful real patch corresponds to this: get_fqdn wraps "
                   "socket.getfqdn() (a Python str, IMMUTABLE) -- it cannot and does not "
                   "mutate the platform name in place; it builds a new ACE value. The "
                   "rival exists solely to test whether the read-only (1/2) precondition "
                   "can be subverted by overwriting platform_name. No resolving patch "
                   "rewrites its input host name, so a verifying rival here is a pure "
                   "verify-not-resolve artifact (vacuous satisfaction via input "
                   "self-normalization).",
     "rationale": "MANDATORY frame-mutation probe (#1 weakness class). "
                  "`platform_name[0] = 120` writes through a 1/2 (read-only) reference "
                  "and MUST fail for INSUFFICIENT PERMISSION (a store needs full "
                  "Acc(list_pred(platform_name))), NOT a value mismatch; the gold "
                  "composition is kept verbatim after the write so the rejection is "
                  "attributable to the mutation. Rejection source: the PERMISSION SYSTEM. "
                  "If it verified => SPEC-TOO-WEAK (frame protection hollow)."},
    {"id": "frame-mutate-domain", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME_ACD,
     "refinement": "the punycode() helper does `domain.encode('idna').decode('ascii')` "
                   "on an immutable str argument -- it never mutates its input. A patch "
                   "that rewrote the domain in place has no faithful counterpart and would "
                   "not resolve; this rival only probes whether the second read-only (1/2) "
                   "input can be overwritten to satisfy the postcondition vacuously.",
     "rationale": "MANDATORY frame-mutation probe, second read-only site. `domain[0] = "
                  "120` writes through Acc(list_pred(domain),1/2) and MUST fail for "
                  "INSUFFICIENT PERMISSION (a store needs full permission). Rejection "
                  "source: the PERMISSION SYSTEM. If it verified => SPEC-TOO-WEAK."},
    {"id": "weak-witness-constant", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WITNESS_CONST,
     "refinement": "returning the hard-coded witness ACE 'xn--p8s937b' PASSES the F2P "
                   "(which mocks socket.getfqdn() -> '漢字', exactly the witness) "
                   "yet is wrong for every other host name. A faithful patch hard-coding "
                   "the Message-ID domain would break the real cached host name used in "
                   "P2P mail tests (test_send, test_idn_send, the many LocmemBackendTests "
                   "that read DNS_NAME) -- verify-not-resolve, diverging from the gold "
                   "transform on the whole non-witness sub-domain.",
     "rationale": "rejection source: the LOAD-BEARING postcondition "
                  "ToSeq(Result())==ace_seq(ToSeq(platform_name)). The witness ACE is "
                  "pinned only CONDITIONALLY (Implies(domain==seq_host_witness(), "
                  "Result()==seq_ace_witness())), so for a GENERAL valid label the "
                  "verifier has no fact equating the constant with ace_seq of the input; "
                  "the equality cannot be closed. all_ascii holds but is insufficient. "
                  "If it verified => SPEC-TOO-WEAK (value pin hollow / echo-vulnerable)."},
    {"id": "weak-raw-passthrough", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_RAW_PASSTHROUGH,
     "refinement": "returning the raw platform name with no transform is EXACTLY the "
                   "pre-patch bug (self._fqdn = socket.getfqdn(); == model_prepatch.py). "
                   "For the F2P witness '漢字' the cached Message-ID domain would "
                   "be the raw non-ASCII name, which crashes iso-8859-1 header "
                   "serialisation -- the precise failure the gold patch fixes. A faithful "
                   "patch doing this FAILS test_non_ascii_dns_non_unicode_email -- "
                   "verify-not-resolve.",
     "rationale": "rejection source: the postcondition. all_ascii(ToSeq(Result())) is "
                  "false for the non-ASCII witness (code points 28450, 23383 both >= 128) "
                  "and ToSeq(Result())==ace_seq(ToSeq(platform_name)) fails (the raw name "
                  "is not its own ACE for a non-ASCII label -- there is no fact equating "
                  "the identity copy with ace_seq). The verifier cannot close either pin. "
                  "A fresh copy is returned so this is a VALUE rejection, distinct from "
                  "the permission rejection of frame-mutate-platform-name. If it verified "
                  "=> SPEC-TOO-WEAK (the all-ASCII/ACE fix would be hollow)."},
    {"id": "oob-swallow-acd", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_OOB_SWALLOW_ACD,
     "refinement": "the faithful patch is a transform whose body catches the codec's "
                   "error and returns '' -- so the four repo call sites that wrap the "
                   "transform in `except UnicodeError` (URLValidator.__call__, "
                   "EmailValidator.__call__, urlize's unquote_quote, is_email_simple) "
                   "stop taking their handler branch and carry an empty domain forward "
                   "instead: an invalid IDN is silently accepted as a valid one. The "
                   "gold transform's body is a bare `domain.encode('idna').decode"
                   "('ascii')` with no try/except, so it propagates. This instance's "
                   "test set does not exercise an ill-formed IDN at those sites, which "
                   "is precisely why the SPEC rather than the oracle has to carry the "
                   "obligation.",
     "rationale": "rejection source: the value-yielding-domain postcondition "
                  "valid_label(ToSeq(domain)) on the NORMAL return. The rival returns a "
                  "value on a label it has just tested as having no ACE, so the "
                  "verifier cannot close that pin (it reports "
                  "`Postcondition of ascii_compatible_domain might not hold. Assertion "
                  "valid_label(ToSeq(domain)) might not hold.`). Note the rival keeps "
                  "the gold body verbatim on the value-yielding path, so NO other pin "
                  "is implicated: the rejection is attributable solely to answering an "
                  "unencodable label with a value of its own choosing. If it verified "
                  "=> SPEC-TOO-WEAK (the out-of-band condition would be unobservable "
                  "and a wrong impl could swallow it)."},
    {"id": "oob-swallow-chn", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_OOB_SWALLOW_CHN,
     "refinement": "the faithful patch caches a stand-in host name ('localhost') "
                   "whenever the platform reports a name with no ACE, instead of "
                   "letting the condition reach get_fqdn's caller. Messages would then "
                   "be stamped with a host name the platform never reported -- a "
                   "silently wrong Message-ID rather than a surfaced error. Second "
                   "site, and a PLAUSIBLE stand-in rather than an empty value, so the "
                   "case cannot be passed by a rejection that only notices emptiness.",
     "rationale": "rejection source: the value-yielding-domain postcondition "
                  "valid_label(ToSeq(platform_name)) on the NORMAL return. all_ascii "
                  "holds for the stand-in and the value-yielding path is the gold "
                  "composition verbatim, so the totality partition is the ONLY clause "
                  "that can reject it. If it verified => SPEC-TOO-WEAK."},
    {"id": "oob-unconditional", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_OOB_UNCONDITIONAL,
     "refinement": "no faithful real patch corresponds to caching nothing ever: the "
                   "cached host name would never be produced and every mail test that "
                   "stamps a Message-ID would error. The rival exists as the MIRROR of "
                   "oob-swallow-*: it checks that the out-of-band obligation cannot be "
                   "discharged by simply never returning a value, which would make the "
                   "totality partition satisfiable without the transform ever running.",
     "rationale": "rejection source: the EXCEPTIONAL postcondition "
                  "Exsures(LabelNotEncodable, ... and not valid_label(ToSeq("
                  "platform_name))). Signalling the condition for a platform name that "
                  "HAS an ACE cannot close `not valid_label(...)`; the verifier reports "
                  "`Postcondition of cached_host_name might not hold. Assertion (not "
                  "valid_label(ToSeq(platform_name))) might not hold.` If it verified "
                  "=> SPEC-TOO-WEAK (the Exsures would be a licence to raise rather "
                  "than an obligation pinned to one half of the input space)."},
]


# ===========================================================================
# AXIOM LANE -- the bundle CONSUMES an @ContractOnly axiom (ace_seq / ace_encode /
# valid_label) for the unchanged stdlib callee str.encode('idna').decode('ascii').
# (1) axiom-soundness: re-run the bundle's executable soundness check (axiom_check.py,
#     read on the HOST and embedded verbatim) -- the REAL callee must be all-ASCII on
#     every label it answers with a value, map the witness '漢字' -> 'xn--p8s937b',
#     and PARTITION its input exactly as the contract claims: the labels it answers
#     with a value are exactly the ones valid_label admits, and every other label is
#     reported out of band and never answered with a substitute value. Both tallies
#     must be non-empty, so neither half of the partition is checked vacuously. The
#     codec is option-free (no flag_dependency; RFC 3490 ToASCII is fixed across
#     CPython 3.x), so the caller's runtime config does not alter the behaviour.
# (2) axiom-containment: two faces, two obligations. The PURE face ace_seq keeps
#     Requires(valid_label(domain)) and is mentioned only in postconditions where it
#     is conjoined after the same return's valid_label pin, so its guard is
#     discharged at every occurrence. The IMPL-CALLABLE face ace_encode is TOTAL --
#     no label-shape precondition at all -- so every caller-reachable label is
#     in-domain by construction. Asserted as a static fact off the frozen model text
#     (no executable disagreement is possible: the impl face's domain is the whole
#     carrier, and the pure face's guard is syntactically co-located with its pin).
# ===========================================================================

_AXIOM_CHECK_SRC = (_DIR / "axiom_check.py").read_text()

_CONTAINMENT_PROBE = (
    "import sys\n"
    "# axiom-containment for django__django-11532 (static structural argument).\n"
    "#\n"
    "# Two axiom faces, two containment obligations.\n"
    "#\n"
    "# (i) The PURE face ace_seq has Requires(valid_label(domain)), so it may only\n"
    "#     be evaluated where that predicate is established. The model mentions it\n"
    "#     ONLY in postconditions, and in each one it is conjoined AFTER the pin\n"
    "#     valid_label(ToSeq(.)) on the same return -- so the guard is discharged at\n"
    "#     every occurrence.\n"
    "# (ii) The IMPL-CALLABLE face ace_encode is TOTAL: it carries NO valid_label\n"
    "#     precondition, matching a real callee that accepts every label and reports\n"
    "#     the ones with no ACE out of band rather than refusing them. So the two\n"
    "#     model call sites --\n"
    "#       - ascii_compatible_domain: `return ace_encode(domain)`           (impl)\n"
    "#       - cached_host_name:        `return ascii_compatible_domain(...)` (composes)\n"
    "#     -- may pass ANY label and are in-domain by construction; there is no\n"
    "#     caller-reachable input outside the axiom's domain because the domain is\n"
    "#     the whole carrier. Containment holds trivially on the impl face and by\n"
    "#     the guard above on the pure face.\n"
    "#\n"
    "# We confirm the structural fact mechanically off the frozen model text, read\n"
    "# at runtime from /work/model.py if present (the runner may or may not mount it)\n"
    "# else from the facts the manifest pinned below (these are the exact strings the\n"
    "# manifest asserted exist at author time, so the check is reproducible either way).\n"
    "import os\n"
    "MODEL = None\n"
    "for _p in ('/work/model.py', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model.py')):\n"
    "    try:\n"
    "        with open(_p, encoding='utf-8') as _f:\n"
    "            MODEL = _f.read()\n"
    "        break\n"
    "    except (OSError, IOError):\n"
    "        continue\n"
    "if MODEL is None:\n"
    "    # model.py not mounted: fall back to the pinned facts (verified on the HOST\n"
    "    # at manifest-load time -- see PINNED below).\n"
    "    print('CONTAINMENT OK (pinned): model.py not in-container; the manifest "
    "verified on the host that the pure axiom face is only evaluated under its "
    "valid_label guard and that the impl-callable face is total.')\n"
    "    sys.exit(0)\n"
    "# (ii) the impl-callable face is TOTAL -- valid_label is never a precondition on\n"
    "# a List[int] carrier (ace_encode / either modeled function), so every label the\n"
    "# implementation can be handed is admissible input rather than excluded:\n"
    "assert 'Requires(valid_label(ToSeq(' not in MODEL, \\\n"
    "    'a valid_label PRECONDITION reappeared on a label carrier -- the "
    "unencodable-label case would be excluded from the claim instead of specified'\n"
    "# (i) the pure face IS guarded where it is DECLARED:\n"
    "assert 'Requires(valid_label(domain))' in MODEL, \\\n"
    "    'ace_seq Requires(valid_label(domain)) missing -- pure axiom domain undefined'\n"
    "acd = MODEL[MODEL.index('def ascii_compatible_domain'):MODEL.index('def cached_host_name')]\n"
    "chn = MODEL[MODEL.index('def cached_host_name'):]\n"
    "# both halves of the totality partition are pinned at BOTH sites, and the\n"
    "# normal-return valid_label pin is what discharges ace_seq's guard there:\n"
    "assert 'Ensures(valid_label(ToSeq(domain)))' in acd \\\n"
    "    and 'Ensures(ToSeq(Result()) == ace_seq(ToSeq(domain)))' in acd, \\\n"
    "    'ascii_compatible_domain lost its value-yielding-domain pin or its value pin'\n"
    "assert 'not valid_label(ToSeq(domain))' in acd, \\\n"
    "    'ascii_compatible_domain lost the out-of-band half of the partition'\n"
    "assert 'ace_encode(domain)' in acd, 'ascii_compatible_domain does not call ace_encode(domain)'\n"
    "assert 'Ensures(valid_label(ToSeq(platform_name)))' in chn \\\n"
    "    and 'Ensures(ToSeq(Result()) == ace_seq(ToSeq(platform_name)))' in chn, \\\n"
    "    'cached_host_name lost its value-yielding-domain pin or its value pin'\n"
    "assert 'not valid_label(ToSeq(platform_name))' in chn, \\\n"
    "    'cached_host_name lost the out-of-band half of the partition'\n"
    "assert 'ascii_compatible_domain(platform_name)' in chn, \\\n"
    "    'cached_host_name does not forward platform_name unchanged'\n"
    "print('CONTAINMENT OK: the impl-callable axiom face is total (no valid_label "
    "precondition), so every caller-reachable label is in-domain; the pure face "
    "ace_seq is evaluated only alongside the valid_label pin that discharges its "
    "guard.')\n"
    "sys.exit(0)\n"
)
# PINNED facts (verified here on the HOST at manifest-load time, so the in-container
# fallback claim above is honest): the impl-callable axiom face is total, the pure
# face is guarded, and both halves of the totality partition are pinned at both sites.
assert "Requires(valid_label(ToSeq(" not in _BASE
assert "Requires(valid_label(domain))" in _BASE
_acd = _BASE[_BASE.index("def ascii_compatible_domain"):_BASE.index("def cached_host_name")]
assert "Ensures(valid_label(ToSeq(domain)))" in _acd
assert "Ensures(ToSeq(Result()) == ace_seq(ToSeq(domain)))" in _acd
assert "not valid_label(ToSeq(domain))" in _acd and "ace_encode(domain)" in _acd
_chn = _BASE[_BASE.index("def cached_host_name"):]
assert "Ensures(valid_label(ToSeq(platform_name)))" in _chn
assert "Ensures(ToSeq(Result()) == ace_seq(ToSeq(platform_name)))" in _chn
assert "not valid_label(ToSeq(platform_name))" in _chn
assert "ascii_compatible_domain(platform_name)" in _chn


AXIOM_TESTS = [
    {
        "id": "ax-sound-ace-seq",
        "axiom": "ace_seq / ace_encode (+ valid_label raise-guard)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "the consumed axiom asserts (a) the real stdlib callee "
                     "str.encode('idna').decode('ascii') is all-ASCII on every "
                     "label it returns a value for -- the property the proof "
                     "consumes; (b) the witness '漢字' -> 'xn--p8s937b'; (c) that "
                     "valid_label characterises exactly the value-yielding set, i.e. "
                     "the real callee signals out of band on precisely the complement "
                     "(so the totality partition is not an over-claim in either "
                     "direction). This probe is axiom_check.py verbatim (stdlib only): "
                     "it runs the REAL callee on the witness + 17 boundary + 20000 fuzz "
                     "labels and exits 0 iff every obligation holds. The idna codec is "
                     "option-free (RFC 3490 ToASCII, fixed across CPython 3.x), so no "
                     "caller runtime config changes the result. Any disagreement => "
                     "AXIOM-UNSOUND.",
    },
    {
        "id": "ax-cover-valid-label",
        "axiom": "ace_seq / ace_encode (+ valid_label raise-guard)",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": False,
        "probe": _CONTAINMENT_PROBE,
        "rationale": "containment, in two halves. The IMPL-CALLABLE face ace_encode is "
                     "TOTAL -- it carries no valid_label precondition -- so the two "
                     "model call sites (`ace_encode(domain)`; cached_host_name "
                     "forwarding platform_name unchanged via ascii_compatible_domain) "
                     "may pass ANY label and are in-domain trivially. The PURE face "
                     "ace_seq does carry Requires(valid_label(domain)), and the model "
                     "evaluates it only in postconditions where the value-yielding pin "
                     "valid_label(ToSeq(.)) on the same return discharges that guard. "
                     "A caller-reachable label OUTSIDE the axiom's domain would be "
                     "AXIOM-TOO-WEAK-FOR-CALLER; this probe confirms (off the frozen "
                     "model text) that no such path exists, and additionally that no "
                     "valid_label PRECONDITION has reappeared -- which would shrink the "
                     "claim back to the encodable labels rather than specifying the "
                     "unencodable ones.",
    },
]
