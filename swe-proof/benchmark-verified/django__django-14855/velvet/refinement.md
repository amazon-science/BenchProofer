# refinement.md — django__django-14855

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `getAdminUrl` `do` block, plus the `render` display model and the
`resolveAddress` axiom) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — **A-consumed** where the
proof uses the axiom's `ensures`, **A-reference** where a deep model is
validated == the real callee by G-AX), or **I** (identical concrete op).

The R/I legs would be mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); for this bundle the impl region is all-A-tagged, so G-CONF is skipped
(`conf_skip = true`, §C) and the A leg is audited by **G-AX**; the narrative is
audited by **G-EQ**. Claim: any impl verifying against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The resolution site — `get_admin_url()` (`helpers.py:206`)

Gold hunk:
```
  try:
-     url = reverse(url_name, args=[quote(remote_obj.pk)])
+     url = reverse(
+         url_name,
+         args=[quote(remote_obj.pk)],
+         current_app=self.model_admin.admin_site.name,
+     )
      return format_html('<a href="{}">{}</a>', url, remote_obj)
  except NoReverseMatch:
      return str(remote_obj)
```

| # | Solution.lean impl op (`getAdminUrl`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `viewName : List Char` | `url_name` (1st arg of `reverse`) | R | `str` ↔ `List Char` (mapping.md §2). Built from `app_label`/`model_name`; unchanged by the patch, taken already-projected. |
| A2 | param `pk : List Char` | `quote(remote_obj.pk)` (the `args=[…]` element) | R | `str` ↔ `List Char`; the positional argument to `reverse`, unchanged. |
| A3 | param `appName : List Char`, passed as `some appName` to `resolveAddress` | `current_app=self.model_admin.admin_site.name` (the ADDED keyword) | R | this is the gold change: the page's admin-site name threaded into the resolver. `current_app=<name>` ↔ `some name` (mapping.md §2). The page always carries a site name, so the modeled call site passes `some appName`, never `none`. |
| A4 | `resolveAddress viewName pk (some appName)` | `reverse(url_name, args=[quote(remote_obj.pk)], current_app=…)` | A-consumed | `resolveAddress` is the weakest contract on the UNCHANGED `reverse` callee the spec needs: a function of (route, arg, context) jointly, pinning no concrete URL (mapping.md §3.1). The proof consumes it through the `ensures`. The `try/except NoReverseMatch` makes a raised `NoReverseMatch` observationally a "no address" outcome, modeled as the `none` result of `resolveAddress`. G-AX confirms against the real `reverse`. |
| A5 | `match … | some a => Rendered.link a objLabel` | `return format_html('<a href="{}">{}</a>', url, remote_obj)` | R + I | the success display: a hyperlink to the resolved address captioned with the object. `format_html`'s HTML assembly is fixed boilerplate (R); the `match` dispatch on the resolution outcome is the `I` control op. |
| A6 | `match … | none => Rendered.plain objLabel` | `except NoReverseMatch: return str(remote_obj)` | R + I | the fallback display: the bare object text (R: `str(remote_obj)` ↔ the label), reached when no address resolves. |

Discriminating content of the change — *the route is resolved within
`some appName` (the page's own context), not within the ambient default* —
lives in the `ensures out = render (resolveAddress viewName pk (some appName))
objLabel` clause (model) ⇔ the added `current_app=…` keyword (real). The
pre-patch resolved with the ambient default (no `current_app`);
`Solution_prepatch.lean` reproduces that as `resolveAddress viewName pk none`
and **fails** the `ensures` clause, because `resolveAddress` is opaque and
`resolveAddress viewName pk none` is not provably equal to
`resolveAddress viewName pk (some appName)` (G-DIFF). This is exactly the bug:
under a custom admin site, the default-context URL (`/admin/…`) differs from the
custom-context URL (`/custom-admin/…`).

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* — adding the
application context to the resolution — is captured exactly: the context is a
genuine third argument to the A-consumed `resolveAddress` (the unchanged
`reverse` callee), and the change is the difference between passing `some
appName` and passing `none`. There is no consumed axiom about the function under
spec (`get_admin_url` is modeled directly as `getAdminUrl`); the only consumed
axiom, `resolveAddress`, covers the **unchanged** library callee `reverse`.

## C. G-CONF skipped (conf_skip = true)

The impl region is all-A-tagged: its sole behaviourally-meaningful op is the
A-consumed `resolveAddress` call (A4), and the surrounding `match` (A5/A6) is
fixed display dispatch with no input-dependent R/I computation a Python shadow
could fuzz over the real repo type. The observable the change governs — the
namespaced URL emitted into the rendered admin page — materializes only by
serving a real admin page against a real URL configuration (the F2P test does
this end-to-end), not as a pure DB-free shadow. So `conformance_check.py` is a
`status=skip` stub; the A leg is covered by G-AX (`axiom_check.py`), spec
strength by G-VERIFY, and discrimination by G-DIFF. See mapping.md §4.

## D. verify(Solution) ⇒ resolved

`getAdminUrl` verifies only if its output equals `render (resolveAddress
viewName pk (some appName)) objLabel` (A4 + A5/A6): the address resolved within
the page's OWN application context, displayed as a captioned hyperlink or, on a
resolution failure, the bare label. By R (`str ↔ List Char`,
`current_app ↔ Option`, `format_html`/`str` displays) the verified routine
equals the patched `get_admin_url` on the tested inputs; by G-AX the axiom
`resolveAddress` is sound for the real `reverse` (and the context genuinely
changes the URL). Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and the one audited callee — and
the gold patch resolves (G-RESOLVE). Trust points are exactly the two of plan
§1.1: axiom soundness (G-AX) and refinement fidelity (this doc, G-EQ).
