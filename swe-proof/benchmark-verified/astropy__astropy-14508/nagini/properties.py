"""properties.py — PBT falsification battery for astropy__astropy-14508.

NOT a Nagini module. A record of adversarially-reasoned cases the runner
(swebench_nagini.pbt) executes:

  * SPEC_TESTS  — full model.py variants that share the FROZEN spec exactly
                  (built by region-surgery: every _swap edits ONLY text inside
                  the # impl-start / # impl-end region, so same_spec is
                  guaranteed). Checked on the host by Nagini verify.
  * AXIOM_TESTS — real-callee probes run in the instance Docker image.

Defended surface (format_float_field(value: float) -> List[int]):
  The renderer turns a finite real into a <=20-char decimal field using the
  MINIMAL number of significant digits. The load-bearing postcondition has four
  clauses:
    (1) Acc(list_pred(Result())) and 1 <= len(Result()) <= 20        (well-formed/cap)
    (2) Implies(shortest_field_len(value) <= 20,
                ToSeq(Result()) == shortest_seq(value))               (fits => exact minimal rendering; the HEADLINE)
    (3) Implies(over-cap and no exponent,
                ToSeq(Result()) == shortest_seq(value).take(20))      (truncate decimals)
    (4) Implies(over-cap and exponent at idx,
                ToSeq(Result()) == take(20-(len-idx)) + drop(idx))    (keep the WHOLE exponent suffix)

  The oracle shortest_seq is GROUNDED, not an answer-key: G-AX validates it ==
  str(value).replace('e','E') (CPython shortest round-tripping repr) on ~240k
  finite floats, and clauses (3)/(4) require the result to be PRODUCED BY a
  take/drop/concat OF that exact rendering -- so it cannot be echoed as a
  constant. The discriminator the gold patch introduces is significant-digit
  MINIMALITY (str spends 4 digits for 0.009125; f"{v:.16G}" spends 16).

  There is NO read-only list/object input: the only argument is an interpreted
  float (a value, not a heap location), so the frame-mutation class is N/A here
  (nothing to over-permission / overwrite). See 'assessment'. The applicable
  weakness classes are partial-domain (over-cap content), ungrounded-oracle
  (here: grounded, so cheapest-honest positive control instead), and the
  minimality discriminator (echo the pre-patch renderer).

  Axiom lane: six @ContractOnly axioms (shortest_field / shortest_seq are
  A-reference deep models of str(value).replace('e','E'); parse_dec / sig_count
  / min_sig / shortest_field_len the supporting numeric theory). Probes execute
  the real stdlib callees and assert axiom-soundness on the finite-float domain,
  plus a caller-domain containment check.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-14508"
FLOAT_ENCODING = "real"   # meta.json verify.flags = ["--float-encoding=real"]

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors (all are substrings of the # impl-start .. # impl-end region only).
# ---------------------------------------------------------------------------

# The two declaration+early-return lines, used to reshape (positive control).
_DECL_BLOCK = (
    "    vs = shortest_field(value, neg)\n"
    "    n = len(vs)\n"
    "    if n <= 20:\n"
    "        return vs\n"
    "    # Over the cap: trim to 20 characters, preserving any exponent suffix. The\n"
    "    # carrier `vs` IS the exact rendering (ToSeq(vs) == shortest_seq(value, neg)),\n"
    "    # so the trim is stated structurally against it via take/drop/concat.\n"
    "    idx = e_index(ToSeq(vs))\n"
    "    result = []  # type: List[int]\n"
    "    old_seq = ToSeq(result)  # type carrier for the per-append step (see below)\n"
)

# The whole over-cap branching block (idx<0 first-20 loop + else exponent-keep),
# used to replace the exponent-preserving trim with a first-20 truncation (a4).
_OVERCAP_BLOCK = (
    "    idx = e_index(ToSeq(vs))\n"
    "    result = []  # type: List[int]\n"
    "    old_seq = ToSeq(result)  # type carrier for the per-append step (see below)\n"
    "    if idx < 0:\n"
    "        j = 0\n"
    "        while j < 20:\n"
    "            # invariants-start\n"
    "            Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))\n"
    "            Invariant(0 <= j and j <= 20 and n == len(vs) and n > 20)\n"
    "            Invariant(n == shortest_field_len(value, neg))\n"
    "            Invariant(ToSeq(vs) == shortest_seq(value, neg))\n"
    "            Invariant(idx == e_index(ToSeq(vs)) and idx < 0)\n"
    "            Invariant(len(result) == j)\n"
    "            Invariant(ToSeq(result) == ToSeq(vs).take(j))\n"
    "            Invariant(MustTerminate(20 - j + 1))\n"
    "            # invariants-end\n"
    "            old_seq = ToSeq(result)\n"
    "            result.append(vs[j])\n"
    "            Assert(ToSeq(result) == old_seq + PSeq(vs[j]))\n"
    "            Assert(ToSeq(vs).take(j) + PSeq(ToSeq(vs)[j]) == ToSeq(vs).take(j + 1))\n"
    "            j = j + 1\n"
    "        Assert(ToSeq(result) == shortest_seq(value, neg).take(20))\n"
    "    else:\n"
    "        keep = 20 - (n - idx)\n"
    "        j = 0\n"
    "        while j < keep:\n"
    "            # invariants-start\n"
    "            Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))\n"
    "            Invariant(0 <= idx and idx < n and n == len(vs) and n > 20)\n"
    "            Invariant(n == shortest_field_len(value, neg))\n"
    "            Invariant(ToSeq(vs) == shortest_seq(value, neg))\n"
    "            Invariant(idx == e_index(ToSeq(vs)))\n"
    "            Invariant(keep == 20 - (n - idx) and keep >= 0 and keep <= idx)\n"
    "            Invariant(0 <= j and j <= keep and len(result) == j)\n"
    "            Invariant(ToSeq(result) == ToSeq(vs).take(j))\n"
    "            Invariant(MustTerminate(keep - j + 1))\n"
    "            # invariants-end\n"
    "            old_seq = ToSeq(result)\n"
    "            result.append(vs[j])\n"
    "            Assert(ToSeq(result) == old_seq + PSeq(vs[j]))\n"
    "            Assert(ToSeq(vs).take(j) + PSeq(ToSeq(vs)[j]) == ToSeq(vs).take(j + 1))\n"
    "            j = j + 1\n"
    "        Assert(ToSeq(result) == ToSeq(vs).take(keep))\n"
    "        k = idx\n"
    "        while k < n:\n"
    "            # invariants-start\n"
    "            Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))\n"
    "            Invariant(0 <= idx and idx <= k and k <= n and n == len(vs) and n > 20)\n"
    "            Invariant(n == shortest_field_len(value, neg))\n"
    "            Invariant(ToSeq(vs) == shortest_seq(value, neg))\n"
    "            Invariant(idx == e_index(ToSeq(vs)))\n"
    "            Invariant(keep == 20 - (n - idx) and keep >= 0)\n"
    "            Invariant(len(result) == keep + (k - idx))\n"
    "            Invariant(ToSeq(result)\n"
    "                      == ToSeq(vs).take(keep)\n"
    "                      + ToSeq(vs).drop(idx).take(k - idx))\n"
    "            Invariant(MustTerminate(n - k + 1))\n"
    "            # invariants-end\n"
    "            old_seq = ToSeq(result)\n"
    "            result.append(vs[k])\n"
    "            Assert(ToSeq(result) == old_seq + PSeq(vs[k]))\n"
    "            Assert(ToSeq(vs).drop(idx)[k - idx] == ToSeq(vs)[k])\n"
    "            Assert(ToSeq(vs).drop(idx).take(k - idx) + PSeq(ToSeq(vs).drop(idx)[k - idx])\n"
    "                   == ToSeq(vs).drop(idx).take(k - idx + 1))\n"
    "            k = k + 1\n"
    "        Assert(ToSeq(vs).drop(idx).take(n - idx) == ToSeq(vs).drop(idx))\n"
    "        Assert(ToSeq(result)\n"
    "               == shortest_seq(value, neg).take(keep)\n"
    "               + shortest_seq(value, neg).drop(idx))\n"
)


# ===========================================================================
# (1) POSITIVE CONTROL (soundness) — structurally-different CORRECT impl.
#     Reshape: hoist the idx / result / old_seq declarations ABOVE the
#     n<=20 early return. Statement order across the branch changes, but the
#     computed values and every invariant/assert it relies on are unchanged,
#     so the gold proof still discharges. MUST verify (else SPEC-TOO-STRONG).
# ===========================================================================
_POS_DECL = (
    "    vs = shortest_field(value, neg)\n"
    "    n = len(vs)\n"
    "    idx = e_index(ToSeq(vs))\n"
    "    result = []  # type: List[int]\n"
    "    old_seq = ToSeq(result)  # type carrier for the per-append step (see below)\n"
    "    if n <= 20:\n"
    "        return vs\n"
    "    # Over the cap: trim to 20 characters, preserving any exponent suffix. The\n"
    "    # carrier `vs` IS the exact rendering (ToSeq(vs) == shortest_seq(value, neg)),\n"
    "    # so the trim is stated structurally against it via take/drop/concat.\n"
)
_pos_control = _swap(_BASE, _DECL_BLOCK, _POS_DECL)


# ===========================================================================
# (2) ADMISSIBILITY — there is NO precondition on the float input (the
#     pre-conditions region is comments only), so the function is total over
#     finite floats. The canonical admissibility witness is the gold impl
#     itself verifying (the spec admits the gold-shaped computation on an
#     F2P-shaped input). MUST verify (else PRECOND-TOO-STRONG). Near-trivial
#     here precisely because the precondition is empty — noted in assessment.
# ===========================================================================
_admiss = _BASE  # frozen impl; same_spec trivially, must verify


# ===========================================================================
# (3) UNIQUENESS — pre-patch renderer echo (the MINIMALITY discriminator).
#     Swap the carrier from shortest_field to padded_field (the f"{v:.16G}"
#     renderer the gold patch removes). padded_field's Ensures do NOT give
#     ToSeq == shortest_seq, so the fits-branch clause (2) and the invariant
#     ToSeq(vs)==shortest_seq(value) are unprovable. MUST reject.
#     Refinement: this IS the pre-patch behaviour -- 0.009125 renders
#     "0.009124999999999999" (16 sig digits), forcing the comment truncation
#     the F2P test_floating_point_string_representation_card forbids. Mirrors
#     model_prepatch.py exactly. (= SPEC-TOO-WEAK if it verified.)
# ===========================================================================
_weak_padded = _swap(_BASE,
                     "    vs = shortest_field(value, neg)\n",
                     "    vs = padded_field(value, neg)\n")


# ===========================================================================
# (4) UNIQUENESS — unbounded echo (the cap clause).
#     Return the full exact rendering without ever trimming. For inputs whose
#     rendering exceeds 20 chars this violates clause (1) 1<=len<=20.
#     MUST reject. Refinement: a real patch returning the untrimmed value_str
#     emits a >20-char field -> the FITS card cannot hold it (the very 20-char
#     cap _format_float exists to enforce); test_floating_point_value_card /
#     test_complex_value_card (22-char scientific values) would not resolve.
#     Cheap supporting case; rejection is from the length bound, clause (1).
# ===========================================================================
_echo_impl = (
    "    vs = shortest_field(value, neg)\n"
    "    return vs\n"
)
# The branching part of the over-cap block WITHOUT the leading idx/result/old_seq
# declarations (those live in _DECL_BLOCK). The full impl body is
# _DECL_BLOCK + _BRANCHING + "    return result\n".
_BRANCHING = _OVERCAP_BLOCK[len(
    "    idx = e_index(ToSeq(vs))\n"
    "    result = []  # type: List[int]\n"
    "    old_seq = ToSeq(result)  # type carrier for the per-append step (see below)\n"
):]
# Replace the entire impl body (decl block through the final assert + return)
# with the unconditional echo.
_echo_full_old = _DECL_BLOCK + _BRANCHING + "    return result\n"
_weak_echo = _swap(_BASE, _echo_full_old, _echo_impl)


# ===========================================================================
# (5) UNIQUENESS / PARTIAL-DOMAIN — first-20 truncation drops the exponent
#     (the adversarial a4 attacker the G-EQ refinement was built to kill).
#     Replace the exponent-preserving trim with an UNCONDITIONAL first-20 copy
#     loop (ignore idx). Internally self-consistent: invariant ToSeq(result)==
#     ToSeq(vs).take(j), final Assert take(20). It satisfies clause (3) (no
#     exponent) but for scientific notation (idx>=0) clause (4) requires
#     take(20-(len-idx)) + drop(idx) != take(20). MUST reject.
#     Refinement: the real edit value_str = value_str[:20] drops the exponent
#     on -4.6737...E+32 (22 chars) -> "-4.673746367476376" with NO exponent,
#     which is a different float; test_floating_point_value_card /
#     test_complex_value_card (P2P, the idx>=0 path) would not resolve.
#     Diverges only on the scientific-notation sub-domain (partial-domain).
#     Termination: this variant collapses the gold's THREE loops into ONE
#     unconditional first-20 copy, so it carries one measure of its own,
#     MustTerminate(20 - j + 1) -- the same shape as the gold's idx<0 loop
#     (`while j < 20`, j up by one) and NOT the gold's `keep`/`n` measures,
#     which name variables this variant's loop does not count on.
# ===========================================================================
_TRUNC_BLOCK = (
    "    idx = e_index(ToSeq(vs))\n"
    "    result = []  # type: List[int]\n"
    "    old_seq = ToSeq(result)  # type carrier for the per-append step (see below)\n"
    "    j = 0\n"
    "    while j < 20:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))\n"
    "        Invariant(0 <= j and j <= 20 and n == len(vs) and n > 20)\n"
    "        Invariant(n == shortest_field_len(value, neg))\n"
    "        Invariant(ToSeq(vs) == shortest_seq(value, neg))\n"
    "        Invariant(idx == e_index(ToSeq(vs)))\n"
    "        Invariant(len(result) == j)\n"
    "        Invariant(ToSeq(result) == ToSeq(vs).take(j))\n"
    "        Invariant(MustTerminate(20 - j + 1))\n"
    "        # invariants-end\n"
    "        old_seq = ToSeq(result)\n"
    "        result.append(vs[j])\n"
    "        Assert(ToSeq(result) == old_seq + PSeq(vs[j]))\n"
    "        Assert(ToSeq(vs).take(j) + PSeq(ToSeq(vs)[j]) == ToSeq(vs).take(j + 1))\n"
    "        j = j + 1\n"
    "    Assert(ToSeq(result) == shortest_seq(value, neg).take(20))\n"
)
_weak_trunc = _swap(_BASE, _OVERCAP_BLOCK, _TRUNC_BLOCK)


# ===========================================================================
# (6) UNIQUENESS / PARTIAL-DOMAIN — over-keep one significand digit in the
#     exponent branch (off-by-one in the trim, value-content + length break).
#     Change keep = 20 - (n - idx) to keep = 21 - (n - idx). The first loop
#     copies one extra significand char, then the suffix is appended, giving
#     len 21 (> 20, clause (1)) AND content take(keep+1)+drop(idx) (clause (4)
#     wants take(20-(len-idx))+drop(idx)). To keep the impl internally
#     consistent the matching invariant `keep == 20 - (n - idx)` is updated to
#     the new value; the FROZEN postcondition is untouched. MUST reject.
#     Refinement: a real patch using value_str[:21-(str_len-idx)]+value_str[idx:]
#     emits a 21-char field with an extra mantissa digit -> the FITS value field
#     overflows / mis-renders the scientific P2P value; test_floating_point_value_card
#     would not resolve. Diverges only on the scientific over-cap sub-domain.
# ===========================================================================
_weak_offbyone = _swap(_BASE,
                       "        keep = 20 - (n - idx)\n",
                       "        keep = 21 - (n - idx)\n")
_weak_offbyone = _weak_offbyone.replace(
    "Invariant(keep == 20 - (n - idx) and keep >= 0 and keep <= idx)",
    "Invariant(keep == 21 - (n - idx) and keep >= 0 and keep <= idx)", 1)
_weak_offbyone = _weak_offbyone.replace(
    "Invariant(keep == 20 - (n - idx) and keep >= 0)",
    "Invariant(keep == 21 - (n - idx) and keep >= 0)", 1)


# ===========================================================================
# (7) UNIQUENESS / BOUNDARY — sign-dropping at a zero value. Render the
#     UNSIGNED number whenever the value is zero, i.e. ignore the sign flag
#     there and emit the positive zero's field for both zeros. Every clause the
#     OLD (value-only) spec could state is satisfied -- the field round-trips to
#     the same real, spends the same minimal significant digits and has the same
#     length -- so this is exactly the implementation the value-only model could
#     not tell from the gold one. It must be rejected by the sign clause of the
#     fits-branch content equality. MUST reject.
#     Refinement: a real patch that normalized a negative zero away would render
#     a negative zero as "0.0", losing the number's sign in the card image; the
#     renderer's own behaviour is to reproduce the number exactly, sign included.
# ===========================================================================
_weak_dropsign = _swap(_BASE,
                       "    vs = shortest_field(value, neg)\n",
                       "    vs = shortest_field(value, neg and value != 0.0)\n")


SPEC_TESTS = [
    {
        "id": "pos-control-hoist-decl",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_control,
        "rationale": ("structurally-different but correct: the idx/result/old_seq "
                      "declarations are hoisted above the n<=20 early return; computed "
                      "values and every invariant/assert are unchanged, so the gold "
                      "proof discharges. Must verify, else SPEC-TOO-STRONG."),
    },
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss,
        "rationale": ("the float input carries NO precondition (pre-conditions region "
                      "is comments only), so the renderer is total over finite floats; "
                      "the gold impl verifying is the admissibility witness. Must verify, "
                      "else PRECOND-TOO-STRONG."),
    },
    {
        "id": "weak-padded-renderer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _weak_padded,
        "refinement": ("padded_field models the pre-patch f\"{value:.16G}\" renderer: it "
                       "renders 0.009125 as \"0.009124999999999999\" (16 sig digits, not "
                       "the minimal 4), forcing the comment truncation the F2P test "
                       "test_floating_point_string_representation_card forbids -- the "
                       "pre-patch did NOT resolve (this is literally model_prepatch.py)."),
        "rationale": ("rejection from postcondition clause (2): padded_field's Ensures do "
                      "not give ToSeq(Result())==shortest_seq(value), so the fits-branch "
                      "content equality and the invariant ToSeq(vs)==shortest_seq(value) "
                      "are unprovable. If it verified => SPEC-TOO-WEAK (the minimality "
                      "discriminator would be missing)."),
    },
    {
        "id": "weak-echo-untrimmed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _weak_echo,
        "refinement": ("returning the untrimmed exact rendering emits a >20-char field "
                       "for scientific-notation values (e.g. -4.6737...E+32 is 22 chars); "
                       "the FITS value field cannot hold it -- the 20-char cap is the "
                       "whole reason _format_float trims -- so test_floating_point_value_card "
                       "/ test_complex_value_card (P2P) would not resolve."),
        "rationale": ("rejection from postcondition clause (1) 1<=len(Result())<=20: the "
                      "echo has length shortest_field_len(value), which can exceed 20. "
                      "Cheap supporting cap-clause case."),
    },
    {
        "id": "weak-trunc-first20-drops-exponent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _weak_trunc,
        "refinement": ("the real edit value_str = value_str[:20] truncates the scientific "
                       "value -4.6737...E+32 (22 chars) to \"-4.673746367476376\" -- the "
                       "E+32 exponent is dropped, yielding a different number; "
                       "test_floating_point_value_card / test_complex_value_card (P2P, the "
                       "idx>=0 over-cap path) would not resolve."),
        "rationale": ("rejection from postcondition clause (4): for over-cap inputs WITH "
                      "an exponent, the spec requires take(20-(len-idx))+drop(idx); the "
                      "unconditional first-20 loop produces take(20), which drops the "
                      "exponent suffix. Satisfies clause (3) (no exponent) -- a genuine "
                      "partial-domain break. If it verified => SPEC-TOO-WEAK (the a4 "
                      "attacker the G-EQ refinement was built to kill)."),
    },
    {
        "id": "weak-offbyone-keep-plus1",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _weak_offbyone,
        "refinement": ("a real patch using value_str[:21-(str_len-idx)]+value_str[idx:] "
                       "keeps one extra significand digit, emitting a 21-char field that "
                       "overflows the 20-char value field and mis-renders the scientific "
                       "P2P value; test_floating_point_value_card would not resolve."),
        "rationale": ("rejection from postcondition clauses (1) and (4): keep+1 makes the "
                      "result 21 chars (>20) and its content take(keep+1)+drop(idx) != "
                      "take(20-(len-idx))+drop(idx). The matching internal invariant is "
                      "updated to keep the variant self-consistent; the FROZEN spec is "
                      "untouched. Partial-domain (scientific over-cap)."),
    },
    {
        "id": "weak-dropsign-at-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _weak_dropsign,
        "refinement": ("dropping the sign when the value is zero renders a negative "
                       "zero as \"0.0\": the card image loses the number's sign. The "
                       "renderer's behaviour is to reproduce the number exactly, and a "
                       "negative zero is a negative number, so this is a real behavioural "
                       "divergence on an input the renderer is reached with."),
        "rationale": ("rejection from postcondition clause (2) via the sign clause on the "
                      "exact rendering: at a zero value with neg set, shortest_seq starts "
                      "with a minus, and this impl's carrier is the UNSIGNED rendering, so "
                      "the content equality is unprovable. It satisfies every clause a "
                      "value-only model could state (same round-trip, same minimal sig "
                      "digits, same length), which is why the sign had to become "
                      "observable. If it verified => SPEC-TOO-WEAK. Boundary/partial-domain "
                      "(the zero sub-domain only)."),
    },
]


# ===========================================================================
# AXIOM LANE — six @ContractOnly axioms. shortest_field / shortest_seq are
# A-reference deep models of str(value).replace('e','E'); parse_dec /
# sig_count / min_sig / shortest_field_len are the supporting numeric theory.
# The probes execute the REAL stdlib callees (the very primitives the gold
# patch swaps to) and assert each axiom's Ensures on the finite-float domain
# the renderer actually reaches, plus a caller-domain containment check.
#
# These probes re-implement the axiom_check.py callees as self-contained
# stdlib python (no bundle file is mounted in-container; per PBT_PLAN §5a.6).
# Eval images run old Python with an ASCII locale: only stdlib + ASCII here.
# ===========================================================================

# Shared callee/checker source embedded verbatim into every probe (mirrors
# axiom_check.py; running the REAL callee, never scraping source).
_CALLEES = r'''
import math, random, sys

def _as_double(value, neg):
    return math.copysign(value, -1.0 if neg else 1.0)

def canon(d):
    # the pair a finite double refines to: (magnitude representative, sign).
    # d + 0.0 is bit-identical to d for finite nonzero d and maps -0.0 -> +0.0,
    # so the pair is a COMPLETE invariant of d.
    return (d + 0.0, math.copysign(1.0, d) < 0.0)

def shortest_field(value, neg):
    return str(_as_double(value, neg)).replace("e", "E")

def padded_field(value, neg=False):
    value_str = f"{_as_double(value, neg):.16G}"
    if "." not in value_str and "E" not in value_str:
        value_str += ".0"
    elif "E" in value_str:
        significand, exponent = value_str.split("E")
        if exponent[0] in ("+", "-"):
            sign = exponent[0]; exponent = exponent[1:]
        else:
            sign = ""
        value_str = f"{significand}E{sign}{int(exponent):02d}"
    return value_str

def parse_dec(field):
    return float(field.replace("E", "e"))

def sig_count(field):
    s = field.replace("E", "e")
    if "e" in s:
        s = s.split("e", 1)[0]
    if s and s[0] in "+-":
        s = s[1:]
    if "." in s:
        intp, frac = s.split(".", 1)
    else:
        intp, frac = s, ""
    digits = intp + frac
    stripped = digits.lstrip("0")
    if stripped == "":
        return 1
    stripped = stripped.rstrip("0")
    if stripped == "":
        return 1
    return len(stripped)

def min_sig(value):
    # fewest significant digits that round-trip == sig_count of Python's shortest
    # repr (str). NOT min{k: float(f"{value:.{k}g}")==value}: %g rounds to nearest
    # and can miss a k-digit round-tripping rendering (e.g. 2**-24 -> %.16g gives
    # ...062 which fails, repr gives ...063 which round-trips at 16, truly minimal).
    if value == 0:
        return 1
    return sig_count(shortest_field(value, False))

def shortest_field_len(value, neg):
    return len(shortest_field(value, neg))

def e_index(field):
    return field.find("E")

def _finite_corpus():
    rng = random.Random(14508)
    vals = [
        0.009125, 8.95, -99.9, 1.0, -1.0, 0.0, -0.0, 100.0, 0.1, 0.5,
        -467374636747637647347374734737437.0,
        1.2345377437887837487e88, 6324767364763746367e-33,
        1e-10, 1e10, 1e100, 1e-100, 1e308, 5e-324,
        2.2250738585072014e-308,
        (1 - 2 ** -53) * 2 ** -60, (1 - 2 ** -53) * 2 ** 0,
        (1 - 2 ** -53) * 2 ** 60, 1.0/3.0, 2.0/3.0, math.pi, math.e,
    ]
    for i in range(-2000, 2001):
        vals.append(float(i))
    for _ in range(60000):
        mant = rng.uniform(-10.0, 10.0); exp = rng.randint(-308, 308)
        v = mant * (10.0 ** exp)
        if math.isfinite(v):
            vals.append(v)
    for _ in range(8000):
        v = rng.uniform(-1e-300, 1e-300)
        if math.isfinite(v):
            vals.append(v)
    return vals
'''

_AX_SHORTEST = _CALLEES + r'''
# axiom-soundness for shortest_field / shortest_seq (same callee+properties):
# round-trip, minimal significant digits, len agreement, exponent suffix <= 5.
bad = 0
for d in _finite_corpus():
    value, neg = canon(d)
    f = shortest_field(value, neg)
    # the pair reconstructs the double, and the axiom's field IS the real callee's
    if repr(_as_double(value, neg)) != repr(d):
        print("PAIR-NOT-COMPLETE", repr(d)); bad += 1
    if f != str(d).replace("e", "E"):
        print("NOT-REAL-CALLEE", repr(d), repr(f)); bad += 1
    if len(f) < 1:
        print("EMPTY", repr(d)); bad += 1; continue
    if parse_dec(f) != value:
        print("NO-ROUNDTRIP", repr(d), repr(f), repr(parse_dec(f))); bad += 1
    if sig_count(f) != min_sig(value):
        print("NOT-MINIMAL", repr(d), repr(f), sig_count(f), min_sig(value)); bad += 1
    if len(f) != shortest_field_len(value, neg):
        print("LEN-MISMATCH", repr(d), repr(f)); bad += 1
    if f.startswith("-") != neg:
        print("SIGN-CLAUSE", repr(d), repr(f), neg); bad += 1
    if neg and len(f) < 2:
        print("SIGNED-TOO-SHORT", repr(d), repr(f)); bad += 1
    idx = f.find("E")
    if idx >= 0 and len(f) - idx > 5:
        print("SUFFIX>5", repr(d), repr(f)); bad += 1
# the headline regression, spelled out
assert shortest_field(*canon(0.009125)) == "0.009125", shortest_field(*canon(0.009125))
# both zeros are distinct numbers with distinct renderings
assert shortest_field(*canon(0.0)) == "0.0"
assert shortest_field(*canon(-0.0)) == "-0.0"
if bad:
    print("VIOLATIONS:", bad); sys.exit(1)
print("AX-SOUND shortest_field/shortest_seq OK over finite-float corpus "
      "(pair-valued: == real callee, sign clause, both zeros)")
sys.exit(0)
'''

_AX_NUMERIC = _CALLEES + r'''
# axiom-soundness for the supporting numeric theory:
#   min_sig(value) >= 1               (Ensures Result() >= 1)
#   sig_count(field) >= 0             (Ensures Result() >= 0)
#   shortest_field_len(value) >= 1    (Ensures Result() >= 1)
#   parse_dec round-trips the exact rendering (its defining use)
bad = 0
for d in _finite_corpus():
    value, neg = canon(d)
    if min_sig(value) < 1:
        print("min_sig<1", repr(d), min_sig(value)); bad += 1
    if shortest_field_len(value, neg) < 1:
        print("sfl<1", repr(d)); bad += 1
    f = shortest_field(value, neg)
    if sig_count(f) < 0:
        print("sig_count<0", repr(d), repr(f)); bad += 1
    if parse_dec(f) != value:
        print("parse_dec break", repr(d), repr(f)); bad += 1
if bad:
    print("VIOLATIONS:", bad); sys.exit(1)
print("AX-SOUND parse_dec/sig_count/min_sig/shortest_field_len OK")
sys.exit(0)
'''

_AX_PADDED = _CALLEES + r'''
# axiom-soundness for padded_field (pre-patch renderer, WEAK axiom): non-empty,
# exponent suffix <= 5, AND the discriminator -- it spends MORE significant
# digits than min_sig on the regression values (so the pre-patch skeleton
# genuinely fails the minimality clause; NOT an artefact).
bad = 0
for d in _finite_corpus():
    f = padded_field(*canon(d))
    if len(f) < 1:
        print("EMPTY", repr(d)); bad += 1
    idx = f.find("E")
    if idx >= 0 and len(f) - idx > 5:
        print("SUFFIX>5", repr(d), repr(f)); bad += 1
disc = [0.009125, 8.95, -99.9, 0.1, 0.2, 0.3, 8.7]
excess = sum(1 for v in disc
             if sig_count(padded_field(*canon(v))) > min_sig(v)
             and sig_count(shortest_field(*canon(v))) == min_sig(v))
if excess < 3:
    print("DISCRIMINATOR-ABSENT", excess); bad += 1
if bad:
    print("VIOLATIONS:", bad); sys.exit(1)
print("AX-SOUND padded_field well-formed + spends EXCESS digits (discriminator real)")
sys.exit(0)
'''

_AX_CONTAINMENT = _CALLEES + r'''
# axiom-containment: every callee-input the MODEL can reach lies inside the
# axiom's Requires domain. The model only ever passes:
#   * the interpreted finite float `value` to shortest_field/shortest_seq/
#     min_sig/shortest_field_len (Requires: none beyond finite; inf/nan are
#     rejected upstream by io.fits before the renderer, mapping.md sec 4);
#   * the rendered field ToSeq(vs) to e_index/sig_count/parse_dec, whose
#     Requires is only len(field) >= 0 -- always true for a materialized field.
# So the reachable-input set is {finite floats} and {their renderings}. Assert
# every such field has len >= 0 (parse_dec/sig_count Requires) and the renderer
# accepts every finite float (no exception in domain). A finite float reaching
# an input OUTSIDE these domains would be AXIOM-TOO-WEAK-FOR-CALLER.
bad = 0
for d in _finite_corpus():
    value, neg = canon(d)
    f = shortest_field(value, neg)   # the only callee-produced field
    if len(f) < 0:                   # parse_dec/sig_count Requires len>=0
        print("FIELD-LEN<0", repr(d)); bad += 1
    try:
        parse_dec(f); sig_count(f); e_index(f)
    except Exception as ex:
        print("CALLEE-REJECTS-REACHABLE-FIELD", repr(d), repr(f), repr(ex)); bad += 1
    try:
        min_sig(value); shortest_field_len(value, neg)
    except Exception as ex:
        print("RENDERER-REJECTS-REACHABLE-FLOAT", repr(d), repr(ex)); bad += 1
    # the caller only ever passes pairs that satisfy the linkage preconditions
    if (value > 0.0 and neg) or (value < 0.0 and not neg):
        print("PAIR-OUTSIDE-PRECONDITION", repr(d), value, neg); bad += 1
if bad:
    print("CONTAINMENT VIOLATIONS:", bad); sys.exit(1)
print("AX-CONTAINMENT OK: every caller-reachable callee input is in-domain")
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-shortest-field-seq",
        "axiom": "shortest_field",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SHORTEST,
        "rationale": ("the real str(value).replace('e','E') must round-trip (parse_dec==value), "
                      "spend the MINIMAL significant digits (sig_count==min_sig), agree in length, "
                      "and keep any exponent suffix <= 5 -- on the finite-float domain the renderer "
                      "reaches. Any violation => AXIOM-UNSOUND. Covers shortest_seq (same callee+props)."),
    },
    {
        "id": "ax-sound-numeric-theory",
        "axiom": "min_sig",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_NUMERIC,
        "rationale": ("min_sig>=1, shortest_field_len>=1, sig_count>=0 (each axiom's Ensures) and "
                      "parse_dec inverts the exact rendering, over the finite-float corpus. Any "
                      "violation => AXIOM-UNSOUND."),
    },
    {
        "id": "ax-sound-padded-discriminator",
        "axiom": "padded_field",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_PADDED,
        "rationale": ("padded_field is non-empty with suffix<=5 AND spends EXCESS significant digits "
                      "(> min_sig) on the regression values -- so the weak pre-patch axiom is a real "
                      "discriminator, not an artefact. Any violation => AXIOM-UNSOUND."),
    },
    {
        "id": "ax-containment-caller-domain",
        "axiom": "shortest_field",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT,
        "rationale": ("every callee-input the model can reach (finite floats to the renderers; their "
                      "materialized fields, len>=0, to parse_dec/sig_count/e_index) lies inside each "
                      "axiom's Requires domain. A reachable input outside => AXIOM-TOO-WEAK-FOR-CALLER."),
    },
]
