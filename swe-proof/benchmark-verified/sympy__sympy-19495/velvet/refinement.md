# refinement.md — sympy__sympy-19495

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`evalSubsFree` `do` block, plus the deep `evalSubsSpec` model and the
`substCond` / `substSet` / `mkSet` / `mkSetOnValue` A-reference callees) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses the axiom's `ensures`), **A-reference** (deep model /
opaque callee validated == real callee by G-AX), or **I** (identical concrete op).
EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ** / **G-AX**.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

**Termination semantics: total.** The obligation runs under
`loom.semantics.termination "total"` (`TotalCorrectness`), so a verifying impl
must TERMINATE and produce `evalSubsSpec boundSym condition baseSet old new`.
(An earlier revision used partial correctness, which a same-spec diverging impl
— a `while true` loop with a trivial invariant before the return — vacuously
satisfied; total semantics excludes that whole class. The real operation is
straight-line: two substitution calls and a constructor call, no loop, so it
trivially terminates.)

**BOTH modeled callees are PARTIAL, and NEITHER one's partiality is exhausted by
its sorts.** Neither the constructor `ConditionSet.__new__` nor the substitution
helper `Basic.subs` is a total function of interchangeable handles: on arguments
outside its domain each RAISES instead of returning a value. mapping.md §3.3, §3.4
and §3.5 give the refusal sites and the resulting model, which has one layer per
kind of refusal:

* where the partiality is **sortal** — "which slot may hold what", and "which
  substitutions exist at all" — it is carried by the argument SORTS (`Binder`,
  `Cond`, `SetObj`, `Old`, `New`, plus `BuiltSet` for the produced set, kept
  distinct from the component sort `SetObj`) together with one axiom per real
  invocation shape (`mkSet`, `mkSetOnValue`);
* where the SUBSTITUTION HELPER is **not** sortally partial — a replacement an
  ordinary relational condition cannot be compared against, e.g.
  `(y > 0).subs(y, I)` → `TypeError` — it is carried by the two `require`s
  `CondSubDefined` / `BaseSubDefined`, because on those inputs the real operation
  has no result either: it propagates the error rather than returning a set, so a
  *total*-semantics contract must not promise one;
* where the **CONSTRUCTOR** is not sortally partial — and it is not: building the
  set TESTS THE CONDITION AGAINST THE ELEMENTS of a finite base
  (`sifted = sift(base_set, lambda _: fuzzy_bool(condition.subs(sym, _)))`,
  `conditionset.py:151-152`), so with a `Symbol` binder, a genuine `Boolean`
  condition and a genuine `Set` base it still refuses when the condition cannot be
  compared against an element (`ConditionSet(x, x > 0, FiniteSet(I))` →
  `TypeError: Invalid comparison of non-real I`) — it is carried by the third
  `require`, `BuildsDefined boundSym condition baseSet old new`, for the same
  reason: the real operation propagates that refusal too. This `require` ranges
  over EVERY set-building invocation the model can NAME at these arguments (either
  shape, at the stored components and at their substituted forms, keyed on the
  binder or on either substitution argument), not merely over the one the `ensures`
  returns — which is what makes a *discarded* extra rebuild denote an invocation
  the real constructor accepts (mapping.md §3.5).

Four consequences are load-bearing for this document:

* **Every application the impl region can write denotes an invocation the real
  callees ACCEPT** (axiom_check.py obligations 7–8, 15 and 18 measure this: 3780 +
  84 constructor invocations on the sort grids, all 72 extra invocation shapes the
  sorts still admit on the boundary cases, and 41904 nameable set-building
  invocations over the pool inputs the three preconditions admit — 0 refused), so
  §E may read a verifying impl as real code that runs to completion.
* **The sorts do not decide the changed behaviour.** The decision under change —
  bind the set's own `self.sym` versus rebind to the substituted value — remains
  an `ensures` decision: both alternatives are well-sorted and writable
  (`mkSet boundSym …` and `mkSetOnValue (newObj new) …`, the latter being the shape
  the patch deletes), and the wrong one is rejected by the postcondition alone.
  What the sorts remove is only the class of applications the real callees refuse.
* **A rival that returns the right value but makes an extra, RESULT-DISCARDED call
  the real callee refuses is closed out — by the sorts where the refusal is sortal,
  and by `BuildsDefined` where it is not.** This class is the one a total-function
  callee model cannot see at all: a weakest-precondition calculus observes nothing
  of a discarded application of a total function, so such a rival verifies while
  its patch raises. Where the extra call is sortally wrong it is a Lean TYPE ERROR,
  hence unwritable rather than merely unproven; two such calls, both refused on this
  instance's own kind of input, are now untypeable:
  `self.func(new, self.condition, self.base_set)` with `new = 1/3`
  (`ValueError('non-symbol dummy not recognized in condition')`, axiom_check.py
  obligation 9) and `self.func(sym, cond, base).subs(sym, p)` — a MANUFACTURED set
  re-substituted at its own binder (`ValueError('A dummy symbol can only be
  replaced with a symbol having the same assumptions…')`, obligation 11). Where it
  is NOT sortally wrong it is writable and well-typed, and the third precondition
  is what makes it harmless: with `BuildsDefined` in force every set-building
  application the impl region can write — including a discarded one — denotes an
  invocation the real constructor accepts. Without it, an extra
  `self.func(self.sym, self.condition, self.base_set.subs(old, new))` on the
  F2P-shaped input `ConditionSet(x, x > 0, FiniteSet(z))` with `z -> I` raises
  `TypeError` in Python while the Lean rival verifies (obligation 16 is exactly
  that input, measured on PRE-PATCH source).
* **The preconditions keep the contract no stronger than the real method.** They
  are what stop total semantics from claiming termination on inputs where the real
  callees raise; obligation 13 measures that inside them the modeled branch really
  is total (0 refusals on the 2328 admitted pool inputs), obligation 12 that they
  hold on the F2P input the problem statement exhibits, and obligations 16–17 the
  same two things for `BuildsDefined` (its exhibit is a real refusal the real
  operation propagates; it holds on the F2P witness and on 2328 of the 2347 inputs
  the substitution preconditions already admit), so they do not shrink the domain
  away from the behaviour under change.

## A. The substitution site — `ConditionSet._eval_subs`, the `isinstance(sym, Expr) and old != sym` branch

Gold hunk (`sympy/sets/conditionset.py`, the second hunk):
```
-        cond = self.condition.subs(old, new)
-        base = self.base_set.subs(old, new)
-        if cond is S.true:
-            return ConditionSet(new, Contains(new, base), base)
-        return self.func(self.sym, cond, base)
+        else:
+            cond = self.condition.subs(old, new)
+            base = self.base_set.subs(old, new)
+            # assumptions are ignored
+            return self.func(self.sym, cond, base)
```
(The first hunk is a pure docstring edit — see §C.)

| # | Solution.lean impl op (`evalSubsFree`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `boundSym : Binder`, `condition : Cond`, `baseSet : SetObj`, `old : Old`, `new : New`; `require CondSubDefined condition old new`, `require BaseSubDefined baseSet old new`, `require BuildsDefined boundSym condition baseSet old new`, `require oldObj old ≠ binderObj boundSym` | `self.sym`, `self.condition`, `self.base_set`, `old`, `new`; this is the `isinstance(self.sym, Expr) and old != sym` branch | R | each SymPy object ↔ an opaque handle of the sort its slot admits, with the two substitution arguments sorted by their ROLE (`Old`, `New`) so the model can name only the substitution the operation was handed (mapping.md §2, §3.4). The fourth `require` is the branch guard `old != self.sym`; the other guard, `isinstance(self.sym, Expr)` (`conditionset.py:209`), is carried by the `Binder` sort, narrowed to a plain `Symbol` (mapping.md §3.3): on a compound `Tuple` binder the method returns `self` untouched, an UNCHANGED early return outside the model (axiom_check.py obligation 5), and on an `Expr`-but-not-`Symbol` binder the constructor is itself partial (obligation 10), so that sub-domain is excluded too. The first two `require`s are the substitution helper's own non-sortal domain (mapping.md §3.4; obligations 11–13) and the third is the CONSTRUCTOR's (mapping.md §3.5; obligations 16–18), at every set-building invocation the model can name at these arguments. G-CONF bridges by constructing real `ConditionSet`s with `Symbol` binders, fuzzing substitution args, and skipping exactly the inputs those three preconditions exclude — for the third it evaluates the operation's own rebuild first and, on every input the constructor refuses, checks that the patched `_eval_subs` refuses it too (309 of them in the last run, all 309 refused), so the precondition is measured no stricter than the real operation rather than assumed so. |
| A2 | `let newCond := substCond condition old new` | `cond = self.condition.subs(old, new)` | A-reference + I | `substCond` is the unchanged `Basic.subs` at the condition slot; opaque, no `ensures` (the method never inspects `cond`). Its result sort `Cond` is the fact that a substituted condition is still legal in the condition slot — measured in both substitution directions by axiom_check.py obligation 6. The callee is PARTIAL: its argument sorts `Old`/`New` keep the nameable substitutions down to the operation's own, and `CondSubDefined condition old new` — discharged by the caller, consumed by nothing — is the rest of its domain (obligation 11 exhibits a real refusal, `(y > 0).subs(y, I)` → `TypeError`). The op itself is concrete/identical; G-CONF runs the real `.subs`. mapping.md §3.1, §3.4. |
| A3 | `let newBase := substSet baseSet old new` | `base = self.base_set.subs(old, new)` | A-reference + I | same as A2 for the base set: result sort `SetObj`, domain `BaseSubDefined baseSet old new`. The receiver sort is the COMPONENT sort `SetObj` while the constructor produces a `BuiltSet`, so the receiver of a substitution can only be the stored base set or a substituted form of it — never a set the impl manufactured, which is the receiver on which the real helper refuses (obligation 11, second refusal). mapping.md §3.4. |
| A4 | `return mkSet boundSym newCond newBase` | `return self.func(self.sym, cond, base)` | A-reference + I | the rebuild op: `mkSet` is the unchanged `ConditionSet` constructor (`self.func`) in its binder-keyed invocation shape, opaque, no `ensures`. The decisive **I/R content** is the BINDER ARGUMENT — `boundSym` (the original `self.sym`), NOT `new`. G-CONF transliterates this choice and runs the real constructor. mapping.md §3.2. |
| A5 | *(no impl op)* `mkSetOnValue` is available but unused by the gold impl | `ConditionSet(new, Contains(new, base), base)` — the pre-patch collapse-path rebuild the patch DELETES (`conditionset.py:245` pre-patch) | A-reference | the second invocation shape of the same unchanged constructor. It is in the axiom surface because it is the shape the deleted code used, so `Solution_prepatch.lean` can transcribe that code faithfully (§A, below) and because the value-keyed shape is genuinely part of the callee's domain (axiom_check.py obligation 8). Opaque, no `ensures`; the gold impl never applies it. |

Discriminating content of the change — the rebuilt set keeps the **original** bound
symbol (`mkSet boundSym …`) rather than being keyed on the substituted value
(`mkSetOnValue (newObj new) …`). This is visible only when the substituted condition
collapses to `S.true`: pre-patch the collapse path used
`ConditionSet(new, Contains(new, base), base)`, conflating the internal binder
with the free symbol being substituted (the problem statement: *"It's as if the
bound variable `x` … were mistaken for a `y`"*). On the non-collapse path, even
the pre-patch code already returned `self.func(self.sym, cond, base)`, so the two
versions agree there; the model is the uniform post-patch behavior across the
whole branch.

`Solution_prepatch.lean` reproduces the bug by returning
`mkSetOnValue (newObj new) (substSet baseSet old new)` — a verbatim transcription
of the deleted collapse-path rebuild, now expressible because the value-keyed
shape has its own axiom — and **fails** `out = evalSubsSpec …` (G-DIFF). The
unsolved goal is exactly
`mkSetOnValue (newObj new) (substSet baseSet old new) = mkSet boundSym (substCond condition old new) (substSet baseSet old new)`,
the binder discrepancy. Note that this rival elaborates cleanly — the sorts do not
type it out — so the rejection is behavioural.

## B. No consumed axioms

`substCond`, `substSet`, `mkSet` and `mkSetOnValue` are modeled `opaque` with **no
asserted `ensures`** — the proof consumes no equational fact about any of them.
They are **A-reference** (validated `== real callee` by G-AX), not A-consumed. The
entire correctness obligation is the binder choice (A4), an R/I fact discharged by
`loom_solve` + `simp_all`.

The sorts are not `ensures` clauses and consume nothing: they are the *domain* of
the callees, i.e. part of the R leg (which repo values a Lean handle stands for),
and they are discharged by G-AX obligations 6–11 and 15 against the real callees
rather than assumed.

`CondSubDefined` / `BaseSubDefined` / `BuildsDefined` are likewise **not** consumed
axioms. They are opaque `Prop`s with no `ensures` and no defining equation, so
nothing about a condition, a set or a built set follows from them; the proof never
uses them, it only carries them as `require`s the caller must discharge (measured:
`by assumption` fails on each of the three inside the impl region, so they are not
even hypotheses in scope there). They record the remaining, non-sortal part of the
two callees' DOMAINS — the same kind of R-leg fact as the sorts.

G-AX obligations 11–14 discharge the two substitution preconditions against the
real helper: 11 exhibits real refusals, 12 that they hold on the instance's own F2P
input, 13 that inside them the modeled branch is total, 14 that the domain is
closed under the re-application the model can still express. Obligations 16–18
discharge `BuildsDefined` against the real constructor: 16 exhibits a fully
well-sorted input on which the constructor refuses the operation's OWN rebuild and
the real pre-patch `_eval_subs` propagates that refusal (so the precondition is
forced, and at that clause is exactly as strict as the operation itself — over the
pool, all 6 own-rebuild exclusions are inputs the real operation raises on); 17 that
it holds on the F2P witness, on the problem statement's second example, and on 2328
of the 2347 inputs the substitution preconditions admit; 18 that its coverage is
complete for what an impl can write (41904 nameable set-building invocations, with
re-application measured idempotent on all 2328 admitted inputs, so deeper nesting
denotes objects already covered) and that the price is 13 inputs excluded only
because a writable EXTRA shape is refused while the operation itself returns — the
sliver of domain traded for building axioms that are total on their sorts, on which
the contract is silent rather than wrong.

G-CONF checks the consumer side of the same claims: it skips the inputs the three
preconditions exclude and treats a raise on any input they ADMIT as a disagreement.

## C. The docstring hunk (no behavior; not modeled)

The first gold hunk only edits the class docstring (removes a stray "Notes"
heading, fixes a duplicated word "and", adds a trailing blank line). It changes no
behavior and is observed by no F2P test; it is carried verbatim in `patch.diff`
(G-RESOLVE applies the whole gold patch) but corresponds to no `do`-block op. No
R/A/I row is owed for a pure-comment edit.

## D. No kind-3 (inexpressible-changed-op) steps

Every modeled step is R, A, or I. The one operation that genuinely *changed* — the
choice of bound symbol in the rebuilt set — is modeled **deeply** (the spelled-out
`evalSubsSpec`/`mkSet boundSym …`, step A4, an A-reference + I), not hidden behind
an axiom about the function under change. There is no consumed axiom.

## E. verify(Solution) ⇒ resolved

`evalSubsFree` verifies only if its output equals `evalSubsSpec boundSym condition
baseSet old new = mkSet boundSym (substCond condition old new) (substSet baseSet
old new)` — i.e. the rebuilt set uses the ORIGINAL binder (A4).

Two things must hold for that to entail a resolving patch, and the sorted model
supplies both.

1. **The returned value is right.** By R (each SymPy object ↔ a handle of its
   slot's sort; `substCond`/`substSet ↔ Basic.subs`; `mkSet ↔` the `ConditionSet`
   constructor, binder-keyed) the verified return equals the post-patch
   `self.func(self.sym, self.condition.subs(old,new), self.base_set.subs(old,new))`
   on the `isinstance(sym, Expr) and old != sym` branch, restricted to a `Symbol`
   binder and to the inputs on which the two component substitutions AND the
   constructor's own test of the condition against the base's elements are defined
   (the three `require`s; on the rest the real method returns nothing at all, it
   propagates the callee's error). The excluded arms — the compound (`Tuple`) binder early return, the
   `Expr`-non-`Symbol` binder sub-domain, and the `old == sym` dummy-renaming arm —
   are UNCHANGED by the gold patch (axiom_check.py obligation 5 confirms the first
   is the identity). By G-AX the deep model equals the real `_eval_subs` on that
   branch (including the collapse witnesses); by G-CONF the R/I transliteration
   agrees with `patch.diff`'s behavior on ≥10⁵ inputs.

2. **Nothing the impl does BESIDES returning that value can fail.** The impl
   region is straight-line under total semantics, so the only way a verifying impl
   could still raise is by invoking a callee out of its domain — including in a
   statement whose result is discarded, which a WP calculus cannot observe when the
   callee is modeled as a total function. That class is closed here in three steps,
   one per layer of the domain model.

   *Sortally.* Every application of `mkSet` / `mkSetOnValue` / `substCond` /
   `substSet` the impl region can *write* is well-sorted by construction, and an
   application outside the sorts does not typecheck, so it cannot appear in a
   verifying file at all — not even discarded. Concretely, the sorts make
   untypeable: an object in the binder slot the condition does not bind
   (`mkSet new …`); a set in the condition slot or a condition in the base slot; a
   substitution in the reverse direction (`substCond condition new old`); a
   substitution keyed on the set's own binder (`substSet baseSet (binderObj boundSym) new`);
   and a substitution whose receiver is a set the impl MANUFACTURED
   (`substSet (mkSet boundSym condition baseSet) … `, ruled out by the
   `SetObj`/`BuiltSet` split).

   *Non-sortally, for the SUBSTITUTION helper.* What the sorts cannot express — a
   replacement the component cannot be compared against — is exactly what
   `CondSubDefined` / `BaseSubDefined` exclude, so on every input the contract
   accepts, both substitution calls return.

   *Non-sortally, for the CONSTRUCTOR.* A set-building call can be well-sorted in
   all three slots and still be refused, because `__new__` tests the condition
   against the elements of a finite base. Those calls ARE writable, so this is the
   one layer the sorts cannot carry, and `BuildsDefined` carries it: it asserts
   definedness at every set-building invocation the model can NAME at these
   arguments — both shapes, at the stored condition and base and at their
   substituted and twice-substituted forms, keyed on the binder or on either
   substitution argument — so an extra, discarded, well-typed rebuild denotes an
   invocation the real constructor accepts. This is what makes the totality claims
   of the two building axioms true for what an impl can actually write, and not only
   for the invocation the `ensures` returns.

   All three steps are measured against the real callees rather than stipulated:
   obligations 6–8, 15 and 18 that the real callees are TOTAL on what the model
   admits (3780 binder-keyed and 84 value-keyed constructor invocations on the sort
   grids, all 72 extra invocation shapes the sorts still allow on the boundary
   cases, 41904 nameable set-building invocations over the admitted pool inputs,
   `Basic.subs` sort-preserving in both directions — 0 refusals anywhere);
   obligations 9–11 and 16 that each excluded shape corresponds to a real invocation
   the real callee genuinely REFUSES (including 96 well-sorted triples and 1
   value-keyed invocation, which is what forces the third precondition rather than a
   fourth sort), so the model tracks the domain instead of over-restricting it;
   obligations 12–14 and 17 that the preconditions are non-vacuous, sufficient for
   the branch to be total, and closed under the re-application the model can still
   express.

   The consumer side of the third step was measured through the real correctness
   oracle rather than argued. The two extra-call shapes that remain WRITABLE and
   verifying — `_probe = self.func(self.sym, self.condition, base)` (binder-keyed,
   raw condition over the substituted base) and
   `_probe = ConditionSet(new, Contains(new, base), base)` (value-keyed on the
   replacement) — were spliced into the gold patch and run through the harness:
   BOTH RESOLVE (FAIL_TO_PASS and PASS_TO_PASS pass with the extra discarded call
   in place). So on this instance the calls the model still admits are calls the
   real callee accepts on every input the test suite exercises, and the ones it
   does not admit are either untypeable or outside the contract's domain — which is
   what makes "verifies ⇒ resolves" hold for this family rather than merely be
   unobserved.

Therefore a model satisfying this spec, refined by the map above, is the gold patch
up to type refinement and audited callees — and the gold patch resolves
(G-RESOLVE). Trust points are exactly the two of plan §1.1: callee soundness
(G-AX, the A-reference equality *and* the domain claim) and refinement fidelity
(this doc, G-EQ + G-CONF).
