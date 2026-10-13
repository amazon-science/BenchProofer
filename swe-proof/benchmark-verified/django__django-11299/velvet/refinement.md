# refinement.md — django__django-11299

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`assignColumnForms` `do` block and the deep `columnForm`/`columnForms`/`formOf`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** / **A-reference** (axiom / deep-model-of-callee — one
A-reference here: `formOf` == `_get_col`), or **I** (identical concrete op).
EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the narrative is audited by **G-EQ**. `patch.diff` is the gold patch **verbatim**
(G-RESOLVE).

## A. The change site — `Query._add_q` (`django/db/models/sql/query.py:1339-1341`)

Gold hunk:
```
                 child_clause, needed_inner = self._add_q(
                     child, used_aliases, branch_negated,
-                    current_negated, allow_joins, split_subq)
+                    current_negated, allow_joins, split_subq, simple_col)
```

The recursive `_add_q` call on a **group** child (`isinstance(child, Node)`)
previously omitted the `simple_col` argument, so the recursion ran with the
parameter default `simple_col=False` (`query.py:1329`); the patch forwards
`simple_col`, so the selector chosen at the top of the walk reaches leaves at
every nesting depth.

| # | Solution.lean impl op (`assignColumnForms`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `bare : Bool` | the `simple_col` parameter threaded through `_add_q` | R | Python truth value ↔ Lean `Bool` (mapping.md §3). |
| A2 | parameter `conds : List Cond` | `q_object.children` — the list walked by `for child in q_object.children` (`query.py:1337`) | R | `Node`/leaf children ↔ `Cond.group`/`Cond.atom`; order preserved (mapping.md §3). |
| A3 | `match conds with \| [] => return []` | loop over `q_object.children` terminates; empty children ⇒ empty assembled clause | I | front-recursive list walk; empty forest ⇒ empty result. |
| A4 | `\| .atom :: rest => … (ResolvedCond.atom (formOf bare)) :: tailR` | the `else` branch: `build_filter(child, …, simple_col=simple_col)` → `_get_col(targets[0], …, simple_col)` (`query.py:1344-1347`, `1278`/`1300`, `71`) | A-reference + I | a leaf receives the column form selected by `simple_col`: `formOf bare`. The leaf's field/lookup/value resolution is UNCHANGED machinery, abstracted out (leaf ↦ `atom`, the I part); the only observable, patch-relevant content is the column FORM, produced by the UNCHANGED `_get_col` callee — modeled deeply as `formOf` and validated **== real `_get_col`** by G-AX (A-reference, mapping.md §4). |
| A5 | `\| .group inner :: rest => let innerR ← assignColumnForms bare inner; …` | the `if isinstance(child, Node):` branch: the **recursive** `self._add_q(child, …, simple_col)` call (`query.py:1339-1341`, post-patch) | I | descent into a group recurses on the group's children **with the same selector `bare`** — exactly the propagation the patch restores. This is the discriminating op (see below). |
| A6 | `formOf bare = if bare then ColForm.bare else ColForm.qualified` | `_get_col`: `if simple_col: return SimpleCol(...)` else `target.get_col(...)` (`query.py:71-74`) | A-reference | the deep model of the UNCHANGED `_get_col` callee's selector→column-class choice; validated **== real `_get_col`** by G-AX on both selector values. Column-class identity (`SimpleCol`/`Col` ↔ `ColForm.bare`/`ColForm.qualified`) is the R-bijection inside the A-reference. |

## B. The discriminating clause and the prepatch

`build_where` enters the walk with `simple_col=True` (`query.py:1324-1325`),
i.e. `bare = true`. The spec's `ensures result = columnForms bare conds` then
forces **every** leaf — including those inside a nested group — to be
`ColForm.bare`. The gold behavior is `assignColumnForms bare inner` in the group
branch (A5): the selector is threaded unchanged into nested groups.

`Solution_prepatch.lean` reproduces the actual defect: the group branch recurses
with `assignColumnForms false inner` (the dropped-argument default). For
`bare = true` and a non-empty nested group, the pre-patch impl yields
`ResolvedCond.atom ColForm.qualified` for the nested leaves whereas the frozen
spec requires `ColForm.bare`; `prove_correct` therefore cannot close
(G-DIFF: verification fails). This is exactly the
`test_simplecol_query` observation — the AND-group leaves of
`Q(num__gt=2, name__isnull=False) | Q(num__lt=F('id'))` must be `SimpleCol`.

## C. One A-reference, no consumed axiom, no kind-3

Every step is R, A-reference, or I. There is **no consumed axiom** and **exactly
one A-reference** (mapping.md §4): the per-leaf column-form choice `formOf`, the
deep model of the UNCHANGED `_get_col` callee's selector→column-class behavior
(A4/A6). It is modeled **deeply and concretely** (`columnForm`/`columnForms`/
`formOf`) rather than hidden behind an opaque `ensures`, and its fidelity is
validated **== the real `_get_col` callee** by G-AX on both selector values
(SPEC_GUIDE §3: deep model ⇒ A-reference, not a consumed axiom). The selector
**propagation** through the tree (A2/A3/A5) and the structure-preserving assembly
are R/I, differential-tested by G-CONF. The rest of the per-leaf resolution
machinery is abstracted to a structural value (a leaf ↦ `atom`, the I leg),
sound because the patch does not alter it and it does not affect which column
form a leaf receives. No operation is inexpressible, so there is no kind-3 step
and no BLOCKED.

## D. verify(Solution) ⇒ resolved

`assignColumnForms` verifies only if its output equals `columnForms bare conds`:
every leaf at every depth gets `formOf bare`, and nested groups are assembled
under the SAME selector (A5). By the R-bijections (`Bool ↔ simple_col`,
`ColForm.bare/qualified ↔ SimpleCol/Col`, `Cond/ResolvedCond ↔ Q-object tree /
assembled WhereNode`) a verified `assignColumnForms` equals the patched `_add_q`
walk's column-form assignment on the assembled tree. G-CONF mechanically
confirms the R/I transliteration agrees with the patched `_add_q` recursion over
≥10⁵ fuzzed condition trees (seed 11299), 0 disagreements. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The trust points are:
refinement fidelity of the R/I propagation legs (this doc, G-EQ + G-CONF), and
the single A-reference column-form bijection `formOf` == real `_get_col`,
validated by G-AX on both selector values. There are no consumed-axiom trust
points.
