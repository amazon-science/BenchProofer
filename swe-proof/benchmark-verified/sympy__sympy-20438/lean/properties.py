"""properties.py — G-PBT falsification battery for sympy__sympy-20438 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant sharing the FROZEN spec byte-for-byte (region surgery:
only text inside ``-- impl-start``/``-- impl-end`` — and, for a case that
legitimately re-proves, inside ``-- proof-start``/``-- proof-end`` — is changed,
so ``markers.same_spec`` holds and the single ``theorem correct_isSubset``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff the file
elaborates with the obligation closed (no ``sorry``/``admit``/``native_decide``,
no new ``axiom``/``theorem``); ``expect:"reject"`` passes iff it does NOT verify
AND the case's refutation ``witness`` holds of the rival while FAILING on the
frozen solution.

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``); that manifest is the design document, not a text
to translate. The nagini bundle contracts THREE functions over a
``List[int]``-plus-handle carrier: a per-element membership fold, a mutual-
containment equality, and an operand-kind routing guard. This Lean bundle models
ONE purely-functional core — the subset verdict of a finite product of finite
integer collections against a finite collection of integer tuples — over a
``List (List Int)`` carrier. That is carrier narrowing, not a thinner battery:
the two nagini functions with no counterpart here (the mutual-containment
equality and the routing guard) are not modeled by this bundle at all, so their
rivals have nothing to attack. See ``assessment`` for the full accounting.

DEFENDED SURFACE (one modeled behavior, one obligation).
``problem_spec_isSubset factors candidate result`` pins EXACTLY:

    result = some ((productSet factors).all (fun x => candidate.contains x))

A single top-level equation, but it carries TWO independent load-bearing
aspects, and the battery attacks both:

  * (D determinedness) the verdict must be ``some _`` — a *determined* answer.
    ``none`` denotes an absent/undetermined verdict, which is precisely the
    behavior the fix removes. Attacked by ``weak-undetermined`` and
    ``weak-affirmative-only``.
  * (V value) the determined boolean must be the conjunction of the per-tuple
    membership test over EVERY tuple of the enumerated product. Attacked by
    ``weak-constant-true``, ``weak-emptiness``, ``weak-drop-factor``,
    ``weak-drop-last-factor`` and ``weak-single-candidate``.

GROUNDING. The postcondition is GROUNDED in the inputs: it relates ``result`` to
a structural fold over ``productSet factors`` and ``candidate``, with no opaque
callee and no answer-key to echo. The bundle declares no ``opaque`` and consumes
no ``axiom`` (both the enumeration and the membership test are modeled deeply),
so the carrier is fully TRANSPARENT: every witness below states the spec
predicate at concrete list literals and closes by ``decide``. No witness binds
anything in its head, so there are no hypotheses whose joint satisfiability
could be in question (no ``witness-inconsistent`` risk). This mirrors nagini's
own note that its membership oracle is a grounded fold over the actual input
handles rather than an opaque answer key.

BINDER STRUCTURE. The spec predicate has TWO input binders, ``factors`` (the
product's list of factors) and ``candidate`` (the collection the product is
tested against). Both are load-bearing and both are VARIED across the reject
witnesses — six distinct ``factors`` values and six distinct ``candidate``
values, over seven distinct input pairs (``pts=7``; see the point-spread block at
the bottom, which records the EVALUATED spec and rival verdict at each point).
No binder is held at one value, so no rival that mishandled only one input could
slip through.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Two nagini cases
    (``frame-mut-psof``, ``frame-mut-fse``) reject a rival that writes to a
    read-only input, which its carrier detects on PERMISSION grounds. Lean is
    referentially transparent: the inputs are immutable values, there is no
    aliasing, no fractional permission and no read-only cell to overwrite, so
    the class collapses. No substitute probe is fabricated (porting map:
    vacuous here).

  * DIVERGENCE / NON-TERMINATION — KNOWN HOLE, not vacuous. Corrected by audit;
    the earlier reading ("a non-terminating implementation cannot be written at
    all") was measured FALSE and is retracted. The frozen solution sets no
    ``loom.semantics.termination`` option, and a rival may prefix the
    implementation with ``partial`` — which the variant scope permits (it adds
    no axiom, no ``sorry``, no new declaration and leaves the obligation
    statement byte-identical), so a ``while true`` implementation that never
    produces a verdict IS writable and IS in scope. Two builds were run to
    establish this: ``partial def`` carrying a diverging ``while true`` loop
    builds as an admissible variant, and ``partial def`` carrying the GOLD body
    still VERIFIES (exit 0), so the marker alone costs the bundle nothing.

    What cannot be built is the WITNESS, and that is what makes the class a
    hole rather than a shippable reject case. ``partial`` makes the definition
    opaque to the kernel: it is compiled without an equation lemma, so the
    diverging term never reduces. Measured, three builds: ``decide`` on the
    refutation reports it ``failed for proposition ... because its `Decidable`
    instance ... did not reduce``; a ``simp``-based variant leaves the
    unreduced ``forIn Lean.Loop.mk`` goal; and a hypothesis-conditioned witness
    (``(h : implementation_isSubset … = v)``) fails on the FROZEN solution too,
    so it discriminates nothing. Under the gate's own screens that is
    ``witness-undecided``, an inconclusive outcome, which would make the
    battery FAIL rather than record a false pass — so no such case is shipped.

    Recorded as a KNOWN HOLE in the SPEC's expressiveness on this carrier (a
    diverging implementation is neither provable nor refutable here), NOT as a
    vacuous class: a vacuous class would claim the battery is complete, and it
    is not. This is the ``partial``-semantics shape of
    ``the corpus-wide termination-semantics finding``, reached by the ``partial`` keyword rather
    than by a bundle-level semantics option.

  * UNGROUNDED-ORACLE ECHO — VACUOUS, for the reason nagini gives for its own
    surface: the postcondition unfolds to a fold over the ACTUAL input handles,
    so producing the verdict IS doing the work and there is no echo to build.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is where the battery lives. Seven
    rivals, each correct on part of the domain and diverging where the modeled
    behavior bites.

  * AXIOM lane — DROPPED. The nagini ``AXIOM_TESTS`` (one contract-only
    membership axiom plus two deep-model reference probes) belong to G-AX, which
    this gate ignores; and this bundle declares no axiom and no ``opaque``
    callee, so there is nothing here to probe.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form, and
every rival below does in fact break it with the same ``'show' tactic failed``
— so a rejection alone attributes NOTHING to the spec. Every ``expect="reject"``
case therefore carries a Lean snippet that states ``¬ problem_spec_isSubset``
at one concrete input and closes by ``decide``. Each was checked with two real
``lake env lean`` builds: it ELABORATES against its own rival (exit 0) and FAILS
on the frozen solution (exit 1, ``decide`` reporting that the negation is not
provable there), so it discriminates rather than asserting a tautology.

An INDEPENDENT audit re-ran all of those builds and added a THIRD per case, the
forgery pair: a file differing from the witness only in dropping the ``¬``, so
it claims the frozen solution is CORRECT at the same input. Every forgery builds
against the frozen solution (exit 0) and fails against its rival (exit 1) — the
exact mirror of the witness — so the frozen side's exit code demonstrably tracks
the CLAIM and not the file's shape. Every gold-side failure is also a plain
``decide`` evaluation, so none of the stuck-reduction classes (irreducible loop,
missing ``Decidable`` instance, unification failure on an un-normalised term)
is in play on this carrier: the enumeration and the membership test are both
modeled deeply, so every witness point genuinely computes.

REFINEMENT (why a verifying rival would be a true verify-does-not-imply-resolve
break). The FAIL_TO_PASS assertions probe the modeled behavior at exactly two
points: a product every one of whose tuples is a member of the candidate
collection, where a determined AFFIRMATIVE verdict is required; and the same
product against a candidate collection holding none of its tuples, where a
determined NEGATIVE verdict is required. Each reject case's ``refinement``
argues from the point(s) at which its faithful real counterpart diverges from
the required verdict there. This was checked mechanically for every rival below,
and it is also why four otherwise-attractive rivals were DROPPED rather than
shipped with an unsupportable refinement — see ``assessment``.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-20438"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swaps(src, *pairs):
    """Apply a sequence of (old, new) surgical swaps, each anchored + unique."""
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


# ---------------------------------------------------------------------------
# Region anchors. Each is unique in Solution.lean (asserted at load by _swap)
# and lies ENTIRELY inside the region it is meant to edit.
# ---------------------------------------------------------------------------

# The whole gold implementation body: the accumulating conjunction over the
# enumerated tuples, wrapped in the determined verdict. Wholly inside
# `-- impl-start`/`-- impl-end`.
_I_BODY = """  let mut acc := true
  for x in productSet factors do
    acc := acc && candidate.contains x
  return some acc"""

# The frozen proof's closing step: bridge the desugared loop to the clean form,
# then discharge with the two induction helpers. Wholly inside
# `-- proof-start`/`-- proof-end`, so re-proving keeps `same_spec` and leaves the
# `theorem correct_isSubset` STATEMENT byte-identical.
_P_CLOSE = """  show some (Id.run (forIn (productSet factors) true (fun x r =>
        (pure (ForInStep.yield (r && candidate.contains x)) : Id _)))) = _
  rw [hfold, hall, Bool.true_and]"""

# The frozen proof's intro line — unique in the file — so the admissibility
# positive can prepend ground `have`s without touching the statement or spec view.
_P_INTRO = "  intro factors candidate\n"


# ---------------------------------------------------------------------------
# Witness scaffold. The carrier is fully transparent (no opaque callee), so each
# refutation is stated at concrete list literals and closed by `decide`. The head
# binds NOTHING, so there are no assumptions to be mutually inconsistent.
# ---------------------------------------------------------------------------
def _w(factors, candidate):
    return (
        f"example : ¬ problem_spec_isSubset {factors} {candidate}\n"
        f"    (implementation_isSubset {factors} {candidate}) := by\n"
        "  unfold problem_spec_isSubset implementation_isSubset\n"
        "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # SOUNDNESS POSITIVES — structurally DIFFERENT but CORRECT implementations
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_isSubset` statement byte-identical, adds no helper lemma,
    # no axiom and no assumption token. All three were confirmed with a real
    # `lake env lean` build.
    # =====================================================================
    {
        "id": "pos-hoist-membership",
        "kind": "soundness",
        "expect": "verify",
        # Direct port of nagini's positive control: hoist the per-element
        # membership read into a named local and accumulate against that local
        # instead of against the call. Definitionally the frozen loop body, so
        # the frozen proof still closes untouched.
        "module": _swap(_BASE, _I_BODY, """  let mut acc := true
  for x in productSet factors do
    let m := candidate.contains x
    acc := acc && m
  return some acc"""),
        "rationale": (
            "PORT of the nagini positive control (there: hoist the membership "
            "read into a local `m` and restructure the accumulator update as "
            "`res = m and res`). Same reshape here: the per-tuple membership "
            "test is bound to a named local and the accumulator updated against "
            "it. The verdict is unchanged on every input, so the single "
            "postcondition equation still holds — if this could not verify, the "
            "postcondition would be SPEC-TOO-STRONG (rejecting a faithful "
            "correct implementation over a local-binding difference). The "
            "reshape is definitionally equal to the frozen body, so the frozen "
            "tactic body closes it verbatim: no re-proving, no new declaration."),
    },
    {
        "id": "pos-reverse-traversal",
        "kind": "soundness",
        "expect": "verify",
        # Traversal-ORDER positive: fold over the enumerated tuples in the
        # opposite order. Genuinely different control flow, and NOT definitionally
        # equal — the proof region is re-proved by composing the frozen helpers
        # with the order-independence of a total conjunction over a list.
        "module": _swaps(
            _BASE,
            (_I_BODY, """  let mut acc := true
  for x in (productSet factors).reverse do
    acc := acc && candidate.contains x
  return some acc"""),
            (_P_CLOSE,
             "  show some (Id.run (forIn ((productSet factors).reverse) true "
             "(fun x r =>\n"
             "        (pure (ForInStep.yield (r && candidate.contains x)) "
             ": Id _)))) = _\n"
             "  rw [hfold, hall, Bool.true_and, List.all_reverse]"),
        ),
        "rationale": (
            "Carries over the nagini positive control's ARGUMENT (a faithful "
            "reshape of the fold must verify) to the aspect this carrier makes "
            "available: the direction of traversal. The nagini sibling could not "
            "flip its fold direction — its invariant is written against a "
            "back-to-front drop, and a forward fold would need an unprovable "
            "append lemma — so it deliberately KEPT the direction and reshaped "
            "only the locals. On this carrier the flip is available and is the "
            "sharper positive: the conjunction over a finite list is "
            "order-independent, so the verdict is identical on every input and "
            "the spec MUST admit it, else SPEC-TOO-STRONG. Re-proved inside the "
            "proof region by composing the frozen helper lemmas with the "
            "order-independence of the fold; statement byte-identical, no new "
            "axiom/lemma, no assumption token."),
    },
    {
        "id": "pos-commuted-conjunction",
        "kind": "soundness",
        "expect": "verify",
        # The canonical "reshaped but CORRECT" case the witness machinery exists
        # to distinguish from a wrong one: commute the accumulator conjunction.
        # Breaks the frozen script (both a commuted-correct and a
        # dropped-conjunct rival fail identically), so this positive proves the
        # battery is not merely observing tactic breakage.
        "module": _swaps(
            _BASE,
            (_I_BODY, """  let mut acc := true
  for x in productSet factors do
    acc := candidate.contains x && acc
  return some acc"""),
            (_P_CLOSE,
             "  show some (Id.run (forIn (productSet factors) true (fun x r =>\n"
             "        (pure (ForInStep.yield (candidate.contains x && r)) "
             ": Id _)))) = _\n"
             "  rw [show (fun (x : List Int) (r : Bool) =>\n"
             "        (pure (ForInStep.yield (candidate.contains x && r)) "
             ": Id _))\n"
             "      = (fun x r => (pure (ForInStep.yield "
             "(r && candidate.contains x)) : Id _)) from\n"
             "      by funext x r; rw [Bool.and_comm]]\n"
             "  rw [hfold, hall, Bool.true_and]"),
        ),
        "rationale": (
            "The accumulator conjunction is commuted: the per-tuple membership "
            "test is the LEFT operand. Behaviour is identical on every input "
            "(conjunction is commutative), so the postcondition must admit it, "
            "else SPEC-TOO-STRONG. This positive is the load-bearing control for "
            "the whole reject lane: a commuted-but-correct implementation and a "
            "wrong one that drops part of the test break the frozen tactic "
            "script in exactly the same way, so shipping it demonstrates that "
            "this battery's rejections are attributed by their witnesses and not "
            "by tactic breakage. Re-proved by rewriting the loop body to the "
            "frozen orientation before applying the frozen helpers; statement "
            "byte-identical, no new axiom/lemma."),
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation must be SATISFIABLE at a normal,
    # F2P-shaped input, not merely closable in the abstract.
    # =====================================================================
    {
        "id": "admiss-f2p-points",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            "  have _ground_affirmative : problem_spec_isSubset "
            "[[1, 2], [1, 2]]\n"
            "      [[1, 1], [1, 2], [2, 1], [2, 2]]\n"
            "      (implementation_isSubset [[1, 2], [1, 2]]\n"
            "        [[1, 1], [1, 2], [2, 1], [2, 2]]) := by\n"
            "    unfold problem_spec_isSubset implementation_isSubset\n"
            "    decide\n"
            "  have _ground_negative : problem_spec_isSubset "
            "[[1, 2], [1, 2]] [[1]]\n"
            "      (implementation_isSubset [[1, 2], [1, 2]] [[1]]) := by\n"
            "    unfold problem_spec_isSubset implementation_isSubset\n"
            "    decide\n"
            # Added by audit: the two BOUNDARY inputs no reject witness reaches
            # on the affirmative side. The empty factor list is the one input
            # whose enumeration is the single EMPTY tuple (a vacuous product),
            # and an empty candidate collection against a non-empty product is
            # the degenerate negative. Both must be satisfiable too, else the
            # obligation is unsatisfiable exactly at a boundary.
            "  have _ground_empty_factors : problem_spec_isSubset [] [[1]]\n"
            "      (implementation_isSubset [] [[1]]) := by\n"
            "    unfold problem_spec_isSubset implementation_isSubset\n"
            "    decide\n"
            "  have _ground_empty_candidate : problem_spec_isSubset "
            "[[1, 2], [1, 2]] []\n"
            "      (implementation_isSubset [[1, 2], [1, 2]] []) := by\n"
            "    unfold problem_spec_isSubset implementation_isSubset\n"
            "    decide\n"
            + _P_INTRO),
        "rationale": (
            "RE-EXPRESSES nagini's admissibility case. There the precondition is "
            "a read-permission on the input, so admissibility means "
            "'the precondition admits a normal input and the permissions "
            "round-trip across the self-calls'. This obligation carries NO "
            "precondition hypothesis at all (the theorem binds only the two "
            "inputs), so that target does not exist here; the honest analogue is "
            "that the modeled behavior is SATISFIABLE by evaluation at exactly "
            "the two F2P-shaped points — a product all of whose tuples are "
            "members of the candidate collection (determined affirmative "
            "verdict) and the same product against a candidate collection "
            "holding none of them (determined negative verdict). Both are "
            "discharged as `have`s by `decide`, then the frozen obligation is "
            "closed verbatim. If this could not verify, the spec would be "
            "unsatisfiable at a normal input — the analogue of "
            "PRECOND-TOO-STRONG. Nothing is assumed: no new declaration, "
            "statement byte-identical, the ground instances are `have`s inside "
            "the existing tactic body. AUDIT: the `have`s were confirmed to do "
            "real work rather than pass trivially — a control variant whose "
            "`have` asserts the WRONG verdict at one of these very points "
            "(`… [[1]] = some true`) FAILS to build (exit 1), so each `decide` "
            "is genuinely evaluating the modeled behavior. The audit also "
            "EXTENDED this case with the two boundary inputs no reject witness "
            "reaches: the empty factor list, whose enumeration is the single "
            "empty tuple (the vacuous product), and an empty candidate "
            "collection against a non-empty product. Both are satisfiable by "
            "evaluation, so the obligation is admissible at the boundaries as "
            "well as at the two F2P-shaped points."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real counterpart would NOT resolve the F2P, and
    # (b) a witness pinning the violation at one concrete input, checked by two
    # real builds to hold of the rival and fail on the frozen solution.
    # =====================================================================

    # ---- attacks D (determinedness): never produces a verdict at all --------
    {
        "id": "weak-undetermined",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_BODY,
                        "  let _ := factors\n"
                        "  let _ := candidate\n"
                        "  return none"),
        "refinement": (
            "This is the pre-fix behavior itself: no verdict is computed for "
            "this combination of carriers, so the answer falls through to the "
            "undetermined one. The faithful real counterpart is the unpatched "
            "repository, where the per-tuple membership conjunction is never "
            "performed. It diverges from the required verdict at BOTH F2P probe "
            "points — the affirmative one (a determined affirmative verdict is "
            "required; an undetermined answer is returned) and the negative one "
            "(a determined negative verdict is required) — so the faithful "
            "patch does NOT resolve. It is also exactly the reported defect."),
        "rationale": (
            "REJECT from the determinedness aspect (D) of the postcondition "
            "equation: the spec pins `result = some (…)`, an inhabited verdict, "
            "and the rival returns the undetermined `none` on every input, so "
            "the equation fails for every `factors`/`candidate`. Refuted at the "
            "affirmative F2P-shaped point (a two-factor product whose every "
            "tuple is a member of the candidate collection), where the spec "
            "demands `some true`. Ports nagini's cheapest-wrong / prepatch-"
            "skeleton rival."),
        "witness": _w("[[1, 2], [1, 2]]", "[[1, 1], [1, 2], [2, 1], [2, 2]]"),
    },

    # ---- attacks D on the NEGATIVE half only (a near-miss of the above) -----
    {
        "id": "weak-affirmative-only",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS of weak-undetermined: this rival agrees with gold wherever
        # the verdict is affirmative and is undetermined only where it should be
        # negative. It therefore gets its OWN witness, at the point that
        # distinguishes it — weak-undetermined's affirmative point would NOT
        # refute it.
        "module": _swap(_BASE, _I_BODY,
                        "  let mut acc := true\n"
                        "  for x in productSet factors do\n"
                        "    acc := acc && candidate.contains x\n"
                        "  if acc then\n"
                        "    return some true\n"
                        "  return none"),
        "refinement": (
            "A half-fix: the per-tuple membership conjunction IS performed, but "
            "only an affirmative outcome is reported as a determined verdict — a "
            "negative outcome still falls through to the undetermined answer. "
            "The faithful real counterpart is a rule that returns the "
            "conjunction only when it holds and otherwise declines to answer. It "
            "agrees with the required verdict at the affirmative F2P probe point "
            "but diverges at the negative one, which requires a DETERMINED "
            "negative verdict rather than an undetermined answer, so the "
            "faithful patch does NOT resolve. Half the reported defect survives "
            "it."),
        "rationale": (
            "REJECT from the determinedness aspect (D): the spec pins "
            "`result = some (conjunction)` for EVERY input, including inputs "
            "where the conjunction is false; this rival returns `none` on "
            "exactly those. A near-miss of `weak-undetermined` that agrees with "
            "gold over the whole affirmative sub-domain, so it is refuted at its "
            "own DISTINCT point: the negative F2P-shaped input (the same product "
            "against a candidate collection holding none of its tuples), where "
            "the spec demands `some false`."),
        "witness": _w("[[1, 2], [1, 2]]", "[[1]]"),
    },

    # ---- attacks V: constant verdict, reads neither input -------------------
    {
        "id": "weak-constant-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_BODY,
                        "  let _ := factors\n"
                        "  let _ := candidate\n"
                        "  return some true"),
        "refinement": (
            "Answers affirmatively without consulting either input. The faithful "
            "real counterpart is a rule that reports containment "
            "unconditionally. It diverges from the required verdict at the "
            "negative F2P probe point, which demands a determined NEGATIVE "
            "verdict, so the faithful patch does NOT resolve. It is the "
            "cheapest possible way to make the affirmative half of the reported "
            "defect look fixed while leaving the negative half wrong."),
        "rationale": (
            "REJECT from the value aspect (V): the spec pins the determined "
            "boolean to the membership conjunction over the enumerated product, "
            "and a constant ignores both binders, so it disagrees on every input "
            "whose conjunction is false. Refuted at a THIRD, distinct point — a "
            "single-factor product against an EMPTY candidate collection — which "
            "also exercises the empty-candidate boundary no other witness "
            "reaches."),
        "witness": _w("[[3]]", "[]"),
    },

    # ---- attacks V: verdict driven by shape, membership never consulted -----
    {
        "id": "weak-emptiness",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_BODY,
                        "  let _ := candidate\n"
                        "  return some (productSet factors).isEmpty"),
        "refinement": (
            "Decides the verdict from the SHAPE of the product alone — whether "
            "its enumeration is empty — never consulting the candidate "
            "collection. The faithful real counterpart is a rule that answers "
            "from emptiness instead of from membership. It diverges at the "
            "affirmative F2P probe point, where the product is non-empty and all "
            "of its tuples ARE members, so the required determined affirmative "
            "verdict is reported negative; so the faithful patch does NOT "
            "resolve. This is the port of nagini's cheapest-wrong "
            "emptiness rival."),
        "rationale": (
            "REJECT from the value aspect (V): the spec pins the verdict to the "
            "per-tuple membership conjunction, and this rival's answer is a "
            "function of `factors` alone — the `candidate` binder is entirely "
            "unread. Refuted at a two-factor single-element product whose ONE "
            "enumerated tuple IS a member of the candidate collection: the "
            "spec's conjunction is therefore TRUE (it demands `some true`) "
            "while the product is non-empty, so the emptiness answer is "
            "`some false`. Evaluation at the witness point (audited): the "
            "enumeration is a single two-component tuple, the candidate "
            "collection holds exactly it, spec verdict `some true`, rival "
            "verdict `some false` — the point is chosen where the two "
            "disagree, and it must be an agreement point for MEMBERSHIP for "
            "the emptiness answer to be the thing that diverges. PORT of "
            "nagini's emptiness-decides-containment rival."),
        "witness": _w("[[1], [2]]", "[[1, 2]]"),
    },

    # ---- attacks V: partial domain — a factor is dropped from the product ---
    {
        "id": "weak-drop-factor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_BODY,
                        "  let mut acc := true\n"
                        "  for x in productSet (factors.drop 1) do\n"
                        "    acc := acc && candidate.contains x\n"
                        "  return some acc"),
        "refinement": (
            "PARTIAL-DOMAIN, and the closest counterpart to nagini's "
            "skip-the-first-element rival: the leading factor is dropped, so the "
            "membership conjunction is taken over the product of the REMAINING "
            "factors — tuples of the wrong arity, and the wrong set of them. The "
            "faithful real counterpart is a rule that enumerates a truncated "
            "product. It diverges at the affirmative F2P probe point, whose "
            "product has two factors: the truncated enumeration yields "
            "one-element tuples that are not members of a collection of "
            "two-element tuples, so the required determined affirmative verdict "
            "is reported negative. The faithful patch does NOT resolve."),
        "rationale": (
            "REJECT from the value aspect (V): the spec pins the conjunction "
            "over `productSet factors`, the FULL product, and the rival folds "
            "over `productSet (factors.drop 1)`. Refuted at a two-factor "
            "product whose FULL enumeration is wholly contained in the "
            "candidate collection while the TRUNCATED enumeration is not — so "
            "the spec demands `some true` and the rival answers `some false`, "
            "and the divergence is attributable to the dropped factor and not "
            "to an unrelated mismatch. Evaluation at the witness point "
            "(audited): the full enumeration is the two two-component tuples, "
            "which the candidate collection holds exactly (spec: `some true`); "
            "dropping the leading factor leaves a single ONE-component tuple, "
            "which no member of a collection of two-component tuples can match "
            "(rival: `some false`). A fourth distinct point, and the only "
            "witness whose candidate collection is exactly the full "
            "enumeration while the truncated enumeration falls outside it — "
            "which is what isolates the ARITY change the dropped factor "
            "causes."),
        "witness": _w("[[1, 2], [5]]", "[[1, 5], [2, 5]]"),
    },

    # ---- attacks V: the OTHER end of the factor list is dropped ------------
    # ADDED BY AUDIT. `weak-drop-factor` attacks the LEADING factor; the
    # trailing one was unattacked, and the two are not the same point: the
    # enumeration is front-recursive, so dropping the last factor changes WHICH
    # tuples are produced in a different way than dropping the first. Kept
    # because its refinement is honestly writable (it breaks the affirmative
    # F2P point), unlike the four rivals the port dropped for that reason.
    {
        "id": "weak-drop-last-factor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_BODY,
                        "  let mut acc := true\n"
                        "  for x in productSet factors.dropLast do\n"
                        "    acc := acc && candidate.contains x\n"
                        "  return some acc"),
        "refinement": (
            "PARTIAL-DOMAIN, the mirror of `weak-drop-factor`: the TRAILING "
            "factor is dropped, so the membership conjunction is taken over the "
            "product of all but the last factor — again tuples of the wrong "
            "arity, but a different set of them, since the enumeration is "
            "front-recursive. The faithful real counterpart is a rule that "
            "enumerates the product of a truncated factor list. It diverges at "
            "the affirmative F2P probe point, whose product has two factors: "
            "dropping the trailing factor yields the one-element tuples of the "
            "leading factor alone, and those are not members of a collection of "
            "two-element tuples, so the required determined affirmative verdict "
            "is reported negative (evaluated: rival `some false`, spec "
            "`some true`). The faithful patch does NOT resolve."),
        "rationale": (
            "REJECT from the value aspect (V): the spec pins the conjunction "
            "over `productSet factors`, and the rival folds over "
            "`productSet factors.dropLast`. Refuted at a SEVENTH distinct point "
            "whose LEADING factor is the single-element one, so the truncated "
            "enumeration is wholly contained in the candidate collection "
            "(rival: `some true`) while the full enumeration is not (spec: "
            "`some false`) — the OPPOSITE polarity from `weak-drop-factor`'s "
            "point, which is what makes the two rivals independent rather than "
            "two spellings of one. Both builds re-run by the audit: the witness "
            "elaborates on the rival (exit 0), fails on the frozen solution "
            "(exit 1, plain `decide` evaluation), and the flipped-claim forgery "
            "builds on the frozen solution (exit 0)."),
        "witness": _w("[[5], [1, 2]]", "[[5]]"),
    },

    # ---- attacks V: the candidate collection is narrowed -------------------
    {
        "id": "weak-single-candidate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_BODY,
                        "  let mut acc := true\n"
                        "  for x in productSet factors do\n"
                        "    acc := acc && (candidate.take 1).contains x\n"
                        "  return some acc"),
        "refinement": (
            "Carries over the ARGUMENT of nagini's dropped-conjunct rival (there: "
            "reduce a mutual containment to one direction) to the aspect this "
            "carrier exposes — the containment test is narrowed so that only the "
            "FIRST member of the candidate collection can ever match. The "
            "faithful real counterpart is a rule that tests each tuple against a "
            "truncated candidate collection. It diverges at the affirmative F2P "
            "probe point, whose product has four tuples matching four distinct "
            "members of the candidate collection: with only the first member "
            "consultable the required determined affirmative verdict is reported "
            "negative. The faithful patch does NOT resolve."),
        "rationale": (
            "REJECT from the value aspect (V): the spec pins each tuple's "
            "membership against the WHOLE `candidate` binder, and the rival "
            "consults only its first element, so the two disagree whenever a "
            "tuple of the product matches a later member. This is the rival that "
            "abuses the `candidate` binder specifically — refuted at a fifth "
            "distinct point (a single-factor two-element product against a "
            "two-member candidate collection) where the product is wholly "
            "contained but only via BOTH members, so the divergence isolates the "
            "narrowed containment test."),
        "witness": _w("[[1, 2]]", "[[1], [2]]"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> LEAN ACCOUNTING. The sibling battery has 10 SPEC cases (2 soundness
# positives, 1 admissibility, 7 uniqueness rivals) plus 3 AXIOM_TESTS, spread
# over THREE contracted functions. This bundle models ONE of those behaviors, so
# most sibling cases have no counterpart here. Every sibling case is recorded.
#
#   sibling case                  -> here
#   ---------------------------------------------------------------------------
#   pos-control-reshape-psof      -> pos-hoist-membership       PORTED
#   admiss-fse-selfcall           -> admiss-f2p-points          RE-EXPRESSED
#   empty-cheapest-psof           -> weak-emptiness             PORTED
#                                    + weak-undetermined        PORTED (split)
#   partial-first-psof            -> weak-drop-factor           RE-EXPRESSED
#   one-direction-fse             -> weak-single-candidate      RE-EXPRESSED
#   frame-mut-psof                -> (none)                     VACUOUS
#   frame-mut-fse                 -> (none)                     VACUOUS
#   pos-control-route-reshape     -> (none)                     NOT MODELED
#   no-guard-route                -> (none)                     NOT MODELED
#   wrong-outcome-route           -> (none)                     NOT MODELED
#   (none)                        -> pos-reverse-traversal      ADDED
#   (none)                        -> pos-commuted-conjunction   ADDED
#   (none)                        -> weak-affirmative-only      ADDED (attacks D)
#   (none)                        -> weak-constant-true         ADDED (attacks V)
#   (none)                        -> weak-drop-last-factor      ADDED BY AUDIT (V)
#   AXIOM_TESTS (3)               -> (none)                     DROPPED (G-AX)
#
# VACUOUS (frame-mut-psof, frame-mut-fse): both reject a rival that WRITES to a
#   read-only input, which the sibling's carrier catches on permission grounds.
#   Lean is referentially transparent — immutable value inputs, no aliasing, no
#   fractional permission, no read-only cell to overwrite — so the class
#   collapses. No substitute probe is fabricated.
# NOT MODELED (the three routing cases + one-direction positive): the sibling
#   contracts two further functions — a mutual-containment equality and an
#   operand-kind routing guard that chooses between an arithmetic reduction and
#   the collection decision. This bundle models NEITHER (mapping.md records them
#   as ride-along consumers of the modeled behavior, plumbing that is not
#   independently cold-derivable, so they get no triple). Their rivals attack
#   postcondition clauses that do not exist in this spec, and fabricating
#   substitutes would mean inventing rivals for unmodeled behavior. Carrier
#   narrowing, recorded rather than padded.
# SPLIT (empty-cheapest-psof): the sibling's single cheapest-wrong rival covers
#   both "never computes the membership test" and "no verdict exists at all",
#   which are one thing on its carrier. Here they are separable and hit the two
#   DIFFERENT aspects of the postcondition — value (weak-emptiness) and
#   determinedness (weak-undetermined) — so the port ships both.
# ADDED (4): two positives and two rivals the sibling did not need.
#   * pos-reverse-traversal / pos-commuted-conjunction: the sibling could not
#     flip its fold direction or commute its accumulator (its invariant is
#     written against a back-to-front drop). Both are available here and both
#     BREAK the frozen tactic script while remaining correct, which is exactly
#     the confound the witness requirement exists to rule out — shipping them
#     shows this battery's rejections come from its witnesses.
#   * weak-affirmative-only / weak-constant-true: needed for aspect coverage.
#     weak-affirmative-only is a deliberate NEAR-MISS of weak-undetermined
#     (it agrees with gold over the entire affirmative sub-domain), so it carries
#     its own witness at the point that distinguishes them rather than sharing.
#     weak-constant-true reads NEITHER binder, closing the "ignores an input
#     entirely" hole. Neither is fabricated for an unmodeled behavior: both
#     attack load-bearing aspects of the SAME single equation.
# DROPPED SOUNDNESS POSITIVE (reported, not hidden): a fourth positive was
#   attempted and abandoned — the SHORT-CIRCUIT shape, which returns the negative
#   verdict from inside the loop on the first non-member instead of accumulating
#   (the most faithful skeleton of the real short-circuiting conjunction). It is
#   correct, but the early `return` desugars the loop into a `ForInStep.done`
#   state machine carrying an `Option (Option Bool)`, and closing it needs a new
#   generalized induction over that machine rather than the frozen helpers
#   (`Type mismatch` on the naive induction hypothesis, since the frozen lemmas
#   are stated over the plain accumulator form). Per the porting rules a shape
#   needing a genuinely new lemma is replaced by a cheaper one, and the proof was
#   NOT weakened to land it: no helper lemma, no `sorry`. Recorded as a known gap
#   — the three shipped positives already include two that require real
#   re-proving.
# DROPPED RIVALS (4) — checked mechanically, and dropped because their
#   `refinement` could not be honestly written: skip-the-FIRST-TUPLE (rather than
#   the first factor); conjunction replaced by disjunction; the factor list
#   consulted directly instead of its enumeration; and the containment direction
#   swapped. Each is genuinely WRONG against the spec and each has a
#   discriminating witness (all four were built and confirmed to refute their
#   rival and fail on gold), but all four AGREE with the required verdict at BOTH
#   F2P probe points. A reject case's refinement must argue that the faithful
#   real patch would not resolve; for these it would, so shipping them would
#   attach a false refinement to a real refutation. They are dropped as
#   unsupportable, not as unrefutable — the aspects they attack (V) are covered
#   by four rivals that DO break the F2P.
#
# ---------------------------------------------------------------------------
# INDEPENDENT AUDIT (adversarial re-derivation; every claim below is a build the
# auditor ran, not an argument). Recorded so the next reader does not have to
# re-pay for it.
#
# STATEMENT INTEGRITY. All 10 cases' `theorem correct_isSubset` STATEMENTS are
#   byte-identical to the frozen one (whitespace-normalized comparison of the
#   declaration head up to `:=`), and `variant_problems` is empty for all 10.
#   No case reformats or weakens a hypothesis.
#
# WITNESS DISCRIMINATION, RE-DERIVED. Each of the six witnesses was rebuilt
#   TWICE independently: against its own rival (all six exit 0) and against the
#   frozen solution (all six exit 1). Every gold-side failure is a PLAIN
#   EVALUATION — "Tactic `decide` proved that the proposition ¬(…) …", i.e. the
#   kernel evaluated the claim and found the spec SATISFIED at that input. No
#   stuck reduction, no missing `Decidable` instance, no unification failure, no
#   missing identifier, no timeout: none of the gate's four stuck-screens is in
#   any of the twelve logs.
#
# FORGERY TEST (attack B′), run on all six even though a plain evaluation does
#   not require it. For each case a second file differing ONLY in the CLAIM was
#   built — the `¬` dropped, so it asserts the frozen solution is CORRECT at
#   that same input. All six forgeries build against the frozen solution
#   (exit 0) and all six FAIL against their rival (exit 1) — the exact mirror of
#   the witnesses. Gold's exit code therefore tracks the claim rather than the
#   file's shape, which is what makes these refutations admissible evidence.
#   No witness is hollow.
#
# TAUTOLOGY / DISCRIMINATION AT THE SOURCE LEVEL. Every witness names the
#   concrete input pair it discriminates at in its own statement, and none binds
#   anything in its head, so `consistency_probe` returns None for all six (no
#   hypotheses to be jointly unsatisfiable) — confirmed by calling the gate's
#   own helper. Each witness point was independently EVALUATED (`#eval`) to
#   confirm the rival and the spec really disagree there; two `rationale`
#   texts described their point incorrectly and were corrected by this audit
#   (see weak-emptiness and weak-drop-factor).
#
# RESHAPED-NOT-WRONG CHECK (attack C). Each rival was confirmed OBSERVABLY
#   different from gold at its witness point by evaluation, not by argument, so
#   no case is vacuous. The three positives were also confirmed to BREAK the
#   frozen tactic script when their proof region is left frozen
#   (pos-reverse-traversal and pos-commuted-conjunction fail with the same
#   `'show' tactic failed` as every rival; pos-hoist-membership is
#   definitionally equal and closes untouched, exit 0). That is the control
#   which shows the reject lane is decided by its witnesses and not by tactic
#   breakage: correct-and-reshaped and wrong break IDENTICALLY here.
#
# SPEC-TOO-WEAK PROBE (attack D) — 7 NEW wrong implementations the battery does
#   not contain, aimed at what the shipped rivals leave unattacked. ALL SEVEN
#   were REJECTED by the frozen spec, and each was given a witness that
#   elaborates on the rival (exit 0) and fails on gold (exit 1):
#     * the empty-factor-list boundary answered affirmatively (the one input
#       whose enumeration is the single EMPTY tuple, which no shipped witness
#       reaches);
#     * the containment direction swapped (candidate tested against the
#       product instead of the reverse);
#     * membership weakened to an arity-only test;
#     * the LAST factor dropped rather than the first;
#     * the conjunction replaced by a disjunction;
#     * the verdict left undetermined only on the empty-candidate boundary;
#     * only the FIRST enumerated tuple tested.
#   No new wrong implementation verifies. NO SPEC HOLE FOUND. Of the seven, the
#   dropped-LAST-factor rival is the only one whose refinement is honestly
#   writable (it misdecides the affirmative F2P point), so it was SHIPPED as
#   `weak-drop-last-factor`; the other six agree with the required verdict at
#   both F2P points, which is the same reason the port dropped four of its own,
#   so they stay unshipped rather than carrying a false refinement.
#
# SPEC-TOO-STRONG PROBE (attack E) — NEW correct reshapes, all admitted by the
#   spec once re-proved inside the proof region:
#     * the postcondition's own fold as the implementation (closes by `rfl`);
#     * De Morgan (not-any-not instead of all);
#     * `foldr` instead of the accumulating `for` loop;
#     * a redundant `&& true` on the accumulator update.
#   All four VERIFY (exit 0), so the spec admits faithful reshapes across the
#   fold direction, the fold combinator, and the boolean spelling. NO SOUNDNESS
#   HOLE FOUND. One reshape is UNCERTAIN rather than a hole: spelling the
#   membership test as `candidate.any (fun c => c == x)` is correct but its
#   equality with `List.contains` is not definitional in the needed argument
#   ORDER (`List.contains` tests `c == x` with the operands the other way
#   round), and the auditor could not close it without a new lemma — `rfl`
#   fails on the operand order and `simp [List.contains, BEq.comm]` hits
#   maximum recursion depth. Reported as unclosed, NOT claimed as a hole.
#
# DROPPED-RIVAL ACCOUNTING RE-DERIVED. Two of the four dropped rivals were
#   independently rebuilt (disjunction-for-conjunction, direction-swapped) and
#   both are indeed genuinely wrong AND witnessable, confirming the port's
#   stated reason for dropping them is the refinement argument and not an
#   inability to refute them. The port's accounting is honest.
#
# POINT SPREAD. The seven reject witnesses probe seven DISTINCT input pairs
# (pts=7). The `spec` / `rival` columns are the EVALUATED verdicts at that point
# (audited by `#eval`), which is what makes each row a checked disagreement
# rather than a claim:
#   (factors, candidate)                          aspect spec  rival case
#     ([[1,2],[1,2]], [[1,1],[1,2],[2,1],[2,2]])   D    some T  none  weak-undetermined
#     ([[1,2],[1,2]], [[1]])                       D    some F  none  weak-affirmative-only
#     ([[3]],         [])                          V    some F  some T weak-constant-true
#     ([[1],[2]],     [[1,2]])                     V    some T  some F weak-emptiness
#     ([[1,2],[5]],   [[1,5],[2,5]])               V    some T  some F weak-drop-factor
#     ([[5]],[[1,2]]) -> ([[5],[1,2]], [[5]])      V    some F  some T weak-drop-last-factor
#     ([[1,2]],       [[1],[2]])                   V    some T  some F weak-single-candidate
#   `factors` takes 6 distinct values spanning one and two factors, one- and
#   two-element factors, and both orderings of a mixed-size factor pair;
#   `candidate` takes 6 distinct values spanning empty, single-member, two-member
#   and four-member collections, and tuples of both arities. Neither binder is
#   held fixed, so a rival mishandling only one input cannot slip through. Both
#   aspects of the equation (D determinedness, V value) are attacked, D by two
#   rivals and V by five. The disagreement POLARITY is mixed too (three points
#   where the spec demands affirmative and the rival answers negative, and four
#   the other way), so no rival is refuted merely by a one-directional bias.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job, and this bundle declares no
# axiom and no `opaque` callee (both the product enumeration and the membership
# test are modeled deeply), so there is nothing to probe; the gate ignores
# AXIOM_TESTS regardless.
AXIOM_TESTS = []
