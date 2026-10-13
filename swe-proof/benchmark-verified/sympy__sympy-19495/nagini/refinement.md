# refinement.md — sympy__sympy-19495

The operation-by-operation correspondence between `model.py`'s implementation
(the `replace_free_parameter` impl region + the deep `build` reduction it calls) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses an axiom's `Ensures`), **A-reference** (a deep
model validated `==` the real callee by `axiom_check.py` / G-AX), or **I**
(identical concrete operation). No step is a *changed* operation Nagini cannot
express (no kind-3).

`patch.diff` is the gold patch **verbatim** — it applies at `base_commit` and
is the real correctness oracle (G-RESOLVE).

## The change

Only one hunk is behaviour-bearing (the other three hunks are docstring text:
removing a stray `Notes\n=====`, deleting a duplicated word, adding a blank
line — pure documentation, no code). The behavioural hunk rewrites the tail of
`ConditionSet._eval_subs` (`sympy/sets/conditionset.py:243-247` @ base_commit),
i.e. the branch reached when the substituted symbol `old` is NOT the bound
(dummy) symbol of the set (`old != sym`):

```
-        cond = self.condition.subs(old, new)
-        base = self.base_set.subs(old, new)
-        if cond is S.true:
-            return ConditionSet(new, Contains(new, base), base)
-        return self.func(self.sym, cond, base)
+        else:
+            cond = self.condition.subs(old, new)
+            base = self.base_set.subs(old, new)
+            # The condition may have become true due to assumptions
+            # on 'sym'. ... we *don't* check if 'sym' actually belongs to
+            # 'base'. ... assumptions are ignored.
+            return self.func(self.sym, cond, base)
```

The fix DELETES the `if cond is S.true: return ConditionSet(new, Contains(new,
base), base)` special case and ALWAYS returns `self.func(self.sym, cond, base)`
— rebuilding the set on the ORIGINAL bound symbol `self.sym`, never adopting
the replacement value `new` as the bound symbol. (`else:` merely re-indents the
existing body under the preceding `if old == sym:` block; it does not change
control flow for `old != sym`.)

## Operation correspondence

`model.py` models the free-symbol branch as `replace_free_parameter(self_sym,
new, cond_after, base_after, base_kind, listed_kind, listed_base, merged_sym,
merged_base)`, having pushed the replacement into the predicate and base domain
already (mirroring the two `subs` calls), and rebuilds via `build`.

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `self_sym: int` | `self.sym` (a SymPy `Symbol`) | R | a SymPy symbol's identity ↔ an `int` id; the only thing observed is *which* symbol becomes the bound symbol of the result (mapping.md §2). |
| 2 | `new: int` | `new` (the replacement value passed to `subs`) | R | same id-abstraction; `new` is the value the pre-patch code wrongly promotes to the bound slot. |
| 3 | `cond_after: int` (a `COND_*` truth tag) | `cond = self.condition.subs(old, new)` | R | the code uses only the *truth status the construction assigns* to the substituted predicate: `ConditionSet.__new__` first rewrites a predicate given as an explicit listing of expressions (conditionset.py:125-134) and then normalizes with `condition = as_Boolean(condition)` (line 136 → `sympy/logic/boolalg.py:20-58`), and only then tests `is S.false` / `is S.true` (lines 144, 146). So a predicate arriving as `1`/`0`, or as a symbol whose `.is_zero` its assumptions decide, IS decided, and the model abstracts the predicate to that 3-valued tag (mapping.md §1.1, §2). A predicate the normalization refuses has no tag and no admitted input. The two `.subs` calls are the caller's responsibility and are pushed into the args (steps consumed by R). |
| 4 | `base_after: int` | `base = self.base_set.subs(old, new)` | R | the substituted base domain's identity ↔ an `int` id; observed only for equality with the result's base. |
| 5 | `base_kind: int` (a `BASE_*` shape tag) | the shape of `base` as `__new__` tests it: `isinstance(base_set, EmptySet)` (line 148) / `isinstance(base_set, FiniteSet)` (line 152) / `isinstance(base_set, cls)` (line 161) / any other `Set` | R | which reduction the construction performs depends on this, so the shape is an observed input rather than hidden behind the identity id (mapping.md §2). |
| 6 | `listed_kind, listed_base: int` | `sift(base_set, lambda _: fuzzy_bool(condition.subs(sym, _)))` and the `Union(know, rv)` join (lines 152-159, 188) | R | the member-by-member decision over an explicitly listed base domain, folded into caller-supplied arguments exactly as the two `.subs` calls are, and abstracted by the same result map (mapping.md §2). |
| 7 | `merged_sym, merged_base: int` | the condition-MERGING branch (lines 161-179): `s, c, base_set = base_set.args`, the four branches that settle `sym`, and the INNER `base_set` the merged object stands over | R | the merge with a base domain that is itself a restricted object, folded into caller-supplied arguments exactly as the listing decision is. A fresh internal name (`Dummy('lambda')`) is not observable and abstracts to one reserved id (mapping.md §1.2, §2). |
| 8 | `return build(self_sym, cond_after, base_after, base_kind, listed_kind, listed_base, merged_sym, merged_base)` | `return self.func(self.sym, cond, base)` | A-reference + R | `self.func` is `ConditionSet`, so this invokes `ConditionSet.__new__(self.sym, cond, base)`, whose reduction ladder (normalize; `is S.false → S.EmptySet`; `is S.true → base_set`; empty base → the empty domain; a listed base decided member by member; a base that is itself a restricted object → the merge of the two restrictions over the inner base domain, keyed on the variable the merge settles on; else a `ConditionSet(sym, cond, base)`) is modelled **deeply** by `build`. `build` is NOT a consumed axiom — it is the spelled-out reduction rule, validated `==` the real `ConditionSet.__new__` by `axiom_check.py` (G-AX §[1], §[3], §[4], §[5]). The crucial property both express: the bound symbol of the rebuilt object is `self.sym`/`self_sym` — never the replacement value — on every base-domain shape but the merge, where the reduction itself settles it. |

The `build` reduction (`__new__`) is UNCHANGED by the patch; modelling it deeply
(rather than re-deriving SymPy's whole constructor) is the standard A-reference
treatment — G-AX runs the real `ConditionSet.__new__` on false/true/open
predicates over four base domains, on the normalization family that only the
constructor decides, and on the empty/listed/merging base-domain shapes, and
asserts agreement. mapping.md §3.1 lists the two shapes of `__new__` left out of
the model (a predicate with no truth value; a non-`Symbol` binder) and records
that each is a refusal of the unchanged code, identical with and without the gold
patch. The merging branch is NOT among them: mapping.md §1.2 records that an
earlier revision wrongly excluded it as unreachable, exhibits the substitution
that reaches it, and states the clause the model now carries for it.

## The discriminator (what the spec senses; G-DIFF)

The pre-patch code, in this same branch, did
`if cond is S.true: return ConditionSet(new, Contains(new, base), base)`. That
rebuilds the object keyed on `new` (the replacement value) wrapped in a fresh
`Contains(new, base)` membership predicate. For the issue's input
(`ConditionSet(x, Contains(y, [-1,1]), imageset(…asin(y)…)).subs(y, 1/3)`),
`Contains(1/3, base)` stays a non-trivial restriction, so the result is the
strange `ConditionSet(1/3, Contains(1/3, base), base)` (`Out[75]`) — the bound
variable `x` was effectively mistaken for `y`.

`model_prepatch.py` reproduces exactly this: when `cond_after == COND_TRUE` it
returns `build(new, COND_OPEN, base_after, base_kind, listed_kind, listed_base,
merged_sym, merged_base)` (the membership predicate stays open ⇒ `K_SET` keyed on
`new`). It **fails** the postcondition
`cond_after == COND_TRUE ⇒ Result().kind == K_BASE ∧ Result().base ==
base_after` — measured: `model_prepatch.py:300:13:301:77: error: Postcondition of
replace_free_parameter might not hold`, while `model.py` verifies.
That clause is precisely the behaviour the added F2P assertions demand: the
collapsed-to-true result must be the base domain, not a set keyed on `new`.

## verify(model) ⇒ resolved

`replace_free_parameter` verifies only if it returns the canonical reduction keyed on
the ORIGINAL `self_sym` — i.e. the base domain when the predicate collapses to
true (step 8, postcondition). By R (symbol/set/predicate-tag id-abstraction)
this is exactly `self.func(self.sym, cond, base)` of the gold patch on the
tested inputs; by G-AX (A-reference §[1]) `build` equals the real
`ConditionSet.__new__` reduction and the modelled free-symbol branch equals the
real `ConditionSet._eval_subs` (§[2], including the issue-17341 case). Therefore
an implementation satisfying this frozen spec, refined by the map above, is the
gold patch up to type refinement and the audited reduction — and the gold patch
resolves (G-RESOLVE). The single trust point is refinement fidelity (this
document, G-EQ) plus the A-reference reduction soundness (G-AX); there is no
consumed `@ContractOnly` axiom.
