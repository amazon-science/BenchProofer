# mapping.md — sphinx-doc__sphinx-8056

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = e188d56ed1248dead58f3f8018c0e9a3f99193f7`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each deep-model reference.

Repo file under change: `sphinx/ext/napoleon/docstring.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `splitSharedNameFields (multiple) (raw)` | `GoogleDocstring._consume_fields(self, parse_type, prefer_type, multiple=False)` — `sphinx/ext/napoleon/docstring.py:269` (post-patch signature; inner loop body lines 273-281) | the modeled changed function: the field collector that gains the multi-name expansion |
| `buildParameterFieldSeq (splitNames) (raw)` | `GoogleDocstring._parse_parameters_section(self, section)` — `sphinx/ext/napoleon/docstring.py:683` | the modeled changed caller: wires `multiple=True` under `napoleon_use_param` |
| `expandOne` / `expandFields` | the per-field expansion the post-patch loop body performs (`docstring.py:275-280`) | pure spec: a raw field's contribution to the output, and the whole concatenation |
| `splitOnComma (s)` *(deep model — A-reference)* | `str.split(",")` (CPython `str`), called at `docstring.py:277` post-patch | pure spec: split a name fragment on the comma separator; validated `splitOnComma == str.split(",")` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `stripWs (s)` *(deep model — A-reference)* | `str.strip()` (CPython `str`), called at `docstring.py:278` post-patch | pure spec: trim surrounding whitespace from a name piece; validated `stripWs == str.strip()` by axiom_check.py (G-AX) |
| `Field` (structure: name/typ/desc) | the `Tuple[str, str, List[str]]` a field is represented as (`docstring.py:269` return type) | carrier for one documented field |
| `raw : List Field` *(FREE INPUT — not modeled)* | the sequence of fields the section scanner yields, i.e. the successive `_consume_field(...)` results gathered by the `while not self._is_section_break()` loop (`docstring.py:272-274`) | the unchanged scanner output; taken as a free input, so the spec makes no claim about the scanner |

The pre-patch repo symbols (refinement audit only, not in the consumer spec
view): `_consume_fields` without a `multiple` parameter, whose loop body kept
every field verbatim (`docstring.py` pre-patch lines 269-277), and
`_parse_parameters_section` calling `_consume_fields()` with no expansion flag.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a field `(_name, _type, _desc)` (`Tuple[str, str, List[str]]`) | `Field` (`{ name, typ, desc }`) | `_name ↔ name`, `_type ↔ typ`, `_desc ↔ desc` componentwise (str ↔ `List Char`, `List[str]` ↔ `List (List Char)`) |
| `str` (a name/type fragment, a desc line) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; empty `str` ↔ `[]` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| `napoleon_use_param` config flag | `splitNames : Bool` | direct |
| the `multiple` parameter | `multiple : Bool` | direct |
| Python truthiness of `_name` (`if multiple and _name` / `elif _name or …`) | `f.name ≠ []` etc. | a `str` is truthy iff non-empty ↔ `List Char ≠ []`; a `List[str]` is truthy iff non-empty ↔ `List (List Char) ≠ []` |
| the unchanged downstream renderer (`_format_docutils_params` / `_format_fields`) | omitted (identity on the field sequence) | both renderers are deterministic functions of the field sequence; the F2P test observes the rendered output, which is fixed once the field sequence is fixed (mapping.md §3.3). Pinning the field sequence pins the rendering. |

Lean `List Char` indexing is total and sound; the carrier is `List Char`
because the operations (split, strip) are per-code-point.

## 3. Callee provenance (kind-A-reference — checked by G-AX / axiom_check.py)

### 3.1 `splitOnComma` deep model ↔ `str.split(",")` (A-reference)
**Callee:** CPython `str.split(sep)` with `sep = ","`. The changed loop splits a
multi-name field with `_name.split(",")` (`docstring.py:277` post-patch). Python
`str.split(",")` returns every comma-delimited piece in order, keeps empty
pieces (between adjacent commas and at the ends), and returns a single-element
list equal to the whole string when there is no comma. `splitOnComma` encodes
exactly this. (`str.split` with an explicit separator does NOT collapse runs or
strip — that is only the no-argument form, which the patch does not use.)

### 3.2 `stripWs` deep model ↔ `str.strip()` (A-reference)
**Callee:** CPython `str.strip()` with no argument. The changed loop trims each
split piece with `name.strip()` (`docstring.py:278` post-patch). The no-argument
`str.strip()` removes leading and trailing whitespace over the FULL Unicode
whitespace set — every code point `c` with `chr(c).isspace()`: the ASCII
whitespace `{' ', '\t', '\n', '\r', '\x0b', '\x0c'}`, the separator controls
U+001C–U+001F, NEL U+0085, NBSP U+00A0, Ogham space U+1680, the Unicode spaces
U+2000–U+200A, the line/paragraph separators U+2028/U+2029, U+202F, U+205F and
the ideographic space U+3000. `stripWs`'s `isWs` enumerates exactly this set,
trimming only the ends and preserving the interior, so the deep model agrees
with the real callee on ALL inputs (e.g. `"x1,\xa0x2"` splits and trims to
`x1`/`x2` on both sides). `axiom_check.py` cross-checks the enumeration against
`chr(c).isspace()` over the whole Unicode range and fuzzes with an alphabet
covering every whitespace code point plus ZWSP (which is NOT whitespace and
must be kept).

### 3.3 The downstream renderer is unchanged (no axiom)
`_format_docutils_params` (`docstring.py:389`) and `_format_fields`
(`docstring.py:435`) are NOT touched by the patch and are deterministic
functions of the field sequence. The behavioural change the F2P test
`test_multiple_parameters` observes (`x1, x2 : array_like` rendering as two
`:param x1:` / `:param x2:` entries under `napoleon_use_param=True`, and as a
single combined `**x1, x2**` entry otherwise) is fully determined by which field
sequence the collector hands the renderer. Hence the spec pins the field
sequence (`expandFields`); the renderer is left as the identity-on-fields
boundary (out of R/I scope, like an unchanged callee).

**Soundness check (G-AX):** `axiom_check.py` runs the real `str.split(",")` and
`str.strip()` on boundary inputs (empty, no-comma, leading/trailing/adjacent
commas, surrounding and interior whitespace, the F2P `"x1, x2"`) plus randomized
fuzz strings, asserting the deep models `splitOnComma` / `stripWs` agree with the
real callees code-point for code-point. Imports only builtins. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`8056`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `expandOne`/`expandFields`/`splitOnComma`/`stripWs` (all R/I or
deep-model-A-reference ops) to Python over the real `Tuple[str, str, List[str]]`
field type, and the oracle is `patch.diff`'s expansion loop body
(`docstring.py:275-281` post-patch) applied to the same raw field list (the
scanner output is the free input `raw`, out of R/I scope). They must agree on
every fuzzed `(multiple, raw)` pair.
