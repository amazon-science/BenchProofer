# refinement.md — django__django-13807

The operation-by-operation correspondence between `model.py`'s implementation
(`build_single_table_command`, `build_three_id_command`, and the consumed
`delimit` / `delimit_id` axioms) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX), or
**I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

The whole change is one bug class applied at three splice sites in
`check_constraints` (`django/db/backends/sqlite3/base.py`): a schema identifier
was interpolated into SQLite PRAGMA / SELECT command text **bare**; the fix
routes each through `self.ops.quote_name(...)` so a reserved-word identifier
(`order`) is delimited (`"order"`) instead of producing a syntax error.

## A. Site #1 — `PRAGMA foreign_key_check(%s)` (`base.py:330`)

Gold hunk:
```
- cursor.execute('PRAGMA foreign_key_check(%s)' % table_name).fetchall()
+ cursor.execute(
+     'PRAGMA foreign_key_check(%s)'
+     % self.ops.quote_name(table_name)
+ ).fetchall()
```

Model: `build_single_table_command(table_name)`.

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `table_name: List[int]` | `table_name: str` | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| A2 | `quoted = delimit_id(table_name)` | `self.ops.quote_name(table_name)` | A-consumed | `delimit_id` IS the runtime `quote_name` call; its `Ensures` (`ToSeq == delimit(...)`) is the consumed contract. Soundness: G-AX (mapping.md §3). |
| A3 | `result = [80,82,...,40] + quoted + [41]` | `'PRAGMA foreign_key_check(%s)' % <quoted>` | R + I | `'PRAGMA foreign_key_check(' ` is the literal code-point prefix (`single_table_prefix()`), `%s` is the substituted delimited identifier, `')'` is the suffix; `% ` interpolation ↔ list `+` (mapping.md §2). The literal code points are the ASCII of the format string (I). |
| A4 | postcondition `ToSeq(Result()) == single_table_prefix() + delimit(ToSeq(table_name)) + close_paren()` | the assembled command string the gold passes to `cursor.execute` | R | states the command text is the prefix, the **delimited** identifier, the suffix — exactly the gold's `% self.ops.quote_name(table_name)`. |

## B. Site #2 — `PRAGMA foreign_key_list(%s)` (`base.py:336`)

Gold hunk:
```
- 'PRAGMA foreign_key_list(%s)' % table_name
+ 'PRAGMA foreign_key_list(%s)' % self.ops.quote_name(table_name)
```

This is the **identical single-identifier delimiting fix** as site A (same
operation: one schema identifier, spliced bare → spliced delimited), differing
only in the fixed literal prefix (`foreign_key_list` vs `foreign_key_check`).

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `build_single_table_command` (the A2/A4 delimiting + splice) | `% self.ops.quote_name(table_name)` at `base.py:336` | A-consumed + R | bijective with site A under "swap the fixed literal prefix". The discriminating clause (delimited vs bare identifier) is byte-for-byte the same; modeling a second contracted function with a different constant prefix would add no differential witness, so site B is represented by the site-A model (mapping.md §1). |

## C. Site #3 — `SELECT %s, %s FROM %s WHERE rowid = %%s` (`base.py:341-343`)

Gold hunk:
```
- 'SELECT %s, %s FROM %s WHERE rowid = %%s' % (
-     primary_key_column_name, column_name, table_name
- ),
+ 'SELECT %s, %s FROM %s WHERE rowid = %%s' % (
+     self.ops.quote_name(primary_key_column_name),
+     self.ops.quote_name(column_name),
+     self.ops.quote_name(table_name),
+ ),
```

Model: `build_three_id_command(ident_a, ident_b, ident_c)`.

The three model parameters `ident_a`, `ident_b`, `ident_c` are the
representation-neutral images of the gold's `primary_key_column_name`,
`column_name`, `table_name` respectively (renamed in the consumer-visible view
to avoid disclosing the undisclosed column-quoting site — see G-LEAK note in
meta.json). The three opaque model constants map to the gold's literal format
fragments under the representation map: `three_id_head()` ↔ `'SELECT '`,
`three_id_sep()` ↔ `', '`, `three_id_mid()` ↔ `' FROM '`. Their concrete code
points (`[1,2]`, `[3]`, `[4,5]`) are abstraction-irrelevant placeholders: the
only load-bearing properties are (i) their constancy — identical in `model.py`
and `model_prepatch.py`, so the sole differential between the twins is
delimit-vs-bare — and (ii) the ordering of the three delimited identifiers they
interleave. No tested behaviour depends on the separators' content (cf. the
omitted constant suffix below); this is the same kind of behaviour-irrelevant
abstraction as omitting `WHERE rowid = %%s`.

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | three params `List[int]` (`ident_a/b/c`) | three `str` identifiers (`primary_key_column_name`, `column_name`, `table_name`) | R | `str` ↔ `List[int]` (mapping.md §2); names abstracted in the spec view. |
| C2 | `a = delimit_id(ident_a)`, `b = delimit_id(ident_b)`, `c = delimit_id(ident_c)` | `self.ops.quote_name(...)` x3 | A-consumed | three calls to the same axiomatized `quote_name`; each `delimit_id` `Ensures` consumed. |
| C3 | `result = three_id_head() + a + three_id_sep() + b + three_id_mid() + c` | `'SELECT %s, %s FROM %s ...' % (pk, col, tbl)` | R + I | the three `%s` map to the three delimited identifiers in order; the constant fragments `'SELECT '`, `', '`, `' FROM '` are represented by the opaque placeholder constants `three_id_head/sep/mid` (R, content-irrelevant); `% ` interpolation ↔ list `+` (I-shaped). |
| C4 | postcondition equates `ToSeq(Result())` to that exact concatenation | the assembled SELECT text | R | pins each spliced identifier to its **delimited** form, in order, around the (abstracted) constant fragments. |

The trailing `WHERE rowid = %%s` is an identifier-free constant suffix (the row
id is bound as a query parameter, not spliced), carries no tested behaviour, and
is omitted from the model (mapping.md §2) — omitting a constant identifier-free
suffix removes no discriminating obligation.

## D. The discriminating change & the prepatch

The behavioural delta at all three sites is identical: the interpolated value is
`self.ops.quote_name(identifier)` (delimited) rather than `identifier` (bare).
`model_prepatch.py` reproduces the pre-patch skeleton — it splices the **bare**
identifier (an element-wise copy of the input list) at both modeled sites — and
**fails** the postconditions
`ToSeq(Result()) == single_table_prefix() + delimit(ToSeq(table_name)) + close_paren()`
and the three-identifier analogue, because `delimit(name) != name` whenever `name` is
not already delimited (e.g. the reserved word `order`: `delimit` adds two
delimiters). This is exactly the spec sensing the bug (G-DIFF). One prepatch
covers both modeled behaviours because the bug class and the discriminating
clause are the same at every site.

## E. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The changed operation — interpolating
the delimited identifier instead of the bare one — is modeled **concretely**:
the splice is list concatenation (R+I), and the only opaque part, the backend
delimiter `quote_name`, is an **unchanged callee** the new code merely *calls*,
so it is the consumed axiom `delimit` (A-consumed), NOT the function under
change. There is no `A-reference` deep model here (the delimiter is unchanged,
hence axiomatized, not re-derived) and no dead axiom (`delimit` / `delimit_id`
are consumed at A2 / C2). The thing that genuinely changed (bare → delimited) is
spelled out in the contract, not hidden behind an axiom about the changed op.

## F. verify(model) ⇒ resolved

`build_single_table_command` / `build_three_id_command` verify only if their
output is the command text with each identifier in its **delimited** form (A4,
C4) — i.e. exactly `% self.ops.quote_name(...)`. By R (str ↔ List[int], `% `
interpolation ↔ concatenation, literal format fragments ↔ their — possibly
abstracted — code points) the
verified commands equal the gold's assembled strings on the tested identifiers;
by G-AX the `delimit` axiom over-approximates the real `quote_name` (A-consumed,
mapping.md §3). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the audited callee — and the gold
patch resolves (G-RESOLVE: the F2P `test_check_constraints_sql_keywords` passes,
because `check_constraints(table_names=['order'])` now issues
`PRAGMA foreign_key_check("order")` and raises `IntegrityError` instead of the
pre-patch `OperationalError: near "order": syntax error`). The trust points are
exactly the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity
(this document, G-EQ).
