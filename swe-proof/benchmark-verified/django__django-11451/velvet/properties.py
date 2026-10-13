"""properties.py — G-PBT falsification battery for django__django-11451 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps with a verdict. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the ``prove_correct``
tactic body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct authGuard`` obligation
survives with a byte-identical statement) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE. One contracted method over four read-only inputs, whose whole
postcondition is a single equality against a total pure decision function:

  authGuard (suppliedName recoveredName : Option Name)
            (password : Option Secret) (backendOutcome : Option Principal)
            return (out : AuthOutcome)
    ensures out = authDecision suppliedName recoveredName password backendOutcome

where ``authDecision`` returns ``{ queried := false, principal := none }`` when
the effective identifier (the supplied one if present, else the recovered one)
is absent OR the secret is absent, and otherwise ``{ queried := true,
principal := backendOutcome }`` — perform the expensive downstream work and hand
back its outcome ONLY when both credentials are present. There is no ``require``
clause, so the admitted domain is total.

The single ``ensures`` clause pins an ``AuthOutcome`` with TWO independently
attackable FACETS, over four INPUT BINDERS:

  (F-queried) ``out.queried`` — whether the expensive downstream work (store
      lookup + credential-strength computation) is performed. It MUST be
      ``false`` exactly when the effective identifier or the secret is absent,
      and ``true`` exactly when both are present. This is THE fix: the
      admissibility short-circuit that suppresses the useless query/hasher run
      on incomplete credentials. A body that proceeds on an absent credential
      fails here — the pre-change behaviour the F2P test observes.
  (F-principal) ``out.principal`` — the principal handed back. On the proceed
      path it MUST equal the free input ``backendOutcome`` verbatim (the outcome
      of the UNCHANGED downstream lookup/verify chain, mapping.md §3); on the
      short-circuit path it MUST be ``none``. GROUNDED in the input
      ``backendOutcome`` (directive 8), not an opaque answer key — a body that
      fabricates the principal (a constant, or ``none`` where the chain located
      one) fails here.

BINDER STRUCTURE (read before judging binder coverage). ``authDecision`` reads
all four binders. The effective identifier is ``effectiveName suppliedName
recoveredName`` — present iff ``suppliedName`` is present, OR ``suppliedName`` is
absent and ``recoveredName`` is present (the fallback recovery). The reject
witnesses vary all four: ``suppliedName`` over ``{none, some 7}``,
``recoveredName`` over ``{none, some 5}`` (one rival is refuted through the
FALLBACK-recovery path, ``suppliedName = none`` with ``recoveredName = some 5``),
``password`` over ``{none, some 3, some 2}``, and ``backendOutcome`` over
``{some 9, some 5, none}`` — including the ABSENT-outcome column, which is the
only place ``weak-work-only-when-located`` differs from the frozen behaviour and
which two rivals defend. No binder is pinned across the battery.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS here. The nagini sibling holds
    ``self.lookups`` / ``self.verifications`` at FULL heap permission the impl
    must WRITE (the cost counters) and reasons about their preservation. Lean and
    Velvet are referentially transparent: there is no heap, no aliasing, no
    fractional-permission system. The four inputs are read-only value binders
    (none ``mut``); the frame obligation is discharged by pinning the exact
    post-state (``out = authDecision …``). Nagini itself records the class as
    inapplicable here (its credential inputs are pass-by-value ``Optional[int]``
    with no ``Acc(.,1/2)``). Not fabricated (porting map: vacuous here).
  * UNGROUNDED-ORACLE ECHO — N/A. There is no ``axiom`` (the ``axioms`` region is
    empty); the downstream lookup/verify chain is folded into the FREE INPUT
    ``backendOutcome`` and the guard decision is modeled DEEPLY as a total
    function of the four inputs. The principal facet is pinned to
    ``backendOutcome`` directly (a transparent input), so there is no answer-key
    to echo — the positives are honest cheapest-reshape controls.
  * COST / COUNTER attacks — SPLIT: one IS expressible here, one is not.
    The nagini surface carries TWO numeric cost counters (lookups,
    verifications) with exact per-path Old+1 clauses. THIS carrier folds all
    downstream cost into a SINGLE boolean observable ``queried`` (did control
    enter the expensive path at all — ``assertNumQueries(0)`` ⇔
    ``queried = false``, mapping.md §2).
      - The TIMING LEAK (nagini uniq-verify-only-on-recognised) DOES have a
        counterpart, contrary to an earlier reading of this carrier: the
        recognised-vs-declined sub-branch is observable through the free input
        ``backendOutcome``, so "spend the work only on the recognised path" is
        expressible as ``queried := backendOutcome.isSome`` — no numeric counter
        needed. Ported as ``weak-work-only-when-located`` (witness at
        backendOutcome = none, machine-checked to discriminate).
      - The MULTIPLICITY near-miss (nagini uniq-double-lookup) has NO
        counterpart: a boolean cannot count. Performing the work twice yields
        ``true || true = true`` — the SAME ``AuthOutcome`` as gold, so such a
        rival is definitionally equal on this carrier and VERIFIES (confirmed by
        a real build). It is genuinely inexpressible, not merely hard; writing
        it as a reject case would be a vacuous case that could never be
        refuted. Carrier narrowing, demonstrated rather than asserted.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no
    loop and no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
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

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so
each reject rival reaches it through Velvet's own tester machinery:
``authGuardTester suppliedName recoveredName password backendOutcome = false``
says the extracted program's observable violates the postcondition at that
concrete input. Checked in a file whose ``prove_correct`` block has been
stripped, so no tactic script can mask the verdict. The carriers are
``Option Nat`` with decidable equality, so every witness closes by ``decide``.
Each reject witness below was run against BOTH the rival (exit 0) and the frozen
solution (exit 1) with two real builds and was SEEN to discriminate.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the unchanged
downstream chain is a directive-7 free input ``backendOutcome`` and the guard is
modeled deeply — no consumed oracle). The gate ignores ``AXIOM_TESTS``
regardless.
"""
from pathlib import Path

INSTANCE = "django__django-11451"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor (lies wholly inside the single `-- impl-start` /
# ---- `-- impl-end` region and is unique in Solution.lean; both facts asserted
# ---- at load by _swap). --------------------------------------------------
_GOLD_IMPL = (
    "    let effective := effectiveName suppliedName recoveredName\n"
    "    if effective.isNone || password.isNone then\n"
    "      return { queried := false, principal := none }\n"
    "    else\n"
    "      return { queried := true, principal := backendOutcome }"
)

assert _GOLD_IMPL in _BASE, "frozen impl region drifted; update _GOLD_IMPL"

# ---- proof-body anchor. A `prove_correct` tactic body is elided from the
# ---- consumer spec view, so a positive case may retune the tactic script
# ---- without touching the spec statement or dropping the obligation. Unique
# ---- in file.
_GOLD_PROOF = (
    "prove_correct authGuard by\n"
    "  loom_solve <;> simp_all [authDecision, effectiveName]"
)

assert _GOLD_PROOF in _BASE, "frozen proof body drifted; update _GOLD_PROOF"


def _impl(body):
    """Full Solution.lean variant with ONLY the impl-region body replaced (the
    frozen proof kept as-is)."""
    return _swap(_BASE, _GOLD_IMPL, body)


def _impl_proof(body, proof):
    """Variant replacing BOTH the impl body and the `prove_correct` tactic body
    (the elided proof region — the spec statement is untouched, so same_spec
    still holds and the obligation survives byte-identical)."""
    return _swap(_impl(body), _GOLD_PROOF, proof)


# ---- witness preamble. Reaches the method contract through Velvet's tester
# ---- machinery; checked in a file whose `prove_correct` block is stripped by
# ---- the gate. `authGuardTester … = false` says the extracted program's
# ---- observable violates the postcondition at that input. No
# ---- `axiom`/`sorry`/`native_decide`; the frozen solution rejects each witness.
def _tester(call):
    return (
        "extract_program_for authGuard\n"
        "prove_precondition_decidable_for authGuard\n"
        "prove_postcondition_decidable_for authGuard\n"
        "derive_tester_for authGuard\n\n"
        f"example : {call} = false := by\n  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else the post-image is SPEC-TOO-STRONG. Each keeps the
    # byte-identical one-clause obligation and only reshapes the executable
    # surface (and, for the branch-restructure, the elided proof body). Both
    # verified out-of-band with real builds.
    # =====================================================================
    {
        "id": "pos-control-single-return",
        "kind": "soundness",
        "expect": "verify",
        # Single-exit reshape: compute the whole outcome into one typed local via
        # an `if`-expression, then return it once — instead of the gold's two
        # early returns. Observationally identical, so the single clause still
        # discharges under the FROZEN proof.
        "module": _impl(
            "    let effective := effectiveName suppliedName recoveredName\n"
            "    let out := if effective.isNone || password.isNone then\n"
            "        ({ queried := false, principal := none } : AuthOutcome)\n"
            "      else\n"
            "        ({ queried := true, principal := backendOutcome } : AuthOutcome)\n"
            "    return out"),
        "rationale": (
            "a correct single-exit reshape: build the whole outcome into one "
            "typed local through an `if`-expression and return it once, rather "
            "than the gold's two early returns. The final outcome equals "
            "`authDecision …` on every input, so the one clause still discharges "
            "under the frozen `loom_solve` script; if it failed to verify the "
            "spec would be SPEC-TOO-STRONG on impl shape. (Sibling: "
            "pos-control-single-return.)"),
    },
    {
        "id": "pos-control-merge-branch",
        "kind": "soundness",
        "expect": "verify",
        # Branch restructure: replace the absent-OR guard with the equivalent
        # both-present condition (`isSome && isSome`) and SWAP the two arms — the
        # De Morgan dual of the gold shape. Behaviourally identical; needs a
        # proof that case-splits the reshaped condition (the elided proof body is
        # retuned, the spec statement untouched).
        "module": _impl_proof(
            "    let effective := effectiveName suppliedName recoveredName\n"
            "    if effective.isSome && password.isSome then\n"
            "      return { queried := true, principal := backendOutcome }\n"
            "    else\n"
            "      return { queried := false, principal := none }",
            "prove_correct authGuard by\n"
            "  loom_solve <;>\n"
            "    simp_all [authDecision, effectiveName] <;>\n"
            "    (cases suppliedName <;> cases recoveredName <;> cases password "
            "<;> simp_all)"),
        "rationale": (
            "the merge-branch analogue: state the proceed guard as its De Morgan "
            "dual `effective.isSome && password.isSome` and swap the two arms. "
            "Both credentials present ⇒ proceed with the located outcome; "
            "otherwise short-circuit — exactly `authDecision …`. The reshaped "
            "condition needs a case-split, so the elided proof body is retuned "
            "(the `ensures` statement is byte-identical, so same_spec holds and "
            "the obligation survives). If a faithful correct restructure could "
            "not verify the spec would be SPEC-TOO-STRONG. (Sibling: "
            "pos-control-merge-branch.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — no `require` clause exists, so the usual "a normal input
    # satisfies the precondition" probe is vacuous (nothing could exclude the
    # F2P-shaped input). Re-aimed at the residual admissibility risk on a total
    # domain: that the post-image is DEGENERATE / trivially met. This case
    # discharges an in-region `assert` pinning BOTH F2P-shaped corners as
    # NON-DEGENERATE: the both-present corner (a genuine proceed — `queried` flips
    # to `true` and the located principal is handed back) and the absent corner (a
    # genuine short-circuit — `queried = false`, no principal). The surrounding
    # impl and the frozen proof are kept verbatim so the method's own obligation
    # still discharges; the assert is LIVE (a false claim about the same points
    # leaves an unsolved goal — confirmed out-of-band).
    # =====================================================================
    {
        "id": "admiss-both-corners-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    assert (with_name_prefix `adm\n"
            "      (authDecision (some 7) none (some 3) (some 9)\n"
            "        = { queried := true, principal := some 9 }\n"
            "       ∧ authDecision none none (some 3) (some 9)\n"
            "        = { queried := false, principal := none }))\n"
            "    let effective := effectiveName suppliedName recoveredName\n"
            "    if effective.isNone || password.isNone then\n"
            "      return { queried := false, principal := none }\n"
            "    else\n"
            "      return { queried := true, principal := backendOutcome }"),
        "rationale": (
            "the modeled behaviour is non-degenerate at BOTH F2P corners: with an "
            "effective identifier and a secret both present the routine genuinely "
            "PROCEEDS (`queried = true`, principal = the located `backendOutcome`), "
            "and with the identifier absent it genuinely SHORT-CIRCUITS "
            "(`queried = false`, no principal). The in-region assert must discharge "
            "(else the post-image would be degenerate / trivially met at the "
            "points that matter); the impl and frozen proof are kept verbatim so "
            "`out = authDecision …` still discharges too. (Sibling: "
            "admiss-fresh-checker, re-aimed from the fresh-Checker precondition "
            "witness — this carrier has no `require`.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Witnesses vary all four
    # binders (see BINDER STRUCTURE above).
    # =====================================================================
    {
        "id": "weak-no-guard-leak",
        "kind": "uniqueness",
        "expect": "reject",
        # THE BUG (== the prepatch skeleton): drop the admissibility short-circuit
        # entirely and ALWAYS proceed into the expensive downstream path. Attacks
        # the F-queried facet on the fully-absent sub-domain.
        "module": _impl(
            "    let _effective := effectiveName suppliedName recoveredName\n"
            "    return { queried := true, principal := backendOutcome }"),
        "refinement": (
            "this IS the pre-change behaviour: with no early short-circuit the "
            "routine always enters the expensive downstream path — issuing the "
            "store lookup and running the credential-strength computation — even "
            "when neither credential is present. The failing test drives the "
            "front entry with incomplete credentials and asserts that NO database "
            "query is issued and the password hasher is NOT run "
            "(`assertNumQueries(0)` and the counting-hasher's call count stays 0). "
            "The unguarded body makes the query (and the hasher run), so those "
            "assertions fail and it does NOT resolve. This is the exact defect the "
            "fix corrects."),
        "rationale": (
            "REJECT from F-queried: on the fully-absent input the rival returns "
            "`queried = true` where `authDecision …` requires `queried = false` "
            "(and `principal = none`, but the rival also hands back "
            "`backendOutcome`). If it verified the spec would admit the pre-change "
            "bug ⇒ SPEC-TOO-WEAK. Refuted at suppliedName=none, recoveredName=none, "
            "password=none, backendOutcome=some 9 (both credentials absent). "
            "(Sibling: uniq-no-guard-leak.)"),
        "witness": _tester("authGuardTester none none none (some 9)"),
    },
    {
        "id": "weak-guard-identifier-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: guard only the ABSENT-identifier half, omitting the
        # absent-secret half. When the identifier is present but the secret is
        # absent it falls through and proceeds. Attacks F-queried on the
        # secret-absent sub-domain.
        "module": _impl(
            "    let effective := effectiveName suppliedName recoveredName\n"
            "    if effective.isNone then\n"
            "      return { queried := false, principal := none }\n"
            "    else\n"
            "      return { queried := true, principal := backendOutcome }"),
        "refinement": (
            "guards only an absent identifier, omitting the absent-secret half of "
            "the fix. Its faithful real patch still enters the expensive path when "
            "the identifier is present but the secret is absent; the failing "
            "test's subcase supplying only the identifier (secret absent) then "
            "issues a query and runs the hasher, failing `assertNumQueries(0)` and "
            "the hasher-call assertion, so it does NOT resolve."),
        "rationale": (
            "REJECT from F-queried on the secret-absent sub-domain: with the "
            "identifier present and the secret absent the rival returns "
            "`queried = true` where `authDecision …` requires `queried = false`. "
            "Refuted at suppliedName=some 7, recoveredName=none, password=none, "
            "backendOutcome=some 9 (identifier present, secret absent). "
            "(Sibling: uniq-guard-identifier-only.)"),
        "witness": _tester("authGuardTester (some 7) none none (some 9)"),
    },
    {
        "id": "weak-guard-secret-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Mirror partial-domain: guard only the ABSENT-secret half, omitting the
        # absent-identifier half. When the secret is present but the effective
        # identifier is absent it falls through and proceeds. Attacks F-queried on
        # the identifier-absent sub-domain.
        "module": _impl(
            "    let _effective := effectiveName suppliedName recoveredName\n"
            "    if password.isNone then\n"
            "      return { queried := false, principal := none }\n"
            "    else\n"
            "      return { queried := true, principal := backendOutcome }"),
        "refinement": (
            "the mirror partial guard: guards only an absent secret, omitting the "
            "absent-identifier half. Its faithful real patch still enters the "
            "expensive path when the secret is present but the identifier is "
            "absent (even after the fallback recovery); the failing test's subcase "
            "supplying only the secret then issues a query "
            "(`… WHERE username IS NULL`) and runs the hasher, failing "
            "`assertNumQueries(0)` and the hasher assertion, so it does NOT "
            "resolve."),
        "rationale": (
            "REJECT from F-queried on the identifier-absent sub-domain: with the "
            "secret present and the effective identifier absent the rival returns "
            "`queried = true` where `authDecision …` requires `queried = false`. "
            "Refuted at suppliedName=none, recoveredName=none, password=some 3, "
            "backendOutcome=some 9 (secret present, identifier absent). "
            "(Sibling: uniq-guard-secret-only.)"),
        "witness": _tester("authGuardTester none none (some 3) (some 9)"),
    },
    {
        "id": "weak-drop-located-principal",
        "kind": "uniqueness",
        "expect": "reject",
        # Value-level (F-principal): guards correctly (F-queried holds), but on
        # the proceed path hands back `none` instead of the located
        # `backendOutcome`. Isolates the principal facet on the both-present
        # sub-domain; refuted through the FALLBACK-recovery identifier path.
        "module": _impl(
            "    let effective := effectiveName suppliedName recoveredName\n"
            "    if effective.isNone || password.isNone then\n"
            "      return { queried := false, principal := none }\n"
            "    else\n"
            "      return { queried := true, principal := none }"),
        "refinement": (
            "guards correctly but DROPS the located principal on the proceed path "
            "(returns nothing even when the downstream chain located and validated "
            "a principal). Its faithful real patch would return `None` on a "
            "successful lookup+verify, so a genuine authentication would be "
            "reported as a failure; the authenticate-identity tests observe the "
            "returned principal and would see `None` where a user is expected, so "
            "it does NOT resolve."),
        "rationale": (
            "REJECT from F-principal on the both-present sub-domain: with both "
            "credentials present `authDecision …` pins `principal = backendOutcome` "
            "but the rival returns `principal = none`, which differs whenever "
            "`backendOutcome ≠ none`. Refuted at suppliedName=none, "
            "recoveredName=some 5, password=some 3, backendOutcome=some 9 — the "
            "effective identifier is the RECOVERED one (fallback path), a "
            "sub-domain no other reject witness exercises. (Sibling: "
            "uniq-wrong-identity, re-expressed: the located principal is the free "
            "input `backendOutcome`, so the wrong-identity attack becomes handing "
            "back the wrong principal.)"),
        "witness": _tester("authGuardTester none (some 5) (some 3) (some 9)"),
    },
    {
        "id": "weak-fabricate-principal",
        "kind": "uniqueness",
        "expect": "reject",
        # Value-level (F-principal), distinct direction: guards correctly, but on
        # the proceed path FABRICATES a fixed principal (`some 0`) instead of the
        # located `backendOutcome`. Refuted at a point where backendOutcome ≠
        # some 0 — a different distinguishing point from weak-drop-located-
        # principal (which is refuted only where backendOutcome is present).
        "module": _impl(
            "    let effective := effectiveName suppliedName recoveredName\n"
            "    if effective.isNone || password.isNone then\n"
            "      return { queried := false, principal := none }\n"
            "    else\n"
            "      return { queried := true, principal := some 0 }"),
        "refinement": (
            "guards correctly but FABRICATES a fixed principal on the proceed path "
            "regardless of what the downstream chain located/validated. Its "
            "faithful real patch would return a fixed user object rather than the "
            "one the lookup+credential check produced — authenticating as the "
            "wrong principal (or authenticating where the secret does not verify). "
            "The authenticate-identity and wrong-secret tests observe the returned "
            "principal and would see the fabricated one, so it does NOT resolve."),
        "rationale": (
            "REJECT from F-principal on the both-present sub-domain: with both "
            "credentials present `authDecision …` pins `principal = backendOutcome` "
            "but the rival returns the constant `some 0`, which differs whenever "
            "`backendOutcome ≠ some 0`. Refuted at suppliedName=some 7, "
            "recoveredName=none, password=some 2, backendOutcome=some 5 (5 ≠ 0) — "
            "a DIFFERENT distinguishing point from weak-drop-located-principal "
            "(refuted only where backendOutcome is present), so the passthrough is "
            "attacked from two independent directions: the located principal must "
            "be handed back VERBATIM, not merely be non-none. (Sibling: "
            "uniq-skip-secret-check, re-expressed: the secret check is folded into "
            "`backendOutcome`, so a body ignoring it returns a principal not equal "
            "to the chain's outcome.)"),
        "witness": _tester("authGuardTester (some 7) none (some 2) (some 5)"),
    },
    {
        "id": "weak-work-only-when-located",
        "kind": "uniqueness",
        "expect": "reject",
        # F-queried on the sub-domain the other rivals leave unattacked: guards
        # correctly and passes the principal through verbatim, but makes the
        # `queried` observable TRACK the downstream outcome — the expensive work
        # is reported as performed only when a principal came back. Refuted at a
        # both-present input with `backendOutcome = none`, the only point where
        # this and gold differ, and the ONLY reject witness in the battery at
        # `backendOutcome = none`.
        "module": _impl(
            "    let effective := effectiveName suppliedName recoveredName\n"
            "    if effective.isNone || password.isNone then\n"
            "      return { queried := false, principal := none }\n"
            "    else\n"
            "      return { queried := backendOutcome.isSome, principal := backendOutcome }"),
        "refinement": (
            "makes the expensive downstream work CONDITIONAL on that work having "
            "yielded a principal — a body that only spends the credential-strength "
            "computation when the identifier lookup succeeded, and skips it "
            "otherwise. Its faithful real patch does strictly LESS work on the "
            "declined path than on the accepted one, so the two paths become "
            "distinguishable by how long the entry routine takes: a caller can "
            "tell a known identifier from an unknown one without any credential. "
            "A currently-passing test pins the credential-strength computation to "
            "run the SAME number of times whether or not the identifier is known "
            "(`Hasher is run once regardless of whether the user exists. Refs "
            "#20760.`); with the work skipped on the declined path that count "
            "drops to 0 and the assertion fails, so it does NOT resolve — it "
            "regresses a P2P while leaving the F2P intact."),
        "rationale": (
            "REJECT from F-queried on the both-present + NOTHING-LOCATED "
            "sub-domain: `authDecision …` pins `queried = true` whenever both "
            "credentials are present, unconditionally on what the chain returns, "
            "but the rival returns `queried = backendOutcome.isSome`, which is "
            "`false` when the chain locates nothing. The two agree everywhere "
            "`backendOutcome` is present, so this is exactly the near-miss the "
            "other four rivals cannot reach: they all pin `backendOutcome` to a "
            "PRESENT value, leaving the absent-outcome column of F-queried "
            "undefended. Refuted at suppliedName=some 7, recoveredName=none, "
            "password=some 3, backendOutcome=none. (Sibling: "
            "uniq-verify-only-on-recognised — the nagini timing leak, which DOES "
            "have a counterpart here: the recognised-vs-declined sub-branch is "
            "observable through the free input `backendOutcome`, so the leak is "
            "expressible as `queried` tracking it, without needing a numeric "
            "counter.)"),
        "witness": _tester("authGuardTester (some 7) none (some 3) none"),
    },
    {
        "id": "weak-never-proceed",
        "kind": "uniqueness",
        "expect": "reject",
        # The OVER-correction, and the polar opposite of weak-no-guard-leak:
        # short-circuit ALWAYS, never performing the downstream work at all.
        # Pins the `true` half of F-queried, which no other rival defends — every
        # other rival agrees with gold on the both-present proceed decision.
        "module": _impl(
            "    let _effective := effectiveName suppliedName recoveredName\n"
            "    return { queried := false, principal := none }"),
        "refinement": (
            "over-corrects the guard into an unconditional short-circuit: the "
            "routine never performs the downstream work and never hands back a "
            "principal, for ANY input. Its faithful real patch declines every "
            "request, so no credential pair authenticates at all — the whole body "
            "of currently-passing authentication tests (a valid identifier plus "
            "the matching secret is expected to authenticate, and the permission "
            "tests need an authenticated principal to query) breaks. It satisfies "
            "the incomplete-credentials assertions the fix targets while "
            "destroying the behaviour around them, so it does NOT resolve."),
        "rationale": (
            "REJECT from F-queried on the both-present sub-domain, in the "
            "direction OPPOSITE to weak-no-guard-leak: `authDecision …` pins "
            "`queried = true` (and `principal = backendOutcome`) when both "
            "credentials are present, but the rival returns `queried = false, "
            "principal = none` everywhere. Without this case the battery only "
            "ever tests that the spec forbids proceeding TOO MUCH — a spec that "
            "demanded `queried = false` unconditionally would pass every other "
            "reject case, so the `true` half of the short-circuit is what this "
            "pins. Refuted at suppliedName=some 7, recoveredName=none, "
            "password=some 3, backendOutcome=none — the same absent-outcome "
            "column, where the wrongness is in the `queried` flag alone. "
            "(No nagini sibling: its counter surface made an all-short-circuit "
            "body fail clause (2) trivially; here it needs stating.)"),
        "witness": _tester("authGuardTester (some 7) none (some 3) none"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 10 SPEC cases (2 soundness
# positives, 1 admissibility, 6 uniqueness rivals) plus a two-case AXIOM lane,
# contracting `authenticate(self, identifier, secret, fallback_identifier)` over
# a permission-bearing heap object (`self.lookups` / `self.verifications`, two
# NUMERIC cost counters written by the impl) plus two `@Pure @ContractOnly`
# axioms `directory_recognises` / `secret_verifies`. THIS bundle models a
# NARROWER, more TRANSPARENT surface: `authGuard` folds all downstream cost into a
# SINGLE boolean observable `queried` (did control enter the expensive path —
# `assertNumQueries(0)` ⇔ `queried = false`, mapping.md §2), folds the unchanged
# lookup/verify chain into the FREE INPUT `backendOutcome`, and models the guard
# decision DEEPLY as the total function `authDecision`. Its whole postcondition is
# `out = authDecision suppliedName recoveredName password backendOutcome`, with
# two attackable facets (F-queried, F-principal). Every sibling case is accounted
# for below.
#
#   sibling case (nagini)            -> here
#   -----------------------------------------------------------------------
#   pos-control-merge-branch         -> pos-control-merge-branch          PORTED
#   pos-control-single-return        -> pos-control-single-return         PORTED
#   admiss-fresh-checker             -> admiss-both-corners-nondegenerate  RE-AIMED
#   uniq-no-guard-leak               -> weak-no-guard-leak                PORTED (central)
#   uniq-guard-identifier-only       -> weak-guard-identifier-only        PORTED
#   uniq-guard-secret-only           -> weak-guard-secret-only            PORTED
#   uniq-wrong-identity              -> weak-drop-located-principal       RE-EXPRESSED
#   uniq-skip-secret-check           -> weak-fabricate-principal          RE-EXPRESSED
#   uniq-verify-only-on-recognised   -> weak-work-only-when-located       PORTED (re-derived)
#   uniq-double-lookup               -> (none)                            NO COUNTERPART
#   (no sibling)                     -> weak-never-proceed                ADDED (over-correction)
#   AXIOM_TESTS (2)                  -> (none)                            DROPPED (G-AX)
#
# PORTED (positives): the merge-branch positive (collapse the nested branches into
#   one combined condition) and the single-return positive (accumulate into one
#   local, return once) port directly — only the carrier changes from a mutated
#   `self` + returned Optional[int] to a returned `AuthOutcome`. The single-return
#   reshape verifies under the FROZEN proof; the merge-branch restructure states
#   the guard as its De Morgan dual and needs a case-split, so its ELIDED proof
#   body is retuned (spec statement byte-identical, obligation preserved). Both
#   verified out-of-band with real builds.
# RE-AIMED (admiss-fresh-checker -> admiss-both-corners-nondegenerate): the nagini
#   control constructs a fresh Checker and asserts the function's `Requires`
#   (Acc on both counters, both >= 0) holds. This carrier has NO `require` clause,
#   so that probe is vacuous; it is re-aimed at the residual total-domain risk (a
#   degenerate / trivially-met post-image) by a live in-region assert that BOTH
#   F2P corners are non-degenerate — a genuine proceed (queried flips true, the
#   located principal is handed back) and a genuine short-circuit (queried false,
#   no principal). loom_solve discharges the assert VC; impl and frozen proof kept
#   verbatim.
# PORTED (weak-no-guard-leak + the two partial guards): the central prepatch bug
#   (drop the short-circuit) and the two partial-domain guards (identifier-only /
#   secret-only) port directly against the F-queried facet — the single boolean
#   `queried` stands in for both nagini counters at once, and the three rivals hit
#   the fully-absent, secret-absent, and identifier-absent sub-domains
#   respectively. Each carries its nagini refinement (unguarded / half-guarded
#   real patch fails `assertNumQueries(0)` + the hasher-call assertion).
# RE-EXPRESSED (uniq-wrong-identity -> weak-drop-located-principal;
#   uniq-skip-secret-check -> weak-fabricate-principal): on nagini the located
#   account is `eff` and the wrong-identity attack returns `eff + 1`, while
#   skip-secret returns the account without consulting `secret_verifies`. On this
#   carrier the located+validated principal IS the free input `backendOutcome`
#   (the lookup/verify chain is unchanged, mapping.md §3), so both attacks become
#   "hand back a principal ≠ backendOutcome": drop it to `none`
#   (weak-drop-located-principal) and fabricate a constant `some 0`
#   (weak-fabricate-principal). The two probe DIFFERENT distinguishing points
#   (backendOutcome present vs backendOutcome ≠ some 0), attacking the passthrough
#   from two independent directions.
# PORTED, re-derived (uniq-verify-only-on-recognised -> weak-work-only-when-located):
#   the nagini timing leak leaves `verifications` at Old on the unrecognised path.
#   An earlier reading of this carrier judged it inexpressible for want of a
#   numeric counter; that was wrong. The recognised-vs-declined sub-branch IS
#   observable here — it is exactly whether the free input `backendOutcome` is
#   present — so the leak is expressible against the BOOLEAN observable as
#   `queried := backendOutcome.isSome`: the work is reported as performed only
#   when the chain located something. It differs from `authDecision` precisely on
#   the both-present + nothing-located inputs, and is refuted at
#   (some 7, none, some 3, none) by a witness confirmed to elaborate against the
#   rival and to FAIL on the frozen solution. This also closes a real coverage
#   gap: every other reject witness pins `backendOutcome` to a PRESENT value, so
#   the absent-outcome column of F-queried was undefended.
# ADDED, no sibling (weak-never-proceed): the polar opposite of
#   weak-no-guard-leak — short-circuit unconditionally, never proceeding. Every
#   other rival agrees with gold that both-present ⇒ proceed, so without this case
#   a spec demanding `queried = false` everywhere would pass the whole reject
#   lane; this pins the `true` half of F-queried. On nagini an all-short-circuit
#   body failed the numeric clause (2) trivially, so the sibling never needed to
#   state it.
# NO COUNTERPART (uniq-double-lookup): the multiplicity near-miss makes `lookups`
#   Old+2. A BOOLEAN cannot count: performing the work twice gives
#   `true || true = true`, the SAME `AuthOutcome` as gold, so the rival is
#   definitionally equal to the frozen impl on this carrier and VERIFIES —
#   confirmed with a real build (exit 0). It is therefore genuinely
#   inexpressible, not merely hard: shipping it as a reject case would be a
#   vacuous case admitting a wrong impl. Omitted because the carrier collapses
#   the distinction, demonstrated rather than asserted.
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job and this bundle declares no
#   axiom (the unchanged lookup/verify chain is a directive-7 free input
#   `backendOutcome`; the guard is modeled deeply). Nothing to probe here; the
#   gate ignores AXIOM_TESTS regardless.
#
# FRAME / PERMISSION-MUTATION: VACUOUS. Referentially-transparent backend — no
#   heap, no aliasing, no fractional permission; the four inputs are read-only
#   value binders (none `mut`) and the frame obligation is discharged by pinning
#   the exact post-state. The nagini sibling itself records this class as
#   inapplicable (its credential inputs are pass-by-value scalars with no
#   `Acc(.,1/2)`). No substitute fabricated.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
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
#
# BINDER / CLAUSE / POINT COVERAGE. Both facets of the single `ensures` clause are
#   attacked: F-queried by weak-no-guard-leak / weak-guard-identifier-only /
#   weak-guard-secret-only / weak-work-only-when-located / weak-never-proceed, and
#   F-principal by weak-drop-located-principal / weak-fabricate-principal; both are
#   defended by the two positive controls and the admissibility case. The seven
#   reject witnesses probe six DISTINCT inputs:
#     supplied=none,   recovered=none,   pw=none,   backend=some 9   weak-no-guard-leak
#     supplied=some 7, recovered=none,   pw=none,   backend=some 9   weak-guard-identifier-only
#     supplied=none,   recovered=none,   pw=some 3, backend=some 9   weak-guard-secret-only
#     supplied=none,   recovered=some 5, pw=some 3, backend=some 9   weak-drop-located-principal
#     supplied=some 7, recovered=none,   pw=some 2, backend=some 5   weak-fabricate-principal
#     supplied=some 7, recovered=none,   pw=some 3, backend=none     weak-work-only-when-located
#     supplied=some 7, recovered=none,   pw=some 3, backend=none     weak-never-proceed
#   so `suppliedName` is varied over {none, some 7}, `recoveredName` over
#   {none, some 5} (weak-drop-located-principal exercises the FALLBACK-recovery
#   path: supplied absent, recovered present), `password` over {none, some 3,
#   some 2}, and `backendOutcome` over {some 9, some 5, NONE}. The variation is
#   MEANINGFUL rather than two spellings of a point: some 5 ≠ some 0 is what makes
#   the fabricated constant observably wrong, and `backendOutcome = none` is the
#   only column on which weak-work-only-when-located differs from gold at all —
#   the last two rivals share an input but are refuted through different facets of
#   the outcome at it (the `queried` flag tracking the outcome vs. never being set).
#   No binder is pinned across the battery. Each witness was SEEN to discriminate:
#   it ELABORATES against the rival (exit 0) and FAILS against the frozen solution
#   (exit 1), confirmed with two real builds each, and each gold-side failure is a
#   SEMANTIC refutation (`decide` proves the tester proposition FALSE) rather than
#   an unfolding failure, missing identifier, or timeout.
AXIOM_TESTS = []
