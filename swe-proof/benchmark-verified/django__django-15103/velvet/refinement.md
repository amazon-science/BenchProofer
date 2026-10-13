# refinement.md — django__django-15103

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `jsonScriptTag` `do` block and the pure `wrapNoId`/`wrapWithId` markup
helpers) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — none here), or **I** (identical
concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The markup site — `json_script()` (`django/utils/html.py:64`)

Gold hunk (`django/utils/html.py`):
```
- return format_html(
-     '<script id="{}" type="application/json">{}</script>',
-     element_id, mark_safe(json_str)
- )
+ if element_id:
+     template = '<script id="{}" type="application/json">{}</script>'
+     args = (element_id, mark_safe(json_str))
+ else:
+     template = '<script type="application/json">{}</script>'
+     args = (mark_safe(json_str),)
+ return format_html(template, *args)
```
plus the signature default `def json_script(value, element_id=None)` (and the
identical default added to the `defaultfilters.py:86` wrapper).

| # | Solution.lean impl op (`jsonScriptTag`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `content : List Char` | `mark_safe(json_str)` where `json_str = json.dumps(value, cls=DjangoJSONEncoder).translate(_json_script_escapes)` | R | the JSON-encoding + escape is UNCHANGED by the patch; its result is the already-safe payload text, abstracted to a `List Char` (mapping.md §2). G-CONF feeds the real encoder's output. |
| A2 | parameter `identifier : List Char` | `element_id`, as escaped by `conditional_escape` inside `format_html` | R | the escaping is UNCHANGED; abstracted to a `List Char`. The truthiness guard `if element_id:` ⟺ `identifier ≠ []` (mapping.md §2 truthiness bridge). |
| A3 | `if identifier = []` selects the bare-element branch | `else:` branch: `template = '<script type="application/json">{}</script>'`, `args = (mark_safe(json_str),)` | I | the branch condition is the CHANGED logic, modeled directly. Falsy id ⟺ `identifier = []`. |
| A4 | `wrapNoId content = openPlain ++ content ++ scriptClose` = `<script type="application/json">` ++ content ++ `</script>` | `format_html('<script type="application/json">{}</script>', mark_safe(json_str))` | I | template interpolation of the single payload arg ⟺ concatenation of the fixed fragments around `content` (mapping.md §2). |
| A5 | `else` selects the id-bearing branch; `wrapWithId identifier content = openWithId identifier ++ content ++ scriptClose` = `<script id="` ++ identifier ++ `" type="application/json">` ++ content ++ `</script>` | `if element_id:` branch: `template = '<script id="{}" type="application/json">{}</script>'`, `args = (element_id, mark_safe(json_str))`, `format_html(template, *args)` | I | template interpolation of `(element_id, payload)` ⟺ concatenation of the fragments with `identifier` spliced into the `id="…"` attribute (mapping.md §2). |
| A6 | `out` returned (`List Char`) | `return mark_safe(format_html(...))` | R | `mark_safe`/`SafeString` is identity on character content (mapping.md §2); the F2P tests compare rendered characters (`assertEqual`/`assertHTMLEqual`). |

Discriminating content of the change — *when the identifier is absent, the
result has NO `id` attribute* — lives in the clause
`identifier = [] → out = wrapNoId content` (no `id="…"` substring). The pre-patch
unconditionally emitted `<script id="…" …>`; `Solution_prepatch.lean` reproduces
that (`return wrapWithId identifier content` always) and **fails** that exact
clause (G-DIFF): with `identifier = []` it would emit `<script id="" …>`, which
is `wrapWithId [] content ≠ wrapNoId content`.

## B. No second independently-observable behavior

The `defaultfilters.py` hunk is purely the wrapper signature default
(`element_id=None`) forwarding to `django.utils.html.json_script`; it adds no
observable computation of its own (mapping.md §1). Both F2P tests bottom out in
the `html.py` markup decision modeled here:
- `test_json_script_without_id` calls `json_script({'key':'value'})` (no id) →
  expects `<script type="application/json">…</script>` (the `wrapNoId` clause);
- `test_without_id` renders the template filter `{{ value|json_script }}` (no id
  arg) → same bare-element expectation, reached via the wrapper's new default.
A single failing prepatch on the empty-identifier clause covers both.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the choice of
whether to emit the `id` attribute — is modeled **directly** as the branch on
`identifier = []`, not hidden behind an axiom. There are **no axioms** and **no
deep-model references** in this bundle: the two callees touched (JSON encoder,
identifier escaper) are unchanged and abstracted as R inputs (mapping.md §3), so
G-AX is `skip`.

## D. verify(Solution) ⇒ resolved

`jsonScriptTag` verifies only if (i) with an empty identifier the output is
exactly `wrapNoId content` — the bare `<script type="application/json">` element
with NO `id` attribute (A3/A4), and (ii) with a non-empty identifier the output
is `wrapWithId identifier content` — the element carrying `id="identifier"`
(A5). By R (`str ↔ List Char`, the truthiness bridge, `mark_safe`/`format_html`
template interpolation = fragment concatenation) the verified wrapper equals the
patched `django.utils.html.json_script` on the tested inputs; by G-CONF the R/I
transliteration of `wrapNoId`/`wrapWithId` agrees with `patch.diff`'s behaviour
over both branches and many payloads. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE). The only trust point is refinement fidelity (this
doc, G-EQ + G-CONF); there are no axioms to trust (no G-AX).
