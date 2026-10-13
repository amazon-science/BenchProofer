# mapping.md — astropy__astropy-14182

Binds every `model.py` symbol to its repository counterpart at
`base_commit = a5917978be39d13cd90b517e1de4e7a539ffaa48`, states the type
abstraction, and gives the provenance of each deep layout model (the real
callee it is validated against by G-AX).

Repo file under change: `astropy/io/ascii/rst.py` (the simple-RST reader/writer
`RST` and its data class `SimpleRSTData`).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `rst_frame_block(block, n)` | `RST.write(self, lines)` — `astropy/io/ascii/rst.py:63` (body line 65) | the modeled changed WRITE behaviour: frame the fixed-width block with its rule line at offset `n` |
| `data_row_offset(header_rows)` | `RST.read(self, table)` (new method, gold) / `SimpleRSTData.start_line` (`rst.py:30`, removed) — sets `self.data.start_line = 2 + len(self.header.header_rows)` | the modeled changed READ behaviour: data start offset = `n + 2` |
| `frame_index(n)` *(deep model — A-reference)* | the WRITE index `idx = len(self.header.header_rows)` (`rst.py:65` post-patch) | pure spec: the block offset (`== n`) of the closing rule line |
| `data_start_index(n)` *(deep model — A-reference)* | the READ offset `2 + len(self.header.header_rows)` (`rst.py` new `read`, post-patch) | pure spec: the processed-line offset (`== n + 2`) of the first data row |
| `rule_at(rows, n)` | the content of the closing rule line — a run of the position character `=` (`SimpleRSTHeader.position_char = "="`, `rst.py:20`) at block offset `n` | pure spec: guarded accessor naming `block[n]` inside the postcondition |
| `rule` (parameter of `rst_frame_block`) | the **content** of the rendered closing rule line `lines[len(self.header.header_rows)]` — its actual column-width run of `=` | the opaque per-block value of the closing rule line; `block[n] == rule`, header rows `!= rule`. It is NOT a fixed constant: the framing line must be a copy of this input line, which is what forbids echoing a synthesised constant. |
| `n` (parameter) | `len(self.header.header_rows)` | the header-row count, supplied by the constructor plumbing |

Pre-patch repo facts the change removes (for the refinement audit, not
referenced from the consumer spec view): the class attribute
`SimpleRSTData.start_line = 3` (`rst.py:30`) and the constant index `lines[1]`
in `RST.write` (`rst.py:65`). The constructor change
`RST.__init__(self, header_rows=None)` → `super().__init__(..., header_rows=
header_rows)` (`rst.py:60-61`) is pure plumbing of the header-row count into the
`header_rows`-aware parent `FixedWidth.__init__` (`fixedwidth.py:339-357`); it is
not a separately-modelled function (refinement.md §C).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a rendered/processed table line (`str`) | one `int` row tag carrying the line's *content identity*: the closing rule line of a block carries the opaque per-block value `rule`, the header rows carry values `!= rule` | the index arithmetic depends on *which* line is the closing rule line, and the WRITE framing depends on copying *that exact line's content*. `str` indexing is banned in Nagini, so lines are not modelled char-wise — but the carrier is value-distinguishing (an opaque per-block `rule`, not a globally-fixed sentinel) so that the framing line cannot be discharged by echoing a constant: it must be a copy of the input line `block[n]`. |
| `lines: List[str]` (the block from `super().write`) | `block: List[int]` row tags | `lines[k]` ↔ `block[k]`; `len(lines)` ↔ `len(block)`; list prepend/append ↔ list `+` |
| `self.header.header_rows: list` | `header_rows: List[int]` (one element per header row) / scalar `n` | `len(self.header.header_rows)` ↔ `len(header_rows)` ↔ `n`; only the *count* is observed |
| `self.data.start_line` assignment + `super().read` slice `data_lines[start_line:]` (`core.py:835-839`) | the integer `Result()` of `data_row_offset` | the whole observable effect of the new `read` is the *value* assigned to `start_line`; modelled as the returned offset |

The fixed-width block layout — `n` header rows, then a rule, then data — is a
structural precondition on `block` (`rst_frame_block` Requires); for READ it is
the offset structure encoded by `data_start_index`. Both are validated against
the real layout by G-AX (§3).

## 3. Deep-model provenance (A-reference — checked by G-AX / axiom_check.py)

There are **no consumed `@ContractOnly` axioms**. Both changed operations are
modelled deeply as integer layout formulas and validated against the real
astropy RST reader/writer.

### 3.1 `frame_index(n) == n` ↔ real `RST.write` framing (A-reference)
**Callee chain:** `RST.write` → `FixedWidth`/`FixedWidthData.write`
(`astropy/io/ascii/fixedwidth.py:261-303`). For a table with `n` header rows,
`FixedWidthData.write` appends, in order: the `n` header text rows
(`for col_attr in header_rows: ... lines.append(...)`, lines 273-294), then the
position/rule line if `position_line is not None` (lines 296-298), then the data
rows (lines 300-301). So the block is
`[ header_0 .. header_{n-1}, rule, data... ]` and the rule line sits at offset
`n`. `RST.write` frames it: `lines = [lines[idx]] + lines + [lines[idx]]` with
`idx = len(self.header.header_rows) = n`. Hence the framing line is the rule line
at offset `frame_index(n) == n`. G-AX renders real tables (`n = 1,2,3`) and
asserts: output framed top & bottom by a rule line, that rule equals the inner
block's line at offset `n`, and the `n` lines before it are non-rule.

### 3.2 `data_start_index(n) == n + 2` ↔ real `RST.read` data start (A-reference)
**Callee chain:** `RST.read` sets `self.data.start_line = 2 + len(self.header.
header_rows)` then calls `super().read(table)`; the base reader slices
`data_lines = data_lines[slice(start_line, end_line)]` over the processed
(non-blank) lines (`astropy/io/ascii/core.py:830-841`, `_get_line_index`). A
simple-RST table's processed lines are
`[ rule, header_0 .. header_{n-1}, rule, data... ]`: offset 0 a rule, offsets
`1..n` the header rows, offset `n+1` the closing rule, data from offset `n+2`.
Hence the first data row is at `data_start_index(n) == n + 2`. G-AX renders real
tables (`n = 1,2,3`), asserts the leading rule at offset 0, the closing rule at
offset `n+1`, the data row at offset `n+2` is non-rule, and a full round-trip
(`QTable.read(... header_rows=...)`) recovers the original rows.

**Flag/configuration dependency:** the layout holds for the simple-RST format
with the default `header_rows` plumbing (`None -> ["name"]`, `n >= 1`) and the
single position line (`SimpleRSTHeader.position_line = 0`, one rule per side).
G-AX exercises exactly this configuration (`format="ascii.rst"`, explicit
`header_rows` lists). It imports only the standard library + `astropy` itself
(the package the gold patch edits); nothing else. Exit 0 iff sound.
