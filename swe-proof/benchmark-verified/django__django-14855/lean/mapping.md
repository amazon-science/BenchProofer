# mapping.md — django__django-14855

## Instance
- repo: django/django
- base_commit: 475cffd1d64c690cdad16ede4d5e81985738ceb4
- spec_provenance: cold (derived from `problem_statement` + gold `patch` + the
  repo source at `base_commit` only; no pre-existing solution consulted)

## The logical change
`AdminReadonlyField.get_admin_url` (`django/contrib/admin/helpers.py:205-215`)
builds a change-view URL for a related object shown in a readonly field. At
`base_commit` it calls the URL resolver WITHOUT telling it which admin site is
currently in effect:

```python
url = reverse(url_name, args=[quote(remote_obj.pk)])
```

so on a non-default (custom-named) admin site the URL resolves under the DEFAULT
`/admin/...` namespace instead of the custom site's namespace. The gold patch
threads the current site's name into the resolver:

```python
url = reverse(
    url_name,
    args=[quote(remote_obj.pk)],
    current_app=self.model_admin.admin_site.name,
)
```

`reverse` (`django/urls/base.py`) reads `current_app` to select the namespace
instance when resolving a namespaced route; `format_html`
(`django/utils/html.py`) builds the `<a href="…">…</a>` markup. Neither is
changed by the patch. On `NoReverseMatch` the function returns `str(remote_obj)`.

## Symbol binding (file:line @ base_commit)
| Lean symbol | Python symbol | location @ base_commit |
|---|---|---|
| `implementation_getAdminUrl` / `problem_spec_getAdminUrl` / `correct_getAdminUrl` | `AdminReadonlyField.get_admin_url` | `django/contrib/admin/helpers.py:205-215` |
| `resolveUrl` (parameter) | `reverse(url_name, args=[…], current_app=…)`, where the `try/except NoReverseMatch` is folded into an `Option` (`none` = raised `NoReverseMatch`) | `django/urls/base.py` `reverse` |
| `formatLink` (parameter) | `format_html('<a href="{}">{}</a>', url, remote_obj)` | `django/utils/html.py` `format_html` |
| `appLabel` | `remote_field.model._meta.app_label` | model `_meta` |
| `modelName` | `remote_field.model._meta.model_name` | model `_meta` |
| `arg` | `quote(remote_obj.pk)` (the single positional arg, already URL-encoded) | `django/contrib/admin/utils.py` `quote` |
| `siteName` | `self.model_admin.admin_site.name` (the current admin site's name) | `AdminSite.name` |
| `remoteObjStr` | `str(remote_obj)` and the `remote_obj` display text in the link body | the related object |

## Type bijection (Lean ↔ Python) — used by G-CONF and G-AX
| Lean | Python | notes |
|---|---|---|
| `appLabel modelName arg siteName remoteObjStr : String` | the corresponding `str` values | byte-for-byte `str ↔ String` |
| `resolveUrl : String → String → Option String → Option String` | `reverse(name, args=[arg], current_app=cur)`; `none` result ↔ `NoReverseMatch` raised; `some s` ↔ returned URL string `s` | the third Lean arg is `Option String`: `some siteName ↔ current_app=siteName`, `none ↔ current_app omitted (None)` |
| `formatLink : String → String → String` | `format_html('<a href="{}">{}</a>', url, remote_obj)` | unchanged downstream callee; modeled abstractly, bound to the REAL callee in G-CONF |
| result `: String` | the returned markup (link) or `str(remote_obj)` fallback | byte-for-byte |

`String ↔ str` is the identity bijection (byte-for-byte).

## The observable behavior
The route name is `"admin:%s_%s_change" % (app_label, model_name)`. The function
resolves it for the encoded pk, telling the resolver the current admin site
(`current_app`); on success it returns the formatted `<a>` link, on
`NoReverseMatch` it returns the plain object string. The fix is solely that the
resolver is invoked WITH the current site's name (`some siteName`) rather than
WITHOUT it (`none`): for a namespaced route this selects the correct namespace
prefix.

## Callee provenance / flag deps
- No unchanged repo callee is consumed as an axiom. The URL-resolution step
  (`reverse`) and the link-formatting step (`format_html`) are left as
  universally-quantified parameters `resolveUrl` / `formatLink` (the spec holds
  for EVERY resolver and formatter), so the proof consumes no property of them
  and there is no `axiom <callee>_prop`. The modeled change is solely WHICH
  current-app identifier is selected for the resolution step. `axiom_check.py` is
  a skip stub.
- The `Option String` third argument of `resolveUrl` carries the flag dependency:
  `current_app` present (`some siteName`) vs absent (`none`). G-CONF fuzzes the
  site name, the route components, the encoded pk, and whether the route resolves.

## G-CONF fuzz seed
- pinned seed: `14855`
- ≥10⁵ fuzzed `(appLabel, modelName, arg, siteName, remoteObjStr, resolvable)`
  tuples over a real namespaced URLconf with a default admin site and a custom
  (named) admin site. `resolveUrl` and `formatLink` are bound to the REAL
  `reverse` / `format_html` callees. The observable is the returned markup string.
