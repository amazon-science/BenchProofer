# refinement.md — astropy__astropy-14182

The operation-by-operation correspondence between `model.py`'s implementations
(`rst_frame_block`, `data_row_offset`, and the deep layout-index models
`frame_index` / `data_start_index`) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A-consumed** (the proof uses an axiom's
`Ensures`), **A-reference** (a deep model validated == the real callee by
axiom_check.py / G-AX, NOT consumed), or **I** (identical concrete operation).

The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

The fix touches one repo class, `RST` (`astropy/io/ascii/rst.py`), at three
hunks that realize **two independently-observable behaviours** — a WRITE
behaviour and a READ behaviour — plus a constructor plumbing change that merely
makes `header_rows` reach the parent. Each behaviour is modelled as its own
contracted function; each has its own failing `model_prepatch`.

## A. WRITE — `RST.write` (`astropy/io/ascii/rst.py:63`)

Gold hunk:
```
     def write(self, lines):
         lines = super().write(lines)
-        lines = [lines[1]] + lines + [lines[1]]
+        idx = len(self.header.header_rows)
+        lines = [lines[idx]] + lines + [lines[idx]]
         return lines
```

`super().write(lines)` (the fixed-width data writer, `fixedwidth.py:261`) emits,
for a table with `n` header rows, the block
`[ header_0, ..., header_{n-1}, rule, data... ]` — the `n` header text rows,
then the position (rule) line, then the data rows. The simple-RST writer frames
this block by repeating the rule line above and below. The pre-patch code used
the constant index `1` (correct only when `n == 1`); the fix computes the index
from the header-row count.

| # | model.py impl op (`rst_frame_block`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `block: List[int]` row tags; the closing rule line carries the opaque per-block value `rule` (`block[n] == rule`), header rows carry other values | `lines = super().write(lines)`, a `List[str]` | R | each rendered line ↔ one row tag; the only structural fact the index computation uses is *which line is the closing rule line and that its content is a specific block line* (mapping.md §2). `rule` ↔ the actual content of the rendered closing rule line `lines[n]` — an opaque per-table value (real column widths, e.g. `"======= ======== ===="`), NOT a fixed constant. |
| A2 | `idx = frame_index(n)` with `frame_index(n) == n` | `idx = len(self.header.header_rows)` | I + R | identical integer computation: the index is the header-row count `n`. `n` ↔ `len(self.header.header_rows)` (R; mapping.md §2). The pre-patch constant `1` is the bug. |
| A3 | `sep = block[idx]` | `lines[idx]` | R | index a sequence at `idx`; `List[int]` ↔ `List[str]`. The Requires pins `block[n] == rule` (the block's opaque closing-rule value) and the earlier header rows `!= rule`, so `block[idx]` IS that closing rule line. **Soundness of A3 now rests on identity, not just rule-ness:** because `rule` is an opaque per-block value (not a fixed constant), the postcondition `Result()[0] == block[n]` can be discharged ONLY by copying the actual input line `block[idx]`; an implementation cannot synthesise a constant equal to `rule`. (Previous revision pinned the rule line to the fixed sentinel `-1`, which let an impl echo that constant without reading the input — the directive-8 echo-the-marker hole the G-EQ adversary found; closed by grounding `rule` in the input carrier.) |
| A4 | `result = [sep] + block + [sep]` | `lines = [lines[idx]] + lines + [lines[idx]]` | I + R | identical list construction (prepend + append the selected line); element type refined `str` ↔ row tag. |

Discriminating content: the framing line is the block's closing rule line at
offset `n` (its actual content), not the line at the constant offset `1` and not
a synthesisable constant. `model_prepatch.py` reproduces the bug (`idx = 1`) and
**fails** the postcondition
`ToSeq(Result()) == PSeq(rule_at(block,n)) + block + PSeq(rule_at(block,n))`
for `n != 1` (where `block[1]` is a header row, whose value `!= rule`). The
echo-a-constant impl (`sep = -1`) likewise fails (it cannot prove `-1 == rule`
for the opaque `rule`). That is exactly the spec sensing the WRITE change and
rejecting the marker-echo cheat (G-DIFF / G-EQ).

## B. READ — `RST.read` (new method) + removed `SimpleRSTData.start_line`

Gold hunks:
```
 class SimpleRSTData(FixedWidthData):
-    start_line = 3
     end_line = -1
     splitter_class = FixedWidthTwoLineDataSplitter
...
+    def read(self, table):
+        self.data.start_line = 2 + len(self.header.header_rows)
+        return super().read(table)
```

A simple-RST table parses (after `process_lines` drops blank lines) as
`[ rule, header_0, ..., header_{n-1}, rule, data... ]`: one leading rule, `n`
header rows, one closing rule, then data. The first data value row is therefore
at processed-line offset `n + 2`. The pre-patch hardcoded `start_line = 3`
(correct only when `n == 1`); the fix computes it from the header-row count.

| # | model.py impl op (`data_row_offset`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `n = len(header_rows)` | `len(self.header.header_rows)` | R | `header_rows: List[int]` (one element per header row) ↔ the real `self.header.header_rows` list; `len` ↔ `len` (mapping.md §2). |
| B2 | `return 2 + n` with `data_start_index(n) == n + 2` | `self.data.start_line = 2 + len(self.header.header_rows)` | I + R | identical affine integer computation `2 + n`. Assigning `self.data.start_line` then `super().read(table)` slices `data_lines[start_line:]` (`core.py:835-839`); the *value* set is the whole observable change, modelled as the function's `Result()`. |

Discriminating content: the data start is `n + 2`, not the constant `3`.
`model_prepatch_2.py` reproduces the bug (`return 3`) and **fails** the
postcondition `Result() == data_start_index(len(header_rows)) == n + 2` for
`n != 1`. That is exactly the spec sensing the READ change (G-DIFF).

## C. Constructor plumbing — `RST.__init__` (`astropy/io/ascii/rst.py:60`)

Gold hunk:
```
-    def __init__(self):
-        super().__init__(delimiter_pad=None, bookend=False)
+    def __init__(self, header_rows=None):
+        super().__init__(delimiter_pad=None, bookend=False, header_rows=header_rows)
```

This is pure parameter plumbing: it accepts `header_rows` and forwards it to the
already-`header_rows`-aware `FixedWidth.__init__` (`fixedwidth.py:339`, which
defaults `None -> ["name"]` and sets `self.header.header_rows` /
`self.data.header_rows`). It introduces no new computed behaviour of its own —
it only makes the header-row count `n` (used by A and B) configurable and
reachable, which is why the original `TypeError: unexpected keyword argument
'header_rows'` disappears. It is therefore **not** modelled as a separate
contracted function: `n = len(self.header.header_rows)` is the abstract input to
both `rst_frame_block` and `data_row_offset`. No kind-3 step; nothing
inexpressible.

## D. No kind-3 (unexpressible-changed-op) steps; no consumed axioms

Every step above is R, I, or R+I. Both *changed* operations — the WRITE framing
index and the READ data-start offset — are modelled **deeply** as the layout
arithmetic `frame_index(n) == n` and `data_start_index(n) == n + 2` (the `pure`
region), consumed directly by the two impls. They are **A-reference** deep
models: validated **== the real astropy RST writer/reader** out-of-band by
axiom_check.py (G-AX), which renders tables with `n = 1,2,3` header rows and
asserts the rule-line framing sits at block offset `n` and the data row begins
at processed offset `n + 2`. There is **no consumed `@ContractOnly` axiom**: the
fixed-width parent machinery (`super().write` / `super().read`) is not
axiomatized inside the proof — its only relevant output (the block layout) is
expressed structurally in the Requires of `rst_frame_block` and validated
against reality by G-AX.

## E. verify(model) ⇒ resolved

`rst_frame_block` verifies only if it frames the block with the rule line at
offset `n` (A2–A4), and `data_row_offset` verifies only if it returns
`n + 2` (B1–B2). By R (row-tag/`str` line correspondence, `len(header_rows)` ↔
`len(self.header.header_rows)`, integer identity) the two verified functions are
the gold patch's two computed indices; by G-AX the deep models `frame_index` /
`data_start_index` equal the real astropy RST layout (A-reference). The
constructor plumbing (C) only supplies `n`. Therefore an implementation
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and audited-against-reality layout models — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom
soundness (here, deep-model fidelity, G-AX) and refinement fidelity (this
document, G-EQ).
