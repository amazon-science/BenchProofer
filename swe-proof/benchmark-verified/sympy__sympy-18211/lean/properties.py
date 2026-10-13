"""properties.py — G-PBT falsification battery for sympy__sympy-18211 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a positive that legitimately re-proves, inside
the ``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_asSet`` STATEMENT
stays byte-identical). ``expect="verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect="reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models a rich imperative surface: a mutable ``Relation`` held at fractional
permission with four observable fields (``solvability`` tag, ``token``, ``sym``,
``n_free``), a ``SolutionSet`` carrier with four projections (``is_fallback``,
``cond``, ``sym``, ``over_reals``), a precondition (``n_free==1`` and the tag in
the two-way domain), a totality/no-Exsures obligation, and value-abstract
accessors ``solved_cond`` / ``solved_sym`` / ``solved_reals`` pinning the
determined branch field-for-field.

This Lean bundle models only the purely-functional CORE — the single total
function that routes between two unchanged callees on whether the set-solving
routine could produce a set. The carrier is narrowed to:

  * ``solveSet rel : Except Unit SetExpr`` (opaque) — the routine's outcome:
    ``.ok s`` a produced set, ``.error ()`` its inability escaping;
  * ``fallbackSet rel : SetExpr`` (opaque) — the symbolic conditional set built
    on the tolerated branch;
  * ``result : Except Unit SetExpr`` — the computed outcome.

and the postcondition collapses to TWO independent top-level clauses, selected
by the routine's own outcome:

  * (C-ok)  ``solveSet rel = .ok s``     ⟹ ``result = .ok s``
            (the produced set is returned UNCHANGED);
  * (C-err) ``solveSet rel = .error ()`` ⟹ ``result = .ok (fallbackSet rel)``
            (the inability is TOLERATED — the fallback set is returned, and the
            error is NEVER propagated: ``result`` is always ``.ok _``).

The BEHAVIOURAL DISCRIMINATOR (the fix): on the ``.error ()`` branch the
computation returns ``.ok (fallbackSet rel)`` rather than letting ``.error ()``
escape. The pre-patch propagated the error; the totality rival below IS that
pre-patch behavior.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: an
    input carries no heap permission, there is no read-only half-permission to
    overwrite and no aliasing to exploit. The nagini frame-mutation rival
    (writing ``rel.solvability = 1`` under a 1/2 share) has no expressible
    instance here — the tag is not even a modeled field; the outcome is observed
    only as the opaque ``solveSet rel``. No substitute is fabricated. (nagini
    case 3.)

  * DIVERGENCE / NON-TERMINATION — a KNOWN HOLE, *not* a vacuous class. The
    earlier reading ("a diverging implementation cannot be written at all") was
    measured FALSE: this bundle sets no ``loom.semantics.termination`` option, so
    the carrier is vanilla total Lean, and a rival that routes the result through
    a ``partial def loopForever rel := loopForever rel`` is both writable and in
    scope. Built: it is REJECTED (exit 1, ``Tactic 'rfl' failed: … loopForever
    rel is not definitionally equal to … Except.ok s``), so the class is real.
    What blocks SHIPPING it is the witness half, and that was measured too:
    ``partial def`` compiles to an opaque constant, so ``¬ loopForever rel =
    Except.ok (fallbackSet rel)`` is unprovable and the witness FAILS on the
    rival (exit 1, ``unsolved goals … ⊢ ¬loopForever rel = Except.ok (fallbackSet
    rel)``) — i.e. ``witness-unproven``, not a refutation. Conditioning on that
    residual by hypothesis is not open either: ``loopForever`` is a name the
    variant declares and the frozen solution does not, which the witness
    vocabulary rule rejects (its failure on gold would be an unknown name, not a
    satisfied spec). So the disposition recorded here is a HOLE in the spec's
    reach, not a complete battery: the obligation does not pin non-termination on
    this carrier in a way any admissible witness can attribute. Nothing is
    shipped for it. (The nagini battery carries no ``diverge-*`` case either.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS, for the reason the nagini docstring gives:
    the determined branch is pinned to the routine's OWN returned set (here
    literally ``result = .ok s`` where ``s`` is what ``solveSet`` produced), a
    value grounded in the input, not an independent answer key. An impl that
    routes correctly reproduces exactly that set — it is CORRECT, not a wrong
    echo. No wrong-echo reject case exists; instead the routing shape is used as
    a structurally-different POSITIVE CONTROL. (nagini oracle-grounding note.)

  * TOTALITY / CONTROL-FLOW — APPLIES. The pre-patch propagated the routine's
    inability; here the rival returns ``.error ()`` on that branch, violating
    (C-err)'s "result is always ``.ok _``". This is the canonical
    verify-does-not-imply-resolve rival (== the pre-patch). (nagini case 4.)

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the domain but
    diverging where a clause bites: returning a fabricated set on the tolerated
    branch instead of ``fallbackSet rel`` (attacks C-err's value), and returning
    the fallback on the SUCCESS branch instead of the produced set (attacks
    C-ok's value — the analogue of nagini's branch-swap / fabricated-fields
    rivals, which discarded the solver's genuine set).

  * PRECONDITION ADMISSIBILITY — APPLIES, and is now carried (case
    ``admiss-f2p-tolerated-shaped``). The port originally dropped this lane on the
    grounds that the frozen ``theorem correct_asSet`` has no precondition
    hypothesis, so there is no antecedent to satisfy. That reason is WRONG, and
    the audit records why: on a TOTAL carrier the analogue of PRECOND-TOO-STRONG
    is the obligation being UNSATISFIABLE at exactly an F2P-shaped input, and the
    unguarded ``∀ rel`` does not by itself show the two clauses are jointly
    satisfiable AT such a point — a spec whose selected clause was contradictory
    on the tolerated branch would close the ``∀`` only if that branch were
    unreachable, which nothing here states. So the lane is landed the way a total
    carrier admits it: at the concrete F2P-shaped relation (a univariate relation
    the set-solving routine cannot handle), discharge the obligation BY EVALUATION
    as a ``have`` — exhibit a set the clause admits, pin the tolerated branch's
    value, and show the outcome is not the inability — and only then close the
    frozen obligation verbatim. See the case's ``rationale`` for what each of the
    three ``have``s buys. (nagini case 2, ``admiss-f2p-undecided-shaped``.)

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so a
rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly and refuting
it. Because the carrier is OPAQUE (``solveSet`` / ``fallbackSet`` have no value
``decide`` can compute), each witness CONDITIONS ON THE CARRIER instead: it fixes
which branch the routine took (``solveSet rel = .error ()`` or ``.ok s``) by
hypothesis, and — where the clause is a value pin — additionally assumes the two
sides are distinguishable (``fallbackSet rel ≠ …`` / ``fallbackSet rel ≠ s``).
Each such conditioned claim is exactly the sub-domain where the rival is wrong,
and each was checked (i) to HOLD of its rival and (ii) to FAIL on the frozen
solution, so it discriminates rather than asserting a tautology. The bound
hypotheses are kept as WEAK as the refutation needs (one branch hypothesis, plus
at most one inequality about a single opaque term) and were each checked jointly
SATISFIABLE (no ``False`` derivable from them alone), so no witness is refuted
from a contradiction.

BINDER / POINT SPREAD. The spec's discriminating structure is the branch of
``solveSet rel`` (the ``Except`` tag) and, within each branch, the returned set —
a 2×2 grid of (branch × constructor-or-payload). The four reject witnesses fill
it exactly: the ``.error ()`` branch under the constructor (C-err totality) and
under a value mismatch (C-err payload), and the ``.ok s`` branch under a value
mismatch (C-ok payload) and under the constructor (C-ok totality, the
audit-added ``totality-swap-branches``). No two rivals are refuted at the same
conditioned point for the same reason. Note that the two constructor witnesses
need only ONE hypothesis while the two payload witnesses need an inequality about
a second opaque term — the constructor pins bite everywhere on their branch,
the payload pins only where the two sets differ. The admissibility positive pins the SAME tolerated branch at a CONCRETE
F2P-shaped relation rather than at a bound ``rel``, which is the one point the
three witnesses cannot reach (they condition on the branch; it evaluates at it).

AUDIT NOTE (adversarial re-derivation of the recorded SOUND). Every case's builds
were re-run independently, and each reject case was additionally subjected to the
FORGERY test: a second file differing from the witness only in WHAT IT CLAIMS
(the ``¬`` dropped, so it asserts the frozen solution is CORRECT at that same
conditioned point), built against the frozen solution. Gold's exit code changed
in all four cases — the flipped claim ELABORATES on gold (exit 0) where the
witness FAILS (exit 1), and on the RIVAL the pair is inverted (flip 1 / witness
0) — so gold's verdict tracks the claim and no rejection is hollow. The two
``Type mismatch`` signatures were additionally settled by a TYPE-REVEALING build
(final step replaced by ``exact (0 : Nat)``) run on both sides: on gold the
residual goal prints ``False``, i.e. ``simp`` PROVED the equation and gold
satisfies the clause, while on the rival it prints the concrete unproved
inequality (``¬{ repr := "FABRICATED" } = fallbackSet rel`` /
``¬fallbackSet rel = s``). That pair is the refutation, not a tactic mismatch.

Defects found and fixed by successive audit passes: the ``admissibility`` lane
had been dropped on a reason that does not hold on a total carrier; the
``partial-domain-wrong-fallback`` witness stated its inequality in the
orientation that made gold's error a syntactic ``Invalid field notation`` rather
than the hypothesis's real type; the ``divergence`` class was recorded as VACUOUS
when it is in fact a reachable-but-unwitnessable HOLE (re-derived above with the
measured build errors); the admissibility positive discharged no-inability-escapes
only under a branch hypothesis, so an unconditional ``have`` (d) was added; and
the ``.ok``-branch CONSTRUCTOR pin was unprobed by any rival, so
``totality-swap-branches`` was added to occupy it.

SPEC-TOO-WEAK probe (attack D), rivals NOT shipped because each is already
covered by a shipped witness's clause or is unwitnessable: always-return-fallback,
always-propagate-error, fallback-built-from-a-different-relation, and
rebuild-the-produced-set were all written and built, and all four were REJECTED
by the frozen obligation (exit 1). No wrong impl verified; no spec hole found.

SPEC-TOO-STRONG probe (attack E), correct reshapes that the frozen spec ACCEPTS
(each built, exit 0): the functorial one-liner
``Except.ok ((solveSet rel).toOption.getD (fallbackSet rel))``; a form routing
through an impl-region helper ``pickSet``; a ``for _ in [0:1]`` loop-bearing
imperative form; and one whose success arm rebuilds the produced set through a
value-preserving projection (``⟨s.repr ++ ""⟩``, closed by
``simp [String.append_empty]; rfl``). The last is the sharpest: the spec pins the
success branch to the produced set up to EQUALITY, not up to syntax, so a faithful
reshape is admitted where a fabricating one is not. Two of these are shipped as
the positive controls; the rest are recorded here rather than shipped, since they
defend the same obligation from the same direction.

AXIOM lane: EMPTY here. The bundle declares two ``opaque`` leaves
(``solveSet`` / ``fallbackSet``, unchanged callees, A-references) and consumes no
``axiom``. The axiom lane belongs to G-AX; this gate ignores it, and the nagini
``AXIOM_TESTS`` are dropped.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-18211"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----

# The whole gold impl body (between -- impl-start / -- impl-end, markers
# exclusive). Every variant that reshapes the impl swaps against this block.
_GOLD_IMPL = (
    "def implementation_asSet (rel : Relation) : Except Unit SetExpr := Id.run do\n"
    "  let mut xset : SetExpr := fallbackSet rel\n"
    "  match solveSet rel with\n"
    "  | Except.ok s =>\n"
    "      xset := s\n"
    "  | Except.error () =>\n"
    "      xset := fallbackSet rel\n"
    "  return Except.ok xset"
)

# The frozen proof body (inside -- proof-start / -- proof-end). Only the positive
# that changes the impl AWAY from `Id.run do` needs to touch this, to drop the
# now-inapplicable `simp only [Id.run]` step.
_GOLD_PROOF = (
    "  intro rel\n"
    "  unfold problem_spec_asSet implementation_asSet\n"
    "  simp only [Id.run]\n"
    "  cases h : solveSet rel with\n"
    "  | ok s => rfl\n"
    "  | error e =>\n"
    "      cases e\n"
    "      rfl"
)

# Sanity: the anchors must appear verbatim and uniquely in _BASE.
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl block drift — re-sync _GOLD_IMPL"
assert _BASE.count(_GOLD_PROOF) == 1, "gold proof block drift — re-sync _GOLD_PROOF"


# ---------------------------------------------------------------------------
# 1. POSITIVE CONTROL (soundness) — imperative reshape that still returns
#    directly on the SUCCESS branch instead of assigning-then-returning. Keeps
#    the `Id.run do` idiom (so the frozen proof closes verbatim), but the control
#    flow is genuinely different: the ok arm returns the produced set immediately
#    rather than routing it through the mutable `xset`. Both clauses hold on every
#    input, and the frozen tactic body still closes. MUST verify; else the routing
#    obligation is SPEC-TOO-STRONG. Ports nagini's explicit-branch positive
#    control to the single modeled site (there the shape branched explicitly on
#    the read-only tag rather than letting try/except drive the dichotomy; here it
#    returns directly on success rather than threading the local).
_POS_IMP_IMPL = (
    "def implementation_asSet (rel : Relation) : Except Unit SetExpr := Id.run do\n"
    "  match solveSet rel with\n"
    "  | Except.ok s =>\n"
    "      return Except.ok s\n"
    "  | Except.error () =>\n"
    "      let mut xset : SetExpr := fallbackSet rel\n"
    "      return Except.ok xset"
)

# ---------------------------------------------------------------------------
# 2. POSITIVE CONTROL (soundness) — the pure-functional form: drop `Id.run do`
#    and the mutable local entirely, matching on the routine's outcome and
#    returning the appropriate `.ok _` directly. Value flow identical on every
#    input. Because the impl is no longer an `Id.run do`, the frozen proof's
#    `simp only [Id.run]` step no longer applies, so the proof body is reshaped
#    (proof-region edit) to drop it; the `cases` split then closes both arms by
#    `rfl`. MUST verify; a second correct shape on a different region than the
#    imperative positive.
_POS_PURE_IMPL = (
    "def implementation_asSet (rel : Relation) : Except Unit SetExpr :=\n"
    "  match solveSet rel with\n"
    "  | Except.ok s => Except.ok s\n"
    "  | Except.error () => Except.ok (fallbackSet rel)"
)
_POS_PURE_PROOF = (
    "  intro rel\n"
    "  unfold problem_spec_asSet implementation_asSet\n"
    "  cases h : solveSet rel with\n"
    "  | ok s => rfl\n"
    "  | error e =>\n"
    "      cases e\n"
    "      rfl"
)


# ---------------------------------------------------------------------------
# 2b. ADMISSIBILITY — the obligation must be SATISFIABLE, non-vacuously, at
#     exactly an F2P-shaped input. The impl region is left byte-identical to
#     gold; three `have`s are prepended to the frozen tactic body (proof-region
#     edit), each discharged BY EVALUATION at the concrete relation, and the
#     frozen obligation then closes verbatim below them.
#
#     `_F2P_REL` is the F2P-shaped point: a univariate relation whose
#     set-solving routine cannot produce an explicit set, so the TOLERATED
#     branch is the one the spec selects there.
_F2P_REL = '⟨"n*cos(n) - 3*sin(n) = 0"⟩'

# (a) the clause selected at that point ADMITS some outcome at all — there
#     exists a set `v` with `problem_spec_asSet _F2P_REL (.ok v)`. Established
#     by cases on the routine's own outcome, each arm exhibiting the witness the
#     clause names. This is the direct analogue of "the precondition admits a
#     normal input": if the selected clause were unsatisfiable here, no impl
#     could be correct at this input and the ∀ would only close vacuously.
_ADM_EXISTS = (
    "  have _admiss_satisfiable :\n"
    f"      ∃ v : SetExpr, problem_spec_asSet {_F2P_REL} (Except.ok v) := by\n"
    "    unfold problem_spec_asSet\n"
    f"    cases h : solveSet {_F2P_REL} with\n"
    "    | ok s => exact ⟨s, rfl⟩\n"
    f"    | error e => cases e; exact ⟨fallbackSet {_F2P_REL}, rfl⟩\n"
)

# (b) on the tolerated branch at that concrete point the computation's value is
#     the fallback set — the clause is met by EVALUATION of the frozen impl at
#     `_F2P_REL`, not merely by the ∀ being closed somewhere.
_ADM_VALUE = (
    f"  have _admiss_tolerated : solveSet {_F2P_REL} = Except.error () →\n"
    f"      implementation_asSet {_F2P_REL}"
    f" = Except.ok (fallbackSet {_F2P_REL}) := by\n"
    "    intro h\n"
    "    unfold implementation_asSet\n"
    "    simp only [Id.run]\n"
    "    rw [h]\n"
    "    rfl\n"
)

# (c) and at that same point the obligation holds AND the outcome is not the
#     inability escaping — the toleration clause is non-vacuously met where the
#     F2P input lands.
_ADM_TOTAL = (
    f"  have _admiss_not_error : solveSet {_F2P_REL} = Except.error () →\n"
    f"      problem_spec_asSet {_F2P_REL} (implementation_asSet {_F2P_REL})\n"
    f"      ∧ implementation_asSet {_F2P_REL} ≠ Except.error () := by\n"
    "    intro h\n"
    "    unfold problem_spec_asSet implementation_asSet\n"
    "    simp only [Id.run]\n"
    "    rw [h]\n"
    "    exact ⟨rfl, by simp⟩\n"
)

# (d) and the outcome at that concrete point is not the inability escaping
#     UNCONDITIONALLY — no branch hypothesis at all. (c) above buys this only
#     under `solveSet _F2P_REL = .error ()`, which leaves the reading "the
#     obligation is satisfiable at this input only if the routine happens to fail
#     there" open. This `have` closes it by casing on the routine's own outcome
#     and evaluating the frozen impl in each arm, so the F2P-shaped point is
#     shown live on the SPEC's own terms rather than on an assumed branch.
#     Added by the audit; measured to verify.
_ADM_TOTAL_UNCOND = (
    f"  have _admiss_never_error : implementation_asSet {_F2P_REL}"
    " ≠ Except.error () := by\n"
    "    unfold implementation_asSet\n"
    "    simp only [Id.run]\n"
    f"    cases h : solveSet {_F2P_REL} with\n"
    "    | ok s => simp\n"
    "    | error e => cases e; simp\n"
)

_ADMISS_PROOF = (_ADM_EXISTS + _ADM_VALUE + _ADM_TOTAL + _ADM_TOTAL_UNCOND
                 + _GOLD_PROOF)


# ---------------------------------------------------------------------------
# 3. TOTALITY / CONTROL-FLOW (the LITERAL pre-patch bug) — on the tolerated
#    branch, PROPAGATE the routine's inability (`.error ()`) instead of returning
#    the fallback set. Correct on the success branch; violates (C-err) only.
#    expect=reject.
_R_PROPAGATE_IMPL = (
    "def implementation_asSet (rel : Relation) : Except Unit SetExpr := Id.run do\n"
    "  let mut xset : SetExpr := fallbackSet rel\n"
    "  match solveSet rel with\n"
    "  | Except.ok s =>\n"
    "      xset := s\n"
    "      return Except.ok xset\n"
    "  | Except.error () =>\n"
    "      return Except.error ()"
)

# ---------------------------------------------------------------------------
# 4. PARTIAL-DOMAIN (wrong fallback value) — on the tolerated branch, tolerate
#    the inability (return `.ok _`, so totality holds) but return a FABRICATED
#    set rather than `fallbackSet rel`. Correct on the success branch and on
#    totality; violates (C-err)'s value pin only. expect=reject.
_R_WRONG_FALLBACK_IMPL = (
    "def implementation_asSet (rel : Relation) : Except Unit SetExpr := Id.run do\n"
    "  let mut xset : SetExpr := fallbackSet rel\n"
    "  match solveSet rel with\n"
    "  | Except.ok s =>\n"
    "      xset := s\n"
    "      return Except.ok xset\n"
    "  | Except.error () =>\n"
    "      return Except.ok ⟨\"FABRICATED\"⟩"
)

# ---------------------------------------------------------------------------
# 5. PARTIAL-DOMAIN (success branch discards the produced set) — on the SUCCESS
#    branch, return the fallback set instead of the routine's produced set.
#    Correct on the tolerated branch; violates (C-ok)'s value pin only.
#    expect=reject. (Analogue of nagini's branch-swap / fabricated-determined-
#    fields rivals: it discards the genuine solver set on the determined path.)
_R_OK_DISCARDS_IMPL = (
    "def implementation_asSet (rel : Relation) : Except Unit SetExpr := Id.run do\n"
    "  let mut xset : SetExpr := fallbackSet rel\n"
    "  match solveSet rel with\n"
    "  | Except.ok s =>\n"
    "      xset := fallbackSet rel\n"
    "  | Except.error () =>\n"
    "      xset := fallbackSet rel\n"
    "  return Except.ok xset"
)

# ---------------------------------------------------------------------------
# 6. BRANCH SWAP (the inability is tolerated on the WRONG branch) — added by the
#    audit. The three witnesses above between them probe: the `.error ()` branch
#    under the constructor pin, the `.error ()` branch under the value pin, and
#    the `.ok s` branch under the value pin. The fourth cell of that grid — the
#    `.ok s` branch under the CONSTRUCTOR pin, i.e. "may the computation report
#    the inability on a branch where the routine SUCCEEDED?" — was unprobed, and
#    the coverage reporter cannot see it (it reads binder spread, and both
#    branches are already spelled). This rival occupies it: it inverts the
#    dichotomy, propagating `.error ()` exactly where the routine produced a set
#    and returning the fallback exactly where it did not. Every existing rival is
#    correct on at least one whole branch; this one is wrong on both, and its
#    witness lands on the `.ok` branch against the constructor, which no shipped
#    witness reached. expect=reject.
_R_SWAP_BRANCHES_IMPL = (
    "def implementation_asSet (rel : Relation) : Except Unit SetExpr := Id.run do\n"
    "  match solveSet rel with\n"
    "  | Except.ok _ =>\n"
    "      return Except.error ()\n"
    "  | Except.error () =>\n"
    "      return Except.ok (fallbackSet rel)"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-return-on-success",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_IMP_IMPL),
        "rationale": (
            "structurally-different but CORRECT impl: on the success branch it "
            "returns the produced set immediately (`return Except.ok s`) instead "
            "of routing it through the mutable local, and only the tolerated "
            "branch threads `xset`. Both clauses (C-ok: return the produced set; "
            "C-err: return the fallback, never propagate the error) hold on every "
            "input, so `problem_spec_asSet rel (implementation_asSet rel)` still "
            "holds for all `rel`. Keeps the `Id.run do` idiom so the FROZEN proof "
            "body (with `simp only [Id.run]`) closes verbatim — no helper lemma, "
            "no axiom, no assumption token. Must verify; else the routing "
            "obligation is SPEC-TOO-STRONG. Ports nagini's explicit-branch "
            "positive control to the single modeled site."
        ),
    },
    {
        "id": "pos-pure-functional-form",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _GOLD_IMPL, _POS_PURE_IMPL),
            _GOLD_PROOF, _POS_PURE_PROOF,
        ),
        "rationale": (
            "a second correct shape on a different region: drop `Id.run do` and "
            "the mutable local entirely, matching on the routine's outcome and "
            "returning the appropriate `.ok _` directly. Value flow identical on "
            "every input, so both clauses hold. Because the impl is no longer an "
            "`Id.run do`, the frozen proof's `simp only [Id.run]` step no longer "
            "applies; the proof body is reshaped (proof-region edit only) to drop "
            "that one step, and the `cases` split closes both arms by `rfl`. The "
            "`theorem correct_asSet` STATEMENT is byte-identical; no new "
            "declaration, no `sorry`/`admit`/`axiom`. Must verify; defends the "
            "obligation with a shape distinct from the imperative positive."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE, non-vacuously, at exactly an
    # F2P-shaped input. On a total carrier this is the analogue of
    # PRECOND-TOO-STRONG: not "does a guard admit the input" (there is no guard)
    # but "is the clause the spec selects at that input satisfiable there at
    # all". Discharged by evaluation at the concrete point, as `have`s, before
    # the frozen obligation closes verbatim.
    # =====================================================================
    {
        "id": "admiss-f2p-tolerated-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_PROOF, _ADMISS_PROOF),
        "rationale": (
            "the impl region is byte-identical to the frozen one; three `have`s "
            "are prepended to the frozen tactic body, each discharged BY "
            "EVALUATION at one concrete F2P-shaped relation (a univariate "
            "relation the set-solving routine cannot handle, so the TOLERATED "
            "branch is the one the spec selects). (a) `_admiss_satisfiable`: the "
            "clause selected at that point admits an outcome at all — `∃ v, "
            "problem_spec_asSet rel (.ok v)` — so no impl is excluded there by "
            "an unsatisfiable clause; (b) `_admiss_tolerated`: on that branch the "
            "computation's value evaluates to `.ok (fallbackSet rel)`, i.e. the "
            "value pin is met by REDUCTION of the impl at this input rather than "
            "merely by the `∀` closing somewhere; (c) `_admiss_not_error`: at that "
            "same point the obligation holds AND the outcome is not the inability "
            "escaping, so the toleration clause bites non-vacuously exactly where "
            "the F2P input lands; (d) `_admiss_never_error`: the same "
            "no-inability-escapes conclusion with NO branch hypothesis at all, by "
            "casing on the routine's own outcome and evaluating the frozen impl in "
            "each arm — (c) alone would leave open the reading that the obligation "
            "is satisfiable here only if the routine happens to fail, and (d) "
            "closes it. Then the frozen obligation is closed verbatim. "
            "Must verify; if it cannot, the modeled behavior is unsatisfiable at a "
            "normal F2P-shaped input — the total-carrier analogue of "
            "PRECOND-TOO-STRONG. Nothing is assumed: statement byte-identical, no "
            "new declaration, no `sorry`/`admit`/`axiom`, ground instances are "
            "`have`s inside the existing tactic body. Ports nagini's "
            "`admiss-f2p-undecided-shaped`, whose precondition-admission "
            "assertions have no antecedent to satisfy on this total carrier but "
            "whose PURPOSE — showing the obligation is not vacuous at the F2P "
            "input — transfers directly."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, and
    # (b) a refutation witness pinning the violation at one conditioned point.
    # =====================================================================

    # ---- the fix itself: propagate the inability (nagini case 4) ----
    {
        "id": "totality-propagate-error",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _R_PROPAGATE_IMPL),
        "refinement": (
            "this IS the pre-patch behavior: on the tolerated branch it lets the "
            "routine's inability escape as `.error ()` rather than returning the "
            "fallback set. In the repo that is the base_commit `_eval_as_set`, "
            "which `return`s the routine's call with no `try/except`, so on the "
            "F2P relation Eq(x*cos(x)-3*sin(x),0) the routine's inability "
            "propagates out of `as_set()` instead of returning the symbolic "
            "conditional set — the F2P test (which asserts a concrete "
            "ConditionSet, not an exception) FAILS. The canonical "
            "verify-does-not-imply-resolve rival."
        ),
        "rationale": (
            "REJECT from clause (C-err): when the routine signals inability the "
            "spec requires `result = .ok (fallbackSet rel)` — in particular "
            "`result` is always `.ok _`, never `.error _` — and the rival returns "
            "`.error ()`. Correct on the success branch, so the failure isolates "
            "the toleration/totality clause. If it verifies, the spec does not "
            "actually require the inability to be tolerated (SPEC-TOO-WEAK)."
        ),
        "witness": (
            "-- Conditioned on the tolerated branch (`solveSet rel = .error ()`).\n"
            "-- The opaque `solveSet` has no computable value, so we FIX which\n"
            "-- branch it took by hypothesis; that is exactly the sub-domain where\n"
            "-- the rival diverges. Holds of the rival (it returns `.error ()`,\n"
            "-- which is never `.ok _`); fails on gold (gold returns\n"
            "-- `.ok (fallbackSet rel)`). One hypothesis, trivially satisfiable.\n"
            "example (rel : Relation) (h : solveSet rel = Except.error ()) :\n"
            "    ¬ problem_spec_asSet rel (implementation_asSet rel) := by\n"
            "  unfold problem_spec_asSet implementation_asSet\n"
            "  rw [h]\n"
            "  simp\n"
        ),
    },

    # ---- wrong fallback VALUE on the tolerated branch ----
    {
        "id": "partial-domain-wrong-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _R_WRONG_FALLBACK_IMPL),
        "refinement": (
            "on the tolerated branch this tolerates the inability (returns "
            "`.ok _`, so totality holds) but returns a fabricated set rather than "
            "the symbolic conditional set for the relation. The real analogue is "
            "returning some OTHER set object on the tolerated path (e.g. a "
            "constant set, or the universal set) instead of "
            "ConditionSet(x, self, Reals). The F2P test asserts equality with the "
            "specific ConditionSet built from the relation, so on the F2P input "
            "the produced set mismatches and the faithful real patch would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from clause (C-err)'s VALUE pin `result = .ok (fallbackSet "
            "rel)`: the rival returns `.ok ⟨\"FABRICATED\"⟩`, which is not "
            "provably equal to `.ok (fallbackSet rel)` (the fallback set is "
            "opaque, so nothing forces it to equal the fabricated literal). "
            "Correct on the success branch AND on totality, so the failure "
            "isolates the fallback-value pin. If it verifies, the tolerated "
            "branch's returned set is unpinned (partial-domain SPEC-TOO-WEAK)."
        ),
        "witness": (
            "-- Conditioned on the tolerated branch AND on the fallback set being\n"
            "-- distinguishable from the fabricated literal. Both hypotheses are\n"
            "-- about DIFFERENT opaque terms (`solveSet rel` and `fallbackSet\n"
            "-- rel`), so they are jointly satisfiable; neither computes, so the\n"
            "-- conditioning is what makes the opaque carrier attackable. Holds of\n"
            "-- the rival (it returns the fabricated set); fails on gold (gold\n"
            "-- returns `.ok (fallbackSet rel)`, which the inequality forbids the\n"
            "-- witness from refuting).\n"
            "--\n"
            "-- The inequality is stated in the orientation `simp` leaves the goal\n"
            "-- in (fabricated literal on the LEFT), and the refutation closes by\n"
            "-- `exact hne` with no `.symm` reorientation. That is deliberate: with\n"
            "-- the hypothesis written the other way round the final step is\n"
            "-- `exact fun heq => hne heq.symm`, and on gold — where `simp` has\n"
            "-- already discharged the equation, leaving `False` and no `heq` to\n"
            "-- bind — Lean reports `Invalid field notation: Type of heq is not\n"
            "-- known; cannot resolve field symm`, a SYNTACTIC failure about an\n"
            "-- unelaborated binder rather than a statement about the spec. The\n"
            "-- orientation below makes gold's failure report the hypothesis's real\n"
            "-- type instead (`{ repr := \"FABRICATED\" } ≠ fallbackSet rel but is\n"
            "-- expected to have type False`), i.e. `simp` PROVED the equation for\n"
            "-- gold and could not for the rival — the refutation, not a tactic\n"
            "-- mismatch. Both orientations discriminate (rival 0 / gold 1 either\n"
            "-- way, and a flipped-claim forgery flips gold's exit code either\n"
            "-- way); this one says so in its error text.\n"
            "example (rel : Relation) (h : solveSet rel = Except.error ())\n"
            "    (hne : (⟨\"FABRICATED\"⟩ : SetExpr) ≠ fallbackSet rel) :\n"
            "    ¬ problem_spec_asSet rel (implementation_asSet rel) := by\n"
            "  unfold problem_spec_asSet implementation_asSet\n"
            "  rw [h]\n"
            "  simp\n"
            "  exact hne\n"
        ),
    },

    # ---- success branch discards the produced set ----
    {
        "id": "partial-domain-success-discards-set",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _R_OK_DISCARDS_IMPL),
        "refinement": (
            "on the SUCCESS branch this discards the routine's produced set and "
            "returns the symbolic fallback set instead. The real analogue is a "
            "patch that returns ConditionSet(x, self, Reals) even when the routine "
            "SUCCEEDED — discarding the genuine solution set for a determined "
            "relation. The PASS_TO_PASS test test_univariate_relational_as_set "
            "observes the real solver sets on solvable relations (e.g. an Interval "
            "union), so returning the fallback there mismatches and the faithful "
            "patch would NOT resolve (it breaks the success path the fix must "
            "leave intact)."
        ),
        "rationale": (
            "REJECT from clause (C-ok)'s VALUE pin `result = .ok s`: when the "
            "routine succeeds with `s` the spec requires the produced set be "
            "returned unchanged, and the rival returns `.ok (fallbackSet rel)`, "
            "not provably equal to `.ok s`. Correct on the tolerated branch, so "
            "the failure isolates the success-branch value pin. If it verifies, "
            "the success branch is not pinned to the routine's own set "
            "(partial-domain SPEC-TOO-WEAK)."
        ),
        "witness": (
            "-- Conditioned on the SUCCESS branch (`solveSet rel = .ok s`) AND on\n"
            "-- the produced set differing from the fallback. Distinct point from\n"
            "-- the two tolerated-branch witnesses above — this is the only rival\n"
            "-- refuted on the `.ok` branch. Both hypotheses concern different\n"
            "-- opaque terms, jointly satisfiable. Holds of the rival (it returns\n"
            "-- the fallback); fails on gold (gold returns `.ok s`).\n"
            "example (rel : Relation) (s : SetExpr) (h : solveSet rel = Except.ok s)\n"
            "    (hne : fallbackSet rel ≠ s) :\n"
            "    ¬ problem_spec_asSet rel (implementation_asSet rel) := by\n"
            "  unfold problem_spec_asSet implementation_asSet\n"
            "  rw [h]\n"
            "  simp\n"
            "  exact hne\n"
        ),
    },

    # ---- the inability is reported on the branch that SUCCEEDED (audit-added) ----
    {
        "id": "totality-swap-branches",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _R_SWAP_BRANCHES_IMPL),
        "refinement": (
            "inverts the dichotomy: the routine's inability is tolerated on the "
            "branch where the routine SUCCEEDED, and the fallback set is returned "
            "on the branch where it could not produce one. The real analogue is a "
            "patch whose handler and normal-return arms are transposed. Both "
            "observable directions break at once: on a relation the routine CAN "
            "solve the inability now escapes, so the PASS_TO_PASS test that "
            "observes real solver sets on solvable relations (an Interval union, "
            "say) raises instead of returning a set; and on the F2P relation the "
            "fallback is returned for the wrong reason. The faithful patch would "
            "NOT resolve — it fails the success path the fix must leave intact."
        ),
        "rationale": (
            "REJECT from clause (C-ok)'s CONSTRUCTOR pin: when the routine "
            "succeeds with `s` the spec requires `result = .ok s`, so in "
            "particular `result` is `.ok _`; the rival returns `.error ()` there. "
            "This is the one cell of the grid the other three rivals leave open — "
            "they probe the `.error ()` branch's constructor pin, the `.error ()` "
            "branch's value pin, and the `.ok s` branch's value pin. If it "
            "verifies, the spec does not require the produced set to be returned "
            "at all on the success branch, only that SOME outcome be produced "
            "(SPEC-TOO-WEAK)."
        ),
        "witness": (
            "-- Conditioned on the SUCCESS branch alone (`solveSet rel = .ok s`).\n"
            "-- ONE hypothesis, and no inequality is needed: the violation is at\n"
            "-- the Except CONSTRUCTOR, not at the payload, so `.error () = .ok s`\n"
            "-- is refuted by `simp` from the constructors being distinct however\n"
            "-- `s` and `fallbackSet rel` compare. That is what makes this witness\n"
            "-- land at a point the `.ok`-branch VALUE witness cannot reach: that\n"
            "-- one must additionally assume `fallbackSet rel ≠ s`, and is silent\n"
            "-- wherever the two coincide, while this one bites everywhere on the\n"
            "-- branch. Measured: holds of the rival (exit 0); fails on the frozen\n"
            "-- solution with `unsolved goals rel s h ⊢ False` (exit 1) — gold\n"
            "-- SATISFIES the clause there, so `simp` closed the equation and left\n"
            "-- nothing to refute. The flipped-claim forgery (the `¬` dropped, i.e.\n"
            "-- asserting gold is CORRECT at this same point) ELABORATES on gold\n"
            "-- (exit 0) and FAILS on the rival (exit 1), so gold's exit code\n"
            "-- tracks what is claimed and the rejection is not hollow.\n"
            "example (rel : Relation) (s : SetExpr) (h : solveSet rel = Except.ok s) :\n"
            "    ¬ problem_spec_asSet rel (implementation_asSet rel) := by\n"
            "  unfold problem_spec_asSet implementation_asSet\n"
            "  rw [h]\n"
            "  simp\n"
        ),
    },
]

# No AXIOM lane here: the bundle consumes no `axiom` (two `opaque` leaves,
# `solveSet` / `fallbackSet`, are unchanged-callee A-references validated by
# G-AX, not consumed contracts). The nagini AXIOM_TESTS belong to G-AX; dropped.
AXIOM_TESTS = []
