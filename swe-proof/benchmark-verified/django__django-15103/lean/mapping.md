# mapping.md — django__django-15103

## Instance
- repo: django/django
- base_commit: dd528cb2cefc0db8b91a7ff0a2bc87305b976597
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
`json_script` (django/utils/html.py:64) required an `element_id` argument and
always wrapped the JSON body in a `<script id="...">` tag. The gold patch makes
`element_id` optional (`element_id=None`) and branches on its truthiness: a
truthy id keeps the `<script id="..." type="application/json">…</script>` frame;
a falsy id (the new default `None`, or an empty string) emits a
`<script type="application/json">…</script>` frame WITHOUT the `id` attribute.

```python
-    return format_html(
-        '<script id="{}" type="application/json">{}</script>',
-        element_id, mark_safe(json_str)
-    )
+    if element_id:
+        template = '<script id="{}" type="application/json">{}</script>'
+        args = (element_id, mark_safe(json_str))
+    else:
+        template = '<script type="application/json">{}</script>'
+        args = (mark_safe(json_str),)
+    return format_html(template, *args)
```

The thin template-filter wrapper `django/template/defaultfilters.py:86` (`def
json_script(value, element_id=None): return _json_script(value, element_id)`) just
gains the same optional default and forwards to the util; it is not separately
modeled (it has no behavior beyond delegation).

The JSON body (`json.dumps(value, cls=DjangoJSONEncoder).translate(
_json_script_escapes)`) and the `format_html` placeholder substitution
(attribute-escaping the substituted id, passing the already-safe body through) are
unchanged in both branches.

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_scriptTag` | `json_script` (django/utils/html.py:64) |
| `problem_spec_scriptTag`   | the post-condition this function must satisfy |
| `jsonBody` (parameter)     | the unchanged body step `json.dumps(value, cls=DjangoJSONEncoder).translate(_json_script_escapes)` (html.py:71), a function of the value |
| `escapeId` (parameter)     | the attribute escaping `format_html` applies to the substituted `element_id` (html.py:93, via `conditional_escape`), a function of the id string |

## Type bijection (Lean ↔ Python) — used by G-CONF
| Lean | Python | notes |
|---|---|---|
| `value : String` | the serialized form of the `value` argument | for G-CONF we fuzz JSON-serializable values; the model takes the value's JSON-encoded body via `jsonBody` |
| `optId : String` | `element_id` (str or None) | empty string `""` ↔ a falsy id (`None` or `""`); non-empty ↔ a truthy id. `optId ≠ ""` ↔ Python `if element_id:` |
| `jsonBody : String → String` | `json.dumps(...).translate(_json_script_escapes)` then `mark_safe` | unchanged body step; modeled abstractly and bound to the REAL pipeline in G-CONF |
| `escapeId : String → String` | the escaping `format_html` applies to the substituted `element_id` | unchanged; modeled abstractly and bound to the REAL `format_html` substitution in G-CONF |
| result `: String` | the returned script-tag string | byte-for-byte `str` |

`String` ↔ Python `str` is the identity bijection (byte-for-byte).

## Callee provenance / flag deps
- No unchanged repo callee is consumed as an axiom. The body-encoding step and the
  attribute escaping are left as universally-quantified parameters `jsonBody` /
  `escapeId` (the spec holds for EVERY encoder/escaper), so the proof consumes no
  property of either and there is no `axiom <callee>_prop`. The modeled change is
  solely WHETHER the `id` attribute is emitted, keyed on id presence.
  `axiom_check.py` is a skip stub.
- Branch dependency: the selected frame depends only on the truthiness of
  `element_id`. G-CONF fuzzes both id-present (truthy) and id-absent (None / "")
  cases plus varied JSON-serializable values.

## G-CONF fuzz seed
- pinned seed: `15103`
- ≥10^5 fuzzed `(value, element_id)` pairs: `element_id` drawn from `None`, `""`,
  and a pool of identifier strings (including ones with HTML-significant
  characters `< > & " '` to exercise the attribute escaping); `value` drawn from a
  pool of JSON-serializable values (dicts, lists, strings with `< > &`, numbers,
  bools, None). The body step is bound to the REAL encode pipeline and the id step
  to the REAL `format_html` substitution.
