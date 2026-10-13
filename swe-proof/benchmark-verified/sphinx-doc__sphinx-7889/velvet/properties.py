"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-7889 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct subscriptMock`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  subscriptMock (displayName : String) (key : Key)
      return (out : Except MockErr String)
    ensures out = subscriptSpec displayName key

The method models subscripting a placeholder object by an arbitrary index and
naming the fresh placeholder after the owning module joined to the index's
textual rendering. The pure region pins the whole outcome as a total function of
the method's own two inputs:

  subscriptSpec displayName key = buildSubclass displayName (textForm key)

where ``textForm`` reduces any key to a TEXTUAL value (an already-textual key is
itself; a non-textual object becomes its textual rendering), and
``buildSubclass`` is the (unchanged) construction callee: given a module and a
name it either

  * succeeds with the display name ``module ++ "." ++ s`` when the name is
    textual (``.str s``) and admissible (carries no NUL character), or
  * fails (``Except.error .valueError``) when the textual name carries a NUL, or
  * fails (``Except.error .typeError``) when the name is NOT textual (``.obj``).

Because ``textForm key`` is ALWAYS textual, ``subscriptSpec`` SUCCEEDS for every
key — textual or not — whose rendering is admissible, producing the joined
display name. That is the load-bearing behaviour: the modeled work is to reduce
the index to its textual form BEFORE construction, so construction never fails on
the ``typeError`` leg for a non-textual index.

The sole ``ensures`` therefore pins TWO independent things about the result:

  * (BRANCH) which outcome fires — for a non-textual key the spec demands the
    SUCCESS value (via ``textForm``), not the ``typeError`` the raw key would
    produce; a rival that hands the raw key on fails here.
  * (VALUE) the produced display name — ``displayName ++ "." ++ rendering``:
    the module prefix, the ``.`` separator, and the index rendering, each pinned
    exactly. A rival that mangles the separator, drops it, drops the module
    prefix, or drops the rendering violates the ensures on the value half.

Both INPUT binders are free (the ``pre-conditions`` region is EMPTY) and the
post-image must hold for EVERY value of each:
  * ``displayName`` — the owning module's display name; the value prefix.
  * ``key`` — the subscription index, in either shape (``.str`` / ``.obj``);
    drives the BRANCH and supplies the rendering in the VALUE.

ADVERSARIAL READ of the classes (mirrors the nagini sibling; see the footer for
the case-by-case accounting):
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The sibling's two
    MANDATORY frame-mutation rivals keep the gold body verbatim then write back
    into a read-only sequence input carrying only a fractional heap permission
    (``Acc(list_pred(...),1/2)``) and are rejected for INSUFFICIENT PERMISSION.
    Lean and Velvet are referentially transparent: every parameter is an
    immutable value, this bundle declares no ``mut`` binder, there is no heap and
    no aliasing. There is no read-only input to overwrite and no permission
    system to trip, so the class is vacuous. No substitute is fabricated.
  * DIVERGENCE / NON-TERMINATION — NOT vacuous, and NOT shippable: a KNOWN GAP
    for a TOOLING reason, recorded here rather than dressed up as an absent
    class. The sibling pins a ``MustTerminate`` obligation. This bundle runs
    under ``loom.semantics.termination "total"``, so the analogue exists and the
    spec is on the right side of it — re-measured with real builds rather than
    argued from the frozen impl's shape:
      - a loop IS in scope inside the impl region even though the frozen body is
        straight-line: prefixing the frozen body with a ``while`` carrying
        ``invariant`` / ``done_with`` / ``decreasing`` clauses and a genuinely
        decreasing measure still VERIFIES (exit 0), so "there is no loop to
        spin" is not a property of this carrier;
      - a loop with NO ``decreasing`` clause is REJECTED with ``error:
        Decreasing annotations are required in total correctness semantics``;
      - a loop whose ``decreasing`` measure does NOT decrease is REJECTED with
        the residual measure goal ``⊢ n + 1 < n``.
    So a diverging rival is expressible and the frozen artifact's termination
    semantics genuinely rejects it, on the measure's own goal rather than only at the
    annotation linter. (An earlier version of this passage excluded the cell from a
    ``partial``-semantics spec hole recorded in an internal findings doc. There is no
    such cohort: all 500 velvet bundles set ``"total"`` and open ``TotalCorrectness``,
    and the ``set_option`` elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``), so the option and the ``open``
    cannot disagree.) What blocks shipping
    it as a reject CASE is the witness half, not the spec: the gate requires the
    witness to ELABORATE against the rival, and a loop-bearing rival's extracted
    tester does not reduce. Every witness form tried against such a rival fails
    (exit 1): the shipped ``simp``/``split <;> decide`` shape stops at
    ``Expected type must not contain free variables``; ``decide +revert`` at
    ``failed to synthesize Decidable (∀ out, NonDetT.run (... forIn
    Lean.Loop.mk ...) = DivM.res out → ...)``; a bare ``decide`` at ``did not
    reduce to `isTrue` or `isFalse```; and splitting the tester leaves the
    un-normalised ``forIn Lean.Loop.mk`` term as an unsolved goal. A
    ``witness_reference`` does not help either — the blocker is on the RIVAL
    side, which no reference can substitute for. That is an inconclusive
    ``witness-unproven``, which would FAIL this gate, so no case is shipped and
    the class is recorded as an open gap in the CASE lane (not in the spec).
    The cause is structural, not a missing incantation, so it is recorded here
    to save the next port the search: a ``while`` becomes a partial-fixpoint
    ``Loop.forIn.loop`` over the ``DivM`` carrier, which is ``noncomputable`` and
    so opaque to kernel reduction — ``decide``/``simp``/``whnf`` cannot evaluate
    it at any input. The generated tester DOES route divergence to a violation
    (``| DivM.res ret => decide post | _ => false``), but that arm is unreachable
    by reduction because the scrutinee never normalises. And the supporting
    library is one-directional: every available loop result derives
    ``triple pre loop post`` FROM an invariant (plus a measure under ``total``),
    i.e. it proves a loop MEETS a postcondition; nothing proves a loop DIVERGES.
    Landing this case therefore needs a new lemma, not a better tactic — the one
    visible route is fixpoint induction on ``Loop.forIn.loop`` (``DivM``'s order
    is flat with ``.div`` as bottom, so an ``= .div`` motive is admissible), which
    no bundle in this corpus has built.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is ``subscriptSpec displayName key``, and ``subscriptSpec`` / ``textForm`` /
    ``buildSubclass`` / ``nameRejected`` are concrete ``def``s in the ``pure``
    region computing the outcome from the method's own arguments (the ``axioms``
    region is EMPTY — ``buildSubclass`` is an A-reference deep model, not an
    opaque answer key). The unique satisfier IS the grounded construction, so
    there is no wrong echo to build; the honest controls are the cheapest
    faithful reshapes (the ``pos-*`` cases).
  * CONTROL-FLOW-EFFECT — captured by the value abstraction, not lost to it. The
    modelled raise path (the TypeError the pre-patch produced on a non-textual
    index) IS the ``Except.error .typeError`` leg of the return carrier, so the
    fork is fully observable to the ensures; the ``raw-index`` rival is its
    discriminator.
  * PARTIAL-DOMAIN / VALUE — heavily exercised. A rival can be correct on part of
    the value domain yet diverge elsewhere: ``omit-key`` is right on the
    degenerate empty index yet wrong on every non-empty one; ``wrong-separator``
    is right on length/prefix/rendering and wrong only on the one separator
    character.

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is STRAIGHT-LINE (no loop):
its extracted program reduces once the model ``def``s are unfolded. Each reject
rival carries a machine-checked refutation ``witness`` — a Velvet tester
statement ``subscriptMockTester <displayName> <key> = false`` at ONE concrete
input, checked in a file whose ``prove_correct`` block has been stripped so no
tactic script can mask the verdict. (``prove_postcondition_decidable_for`` cannot
on its own synthesize ``DecidableEq`` for the ``Except MockErr String`` return
carrier, so each witness first ``deriving instance DecidableEq for Except`` — an
instance, not an assumption: no ``axiom`` / ``sorry`` / ``native_decide`` is
involved, and the frozen solution rejects the witnesses all the same.) ``decide``
alone gets STUCK reducing the ``String`` ``Except`` equality, so each witness
first ``simp``-unfolds the tester / exec / model ``def``s and then closes the
residual literal (in)equality with ``split <;> decide``. Both halves were checked
out-of-band with ``scripts/lean_verify.sh``: every witness ELABORATES against its
rival and FAILS against the frozen solution, so each rejection is a genuine spec
refutation and not mechanical tactic breakage.

The gold-side failures were additionally checked to TRACK THE CLAIM rather than
to be mechanical: dropping the closing tactic and reading what ``simp`` leaves
prints ``⊢ False`` on the frozen solution (``simp`` fully evaluated the concrete
claim and reduced the false assertion to ``False``) against a residual concrete
(in)equality such as ``¬Except.ok "m/A" = ... Except.ok "m.A"`` on the rival. The
flipped-claim control — the same witness asserting the tester returns ``true``,
i.e. that the frozen solution is WRONG there — fails on the frozen solution with
a DIFFERENT error (``No goals to be solved``: the claim was already discharged),
so the exit code carries information about the claim and not merely about the
tactic.

ONE sub-domain is out of reach of a literal-input witness on this carrier, and it
is reached by hypothesis instead. ``String.contains`` — the admissibility guard's
scan — does not reduce in the kernel at ANY literal: ``decide``,
``decide +kernel``, ``rfl`` and ``simp`` all stall even on ``"ab".contains 'x'``,
and rewriting the literal to ``String.mk [..]`` does not help. So the fork where
the guard FIRES cannot be refuted at a concrete name; ``wrong-refusal-outcome``
and ``guard-skipped-on-coerced`` state their refutations for an arbitrary name
ASSUMED to trip the guard, which is sound because the assumption is satisfiable
(nothing derives ``False`` from it, and the gate's own consistency probe confirms
this — measured: the probe file fails to derive ``False``, exit 1). Those two
witnesses discriminate SYMMETRICALLY, which is the strongest form available: each
elaborates against its rival and fails on the frozen solution, and its
flipped-claim control elaborates against the FROZEN solution (exit 0) and fails
against the rival (exit 1) — so the exit code tracks the CLAIM, not the tactic.

The irreducibility itself was re-measured rather than inherited: ``decide``,
``decide +kernel``, ``rfl``, ``simp`` and ``simp [String.contains, String.any]``
all fail on ``nameRejected`` at a literal, in BOTH directions (an admissible
``"ab"``/``"~T"`` and a NUL-carrying ``"a\x00b"``), and equally after rewriting
the literal as ``String.mk [Char.ofNat 0]``; the residual goal is always the
un-reduced ``String.anyAux`` scan (e.g. ``⊢ ("a\x00b".any fun a => a ==
Char.ofNat 0) = true``). Only ``native_decide`` closes it, and that is a banned
token. So the hypothesis-conditioned form is forced by the carrier, not chosen
for convenience.

AXIOM lane: DROPPED. The axiom lane is G-AX's job and this gate ignores
``AXIOM_TESTS``. ``buildSubclass`` is a deep-model A-reference (validated ==
the real construction callee by G-AX), not a consumed axiom; ``meta.json``
declares no consumed axiom.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7889"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — everything strictly BETWEEN the method's
# `-- impl-start` / `-- impl-end` (marker lines included). Every rival and
# reshape edits ONLY this block (and, for reshapes/admissibility, the elided
# `prove_correct` tactic body), so the spec view is untouched and same_spec
# holds by construction.
_IMPL = (
    "    -- impl-start\n"
    "    -- Take the textual form of the key BEFORE handing it to construction, so\n"
    "    -- the name passed in is always textual and construction never fails.\n"
    "    let name := textForm key\n"
    "    let out := buildSubclass displayName name\n"
    "    return out\n"
    "    -- impl-end"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A reshape that changes the impl's syntactic form
# may retune THIS block (elided from the spec view); rivals leave it as-is (the
# rejection is carried by the witness, not the tactic script).
_PROOF = "prove_correct subscriptMock by\n  loom_solve"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL,
                 "    -- impl-start\n" + new_body + "\n    -- impl-end")


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery:
# ---- `subscriptMockTester <displayName> <key> = false` says the extracted
# ---- program's result violates the postcondition at that concrete input.
# ---- Checked in a file whose `prove_correct` block is stripped. The
# ---- `Except MockErr String` return carrier needs a decidable-equality
# ---- instance for the tester derivation; it is derived, not assumed.
_DEC = "deriving instance DecidableEq for Except\n\n"
_TESTER = (_DEC +
           "extract_program_for subscriptMock\n"
           "prove_precondition_decidable_for subscriptMock\n"
           "prove_postcondition_decidable_for subscriptMock\n"
           "derive_tester_for subscriptMock\n\n")

# `decide` stalls on the `String`/`Except` literal equality, so first unfold the
# tester / exec / model `def`s with `simp`, then close the residual literal
# (in)equality with `split <;> decide`.
_WTAC = (
    "  simp [subscriptMockTester, subscriptMockExec, subscriptMock, "
    "NonDetT.run, buildSubclass, subscriptSpec, textForm, nameRejected]\n"
    "  split <;> decide\n"
)


def _witness(call):
    return _TESTER + f"example : {call} = false := by\n{_WTAC}"


# ---- witness at a point described by HYPOTHESIS rather than by a literal.
# ---- The admissibility guard `nameRejected` is a `String.contains` scan, and
# ---- `String.contains` does NOT reduce in the kernel at ANY literal (measured:
# ---- `decide`, `decide +kernel`, `rfl` and `simp` all stall on
# ---- `"ab".contains 'x' = false`, and equally on a NUL-carrying literal, even
# ---- after rewriting the literal to `String.mk [..]`). So the inadmissible
# ---- sub-domain — the one where the guard FIRES — is unreachable by a
# ---- literal-input witness on this carrier. It is reachable by hypothesis: the
# ---- refutation is stated for an arbitrary name `s` ASSUMED to trip the guard,
# ---- which is exactly the technique for a term no tactic can compute. The
# ---- hypothesis is satisfiable (nothing derives `False` from
# ---- `nameRejected s = true`, and the gate's own consistency probe confirms
# ---- it), so the refuted input exists.
def _witness_guarded(call):
    return _TESTER + (
        "example (s : String) (h : nameRejected s = true) :\n"
        f"    {call} = false := by\n"
        "  simp [subscriptMockTester, subscriptMockExec, subscriptMock, "
        "NonDetT.run, buildSubclass, subscriptSpec, textForm, h]\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the produced value identical and
    # only reshapes the executable surface, so the reproof stays close to (or
    # equal to) the frozen `loom_solve`.
    # =====================================================================
    {
        "id": "pos-match-inline",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: instead of naming `textForm key` and then constructing,
        # match the key shape directly and construct from the textual value in
        # each arm. Both arms feed a `.str` name, so the produced value is
        # identical to gold on every input. The do-block changed shape, so the
        # proof is retuned (still a `simp_all` away from `loom_solve`).
        "module": _impl_reproved(
            "    -- Match the key shape directly, constructing from the textual\n"
            "    -- value in each arm; both arms feed a textual name.\n"
            "    let out := match key with\n"
            "      | .str s => buildSubclass displayName (.str s)\n"
            "      | .obj s => buildSubclass displayName (.str s)\n"
            "    return out",
            "prove_correct subscriptMock by\n"
            "  loom_solve <;> simp_all [subscriptSpec, buildSubclass, textForm]"),
        "rationale": "matching the key shape and constructing from the textual "
                     "value in each arm feeds `buildSubclass` exactly the same "
                     "textual name gold's `textForm key` does, so "
                     "`out = subscriptSpec displayName key` still holds on every "
                     "input; a correct reshape must verify, else SPEC-TOO-STRONG "
                     "on the inline-vs-named coercion axis.",
    },
    {
        "id": "pos-name-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the textual name and the construction result to typed
        # locals (rename `out` -> `result`) before returning. Pure renaming /
        # local-binding; the value flow is identical, so the frozen `loom_solve`
        # still closes the proof unchanged.
        "module": _impl(
            "    -- Bind the textual name and the construction result to typed\n"
            "    -- locals before returning; pure renaming, same value flow.\n"
            "    let name : Key := textForm key\n"
            "    let result := buildSubclass displayName name\n"
            "    return result"),
        "rationale": "binding the textual name and the result to typed locals is "
                     "a pure renaming of the frozen body, so the produced value "
                     "and thus `out = subscriptSpec displayName key` are "
                     "unchanged; a correct reshape must verify (the frozen "
                     "`loom_solve` closes it unchanged), else SPEC-TOO-STRONG on "
                     "local naming.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO precondition (the pre-conditions
    # region is EMPTY), so the sibling's "a normal parametrised-generic index
    # satisfies the precondition" probe has no direct analogue: every input is
    # in-domain and there is no `Requires` to establish. The analogue on a TOTAL
    # carrier is the obligation being UNSATISFIABLE at exactly an F2P-shaped
    # input, which is what this case tests: it discharges the frozen obligation's
    # own post-image, by evaluation, as a `have`-style in-region assert at the
    # concrete F2P point (the parametrised-generic index, rendered "~T", modeled
    # as a non-textual `.obj` key), BEFORE closing the frozen obligation
    # verbatim. Three conjuncts, each independently load-bearing:
    #   (1) the obligation is SATISFIABLE at that point, and at the value the
    #       desired behaviour demands: `subscriptSpec "mod" (.obj "~T")` is
    #       `Except.ok "mod.~T"` — this is the sibling's "the precondition admits
    #       the normal parametrised-generic index" clause, re-aimed at the
    #       obligation itself. Guarded by the admissibility hypothesis, because
    #       the guard is not kernel-reducible here (see `_witness_guarded`); the
    #       hypothesis is discharged for "~T" by the real construction operation
    #       and is what makes the F2P point in-domain at all.
    #   (2) the coercion's rendering at that point is the textual value "~T" —
    #       so the fork is not degenerate by the coercion doing nothing;
    #   (3) the RAW key at that same point lands on the `typeError` leg — so the
    #       fork is not degenerate by construction succeeding anyway. Together
    #       (2)+(3) say the coercion genuinely moves this input from failure to
    #       success, which is the whole modeled behaviour.
    # Each conjunct was checked LIVE: replacing any one of them with a false
    # claim (wrong success value, obligation claimed unsatisfiable at the F2P
    # point, wrong rendering, raw key claimed to succeed, wrong module prefix)
    # makes the case FAIL to verify. The rest of the impl is kept verbatim so the
    # method's own obligation still discharges; the proof is retuned to also
    # close the assert.
    # =====================================================================
    {
        "id": "admiss-coercion-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    -- At the F2P-shaped point — the parametrised-generic index,\n"
            "    -- rendered \"~T\" as a non-textual key — the obligation is\n"
            "    -- SATISFIABLE and at the demanded value, the coercion's\n"
            "    -- rendering is textual, and the RAW key would fail: the modeled\n"
            "    -- fork is live, not degenerate.\n"
            "    assert (with_name_prefix `assert\n"
            "      ((nameRejected \"~T\" = false →\n"
            "         subscriptSpec \"mod\" (.obj \"~T\") = Except.ok \"mod.~T\") ∧\n"
            "       textForm (.obj \"~T\") = Key.str \"~T\" ∧\n"
            "       buildSubclass \"mod\" (.obj \"~T\") = Except.error MockErr.typeError))\n"
            "    let name := textForm key\n"
            "    let out := buildSubclass displayName name\n"
            "    return out",
            "prove_correct subscriptMock by\n"
            "  loom_solve <;>\n"
            "    refine ⟨fun hadm => ?_, rfl, rfl⟩ <;>\n"
            "    simp [subscriptSpec, buildSubclass, textForm, nameRejected] "
            "at hadm ⊢ <;>\n"
            "    simp [hadm]"),
        "rationale": "the frozen obligation is SATISFIABLE at an F2P-shaped "
                     "input, and satisfiable at the value the desired behaviour "
                     "demands: at the parametrised-generic index (a non-textual "
                     "key rendering \"~T\", admissible as a class name) the "
                     "post-image is `Except.ok \"mod.~T\"` — discharged by "
                     "evaluation in-region, so a spec that was unsatisfiable "
                     "exactly there (the total-carrier analogue of "
                     "PRECOND-TOO-STRONG) would fail this case. It further pins "
                     "the fork as non-degenerate from both sides: the coercion's "
                     "rendering is a textual value, and the RAW key at the same "
                     "point lands on the `typeError` leg — so the coercion really "
                     "does move the input from failure to success, rather than "
                     "the obligation holding because construction never failed. "
                     "The impl is kept verbatim so the ensures still discharges "
                     "too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is straight-line, refuted at a concrete input
    # by a witness that FAILS on the frozen solution, and carries the refinement
    # argument that its faithful real counterpart would NOT resolve the F2P.
    # =====================================================================
    {
        "id": "raw-index-no-coercion",
        "kind": "uniqueness",
        "expect": "reject",
        # PRE-PATCH SHAPE: hand the key on UNCHANGED, without taking its textual
        # form. For a non-textual index this lands on the `typeError` leg instead
        # of the success value the spec demands — the modelled image of the real
        # failure on a parametrised-generic index.
        "module": _impl(
            "    -- Hand the key to construction UNCHANGED, without taking its\n"
            "    -- textual form first.\n"
            "    let out := buildSubclass displayName key\n"
            "    return out"),
        "refinement": "this IS the pre-patch: constructing from the raw index "
                      "fails on a non-textual (parametrised-generic) index, so "
                      "building a subclass of a generically-typed placeholder "
                      "fails at construction time. The F2P test builds exactly "
                      "such a subclass and asserts it succeeds; the pre-patch "
                      "raises instead — it does NOT resolve (it is the exact bug "
                      "the change fixes, the precise discriminator G-DIFF senses).",
        "rationale": "REJECT from `out = subscriptSpec displayName key` on the "
                     "BRANCH: for a non-textual `.obj` key the post-image demands "
                     "the success value `buildSubclass displayName (textForm key)`, "
                     "but the rival produces `Except.error .typeError`. Refuted at "
                     "a non-textual key (`.obj \"T\"`) — the sub-domain where the "
                     "coercion matters and every value rival below (which uses a "
                     "textual key) is silent.",
        "witness": _witness('subscriptMockTester "m" (.obj "T")'),
    },
    {
        "id": "wrong-separator",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN / VALUE: correct outcome (always succeeds on a textual
        # key) and correct module prefix + rendering, but joins them with "/"
        # instead of the "." the spec pins.
        "module": _impl(
            "    -- Join the module prefix and the index rendering with the wrong\n"
            "    -- separator character.\n"
            "    let s := match key with | .str s => s | .obj s => s\n"
            "    let out : Except MockErr String := Except.ok (displayName ++ \"/\" ++ s)\n"
            "    return out"),
        "refinement": "a faithful patch joining the module and the index "
                      "rendering with the wrong separator would name every "
                      "placeholder with a corrupted dotted path (e.g. `mod/T` "
                      "instead of `mod.T`); the F2P/P2P tests observe the "
                      "constructed placeholder's display name, and any consumer "
                      "reading that path would see the wrong module — it would "
                      "NOT resolve.",
        "rationale": "REJECT from `out = subscriptSpec displayName key` on the "
                     "VALUE: the post-image joins with `.` (the `buildSubclass` "
                     "success value `module ++ \".\" ++ s`), the rival joins with "
                     "`/`, so the produced display name differs on the one "
                     "separator character. Refuted at a textual key (`.str \"A\"`) "
                     "with a non-empty module (`\"m\"`), where the separator is "
                     "observable.",
        "witness": _witness('subscriptMockTester "m" (.str "A")'),
    },
    {
        "id": "drop-separator",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN / VALUE: correct outcome and correct components, but the
        # separator is DROPPED entirely — `module ++ rendering`, off by the one
        # separator character. Refuted at a NON-textual key to vary the `key`
        # binder shape against the other value rivals.
        "module": _impl(
            "    -- Concatenate the module prefix and the index rendering with NO\n"
            "    -- separator between them.\n"
            "    let s := match key with | .str s => s | .obj s => s\n"
            "    let out : Except MockErr String := Except.ok (displayName ++ s)\n"
            "    return out"),
        "refinement": "a faithful patch concatenating the module and the index "
                      "rendering without a separator would lose the dotted module "
                      "path in the placeholder's display name (`pkgB` instead of "
                      "`pkg.B`); the tests observe that display name — it would "
                      "NOT resolve.",
        "rationale": "REJECT from `out = subscriptSpec displayName key` on the "
                     "VALUE: the post-image inserts the `.` separator, the rival "
                     "omits it, so the produced name is off by one character. "
                     "Refuted at a NON-textual key (`.obj \"B\"`) with module "
                     "`\"pkg\"` — varying the `key` binder shape (an `.obj`, where "
                     "the coercion has also fired) against the textual-key value "
                     "rivals.",
        "witness": _witness('subscriptMockTester "pkg" (.obj "B")'),
    },
    {
        "id": "omit-key-render",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN / VALUE: return `module ++ "."` and NEVER append the
        # index rendering. Correct on the degenerate empty index, wrong on every
        # non-empty one.
        "module": _impl(
            "    -- Build the module prefix and separator but never append the\n"
            "    -- index rendering.\n"
            "    let out : Except MockErr String := Except.ok (displayName ++ \".\")\n"
            "    return out"),
        "refinement": "a faithful patch that named every placeholder `module.` "
                      "(dropping the index entirely) would give distinct "
                      "subscripts the SAME display name — `SomeClass[T]` and "
                      "`SomeClass[U]` would collide on `mod.`; the F2P/P2P tests "
                      "build distinct subclasses and would get an "
                      "indistinguishable (wrong) display name — it would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = subscriptSpec displayName key` on the "
                     "VALUE: the post-image appends the index rendering "
                     "(`... ++ \".\" ++ s`), the rival stops at `module ++ \".\"`, "
                     "so it disagrees on every non-empty index. Refuted at a "
                     "textual key (`.str \"C\"`) with a non-empty rendering — the "
                     "sub-domain where dropping the rendering is observable "
                     "(correct only on the degenerate empty index).",
        "witness": _witness('subscriptMockTester "q" (.str "C")'),
    },
    {
        "id": "drop-module-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN / VALUE on the `displayName` binder: correct outcome and
        # correct rendering, but the produced name is JUST the index rendering —
        # the module prefix and separator are dropped. Built to abuse
        # `displayName`, the value's prefix: every other value rival keeps the
        # module prefix, so none of them attests the produced name DEPENDS on
        # `displayName`. This one is wrong exactly because it drops it (correct
        # only on the degenerate empty module).
        "module": _impl(
            "    -- Return just the index rendering; drop the module prefix and\n"
            "    -- the separator.\n"
            "    let s := match key with | .str s => s | .obj s => s\n"
            "    let out : Except MockErr String := Except.ok s\n"
            "    return out"),
        "refinement": "a faithful patch naming the placeholder after the index "
                      "alone (dropping the owning module) would strip the module "
                      "path from every placeholder's display name (`A` instead of "
                      "`mod.A`); the tests observe that display name — it would "
                      "NOT resolve.",
        "rationale": "REJECT from `out = subscriptSpec displayName key` on the "
                     "VALUE, abusing the `displayName` binder: the post-image "
                     "prefixes the produced name with `displayName ++ \".\"`, the "
                     "rival drops it. Refuted at a NON-empty module (`\"mod\"`) "
                     "with a textual key — the sub-domain where the missing prefix "
                     "is observable, and the only witness that makes the "
                     "post-image's dependence on `displayName` visible (correct "
                     "only on the degenerate empty module).",
        "witness": _witness('subscriptMockTester "mod" (.str "A")'),
    },
    {
        "id": "wrong-refusal-outcome",
        "kind": "uniqueness",
        "expect": "reject",
        # BRANCH, on the OTHER fork: every rival above is silent about WHICH
        # failure an inadmissible name produces — they all agree with gold there,
        # because they only ever disagree on the success value or on the
        # non-textual leg. This one is right on every admissible name (same
        # outcome, same joined value) and reports the WRONG failure for an
        # inadmissible one: the non-textual `typeError` instead of the refusal
        # `valueError` the spec pins. Refuted at a name ASSUMED inadmissible,
        # because the guard does not reduce at a literal on this carrier (see
        # `_witness_guarded`).
        "module": _impl(
            "    -- Report the non-textual failure for a name the class machinery\n"
            "    -- refuses, instead of the refusal outcome.\n"
            "    let s := match key with | .str s => s | .obj s => s\n"
            "    let out : Except MockErr String :=\n"
            "      if nameRejected s then Except.error MockErr.typeError\n"
            "      else Except.ok (displayName ++ \".\" ++ s)\n"
            "    return out"),
        "refinement": "a faithful patch that reported the non-textual failure "
                      "for a name the class machinery refuses would raise the "
                      "wrong exception type for such an index: a caller "
                      "distinguishing 'this index is not textual' from 'this "
                      "name is not admissible as a class name' — the two "
                      "distinct failures the construction operation is "
                      "documented to produce — would take the wrong recovery "
                      "path, and the two outcomes are separately observable. It "
                      "is also silently right everywhere the shipped rivals "
                      "look, so nothing else in this battery would catch it.",
        "rationale": "REJECT from `out = subscriptSpec displayName key` on the "
                     "BRANCH, at the refusal fork: the post-image demands "
                     "`Except.error .valueError` for a name carrying a NUL "
                     "character (the `nameRejected` leg of `buildSubclass`), the "
                     "rival produces `Except.error .typeError`. This is the ONLY "
                     "case attacking that leg — every other rival agrees with "
                     "gold on it — so it is what attests the spec pins WHICH of "
                     "the two failures fires, not merely that one does. Refuted "
                     "over an arbitrary name assumed to trip the guard, the "
                     "sub-domain no literal-input witness can reach here.",
        "witness": _witness_guarded('subscriptMockTester "m" (.str s)'),
    },
    {
        "id": "guard-skipped-on-coerced",
        "kind": "uniqueness",
        "expect": "reject",
        # BRANCH x KEY-SHAPE, the one cell of the behaviour table nothing else
        # reaches. `wrong-refusal-outcome` attacks the refusal fork but only at a
        # key that was ALREADY textual; `raw-index-no-coercion` attacks the
        # non-textual key but only at an admissible rendering. This rival takes
        # the textual form (so it is right on every admissible input, textual or
        # not) and then skips the admissibility guard on the coerced leg only:
        # for a NON-textual key whose rendering is inadmissible it succeeds where
        # the spec demands the refusal outcome. Refuted at a non-textual key with
        # a rendering ASSUMED to trip the guard, because the guard does not
        # reduce at a literal on this carrier (see `_witness_guarded`).
        "module": _impl(
            "    -- Take the textual form, then join the module prefix and the\n"
            "    -- rendering unconditionally for a non-textual key.\n"
            "    let out : Except MockErr String :=\n"
            "      match key with\n"
            "      | .str s => buildSubclass displayName (.str s)\n"
            "      | .obj s => Except.ok (displayName ++ \".\" ++ s)\n"
            "    return out"),
        "refinement": "a faithful patch that applied the coercion but then "
                      "bypassed the class machinery's own name check for a "
                      "coerced index would CONSTRUCT a class for a rendering "
                      "that cannot name one, instead of surfacing the refusal "
                      "the construction operation raises; a caller relying on "
                      "that failure to reject an unusable index would instead "
                      "receive a placeholder the class machinery never agreed "
                      "to build, and the two outcomes are separately "
                      "observable — it would NOT resolve.",
        "rationale": "REJECT from `out = subscriptSpec displayName key` on the "
                     "BRANCH, at the refusal fork REACHED THROUGH the coercion: "
                     "the post-image is `buildSubclass displayName (textForm "
                     "key)`, which for a non-textual key whose rendering carries "
                     "a NUL demands `Except.error .valueError`; the rival "
                     "returns `Except.ok`. This is the only case that pins the "
                     "guard as applying to a COERCED rendering and not merely to "
                     "an already-textual key — `wrong-refusal-outcome` varies the "
                     "outcome at a `.str` key, `raw-index-no-coercion` varies the "
                     "key shape at an admissible rendering, and neither crosses "
                     "the two. Refuted over an arbitrary rendering assumed to "
                     "trip the guard, at a NON-textual key.",
        "witness": _witness_guarded('subscriptMockTester "m" (.obj s)'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (1 soundness
# positive, 1 admissibility, 6 uniqueness — two of which are the mandatory
# frame-mutation rivals). Every one is accounted for below. The sibling models
# _MockObject.__getitem__ over TWO read-only `List[int]` inputs carrying
# fractional heap permissions (`key_text`, `module`), with the display content
# materialised by a verified `while` loop and a `MustTerminate` obligation; this
# backend models the same subscription STRAIGHT-LINE, with the index abstracted
# to a `Key` (textual `.str` / non-textual `.obj` carrying its rendering), the
# textual coercion as the pure `textForm`, and the whole outcome (success value
# or the modeled TypeError/ValueError legs) as `subscriptSpec` /
# `buildSubclass`. The BRANCH surface (does the non-textual index construct?) and
# the VALUE surface (`module ++ "." ++ rendering`) carry across intact; the
# permission surface, the loop, and the termination obligation do not exist here.
#
#   sibling case            -> here                              disposition
#   -----------------------------------------------------------------------
#   pos-reorder             -> pos-match-inline                  RE-SHAPED
#   admiss-tilde-T          -> admiss-coercion-nondegenerate     RE-AIMED
#   frame-module-write      -> (none)                            VACUOUS
#   frame-key-write         -> (none)                            VACUOUS
#   raw-index-no-coercion   -> raw-index-no-coercion             PORTED
#   wrong-separator         -> wrong-separator                   PORTED
#   drop-separator          -> drop-separator                    PORTED
#   omit-key-render         -> omit-key-render                   PORTED
#   (no sibling)            -> pos-name-local                    ADDED (2nd pos.)
#   (no sibling)            -> drop-module-prefix                ADDED (binder cov.)
#   (no sibling)            -> wrong-refusal-outcome             ADDED (clause cov.)
#   (no sibling)            -> guard-skipped-on-coerced          ADDED (clause cov.)
#
# 4 ported, 1 re-shaped positive, 1 re-aimed admissibility, 2 vacuous;
# 1 extra positive + 3 clause/binder-coverage rivals added.
#
# ADDED (guard-skipped-on-coerced): the behaviour table is BRANCH-fork x
#   KEY-SHAPE, and the shipped rivals cover only its diagonal —
#   `wrong-refusal-outcome` varies WHICH failure fires but only at an already
#   textual key, `raw-index-no-coercion` varies the key shape but only at an
#   admissible rendering. Neither attests that the admissibility guard applies to
#   a COERCED rendering, so an impl that coerces and then joins a non-textual
#   key's rendering unconditionally was silently right everywhere the battery
#   looked. This rival is exactly that impl; refuted at a non-textual key with a
#   rendering assumed to trip the guard.
#
# VACUOUS (frame-module-write, frame-key-write): the sibling's two MANDATORY
#   frame-mutation rivals keep the gold body verbatim then write back into a
#   read-only sequence input granted only at half permission, and must be
#   rejected for INSUFFICIENT PERMISSION. This backend is referentially
#   transparent: every parameter is an immutable value, the method declares no
#   `mut` binder, there is no heap and no aliasing. There is no read-only input
#   to overwrite and no permission system to trip, so the class is vacuous. No
#   substitute is fabricated.
# KNOWN GAP (divergence) — a TOOLING gap in the CASE lane, not a spec hole and
#   not a vacuous class. The sibling pins a `MustTerminate(2)` total-correctness
#   obligation and carries no explicit diverge-reject case (the obligation is
#   discharged inline by its bounded loop). This bundle runs under
#   `loom.semantics.termination "total"`, and the earlier claim here — that a
#   diverging impl "cannot be written at all" because the frozen body is
#   straight-line — was measured FALSE with real builds. A `while` loop is in
#   scope inside the impl region regardless of the frozen body's shape: with a
#   genuinely decreasing measure a loop-bearing impl of this spec VERIFIES
#   (exit 0); with no `decreasing` clause it is rejected for `Decreasing
#   annotations are required in total correctness semantics`; with a
#   non-decreasing measure it is rejected on the residual goal `⊢ n + 1 < n`.
#   So the rival is expressible and the spec rejects it — the correct
#   disposition is that this class is CLOSED BY THE SPEC but not shippable as a
#   case, because the witness cannot be landed: a loop-bearing rival's extracted
#   tester does not reduce (`Expected type must not contain free variables`,
#   `failed to synthesize Decidable (... forIn Lean.Loop.mk ...)`, `did not
#   reduce to `isTrue` or `isFalse``), so the witness build fails on the RIVAL
#   side — an inconclusive `witness-unproven` that would fail this gate, and one
#   a `witness_reference` cannot repair since the block is on the rival half.
#   Recorded as an open gap so it stays visible; see WITNESS MECHANICS above for
#   the measured error text.
# RE-AIMED (admissibility): the sibling's admiss-tilde-T asserts the
#   half-permission Requires predicates (list_pred ownership + NUL-free) hold of
#   the F2P-shaped index rendering "~T". This backend's method has NO
#   precondition and no permission surface, so that exact probe has no analogue
#   (every input is in-domain, there is no Requires to establish). It is re-aimed
#   at the TOTAL-carrier analogue, which is the same direction the sibling tests:
#   the obligation being unsatisfiable at exactly an F2P-shaped input. The case
#   discharges the frozen post-image AT that concrete point, by evaluation, as an
#   in-region assert — `subscriptSpec "mod" (.obj "~T") = Except.ok "mod.~T"`
#   under the admissibility hypothesis on "~T" (the direct carrier image of the
#   sibling's NUL-free Requires clause, stated as a hypothesis because the guard
#   is not kernel-reducible here) — before closing the frozen obligation
#   verbatim. It additionally pins the fork non-degenerate from both sides
#   (`textForm (.obj "~T") = .str "~T"`, and the raw key failing on the
#   `typeError` leg). Every conjunct was measured LIVE: each one replaced by a
#   false claim makes the case fail.
# RE-SHAPED (pos-match-inline): the sibling's positive control reorders the two
#   independent leading statements of its straight-line prologue and renames the
#   fabricator result. This backend's frozen body has only two dependent
#   statements (name then construct), so the exact reorder does not exist; the
#   reshape SPIRIT — "structurally different, behaviourally identical" — is
#   carried by matching the key shape and constructing from the textual value in
#   each arm. Same value on every input; the reproof is `loom_solve <;>
#   simp_all`.
# ADDED (pos-name-local): a second positive control this backend affords — bind
#   the textual name and the construction result to typed locals (renaming
#   `out`). Guards the spec against being SPEC-TOO-STRONG on local naming; the
#   frozen `loom_solve` closes it unchanged.
# ADDED (drop-module-prefix): the sibling's value rivals attack the separator and
#   the key rendering but never the MODULE PREFIX in isolation. This backend's
#   VALUE (`displayName ++ "." ++ rendering`) has an independent dependence on the
#   `displayName` binder that no other rival demonstrates — every other value
#   rival keeps the module prefix. This rival keeps the rendering exactly right
#   and drops the module prefix, refuted at a non-empty module, the point that
#   makes the post-image's dependence on `displayName` observable.
# ADDED (wrong-refusal-outcome): the ported rivals attack the BRANCH only on the
#   non-textual fork and the VALUE only on the success leg — every one of them
#   AGREES with the frozen post-image about what an INADMISSIBLE name produces,
#   so nothing in the ported set attests that the spec pins WHICH of the two
#   distinct failures fires. This rival is right on every admissible name and
#   reports the non-textual failure where the spec demands the refusal one. It is
#   also the case that forced the hypothesis-conditioned witness form: the guard
#   is not kernel-reducible at a literal on this carrier, so this sub-domain is
#   reachable only at a point described by hypothesis (see WITNESS MECHANICS).
#
# BINDER / CLAUSE COVERAGE of the reject witnesses over the two input binders of
#   the sole ensures (pts = 5 distinct input points):
#     displayName — "m" (raw-index / wrong-separator), "pkg" (drop-separator),
#                   "q" (omit-key), "mod" (drop-module-prefix): all non-empty,
#                   and drop-module-prefix's refutation DEPENDS on it being
#                   non-empty (its divergence is the dropped prefix).
#     key         — `.obj "T"` (raw-index, non-textual), `.str "A"`
#                   (wrong-separator, textual), `.obj "B"` (drop-separator,
#                   non-textual), `.str "C"` (omit-key, textual), `.str "A"`
#                   (drop-module-prefix, textual), plus an arbitrary `.str s`
#                   ASSUMED inadmissible (wrong-refusal-outcome) and an arbitrary
#                   `.obj s` ASSUMED inadmissible (guard-skipped-on-coerced):
#                   BOTH shapes
#                   exercised — the non-textual `.obj` shape is where the coercion
#                   fires (BRANCH), the textual `.str` shape isolates the VALUE
#                   clauses, and the guarded point reaches the inadmissible
#                   sub-domain the literals cannot (`String.contains` does not
#                   reduce in the kernel at any literal here).
#   Every independent behaviour of the post-image is attacked: the BRANCH on both
#   forks AND at both key shapes — does a non-textual index construct
#   (raw-index), which failure does an inadmissible ALREADY-TEXTUAL name produce
#   (wrong-refusal-outcome), and does the admissibility guard still apply to a
#   COERCED rendering (guard-skipped-on-coerced) — and each component of the
#   VALUE: the separator character (wrong-separator), the separator presence
#   (drop-separator), the index rendering (omit-key-render), and the module
#   prefix (drop-module-prefix).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# consumed axiom (`buildSubclass` is a deep-model A-reference, `textForm` an
# I-op, both checked by G-AX / G-CONF), and this gate ignores AXIOM_TESTS
# regardless.
AXIOM_TESTS = []
