# mapping.md — sympy__sympy-19495

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 25fbcce5b1a4c7e3956e6062930f4a44ce95a632`, states the type
abstraction, and gives the provenance of the deeply-modelled (A-reference)
reduction.

Repo file under change: `sympy/sets/conditionset.py`. All line numbers below are
**base_commit** line numbers; the gold patch shifts everything after line 116 by
−2 because it deletes two docstring lines, and it changes no line inside
`__new__`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `replace_free_parameter(self_sym, new, cond_after, base_after, base_kind, listed_kind, listed_base, merged_sym, merged_base)` | `ConditionSet._eval_subs(self, old, new)` — `sympy/sets/conditionset.py:208`; the `old != sym` branch, body lines **243-247** | the modeled changed behaviour (free-parameter substitution into a `ConditionSet`) |
| `build(sym, cond, base, base_kind, listed_kind, listed_base, merged_sym, merged_base)` *(deep model — A-reference)* | `ConditionSet.__new__(cls, sym, condition, base_set)` — `sympy/sets/conditionset.py:117`; the reduction ladder at lines **125-159**, **161-179** and **187-188** | the unchanged constructor the patched branch calls via `self.func(...)`; its reduction rule, modelled deeply and validated by G-AX |
| `Result0` (kind/sym/base/cond) | the value `ConditionSet._eval_subs` returns: `S.EmptySet`, a base domain, or a `ConditionSet` instance | minimal carrier of the observed fields of the result |
| `COND_FALSE / COND_TRUE / COND_OPEN` | the truth status **the constructor itself assigns** to the predicate and then branches on: `condition is S.false` / `condition is S.true` / otherwise (lines **144**, **146**) — evaluated on the *normalized* predicate, i.e. after the explicit-listing rewrite (lines **125-134**) and after `condition = as_Boolean(condition)` (line **136** → `sympy/logic/boolalg.py:20-58`) | 3-valued truth status of the substituted predicate |
| `BASE_EMPTY / BASE_LISTED / BASE_MERGED / BASE_PLAIN` | `isinstance(base_set, EmptySet)` (line **148**) / `isinstance(base_set, FiniteSet)` (line **152**) / `isinstance(base_set, cls)` (line **161**) / any other `Set` | shape of the base domain, which selects which reduction applies — four values because `__new__` dispatches on four shapes |
| `listed_kind / listed_base` | the outcome of the member-by-member decision over an explicitly listed base domain: `sift(base_set, lambda _: fuzzy_bool(condition.subs(sym, _)))` at lines **152-159**, combined with `return rv if know is None else Union(know, rv)` at line **188** | the surviving object's kind and base-domain identity for a listed base domain |
| `merged_sym / merged_base` | the outcome of the condition-MERGING branch at lines **161-179**: `s, c, base_set = base_set.args`, the four branches that settle `sym` (`sym == s` ⇒ keep; `sym not in c.free_symbols` ⇒ keep; `s not in condition.free_symbols` ⇒ `sym = s`; else `Symbol('lambda')`, or `Dummy('lambda')` if that name is taken), and the INNER `base_set` the merged object then stands over; then the check at lines **181-185** applied to the binder just settled on, whose refusing outcome is `merged_sym == MERGE_REFUSED`, on which the result is the pinned `K_REFUSED` (§3.1.1) | the bound variable the merge settles on and the domain the merged object ranges over, plus whether the construction then refuses that bound variable outright |
| `MERGE_REFUSED` | the `raise ValueError('non-symbol dummy not recognized in condition')` at lines **184-185**, reached with the binder the MERGE settled on (lines 161-179), i.e. `not isinstance(sym, Symbol)` **and** `Dummy('lambda') not in condition.xreplace({sym: Dummy('lambda')}).free_symbols` | that the merge settled on a binder the construction refuses, so no domain is delivered; the result is `K_REFUSED` — see §3.1.1 |
| `K_EMPTY / K_BASE / K_SET` | result is `S.EmptySet` / a base domain (or a `Union`/`FiniteSet` of surviving members) / a `ConditionSet` | 3-valued kind of the canonical result |

The pre-patch repo construct the change removes (audited in refinement.md, NOT
referenced from the consumer spec view): the special case
`if cond is S.true: return ConditionSet(new, Contains(new, base), base)`
(`conditionset.py:245-246` @ base_commit), which rebuilt the set keyed on the
replacement value `new`.

### 1.1 Why the truth tag is the *normalized* status (correction)

An earlier revision of this file said the tag was `cond is S.true` /
`is S.false` applied to the substituted predicate **as written**. That was a
false statement about the callee, and it made the interpretation of the model
wrong on a family of inputs the model does admit. `ConditionSet.__new__`
normalizes before it branches:

```python
if isinstance(condition, FiniteSet):      # 125-134: listing of expressions
    condition = And(*(Eq(lhs, 0) for lhs in condition))
condition = as_Boolean(condition)         # 136
...
if condition is S.false:                  # 144
    return S.EmptySet
elif condition is S.true:                 # 146
    return base_set
```

and `as_Boolean` (`sympy/logic/boolalg.py:20-58`) maps `1`/`0` to `S.true`/
`S.false`, maps a `Symbol` to `S.true`/`S.false` whenever its `.is_zero` is
decided, returns an already-`Boolean` predicate unchanged, and otherwise raises
`TypeError`. So a predicate that arrives as a bare symbol and is replaced by a
number, or by a symbol carrying a `zero=`/`nonzero=` assumption, **is a decided
predicate as far as the construction is concerned**, and the construction
reduces on it. Measured on the real patched code at base_commit:

| input | real `_eval_subs` result | tag the constructor assigns |
|---|---|---|
| `ConditionSet(x, y, Reals)._eval_subs(y, 1)` | `Reals` | `COND_TRUE` |
| `ConditionSet(x, y, Reals)._eval_subs(y, 0)` | `EmptySet` | `COND_FALSE` |
| `ConditionSet(x, y, Reals)._eval_subs(y, Symbol('c', nonzero=True))` | `Reals` | `COND_TRUE` |
| `ConditionSet(x, y, Reals)._eval_subs(y, Symbol('d', zero=True))` | `EmptySet` | `COND_FALSE` |
| `ConditionSet(x, y, Reals)._eval_subs(y, FiniteSet(0))` | `Reals` | `COND_TRUE` |
| `ConditionSet(x, y, Reals)._eval_subs(y, FiniteSet(1, 2))` | `EmptySet` | `COND_FALSE` |
| `ConditionSet(x, y, Reals)._eval_subs(y, 2)` | raises `TypeError` | *no tag* (out of domain, §G-CONF) |

The model's clauses were and are correct — nothing in `model.py` changed to
settle this. What was wrong was the abstraction function stated here and
implemented in `conformance_check.py`'s `cond_tag`, which tagged all seven rows
`COND_OPEN` and so read the spec as pinning `K_SET` where the real code (both
with and without the gold patch — the tail these inputs reach is the UNCHANGED
constructor) delivers the base domain or the empty domain. `cond_tag` now
replays lines 125-134 and 136 with the repo's own `as_Boolean`, a folded-in
unchanged callee exactly like the two `.subs` calls and `sift`/`fuzzy_bool`.

### 1.2 Why the merge is modelled, and why the result's kind is read by value (correction)

A second false statement lived in §3.1 below: it declared a base domain that is
itself a `ConditionSet` **out of scope** on the ground that it is "not reachable
by the substitutions this branch performs", with "Measured: 0 samples in 100000
comparisons". The reachability claim is wrong, and the measurement was an
artefact of a pool that contained no compound base domains. A `Union` base whose
other part collapses under the replacement leaves the bare inner `ConditionSet`,
and then `__new__`'s merging branch runs and can rename the bound variable.
Measured on the real patched code at base_commit:

| input | real `_eval_subs` result | binder branch (lines 161-179) |
|---|---|---|
| `ConditionSet(x, x<y, Union(Interval(0,y), ConditionSet(z, x+z>0, Reals))).subs(y,-1)` | `ConditionSet(z, (z<-1) & (x+z>0), Reals)` | `s not in condition.free_symbols` ⇒ `sym = s` |
| `ConditionSet(x, x<y, Union(Interval(0,y), ConditionSet(z, z<2, Reals))).subs(y,-1)` | `ConditionSet(x, (x<-1) & (x<2), Reals)` | `sym not in c.free_symbols` ⇒ keep `sym` |
| `ConditionSet(z, z<y, Union(Interval(0,y), ConditionSet(z, x+z>0, Reals))).subs(y,-1)` | `ConditionSet(z, (z<-1) & (x+z>0), Reals)` | `sym == s` ⇒ keep `sym` |
| `ConditionSet(x, (x<z) & (x<y), Union(Interval(0,y), ConditionSet(z, x+z>0, Reals))).subs(y,-1)` | `ConditionSet(lambda, (lambda<-1) & (lambda<z) & (lambda+x>0), Reals)` | both cross-occur ⇒ `Symbol('lambda')` |
| the same with a symbol literally named `lambda` in the predicate | `ConditionSet(_lambda, …)` (a `Dummy`) | the name is taken ⇒ `Dummy('lambda')` |
| `ConditionSet(x, Contains(y,[-2,0]), Union(Interval(0,y), ConditionSet(z, x+z>0, Reals))).subs(y,-1)` | `ConditionSet(z, x+z>0, Reals)` — the inner object handed straight back | none: `condition is S.true` pre-empts at line 146 |
| `ConditionSet(z, z<y, Union(Interval(0,y), ConditionSet(z, z>=-1, Reals))).subs(y,-1)` | `ConditionSet(z, False, Reals)` | `sym == s`; **no further reduction** after the merge |

So the model owed a clause here and did not have one. The repair is **more**
specification, not less: `base_kind` gains a fourth value `BASE_MERGED`, the
merge's outcome is folded into `merged_sym` / `merged_base` exactly as the
listing decision is folded into `listed_kind` / `listed_base`, and both
`build` and `replace_free_parameter` gain

```python
Ensures(Implies(cond == COND_OPEN and base_kind == BASE_MERGED,
                Result().kind == K_SET and Result().sym == merged_sym
                and Result().base == merged_base))
```

No `Requires` was narrowed to push the divergent input out of the domain: the
admitted `base_kind` set grew from three values to four, and the domain
`conformance_check.py` compares over grew with it (`domain_rejected` is now 0
because nothing is excluded by base shape at all — the base-shape scope is every
`Set`).

The last row of the table settles a second, smaller thing. The merged object is
delivered with **no re-reduction** (the branch falls through to `Basic.__new__`
at line 187), so it can carry an identically false predicate and still stand.
The model therefore claims `kind`, `sym` and `base` for the merge but **not**
`cond == COND_OPEN`, which it does claim on every other `K_SET` shape. That is
a faithful reading, not a hole: a rival that returned the empty domain here
would contradict the clause's `Result().kind == K_SET`.

The sixth row settles a third: when the predicate collapses to true and the base
domain is itself a restricted object, `condition is S.true` hands that object
straight back. The model calls that `K_BASE` ("the base domain passes through"),
but an abstraction function that read `kind` off the *Python type* of the
returned value would call it `K_SET` and report a spurious divergence. So the
result abstraction (§2 row 6) tests equality with the replacement-applied base
domain BEFORE it tests `isinstance(_, ConditionSet)`: `kind` classifies the
reduction's outcome, not the shape of the value.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a SymPy `Symbol` (`self.sym`, `new` when it is a symbol/value) | `int` identity id | only the *identity* of the bound symbol matters to the tested behaviour (which symbol heads the result, and whether it is `self.sym` vs `new`); distinct symbols ↦ distinct ids, the same symbol ↦ the same id. |
| a SymPy predicate `self.condition.subs(old,new)` | an `int` truth tag `COND_FALSE/TRUE/OPEN` | the constructor branches on the truth status it assigns to the predicate after normalizing it (§1, §1.1): `as_Boolean(listing-rewrite(cond)) is S.true / is S.false / otherwise`. The two `.subs` calls that produce the predicate are folded into the model's `cond_after` argument (R, refinement.md step 3). A predicate the constructor refuses to read as a truth value has no carrier and is out of domain (§G-CONF). |
| a SymPy `Set` `self.base_set.subs(old,new)` | an `int` identity id | observed only for equality with the result's base domain; `.subs` on the base is folded into the model's `base_after` argument. |
| the *shape* of that base domain | `BASE_EMPTY / BASE_LISTED / BASE_MERGED / BASE_PLAIN` | `isinstance(_, EmptySet)` / `isinstance(_, FiniteSet)` / `isinstance(_, ConditionSet)` / any other `Set`. This is an observed input, not an opaque id, because the reduction the constructor performs depends on it (lines 148, 152, 161). |
| the constructor's member-by-member decision over a listed base domain | `listed_kind` (a `K_*`) + `listed_base` (an `int` identity id) | `sift` + `fuzzy_bool` at lines 152-159 and the `Union(know, rv)` join at line 188, replayed with the repo's own helpers and abstracted like any other returned object. Folded into caller-supplied arguments exactly as `cond_after`/`base_after` are. |
| the constructor's MERGE with a base domain that is itself a restricted object | `merged_sym` + `merged_base` (an `int` identity id each) | lines 161-179 replayed with the constructor's own four branches, followed by the lines-181-185 check on the binder they settle on; folded into caller-supplied arguments exactly as `cond_after`/`base_after`/`listed_*` are. A fresh internal name (`Dummy('lambda')`) is not observable — no caller can write it and its identity differs between evaluations — so every `Dummy` maps to one reserved id (`-1`). Real identity ids are `>= 1`, so `0` is free and carries `MERGE_REFUSED`: the merge settled on a binder the construction refuses outright, i.e. there is no domain and no binder identity to name; the spec pins that outcome as the fourth result kind `K_REFUSED` (§3.1.1). The load-bearing distinction is unaffected: a result keyed on the replacement value is always a *named* `Symbol`. |
| the returned object (`EmptySet` / base domain / `ConditionSet`) | `Result0` with `(kind, sym, base, cond)` | `K_EMPTY ↔ S.EmptySet`; `K_BASE ↔ a base domain passes through` (including `FiniteSet(*survivors)`, `Union(know, rv)`, and the base domain itself when it is a restricted object handed back by line 146); `K_SET` ↔ a newly built restricted object `ConditionSet(sym, …, base)`, with `Result0.sym` the bound symbol id. `kind` classifies the reduction's outcome, so the pass-through test (equality with the replacement-applied base domain) comes before the `isinstance(_, ConditionSet)` test — see §1.2. |

Rich-object field access / indexing is banned in Nagini, so the carriers are
`int` ids + a minimal `Result0` class; the specification is phrased over those.

## 3. Deep-model provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `build` ↔ `ConditionSet.__new__` reduction (A-reference)
**Callee:** `ConditionSet.__new__` (`sympy/sets/conditionset.py:117`). The
patched branch returns `self.func(self.sym, cond, base)`, where `self.func` is
`ConditionSet`; constructing a `ConditionSet` runs `__new__`, whose reduction
ladder is (base_commit lines 125-159, 187-188):

```python
if isinstance(condition, FiniteSet):        # 125-134  listing of expressions
    condition = And(*(Eq(lhs, 0) for lhs in condition))
condition = as_Boolean(condition)           # 136      normalize to a truth value
if condition is S.false:                    # 144
    return S.EmptySet
elif condition is S.true:                   # 146
    return base_set
if isinstance(base_set, EmptySet):          # 148
    return base_set
know = None
if isinstance(base_set, FiniteSet):         # 152-159  decide member by member
    sifted = sift(base_set, lambda _: fuzzy_bool(condition.subs(sym, _)))
    if sifted[None]:
        know = FiniteSet(*sifted[True]); base_set = FiniteSet(*sifted[None])
    else:
        return FiniteSet(*sifted[True])
if isinstance(base_set, cls):               # 161-179  MERGE the restrictions
    s, c, base_set = base_set.args          #          (base_set becomes INNER)
    if sym == s:                 condition = And(condition, c)
    elif sym not in c.free_symbols:
                                 condition = And(condition, c.xreplace({s: sym}))
    elif s not in condition.free_symbols:
                                 condition = And(condition.xreplace({sym: s}), c)
                                 sym = s
    else:
        dum = Symbol('lambda')              #          a fresh internal name,
        if dum in condition.free_symbols or dum in c.free_symbols:
            dum = Dummy(str(dum))           #          or a Dummy if it is taken
        condition = And(condition.xreplace({sym: dum}), c.xreplace({s: dum}))
        sym = dum
...                                         # NO further reduction from here on
rv = Basic.__new__(cls, sym, condition, base_set)   # 187
return rv if know is None else Union(know, rv)      # 188
```

`build` encodes precisely this ladder, in this order: false ⇒ empty domain;
empty base domain ⇒ empty domain; true ⇒ the base domain; listed base domain ⇒
the folded member-by-member outcome (`listed_kind`, `listed_base`); a base domain
that is itself a restricted object ⇒ the folded merge outcome (`merged_sym`,
`merged_base`) — the one shape whose bound variable the reduction, not the
caller, settles; otherwise a restricted object keyed on `sym` over that base
domain. The sifting branch and the merging branch cannot both run: after sifting,
`base_set` is a `FiniteSet`, so `isinstance(base_set, cls)` is false — the four
`base_kind` values really are a partition. This is an UNCHANGED callee modelled
deeply, **not** axiomatized.

**Declared scope, and what is left out.** Every base-domain shape is modelled
(see §1.2, which corrects an earlier revision that wrongly excluded the merging
branch and wrongly claimed it unreachable). Two shapes of `__new__` are outside
the model, and each is counted and reported by `conformance_check.py` rather
than silently dropped:

1. **a predicate the constructor refuses to read as a truth value** (line 136
   raising `TypeError('expecting bool or Boolean, not ...')`, e.g. a substituted
   `2` or `nan`): there is no `COND_*` carrier for it, so the model admits no
   such input. The operation delivers no object at all — measured, both
   `cs._eval_subs(old, new)` and the public `cs.subs(old, new)` raise the same
   `TypeError`.
2. **a bound variable the CALLER supplies that is not a `Symbol`** (the
   `Tuple`-sym syntax at lines 138-139, which skips the ladder entirely; and a
   compound `Expr` binder, which reaches the check at lines 181-185): the
   `int`-identity carrier of §2 row 1 is declared for a `Symbol`, and the model
   admits no other binder from the caller. Measured: `nonsymbol_binder: 0` —
   the pool's binders are all `Symbol`s, so this exclusion is declared but not
   the one that bites.

### 3.1.1 The lines-181-185 check is on the SETTLED binder, and is not `isinstance` (correction)

An earlier revision of §3.1 folded the lines-181-185 check into exclusion 2
above, as though it were a property of the caller's binder. Both halves of that
were wrong about the callee, and together they made the model assert a delivered
object where the real constructor raises.

*The binder it tests is the one the reduction SETTLED on, not the caller's.* The
check sits AFTER the merge (lines 161-179), and merge branch 3 assigns `sym = s`
— it ADOPTS the inner object's binder. An inner binder may be a compound `Expr`
while the caller's is an ordinary `Symbol`, so line 181 sees a non-`Symbol`
on inputs exclusion 2 does not cover. This is exactly the intersection §1.2
opened by widening `base_kind` to include `BASE_MERGED`, and the scope statement
was not re-derived for it.

*And the check is not `isinstance(sym, Symbol)`.* A compound settled binder is
refused only when a fresh `Dummy` substituted for it leaves NO trace in the
conjoined predicate:

```python
if not isinstance(sym, Symbol):          # 181
    s = Dummy('lambda')
    if s not in condition.xreplace({sym: s}).free_symbols:   # 183
        raise ValueError('non-symbol dummy not recognized in condition')
```

So a compound settled binder the merged predicate still mentions is **accepted**,
and the object stands keyed on that compound expression. Measured on the real
patched code at base_commit:

| input (all with `.subs(y, -1)`, outer binder `z` a plain `Symbol`) | real result |
|---|---|
| `ConditionSet(z, z<=0, Union(Interval(0,y), ConditionSet(x+1, (z<5)&(x+1>0), Reals)))` | raises `ValueError` — the conjoined predicate collapses, no trace of `x+1` |
| `…ConditionSet(x+1, (z<5)&Contains(x+1,Interval(0,1)), Reals)…` | `ConditionSet(x + 1, (z<5)&(x+1<=0)&Contains(x+1,Interval(0,1)), Reals)` — **delivered**, keyed on `x+1` |
| `…ConditionSet(x+1, (z<5)&(sin(x+1)>0), Reals)…` | `ConditionSet(x + 1, (z<5)&(x+1<=0)&(sin(x+1)>0), Reals)` — **delivered** |
| `…ConditionSet(x**2, (z<5)&(sin(x**2)>0), Reals)…` | `ConditionSet(x**2, …)` — **delivered** |
| `ConditionSet(x, Contains(y,Interval(-2,0)), Union(Interval(0,y), ConditionSet(x+1,(z<5)&(x+1>0),Reals)))` | `ConditionSet(x + 1, (z<5)&(x+1>0), Reals)` — **delivered**; `condition is S.true` pre-empts at line 146, so the check is never reached |

Sweeping compound inner binders (`x+1`, `2*x`, `x**2`, `2*x+3`, `x+w`) × inner
predicates × outer predicates: 15 refuse and 45 deliver. So the honest scope is
the REFUSAL itself, not compound settled binders as a class. Excluding the whole
class would have dropped those 45 delivered results — real behaviour on which the
merge clause is correct as written.

The model therefore gains `MERGE_REFUSED`, a distinguished value of the existing
`merged_sym` carrier (real identity ids are `>= 1` and the fresh-name id is `-1`,
so `0` is free), which reports that the merge settled on a binder the
construction refuses.

**The refusal is PINNED, not excluded.** A first attempt guarded the merge clause
with `merged_sym != MERGE_REFUSED` and stopped there, leaving that sliver
unconstrained. Three rivals written against it verified while doing something the
real constructor never does (delivering a set keyed on the replacement value;
echoing the arguments; returning a fabricated domain), so claiming nothing there
was a hole and not a scope limit. The model instead names the outcome: a fourth
result kind `K_REFUSED`, with three clauses per operation —

* merge accepted (`merged_sym != MERGE_REFUSED`) ⇒ the merge clause as before;
* merge refused ⇒ `Result().kind == K_REFUSED`;
* everywhere else ⇒ `Result().kind != K_REFUSED` (a refusal cannot be invented on
  an input the constructor answers).

Both operations therefore stay TOTAL — they always deliver an answer, and on those
inputs the answer is the refusal — and the reduction is pinned on the whole
admitted domain. No precondition was narrowed and the witness stays admissible.

`merged_outcome` replays lines 181-185 on the binder the merge settled on and on
the CONJOINED predicate. `conformance_check.py` then compares that leg in BOTH
directions rather than skipping it: the shadow is required to return `K_REFUSED`,
the real `_eval_subs` is required to refuse with that identical `ValueError` (via
the same `_refusal` cross-check the other exclusions use, never assumed), any
compared input on which the shadow claims `K_REFUSED` while the real method
delivers is reported as a disagreement, and the leg is counted
(`merge_refused_binder`) so a run that never reaches it FAILS rather than quietly
measuring a weaker claim. Measured on the gold-applied worktree at base_commit:
100000 comparisons, 0 disagreements, `merge_refused_binder: 3`,
`base_merged: 3535` of which `merge_renamed_binder: 1609`.

Note this is a refusal of the UNCHANGED tail: measured with the gold patch
WITHHELD, all 45 inputs of the witness class produce the identical result
pre- and post-patch (45/45), so the correction does not touch the patch's own
behaviour change.

To these `conformance_check.py` adds a further counted exclusion that is not a
scope limit on `build` but an absence of any result to compare: **a replacement
on which the operation itself raises** — either the substitution (`nan`, `I`,
a `FiniteSet` into a comparison) or the constructor's own `sift`/`fuzzy_bool`
decision over a listing (a predicate symbol reused as a listed real member).
The script does not assume these deliver nothing: it *requires* the real
`_eval_subs` to refuse the input with the identical exception, and reports a
disagreement if the real method instead returns a value.

All of these are refusals of the UNCHANGED code, and were measured to be
byte-identical at base_commit with and without the gold patch (the inputs that
reach them are on the shared tail, and the pre-patch special case they would
otherwise hit is not entered). So no part of the behaviour under specification
hides inside them.

### 3.2 `replace_free_parameter` ↔ `_eval_subs` free-symbol branch (A-reference)
**Callee:** the post-patch `ConditionSet._eval_subs` tail
(`conditionset.py:243-247` @ base_commit → the `else` block post-patch):
`cond = condition.subs(old,new)`, `base = base_set.subs(old,new)`,
`return self.func(self.sym, cond, base)`. The model encodes that the rebuilt
object keeps the ORIGINAL bound symbol `self.sym`, and that the rebuild is the
same reduction ladder of §3.1 applied to `(cond_after, base_after)`.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL post-patch SymPy:
- §[1] `ConditionSet.__new__` on false/true/open predicates over four base
  domains (`Integers`, `Reals`, `[0,∞)`, `[-1,1]`), asserting `build`'s kind
  (empty/base/set) and that the open case is keyed on the original symbol.
- §[2] the full `_eval_subs` free-symbol branch on four cases — including the
  issue-17341 input `ConditionSet(x, Contains(y,[-1,1]), imageset(λk.2kπ+asin
  (y), ℤ)).subs(y, 1/3)` and the F2P regression `ConditionSet(n, n<x,
  [-∞,0]).subs(x, p)` (negative `n`, positive `p`) — asserting the model's
  predicted `(kind, bound symbol)` matches and the bound symbol is `self.sym`,
  never `new`. It asserts the headline `…dummy_eq(imageset(λk.2kπ+asin(1/3),ℤ))`.
- §[3] the normalization family of §1.1: that the constructor assigns
  `COND_TRUE`/`COND_FALSE` to a predicate given as `1`/`0`, as a symbol whose
  `.is_zero` is decided either way, and as an explicit listing of expressions;
  that an undecided symbol stays `COND_OPEN`; and that the two declared refusals
  (a predicate with no truth value, a non-`Symbol` binder) behave as §3.1
  states. It also checks that a `ConditionSet` base really does merge and rename,
  and that `merged_outcome` replays the same binder.
- §[4] the base-domain shape ladder: an empty base domain, and a listed base
  domain whose members the predicate refutes / admits / leaves undecided.
- §[5] the condition-MERGING branch (§1.2) in its own right: all four binder
  outcomes including `Symbol('lambda')` and the `Dummy` collision, the merged
  object standing over the INNER base domain, the conjoined predicate containing
  both restrictions, both truth reductions pre-empting the merge, and the
  no-further-reduction property — that `ConditionSet(z, z<-1,
  ConditionSet(z, z>=-1, Reals))` really is a standing restricted object whose
  predicate normalizes to `False` and which is NOT the empty domain, reached
  through the modeled operation as well as directly.
  *(Negative control: making `merged_outcome`'s third branch keep the outer
  variable instead of adopting the inner one turns §[1], §[2] and §[5] red with
  9 violations, so these checks are not vacuous.)*
- Exit 0 iff every observation agrees. Imports only `sympy` (the patched module)
  + stdlib; nothing else.

No flag dependency (no floats; no kwargs/defaults beyond `base_set=S.UniversalSet`
which is not exercised in this branch).

## G-CONF (differential conformance)

`conformance_check.py` diffs the contract-stripped `# impl-start`/`# impl-end`
regions of `model.py` (`replace_free_parameter` → `build` → `Result0`, copied
verbatim; the `pure` region is empty and no `@ContractOnly` axiom exists, so
nothing is transliterated and no `PSeq` shim is needed) against the REAL patched
repo method, **called** in-container: `ConditionSet._eval_subs`
(`sympy/sets/conditionset.py:208` @ base_commit, §1), on its `old != sym`
branch. Each input also cross-checks that the public `cs.subs(old, new)` yields
the same value, so the modeled private branch is confirmed reachable.

**Bridge (§2, inverted).** Concrete first: a real `ConditionSet`, a real free
symbol `old`, a real replacement `new`. The real `Basic.subs` calls produce
`cond_after` / `base_after`; those are abstracted into the model's carriers —
`Symbol`/`Set` ↦ interned `int` identity id, base domain ↦ its shape tag,
predicate ↦ `COND_FALSE/TRUE/OPEN` **as the constructor itself assigns it**
(listing rewrite + `as_Boolean`, then `is S.false` / `is S.true` / otherwise:
§1.1). The member-by-member outcome for a listed base domain is replayed with
the repo's `sift`/`fuzzy_bool`; the MERGE outcome for a base domain that is
itself a restricted object is replayed with the constructor's own four branches
(§1.2, `merged_outcome`). The oracle's return value is abstracted the same way
(`S.EmptySet` ↦ `K_EMPTY`; a value equal to the replacement-applied base domain
↦ `K_BASE`; else a `ConditionSet` ↦ `K_SET` with its `.sym`/`.base_set`, and
anything else ↦ `K_BASE`) and compared to `Result0` on exactly the fields
`replace_free_parameter`'s `Ensures` observe — which for the merge are `kind`,
`sym` and `base` but not `cond`, because the spec claims no truth status there
(§1.2).

**Domain.** Every compared input satisfies the model's `Requires` (the tag is
one of the three and the base-shape tag one of the four, by construction) and
the branch guards (`old != cs.sym`, and a `Symbol` bound variable — `Expr` is
the code's own guard and is asserted too). Nothing is excluded by base-domain
shape: §3.1's scope is every `Set`, so the `domain_rejected` counter is 0 by
measurement. The remaining counted exclusions are §3.1's two refusals plus the
operation's own; each is reported in the summary line.

**Inputs.** The space is infinite, so: **125 boundary cases** (the issue-17341
headline; the F2P regression `ConditionSet(n, n < x, Interval(-oo, 0)).subs(x,
p)`; each of the impl's branches over each of the 22 base-domain families;
base domains that collapse to empty under the replacement; listed base domains
whose members are all refuted / all admitted / partly undecided; the §1.1
normalization family over six base-domain shapes; a predicate handed over as an
explicit listing; a replacement that collides with the bound variable; the ten
merge inputs of §1.2 — all four binder outcomes, both truth pre-emptions, the
no-re-reduction case and a negative replacement *symbol*; and the three refusal
shapes) then seeded fuzz over an **8832**-element pool of real `ConditionSet`s
(10 binders × 4 free symbols × 11 predicate shapes × 22 base-domain shapes,
minus the ones the constructor reduces or renames) crossed with **16**
replacement values, to **100000 in-domain comparisons**.

Measured (seed 19495, gold patch applied, exit 0, 0 disagreements):

| quantity | value |
|---|---|
| in-domain comparisons | 100000 (122 of the 125 boundary inputs + fuzz) |
| `COND_FALSE` / `COND_TRUE` / `COND_OPEN` | 10794 / 22739 / 66467 |
| `BASE_EMPTY` / `BASE_LISTED` / `BASE_PLAIN` / `BASE_MERGED` | 2706 / 26309 / 67455 / 3530 |
| merge comparisons that did NOT carry the outer bound variable over | 1604 |
| `K_EMPTY` / `K_BASE` / `K_SET` | 14836 / 24464 / 60700 |
| outside §3.1's base-domain scope | 0 (nothing is excluded by base shape) |
| predicate with no truth value (exclusion 1) | 3654 |
| non-`Symbol` bound variable (exclusion 2) | 0 |
| operation itself raises (the third counted absence) | 4429 |

The script FAILS if `BASE_MERGED` is never compared, or is compared only where
the merge happens to keep the outer bound variable: those are the comparisons on
which the merged clause says something the plain-base clause does not, and a run
without them would be measuring a weaker spec than the one shipped.

(The figures recorded here before an earlier revision — 33 boundary, 3370
out-of-scope, 11320/18730/69950 — were stale: they described a script revision
two refinements old, and re-running the *unmodified* bundled script at the same
seed already printed 63 boundary, 0 out-of-scope, 11819/19140/69041. The table
above is the current script's own output.)

**Pinned seed: `19495`** (`SEED` in `conformance_check.py`; the same seed the
velvet and lean siblings pin).

**Discrimination control.** With the gold patch withheld, the identical script
and seed FAIL inside the boundary set: **11 disagreements over the 122 boundary
comparisons**, every one on the `COND_TRUE` path — the issue-17341 headline
(`ConditionSet(1/3, Contains(1/3, …), …)` instead of the image set), the F2P
regression (a `ConditionSet` instead of `EmptySet`), the
replacement-collides-with-the-bound-variable case
(`ConditionSet(x, Contains(x, Reals), Reals)` instead of `Reals`),
`true_base*` over plain base domains, and `merge_pre_empted_true`, where the
pre-patch line makes the constructor raise instead of handing the inner object
back. Pre-patch returned `ConditionSet(new, Contains(new, base), base)`, keying
the result on `new`. The green verdict is therefore evidence about the behaviour
under specification, not a vacuous pass.

**Controls on the merged clause specifically.** Two further runs, gold applied,
with only the shadow's merge branch weakened, both FAIL inside the boundary set:

| weakened shadow | result |
|---|---|
| `Result0(K_SET, sym, merged_base, cond)` — keeps the OUTER bound variable | FAIL, 5 disagreements (`merge_adopts_inner_sym`, `merge_inner_base`, `merge_mints_lambda`, `merge_mints_dummy`, …) |
| `Result0(K_SET, merged_sym, base, cond)` — leaves the object over the OUTER base domain | FAIL, 8 disagreements (every merge case) |

These are the same two rivals `properties.py` carries as
`weak-build-merged-keeps-outer-sym` and `weak-build-merged-keeps-outer-base`, so
the new clause is load-bearing under both gates.
