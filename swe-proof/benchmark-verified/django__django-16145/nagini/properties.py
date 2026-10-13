"""PBT manifest for django__django-16145 (NOT a Nagini module; a record of
adversarial cases the runner swebench_nagini.pbt executes + stamps RESULT).

Defended surface (frozen spec in model.py; see refinement.md / mapping.md):

  display_address(addr: List[int], raw_ipv6: bool) -> List[int]
    Requires: Acc(list_pred(addr), 1/2)            -- addr is READ-ONLY (1/2 perm)
    Ensures (frame): Acc(list_pred(addr), 1/2)     -- the 1/2 perm is returned
    Ensures: Acc(list_pred(Result()))              -- the result is fully owned
    Ensures (DECISION, load-bearing):
        ToSeq(Result()) == shown_address(ToSeq(addr), raw_ipv6)

  shown_address(addr, raw_ipv6) =                                # @Pure, grounded
      PSeq(91) + addr + PSeq(93)        if raw_ipv6              # "[" + addr + "]"
      wildcard_dotted()                 elif addr == wildcard_short()  # "0"->"0.0.0.0"
      addr                              otherwise               # identity
    wildcard_short()  = PSeq(48)                    # "0"
    wildcard_dotted() = PSeq(48,46,48,46,48,46,48)  # "0.0.0.0"
  Priority order: bracket-IPv6 first, then the "0"->"0.0.0.0" wildcard expansion,
  then identity. (code points: '0'=48 '.'=46 '['=91 ']'=93)

This models the gold runserver hunk that derives the announced address:
    +        if self._raw_ipv6:   addr = f"[{self.addr}]"
    +        elif self.addr == "0": addr = "0.0.0.0"
    +        else:                addr = self.addr
  replacing the pre-patch one-liner ("[%s]" % self.addr if self._raw_ipv6 else
  self.addr), which had NO "0"->"0.0.0.0" expansion. The F2P test_zero_ip_addr
  runs addrport="0:8000" (self.addr=="0", _raw_ipv6==False) and asserts the line
  "Starting development server at http://0.0.0.0:8000/".

GROUNDED-ORACLE NOTE: the postcondition oracle shown_address(ToSeq(addr),
raw_ipv6) is GROUNDED in the arguments -- a @Pure piecewise transcription fully
computable from `addr` and `raw_ipv6`, with NO opaque answer-key/marker. So there
is NO *wrong* echo a rival can return: any impl that reproduces shown_address is
correct (a positive control), and any constant/echo that diverges fails the
postcondition. The uniqueness lane is therefore about whether a rival can satisfy
the decision on the reachable input domain while diverging on a discriminating
sub-domain (the wildcard "0" -- the pre-patch behaviour; a malformed IPv6 wrap;
a gutted identity branch) -- exactly what the gold patch newly fixes/relies on.

AXIOM LANE: there is NO @ContractOnly axiom in this bundle (axioms region empty),
and NO A-reference deep model standing in for a library callee: the whole
derivation is primitive Python string formatting / comparison / literals modelled
directly on the List[int]/PSeq[int] code-point carrier (mapping.md sec 3,
refinement.md sec B). axiom_check.py validates the only remaining soundness
obligation -- that the modelled shown_address equals Python's own evaluation of
the gold patch.diff expression over boundary + fuzz addresses, and that the
pre-patch expression differs from gold exactly on the wildcard discriminator. We
re-run that real-evaluation equivalence (axiom_check.py verbatim, stdlib-only,
read on the HOST at load time and embedded into the probe) as an axiom-soundness
check. A containment probe is N/A (no axiom Requires domain to fall outside).

REGION-SURGERY: every spec variant is built by _swap on _BASE editing ONLY text
inside # impl-start/# impl-end (the invariants are nested inside that region, so
editing them is still inside impl and preserves same_spec). The frozen spec
(axioms/pure/pre/post-conditions/signatures) is never touched.
"""
from pathlib import Path

INSTANCE = "django__django-16145"
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
# ---------------------------------------------------------------------------
# the wildcard branch -- the operation the gold patch ADDS.
_WILD_LIT = "        result = [48, 46, 48, 46, 48, 46, 48]\n"
_WILD_ASSERT_RES = "        Assert(ToSeq(result) == wildcard_dotted())\n"

# the bracket-close + its framing asserts.
_BRACKET_CLOSE = (
    "        result = result + [93]\n"
    "        Assert(ToSeq(result) == PSeq(91) + ToSeq(addr) + PSeq(93))\n"
    "        Assert(shown_address(ToSeq(addr), raw_ipv6) == PSeq(91) + ToSeq(addr) + PSeq(93))\n"
)

# the entire else (identity) branch body, after the `else:` line.
_ELSE_BODY = (
    "        i = 0\n"
    "        while i < len(addr):\n"
    "            # invariants-start\n"
    "            Invariant(Acc(list_pred(addr), 1 / 2))\n"
    "            Invariant(Acc(list_pred(result)))\n"
    "            Invariant(0 <= i and i <= len(addr))\n"
    "            Invariant(ToSeq(addr) != wildcard_short())\n"
    "            Invariant(ToSeq(result) == ToSeq(addr).take(i))\n"
    "            Invariant(MustTerminate(len(addr) - i + 1))\n"
    "            # invariants-end\n"
    "            c = addr[i]\n"
    "            Assert(ToSeq(addr).take(i + 1) == ToSeq(addr).take(i) + PSeq(c))\n"
    "            result = result + [c]\n"
    "            i = i + 1\n"
    "        Assert(ToSeq(addr).take(len(addr)) == ToSeq(addr))\n"
    "        Assert(ToSeq(result) == ToSeq(addr))\n"
    "        Assert(ToSeq(addr) != wildcard_short())\n"
    "        Assert(shown_address(ToSeq(addr), raw_ipv6) == ToSeq(addr))\n"
)

# the read inside the bracket copy-loop (the FIRST `c = addr[i]`).
_BRACKET_READ = (
    "        result = [91]\n"
    "        i = 0\n"
)
_BRACKET_READC = (
    "            c = addr[i]\n"
    "            Assert(ToSeq(addr).take(i + 1) == ToSeq(addr).take(i) + PSeq(c))\n"
    "            result = result + [c]\n"
    "            i = i + 1\n"
    "        Assert(ToSeq(addr).take(len(addr)) == ToSeq(addr))\n"
    "        Assert(ToSeq(result) == PSeq(91) + ToSeq(addr))\n"
)

# the top of the impl body (for an admissibility self-call prologue).
_IMPL_TOP = "    result = []  # type: List[int]\n    c = 0\n"

for _a in (_WILD_LIT, _WILD_ASSERT_RES, _BRACKET_CLOSE, _ELSE_BODY,
           _BRACKET_READ, _BRACKET_READC, _IMPL_TOP):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"


# ===========================================================================
# POSITIVE CONTROLS / ADMISSIBILITY  (expect "verify")
# ===========================================================================

# (5a) POSITIVE CONTROL -- structurally-different CORRECT wildcard construction.
# The "0.0.0.0" result literal [48,46,48,46,48,46,48] is built by concatenating
# two independent list literals instead of one flat literal. The data-shape of
# the construction differs, but the value is identical, and the gold framing
# asserts (ToSeq(result)==wildcard_dotted(); shown_address==wildcard_dotted())
# are kept VERBATIM so the gold proof stays valid -- the verifier still discharges
# them because both sides are concrete sequences. MUST verify; else the
# postcondition is over-fit to the exact literal FORM => SPEC-TOO-STRONG.
_POS_WILD_SPLIT = _swap(
    _BASE, _WILD_LIT,
    "        result = [48, 46, 48, 46] + [48, 46, 48]\n",
)

# (5b) POSITIVE CONTROL -- the bracket-close written as a list-concat reshape.
# Instead of the flat inline append `result = result + [93]`, the closing
# bracket fragment is BUILT INDEPENDENTLY as its own typed List[int] (`close`)
# and then concatenated onto `result`. Same value (PSeq(91)+addr+PSeq(93)),
# different construction shape (a separate fragment + list-list concat vs an
# inline single-element literal append). All gold framing asserts kept verbatim.
# MUST verify; else the postcondition is over-fit to the exact append FORM =>
# SPEC-TOO-STRONG.
#
# NOTE: an earlier reshape `result = result + [] + [93]` was REJECTED, but the
# rejection was a Nagini PROOF artifact, NOT a spec rejection: the bare empty
# literal `[]` has no inferred element type, so the list `+` precondition on
# `(result + [])` could not be discharged ("The precondition of (result + [])
# might not hold."), independent of the postcondition. Building `close` as a
# typed List[int] removes that artifact while still exercising a genuinely
# different construction shape for the same value.
_POS_BRACKET_RESHAPE = _swap(
    _BASE, "        result = result + [93]\n",
    "        close = []  # type: List[int]\n"
    "        close = close + [93]\n"
    "        result = result + close\n",
)

# (6) ADMISSIBILITY -- a self-call on the F2P-shaped input: the wildcard "0"
# (addr=[48], raw_ipv6=False -- EXACTLY addrport="0:8000"). The fresh literal
# establishes Acc(list_pred(.),1/2); we assert the result property holds for it
# (ToSeq(_r)==shown_address(ToSeq(probe),False)). MUST verify; else the
# precondition / postcondition rejects a normal F2P input => PRECOND-TOO-STRONG.
_POS_ADMISS = _swap(
    _BASE, _IMPL_TOP,
    "    probe = [48]  # type: List[int]\n"
    "    Assert(Acc(list_pred(probe), 1 / 2))\n"
    "    result = []  # type: List[int]\n    c = 0\n",
)


# ===========================================================================
# UNIQUENESS RIVALS  (spec-too-weak probes -- expect "reject")
# ===========================================================================

# (1) FRAME MUTATION -- MANDATORY (#1 weakness class). addr is read-only at 1/2.
# This rival WRITES `addr[i] = 48` (overwrite each char to '0') before reading it
# in the bracket copy-loop, attempting to normalise the input. Under
# Acc(list_pred(addr),1/2) a store needs FULL permission, so it MUST be rejected
# for INSUFFICIENT PERMISSION (not a value mismatch). All gold invariants/asserts
# are kept verbatim, so the rejection is attributable solely to the write.
_RIVAL_FRAME = _swap(
    _BASE, _BRACKET_READC,
    "            addr[i] = 48\n"
    "            c = addr[i]\n"
    "            Assert(ToSeq(addr).take(i + 1) == ToSeq(addr).take(i) + PSeq(c))\n"
    "            result = result + [c]\n"
    "            i = i + 1\n"
    "        Assert(ToSeq(addr).take(len(addr)) == ToSeq(addr))\n"
    "        Assert(ToSeq(result) == PSeq(91) + ToSeq(addr))\n",
)

# (3a) PARTIAL-DOMAIN -- DROP the wildcard expansion (== model_prepatch.py). The
# wildcard branch produces the bound address VERBATIM ([48], i.e. "0") instead of
# the dotted form [48,46,48,46,48,46,48] ("0.0.0.0"). Inside this branch the
# guard already proved ToSeq(addr)==wildcard_short(), so [48] == addr; the first
# framing assert is re-pinned to wildcard_short() (provable), the gold
# shown_address==wildcard_dotted() assert is kept verbatim (still true). The
# postcondition ToSeq(Result())==shown_address then requires
# wildcard_short()==wildcard_dotted() -- FALSE. This is exactly the pre-patch
# behaviour and the G-DIFF discriminator.
_RIVAL_PREPATCH = _swap(_BASE, _WILD_LIT, "        result = [48]\n")
_RIVAL_PREPATCH = _swap(_RIVAL_PREPATCH, _WILD_ASSERT_RES,
                        "        Assert(ToSeq(result) == wildcard_short())\n")

# (3b) PARTIAL-DOMAIN -- bracket branch DROPS the closing ']'. The bracket result
# is "[" + addr (PSeq(91)+addr) with no trailing PSeq(93). The gold assert
# proving ToSeq(result)==PSeq(91)+ToSeq(addr) (BEFORE the close) is kept; the
# close line and its two +PSeq(93) framing asserts are removed (so they don't
# fail as proof errors). The postcondition ToSeq(Result())==shown_address then
# requires PSeq(91)+addr == PSeq(91)+addr+PSeq(93) -- FALSE for every raw_ipv6
# input. Rejection comes from the POSTCONDITION (bracket-wrap clause).
_RIVAL_DROP_CLOSE = _swap(_BASE, _BRACKET_CLOSE, "")

# (3c) PARTIAL-DOMAIN -- gut the identity (else) branch to a no-op, leaving
# `result` at its initial []. For every non-bracket, non-wildcard address (every
# hostname / IPv4 the command can pass, e.g. "127.0.0.1") the result is [] while
# the spec requires ToSeq(result)==ToSeq(addr). The postcondition cannot be
# closed on any nonempty identity-branch input. Correct only on the empty address.
_RIVAL_GUT_ELSE = _swap(_BASE, _ELSE_BODY, "        result = result\n")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-wildcard-split", "kind": "soundness", "expect": "verify",
     "module": _POS_WILD_SPLIT,
     "rationale": "structurally-different but CORRECT impl: the '0.0.0.0' result is "
                  "built by concatenating two list literals ([48,46,48,46]+[48,46,48]) "
                  "instead of one flat literal -- same value, different construction "
                  "shape. Every gold framing assert is kept verbatim so the proof stays "
                  "valid (both sides concrete sequences). Must verify; else the "
                  "postcondition is over-fit to the literal FORM => SPEC-TOO-STRONG."},
    {"id": "pos-control-bracket-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_BRACKET_RESHAPE,
     "rationale": "structurally-different but CORRECT impl: the closing bracket fragment is "
                  "BUILT INDEPENDENTLY as a typed List[int] (`close = []; close = close + "
                  "[93]`) and concatenated onto `result` (`result = result + close`), instead "
                  "of the flat inline append `result = result + [93]`. Same value, different "
                  "construction shape; all gold framing asserts kept verbatim. Must verify; "
                  "else the postcondition is over-fit to the append FORM => SPEC-TOO-STRONG. "
                  "(The prior `result + [] + [93]` reshape was rejected by a Nagini proof "
                  "artifact -- the untyped empty literal `[]` breaks the list `+` precondition "
                  "on `(result + [])` -- NOT by the spec; the typed `close` removes it.)"},
    {"id": "admiss-selfcall-wildcard", "kind": "admissibility", "expect": "verify",
     "module": _POS_ADMISS,
     "rationale": "the EXACT F2P input -- the wildcard '0' (addr=[48], "
                  "raw_ipv6=False, i.e. addrport=\"0:8000\") -- must establish the "
                  "precondition Acc(list_pred(.),1/2), asserted AT the witness. It is "
                  "asserted rather than exercised by a self-call because the model "
                  "carries Requires(MustTerminate(2)) and a same-level self-call on a "
                  "non-shrinking argument is an obligation leak Nagini is right to "
                  "refuse; the result property that call used to assert stated a fact "
                  "about the CALL, not about the precondition's domain, so it is not "
                  "part of what this case proves. If the precondition rejects this "
                  "normal F2P input => PRECOND-TOO-STRONG. NEGATIVE CONTROL: THERE IS "
                  "NONE, and that is a fact about this precondition rather than about "
                  "the probe. display_address's only frozen clause is "
                  "Acc(list_pred(addr), 1 / 2), and no VALUE violates a permission "
                  "clause: measured, the same assert at probe = [] still reports "
                  "`Verification successful`. So this case checks permission "
                  "admissibility plus the fact that the gold body after it verifies "
                  "under the obligation; it does NOT pin a value domain, and must not "
                  "be read as strong as a case whose precondition carries a length or "
                  "element-domain clause a witness can leave."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutate-addr", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "no faithful real patch corresponds to this: inner_run reads "
                   "self.addr (an immutable str) and only formats it into the "
                   "announcement -- it never mutates the bound address. The rival exists "
                   "solely to test whether the read-only (1/2) precondition can be "
                   "subverted by overwriting `addr`. There is no resolving patch that "
                   "rewrites its input address, so a verifying rival here would be a pure "
                   "verify-not-resolve artifact (vacuous satisfaction via "
                   "self-normalisation).",
     "rationale": "MANDATORY frame-mutation probe. `addr[i] = 48` writes through a 1/2 "
                  "(read-only) reference and MUST fail for INSUFFICIENT PERMISSION (a "
                  "store needs full Acc(list_pred(addr))), NOT a value mismatch; the gold "
                  "invariants/asserts are kept verbatim so the rejection is attributable "
                  "to the write. Rejection source: the PERMISSION SYSTEM. If it verified "
                  "=> SPEC-TOO-WEAK (frame protection hollow)."},
    {"id": "weak-prepatch-no-wildcard", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PREPATCH,
     "refinement": "this is EXACTLY the pre-patch behaviour (model_prepatch.py): the "
                   "wildcard '0' is shown verbatim as '0' instead of expanded to "
                   "'0.0.0.0'. A faithful patch lacking the `elif self.addr==\"0\": "
                   "addr=\"0.0.0.0\"` branch renders 'Starting development server at "
                   "http://0:8000/' for addrport=\"0:8000\" and FAILS the F2P "
                   "test_zero_ip_addr (which asserts http://0.0.0.0:8000/) -- this is the "
                   "precise verify-not-resolve case the bundle's G-DIFF/G-AX discriminator "
                   "is built around.",
     "rationale": "rejection source: the postcondition ToSeq(Result())==shown_address. In "
                  "the wildcard branch the guard proves ToSeq(addr)==wildcard_short(), so "
                  "result==[48]==addr; the gold shown_address==wildcard_dotted() assert is "
                  "kept, so the postcondition reduces to wildcard_short()==wildcard_dotted() "
                  "-- FALSE. If it verified => SPEC-TOO-WEAK (the bundle would no longer "
                  "sense the change it exists to encode)."},
    {"id": "weak-drop-close-bracket", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_CLOSE,
     "refinement": "dropping the closing ']' yields '[' + addr with no terminator, e.g. "
                   "'[::1' for a bracketed IPv6 literal. A faithful patch doing "
                   "f\"[{self.addr}\" (missing the ']') renders a malformed host part and "
                   "FAILS test_runner_addrport_ipv6 / test_runner_hostname_ipv6 (which "
                   "expect the bracketed form '[...]') -- verify-not-resolve.",
     "rationale": "rejection source: the postcondition ToSeq(Result())==shown_address "
                  "(bracket-wrap clause). The pre-close assert ToSeq(result)==PSeq(91)+addr "
                  "is kept and proven; with the close removed the postcondition requires "
                  "PSeq(91)+addr == PSeq(91)+addr+PSeq(93), FALSE on every raw_ipv6 input. "
                  "If it verified => SPEC-TOO-WEAK."},
    {"id": "weak-gut-identity-branch", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_GUT_ELSE,
     "refinement": "gutting the identity branch to a no-op returns [] (empty) for every "
                   "non-bracket non-wildcard address -- every hostname / IPv4 the command "
                   "can pass (e.g. self.addr=='127.0.0.1' from the default, or a custom "
                   "host). A faithful patch returning the empty address renders 'Starting "
                   "development server at http://:8000/' and FAILS the verbatim-address "
                   "P2P cases (test_runner_hostname, test_runner_custom_defaults, "
                   "test_runserver_addrport) -- verify-not-resolve.",
     "rationale": "rejection source: the postcondition ToSeq(Result())==shown_address "
                  "(identity clause). The else branch leaves result==[] while the spec "
                  "requires ToSeq(result)==ToSeq(addr); the postcondition cannot be closed "
                  "on any nonempty identity-branch input. If it verified => SPEC-TOO-WEAK."},
]


# ===========================================================================
# AXIOM LANE -- no @ContractOnly axiom is consumed and no A-reference deep model
# stands in for a library callee (the derivation is primitive string ops modelled
# directly on the code-point carrier). We re-run axiom_check.py's REAL-evaluation
# equivalence (the modelled shown_address == Python's own evaluation of the gold
# patch.diff expression over boundary + fuzz addresses x both flags, AND the
# pre-patch expression differs from gold exactly on the wildcard discriminator) as
# an axiom-soundness probe. axiom_check.py is read on the HOST at load time and
# embedded verbatim (stdlib-only; the runner mounts only the probe at /work). A
# containment probe is N/A -- there is no axiom Requires domain to fall outside.
# ===========================================================================

_AXIOM_CHECK_SRC = (_DIR / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-ref-shown-equals-gold-expression",
        "axiom": "shown_address",  # deep model validated == the gold patch expression
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "the deep model shown_address (pure region) is the only soundness "
                     "obligation: it must equal Python's own evaluation of the gold "
                     "patch.diff expression (f\"[{addr}]\" if raw_ipv6 / \"0.0.0.0\" if "
                     "addr==\"0\" / addr) on every input. This probe (axiom_check.py "
                     "verbatim, stdlib-only) runs the gold expression on 13 boundary "
                     "addresses (the wildcard '0', '0.0.0.0', '00', '0.0', IPv4/IPv6 "
                     "literals, the empty string, hostnames) x both raw_ipv6 values plus a "
                     "randomised fuzz, asserting model_shown == gold_expression, and "
                     "confirms the pre-patch expression differs from gold exactly on the "
                     "wildcard '0' non-IPv6 input. Exit 0 iff every observation agrees; any "
                     "disagreement => the deep model is UNSOUND.",
    },
]
