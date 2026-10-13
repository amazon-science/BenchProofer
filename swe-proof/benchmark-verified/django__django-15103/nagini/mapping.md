# mapping.md — django__django-15103

Binds every `model.py` symbol to its repository counterpart at
`base_commit = dd528cb2cefc0db8b91a7ff0a2bc87305b976597`, states the type
abstraction, and gives the provenance of the wrapper callees the refinement
relies on (no callee is *consumed* as an axiom; the one structural assumption is
checked executably by `axiom_check.py` / G-AX).

Repo files under change: `django/utils/html.py`, `django/template/defaultfilters.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `build_json_script(payload, element_id)` | `json_script(value, element_id)` — `django/utils/html.py:64` (body 70-75) | the modeled changed function (the conditional script-tag wrapper) |
| `tag_open_with_id()` | the literal `'<script id="'` of the id-bearing template (`html.py:73` pre / `html.py` post-patch with-id branch) | pure spec: id-bearing opening-tag prefix |
| `attr_close_and_type()` | the literal `'" type="application/json">'` joining the id value to the media type | pure spec: attribute-close + media-type segment |
| `tag_open_no_id()` | the literal `'<script type="application/json">'` of the id-free template (introduced by the patch's `else` branch) | pure spec: id-free opening tag (no id attribute) |
| `tag_close()` | the literal `'</script>'` | pure spec: closing tag |
| `prefix_with_id(ident)` | the id-bearing opening tag instantiated with `element_id` | pure spec: `<script id="` + ident + `" type="application/json">` |

The thin template-filter wrapper `django.template.defaultfilters.json_script`
(`defaultfilters.py:86`, body `return _json_script(value, element_id)`) is a
pass-through to `django.utils.html.json_script`; the patch only adds the
`element_id=None` default to both signatures. Its behaviour is fully captured by
the modeled `build_json_script` (the template filter adds nothing observable
beyond forwarding the optional argument). It is therefore not modeled separately;
see refinement.md §B.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `value` (arbitrary JSON-serializable) → `json.dumps(value, cls=DjangoJSONEncoder).translate(_json_script_escapes)` → a `str` | the model's `payload: List[int]` of Unicode code points | the model takes the *already-serialized, JSON-script-escaped* payload as input; `payload[k] == ord(json_str[k])`. The serialization/escape step is UNCHANGED by the patch and is not part of the modeled operation. |
| `element_id` (`str` or `None` / falsy) | `element_id: Optional[List[int]]` | `None` ↔ absent identifier; a non-empty list ↔ a present identifier (`element_id[k] == ord(s[k])`); an empty list ↔ an empty (falsy) token, treated as absent — matching Python truthiness `if element_id:` |
| the returned `SafeString` from `format_html(...)` | `List[int]` of the rendered characters | `mark_safe`/`SafeString` only set the safe flag; they do not change character content (the F2P tests compare rendered characters). Modeled as the identity on code points. |
| `format_html(template, *args)` positional interpolation | literal sequence concatenation in the model | for the tested inputs, `format_html` substitutes each `{}` with the conditional-escape of the arg, joins the constant template literals, and `mark_safe`s the result. `mark_safe(json_str)` is already safe (identity); `element_id` contains no HTML-special characters in the tested usage (identity). Hence the rendered output is exactly the literal concatenation the model assembles. Validated executably by axiom_check.py (G-AX). |
| keyword default `element_id=None` | explicit `Optional[List[int]]` parameter; `None` handled as absent | the patch's sole signature change is making the argument optional with default `None`. |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

**Total correctness:** `build_json_script` carries `Requires(MustTerminate(2))`
— the real `json_script` is a bounded, straight-line computation (one
`format_html` call over constant templates), so the modeled operation must
terminate and return. This closes the vacuous-satisfaction hole (an impl that
loops forever satisfies the value postconditions only vacuously and would hang
every caller); Nagini's obligation system rejects any loop that does not
consume the obligation with a strictly decreasing measure.

## 3. Callee provenance (no consumed axioms)

This bundle has **no `@ContractOnly` axiom** and **no deep-model A-reference to a
stdlib callee**. The changed operation — selecting the id-bearing vs. id-free
template and assembling the wrapped element — is modeled DEEPLY and concretely
(constant code-point literals + two verified append loops). The only callees the
real code invokes (`format_html`, `mark_safe`, `json.dumps`, `str.translate`) are
UNCHANGED by the patch; they produce the `payload` input and wrap the assembled
markup, and are treated under the R-refinement above (structure-preserving
wrappers).

**Soundness check (G-AX), `axiom_check.py`:** runs the REAL post-patch
`django.utils.html.json_script` on boundary inputs (absent id `None`, empty id
`''`, present ids; payloads exercising the JSON-script escapes `> < &` and
ordinary/whitespace/quote content) plus 4000 randomized fuzz cases, and asserts
the model's structural assembly `build_json_script(payload, element_id)` equals
the real output character-for-character (with `payload` set to the real
serialized+escaped JSON string). This validates the refinement's wrapper
assumptions (positional interpolation, `mark_safe` identity, HTML-special-free
ids). Exit 0 iff sound; observed 4119/4119 matches. It imports Django (the
package under test, present in the eval container) and the standard library only.
