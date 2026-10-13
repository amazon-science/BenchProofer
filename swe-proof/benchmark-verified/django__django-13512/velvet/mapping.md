# mapping.md — django__django-13512

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = b79088306513d5ed76d31ac40ab3c15f858946ea`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each modeled callee.

Repo files under change:
`django/forms/fields.py` and `django/contrib/admin/utils.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `serializeStringValue (text : List Char)` | `JSONField.prepare_value(self, value)` — `django/forms/fields.py:1258` (body line 1261), and the structurally identical JSONField branch of `display_for_field` — `django/contrib/admin/utils.py:400-403` | the modeled changed behaviour: a `str` value rendered to its JSON text form |
| `jsonChar (c : Char)` | the per-code-point rendering performed by the CPython JSON string encoder under `ensure_ascii=False` (`json/encoder.py` `py_encode_basestring`) | pure spec: JSON text of one code point inside a string literal |
| `jsonEscapedSeq (s : List Char)` *(deep model — A-reference)* | the body of `json.dumps(s, ensure_ascii=False)` for a `str` argument `s` (CPython stdlib `json`), validated `jsonEscapedSeq == real json body` by axiom_check.py (G-AX), NOT a consumed axiom | pure spec: escape of a sequence |
| `hexDigit (n : UInt32)` | the lowercase hex nibble emitted in a `\u00XX` control-escape | pure helper (control code points only) |

The pre-patch repo symbols (refinement audit only, not in the consumer spec
view): `json.dumps(value, cls=self.encoder)` at `fields.py:1261` and
`field.get_prep_value(value)` at `utils.py:403` (which itself is
`json.dumps(value, cls=self.encoder)`, `django/db/models/fields/json.py:84`).
Both omit `ensure_ascii=False`, hence default `ensure_ascii=True`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a `str` value being serialized, and the serializer's `str` return | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; `str` concat ↔ `List` `++`; empty `str` ↔ `[]` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; `c.val` ↔ `ord ch`. Exact on every Unicode scalar value (the carrier of `str`). |
| the surrounding `"` … `"` quotes the encoder writes | `'"' :: body ++ ['"']` | the JSON string-literal delimiters; the post-condition pins them explicitly |
| `cls=self.encoder` / `cls=field.encoder` (default `DjangoJSONEncoder`) | omitted | the encoder only adds `default()` handling for non-`str`/non-container leaf objects (datetime, Decimal, UUID, …); on the `str` carrier under model it is the identity. F2P inputs are plain `str` leaves. mapping.md §3.2. |

`str` is a sequence of Unicode scalar values; the modeled operation is
per-code-point, so the carrier is `List Char`. Lean `Char`/`List Char` indexing
is total and sound.

### Scope note — only the `str`-leaf rendering is modeled
The patched call sites serialize whole JSON values (`dict`, `list`, `str`, …).
The ONLY behaviour the patch changes, and the ONLY behaviour the F2P tests
discriminate, is how a **string leaf** is rendered: under the default
`ensure_ascii=True` every code point ≥ U+0080 becomes a `\uXXXX` escape; under
the patch's `ensure_ascii=False` it passes through literally. Container framing
(`{`, `}`, `[`, `]`, `, `, `": "`, key ordering) and the rendering of non-string
leaves are **byte-identical** before and after the patch (`ensure_ascii` only
affects string escaping), so they are refinement-invariant and need not be
modeled. `serializeStringValue` models the string-leaf renderer — the locus of
the change — directly; G-CONF (§4) confirms the full `prepare_value` agrees on
string inputs and that container framing is unchanged.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `jsonEscapedSeq` deep model ↔ `json.dumps(s, ensure_ascii=False)` (A-reference)
**Callee:** CPython `json.dumps(s, ensure_ascii=False)` for a `str` argument.
The changed rendering operation is modeled **deeply** by `jsonEscapedSeq` (with
`jsonChar`) in the `pure` region; there is **no consumed encode axiom**. The
reference behaviour of the string-literal encoder
(`json.encoder.py_encode_basestring`, every supported 3.x incl. the interpreter
in this image):

```python
ESCAPE_DCT = {'\\': '\\\\', '"': '\\"', '\b': '\\b', '\f': '\\f',
              '\n': '\\n', '\r': '\\r', '\t': '\\t'}
for i in range(0x20):
    ESCAPE_DCT.setdefault(chr(i), '\\u{0:04x}'.format(i))

def py_encode_basestring(s):
    def replace(match):
        return ESCAPE_DCT[match.group(0)]
    return '"' + ESCAPE.sub(replace, s) + '"'   # ESCAPE = [\\"]|[\x00-\x1f]
```

Per code point `c` (let `v = ord(c)`):
* `v = 0x22 (")` → `\"`; `v = 0x5c (\)` → `\\`;
* `v ∈ {0x08,0x09,0x0a,0x0c,0x0d}` → `\b \t \n \f \r`;
* `v < 0x20` otherwise → `\u00xx` (lowercase, two leading zeros);
* **`v ≥ 0x20` otherwise → the code point itself** — and crucially this clause
  covers every `v ≥ 0x80`, which is the whole behaviour at issue.

This is exactly what `jsonChar`/`jsonEscapedSeq` encode (`jsonChar`'s `else [c]`
is the literal pass-through; the `< 32` arm builds `\u00` + two hex nibbles via
`hexDigit`). Note U+002F (`/`) is **not** escaped by `json` (unlike some JSON
encoders) — `jsonChar` correctly passes it through.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL
`json.dumps(s, ensure_ascii=False)` on boundary inputs (every special char, the
ASCII/non-ASCII boundary U+007F/U+0080, astral code points, the issue's CJK and
emoji) plus 20 000 randomized fuzz strings, asserting
`'"' + ''.join(jsonChar) + '"' == real json.dumps(s, ensure_ascii=False)`.
Imports only stdlib `json`. Exit 0 iff sound.

### 3.2 The `cls=encoder` argument (A — identity on the `str` carrier)
Both call sites pass `cls=self.encoder` / `cls=field.encoder` (default
`django.core.serializers.json.DjangoJSONEncoder`). A `json.JSONEncoder`
subclass's only behavioural extension is `default(self, o)`, invoked for objects
the base encoder cannot serialize (datetime/date/time, timedelta, Decimal, UUID,
Promise). It never intercepts `str` leaves — those go through
`py_encode_basestring(_ascii)` regardless of `cls`. On the `List Char`/`str`
carrier the encoder choice is therefore the identity, and is omitted from the
model. G-AX exercises the default encoder; G-CONF runs the real
`prepare_value` (which uses the real `self.encoder`) as oracle.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13512`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`jsonChar`/`jsonEscapedSeq` (R/I-tagged ops) to Python and compares against the
patched `JSONField.prepare_value` (the G-RESOLVE oracle) on `str` inputs, and
additionally checks that container framing (dict/list values) is unchanged from
the pre-patch behaviour modulo the string-leaf escaping the shadow models.
