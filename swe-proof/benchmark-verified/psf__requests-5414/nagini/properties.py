# properties.py — PBT falsification battery for psf__requests-5414.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
# model.py variants that share the FROZEN spec (region-surgery: edits live ONLY
# inside the # impl-start / # impl-end region, which spec_view elides — so
# same_spec holds by construction) and are checked by Nagini verify; axiom cases
# are real-callee probes checked in Docker.
#
# DEFENDED SURFACE (what this spec protects — see model.py / refinement.md):
#
#   screen_host(host: List[int], host_is_ascii: bool, encodable: bool) -> None
#     Requires Acc(list_pred(host), 1/2)         <-- READ-ONLY input (half perm)
#     Requires len(host) > 0
#     Requires MustTerminate(2)                   <-- TOTAL correctness (see below)
#     Ensures  Acc(list_pred(host), 1/2)          <-- frame: caller keeps its half
#     Ensures  len(host) > 0
#     Ensures  Implies(host_is_ascii,
#                      len(host) > 0 and not is_invalid_leading(host[0]))   <-- LOAD-BEARING
#                  (normal return on an ASCII host  =>  host[0] NOT in {42,46})
#     Ensures  Implies(not host_is_ascii, encodable is True)                <-- LOAD-BEARING
#                  (normal return on a non-ASCII host => the encoder accepted)
#     Exsures(InvalidLocator,
#             Acc(list_pred(host),1/2) and len(host) > 0 and
#             ((host_is_ascii and is_invalid_leading(host[0]))
#              or (not host_is_ascii and encodable is False)))              <-- LOAD-BEARING
#                  (rejection EXACTLY on the two disjoint reject cases)
#
#   is_invalid_leading(c) is a @Pure helper FULLY GROUNDED in the input
#   (`c == 42 or c == 46`, an unfolded membership test on host[0]); it is NOT an
#   opaque answer-key oracle an impl could echo without doing the work. The
#   load-bearing equality is checked against the unfolded disjunction itself, so
#   there is no "wrong ungrounded-oracle echo" to construct (the cheapest honest
#   impl IS the gold branch). The ungrounded-oracle class is therefore N/A here
#   (see 'assessment'); its slot is filled by an honest inline-oracle positive
#   control (case pos-inline).
#
#   THE BEHAVIOURAL DISCRIMINATOR (the bug fix, issue: http://.example.com): the
#   ASCII leading-code-point screen is widened from rejecting only '*' (42) to
#   rejecting BOTH '*' (42) and '.' (46). The F2P test asserts
#   InvalidURL on http://.example.com (host '.example.com', ASCII, first cp 46);
#   the P2P test_invalid_url[InvalidURL-http://*example.com] asserts InvalidURL on
#   host '*example.com' (first cp 42). model_prepatch.py is exactly the
#   "reject 42 only" rival (case partial-star-only); a "reject 46 only" rival
#   (case partial-dot-only) breaks the P2P.
#
#   READ-ONLY INPUT => FRAME-MUTATION is MANDATORY (case frame-mutation).
#
#   TERMINATION (total correctness — closes the vacuous-divergence hole): the
#   precondition carries Requires(MustTerminate(2)); the encode_label axiom
#   carries the strictly smaller Requires(MustTerminate(1)). Nagini is a
#   partial-correctness verifier by default, so WITHOUT the obligation a rival
#   that diverges before answering — bare self-recursion of the contracted
#   routine, or an endless loop — satisfies every Ensures/Exsures VACUOUSLY and
#   verifies (the G-PANEL-1 spec-too-weak counterexample this spec was
#   strengthened against). With it, a self-call is rejected ("Callee ... might
#   not take all unsatisfied obligations") and an unbounded loop is rejected
#   ("Loop might not take all unsatisfied obligations"), while the bounded
#   encoder call (measure 1 < 2) remains admitted (cases nonterm-self-recursion
#   / nonterm-endless-loop below).
#
#   AXIOM LANE: meta.axioms has ONE @ContractOnly A-consumed axiom, encode_label,
#   abstracting the UNCHANGED IDNA encoder _get_idna_encoded_host (calls
#   idna.encode(host, uts46=True), maps idna.IDNAError -> UnicodeError). Its
#   Ensures/Exsures are CONSUMED by screen_host's non-ASCII path, so both an
#   axiom-soundness probe (real callee total over {accept->str, reject->
#   UnicodeError}) and an axiom-containment probe (every host the model can drive
#   the callee with — i.e. every NON-ASCII host, the only branch that calls
#   encode_label — yields an outcome the boolean `encodable` abstraction covers)
#   are included. Both CALL the real callee in Docker (apply_gold=True); the
#   oracle host battery is lifted from axiom_check.py.
from pathlib import Path

INSTANCE = "psf__requests-5414"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ===========================================================================
# The single impl region (between # impl-start / # impl-end). Editing only this
# keeps spec_view (hence same_spec) byte-identical. The whole gold body is a
# unique anchor.
# ===========================================================================
_IMPL_GOLD = """    if not host_is_ascii:
        encode_label(encodable)
    elif is_invalid_leading(host[0]):
        raise InvalidLocator()"""

assert _IMPL_GOLD in _BASE, "impl anchor drift: screen_host body not verbatim"


# ===========================================================================
# (1) POSITIVE CONTROL — structurally different but CORRECT (verify).
# Branch-REORDER: test host_is_ascii FIRST (gold tests `not host_is_ascii`
# first), with the leading-code-point screen nested inside the ASCII arm and the
# encoder call moved to the else arm. Behaviourally identical on every input:
#   ASCII + invalid leading  -> raise            (== gold elif raise)
#   ASCII + valid leading    -> return normally   (== gold falls through)
#   non-ASCII                -> encode_label(encodable)  (== gold if-branch)
# No loop, no fold lemma, no dropped framing assert — a pure control-flow
# reshape that keeps the gold proof valid. If this cannot verify => SPEC-TOO-STRONG.
# ===========================================================================
_IMPL_POS_REORDER = """    if host_is_ascii:
        if is_invalid_leading(host[0]):
            raise InvalidLocator()
    else:
        encode_label(encodable)"""

# ===========================================================================
# (2) POSITIVE CONTROL (inline oracle) — honest cheapest impl (verify).
# is_invalid_leading is a @Pure, fully-unfolded membership test (c==42 or
# c==46); inlining it as the literal disjunction host[0]==42 or host[0]==46 is
# the SAME computation and must satisfy the postcondition that is phrased over
# is_invalid_leading(host[0]). This is the honest positive control that stands in
# for the (N/A) ungrounded-oracle slot: there is no WRONG echo because the oracle
# is grounded — the only way to satisfy the Ensures is to actually compute the
# membership test, which this does. Must verify, else SPEC-TOO-STRONG.
# ===========================================================================
_IMPL_POS_INLINE = """    if not host_is_ascii:
        encode_label(encodable)
    elif host[0] == 42 or host[0] == 46:
        raise InvalidLocator()"""

# ===========================================================================
# (3) ADMISSIBILITY — the precondition admits a normal F2P-shaped input (verify).
# Cannot add a top-level caller (that leaves the impl region and breaks
# same_spec). Instead, in-region: re-derive that the half-permission `host` is
# READABLE (read host[0]) and that the Requires fact len(host) > 0 is usable,
# then run the gold body and reach a NORMAL return for an in-domain input (an
# ASCII host whose first code point is valid, or a non-ASCII encodable host). If
# the Requires were vacuous / over-strong the impl could not both read the
# half-permission input and reach a normal return => PRECOND-TOO-STRONG.
# ===========================================================================
_IMPL_ADMISS = """    # admissibility: the half-permission `host` is readable and len(host) > 0 is
    # usable; a normal (non-raising) return is reachable for an in-domain input.
    Assert(len(host) > 0)
    first = host[0]  # type: int
    Assert(first == host[0])
    if not host_is_ascii:
        encode_label(encodable)
    elif is_invalid_leading(host[0]):
        raise InvalidLocator()"""

# ===========================================================================
# (4) FRAME-MUTATION — write to the read-only input `host` (reject). MANDATORY.
# screen_host holds only Acc(list_pred(host), 1/2). host[0] is in-bounds
# (len(host) > 0), so the WRITE host[0] = host[0] is well-typed and
# value-NEUTRAL (writes back the same code point) — yet a list-element store
# needs FULL permission. With only the half-permission the Requires grants,
# Nagini rejects for INSUFFICIENT PERMISSION. The gold branch is kept VERBATIM
# after the write, so the rejection is attributable to the write, not to a spec
# change or a behavioural divergence. A byte-fuzzer never thinks to mutate a
# read-only input — this is the project's #1 weakness class.
# ===========================================================================
_IMPL_FRAME = """    host[0] = host[0]
    if not host_is_ascii:
        encode_label(encodable)
    elif is_invalid_leading(host[0]):
        raise InvalidLocator()"""

# ===========================================================================
# (5) PARTIAL-DOMAIN / reject '*' only — THE PRE-PATCH BUG (reject).
# This is model_prepatch.py: the ASCII screen rejects ONLY host[0]==42 ('*') and
# lets a host beginning with 46 ('.') return normally. It agrees with the gold on
# the '*' sub-domain and on every non-46 ASCII host, but DIVERGES on an ASCII
# host whose first code point is 46. The normal-completion postcondition
# Implies(host_is_ascii, not is_invalid_leading(host[0])) then fails: on such a
# host is_invalid_leading(46) is True yet the impl returns normally.
# ===========================================================================
_IMPL_STAR_ONLY = """    if not host_is_ascii:
        encode_label(encodable)
    elif host[0] == 42:
        raise InvalidLocator()"""

# ===========================================================================
# (6) PARTIAL-DOMAIN / reject '.' only — the mirror miss (reject).
# Rejects ONLY host[0]==46 ('.') and lets a host beginning with 42 ('*') return
# normally. Diverges from gold on an ASCII host whose first code point is 42. The
# normal-completion postcondition fails: is_invalid_leading(42) is True yet the
# impl returns normally on an ASCII '*' host.
# ===========================================================================
_IMPL_DOT_ONLY = """    if not host_is_ascii:
        encode_label(encodable)
    elif host[0] == 46:
        raise InvalidLocator()"""

# ===========================================================================
# (7) CONTROL-FLOW-EFFECT / drop the encoder call (reject).
# On the non-ASCII path, do nothing (drop the encode_label(encodable) call). The
# encoder call is the ONLY thing that signals the rejection on the non-ASCII path
# (via the axiom's Exsures); dropping it is a side-effect difference invisible to
# a pure value check of the host. But the normal-completion postcondition
# Implies(not host_is_ascii, encodable is True) now fails: on a non-ASCII host
# with encodable=False the impl returns normally instead of being rejected.
# ===========================================================================
_IMPL_DROP_ENCODE = """    if not host_is_ascii:
        pass
    elif is_invalid_leading(host[0]):
        raise InvalidLocator()"""

# ===========================================================================
# (8) CONTROL-FLOW-EFFECT / always-raise on non-ASCII (reject, supporting).
# On the non-ASCII path, raise unconditionally instead of deferring to the
# encoder. This over-rejects: on a non-ASCII ENCODABLE host the gold returns
# normally, but this rival raises. The Exsures requires that any rejection be
# (host_is_ascii and is_invalid_leading(host[0])) OR
# (not host_is_ascii and encodable is False); when encodable is True on the
# non-ASCII path neither disjunct holds, so the Exsures is violated.
# ===========================================================================
_IMPL_ALWAYS_RAISE = """    if not host_is_ascii:
        raise InvalidLocator()
    elif is_invalid_leading(host[0]):
        raise InvalidLocator()"""

# ===========================================================================
# (9) NON-TERMINATION / bare self-recursion (reject). THE G-PANEL-1 rival class.
# The contracted routine re-invokes ITSELF with the same arguments: every
# Ensures/Exsures is discharged by echoing the routine's own contract, and
# without a termination obligation the diverging call verifies vacuously —
# exactly the wrong-impl the auditor built against the pre-strengthening spec.
# With Requires(MustTerminate(2)) the self-call has no strictly smaller measure
# available, so Nagini rejects: "Callee screen_host might not take all
# unsatisfied obligations".
# ===========================================================================
_IMPL_SELF_RECURSE = """    screen_host(host, host_is_ascii, encodable)"""

# ===========================================================================
# (10) NON-TERMINATION / endless loop (reject, supporting).
# `while True: pass` never reaches a return or a raise, so every postcondition
# holds vacuously under partial correctness. With the MustTerminate obligation
# in context the unbounded loop is rejected: "Loop might not take all
# unsatisfied obligations from the context".
# ===========================================================================
_IMPL_ENDLESS_LOOP = """    while True:
        Invariant(Acc(list_pred(host), 1 / 2))
        pass"""


SPEC_TESTS = [
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_POS_REORDER),
        "rationale": "Structurally different but correct: branch order flipped "
                     "(test host_is_ascii FIRST, nest the leading-code-point screen "
                     "in the ASCII arm, move the encoder call to the else arm). "
                     "Behaviourally identical on all three cases (ASCII+invalid->raise, "
                     "ASCII+valid->return, non-ASCII->encode_label). No loop / fold "
                     "lemma / dropped framing assert. Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-inline-oracle",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_POS_INLINE),
        "rationale": "Honest cheapest impl: inline the @Pure is_invalid_leading as "
                     "its unfolded body host[0]==42 or host[0]==46 — the SAME "
                     "computation, so it satisfies the postcondition phrased over "
                     "is_invalid_leading(host[0]). Stands in for the (N/A) "
                     "ungrounded-oracle slot: the oracle is GROUNDED in host[0], so "
                     "there is no wrong echo; the only way to satisfy Ensures is to "
                     "actually compute the membership test, which this does. Must "
                     "verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admissibility-readonly-host",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_ADMISS),
        "rationale": "Re-derives in-region that the half-permission `host` is "
                     "readable (reads host[0]) and that the Requires fact "
                     "len(host) > 0 is usable, then reaches a normal return for an "
                     "in-domain (F2P-shaped) input. If the Requires were vacuous or "
                     "over-strong the impl could not both read the half-permission "
                     "input and return => PRECOND-TOO-STRONG. Source: the "
                     "Acc(list_pred(host),1/2) and len(host)>0 Requires.",
    },
    {
        "id": "frame-mutation-write-host",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_FRAME),
        "refinement": "A faithful real patch in which the host-screen slice WROTE "
                      "back into the host (e.g. normalising host in place, host = "
                      "list(host); host[0] = ...) would mutate the `host` local that "
                      "prepare_url goes on to use for netloc reconstruction below the "
                      "slice (requests/models.py:409+). The gold slice only READS "
                      "host (host.startswith(...), host[0]); the reconstructed netloc "
                      "and every downstream assertion in test_invalid_url / the "
                      "preparing-URL P2P tests depend on host being untouched, so a "
                      "mutating slice would corrupt the URL the tests inspect and "
                      "would NOT faithfully resolve the F2P/P2P.",
        "rationale": "screen_host holds only Acc(list_pred(host), 1/2). The store "
                     "host[0] = host[0] (value-neutral, in-bounds via len(host)>0) "
                     "needs FULL permission => Nagini rejects for INSUFFICIENT "
                     "PERMISSION. Source: the permission system + the "
                     "Acc(list_pred(host),1/2) Requires/Ensures. Gold branch kept "
                     "verbatim after the write so the rejection is attributable to "
                     "the write.",
    },
    {
        "id": "partial-star-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_STAR_ONLY),
        "refinement": "This IS the pre-patch behaviour (model_prepatch.py): the "
                      "ASCII screen is host.startswith(u'*') — it rejects only '*' "
                      "(42) and lets a host beginning with '.' (46) pass. On the F2P "
                      "input http://.example.com (host '.example.com', ASCII, first "
                      "cp 46) the faithful patch returns normally instead of raising "
                      "InvalidURL, so test_invalid_url[InvalidURL-http://.example.com] "
                      "FAILS — the patch does NOT resolve. This is precisely the bug "
                      "the gold widening fixes.",
        "rationale": "On an ASCII host with host[0]==46 the impl returns normally, "
                      "but is_invalid_leading(46) is True, so the normal-completion "
                      "postcondition Implies(host_is_ascii, not "
                      "is_invalid_leading(host[0])) fails. Source: that load-bearing "
                      "Ensures clause (the same clause that fails for "
                      "model_prepatch.py, G-DIFF).",
    },
    {
        "id": "partial-dot-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_DOT_ONLY),
        "refinement": "The mirror miss: reject only '.' (46) and let a host "
                      "beginning with '*' (42) pass. On the P2P input "
                      "http://*example.com (host '*example.com', ASCII, first cp 42) "
                      "the faithful patch returns normally instead of raising, so "
                      "test_invalid_url[InvalidURL-http://*example.com] (a PASS_TO_PASS "
                      "the patch must preserve) FAILS — the patch does NOT resolve. "
                      "It would also regress the legacy startswith('*') wildcard "
                      "rejection.",
        "rationale": "On an ASCII host with host[0]==42 the impl returns normally, "
                      "but is_invalid_leading(42) is True, so the normal-completion "
                      "postcondition Implies(host_is_ascii, not "
                      "is_invalid_leading(host[0])) fails. Source: that load-bearing "
                      "Ensures clause.",
    },
    {
        "id": "control-flow-drop-encoder",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_DROP_ENCODE),
        "refinement": "A faithful real patch that DROPPED the non-ASCII IDNA branch "
                      "(`if not unicode_is_ascii(host): host = "
                      "self._get_idna_encoded_host(host) except UnicodeError: raise "
                      "InvalidURL(...)`) would no longer reject an un-encodable "
                      "internationalised host: a host like the malformed-IDNA cases "
                      "in the preparing-URL suite would slip through to netloc "
                      "reconstruction (or fail later with the wrong error type) "
                      "instead of raising InvalidURL, regressing the IDNA P2P "
                      "expectations — the patch would NOT faithfully resolve.",
        "rationale": "On the non-ASCII path the impl returns normally regardless of "
                      "`encodable`; for encodable=False this violates the "
                      "normal-completion postcondition Implies(not host_is_ascii, "
                      "encodable is True). Source: that load-bearing Ensures clause. "
                      "The dropped encode_label call is a side-effect difference "
                      "invisible to a pure value-of-host abstraction but caught here.",
    },
    {
        "id": "control-flow-always-raise-nonascii",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_ALWAYS_RAISE),
        "refinement": "A faithful real patch that raised InvalidURL on EVERY "
                      "non-ASCII host (instead of deferring to "
                      "_get_idna_encoded_host) would reject the encodable "
                      "internationalised hosts the preparing-URL P2P tests expect to "
                      "succeed (e.g. the IDNA round-trip fixtures), so those P2P tests "
                      "FAIL — the patch does NOT resolve.",
        "rationale": "On a non-ASCII ENCODABLE host (encodable=True) the impl raises, "
                      "but the Exsures requires any rejection to be (host_is_ascii and "
                      "is_invalid_leading(host[0])) or (not host_is_ascii and "
                      "encodable is False); neither disjunct holds when encodable is "
                      "True on the non-ASCII path, so the Exsures is violated. Source: "
                      "the Exsures rejection clause (over-rejection direction).",
    },
    {
        "id": "nonterm-self-recursion",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_SELF_RECURSE),
        "refinement": "A real prepare_url host slice that re-entered itself "
                      "unconditionally would never finish preparing the URL: "
                      "requests.get(...) would hang (RecursionError at best) on "
                      "EVERY request, so neither the F2P "
                      "test_invalid_url[InvalidURL-http://.example.com] nor any "
                      "P2P preparing-URL test can pass — the patch does NOT "
                      "resolve.",
        "rationale": "The impl discharges every Ensures/Exsures by echoing the "
                      "routine's own contract and diverges. Under partial "
                      "correctness this verifies vacuously (the recorded "
                      "G-PANEL-1 wrong-impl class); with "
                      "Requires(MustTerminate(2)) no strictly smaller measure "
                      "is available for the self-call, so Nagini rejects "
                      "('Callee screen_host might not take all unsatisfied "
                      "obligations'). Source: the MustTerminate(2) Requires.",
    },
    {
        "id": "nonterm-endless-loop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_ENDLESS_LOOP),
        "refinement": "A real slice that spun forever before deciding the host "
                      "would hang every request; no F2P/P2P test completes — "
                      "the patch does NOT resolve.",
        "rationale": "`while True: pass` reaches neither a return nor a raise, "
                      "so all postconditions hold vacuously under partial "
                      "correctness. The MustTerminate(2) obligation in context "
                      "makes Nagini reject the unbounded loop ('Loop might not "
                      "take all unsatisfied obligations from the context'). "
                      "Source: the MustTerminate(2) Requires.",
    },
]


# ===========================================================================
# AXIOM LANE — the one @ContractOnly A-consumed axiom encode_label, abstracting
# the UNCHANGED IDNA encoder _get_idna_encoded_host. Both probes CALL the real
# callee in the instance image (apply_gold=True; the encoder is not touched by
# the patch but we run post-gold to match the verified-twin world). The oracle
# host battery is lifted from axiom_check.py. Probes import only stdlib + the
# requests/idna callee that lives in the image; open nothing on disk; print a
# diagnostic; sys.exit(0) iff the obligation holds.
# ===========================================================================

# Oracle hosts (from axiom_check.py / the requests preparing-URL fixtures).
_ENCODABLE_HOSTS = [
    'ジェーピーニック.jp',
    'straße.de',
    'Königsgäßchen.de',
    'xn--n3h.net',
    'ドメイン.テスト',
    'مثال.إختبار',
    'παράδειγμα.δοκιμή',
    '例え.テスト',
]
_NOT_ENCODABLE_HOSTS = [
    '☃.net',
    '.straße.de',
    'straße..de',
    'xn--.de',
    '​.de',
    'a' * 100 + 'ß.de',
]

# Embed the oracle hosts as a literal so the probe is self-contained in-container
# (the runner mounts ONLY the probe script at /work; model.py/axiom_check.py are
# NOT in the container — pilot bug #6). repr() keeps the non-ASCII glyphs as
# escaped unicode, safe under the container's ASCII locale.
_ENC_REPR = repr(_ENCODABLE_HOSTS)
_NOTENC_REPR = repr(_NOT_ENCODABLE_HOSTS)

_AX_SOUNDNESS_PROBE = '''# -*- coding: utf-8 -*-
"""axiom-soundness probe for encode_label (psf__requests-5414).

The axiom:
    encode_label(encodable) -> None
        Ensures(encodable is True)                  # normal completion => encodable
        Exsures(InvalidLocator, encodable is False) # rejection => not encodable

i.e. the only observable of the real callee _get_idna_encoded_host on the model's
domain (NON-ASCII hosts) is the single bit `encodable`: it RETURNS A str EXACTLY
when the label is encodable and RAISES UnicodeError EXACTLY when it is not — and
NOTHING ELSE (no other out-of-band signal). We run the REAL callee (which calls
idna.encode(host, uts46=True), the recorded flag_dependency) on the oracle +
fuzz NON-ASCII hosts and assert it is TOTAL over {accept->str, reject->
UnicodeError}. Any third outcome on an in-domain (non-ASCII) host is AXIOM-UNSOUND.
"""
import random
import sys

ENCODABLE_HOSTS = %s
NOT_ENCODABLE_HOSTS = %s


def is_ascii(s):
    try:
        s.encode('ascii')
        return True
    except UnicodeEncodeError:
        return False


def main():
    try:
        from requests.models import PreparedRequest
    except Exception as exc:
        print("AX-SOUND SKIP: requests.PreparedRequest unavailable (%%r)" %% (exc,))
        return 0
    try:
        import idna  # noqa: F401
    except Exception as exc:
        print("AX-SOUND SKIP: idna unavailable (%%r)" %% (exc,))
        return 0

    encode = PreparedRequest._get_idna_encoded_host

    def observe(host):
        # classify the real callee outcome into the axiom's two channels.
        try:
            result = encode(host)
        except UnicodeError:
            return ('reject', None)
        except Exception as other:  # any OTHER out-of-band signal -> axiom unsound
            return ('other', other)
        else:
            return ('accept', result)

    n_accept = 0
    for host in ENCODABLE_HOSTS:
        if is_ascii(host):
            continue
        kind, info = observe(host)
        # Ensures(encodable is True): normal completion must be a str.
        assert kind == 'accept', (
            "AXIOM-UNSOUND: real _get_idna_encoded_host did NOT encode a host the "
            "repo expects to encode (%%r): outcome=%%r" %% (host, (kind, info)))
        assert isinstance(info, str), (
            "AXIOM-UNSOUND: normal completion on %%r returned %%r, expected str"
            %% (host, info))
        n_accept += 1

    n_reject = 0
    for host in NOT_ENCODABLE_HOSTS:
        if is_ascii(host):
            continue
        kind, info = observe(host)
        # the ONLY relied-on fact: accept(str) or reject(UnicodeError), never other.
        assert kind in ('accept', 'reject'), (
            "AXIOM-UNSOUND: real _get_idna_encoded_host produced a non-UnicodeError "
            "out-of-band signal on %%r: %%r" %% (host, info))
        if kind == 'reject':
            n_reject += 1

    rng = random.Random(5414)
    non_ascii_pool = list('àáâãäåçèé'
                          'αβγδεабвг'
                          'ぁあぃいمثال') + [
                          '☃', '•', '​']
    ascii_pool = list('abcdefghijklmnopqrstuvwxyz0123456789.-')
    n_fuzz = 0
    for _ in range(2000):
        m = rng.randint(1, 24)
        chars = [rng.choice(non_ascii_pool)]
        for _ in range(m):
            chars.append(rng.choice(non_ascii_pool + ascii_pool))
        rng.shuffle(chars)
        host = ''.join(chars)
        if is_ascii(host):
            continue
        kind, info = observe(host)
        assert kind in ('accept', 'reject'), (
            "AXIOM-UNSOUND: real _get_idna_encoded_host produced a non-UnicodeError "
            "out-of-band signal on %%r: %%r" %% (host, info))
        if kind == 'accept':
            assert isinstance(info, str), (
                "AXIOM-UNSOUND: accepted %%r but returned %%r, expected str"
                %% (host, info))
        n_fuzz += 1

    print("AX-SOUND OK: real _get_idna_encoded_host on %%d encodable + %%d "
          "not-encodable oracle hosts + %%d non-ASCII fuzz is TOTAL over "
          "{accept->str, reject->UnicodeError}; encode_label sound (uts46=True)"
          %% (n_accept, n_reject, n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
''' % (_ENC_REPR, _NOTENC_REPR)


_AX_CONTAINMENT_PROBE = '''# -*- coding: utf-8 -*-
"""axiom-containment probe for encode_label (psf__requests-5414).

CONTAINMENT, not whole-domain coverage. screen_host calls encode_label EXACTLY
on the non-ASCII branch (`if not host_is_ascii`), and ONLY there — so the set of
real-callee inputs the model can DRIVE is exactly the NON-ASCII hosts. The axiom
has an EMPTY Requires (it constrains no input domain; it accepts encodable in
{True, False}). Containment therefore asks: does every NON-ASCII host the model
can reach produce an outcome that the boolean `encodable` abstraction can
REPRESENT — i.e. accept (encodable True) or reject (encodable False), never a
third outcome the axiom cannot express? A reachable non-ASCII host whose real
outcome is neither accept(str) nor reject(UnicodeError) would be a caller-
reachable input the axiom does NOT cover => AXIOM-TOO-WEAK-FOR-CALLER.

We additionally confirm the abstraction is NON-VACUOUS on the reachable domain:
the model reaches BOTH encodable=True (the gold returns normally) and
encodable=False (the gold raises) on real non-ASCII hosts, and the axiom covers
BOTH (Ensures for True, Exsures for False). ASCII hosts are EXCLUDED: the model
never calls encode_label on them (they take the elif screen branch), so they are
outside the reachable callee-input set and irrelevant to containment.
"""
import random
import sys

ENCODABLE_HOSTS = %s
NOT_ENCODABLE_HOSTS = %s


def is_ascii(s):
    try:
        s.encode('ascii')
        return True
    except UnicodeEncodeError:
        return False


def main():
    try:
        from requests.models import PreparedRequest
    except Exception as exc:
        print("AX-COVER SKIP: requests.PreparedRequest unavailable (%%r)" %% (exc,))
        return 0
    try:
        import idna  # noqa: F401
    except Exception as exc:
        print("AX-COVER SKIP: idna unavailable (%%r)" %% (exc,))
        return 0

    encode = PreparedRequest._get_idna_encoded_host

    def covered(host):
        # An input is COVERED iff its real outcome maps to an `encodable` value
        # the axiom expresses: accept->True (Ensures) or reject->False (Exsures).
        try:
            result = encode(host)
        except UnicodeError:
            return ('reject', None)       # encodable=False, covered by Exsures
        except Exception as other:
            return ('other', other)       # NOT covered by the boolean abstraction
        else:
            return ('accept', result)     # encodable=True, covered by Ensures

    saw_true = False   # the model reaches encodable=True on a real non-ASCII host
    saw_false = False  # the model reaches encodable=False on a real non-ASCII host
    n_checked = 0

    # The reachable callee-input set = NON-ASCII hosts. Enumerate the oracle
    # battery (both partitions) + a non-ASCII fuzz; assert every one is covered.
    battery = list(ENCODABLE_HOSTS) + list(NOT_ENCODABLE_HOSTS)
    for host in battery:
        if is_ascii(host):
            continue  # not reachable as a callee input (takes the ASCII branch)
        kind, info = covered(host)
        assert kind in ('accept', 'reject'), (
            "AXIOM-TOO-WEAK-FOR-CALLER: reachable non-ASCII host %%r produced an "
            "outcome the boolean `encodable` abstraction cannot express: %%r"
            %% (host, info))
        saw_true = saw_true or (kind == 'accept')
        saw_false = saw_false or (kind == 'reject')
        n_checked += 1

    rng = random.Random(54140)
    non_ascii_pool = list('àáâãäåçèé'
                          'αβγδεабвг'
                          'ぁあぃいمثال') + [
                          '☃', '•', '​']
    ascii_pool = list('abcdefghijklmnopqrstuvwxyz0123456789.-')
    for _ in range(1500):
        m = rng.randint(1, 24)
        chars = [rng.choice(non_ascii_pool)]
        for _ in range(m):
            chars.append(rng.choice(non_ascii_pool + ascii_pool))
        rng.shuffle(chars)
        host = ''.join(chars)
        if is_ascii(host):
            continue
        kind, info = covered(host)
        assert kind in ('accept', 'reject'), (
            "AXIOM-TOO-WEAK-FOR-CALLER: reachable non-ASCII fuzz host %%r produced "
            "an outcome the abstraction cannot express: %%r" %% (host, info))
        saw_true = saw_true or (kind == 'accept')
        saw_false = saw_false or (kind == 'reject')
        n_checked += 1

    # Non-vacuity: the model reaches BOTH abstract values, and the axiom covers
    # both. (If only one were reachable the containment would still HOLD, but we
    # report it for the audit.)
    assert saw_true, ("containment note: no reachable non-ASCII host encoded "
                      "successfully in this run (encodable=True path unexercised)")
    assert saw_false, ("containment note: no reachable non-ASCII host failed to "
                       "encode in this run (encodable=False path unexercised)")

    print("AX-COVER OK: all %%d reachable NON-ASCII hosts produce an outcome the "
          "boolean `encodable` abstraction covers (accept->True / reject->False); "
          "both abstract values reached; encode_label domain contains the "
          "caller-reachable inputs" %% (n_checked,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
''' % (_ENC_REPR, _NOTENC_REPR)


AXIOM_TESTS = [
    {
        "id": "ax-sound-encode_label",
        "axiom": "encode_label",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUNDNESS_PROBE,
        "rationale": "Runs the REAL _get_idna_encoded_host (idna.encode(uts46=True), "
                     "the recorded flag_dependency) on the encodable + not-encodable "
                     "oracle hosts + 2000 non-ASCII fuzz and asserts it is TOTAL over "
                     "{accept->str (Ensures encodable is True), reject->UnicodeError "
                     "(Exsures encodable is False)} — never a third out-of-band "
                     "signal. Any third outcome on an in-domain non-ASCII host is "
                     "AXIOM-UNSOUND.",
    },
    {
        "id": "ax-cover-encode_label",
        "axiom": "encode_label",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT_PROBE,
        "rationale": "screen_host calls encode_label ONLY on the non-ASCII branch, so "
                     "the reachable callee-input set is exactly the NON-ASCII hosts. "
                     "The axiom's Requires is empty (covers encodable in {True,False}). "
                     "Asserts every reachable non-ASCII host (oracle + fuzz) yields an "
                     "outcome the boolean abstraction can express (accept->True / "
                     "reject->False); a non-ASCII host with a third outcome would be a "
                     "caller-reachable input outside the axiom domain => "
                     "AXIOM-TOO-WEAK-FOR-CALLER. ASCII hosts are excluded (the model "
                     "never drives the callee with them).",
    },
]
