# mapping.md — sympy__sympy-19495

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 25fbcce5b1a4c7e3956e6062930f4a44ce95a632`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each modeled callee.

Repo file under change: `sympy/sets/conditionset.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `evalSubsFree (boundSym) (condition) (baseSet) (old) (new)` | `ConditionSet._eval_subs(self, old, new)` — `sympy/sets/conditionset.py:208`, the `isinstance(self.sym, Expr) and old != sym` branch (lines 242–246 pre-patch / 241–248 post-patch), further restricted to a `Symbol` binder (§3.3) | the modeled changed method, restricted to the branch the patch edits |
| `Obj` *(opaque sort)* | any SymPy object occupying a plain (non-condition, non-set, non-binder) slot: a binder once it has left the binder slot, a substitution target `old`, a replacement `new` | opaque handle |
| `Cond` *(opaque sort)* | a SymPy `Boolean` — anything `as_Boolean` accepts, i.e. anything the constructor accepts in its condition slot (`conditionset.py:135`) | opaque handle, **sorted** because the constructor is partial in that slot (§3.3) |
| `SetObj` *(opaque sort)* | a SymPy `Set` in the **component** role: `self.base_set`, or that set with a substitution pushed through it | opaque handle, **sorted** for the same reason (§3.3) |
| `BuiltSet` *(opaque sort)* | the SymPy `Set` the operation RETURNS — the freshly built `ConditionSet` | opaque handle, a sort distinct from `SetObj` so a produced set cannot re-enter a component slot (§3.4) |
| `Binder` *(opaque sort)* | `self.sym` when it is a plain `Symbol` (`self.args[0]`, `conditionset.py:212`) | the set's own internal binder; a sort of its own so that the domain restriction is carried by the TYPE (§3.3) |
| `Old` *(opaque sort)* | the `old` argument of `_eval_subs` in its substitution role — the object a `Basic.subs` call replaces | opaque handle, **sorted** so the model can name only the substitution the operation was handed (§3.4) |
| `New` *(opaque sort)* | the `new` argument of `_eval_subs` in its substitution role — the object `Basic.subs` puts in `old`'s place | opaque handle, **sorted** for the same reason (§3.4) |
| `binderObj` | the identity view of `self.sym` as an ordinary object — how the binder is named when a substitution argument could refer to it (`old != sym`, `conditionset.py:208`) | injection `Binder → Obj` |
| `oldObj` | the identity view of `old` as an ordinary object — how it is named in a plain slot rather than its substitution role | injection `Old → Obj` |
| `newObj` | the identity view of `new` as an ordinary object, for the same reason | injection `New → Obj` |
| `boundSym` | `self.sym` / `sym` | the set's own internal binder |
| `condition` | `self.condition` (`self.args[1]`, the filtering predicate) | the condition object |
| `baseSet` | `self.base_set` (`self.args[2]`, the set being filtered) | the base set object |
| `old` | `old` arg of `_eval_subs` | the symbol being replaced (here `old != self.sym`) |
| `new` | `new` arg of `_eval_subs` | the replacement value |
| `substCond` *(opaque — A-reference)* | `Basic.subs(self, old, new)` applied as `self.condition.subs(old, new)` (`conditionset.py:243`) | unchanged structural-substitution callee, at the condition slot |
| `substSet` *(opaque — A-reference)* | the SAME callee applied as `self.base_set.subs(old, new)` (`conditionset.py:244`) | unchanged structural-substitution callee, at the base slot |
| `CondSubDefined condition old new` *(opaque `Prop`)* | `self.condition.subs(old, new)` returns normally rather than propagating an error out of `_eval_subs` | the condition-slot substitution's DOMAIN, carried as a `require` (§3.4) |
| `BaseSubDefined baseSet old new` *(opaque `Prop`)* | `self.base_set.subs(old, new)` returns normally | the base-slot substitution's DOMAIN, carried as a `require` (§3.4) |
| `mkSet` *(opaque — A-reference)* | `self.func(sym, cond, base)` — the `ConditionSet` constructor `ConditionSet.__new__` (`conditionset.py:117`), reached via `self.func`, in its **binder-keyed invocation shape** | unchanged set-builder constructor, shape 1 (§3.3) |
| `mkSetOnValue` *(opaque — A-reference)* | the SAME constructor in its **value-keyed invocation shape** `ConditionSet(v, Contains(v, s), s)` (`conditionset.py:245` pre-patch; the shape the problem statement's `Out[75]` displays) | unchanged set-builder constructor, shape 2 (§3.3) |
| `evalSubsSpec` *(pure deep model — R/I)* | the rebuild expression `self.func(self.sym, cond, base)` with `cond = condition.subs`, `base = base_set.subs` (`conditionset.py:246/248` post-patch) | which objects are forwarded to the constructor |

### The change being modeled
Pre-patch (`conditionset.py:242-246`):
```python
cond = self.condition.subs(old, new)
base = self.base_set.subs(old, new)
if cond is S.true:
    return ConditionSet(new, Contains(new, base), base)   # <-- uses `new` as binder
return self.func(self.sym, cond, base)
```
Post-patch (`conditionset.py:241-248`):
```python
else:
    cond = self.condition.subs(old, new)
    base = self.base_set.subs(old, new)
    # assumptions are ignored; consistent with __new__
    return self.func(self.sym, cond, base)               # <-- always the original binder
```
The discriminating change: when the substituted `cond` collapses to `S.true`, the
pre-patch code rebuilds the set with the **substituted value `new`** as the bound
symbol (and a `Contains(new, base)` condition); the post-patch code **always**
rebuilds with the **original** `self.sym`. `evalSubsFree`'s spec pins
`mkSet boundSym …`; `Solution_prepatch.lean` pins `mkSetOnValue new …` — the
pre-patch collapse-path shape verbatim — and fails G-DIFF.

Note that when `cond` does NOT collapse, even the pre-patch code already returned
`self.func(self.sym, cond, base)`, so the two versions differ ONLY on the
collapse path. The model `mkSet boundSym (substCond …) (substSet …)` is the
post-patch behavior on the whole branch (collapse or not), because post-patch the
rebuild is uniform; G-AX validates that uniform model against the real method on
both collapsing and non-collapsing inputs.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the Lean
value domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

The Lean side is **sorted**: a SymPy object's Lean carrier depends on which
constructor slot it inhabits, because the constructor is only defined on the right
kind of object in each slot (§3.3). The operation still never inspects internal
structure — only which object reaches which slot is observed.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a SymPy object in a plain slot (`old`, `new`, a binder seen as a value) | opaque `Obj` handle | identity-as-a-handle; the bijection preserves object identity. G-AX/G-CONF use concrete SymPy objects and observe structural equality (`==`, or `dummy_eq` for sets that differ only by bound-symbol naming). |
| a SymPy `Boolean` (what `as_Boolean` accepts) in the condition slot | `Cond` handle | identity-as-a-handle. The sort is exactly the constructor's condition-slot domain: `as_Boolean` (`conditionset.py:135`) raises `TypeError` on a non-Boolean, so a non-`Cond` in that slot is not a set-construction at all. |
| a SymPy `Set` in the base (component) slot | `SetObj` handle | identity-as-a-handle. The sort is exactly the constructor's base-slot domain: `raise TypeError('expecting set for base_set')` (`conditionset.py:141-142`). |
| the SymPy `Set` returned by the modeled branch | `BuiltSet` handle | identity-as-a-handle. Same Python type as a `SetObj` — the distinction is one of ROLE, not of type: the operation reads components and produces a result, and never feeds a result back into a component slot. Keeping the roles apart is what makes the substitution callee's receiver un-manufacturable (§3.4). |
| `old` in its substitution role (the `.subs` first argument) | `Old` handle | identity-as-a-handle; `oldObj old` is the same object seen in a plain slot. |
| `new` in its substitution role (the `.subs` second argument) | `New` handle | identity-as-a-handle; `newObj new` is the same object seen in a plain slot. |
| `self.sym` when it is a plain `Symbol` | `Binder` handle | identity-as-a-handle. The sort restricts the modeled domain to a single-symbol binder: the constructor is TOTAL for a `Symbol` binder over every condition and base (axiom_check.py obligation 7, 3780/3780 accepted inside the third precondition, §3.5) and PARTIAL for an `Expr`-but-not-`Symbol` binder (obligation 10; e.g. `ConditionSet(f(x), Contains(y, Interval(-1,1)), S.Reals)` raises `ValueError('non-symbol dummy not recognized in condition')`, `conditionset.py:180-183`). |
| `self.sym` viewed as an ordinary value (as `old != sym` views it) | `binderObj boundSym : Obj` | identity; the binder object itself. `old != self.sym` ↔ `old ≠ binderObj boundSym` (the `require`). |
| `x.subs(old, new)` (`Basic.subs`) on a condition / on a set | `substCond x old new` / `substSet x old new` | a pure function of `(whole, old, new)`; same inputs ⇒ structurally-equal SymPy object. Sort-preserving in both substitution directions (axiom_check.py obligation 6), so a substituted component is still legal in the slot it came from. The method never inspects the result, so no `ensures` is owed — but the callee is PARTIAL, and that domain is carried by the first two `Prop`s below (§3.4). |
| `self.condition.subs(old, new)` / `self.base_set.subs(old, new)` returns rather than raising | `CondSubDefined condition old new` / `BaseSubDefined baseSet old new` | an opaque predicate, true exactly on the pairs `(component, replacement)` the real callee is defined on. Not a fact about the result — nothing about a condition or a set follows from it — but a fact about the DOMAIN, so it appears as a `require` (§3.4). |
| `self.func(sym, cond, base)` (`ConditionSet` ctor, binder-keyed) | `mkSet sym cond base` | a pure function of `(binder, condition, base)`; same inputs ⇒ equal set (up to `__new__`'s own canonicalization, part of the unchanged callee). Result carrier `BuiltSet`. |
| `ConditionSet(v, Contains(v, s), s)` (same ctor, value-keyed) | `mkSetOnValue v s` | a pure function of `(value, set)`, result carrier `BuiltSet`. ONE set argument, used both as the set tested and the set bound over, because that is the sub-domain on which this shape is total (§3.3). |
| `self.func(...)` / `ConditionSet(...)` returns rather than raising, at EVERY set-building invocation the model can name at these arguments | `BuildsDefined boundSym condition baseSet old new` | an opaque predicate. Neither shape is total even on well-sorted slots: building the set tests the condition against the elements of a finite base (`conditionset.py:151-152`), so a non-comparable element makes the constructor signal. Like the two above it is a fact about the DOMAIN, not about a result, so it appears as a `require` — and it is bundled over all nameable invocations, which is what makes a discarded extra rebuild denote an accepted invocation (§3.5). |

The fourth `require` is the branch guard `old != self.sym` (the first two are the
substitution callee's non-sortal domain, §3.4, and the third is the
constructor's, §3.5); the other guard,
`isinstance(self.sym, Expr)` (`conditionset.py:209`), is carried by the `Binder`
sort together with the narrowing to `Symbol`. The excluded arms — the compound
(`Tuple`) binder early return (`conditionset.py:209-212`, return `self`
untouched), the `Expr`-but-not-`Symbol` binder sub-domain, and the
`old == self.sym` arm (dummy-symbol renaming, `conditionset.py:213-241`) — are all
UNCHANGED by the gold patch and not modeled; axiom_check.py exercises the `Tuple`
arm to confirm the identity behavior and exhibits the constructor's refusals on
the `Expr`-non-`Symbol` sub-domain.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `substCond` / `substSet` ↔ `Basic.subs` (A-reference, opaque, no `ensures`)
**Callee:** `sympy.core.basic.Basic.subs`, applied as `self.condition.subs(old, new)`
and `self.base_set.subs(old, new)` (`conditionset.py:243-244` pre / `246-247`
post). UNCHANGED by the gold patch (the patch only re-indents these two lines into
an `else` block and removes the `cond is S.true` special case beneath them).
One repo callee, two Lean axioms, because the sorts differ per slot: a substituted
condition must still be a condition and a substituted set must still be a set —
checked in both substitution directions by axiom_check.py obligation 6.
Modeled `opaque` with **NO asserted `ensures`** — the method never inspects the
substituted condition/base, only forwards them to the constructor (directive 7:
weakest sufficient contract = none). Its **domain** is a different matter: this
callee is PARTIAL, and §3.4 gives the two mechanisms that model that (the `Old` /
`New` sorts and the `SetObj`/`BuiltSet` split for the sortal part, the two
definedness preconditions for the rest). Tagged **A-reference**.

### 3.2 `mkSet` / `mkSetOnValue` ↔ `self.func` (the `ConditionSet` constructor) (A-reference, opaque, no `ensures`)
**Callee:** `ConditionSet.__new__` (`conditionset.py:117`), reached via `self.func`.
UNCHANGED by the gold patch. Modeled `opaque` with **NO asserted `ensures`** — the
method's sole responsibility is to choose WHICH binder/condition/base triple to
hand the constructor. Tagged **A-reference**.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL `ConditionSet._eval_subs`
on boundary + fuzzed `(set, old, new)` triples with `old != sym`, asserting that the
real result equals the deep model
`self.func(self.sym, self.condition.subs(old,new), self.base_set.subs(old,new))`
(the A-reference equality), including the load-bearing **collapse witnesses**
where `condition.subs(old,new) is S.true` (an ImageSet base, and an Interval base
where assumptions force the condition true) — the inputs on which the binder
choice is observable. Imports only `sympy`. Exit 0 iff sound.

### 3.3 The constructor is PARTIAL — how the sorts model its domain

`ConditionSet.__new__` is **not** a total function of three arbitrary handles: on
arguments outside its domain it RAISES instead of returning a set. At the base
commit it refuses, in this order:

| refusal | site | trigger |
|---|---|---|
| `TypeError` from `as_Boolean` | `conditionset.py:135` | the condition slot is not a `Boolean` |
| `TypeError('expecting set for base_set')` | `conditionset.py:141-142` | the base slot is not a `Set` |
| `ValueError('non-symbol dummy not recognized in condition')` | `conditionset.py:180-183` | the binder is not a `Symbol` **and** the condition does not mention it (a fresh `Dummy` substituted for the binder does not appear in the condition's free symbols) |
| `BadSignatureError` from `Lambda` | via `Union(know, rv)` → `ConditionSet._contains` | a non-`Symbol` binder survives into a set whose membership test is re-expressed as a `Lambda` |

Modelling such a callee as a **total** Lean function of unsorted handles is
unsound in a specific, general way: an impl may make an ADDITIONAL invocation of
it and DISCARD the result, and the weakest-precondition calculus cannot observe a
discarded application of a total function — so an impl whose returned value is
exactly `evalSubsSpec …` verifies even though the real code it denotes raises
before returning. On this instance's own F2P input that is not hypothetical: the
extra call `self.func(new, self.condition, self.base_set)` with `new = 1/3`
raises `ValueError('non-symbol dummy not recognized in condition')`, so the patch
does not resolve while the Lean file verifies.

The model therefore represents the domain by **sorting the argument slots** and by
providing **one axiom per real invocation shape**, so that every application the
model can express denotes an invocation the real constructor ACCEPTS, and an
invocation it would refuse is a Lean **type error** — unwritable, not merely
unproven, and unwritable even when its result is discarded:

* `mkSet : Binder → Cond → SetObj → BuiltSet` — the binder-keyed shape. Total on
  its sorts over the modeled domain: a `Symbol` binder with any of the pool's
  conditions and base sets is accepted (axiom_check.py obligation 7: 3780
  invocations, 0 refused). The three slot sorts are precisely the first three
  refusals above, and the `Symbol` narrowing of `Binder` is what avoids the third
  and fourth.
* `mkSetOnValue : Obj → SetObj → BuiltSet` — the value-keyed shape, an arbitrary
  object bound over the membership test of THAT object in the base set. The
  constructor accepts a non-`Symbol` binder exactly when the condition mentions
  it, and `Contains(v, s)` does mention `v`. Total on its sorts over the modeled
  domain (obligation 8: 84 invocations, 0 refused). It takes **one** set argument,
  used both as the set tested and the set bound over, because the cross-base
  variant `ConditionSet(v, Contains(v, s₁), s₂)` with `s₁ ≠ s₂` is NOT always
  accepted (obligation 10 exhibits `BadSignatureError` witnesses), so a two-set
  axiom would re-open the hole.

Neither totality claim is unconditional, and §3.5 is the rest of the story: the
constructor's domain is **not** exhausted by these sorts, so both claims are
qualified by the third precondition `BuildsDefined`.

A correspondence rule follows, and G-EQ audits the spec against it: an
**invocation** of the constructor is a SATURATED application of `mkSet` or
`mkSetOnValue`. A partial application (`mkSet boundSym newCond`, a
`SetObj → BuiltSet` value) denotes no invocation at all — no argument triple has
been assembled — so it is harmless; it cannot be saturated except with a `SetObj`,
which lands back inside the accepted domain.

Obligations 7 and 8 are what make the sorting an executable claim about the real
callee rather than a stipulation: they measure that the model is not STRICTER than
the real constructor on the shapes it admits, while obligations 9 and 10 exhibit,
for each excluded shape, a real invocation that IS refused — so the model is not
LOOSER either.

**What the sorts must NOT decide.** The question this instance is about is *which*
binder the rebuilt set carries: the set's own `self.sym`, or the substituted value
`new`. Sorting the slots must not answer that question by typing, or the
postcondition would be doing no work. It does not: both answers are well-sorted
and writable, `mkSet boundSym (substCond …) (substSet …)` and
`mkSetOnValue (newObj new) (substSet …)`, precisely because the value-keyed shape
is a real invocation shape of the same real callee — the one the deleted branch
used, whose own arguments the constructor accepts (obligation 8). The value-keyed
rebuild elaborates and is rejected by `ensures out = evalSubsSpec …` and by
nothing else; `Solution_prepatch.lean` is exactly that impl, and it fails G-DIFF
on the binder discrepancy. What the sorts remove is only the set of applications
the real callee would REFUSE — never a behaviour the real code could exhibit.

### 3.4 The SUBSTITUTION callee is PARTIAL too — sorted roles plus two preconditions

`Basic.subs` is likewise not a total function of `(component, old, new)`, and its
partiality has two distinct causes, which the model handles differently because
they are different kinds of fact.

**(a) The receiver and the substituted object.** Applied to a membership-style set
AT THAT SET'S OWN BINDER, with a replacement whose assumptions differ from the
binder's, `ConditionSet._eval_subs` reaches the dummy-renaming arm and raises
`ValueError('A dummy symbol can only be replaced with a symbol having the same
assumptions…')` (`conditionset.py:225-231`). This is a fact about WHICH
substitutions exist, so it is carried by SORTS, exactly as in §3.3:

* `substCond : Cond → Old → New → Cond` and `substSet : SetObj → Old → New → SetObj`.
  The two substitution arguments have sorts of their own, so the only substitution
  the model can name is the one the operation was handed: not the reverse
  direction (`substCond condition new old` does not typecheck), not one keyed on
  the set's own binder (`substSet baseSet (binderObj boundSym) new` does not
  either), and not one that reuses a plain object in a substitution role.
* The receiver of `substSet` is a `SetObj`, and the constructor produces a
  `BuiltSet`. So a receiver the model can name is the stored base set or a
  substituted form of it — never a set the impl MANUFACTURED and then substituted
  into. That closes the shape the previous model admitted:
  `substSet (mkSet boundSym condition baseSet) (binderObj boundSym) new`, whose
  real counterpart raises on this instance's own kind of input (a negative-symbol
  binder with a positive replacement over `Interval(0, oo)`).

**(b) The replacement itself.** Independently of any binder, a relational
condition cannot be compared against every object: `(y > 0).subs(y, I)` raises
`TypeError('Invalid comparison of non-real I')`, and `zoo` / `nan` raise likewise.
No sorting can express this — the offending arguments are ordinary objects in
ordinary roles — and it is not a fact about the callee's RESULT either, because on
those inputs there is no result: the error propagates out of `_eval_subs`, so the
real operation returns nothing at all. Under `loom.semantics.termination "total"`
the contract PROMISES a result, so it may only promise one where the real
operation has one. Hence the two preconditions

```
require CondSubDefined condition old new
require BaseSubDefined baseSet old new
```

which are opaque: nothing about a condition or a set is derivable from them, they
only record that the callee delivers a value here. They are **domain facts**, not
consumed `ensures` — no proof step uses them other than to be discharged by the
caller — and because of (a) they cover EVERY substitution the model can name, one
per slot.

Obligations 11–15 make all of this executable rather than stipulated:
11 exhibits both refusal kinds on real objects; 12 measures that the preconditions
are non-vacuous and hold on the F2P input the problem statement exhibits;
13 measures that they are SUFFICIENT — on every pool input they admit, the real
`_eval_subs` returns normally, 0 refusals, which is what licenses a
total-correctness contract; 14 measures that the domain is closed under the
re-application the model can still express (`substCond (substCond c old new) old new`
is writable, so it must be defined); and 15 enumerates every extra invocation
shape the sorts still let an impl name and measures that the real callees accept
all of them (72 shapes on the boundary cases, plus 41904 nameable set-building
invocations on the admitted pool inputs, 0 refused) — the model is not stricter
than the real code, only as strict.

### 3.5 The CONSTRUCTOR's partiality is not sortal either — the third precondition

Sorting the three slots is **not** the constructor's whole domain. Before it
returns, `ConditionSet.__new__` TESTS THE CONDITION AGAINST THE ELEMENTS of a
finite base:

```
# conditionset.py:151-152
sifted = sift(base_set, lambda _: fuzzy_bool(condition.subs(sym, _)))
```

so a base element the condition cannot be compared against makes it raise with
every slot holding exactly the kind of object it asks for:

| refusal | trigger | witness |
|---|---|---|
| `TypeError('Invalid comparison of non-real I')` | a relational condition sifted over a base holding a non-real element | `ConditionSet(x, x > 0, FiniteSet(I))` |
| `TypeError('Invalid NaN comparison')` | the same with `nan` / `zoo` | `ConditionSet(n, n >= 1, FiniteSet(nan))` |
| `ValueError('non-symbol dummy not recognized in condition')` | the value-keyed shape when the membership test ABSORBS the object it tests (it is solved against the set's own description, so the condition no longer mentions the object being bound) | `ConditionSet(zoo, Contains(zoo, ImageSet(Lambda(k, 2πk + zoo), ℤ)), …)` |

On this instance that is reachable **inside** the two substitution preconditions,
which is what makes it a defect of a model that stops at §3.3–§3.4 rather than a
curiosity. The exhibit (axiom_check.py obligation 16, measured on the PRE-PATCH
source so it is a property of the unchanged callee):

```
C = ConditionSet(x, x > 0, FiniteSet(z));  old, new = z, I
C.condition.subs(z, I)  ->  x > 0          # CondSubDefined HOLDS
C.base_set.subs(z, I)   ->  FiniteSet(I)   # BaseSubDefined  HOLDS
z != C.sym              ->  True           # the branch guard HOLDS
C.func(C.sym, x > 0, FiniteSet(I))  ->  TypeError('Invalid comparison of non-real I')
C._eval_subs(z, I)                  ->  the same TypeError, propagated
```

The real operation has NO result here, so under `loom.semantics.termination
"total"` the contract must not promise one. Hence the third precondition

```
require BuildsDefined boundSym condition baseSet old new
```

opaque like the other two, consumed by no proof step, and taking all five of the
operation's arguments because of what it has to cover:

**It ranges over every set-building invocation the model can NAME, not only the
one the contract returns.** That is deliberate, and it is what licenses treating
`mkSet` / `mkSetOnValue` as TOTAL functions of their sorts — the property §3.3
relies on when it argues that a discarded extra call is unwritable rather than
invisible. The enumeration is finite and complete: the only nameable binder is the
set's own; the only nameable objects are that binder, `oldObj old` and
`newObj new`; the only nameable components are the stored condition / base set and
their images under the ONE substitution the `Old` / `New` sorts admit (enumerated
to depth 2, with obligation 14 measuring that a further application changes
nothing — idempotent on 2328/2328 admitted pool inputs); and the only two shapes
are the binder-keyed and the value-keyed one. That is 9 + 9 = 18 invocations per
input, all measured.

**Price, measured rather than asserted.** Over the pool the precondition excludes
19 of the 2347 inputs the two substitution preconditions admit. 6 of the 19 are
excluded because the constructor refuses the operation's OWN rebuild — and the
real `_eval_subs` raises on all 6, so that clause is exactly as strict as the
operation itself (obligation 16). The other 13 are excluded only because a
writable EXTRA shape is refused, and there the real operation returns normally:
those inputs are the sliver of the operation's domain the model gives up in
exchange for building axioms that are total on their sorts. Giving it up is
conservative — the contract is silent there rather than over-strong — and 13 of
2347 inputs (0.6%) is not where the behaviour under change lives: the F2P witness
and the second example the problem statement displays both satisfy the
precondition (obligation 17). G-CONF checks the same claim on the consumer side:
it computes the shadow's rebuild FIRST and, where the constructor refuses it,
skips the input and asserts that the patched `_eval_subs` refuses it too.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`19495`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `evalSubsSpec`'s binder choice to Python (the R/I-tagged op:
rebuild with the ORIGINAL `self.sym`) and leaves the unchanged callees as the real
`Basic.subs` and the real `ConditionSet` constructor (A-tagged → run the real
callee). It diffs the resulting set (via `dummy_eq`, which equates sets differing
only by bound-symbol name, plus exact `==`) against the patched
`ConditionSet._eval_subs` over ≥10⁵ fuzzed `(set, old, new)` inputs, drawing
binders from a `Symbol` pool to match the `Binder` sort (§2).
