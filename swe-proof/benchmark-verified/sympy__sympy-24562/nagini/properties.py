# properties.py — PBT manifest for sympy__sympy-24562. NOT a Nagini module; a
# record of adversarial falsification cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT.
#
# Defended surface (read from model.py / refinement.md / mapping.md / meta.json):
#   combine_ratio(p_num, p_den, q_digits: List[int], q_den) -> Tuple[int,int]
#     READ-ONLY input  q_digits           (Requires Acc(list_pred(q_digits), 1/2))
#     LOAD-BEARING posts:
#       Result()[0] == p_num * q_den                       (numerator branch)
#       Result()[1] == p_den * read_int(ToSeq(q_digits))   (denominator branch)
#     FRAME posts (gold, kept verbatim in every rival):
#       Acc(list_pred(q_digits), 1/2)  +  len(ToSeq(q_digits)) >= 1  +
#       all-digit Forall preserved.
#   read_int : @Pure @ContractOnly axiom (A-consumed). Ensures(Result() >= 0)
#     ONLY -- the integer VALUE is UNPINNED. Crucially it is GROUNDED in the actual
#     input handle: the postcondition term is read_int(ToSeq(q_digits)) over THE
#     SAME q_digits the impl reads, NOT an opaque pre-computed answer key. There is
#     no fixed scalar to "echo": any impl satisfying Result()[1]==p_den*read_int(
#     ToSeq(q_digits)) must actually form p_den * read_int(<that handle>). So the
#     ungrounded-oracle-echo class does NOT apply here (see assessment); we instead
#     give an honest cheapest-impl positive control + the read-then-scale rivals.
#   aux_value : @Pure @ContractOnly axiom (A-reference). UNPINNED (Result() >= 0).
#     Never referenced by model.py's proof or postconditions -- only by the hidden
#     model_prepatch.py impl (repeat-then-read). It cannot be used to cheat the
#     model.py spec because the postcondition never mentions it.
#
# Region-surgery (_swap on _BASE) edits ONLY inside the # impl-start/# impl-end
# region, so every spec case is same_spec by construction (the frozen
# axioms/pure/pre/post-conditions are never touched).
from pathlib import Path

INSTANCE = "sympy__sympy-24562"
FLOAT_ENCODING = None  # meta.json float_encoding is null and unused


_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The gold impl body (exactly the text strictly inside # impl-start/# impl-end).
# Every rival is a _swap of this block; the markers, signature, axioms, pure,
# and pre/post-conditions are never touched -> same_spec holds by construction.
# ---------------------------------------------------------------------------
_GOLD = """    # The integer value of the divisor's textual numerator.
    q_value = read_int(ToSeq(q_digits))  # type: int
    # The numerator picks up the divisor's denominator; the denominator picks
    # up the dividend's denominator and the divisor's integer value.
    out_num = p_num * q_den  # type: int
    out_den = p_den * q_value  # type: int
    return (out_num, out_den)"""


# ===========================================================================
# (1) FRAME-MUTATION — MANDATORY: q_digits is read-only (Acc(list_pred,1/2)).
# A rival that WRITES the (non-empty) input list back to itself is a VALUE
# no-op on the digit sequence, so the postcondition value/frame clauses would
# still hold; the spec must reject it purely for INSUFFICIENT PERMISSION
# (writing q_digits[0] needs full list_pred(q_digits), the contract grants only
# 1/2). All gold computation/return is kept verbatim so the rejection is
# attributable solely to the write.
# ===========================================================================
_frame_mut = _swap(
    _BASE,
    _GOLD,
    """    # The integer value of the divisor's textual numerator.
    q_value = read_int(ToSeq(q_digits))  # type: int
    # WRITE to the read-only input -> needs FULL list_pred(q_digits) permission
    # but the contract grants only Acc(list_pred(q_digits), 1/2): insufficient.
    q_digits[0] = q_digits[0]
    out_num = p_num * q_den  # type: int
    out_den = p_den * q_value  # type: int
    return (out_num, out_den)""",
)


# ===========================================================================
# (2) PARTIAL-DOMAIN on the NUMERATOR — correct on integer dividends
# (p_den == 1) but drops the q_den factor on fractional dividends (p_den > 1).
# This is the verdict's exact counterexample shape: the OLD narrow spec (which
# only ever saw p_den==1) admitted `out_num = p_num`. The widened spec pins
# Result()[0] == p_num * q_den for ALL p_den, so this must be REJECTED.
# ===========================================================================
_partial_num = _swap(
    _BASE,
    _GOLD,
    """    # The integer value of the divisor's textual numerator.
    q_value = read_int(ToSeq(q_digits))  # type: int
    # Numerator: correct only on integer dividends; drops q_den when p_den > 1.
    if p_den == 1:
        out_num = p_num * q_den  # type: int
    else:
        out_num = p_num  # WRONG on fractional dividend: omits the q_den factor
    out_den = p_den * q_value  # type: int
    return (out_num, out_den)""",
)


# ===========================================================================
# (3) DENOMINATOR uses q_den instead of the read value (atk_7 family) — a
# same-spec WRONG impl that forms out_den = p_den * q_den, ignoring the
# divisor's textual numeric value entirely. Must fail the denominator post.
# ===========================================================================
_den_uses_qden = _swap(
    _BASE,
    _GOLD,
    """    # The integer value of the divisor's textual numerator.
    q_value = read_int(ToSeq(q_digits))  # type: int
    out_num = p_num * q_den  # type: int
    # WRONG: denominator uses q_den in place of the read value read_int(q_digits).
    out_den = p_den * q_den  # type: int
    return (out_num, out_den)""",
)


# ===========================================================================
# (4) DENOMINATOR drops p_den (atk_4 family) — out_den = q_value, ignoring the
# dividend's denominator. Must fail the denominator post.
# ===========================================================================
_den_drops_pden = _swap(
    _BASE,
    _GOLD,
    """    # The integer value of the divisor's textual numerator.
    q_value = read_int(ToSeq(q_digits))  # type: int
    out_num = p_num * q_den  # type: int
    # WRONG: denominator omits the dividend denominator factor p_den.
    out_den = q_value  # type: int
    return (out_num, out_den)""",
)


# ===========================================================================
# (5) POSITIVE CONTROL (soundness) — structurally DIFFERENT but CORRECT.
# Shape change: read the token FIRST, form the denominator BEFORE the numerator,
# and use a single tuple-construction local. No loop, no fold, no framing
# lemma needed (the postcondition is pure integer arithmetic over read_int of
# the SAME handle), so this is pilot-safe: it touches no proof obligation the
# gold proof did not already discharge. If a faithful correct impl of this shape
# cannot verify => SPEC-TOO-STRONG.
# ===========================================================================
_pos_ctrl = _swap(
    _BASE,
    _GOLD,
    """    # Read the divisor's textual numerator first, build the denominator
    # before the numerator, in the opposite statement order.
    q_value = read_int(ToSeq(q_digits))  # type: int
    out_den = p_den * q_value  # type: int
    # multiplication commuted (q_den * p_num instead of p_num * q_den)
    out_num = q_den * p_num  # type: int
    result = (out_num, out_den)  # type: Tuple[int, int]
    return result""",
)


# ===========================================================================
# (6) ADMISSIBILITY — the precondition must admit a normal F2P-shaped input.
# Inside the impl we ASSERT the post-shaped facts hold for the actual handle
# (the all-digit read is non-negative, the 1/2 permission round-trips and the
# digits remain readable) before returning the gold pair. If the precondition
# could not be established for a legitimate F2P-shaped input these asserts /
# the read would fail => PRECOND-TOO-STRONG. Uses only permissions the gold
# proof already holds (read q_digits under Acc(...,1/2); call the pure read_int).
# ===========================================================================
_admiss = _swap(
    _BASE,
    _GOLD,
    """    # The integer value of the divisor's textual numerator.
    q_value = read_int(ToSeq(q_digits))  # type: int
    # admissibility: a normal F2P-shaped input establishes the Requires --
    # the all-digit token reads to a non-negative integer, the read-only 1/2
    # permission round-trips, and the digit sequence remains readable.
    Assert(q_value == read_int(ToSeq(q_digits)))
    Assert(q_value >= 0)
    Assert(Acc(list_pred(q_digits), 1 / 2))
    Assert(len(ToSeq(q_digits)) >= 1)
    out_num = p_num * q_den  # type: int
    out_den = p_den * q_value  # type: int
    return (out_num, out_den)""",
)


SPEC_TESTS = [
    {
        "id": "frame-mut-qdigits",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _frame_mut,
        "refinement": (
            "Writing q_digits[0]=q_digits[0] is a VALUE no-op on the digit "
            "sequence, so a 'faithful' real patch that mutated the textual "
            "divisor numerator in place would still compute the same "
            "read-then-scale (numerator, denominator) and could look correct on "
            "the F2P grid -- the value abstraction cannot see the write. The "
            "real Rational.__new__ only READS the parsed operands (q.p / q.q) "
            "and never mutates the incoming token; it parses a fresh Rational "
            "(q = Rational(q)). A patch that mutated the input string/object "
            "would corrupt a shared/interned operand and is not what the gold "
            "patch does, so it would not be the faithful fix. The spec must "
            "reject it on PERMISSION grounds, matching the read-only carrier."
        ),
        "rationale": (
            "Rejection comes from the permission system, NOT a postcondition "
            "value clause: assigning q_digits[0] needs full list_pred(q_digits) "
            "write permission but the precondition/return grant only "
            "Acc(list_pred(q_digits), 1/2). INSUFFICIENT PERMISSION."
        ),
    },
    {
        "id": "partial-domain-numerator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _partial_num,
        "refinement": (
            "Returning p_num (no q_den factor) on fractional dividends "
            "(p_den > 1) is the verdict's counterexample: the old NARROW spec "
            "(which only saw p_den==1) admitted out_num=p_num. The faithful "
            "real correspondent drops the `p *= q.q` step for a fractional "
            "dividend, so the numerator omits q.q (= q_den). On the F2P grid "
            "this misdecides every cell with a fractional dividend AND a "
            "fractional divisor -- e.g. Rational('1.5','1.5') (p_den=2,q_den=2) "
            "would give numerator 3 instead of 3*2=6, so "
            "as_numer_denom() != Rational('1.5/1.5').as_numer_denom() -- the "
            "first-failing F2P cell. It does NOT resolve."
        ),
        "rationale": (
            "Rejection from the numerator postcondition Result()[0]==p_num*q_den: "
            "on the p_den>1 branch the impl returns p_num, which is not "
            "p_num*q_den whenever q_den != 1."
        ),
    },
    {
        "id": "denominator-uses-qden",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _den_uses_qden,
        "refinement": (
            "out_den = p_den * q_den ignores the divisor's textual numeric value "
            "entirely. The faithful real correspondent would accumulate q.q "
            "(the divisor DENOMINATOR) into the denominator instead of q.p (the "
            "divisor numerator the token spells). On the headline "
            "Rational('0.5','100') (p_den=2, q_den=1) this gives denominator "
            "2*1=2 instead of 2*100=200, so the result is 100/2 reduced != "
            "1/200. It does NOT resolve (F2P asserts Rational('0.5','100') == "
            "Rational(1,200))."
        ),
        "rationale": (
            "Rejection from the denominator postcondition "
            "Result()[1]==p_den*read_int(ToSeq(q_digits)): p_den*q_den is not "
            "p_den*read_int(q_digits) whenever the spelled value != q_den, which "
            "read_int leaves free (its value is unpinned, so the verifier cannot "
            "prove the equality)."
        ),
    },
    {
        "id": "denominator-drops-pden",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _den_drops_pden,
        "refinement": (
            "out_den = read_int(q_digits) omits the dividend denominator factor "
            "p_den. The faithful real correspondent drops the `Q *= p.q` "
            "accumulation, so a fractional dividend loses its denominator. On "
            "the headline Rational('0.5','100') (p_den=2, read_int=100) the "
            "constructed denominator would be 100 instead of 2*100=200, giving "
            "1/100 (after reduction) instead of 1/200, so the F2P assertion "
            "Rational('0.5','100') == Rational(1,200) fails. It does NOT resolve."
        ),
        "rationale": (
            "Rejection from the denominator postcondition "
            "Result()[1]==p_den*read_int(ToSeq(q_digits)): read_int(q_digits) "
            "alone is not p_den*read_int(q_digits) whenever p_den != 1."
        ),
    },
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_ctrl,
        "rationale": (
            "A structurally-different but CORRECT impl: token read first, "
            "denominator formed before the numerator, multiplication commuted "
            "(q_den * p_num), result built via a named tuple local. It computes "
            "the identical (p_num*q_den, p_den*read_int(q_digits)) pair and must "
            "verify. If it cannot, the postcondition is SPEC-TOO-STRONG. The "
            "shape change is statement-reorder / local-reshape only (pilot-safe: "
            "no loop, no fold, no framing lemma -- the postcondition is pure "
            "integer arithmetic the gold proof already discharges)."
        ),
    },
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss,
        "rationale": (
            "The precondition (Acc(list_pred(q_digits),1/2), len>=1, all-digit, "
            "p_den>=1, q_den>=1) must admit a normal F2P-shaped input. The impl "
            "asserts the load-bearing Requires-derived facts -- the all-digit "
            "read is non-negative, the read-only 1/2 permission round-trips, the "
            "digit sequence stays readable -- before returning the gold pair. If "
            "these cannot be established the precondition is PRECOND-TOO-STRONG. "
            "Uses only permissions the gold proof already holds."
        ),
    },
]


# ===========================================================================
# AXIOM LANE — the bundle has two @ContractOnly axioms:
#   read_int  (A-consumed):  Requires non-empty all-digit token (48<=d<=57);
#                            Ensures Result() >= 0. Real callee: the textual
#                            integer reader the constructor uses,
#                            fractions.Fraction(s).numerator (== int(s) for an
#                            all-digit s), reached via q = Rational(q) -> Q*=q.p.
#   aux_value (A-reference): Requires non-empty all-digit token AND n>=1;
#                            Ensures Result() >= 0 (value UNPINNED). Real
#                            operation: repeat-then-read, fractions.Fraction(
#                            s*n).numerator (the pre-patch q*=p.q on the textual
#                            divisor). Used only by model_prepatch.py.
# Both probes import only the stdlib `fractions` (the very parser Rational(str)
# uses for a textual operand), so they are self-contained and run in any
# instance image. They mirror axiom_check.py's logic. Soundness + containment
# are both covered: every input fuzzed lies in the axiom's Requires domain
# (containment), and we additionally fuzz the Requires-EXCLUDED boundary to
# confirm the tight precondition does not over-claim.
# ===========================================================================

_READ_INT_PROBE = r'''
import fractions, random, sys

FAIL = []
def fail(m):
    FAIL.append(m); print("VIOLATION:", m)

def read_int_real(s):
    # the real textual-integer reader the constructor uses for an all-digit
    # operand (q = Rational(q) -> fractions.Fraction(q).numerator)
    return fractions.Fraction(s).numerator

def is_req_ok(s):
    return len(s) >= 1 and all('0' <= ch <= '9' for ch in s)

def check_ensures(s):
    # CONTAINMENT: s is in read_int's Requires domain (non-empty all-digit).
    assert is_req_ok(s)
    v = read_int_real(s)                       # must not raise
    if not (isinstance(v, int) and v >= 0):
        fail("read_int unsound: %r -> %r (expected non-negative int)" % (s, v))
    if v != int(s):
        fail("read_int value mismatch: %r reader=%r int=%r" % (s, v, int(s)))

# boundary all-digit tokens (incl. the headline witnesses '100', '0', '15')
for s in ["0", "1", "9", "00", "100", "200", "1001", "0123456789",
          "9" * 40, "100100", "5", "15", "150"]:
    check_ensures(s)

# randomized all-digit fuzz -- every input lies inside the Requires domain
rng = random.Random(24562)
for _ in range(20000):
    L = rng.randint(1, 24)
    s = "".join(rng.choice("0123456789") for _ in range(L))
    check_ensures(s)

# Requires-EXCLUDED boundary (over-claim guard): on a NON-all-digit input the
# real reader returns a NEGATIVE value or RAISES -- so excluding it is correct
# and Ensures(Result()>=0) is sound ONLY because the precondition is tight.
# (We do NOT require it to raise; if it parses, it may be negative -- the very
# over-claim the tight Requires avoids. This is a soundness witness, not a
# containment failure.)
witnessed_neg_or_raise = 0
for s in ["", "-5", "-100", "+7", " 5", "5 ", "1.5", "1/2", "abc",
          "12a", "0x10", "1e3", "  ", "\t1"]:
    assert not is_req_ok(s)
    try:
        v = read_int_real(s)
    except (ValueError, ZeroDivisionError):
        witnessed_neg_or_raise += 1
        continue
    if not isinstance(v, int):
        fail("excluded input %r gave non-int %r" % (s, v))
    if v < 0:
        witnessed_neg_or_raise += 1
if witnessed_neg_or_raise == 0:
    fail("no Requires-excluded input went negative or raised -- precondition "
         "may be needlessly tight or the over-claim guard is vacuous")

if FAIL:
    print("READ_INT AXIOM FAILED: %d violation(s)" % len(FAIL)); sys.exit(1)
print("READ_INT OK: real fractions.Fraction reader is non-negative (== int(s)) "
      "on 13 boundary + 20000 all-digit fuzz tokens (all in Requires domain); "
      "%d Requires-excluded inputs go negative/raise (no over-claim)."
      % witnessed_neg_or_raise)
sys.exit(0)
'''

_AUX_VALUE_PROBE = r'''
import fractions, random, sys

FAIL = []
def fail(m):
    FAIL.append(m); print("VIOLATION:", m)

def read_int_real(s):
    return fractions.Fraction(s).numerator

def aux_value_real(s, n):
    # the value the pre-patch alternative reading obtains: repeat the digit
    # token n times (Python str repetition), then read the longer token once
    # (the pre-patch `q *= p.q` while q was still the textual divisor).
    return fractions.Fraction(s * n).numerator

def is_req_ok(s):
    return len(s) >= 1 and all('0' <= ch <= '9' for ch in s)

def check_ensures(s, n):
    # CONTAINMENT: (s, n) in aux_value's Requires domain (all-digit, n>=1).
    assert is_req_ok(s) and n >= 1
    v = aux_value_real(s, n)                    # must not raise
    if not (isinstance(v, int) and v >= 0):
        fail("aux_value unsound: (%r,%d) -> %r (expected non-negative int)"
             % (s, n, v))
    if v != int(s * n):
        fail("aux_value value mismatch: (%r,%d) real=%r int(s*n)=%r"
             % (s, n, v, int(s * n)))

# boundary (s, n) -- every input in the Requires domain
for s, n in [("100", 2), ("1", 1), ("9", 5), ("5", 2), ("200", 3),
             ("12", 4), ("0", 2), ("100", 1), ("15", 2), ("150", 2)]:
    check_ensures(s, n)

rng = random.Random(124562)
for _ in range(5000):
    L = rng.randint(1, 12)
    s = "".join(rng.choice("0123456789") for _ in range(L))
    n = rng.randint(1, 6)
    check_ensures(s, n)

# The DISCRIMINATING arithmetic fact the denominator postcondition relies on:
# repeat-then-read is NOT read-then-scale, so an impl that used aux_value for
# the denominator provably cannot satisfy Result()[1]==p_den*read_int(...).
# This is exactly the reported bug: Rational('0.5','100') -> 1/100100 not 1/200.
if aux_value_real("100", 2) != 100100:
    fail("aux_value('100',2) != 100100")
if read_int_real("100") * 2 != 200:
    fail("read_int('100')*2 != 200")
if aux_value_real("100", 2) == read_int_real("100") * 2:
    fail("aux_value('100',2) unexpectedly == read_int('100')*2 (no discriminator)")
differ = 0
for _ in range(5000):
    L = rng.randint(1, 8)
    s = "".join(rng.choice("0123456789") for _ in range(L))
    if s[0] == "0":
        continue
    n = rng.randint(2, 6)
    if aux_value_real(s, n) != read_int_real(s) * n:
        differ += 1
if differ == 0:
    fail("expected repeat-then-read to differ from read-then-scale in fuzz")

if FAIL:
    print("AUX_VALUE AXIOM FAILED: %d violation(s)" % len(FAIL)); sys.exit(1)
print("AUX_VALUE OK: real repeat-then-read is non-negative (== int(s*n)) on 10 "
      "boundary + 5000 fuzz (all in Requires domain); discriminating fact "
      "int(s*n) != n*int(s) confirmed (%d differ in fuzz)." % differ)
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-read-int-sound",
        "axiom": "read_int",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _READ_INT_PROBE,
        "rationale": (
            "read_int (A-consumed) stands for the real textual-integer reader "
            "fractions.Fraction(s).numerator the constructor uses for a textual "
            "divisor numerator (q = Rational(q) -> Q *= q.p). The axiom's only "
            "Ensures is Result() >= 0 on a non-empty all-digit token. The probe "
            "runs the REAL reader on 13 boundary + 20000 fuzz all-digit tokens "
            "(every one inside the Requires domain -- the all-digit containment "
            "the model can reach) and asserts non-negativity + the exact value "
            "int(s); a violation would be AXIOM-UNSOUND. It ALSO fuzzes the "
            "Requires-EXCLUDED boundary (sign/empty/decimal/slash/non-digit/"
            "whitespace) to confirm those are exactly where the reader goes "
            "negative or raises -- justifying the tight precondition (no "
            "over-claim)."
        ),
    },
    {
        "id": "ax-read-int-containment",
        "axiom": "read_int",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _READ_INT_PROBE,
        "rationale": (
            "Containment: the ONLY callee-input the model can pass to read_int "
            "is ToSeq(q_digits), and the precondition forces it non-empty "
            "(len>=1) and all-digit (48<=q_digits[k]<=57) -- the postcondition "
            "frame clauses preserve exactly that. Every token the probe exercises "
            "satisfies is_req_ok (non-empty all-digit), so each caller-reachable "
            "input lies inside read_int's Requires domain. A reachable input "
            "OUTSIDE that domain would be AXIOM-TOO-WEAK-FOR-CALLER; none exists "
            "(the caller can never reach a sign/decimal/empty token because the "
            "precondition excludes them). Shares the read_int probe (same "
            "obligation, exercised over the in-domain inputs)."
        ),
    },
    {
        "id": "ax-aux-value-sound",
        "axiom": "aux_value",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AUX_VALUE_PROBE,
        "rationale": (
            "aux_value (A-reference) stands for the repeat-then-read value "
            "fractions.Fraction(s*n).numerator (the pre-patch `q *= p.q` on the "
            "textual divisor). The axiom's only Ensures is Result() >= 0 on a "
            "non-empty all-digit token with n>=1; its value is deliberately "
            "UNPINNED. The probe runs the REAL operation on 10 boundary + 5000 "
            "fuzz (s,n) (all in the Requires domain) asserting non-negativity + "
            "the value int(s*n); a violation is AXIOM-UNSOUND. It also confirms "
            "the discriminating fact int(s*n) != n*int(s) that makes the "
            "denominator postcondition reject the prepatch repeat-then-read path. "
            "aux_value is never referenced by model.py's proof/postconditions "
            "(only by the hidden model_prepatch.py), so its soundness is the only "
            "obligation; there is no caller-reachable input to contain (model.py "
            "never calls it)."
        ),
    },
]
