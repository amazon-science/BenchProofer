# refinement.md — astropy__astropy-13033

Operation-by-operation correspondence between `implementation_checkRequiredColumns`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH
`BaseTimeSeries._check_required_columns`). Tags: **R** type refinement,
**A-consumed** proof uses an axiom, **A-reference** deep model validated == real
callee, **I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `if !requiredColumnsEnabled then return .ok requiredColumnsRelax` | `if not self._required_columns_enabled: return` | R |
| 2 | `match requiredColumns with \| none => return .ok requiredColumnsRelax` | `if self._required_columns is not None:` (else fall through to no-op) | R |
| 3 | `let required := if requiredColumnsRelax then reqCols.take colnames.length else reqCols` | `required_columns = self._required_columns[:len(self.colnames)] if relax else self._required_columns` | R |
| 4 | `let plural := if required.length > 1 then "s" else ""` | `plural = 's' if len(required_columns) > 1 else ''` | I |
| 5 | `if !requiredColumnsRelax && colnames.length == 0 then return .error (… expected '… headD …' … but time series has no columns)` | `if not relax and len(self.colnames) == 0: raise ValueError("… expected '{}' … but time series has no columns".format(cls, required_columns[0], plural))` | I |
| 6 | `else if colnames.take required.length != required then return .error (… expected renderNames required … but found renderNames (colnames.take required.length))` | `elif self.colnames[:len(required_columns)] != required_columns: raise ValueError("… expected {} … but found {}".format(cls, as_scalar_or_list_str(required_columns), plural, as_scalar_or_list_str(self.colnames[:len(required_columns)])))` | R |
| 6a | `renderNames xs = match xs with \| [x] => pyStrRepr x \| _ => pyListRepr xs` | `def as_scalar_or_list_str(obj): if not hasattr(obj,'__len__'): f"'{obj}'"; elif len(obj)==1: f"'{obj[0]}'"; else: str(obj)` | R |
| 6b | `pyListRepr xs = "[" ++ ", ".intercalate (xs.map pyReprStr) ++ "]"` with `pyReprStr` **opaque** | `str(list_of_str)` = `'[' + ', '.join(repr(x) for x in xs) + ']'`; each element via the UNCHANGED builtin `repr` | **A-reference** (`pyReprStr` ↔ `str.__repr__`; validated by G-AX) |
| 7 | `let newRelax := if requiredColumnsRelax && reqCols == colnames.take reqCols.length then false else requiredColumnsRelax; return .ok newRelax` | `if relax and self._required_columns == self.colnames[:len(self._required_columns)]: self._required_columns_relax = False` | R |

Notes:

- **Every step is R or I except 6b, an A-reference.** The changed op (the
  mismatch-message construction and the adaptive single-vs-list rendering) is
  modeled DEEPLY as pure string functions (`renderNames`, `pyStrRepr`,
  `pyListRepr`); SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed op.
  ONE building block inside that rendering is an UNCHANGED platform builtin the
  patch never touches: the per-element rendering `str(list)` applies (Python
  `repr` of a `str`, with its quote choice — double quotes when the value embeds
  a single quote — and its backslash/control-character escaping tables).
  Approximating those tables concretely in Lean would be unfaithful on names
  containing quotes/backslashes/control characters, so that leaf is declared
  `opaque pyReprStr` (axioms region) and its binding to the real builtin is
  validated executably by **G-AX** (`axiom_check.py`: composition equals real
  `str(list)` byte-for-byte over adversarial + fuzzed names; `repr` round-trips
  each name). No `axiom` is consumed by the proof.
- **R vs I.** Steps 4, 5 are tagged **I**: they are unchanged by the patch and
  their Lean form is a literal transliteration (`plural`, the no-columns
  message). Steps 1–3, 6, 7 are **R**: the Python objects (`self`, the table,
  `raise`/return) are refined to the `Except String Bool` carrier and
  `List String`/`Option` inputs per the mapping.md bijection. The slice `xs[:n]`
  ↔ `xs.take n` and `xs[0]` ↔ `xs.headD ""` bijections hold because the modeled
  inputs are list-shaped (mapping.md).
- **The fix itself** is step 6 (+ helper 6a): the found side moves from
  `self.colnames[0]` (single head) to `as_scalar_or_list_str(self.colnames[:len(required_columns)])`
  (the full present leading slice), and both sides are rendered with
  `as_scalar_or_list_str`. The pre-patch impl (`Solution_prepatch.lean`) keeps
  the single-head rendering `expected '<required.headD>' … but found
  '<colnames.headD>'`, which is the actual misleading message; that impl's
  carried `rfl` proof fails to typecheck against the spec (G-DIFF).
- The `as_scalar_or_list_str` **scalar** branch (`not hasattr(obj,'__len__')`)
  is unreachable for the two real call sites (both pass lists), so it is not
  modeled; the two list branches (`len==1` → quoted scalar; else → list repr)
  are. (mapping.md.)
- **G-CONF** mechanically refutes the R/I legs: a faithful in-process replica of
  the post-patch `_check_required_columns` is diffed (message strings compared
  byte-for-byte) against the impl shadow over ≥1e5 fuzzed inputs, with a name
  pool covering quotes/backslashes/control chars/non-ASCII; the shadow
  interprets the opaque `pyReprStr` as the real `repr`. The single A leg (6b)
  is validated by **G-AX**.
