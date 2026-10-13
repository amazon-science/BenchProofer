# mapping.md — django__django-15103

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = dd528cb2cefc0db8b91a7ff0a2bc87305b976597`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of every abstracted input.

Repo files under change:
- `django/utils/html.py` — the markup-building site (the discriminating change).
- `django/template/defaultfilters.py` — a thin re-export wrapper.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `jsonScriptTag (identifier content : List Char)` | `json_script(value, element_id)` — `django/utils/html.py:64` (body lines 70-77) | the modeled changed function: builds the `<script …>` wrapper, now with an optional id |
| `content` *(abstracted input — R)* | `json_str = json.dumps(value, cls=DjangoJSONEncoder).translate(_json_script_escapes)`, then `mark_safe(json_str)` (`html.py:71`) | the already-encoded, already-safe payload text. UNCHANGED by the patch; modeled as a plain `List Char` input |
| `identifier` *(abstracted input — R)* | `conditional_escape(element_id)` as performed inside `format_html` (`html.py:74,99`) | the already-escaped identifier text. The escaping step is UNCHANGED; modeled as a plain `List Char`. Empty `[]` ⟺ the `element_id` being falsy (`None`/`""`) |
| `openPlain`, `openWithId`, `scriptClose`, `wrapNoId`, `wrapWithId` *(pure)* | the two format-string literals `'<script type="application/json">{}</script>'` and `'<script id="{}" type="application/json">{}</script>'` (`html.py` post-patch lines 73,75) | pure spec: the fixed markup fragments and their concatenation |

The second changed file, `django/template/defaultfilters.py:86`, only changes the
template-filter wrapper signature `def json_script(value, element_id)` →
`def json_script(value, element_id=None)` and forwards verbatim to
`django.utils.html.json_script`; it adds **no behavior of its own** (it is a
`@register.filter` re-export, `defaultfilters.py:16` import alias `_json_script`).
The observable behavior change lives entirely in `django/utils/html.py`, so a
single modeled function suffices; the wrapper is recorded under
`additional_change_sites` (R-only signature default) in meta.json.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the JSON-encoded payload `mark_safe(json_str)` (`str`) | `content : List Char` | `s` (Python str) ↔ `s` as `List Char`; `str` concat ↔ `List` `++`; empty `str` ↔ `[]`. The payload is already produced and safe; modeled as an opaque char sequence the wrapper splices in unchanged. |
| the escaped identifier `conditional_escape(element_id)` (`str`) | `identifier : List Char` | same `str ↔ List Char` bijection. **Truthiness bridge:** the Python guard `if element_id:` is true iff `element_id` is a non-empty, non-`None` value; for the string identifiers this filter passes, an empty/`None` `element_id` ⟺ the Lean `identifier = []` case, and any non-empty identifier ⟺ `identifier ≠ []`. G-CONF feeds `element_id = None`, `''`, and non-empty strings to exercise both branches. |
| the resulting markup `mark_safe(format_html(...))` (`SafeString`) | `out : List Char` | `mark_safe`/`SafeString` only set the safe flag; identity on character content. The two format strings interpolate `{}`/`id="{}"`; under the bijection the concatenations `openPlain ++ content ++ scriptClose` and `openWithId identifier ++ content ++ scriptClose` are exactly the two rendered strings. |

`format_html(template, *args)` runs each interpolated arg through
`conditional_escape` and then `template.format(...)`. Both args here
(`element_id`, `mark_safe(json_str)`) are abstracted as their post-escape values
(`identifier`, `content`), so the only thing `jsonScriptTag` models is the
TEMPLATE SELECTION — which template literal is used and how the args are spliced
into it — which is precisely the changed code.

## 3. Abstracted inputs (no axioms — no G-AX)

There are **no axiomatized callees** in this bundle and **no deep-model
references**. The two callees the wrapper invokes — the JSON encoder
(`json.dumps(...).translate(...)`) and the identifier escaper
(`conditional_escape`) — are **UNCHANGED** by the patch and identical pre- and
post-fix. Their results are therefore taken as plain `List Char` inputs
(`content`, `identifier`), R-tagged in refinement.md. No `axiom_check.py` is
shipped; meta.json sets `G-AX = skip` (mirrors django__django-11951).

The single changed behavior — *omit the `id` attribute when the identifier is
absent* — is modeled **directly** as the branch on `identifier = []`, not behind
any axiom. There is no kind-3 (inexpressible-changed-op) step.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15103`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `wrapNoId`/`wrapWithId` (the R/I-tagged markup ops) to Python and
compares against the real patched `django.utils.html.json_script` over the two
branches (falsy `element_id`: `None`, `''`; truthy: random identifiers) and a
range of payload values. Both inputs feed through the real (unchanged) encoder /
escaper inside the oracle; the shadow splices the same post-escape values into
the two template literals.
