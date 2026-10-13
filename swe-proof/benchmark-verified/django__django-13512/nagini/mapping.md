# mapping.md — django__django-13512

Binds every `model.py` symbol to its repository counterpart at
`base_commit = b79088306513d5ed76d31ac40ab3c15f858946ea`, states the type
abstraction, and gives the provenance of the deep-model reference (the real
serialiser the deep model is validated against by G-AX).

Repo files under change:
- `django/forms/fields.py` (`JSONField.prepare_value`)
- `django/contrib/admin/utils.py` (`display_for_field`, the `JSONField` branch)

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `json_render_text(text)` | the JSON-text rendering of a text scalar produced for display/edit: `JSONField.prepare_value` — `django/forms/fields.py:1258` (body line 1261), and the `JSONField` branch of `display_for_field` — `django/contrib/admin/utils.py:401` (body line 403) | the modelled changed behaviour: serialise a value to its JSON text, keeping non-ASCII literal |
| `json_string_body(s)` *(deep model — A-reference)* | the per-character JSON string body produced by CPython `json.dumps(s, ensure_ascii=False)` (`Lib/json/encoder.py`, `py_encode_basestring` / the C encoder, `ensure_ascii=False` path) | pure spec: per-code-point JSON-text encoding of a sequence; the deep model of the unchanged serialiser, validated `json_string_body == json.dumps(...,ensure_ascii=False)` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `json_char(c)` | the per-character rule of `json.dumps(..., ensure_ascii=False)`: escape only `"` and `\`, keep everything else (incl. all non-ASCII) literal | pure spec: JSON-text encoding for one printable code point |

The pre-patch repo expressions the change replaces (for the refinement audit,
not referenced from the consumer spec view):
- `json.dumps(value, cls=self.encoder)` (`forms/fields.py:1261`) — the default
  `ensure_ascii=True` transliterates every non-ASCII code point into `\uXXXX`.
- `field.get_prep_value(value)` (`admin/utils.py:403`), whose body is
  `json.dumps(value, cls=self.encoder)` (`django/db/models/fields/json.py:84`)
  — likewise `ensure_ascii=True`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the text scalar being serialised; the returned JSON text) | `List[int]` of Unicode code points | `s[k]` ↔ `text[k] == ord(s[k])`; `len(s)` ↔ `len(text)`; `str` concatenation ↔ list `+`; empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materialises the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `json.dumps(value, ensure_ascii=False, cls=self.encoder)` on a text scalar | `'"' + json_string_body(text) + '"'` | for a string value JSON emits the quoted, per-character-encoded body; the optional `cls` encoder only customises serialisation of non-JSON-native objects and is the identity on a plain text scalar |
| the dict/list cases the F2P tests also pass (`{'a': '…'}`, `['…','…']`) | not separately modelled | the discriminating per-character behaviour is identical inside any nested string; the modelled text-scalar case is the load-bearing one the F2P tests pin (`'a'`→`'"a"'`, `'你好 世界'` literal, `'😀🐱'` literal). Structural punctuation (`{`, `}`, `[`, `]`, `:`, `,`, spaces) is ASCII and passes through `json_char` unchanged. |

The modelled domain is restricted by a `Requires` to printable code points
(`>= U+0020`), which is exactly the domain of every tested input (CJK, emoji,
accented Latin, ASCII letters, braces, quotes, commas, spaces). `str` indexing
is banned in Nagini, so the carrier is `List[int]` and the spec is phrased over
`PSeq[int]` via `ToSeq`.

## 3. Deep-model reference provenance (kind A-reference — checked by G-AX)

### 3.1 `json_string_body` deep model ↔ `json.dumps(s, ensure_ascii=False)`

**Callee:** CPython `json.dumps(s, ensure_ascii=False)` for a text scalar `s`.
The changed serialisation operation is modelled **deeply** by the `@Pure` fold
`json_string_body` (with `json_char`) in the `pure` region; there is **no
serialiser axiom** the proof consumes. The deep model is validated equal to the
real callee out-of-band by axiom_check.py (G-AX). The per-character rule of the
`ensure_ascii=False` encoder (`Lib/json/encoder.py`,
`ESCAPE = re.compile(r'[\x00-\x1f\\"]')`, `py_encode_basestring`):

```python
ESCAPE_DCT = {'\\': '\\\\', '"': '\\"', '\b': '\\b', '\f': '\\f',
              '\n': '\\n', '\r': '\\r', '\t': '\\t',
              ...control chars \x00-\x1f -> '\\u00XX'...}
def py_encode_basestring(s):
    def replace(match): return ESCAPE_DCT[match.group(0)]
    return '"' + ESCAPE.sub(replace, s) + '"'
```

`ESCAPE` matches ONLY `"`, `\`, and the control code points `\x00`–`\x1f`;
**no** code point `>= 0x20` (including every non-ASCII code point) is escaped
under `ensure_ascii=False` — each is emitted literally. On the modelled domain
(`>= U+0020`) the only escaped code points are `"` → `\"` and `\` → `\\`, which
is exactly what `json_char` encodes; every other code point (incl. CJK, emoji,
accented Latin) maps to itself. This is the single behavioural change the F2P
tests observe: with the pre-patch default `ensure_ascii=True`
(`py_encode_basestring_ascii`), every code point `>= 0x7f` is replaced by a
`\uXXXX` escape; the fix passes `ensure_ascii=False` so non-ASCII text is kept
literal. Docs: https://docs.python.org/3/library/json.html#json.dumps
("If ensure_ascii is false … the output … may contain non-ASCII characters").

**Flag dependency:** the deep model is sound only for `ensure_ascii=False`
(the gold patch's explicit argument). axiom_check.py fuzzes exactly that
configuration. The `cls`/`encoder` argument does not affect string-scalar
serialisation (only object hooks for non-native types) and is the identity on
the tested text scalars.

**Soundness check (G-AX):** `axiom_check.py` runs the real
`json.dumps(s, ensure_ascii=False)` on the F2P discriminator inputs (asserted
loud, not skipped), an index-level per-code-point sweep over the entire
printable BMP `U+0020`–`U+FFFF` plus astral samples (asserting `json_char(c)`
equals the real serialiser's per-character body — at the index level, no double
mask — and that every `c >= 128` is kept literal on BOTH sides), 15 boundary
strings, and 40 000 randomized fuzz strings over the modelled domain. Exit 0
iff every observation matches. It imports only the standard-library `json`
module — the very module the gold patch calls.
