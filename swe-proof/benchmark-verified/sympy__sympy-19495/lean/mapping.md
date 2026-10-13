# mapping.md — sympy__sympy-19495

## Symbol binding

- **Modeled function:** `ConditionSet._eval_subs(self, old, new)`
  — `sympy/sets/conditionset.py:208` @ base_commit `25fbcce5b1`.
- **Edited lines:** the `else`-branch tail of `_eval_subs`,
  `sympy/sets/conditionset.py:243-247` @ base_commit (the hunk that deletes the
  `if cond is S.true: return ConditionSet(new, Contains(new, base), base)`
  special case). The other gold hunks (lines 80-115) are class-docstring
  whitespace only — behavior-neutral, not modeled.
- **Lean carrier:** `Solution.lean`
  - `problem_spec_freeSubs` / `implementation_freeSubs` / `correct_freeSubs`.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

Five distinct Lean carriers, one per sympy *kind the callees are defined on*,
because each modeled callee is defined on some kinds and raises on the others
(see "Carrier discipline" below):

| Lean | Python | notes |
|---|---|---|
| `Expr` (abstract carrier, `structure { tag : Nat }`) | a general sympy symbolic expression (`sympy.Expr`: a `Symbol`, a number, an applied function) — anything admissible as a substitution *value* | only structural identity + the substitution behavior matter |
| `SymE` (abstract carrier, `structure { tag : Nat }`) | a sympy `Symbol` — the kind a `ConditionSet` may be BOUND over, i.e. `self.sym` | its own carrier: the assembly routine's first position is defined on a symbol and, for an arbitrary condition, on nothing else. One-way into `Expr` via `symExpr`; nothing maps back |
| `Cond` (abstract carrier, `structure { tag : Nat }`) | a sympy `Boolean` GIVEN OUTRIGHT — the `ConditionSet.condition` component, and not one carrying a `ConditionSet` inside it | its own carrier: a `Boolean` is what `e is S.true` inspects and what `Contains(...)` yields. The "outright" reading is what makes the callees deterministic on it under `==` (see "Structural identity" below) |
| `SetE` (abstract carrier, `structure { tag : Nat }`) | a sympy `Set` whose elements are expressions and which is described by its own range rather than by a further condition-restriction — the `ConditionSet.base_set` component as this branch RECEIVES it | its own carrier: a `Set` is what a membership question is asked about. Narrowed the same way and for the same reason as `Cond`; the shapes left out are the ones an assembly returns, which live on `AsmSet` |
| `AsmSet` (abstract carrier, `structure { tag : Nat }`) | the `Set` that the assembly routine `ConditionSet(σ, γ, β)` RETURNS | its own carrier, and a TERMINAL one: no projections, and no modeled routine takes one. The routine assembles a set once, at the end, and returns it; reading an assembled value apart, substituting into one, or restricting one further are not calls it makes and not calls the real routines are defined on (see "Assembly normalises" and "The assembled-set carrier is terminal" below) |
| `.tag : Nat` (on all five) | *(nothing)* | an inert inhabitant with **no Python counterpart**. It exists solely so each carrier is `Inhabited` + `DecidableEq` and so a G-PBT witness can name a particular element. No spec clause and no modeled callee reads it. |
| `CondSet` (`sym : SymE`, `cond : Cond`, `base : SetE`) | a `ConditionSet` instance via `self.sym`, `self.condition`, `self.base_set` | the three `.args` components, at their three kinds. The INPUT type only — a value already known to be of the three-part shape, which is what makes those three reads defined |
| `symExpr σ` | the identity on a `Symbol`, viewed at the `Expr` kind (`Symbol` **is** an `Expr`) | the inclusion of the bound-variable kind into the expression kind; total and injective. It is what lets the bound variable be compared with the symbol being substituted. Deliberately no inverse: an arbitrary `Expr` is not a `Symbol` |
| `subsCond c old new` | `c.subs(old, new)` where `c` is the `Boolean` condition | the genuine, unchanged substitution routine at the condition component (A-reference) |
| `subsSet s old new` | `s.subs(old, new)` where `s` is the `Set` base | the same unchanged substitution routine at the base-set component (A-reference) |
| `mkSet σ γ β` | `self.func(σ, γ, β)`, i.e. `ConditionSet(σ, γ, β)` with `σ` a `Symbol` | the genuine, unchanged set-assembly routine (A-reference). Its first argument is a `SymE` because that is the domain on which it is defined for an arbitrary condition. Returns a `Set` and nothing more specific: it NORMALISES, so the object it returns need not be a `ConditionSet` at all — hence the result carrier `AsmSet`, which has no readable components and which no routine consumes. See "Assembly normalises" and "The assembled-set carrier is terminal" below |
| `isTrue c` | `c is S.true` | predicate detecting the collapsed-to-true condition (only reached by the prepatch impl) |
| `mkMemberSet v β` | `ConditionSet(v, Contains(v, β), β)` — `v` a general expression, `β` a `Set` | ONE fused routine, not a composition: the assembly accepts a non-`Symbol` first argument exactly when that argument occurs in the condition it is handed, which is the case here and is not the case in general. This is the pre-patch's deleted expression; only the prepatch impl and the two ARG-1 rivals reach it |
| `{ sym := σ, cond := γ, base := β } : CondSet` | the ARGUMENT TRIPLE `(σ, γ, β)` about to be handed to `self.func` — *not* a constructed set | a binding of the three component values; only `mkSet` crosses into "a set exists now" |
| result `AsmSet` | the `Set` that `self.func(...)` returns | a bare assembled set: the model offers no way to read a bound variable, condition or base back out of it, and no way to hand it to another routine, because on the modeled side each of those uses is undefined or re-entrant |

### Carrier discipline (a domain obligation, not decoration)

A Lean `opaque` declaration is a TOTAL function; each sympy callee it models is
PARTIAL. Splitting the carriers into `Expr` / `SymE` / `Cond` / `SetE` / `AsmSet`
is what makes "well-typed in the model" coincide with "defined on the modeled
side", so that an implementation the verifier accepts always has a faithful
transliteration. The partiality is real and measured on the gold-patched testbed:

- **The assembly's first argument.** `ConditionSet(σ, γ, β)` raises
  `ValueError: non-symbol dummy not recognized in condition` when `σ` is not a
  `Symbol` and does not occur in `γ`. This is not an exotic input: the gold code
  itself raises it — `ConditionSet(2*x, Eq(2*x, y), Reals).subs(x, 3)` takes the
  modeled branch and raises, and so does the spelled-out
  `self.func(self.sym, cond, base)` at the same input — while the identical input
  with a `Symbol` bound variable returns normally. So `mkSet`'s first argument is
  a `SymE` and nothing else. Restricted that way the routine is total over the
  shapes this branch ranges over: 672 `(Symbol, condition, base)` triples
  (7 symbols × 8 conditions × 12 base sets), 0 raises.
- **The assembly's RESULT.** An assembled set is not something the routines this
  branch has are defined on. `ConditionSet(v, Contains(v, A), A)` for an
  ASSEMBLED (condition-restricted) `A` raises `TypeError: Incompatible use of
  binary symbol \`x\` as a real variable in \`x < y\`` out of the boolean
  simplifier — 25 of 36 `(v, A)` pairs (9 values × 4 assembled sets) — and a
  substitution applied to a set assembled inside the routine re-enters the
  routine rather than calling anything external: adding exactly that discarded
  call in-process gives `RecursionError: maximum recursion depth exceeded`. So
  `mkSet` and `mkMemberSet` return an `AsmSet`, which nothing consumes.
- **How much of the gap that closes.** Enumerating EVERY well-typed composition
  of the modeled vocabulary at each of the four triples the F2P + P2P tests push
  through this branch: 12732 compositions and **0 raises** as the model stands;
  21444 compositions and 1023 raises when the assembly's first position is drawn
  from the general `Expr` pool (all of them the `ValueError` above); and a
  further 53280 compositions admitted by a model whose assembly RESULT were
  consumable, of which 5136 raise and 41344 are the re-entrant substitution
  above.
- **Why the deleted expression survives as one fused routine.** The domain rule
  above is a JOINT constraint on the assembly's first two arguments, so
  `ConditionSet(v, Contains(v, β), β)` is defined for a general expression `v`
  where `ConditionSet(v, γ, β)` is not. Modeling that pair as the single
  `mkMemberSet : Expr → SetE → AsmSet` keeps the pre-patch's expression
  expressible — which is what gives G-DIFF a real discrimination test instead of
  an elaboration failure — while removing the bare membership question from the
  vocabulary, and with it every off-domain `Contains(...)` call an
  implementation could have named. Measured: 198 of 216 `(v, β)` pairs
  (18 values × 12 base sets) return normally; the 18 that raise all share one
  base set that is itself condition-restricted — i.e. an ASSEMBLED set, which is
  precisely the value the model keeps out of this position by putting it on
  `AsmSet`.
- **The substitution's replacement value.** `c.subs(old, new)` raises when `new`
  is a `Set` or a `Boolean` rather than a general expression: `SympifyError:
  NotImplemented` for `(y < 1).subs(y, Interval(0, 1))`, and `TypeError: A
  Boolean argument can only be used in Eq and Ne` for `(y < 1).subs(y, S.true)`.
  So the `old`/`new` arguments of `subsCond`/`subsSet` are `Expr` and nothing
  else, and the bound variable reaches them only through `symExpr`.
- `c.subs(...)` at the condition returns a `Boolean` and `s.subs(...)` at the base
  returns a `Set`; the two results are not interchangeable, hence two names.

With the carriers separated, each of those off-domain calls is a Lean TYPE ERROR:
a file naming one does not elaborate, so it never reaches the verifier.

### What the carriers denote, and what that leaves out

The carriers denote the sub-kinds this branch actually ranges over: `SymE` is a
`Symbol`; `SetE` is a set whose ELEMENTS are expressions, described by its own
range; `Cond` is a condition over expressions given outright; and `AsmSet` is
whatever the assembly hands back. Two measured shapes sit outside the `Cond` /
`SetE` reading, and each is now excluded by a carrier rather than by a note:

- a base set that is itself condition-restricted — i.e. an assembled set. On the
  Python side `Contains(v, ConditionSet(z, z<y, Reals))` raises `TypeError:
  Incompatible use of binary symbol` out of the boolean simplifier, and
  substituting into such a set re-enters `_eval_subs`. In the model such a value
  can only be an `AsmSet`, which is not the carrier `subsSet`, `mkSet` or
  `mkMemberSet` take a set from, so no term names either call.
- a base set whose ELEMENT is itself a set — `ConditionSet(x, x < 1,
  FiniteSet(Interval(0,1)))` raises `SympifyError`, though the same base with a
  condition not mentioning the bound variable returns normally. This is the one
  residual the carriers do not separate: `SetE` reads as a set of expressions,
  and nothing in the model can build a set of sets, so no term reaches it
  either. It is recorded rather than typed away because no modeled routine
  produces such a base from one that is not already such a base.

Neither is reachable here, and the narrowing costs no tested coverage. Measured
two ways. (i) The exhaustive composition enumeration over the four triples the
tests push through this branch (`ConditionSet(x, x<y, {y,z})` subs y↦w;
`ConditionSet(n, n<x, (0,oo))` and `ConditionSet(n, n<x, (-oo,0))` subs x↦p; and
the F2P's `ConditionSet(x, Contains(y, [-1,1]), ImageSet(…asin(y)…))` subs
y↦1/3) gives 12732 well-typed terms and 0 raises. (ii) Instrumenting
`_eval_subs` and running the F2P test plus all eight P2P tests records 14 calls,
of which exactly 4 take the modeled branch; in all 4 the bound variable is a
`Symbol` and in none of them is the condition or the base set condition-
restricted. The G-CONF differential agrees from the other side: over its
80299 fuzzed inputs, 0 were skipped for having a condition-restricted component,
so the narrowing removes nothing the differential was covering.

### Assembly normalises, so the result carrier has no components

`self.func(sym, cond, base)` is `ConditionSet.__new__`, which CANONICALISES. The
object it returns is frequently not a `ConditionSet`, and then it has no `.sym`,
no `.condition` and no `.base_set` at all. Measured at base_commit:

| call | returns | `.sym` |
|---|---|---|
| `ConditionSet(x, Contains(x, Interval(0,3)), Interval(0,3))` | `ConditionSet(...)` | `x` |
| `ConditionSet(x, S.true, Interval(0,3))` | `Interval(0, 3)` | `AttributeError: 'Interval' object has no attribute 'sym'` |
| `ConditionSet(x, S.false, Interval(0,3))` | `EmptySet` | `AttributeError: 'EmptySet' object has no attribute 'sym'` |

The `S.true` row is exactly the corner case the modeled change is about, so this
is not an exotic corner: on the very sub-domain where the behavior is decided, an
assembled result is a bare `Interval`. Therefore `mkSet` returns `AsmSet` — a
carrier with no projections — and the three-field record `CondSet` is the INPUT
type only. Reading components off the input is as defined as `_eval_subs`'s own
reads (the input *is* a `ConditionSet`, or the method would not have been
reached); reading them off an assembled result is undefined. In the model the
first is a projection and the second does not typecheck, which is the whole point
of having two types.

### The assembled-set carrier is terminal, not just projection-free

Having no projections is only half of what the measurements ask for. The other
half is that no ROUTINE may take an assembled set either, and that is why the
result is `AsmSet` rather than the `SetE` an input base set has. Two facts,
measured at base_commit:

- **A membership question about an assembled set is not defined.** With `A` a
  condition-restricted set, `ConditionSet(v, Contains(v, A), A)` raises
  `TypeError: Incompatible use of binary symbol \`x\` as a real variable in
  \`x < y\`` from the boolean simplifier — 25 of 36 `(v, A)` pairs over 9 values
  × 4 assembled sets (G-CONF LEG 5a). The 11 that return are the ones where
  normalisation removes the nesting before the simplifier sees it, so being
  defined here is a property of the particular value, not of the operation.
- **A substitution applied to an assembled set is not an external callee at
  all.** `.subs` on a `ConditionSet` dispatches into `_eval_subs` — the routine
  being modeled. Adding exactly that discarded call inside the real routine
  (`inner = self.func(sym, cond, base); inner.subs(old, new)`) gives
  `RecursionError: maximum recursion depth exceeded` (G-CONF LEG 5b). A model
  that let an assembled set be substituted into would be modeling recursion the
  routine does not have.

So the vocabulary has exactly one thing to do with an assembled set: return it.
The three positions a looser model would open — a membership question about one,
a substitution into one, and a further condition-restriction of one — are Lean
type errors here, and the enumeration puts a number on what that removes: 53280
further well-typed terms at the four tested triples, 5136 of them raising and
41344 re-entrant. This is also what makes the narrowing of `Cond` and `SetE` to
components given OUTRIGHT stable rather than wishful: the one operation that
could have produced a condition-restricted value inside them is the assembly, and
its result cannot get back in.

### Structural identity on the carriers, and why the spec's `=` is an equation

`mkSet` is a function on the carriers, and it has to be: it is what the spec's
`=` is asserted between. Two things make that reading sound on the carriers as
they are typed, and both are measured rather than assumed.

- **Determinism under `==`.** Over the G-CONF grid (54 inputs, 3 repeats each),
  `cs.condition.subs(old, new)`, `cs.base_set.subs(old, new)`,
  `cs.func(cs.sym, cond', base')` and the real routine `cs.subs(old, new)` each
  return an `==`-equal value on every repeat: 0 instabilities in all four
  columns (LEG 4). Across the four triples the F2P + P2P tests push through this
  branch the same holds. So every carrier — `Expr`, `SymE`, `Cond`, `SetE`,
  `AsmSet` — carries plain structural identity, and `conformance_check.py`
  compares with strict `==` and no `.dummy_eq` fallback.
- **Where non-determinism would have come from, and why it is outside the
  model.** `ConditionSet.__new__` has one arm that mints a fresh `Dummy`: the
  rename arm, reached when the base set it is handed is ITSELF a
  `ConditionSet` binding a colliding variable. Measured at

  ```python
  cs  = ConditionSet(x, (x > lambda_) & (x < y),
                     Intersection(ConditionSet(y, x + y < w, Reals), Reals,
                                  evaluate=False))
  old, new = w, Integer(2)
  ```

  three successive `cs._eval_subs(w, 2)` calls return objects that are pairwise
  `==`-unequal and pairwise `.dummy_eq`, because the substituted base normalises
  to a nested `ConditionSet`. That input is not in the model: its base set is
  condition-restricted, so it is not a `SetE` — it is the shape the previous
  section puts on `AsmSet` — and G-CONF skips it as outside the carriers. The
  narrowing is what buys the equation, and it costs nothing tested: of the 14
  `_eval_subs` calls the F2P and eight P2P tests make, the 4 that take the
  modeled branch have no condition-restricted component in either position, and
  of G-CONF's fuzzed inputs 0 were skipped for having one.

An implementation cannot get around this by renaming anything itself: no modeled
operation renames a bound variable, and `SymE` has no constructor, so the bound
variable an implementation returns is the one it was given or nothing.

### Modeled vocabulary (exhaustive)

The model's whole vocabulary is:

> the five carriers `Expr` / `SymE` / `Cond` / `SetE` / `AsmSet`; `symExpr`;
> `mkSet`; `subsCond`; `subsSet`; `isTrue`; `mkMemberSet`; and `CondSet`
> construction / field projection.

Anything else an implementation might name has **no antecedent in
`_eval_subs`** and therefore no faithful transliteration — in particular:
arithmetic on `.tag`, a carrier literal `⟨k⟩` minted from nothing, any crossing
between the carriers (e.g. `(⟨e.tag⟩ : SymE)` from an `Expr`), and any ambient
effect primitive such as `dbg_trace` / `IO`. `_eval_subs` computes from its three
inputs with the callees above and returns; it mints no symbols, reads no
representation, and prints nothing. A term outside this vocabulary is not a
statement about the specification. (It is not load-bearing either: the one such
shape that elaborates, `mkSet ⟨new.tag⟩ cond' base'`, is REJECTED by the spec —
G-PBT's audit record, ATTACK D — and it is not even an undefined call, since
every inhabitant of `SymE` denotes a `Symbol` and the assembly is total there.)

### Where the assembly happens, and what a record binding means

`_eval_subs` ends in a single `self.func(sym, cond, base)` application, and
`mkSet` is that application — modeled explicitly rather than left implicit, so
that the model says out loud *when* a set comes into existence.

A `CondSet` value therefore has two readings and they are not in conflict. As the
INPUT it denotes the `ConditionSet` the method was called on. As a local binding
inside an implementation it denotes the ARGUMENT TRIPLE `(sym, cond, base)` about
to be handed to `self.func` — no set exists yet, and reading its fields is
reading three local values back. That is why

```lean
let built : CondSet := { sym := cs.sym, cond := subsCond cs.cond old new,
                         base := subsSet cs.base old new }
return mkSet built.sym built.cond built.base
```

is faithful (and verifies), while

```lean
let assembled := mkSet cs.sym cond' base'
return mkSet assembled.sym assembled.cond assembled.base
```

does not typecheck — `assembled : AsmSet` and the environment contains no
`AsmSet.sym`. The two shapes look alike and denote different things: the first
binds three values, the second calls the assembly routine and then asks the
normalised result for components it may not have. Nor does

```lean
let assembled := mkSet cs.sym cond' base'
return mkSet cs.sym cond' (subsSet assembled old new)
```

typecheck, for the same reason one step further out: `subsSet` takes a `SetE` and
an assembled set is not one. `refinement.md` §"where the assembly is modeled"
carries the argument in full.

## Callee provenance + flag deps

- `subsCond` / `subsSet` ↔ `Basic.subs` — UNCHANGED by the patch; the ordinary
  substitution dispatcher, named twice because it is applied at two different
  kinds (`Boolean` condition, `Set` base) and returns that kind. **A-reference**
  (modeled deeply via the impl's op-for-op transliteration; validated == real
  callee by G-CONF in-process). No flag dependence: `_eval_subs` calls
  `.subs(old, new)` with positional args only.
- `mkSet` ↔ `self.func(...)` = `ConditionSet(...)` — UNCHANGED by the patch (the
  gold hunk deletes a call to it, it does not alter it). **A-reference**
  (validated == the real callee by G-CONF in-process, whose shadow ends in
  `cs.func(cs.sym, cs.condition.subs(old, new), cs.base_set.subs(old, new))`).
  Opaque in both directions: no axiom describes its value, and its RESULT type
  `AsmSet` exposes nothing and is accepted nowhere, which is what makes the
  normalisation above unexploitable. Its DOMAIN is validated as a leg in its own
  right rather than inherited from the differential: the differential only ever
  calls it at the gold argument triple, so G-CONF's LEG 2 exercises the first
  argument over both pools and asserts the `Symbol` / non-`Symbol` split in both
  directions, and LEG 5 measures the result position from the other side (what
  happens when an assembled value is handed onward). No flag dependence: called
  with three positional args.
- `symExpr` ↔ the inclusion `Symbol ⊂ Expr`, which on the Python side is the
  identity — a `Symbol` already IS an `Expr`, so the "call" it names is free.
  Total; no flag dependence. It exists so the bound variable can appear where a
  general expression is called for (the guard's comparison with `old`, and the
  fused membership assembly) without the reverse being expressible.
- `mkMemberSet` ↔ `ConditionSet(v, Contains(v, base), base)` and `isTrue` ↔
  `is S.true` are reached only by the prepatch impl and by the two ARG-1 rivals.
  `isTrue` is total on `Cond → Bool`; `mkMemberSet` is total on the base sets
  this branch ranges over (G-CONF LEG 3: 54 of 54) and returns an `AsmSet`,
  because what it names is the same assembly routine — so its result is no more
  consumable than `mkSet`'s, and the values it is NOT total on are exactly the
  assembled ones that carrier keeps out of its argument (LEG 5a).
- No consumed `axiom <callee>_prop` is needed by the construction; G-AX is a
  skip stub. If the proof agent's axiom-propose loop later needs a
  `subsCond`/`subsSet` property, it must be the weakest one and `axiom_check.py`
  is updated to run `Basic.subs` against it.

## Branch guard

The modeled branch is the `old != self.sym` path AND `isinstance(self.sym,
Symbol)`. Two things are excluded, both deliberately:

- the early `return self` guard for the Tuple/equation-set syntax (the non-`Expr`
  dummies); and
- a bound variable that is an `Expr` but not a `Symbol` (e.g. `2*x`), which is
  the input the assembly routine raises on. `self.sym` is a `Symbol` in all four
  triples the F2P + P2P tests push through this branch, so nothing tested is lost.

That narrowing also settles which EQUALITY the guard may use. `Solution.lean`
states the guard as the structural disequality `old ≠ symExpr cs.sym`, whereas
the real test is sympy's semantic `old == self.sym`. The two can disagree —
measured: 6 of 144 ordered pairs over a 12-value pool are `==`-equal but
structurally different, and every one is a `Float` against an `Integer`
(`Float(2.0) == Integer(2)` is `True`, while `.subs` matches structurally, so
`(x>2).subs(Float(2.0), q)` is a no-op where `(x>2).subs(Integer(2), q)`
substitutes). None of the divergences involves a `Symbol` on either side, and the
one behavioural disagreement they can produce needs a non-`Symbol` bound variable
to sit on: `ConditionSet(Integer(2), x>2, Integers)._eval_subs(Float(2.0), q)`
takes the RENAME branch although the two are structurally distinct. With the
bound variable narrowed to a `Symbol` that input is outside the model, and on the
remaining domain the structural guard and the real test coincide — so the guard
stays a plain decidable disequality instead of an opaque semantic-equality
predicate. G-CONF only feeds inputs where `cs.sym` is a `Symbol` and
`old != cs.sym`.

## Pinned G-CONF fuzz seed

`SEED = 19495` (also hard-coded in `conformance_check.py`), `N = 100_000`.

`conformance_check.py` runs five legs, all of which must pass — the differential
plus the four domain/identity premises the carrier split rests on. Measured
output on the gold-patched testbed:

```
LEG 1 differential (strict ==): ran=80299 disagreements=0 condition-collapse inputs=959 inputs outside the carriers=0 carrier escapes: cond=0 base=0 (seed=19495, N=100000)
LEG 2 binding-position domain: Symbol ok=72 raise=0 | non-Symbol ok=0 raise=90 exc=['ValueError']
LEG 3 fused-membership domain: ok=54 raise=0 exc=[]
LEG 4 determinism under `==` over 3 repeats: checked=54 unstable: subsCond=0 subsSet=0 mkSet=0 real_routine=0
LEG 5a fused membership on an ASSEMBLED set: ok=11 raise=25 exc=['TypeError: Incompatible use of binary symbol `n` as a real ', 'TypeError: ... `x` ...', 'TypeError: ... `y` ...']
LEG 5b substitution applied to a set assembled inside the routine: RecursionError
conformance: legs_passed=5/5
```

- LEG 1 compares with strict `==` and no `.dummy_eq` fallback, which is what the
  spec asserts. It fails if the condition-collapse corner case is never reached
  (so the differential cannot go silent on the sub-domain the fix decides) and it
  fails if a substituted condition or base leaves the carriers — `carrier
  escapes: cond=0 base=0` is the measurement that `subsCond : Cond → … → Cond`
  and `subsSet : SetE → … → SetE` are honest types. `inputs outside the
  carriers=0` records that the narrowing removed nothing this differential was
  covering.
- LEG 2 fails in BOTH directions: if the assembly raises for a `Symbol` bound
  variable (the `SymE` carrier would be unsound) and if it accepts a
  non-`Symbol` one (the carrier would be narrower than the real domain).
- LEG 3's grid deliberately excludes the assembled bases, which are the ones it
  would raise on; LEG 5a is that exclusion measured rather than assumed, so the
  two legs together pin `mkMemberSet`'s argument to exactly `SetE`.
- LEG 4 is the premise behind structural identity: every callee, and the real
  routine, is determined by its arguments up to `==` on the carriers.
- LEG 5 is the premise behind `AsmSet` being terminal, in both consumer
  positions the model would otherwise have. It fails if the membership assembly
  accepts every assembled set (the carrier would be too narrow) and if the
  re-entrant substitution returns normally (it would be an ordinary callee).
