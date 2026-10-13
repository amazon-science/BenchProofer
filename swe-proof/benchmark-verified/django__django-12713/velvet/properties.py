"""properties.py — G-PBT falsification battery for django__django-12713 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct resolveWidget`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method, two read-only inputs):

  resolveWidget (provided : Option Widget) (computedDefault : Option Widget)
      return (out : Option Widget)
    ensures out = (if provided.isNone then computedDefault else provided)

The method resolves WHICH widget an input field ends up with. The caller may
supply one explicitly (``provided = some w``); when it does, that widget must be
the one used. When the caller supplies none (``provided = none``), the widget is
the field-derived default (``computedDefault``), which may itself be absent
(``none``). The single load-bearing ``ensures`` is a two-way PRECEDENCE with two
independently-attackable arms:

  * PRESERVATION arm (``provided.isSome``): the caller's widget is kept exactly
    (``out = provided``). This IS the behaviour the change adds — a
    caller-supplied widget is no longer clobbered by a field-derived default.
  * FALLBACK arm (``provided.isNone``): the field-derived default is applied
    exactly (``out = computedDefault``), whatever it is — including ``none`` when
    the field has no special default (nothing is fabricated).

TWO INPUT BINDERS: ``provided`` and ``computedDefault``, each ranging over
``{none, some w}``. Both are load-bearing: ``provided`` selects the arm and, on
the preservation arm, IS the result; ``computedDefault`` is the result on the
fallback arm. ``Widget`` is an opaque tagged identity (``id : Nat``); only WHICH
widget is used is observable, matching the consumer, which compares the resolved
widget to the one it supplied (mapping.md §2). The four reject witnesses drive
``(provided, computedDefault)`` to four DISTINCT points — the COMPLETE
``{none, some} × {none, some}`` square — so the manifest demonstrates the
post-image's dependence on both binders on BOTH arms, not on a single pinned
shape (pts = 4).

CARRIER NOTE — THE DECIDABLE BOUNDARY. A witness reaches the post-image through
Velvet's tester machinery (``resolveWidgetTester provided computedDefault =
false`` says the extracted program's result violates the postcondition at that
concrete input) and closes by ``decide``, checked in a file whose
``prove_correct`` block has been stripped so no tactic script can mask the
verdict. ``Widget`` derives ``DecidableEq`` and every witness input is a concrete
``Option Widget`` literal, so ``decide`` reduces the extracted program — gold's
included — to a literal Boolean. THE FAIL-ON-GOLD HALF IS A SEMANTIC REFUTATION,
NOT A STUCK TERM. Every witness here is fully computable against the frozen impl
too, and the gold-side build fails with

    error: Tactic `decide` proved that the proposition
      resolveWidgetTester <p> <d> = false
    is false

i.e. the kernel evaluates gold's extracted tester at the witnessed input and
reports ``true`` — gold SATISFIES the postcondition exactly where the rival
violates it. That is the strongest form the FAIL-on-gold half can take: the
witness is refuted on its merits at a computed value, never for a syntactic
reason (no unknown identifier, no type error, no unfolding failure, no timeout),
so each rejection is attributable to the spec and not to a tactic gap. It is
also what makes each gold-side build double as a NON-VACUITY certificate: gold's
postcondition is decidably TRUE at all four ``(provided, computedDefault)``
quadrants. Each reject rival is a loop-free closed form whose extracted tester
``decide``s over the same literal. No weakening: the frozen spec is untouched and
each rival's divergence is real at the witnessed input (both halves re-checked
with ``scripts/lean_verify.sh`` under audit — rival exit 0, gold exit 1 with the
refutation above, for all four reject cases).

ADVERSARIAL READ of the nagini classes on THIS carrier (see the footer for the
full case-by-case accounting):

  * The nagini sibling contracts a FIVE-input dict-mutating routine
    ``select_component`` whose postcondition has SIX top-level clauses:
    preservation (P), three priority-default clauses (1/2/3), a no-establish
    clause (4), and a forward no-spurious-key frame clause (F). This velvet
    bundle models a DELIBERATELY NARROWER carrier (mapping.md §2, refinement.md
    §A): the entire priority-selection chain — which of autocomplete / raw_id /
    filter default applies — is UNCHANGED by the fix and is folded into the
    single free input ``computedDefault`` (the ORACLE-choice precedent). What the
    fix actually changes, and all this bundle models, is the PRECEDENCE of a
    caller-supplied widget over that default. So nagini's three priority-order
    rivals (always-tertiary, priority-swap, wrong-identity) attack an ordering
    this carrier does not model and have NO counterpart here — porting them would
    mean fabricating rivals for a behaviour the bundle abstracts away.
  * FRAME / SPURIOUS-KEY — VACUOUS. Nagini holds ``options`` at full permission
    and its (F) clause forbids adding a stray key; the sibling's spurious-key
    rival stores an unrelated option. This backend is referentially transparent:
    the output is a single ``Option Widget`` value, there is no dict, no heap, no
    aliasing, no ``Old``, and no ``mut`` binder over any input — there is no
    container to add a stray key to and no frame clause to violate. No carrier
    analogue; NOT fabricated (porting map: this class is vacuous on a
    referentially-transparent backend).
  * ADMISSIBILITY — PORTED (re-aimed), by the second audit. The sibling
    self-calls on an F2P-shaped input to prove its
    ``Requires(Acc(dict_pred(options)))`` + pinned-boolean precondition admits it.
    This bundle declares NO ``require`` (pre-conditions region empty), so there is
    no PRECONDITION to admit — but that is NOT a reason to drop the lane, and the
    first port's claim that it was therefore vacuous was wrong. On a total carrier
    the analogue of PRECOND-TOO-STRONG is the OBLIGATION being unsatisfiable or
    DEGENERATE at exactly an F2P-shaped input, and ``admiss-f2p-precedence-
    nondegenerate`` tests that directly: it discharges the obligation AT the F2P
    shape by evaluation, as an in-region ``assert``, before closing the frozen
    obligation verbatim. "The post-image is a total function so it is satisfiable
    everywhere by construction" is an ARGUMENT, and this gate's job is to demand
    the machine-checked version of it — which is also what rules out the
    degenerate reading (an obligation collapsing every input to one value would
    satisfy a satisfiability probe and test nothing), pinned here by the third
    conjunct ``some {id:=1} ≠ some {id:=2}``.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is pinned to a closed
    ``Option``-precedence over the method's own two arguments; there is no
    opaque answer-key term a wrong impl could echo. The cheapest correct impl
    computes the precedence honestly, which the positive controls cover.
"""
from pathlib import Path

INSTANCE = "django__django-12713"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the WHOLE gold impl body (between the -- impl markers): a single anchor
# ---- lying wholly inside the impl region and unique in the file (both facts
# ---- asserted at load by _swap). Every reject rival and both positive controls
# ---- swap on this block, so the spec view (and hence markers.same_spec) is
# ---- preserved verbatim and the prove_correct resolveWidget statement is
# ---- byte-identical.
_IMPL = (
    "    let mut widget := provided\n"
    "    if widget.isNone then\n"
    "      widget := computedDefault\n"
    "    return widget"
)

# ---- The frozen prove_correct tactic body (`prove_correct resolveWidget by
# ---- loom_solve`) is left UNTOUCHED by every variant: both correct positive
# ---- controls are discharged by `loom_solve` unchanged, and for a reject rival
# ---- the tactic outcome is irrelevant — the WITNESS, not the proof, is what the
# ---- gate scores. So only the impl block is ever swapped.
def _rival(new_impl):
    """Full variant: whole impl block replaced; proof left as the frozen loom_solve."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- The frozen proof text, for the ONE case that must retune it (the
# ---- admissibility positive, whose in-region `assert` adds a VC the frozen
# ---- `loom_solve` alone does not clear). The tactic body is elided from the
# ---- consumer spec view, so retuning it keeps markers.same_spec and leaves the
# ---- `prove_correct resolveWidget` obligation byte-identical.
_PROOF = "prove_correct resolveWidget by\n  loom_solve"


def _reproved(new_impl, new_proof):
    """Variant with the impl block replaced AND the tactic body retuned."""
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `resolveWidgetTester provided computedDefault = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped, so
# ---- no tactic script can interfere. Every argument is a concrete `Option
# ---- Widget` literal (Widget derives DecidableEq) so `decide` reduces BOTH the
# ---- rival's extracted program and the frozen one to a literal Boolean: the
# ---- gold-side half fails because the kernel EVALUATES gold's tester and finds
# ---- `true` (gold satisfies the postcondition there), never because the term is
# ---- stuck. See the CARRIER NOTE; a stuck gold-side term would discriminate
# ---- nothing, and the audit's forgery pair below rules that out by measurement.
def _witness(provided_lit, cdefault_lit):
    return (
        "\n"
        "extract_program_for resolveWidget\n"
        "prove_precondition_decidable_for resolveWidget\n"
        "prove_postcondition_decidable_for resolveWidget\n"
        "derive_tester_for resolveWidget\n\n"
        f"example : resolveWidgetTester {provided_lit} {cdefault_lit} = false := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG (over-fit to the frozen impl's shape).
    # =====================================================================
    {
        "id": "pos-control-match",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different CORRECT impl: a `match` on `provided` instead of
        # the mut-local guard. `some w` keeps the caller's widget; `none` returns
        # the computed default. Observationally identical on every input; the
        # obligation `out = if provided.isNone then computedDefault else provided`
        # still discharges under `loom_solve`.
        "module": _rival(
            "    match provided with\n"
            "    | some w => return (some w)\n"
            "    | none => return computedDefault"),
        "rationale": (
            "POSITIVE CONTROL: a `match provided with | some w => some w | none => "
            "computedDefault` reshape of the frozen mut-guard — same two-way "
            "precedence (caller's widget on the preservation arm, computed default "
            "on the fallback arm), a completely different control-flow shape. `out "
            "= (if provided.isNone then computedDefault else provided)` still holds "
            "on the whole domain and closes under `loom_solve`. If it cannot verify, "
            "the postcondition is over-fit to the mut-guard FORM => SPEC-TOO-STRONG. "
            "(Sibling: pos-nested-ifelse.)"),
    },
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded precedence expression
        # directly, no mut-local. `out` IS `if provided.isNone then computedDefault
        # else provided`, so the ensures holds trivially; `loom_solve` closes it.
        "module": _rival(
            "    return (if provided.isNone then computedDefault else provided)"),
        "rationale": (
            "POSITIVE CONTROL: the cheapest honest correct impl returns the grounded "
            "precedence `if provided.isNone then computedDefault else provided` "
            "directly (no mut-local). `out` IS that expression, so the ensures holds "
            "on the whole domain and closes under `loom_solve`. If this fails to "
            "verify the spec is over-fit to the imperative shape (SPEC-TOO-STRONG). "
            "Also the honest no-ungrounded-echo control: the precedence is a closed "
            "function of the two inputs, not an opaque answer key, so a direct "
            "return is correct rather than a cheat. (Sibling: pos-stage-local.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — ADDED BY THE SECOND AUDIT. The first port recorded this
    # lane as VACUOUS because "this bundle declares NO `require`, so there is no
    # precondition to admit". That reason is the one the audit brief names as
    # measurably wrong: on a TOTAL carrier the analogue of PRECOND-TOO-STRONG is
    # the OBLIGATION being unsatisfiable at exactly an F2P-shaped input, and a
    # positive that discharges the obligation AT that concrete input — by
    # evaluation, as an in-region `assert`, before closing the frozen obligation
    # verbatim — tests it directly. It is not vacuous and it is not free: the
    # `assert` is a live VC (proved below), and it pins the two facts that make
    # the obligation non-degenerate at the F2P shape:
    #   (a) at the F2P-shaped point — a caller-supplied widget competing with a
    #       DIFFERENT field-derived default — the post-image evaluates to the
    #       CALLER's widget, not the default. This is the arm the change adds, so
    #       an obligation unsatisfiable here would be a spec that pins behaviour
    #       no impl can deliver at the very input the failing test drives.
    #   (b) at the mirror point (caller supplied none) it evaluates to the
    #       DEFAULT, and the two results are DISTINCT (`some {id:=1} ≠ some
    #       {id:=2}`). That last conjunct is what stops the case being degenerate:
    #       without it, an obligation that mapped every input to one value would
    #       satisfy (a) and (b) simultaneously and still test nothing.
    # The impl is kept BYTE-IDENTICAL to the frozen one so the method's own
    # `ensures` still discharges; only the elided tactic body gains the `decide`
    # arm that clears the assert's VC. LIVENESS MEASURED, not assumed: the same
    # case with conjunct (a) flipped to claim the DEFAULT wins fails to build
    # (`Tactic \`decide\` proved that the proposition … is false`), so the assert
    # really is carrying the claim rather than decorating it.
    # =====================================================================
    {
        "id": "admiss-f2p-precedence-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _reproved(
            "    assert (with_name_prefix `admiss\n"
            "      (((if (some {id := 1} : Option Widget).isNone then (some {id := 2} : Option Widget)\n"
            "         else (some {id := 1} : Option Widget)) = some {id := 1}) ∧\n"
            "       ((if (none : Option Widget).isNone then (some {id := 2} : Option Widget)\n"
            "         else (none : Option Widget)) = some {id := 2}) ∧\n"
            "       ((some {id := 1} : Option Widget) ≠ (some {id := 2} : Option Widget))))\n"
            + _IMPL,
            "prove_correct resolveWidget by\n  loom_solve <;> decide"),
        "rationale": (
            "ADMISSIBILITY on a total carrier: the obligation `out = (if "
            "provided.isNone then computedDefault else provided)` is SATISFIABLE "
            "and NON-DEGENERATE at the F2P-shaped input. The in-region assert "
            "discharges by evaluation that at the F2P shape — a caller-supplied "
            "widget competing with a DIFFERENT field-derived default — the "
            "post-image is the CALLER's widget (`some {id:=1}`), that at the "
            "mirror point (caller supplies none) it is the DEFAULT (`some "
            "{id:=2}`), and that those two results are DISTINCT. Were the "
            "obligation unsatisfiable at that point the spec would pin behaviour "
            "no impl can deliver at exactly the input the failing test drives "
            "(the total-carrier analogue of PRECOND-TOO-STRONG); were it "
            "degenerate, a spec collapsing every input to one value would read "
            "like a live one. The impl is kept byte-identical to the frozen one "
            "so the method's own ensures discharges too, and the assert is LIVE "
            "— flipping the first conjunct to claim the default wins makes the "
            "build FAIL. (Sibling: admiss-f2p-selfcall, re-aimed from "
            "precondition admissibility — this bundle has no `require` — to "
            "obligation satisfiability at the F2P shape.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each a LOOP-FREE closed form with a machine-checked
    # refutation witness at a DISTINCT concrete input and the refinement argument
    # for why its faithful real counterpart would NOT resolve the failing test.
    # =====================================================================

    # ---- PRESERVATION arm: overwrite the caller's widget with the default ----
    {
        "id": "weak-unconditional-overwrite",
        "kind": "uniqueness",
        "expect": "reject",
        # THE central attack and the literal pre-patch behaviour: apply the
        # computed default whenever one exists, WITHOUT the "caller supplied none"
        # guard, so a caller-supplied widget is clobbered by the field-derived
        # default. Correct on the fallback arm; diverges on the preservation arm.
        "module": _rival(
            "    let mut widget := provided\n"
            "    if computedDefault.isSome then\n"
            "      widget := computedDefault\n"
            "    return widget"),
        "refinement": (
            "this is the pre-change behaviour the fix corrects: the field-derived "
            "default is applied unconditionally, so a widget the caller supplied "
            "explicitly is overwritten whenever a default exists. In the failing "
            "scenario the caller supplies a widget explicitly for a field whose "
            "unchanged selection chain would otherwise pick a different default; a "
            "faithful counterpart that dropped the caller-supplied guard would "
            "replace the caller's widget with that default, and the test that checks "
            "the resolved widget is the one the caller supplied FAILS — it is "
            "exactly the reported bug, so it would NOT resolve. Correct on the "
            "fallback arm (caller supplied none), a true partial-domain break."),
        "rationale": (
            "REJECT from `out = (if provided.isNone then computedDefault else "
            "provided)` via the PRESERVATION arm: when `provided = some w` and "
            "`computedDefault = some d` with `d ≠ w`, the spec pins `out = some w` "
            "but this rival returns `some d`. Verifying would be SPEC-TOO-WEAK (the "
            "caller-precedence guarantee — the fix itself — unpinned). Refuted at "
            "`provided = some {id:=1}`, `computedDefault = some {id:=2}`: the rival "
            "returns `some {id:=2}`, the spec `some {id:=1}`. Varies `provided` to "
            "`some` (preservation arm). (Sibling: weak-no-guard-overwrite.)"),
        "witness": _witness("(some {id := 1})", "(some {id := 2})"),
    },

    # ---- FALLBACK arm: drop the default entirely ----
    {
        "id": "weak-drop-default",
        "kind": "uniqueness",
        "expect": "reject",
        # Never apply the computed default — always return the caller's slot even
        # when it is empty. Correct on the preservation arm; wrong on the fallback
        # arm whenever a default exists (returns `none` where the spec pins the
        # default).
        "module": _rival(
            "    let widget := provided\n"
            "    return widget"),
        "refinement": (
            "a faithful counterpart that never applied the field-derived default "
            "would leave the widget unset for a field the caller did NOT supply a "
            "widget for — every field that relies on the autocomplete / raw_id / "
            "filter default would silently get no special widget. The tests that "
            "assert the field-derived widget is selected when the caller supplies "
            "none FAIL, so it would NOT resolve. Correct on the preservation arm "
            "(caller supplied a widget), a true partial-domain break on the arm "
            "opposite the overwrite rival — the two do NOT share a witness."),
        "rationale": (
            "REJECT from `out = (if provided.isNone then computedDefault else "
            "provided)` via the FALLBACK arm: when `provided = none` and "
            "`computedDefault = some d`, the spec pins `out = some d` but this rival "
            "returns `none`. Verifying would be SPEC-TOO-WEAK (the default-applied "
            "guarantee unpinned). Refuted at `provided = none`, `computedDefault = "
            "some {id:=2}`: the rival returns `none`, the spec `some {id:=2}`. Varies "
            "`provided` to `none` and `computedDefault` to `some` — the fallback arm "
            "the overwrite rival never probes. (No direct sibling: nagini pins the "
            "same arm through its priority-default clauses (1)/(2)/(3), which this "
            "carrier folds into the single free `computedDefault`.)"),
        "witness": _witness("none", "(some {id := 2})"),
    },

    # ---- FALLBACK arm: fabricate a widget when no default exists ----
    {
        "id": "weak-fabricate-default",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep the caller's widget when supplied, but on the fallback arm fabricate
        # a widget rather than returning the (possibly absent) computed default.
        # Correct when `provided = some` and when `computedDefault = some d` HAPPENS
        # to equal the fabricated widget; wrong whenever a caller supplies none and
        # the field has no default (computedDefault = none), where the spec pins
        # `out = none` (nothing fabricated).
        "module": _rival(
            "    match provided with\n"
            "    | some w => return (some w)\n"
            "    | none => return (some {id := 0})"),
        "refinement": (
            "a faithful counterpart that forced a widget onto a field even when the "
            "caller supplied none AND the unchanged selection chain fired no branch "
            "(no autocomplete / raw_id / filter default) would render a special "
            "widget for a plain field that should get the framework's ordinary "
            "default (no widget override). The tests that expect a plain field with "
            "no caller widget and no field-derived default to receive NO override "
            "FAIL, so it would NOT resolve. Correct on the preservation arm."),
        "rationale": (
            "REJECT from `out = (if provided.isNone then computedDefault else "
            "provided)` via the FALLBACK arm at `computedDefault = none`: when "
            "`provided = none` and `computedDefault = none` the spec pins `out = "
            "none`, but this rival returns `some {id:=0}`. Verifying would be "
            "SPEC-TOO-WEAK (the no-fabrication guarantee unpinned). Refuted at "
            "`provided = none`, `computedDefault = none` — the ONLY witness that "
            "drives `computedDefault` to `none`, a point neither other rival "
            "probes. (Sibling: weak-establish-no-test — establish a default where "
            "the spec pins none.)"),
        "witness": _witness("none", "none"),
    },

    # ---- PRESERVATION arm at `computedDefault = none`: keep the caller's widget
    # ---- only when a default ALSO exists ----
    {
        "id": "weak-preserve-only-when-default",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. The three rivals above leave the fourth quadrant of the
        # (provided, computedDefault) square — `(some w, none)` — entirely
        # unprobed, and it is a quadrant where a rival can be wrong: this one
        # honours the caller's widget when a field-derived default happens to
        # exist, but drops it on the floor when the field has no default at all.
        # Correct at (some w, some d), (none, some d) and (none, none); wrong at
        # exactly (some w, none). None of the other three witnesses can see it,
        # so without this case the preservation arm is only ever attacked at
        # `computedDefault = some` and the postcondition's independence from
        # `computedDefault` on that arm is untested.
        "module": _rival(
            "    match provided, computedDefault with\n"
            "    | some w, some _ => return (some w)\n"
            "    | some _, none   => return none\n"
            "    | none,   dflt   => return dflt"),
        "refinement": (
            "a faithful counterpart would honour the caller's widget only for a "
            "field whose unchanged selection chain would ALSO have produced a "
            "default of its own, and silently discard it for a plain field the "
            "chain fires no branch for — the caller's explicit request is dropped "
            "in precisely the case where nothing else was competing for the slot. "
            "Every test that supplies a widget for an ordinary field and expects "
            "to get that widget back FAILS, so it would NOT resolve. It also "
            "cannot be dismissed as an unreachable shape: it is correct on the "
            "whole fallback arm and correct on the preservation arm whenever a "
            "default exists, so only the fourth quadrant separates it from gold — "
            "a true partial-domain break at a point no other rival reaches."),
        "rationale": (
            "REJECT from `out = (if provided.isNone then computedDefault else "
            "provided)` via the PRESERVATION arm at `computedDefault = none`: when "
            "`provided = some w` and `computedDefault = none` the spec pins `out = "
            "some w` — the `else provided` branch does not consult "
            "`computedDefault` at all — but this rival returns `none`. Verifying "
            "would be SPEC-TOO-WEAK: the preservation arm's INDEPENDENCE from "
            "`computedDefault` would be unpinned, leaving a spec that only "
            "guarantees the caller's widget survives when a default also exists. "
            "Refuted at `provided = some {id:=1}`, `computedDefault = none` — the "
            "fourth quadrant, which weak-unconditional-overwrite (some 1, some 2), "
            "weak-drop-default (none, some 2) and weak-fabricate-default (none, "
            "none) all miss. Varies `computedDefault` to `none` while `provided` "
            "stays `some`, the one combination the battery otherwise never "
            "reaches. (No sibling: nagini's dict carrier states preservation as a "
            "quantified Old-value clause (P) that ranges over this point "
            "implicitly rather than as a separate rival.)"),
        "witness": _witness("(some {id := 1})", "none"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 9 SPEC cases (2
# soundness positives, 1 admissibility, 6 uniqueness rivals) plus a 2-case AXIOM
# lane. It contracts a FIVE-input dict-mutating routine `select_component` whose
# postcondition has SIX top-level clauses: preservation (P), three priority
# defaults (1/2/3), no-establish (4), and a forward no-spurious-key frame (F).
#
# This velvet bundle models a DELIBERATELY NARROWER carrier (mapping.md §2,
# refinement.md §A): the whole priority-selection chain that computes WHICH
# default applies is UNCHANGED by the fix and is folded into the single free
# input `computedDefault`; what the fix actually adds — and all this bundle
# models — is the PRECEDENCE of a caller-supplied widget over that default,
# `out = (if provided.isNone then computedDefault else provided)`. That
# narrowing collapses the three priority-order clauses into one free input and
# removes the dict/frame surface entirely.
#
#   sibling case                kind          -> here                        disposition
#   -------------------------------------------------------------------------------------
#   pos-nested-ifelse           soundness     -> pos-control-match           PORTED (reshaped)
#   pos-stage-local             soundness     -> pos-control-direct          PORTED (reshaped)
#   admiss-f2p-selfcall         admissibility -> admiss-f2p-precedence-nondegenerate
#                                                                            PORTED (re-aimed, audit 2)
#   weak-no-guard-overwrite     uniqueness    -> weak-unconditional-overwrite PORTED (the fix)
#   weak-always-tertiary        uniqueness    -> (none)                      VACUOUS (carrier)
#   weak-priority-swap          uniqueness    -> (none)                      VACUOUS (carrier)
#   weak-wrong-identity         uniqueness    -> (none)                      VACUOUS (carrier)
#   weak-establish-no-test      uniqueness    -> weak-fabricate-default      PORTED
#   weak-spurious-key           uniqueness    -> (none)                      VACUOUS (carrier)
#   (no sibling)                uniqueness    -> weak-drop-default           ADDED
#   (no sibling)                uniqueness    -> weak-preserve-only-when-default ADDED (audit)
#   AXIOM_TESTS (2)             axiom         -> (none)                      DROPPED (G-AX)
#
# 2 uniqueness ported + 2 added (one by audit 1), 2 soundness ported, 1
# admissibility ported/re-aimed (audit 2); 2 nagini ordering rivals vacuous on
# this carrier, 1 frame rival vacuous, 2 axiom cases dropped; nagini's
# wrong-identity rival re-derived as EXPRESSIBLE (see below) and subsumed by an
# existing case at the same input.
# Total 7 SPEC cases (2 soundness, 1 admissibility, 4 uniqueness).
#
# PORTED (2 positive controls): pos-nested-ifelse (a spelling reshape of the
#   priority chain) ports to pos-control-match — a `match provided` reshape of the
#   frozen mut-guard, a maximally different control-flow shape that is still
#   observationally identical. pos-stage-local (compute-then-store-once) ports to
#   pos-control-direct — return the grounded precedence expression directly. Both
#   verified to build under `loom_solve`.
# PORTED (weak-no-guard-overwrite -> weak-unconditional-overwrite): the literal
#   pre-patch bug — apply the default unconditionally, clobbering a caller-supplied
#   widget. Rejected by the PRESERVATION arm; refuted at (some 1, some 2). This is
#   the fix itself and the F2P heart.
# PORTED (weak-establish-no-test -> weak-fabricate-default): nagini's clause (4)
#   rival establishes a default where the spec pins none; here the analogue
#   fabricates a widget on the fallback arm when `computedDefault = none`, where
#   the spec pins `out = none`. Rejected by the FALLBACK arm at computedDefault =
#   none; refuted at (none, none).
# ADDED (weak-drop-default): nagini pins the "correct default when absent" behaviour
#   through its three priority-default clauses (1)/(2)/(3), which this carrier folds
#   into the single free `computedDefault`. So the FALLBACK arm (`provided.isNone
#   ==> out = computedDefault`) needs its own attack: drop the default entirely and
#   always return the caller's (empty) slot. Rejected by the FALLBACK arm; refuted
#   at (none, some 2) — the point that exercises `computedDefault = some` on the
#   fallback arm, which neither other rival does.
# VACUOUS-BY-CARRIER (weak-always-tertiary, weak-priority-swap): both attack the
#   PRIORITY ORDER of the field-derived default — WHICH of autocomplete/raw_id/
#   filter fires. That selection chain is UNCHANGED by the fix and is abstracted to
#   the single free input `computedDefault` (mapping.md §2, §3; refinement.md §A2),
#   so this bundle makes no behavioural claim about it. The ordering lives INSIDE
#   the computation of `computedDefault`, which is a free input here, not a term
#   any impl of `resolveWidget` computes: there is literally no expression a rival
#   could reorder, hence no clause of THIS spec to violate and no discriminating
#   witness. DROPPED rather than faked (porting map: rivals for a behaviour this
#   bundle does not model).
# EXPRESSIBLE, PORTED BY AUDIT (weak-wrong-identity): the original port filed this
#   with the two ordering rivals as "vacuous by carrier". That was WRONG, and the
#   audit landed it. Nagini's (W4) stores the WRONG DEFAULT IDENTITY on a branch
#   whose guard it keeps; the carrier analogue does not need the selection chain at
#   all — a rival can return a widget DERIVED FROM but unequal to `computedDefault`
#   on the fallback arm (`computedDefault.map (fun w => {id := w.id + 1})`), which
#   the spec's `then computedDefault` branch pins exactly. Built under audit: the
#   rival fails to verify (`unsolved goals`, residual goal `Option.map (fun w =>
#   {id := w.id + 1}) computedDefault = if provided.isNone …`) and its witness at
#   `(none, some {id := 2})` elaborates green against it (exit 0), so it IS
#   expressible and discriminable. It is NOT added as a separate case only because
#   weak-drop-default already refutes at that exact input by the same `then
#   computedDefault` clause — a second rival there would raise the case count
#   without reaching a new point. The identity distinction the carrier DOES lose is
#   only WHICH SOURCE the default came from (autocomplete vs raw_id vs filter),
#   since all three are folded into one free `Option Widget`; the distinction
#   between the default and a wrong value is fully preserved and is attacked.
# VACUOUS (weak-spurious-key): nagini holds `options` at full permission and its
#   (F) frame clause forbids adding a stray key; the rival stores an unrelated
#   option. This backend is referentially transparent — the output is a single
#   `Option Widget`, there is no dict/heap/aliasing/Old and no `mut` binder over
#   any input — so there is no container to add a stray key to and no frame clause
#   to violate. No carrier analogue; NOT fabricated.
# PORTED / RE-AIMED (admiss-f2p-selfcall -> admiss-f2p-precedence-nondegenerate),
#   BY AUDIT 2. The first port filed this VACUOUS on the reasoning that "this
#   bundle declares NO `require`, so there is no precondition to admit, and the
#   post-image is a total function so `out = …` is satisfiable everywhere by
#   construction". Both halves are true statements and neither licenses dropping
#   the lane: the admissibility lane is what detects PRECOND-TOO-STRONG, and on a
#   TOTAL carrier its analogue is the obligation being unsatisfiable — or
#   DEGENERATE — at exactly an F2P-shaped input. "Satisfiable by construction" is
#   an argument; the gate exists to demand the machine-checked form of it, which is
#   an in-region `assert` discharging the obligation AT the F2P shape by evaluation
#   before the frozen obligation closes verbatim. Landed and measured: the case
#   VERIFIES (exit 0), and the same case with its first conjunct flipped to claim
#   the field-derived default wins FAILS (exit 1, `Tactic `decide` proved that the
#   proposition … is false`), so the assert is live rather than decorative. The
#   non-degeneracy conjunct (`some {id:=1} ≠ some {id:=2}`) is what distinguishes
#   this from a probe an all-collapsing obligation would also pass.
# AXIOM_TESTS (2): dropped. The axiom lane is G-AX's job; this bundle consumes no
#   axiom `ensures` (meta.json axioms = [], deep_model_references = []; the changed
#   op is modeled deeply as the Option-precedence, validated by G-CONF), and this
#   gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The sole `ensures` clause has TWO binders — `provided
#   : Option Widget` and `computedDefault : Option Widget` — and TWO independent
#   arms (preservation when `provided.isSome`, fallback when `provided.isNone`).
#   After the audit's addition the four reject witnesses probe FOUR DISTINCT input
#   points, which is the COMPLETE (provided, computedDefault) square (pts = 4):
#     * weak-unconditional-overwrite     (some 1, some 2)   preservation arm, default present
#     * weak-preserve-only-when-default  (some 1, none)     preservation arm, default absent
#     * weak-drop-default                (none,   some 2)   fallback arm, default present
#     * weak-fabricate-default           (none,   none)     fallback arm, default absent
#   `provided` ranges over {some, none} and `computedDefault` ranges over {some,
#   none}, and the variation is MEANINGFUL at every point rather than two spellings
#   of one: each of the four rivals is refuted at its own quadrant and is CORRECT at
#   the other three, so every witness input is a point where the spec's verdict
#   actually changes. Both binders are load-bearing on both arms — `provided`
#   selects the arm, and `computedDefault` separates the two witnesses within EACH
#   arm (drop-default vs fabricate-default on the fallback arm;
#   unconditional-overwrite vs preserve-only-when-default on the preservation arm).
#   That last pair is what pins the preservation arm's INDEPENDENCE from
#   `computedDefault`: `else provided` must ignore the default, not merely defer to
#   the caller when a default happens to exist. No two rivals share an input.
# WITNESS DISCRIMINATION (re-derived under audit: two real builds per reject case
#   via scripts/lean_verify.sh, exit codes observed, not predicted). Each witness
#   ELABORATES green against its loop-free rival (exit 0) and FAILS against the
#   frozen solution (exit 1) with `Tactic \`decide\` proved that the proposition
#   resolveWidgetTester <p> <d> = false is false` — a SEMANTIC refutation at a
#   computed value, not a stuck term, a missing identifier, a type error or a
#   timeout (see the CARRIER NOTE; the docstring's earlier "stays STUCK" account of
#   this half was factually wrong and has been corrected). The same witnesses were
#   additionally built against BOTH correct positive controls and failed there too
#   (exit 1, same semantic refutation), confirming they discriminate WRONGNESS and
#   not the frozen impl's mut-loop SHAPE — the trap the witness requirement exists
#   to catch. No witness binds a hypothesis (Widget is a concrete DecidableEq
#   structure), so there is no joint-satisfiability obligation and the gate's
#   consistency probe is correctly not triggered. No `sorry`/`admit`/
#   `native_decide`/`axiom` in any variant or witness.
# SPEC-TOO-WEAK PROBES THAT FOUND NOTHING (attack D, run under audit; all four
#   rejected, so no spec hole): return `computedDefault` unconditionally (ignore the
#   caller); the two arms SWAPPED (`if provided.isNone then provided else
#   computedDefault`); default-wins precedence (fall back to `provided` only when
#   the default is absent); and the fallback arm returning a widget derived from but
#   unequal to the default. Each failed with an `unsolved goals` residual naming the
#   ensures, i.e. the single clause is strong enough to pin all four.
# SPEC-TOO-STRONG PROBES (attack E, run under audit). Three correct reshapes were
#   tried beyond the two shipped controls. `match provided with | none =>
#   computedDefault | some _ => provided` verifies under the frozen `loom_solve`
#   unchanged (exit 0). Two more — `provided.orElse (fun _ => computedDefault)` and
#   the mirror-image mut-guard (`let mut widget := computedDefault; if
#   provided.isSome then widget := provided`) — are NOT closed by bare `loom_solve`,
#   but both verify once the tactic body is extended to case on `provided` (exit 0
#   for each). So these are PROOF-SCRIPT gaps in a tactic body that is not part of
#   the spec, NOT soundness holes: no faithful correct impl was found that the
#   frozen POSTCONDITION rejects. They are not shipped as controls because a
#   positive control is most informative when it discharges under the frozen proof
#   unchanged.
# SECOND-AUDIT PROBES (independent re-derivation; every exit code below observed
#   via scripts/lean_verify.sh, none predicted).
#   WITNESS FORGERY PAIR (attack B'), the check the first audit did NOT run. For
#   each of the four reject cases the witness was rebuilt against the rival (exit 0)
#   and against the frozen solution (exit 1), AND a FORGERY differing only in the
#   claim — `= true` in place of `= false`, i.e. asserting the frozen impl IS
#   correct at that input — was built on BOTH sides. The forgery VERIFIES on gold
#   (exit 0) and FAILS on the rival (exit 1, `… = true is false`), the exact mirror
#   of the honest witness. So gold's exit code TRACKS THE CLAIM rather than being a
#   constant property of the carrier: these are real refutations, not the hollow
#   stuck-term class the brief warns about. This is the strongest available evidence
#   and it is what upgrades the first audit's "the error text looks semantic" to a
#   measurement.
#   NEW WRONG IMPLS, all REJECTED, so still no spec hole: (a) an IDENTITY-specific
#   hole that is correct at all four of the battery's witness points and wrong only
#   at `provided = some {id := 7}` — the sharpest test of whether the four-point
#   square is doing the work or merely the {none,some} shapes are, and the spec
#   pins it anyway (residual goal over `i.id == 7`); (b) wrong identity on the
#   PRESERVATION arm (`provided.map (fun w => {id := w.id + 1})`), the arm the first
#   audit's identity probe never reached (it hit the fallback arm only); (c) a
#   canonicalising collapse returning `some {id := 1}` whenever either input is
#   `some`. Each left an `unsolved goals` residual naming the single ensures.
#   NEW CORRECT RESHAPES: `match provided, computedDefault with | some w, _ => some
#   w | none, some d => some d | none, none => none` — a four-way match on BOTH
#   binders, the most different shape available — VERIFIES under the frozen
#   `loom_solve` unchanged (exit 0). The `isSome`-guard mirror (`if provided.isSome
#   then provided else computedDefault`) does not close under bare `loom_solve`
#   (exit 1, residual comparing the two if-expressions) but VERIFIES once the tactic
#   cases on `provided` (exit 0) — the same PROOF-SCRIPT gap class as E1/E2 above,
#   not a SPEC-TOO-STRONG finding, and independently re-confirmed here rather than
#   taken on the first audit's word.
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
AXIOM_TESTS = []
