# properties.py — PBT falsification battery for psf__requests-1724.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a FULL model.py variant built by region-surgery: we edit
# ONLY text strictly inside the single `# impl-start` / `# impl-end` span, so the
# frozen spec (axioms / pure / pre- / post-conditions, and the function
# signatures) is provably untouched (markers.same_spec holds). The runner then
# runs Nagini verify on each variant and checks (same_spec AND verify-outcome).
#
# Defended surface (frozen spec of normalize_method(chars, native) -> TextToken):
#   Requires  Acc(list_pred(chars), 1/2)                 # chars is READ-ONLY (half perm)
#   Ensures   Acc(list_pred(chars), 1/2)                 # read perm returned
#   Ensures   Acc(Result().chars) and Acc(list_pred(Result().chars))
#   Ensures   Acc(Result().native)
#   Ensures   len(Result().chars) == len(chars)          # length preserved
#   Ensures   ToSeq(Result().chars) == upper_seq(ToSeq(chars))   # LOAD-BEARING content pin
#   Ensures   Result().native == to_native(ToSeq(chars)) # LOAD-BEARING flavour pin (the bug-sensing clause)
#   Ensures   native_form(Result().native)               # ... and the flavour so obtained IS a native one
#
# Two load-bearing clauses:
#   (content) ToSeq(Result().chars) == upper_seq(ToSeq(chars)) — GROUNDED in the
#       argument via the fully-unfolded @Pure fold upper_seq (NOT an opaque
#       answer-key oracle: there is nothing to "echo"). Attacked by partial-domain
#       / identity / off-by-one content rivals.
#   (flavour) Result().native == to_native(ToSeq(chars)) — GROUNDED in the
#       argument through the axiomatized native-flavour constructor: the carried
#       flavour must be the one that constructor yields for the supplied content.
#       to_native leaves that flavour UNINTERPRETED (its only Ensures is the
#       opaque native_form(Result())), so the clause cannot be discharged by any
#       literal — the constructor has to be invoked on the supplied content.
#       native_form(Result().native) then states, opaquely, that the flavour so
#       obtained is a native one; it too has no other source. model_prepatch sets
#       native_flavour = native and FAILS the clause (G-DIFF), and so does an
#       impl that hands the literal True to the carrier
#       (ungrounded-flavour-literal below) — the case that made the earlier
#       constant pin Result().native == True SPEC-TOO-WEAK.
#
# chars is held at Acc(..., 1/2) => FRAME-MUTATION is MANDATORY.

from pathlib import Path

INSTANCE = "psf__requests-1724"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact gold impl body (strictly between # impl-start and # impl-end). All
# surgery replaces this whole block so the edit is guaranteed inside the span.
_GOLD_IMPL = """    # impl-start
    native_flavour = to_native(ToSeq(chars))
    out = []  # type: List[int]
    i = len(chars)
    while i > 0:
        # invariants-start
        Invariant(MustTerminate(i + 1))
        Invariant(Acc(list_pred(chars), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(chars))
        Invariant(len(out) == len(chars) - i)
        Invariant(ToSeq(out) == upper_seq(ToSeq(chars).drop(i)))
        Invariant(native_flavour == to_native(ToSeq(chars)))
        # invariants-end
        c = chars[i - 1]
        Assert(ToSeq(chars).drop(i - 1)[0] == c)
        Assert(ToSeq(chars).drop(i - 1).drop(1) == ToSeq(chars).drop(i))
        out = [upper_cp(c)] + out
        i = i - 1
    return TextToken(out, native_flavour)
    # impl-end"""

assert _GOLD_IMPL in _BASE, "drift: gold impl block not found verbatim in model.py"
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl block not unique"


def _impl(new_body_lines: str) -> str:
    """Return a full model.py whose impl span body is replaced by new_body_lines.
    new_body_lines is the text BETWEEN the markers (without the marker lines);
    we re-wrap it with the exact # impl-start / # impl-end markers so the span is
    preserved and only inner text changes (same_spec invariant)."""
    new_block = "    # impl-start\n" + new_body_lines.rstrip("\n") + "\n    # impl-end"
    return _BASE.replace(_GOLD_IMPL, new_block, 1)


# ----------------------------------------------------------------------------
# SPEC_TESTS
# ----------------------------------------------------------------------------

SPEC_TESTS = []

# === 1. UNGROUNDED-FLAVOUR ECHO (the #2 spec-too-weak mode) =================
# Keep the gold backward loop and ALL its framing asserts/invariants verbatim
# (per pilot bug #2 — do not drop the proof obligations), and drop ONLY the
# flavour derivation: never invoke the native-flavour constructor, hand the
# literal True to the carrier instead. Under a constant flavour pin
# (Ensures Result().native == True) this verifies — True == True discharges it —
# and that is exactly the hole G-EQ refuted: the faithful refinement of an impl
# that never invokes the constructor is a tree with no coercion of the supplied
# method, which leaves a non-native method non-native and does NOT resolve. The
# grounded pin (Result().native == to_native(ToSeq(chars)), to_native
# uninterpreted) must REJECT it.
SPEC_TESTS.append({
    "id": "ungrounded-flavour-literal",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _impl(
        "    out = []  # type: List[int]\n"
        "    i = len(chars)\n"
        "    while i > 0:\n"
        "        # invariants-start\n"
        "        Invariant(MustTerminate(i + 1))\n"
        "        Invariant(Acc(list_pred(chars), 1 / 2))\n"
        "        Invariant(Acc(list_pred(out)))\n"
        "        Invariant(0 <= i and i <= len(chars))\n"
        "        Invariant(len(out) == len(chars) - i)\n"
        "        Invariant(ToSeq(out) == upper_seq(ToSeq(chars).drop(i)))\n"
        "        # invariants-end\n"
        "        c = chars[i - 1]\n"
        "        Assert(ToSeq(chars).drop(i - 1)[0] == c)\n"
        "        Assert(ToSeq(chars).drop(i - 1).drop(1) == ToSeq(chars).drop(i))\n"
        "        out = [upper_cp(c)] + out\n"
        "        i = i - 1\n"
        "    return TextToken(out, True)\n"
    ),
    "refinement": "The model operation this impl drops is the one the real patch "
                  "ADDS: routing the supplied method through the native-text "
                  "constructor (`method = builtin_str(method)`) before the case "
                  "map. An impl that never invokes it refines to a tree that "
                  "leaves the caller\'s method at the flavour it arrived in, so a "
                  "non-native (py2 `unicode`) method name still reaches the header "
                  "assembly and the byte-string concatenation there raises "
                  "UnicodeDecodeError. Measured in the instance image: with no "
                  "coercion test_requests.py::RequestsTestCase::"
                  "test_unicode_method_name FAILS (deterministically, 3/3, "
                  "client-side, no network involved); with it, PASSES 3/3. So this "
                  "impl verifying under a constant flavour pin was a real "
                  "verify-not-resolve break, not an environment artifact.",
    "rationale": "Reject from the grounded flavour pin Result().native == "
                 "to_native(ToSeq(chars)): to_native is uninterpreted (its only "
                 "Ensures is the opaque native_form(Result())), so `True` cannot be "
                 "shown equal to the constructor\'s product for the supplied "
                 "content, and native_form(True) has no source either. All gold "
                 "loop invariants/asserts kept verbatim (pilot bug #2) so the "
                 "rejection is attributable to the flavour clause alone — measured: "
                 "the single reported error is the flavour postcondition.",
})

# === 1b. POSITIVE CONTROL (soundness) — the flavour derived, in another shape =
# Structurally-different-but-CORRECT impl: consume the native-flavour constructor
# AFTER the content fold rather than before it (the real-code counterpart is
# `builtin_str(method.upper())` in place of `builtin_str(method).upper()` — the
# same carried method for the ASCII method-name domain, and it resolves the same
# way). The grounded pin must NOT force one particular ORDER or one particular
# call site, only that the carried flavour be the constructor's product for the
# supplied content. Needs no native_flavour loop invariant precisely because the
# call now happens after the loop. All gold framing asserts/invariants kept.
SPEC_TESTS.append({
    "id": "pos-control-flavour-after-fold",
    "kind": "soundness",
    "expect": "verify",
    "module": _impl(
        "    out = []  # type: List[int]\n"
        "    i = len(chars)\n"
        "    while i > 0:\n"
        "        # invariants-start\n"
        "        Invariant(MustTerminate(i + 1))\n"
        "        Invariant(Acc(list_pred(chars), 1 / 2))\n"
        "        Invariant(Acc(list_pred(out)))\n"
        "        Invariant(0 <= i and i <= len(chars))\n"
        "        Invariant(len(out) == len(chars) - i)\n"
        "        Invariant(ToSeq(out) == upper_seq(ToSeq(chars).drop(i)))\n"
        "        # invariants-end\n"
        "        c = chars[i - 1]\n"
        "        Assert(ToSeq(chars).drop(i - 1)[0] == c)\n"
        "        Assert(ToSeq(chars).drop(i - 1).drop(1) == ToSeq(chars).drop(i))\n"
        "        out = [upper_cp(c)] + out\n"
        "        i = i - 1\n"
        "    native_flavour = to_native(ToSeq(chars))\n"
        "    return TextToken(out, native_flavour)\n"
    ),
    "rationale": "A faithful correct impl that derives the carried flavour from "
                 "the same constructor at a DIFFERENT point in the body MUST "
                 "verify. If it cannot, the grounded pin would be SPEC-TOO-STRONG "
                 "(pinning a call site / an operation order rather than the carried "
                 "flavour). Guards the repair of the constant-pin weakness against "
                 "overshoot.",
})

# === 2. POSITIVE CONTROL #2 (soundness, different content shape) =============
# A forward shape is BANNED here (pilot bug #3: forward-append vs front-recursive
# upper_seq needs an f(a+b) lemma). Instead, reshape WITHIN the backward loop:
# build the prepended element from upper_cp(chars[i-1]) inlined into the list
# literal (drop the intermediate `c`), keeping the framing asserts rephrased to
# use chars[i-1] directly. This is a local-variable reshape, NOT a loop-direction
# flip, so the gold proof obligations still discharge.
SPEC_TESTS.append({
    "id": "pos-control-inline-elem",
    "kind": "soundness",
    "expect": "verify",
    "module": _impl(
        "    native_flavour = to_native(ToSeq(chars))\n"
        "    out = []  # type: List[int]\n"
        "    i = len(chars)\n"
        "    while i > 0:\n"
        "        # invariants-start\n"
        "        Invariant(MustTerminate(i + 1))\n"
        "        Invariant(Acc(list_pred(chars), 1 / 2))\n"
        "        Invariant(Acc(list_pred(out)))\n"
        "        Invariant(0 <= i and i <= len(chars))\n"
        "        Invariant(len(out) == len(chars) - i)\n"
        "        Invariant(ToSeq(out) == upper_seq(ToSeq(chars).drop(i)))\n"
        "        Invariant(native_flavour == to_native(ToSeq(chars)))\n"
        "        # invariants-end\n"
        "        Assert(ToSeq(chars).drop(i - 1)[0] == chars[i - 1])\n"
        "        Assert(ToSeq(chars).drop(i - 1).drop(1) == ToSeq(chars).drop(i))\n"
        "        out = [upper_cp(chars[i - 1])] + out\n"
        "        i = i - 1\n"
        "    return TextToken(out, native_flavour)\n"
    ),
    "rationale": "Local-variable reshape (inline the element, drop intermediate "
                 "`c`) keeping the backward loop, invariants, and framing asserts. "
                 "A faithful correct impl in a different concrete shape MUST verify "
                 "(else SPEC-TOO-STRONG). Avoids the front-recursive forward-append "
                 "lemma trap (pilot bug #3).",
})

# === 3. ADMISSIBILITY =======================================================
# A positive-control caller that builds an F2P-shaped input ('post' lowercase,
# native=False — the non-native flavour the bug concerns) and calls
# normalize_method, asserting the precondition is admitted and the result pins
# hold. A freshly-built list literal carries full list_pred permission, so
# passing it to a Requires(Acc(list_pred, 1/2)) parameter is admissible. If this
# fails to verify, the precondition would be PRECOND-TOO-STRONG (rejecting a
# normal input). We keep the gold body for normalize_method itself and add the
# self-call as a NEW function inside the impl span — but a self-call must live in
# its own function; instead we exercise admissibility by replacing the body with
# the gold body PLUS a leading admissibility assertion chain that establishes the
# Requires holds for the actual parameter (the parameter is in-domain by the
# Requires itself). The strongest admissibility signal is simply that the gold
# body verifies given the Requires — but to make a DISTINCT case we add an
# explicit caller helper at module level is NOT possible (would change spec_view).
# So: admissibility here is the F2P-shaped self-consistency — assert the
# precondition's list_pred(chars,1/2) is available at entry and threads through.
SPEC_TESTS.append({
    "id": "admiss-f2p-shaped",
    "kind": "admissibility",
    "expect": "verify",
    "module": _impl(
        "    # Admissibility: the Requires Acc(list_pred(chars), 1/2) is held at\n"
        "    # entry for any in-domain (F2P-shaped) input, e.g. a lowercase\n"
        "    # method name supplied in the NON-native flavour (native False). We\n"
        "    # consume that read permission immediately (length read) to witness\n"
        "    # the precondition admits the input, then run the gold body.\n"
        "    Assert(len(chars) >= 0)\n"
        "    native_flavour = to_native(ToSeq(chars))\n"
        "    out = []  # type: List[int]\n"
        "    i = len(chars)\n"
        "    while i > 0:\n"
        "        # invariants-start\n"
        "        Invariant(MustTerminate(i + 1))\n"
        "        Invariant(Acc(list_pred(chars), 1 / 2))\n"
        "        Invariant(Acc(list_pred(out)))\n"
        "        Invariant(0 <= i and i <= len(chars))\n"
        "        Invariant(len(out) == len(chars) - i)\n"
        "        Invariant(ToSeq(out) == upper_seq(ToSeq(chars).drop(i)))\n"
        "        Invariant(native_flavour == to_native(ToSeq(chars)))\n"
        "        # invariants-end\n"
        "        c = chars[i - 1]\n"
        "        Assert(ToSeq(chars).drop(i - 1)[0] == c)\n"
        "        Assert(ToSeq(chars).drop(i - 1).drop(1) == ToSeq(chars).drop(i))\n"
        "        out = [upper_cp(c)] + out\n"
        "        i = i - 1\n"
        "    return TextToken(out, native_flavour)\n"
    ),
    "rationale": "The precondition Acc(list_pred(chars), 1/2) must admit a normal "
                 "F2P-shaped input (a lowercase method name). The leading "
                 "Assert(len(chars) >= 0) reads chars under the half-permission, "
                 "witnessing the precondition is establishable / consumable for an "
                 "in-domain input. If it cannot be discharged, PRECOND-TOO-STRONG.",
})

# === 4. FRAME-MUTATION (MANDATORY — chars is Acc(..., 1/2) read-only) ========
# Rival that WRITES to the read-only input chars to compute the result in place:
# it upper-cases chars[i] in place, then returns a TextToken aliasing chars.
# Writing chars[i] = ... requires FULL list_pred(chars) permission, but the
# Requires grants only 1/2 — so the assignment must fail for INSUFFICIENT
# PERMISSION. Gold postcondition pins kept verbatim so the rejection is
# attributable to the write, not to a content/flavour mismatch.
SPEC_TESTS.append({
    "id": "frame-mutate-input-inplace",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _impl(
        "    native_flavour = to_native(ToSeq(chars))\n"
        "    i = 0\n"
        "    while i < len(chars):\n"
        "        # invariants-start\n"
        "        Invariant(Acc(list_pred(chars), 1 / 2))\n"
        "        Invariant(0 <= i)\n"
        "        Invariant(MustTerminate(len(chars) - i + 1))\n"
        "        Invariant(native_flavour == to_native(ToSeq(chars)))\n"
        "        # invariants-end\n"
        "        # Frame violation: writing the read-only input needs FULL\n"
        "        # list_pred(chars); only 1/2 is held -> insufficient permission.\n"
        "        chars[i] = upper_cp(chars[i])\n"
        "        i = i + 1\n"
        "    return TextToken(chars, native_flavour)\n"
    ),
    "refinement": "A faithful real patch that upper-cased the SUPPLIED method "
                  "object in place would mutate the caller's argument (the str/list "
                  "passed as `method`), a destructive side effect the gold patch "
                  "never performs — gold builds a fresh value via builtin_str(...) "
                  ".upper(). An in-place rival would corrupt the caller's data and "
                  "is not behaviourally equal to gold, so it would not faithfully "
                  "resolve the F2P/P2P; verifying it would be a verify-not-resolve "
                  "break.",
    "rationale": "Reject from the permission system: chars[i] = ... requires full "
                 "list_pred(chars) write permission, but Requires grants only "
                 "Acc(list_pred(chars), 1/2). The #1 weakness class; a byte-fuzzer "
                 "never constructs an in-place write.",
})

# === 5. FRAME-MUTATION variant — grow the read-only input ====================
# Append to chars (chars.append) instead of element write — also needs full
# write permission on chars. Supporting case; carries its own refinement.
SPEC_TESTS.append({
    "id": "frame-append-input",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _impl(
        "    native_flavour = to_native(ToSeq(chars))\n"
        "    out = []  # type: List[int]\n"
        "    i = len(chars)\n"
        "    while i > 0:\n"
        "        # invariants-start\n"
        "        Invariant(MustTerminate(i + 1))\n"
        "        Invariant(Acc(list_pred(chars), 1 / 2))\n"
        "        Invariant(Acc(list_pred(out)))\n"
        "        Invariant(0 <= i and i <= len(chars))\n"
        "        Invariant(len(out) == len(chars) - i)\n"
        "        Invariant(ToSeq(out) == upper_seq(ToSeq(chars).drop(i)))\n"
        "        Invariant(native_flavour == to_native(ToSeq(chars)))\n"
        "        # invariants-end\n"
        "        c = chars[i - 1]\n"
        "        Assert(ToSeq(chars).drop(i - 1)[0] == c)\n"
        "        Assert(ToSeq(chars).drop(i - 1).drop(1) == ToSeq(chars).drop(i))\n"
        "        out = [upper_cp(c)] + out\n"
        "        i = i - 1\n"
        "    # Frame violation: mutating the read-only input by appending needs\n"
        "    # full list_pred(chars); only 1/2 is held -> insufficient permission.\n"
        "    chars.append(0)\n"
        "    return TextToken(out, native_flavour)\n"
    ),
    "refinement": "A real patch that appended to / grew the caller's supplied "
                  "method object is a destructive side effect on the caller's input "
                  "that gold never performs; it is not behaviourally equal to gold "
                  "and would not faithfully resolve. Supporting frame case.",
    "rationale": "Reject from the permission system: chars.append needs full "
                 "list_pred(chars) write permission; Requires grants only 1/2.",
})

# === 6. PARTIAL-DOMAIN — identity (drop the upper-casing) ====================
# Rival that returns a copy of chars unchanged (no upper map). It verifies ONLY on
# the sub-domain where the input has no ASCII lowercase (upper_seq is identity
# there); the content pin ToSeq(Result().chars) == upper_seq(ToSeq(chars)) must
# REJECT it because it cannot be proven for an arbitrary in-domain chars (e.g. a
# lowercase 'post'). Uses a fresh copy (no frame issue) so the rejection is purely
# the content clause.
SPEC_TESTS.append({
    "id": "partial-identity-no-upper",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _impl(
        "    native_flavour = to_native(ToSeq(chars))\n"
        "    out = []  # type: List[int]\n"
        "    i = len(chars)\n"
        "    while i > 0:\n"
        "        # invariants-start\n"
        "        Invariant(MustTerminate(i + 1))\n"
        "        Invariant(Acc(list_pred(chars), 1 / 2))\n"
        "        Invariant(Acc(list_pred(out)))\n"
        "        Invariant(0 <= i and i <= len(chars))\n"
        "        Invariant(len(out) == len(chars) - i)\n"
        "        Invariant(ToSeq(out) == ToSeq(chars).drop(i))\n"
        "        Invariant(native_flavour == to_native(ToSeq(chars)))\n"
        "        # invariants-end\n"
        "        c = chars[i - 1]\n"
        "        Assert(ToSeq(chars).drop(i - 1)[0] == c)\n"
        "        Assert(ToSeq(chars).drop(i - 1).drop(1) == ToSeq(chars).drop(i))\n"
        "        out = [c] + out\n"
        "        i = i - 1\n"
        "    return TextToken(out, native_flavour)\n"
    ),
    "refinement": "A real patch that copied the method WITHOUT case-normalising it "
                  "(dropping .upper()) sends a lowercase method 'post' instead of "
                  "'POST'; HTTP method dispatch / redirect handling and the F2P "
                  "tests that exercise method case (e.g. uppercase-scheme redirect, "
                  "the request method carried into the prepared request) would not "
                  "behave as gold. So this faithful impl would not resolve.",
    "rationale": "Reject from the content pin ToSeq(Result().chars) == "
                 "upper_seq(ToSeq(chars)): for a lowercase input, out == chars != "
                 "upper_seq(chars). The matching invariant (out == chars.drop(i)) "
                 "is provable but the postcondition then fails.",
})

# === 7. PARTIAL-DOMAIN — off-by-one (skip the first element's upper map) =====
# Rival upper-cases every position EXCEPT the first (i == 1 leaves chars[0] raw).
# It would verify on inputs whose first code point is not lowercase (e.g. 'POST',
# 'Get'), but the content pin must REJECT it because for a lowercase-leading input
# ('post') the first element diverges from upper_seq. Fresh `out` (no frame
# issue). Invariant relaxed to match the executable shape so the rejection is the
# postcondition, not a proof gap.
SPEC_TESTS.append({
    "id": "partial-skip-first-upper",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _impl(
        "    native_flavour = to_native(ToSeq(chars))\n"
        "    out = []  # type: List[int]\n"
        "    i = len(chars)\n"
        "    while i > 1:\n"
        "        # invariants-start\n"
        "        Invariant(MustTerminate(i + 1))\n"
        "        Invariant(Acc(list_pred(chars), 1 / 2))\n"
        "        Invariant(Acc(list_pred(out)))\n"
        "        Invariant(0 <= i and i <= len(chars))\n"
        "        Invariant(len(out) == len(chars) - i)\n"
        "        Invariant(ToSeq(out) == upper_seq(ToSeq(chars).drop(i)))\n"
        "        Invariant(native_flavour == to_native(ToSeq(chars)))\n"
        "        # invariants-end\n"
        "        c = chars[i - 1]\n"
        "        Assert(ToSeq(chars).drop(i - 1)[0] == c)\n"
        "        Assert(ToSeq(chars).drop(i - 1).drop(1) == ToSeq(chars).drop(i))\n"
        "        out = [upper_cp(c)] + out\n"
        "        i = i - 1\n"
        "    # leave the first element (chars[0]) un-upper-cased when len>=1\n"
        "    if len(chars) > 0:\n"
        "        first = chars[0]  # type: int\n"
        "        out = [first] + out\n"
        "    return TextToken(out, native_flavour)\n"
    ),
    "refinement": "A real patch that case-normalised all but the first character "
                  "of the method ('pOST' from 'post') sends a malformed method; the "
                  "carried request method would be wrong on lowercase-leading method "
                  "names, diverging from gold on the F2P/P2P method-case behaviour. "
                  "Not behaviourally equal to gold, would not resolve.",
    "rationale": "Reject from the content pin: for a lowercase-leading input, "
                 "Result().chars[0] == chars[0] != upper_cp(chars[0]), so "
                 "ToSeq(Result().chars) != upper_seq(ToSeq(chars)).",
})

# === 8. FLAVOUR ECHO OF THE SUPPLIED FLAVOUR ================================
# Both pins are GROUNDED in the argument: the content pin through the fully
# unfolded upper_seq fold, the flavour pin through the uninterpreted
# native-flavour constructor (case 1 is the ungrounded-literal rival the constant
# pin Result().native == True used to admit, and the reason "setting native True
# IS the correct work, so there is no echo to make" was wrong: in the real code
# setting the flavour IS invoking the constructor, and an impl that only CLAIMS
# the flavour refines to code that never coerces). This case is the other value
# cheat: right length, right content, but the flavour flipped to the supplied
# `native` — the discriminating defect, which the flavour pin must reject.
SPEC_TESTS.append({
    "id": "flavour-echo-supplied",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _impl(
        "    out = []  # type: List[int]\n"
        "    i = len(chars)\n"
        "    while i > 0:\n"
        "        # invariants-start\n"
        "        Invariant(MustTerminate(i + 1))\n"
        "        Invariant(Acc(list_pred(chars), 1 / 2))\n"
        "        Invariant(Acc(list_pred(out)))\n"
        "        Invariant(0 <= i and i <= len(chars))\n"
        "        Invariant(len(out) == len(chars) - i)\n"
        "        Invariant(ToSeq(out) == upper_seq(ToSeq(chars).drop(i)))\n"
        "        # invariants-end\n"
        "        c = chars[i - 1]\n"
        "        Assert(ToSeq(chars).drop(i - 1)[0] == c)\n"
        "        Assert(ToSeq(chars).drop(i - 1).drop(1) == ToSeq(chars).drop(i))\n"
        "        out = [upper_cp(c)] + out\n"
        "        i = i - 1\n"
        "    return TextToken(out, native)\n"
    ),
    "refinement": "This is exactly the pre-patch behaviour: carry the SUPPLIED "
                  "flavour (native_flavour = native) instead of forcing native. A "
                  "non-native (py2 unicode) method then stays non-native and "
                  "contaminates the byte-string header assembly downstream — the "
                  "very bug the patch fixes. model_prepatch.py is this impl and the "
                  "issue's failing behaviour; it does NOT resolve the F2P.",
    "rationale": "Reject from the grounded flavour pin Result().native == "
                 "to_native(ToSeq(chars)): the supplied `native` is not the "
                 "constructor\'s product for the supplied content (and nothing "
                 "gives native_form of it). Identical to model_prepatch (G-DIFF).",
})

# === 9. CONTROL-FLOW-EFFECT — divergence (the termination obligation) ========
# normalize_method has no observable raise path or side-effect channel beyond the
# read-only input (covered by frame-mutation) and the freshly constructed result.
# The one remaining control-flow channel is NON-TERMINATION: a rival that does
# all the modeled work and then diverges satisfies every value clause vacuously
# (the code after an endless loop is unreachable, so Viper proves the
# postcondition from False). Its faithful refinement is a request that never
# returns, which resolves nothing and hangs the suite, so the spec has to refuse
# it — that is what Requires(MustTerminate(3)) on the method plus the per-loop
# MustTerminate invariants are for, and this case is their control.
SPEC_TESTS.append({
    "id": "diverge-after-fold",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _impl(
        "    native_flavour = to_native(ToSeq(chars))\n"
        "    out = []  # type: List[int]\n"
        "    i = len(chars)\n"
        "    while i > 0:\n"
        "        # invariants-start\n"
        "        Invariant(MustTerminate(i + 1))\n"
        "        Invariant(Acc(list_pred(chars), 1 / 2))\n"
        "        Invariant(Acc(list_pred(out)))\n"
        "        Invariant(0 <= i and i <= len(chars))\n"
        "        Invariant(len(out) == len(chars) - i)\n"
        "        Invariant(ToSeq(out) == upper_seq(ToSeq(chars).drop(i)))\n"
        "        Invariant(native_flavour == to_native(ToSeq(chars)))\n"
        "        # invariants-end\n"
        "        c = chars[i - 1]\n"
        "        Assert(ToSeq(chars).drop(i - 1)[0] == c)\n"
        "        Assert(ToSeq(chars).drop(i - 1).drop(1) == ToSeq(chars).drop(i))\n"
        "        out = [upper_cp(c)] + out\n"
        "        i = i - 1\n"
        "    while 0 == 0:\n"
        "        # invariants-start\n"
        "        Invariant(Acc(list_pred(chars), 1 / 2))\n"
        "        Invariant(Acc(list_pred(out)))\n"
        "        # invariants-end\n"
        "        i = i - 1\n"
        "    return TextToken(out, native_flavour)\n"
    ),
    "refinement": "A real counterpart that computed the carried method and then "
                  "looped forever would make every request hang: the F2P/P2P suite "
                  "never returns a verdict, so the harness records no resolution. "
                  "Behaviourally it is as far from gold as an impl can be, and it "
                  "is the one rival that a value-only spec accepts for free, since "
                  "the clauses are then proven from an unreachable state.",
    "rationale": "Reject from the termination obligation: the method carries "
                 "Requires(MustTerminate(3)), so every loop in the body needs a "
                 "MustTerminate invariant whose measure decreases; the endless loop "
                 "has none and cannot have one. Without that obligation this rival "
                 "verifies vacuously (measured on the pre-repair spec), which is "
                 "why the obligation is part of the defended surface.",
})


# ----------------------------------------------------------------------------
# AXIOM_TESTS — the bundle carries one @ContractOnly axiom (to_native, A-consumed)
# and one A-reference deep model (upper_seq == str.upper). Both are checked by
# the real callee in Docker. We reuse/strengthen axiom_check.py's logic, calling
# the REAL callees (pilot bug #4: never scrape source).
# ----------------------------------------------------------------------------

AXIOM_TESTS = []

# --- ax-sound-to_native: AXIOM-SOUNDNESS for to_native (~ builtin_str) --------
# Obligation: builtin_str(value) is ALWAYS of the native text flavour
# (type(...) is str on the running interpreter), independent of the argument's
# flavour — which is what the axiom's only Ensures, the opaque
# native_form(Result()), says of the flavour it yields. Fuzz native args, the
# other text flavour (bytes / unicode), boundaries (empty), and method-name
# sentinels. We call the REAL requests.compat.builtin_str (the symbol the gold
# patch imports), falling back to stdlib str only if requests is absent.
AXIOM_TESTS.append({
    "id": "ax-sound-to_native",
    "axiom": "to_native",
    "kind": "axiom-soundness",
    "expect": "holds",
    "apply_gold": True,
    "probe": r'''
import sys, random
# Real native-flavour constructor the gold patch imports & calls.
try:
    from requests.compat import builtin_str as REAL
    src = "requests.compat.builtin_str"
except Exception as e:
    REAL = str
    src = "stdlib str (requests not importable: %r)" % (e,)

def is_native(v):
    # The native text flavour == the builtin str type on the running
    # interpreter (str on py3; the byte-str on py2).
    return type(v) is str

# Inputs spanning the flavours builtin_str must coerce: already-native text,
# the OTHER text flavour (bytes, and unicode where distinct), plus boundaries
# and HTTP method-name sentinels. The to_native axiom claims the PRODUCT is
# native for every one of these.
cases = []
native_args = ["POST", "get", "", "DELETE", "x", "Get", "pOsT", "options"]
cases.extend(native_args)
cases.extend([b"POST", b"get", b"", b"x"])          # bytes flavour
try:
    cases.extend([unicode("POST"), unicode("get"), unicode("")])  # py2 unicode
except NameError:
    cases.extend([u"POST", u"get", u""])            # py3: u'' is str, still native

rng = random.Random(1724)
ALPH = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
for _ in range(5000):
    n = rng.randint(0, 12)
    s = "".join(rng.choice(ALPH) for _ in range(n))
    cases.append(s)
    cases.append(s.encode("ascii"))

bad = 0
for v in cases:
    produced = REAL(v)
    if not is_native(produced):
        bad += 1
        if bad <= 5:
            print("AXIOM-UNSOUND to_native on %r (%s): builtin_str -> %r (%s) NOT native"
                  % (v, type(v).__name__, produced, type(produced).__name__))
if bad:
    print("to_native axiom UNSOUND: %d/%d inputs produced non-native (%s)"
          % (bad, len(cases), src))
    sys.exit(1)
print("ax-sound-to_native OK: builtin_str (%s) produced the native flavour on "
      "all %d inputs (native + bytes + unicode + 5000 fuzz)" % (src, len(cases)))
sys.exit(0)
''',
    "rationale": "AXIOM-UNSOUND if the real builtin_str ever yields a non-native "
                 "value. The proof consumes only Ensures(native_form(Result())) "
                 "(the flavour produced IS a native one, the value of that flavour "
                 "left uninterpreted); the patch newly calls builtin_str on "
                 "the supplied method to force the native flavour before .upper(). "
                 "Probe calls the REAL callee (pilot bug #4) over the flavour "
                 "spectrum it must coerce.",
})

# --- ax-cover-to_native: AXIOM-CONTAINMENT for to_native ----------------------
# The model reaches to_native(ToSeq(chars)) for ANY chars satisfying the
# Requires Acc(list_pred(chars), 1/2): an arbitrary finite sequence of ints. The
# axiom's Requires domain is the whole PSeq[int] (no domain restriction — the
# only Ensures, native_form(Result()), is unconditional). So every caller-reachable input
# (every code-point sequence) lies inside the axiom domain. We DEMONSTRATE this
# by running the real callee on the most extreme code-point sequences the caller
# could pass (empty, full ASCII control range, high code points) and confirming
# the real callee accepts them and stays native — i.e. nothing the model can
# reach falls outside what builtin_str handles natively.
AXIOM_TESTS.append({
    "id": "ax-cover-to_native",
    "axiom": "to_native",
    "kind": "axiom-containment",
    "expect": "covered",
    "apply_gold": True,
    "probe": r'''
import sys
try:
    from requests.compat import builtin_str as REAL
    src = "requests.compat.builtin_str"
except Exception as e:
    REAL = str
    src = "stdlib str (requests not importable: %r)" % (e,)

def is_native(v):
    return type(v) is str

# The model's Requires admits ANY finite code-point sequence (List[int] -> PSeq).
# to_native's Requires is the whole PSeq[int] domain (unconditional Ensures), so
# containment is trivially total: there is NO caller-reachable input outside it.
# We witness this by exercising the extremes of the reachable code-point domain
# (the str the supplied method materialises to) and confirming builtin_str both
# ACCEPTS them and yields a native value -- i.e. the axiom's claim covers them.
extreme = [
    "",                                   # empty method
    "".join(chr(c) for c in range(0, 128)),  # full ASCII incl. controls
    "post", "POST", "Get", "pOsT",        # F2P method-name shapes
    "éÿ",                       # high Latin-1 (non-ASCII code points)
    "Āſ",                       # beyond Latin-1
]
bad = 0
for s in extreme:
    produced = REAL(s)
    if not is_native(produced):
        bad += 1
        print("CONTAINMENT GAP: reachable input %r produced non-native %r (%s)"
              % (s, produced, type(produced).__name__))
if bad:
    print("to_native AXIOM-TOO-WEAK-FOR-CALLER: %d reachable inputs not covered (%s)"
          % (bad, src))
    sys.exit(1)
print("ax-cover-to_native OK: to_native's domain (all PSeq[int]) contains every "
      "caller-reachable code-point sequence; builtin_str (%s) accepts & stays "
      "native on all %d extremes" % (src, len(extreme)))
sys.exit(0)
''',
    "rationale": "AXIOM-TOO-WEAK-FOR-CALLER only if the model could pass an input "
                 "outside the axiom's Requires domain. to_native's domain is the "
                 "whole PSeq[int]; the model's Requires admits exactly arbitrary "
                 "code-point sequences -> total containment. Witnessed on the "
                 "domain extremes the caller can reach.",
})

# --- ax-sound-upper_seq: A-REFERENCE deep model == real str.upper -------------
# upper_seq is NOT a consumed axiom; it is a deep model validated == the real
# str.upper on the ASCII method-name domain (G-AX). Re-run that here, calling the
# REAL str.upper (pilot bug #4) over the exhaustive 128-code-point ASCII sweep,
# the ten HTTP method names, and a large randomized ASCII fuzz. Any mismatch in
# the ASCII domain the methods inhabit is a deep-model unsoundness.
AXIOM_TESTS.append({
    "id": "ax-sound-upper_seq",
    "axiom": "upper_seq",
    "kind": "axiom-soundness",
    "expect": "holds",
    "apply_gold": True,
    "probe": r'''
import sys, random

def upper_cp(c):
    if 97 <= c <= 122:   # 'a'..'z' -> 'A'..'Z'
        return c - 32
    return c

def upper_seq(cps):
    return [upper_cp(c) for c in cps]

def check(s):
    observed = [ord(ch) for ch in s.upper()]        # REAL str.upper callee
    expected = upper_seq([ord(ch) for ch in s])     # deep model
    return observed == expected

bad = 0
samples = []
# exhaustive single ASCII code point
for c in range(0, 128):
    samples.append(chr(c))
# HTTP method names + mixed-case boundaries
samples += ["", "get", "post", "put", "delete", "head", "options", "patch",
            "trace", "connect", "GET", "POST", "Get", "pOsT", "abcXYZ123",
            "".join(chr(c) for c in range(0, 128))]
# randomized ASCII fuzz
rng = random.Random(1724)
for _ in range(20000):
    n = rng.randint(0, 16)
    samples.append("".join(chr(rng.randint(0, 127)) for _ in range(n)))

for s in samples:
    if not check(s):
        bad += 1
        if bad <= 5:
            print("DEEP-MODEL UNSOUND upper_seq on %r: str.upper=%r model=%r"
                  % (s, [ord(ch) for ch in s.upper()],
                     upper_seq([ord(ch) for ch in s])))
if bad:
    print("upper_seq deep model UNSOUND vs str.upper: %d/%d mismatches"
          % (bad, len(samples)))
    sys.exit(1)
print("ax-sound-upper_seq OK: deep model == real str.upper on 128 ASCII sweep + "
      "method names + 20000 fuzz (%d inputs)" % (len(samples),))
sys.exit(0)
''',
    "rationale": "A-reference: the deep model upper_seq/upper_cp must equal the "
                 "real str.upper on the ASCII method-name domain (G-AX). Any "
                 "mismatch is deep-model unsoundness. Calls the REAL str.upper "
                 "(pilot bug #4), not source scraping.",
})

# --- ax-cover-upper_seq: A-REFERENCE caller-domain containment ----------------
# The model invokes the upper map ONLY on code points drawn from chars (the
# supplied method). The deep model claims faithfulness on the ASCII domain
# (0..127), which is where HTTP method names live. The containment question:
# could the caller reach a code point OUTSIDE the validated ASCII domain where
# str.upper diverges from upper_cp (locale / multi-char expansion)? The F2P/P2P
# methods are ASCII; we DEMONSTRATE the divergence boundary so the model's
# ASCII-only faithfulness claim is honest: confirm str.upper == upper_cp across
# 0..127 (covered) AND exhibit a known non-ASCII point where they differ (the
# claim's stated boundary), so the scope is documented, not silently exceeded.
AXIOM_TESTS.append({
    "id": "ax-cover-upper_seq",
    "axiom": "upper_seq",
    "kind": "axiom-containment",
    "expect": "covered",
    "apply_gold": True,
    "probe": r'''
import sys

def upper_cp(c):
    if 97 <= c <= 122:
        return c - 32
    return c

# 1) Containment: every ASCII code point (the caller-reachable method domain)
#    is covered -- str.upper agrees with upper_cp on all of 0..127.
gap = 0
for c in range(0, 128):
    if [ord(x) for x in chr(c).upper()] != [upper_cp(c)]:
        gap += 1
        print("ASCII containment gap at code point %d: str.upper=%r upper_cp=%d"
              % (c, [ord(x) for x in chr(c).upper()], upper_cp(c)))
if gap:
    print("upper_seq AXIOM-TOO-WEAK-FOR-CALLER: %d ASCII code points diverge" % gap)
    sys.exit(1)

# 2) Honest scope boundary: the deep model claims faithfulness ONLY on ASCII.
#    Outside it, real str.upper has multi-char / locale expansions (e.g. the
#    German sharp-s expands to 'SS'; a single code point upper-maps to two).
#    The caller (HTTP method names) never reaches these, so the ASCII-only scope
#    is a CORRECT containment (float-vs-int rule: covering exactly the reachable
#    domain is sound). We assert such a point exists to document the boundary.
sharp_s = "ß"  # U+00DF LATIN SMALL LETTER SHARP S
expands = len(sharp_s.upper()) > 1 or [ord(x) for x in sharp_s.upper()] != [upper_cp(ord(sharp_s))]
print("scope boundary witnessed: str.upper(%r)=%r vs single-cp model upper_cp -> "
      "non-ASCII expansion=%s (caller never reaches non-ASCII method names)"
      % (sharp_s, sharp_s.upper(), expands))
print("ax-cover-upper_seq OK: ASCII method domain (0..127) fully covered by the "
      "deep model; non-ASCII is outside the caller-reachable domain (sound scope)")
sys.exit(0)
''',
    "rationale": "AXIOM-TOO-WEAK-FOR-CALLER only if a caller-reachable code point "
                 "lies outside the validated domain. HTTP method names are ASCII "
                 "(0..127), fully covered. The deep model's ASCII-only scope is a "
                 "correct containment (covering exactly the reachable domain is "
                 "sound); non-ASCII str.upper expansions are unreachable here.",
})
