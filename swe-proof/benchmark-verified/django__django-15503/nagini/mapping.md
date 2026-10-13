# mapping.md — django__django-15503

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 859a87d873ce7152af73ab851653b4e1c3ffea4c`, states the type
abstraction, and gives the provenance of the deep-model reference (callee
source + the exact behaviour the model encodes).

Repo file under change: `django/db/models/fields/json.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `compile_final_key_segment(key)` | the post-patch `HasKeyLookup.compile_json_path_final_key(self, key_transform)` (the new method introduced by the fix in `django/db/models/fields/json.py`, class at line 172) — together with its use inside `HasKeyLookup.as_sql` (line 175) which routes the FINAL key transform through it (`*rhs_key_transforms, final_key = ...; rhs_json_path += self.compile_json_path_final_key(final_key)`) | the modeled changed function: compile the final key of a key-membership test into a JSON-path step |
| `member_access_segment(key)` *(deep model — A-reference)* | `".%s" % json.dumps(key_transform)` — the body of `compile_json_path_final_key` | pure spec: the object-member path step `."key"` |
| `json_string_literal(s)` *(deep model — A-reference)* | `json.dumps(key_transform)` — CPython stdlib `json.dumps` on a `str`, default flags (`ensure_ascii=True`) | pure spec: the JSON string literal of a key on the modelled domain (verbatim key wrapped in double quotes); validated `json_string_literal == json.dumps` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `all_digits(s)` | the `int(key_transform)` / `except ValueError` discriminator in `compile_json_path` (lines 132-138) | pure spec: the predicate that selects the buggy array-index branch (a key whose characters are all decimal digits parses as `int`) |
| `is_digit(c)` | `str.isdigit`-style single-character test | pure spec helper |
| `in_domain(s)` | (modelling restriction, no repo symbol) | the key character domain on which `json.dumps(key) == '"'+key+'"'` |

The pre-patch repo construct the change replaces (for the refinement audit, not
referenced from the consumer spec view): in `HasKeyLookup.as_sql` the final key
went through the array-aware `compile_json_path(rhs_key_transforms,
include_root=False)` (line 129, the `[%s] % int(key)` branch at lines 137-138),
so a numeric key became an array index. The fix adds
`compile_json_path_final_key` (forces the member form for the final key) and a
subclass `HasKeyOrArrayIndex` that overrides it back to the array-aware form for
the two Oracle/SQLite `isnull` call sites that genuinely address array indices.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` key (`key_transform`, a single key name) | `List[int]` of Unicode code points | `s[k]` ↔ `key[k] == ord(s[k])`; `len(s)` ↔ `len(key)`; empty `str` ↔ `[]` |
| `str` path step (the return of `compile_json_path_final_key`) | `List[int]` of code points | `str` concatenation ↔ list `+`; `'.'` ↔ `46`, `'"'` ↔ `34`, `'['` ↔ `91`, `']'` ↔ `93` |
| a `str` value inside a specification | `PSeq[int]` via `ToSeq(list)` | `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `json.dumps(key)` (`ensure_ascii=True` default) | `json_string_literal(key) = '"' + key + '"'` on the domain | identity on the modelled domain (see §3); outside it `json.dumps` escapes, so the domain is restricted accordingly |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout and the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `member_access_segment` / `json_string_literal` deep model ↔ the fixed callee (A-reference)

**Callee:** the new method
```python
class HasKeyLookup(PostgresOperatorLookup):
    def compile_json_path_final_key(self, key_transform):
        # Compile the final key without interpreting ints as array elements.
        return ".%s" % json.dumps(key_transform)
```
The changed serialization step is modeled **deeply** by the `@Pure` functions
`json_string_literal` and `member_access_segment` in the `pure` region; there is
**no consumed `@ContractOnly` axiom**. The deep model is validated equal to the
real callee out-of-band by axiom_check.py (G-AX).

`json.dumps` of a `str` (CPython stdlib, default flags) escapes only the double
quote, the backslash, and control characters, and — with the default
`ensure_ascii=True` — renders any non-ASCII code point as `\uXXXX`. The modelled
key domain `in_domain` is exactly **printable ASCII 32..126 excluding `"`(34)
and `\`(92)**, on which none of those escapes fire, so

  `json.dumps(key) == '"' + key + '"'`  (i.e. `json_string_literal(key)`),

and therefore `compile_json_path_final_key(key) == '.' + '"' + key + '"' ==
member_access_segment(key)`. axiom_check.py asserts this equality on the F2P
keys + boundary cases + 70 000 fuzz keys (incl. an all-digit stress set),
0 mismatches. The behaviour is independent of any flag other than CPython's
default `json.dumps` configuration. Docs:
https://docs.python.org/3/library/json.html#json.dumps .

The discriminating content of the change — a numeric key like `"1111"` / `"000"`
becomes the object-member step `."1111"` / `."000"` instead of the array-element
step `[1111]` / `[0]` — lives in `member_access_segment` always beginning with
`.`(46)`"`(34) and reproducing the key digits verbatim. The pre-patch path
compiler `compile_json_path([key], include_root=False)` produced `[<int(key)>]`
for an all-digit key (array form, leading zeros dropped); `model_prepatch.py`
reproduces that array-element branch and **fails** the postcondition
`ToSeq(Result()) == member_access_segment(ToSeq(key))` — exactly the spec
sensing the change (G-DIFF). axiom_check.py also confirms this discriminator
against the real `compile_json_path` (`"000" -> "[0]"`, `"1111" -> "[1111]"`).

### 3.2 Unchanged sites NOT modeled (refinement-audit note)

The gold patch also (a) re-points two Oracle/SQLite `KeyTransformIsNull` call
sites (lines 389-393, 400-408) and one Oracle `KeyTransform...` site
(lines 465-476) from `HasKey` to the new subclass `HasKeyOrArrayIndex`, and
(b) defines `HasKeyOrArrayIndex` to override `compile_json_path_final_key` back
to the array-aware `compile_json_path([key_transform], include_root=False)`.
These are class-wiring / vendor-routing changes whose *behaviour* on the final
key is exactly one of the two segment forms already modeled (member-access vs
array-element). They introduce no new computation beyond what
`compile_final_key_segment` (member form) and the prepatch (array form) already
exercise, so they need no separate modeled function; the single modeled
behaviour (member-access for an OBJECT key) is the F2P discriminator and is the
root fix. Provenance recorded here for the G-EQ audit; G-RESOLVE runs the gold
patch verbatim, exercising all sites.
