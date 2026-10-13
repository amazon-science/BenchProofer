"""properties.py — G-PBT falsification battery for django__django-15503 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both of which the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct compileRhsPath`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  compileRhsPath (lhsPath : List Char) (keys : List (List Char))
      return (out : List Char)
    require keys ≠ []
    require keys.all isSimpleKey
    ensures out = lhsPath ++ compilePrefix keys.dropLast ++ memberSeg keys.getLast!

The method builds the path string that locates a queried key within a JSON
document, given the already-compiled path ``lhsPath`` to the enclosing document
and the non-empty list ``keys`` reaching the queried key. The load-bearing
``ensures`` clause is a concatenation of THREE independent, fully-grounded pure
functions of the method's own inputs (the ``axioms`` region is empty — no opaque
answer key):

  * ``lhsPath``                          — the enclosing-document prefix, echoed
                                           verbatim;
  * ``compilePrefix keys.dropLast``      — the INTERIOR keys, each compiled by the
                                           document's general rule (a numeric key
                                           addresses an array element ``[n]``,
                                           everything else an object member
                                           ``."k"``);
  * ``memberSeg keys.getLast!``          — the QUERIED (final) key, located BY
                                           NAME — as an object member ``."k"`` —
                                           regardless of its spelling (so a
                                           digit-only final key becomes ``."123"``
                                           and NOT the array step ``[123]``).

The interior/final split is the whole point: the general rule (``keySeg`` /
``compilePrefix``) still routes a numeric interior key to an array position, but
the final key is ALWAYS an object member. Every one of these three sub-images is
independently attackable, and the two input binders (``lhsPath``, ``keys``) are
both varied by the reject witnesses.

ADVERSARIAL READ of the classes (mirrors the nagini sibling; see the footer for
the case-by-case accounting):
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The sibling's MANDATORY
    frame-mutation rival keeps the gold body then writes through the read-only
    key input, which there carries only a fractional heap permission, and is
    rejected for INSUFFICIENT PERMISSION. Lean and Velvet are referentially
    transparent: every parameter is an immutable value, this bundle declares no
    ``mut`` binder on ``lhsPath`` or ``keys``, there is no heap and no aliasing.
    There is no read-only input to overwrite and no permission system to trip, so
    the class is vacuous. No substitute is fabricated (per the porting map, this
    class is legitimately dropped here rather than replaced); the sibling's
    "inputs are not mutated" obligation is structurally guaranteed by the ABSENCE
    of ``mut``.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is pinned to concrete ``def``s of the method's OWN inputs
    (``compilePrefix`` / ``keySeg`` / ``arraySeg`` / ``canonicalDigits`` /
    ``memberSeg``, all fully unfolded), NOT an opaque marker. There is no wrong
    constant an impl could echo: any constant-returning impl fails the grounded
    equality at once. The honest cheapest-reshape positive controls (``pos-*``)
    stand in.
  * CONTROL-FLOW-EFFECT — N/A. The method computes a pure path string; there is
    no raise / early-return / side-effect path the value abstraction misses. The
    only observable is the returned sequence, pinned in full by the equality
    clause.
  * PARTIAL-DOMAIN / VALUE — heavily exercised. The pre-patch array-element form
    (the F2P discriminator), the interior-vs-final routing, the by-name quoting
    glyph, and the off-by-one truncations all become rivals correct on PART of
    the domain and wrong on the interesting sub-domain, each refuted at a distinct
    concrete point.

WITNESS MECHANICS on this carrier. The spec here is a ``method`` CONTRACT, not a
bare predicate, so a witness reaches it through Velvet's own tester machinery:
``compileRhsPathTester <lhsPath> <keys> = false`` says the extracted program's
result violates the method's postcondition at that concrete input. It is checked
in a file whose ``prove_correct`` block has been stripped, so no tactic script
can mask the verdict. Every witness input satisfies both preconditions
(``keys ≠ []`` and ``keys.all isSimpleKey`` — every key is a non-empty ASCII
alphanumeric run), so the precondition decides ``true`` and the tester reduces to
the postcondition check; all inputs are concrete ``List Char`` / ``List (List
Char)`` literals, so each tester ``decide``s. No ``sorry`` / ``admit`` /
``native_decide`` / ``axiom``. Both halves were checked out-of-band with
``scripts/lean_verify.sh``: every witness ELABORATES against its rival (exit 0)
and FAILS against the frozen solution (``decide proved ... is false``).
"""
from pathlib import Path

INSTANCE = "django__django-15503"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The whole executable body: split the key list into
# ---- the interior keys and the queried (final) key, compile the interior keys
# ---- by the general rule, locate the final key by name, and concatenate onto
# ---- the enclosing-document prefix. Lies wholly inside the one impl region and
# ---- is unique in Solution.lean (both facts asserted at load by _swap).
_IMPL = (
    "    let prefixKeys := keys.dropLast\n"
    "    let finalKey   := keys.getLast!\n"
    "    let prefixPath := compilePrefix prefixKeys\n"
    "    let finalSeg   := memberSeg finalKey\n"
    "    return lhsPath ++ prefixPath ++ finalSeg\n"
)

# ---- proof-body anchor. A `prove_correct` tactic body is elided from the
# ---- consumer spec view, so a reshape / an in-region assert may retune the
# ---- tactic script without touching the spec or dropping the obligation.
# ---- Unique in the file.
_PROOF = "prove_correct compileRhsPath by loom_solve"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for reshapes / asserts)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. Reaches the method contract through Velvet's tester
# ---- machinery; checked in a file whose `prove_correct` block is stripped.
_TESTER = (
    "extract_program_for compileRhsPath\n"
    "prove_precondition_decidable_for compileRhsPath\n"
    "prove_postcondition_decidable_for compileRhsPath\n"
    "derive_tester_for compileRhsPath\n\n"
)


def _witness(call):
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the obligation and the byte-identical
    # theorem statement; only the executable surface moves.
    # =====================================================================
    {
        "id": "pos-return-spec-directly",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the let-bind skeleton and return the modeled path
        # directly. Observationally identical (the skeleton's result IS the
        # modeled concatenation), so the post-image holds definitionally and the
        # frozen `loom_solve` discharges it unchanged.
        "module": _impl(
            "    return lhsPath ++ compilePrefix keys.dropLast "
            "++ memberSeg keys.getLast!\n"),
        "rationale": "returning the modeled path directly satisfies "
                     "`out = lhsPath ++ compilePrefix keys.dropLast ++ memberSeg "
                     "keys.getLast!` definitionally, so a correct bind-free reshape "
                     "must verify (else SPEC-TOO-STRONG on the let-bind form). This "
                     "is the honest cheapest impl: no echo shortcut exists for the "
                     "grounded equality, so the cheapest faithful impl still "
                     "assembles the interior segments and the by-name final "
                     "segment.",
    },
    {
        "id": "pos-final-first-reassoc",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the final segment BEFORE the interior prefix and
        # re-associate the concatenation ((lhsPath ++ prefix) ++ final). `++` is
        # associative and the bind order is irrelevant, so the same string is
        # produced on every input; the frozen `loom_solve` discharges it.
        "module": _impl(
            "    let finalSeg   := memberSeg keys.getLast!\n"
            "    let prefixPath := compilePrefix keys.dropLast\n"
            "    return (lhsPath ++ prefixPath) ++ finalSeg\n"),
        "rationale": "reordering the binds and re-associating the concatenation "
                     "computes the SAME path on every input (`++` is associative), "
                     "so `out = lhsPath ++ compilePrefix keys.dropLast ++ memberSeg "
                     "keys.getLast!` still discharges; a correct reshape must verify "
                     "else SPEC-TOO-STRONG on the bind order / association.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries a `require` (keys ≠ [] AND every key
    # simple), which is trivially satisfiable for every F2P-shaped numeric key,
    # so the sibling's "a normal input satisfies the precondition" reading is
    # not where the risk sits. It is RE-AIMED at the residual admissibility risk
    # on this surface: that the post-image is DEGENERATE at the interesting point
    # — a spec no impl distinguishes reads exactly like one every impl meets.
    # This case discharges an in-region `assert` pinning that the F2P-shaped
    # numeric key "123" (a) is in the modeled domain (`isSimpleKey`), (b) as the
    # FINAL/queried key renders BY NAME (`memberSeg "123" = ."123"`), and (c) by
    # the GENERAL interior rule would instead render as the array step
    # (`keySeg "123" = [123]`) — so the interior-vs-final split is genuinely
    # non-degenerate. The surrounding impl is kept verbatim so the method's own
    # obligation still discharges; the assert is live (a false claim leaves an
    # unsolved goal). The nagini sibling's `admiss-numeric-key` is preserved in
    # spirit: same F2P-shaped key "123", same length/shape reasoning, re-aimed
    # from a permission-establishment probe to a non-degeneracy probe.
    # =====================================================================
    {
        "id": "admiss-numeric-final-by-name",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    let prefixKeys := keys.dropLast\n"
            "    let finalKey   := keys.getLast!\n"
            "    let prefixPath := compilePrefix prefixKeys\n"
            "    let finalSeg   := memberSeg finalKey\n"
            "    assert (with_name_prefix `assert\n"
            "      (isSimpleKey ['1','2','3'] = true ∧\n"
            "       memberSeg ['1','2','3'] = ['.','\"','1','2','3','\"'] ∧\n"
            "       keySeg ['1','2','3'] = ['[','1','2','3',']']))\n"
            "    return lhsPath ++ prefixPath ++ finalSeg\n",
            "prove_correct compileRhsPath by loom_solve\n"
            "  <;> simp_all [isSimpleKey, isSimpleChar, memberSeg, keySeg, "
            "isNumericKey, arraySeg, canonicalDigits, stripZeros]"),
        "rationale": "the F2P-shaped numeric key \"123\" is in the modeled domain "
                     "(`isSimpleKey` holds), and the post-image is non-degenerate at "
                     "it: as the queried final key it renders BY NAME "
                     "(`memberSeg \"123\" = .\"123\"`), whereas the general interior "
                     "rule would render the array step (`keySeg \"123\" = [123]`). "
                     "The in-region assert must discharge (else the interior/final "
                     "split is degenerate / PRECOND-TOO-STRONG); the impl is kept "
                     "verbatim so the ensures clause still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P (test_has_key_number / test_has_keys,
    # which exercise numeric object keys "123"/"456"/"999"/"789"/"777"/"000").
    # Each rival keeps the frozen `prove_correct` block (which no longer closes
    # for the reshaped impl); the witness is what attributes the rejection to the
    # SPEC.
    # =====================================================================
    {
        "id": "prepatch-array-index",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch behaviour: compile the queried (final) key by the SAME
        # general array-aware rule as the interior keys, so a digit-only final
        # key becomes the array step `[n]` instead of the object member `."n"`.
        "module": _impl(
            "    let wholePath := compilePrefix keys\n"
            "    return lhsPath ++ wholePath\n"),
        "refinement": "this IS the pre-patch form: the whole key list — including "
                      "the queried key — is compiled by the general array-aware "
                      "rule, so a digit-only queried key is addressed as an array "
                      "position (e.g. `[123]`, and a leading-zero key even loses its "
                      "zeros, `[0]`) rather than the object member `.\"123\"`. This "
                      "is the exact F2P discriminator: test_has_key_number asserts a "
                      "numeric object key \"123\"/\"000\" is found via the "
                      "object-member path, NOT the array-index path. A patch keeping "
                      "the array form does NOT resolve.",
        "rationale": "REJECT from the ensures' `memberSeg keys.getLast!` sub-image: "
                     "on a digit-only final key the general rule yields "
                     "`arraySeg`/`[n]` where the post-image demands `memberSeg`/"
                     "`.\"n\"`. Refuted at the single numeric queried key \"123\" "
                     "(`keys = [['1','2','3']]`, empty `lhsPath`), the F2P shape.",
        "witness": _witness("compileRhsPathTester [] [['1','2','3']]"),
    },
    {
        "id": "final-array-interior-ok",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the INTERIOR sub-image specifically. The final key is compiled
        # correctly by name, but the interior keys are ALSO forced to object
        # members (memberSeg) instead of the general array-aware rule — so a
        # numeric INTERIOR key is wrongly `."0"` where the document path needs
        # the array step `[0]`. Correct final handling; wrong interior routing.
        "module": _impl(
            "    let prefixPath := (keys.dropLast).flatMap (fun k => memberSeg k)\n"
            "    let finalSeg   := memberSeg keys.getLast!\n"
            "    return lhsPath ++ prefixPath ++ finalSeg\n"),
        "refinement": "a counterpart that located an INTERIOR numeric key by name "
                      "instead of by array position would build the wrong document "
                      "path for a nested numeric container — the interior keys keep "
                      "the document's general (array-aware) rule; only the queried "
                      "final key changes to by-name. A nested lookup through a "
                      "numeric interior key (e.g. an array index) would address the "
                      "wrong element, so the membership SQL tests the wrong path and "
                      "the deep-lookup F2P shapes would fail. It would NOT resolve.",
        "rationale": "REJECT from the ensures' `compilePrefix keys.dropLast` "
                     "sub-image: `compilePrefix` routes a numeric interior key "
                     "through `arraySeg` (`[n]`), but this rival forces every "
                     "interior key through `memberSeg` (`.\"n\"`). Refuted at a "
                     "two-key list with a numeric INTERIOR key `[['0'],['7','8','9']]`"
                     " (varying the `keys` LENGTH — the only multi-key witness).",
        "witness": _witness("compileRhsPathTester [] [['0'],['7','8','9']]"),
    },
    {
        "id": "wrong-quote-glyph",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE-LEVEL mask: wrap the final key in single quotes instead of the
        # JSON double quote. Correct length, correct prefix, correct key
        # characters between the quotes — only the quote glyph is wrong.
        "module": _impl(
            "    let prefixKeys := keys.dropLast\n"
            "    let finalKey   := keys.getLast!\n"
            "    let prefixPath := compilePrefix prefixKeys\n"
            "    let finalSeg   := '.' :: '\\'' :: finalKey ++ ['\\'']\n"
            "    return lhsPath ++ prefixPath ++ finalSeg\n"),
        "refinement": "a JSON string is delimited by DOUBLE quotes; a path step "
                      "wrapping the queried key in single quotes is not the "
                      "membership-operator syntax the database expects, so the key "
                      "would not match and the F2P (test_has_key_number / "
                      "test_has_keys) would fail. A patch emitting single quotes "
                      "does NOT resolve.",
        "rationale": "REJECT from the ensures' `memberSeg keys.getLast!` sub-image: "
                     "`memberSeg` pins the double-quote glyph (`.\"k\"`); a single "
                     "quote makes the delimiter code point wrong at both quote "
                     "positions. Refuted at an alphabetic queried key "
                     "`[['a']]` (empty `lhsPath`), so the glyph is attacked "
                     "independent of the numeric-routing rivals.",
        "witness": _witness("compileRhsPathTester [] [['a']]"),
    },
    {
        "id": "drop-last-key-char",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN off-by-one: render the queried key one character short
        # (drop its final character). Correct prefix, correct quotes, correct
        # all-but-last of the key; diverges only on the last key character and
        # the total length. Correct on the empty-key sub-domain (excluded by the
        # precondition), wrong whenever the final key has ≥ 2 characters.
        "module": _impl(
            "    let prefixKeys := keys.dropLast\n"
            "    let finalKey   := keys.getLast!\n"
            "    let prefixPath := compilePrefix prefixKeys\n"
            "    let finalSeg   := memberSeg finalKey.dropLast\n"
            "    return lhsPath ++ prefixPath ++ finalSeg\n"),
        "refinement": "rendering the queried key one character short emits a path "
                      "step for a DIFFERENT (truncated) key, e.g. \"ab\" -> "
                      "`.\"a\"`. The membership SQL would test the wrong key and the "
                      "F2P would not find the intended key. A patch that truncates "
                      "the queried key does NOT resolve.",
        "rationale": "REJECT from the ensures' `memberSeg keys.getLast!` sub-image: "
                     "the appended key is `finalKey.dropLast`, not `finalKey`, so "
                     "the element-wise pin (and the length) fail whenever the "
                     "queried key has ≥ 2 characters. Refuted at a two-character "
                     "queried key `[['a','b']]` — a point where prefix, quotes and "
                     "all-but-last agree but the last character and length diverge.",
        "witness": _witness("compileRhsPathTester [] [['a','b']]"),
    },
    {
        "id": "skip-first-key-char",
        "kind": "uniqueness",
        "expect": "reject",
        # Symmetric off-by-one: drop the FIRST character of the queried key.
        # Correct prefix and quotes; wrong whenever the final key is non-empty
        # (which the precondition guarantees).
        "module": _impl(
            "    let prefixKeys := keys.dropLast\n"
            "    let finalKey   := keys.getLast!\n"
            "    let prefixPath := compilePrefix prefixKeys\n"
            "    let finalSeg   := memberSeg (finalKey.drop 1)\n"
            "    return lhsPath ++ prefixPath ++ finalSeg\n"),
        "refinement": "dropping the first character of the queried key emits a path "
                      "step for a DIFFERENT key, e.g. \"1111\" -> `.\"111\"`. The "
                      "membership SQL tests the wrong key and the F2P (the numeric "
                      "key \"1111\"/\"123\" would not be found). A patch that drops "
                      "the first character does NOT resolve.",
        "rationale": "REJECT from the ensures' `memberSeg keys.getLast!` sub-image: "
                     "the appended key is `finalKey.drop 1`, missing the first "
                     "character, so the element-wise pin fails at index 0. Refuted "
                     "at the numeric queried key `[['1','1','1','1']]` (the problem "
                     "statement's \"1111\"), the symmetric off-by-one point.",
        "witness": _witness("compileRhsPathTester [] [['1','1','1','1']]"),
    },
    {
        "id": "drop-lhs-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the `lhsPath` sub-image: omit the enclosing-document prefix
        # entirely. Correct interior + final compilation; the result is missing
        # the already-compiled path to the enclosing document. Correct only when
        # lhsPath is empty; wrong whenever it is non-empty.
        "module": _impl(
            "    let prefixKeys := keys.dropLast\n"
            "    let finalKey   := keys.getLast!\n"
            "    let prefixPath := compilePrefix prefixKeys\n"
            "    let finalSeg   := memberSeg finalKey\n"
            "    return prefixPath ++ finalSeg\n"),
        "refinement": "a counterpart that dropped the enclosing-document prefix "
                      "would build a rootless path that no longer descends through "
                      "the left-hand-side document — the membership test would run "
                      "against the wrong (top-level) location and fail for any "
                      "lookup nested under a key transform. A patch that omits the "
                      "left-hand path does NOT resolve.",
        "rationale": "REJECT from the ensures' leading `lhsPath ++ ...` sub-image: "
                     "the post-image prepends the enclosing-document prefix, which "
                     "this rival drops. Refuted at a non-empty `lhsPath = ['x']` "
                     "(the ONLY reject witness that moves the `lhsPath` binder off "
                     "the empty value), with an ordinary queried key `[['a']]`.",
        "witness": _witness("compileRhsPathTester ['x'] [['a']]"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 1 mandatory frame-mutation, 4 uniqueness rivals)
# and 0 AXIOM_TESTS. The sibling models a SINGLE function
# `compile_final_key_segment(key)` — the final key's segment ALONE — over a
# read-only `List[int]` carrying a fractional heap permission, with the segment
# built by a verified `while` loop under gold invariants. THIS bundle models the
# WHOLE right-hand-side path construction `compileRhsPath(lhsPath, keys)`: it
# carries the same final-key by-name behaviour (`memberSeg keys.getLast!`) AND
# the surrounding interior-key compilation (`compilePrefix keys.dropLast`) and
# the enclosing-document prefix (`lhsPath`) that the sibling's narrower carrier
# does not model. The value surface carries across intact and is WIDENED; the
# permission surface and the loop do not exist here.
#
#   sibling case            -> here                              disposition
#   -----------------------------------------------------------------------
#   pos-prefix-reshape      -> pos-final-first-reassoc           PORTED (reshaped)
#   honest-cheapest         -> pos-return-spec-directly          PORTED (re-aimed)
#   admiss-numeric-key      -> admiss-numeric-final-by-name      RE-AIMED
#   frame-mutate-key        -> (none)                            VACUOUS
#   prepatch-array-index    -> prepatch-array-index              PORTED
#   drop-last-char          -> drop-last-key-char                PORTED
#   skip-first-char         -> skip-first-key-char               PORTED
#   wrong-quote             -> wrong-quote-glyph                 PORTED
#   (no sibling)            -> final-array-interior-ok           ADDED (interior clause)
#   (no sibling)            -> drop-lhs-prefix                   ADDED (lhsPath clause)
#
# 6 ported, 1 re-aimed, 1 vacuous; 2 clause-coverage rivals added.
#
# VACUOUS (frame-mutate-key): the sibling's MANDATORY frame-mutation rival keeps
#   the gold body verbatim then writes through the read-only key input, held only
#   at half heap permission, and must be rejected for INSUFFICIENT PERMISSION.
#   This backend is referentially transparent: every parameter is an immutable
#   value, the method declares no `mut` binder on `lhsPath` or `keys`, there is no
#   heap and no aliasing. There is no read-only input to overwrite and no
#   permission system to trip, so the class is vacuous. No substitute is
#   fabricated (per the porting map, dropped rather than replaced); the "inputs
#   not mutated" obligation is discharged by the ABSENCE of `mut`.
# RE-AIMED (admissibility): the sibling self-calls `compile_final_key_segment`
#   on the numeric key "123" and asserts the precondition is establishable and the
#   result length is len(key)+3. The precondition here (`keys ≠ [] AND keys.all
#   isSimpleKey`) is trivially satisfiable for every F2P-shaped numeric key, so
#   that reading is not where the risk sits. It is re-aimed at the residual
#   total-domain risk — that the interior-vs-final split is DEGENERATE at the
#   interesting point — via an in-region assert that "123" is in-domain, renders
#   BY NAME as the final key (`memberSeg "123" = ."123"`), and would render as the
#   ARRAY step under the general rule (`keySeg "123" = [123]`). Same F2P-shaped
#   key, re-aimed from permission-establishment to non-degeneracy.
# PORTED-RESHAPED (pos-prefix-reshape): the sibling builds the '.\"' prefix by two
#   one-element appends keeping the gold loop / invariants. This backend's frozen
#   impl is loop-free, so the exact append-reshape does not exist. The reshape
#   SPIRIT — structurally different, behaviourally identical — is carried by
#   pos-final-first-reassoc (reorder the binds, re-associate `++`). Same string on
#   every input; the reproof is the frozen `loom_solve`.
# PORTED-REAIMED (honest-cheapest): the sibling's honest cheapest control IS the
#   gold body (grounded oracle has no echo shortcut). Here the cheapest faithful
#   impl is the bind-free direct return (pos-return-spec-directly): it still
#   assembles the interior segments and the by-name final segment, so it verifies
#   definitionally — the same "no echo shortcut for a grounded oracle" argument.
# ADDED (2): the sibling's narrower carrier (final segment ALONE) cannot express
#   two clauses this wider carrier introduces, so each gets its own rival:
#     final-array-interior-ok — attacks `compilePrefix keys.dropLast` (a numeric
#       INTERIOR key must keep the general array-aware rule; only the final key is
#       by-name). This is the interior/final SPLIT the fix turns on, invisible to
#       a final-key-only model.
#     drop-lhs-prefix — attacks the leading `lhsPath ++ ...` (the enclosing-
#       document prefix must be prepended). The sibling has no lhs input at all.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses (pts = 6 distinct input points):
#   The three independent top-level sub-images of the sole ensures are each
#   attacked:
#     lhsPath                     -> drop-lhs-prefix
#     compilePrefix keys.dropLast -> final-array-interior-ok
#     memberSeg keys.getLast!     -> prepatch-array-index / wrong-quote-glyph /
#                                    drop-last-key-char / skip-first-key-char
#   The two input binders are both varied:
#     lhsPath : []  (5 rivals),  ['x']  (drop-lhs-prefix)          -> both empty and
#               non-empty (drop-lhs-prefix is the only rival that could mishandle a
#               non-empty prefix, and it is refuted exactly there).
#     keys    : [['1','2','3']], [['a']], [['a','b']], [['1','1','1','1']],
#               [['0'],['7','8','9']], [['a']]                     -> single- and
#               MULTI-key lists (length varied by final-array-interior-ok), numeric
#               and alphabetic keys, 1- to 4-character keys.
#   Six distinct witness points, so pts = 6; no binder is held constant across all
#   rivals, and the two near-misses (drop-last / skip-first) sit at their own
#   multi-character points distinct from the exact-value rivals.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# consumed `axiom`, and its two deep models (`compilePrefix` == compile_json_path,
# `memberSeg` == '.%s'%json.dumps) are A-references validated there. This gate
# ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
