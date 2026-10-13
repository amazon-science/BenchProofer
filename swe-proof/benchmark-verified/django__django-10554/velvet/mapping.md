# mapping.md — django__django-10554

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 14d026cccb144c6877294ba4cd4e03ebf0842498`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance / flag dependencies.

Repo files under change:
* `django/db/models/sql/compiler.py` — `SQLCompiler.get_order_by` (def at line
  254; the modeled hunk is the combinator branch at lines 343-359).
* `django/db/models/sql/query.py` — new method `Query.add_select_col` (added
  after `clear_select_fields`, def at line 1768).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolveOrderingTerm (candidates : List Candidate) (querySelectLen : Nat)` | the per–`(expr, is_ref)` body of the `for … else` search loop in `get_order_by` over `enumerate(self.select)` — `compiler.py:343-359` (post-patch 343-364) | the modeled changed behavior: how ONE ordering term is bound against the result-set columns |
| `querySelectLen : Nat` | `len(self.query.select)` BEFORE `add_select_col` runs — the QUERY's select tuple (`query.py`), a sequence DISTINCT from the compiler's `self.select` that the loop scans; e.g. with `.extra(select=…)` or annotations `len(self.select)` (compiler: extra + fields + annotations) exceeds `len(self.query.select)` (which can even be 0) | the pre-append length of the sequence the appended column lands in |
| `Candidate.aligns` | the loop's column-match test `src == sel_expr` (after the `is_ref`/`col_alias` unwrapping), `compiler.py:351-355` | whether the ordering term's source lines up with this select column |
| `Candidate.labelled` | `col_alias` truthiness for a select entry `(sel_expr, _, col_alias)`, `compiler.py:350` | whether the select column carries an explicit alias (label) |
| `firstAligned` | the `for idx, (sel_expr, _, col_alias) in enumerate(self.select): … if src == sel_expr: … break` search, `compiler.py:350-357` | 0-based index of the first matching select column |
| `disposition` | the whole resolved-term binding incl. the `else:` (no-`break`) clause, `compiler.py:355-364` post-patch | position bound / appended / rejected |
| `Disposition.position n` | `resolved.set_source_expressions([RawSQL('%d' % (idx + 1), ())])` then `break`, `compiler.py:356-357` | bind to the 1-based position of the matched column |
| `Disposition.appended n` | `self.query.add_select_col(src)` + `set_source_expressions([RawSQL('%d' % len(self.query.select), ())])`, post-patch `compiler.py:362-364` (the NEW behavior; `add_select_col` appends `src` to `self.query.select`, so `len(self.query.select)` = pre-append length + 1 = `querySelectLen + 1` is the value emitted — NOT `len(self.select) + 1`: `self.query.select` and the scanned `self.select` are different sequences with independent lengths) | append the term's source to the query's select tuple and bind to `querySelectLen + 1` |
| `Disposition.rejected` | `raise DatabaseError('ORDER BY term does not match any column in the result set.')`, `compiler.py:359` (pre-patch) / guarded by `if col_alias:` post-patch (`compiler.py:359-360`) | the term cannot be placed |

The pre-patch behavior the change replaces (refinement audit only; not in the
consumer spec view): the `for … else` always took `raise DatabaseError(...)` in
the no-`break` case (`compiler.py:358-359`). Post-patch the `else` raises ONLY
when `col_alias` is truthy for the trailing select entry, otherwise appends.

`add_select_col` (query.py, new) is the appended-column mechanism:
```python
def add_select_col(self, col):
    self.select += col,
    self.values_select += col.output_field.name,
```
After it runs, `len(self.query.select)` equals the old length + 1, i.e. the
1-based position of the just-appended column — exactly `Disposition.appended
(querySelectLen + 1)` where `querySelectLen` is `len(self.query.select)`
before the call. NOTE (faithfulness, G-PANEL-2 repair): `self.query.select`
is NOT the sequence the search loop scans. The loop scans the COMPILER's
`self.select` (extra-select entries + fields + annotations, assembled by
`pre_sql_setup`), while `add_select_col` grows the QUERY's `select` tuple.
With e.g. `Number.objects.extra(select={'ex':'num+100'})` in a union,
`len(compiler.select)` is 4 while `len(query.select)` is 0 → the emitted
ordinal is `0 + 1 = 1` ('ORDER BY (1)'), not `4 + 1 = 5`. Hence the model
carries the two lengths independently: `candidates` (compiler select, the
scanned sequence) and `querySelectLen` (query select tuple, the appended-into
sequence).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the modeled repo behavior.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.select`, a tuple `[(sel_expr, (sql,params), col_alias), …]` walked by the search loop | `List Candidate` | the `i`-th select entry ↔ `candidates[i]`; `len(self.select)` ↔ `candidates.length`; tuple order ↔ list order |
| `self.query.select`, the QUERY's select tuple (a separate sequence — see §1's `querySelectLen` row) | `querySelectLen : Nat` | `len(self.query.select)` before `add_select_col` ↔ `querySelectLen`; only its LENGTH is observable on the modeled branch (it determines the emitted ordinal) |
| `col_alias` (3rd element of a select entry — `None`/`''` vs a non-empty alias string) | `Candidate.labelled : Bool` | `bool(col_alias)` ↔ `labelled` (Python truthiness: `None`/`''` ↦ `false`, any non-empty alias ↦ `true`) |
| the match test `src == sel_expr` for this term, AFTER the `is_ref and col_alias == src.refs` ref-unwrapping and the `elif col_alias: continue` skip | `Candidate.aligns : Bool` | `True` iff this select entry is the first the loop's `if src == sel_expr` succeeds on for this term. The `elif col_alias: continue` means an aliased column that the term does not ref is never a match — folded into `aligns=false` for that entry (mapping.md §3). |
| the bound 1-based position `idx + 1` / `len(self.query.select)` | `Nat` inside `Disposition` | `idx + 1` ↔ `position (idx+1)`; the post-append length ↔ `appended (length+1)` |
| `raise DatabaseError('ORDER BY term does not match …')` | `Disposition.rejected` | the exception outcome modeled as a tagged result (SPEC_GUIDE §2: "exception raised" → tagged structure) |

The ordering term is processed against a NON-EMPTY `self.select` whenever the
fall-through is reachable (a combined query that produced columns); `require
candidates ≠ []` pins that the trailing-column inspection (`getLast?`) is well
defined. An empty `self.select` cannot reach the no-match `else` with a
trailing-column query in the F2P scenarios.

## 3. Callee provenance / abstracted machinery

There are **no axiomatized callees** and **no A-reference deep models of an
external callee** in this bundle. The only operation the gold patch CHANGES is
control-flow local to `get_order_by`: the disposition of an ordering term in the
no-match (`else`) case, now split by `col_alias` into rejected-vs-appended. That
change is modeled DEEPLY and CONCRETELY (`disposition` over the
`Candidate`/`Disposition` carriers) — no opaque oracle.

The surrounding machinery the loop calls — `resolve_expression`,
`get_source_expressions`, the `is_ref`/`col_alias == src.refs` ref-unwrapping,
`RawSQL`, `compile`, `add_select_col`'s `output_field.name` bookkeeping — is
UNCHANGED by the patch and does not affect WHICH disposition a term receives
beyond producing the per-candidate `aligns`/`labelled` booleans. It is therefore
abstracted to those two structural flags, supplied as the `Candidate` fields, and
exercised structurally by G-CONF (conformance_check.py), not asserted as an
axiom. Hence G-AX is vacuous (status=skip), as in the sibling control-flow
bundle django__django-11299.

### Flag dependency
The split the patch introduces is governed entirely by `bool(col_alias)` of the
trailing select column in the no-match case. G-CONF fuzzes both labelled and
unlabelled trailing columns (and labelled/unlabelled interior columns) so the
discriminating branch is covered.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`10554`** so the
consumer-side verdict (§11.3) is reproducible. The SHADOW is the
`firstAligned`/`lastLabelled`/`disposition` model from Solution.lean
transliterated to Python; the ORACLE is the PATCHED `get_order_by`
term-binding logic transliterated verbatim (the real `get_order_by` requires a
fully set-up DB compiler + combined query + resolved expressions to reach the
modeled branch — impractical to isolate; per the worker prompt the oracle is the
patched control flow transliterated, with the unchanged per-candidate
resolution folded to the `aligns`/`labelled` booleans). Both sides take the
query-select pre-append length as an independent input (fuzzed 0..8, crossed
exhaustively 0..4 with all small candidate sequences) so the two sequences'
length divergence is exercised. There are no A-tagged ops in the impl region,
so the shadow is pure R/I.
