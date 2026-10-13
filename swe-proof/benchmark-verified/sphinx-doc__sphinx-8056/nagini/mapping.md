# mapping.md — sphinx-doc__sphinx-8056

Binds every `model.py` symbol to its repository counterpart at
`base_commit = e188d56ed1248dead58f3f8018c0e9a3f99193f7`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `sphinx/ext/napoleon/docstring.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `emitted_names(name, multiple, type_nonempty, desc_nonempty)` | the per-field body of `GoogleDocstring._consume_fields` — `sphinx/ext/napoleon/docstring.py:269` (loop body 273-276) — as reached from `_parse_parameters_section` (`docstring.py:683`) | the modeled changed behaviour: how ONE consumed field is turned into the emitted field entries, gated by the per-comma "multiple" expansion |
| `multiple` parameter | the new `multiple: bool = False` parameter of `_consume_fields` (added by the patch; passed `multiple=True` only from the `napoleon_use_param` branch of `_parse_parameters_section`) | the boolean that selects the per-comma expansion |
| `name` parameter (`List[int]`) | the local `_name: str` produced by `_consume_field` for one field (`docstring.py:274`) | the field's name run (a comma-separated list of parameter names) |
| `type_nonempty`, `desc_nonempty` | the truthiness of the local `_type` / `_desc` from `_consume_field` (`docstring.py:274`); they gate the legacy `elif _name or _type or _desc` keep-condition | booleans summarizing whether the field's type / description are non-empty |
| `split_on_comma(s)` *(axiom — A-consumed)* | `str.split(',')` — CPython built-in `str.split` (called in the patched loop: `for name in _name.split(",")`) | unchanged stdlib callee: split the name run on literal commas |
| `num_commas(s)` *(axiom — A-consumed)* | `str.count(',')` arithmetic identity `len(s.split(',')) == s.count(',') + 1` (CPython `str.split`/`str.count`) | unchanged stdlib fact: the number of comma-separated runs |
| `trim(s)` *(axiom — A-consumed)* | `str.strip()` — CPython built-in (called in the patched loop: `name.strip()`) | unchanged stdlib callee: drop surrounding whitespace from one name |

The repo behaviour the change introduces (for the refinement audit, NOT named in
the consumer spec view): `_consume_fields` gains `multiple: bool = False` and,
when `multiple and _name`, replaces the single `fields.append((_name, _type,
_desc))` with `for name in _name.split(','): fields.append((name.strip(),
_type, _desc))`; `_parse_parameters_section` calls `_consume_fields(multiple=
True)` in its `napoleon_use_param` branch (and `_consume_fields()` otherwise).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `_name: str` (the field name run) | `name: List[int]` of Unicode code points | `name[k] == ord(_name[k])`; `len(name) == len(_name)`; an empty `str` ↔ `[]`; "name is non-empty/truthy" ↔ `len(name) > 0` |
| a `str` value inside the specification | `PSeq[int]` via `ToSeq` | `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `_name.split(',')` — a `List[str]` | `PSeq[PSeq[int]]` (`split_on_comma`) | the k-th run ↔ `split_on_comma(ToSeq(name))[k]`; list length ↔ `len(...)` |
| the emitted `fields` list of `(name, type, desc)` tuples | `PSeq[PSeq[int]]` of the emitted NAME runs only | each tuple shares `_type`/`_desc` verbatim across an expanded field, so the emitted-name sequence carries the entire observable change; the type/desc are modeled only by their non-emptiness (`type_nonempty`/`desc_nonempty`), which is all the keep-guard `_name or _type or _desc` reads |
| `_name.strip()` (whitespace trim) | `trim(...)` (axiom) | identity on code points outside the leading/trailing whitespace runs |
| boolean `multiple` / truthiness of `_type`,`_desc` | `bool` params | identical |

`str` indexing/iteration is banned in Nagini, so name runs are carried as
`List[int]` / `PSeq[int]`; the emitted-name sequence is a pure `PSeq[PSeq[int]]`
(pure sequences carry no heap permission, so the spec quantifies over entries
directly).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

All three axioms stand in for UNCHANGED Python built-ins the patched loop calls;
none is the function under change, and each is the WEAKEST contract the proof
needs.

### 3.1 `num_commas` ↔ `str.count(',')`
**Callee fact:** CPython `str.split(sep)` returns `str.count(sep) + 1` runs for a
single-character `sep` (a non-empty separator always produces at least one run,
including for the empty string: `''.split(',') == ['']`). The axiom claims only
`num_commas(s) >= 0` and `num_commas('') == 0` — the minimum the count clause
needs. Docs: https://docs.python.org/3/library/stdtypes.html#str.split.

### 3.2 `split_on_comma` ↔ `str.split(',')`
**Callee:** CPython `str.split(',')`. The axiom claims only
`len(split_on_comma(s)) == num_commas(s) + 1` (the run count). The CONTENT of
each run is NOT pinned by the axiom; the model's content clause
`Result()[k] == trim(split_on_comma(name)[k])` is discharged BY CONSTRUCTION
(the impl literally returns `trim(parts[k])` for `parts = split_on_comma(name)`),
so the proof relies only on the count axiom plus the definition of `trim`/
`split_on_comma`. G-AX validates the run count against the real `str.split(',')`
and validates the COMPOSED observable (see §3.4). Docs:
https://docs.python.org/3/library/stdtypes.html#str.split.

### 3.3 `trim` ↔ `str.strip()`
**Callee:** CPython `str.strip()` with no argument — removes leading and trailing
whitespace, preserves interior content, idempotent. The axiom states no Ensures
beyond its documented behaviour (it is used purely as a stand-in: the spec pins
`Result()[k] == trim(...)`, and `trim` IS `str.strip`). G-AX asserts the real
`str.strip()` meets the documented behaviour (interior substring, non-whitespace
endpoints, idempotent). Docs:
https://docs.python.org/3/library/stdtypes.html#str.strip.

### 3.4 Composed-observable soundness (G-AX)
`axiom_check.py` runs the REAL built-ins on boundary inputs (empty, lone/leading/
trailing/doubled commas, the F2P `"x1, x2"`, whitespace-padded names,
`"*args, **kwargs"`, `"x1, x2, optional"`) plus 30 000 randomized fuzz strings
over an alphabet of letters, digits, spaces, tabs, newlines, commas, `*` and `\`.
For each it asserts (a) each axiom's claim holds on the real callee and (b) the
COMPOSED model `emitted_names` (computed with the real `split`/`strip`) equals
the gold patch's per-field `_consume_fields` behaviour
(`[n.strip() for n in name.split(',')]` when `multiple and name`, else the single
verbatim entry guarded by `name or type or desc`), across every `(multiple,
type_nonempty, desc_nonempty)` flag combination. The F2P discriminator
`"x1, x2" → ["x1", "x2"]` (and its non-expansion form `→ ["x1, x2"]`) is checked
explicitly. Imports only Python built-ins (`str.split`/`str.strip`/`str.count`)
— the exact operations the gold patch calls. Exit 0 iff sound.
