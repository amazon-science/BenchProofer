# mapping.md — django__django-10554

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 14d026cccb144c6877294ba4cd4e03ebf0842498`, states the type
abstraction, and records that this bundle has **no axiomatized callees** (the
whole observed behaviour is modelled deeply, so there is nothing for G-AX to
execute).

Repo files under change:
`django/db/models/sql/compiler.py` (the rewrite of one ORDER BY term inside
`SQLCompiler.get_order_by`, in the `if self.query.combinator:` block) and
`django/db/models/sql/query.py` (a new one-line helper `Query.add_select_col`
that the rewrite calls to add the column).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `relabel_order_term(cols, src, aliased)` | the body of the `for idx, (sel_expr, _, col_alias) in enumerate(self.select): ... else: ...` loop inside `SQLCompiler.get_order_by` — `django/db/models/sql/compiler.py:351-363` | the modelled changed behaviour: rewrite ONE ordering term of a combined query into a 1-based position in the result set's column list, choosing among match / append / reject |
| `cols: List[int]` | `self.select` (the compiler's tuple of `(expr, (sql, params), alias)` triples), abstracted to the list of selected-column identities, plus the column list grown by `self.query.add_select_col` / `self.query.select` | the result set's current column list; the only mutated object |
| `src: int` | `src = resolved.get_source_expressions()[0]` (the column the ordering term resolves to, after the `is_ref`/`col_alias` unwrapping) | the identity of the column an ORDER BY term refers to |
| `aliased: bool` | `col_alias` being truthy on the unmatched term — i.e. whether the selected entry the term would correspond to is an aliased/derived expression rather than a plain column | the discriminator deciding reject-vs-append on a no-match |
| `first_pos(src, cols)` *(deep @Pure spec)* | the index search `for idx, (sel_expr, _, col_alias) in enumerate(self.select): ... if src == sel_expr: ... break` — the position of the FIRST selected column equal to the term (0 if none) | pure spec: leftmost matching 1-based position, modelled deeply (front-recursive fold) |
| `OrderTermUnmatched` *(user exception)* | `raise DatabaseError('ORDER BY term does not match any column in the result set.')` | a user-defined stand-in for the error raised when an aliased term matches no column (a builtin-exception `Exsures` crashes the Nagini translator) |

The position assignment `resolved.set_source_expressions([RawSQL('%d' % (idx + 1), ())])`
(match) and `RawSQL('%d' % len(self.query.select), ())` (append) are abstracted
to the returned 1-based integer position; the downstream `RawSQL` rendering is
not modelled (outside the pinned behaviour).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.select` — a tuple of `(sel_expr, (sql,params), col_alias)` triples | `cols: List[int]` of column identities | the k-th selected column ↔ `cols[k]`; "`src == sel_expr` for some selected entry" ↔ "`cols[k] == src` for some k"; `len(self.select)` ↔ `len(cols)` |
| the resolved ordering column `src` | `src: int` | the column identity the term refers to (an opaque equality token; the model only needs `==` against selected columns, which is what the real `src == sel_expr` test uses) |
| `col_alias` truthiness on the no-match path | `aliased: bool` | the real code appends only when the unmatched term has no alias (`if col_alias: raise … else: add_select_col`); the boolean carries exactly that distinction |
| `self.query.add_select_col(src)` then `self.query.select` grows by one; new position is `len(self.query.select)` | `cols.append(src)`; new position `len(cols)` | the gold helper does `self.select += col,` (length grows by 1, the column is appended at the end); modelled as a list append, with the new 1-based position equal to the new length |
| `raise DatabaseError(...)` | `raise OrderTermUnmatched()` | abstract "the request is rejected"; user exception so the `Exsures` is translatable |

`self.select` indexing/iteration and the rich expression objects are abstracted
to `List[int]`; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Conformance check (G-CONF)

`conformance_check.py` runs the contract-stripped impl region against the real
patched rewrite in `SQLCompiler.get_order_by` (column identity k realized as a
`RawSQL('COL_<k>', ())` selected expression; `aliased` realized as one trailing
aliased never-matching selected entry) on >= 1e5 inputs. **Pinned fuzz seed:
10554.**

## 4. Callee provenance (kind-A) — NONE

This bundle axiomatizes **no callees**. The one helper the patched line calls,
`Query.add_select_col` (`django/db/models/sql/query.py`), is itself **added by
the same patch** and does nothing but `self.select += col,` (plus a parallel
`values_select` append that does not affect the observed ordering positions);
its sole observable effect — the column list grows by one at the end and the new
position is the new length — is modelled directly by `cols.append(src)` (an
**identical** concrete operation under the `self.select` ↔ `cols` refinement),
not axiomatized. There is therefore nothing for `axiom_check.py` / G-AX to run,
and no `@ContractOnly` declaration in `model.py` (the `axioms` region is empty
by design). The match-search loop and the reject/append decision are modelled
deeply (the `first_pos` fold + the explicit branch), so they are references the
model IS, not callees it consumes.
