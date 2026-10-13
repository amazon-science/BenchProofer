# refinement.md — django__django-15103

Maps every operation in `implementation_scriptTag` to its `patch.diff`
counterpart in `json_script` (django/utils/html.py:64). Tags: **R**
type-refinement, **A-consumed** proof uses a callee axiom, **A-reference** op left
as the real repo callee in G-CONF (not axiomatized), **I** identical concrete op.

## Patch (post-patch `json_script`)
```python
def json_script(value, element_id=None):
    from django.core.serializers.json import DjangoJSONEncoder
    json_str = json.dumps(value, cls=DjangoJSONEncoder).translate(_json_script_escapes)
    if element_id:
        template = '<script id="{}" type="application/json">{}</script>'
        args = (element_id, mark_safe(json_str))
    else:
        template = '<script type="application/json">{}</script>'
        args = (mark_safe(json_str),)
    return format_html(template, *args)
```

The fix makes `element_id` optional (default `None`) and branches on its
truthiness: a truthy id emits the `<script id="...">` frame (id substituted into
the `{}` placeholder, hence attribute-escaped by `format_html`), a falsy id (the
new default, or empty string) emits a `<script>` frame WITHOUT the `id`
attribute. The JSON body computation (`json.dumps(...).translate(...)` then
`mark_safe`) and the `format_html` substitution are unchanged in both branches.

## Modeling decision
The observable behavior of `json_script` is the returned HTML script-tag string.
That string is:

    "<script id=\"" + escape(element_id) + "\" type=\"application/json\">" + body + "</script>"   (id present)
    "<script type=\"application/json\">" + body + "</script>"                                       (id absent)

where `body` is the safe JSON body (independent of the id) and `escape` is the
attribute escaping that `format_html` applies to substituted args. The fix
changes WHETHER the `id` attribute (and its substituted, escaped id value) is
emitted, keyed on whether an id is supplied. So the model:

- takes `optId : String`, with the empty string modeling the absent/falsy id
  (Python `None` and `""` are both falsy — the `if element_id:` test) and a
  non-empty string modeling a supplied id;
- branches exactly as the patch does on `optId ≠ ""`;
- applies an arbitrary `jsonBody : String → String` (the unchanged encoder +
  entity-translation step) to the value, and an arbitrary `escapeId : String →
  String` (the unchanged attribute escaping done by `format_html` on the
  substituted id) to the id;
- frames each branch with the corresponding unchanged literal tag text.

Universally quantifying `jsonBody` and `escapeId` makes the spec hold for EVERY
encoder/escaper, so the only thing it can pin is which frame is selected and how
the abstract pieces are assembled — which is exactly the fix.

## Operation correspondence
| # | Lean op (`implementation_scriptTag`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let jsonStr := jsonBody value` | `json_str = json.dumps(value, cls=DjangoJSONEncoder).translate(_json_script_escapes)` | A-reference | unchanged encoder + entity-translation step; left abstract (universally quantified) and bound to the REAL encode pipeline in G-CONF. No property consumed ⇒ NOT an `axiom`. |
| 2 | `if optId ≠ "" then …` | `if element_id:` | R | Python truthiness of `element_id` (where `None`/`""` are falsy) ↔ `optId ≠ ""`. This is the fixed branch token. |
| 3 | `"<script id=\"" ++ escapeId optId ++ "\" type=\"application/json\">" ++ jsonStr ++ "</script>"` | `format_html('<script id="{}" type="application/json">{}</script>', element_id, mark_safe(json_str))` | R / A-reference | the literal tag text is `I`; `escapeId optId` is the A-reference (the attribute escaping `format_html` applies to the substituted id); `jsonStr` is op #1. |
| 4 | `"<script type=\"application/json\">" ++ jsonStr ++ "</script>"` | `format_html('<script type="application/json">{}</script>', mark_safe(json_str))` | R / A-reference | id-absent frame; only the body is substituted (already-safe ⇒ unchanged). |
| 5 | `return result` | `return format_html(template, *args)` | I | return the assembled script-tag string. |

## R/I legs ⇒ G-CONF
The branch selection (op #2, R) and the literal tag framing (ops #3/#4 literal
text, I) are the R/I content. Ops #1 and the `escapeId` piece of #3 are
A-references: G-CONF leaves them as the REAL repo behavior (it does NOT substitute
an axiom model), which is how the R/I branch-selection + framing legs are
isolated and tested. `conf_skip = false`: the impl region has genuine R/I content
(the id-presence branch is the fixed behavior), so `conformance_check.py`
differential-tests the shadow (branch selection + literal framing, with the real
encode pipeline as the body step and `format_html`'s escaping as the id step)
against the patched `json_script`'s returned string over ≥10^5 fuzzed inputs.

## No A-consumed row
The proof consumes no property of `jsonBody` or `escapeId` (both universally
quantified), so `meta.json axioms = []`. Ops #1/#3-escape are recorded as
A-references solely to document the G-CONF binding to the real callees; there is
no `opaque`/`axiom` declaration in `Solution.lean` and `axiom_check.py` is a skip
stub.

## F2P alignment
`test_json_script_without_id` calls `json_script({'key': 'value'})` (no id) and
expects `<script type="application/json">{"key": "value"}</script>` — NO `id`
attribute. `test_without_id` (template filter) renders `{{ value|json_script }}`
with `value={}` and expects `<script type="application/json">{}</script>`.
Pre-patch, `element_id` was mandatory and the `<script id="...">` frame was always
emitted, so an id-less call either errored (missing arg) or produced an `id`
attribute — the discriminating clause `problem_spec_scriptTag` pins (empty id ⇒
no `id` attribute) and the prepatch impl (always emits the `id` frame) cannot
satisfy. `patch.diff` (gold verbatim) makes the harness resolve.
