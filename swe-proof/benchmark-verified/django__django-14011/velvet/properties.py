"""properties.py — G-PBT falsification battery for django__django-14011 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
both ``prove_correct`` headers survive). ``expect:"verify"`` passes iff (in scope
AND verifies); ``expect:"reject"`` passes iff (in scope AND does NOT verify AND
its refutation ``witness`` discriminates — the witness must ELABORATE against the
rival and FAIL against the frozen solution).

This battery is PORTED from the nagini sibling: the adversarial ARGUMENT is
carried over, the mechanics are re-expressed on this backend's carrier. The
accounting of which sibling case landed where, and which did not, is at the
bottom of this file.

DEFENDED SURFACE (two contracted methods, both over immutable value carriers):

  installPreferred (preferred registry : List (String × Int))
                                        return (out : List (String × Int))
    ensures out = preferred ++ registry                            -- (P1) VALUE
    ensures out.length = preferred.length + registry.length        -- (P2) LENGTH
    ensures ∀ p, p ∈ preferred → p ∈ out                           -- (P3) MEMBERSHIP
      Input binders: `preferred`, `registry`.
      The keyed registry is an association list under first-match lookup, so
      prepending `preferred` is exactly "the preferred bindings take precedence,
      and aliases absent from `preferred` keep their prior binding". (P1) is the
      load-bearing clause; (P2)/(P3) are independent weaker projections that a
      rival can satisfy while violating (P1), and vice versa — both directions
      are attacked below.

  releaseAll (handles : List Bool) return (out : List Bool)
    ensures out = releasedSeq handles                              -- (R1) VALUE
    ensures out.length = handles.length                            -- (R2) LENGTH
    ensures ∀ b ∈ out, b = false                                   -- (R3) UNIVERSAL
      Input binder: `handles`.
      A handle is modeled by a Bool recording whether it is currently active;
      `releasedSeq` maps every entry to inactive regardless of its prior state.
      (R2) and (R3) are again independent of each other — a rival can end every
      entry inactive while returning the wrong LENGTH, or preserve the length
      while leaving an entry active — and each is attacked separately.

Both preconditions are EMPTY (neither method carries a `require`). That removes
the LITERAL admissibility probe (there is no precondition an F2P-shaped input
could fail) but NOT the lane: on a total carrier the PRECOND-TOO-STRONG analogue
is the obligation being UNSATISFIABLE or DEGENERATE at exactly the F2P-shaped
input, since a post-image no impl can meet reads exactly like one every impl
meets, and no uniqueness rival would notice. Two `kind="admissibility"` cases
below discharge that by evaluation at the concrete overlapping-key install point
and the active-handle release point. (Audit-corrected: the port recorded the lane
as vacuous with "the frozen obligation has no precondition", which is the reason
this argument rejects.)

WHAT THE SPEC DEFENDS, and the attacks it must survive:

  * PRECEDENCE is the primary discriminator. The behavior only helps an isolated
    worker if the bindings handed to it WIN over whatever the worker already has
    for the same key. So the battery attacks precedence from both sides: a rival
    that ignores the handed-in set entirely (keeps the registry as-is), a rival
    that discards the prior registry, a rival that merges in the WRONG order (so
    first-match resolves to the stale binding), and — the sharpest — a rival that
    installs a handed-in binding only when its key is NOT already present, which
    is correct on every disjoint input and wrong exactly on the overlap, the one
    sub-domain that motivates the behavior at all. And from the opposite side, an
    OVER-REACH: a rival that rebinds the value of every key the parent did NOT
    hand over, keeping the key-set, the positions and the length intact.
  * UNIVERSALITY is the release-side discriminator. "Every handle ends inactive"
    is a ∀ over the whole carrier, so partial coverage is the reasoned attack:
    release all but the last, which is right exactly on the registries whose LAST
    handle is already inactive and wrong on every other one (audit-measured — it
    is already wrong at the single-entry active registry [true], not only on
    longer ones).
  * DOMAIN-COMPLETENESS on both sides. Each value clause is pinned over the WHOLE
    input, including the last element, so a loop that stops one short must fail.
  * The post-images are GROUNDED in the method's own inputs (`preferred ++
    registry`; a total fold `releasedSeq handles`). The ``axioms`` region is
    EMPTY, so there is no opaque answer key for a wrong impl to echo, and the
    ungrounded-oracle probe has no counterpart here.

THE CARRIER IS FULLY TRANSPARENT (String × Int pairs and Bools; no `opaque`
term anywhere), so every witness is stated at CONCRETE LITERAL inputs and no
witness binds a hypothesis — there is no carrier-conditioning here and therefore
no joint-satisfiability obligation on any witness in this file.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION-MUTATION — VACUOUS. The sibling carries TWO such rivals as
    its self-declared #1 weakness class, because there the parent-supplied set
    and the identity list are held read-only and a store through them must fail
    for insufficient permission. Lean and Velvet are referentially transparent:
    every parameter here is an immutable value, no binder is declared `mut`,
    there is no heap and no aliasing, so there is no read-only input to overwrite
    and no substitute probe to build. Not fabricated.
  * CAPABILITY PROVENANCE — NO COUNTERPART. The sibling's two sharpest rivals
    (omit the configuration step; obtain the capability for a DIFFERENT server
    and pass it off as this one's) attack an abstract body-less predicate whose
    sole producer is a consumed axiom. This bundle has no consumed axiom and no
    capability predicate: the configuration step is modeled as the R-leg framing
    (the method TAKES the handed-in set as a parameter — a function that consumes
    it can only exist where it is accepted), not as a separate obligation. So
    there is no capability to launder and nothing to omit. The BEHAVIORAL content
    of the omission rival — the worker ends up operating on its own bindings
    rather than the handed-in ones — does port, and is `weak-ignore-preferred`
    below, which is also this bundle's `Solution_prepatch.lean` shape.
  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the heart of the port. Both sibling
    partial-domain rivals port near 1:1, plus the no-close rival, plus three
    added rivals isolating clauses this carrier exposes that nagini's did not.
  * DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here,
    and a diverging rival is REJECTED rather than admitted. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
    two lines have to move together, and they do here. Under the total scope a
    postcondition is claimed of ALL runs, not only of terminating ones, and the
    verifier emits a descent obligation ``measure b' < measure b`` for every
    loop in the impl (2 loops here, measures ``i``). A rival that loops without
    a measure is refused outright (``Decreasing annotations are required in
    total correctness semantics``), and a rival that supplies a CONSTANT
    measure to dodge that is refused on the measure's own goal (``case
    «decreasing_1: spin» ... ⊢ spin < spin``), re-measured on this bundle with
    a real build. Divergence therefore does not discharge the ``ensures``
    clauses vacuously. It is still not shipped as a G-PBT reject case, and the
    reason is the witness contract rather than a spec weakness. A reject case
    must carry a witness that ELABORATES against the rival, and neither diverging
    shape gets past that. With NO measure the descent obligation fails at the
    ``method`` itself, ahead of any appended tester, and the witness file retains
    the ``method`` (it strips only the ``prove_correct`` obligations), so the rival
    module does not compile at all. With a measure that does not decrease the
    refusal moves to the ``prove_correct`` site, which IS stripped, so that module
    does elaborate; but the rival's post-image is then an unreduced
    ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` / ``onDoneGadget`` /
    ``decreasingGadget``, which the kernel will not normalise to a value a
    concrete-input tester can decide. Either way the gate returns
    ``witness-unproven``, an inconclusive outcome. Measured through the
    gate's own ``_check_witness``, even ``example : True := trivial`` comes
    back ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome
    and would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.

DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging rival
is REJECTED rather than admitted. This bundle sets
``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
and the ``open`` is the line that actually selects the semantics: both
namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and
the ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
two lines have to move together, and they do here. Under the total scope a
postcondition is claimed of ALL runs, not only of terminating ones, and the
verifier emits a descent obligation ``measure b' < measure b`` for every loop
in the impl (2 loops here, measures ``i``). A rival that loops without a
measure is refused outright (``Decreasing annotations are required in total
correctness semantics``), and a rival that supplies a CONSTANT measure to dodge
that is refused on the measure's own goal (``case «decreasing_1: spin» ... ⊢
spin < spin``), re-measured on this bundle with a real build. Divergence
therefore does not discharge the ``ensures`` clauses vacuously. It is still not
shipped as a G-PBT reject case, and the reason is the witness contract rather
than a spec weakness. A reject case must carry a witness that ELABORATES
against the rival, and neither diverging shape gets past that. With NO measure
the descent obligation fails at the ``method`` itself, ahead of any appended
tester, and the witness file retains the ``method`` (it strips only the
``prove_correct`` obligations), so the rival module does not compile at all. With
a measure that does not decrease the refusal moves to the ``prove_correct`` site,
which IS stripped, so that module does elaborate; but the rival's post-image is
then an unreduced ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` /
``onDoneGadget`` / ``decreasingGadget``, which the kernel will not normalise to a
value a concrete-input tester can decide. Either way the gate returns
``witness-unproven``, an inconclusive outcome.
Measured through the gate's own ``_check_witness``, even
``example : True := trivial`` comes back ``witness-unproven`` on this rival,
which is an INCONCLUSIVE outcome and would fail the whole battery rather than
pass a case. That is the right behavior: a diverging impl has no output at any
input, so there is no value for a witness to disagree with, and its rejection
is a judgement of the termination obligation rather than a postcondition
violation at a point. Recorded as REJECTED-BY-SPEC and not expressible as a
witnessed case, which is neither a spec hole nor a battery gap.

WITNESS MECHANICS (specific to this carrier). Each obligation is a ``method``
CONTRACT, not a bare predicate, so a witness reaches it through Velvet's own
tester machinery: ``<name>Tester <args> = false`` says the extracted program's
result violates the postcondition at that concrete input, checked in a file whose
``prove_correct`` blocks have been stripped, so no tactic script can mask the
verdict.

THE ASYMMETRY, STATED HONESTLY. Both frozen impls are backward ``while`` loops
whose extracted programs do NOT kernel-reduce: a ``decide`` on either tester gets
stuck for EVERY input, including inputs where the frozen program is RIGHT
(measured: ``installPreferredTester [("a", 1)] [] = true`` and
``releaseAllTester [true] = true`` — both TRUE claims about the frozen solution —
also fail to elaborate, "did not reduce to isTrue or isFalse"). Every reject
rival below is reshaped into a loop-free closed form so that its tester DOES
reduce; consequently the gate's gold-side leg (the witness must FAIL on the
frozen solution) is satisfied by NON-REDUCTION rather than by refutation, and on
its own it therefore attests nothing.

WHAT CLOSES IT. Each witness states its refutation in three machine-checked
parts, so its force does not rest on the gold-side stall:

  (a) ``<name>Exec <input> = DivM.res <concrete wrong value>`` by ``rfl`` — pins
      the value the rival's extracted program actually returns, which also rules
      out the tester's ``| _ => false`` arm as the source of ``Tester = false``;
  (b) ``<concrete wrong value> ≠ <the spec's own post-image at that input>`` by
      ``decide`` — that value is wrong per the SPEC, decided on ground data with
      no reference to any implementation;
  (c) the ``Tester = false`` claim the gate's protocol consumes.

(a)+(b) are a self-contained counterexample: the rival returns X and the spec's
post-image at that input is not X. Independently cross-checked out-of-band
(recorded here, not gate-visible): every witness below was ALSO built against a
CORRECT loop-free implementation (``return preferred ++ registry`` /
``return releasedSeq handles``) and each FAILED there — leg (a) with ``rfl
failed: not definitionally equal``, and leg (c) with ``decide proved that the
proposition ... = false is false``, i.e. ``decide`` positively established that
the correct impl SATISFIES the contract at that very input. That is the check the
gate structurally cannot run, and it is what shows these rivals are refuted for
being WRONG rather than for being loop-free. Every exit code quoted in this file
was observed on a real ``scripts/lean_verify.sh`` build.

THE FORGERY TEST, which is what actually settles it. "The subject-side error
looks semantic" is not evidence; an error is admissible only if it CHANGES when
the CLAIM changes. So for all ten reject cases the second audit built a FORGERY
differing from the witness only in what it asserts — the OPPOSITE claim, namely
that the subject impl is CORRECT at exactly the witness's input
(``<name>Exec <input> = DivM.res <the spec's own post-image>`` and
``<name>Tester <input> = true``) — and built it on every side:

  * against the gate's discrimination SUBJECT (the verifying positive): the
    forgery ELABORATES, exit 0, all ten. The real witness FAILS there, exit 1.
    Same file shape, opposite claim, opposite exit code — so the subject-side
    exit code tracks the claim and carries real information.
  * against each RIVAL: the forgery FAILS, exit 1, all ten — the mirror image,
    confirming the rival is the impl that is wrong at that point.
  * against the FROZEN solution: the forgery fails too, exit 1, all ten, with
    the same ``did not reduce to isTrue or isFalse`` stall as the real witness.
    That is the honest measurement of the asymmetry declared above: gold's exit
    code is claim-INDEPENDENT and attests nothing, which is precisely why the
    gate falls back to a verifying positive and why these cases are scored
    against one.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom``; both callees are
deep A-references validated == the real callee by axiom_check.py, which is G-AX's
job. The sibling's five ``AXIOM_TESTS`` are dropped — this gate ignores them.
"""
from pathlib import Path

INSTANCE = "django__django-14011"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside an impl region (between -- impl-start and
# -- impl-end) or inside a prove_correct tactic body, and each is unique in
# Solution.lean; both facts are asserted at load by _swap. Editing only these
# keeps markers.same_spec True and both prove_correct headers present (the spec
# view elides both regions).
# ---------------------------------------------------------------------------

# The WHOLE executable body of installPreferred: the backward loop that prepends
# each preferred binding so first-match lookup gives it precedence. Reject rivals
# replace this with a loop-free closed form (so their tester reduces under
# `decide`); so does the closed-form positive control.
_IP_IMPL = """    let mut result : List (String × Int) := registry
    let mut i := preferred.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ preferred.length
      invariant result = preferred.drop i ++ registry
      done_with i = 0
      decreasing i
    do
      let kv := preferred[i - 1]!
      result := kv :: result
      i := i - 1
    return result
"""

# The FULL frozen installPreferred proof body. A positive control that collapses
# the loop retunes this; the tactic body is elided from the spec view, so that is
# a proof reshape, not a spec change. Reject rivals keep it as-is (it fails to
# close for a wrong impl, which is the intended rejection, but the WITNESS — not
# the tactic failure — is what the gate scores).
_IP_PROOF = """prove_correct installPreferred by
  loom_solve
  rw [overlay_drop_step preferred registry i (by omega) (by omega)]
  simp_all
"""

# The two-line loop body of installPreferred: bind the current preferred entry to
# a local, then prepend it. The let-inlining positive control fuses these.
_IP_LOOP_BODY = """      let kv := preferred[i - 1]!
      result := kv :: result
"""

# The WHOLE executable body of releaseAll: the backward loop that builds the
# all-inactive image one entry at a time.
_RA_IMPL = """    let mut result : List Bool := []
    let mut i := handles.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ handles.length
      invariant result = releasedSeq (handles.drop i)
      done_with i = 0
      decreasing i
    do
      result := false :: result
      i := i - 1
    return result
"""

# The FULL frozen releaseAll proof body.
_RA_PROOF = """prove_correct releaseAll by
  loom_solve
  rw [released_drop_step handles i (by omega) (by omega)]
  simp_all
"""


# The FIRST line of each impl region, used as the splice point for the
# admissibility asserts below: an `assert` placed here runs BEFORE the frozen
# loop and leaves the whole rest of the impl (and both frozen proof bodies)
# byte-identical, so the method's own obligation still discharges exactly as
# frozen and the only new goal is the assert's own.
_IP_IMPL_HEAD = "    let mut result : List (String × Int) := registry\n"
_RA_IMPL_HEAD = "    let mut result : List Bool := []\n"


def _ip_admiss(assert_body):
    """Solution.lean with `assert_body` spliced at the head of installPreferred."""
    return _swap(_BASE, _IP_IMPL_HEAD, assert_body + _IP_IMPL_HEAD)


def _ra_admiss(assert_body):
    """Solution.lean with `assert_body` spliced at the head of releaseAll."""
    return _swap(_BASE, _RA_IMPL_HEAD, assert_body + _RA_IMPL_HEAD)


def _ip_rival(expr):
    """Solution.lean whose installPreferred body is one loop-free `return`."""
    return _swap(_BASE, _IP_IMPL, f"    return ({expr})\n")


def _ra_rival(expr):
    """Solution.lean whose releaseAll body is one loop-free `return`."""
    return _swap(_BASE, _RA_IMPL, f"    return ({expr})\n")


# ---- witness preambles. Reach each method contract through Velvet's tester
# ---- machinery: `<name>Tester <args> = false` says the extracted program's
# ---- result violates the postcondition at that concrete input. Appended to
# ---- BOTH the rival and the frozen file, so the derived names exist on both
# ---- sides by construction.
_IP_TESTER = ("extract_program_for installPreferred\n"
              "prove_precondition_decidable_for installPreferred\n"
              "prove_postcondition_decidable_for installPreferred\n"
              "derive_tester_for installPreferred\n\n")
_RA_TESTER = ("extract_program_for releaseAll\n"
              "prove_precondition_decidable_for releaseAll\n"
              "prove_postcondition_decidable_for releaseAll\n"
              "derive_tester_for releaseAll\n\n")


def _ip_witness(pref, reg, got):
    """Three-part refutation for installPreferred at a concrete (pref, reg)."""
    return _IP_TESTER + (
        "-- (a) the value the rival's extracted program actually returns\n"
        f"example : installPreferredExec {pref} {reg}\n"
        f"    = DivM.res {got} := by rfl\n\n"
        "-- (b) that value is NOT the one the spec's post-image names here\n"
        f"example : ({got} : List (String × Int)) ≠ {pref} ++ {reg} := by decide\n\n"
        "-- (c) hence the contract is violated at this input\n"
        f"example : installPreferredTester {pref} {reg} = false := by decide\n")


def _ra_witness(handles, got):
    """Three-part refutation for releaseAll at a concrete `handles`."""
    return _RA_TESTER + (
        "-- (a) the value the rival's extracted program actually returns\n"
        f"example : releaseAllExec {handles}\n"
        f"    = DivM.res {got} := by rfl\n\n"
        "-- (b) that value is NOT the one the spec's post-image names here\n"
        f"example : ({got} : List Bool) ≠ releasedSeq {handles} := by decide\n\n"
        "-- (c) hence the contract is violated at this input\n"
        f"example : releaseAllTester {handles} = false := by decide\n")


_EMPTY_REG = "([] : List (String × Int))"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Each keeps its `ensures` clauses byte-identical and only
    # reshapes the executable surface (and, where the reshape makes the frozen
    # loop lemma inapplicable, the tactic body — which the spec view elides).
    # =====================================================================
    {
        "id": "pos-install-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the accumulating loop to the closed form the post-image names
        # directly: a completely different control-flow shape (no loop, no
        # accumulator, no index) computing the same merge. The loop-specific
        # rewrite is dropped because there is no longer a loop step to fold, so
        # `loom_solve` closes the residual goal outright.
        "module": _swap(
            _swap(_BASE, _IP_IMPL, "    return preferred ++ registry\n"),
            _IP_PROOF, "prove_correct installPreferred by\n  loom_solve\n"),
        "rationale": "the post-image `preferred ++ registry` is GROUNDED in the "
                     "method's own inputs (no opaque answer key), so returning it "
                     "directly is the honest cheapest CORRECT impl and MUST verify "
                     "— clause (P1) is literally `out = preferred ++ registry`. If "
                     "it failed, (P1) would be over-fit to the accumulating-loop "
                     "FORM => SPEC-TOO-STRONG. It doubles as evidence the clause is "
                     "not echo-vulnerable: there is no oracle to echo, and any "
                     "wrong constant fails (P1). Observed: verifies (exit 0). "
                     "(Ports the sibling's structurally-different-but-correct "
                     "install positive.)",
    },
    {
        "id": "pos-install-inline-binding",
        "kind": "soundness",
        "expect": "verify",
        # Keep the backward loop and EVERY invariant byte-identical; fuse the
        # local binding into the prepend. The smallest honest reshape available
        # on this impl, and it needs no proof retune at all — so it isolates
        # "does the obligation depend on the loop body's syntactic form" from
        # "does it depend on the algorithm".
        "module": _swap(_BASE, _IP_LOOP_BODY,
                        "      result := preferred[i - 1]! :: result\n"),
        "rationale": "a faithful reshape that inlines the loop's local binding "
                     "into the prepend, keeping the loop, its bound, its invariant "
                     "and the frozen proof script all byte-identical. Same "
                     "per-step transition, different data shape. MUST verify; if "
                     "it did not, the obligation would depend on the loop body's "
                     "syntactic form rather than on its behavior => "
                     "SPEC-TOO-STRONG. Observed: verifies (exit 0) with no proof "
                     "retune.",
    },
    {
        "id": "pos-release-map",
        "kind": "soundness",
        "expect": "verify",
        # A structurally different CORRECT release: a single traversal mapping
        # every entry to inactive, instead of the backward accumulating loop.
        # `List.map` is not definitionally the front-recursive fold, so the proof
        # is retuned to a two-case induction (still only the tactic body, and it
        # introduces no lemma and assumes nothing).
        "module": _swap(
            _swap(_BASE, _RA_IMPL, "    return handles.map (fun _ => false)\n"),
            _RA_PROOF,
            "prove_correct releaseAll by\n"
            "  loom_solve\n"
            "  induction handles with\n"
            "  | nil => rfl\n"
            "  | cons c cs ih => simp_all [releasedSeq_cons]\n"),
        "rationale": "a structurally different CORRECT release: one forward "
                     "traversal sending every entry to inactive, versus the frozen "
                     "backward accumulation. Extensionally equal to the fold the "
                     "post-image names, so all three release clauses (R1)/(R2)/"
                     "(R3) must still discharge; the proof is retuned to a "
                     "two-case induction over the frozen `releasedSeq_cons` lemma "
                     "(tactic body only — no new lemma, no assumption). MUST "
                     "verify, else the release clauses are over-fit to the "
                     "accumulation shape => SPEC-TOO-STRONG. Observed: verifies "
                     "(exit 0). (Ports the sibling's structurally-different-but-"
                     "correct teardown positive; its close-before-release reorder "
                     "has no counterpart, as this carrier has a single write.)",
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG) — the lane the port dropped, landed by
    # the audit. Neither method carries a `require`, so the literal "a normal
    # input satisfies the precondition" probe has no precondition to satisfy.
    # That does NOT make the lane vacuous: on a TOTAL carrier the analogue is
    # the obligation being UNSATISFIABLE or DEGENERATE at exactly the
    # F2P-shaped input — a post-image no impl can meet reads exactly like one
    # every impl meets, and nothing else in this battery would notice. Each
    # case below discharges an in-region `assert`, at a concrete F2P-shaped
    # point, that the post-image is jointly satisfiable there AND non-degenerate
    # in the direction the behavior exists for; the rest of the impl and BOTH
    # frozen proof bodies are kept byte-identical, so the method's own
    # obligation still discharges as frozen. The asserts are LIVE, not
    # decoration: audit-measured, negating one claim in each leaves `unsolved
    # goals` (exit 1) while the true form needs no proof retune at all (exit 0).
    # =====================================================================
    {
        "id": "admiss-install-overlap-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        # The F2P-shaped install point: ONE handed-in binding for a key the
        # worker ALREADY has. Asserts the post-image at that point (a) resolves
        # the shared key to the HANDED-IN value under first-match lookup — the
        # whole content of "precedence" — (b) keeps BOTH bindings, so precedence
        # is not implemented by deletion, and (c) is NOT the reversed merge, so
        # the clause is orientation-sensitive at this very point rather than
        # merely somewhere. Jointly satisfiable => the obligation is meetable
        # here; if any conjunct failed, (P1) would be unsatisfiable or degenerate
        # at the one input the behavior exists for => PRECOND-TOO-STRONG.
        "module": _ip_admiss(
            '    assert (with_name_prefix `admiss\n'
            '      ((([("default", (7 : Int))] ++ [("default", (0 : Int))]).find?\n'
            '          (fun q => q.1 == "default")) = some ("default", (7 : Int))\n'
            '        ∧ ([("default", (7 : Int))] ++ [("default", (0 : Int))]).length = 2\n'
            '        ∧ ([("default", (7 : Int))] ++ [("default", (0 : Int))])\n'
            '            ≠ [("default", (0 : Int)), ("default", (7 : Int))]))\n'),
        "rationale": "the install obligation is SATISFIABLE and NON-DEGENERATE at "
                     "the F2P-shaped point where one handed-in binding overlaps a "
                     "key the registry already has — the only sub-domain the "
                     "behavior exists for. Three conjuncts, all discharged by "
                     "evaluation on ground data: first-match lookup over the "
                     "post-image `preferred ++ registry` returns the HANDED-IN "
                     "value (not the prior one), the merge keeps BOTH bindings "
                     "(precedence is not deletion), and the post-image is NOT the "
                     "reversed merge (so (P1) is orientation-sensitive AT this "
                     "point, not merely somewhere). If any conjunct failed, (P1) "
                     "would be unsatisfiable or degenerate exactly where it must "
                     "bite => PRECOND-TOO-STRONG, and every uniqueness rival below "
                     "would be rejecting against an obligation no impl can meet. "
                     "The impl after the assert and BOTH frozen proof bodies are "
                     "byte-identical, so `out = preferred ++ registry` still "
                     "discharges as frozen. Observed: verifies (exit 0) with NO "
                     "proof retune; negating the first conjunct (the stale binding "
                     "wins) leaves `unsolved goals` (exit 1), so the assert is "
                     "live. (Lands the sibling's admiss-serve lane, which the port "
                     "recorded as vacuous on the grounds that the frozen "
                     "obligation carries no `require` — see the accounting.)",
    },
    {
        "id": "admiss-release-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        # The F2P-shaped release point: an ACTIVE handle. Asserts the post-image
        # (a) actually FLIPS it (so the release clause is not degenerately
        # satisfied by the identity at the interesting state), (b) preserves
        # length there, and (c) satisfies the ∀ at a MIXED-state input — the
        # three release clauses jointly, at a concrete point.
        "module": _ra_admiss(
            '    assert (with_name_prefix `admiss\n'
            '      (releasedSeq [true] = [false]\n'
            '        ∧ (releasedSeq [true]).length = ([true] : List Bool).length\n'
            '        ∧ (∀ b ∈ releasedSeq [true, false], b = false)))\n'),
        "rationale": "the release obligation is SATISFIABLE and NON-DEGENERATE at "
                     "the F2P-shaped point that motivates the behavior: a handle "
                     "that is ACTIVE. Asserts, by evaluation, that the post-image "
                     "`releasedSeq` actually FLIPS that handle (so (R1) is not "
                     "degenerately met by the identity at the one state where it "
                     "must bite), that it preserves the length there (R2), and "
                     "that the universal clause (R3) holds at a MIXED-state input "
                     "— all three release clauses jointly, at concrete points. If "
                     "any failed, the release obligation would be unsatisfiable or "
                     "vacuous exactly at the interesting state => "
                     "PRECOND-TOO-STRONG. Impl after the assert and both frozen "
                     "proof bodies byte-identical. Observed: verifies (exit 0) with "
                     "no retune; asserting instead that the active handle stays "
                     "active leaves `unsolved goals` (exit 1), so the assert is "
                     "live. (Lands the sibling's admiss-teardown lane.)",
    },


    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form carrying a
    # three-part machine-checked refutation at a concrete input, and the
    # refinement argument for why its faithful counterpart would NOT resolve.
    # =====================================================================
    {
        "id": "weak-ignore-preferred",
        "kind": "uniqueness",
        "expect": "reject",
        # THE central differential (this bundle's pre-image shape): return the
        # registry untouched, ignoring the handed-in bindings entirely.
        "module": _ip_rival("registry"),
        "refinement": "this IS the pre-image behavior: the isolated worker "
                      "operates against the bindings it already has and never "
                      "installs the ones handed to it by its parent. On the "
                      "evaluated configuration a key that resolves to a "
                      "worker-local binding resolves to a FRESH, EMPTY store "
                      "rather than the populated one the parent set up, so the "
                      "failing tests that require data and fixtures written on the "
                      "parent side to be visible to the worker still observe an "
                      "empty store and FAIL. A faithful counterpart would NOT "
                      "resolve.",
        "rationale": "REJECT from (P1) `out = preferred ++ registry`: the rival "
                     "returns `registry`, which differs whenever `preferred` is "
                     "non-empty — so it also violates (P2) LENGTH and (P3) "
                     "MEMBERSHIP there. If it verified, the spec would admit the "
                     "pre-image => SPEC-TOO-WEAK (and the recorded G-DIFF result "
                     "would be unreproducible). Refuted at preferred=[(\"a\", 1)], "
                     "registry=[]: the rival's extracted program returns [] "
                     "(pinned by `rfl`) where the post-image names [(\"a\", 1)]. "
                     "Varies `preferred` off empty while holding `registry` empty. "
                     "Cross-checked against a CORRECT loop-free impl: the same "
                     "witness FAILS there, with `decide` positively proving the "
                     "contract HOLDS at this input — so the refutation tracks "
                     "wrongness, not loop-freeness. (Sibling: rival-omit-handoff, "
                     "behavioral content only — see the capability note in the "
                     "docstring.)",
        "witness": _ip_witness('[("a", 1)]', _EMPTY_REG, _EMPTY_REG),
    },
    {
        "id": "weak-discard-registry",
        "kind": "uniqueness",
        "expect": "reject",
        # The mirror error: install the handed-in bindings but THROW AWAY the
        # prior registry, so keys the parent did not hand over lose their
        # binding. Attacks the same clause from the opposite side, and is the
        # only rival that moves `registry` while holding `preferred` empty.
        "module": _ip_rival("preferred"),
        "refinement": "a counterpart that replaced the registry with the handed-in "
                      "set, rather than overlaying it, would drop every binding the "
                      "parent did not hand over — so any key the worker legitimately "
                      "resolves on its own becomes unbound and the request handling "
                      "that touches it errors instead of proceeding. That breaks "
                      "currently-passing request-handling behavior as well as the "
                      "target tests, so it would NOT resolve.",
        "rationale": "REJECT from (P1) `out = preferred ++ registry`: the rival "
                     "returns `preferred`, dropping the registry tail, so it "
                     "differs whenever `registry` is non-empty. Note it still "
                     "satisfies (P3) MEMBERSHIP at every input — which is exactly "
                     "why (P3) alone would be too weak and (P1) is load-bearing. "
                     "Refuted at preferred=[], registry=[(\"b\", 2)]: the rival "
                     "returns [] where the post-image names [(\"b\", 2)]. This is "
                     "the case that VARIES `registry` (and pins `preferred` at "
                     "empty), the complement of weak-ignore-preferred's point. "
                     "Cross-checked against a CORRECT loop-free impl: the witness "
                     "FAILS there (`decide` proves the contract holds). (Added: no "
                     "sibling — nagini's carrier writes elements in place, so it "
                     "cannot express dropping the carrier's tail.)",
        "witness": _ip_witness(_EMPTY_REG, '[("b", 2)]', _EMPTY_REG),
    },
    {
        "id": "weak-wrong-precedence",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS on the ORDER: merge both sides but the WRONG way round, so
        # first-match lookup resolves a shared key to the STALE binding. Keeps
        # every element and the exact length — it satisfies (P2) and (P3) at
        # every input and violates only (P1).
        "module": _ip_rival("registry ++ preferred"),
        "refinement": "a counterpart that merged the handed-in bindings with lower "
                      "rather than higher precedence would leave every key the "
                      "worker already has resolving to the worker's own binding, "
                      "which for the evaluated configuration is the fresh empty "
                      "store — the parent's populated one is present in the merge "
                      "but never selected. The data-visibility tests observe the "
                      "resolved binding, so they still FAIL: it would NOT resolve.",
        "rationale": "REJECT from (P1) `out = preferred ++ registry`, which pins "
                     "ORDER and not just content: the rival's result is a "
                     "PERMUTATION of the correct one, so it satisfies (P2) LENGTH "
                     "and (P3) MEMBERSHIP at EVERY input and is refutable only by "
                     "(P1). A spec pinning only length and membership would MISS "
                     "this => SPEC-TOO-WEAK, which is precisely why this case is "
                     "here. Refuted at preferred=[(\"a\", 1)], "
                     "registry=[(\"b\", 2)]: the rival returns "
                     "[(\"b\", 2), (\"a\", 1)] where the post-image names "
                     "[(\"a\", 1), (\"b\", 2)] — the first input point at which "
                     "BOTH binders are non-empty, so it exercises the interaction "
                     "the two preceding rivals cannot. Cross-checked against a "
                     "CORRECT loop-free impl: the witness FAILS there. (Added by "
                     "audit; no sibling.)",
        "witness": _ip_witness('[("a", 1)]', '[("b", 2)]',
                               '[("b", 2), ("a", 1)]'),
    },
    {
        "id": "weak-partial-install",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN, install side: overlay every handed-in binding EXCEPT
        # the last (the install loop stops one short). Correct EXACTLY when the
        # handed-in set is EMPTY, and wrong on every non-empty one — a length-1
        # handed-in set is already refuted, because the one entry it has IS the
        # last one and is therefore the one dropped. (Audit-corrected: the port's
        # prose claimed agreement on every handed-in set of size ≤1, which is
        # false; machine-checked below.)
        "module": _ip_rival("preferred.dropLast ++ registry"),
        "refinement": "an install that stops one short leaves the last handed-in "
                      "binding uninstalled, so requests resolving that key get a "
                      "fresh worker-local binding — an empty store — instead of the "
                      "parent's. The failing tests exercise the handed-in set for "
                      "the primary key, and that key is dropped whenever it is last "
                      "in the handed-in set — which, for a single-entry set, is "
                      "always. A counterpart of this shape would NOT resolve.",
        "rationale": "REJECT from (P1), which is pinned over the WHOLE handed-in "
                     "set including its last entry (and from (P2) LENGTH, which the "
                     "dropped entry also breaks). The rival agrees with the "
                     "post-image ONLY where the handed-in set is empty, so a "
                     "domain-incomplete spec would admit it => SPEC-TOO-WEAK. "
                     "Refuted at preferred=[(\"a\", 1), (\"c\", 3)], "
                     "registry=[(\"b\", 2)]: the rival returns "
                     "[(\"a\", 1), (\"b\", 2)] where the post-image names "
                     "[(\"a\", 1), (\"c\", 3), (\"b\", 2)]. Its own distinguishing "
                     "point — a length-2 `preferred`, which no other case probes. "
                     "The gate refutes this witness against a VERIFYING alternative "
                     "impl of the same spec (the frozen loop cannot decide; see the "
                     "asymmetry note above), where `decide` positively establishes "
                     "the contract HOLDS at this input. Audit-measured: the same "
                     "witness shape at the length-1 point preferred=[(\"a\", 1)], "
                     "registry=[(\"b\", 2)] ALSO elaborates against this rival "
                     "(exit 0), which is what corrects the ≤1 claim. (Ports sibling "
                     "rival-partial-install-serve.)",
        "witness": _ip_witness('[("a", 1), ("c", 3)]', '[("b", 2)]',
                               '[("a", 1), ("b", 2)]'),
    },
    {
        "id": "weak-skip-already-bound",
        "kind": "uniqueness",
        "expect": "reject",
        # THE SHARPEST near-miss on the precedence clause: install a handed-in
        # binding only when its key is NOT already bound in the registry. Agrees
        # with gold on EVERY input where the two sides share no key — i.e. on
        # every input the other install rivals are refuted at — and is wrong
        # exactly on the OVERLAP, the one sub-domain the behavior exists for.
        # Given its own witness accordingly (a shared key), per the near-miss
        # rule: its rationale claims a narrower sub-domain than the others', so
        # it must be demonstrated there.
        "module": _ip_rival(
            "preferred.filter (fun p => !registry.any (fun q => q.1 == p.1)) "
            "++ registry"),
        "refinement": "a counterpart that installed a handed-in binding only for "
                      "keys the worker does not already resolve is a "
                      "\"don't clobber what's there\" install — and it is wrong on "
                      "exactly the case the behavior exists for: the worker DOES "
                      "already resolve the primary key (it resolves it lazily to a "
                      "fresh empty store), so the parent's binding is skipped and "
                      "the worker keeps the empty one. The data-visibility tests "
                      "still observe an empty store and FAIL, while the impl looks "
                      "correct on every input where the two sides are disjoint: it "
                      "would NOT resolve.",
        "rationale": "REJECT from (P1) `out = preferred ++ registry`, which is "
                     "unconditional — precedence is NOT contingent on the key being "
                     "unbound. This is a strict near-miss: it agrees with gold "
                     "wherever `preferred` and `registry` share no key, so it "
                     "survives every witness the other install rivals use and needs "
                     "its own. Refuted at preferred=[(\"a\", 1)], "
                     "registry=[(\"a\", 9)] — a SHARED key, the only overlapping "
                     "input point in this battery: the rival returns [(\"a\", 9)] "
                     "(the stale binding wins) where the post-image names "
                     "[(\"a\", 1), (\"a\", 9)]. A spec pinning precedence only for "
                     "fresh keys would MISS this => SPEC-TOO-WEAK. Cross-checked "
                     "against a CORRECT loop-free impl: the witness FAILS there. "
                     "(Added by audit; the closest sibling is "
                     "rival-clobber-noverride-serve, which attacks the OPPOSITE "
                     "over-reach — see the accounting below.)",
        "witness": _ip_witness('[("a", 1)]', '[("a", 9)]', '[("a", 9)]'),
    },
    {
        "id": "weak-clobber-unpreferred",
        "kind": "uniqueness",
        "expect": "reject",
        # THE OVER-REACH, the opposite direction from weak-skip-already-bound:
        # install the handed-in bindings AND additionally overwrite the VALUE of
        # every prior registry entry with the first handed-in value, keeping each
        # prior KEY, its POSITION, and the total LENGTH. So (P2) LENGTH holds at
        # every input and (P3) MEMBERSHIP holds too (the whole `preferred` prefix
        # is present verbatim); only (P1) refutes it. Added by the audit: the port
        # recorded this class as "not wrong on this carrier" on the grounds that
        # the over-reach needs "a value the input does not contain" — but the
        # first handed-in value IS in the input, so no value is invented and the
        # rival is a same-spec impl edit. Machine-checked: it does not verify, and
        # its witness elaborates against it while `decide` positively establishes
        # the contract HOLDS at that input for a verifying alternative impl.
        "module": _ip_rival(
            "preferred ++ registry.map "
            "(fun q => (q.1, (preferred.map (fun p => p.2)).headD q.2))"),
        "refinement": "a counterpart that installed the handed-in bindings and then "
                      "rebound every OTHER key in the worker's registry to the "
                      "handed-in resource would destroy the bindings the parent "
                      "deliberately did not hand over: a key the worker legitimately "
                      "resolves on its own now resolves to somebody else's resource, "
                      "so request handling that touches it reads and writes the wrong "
                      "store. That corrupts currently-passing behavior as well as the "
                      "target tests, so it would NOT resolve. The clause it breaks is "
                      "the one that says an alias absent from the handed-in set KEEPS "
                      "its prior binding.",
        "rationale": "REJECT from (P1) `out = preferred ++ registry`, whose right "
                     "conjunct pins the prior registry POINTWISE and not merely its "
                     "keys, positions or length. This is the only rival that keeps "
                     "every prior KEY and POSITION and the exact LENGTH while "
                     "corrupting prior VALUES, so it satisfies (P2) at every input "
                     "and (P3) at every input (the `preferred` prefix is present "
                     "verbatim) and is refutable by (P1) alone. A spec pinning only "
                     "length, membership and the key-set would MISS it => "
                     "SPEC-TOO-WEAK. Refuted at preferred=[(\"d\", 4)], "
                     "registry=[(\"b\", 2), (\"e\", 5)]: the rival returns "
                     "[(\"d\", 4), (\"b\", 4), (\"e\", 4)] — both prior VALUES "
                     "clobbered to the handed-in one, keys and length intact — where "
                     "the post-image names "
                     "[(\"d\", 4), (\"b\", 2), (\"e\", 5)]. A FRESH input point no "
                     "other case uses, and the only one at which `registry` has "
                     "length 2. (Added by audit; ports the behavioral content of "
                     "sibling rival-clobber-noverride-serve, which the port had "
                     "recorded as inexpressible here — see the accounting below.)",
        "witness": _ip_witness('[("d", 4)]', '[("b", 2), ("e", 5)]',
                               '[("d", 4), ("b", 4), ("e", 4)]'),
    },
    {
        "id": "weak-no-release",
        "kind": "uniqueness",
        "expect": "reject",
        # The release-side pre-image shape: return the handles untouched, so a
        # handle that was active stays active.
        "module": _ra_rival("handles"),
        "refinement": "this is the release-side pre-image: the worker is recycled "
                      "without releasing the resources it held, so a resource left "
                      "active at teardown is still active when teardown inspects it "
                      "— the publicly reported symptom the change fixes. The test "
                      "that observes this directly is skipped on the evaluated "
                      "backend, but it is still a wrong implementation the spec must "
                      "reject, and a counterpart of this shape reinstates the leak.",
        "rationale": "REJECT from (R1) `out = releasedSeq handles` and (R3) "
                     "`∀ b ∈ out, b = false`: returning the input leaves every "
                     "active entry active, so both clauses fail whenever any input "
                     "handle is active. Refuted at handles=[true]: the rival "
                     "returns [true] where the post-image names [false]. This is "
                     "the ACTIVE-handle point for the `handles` binder. "
                     "Cross-checked against a CORRECT loop-free impl: the witness "
                     "FAILS there, with `decide` positively proving the contract "
                     "holds at [true]. (Ports sibling rival-no-close-teardown.)",
        "witness": _ra_witness('[true]', '[true]'),
    },
    {
        "id": "weak-discard-handles",
        "kind": "uniqueness",
        "expect": "reject",
        # Satisfy the UNIVERSAL clause vacuously by returning nothing: every
        # entry of the empty list is inactive, so (R3) holds trivially while
        # (R1) and (R2) fail. This is the rival that isolates (R3) from (R2) —
        # without a length clause the spec would admit it.
        "module": _ra_rival("([] : List Bool)"),
        "refinement": "a counterpart that discarded the registry instead of "
                      "releasing its entries would leave the held resources "
                      "untouched while reporting an empty set of holdings — the leak "
                      "persists AND the worker's own bookkeeping loses track of what "
                      "it holds, so subsequent handling cannot release them either. "
                      "It would NOT resolve, and it is strictly worse than the "
                      "no-release shape.",
        "rationale": "REJECT from (R1) `out = releasedSeq handles` and (R2) "
                     "`out.length = handles.length` — but NOT from (R3): every entry "
                     "of [] is inactive, so the rival satisfies the UNIVERSAL clause "
                     "vacuously at every input. That is the point: a spec carrying "
                     "only (R3) would admit an impl that reports nothing held, so "
                     "this case is what makes (R2)'s independence load-bearing => "
                     "otherwise SPEC-TOO-WEAK. Refuted at handles=[false]: the "
                     "rival returns [] where the post-image names [false]. Deliber"
                     "ately probes an ALREADY-INACTIVE handle — the sub-domain where "
                     "weak-no-release is indistinguishable from gold, so the two "
                     "rivals genuinely need different points. Cross-checked against "
                     "a CORRECT loop-free impl: the witness FAILS there. (Added by "
                     "audit; no sibling — nagini's carrier is a fixed-length "
                     "in-place registry, so it cannot express a length change.)",
        "witness": _ra_witness('[false]', _EMPTY_REG.replace(
            "List (String × Int)", "List Bool")),
    },
    {
        "id": "weak-partial-release",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN, release side: release every handle EXCEPT the last,
        # which it passes through unchanged. Preserves the LENGTH exactly, so it
        # satisfies (R2) at every input and is refutable only by (R1)/(R3).
        # Correct exactly on the registries whose LAST handle is already inactive
        # (including the empty one); wrong on every registry whose last handle is
        # active, INCLUDING the single-entry [true]. (Audit-corrected: the port's
        # prose claimed agreement on every registry of length ≤1, which is false —
        # `handles.drop (handles.length - 1)` passes the sole entry of a
        # single-entry registry through unreleased. Machine-checked below.)
        "module": _ra_rival(
            "releasedSeq handles.dropLast ++ handles.drop (handles.length - 1)"),
        "refinement": "a release pass that stops one short leaves the last held "
                      "resource active after the worker is recycled — the same leak "
                      "the change fixes, on a sub-domain. A counterpart of this "
                      "shape reinstates the reported failure whenever the worker "
                      "holds more than one resource and the last one is live, so it "
                      "would NOT resolve.",
        "rationale": "REJECT from (R3) `∀ b ∈ out, b = false` and (R1), over the "
                     "WHOLE registry including its last entry. It preserves LENGTH "
                     "exactly, so (R2) holds at every input and the universal "
                     "clause is what refutes it — the complement of "
                     "weak-discard-handles, which breaks (R2) and satisfies (R3). "
                     "The rival agrees with the post-image ONLY on registries whose "
                     "LAST handle is already inactive (the empty one included), so a "
                     "domain-incomplete spec would admit it => SPEC-TOO-WEAK. "
                     "Refuted at handles=[false, true]: the rival returns "
                     "[false, true] (the trailing ACTIVE handle survives) where the "
                     "post-image names [false, false]. A length-2 MIXED-state "
                     "registry — its own point, which no other case probes. The gate "
                     "refutes this witness against a VERIFYING alternative impl of "
                     "the same spec (the frozen loop cannot decide), where `decide` "
                     "positively establishes the contract HOLDS at this input. "
                     "Audit-measured: the same witness shape at the single-entry "
                     "ACTIVE point handles=[true] ALSO elaborates against this rival "
                     "(exit 0), which is what corrects the length-≤1 claim — so this "
                     "rival is NOT indistinguishable from gold there and does not in "
                     "fact need a length-2 point to be refuted at all. "
                     "(Ports sibling rival-partial-close-teardown.)",
        "witness": _ra_witness('[false, true]', '[false, true]'),
    },
    {
        "id": "weak-truncate-release",
        "kind": "uniqueness",
        "expect": "reject",
        # The other side of the partial-release error: release every handle
        # except the last and DROP it from the result. Every returned entry IS
        # inactive, so (R3) holds; only (R1) and (R2) refute it. Together with
        # weak-partial-release this shows neither (R2) nor (R3) subsumes the
        # other.
        "module": _ra_rival("releasedSeq handles.dropLast"),
        "refinement": "a counterpart that released all but the last held resource "
                      "and dropped it from its bookkeeping leaves that resource "
                      "active AND unaccounted for, so nothing later releases it "
                      "either — the leak persists on every registry holding more "
                      "than one resource. It would NOT resolve.",
        "rationale": "REJECT from (R2) `out.length = handles.length` and (R1): the "
                     "result is one entry short. It satisfies (R3) at EVERY input "
                     "(every entry it does return is inactive), so it is refutable "
                     "only by the length and value clauses — the mirror of "
                     "weak-partial-release, which satisfies (R2) and violates (R3). "
                     "The pair together demonstrate that (R2) and (R3) are "
                     "independent and neither alone is sufficient => a spec dropping "
                     "either is SPEC-TOO-WEAK. Refuted at handles=[true, true]: the "
                     "rival returns [false] where the post-image names "
                     "[false, false]. A length-2 ALL-ACTIVE registry, distinct from "
                     "weak-partial-release's mixed-state point. Cross-checked "
                     "against a CORRECT loop-free impl: the witness FAILS there. "
                     "(Added by audit; no sibling, same fixed-length-carrier reason "
                     "as weak-discard-handles.)",
        "witness": _ra_witness('[true, true]', '[false]'),
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING
# ===========================================================================
# The sibling battery has 8 SPEC cases (2 soundness positives, 2 admissibility,
# 4+2 uniqueness rivals = 4 value/domain + 2 frame) plus a 5-case AXIOM lane. It
# contracts TWO functions over MUTABLE list carriers with fractional read-only
# permissions and one abstract capability predicate. This bundle contracts two
# methods over IMMUTABLE value carriers with EMPTY preconditions and no axiom, so
# the permission and capability machinery has no counterpart while the value and
# domain-completeness content ports directly — and the immutable carrier exposes
# LENGTH and ORDER clauses nagini's fixed-length in-place carrier could not, which
# is where the added cases come from.
#
#   sibling case                        -> here                          disposition
#   -------------------------------------------------------------------------------
#   pos-serve-reshape                   -> pos-install-inline-binding    PORTED
#                                          + pos-install-closed-form     PORTED (split)
#   pos-teardown-reorder                -> pos-release-map               PORTED (reshaped)
#   admiss-serve                        -> admiss-install-overlap-...    PORTED (by audit)
#   admiss-teardown                     -> admiss-release-nondegenerate  PORTED (by audit)
#   frame-mutate-override-serve         -> (none)                        VACUOUS
#   frame-mutate-tokens-teardown        -> (none)                        VACUOUS
#   rival-omit-handoff                  -> weak-ignore-preferred         PORTED (behavior only)
#   rival-handoff-wrong-server          -> (none)                        NO COUNTERPART
#   rival-partial-install-serve         -> weak-partial-install          PORTED
#   rival-clobber-noverride-serve       -> weak-clobber-unpreferred      PORTED (by audit)
#   rival-no-close-teardown             -> weak-no-release               PORTED
#   rival-partial-close-teardown        -> weak-partial-release          PORTED
#   (no sibling)                        -> weak-discard-registry         ADDED
#   (no sibling)                        -> weak-wrong-precedence         ADDED
#   (no sibling)                        -> weak-skip-already-bound       ADDED
#   (no sibling)                        -> weak-discard-handles          ADDED
#   (no sibling)                        -> weak-truncate-release         ADDED
#   AXIOM_TESTS (5)                     -> (none)                        DROPPED (G-AX)
#
# 8 ported (one split into two positives; two admissibility landed by audit),
# 5 added, 2 vacuous, 1 with no counterpart, 5 dropped = 15 SPEC cases
# (3 soundness, 10 uniqueness, 2 admissibility).
#
# VACUOUS (2). The two FRAME rivals are the sibling's self-declared #1 weakness
#   class: a store through a reference held at half permission must fail for
#   insufficient permission. Lean and Velvet are referentially transparent —
#   every input here is an immutable value, no binder is `mut` (the only `mut`
#   in the file is on loop-local accumulators INSIDE the impl region), there is
#   no heap and no aliasing — so there is no read-only input to overwrite. Per
#   the porting map this class is genuinely vacuous on Lean-family carriers and
#   no substitute was fabricated.
#
# ADMISSIBILITY, LANDED BY AUDIT (2). The port recorded both sibling
#   admissibility cases as VACUOUS because "neither method carries a `require`,
#   so the precondition is True and cannot be too strong". The premise is true
#   and the conclusion does not follow: it retires the LITERAL probe, not the
#   lane. On a total carrier the PRECOND-TOO-STRONG analogue is the obligation
#   being unsatisfiable or DEGENERATE at exactly the F2P-shaped input — a
#   post-image no impl can meet is indistinguishable, to every other case in
#   this battery, from one every impl meets, because the uniqueness rivals only
#   ever show that WRONG impls fail. Dropping the lane therefore removed one of
#   the three directions this gate exists to test. Landed as
#   admiss-install-overlap-nondegenerate (the overlapping-key install point,
#   asserting first-match resolves to the handed-in value, both bindings
#   survive, and the merge is orientation-sensitive there) and
#   admiss-release-nondegenerate (the ACTIVE-handle point, asserting the
#   post-image actually flips it plus (R2)/(R3) jointly). Both keep the impl
#   after the assert and BOTH frozen proof bodies byte-identical, and both
#   verify with no proof retune (exit 0); negating one conjunct in each leaves
#   `unsolved goals` (exit 1), which is what shows the asserts are live rather
#   than decorative.
#
# NO COUNTERPART (1). rival-handoff-wrong-server launders an abstract capability
#   from one server to another. That attack needs a body-less predicate whose sole
#   producer is a consumed axiom; this bundle's `axioms` region is EMPTY and the
#   acceptance of the handed-in set is R-leg framing (the method takes it as a
#   parameter) rather than a modeled obligation. There is no capability term to
#   name a wrong subject for, so the rival cannot be expressed — not because it
#   would be hard to refute, but because its target does not exist here.
#
# CORRECTED BY AUDIT (1). The port recorded rival-clobber-noverride-serve as NOT
#   WRONG ON THIS CARRIER, reasoning that the over-reach "is not expressible as a
#   same-spec impl edit without inventing a value the input does not contain".
#   That reason does not hold: the over-reach needs no invented value, because the
#   FIRST HANDED-IN VALUE is already in the input and can be written over every
#   prior registry entry. `weak-clobber-unpreferred` above does exactly that, and
#   it is measured — the rival does not verify, and its witness elaborates against
#   it (exit 0) while against a verifying alternative impl of the same spec
#   `decide` positively establishes that the contract HOLDS at the same input
#   (exit 1, `decide` proved the proposition ... = false is false). So the class
#   was expressible all along and the sibling's sharpest value-clause rival is now
#   ported rather than absorbed. It also adds real reach: it is the ONLY case that
#   keeps every prior KEY, POSITION and the exact LENGTH while corrupting prior
#   VALUES, so it is the only rival refutable by (P1) alone against a result whose
#   key-set is correct — and the only one whose `registry` has length 2.
#
# ADDED (5), and why case count grew rather than shrank. This bundle's carrier is
#   an immutable list, so the postcondition carries LENGTH and ORDER clauses that
#   nagini's fixed-length in-place carrier could not state — and each is
#   independently attackable. weak-discard-registry and weak-wrong-precedence
#   attack (P1) from directions the sibling's in-place writes cannot express;
#   weak-skip-already-bound is the sharpest near-miss on precedence and the only
#   case probing a SHARED key; weak-discard-handles and weak-truncate-release
#   isolate (R2) from (R3) in both directions, which the pair
#   weak-partial-release / weak-truncate-release demonstrates is necessary.
#
# DROPPED positives: none. No soundness positive was abandoned for a proof that
#   would not close; all three build (exit 0), two with the frozen tactic body
#   and one with a two-case induction over a frozen lemma.
#
# ADDITIONAL SOUNDNESS PROBES the audit ran and did NOT ship (they duplicate the
#   three positives' coverage, so shipping them would only cost builds). Each is a
#   faithful CORRECT reshape checked against the frozen spec, and each VERIFIES —
#   so no SPEC-TOO-STRONG hole was found in either direction:
#     install as `preferred.foldr (fun kv acc => kv :: acc) registry`   exit 0
#     install as `preferred.reverse.reverseAux registry`                exit 0
#     release as `List.replicate handles.length false`                  exit 0
#     release as the post-image `releasedSeq handles` verbatim          exit 0
#   One reshape needed its tactic body retuned before it closed (the foldr one
#   fails with `No goals to be solved` under a two-case induction and closes under
#   `loom_solve <;> simp_all [List.foldr_cons_eq_append]`). That is a proof-shape
#   fact about the tactic script, not a spec fact: the reshape IS provable, which
#   is what the soundness direction asks.
#
# SECOND-AUDIT PROBES (also not shipped; recorded so the coverage is on record).
#   Attack D, three NEW wrong impls aimed at what the shipped rivals leave alone
#   — all three REJECTED, so no spec hole:
#     install `preferred ++ registry.dropLast`  (drops the REGISTRY's last
#       entry, the mirror of weak-partial-install, which no shipped rival does)
#                                                                    exit 1
#     release `releasedSeq handles ++ [false]`  (result one entry too LONG —
#       every shipped release rival is short or length-preserving)    exit 1
#     install `preferred.map (fun p => (p.1, 0)) ++ registry`  (corrupts the
#       HANDED-IN values, where weak-clobber-unpreferred corrupts prior ones)
#                                                                    exit 1
#   Attack E, two more correct reshapes, both PROVABLE so no SPEC-TOO-STRONG:
#     release `handles.foldr (fun _ acc => false :: acc) []`          exit 0
#       (under `all_goals (induction handles ...)`; the two-case induction alone
#        fails on the nil ∀ goal — a tactic fact, not a spec fact)
#     install `preferred.flatMap (fun kv => [kv]) ++ registry`        exit 0
#       (under `loom_solve <;> simp_all [List.flatMap_singleton]`; with
#        `List.flatMap_def` it leaves a `.sum` goal — again tactic, not spec)
#
# BINDER COVERAGE (the check the gate does not run). installPreferred's two
#   binders are varied independently and jointly: `preferred` moves off empty
#   with `registry` empty (weak-ignore-preferred), `registry` moves with
#   `preferred` empty (weak-discard-registry), both non-empty and DISJOINT
#   (weak-wrong-precedence, weak-partial-install at `preferred` length 2,
#   weak-clobber-unpreferred at `registry` length 2), and both non-empty and
#   OVERLAPPING (weak-skip-already-bound). So each binder is moved to length 0, 1
#   and 2 and the shared-key interaction is reached. releaseAll's single binder is
#   probed at an active singleton, an inactive singleton, a mixed-state pair and
#   an all-active pair — so no witness holds it at a fixed value. Ten reject cases
#   at ten DISTINCT input points.
#
#   Two caveats the audit measured rather than argued, kept here because the
#   coverage reporter cannot see them. (i) The already-inactive point does NOT
#   separate weak-no-release from weak-partial-release: the latter is refutable at
#   the ACTIVE singleton [true] too (measured, exit 0), so its length-2 point buys
#   distinct COVERAGE, not distinct necessity. (ii) weak-partial-install and
#   weak-partial-release each agree with the post-image on a strictly SMALLER
#   sub-domain than the port's prose claimed (empty handed-in set / last-handle-
#   already-inactive respectively, NOT everything of length ≤1); the rationales
#   above now state the measured sub-domain.
