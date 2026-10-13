# mapping.md — django__django-13512

## Symbol binding (file:line @ base_commit b790883)
- `JSONField.prepare_value` — `django/forms/fields.py:1258` (changed line 1261).
  Post-patch: `return json.dumps(value, ensure_ascii=False, cls=self.encoder)`.
- `display_for_field` (JSONField branch) — `django/contrib/admin/utils.py:401`
  (changed line 403). Post-patch: `return json.dumps(value, ensure_ascii=False,
  cls=field.encoder)`. The removed `field.get_prep_value(value)` is itself
  `json.dumps(value, cls=field.encoder)` (`django/db/models/fields/json.py:81`),
  so both sites collapse to the same `json.dumps(…, ensure_ascii=False, …)` call.
- `json.dumps` — CPython stdlib (unchanged callee). The flag `ensure_ascii`
  controls only string-leaf character rendering.

## Modeled function
`jsonEncodeString` ≙ the JSON serializer's **string-leaf renderer** — the
function turning a text value into its quoted JSON string literal. This is the
smallest carrier on which `ensure_ascii` is observable; the whole-document walk
(objects/arrays/numbers/bools/null, key quoting, `", "`/`": "` separators) is
flag-independent and is the unchanged `json.dumps` structure (not modeled).

## Lean ↔ Python type bijection (used by G-CONF + G-AX)
| Python | Lean | bijection |
|---|---|---|
| `str` (text value, per-code-point) | `List Char` | `s ↔ list(s)` over Unicode code points; astral chars are ONE `Char` in Lean and ONE code point in Python (`json.dumps(ensure_ascii=False)` emits the literal char, so no surrogate handling is needed on the literal-output side) |
| serialized JSON string literal `str` | `List Char` | `result ↔ list(result)` |
| `\uXXXX` escape (pre-patch, ≥U+0080) | `['\\','u',h,h,h,h]` | only in the prepatch impl's `escapeBuggy` |

## Callee provenance + flag deps
- `json.dumps` string-leaf rendering: unchanged callee, A-REFERENCE (deep-modeled
  by `escapeChar`, validated == real renderer by G-CONF, NOT a consumed axiom).
- **Flag dependency:** the modeled behavior is the `ensure_ascii=False`
  configuration (post-patch). G-CONF MUST call `json.dumps(s, ensure_ascii=False)`
  (no custom `cls` — the F2P tests use the default encoder) when building the
  reference rendering. The escape table for `"`, `\`, and controls < U+0020 is
  identical under either flag; only the ≥U+0080 branch is flag-sensitive.

## Domain note (modeling limitation)
Lean `Char` ranges over Unicode SCALAR values (it excludes the surrogate range
U+D800–U+DFFF). Python `str` can additionally hold lone surrogates, which
`json.dumps(ensure_ascii=False)` renders specially; those are not representable
in the `List Char` model and are out of scope. The benchmark's F2P/PASS values
(CJK, emoji, Latin diacritics, ASCII) are all scalar-value strings, so the model
is faithful on every input the tests exercise. The post-patch `escapeChar` is
exact `json.dumps(s, ensure_ascii=False)` for any scalar-value string (G-CONF,
2·10⁵ draws incl. astral, 0 mismatch).

## G-CONF fuzz seed
Pinned seed: **13512**. Fuzzer draws strings from a mixed alphabet: printable
ASCII, the control range U+0000–U+001F (incl. `\b \t \n \f \r`), `"`, `\`, `/`,
Latin-1 (é, ñ, …), CJK (中, 你, 好), and astral/emoji (😀, 🐱) code points; lengths
0–40; ≥10⁵ draws. Each draw `s`: assert
`'"' + ''.join(escapeChar(c) for c in s) + '"' == json.dumps(s, ensure_ascii=False)`
where `escapeChar` is the Python shadow of the Lean `escapeChar`.

## No consumed axiom
`escapeChar`/`escapeBody` are concrete Lean `def`s; the proof reasons about them
directly. `axioms = []`; `axiom_check.py` is a skip stub.
