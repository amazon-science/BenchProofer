# refinement.md — django__django-15554

The operation-by-operation correspondence between `model.py`'s implementation
(the `install_join` impl region and the deep predicates `matches_default` /
`matches_constrained` / `no_eligible_match`) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A-consumed** (proof uses an
axiom's `Ensures`), **A-reference** (a deep model validated == a real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The decisive hunk — the alias-reuse predicate in `Query.join` (`query.py:1014`)

Gold hunk (the `reuse_aliases` computation):
```
-        reuse_aliases = [
-            a
-            for a, j in self.alias_map.items()
-            if (reuse is None or a in reuse) and j.equals(join)
-        ]
+        if reuse_with_filtered_relation and reuse:
+            reuse_aliases = [
+                a for a, j in self.alias_map.items() if a in reuse and j.equals(join)
+            ]
+        else:
+            reuse_aliases = [
+                a
+                for a, j in self.alias_map.items()
+                if (reuse is None or a in reuse) and j == join
+            ]
```

| # | model.py impl op (`install_join`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `base[i] : List[int]`, `frel[i] : List[int]` over slots | the joins `j` of `self.alias_map.items()` | R | `alias_map` ordered dict ↔ parallel arrays; `j.identity[:-1]` ↔ `base[i]`, `j.filtered_relation` ↔ `frel[i]` (mapping.md §2). |
| A2 | `reuse_all : bool`, `reuse_mask[i] : bool` | `reuse is None` / `a in reuse` | R | `reuse is None` ↔ `reuse_all`; `a in reuse` ↔ `reuse_mask[i]` (mapping.md §2). |
| A3 | `constrained : bool` | `reuse_with_filtered_relation and reuse` (the new branch guard) | R | the constrained branch is taken iff a non-empty reuse set is supplied with the filtered-relation flag; modeled by the `constrained` boolean with `Requires(Implies(constrained, not reuse_all))` (a non-empty reuse set ⇒ `reuse is not None`). |
| A4 | default branch: `reusable(i,…) and matches_default(i,…)` = `(reuse_all or reuse_mask[i]) and (base[i]==jb and frel[i]==jf)` | default branch: `(reuse is None or a in reuse) and j == join` | I + R | `j == join` is `Join.__eq__`, full-identity equality **including** `filtered_relation` (`datastructures.py:156-159`); under the interning bijection it is exactly `base[i]==jb and frel[i]==jf`. The reuse guard is identical. |
| A5 | constrained branch: `reuse_mask[i] and matches_constrained(i,…)` = `reuse_mask[i] and base[i]==jb` | constrained branch: `a in reuse and j.equals(join)` | I + R | `j.equals(join)` is `Join.equals`, identity-minus-`filtered_relation` (`datastructures.py:164-166`); under the bijection it is `base[i]==jb`. Only masked slots are eligible (`a in reuse`). |
| A6 | `Result() = not found` where `found` ⇔ some eligible slot matched | `reuse_aliases` non-empty ⇒ reuse; empty ⇒ fall through to `self.table_alias(create=True)` and append a new alias (`query.py:1042-1053`) | R | `Result() == True` (a fresh slot is needed) ↔ `not reuse_aliases` (no reusable alias found, so `join()` creates a new alias). Which matching alias is reused is unchanged by the patch and not modeled. |

The discriminating content of the change is **A4**: the default predicate moves
from `j.equals(join)` (ignores `filtered_relation`) to `j == join` (includes it).
With two descriptors sharing a base relation but differing in `filtered_relation`
(two `FilteredRelation`s on the same relation with different conditions, the F2P
`test_multiple`), the new predicate yields NO match ⇒ a fresh alias ⇒ two
distinct joins; the old predicate matched ⇒ reuse ⇒ the second filtered relation
was silently merged into the first. `model_prepatch.py` reproduces the old
default predicate (`matches_constrained` in the default branch) and **fails** the
loop invariant `Implies(found, not no_eligible_match(…))` — the spec's
`no_eligible_match` uses `matches_default` (full identity), so a base-only match
cannot discharge it. This is exactly the spec sensing the change (G-DIFF).

## B. The plumbing hunks — threading `reuse_with_filtered_relation` (R)

The gold patch also adds the keyword `reuse_with_filtered_relation` to
`build_filter` (`query.py:1318`), passes it down to `setup_joins`
(`query.py:1416`), sets it `True` from `build_filtered_relation_q`
(`query.py:1578`), and in `setup_joins` forces `reuse = can_reuse` and forwards
the flag into `self.join(...)` (`query.py:1843-1854`).

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | the `constrained` parameter of `install_join` and `Requires(Implies(constrained, not reuse_all))` | the `reuse_with_filtered_relation` keyword + the `setup_joins` line `reuse = can_reuse if join.m2m or reuse_with_filtered_relation else None` then `self.join(connection, reuse=reuse, reuse_with_filtered_relation=...)` | R | the entire keyword thread is a *data-flow rename*: it merely arranges that, when computing a `FilteredRelation`'s own sub-filter joins, `join()` is entered with `reuse_with_filtered_relation=True` and a non-empty `reuse` set — i.e. `constrained=True`. The behavioural content lives in §A's predicate selection; B is the routing that decides which branch (A4 vs A5) a given call takes. No new behaviour beyond passing a boolean. |

These hunks add no operation Nagini cannot express; they thread a boolean. They
are not separately modeled as functions because they compute no value the spec
observes beyond the branch selector `constrained`, which `install_join` takes as
a parameter. (Modeling them as identity-returning pass-throughs would add no
differential witness.)

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The one operation that genuinely *changed* — the
equality predicate deciding alias reuse — is pure tuple/integer equality over
`Join.identity`, modeled **deeply** (`matches_default` includes the refinement
tag, `matches_constrained` excludes it; `no_eligible_match` folds the eligible
match over all slots). There is **no consumed axiom**: nothing opaque is called
inside an `Ensures`. The real `Join.__eq__` / `Join.equals` semantics the deep
predicates refine are validated executably by `axiom_check.py` (G-AX,
A-reference §3 of mapping.md), not consumed as a `@ContractOnly`.

## D. verify(model) ⇒ resolved

`install_join` verifies only if `Result()` equals `no_eligible_match(...)` —
i.e. a fresh slot is reported exactly when no reuse-eligible slot matches under
the *active* predicate, and the active default predicate compares the FULL
identity including the refinement tag (A4). By R (alias_map ↔ arrays,
`Join.identity` interning, `reuse` ↔ mask/flag) the verified decision equals the
gold `join()`'s reuse-vs-new-alias decision on the tested configurations; by G-AX
the deep predicates equal the real `Join.__eq__` / `Join.equals`
(A-reference). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The only trust point is refinement fidelity (this document, G-EQ)
plus the executable `Join`-semantics check (G-AX); there is no axiom-soundness
trust point because no axiom is consumed.
