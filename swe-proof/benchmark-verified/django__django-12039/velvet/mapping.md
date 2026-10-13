# mapping.md — django__django-12039

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 58c1acb1d6054dfec29d0f30b1033bae6ef62aec`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

Repo file under change: `django/db/backends/ddl_references.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `renderColumn (name, suffixes, idx)` | the inner `col_str(column, idx)` closure of `Columns.__str__` — `django/db/backends/ddl_references.py:85` (body `:87`) | the modeled changed function: text of one indexed column reference |
| `columnText (name, suffixes, idx)` | the post-patch semantics of that same `col_str` — `django/db/backends/ddl_references.py:85-91` (post-patch) | pure spec: rendering of one column |
| `name : List Char` | `self.quote_name(column)` — the already-quoted column-name token (`ddl_references.py:87`) | input carrier; the unchanged name-quoting callee's result, not modeled as an axiom |
| `suffixes : List (List Char)` | `self.col_suffixes` — `django/db/backends/ddl_references.py:80` (set in `__init__` `:80`) | per-column trailing qualifiers (ordering tokens) |
| `idx : Nat` | the `idx` position from `enumerate(self.columns)` (`ddl_references.py:91`) | position of this column |

Context for the carrier `suffixes`: `col_suffixes` is constructed in
`django/db/models/indexes.py:51` as `[order[1] for order in self.fields_orders]`,
where `fields_orders` (`indexes.py:30-33`) is `(field_name[1:], 'DESC')` for a
`-`-prefixed field and `(field_name, '')` otherwise. So for an ascending field
the qualifier is the **empty string** `''` (NOT absent) — the precise condition
the issue describes ("it will contain empty strings"). The descending qualifier
is the token `'DESC'`. An `IndexError` (the original `try/except`) occurs only
when `idx` exceeds `len(col_suffixes)` — modeled as `idx ≥ suffixes.length`.

### Parallel (test-neutral) second site

The gold patch makes the byte-identical whitespace fix to the inner `col_str`
of `IndexColumns.__str__` (`django/db/backends/ddl_references.py:111-119`,
post-patch `:117-120`). Its observing tests
(`test_ops_class_columns_lists_sql`, `test_ops_class_descending_columns_list_sql`)
live in `@skipUnless(connection.vendor == 'postgresql', …)` /
`@skipIf(connection.vendor == 'postgresql', …)` classes
(`tests/indexes/tests.py:79,116,…`), so they are **skipped** on the SQLite
eval image. The behaviour is identical to site A (append a qualifier only when
non-empty, with one separating space; `opclasses[idx]` is always present per the
`Index.__init__` length guarantee, `ddl_references.py:113-114`), so site A's
modeled `columnText` captures the only harness-observable change. Mirrors the
11276 site-B (urlize) pattern: one modeled site, one test-neutral parallel edit.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

The table G-CONF (§4.1) uses to translate values between the Lean value domain
and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.quote_name(column)` — the quoted name token (a `str`) | `name : List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `str` concat ↔ `List` `++`; a single ASCII space `' '` ↔ `' '`. G-CONF uses `quote_name = identity`, so the token equals the raw column string (its quoting is an unchanged callee, out of scope of the change). |
| `self.col_suffixes` — a tuple/list of `str` | `suffixes : List (List Char)` | `tuple/list of str` ↔ `List (List Char)`, element-wise via the row above; `len(col_suffixes)` ↔ `suffixes.length`; the empty string `''` ↔ `[]`; absent position (`idx ≥ len`) ↔ `idx ≥ suffixes.length`. |
| `enumerate(self.columns)` index `idx` | `idx : Nat` | identity on positions. |
| `', '.join(col_str(c, i) for i, c in enumerate(columns))` (the unchanged surrounding render) | per-column `columnText` joined by `", "` (outside the verified method; checked by G-CONF over the full multi-column render) | `', '.join` ↔ list-of-`columnText` interspersed with `", "`. Unchanged glue (I). |

Lean `List Char` is total/sound to index; `suffixes[idx]!` with the guard
`idx < suffixes.length` never hits the default. The `try/except IndexError` of
the real code is modeled by the total guard `idx < suffixes.length` vs `≥`.

## 3. Callee provenance

**No axiomatized callees (no A-consumed, no A-reference).** The single modeled
operation is the *changed* op itself (`col_str`'s rendering), spelled out deeply
as `columnText` and validated against the real patched behaviour by G-CONF
(`conformance_check.py`), not by an axiom. The unchanged callee `quote_name` is
absorbed into the input carrier `name` (R-refinement, identity in G-CONF), so it
needs no contract. Consequently `axiom_check.py` (G-AX) has no obligation to
discharge and reports `status="skip"` (`reason="no-axioms"`).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`12039`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `columnText` (all R/I-tagged ops) to Python and compares the full
multi-column `Columns.__str__` render against the real patched `Columns`
(`quote_name = identity`). There are no A-tagged callees to leave as real-callee
calls in the shadow.
