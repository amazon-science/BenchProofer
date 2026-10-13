# refinement.md — django__django-12039

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `renderColumn` `do` block, plus the deep `columnText` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — A-consumed / A-reference), or **I** (identical
concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); there are no A legs in this bundle (mapping.md §3). Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The modeled site — `Columns.__str__.col_str` (`ddl_references.py:85`)

Gold hunk (first hunk):
```
 def col_str(column, idx):
+    col = self.quote_name(column)
     try:
-        return self.quote_name(column) + self.col_suffixes[idx]
+        suffix = self.col_suffixes[idx]
+        if suffix:
+            col = '{} {}'.format(col, suffix)
     except IndexError:
-        return self.quote_name(column)
+        pass
+    return col
```

| # | Solution.lean impl op (`renderColumn`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `name : List Char` | `self.quote_name(column)` (`col = self.quote_name(column)`) | R | quoted-name token `str` ↔ `List Char` (mapping.md §2); `quote_name` is an unchanged callee absorbed into the carrier, identity in G-CONF. |
| A2 | param `suffixes : List (List Char)`, `idx : Nat` | `self.col_suffixes`, `idx` | R | tuple-of-`str` ↔ `List (List Char)`; `''` ↔ `[]`; positions identity (mapping.md §2). |
| A3 | `if idx < suffixes.length then …` | `try: suffix = self.col_suffixes[idx] … except IndexError:` | I | the bounds test: an in-range subscript vs `IndexError`. `idx < suffixes.length` ⇔ no `IndexError`; `≥` ⇔ `IndexError` (the `except` body is `pass`, then `return col`). |
| A4 | `if suffix ≠ [] then col := name ++ ' ' :: suffix` | `if suffix: col = '{} {}'.format(col, suffix)` | I | non-empty test `suffix ≠ []` ⇔ Python truthiness of a `str` (`''` is falsy, any non-empty str truthy); `'{} {}'.format(col, suffix)` ⇔ `name ++ ' ' :: suffix` (exactly one separating space). This is the behavioural change. |
| A5 | `return col` (initialised `col := name`, possibly updated) | `return col` (after the `try/except`) | I | when the qualifier is absent OR empty, `col` stays `name` — emits the bare name, no trailing space. Matches the post-patch flow. |
| A6 | (outside the method) per-column `columnText` joined by `", "` | `', '.join(col_str(c, i) for …)` | I | unchanged glue; G-CONF exercises the full `Columns.__str__` multi-column render, not just one column. |

Discriminating content of the change — a **non-empty** qualifier is now preceded
by exactly one space (`name ++ ' ' :: suffix`), and an **empty** qualifier
(`''`, the ascending case) contributes nothing. The pre-patch bare concatenation
`self.quote_name(column) + self.col_suffixes[idx]` is reproduced in
`Solution_prepatch.lean` (`name ++ suffixes[idx]!`), which **fails**
`out = columnText name suffixes idx` on the supplied-non-empty-qualifier case
(the `'-headline' → 'DESC'` input the F2P `test_descending_columns_list_sql`
observes): `"name"DESC` vs the required `"name" DESC` (G-DIFF).

The empty-qualifier branch (A4 false) is what the P2P `test_columns_list_sql`
(ascending field → `''` suffix) observes: output is the bare name, no trailing
space — already satisfied by both pre- and post-patch *for the ascending field
in `Columns`*, and by the spec's `columnText` empty-qualifier branch.

## B. The parallel test-neutral site — `IndexColumns.__str__.col_str`

Gold second hunk applies the byte-identical whitespace fix to
`IndexColumns.__str__`'s `col_str` (`ddl_references.py:117-120`, post-patch).
Its observing tests are PostgreSQL-only (`@skipUnless`/`@skipIf` on the
postgresql vendor), so they are **skipped** on the SQLite eval image and are
**test-neutral** for G-RESOLVE (mapping.md §1). The fix is the same op as A4/A5
(append non-empty qualifier with one space), so no separate modeled method and
no separate failing prepatch is needed: a `Solution_prepatch_<k>` must keep the
spec byte-identical and would fail on the *same* clause as site A. Mirrors the
11276 site-B (urlize callee swap) treatment — one modeled site carries the
discriminating behaviour, the parallel edit is audited by this note + G-CONF
(which can also exercise `IndexColumns` should coverage be extended) but is not
independently test-observable.

## B2. Termination semantics

The file uses `loom.semantics.termination "total"` (total correctness). The
real `col_str` is straight-line string formatting that always terminates and
returns, and the F2P test observes its return value (the rendered
`(%s DESC)` SQL fragment), so total correctness is the faithful semantics.
Partial correctness would admit a same-spec implementation that diverges (an
infinite loop in the non-empty-qualifier branch vacuously satisfies every
`ensures`) — a wrong impl the tests would fail — so it would leave the spec
too weak.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — the per-column
qualifier rendering — is modeled **deeply** (the spelled-out `columnText`, steps
A3–A5, all **I**), not hidden behind an axiom about the function under change.
There are no consumed axioms and no A-reference deep models (mapping.md §3); the
unchanged callee `quote_name` is an R-refinement carrier, not an axiom.

## D. verify(Solution) ⇒ resolved

`renderColumn` verifies only if its output equals `columnText` exactly: a
non-empty qualifier yields `name ++ ' ' :: suffix` (one separating space, A4),
an empty qualifier or an out-of-range position yields the bare `name` (A4 false
/ A3 false, A5). By R (`str ↔ List Char`, `quote_name`/positions identities) the
verified renderer equals the post-patch `col_str` on the tested inputs; by G-CONF
the R/I transliteration of `columnText`, joined into the full `Columns.__str__`,
agrees with `patch.diff`'s behaviour on ≥10⁵ inputs. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). There are no axiom trust
points (mapping.md §3); the only residual trust is refinement fidelity, which
G-CONF + G-EQ cover.
