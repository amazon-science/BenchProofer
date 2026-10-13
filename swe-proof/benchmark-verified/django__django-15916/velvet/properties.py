"""properties.py — G-PBT falsification battery for django__django-15916 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, where a case legitimately re-proves, the
``prove_correct`` tactic body — is changed, both elided from the consumer spec
view, so ``markers.same_spec`` holds and the ``prove_correct selectFieldCallback``
obligation survives with a byte-identical STATEMENT and header) and swaps in a
candidate implementation; it is judged by the real verifier.
``expect:"verify"`` passes iff (in scope AND the file elaborates with every
obligation closed); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` discriminates: the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one modeled method over three read-only callback sources):

  selectFieldCallback (configCallback : Option Nat)
                      (declaredCallback : Option (Option Nat))
                      (inheritedCallback : Option Nat)
      return (out : Option Nat)
    ensures out = configCallback                                 -- (Q) VALUE pin

The desired behavior: the callback a model-backed form's fields are built with
is EXACTLY the one the form's own configuration resolves to (``configCallback``),
independently of what is named directly on the class body (``declaredCallback``)
or offered as a default by a parent form (``inheritedCallback``). The method has
NO ``require`` clause, so the admitted domain is total over all three ``Option``
carriers.

CARRIER — the decisive fact of this port. There are THREE input binders but the
single postcondition clause (Q) references only ``configCallback``; the whole
correction is that the other two sources — which the PRE-image conflated into the
selection (``declaredCallback.getD inheritedCallback``, the class-body value if
named even when that value is "no callback", else the parent default) — must NOT
influence the result. So (Q) is a bare equality with NO opaque callee: the
``axioms`` region declares nothing, ``configCallback`` is a concrete ``Option
Nat`` input, and the result is that input itself. There is no answer-key to echo
(directive 8): the post-image is the input value, so a rival can only satisfy
(Q) by returning ``configCallback`` unchanged. Every rival is therefore refutable
by a FULLY TRANSPARENT ``decide`` at concrete literal inputs — no conditioning on
an opaque term is needed, and the two conflated sources are exactly the binders a
rival abuses, so the battery varies all three. Critically, (Q) is an equality and
therefore pins BOTH halves of the ``configCallback`` domain: a form whose own
configuration resolves to "no callback" must be built with no callback, so a rival
that merely *falls back* to a conflated source where the config source is absent
is as wrong as one that overrides it. The battery attacks both halves (see the
COVERAGE footer; the absent-config half was added by the 2026-08-12 audit).

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling notes this class is
    N/A even there: both modeled functions take pass-by-value ``int`` params with
    no read-only heap input under ``Acc(...,1/2)``. On this backend the same holds
    a fortiori — Lean/Velvet are referentially transparent, the three inputs are
    immutable values, no ``mut`` binder is declared, there is no heap and no
    aliasing. No read-only field to overwrite, no substitute probe. Not fabricated.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line a single ``return`` over immutable values,
    no loop and no recursion), so there is no control flow here to make
    diverge: a diverging rival cannot be obtained by mutating this body, it has
    to bring a loop of its own. When it does, the semantics refuse it. This
    bundle sets ``loom.semantics.termination "total"`` AND carries
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
  * UNGROUNDED-ORACLE ECHO — N/A. The nagini note is explicit that ``resolve_attr``
    is a pure helper FULLY UNFOLDED over the args (own if own!=0 else inherited),
    grounded in the inputs, so "echoing the answer" IS the correct answer and there
    is no wrong echo to build. Here the post-image is even more direct — the result
    is the input ``configCallback`` itself, so there is no opaque answer key. The
    nagini honest cheapest-impl positive CONTROLS port instead (the two soundness
    reshapes below).

WITNESS MECHANICS ON THIS BUNDLE. The postcondition is a ``method`` CONTRACT, not
a bare predicate, and the method is COMPUTABLE (no ``noncomputable`` opaque callee
in the impl), so each witness reaches the contract through Velvet's own tester
machinery: ``derive_tester_for selectFieldCallback`` yields
``selectFieldCallbackTester config declared inherited : Bool``, and
``selectFieldCallbackTester … = false`` says the extracted program's result
VIOLATES (Q) at that concrete input. Checked in a file whose ``prove_correct``
block is stripped, so no tactic script can mask the verdict; the method has no
``require`` clause, so every input reaches (Q). ``Option Nat``/``Option (Option
Nat)`` are all ``DecidableEq``, so every witness closes by ``decide`` at concrete
literals. Each witness ELABORATES against its rival (``= false`` provable) and
FAILS against the frozen solution (there ``= true``, so ``decide`` proves the
statement false) — both halves checked out-of-band with ``scripts/lean_verify.sh``
(rival exit 0, gold exit 1) for every reject case. No witness binds a hypothesis
over an opaque term (there is none), so ``witness-inconsistent`` cannot arise.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom`` (the three callback
sources are the input bijection, not consumed callee contracts — mapping.md §3),
so there is nothing there to probe; and the gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15916"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- The frozen impl body: the single return line the variants replace. It
# ---- lies wholly inside the one `-- impl-start` / `-- impl-end` region and is
# ---- unique in Solution.lean (the `ensures` states `out = configCallback`
# ---- WITHOUT a `return`), both asserted at load by _swap — so each edit keeps
# ---- same_spec by construction and leaves the frozen `prove_correct
# ---- selectFieldCallback` statement + header intact.
_GOLD_IMPL = "    return configCallback\n"
assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted from expected text"

# The frozen proof body. Elided from the consumer spec view, so a variant that
# reshapes the impl (and thus the goal `loom_solve` faces) may retune it — the
# obligation STATEMENT and the `prove_correct` header are untouched, so same_spec
# still holds. Anchored on the exact frozen script.
_GOLD_PROOF = "prove_correct selectFieldCallback by\n  loom_solve"
assert _BASE.count(_GOLD_PROOF) == 1, "frozen proof body drifted from expected text"


def _impl(body):
    """Full Solution.lean variant: replace the gold impl body only."""
    return _swap(_BASE, _GOLD_IMPL, body)


def _impl_proof(body, proof):
    """Reshape the impl body AND retune the `prove_correct` tactic script."""
    return _swap(_swap(_BASE, _GOLD_IMPL, body), _GOLD_PROOF, proof)


# ---- witness preamble. The spec is a `method` CONTRACT, so a witness reaches it
# ---- through Velvet's tester machinery: `selectFieldCallbackTester config
# ---- declared inherited = false` says the extracted program's result violates
# ---- (Q) at that concrete input. Checked in a file whose `prove_correct` block
# ---- is stripped, so no tactic script can mask the verdict. Every carrier
# ---- (`Option Nat`, `Option (Option Nat)`) is DecidableEq, so each witness
# ---- closes by `decide`.
def _tester():
    m = "selectFieldCallback"
    return (f"extract_program_for {m}\n"
            f"prove_precondition_decidable_for {m}\n"
            f"prove_postcondition_decidable_for {m}\n"
            f"derive_tester_for {m}\n\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify, else the post-image is SPEC-TOO-STRONG. Ports the
    # nagini positive-control ARGUMENT ("a faithful, structurally-different
    # correct impl of the same selection is not rejected"). The nagini positives
    # reshape a 2-/3-way `resolve_attr` select with explicit ifs; on this carrier
    # the selection collapses to returning `configCallback` directly, so the
    # argument is carried by two reshapes native to this carrier: a match on the
    # `Option` and an intermediate `let` binding.
    # =====================================================================
    {
        "id": "pos-config-match",
        "kind": "soundness",
        "expect": "verify",
        # Dispatch on the config source's `Option` shape and rebuild it — an
        # observationally identical reshape whose goal the frozen `loom_solve`
        # does not close on its own, so the proof is retuned (statement + header
        # byte-identical).
        "module": _impl_proof(
            "    match configCallback with\n"
            "    | none => return none\n"
            "    | some n => return (some n)\n",
            "prove_correct selectFieldCallback by\n"
            "  loom_solve <;> (cases configCallback <;> simp_all)"),
        "rationale": "PASS SOURCE = (Q) out = configCallback. Matching on the "
                     "config source and rebuilding it (`none => none`, `some n => "
                     "some n`) is observationally identical to returning it "
                     "directly, so (Q) discharges; the retuned tactic closes the "
                     "reshaped goal by case-splitting the Option. A faithful "
                     "structurally-different reshape MUST verify; if it cannot the "
                     "post-image is over-fit to the exact return FORM "
                     "(SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-config-let",
        "kind": "soundness",
        "expect": "verify",
        # Bind the config source to an intermediate local, then return it (an
        # extra binding, same semantics). The frozen `loom_solve` closes it
        # unchanged.
        "module": _impl(
            "    let selected := configCallback\n"
            "    return selected\n"),
        "rationale": "PASS SOURCE = (Q). Binding the config source to an "
                     "intermediate local `selected` and returning it is "
                     "observationally identical to the direct form, so (Q) still "
                     "discharges and the frozen `loom_solve` body closes it "
                     "unchanged. A faithful reshape MUST verify, else "
                     "SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — this method declares NO `require` clause, so the nagini
    # "a normal F2P-shaped input satisfies the precondition" probe is vacuous
    # (there is no precondition an input could violate). Re-aimed (as on
    # django__django-16819) at the residual admissibility risk on a total domain:
    # that the post-image is UNSATISFIABLE / degenerate at the decisive F2P
    # corner. Keeps the gold impl verbatim (so (Q) still discharges) and adds an
    # in-region `assert` pinning the post-image at the F2P shape of the
    # explicit-"no callback"-on-the-body configuration (`declared = some none`)
    # while the form's own configuration resolves to a real callback
    # (`config = some 1`). There the required answer (`configCallback`) must
    # DIFFER from the pre-image collapse (`declared.getD inherited = none`).
    #
    # AUDIT REPAIR (2026-08-12). The shipped assert stated this over CLOSED
    # LITERALS — `(some 1) ≠ (some none : Option (Option Nat)).getD none` — a
    # ground arithmetic fact about `Option.getD` that mentions NEITHER
    # `configCallback` NOR `declaredCallback`, so it held independently of this
    # method and of (Q); the same line discharges under any spec whatsoever, and
    # the case therefore attested nothing about the post-image's admissibility at
    # that corner. Re-stated over the METHOD'S OWN BINDERS as an implication: at
    # any input where the config source resolves to a real callback and the body
    # names an explicit "no callback", the value (Q) demands is DISTINCT from what
    # the pre-image collapse would supply. Liveness re-measured by hand: the
    # negated form (`… configCallback = declaredCallback.getD inheritedCallback`)
    # leaves `⊢ configCallback = some 1 → ¬declaredCallback = some none` unsolved
    # (lean_verify exit 1), so the assert is load-bearing, not decoration.
    # Folds nagini's two per-function admissibility cases (one function is
    # modeled here).
    # =====================================================================
    {
        "id": "admiss-f2p-config-shadows-declared-none",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(
            "    assert (with_name_prefix `assert\n"
            "      (configCallback = some 1 → declaredCallback = some none →\n"
            "        configCallback ≠ declaredCallback.getD inheritedCallback))\n"
            "    return configCallback\n",
            "prove_correct selectFieldCallback by\n  loom_solve <;> simp_all"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the F2P "
                     "corner, stated over THIS METHOD'S BINDERS: at any input where "
                     "the form's own configuration resolves to a real callback "
                     "(`configCallback = some 1`) and the class body names an "
                     "explicit \"no callback\" (`declaredCallback = some none`), the "
                     "value (Q) demands is DISTINCT from the pre-image collapse "
                     "`declaredCallback.getD inheritedCallback` — so (Q) is not "
                     "degenerate there and does not coincide with the pre-image. The "
                     "in-region assert must discharge (else the obligation is "
                     "unsatisfiable/degenerate at that F2P point => "
                     "PRECOND-TOO-STRONG); the impl is verbatim so (Q) discharges "
                     "too. The assert conditions on the binders rather than on "
                     "closed literals, so it cannot hold independently of the "
                     "method's inputs.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input that ELABORATES against the rival and FAILS against gold.
    # They attack the single clause (Q) `out = configCallback` from the distinct
    # WRONG-SOURCE angles the two conflated inputs (`declaredCallback`,
    # `inheritedCallback`) allow — exactly the sources the correction must stop
    # influencing the result. The witnesses vary all three binders (see footer).
    # =====================================================================
    {
        "id": "reject-prepatch-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-image bug (Solution_prepatch.lean): the class-body value when a
        # name is present there (EVEN an explicit "no callback"), otherwise the
        # parent default. Never consults the form's own resolved configuration.
        "module": _impl("    return (declaredCallback.getD inheritedCallback)\n"),
        "refinement": "this is the pre-image selection: the metaclass took the "
                      "class-body callback if the key was present (even when its "
                      "value was the explicit \"no callback\"), else the first "
                      "parent form's default — never the form's own configuration. "
                      "For test_custom_callback_from_base_form_meta a factory-made "
                      "subclass carries an explicit \"no callback\" on its body "
                      "while its configuration inherits a real callback; the "
                      "pre-image returns \"no callback\" and the produced field "
                      "gets the model default widget, not the custom one — so the "
                      "F2P assertion stays RED. The faithful real counterpart is "
                      "exactly what does NOT resolve.",
        "rationale": "REJECT from (Q) out = configCallback: with a class-body "
                     "explicit \"no callback\" present (`declaredCallback = some "
                     "none`) the collapse returns `none`, but (Q) demands "
                     "`configCallback = some 1`. Refuted at config=some 1, "
                     "declared=some none, inherited=some 2 — the F2P shape. "
                     "Transparent equality (`some 1 ≠ none`), decidable at concrete "
                     "literals. If it verified => SPEC-TOO-WEAK (admits the bug).",
        "witness": _tester() +
                   "example : selectFieldCallbackTester (some 1) (some none) "
                   "(some 2) = false := by\n  decide\n",
    },
    {
        "id": "reject-use-inherited",
        "kind": "uniqueness",
        "expect": "reject",
        # Return the parent's offered default, ignoring both the class body and
        # the form's own configuration. Correct only when the parent default
        # happens to equal the resolved config; wrong otherwise.
        "module": _impl("    return inheritedCallback\n"),
        "refinement": "always using a parent form's offered default corresponds to "
                      "a patch that read the base-form callback and ignored the "
                      "form's own resolved configuration. For "
                      "test_custom_callback_in_meta a form declares the callback on "
                      "its OWN configuration with no parent offering one; the "
                      "parent default is absent, so this returns \"no callback\" "
                      "and the widget is the model default — the F2P assertion "
                      "stays RED. A faithful such patch does NOT resolve.",
        "rationale": "REJECT from (Q): the rival returns `inheritedCallback`, not "
                     "`configCallback`. Refuted at config=some 3, declared=none, "
                     "inherited=some 4 (rival returns some 4, (Q) demands some 3) — "
                     "a point where the parent default differs from the resolved "
                     "config, varying the `inheritedCallback` binder to a distinct "
                     "value. Transparent (`some 4 ≠ some 3`). If "
                     "it verified => SPEC-TOO-WEAK (result leaks the parent "
                     "default).",
        "witness": _tester() +
                   "example : selectFieldCallbackTester (some 3) none "
                   "(some 4) = false := by\n  decide\n",
    },
    {
        "id": "reject-use-declared",
        "kind": "uniqueness",
        "expect": "reject",
        # Return only what is named on the class body (flattening the presence
        # layer), ignoring both the parent default and the form's own resolved
        # configuration. Correct only when the class-body name equals the resolved
        # config; wrong otherwise.
        "module": _impl("    return declaredCallback.join\n"),
        "refinement": "reading only what is named directly on the class body "
                      "corresponds to a patch that consulted the class-body "
                      "attribute instead of the form's own resolved configuration. "
                      "When the class body names a DIFFERENT callback from the one "
                      "the configuration resolves to, the produced field uses the "
                      "wrong widget; existing callback tests that route an explicit "
                      "callback through the factory (which post-image is surfaced "
                      "via the configuration) then observe the wrong widget, so a "
                      "faithful such patch does NOT resolve.",
        "rationale": "REJECT from (Q): the rival returns the flattened class-body "
                     "value `declaredCallback.join`, not `configCallback`. Refuted "
                     "at config=some 5, declared=some (some 6), inherited=none "
                     "(rival returns some 6, (Q) demands some 5). Transparent "
                     "(`some 6 ≠ some 5`). If it verified => SPEC-TOO-WEAK (result "
                     "leaks the class-body name).",
        "witness": _tester() +
                   "example : selectFieldCallbackTester (some 5) (some (some 6)) "
                   "none = false := by\n  decide\n",
    },
    {
        "id": "reject-const-none",
        "kind": "uniqueness",
        "expect": "reject",
        # Never select any callback — strictly worse than the pre-image, which at
        # least surfaced the class-body / parent value.
        #
        # AUDIT REPAIR (2026-08-12). The shipped case claimed to be a NON-SUBSUMED
        # near-miss, "wrong even where reject-prepatch-collapse agrees with gold",
        # and then refuted itself at `config=some 7, declared=none, inherited=none`
        # — a point where the pre-image collapse returns `none` too, i.e. a point
        # where BOTH rivals are wrong. Re-measured by hand: the collapse rival
        # built against the shipped witness at that very input ELABORATES
        # (lean_verify exit 0), so the collapse is wrong there as well and the
        # shipped witness did not sit at a non-subsumption point at all. The claim
        # is now DEMONSTRATED rather than asserted: the first example refutes this
        # rival at `config=some 1, declared=some (some 1), inherited=none`, where
        # the collapse returns `some 1` = `configCallback` and so AGREES with (Q)
        # (confirmed: the collapse's tester returns `true` there, exit 0) while this
        # rival still returns `none`. The both-sources-absent shape is kept as the
        # second example so no binder coverage is lost.
        "module": _impl("    return none\n"),
        "refinement": "returning \"no callback\" for every form corresponds to a "
                      "patch that never selects any field-building callback — every "
                      "callback test (F2P and P2P) then observes the model default "
                      "widget instead of the custom one, so it would NOT resolve. "
                      "GENUINELY non-subsumed by the pre-image collapse: when the "
                      "class body names the SAME callback the form's own "
                      "configuration resolves to, the collapse coincidentally "
                      "produces the right answer and the field gets the custom "
                      "widget, while this rival still produces the model default. "
                      "That is a configuration the collapse survives and this rival "
                      "does not.",
        "rationale": "REJECT from (Q): the rival returns the constant `none`, so "
                     "(Q) fails whenever `configCallback` is present. Refuted at "
                     "TWO points. (i) config=some 1, declared=some (some 1), "
                     "inherited=none — the NON-SUBSUMPTION point: the pre-image "
                     "collapse `declaredCallback.getD inheritedCallback` returns "
                     "`some 1` there and satisfies (Q), so this input separates "
                     "this rival from reject-prepatch-collapse rather than "
                     "re-refuting the same defect. (ii) config=some 7, "
                     "declared=none, inherited=none — the both-conflated-sources-"
                     "absent binder shape. Both transparent and decidable at "
                     "concrete literals. If it verified => SPEC-TOO-WEAK (result "
                     "never surfaces the config).",
        "witness": _tester() +
                   "-- (i) the NON-SUBSUMPTION point: the pre-image collapse\n"
                   "--     `declaredCallback.getD inheritedCallback` returns `some 1`\n"
                   "--     here and SATISFIES (Q), so this input attributes the\n"
                   "--     rejection to THIS rival's defect and not to the collapse's.\n"
                   "example : selectFieldCallbackTester (some 1) (some (some 1)) "
                   "none = false := by\n  decide\n\n"
                   "-- (ii) the both-conflated-sources-absent binder shape.\n"
                   "example : selectFieldCallbackTester (some 7) none "
                   "none = false := by\n  decide\n",
    },

    # =====================================================================
    # ADDED BY AUDIT (2026-08-12) — the `configCallback = none` HALF OF THE
    # DOMAIN. Every shipped reject witness pinned `configCallback` to a PRESENT
    # callback (`some 1/3/5/7`), so the battery never exercised the sub-domain
    # where the form's own configuration resolves to "no callback" and (Q)
    # therefore demands `none`. That is exactly the half where a rival can leak a
    # conflated source WITHOUT ever contradicting a shipped witness: a rival that
    # falls back to the class body or the parent default *only when the config
    # source is absent* agrees with gold at all four shipped points. Two such
    # rivals are added, one per conflated source; each is refuted at
    # `configCallback = none` with the leaked source PRESENT, so (Q) demands
    # `none` and the rival supplies a callback.
    # =====================================================================
    {
        "id": "reject-fallback-to-inherited-when-config-absent",
        "kind": "uniqueness",
        "expect": "reject",
        # Use the form's own resolved configuration when it has one, else fall
        # back to the parent form's offered default. Agrees with gold on the whole
        # `configCallback = some _` half — including every other reject witness's
        # input — and diverges only where the configuration resolves to "no
        # callback" while a parent offers one.
        "module": _impl(
            "    return (configCallback.orElse (fun _ => inheritedCallback))\n"),
        "refinement": "corresponds to a patch that reads the form's own resolved "
                      "configuration but keeps a parent form's offered default as a "
                      "fallback when the form's own configuration resolves to \"no "
                      "callback\". The desired behavior is that the form's own "
                      "configuration is authoritative in BOTH directions: a form "
                      "whose own configuration resolves to \"no callback\" must have "
                      "its fields built with no callback, even under a parent that "
                      "offers one — the parent's default is reachable only THROUGH "
                      "the configuration ancestry, never around it. A form that "
                      "deliberately resolves to \"no callback\" would silently get "
                      "the parent's widget instead of the model default, so a "
                      "faithful patch with this fallback does NOT resolve.",
        "rationale": "REJECT from (Q) out = configCallback: the rival returns "
                     "`configCallback.orElse (fun _ => inheritedCallback)`, which "
                     "differs from `configCallback` exactly when `configCallback = "
                     "none` and `inheritedCallback` is present. Refuted at "
                     "config=none, declared=none, inherited=some 2 (rival returns "
                     "some 2, (Q) demands none). This is the sub-domain NO other "
                     "reject case reaches — all four of the others pin "
                     "`configCallback` present, where this rival is CORRECT — so it "
                     "is non-subsumed by construction. Transparent (`some 2 ≠ "
                     "none`), decidable at concrete literals. If it verified => "
                     "SPEC-TOO-WEAK ((Q) would not pin the absent-config half and a "
                     "parent default could leak into it).",
        "witness": _tester() +
                   "example : selectFieldCallbackTester none none "
                   "(some 2) = false := by\n  decide\n",
    },
    {
        "id": "reject-fallback-to-declared-when-config-absent",
        "kind": "uniqueness",
        "expect": "reject",
        # Same shape, other conflated source: fall back to what is named on the
        # class body when the form's own resolved configuration is absent.
        "module": _impl(
            "    return (configCallback.orElse (fun _ => declaredCallback.join))\n"),
        "refinement": "corresponds to a patch that consults the form's own resolved "
                      "configuration first but keeps the class-body name as a "
                      "fallback when that configuration resolves to \"no callback\". "
                      "The correction makes the form's own configuration the SOLE "
                      "source: a form whose configuration resolves to \"no "
                      "callback\" must build its fields with no callback even when "
                      "something is named on the class body, since the class-body "
                      "name is no longer a source the field-building consults at "
                      "all. A form carrying a leftover class-body name would "
                      "silently get that callback's widget, so a faithful patch "
                      "with this fallback does NOT resolve.",
        "rationale": "REJECT from (Q): the rival returns `configCallback.orElse "
                     "(fun _ => declaredCallback.join)`, differing from "
                     "`configCallback` exactly when `configCallback = none` and the "
                     "class body names a callback. Refuted at config=none, "
                     "declared=some (some 9), inherited=none (rival returns some 9, "
                     "(Q) demands none). Distinct from "
                     "reject-fallback-to-inherited-when-config-absent (that one "
                     "leaks the PARENT default; this one leaks the CLASS-BODY name — "
                     "the two rivals disagree at config=none, declared=some (some "
                     "9), inherited=some 2) and non-subsumed by the other four, "
                     "which all pin `configCallback` present where this rival is "
                     "correct. Transparent (`some 9 ≠ none`). If it verified => "
                     "SPEC-TOO-WEAK (the class-body name could leak into the "
                     "absent-config half).",
        "witness": _tester() +
                   "example : selectFieldCallbackTester none (some (some 9)) "
                   "none = false := by\n  decide\n",
    },

    # =====================================================================
    # ADDED BY AUDIT (2026-08-12) — a positive control that dispatches on a
    # binder the result must IGNORE. The two shipped positives both reshape the
    # handling of `configCallback` itself (match-and-rebuild, let-binding), so
    # neither shows that the spec tolerates an impl whose CONTROL FLOW reads one
    # of the two conflated sources while its RESULT does not depend on it. That is
    # the faithful shape of a real patch that still has the other sources in hand,
    # and a spec that rejected it would be over-fit to a body that never mentions
    # them.
    # =====================================================================
    {
        "id": "pos-declared-dispatch-config-result",
        "kind": "soundness",
        "expect": "verify",
        # Branch on the class-body source's presence, return the config source in
        # BOTH branches. Verified with the frozen `loom_solve` unchanged.
        "module": _impl(
            "    match declaredCallback with\n"
            "    | none => return configCallback\n"
            "    | some _ => return configCallback\n"),
        "rationale": "PASS SOURCE = (Q) out = configCallback. Dispatching on the "
                     "class-body source's presence while returning the config "
                     "source in BOTH branches is observationally identical to "
                     "returning it directly: the result does not depend on the "
                     "branch taken. This is the faithful shape of a selection made "
                     "with all three sources in hand, so it MUST verify; if it "
                     "could not, the post-image would be over-fit to a body that "
                     "never MENTIONS the conflated sources (SPEC-TOO-STRONG), which "
                     "is a syntactic accident rather than the behavior (Q) pins.",
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING. The sibling battery has 9 SPEC cases (2 soundness
# positives, 2 admissibility, 5 uniqueness rivals) plus an EMPTY AXIOM lane, and
# contracts TWO functions over pass-by-value ints:
#   declared_form_callback(meta_own, meta_inherited)              -> resolve_attr
#   factory_form_callback(passed, base_meta_own, base_meta_inherited)
#        -> resolve_attr(passed, resolve_attr(base_own, base_inh))
# where resolve_attr is the 2-way "own if own!=0 else inherited" select, fully
# unfolded in the pure region. This velvet bundle models a NARROWER surface: the
# single purely-functional core `selectFieldCallback`, whose whole corrected
# behavior is `out = configCallback` — the form's OWN resolved configuration,
# with the two PRE-image sources (the class-body value and the parent default,
# nagini's `resolve_attr` operands) collapsed into inputs the result must now
# IGNORE (mapping.md §1.1: "the two pre-patch sources collapse, post-patch").
# Every sibling case is accounted for below.
#
#   sibling case (nagini)              -> here
#   -----------------------------------------------------------------------
#   pos-declared-branch-reorder        -> pos-config-match            PORTED (arg.)
#   pos-factory-explicit-if            -> pos-config-let              PORTED (arg.)
#   admiss-declared-f2p-shape          -> admiss-f2p-config-shadows-  RE-AIMED
#   admiss-factory-f2p-shape           -> declared-none (folded)      FOLDED
#   weak-declared-drop-own             -> reject-use-inherited        PORTED
#   weak-declared-inverted-shadow      -> (see reject-use-declared)   RE-EXPRESSED
#   weak-factory-passed-wins           -> reject-prepatch-collapse    PORTED (= pre-image)
#   weak-factory-drop-base-inherited   -> (none)                      NOT MODELED
#   weak-factory-ignore-passed         -> reject-use-inherited        FOLDED
#   AXIOM_TESTS (none)                 -> (none)                      EMPTY (G-AX)
#
# PORTED (2 positives): the nagini positives reshape the `resolve_attr` select
#   with inverted branch order / explicit nested ifs. On this carrier the
#   selection collapses to returning `configCallback`, so those exact reshapes
#   have no counterpart; the ARGUMENT ("a faithful structurally-different correct
#   impl must verify") is carried by pos-config-match (match + rebuild the Option,
#   proof retuned) and pos-config-let (intermediate let-binding, frozen proof).
# RE-AIMED / FOLDED (admissibility): the two sibling admissibility cases assert
#   the fractional-permission-free precondition (all params >= 0) admits the two
#   F2P shapes. This method declares NO `require` clause, so precondition
#   admissibility is vacuous. Re-aimed at the residual total-domain risk (the
#   post-image is degenerate/unsatisfiable at the F2P corner) with ONE case
#   (one function modeled here): an in-region live assert pins that at the
#   test_custom_callback_from_base_form_meta corner the required answer differs
#   from the pre-image collapse.
# PORTED / FOLDED / RE-EXPRESSED (rivals): the sibling rivals are the pre-image
#   bugs and near-misses of a TWO-level `resolve_attr` selection. Here the whole
#   selection is `out = configCallback`, and the wrong-source rivals are:
#     - reject-prepatch-collapse = `declaredCallback.getD inheritedCallback`, the
#       EXACT pre-image selection (Solution_prepatch.lean) — ports nagini
#       weak-factory-passed-wins / weak-declared-drop-own's "wrong source wins"
#       family, refuted on the F2P shape where the class body carries an explicit
#       "no callback".
#     - reject-use-inherited = leak the parent default (folds weak-declared-drop-
#       own and weak-factory-ignore-passed: "ignore the resolved value, use the
#       inherited/base one").
#     - reject-use-declared = leak the class-body name (re-expresses weak-declared-
#       inverted-shadow's "the other source shadows the right one" onto this
#       carrier's declared source).
#     - reject-const-none = never select — a near-miss the audit re-witnessed at
#       a genuine non-subsumption point (see the case's own note).
#     - reject-fallback-to-{inherited,declared}-when-config-absent = ADDED BY THE
#       AUDIT. These are the true velvet counterparts of the sibling's
#       "FALLBACK-DROPPED / wrong source supplies the answer where the right one
#       is empty" family, re-expressed on the binder this carrier actually has.
# RE-DERIVED BY THE AUDIT (weak-factory-drop-base-inherited): the sibling drops
#   the base form's INHERITED (grand-base Meta) fallback — a distinction of the
#   TWO-level factory resolution (`resolve_attr(passed, resolve_attr(base_own,
#   base_inh))`). The port recorded this as inexpressible carrier narrowing, and
#   the LITERAL binder claim is right: this bundle models the collapsed post-image
#   `out = configCallback`, where the base's own-vs-inherited layering is already
#   resolved into the single `configCallback` input (mapping.md §1.1), so there is
#   no separate base_inherited binder to drop. But the sibling case's ATTACK —
#   "the resolution consults one fewer source than it should, so it returns
#   nothing where the right source is empty and a further source would have
#   supplied a value" — IS expressible here, on the two conflated sources, in the
#   direction the port left uncovered: a rival that keeps a fallback the collapsed
#   selection must not have. That is
#   reject-fallback-to-{inherited,declared}-when-config-absent above, both landed
#   with machine-checked discriminating witnesses at `configCallback = none`. So
#   the omission is recorded as PARTIALLY EXPRESSIBLE and now closed, not as
#   carrier narrowing alone.
# EMPTY (axiom lane): the sibling has no @ContractOnly axiom and no consumed
#   axiom; here the `axioms` region declares nothing (the three callback sources
#   are the input bijection, not consumed callee contracts — mapping.md §3). The
#   gate ignores AXIOM_TESTS regardless.
#
# VACUOUS (frame/permission-mutation): N/A even on nagini (pass-by-value int
#   params, no read-only heap input). On this referentially-transparent backend
#   there is no `mut` binder, no heap, no aliasing — no read-only field to
#   overwrite and no substitute probe. Not fabricated.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line a single ``return`` over immutable values, no loop
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
# COVERAGE (revised by the 2026-08-12 audit). The sole obligation
# (`prove_correct selectFieldCallback`) is defended by three positives
# (pos-config-match, pos-config-let, pos-declared-dispatch-config-result) plus the
# admissibility positive, and attacked by SIX reject rivals. The single
# postcondition clause (Q) `out = configCallback` is attacked from every
# wrong-source angle the carrier allows, in BOTH halves of the `configCallback`
# domain:
#   config PRESENT — leak the class body (reject-use-declared), leak the parent
#     default (reject-use-inherited), the exact pre-image collapse of the two
#     (reject-prepatch-collapse), never select (reject-const-none);
#   config ABSENT — fall back to the parent default
#     (reject-fallback-to-inherited-when-config-absent) or to the class-body name
#     (reject-fallback-to-declared-when-config-absent) only where the form's own
#     configuration resolves to "no callback". The audit found this half
#     UNATTACKED: all four original witnesses pinned `configCallback` present, so
#     a rival leaking a conflated source only in the absent-config case agreed
#     with every one of them.
# The three input binders are varied across the reject witnesses (7 distinct
# input points over 6 cases):
#   config=some 1, declared=some none,     inherited=some 2   reject-prepatch-collapse
#   config=some 3, declared=none,          inherited=some 4   reject-use-inherited
#   config=some 5, declared=some (some 6), inherited=none     reject-use-declared
#   config=some 1, declared=some (some 1), inherited=none     reject-const-none (i)
#   config=some 7, declared=none,          inherited=none     reject-const-none (ii)
#   config=none,   declared=none,          inherited=some 2   reject-fallback-to-inherited-…
#   config=none,   declared=some (some 9), inherited=none     reject-fallback-to-declared-…
# so configCallback moves over {none, some 1,3,5,7} (BOTH `Option` shapes),
# declaredCallback over {none, some none, some (some 1/6/9)} (all three
# presence/value shapes), and inheritedCallback over {none, some 2, some 4}. No
# binder is pinned across the battery — the two conflated sources the correction
# must IGNORE are exactly the binders the rivals abuse, and each is abused in both
# directions (leaking INTO a present config and INTO an absent one), so the
# battery attests the spec's dependence on `configCallback` alone.
#
# NON-SUBSUMPTION. Each rival is refuted at an input where at least one OTHER
# rival satisfies (Q), so no case merely re-refutes another's defect: the collapse
# agrees with (Q) at reject-const-none's point (i); the two absent-config
# fallbacks are correct at all of the config-present points and disagree with each
# other at config=none, declared=some (some 9), inherited=some 2.
#
# PROBED AND NOT FOUND (audit attacks D/E, machine-checked, all builds re-run by
# hand). Four further wrong impls were tried against the frozen spec and all were
# REJECTED, so no spec hole: `configCallback.orElse inherited`,
# `configCallback.orElse declaredCallback.join` (both then ADDED above as rivals),
# `configCallback.map (fun n => n - 1 + 1)` (a `Nat`-truncation probe — refuted at
# config=some 0), and `some (configCallback.getD 0)` (collapsing "no callback" to
# a callback — refuted at config=none). Four further CORRECT reshapes were tried
# and all VERIFIED, so the post-image is not over-fit: an `isSome` if-ladder,
# `configCallback.map id`, `configCallback.orElse (fun _ => configCallback)`, and
# the declared-dispatch (kept above as a positive).
AXIOM_TESTS = []
