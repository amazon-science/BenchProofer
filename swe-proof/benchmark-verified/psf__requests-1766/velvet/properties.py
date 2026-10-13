"""properties.py — G-PBT falsification battery for psf__requests-1766 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct`` obligation survives) and swaps in a candidate
implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE. One contracted method assembling a protection-directive
segment onto an already-built prefix:

  appendQopDirective (base ncvalue cnonce : List Char) return (out : List Char)
    ensures out = base ++ qopSegment ncvalue cnonce
    ensures (out.drop base.length).take directiveHead.length = directiveHead
    ensures (directiveHead.take (6 + quotedValueToken.length)).drop 6
              = quotedValueToken

All three inputs are FREE, read-only ``List Char`` values (none is a ``mut``
binder) and there is no ``require`` clause, so the admitted domain is total: the
post-image must hold for EVERY triple of prefix / count value / client-nonce
value.

The obligation bundles a FULL output equality with two structural pins:
  (a) the whole result is exactly ``base ++ qopSegment ncvalue cnonce`` — the
      segment is the literal head (which carries the QUOTED value token), then
      the count value emitted BARE, the literal mid, the client-nonce value,
      and a closing quote;
  (b) the run of ``directiveHead.length`` characters after the prefix equals
      ``directiveHead`` verbatim; and
  (c) the six-character window of ``directiveHead`` after its ``, qop=`` lead is
      exactly ``quotedValueToken`` = the DOUBLE-quoted token — the load-bearing
      clause the change corrects (a bare token would leave that window short a
      quote at each end).
Every piece of the segment is a fully-unfolded constant character literal or one
of the method's own two interpolated arguments; there is NO opaque callee.

ADVERSARIAL READ of the nagini classes:
  * FRAME-MUTATION — VACUOUS on this backend. The class exists on nagini because
    an input carries a fractional heap permission an impl can overwrite (all
    three inputs there are ``Acc(...,1/2)`` read-only). Lean and Velvet are
    referentially transparent: every parameter is an immutable value, there is
    no heap and no aliasing, and no input is a ``mut`` binder — there is no
    read-only input to mutate and no substitute probe to build. Reported as
    vacuous, not fabricated (see footer).
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is a total, fully unfolded
    function of the method's own arguments and constant literals; there is no
    opaque answer key to echo. Instead we carry an honest cheapest-reshape
    POSITIVE CONTROL (``pos-*``).
  * PARTIAL-DOMAIN / VALUE — APPLIES: near-miss impls right on part of the
    domain but diverging on a sub-domain (the value token unquoted, single-
    quoted, or missing its closing quote; the two interpolated values swapped).
    Each is refuted at a concrete point, and the points vary all three input
    binders so none is pinned across the battery.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the segment is
assembled deeply from constant literals and the two interpolated inputs, so no
callee is owed a contract). The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "psf__requests-1766"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Impl-region anchors. Each `old` below occurs EXACTLY ONCE in Solution.lean
# and lies strictly inside `-- impl-start` / `-- impl-end`, so every variant is
# same_spec by construction. Uniqueness is asserted at load by _swap.
# ---------------------------------------------------------------------------

# The whole gold impl body (used by variants that restructure the construction).
_GOLD_IMPL = """    let mut result : List Char := base
    -- ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
    result := result ++ [',', ' ', 'q', 'o', 'p', '=']
    result := result ++ ['"', 'a', 'u', 't', 'h', '"']
    result := result ++ [',', ' ', 'n', 'c', '=']
    -- the count value, bare (no surrounding quotes)
    result := result ++ ncvalue
    -- ', cnonce="'
    result := result ++ [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '"']
    -- the client-nonce value
    result := result ++ cnonce
    -- closing double quote
    result := result ++ ['"']
    return result"""

# The single line carrying the QUOTED value token `"auth"`.
_QUOTED_TOKEN_LINE = "    result := result ++ ['\"', 'a', 'u', 't', 'h', '\"']"

# The `mut result := base` head line; a stable insertion point for an in-region
# admissibility assert (occurs once, inside the impl region).
_RESULT_HEAD = "    let mut result : List Char := base"

# The count-value → client-nonce-value stretch (for the value-swap rival). The
# whole stretch is anchored so the two `++` lines are distinguishable.
_VALUE_STRETCH = """    result := result ++ ncvalue
    -- ', cnonce="'
    result := result ++ [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '"']
    -- the client-nonce value
    result := result ++ cnonce"""


# ---- witness preamble. The spec here is a `method` CONTRACT, not a bare
# ---- predicate, so a witness reaches it through Velvet's own tester
# ---- machinery: `appendQopDirectiveTester base ncvalue cnonce = false` says
# ---- the extracted program's result violates the method's postcondition at
# ---- that concrete input. Checked in a file whose `prove_correct` block has
# ---- been stripped, so no tactic script can mask the verdict. `List Char` has
# ---- DecidableEq, so every witness closes by `decide` at literal inputs.
def _tester(pre=""):
    m = "appendQopDirective"
    return (f"{pre}extract_program_for {m}\n"
            f"prove_precondition_decidable_for {m}\n"
            f"prove_postcondition_decidable_for {m}\n"
            f"derive_tester_for {m}\n\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # impl that MUST verify; else the post-image is SPEC-TOO-STRONG. The
    # obligation is preserved and only the executable surface is reshaped:
    # the whole appended suffix is assembled as ONE concatenation expression
    # instead of eight incremental mutable rebinds. Observationally identical
    # on every input (associativity of `++`); the frozen `loom_solve <;>
    # simp_all [...]` still discharges the full equality and both structural
    # pins with no new obligation.
    # =====================================================================
    {
        "id": "pos-single-concat",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    -- Assemble the whole appended suffix as a single concatenation\n"
            "    -- expression rather than eight incremental rebinds; the result\n"
            "    -- is identical on every input and no input is mutated.\n"
            "    let result : List Char :=\n"
            "      base ++ [',', ' ', 'q', 'o', 'p', '='] ++ ['\"', 'a', 'u', 't', 'h', '\"']\n"
            "        ++ [',', ' ', 'n', 'c', '='] ++ ncvalue\n"
            "        ++ [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '\"'] ++ cnonce ++ ['\"']\n"
            "    return result"),
        "rationale": (
            "a correct impl in a different executable shape (single concatenation "
            "expression, no incremental mutable rebinds) computes the identical "
            "`out` on every input and adds no new proof obligation, so the full "
            "equality and both structural pins still discharge under the frozen "
            "`loom_solve <;> simp_all [...]`; if it fails => SPEC-TOO-STRONG on "
            "impl shape."),
    },

    # =====================================================================
    # ADMISSIBILITY — no `require` clause exists, so the usual "a normal input
    # satisfies the precondition" probe is vacuous (nothing could exclude the
    # F2P-shaped input). Re-aimed at the residual admissibility risk on a total
    # domain: that the post-image is UNSATISFIABLE / degenerate at the
    # interesting point. This case discharges an in-region `assert` pinning the
    # segment at an F2P-shaped input (a credential prefix and short count /
    # client-nonce tokens) to the assembled sequence that CARRIES the quoted
    # value token — demonstrating the spec is satisfiable AND non-degenerate
    # there. The impl is kept verbatim so the method's own obligation still
    # discharges; the assert is live, not decoration: a false claim about the
    # same point leaves an unsolved `False` goal (verified during authoring).
    # =====================================================================
    {
        "id": "admiss-f2p-quoted-segment",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _RESULT_HEAD,
            "    -- Admissibility probe (F2P-shaped input): at a concrete prefix\n"
            "    -- and short count/client-nonce tokens the post-image is\n"
            "    -- satisfiable AND carries the QUOTED value token contiguously,\n"
            "    -- so the spec is non-degenerate at the interesting point.\n"
            "    assert (with_name_prefix `admiss\n"
            "      (['D','i','g','e','s','t'] ++ qopSegment ['0','1'] ['a','b']\n"
            "        = ['D','i','g','e','s','t'] ++ [',',' ','q','o','p','=']"
            " ++ ['\"','a','u','t','h','\"']\n"
            "            ++ [',',' ','n','c','='] ++ ['0','1']\n"
            "            ++ [',',' ','c','n','o','n','c','e','=','\"']"
            " ++ ['a','b'] ++ ['\"']))\n"
            + _RESULT_HEAD),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at an F2P-shaped "
            "input: a credential prefix with short count '01' and client-nonce "
            "'ab' assembles to the sequence carrying the contiguous quoted token "
            "`\"auth\"`. The in-region assert must discharge (else the obligation "
            "is unsatisfiable/PRECOND-TOO-STRONG); the impl is verbatim so the "
            "equality and structural pins still discharge under the frozen proof."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P. Witnesses vary all three binders:
    # `base` over `[]` / `['D']` / `['x']`, `ncvalue` over `[]` / `['1']` /
    # `['9']`, `cnonce` over `[]` / `['2']`.
    # =====================================================================
    {
        "id": "weak-bare-value",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-fix bug. Drop the surrounding double quotes from the value
        # token -> emit the BARE token. Correct on EVERYTHING except the one
        # window the fix is about, so it is the sharpest partial-domain rival.
        "module": _swap(
            _BASE, _QUOTED_TOKEN_LINE,
            "    result := result ++ ['a', 'u', 't', 'h']  -- BARE value token (pre-fix)"),
        "refinement": (
            "this is exactly the pre-fix behaviour (the value emitted as a bare "
            "token). Its faithful real counterpart emits the bare token and FAILS "
            "the F2P test that asserts the DOUBLE-quoted substring is present in "
            "the credential — it would NOT resolve."),
        "rationale": (
            "REJECT from the value-token pin (clause c) and the full equality "
            "(clause a): the segment must carry the QUOTED token, so the window "
            "after `, qop=` must equal `['\"','a','u','t','h','\"']`; the bare "
            "token is two characters short and every derived clause diverges. "
            "Refuted at base=['D'], ncvalue=['1'], cnonce=['2']."),
        "witness": _tester() +
                   "example : appendQopDirectiveTester ['D'] ['1'] ['2'] = false := by\n"
                   "  decide\n",
    },
    {
        "id": "weak-single-quote",
        "kind": "uniqueness",
        "expect": "reject",
        # A near-miss that wraps the value in SINGLE quotes instead of double.
        "module": _swap(
            _BASE, _QUOTED_TOKEN_LINE,
            "    result := result ++ ['\\'', 'a', 'u', 't', 'h', '\\'']  -- SINGLE-quoted"),
        "refinement": (
            "a faithful counterpart wrapping the value in SINGLE quotes emits the "
            "wrong glyph; the F2P asserts the DOUBLE-quoted substring is present, "
            "which single quotes do not satisfy, and RFC 2617 mandates the "
            "double-quoted string — it would NOT resolve."),
        "rationale": (
            "REJECT from the value-token pin (clause c): the pinned token uses the "
            "double-quote character, and the single-quote glyph differs from it, "
            "so the window after `, qop=` is not `quotedValueToken` and the full "
            "equality is false. Refuted at base=['x'], ncvalue=['9'], cnonce=[]."),
        "witness": _tester() +
                   "example : appendQopDirectiveTester ['x'] ['9'] [] = false := by\n"
                   "  decide\n",
    },
    {
        "id": "weak-missing-close-quote",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit only the OPENING quote: the value token loses its closing quote.
        "module": _swap(
            _BASE, _QUOTED_TOKEN_LINE,
            "    result := result ++ ['\"', 'a', 'u', 't', 'h']  -- MISSING closing quote"),
        "refinement": (
            "a faithful counterpart emitting an unbalanced value (no closing "
            "quote) produces a malformed credential; the quoted token is no "
            "longer a balanced contiguous run (a comma follows the token instead "
            "of the closing quote), so the F2P substring is absent — it would NOT "
            "resolve."),
        "rationale": (
            "REJECT from the value-token pin (clause c) and the head pin (clause "
            "b): without the closing quote the window after `, qop=` is one "
            "character short of `quotedValueToken`, the assembled head is not "
            "`directiveHead`, and the full equality is false. Refuted at base=[], "
            "ncvalue=[], cnonce=['2']."),
        "witness": _tester() +
                   "example : appendQopDirectiveTester [] [] ['2'] = false := by\n"
                   "  decide\n",
    },
    {
        "id": "weak-swap-values",
        "kind": "uniqueness",
        "expect": "reject",
        # Interpolate cnonce where the bare count value belongs and ncvalue where
        # the quoted client-nonce belongs. A value-level structural divergence
        # that leaves the QUOTED token intact (so it is NOT refutable by the
        # value-token pin) but breaks the full output equality whenever the two
        # interpolated values differ.
        "module": _swap(
            _BASE, _VALUE_STRETCH,
            "    result := result ++ cnonce  -- SWAPPED: cnonce in the bare count slot\n"
            "    -- ', cnonce=\"'\n"
            "    result := result ++ [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '\"']\n"
            "    -- the client-nonce value\n"
            "    result := result ++ ncvalue  -- SWAPPED: ncvalue in the client-nonce slot"),
        "refinement": (
            "a faithful counterpart interpolating the client-nonce as the bare "
            "count and the count as the quoted client-nonce emits the wrong "
            "directive values; the credential the server validates is malformed "
            "and Digest auth against the live endpoint the F2P exercises still "
            "fails — it would NOT resolve."),
        "rationale": (
            "REJECT from the full output equality (clause a): the post-image pins "
            "`... ++ ncvalue ++ directiveMid ++ cnonce ++ ...`; swapping the two "
            "interpolated values makes the equality false for any ncvalue ≠ "
            "cnonce. Refuted at base=[], ncvalue=['1'], cnonce=['2'] (distinct "
            "values), where this rival mishandles the values while the value-token "
            "pin still holds — its own separating witness, distinct from the "
            "quote-shape rivals'."),
        "witness": _tester() +
                   "example : appendQopDirectiveTester [] ['1'] ['2'] = false := by\n"
                   "  decide\n",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 cases (1 soundness
# positive, 1 admissibility, 5 uniqueness/frame rivals) over the single modeled
# function `append_qop_directive(base, ncvalue, cnonce)`. This bundle models the
# same one function as `appendQopDirective`, so the surface maps one-to-one and
# no case is dropped for a narrowed carrier.
#
#   sibling case                       -> here
#   ---------------------------------------------------------------------
#   pos-control-single-concat          -> pos-single-concat          PORTED
#   admiss-f2p-shaped                  -> admiss-f2p-quoted-segment   RE-AIMED
#   weak-bare-value                    -> weak-bare-value             PORTED
#   weak-single-quote                  -> weak-single-quote          PORTED
#   weak-missing-close-quote           -> weak-missing-close-quote    PORTED
#   weak-swap-nc-cnonce                -> weak-swap-values            PORTED
#   frame-mutate-base                  -> (none)                      VACUOUS
#
# 5 ported, 1 re-aimed, 1 vacuous = 7.
#
# RE-AIMED (admissibility): the sibling constructs an F2P-shaped input and calls
#   the function to prove the precondition is met for a normal input. Here no
#   `require` clause exists, so that reading is vacuous (nothing could exclude
#   the input). The case is re-aimed at proving the post-image is satisfiable and
#   NON-degenerate at the F2P corner (a real prefix + short tokens assemble to a
#   sequence carrying the contiguous quoted value token). The in-region assert is
#   discharged symbolically against concrete literals by the frozen proof; a
#   false claim at the same point leaves an unsolved `False` goal (verified).
# FRAME-MUTATION: VACUOUS here. The sibling's rival WRITES a read-only input held
#   at Acc(...,1/2). This backend is referentially transparent, has no heap and
#   no aliasing, and this bundle declares NO `mut` binder among the parameters
#   (`base` is copied into a local `mut result`; the parameter itself is never
#   written) — there is no read-only input to overwrite and no substitute probe
#   to build. No case fabricated.
#
# BINDER / POINT COVERAGE. The four reject witnesses probe four distinct inputs:
#   (base=['D'], ncvalue=['1'], cnonce=['2'])  weak-bare-value
#   (base=['x'], ncvalue=['9'], cnonce=[])     weak-single-quote
#   (base=[],    ncvalue=[],    cnonce=['2'])  weak-missing-close-quote
#   (base=[],    ncvalue=['1'], cnonce=['2'])  weak-swap-values
#   so `base` is varied over ['D'] / ['x'] / [], `ncvalue` over ['1'] / ['9'] /
#   [], and `cnonce` over ['2'] / []. No input binder is pinned across the
#   battery, so a rival mishandling only one input would still be caught. The
#   three top-level clauses are attacked: the value-token pin (clause c) and the
#   full equality (clause a) by the quote-shape rivals, the head pin (clause b)
#   additionally by weak-missing-close-quote, and clause a specifically on the
#   interpolated-value ordering by weak-swap-values.
#
# WITNESS DISTINCTNESS. weak-bare-value and weak-missing-close-quote both diverge
#   on the value token but at different windows (two chars short vs one char
#   short, and only the latter also breaks the head pin), and are refuted at
#   different points. weak-swap-values leaves the quoted token intact and is the
#   only rival refutable purely by the interpolated-value ordering, so it carries
#   its own witness at distinct ncvalue/cnonce rather than sharing a quote-shape
#   rival's.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom (the segment is assembled deeply from constant literals and the two
# interpolated inputs), so there is nothing there to probe.
AXIOM_TESTS = []
