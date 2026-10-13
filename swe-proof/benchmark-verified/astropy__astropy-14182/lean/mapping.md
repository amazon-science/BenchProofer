# mapping.md — astropy__astropy-14182

## Symbol binding (file:line @ base_commit a5917978be39d13cd90b517e1de4e7a539ffaa48)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_rstWrap` / `problem_spec_rstWrap` / `correct_rstWrap` | `RST.write(self, lines)` — the line that brackets the rendered table with a separator line | `astropy/io/ascii/rst.py:63-66` |
| `implementation_rstDataStart` / `problem_spec_rstDataStart` / `correct_rstDataStart` | the data start-line position used when parsing an `ascii.rst` table (the value assigned to `self.data.start_line`) | `astropy/io/ascii/rst.py` — class attr `SimpleRSTData.start_line = 3` (base), replaced by the new `RST.read` override |

The format under specification is the simple reStructuredText fixed-width table.
The issue asks that this format accept a *list of header rows to emit/parse*
(the `header_rows` keyword), exactly as the sibling fixed-width formats already
do. Two positions in the format depend on **how many** header rows there are:

- **emit (wrap):** after the fixed-width renderer lays out the table, the output
  is `[sep] + lines + [sep]` where `sep` is the column-rule line (the row of
  `=` characters). The renderer places that rule line *after* all the header
  rows, so it sits at 0-based index `len(header_rows)` in the rendered list. With
  a single header row that index is `1`; with three header rows it is `3`.
- **parse (data start):** the first data line sits two lines below the last
  header row plus the leading rule line, i.e. at index `2 + len(header_rows)`.
  With a single header row that is line `3` (the historical constant); with three
  header rows it is line `5`.

### What the renderer produces (base_commit)

`FixedWidthData.write` (astropy/io/ascii/fixedwidth.py:261-303) appends, in order:
one line per header row (`for vals in hdrs_list`), then — when a position line is
configured — the column-rule line (`self.header.position_char * width`), then the
data lines. So in the list returned by `super().write(lines)`:

```
index 0 .. n-1   the n header rows (name, unit, dtype, …)
index n          the column-rule line  ("===== ========")
index n+1 ..      the formatted data rows
```

Hence `lines[n]` (n = number of header rows) is the rule line that must bracket
the table top and bottom. The historical code used `lines[1]`, correct only for
the single-header-row default (n = 1).

### What the parser needs (base_commit)

`SimpleRSTData.start_line` told the data reader which line begins the data. For a
table laid out as `rule / header rows / rule / data / rule`, with n header rows
the data begins after `rule(1) + n header rows + rule(1)` = `n + 2` lines, i.e.
at index `2 + n`. The historical class attribute fixed this at `3` (n = 1 only).

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `self.header.header_rows` (its length) | `numHeaderRows : Nat` | `len(header_rows)` ↔ `numHeaderRows` |
| the list returned by `super().write(lines)` | `lines : List String` | element-wise string identity, 0-based index ↔ `List` index |
| `lines[idx]` (a rendered text line) | `lines.getD idx ""` | total in-range read; equal to `lines[idx]` whenever `idx < len(lines)` (always true here: the rule line and data follow the header rows) |
| `[lines[idx]] + lines + [lines[idx]]` | `[sep] ++ lines ++ [sep]` | list concatenation |
| `self.data.start_line` (an int line index) | `result : Nat` | identity |

## Callee provenance + flag dependencies

- **No consumed callee axiom; no A-reference.** Both modeled behaviors are pure
  arithmetic/structural functions of `numHeaderRows` (and, for the wrap, the
  rendered `lines`). The output of `super().write` / the fixed-width renderer is
  taken as an *input observation* (`lines`), not re-modeled: the patch does not
  change the renderer, only which index of its output is selected. SPEC_GUIDE §3
  forbids axiomatizing a deeply-modeled changed decision, so the `axioms` region
  is empty and **G-AX skips**.
- The `header_rows` keyword threads through `FixedWidth.__init__`
  (fixedwidth.py:339-357): when `None` it defaults to `["name"]` (length 1).
  This default is why the historical constants `1` and `3` were correct before
  the change and remain correct under the new formulas at `numHeaderRows = 1`.

## G-CONF fuzz seed

Pinned LCG seed: **14182** (see `conformance_check.py` `SEED`). Corpus: random
`numHeaderRows` in `0..8` paired with random rendered-line lists of length
`numHeaderRows + 1 + d` (d ≥ 1 data rows), over ≥1e5 inputs. The R/I shadows of
`implementation_rstWrap` and `implementation_rstDataStart` are diffed against an
in-process replica of the post-patch index selection. Hand-picked edge cases pin
the discriminator: `numHeaderRows ∈ {1,2,3}` (the F2P round-trip uses 3).
