"""properties.py — G-PBT falsification battery for django__django-13158 (lean).

NOT a Lean module: a manifest of adversarial cases the G-PBT runner executes
over the frozen `Solution.lean`. Every case edits ONLY the implementation region
(and, where a positive control needs it, the proof body), so
`variant_scope.same_spec` holds by construction and every rejection is
attributable to the postcondition rather than to a tampered spec.

DEFENDED SURFACE
----------------
One obligation is modeled here:

    theorem correct_makeEmpty :
        ∀ q : Query, problem_spec_makeEmpty q (implementation_makeEmpty q)

over the single input binder `q : Query`, an inductive TREE — a node carrying its
own `selfEmpty : Bool` marker plus the list of sub-queries whose results are
combined into it, nested to any depth. The postcondition is a conjunction of two
independent top-level clauses:

  * `YieldsNothing result` — the guarantee holds of the WHOLE tree: this node's
    own marker is forced AND, recursively, so is every combined sub-query's. This
    clause is itself recursive, so it decomposes into three independently
    attackable positions: the TOP node's own marker, a DEPTH-1 sub-query's
    marker, and a DEPTH-2 (nested) sub-query's marker.
  * `toShape result = toShape q` — the frame: the operation flips markers only,
    it neither adds nor drops a sub-query at any level.

The carrier is FULLY TRANSPARENT — `Query`, `YieldsNothing` and `toShape` are
concrete inductives/defs with no `opaque` callee anywhere — so no rival needs
carrier conditioning. Every witness below states the refutation at a literal
tree, and no witness binds a hypothesis (so the gate's `consistency_probe` is
not even reached: there are no assumptions that could be inconsistent).

`YieldsNothing` is defined by well-founded recursion, so `decide` cannot reduce
it (`failed to synthesize Decidable`) and `rw [YieldsNothing]` alone does not
fire on a nested position.

WITNESS SHAPE — and the THIRD AUDIT's repair of three hollow witnesses
---------------------------------------------------------------------
The shape originally shipped here was: `intro` the spec, project the clause under
attack by GUESSING the sub-query the recursion should have handled (`h1.2
(Query.mk false []) (by simp)`), then peel `YieldsNothing`. Three of the four
witnesses (`reject-no-recursion`, `reject-depth-one-only`,
`reject-breadth-skip-sib`) used it, and it is HOLLOW on this carrier. Measured,
not argued:

  * The frozen impl's result at a literal input does NOT reduce inside a witness
    file. `simp [implementation_makeEmpty, Id.run]`, `rfl`, `decide +kernel` and
    a hand-written `simp only [...forIn_cons, forIn_nil, bind_pure_comp...]` all
    leave a residual `do PUnit.unit; let x ← ForInStep.yield ...` term (5 builds,
    all exit 1). So gold's membership side-goal `Query.mk false [] ∈ do ...` is
    unprovable for EVERY claimed element, true or false.
  * Consequence: gold's exit code carried no information about the claim. The
    B′ agreement-point forgery — the same script with the projected element moved
    to the one gold ACTUALLY has, i.e. asserting gold is CORRECT there — fails on
    gold with the same `unsolved goals` on the same membership step (exit 1). A
    witness asserting the frozen solution is correct would have been recorded as
    `rejected`. The gate's `_stuck_screen` does not fire here: the message is a
    plain `unsolved goals`, not a `decide`-stall or a `forIn Lean.Loop.mk`
    unification, so nothing flagged it.
  * The type-reveal pair confirms the mechanism: on the RIVAL the projected
    hypothesis reads `false = true ∧ ∀ q ∈ [], YieldsNothing q` (the membership
    was discharged and the equation is genuinely false), while on GOLD the same
    hypothesis reads `match implementation_makeEmpty (Query.mk false []) with
    ...` — never evaluated.

The repaired shape stages the refutation on an EVALUATION instead, and the fix is
one simp lemma: adding `Id.instMonad` (with `Id.run, pure`) collapses the residual
`Id`-monad wrapper that blocked every earlier attempt, so the frozen impl's value
at a literal input computes to a closed literal. Each witness now opens with

    have hv : implementation_makeEmpty <input> = <the RIVAL's literal value> := by
      simp [implementation_makeEmpty, Id.run, pure, Id.instMonad, Query.combined]

then rewrites with it and peels `YieldsNothing` one `unfold`/`simp` per tree level
over the now-literal result. `hv` is a concrete equation between closed trees that
COMPUTES on both sides: True for the rival, False for the frozen solution. That is
what makes the gold-side exit code track the claim. Verified per case: rival exit
0, gold exit 1, and the B′ flipped-claim build (the same script with GOLD's own
literal value substituted) fails on gold at a DIFFERENT point with a visibly
different error (`hv` now holds, `h1 : True`, `⊢ False`) rather than the identical
one — so the error moves when the claim moves.

`reject-top-unmarked`'s WITNESS was not hollow in the third audit's sense — its
gold-side failure was a fully reduced `⊢ False` under `h1 : true = true ∧ ...`,
and the type-reveal pair showed gold `true = true ∧ ...` vs rival
`false = true ∧ ...`, a decided false equation on the marker under attack.

But the FOURTH audit found the defect one level up, in the RIVAL rather than in
the witness: that rival's self-call was the rival itself, so the "keep the input
marker" defect recurred at every level and no node was ever forced. The witness
discriminated honestly; what it discriminated was not the top position it claimed.
Three prose claims rested on the top-only reading and all three were false
(see the note above `_R_TOP`). Both the rival and its prose are repaired here, and
the witness is now staged on `hv` like the other three so that its input's
sub-query is one the rival provably forces. `pts=4` is unchanged, but it is now
four genuinely distinct positions rather than three plus a superset.

BINDER / CLAUSE COVERAGE
------------------------
There is one input binder, `q`, and it is a tree, so "varying the binder" means
varying the tree POSITION each rival is refuted at. The three reject witnesses
probe three DISTINCT input trees, chosen so that no two agree on the position
that discriminates them:

  | case                    | witness input tree                | position attacked |
  |-------------------------|-----------------------------------|-------------------|
  | reject-top-unmarked     | one sub-query, top marker false   | top node's marker |
  | reject-no-recursion     | one sub-query, top marker TRUE    | depth-1 sub-query |
  | reject-breadth-skip-sib | TWO sub-queries, both above marked| a later SIBLING   |
  | reject-depth-one-only   | two nesting levels below the top   | depth-2 sub-query |

Note the second row's top marker is deliberately `true`: it holds the top-node
position at the value that ALREADY satisfies the clause, so the case can only be
discriminated by the sub-query position, and a rival that got the top node right
and the children wrong cannot hide behind it. Conversely the first row's tree
carries a sub-query the rival FORCES correctly (true of the repaired rival, and
measured — see the note above `_R_TOP`; it was NOT true of the rival as
originally shipped, which forced nothing anywhere), so it discriminates only on
the top node. The third row holds BOTH the top node and the FIRST sub-query at
markers that already satisfy the clause, so only a later sibling can be what
discriminates: that isolates the BREADTH position (some sub-queries at a level
handled, others not), which is a different sub-domain from the DEPTH positions
rows 2 and 4 attack. `pts=4`.

Recursive-clause positions are therefore probed along both axes the recursion
has — how FAR down it goes (rows 2, 4) and how MANY siblings it covers at a
level (row 3).

The four reject witnesses were shown to be MUTUALLY non-redundant rather than
assumed to be: each witness was built against each of the other three rivals, a
12-build matrix.

FOURTH-AUDIT CORRECTION. The paragraph here previously reported "eleven of the
twelve fail; the single crossing pair is the breadth witness against
`reject-no-recursion`". Re-measured, the matrix over the AS-SHIPPED rivals had
THREE crossings, not one: the extra two were `reject-no-recursion`'s witness and
`reject-breadth-skip-sib`'s witness against `reject-top-unmarked` (both exit 0).
The cause was the top rival itself, whose self-call was the rival rather than a
corrected sub-result, so it left EVERY marker unforced and was consequently
caught by every witness that looks at any marker. That made the top case a
superset of the others rather than an isolation of the top position, and the
count in this paragraph was wrong because it was never re-run after the breadth
rival was added. The top rival has been repaired to force every node except the
top. On the repaired set, eleven of the twelve builds fail (exit 1) and exactly
ONE crossing survives — the breadth witness against the `reject-no-recursion`
rival (exit 0). That one is the documented, harmless case: a rival that recurses
nowhere also skips the later sibling, so the breadth input refutes it too, while
the converse does not hold (the no-recursion witness against the breadth rival is
exit 1). Neither case is a restatement of the other.

The six builds that isolate the repaired top case are recorded separately: each of
the other three witnesses against the repaired top rival fails (exit 1), and the
top witness fails against each of the other three rivals (exit 1). So the top
position is now genuinely isolated rather than being caught incidentally by every
marker-reading witness.

A fifth input position is covered by the admissibility case below, which is
stated at the same two-sub-query breadth shape but as a POSITIVE.

PORTING NOTES — which nagini cases port, which are OMITTED and why
------------------------------------------------------------------
The nagini sibling contracts FOUR functions (`matches_nothing`, `duplicate`,
`mark_matching_nothing`, `none`) over a flat carrier: a `where_empty: bool` plus
a `child_empty: List[bool]` of one flag per constituent, one level deep. This
bundle models ONE obligation over a genuinely RECURSIVE tree. That is carrier
narrowing in both directions at once, and it is what governs the port:

  * `partial-domain-mark-skip-last` (mark every constituent but the last) PORTS,
    as `reject-no-recursion` / `reject-depth-one-only` / (added by audit)
    `reject-breadth-skip-sib`. On nagini's flat vector "skip the last flag" is
    the natural sub-domain miss; on a tree there are TWO axes, and the port
    initially carried only one. The DEPTH sharpening ("handle this level but not
    the one below") is strictly stronger and nagini's one-level carrier cannot
    express it; but the original BREADTH axis ("handle some sub-queries at a
    level, not the rest") is separately expressible here and was left unprobed,
    since every shipped witness tree had at most one sub-query per level. The
    audit added `reject-breadth-skip-sib` for it. Both directions of the nagini
    argument (a constituent left matching its rows => the combined result still
    emits them) are preserved.
  * `partial-domain-duplicate-fabricate-last-flag` is VACUOUS: it attaches to
    `duplicate`, which is not a modeled function in this bundle, and the property
    it violates (the copy's flags equal the SOURCE's flags elementwise) is a
    faithful-clone obligation. The operation modeled here forces every marker to
    `true` unconditionally, so there is no copy-fidelity clause for a fabricated
    flag to contradict — the fabricated value and the required value coincide.
    Omitted as unmodeled, not as too-hard.
  * `none-mutate-source-no-copy` and `frame-mutation-duplicate-source-write`
    (nagini's two aliasing/permission rivals) are VACUOUS here. They attack a
    shallow SHARE between a clone and its source — a property of Python
    reference aliasing, expressed on nagini via fractional permissions. Lean is
    referentially transparent: `implementation_makeEmpty` returns a fresh tree
    and there is no source to corrupt, so the distinction those rivals abuse
    does not exist on this carrier. Not fabricated a substitute; see the frame
    discussion below for what DOES survive of the frame obligation.
  * `frame-mutation-matches_nothing` is vacuous for the same reason, and doubly
    so: the observable it guards (`matches_nothing`, a pure read of one field) is
    not a modeled function in this bundle at all.
  * `positive-matches-local-read` and `positive-duplicate-read-locals` attach to
    `matches_nothing` / `duplicate`, neither of which is modeled here. Omitted as
    unmodeled, not as too-hard.
  * `positive-mark-local-flag` PORTS as `verify-marker-via-local`, and is joined
    by `verify-map-form`, a second positive in a genuinely different shape
    (`List.map` in place of the accumulator `for`) whose proof had to be
    re-closed for the new impl.
  * `admissibility-f2p-shaped-compound` PORTS, as `admiss-f2p-shaped-compound`
    (added by the second audit). The port had recorded it VACUOUS on the ground
    that the lean obligation is `∀ q : Query, ...` with no precondition
    hypothesis, so "there is nothing to over-constrain". That reason was WRONG:
    it describes the absence of nagini's `Requires` MECHANISM, not the absence of
    the lane. On a total carrier the analogue of PRECOND-TOO-STRONG is the
    obligation being UNSATISFIABLE at exactly an F2P-shaped input, which a
    positive that discharges the spec predicate at that concrete input — by
    evaluation, as `have`s, before closing the frozen obligation verbatim — tests
    directly. The shipped case does that at the F2P shape (a top query combining
    TWO plain sub-queries, none of them yet forced) and is THREE-sided so it
    cannot pass as a tautology about whatever the impl returns: the spec HOLDS
    there, the impl's value there is pinned to LITERALS, and the spec REFUSES at
    that same input the answer that forces only the top node. Both content halves
    were measured load-bearing — flipping the pinned literal and flipping the
    refusal each make the case FAIL (exit 1).
  * The divergence lane (`nonterm-none-self-recursion`,
    `nonterm-none-endless-loop`) ships NO case, but the FIFTH audit re-derived the
    reason and the reason previously recorded here was FALSE. The old text said "a
    diverging implementation cannot be written at all", i.e. that the termination
    checker refuses every diverging shape before any spec question is reached.
    Half of that is measured true and half is measured false:

      - As a total `def`, yes: a self-call on a non-smaller argument is refused by
        `decreasing_by` (built the bare `| .mk e combined =>
        implementation_makeEmpty (Query.mk e combined)` shape — exit 1, and the
        failure is `Tactic 'assumption' failed ... ⊢ ?m ∈ ?m` inside the measure,
        i.e. the termination obligation, never a spec clause).
      - As a `partial def`, NO: prefixing `partial` elaborates the diverging
        definition fine (the only errors in that build are the frozen proof
        script's own `rw`/`.induct` failures at the obligation, exits 1 — the
        DEFINITION is accepted). `partial` is also not an assumption token
        `variant_scope` bans, so the rival is expressible and in scope. The old
        text's blanket "cannot be written at all" is wrong.

    What actually keeps the case off the manifest is the WITNESS half, measured
    two ways. A `partial def` has no equation lemmas, so its value at a literal
    input does not reduce: the value-pinning `hv` shape every other reject case
    here uses makes no progress against it (`simp made no progress`, exit 1), so
    the witness fails on the RIVAL — the half that must succeed. And the
    hypothesis-conditioned form the audit brief prescribes as the fallback is
    VACUOUS here rather than merely hard: conditioning on `hv : implementation_
    makeEmpty (Query.mk false []) = Query.mk false []` and refuting from it
    elaborates against the diverging rival (exit 0) AND against the frozen
    solution (exit 0), because the hypothesis is doing all the work and any impl
    admits the derivation. The gate would record that as `witness-vacuous`. So the
    class is not shippable as a green reject case on this carrier — not because
    the rival is inexpressible, but because nothing can discriminate it.

    This bundle is on lean, which has no `loom.semantics.termination` line at all
    (checked: the option appears in the velvet sibling only), so the "partial"
    reading of that setting — under which a diverging rival verifies vacuously and
    the lane is a spec HOLE — does not apply to the frozen artifact judged here.
    Recorded as a KNOWN LIMIT of the witness protocol on an unreducible impl
    rather than as a vacuous class, since "vacuous" would claim the battery is
    complete and this only claims no witness exists.
  * `AXIOM_TESTS` are dropped: the axiom lane is G-AX's job and this gate ignores
    them. (`meta.json axioms == []` regardless — there is no `opaque`/`axiom` in
    this bundle.)

THE FRAME CLAUSE IS DEFENDED BY THE POSITIVES, NOT BY A RIVAL — a deliberate,
empirically forced omission
---------------------------------------------------------------------------
`toShape result = toShape q` is the one top-level clause with NO reject case, and
the reason is a measured fact about the harness rather than a gap in effort. Two
rivals that violate it were built, and both were REFUTABLE on this carrier — each
had a witness that elaborated against the rival and failed on gold, so each would
have shipped as a green reject case:

  * mark every sub-query correctly, then DROP them (return no sub-queries);
  * mark every sub-query correctly, then DUPLICATE them.

Both were dropped because their `refinement` claim is FALSE. Their faithful real
patches were applied at `base_commit` and the suite was run: both resolve the
F2P and leave the whole `queries` app green (also checked with the sub-query list
reversed, and with an extra sub-query grafted in — 4 structure mutations, all
green on `queries` + `test_explain` + `filtered_relation`). The reason is
visible downstream: once every sub-query is marked, the code that renders a
combined query considers only the sub-queries NOT marked empty, so a marked
sub-query contributes nothing whether it is still present or not — the structure
of an already-emptied combined query is unobservable. A reject case over this
clause would therefore assert "a verifying rival here is a real
verify-does-not-imply-resolve break" when in fact its patch RESOLVES. That is
precisely the corrupt artifact this battery must not ship, so the clause is left
defended by the two positives (both preserve the structure exactly and both must
verify) and the gap is recorded here instead. The clause is not idle in the spec:
it is what stops an impl from returning `Query.mk true []` for every input, which
is not the modeled operation; it is simply not a clause whose violation the F2P
observes.

AUDIT CONFIRMATION of this omission. The reason above was re-derived from the real
code rather than taken on trust: the routine that renders a combined query does
filter its operands on the emptiness marker before compiling them, so once every
sub-query is marked, a marked sub-query contributes nothing whether it is still
present or not. The disposition (no reject case) is right and the stated reason is
the true one. The audit additionally rebuilt both rivals as attack-D probes and
confirmed the SPEC does reject them — drop-all-sub-queries and reverse-the-
siblings each fail to verify — so this clause is not merely unprobed prose, it is
known to bite. It stays out of SPEC_TESTS because a green reject case here would
ship a false resolve-claim, which is the more expensive error.

Every reject case carries a `witness`: a Lean snippet negating the spec predicate
at one concrete input, checked in a file with the frozen obligation removed. It
must (1) elaborate against the rival and (2) FAIL against the frozen solution.
All four below were built BOTH ways with scripts/lean_verify.sh and seen to
discriminate; both positives were built and their proofs close.

That two-build check is NECESSARY BUT NOT SUFFICIENT, and this battery is the
proof: three of these four witnesses passed both halves while being hollow,
because gold's half failed on a step that could not have succeeded for any claim.
See the WITNESS SHAPE section above for the measurement and the repair. The
standard applied here is stronger than the gate's: each reject case's gold-side
failure must MOVE when the claim moves (attack B′), which is checked by
substituting gold's own literal value into the same script and confirming a
different error.

WHY SPEC-TOO-WEAK IS UNREACHABLE HERE (independent audit result)
---------------------------------------------------------------
The postcondition is SINGLE-VALUED, and that was proven rather than argued. The
audit built `problem_spec_makeEmpty q r1 → problem_spec_makeEmpty q r2 → r1 = r2`
on top of the frozen definitions (by induction on the tree: `YieldsNothing` pins
every marker to `true` at every level, and `toShape r = toShape q` pins the exact
nesting, so the two results are structurally identical and markerwise equal),
and from it `(∀ q, problem_spec_makeEmpty q (f q)) → ∀ q, f q =
implementation_makeEmpty q`. Elaborated at exit 0 with no `sorry`.

RE-DERIVED INDEPENDENTLY by the second audit rather than taken from the record:
`audit_spec_pins_impl : ∀ q r, problem_spec_makeEmpty q r → r =
implementation_makeEmpty q` (via a list lemma lifting the pointwise pinning
through the shape equality), and from it both `audit_no_weak_spec` and
`audit_spec_unique`. Freshly authored proof, exit 0, no `sorry`.

Consequence: ANY impl satisfying the frozen spec agrees with the frozen impl at
every input, so no wrong implementation can verify and no amount of extra rival
construction can find a spec hole. That is why the reject lane's job here is
attribution (each rejection traceable to a named clause at a named position)
rather than hole-hunting, and why the four rivals are chosen to cover distinct
POSITIONS rather than to be numerous. Attacks D and E were still run: three new
wrong impls (drop all sub-queries; reverse the sibling order; recurse into the
first sibling only) were all rejected, and two new CORRECT reshapes (reverse-
accumulate-then-reverse, and `foldr` in place of the loop) both verified — no
SPEC-TOO-STRONG. The breadth rival was kept as a case; the other two D probes
attacked the frame clause and are discussed directly below.

SECOND AUDIT, attacks D and E again, with six further wrong impls the battery
does not contain — graft an extra sub-query onto every node; leave a LEAF's own
marker unforced while handling every non-leaf correctly; reverse the sibling
order; recurse to depth 2 but no further; drop all sub-queries; duplicate the
frozen shape with a fabricated child. Every one is REJECTED by the spec, and each
was additionally given its own witness which held of the rival (exit 0) and
failed on the frozen solution (exit 1), so the rejections are the spec's and not
the tactic script's. Two further CORRECT reshapes were built: `foldl` with a
tail-append accumulator VERIFIES (exit 0), as does the `foldr` reshape. Two more
reshapes (an outer `reverse ∘ map ∘ reverse`, and a prepend-then-reverse loop)
could not be closed — in both cases the build failed inside MY OWN bridge lemma
(a `decreasing_by` that could not see through `List.mem_reverse`, and a `rw` that
could not find the `forIn` pattern after a `congr 1` split), never at the spec
clauses, so they are recorded as UNCERTAIN rather than as spec holes. Consistent
with the single-valuedness proof, `spec_holes` is empty.

FIFTH AUDIT — what was re-run, and the one claim it had to correct
-----------------------------------------------------------------
Everything below is a build this audit performed itself, not a record it read.

  * STATEMENT INTEGRITY. Every case's `theorem correct_makeEmpty` statement is
    byte-identical to the frozen one, and every case's region diff is confined to
    the regions its lane is allowed to touch (`impl` for the four rivals and
    `verify-marker-via-local`; `impl`+`proof` for `verify-map-form`; `proof` only
    for the admissibility case). No reformatted hypothesis anywhere.
  * WITNESS DISCRIMINATION, re-derived. All four: rival exit 0, gold exit 1. Gold's
    failure is at the `hv` line in every case, and it is an EVALUATION verdict, not
    a stall — the reveal build confirms `simp [implementation_makeEmpty, Id.run,
    pure, Id.instMonad]` closes the TRUE equation for the frozen impl at all three
    witness inputs (exit 0), so `simp` does reduce here and gold's exit 1 is a
    decided false equation between closed trees.
  * THE FORGERY PAIR (B′) for all four, since none of the four gold signatures is a
    plain evaluation — each is an `unsolved goals` residue. Substituting GOLD's own
    literal value (i.e. claiming the frozen solution is CORRECT at that input)
    moves the error in every case: gold then DISCHARGES `hv` and the residue
    appears a line later with a different context — `h1 : True` for
    `reject-no-recursion`, `reject-depth-one-only` and `reject-breadth-skip-sib`
    (`simp` PROVED the marker clause for the frozen impl), and `h1 :
    YieldsNothing (Query.mk true [])` for `reject-top-unmarked`. The real witnesses
    leave `hv` itself unproven. So gold's exit code tracks the claim: none of the
    four is hollow.
  * NON-REDUNDANCY, the 12-build matrix, re-measured from scratch rather than
    trusted: eleven exit 1 and exactly one crossing survives, `reject-breadth-skip-
    sib`'s witness against the `reject-no-recursion` rival (exit 0) — which is the
    single crossing the paragraph above documents, and the converse is exit 1. The
    six builds isolating the repaired top rival all came back exit 1 as recorded.
  * ATTACK D, six further wrong impls this battery does not contain: skip the LAST
    sub-query (nagini's original axis, at the one position no shipped rival holds),
    leave a LEAF's own marker at its input value, graft an extra sub-query onto
    every node, drop all sub-queries, return `e && true` as the marker, and a
    diverging shape. NONE verifies, so no spec hole; consistent with the
    single-valuedness result, which this audit also re-derived from scratch as
    `audit_shape_pins / audit_spec_pins_impl / audit_no_weak_spec` on top of the
    frozen definitions — freshly authored, exit 0, zero `sorry`.
  * ATTACK E, three further correct reshapes: a `foldr` traversal VERIFIES (exit 0)
    and a `List.concat` accumulator VERIFIES (exit 0), so the spec accepts
    structure-preserving traversals it was not written against. A
    `reverse ∘ map ∘ reverse` reshape again failed inside the audit's own
    `decreasing_by` bridge (`Tactic 'assumption' failed ... ⊢ ?m ∈ List.reverse ?m`)
    and never at a spec clause, so it stays UNCERTAIN, not a hole. No
    SPEC-TOO-STRONG.
  * THE ADMISSIBILITY CASE's two content halves, re-measured independently: flipping
    the pinned literal fails (exit 1, `⊢ Query.mk true [Query.mk true [], Query.mk
    true []] = Query.mk true [Query.mk false [], Query.mk true []]` — the spec's own
    value contradicts the flipped one), and flipping the refusal fails BOTH naively
    (exit 1) and when honestly re-proven with the same script `_adm_holds` uses
    (exit 1, unsolved at `case refine_1.inl`) — so the spec genuinely refuses the
    top-only answer at that input and the clause is not inert.
  * The `decide` claim in the WITNESS SHAPE section holds: `YieldsNothing` at a
    literal is `failed to synthesize Decidable` (exit 1), so the value-pinning
    shape is required rather than preferred.
  * The frame-clause omission's downstream reason was re-read at `base_commit`: the
    routine that renders a combined query builds its per-operand compilers from
    `combined_queries` FILTERED on the emptiness marker, so once every sub-query is
    marked the structure below is unobservable. The recorded reason is the true one.
  * `reject-depth-one-only`'s refinement grounds itself on the same module
    exercising a combined query whose operand is itself combined; that call site was
    located and it exists, so the near-miss sub-domain the case claims is one the
    module really reaches.
  * ONE CORRECTION, in the divergence-lane paragraph above: its stated reason ("a
    diverging implementation cannot be written at all") was measurably false — a
    `partial def` elaborates. The disposition (no case) is unchanged, but the true
    reason is that no witness can discriminate such a rival, which is now recorded
    as a known limit rather than as a vacuous class. That paragraph carries the
    exit codes.
"""
from pathlib import Path

INSTANCE = "django__django-13158"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence; assert it matched, so silent drift in
    Solution.lean fails loudly instead of yielding a no-op variant."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks. `_GOLD_BODY` is the whole impl region body including its
# `decreasing_by`; `_GOLD_PROOF` is the whole proof-region body. Both are
# strictly inside the regions a variant may edit.
# ---------------------------------------------------------------------------

_GOLD_BODY = (
    "  | .mk _ combined => Id.run do\n"
    "    -- Force this node's own row-selection to match nothing.\n"
    "    let mut subs : List Query := []\n"
    "    -- Recurse into each combined sub-query so it, too, returns nothing.\n"
    "    for sub in combined do\n"
    "      subs := subs ++ [implementation_makeEmpty sub]\n"
    "    return Query.mk true subs\n"
    "decreasing_by all_goals (have h := List.sizeOf_lt_of_mem ‹_ ∈ _›; "
    "simp_all; omega)\n"
)

_DEC = ("decreasing_by all_goals (have h := List.sizeOf_lt_of_mem ‹_ ∈ _›; "
        "simp_all; omega)\n")

# The frozen proof body, reused verbatim by the positive whose impl reduces the
# same way, and partly reused by the other.
_lo = _BASE.index("-- proof-start\n") + len("-- proof-start\n")
_hi = _BASE.index("-- proof-end")
_GOLD_PROOF = _BASE[_lo:_hi]
assert "theorem correct_makeEmpty" in _GOLD_PROOF


def _impl(body: str) -> str:
    return _swap(_BASE, _GOLD_BODY, body)


def _impl_proof(body: str, proof: str) -> str:
    return _swap(_impl(body), _GOLD_PROOF, proof)


# ===========================================================================
# UNIQUENESS (expect="reject") — a wrong impl the frozen spec must refute
# ===========================================================================

# (1) EVERY node's own marker is left at whatever the input carried; only the
#     combination structure is rebuilt. Attacks the FIRST conjunct of
#     `YieldsNothing` at the TOP position — and, because the self-call carries the
#     same defect all the way down, at every DEEPER position too.
#
# FOURTH-AUDIT REPAIR of the rival itself, not just of its prose. The shape
# shipped here was
#
#     | .mk e combined => ... subs := subs ++ [implementation_makeEmpty sub] ...
#                             return Query.mk e subs
#
# whose self-call is `implementation_makeEmpty`, i.e. the RIVAL, so the "keep the
# input marker" defect recurs at every level and NO node is ever forced. Three
# prose claims rested on it being top-only and all three are false of it,
# measured: (a) the comment said "the single sub-query the rival DOES mark
# correctly" — it does not: at `Query.mk false [Query.mk false []]` the rival
# returns `Query.mk false [Query.mk false []]`, the input unchanged (build: the
# claim `= Query.mk true [Query.mk true []]` fails on this rival, exit 1, while
# `= Query.mk false [Query.mk false []]` succeeds, exit 0); (b) the rationale
# said the refutation is "attributable to the marker conjunct alone" at the TOP —
# it is attributable to the marker conjunct at EVERY level, so the case did not
# isolate the position it claimed; (c) the manifest's non-redundancy paragraph
# claimed exactly ONE crossing in the 12-build matrix, and the real matrix has
# THREE: this rival, marking nothing anywhere, is ALSO caught by
# `reject-no-recursion`'s witness (exit 0) and by `reject-breadth-skip-sib`'s
# (exit 0), because a rival that forces no marker at all fails every one of those
# inputs too.
#
# The repair forces every node EXCEPT the top, so the top marker is genuinely the
# only discriminating position. `(implementation_makeEmpty sub).combined` reuses
# the rival's own recursion for the structure below while `Query.mk true`
# overwrites the marker the rival would have left, which is what makes the defect
# strictly top-local. Re-measured on the repaired rival: all SIX cross-builds fail
# (each of the other three witnesses against this rival, exit 1; this witness
# against each of the other three rivals, exit 1), so the case is now isolated on
# the top position rather than being a superset of the other three.
_R_TOP = _impl(
    "  | .mk e combined => Id.run do\n"
    "    let mut subs : List Query := []\n"
    "    for sub in combined do\n"
    "      subs := subs ++ [Query.mk true (implementation_makeEmpty sub).combined]\n"
    "    return Query.mk e subs\n" + _DEC
)

# Refuted at a tree whose top marker is false and whose single sub-query the
# rival DOES force correctly (now true of the repaired rival, and measured: the
# rival's value at this input is `Query.mk false [Query.mk true []]`), so only the
# top position can discriminate. The input carries that sub-query on purpose: at
# the bare leaf `Query.mk false []` the recursive conjunct is vacuous for a second
# reason (there is nothing to recurse into), so a leaf would leave "the recursion
# is irrelevant here" resting on the empty list rather than on a sub-query the
# rival handles CORRECTLY.
#
# Staged on `hv` like the other three, so the gold-side exit code tracks the
# claim: `hv` computes to True for the rival and to False for the frozen solution.
# Measured — rival exit 0, gold exit 1 with `⊢ False` under an unsolved
# `hv`; and the B′ forgery (the same script with GOLD's own literal
# `Query.mk true [Query.mk true []]` substituted, i.e. claiming gold is CORRECT
# here) fails on gold at a DIFFERENT point with a visibly different context (`hv`
# now DISCHARGED and `h1 : YieldsNothing (Query.mk true [])` present, where the
# real witness leaves `hv` itself unproven). The error moves when the claim moves.
_W_TOP = """example : ¬ problem_spec_makeEmpty
    (Query.mk false [Query.mk false []])
    (implementation_makeEmpty (Query.mk false [Query.mk false []])) := by
  intro h
  -- Pin this implementation's value at this input to a closed LITERAL, by
  -- evaluation: the sub-query IS forced, only the TOP marker is not. True for the
  -- rival, FALSE for the frozen solution.
  have hv : implementation_makeEmpty (Query.mk false [Query.mk false []])
      = Query.mk false [Query.mk true []] := by
    simp [implementation_makeEmpty, Id.run, pure, Id.instMonad, Query.combined]
  rw [hv] at h
  -- The result is a literal now, so the spec's own predicate EVALUATES and the
  -- unforced TOP marker surfaces as `false = true`.
  have h1 := h.1
  unfold YieldsNothing at h1
  simp at h1
"""

# (2) No recursion at all: force this node's marker and carry the combined
#     sub-queries through untouched. The pre-fix shape. Attacks the RECURSIVE
#     conjunct of `YieldsNothing` at DEPTH 1.
_R_NOREC = _impl(
    "  | .mk _ combined => Id.run do\n"
    "    return Query.mk true combined\n"
)

# Refuted at a tree whose top marker is ALREADY true — so the top position
# cannot be what discriminates — carrying one unmarked sub-query.
#
# THIRD-AUDIT REPAIR (this witness was HOLLOW as shipped; see the WITNESS SHAPE
# note below). The refutation is now staged on `hv`, which pins the impl's value
# at this input to a closed LITERAL by EVALUATION. That equation computes to True
# for the rival and to False for the frozen solution, so the gold-side exit code
# is a decided false equation between closed trees rather than a tactic that
# stalled on an unreduced `forIn`.
_W_NOREC = """example : ¬ problem_spec_makeEmpty
    (Query.mk true [Query.mk false []])
    (implementation_makeEmpty (Query.mk true [Query.mk false []])) := by
  intro h
  -- Pin this implementation's value at this input to a closed LITERAL, by
  -- evaluation. This equation is what carries the discrimination: it computes to
  -- True for the rival and to False for the frozen solution.
  have hv : implementation_makeEmpty (Query.mk true [Query.mk false []])
      = Query.mk true [Query.mk false []] := by
    simp [implementation_makeEmpty, Id.run, pure, Id.instMonad, Query.combined]
  rw [hv] at h
  -- The result is a literal now, so the spec's own recursive predicate
  -- EVALUATES and the unforced sub-query marker surfaces as `false = true`.
  have h1 := h.1
  unfold YieldsNothing at h1
  simp at h1
  unfold YieldsNothing at h1
  simp at h1
"""

# (3) Recurse exactly ONE level: force this node's marker and each direct
#     sub-query's own marker, but do not descend into the sub-queries' own
#     combined lists. A NEAR-MISS of (2): it agrees with gold on every tree of
#     depth <= 1, so it needs its own witness at a strictly deeper input.
#     Measured under audit: (2)'s witness, built against THIS rival, exits 1 —
#     confirming the two rivals really are discriminated at different inputs and
#     that this case is not a restatement of (2).
_R_DEPTH1 = _impl(
    "  | .mk _ combined => Id.run do\n"
    "    let mut subs : List Query := []\n"
    "    for sub in combined do\n"
    "      subs := subs ++ [Query.mk true sub.combined]\n"
    "    return Query.mk true subs\n"
)

# Refuted at a tree with TWO levels below the top: the rival marks the depth-1
# sub-query correctly and leaves the depth-2 one untouched.
#
# THIRD-AUDIT REPAIR (hollow as shipped — see the WITNESS SHAPE note). Same
# value-pinning shape as `_W_NOREC`; the depth-2 marker surfaces after peeling
# `YieldsNothing` once per tree level over the now-literal result.
_W_DEPTH1 = """example : ¬ problem_spec_makeEmpty
    (Query.mk false [Query.mk false [Query.mk false []]])
    (implementation_makeEmpty (Query.mk false [Query.mk false [Query.mk false []]])) := by
  intro h
  -- Pin this implementation's value at this input to a closed LITERAL, by
  -- evaluation: True for the rival, FALSE for the frozen solution.
  have hv : implementation_makeEmpty (Query.mk false [Query.mk false [Query.mk false []]])
      = Query.mk true [Query.mk true [Query.mk false []]] := by
    simp [implementation_makeEmpty, Id.run, pure, Id.instMonad, Query.combined]
  rw [hv] at h
  -- One peel per tree level over the literal result; the DEPTH-2 marker is the
  -- one that surfaces as `false = true`.
  have h1 := h.1
  unfold YieldsNothing at h1
  simp at h1
  unfold YieldsNothing at h1
  simp at h1
  unfold YieldsNothing at h1
  simp at h1
"""

# (4) BREADTH miss (added by audit): recurse into the FIRST combined sub-query
#     only and carry the remaining siblings through untouched. This is the
#     tree-carrier form of nagini's `partial-domain-mark-skip-last` on its
#     original axis — some sub-queries at a level handled, the rest not — and it
#     was the one recursive position the ported battery left unattacked: the
#     three shipped rivals all vary how FAR the recursion descends, and every one
#     of their witness trees has at most ONE sub-query per level, so none of them
#     can see a skipped SIBLING. It is fully recursive in depth (it self-calls on
#     the head), so a depth witness does not catch it either.
_R_BREADTH = _impl(
    "  | .mk _ combined => Id.run do\n"
    "    match combined with\n"
    "    | [] => return Query.mk true []\n"
    "    | c :: rest => return Query.mk true (implementation_makeEmpty c :: rest)\n"
    "decreasing_by all_goals (simp_wf; omega)\n"
)

# Refuted at a tree with TWO sub-queries whose top marker AND whose first
# sub-query's marker are ALREADY true — so neither the top position nor the
# recursed-into head can be what discriminates — while the SECOND sibling is
# unmarked.
#
# THIRD-AUDIT REPAIR (hollow as shipped — see the WITNESS SHAPE note). Same
# value-pinning shape; the skipped SECOND sibling's marker is what surfaces.
_W_BREADTH = """example : ¬ problem_spec_makeEmpty
    (Query.mk true [Query.mk true [], Query.mk false []])
    (implementation_makeEmpty (Query.mk true [Query.mk true [], Query.mk false []])) := by
  intro h
  -- Pin this implementation's value at this input to a closed LITERAL, by
  -- evaluation: True for the rival, FALSE for the frozen solution.
  have hv : implementation_makeEmpty (Query.mk true [Query.mk true [], Query.mk false []])
      = Query.mk true [Query.mk true [], Query.mk false []] := by
    simp [implementation_makeEmpty, Id.run, pure, Id.instMonad, Query.combined]
  rw [hv] at h
  -- The literal result makes the recursive predicate evaluate; the SECOND
  -- sibling's unforced marker surfaces as `false = true`.
  have h1 := h.1
  unfold YieldsNothing at h1
  simp at h1
  unfold YieldsNothing at h1
  simp at h1
"""


# ===========================================================================
# SOUNDNESS (expect="verify") — structurally different but CORRECT impls
# ===========================================================================

# (4) Same accumulator loop, but the recursive result is bound to a local before
#     being appended and the marker is written through a typed local. This is the
#     port of nagini's `positive-mark-local-flag`. The `let`s zeta-reduce, so the
#     frozen proof body closes it verbatim (confirmed by build).
_P_LOCAL = _impl(
    "  | .mk _ combined => Id.run do\n"
    "    let mut subs : List Query := []\n"
    "    for sub in combined do\n"
    "      let done := implementation_makeEmpty sub\n"
    "      subs := subs ++ [done]\n"
    "    let mark : Bool := true\n"
    "    return Query.mk mark subs\n" + _DEC
)

# (5) A genuinely different SHAPE: the accumulator `for` is replaced by a single
#     `List.map`. Same value at every input, but the impl no longer reduces
#     through `forIn`, so the frozen `forIn_aux` bridge lemma is dead weight and
#     `impl_eq` becomes near-definitional. The proof is re-closed for the new
#     shape — the `theorem correct_makeEmpty` STATEMENT is byte-identical and the
#     obligation is fully reproven (no new lemma, no `sorry`).
_P_MAP_PROOF = """theorem correct_makeEmpty :
    ∀ q : Query, problem_spec_makeEmpty q (implementation_makeEmpty q) := by
  have impl_eq : ∀ (e : Bool) (combined : List Query),
      implementation_makeEmpty (.mk e combined) = Query.mk true (combined.map implementation_makeEmpty) := by
    intro e combined
    conv_lhs => rw [implementation_makeEmpty]
    simp only [Id.run, pure]
  intro q
  induction q using implementation_makeEmpty.induct with
  | _ e combined ih =>
    rw [impl_eq]
    constructor
    · show YieldsNothing (Query.mk true _)
      rw [YieldsNothing]
      refine ⟨rfl, ?_⟩
      intro qq hqq
      simp only [List.mem_map] at hqq
      obtain ⟨sub, hsub, rfl⟩ := hqq
      exact (ih sub hsub).1
    · show toShape (Query.mk true _) = toShape (Query.mk e combined)
      rw [toShape, toShape]
      congr 1
      rw [List.map_map]
      apply List.map_congr_left
      intro sub hsub
      exact (ih sub hsub).2

"""

_P_MAP = _impl_proof(
    "  | .mk _ combined => Id.run do\n"
    "    return Query.mk true (combined.map implementation_makeEmpty)\n" + _DEC,
    _P_MAP_PROOF,
)


# ===========================================================================
# ADMISSIBILITY (expect="verify") — the obligation is SATISFIABLE at an
# F2P-shaped input, which is the total-carrier analogue of PRECOND-TOO-STRONG
# ===========================================================================
# Added by the second audit. The first port dropped this lane on the ground that
# the frozen obligation carries no precondition hypothesis, so there was nothing
# to over-constrain. That is the absence of nagini's `Requires` MECHANISM, not
# the absence of the lane: on a total carrier the counterpart of
# PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at exactly an
# F2P-shaped input. So the case discharges the spec predicate at one such input
# BY EVALUATION, as `have`s inside the existing tactic body, and then closes the
# frozen obligation verbatim — the `theorem correct_makeEmpty` statement stays
# byte-identical, no new declaration, no lemma, no `sorry`.
#
# The F2P shape is a top query that COMBINES TWO plain sub-queries, none of them
# yet forced. It is three-sided so it cannot pass as a definitional tautology
# about whatever the impl happens to return:
#   (a) the spec HOLDS at that input, stated over a LITERAL result rather than
#       over `implementation_makeEmpty`'s own output (the latter would just be
#       the frozen theorem specialized, closable by `exact correct_makeEmpty _`,
#       and would pass even if the spec pinned the wrong value);
#   (b) the impl's value there is pinned to those same literals, so (a) says
#       something about the result and not merely about its own subject;
#   (c) at that SAME input the spec REFUSES the answer that forces only the top
#       node, so the satisfiable point is also the discriminating one.
# Both content halves were measured load-bearing rather than asserted to be:
# flipping the pinned literal (exit 1) and flipping the refusal (exit 1) each
# break the case, while the case itself elaborates at exit 0.
_PROOF_INTRO = ("  intro q\n"
                "  induction q using implementation_makeEmpty.induct with\n")
assert _GOLD_PROOF.count(_PROOF_INTRO) == 1

_ADMISS_HAVES = """  -- ADMISSIBILITY: the obligation is SATISFIABLE at an F2P-shaped input --
  -- a top query that COMBINES TWO plain sub-queries, none of them yet forced.
  -- Discharged by evaluation here, before the frozen obligation is closed
  -- verbatim below. Three-sided, so it is not a tautology about whatever the
  -- impl happens to return.
  have _adm_holds : problem_spec_makeEmpty
      (Query.mk false [Query.mk false [], Query.mk false []])
      (Query.mk true [Query.mk true [], Query.mk true []]) := by
    refine ⟨?_, ?_⟩
    · unfold YieldsNothing
      refine ⟨rfl, ?_⟩
      intro qq hqq
      simp only [List.mem_cons, List.not_mem_nil, or_false] at hqq
      rcases hqq with rfl | rfl
      all_goals (unfold YieldsNothing; simp)
    · simp [toShape]
  -- The impl's value at that input, pinned to those same LITERALS, so the
  -- clause above asserts something about the result rather than about its own
  -- subject. (A `have` of the form `problem_spec _ (implementation_ _)` would be
  -- the frozen theorem specialized and would hold of a spec pinning any value.)
  have _adm_pinned : implementation_makeEmpty
      (Query.mk false [Query.mk false [], Query.mk false []])
      = Query.mk true [Query.mk true [], Query.mk true []] := by
    simp only [impl_eq, List.map_cons, List.map_nil]
  -- And at that SAME input the spec REFUSES the answer that forces only the top
  -- node, so the satisfiable point is also the discriminating one.
  have _adm_refuses : ¬ problem_spec_makeEmpty
      (Query.mk false [Query.mk false [], Query.mk false []])
      (Query.mk true [Query.mk false [], Query.mk false []]) := by
    intro hcon
    have hc1 := hcon.1
    unfold YieldsNothing at hc1
    have hc2 := hc1.2 (Query.mk false []) (by simp)
    unfold YieldsNothing at hc2
    simp at hc2
"""

_ADMISS = _swap(_BASE, _PROOF_INTRO, _ADMISS_HAVES + _PROOF_INTRO)


SPEC_TESTS = [
    # ------------------------------------------------------------------ rivals
    {
        "id": "reject-top-unmarked",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_TOP,
        "rationale": (
            "Violates the FIRST conjunct of `YieldsNothing result` at the TOP "
            "node: the returned node's own marker is whatever the input carried "
            "instead of being forced, while every node BELOW it is forced "
            "correctly. Refuted at `Query.mk false [Query.mk false []]`, whose "
            "single sub-query the rival does force (measured: the rival's value "
            "there is `Query.mk false [Query.mk true []]`), so the top node is "
            "the only position that can be the source of the contradiction. The "
            "second spec clause `toShape result = toShape q` still holds of this "
            "rival, so the rejection is attributable to the marker conjunct at "
            "the top position alone. AUDIT CORRECTION — the earlier text named "
            "the refutation input as the bare leaf `Query.mk false []`, which is "
            "not the input the witness uses, and the rival it described left "
            "EVERY marker unforced rather than only the top one, so the "
            "'attributable to the top position' claim was false of it. Both the "
            "rival and this text were repaired; the six cross-builds that isolate "
            "the position are recorded above the rival."
        ),
        "refinement": (
            "A patch that recursed into every combined sub-query but never "
            "forced the top query's own row-selection is not the modeled "
            "operation: forcing the node's OWN row-selection is the whole of "
            "the pre-existing behavior, and the change under study only ADDS "
            "the recursion on top of it. AUDIT CORRECTION — the honest scope "
            "of the F2P grounding is narrower than a resolve/not-resolve "
            "claim, and the earlier text here overstated it. For a node that "
            "combines sub-queries, the rendered result is assembled from the "
            "sub-queries alone, so the top node's own marker is not what the "
            "single F2P observes; the F2P is discriminated by the recursive "
            "clause (see `reject-no-recursion`), not by this one. What DOES "
            "ground this rival is the plain non-combined use of the same "
            "operation, which several sibling tests in the same module exercise "
            "and which reads the node's own marker directly: dropping the "
            "self-force would regress those. Not re-measured under this audit, "
            "so it is stated as the reading of the call sites rather than as a "
            "suite measurement. The clause is in any case pinned by the spec, "
            "which the uniqueness proof below shows is single-valued."
        ),
        "witness": _W_TOP,
    },
    {
        "id": "reject-no-recursion",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_NOREC,
        "rationale": (
            "Violates the RECURSIVE conjunct of `YieldsNothing result`: this "
            "node's own marker is forced, but the combined sub-queries are "
            "carried through with their input markers, so the guarantee fails "
            "one level down. Refuted at `Query.mk true [Query.mk false []]`, "
            "whose top marker is deliberately ALREADY true so that the top "
            "position cannot be what discriminates — only the depth-1 "
            "sub-query can be. This is the clause the whole behavior change "
            "turns on."
        ),
        "refinement": (
            "This is exactly the unfixed behavior: forcing only the top node "
            "empty. Measured at base_commit, the F2P fails with the combined "
            "query returning all four rows instead of none, since a node's "
            "result is the combination of its sub-queries' results and each "
            "unforced sub-query still contributes its own. A patch of this "
            "shape does not resolve the instance, so a rival that verified "
            "here would be a true verify-does-not-imply-resolve break."
        ),
        "witness": _W_NOREC,
    },
    {
        "id": "reject-depth-one-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_DEPTH1,
        "rationale": (
            "A NEAR-MISS of `reject-no-recursion`: it forces this node's marker "
            "AND each direct sub-query's own marker, but does not descend into "
            "those sub-queries' own combined lists, so `YieldsNothing` fails at "
            "DEPTH 2. Because it agrees with the frozen solution on every tree "
            "of depth <= 1, the witness for `reject-no-recursion` would not "
            "discriminate it; it therefore carries its own witness at a "
            "strictly deeper input, so the sub-domain its rationale claims is "
            "the sub-domain the manifest actually demonstrates. This is the "
            "tree-carrier sharpening of nagini's skip-a-constituent rival: the "
            "combination nests to any depth, so handling one level is not "
            "handling all of them."
        ),
        "refinement": (
            "A patch that forced each direct sub-query's own row-selection "
            "without recursing (an inlined one-level version of the fix) leaves "
            "any nested combined sub-query still selecting its rows. It happens "
            "to satisfy the single F2P, whose combined query is one level deep "
            "(two plain operands) — but it is not the modeled behavior, which is "
            "the whole-tree guarantee: the combination can nest, and the "
            "operation must hold of every sub-query recursively. The spec pins "
            "the recursive guarantee rather than a depth-1 approximation of it, "
            "so this rival must be refuted. Honest scope, stated here rather "
            "than deferred elsewhere: of the four rivals this is the ONE whose "
            "faithful patch is not known to break the single F2P, because that "
            "test combines two plain operands and so never reaches depth 2. It "
            "is grounded on the modeled behavior instead — the combination nests "
            "to any depth (the same module exercises a combined query whose "
            "operand is itself a combined query), and the operation must hold of "
            "every sub-query recursively, not just of the first level."
        ),
        "witness": _W_DEPTH1,
    },
    {
        "id": "reject-breadth-skip-sib",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_BREADTH,
        "rationale": (
            "Added by audit to close the one recursive position the battery left "
            "unprobed. Violates the RECURSIVE conjunct of `YieldsNothing result` "
            "in BREADTH rather than in depth: the operation is applied to the "
            "first combined sub-query and the remaining siblings are carried "
            "through with their input markers. The three other rivals all vary "
            "how far the recursion DESCENDS, and each of their witness trees has "
            "at most one sub-query per level, so none of them discriminates a "
            "skipped sibling; conversely this rival descends fully on the head, "
            "so the depth witnesses do not catch it. Refuted at "
            "`Query.mk true [Query.mk true [], Query.mk false []]`, whose top "
            "marker AND whose first sub-query's marker are deliberately ALREADY "
            "true, so only the second sibling can be what discriminates."
        ),
        "refinement": (
            "This is the tree-carrier form of nagini's skip-a-constituent rival "
            "on its original axis. A patch that forced only the first of the "
            "combined sub-queries empty leaves every later sibling still "
            "selecting its own rows, and a node's result is the combination of "
            "all of them — so the combined query keeps emitting the later "
            "operands' rows and the empty-result guarantee fails. The single F2P "
            "combines exactly two operands, so it observes this directly: the "
            "second operand's rows would still come back where none are "
            "expected. A patch of this shape does not resolve the instance, "
            "which makes a rival that verified here a true "
            "verify-does-not-imply-resolve break."
        ),
        "witness": _W_BREADTH,
    },
    # ---------------------------------------------------------------- positives
    {
        "id": "verify-marker-via-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _P_LOCAL,
        "rationale": (
            "Structurally different but CORRECT: the recursive result is bound "
            "to a local before being appended and the forced marker is written "
            "through a typed local rather than as a literal. Same value at every "
            "input, and both spec clauses are preserved (the sub-query list is "
            "built in the same order, so the shape equality is untouched). The "
            "port of nagini's `positive-mark-local-flag`. Must verify, else "
            "SPEC-TOO-STRONG — the spec would be over-fitted to one executable "
            "spelling of the same computation."
        ),
    },
    {
        "id": "verify-map-form",
        "kind": "soundness",
        "expect": "verify",
        "module": _P_MAP,
        "rationale": (
            "A genuinely different impl SHAPE: the accumulator loop over the "
            "combined sub-queries is replaced by a single structural map, so the "
            "impl no longer reduces through the frozen proof's `forIn` bridge "
            "and the obligation had to be re-closed (the `theorem "
            "correct_makeEmpty` statement is byte-identical; only the tactic "
            "body differs, with no new lemma and nothing assumed). This is the "
            "positive that actually exercises the frame clause `toShape result = "
            "toShape q`: it rebuilds the sub-query list by a different route, so "
            "verifying attests that the spec accepts any structure-preserving "
            "traversal rather than one particular loop. Must verify, else "
            "SPEC-TOO-STRONG."
        ),
    },
    # ------------------------------------------------------------ admissibility
    {
        "id": "admiss-f2p-shaped-compound",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "The ADMISSIBILITY lane, ported by the second audit from nagini's "
            "`admissibility-f2p-shaped-compound`. The first port dropped it as "
            "vacuous because the frozen obligation is a bare `∀ q : Query, ...` "
            "with no precondition hypothesis; that reason names the absence of "
            "nagini's `Requires` MECHANISM, not the absence of the lane. On this "
            "total carrier the counterpart of PRECOND-TOO-STRONG is the "
            "obligation being UNSATISFIABLE at exactly an F2P-shaped input, so "
            "this case discharges the spec predicate at one — a top query that "
            "COMBINES TWO plain sub-queries, none of them yet forced, which is "
            "the configuration the modeled operation exists to serve. It is "
            "three-sided so it cannot pass as a tautology about whatever the impl "
            "returns: the spec HOLDS there at a LITERAL result, the impl's value "
            "there is pinned to those same literals, and at that same input the "
            "spec REFUSES the answer that forces only the top node — so the "
            "satisfiable point is also the discriminating one. Stating the first "
            "clause over a literal rather than over "
            "`implementation_makeEmpty`'s own output is what gives it content: "
            "the latter is the frozen theorem specialized (`exact "
            "correct_makeEmpty _` closes it) and would hold of a spec pinning any "
            "value. All three are `have`s inside the existing tactic body, the "
            "`theorem correct_makeEmpty` statement is byte-identical, and no "
            "declaration, lemma, axiom or `sorry` is added; the frozen script then "
            "closes the obligation verbatim. If this FAILED => the spec is "
            "unsatisfiable at a shape the change must handle. Measured: the case "
            "elaborates (exit 0), and both content halves are load-bearing rather "
            "than inert — flipping the pinned literal makes it FAIL (exit 1) and "
            "flipping the refusal makes it FAIL (exit 1)."
        ),
    },
]

# The axiom lane is G-AX's job and this gate ignores it; there is no
# `opaque`/`axiom` in this bundle to test in any case (meta.json axioms == []).
AXIOM_TESTS = []
