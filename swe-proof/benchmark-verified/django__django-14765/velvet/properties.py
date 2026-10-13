"""properties.py — G-PBT falsification battery for django__django-14765 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both regions the consumer spec view elides — so ``markers.same_spec`` holds
and the ``prove_correct`` obligation survives with a byte-identical statement)
and swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method over the shape of an optional
set-typed argument a registry-style object normalizes at construction). The
argument's shape is the single input binder ``arg : SetArg``, a three-way
partition:

  * ``absent``        — no value supplied;
  * ``alreadySet xs`` — a value supplied that is ALREADY a set, members ``xs``;
  * ``coercible ys``  — a value supplied that is NOT a set (members ``ys``).

AUDIT NOTE (independent re-derivation of this port). Two defects were found and
repaired here; both were coverage gaps rather than hollow cases. (1) The port's
own coverage prose claimed the ``alreadySet`` payload was probed "above AND
below its length-0 degenerate point", but every ``alreadySet`` reject witness in
fact sat at a NON-EMPTY payload (``["A"]`` / ``["B","C"]``) — the empty-set
sub-domain was described and not demonstrated. ``alreadyset-empty-rejects`` now
attacks it at ``.alreadySet []`` (machine-checked: rival 0 / gold 1, and a
flipped-claim forgery gold 0 / rival 1). (2) The whole ``admissibility`` lane was
dropped as "vacuous because the method has no ``require``"; that reason is
wrong on a total carrier — the analogue is the obligation being unsatisfiable or
degenerate at an F2P-shaped input, which is directly testable and is now tested
by ``admiss-f2p-nondegenerate``. Attacks D and E were also run out-of-band: six
NEW wrong impls (coercible-keeps-members, reverse / dedup / dropLast members,
alreadySet-empty-rejects, absent-sentinel) were all REJECTED, and three NEW
correct reshapes (an ``if``-then-``match`` dispatch, an ``xs ++ []`` reshape, and
a nested-``let`` two-level dispatch) all VERIFIED — so no spec hole in either
direction was found on this carrier.

  normalizeSetArg (arg : SetArg)
      return (out : Except InitErr (List String))
    ensures out = normalizeSpec arg                                   -- (C-eq)
    ensures arg = .absent → out = Except.ok []                        -- (C-abs)
    ensures ∀ xs, arg = .alreadySet xs → out = Except.ok xs           -- (C-set)
    ensures ∀ ys, arg = .coercible ys → out = Except.error .rejected  -- (C-rej)

``normalizeSpec`` is a fully-unfolded ``def`` in the ``pure`` region (a direct
three-arm dispatch: absent→empty, already-a-set→kept-as-is, not-a-set→rejected)
— there is NO opaque answer key to echo; pinning ``out = normalizeSpec arg`` IS
the work. The load-bearing behaviour: an absent argument becomes the empty
collection, an argument that is already a set is stored with its members
preserved EXACTLY, and an argument that is not already a set is REJECTED rather
than silently coerced into one.

BINDER STRUCTURE (read before judging binder coverage). The postcondition
depends on EXACTLY ONE input, ``arg`` — but ``arg`` is a rich sum whose three
constructor arms each carry distinct behaviour, and two arms carry a payload
(``xs`` / ``ys``) that the accepting clause pins element-wise. So "vary the
binder" here means: exercise all THREE constructor arms, AND move the
``alreadySet`` payload across empty and non-empty so the member-preservation
clause is probed below AND above its length-0 degenerate point. The reject
witnesses below cover ``coercible`` (at a non-empty payload via full coercion,
and at the EMPTY payload via a truthiness-split that accepts only the empty
not-a-set), ``alreadySet`` at a NON-EMPTY payload (drop / wrong-members) and at
the EMPTY payload (``alreadyset-empty-rejects``, which refuses exactly the empty
set), and ``absent``.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS here. The nagini sibling carries this
    class as MANDATORY because its ``real_apps`` input is held at a fractional
    heap permission (``Acc(list_pred(real_apps), 1/2)``) a rival could illegally
    write. Lean and Velvet are referentially transparent: ``arg`` is an immutable
    value, this bundle declares no ``mut`` parameter, and there is no heap and no
    aliasing — so there is no read-only input to overwrite and no substitute
    probe to fabricate. Not fabricated (per the porting map: this class is
    vacuous on Lean/Velvet). The sibling's ``frame-mutate-real-apps`` case has no
    counterpart here.
  * UNGROUNDED-ORACLE ECHO — N/A. ``normalizeSpec`` is a concrete ``def`` in the
    ``pure`` region and the ``axioms`` region is empty, so there is no answer key
    to echo. The honest grounded controls (a correct reshape + an admissibility
    non-degeneracy assert) are the directive-2 substitute.
  * PARTIAL-DOMAIN / VALUE — the core attacks. Each rival is correct on part of
    the ``SetArg`` partition but diverges on one arm: coerce the non-set arm
    (the pre-patch bug), drop / corrupt the members on the already-a-set arm, or
    reject the absent arm.

WITNESS MECHANICS ON THIS BUNDLE. The four postcondition clauses include two
UNBOUNDED quantifiers (``∀ xs`` / ``∀ ys``), so ``prove_postcondition_decidable_for``
cannot synthesise a ``Decidable`` instance for the whole contract and the
``<name>Tester`` route gets stuck (measured: ``decide`` cannot reduce the
tester). The witness therefore attacks the LOAD-BEARING equality clause
(C-eq, ``out = normalizeSpec arg``) DIRECTLY on the extracted program:
``normalizeSetArgExec arg`` reduces to ``DivM.res result``, and
``normalizeSetArgExec arg ≠ DivM.res (normalizeSpec arg)`` says the impl's
result contradicts the spec's grounded answer at that concrete ``arg``. Checked
in a file whose ``prove_correct`` block is stripped, so no tactic script can
mask the verdict; the method has no ``require`` clause, so every input reaches
the postcondition. Each witness ELABORATES against its rival (whose extracted
program reduces to the wrong constant) and FAILS against the frozen solution
(where the goal reduces to ``False``) — both halves checked out-of-band with
``scripts/lean_verify.sh`` (rival elaborates, gold fails) for every reject case.
The witnesses bind nothing (all inputs are concrete literals), so there is no
consistency-probe obligation.

AXIOM lane: EMPTY (``meta.json`` declares no ``axiom`` and no A-reference deep
model; the two primitive tests the construction performs — "absent?" and
"already a set?" — are modeled as the free input ``SetArg`` (directive 7), and
the changed action is modeled DEEPLY as ``normalizeSpec``). There is no callee
to axiomatize, so there is nothing for the axiom lane to probe and the gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-14765"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The WHOLE frozen impl body (everything strictly
# ---- between the markers). The individual `match` arms each occur twice in
# ---- Solution.lean (once in `normalizeSpec` in the frozen `pure` region, once
# ---- here), so anchoring on an arm alone would not be unique; the full block —
# ---- with its `let result` / `return result` — lies wholly inside the impl
# ---- region and is unique (both facts asserted at load by _swap). ----
_IMPL = (
    "    let result : Except InitErr (List String) :=\n"
    "      match arg with\n"
    "      | .absent        => Except.ok []\n"
    "      | .alreadySet xs => Except.ok xs\n"
    "      | .coercible _   => Except.error .rejected\n"
    "    return result"
)


def _impl(new_body: str) -> str:
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_asserted(prefix: str) -> str:
    """Frozen impl KEPT VERBATIM with an in-region `assert` prefixed to it.

    For the admissibility case: the frozen dispatch is untouched (so the four
    `ensures` clauses discharge exactly as they do for gold, and the case cannot
    pass by weakening anything), and the added obligation is a NEW goal the
    frozen `loom_solve` must also close. Both the assert and the impl body lie
    wholly inside the elided impl region, so the spec view and the
    `prove_correct` header are byte-identical.
    """
    return _swap(_BASE, _IMPL, prefix + _IMPL)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- and its postcondition carries unbounded quantifiers (so the `<name>Tester`
# ---- route cannot be made decidable). A witness therefore reaches the impl
# ---- through Velvet's extractor and states the load-bearing equality clause
# ---- directly: `normalizeSetArgExec arg` reduces to `DivM.res result`, and
# ---- `≠ DivM.res (normalizeSpec arg)` says the impl contradicts the grounded
# ---- spec answer at that input. Checked in a file whose `prove_correct` block
# ---- is stripped, so no tactic script can interfere. The witness binds nothing
# ---- (concrete literal input), so it carries no consistency-probe obligation.
def _witness(arg: str) -> str:
    return (
        "extract_program_for normalizeSetArg\n\n"
        f"example : normalizeSetArgExec ({arg}) ≠ DivM.res (normalizeSpec ({arg})) := by\n"
        "  unfold normalizeSetArgExec normalizeSetArg\n"
        "  simp [NonDetT.run, pure, normalizeSpec]\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # impl that MUST verify, else SPEC-TOO-STRONG. The three-arm dispatch is
    # written with the arms in a DIFFERENT order (reject arm first, absent arm
    # last). A `match` on disjoint constructors is order-insensitive, so the
    # computed result is identical on every arm and all four clauses still hold.
    # The frozen `loom_solve` script closes the byte-identical obligation on the
    # reordered arms with no retune (verified out-of-band with a real build).
    # =====================================================================
    {
        "id": "pos-reorder-arms",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    let result : Except InitErr (List String) :=\n"
            "      match arg with\n"
            "      | .coercible _   => Except.error .rejected\n"
            "      | .alreadySet xs => Except.ok xs\n"
            "      | .absent        => Except.ok []\n"
            "    return result"),
        "rationale": "structurally different CORRECT reshape: the three-way "
                     "dispatch is written with its arms reordered (reject arm "
                     "first, absent arm last). A match on disjoint constructors "
                     "is order-insensitive, so the result is identical on every "
                     "arm and `out = normalizeSpec arg` plus all three subsidiary "
                     "clauses still hold. A faithful reshape MUST verify, else "
                     "SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY (ADDED BY AUDIT) — on a total carrier the PRECOND-TOO-STRONG
    # direction is not vacuous just because the method declares no `require`.
    # The analogue is the obligation being UNSATISFIABLE or DEGENERATE at an
    # F2P-shaped input: a post-image no impl can meet reads exactly like one every
    # impl meets, and a post-image that collapses to a single constant answer
    # would make all four clauses hold for trivial reasons. This case discharges,
    # BY EVALUATION and as an in-region `assert` before the frozen obligation is
    # closed verbatim, that the spec's answer at each of the three arms is the
    # intended one AND that those answers are pairwise DISTINCT — so the
    # obligation is jointly satisfiable at a concrete supported input and the
    # three arms are genuinely discriminated rather than collapsed.
    # Checked out-of-band that the assert is LOAD-BEARING and not inert: the same
    # file with one clause replaced by a FALSE claim (`normalizeSpec (.coercible
    # ["A"]) = Except.ok ["A"]`) FAILS to build with `unsolved goals case
    # «admiss_1: ...»`, so a degenerate post-image would be caught here.
    # =====================================================================
    {
        "id": "admiss-f2p-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_asserted(
            "    assert (with_name_prefix `admiss\n"
            "      (normalizeSpec (.coercible [\"A\"]) = Except.error .rejected ∧\n"
            "       normalizeSpec .absent = Except.ok [] ∧\n"
            "       normalizeSpec (.alreadySet [\"A\"]) = Except.ok [\"A\"] ∧\n"
            "       normalizeSpec (.coercible [\"A\"]) ≠ normalizeSpec (.alreadySet [\"A\"]) ∧\n"
            "       normalizeSpec (.alreadySet [\"A\"]) ≠ normalizeSpec .absent))\n"),
        "rationale": "the obligation must be SATISFIABLE and NON-DEGENERATE at a "
                     "concrete input of the shape the failing test supplies. The "
                     "in-region assert discharges, by evaluation, that the spec's "
                     "answer is `error .rejected` at a supplied non-set argument "
                     "(the shape whose refusal is the load-bearing behaviour), "
                     "`ok []` at an absent argument, and `ok [\"A\"]` at an "
                     "already-a-set argument — and that those three answers are "
                     "PAIRWISE DISTINCT, so the post-image does not collapse to a "
                     "single constant that every impl would meet. The frozen "
                     "dispatch is kept VERBATIM, so the method's own four "
                     "`ensures` clauses discharge as they do for gold and this "
                     "case cannot pass by weakening any of them; the assert is a "
                     "NEW goal the frozen `loom_solve` must also close. Must "
                     "verify, else PRECOND-TOO-STRONG / SPEC-UNSATISFIABLE.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each swaps ONE arm of the three-way dispatch,
    # carries a machine-checked witness at a concrete input that fails on the
    # frozen solution, and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "coerce-nonset",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch bug: an argument that is not already a set is silently
        # turned into an (empty) set and ACCEPTED instead of being rejected.
        "module": _impl(
            "    let result : Except InitErr (List String) :=\n"
            "      match arg with\n"
            "      | .absent        => Except.ok []\n"
            "      | .alreadySet xs => Except.ok xs\n"
            "      | .coercible _   => Except.ok []\n"
            "    return result"),
        "refinement": "this is the pre-patch behaviour: a supplied argument that "
                      "is not already a set is silently converted into one and "
                      "stored, so construction returns normally. The failing test "
                      "constructs the object with a non-set collection and expects "
                      "the construction to be REJECTED; a variant that accepts and "
                      "coerces it returns normally instead, so the test still sees "
                      "a successful construction — it would NOT resolve. This is "
                      "exactly the behaviour the fix removes.",
        "rationale": "REJECT from (C-eq) out = normalizeSpec arg and (C-rej) "
                     "∀ ys, arg = .coercible ys → out = error .rejected: on a "
                     "coercible argument normalizeSpec yields error .rejected but "
                     "the rival yields ok []. Refuted at `.coercible [\"A\"]`, the "
                     "not-already-a-set arm.",
        "witness": _witness(".coercible [\"A\"]"),
    },
    {
        "id": "coercible-empty-accepts",
        "kind": "uniqueness",
        "expect": "reject",
        # A near-miss on the not-a-set arm that coerce-nonset does NOT subsume:
        # it REJECTS a non-empty non-set argument (correct on `.coercible ["A"]`,
        # exactly where coerce-nonset is refuted) but ACCEPTS an EMPTY non-set,
        # storing the empty collection instead of rejecting. Correct on the whole
        # partition EXCEPT the empty not-a-set sub-domain.
        "module": _impl(
            "    let result : Except InitErr (List String) :=\n"
            "      match arg with\n"
            "      | .absent        => Except.ok []\n"
            "      | .alreadySet xs => Except.ok xs\n"
            "      | .coercible ys  =>\n"
            "        if ys.isEmpty then Except.ok [] else Except.error .rejected\n"
            "    return result"),
        "refinement": "the faithful real patch guards the refusal on truthiness "
                      "rather than on is-None: it refuses a supplied non-set "
                      "argument only when that argument is non-empty, so an EMPTY "
                      "non-set argument (which is falsy) slips past and is stored "
                      "as the empty collection instead of being rejected. The "
                      "desired behaviour refuses EVERY supplied non-set argument, "
                      "empty or not; a test that supplies an empty non-set and "
                      "expects the construction to be refused would still see a "
                      "successful construction — it would NOT resolve. Distinct "
                      "from coerce-nonset, which accepts EVERY non-set argument: "
                      "this rival agrees with the desired behaviour on a non-empty "
                      "non-set and diverges ONLY on the empty non-set sub-domain, "
                      "so coerce-nonset's witness (at a non-empty non-set) does not "
                      "refute it.",
        "rationale": "REJECT from (C-eq) out = normalizeSpec arg and (C-rej) "
                     "∀ ys, arg = .coercible ys → out = error .rejected: on a "
                     "coercible argument normalizeSpec yields error .rejected for "
                     "EVERY payload, but the rival yields ok [] when the payload is "
                     "empty. Refuted at `.coercible []`, the empty not-a-set point "
                     "no other reject witness probes — coerce-nonset is refuted at "
                     "`.coercible [\"A\"]`, where THIS rival agrees with the spec.",
        "witness": _witness(".coercible []"),
    },
    {
        "id": "drop-members",
        "kind": "uniqueness",
        "expect": "reject",
        # Accepts an already-a-set argument (correct outcome) but stores the
        # EMPTY collection instead of the argument's members.
        "module": _impl(
            "    let result : Except InitErr (List String) :=\n"
            "      match arg with\n"
            "      | .absent        => Except.ok []\n"
            "      | .alreadySet _  => Except.ok []\n"
            "      | .coercible _   => Except.error .rejected\n"
            "    return result"),
        "refinement": "storing the empty collection for an already-a-set argument "
                      "corresponds to a real patch that accepts the set but "
                      "replaces it with a fresh empty one — the stored collection "
                      "loses every member the caller supplied. Downstream code "
                      "reads back the stored collection by membership; with the "
                      "members dropped the object behaves as if the caller passed "
                      "nothing, so a test that builds it from a non-empty set and "
                      "relies on that membership FAILS — it would NOT resolve.",
        "rationale": "REJECT from (C-eq) and (C-set) ∀ xs, arg = .alreadySet xs → "
                     "out = ok xs: normalizeSpec keeps the members `xs`, the rival "
                     "returns ok [] regardless. Refuted at `.alreadySet [\"A\"]`, a "
                     "NON-EMPTY set payload where [] ≠ [\"A\"].",
        "witness": _witness(".alreadySet [\"A\"]"),
    },
    {
        "id": "wrong-members",
        "kind": "uniqueness",
        "expect": "reject",
        # Right shape (accepts the set), wrong members: appends a spurious extra
        # member. A near-miss that agrees with gold on the EMPTY set (where a
        # drop-all rival also agrees) but diverges on every non-empty set — and
        # even on the empty set here, since it appends unconditionally.
        "module": _impl(
            "    let result : Except InitErr (List String) :=\n"
            "      match arg with\n"
            "      | .absent        => Except.ok []\n"
            "      | .alreadySet xs => Except.ok (xs ++ [\"X\"])\n"
            "      | .coercible _   => Except.error .rejected\n"
            "    return result"),
        "refinement": "adding a member to the stored set corresponds to a real "
                      "patch that accepts the caller's set but stores a SUPERSET "
                      "of it (an extra app label). Downstream membership reads then "
                      "see an entry the caller never supplied, so an object built "
                      "from a specific set no longer equals / iterates to that set; "
                      "a test asserting the exact stored membership FAILS — it "
                      "would NOT resolve. Distinct from drop-members: this stores "
                      "the WRONG members rather than none, and diverges even on a "
                      "set whose intended stored value is a strict subset.",
        "rationale": "REJECT from (C-eq) and (C-set): normalizeSpec keeps `xs` "
                     "exactly, the rival returns ok (xs ++ [\"X\"]). Refuted at "
                     "`.alreadySet [\"B\", \"C\"]`, where the spec demands "
                     "[\"B\", \"C\"] but the rival yields [\"B\", \"C\", \"X\"] — a "
                     "member-level near-miss (right constructor, wrong payload).",
        "witness": _witness(".alreadySet [\"B\", \"C\"]"),
    },
    {
        "id": "alreadyset-empty-rejects",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. Attacks the already-a-set arm at its EMPTY payload —
        # the point the two member-level rivals above leave unprobed (both are
        # refuted at a NON-EMPTY payload, and BOTH agree with the spec on the
        # empty set: drop-members returns ok [] which IS correct there, and
        # wrong-members' divergence is only visible because it appends). This
        # rival is correct on every non-empty set and refuses ONLY the empty one.
        "module": _impl(
            "    let result : Except InitErr (List String) :=\n"
            "      match arg with\n"
            "      | .absent        => Except.ok []\n"
            "      | .alreadySet xs =>\n"
            "        if xs.isEmpty then Except.error .rejected else Except.ok xs\n"
            "      | .coercible _   => Except.error .rejected\n"
            "    return result"),
        "refinement": "this is the mirror-image truthiness confusion to "
                      "coercible-empty-accepts: a faithful real patch that gates "
                      "ACCEPTANCE of a supplied set on that set being non-empty "
                      "refuses an argument that is a genuine but EMPTY set, "
                      "instead of storing it as the empty collection. Supplying "
                      "an empty set of this kind is a normal, supported call, so "
                      "a patch that refused it would break the passing tests that "
                      "construct the object that way — it would NOT resolve. "
                      "Distinct from drop-members and wrong-members, which get "
                      "the empty-set case RIGHT and corrupt only non-empty "
                      "payloads; this one is correct on every non-empty payload "
                      "and wrong only at the degenerate point.",
        "rationale": "REJECT from (C-eq) out = normalizeSpec arg and (C-set) "
                     "∀ xs, arg = .alreadySet xs → out = Except.ok xs: the clause "
                     "pins ok xs for EVERY payload including the empty one, but "
                     "the rival yields error .rejected there. Refuted at "
                     "`.alreadySet []`, the length-0 degenerate point of the "
                     "member-preservation clause that no other reject witness "
                     "reaches — drop-members and wrong-members are refuted at "
                     "non-empty payloads, where THIS rival agrees with the spec.",
        "witness": _witness(".alreadySet []"),
    },
    {
        "id": "absent-rejects",
        "kind": "uniqueness",
        "expect": "reject",
        # Rejects the ABSENT argument instead of supplying the empty-collection
        # default. Attacks the absent arm, which the other three rivals leave
        # untouched.
        "module": _impl(
            "    let result : Except InitErr (List String) :=\n"
            "      match arg with\n"
            "      | .absent        => Except.error .rejected\n"
            "      | .alreadySet xs => Except.ok xs\n"
            "      | .coercible _   => Except.error .rejected\n"
            "    return result"),
        "refinement": "rejecting an absent argument corresponds to a real patch "
                      "that fails construction when no collection is supplied "
                      "instead of defaulting it to the empty collection. Almost "
                      "every construction of this object omits the argument, so a "
                      "patch that raised on the absent case would break the "
                      "overwhelming majority of the passing tests (which build the "
                      "object with no such argument) — it would NOT resolve, and "
                      "would in fact regress the whole suite.",
        "rationale": "REJECT from (C-eq) and (C-abs) arg = .absent → out = ok []: "
                     "normalizeSpec .absent = ok [] but the rival returns "
                     "error .rejected. Refuted at `.absent`, the arm no other "
                     "reject witness probes.",
        "witness": _witness(".absent"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 SPEC cases (1 soundness
# positive, 1 admissibility, 1 frame-mutation, 3 partial-domain/value rivals) and
# an EMPTY axiom lane. Both bundles model the SAME single behaviour — how the
# optional set-typed argument is normalized at construction — but over different
# carriers: nagini uses a heap-permissioned List[int] plus separate boolean
# inputs (`present`, `is_expected_kind`), whereas velvet folds the two primitive
# tests into the single free input `SetArg` (a three-way partition) and models
# the rejection as `Except.error`.
#
#   sibling case                          -> here                    disposition
#   ---------------------------------------------------------------------------
#   pos-control-reorder-decision          -> pos-reorder-arms         PORTED
#   admiss-f2p-p2p-shaped-input           -> admiss-f2p-nondegenerate RE-AIMED
#   frame-mutate-real-apps                -> (none)                   VACUOUS
#   prepatch-coerce-nonempty-offkind      -> coerce-nonset            PORTED
#   partial-domain-raise-nonempty-only    -> coercible-empty-accepts  PORTED
#   partial-domain-drop-last              -> drop-members / wrong-members  RE-EXPRESSED
#   (no sibling)                          -> absent-rejects           ADDED
#   (no sibling)                          -> alreadyset-empty-rejects ADDED (audit)
#   AXIOM_TESTS (empty)                   -> (none)                   N/A
#
# PORTED (positive control): the sibling reorders the decision (raise-first,
#   then absent, then copy). Here the dispatch is a `match`; the port reorders
#   its three arms (reject arm first, absent arm last). Order-insensitive on
#   disjoint constructors, so it stays correct; the frozen `loom_solve` closes it
#   unchanged. Verified to build (expect="verify").
# PORTED (the pre-patch bug): prepatch-coerce-nonempty-offkind IS the pre-patch
#   silent coercion of a present off-kind collection. It ports directly to
#   coerce-nonset: the `.coercible` arm returns `ok []` (accept + coerce) instead
#   of `error .rejected`. This is the F2P discriminator.
# PORTED (partial-domain-raise-nonempty-only): the sibling's "only raise on a
#   NON-EMPTY off-kind collection; an EMPTY off-kind slips through" bug exploited
#   nagini's `len(real_apps) > 0` truthiness split of the off-kind sub-domain.
#   The `.coercible ys` payload carries its own members here, so `ys.isEmpty` is a
#   live emptiness binder on the not-a-set arm — the truthiness split IS
#   expressible on this carrier. It ports directly to coercible-empty-accepts: the
#   `.coercible` arm returns `error .rejected` for a non-empty payload but `ok []`
#   for an empty one. This is NOT subsumed by coerce-nonset: coerce-nonset accepts
#   EVERY non-set argument and is refuted at `.coercible ["A"]`, exactly where this
#   rival AGREES with the spec; this rival diverges only on the empty not-a-set
#   sub-domain and is refuted at `.coercible []`. (An earlier port dropped this as
#   a carrier-narrowing "fold" on the theory that emptiness on the not-a-set arm
#   is unobservable; that is false — the spec's (C-rej) clause pins error for
#   every payload, and a machine-checked witness at `.coercible []` refutes the
#   rival and fails on gold, so the distinction is real and expressible.)
# RE-EXPRESSED (partial-domain-drop-last): the sibling's off-by-one drops the
#   last stored element. On this carrier the stored value is the argument's
#   member list, pinned element-wise by (C-set). "Corrupt the stored membership"
#   re-expresses as TWO member-level rivals on the already-a-set arm:
#   drop-members (store [] — the degenerate loss) and wrong-members (store a
#   superset — a near-miss the drop rival does not subsume, refuted on a set whose
#   correct value differs from the rival's by an extra element). Together they
#   probe the `alreadySet` payload at empty-answer and non-empty-answer points.
# ADDED (absent-rejects, no sibling): the `SetArg.absent` arm has its own clause
#   (C-abs). No sibling rival attacks the absent default directly (the sibling's
#   absent case only appears inside the reorder positive), so a rival that rejects
#   the absent argument is added to attack (C-abs) and move `arg` to `.absent` —
#   the arm no other reject witness probes.
# RE-AIMED (admissibility): the sibling's half-permission assertion has no
#   counterpart here (referential transparency, no permissions), and the method
#   declares no `require` — but that is NOT a reason to drop the lane, and an
#   earlier port dropped it on exactly that reasoning. On a total carrier the
#   PRECOND-TOO-STRONG analogue is the obligation being unsatisfiable or
#   DEGENERATE at an F2P-shaped input, and the sibling's per-branch facts re-aim
#   directly onto it: admiss-f2p-nondegenerate discharges, by evaluation and as an
#   in-region `assert` placed before the frozen obligation is closed verbatim,
#   that the spec's answer at each of the three arms is the intended one and that
#   the three answers are pairwise DISTINCT. The earlier port's argument for
#   dropping it ("the reject cases already witness the arms distinct") is not a
#   substitute: those cases show gold differs from each WRONG constant, which is a
#   property of the rivals, whereas this case shows the spec's own post-image is
#   jointly satisfiable and non-collapsing at one concrete supported input — the
#   thing an expect="verify" case is what tests. Confirmed load-bearing rather
#   than decorative: substituting a FALSE claim for one conjunct makes the file
#   fail to build (`unsolved goals case «admiss_1: ...»`).
# VACUOUS (frame-mutation): the sibling carries this MANDATORY because `real_apps`
#   is held at Acc(list_pred(real_apps), 1/2) — read-only — a rival could
#   illegally write. Lean and Velvet are referentially transparent, have no
#   heap/aliasing, and this bundle declares no `mut` parameter — `arg` is an
#   immutable value with no permission footprint, so there is no read-only input
#   to overwrite and no substitute probe. Not fabricated (porting map: vacuous).
#
# BINDER / CLAUSE COVERAGE of the SIX reject witnesses over the single input
#   binder `arg` and the four clauses:
#     arg constructor arm — .coercible (coerce-nonset at ["A"],
#                           coercible-empty-accepts at []), .alreadySet
#                           (drop-members / wrong-members at non-empty,
#                           alreadyset-empty-rejects at []), .absent
#                           (absent-rejects): all THREE arms exercised.
#     coercible payload   — [] and ["A"], so the not-a-set arm is probed at BOTH
#                           its empty and non-empty points (the emptiness binder
#                           `ys.isEmpty` the truthiness-split rival abuses).
#     alreadySet payload  — [] (alreadyset-empty-rejects), ["A"] (drop-members)
#                           and ["B","C"] (wrong-members), so the
#                           member-preservation clause is probed BOTH at its
#                           length-0 degenerate point and above it, the latter at
#                           a point where the correct answer and the rival's
#                           differ by exactly one element (member-level).
#                           (An earlier port claimed this two-sided coverage while
#                           in fact probing only non-empty payloads; the empty
#                           point is now actually demonstrated, with a
#                           machine-checked witness that elaborates on the rival
#                           and fails on gold.)
#   CLAUSES: (C-eq) out = normalizeSpec arg attacked by all six; (C-rej) by
#     coerce-nonset and coercible-empty-accepts; (C-set) by drop-members,
#     wrong-members and alreadyset-empty-rejects; (C-abs) by absent-rejects.
#     Every top-level clause is attacked. All six reject witnesses probe DISTINCT
#     input points: .coercible ["A"], .coercible [], .alreadySet [],
#     .alreadySet ["A"], .alreadySet ["B","C"], .absent (pts=6).
#
# AXIOM_TESTS: dropped/empty. The sibling's axiom lane is already empty
# (meta.json axioms == [] and deep_model_references == []); this bundle likewise
# declares no axiom and no A-reference (the primitive tests are the free input
# SetArg, the action is the deep model normalizeSpec), so there is nothing for
# the axiom lane to probe and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
