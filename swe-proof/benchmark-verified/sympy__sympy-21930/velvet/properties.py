"""properties.py — G-PBT falsification battery for sympy__sympy-21930 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
every ``prove_correct <method>`` obligation survives with a byte-identical
header) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against a subject known to satisfy the spec).

DEFENDED SURFACE — THREE contracted rendering methods, one obligation each:

  tensorIndexLatex (symbol upper lower)
    ensures out = wrapGroup (symbol ++ "^{" ++ concatNames upper
                              ++ "}_{" ++ concatNames lower ++ "}")
  bDaggerLatex (name)
    ensures out = wrapGroup (<creation-b template> ++ name ++ "}")
  aDaggerLatex (name)
    ensures out = wrapGroup (<creation-a template> ++ name ++ "}")

Each renderer produces a LaTeX atom and then encloses it in an explicit
``{ … }`` group (``wrapGroup s = "{" ++ s ++ "}"``), so that a token appended
after the atom (an exponent) binds to the WHOLE group rather than colliding with
the atom's trailing subscript. That enclosing group is the entire content of the
desired behavior: the pre-image emits the bare atom, and the failing scenario is
a double superscript rendered against the un-grouped atom.

Each obligation is a SINGLE top-level clause — the exact character sequence the
method must return — but that sequence has structurally independent features a
rival can get wrong, and the battery attacks each of them separately:

  (a) the LEADING ``{`` of the enclosing group;
  (b) the TRAILING ``}`` of the enclosing group;
  (c) the ATOM BODY between them — which for the tensor renderer is itself
      composed of a base symbol, an upper index run and a lower index run at
      DISTINCT positions in the template, and for the creation renderers is a
      literal template with the state name interpolated into it.

(c) matters independently of (a)/(b): a rival may wrap correctly and still be
wrong, and such a rival is invisible to any battery that only mangles the wrap.
Seven rivals here exist solely to cover it — the tensor run-swap, the tensor
dropped-upper-run, the creation dropped-name, and the FOUR character-ORDER rivals
(tensor upper per-name reverse, tensor lower per-name reverse, tensor base-symbol
reverse, creation name reverse) described under SUB-DOMAIN SPLITS below.

INPUT BINDERS. ``tensorIndexLatex`` has three free binders — ``symbol``,
``upper`` (the run of upper index names) and ``lower`` (the run of lower index
names); ``bDaggerLatex`` / ``aDaggerLatex`` each have one, ``name`` (the state
name). No binder is held at a single value across the reject witnesses, and no
binder is left unabused: ``upper``/``lower`` are each varied over empty,
singleton and two-element runs, are SWAPPED against each other by one rival, and
one rival drops ``upper``'s contribution entirely. ``name`` is varied over four
LABELS and dropped entirely by one rival — but note that ``"0"``/``"3"``/``"5"``/
``"7"`` are four spellings of ONE structural point (a length-1 label), which is
why the two reverse rivals below carry the battery's only multi-character inputs.

SUB-DOMAIN SPLITS. Four rivals are deliberately NEAR-MISSES that agree with the
post-image on part of the domain, so they cannot share a witness with the
always-wrong rivals and each carries its own discriminating input:

  * the creation dropped-name rival is CORRECT at the empty ``name`` (there the
    interpolated run contributes nothing) and wrong at every non-empty one —
    measured: its witness at ``name="3"`` refutes it, and the same claim at
    ``name=[]`` does NOT (it holds of the post-image there);
  * the tensor run-swap rival is CORRECT whenever ``upper = lower`` (including
    when both are empty) and wrong otherwise, so it is refuted at an input where
    the two runs DIFFER;
  * the FOUR CHARACTER-ORDER rivals (``reject-tensor-reverse-index-names``,
    ``reject-tensor-reverse-lower-names``, ``reject-tensor-reverse-symbol``,
    ``reject-bdagger-reverse-name``) are the IDENTITY on every SINGLE-CHARACTER
    label, and so agree with the post-image at every OTHER input point in this
    battery. They pin the sub-domain no delimiter- or length-shaped rival
    reaches: that the clause fixes the character CONTENT of each interpolated
    label and not merely its length, count or template slot. Each is therefore
    refuted at a MULTI-CHARACTER label (``upper=["xy"]``; ``lower=["jk"]``;
    ``symbol="Sq"``; ``name="ab"``) — measured: reversing is observationally
    identical to the post-image at every single-character point, so a battery
    whose witnesses were all single-character would admit all four. Each of the
    three interpolated carriers of the tensor template (base symbol, upper run,
    lower run) now has its per-name character order attacked separately, because
    a rival mangling one of them is invisible to the rivals aimed at the others.

CARRIER NOTE — THE DECIDABLE BOUNDARY, AND WHY THE TENSOR LANE NEEDS A
REFERENCE. A witness reaches the post-image through Velvet's tester machinery
(``<method>Tester args = false`` says the extracted program's result violates the
method's postcondition at that concrete input) and closes by ``decide``, checked
in a file whose ``prove_correct`` blocks have been stripped so no tactic script
can mask the verdict. The carrier is ``List Char`` throughout — fully concrete
literal inputs, no opaque term, so no conditioning on the carrier is needed and
no witness here binds any hypothesis.

The frozen ``tensorIndexLatex`` impl, however, runs two backward ``while`` loops
over the index runs, and under ``loom.semantics.choice "demonic"`` the loop
fixpoint elaborates through ``Classical.choice``, which the kernel cannot unfold.
MEASURED: against the frozen tensor impl ``decide`` is stuck for EVERY claim,
true or false — the build fails with ``did not reduce to `isTrue` or `isFalse` ``
rather than by deciding anything, so its exit code attests to a refutation that
was never performed. Each tensor reject therefore carries a
``witness_reference``: ``_TENSOR_LOOPFREE``, a loop-free implementation of the
same frozen spec that DOES reduce, and which the gate independently checks shares
the spec and VERIFIES before refuting the witness against it. That is sound for
the reason gold was: an impl the verifier accepts cannot violate its own spec, so
a genuine witness must fail there too. Measured for all five tensor witnesses:
against the reference the build fails with ``decide`` PROVING the tester false —
a real refutation, no stuck reduction. ``_TENSOR_LOOPFREE`` also ships as its own
``expect="verify"`` case (``pos-tensor-loopfree-reference``), so the battery
itself records that loop-freeness is not what any rival is rejected for. The two
creation renderers are loop-free already, so both gold and rival reduce and
discrimination there is by VALUE against the frozen solution directly.

ADVERSARIAL READ of the nagini classes:
  * FRAME-MUTATION — VACUOUS on this backend. The nagini sibling's two
    frame-mutation rivals exist because its read-only input carries a fractional
    heap permission an impl could overwrite (an indexed store, an append). This
    backend is referentially transparent: ``symbol`` / ``upper`` / ``lower`` /
    ``name`` are immutable value parameters, this bundle declares no ``mut`` input
    binder, and there is no heap or aliasing. There is no read-only input to
    overwrite and no permission system to trip, so the class is vacuous. No
    substitute permission probe is fabricated.
  * DIVERGENCE / NON-TERMINATION - CLOSED BY THE SEMANTICS, and NOT the spec hole
    an earlier revision of this docstring described. That revision asserted this
    bundle sets ``loom.semantics.termination
    "partial"`` and that a non-terminating impl therefore satisfies every
    ``ensures`` VACUOUSLY. That was FALSE about this artifact: ``Solution.lean``
    line 4 sets ``"total"``. The bullet described the pre-remediation corpus (the
    ``partial`` -> ``total`` flip has since landed corpus-wide) and was never
    re-derived against the file it ships beside. Re-measured here with real
    builds, under the semantics this bundle actually sets:

      - a rival whose upper-index loop carries NO ``decreasing`` measure is
        REJECTED (exit 1, ``Decreasing annotations are required in total
        correctness semantics``). So the class is NOT admitted vacuously and the
        old "verifies vacuously" claim is measured-wrong.
      - it is nevertheless NOT shippable as a witnessed reject case, for a
        demonstrated TOOLING reason rather than a carrier one: that error is
        raised on the impl itself, so it also breaks the witness file, which
        contains the same impl. Measured: the witness built against this rival
        fails with the identical decreasing-annotations error (exit 1) instead of
        elaborating, so the rival half of the discrimination check can never
        succeed and the case would land ``witness-unproven`` — inconclusive, not
        a pass. Rejection here is attributable to the TERMINATION obligation,
        which needs no value witness, rather than to the postcondition.
      - and there is NO residual measure hole either. A previous revision of this
        bullet recorded one in ``spec_holes``, claiming the ``total`` obligation
        accepts a NON-DECREASING measure so that ``while 0 < 1`` with
        ``decreasing (0 : Nat)`` VERIFIES while returning the UNGROUPED atom. That
        is RETRACTED on measurement: the same loop carrying that constant measure
        is REJECTED, exit 1, on the measure's own goal:
        ``unsolved goals case «decreasing_1: (0 : Nat)» ⊢ 0 < 0``. The obligation
        is real because both header lines select it: line 4's ``set_option
        loom.semantics.termination "total"`` makes Loom's option handler open the
        ``TotalCorrectness`` scope, and the file opens it explicitly as well;
        ``TotalCorrectness.WPGen.forWithInvariantLoop`` takes the ``measure`` and
        emits ``⌜measure b' < measure b⌝`` as a goal, whereas only the
        ``PartialCorrectness`` twin takes a measure and discards it. So a
        diverging rival cannot launder a wrong answer through an unreachable exit
        here: it never gets past its own descent obligation.
  * PARTIAL-DOMAIN / VALUE — APPLIES, and carries the reject lane. The single
    postcondition pins the full character sequence on EVERY input, so any rival
    that mishandles the enclosing group or the atom body diverges from the
    post-image and is refuted.
  * UNGROUNDED-ORACLE ECHO — N/A. The ``axioms`` region is empty (mapping.md §3):
    there is no opaque answer-key. Every postcondition is a fully-grounded
    function of the method's own inputs (literal templates + ``concatNames`` over
    the index names + the group wrap), so the only way to satisfy it is to build
    that exact sequence, which the positive controls do honestly.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-21930"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors (verbatim from Solution.lean) ----------------------
# Each anchor lies wholly inside one method's impl region (or, for _TENSOR_PROOF,
# inside a prove_correct tactic body — also elided by the spec view) and is
# unique in the file, both asserted by _swap at load time. So same_spec is
# preserved and any rejection is attributable to the postcondition, never a
# tampered spec.

# The FULL tensorIndexLatex impl body (backward loops + group wrap). Unique.
_TENSOR_IMPL = (
    "    -- impl-start\n"
    "    let mut up : List Char := []\n"
    "    let mut i := upper.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ upper.length\n"
    "      invariant up = concatNames (upper.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      up := upper[i - 1]! ++ up\n"
    "      i := i - 1\n"
    "    let mut lo : List Char := []\n"
    "    let mut j := lower.length\n"
    "    while j > 0\n"
    "      invariant 0 ≤ j ∧ j ≤ lower.length\n"
    "      invariant lo = concatNames (lower.drop j)\n"
    "      done_with j = 0\n"
    "      decreasing j\n"
    "    do\n"
    "      lo := lower[j - 1]! ++ lo\n"
    "      j := j - 1\n"
    '    let body := symbol ++ "^{".toList ++ up ++ "}_{".toList ++ lo ++ "}".toList\n'
    "    let out := wrapGroup body\n"
    "    return out\n"
    "    -- impl-end"
)
assert _BASE.count(_TENSOR_IMPL) == 1, "tensor-impl anchor drift"

# The tensor obligation's frozen tactic body. Every loop-free tensor variant
# removes the two loops, so the two per-loop bullets the frozen script discharges
# no longer exist and `loom_solve` alone closes the reshaped obligation. This
# lies inside the prove_correct tactic body (elided by the velvet spec view); the
# `prove_correct tensorIndexLatex` HEADER — the obligation itself — is retained
# byte-for-byte, which variant_scope independently enforces.
_TENSOR_PROOF = (
    "prove_correct tensorIndexLatex by\n"
    "  loom_solve\n"
    "  · rw [concatNames_drop_step upper i (by omega) (by omega)]; simp_all\n"
    "  · rw [concatNames_drop_step lower j (by omega) (by omega)]; simp_all\n"
)
assert _BASE.count(_TENSOR_PROOF) == 1, "tensor-proof anchor drift"

# The gold tensor tail — the unique `let body … / let out := wrapGroup …` line
# trio (the looped tensor positive reshapes only this, keeping both loops).
_TENSOR_TAIL = (
    '    let body := symbol ++ "^{".toList ++ up ++ "}_{".toList ++ lo ++ "}".toList\n'
    "    let out := wrapGroup body\n"
    "    return out"
)
assert _BASE.count(_TENSOR_TAIL) == 1, "tensor-tail anchor drift"

# The bDaggerLatex impl body (loop-free). Unique via the `b` template literal.
_BD_IMPL = (
    r'    let body := "b^\\dagger_{".toList ++ name ++ "}".toList' "\n"
    "    let out := wrapGroup body\n"
    "    return out"
)
assert _BASE.count(_BD_IMPL) == 1, "bDagger-impl anchor drift"

# The aDaggerLatex impl body (loop-free). Unique via the `a` template literal.
_AD_IMPL = (
    r'    let body := "a^\\dagger_{".toList ++ name ++ "}".toList' "\n"
    "    let out := wrapGroup body\n"
    "    return out"
)
assert _BASE.count(_AD_IMPL) == 1, "aDagger-impl anchor drift"

# The tensor atom body expression, spelled with the SAME fold `concatNames` the
# postcondition uses, so a loop-free tensor variant differs from gold only in
# what it does around/with the index runs — never in how they are folded.
_TB = ('symbol ++ "^{".toList ++ concatNames upper ++ "}_{".toList '
       '++ concatNames lower ++ "}".toList')


def _tensor(expr):
    """A loop-free tensorIndexLatex variant returning `expr`.

    Replaces the whole looped body so the extracted Exec kernel-reduces under
    `decide` (see CARRIER NOTE), and drops the two now-nonexistent per-loop
    bullets from the obligation's tactic body so a CORRECT loop-free impl still
    proves. The `prove_correct` header is untouched.
    """
    body = _swap(_BASE, _TENSOR_IMPL,
                 "    -- impl-start\n"
                 "    let out := " + expr + "\n"
                 "    return out\n"
                 "    -- impl-end")
    return _swap(body, _TENSOR_PROOF,
                 "prove_correct tensorIndexLatex by\n  loom_solve\n")


# The witness_reference for every tensor reject: a loop-free impl of the frozen
# spec, built from the same `concatNames` fold the postcondition uses, so it is
# observationally identical to gold and VERIFIES (checked by the gate before any
# witness is refuted against it), while reducing where gold's loops cannot.
_TENSOR_LOOPFREE = _tensor("wrapGroup (" + _TB + ")")


def _tester(base, ex):
    """Reach the post-image through Velvet's tester machinery, checked in a file
    whose prove_correct blocks are stripped. `ex` is a `<base>Tester … = false`
    example closed by `decide` at fully-concrete literal inputs — it binds no
    hypothesis, so there is nothing for the gate's consistency probe to find
    inconsistent."""
    return (f"extract_program_for {base}\n"
            f"prove_precondition_decidable_for {base}\n"
            f"prove_postcondition_decidable_for {base}\n"
            f"derive_tester_for {base}\n\n" + ex)


def _tensor_witness(symbol, upper, lower):
    return _tester(
        "tensorIndexLatex",
        f"example : tensorIndexLatexTester {symbol} {upper} {lower} "
        "= false := by\n  decide\n")


def _name_witness(base, name):
    return _tester(
        base, f'example : {base}Tester "{name}".toList = false := by\n  decide\n')


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally-different but CORRECT impls,
    # each MUST verify. If a faithful correct reshape cannot verify, the
    # postcondition is SPEC-TOO-STRONG (it over-pins the syntactic shape of the
    # impl rather than the returned sequence). All four verified green during
    # authoring.
    # =====================================================================
    {
        "id": "pos-tensor-inline-wrap",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _TENSOR_TAIL,
            '    return wrapGroup (symbol ++ "^{".toList ++ up ++ "}_{".toList '
            '++ lo ++ "}".toList)'),
        "rationale": (
            "drops the intermediate `let body := … / let out := wrapGroup body` "
            "binding and returns `wrapGroup (…)` applied directly to the same "
            "atom expression, keeping BOTH backward index loops and their "
            "invariants verbatim. Observationally identical to gold on every "
            "input, so out = wrapGroup (symbol ++ … ) still holds and the frozen "
            "`loom_solve; rw [concatNames_drop_step …]; simp_all` proof still "
            "closes unedited. Must verify else SPEC-TOO-STRONG."),
    },
    {
        "id": "pos-tensor-loopfree-reference",
        "kind": "soundness",
        "expect": "verify",
        "module": _TENSOR_LOOPFREE,
        "rationale": (
            "the SAME source every tensor reject names as its "
            "`witness_reference`, shipped as a case in its own right so the "
            "battery records that loop-freeness is NOT what any tensor rival is "
            "rejected for. It computes the index runs directly with the "
            "`concatNames` fold the postcondition itself uses instead of "
            "accumulating them in two backward `while` loops — a genuinely "
            "different control-flow shape, observationally identical on every "
            "input, so the obligation still holds and `loom_solve` alone closes "
            "it (the frozen script's two per-loop bullets are dropped because "
            "the loops they discharge no longer exist; the `prove_correct` "
            "header is untouched). Must verify else SPEC-TOO-STRONG — and if it "
            "did not, every tensor reject would be reported "
            "witness-reference-invalid rather than passing."),
    },
    {
        "id": "pos-bdagger-return-wrap-directly",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _BD_IMPL,
            r'    return wrapGroup ("b^\\dagger_{".toList ++ name ++ "}".toList)'),
        "rationale": (
            "returns wrapGroup applied to the atom directly rather than binding "
            "it to `body` and `out` first — the same returned sequence for every "
            "`name`, so the postcondition holds and the frozen `loom_solve` proof "
            "closes. Must verify else SPEC-TOO-STRONG over the let-binding shape."),
    },
    {
        "id": "pos-adagger-rename-drop-out-let",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _AD_IMPL,
            r'    let atom := "a^\\dagger_{".toList ++ name ++ "}".toList'
            "\n    return wrapGroup atom"),
        "rationale": (
            "renames the atom binding and drops the intermediate `let out`, "
            "returning `wrapGroup atom` directly — the identical returned "
            "sequence for every `name`, so the postcondition holds and the "
            "frozen `loom_solve` proof closes with no proof edit. Must verify "
            "else SPEC-TOO-STRONG over the let-binding shape."),
    },

    # =====================================================================
    # ADMISSIBILITY — the third direction (PRECOND-TOO-STRONG). None of the three
    # methods declares a `require` clause, so the nagini sibling's literal
    # "a normal input satisfies the precondition" probe is degenerate. The
    # analogue on a TOTAL carrier is the obligation being UNSATISFIABLE at an
    # F2P-shaped input, which a positive that discharges the post-image at that
    # concrete input — by evaluation, as a `have`, before closing the frozen
    # obligation verbatim — tests directly. An earlier revision of this manifest
    # recorded the whole lane as VACUOUS on the grounds that "no method declares a
    # precondition"; that is the reason the audit brief names as insufficient, and
    # it left the battery testing two of the gate's three directions.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-tensor",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, "prove_correct tensorIndexLatex by",
            "prove_correct tensorIndexLatex by\n"
            "  have f2p_shaped :\n"
            "      wrapGroup (\"A\".toList ++ \"^{\".toList\n"
            "          ++ concatNames [\"a\".toList, \"b\".toList] ++ \"}_{\".toList\n"
            "          ++ concatNames [\"i\".toList, \"j\".toList] ++ \"}\".toList)\n"
            "        = \"{A^{ab}_{ij}}\".toList := by\n"
            "    decide"),
        "rationale": (
            "PRECOND-TOO-STRONG probe for the tensor obligation. The impl region "
            "is kept VERBATIM and the `prove_correct` header is untouched; what "
                "is added, inside the (spec-view-elided) tactic body, is a `have` "
            "that discharges the obligation's own post-image at one concrete "
            "F2P-shaped input BY EVALUATION — a two-index atom with two-element "
            "upper and lower runs — showing the required sequence at that point "
            "is `{A^{ab}_{ij}}`, the grouped form, and that `decide` can actually "
            "REACH it. Then the frozen obligation closes as before. If the "
            "post-image were unsatisfiable at an F2P-shaped input (the total-"
            "carrier analogue of a precondition that excludes a normal input), "
            "the `have` would not discharge and this case would fail. Measured "
            "exit 0 in scope. This is the battery's only case in the "
            "`admissibility` lane, so without it the manifest tested "
            "SPEC-TOO-WEAK and SPEC-TOO-STRONG but never PRECOND-TOO-STRONG."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input, and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P. Each tensor rival is loop-free (so
    # its extracted tester reduces) and names _TENSOR_LOOPFREE as the subject the
    # witness is refuted against; the creation rivals discriminate against the
    # frozen solution directly. See CARRIER NOTE.
    # =====================================================================

    # --- (b) tensorIndexLatex, TRAILING `}` dropped: the wrap only OPENS the
    # --- group. This is the reported symptom for the tensor atom — the group is
    # --- never closed, so a following exponent still collides with the interior
    # --- subscript.
    {
        "id": "reject-tensor-drop-closing-brace",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _tensor('"{".toList ++ (' + _TB + ')'),
        "witness_reference": _TENSOR_LOOPFREE,
        "refinement": (
            "opening the group but never closing it emits `{symbol^{..}_{..}` "
            "with no trailing `}`. The faithful real counterpart — a renderer "
            "that prepends `{` but not `}` — produces a token that is NOT the "
            "grouped form the tests demand, so the double superscript still "
            "binds to the interior subscript and the tensor and issue-witness "
            "assertions still fail: it does NOT resolve."),
        "rationale": (
            "REJECT from `out = wrapGroup (symbol ++ … ++ \"}\")`: the missing "
            "trailing `}` makes the returned sequence one character short of the "
            "post-image at EVERY input. Attacks feature (b), the group's closing "
            "delimiter. Refuted at symbol=\"S\", upper=[\"i\"], lower=[\"j\"] "
            "(all three binders populated, singleton runs)."),
        "witness": _tensor_witness('"S".toList', '["i".toList]', '["j".toList]'),
    },

    # --- (a)+(b) tensorIndexLatex, NO WRAP AT ALL (bare atom) — the pre-image
    # --- behaviour: return the ungrouped `symbol^{..}_{..}`. Correct on NO input.
    {
        "id": "reject-tensor-prepatch-bare-atom",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _tensor(_TB),
        "witness_reference": _TENSOR_LOOPFREE,
        "refinement": (
            "returning the bare atom with NO enclosing group is exactly the "
            "pre-image behaviour; the double superscript then renders against "
            "the un-grouped atom, which is the malformation the issue reports. "
            "It fails every grouped-form assertion — this is the state being "
            "fixed, so it does NOT resolve."),
        "rationale": (
            "REJECT from `out = wrapGroup (…)`: with no `{`/`}` the returned "
            "sequence is missing BOTH group delimiters (features (a) and (b) at "
            "once). Refuted at symbol=\"T\", upper=[] (EMPTY upper run), "
            "lower=[\"k\"] — moving `upper` to the empty list and `symbol` / "
            "`lower` off the previous rival's values."),
        "witness": _tensor_witness('"T".toList', '[]', '["k".toList]'),
    },

    # --- (a) tensorIndexLatex, WRONG OPENING delimiter: open the group with `^`
    # --- instead of `{`. Single-character divergence at the head; the closing
    # --- `}` is correct.
    {
        "id": "reject-tensor-wrong-opening-delimiter",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _tensor('"^".toList ++ (' + _TB + ') ++ "}".toList'),
        "witness_reference": _TENSOR_LOOPFREE,
        "refinement": (
            "opening with `^` instead of `{` models a change that emitted a "
            "stray superscript marker rather than a group brace: it renders "
            "`^symbol^{..}_{..}}`, a doubly-malformed token that is not the "
            "grouped form and fails every tensor rendering assertion — it does "
            "NOT resolve."),
        "rationale": (
            "REJECT from `out = wrapGroup (…)`: the head character is `^`, not "
            "the `{` the post-image opens with. Attacks feature (a) alone. "
            "Refuted at symbol=\"U\", upper=[\"m\"], lower=[] — moving `lower` "
            "to the EMPTY list and all three binders off the other rivals' "
            "values."),
        "witness": _tensor_witness('"U".toList', '["m".toList]', '[]'),
    },

    # --- (c) tensorIndexLatex, the TWO INDEX RUNS SWAPPED. Wraps correctly and
    # --- folds both runs correctly, but interpolates them at each other's
    # --- position: `symbol^{lowers}_{uppers}`. A NEAR-MISS — correct on the
    # --- whole sub-domain where the two runs coincide (in particular when both
    # --- are empty), so it needs its own witness at an input where they differ.
    {
        "id": "reject-tensor-swap-index-runs",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _tensor(
            'wrapGroup (symbol ++ "^{".toList ++ concatNames lower '
            '++ "}_{".toList ++ concatNames upper ++ "}".toList)'),
        "witness_reference": _TENSOR_LOOPFREE,
        "refinement": (
            "emitting the lower index run in the upper position and vice versa "
            "renders the atom with its two index runs transposed. The faithful "
            "real counterpart reads the two index collections in the wrong "
            "order, so it renders a token whose index placement differs from "
            "the expected one on any atom whose two runs differ, failing the "
            "tensor rendering assertion: it does NOT resolve. Note this rival "
            "wraps the group CORRECTLY, so it is invisible to any battery that "
            "only attacks the enclosing delimiters."),
        "rationale": (
            "REJECT from the atom-body half of `out = wrapGroup (symbol ++ "
            "\"^{\" ++ concatNames upper ++ \"}_{\" ++ concatNames lower ++ "
            "\"}\")`: the clause pins WHICH run lands in WHICH template slot, "
            "and this rival exchanges them — attacking feature (c), the only "
            "rival that abuses `upper` and `lower` as DISTINCT binders rather "
            "than merely varying them. NEAR-MISS: agrees with the post-image "
            "whenever upper = lower (both-empty included), so it is refuted at "
            "an input where they DIFFER and where both are multi-element: "
            "symbol=\"t\", upper=[\"a\",\"b\"], lower=[\"i\",\"j\"] (the only "
            "witness probing two-element runs, so the fold is exercised past "
            "its first step)."),
        "witness": _tensor_witness(
            '"t".toList', '["a".toList, "b".toList]', '["i".toList, "j".toList]'),
    },

    # --- (c) tensorIndexLatex, the UPPER RUN'S CONTRIBUTION DROPPED. Wraps
    # --- correctly, places the lower run correctly, but emits an empty upper
    # --- slot — ignoring the `upper` binder entirely.
    {
        "id": "reject-tensor-drop-upper-run",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _tensor(
            'wrapGroup (symbol ++ "^{".toList ++ "}_{".toList '
            '++ concatNames lower ++ "}".toList)'),
        "witness_reference": _TENSOR_LOOPFREE,
        "refinement": (
            "dropping the upper run's contribution renders the atom with an "
            "empty upper slot. The faithful real counterpart never reads that "
            "index collection, so any atom carrying upper indices renders "
            "without them and the tensor rendering assertion fails: it does NOT "
            "resolve."),
        "rationale": (
            "REJECT from the atom-body half of the clause: `concatNames upper` "
            "is pinned into the upper template slot and this rival emits "
            "nothing there, so the returned sequence is short by the upper "
            "run's characters. Attacks feature (c) and is the rival that makes "
            "`upper` a LOAD-BEARING binder: a spec that did not constrain it "
            "would admit this. Correct exactly when upper is empty — hence "
            "refuted at a POPULATED upper: symbol=\"v\", upper=[\"p\"], "
            "lower=[\"q\"]."),
        "witness": _tensor_witness('"v".toList', '["p".toList]', '["q".toList]'),
    },

    # --- (c) tensorIndexLatex, EACH INDEX NAME'S CHARACTERS REVERSED. Wraps
    # --- correctly, places both runs in the right slots, folds the right number
    # --- of names — and mangles the INTERNAL character order of each name. The
    # --- deepest near-miss in the battery: it is the IDENTITY on every run whose
    # --- names are all single-character, which is what every other witness here
    # --- uses, so it needs a MULTI-CHARACTER index name to be refuted at all.
    {
        "id": "reject-tensor-reverse-index-names",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _tensor(
            'wrapGroup (symbol ++ "^{".toList ++ concatNames (upper.map List.reverse) '
            '++ "}_{".toList ++ concatNames lower ++ "}".toList)'),
        "witness_reference": _TENSOR_LOOPFREE,
        "refinement": (
            "reversing the characters of each upper index name renders the atom "
            "with corrupted index labels. The faithful real counterpart walks "
            "each label backwards, so any atom carrying a multi-character index "
            "label renders that label mis-spelled and the tensor rendering "
            "assertion fails: it does NOT resolve. Note it wraps the group "
            "CORRECTLY, places both runs correctly, and folds the correct NUMBER "
            "of names — every structural feature (a), (b) and the run-placement "
            "half of (c) is satisfied."),
        "rationale": (
            "REJECT from the atom-body half of the clause: `concatNames upper` "
            "pins the CHARACTER CONTENT of the folded upper run, not merely how "
            "many names it draws from or where they land, and this rival permutes "
            "the characters inside each name. NEAR-MISS at the deepest level "
            "measured here — it is the IDENTITY whenever every upper name is a "
            "single character, so it AGREES with the post-image at all nine input "
            "points the other ten witnesses use (verified: the `Tester … = false` "
            "claim is refuted against this rival at each of the five shipped "
            "tensor points, including the two-element-run one). It is therefore "
            "refuted at the battery's ONLY multi-character index label: "
            "symbol=\"S\", upper=[\"xy\"], lower=[\"j\"] — the input point that "
            "makes `upper`'s per-name character content, and not just its length "
            "or position, load-bearing."),
        "witness": _tensor_witness('"S".toList', '["xy".toList]', '["j".toList]'),
    },

    # --- (c) tensorIndexLatex, the BASE SYMBOL'S characters reversed. The
    # --- `symbol`-side counterpart of the per-name reverse rival: wraps
    # --- correctly, places and folds both index runs correctly, emits a symbol of
    # --- the right LENGTH in the right slot — and mangles its character order.
    # --- Identity on every single-character symbol, which is what all six of the
    # --- previously-shipped tensor witnesses used (S/T/U/t/v/S).
    {
        "id": "reject-tensor-reverse-symbol",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _tensor(
            'wrapGroup (symbol.reverse ++ "^{".toList ++ concatNames upper '
            '++ "}_{".toList ++ concatNames lower ++ "}".toList)'),
        "witness_reference": _TENSOR_LOOPFREE,
        "refinement": (
            "reversing the base symbol's characters renders the atom under a "
            "mis-spelled base name. The faithful real counterpart reads the "
            "symbol's label backwards, so any atom whose base symbol is longer "
            "than one character renders with the wrong name while single-character "
            "ones are unaffected; the tensor rendering assertion compares against "
            "the correctly-spelled base and fails, so it does NOT resolve. It "
            "wraps the group CORRECTLY, places both index runs correctly, and "
            "preserves the atom's LENGTH."),
        "rationale": (
            "REJECT from the atom-body half of the clause: `symbol` is pinned into "
            "the template as ITSELF, not as a permutation of it or a run of the "
            "right length. NEAR-MISS: the IDENTITY at every single-character "
            "`symbol`, and MEASURED to agree with the post-image at ALL SIX input "
            "points the other tensor witnesses use — the `Tester … = false` claim "
            "is refuted against this rival at each of S/T/U/t/v/S. So `symbol` was "
            "VARIED but never ABUSED: it was single-character at every point the "
            "battery probed, exactly the blind spot the per-name-reverse rival "
            "closed for `upper`. Refuted at the battery's only MULTI-CHARACTER base "
            "symbol, symbol=\"Sq\", upper=[\"i\"], lower=[\"j\"]."),
        "witness": _tensor_witness('"Sq".toList', '["i".toList]', '["j".toList]'),
    },

    # --- (c) tensorIndexLatex, EACH LOWER INDEX NAME'S characters reversed — the
    # --- `lower`-run mirror of the shipped upper-run reverse rival. Every `lower`
    # --- name at every previously-shipped witness point was single-character, so
    # --- this rival was invisible to all of them too.
    {
        "id": "reject-tensor-reverse-lower-names",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _tensor(
            'wrapGroup (symbol ++ "^{".toList ++ concatNames upper '
            '++ "}_{".toList ++ concatNames (lower.map List.reverse) '
            '++ "}".toList)'),
        "witness_reference": _TENSOR_LOOPFREE,
        "refinement": (
            "reversing the characters of each LOWER index name renders the atom "
            "with corrupted lower index labels. The faithful real counterpart "
            "walks each lower label backwards, so any atom carrying a "
            "multi-character lower index renders it mis-spelled and the tensor "
            "rendering assertion fails: it does NOT resolve. Every delimiter "
            "feature and both run PLACEMENTS are correct."),
        "rationale": (
            "REJECT from the atom-body half of the clause: `concatNames lower` "
            "pins the CHARACTER CONTENT of the folded LOWER run. The shipped "
            "per-name-reverse rival attacks the same property on `upper` only, so "
            "a rival mangling the lower run's per-name content had nothing aimed "
            "at it. MEASURED to agree with the post-image at ALL SIX of the other "
            "tensor witness points (every `lower` name there is a single "
            "character, including the two-element run [\"i\",\"j\"]), so it is "
            "refuted at a MULTI-CHARACTER lower label: symbol=\"S\", "
            "upper=[\"i\"], lower=[\"jk\"]. Together with the symbol-reverse "
            "rival this makes the per-name character content of BOTH index runs, "
            "and of the base symbol, load-bearing."),
        "witness": _tensor_witness('"S".toList', '["i".toList]', '["jk".toList]'),
    },

    # --- (b) bDaggerLatex, TRAILING `}` dropped.
    {
        "id": "reject-bdagger-drop-closing-brace",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _BD_IMPL,
            r'    let out := "{".toList ++ ("b^\\dagger_{".toList ++ name '
            r'++ "}".toList)' "\n    return out"),
        "refinement": (
            "opening the creation-b atom's group but never closing it renders "
            "the atom with no trailing `}`, so an appended exponent still "
            "collides with the subscript — the reported symptom for the "
            "creation operator. The creation-operator and commutator rendering "
            "assertions still fail: it does NOT resolve."),
        "rationale": (
            "REJECT from `out = wrapGroup (\"b…\" ++ name ++ \"}\")`: the "
            "missing trailing `}` shortens the returned sequence at every "
            "`name`. Attacks feature (b). Refuted at name=\"0\" (the state "
            "label the reported scenario itself uses)."),
        "witness": _name_witness("bDaggerLatex", "0"),
    },

    # --- (a)+(b) bDaggerLatex, NO WRAP (bare atom) — the pre-image behaviour.
    {
        "id": "reject-bdagger-prepatch-bare-atom",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _BD_IMPL,
            r'    let out := "b^\\dagger_{".toList ++ name ++ "}".toList'
            "\n    return out"),
        "refinement": (
            "returning the bare creation-b atom with no enclosing group is the "
            "pre-image behaviour; the double superscript then renders against "
            "the un-grouped atom, which is exactly the reported malformation. "
            "It fails the creation-operator rendering assertions and does NOT "
            "resolve."),
        "rationale": (
            "REJECT from `out = wrapGroup (…)`: no `{`/`}` around the atom "
            "(features (a) and (b) at once). Refuted at name=\"5\" — moving the "
            "`name` binder off the value the other creation-b rivals use."),
        "witness": _name_witness("bDaggerLatex", "5"),
    },

    # --- (c) bDaggerLatex, the STATE NAME'S CONTRIBUTION DROPPED. Wraps
    # --- correctly and emits the whole literal template correctly, but never
    # --- interpolates `name`. A NEAR-MISS: correct at the empty name.
    {
        "id": "reject-bdagger-drop-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _BD_IMPL,
            r'    let out := wrapGroup ("b^\\dagger_{".toList ++ "}".toList)'
            "\n    return out"),
        "refinement": (
            "dropping the interpolated state name renders the creation-b atom "
            "with an empty subscript. The faithful real counterpart never reads "
            "the state's label, so every operator renders with a blank "
            "subscript instead of its own; the creation-operator and commutator "
            "rendering assertions compare against the labelled form and fail, "
            "so it does NOT resolve. This rival wraps the group CORRECTLY — it "
            "is invisible to any battery that only attacks the delimiters."),
        "rationale": (
            "REJECT from the atom-body half of `out = wrapGroup (\"b…\" ++ name "
            "++ \"}\")`: the clause pins `name` into the template and this "
            "rival omits it, so the returned sequence is short by the name's "
            "characters. Attacks feature (c) and is what makes `name` a "
            "LOAD-BEARING binder for the creation renderers: a spec that did "
            "not constrain it would admit this. NEAR-MISS — measured CORRECT at "
            "name=[] (the empty name contributes nothing, and the witness claim "
            "below does NOT hold there), so it is refuted at a NON-EMPTY name, "
            "name=\"3\", off both other creation-b rivals' values."),
        "witness": _name_witness("bDaggerLatex", "3"),
    },

    # --- (b) aDaggerLatex, TRAILING `}` dropped.
    {
        "id": "reject-adagger-drop-closing-brace",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _AD_IMPL,
            r'    let out := "{".toList ++ ("a^\\dagger_{".toList ++ name '
            r'++ "}".toList)' "\n    return out"),
        "refinement": (
            "opening the creation-a atom's group but never closing it leaves "
            "the atom unclosed; an appended exponent still collides with the "
            "subscript. The creation-a rendering assertions still fail: it does "
            "NOT resolve."),
        "rationale": (
            "REJECT from `out = wrapGroup (\"a…\" ++ name ++ \"}\")`: the "
            "missing trailing `}` shortens the returned sequence. Attacks "
            "feature (b). Refuted at name=\"0\"."),
        "witness": _name_witness("aDaggerLatex", "0"),
    },

    # --- (c) bDaggerLatex, the STATE NAME'S CHARACTERS REVERSED. The creation-side
    # --- counterpart of the tensor reverse rival: wraps correctly, emits the whole
    # --- literal template correctly, interpolates a name of the RIGHT LENGTH at
    # --- the right position, and gets its character order wrong. Identity on every
    # --- single-character name, so the three other creation-b witnesses (all
    # --- single-character labels) cannot see it.
    {
        "id": "reject-bdagger-reverse-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _BD_IMPL,
            r'    let out := wrapGroup ("b^\\dagger_{".toList ++ name.reverse '
            r'++ "}".toList)' "\n    return out"),
        "refinement": (
            "reversing the interpolated state name renders the creation-b atom "
            "with a mis-spelled subscript label. The faithful real counterpart "
            "reads the state's label backwards, so every multi-character label "
            "renders reversed while single-character ones are unaffected; the "
            "creation-operator and commutator rendering assertions compare "
            "against the correctly-spelled form and fail, so it does NOT resolve. "
            "It wraps the group CORRECTLY and preserves the atom's LENGTH, so it "
            "is invisible both to a battery that only attacks the delimiters and "
            "to one that only counts characters."),
        "rationale": (
            "REJECT from the atom-body half of `out = wrapGroup (\"b…\" ++ name "
            "++ \"}\")`: the clause pins `name` itself into the template, not "
            "merely a permutation of it or a run of the right length. NEAR-MISS: "
            "it is the IDENTITY at every single-character `name`, so it AGREES "
            "with the post-image at name=\"0\"/\"3\"/\"5\"/\"7\" — every point "
            "the other creation witnesses use (verified: the `Tester … = false` "
            "claim is refuted against this rival at name=\"0\"). It is therefore "
            "refuted at the battery's only MULTI-CHARACTER state label, "
            "name=\"ab\", which is what makes the ORDER of `name`'s characters "
            "load-bearing rather than merely its length."),
        "witness": _name_witness("bDaggerLatex", "ab"),
    },

    # --- (a) aDaggerLatex, WRONG OPENING delimiter `^`.
    {
        "id": "reject-adagger-wrong-opening-delimiter",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _AD_IMPL,
            r'    let out := "^".toList ++ ("a^\\dagger_{".toList ++ name '
            r'++ "}".toList) ++ "}".toList' "\n    return out"),
        "refinement": (
            "opening the creation-a atom with `^` instead of `{` models a "
            "change that emitted a stray superscript rather than a group brace, "
            "rendering a doubly-malformed token that is not the grouped form. "
            "It fails the creation-a rendering assertions and does NOT resolve."),
        "rationale": (
            "REJECT from `out = wrapGroup (…)`: the head character is `^`, not "
            "the `{` the post-image opens with. Attacks feature (a). Refuted at "
            "name=\"7\" — moving the `name` binder off the other creation-a "
            "rival's value."),
        "witness": _name_witness("aDaggerLatex", "7"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The nagini sibling contracts THREE byte-identical
# renderers over a `List[int]` code-point carrier, each taking one opaque `body`
# to be wrapped, and swaps ALL THREE impl regions uniformly per case. This velvet
# bundle models the same three renderers as three DISTINCT methods over a
# `List Char` carrier — and gives the tensor renderer its full (symbol,
# upper-run, lower-run) structure rather than a single opaque `body`
# (mapping.md §1-2). So each nagini uniform swap becomes one or more per-method
# cases here, and the tensor renderer's decomposed inputs open an attack surface
# nagini's opaque `body` does not have (the run-swap and dropped-run rivals).
#
#   nagini case                          -> here
#   ---------------------------------------------------------------------
#   pos-control-empty-init-append-open   -> pos-tensor-inline-wrap /
#                                           pos-tensor-loopfree-reference /
#                                           pos-bdagger-return-wrap-directly /
#                                           pos-adagger-rename-drop-out-let  RE-EXPRESSED (x4)
#   admiss-f2p-bdagger-body              -> admiss-f2p-shaped-tensor      RE-EXPRESSED
#   frame-mutation-store-body (3a)       -> (none)                        VACUOUS
#   frame-mutation-append-body (3b)      -> (none)                        VACUOUS
#   partial-drop-closing-brace (4)       -> reject-{tensor,bdagger,adagger}-drop-closing-brace  PORTED (x3)
#   partial-drop-last-body-char (4b)     -> reject-bdagger-drop-name      RE-EXPRESSED
#   partial-wrong-opening-delimiter (4c) -> reject-tensor-wrong-opening-delimiter /
#                                           reject-adagger-wrong-opening-delimiter  PORTED (x2)
#   prepatch-bare-body-no-braces (5)     -> reject-tensor-prepatch-bare-atom /
#                                           reject-bdagger-prepatch-bare-atom  PORTED (x2)
#   vacuous-nonterminating-loop (6)      -> (none — TOOLING + SPEC-CLOSED)  NOT PORTABLE
#   AXIOM_TESTS (ax-sound…)              -> (none)                        DROPPED (G-AX lane)
#   (no nagini counterpart)              -> reject-tensor-swap-index-runs /
#                                           reject-tensor-drop-upper-run   CARRIER-NEW (x2)
#   (no nagini counterpart)              -> reject-tensor-reverse-index-names /
#                                           reject-bdagger-reverse-name    AUDIT-NEW (x2)
#   (no nagini counterpart)              -> reject-tensor-reverse-symbol /
#                                           reject-tensor-reverse-lower-names  AUDIT-NEW (x2)
#
# RE-EXPRESSED (positive control): the nagini positive reshapes the impl (seed
#   the open brace by an explicit append rather than a list literal) and stays
#   correct. Re-expressed here as one structurally-different correct reshape per
#   method, plus the loop-free tensor reference (a control-flow reshape, not just
#   a let-binding one) which the tensor reject lane also needs as its witness
#   subject. All four VERIFY (checked during authoring); a failure would be
#   SPEC-TOO-STRONG.
# RE-EXPRESSED (partial-drop-last-body-char 4b): the nagini rival stops the copy
#   loop one element early, dropping the last body character — CORRECT on the
#   empty body, wrong on every non-empty one. What that case really tests is a
#   rival that gets the WRAP right and the CONTENT wrong, on a proper sub-domain.
#   On this carrier there is no element-by-element copy loop to shorten, but the
#   same shape is available and is now carried by reject-bdagger-drop-name: it
#   wraps correctly, drops the input's contribution to the atom, and is likewise
#   correct exactly on the empty input (measured: the witness claim holds at
#   name="3" and does NOT hold at name=[]). A previous revision of this manifest
#   recorded 4b as SUBSUMED by the drop-closing-brace rivals; that was wrong —
#   those rivals are wrong on EVERY input, so they never exercise the sub-domain
#   split, and they mangle the wrap rather than the content. Ported properly.
# CARRIER-NEW (reject-tensor-swap-index-runs, reject-tensor-drop-upper-run): no
#   nagini counterpart exists because nagini models the renderer's input as ONE
#   opaque `body` already assembled, so there is no run-placement or per-run
#   contribution to get wrong. This bundle's tensor postcondition pins three
#   binders into three distinct template slots, and a rival that transposes two
#   of them or ignores one satisfies every delimiter-shaped clause while
#   returning the wrong sequence. Without these two, `upper` and `lower` would be
#   merely VARIED by the witnesses and never ABUSED — a rival mishandling only
#   the index runs would verify and the battery would not notice.
# AUDIT-NEW (reject-tensor-reverse-index-names, reject-bdagger-reverse-name): no
#   nagini counterpart and no carrier-shape reason — these close a measured GAP in
#   this battery's own input coverage, found by the independent audit of the
#   ported manifest. Every witness the port shipped states its refutation at a
#   SINGLE-CHARACTER label, and a rival that permutes the characters INSIDE a
#   label is the identity on exactly that sub-domain. Measured with real builds: a
#   per-name-reversing tensor rival and a name-reversing creation rival are both
#   REJECTED by the frozen spec (so the spec is not weak here — no spec_holes
#   entry), but the `Tester … = false` claim at every one of the port's nine input
#   points is REFUTED against them, i.e. they agree with the post-image at each.
#   Without a multi-character label the battery could not have discriminated
#   either, so `upper`'s per-name character content and `name`'s character ORDER
#   were varied-but-not-abused. These two rivals make them load-bearing.
# RE-EXPRESSED (admiss-f2p-bdagger-body): the nagini admissibility case
#   establishes the read-only-input precondition for a realistic body and asserts
#   the renderer accepts it. NONE of the three methods here declares a
#   precondition (the `pre-conditions` regions are empty), so the LITERAL
#   precondition-admits-input probe is degenerate — but an earlier revision of
#   this manifest stopped there and recorded the whole lane as VACUOUS, which left
#   the battery testing only two of the gate's three directions. "The frozen
#   obligation has no precondition" is exactly the reason the audit lane rejects:
#   the analogue on a TOTAL carrier is the obligation being UNSATISFIABLE at an
#   F2P-shaped input. That is now tested directly by admiss-f2p-shaped-tensor,
#   which discharges the tensor post-image at a concrete two-index F2P-shaped atom
#   by EVALUATION as a `have`, before closing the frozen obligation verbatim
#   (measured exit 0, in scope). The four soundness positives do NOT substitute
#   for it: they show a correct impl verifies, not that the required sequence is
#   reachable and evaluable at a specific interesting point.
# VACUOUS (frame-mutation 3a/3b): the two nagini frame rivals mutate the
#   read-only input (an indexed self-store; an append) and are rejected for
#   insufficient permission under a fractional heap permission. This backend is
#   referentially transparent — the inputs are immutable value parameters, no
#   `mut` input binder is declared, and there is no heap, aliasing, or fractional
#   permission — so there is nothing to overwrite and no permission system to
#   trip. The class is vacuous; no substitute is fabricated.
# NOT PORTABLE - TOOLING LIMIT, class CLOSED BY THE SEMANTICS
#   (vacuous-nonterminating-loop 6): see the corrected DIVERGENCE bullet in the
#   module docstring. This bundle sets termination "total", NOT "partial" as an
#   earlier revision of this file claimed, and under "total" a measure-less
#   diverging rival is REJECTED (measured: exit 1, `Decreasing annotations are
#   required in total correctness semantics`) — so the class is not admitted
#   vacuously. It is still not shippable as a witnessed reject, but for a TOOLING
#   reason that is now stated with its error text: the same diagnostic is raised
#   on the impl, so it also breaks the WITNESS file (which embeds that impl),
#   measured exit 1 with the identical message where the witness must ELABORATE.
#   The rival half of the discrimination check therefore cannot succeed and the
#   case would land `witness-unproven` (inconclusive). Rejection here is owed to
#   the TERMINATION obligation, which needs no value witness.
#   And there is NO residual measure hole, which RETRACTS what this entry used to
#   say. It claimed the obligation accepts a NON-DECREASING measure, so that
#   `while 0 < 1` + `decreasing (0 : Nat)` returning the UNGROUPED atom VERIFIES.
#   Re-measured on this cell: that rival is REJECTED, exit 1, on the measure's own
#   goal, `unsolved goals case «decreasing_1: (0 : Nat)» |- 0 < 0`. The frozen
#   header selects the real rule twice over (line 4's `set_option ... "total"`
#   itself opens the `TotalCorrectness` scope, and the file opens it explicitly),
#   and `TotalCorrectness.WPGen.forWithInvariantLoop` emits `measure b' < measure b`
#   as a goal where the `PartialCorrectness` twin would discard it. No `spec_holes`
#   entry is filed for this class: it is closed, not escalated.
# DROPPED (AXIOM_TESTS): the nagini battery's AXIOM_TESTS validate its deep
#   A-reference models against the real rendering library. This bundle has NO
#   axiomatized callee and NO deep-model reference (meta.json axioms=[],
#   deep_model_references=[]; mapping.md §3), so there is no axiom lane to
#   mirror; the axiom lane is G-AX's job and this gate ignores AXIOM_TESTS
#   regardless.
#
# BINDER / CLAUSE COVERAGE. Each of the three obligations is DEFENDED by its own
#   verifying soundness positive and ATTACKED by >=1 reject rival:
#     * tensorIndexLatex — EIGHT rivals covering the leading `{` (a), the trailing
#       `}` (b), both at once, and the ATOM BODY (c) five times. Their witnesses
#       move all three binders: symbol S/T/U/t/v/S/MULTI-CHARACTER "Sq"/S; upper
#       singleton/EMPTY/singleton/two-element/singleton/MULTI-CHARACTER-singleton/
#       singleton/singleton; lower singleton/singleton/EMPTY/two-element/
#       singleton/singleton/singleton/MULTI-CHARACTER-singleton — and the run-swap,
#       drop-upper and three character-ORDER rivals make `symbol`, `upper` and
#       `lower` load-bearing (in placement, in contribution, and in per-name
#       character content) rather than merely varied;
#     * bDaggerLatex — four rivals covering (b), (a)+(b) and (c) twice, at
#       name="0"/"5"/"3"/"ab";
#     * aDaggerLatex — two rivals covering (b) and (a), at name="0"/"7".
#   FOURTEEN reject witnesses probe THIRTEEN distinct input points (name="0" is
#   shared by the two drop-closing-brace rivals, which attack DIFFERENT methods
#   — bDaggerLatex and aDaggerLatex — so the shared spelling is not a shared
#   probe). An earlier revision of this line claimed "eleven witnesses, eleven
#   distinct points" while the battery shipped ten witnesses over nine points;
#   the counts are now stated from the manifest as it stands.
#   SIX rivals are near-misses correct on a proper sub-domain (empty name;
#   upper = lower; and the four character-ORDER rivals, which are the identity on
#   every single-character label) and each is refuted at an input that leaves
#   that sub-domain, so no rival's rationale claims a sub-domain the manifest
#   fails to demonstrate. The FOUR multi-character points ("xy" as an upper index
#   label, "ab" as a state label, "Sq" as a base symbol, "jk" as a lower index
#   label) exist because two successive audits measured that WITHOUT them four
#   genuinely wrong rivals agree with the post-image at every input point the
#   battery probed, and would have been admitted. The second audit's finding was
#   that the first had closed this blind spot for `upper`'s per-name content and
#   for `name` while leaving the identical spot open on `symbol` and on `lower`'s
#   per-name content: both were single-character at ALL SIX shipped tensor points,
#   and the reversing rival for each was measured REFUTED (i.e. in agreement with
#   the post-image) at every one of them.
#
# AXIOM_TESTS: empty. No axiomatized callee to probe; this gate ignores
#   AXIOM_TESTS regardless.
AXIOM_TESTS = []
