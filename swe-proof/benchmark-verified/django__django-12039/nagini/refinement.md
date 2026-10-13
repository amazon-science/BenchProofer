# refinement.md — django__django-12039

The operation-by-operation correspondence between `model.py`'s implementation
(the `render_column` / `render_column_with_opclass` impl regions and the deep
`joined` model) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement), **A** (axiomatized callee — **A-consumed**, the proof uses
an axiom's `Ensures`; **A-reference**, a deep model validated == a real callee
by axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. Site 1 — `Columns.__str__.col_str` (`django/db/backends/ddl_references.py:85-91`)

Gold hunk:
```
     def col_str(column, idx):
+        col = self.quote_name(column)
         try:
-            return self.quote_name(column) + self.col_suffixes[idx]
+            suffix = self.col_suffixes[idx]
+            if suffix:
+                col = '{} {}'.format(col, suffix)
         except IndexError:
-            return self.quote_name(column)
+            pass
+        return col
```

Modeled by `render_column(base, suffix)`.

| # | model.py impl op (`render_column`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `base: List[int]` | `col = self.quote_name(column)` | R | `str` (the quoted column) ↔ `List[int]` of code points (mapping.md §2). `quote_name` runs upstream of the modeled join; its result is the `base` input. |
| A2 | param `suffix: List[int]` | `suffix = self.col_suffixes[idx]` | R | `str` ordering suffix ↔ `List[int]`; `''` (ascending) ↔ `[]` (mapping.md §2). The `try/except IndexError` is effectively dead in the tested flow (`col_suffixes` has one entry per column — mapping.md §1); the discriminator is empty vs non-empty suffix, which the spec pins directly. |
| A3 | copy `base` into `result` (the `j`-loop) | `col = self.quote_name(column)` (the base of the returned string) | R + I | element-wise copy of the code-point list ↔ the `str` `col`. |
| A4 | `if len(suffix) > 0: append sep() then suffix` else leave `result == base` | `if suffix: col = '{} {}'.format(col, suffix)` else `col` unchanged | A-reference + I | the changed join is modeled **deeply**: `joined(base, suffix)` (`pure` region) and the verified loops ARE the join. There is no consumed axiom. G-AX validates `joined == real col_str join` (mapping.md §3.1). `if len(suffix) > 0` ↔ Python truthiness `if suffix` on a `str` (empty ⇔ falsy); `append sep()` (`[32]`) + the suffix copy ↔ `'{} {}'.format(col, suffix)` (a single space between). |
| A5 | `return result` | `return col` | R | identity on character content. |

## B. Site 2 — `IndexColumns.__str__.col_str` (`django/db/backends/ddl_references.py:111-122`)

Gold hunk:
```
         col = '{} {}'.format(self.quote_name(column), self.opclasses[idx])
         try:
-            col = '{} {}'.format(col, self.col_suffixes[idx])
+            suffix = self.col_suffixes[idx]
+            if suffix:
+                col = '{} {}'.format(col, suffix)
         except IndexError:
             pass
         return col
```

Modeled by `render_column_with_opclass(base, suffix)`.

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | param `base: List[int]` | `col = '{} {}'.format(self.quote_name(column), self.opclasses[idx])` | R | the already-assembled "quoted column + opclass" `str` ↔ `List[int]` (mapping.md §2). This assembly runs upstream of the modeled join and is the `base` input; the join is insensitive to its content. |
| B2 | param `suffix: List[int]` | `suffix = self.col_suffixes[idx]` | R | same as A2. |
| B3 | copy `base` into `result` (the `j`-loop) | the base `col` text | R + I | as A3. |
| B4 | `if len(suffix) > 0: append sep() then suffix` else leave `result == base` | `if suffix: col = '{} {}'.format(col, suffix)` else `col` unchanged | A-reference + I | identical join to A4 (`joined`), the deep model validated by G-AX. The pre-patch did this UNCONDITIONALLY, leaving a trailing space for the empty suffix; the fix guards on `if suffix`. |
| B5 | `return result` | `return col` | R | identity on character content. |

## C. The two independently-observable fixed behaviours (G-DIFF)

The single join fix manifests as TWO distinct, independently-tested behaviours,
so there are two prepatch witnesses:

* **`model_prepatch.py` (site 1):** `render_column` reverts to the direct
  concatenation `base + suffix` (no separator), unconditionally. It FAILS the
  postcondition `ToSeq(Result()) == joined(...)` (and the
  `Result()[len(base)] == sep()` clause) for a non-empty suffix — exactly the
  missing-space bug the F2P `test_descending_columns_list_sql` observes
  (`"headline" DESC`, not `"headline"DESC`).
* **`model_prepatch_2.py` (site 2):** `render_column_with_opclass` reverts to
  appending the separator + suffix UNCONDITIONALLY. It FAILS the postcondition
  `ToSeq(Result()) == joined(...)` (and the `Implies(len(suffix)==0,
  Result()==base)` clause) for the empty suffix — the trailing-space bug for an
  opclass index without explicit ordering.

Both share the byte-identical frozen spec (axioms / pure / pre / post regions);
each fails on its own site's discriminating clause.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the conditional space-separated join — is modeled **deeply**
(`joined`, the verified loops), not hidden behind an axiom about the function
under change. There are **no consumed axioms**: `joined` is an **A-reference**
(G-AX checks `joined == real col_str join`); upstream callees (`quote_name`,
the opclass `str.format`) produce the join's `base` input and are not part of
the modeled operation.

## E. verify(model) ⇒ resolved

`render_column` / `render_column_with_opclass` verify only if their output
equals `joined(base, suffix)` — a single separating space before a non-empty
suffix (A4/B4) and the base verbatim for an empty suffix. By R (`str` ↔
`List[int]`, `'{} {}'.format`/`+` ↔ list `+` with `[32]`) the verified join
equals the gold `col_str` join at both sites; by G-AX the deep model `joined`
equals the real join (A-reference). Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the
gold patch resolves (G-RESOLVE). The single trust point is refinement fidelity
(this document, G-EQ) plus the G-AX A-reference check; there is no axiom
soundness obligation (no consumed axiom).
