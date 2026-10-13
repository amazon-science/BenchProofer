"""properties.py — G-PBT falsification battery for django__django-14349 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct validateUrl`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  validateUrl (value : List Char) (baselineVerdict : BaselineOutcome)
      return (outcome : CallOutcome)
    require baselineVerdict = baselineOutcome value
    ensures outcome = (if containsForbidden value then CallOutcome.rejected
                       else liftBaseline (baselineOutcome value))

Models the entry point that screens a candidate string: a forbidden control
character anywhere in ``value`` refuses the string OUTRIGHT (``CallOutcome
.rejected``), decided WITHOUT consulting the pre-existing structural validation;
otherwise the call's outcome is exactly that unchanged validation's own three-
way ending, surfaced through ``liftBaseline`` (acceptance ↦ ``accepted``, the
designated refusal ↦ ``rejected``, an unrelated abort ↦ ``crashed``).

  * ``containsForbidden`` is a total, fully-unfolded front-recursive scan
    (``isForbidden c || containsForbidden cs``); ``isForbidden`` is grounded
    entirely in its argument (``c = '\\t' || c = '\\r' || c = '\\n'``). There is
    no opaque answer-key here.
  * ``baselineOutcome`` is the ONE opaque ``axiom`` — the deterministic three-way
    outcome of the UNCHANGED structural validation, an ``List Char →
    BaselineOutcome`` with no constraining lemma. It enters BOTH the precondition
    (``baselineVerdict = baselineOutcome value``) and the postcondition's
    ``else`` branch. It has no computable content, so the tester+``decide``
    route (``derive_tester_for`` → ``…Tester args = false``) is UNAVAILABLE —
    though the port's stated reason was wrong and is corrected here from real
    builds. ``extract_program_for validateUrl`` SUCCEEDS (exit 0), and with it
    ``derive_tester_for`` does produce ``validateUrlExec : List Char →
    BaselineOutcome → DivM CallOutcome`` and ``validateUrlTester : List Char →
    BaselineOutcome → Bool``. What actually blocks the route is (a) a
    code-generator error on the file, ``baselineOutcome not supported by code
    generator; consider marking definition as noncomputable``, and (b) more
    decisively, the ``decide`` itself: on ``validateUrlTester ['\\t']
    BaselineOutcome.accepts = false`` it reports ``did not reduce to `isTrue` or
    `isFalse` … reduction got stuck at the Decidable instance``, and it is stuck
    with the BYTE-IDENTICAL message against the frozen solution and against a
    rival — so that route's exit code would carry no information about the claim.
    That is exactly the ``witness-undecided`` shape the gate screens for, which is
    why the conditioned-triple witnesses below are used instead. This does NOT
    empty the reject lane. An opaque term has
    no VALUE to compute but is still a term one can QUANTIFY over: every reject
    rival is refuted by CONDITIONING ON THE CARRIER — the method's Hoare triple
    is refuted at a point described by hypothesis (``hb : baselineOutcome v =
    BaselineOutcome.<c>``), so the refutation holds exactly on the sub-domain
    where the rival diverges from the spec. Each witness carries ONE hypothesis
    per opaque term (``hb`` about ``baselineOutcome v``; ``hpre`` merely binds
    ``baselineVerdict`` to it to satisfy the precondition), so the assumptions
    are jointly satisfiable — the consistency probe leaves ``False`` unsolved.
    Every witness was SEEN to discriminate with real builds: it ELABORATES
    against its rival (EXIT 0) and FAILS against the frozen solution (EXIT 1).

TWO INPUT BINDERS, both free (the ``require`` only ties ``baselineVerdict`` to
``baselineOutcome value``, not to a literal):
  * ``value``           — the candidate string; drives ``containsForbidden`` and
                          feeds the opaque ``baselineOutcome``;
  * ``baselineVerdict`` — the unchanged validation's outcome (= ``baselineOutcome
                          value``), surfaced on the forbidden-char-free path.

ADVERSARIAL READ of the nagini classes (see the footer for the case-by-case
accounting):
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The sibling carries a
    MANDATORY frame-mutation rival: it keeps the gold body then writes back into
    the read-only ``value`` held at a fractional heap permission
    (``Acc(list_pred(value),1/2)``), and must be rejected for INSUFFICIENT
    PERMISSION. Lean and Velvet are referentially transparent: every parameter
    is an immutable value, this bundle declares no ``mut`` binder, there is no
    heap and no aliasing. There is no read-only input to overwrite and no
    permission system to trip, so the class is vacuous. No substitute is
    fabricated (per the porting map, this class is legitimately dropped here).
  * TERMINATION / DIVERGENCE — the port's stated REASON was FALSE, and the true
    disposition is different from both the port's and the obvious correction.
    Every earlier revision of this file asserted "this bundle's ``set_option
    loom.semantics.termination`` is ``"partial"``, so a diverging impl VERIFIES
    vacuously". That is false against the frozen file this battery loads:
    ``Solution.lean`` line 4 reads ``set_option loom.semantics.termination
    "total"``. Under ``"total"`` a diverging rival supplying NO measure is
    genuinely REJECTED — measured, exit 1, ``error: Decreasing annotations are
    required in total correctness semantics`` — so the class is NOT the
    "spec admits it" hole the old prose claimed.
    It still cannot be carried as a reject CASE, for a mechanical reason that is
    neither vacuity nor a spec hole, and this was measured rather than argued.
    The termination obligation is reported at the ``method`` declaration itself
    (line 90), BEFORE and independently of ``prove_correct``, so the rival's
    source does not elaborate AT ALL. The gate's reject protocol requires the
    ``witness`` to hold OF THE RIVAL (``rival.success``) before it will look at
    the gold side, and a file that fails to elaborate can prove nothing: the
    witness build against this rival returns exit 1 with that same termination
    error, which the gate records as ``witness-unproven`` — an INCONCLUSIVE
    outcome that fails the battery outright. A ``witness_reference`` does not
    help: it substitutes the GOLD-side subject, never the rival-side one. So the
    honest record is: the spec REJECTS this class (which is the outcome we want,
    and the reason no case is needed to defend it), and the reject lane cannot
    express a rejection that happens at elaboration time rather than proof time.
    Verified by build, not assumed: rival impl exit 1, witness-vs-rival exit 1,
    both with the termination error; witness-vs-gold exit 1 (value refutation).
  * DIVERGENCE / NON-TERMINATION: fully CLOSED under ``"total"``, and the sharper
    claim this bullet used to make about it is RETRACTED. The retracted text said
    the ``decreasing`` annotation is required but its measure is NOT VALIDATED, so
    a diverging loop carrying a bogus, plainly INCREASING measure
    (``while 0 = 0 ... done_with False; decreasing k`` with body ``k := k + 1``)
    verifies at exit 0, and that because ``done_with False`` makes everything
    after the loop unreachable it verifies while returning an unambiguously WRONG
    constant. Re-measured on that exact shape, it does not reproduce: the build is
    REJECTED at exit 1 on the MEASURE's own goal, under the clause's own name
    (``case «decreasing_1: k» ... k + 1 < k``). The mechanism is structural rather
    than a tactic accident. Loom's total-correctness loop generator
    (``forWithInvariantLoop`` under ``TotalCorrectness.DemonicChoice.WPGen``)
    takes a ``measure : β -> Nat`` and emits the per-iteration side condition
    ``with_name_prefix `decreasing (measure b' < measure b)``, so a constant or
    increasing measure arrives as an unprovable goal no matter what the
    continuation can reach; the twin that takes ``measure : β -> Option ℕ`` and
    DISCARDS it lives under ``PartialCorrectness``, which nothing here opens.
    So flipping the option to ``"total"`` IS sufficient, no unchecked measure
    re-admits the vacuity, there is no cell-local spec hole, and no
    ``spec_holes`` entry is owed. The class ships no case all the same, on the
    witness path rather than the spec: a reject case needs a witness that
    ELABORATES against the rival, and a diverging rival's module does not compile
    at all, so the case would score MALFORMED instead of rejecting.
  * UNGROUNDED-ORACLE ECHO — N/A as an ATTACK. The load-bearing ``then`` branch
    is pinned to ``containsForbidden value``, a fully-unfolded ``def`` over the
    argument. The ``else`` branch defers to ``baselineOutcome value`` (the
    opaque axiom), but that IS the unchanged behaviour the fix passes through —
    the postcondition surfaces it, never echoes a wrong marker. The unique
    satisfier is the grounded decision (scan the input; else surface the baseline
    outcome). The honest controls are the cheapest faithful reshapes (``pos-*``).
  * CONTROL-FLOW / PARTIAL-DOMAIN / VALUE — heavily exercised. The sole clause
    forks on ``containsForbidden value`` and, on the clean path, on the three-way
    ``baselineOutcome value``. Rivals attack: the screen removed entirely
    (prepatch); a first-code-point-only screen (mid-string sub-domain); the
    baseline deferral dropped (clean path hard-coded); one baseline outcome
    collapsed to a refusal (the ``crashes`` constructor this carrier newly
    exposes); and always-refuse (the clean path removed).

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries two
axiom-soundness / containment probes over the real ``URLValidator`` callee; that
is G-AX's job (``axiom_check.py`` / ``mapping.md``, which validate
``baselineOutcome`` total+deterministic and ``containsForbidden`` == the real
screen) and the G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-14349"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- The frozen impl body, verbatim — everything strictly BETWEEN the method's
# ---- `-- impl-start` / `-- impl-end`. Every rival and reshape edits ONLY this
# ---- block (and, for the admissibility case, the elided `prove_correct` tactic
# ---- body), so the spec view is untouched and same_spec holds by construction.
# ---- The block lies wholly inside the single impl region and is unique in
# ---- Solution.lean (both facts asserted at load by _swap).
_IMPL = (
    "    if containsForbidden value then\n"
    "      return CallOutcome.rejected\n"
    "    else\n"
    "      return liftBaseline baselineVerdict"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# ---- The frozen proof, verbatim. The admissibility case adds an in-region
# ---- `assert` (a side goal `loom_solve` leaves open) and retunes THIS block to
# ---- discharge it; the obligation STATEMENT and the `prove_correct` header are
# ---- untouched, so same_spec still holds. Rivals and pos reshapes leave it
# ---- as-is. Anchored on the exact frozen script.
_PROOF = "prove_correct validateUrl by\n  loom_solve"

assert _BASE.count(_PROOF) == 1, "prove_correct validateUrl body drifted"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_proof(new_body, new_proof):
    """Reshape the impl body AND retune the (elided) prove_correct tactic body."""
    return _swap(_swap(_BASE, _IMPL, new_body), _PROOF, new_proof)


# ---- WITNESS builder. The spec is a `method` CONTRACT over an opaque,
# ---- noncomputable carrier (`baselineOutcome`), so a witness cannot go through
# ---- the tester machinery (extraction fails on `baselineOutcome`, which has no
# ---- executable code). Each witness instead refutes the method's Hoare triple
# ---- DIRECTLY at a point described by hypothesis — conditioning on
# ---- `baselineOutcome value` so the refutation holds exactly where the rival
# ---- diverges. Checked in a file whose `prove_correct` block has been stripped,
# ---- so no tactic script can mask the verdict. `rw [triple]` exposes the
# ---- weakest precondition of the straight-line body; `simp only [le_Prop_eq]`
# ---- + `intro hcon` peels the precondition implication; `hcon hpre` discharges
# ---- `baselineVerdict = baselineOutcome value` from `hpre`; the `rw [...]`
# ---- lines fold `baselineOutcome value` to the concrete outcome via `hb` (and
# ---- `baselineVerdict` via `hpre` when the rival's returned value mentions it);
# ---- `simp [...]` then reduces `wp`, the scan, and `liftBaseline` to a decided
# ---- constructor clash. All reduction lemmas come from the frozen `Velvet.Std`
# ---- import; no banned token (sorry/admit/native_decide/axiom/opaque).
#
# `value_lit`  — the concrete `List Char` input.
# `outcome`    — the `BaselineOutcome.<c>` the opaque baseline takes at value_lit.
# `rw_pre`     — True iff the rival's returned value mentions `baselineVerdict`
#                (so `rw [hpre, ...]` is needed; else `rw [hb]` alone).
def _witness(value_lit, outcome, rw_pre=True):
    rw = f"rw [hpre, hb] at h" if rw_pre else "rw [hb] at h"
    return (
        f"example (baselineVerdict : BaselineOutcome)\n"
        f"    (hpre : baselineVerdict = baselineOutcome {value_lit})\n"
        f"    (hb : baselineOutcome {value_lit} = BaselineOutcome.{outcome}) :\n"
        f"    ¬ triple (l := Prop) (baselineVerdict = baselineOutcome {value_lit})\n"
        f"        (validateUrl {value_lit} baselineVerdict)\n"
        f"        (fun outcome => outcome =\n"
        f"          (if containsForbidden {value_lit} then CallOutcome.rejected\n"
        f"           else liftBaseline (baselineOutcome {value_lit}))) := by\n"
        f"  unfold validateUrl\n"
        f"  rw [triple]\n"
        f"  simp only [le_Prop_eq]\n"
        f"  intro hcon\n"
        f"  have h := hcon hpre\n"
        f"  {rw}\n"
        f"  simp [wp_pure, isForbidden, containsForbidden, liftBaseline] at h\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG on the SHAPE of the impl. Each keeps the decision
    # value identical and only reshapes the executable surface, so the frozen
    # `loom_solve` script still discharges the byte-identical obligation.
    # =====================================================================
    {
        "id": "pos-localvar-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the per-string forbidden-character verdict to a local
        # `bad` first and branch on it, instead of testing `containsForbidden
        # value` inline in the guard. Observationally identical on every input.
        "module": _impl(
            "    let bad := containsForbidden value\n"
            "    if bad then\n"
            "      return CallOutcome.rejected\n"
            "    else\n"
            "      return liftBaseline baselineVerdict"),
        "rationale": "structurally-different but CORRECT impl: the forbidden-"
                     "character verdict is bound to a local `bad` and the guard "
                     "tests `bad` instead of `containsForbidden value` inline. "
                     "Same outcome on every (value, baselineVerdict), no new proof "
                     "obligation, so the single ensures clause still discharges "
                     "under the frozen `loom_solve`. A pure local-variable reshape "
                     "(no dropped clause, no branch inversion). If it FAILS => "
                     "SPEC-TOO-STRONG (a faithful correct impl is rejected).",
    },
    {
        "id": "pos-conditional-binding",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: derive the outcome with a single pure conditional expression
        # bound to `out`, then return it — instead of two `return`s across an
        # if/else. Definitionally the frozen post-image, so `loom_solve` closes
        # the byte-identical obligation. A second, distinct impl shape.
        "module": _impl(
            "    let out : CallOutcome :=\n"
            "      if containsForbidden value then CallOutcome.rejected\n"
            "      else liftBaseline baselineVerdict\n"
            "    return out"),
        "rationale": "second correct reshape: the outcome is computed as one pure "
                     "conditional expression bound to `out` and returned, rather "
                     "than via two branch-local `return`s. The returned value is "
                     "definitionally the post-image on every input, so the ensures "
                     "clause discharges under the frozen `loom_solve`. Exercises a "
                     "second impl shape so the reshape space is not a single point; "
                     "if it FAILS => SPEC-TOO-STRONG on the executable staging.",
    },
    {
        "id": "pos-destructure-baseline",
        "kind": "soundness",
        "expect": "verify",
        # ADDED BY AUDIT. The two positives above are both DEFINITIONALLY the
        # frozen impl: a `let bad :=` binding and a hoisted `let out := if …`
        # each zeta-reduce to the frozen term, so `loom_solve` closes them for
        # the same reason it closes the frozen body — they exercise the
        # elaborator's staging, not the spec's tolerance of a different proof
        # shape. This reshape is NOT definitionally equal: the `else` arm
        # replaces `liftBaseline baselineVerdict` (one application of a def) with
        # a three-way `match` on `baselineVerdict` returning each constructor's
        # image directly. Reducing it to the post-image requires CASE ANALYSIS on
        # the scrutinee rather than unfolding, so the ensures clause is discharged
        # by a genuinely different route while the returned value is unchanged on
        # every input. Measured: verifies under the frozen `loom_solve` (exit 0),
        # and each reject witness was additionally built against THIS impl as a
        # correct-reshape control — all six exit 1, so no witness refutes it.
        "module": _impl(
            "    if containsForbidden value then\n"
            "      return CallOutcome.rejected\n"
            "    else\n"
            "      match baselineVerdict with\n"
            "      | BaselineOutcome.accepts => return CallOutcome.accepted\n"
            "      | BaselineOutcome.rejects => return CallOutcome.rejected\n"
            "      | BaselineOutcome.crashes => return CallOutcome.crashed"),
        "rationale": "third correct reshape, and the only one that is NOT "
                     "definitionally the frozen impl: the `else` arm destructures "
                     "`baselineVerdict` into its three constructors and returns "
                     "each one's image directly, instead of applying "
                     "`liftBaseline`. Observationally identical on every "
                     "(value, baselineVerdict) — it is exactly `liftBaseline`'s "
                     "defining table — but the obligation now needs case analysis "
                     "on the scrutinee where the other two positives needed only "
                     "unfolding, so it tests that the frozen `loom_solve` tolerates "
                     "a different PROOF route and not merely a different staging of "
                     "the same term. It also doubles as the correct-reshape control "
                     "for the reject lane: every witness below was built against "
                     "this impl and none of them holds of it, which is what "
                     "separates a real refutation from a tactic mismatch. If it "
                     "FAILS => SPEC-TOO-STRONG (the spec pins the impl's shape, "
                     "not its behaviour).",
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the sibling `admiss-reads`. The sibling
    # asserts the half-permission admits reading a normal F2P-shaped value's
    # length + first code point. Lean/Velvet have no permission surface, and the
    # method's only `require` ties `baselineVerdict` to `baselineOutcome value`
    # (an opaque term no literal input can be proven equal to independently), so
    # the "a normal input satisfies the precondition" probe is degenerate here.
    # Re-aimed at the residual admissibility risk on this carrier: on a TOTAL
    # carrier the analogue of PRECOND-TOO-STRONG is the obligation being
    # UNSATISFIABLE at exactly an F2P-shaped input, so the probe discharges the
    # method's own Hoare triple AT two concrete inputs — by evaluation, as a
    # `have`, before closing the frozen obligation verbatim — rather than
    # asserting a decidable side claim about the post-image in the abstract.
    #
    # AUDIT (attack F / the admissibility lane). The shipped case used an
    # in-region `assert` over a CLOSED literal expression, discharged by
    # `loom_solve <;> decide`. That assert mentions neither `validateUrl` nor
    # either binder: it restates the post-image's `then` arm as arithmetic on
    # literals, so it cannot witness that the OBLIGATION is satisfiable at an
    # F2P-shaped point. Measured (real builds, exit codes as observed): the
    # `assert` form's own liveness twins DO fail (a flipped claim, exit 1
    # `decide proved that the proposition … is false`; the same claim at a clean
    # value `['a']`, exit 1), so the shipped case was live rather than vacuous —
    # but it was strictly weaker than the shape the lane calls for. Replaced
    # with two `have`s that each discharge the real triple:
    #   * adm_forbidden — at the mid-string-TAB F2P corner `['a','\t']` with an
    #     ACCEPTING baseline, the obligation forces `rejected`: the screen
    #     overrides the baseline rather than being subsumed by it;
    #   * adm_clean — at the clean value `['a']` with an accepting baseline, the
    #     obligation forces `accepted`: the clean path is live too, so the
    #     post-image is not the constant refusal.
    # Both are proven by EVALUATION over the frozen clause (`unfold validateUrl;
    # rw [triple]; simp [wp_pure, isForbidden, containsForbidden,
    # liftBaseline]`), then the frozen `loom_solve` closes the byte-identical
    # obligation. Liveness measured: flipping adm_forbidden to `accepted` fails
    # (exit 1, `⊢ False`) and flipping adm_clean to `rejected` fails (exit 1), so
    # neither `have` is a tautology `simp` would close for any target. If this
    # case cannot verify => the obligation is unsatisfiable at an F2P-shaped
    # input / PRECOND-TOO-STRONG.
    # =====================================================================
    {
        "id": "admiss-forbidden-overrides-baseline",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(
            _IMPL,
            "prove_correct validateUrl by\n"
            "  have adm_forbidden : triple (l := Prop)\n"
            "      (BaselineOutcome.accepts = baselineOutcome ['a', '\\t'])\n"
            "      (validateUrl ['a', '\\t'] BaselineOutcome.accepts)\n"
            "      (fun outcome => outcome = CallOutcome.rejected) := by\n"
            "    unfold validateUrl\n"
            "    rw [triple]\n"
            "    simp only [le_Prop_eq]\n"
            "    intro _\n"
            "    simp [wp_pure, isForbidden, containsForbidden, liftBaseline]\n"
            "  have adm_clean : triple (l := Prop)\n"
            "      (BaselineOutcome.accepts = baselineOutcome ['a'])\n"
            "      (validateUrl ['a'] BaselineOutcome.accepts)\n"
            "      (fun outcome => outcome = CallOutcome.accepted) := by\n"
            "    unfold validateUrl\n"
            "    rw [triple]\n"
            "    simp only [le_Prop_eq]\n"
            "    intro _\n"
            "    simp [wp_pure, isForbidden, containsForbidden, liftBaseline]\n"
            "  loom_solve\n"),
        "rationale": "the method's OWN obligation is satisfiable, and "
                     "non-degenerate in BOTH branches, at concrete F2P-shaped "
                     "inputs — discharged by evaluation as two `have`s over the "
                     "frozen triple before the frozen `loom_solve` closes the "
                     "byte-identical obligation. `adm_forbidden`: at "
                     "`['a', '\\t']` (a mid-string forbidden code point) with an "
                     "ACCEPTING baseline the triple forces `CallOutcome.rejected` "
                     "— the screen overrides the baseline rather than being "
                     "subsumed by it. `adm_clean`: at the clean `['a']` with the "
                     "same accepting baseline it forces `CallOutcome.accepted` — "
                     "the deferral path is live, so the post-image is not the "
                     "constant refusal. Each claim is falsifiable: flipping "
                     "either target leaves `⊢ False` unsolved. If it cannot "
                     "verify => the obligation is unsatisfiable at an F2P-shaped "
                     "input / PRECOND-TOO-STRONG.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness that
    # CONDITIONS on the opaque `baselineOutcome value` at one concrete input, and
    # the refinement argument that its faithful real counterpart would NOT resolve
    # the F2P. Witnesses vary BOTH binders: `value` over ['\t'] / ['a'] /
    # ['a','\t'], and `baselineVerdict` (= baselineOutcome value) over all three
    # BaselineOutcome constructors (accepts / rejects / crashes).
    # =====================================================================
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch skeleton: NO forbidden-character screen — the call's
        # outcome is the unchanged validation's outcome alone.
        "module": _impl("    return liftBaseline baselineVerdict"),
        "refinement": "this IS the pre-patch behaviour: no early forbidden-"
                      "character screen, so the outcome is the unchanged structural "
                      "validation's ending alone. Its faithful real counterpart is "
                      "the unchanged repo. On a value carrying a forbidden control "
                      "character that the (post-bpo-43882) validation would accept — "
                      "e.g. one whose sole such character is stripped before "
                      "splitting — it returns an acceptance instead of refusing, so "
                      "the failing test that now asserts the designated refusal IS "
                      "raised for such values still fails. It would NOT resolve.",
        "rationale": "REJECT from the `then` branch (`containsForbidden value => "
                     "CallOutcome.rejected`): on a value carrying a forbidden "
                     "character whose baseline ACCEPTS, the post-image demands "
                     "`rejected` but the rival surfaces the baseline "
                     "(`accepted`). CONTROL-FLOW: the early-refuse fork is removed. "
                     "Refuted at `value = ['\\t']` (forbidden), "
                     "`baselineOutcome value = accepts`. If it VERIFIES => "
                     "SPEC-TOO-WEAK (the screen is unenforced).",
        "witness": _witness("['\\t']", "accepts", rw_pre=True),
    },
    {
        "id": "weak-screen-to-crash",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. Every shipped rival attacks the `then` branch's GUARD
        # (removed entirely by weak-prepatch, narrowed to index 0 by
        # weak-first-char-only) or the `else` branch. None attacks the CONSTRUCTOR
        # the `then` branch returns: the screen fires on exactly the right values
        # but surfaces the WRONG ending — an unrelated abort escaping the call
        # instead of the designated refusal. So `containsForbidden` is pinned as a
        # guard by the shipped set while `CallOutcome.rejected` as the screen's
        # ANSWER was unpinned.
        "module": _impl(
            "    if containsForbidden value then\n"
            "      return CallOutcome.crashed\n"
            "    else\n"
            "      return liftBaseline baselineVerdict"),
        "refinement": "raising the wrong thing on the screened path is what a real "
                      "patch that added the new check but signalled it with a bare "
                      "`raise`/`assert`/an unrelated exception class — rather than "
                      "the designated validation failure the rest of the project "
                      "catches — would do. The screen fires on exactly the right "
                      "strings, so it is a near-miss on the guard, but the caller "
                      "observes an escaping error instead of the ordinary refusal: "
                      "the failing test asserts the DESIGNATED refusal IS raised "
                      "for such values, and an unrelated error escaping is not "
                      "that. It also breaks every existing case that relies on the "
                      "refusal being catchable. It would NOT resolve.",
        "rationale": "REJECT from the `then` branch's VALUE (`containsForbidden "
                     "value => CallOutcome.rejected`): on a value carrying a "
                     "forbidden character the post-image demands `rejected` but the "
                     "rival returns `crashed`. Distinct from weak-prepatch and "
                     "weak-first-char-only, which both keep the right answer on the "
                     "path they do screen and attack the GUARD instead; this one "
                     "keeps the guard exactly right and moves the ANSWER, so it is "
                     "the only rival that pins the `then` arm's constructor. Its "
                     "witness also moves the baseline to `crashes` at a FORBIDDEN "
                     "value — the one (value, outcome) corner where the screen must "
                     "override an aborting baseline, which no other case reaches "
                     "(weak-crash-to-reject conditions `crashes` at a CLEAN value). "
                     "Refuted at `value = ['\\t']`, `baselineOutcome value = "
                     "crashes`. If it VERIFIES => SPEC-TOO-WEAK (the screen's own "
                     "outcome is unenforced).",
        "witness": _witness("['\\t']", "crashes", rw_pre=True),
    },
    {
        "id": "weak-first-char-only",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: scan ONLY the first code point. Rejects a LEADING
        # forbidden character but MISSES one anywhere past index 0, deferring to
        # the baseline there. Correct on the leading sub-domain; wrong on the
        # not-first-position sub-domain (the mid-string F2P case).
        "module": _impl(
            "    match value with\n"
            "    | [] => return liftBaseline baselineVerdict\n"
            "    | c :: _ =>\n"
            "      if isForbidden c then\n"
            "        return CallOutcome.rejected\n"
            "      else\n"
            "        return liftBaseline baselineVerdict"),
        "refinement": "checking only the first code point is what a real patch "
                      "that screened `value[:1]` / `value.startswith((...))` would "
                      "do. It refuses a leading forbidden character but ACCEPTS one "
                      "anywhere past index 0, deferring to the unchanged validation "
                      "there. It does NOT refuse a value whose only forbidden "
                      "character sits mid-string — a literal F2P input that asserts "
                      "the designated refusal IS raised. A genuine PARTIAL-DOMAIN "
                      "break on the not-first-position sub-domain; would NOT "
                      "resolve.",
        "rationale": "REJECT from the `then` branch: for a value whose only "
                     "forbidden character is at index >= 1 (a clean head, TAB at "
                     "index 1) with an accepting baseline, the rival defers to the "
                     "baseline (`accepted`) but the post-image demands `rejected` "
                     "(`containsForbidden` is true ANYWHERE). PARTIAL-DOMAIN: the "
                     "rival pins only the first-position sub-domain, so its witness "
                     "moves `value` to a two-element list with a clean head — a "
                     "distinct point from weak-prepatch's leading-forbidden input. "
                     "If it VERIFIES => SPEC-TOO-WEAK on the not-first-position "
                     "sub-domain.",
        "witness": _witness("['a', '\\t']", "accepts", rw_pre=True),
    },
    {
        "id": "weak-drop-baseline",
        "kind": "uniqueness",
        "expect": "reject",
        # Scans for a forbidden character exactly like gold (so it correctly
        # refuses any forbidden-char value) but on the clean path hard-codes an
        # acceptance, dropping the deferral to the unchanged validation. Attacks
        # the `else` branch: it pins the forbidden-char half but unpins the
        # baseline-surfacing half.
        "module": _impl(
            "    if containsForbidden value then\n"
            "      return CallOutcome.rejected\n"
            "    else\n"
            "      return CallOutcome.accepted"),
        "refinement": "screening for forbidden characters but then hard-coding an "
                      "acceptance on the clean path is what a real patch that added "
                      "the new screen but DELETED the rest of the validator "
                      "(scheme/regex/IDN/IPv6/host-length) would do. It would accept "
                      "every forbidden-char-free string regardless of whether it is "
                      "a valid URL, failing every existing case that the unchanged "
                      "validation refuses (e.g. 'no_scheme'). It would NOT resolve "
                      "(the deferral is unchanged behaviour the patch must "
                      "preserve).",
        "rationale": "REJECT from the `else` branch (`liftBaseline (baselineOutcome "
                     "value)`): on a forbidden-char-free value whose baseline "
                     "REFUSES (`rejects`), the post-image demands `rejected` but "
                     "the rival hard-codes `accepted`. CONTROL-FLOW-EFFECT: the "
                     "baseline deferral is dropped, so the surface half of the "
                     "outcome is lost. Refuted at `value = ['a']` (clean), "
                     "`baselineOutcome value = rejects` — moving `baselineVerdict` "
                     "to the `rejects` constructor. If it VERIFIES => SPEC-TOO-WEAK "
                     "(the baseline surfacing is unenforced).",
        "witness": _witness("['a']", "rejects", rw_pre=False),
    },
    {
        "id": "weak-crash-to-reject",
        "kind": "uniqueness",
        "expect": "reject",
        # BINDER-COVERAGE (the third BaselineOutcome constructor this carrier
        # newly exposes). Correct on the accepts/rejects baselines but collapses
        # the `crashes` outcome to a designated refusal on the clean path. A
        # near-miss: it defers faithfully except for the one baseline constructor
        # nagini could not distinguish (it modeled the baseline as a single bool).
        "module": _impl(
            "    if containsForbidden value then\n"
            "      return CallOutcome.rejected\n"
            "    else\n"
            "      match baselineVerdict with\n"
            "      | BaselineOutcome.crashes => return CallOutcome.rejected\n"
            "      | b => return liftBaseline b"),
        "refinement": "collapsing the unchanged validation's third ending (an "
                      "unrelated error escaping — the real hostname-None `TypeError` "
                      "family, e.g. \"http://?@[::1]\") into the designated refusal "
                      "is what a real patch that wrapped the whole validator in a "
                      "catch-all `except: raise ValidationError` would do. It "
                      "converts an escaping error into the ordinary refusal, "
                      "changing behaviour the patch leaves untouched — the crash "
                      "propagates unchanged pre- and post-patch — so a PASS_TO_PASS "
                      "case that observes the escaping error's identity would break. "
                      "It would NOT resolve.",
        "rationale": "REJECT from the `else` branch: on a forbidden-char-free value "
                     "whose baseline CRASHES, the post-image demands `liftBaseline "
                     "crashes = crashed` but the rival returns `rejected`. A "
                     "near-miss of weak-drop-baseline that agrees with gold on the "
                     "accepts/rejects baselines, so it carries its OWN witness at "
                     "the `crashes` constructor — the third baseline outcome no "
                     "other reject rival probes (and one nagini's single-bool "
                     "downstream model could not express). Refuted at "
                     "`value = ['a']`, `baselineOutcome value = crashes`. If it "
                     "VERIFIES => SPEC-TOO-WEAK on the crash sub-domain.",
        "witness": _witness("['a']", "crashes", rw_pre=True),
    },
    {
        "id": "weak-always-reject",
        "kind": "uniqueness",
        "expect": "reject",
        # ALWAYS refuses (every input takes the refusal path). CONTROL-FLOW-EFFECT
        # (dual of weak-prepatch): the accept/defer fork is removed entirely.
        "module": _impl("    return CallOutcome.rejected"),
        "refinement": "always refusing is what a real patch that hard-coded the "
                      "guard true (or compared `value` against an always-truthy "
                      "set) would do — it refuses EVERY string, including every "
                      "valid one the project must accept. It fails every existing "
                      "case that requires the validator to accept a well-formed URL "
                      "(the entire valid-URL fixture). It would NOT resolve.",
        "rationale": "REJECT from the `else` branch: on a forbidden-char-free value "
                     "whose baseline ACCEPTS, the post-image demands `liftBaseline "
                     "accepts = accepted` but the rival returns `rejected`. "
                     "CONTROL-FLOW-EFFECT (dual of weak-prepatch): the accept/defer "
                     "fork is removed. Refuted at `value = ['a']` (clean), "
                     "`baselineOutcome value = accepts` — the accepts baseline on a "
                     "clean value, the sub-domain weak-drop-baseline (rejects) does "
                     "not probe. If it VERIFIES => SPEC-TOO-WEAK (acceptance "
                     "unpinned).",
        "witness": _witness("['a']", "accepts", rw_pre=False),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (1 soundness
# positive, 1 admissibility, 6 uniqueness — one of which is the mandatory frame-
# mutation rival, one the divergence rival) plus 2 AXIOM_TESTS probes. The
# sibling models the same screen over a `List[int]` value at a fractional heap
# permission, with the scan a verified `while` loop under a `MustTerminate(2)`
# precondition and the downstream verdict a single BOOL `accepted`; this backend
# models the purely-functional core straight-line over `List Char`, with the
# unchanged validation an opaque three-way `baselineOutcome` axiom. The value
# surface carries across; the permission surface, the loop, and the termination
# obligation do not exist here — but the three-way baseline is RICHER than
# nagini's single bool.
#
#   sibling case            -> here                              disposition
#   -----------------------------------------------------------------------
#   pos-localvar-reshape    -> pos-localvar-reshape              PORTED
#   (no sibling)            -> pos-conditional-binding           ADDED (2nd shape)
#   admiss-reads            -> admiss-forbidden-overrides-baseline RE-AIMED
#   frame-mut-write         -> (none)                            VACUOUS
#   weak-diverge            -> (none)                  REJECTED BY SPEC, unshippable
#   weak-prepatch           -> weak-prepatch                      PORTED
#   weak-first-char-only    -> weak-first-char-only               PORTED
#   weak-drop-downstream    -> weak-drop-baseline                 PORTED
#   weak-always-reject      -> weak-always-reject                 PORTED
#   (no sibling)            -> weak-crash-to-reject               ADDED (binder cov.)
#   (no sibling)            -> weak-screen-to-crash               ADDED BY AUDIT
#   (no sibling)            -> pos-destructure-baseline           ADDED BY AUDIT
#
# 4 ported, 1 re-aimed (then STRENGTHENED by audit), 4 added, 1 vacuous
# (frame-mutation), 1 rejected-by-the-spec-but-unshippable (divergence, see below)
# = 10 velvet cases (4 verify, 6 reject).
#
# ADDED BY AUDIT (pos-destructure-baseline): the two shipped positives are both
#   DEFINITIONALLY the frozen impl — `let bad := containsForbidden value` and
#   `let out := if …` each zeta-reduce to the frozen term, so `loom_solve` closes
#   them for precisely the reason it closes the frozen body. Neither shows the
#   spec tolerates a different PROOF route, only a different elaboration staging,
#   which is the "positive whose different shape is definitionally equal" failure
#   mode. The added positive destructures `baselineVerdict` into its three
#   constructors in place of applying `liftBaseline`: same value on every input
#   (it is `liftBaseline`'s own defining table) but the obligation now requires
#   case analysis on the scrutinee. Measured: verifies under the frozen
#   `loom_solve` (exit 0). It is also the correct-reshape control for the reject
#   lane — all six witnesses were built against it and all six EXIT 1.
#
# VACUOUS (frame-mut-write): the sibling's MANDATORY frame-mutation rival keeps
#   the gold body verbatim then writes back into the read-only `value` held at
#   Acc(list_pred(value),1/2), and must be rejected for INSUFFICIENT PERMISSION.
#   This backend is referentially transparent: every parameter is an immutable
#   value, the method declares no `mut` binder, there is no heap and no aliasing.
#   No read-only input to overwrite, no permission system to trip. Not fabricated.
# NOT EXPRESSIBLE AS A CASE, but for a reason the two earlier revisions both got
#   wrong (weak-diverge). Revision 1 recorded it VACUOUS ("the frozen impl is
#   straight-line, so there is no diverging variant to build"); that is wrong, a
#   diverging prefix splices onto a loop-free impl fine. Revision 2 recorded it a
#   SPEC HOLE citing `set_option loom.semantics.termination "partial"`; that is
#   wrong too, and checkably so: the frozen `Solution.lean` line 4 of THIS cell
#   reads `"total"`, as it does in all 500 velvet bundles. All of revision 2's
#   reasoning ("such a rival VERIFIES", a `partial` cohort with this cell recorded
#   in it) described a bundle this is not. Re-derived from builds:
#     * diverging rival, NO `decreasing` measure          -> exit 1, REJECTED
#       (`error: Decreasing annotations are required in total correctness
#       semantics`, reported at the `method` on line 90)
#     * the same witness built against that rival         -> exit 1, SAME error
#   The second line is why the class still cannot ship. The termination error is
#   raised at the `method` declaration, before `prove_correct` and independently
#   of it, so the rival's SOURCE does not elaborate; the gate requires the witness
#   to hold OF THE RIVAL before it consults the gold side, so the case would be
#   recorded `witness-unproven` — INCONCLUSIVE, which fails the battery. (A
#   `witness_reference` cannot rescue it: that substitutes the gold-side subject,
#   never the rival-side one.) The right reading is therefore the OPPOSITE of a
#   spec hole: the spec correctly REJECTS divergence-without-measure, and needs
#   no case to defend a class it refuses at elaboration time.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``if`` over immutable values, no loop and no
#   recursion), so there is no control flow here to make diverge: a diverging
#   rival cannot be obtained by mutating this body, it has to bring a loop of
#   its own. When it does, the semantics refuse it. This bundle sets
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
# RE-AIMED, then STRENGTHENED BY AUDIT (admissibility): the sibling asserts the
#   half-permission admits reading a normal value's length + first code point.
#   This backend has no permission surface, so the permission form is genuinely
#   inexpressible. The port re-aimed it at an in-region `assert` over a CLOSED
#   literal expression discharged by `decide`. That assert was live (its flipped
#   twin and its clean-value twin both fail) but it mentions neither
#   `validateUrl` nor either binder — it restates the post-image's `then` arm as
#   arithmetic on literals, so it never shows the OBLIGATION is satisfiable at an
#   F2P-shaped input, which is the analogue of PRECOND-TOO-STRONG on a total
#   carrier. Replaced with two `have`s that discharge the real Hoare triple at
#   two concrete inputs by evaluation before the frozen `loom_solve` closes the
#   byte-identical obligation: `rejected` at the mid-string-TAB F2P corner with
#   an ACCEPTING baseline, and `accepted` at a clean value with the same
#   baseline. Both liveness twins (each target flipped) fail.
# ADDED (pos-conditional-binding): the sibling ships one positive control; a
#   second faithful reshape (pure conditional binding vs. branch-local returns)
#   exercises a distinct impl shape so the reshape space is not a single point.
# ADDED (weak-crash-to-reject): nagini's downstream verdict is a single BOOL
#   (`accepted`), so its rivals can only move that one bit. This backend's
#   baseline is a THREE-way outcome (accepts/rejects/crashes), so the `crashes`
#   constructor is a binder value no sibling rival could reach. The rival collapses
#   it to a refusal — a real divergence from `liftBaseline crashes = crashed`,
#   with a machine-checked witness — attacking the baseline binder at the value
#   nagini's abstraction could not express.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses (5 distinct input points; the
# opaque baseline is conditioned, not enumerated, so distinct (value, outcome)
# pairs are distinct points):
#   value            — ['\t'] (prepatch and screen-to-crash, forbidden at 0),
#                      ['a','\t'] (first-char, forbidden at 1, clean head), ['a']
#                      (drop-baseline / crash-to-reject / always-reject, clean):
#                      varied over forbidden-at-0, forbidden-mid, and clean.
#   baselineVerdict  — via `hb : baselineOutcome value = ...`: accepts (prepatch,
#                      first-char, always-reject), rejects (drop-baseline),
#                      crashes (crash-to-reject at a CLEAN value,
#                      screen-to-crash at a FORBIDDEN value): ALL THREE
#                      constructors moved, and `crashes` moved on BOTH sides of
#                      the guard.
#   Both branches of the sole clause attacked, and on each branch both the GUARD
#   and the returned CONSTRUCTOR: the `then` branch's guard by weak-prepatch
#   (removed) and weak-first-char-only (narrowed to index 0), its constructor by
#   weak-screen-to-crash; the `else` branch (`liftBaseline (baselineOutcome
#   value)`) by weak-drop-baseline, weak-crash-to-reject, and weak-always-reject.
#   Defended by the two positive controls (both branches computed correctly) and
#   the admissibility case (the obligation satisfiable and non-degenerate in BOTH
#   branches at concrete F2P-shaped inputs).
#
# WITNESS CONSISTENCY. Each reject witness binds `baselineVerdict` plus ONE
#   hypothesis per opaque term (`hb` about `baselineOutcome value`; `hpre` ties
#   `baselineVerdict` to it). The consistency probe (`example <binders> : False`)
#   leaves `False` unsolved for every case — the assumptions are jointly
#   satisfiable, so no witness is a contradiction-forgery. Verified out-of-band
#   with real builds: every witness ELABORATES against its rival (EXIT 0) and
#   FAILS against the frozen solution (EXIT 1).
#
# WITNESS DISCRIMINATION, RE-DERIVED BY AUDIT (attack B/B′; all exit codes below
#   were observed, not predicted). For every reject case: witness vs rival EXIT
#   0, witness vs frozen solution EXIT 1, consistency probe EXIT 1 (`False`
#   unsolved, i.e. hypotheses satisfiable). The gold-side failure is `unsolved
#   goals … ⊢ False` with the refutation's own hypothesis in context, so it is a
#   semantic refutation and not a missing identifier, a type error or a timeout.
#   Three independent forgery/reveal controls confirm gold's exit code TRACKS THE
#   CLAIM rather than being unconditional:
#     * FLIPPED CLAIM (drop the `¬`, asserting the obligation HOLDS there): EXIT
#       0 against the frozen solution for all six points, and EXIT 1 against
#       every rival. The exit code therefore carries information about the claim
#       in both directions — the hollow-case signature would have been the same
#       error for both polarities.
#     * TYPE-REVEALING probe (`exact (h : Nat)` in place of the closing step):
#       against the frozen solution `h` reduces to `True` at the two points where
#       `simp` can finish (so `simp` PROVED the obligation's equation there),
#       while against each rival the same probe prints a concrete unsatisfiable
#       equation (e.g. `CallOutcome.accepted = if … then CallOutcome.rejected
#       else CallOutcome.accepted`, and for weak-screen-to-crash a `then` arm
#       returning `crashed` where the post-image demands `rejected`).
#     * CORRECT-RESHAPE control: each witness was additionally built against two
#       VERIFYING correct reshapes of this same spec (a `match` on the scan, and
#       a full destructuring of `baselineVerdict`). All TWELVE builds EXIT 1 — so
#       no witness refutes a merely differently-SHAPED correct impl, which is the
#       test that separates a real refutation from a tactic mismatch. (The second
#       reshape is now shipped as `pos-destructure-baseline`, so this control is
#       re-run by the gate itself on every future run.)
#   SECOND AUDIT PASS — all 27 gate builds re-derived independently, plus 24
#   forgery/reveal builds. Reproduced exactly: 3 (now 4) verify variants EXIT 0,
#   6 reject variants EXIT 1, 6 witnesses rival-EXIT 0 / gold-EXIT 1, 6
#   consistency probes EXIT 1. The gold-side signature falls in TWO classes, and
#   neither is a plain evaluation, so the FORGERY test was run on all six rather
#   than on a sampled subset:
#     - `h : True` (prepatch, screen-to-crash, first-char-only, crash-to-reject):
#       `simp` PROVED the obligation's equation for the frozen impl at that point;
#     - `h : (match baselineVerdict with …) = <constructor>` (drop-baseline,
#       always-reject): a concrete equation left standing, unprovable without `hb`.
#   FLIPPED CLAIM (the `¬` dropped, i.e. asserting the frozen impl IS correct at
#   that very point) — EXIT 0 on gold and EXIT 1 on the rival, for ALL SIX points.
#   That is a clean polarity inversion in both directions, which is exactly what a
#   hollow case cannot produce: were gold's exit code unconditional, the flip would
#   have failed with the byte-identical error. The gold-side exit code therefore
#   carries information about the CLAIM, not about the carrier.
#   ANCHOR re-checked: `validateUrl_correct ['\t'] baselineVerdict` typechecks
#   directly as the witness's stated triple against the FULL frozen file, proof
#   intact (EXIT 0) — the witnesses refute the frozen obligation itself, not a
#   restatement of it.
#   The `witness-undecided` tester-route claim was also re-measured rather than
#   trusted: `extract_program_for` + `derive_tester_for` do produce
#   `validateUrlTester`, and `decide` on it is stuck with the byte-identical
#   `did not reduce to isTrue or isFalse` for the claim AND its negation, on gold
#   and on a rival alike (4 builds, all EXIT 1). So that route genuinely carries no
#   information and the conditioned-triple witnesses are the right shape here.
#   The witness's `triple` was also checked to be the frozen obligation itself
#   instantiated, not a restatement: `validateUrl_correct ['\t'] baselineVerdict`
#   typechecks directly against the witness's stated triple (EXIT 0), so
#   refuting the witness refutes the frozen obligation at that input.
#
# AUDIT PROBES beyond the shipped cases (attacks D and E; every variant below was
# built for real and its exit code observed). None of them is shipped as a case —
# the D probes only confirm the spec already refutes them, and the E probes only
# confirm it accepts faithful reshapes — but they bound what the battery leaves
# unprobed.
#   D (SPEC-TOO-WEAK: NEW wrong impls; every one must be REJECTED — all were,
#   each with the frozen `loom_solve` AND again with a retuned tactic body
#   (`<;> (try grind) <;> (try simp_all) <;> (try decide)`), since a rival may
#   rewrite the proof and a spec hole must be probed with the strongest attempt):
#     * screen YIELDS to the baseline when the baseline aborts (the screen must
#       override even the aborting ending) — rejected, `⊢ CallOutcome.crashed =
#       if containsForbidden value …`;
#     * PARTIAL forbidden set (screens TAB and CR but not LF) — rejected;
#     * LAST-code-point-only screen (dual of first-char-only) — rejected;
#     * the abort ending collapsed to an ACCEPT on the clean path — rejected;
#     * the empty string short-circuited to an ACCEPT, bypassing the deferral —
#       rejected;
#     * the screened path returning `accepted` — rejected;
#     * the screened path returning `crashed` — rejected, and this one was
#       promoted into the battery as `weak-screen-to-crash` (it was the only
#       genuine coverage gap: no shipped rival pinned the `then` arm's returned
#       constructor).
#     * RE-DERIVED AND EXTENDED (second audit pass). Ten D probes rebuilt, each
#       twice (frozen `loom_solve` AND the retuned body above): the screen made
#       conditional on the baseline; a PARTIAL forbidden alphabet (TAB+CR, no LF —
#       no shipped rival narrows the forbidden SET, only the scan's positional
#       extent); last-code-point-only; accepts mislifted to `crashed`; rejects
#       mislifted to `crashed`; the empty string short-circuited to an accept; the
#       screened path returning `accepted`; the guard negated; constant `accepted`;
#       constant `crashed`. ALL TWENTY builds EXIT 1. Plus the tightest near-miss
#       the carrier admits — the screen suppressed on exactly ONE of the six
#       (value-class, baseline-outcome) corners, `containsForbidden value &&
#       baselineVerdict ≠ crashes`, correct on the other five — also rejected in
#       both proof variants. So the `then` arm is pinned unconditionally, not just
#       on the corners the shipped witnesses visit.
#   E (SPEC-TOO-STRONG: NEW faithful correct reshapes; each must be PROVABLE):
#     * `match containsForbidden value with | true | false` — verifies;
#     * the guard NEGATED with the branches swapped — verifies;
#     * `baselineVerdict` fully DESTRUCTURED into its three constructors instead
#       of going through `liftBaseline` — verifies, and the second audit pass
#       PROMOTED it into the battery as `pos-destructure-baseline`, since it is the
#       only reshape tried that is not definitionally the frozen impl;
#     * the guard additionally CONSULTING `baselineVerdict` on a redundant branch
#       (`containsForbidden value && baselineVerdict ≠ rejects`, falling through to
#       a second `containsForbidden` test) — verifies in both proof variants. Worth
#       recording because it is correct only via the `require`: the spec admits an
#       impl that leans on the precondition, which is the right answer (the
#       precondition IS available to the implementer) but is not obvious a priori;
#     * `value.any isForbidden` in place of the recursive `containsForbidden`.
#       This one does NOT close under the frozen `loom_solve`: the leftover goals
#       are `CallOutcome.rejected = if containsForbidden value …` under
#       `if_pos : value.any isForbidden = true`, i.e. the two scans are equal but
#       not DEFINITIONALLY so. It is a TACTIC gap, not a spec hole, and it was
#       closed: supplying the bridging lemma `∀ l, l.any isForbidden =
#       containsForbidden l` (a four-line induction) in the tactic body makes it
#       verify, in all four variations tried. Recorded here rather than shipped
#       because a positive control whose proof carries its own lemma tests the
#       lemma more than the spec.
#   On the VALUE surface no probe verified that should have been rejected, and no
#   faithful reshape was rejected that could not be proven. The `value.any
#   isForbidden` reshape was re-measured this pass and reproduces exactly: exit 1
#   under the frozen `loom_solve`, exit 0 once the bridging lemma `∀ l, l.any
#   isForbidden = containsForbidden l` is supplied — a tactic gap, not a spec hole.
#   The spec hole this cell DOES carry is on the TERMINATION surface and was found
#   by attack D this pass: the `decreasing` measure is required but not validated,
#   so a diverging loop with a bogus increasing measure verifies while returning a
#   wrong constant. Written up above and escalated in the audit payload's
#   `spec_holes`; it is cell-local in the sense that it is a property of the frozen
#   `set_option` pair, and it refutes the corpus-wide remediation on record.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (axiom_check.py validates
# `baselineOutcome` total+deterministic-onto-three-outcomes and `containsForbidden`
# == the real screen); the G-PBT gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
