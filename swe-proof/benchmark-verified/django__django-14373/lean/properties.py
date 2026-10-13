# properties.py — G-PBT falsification battery for django__django-14373 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive reproves, the proof body — is edited), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   renderYear : Nat → String, the fixed-width decimal rendering of a whole number.
#   The single postcondition clause `result = padZeros 4 (toString year)` pins the
#   whole output: the base-ten numeral of `year`, left-padded with the `'0'`
#   character to a minimum width of four. padZeros / toString are total, transparent
#   operations over a fully computable carrier (Nat → String), so `decide` computes
#   the spec at any literal input — witnesses need NO conditioning on the carrier.
#
# Although the postcondition is a single string equality, it pins several INDEPENDENT
# sub-behaviours over the one input binder `year` that a rival can attack one at a
# time. Naming them for the coverage argument:
#   (P-width) the result is a CONSTANT four characters wide for any year whose numeral
#             is shorter than four digits — the leading positions are FILLED, never
#             dropped. This is the load-bearing behaviour the F2P demands (a sub-1000
#             year must render as four characters, not its bare significant digits).
#   (P-fill)  the FILL character is the digit `'0'`, not a space or any other glyph.
#   (P-order) the significant digits appear in their true base-ten order (no
#             transposition / reversal).
#   (P-value) the digits are those of `year` itself (no off-by-one on any digit).
#   (P-nooverflow) a year whose numeral already reaches width four is emitted in full
#             with NO extra padding and no spurious trailing character (exactly four
#             chars for a four-digit year).
#
# CARRIER NOTE: the nagini sibling modeled the same rendering as a List[int] of ASCII
# code points with SIX numbered post-facts (len==4, each 48..57, place-weighted
# reconstruction, leading == 48+year//1000, etc.). This backend models the observable
# the fix actually governs — the appended STRING — directly as `padZeros 4 (toString
# year)`. So nagini's per-code-point clauses collapse onto sub-behaviours of one
# string equality: nagini's (P2) len==4 / (P5) leading-digit become (P-width) here;
# (P3) each-char-a-digit becomes (P-fill); (P1)/(P4) order+reconstruction become
# (P-order)/(P-value). Each nagini rival ports onto the clause it attacked.
#
# LANES THAT DO NOT PORT:
#   * FRAME / PERMISSION-MUTATION. Nagini's frame-mutation class (a rival writing back
#     into an Acc(x,1/2) read-only heap input to satisfy the postcondition vacuously)
#     is nagini-specific: it needs fractional permissions and aliasable heap. Lean is
#     referentially transparent — the sole input `year : Nat` is an immutable value and
#     there is no caller-owned heap to overwrite — so the whole class is VACUOUS here.
#     The nagini sibling already recorded this as N/A (its `year` is a plain int); we
#     concur. See 'assessment'.
#   * AXIOM_TESTS. No @ContractOnly axioms and no opaque callees: the rendering is
#     modeled DEEPLY (toString + padZeros over concrete Nat/String ops), so there is no
#     consumed axiom, mapping.md records axiom_check.py as a skip stub, and the axiom
#     lane belongs to G-AX regardless.
#
# ADMISSIBILITY ON A TOTAL CARRIER (nagini's `admiss-self-call` defended the
# precondition 1 <= year <= 9999 by self-calling on F2P-shaped sub-1000 years).
# The lean obligation carries NO precondition hypothesis — `year : Nat` is a
# superset of the datetime range (mapping.md) — but "there is no Requires" is NOT
# a reason to drop the lane, because the analogue of PRECOND-TOO-STRONG on a total
# carrier is the obligation being UNSATISFIABLE at exactly an F2P-shaped input. A
# spec that pinned an unreachable value at the low sub-domain would still discharge
# `∀ year, …` vacuously nowhere — it would simply be unprovable at that point,
# and no uniqueness rival exhibits that: a rival's failure says the RIVAL is wrong,
# never that the spec is unsatisfiable. `admiss-f2p-point` closes that direction
# directly: it discharges the postcondition BY EVALUATION at the two concrete
# F2P-shaped years, as `have` steps, before closing the frozen obligation verbatim.
# See the case's rationale for the negative control that shows the steps are
# load-bearing rather than no-ops.
from pathlib import Path

INSTANCE = "django__django-14373"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------------
# The full impl body, lying ENTIRELY inside impl-start/impl-end and unique in the file.
# Every rival and reshaped positive swaps THIS block; the frozen spec (padZeros,
# problem_spec_renderYear) and the theorem STATEMENT are never touched.
_IMPL = (
    "def implementation_renderYear (year : Nat) : String := Id.run do\n"
    "  return padZeros 4 (toString year)"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted"

# The frozen proof body (the tactic lines inside proof-start/proof-end). Left in place
# by the reshaped positive (still closes) and by every rival (reads the witness, not the
# rival build); byte-identical across all cases so the theorem STATEMENT is preserved.
_PROOF = (
    "  intro year\n"
    "  unfold problem_spec_renderYear implementation_renderYear\n"
    "  rfl"
)
assert _BASE.count(_PROOF) == 1, "proof body anchor drifted"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-reshape-let: structurally-DIFFERENT but behaviourally identical impl. The
# numeral is bound to a local `let s` inside the `do` block before padding; the return
# expression is otherwise unchanged, so the output equals the frozen impl's on every
# input. The frozen `theorem correct_renderYear` STATEMENT is byte-identical AND the
# frozen proof body still closes (the let binding is definitionally transparent), so
# this is a faithful restructure with no reproof and no new axiom/lemma/sorry. If it
# FAILS => SPEC-TOO-STRONG (postcondition over-fit to one syntactic impl shape).
_POS_LET = _swap(
    _BASE,
    _IMPL,
    "def implementation_renderYear (year : Nat) : String := Id.run do\n"
    "  let s := toString year\n"
    "  return padZeros 4 s",
)

# pos-direct-grounded: the cheapest HONEST impl. The postcondition is literally
# `result = padZeros 4 (toString year)` and padZeros/toString are GROUNDED in the
# argument (total transparent functions), so directly returning that expression — with
# no `Id.run do` wrapper — is a fully-grounded correct implementation, not an
# ungrounded-oracle echo (a wrong constant fails the postcondition; see the reject
# cases). The frozen proof body still closes: after `unfold` the impl is definitionally
# the RHS, so `rfl` discharges it. The theorem STATEMENT is byte-identical. MUST verify;
# else SPEC-TOO-STRONG.
_POS_DIRECT = _swap(
    _BASE,
    _IMPL,
    "def implementation_renderYear (year : Nat) : String :=\n"
    "  padZeros 4 (toString year)",
)


# ===========================================================================
# ADMISSIBILITY (the PRECOND-TOO-STRONG direction, in its total-carrier form).
# The IMPL is the frozen one byte-for-byte; only the PROOF BODY is extended, which
# variant_scope permits (the theorem STATEMENT is what must be preserved, and it is).
# Ahead of closing the frozen obligation verbatim (`unfold …; rfl`), the proof
# discharges the postcondition BY EVALUATION at the two concrete F2P-shaped years,
# and separately pins the evaluated text each one renders to. So the case fails if
# the obligation is unsatisfiable at either F2P point, or if the rendered value
# there is anything other than the four-character padded form.
# ===========================================================================

_ADM_F2P = _swap(
    _BASE,
    _PROOF,
    "  intro year\n"
    "  -- the obligation is SATISFIABLE at the F2P-shaped low sub-domain: discharge\n"
    "  -- it by evaluation at both concrete points before closing the general goal.\n"
    "  have f2p_low : problem_spec_renderYear 1 (implementation_renderYear 1) := by\n"
    "    unfold problem_spec_renderYear implementation_renderYear\n"
    "    decide\n"
    "  have f2p_low_val : implementation_renderYear 1 = \"0001\" := by\n"
    "    unfold implementation_renderYear\n"
    "    decide\n"
    "  have f2p_high : problem_spec_renderYear 999 (implementation_renderYear 999) := by\n"
    "    unfold problem_spec_renderYear implementation_renderYear\n"
    "    decide\n"
    "  have f2p_high_val : implementation_renderYear 999 = \"0999\" := by\n"
    "    unfold implementation_renderYear\n"
    "    decide\n"
    "  unfold problem_spec_renderYear implementation_renderYear\n"
    "  rfl",
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; the frozen proof body is left in
# place (it will not close for the reshaped impl, but the gate reads the WITNESS —
# checked in a file with the obligation removed — not the rival's own build).
# ===========================================================================

# weak-no-pad: return the bare numeral with NO leading-zero padding. This is exactly
# the PRE-PATCH shape (the method returned the raw year rendered without padding).
# Correct for any year whose numeral is already >= 4 chars; WRONG for a sub-1000 year,
# which renders with fewer than four characters.
_RIV_NOPAD = _swap(
    _BASE,
    _IMPL,
    "def implementation_renderYear (year : Nat) : String := Id.run do\n"
    "  return toString year",
)

# weak-space-pad: pad to a constant four-width field but FILL with the space character
# instead of the zero digit. len is 4 but the fill glyph is wrong.
_RIV_SPACEPAD = _swap(
    _BASE,
    _IMPL,
    "def implementation_renderYear (year : Nat) : String := Id.run do\n"
    "  let s := toString year\n"
    "  return String.mk (List.replicate (4 - s.length) ' ') ++ s",
)

# weak-reverse-digits: pad to width four but with the significant digits REVERSED (the
# numeral's characters are reversed before padding). Same width, same fill, same digit
# multiset — only the ORDER is wrong.
_RIV_REVERSE = _swap(
    _BASE,
    _IMPL,
    "def implementation_renderYear (year : Nat) : String := Id.run do\n"
    "  return padZeros 4 (String.mk (toString year).data.reverse)",
)

# weak-units-plus-one-on-tens: render correctly except add 1 to the year when it is a
# multiple of ten (so the last significant digit is corrupted from '0' to '1').
# Correct on every year NOT ending in zero; WRONG on multiples of ten. A supporting
# near-miss attacking the digit VALUE rather than the width/fill/order.
_RIV_PLUSONE = _swap(
    _BASE,
    _IMPL,
    "def implementation_renderYear (year : Nat) : String := Id.run do\n"
    "  if year % 10 == 0 then\n"
    "    return padZeros 4 (toString (year + 1))\n"
    "  else\n"
    "    return padZeros 4 (toString year)",
)

# weak-overflow-high: pad correctly but append a spurious trailing '0' for years whose
# numeral is already at least four digits, yielding FIVE characters for a four-digit
# year while sub-1000 years still get four. The inverse of weak-no-pad: correct width
# only on the low sub-domain.
_RIV_OVERFLOW = _swap(
    _BASE,
    _IMPL,
    "def implementation_renderYear (year : Nat) : String := Id.run do\n"
    "  if year ≥ 1000 then\n"
    "    return padZeros 4 (toString year) ++ \"0\"\n"
    "  else\n"
    "    return padZeros 4 (toString year)",
)


def _wit(year, note):
    """A refutation witness: `¬ problem_spec_renderYear year (implementation_renderYear
    year)` at a concrete literal `year`, closed by `decide`. padZeros/toString are
    total transparent functions, so `decide` computes both sides. Elaborates against a
    rival that diverges from the spec at that year, and fails on gold (which satisfies
    the spec at every year). No head binder => no consistency probe needed."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_renderYear {year} "
        f"(implementation_renderYear {year}) := by\n"
        f"  unfold problem_spec_renderYear implementation_renderYear\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-reshape-let",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LET,
        "rationale": (
            "structurally-different but CORRECT impl: the numeral is bound to a local "
            "`let s` inside the do-block before padding, keeping the return expression, "
            "so the output equals the frozen impl's on every year. The frozen `theorem "
            "correct_renderYear` STATEMENT is byte-identical and the frozen proof body "
            "still closes (the let binding is definitionally transparent) — a faithful "
            "restructure with no reproof and no new axiom/lemma/sorry. If it FAILS => "
            "SPEC-TOO-STRONG (postcondition over-fit to one syntactic impl shape)."
        ),
    },
    {
        "id": "pos-direct-grounded",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": (
            "the postcondition is literally result = padZeros 4 (toString year), and "
            "padZeros/toString are GROUNDED in the argument (total transparent "
            "functions), so returning that expression directly (no Id.run wrapper) is "
            "the honest cheapest CORRECT impl, not an ungrounded echo; after `unfold` "
            "the impl is definitionally the RHS so the frozen `rfl` proof body still "
            "closes the byte-identical theorem STATEMENT. Must verify; else "
            "SPEC-TOO-STRONG. Also shows the spec is not echo-vulnerable — any WRONG "
            "constant/reshape fails the postcondition (see the reject cases)."
        ),
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "admiss-f2p-point",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADM_F2P,
        "rationale": (
            "the PRECOND-TOO-STRONG direction in the form it takes on a TOTAL carrier. "
            "The frozen obligation quantifies over all of Nat with no precondition "
            "hypothesis, so there is no Requires to be too strong; the analogue is the "
            "obligation being UNSATISFIABLE at exactly an F2P-shaped input, which no "
            "uniqueness rival can exhibit (a rival's failure says the RIVAL is wrong, "
            "never that the spec is unsatisfiable at a point). This case tests that "
            "directly: the impl region is the frozen one byte-for-byte and only the "
            "PROOF BODY is extended, discharging problem_spec_renderYear BY EVALUATION "
            "at year=1 and year=999 — the two concrete F2P-shaped low-sub-domain points "
            "— as `have` steps, and pinning the evaluated text at each ('0001', '0999'), "
            "before closing the frozen obligation verbatim with the unchanged "
            "`unfold …; rfl`. The theorem STATEMENT is byte-identical and no new "
            "axiom/lemma/sorry appears. The `have` steps are LOAD-BEARING, not no-ops: "
            "the same proof shape with the expected text changed to the unpadded '1' "
            "(resp. '999') FAILS to build (`decide` refutes it), so this case would "
            "break if the spec pinned an unreachable value at the low sub-domain. If it "
            "FAILS => PRECOND-TOO-STRONG (the spec is unsatisfiable where the real "
            "behaviour demands a four-character rendering)."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-no-pad",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NOPAD,
        "refinement": (
            "returning the bare numeral with no leading-zero padding is the PRE-PATCH "
            "shape: a value below 1000 renders as its bare significant digits (1 -> a "
            "single-character string, 999 -> three characters) instead of four. The F2P "
            "test asserts the sub-1000 year renders as a four-character zero-padded "
            "string ('0001', '0999'), so a faithful patch of this shape FAILS the F2P "
            "and does NOT resolve — a verifying rival would be a true "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by result = padZeros 4 (toString year). Attacks (P-width): a "
            "sub-1000 year must render at a CONSTANT width of four with the leading "
            "positions filled. Witness at year=1 (numeral '1') — the F2P boundary — "
            "where gold = '0001' and the rival = '1'. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # year=1: gold '0001'; rival '1' (one char).
        "witness": _wit(1, "sub-1000 year: gold pads to four chars, rival drops leading zeros"),
    },
    {
        "id": "weak-space-pad",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SPACEPAD,
        "refinement": (
            "padding to width four but filling with the SPACE character instead of the "
            "zero digit is the space-pad mistake (a `'%4d'`-style field) instead of "
            "zero-pad (`'%04d'`): a sub-1000 year renders with leading spaces, not "
            "leading zero characters. The F2P asserts literal zero characters "
            "('0001'/'0999'), so a faithful patch of this shape FAILS the F2P and does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECTED by result = padZeros 4 (toString year). Attacks (P-fill): the "
            "fill glyph must be the digit '0', not a space. Witness at year=7 (numeral "
            "'7', a DIFFERENT year from the other witnesses) where gold = '0007' and the "
            "rival = '   7'. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # year=7: gold '0007'; rival '   7' (space-filled).
        "witness": _wit(7, "sub-1000 year: gold fills with '0', rival fills with space"),
    },
    {
        "id": "weak-reverse-digits",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REVERSE,
        "refinement": (
            "reversing the numeral's characters before padding produces a four-char "
            "field with every position a digit and the SAME digit multiset, but the "
            "significant digits are in the wrong ORDER (e.g. a four-digit year comes out "
            "with its digits reversed). The real rendering never reorders digits; the "
            "PASS_TO_PASS dateformat tests assert the exact rendered year, so a faithful "
            "patch of this shape FAILS those P2P tests and does NOT resolve."
        ),
        "rationale": (
            "REJECTED by result = padZeros 4 (toString year). Attacks (P-order): the "
            "significant digits must appear in true base-ten order. Witness at year=1234 "
            "(a >=1000 year, so no padding masks the reorder) where gold = '1234' and "
            "the rival = '4321'. If it VERIFIES => SPEC-TOO-WEAK. Distinct from the "
            "width/fill rivals — this one keeps width AND fill correct and abuses only "
            "order, so it needs its own >=1000 witness."
        ),
        # year=1234: gold '1234'; rival '4321' (digits reversed).
        "witness": _wit(1234, "four-digit year: gold keeps digit order, rival reverses it"),
    },
    {
        "id": "weak-units-plus-one-on-tens",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PLUSONE,
        "refinement": (
            "adding one to the year on multiples of ten corrupts the trailing digit for "
            "every year ending in zero (a year like 10 renders as if it were 11, 2020 as "
            "2021). The real rendering never alters the value; the dateformat P2P tests "
            "assert the exact rendered year, so a faithful patch of this shape FAILS "
            "those P2P tests on any year ending in zero and does NOT resolve."
        ),
        "rationale": (
            "REJECTED by result = padZeros 4 (toString year). Attacks (P-value): the "
            "digits must be those of `year` itself, no off-by-one. Witness at year=10 "
            "(a multiple of ten distinct from the other witness points) where gold = "
            "'0010' and the rival = '0011'. If it VERIFIES => SPEC-TOO-WEAK. This is the "
            "near-miss: correct on every year NOT ending in zero, so it needs a "
            "multiple-of-ten witness to discriminate."
        ),
        # year=10: gold '0010'; rival '0011' (value corrupted).
        "witness": _wit(10, "multiple of ten: gold renders the true value, rival adds one"),
    },
    {
        "id": "weak-overflow-high",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_OVERFLOW,
        "refinement": (
            "appending a spurious trailing zero for years already at least four digits "
            "yields five characters for a four-digit year (a year like 1000 renders as "
            "five chars). The real rendering emits a four-digit year in full with no "
            "extra padding; the dateformat P2P tests assert the exact four-character "
            "year, so a faithful patch of this shape FAILS those P2P tests on any "
            "four-digit year and does NOT resolve."
        ),
        "rationale": (
            "REJECTED by result = padZeros 4 (toString year). Attacks (P-nooverflow): a "
            "year whose numeral already reaches width four is emitted in full with no "
            "extra character. Witness at year=1000 (a >=1000 year distinct from 1234) "
            "where gold = '1000' and the rival = '10000'. If it VERIFIES => "
            "SPEC-TOO-WEAK. This is the inverse of weak-no-pad — correct width only on "
            "the low sub-domain — so it needs a >=1000 witness."
        ),
        # year=1000: gold '1000'; rival '10000' (spurious trailing zero).
        "witness": _wit(1000, "four-digit year: gold emits four chars, rival overflows to five"),
    },
]


# No @ContractOnly axioms and no opaque callees: the fixed-width decimal rendering
# (base-ten conversion + leading-zero padding) is modeled DEEPLY (toString + padZeros
# over the transparent Nat/String carrier), so there is no consumed axiom to probe and
# the axiom lane is vacuous here — it belongs to G-AX regardless.
AXIOM_TESTS = []
