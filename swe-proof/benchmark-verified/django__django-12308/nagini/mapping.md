# mapping.md — django__django-12308

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 2e0f04507b17362239ba49830d26fec504d46978`, states the type
abstraction, and gives the provenance of each deep-model reference (callee
source + the exact behaviour the model encodes).

Repo file under change: `django/contrib/admin/utils.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `display_structured_value(value, empty, content, present, encodable)` | `display_for_field(value, field, empty_value_display)` — `django/contrib/admin/utils.py:380` (the added JSONField branch, body lines 401–405 post-patch) | the modeled changed function, restricted to the structured-data (JSONField) dispatch |
| `interchange_form(value)` (via `node_body` / `ser_list`) *(deep model — A-reference)* | `field.get_prep_value(value)` == `json.dumps(value)` (default `encoder=None`) — `JSONField.get_prep_value` at `django/db/models/fields/json.py:83`, which calls CPython `json.dumps` | pure spec: the canonical interchange encoding, modelled DEEPLY and STRUCTURALLY as the full recursive serialisation of the value tree (string tokens / keys in the U+0022 `"` delimiter; arrays bracketed; objects braced with `: ` member separators); validated `== json.dumps` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `fallback_form(content)` *(deep model — A-reference)* | the fallback callee `display_for_value(value, empty_value_display)` — `django/contrib/admin/utils.py:406` (post-patch), defined at `django/contrib/admin/utils.py:404` (base) — **the whole function, not just its general arm**: it dispatches on the value's own shape, so a `list`/`tuple` takes the join arm `', '.join(str(v) for v in value)` (`utils.py:420`) and everything else the general arm `str(value)` (`utils.py:422`) | pure spec: the fallback display text passed through UNCHANGED (`fallback_form` = identity on `content`, which CARRIES `display_for_value(value, empty_value_display)`'s own output — **not** `str(value)`, since the two differ on every list/tuple-rooted value) — the renderer adds no delimiters of its own; validated against the real `display_for_value` by axiom_check.py (G-AX), NOT consumed as an axiom |

The pre-patch repo state (for the refinement audit, not referenced from the
consumer spec view): `display_for_field` had **no** structured-data branch, so a
present structured value fell straight through to
`display_for_value(value, empty_value_display)` (the general arm `str(value)`,
or the list/tuple arm `', '.join(str(v) for v in value)`) — the single-quote
printout. The gold patch inserts the branch (`django/contrib/admin/utils.py:401`):

```python
elif isinstance(field, models.JSONField) and value:
    try:
        return field.get_prep_value(value)
    except TypeError:
        return display_for_value(value, empty_value_display)
```

`models.JSONField` resolves to `django.db.models.fields.json.JSONField`
(exported from `django/db/models/__init__.py:21,47`), present at this
`base_commit` (PR #12990 already landed).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the rendered result, the `empty_value_display`, a string-token's contents, an object key, the printout token) | `List[int]` of Unicode code points | `s[k]` ↔ `content[k] == ord(s[k])`; `len(s)` ↔ `len(content)`; `str` concatenation ↔ list `+`; empty `str` ↔ `[]` |
| a `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list; `PSeq` `+`/`take`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| the structured JSON `value` (str / list / dict, recursively) | a recursive `JNode` tree in sibling/inner linked form: `kind` 0 = STRING (contents in `text`), 1 = ARRAY (elements = sibling list at `inner`), 2 = OBJECT (members = sibling list at `inner`), 3 = MEMBER (key in `text`, value = single node at `inner`, no siblings) | `"…"` ↔ STRING; `[e1, e2, …]` ↔ ARRAY whose `inner` is the element sibling list; `{k1: v1, …}` ↔ OBJECT whose `inner` is the MEMBER sibling list; each MEMBER carries its key in `text` and its value as the single node `inner`. `interchange_form` over this tree reproduces `json.dumps(value)` code point for code point for EVERY token: what sits between the two U+0022 delimiters is `esc_seq(text)`, the token's own code points each replaced by that code point's form in the interchange alphabet. |
| the `elif value is None` arm at `django/contrib/admin/utils.py:389` — the **only** arm that returns the placeholder | the boolean `present` | `present == (value is not None)`. The `and value` truthiness guard is deliberately **NOT** folded in here: when it fails on a non-None falsy value, control does **not** reach the placeholder arm (that arm is already behind it) but falls THROUGH to the final `else` at `utils.py:406`. So a falsy stored value (`[]`, `''`, `{}`, `0`, `False`) is `present == True` and renders via the fallback, never as the placeholder |
| the `and value` guard at `utils.py:401` **and** whether `field.get_prep_value(value)` returns vs. raises `TypeError` | the boolean `encodable` | `encodable == (bool(value) and json.dumps(value) returns)`. Both conditions must hold for the encoder's output to be what is displayed: a falsy value never enters the branch, and a truthy one whose contents `json.dumps` cannot express raises `TypeError` and is caught. The two guards therefore yield **three** outcomes — placeholder (`value is None`) / interchange (`present and encodable`) / fallback (`present and not encodable`) — matching the model's three arms |
| `display_for_value(value, empty_value_display)`'s own return value on the fall-through arm (`utils.py:406`) — the join arm `', '.join(str(v) for v in value)` for a list/tuple, `str(value)` otherwise | the `List[int]` `content` (consulted only on the `present and not encodable` branch) | `content[k] == ord(display_for_value(value, empty_value_display)[k])`; `fallback_form(content) == content` (identity): the renderer returns that text unchanged. **`content` is that callee's output, not `str(value)`** — for `[{('x','y'):'z'}]` the real text is `{('x', 'y'): 'z'}` (join arm) whereas `str(value)` would be `[{('x', 'y'): 'z'}]`. Where the text shows string tokens they carry the single quote `'` |

`str` indexing/iteration is banned in Nagini, so every string carrier is
`List[int]`; the specification is phrased over `PSeq[int]` via `ToSeq`. The JSON
value is a tree, so it is modelled as a recursive `JNode` (the §3-mandated deep
modelling of the rich object), NOT a single representative token — the F2P
discriminator is STRUCTURAL (`["a", "b"]`, `{"a": {"b": "c"}}`), which a single
token cannot express.

## 3. Callee provenance (deep-model references — checked by G-AX / axiom_check.py)

There are **no consumed `@ContractOnly` axioms**. The two callees the new branch
invokes are modelled deeply and validated against the real callees out-of-band.

### 3.1 `interchange_form` deep model ↔ `JSONField.get_prep_value` / `json.dumps` (A-reference)
**Callee:** `django.db.models.fields.json.JSONField.get_prep_value(value)`
(`django/db/models/fields/json.py:83`):

```python
def get_prep_value(self, value):
    if value is None:
        return value
    return json.dumps(value, cls=self.encoder)
```

With the default `encoder=None`, this is exactly CPython `json.dumps(value)`.
`json.dumps` is the canonical JSON serializer: it serialises the value tree
STRUCTURALLY — every string token and every dict key delimited by the **double
quote U+0022** (`"`), arrays between `[`…`]` comma-and-space separated, objects
between `{`…`}` with `"key": value` members. `model.py`'s `interchange_form`
(via `node_body` / `ser_list`) is exactly this recursive structural
serialisation: `{'a': {'b': 'c'}}` → `{"a": {"b": "c"}}`, `['a', 'b']` →
`["a", "b"]`, `'a'` → `"a"`. Docs: https://docs.python.org/3/library/json.html#json.dumps.

The behavioural change the F2P test observes is precisely this structural
double-quote serialisation (vs. the single-quote host-language printout).
**G-AX (`axiom_check.py`) reproduces the EXACT structural serialiser
(`interchange_form_model` = `node_body`/`ser_list`) and asserts
`interchange_form(value) == json.dumps(value)` — the SAME property `model.py`
proves (`ToSeq(Result()) == interchange_form(value)`) — on the SAME input set:
the three encodable F2P values, 47 boundary structured values (every escape
class as a token AND as an object key), 20 000 randomized nested
dict/list/string values whose tokens are drawn from the full code point range,
and a sweep of ALL 1 114 112 code points as a single-token value (plus a sampled
1 141 of them as object keys inside a nested value).** Measured: 1 135 253
checks, zero divergences. It does NOT route the F2P values
through a parallel reproduction function; the asserted property is identical to
the proved one.

**Token form (no domain restriction).** The deep model does not splice a
token's code points between the delimiters; it models `json.dumps`' own
character transform explicitly, as `esc_seq` / `esc_char` / `hex_form` /
`hex_digit` in the pure region (`model.py`), mirroring
`json.encoder.py_encode_basestring_ascii` / the C `c_encode_basestring_ascii`
that `json.dumps` selects under `ensure_ascii=True`:

| code point | interchange form | model |
|---|---|---|
| U+0022 `"` | `\"` | `esc_char(34) == PSeq(92, 34)` |
| U+005C `\` | `\\` | `esc_char(92) == PSeq(92, 92)` |
| U+0008, U+0009, U+000A, U+000C, U+000D | `\b`, `\t`, `\n`, `\f`, `\r` | the five two-code-point arms |
| U+0020..U+007E (other) | the code point itself | `esc_char(c) == PSeq(c)` |
| any other <= U+FFFF (incl. U+007F, the C1 band, lone surrogates) | `\uXXXX`, four LOWERCASE hex digits, most significant first | `hex_form(c)` |
| > U+FFFF | the two `\uXXXX` forms of its UTF-16 surrogate halves | `hex_form(55296 + (c - 65536) // 1024) + hex_form(56320 + (c - 65536) % 1024)` |

So there is no restriction of the token domain: every code point is in domain,
as a string token and as an object key.

**Flag dependency:** sound under the default `encoder=None` (Django's
`models.JSONField()` passes no encoder), i.e. plain `json.dumps(value)` with
`cls=None`, hence `ensure_ascii=True` (ASCII-only output, which is what the
`\uXXXX` forms above encode), `separators=None` (`', '` between siblings and
`': '` after a key), `sort_keys=False` (members in insertion order) and
`indent=None` (no line breaks). Recorded because a non-default `encoder` (e.g.
one passing `ensure_ascii=False` or `sort_keys=True`) would render differently;
`JSONField()` as `display_for_field`'s field argument fixes the default.

### 3.2 `fallback_form` deep model ↔ `display_for_value` (A-reference)
**Callee:** the fall-through arm `display_for_value(value, empty_value_display)`
(`django/contrib/admin/utils.py:406` post-patch; the function is defined at
`utils.py:404` in the base tree). `display_for_value` is **not** `str` for every
input — it dispatches on the value's own shape:

```python
elif isinstance(value, (list, tuple)):
    return ', '.join(str(v) for v in value)   # utils.py:420 — the JOIN arm
else:
    return str(value)                          # utils.py:422 — the general arm
```

so it is modelled as an **opaque callee whose output is carried**, not as `str`.
`model.py` puts that callee's OWN return value in `content` and `fallback_form`
is the **identity** on it (`fallback_form(content) == content`): the renderer
adds **no** delimiters of its own. Modelling it as `str(value)` would be
unfaithful on every list/tuple-rooted value — `[{('x','y'):'z'}]` really renders
as `{('x', 'y'): 'z'}` (join arm), whereas `str(value)` gives
`[{('x', 'y'): 'z'}]`. On the one non-encodable F2P value, the tuple-keyed dict
`{('a', 'b'): 'c'}`, the dispatch reaches the general arm and the text
coincides with `str(value)`; the single-quote U+0027 delimiters visible there
come from `repr` on the string tokens INSIDE the text, not from any outer wrap.
Docs: https://docs.python.org/3/reference/datamodel.html#object.__repr__.

G-AX confirms, on the tuple-keyed F2P value, that `json.dumps` raises
`TypeError` (the fallback fires), that the real `display_for_value(value, …)`
output equals the test's expected display and passes through `fallback_form`
unchanged, and the single-quote-vs-double-quote delimiter contrast holds between
that text's internal tokens (`repr('a')` = `'a'`) and `json.dumps`'s (`"a"`). It
additionally pins the **join arm** against `str` on list/tuple-rooted
non-encodable values and the three-outcome dispatch on the falsy stored values
(`[]`, `''`, `{}`, `0`, `False`), which take the fallback and not the
placeholder.

**Soundness check (G-AX):** `axiom_check.py` reproduces the structural
serialiser and runs the real `json.dumps` on the three encodable F2P values, 15
boundary + 20 000 randomized nested structured values, asserting
`interchange_form == json.dumps` (the A-reference 1 structural equality, the
very property `model.py` proves). For A-reference 2 it imports the **real**
`django.contrib.admin.utils.display_for_value` and asserts
`fallback_form(display_for_value(value, empty)) == display_for_value(value, empty)`
(the identity pass-through) on the tuple-key F2P value, on list/tuple-rooted
non-encodables where the **join arm** makes the real text differ from
`str(value)`, and on the falsy stored values; plus the `TypeError` raise and the
delimiter contrast (`"` vs `'`). Beyond the standard-library `json` (the module
`get_prep_value` calls) it imports only that one repo function, which is the
callee under reference.
Confirmed RC=0 in the pinned eval container (`sweb.eval.x86_64.django_1776_django-12308`).
Exit 0 iff sound.

## 4. G-CONF (conformance_check.py)

`conformance_check.py` embeds the impl region of `model.py` verbatim
(contract calls stripped) as the SHADOW and diffs it against the REAL patched
`display_for_field` (driven with a default `models.JSONField()`) in-container
over >= 1e5 Requires-satisfying inputs: boundary structured values + absent
probes + randomized nested dict/list/string fuzz whose string tokens and keys
are drawn from the FULL code point range (the delimiter U+0022, the escape
character U+005C, the control positions, the non-ASCII BMP band, the surrogate
range and the astral planes -- §3.1 imposes no token restriction), mixing
encodable / non-encodable / absent cases. The shadow copies the new
`append_escaped` / `append_esc_char` impl regions and the `esc_seq` / `esc_char`
/ `hex_form` / `hex_digit` pure region verbatim alongside the rest.
**Pinned fuzz seed: 12308.**
