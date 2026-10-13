"""properties.py — G-PBT falsification battery for django__django-12193 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct computeContextAttrs`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; each is
checked by the real verifier. ``expect:"verify"`` passes iff (in scope AND
verifies); ``expect:"reject"`` passes iff (in scope AND does NOT verify AND its
refutation ``witness`` discriminates: the witness must ELABORATE against the
rival and FAIL against the frozen solution).

DEFENDED SURFACE. One contracted method over a mutable attribute mapping and a
read-only affirmative observation, deriving the mapping a checkbox-style control
hands to the shared base renderer for one rendering:

  computeContextAttrs (mut attrs : List (String × Bool)) (checked : Bool)
      return (effective : List (String × Bool))
    ensures attrs = attrsOld                                            -- (1)
    ensures effective = if checked then withChecked attrsOld else attrsOld  -- (2)

``attrs`` is the caller-owned attribute mapping; the SAME mapping value is reused
across the repeated renderings of a multi-element control, so the operation must
treat it as read-only state. ``checked`` is the observation of whether this
element's backing value makes the control affirmative. ``withChecked`` (a
concrete ``def`` in the ``pure`` region — the ``axioms`` region declares nothing)
installs the ``"checked" ↦ true`` entry into a mapping (overwrite if present,
append if absent). There is no ``require`` clause, so the admitted domain is
total: the post-image must hold for EVERY starting state.

TWO independent top-level clauses, each load-bearing:
  (1) ``attrs = attrsOld`` — the caller's mapping is read-only across the
      operation. This is the directive-5 frame clause: ``attrs`` is ``mut`` but
      is conceptually unchanged, so it is pinned exactly to its entry value. It
      is the #1 defended property: a body that writes the affirmative flag into
      the caller's own mapping fails here, which is precisely what lets a later
      element rendered from the same mapping start clean rather than inherit a
      flag from an earlier affirmative element.
  (2) ``effective = if checked then withChecked attrsOld else attrsOld`` — the
      onward mapping. On the affirmative sub-domain (``checked = true``) it is
      the caller's mapping with the affirmative entry recorded true; on the
      negative sub-domain (``checked = false``) it is the caller's mapping
      verbatim. This clause carries the full both-directions key/value pinning:
      the affirmative entry present-and-true when affirmative, and NO entry added
      when negative.

ADVERSARIAL READ of the sibling classes on this carrier:
  * FRAME-MUTATION — APPLIES, and PORTS to a real value attack (NOT vacuous).
    On the sibling the caller's mapping is held at a fractional heap permission
    (``Acc(dict_pred(attrs), 1/2)``) an impl cannot legally write, and the
    rejection comes from the permission system. Lean/Velvet are referentially
    transparent and have no such permission, BUT ``attrs`` is a ``mut`` binder
    here and clause (1) pins it unchanged, so a body that writes the affirmative
    flag into ``attrs`` and hands that same value on violates a genuine
    postcondition clause. The sibling's mandatory frame-mutation probe therefore
    re-expresses as ``weak-frame-write-attrs`` — the rejection SOURCE changes
    (postcondition clause (1), not a permission system), but the attack (the
    exact pre-change in-place write the fix removes) is the same. The sibling's
    second frame flavour (write-then-return-fresh) collapses onto it here: clause
    (1) catches ANY write to ``attrs`` regardless of what value is returned, so
    there is no permission-vs-freshness distinction to keep (see footer).
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is pinned to ``withChecked``, a
    total, fully-unfolded function of the method's OWN input ``attrs`` — there is
    no opaque answer key to echo (evaluating ``withChecked`` IS the correct
    answer), so there is no wrong echo to build. Honest cheapest-reshape positive
    controls (``pos-*``) stand in.
  * PARTIAL-DOMAIN / VALUE — APPLIES: a body right on one ``checked`` sub-domain
    but wrong on the other (always force the flag on; never force it on), plus
    value-level rivals (wrong flag value; a spurious extra entry; the affirmative
    entry APPENDED rather than installed, which is wrong only where the key is
    already present; and one UNRELATED entry's value clobbered while the
    affirmative entry is installed entirely correctly, which is wrong only where
    the caller's mapping has an entry besides the affirmative one). Each is
    refuted at a concrete point on the sub-domain where it goes wrong.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no
    loop and no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so
each reject rival reaches it through Velvet's own tester machinery:
``computeContextAttrsTester <attrs> <checked> = false`` says the extracted
program's observable (the mutated ``attrs`` and the returned ``effective``)
violates the method's postcondition at that concrete starting state. It is
checked in a file whose ``prove_correct`` block has been stripped, so no tactic
script can mask the verdict. There is no ``require`` clause, so the precondition
is ``True`` and decides trivially. All inputs are concrete ``List (String ×
Bool)`` / ``Bool`` literals, so each tester ``decide``s. Each witness binds
nothing (literal starting state), so there are no hypotheses to be inconsistent.
No ``sorry`` / ``admit`` / ``native_decide`` / ``axiom``.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the mapping
transformation is modeled directly as the pure ``withChecked`` and the frame is
pinned by clause (1) — there is no unchanged callee whose contract the proof
consumes; mapping.md §3). The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-12193"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the whole executable body (bind the onward mapping
# ---- from a SEPARATE value — the caller's mapping with the affirmative entry
# ---- recorded when affirmative, else the caller's mapping itself — and return
# ---- it). Lies wholly inside the single impl region and is unique in
# ---- Solution.lean; both facts asserted at load by _swap. Reshaped wholesale by
# ---- the rivals and the positive controls. ----
_GOLD_IMPL = (
    "    let effective := if checked then withChecked attrs else attrs\n"
    "    return effective"
)

assert _GOLD_IMPL in _BASE, "frozen impl region drifted; update _GOLD_IMPL"

# ---- proof-body anchor. A `prove_correct` tactic body is elided from the
# ---- consumer spec view, so a case that introduces an in-region `assert` may
# ---- retune the tactic script without touching the spec statement or dropping
# ---- the obligation. Unique in the file.
_GOLD_PROOF = "prove_correct computeContextAttrs by\n  loom_solve"

assert _GOLD_PROOF in _BASE, "frozen proof body drifted; update _GOLD_PROOF"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl block."""
    return _swap(_BASE, _GOLD_IMPL, body)


# ---- witness preamble. Reaches the method contract through Velvet's tester
# ---- machinery; checked in a file whose `prove_correct` block is stripped. The
# ---- method mutates `attrs` and returns `effective`, so the tester takes the
# ---- (mutable) starting mapping and the observation and reports whether the
# ---- resulting observable satisfies the postcondition. Fields are
# ---- `String`/`Bool`, whose equalities `decide` settles directly. ----
def _tester(body):
    return ("extract_program_for computeContextAttrs\n"
            "prove_precondition_decidable_for computeContextAttrs\n"
            "prove_postcondition_decidable_for computeContextAttrs\n"
            "derive_tester_for computeContextAttrs\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # post-image is SPEC-TOO-STRONG. Each keeps the obligation and the
    # byte-identical theorem statement; only the executable surface moves, and
    # the frozen `loom_solve` still discharges it (verified out-of-band with two
    # real builds).
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: handle the negative case first (pass the caller's mapping
        # through), fall through to the affirmative merge last. Observationally
        # identical (the decision collapses to the same onward mapping), no
        # write to `attrs`, so clauses (1) and (2) still hold definitionally.
        "module": _impl(
            "    let effective := if !checked then attrs else withChecked attrs\n"
            "    return effective"),
        "rationale": "structurally different CORRECT impl (negative case handled "
                     "first, affirmative merge last). The onward mapping is the "
                     "same value and `attrs` is never written, so clause (1) "
                     "`attrs = attrsOld` and clause (2) "
                     "`effective = if checked then withChecked attrsOld else "
                     "attrsOld` both hold definitionally and the frozen tactic "
                     "discharges the byte-identical obligation. Must verify, else "
                     "SPEC-TOO-STRONG (over-fit to the gold branch order).",
    },
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: stage each onward mapping through an explicit if/else with a
        # local binding and an in-branch return, instead of the single
        # let-then-return. Identical behaviour, no write to `attrs`.
        "module": _impl(
            "    if checked then\n"
            "      let prepared := withChecked attrs\n"
            "      return prepared\n"
            "    else\n"
            "      let passthrough := attrs\n"
            "      return passthrough"),
        "rationale": "CORRECT impl staging each onward mapping through a local "
                     "binding inside an explicit if/else with in-branch returns "
                     "instead of one inline let-then-return. Same behaviour and no "
                     "write to `attrs`, so clauses (1) and (2) still discharge and "
                     "the frozen tactic closes it; confirms the spec is not over-fit "
                     "to the inline-binding shape. Must verify, else SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — no `require` clause exists, so the sibling's "a normal
    # F2P-shaped caller mapping satisfies the (half-permission) precondition"
    # probe is vacuous: nothing could exclude the input. Re-aimed at the residual
    # admissibility risk on a total domain — that the post-image is
    # UNSATISFIABLE / degenerate at the interesting point. An in-region `assert`
    # pins the modeled mapping transform's value at the two F2P-shaped inputs (a
    # caller mapping already carrying the affirmative key at false is overwritten
    # to true — no duplicate entry; an absent key is appended), so the post-image
    # is demonstrably non-degenerate there. The gold body is kept verbatim so the
    # method's own obligation still discharges; the proof body is retuned (elided
    # from the spec view) to also close the concrete-literal assert. A false claim
    # about the same point would leave an unsolved goal (checked out-of-band).
    # =====================================================================
    {
        "id": "admiss-nondegenerate-merge",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _GOLD_IMPL,
                "    assert (with_name_prefix `assert\n"
                "      (withChecked [(\"checked\", false)] = [(\"checked\", true)] ∧\n"
                "       withChecked ([] : List (String × Bool)) = [(\"checked\", true)]))\n"
                + _GOLD_IMPL),
            _GOLD_PROOF,
            "prove_correct computeContextAttrs by\n"
            "  loom_solve <;> first | (refine ⟨?_, ?_⟩ <;> decide) | simp_all"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the two "
                     "F2P-shaped inputs: a caller mapping already carrying the "
                     "affirmative key at false is OVERWRITTEN to true (one entry, "
                     "not a duplicate), and an absent key is appended. The in-region "
                     "assert must discharge (else the obligation is degenerate / "
                     "PRECOND-TOO-STRONG); the gold body is kept verbatim so the "
                     "method's own `ensures` still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete starting state and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Witnesses vary BOTH binders:
    # `checked` over {true, false} and `attrs` over the empty mapping, a mapping
    # carrying an unrelated key, the F2P mapping carrying the affirmative key at
    # false, and further single-key mappings — so neither binder is pinned across
    # the battery.
    # =====================================================================
    {
        "id": "weak-frame-write-attrs",
        "kind": "uniqueness",
        "expect": "reject",
        # FRAME-MUTATION (the #1 defended property and the literal pre-change
        # bug): on the affirmative arm, write the affirmative entry INTO the
        # caller's own mapping and hand that same value on. The returned onward
        # mapping is still the right value (clause (2) holds), so the ONLY failing
        # clause is the frame (1): `attrs` no longer equals `attrsOld`.
        "module": _impl(
            "    if checked then\n"
            "      attrs := withChecked attrs\n"
            "      return attrs\n"
            "    else\n"
            "      return attrs"),
        "refinement": "this is the pre-change behaviour the fix removes: writing the "
                      "affirmative flag in place into the caller's OWN mapping. "
                      "Because that same mapping value is reused across the repeated "
                      "renderings of a multi-element control, the flag set during one "
                      "affirmative element's rendering persists into the mapping the "
                      "next element sees. The failing test drives a caller mapping "
                      "through the affirmative rendering and asserts the caller's "
                      "mapping still carries the flag at its ORIGINAL value "
                      "afterwards; the in-place write leaves it flipped, and the "
                      "multi-element test then sees a later negative element wrongly "
                      "marked affirmative — it would NOT resolve (it IS the bug).",
        "rationale": "REJECT from clause (1) `attrs = attrsOld`: the body writes the "
                     "affirmative entry into `attrs` and returns it, so the "
                     "post-state of the caller's mapping disagrees with its entry "
                     "value. Clause (2) is kept correct (the returned value is the "
                     "right onward mapping), so the ONLY failing clause is the frame. "
                     "This is the sibling's mandatory permission-frame probe "
                     "re-expressed as a value attack on the `mut` frame clause. "
                     "Refuted at a mapping carrying an unrelated key, checked = true. "
                     "If it verified => SPEC-TOO-WEAK (the frame protection is "
                     "hollow).",
        "witness": _tester(
            "example : computeContextAttrsTester [(\"class\", true)] true = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-always-affirmative",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN (negative sub-domain): force the affirmative entry on for
        # EVERY observation, dropping the negative arm. Correct when affirmative;
        # wrong on the negative sub-domain, where the onward mapping must be the
        # caller's mapping verbatim with NO entry added. (The sibling's
        # always-selected AND else-sets rivals both collapse onto this single
        # impl here — see footer.)
        "module": _impl(
            "    let effective := withChecked attrs\n"
            "    return effective"),
        "refinement": "a counterpart that unconditionally records the affirmative "
                      "flag — ignoring the negative observation — marks a control "
                      "affirmative for a backing value that is not. The negative-value "
                      "rendering tests expect NO affirmative flag on the onward "
                      "mapping, and the multi-element test expects a negative "
                      "element's mapping to carry no such entry; an unconditional "
                      "flag makes those mappings unequal and the tests fail — it "
                      "would NOT resolve.",
        "rationale": "REJECT from clause (2) on the negative sub-domain "
                     "(`checked = false`): the post-image demands `effective = "
                     "attrsOld` (the caller's mapping verbatim), but the body forces "
                     "the affirmative entry on. Clause (1) is kept correct (no write "
                     "to `attrs`). Refuted at a mapping carrying an unrelated key, "
                     "checked = false. If it verified => SPEC-TOO-WEAK.",
        "witness": _tester(
            "example : computeContextAttrsTester [(\"class\", true)] false = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-never-affirmative",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN (affirmative sub-domain): never record the affirmative
        # entry; always pass the caller's mapping through. Correct on the negative
        # sub-domain; wrong on the affirmative one, where the onward mapping must
        # carry the affirmative entry at true.
        "module": _impl(
            "    let effective := attrs\n"
            "    return effective"),
        "refinement": "a counterpart that never records the affirmative flag "
                      "(always hands the caller's mapping through unchanged) leaves "
                      "an affirmative control un-marked. The affirmative-value "
                      "rendering tests expect the affirmative flag on the onward "
                      "mapping and the multi-element test expects the first "
                      "affirmative element's mapping to carry it; a bare pass-through "
                      "omits it and the tests fail — it would NOT resolve.",
        "rationale": "REJECT from clause (2) on the affirmative sub-domain "
                     "(`checked = true`): the post-image demands `effective = "
                     "withChecked attrsOld` (the affirmative entry recorded true), "
                     "but a bare pass-through of `attrs` omits it. Clause (1) is kept "
                     "correct. Refuted at the EMPTY caller mapping, checked = true — "
                     "a point no other witness probes. If it verified => "
                     "SPEC-TOO-WEAK.",
        "witness": _tester(
            "example : computeContextAttrsTester ([] : List (String × Bool)) true "
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-wrong-flag-value",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE-LEVEL: on the affirmative arm, record the affirmative entry with
        # the WRONG value (false). Fresh, no write to `attrs`, correct key set —
        # but the pinned value is wrong.
        "module": _impl(
            "    let effective := if checked then setFlag attrs \"checked\" false "
            "else attrs\n"
            "    return effective"),
        "refinement": "a counterpart that records the affirmative entry with value "
                      "false for an affirmative control renders it un-marked despite "
                      "an affirmative backing value. The affirmative-value rendering "
                      "tests expect the flag present-and-true and the multi-element "
                      "test pins the first element's mapping to the affirmative entry "
                      "at true; the false value makes those mappings unequal and the "
                      "tests fail — it would NOT resolve.",
        "rationale": "REJECT from clause (2) on the affirmative sub-domain: the "
                     "post-image pins the affirmative entry to `true` "
                     "(`withChecked attrsOld`), and recording it at `false` cannot "
                     "satisfy it. Clause (1) is kept correct. Refuted at the F2P "
                     "mapping `[(\"checked\", false)]` (the affirmative key already "
                     "present at false, exercising the overwrite path), checked = "
                     "true. If it verified => SPEC-TOO-WEAK.",
        "witness": _tester(
            "example : computeContextAttrsTester [(\"checked\", false)] true "
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-spurious-entry",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE-LEVEL (extra key): on the affirmative arm, build the correct merge
        # then add a SECOND, unrelated entry the caller never had. The onward
        # mapping then carries a key outside `keys(attrsOld) ∪ {"checked"}`.
        "module": _impl(
            "    let effective := if checked then setFlag (withChecked attrs) \"x\" "
            "true else attrs\n"
            "    return effective"),
        "refinement": "a counterpart that injects a stray attribute beyond the "
                      "affirmative entry renders an extra attribute the rendering "
                      "step never expected. The multi-element test pins the first "
                      "element's onward mapping EXACTLY to the affirmative entry "
                      "(equality comparison); an extra key makes the mappings unequal "
                      "and the test fails — it would NOT resolve.",
        "rationale": "REJECT from clause (2) on the affirmative sub-domain: the "
                     "post-image pins `effective` to `withChecked attrsOld` exactly "
                     "(keys `= keys(attrsOld) ∪ {\"checked\"}`), so a spurious entry "
                     "`\"x\"` absent from `attrsOld` breaks the equality. Clause (1) "
                     "is kept correct. Refuted at a mapping carrying an unrelated key "
                     "`[(\"foo\", true)]`, checked = true. If it verified => "
                     "SPEC-TOO-WEAK.",
        "witness": _tester(
            "example : computeContextAttrsTester [(\"foo\", true)] true = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-append-duplicate-entry",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS on the OVERWRITE clause (added by audit). On the affirmative
        # arm, APPEND the affirmative entry at the end instead of installing it
        # (overwrite-if-present / append-if-absent). Agrees with the frozen
        # post-image on every caller mapping that does NOT already carry the
        # affirmative key — including every input the other four clause-(2) rivals
        # are refuted at except one — and diverges ONLY when the key is already
        # present, where appending leaves the FIRST (stale) entry positionally
        # determining the value and yields a duplicate key. The tightest rival in
        # the battery: no existing case attacks the overwrite direction, so
        # without it `withChecked`'s replace-vs-append behaviour is asserted by
        # the manifest and demonstrated nowhere.
        "module": _impl(
            "    let effective := if checked then attrs ++ [(\"checked\", true)] "
            "else attrs\n"
            "    return effective"),
        "refinement": "a counterpart that appends the affirmative entry rather than "
                      "installing it leaves a caller mapping that already carries the "
                      "entry at its stale value with TWO entries for the same "
                      "attribute, the stale one first. A mapping carries unique keys, "
                      "so the onward mapping is read at the stale value and the control "
                      "renders un-marked despite an affirmative backing value; the "
                      "rendering test that supplies a mapping already carrying the "
                      "entry then sees the wrong flag and the equality comparison "
                      "against the expected single-entry mapping fails — it would NOT "
                      "resolve.",
        "rationale": "REJECT from clause (2) on the affirmative sub-domain, at the "
                     "OVERWRITE point specifically: the post-image pins `effective` to "
                     "`withChecked attrsOld`, which REPLACES an existing affirmative "
                     "entry in place, whereas appending yields a distinct list "
                     "(duplicate key, stale value first). Clause (1) is kept correct. "
                     "Refuted at `[(\"checked\", false)]`, checked = true — the one "
                     "input where the two differ; on every mapping lacking the key "
                     "this rival is observationally IDENTICAL to gold, which is what "
                     "makes it the near-miss the other rivals leave unattacked. If it "
                     "verified => SPEC-TOO-WEAK (the overwrite clause is hollow).",
        "witness": _tester(
            "example : computeContextAttrsTester [(\"checked\", false)] true "
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-clobber-unrelated-entry",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE-LEVEL on the OTHER-KEYS-PRESERVED conjunct (added by audit #2).
        # Clause (2) pins `effective` to `withChecked attrsOld`, which decomposes
        # into THREE independent conjuncts: the key set is
        # `keys(attrsOld) ∪ {"checked"}`, the affirmative entry is true, AND every
        # OTHER key keeps the value the caller gave it. The first two were each
        # attacked (weak-spurious-entry, weak-wrong-flag-value); the third was
        # attacked by nothing. This rival installs the affirmative entry
        # CORRECTLY (right key, right value, overwrite semantics, no duplicate, no
        # extra key, `attrs` never written) and corrupts ONE UNRELATED entry's
        # value instead. So it is the only rival that survives every other case's
        # discriminator and it is refuted at a TWO-ENTRY mapping — the whole rest
        # of the battery is refuted at mappings of at most one entry, where there
        # is no "other key" to corrupt and the conjunct is unreachable in
        # principle rather than merely unprobed.
        "module": _impl(
            "    let effective := if checked then setFlag (withChecked attrs) "
            "\"class\" false else attrs\n"
            "    return effective"),
        "refinement": "a counterpart that records the affirmative flag correctly but "
                      "overwrites one of the caller's OTHER attribute entries hands "
                      "the rendering step an attribute the caller set to one value at "
                      "the opposite value. The caller's other attributes are supplied "
                      "precisely so the rendering carries them, so a rendering that "
                      "silently flips one produces different markup for that "
                      "attribute; the rendering tests compare the produced attribute "
                      "mapping (and the emitted markup) against the caller's own "
                      "entries and see the flipped one, so they fail — it would NOT "
                      "resolve.",
        "rationale": "REJECT from clause (2) on the affirmative sub-domain, at the "
                     "OTHER-KEYS-PRESERVED conjunct specifically: the post-image pins "
                     "`effective` to `withChecked attrsOld`, which changes ONLY the "
                     "affirmative entry and leaves every other association exactly as "
                     "the caller supplied it. This body gets the affirmative entry "
                     "entirely right — correct key, value `true`, installed with "
                     "overwrite semantics, no duplicate, no spurious key — and "
                     "corrupts an unrelated entry's value instead, so it is the one "
                     "rival no other case's witness can refute. Clause (1) is kept "
                     "correct (`attrs` is never written). Refuted at the TWO-ENTRY "
                     "mapping `[(\"class\", true), (\"id\", true)]`, checked = true — "
                     "the only witness in the battery with more than one entry, which "
                     "is what makes the conjunct reachable at all. If it verified => "
                     "SPEC-TOO-WEAK (the spec would pin the affirmative entry while "
                     "letting the caller's other attributes be rewritten freely).",
        "witness": _tester(
            "example : computeContextAttrsTester [(\"class\", true), (\"id\", true)] "
            "true = false := by\n  decide\n"),
    },
    {
        "id": "weak-frame-write-negative-arm",
        "kind": "uniqueness",
        "expect": "reject",
        # FRAME on the NEGATIVE sub-domain (added by audit). The shipped
        # frame rival writes `attrs` only on the AFFIRMATIVE arm, so clause (1) is
        # demonstrated at `checked = true` and nowhere else. This rival writes the
        # caller's mapping on the NEGATIVE arm instead, while RETURNING the saved
        # entry value so clause (2) still holds there — isolating the rejection to
        # the frame at the sub-domain the battery otherwise leaves unprobed.
        "module": _impl(
            "    if checked then\n"
            "      return withChecked attrs\n"
            "    else\n"
            "      let saved := attrs\n"
            "      attrs := setFlag attrs \"checked\" true\n"
            "      return saved"),
        "refinement": "a counterpart that writes the affirmative flag into the "
                      "caller's OWN mapping while rendering a NEGATIVE element hands "
                      "the correct onward mapping to this rendering but leaves the "
                      "caller's mapping flipped. Because that mapping value is reused "
                      "across the repeated renderings of a multi-element control, "
                      "every element after a negative one is then marked affirmative. "
                      "The test that drives a caller mapping through a rendering and "
                      "asserts the caller's mapping still carries its ORIGINAL value "
                      "afterwards fails, and the multi-element test sees a later "
                      "element wrongly marked — it would NOT resolve.",
        "rationale": "REJECT from clause (1) `attrs = attrsOld` on the NEGATIVE "
                     "sub-domain (`checked = false`). The shipped "
                     "weak-frame-write-attrs writes `attrs` on the AFFIRMATIVE arm "
                     "only, leaving the residual goal `withChecked attrsOld = "
                     "attrsOld` under `if_pos : checked = true`; this rival leaves "
                     "`setFlag attrsOld \"checked\" true = attrsOld` under `if_neg`, a "
                     "DIFFERENT sub-domain, so it is not a witness-sharing duplicate. "
                     "Clause (2) is kept correct on both arms (the saved entry value "
                     "is returned). Refuted at the EMPTY caller mapping, checked = "
                     "false — a point no other witness probes. If it verified => "
                     "SPEC-TOO-WEAK (the frame is pinned on only half the domain).",
        "witness": _tester(
            "example : computeContextAttrsTester ([] : List (String × Bool)) false "
            "= false := by\n  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 10 SPEC cases (2 soundness
# positives, 1 admissibility, 2 frame-mutation rivals, 5 uniqueness rivals) plus a
# 3-case AXIOM lane, contracting one function `prepare_attrs(value, attrs)` over a
# heap dict held at half permission, with two @ContractOnly callees (`mapping_with`
# / `mapping_copy`) and a @Pure GROUNDED predicate `counts_as_selected(value)`.
# This bundle models the same operation over the purely-functional carrier — the
# caller mapping `attrs : List (String × Bool)` and the affirmative observation
# taken directly as `checked : Bool` — and pins TWO clauses: the frame (`attrs`
# unchanged, the #1 property) and the onward mapping (the affirmative merge when
# affirmative, the caller mapping verbatim when negative). Every sibling case is
# accounted for below.
#
#   sibling case                    -> here
#   ---------------------------------------------------------------------
#   pos-reorder                     -> pos-branch-reorder                PORTED
#   pos-local                       -> pos-local-reshape                 PORTED
#   admiss-present-dict             -> admiss-nondegenerate-merge        RE-AIMED
#   frame-mutate-return-self        -> weak-frame-write-attrs            PORTED
#   frame-mutate-return-fresh       -> (none)                           COLLAPSED
#   always-selected                 -> weak-always-affirmative          PORTED
#   never-selected                  -> weak-never-affirmative           PORTED
#   wrong-flag-false                -> weak-wrong-flag-value             PORTED
#   spurious-key                    -> weak-spurious-entry               PORTED
#   else-sets-checked               -> (none)                           COLLAPSED
#   AXIOM_TESTS (3)                 -> (none)                           DROPPED (G-AX)
#
# PORTED (positives): both structural reshapes port directly — a branch reorder
#   and an explicit if/else with local bindings and in-branch returns. Neither
#   writes `attrs`, so the frozen `loom_solve` closes the byte-identical obligation.
# RE-AIMED (admissibility): the sibling's admissibility case does a self-call to
#   witness that a normal present-dict F2P-shaped input satisfies the
#   half-permission precondition (Requires(Acc(dict_pred(attrs), 1/2))). There is
#   no `require` clause here (pre-conditions region empty), so the "a normal input
#   satisfies the precondition" reading is vacuous. Re-aimed at proving the
#   post-image is satisfiable AND non-degenerate at the two F2P-shaped inputs (the
#   affirmative key overwritten from false to true — no duplicate; an absent key
#   appended), via a live in-region assert against concrete literals. Preserves the
#   sibling's F2P shape (a present dict already holding the affirmative key).
# PORTED (frame-mutate-return-self): the sibling writes the caller's dict held at
#   Acc(.,1/2) and is rejected by the PERMISSION SYSTEM. This backend has no
#   permission system, BUT `attrs` is a `mut` binder pinned unchanged by clause (1)
#   (directive-5 frame discipline), so a body that writes it violates a genuine
#   postcondition clause. The attack ports (it is the literal pre-change in-place
#   write the fix removes); only the rejection SOURCE changes (postcondition clause
#   (1), not permissions). This is the sibling's #1 defended property and it is NOT
#   vacuous here.
# COLLAPSED (frame-mutate-return-fresh): the sibling's second frame flavour writes
#   the caller's dict IN PLACE but then returns a FRESH copy, to isolate the
#   rejection to the WRITE alone (under permissions, `Result() is not attrs` would
#   hold, so only the write is illegal). On this carrier clause (1) `attrs =
#   attrsOld` catches ANY write to `attrs` regardless of what value is returned —
#   there is no permission-vs-freshness distinction, so a write-then-return-fresh
#   rival fails clause (1) at the SAME point and for the SAME reason as
#   weak-frame-write-attrs. It would share that rival's witness and demonstrate no
#   new sub-domain, so it is collapsed, not shipped (spec_guide: two rivals may
#   share a witness only if they fail at the same input for the same reason — here
#   they do, so one suffices). MEASURED (audit): the write-then-return-fresh impl
#   was built and leaves the residual goal `withChecked attrsOld = attrsOld` under
#   `if_pos : checked = true` — BYTE-IDENTICAL to weak-frame-write-attrs' goal —
#   and weak-frame-write-attrs' own witness elaborates against it unchanged. The
#   collapse is confirmed, not assumed. Note this shared goal is why the frame
#   clause needed a SECOND rival on the other sub-domain
#   (weak-frame-write-negative-arm): both sibling frame flavours land at
#   `checked = true`, so `checked = false` was frame-unprobed until the audit.
# COLLAPSED (else-sets-checked): the sibling's supporting near-miss forces the
#   affirmative key on in the NEGATIVE branch while keeping the affirmative branch
#   correct — i.e. `withChecked` in both branches. On this carrier that is
#   byte-identical to the always-selected rival's impl (`withChecked attrs`
#   unconditionally): both branches produce the same value, so the two sibling
#   rivals map to ONE impl here, refuted at the same negative-sub-domain point.
#   Kept as weak-always-affirmative; the else-sets duplicate is collapsed, not a
#   dropped attack (the negative-sub-domain clause it targeted IS attacked).
#   MEASURED (audit): the two-branch `withChecked` spelling was built and leaves
#   the residual goal `withChecked attrsOld = if checked = true then withChecked
#   attrsOld else attrsOld` — byte-identical to weak-always-affirmative's — and
#   that rival's witness elaborates against it unchanged. Collapse confirmed.
#
# ADDED BY AUDIT (two sub-domains the ported set left unattacked; each rival was
#   built and each witness re-derived twice, rival exit 0 / gold exit 1 with a
#   semantic `decide` refutation on gold):
#   weak-append-duplicate-entry    — clause (2), the OVERWRITE direction of
#     `withChecked`. Every ported clause-(2) rival is wrong on mappings that lack
#     the affirmative key, so append-instead-of-install agreed with gold at all
#     but one input and no case pinned replace-vs-append. Refuted at
#     [("checked", false)] / true.
#   weak-frame-write-negative-arm  — clause (1) on the NEGATIVE sub-domain. Both
#     sibling frame flavours write on the affirmative arm, so the frame was pinned
#     at `checked = true` only. Refuted at [] / false.
#
# ADDED BY AUDIT #2 (a third conjunct of clause (2) that both the port AND the
#   first audit left unattacked; rival built and witness re-derived twice by the
#   auditor, rival exit 0 / gold exit 1 with a semantic `decide` refutation, plus
#   the flipped-claim FORGERY pair below):
#   weak-clobber-unrelated-entry   — clause (2), the OTHER-KEYS-PRESERVED
#     conjunct. `effective = withChecked attrsOld` decomposes into three
#     independent conjuncts — the key set, the affirmative entry's value, and
#     every OTHER key keeping the caller's value. The first two were attacked
#     (weak-spurious-entry, weak-wrong-flag-value); the third was attacked by
#     nothing, and could not have been: every other witness starts from a mapping
#     of AT MOST ONE entry, where there is no other key to corrupt, so the
#     conjunct was unreachable in principle rather than merely unprobed. This
#     rival installs the affirmative entry entirely correctly and flips one
#     unrelated entry's value instead, so no other case's witness refutes it.
#     Refuted at the two-entry mapping [("class", true), ("id", true)] / true.
#     MEASURED discrimination (auditor's builds): witness on rival exit 0; on the
#     frozen solution exit 1 with `decide proved that the proposition
#     computeContextAttrsTester [("class", true), ("id", true)] true = false is
#     false`. FORGERY CHECK (the claim flipped to `= true`): on the frozen
#     solution it ELABORATES (exit 0) and on the rival it FAILS (exit 1) with the
#     mirror-image message — so gold's exit code tracks WHAT IS CLAIMED and the
#     refutation carries information rather than being a fixed tactic mismatch.
#     `#eval` of the tester confirms the two sides disagree at that input
#     (gold true / rival false).
#
# NOT SHIPPED — an ORDER-ONLY near-miss that the carrier makes wrong but the real
#   domain does not (auditor, measured). `(attrs.filter (·.1 != "checked")) ++
#   [("checked", true)]` removes any existing affirmative entry and re-appends it.
#   It is REJECTED by the spec (exit 1) and a witness at
#   [("checked", false), ("class", true)] / true discriminates cleanly
#   (rival 0 / gold 1). It is deliberately NOT shipped: on this carrier the
#   onward mapping is an association LIST, so it differs from `withChecked` in the
#   POSITION of the affirmative entry, and position is NOT observable in the real
#   domain — the counterpart mapping compares equal (mapping equality ignores
#   entry order) and the rendering step sorts attributes before emitting them. Its
#   `refinement` would therefore have to claim a failing counterpart that does not
#   in fact fail, so shipping it would attest to a distinction the carrier invents.
#   Recorded here rather than dropped silently: the two NATURAL faithful spellings
#   of the onward mapping both agree with `withChecked` positionally, so this is a
#   carrier artifact and not a gap.
#
# DIVERGENCE LANE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
#   and no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
#
# BINDER / CLAUSE COVERAGE. Both independent top-level clauses are attacked on
#   BOTH of their sub-domains:
#   (1) the frame by weak-frame-write-attrs (affirmative arm) and
#       weak-frame-write-negative-arm (negative arm);
#   (2) the onward mapping by weak-always-affirmative (negative sub-domain),
#       weak-never-affirmative (affirmative sub-domain), weak-wrong-flag-value
#       (the pinned true value), weak-spurious-entry (the exact key set),
#       weak-append-duplicate-entry (the overwrite-vs-append direction), and
#       weak-clobber-unrelated-entry (the other-keys-preserved conjunct);
#   and both clauses are defended by the two positive controls and the
#   admissibility case. Clause (2) is the conjunction of THREE independent
#   requirements on the onward mapping and each now has its own rival: the key set
#   (spurious-entry), the affirmative entry's value and position
#   (wrong-flag-value, append-duplicate-entry), and every other key's value
#   (clobber-unrelated-entry). The eight reject witnesses probe seven DISTINCT
#   starting states:
#     [("class", true)]              true    weak-frame-write-attrs
#     []                             false   weak-frame-write-negative-arm
#     [("class", true)]              false   weak-always-affirmative
#     []                             true    weak-never-affirmative
#     [("checked", false)]           true    weak-wrong-flag-value
#     [("foo", true)]                true    weak-spurious-entry
#     [("checked", false)]           true    weak-append-duplicate-entry
#     [("class", true),("id", true)] true    weak-clobber-unrelated-entry
#   so `checked` is varied over {true, false} against BOTH clauses, and `attrs`
#   over the empty mapping, an unrelated-key mapping, the F2P mapping carrying the
#   affirmative key at false, a further single-key mapping, and a TWO-entry mapping
#   — neither binder is pinned across the battery, and neither clause is pinned on
#   only half its domain. The two-entry state is load-bearing rather than a fifth
#   spelling of "some mapping": at one entry or fewer there is no unrelated key, so
#   the other-keys-preserved conjunct cannot be violated at all and the rival that
#   attacks it has no refutation point (this is why the battery carried none until
#   the second audit). weak-wrong-flag-value and weak-append-duplicate-entry share
#   a starting state but fail for DIFFERENT reasons (the recorded VALUE vs the
#   entry's position/multiplicity) and neither's witness holds of the other's gold,
#   so this is not witness-sharing. Each witness binds nothing (literal starting
#   state), so no consistency probe applies.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
#   axiom and no A-reference deep model (the mapping transform is modeled deeply as
#   the pure `withChecked` and checked by G-CONF; mapping.md §3), so there is
#   nothing there to probe.
AXIOM_TESTS = []
