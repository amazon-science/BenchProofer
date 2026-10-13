"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-26291 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_<name>`` STATEMENT
stays byte-identical). ``expect="verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect="reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` HOLDS of the rival
while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery (see
``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models TWO functions with fractional-permission contracts (``measure`` with
``Requires(context > 0)``, and ``call`` with a four-clause postcondition over an
integer measurement count, a measured-with handle, and a supplied-vs-resolved
context). This Lean bundle models only the purely-functional CORE the gold patch
adds — the resolution of WHICH measurement context flows into the routine's
downstream steps: a total function over an optional supplied context and an
always-present surface context, returning the pair of (necessarily present)
contexts the two consecutive downstream steps are handed. Most nagini cases
attach to a behavior this bundle does not model (the integer count, the
measure-precondition, the twice-measurement) and so have NO counterpart here;
the mapping of each nagini case to its Lean counterpart (or its principled
omission) is in the module ``assessment`` in the submitted payload.

AUDIT REPAIR (spec-too-weak, G-EQ / G-PANEL-1). An earlier revision of this
bundle modeled the resolution as a SINGLE resolved context
(``result : Option RenderContext``, pinned to ``some (suppliedContext.getD
surfaceContext)``), bound by mapping.md to "the context in hand when the extent
step is reached". The modeled routine has TWO consecutive downstream steps that
each consume the context, and the gold change rebinds the routine's own
parameter, so BOTH of them see the resolved context. Under the single-context
model a rival that resolved a context for the EARLIER step only and let the LATER
step proceed with "nothing" was indistinguishable from gold: it verified, yet its
faithful real counterpart does not repair the reported scenario at all — it moves
the same crash one frame downstream, into the placement step's own arithmetic, so
the FAIL_TO_PASS still fails. That is a verify-does-not-imply-resolve break of the
worst kind, and it was measured (a retained attack that verified against the old
spec). The repair generalizes the modeled observable from ONE resolved context to
the PAIR of contexts the two steps are handed, pinned COMPONENTWISE, and adds the
reject rival ``reject-unresolved-at-later-step`` — the exact shape that used to
slip through — so the hole is now defended by a shipped case rather than by
argument. ``conformance_check.py`` was widened in the same repair: it now
intercepts BOTH consumers and lets the routine run to completion, instead of
raising out of the first interception (which is why the differential could not
see the second consumer either).

DEFENDED SURFACE (one modeled behavior). The routine settles on exactly one
present measurement context and hands THAT one to each of its two consecutive
downstream steps. The postcondition pins both components of ``result`` to a
single grounded computation over the two inputs:

    result.1 = some (suppliedContext.getD surfaceContext) ∧
    result.2 = some (suppliedContext.getD surfaceContext)

which has two independent, input-selected clauses, each asserted of BOTH steps:

  * SUPPLIED PASSTHROUGH — when the caller supplied a context (``some r``), each
    step receives that very context (``some r``), unchanged;
  * SURFACE FALLBACK (the CHANGED clause) — when the caller supplied nothing
    (``none``), each step receives the context obtained from the host's drawing
    surface (``some surfaceContext``), never left unresolved (``none``).

and one SHARING clause that is a consequence of pinning both components to the
same grounded term: the two steps receive the SAME context, so resolving for one
step and not the other is excluded.

The BEHAVIOURAL DISCRIMINATOR (the fix): on the no-context path, resolve the
surface's context and carry THAT into every downstream step, instead of
propagating "nothing". The pre-fix behavior left the context unresolved on that
path for both steps — that is the surface-fallback rival below; resolving it for
only one step is the later-step rival.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: an
    input carries no heap permission, there is no read-only half-permission to
    overwrite and no aliasing to exploit. The nagini frame reasoning
    (``self`` full-write, value-typed inputs) has no expressible instance here;
    no substitute is fabricated.

  * DIVERGENCE / NON-TERMINATION — APPLIES, and now SHIPPED as
    ``reject-diverging-resolution``. The frozen bundle sets no
    ``loom.semantics.termination`` option — it is plain Lean, where a total
    ``def`` must terminate — but the impl region may be prefixed ``partial``,
    which admits a genuinely non-terminating body:

        partial def implementation_resolveRenderContext ... := Id.run do
          let rec loop (n : Nat) : Option RenderContext × Option RenderContext :=
            loop (n+1)
          return loop 0

    That rival is IN SCOPE (``variant_problems`` clean: same_spec holds, the
    theorem statement is byte-identical, no new axiom/sorry) and the verifier
    REJECTS it.

    AUDIT REPAIR (this class was previously recorded here as a KNOWN HOLE, on
    the reasoning that the rival is UNWITNESSABLE because ``partial`` compiles
    the body to an opaque fixpoint whose ``loop 0`` term does not reduce for ANY
    claim, so a one-point refutation and its flipped forgery both fail
    identically on the RIVAL side and the case would land as
    ``witness-unproven``. The one-point measurement was right; the CONCLUSION
    drawn from it was wrong, and the audit measured the difference.

    The refutation does not need ``loop 0`` to reduce, because it does not have
    to say what the diverging impl RETURNS — only that a single input-independent
    term cannot be the resolved context for TWO DISTINCT surface contexts at
    once. So the witness is stated at a PAIR of points ``a ≠ b``: the spec pins
    ``result.1`` to ``some a`` on ``(none, a)`` and to ``some b`` on
    ``(none, b)``, and since the rival's first component is the SAME unreduced
    term at both, the two conjuncts transitively give ``some a = some b``,
    contradicting the hypothesis. Nothing about the loop is unfolded; the two
    hypotheses are chained against each other, which is exactly the technique
    that makes an irreducible carrier attackable.

    Measured, and both directions carry information (the two-line forgery
    experiment, attack B′): the refutation ELABORATES against the diverging
    rival (exit 0) and FAILS on the frozen solution (exit 1) with ``Invalid
    field `symm`: The environment does not contain `True.symm` … h1 has type
    True`` — i.e. ``simp`` PROVED the frozen impl's first-component equation at
    both points, so there is nothing left to chain and the refutation genuinely
    does not hold of gold. The FLIPPED claim (asserting the pair IS correct at
    both points) inverts cleanly: exit 0 on the frozen solution, exit 1 on the
    diverging rival. Gold's exit code therefore tracks the claim rather than the
    carrier. The gold-side error is a plain evaluation residue, not one of the
    stuck-reduction screens: no ``did not reduce to isTrue/isFalse``, no
    ``Dependent elimination failed``, no ``forIn Lean.Loop.mk``, no missing
    ``Decidable`` instance. The same witness was additionally refuted against
    FOUR other independently VERIFYING impls of this spec (both shipped
    positives and two further correct reshapes), each failing with the same
    ``True.symm`` residue, so its failure is a property of satisfying the spec
    and not of gold's particular syntactic shape.

    (The nagini sibling carries no ``diverge-*`` case, so this is not a
    recovered omission but a class the port under-attacked on this carrier.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: both
    components of ``result`` are pinned equal to ``some (suppliedContext.getD
    surfaceContext)``, a term built only from the two inputs. There is no opaque
    answer key an implementation could echo. ``RenderContext`` is ``opaque`` only
    as the element type of the optional carrier and the surface value (so the
    context can appear in the executable impl); it is NOT an oracle for the
    resolution decision — the impl still has to select the right branch, twice.

  * VALUE / CONTROL-FLOW — APPLIES. Four value-level reject rivals attack the
    resolution (a fifth, divergence, is above):
    the pre-fix "leave it unresolved on the no-context path" (surface-fallback
    clause, PRESENCE, both steps), "resolve for the earlier step but hand the
    later step nothing" (the SHARING clause — the ported spec-too-weak attack),
    "settle on a present context that is not the host surface's"
    (surface-fallback clause, SOURCE), and "always take the surface even when a
    context was supplied" (supplied-passthrough clause).

CONDITIONING ON THE OPAQUE CARRIER. ``RenderContext`` is opaque, so no concrete
literal exists to feed ``decide``. The witnesses therefore QUANTIFY over the
carrier instead of computing it, which is enough: nothing has to PROVE an opaque
guard, the refutation is stated at a point described by hypothesis, and the
gate's consistency probe confirms the hypotheses are satisfiable (no tactic
derives ``False`` from a disequation between opaque terms).

  * The surface-fallback rival hands ``none`` to both steps on the ``none``
    input, which is ``≠ some surfaceContext`` by ``Option`` disjointness —
    refutable with NO hypothesis at all.
  * The later-step rival hands the resolved context to the extent step and
    ``none`` to the placement step on the ``none`` input, so its FIRST component
    matches the spec and only the SECOND is disjoint — again refutable with no
    hypothesis, and only because the postcondition constrains ``result.2``.

UNCONDITIONED-WITNESS TACTIC (audit repair #2 — the ``Id.run`` monadic residue).
The two unconditioned witnesses (surface-fallback and later-step) close with
``simp [Id.run, pure, Id.instMonad]``, NOT with ``simp [Id.run]``. That is not a
cosmetic strengthening; ``simp [Id.run]`` made both cases HOLLOW, and the audit
measured it in both directions.

``unfold`` on an ``Id.run do`` body leaves a ``pure (…)`` application in the
goal. ``Id.run`` alone rewrites the ``.run`` wrapper but not that ``pure``, so on
the frozen solution the goal stays ``(pure (some sC, some sC)).1 = some sC`` — an
equation ``simp`` never DISCHARGES. Gold's build therefore failed for a reason
that had nothing to do with the claim:

  * flipped claim (drop the ``¬``, i.e. assert gold is CORRECT at ``none`` — the
    exact opposite of a refutation): ALSO exit 1 on gold, with the mirror-image
    ``unsolved goals ⊢ (pure (some sC, some sC)).1 = some sC ∧ …``. Both
    directions fail, so gold's exit code carried no information about the claim;
  * a claim TRUE OF GOLD AND of both rivals (the spec at a ``some r`` input,
    where all three agree): exit 1 on gold and exit 1 on both rivals — the
    tactic cannot even state gold's own correctness;
  * type-reveal on the hypothesis: under ``simp [Id.run]`` the conjunct has type
    ``(pure (some sC, some sC)).1 = some sC`` (a concrete, UNPROVED equation);
    under ``simp [Id.run, pure, Id.instMonad]`` it has type ``True`` — ``simp``
    PROVED the equation for gold. That pair is the genuine refutation.

Adding ``pure`` and ``Id.instMonad`` reduces the monadic residue, and the exit
codes then track the claim exactly: the refutation is exit 0 on each rival and
exit 1 on gold, while the flipped claim inverts to exit 0 on gold and exit 1 on
each rival. The repaired witnesses were additionally refuted against FOUR
independently VERIFYING impls of this spec, so their gold-side failure is a
property of satisfying the spec rather than of gold's syntactic shape.
  * The substitute-source rival hands ``some e`` to both steps on the ``none``
    input for an element ``e`` that inhabits the carrier but is not identified
    with ``surfaceContext``; the witness assumes ``e ≠ surfaceContext``.
  * The supplied-passthrough rival hands ``some surfaceContext`` to both steps on
    a ``some r`` input; that equals the spec's ``some r`` only if
    ``surfaceContext = r``. The witness assumes the single separating hypothesis
    ``surfaceContext ≠ r`` — the exact sub-domain where the rival is wrong.

WITNESS TACTIC (audit repair). The two conditioned witnesses discharge their
``Option`` equality with ``injection`` applied to the relevant CONJUNCT
(``hh.1``), NOT by applying ``Option.some.inj`` to the raw hypothesis. The
distinction is the whole discrimination check: ``Option.some.inj`` does not APPLY
to the frozen impl, because an ``Id.run do`` block with a ``let mut``/``if`` is
not syntactically ``some _``, so the frozen build fails with ``Application type
mismatch`` — a syntactic non-application that appears for a FALSE claim about the
rival too (measured), hence attests nothing. ``injection`` reduces the impl first,
so the frozen build instead fails on the residual goal (``surfaceContext = r`` /
``e = surfaceContext``), which is the actual unprovable content of the claim on
gold.

Each witness was checked, with real builds, to ELABORATE against its rival and
to FAIL SEMANTICALLY against the frozen solution, so each discriminates rather
than asserting a tautology or tripping over a syntactic mismatch.

BINDER / POINT SPREAD. The frozen theorem carries NO precondition hypothesis
(the modeled behavior is total, so ``∀`` is unguarded). The reject witnesses move
BOTH input binders across the branch split of ``getD``: ``suppliedContext`` takes
``none`` (surface-fallback, later-step, substitute-source and divergence
witnesses) and ``some r`` (supplied-passthrough witness); ``surfaceContext`` is
the value used on the ``none`` witnesses and the DISTINCT-from-``r`` value that
makes the ``some`` witness bite. The four ``none``-input rivals differ in WHAT the
``none`` branch produces — nothing at all, nothing at the later step only, a
present non-surface element, and nothing ever (divergence) — so that branch is
probed at four genuinely different points and not four spellings of one. They also
spread across the RESULT binders: three are refuted through ``result.1`` and one
only through ``result.2``, so neither component is left unexercised, and the
``result.2``-only case was independently CONFIRMED load-bearing by measurement (a
witness refuting only ``result.1`` at that input ELABORATES against the
surface-fallback rival and FAILS against the later-step rival, whose first
component matches the spec). The divergence witness additionally moves
``surfaceContext`` to TWO values inside a single claim, which no other case does,
and refutes through the pinned term's input-DEPENDENCE rather than its value at
one point. No binder is held at one convenient value by every rival, and the five
witnesses fail for five different reasons — dropped fallback, fallback dropped for
the later step, wrong source, ignored supplied, and never resolved at all.

AXIOM lane: EMPTY here. The bundle consumes no ``axiom`` (mapping.md: the
surface's renderer is modeled as the plain input ``surfaceContext``, not an
axiomatized callee; ``axiom_check.py`` is a skip stub and G-AX skips). The
nagini ``AXIOM_TESTS`` belong to G-AX and are dropped.

NAGINI CASES NOT PORTED, with the per-case reason (audit-reviewed):

  * ``reject-measure-twice`` and ``reject-skip-measurement-no-renderer``'s COUNT
    half — INEXPRESSIBLE. Both are refuted by ``Ensures(self.measurements == 1)``,
    an observable of a MUTABLE field counting invocations. This carrier models a
    pure resolution returning values; it has no state, so "how many times the
    measurement ran" has no denotation in ``problem_spec`` and cannot be modeled
    without changing the frozen spec's signature. The behavioral half of
    ``reject-skip-measurement-no-renderer`` (nothing present is resolved on the
    no-context path) IS ported, as ``reject-unresolved-on-no-context``.

    DEMONSTRATED, not asserted (audit). The carrier's collapse of this
    distinction was measured rather than argued: an impl that performs the
    resolution TWICE (repeat the ``if ctx.isNone then ctx := some
    surfaceContext`` guard) and one that re-resolves by recomputing
    ``some (ctx.getD surfaceContext)`` after the guard both VERIFY against the
    frozen obligation (two real builds, exit 0 each). That is the correct
    outcome, not a spec hole: on a pure value carrier a repeated idempotent
    resolution is observationally identical to a single one, so both are
    faithful impls and the spec is right to accept them. It is also the direct
    evidence that the invocation-count observable has no denotation here — the
    nagini count rivals cannot be ported because their refuting clause is not
    expressible, exactly as claimed above.

    NOTE what this does NOT excuse. "How many times the resolution ran" has no
    denotation; "which context each downstream step was handed" does, and the
    audit repair above shows it is load-bearing. Per-step observables therefore
    belong in the model even though per-invocation counts do not.
  * ``reject-measure-wrong-handle`` — INEXPRESSIBLE. It attacks the impl of the
    SECOND nagini function (``measure``'s own postcondition, "record the handle
    you were handed"). This bundle models one function; there is no second impl
    region to mutate and no ``measured_with`` field to falsify.
  * ``reject-partial-domain-pass-axes`` — INEXPRESSIBLE. Its rejection comes from
    ``measure``'s ``Requires(context > 0)`` failing for an unconstrained integer
    handle. Here the surface context is typed ``RenderContext`` (not ``Option``),
    so "a handle that might not be a usable context" is ruled out by the TYPE and
    a rival cannot even state it. The frozen theorem has no precondition to
    under-discharge.
  * ``reject-substitute-present-context`` — EXPRESSIBLE, and now PORTED as
    ``reject-substitute-present-source``. Recorded here because the first port
    omitted it on the reasoning that the opaque carrier has no second inhabitant
    to substitute; that reasoning is wrong. A substitute does not have to be
    constructed, only denoted, and ``Classical.choice`` on the carrier's
    nonemptiness witness denotes one. This was the one omission that mattered:
    it is the only case separating presence from source, and its nagini ancestor
    is a recorded spec-too-weak failure under a presence-only postcondition.
  * ``pos-control-branch-reorder`` and ``admiss-no-renderer-path`` — PORTED, as
    ``pos-control-match-branch`` and ``admiss-no-context-path``.
  * ``AXIOM_TESTS`` (``ax-sound-axes_context``, ``ax-contain-axes_context``) —
    out of lane (G-AX), and vacuous here besides: no axiom is consumed.

AUDIT PROBES BEYOND THE SHIPPED CASES (recorded so the next auditor does not pay
for them twice; all measured with real builds).

SPEC-TOO-WEAK probe — six further WRONG impls the battery does not contain were
built, each with the frozen tactic AND with a deliberately stronger fresh proof
script, to see whether any could satisfy the frozen obligation: surface handed to
the extent step only; the caller's raw value handed to the placement step; both
arms sourcing the surface; a substitute element at the placement step only; the
sharing clause broken on the SUPPLIED branch (``(some r, none)``); and the guard
inverted to fire on ``isSome``. All twelve builds failed, and under the strong
script the residual goals were the SPEC's own unproved equations (e.g. ``⊢ (pure
(some surfaceContext, some val)).1 = some val``) rather than tactic breakage —
so each is rejected by the postcondition and not by proof-script mismatch. No
spec hole found in this direction.

SPEC-TOO-STRONG probe — three further CORRECT reshapes were built beyond the two
shipped positives: ``suppliedContext.orElse (fun _ => some surfaceContext)``,
``suppliedContext.elim (some surfaceContext) some``, and the mirror-image guard
(default to the surface, overwrite when a context WAS supplied). All three verify
under the frozen tactic body, exit 0 each. The spec admits every faithful shape
tried, so no soundness hole in this direction either.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-26291"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Every anchor lies ENTIRELY inside the impl region (or, for the admissibility
# case that re-proves, the proof region) so same_spec stays byte-identical.

# The whole gold impl body of `implementation_resolveRenderContext` (the
# default-then-overwrite-if-none shape, then hand the one settled binding to both
# downstream steps), inside -- impl-start / -- impl-end.
_I_BODY = (
    "  -- Start from whatever the caller supplied (possibly nothing).\n"
    "  let mut ctx := suppliedContext\n"
    "  -- If the caller supplied nothing, fall back to the context obtained from the\n"
    "  -- host's drawing surface, which is always available.\n"
    "  if ctx.isNone then\n"
    "    ctx := some surfaceContext\n"
    "  -- Both steps read the SAME settled binding, so each is handed a present,\n"
    "  -- concrete context: the extent step first, then the placement step.\n"
    "  let extentStepContext := ctx\n"
    "  let placementStepContext := ctx\n"
    "  return (extentStepContext, placementStepContext)"
)

# The frozen fallback assignment (the CHANGED clause of the fix), unique inside
# the impl region.
_I_FALLBACK = "    ctx := some surfaceContext"

# The frozen initial binding, unique inside the impl region.
_I_INIT = "  let mut ctx := suppliedContext"

# The binding handed to the LATER (placement) step, unique inside the impl
# region. Anchors the rival that resolves for the earlier step only.
_I_PLACEMENT = "  let placementStepContext := ctx"

# The frozen impl's `def` header. Unique in the file and INSIDE the impl region
# (`-- impl-start` precedes it), so a case may prefix it with `noncomputable`
# when its rival body needs a non-executable term. Same-spec is unaffected (the
# whole impl region is elided from the spec view) and the theorem statement is
# untouched.
_I_HDR = "def implementation_resolveRenderContext"

# The frozen proof body (proof region).
_P_FROZEN = (
    "  intro suppliedContext surfaceContext\n"
    "  unfold problem_spec_resolveRenderContext implementation_resolveRenderContext\n"
    "  cases suppliedContext <;> exact ⟨rfl, rfl⟩"
)

for _a in (_I_BODY, _I_FALLBACK, _I_INIT, _I_PLACEMENT, _I_HDR, _P_FROZEN):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drift ({_BASE.count(_a)} hits): {_a!r}")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Each
    # keeps the theorem statement byte-identical and re-uses the frozen tactic
    # body (no helper lemma, no axiom, no assumption token introduced).
    #
    # Ports nagini case `pos-control-branch-reorder`: the nagini positive
    # replaced the gold "default-then-overwrite-if-none" shape with an explicit
    # two-arm branch on `renderer is None`, one resolution per arm. Here the
    # analogous structural reshape is an explicit `match` on the optional
    # supplied context.
    # =====================================================================
    {
        "id": "pos-control-match-branch",
        "kind": "soundness",
        "expect": "verify",
        # Replace the mutable default-then-overwrite shape with an explicit
        # two-arm match, each arm building the pair for both steps directly:
        # `some r` hands `some r` to both, `none` hands the surface context to
        # both. Same pair on every input, so both conjuncts still hold. The
        # frozen `cases suppliedContext <;> exact ⟨rfl, rfl⟩` closes both arms
        # after the match reduces definitionally.
        "module": _swap(
            _BASE, _I_BODY,
            "  match suppliedContext with\n"
            "  | some r => return (some r, some r)\n"
            "  | none => return (some surfaceContext, some surfaceContext)",
        ),
        "rationale": "structurally-different correct impl: an explicit two-arm "
                     "`match` on the optional supplied context (one resolution "
                     "per arm, built into the pair directly) replacing the gold "
                     "default-then-overwrite shape with a shared local. The pair "
                     "handed downstream is identical on every input (`(some r, "
                     "some r)` on a supplied context, `(some surfaceContext, some "
                     "surfaceContext)` on none), so both conjuncts of the "
                     "postcondition still hold. Must verify, else the resolution "
                     "clause is SPEC-TOO-STRONG — in particular, pinning the pair "
                     "componentwise must not force the gold's SHAPE (one shared "
                     "mutable local) on a correct impl that resolves per arm. "
                     "Proof: the frozen `cases … <;> exact ⟨rfl, rfl⟩` closes both "
                     "arms. Ports nagini's branch-reorder positive to the single "
                     "modeled site.",
    },
    {
        "id": "pos-control-getd-inlined",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the whole body to the single `getD` expression the spec pins,
        # bound once and shared by both components. A different impl SHAPE (no
        # mutable local, no conditional) computing the same pair; the frozen
        # `cases … <;> exact ⟨rfl, rfl⟩` still closes both arms.
        "module": _swap(
            _BASE, _I_BODY,
            "  let resolved := some (suppliedContext.getD surfaceContext)\n"
            "  return (resolved, resolved)",
        ),
        "rationale": "a second structurally-different correct impl: collapse the "
                     "mutable-local conditional to the single fallback expression "
                     "`some (suppliedContext.getD surfaceContext)`, bound once and "
                     "handed to both steps. No mutable local, no branch — a "
                     "distinct shape from both the gold and the match-branch "
                     "positive — yet the pair is identical on every input, so both "
                     "conjuncts hold. Must verify. Proof: frozen `cases … <;> exact "
                     "⟨rfl, rfl⟩` closes both arms. Defends the resolution clause "
                     "with a second correct reshape on a different impl form.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal, F2P-shaped input rather than only
    # in the abstract. The FAIL_TO_PASS scenario (`test_inset_axes_tight`) calls
    # the locator with the context ABSENT (`renderer=None` ↔ `suppliedContext =
    # none`), so the F2P-shaped input is the no-context / surface-fallback path.
    # The frozen theorem carries no precondition hypothesis (total behavior, `∀`
    # unguarded), so the nagini precondition-admission probe
    # (`admiss-no-renderer-path`) has no binder to attack; the honest analogue
    # discharges the spec predicate at the no-context input (surface quantified,
    # since RenderContext is opaque and has no literal) by `exact ⟨rfl, rfl⟩`
    # inside a `have`, then closes the frozen obligation verbatim. Nothing is
    # assumed: no new top-level declaration, statement byte-identical. Ports
    # nagini's `admiss-no-renderer-path`.
    # =====================================================================
    {
        "id": "admiss-no-context-path",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_FROZEN,
            "  have _adm : ∀ (s : RenderContext),\n"
            "      problem_spec_resolveRenderContext none s\n"
            "        (implementation_resolveRenderContext none s) := by\n"
            "    intro s\n"
            "    unfold problem_spec_resolveRenderContext implementation_resolveRenderContext\n"
            "    exact ⟨rfl, rfl⟩\n"
            + _P_FROZEN,
        ),
        "rationale": "the obligation — BOTH conjuncts, i.e. both downstream steps "
                     "— is discharged at the F2P-shaped no-context input (the "
                     "tight-bbox path calls the locator with the context absent; "
                     "`suppliedContext = none`, surface quantified since the opaque "
                     "carrier has no literal) by `exact ⟨rfl, rfl⟩` in a `have`, "
                     "then the frozen obligation is closed verbatim. Verifies (else "
                     "the modeled behavior is unsatisfiable at exactly the input "
                     "the F2P exercises — the analogue of PRECOND-TOO-STRONG). "
                     "Nothing is assumed: no new declaration, the theorem statement "
                     "is byte-identical, and the ground instance is a `have` inside "
                     "the existing tactic body. Ports nagini's no-renderer-path "
                     "admissibility probe. LOAD-BEARING, measured (audit): the "
                     "`have` is not a decoration that would elaborate against "
                     "anything. Built against the pre-fix impl (the no-context path "
                     "left unresolved), the SAME `have` fails on its own line: the "
                     "`⟨rfl, rfl⟩` is rejected with `Application type mismatch`, "
                     "reported against the component whose unresolved side is not "
                     "definitionally equal to `some (none.getD s)`. Re-measured in "
                     "the audit against a SECOND wrong impl (the resolved context "
                     "to the extent step, the caller's raw value to the placement "
                     "step), where the same `have` fails the same way on the "
                     "second component (`(pure (some (none.getD s), none)).run.2 = "
                     "some (none.getD s)`). So the ground instance genuinely "
                     "discharges the obligation at the F2P-shaped input rather than "
                     "restating it.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement argument
    # that its faithful real patch would NOT resolve the F2P, so a verifying
    # rival would be a true verify-does-not-imply-resolve break rather than an
    # artifact, and (b) a refutation witness pinning the violation at one
    # concrete input (conditioned on the opaque carrier where required).
    # =====================================================================

    # ---- the fix itself: leave the context UNRESOLVED on the no-context path
    #      (the pre-fix bug). Ports nagini `reject-skip-measurement-no-renderer`
    #      / the pre-fix propagation the whole patch removes. ----
    {
        "id": "reject-unresolved-on-no-context",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior: on the no-context path, do NOT resolve the surface
        # context — leave `ctx` as `none`, so "nothing" is what both downstream
        # steps are handed.
        "module": _swap(_BASE, _I_FALLBACK, "    ctx := none"),
        "refinement": "this IS the pre-fix behavior: on the no-context path the "
                      "routine never resolves a present context and hands "
                      "'nothing' to its downstream steps. In the reported "
                      "tight-bbox scenario the extent arithmetic is handed nothing "
                      "and raises (the reported AttributeError), so the "
                      "FAIL_TO_PASS save still crashes — the faithful real patch "
                      "would NOT resolve.",
        "rationale": "REJECT from the surface-fallback clause: on `suppliedContext "
                     "= none` the spec pins BOTH components to `some "
                     "surfaceContext` while the rival hands `none` to both, so "
                     "`result.1` already differs by `Option` disjointness. Binder "
                     "spread: probes `suppliedContext = none` (the surface-fallback "
                     "branch of `getD`) at the point where NOTHING is resolved; the "
                     "witness needs no hypothesis on the opaque carrier "
                     "(`none ≠ some _`).",
        "witness": (
            "-- Refuted on the no-context path. The rival hands `none` to both steps\n"
            "-- where the spec requires `some surfaceContext`; these are disjoint\n"
            "-- `Option` constructors, so no hypothesis on the opaque carrier is\n"
            "-- needed. The first conjunct alone is already false.\n"
            "--\n"
            "-- AUDIT REPAIR (discrimination). `pure` and `Id.instMonad` are in the\n"
            "-- simp set, not just `Id.run`. `unfold` on an `Id.run do` body leaves a\n"
            "-- `pure (…)` application, and `Id.run` alone does not reduce it, so with\n"
            "-- `simp [Id.run]` gold's goal stayed `(pure (some sC, some sC)).1 = some\n"
            "-- sC` — an equation simp never discharged. Gold then failed for BOTH the\n"
            "-- refutation AND its flipped opposite (measured: the claim that gold is\n"
            "-- CORRECT here is also exit 1), so gold's exit code attested nothing.\n"
            "-- With `pure`/`Id.instMonad` the residue reduces: the type-reveal shows\n"
            "-- gold's conjunct becomes `True` (simp PROVED it) while the rival's stays\n"
            "-- a concrete false equation, and the flipped claim now inverts cleanly\n"
            "-- (exit 0 on gold, exit 1 on the rival).\n"
            "example (surfaceContext : RenderContext) :\n"
            "    ¬ problem_spec_resolveRenderContext none surfaceContext\n"
            "      (implementation_resolveRenderContext none surfaceContext) := by\n"
            "  unfold problem_spec_resolveRenderContext implementation_resolveRenderContext\n"
            "  simp [Id.run, pure, Id.instMonad]\n"
        ),
    },

    # ---- THE PORTED SPEC-TOO-WEAK ATTACK: resolve for the EARLIER step only and
    #      let the LATER step proceed with "nothing". Under the previous
    #      single-context model this rival VERIFIED (measured; recorded in
    #      verdict.md as the retained G-EQ / G-PANEL-1 attack), while its faithful
    #      real counterpart does not repair the instance at all. It is shipped
    #      here so the repaired postcondition's SHARING clause is defended by a
    #      case rather than by argument. ----
    {
        "id": "reject-unresolved-at-later-step",
        "kind": "uniqueness",
        "expect": "reject",
        # Wrong: the fallback still runs, so the EXTENT step gets the resolved
        # context — but the PLACEMENT step is handed the caller's original value,
        # which on the no-context path is "nothing". Exactly the shape that
        # slipped through the single-context model.
        "module": _swap(_BASE, _I_PLACEMENT,
                        "  let placementStepContext := suppliedContext"),
        "refinement": "its faithful patch resolves a context for the extent call "
                      "site only (e.g. binding a separate local for that call) "
                      "while the later placement call still receives the caller's "
                      "original argument. On the tight-bbox path the caller passes "
                      "nothing, so the extent step now succeeds and the SAME "
                      "failure reappears one frame downstream, in the placement "
                      "step's own arithmetic, which dereferences the context it "
                      "was handed. The FAIL_TO_PASS save therefore still raises "
                      "and the instance is NOT resolved. MEASURED, not argued: an "
                      "impl of exactly this shape was submitted against the "
                      "previous single-context postcondition, VERIFIED, and its "
                      "patch failed FAIL_TO_PASS 1/1 while passing 49/49 "
                      "PASS_TO_PASS — a true verify-does-not-imply-resolve break. "
                      "The differential in conformance_check.py was widened in the "
                      "same repair and now separates this shape from gold on the "
                      "real post-patch code (measured: 46 disagreements in 300 "
                      "inputs, all on the second component).",
        "rationale": "REJECT from the SHARING clause: pinning BOTH components to "
                     "the same grounded term forces every downstream step to see "
                     "the resolved context, so settling the question for the "
                     "earlier step and leaving the later one holding `none` is "
                     "excluded. Uniquely among the rivals, `result.1` MATCHES the "
                     "spec here and only `result.2` is violated — this is the case "
                     "that proves the second conjunct is load-bearing, and the case "
                     "the previous single-component postcondition could not "
                     "express. Binder spread: shares the `none` input with the "
                     "other two `none` rivals but is the only one refuted through "
                     "the second component.",
        "witness": (
            "-- Refuted on the no-context path, through the SECOND component only.\n"
            "-- The fallback still runs, so the extent step is handed the resolved\n"
            "-- `some surfaceContext` and the first conjunct holds; the placement\n"
            "-- step is handed the caller's original `none`, which is disjoint from\n"
            "-- the required `some surfaceContext`. No hypothesis on the opaque\n"
            "-- carrier is needed. Under a postcondition that constrained only the\n"
            "-- first component this claim would be UNPROVABLE (there would be\n"
            "-- nothing false to derive), which is exactly why the second conjunct\n"
            "-- exists.\n"
            "--\n"
            "-- AUDIT REPAIR (discrimination): same `pure`/`Id.instMonad` repair as the\n"
            "-- surface-fallback witness — under `simp [Id.run]` the unreduced `pure`\n"
            "-- residue made gold fail for the flipped claim too, so the gold-side exit\n"
            "-- code carried no information. Measured on this rival as well: refutation\n"
            "-- exit 0 / flipped exit 1 against the rival, and the mirror against gold.\n"
            "-- Independently confirmed load-bearing through the SECOND component: a\n"
            "-- witness refuting only `result.1` at this input ELABORATES against the\n"
            "-- surface-fallback rival but FAILS against this one (whose first\n"
            "-- component matches the spec), so this case is refuted by `result.2`\n"
            "-- alone and nothing else in the battery covers that.\n"
            "example (surfaceContext : RenderContext) :\n"
            "    ¬ problem_spec_resolveRenderContext none surfaceContext\n"
            "      (implementation_resolveRenderContext none surfaceContext) := by\n"
            "  unfold problem_spec_resolveRenderContext implementation_resolveRenderContext\n"
            "  simp [Id.run, pure, Id.instMonad]\n"
        ),
    },

    # ---- ignore the supplied context: always take the surface. Ports nagini
    #      `reject-ignore-supplied-renderer` (measure against the resolved
    #      context on BOTH branches, ignoring the supplied one). ----
    {
        "id": "reject-ignore-supplied-context",
        "kind": "uniqueness",
        "expect": "reject",
        # Wrong: initialize `ctx` to the surface context unconditionally, so a
        # supplied context is discarded (the conditional then never changes it)
        # and both steps are handed the surface's context.
        "module": _swap(_BASE, _I_INIT, "  let mut ctx := some surfaceContext"),
        "refinement": "its faithful patch always sources the surface's context "
                      "(`ax.figure._get_renderer()`) even when the caller threaded "
                      "in a real context. On the supplied-context paths the normal "
                      "render/save and the position/image P2P tests exercise "
                      "(test_inset_locator, test_anchored_locator_base_call), the "
                      "geometry would be measured against a DIFFERENT context than "
                      "the one passed in, perturbing the computed extents => those "
                      "P2P tests would NOT pass. Not a faithful resolve.",
        "rationale": "REJECT from the supplied-passthrough clause: on "
                     "`suppliedContext = some r` the spec pins both components to "
                     "`some r` while the rival hands `some surfaceContext` to both; "
                     "these differ whenever `surfaceContext ≠ r`. Binder spread: "
                     "the ONLY rival probing `suppliedContext = some _`, and it "
                     "also MOVES the `surfaceContext` binder to a value distinct "
                     "from the supplied one — the exact separating sub-domain — so "
                     "both input binders are demonstrated live rather than held "
                     "fixed.",
        "witness": (
            "-- Refuted on the supplied-context path, conditioned on the opaque\n"
            "-- carrier: whenever the surface context differs from the supplied\n"
            "-- one, the rival's `some surfaceContext` differs from the spec's\n"
            "-- `some r`. One hypothesis on one opaque term; jointly satisfiable.\n"
            "--\n"
            "-- AUDIT REPAIR (discrimination). The refutation is discharged by\n"
            "-- `injection` on the relevant CONJUNCT of the `Option` equality\n"
            "-- rather than by applying `Option.some.inj` to the raw hypothesis.\n"
            "-- Both scripts elaborate against the rival, but `exact h\n"
            "-- (Option.some.inj hh.1)` failed on the frozen solution with\n"
            "-- `Application type mismatch ... in the application Option.some.inj` —\n"
            "-- the `Id.run do` block's `have ctx := ...; if ... then ...` term is\n"
            "-- not syntactically `some _`, so the lemma simply does not APPLY\n"
            "-- there. That is a syntactic non-application, not a semantic\n"
            "-- refutation of the concrete claim, and the same mismatch appears for\n"
            "-- a claim that is FALSE of the rival (measured), so the gold-side\n"
            "-- exit code discriminated nothing. `injection` unfolds the impl by\n"
            "-- whnf first, so on gold the build now fails on the residual goal\n"
            "-- `surfaceContext = r` — the actual unprovable content: gold hands the\n"
            "-- SUPPLIED context to each step here, and `h : surfaceContext ≠ r` is\n"
            "-- exactly why the claim is false of gold.\n"
            "example (r surfaceContext : RenderContext) (h : surfaceContext ≠ r) :\n"
            "    ¬ problem_spec_resolveRenderContext (some r) surfaceContext\n"
            "      (implementation_resolveRenderContext (some r) surfaceContext) := by\n"
            "  unfold problem_spec_resolveRenderContext implementation_resolveRenderContext\n"
            "  intro hh\n"
            "  apply h\n"
            "  injection hh.1\n"
        ),
    },

    # ---- SUBSTITUTE SOURCE: on the no-context path resolve a context that is
    #      PRESENT but is not the host surface's. Ports nagini
    #      `reject-substitute-present-context`, which the first port dropped as
    #      "unportable: no second inhabitant of the opaque carrier exists". The
    #      audit landed it: a second inhabitant does not have to be CONSTRUCTED,
    #      only DENOTED, and `Classical.choice ⟨surfaceContext⟩` denotes an
    #      element of the carrier that nothing identifies with `surfaceContext`.
    #      This is the case class that distinguishes "settles on SOME present
    #      context" from "settles on the HOST SURFACE's context" — the clause the
    #      other rivals leave unattacked, and the one whose nagini ancestor is a
    #      recorded spec-too-weak failure under a presence-only postcondition. ----
    {
        "id": "reject-substitute-present-source",
        "kind": "uniqueness",
        "expect": "reject",
        # Wrong: on the no-context path resolve a context that is present but is
        # NOT the one the host's drawing surface furnishes. `Classical.choice` on
        # the carrier's nonemptiness witness yields such an element: it inhabits
        # `RenderContext` (so both components are genuinely `some _`, satisfying a
        # presence-only reading) while being provably-nothing in particular, so
        # it cannot be shown equal to `surfaceContext`. The impl is marked
        # `noncomputable` because `Classical.choice` has no code generator; the
        # header edit lies inside the impl region, so same_spec and the frozen
        # theorem statement are untouched.
        "module": _swap(
            _swap(_BASE, _I_FALLBACK,
                  "    ctx := some (Classical.choice "
                  "(⟨surfaceContext⟩ : Nonempty RenderContext))"),
            _I_HDR, "noncomputable " + _I_HDR,
        ),
        "refinement": "its faithful patch resolves the no-context path from a "
                      "SUBSTITUTE present source — a freshly constructed "
                      "measurement context of its own, rather than the one the "
                      "host's drawing surface furnishes. The downstream steps then "
                      "measure and place the sub-region against a context whose "
                      "scale/size need not match the host surface's, so the "
                      "placement computed on the tight-bbox path differs from the "
                      "gold's whenever the two disagree. The thin no-raise F2P "
                      "cannot observe that (a present context is enough to avoid "
                      "the crash), which is exactly why the SPEC has to pin the "
                      "source rather than mere presence — a rival that verified "
                      "here would be a true verify-does-not-imply-resolve break.",
        "rationale": "REJECT from the surface-fallback clause's SOURCE, not its "
                     "presence: the spec pins both components to `some "
                     "surfaceContext` on `suppliedContext = none`, so handing some "
                     "OTHER present element to the steps is unprovable. This is "
                     "the only rival that separates 'settles on a present context' "
                     "from 'settles on the host surface's context'; the "
                     "unresolved-on-no-context rival attacks presence, the "
                     "later-step rival attacks sharing, and the ignore-supplied "
                     "rival attacks the other branch, so a presence-only "
                     "postcondition would still reject those while admitting this "
                     "one. Binder spread: shares the `none` input with the other "
                     "`none` rivals but moves the RESOLVED value off "
                     "`surfaceContext`, a point no other rival visits.",
        "witness": (
            "-- Refuted on the no-context path, conditioned on the opaque carrier:\n"
            "-- if the substitute element differs from the surface's context, the\n"
            "-- rival's `some (substitute)` is not the spec's `some surfaceContext`.\n"
            "-- One hypothesis, about one opaque term, and satisfiable: the carrier\n"
            "-- is opaque, so nothing identifies `Classical.choice ⟨surfaceContext⟩`\n"
            "-- with `surfaceContext` and no tactic derives `False` from the\n"
            "-- hypothesis alone (the gate's consistency probe confirms this).\n"
            "-- `injection` on the conjunct (not `Option.some.inj`) so the gold-side\n"
            "-- failure is the SEMANTIC residual goal rather than a lemma that fails\n"
            "-- to apply.\n"
            "example (surfaceContext : RenderContext)\n"
            "    (h : Classical.choice (⟨surfaceContext⟩ : Nonempty RenderContext)\n"
            "           ≠ surfaceContext) :\n"
            "    ¬ problem_spec_resolveRenderContext none surfaceContext\n"
            "      (implementation_resolveRenderContext none surfaceContext) := by\n"
            "  unfold problem_spec_resolveRenderContext implementation_resolveRenderContext\n"
            "  intro hh\n"
            "  apply h\n"
            "  injection hh.1\n"
        ),
    },

    # ---- DIVERGENCE: a routine that never settles the question at all, so no
    #      downstream step is ever reached. Landed by the audit; this class was
    #      previously recorded as an unwitnessable KNOWN HOLE (see the module
    #      docstring for the measurement that overturned that reading). The
    #      refutation does not unfold the non-terminating term — it chains the
    #      spec at TWO DISTINCT surface contexts against each other, which an
    #      input-independent result cannot satisfy at both. ----
    {
        "id": "reject-diverging-resolution",
        "kind": "uniqueness",
        "expect": "reject",
        # Wrong: the routine never terminates, so it never settles on a context
        # and never hands one to either downstream step. `partial` is required
        # because a total `def` may not diverge; the prefix lies inside the impl
        # region, so same_spec and the frozen theorem statement are untouched.
        "module": _swap(
            _swap(_BASE, _I_BODY,
                  "  let rec loop (n : Nat) : "
                  "Option RenderContext × Option RenderContext :=\n"
                  "    loop (n+1)\n"
                  "  return loop 0"),
            _I_HDR, "partial " + _I_HDR,
        ),
        "refinement": "its faithful patch makes the resolution step itself fail "
                      "to complete — the routine spins instead of settling on a "
                      "context, so neither the extent step nor the placement "
                      "step is ever reached. On the tight-bbox path the "
                      "FAIL_TO_PASS save never returns, so it does not pass; and "
                      "because the routine is on the normal draw path too, every "
                      "PASS_TO_PASS position/image test hangs as well. Strictly "
                      "worse than the pre-fix behavior, which at least raised.",
        "rationale": "REJECT because the obligation is a TOTAL one: the frozen "
                     "theorem quantifies over every input and pins both "
                     "components to a grounded term computed FROM those inputs, "
                     "so a result that cannot depend on the inputs at all "
                     "satisfies it at no more than one point. Binder spread: this "
                     "is the only case that moves the `surfaceContext` binder to "
                     "TWO values in a single claim, and the only one whose "
                     "refutation comes from the input-DEPENDENCE of the pinned "
                     "term rather than from the value at one point. Attacks the "
                     "surface-fallback clause at two distinct surface contexts "
                     "simultaneously.",
        "witness": (
            "-- Refuted at a PAIR of no-context points with distinct surface\n"
            "-- contexts. Nothing about the non-terminating term is unfolded, and\n"
            "-- nothing needs to be: the spec pins `result.1` to `some a` at\n"
            "-- `(none, a)` and to `some b` at `(none, b)`, while this rival's first\n"
            "-- component is the SAME input-independent term at both points. The two\n"
            "-- conjuncts therefore chain to `some a = some b`, contradicting the\n"
            "-- hypothesis. One hypothesis, on two carrier elements, and plainly\n"
            "-- satisfiable — the carrier is opaque, so no tactic derives `False`\n"
            "-- from `a ≠ b` (the gate's consistency probe confirms it).\n"
            "--\n"
            "-- DISCRIMINATION, measured in both directions (attack B'). Against the\n"
            "-- rival this elaborates; against the frozen solution it fails with\n"
            "-- `Invalid field `symm`: The environment does not contain `True.symm`,\n"
            "-- h1 has type True` — i.e. simp PROVED the frozen impl's\n"
            "-- first-component equation at BOTH points, leaving nothing to chain, so\n"
            "-- the refutation genuinely does not hold of gold. The FLIPPED claim\n"
            "-- (that the pair IS correct at both points) inverts cleanly: it holds\n"
            "-- of gold and fails of the rival. The gold-side error is a plain\n"
            "-- evaluation residue — none of the stuck-reduction screens fire (no\n"
            "-- undecided `decide`, no dependent-elimination failure, no missing\n"
            "-- `Decidable` instance). The same witness was also refuted against four\n"
            "-- other VERIFYING impls of this spec, so its gold-side failure follows\n"
            "-- from satisfying the spec, not from gold's syntactic shape.\n"
            "example (a b : RenderContext) (hab : a ≠ b) :\n"
            "    ¬ (problem_spec_resolveRenderContext none a\n"
            "         (implementation_resolveRenderContext none a)\n"
            "       ∧ problem_spec_resolveRenderContext none b\n"
            "         (implementation_resolveRenderContext none b)) := by\n"
            "  unfold problem_spec_resolveRenderContext implementation_resolveRenderContext\n"
            "  intro hh\n"
            "  have h1 := hh.1.1\n"
            "  have h2 := hh.2.1\n"
            "  simp [Id.run, pure, Id.instMonad] at h1 h2\n"
            "  exact hab (Option.some.inj (h1.symm.trans h2))\n"
        ),
    },
]

# No AXIOM lane here: the bundle consumes no `axiom` (the surface's context is
# modeled as the plain input `surfaceContext`, not an axiomatized callee, per
# mapping.md; axiom_check.py is a skip stub and G-AX skips). The nagini
# AXIOM_TESTS belong to G-AX and are dropped.
AXIOM_TESTS = []
