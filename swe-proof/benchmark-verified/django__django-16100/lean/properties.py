"""properties.py — G-PBT falsification battery for django__django-16100 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_changelistView``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND
the file elaborates with the obligation closed); ``expect:"reject"`` passes iff
(in scope AND it does NOT verify AND the case's refutation ``witness`` holds of
the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled behavior over an all-or-nothing state fold).
A bulk operation applies a front-to-back sequence of state-transitions
``steps : List (σ → Except E σ)`` to a starting state ``s0``; each transition
either advances the state or reports a failure. The observable outcome is
``result : σ × Option E`` and is pinned by a two-way case split on the fold
``applyAll s0 steps``:

  changelistView (s0, steps) : σ × Option E
    applyAll s0 steps = .ok sf   →  result = (sf, none)
    applyAll s0 steps = .error e →  result = (s0, some e)

i.e. if EVERY transition succeeds the final state is committed and no failure
is reported; if ANY transition fails the state is observed EXACTLY as it was
before the sequence began (``s0`` — no partial/committed prefix) and that first
failure is reported. Both clauses are grounded in the inputs: the result
equals a term built solely from ``s0`` and the fold over ``steps``, so there is
no answer key to echo.

CARRIER NOTE — this spec quantifies over abstract type variables ``σ`` and
``E`` and over an arbitrary list of transition FUNCTIONS. The individual
transition is opaque (a universally-quantified ``f``), so a rival that
mishandles one transition in isolation is not refutable at that level of
abstraction. What IS fully transparent — and what every rival below attacks —
is the COMBINATION: the traversal of the list, the short-circuit on the first
error, the all-or-nothing choice between ``s0`` and the folded final state, and
the ``Option E`` failure component. Each witness instantiates ``σ := Nat`` and
``E := Nat`` with concrete ``s0`` and concrete literal transitions, so the
whole outcome becomes ``decide``-able.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent:
    the inputs carry no heap permission, there is no read-only half-permission
    to overwrite and no aliasing to exploit. The nagini ``frame-mutate-original``
    rival (write to a read-only input, then commit) has no expressible instance
    here and no substitute is fabricated for it.

  * ADMISSIBILITY — the nagini precondition-admission probe becomes a
    satisfiability control: the frozen theorem carries NO precondition
    hypothesis (the modeled behavior is total, ``∀`` unguarded), so there is no
    binder to attack; the honest analogue discharges the spec predicate at the
    F2P-shaped two-transition input (first succeeds, second fails ⇒ full revert)
    by evaluation, inside the proof region, alongside the frozen obligation.

  * PARTIAL-DOMAIN / VALUE — the nagini F2P discriminators port to rivals that
    break the all-or-nothing COMBINATION: keep the partially-advanced state on a
    failure instead of reverting to ``s0`` (the committed-prefix / pre-patch
    bug), swallow the failure so it is never reported, or discard the folded
    result on the all-success path. Each attacks a DIFFERENT transparent clause.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen tactic script is tuned to the frozen
form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS the spec at one concrete input, stated directly against
``problem_spec_changelistView`` at ``σ := Nat`` / ``E := Nat`` literals. The
inputs are spread so the reject witnesses vary BOTH spec binders — ``s0`` and
``steps`` (length, contents, whether the terminal transition errors) — and each
top-level clause of the postcondition is attacked:

  * keep-state-on-fail   is refuted on a two-transition batch whose SECOND
    transition fails (``s0=0``, ``[+1, error]``): the error clause pins the
    state to ``s0=0`` while the rival commits the partially-advanced ``1``.
  * swallow-failure       is refuted on a single failing transition
    (``s0=0``, ``[error]``): the error clause requires ``some e`` while the
    rival reports ``none``.
  * discard-final-state   is refuted on an all-SUCCESS single transition
    (``s0=3``, ``[+1]``): the ok clause pins the state to the folded ``4``
    while the rival returns the untouched ``s0=3``.

No two rivals share a refutation point: keep-state and swallow attack the error
(``.error``) clause but at different batch shapes (a mid-batch failure with a
committed prefix vs. an immediate failure), and discard-final attacks the
opposite (``.ok``) clause on an all-success batch.

AXIOM lane: EMPTY. meta.json axioms == [] and the deep-model reference is the
rollback semantics itself; the modeled behavior is a total computation over the
inputs, so there is no axiom-soundness / axiom-containment obligation to probe
here (that lane belongs to G-AX in any case). See the ``assessment`` in the
submitted payload for the nagini cases ported / omitted and why.
"""
from pathlib import Path

INSTANCE = "django__django-16100"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl loop body (strictly between the impl markers). Every impl
# replacement lands entirely inside the impl region.
_I_IMPL = (
    "  let mut s := s0\n"
    "  for f in steps do\n"
    "    match f s with\n"
    "    | .ok s'   => s := s'\n"
    "    | .error e => return (s0, some e)\n"
    "  return (s, none)\n"
    "-- impl-end"
)

# The nested `key` loop inside the frozen proof, whose match-arm order must
# track the impl's arm order (so a branch-reordered positive re-proves cleanly).
_P_KEY = (
    "      (Id.run do\n"
    "        let mut s := acc\n"
    "        for f in steps do\n"
    "          match f s with\n"
    "          | .ok s'   => s := s'\n"
    "          | .error e => return (s0, some e)\n"
    "        return (s, none)) = loopRec s0 acc steps := by"
)

# The head of the frozen proof body, an anchor entirely inside the proof region
# used to prepend an admissibility ground instance.
_P_HEAD = (
    "  unfold problem_spec_changelistView\n"
    "  rw [impl_eq_loopRec, loopRec_eq_closed]"
)

# Shared witness tactic: instantiate the abstract carrier at Nat/Nat, unfold the
# spec + impl + fold, reduce the `Id.run`/`foldl` machinery, then `decide` the
# concrete (in)equality. `decide` is total on these Nat literals; no opaque term
# survives once σ and E are Nat and the transitions are literal.
_W_TAC = (
    "  unfold problem_spec_changelistView implementation_changelistView applyAll\n"
    "  simp only [List.foldl_cons, List.foldl_nil, Except.bind, Id.run]\n"
    "  decide"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally-different but CORRECT impl
    # that MUST verify. If a faithful correct implementation cannot satisfy the
    # frozen obligation the spec is SPEC-TOO-STRONG. Keeps the
    # `theorem correct_changelistView` statement byte-identical; because the arm
    # order of the loop's `match` changed, the frozen proof's nested `key` loop
    # is re-shaped to the SAME new arm order (no new lemma, no assumption).
    # =====================================================================
    {
        "id": "pos-match-arm-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Swap the two `match` arms (test `.error` first, `.ok` second). Same
        # transition-by-transition behavior, same short-circuit, same committed
        # value in each arm — observationally identical to the frozen impl. The
        # frozen proof's `key` helper pattern-matches in the frozen arm order, so
        # the nested loop is reordered to match; every proof step downstream is
        # unchanged.
        "module": _swap(
            _swap(
                _BASE, _I_IMPL,
                "  let mut s := s0\n"
                "  for f in steps do\n"
                "    match f s with\n"
                "    | .error e => return (s0, some e)\n"
                "    | .ok s'   => s := s'\n"
                "  return (s, none)\n"
                "-- impl-end",
            ),
            _P_KEY,
            "      (Id.run do\n"
            "        let mut s := acc\n"
            "        for f in steps do\n"
            "          match f s with\n"
            "          | .error e => return (s0, some e)\n"
            "          | .ok s'   => s := s'\n"
            "        return (s, none)) = loopRec s0 acc steps := by",
        ),
        "rationale": "reordering the two `match` arms preserves the exact "
                     "short-circuit decision and the value committed in each arm, "
                     "so both clauses of the postcondition still hold; it must "
                     "verify (else SPEC-TOO-STRONG). Re-proved because the frozen "
                     "proof's nested loop pattern-matches in the original arm "
                     "order: the nested loop is reordered to the same new order, "
                     "with no new declaration and the theorem statement "
                     "byte-identical.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at a normal, F2P-shaped input rather than only
    # provable in the abstract. The frozen theorem carries NO precondition
    # hypothesis (the modeled behavior is total, so `∀` is unguarded), so the
    # nagini precondition-admission probe has no binder to attack; the honest
    # analogue discharges the spec predicate at the F2P shape (a two-transition
    # batch whose first transition succeeds and whose second fails, so the state
    # fully reverts to s0) by evaluation, inside the proof region, alongside the
    # frozen obligation.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-batch",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_HEAD,
            "  have _ground : problem_spec_changelistView (E := Nat)\n"
            "      (0 : Nat) [fun s => Except.ok (s+1), fun _ => Except.error 7]\n"
            "      (implementation_changelistView (0 : Nat)\n"
            "        [fun s => Except.ok (s+1), fun _ => Except.error 7]) := by\n"
            "    unfold problem_spec_changelistView implementation_changelistView applyAll\n"
            "    simp only [List.foldl_cons, List.foldl_nil, Except.bind, Id.run]\n"
            "    decide\n"
            + _P_HEAD,
        ),
        "rationale": "the obligation is discharged at a ground F2P-shaped batch "
                     "(a two-transition sequence whose first transition succeeds "
                     "and whose second fails, so the observable state reverts to "
                     "s0 with the failure reported) by `decide`, then the frozen "
                     "obligation is closed verbatim. Verifies (else the spec is "
                     "unsatisfiable at the normal input, the analogue of "
                     "PRECOND-TOO-STRONG). Nothing is assumed: no new declaration, "
                     "the theorem statement is byte-identical, and the ground "
                     "instance is a `have` inside the existing tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break, and
    # (b) a refutation witness pinning the violation at one concrete input,
    # checked to hold of the rival and FAIL on gold.
    # =====================================================================
    {
        "id": "weak-keep-state-on-fail",
        "kind": "uniqueness",
        "expect": "reject",
        # On a failing transition, report the failure but commit the
        # PARTIALLY-ADVANCED state `s` instead of reverting to `s0`. This is the
        # committed-prefix / pre-patch behavior: earlier successful transitions
        # persist even though a later one fails.
        "module": _swap(
            _BASE, _I_IMPL,
            "  let mut s := s0\n"
            "  for f in steps do\n"
            "    match f s with\n"
            "    | .ok s'   => s := s'\n"
            "    | .error e => return (s, some e)\n"
            "  return (s, none)\n"
            "-- impl-end",
        ),
        "refinement": "committing the partially-advanced state on a failure is "
                      "exactly the pre-existing behavior the issue reports: the "
                      "writes performed before the failing operation persist. On "
                      "the F2P scenario where an earlier operation succeeds and a "
                      "later one raises, this leaves the store carrying the "
                      "earlier operation's replacement rather than the original "
                      "value, so the atomic all-or-nothing guarantee is not "
                      "restored and the F2P is not resolved.",
        "rationale": "REJECT from the error clause `applyAll = .error e → result "
                     "= (s0, some e)`: on a batch whose second transition fails "
                     "the spec pins the state to s0 (full revert) while the rival "
                     "returns the advanced state. Refuted at s0=0, steps=[+1, "
                     "error] — a MID-batch failure with a committed prefix, "
                     "distinct from the immediate failure the swallow rival uses.",
        "witness": (
            "-- Batch [+1, error] from s0=0: the first transition advances 0→1,\n"
            "-- the second fails. The error clause pins the observable state to\n"
            "-- s0=0; committing the advanced state gives 1.\n"
            "example : ¬ problem_spec_changelistView (E := Nat)\n"
            "    (0 : Nat) [fun s => Except.ok (s+1), fun _ => Except.error 7]\n"
            "    (implementation_changelistView (0 : Nat)\n"
            "      [fun s => Except.ok (s+1), fun _ => Except.error 7]) := by\n"
            + _W_TAC + "\n"
        ),
    },
    {
        "id": "weak-swallow-failure",
        "kind": "uniqueness",
        "expect": "reject",
        # On a failing transition, revert the state (keep s0) but DO NOT report
        # the failure: continue as if it succeeded, ending with `none`. The
        # failure is silently swallowed instead of propagated.
        "module": _swap(
            _BASE, _I_IMPL,
            "  let mut s := s0\n"
            "  for f in steps do\n"
            "    match f s with\n"
            "    | .ok s'   => s := s'\n"
            "    | .error _ => s := s0\n"
            "  return (s, none)\n"
            "-- impl-end",
        ),
        "refinement": "swallowing the failure (never reporting it) corresponds to "
                      "a change that catches the exception and proceeds silently. "
                      "The F2P asserts that the failing scenario RAISES out of the "
                      "view; a patch that suppresses the failure would not "
                      "propagate it and the F2P's expected exception never "
                      "surfaces, so it is not resolved.",
        "rationale": "REJECT from the error clause `applyAll = .error e → result "
                     "= (s0, some e)`: the failure component must be `some e`, but "
                     "the rival reports `none`. Refuted at s0=0, steps=[error] — "
                     "an IMMEDIATE failure (the failure-reporting half of the "
                     "error clause), distinct from the committed-prefix shape the "
                     "keep-state rival uses.",
        "witness": (
            "-- Batch [error] from s0=0: the sole transition fails immediately.\n"
            "-- The error clause requires the failure be reported (some 7);\n"
            "-- swallowing it reports none.\n"
            "example : ¬ problem_spec_changelistView (E := Nat)\n"
            "    (0 : Nat) [fun _ => Except.error 7]\n"
            "    (implementation_changelistView (0 : Nat)\n"
            "      [fun _ => Except.error 7]) := by\n"
            + _W_TAC + "\n"
        ),
    },
    {
        "id": "weak-discard-final-state",
        "kind": "uniqueness",
        "expect": "reject",
        # On the all-success path, discard the folded final state and return the
        # UNTOUCHED s0. Correct on any failing batch (state reverts to s0 either
        # way), so a strict PARTIAL-DOMAIN attack on the ok clause only.
        "module": _swap(
            _BASE, _I_IMPL,
            "  let mut s := s0\n"
            "  for f in steps do\n"
            "    match f s with\n"
            "    | .ok s'   => s := s'\n"
            "    | .error e => return (s0, some e)\n"
            "  return (s0, none)\n"
            "-- impl-end",
        ),
        "refinement": "returning the pre-loop state on the all-success path "
                      "corresponds to a change that never persists the successful "
                      "writes — the opposite failure of the committed-prefix bug. "
                      "On the all-success F2P scenario the store would show the "
                      "original values rather than the replacements, so the "
                      "successful bulk edit is lost and the F2P is not resolved.",
        "rationale": "REJECT from the ok clause `applyAll = .ok sf → result = "
                     "(sf, none)`: on an all-success batch the spec pins the state "
                     "to the folded final state sf, but the rival returns the "
                     "untouched s0. Correct on every failing batch (both revert to "
                     "s0), so a strict PARTIAL-DOMAIN attack the two error-clause "
                     "rivals do not subsume. Refuted at s0=3, steps=[+1].",
        "witness": (
            "-- Batch [+1] from s0=3: the sole transition succeeds, advancing\n"
            "-- 3→4. The ok clause pins the state to the folded 4; returning the\n"
            "-- untouched s0 gives 3.\n"
            "example : ¬ problem_spec_changelistView (E := Nat)\n"
            "    (3 : Nat) [fun s => Except.ok (s+1)]\n"
            "    (implementation_changelistView (3 : Nat)\n"
            "      [fun s => Except.ok (s+1)]) := by\n"
            + _W_TAC + "\n"
        ),
    },
]
