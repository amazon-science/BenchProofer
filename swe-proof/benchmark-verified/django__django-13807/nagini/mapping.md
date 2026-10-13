# mapping.md — django__django-13807

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 89fc144dedc737a79929231438f035b1d4a993c9`, states the type
abstraction, and gives the provenance of the one axiomatized callee.

Repo file under change: `django/db/backends/sqlite3/base.py`
(method `DatabaseWrapper.check_constraints`, lines 316–353).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `build_single_table_command(table_name)` | the per-table foreign-key-check command assembled in `check_constraints` — `'PRAGMA foreign_key_check(%s)' % ...` (`django/db/backends/sqlite3/base.py:330`) | modeled changed site #1 (the F2P-observed one): the command text that names a single table |
| `build_three_id_command(ident_a, ident_b, ident_c)` | the bad-row lookup command assembled in `check_constraints` — `'SELECT %s, %s FROM %s WHERE rowid = %%s' % (...)` (`django/db/backends/sqlite3/base.py:341-343`) | modeled changed site #3: the command text that names two columns and a table. The three params `ident_a/b/c` are the spec-view-neutral images of the gold's `primary_key_column_name`, `column_name`, `table_name` (renamed in the consumer view to avoid disclosing the undisclosed column-quoting site — see meta.json G-LEAK note) |
| `delimit(name)` *(axiom — A-consumed, pure)* | `DatabaseOperations.quote_name` — `django/db/backends/sqlite3/operations.py:170-173`, reached as `self.ops.quote_name(...)` | unchanged backend callee the patch routes every spliced identifier through; pure spec of its code-point behaviour |
| `delimit_id(name)` *(axiom — A-consumed, runtime counterpart of `delimit`)* | same callee `self.ops.quote_name(name)` at the call sites added by the patch (`base.py:330,336,341-343` post-patch) | the actual runtime call returning the delimited identifier as a fresh string; content == `delimit(name)` |
| `single_table_prefix` | the literal `'PRAGMA foreign_key_check('` | pure spec: fixed command prefix as code points |
| `close_paren` | the literal `')'` | pure spec |
| `three_id_head` / `three_id_sep` / `three_id_mid` | the literals `'SELECT '`, `', '`, `' FROM '` | pure spec: the constant fragments of the three-identifier command. Modelled as **opaque placeholder code points** (`[1,2]`, `[3]`, `[4,5]`) rather than the literal SQL bytes, because the SQL spelling would disclose the undisclosed site #3 in the consumer spec view (G-LEAK). Only their constancy (identical across the twins) and the ordering of the three delimited identifiers they interleave are load-bearing; their content carries no tested behaviour |

The gold patch has a third quoting change, site #2 —
`'PRAGMA foreign_key_list(%s)' % table_name` →
`% self.ops.quote_name(table_name)` (`base.py:336`). It is the **same**
single-identifier delimiting fix as site #1 (`build_single_table_command`):
identical operation, identical refinement, identical discriminating clause. It
is therefore covered by the site-#1 model rather than a redundant third
contracted function (refinement.md §B notes the 1:1 correspondence). All three
sites share the bug class "a schema identifier is spliced into command text
without delimiting it".

The pre-patch repo construct the change removes (for the refinement audit, not
referenced from the consumer spec view): the bare `% table_name` /
`% (primary_key_column_name, column_name, table_name)` string interpolations at
`base.py:330,336,342`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` table/column identifier (`table_name`, `column_name`, `primary_key_column_name`) | `List[int]` of Unicode code points | `name[k]` ↔ `ord(name[k])`; `len(name)` ↔ `len`; empty `str` ↔ `[]` |
| `str` SQL command text built by `% ...` interpolation | `List[int]` (the assembled command), specified over `PSeq[int]` via `ToSeq` | `'PREFIX' % x` is the concatenation `prefix_codepoints + codepoints(x)`; modeled as list `+` / `PSeq` `+` |
| `'PRAGMA foreign_key_check(%s)' % q` | `single_table_prefix() + q + close_paren()` | the format string is the fixed prefix `'PRAGMA foreign_key_check('`, the substituted value, then `')'` |
| `'SELECT %s, %s FROM %s WHERE rowid = %%s' % (a,b,c)` | `three_id_head()+a+three_id_sep()+b+three_id_mid()+c` (the constant fragments are opaque placeholders; the `WHERE rowid = ?` tail is a constant, identifier-free suffix, omitted) | the three `%s` are the three delimited identifiers in order; the constant fragments are content-irrelevant (only their constancy + the identifier ordering matter); the suffix contains no schema identifier so it carries no tested behaviour |
| `self.ops.quote_name(name)` | `delimit(ToSeq(name))` (spec) / `delimit_id(name)` (runtime) | the backend delimiter; see §3 |

`str` indexing/iteration is banned in Nagini, so identifiers are `List[int]`
and command text is specified over `PSeq[int]` via `ToSeq`. The trailing
`WHERE rowid = %%s` parameter placeholder is a constant, identifier-free suffix
of the SELECT command (the row id is bound as a query parameter, not spliced),
so it is observationally irrelevant to the modeled behaviour and omitted; this
does not weaken the discriminating clause, which is entirely about the three
spliced identifiers.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### `delimit` / `delimit_id` ↔ `sqlite3 DatabaseOperations.quote_name` (A-consumed)
**Callee** (`django/db/backends/sqlite3/operations.py:170-173`, verbatim at
base_commit):

```python
def quote_name(self, name):
    if name.startswith('"') and name.endswith('"'):
        return name  # Quoting once is enough.
    return '"%s"' % name
```

`self.ops` in `check_constraints` is this class (`base.py:173`,
`ops_class = DatabaseOperations`). The axiom encodes exactly this, over code
points (delimiter = code point 34, the ASCII double quote `"`):

  * **already-delimited** — `name` begins AND ends with the delimiter
    (`name.startswith('"') and name.endswith('"')`; note a lone `"` of length 1
    satisfies both, since `'"'.startswith('"')` and `'"'.endswith('"')` are both
    True): returned **unchanged**;
  * **otherwise** — wrapped to `'"' + name + '"'`, i.e. `[34] + name + [34]`.

This is the WEAKEST contract the proof needs and is exactly the observed
behaviour — not stronger (it does not claim, e.g., escaping of interior quotes;
the real method does not escape either). It never raises on a `str` input.

The discriminating consequence: a SQL **reserved word** identifier (e.g.
`order`, `select`, `where` — the F2P case) is not already delimited, so
`quote_name` returns the strictly-longer `"order"`; the command text must
contain that delimited form for the word to be parsed as a name rather than the
keyword. The pre-patch impl splices the bare word and the spec rejects it.

`delimit_id` is the same callee viewed as a runtime list-returning call (the
literal `self.ops.quote_name(name)` at the patched call sites); its `Ensures`
ties its observable content to `delimit(name)`, so the single G-AX check on
`quote_name` covers both.

**Soundness check (G-AX):** `axiom_check.py` configures Django in-container,
instantiates the sqlite3 `DatabaseOperations`, and runs the REAL
`ops.quote_name` on 24 boundary identifiers (SQL keywords; ordinary names;
already-delimited names; the lone-`"` edge; non-ASCII; names with spaces /
semicolons / interior quotes / one-sided quotes) plus 20 000 randomized fuzz
identifiers, asserting every observation equals the `delimit` axiom's `Ensures`
and is delimiter-bracketed, and that quoting is idempotent. Exit 0 iff sound.
No flag dependency (the method takes no keyword arguments).
