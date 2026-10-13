"""properties.py — PBT falsification manifest for sympy__sympy-22456.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The function under spec is

    rebuild_from_args(s: Atomic) -> Atomic    # deep model of
                                              # String.func(*String.args) == self

`Atomic` carries only the single facet token equality depends on: its defining
`text: List[int]` of Unicode code points (specified over `PSeq[int]` via ToSeq).
The positional-argument list is modeled by its length alone (it is empty:
`arg_count(s) == 0`). Load-bearing contract of `rebuild_from_args`:

    Requires(Acc(s.text,1/2) and Acc(list_pred(s.text),1/2))     # READ-ONLY input
    Requires(MustTerminate(len(s.text) + 2))                     # THE DELIVERY PIN
    Ensures (Acc(s.text,1/2) and Acc(list_pred(s.text),1/2))     # s returned read-only
    Ensures (Acc(Result().text) and Acc(list_pred(Result().text)))  # fresh full token
    Ensures (arg_count(s) == 0)                                   # empty arg list
    Ensures (ToSeq(Result().text) == ToSeq(s.text))              # THE INVARIANCE PIN

What the spec defends, and the attacks it must survive:

  * THE VALUE PIN is `ToSeq(Result().text) == ToSeq(s.text)`: the reconstruction
    must carry EXACTLY the original text, element for element, even when that text
    is non-empty. This is GROUNDED in the input `s.text` (it is a function of the
    argument's own field), NOT pinned to an opaque @Pure answer-key / exact
    marker. The only @Pure helper, `arg_count(s)`, returns a CONSTANT 0 (it is
    not an answer key for the result text). The discriminating content of the
    reported behaviour is exactly this: a reconstruction that can only source the
    text from the (empty) argument list loses any non-empty text. Every value
    rival reproduces a position where the rebuilt text is NOT exactly s.text (or
    mutates the read-only input to fake it).

  * THE DELIVERY PIN is `Requires(MustTerminate(len(s.text) + 2))`: the value pin
    is claimed of EVERY admissible call, not only of the calls that reach a
    return, so a reconstruction must actually HAND A TOKEN BACK. Without it the
    value pin is satisfiable WITHOUT ESTABLISHING ANYTHING: a reconstruction whose
    body is a call to this same contract on this same token has the pin assumed at
    its own call site and discharges its own conclusion by borrowing it, and an
    advancing-loop reconstruction whose counter never moves reaches no return at
    all. Both are pure verification artifacts — neither ever produces a
    reconstruction for a caller to compare — and both are now rejected for an
    OBLIGATION LEAK, the two reject cases `nondelivery-selfcall-same-token` and
    `nondelivery-loop-no-advance`. Because the level is keyed on the SIZE OF THE
    PAYLOAD BEING REPRODUCED rather than on the mere presence of a self-call, the
    pin does NOT forbid recursion: the positive control `pos-control-descent`
    hands a STRICTLY SMALLER token to the same contract and must still verify. A
    level keyed on `arg_count` (a constant 0) instead of the payload would be
    vacuous, which is why the reject case `nondelivery-selfcall-argcount-level`
    exercises exactly that substitution.

  * The input `s` is held READ-ONLY (Acc(s.text,1/2), Acc(list_pred(s.text),1/2)).
    The MANDATORY attack is FRAME MUTATION (`frame-mutate-overwrite-s`): an impl
    that WRITES to the read-only `s` (rebinds `s.text`) to satisfy the pin
    vacuously must fail for INSUFFICIENT PERMISSION (a field store needs FULL
    permission), not for a wrong value. A second frame-mutation rival
    (`frame-mutate-clear-contents`) writes through the list contents.

  * There are NO @ContractOnly axioms (empty axioms region). The one operation
    that changed — how the atomic token reconstructs itself from its arguments —
    is an A-reference DEEP MODEL (the text-preserving rebuild loop), validated ==
    the real callee by axiom_check.py / G-AX, not consumed in-proof. The axiom
    lane therefore runs the REAL post-patch `String.func(*String.args)` in Docker
    and checks: the deep model (rebuilt token carries exactly the original text;
    func(*args) == self; func(**kwargs()) == self) == the real callee over the
    F2P literal + boundary + fuzz texts (axiom-soundness), and that every text
    the model can reach (any List[int] of code points -> any Python str) is a
    constructible String the real callee accepts (axiom-containment). Both probes
    are SELF-CONTAINED (import only sympy + stdlib): the runner mounts ONLY the
    probe at /work — axiom_check.py is NOT in-container, so its oracle is
    transcribed inline.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`) that
edits ONLY inside the single `# impl-start`/`# impl-end` block of
`rebuild_from_args` (the nested `# invariants-start`/`# invariants-end` block sits
INSIDE that impl region, so loop invariants are freely editable too). The frozen
spec (Requires/Ensures, the @Pure helper, the Atomic constructor) is never
touched, so `markers.same_spec` is guaranteed and a rejection is attributable to
the POSTCONDITION catching wrong behaviour (or the permission system, or the
delivery obligation), never to a tampered spec. Each `expect:"reject"` rival
carries the refinement argument that its faithful real patch would NOT resolve
the F2P (`st.func(*st.args) == st` on `String('foobar')`).

Every variant that keeps a loop carries its own `Invariant(MustTerminate(...))`,
since the shared `Requires(MustTerminate(...))` must be discharged by whatever
body the variant supplies. A value rival that omitted it would be rejected for a
LEAKED OBLIGATION rather than for its wrong value, and the uniqueness finding
would no longer be attributable to the value pin.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-22456"
FLOAT_ENCODING = None  # meta.json float_encoding is null

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmark: the ENTIRE gold impl body of rebuild_from_args, verbatim,
# strictly between `# impl-start` and `# impl-end`. Every variant swaps this
# whole block, so nothing outside the impl region is ever touched.
# ---------------------------------------------------------------------------
_GOLD_IMPL = """    # The reconstruction operation yields the very same token (its result is the
    # original object), so it carries the original text regardless of how many
    # positional arguments there are. Materialise a fresh carrier holding
    # exactly the original text.
    n = len(s.text)
    rebuilt_text = []  # type: List[int]
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
        Invariant(Acc(list_pred(rebuilt_text)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(s.text))
        Invariant(ToSeq(rebuilt_text) == ToSeq(s.text).take(i))
        # At most `n - i` passes remain; `i` rises by exactly one each pass and
        # `n` is loop-invariant, so the bound strictly decreases, and the `+ 1`
        # keeps it positive on the final pass. The reproduction completes.
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        c = s.text[i]
        Assert(ToSeq(s.text).take(i + 1) == ToSeq(s.text).take(i) + PSeq(c))
        rebuilt_text = rebuilt_text + [c]
        i = i + 1
    Assert(i == n)
    Assert(ToSeq(s.text).take(n) == ToSeq(s.text))
    Assert(ToSeq(rebuilt_text) == ToSeq(s.text))
    result = Atomic(rebuilt_text)  # type: Atomic
    Assert(result.text is rebuilt_text)
    Assert(ToSeq(result.text) == ToSeq(s.text))
    return result"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5) Structurally-DIFFERENT but CORRECT reconstruction. Reshape: instead of the
# `c = s.text[i]` + framing assert + `rebuilt_text = rebuilt_text + [c]` triple,
# inline the read into a single-element list literal `[s.text[i]]` and append
# that. This is the SAME forward, front-recursive `take(i)` loop (no induction
# lemma the verifier can't auto-discharge), only the per-iteration spelling
# differs and a local-variable (`elem`) reshape replaces `c`. The framing assert
# `take(i+1) == take(i) + PSeq(...)` and every loop invariant are KEPT verbatim
# (pilot bug #2: a positive control must keep the gold proof obligations). If
# this CORRECT, differently-spelled impl fails to verify, the postcondition is
# over-fit to the exact gold spelling => SPEC-TOO-STRONG.
_POS_RESHAPE = """    # Structurally different but correct: same forward copy, the element read is
    # inlined into the appended single-element list, with a local reshape.
    n = len(s.text)
    rebuilt_text = []  # type: List[int]
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
        Invariant(Acc(list_pred(rebuilt_text)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(s.text))
        Invariant(ToSeq(rebuilt_text) == ToSeq(s.text).take(i))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        elem = s.text[i]  # type: int
        Assert(ToSeq(s.text).take(i + 1) == ToSeq(s.text).take(i) + PSeq(elem))
        one = [elem]  # type: List[int]
        rebuilt_text = rebuilt_text + one
        i = i + 1
    Assert(i == n)
    Assert(ToSeq(s.text).take(n) == ToSeq(s.text))
    Assert(ToSeq(rebuilt_text) == ToSeq(s.text))
    result = Atomic(rebuilt_text)  # type: Atomic
    Assert(result.text is rebuilt_text)
    Assert(ToSeq(result.text) == ToSeq(s.text))
    return result"""
_POS_CONTROL = _swap(_BASE, _GOLD_IMPL, _POS_RESHAPE)

# (6) ADMISSIBILITY / ANTI-OVER-FIT (this is BOTH). A real in-domain call must be
# establishable — not only the permissions, but the DELIVERY LEVEL too. This impl
# reproduces the payload minus its final element into a strictly SMALLER token and
# hands THAT token to this same contract, i.e. it is a RECURSIVE-DESCENT
# reconstruction, the shape a structurally recursive rebuild has. Two ways it can
# fail, and each names a different defect:
#   * if the Acc(.,1/2) permissions cannot be established for a normal freshly
#     built token => PRECOND-TOO-STRONG;
#   * if the delivery obligation rejects a descent on a strictly smaller payload
#     => the level was keyed on the mere PRESENCE of a self-call rather than on the
#     size of the payload being reproduced, i.e. the spec forbids a correct
#     implementation strategy => SPEC-TOO-STRONG / over-fit to the reference loop.
# Paired with `nondelivery-selfcall-same-token` (same-token re-entry, rejected)
# this pins the delivery obligation to NON-DELIVERY rather than to self-calls as
# such. The gold body then runs unchanged on the real `s`.
_ADMISS_IMPL = """    # ADMISSIBILITY + descent: reproduce the payload minus its final element into a
    # strictly SMALLER token and hand that to this same contract; its level is
    # strictly below ours, so the call is admissible and its answer must carry
    # exactly that shorter payload.
    n = len(s.text)
    if n > 0:
        head_text = []  # type: List[int]
        k = 0
        while k < n - 1:
            # invariants-start
            Invariant(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
            Invariant(Acc(list_pred(head_text)))
            Invariant(0 <= k and k <= n - 1)
            Invariant(n == len(s.text))
            Invariant(ToSeq(head_text) == ToSeq(s.text).take(k))
            Invariant(MustTerminate(n - k + 1))
            # invariants-end
            head_text = head_text + [s.text[k]]
            k = k + 1
        smaller = Atomic(head_text)  # type: Atomic
        Assert(len(smaller.text) == n - 1)
        inner = rebuild_from_args(smaller)  # type: Atomic
        Assert(ToSeq(inner.text) == ToSeq(s.text).take(n - 1))
    # gold body on the real argument
    rebuilt_text = []  # type: List[int]
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
        Invariant(Acc(list_pred(rebuilt_text)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(s.text))
        Invariant(ToSeq(rebuilt_text) == ToSeq(s.text).take(i))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        c = s.text[i]
        Assert(ToSeq(s.text).take(i + 1) == ToSeq(s.text).take(i) + PSeq(c))
        rebuilt_text = rebuilt_text + [c]
        i = i + 1
    Assert(i == n)
    Assert(ToSeq(s.text).take(n) == ToSeq(s.text))
    Assert(ToSeq(rebuilt_text) == ToSeq(s.text))
    result = Atomic(rebuilt_text)  # type: Atomic
    Assert(result.text is rebuilt_text)
    Assert(ToSeq(result.text) == ToSeq(s.text))
    return result"""
_ADMISS = _swap(_BASE, _GOLD_IMPL, _ADMISS_IMPL)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (1) FRAME MUTATION — MANDATORY, the #1 weakness class. `s` is read-only
# (Acc(s.text,1/2)). This rival tries to satisfy the pin VACUOUSLY by rebinding
# the read-only field `s.text` to a fresh empty carrier and returning a token
# built from that same empty carrier — so both texts trivially compare equal
# ([] == []) without ever reproducing the original text. Rebinding `s.text`
# requires FULL Acc(s.text); only 1/2 is held, so it must fail for INSUFFICIENT
# PERMISSION (not a wrong value). The field-store is the ONLY deviation from a
# trivially-shaped body, so the failure is attributable solely to the write.
# Rejection source: the PERMISSION SYSTEM.
_FRAME_OVERWRITE = """    # FRAME MUTATION: rebind the READ-ONLY field s.text to fake the invariance.
    cleared = []  # type: List[int]
    s.text = cleared
    result = Atomic([])  # type: Atomic
    return result"""
_RIVAL_FRAME_OVERWRITE = _swap(_BASE, _GOLD_IMPL, _FRAME_OVERWRITE)

# (1b) FRAME MUTATION through the list CONTENTS. Rather than rebind the field,
# this rival appends into the read-only list `s.text` itself (mutating the
# operand the contract observes as unmodified). A list mutation needs FULL
# Acc(list_pred(s.text)); only 1/2 is held => INSUFFICIENT PERMISSION. Rejection
# source: the PERMISSION SYSTEM (the list-predicate half-permission).
_FRAME_CONTENTS = """    # FRAME MUTATION through contents: write into the read-only list s.text.
    s.text.append(0)
    n = len(s.text)
    rebuilt_text = []  # type: List[int]
    i = 0
    while i < n:
        Invariant(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
        Invariant(Acc(list_pred(rebuilt_text)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(s.text))
        Invariant(ToSeq(rebuilt_text) == ToSeq(s.text).take(i))
        Invariant(MustTerminate(n - i + 1))
        c = s.text[i]
        Assert(ToSeq(s.text).take(i + 1) == ToSeq(s.text).take(i) + PSeq(c))
        rebuilt_text = rebuilt_text + [c]
        i = i + 1
    result = Atomic(rebuilt_text)  # type: Atomic
    return result"""
_RIVAL_FRAME_CONTENTS = _swap(_BASE, _GOLD_IMPL, _FRAME_CONTENTS)

# (3a) PARTIAL-DOMAIN — the PRE-FIX reconstruction, as a uniqueness rival. The
# generic positional rebuild can only source the text from the (empty,
# arg_count==0) argument list, so it produces an EMPTY text and returns a token
# carrying []. This is correct ONLY on the sub-domain `s.text == []` (empty text);
# it diverges on EVERY non-empty text. This is exactly model_prepatch.py's body /
# the real pre-fix `String.func(*String.args)` (which actually raises TypeError).
# Rejection source: THE PIN `ToSeq(Result().text) == ToSeq(s.text)` — [] != s.text
# whenever s.text is non-empty.
_PARTIAL_EMPTY = """    # PRE-FIX: rebuild from the empty positional-argument list -> empty text.
    n = arg_count(s)
    rebuilt_text = []  # type: List[int]
    i = 0
    while i < n:
        Invariant(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
        Invariant(Acc(list_pred(rebuilt_text)))
        Invariant(0 <= i and i <= n)
        Invariant(ToSeq(rebuilt_text) == ToSeq(s.text).take(i))
        Invariant(MustTerminate(n - i + 1))
        c = s.text[i]
        rebuilt_text = rebuilt_text + [c]
        i = i + 1
    return Atomic(rebuilt_text)"""
_RIVAL_PARTIAL_EMPTY = _swap(_BASE, _GOLD_IMPL, _PARTIAL_EMPTY)

# (3b) PARTIAL-DOMAIN — DROP THE LAST element. Copy text[0 .. n-2], stopping one
# short. Correct ONLY on the sub-domain `len(s.text) <= 1` (empty or, for the
# empty case, trivially; for a single char it drops it so it is wrong there too —
# in fact it agrees with gold ONLY on the empty text). It diverges on every
# text of length >= 1. Faithful real patch: a func that reconstructs all-but-last
# char — fails the F2P `String('foobar').func(*args) == String('foobar')` (yields
# 'fooba'). Rejection source: THE PIN — ToSeq(Result().text) is take(n-1) of
# s.text, != ToSeq(s.text) whenever n >= 1.
_PARTIAL_DROP_LAST = """    # PARTIAL-DOMAIN: copy all but the last element (off-by-one short).
    n = len(s.text)
    rebuilt_text = []  # type: List[int]
    i = 0
    while i < n - 1:
        Invariant(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
        Invariant(Acc(list_pred(rebuilt_text)))
        Invariant(0 <= i and i <= n - 1)
        Invariant(n == len(s.text))
        Invariant(ToSeq(rebuilt_text) == ToSeq(s.text).take(i))
        Invariant(MustTerminate(n - i))
        c = s.text[i]
        Assert(ToSeq(s.text).take(i + 1) == ToSeq(s.text).take(i) + PSeq(c))
        rebuilt_text = rebuilt_text + [c]
        i = i + 1
    return Atomic(rebuilt_text)"""
_RIVAL_PARTIAL_DROP_LAST = _swap(_BASE, _GOLD_IMPL, _PARTIAL_DROP_LAST)

# (3c) PARTIAL-DOMAIN — DROP THE FIRST element. Copy text[1 .. n-1], skipping
# index 0. Correct ONLY on the empty text; it diverges on every non-empty text
# (it loses the first char). Faithful real patch: a func that reconstructs from
# args[1:] — fails the F2P (yields 'oobar' for 'foobar'). Rejection source: THE
# PIN — the result is a SUFFIX of s.text (take(n) of s.text[1:]), != ToSeq(s.text)
# whenever n >= 1 (the first element is dropped).
_PARTIAL_DROP_FIRST = """    # PARTIAL-DOMAIN: skip index 0 (drop the first element).
    n = len(s.text)
    rebuilt_text = []  # type: List[int]
    i = 1
    while i < n:
        Invariant(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
        Invariant(Acc(list_pred(rebuilt_text)))
        Invariant(1 <= i and i <= n or n == 0)
        Invariant(n == len(s.text))
        Invariant(MustTerminate(n - i + 1))
        c = s.text[i]
        rebuilt_text = rebuilt_text + [c]
        i = i + 1
    return Atomic(rebuilt_text)"""
_RIVAL_PARTIAL_DROP_FIRST = _swap(_BASE, _GOLD_IMPL, _PARTIAL_DROP_FIRST)

# (3d) PARTIAL-DOMAIN / value-double-mask — return the original text length's
# worth of a CONSTANT element (0), not the original elements. The result has the
# RIGHT LENGTH but the WRONG VALUES, so a spec that pinned only the length (or a
# value proxy that drops disagreeing indices) would admit it. The real pin is
# element-wise PSeq equality, so this must reject. Correct ONLY when s.text is
# all-zeros or empty. Faithful real patch: a func that reconstructs a string of
# NUL chars of the right length — fails the F2P (yields '\\x00\\x00...' not
# 'foobar'). Rejection source: THE PIN — ToSeq(Result().text) is a run of 0s,
# != ToSeq(s.text) whenever any element of s.text is non-zero.
_PARTIAL_ZEROS = """    # value-double-mask: right LENGTH, constant (wrong) VALUES.
    n = len(s.text)
    rebuilt_text = []  # type: List[int]
    i = 0
    while i < n:
        Invariant(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
        Invariant(Acc(list_pred(rebuilt_text)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(s.text))
        Invariant(len(rebuilt_text) == i)
        Invariant(MustTerminate(n - i + 1))
        rebuilt_text = rebuilt_text + [0]
        i = i + 1
    return Atomic(rebuilt_text)"""
_RIVAL_PARTIAL_ZEROS = _swap(_BASE, _GOLD_IMPL, _PARTIAL_ZEROS)

# (4a) NON-DELIVERY — SELF-CALL ON THE SAME TOKEN. "The reconstruction of this
# token is whatever the reconstruction of this token returns." The value pin is
# ASSUMED at the call site and discharges the identical conclusion, so the whole
# text-preservation claim is proved by borrowing it and NOTHING about the payload
# is ever established. The call is UNGUARDED, so it sits on a feasible path (this
# is not the vacuity of an unreachable branch). The delivery pin is what refutes
# it: the callee is handed a token whose payload has the SAME size, so its level
# is not strictly below this one. Faithful real patch: a reconstruction whose body
# re-enters the same reconstruction on the same token — it never returns, so the
# invariance assertion can never be observed to hold. Rejection source: THE
# DELIVERY PIN (leaked obligation at the self-call), not a wrong value.
_NONDELIVERY_SELFCALL = """    # NON-DELIVERY: re-enter this very contract on this very token.
    return rebuild_from_args(s)"""
_RIVAL_NONDELIVERY_SELFCALL = _swap(_BASE, _GOLD_IMPL, _NONDELIVERY_SELFCALL)

# (4b) NON-DELIVERY — SELF-CALL WITH THE LEVEL TAKEN FROM THE ARGUMENT COUNT. The
# same borrowing as (4a), but first it establishes that the argument count is zero
# and tries to spend THAT as the delivery level. This is the probe that the level
# is keyed on the payload actually being reproduced and not on the (constant 0)
# argument count: a level read off the argument count would be the same for the
# caller and the callee, so it could never strictly decrease and any obligation
# phrased over it would be vacuous. Faithful real patch: same as (4a) — a
# self-re-entering reconstruction that never delivers. Rejection source: THE
# DELIVERY PIN.
_NONDELIVERY_ARGCOUNT = """    # NON-DELIVERY: try to spend the (always-zero) argument count as the level.
    Assert(arg_count(s) == 0)
    zero = arg_count(s)  # type: int
    Assert(zero == 0)
    return rebuild_from_args(s)"""
_RIVAL_NONDELIVERY_ARGCOUNT = _swap(_BASE, _GOLD_IMPL, _NONDELIVERY_ARGCOUNT)

# (4c) NON-DELIVERY — LOOP THAT NEVER ADVANCES. The copy loop is entered with the
# right invariants but its counter is never incremented, so for any non-empty
# payload the loop never exits and no token is ever handed back; the value pin
# would then be claimed only of runs that reach the return, of which there are
# none. Note it is correct-and-delivering on exactly the EMPTY payload (the loop
# body never runs), which is the boundary the reported behaviour also happens to
# get right — so this is a genuine partial-domain rival, wrong on precisely the
# non-empty payloads that discriminate. Faithful real patch: a reconstruction that
# spins on any non-empty text — the invariance assertion never completes.
# Rejection source: THE DELIVERY PIN (the loop leaks the caller's obligation).
_NONDELIVERY_NOADVANCE = """    # NON-DELIVERY: the copy loop never advances, so nothing is handed back.
    n = len(s.text)
    rebuilt_text = []  # type: List[int]
    i = 0
    while i < n:
        Invariant(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
        Invariant(Acc(list_pred(rebuilt_text)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(s.text))
        Invariant(ToSeq(rebuilt_text) == ToSeq(s.text).take(i))
        c = s.text[i]
        Assert(ToSeq(s.text).take(i + 1) == ToSeq(s.text).take(i) + PSeq(c))
        i = i + 0
    Assert(ToSeq(rebuilt_text) == ToSeq(s.text))
    return Atomic(rebuilt_text)"""
_RIVAL_NONDELIVERY_NOADVANCE = _swap(_BASE, _GOLD_IMPL, _NONDELIVERY_NOADVANCE)


SPEC_TESTS = [
    # ---- positive controls (must verify) ----
    {"id": "pos-control-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_CONTROL,
     "rationale": "structurally-different but CORRECT reconstruction: same forward "
                  "front-recursive take(i) loop (no induction lemma needed), but the "
                  "element read is inlined into the appended single-element list with a "
                  "local-variable reshape; every loop invariant and the take(i+1) framing "
                  "assert are kept verbatim. If this correct, differently-spelled impl "
                  "fails to verify, the postcondition is over-fit to the gold spelling "
                  "=> SPEC-TOO-STRONG."},
    {"id": "pos-control-descent", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "RECURSIVE DESCENT, and it must verify for TWO independent reasons. "
                  "(a) Admissibility: it hands a freshly built in-domain token to this "
                  "same contract, so if the Acc(.,1/2) permissions could not be "
                  "established for a normal input => PRECOND-TOO-STRONG. (b) Anti-over-fit "
                  "for the delivery pin: the token it descends on carries a STRICTLY "
                  "SMALLER payload, so a delivery obligation keyed on the size of the "
                  "payload being reproduced admits it. If it were rejected, the obligation "
                  "would be keyed on the mere PRESENCE of a self-call and would forbid a "
                  "correct implementation strategy (structural recursion) rather than "
                  "demanding delivery => SPEC-TOO-STRONG. Paired with "
                  "nondelivery-selfcall-same-token this pins the obligation to "
                  "NON-DELIVERY rather than to self-calls as such."},

    # ---- uniqueness rivals (must reject) ----
    {"id": "frame-mutate-overwrite-s", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME_OVERWRITE,
     "refinement": "no faithful real patch corresponds to this: the gold reconstruction "
                   "NEVER mutates the original token (`func` returns the same object "
                   "unchanged), and the contract observes `s` as a read-only input "
                   "(Acc(s.text,1/2)). Rebinding s.text to fake the invariance ([]==[]) "
                   "is a pure verification artifact — its real analogue would corrupt the "
                   "input token in place and could not resolve (the F2P compares the "
                   "rebuilt token to the UNMODIFIED original). It must be rejected on "
                   "permission, not silently admitted.",
     "rationale": "rejection from the PERMISSION SYSTEM: under Acc(s.text,1/2) a field "
                  "store `s.text = ...` needs FULL permission, so the impl fails for "
                  "INSUFFICIENT PERMISSION (not a wrong value)."},
    {"id": "frame-mutate-clear-contents", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME_CONTENTS,
     "refinement": "mutating the original token's text list in place (s.text.append(...)) "
                   "has no resolving real-patch analogue: the gold `func` leaves the "
                   "original token untouched and the F2P compares the reconstruction to "
                   "the unmodified original. A patch that appends to the input's payload "
                   "would change the original and break equality. Pure artifact; must be "
                   "rejected on permission.",
     "rationale": "rejection from the PERMISSION SYSTEM: a list mutation needs FULL "
                  "Acc(list_pred(s.text)); only 1/2 is held, so the append fails for "
                  "INSUFFICIENT PERMISSION."},
    {"id": "partial-domain-prefix-empty", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL_EMPTY,
     "refinement": "this IS the pre-fix reconstruction (model_prepatch.py / the real "
                   "pre-fix String.func(*String.args), which sources the text only from "
                   "the empty positional arg list and so loses it — the real code raises "
                   "TypeError). Its faithful real patch is the UNPATCHED code, which FAILS "
                   "the F2P `String('foobar').func(*args) == String('foobar')` (the "
                   "reconstruction has empty text). Definitively non-resolving.",
     "rationale": "rejection from THE PIN ToSeq(Result().text) == ToSeq(s.text): the "
                  "result text is [] (it copies arg_count(s)==0 elements), which equals "
                  "s.text only when s.text is empty; for any non-empty text the "
                  "postcondition fails."},
    {"id": "partial-domain-drop-last", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL_DROP_LAST,
     "refinement": "a reconstruction that copies all-but-the-last element agrees with "
                   "gold only on the empty text; on every text of length >= 1 it under-"
                   "copies. Its faithful real patch (a func dropping the final char) FAILS "
                   "the F2P (yields 'fooba' for 'foobar'). Faithful but non-resolving.",
     "rationale": "rejection from THE PIN: the result text is take(n-1) of s.text, which "
                  "!= ToSeq(s.text) whenever n >= 1 (the last element is missing)."},
    {"id": "partial-domain-drop-first", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL_DROP_FIRST,
     "refinement": "a reconstruction that skips index 0 agrees with gold only on the "
                   "empty text; on every non-empty text it loses the first element. Its "
                   "faithful real patch (a func reconstructing from args[1:]) FAILS the "
                   "F2P (yields 'oobar' for 'foobar'). Faithful but non-resolving.",
     "rationale": "rejection from THE PIN: the result text is a strict SUFFIX of s.text "
                  "(first element dropped), so ToSeq(Result().text) != ToSeq(s.text) for "
                  "any non-empty text."},
    {"id": "value-mask-right-length-wrong-values", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL_ZEROS,
     "refinement": "a reconstruction that emits the RIGHT NUMBER of characters but all "
                   "NUL (constant 0) agrees with gold only on empty/all-zero text; its "
                   "faithful real patch (a func building a NUL-run of the right length) "
                   "FAILS the F2P (yields '\\x00\\x00\\x00\\x00\\x00\\x00' not 'foobar'). "
                   "Faithful but non-resolving. This is the value-level double-mask probe: "
                   "a length-only or disagreeing-index-dropping proxy would wrongly admit "
                   "it.",
     "rationale": "rejection from THE PIN: the result is element-wise pinned "
                  "(ToSeq(Result().text) == ToSeq(s.text)), so a run of 0s != s.text "
                  "whenever any element of s.text is non-zero — length agreement does not "
                  "satisfy the element-wise PSeq equality."},
    {"id": "nondelivery-selfcall-same-token", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NONDELIVERY_SELFCALL,
     "refinement": "its faithful real patch is a reconstruction whose body re-enters the "
                   "same reconstruction on the same token. It applies and is structurally "
                   "the same edit as the resolving one, but it NEVER RETURNS, so the "
                   "invariance assertion `st.func(*st.args) == st` cannot pass and the F2P "
                   "fails. Faithful, admissible, and definitively non-resolving — this is "
                   "the exact shape that made this cell's spec too weak before the delivery "
                   "pin existed, kept here as a permanent regression case.",
     "rationale": "rejection from THE DELIVERY PIN, not from a wrong value: the value pin "
                  "IS satisfiable here by borrowing it (the callee's identical Ensures is "
                  "assumed at the call site and discharges the caller's conclusion, so "
                  "nothing about the payload is ever established). What refutes it is that "
                  "the callee is handed a token of the SAME payload size, so its level is "
                  "not strictly below the caller's => LEAKED OBLIGATION. The call is "
                  "unguarded, so it is on a feasible path and the rejection is not the "
                  "vacuity of an unreachable branch."},
    {"id": "nondelivery-selfcall-argcount-level", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NONDELIVERY_ARGCOUNT,
     "refinement": "the same non-returning reconstruction as the previous case, so the same "
                   "faithful real patch and the same non-resolution; what differs is the "
                   "verification story it tries to tell.",
     "rationale": "rejection from THE DELIVERY PIN. This case exists to show the level is "
                  "keyed on the PAYLOAD BEING REPRODUCED and not on the argument count: it "
                  "first establishes arg_count(s) == 0 and tries to spend that as the level. "
                  "Since the argument count is the same constant for caller and callee, a "
                  "level read off it could never strictly decrease and any obligation "
                  "phrased over it would be vacuous — if THIS were admitted, the delivery "
                  "pin would be decoration."},
    {"id": "nondelivery-loop-no-advance", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NONDELIVERY_NOADVANCE,
     "refinement": "its faithful real patch is a reconstruction that spins on any non-empty "
                   "text; it delivers for the empty text alone, so the F2P (on 'foobar') "
                   "never completes and the instance is not resolved. Faithful but "
                   "non-resolving, and a genuine PARTIAL-DOMAIN rival: correct exactly on "
                   "the empty payload, wrong on precisely the non-empty payloads that "
                   "discriminate the reported behaviour.",
     "rationale": "rejection from THE DELIVERY PIN: the loop advances its counter by zero, "
                  "so no decreasing measure can be supplied for it and it cannot take the "
                  "caller's obligation => LEAKED OBLIGATION at the loop. Without the "
                  "delivery pin this verifies, because every Ensures would be claimed only "
                  "of runs reaching the return and for a non-empty payload there are none."},
]


# ===========================================================================
# AXIOM LANE (Docker, real sympy callee under the gold patch)
# ===========================================================================
# There are NO @ContractOnly axioms (empty axioms region). The one operation that
# changed — how the atomic String token reconstructs itself from its (empty)
# positional arguments — is an A-reference DEEP MODEL (the text-preserving rebuild
# loop), validated == the real callee by axiom_check.py / G-AX, NOT consumed
# in-proof. These two probes run the REAL post-patch String callee in Docker:
#   - axiom-soundness: the deep model's claims — func(*args) == self, the rebuilt
#     token carries EXACTLY the original text (the model's
#     ToSeq(Result().text)==ToSeq(s.text) clause), func(**kwargs()) == self, and
#     the text/arg-count bijections (String(t).text==t, String(t).args==()) — hold
#     on the REAL String over the F2P literal 'foobar' + a boundary family + 5000
#     fuzz texts. This transcribes axiom_check.py's oracle inline (the runner
#     mounts ONLY the probe at /work) and additionally pins the per-element text
#     equality the model's PSeq clause encodes.
#   - axiom-containment: every text the model can reach (its Requires admits ANY
#     List[int] of code points, i.e. any Python str via the type bijection) is a
#     constructible String the real callee accepts, so the A-reference is exercised
#     exactly where the model reaches it. A reachable text the callee could not
#     form would be AXIOM-TOO-WEAK-FOR-CALLER (none exists — String accepts any
#     str).
# Both probes are SELF-CONTAINED (import only sympy + stdlib). They are written for
# old in-container Python (ASCII locale) — no file reads, but the embedded unicode
# is constructed via chr()/code points to avoid any source-encoding hazard.

_AX_INVARIANCE_SOUND = r'''
import random
import sys


def main():
    from sympy.codegen.ast import String

    bad = []
    n = 0

    def check(t):
        st = String(t)
        # (1) text bijection the model relies on
        if st.text != t:
            bad.append(("text bijection", repr(t), repr(st.text)))
            return
        # (2) arg-count pin: text is OFF the positional arg list
        if st.args != ():
            bad.append(("args not empty", repr(t), repr(st.args)))
            return
        # (3a) the discriminating args-invariance: func(*args) == self
        rebuilt = st.func(*st.args)
        if rebuilt != st:
            bad.append(("func(*args) != self", repr(t)))
            return
        # (3b) the model's element-wise text pin: rebuilt carries EXACTLY t
        if rebuilt.text != st.text or rebuilt.text != t:
            bad.append(("rebuilt text != original", repr(t), repr(rebuilt.text)))
            return
        # (3c) the pre-existing kwargs invariance still holds
        if st.func(**st.kwargs()) != st:
            bad.append(("func(**kwargs()) != self", repr(t)))

    # ---- F2P literal (must NOT be skipped) ----
    check('foobar')
    n += 1

    # ---- boundary family (unicode built via code points: ASCII-safe source) ----
    boundary = [
        '',
        'a',
        'foobar',
        'foo bar',
        "Joe's",
        'a"b',
        '<x>&amp;',
        chr(0x00e9) + chr(0x00e0) + chr(0x00fc),   # accents
        chr(0x03a9) + chr(0x2248) + chr(0x221a),   # greek/math
        'x' * 200,
        ' ',
        '\n\t',
        chr(0),            # NUL char (the value-mask rival's wrong reconstruction)
        chr(0x1f600),      # astral emoji
    ]
    for t in boundary:
        check(t)
        n += 1

    # ---- randomized fuzz (ASCII-safe alphabet + a few code points) ----
    rng = random.Random(22456)
    alphabet = [chr(c) for c in range(32, 127)]
    alphabet += [chr(0x00e9), chr(0x03a9), chr(0x2248), chr(0x1f600), chr(0)]
    for _ in range(5000):
        k = rng.randint(0, 24)
        t = ''.join(rng.choice(alphabet) for _ in range(k))
        check(t)
        n += 1

    if bad:
        print("AXIOM-UNSOUND (deep model != real String callee):", bad[:8])
        return 1
    print("invariance A-reference SOUND: real String.func(*args) == self with "
          "rebuilt.text == original text, func(**kwargs()) == self, and the "
          "text/arg-count bijections hold on", n, "texts (F2P 'foobar' + boundary "
          "+ 5000 fuzz).")
    return 0


sys.exit(main())
'''

_AX_INVARIANCE_CONTAIN = r'''
import random
import sys


def main():
    from sympy.codegen.ast import String

    # The model's Requires admits ANY List[int] of Unicode code points, i.e. via
    # the type bijection (List[int] <-> str), ANY Python str. The A-reference
    # callee is String.func; its supported input domain is ANY str (String's
    # constructor _construct_text wraps any text). So every text the model can
    # reach is a constructible String the real callee accepts — the A-reference is
    # exercised exactly where the model reaches it. A reachable text the callee
    # could NOT form would be AXIOM-TOO-WEAK-FOR-CALLER; we confirm none exists by
    # constructing the boundary + a fuzz of code-point sequences (incl. NUL, the
    # empty text, astral chars, long texts) and confirming String(t) builds with
    # text == t and func present.
    bad = []
    n = 0

    def constructible(t):
        try:
            st = String(t)
        except Exception as e:  # noqa: BLE001
            bad.append(("model-reachable text NOT constructible", repr(t), repr(e)))
            return
        if st.text != t:
            bad.append(("constructed text mismatch", repr(t), repr(st.text)))
            return
        if not hasattr(st, 'func'):
            bad.append(("no func on String", repr(t)))

    boundary = [
        '', 'a', 'foobar', 'x' * 500, ' ', '\n\t', chr(0),
        chr(0x00e9), chr(0x03a9), chr(0x1f600),
    ]
    for t in boundary:
        constructible(t)
        n += 1

    rng = random.Random(122456)
    alphabet = [chr(c) for c in range(0, 0x2500)]  # wide BMP range incl. control
    for _ in range(3000):
        k = rng.randint(0, 40)
        t = ''.join(rng.choice(alphabet) for _ in range(k))
        constructible(t)
        n += 1

    if bad:
        print("AXIOM-TOO-WEAK-FOR-CALLER:", bad[:8])
        return 1
    print("containment OK: every text the model can reach (any code-point sequence "
          "-> any str, incl. NUL/astral/empty/long) is a constructible String the "
          "real func callee accepts.", n, "texts confirmed.")
    return 0


sys.exit(main())
'''

AXIOM_TESTS = [
    {"id": "ax-invariance-sound", "axiom": "invariance-A-reference",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _AX_INVARIANCE_SOUND,
     "rationale": "if the real post-patch String.func(*String.args) is NOT equal to the "
                  "original token, or the rebuilt token's text is not exactly the original "
                  "text, on any input => the A-reference deep model is unsound "
                  "(AXIOM-UNSOUND). Strengthens axiom_check.py: it transcribes the same "
                  "oracle inline and additionally pins the element-wise text equality the "
                  "model's PSeq clause encodes, over the F2P literal + boundary + 5000 "
                  "fuzz texts (incl. NUL/astral)."},
    {"id": "ax-invariance-containment", "axiom": "invariance-A-reference",
     "kind": "axiom-containment", "expect": "covered", "apply_gold": True,
     "probe": _AX_INVARIANCE_CONTAIN,
     "rationale": "every text the model can reach (its Requires admits any List[int] of "
                  "code points, i.e. any str) is a constructible String the real func "
                  "callee accepts, so the A-reference is exercised exactly where the model "
                  "reaches it. A reachable text the callee could not form would be "
                  "AXIOM-TOO-WEAK-FOR-CALLER (none exists — String accepts any str)."},
]
