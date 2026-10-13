# mapping.md — django__django-14855

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 475cffd1d64c690cdad16ede4d5e81985738ceb4`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the one axiomatized callee.

Repo file under change: `django/contrib/admin/helpers.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `getAdminUrl (viewName pk appName objLabel)` | `AdminReadonlyField.get_admin_url(self, remote_field, remote_obj)` — `django/contrib/admin/helpers.py:206` | the modeled changed function (renders a readonly FK as a link) |
| `resolveAddress` *(axiom — A-consumed)* | `django.urls.base.reverse(viewname, urlconf, args, kwargs, current_app)` — `django/urls/base.py:27` | the UNCHANGED address-resolution callee the function calls; the fix threads its `current_app` argument |
| `render (addr) (label)` | `format_html('<a href="{}">{}</a>', url, remote_obj)` on the success leg / `str(remote_obj)` on the `NoReverseMatch` leg — `helpers.py:215,217` | pure spec: how a resolution outcome is displayed |
| `Rendered.link` / `Rendered.plain` | the two display outcomes (`<a href=…>label</a>` vs the bare label) | pure spec: the two display shapes |

The function's arguments are derived from `self`/`remote_obj` inside the real
method; the model takes them already-projected (refinement audit only, not in
the consumer view):
* `viewName` ← `url_name = 'admin:%s_%s_change' % (app_label, model_name)`
  (`helpers.py:207-210`);
* `pk` ← `quote(remote_obj.pk)` (`helpers.py:213` arg);
* `appName` ← `self.model_admin.admin_site.name` (the page's admin-site name);
* `objLabel` ← `remote_obj` rendered as text (the link caption / fallback).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `str` (`url_name`, the quoted pk, the admin-site name, the rendered object) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; per-code-point; empty `str` ↔ `[]` |
| `current_app=<name>` keyword (`reverse`'s 5th param) | `Option (List Char)` | a supplied site name `name` ↔ `some name.toList`; omitted/`current_app=None` ↔ `none`. The page always carries a site name, so the modeled call site passes `some appName`. |
| `reverse(...)` return / `NoReverseMatch` raised | `Option (List Char)` | a resolved URL `u` ↔ `some u.toList`; `NoReverseMatch` raised ↔ `none`. (The `try/except NoReverseMatch` in `get_admin_url` makes the raise observationally a "no address" outcome — modeled as `none`.) |
| `format_html('<a href="{}">{}</a>', url, obj)` | `Rendered.link url obj` | the success display: a hyperlink to `url` captioned with the object. `format_html`'s HTML assembly is fixed boilerplate around the two interpolated values; the behaviour the F2P test observes is *which url* is interpolated. |
| `str(remote_obj)` (except leg) | `Rendered.plain obj` | the fallback display: the bare object text, no hyperlink. |

Lean `String`/`List Char` indexing is total and sound; the carrier is
`List Char` because the values are strings compared by content.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `resolveAddress` ↔ `django.urls.base.reverse` (A-consumed)
**Callee:** `django.urls.base.reverse(viewname, urlconf=None, args=None,
kwargs=None, current_app=None)` — UNCHANGED by the patch. The fix is a pure
argument-threading change: it adds the keyword `current_app=self.model_admin.
admin_site.name` to the existing `reverse(url_name, args=[quote(remote_obj.pk)])`
call. `reverse` itself is not edited.

**Why `resolveAddress` takes the context as a third argument.** `reverse`
resolves a named route to a URL *within a current application namespace*. When
two `AdminSite` instances register the same app under different namespaces
(e.g. the default `admin` and a custom `namespaced_admin`), the SAME
`viewname`+`args` resolve to DIFFERENT URLs depending on the `current_app`
passed. The axiom models exactly this: `resolveAddress` is a function of
(route, arg, context) jointly, and pins NO concrete URL — the weakest contract
sufficient for the proof (directive 7). The only load-bearing fact the spec
relies on is that the context is a genuine determinant of the result; that the
real `reverse` honours `current_app` (different namespace ⇒ different URL) is
what makes `Solution.lean` (context `some appName`) and `Solution_prepatch.lean`
(context `none`, the ambient default) inequivalent, and is checked by G-AX.

**Soundness check (G-AX):** `axiom_check.py` builds a real Django URL
configuration with two admin sites registered under distinct namespaces
(`admin` and a custom site), then for the same `viewname`+`pk` runs the REAL
`reverse` once with `current_app=<custom site name>` and once with the default
(`current_app=None`). It asserts (a) `reverse` is a deterministic function of
its `(viewname, args, current_app)` inputs (same inputs ⇒ same output), and
(b) the custom context yields a URL under the custom namespace's prefix while
the default context yields one under the default prefix — i.e. the context
genuinely changes the result. This is precisely the obligation the bug violated.
Imports only `django` (configured in-process). Exit 0 iff sound.

## 4. G-CONF — skipped (conf_skip = true)

The modeled `do` block contains NO R/I (type-refinement or identical-concrete)
input-dependent computation to differential-test: its entire content is the
single A-consumed callee `resolveAddress` (the `reverse` call) followed by a
`match` that dispatches to the two display shapes `render` defines. The display
assembly (`format_html` / `str`) is fixed boilerplate (R), and the one
behaviourally-meaningful op — *which context the route resolves within* — is the
A-consumed `reverse` call, validated by G-AX, not by a pure Python shadow.

Per SPEC_GUIDE §3 / WORKER_PROMPT: when the impl region is all-A-tagged, set
`meta.json conf_skip=true` and ship a `status=skip` stub. The observable the
change governs (the namespaced URL emitted into the rendered page) materializes
only by serving a real admin page against a real URL configuration — which is
exactly what the F2P test
`test_readonly_foreignkey_links_custom_admin_site` does end-to-end; it is not a
pure, DB-free R/I shadow this gate can fuzz over ≥10⁵ inputs. The behavioural
soundness of the `reverse` contract is covered by G-AX; spec-strength by
G-VERIFY; discrimination by G-DIFF.

The pinned fuzz seed (for the G-AX randomized leg) is **`14855`**.
