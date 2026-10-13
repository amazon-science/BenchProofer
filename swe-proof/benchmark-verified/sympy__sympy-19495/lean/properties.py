"""properties.py — G-PBT falsification battery for sympy__sympy-19495 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region is changed, so ``markers.same_spec`` holds and the
``theorem correct_freeSubs`` STATEMENT stays byte-identical). ``expect:"verify"``
passes iff (in scope AND the file elaborates with the obligation closed, no
``sorry``/``admit``/``native_decide`` and no new ``axiom``/``theorem``);
``expect:"reject"`` passes iff (in scope AND it does NOT verify AND the case's
refutation ``witness`` holds of the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled behavior; a single spec equation over the input's
three components). A set is described by three components — a BOUND VARIABLE, a
condition phrased on that variable, and a base set the variable ranges over.
Substituting a *free* symbol ``old`` (one that is NOT the bound variable) by
``new`` acts only on the condition and the base set; the bound variable is part
of the binding structure and must be carried through unchanged — INCLUDING the
corner case where the substitution collapses the condition to trivially-true.
The spec pins this as ONE equation naming the result exactly:

  problem_spec_freeSubs (cs : CondSet) (old new : Expr) (result : AsmSet) : Prop
    result = mkSet cs.sym (subsCond cs.cond old new) (subsSet cs.base old new)

``mkSet`` is the OPAQUE set-assembly routine and ``subsCond``/``subsSet`` are the
OPAQUE ordinary substitution routine taken at the condition and at the base-set
component (no constraining axiom; their value at any point is unknown to the
tactics), all three reused unchanged.

The three independent behavioural commitments are the three ARGUMENT POSITIONS of
that assembly, and this manifest calls them ARG 1 / ARG 2 / ARG 3:

    ARG 1 = cs.sym                    -- binding structure preserved
    ARG 2 = subsCond cs.cond old new  -- condition substituted
    ARG 3 = subsSet cs.base old new   -- base substituted

Since ``mkSet`` carries no axiom, the ONLY route to the equation is congruence,
so an implementation that disagrees at any one position cannot discharge it. That
is why a single equation is not a weaker statement than a three-field
conjunction: it pins the same three commitments, and it additionally refuses to
say anything about what an assembled set is made of (see "WHY AN ASSEMBLED SET
IS ITS OWN CARRIER" below), which is what keeps every term of the model denoting a routine
call that is actually defined.

WHY THE BINDING POSITION HAS ITS OWN CARRIER (the DOMAIN obligation that decides
which rivals can even be written). ARG 1's position does not accept a general
expression: ``mkSet`` has type ``SymE → Cond → SetE → AsmSet``, where ``SymE``
is the carrier of BOUND VARIABLES, and the only bridge between the carriers is the one-way inclusion
``symExpr : SymE → Expr`` (used where an expression is called for, e.g. comparing
the bound variable with the symbol being substituted). This is forced by the real
routine, in both directions:

  * FAITHFULNESS. The real assembly routine is PARTIAL in its first argument: for
    a first argument that is not a symbol it raises ``ValueError: non-symbol dummy
    not recognized in condition`` unless that argument occurs in the condition it
    is handed. Measured on the gold-patched testbed: the gold call itself raises
    for a non-symbol bound variable (``ConditionSet(2*x, Eq(2*x, y),
    Reals).subs(x, 3)`` → that ``ValueError``, and so does the spelled-out
    ``self.func(self.sym, cond, base)`` at the same input), while the identical
    input with a symbol bound variable returns normally. A model whose ARG-1
    position ranged over general expressions would therefore be describing calls
    the real routine cannot make.
  * DEFINEDNESS OF EVERY WELL-TYPED TERM. A Lean ``opaque`` is TOTAL. Restricted
    to a symbol first argument the real assembly IS total over the shapes this
    branch ranges over: 672 (symbol, condition, base) triples over a pool of 7
    symbols × 8 conditions × 12 base sets, 0 raises. Un-restricted it is not, and
    the gap is reachable: enumerating EVERY well-typed term of the modeled
    vocabulary at each triple that the F2P + P2P tests actually push through this
    branch gives 1023 raises out of 21444 terms when the ARG-1 position is drawn
    from the general expression pool — every one of them that same ``ValueError``
    through the assembly — against 0 raises out of 12732 terms with the position
    typed by ``SymE``. So the carrier split is what makes "well-typed here"
    coincide with "a call the real code can make", which is the property a rival
    is judged against.

The one shape that legitimately needs a general expression in a binding position
is the pre-patch's own deleted expression ``ConditionSet(new, Contains(new,
base), base)``, and it is available as ONE fused routine ``mkMemberSet : Expr →
SetE → AsmSet``, because the real routine's ARG-1 domain rule is a JOINT
constraint on its first two arguments: a non-symbol first argument is accepted
exactly when it occurs in the condition, which is why the pair (value, membership
condition on that value) is defined while the value alone with an arbitrary
condition is not. Measured: ``ConditionSet(v, Contains(v, b), b)`` over 18 values
× 12 base sets returns normally on 198 of 216 pairs. The 18 that raise all have
the SAME base set — one that is itself condition-restricted (``ConditionSet(z,
z<y, Reals)``), where the membership routine raises ``TypeError: Incompatible use
of binary symbol`` from the boolean simplifier — and such a set is not an
inhabitant of the base-set carrier at all (see WHY AN ASSEMBLED SET IS ITS OWN
CARRIER and WHAT THE CONDITION AND BASE-SET CARRIERS DENOTE). Keeping the
membership routine fused also removes the bare membership question, whose off-domain calls were an earlier
rival family, from the vocabulary entirely.

WHY AN ASSEMBLED SET IS ITS OWN CARRIER, AND A TERMINAL ONE (the domain
obligation this spec was last strengthened on, and the reason the OUTPUT carrier
differs from both the input record and the base-set carrier). The modeled routine
assembles a set exactly ONCE, at the end, and returns it; nothing it does consumes
an assembled value. The model says so: ``mkSet`` and ``mkMemberSet`` land on
``AsmSet``, which has no projections and appears in no argument position, so an
assembled set can be neither taken apart, nor substituted into, nor restricted
further. Both halves are forced by measurement on the gold-patched testbed:

  * NO PROJECTIONS. The assembly NORMALISES its arguments: handed a bound
    variable, a condition and a base set it may return an object that is not of
    the three-part shape at all (a bare interval, an image, the empty set), in
    which case asking that result for its bound variable, its condition or its
    base is UNDEFINED and raises ``AttributeError``. The INPUT keeps the
    three-field record ``CondSet`` — it is a set already known to be of the
    three-part shape, so reading its components off is exactly as defined as the
    modeled routine's own reads.
  * NO CONSUMER. An assembled set is condition-restricted, and the routines that
    take a base set are not defined on those. Enumerating the terms that put an
    assembled set in a consumer position at the four tested triples gives 53280
    terms, of which 5136 RAISE outright — ``TypeError: Incompatible use of binary
    symbol `x` as a real variable in `x < y``` out of the boolean simplifier for
    the membership assembly, plus ``BadSignatureError`` where the assembled set
    reaches a binder position — and the remaining 41344 apply the substitution
    routine to an assembled set, which re-enters the modeled routine on an
    argument rebuilt from its own components and DIVERGES (measured in-process by
    adding that one discarded call inside the routine: ``RecursionError: maximum
    recursion depth exceeded``). With the carrier terminal, every one of those
    53280 terms is a Lean type error instead; the error text for the three shapes
    an audit found is quoted in the OUT-OF-DOMAIN entry below.

TYPED CARRIERS (the reason there are five of them, and a REJECTION CRITERION this
battery's judge must apply to every rival it reads). The carriers are ``Expr`` (a
general symbolic expression), ``SymE`` (a bound variable), ``Cond`` (a condition
given outright), ``SetE`` (a base set given outright) and ``AsmSet`` (an
assembled set — result-only), mirroring the distinct kinds the modeled routines
are actually defined on. Each is an abstract carrier with structural identity (a
``Nat`` tag inhabits it but is never inspected by the spec and has no counterpart
on the modeled side), so concrete carriers ``(⟨k⟩ : Expr)`` / ``(⟨k⟩ : SymE)`` /
``(⟨k⟩ : Cond)`` / ``(⟨k⟩ : SetE)`` are constructible and ``DecidableEq``, and a
witness can name a particular element.

Separating them is LOAD-BEARING, not decoration: the opaque declarations here are
TOTAL functions, while the routines they model are each defined on some kinds and
raise on the others. Under a single carrier a rival could write a well-typed but
undefined call — bind a set over a value the assembly cannot bind, ask a
membership question about a condition, substitute a set in for a symbol — get it
accepted by the elaborator, and yet have no counterpart on the modeled side at
all; the value would be discarded, so the equation would not notice. With the
carriers separated, every such call is a TYPE ERROR: the file does not elaborate,
so it is not a rival at all. Consequently the modeled vocabulary is exactly {the
five carriers, ``symExpr``, ``mkSet``, ``subsCond``, ``subsSet``, ``isTrue``,
``mkMemberSet``, ``CondSet`` construction and projection}, and a rival that
reaches outside it — tag arithmetic, a crossing between carriers via ``.tag``, a
literal minted on the RESULT carrier, an ambient tracing primitive — is naming
something with no antecedent in the modeled routine and therefore has no faithful
counterpart to judge. Such a rival is OUT OF SCOPE, not evidence about the spec.
(Measured, so the exclusion is not load-bearing anyway: the tag-crossing shape
``mkSet ⟨new.tag⟩ cond' base'`` and the result-carrier literal
``return (⟨0⟩ : AsmSet)`` both ELABORATE, and both are REJECTED by the spec — see
ATTACK D.)

A literal minted on an ARGUMENT carrier is a different matter and IS in the
vocabulary, because it denotes a call the real routine can make. Every inhabitant
of ``SymE`` denotes a bound variable, and the assembly restricted to a symbol
first argument is total over the measured pool, so ``mkSet ⟨0⟩ cond' base'`` is a
DEFINED call whose result is simply not the one the equation names — the real
routine handed a different symbol returns a differently-bound set rather than
raising. That is exactly the sibling's ``weak-build-open-wrong-sym`` shape
(``Result0(K_SET, 0, base, cond)``, the open case keyed on a fixed constant), and
it is shipped here as ``fixed-sym-binding``. The RESULT carrier is the one place
the rule bites, and for a stated reason: ``AsmSet`` is what the assembly RETURNS
and nothing else produces one, so a minted ``AsmSet`` corresponds to no call at
all, whereas a minted ``SymE`` corresponds to the assembly called on some other
bound variable.

OUT-OF-DOMAIN SHAPES ARE NOT BATTERY CASES (recorded here because they are the
first thing an attacker tries, and because the first of them was a live rival
against an earlier revision of this spec). A case can only be a rival if it
ELABORATES; these do not, so they cannot appear in ``SPEC_TESTS`` — an
``expect="reject"`` case whose witness cannot be built against the rival is
inconclusive, not a finding. All were measured with real builds against the
CURRENT frozen spec:

  * BIND THE ASSEMBLY OVER A GENERAL EXPRESSION —
    ``return mkSet new cond' base'``: ``error: Application type mismatch: The
    argument / new / has type / Expr / but is expected to have type / SymE / in
    the application / mkSet new`` (line breaks shown as ``/``). Likewise
    ``mkSet old cond' base'``, with ``old`` in place of ``new``. This is the shape
    whose faithful counterpart raises ``ValueError: non-symbol dummy not
    recognized in condition`` at the F2P input, so it is exactly the class the
    carrier split had to remove.
  * ASK A MEMBERSHIP QUESTION ABOUT A CONDITION —
    ``let _probe := mkMemberSet cond' base'``: ``error: Application type
    mismatch: The argument / cond' / has type / Cond / but is expected to have
    type / Expr / in the application / mkMemberSet cond'``.
  * PROJECT A COMPONENT OUT OF AN ASSEMBLED SET —
    ``let assembled := mkSet cs.sym cond' base'; return mkSet assembled.sym
    assembled.cond assembled.base``: ``error: Invalid field `sym`: The
    environment does not contain `AsmSet.sym` / assembled / has type / AsmSet``
    (likewise ``cond``, ``base``).
  * DESTRUCTURE AN ASSEMBLED SET AS IF IT WERE THE INPUT RECORD —
    ``{ sym := …, cond := …, base := … } : AsmSet``: ``error: `sym` is not a
    field of structure `AsmSet` `` (likewise ``cond``, ``base``), plus
    ``error: Fields missing: `tag` ``.
  * ASK A MEMBERSHIP QUESTION ABOUT AN ASSEMBLED SET —
    ``let _probe := mkMemberSet old (mkSet cs.sym cs.cond cs.base)``:
    ``error: Application type mismatch: The argument / mkSet cs.sym cs.cond
    cs.base / has type / AsmSet / but is expected to have type / SetE / in the
    application / mkMemberSet old (mkSet cs.sym cs.cond cs.base)``. Same error
    with ``symExpr cs.sym`` in the value position, and with a fused membership
    assembly in place of the inner assembly (``mkMemberSet new (mkMemberSet new
    base')``). The faithful counterpart of the first raises ``TypeError:
    Incompatible use of binary symbol `x` as a real variable in `x < y``` at the
    P2P triple ``ConditionSet(x, x<y, {y,z})`` subs y↦w.
  * SUBSTITUTE INTO AN ASSEMBLED SET —
    ``let _probe := subsSet (mkSet cs.sym cs.cond cs.base) old new``: the same
    ``Application type mismatch`` with ``in the application / subsSet (mkSet
    cs.sym cs.cond cs.base)``; likewise for ``subsSet (mkSet cs.sym cond' base')
    old new`` and for ``subsSet (mkMemberSet new base') old new``. The faithful
    counterpart re-enters the modeled routine on an argument rebuilt from its own
    components and DIVERGES (``RecursionError: maximum recursion depth
    exceeded``).
  * RESTRICT AN ASSEMBLED SET FURTHER —
    ``let _probe := mkSet cs.sym cs.cond (mkSet cs.sym cs.cond cs.base)``: the
    same ``Application type mismatch`` at the third position.

In each case the elaboration error is the FIRST error reported; the shapes that
leave the returned value ill-typed then also report a downstream
``Tactic `rfl` failed`` on the carried proof, which is a consequence of the
elaboration failure and not a separate finding. The last three entries are the
class an audit found live against the previous revision (three attacks, each
adding ONE discarded line to the gold impl, each of which verified with no axioms
while its faithful patch failed the F2P test); they are re-encoded verbatim as
positive controls in ATTACK D' below.

The nearby shape that DOES elaborate is the FAITHFUL one and it VERIFIES:
binding the three components as a ``CondSet`` and assembling them once
(``let built : CondSet := {…}; return mkSet built.sym built.cond built.base``) is
what the modeled routine does, and it is ``pos-build-then-assemble`` below. The
distinction the carriers draw is therefore exactly "components read off the
INPUT" (defined) versus "components read off an ASSEMBLED result" (undefined),
and exactly "a set bound over a bound variable, or over a value it is handed a
membership condition for" (defined) versus "a set bound over an arbitrary value"
(undefined) — not "one record literal fewer".

WHAT THE CONDITION AND BASE-SET CARRIERS DENOTE, AND WHY THAT MAKES THE SPEC'S
``=`` SOUND (stated because a domain obligation is only as good as its
measurements). ``SetE`` is a base set GIVEN OUTRIGHT — described by its own range
rather than by a further condition-restriction — and ``Cond`` is a condition
given outright, carrying no condition-restricted set inside it. Three
measurements make that the right cut:

  * IT COSTS NO TESTED COVERAGE. Instrumenting the real routine and running the
    F2P + P2P tests records 14 entries, of which exactly 4 reach the modeled
    branch: ``ConditionSet(x, x<y, {y,z})`` subs y↦w; ``ConditionSet(n, n<x,
    (0,oo))`` and ``ConditionSet(n, n<x, (-oo,0))`` subs x↦p; and the F2P's
    ``ConditionSet(x, Contains(y, [-1,1]), ImageSet(…asin(y)…))`` subs y↦1/3. In
    all four the bound variable is a symbol (so the ARG-1 narrowing is free) and
    NEITHER the condition NOR the base set contains a condition-restricted set
    (so this narrowing is free too).
  * THE ROUTINES ARE TOTAL THERE. Enumerating every well-typed term of the
    vocabulary at those four triples gives 12732 terms and 0 raises.
  * THE ROUTINES ARE FUNCTIONS THERE, ON STRUCTURAL IDENTITY — which is what lets
    the spec state its requirement as an equation between assembled values, with
    no quotient anywhere. Over 80299 fuzzed inputs on these shapes the
    transliteration of the spec's right-hand side equals the real routine's result
    under plain structural equality (0 disagreements, no renaming allowance
    needed), and repeating each of the substitution routines, the assembly and the
    whole routine three times gives 0 instabilities. Both properties FAIL outside
    the narrowing, which is why it is part of the carrier rather than prose: with a
    condition-restricted base the assembly can take the arm that renames a
    colliding bound variable and mint a FRESH name per call (three repeats
    pairwise unequal, pairwise equal-up-to-renaming), and the substitution routine
    is not capture-avoiding, so on a base with a nested binder it does not respect
    renaming either (``ConditionSet(y, y<x, Reals)`` and ``ConditionSet(z, z<x,
    Reals)`` are the same set up to renaming, but substituting x↦z gives
    ``ConditionSet(y, y<z, Reals)`` from the first and the degenerate
    ``ConditionSet(z, z<z, Reals)`` from the second). A model that took those
    shapes in would have to choose between an assembly that is not a function and
    substitution routines that are not; on the shapes this branch receives,
    neither problem exists and both are genuine functions.

Two measured shapes sit outside that reading, and both are excluded by the
carriers rather than argued away:

  * a base set whose ELEMENT is itself a set: ``ConditionSet(x, x < 1,
    FiniteSet(Interval(0,1)))`` raises ``SympifyError``, though the same base with
    a condition not mentioning the bound variable returns normally. This is the
    one residual the carriers do not separate — a set of sets is still a set given
    outright — and it is not reachable from the four triples (0 raises in the
    enumeration above);
  * a base set that is itself condition-restricted: the membership routine raises
    ``TypeError: Incompatible use of binary symbol`` for ``Contains(v,
    ConditionSet(z, z<y, Reals))``. This is no longer a residual: such a set is
    not an inhabitant of ``SetE``, and the one way an implementation could
    manufacture one — assembling it — now lands on ``AsmSet``, which no routine
    consumes.

WHY THE GUARD IS A STRUCTURAL DISEQUALITY. The obligation's binder hypothesis is
``old ≠ symExpr cs.sym``, i.e. the substituted symbol is structurally not the
bound variable, whereas the real branch test is sympy's ``old == self.sym``,
which is semantic and coarser. Those two can disagree — measured: over a 12-value
pool, 6 of 144 ordered pairs are semantically equal but structurally different,
and every one of them is a Float against an Integer (``Float(2.0) == Integer(2)``
is ``True`` while ``.subs`` matches structurally, so ``(x>2).subs(Float(2.0), q)``
is a no-op where ``(x>2).subs(Integer(2), q)`` substitutes). None involves a
symbol on either side, and the real disagreement it can produce needs a NON-symbol
bound variable to sit on (``ConditionSet(Integer(2), x>2, Integers)._eval_subs(
Float(2.0), q)`` takes the rename branch although the two are structurally
distinct). With ARG 1 narrowed to a bound variable, that input is outside the
model, and on the remaining domain the structural guard and the real test
coincide — so the guard can stay a plain decidable disequality instead of an
opaque semantic-equality predicate, which would have brought its own vacuity
risk.

BINDER STRUCTURE (read before judging binder/argument coverage). The spec has
three inputs — ``cs`` (whose fields ``sym``/``cond``/``base`` each feed a distinct
argument position), ``old`` and ``new`` — and three INDEPENDENT positions. Each is
attacked by a rival that mishandles exactly one field:

  * ARG 1 is the LOAD-BEARING one (the pre-patch bug). A collapsed-to-true
    condition must NOT rebind the bound variable to ``new``; the rival that does
    is the faithful pre-patch shape. The carrier split narrows HOW that family
    can be spelled but does not reduce it to one shape: putting the SUBSTITUTED
    VALUE in the binding position does require the fused membership assembly
    (``new`` is an ``Expr``, and the plain assembly's first position is
    ``SymE``), but putting some OTHER bound variable there needs no such
    routine, because a bound variable is directly constructible
    (``(⟨k⟩ : SymE)``) and the plain assembly accepts it. So the family has
    THREE shipped members: the two that key the result on ``new`` through the
    fused assembly (``true-rebind-to-new``, ``open-rebind-to-new``) and one that
    keeps the plain assembly and substitutes a DIFFERENT bound variable for the
    input's (``fixed-sym-binding``). An earlier revision of this manifest
    asserted the fused assembly was the ONLY route; that was wrong — measured,
    ``mkSet ⟨0⟩ cond' base'`` elaborates, is rejected, and carries a
    discriminating witness — and is retracted.
  * ARG 2 / ARG 3 pin that the condition and base are the input components with
    the substitution applied — dropping either substitution (assembling from the
    un-substituted component) is refuted.

The seven reject witnesses probe SEVEN DISJOINT input points (disjoint carrier
tags for ``cs``/``old``/``new`` each time), so every input is varied and no
position is left constant across the battery.

ALL THREE POSITIONS are attacked on BOTH sides of the collapse test, which is
what makes each one's coverage a domain rather than a point:

  * ARG 1 — ``true-rebind-to-new`` breaks the binding where the condition
    collapses, ``open-rebind-to-new`` where it does not, and
    ``fixed-sym-binding`` breaks it BRANCH-FREE (on both sides at once) by
    keying the plain assembly on a bound variable other than the input's.
  * ARG 2 — ``drop-cond-subs`` off the collapse branch, ``true-replaces-cond``
    on it; the latter is a near-miss that gets ARG 1 RIGHT and so is not refuted
    by ARG 1's witness.
  * ARG 3 — ``drop-base-subs`` off the collapse branch, ``true-keeps-base`` on
    it; the latter likewise gets ARG 1 AND ARG 2 right, so neither of their
    witnesses refutes it.

WHY THE COND-COLLAPSE TAG MACHINERY IS NOT A SEPARATE RIVAL FAMILY HERE (carrier
narrowing). The nagini sibling decomposes this into TWO functions — a
constructor deep-model ``build(sym,cond,base)`` returning a tagged result
(EMPTY/BASE/SET) and a ``replace_free_parameter`` free-symbol branch — and hangs
most of its rivals on the tag reduction (``TRUE→base``, ``OPEN→set keyed on
sym``, ``FALSE→empty``). This Lean bundle models only the purely functional core
that the fix actually touches: the free-symbol substitution's STRUCTURAL
preservation (bound variable unchanged; condition and base substituted). The
EMPTY/BASE/SET tag reduction is a property of the ASSEMBLY routine, not of the
substitution branch, and this spec deliberately declines to state it: ``mkSet``
is opaque precisely because the normalisation it performs is not part of the
modeled behavior. So nagini's rivals that attack the tag reduction
(``weak-build-*``, ``weak-rfp-true-to-empty``) have no impl-region counterpart.
The headline pre-patch bug — a collapsed-to-true condition rebinding the bound
variable to ``new`` — IS on this carrier and is the ARG-1 rival below. This is
genuine carrier narrowing, recorded in the accounting block, NOT an effort
omission.

ADVERSARIAL READ of the remaining nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Nagini's fractional-permission frame
    (``Acc(.,1/2)``) and any write-through-input rival do not exist here: Lean is
    referentially transparent, ``cs``/``old``/``new`` are immutable values with no
    heap footprint, no ``mut`` binder over an input, no aliasing. Not fabricated
    (porting map: this class is vacuous on lean).

  * ADMISSIBILITY — PRESENT (``admiss-ground-free-symbol``). The sibling
    self-calls on an F2P-shaped collapsed-to-true input to show the precondition
    admits it; the analogue on this total carrier is the obligation being
    unsatisfiable at an F2P-shaped input, which a positive that DISCHARGES the
    obligation at that concrete input — by evaluation, as ``have``s, before
    closing the frozen ``∀`` obligation verbatim — tests directly. That is the
    case below. Note that the guard is no longer decidable at a literal: it
    compares an expression with ``symExpr cs.sym``, and ``symExpr`` is opaque, so
    the case exhibits an ADMITTED point by a case split on the carrier's decidable
    equality (of two distinct expressions, at least one differs from the image of
    the bound variable) rather than by ``decide``. That is strictly stronger than
    the old ``decide`` form: it proves the admitted set is non-empty for EVERY
    interpretation of the opaque inclusion, not just for one where the tags
    happened to differ. (An earlier revision of this manifest argued the lane was
    subsumed by the positive controls on the grounds that the guard is "trivially
    satisfiable". That reasoning was wrong and is retracted: the positive controls
    only discharge the ``∀`` goal, whose binder the frozen ``intro`` DISCARDS, so
    nothing in the battery evaluated the obligation at any concrete point, and
    PRECOND-TOO-STRONG was untested.)

  * DIVERGENCE / NON-TERMINATION — VACUOUS on this carrier, for a measured
    reason. This bundle sets no ``loom.semantics.termination`` option; it is plain
    total Lean, where the elaborator itself discharges termination. A rival whose
    recursion carries no decreasing measure is therefore not a spec-level
    rejection but a FILE THAT DOES NOT ELABORATE: a self-recursive
    ``implementation_freeSubs`` fails with ``fail to show termination for
    implementation_freeSubs … no parameters suitable for structural recursion``,
    an error about the definition rather than about the equation, so it
    attributes nothing to the spec. The one shape that DOES elaborate,
    ``partial def``, cannot be witnessed: ``partial`` makes the function opaque to
    the kernel, so no refutation can reduce through it. Re-measured with real
    builds during the audit: the ``unfold``-based witness that discriminates
    every shipped rival gets ``Tactic `unfold` failed to unfold
    `implementation_freeSubs```; ``simp [problem_spec_freeSubs]`` gets
    ``unsolved goals``; ``decide +kernel`` gets ``failed to synthesize`` (no
    ``Decidable`` instance over the opaque carriers at all); and the
    hypothesis-only shape (``intro``/``obtain`` with no unfolding) fails with the
    SAME error on the RIVAL as on gold — i.e. it does not discriminate, because
    without unfolding the two impls are indistinguishable. So the rival build
    (the half that must SUCCEED) fails in every shape, which is a
    non-discriminator, not a refutation. (``partial`` is NOT on
    ``pbt_witness``'s banned-token list — that list is ``sorry``/``sorryAx``/
    ``admit``/``native_decide``/``axiom``/``opaque``/``unsafe``/``extern``/
    ``implemented_by`` — and ``variant_scope`` admits the ``partial`` variant with
    no problems, so the exclusion rests solely on the unwitnessability measured
    above, not on a token ban.) So there is no shippable diverging rival here: the
    class is vacuous, not a known hole.

  * UNGROUNDED-ORACLE ECHO — N/A, and this needs re-arguing now that the spec is
    a single equation to an opaque application, because that is the shape an
    echo would also have. It is not an echo, for two reasons. (1) ``mkSet`` is
    not an answer key: it is the REAL assembly routine the modeled code ends in,
    an A-reference validated against the actual callee by G-CONF in-process, not
    a name minted to hold the expected output. There is no ``freeSubsOracle``
    here whose value the spec asserts. (2) The discriminating content lives
    entirely in the ARGUMENTS, each of which is grounded in the INPUT carriers:
    ``cs.sym`` is a projection of the input, and ``subsCond``/``subsSet`` are the
    unchanged substitution routine applied to the input's own components. An
    echo is refutation-proof because a rival can satisfy it by calling the same
    oracle; here a rival must reproduce all three argument terms, and the seven
    rivals below each fail to, which is what the witnesses demonstrate at
    concrete points.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``rfl`` is tuned to the frozen impl's
form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS the spec at one concrete input. Each was checked (two real
``lake env lean`` builds) to ELABORATE against its rival and to FAIL against the
frozen solution (so it discriminates rather than asserting a tautology).

Because ``mkSet``/``mkMemberSet``/``subsCond``/``subsSet``/``isTrue`` are opaque,
each witness is CONDITIONED on the carrier with weak, jointly-satisfiable
hypotheses about DISTINCT opaque terms (never two hypotheses about the SAME term —
that would be ``witness-inconsistent``). Two kinds of hypothesis appear, and the
second is forced by the assembly routine being opaque:

  * a BRANCH SELECTOR — ``isTrue (subsCond …) = true`` / ``= false`` — choosing
    the side of the collapse test the rival mishandles; and
  * an OBJECT-LEVEL DISTINCTNESS hypothesis: the set the RIVAL assembles differs
    from the set the SPEC names, at that one concrete point. This is unavoidable
    and it is also the honest statement of the finding. ``mkSet`` normalises, so
    it is NOT known injective — assuming injectivity would be assuming something
    false of the real routine — and therefore "the arguments differ" does not by
    itself entail "the results differ". What the F2P regression asserts is
    precisely the object-level fact: the set the pre-patch code assembles is not
    the set the patched code assembles at that input. Measured on the testbed at
    the two F2P points, so the hypothesis is not a convenient assumption: the
    pre-patch expression returns ``EmptySet`` where gold returns
    ``Interval(-oo, 0)``, and ``ConditionSet(1/3, Contains(1/3, img), img)`` where
    gold returns the bare ``img`` (``.dummy_eq`` False). The witness assumes
    exactly that, at one named point, and nothing more; the two applications it
    names are DISTINCT terms, so the gate's consistency probe cannot derive
    ``False`` from the pair.

The witness FAILS on gold for a structural reason: against the frozen impl the
two applications in the goal are the SAME term, so no distinctness hypothesis
about a different pair of arguments can close it — which is the discrimination
the two-build check measures.

WHY SPEC-TOO-WEAK IS BOUNDED HERE (machine-checked, and the reason the rival set
above is complete rather than merely plausible). The spec is a single equation
naming the result outright, so it is a TOTAL FUNCTIONAL specification: it has
EXACTLY one satisfier at each input. Both halves were proven with the real
verifier in an audit scratch file (not shippable as a case — ``variant_scope``
rightly forbids a variant from adding a theorem):

    theorem spec_unique (cs old new) (r1 r2)
        (h1 : problem_spec_freeSubs cs old new r1)
        (h2 : problem_spec_freeSubs cs old new r2) : r1 = r2
      -- `unfold problem_spec_freeSubs at h1 h2; exact h1.trans h2.symm`

    theorem verifier_pins_impl_on_guarded_domain (f)
        (hf : ∀ cs old new, old ≠ symExpr cs.sym →
                problem_spec_freeSubs cs old new (f cs old new)) :
        ∀ cs old new, old ≠ symExpr cs.sym →
          f cs old new = implementation_freeSubs cs old new

The second says ANY implementation that discharges the frozen obligation is
pointwise equal to the frozen one on the whole guarded domain. So no wrong impl
can verify — SPEC-TOO-WEAK is impossible on this spec by construction, and the
rivals above are confirming instances of that, not samples from an open space.
The residual risk on such a spec is NOT weakness but the DOMAIN question the
carriers answer: a term that is well-typed here but UNDEFINED on the modeled
side, which a functional spec does not exclude because such a term can be
computed and DISCARDED by an implementation whose returned value is still
correct. That risk is what "WHY THE BINDING POSITION HAS ITS OWN CARRIER", "WHY
AN ASSEMBLED SET IS ITS OWN CARRIER", the OUT-OF-DOMAIN measurements and "WHAT
THE CONDITION AND BASE-SET CARRIERS DENOTE" above address, and it is the axis on
which this spec has been strengthened twice — first at the assembly's INPUT
position (a general expression where a bound variable belongs) and then at its
OUTPUT (an assembled set handed back to a consumer). The
SPEC-TOO-STRONG direction is what the positives cover; hence four of them,
including one whose control flow (``pos-branch-on-collapse``) is not
definitionally the frozen impl and one (``pos-build-then-assemble``) that binds
the components as a record first.

AXIOM lane: EMPTY. The changed behavior is modeled DEEPLY in the frozen spec
(the unchanged substitution routine, modeled as ``subsCond``/``subsSet``, and the
unchanged assembly routine, modeled as ``mkSet``, whose soundness is G-CONF's /
G-AX's job, not this gate's), with no consumed axiom. ``AXIOM_TESTS`` is
therefore empty.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-19495"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchor (unique inside Solution.lean; verified at load) ----------
# The whole impl def is the load-bearing region; every rival reshape and every
# positive-control reshape lands ENTIRELY inside `-- impl-start`/`-- impl-end`.
# The frozen `theorem correct_freeSubs` STATEMENT and its `rfl` proof body are
# left untouched by most cases: the definitional positive controls still close
# under it (verified with real builds), and the reject rivals are judged by their
# witness, not by whether the frozen `rfl` happens to break.
_IMPL = (
    "def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do\n"
    "  let cond' := subsCond cs.cond old new\n"
    "  let base' := subsSet cs.base old new\n"
    "  return mkSet cs.sym cond' base'"
)


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec + proof intact)."""
    return _swap(_BASE, _IMPL, new_impl)


# The frozen proof's TACTIC BODY (everything after `:= by`). `variant_scope`
# requires the `theorem correct_freeSubs` STATEMENT to stay byte-identical but
# lets the tactic body differ, since a variant legitimately RE-PROVES the same
# obligation. Two cases below need that: the admissibility positive (which
# discharges the obligation at a concrete input as a `have` before closing the
# frozen goal verbatim) and the branch-shaped positive (whose impl is NOT
# definitionally the frozen one, so a case split is required).
_PROOF_BODY = "  intro cs old new _\n  rfl"


def _with_proof(new_body: str, impl: str | None = None) -> str:
    """Solution.lean with the proof TACTIC BODY (and optionally the impl)
    replaced; the `theorem correct_freeSubs` statement stays byte-identical."""
    src = _BASE if impl is None else _with_impl(impl)
    return _swap(src, _PROOF_BODY, new_body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-drop-scaffold",
        "kind": "soundness",
        "expect": "verify",
        # Functional reshape: drop the `Id.run do` scaffold and the local
        # `let`s, assembling the set directly. Definitionally identical on every
        # input, so the frozen `rfl` still closes it. Verified with a real build.
        "module": _with_impl(
            "def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet :=\n"
            "  mkSet cs.sym (subsCond cs.cond old new) (subsSet cs.base old new)"
        ),
        "rationale": "correct reshape of the mutable-do builder into a direct assembly; "
                     "it computes the same set on every input, so it satisfies "
                     "`result = mkSet cs.sym (subsCond cs.cond old new) (subsSet cs.base "
                     "old new)` — else SPEC-TOO-STRONG. The frozen `rfl` closes it "
                     "unchanged; no new axiom/lemma, no assumption token.",
    },
    {
        "id": "pos-let-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different CORRECT reshape: SAME `Id.run do` scaffold, the
        # two local `let`s computed in the opposite order (base before cond).
        # The assembly receives the same three arguments, so the equation holds
        # and the frozen proof body closes unchanged.
        "module": _with_impl(
            "def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do\n"
            "  let base' := subsSet cs.base old new\n"
            "  let cond' := subsCond cs.cond old new\n"
            "  return mkSet cs.sym cond' base'"
        ),
        "rationale": "structurally different CORRECT reshape: the two local "
                     "substitutions computed in the opposite order; the assembly gets "
                     "the same three arguments, so the equation holds. A faithful "
                     "reshape MUST verify, else SPEC-TOO-STRONG. The frozen `rfl` still "
                     "closes it; no new axiom/lemma.",
    },
    {
        "id": "pos-build-then-assemble",
        "kind": "soundness",
        "expect": "verify",
        # THE DOMAIN-BOUNDARY POSITIVE. It binds the three components as a
        # `CondSet` record and then assembles that record's fields — which is
        # exactly what the modeled routine does, and is DEFINED, because the
        # components are read off a value known to be of the three-part shape.
        # It must be distinguished from the shape that reads components back out
        # of an ASSEMBLED set, which is undefined on the modeled side and is a
        # TYPE ERROR here (see the OUT-OF-DOMAIN entry in the docstring). This
        # case is the control proving the carrier split rejects only the latter:
        # if it did not verify, the split would be over-tight and the spec
        # SPEC-TOO-STRONG against the real routine's own control flow.
        "module": _with_impl(
            "def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do\n"
            "  let built : CondSet :=\n"
            "    { sym := cs.sym, cond := subsCond cs.cond old new,\n"
            "      base := subsSet cs.base old new }\n"
            "  return mkSet built.sym built.cond built.base"
        ),
        "rationale": "CORRECT reshape that BINDS the three components as a record before "
                     "assembling them, the way the modeled routine does. Definitionally "
                     "the frozen impl (record projection on a literal reduces), so the "
                     "frozen `rfl` closes it. It is the soundness control for the "
                     "output-carrier split: components read off a value KNOWN to be of "
                     "the three-part shape are defined and must be allowed, while "
                     "components read off an assembled result are undefined and are a "
                     "type error. If this were rejected the split would be over-tight => "
                     "SPEC-TOO-STRONG. No new axiom/lemma, no assumption token.",
    },
    {
        "id": "pos-branch-on-collapse",
        "kind": "soundness",
        "expect": "verify",
        # Correct reshape that is NOT definitionally the frozen impl: it BRANCHES
        # on the collapse test (the same `if isTrue cond'` the pre-patch shape
        # branches on) and assembles the correct set in BOTH branches. This is
        # the reshape that matters for soundness here — the frozen `rfl` does NOT
        # close it (the `ite` blocks it), so it needs the case split. If a
        # faithful impl of this shape could not be proven, the spec would be
        # SPEC-TOO-STRONG against exactly the control flow the real change lives
        # in.
        "module": _with_proof(
            "  intro cs old new _\n"
            "  unfold problem_spec_freeSubs implementation_freeSubs\n"
            "  simp only [Id.run]\n"
            "  split <;> rfl",
            "def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do\n"
            "  let cond' := subsCond cs.cond old new\n"
            "  let base' := subsSet cs.base old new\n"
            "  if isTrue cond' then\n"
            "    return mkSet cs.sym cond' base'\n"
            "  return mkSet cs.sym cond' base'",
        ),
        "rationale": "CORRECT reshape whose control flow matches the modeled branch: it "
                     "tests the collapse condition and assembles the same correct set on "
                     "both sides, so the equation holds at every input. Unlike the other "
                     "positives this is NOT definitionally the frozen impl — the `ite` "
                     "blocks the frozen `rfl` — so it is reproven with a `split`, which "
                     "`variant_scope` permits (statement byte-identical, tactic body "
                     "free). A faithful branch-shaped impl MUST verify, else "
                     "SPEC-TOO-STRONG on exactly the control flow the change lives in. No "
                     "new axiom/lemma, no assumption token.",
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG) — the frozen obligation is a `∀` under
    # the binder hypothesis `old ≠ symExpr cs.sym`. On a total carrier the
    # analogue of a too-strong precondition is the obligation being UNSATISFIABLE
    # at an F2P-shaped concrete input, so this case discharges it there BY
    # EVALUATION, as `have`s, before closing the frozen obligation verbatim. The
    # guard is not decidable at a literal (`symExpr` is opaque), so the admitted
    # point is exhibited by a case split on the carrier's decidable equality:
    # of two distinct expressions, at least one differs from the image of the
    # bound variable, whatever that opaque image is. If the guard excluded every
    # F2P-shaped point, or the spec's own equation were unsatisfiable at one, the
    # `have`s would not elaborate and this case would fail.
    # =====================================================================
    {
        "id": "admiss-ground-free-symbol",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_proof(
            "  -- ADMISSIBILITY at a concrete F2P-shaped point: a set bound at\n"
            "  -- bound-variable tag 0 with condition 1 over base 2, substituting a FREE\n"
            "  -- symbol by the value 4.\n"
            "  -- (1) the binder guard `old ≠ symExpr cs.sym` ADMITS such a point. The\n"
            "  --     guard compares an expression with the INCLUSION of the bound\n"
            "  --     variable, which is opaque, so the admitting expression comes from a\n"
            "  --     case split on the carrier's decidable equality: of the two distinct\n"
            "  --     expressions ⟨3⟩ and ⟨5⟩, at least one differs from that inclusion,\n"
            "  --     whatever it is.\n"
            "  have _pre : ∃ old : Expr,\n"
            "      old ≠ symExpr (({ sym := ⟨0⟩, cond := ⟨1⟩, base := ⟨2⟩ } : CondSet).sym) := by\n"
            "    by_cases h : (⟨3⟩ : Expr) = symExpr ⟨0⟩\n"
            "    · refine ⟨⟨5⟩, ?_⟩\n"
            "      rw [← h]\n"
            "      decide\n"
            "    · exact ⟨⟨3⟩, h⟩\n"
            "  -- (2) at such a point the result is the set assembled from the ORIGINAL\n"
            "  --     bound variable and the two substituted components (evaluated, not\n"
            "  --     assumed);\n"
            "  have _shape : implementation_freeSubs ⟨⟨0⟩, ⟨1⟩, ⟨2⟩⟩ ⟨3⟩ ⟨4⟩\n"
            "      = mkSet (⟨0⟩ : SymE) (subsCond ⟨1⟩ ⟨3⟩ ⟨4⟩) (subsSet ⟨2⟩ ⟨3⟩ ⟨4⟩) := rfl\n"
            "  -- (3) the binding position is a REAL choice, so (2) is not satisfied by\n"
            "  --     accident: the bound-variable carrier has at least two distinct\n"
            "  --     inhabitants and ⟨0⟩ names one of them;\n"
            "  have _sym_choice : (⟨0⟩ : SymE) ≠ (⟨5⟩ : SymE) := by decide\n"
            "  -- (4) the FULL obligation holds at a concrete ADMITTED point.\n"
            "  have _ground : ∃ old : Expr, old ≠ symExpr (⟨0⟩ : SymE) ∧\n"
            "      problem_spec_freeSubs ⟨⟨0⟩, ⟨1⟩, ⟨2⟩⟩ old ⟨4⟩\n"
            "        (implementation_freeSubs ⟨⟨0⟩, ⟨1⟩, ⟨2⟩⟩ old ⟨4⟩) := by\n"
            "    by_cases h : (⟨3⟩ : Expr) = symExpr ⟨0⟩\n"
            "    · refine ⟨⟨5⟩, ?_, rfl⟩\n"
            "      rw [← h]\n"
            "      decide\n"
            "    · exact ⟨⟨3⟩, h, rfl⟩\n"
            "  intro cs old new _\n"
            "  rfl"
        ),
        "rationale": "ADMISSIBILITY / PRECOND-TOO-STRONG. The frozen obligation carries the "
                     "binder hypothesis `old ≠ symExpr cs.sym`; this case shows it is "
                     "satisfiable AT AN F2P-SHAPED INPUT and that the obligation is "
                     "non-vacuous there, by DISCHARGING it at a concrete admitted point by "
                     "evaluation as `have`s, then closing the frozen `∀` goal verbatim. "
                     "Because the guard now compares against the OPAQUE inclusion of the "
                     "bound variable, the admitted point is produced by a case split on "
                     "decidable equality rather than by `decide` — which proves the "
                     "admitted set non-empty under EVERY interpretation of that inclusion, "
                     "not just under one. The `_shape` and `_sym_choice` `have`s are the "
                     "load-bearing pair: the result at the point is the assembly on bound "
                     "variable ⟨0⟩ — the ORIGINAL — and the binding position is a genuine "
                     "choice (the carrier has another inhabitant ⟨5⟩), so the concrete "
                     "post-image is non-degenerate rather than trivially satisfied. If the "
                     "guard excluded every free-symbol input, or the equation were "
                     "unsatisfiable at one, no `have` would elaborate and this case would "
                     "REJECT => PRECOND-TOO-STRONG. Statement byte-identical; the tactic "
                     "body is extended, which `variant_scope` permits; no new axiom/lemma, "
                     "no assumption token.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing F2P test (test_subs_CondSet).
    # The witnesses attack the three independent argument positions and vary the
    # inputs `cs`/`old`/`new` across seven disjoint points.
    # =====================================================================
    {
        "id": "true-rebind-to-new",
        "kind": "uniqueness",
        "expect": "reject",
        # ARG 1 attack — THE HEADLINE PRE-PATCH BUG. When the substituted
        # condition collapses to trivially-true, assemble the set on the
        # replacement VALUE `new` (via the fused membership assembly, which is
        # the pre-patch's own `ConditionSet(new, Contains(new, base), base)`)
        # instead of on the input's bound variable. Correct whenever the
        # condition does NOT collapse; wrong exactly on the collapse sub-domain.
        "module": _with_impl(
            "def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do\n"
            "  let cond' := subsCond cs.cond old new\n"
            "  let base' := subsSet cs.base old new\n"
            "  if isTrue cond' then\n"
            "    return mkMemberSet new base'\n"
            "  return mkSet cs.sym cond' base'"
        ),
        "refinement": "this is the pre-patch shape verbatim: on a collapsed-to-true "
                      "condition it rebuilds the set keyed on the replacement value `new` "
                      "under a membership restriction, instead of assembling on the "
                      "original bound variable. Measured at the two F2P points on the "
                      "testbed: that expression returns the empty set where gold returns "
                      "the substituted base interval, and returns a membership-restricted "
                      "set where gold returns the bare image set (`.dummy_eq` False). The "
                      "added regression assertions reject both => it would NOT resolve.",
        "rationale": "REJECT from ARG 1 (`cs.sym`): on the collapse sub-domain the rival "
                     "assembles on `new` where the spec assembles on `cs.sym`. Refuted at "
                     "a point where the condition collapses (branch selector `isTrue "
                     "(subsCond …) = true`, firing the pre-patch branch) under the "
                     "object-level hypothesis that the set the rival assembles there is "
                     "not the set the spec names — which is exactly what the F2P "
                     "regression asserts about that input, and what the testbed "
                     "measurement above confirms. If it verified => SPEC-TOO-WEAK (the "
                     "binding-preservation commitment hollow). Inputs at tags cs=(0,1,2), "
                     "old=3, new=4.",
        "witness": (
            "example (h1 : isTrue (subsCond ⟨1⟩ ⟨3⟩ ⟨4⟩) = true)\n"
            "    (h2 : mkMemberSet ⟨4⟩ (subsSet ⟨2⟩ ⟨3⟩ ⟨4⟩)\n"
            "            ≠ mkSet ⟨0⟩ (subsCond ⟨1⟩ ⟨3⟩ ⟨4⟩) (subsSet ⟨2⟩ ⟨3⟩ ⟨4⟩)) :\n"
            "    ¬ problem_spec_freeSubs ⟨⟨0⟩, ⟨1⟩, ⟨2⟩⟩ ⟨3⟩ ⟨4⟩\n"
            "        (implementation_freeSubs ⟨⟨0⟩, ⟨1⟩, ⟨2⟩⟩ ⟨3⟩ ⟨4⟩) := by\n"
            "  unfold problem_spec_freeSubs implementation_freeSubs\n"
            "  simp only [Id.run, h1, if_true]\n"
            "  exact h2\n"
        ),
    },
    {
        "id": "drop-cond-subs",
        "kind": "uniqueness",
        "expect": "reject",
        # ARG 2 attack: assemble from the condition UNCHANGED (skip applying the
        # substitution to it) while still substituting the base. Correct only
        # where the substitution is a no-op on the condition; wrong wherever the
        # free symbol actually occurs in the condition.
        "module": _with_impl(
            "def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do\n"
            "  let base' := subsSet cs.base old new\n"
            "  return mkSet cs.sym cs.cond base'"
        ),
        "refinement": "a faithful real patch that left the condition un-substituted "
                      "would leave the free symbol standing in the returned condition. "
                      "The F2P asserts the substituted set's condition is the input "
                      "condition with the replacement applied (e.g. `y < 1` becomes the "
                      "condition after `y ↦ new`); an un-substituted condition still "
                      "mentioning the old symbol is a different set => it would NOT "
                      "resolve.",
        "rationale": "REJECT from ARG 2 (`subsCond cs.cond old new`): the rival assembles "
                     "from the un-substituted `cs.cond`. Refuted under the object-level "
                     "hypothesis that assembling from the un-substituted condition gives "
                     "a different set from assembling from the substituted one at that "
                     "point — the substitution moves the condition observably there. If "
                     "it verified => SPEC-TOO-WEAK. Inputs at tags cs=(5,6,7), old=8, "
                     "new=9 — distinct from the other rivals.",
        "witness": (
            "example (h : mkSet ⟨5⟩ ⟨6⟩ (subsSet ⟨7⟩ ⟨8⟩ ⟨9⟩)\n"
            "            ≠ mkSet ⟨5⟩ (subsCond ⟨6⟩ ⟨8⟩ ⟨9⟩) (subsSet ⟨7⟩ ⟨8⟩ ⟨9⟩)) :\n"
            "    ¬ problem_spec_freeSubs ⟨⟨5⟩, ⟨6⟩, ⟨7⟩⟩ ⟨8⟩ ⟨9⟩\n"
            "        (implementation_freeSubs ⟨⟨5⟩, ⟨6⟩, ⟨7⟩⟩ ⟨8⟩ ⟨9⟩) := by\n"
            "  unfold problem_spec_freeSubs implementation_freeSubs\n"
            "  simp only [Id.run]\n"
            "  exact h\n"
        ),
    },
    {
        "id": "drop-base-subs",
        "kind": "uniqueness",
        "expect": "reject",
        # ARG 3 attack: assemble from the base set UNCHANGED (skip applying the
        # substitution to it) while still substituting the condition. Correct
        # only where the substitution is a no-op on the base; wrong wherever the
        # free symbol actually occurs in the base set.
        "module": _with_impl(
            "def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do\n"
            "  let cond' := subsCond cs.cond old new\n"
            "  return mkSet cs.sym cond' cs.base"
        ),
        "refinement": "a faithful real patch that left the base set un-substituted would "
                      "leave the free symbol standing in the returned base. The F2P "
                      "asserts the substituted set's base is the input base with the "
                      "replacement applied (the reported bug: substituting into the base "
                      "must actually reach the base set); an un-substituted base is a "
                      "different set => it would NOT resolve.",
        "rationale": "REJECT from ARG 3 (`subsSet cs.base old new`): the rival assembles "
                     "from the un-substituted `cs.base`. Refuted under the object-level "
                     "hypothesis that assembling from the un-substituted base gives a "
                     "different set from assembling from the substituted one at that "
                     "point — the substitution moves the base observably there. If it "
                     "verified => SPEC-TOO-WEAK. Inputs at tags cs=(10,11,12), old=13, "
                     "new=14 — distinct from the other rivals.",
        "witness": (
            "example (h : mkSet ⟨10⟩ (subsCond ⟨11⟩ ⟨13⟩ ⟨14⟩) ⟨12⟩\n"
            "            ≠ mkSet ⟨10⟩ (subsCond ⟨11⟩ ⟨13⟩ ⟨14⟩) (subsSet ⟨12⟩ ⟨13⟩ ⟨14⟩)) :\n"
            "    ¬ problem_spec_freeSubs ⟨⟨10⟩, ⟨11⟩, ⟨12⟩⟩ ⟨13⟩ ⟨14⟩\n"
            "        (implementation_freeSubs ⟨⟨10⟩, ⟨11⟩, ⟨12⟩⟩ ⟨13⟩ ⟨14⟩) := by\n"
            "  unfold problem_spec_freeSubs implementation_freeSubs\n"
            "  simp only [Id.run]\n"
            "  exact h\n"
        ),
    },
    {
        "id": "open-rebind-to-new",
        "kind": "uniqueness",
        "expect": "reject",
        # ARG 1 attack on the OTHER sub-domain. `true-rebind-to-new` breaks the
        # binding only where the condition COLLAPSES; this one preserves it there
        # and breaks it on the complementary (non-collapse / "open") branch. The
        # two together pin ARG 1 over the whole domain of the collapse test,
        # rather than on one side of it. This is the lean counterpart of the
        # sibling's open-branch keyed-on-new rival, which the accounting block
        # previously recorded as having no counterpart on this carrier. With the
        # binding position typed, the fused membership assembly is the only way an
        # implementation can key a set on the substituted value at all, so this
        # rival necessarily has that shape.
        "module": _with_impl(
            "def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do\n"
            "  let cond' := subsCond cs.cond old new\n"
            "  let base' := subsSet cs.base old new\n"
            "  if isTrue cond' then\n"
            "    return mkSet cs.sym cond' base'\n"
            "  return mkMemberSet new base'"
        ),
        "refinement": "a faithful real patch that rebuilt the set on the replacement value "
                      "whenever the substituted condition did NOT collapse would produce the "
                      "wrong bound variable for every ordinary free-symbol substitution — "
                      "the common case. The regression assertions check that substituting a "
                      "free symbol into such a set yields a set still bound by the ORIGINAL "
                      "variable with the substituted condition; a membership-restricted set "
                      "keyed on the replacement value is a different set => it would NOT "
                      "resolve.",
        "rationale": "REJECT from ARG 1 (`cs.sym`) on the NON-collapse sub-domain: there "
                     "the rival keys the set on `new`. Refuted at a point where the "
                     "condition does NOT collapse (branch selector `isTrue (subsCond …) = "
                     "false`, selecting the other branch), so it is a genuinely different "
                     "sub-domain from `true-rebind-to-new` and not a respelling of it, "
                     "under the object-level hypothesis that the two assembled sets differ "
                     "there. If it verified => SPEC-TOO-WEAK. Inputs at tags cs=(20,21,22), "
                     "old=23, new=24 — disjoint from every other rival.",
        "witness": (
            "example (h1 : isTrue (subsCond ⟨21⟩ ⟨23⟩ ⟨24⟩) = false)\n"
            "    (h2 : mkMemberSet ⟨24⟩ (subsSet ⟨22⟩ ⟨23⟩ ⟨24⟩)\n"
            "            ≠ mkSet ⟨20⟩ (subsCond ⟨21⟩ ⟨23⟩ ⟨24⟩) (subsSet ⟨22⟩ ⟨23⟩ ⟨24⟩)) :\n"
            "    ¬ problem_spec_freeSubs ⟨⟨20⟩, ⟨21⟩, ⟨22⟩⟩ ⟨23⟩ ⟨24⟩\n"
            "        (implementation_freeSubs ⟨⟨20⟩, ⟨21⟩, ⟨22⟩⟩ ⟨23⟩ ⟨24⟩) := by\n"
            "  unfold problem_spec_freeSubs implementation_freeSubs\n"
            "  simp only [Id.run, h1, Bool.false_eq_true, if_false]\n"
            "  exact h2\n"
        ),
    },
    {
        "id": "fixed-sym-binding",
        "kind": "uniqueness",
        "expect": "reject",
        # ARG 1 attack, BRANCH-FREE and through the PLAIN assembly. The other two
        # ARG-1 rivals both key the result on the substituted VALUE `new`, which
        # forces the fused membership assembly (`new` is an `Expr`); this one
        # keys it on a DIFFERENT BOUND VARIABLE, which the plain assembly takes
        # directly, so it reaches the binding position by a route neither of them
        # uses and is correct only on the sub-domain where the input's bound
        # variable happens to be that one. It is what makes ARG 1's coverage the
        # whole position rather than "the two spellings that need the fused
        # routine": both other ARG-1 rivals are branch-conditioned and both
        # replace the ASSEMBLY ROUTINE as well as its first argument, so neither
        # tests that the plain assembly's first argument is pinned to `cs.sym`.
        "module": _with_impl(
            "def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do\n"
            "  let cond' := subsCond cs.cond old new\n"
            "  let base' := subsSet cs.base old new\n"
            "  return mkSet ⟨0⟩ cond' base'"
        ),
        "refinement": "a faithful real patch that assembled the substituted set on a bound "
                      "variable of its own choosing rather than on the input's would break "
                      "every caller that reads the result's bound variable, on EVERY input "
                      "(not just on the collapse corner): the regression assertions check "
                      "that substituting a free symbol yields a set still bound by the "
                      "ORIGINAL variable, and one bound by a different variable is a "
                      "different set (the `.dummy_eq` comparison is what observes this) => "
                      "it would NOT resolve.",
        "rationale": "REJECT from ARG 1 (`cs.sym`) BRANCH-FREE and through the PLAIN "
                     "assembly: the rival keeps the assembly routine and every other "
                     "argument the spec names, and changes ONLY its first argument to a "
                     "fixed bound variable. That is a different route into the binding "
                     "position from the other two ARG-1 rivals, which both key on the "
                     "substituted value and therefore must go through the fused membership "
                     "assembly — so neither of them establishes that the plain assembly's "
                     "first argument is pinned. Refuted under the single object-level "
                     "hypothesis that assembling on ⟨0⟩ differs from assembling on the "
                     "input's ⟨30⟩ at that point (one hypothesis, one opaque pair, so the "
                     "consistency probe cannot derive `False`). No branch selector is "
                     "needed, because the rival is wrong on both sides of the collapse "
                     "test. If it verified => SPEC-TOO-WEAK. Inputs at tags cs=(30,31,32), "
                     "old=33, new=34 — disjoint from every other rival.",
        "witness": (
            "example (h : mkSet ⟨0⟩ (subsCond ⟨31⟩ ⟨33⟩ ⟨34⟩) (subsSet ⟨32⟩ ⟨33⟩ ⟨34⟩)\n"
            "            ≠ mkSet ⟨30⟩ (subsCond ⟨31⟩ ⟨33⟩ ⟨34⟩) (subsSet ⟨32⟩ ⟨33⟩ ⟨34⟩)) :\n"
            "    ¬ problem_spec_freeSubs ⟨⟨30⟩, ⟨31⟩, ⟨32⟩⟩ ⟨33⟩ ⟨34⟩\n"
            "        (implementation_freeSubs ⟨⟨30⟩, ⟨31⟩, ⟨32⟩⟩ ⟨33⟩ ⟨34⟩) := by\n"
            "  unfold problem_spec_freeSubs implementation_freeSubs\n"
            "  simp only [Id.run]\n"
            "  exact h\n"
        ),
    },
    {
        "id": "true-replaces-cond",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS on the collapse sub-domain, aimed at ARG 2 where the other
        # ARG-2 rival is silent. It keeps the bound variable (so ARG 1 is right
        # and `true-rebind-to-new`'s witness would NOT refute it) but on collapse
        # it assembles under a freshly-built membership restriction instead of the
        # substituted condition — i.e. the pre-patch shape with only its
        # bound-variable half repaired.
        "module": _with_impl(
            "def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do\n"
            "  let cond' := subsCond cs.cond old new\n"
            "  let base' := subsSet cs.base old new\n"
            "  if isTrue cond' then\n"
            "    return mkMemberSet (symExpr cs.sym) base'\n"
            "  return mkSet cs.sym cond' base'"
        ),
        "refinement": "this is the pre-patch special case with only its bound-variable half "
                      "repaired: on a collapsed-to-true condition it keeps the original "
                      "bound variable but still replaces the condition with a "
                      "freshly-minted membership restriction instead of carrying the "
                      "substituted condition through. The regression assertions require the "
                      "collapsed case to reduce to the (substitution-applied) base domain, "
                      "not to a set re-restricted by a membership predicate — a restricted "
                      "object is not the base domain => it would NOT resolve.",
        "rationale": "REJECT from ARG 2 (`subsCond cs.cond old new`) on the COLLAPSE "
                     "sub-domain, which the other ARG-2 rival never reaches: there the "
                     "rival assembles under a membership restriction on the bound variable "
                     "instead of the substituted condition. Refuted under two hypotheses "
                     "about DISTINCT opaque terms (the branch selector, and the "
                     "distinctness of the two assembled sets), so they are jointly "
                     "satisfiable and the consistency probe cannot derive `False`. Note "
                     "this rival gets ARG 1 RIGHT, so `true-rebind-to-new`'s witness does "
                     "not refute it — it is a distinct near-miss. If it verified => "
                     "SPEC-TOO-WEAK. Inputs at tags cs=(15,16,17), old=18, new=19 "
                     "— disjoint from every other rival.",
        "witness": (
            "example (h1 : isTrue (subsCond ⟨16⟩ ⟨18⟩ ⟨19⟩) = true)\n"
            "    (h2 : mkMemberSet (symExpr ⟨15⟩) (subsSet ⟨17⟩ ⟨18⟩ ⟨19⟩)\n"
            "            ≠ mkSet ⟨15⟩ (subsCond ⟨16⟩ ⟨18⟩ ⟨19⟩) (subsSet ⟨17⟩ ⟨18⟩ ⟨19⟩)) :\n"
            "    ¬ problem_spec_freeSubs ⟨⟨15⟩, ⟨16⟩, ⟨17⟩⟩ ⟨18⟩ ⟨19⟩\n"
            "        (implementation_freeSubs ⟨⟨15⟩, ⟨16⟩, ⟨17⟩⟩ ⟨18⟩ ⟨19⟩) := by\n"
            "  unfold problem_spec_freeSubs implementation_freeSubs\n"
            "  simp only [Id.run, h1, if_true]\n"
            "  exact h2\n"
        ),
    },
    {
        "id": "true-keeps-base",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS on the collapse sub-domain aimed at ARG 3, the sub-domain the
        # other ARG-3 rival never reaches. `drop-base-subs` is branch-free, so it
        # drops the base substitution EVERYWHERE; this one drops it only where
        # the condition collapses and is otherwise correct. It gets ARG 1 *and*
        # ARG 2 right, so no other witness in the battery refutes it — the
        # collapse branch is exactly where the modeled change lives, and it is
        # the sub-domain on which a base regression is easiest to miss.
        "module": _with_impl(
            "def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do\n"
            "  let cond' := subsCond cs.cond old new\n"
            "  let base' := subsSet cs.base old new\n"
            "  if isTrue cond' then\n"
            "    return mkSet cs.sym cond' cs.base\n"
            "  return mkSet cs.sym cond' base'"
        ),
        "refinement": "a faithful real patch that carried the base set through "
                      "un-substituted ONLY when the substituted condition collapsed to "
                      "trivially-true would leave the free symbol standing in the returned "
                      "base on exactly the corner case the change is about. The regression "
                      "assertions require the collapsed case to reduce to the "
                      "REPLACEMENT-APPLIED base domain; a base still mentioning the old "
                      "symbol is a different set => it would NOT resolve. It is a strictly "
                      "harder near-miss than the branch-free ARG-3 rival, which is wrong "
                      "on every input and so is caught by any base-moving point.",
        "rationale": "REJECT from ARG 3 (`subsSet cs.base old new`) on the COLLAPSE "
                     "sub-domain, which the other ARG-3 rival never reaches: there the "
                     "rival assembles from the un-substituted `cs.base`. Refuted under two "
                     "hypotheses about DISTINCT opaque terms (the branch selector, and the "
                     "distinctness of the two assembled sets), so they are jointly "
                     "satisfiable and the consistency probe cannot derive `False`. Note "
                     "this rival gets ARG 1 and ARG 2 right, so no other witness in the "
                     "battery refutes it — it is a distinct near-miss, not a respelling. "
                     "If it verified => SPEC-TOO-WEAK. Inputs at tags cs=(25,26,27), "
                     "old=28, new=29 — disjoint from every other rival.",
        "witness": (
            "example (h1 : isTrue (subsCond ⟨26⟩ ⟨28⟩ ⟨29⟩) = true)\n"
            "    (h2 : mkSet ⟨25⟩ (subsCond ⟨26⟩ ⟨28⟩ ⟨29⟩) ⟨27⟩\n"
            "            ≠ mkSet ⟨25⟩ (subsCond ⟨26⟩ ⟨28⟩ ⟨29⟩) (subsSet ⟨27⟩ ⟨28⟩ ⟨29⟩)) :\n"
            "    ¬ problem_spec_freeSubs ⟨⟨25⟩, ⟨26⟩, ⟨27⟩⟩ ⟨28⟩ ⟨29⟩\n"
            "        (implementation_freeSubs ⟨⟨25⟩, ⟨26⟩, ⟨27⟩⟩ ⟨28⟩ ⟨29⟩) := by\n"
            "  unfold problem_spec_freeSubs implementation_freeSubs\n"
            "  simp only [Id.run, h1, if_true]\n"
            "  exact h2\n"
        ),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 18 SPEC cases (2 soundness
# positives, 1 admissibility, 15 uniqueness rivals) plus a 1-case AXIOM lane.
# (An earlier revision of this block said "7 SPEC cases (… 5 uniqueness rivals)"
# and claimed every sibling case was recorded; both were wrong — 9 rivals were
# unlisted, 5 of them constructor rivals and 4 of them the divergence family —
# and the count is corrected here with every one of the 18 enumerated below.)
# It contracts TWO functions — `build(sym,cond,base) -> Result0` (a constructor
# deep-model returning an EMPTY/BASE/SET tag) and `replace_free_parameter` (the
# patched free-symbol branch) — and hangs most rivals on the constructor's tag
# reduction. This Lean bundle models only the purely functional core the fix
# touches: `freeSubs(cs, old, new)`, the free-symbol substitution's STRUCTURAL
# preservation (bound variable unchanged; condition and base substituted), with
# the assembly routine itself left OPAQUE. Every sibling case is recorded below.
#
#   sibling case                     -> here
#   ---------------------------------------------------------------------
#   pos-build-reorder                -> pos-let-reorder            RE-EXPRESSED
#   pos-rfp-inline                   -> pos-drop-scaffold          RE-EXPRESSED
#   admiss-rfp-true                  -> admiss-ground-free-symbol  RE-EXPRESSED
#   weak-rfp-true-keyed-on-new       -> true-rebind-to-new         RE-EXPRESSED
#   weak-rfp-open-keyed-on-new       -> open-rebind-to-new         RE-EXPRESSED
#   weak-rfp-true-to-empty           -> (none)                     NOT MODELED (tag)
#   weak-build-open-wrong-sym        -> fixed-sym-binding          RE-EXPRESSED
#   weak-build-true-wrong-base       -> true-keeps-base            RE-EXPRESSED
#   -- the divergence family (4), VACUOUS on this carrier; see the DIVERGENCE
#      entry in the docstring for the re-measured builds --
#   weak-rfp-never-delivers-selfcall -> (none)   VACUOUS (no termination option)
#   weak-rfp-never-delivers-loop     -> (none)   VACUOUS (no termination option)
#   weak-rfp-measure-not-kept        -> (none)   VACUOUS (no termination option)
#   weak-rfp-partial-then-never-delivers -> (none) VACUOUS (as above)
#   weak-build-never-delivers        -> (none)   VACUOUS (as above, in `build`)
#   -- the remaining constructor rivals (5), NOT MODELED (build); each attacks a
#      `build` postcondition over the EMPTY/LISTED/MERGED reduction. Here the
#      assembly routine is the OPAQUE `mkSet` and its result is a bare `AsmSet`
#      with no tag field, no LISTED/MERGED base kinds and no readable
#      components, so there is no impl-region edit that can express any of them --
#   weak-build-drop-empty-base       -> (none)   NOT MODELED (build: BASE_EMPTY)
#   weak-build-listed-ignore-members -> (none)   NOT MODELED (build: BASE_LISTED)
#   weak-build-listed-wrong-sym      -> (none)   NOT MODELED (build: BASE_LISTED)
#   weak-build-merged-keeps-outer-sym  -> (none) NOT MODELED (build: BASE_MERGED)
#   weak-build-merged-keeps-outer-base -> (none) NOT MODELED (build: BASE_MERGED)
#   (added: the ARG-2/ARG-3 substitution-drop rivals drop-cond-subs,
#           drop-base-subs; the collapse-branch ARG-2 near-miss
#           true-replaces-cond; the collapse-branch ARG-3 near-miss
#           true-keeps-base; the branch-shaped correct reshape
#           pos-branch-on-collapse; the domain-boundary correct reshape
#           pos-build-then-assemble)
#   AXIOM_TESTS (1)                  -> (none)                     DROPPED (G-AX)
#
# RE-EXPRESSED (positive controls): the sibling's branch-reorder and
#   inline-instead-of-delegate both carry the ARGUMENT that a structurally
#   different but faithful impl must verify. Here the editable surface is the
#   single assembly call, so that argument is carried by (a) dropping the
#   `Id.run do` scaffold and assembling directly (pos-drop-scaffold) and
#   (b) computing the two local substitutions in the opposite order
#   (pos-let-reorder). Both keep the frozen `rfl` proof and were verified with
#   real builds. `pos-build-then-assemble` and `pos-branch-on-collapse` are
#   ADDITIONS with no sibling counterpart, argued at their case sites.
# RE-EXPRESSED (headline rival): the sibling's `weak-rfp-true-keyed-on-new` IS the
#   pre-patch bug — a collapsed-to-true condition rebuilding the set keyed on the
#   replacement value `new`. On this carrier that is `true-rebind-to-new`
#   (ARG 1: keying the set on `new` rather than assembling on `cs.sym`), refuted
#   by a witness whose branch selector is the condition collapsing
#   (`isTrue (subsCond …) = true`).
# RE-EXPRESSED (admissibility): `admiss-ground-free-symbol`. The sibling asserts
#   the post-image at an F2P-shaped input to show the precondition admits it; here
#   the obligation is discharged AT a concrete F2P-shaped point by evaluation, as
#   `have`s, before the frozen `∀` obligation is closed verbatim. The admitted
#   point is exhibited by a case split on decidable equality (the guard compares
#   against the opaque `symExpr`), and the load-bearing pair of `have`s evaluates
#   the result to the assembly on bound variable ⟨0⟩ and shows the binding
#   position is a real choice, so the concrete post-image is non-degenerate. This
#   is what tests PRECOND-TOO-STRONG on a total carrier: the frozen proof `intro`s
#   and DISCARDS the guard, so without this case nothing in the battery evaluated
#   the obligation anywhere.
# RE-EXPRESSED (open-branch rival): `weak-rfp-open-keyed-on-new` DOES have a
#   counterpart here and is now `open-rebind-to-new`. It is not a tag rival: keying
#   the non-collapse result on `new` is a violation of ARG 1, which this spec
#   states, and it is refuted by a witness whose branch selector is the collapse
#   test being `false`. An earlier revision recorded it as NOT MODELED (tag); that
#   was wrong and is retracted.
# RE-EXPRESSED (the keyed-base clause): `weak-build-true-wrong-base` attacks the
#   sibling clause `cond_after==COND_TRUE => base==base_after` — on a collapse the
#   result's base must be the SUBSTITUTION-APPLIED base. Stripped of the tag
#   machinery, that clause is ARG 3 restricted to the collapse branch, and it IS
#   on this carrier: `true-keeps-base` assembles from the un-substituted base
#   exactly where the condition collapses. It is a genuine near-miss rather than a
#   respelling of `drop-base-subs`, because it gets ARG 1 and ARG 2 right and is
#   correct off the collapse branch, so no other witness in the battery refutes
#   it. An earlier revision recorded it as NOT MODELED (build); that was wrong —
#   the clause survives the carrier narrowing even though the constructor's tag
#   field does not — and is retracted.
# RE-EXPRESSED (the bound-symbol propagation clause): `weak-build-open-wrong-sym`
#   keys the sibling's open-case result on a FIXED wrong constant (0) instead of
#   the bound variable it was passed, attacking `cond==COND_OPEN and
#   base_kind==BASE_PLAIN => sym==sym`. Stripped of the tag machinery, that clause
#   is ARG 1 with the ASSEMBLY ROUTINE held fixed, and it IS on this carrier:
#   `fixed-sym-binding` returns `mkSet ⟨0⟩ cond' base'`, which elaborates (a bound
#   variable is directly constructible and the plain assembly's first position
#   takes one), is REJECTED, and carries a discriminating witness. An earlier
#   revision recorded it as NOT MODELED (build) on the grounds that the binding
#   position could only be reached through the fused membership assembly; that was
#   wrong — measured with real builds during this audit: variant exit 1, witness
#   exit 0 on the rival and 1 on gold, consistency probe non-zero, and the
#   claim-flip inverted (exit 0 on gold, 1 on the rival) — and is retracted. It is
#   a genuine third ARG-1 member rather than a respelling of the two keyed-on-`new`
#   rivals, which are both branch-conditioned and both swap the assembly routine
#   itself, so neither pins the plain assembly's first argument.
# NOT MODELED (the one remaining tag/constructor rival): weak-rfp-true-to-empty
#   attacks the EMPTY/BASE/SET tag reduction the sibling's `build` deep-model
#   produces (open->set keyed on sym, true->base, false->empty). Unlike the
#   keyed-base and bound-symbol clauses above, what it asserts is the EXISTENCE of
#   a distinguished EMPTY result tag: it claims the collapse yields the empty
#   domain rather than the base domain. That is a property of the ASSEMBLY
#   ROUTINE, not of the free-symbol substitution branch this Lean bundle models,
#   and this spec deliberately leaves that routine opaque — the normalisation it
#   performs (which is exactly what turns an assembly into an interval, an image
#   or the empty set) is real, is why the result carrier has no readable
#   components, and is not part of the modeled behavior. There is no impl-region
#   edit that can express "returns the empty tag": the nearest spelling, returning
#   a minted `(⟨0⟩ : AsmSet)` literal on the collapse branch, is out of the
#   modeled vocabulary (a result-carrier literal minted from nothing, denoting no
#   routine call) — measured during this audit, it elaborates and is REJECTED
#   (exit 1), so it attributes nothing the shipped rivals do not already. This is
#   genuine carrier narrowing, NOT an effort omission: all three argument
#   positions the impl CAN influence are each attacked on BOTH sides of the
#   collapse test by a rival with a machine-checked discriminating witness, and
#   ARG 1 additionally by a branch-free rival through the plain assembly.
#
#   The seven reject witnesses probe SEVEN DISJOINT input points — cs=(0,1,2)
#   old=3 new=4; cs=(5,6,7) old=8 new=9; cs=(10,11,12) old=13 new=14;
#   cs=(15,16,17) old=18 new=19; cs=(20,21,22) old=23 new=24; cs=(25,26,27)
#   old=28 new=29; cs=(30,31,32) old=33 new=34 — so all three inputs
#   (cs / old / new) are varied and every argument position is attacked at two or
#   more distinct points on opposite sides of the collapse test. All witnesses
#   CONDITION on the opaque carrier with weak, jointly-satisfiable hypotheses
#   about DISTINCT opaque terms (never two about the same term), never by
#   computing the opaque `mkSet`/`mkMemberSet`/`subsCond`/`subsSet`/`isTrue`.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; the opaque callees here are
# the unchanged substitution routine, modeled at the condition and base-set
# components as `subsCond`/`subsSet`, and the unchanged assembly routine, modeled
# as `mkSet` (with `mkMemberSet` for the fused value-plus-membership assembly the
# pre-patch used, and `symExpr` for the bound-variable inclusion; all validated ==
# the real callee by G-CONF), and the changed behavior is modeled deeply in the
# frozen spec with no consumed axiom, so there is nothing for this gate to probe.
#
# ---------------------------------------------------------------------------
# INDEPENDENT AUDIT RECORD (adversarial re-derivation on the typed-binding spec)
#
# Every claim below was re-run with the real verifier against the CURRENT frozen
# `Solution.lean`, not inherited from the port or from a previous spec revision.
#
# ATTACK A (statement integrity). For all 12 cases the `theorem correct_freeSubs`
#   statement, the whole `-- axioms-start/end` region, the whole
#   `-- pure-start/end` region, the whole `-- post-conditions-start/end` region
#   AND the entire file prefix up to `-- impl-start` (docstring and all comments
#   included) are BYTE-IDENTICAL to the frozen file, compared programmatically.
#   No case reformats or weakens a hypothesis.
#
# ATTACK B (witness discrimination, re-derived). For each of the 7 reject cases:
#   witness-on-rival exit 0, witness-on-gold exit 1, consistency probe exit 1
#   (`unsolved goals ⊢ False` — hypotheses jointly satisfiable, so no witness
#   proves its refutation from a contradiction). The rival variant itself also
#   fails to verify (exit 1). Gold's failure is a `Type mismatch` on the
#   distinctness hypothesis in all 7, never an unknown identifier and never a
#   timeout.
#
# ATTACK B' (FORGERY test — required for all 7, since a `Type mismatch` is not a
#   plain evaluation and it is the shape a hollow witness would also have). Two
#   independent probes, both re-run:
#     - CLAIM FLIP: assert the spec HOLDS at the witness's own point (drop the
#       `¬`), closed by `rfl`. Exit 0 on GOLD and exit 1 on every RIVAL — exactly
#       inverted from the witness, so gold's exit code TRACKS THE CLAIM rather
#       than failing for an unrelated reason. The rival's flip error is a
#       `Tactic `rfl` failed` naming the rival's own returned term, i.e. the
#       flipped claim is false there for a semantic reason.
#     - GOAL REVEAL: replace the final `exact h`/`exact h2` with `exact (0 : Nat)`
#       and read the type Lean prints for the goal on each side. On GOLD the goal
#       is `¬pure (mkSet cs.sym (subsCond …) (subsSet …)) = mkSet cs.sym
#       (subsCond …) (subsSet …)` — the two sides are the SAME term, so the
#       equation HOLDS and the negation is genuinely unprovable; on each RIVAL the
#       left side is that rival's own differing term (`mkMemberSet ⟨4⟩ …`,
#       `mkSet ⟨5⟩ ⟨6⟩ …`, `mkSet ⟨0⟩ …`, etc.). That pair is the refutation
#       content: the witness's hypothesis is about the rival's term, which is why
#       `exact h` type-checks there and cannot on gold.
#
# ATTACK C (is the rival wrong, or just different?). All 7 rivals differ from the
#   frozen impl OBSERVABLY on this carrier: each assembles the set from a
#   different argument triple (or through a different assembly routine) at a
#   concrete tag point — confirmed by the GOAL REVEAL above, which prints each
#   rival's returned term next to gold's and shows them syntactically distinct —
#   and neither assembly carries an axiom, so no rival is definitionally equal to
#   gold and none is merely reshaped.
#
# ATTACK D (SPEC-TOO-WEAK probe). A further 10 NEW wrong impls the battery does
#   not contain were built against the frozen spec in this audit pass; 9 were
#   REJECTED (exit 1): the substitution direction reversed on both components;
#   `subsCond cs.cond old old` (a no-op substitution on the condition); a bound
#   variable MINTED from the substituted value's tag (`mkSet ⟨new.tag⟩ cond'
#   base'`, the out-of-vocabulary shape that elaborates — so the vocabulary
#   restriction is not what excludes it); a double-substituted base; the fused
#   membership assembly on the bound variable unconditionally; a condition
#   substituted `new`-for-`new`; both substitutions dropped only on the collapse
#   branch; a minted result-carrier literal `(⟨0⟩ : AsmSet)` on the collapse
#   branch; and an impl that differs from gold exactly where the substituted
#   symbol IS the bound variable's image (`if old = symExpr cs.sym then …`) —
#   rejected because the frozen `rfl` cannot see through the `ite`, though it is
#   PROVABLE with a case split (see ATTACK E), which is the correct disposition
#   for an impl the guard makes irrelevant. The 10th, `D8-discarded-probe`, VERIFIES
#   (exit 0) and is NOT a hole: it returns exactly gold's value and merely computes
#   two IN-VOCABULARY, in-domain calls it discards (`mkMemberSet old cs.base`,
#   `isTrue cs.cond`), so there is no wrong observable behavior to reject. That is
#   the residual a total functional specification cannot close by itself and is
#   precisely why the carriers are typed — see ATTACK D'. This is the expected
#   outcome overall, because the manifest's central claim was re-checked with the
#   real verifier in an audit scratch file (exit 0): `spec_unique` (any two
#   satisfiers at one input are equal) AND `verifier_pins_impl` (any `f`
#   discharging the frozen obligation equals the frozen impl on the whole guarded
#   domain) both elaborate against the current spec. The spec is a total
#   functional specification, so SPEC-TOO-WEAK is impossible by construction.
#   NO SPEC HOLE FOUND.
#
# ATTACK D' (OUT-OF-DOMAIN probe — the axis on which this spec was last
#   strengthened, and the one a total functional specification does NOT close by
#   itself, because such a term can be computed and DISCARDED while the returned
#   value stays correct).
#
#   POSITIVE CONTROL FIRST. Every attack a previous audit pass recorded against an
#   earlier revision of this spec was re-encoded VERBATIM from its record and
#   rebuilt against the frozen file. All are still same-spec
#   (`markers.same_spec` True) and NONE elaborates any more (exit 1 each):
#
#     - `let _probe := mkSet new cs.cond base'` (the ARG-1 family):
#       `error: Application type mismatch: The argument / new / has type / Expr /
#       but is expected to have type / SymE / in the application / mkSet new`.
#       Its faithful transliteration `self.func(new, self.condition, base)` was
#       the term that raised `ValueError: non-symbol dummy not recognized in
#       condition` at the F2P input. Three further members of that family — the
#       substituted condition in place of the raw one, the raw base in place of
#       the substituted one, and `old` in place of `new` at the binding position —
#       report the SAME error at the same position.
#     - `let _probe := mkMemberSet old (mkSet cs.sym cs.cond cs.base)` and
#       `let _probe := mkMemberSet (symExpr cs.sym) (mkSet cs.sym cs.cond
#       cs.base)` (an ASSEMBLED set asked a membership question):
#       `error: Application type mismatch: The argument / mkSet cs.sym cs.cond
#       cs.base / has type / AsmSet / but is expected to have type / SetE / in the
#       application / mkMemberSet old (mkSet cs.sym cs.cond cs.base)`. The
#       faithful transliteration raises `TypeError: Incompatible use of binary
#       symbol \`x\` as a real variable in \`x < y\`` from the boolean simplifier
#       at the P2P triple `ConditionSet(x, x<y, {y,z})` subs y↦w.
#     - `let _probe := subsSet (mkSet cs.sym cs.cond cs.base) old new` (an
#       ASSEMBLED set substituted into): the same `Application type mismatch`,
#       `in the application / subsSet (mkSet cs.sym cs.cond cs.base)`. The
#       faithful transliteration DIVERGES: re-measured in-process by adding that
#       one discarded call inside the real routine, `RecursionError: maximum
#       recursion depth exceeded`.
#
#   Four further members of the assembled-set family were built as well and all
#   four report the same mismatch at the same position: the fused membership
#   assembly nested in itself (`mkMemberSet new (mkMemberSet new base')`), a
#   substitution applied to a fused membership assembly, a substitution applied to
#   the assembly of the SUBSTITUTED components (`subsSet (mkSet cs.sym cond'
#   base') old new`), and an assembled set as the assembly's own base
#   (`mkSet cs.sym cs.cond (mkSet cs.sym cs.cond cs.base)`). That is the point of
#   giving the assembly's result its own terminal carrier: the whole class goes at
#   once, not one spelling of it, and the count behind "the whole class" is the
#   53280-term enumeration in the docstring.
#
#   Four shapes that are well-typed under a looser model but
#   UNDEFINED on the modeled side were then built: an assembly bound over a general
#   expression (`mkSet new cond' base'` and `mkSet old cond' base'` — the shape
#   whose real counterpart raises `ValueError: non-symbol dummy not recognized in
#   condition` at the F2P input), an off-domain membership question (`mkMemberSet
#   cond' base'`), a projection out of an assembled set (`(mkSet …).sym`), and a
#   destructuring of an assembled set as the input record. All are ELABORATION
#   FAILURES rather than rivals — the errors are quoted in the docstring's
#   OUT-OF-DOMAIN entry — while the faithful neighbours are shipped as cases
#   (`pos-build-then-assemble`, which VERIFIES, for the input-record read;
#   `true-rebind-to-new` and `open-rebind-to-new` for the fused
#   value-plus-membership assembly, which IS defined on the modeled side and is the
#   pre-patch's own expression; and `fixed-sym-binding` for a MINTED bound
#   variable, which is likewise a defined call — every inhabitant of `SymE` denotes
#   a bound variable and the assembly restricted to one is total over the measured
#   pool — whose result is simply not the one the equation names). So the
#   domain narrowing is tight on the undefined shapes and loose on the defined
#   ones, which is the pair of measurements that makes it a domain obligation
#   rather than a convenience. The exhaustive term enumeration behind it (12732
#   well-typed terms at the four tested triples, 0 raises, against 21444 / 1023
#   with an untyped binding position and 53280 further terms admitted by a model
#   whose assembly result were consumable, 5136 of them raising and 41344
#   diverging) is in the docstring, together with the one residual partiality the
#   carriers do not separate and the measurement that it is not reachable from
#   this branch.
#
# ATTACK E (SPEC-TOO-STRONG probe). A further 5 NEW correct reshapes were built in
#   this audit pass and all 5 are PROVABLE (exit 0): a `match`-destructuring impl;
#   an impl that routes the assembly through a local function value; a `let mut`
#   accumulator whose branches both assign the substituted base; a non-monadic
#   three-`let` impl; and the off-guard-differing impl noted in ATTACK D
#   (`if old = symExpr cs.sym then return mkMemberSet new base'`), which the frozen
#   `rfl` cannot close but which closes with `split` + `exact absurd … hne`,
#   discharging the impossible branch FROM the frozen guard hypothesis. That last
#   one is the load-bearing soundness measurement: the guard is a real hypothesis
#   the proof can consume, not decoration, and an impl that is faithful ON the
#   guarded domain is provable however it behaves off it. Two proof spellings of it
#   failed (`rw [if_neg hne]` and `split <;> simp_all`) and are recorded as tactic
#   gaps, not spec findings, since a working spelling exists. No faithful correct
#   impl is rejected. NO SOUNDNESS HOLE FOUND.
#
# ATTACK F' (divergence, re-measured against the semantics THIS bundle sets).
#   Confirmed by re-reading the frozen file: it sets NO
#   `loom.semantics.termination` option at all (the velvet sibling of this same
#   instance sets `"total"`; this lean bundle is plain total Lean), so the
#   disposition is decided by the elaborator's own termination check. Re-measured:
#   a self-recursive `implementation_freeSubs` fails to ELABORATE (`fail to show
#   termination … no parameters suitable for structural recursion`), an error about
#   the definition and not about the equation, so it attributes nothing to the
#   spec; the `partial def` shape IS admitted by `variant_scope` and IS rejected
#   (exit 1), but no witness can refute it — four shapes were tried against it
#   (`simp [implementation_freeSubs]`, `unfold … rfl`, `decide +kernel`,
#   `simp only … congr 1`) and every one fails on the RIVAL, the half that must
#   SUCCEED, because `partial` makes the function opaque to the kernel
#   (`Tactic `unfold` failed to unfold `implementation_freeSubs``). A rival whose
#   witness cannot be built is a non-discriminator, not a refutation. So the four
#   self-recursive / looping shapes and `weak-build-never-delivers` are VACUOUS
#   here — there is no shippable diverging rival — rather than a known hole.
#
# COVERAGE (`scripts/pbt_coverage.py`, advisory): re-run after the repair below,
#   `obl=1 cases=12 (+5/-7) binders=3 pts=7-7`, no findings. The variation is
#   meaningful rather than seven spellings of one point: the seven reject points
#   sit on OPPOSITE sides of the collapse test (three with `isTrue … = true`, one
#   with `= false`, three branch-free), and each argument position is attacked at
#   two or more points that no single other witness in the battery refutes.
#
# ONE CASE-LEVEL defect was found and repaired by THIS audit pass. The manifest
# claimed, in BINDER STRUCTURE and again in the accounting block, that the carrier
# split left the fused membership assembly as the ONLY route into the binding
# position, and on that basis recorded the sibling's `weak-build-open-wrong-sym`
# (bound-symbol propagation) as NOT MODELED. Both were false: a bound variable is
# directly constructible on this carrier and the plain assembly's first position
# accepts one, so `mkSet ⟨0⟩ cond' base'` is a well-typed, in-vocabulary rival that
# denotes a defined call. It is now shipped as `fixed-sym-binding`, with the builds
# reported above, and it closes a real gap rather than adding a respelling: the two
# pre-existing ARG-1 rivals are both branch-conditioned AND both swap the assembly
# ROUTINE along with its first argument, so neither of them tested that the plain
# assembly's first argument is pinned to `cs.sym`.
#
# Two PROSE defects were found and repaired by an earlier revision of this audit
# (no case behavior changed): the false claim that `partial` is on
# `pbt_witness`'s banned-token list (it is not, and `variant_scope` admits the
# `partial` variant — the exclusion rests on the re-measured unwitnessability
# instead), and the accounting block's undercount of the sibling battery as 7
# SPEC cases with "every sibling case recorded" when it has 18 and 9 were
# unlisted.
