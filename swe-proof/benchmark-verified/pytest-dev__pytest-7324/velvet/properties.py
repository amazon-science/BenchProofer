"""properties.py — G-PBT falsification battery for pytest-dev__pytest-7324 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps with a verdict. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside
``-- impl-start`` / ``-- impl-end``, or inside the ``prove_correct`` tactic
body, is changed — both regions are elided by the consumer spec view, so
``markers.same_spec`` holds and the ``prove_correct evalBareIdent`` obligation
survives with a byte-identical ``method``/``ensures`` header). It is judged by
the real verifier: ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and
FAIL against the frozen solution).

DEFENDED SURFACE — ONE modeled operation:

  evalBareIdent (ident : List Char) (matcher : List Char → Bool)
      return (out : Except CompileErr Bool)
    ensures out = Except.ok (matcher ident)

That single clause is the whole pin, and it is a CONJUNCTION of two independent
demands packed into one equation, each of which a rival can violate alone:

  (i)  the OUTCOME TAG is ``Except.ok`` for EVERY ``ident`` — no admissible
       identifier may fail to become evaluable, including the identifiers whose
       spelling coincides with one of the language's literal constants (the
       ``isReservedName`` spellings, which ``compileName`` refuses);
  (ii) the PAYLOAD is ``matcher ident`` — the acceptance test is consulted on
       the identifier AS WRITTEN, not on whatever disguised spelling the
       implementation had to route through the compiler to satisfy (i).

Both halves are GROUNDED in the method's own inputs (spec_guide directive 8):
``compileName``/``isReservedName`` are total, fully-unfolded pure ``def``s in
the ``pure`` region — not opaque answer keys — and the payload is pinned to a
free-input function applied to a method parameter. The ``axioms`` region is
EMPTY, so there is no ungrounded oracle for a wrong impl to echo. Any impl that
disguises the identifier for the compile step must therefore recover the
original spelling EXACTLY before consulting ``matcher``: the two operations are
forced to be mutual inverses by (ii), and (i) forces the disguise to be
effective on every input. That mutual-inverse obligation is what the reject
lane below attacks from six independent directions.

BINDER STRUCTURE (read before judging binder coverage). Two input binders, both
load-bearing, and the reject witnesses vary BOTH:

  * ``ident`` — the discriminating binder. The spec's demand is uniform in
    ``ident``, but implementations are not: the interesting sub-domains are the
    reserved-constant spellings (where (i) bites), the ordinary spellings (where
    (i) is free and only (ii) bites), and the spellings that COLLIDE with a
    reserved one once disguised (where an ill-chosen disguise re-creates the
    very failure it was meant to avoid). The witnesses probe all three:
    ``"True"``, ``"False"``, ``"None"``, ``"if"``, ``"rue"``.
  * ``matcher`` — the free acceptance test. It is instantiated at a concrete
    decidable lambda in every witness so the tester reduces to a ground boolean,
    and it is varied across ``fun _ => true``, ``fun _ => false`` and the
    self-recognising ``fun s => s == <the probed ident>``. Varying it matters:
    a rival that consults ``matcher`` on the WRONG spelling is invisible to a
    constant matcher (both spellings get the same verdict) and only shows up
    against a matcher that can tell the two spellings apart. FOUR of the seven
    witnesses below rely on exactly that discrimination, so ``matcher`` is not a
    binder the battery holds pinned. Measured rather than asserted: each witness
    was rebuilt with its self-recognising ``matcher`` replaced by the constant
    ``fun _ => true``, and the rival leg then FAILS for reject-no-recovery,
    reject-over-recover, reject-wrong-end and reject-selective-recovery (their
    refutations genuinely need a discriminating matcher) while it still succeeds
    for reject-colliding-disguise (whose break is in the OUTCOME TAG, clause (i),
    so it does not depend on the matcher at all).

ADVERSARIAL READ of the nagini classes on this carrier. The nagini sibling
contracts TWO functions — one that builds the disguised name, one that recovers
the original and consults the membership predicate — and ships 5 positives + 6
rivals. This bundle models the SAME logical change as ONE
method: the disguise and its inverse are a single ``do`` block, so nagini's
per-site split collapses to one obligation and its per-site rivals become
rivals against the two halves (i)/(ii) of the single clause. That is carrier
narrowing, not a thinner battery — every nagini rival that is still wrong here
is ported, and the ones that are not are listed as omitted.

  * SOUNDNESS positives — APPLY, and they must not all be cheap. Nagini's
    ``pos-encode-local`` / ``pos-lookup-local`` (read the element into a local
    before appending) are element-level reshapes of a per-character loop that
    does not exist on this carrier; their force here is carried by reshapes that
    change the DISGUISE ITSELF while keeping the value: a different disguise
    width (``pos-wider-disguise``), a different outcome-plumbing form
    (``pos-explicit-outcome-match``), and a disguise attached at the opposite END
    of the identifier with a ``take``-based inverse (``pos-trailing-disguise``).
    For the latter two a bare ``loom_solve`` was observed to leave the
    obligation OPEN, and ``pos-trailing-disguise`` additionally needed a fresh
    last-character argument to re-establish (i) — so these are load-bearing, not
    decorative. ``pos-value-only`` is retained as the maximally-different
    (disguise-free) control and is honestly labelled as the WEAKEST of the four:
    its body is the post-image verbatim, so it closes at reflexivity strength.
  * ADMISSIBILITY — nagini's two admissibility probes are self-calls that must
    establish ``Requires``. This method has NO ``require`` clause (its
    ``pre-conditions`` region is empty), so "a normal F2P input satisfies the
    precondition" is trivially true and is not where the risk sits. Nagini's
    real content there — that the precondition ADMITS the reserved-constant
    spellings the program actually contains — is re-expressed as
    ``admiss-discriminator-grounded``: an in-region ``assert`` pinning, at
    concrete inputs, that the modeled compiler REFUSES a reserved-constant
    spelling, ACCEPTS the same spelling once disguised, ACCEPTS an ordinary
    spelling, and that the disguise's inverse recovers the original. Those four
    facts are what make (i) a non-degenerate demand; if any were false the
    single ``ensures`` clause would be satisfiable without doing the work. The
    surrounding impl is kept verbatim so the method's own obligation still
    discharges alongside the assert.
  * FRAME / PERMISSION MUTATION (nagini's two MANDATORY read-only-write rivals,
    ``encode-frame-mutate`` / ``lookup-frame-mutate``) — INEXPRESSIBLE here, and
    DEMONSTRATED so rather than asserted. The nagini sibling holds each input at
    a fractional heap permission an impl can illegally overwrite. On this carrier
    ``ident`` and ``matcher`` are immutable values (neither declared ``mut``),
    there is no heap and no aliasing. The counterpart rival was actually built
    and run: assigning to the input inside the impl region
    (``ident := "True".toList``) does not yield a wrong-but-well-formed rival, it
    yields a file the front-end refuses —
    ``` `ident` cannot be mutated, only variables declared using `let mut` can be
    mutated ``` followed by ``Failed to parse an assertion without names: WPGen
    sorry``. So the mutation a nagini rival performs is not writable in this
    fragment at all; any attempt is a MALFORMED case, not a rival the spec could
    reject. Not fabricated, and not dropped for difficulty.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
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
  * UNGROUNDED-ORACLE ECHO — N/A. The ``axioms`` region declares nothing; the
    post-image is ``Except.ok (matcher ident)``, i.e. a free input applied to a
    method parameter, and the modeled compiler is a fully-unfolded ``pure``
    ``def``. There is no answer key to echo. (Nagini's ``lookup-no-strip`` is the
    wrong-ARGUMENT analogue of an echo and IS ported, as
    ``reject-no-recovery``.)
  * AXIOM LANE — EMPTY, same disposition as the nagini sibling: no ``axiom`` is
    declared or consumed, the one unchanged callee is a deep model (an
    A-reference validated by G-AX / axiom_check.py) and the acceptance test is a
    free input carrying no behavioural claim. The gate ignores ``AXIOM_TESTS``
    regardless.

WITNESS MECHANICS (specific to this carrier). The obligation is a ``method``
CONTRACT, not a bare predicate, so each witness reaches it through Velvet's own
tester machinery: ``evalBareIdentTester <ident> <matcher> = false`` says the
extracted program's result violates the postcondition at that concrete input,
checked in a file whose ``prove_correct`` block has been stripped (no tactic
script can mask the verdict).

Two carrier facts had to be measured before these witnesses could be stated,
and both are load-bearing:

  1. ``prove_postcondition_decidable_for`` cannot synthesise a decision
     procedure for the return type on its own — ``DecidableEq (Except CompileErr
     Bool)`` fails to synthesise, because the frozen ``CompileErr`` derives
     ``DecidableEq`` but ``Except`` has no such instance in scope, and the
     command then reports ``unsolved goals ... ⊢ Decidable (out = Except.ok
     (matcher ident))``. Each witness therefore supplies a COMPUTABLE
     ``instance decEqOutcome`` for that type first. This is a decision procedure
     for an already-decidable equality on a two-constructor type, introduced by
     the witness itself and hence present in BOTH builds; it assumes nothing
     about the spec, and the ``by simp`` obligations inside it are the
     constructor-disjointness facts.
  2. Unlike bundles whose impl is a ``while`` loop, this bundle's frozen impl is
     LOOP-FREE, so ``evalBareIdentExec`` kernel-reduces and the tester genuinely
     DECIDES at a literal input. That is what makes the gold-side leg of every
     witness below a SEMANTIC refutation rather than a stall: on the frozen
     solution each one fails with ``decide proved that the proposition ... is
     false``, observed verbatim for all seven. So no witness here rests on
     non-reduction, no conditioning on an opaque term is needed, and every
     witness head binds NOTHING (no hypotheses, hence nothing that could be
     jointly unsatisfiable).

Every exit code quoted in this file was observed on a real ``lean_verify.sh``
build of the exact text shipped below.

RESOLVE LINKAGE, MEASURED (independent audit). Each rival's shape was applied to
the real module at ``base_commit`` and the graded identifier cases were executed,
rather than argued about. Six of the seven rivals do break the graded set and so
carry a genuine "would not resolve" refinement; the counts in those refinements
are the measured ones. The exception is ``reject-colliding-disguise``, which is
wrong on the modeled surface yet still passes every graded case — its refinement
now says so instead of claiming a break it does not have, and the case is kept
for spec strength only. That gap is a property of the graded test set (the
scored identifiers happen to contain no proper suffix of a reserved-constant
spelling), not of this battery, and it is the one place where "the spec rejects
it" and "the test suite catches it" come apart on this cell.

SPEC-TOO-STRONG probe (attack E), measured: a CONDITIONAL-disguise impl that
disguises only the spellings that need it and inverts correspondingly — the
correct sibling of ``reject-partial-domain`` / ``reject-selective-recovery``, and
the shape most at risk of being over-rejected — was written and PROVEN (exit 0,
frozen tail applied per branch after a ``by_cases`` on the guard). Two further
correct reshapes (recovery via ``List.tail``; ``Except.bind`` plumbing) also
verify. So the clause admits conditional and alternative-inverse shapes, not just
the frozen unconditional one, and no over-strength hole was found.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-7324"
BACKEND = "velvet"

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    """Replace exactly one occurrence of an in-region substring; assert it
    actually matched, so silent drift (Solution.lean edited) fails loudly at
    manifest load rather than producing a quietly-wrong variant."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks. Each lies wholly inside the `impl` region (between
# -- impl-start and -- impl-end) or inside the `prove_correct` tactic body, and
# each is unique in Solution.lean; both facts are asserted at load by _swap.
# Editing only these keeps markers.same_spec True and the `prove_correct
# evalBareIdent` obligation present with a byte-identical method header.
# ---------------------------------------------------------------------------

# The WHOLE executable body: disguise the identifier for the compile step,
# recover the original spelling, consult the acceptance test on it.
_IMPL = """    let identPrefix : List Char := ['$']
    let name : List Char := identPrefix ++ ident
    let compiled : Except CompileErr Unit := compileName name
    let key : List Char := name.drop identPrefix.length
    let out : Except CompileErr Bool := compiled.map (fun _ => matcher key)
    return out"""

# The FULL frozen proof body. Every variant reshapes the impl, so every variant
# must retune this; the tactic body is elided from the spec view, so retuning it
# is a proof reshape, not a spec change.
_PROOF = """prove_correct evalBareIdent by
  loom_solve
  have hkey : List.drop ['$'].length (['$'] ++ ident) = ident := by simp
  have hok : compileName (['$'] ++ ident) = Except.ok () := by
    have h : isReservedName (['$'] ++ ident) = false := by unfold isReservedName; simp
    unfold compileName; rw [h]; rfl
  rw [hok, hkey]; rfl"""

# A rival never has to prove anything, so it carries the minimal honest proof
# attempt. This matters for attribution: with the frozen tactic tail dropped,
# the residual goal the verifier reports is the POSTCONDITION itself, so the
# rejection is visibly the spec refusing the impl and not a tactic mismatch.
# The observed residual for every rival below has the shape
#   ⊢ Except.map (fun x => matcher <the rival's recovered spelling>)
#       (compileName <the rival's compiled name>) = Except.ok (matcher ident)
# i.e. exactly clauses (i)+(ii) left open.
_BARE_PROOF = "prove_correct evalBareIdent by\n  loom_solve"


def _rival(impl):
    return _swap(_swap(_BASE, _IMPL, impl), _PROOF, _BARE_PROOF)


# ---------------------------------------------------------------------------
# Witness preamble. Reaches the method contract through Velvet's tester
# machinery; `evalBareIdentTester <ident> <matcher> = false` says the extracted
# program's result violates the postcondition at that concrete input.
#
# `decEqOutcome` is a COMPUTABLE decision procedure for equality on the return
# type, which `prove_postcondition_decidable_for` cannot synthesise by itself
# (measured: `failed to synthesize DecidableEq (Except CompileErr Bool)`, and
# without it the postcondition-decidability command reports `unsolved goals
# ... ⊢ Decidable (out = Except.ok (matcher ident))`). It is declared by the
# WITNESS, so it is appended to the rival file and the gold file alike and
# exists on both sides by construction; it assumes nothing about the spec.
# ---------------------------------------------------------------------------
_TESTER = """instance decEqOutcome : DecidableEq (Except CompileErr Bool) := fun a b =>
  match a, b with
  | .error .reservedConstant, .error .reservedConstant => isTrue rfl
  | .error _, .ok _ => isFalse (by simp)
  | .ok _, .error _ => isFalse (by simp)
  | .ok x, .ok y =>
    if h : x = y then isTrue (by rw [h]) else isFalse (by simp [h])

extract_program_for evalBareIdent
prove_precondition_decidable_for evalBareIdent
prove_postcondition_decidable_for evalBareIdent
derive_tester_for evalBareIdent

"""


def _witness(ident_lit, matcher_lit):
    return _TESTER + (f"example : evalBareIdentTester {ident_lit} {matcher_lit}"
                      " = false := by decide\n")


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (S.value) Maximally-different shape: no disguise, no compile step, just the
# value. Honest but the WEAKEST of the four positives — its body is the
# post-image verbatim, so `loom_solve` closes it at reflexivity strength and it
# can only detect a spec over-fit to the PRESENCE of a disguise step. Kept as
# the minimal-shape control; the other three carry the load.
_POS_VALUE_ONLY = _swap(
    _swap(_BASE, _IMPL,
          "    let out : Except CompileErr Bool := Except.ok (matcher ident)\n"
          "    return out"),
    _PROOF, _BARE_PROOF)

# (S.width) A WIDER disguise: two sentinel characters instead of one, with the
# inverse widened to match. Behaviourally identical, structurally different in
# the one quantity clause (ii) forces to agree between the two operations. The
# proof must re-establish (i) at the new width and re-derive the inverse.
_POS_WIDER = _swap(
    _swap(_BASE, _IMPL,
          "    let identPrefix : List Char := ['$', '$']\n"
          "    let name : List Char := identPrefix ++ ident\n"
          "    let compiled : Except CompileErr Unit := compileName name\n"
          "    let key : List Char := name.drop identPrefix.length\n"
          "    let out : Except CompileErr Bool := compiled.map (fun _ => matcher key)\n"
          "    return out"),
    _PROOF,
    "prove_correct evalBareIdent by\n"
    "  loom_solve\n"
    "  have hkey : List.drop ['$', '$'].length (['$', '$'] ++ ident) = ident := by simp\n"
    "  have hok : compileName (['$', '$'] ++ ident) = Except.ok () := by\n"
    "    have h : isReservedName (['$', '$'] ++ ident) = false := by\n"
    "      unfold isReservedName; simp\n"
    "    unfold compileName; rw [h]; rfl\n"
    "  rw [hok, hkey]; rfl")

# (S.match) Different outcome plumbing: an explicit `match` on the compile
# outcome instead of `Except.map`, and the inverse computed before the branch
# rather than inside the mapped function. Measured: with the frozen tactic tail
# this shape reports `No goals to be solved` (the trailing `rfl` is one step too
# many once the match has been reduced), so the tail is retuned — evidence the
# obligation is NOT closed by the frozen script's shape and the case is
# load-bearing rather than definitionally the frozen body.
_POS_EXPLICIT_MATCH = _swap(
    _swap(_BASE, _IMPL,
          "    let identPrefix : List Char := ['$']\n"
          "    let name : List Char := identPrefix ++ ident\n"
          "    let key : List Char := name.drop identPrefix.length\n"
          "    let out : Except CompileErr Bool :=\n"
          "      match compileName name with\n"
          "      | Except.error e => Except.error e\n"
          "      | Except.ok _ => Except.ok (matcher key)\n"
          "    return out"),
    _PROOF,
    "prove_correct evalBareIdent by\n"
    "  loom_solve\n"
    "  have hkey : List.drop ['$'].length (['$'] ++ ident) = ident := by simp\n"
    "  have hok : compileName (['$'] ++ ident) = Except.ok () := by\n"
    "    have h : isReservedName (['$'] ++ ident) = false := by unfold isReservedName; simp\n"
    "    unfold compileName; rw [h]; rfl\n"
    "  rw [hok, hkey]")

# (S.trailing) The sharpest correct reshape available: attach the disguise at the
# OPPOSITE END of the identifier and invert it with `take` on the length rather
# than `drop` on the front. Still correct — a trailing sentinel is just as
# effective at avoiding every reserved-constant spelling, and the inverse still
# recovers the original exactly — but nothing about the frozen proof survives:
# (i) now needs a LAST-CHARACTER argument (a name ending in the sentinel cannot
# be any of the three reserved spellings) instead of a first-character one.
# Measured: a first attempt reusing the frozen `simp`-only discharge of (i) left
# `⊢ (¬ident ++ ['$'] = ['T','r','u','e'] ∧ ...) ∧ ...` unsolved, so the case
# genuinely exercises the clause rather than the frozen script.
_POS_TRAILING = _swap(
    _swap(_BASE, _IMPL,
          "    let identSuffix : List Char := ['$']\n"
          "    let name : List Char := ident ++ identSuffix\n"
          "    let compiled : Except CompileErr Unit := compileName name\n"
          "    let key : List Char := name.take (name.length - identSuffix.length)\n"
          "    let out : Except CompileErr Bool := compiled.map (fun _ => matcher key)\n"
          "    return out"),
    _PROOF,
    "prove_correct evalBareIdent by\n"
    "  loom_solve\n"
    "  have hkey : List.take ((ident ++ ['$']).length - ['$'].length) (ident ++ ['$'])\n"
    "      = ident := by\n"
    "    simp\n"
    "  have hlast : (ident ++ ['$']).getLast? = some '$' := by simp\n"
    "  have hok : compileName (ident ++ ['$']) = Except.ok () := by\n"
    "    have h : isReservedName (ident ++ ['$']) = false := by\n"
    "      unfold isReservedName\n"
    "      simp only [Bool.or_eq_false_iff, decide_eq_false_iff_not]\n"
    "      refine ⟨⟨?_, ?_⟩, ?_⟩ <;> (intro hEq; rw [hEq] at hlast; simp at hlast)\n"
    "    unfold compileName; rw [h]; rfl\n"
    "  rw [hok, hkey]; rfl")

# (A.grounded) ADMISSIBILITY. The method has no `require` clause, so nagini's
# "a normal input establishes Requires" probe is trivial here. What IS at risk
# is that the discriminator be DEGENERATE — that the modeled compiler refuse
# nothing, or accept nothing, or that the disguise's inverse not actually
# recover the original — in which case the single `ensures` clause would be
# satisfiable without doing the work. This discharges an in-region `assert`
# pinning all four facts at concrete inputs; the surrounding impl is kept
# verbatim so the method's own obligation still discharges alongside it.
_ADMISS_GROUNDED = _swap(
    _swap(_BASE, _IMPL,
          "    assert (with_name_prefix `adm\n"
          "      (compileName (['$'] ++ \"True\".toList) = Except.ok () ∧\n"
          "       compileName \"True\".toList = Except.error .reservedConstant ∧\n"
          "       compileName \"if\".toList = Except.ok () ∧\n"
          "       (['$'] ++ \"None\".toList).drop ['$'].length = \"None\".toList))\n"
          + _IMPL),
    _PROOF,
    "prove_correct evalBareIdent by\n"
    "  loom_solve\n"
    "  all_goals\n"
    "    first\n"
    "    | (refine ⟨?_, ?_, ?_, ?_⟩ <;> simp [compileName, isReservedName])\n"
    "    | (have hkey : List.drop ['$'].length (['$'] ++ ident) = ident := by simp\n"
    "       have hok : compileName (['$'] ++ ident) = Except.ok () := by\n"
    "         have h : isReservedName (['$'] ++ ident) = false := by\n"
    "           unfold isReservedName; simp\n"
    "         unfold compileName; rw [h]; rfl\n"
    "       rw [hok, hkey]; rfl)")


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (U.none) NO DISGUISE AT ALL — the pre-image behaviour (= Solution_prepatch).
# Compile the identifier under its own spelling; the reserved-constant spellings
# are then refused and the outcome tag is `Except.error`. Attacks clause (i).
_RIVAL_NO_DISGUISE = _rival(
    "    let identPrefix : List Char := []\n"
    "    let name : List Char := identPrefix ++ ident\n"
    "    let compiled : Except CompileErr Unit := compileName name\n"
    "    let key : List Char := name.drop identPrefix.length\n"
    "    let out : Except CompileErr Bool := compiled.map (fun _ => matcher key)\n"
    "    return out")

# (U.norecover) NO RECOVERY — disguise correctly (so clause (i) holds for every
# input) but consult the acceptance test on the DISGUISED spelling. Attacks
# clause (ii) in isolation: this is the wrong-ARGUMENT rival, nagini's
# `lookup-no-strip`.
_RIVAL_NO_RECOVERY = _rival(
    "    let identPrefix : List Char := ['$']\n"
    "    let name : List Char := identPrefix ++ ident\n"
    "    let compiled : Except CompileErr Unit := compileName name\n"
    "    let key : List Char := name\n"
    "    let out : Except CompileErr Bool := compiled.map (fun _ => matcher key)\n"
    "    return out")

# (U.over) OVER-RECOVERY — the inverse removes one character too many, so the
# acceptance test is asked about a truncated spelling. Attacks (ii) via the
# WIDTH of the inverse. Nagini's `lookup-over-strip`.
_RIVAL_OVER_RECOVER = _rival(
    "    let identPrefix : List Char := ['$']\n"
    "    let name : List Char := identPrefix ++ ident\n"
    "    let compiled : Except CompileErr Unit := compileName name\n"
    "    let key : List Char := name.drop (identPrefix.length + 1)\n"
    "    let out : Except CompileErr Bool := compiled.map (fun _ => matcher key)\n"
    "    return out")

# (U.partial) PARTIAL DOMAIN — disguise only SOME of the spellings that need it
# (two of the three reserved-constant spellings), leaving the third undisguised
# and therefore refused. Correct on every input except one narrow sub-domain,
# which is what makes it the sharpest test of whether the clause is demanded
# UNIFORMLY in `ident`. Nagini's `encode-partial-first-char`.
_RIVAL_PARTIAL = _rival(
    "    let identPrefix : List Char :=\n"
    "      if ident = \"True\".toList || ident = \"False\".toList then ['$'] else []\n"
    "    let name : List Char := identPrefix ++ ident\n"
    "    let compiled : Except CompileErr Unit := compileName name\n"
    "    let key : List Char := name.drop identPrefix.length\n"
    "    let out : Except CompileErr Bool := compiled.map (fun _ => matcher key)\n"
    "    return out")

# (U.end) WRONG END — the inverse removes the right NUMBER of characters but
# from the wrong end of the disguised name. A near-miss of U.over: same width,
# different position, and it agrees with gold wherever the identifier is
# palindromic-at-the-edges, so it gets its own probe point.
_RIVAL_WRONG_END = _rival(
    "    let identPrefix : List Char := ['$']\n"
    "    let name : List Char := identPrefix ++ ident\n"
    "    let compiled : Except CompileErr Unit := compileName name\n"
    "    let key : List Char := name.take (name.length - identPrefix.length)\n"
    "    let out : Except CompileErr Bool := compiled.map (fun _ => matcher key)\n"
    "    return out")

# (U.selective) SELECTIVE RECOVERY — the NEAREST miss in the battery. It
# disguises unconditionally (so clause (i) holds everywhere, unlike U.none and
# U.partial) and it recovers correctly on exactly the sub-domain the F2P inputs
# live in (the reserved-constant spellings), so it is RIGHT at every input the
# other five rivals are refuted at. It is wrong only on ORDINARY spellings,
# where it consults the acceptance test on the disguised name. Probed there.
_RIVAL_SELECTIVE = _rival(
    "    let identPrefix : List Char := ['$']\n"
    "    let name : List Char := identPrefix ++ ident\n"
    "    let compiled : Except CompileErr Unit := compileName name\n"
    "    let key : List Char :=\n"
    "      if isReservedName ident then name.drop identPrefix.length else name\n"
    "    let out : Except CompileErr Bool := compiled.map (fun _ => matcher key)\n"
    "    return out")

# (U.collide) COLLIDING DISGUISE — the disguise/inverse pair is structurally
# PERFECT (same widths, same ends, mutual inverses, so clause (ii) holds for
# every input) but the sentinel character chosen is one an ordinary identifier
# can itself begin with. Disguising then re-creates a reserved-constant spelling
# out of an identifier that was fine, and clause (i) fails on that sub-domain.
# Attacks the one property the frozen impl's comment calls load-bearing — that
# the sentinel be outside the user-writable alphabet — and no other rival
# touches it.
_RIVAL_COLLIDE = _rival(
    "    let identPrefix : List Char := ['T']\n"
    "    let name : List Char := identPrefix ++ ident\n"
    "    let compiled : Except CompileErr Unit := compileName name\n"
    "    let key : List Char := name.drop identPrefix.length\n"
    "    let out : Except CompileErr Bool := compiled.map (fun _ => matcher key)\n"
    "    return out")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ---------------------------------
    {
        "id": "pos-value-only",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_VALUE_ONLY,
        "rationale":
            "a correct impl with NO disguise step at all — it produces the "
            "pinned value directly — must satisfy `out = Except.ok (matcher "
            "ident)`. Exercises the obligation from the maximally different "
            "(disguise-free, branch-free) shape, showing the clause pins the "
            "VALUE and not the presence of a compile round-trip; a spec that "
            "rejected it would be SPEC-TOO-STRONG on the impl's shape. NOTE "
            "(honest labelling): the body is the post-image verbatim, so this "
            "closes at reflexivity strength and is the WEAKEST of the four "
            "positives — pos-wider-disguise, pos-explicit-outcome-match and "
            "pos-trailing-disguise carry the load. (Sibling: the "
            "pos-encode-assert-grounded / cheapest-honest-impl control, whose "
            "point was that a GROUNDED pin cannot be echoed: here the cheapest "
            "impl satisfying the pin is a correct one, which is exactly what "
            "this case demonstrates.)",
    },
    {
        "id": "pos-wider-disguise",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_WIDER,
        "rationale":
            "a correct impl that disguises the identifier with a WIDER sentinel "
            "and widens the inverse to match must verify. The postcondition "
            "forces the disguise and its inverse to be mutual inverses but says "
            "nothing about their width, so varying the width while keeping them "
            "paired must be admitted; the proof has to re-establish "
            "`compileName` success at the new width and re-derive the inverse, "
            "so nothing is inherited from the frozen script. If it failed, the "
            "clause would be over-fit to one particular disguise width => "
            "SPEC-TOO-STRONG. (Sibling: pos-encode-local / pos-lookup-local, "
            "the structurally-different-but-correct reshapes of each site.)",
    },
    {
        "id": "pos-explicit-outcome-match",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_EXPLICIT_MATCH,
        "rationale":
            "a correct impl that plumbs the compile outcome through an explicit "
            "two-branch `match` instead of a mapped function, and computes the "
            "recovered spelling before the branch rather than inside it, must "
            "verify. NOT a definitional restatement of the frozen body: reusing "
            "the frozen tactic tail on this shape was observed to report `No "
            "goals to be solved`, so the obligation had to be re-closed for the "
            "new reduction behaviour. Shows the clause admits any impl whose "
            "OUTCOME is right regardless of how the success/failure branch is "
            "expressed; rejecting it would be SPEC-TOO-STRONG on the plumbing "
            "form. (Sibling: pos-lookup-local.)",
    },
    {
        "id": "pos-trailing-disguise",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_TRAILING,
        "rationale":
            "the sharpest correct reshape: attach the disguise at the OPPOSITE "
            "END of the identifier and invert it with a length-based `take` "
            "rather than a front `drop`. Still correct — a trailing sentinel "
            "avoids every reserved-constant spelling just as effectively, and "
            "the inverse still recovers the original exactly — but nothing "
            "about the frozen proof survives: success of the compile step now "
            "needs a LAST-character argument where the frozen one used a "
            "first-character argument. Measured: the frozen `simp`-only "
            "discharge left `⊢ (¬ident ++ ['$'] = ['T','r','u','e'] ∧ ...) ∧ "
            "...` unsolved, so this positive is load-bearing. Verifying here "
            "shows the clause pins the RESULT and not the side the disguise is "
            "attached to; a spec that rejected it would be SPEC-TOO-STRONG on "
            "the direction of the transformation.",
    },
    {
        "id": "admiss-discriminator-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS_GROUNDED,
        "rationale":
            "the method carries no `require` clause, so nagini's `a normal F2P "
            "input establishes Requires` probe is trivially satisfied here; its "
            "real content — that the surface ADMITS the identifiers the program "
            "actually contains, including the reserved-constant spellings — is "
            "re-expressed as a grounded in-region assert. It pins, at concrete "
            "inputs, that the modeled compiler REFUSES a reserved-constant "
            "spelling, ACCEPTS that same spelling once disguised, ACCEPTS an "
            "ordinary spelling, and that the inverse recovers the original "
            "unchanged. Those four facts are what make the single `ensures` "
            "clause a non-degenerate demand: if any failed, the clause would be "
            "satisfiable without doing the work, or would exclude an input the "
            "program must handle (PRECOND/SURFACE-TOO-STRONG). The surrounding "
            "impl is kept verbatim so the method's own obligation still "
            "discharges alongside the assert. (Siblings: admiss-encode-reserved "
            "and admiss-lookup-prefixed, merged — one obligation, one probe.)",
    },

    # ---- uniqueness rivals (must be REJECTED) ----------------------------
    {
        "id": "reject-no-disguise",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_NO_DISGUISE,
        "rationale":
            "the pre-image behaviour: compile the identifier under its own "
            "spelling. Rejection source: clause (i) of `out = Except.ok "
            "(matcher ident)` — for a reserved-constant spelling `compileName` "
            "returns `Except.error`, so the outcome tag is wrong and no value "
            "of `matcher` can repair it. With the frozen tactic tail dropped "
            "the residual goal is the postcondition itself (`⊢ Except.map ... "
            "(compileName ([] ++ ident)) = Except.ok (matcher ident)`), so the "
            "rejection is attributable to the clause and not to a tactic gap. "
            "If it VERIFIED => SPEC-TOO-WEAK (the spec would admit the "
            "pre-image). (Sibling: encode-no-sentinel.)",
        "refinement":
            "the faithful real patch is the pre-image itself — build the name "
            "node from the identifier as written. For the three F2P inputs the "
            "language's own compiler refuses that node (it raises, and on a "
            "debug interpreter trips the assertion quoted in the problem "
            "statement), so the expression never becomes evaluable and "
            "test_valid_idents[True/False/None] would FAIL. It would NOT "
            "resolve; a verifying rival here would be a true "
            "verify-does-not-imply-resolve break.",
        "witness": _witness('"True".toList', "(fun _ => true)"),
    },
    {
        "id": "reject-no-recovery",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_NO_RECOVERY,
        "rationale":
            "disguises correctly — so clause (i) holds for EVERY input — but "
            "consults the acceptance test on the DISGUISED spelling, never "
            "recovering the original. Rejection source: clause (ii); the "
            "post-image demands `matcher ident` and the impl produces `matcher "
            "(['$'] ++ ident)`, which are not equal for a `matcher` that can "
            "distinguish the two spellings (and `matcher` is a FREE input, so "
            "the spec must hold for every one of them). This is the "
            "wrong-ARGUMENT rival: the analogue of an oracle echo on the wrong "
            "argument, refuted because the argument is grounded. If it VERIFIED "
            "=> SPEC-TOO-WEAK (the acceptance test could be asked about a "
            "spelling the user never wrote). (Sibling: lookup-no-strip, = the "
            "second pre-image model.)",
        "refinement":
            "the faithful real patch disguises the name for the compile step "
            "and then hands the disguised spelling to the acceptance test. The "
            "F2P test builds an acceptance test that recognises exactly the one "
            "identifier it wrote, so it would be asked about the disguised "
            "spelling instead and would not recognise it — "
            "test_valid_idents[True/False/None] would FAIL, and so would all 19 "
            "already-passing ORDINARY valid-ident cases (measured by running "
            "this shape against the real module). The invalid-ident cases are "
            "unaffected: those spellings are rejected by the scanner before this "
            "code is reached, so they are not part of the break. It would NOT "
            "resolve.",
        "witness": _witness('"False".toList', '(fun s => s == "False".toList)'),
    },
    {
        "id": "reject-over-recover",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_OVER_RECOVER,
        "rationale":
            "the inverse removes ONE CHARACTER TOO MANY, so the acceptance test "
            "is asked about a truncated spelling. Rejection source: clause (ii) "
            "via the WIDTH of the inverse — the impl produces `matcher (drop 2 "
            "(['$'] ++ ident))`, i.e. `matcher ident.tail`, against a post-image "
            "of `matcher ident`. Distinct from reject-no-recovery (which gets "
            "the width wrong in the other direction, recovering nothing) and "
            "probed at a third identifier with its own self-recognising "
            "acceptance test. If it VERIFIED => SPEC-TOO-WEAK (the inverse's "
            "width would be unconstrained). (Sibling: lookup-over-strip.)",
        "refinement":
            "the faithful real patch mis-measures the disguise's width and "
            "strips one character too many before consulting the acceptance "
            "test. For an F2P input the test is asked about the identifier "
            "minus its first character, which it does not recognise, so "
            "test_valid_idents[True/False/None] would FAIL. It would NOT "
            "resolve.",
        "witness": _witness('"None".toList', '(fun s => s == "None".toList)'),
    },
    {
        "id": "reject-partial-domain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_PARTIAL,
        "rationale":
            "PARTIAL-DOMAIN: disguises only TWO of the three spellings that "
            "need it, leaving the third to be refused by the compile step. "
            "Correct on every other input — including both other F2P inputs — "
            "so it is the sharpest test of whether the clause is demanded "
            "UNIFORMLY in the `ident` binder rather than merely on the inputs a "
            "battery happens to probe. Rejection source: clause (i), on the "
            "single sub-domain where the guard is false; the residual goal "
            "carries the impl's own `if` unreduced, showing the verifier cannot "
            "discharge the clause for arbitrary `ident`. If it VERIFIED => "
            "SPEC-TOO-WEAK (domain-incomplete). (Sibling: "
            "encode-partial-first-char.)",
        "refinement":
            "the faithful real patch disguises the name only for an enumerated "
            "subset of the problematic spellings. The third spelling is exactly "
            "the input the test patch ADDS, so test_valid_idents[None] would "
            "still crash the compile step and FAIL. It would NOT resolve — and "
            "a battery that probed only the two enumerated spellings would miss "
            "it, which is why this rival is probed at the omitted one.",
        "witness": _witness('"None".toList', "(fun _ => false)"),
    },
    {
        "id": "reject-wrong-end",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_WRONG_END,
        "rationale":
            "the inverse removes the right NUMBER of characters but from the "
            "WRONG END of the disguised name, so the acceptance test is asked "
            "about the sentinel-plus-identifier minus its final character. "
            "Rejection source: clause (ii) via the POSITION of the inverse "
            "rather than its width — a near-miss of reject-over-recover that "
            "agrees with it nowhere in general, hence its own probe point and "
            "its own self-recognising acceptance test. If it VERIFIED => "
            "SPEC-TOO-WEAK (the clause would not force the disguise and its "
            "inverse to act on the same end). (No nagini sibling: nagini's "
            "sites are a prepend and a front-strip, so `wrong end` is not "
            "expressible there — this is a rival the carrier ADDS.)",
        "refinement":
            "the faithful real patch trims the disguise off the wrong end "
            "before consulting the acceptance test, handing it the sentinel "
            "followed by a truncated identifier. The F2P acceptance test "
            "recognises only the exact identifier written, so it would not "
            "recognise that string and test_valid_idents[True/False/None] would "
            "FAIL. It would NOT resolve.",
        "witness": _witness('"True".toList', '(fun s => s == "True".toList)'),
    },
    {
        "id": "reject-selective-recovery",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_SELECTIVE,
        "rationale":
            "the NEAREST MISS in the battery, and the reason it carries its own "
            "probe point. It disguises unconditionally (clause (i) holds "
            "everywhere) and recovers the original spelling on exactly the "
            "sub-domain the F2P inputs occupy — the reserved-constant "
            "spellings — so it is CORRECT at every RESERVED-spelling input, "
            "which is where five of the other six rivals are refuted, and a "
            "battery that only probed the F2P spellings would record it as "
            "verifying. (Precisely: it agrees with the frozen impl on the three "
            "reserved spellings; it is NOT correct at every input every other "
            "rival is refuted at — measured, it is also refuted at `\"rue\"`, "
            "the ordinary spelling reject-colliding-disguise is probed at, "
            "since that too is an ordinary spelling.) It is wrong only on "
            "ORDINARY "
            "spellings, where it consults the acceptance test on the disguised "
            "name. Rejection source: clause (ii) on that complementary "
            "sub-domain; probed at an ordinary spelling with an acceptance test "
            "that distinguishes the two candidates. If it VERIFIED => "
            "SPEC-TOO-WEAK on the non-reserved sub-domain — the exact hole a "
            "reserved-spelling-only battery would leave open.",
        "refinement":
            "the faithful real patch strips the disguise only when the "
            "identifier is one of the problematic spellings and otherwise "
            "leaves it in place. The three F2P cases would pass, but the 19 "
            "already-passing ordinary valid-ident cases (`if`, `else`, `while`, "
            "`1234`, `a[bcd]`, ...) would each have the acceptance test asked "
            "about the disguised spelling and FAIL, so the instance would NOT "
            "resolve. It is a resolve-breaking rival whose break is invisible "
            "at the F2P inputs alone.",
        "witness": _witness('"if".toList', '(fun s => s == "if".toList)'),
    },
    {
        "id": "reject-colliding-disguise",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_COLLIDE,
        "rationale":
            "the disguise/inverse pair is structurally PERFECT — same width, "
            "same end, exact mutual inverses, so clause (ii) holds for every "
            "input — but the sentinel chosen is a character an ordinary "
            "identifier can itself begin with. Disguising then MANUFACTURES a "
            "reserved-constant spelling out of an identifier that was "
            "unproblematic, and clause (i) fails on that sub-domain. Rejection "
            "source: clause (i), reached through the disguise's collision "
            "behaviour rather than through its absence — the one property no "
            "other rival touches, and the property the modeled behaviour "
            "actually depends on. If it VERIFIED => SPEC-TOO-WEAK (the spec "
            "would not force the disguise to be collision-free, so an impl "
            "could reintroduce the very failure the modeled behaviour exists to "
            "prevent). (No nagini sibling: nagini pins its sentinel to a "
            "grounded constant in the spec's own pure helper, so a "
            "colliding-sentinel rival is not expressible there. This is the "
            "second rival the carrier ADDS, and the more valuable one.)",
        "refinement":
            "HONEST LABELLING (measured, not argued — this rival's resolve "
            "linkage is WEAKER than the other six and the earlier claim here "
            "was wrong). The faithful real patch picks a disguise character "
            "drawn from the identifier alphabet rather than from outside it. "
            "Such a patch is genuinely WRONG on the modeled surface — an "
            "identifier that completes a reserved-constant spelling once "
            "disguised fails to become evaluable, and the spec refutes it at "
            "such an input (see `witness`) — but it does NOT break the scored "
            "test set: the graded identifiers were enumerated and none of them "
            "is a proper suffix of a reserved-constant spelling, so every "
            "scored case still passes and this shape would in fact RESOLVE. "
            "So this case is retained on SPEC-STRENGTH grounds only: it is the "
            "sole rival attacking collision-freedom of the disguise (a real "
            "obligation of the modeled behaviour, and one every other rival "
            "leaves untouched), and it documents a resolve-vs-correct GAP in "
            "the graded test set rather than claiming a resolve break it does "
            "not have. It is NOT evidence of verify=>resolve for this cell.",
        "witness": _witness('"rue".toList', '(fun s => s == "rue".toList)'),
    },
]

# ===========================================================================
# AXIOM LANE — none, matching the nagini sibling's disposition.
# ===========================================================================
# The `axioms` region of the frozen solution declares nothing: the one unchanged
# callee this slice relies on is modeled DEEPLY as a total `pure` def (an
# A-reference validated against the real callee by axiom_check.py / G-AX, which
# is a separate gate), and the acceptance test is a FREE INPUT carrying no
# behavioural claim the runner could falsify by execution. There is therefore no
# consumed contract for this lane to probe. The G-PBT gate ignores AXIOM_TESTS
# regardless.
AXIOM_TESTS = []
