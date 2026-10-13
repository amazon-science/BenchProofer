"""properties.py — G-PBT falsification battery for django__django-11265 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte — region surgery touches ONLY text inside an ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, both of which
the consumer spec view elides — so ``markers.same_spec`` holds by construction
and both ``prove_correct`` headers survive. ``expect:"verify"`` passes iff (in
scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does NOT
verify AND its refutation ``witness`` discriminates: the witness must ELABORATE
against the rival and FAIL against the frozen solution).

DEFENDED SURFACE — TWO contracted methods, both purely functional, no ``mut``
binder, no ``require`` clause (so no input is out of domain and no witness can
be vacuously excluded by a false precondition):

  inheritedFilteredRelations (outerRelations : List Name) return (out : List Name)
    ensures out = outerRelations                                    -- CLAUSE 1A
    ensures ∀ n, n ∈ outerRelations → resolves out n false           -- CLAUSE 1B

  canRemoveLeadingJoin (preservesUnmatchedRows carriesOwnFilter : Bool)
      return (out : Bool)
    ensures out = joinRemovable preservesUnmatchedRows carriesOwnFilter  -- CLAUSE 2

Obligation 1 pins the registry of named relations a derived nested query
recognises: it is EXACTLY the originating query's registry — the same names, in
the same order, with nothing added, nothing dropped and nothing coalesced
(CLAUSE 1A is an exact list equality, not a set or membership relation) — and
every name in that registry therefore RESOLVES against the derived query
(CLAUSE 1B, the consequence the issue's reported failure is the negation of: a
reference to a recognised name must resolve instead of erroring out).

Obligation 2 pins a two-conjunct structural decision over two independent
boolean properties of a join: it may be dropped as a simplification only when it
neither preserves rows with no match on the other side NOR carries its own
filter condition. ``joinRemovable`` is a fully-unfolded ``def`` over the
method's own two arguments (with a ``@[grind]`` definitional lemma), so there is
no opaque answer key to echo — directive 8 is satisfied and the
UNGROUNDED-ORACLE-ECHO class does not apply, exactly as the nagini sibling
records for its own grounded ``may_trim_leading_join`` helper. Instead the
clause is attacked by partial-domain rivals, each getting the decision wrong on
a specific ``(preservesUnmatchedRows, carriesOwnFilter)`` sub-domain, including
the pre-image behaviour itself.

THREE input binders total, all FREE (nothing pinned by a precondition):
  * ``outerRelations``          — the registry of recognised names: its
                                  CONTENTS, LENGTH, ORDER and MULTIPLICITY all
                                  matter to CLAUSE 1A;
  * ``preservesUnmatchedRows``  — whether the join keeps rows with no match on
                                  the other side;
  * ``carriesOwnFilter``        — whether the join carries its own filter.
The reject witnesses below probe TEN distinct input points: six distinct
``outerRelations`` values (a singleton, a two-element list, a three-element
list, a non-palindromic pair, and a list with a REPEATED name) and ALL FOUR
combinations of the two booleans, so neither boolean is ever held fixed across
the site-2 rivals. That last point is the specific gap this corpus has been
burned by twice: a spec with two independent toggles whose battery only ever
moves one of them would not notice a rival that mishandled the other.

The repeated-name registry is ``weak1-collapse-duplicate-name``'s ``[4, 4]``,
and it is load-bearing rather than decorative: MULTIPLICITY is the fourth
observable of CLAUSE 1A's exact list equality (alongside contents, length and
order), and until that rival landed no case moved it — the five other site-1
registries are all duplicate-free, so a rival that canonicalised the registry by
de-duplicating it was unattacked. An earlier revision of this docstring CLAIMED
one of those five carried a repeated name; none did, and the claim is corrected
by shipping the rival rather than by softening the sentence.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION-MUTATION — VACUOUS. The sibling's two mandatory
    frame-mutation rivals (one per site) write to a half-permission read-only
    input to satisfy the postcondition cheaply; they must be rejected for
    insufficient permission rather than for a value mismatch. Velvet is
    referentially transparent: there is no heap, no aliasing and no fractional
    permission; every input here is an immutable value and neither method
    declares a ``mut`` binder, so there is no read-only cell to overwrite. No
    substitute probe is fabricated (per the porting map, this class is
    legitimately dropped rather than replaced). MEASURED rather than argued, on
    both routes a port might try: (a) adding a ``mut`` to a binder is not a
    variant at all but a SPEC edit — ``variant_problems`` returns "spec view
    differs (same_spec failed)", so the case could never be in scope; (b) an
    in-region write to the existing immutable binder does not reach the
    verifier's permission logic because it does not ELABORATE — the build fails
    at parse/elab with ```outerRelations` cannot be mutated, only variables
    declared using `let mut` can be mutated``, a tooling error carrying no
    information about the spec. So the class is genuinely inexpressible here, and
    the reason is the binder discipline of the carrier, not a hard proof.

  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. Every
    frozen impl region is LOOP-FREE (straight-line ``let`` over immutable
    values, no loop and no recursion), so there is no control flow here to make
    diverge: a diverging rival cannot be obtained by mutating this body, it has
    to bring a loop of its own. When it does, the semantics refuse it. This
    bundle sets ``loom.semantics.termination "total"`` AND carries
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

  * PARTIAL-DOMAIN / VALUE — heavily exercised; the whole reject lane below.

WITNESS MECHANICS ON THIS BUNDLE. Two different routes were needed, both
checked out-of-band with ``scripts/lean_verify.sh`` (two real builds per case):

  * Obligation 2's postcondition is a pure boolean equation, so Velvet's own
    tester machinery derives cleanly and the witness is
    ``canRemoveLeadingJoinTester <p> <c> = false`` under ``decide``.
  * Obligation 1's CLAUSE 1B is a ``∀ … → Prop`` over the ``resolves``
    predicate, so ``prove_postcondition_decidable_for`` leaves an undischarged
    ``Decidable (∀ n ∈ outerRelations, resolves out n false)`` goal and the
    tester route is unavailable (measured: the derived tester does not reduce
    under ``decide``). Those witnesses therefore refute the method's Hoare
    triple DIRECTLY at one concrete input, restating the frozen conjunction
    verbatim under ``¬ triple`` — the astropy-7606 pattern. ``triple``/``pure``
    come from the frozen ``Velvet.Std`` import, so both builds share them.

Every witness states its refutation at LITERAL inputs and binds nothing, so
none of them can be a proof-from-contradiction and none incurs a consistency
obligation. Both halves were observed for all nine: the rival build exits 0 and
the gold build fails with the residual goal that the frozen impl does in fact
satisfy the clause there.

The gold-side failures are SEMANTIC on both routes, and that is established by
the FORGERY PAIR rather than by reading the error text — a gold-side error is
admissible evidence only if it CHANGES when the claim changes. For each of the
nine witnesses the OPPOSITE claim was built against the frozen solution (route
A: the same statement with the `¬` dropped; route B: the tester equation with
`= false` swapped for `= true`), i.e. an assertion that the frozen impl IS
correct at that point:

  route A (5 cases): witness gold EXIT 1 (`⊢ False`) / forgery gold EXIT 0
  route B (4 cases): witness gold EXIT 1 (`decide` proved the tester claim
                     false) / forgery gold EXIT 0

Gold's exit code therefore tracks what is being claimed on both routes, and the
rival side is the mirror image (witness 0 / forgery 1) in all nine. An EARLIER
revision of route A asserted this from the error text alone and was WRONG: with
`resolves` absent from the simp set the gold build exits 1 for the witness AND
for its flipped claim (residual `⊢ ¬resolves [7] 7 false` vs `⊢ resolves [7] 7
false` — a stalled unfolding, not a verdict), so those five rejections attested
to a stuck `simp` rather than to the spec, and the gate would have recorded
`rejected` for a witness asserting gold is CORRECT there. See the note on
`_witness1` for the measured table; the repair is the `resolves` unfolding.

POSITIVE-CONTROL SHAPES ARE CHECKED FOR DEFINITIONAL EQUALITY. A positive whose
"different shape" reduces to the frozen impl's term by `rfl` passes honestly and
tests nothing: the frozen `loom_solve` never has to reprove the clause, because
the kernel already identifies the two terms. So each positive's reshape is
measured against `rfl` before it is shipped, and only non-defeq shapes are kept:
  * `outerRelations.take outerRelations.length` — NOT defeq (`rfl` exits 1) ✓
  * `outerRelations.reverse.reverse`            — NOT defeq (`rfl` exits 1) ✓
  * `! (p || c)`                                — NOT defeq (`rfl` exits 1) ✓
  * `if p then false else ! c`                  — NOT defeq (`rfl` exits 1) ✓
  * `[] ++ outerRelations`                      — DEFEQ (`rfl` exits 0) ✗ dropped
The last line is why `pos1-prepend-nothing` no longer carries the `[] ++ _`
shape: `List.append` recurses on its FIRST argument, so `[] ++ l` reduces to `l`
in one step and the variant's obligation is the frozen one up to conversion.

AXIOM lane: EMPTY. ``meta.json`` declares ``axioms: []`` and
``deep_model_references: []`` — both changed behaviours are modeled deeply as
list-frame and boolean logic over free inputs, so nothing in either proof rests
on an assumed contract. The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-11265"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside an impl region (between `-- impl-start` and
# `-- impl-end`) or is a full `prove_correct` block, and each is unique in
# Solution.lean — both asserted at load time, so the manifest breaks loudly if
# the frozen solution ever changes. Editing only these keeps
# `markers.same_spec` True and both `prove_correct` headers byte-identical.
# ---------------------------------------------------------------------------

# Obligation 1's whole executable body.
_IMPL1 = (
    "    let out := outerRelations\n"
    "    return out"
)
assert _BASE.count(_IMPL1) == 1, "obligation-1 impl region drifted"

# Obligation 2's whole executable body.
_IMPL2 = (
    "    let out := (! preservesUnmatchedRows) && (! carriesOwnFilter)\n"
    "    return out"
)
assert _BASE.count(_IMPL2) == 1, "obligation-2 impl region drifted"

# The two frozen proof blocks. A variant that adds an in-region `assert` may
# retune the tactic body (it is elided from the spec view, so this is a proof
# reshape and not a spec change); rivals leave both blocks untouched.
_PROOF1 = "prove_correct inheritedFilteredRelations by\n  loom_solve"
assert _BASE.count(_PROOF1) == 1, "obligation-1 proof block drifted"

_PROOF2 = "prove_correct canRemoveLeadingJoin by\n  loom_solve"
assert _BASE.count(_PROOF2) == 1, "obligation-2 proof block drifted"


def _impl1(body):
    return _swap(_BASE, _IMPL1, body)


def _impl2(body):
    return _swap(_BASE, _IMPL2, body)


def _impl1_reproved(body, proof):
    return _swap(_impl1(body), _PROOF1, proof)


# ---- WITNESS ROUTE A (obligation 1). CLAUSE 1B is a `∀ … → Prop` over
# ---- `resolves`, so `prove_postcondition_decidable_for` cannot discharge its
# ---- decidability goal and the derived tester does not reduce under `decide`
# ---- (measured: the residual goal is `Decidable (∀ n ∈ outerRelations,
# ---- resolves out n false)` and `decide` then reports reduction "got stuck at
# ---- the `Decidable` instance"). The refutation is stated DIRECTLY against the
# ---- method's Hoare triple at one literal registry, restating the frozen
# ---- conjunction verbatim, in a file whose `prove_correct` blocks have been
# ---- stripped so no tactic script can mask the verdict. Binds nothing => no
# ---- consistency obligation.
# ----
# ---- `resolves` IS IN THE SIMP SET, AND THAT IS LOAD-BEARING. Without it the
# ---- gold-side build still exits 1, but for the WRONG REASON: `simp` reduces
# ---- the triple and then stalls on an opaque `resolves [7] 7 false` atom it
# ---- cannot unfold, so the residual goal is `⊢ ¬resolves [7] 7 false` and the
# ---- exit code carries no information about the CLAIM. Measured with the
# ---- forgery pair the discrimination check exists to catch — build the OPPOSITE
# ---- claim (the same statement with the `¬` dropped, i.e. asserting the frozen
# ---- impl IS correct at that registry) against the frozen solution:
# ----   simp [triple, pure]            -> witness gold EXIT 1 (`⊢ ¬resolves [7] 7 false`)
# ----                                     forgery gold EXIT 1 (`⊢ resolves [7] 7 false`)
# ----   simp [triple, pure, resolves]  -> witness gold EXIT 1 (`⊢ False`)
# ----                                     forgery gold EXIT 0  (gold IS correct there)
# ---- Both directions must move, and only the second form moves them: with
# ---- `resolves` unfolded the membership goal evaluates, so gold's failure is a
# ---- SEMANTIC refutation of the concrete claim (`⊢ False` = the negation is
# ---- unprovable because the clause HOLDS) rather than a stuck unfolding. On the
# ---- rival side the pair is the mirror image (witness 0 / forgery 1), so the
# ---- exit codes track the claim on both subjects, which is exactly what makes
# ---- these five rejections attributable to the spec.
def _witness1(registry, rewrites=()):
    """Route-A witness at `registry`, optionally with extra `simp` rewrites.

    `rewrites` supplies CLOSED equations `simp` needs but cannot derive on its
    own. Only one rival needs any: `.eraseDups` is defined through
    `List.eraseDupsBy`, whose `Decidable`-instance-laden recursion `simp` does
    not evaluate, so without a rewrite the RIVAL build stalls at
    `⊢ [4, 4].eraseDups = [4, 4] → 4 ∉ [4, 4].eraseDups` (measured: exit 1, the
    half that must succeed) and the case would be recorded `witness-unproven`.
    Supplying the reduction as `decide +kernel` — the repair the gate's own
    scikit-learn-13135 note prescribes for a projection the kernel can compute
    but `simp` will not — makes the rival build close, and it does NOT weaken the
    gold side: the equation is a true closed fact about `eraseDups` alone,
    mentions neither method nor `out`, and gold's build reports it UNUSED while
    still failing with `⊢ False`. So gold fails for the same semantic reason as
    every other route-A case, on a claim the rewrite could not have prejudiced.
    """
    extra = "".join(f", {r}" for r in rewrites)
    return (f"example : ¬ triple (l := Prop) (True)\n"
            f"    (inheritedFilteredRelations {registry})\n"
            f"    (fun out => out = {registry}\n"
            f"      ∧ (∀ n, n ∈ {registry} → resolves out n false)) := by\n"
            f"  unfold inheritedFilteredRelations\n"
            f"  simp [triple, pure, resolves{extra}]\n")


# ---- WITNESS ROUTE B (obligation 2). The postcondition is a pure boolean
# ---- equation, so Velvet's tester machinery derives cleanly and the witness is
# ---- a `decide`-able tester statement: `= false` says the extracted program's
# ---- result violates the postcondition at that concrete input. There is no
# ---- `require` clause on this method, so the tester cannot short-circuit to
# ---- `true` on a false precondition.
def _witness2(preserves, carries):
    return ("extract_program_for canRemoveLeadingJoin\n"
            "prove_precondition_decidable_for canRemoveLeadingJoin\n"
            "prove_postcondition_decidable_for canRemoveLeadingJoin\n"
            "derive_tester_for canRemoveLeadingJoin\n\n"
            f"example : canRemoveLeadingJoinTester {preserves} {carries} "
            f"= false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # OBLIGATION 1 — POSITIVE CONTROLS (soundness). Structurally different but
    # CORRECT impls that MUST verify, else SPEC-TOO-STRONG. Both keep the whole
    # registry, so both clauses still hold on the entire domain, and the frozen
    # `loom_solve` closes the byte-identical obligation. Verified out-of-band
    # with real builds.
    # =====================================================================
    {
        "id": "pos1-prepend-nothing",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl1(
            "    let out := outerRelations.take outerRelations.length\n"
            "    return out"),
        "rationale": "structurally different CORRECT impl for CLAUSE 1A/1B: the "
                     "registry is rebuilt by taking a prefix of its own full "
                     "length rather than handed through directly. Same value on "
                     "every input, so `out = outerRelations` and the resolution "
                     "corollary hold everywhere, and this MUST verify; a failure "
                     "would be SPEC-TOO-STRONG (the spec would reject an impl "
                     "that produces exactly the required registry). The shape is "
                     "chosen so the reshape is NOT definitionally equal to the "
                     "frozen impl: `l.take l.length = l` needs the length to be "
                     "consumed structurally and does NOT close by `rfl` "
                     "(measured: exit 1 on `example (l : List Name) : "
                     "l.take l.length = l := rfl`), so the frozen `loom_solve` "
                     "has to reprove CLAUSE 1A rather than accept a term the "
                     "kernel already identifies with `outerRelations`. The "
                     "earlier `[] ++ outerRelations` form was replaced for "
                     "exactly this reason: `[] ++ l` reduces to `l` by `rfl` "
                     "(measured: exit 0), which made that positive attest to "
                     "nothing beyond the frozen case itself.",
    },
    {
        "id": "pos1-double-reverse",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl1(
            "    let out := outerRelations.reverse.reverse\n    return out"),
        "rationale": "a second structurally different CORRECT impl: the registry "
                     "is traversed twice in opposite directions, so the "
                     "executable shape differs substantially while the value is "
                     "identical (order and multiplicity both restored). CLAUSE "
                     "1A's exact list equality still holds on the whole domain, "
                     "so this must verify. Chosen because it is the reshape "
                     "CLOSEST to the ORDER-attacking rival below — if the spec "
                     "could not tell a genuine order-preserving reshape from an "
                     "order-losing one, exactly one of these two cases would "
                     "misbehave.",
    },
    # =====================================================================
    # OBLIGATION 1 — ADMISSIBILITY. The sibling's site-1 admissibility probe
    # invokes the modeled function on an in-domain input shaped like the failing
    # scenario (a one-element registry whose sole name is the referenced one) to
    # confirm the precondition admits a normal input. This method has NO
    # `require` clause, so "the precondition admits it" is trivial and would be
    # a hollow probe. The residual admissibility risk here is instead that the
    # post-image is DEGENERATE — satisfiable by a constant — so the re-aimed
    # probe asserts, at a concrete failing-scenario-shaped input, that the
    # required registry DOES make the referenced name resolve AND that an empty
    # registry does NOT. Both halves are needed: the second is what makes the
    # obligation non-vacuous. The impl is kept verbatim so the method's own
    # `ensures` clauses still discharge; only the elided tactic body is retuned
    # to clear the extra goal. The assert is LIVE — flipping the second
    # conjunct's polarity leaves an unsolved goal (checked out-of-band).
    # =====================================================================
    {
        "id": "admiss1-nondegenerate-resolution",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl1_reproved(
            "    assert (with_name_prefix `admiss\n"
            "      ((∀ n, n ∈ ([4] : List Name) → resolves [4] n false) ∧\n"
            "       ¬ (∀ n, n ∈ ([4] : List Name) → resolves ([] : List Name) n false)))\n"
            "    let out := outerRelations\n"
            "    return out",
            _PROOF1 + "\n  all_goals simp [resolves]"),
        "rationale": "the post-image is ADMISSIBLE and NON-DEGENERATE at an "
                     "in-domain input shaped like the reported failure (a "
                     "single-name registry, the name being the one a lookup "
                     "references): carrying that registry through makes the name "
                     "resolve, AND — the half that makes CLAUSE 1B bite — an "
                     "empty registry does NOT. So the obligation is neither "
                     "unsatisfiable (PRECOND-TOO-STRONG) nor a constant collapse "
                     "satisfiable by any registry whatsoever. The in-region "
                     "assert must discharge; the impl is kept verbatim so both "
                     "`ensures` clauses discharge too.",
    },
    # =====================================================================
    # OBLIGATION 1 — UNIQUENESS rivals. Each shares the frozen spec, gets part
    # of the domain right, and MUST be rejected. Each carries a machine-checked
    # refutation witness at its OWN input point (six distinct registries), plus
    # the refinement argument that its faithful counterpart would not resolve.
    # =====================================================================
    {
        "id": "weak1-empty-registry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl1("    let out : List Name := []\n    return out"),
        "refinement": "this IS the pre-image behaviour, and the direct cause of "
                      "the error the issue reports: the derived nested query is "
                      "built recognising NO named relations at all, so a lookup "
                      "that references one of the originating query's named "
                      "relations cannot be resolved there and the operation "
                      "errors out on that name instead of running. A counterpart "
                      "carrying this behaviour reproduces the reported failure "
                      "verbatim, so it would NOT resolve the failing test.",
        "rationale": "REJECT from CLAUSE 1A (`out = outerRelations` fails for "
                     "every non-empty registry) and independently from CLAUSE 1B "
                     "(no name resolves against an empty registry). Verifying "
                     "would be SPEC-TOO-WEAK on the headline behaviour. Refuted "
                     "at outerRelations = [7]: the clause requires the single "
                     "name to be carried through and to resolve; the rival "
                     "carries nothing.",
        "witness": _witness1("[7]"),
    },
    {
        "id": "weak1-drop-first-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl1("    let out := outerRelations.drop 1\n    return out"),
        "refinement": "a near-miss that carries the registry through EXCEPT its "
                      "first entry. A counterpart with this behaviour leaves the "
                      "first-declared named relation unrecognised by the derived "
                      "query, so a lookup referencing that one still errors out "
                      "— the same reported symptom, merely narrowed to one name "
                      "instead of all of them. Since the failing scenario "
                      "references a registry whose relevant name is the first "
                      "declared, it would NOT resolve.",
        "rationale": "REJECT from CLAUSE 1A: a registry missing its head can "
                     "never equal the full originating registry. Refuted at "
                     "outerRelations = [3, 8] — a two-element registry, so the "
                     "rival is right about the tail and wrong only about the "
                     "head; that is the sub-domain the empty-registry rival does "
                     "not cover, and this is a distinct input point (LENGTH and "
                     "CONTENTS both moved).",
        "witness": _witness1("[3, 8]"),
    },
    {
        "id": "weak1-drop-last-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl1("    let out := outerRelations.dropLast\n    return out"),
        "refinement": "the mirror near-miss: the registry is carried through "
                      "except its FINAL entry. A counterpart with this behaviour "
                      "leaves the last-declared named relation unrecognised, so "
                      "a lookup referencing it errors out exactly as reported. "
                      "It would NOT resolve, and it is a genuinely different "
                      "counterpart from the drop-first one (a different name "
                      "goes missing), so it is given its own witness point "
                      "rather than sharing.",
        "rationale": "REJECT from CLAUSE 1A: a registry missing its last entry "
                     "cannot equal the full originating registry, and from "
                     "CLAUSE 1B the dropped name no longer resolves. Refuted at "
                     "outerRelations = [5, 2, 9] — a three-element registry, so "
                     "the rival is right about a strictly larger prefix than any "
                     "other rival here and diverges only on the tail entry. "
                     "Third distinct LENGTH probed.",
        "witness": _witness1("[5, 2, 9]"),
    },
    {
        "id": "weak1-reordered-registry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl1("    let out := outerRelations.reverse\n    return out"),
        "refinement": "the closest near-miss in the reject lane: it carries every "
                      "name through, losing only their ORDER. A counterpart with "
                      "this behaviour would rebuild the registry from a "
                      "re-sequenced traversal rather than propagating the "
                      "originating registry itself. Every name resolves, so the "
                      "reported error does not reappear — but the derived query's "
                      "registry is no longer the originating one, and the "
                      "declaration order of named relations governs the order in "
                      "which their conditions are attached downstream, so the "
                      "operation is no longer the identity-preserving "
                      "propagation the fix requires. This is precisely the rival "
                      "that would slip past a spec stated as set membership "
                      "rather than exact equality, which is why the clause is an "
                      "exact list equality and why this case exists.",
        "rationale": "REJECT from CLAUSE 1A specifically, and from CLAUSE 1A "
                     "ALONE: CLAUSE 1B is fully satisfied by this rival (every "
                     "name is still present, so every name still resolves). It is "
                     "therefore the case that proves CLAUSE 1A is load-bearing "
                     "independently of the membership corollary — attacking the "
                     "ORDER sub-behaviour that no other rival touches. Refuted at "
                     "outerRelations = [6, 1], a non-palindromic pair (a "
                     "palindromic registry would make the rival agree with gold, "
                     "so the witness input is chosen to discriminate).",
        "witness": _witness1("[6, 1]"),
    },
    {
        "id": "weak1-extra-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl1("    let out := outerRelations ++ [0]\n    return out"),
        "refinement": "the OVER-propagating direction: every originating name is "
                      "carried through and an extra one is recognised on top. A "
                      "counterpart with this behaviour would have the derived "
                      "query recognise a name the originating query never "
                      "declared, so a lookup naming it would silently resolve to "
                      "a relation with no definition instead of being rejected — "
                      "a different wrong result rather than the reported error. "
                      "It would NOT resolve, and it tests the clause in the "
                      "direction all the dropping rivals leave open: over- as "
                      "well as under-propagation is wrong.",
        "rationale": "REJECT from CLAUSE 1A: an extended registry cannot equal "
                     "the originating registry. CLAUSE 1B is again satisfied "
                     "(a superset resolves everything), so this rival too is "
                     "refuted by the exact-equality clause alone — from the "
                     "opposite side of the reordering rival. Refuted at "
                     "outerRelations = [2]: gold's registry is [2], the rival's "
                     "is [2, 0]. Fifth distinct input point for this binder.",
        "witness": _witness1("[2]"),
    },
    {
        "id": "weak1-collapse-duplicate-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl1("    let out := outerRelations.eraseDups\n    return out"),
        "refinement": "the CANONICALISING near-miss, and the only rival that "
                      "attacks MULTIPLICITY: every distinct name is carried "
                      "through, in its original relative order, and only repeated "
                      "occurrences are collapsed. A counterpart with this "
                      "behaviour would rebuild the derived query's registry as a "
                      "de-duplicated traversal of the originating one rather than "
                      "propagating that registry itself. Every name still "
                      "resolves, so the reported error does not reappear — but the "
                      "derived registry is no longer the originating one, and a "
                      "registry that has silently changed shape is not the "
                      "identity-preserving propagation the fix requires; the "
                      "operation would agree with the required behaviour on every "
                      "duplicate-free registry and diverge on any other, which is "
                      "exactly the profile of a near-miss that ships. It would NOT "
                      "resolve.",
        "rationale": "REJECT from CLAUSE 1A, and from CLAUSE 1A ALONE (CLAUSE 1B "
                     "is fully satisfied: `eraseDups` preserves the name SET, so "
                     "every originating name still resolves). It is therefore the "
                     "third case — with the reordering and extra-name rivals — "
                     "showing 1A bites independently of the membership corollary, "
                     "and the only one that moves MULTIPLICITY: CLAUSE 1A is an "
                     "exact list equality, so contents, length, ORDER and "
                     "multiplicity are all pinned, and the other five site-1 "
                     "registries are duplicate-free and cannot discriminate here. "
                     "Refuted at outerRelations = [4, 4], a registry with a "
                     "repeated name (a duplicate-free one would make the rival "
                     "agree with gold, so the witness input is chosen to "
                     "discriminate): gold's registry is [4, 4], the rival's is "
                     "[4]. Sixth distinct input point for this binder.",
        "witness": _witness1(
            "[4, 4]",
            ("show ([4, 4] : List Name).eraseDups = [4] from by decide +kernel",)),
    },

    # =====================================================================
    # OBLIGATION 2 — POSITIVE CONTROLS (soundness). Both are structurally
    # different but CORRECT decision procedures that MUST verify, else
    # SPEC-TOO-STRONG. Both keep the full two-conjunct decision, so the frozen
    # `loom_solve` closes the byte-identical obligation. Verified out-of-band.
    # =====================================================================
    {
        "id": "pos2-de-morgan",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl2(
            "    let out := ! (preservesUnmatchedRows || carriesOwnFilter)\n"
            "    return out"),
        "rationale": "structurally different CORRECT impl for CLAUSE 2: the "
                     "conjunction of two negations is re-expressed as the "
                     "negation of a disjunction. Same function on all four "
                     "inputs, so the clause holds on the whole domain and this "
                     "must verify; a failure would be SPEC-TOO-STRONG (the spec "
                     "would be pinned to one syntactic form of its own decision "
                     "rather than to the decision).",
    },
    {
        "id": "pos2-branch-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl2(
            "    let out := if preservesUnmatchedRows then false "
            "else ! carriesOwnFilter\n"
            "    return out"),
        "rationale": "the direct port of the sibling's site-2 positive control: "
                     "the decision is hoisted into an explicit BRANCH on the "
                     "first property, with the second consulted only on the "
                     "surviving arm. Different control flow, identical values on "
                     "all four inputs, so CLAUSE 2 still holds and this must "
                     "verify. Deliberately the reshape that most resembles the "
                     "conjunct-dropping rivals below — a spec that could not "
                     "distinguish reshaping the branch structure from deleting a "
                     "conjunct would fail one of these two cases.",
    },
    # =====================================================================
    # OBLIGATION 2 — ADMISSIBILITY. Same re-aiming as obligation 1: this method
    # has no `require` clause, so what is worth probing is that the decision is
    # NON-DEGENERATE — that it is genuinely a function of BOTH inputs and not a
    # constant. The in-region assert pins the full truth table, which is exactly
    # the claim "each of the four input combinations gets its own answer, and
    # only one of them permits removal". The frozen proof discharges it
    # unchanged. The assert is LIVE — flipping any entry leaves an unsolved goal
    # (checked out-of-band).
    # =====================================================================
    {
        "id": "admiss2-full-truth-table",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl2(
            "    assert (with_name_prefix `admiss\n"
            "      (joinRemovable false false = true ∧ joinRemovable false true = false ∧\n"
            "       joinRemovable true false = false ∧ joinRemovable true true = false))\n"
            "    let out := (! preservesUnmatchedRows) && (! carriesOwnFilter)\n"
            "    return out"),
        "rationale": "CLAUSE 2's post-image is admissible and NON-DEGENERATE over "
                     "the whole 2x2 input space: exactly one combination permits "
                     "the simplification and the other three forbid it, so the "
                     "decision depends on BOTH binders and is not satisfiable by "
                     "any constant. That is the property the two "
                     "conjunct-dropping rivals below violate from opposite sides, "
                     "and asserting it here confirms the domain the spec claims "
                     "is real rather than empty (a failure would be "
                     "PRECOND-TOO-STRONG / a vacuous post-image). The impl is "
                     "kept verbatim so the method's own `ensures` discharges too.",
    },
    # =====================================================================
    # OBLIGATION 2 — UNIQUENESS rivals. All FOUR boolean input combinations are
    # used as witness points across these rivals, so neither binder is ever held
    # fixed: the two conjunct-dropping rivals discriminate on opposite binders,
    # and the two constant rivals pin the remaining corners.
    # =====================================================================
    {
        "id": "weak2-drops-own-filter-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl2("    let out := ! preservesUnmatchedRows\n    return out"),
        "refinement": "THE pre-image behaviour at this site, and the headline "
                      "weakness the battery exists to catch: the decision "
                      "consults only whether the join preserves unmatched rows "
                      "and ignores whether it carries its own filter. On a join "
                      "that does not preserve unmatched rows but DOES carry its "
                      "own filter, this permits the simplification and the "
                      "join's filter condition is silently discarded — so the "
                      "operation returns the wrong rows rather than erroring. A "
                      "counterpart carrying this behaviour is exactly the "
                      "pre-image code the fix replaces, and it would NOT resolve "
                      "the failing test even with the registry behaviour "
                      "correct.",
        "rationale": "REJECT from CLAUSE 2 via the `carriesOwnFilter` conjunct: "
                     "at preservesUnmatchedRows = false, carriesOwnFilter = true "
                     "the required decision is `false` (keep the join) and the "
                     "rival answers `true`. Verifying would be SPEC-TOO-WEAK on "
                     "precisely the conjunct the fix adds. Refuted at "
                     "(false, true) — the point that moves `carriesOwnFilter` "
                     "while the other rival's point holds it low.",
        "witness": _witness2("false", "true"),
    },
    {
        "id": "weak2-drops-row-preservation-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl2("    let out := ! carriesOwnFilter\n    return out"),
        "refinement": "the MIRROR omission, and the reason this rival is not "
                      "subsumed by the one above: it keeps the filter conjunct "
                      "and drops the row-preservation one. A counterpart with "
                      "this behaviour would simplify away a join that preserves "
                      "rows having no match on the other side, losing exactly "
                      "those rows from the result. That regresses the "
                      "long-standing behaviour the other pre-existing tests pin, "
                      "so it would NOT resolve — over-permissive in the other "
                      "direction is still wrong. Without this case the battery "
                      "would demonstrate only that one of the two independent "
                      "toggles is load-bearing.",
        "rationale": "REJECT from CLAUSE 2 via the `preservesUnmatchedRows` "
                     "conjunct: at preservesUnmatchedRows = true, "
                     "carriesOwnFilter = false the required decision is `false` "
                     "and the rival answers `true`. Refuted at (true, false) — "
                     "the complementary point, so the two conjunct-dropping "
                     "rivals together vary BOTH binders rather than agreeing on "
                     "one.",
        "witness": _witness2("true", "false"),
    },
    {
        "id": "weak2-never-remove",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl2("    let out := false\n    return out"),
        "refinement": "the constant-refuse rival: no leading join is ever "
                      "simplified away. A counterpart with this behaviour never "
                      "loses a filter and never loses a row, so it does not "
                      "reproduce the reported failure — but it also never "
                      "performs the simplification the operation exists to "
                      "perform, diverging from the required behaviour on the one "
                      "input combination where removal IS permitted and "
                      "regressing the pre-existing tests that pin that "
                      "simplification. It would NOT resolve.",
        "rationale": "REJECT from CLAUSE 2 on the single positive corner of the "
                     "decision: at preservesUnmatchedRows = false, "
                     "carriesOwnFilter = false the required answer is `true` and "
                     "the rival answers `false`. This is the ONLY witness point "
                     "at which the required decision is `true`, so it is the one "
                     "case establishing that the clause forbids a blanket refusal "
                     "as well as a blanket permission. Refuted at (false, false).",
        "witness": _witness2("false", "false"),
    },
    {
        "id": "weak2-always-remove",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl2("    let out := true\n    return out"),
        "refinement": "the constant-permit rival, and the one that most directly "
                      "exhibits the harm: every leading join is simplified away "
                      "regardless of either property, so both a filter-carrying "
                      "join's condition and a row-preserving join's rows can be "
                      "lost. A counterpart with this behaviour is strictly worse "
                      "than the pre-image on the failing scenario and would NOT "
                      "resolve. Included because it is the rival a spec stating "
                      "only 'the decision is a boolean' would admit.",
        "rationale": "REJECT from CLAUSE 2 at the fourth and last input corner: "
                     "at preservesUnmatchedRows = true, carriesOwnFilter = true "
                     "the required answer is `false` and the rival answers "
                     "`true`. Refuted at (true, true) — the only remaining "
                     "combination, so this rival completes the 2x2 coverage of "
                     "the two binders across the reject lane.",
        "witness": _witness2("true", "true"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING. The sibling battery has 13 SPEC cases across TWO
# nagini functions (2 soundness positives, 2 admissibility, 9 uniqueness rivals)
# plus an EMPTY axiom lane. This bundle contracts the SAME two behaviours, so —
# unusually for this port wave — there is no carrier narrowing to absorb: both
# obligations survive, and the port is 16 cases against the sibling's 13.
#
#   sibling case              -> here                                disposition
#   -------------------------------------------------------------------------
#   s1-frame-mutation         -> (none)                              VACUOUS
#   s1-drop-last-alias        -> weak1-drop-last-name                PORTED
#   s1-drop-first-alias       -> weak1-drop-first-name               PORTED
#   s1-empty-registry         -> weak1-empty-registry                PORTED
#   s1-pos-control            -> pos1-prepend-nothing                PORTED
#   (no sibling)              -> pos1-double-reverse                 ADDED
#   s1-admissibility          -> admiss1-nondegenerate-resolution    PORTED (re-aimed)
#   (no sibling)              -> weak1-reordered-registry            ADDED
#   (no sibling)              -> weak1-extra-name                    ADDED
#   (no sibling)              -> weak1-collapse-duplicate-name        ADDED
#   s2-frame-mutation         -> (none)                              VACUOUS
#   s2-real-bug               -> weak2-drops-own-filter-conjunct     PORTED
#   s2-never-trim             -> weak2-always-remove                 PORTED (re-polarised)
#   s2-inverted-filter        -> weak2-drops-row-preservation-conjunct  PORTED (re-expressed)
#   s2-drop-downstream        -> (none)                              NO COUNTERPART
#   s2-pos-control            -> pos2-branch-reshape                 PORTED
#   (no sibling)              -> pos2-de-morgan                      ADDED
#   s2-admissibility          -> admiss2-full-truth-table            PORTED (re-aimed)
#   (no sibling)              -> weak2-never-remove                  ADDED
#   AXIOM_TESTS ([])          -> (none)                              DROPPED (G-AX)
#   (divergence: no sibling case) -> (none)                          SPEC-CLOSED
#
# PORTED (rivals, obligation 1): the sibling's three site-1 rivals port
#   one-for-one — its loop that stops one short becomes `.dropLast`, its loop
#   starting at index 1 becomes `.drop 1`, and its empty-list return is the same
#   rival here. Each gets its own witness registry rather than sharing, because
#   they are genuinely different counterparts (a different name goes missing) and
#   a shared witness would let each one's rationale claim a sub-domain the
#   manifest never demonstrates.
# ADDED (obligation 1): the sibling's carrier states site 1 as an exact sequence
#   equality too, but its rival set only ever DROPS entries, so nothing there
#   tests the order or the no-extras direction. On this carrier CLAUSE 1A is an
#   exact `List` equality while CLAUSE 1B is only a membership corollary, and the
#   two come apart: `weak1-reordered-registry`, `weak1-extra-name` and
#   `weak1-collapse-duplicate-name` all SATISFY 1B and are refuted by 1A alone,
#   which is what shows 1A is load-bearing on its own rather than a decoration on
#   the membership claim. Without them a spec written as set membership would pass
#   this battery — and without the third, a spec written as MULTISET membership
#   still would, since order is the only 1B-invariant observable the first two
#   move. `weak1-collapse-duplicate-name` closes that: exact list equality pins
#   four observables (contents, length, order, multiplicity) and each now has a
#   rival that moves it and nothing else 1B can see.
# PORTED-RE-EXPRESSED (rivals, obligation 2): the sibling's site-2 rivals are
#   expressed over its two-scalar trim oracle; here the same three attacks land
#   as conjunct surgery on the boolean decision. Its real-bug rival (guard
#   ignores the filter property) is `weak2-drops-own-filter-conjunct` verbatim in
#   spirit. Its never-trim rival becomes `weak2-always-remove`: the sibling's
#   function returns the RETAINED conditions, so "never trim" there means "always
#   keep", whereas this method returns the REMOVAL decision, so the same wrong
#   behaviour is the constant `true` — the polarity flips with the carrier, and
#   `weak2-never-remove` is added to pin the opposite corner the sibling's
#   carrier reached through its other clause.
#   Its inverted-filter rival (wrong conjunct polarity, i.e.
#   `(! preservesUnmatchedRows) && carriesOwnFilter`) is re-expressed as
#   `weak2-drops-row-preservation-conjunct`. The reason is EXHAUSTION, not a
#   shared corner: obligation 2's clause is a total function `Bool -> Bool ->
#   Bool`, so a wrong impl must differ from the required decision at one of the
#   FOUR input corners, and the four rivals below already refute one corner each.
#   Any further site-2 rival is therefore refuted at a corner some existing rival
#   already occupies, and CLAUSE 2 is pinned completely by the four already
#   shipped. That exhaustion claim is now MEASURED EXHAUSTIVELY rather than
#   argued: all 16 functions `Bool -> Bool -> Bool` were built against the frozen
#   spec as `if p then (if c then _ else _) else (if c then _ else _)` variants.
#   Exactly ONE verifies (exit 0) — the required decision, true only at
#   (false, false) — and the other 15 are rejected (exit 1, each with the
#   residual `ensures` goal). So CLAUSE 2 pins its behaviour COMPLETELY on this
#   carrier: there is no wrong site-2 impl left for a rival to express, and no
#   SPEC-TOO-WEAK hole at this obligation. The literal inversion was built and
#   measured to confirm this rather
#   than assumed: it is expressible and genuinely wrong (module exit 1; its
#   witness at (false, true) elaborates against it, exit 0, and fails against the
#   frozen solution, exit 1, with `decide` proving
#   `canRemoveLeadingJoinTester false true = false` is false), but it diverges
#   from the required decision only at (false, false) and (false, true) — the
#   corners `weak2-never-remove` and `weak2-drops-own-filter-conjunct` already
#   refute — so it would add a rival without adding a sub-domain. It is dropped
#   as REDUNDANT, and the mirror conjunct-drop is kept because it is the rival
#   that varies the binder the headline rival holds fixed, at (true, false),
#   which nothing else reaches. (An earlier revision of this note claimed the
#   inversion and the mirror drop are "refuted at the same corner for the same
#   reason"; that is false — they are refuted at (false, true)/(false, false) and
#   at (true, false) respectively — and it is corrected here.)
# NO COUNTERPART (s2-drop-downstream): the sibling's site-2 function also
#   ASSEMBLES the retained condition list, so it has a rival that gets the
#   decision right and loses a downstream condition. This bundle models only the
#   DECISION (a `Bool`), not the assembly, so there is no downstream list to
#   drop an element from and no way to express this rival. Carrier narrowing, not
#   an omission of convenience.
# PORTED-RE-AIMED (admissibility, both sites): the sibling's probes self-call the
#   modeled function on an in-domain input to show its `Requires` admits a normal
#   input. Neither method here declares a `require` clause, so that probe would be
#   trivially true and would attest nothing. Both are re-aimed at the residual
#   risk that survives on this carrier — that the post-image is DEGENERATE: for
#   obligation 1, that the required registry makes a referenced name resolve
#   while an empty one does not; for obligation 2, the full 2x2 truth table, i.e.
#   the decision genuinely depends on both binders. Both asserts were checked
#   LIVE (flipping a conjunct leaves an unsolved goal).
# ADDED (positives): a second positive per obligation, each chosen to be the
#   reshape closest to that obligation's sharpest rival —
#   `pos1-double-reverse` against `weak1-reordered-registry`, and
#   `pos2-branch-reshape`/`pos2-de-morgan` against the conjunct-dropping rivals.
#   The pairing is the point: the spec must accept the order-preserving reshape
#   and reject the order-losing rival, and accept the branch reshape and reject
#   the conjunct deletion. All four verified with real builds, and all four were
#   additionally checked NOT to be definitionally equal to the frozen impl (see
#   the `rfl` table in the module docstring) so that each one's `loom_solve`
#   genuinely rediscovers its clause instead of closing by conversion.
#   NOTE on the spec's tolerance for reshapes: the frozen `loom_solve` does NOT
#   close every faithful reshape of obligation 1. `outerRelations.map id` and
#   `outerRelations.filter (fun _ => true)` are both correct and both leave a
#   residual `List.map id outerRelations = outerRelations` /
#   `List.filter (fun x => true) outerRelations = outerRelations` goal (module
#   exit 1). This is a PROOF-SCRIPT limit, not a spec hole, and it is recorded
#   here so a later reader does not mistake it for one: with the elided tactic
#   body retuned to `loom_solve; all_goals simp` both impls VERIFY against the
#   byte-identical spec (measured, exit 0). The spec admits them; only the frozen
#   script's automation does not reach them, which is precisely why positives are
#   selected from the reshapes the frozen script does close.
# VACUOUS (both frame-mutation rivals): the sibling makes these MANDATORY
#   because its two inputs carry half permission and a write must be rejected for
#   insufficient permission rather than a value mismatch. Velvet has no heap, no
#   aliasing and no fractional permission; every input here is an immutable value
#   and neither method declares a `mut` binder, so there is no read-only cell to
#   overwrite. Not replaced by a substitute probe (porting map: vacuous here).
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. Every frozen impl region
#   is LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
#   recursion), so there is no control flow here to make diverge: a diverging
#   rival cannot be obtained by mutating this body, it has to bring a loop of
#   its own. When it does, the semantics refuse it. This bundle sets
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
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job, this bundle declares no
#   axioms and no deep-model references, and the gate ignores AXIOM_TESTS anyway.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses (pts = 10 distinct points):
#   outerRelations         — [7], [3, 8], [5, 2, 9], [6, 1], [2], [4, 4]: six
#                            distinct values varying LENGTH (1, 2, 3), CONTENTS,
#                            ORDER (the reordering rival's [6, 1] is
#                            non-palindromic on purpose) and MULTIPLICITY (the
#                            de-duplicating rival's [4, 4] repeats a name on
#                            purpose — a duplicate-free registry would make that
#                            rival agree with gold). No two site-1 rivals share a
#                            point.
#   preservesUnmatchedRows — false, true, false, true: varied, and paired against
#                            both values of the other binder.
#   carriesOwnFilter       — true, false, false, true: varied likewise. All FOUR
#                            combinations appear, so neither boolean is held
#                            fixed across the site-2 rivals — the exact gap that
#                            let a two-toggle spec ship under-attacked twice
#                            before in this corpus.
#   Both obligations are DEFENDED (2 soundness positives + 1 admissibility each)
#   and ATTACKED (6 rivals on obligation 1, 4 on obligation 2). Every
#   independent top-level clause is attacked: CLAUSE 1A by all six site-1
#   rivals — and by weak1-reordered-registry / weak1-extra-name /
#   weak1-collapse-duplicate-name ALONE, since those three satisfy 1B; CLAUSE 1B
#   by weak1-empty-registry and weak1-drop-last-name (the dropped name stops
#   resolving); CLAUSE 2 by all four site-2 rivals, one per input corner, with
#   each conjunct singled out by its own conjunct-dropping rival. The three
#   1B-satisfying rivals are the ones that pin 1A's exact-equality strength, one
#   observable each: ORDER (reverse), NO-EXTRAS (append), MULTIPLICITY
#   (eraseDups).
AXIOM_TESTS = []
