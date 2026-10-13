# mapping.md — django__django-13670

Binds every `model.py` symbol to its repository counterpart at
`base_commit = c448e614c60cc97c6194c62052363f4f501e0953`, states the type
abstraction, and records callee provenance.

Repo file under change: `django/utils/dateformat.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `abbreviated_year(year)` | `DateFormat.y(self)` — `django/utils/dateformat.py:327` (body line 329) | the modeled changed method (two-digit abbreviated-year renderer) |
| `tens_digit(v)` / `units_digit(v)` | the per-digit emission of the `'%02d'` formatting of `year % 100` | pure spec: the two decimal-digit code points |

The repo method reads `self.data.year` (an `int`, the calendar year of the
`date`/`datetime` carried by the `DateFormat`); the modeled `year` parameter is
that value. The method returns a `str`; the model returns the `List[int]` of
its code points.

The pre-change repo expression the change replaces (for the refinement audit,
not referenced from the consumer spec view): the body `return str(self.data.year)[2:]`
(`dateformat.py:329`), a slice of the year's decimal string. The post-change
body is `return '%02d' % (self.data.year % 100)` (`dateformat.py:330`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.data.year` (`int` calendar year, 1..9999) | `year: int`, `Requires(1 <= year <= 9999)` | identity on the integer value (datetime's documented year range, `datetime.MINYEAR..MAXYEAR`) |
| the returned `str` (always two characters) | `List[int]` of Unicode code points | `s[k]` ↔ `Result()[k] == ord(s[k])`; `len(s)` ↔ `len(Result())`; `ord('0') == 48`, `ord('9') == 57` |
| `'%02d' % (year % 100)` (Python `%`-formatting: fixed width 2, zero-padded, the value `year % 100` ∈ 0..99) | the two code points `tens_digit(year % 100)`, `units_digit(year % 100)` | `'%02d' % v` for `0 <= v <= 99` is exactly the tens digit `v // 10` then the units digit `v % 10`, each as a decimal-digit character; zero-padding supplies the leading `'0'` for `v < 10` (validated exhaustively by axiom_check.py) |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`.

## 3. Callee provenance

**None.** No library callee is invoked by the changed expression. The renderer
is pure integer arithmetic (`%`, `//`) and decimal-digit emission, which is
modelled **deeply** in `model.py` (`tens_digit`/`units_digit` over the integer
year, with the postcondition pinning the result element-wise to the input
year's arithmetic). There is therefore **no `@ContractOnly` axiom** (no
A-consumed callee) and the only soundness obligation is deep-model fidelity:

- **A-reference (deep-model fidelity):** the pinned mapping
  `result == [ord('0') + (year%100)//10, ord('0') + (year%100)%10]` equals the
  real post-change renderer expression `'%02d' % (year % 100)`. `axiom_check.py`
  (G-AX) validates this **over the entire admitted year domain 1..9999**
  (not a fuzz sample — the domain is small enough to check exhaustively),
  asserting equality, width 2, and digit-range, and additionally confirms the
  pre-change expression `str(year)[2:]` differs on the sub-100 / sub-1000
  regime so the spec genuinely senses the change. Stdlib-only; exit 0 iff sound.

No flag dependency (no floats, no library defaults). `float_encoding` is null.
