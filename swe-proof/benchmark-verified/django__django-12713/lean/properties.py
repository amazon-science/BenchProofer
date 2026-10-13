# -*- coding: utf-8 -*-
"""properties.py — G-PBT falsification battery for django__django-12713 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
single ``theorem correct_resolveWidget`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models the selection as an in-place mutation of a ``Dict[int,int]`` options bag
held at FULL permission, and pins each row against grounded ``@Pure`` integer
constants. This Lean bundle models the SAME single purely-functional core — the
choice of which widget a multi-valued relation field ends up with — over an
``Option Widget`` result computed from ``incoming`` (the caller's already-chosen
widget) and four classification lists. Every nagini reject rival carries over as
an attack on one of the two arms of the postcondition (the caller-precedence arm
or the configuration-cascade arm), or as a faithful correct positive. Two
nagini classes are VACUOUS on this carrier and are recorded as such in the
accounting block at the bottom (no substitute is fabricated).

DEFENDED SURFACE (one modeled behavior; a single equation with two arms).
``problem_spec_resolveWidget name incoming auto raw vert horiz result`` pins the
result EXACTLY to:

  * (A PRECEDENCE arm)  ``incoming = some w  ⟹  result = some w`` — a widget the
    caller already chose is kept exactly as supplied and the configuration is not
    consulted at all. THIS is the fix: pre-fix the configuration cascade ran
    unconditionally and overwrote the caller's widget. Note this is TWO
    obligations, and each has its own rival: the configuration must not win
    (``weak-overwrite`` deletes the guard) AND the supplied ``w`` must come back
    verbatim (``weak-mangle-caller`` keeps the guard and perturbs ``w``).
  * (B CASCADE arm)  ``incoming = none  ⟹  result = defaultWidget …``, where the
    configuration choice is itself a priority cascade with four sub-outcomes:
      - (B-auto)   ``name ∈ auto``                        ⟹ autocomplete
      - (B-raw)    ``name ∉ auto, name ∈ raw``            ⟹ raw-id
      - (B-filt)   ``name ∉ auto,raw, name ∈ vert++horiz`` ⟹ filtered (vertical
                   flag = ``name ∈ vert``)
      - (B-none)   ``name`` in none of the groups          ⟹ no widget (``none``)

BINDER STRUCTURE. The spec predicate has SIX input binders: ``name`` (the field
name), ``incoming`` (the caller-supplied widget option), and the four
classification lists ``auto`` / ``raw`` / ``vert`` / ``horiz``. All six are
load-bearing and all are varied across the reject witnesses (see the point-spread
block at the bottom). The seven reject witnesses probe seven DISTINCT input
tuples (``pts=7``).

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling holds ``options`` at
    FULL permission because the repo mutates the ``**kwargs`` dict in place; its
    frame defence is the PRESERVATION clause on the entry component. On this
    referentially transparent carrier there is no heap, no ``mut`` input binder,
    no aliasing, and no read-only cell to overwrite — the analogous defence is
    simply the PRECEDENCE arm (A): a caller widget must be returned unchanged.
    That arm IS attacked (``weak-overwrite``, the literal pre-patch bug). The
    nagini SPURIOUS-KEY frame rival (``weak-spurious-key``: store a stray extra
    option key) is genuinely VACUOUS here — the result is a single
    ``Option Widget``, not a container, so there is no stray key to add and no
    forward-frame clause to violate. No substitute probe is fabricated.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result`` is
    pinned by ``defaultWidget`` structurally over the four input lists (membership
    + the vertical flag), with no opaque answer key an implementation could echo.
    In its place the battery carries honest cheapest-implementation POSITIVE
    CONTROLS that must verify.

  * DIVERGENCE / NON-TERMINATION — VACUOUS on lean. ``implementation_resolveWidget``
    is a total Lean ``def`` (``Id.run do`` with no recursion); a diverging
    implementation cannot be written at all, so there is nothing to port. (This is
    the genuinely-vacuous lean case, NOT the velvet ``partial`` spec hole.)

  * PARTIAL-DOMAIN / VALUE — APPLIES. The remaining rivals are correct on part of
    the domain but diverge where the fix or the priority order bites: overwrite a
    caller widget (attacks A), collapse the cascade so the same widget is always
    stored (attacks B-auto/B-raw), swap the auto/raw priority (attacks B-auto),
    render the wrong widget kind on the winning branch (attacks B-auto), establish
    a widget when the name matches nothing (attacks B-none), and compute the wrong
    vertical flag on the filtered branch (attacks B-filt).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so a
rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet that states the spec predicate at ONE concrete,
fully-ground input and closes ``¬ problem_spec_resolveWidget … (implementation…)``
by ``decide`` (the ``Id.run do`` body and the ``defaultWidget`` cascade both
reduce under ``decide`` on ground list literals). Each witness binds NOTHING in
its head — all inputs are ground literals — so there are no hypotheses whose
consistency could be in question. Each was checked with two real ``lake env lean``
builds to HOLD of its rival and to FAIL on the frozen solution, so it
discriminates rather than asserting a tautology.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart is a
widget-selection block that mis-decides for some field configuration the tests
exercise, so the F2P override case (or a PASS_TO_PASS widget-selection test) reads
back the wrong widget kind and the faithful patch would NOT resolve.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the changed decision is modeled deeply); the axiom lane belongs to
G-AX, and the nagini ``AXIOM_TESTS`` are dropped.
"""
from pathlib import Path

INSTANCE = "django__django-12713"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text(encoding="utf-8")


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


def _swaps(src, *pairs):
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The guarded configuration cascade in the impl region, INCLUDING its leading
# comment line. Removing the guard (dropping this whole block for the unguarded
# cascade) is the pre-patch bug.
_GUARD_BLOCK = (
    "  -- Only consult the configuration when the caller chose nothing.\n"
    "  if widget.isNone then\n"
    "    if name ∈ auto then\n"
    "      widget := some .autocomplete\n"
    "    else if name ∈ raw then\n"
    "      widget := some .rawId\n"
    "    else if name ∈ (vert ++ horiz) then\n"
    "      widget := some (.filtered (name ∈ vert))"
)

# The inner priority cascade only (4-space indented; sits inside the guard). Used
# by rivals that keep the guard but reshape the priority decision.
_INNER = (
    "    if name ∈ auto then\n"
    "      widget := some .autocomplete\n"
    "    else if name ∈ raw then\n"
    "      widget := some .rawId\n"
    "    else if name ∈ (vert ++ horiz) then\n"
    "      widget := some (.filtered (name ∈ vert))"
)

# The autocomplete assignment (winning primary branch). Unique.
_AUTO_ASSIGN = "      widget := some .autocomplete"

# The single `let mut` seed of the accumulator from the caller's option. Unique.
# Used by the rival that carries the caller's widget through NOT-verbatim, which
# attacks the "kept EXACTLY as supplied" half of arm A (the guard can be present
# and still not preserve `w` itself).
_MUT_SEED = "  let mut widget := incoming\n"

# The filtered assignment with its computed vertical flag. Unique in the file
# (the spec's `defaultWidget` writes `some (.filtered (name ∈ vert))` WITHOUT the
# `widget :=` prefix, so this anchor lies wholly inside the impl region).
_FILT_ASSIGN = "      widget := some (.filtered (name ∈ vert))"

# The `none` branch of the frozen proof (proof region). Used by the staged-local
# positive to re-prove for its reshaped impl. Lies wholly inside
# `-- proof-start`/`-- proof-end`, so same_spec is untouched and the
# `correct_resolveWidget` STATEMENT stays byte-identical.
_PROOF_NONE = (
    "  | none =>\n"
    "    simp only [Id.run, Option.isNone_none, if_true]\n"
    "    by_cases hauto : name ∈ auto\n"
    "    · simp only [hauto, if_true]; rfl\n"
    "    · by_cases hraw : name ∈ raw\n"
    "      · simp only [hauto, hraw, if_true, if_false]; rfl\n"
    "      · by_cases hvh : name ∈ (vert ++ horiz)\n"
    "        · simp only [hauto, hraw, hvh, if_true, if_false]; rfl\n"
    "        · simp only [hauto, hraw, hvh, if_false]; rfl"
)

# The frozen proof's intro line (unique) — the admissibility positive prepends a
# ground `have` before it without touching the STATEMENT or the spec view.
_P_INTRO = "  intro name incoming auto raw vert horiz"


# ---------------------------------------------------------------------------
# witness scaffold. State the spec predicate at one ground input and refute it.
# ---------------------------------------------------------------------------
def _w(name, incoming, auto, raw, vert, horiz):
    args = f"{name} {incoming} {auto} {raw} {vert} {horiz}"
    return (
        f"example : ¬ problem_spec_resolveWidget {args}\n"
        f"    (implementation_resolveWidget {args}) := by\n"
        "  unfold problem_spec_resolveWidget implementation_resolveWidget "
        "defaultWidget\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_resolveWidget` statement byte-identical.
    # =====================================================================
    {
        "id": "pos-branch-split",
        "kind": "soundness",
        "expect": "verify",
        # Keep the SAME guard and the SAME auto>raw>filtered priority, but SPLIT
        # the single filtered branch into two: test the vertical subset first
        # (emitting the vertical flag as the literal `true`), then the horizontal
        # subset. Correct because `name ∈ vert` already decides the flag on the
        # first sub-branch, so both sub-branches agree with
        # `.filtered (name ∈ vert)` on the whole `vert ++ horiz` membership set —
        # but the branch STRUCTURE genuinely differs (4 tests, not 3), so the
        # frozen `none`-branch proof no longer closes and the case must RE-PROVE:
        # `List.mem_append` splits the disjunction and each of the four leaves is
        # discharged separately. Verified: real build, exit 0.
        #
        # This REPLACES the ported nagini `pos-nested-ifelse` (S1), which was
        # VACUOUS on this carrier. That case only re-parenthesized the else-if
        # ladder into nested if/else, and Lean's `else if` is *sugar* for exactly
        # that nesting: `#print` shows the reshaped impl elaborating to a term
        # BYTE-IDENTICAL to the frozen one (923 chars, char-for-char equal), which
        # is why the frozen proof closed "unchanged". It tested no reshape at all —
        # it re-verified the frozen impl under a different spelling. A positive
        # control has to differ as a TERM, not merely as source text.
        "module": _swaps(
            _BASE,
            (_INNER,
             "    if name ∈ auto then\n"
             "      widget := some .autocomplete\n"
             "    else if name ∈ raw then\n"
             "      widget := some .rawId\n"
             "    else if name ∈ vert then\n"
             "      widget := some (.filtered true)\n"
             "    else if name ∈ horiz then\n"
             "      widget := some (.filtered (name ∈ vert))"),
            (_PROOF_NONE,
             "  | none =>\n"
             "    simp only [Id.run, Option.isNone_none, if_true, "
             "List.mem_append]\n"
             "    by_cases hauto : name ∈ auto\n"
             "    · simp only [hauto, if_true]; rfl\n"
             "    · by_cases hraw : name ∈ raw\n"
             "      · simp only [hauto, hraw, if_true, if_false]; rfl\n"
             "      · by_cases hv : name ∈ vert\n"
             "        · simp only [hauto, hraw, hv, if_true, if_false, true_or, "
             "decide_true]; rfl\n"
             "        · by_cases hh : name ∈ horiz\n"
             "          · simp only [hauto, hraw, hv, hh, if_true, if_false, "
             "or_true]; rfl\n"
             "          · simp only [hauto, hraw, hv, hh, if_false, or_self]; "
             "rfl"),
        ),
        "rationale": "POSITIVE CONTROL: structurally-different CORRECT impl — the "
        "same caller-precedence guard and the same auto>raw>filtered priority, but "
        "the filtered branch is SPLIT into a vertical-subset test (flag = literal "
        "`true`) followed by a horizontal-subset test. Faithful: on the first "
        "sub-branch `name ∈ vert` holds so the literal `true` IS `name ∈ vert`, and "
        "the two sub-branches together cover exactly `name ∈ vert ++ horiz`; both "
        "arms A and B are unchanged, so the spec equation holds on every input. "
        "Unlike a re-parenthesized ladder this is a genuinely different elaborated "
        "term (4 branch tests, not 3), so the frozen proof does NOT close and the "
        "case re-proves inside the proof region (`List.mem_append` + four leaves; "
        "STATEMENT byte-identical, no new axiom/lemma). If it cannot verify, the "
        "spec is over-fit to the frozen branch structure => SPEC-TOO-STRONG. "
        "Replaces nagini's pos-nested-ifelse (S1), which is vacuous here: `else if` "
        "is sugar for nested if/else, so that reshape elaborated to a term "
        "byte-identical to the frozen impl and tested nothing.",
    },
    {
        "id": "pos-stage-local",
        "kind": "soundness",
        "expect": "verify",
        # Compute-then-store-once reshape: inside the guard, stage the chosen
        # widget through a typed local, then perform ONE assignment. A genuinely
        # different executable shape that keeps the identical guard + priority
        # decision. The `none` branch of the proof simplifies to `... ; rfl`
        # (the staged local is definitionally `defaultWidget`), re-proved inside
        # the proof region — STATEMENT byte-identical, no new axiom/lemma.
        # (Verified: real build.)
        "module": _swaps(
            _BASE,
            (_INNER,
             "    let chosen : Option Widget :=\n"
             "      if name ∈ auto then some .autocomplete\n"
             "      else if name ∈ raw then some .rawId\n"
             "      else if name ∈ (vert ++ horiz) then "
             "some (.filtered (name ∈ vert))\n"
             "      else none\n"
             "    widget := chosen"),
            (_PROOF_NONE,
             "  | none =>\n"
             "    simp only [Id.run, Option.isNone_none, if_true]\n"
             "    rfl"),
        ),
        "rationale": "POSITIVE CONTROL: compute-then-store-once reshape — stage "
        "the chosen widget through a typed local, then perform ONE guarded write. "
        "Same guard + priority decision; only the executable shape differs. The "
        "staged local is definitionally `defaultWidget`, so the `none` branch of "
        "the proof closes with `rfl` after unfolding (re-proved in the proof "
        "region; STATEMENT byte-identical, no new axiom/lemma). If it fails => "
        "SPEC-TOO-STRONG. Ports nagini's pos-stage-local (S2).",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at
    # normal, F2P-shaped inputs. The frozen theorem carries no precondition, so
    # the nagini precondition-admission self-call re-expresses as: discharge the
    # spec predicate by evaluation at the F2P shape (a caller widget present on
    # entry AND the name in a classification group — where the fix bites) AND at
    # a component-absent shape, each as a `have`, then close the frozen obligation
    # verbatim. Nothing is assumed: no new declaration, statement byte-identical,
    # ground instances are `have`s prepended to the existing tactic body.
    # (Verified: real build.)
    # =====================================================================
    {
        "id": "admiss-f2p-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            "  have _present : problem_spec_resolveWidget 0 (some (.supplied 7)) "
            "[] [] [0] []\n"
            "      (implementation_resolveWidget 0 (some (.supplied 7)) "
            "[] [] [0] []) := by\n"
            "    unfold problem_spec_resolveWidget implementation_resolveWidget "
            "defaultWidget\n"
            "    decide\n"
            "  have _absent : problem_spec_resolveWidget 0 none [0] [] [] []\n"
            "      (implementation_resolveWidget 0 none [0] [] [] []) := by\n"
            "    unfold problem_spec_resolveWidget implementation_resolveWidget "
            "defaultWidget\n"
            "    decide\n"
            + _P_INTRO),
        "rationale": "ADMISSIBILITY: the obligation is discharged at the F2P shape "
        "(a caller widget present on entry — `some (.supplied 7)` — while the name "
        "IS in a classification group, exactly where the fix bites and precedence "
        "must win) AND at a component-absent shape (`none`, name in the auto "
        "group), each by evaluation as a `have`, then the frozen obligation is "
        "closed verbatim. Verifies (else the modeled behavior would be "
        "unsatisfiable at a normal F2P input — the analogue of PRECOND-TOO-STRONG). "
        "Nothing is assumed: no new declaration, statement byte-identical, ground "
        "instances are `have`s in the existing tactic body. Ports nagini's "
        "admiss-f2p-selfcall.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P/P2P, and (b) a witness pinning
    # the violation at one concrete input.
    # =====================================================================

    # ---- the fix itself: overwrite the caller's widget (attacks arm A) ----
    {
        "id": "weak-overwrite",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-patch behavior: drop the `if widget.isNone` guard so the cascade
        # runs UNCONDITIONALLY, overwriting a caller-supplied widget with a
        # configuration-chosen one.
        "module": _swap(
            _BASE, _GUARD_BLOCK,
            "  if name ∈ auto then\n"
            "    widget := some .autocomplete\n"
            "  else if name ∈ raw then\n"
            "    widget := some .rawId\n"
            "  else if name ∈ (vert ++ horiz) then\n"
            "    widget := some (.filtered (name ∈ vert))"),
        "refinement": "this IS the pre-patch behavior: the classification cascade "
        "runs with no `caller already chose a widget` guard, so a widget the caller "
        "supplied (via the field-class override mapping) is replaced by a "
        "configuration-derived widget whenever the field name matches one of the "
        "groups. The F2P override case supplies a caller widget AND puts the name "
        "in a filtered group; a faithful patch keeping the unconditional cascade "
        "replaces the caller widget with the filtered one, so the test that asserts "
        "the caller's widget survived FAILS — the F2P is NOT resolved (it IS the "
        "bug).",
        "rationale": "REJECT from arm A (precedence): when `incoming = some w` the "
        "spec pins `result = some w`, but with the guard removed and the name in a "
        "group the rival returns the configuration widget instead. Refuted at "
        "incoming = some (.supplied 7), name in the filtered group (name=0, "
        "vert=[0]): gold keeps the supplied widget, the rival returns "
        "`filtered true`.",
        "witness": _w("0", "(some (.supplied 7))", "[]", "[]", "[0]", "[]"),
    },

    # ---- caller widget kept, but NOT verbatim (attacks arm A's "exactly") ----
    {
        "id": "weak-mangle-caller",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep the precedence guard fully intact — the configuration is genuinely
        # not consulted when the caller chose something — but carry the caller's
        # widget through with its opaque object identity ALTERED. Arm A has two
        # halves and every other rival only attacks the first: `weak-overwrite`
        # removes the guard (the configuration wins), while this one honours the
        # guard and still fails to return `some w` for the `w` supplied.
        "module": _swap(
            _BASE, _MUT_SEED,
            "  let mut widget : Option Widget := match incoming with\n"
            "    | some (Widget.supplied i) => some (Widget.supplied (i + 1))\n"
            "    | other => other\n"),
        "refinement": "keeps the caller-precedence guard but does not hand back the "
        "caller's widget itself — it substitutes a DIFFERENT widget object of the "
        "same kind. A faithful patch that guarded the cascade correctly and then "
        "re-instantiated (rather than passed through) the widget the caller put in "
        "the options bag would hand the form field a widget the caller never "
        "configured, losing whatever state that instance carried. The override case "
        "asserts on the identity/class of the widget the caller supplied, so it "
        "reads back a substitute and FAILS — NOT resolved. This is the failure mode "
        "a guard-only reading of the fix still permits.",
        "rationale": "REJECT from arm A (precedence, the EXACTLY half): when "
        "`incoming = some w` the spec pins `result = some w` for that same `w`, not "
        "merely `some` widget of the same kind, and not the configuration's choice. "
        "The guard here is intact and the configuration is never consulted, so this "
        "rival is rejected purely for failing to preserve the supplied widget's "
        "identity. Refuted at incoming = some (.supplied 7) with ALL FOUR "
        "classification lists empty (so no cascade branch could fire even without "
        "the guard — isolating identity-preservation from guard-presence): gold "
        "returns `some (.supplied 7)`, the rival returns `some (.supplied 8)`.",
        "witness": _w("9", "(some (Widget.supplied 7))", "[]", "[]", "[]", "[]"),
    },

    # ---- collapse the cascade: always store the filtered widget (attacks B) ----
    {
        "id": "weak-always-filtered",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep the guard, but ignore which group the name matches and always store
        # the filtered widget when it matches ANY group.
        "module": _swap(
            _BASE, _INNER,
            "    if name ∈ auto ∨ name ∈ raw ∨ name ∈ (vert ++ horiz) then\n"
            "      widget := some (.filtered (name ∈ vert))"),
        "refinement": "collapses the priority cascade into a single branch that "
        "renders the filtered widget for ANY classified name. A faithful patch "
        "doing this picks the filtered multi-select even for a name configured for "
        "autocomplete or raw-id; the PASS_TO_PASS widget-selection tests pin the "
        "SPECIFIC widget kind per configuration (autocomplete for autocomplete "
        "names, raw-id for raw-id names), so the faithful patch renders the wrong "
        "widget for those fields and FAILS those tests — NOT resolved.",
        "rationale": "REJECT from arm B (B-auto): when `incoming = none` and "
        "`name ∈ auto`, the spec pins the autocomplete widget, but the rival stores "
        "the filtered widget. Refuted at name=1, incoming=none, auto=[1]: gold = "
        "autocomplete, rival = filtered false.",
        "witness": _w("1", "none", "[1]", "[]", "[]", "[]"),
    },

    # ---- priority swap: raw-id checked before autocomplete (attacks B-auto) ----
    {
        "id": "weak-priority-swap",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep the guard, but test raw-id membership BEFORE autocomplete.
        "module": _swap(
            _BASE, _INNER,
            "    if name ∈ raw then\n"
            "      widget := some .rawId\n"
            "    else if name ∈ auto then\n"
            "      widget := some .autocomplete\n"
            "    else if name ∈ (vert ++ horiz) then\n"
            "      widget := some (.filtered (name ∈ vert))"),
        "refinement": "tests the raw-id group before the autocomplete group. For a "
        "name that is in BOTH groups this picks the raw-id widget where the intended "
        "behavior picks autocomplete. A faithful patch reversing that order changes "
        "which widget a dual-classified field gets, diverging from the behavior the "
        "widget-selection tests pin — NOT resolved.",
        "rationale": "REJECT from arm B (B-auto): when `incoming = none` and "
        "`name ∈ auto` (regardless of raw membership) the spec pins the autocomplete "
        "widget. At name=2, auto=[2], raw=[2] the rival stores the raw-id widget "
        "instead. Refuted at that dual-membership point (a distinct input exercising "
        "a non-empty raw list).",
        "witness": _w("2", "none", "[2]", "[2]", "[]", "[]"),
    },

    # ---- wrong widget kind on the winning branch (attacks B-auto) ----
    {
        "id": "weak-wrong-kind",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep guard + priority order, but the autocomplete branch stores the
        # raw-id widget kind instead of the autocomplete kind.
        "module": _swap(
            _BASE, _AUTO_ASSIGN, "      widget := some .rawId"),
        "refinement": "the winning (autocomplete) branch constructs the WRONG "
        "widget kind — the raw-id multi-select instead of the autocomplete one. A "
        "faithful patch building the wrong widget class on that branch renders a "
        "raw-id widget for an autocomplete field; the autocomplete widget-selection "
        "test pins the autocomplete class and FAILS — NOT resolved.",
        "rationale": "REJECT from arm B (B-auto): when `incoming = none` and "
        "`name ∈ auto` the spec pins the autocomplete widget; this rival stores the "
        "raw-id widget on that branch. Refuted at name=3, auto=[3] (a distinct "
        "auto-only membership point).",
        "witness": _w("3", "none", "[3]", "[]", "[]", "[]"),
    },

    # ---- establish a widget when the name matches nothing (attacks B-none) ----
    {
        "id": "weak-establish-none",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep guard + priority order, but in the no-match fall-through still store
        # a widget (autocomplete) instead of leaving the field without one.
        "module": _swap(
            _BASE, _INNER,
            "    if name ∈ auto then\n"
            "      widget := some .autocomplete\n"
            "    else if name ∈ raw then\n"
            "      widget := some .rawId\n"
            "    else if name ∈ (vert ++ horiz) then\n"
            "      widget := some (.filtered (name ∈ vert))\n"
            "    else\n"
            "      widget := some .autocomplete"),
        "refinement": "forces a widget onto a name that is in NONE of the "
        "classification groups (and had no caller widget). A faithful patch that "
        "assigned a widget in the fall-through case would attach a "
        "configuration-chosen widget to a plain relation field; the widget-selection "
        "test for an unclassified field expects the default (no configuration-chosen "
        "widget), so forcing one on FAILS it — NOT resolved.",
        "rationale": "REJECT from arm B (B-none): when `incoming = none` and the "
        "name is in no group, the spec pins `result = none`; this rival establishes "
        "the autocomplete widget anyway. Refuted at name=4 with all lists empty: "
        "gold = none, rival = some autocomplete.",
        "witness": _w("4", "none", "[]", "[]", "[]", "[]"),
    },

    # ---- wrong vertical flag on the filtered branch (attacks B-filt) ----
    {
        "id": "weak-vertical-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep guard + priority order + the filtered widget kind, but hard-wire the
        # vertical flag to `true` instead of computing `name ∈ vert`.
        "module": _swap(
            _BASE, _FILT_ASSIGN, "      widget := some (.filtered true)"),
        "refinement": "the filtered branch hard-wires the vertical flag to true "
        "rather than computing whether the name is in the vertical subset. A "
        "faithful patch that always passed the vertical flag would lay out a "
        "horizontal filtered field as vertical; the filtered-widget test pins the "
        "vertical flag from the name's subset membership, so a horizontally-"
        "configured field renders with the wrong orientation and the test FAILS — "
        "NOT resolved.",
        "rationale": "REJECT from arm B (B-filt): when `incoming = none` and the "
        "name is in the filtered group via the HORIZONTAL subset, the spec pins the "
        "filtered widget with vertical flag `name ∈ vert = false`; this rival emits "
        "`filtered true`. Refuted at name=5, horiz=[5], vert=[]: gold = "
        "filtered false, rival = filtered true.",
        "witness": _w("5", "none", "[]", "[]", "[]", "[5]"),
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 6 uniqueness rivals) plus an EMPTY AXIOM lane. This
# bundle models the SAME single purely-functional core (the widget-selection
# decision) and re-expresses every sibling case that has a counterpart on this
# carrier; the nagini SPURIOUS-KEY frame rival is genuinely VACUOUS here. This
# battery has 10 SPEC cases (2 soundness positives, 1 admissibility, 7 uniqueness
# rivals): one sibling positive was REPLACED as vacuous-on-this-carrier and two
# rivals were ADDED for clauses no sibling case reached (see below).
#
#   sibling case                 -> here
#   -----------------------------------------------------------------------
#   pos-nested-ifelse (S1)       -> pos-branch-split        REPLACED (S1 vacuous)
#   pos-stage-local   (S2)       -> pos-stage-local         PORTED (re-proved)
#   admiss-f2p-selfcall          -> admiss-f2p-ground       RE-EXPRESSED
#   weak-no-guard-overwrite (W1) -> weak-overwrite          PORTED  (arm A, guard)
#   weak-always-tertiary   (W2)  -> weak-always-filtered    PORTED  (arm B-auto)
#   weak-priority-swap     (W3)  -> weak-priority-swap      PORTED  (arm B-auto)
#   weak-wrong-identity    (W4)  -> weak-wrong-kind         PORTED  (arm B-auto)
#   weak-establish-no-test (W5)  -> weak-establish-none     PORTED  (arm B-none)
#   weak-spurious-key      (W6)  -> (none)                  VACUOUS (see below)
#   (none)                       -> weak-vertical-flag      ADDED   (arm B-filt)
#   (none)                       -> weak-mangle-caller      ADDED   (arm A, exactly)
#   AXIOM_TESTS (2)              -> (none)                  DROPPED (G-AX)
#
# REPLACED (pos-nested-ifelse -> pos-branch-split). The ported S1 respelled the
#   else-if ladder as nested if/else. On nagini that is a real reshape of Python
#   `elif`; in Lean `else if` IS sugar for nested `if/else`, so the "reshaped" impl
#   elaborated to a term BYTE-IDENTICAL to the frozen one (checked with `#print` on
#   both: 923 characters, char-for-char equal) — which is precisely why the frozen
#   proof closed with no edit. It re-verified the frozen implementation under a
#   different spelling, so it could not have detected a spec over-fit to the frozen
#   branch structure: a positive control has to differ as a TERM, not as source
#   text. Replaced by `pos-branch-split`, which splits the filtered branch in two
#   (4 branch tests vs 3, a genuinely distinct elaborated term) and therefore has
#   to re-prove the `none` branch. Both facts machine-checked.
# ADDED (weak-mangle-caller): arm A pins `result = some w` for the SAME `w`, which
#   is two obligations — the configuration must not win (guard present) AND the
#   supplied widget must come back verbatim. Every ported rival attacked only the
#   first: `weak-overwrite` deletes the guard. A rival that honours the guard and
#   still perturbs the supplied widget's opaque identity was unattacked, so the
#   "kept exactly as supplied" half of the defended surface rested on no rival at
#   all. Its witness fires with all four classification lists EMPTY, so no cascade
#   branch could fire even absent the guard — isolating identity-preservation from
#   guard-presence rather than re-testing `weak-overwrite`'s point.
#
# RE-EXPRESSED (admiss-f2p-ground): the nagini admissibility case asserts the
#   pinned-boolean precondition is satisfiable on a present-component and an
#   absent-component witness (a full self-call blows the Viper budget there). This
#   Lean theorem carries NO precondition, so the honest analogue is to discharge
#   the POSTCONDITION at the same two shapes (caller widget present where the fix
#   bites; caller widget absent with a classified name) by evaluation as `have`s,
#   proving the modeled behavior is satisfiable at normal F2P-shaped inputs, then
#   close the frozen obligation verbatim.
# VACUOUS (weak-spurious-key): nagini's forward no-spurious-key frame rival stores
#   a stray extra key in the mutated options DICT. This carrier's result is a
#   single `Option Widget`, not a container — there is no stray key to add and no
#   forward-frame clause to violate. The class is vacuous; no substitute is
#   fabricated. Its sibling PRESERVATION concern (do not clobber the caller's
#   entry) IS ported as the central `weak-overwrite` rival on arm A.
# VACUOUS (frame/permission mutation, divergence/non-termination): see the
#   ADVERSARIAL READ in the module docstring. Referential transparency collapses
#   the frame class (no `mut` input, no aliasing); a total Lean `def` collapses
#   the divergence class (a diverging impl cannot be written). No substitutes.
# ADDED (weak-vertical-flag): the nagini rivals attack the caller-precedence guard
#   and the priority/identity of the chosen widget, but none attacks the vertical
#   flag the filtered branch computes (`name ∈ vert`). That flag is a genuine,
#   load-bearing sub-clause of the SAME modeled spec (arm B-filt), so a rival that
#   hard-wires it is added — not a fabricated rival for an unmodeled behavior.
#
# POINT SPREAD. The seven reject witnesses probe seven DISTINCT input tuples:
#   (name, incoming, auto, raw, vert, horiz) =
#     (0, some (.supplied 7), [], [], [0], [])   weak-overwrite       arm A guard
#     (9, some (.supplied 7), [], [], [], [])    weak-mangle-caller   arm A exactly
#     (1, none,               [1], [], [], [])   weak-always-filtered  arm B-auto
#     (2, none,               [2], [2], [], [])  weak-priority-swap    arm B-auto
#     (3, none,               [3], [], [], [])   weak-wrong-kind       arm B-auto
#     (4, none,               [], [], [], [])    weak-establish-none   arm B-none
#     (5, none,               [], [], [], [5])   weak-vertical-flag    arm B-filt
#   Across them `incoming` takes both `some` and `none`; `name` ranges over 0..5
#   and 9; and `auto`/`raw`/`vert`/`horiz` each take empty and non-empty shapes,
#   with the membership-bearing list differing per witness — so no input binder is
#   pinned. The two arm-A points are deliberately complementary rather than two
#   spellings of one point: the first has `vert=[0]` so a cascade branch WOULD fire
#   (isolating guard-presence), the second has every list empty so none could
#   (isolating identity-preservation).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (the decision is modeled deeply), so there is nothing to probe and the
# gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
