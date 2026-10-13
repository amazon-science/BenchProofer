"""properties.py — G-PBT falsification battery for django__django-16139 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct buildRelativeLink`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a single key value, returning a
per-character URL sequence, ``List Char``):

  buildRelativeLink (key : Nat) return (link : List Char)
    ensures link = relativeLink key            -- THE load-bearing (only) clause

``relativeLink`` is a fully unfolded ``def`` in the ``pure`` region — there is NO
opaque answer key to echo:

  relativeLink key = "../../".toList ++ (toString key).toList ++ "/password/".toList

so the single ``ensures`` clause pins THREE independent structural parts of the
produced relative reference over the sole input binder ``key``:

  * ASCENT PREFIX: the reference ascends exactly two levels ("../../"), so the
    resolved target does not depend on the identifier the current page was
    addressed by;
  * KEYED MIDDLE: the descending segment is the record's own key rendered in its
    usual decimal text form (``toString key``) — the reference is KEYED BY the
    key, not by any other identifier and not by a constant;
  * TRAILING SEGMENT: the reference descends into the record's password
    sub-page ("/password/"), not some other action page.

``relativeLink`` is GROUNDED in the input (a total function of ``key``); the
``axioms`` region is empty (the transformation is modeled DEEPLY — decimal
rendering as ``toString`` and segment concatenation as ``++``), so there is no
answer key to echo and the ungrounded-oracle probe is replaced by two honest
positive controls. The sole INPUT BINDER is ``key``.

THE CARRIER IS FULLY TRANSPARENT. ``relativeLink`` computes on ``Char`` literals
and ``toString`` of a concrete ``Nat``, so a witness reaches the method's
postcondition through Velvet's own tester machinery
(``extract_program_for buildRelativeLink`` + the decidability lemmas +
``derive_tester_for buildRelativeLink`` give ``buildRelativeLinkTester key``,
which is ``false`` exactly when the extracted program violates the ``ensures``
clause) and states ``buildRelativeLinkTester k = false`` at a concrete ``k``,
closed by ``decide`` on the residual literal (no opaque leaf, no carrier
conditioning, so no witness binds a hypothesis and there is no joint-
satisfiability obligation). There is no ``require`` clause, so every ``k`` is in
the precondition domain and the tester reaches the postcondition rather than
vacuously passing. Both halves of every witness were checked out-of-band with
``scripts/lean_verify.sh`` (rival elaborates EXIT 0; gold FAILS with
``decide proved … is false`` EXIT 1) for every reject case.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries this as a
    MANDATORY rival (write to the read-only ``prefix`` held at
    ``Acc(list_pred(prefix), 1/2)``) because a store needs full permission. Lean
    and Velvet are referentially transparent: the sole input ``key`` is an
    immutable ``Nat`` value, this bundle declares NO ``mut`` binder over any
    input, and there is no heap and no aliasing — so there is no read-only input
    to overwrite and no substitute probe to build. Not fabricated (per the
    porting map: this class is vacuous on Lean/Velvet).
  * SOUNDNESS positives — APPLY: a structurally different but faithful impl must
    still verify, else SPEC-TOO-STRONG.
  * ADMISSIBILITY — RE-AIMED. The nagini self-call establishes that the
    fractional-permission precondition ADMITS an F2P-shaped input. This bundle
    carries NO ``require`` clause (the render is total), so that probe is
    degenerate; it is re-aimed at the residual admissibility risk on a
    transparent carrier — that the post-image is DEGENERATE (does not actually
    demand the two-levels-up, key-indexed, password sub-page form). An in-region
    assert pins the post-image at an F2P-shaped key AND that it differs from the
    pre-patch one-level reference; the impl is kept verbatim so the method's own
    obligation still discharges.
  * PARTIAL-DOMAIN / VALUE rivals — APPLY; the heart of the port. The nagini
    ``resolve``-over-list model (a fold over ``prefix + [token] + [current_action]``
    distinguishing token vs pk) NARROWS here to the produced URL string: the
    token / current_action / pk list positions collapse into the three structural
    parts of ``relativeLink``. Each nagini rival re-expresses directly onto one
    part — the ascent prefix, the keyed middle, or the trailing segment.

AXIOM lane: EMPTY (``meta.json`` declares no consumed ``axiom``; the
transformation is modeled DEEPLY — G-AX is skipped for this bundle — and this
gate ignores ``AXIOM_TESTS`` regardless).
"""
from pathlib import Path

INSTANCE = "django__django-16139"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside a region the spec view elides (the impl body
# between -- impl-start / -- impl-end, or the prove_correct tactic body) and is
# unique in Solution.lean; both facts are asserted at load by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct buildRelativeLink
# statement byte-identical.
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method (the single result-construction line).
_IMPL = (
    '    return "../../".toList ++ (toString key).toList ++ "/password/".toList'
)
assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"

# The FULL frozen proof body (unique in the file, elided from the spec view). A
# case that adds an in-region assert retunes this to also close the ground assert
# goal; that is a proof reshape, not a spec change.
_PROOF = "prove_correct buildRelativeLink by\n  loom_solve"
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- WITNESS machinery. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `buildRelativeLinkTester key = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped, so no tactic script
# ---- can mask the verdict. There is no `require` clause, so every key is in the
# ---- precondition domain and the tester reaches the postcondition rather than
# ---- vacuously passing on an excluded input.
_TESTER = (
    "extract_program_for buildRelativeLink\n"
    "prove_precondition_decidable_for buildRelativeLink\n"
    "prove_postcondition_decidable_for buildRelativeLink\n"
    "derive_tester_for buildRelativeLink\n\n"
)


def _witness(key_expr: str) -> str:
    return _TESTER + (
        f"example : buildRelativeLinkTester {key_expr} = false := by\n  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — the honest cheapest reshape, which MUST
    # verify (else SPEC-TOO-STRONG). Bind each of the three segments to a typed
    # local, then assemble the reference by concatenation. The returned value is
    # identical, so `link = relativeLink key` still discharges under the frozen
    # `loom_solve`. This is a local-binding reshape (directive-5 safe): the
    # read-only `key` is not mutated. Ports the nagini pos-concat ARGUMENT
    # (assemble the reference from locals instead of a single literal).
    # =====================================================================
    {
        "id": "pos-bind-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(
            '    let up := "../../".toList\n'
            '    let mid := (toString key).toList\n'
            '    let tail := "/password/".toList\n'
            "    return up ++ mid ++ tail"),
        "rationale": "PASS SOURCE = the sole clause `link = relativeLink key`. "
                     "Binding the ascent prefix, the keyed middle, and the "
                     "trailing segment to typed locals before concatenating leaves "
                     "the returned value identical, so `link = relativeLink key` "
                     "still holds and the frozen `loom_solve` closes the "
                     "byte-identical obligation. A faithful correct reshape MUST "
                     "verify, else the clause is over-fit to the exact impl FORM "
                     "=> SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — a second honest correct shape: a different
    # ASSOCIATION of the same concatenation (fold the ascent prefix and the keyed
    # middle into one local, then append the trailing segment). `++` is
    # associative, so the produced value is identical and the frozen proof still
    # closes with no retune. Confirms the clause is not over-fit to the exact
    # bracketing of the three-way `++`.
    # =====================================================================
    {
        "id": "pos-regroup",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(
            '    let prefixSegs := "../../".toList ++ (toString key).toList\n'
            '    return prefixSegs ++ "/password/".toList'),
        "rationale": "PASS SOURCE = the sole clause `link = relativeLink key`. "
                     "Reassociating the three-way concatenation (fold the ascent "
                     "prefix and the keyed middle together, then append the "
                     "trailing segment) yields the identical sequence by "
                     "associativity of `++`, so `link = relativeLink key` still "
                     "discharges under the frozen proof. A second honest shape "
                     "verifying confirms the clause is not over-fit to one "
                     "bracketing; else SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED. The nagini sibling self-calls on an F2P-shaped
    # input to show the fractional-permission precondition ADMITS it. This bundle
    # carries NO `require` clause (the render is total), so that probe is
    # degenerate. Re-aimed at the residual admissibility risk on a transparent
    # carrier: that the post-image is DEGENERATE — that it does not actually
    # demand the two-levels-up, key-indexed, password sub-page reference (distinct
    # from the pre-patch one-level reference). An in-region assert pins the
    # post-image at an F2P-shaped key AND that it differs from the pre-patch
    # reference; the impl is kept verbatim so the method's own obligation still
    # discharges; the proof gains a `decide` arm to close the ground assert. The
    # assert is LIVE — a false claim leaves an unsolved `decide` goal (verified
    # out of band).
    # =====================================================================
    {
        "id": "admiss-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL,
                '    assert (with_name_prefix `admiss\n'
                '      (relativeLink 5 = "../../5/password/".toList\n'
                '       ∧ relativeLink 5 ≠ "../password/".toList))\n'
                + _IMPL),
            _PROOF,
            "prove_correct buildRelativeLink by\n  loom_solve <;> decide"),
        "rationale": "PASS SOURCE = the post-image is non-degenerate at an "
                     "F2P-shaped key. The in-region assert pins `relativeLink 5` to "
                     "the two-levels-up, key-indexed, password sub-page reference "
                     "('../../5/password/') AND to something OTHER than the "
                     "pre-patch one-level reference ('../password/') — so the spec "
                     "genuinely demands the ascent-prefixed, keyed reference, not a "
                     "degenerate or pre-patch form. The assert must discharge (else "
                     "the obligation is degenerate) and the frozen body keeps "
                     "`link = relativeLink key` intact, so the module verifies. "
                     "Since the render is total there is no precondition to "
                     "over-strengthen; this defends against a hollow post-image.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a straight-line closed form with a
    # machine-checked refutation witness at a concrete key, and the refinement
    # argument for why its faithful real counterpart would NOT resolve the
    # failing test.
    # =====================================================================

    # ---- ASCENT-PREFIX clause (THE pre-patch bug): the fixed one-level
    # ---- reference that omits the key entirely. ----
    {
        "id": "weak-prepatch-onelevel",
        "kind": "uniqueness",
        "expect": "reject",
        # The verbatim pre-patch reference: ascends ONE level and carries no key.
        "module": _with_impl('    return "../password/".toList'),
        "refinement": "this is the verbatim pre-patch reference — a fixed "
                      "one-level-up link that carries no key at all. When the "
                      "record's change page is reached under an identifier other "
                      "than its key (the to_field access the failing test "
                      "exercises), resolving this one-level reference lands on a "
                      "page keyed by that OTHER identifier, not the record's own "
                      "key, so the resolved link 404s. A faithful patch that left "
                      "the reference at the one-level fixed string still resolves "
                      "to the wrong page for that access, so it would NOT resolve "
                      "— it is the original bug.",
        "rationale": "REJECT from `link = relativeLink key` (ASCENT-PREFIX part): "
                     "the impl returns the one-level reference '../password/' "
                     "regardless of key, while the post-image demands the "
                     "two-levels-up, key-indexed reference; they differ at every "
                     "key. Refuted at key 5 — `buildRelativeLinkTester 5 = false` "
                     "elaborates against the rival and fails against gold.",
        "witness": _witness("5"),
    },

    # ---- ASCENT-PREFIX clause: ascend only one level (keep the key). ----
    {
        "id": "weak-underpop",
        "kind": "uniqueness",
        "expect": "reject",
        # One '..' instead of two: the key is present and the trailing segment is
        # right, but the reference ascends only one level, so it nests UNDER the
        # current-page identifier instead of replacing it.
        "module": _with_impl(
            '    return "../".toList ++ (toString key).toList ++ "/password/".toList'),
        "refinement": "ascending only one level leaves the current page's own "
                      "addressing segment in the resolved path, so the reference "
                      "resolves to a page nested UNDER that identifier "
                      "(…/<accessed-as>/<key>/password/) rather than the record's "
                      "own password sub-page. That path is not a valid "
                      "password-change URL, so a faithful patch omitting one level "
                      "of ascent would NOT resolve the failing test.",
        "rationale": "REJECT from `link = relativeLink key` (ASCENT-PREFIX part): "
                     "the impl's leading segment is '../' where the post-image "
                     "demands '../../', so the returned sequence differs from "
                     "`relativeLink key` at every key. Refuted at key 7 — a "
                     "distinct input point from the other rivals.",
        "witness": _witness("7"),
    },

    # ---- ASCENT-PREFIX clause: ascend one level too many. ----
    {
        "id": "weak-overpop",
        "kind": "uniqueness",
        "expect": "reject",
        # Three '..' instead of two: over-ascends, so resolving the reference
        # drops a shared path segment above the record — the target is keyed
        # correctly but rooted one level too high.
        "module": _with_impl(
            '    return "../../../".toList ++ (toString key).toList ++ "/password/".toList'),
        "refinement": "ascending one level too many drops a shared path segment "
                      "above the record, so the reference resolves to a page "
                      "rooted one level too high (missing an intermediate segment) "
                      "— not the record's password sub-page. A faithful patch "
                      "over-ascending would resolve to a non-existent URL and so "
                      "would NOT resolve the failing test.",
        "rationale": "REJECT from `link = relativeLink key` (ASCENT-PREFIX part): "
                     "the impl's leading segment is '../../../' where the "
                     "post-image demands '../../', so the returned sequence differs "
                     "from `relativeLink key` at every key. Refuted at key 42 — a "
                     "multi-digit key, exercising the decimal render over more than "
                     "one code point.",
        "witness": _witness("42"),
    },

    # ---- TRAILING-SEGMENT clause: correct ascent and key, wrong action page. ----
    {
        "id": "weak-wrong-trailing",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct two-levels-up and key-indexed, but the trailing segment names a
        # different action page than the password sub-page.
        "module": _with_impl(
            '    return "../../".toList ++ (toString key).toList ++ "/change/".toList'),
        "refinement": "keeping the ascent and the key but naming a different "
                      "trailing action page points the help-text link at the wrong "
                      "sub-page (the record's change page, not its password "
                      "sub-page). The failing test asserts the resolved link equals "
                      "the record's password-change URL, so a faithful patch with "
                      "the wrong trailing segment would resolve to the wrong page "
                      "and NOT resolve.",
        "rationale": "REJECT from `link = relativeLink key` (TRAILING-SEGMENT "
                     "part): the impl's trailing segment is '/change/' where the "
                     "post-image demands '/password/', so the returned sequence "
                     "differs from `relativeLink key` at every key. Refuted at key "
                     "3 — a distinct input point from the other rivals.",
        "witness": _witness("3"),
    },

    # ---- KEYED-MIDDLE clause: correct shape, wrong key (constant). ----
    {
        "id": "weak-constant-key",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct ascent (two levels) and trailing segment, but the descending
        # segment is a CONSTANT rather than the record's own key — the port of the
        # nagini token-echo rival (right shape, keyed by the wrong identifier).
        # Correct only on the degenerate sub-domain key == 1; wrong everywhere
        # else. This is the ONLY rival that varies whether the middle segment
        # actually depends on the `key` binder.
        "module": _with_impl(
            '    return "../../".toList ++ "1".toList ++ "/password/".toList'),
        "refinement": "producing a reference with the correct ascent and trailing "
                      "segment but a CONSTANT descending segment keys the password "
                      "sub-page by a fixed identifier rather than the record's own "
                      "key — the same class of defect as keying by the identifier "
                      "the page was accessed through instead of the record's key. "
                      "It resolves to the right page only when the record's key "
                      "happens to equal that constant; for every other record it "
                      "resolves to a different record's password page, so a "
                      "faithful patch keying by anything other than the record's "
                      "own key would NOT resolve the failing test. This is the "
                      "precise key-vs-other-identifier hole the patch closes.",
        "rationale": "REJECT from `link = relativeLink key` (KEYED-MIDDLE part): "
                     "the impl's middle segment is the constant '1' where the "
                     "post-image demands `toString key`, so the returned sequence "
                     "differs from `relativeLink key` at every key != 1. Refuted at "
                     "key 9 (constant '1' != render '9') — the sole rival that "
                     "abuses the `key` binder, demonstrating the spec's dependence "
                     "on it. Correct only on the degenerate key == 1 sub-domain.",
        "witness": _witness("9"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 8 SPEC cases (1
# soundness positive, 1 admissibility, 1 mandatory frame-mutation rival, 5
# uniqueness value rivals) plus a 2-case AXIOM lane. The sibling contracts
# `build_action_reference` over a LIST carrier and specifies correctness via a
# `resolve` fold over `prefix + [token] + [current_action]` — a model rich enough
# to distinguish the access token from the record's pk. This velvet bundle models
# the SAME behaviour NARROWED to its purely-functional core: the produced relative
# reference `relativeLink key` as a `List Char` URL, a total function of the
# single input `key` (= self.instance.pk). The token / current_action / pk list
# positions of the nagini `resolve` model collapse into the three STRUCTURAL parts
# of the produced string (ascent prefix, keyed middle, trailing segment), so every
# nagini value rival re-expresses onto one of those parts.
#
#   sibling case            kind          -> here                   disposition
#   ---------------------------------------------------------------------------
#   pos-concat              soundness     -> pos-bind-local         PORTED
#   (—)                     soundness     -> pos-regroup            ADDED
#   admiss-f2p-shape        admissibility -> admiss-grounded        RE-AIMED
#   frame-prefix-write      uniqueness    -> (none)                 VACUOUS
#   w1-token-keyed          uniqueness    -> weak-prepatch-onelevel PORTED
#   w2-partial-pop          uniqueness    -> weak-underpop          PORTED
#   w3-over-pop             uniqueness    -> weak-overpop           PORTED
#   w4-wrong-action         uniqueness    -> weak-wrong-trailing    PORTED
#   w5-token-echo           uniqueness    -> weak-constant-key      PORTED (re-expr)
#   AXIOM_TESTS (2)         axiom         -> (none)                 DROPPED (G-AX)
#
# 5 ported, 1 re-expressed, 1 added, 1 re-aimed, 1 vacuous, 2 dropped
#   = 8 velvet SPEC cases (2 soundness, 1 admissibility, 5 uniqueness).
#
# PORTED (pos-concat -> pos-bind-local): the sibling assembles the reference from
#   typed locals + list concatenation instead of one 4-element literal; here the
#   three segments are bound to typed locals and concatenated. Same argument (a
#   faithful reshape must verify). Verified to build.
# ADDED (pos-regroup): a second honest correct shape that reassociates the
#   three-way `++`, confirming the clause is not over-fit to one bracketing. The
#   sibling ships one positive control; velvet's cheap `loom_solve` lets a second
#   honest shape defend the obligation from a different angle. Verified to build.
# RE-AIMED (admiss-f2p-shape -> admiss-grounded): the sibling asserts the
#   fractional-permission precondition (read-permission on prefix, the
#   non-negative-segments quantifier, the >=0 scalar guards) admits an F2P-shaped
#   input. This bundle carries NO `require` clause (the render is total), so that
#   probe is degenerate. Re-aimed at the residual risk on a transparent carrier —
#   a DEGENERATE post-image — via a live in-region assert pinning the post-image
#   at an F2P-shaped key AND that it differs from the pre-patch one-level
#   reference. Verified to build; the assert is live (a false claim leaves an
#   unsolved `decide` goal, verified out of band).
# VACUOUS (frame-prefix-write): the sibling carries this as MANDATORY because
#   `prefix` is held at Acc(list_pred(prefix), 1/2) and a rival can illegally
#   store into it. This backend is referentially transparent and this bundle
#   declares no `mut` binder — the sole input `key` is an immutable `Nat` value
#   with no heap footprint — so there is no read-only input to overwrite and no
#   substitute probe to build. Not fabricated (per the porting map: this class is
#   vacuous on Lean/Velvet).
# PORTED (w1..w4 -> the four structural rivals): w1-token-keyed is the verbatim
#   pre-patch one-level reference (weak-prepatch-onelevel); w2-partial-pop is
#   ascending only one level (weak-underpop); w3-over-pop is ascending one level
#   too many (weak-overpop); w4-wrong-action names the wrong trailing action page
#   (weak-wrong-trailing). Each re-expresses onto the corresponding structural
#   part of `relativeLink` and carries a machine-checked witness that ELABORATES
#   against the rival and FAILS against the frozen solution (two real builds per
#   case). The refinement arguments carry over: each faithful counterpart still
#   resolves to the wrong URL for the to_field access the failing test exercises.
# PORTED / RE-EXPRESSED (w5-token-echo -> weak-constant-key): the sibling's rival
#   keys the reference by the access token instead of the record's pk. On this
#   narrowed carrier there is no separate token binder — the model has only
#   `key` — so the "keyed by the wrong identifier" defect re-expresses as "keyed
#   by a constant instead of `toString key`" (correct shape, wrong middle
#   segment). This is the ONLY rival that abuses the `key` binder, so it is what
#   demonstrates the spec's dependence on it (a rival ignoring `key` would verify
#   were the middle not pinned to `toString key`).
# DROPPED (AXIOM_TESTS, 2): the sibling's axiom lane validates the `resolve` deep
#   model == urllib.parse.urljoin (soundness) and its reachable-domain containment.
#   This velvet bundle declares no consumed `axiom` (the transformation is modeled
#   deeply as `toString`/`++`, so G-AX is skipped per mapping.md), and this gate
#   ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The obligation has one input binder, `key : Nat`, and
#   one top-level clause, `link = relativeLink key`, with three independent
#   structural parts (ascent prefix, keyed middle, trailing segment). The five
#   reject witnesses probe five DISTINCT keys — 5, 7, 42, 3, 9 (pts=5) — so `key`
#   is varied (single- and multi-digit) and no two rivals are refuted at the same
#   point. Part coverage: the ascent prefix is attacked by weak-prepatch-onelevel
#   (one level, no key), weak-underpop (one level), and weak-overpop (three
#   levels); the keyed middle is attacked by weak-constant-key (constant instead
#   of `toString key`) — the only rival that varies whether the middle depends on
#   the `key` binder; the trailing segment is attacked by weak-wrong-trailing. The
#   two positive controls defend the whole obligation. Every structural part is
#   both defended and attacked.
# WITNESS DISCRIMINATION (verified during authoring with two real builds per
#   reject case): each witness ELABORATES against its rival (the extracted
#   program's tester is provably `false` at the probed key — EXIT 0) and FAILS
#   against the frozen solution (`decide proved … is false` — EXIT 1). No witness
#   binds a hypothesis (the carrier is fully transparent and there is no `require`
#   clause), so there is no joint-satisfiability obligation. No
#   `sorry`/`admit`/`native_decide`/`axiom` appears in any variant.
AXIOM_TESTS = []
