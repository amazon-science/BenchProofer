# mapping.md — django__django-12039

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 58c1acb1d6054dfec29d0f30b1033bae6ef62aec`, states the type
abstraction, and records the provenance of the deeply-modelled operation.

Repo file under change: `django/db/backends/ddl_references.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `render_column(base, suffix)` | `Columns.__str__`'s inner `col_str(column, idx)` — `django/db/backends/ddl_references.py:85-89` | the modeled changed function, **site 1**. `base` = the quoted column `self.quote_name(column)`; `suffix` = `self.col_suffixes[idx]`. |
| `render_column_with_opclass(base, suffix)` | `IndexColumns.__str__`'s inner `col_str(column, idx)` — `django/db/backends/ddl_references.py:112-120` | the modeled changed function, **site 2**. `base` = the quoted column already combined with its operator class, `'{} {}'.format(self.quote_name(column), self.opclasses[idx])`; `suffix` = `self.col_suffixes[idx]`. |
| `joined(base, suffix)` *(deep model — A-reference)* | the `col_str` join logic introduced by the gold patch at BOTH sites: `if suffix: col = '{} {}'.format(col, suffix)` (else `col` unchanged) | pure spec: the rendered text of one column reference; the deep model of the changed join, validated `joined == real col_str join` by axiom_check.py (G-AX), NOT consumed as an axiom. |
| `sep()` | the literal space `' '` inside `'{} {}'.format(...)` | pure spec: the separator code point U+0020 (32). |

The pre-patch repo behaviour the change replaces (for the refinement audit, not
referenced from the consumer spec view):
* **Site 1** (`:87,:89`): `return self.quote_name(column) + self.col_suffixes[idx]`
  — direct concatenation, NO separating space, with `self.quote_name(column)` as
  the `IndexError` fallback. For a non-empty ordering suffix (`'DESC'`) this
  produces `"name"DESC` (the keyword fuses with the column).
* **Site 2** (`:117`): `col = '{} {}'.format(col, self.col_suffixes[idx])`
  — appended UNCONDITIONALLY. For the empty-string suffix (ascending order)
  this produces `"name" text_pattern_ops ` (a trailing space).

Why the suffix is the empty string, not absent: `Index.__init__` builds
`fields_orders` as `(name, 'DESC') if '-'-prefixed else (name, '')`
(`django/db/models/indexes.py:30-33`), and `Index.create_sql` passes
`col_suffixes = [order[1] for order in self.fields_orders]`
(`indexes.py:51`). So `self.col_suffixes` is the SAME length as the columns and
contains `''` for ascending order — the `IndexError` path is effectively dead in
the tested flow; the discriminator is empty-string-suffix vs non-empty-suffix.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (`col` / the quoted column / opclass-combined base, and the ordering suffix) | `List[int]` of Unicode code points | `s[k]` ↔ `base[k] == ord(s[k])`; `len(s)` ↔ `len(base)`; `str` concatenation / `'{} {}'.format(a, b)` ↔ list `+` with a `[32]` separator; an empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `self.quote_name(column)` (site 1 base) | the opaque input `base: List[int]` | the quoting callee runs UPSTREAM of the modeled join; its result is the join's `base` input. The join is insensitive to the base's content, so it is modeled as an arbitrary code-point list. |
| `'{} {}'.format(self.quote_name(column), self.opclasses[idx])` (site 2 base) | the opaque input `base: List[int]` | likewise upstream of the join; the already-assembled "column + opclass" token is the join's `base` input. |
| `self.col_suffixes[idx]` | the input `suffix: List[int]` | the ordering suffix, `''` (ascending) → `[]`, or e.g. `'DESC'` → `[68,69,83,67]`. |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Deep-modelled operation provenance (A-reference — checked by G-AX)

### 3.1 `joined` deep model ↔ the real `col_str` join (A-reference)

The changed operation is the *join* of the base token with the ordering suffix.
The gold patch makes BOTH sites perform the identical join:

```python
col = <base>                      # site 1: quote_name(column)
                                  # site 2: '{} {}'.format(quote_name(column), opclasses[idx])
try:
    suffix = self.col_suffixes[idx]
    if suffix:                    # <- the fix: only when the suffix is non-empty
        col = '{} {}'.format(col, suffix)
except IndexError:
    pass
return col
```

This is exactly `joined(base, suffix)` in `model.py`'s `pure` region:
`base` when `suffix` is empty, else `base + ' ' + suffix`. There is **no
`@ContractOnly` axiom** the proof consumes; the join is spelled out and the
verified loops in `render_column` / `render_column_with_opclass` compute it.
The deep model is validated **== the real join** out-of-band by `axiom_check.py`
(G-AX): it runs the real Python `str.format`/truthiness join (the gold logic,
identical at both sites) on boundary + 20 000 fuzz `(base, suffix)` pairs and
asserts `joined == real col_str join`, plus the structural guarantees (empty
suffix → no trailing space; non-empty suffix → a single separating space, no
fusion). `str.format`/`+` are the Python standard library; nothing
repo-specific is imported.

The behavioural discriminator the F2P test observes: for a descending column
(`fields=['-headline']`, suffix `'DESC'`) the rendered text must be
`"headline" DESC` (a space before `DESC`), not `"headline"DESC`. This lives in
`joined`'s non-empty branch (`base + PSeq(32) + suffix`) ⇔ the gold's
`'{} {}'.format(col, suffix)`. The pre-patch site-1 concatenation
(`quote_name(column) + col_suffixes[idx]`) omits the space;
`model_prepatch.py` reproduces it and FAILS the postcondition. For the empty
suffix (ascending / opclass-without-order), the rendered text must equal the
base exactly with no trailing space; the pre-patch site-2 unconditional append
adds one, and `model_prepatch_2.py` reproduces that and FAILS.

## 4. Axioms

None. This bundle consumes no `@ContractOnly` axioms: every upstream callee
(`quote_name`, `str.format` for the opclass) produces the join's `base` input
and is not part of the modeled join; the changed join itself is modeled deeply
(§3.1) and checked by G-AX as an A-reference.
