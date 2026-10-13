"""properties.py — G-PBT falsification battery for django__django-16901 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves or adds a
ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_xorFallback``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND
the file elaborates with the obligation closed, no ``sorry``/``admit``/
``native_decide`` and no new ``axiom``/``theorem``); ``expect:"reject"`` passes
iff (in scope AND it does NOT verify AND the case's refutation ``witness`` holds
of the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled behavior; a single spec predicate over a single
input binder). A combined predicate is built from a list of per-operand truth
values ``cs`` and must be true exactly when an ODD number of the operands hold
(the meaning of an n-ary exclusive-or):

  problem_spec_xorFallback (cs : List Bool) (result : Bool) : Prop
    result = (countTrue cs % 2 == 1)        -- THE load-bearing (and only) clause

where ``countTrue cs`` is the number of operands whose condition holds. The
whole output is pinned to this single parity relation; nothing is left free.
There is NO opaque answer key to echo (the ``axioms`` region declares no
``opaque``/``axiom``; ``countTrue`` is a concrete front-recursive fold over the
input carrier), so the spec is fully grounded in the input (spec_guide directive
8) and ``decide`` settles it at any ground list.

BINDER STRUCTURE (read this before judging binder coverage). The postcondition
depends on EXACTLY ONE input binder — the operand list ``cs`` — through two
observable quantities of it: the PARITY of its true-count and (implicitly) the
count itself. The discriminating content of the fix lives entirely in ``cs``
whose true-count exceeds 2: for a true-count of 0/1/2 the parity relation
``count % 2 == 1`` coincides with the pre-patch "exactly one" test, so the spec
only separates a correct impl from the pre-patch one once the count can exceed 2
(an odd count of 3, 5, … must hold). The reject witnesses therefore live in that
sub-domain (true-counts 3 and 5), at the adjacent even boundary (a length>2 list
with true-count 2), and — for the two rivals that attack something other than the
count test — on the length-<=2 sub-domain and at a point where the list's LENGTH
parity and its TRUE-count parity disagree. Five witnesses at five distinct input
points, so the battery exercises the spec's dependence on the count/parity of
``cs`` rather than probing a single point.

WHAT EACH REJECT CASE PINS (one operator of the modeled behavior apiece, so no
single case's rejection has to carry the whole claim):

  weak-no-parity       the parity REDUCTION exists at all (pre-patch behavior)
  weak-mod3            the MODULUS is 2
  weak-invert-parity   the RESIDUE compared against is 1, not 0
  weak-or-connective   the two legs are joined by ``&&``, not ``||``
  weak-length-parity   the reduced quantity is the TRUE-count, not the length

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling holds the operand
    list at a half-permission (``Acc(list_pred(operands),1/2)``) and makes its
    MANDATORY frame-mutation rival WRITE back into it (``operands[0] =
    operands[0]``), which must be rejected for insufficient permission. Lean is
    referentially transparent: ``cs`` is an immutable value with no heap
    footprint, no ``mut`` binder over it, and no aliasing — there is no
    read-only carrier to overwrite and no store to reject. NOT fabricated (per
    the porting map this class is vacuous here); see the accounting block.

  * CONTROL-FLOW-EFFECT / NON-TERMINATION — VACUOUS. The nagini sibling carries
    a ``Requires(MustTerminate(2))`` obligation and a never-terminating-loop
    rival that VERIFIED under partial correctness, pinned by that obligation.
    Here the modeled function is a total ``for`` fold over a finite ``List Bool``
    (no ``while``, no recursion needing ``termination_by``); ``correct_xorFallback``
    is a total-correctness statement about a total function, so there is no
    partial-correctness hole and no non-terminating rival is expressible. NOT
    fabricated; see the accounting block.

  * UNGROUNDED-ORACLE ECHO — N/A: the post-image is a parity relation on the
    input's own true-count, not an axiomatized oracle; nothing to echo.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof script is tuned to the frozen
``Id.run do`` form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at a ``decide``-able concrete operand list; each was checked
(two real ``lake env lean`` builds) to ELABORATE against its rival and to FAIL
against the frozen solution (so it discriminates rather than asserting a
tautology). ``List Bool`` literals are ground and ``countTrue``/the impl compute,
so the snippets ``unfold`` the spec + impl and ``decide`` the concrete boolean
equality; against gold the same ``decide`` faces ``b = b`` and fails.

The gold-side failure is a SEMANTIC refutation, not a syntactic accident: Lean
reports ``Tactic `decide` proved that the proposition ... is false``, i.e. it
evaluated the frozen impl at that literal and found it DOES satisfy the spec
there. No witness fails on gold for a missing identifier, a type error, an
unfolding failure or a timeout — each witness is stated purely over
``problem_spec_xorFallback``/``implementation_xorFallback``/``countTrue``, all
three of which the frozen solution and every rival share, so both builds ask the
same question. None of the witnesses binds a hypothesis, so there is no
consistency probe to run and no risk of a refutation drawn from a contradiction.

AXIOM lane: EMPTY. meta.json ``axioms == []`` and ``deep_model_references == []``;
the changed op (the parity reduction) is integer arithmetic modeled DEEPLY with
native ``%``/``+``/``==``/``&&``/``||``, never axiomatized, so there is no
axiom-soundness obligation to probe here (that lane belongs to G-AX).
``AXIOM_TESTS`` is therefore empty.
"""
from pathlib import Path

INSTANCE = "django__django-16901"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The final conjunction line and the len-guarded rhs branch both lie wholly
# inside `-- impl-start`/`-- impl-end`; the parity-test line inside that branch.
_RET = "  return lhs && rhs"
_BRANCH = (
    "  if cs.length > 2 then\n"
    "    rhs := (rhsSum % 2 == 1)\n"
    "  else\n"
    "    rhs := (rhsSum == 1)\n"
)
_PARITY_LINE = "    rhs := (rhsSum % 2 == 1)\n"
_GUARD_LINE = "  if cs.length > 2 then\n"

# The two frozen proof bullets that discharge the len-guarded `split`, in frozen
# order (parity leg first, exactly-one leg second). A variant that COMPLEMENTS the
# branch guard swaps which leg `split` presents first, so exchanging these two
# bullets is the whole re-proof — no new lemma, no assumption token.
_PARITY_BULLET = (
    "  · rcases Nat.eq_zero_or_pos (countTrue cs) with h | h\n"
    "    · simp [h]\n"
    "    · simp [decide_eq_true h]\n"
)
_EXACT_BULLET = (
    "  · rename_i hlen\n"
    "    have h2 : countTrue cs ≤ 2 := by omega\n"
    "    interval_cases hc : countTrue cs <;> simp\n"
)

# The theorem-statement line + `:= by` boundary; an admissibility ground instance
# is inserted immediately AFTER this boundary (inside the tactic body / proof
# region), so the theorem STATEMENT stays byte-identical.
_STMT = (
    "    problem_spec_xorFallback cs (implementation_xorFallback cs) := by\n"
)

for _a in (_RET, _BRANCH, _PARITY_LINE, _GUARD_LINE, _STMT,
           _PARITY_BULLET, _EXACT_BULLET, _PARITY_BULLET + _EXACT_BULLET):
    assert _BASE.count(_a) == 1, f"anchor drifted from Solution.lean: {_a!r}"


def _witness(list_lit: str) -> str:
    """Refutation witness: the spec predicate is FALSE of the rival at a ground
    operand list. Checked where the frozen obligation is elided, so no tactic
    script can mask the verdict; `decide` settles the ground boolean equality."""
    return (
        f"example : ¬ problem_spec_xorFallback {list_lit}\n"
        f"    (implementation_xorFallback {list_lit}) := by\n"
        "  unfold problem_spec_xorFallback implementation_xorFallback\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness / admissibility) — MUST verify, else the
    # spec is SPEC-TOO-STRONG (or unsatisfiable at the F2P input). Each keeps the
    # `theorem correct_xorFallback` STATEMENT byte-identical.
    # =====================================================================
    {
        "id": "pos-commute-and",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different but behaviourally identical: the disjunction leg
        # and the count/parity leg are combined by a COMMUTED final conjunction
        # (`rhs && lhs` instead of `lhs && rhs`). `&&` is commutative on Bool, so
        # the value is identical on every input, and the frozen proof still closes
        # verbatim (verified with a real build) — no proof authoring, no helper
        # lemma, no assumption token.
        "module": _swap(_BASE, _RET, "  return rhs && lhs"),
        "rationale": (
            "correct reshape: the two legs of the combined predicate are joined by "
            "a COMMUTED conjunction (`rhs && lhs`). `&&` is commutative, so the "
            "result equals `lhs && rhs` on every input and thus satisfies the single "
            "clause `result = (countTrue cs % 2 == 1)`; a faithful correct impl MUST "
            "verify, else SPEC-TOO-STRONG. Proof: the frozen tactic script closes "
            "unchanged (the commuted conjunction is handled by the same rewrite/"
            "case split); statement byte-identical, no new axiom/lemma."
        ),
    },
    {
        "id": "admiss-f2p-ground",
        "kind": "admissibility",
        "expect": "verify",
        # The frozen theorem carries NO precondition hypothesis (`∀ cs` is
        # unguarded — the behavior is total), so nagini's precondition-admission
        # probe has no binder to attack. The honest analogue: discharge the spec
        # predicate at the F2P ground input (a 5-operand all-true list, the
        # instance's `Q^Q^Q^Q^Q` scenario, true-count 5 which is ODD so the
        # combined predicate must hold) inside the proof region, alongside the
        # frozen obligation. If that ground instance could not be discharged the
        # modeled behavior would be unsatisfiable at exactly the F2P input.
        "module": _swap(
            _BASE, _STMT,
            _STMT
            + "  have _ground : problem_spec_xorFallback [true, true, true, true, true]\n"
              "      (implementation_xorFallback [true, true, true, true, true]) := by\n"
              "    unfold problem_spec_xorFallback implementation_xorFallback\n"
              "    decide\n",
        ),
        "rationale": (
            "the obligation is discharged at the F2P-shaped ground input (a "
            "5-operand list whose true-count is 5, an ODD count, so the combined "
            "predicate must be true) by `decide`, then the frozen obligation is "
            "closed verbatim. Verifies (else the spec is unsatisfiable at the normal "
            "F2P input — the analogue of PRECOND-TOO-STRONG). Nothing is assumed: "
            "the theorem STATEMENT is byte-identical, the ground instance is a "
            "`have` inside the existing tactic body, and no new declaration/axiom/"
            "`sorry` is introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, so a verifying rival would be
    # a true verify-does-not-imply-resolve break, and (b) a machine-checked
    # refutation witness at a concrete operand list.
    # =====================================================================
    {
        "id": "weak-no-parity",
        "kind": "uniqueness",
        "expect": "reject",
        # PRE-PATCH behaviour (Solution_prepatch.lean): drop the parity reduction —
        # compare the raw true-count directly to one for EVERY operand count
        # ("exactly one true operand"). Correct on true-count 0/1/2, wrong the
        # moment the count exceeds 2.
        "module": _swap(_BASE, _BRANCH, "  rhs := (rhsSum == 1)\n"),
        "refinement": (
            "this IS the pre-patch fallback: the running sum is compared directly to "
            "one, so the combined predicate is 'exactly one operand true' for every "
            "operand count, with no parity reduction. Its faithful real patch is the "
            "unchanged repo, which on the F2P's 5-clause XOR selects the wrong rows "
            "(a row with 3 true operands is XOR-true — an odd count — but the "
            "exactly-one fallback rejects it). It fails the F2P test_filter_multiple "
            "— it does NOT resolve (the precise change the spec senses)."
        ),
        "rationale": (
            "REJECT from `result = (countTrue cs % 2 == 1)`: with the parity "
            "reduction dropped the rival returns `any || (rawcount == 1)`, which for "
            "a true-count of 3 is False while the spec demands True (3 is odd). "
            "PARTIAL-DOMAIN: correct on true-counts 0/1/2, wrong once the count "
            "exceeds 2. Refuted at true-count 3."
        ),
        "witness": _witness("[true, true, true]"),
    },
    {
        "id": "weak-mod3",
        "kind": "uniqueness",
        "expect": "reject",
        # Reduce modulo 3 instead of 2 for >2 operands. Agrees with parity on
        # true-counts 0/1/2 but diverges once the count's mod-3 value differs from
        # its parity — e.g. true-count 5 gives 5 % 3 == 2 ≠ 1 (False) while parity
        # demands True (5 is odd).
        "module": _swap(_BASE, _PARITY_LINE, "    rhs := (rhsSum % 3 == 1)\n"),
        "refinement": (
            "reducing modulo 3 is NOT the n-ary XOR semantics — XOR is true iff an "
            "ODD number of operands hold, i.e. remainder mod 2. A real patch using "
            "MOD(sum, 3) would, on the F2P's 5-clause XOR, mis-select rows: a "
            "5-true-operand row is XOR-true (odd) but 5 %% 3 == 2 != 1, so it is "
            "rejected. It fails the F2P — it does NOT resolve."
        ),
        "rationale": (
            "REJECT from `result = (countTrue cs % 2 == 1)`: for >2 operands the "
            "rival's test is `sum % 3 == 1`, but the spec requires `sum % 2 == 1`. "
            "At true-count 5 the rival gives 5 %% 3 == 2 (False) while the spec "
            "demands True. Refuted at true-count 5 — a point distinct from the "
            "no-parity rival's true-count 3, so the two witnesses probe different "
            "counts of `cs`."
        ),
        "witness": _witness("[true, true, true, true, true]"),
    },
    {
        "id": "weak-invert-parity",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS: keep the mod-2 reduction but INVERT the residue test
        # (`== 0` instead of `== 1`) for >2 operands — an EVEN-count predicate.
        # Agrees with parity nowhere on the >2 sub-domain but is refuted most
        # sharply at the even boundary a length>2 list can reach (true-count 2),
        # which the odd-count witnesses never probe.
        "module": _swap(_BASE, _PARITY_LINE, "    rhs := (rhsSum % 2 == 0)\n"),
        "refinement": (
            "testing `sum % 2 == 0` inverts the parity: it treats an EVEN number of "
            "true operands as a match. A real patch with the residue inverted would, "
            "on the F2P's XOR, select the complementary rows — a 2-true-operand row "
            "(even) would be reported true though n-ary XOR is false there, and a "
            "3-true-operand row (odd, XOR-true) reported false. It fails the F2P — it "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECT from `result = (countTrue cs % 2 == 1)`: for >2 operands the "
            "rival tests `sum % 2 == 0` (even) where the spec demands `sum % 2 == 1` "
            "(odd). At a length-3 list with true-count 2 the rival returns True "
            "(2 is even) while the spec demands False. Refuted at the EVEN boundary "
            "of the >2 sub-domain (true-count 2), a point neither odd-count witness "
            "reaches, so this near-miss carries its own distinguishing input."
        ),
        "witness": _witness("[true, true, false]"),
    },
    {
        "id": "weak-or-connective",
        "kind": "uniqueness",
        "expect": "reject",
        # WRONG CONNECTIVE: join the disjunction leg and the count/parity leg by
        # `||` instead of `&&`. Every previous rival keeps the conjunction and
        # perturbs the count test, so the final connective was the one operator in
        # the modeled behavior no witness constrained. Refuted at a true-count of 2
        # on a length-2 list — the `<=2` sub-domain the other three never enter,
        # since a disjunction that is true there drags the whole result true.
        "module": _swap(_BASE, _RET, "  return lhs || rhs"),
        "refinement": (
            "the combined predicate conjoins the disjunction leg with the "
            "count test; joining them by a DISJUNCTION instead makes the result "
            "true whenever ANY operand holds, so the count test stops "
            "constraining anything. A real patch that emitted the two legs under "
            "the wrong connective would, on the F2P's multi-clause XOR, select "
            "every row with at least one true operand — a 2-true-operand row "
            "would be reported true though n-ary XOR is false there. It fails "
            "the F2P — it does NOT resolve."
        ),
        "rationale": (
            "REJECT from `result = (countTrue cs % 2 == 1)`: the rival returns "
            "`any || counttest`, which at a length-2 list with true-count 2 is "
            "True (the disjunction holds) while the spec demands False (2 is "
            "even). Refuted on the length-<=2 sub-domain, which the three "
            "count-perturbing rivals never reach — this is the only case that "
            "pins the FINAL CONNECTIVE rather than the count test."
        ),
        "witness": _witness("[true, true]"),
    },
    {
        "id": "weak-length-parity",
        "kind": "uniqueness",
        "expect": "reject",
        # WRONG QUANTITY: take the parity of the OPERAND COUNT instead of the
        # TRUE-operand count. Coincides with the spec whenever every operand is
        # true, so all three earlier witnesses (whose lists are all-true, except
        # the invert-parity one) leave it largely unattacked; it diverges as soon
        # as the list length and its true-count differ in parity.
        "module": _swap(
            _BASE, _PARITY_LINE, "    rhs := (cs.length % 2 == 1)\n"),
        "refinement": (
            "the parity that matters is the parity of the number of operands "
            "whose condition HOLDS, not the parity of how many operands there "
            "are. A real patch that reduced the operand count rather than the "
            "sum of per-operand contributions would ignore the row entirely: on "
            "the F2P's 3-clause scenario every row of an odd-length clause list "
            "would be reported true whenever any operand holds, so a row with 2 "
            "true operands out of 3 is selected though n-ary XOR is false. It "
            "fails the F2P — it does NOT resolve."
        ),
        "rationale": (
            "REJECT from `result = (countTrue cs % 2 == 1)`: the rival tests "
            "`cs.length % 2 == 1`, a quantity of the list's SHAPE rather than of "
            "its contents, so it is constant as the true-count varies at fixed "
            "length. At the length-3 list `[false, true, true]` (true-count 2, "
            "EVEN) the rival returns True because the length 3 is odd, while the "
            "spec demands False. This is the only case that pins the spec to the "
            "TRUE-count rather than to any parity of the input."
        ),
        "witness": _witness("[false, true, true]"),
    },
    {
        "id": "pos-guard-complement",
        "kind": "soundness",
        "expect": "verify",
        # The sibling's OTHER reshape, landed rather than dropped: COMPLEMENT the
        # branch guard (`<= 2` with the legs exchanged) AND commute the final
        # conjunction. Semantically identical on every input. It does need the
        # frozen proof's two `split` bullets EXCHANGED — `split` now presents the
        # exactly-one leg first — but that is a mechanical reordering of existing
        # bullets, not a new lemma, so the case still authors no proof.
        "module": _swap(
            _swap(
                _swap(_BASE, _BRANCH,
                      "  if cs.length ≤ 2 then\n"
                      "    rhs := (rhsSum == 1)\n"
                      "  else\n"
                      "    rhs := (rhsSum % 2 == 1)\n"),
                _RET, "  return rhs && lhs"),
            _PARITY_BULLET + _EXACT_BULLET, _EXACT_BULLET + _PARITY_BULLET),
        "rationale": (
            "correct reshape, the STRONGER positive: the len guard is "
            "COMPLEMENTED (`≤ 2` with the two legs exchanged) and the final "
            "conjunction is COMMUTED, so both the branch structure and the "
            "operand order differ from the frozen impl while the value is "
            "identical on every input — it therefore satisfies "
            "`result = (countTrue cs % 2 == 1)` and MUST verify, else "
            "SPEC-TOO-STRONG. Because the complemented guard makes the frozen "
            "`split` present its two legs in the opposite order, the proof "
            "EXCHANGES the two existing bullets and changes nothing else: no new "
            "lemma, no new axiom/`sorry`, statement byte-identical. This closes "
            "the one reshape the branch-guard-preserving commute cannot reach — "
            "that the spec does not depend on the guard's polarity."
        ),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 1 MANDATORY frame-mutation, 1 non-termination, 3
# value/uniqueness rivals) plus an empty AXIOM lane. This bundle models the same
# single behavior (the parity-vs-exactly-one decision) over one input binder
# `cs : List Bool`; every sibling case is recorded below.
#
#   sibling case            -> here                    disposition
#   -----------------------------------------------------------------
#   pos-reorder-commute     -> pos-commute-and         PORTED (commute only)
#                           -> pos-guard-complement    PORTED IN FULL (guard
#                                                       complement + commute; the
#                                                       sibling's whole reshape)
#   admiss-reads            -> admiss-f2p-ground        RE-EXPRESSED (no precond;
#                                                       ground F2P instance)
#   frame-mut-write         -> (none)                  VACUOUS (no heap / no mut)
#   weak-nonterm            -> (none)                  VACUOUS (total for-fold)
#   weak-no-mod             -> weak-no-parity          PORTED
#   weak-eq-true            -> weak-no-parity          FOLDED (same impl here:
#                                                       `rawcount == 1` for all n)
#   weak-mod3               -> weak-mod3               PORTED
#   (new near-miss)         -> weak-invert-parity      ADDED (inverted residue,
#                                                       refuted at the even
#                                                       boundary the others miss)
#   (new connective probe)  -> weak-or-connective      ADDED (wrong final
#                                                       connective; the only case
#                                                       pinning `&&` vs `||`, and
#                                                       the only one refuted on
#                                                       the length-<=2 sub-domain)
#   (new quantity probe)    -> weak-length-parity      ADDED (parity of the LIST
#                                                       LENGTH, not of the
#                                                       true-count; pins WHICH
#                                                       quantity is reduced)
#   AXIOM_TESTS (0)         -> (none)                  DROPPED (G-AX's lane)
#
# PORTED (positive), two cases. pos-commute-and keeps the gold `for`-fold and the
#   len-guarded branch verbatim and only COMMUTES the final conjunction; `&&` is
#   commutative, the value is identical, and the frozen proof closes unchanged.
#   pos-guard-complement additionally COMPLEMENTS the branch guard (`≤ 2` with the
#   legs exchanged), which is the sibling's reshape in full. The complemented guard
#   makes the frozen `split` present its two legs in the opposite order, so the
#   proof EXCHANGES the frozen script's two existing bullets — a mechanical
#   reordering, no new lemma and no assumption token — and closes (verified with a
#   real build). Both are carried: the commute alone attests that the spec ignores
#   operand order, the guard complement that it ignores the guard's polarity.
# RE-EXPRESSED (admissibility): the sibling self-asserts, under a half-permission,
#   that an F2P-shaped read is admitted. This bundle's `correct_xorFallback` carries
#   NO precondition hypothesis (`∀ cs` unguarded — total behavior), so there is no
#   precondition to admit. The honest analogue discharges the spec at the F2P ground
#   input (5 all-true operands, odd count) inside the proof region alongside the
#   frozen obligation, confirming the behavior is satisfiable at exactly the F2P
#   input rather than only in the abstract.
# VACUOUS (frame-mutation): the sibling carries this MANDATORY because `operands`
#   is held at Acc(.,1/2) and a write must be rejected. Lean is referentially
#   transparent: `cs` is an immutable value with no aliasing, so there is no
#   read-only carrier to overwrite and no store for the spec to reject. Note the
#   precise reason — it is NOT that a write is inexpressible. `let mut shadow := cs;
#   shadow := shadow.set 0 true` type-checks fine, but it mutates a local COPY, so
#   the modeled function's value is unchanged and the variant VERIFIES (confirmed
#   with a real build). That is the correct outcome, not a hole: on this carrier a
#   write to the input is not observable in the result, so there is no wrong
#   behavior for a witness to refute and no rival to land. The obligation the
#   sibling's permission system discharges is discharged HERE by the type system,
#   before any spec is written. Not fabricated (porting map).
# VACUOUS (non-termination): the sibling's P1 witness is a never-exiting `while`
#   loop that verified under partial correctness, pinned by MustTerminate. Here the
#   impl is a total `for` fold over a finite `List Bool` — no `while`, no recursion
#   needing `termination_by` — and `correct_xorFallback` is a TOTAL-correctness
#   statement about a total function. Confirmed by build, not just argued: the
#   closest expressible rival, `partial def implementation_xorFallback cs :=
#   implementation_xorFallback cs`, does NOT verify — the obligation is stated of
#   the function's value, and with no reduction available the frozen script cannot
#   discharge it, so there is no vacuous pass to exhibit. This bundle is vanilla
#   Lean 4 with no partial-correctness option in scope; the known partial-semantics
#   hole is a VELVET matter, recorded in the corpus-wide termination-semantics finding (401 velvet
#   bundles; lean unaffected) and deliberately NOT re-reported here. Not fabricated.
# FOLDED (weak-eq-true): the sibling's second phrasing of the exactly-one bug is,
#   on this carrier, the SAME impl as weak-no-mod — dropping the parity branch
#   leaves `rawcount == 1` for every count, which is precisely weak-no-parity's
#   body. It needs no separate rival.
# ADDED (weak-invert-parity): a near-miss that keeps the mod-2 reduction but
#   inverts the residue test, refuted at the EVEN boundary (true-count 2 on a
#   length>2 list) that the two odd-count witnesses never reach — so the three
#   witnesses probe THREE distinct true-counts of `cs` (3, 5, 2), exercising the
#   spec's dependence on the count/parity of the single input binder.
#
#   The five witnesses probe FIVE distinct input points; across them the operand
#   list `cs` takes true-counts {3, 5, 2, 2, 2} at lengths {3, 5, 3, 2, 3},
#   spanning the odd sub-domain where parity separates from exactly-one, the even
#   boundary where the inverted-parity near-miss diverges, the length-<=2
#   sub-domain (where only the wrong-connective rival can be caught, since every
#   count-perturbing rival is CORRECT there), and a length/true-count parity
#   disagreement. pts = 5. Note that the last three points share a true-count of 2
#   yet are NOT three spellings of one point: they differ in length and in which
#   operator they falsify, and each is the only point in the battery at which its
#   own rival diverges from the spec (checked by exhaustive enumeration over all
#   lists up to length 6, then by two real builds apiece). The single load-bearing
#   binder `cs` is varied across those counts and lengths; there is no free binder
#   to leave pinned.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no axiom
# (the parity op is modeled deeply, not axiomatized), so there is nothing to probe
# and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
