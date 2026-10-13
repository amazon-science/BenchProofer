"""properties.py — G-PBT falsification battery for django__django-12419 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct`` obligation survives) and swaps in a candidate
implementation, checked by the real verifier. ``expect:"verify"`` passes iff
(in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does NOT
verify AND its refutation ``witness`` discriminates: elaborates against the
rival, FAILS against the frozen solution).

DEFENDED SURFACE (one contracted query over the empty input domain):

  defaultReferrerPolicy return (policy)   ensures policy = sameOriginPolicy
                                          ensures policy = "same-origin".toList
                                          ensures policy ≠ []

The modeled behaviour is the framework's DEFAULT policy token: a definite,
restrictive same-origin restriction, supplied out of the box in place of the
unset/absent sentinel (modeled as the empty token sequence) that would emit no
policy at all. The query takes NO input and mutates nothing.

  Load-bearing clauses:
    (C1) policy = sameOriginPolicy        -- the EXACT default token; also the
    (C2) policy = "same-origin".toList       same token spelled as a literal
                                             (C1 and C2 are the same predicate,
                                             so a rival violating one violates
                                             both).
    (C3) policy ≠ []                      -- a definite policy is provided, NOT
                                             the unset/absent sentinel that
                                             emits nothing.

  CLAUSE DEPENDENCE (machine-checked during audit; corrects an earlier claim in
  this file that C3 was independently load-bearing). All three clauses are
  equivalent to C1 alone. Proved in Lean against this carrier:

      c1_entails_c3   : p = sameOriginPolicy → p ≠ []          (by `decide`)
      c1_iff_c2       : p = sameOriginPolicy ↔ p = "same-origin".toList
      post_collapses  : (C1 ∧ C2 ∧ C3) ↔ C1

  C2 is the same predicate as C1 (``sameOriginPolicy`` is a ``def`` for that very
  literal, so the two differ only by an unfolding). C3 is *entailed* by C1: the
  token is a fixed non-empty literal, so anything equal to it is non-empty. There
  is therefore NO rival that can violate C3 while satisfying C1 — C3 excludes
  nothing C1 has not already excluded, and it cannot be attacked "independently".
  C3 documents intent (a definite policy rather than the absent sentinel) and
  earns its place as a readable statement of the security property; it does not
  add falsification surface. The battery is honest about this rather than
  claiming three separable facets it cannot exhibit.

  What this means for the reject lane: every rival below is refuted by C1, and
  ``weak-absent-sentinel`` is a rival against the *pre-fix value* (which is the
  behaviour the fix replaces, so it is worth keeping as a regression probe), NOT
  a rival that isolates a distinct clause.

  There is no opaque answer-key oracle: ``sameOriginPolicy`` is a concrete
  ``def`` in the ``pure`` region equal to a fixed literal, so pinning
  ``policy = sameOriginPolicy`` is grounded, not an echo.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME-MUTATION — VACUOUS. The class exists on nagini because the input
    carries a fractional heap permission (only ``Acc(list_pred(slot.value),
    1/2)`` is held), so an impl that appends in place must be rejected for
    insufficient permission. Lean/Velvet are referentially transparent: there
    is no heap, no aliasing, no fractional permission — AND this bundle's query
    takes no parameters and declares no ``mut`` binder, so there is no
    read-only input to overwrite. No substitute probe is fabricated.
  * SETDEFAULT-IDENTITY (nagini P2) — NO COUNTERPART. On nagini the "never
    clobber an already-present header" guarantee is a control-flow effect over
    a mutable slot, pinned by ``Old(slot.present) → slot.value is
    Old(slot.value)``. This bundle models ONLY the constant default-policy
    PROVIDER — the setting value. The downstream consumer that performs the
    setdefault (the security middleware) is unchanged by the fix and is not
    modeled here (mapping.md §3). There is no present/absent pre-state, no
    ``Old`` frame, and no mutation to observe, so the P2 attack has nothing to
    land on. Reported as an omission (module footer), not faked.
  * UNGROUNDED-ORACLE ECHO — N/A. ``sameOriginPolicy`` is a concrete literal,
    the ``axioms`` region is empty, and the post-images are total functions of
    no input. There is no answer-key to echo; the positives are honest
    cheapest-reshape controls.
  * WRONG-VALUE / PARTIAL-DOMAIN — APPLIES to C1/C2: a rival attaching a
    DIFFERENT non-empty token, or the exact token with the final code point
    dropped (a near-miss right on the 10-element prefix).
  * ABSENT-SENTINEL — a rival yielding the empty token sequence (the pre-fix
    unset value) satisfies nothing. It is refuted by C1 like every other rival
    (C3 is entailed by C1 — see CLAUSE DEPENDENCE above, machine-checked), so it
    does NOT isolate the non-emptiness clause. Its value is as a regression probe
    aimed at the specific pre-fix value the change replaces.

WITNESS PLACEMENT. The query takes NO argument, so its extracted tester is a
single ``Bool`` (``defaultReferrerPolicyTester : Bool``) — there is exactly ONE
input point (the empty tuple) at which any rival can be refuted, and
``pts=1`` is therefore STRUCTURAL, not a coverage gap: there is no binder to
vary because there is no binder. Each reject case's witness asserts
``defaultReferrerPolicyTester = false`` — i.e. the extracted program violates
the postcondition. The three rivals return THREE DISTINCT wrong values (a
different non-empty token / the token truncated by one code point / the absent
sentinel), so they are three genuinely different implementations; but they are
all refuted by the SAME clause, C1, because the post-image collapses to C1 (see
CLAUSE DEPENDENCE). They probe three distinct *value* divergences — a wholly
different token, a one-code-point near-miss, and the pre-fix empty value — not
three distinct clauses. The witness snippet text coincides only because the carrier
admits a single input; it is elaborated against each rival's own impl and each
FAILS against the frozen solution (machine-checked both halves).

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the default
policy is a value supplied directly, modeled deeply as its concrete token
sequence). There is no axiom-soundness obligation to probe, and the gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-12419"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor (lies wholly inside the single impl region and is
# ---- unique in Solution.lean; both facts asserted at load by _swap). No
# ---- case here retunes the proof body: the frozen tactic
# ---- (`loom_solve <;> simp [sameOriginPolicy]`) already unfolds the token
# ---- definition, so every reshape below closes under it unchanged.
_A_RETURN = "    return sameOriginPolicy"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `defaultReferrerPolicyTester = false` says the extracted program's
# ---- result violates the method's postcondition. The query takes no argument,
# ---- so the tester is a nullary `Bool`. Checked in a file whose
# ---- `prove_correct` block has been stripped, so no tactic script can mask
# ---- the verdict.
_WITNESS = (
    "extract_program_for defaultReferrerPolicy\n"
    "prove_precondition_decidable_for defaultReferrerPolicy\n"
    "prove_postcondition_decidable_for defaultReferrerPolicy\n"
    "derive_tester_for defaultReferrerPolicy\n\n"
    "example : defaultReferrerPolicyTester = false := by\n  decide\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps every obligation and only reshapes
    # the executable surface; the post-images are point-wise over a
    # zero-argument value, so no induction is needed and each reproof stays a
    # single `simp`-unfold away from the frozen script.
    # =====================================================================
    {
        "id": "pos-literal-token",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: return the token spelled as the string literal instead of
        # through the named definition. Observationally the same token.
        "module": _swap(_BASE, _A_RETURN, '    return "same-origin".toList'),
        "rationale": "returning the default token as its literal form instead "
                     "of via the named definition yields the same token, so all "
                     "three clauses (all equivalent to C1's exact value) still "
                     "discharge; a correct reshape must verify, else "
                     "SPEC-TOO-STRONG. The frozen tactic already unfolds "
                     "`sameOriginPolicy`, so no retuning is needed.",
    },
    {
        "id": "pos-named-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the token to a typed local, then return it. Same value
        # flow; the frozen proof still closes after unfolding the definition.
        "module": _swap(
            _BASE, _A_RETURN,
            "    let p : List Char := sameOriginPolicy\n    return p"),
        "rationale": "binding the default token to a typed local before "
                     "returning it leaves the returned value unchanged, so "
                     "C1 (and hence C2/C3, which it entails) still holds; a "
                     "correct reshape must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — the query has no `require` clause, so there is no
    # precondition that could exclude a normal input; the usual "a normal
    # input satisfies the precondition" probe is vacuously satisfied (the
    # domain is the empty tuple). The residual admissibility risk on a total
    # domain is that the post-image is UNSATISFIABLE / DEGENERATE — a spec no
    # impl can meet reads exactly like a spec every impl meets.
    #
    # STRENGTHENED BY AUDIT. The original assert claimed only
    # `sameOriginPolicy = "same-origin".toList ∧ sameOriginPolicy ≠ []`, which is
    # C2 ∧ C3 restated about the definition itself — both entailed by unfolding a
    # `def`, so it exercised the post-image at no concrete point. It now discharges
    # the FULL post-image at the CONCRETE token the F2P assertion observes, written
    # out as its explicit 11-element code-point sequence (`observed`) rather than
    # via the named definition, plus its length. That is the total-carrier analogue
    # of the sibling's absent-input self-call: the obligation is shown satisfiable
    # BY EVALUATION at exactly the F2P-shaped value, and only then is the frozen
    # obligation closed verbatim. Machine-checked live during the audit: the case
    # verifies (exit 0), and the same case with `observed.length = 10` fails with
    # `unsolved goals … ⊢ False` (exit 1), so the assert is load-bearing and not
    # an unfolding tautology.
    # =====================================================================
    {
        "id": "admiss-token-definite-nonempty",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _A_RETURN,
            "    assert (with_name_prefix `assert\n"
            "      (let observed : List Char :=\n"
            "         ['s','a','m','e','-','o','r','i','g','i','n']\n"
            "       observed = sameOriginPolicy ∧ observed = \"same-origin\".toList ∧\n"
            "         observed ≠ [] ∧ observed.length = 11))\n"
            "    return sameOriginPolicy"),
        "rationale": "the post-image is satisfiable AND non-degenerate AT A "
                     "CONCRETE POINT: the assert names the F2P-observable token as "
                     "an explicit 11-element code-point sequence (NOT via the "
                     "named definition, so it cannot discharge by unfolding alone) "
                     "and discharges the whole post-image plus the length at that "
                     "value, by evaluation. This is the total-carrier analogue of "
                     "a precondition-admits-a-normal-input probe: an unsatisfiable "
                     "or degenerate obligation reads exactly like one every impl "
                     "meets, and evaluating it at the value the failing test "
                     "observes is what tells them apart. Verified live during the "
                     "audit, with a false-length variant of the same case failing "
                     "on an unsolved goal, so the assert is load-bearing. The impl "
                     "is kept verbatim so all the ensures clauses discharge too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # the single input point and the refinement argument that its faithful
    # real counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-wrong-policy-value",
        "kind": "uniqueness",
        "expect": "reject",
        # Attaches a DIFFERENT non-empty token (the code points of another,
        # more permissive policy). Non-empty, so C3 holds, but the exact value
        # is wrong — C1/C2 fail.
        "module": _swap(_BASE, _A_RETURN, '    return "no-referrer".toList'),
        "refinement": "a real patch choosing a different default policy token "
                      "would ship that other token as the setting value, and the "
                      "downstream consumer forwards it verbatim into the "
                      "Referrer-Policy header. The failing test asserts the "
                      "default middleware stack emits exactly the same-origin "
                      "header line, so a different token would emit a different "
                      "header line and would NOT resolve.",
        "rationale": "REJECT from C1/C2 (policy = sameOriginPolicy): a non-empty "
                     "but DIFFERENT token satisfies C3 (≠ []) yet is not the "
                     "exact default token the post-image pins.",
        "witness": _WITNESS,
    },
    {
        "id": "weak-truncated-last-code-point",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss: the exact default token with the FINAL code point dropped.
        # Correct on the 10-element prefix, diverges on the last element.
        # Non-empty, so C3 holds; C1/C2 fail on length / last element.
        "module": _swap(_BASE, _A_RETURN, '    return "same-origi".toList'),
        "refinement": "a real value that dropped the final character of the "
                      "default token would ship a truncated setting, and the "
                      "consumer would forward it as a truncated header value. "
                      "The failing test asserts the FULL header line, so a "
                      "last-element divergence would NOT resolve. This is the "
                      "sub-domain (final code point) a tight post-image must "
                      "defend and a near-miss only agrees with by luck on the "
                      "prefix.",
        "rationale": "REJECT from C1/C2 (policy = sameOriginPolicy): the "
                     "10-element prefix matches but the full token requires all "
                     "eleven code points, so the truncated token fails on "
                     "length / last element while still satisfying C3 (≠ []).",
        "witness": _WITNESS,
    },
    {
        "id": "weak-absent-sentinel",
        "kind": "uniqueness",
        "expect": "reject",
        # Yields the empty token sequence — the unset/absent sentinel the change
        # replaces. Refuted by C1 (as is every rival: C3 is entailed by C1, see
        # CLAUSE DEPENDENCE). Kept as the regression probe aimed at the exact
        # pre-change value, not as an isolator of the non-emptiness clause.
        "module": _swap(_BASE, _A_RETURN, "    return []"),
        "refinement": "leaving the default as the unset/absent sentinel is "
                      "precisely the pre-fix behaviour: the consumer emits NO "
                      "policy header at all when the setting is falsy. The "
                      "failing test asserts the header line is PRESENT with the "
                      "same-origin value, so an absent default would NOT resolve "
                      "(no line emitted). This is the exact defect the fix "
                      "corrects.",
        "rationale": "REJECT from C1 (policy = sameOriginPolicy): the empty "
                     "token sequence is not the exact default token. C3 (≠ []) "
                     "is also violated, but C3 is ENTAILED by C1 on this carrier "
                     "(machine-checked: post_collapses), so this rival does not "
                     "attack a separate clause — it is the regression probe for "
                     "the absent-sentinel value the change replaces.",
        "witness": _WITNESS,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 SPEC cases (1
# soundness positive, 1 admissibility, 4 uniqueness rivals) over a stateful
# `HeaderSlot` carrier with fractional heap permissions. THIS bundle is a
# radically narrowed carrier: it models ONLY the constant default-policy
# PROVIDER (the shipped default-policy setting value), a zero-argument query
# returning a fixed `List Char`. The stateful slot, the present/absent
# pre-state, the setdefault control-flow effect, and the fractional list
# permission are all downstream-consumer machinery the fix does not touch and
# this bundle does not model (mapping.md §3). Carrier narrowing, not a gap in
# coverage of what IS modeled.
#
#   sibling case                    -> here
#   ---------------------------------------------------------------------
#   pos-control-literal-value       -> pos-literal-token                PORTED
#   frame-mutation-append-inplace   -> (none)                           VACUOUS
#   weak-wrong-policy-value         -> weak-wrong-policy-value          PORTED
#   weak-truncated-last-element     -> weak-truncated-last-code-point   PORTED
#   weak-setdefault-overwrite       -> (none)          NO COUNTERPART (unmodeled)
#   admiss-absent-slot-selfcall     -> admiss-token-definite-nonempty   RE-AIMED
#
# 3 ported, 1 re-aimed, 2 omitted = 6.
#
# PORTED (3): the value-oriented cases carry over directly. The sibling's
#   positive control reshapes the per-element copy loop into a single literal;
#   here the impl is already a single return, so the cheapest correct reshape is
#   the literal-vs-named-definition swap (pos-literal-token). The two weak-value
#   rivals (a different non-empty policy; the token truncated by one code point)
#   port their ARGUMENT verbatim — only the carrier changes from a mutated slot
#   field to a returned `List Char`.
# RE-AIMED (admissibility): the sibling's case constructs a fresh absent slot
#   and self-calls to confirm the precondition admits it. This query has no
#   `require` clause and no input, so that probe is vacuous. It is re-aimed at
#   the residual total-domain risk — an UNSATISFIABLE/degenerate post-image — by
#   discharging an in-region assert that the exact default token is a definite
#   non-empty policy equal to its literal form (verified live: a false claim at
#   the same token leaves an unsolved goal).
# VACUOUS (frame-mutation): the sibling's mandatory read-only-input probe needs
#   a fractional heap permission an impl can overwrite. This backend is
#   referentially transparent, has no heap/aliasing, and this bundle declares no
#   `mut` binder and takes no parameter — there is no read-only input to mutate.
#   No substitute fabricated (per the porting map: this class is VACUOUS here).
# NO COUNTERPART (setdefault-overwrite): the sibling's P2 rival attacks the
#   "never clobber an already-present header" guarantee — a control-flow effect
#   over a mutable slot pinned by an `Old(...)` identity clause. This bundle
#   models the constant provider, not the middleware that performs the
#   setdefault; there is no pre-state, no `Old` frame, and no mutation, so the
#   attack has nothing to land on. Omitted because the modeled surface does not
#   include that behaviour, NOT because it was hard to prove.
#
# ADDED (1, no sibling counterpart): weak-absent-sentinel returns the empty
#   token sequence — the pre-change unset/absent value. It mirrors the exact
#   behaviour the change replaces (an absent default emits no header line), so it
#   is the regression probe for that value. It is refuted by C1 like every other
#   rival — C3 is entailed by C1 (machine-checked; see CLAUSE DEPENDENCE), so it
#   does NOT attack a clause the other rivals leave alone. A real divergence with
#   a machine-checked witness, not fabricated wrongness.
#
# BINDER / POINT COVERAGE. The modeled query takes NO argument, so there is no
#   input binder to vary and the extracted tester is a nullary `Bool`. There is
#   exactly ONE input point (the empty tuple); `pts=1` is therefore STRUCTURAL,
#   not a coverage defect — the coverage tool's "move the witness to a
#   distinguishing input" finding is N/A because no distinct input exists.
#
#   Nor can the battery carry CLAUSE coverage, and the audit corrected an earlier
#   claim here that it did: the post-image collapses to C1 (machine-checked —
#   post_collapses, see CLAUSE DEPENDENCE), so there is exactly ONE separable
#   clause and every rival is refuted by it. This is a property of the frozen
#   spec, not a gap the battery could close by adding cases: no impl can violate
#   C2 or C3 while satisfying C1.
#
#   What the battery therefore varies is the WRONG VALUE returned, which is the
#   only axis available: a wholly different non-empty token
#   (weak-wrong-policy-value), a one-code-point near-miss on the correct token
#   (weak-truncated-last-code-point), and the pre-change absent sentinel
#   (weak-absent-sentinel). Those are three genuinely different impls, and the
#   near-miss in particular is the one a value-fuzzer only catches by luck. The
#   three reject witnesses share the same snippet text ONLY because the carrier
#   admits a single input; each is elaborated against its own rival impl and each
#   FAILS against the frozen solution.
#
#   AUDIT NOTE (spec-too-strong probes, machine-checked, not shipped as cases):
#   five further CORRECT reshapes were built and all VERIFY under the frozen
#   tactic — an explicit 11-element char list, `"same-".toList ++ "origin".toList`,
#   a two-local append, a `'s' :: "ame-origin".toList` cons, and an
#   `if … = [] then [] else …` guard. So the spec is not rejecting faithful
#   reshapes. A while-loop reshape that rebuilds the token element-by-element
#   (the sibling positive's original shape) could NOT be closed in 5 proof
#   attempts: `loom_solve` leaves a `List.take`/`List.drop` step goal that
#   `simp_all`/`omega`/`interval_cases`/`decide +kernel` did not discharge
#   (`decide +kernel` fails with "Expected type must not contain free
#   variables"). That is a TACTIC limit on a loop-bearing variant of a constant
#   provider, not evidence of a spec hole; recorded as uncertain rather than
#   claimed either way.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (the default policy is a value modeled deeply as its concrete token
# sequence), so there is nothing there to probe.
AXIOM_TESTS = []
