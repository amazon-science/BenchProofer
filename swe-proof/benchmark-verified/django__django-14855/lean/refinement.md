# refinement.md — django__django-14855

Maps every operation in `implementation_getAdminUrl` to its `patch.diff`
counterpart in `AdminReadonlyField.get_admin_url`
(`django/contrib/admin/helpers.py:205-215`). Tags: **R** type-refinement,
**A-consumed** proof uses a callee axiom, **A-reference** op left as the real
repo callee in G-CONF (not axiomatized), **I** identical concrete op.

## Patch (post-patch `get_admin_url`)
```python
def get_admin_url(self, remote_field, remote_obj):
    url_name = 'admin:%s_%s_change' % (
        remote_field.model._meta.app_label,
        remote_field.model._meta.model_name,
    )
    try:
        url = reverse(
            url_name,
            args=[quote(remote_obj.pk)],
            current_app=self.model_admin.admin_site.name,   # <-- the fix
        )
        return format_html('<a href="{}">{}</a>', url, remote_obj)
    except NoReverseMatch:
        return str(remote_obj)
```

The single changed token is the `current_app=self.model_admin.admin_site.name`
keyword added to the `reverse(...)` call; everything else is unchanged.

## Modeling decision
The observable behavior of `get_admin_url` is the returned markup string. It is

    match reverse(url_name, [quote(pk)], current_app=site_name):
      ok url  -> format_html('<a href="{}">{}</a>', url, remote_obj)
      raises  -> str(remote_obj)

The fix changes WHICH `current_app` the resolver receives (the current site's
name, not nothing). So the model:

- assembles the route name `"admin:" ++ appLabel ++ "_" ++ modelName ++
  "_change"` exactly as the Python `%`-format does;
- invokes an arbitrary `resolveUrl : String → String → Option String → Option
  String` (standing for the unchanged `reverse`, with the `try/except
  NoReverseMatch` folded into `Option`) on the route name, the encoded id, and
  the current site identifier `some siteName`;
- on `some url` applies an arbitrary `formatLink : String → String → String`
  (standing for the unchanged `format_html`) to the URL and the display text;
- on `none` returns the display text (`str(remote_obj)`).

Universally quantifying `resolveUrl`/`formatLink` makes the spec hold for EVERY
resolver and formatter, so the only thing it can pin is that the correct
`current_app` (`some siteName`) reaches the resolution step — which is exactly the
bug.

## Operation correspondence
| # | Lean op (`implementation_getAdminUrl`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let urlName := "admin:" ++ appLabel ++ "_" ++ modelName ++ "_change"` | `url_name = 'admin:%s_%s_change' % (app_label, model_name)` | I | string formatting ↔ `++` concatenation; `app_label`/`model_name : str ↔ String`. |
| 2 | `resolveUrl urlName arg (some siteName)` | `reverse(url_name, args=[quote(remote_obj.pk)], current_app=self.model_admin.admin_site.name)` | A-reference | unchanged downstream callee `reverse`; left abstract (universally quantified) and bound to the REAL `reverse` in G-CONF. The `some siteName` third arg is the FIXED token (`current_app=site name`). No property consumed ⇒ NOT A-consumed, NOT axiomatized. |
| 3 | `match … | some url => return formatLink url remoteObjStr` | `return format_html('<a href="{}">{}</a>', url, remote_obj)` | A-reference | unchanged downstream callee `format_html`; left abstract and bound to the REAL `format_html` in G-CONF. |
| 4 | `match … | none => return remoteObjStr` | `except NoReverseMatch: return str(remote_obj)` | R | `Option.none ↔ NoReverseMatch raised`; the `str(remote_obj)` fallback ↔ `remoteObjStr`. The `try/except` control flow refines to the `Option` match. |

## R/I legs ⇒ G-CONF
Op 1 (route formatting, I) and op 4 (the `Option`/exception refinement, R) are the
R/I content; op 2 carries the FIXED token (`current_app` = `some siteName`). Ops
2 and 3 are A-references: G-CONF leaves them as the REAL `reverse` / `format_html`
(it does NOT substitute axiom models), which is precisely how the
current-app-selection leg is isolated and tested. `conf_skip = false`: the impl
region has genuine R/I content plus the fixed-token argument, so
`conformance_check.py` differential-tests the shadow (route formatting + resolving
with the current site's name as `current_app` + link/fallback framing, using the
REAL `reverse`/`format_html`) against the patched `get_admin_url`'s returned markup
over ≥10⁵ fuzzed inputs.

## No A-consumed row
The proof consumes no property of `resolveUrl`/`formatLink` (both universally
quantified), so `meta.json axioms = []`. Ops 2 and 3 are recorded as A-references
solely to document the G-CONF binding to the real callees; there is no
`opaque`/`axiom` declaration in `Solution.lean` and `axiom_check.py` is a skip
stub. No changed op is inexpressible: the fix is the `current_app` argument, which
is modeled directly as the `some siteName` resolver argument.

## F2P alignment
`test_readonly_foreignkey_links_custom_admin_site` renders a model with readonly
ForeignKey fields under the custom `namespaced_admin` site and asserts the
generated links carry the custom site's URL prefix (e.g.
`/test_admin/admin2/...`), not the default `/test_admin/admin/...`. Pre-patch the
resolver was called WITHOUT `current_app`, so the URL resolved under the default
namespace — the discriminating clause `problem_spec_getAdminUrl` pins (resolver
receives `some siteName`) and the prepatch impl (resolver receives `none`) cannot
satisfy. `test_readonly_foreignkey_links_default_admin_site` (PASS_TO_PASS) keeps
the default-site behavior unchanged. `patch.diff` (gold verbatim) makes the
harness resolve.
