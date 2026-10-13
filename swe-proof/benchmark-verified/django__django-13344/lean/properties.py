"""properties.py — G-PBT falsification battery for django__django-13344 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
single ``theorem correct_initComponent`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
contracts TWO functions — ``configure_handler`` (three facts P/S/A) and
``configure_settings_handler`` (adds the store-selection facts N/R/Q) — over a
heap carrier with fractional permissions. This Lean bundle models ONLY the
purely-functional shared-construction core the fix delegates to: a component
built from an optional handler, pinned by the SAME three P/S/A facts. The
store-selection functionality (N/R/Q) is subclass-specific configuration that
this bundle's SPEC SURFACE does not model, so every nagini case attached to it
has no counterpart here (spec narrowing — see ``assessment``). Chasing
case-count parity would mean fabricating rivals for behavior this bundle does
not model; the port instead covers the surface it DOES model.

Note on that narrowing (corrected in audit): the reason is the SPEC's scope, NOT
that the change leaves store selection alone. It does not: the change also
restructures the store/name/timeout selection in the subclass that accepts
explicit overrides, and the accompanying tests add assertions tying the selected
store to the selected name (plus two new constructor tests), all of which sit in
PASS_TO_PASS. Those facts are real and load-bearing for that instance; they are
simply OUTSIDE ``problem_spec_initComponent``, whose ``Component`` carries no
store or name field. Because a G-PBT case may only vary the impl region — adding
a ``Component`` field or a spec conjunct changes the spec view and is rejected
by ``variant_scope`` (measured: ``spec view differs (same_spec failed)`` for
both) — the N/R/Q rivals are INEXPRESSIBLE on this bundle, not inapplicable to
the underlying change. That distinction matters: it makes the unmodeled
store-selection surface a visible scope boundary of this bundle rather than a
claim that no such behavior exists.

DEFENDED SURFACE (one modeled behavior; three independent top-level clauses).
``problem_spec_initComponent handler result`` pins EXACTLY:

  * (P handler)   ``result.handler = handler`` — the component keeps exactly the
    handler it was given;
  * (S signal)    ``result.missingHandlerFlagged = handler.isNone`` — the
    "missing handler" notice is raised exactly when no handler was supplied;
  * (A async)     ``result.reportsAsync = handlerIsAsync handler`` — the instance
    reports as asynchronous exactly when its handler is asynchronous.

The BEHAVIOURAL DISCRIMINATOR (the fix): clause (A). Pre-fix, construction
skipped the asynchronous-capability check, so an instance built from an
asynchronous handler reported as ordinary regardless. ``weak-async-dropped``
below IS that pre-fix behavior; the F2P that keys on the asynchronous marker
would fail for a faithful patch that omits the check. Clause (S) is the other
F2P key (the deprecation-notice behavior). Clause (P) pins handler retention.

BINDER STRUCTURE. The spec predicate has ONE input binder: ``handler : Option
Handler``, which ranges over ``none``, ``some { isAsync := false }`` and
``some { isAsync := true }`` — the three points that separate the three clauses.
The reject witnesses probe ALL THREE of these distinct inputs (``pts=3``):
(A) is refuted at ``some { isAsync := true }``, (S) at whichever of ``none`` /
``some {isAsync:=false}`` the rival mishandles, and (P) at ``some {isAsync:=true}``.
No binder value is held fixed across the reject lane.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling holds every handler
    field with FULL permission and notes (its own docstring) that the
    ``Acc(...,1/2)`` frame-mutation class does not apply because the value params
    are immutable. On this referentially transparent carrier it is doubly
    vacuous: ``handler`` is an immutable value, there is no ``mut`` input binder,
    no aliasing, no read-only cell to overwrite. No substitute probe is
    fabricated (porting map: vacuous here).

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The nagini oracle ``producer_is_async`` is
    ``@ContractOnly`` but GROUNDED in the argument; here the analogous predicate
    ``handlerIsAsync`` is a TRANSPARENT deep model (``some h => h.isAsync | none
    => false``), so there is no opaque answer key an implementation could echo —
    producing each field from the actual ``handler`` IS the work. The honest
    stand-in is the cheapest-correct positive control (``pos-cheapest-grounded``).

  * DIVERGENCE / NON-TERMINATION — VACUOUS on lean. ``implementation_initComponent``
    is a total Lean ``def``; a diverging implementation cannot be written at all,
    so this class is genuinely empty here (not a spec hole — contrast velvet's
    ``partial`` semantics, ``the corpus-wide termination-semantics finding``).

  * PARTIAL-DOMAIN / VALUE — APPLIES. Every ported nagini rival is a
    partial-domain attack correct on part of the ``handler`` domain but diverging
    where its clause bites: drop the async check (correct on sync/None, wrong on
    async); always/never signal absence (correct on one branch of ``isNone``,
    wrong on the other); fail to retain the handler.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``⟨rfl, rfl, rfl⟩`` / ``by_cases`` proof
is tuned to the frozen form — so a rejection alone attributes nothing to the
spec. Every ``expect="reject"`` case therefore carries a Lean snippet that states
the spec predicate directly at ONE concrete ground ``handler`` and closes ``¬
problem_spec_initComponent handler (implementation_initComponent handler)`` by
``decide`` (the ``Id.run do`` body and the ``Option.isNone`` / ``handlerIsAsync``
matches all reduce on ground literals). Each witness binds NOTHING in its head
(the input is a ground literal), so there are no hypotheses whose consistency
could be in question. Each was checked with two real ``lake env lean`` builds to
HOLD of its rival and to FAIL on the frozen solution, so it discriminates rather
than asserting a tautology.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart is a
constructor that mishandles one of the three facts, so the F2P behavior it keys
on (the asynchronous marker, or the deprecation notice, or handler retention for
the downstream chain) diverges from what the tests assert — so the faithful patch
would NOT resolve.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the two effects are modeled deeply as ``Option.isNone`` /
``handlerIsAsync``); the axiom lane belongs to G-AX, and the nagini
``AXIOM_TESTS`` are dropped.

INDEPENDENT AUDIT RECORD (all exit codes from real ``lake env lean`` builds).

  * Statement integrity: every case's ``theorem correct_initComponent`` STATEMENT
    was extracted and compared to the frozen one — byte-identical for all cases,
    and each case's whole-file diff against ``Solution.lean`` touches only the
    impl region (plus, for the two positives that re-prove and the two
    ``have``-prepending positives, the proof region).
  * Witnesses re-derived independently, 2 builds each: all four rivals build
    their witness (exit 0) and all four FAIL on the frozen solution (exit 1) with
    ``Tactic `decide` proved that the proposition ... is false`` — a SEMANTIC
    refutation in every case, never a missing identifier, type error or timeout.
    No witness binds anything, so ``consistency_probe`` is ``None`` by
    construction (nothing to be inconsistent).
  * Clause attribution machine-checked, 12 further builds: for each reject case,
    the three clauses were stated separately at that case's witness point. In
    every case exactly the clause its ``rationale`` names fails (exit 1, again
    ``decide ... is false``) and the other two HOLD (exit 0). So each rival is
    wrong for the stated reason and only that reason — the rejections are not
    over-attributed.
  * Attack D (SPEC-TOO-WEAK probes), five NEW wrong impls not in this battery:
    over-report async for any supplied handler; the signal and async fields
    crossed; the signal negated via ``isSome``; the absent handler reporting
    async. All four were REJECTED (exit 1) and each was independently refuted by
    a witness at its own point (exit 0 against the rival). A fifth probe rebuilt
    the handler from its observed bit (``some h => some { isAsync := h.isAsync }``)
    — that one VERIFIES (exit 0), correctly: it is definitionally equal to the
    frozen impl by structure eta, so it is a correct reshape and not a hole. Its
    witness accordingly fails against it (exit 1), which is the signature of an
    observably-identical impl rather than a wrong one.
  * Attack E (SPEC-TOO-STRONG probes), five NEW correct reshapes: a branchwise
    whole-function ``match``; ``!isSome`` for the signal with the async match
    inlined; an early ``return`` on the absent handler; ``decide (stored = none)``
    with ``handlerIsAsync stored && stored.isSome``; and a record-update
    (``{ base with ... }``) shape. ALL FIVE were proven (exit 0). The last two are
    not defeq to the spec tuple (``b && true = b`` and ``decide (· = none)`` need
    real rewriting, so ``⟨rfl,rfl,rfl⟩`` genuinely does not close them) and each
    needed one honest extra step — ``by_cases`` plus ``simp_all [handlerIsAsync,
    Id.run]``. So the spec is not merely accepting syntactic clones of the frozen
    body: it admits faithful reshapes whose proofs differ. No soundness hole.
  * No hole was found in the FROZEN spec, and the reason is stronger than "we
    tried and failed": see ``pos-spec-determinate``, which PROVES the spec admits
    at most one ``Component`` per input. Every attack-D probe that was rejected
    had to be, and every attack-E reshape that verified had to.
"""
from pathlib import Path

INSTANCE = "django__django-13344"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# region anchors (each unique inside Solution.lean; verified at load)
# ---------------------------------------------------------------------------

# The WHOLE impl body (everything strictly inside `-- impl-start`/`-- impl-end`,
# after the `Id.run do` header). Swapping it lands entirely inside the impl
# region, so the spec view and the theorem STATEMENT are untouched.
_IMPL_BODY = (
    '  -- raise the "missing handler" notice when no handler is supplied\n'
    "  let mut missingFlag := false\n"
    "  if handler.isNone then\n"
    "    missingFlag := true\n"
    "  -- keep the handler the component was built from\n"
    "  let stored := handler\n"
    "  -- asynchronous-capability check: report async exactly when the handler is async\n"
    "  let mut async := false\n"
    "  if handlerIsAsync stored then\n"
    "    async := true\n"
    "  return { handler := stored, missingHandlerFlagged := missingFlag, reportsAsync := async }"
)

# The frozen proof's intro line (proof region) — unique in the file — so the
# admissibility positive can prepend ground `have`s without touching the theorem
# STATEMENT or the spec view.
_P_INTRO = "  intro handler\n"


def _impl(new_body: str) -> str:
    """Replace ONLY the impl body of implementation_initComponent."""
    return _swap(_BASE, _IMPL_BODY, new_body)


# ---------------------------------------------------------------------------
# witness scaffold. States the spec predicate directly at one ground `handler`
# and refutes it by `decide` (the `Id.run do` body reduces on the literal).
# ---------------------------------------------------------------------------
def _w(handler_lit: str) -> str:
    return (
        f"example : ¬ problem_spec_initComponent {handler_lit}\n"
        f"    (implementation_initComponent {handler_lit}) := by\n"
        "  unfold problem_spec_initComponent implementation_initComponent\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_initComponent` statement byte-identical.
    # =====================================================================
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reordered/temp-reshaped CORRECT impl: store the handler FIRST, set the
        # signal via a mutable default-false then override on isNone, and bind the
        # async flag through a `let` before the record. Same values, different
        # control-flow shape. All three facts are direct field equalities (no
        # fold), so the proof collapses to `⟨rfl, rfl, rfl⟩` on both `Option`
        # cases. Statement byte-identical; no new axiom/lemma. (Verified: real
        # build.) Ports nagini's pos-control-reorder.
        "module": _swap(
            _impl(
                "  let stored := handler\n"
                "  let mut missingFlag := false\n"
                "  if handler.isNone then\n"
                "    missingFlag := true\n"
                "  let isAsyncFlag := handlerIsAsync stored\n"
                "  return { handler := stored, missingHandlerFlagged := missingFlag, "
                "reportsAsync := isAsyncFlag }"
            ),
            "  cases handler with\n"
            "  | none => exact ⟨rfl, rfl, rfl⟩\n"
            "  | some h =>\n"
            "    by_cases hb : h.isAsync <;>\n"
            "      simp only [handlerIsAsync, hb, Id.run, if_true] <;>\n"
            "      exact ⟨rfl, rfl, rfl⟩",
            "  cases handler with\n"
            "  | none => exact ⟨rfl, rfl, rfl⟩\n"
            "  | some h => exact ⟨rfl, rfl, rfl⟩",
        ),
        "rationale": "correct but reordered/temp-reshaped impl must verify (P/S/A "
                     "are direct field equalities, no fold lemma needed); else "
                     "SPEC-TOO-STRONG. Re-proved for the reshaped body (both "
                     "`Option` cases close by `⟨rfl,rfl,rfl⟩`); statement "
                     "byte-identical, no new axiom/lemma. Ports nagini's "
                     "pos-control-reorder.",
    },
    {
        "id": "pos-cheapest-grounded",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest HONEST positive control: assign each field its grounded
        # value in one pass with no mutable state — the signal from `isNone`, the
        # async report from `handlerIsAsync` directly. Since the async predicate is
        # a transparent deep model grounded in the input (not an opaque answer
        # key), the cheapest correct impl echoes it directly, which IS the work.
        # Proof collapses to `⟨rfl,rfl,rfl⟩`. (Verified: real build.) Stands in for
        # nagini's pos-cheapest-grounded (there over the grounded oracle).
        "module": _swap(
            _impl(
                "  return { handler := handler, "
                "missingHandlerFlagged := handler.isNone, "
                "reportsAsync := handlerIsAsync handler }"
            ),
            "  cases handler with\n"
            "  | none => exact ⟨rfl, rfl, rfl⟩\n"
            "  | some h =>\n"
            "    by_cases hb : h.isAsync <;>\n"
            "      simp only [handlerIsAsync, hb, Id.run, if_true] <;>\n"
            "      exact ⟨rfl, rfl, rfl⟩",
            "  exact ⟨rfl, rfl, rfl⟩",
        ),
        "rationale": "cheapest correct impl: assigns each field its grounded value "
                     "in one pass (signal from `isNone`, async from `handlerIsAsync` "
                     "directly). The async predicate is a transparent grounded deep "
                     "model, not an opaque oracle => no wrong echo; this is the "
                     "honest positive control. Re-proved by `⟨rfl,rfl,rfl⟩` (the "
                     "record already IS the spec's field tuple); statement "
                     "byte-identical, no new axiom/lemma. Ports nagini's "
                     "pos-cheapest-grounded.",
    },
    {
        "id": "pos-spec-determinate",
        "kind": "soundness",
        "expect": "verify",
        # ADDED IN AUDIT. The four reject rivals below show that four particular
        # wrong impls are refuted. This case shows something strictly stronger,
        # and it is the reason SPEC-TOO-WEAK is unreachable here rather than
        # merely unobserved: the spec is FUNCTIONAL — it admits AT MOST ONE
        # `Component` per input. `problem_spec_initComponent handler r` fixes all
        # three of `r`'s fields by equations against `handler`, and `Component`
        # has exactly those three fields, so any two satisfying results are
        # equal. Consequence: for every input the set of spec-satisfying results
        # is a singleton, which is exactly the frozen impl's output (the frozen
        # theorem supplies existence). So NO impl differing observably from the
        # frozen one at ANY input can satisfy this spec — no tuned wrong impl
        # exists to be found, and directive 5's frame obligation is discharged
        # with no field left free. Proved as a ground `have` prepended to the
        # frozen tactic body, which then closes verbatim: nothing is assumed, no
        # new top-level declaration, statement byte-identical. Verified: real
        # build (exit 0). No nagini counterpart — the heap carrier there cannot
        # state result determinacy this cheaply.
        "module": _swap(
            _BASE, _P_INTRO,
            "  have _det : ∀ (hd : Option Handler) (r1 r2 : Component),\n"
            "      problem_spec_initComponent hd r1 → problem_spec_initComponent hd r2 → r1 = r2 := by\n"
            "    intro hd r1 r2 ⟨a1, a2, a3⟩ ⟨b1, b2, b3⟩\n"
            "    cases r1\n"
            "    cases r2\n"
            "    simp_all\n"
            + _P_INTRO),
        "rationale": "the spec is FUNCTIONAL: it admits at most one `Component` "
                     "per input (all three fields of the three-field record are "
                     "pinned by equations against `handler`), so the "
                     "spec-satisfying result set is a singleton and, with the "
                     "frozen theorem's existence half, that singleton IS the "
                     "frozen impl's output. Hence no observably-different impl "
                     "can verify: SPEC-TOO-WEAK is structurally unreachable, not "
                     "just unobserved by the four rivals below, and no output "
                     "field is left free (directive 5). Must verify; a failure "
                     "would mean the spec leaves some field underdetermined.",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at
    # normal, F2P-shaped inputs. The frozen theorem carries NO precondition (the
    # spec is total over `Option Handler`), so the nagini precondition-admission
    # self-call re-expresses as: discharge the spec predicate by evaluation at the
    # two F2P-shaped inputs (a supplied async handler, and the absent handler) as
    # ground `have`s prepended to the frozen tactic body, then close the frozen
    # obligation verbatim. Nothing is assumed: no new declaration, statement
    # byte-identical, ground instances are `have`s in the existing tactic body.
    # (Verified: real build.)
    # =====================================================================
    {
        "id": "admiss-f2p-inputs",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            "  have _async : problem_spec_initComponent (some { isAsync := true })\n"
            "      (implementation_initComponent (some { isAsync := true })) := by\n"
            "    unfold problem_spec_initComponent implementation_initComponent\n"
            "    exact ⟨rfl, rfl, rfl⟩\n"
            "  have _none : problem_spec_initComponent none\n"
            "      (implementation_initComponent none) := by\n"
            "    unfold problem_spec_initComponent implementation_initComponent\n"
            "    exact ⟨rfl, rfl, rfl⟩\n"
            + _P_INTRO),
        "rationale": "the obligation is discharged at the two F2P-shaped inputs (a "
                     "supplied asynchronous handler, and the absent handler — the "
                     "inputs the async-marker and deprecation-notice F2P tests key "
                     "on) by evaluation as ground `have`s, then the frozen "
                     "obligation is closed verbatim. Verifies (else the modeled "
                     "behavior would be unsatisfiable at exactly a normal F2P input "
                     "— the analogue of PRECOND-TOO-STRONG). Nothing is assumed: no "
                     "new declaration, statement byte-identical, ground instances "
                     "are `have`s in the existing tactic body. Ports nagini's "
                     "admiss-self-call (which constructed a fresh handler and "
                     "called the modeled function on an F2P-shaped supplied/None "
                     "producer).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a witness pinning the
    # violation at one concrete input.
    # =====================================================================

    # ---- THE bug-delta: drop the asynchronous-capability check (attacks A) ----
    {
        "id": "weak-async-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior: never run the async check — hardcode reportsAsync =
        # false. Correct on every sync/absent handler, WRONG on an async handler.
        "module": _impl(
            '  -- raise the "missing handler" notice when no handler is supplied\n'
            "  let mut missingFlag := false\n"
            "  if handler.isNone then\n"
            "    missingFlag := true\n"
            "  let stored := handler\n"
            "  return { handler := stored, missingHandlerFlagged := missingFlag, "
            "reportsAsync := false }"
        ),
        "refinement": "this IS the pre-fix omission of the asynchronous-capability "
                      "check: the async marker is never set, so an instance built "
                      "from an asynchronous handler reports as ordinary. The F2P "
                      "that asserts the instance reports asynchronous for an "
                      "asynchronous handler would FAIL, so the faithful real patch "
                      "does NOT resolve.",
        "rationale": "REJECT from clause (A): the spec pins "
                     "`reportsAsync = handlerIsAsync handler`, but the rival emits "
                     "`false`, differing whenever the handler is asynchronous. "
                     "Refuted at handler = some { isAsync := true }.",
        "witness": _w("(some { isAsync := true })"),
    },

    # ---- always signal absence, regardless of handler (attacks S) ----
    {
        "id": "weak-signal-always",
        "kind": "uniqueness",
        "expect": "reject",
        # Always raise the "missing handler" notice. Correct only on the absent
        # handler; WRONG for any supplied handler.
        "module": _impl(
            "  let mut missingFlag := true\n"
            "  let stored := handler\n"
            "  let mut async := false\n"
            "  if handlerIsAsync stored then\n"
            "    async := true\n"
            "  return { handler := stored, missingHandlerFlagged := missingFlag, "
            "reportsAsync := async }"
        ),
        "refinement": "this fires the deprecation notice even when a handler IS "
                      "supplied. The F2P that asserts the notice is raised ONLY "
                      "when no handler is supplied (and not otherwise) would FAIL "
                      "on the supplied-handler path, so the faithful real patch "
                      "warns spuriously and does NOT resolve.",
        "rationale": "REJECT from clause (S): the spec pins "
                     "`missingHandlerFlagged = handler.isNone`, but the rival emits "
                     "`true` unconditionally, differing whenever a handler is "
                     "supplied. Refuted at handler = some { isAsync := false } (a "
                     "supplied, non-async handler — a distinct input from the "
                     "async-clause witness).",
        "witness": _w("(some { isAsync := false })"),
    },

    # ---- never signal absence (attacks S on the other branch) ----
    {
        "id": "weak-signal-never",
        "kind": "uniqueness",
        "expect": "reject",
        # Never raise the notice. Correct on every supplied handler; WRONG when the
        # handler is absent. This is the DUAL of weak-signal-always: it exercises
        # the OTHER branch of `isNone`, so the (S) clause is attacked at both of its
        # boundary inputs and no rival lets the None-signal path go unprobed.
        "module": _impl(
            "  let mut missingFlag := false\n"
            "  let stored := handler\n"
            "  let mut async := false\n"
            "  if handlerIsAsync stored then\n"
            "    async := true\n"
            "  return { handler := stored, missingHandlerFlagged := missingFlag, "
            "reportsAsync := async }"
        ),
        "refinement": "this SUPPRESSES the deprecation notice even when no handler "
                      "is supplied. The F2P that asserts the notice is raised when "
                      "the handler is absent would FAIL, so the faithful real patch "
                      "silently drops the required notice and does NOT resolve.",
        "rationale": "REJECT from clause (S): the spec pins "
                     "`missingHandlerFlagged = handler.isNone`, but the rival emits "
                     "`false` unconditionally, differing when the handler is absent. "
                     "Refuted at handler = none — the boundary the always-signal "
                     "rival does not exercise, so the two (S) rivals jointly pin "
                     "both branches of `isNone`.",
        "witness": _w("none"),
    },

    # ---- fail to retain the handler (attacks P) ----
    {
        "id": "weak-handler-not-retained",
        "kind": "uniqueness",
        "expect": "reject",
        # Store `none` instead of the supplied handler. The signal/async facts are
        # still computed from the real `handler`, so a value-proxy checking only
        # signal/async would miss it — but (P) pins retention, so it must reject.
        "module": _impl(
            '  -- raise the "missing handler" notice when no handler is supplied\n'
            "  let mut missingFlag := false\n"
            "  if handler.isNone then\n"
            "    missingFlag := true\n"
            "  let mut async := false\n"
            "  if handlerIsAsync handler then\n"
            "    async := true\n"
            "  return { handler := none, missingHandlerFlagged := missingFlag, "
            "reportsAsync := async }"
        ),
        "refinement": "this drops handler retention (keeps none instead of the "
                      "supplied handler) while still computing the signal and async "
                      "facts from the real handler. Downstream the component would "
                      "invoke the absent handler instead of the real one, so the "
                      "request-processing chain breaks and the constructor/chaining "
                      "behavior diverges — the faithful real patch does NOT resolve.",
        "rationale": "REJECT from clause (P): the spec pins "
                     "`result.handler = handler`, but the rival stores `none`, "
                     "differing whenever a handler is supplied. Refuted at "
                     "handler = some { isAsync := true } (a supplied handler; the "
                     "signal/async facts are computed correctly here, so ONLY the "
                     "(P) clause discriminates).",
        "witness": _w("(some { isAsync := true })"),
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 6 uniqueness rivals: 3 against configure_handler's
# P/S/A facts and 3 against configure_settings_handler's N/R/Q store-selection
# facts) plus an EMPTY-in-effect AXIOM lane. This bundle models ONLY the shared
# purely-functional construction core (P/S/A) and re-expresses every sibling case
# attached to it; the store-selection cases (N/R/Q) have no counterpart because
# that behavior is outside this bundle's frozen spec surface and a rival for it is
# INEXPRESSIBLE under impl-only surgery (see the DROPPED note below — the earlier
# "the fix does not touch it" justification was false and is retracted). It ADDS
# one rival (weak-signal-never) to attack clause (S) at its OTHER boundary,
# satisfying this backend's per-branch coverage, and one positive
# (pos-spec-determinate, added in audit) proving the spec is functional. Every
# sibling case is recorded below.
#
#   sibling case                 -> here
#   -----------------------------------------------------------------------
#   pos-control-reorder          -> pos-control-reorder        PORTED (re-proved)
#   pos-cheapest-grounded        -> pos-cheapest-grounded      RE-EXPRESSED
#   admiss-self-call             -> admiss-f2p-inputs          RE-EXPRESSED
#   weak-async-dropped           -> weak-async-dropped         PORTED  (attacks A)
#   weak-signal-always           -> weak-signal-always         PORTED  (attacks S)
#   weak-producer-not-retained   -> weak-handler-not-retained  PORTED  (attacks P)
#   (none)                       -> weak-signal-never          ADDED   (attacks S)
#   (none)                       -> pos-spec-determinate       ADDED   (audit; spec functional)
#   weak-override-ignored        -> (none)                     DROPPED (N inexpressible)
#   weak-store-stale             -> (none)                     DROPPED (R inexpressible)
#   weak-result-stale            -> (none)                     DROPPED (Q inexpressible)
#   AXIOM_TESTS                  -> (none)                     DROPPED (G-AX)
#
# DROPPED (weak-override-ignored, weak-store-stale, weak-result-stale): these
#   three nagini rivals attack the store-selection invariant (N: store_name
#   selection; R: store == resolve_store(store_name); Q: Result() == store) of
#   configure_settings_handler.
#   CORRECTED IN AUDIT. An earlier version of this note justified the drop by
#   asserting the change "does NOT touch" store selection. That is FALSE and is
#   retracted: the change also restructures name/store/timeout selection in the
#   subclass that accepts explicit overrides, and the accompanying tests add
#   store-vs-name assertions plus two new constructor tests, all in PASS_TO_PASS.
#   The N/R/Q facts are therefore real and load-bearing for the instance.
#   The ACTUAL, verified reason these three cases have no counterpart is
#   INEXPRESSIBILITY on this bundle's frozen spec surface, which is narrower than
#   the change: `problem_spec_initComponent` relates a `Component` carrying only
#   handler / notice / async-report — there is no store or name field, hence no
#   N/R/Q obligation for a rival to violate. A G-PBT case may vary ONLY the impl
#   region, so landing such a rival would require adding a `Component` field or a
#   spec conjunct; both were tried and both are rejected by variant_scope with
#   `spec view differs (same_spec failed)`. Writing an impl-only rival that
#   mis-selects a store it cannot store is impossible, and a rival that merely
#   reshapes the three modeled fields would be a duplicate of the four already
#   here. So: inexpressible on this carrier, and recorded as a SCOPE BOUNDARY of
#   this bundle (the store-selection surface is unmodeled and hence undefended
#   here) rather than as a claim that the behavior is untouched by the change.
# RE-EXPRESSED (pos-cheapest-grounded): the sibling's cheapest positive echoes the
#   grounded oracle `producer_is_async(producer)` and the up-front name selection.
#   This carrier's async predicate `handlerIsAsync` is a TRANSPARENT deep model
#   grounded in the input, so the analogous cheapest impl assigns each field its
#   grounded value in one pass with no mutable state; the record already IS the
#   spec's field tuple, so the proof collapses to `⟨rfl,rfl,rfl⟩`.
# RE-EXPRESSED (admiss-f2p-inputs): the sibling constructs a fresh handler and
#   self-calls the modeled function on an F2P-shaped supplied producer / None to
#   confirm the precondition admits a normal input. This bundle's spec is TOTAL
#   (no precondition), so the honest analogue discharges the postcondition at the
#   two F2P-shaped inputs (a supplied async handler, the absent handler) as ground
#   `have`s, then closes the frozen obligation verbatim — proving the modeled
#   behavior is satisfiable at exactly the normal inputs the F2P tests key on.
# ADDED (weak-signal-never): the sibling's clause-(S) rival (weak-signal-always)
#   only exercises one branch of the None-signal (always warn). This backend's
#   coverage tool requires the (S) clause's binder to be varied; the dual rival
#   (never warn) refutes at handler = none, so the two (S) rivals jointly pin both
#   branches of `handler.isNone`. It attacks the SAME modeled clause, not an
#   unmodeled behavior.
# VACUOUS (frame/permission mutation): the sibling notes its inputs are held with
#   full permission so its Acc(...,1/2) frame-mutation class does not apply; on
#   this referentially transparent carrier it is doubly vacuous — no `mut` input,
#   no aliasing, no read-only cell. No substitute probe is fabricated.
# VACUOUS (divergence): on lean `implementation_initComponent` is a total `def`;
#   a diverging impl cannot be written, so the class is genuinely empty (contrast
#   velvet `partial` semantics — the corpus-wide termination-semantics finding).
#
# POINT SPREAD. The four reject witnesses probe the THREE distinct inputs the
# single binder `handler` can take that separate the three clauses (pts=3):
#   handler =
#     some { isAsync := true }   weak-async-dropped         A
#     some { isAsync := false }  weak-signal-always         S
#     none                       weak-signal-never          S
#     some { isAsync := true }   weak-handler-not-retained  P
#   Across them the binder takes all three distinguishing values (none, sync
#   handler, async handler), so no input value is pinned and each clause is
#   refuted at an input where ONLY that clause discriminates.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# opaque callee and consumes no axiom (both effects modeled deeply), so there is
# nothing to probe and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
