# refinement.md — sympy__sympy-19495

Maps every operation in `implementation_freeSubs` (Solution.lean impl region) to
its `patch.diff` counterpart. Tags: **R** (type refinement), **A-consumed**
(proof uses an axiom's property), **A-reference** (deep model validated == real
callee by G-CONF/G-AX), **I** (identical concrete op).

## Modeled function

`ConditionSet._eval_subs(self, old, new)` in `sympy/sets/conditionset.py`, the
branch reached when `old != self.sym` (substituting a *free* symbol, not the
bound/dummy variable) and `self.sym` is a `Symbol` — see `mapping.md`
§"Branch guard" for why the second condition is part of the branch and costs no
tested coverage. Post-patch source (gold):

```python
        else:
            cond = self.condition.subs(old, new)
            base = self.base_set.subs(old, new)
            return self.func(self.sym, cond, base)
```

The pre-patch buggy source it replaces:

```python
        cond = self.condition.subs(old, new)
        base = self.base_set.subs(old, new)
        if cond is S.true:
            return ConditionSet(new, Contains(new, base), base)
        return self.func(self.sym, cond, base)
```

(The remaining hunks in the gold patch are pure docstring whitespace edits in
`__new__`'s class docstring — behavior-neutral; not modeled.)

## Operation correspondence

| # | `implementation_freeSubs` op | `patch.diff` counterpart | tag |
|---|---|---|---|
| 1 | `let cond' := subsCond cs.cond old new` | `cond = self.condition.subs(old, new)` | **A-reference** — `subsCond` is the genuine `Basic.subs` at the `Boolean` condition component (`Cond → Expr → Expr → Cond`); validated == real callee by G-CONF (exercised in-process). No consumed `_prop` axiom. |
| 2 | `let base' := subsSet cs.base old new` | `base = self.base_set.subs(old, new)` | **A-reference** — the same substitution callee at the `Set` base component (`SetE → Expr → Expr → SetE`); validated by G-CONF. |
| 3 | `return mkSet cs.sym cond' base'` | `return self.func(self.sym, cond, base)` | **A-reference** — `mkSet` is the genuine, unchanged set-assembly routine `ConditionSet.__new__` (`SymE → Cond → SetE → AsmSet`); validated == real callee by G-CONF, whose shadow ends in that same `cs.func(...)` call. The set is assembled from the ORIGINAL bound variable `self.sym` (= `cs.sym`, a `SymE` because that is the kind the routine is defined on for an arbitrary condition), the substituted condition, and the substituted base set; the identity of the bound variable is preserved verbatim. |

There is **no** `if cond is S.true: return ConditionSet(new, …)` step in the
impl — that is precisely the special case the fix deletes. The prepatch impl
(`Solution_prepatch.lean`) reintroduces it as `if isTrue cond' then return
mkMemberSet new base'`, where `mkMemberSet : Expr → SetE → AsmSet` mirrors the
deleted expression `ConditionSet(new, Contains(new, base), base)` as ONE fused
routine. Fusing it is a domain requirement, not an abbreviation: the assembly
accepts a non-`Symbol` first argument exactly when that argument occurs in the
condition it is handed, which is true of this pair and false in general
(`mapping.md` §"Carrier discipline" has the 198/216 measurement and the raise the
unfused spelling produces). So the prepatch's rebinding of the set to `new`
remains fully expressible — G-DIFF gets a real discrimination test rather than an
elaboration failure — while the bare membership question, which has off-domain
spellings, is not in the vocabulary at all. G-DIFF confirms the prepatch's
`correct_freeSubs` cannot close.

No changed op is inexpressible; the branch is modeled element-for-element.

## Soundness notes

- The spec is the single equation `result = mkSet cs.sym (subsCond cs.cond old
  new) (subsSet cs.base old new)`. Its three ARGUMENT POSITIONS carry the three
  independent commitments, and because `mkSet` carries no axiom the only route to
  the equation is congruence — so disagreeing at any one position is
  unprovable, and the equation is not a weaker statement than a three-field
  conjunction would be.
- Argument position 1 = `cs.sym` (directive 5 frame): pins the bound variable to
  its input value. This is the soundness-critical position — the prepatch's
  rebinding to `new` is exactly what it forbids, and the F2P `.dummy_eq` check
  observes it (the bare-`ImageSet` collapse the issue reports follows once the
  set constructor receives the correct `(sym, cond, base)`). Its TYPE carries a
  second commitment: the position is `SymE`, so the only values that can reach it
  are ones the real routine is defined on.
- Argument positions 2 and 3 are the substituted condition/base (directive 8
  grounded): the result must be *produced by* applying the real substitution to
  the input's own components, not echoed from an oracle.
- **Carrier kinds are part of the contract.** The model has five carriers —
  `Expr` (a general symbolic expression, the only thing a substitution may put in
  for a symbol), `SymE` (a bound variable, i.e. a `Symbol`), `Cond` (the
  `Boolean` condition, given outright), `SetE` (the `Set` base as this branch
  receives it, described by its own range rather than by a further
  condition-restriction) and `AsmSet` (what the assembly RETURNS: a terminal
  carrier, with no projections and accepted by no routine) — matching the sympy
  kinds the callees are defined on, with the one-way inclusion `symExpr : SymE →
  Expr` and no way back. A Lean `opaque` is total where the callee it models is
  not, so a coarser carrier set would let an impl name a call the elaborator
  accepts and `_eval_subs` could not make: `ConditionSet(v, γ, β)` raises
  `ValueError: non-symbol dummy not recognized in condition` when `v` is not a
  `Symbol` and does not occur in `γ`; `Contains(v, s)` raises `TypeError:
  expecting Set` for a non-`Set` second argument and `TypeError: Incompatible use
  of binary symbol` when `s` is condition-restricted, i.e. assembled; `c.subs(old,
  new)` raises `SympifyError: NotImplemented` when the replacement value is a
  `Set` or a `Boolean`; and `.subs` on an assembled set is not an external callee
  at all but a re-entry into `_eval_subs` (`RecursionError` when the call is
  added in-process). None of those is a corner: enumerating every well-typed
  composition of the vocabulary at the four triples the F2P + P2P tests push
  through this branch gives **0 raises** out of 12732 terms as the carriers now
  stand, against 1023 raises out of 21444 when the binding position is drawn from
  the general expression pool, and a further 53280 terms admitted once the
  assembly's RESULT is consumable, of which 5136 raise and 41344 re-enter the
  routine. With the kinds separated every
  such call is a Lean type error, so each op above has a total counterpart and the
  op-for-op reading is exact. `mapping.md` §"Carrier discipline" carries the
  measurements, and its §"Modeled vocabulary" fixes the exhaustive list of names
  an impl of this routine can use; `_eval_subs` computes from its three inputs
  with those callees and returns, so a term outside that list (tag arithmetic, a
  minted carrier literal, a cross-carrier coercion via `.tag`, an ambient effect
  primitive such as `dbg_trace`) has no op in `patch.diff` to correspond to and
  is outside the refinement, not a laxity in it.

### Where the assembly is modeled (and why the result carries nothing)

The spec's `result : AsmSet` is the OBJECT `self.func(...)` returns, and `mkSet`
is that call, modeled explicitly as an unchanged A-reference. The result carrier
is deliberately featureless AND terminal: `AsmSet` has no `sym`/`cond`/`base`
projections at all, and no modeled routine takes one as an argument. Four
reasons, in the order they matter:

1. **The assembly routine CANONICALISES, so its result need not have
   components.** `ConditionSet(x, S.true, Interval(0,3))` returns `Interval(0, 3)`
   and `ConditionSet(x, S.false, Interval(0,3))` returns `EmptySet`; asking either
   for `.sym`, `.condition` or `.base_set` raises `AttributeError`
   (`mapping.md` §"Assembly normalises" has the measured table). The `S.true` row
   is the very sub-domain the modeled change decides. A Lean `opaque` is a total
   function and a record projection is a total operation, so a model in which the
   result were a three-field record would let an implementation read components
   off an object that has none — a well-typed term with no counterpart the real
   code could execute. Giving the result its own projection-free carrier makes
   that shape a type error instead (measured: `properties.py`'s OUT-OF-DOMAIN
   entry quotes both the projection and the destructuring failure). Reading
   components off the INPUT stays available, because the input *is* a
   `ConditionSet` (or `_eval_subs` would not have been entered), which is exactly
   the read the gold source itself performs.

2. **The patch changes only the arguments, never the assembly routine.**
   `self.func` (= `ConditionSet`) is an UNCHANGED callee: both legs of the
   refinement — impl op 3 and the gold `return self.func(self.sym, cond, base)` —
   apply the *same* routine to the *same* argument positions. So the model leaves
   it OPAQUE: no axiom describes what it computes, and the normalisation itself is
   not part of the modeled behavior. The behavioural content of the fix is which
   three arguments reach it, which is what the three argument positions state.

3. **An assembled set is not something this branch does anything else with, and
   the routines are not defined on one.** `_eval_subs` assembles a set once, in
   its `return`, and hands it to its caller. Modeling the result as a `SetE` — the
   carrier an INPUT base set has — would make three further calls well-typed that
   the real code cannot make, and measurement says they are not defined:
   `ConditionSet(v, Contains(v, A), A)` for an assembled `A` raises `TypeError:
   Incompatible use of binary symbol` in 25 of 36 grid pairs (G-CONF LEG 5a); a
   substitution applied to a set assembled inside the routine re-enters
   `_eval_subs` and, added in-process, gives `RecursionError` (LEG 5b); and a
   further condition-restriction takes the same assembled value into the same
   position. So the result gets its own terminal carrier, and all three shapes are
   Lean type errors. This is also what keeps `Cond` and `SetE` narrow honestly:
   the only operation that could manufacture a condition-restricted value for
   those positions is the assembly, and its result cannot re-enter them.

4. **Opacity plus determinism gives exactly the strength needed, and no more.**
   `mkSet` is a function on the carriers, and the equation is asserted between its
   results, so what has to hold on the Python side is that equal argument triples
   give equal objects — under plain `==`, which is what the spec's `=` says.
   Measured over the G-CONF grid (54 inputs × 3 repeats): 0 instabilities for
   `condition.subs`, for `base_set.subs`, for `cs.func(...)` and for the real
   routine `cs.subs(...)` (LEG 4), and the differential itself compares with
   strict `==` and no `.dummy_eq` fallback over 80299 inputs, 0 disagreements.
   The one arm of `ConditionSet.__new__` that mints a fresh `Dummy` — the rename
   arm — is reached only when the base set handed to it is ITSELF a
   `ConditionSet`; at such an input three successive `_eval_subs(w, 2)` calls do
   return pairwise `==`-unequal, pairwise `.dummy_eq` objects, which is why that
   shape is not an inhabitant of `SetE` and lands on `AsmSet` instead
   (`mapping.md` §"Structural identity on the carriers" carries the input and the
   numbers). So no quotient is taken anywhere, and an implementation could not
   exploit one if it were: no modeled operation renames a bound variable, and
   `SymE` has no constructor. Congruence is then the only route the
   verifier has to the equation, since no axiom about `mkSet` exists to shortcut
   it — hence an implementation discharging `result = mkSet cs.sym (subsCond …)
   (subsSet …)` must reproduce all three arguments, and the prepatch, which hands
   `new` (≠ `cs.sym`) in the collapse case, cannot. The converse is *not* claimed
   and must not be: `mkSet` is not injective (the two rows in point 1 are the
   counterexamples), so "the arguments differ" does not by itself prove "the
   objects differ". That is why each G-PBT reject witness states the object-level
   distinctness at its own concrete point as a hypothesis rather than deriving it
   from an injectivity it does not have — the same fact the F2P regression
   asserts about the F2P input.

**G-CONF validates the bridge mechanically, not in prose — in five legs, because
one leg validates only half of an A-reference.** LEG 1 is the differential: the
shadow `cs.func(cs.sym, cs.condition.subs(old,new), cs.base_set.subs(old,new))` —
the impl's op-for-op transliteration, `mkSet` included, run against the REAL
callees — diffed against the real `cs.subs(old,new)` over ≥1e5 fuzzed inputs
(including the condition-collapse corner case, which the leg fails if it never
reaches) under the gold patch: 80299 inputs on the modeled branch, 0
disagreements. Inputs are drawn where `cs.sym` is a `Symbol` and `old != cs.sym`,
i.e. the modeled branch, and results are compared with STRICT `==` — no renaming
allowance — matching the identity point 4 fixes. The leg also fails if a
substituted condition or base leaves the carriers, which is the measurement that
`subsCond` and `subsSet` return the kinds their types claim (0 escapes), and it
reports how many inputs the narrowed carriers excluded (0 of them).

What LEG 1 cannot show, and must not be read as showing, is that the assembly
callee is defined WHEREVER the model can name it: every fuzzed input calls
`mkSet` at the gold argument triple, so a differential over that shadow validates
one composition, not the leg's whole domain. That is the other half of an
A-reference — the callee is partial, the `opaque` is total — and it is measured
separately. LEG 2 exercises the assembly's first argument over both pools and
asserts the split the `SymE` carrier draws, in BOTH directions: it fails if the
routine raises for a `Symbol` bound variable (the carrier would be unsound) and
equally if it accepts a non-`Symbol` one (the carrier would be narrower than the
real domain). LEG 3 does the same for the fused membership assembly, whose domain
is wider on purpose — wider in the first argument, and no wider in the second,
which is what LEG 5a measures from the other side. LEG 4 measures the identity the
equation is stated under, and LEG 5 the two consumer positions the terminal result
carrier closes. So with `mkSet` modeled explicitly the shadow is a literal reading
of the spec's right-hand side, and the domain the model gives it is a measurement
rather than an assumption; `mapping.md` §"Pinned G-CONF fuzz seed" records all
five legs' output.

The spec is intentionally the `old ≠ symExpr cs.sym` BRANCH contract (the
precondition sits in the `correct_freeSubs` binder per SPEC_GUIDE §1); it does not
purport to describe the bound-variable-rename branch (`old = sym`), the
equation-set syntax early return, a set bound over a non-`Symbol` expression
(which the real routine raises on), or a set whose condition or base set is itself
condition-restricted (the shape on which the assembly mints a fresh bound-variable
name, and which the carriers place outside the input type). All four exclusions are
carried by the types, and each is measured to cost nothing the tests exercise: of
the 14 `_eval_subs` calls the F2P and eight P2P tests make, the 4 that take the
modeled branch satisfy every one of them.

### What the domain exclusions cost, in numbers

An exclusion that is not accounted for is indistinguishable from a spec that
quietly declines the hard inputs, so each one is stated with the fraction of
inputs it removes rather than only with its justification. This model's
exclusions are carried by the CARRIERS (a Lean type error for anything outside
them) rather than by a precondition, and their measured cost is:

| exclusion | carried by | cost |
|---|---|---|
| bound variable not a `Symbol` | `SymE` at the assembly's argument 1 | 0 of the 4 modeled-branch calls the F2P + P2P tests make; the fuzz pool draws only `Symbol` binders, and LEG 2 measures the split in both directions (72 accepted / 90 raised) |
| condition or base set itself condition-restricted | `Cond` / `SetE` read as components given outright | **0 of 80299** fuzzed inputs on the modeled branch (`inputs outside the carriers=0`, LEG 1) and 0 of the 4 tested branch calls |
| an assembled set handed onward (read apart, substituted into, restricted further) | `AsmSet`, terminal | not an input exclusion at all: it removes TERMS an implementation could write (53280 at the four tested triples), not inputs the spec speaks about, so its input-side cost is 0 by construction |
| the rename branch (`old = sym`) and the equation-set early return | the `correct_freeSubs` binder hypothesis | the other 10 of the 14 recorded `_eval_subs` calls; these are separate branches of the real routine, not narrowings of the modeled one |

The one residual the carriers do NOT separate is a base set whose ELEMENT is
itself a set (`ConditionSet(x, x < 1, FiniteSet(Interval(0,1)))` raises
`SympifyError`). It is recorded rather than typed away because no modeled routine
can produce such a base from one that is not already such a base, and the
enumeration confirms no term of the vocabulary reaches it (0 raises in 12732
terms). `mapping.md` §"What the carriers denote, and what that leaves out" carries
the measurement.

For the record, the velvet sibling of this instance reaches the same domain
obligation the other way — a `BuildsDefined` PRECONDITION bundled over every
nameable set-building invocation, whose cost it measures as 13-19 of 2347 fuzzed
inputs (~0.6-0.8%) excluded. The choice is a modeling one and the two are not in
conflict: a precondition excludes INPUTS on which some writable call would raise,
where a carrier makes those calls unwritable. The lean side pays 0% on inputs
because the exclusion falls on terms instead, and it owes the accounting above in
exchange.
