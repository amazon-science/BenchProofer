# properties.py — PBT falsification battery for psf__requests-1766.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a FULL model.py variant that shares the frozen spec exactly
# (same_spec) and edits ONLY the impl region (between `# impl-start`/`# impl-end`)
# via region-surgery on _BASE. The runner checks each with Nagini verify +
# same_spec.
#
# Defended surface (read model.py + refinement.md + instance.json):
#   append_qop_directive(base, ncvalue, cnonce) assembles a Digest credential's
#   quality-of-protection directive segment. The gold patch wraps the value
#   `auth` in double quotes (`qop=auth` -> `qop="auth"`); the F2P test
#   test_DIGESTAUTH_QUOTES_QOP_VALUE asserts `'"auth"' in Authorization`.
#
#   ALL THREE inputs are READ-ONLY: Acc(list_pred(base|ncvalue|cnonce), 1/2).
#   => FRAME-MUTATION is mandatory (a rival that writes an input to build the
#      result must be rejected for insufficient permission).
#
#   Load-bearing postcondition (model.py:99):
#      ToSeq(Result()) == ToSeq(base) + qop_segment(ToSeq(ncvalue), ToSeq(cnonce))
#   a FULL equality pinning the entire output to a function of the inputs, plus
#   two structural pins (model.py:103-104) anchoring the QUOTED token `"auth"`
#   (PSeq(34,97,117,116,104,34)) contiguously at the head of the segment.
#
#   The @Pure helpers (qop_segment / directive_head / quoted_value_token) are
#   GROUNDED: ncvalue/cnonce are the function's own args and every other piece is
#   a fully-unfolded constant PSeq literal. There is NO opaque answer-key oracle
#   to echo (no ContractOnly, no axioms) — so ungrounded-oracle echo does not
#   apply here; see 'assessment'. Instead an honest cheapest correct impl is the
#   positive control.
#
#   No @ContractOnly axioms, no deep-model A-references => AXIOM_TESTS = [].
from pathlib import Path

INSTANCE = "psf__requests-1766"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The exact impl-region pieces we surgically replace. Each `old` below occurs
# EXACTLY ONCE in model.py and lies strictly inside # impl-start / # impl-end,
# so every variant is same_spec by construction.
# ---------------------------------------------------------------------------

# The whole gold impl body (used by variants that restructure the construction).
_GOLD_IMPL = """    result = list(base)  # type: List[int]
    # ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
    result = result + [44, 32, 113, 111, 112, 61]
    result = result + [34, 97, 117, 116, 104, 34]
    result = result + [44, 32, 110, 99, 61]
    # the count value, bare
    result = result + ncvalue
    # ', cnonce="'
    result = result + [44, 32, 99, 110, 111, 110, 99, 101, 61, 34]
    # the client-nonce value
    result = result + cnonce
    # closing double quote
    result = result + [34]
    return result"""

# The single line carrying the QUOTED value token `"auth"` = [34,97,117,116,104,34].
_QUOTED_TOKEN_LINE = "    result = result + [34, 97, 117, 116, 104, 34]"


# === SPEC_TESTS =============================================================
SPEC_TESTS = []

# --- 1. FRAME-MUTATION (MANDATORY: all inputs are Acc(...,1/2) read-only) ----
# Rival builds the result by MUTATING the read-only input `base` in place
# (base += ... then return base) instead of allocating a fresh list. `base`
# carries only Acc(list_pred(base), 1/2) — a write needs the full predicate, so
# this must be REJECTED for insufficient permission. The gold postconditions are
# kept verbatim, so the rejection is attributable purely to the input write.
_frame_mut = _swap(
    _BASE, _GOLD_IMPL,
    """    # Adversary: mutate the read-only input `base` in place to assemble the
    # credential, then return it. base has only Acc(list_pred(base), 1/2);
    # an in-place append needs full write permission => must REJECT.
    base.append(44)
    base.append(32)
    base.append(113)
    base.append(111)
    base.append(112)
    base.append(61)
    base.append(34)
    base.append(97)
    base.append(117)
    base.append(116)
    base.append(104)
    base.append(34)
    return base""")
SPEC_TESTS.append({
    "id": "frame-mutate-base",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _frame_mut,
    "refinement": (
        "A faithful real patch that mutated the caller's credential buffer in "
        "place (appending to `base` and returning it) would alias-corrupt the "
        "HTTPDigestAuth credential accumulation across the surrounding "
        "build_digest_header logic; it is NOT the gold `base += ...` rebind "
        "(`str` += allocates a new str object) and would not be the accepted fix. "
        "Here it must be rejected at the spec level for insufficient permission — "
        "the only `Acc` on base is 1/2."),
    "rationale": (
        "permission system: base has Acc(list_pred(base), 1/2) (model.py:88); "
        "list.append mutates and requires the full predicate, so this fails to "
        "verify for insufficient permission, NOT a postcondition mismatch."),
})

# --- 2. PARTIAL-DOMAIN / pre-patch: bare `auth` (the literal bug) ------------
# Drop the surrounding double quotes (34) from the value token -> emit the bare
# `qop=auth, nc=` exactly like the pre-patch code. This is correct on EVERYTHING
# except the one byte-pair the fix is about, so it is the sharpest partial-domain
# rival. Must REJECT (postcondition pins the QUOTED token).
_bare_value = _swap(
    _BASE, _QUOTED_TOKEN_LINE,
    "    result = result + [97, 117, 116, 104]  # BARE value `auth` (pre-patch bug)")
SPEC_TESTS.append({
    "id": "weak-bare-value",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _bare_value,
    "refinement": (
        "This is exactly the pre-patch behaviour (`qop=auth`). Its faithful real "
        "patch emits the bare value and FAILS the F2P "
        "test_DIGESTAUTH_QUOTES_QOP_VALUE which asserts `'\"auth\"' in "
        "Authorization` — it would not resolve."),
    "rationale": (
        "postcondition ToSeq(Result()) == ToSeq(base) + qop_segment(...) "
        "(model.py:99) plus the structural pin "
        "directive_head()...drop(6)==quoted_value_token() (model.py:104): the "
        "segment must carry [34,97,117,116,104,34]; bare auth differs."),
})

# --- 3. WRONG-QUOTE-GLYPH: single quote `'auth'` instead of `"auth"` ---------
# Use the single-quote code point 39 instead of the double-quote 34 around the
# value. A real near-miss that emits `qop='auth'`. Must REJECT.
_single_quote = _swap(
    _BASE, _QUOTED_TOKEN_LINE,
    "    result = result + [39, 97, 117, 116, 104, 39]  # SINGLE-quoted `'auth'`")
SPEC_TESTS.append({
    "id": "weak-single-quote",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _single_quote,
    "refinement": (
        "A faithful real patch wrapping the value in SINGLE quotes emits "
        "`qop='auth'`; the F2P asserts the DOUBLE-quoted substring `'\"auth\"'` "
        "is present, which single quotes do not satisfy — it would not resolve, "
        "and RFC 2617 requires the double-quoted string."),
    "rationale": (
        "postcondition pins quoted_value_token() == PSeq(34,97,117,116,104,34) "
        "(double quote 34, model.py:51,104); code point 39 != 34 makes the "
        "ToSeq equality clause false."),
})

# --- 4. MISSING-CLOSING-QUOTE: open `"auth` with no closing quote ------------
# Emit only the opening double quote: `, qop="auth, nc=`. Real malformed output.
# Must REJECT.
_no_close = _swap(
    _BASE, _QUOTED_TOKEN_LINE,
    "    result = result + [34, 97, 117, 116, 104]  # MISSING closing quote")
SPEC_TESTS.append({
    "id": "weak-missing-close-quote",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _no_close,
    "refinement": (
        "A faithful real patch emitting `qop=\"auth, nc=` (no closing quote) "
        "produces a malformed credential; the value token is no longer the "
        "balanced quoted string `\"auth\"` and the F2P substring `'\"auth\"'` is "
        "not present as a contiguous run (the `,` follows the `h`), so it would "
        "not resolve."),
    "rationale": (
        "postcondition: directive_head() = `, qop=` + quoted_value_token() + "
        "`, nc=` (model.py:59); without the closing 34 the assembled head differs "
        "from directive_head(), breaking the ToSeq equality and the structural "
        "take(len(directive_head())) pin (model.py:103)."),
})

# --- 5. SUPPORTING near-miss: nc / cnonce values swapped ---------------------
# Interpolate `cnonce` where `ncvalue` belongs and vice versa. Both are read-only
# args; this is a value-level structural divergence. Must REJECT.
_swap_vals = _swap(
    _BASE,
    "    result = result + ncvalue\n    # ', cnonce=\"'\n    result = result + [44, 32, 99, 110, 111, 110, 99, 101, 61, 34]\n    # the client-nonce value\n    result = result + cnonce",
    "    result = result + cnonce  # SWAPPED: cnonce in the bare nc slot\n    # ', cnonce=\"'\n    result = result + [44, 32, 99, 110, 111, 110, 99, 101, 61, 34]\n    # the client-nonce value\n    result = result + ncvalue  # SWAPPED: ncvalue in the cnonce slot")
SPEC_TESTS.append({
    "id": "weak-swap-nc-cnonce",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap_vals,
    "refinement": (
        "A faithful patch interpolating cnonce as the bare count and ncvalue as "
        "the quoted client-nonce emits the wrong directive values; the credential "
        "the server validates would be malformed and the request would fail Digest "
        "auth on the live endpoint the F2P exercises — it would not resolve."),
    "rationale": (
        "postcondition ToSeq(Result()) == ToSeq(base) + directive_head() + ncvalue "
        "+ directive_mid() + cnonce + directive_tail() (model.py:99,81): swapping "
        "ncvalue and cnonce makes the ToSeq equality false for any ncvalue != "
        "cnonce."),
})

# --- 6. POSITIVE CONTROL (soundness): structurally-different CORRECT impl -----
# Same behaviour, different executable shape: build the whole appended suffix in
# ONE concatenated list literal (instead of seven incremental `result = result +`
# rebinds), interleaving the two input lists with `+`. Pins nothing extra; the
# gold postcondition's ToSeq equality is established by associativity of `+`,
# which Nagini discharges automatically for PSeq/list `+`. MUST VERIFY (else
# SPEC-TOO-STRONG). No fold/induction is involved, so there is no auto-discharge
# proof-gap risk (pilot bug #3 N/A).
_pos_control = _swap(
    _BASE, _GOLD_IMPL,
    """    # Structurally different but behaviourally identical: assemble the
    # appended suffix as a single concatenation expression rather than seven
    # incremental rebinds. Same result; no input is written.
    head = [44, 32, 113, 111, 112, 61] + [34, 97, 117, 116, 104, 34] + [44, 32, 110, 99, 61]  # type: List[int]
    mid = [44, 32, 99, 110, 111, 110, 99, 101, 61, 34]  # type: List[int]
    # `list(base)` is lifted into its own typed statement: Nagini cannot infer
    # the element type of a generic `list(...)` constructor embedded directly in
    # a `+` chain (it raises `generic.constructor.without.type`). Binding it to a
    # `# type: List[int]` local first is a pure proof/translation accommodation;
    # the assembled result and the (still single) concatenation expression are
    # behaviourally identical and write no input.
    prefix = list(base)  # type: List[int]
    result = prefix + head + ncvalue + mid + cnonce + [34]  # type: List[int]
    return result""")
SPEC_TESTS.append({
    "id": "pos-control-single-concat",
    "kind": "soundness",
    "expect": "verify",
    "module": _pos_control,
    "rationale": (
        "a correct impl in a different executable shape (single concatenation "
        "expression, no incremental rebinds, no input mutation) must verify; the "
        "ToSeq equality follows from associativity of list/PSeq `+`, which Nagini "
        "discharges without induction. If it fails => SPEC-TOO-STRONG."),
})

# --- 7. ADMISSIBILITY: precondition admits an F2P-shaped input ---------------
# A self-call caller: build three concrete in-domain List[int] (an F2P-shaped
# base + ncvalue + cnonce), establish their list_pred, and call
# append_qop_directive. If the Requires (Acc(...,1/2) on each) cannot be met for
# a normal input => PRECOND-TOO-STRONG. The original function is kept intact (we
# only edit its impl region to ALSO exercise a self-call); same_spec holds.
_admiss = _swap(
    _BASE, _GOLD_IMPL,
    _GOLD_IMPL + """


def _admissibility_caller() -> None:
    # An F2P-shaped input: a non-empty prefix 'Digest' and two short token
    # values (nc '00000001', cnonce 'abcd').
    base = [68, 105, 103, 101, 115, 116]  # type: List[int]
    nc = [48, 48, 48, 48, 48, 48, 48, 49]  # type: List[int]
    cn = [97, 98, 99, 100]  # type: List[int]
    out = append_qop_directive(base, nc, cn)  # type: List[int]
    # Reading the result back is legitimate (full perm on Result()).
    assert len(out) >= 0""")
SPEC_TESTS.append({
    "id": "admiss-f2p-shaped",
    "kind": "admissibility",
    "expect": "verify",
    "module": _admiss,
    "rationale": (
        "a positive-control caller constructs an F2P-shaped input (prefix "
        "'Digest', nc '00000001', cnonce 'abcd') and calls append_qop_directive; "
        "the Requires (Acc(list_pred(x),1/2) on each fresh list) is established "
        "trivially. If the call site fails to verify => PRECOND-TOO-STRONG."),
})


# === AXIOM_TESTS ============================================================
# No @ContractOnly axioms and no deep-model A-references: the directive segment
# is a %-format of a constant template with two %s substitutions, modelled deeply
# as PSeq concatenation. meta.json axioms == [] and deep_model_references == [].
# Nothing to probe in Docker.
AXIOM_TESTS = []
