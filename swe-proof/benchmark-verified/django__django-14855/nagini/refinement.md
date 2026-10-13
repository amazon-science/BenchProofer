# refinement.md — django__django-14855

The operation-by-operation correspondence between `model.py`'s implementation
(the `related_link_target` impl region and the consumed `resolve_prefix` axiom) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — here **A-consumed**, the proof uses the axiom's
`Ensures`), or **I** (identical concrete operation). The claim: *any
implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The change site — `AdminReadonlyField.get_admin_url` (`django/contrib/admin/helpers.py:212`)

Gold hunk:
```
-            url = reverse(url_name, args=[quote(remote_obj.pk)])
+            url = reverse(
+                url_name,
+                args=[quote(remote_obj.pk)],
+                current_app=self.model_admin.admin_site.name,
+            )
             return format_html('<a href="{}">{}</a>', url, remote_obj)
```

The surrounding lines the hunk sits in matter to the refinement and are quoted
here once (`helpers.py:206-216`): the call is inside a `try:` whose
`except NoReverseMatch:` arm does `return str(remote_obj)` — the rendering with
NO link. So the change site has two exits, and both are modeled.

| # | model.py impl op (`related_link_target`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameters `names, prefixes, exposes` (the sibling-instance registry) | the ambient `reverse` resolver state: `resolver.app_dict['admin']` (instance namespaces), their mount prefixes, and each instance's route table — all built from every registered `AdminSite` (its `get_urls()` iterating its own `_registry`) | R | the registry of sibling deployments under the shared `admin` app namespace ↔ parallel `PSeq` lists, with `exposes[k]` the bit "instance k carries a route for this identifier and argument" (mapping.md §2). |
| 2 | `current_idx`; `selector = nm[current_idx]` | `self.model_admin.admin_site.name` — the current deployment's instance name | R | `AdminSite.name` (`str`) ↔ `names[current_idx]` (`PSeq[int]`); `model_admin.admin_site` is the current site (mapping.md §1,§2). |
| 3 | `default_idx` | the instance `reverse` falls back to when it consults no selector (its `elif ns not in app_list: ns = app_list[0]` arm) | R | existential placeholder; the model never fixes its physical index (mapping.md §2), which is why the exact fallback rule — `app_dict['admin'][0]` unless a sibling is itself named `admin` — is not load-bearing. Load-bearing only for the empty-name clauses of step 5, which name this index without fixing it. |
| 4 | `resolve_prefix(nm, pf, ex, default_idx, selector, True)` — selector supplied (`has_selector=True`), route vector passed UNDOCTORED | `reverse(url_name, args=[quote(remote_obj.pk)], current_app=self.model_admin.admin_site.name)` — `current_app` supplied | A-consumed | `resolve_prefix` is the weakest contract on `reverse`'s namespace→instance selection AND the in-instance identifier lookup that follows it (mapping.md §3.1). The proof consumes its `has_selector` Ensures: a selector naming a registered instance returns that instance's prefix when that instance carries the route, and produces nothing when it does not. The patch supplies `current_app`, so `has_selector=True` (the `if current_ns and current_ns in app_list` branch). G-AX confirms both production clauses against the real `reverse`. |
| 5 | `Assert(nm[current_idx] == selector)` + the name-uniqueness `Requires` instantiate the axiom's two `has_selector` Foralls at `k=current_idx`, under the axiom's non-empty-selector guard | (the resolver matching `current_app` to the unique instance namespace `admin:<name>`, reached only past `if current_app:`, and then `_reverse_with_prefix` searching THAT instance for the identifier) | I + R | `selector` IS `names[current_idx]` (a registered instance, k=current_idx). Uniqueness of names ⇒ no other k matches ⇒ `resolve_prefix` returns exactly `prefixes[current_idx]` when `exposes[current_idx]`, and nothing when not — **and only when the name is non-empty**. An empty `AdminSite.name` is falsy, so the real `reverse` never reaches this matching (`base.py:41`) and resolves against the default instead — including for the route question, since it is then the DEFAULT instance that `_reverse_with_prefix` searches. The axiom's four clauses split on exactly those two axes, and the postcondition carries the same split (mapping.md §3.1, "Falsiness dependency" and "Partiality"). Concrete reasoning identical on both sides. |
| 6 | `return url` — a `PSeq[int]` that is `prefixes[selected]` when the selected deployment carries the route, and the EMPTY sequence when it does not | `url` then `format_html('<a href="{}">{}</a>', url, remote_obj)` on the resolving path; `except NoReverseMatch: return str(remote_obj)` on the non-resolving one | R | `format_html` wraps the URL into an `<a href>`; the F2P test observes the `href` prefix, which is exactly `url`'s prefix, and the wrapping does not depend on / change which instance prefix `url` carries (mapping.md §1). The `NoReverseMatch` exit produces markup with no `href` at all, i.e. NO prefix — the empty `PSeq` (mapping.md §2). Because every registered deployment's prefix is non-empty (a produced URL carries the resolution root), the two outcomes are distinguishable in the modeled value, so this exit is expressed rather than abstracted. |

The discriminating content of the change — passing the CURRENT site's name as
the resolution selector rather than nothing — lives in step 4's `has_selector`
flag (`True` in model.py vs `False` in `model_prepatch.py`). The pre-patch
omits `current_app` (`reverse(url_name, args=[quote(remote_obj.pk)])`);
`model_prepatch.py` reproduces that by calling `resolve_prefix(..., False)`,
which by the axiom resolves against the default deployment, and **fails** the
postcondition's non-empty-name route-carrying clause
(`len(names[current_idx]) > 0 and exposes[current_idx] ⇒ Result() ==
ToSeq(prefixes)[current_idx]`) whenever the current deployment has a non-empty
name, carries the route, and is not the default — exactly the spec sensing the
change (G-DIFF; measured, the twin fails on that clause).
The empty-name clauses are shared by both twins (both correctly resolve against
the default there), so they carry no discriminating content and cannot mask the
bug: the non-empty clause alone already rejects the pre-patch call. The two
route-absent clauses are likewise shared by both twins on the slices where they
apply; they constrain a DISJOINT slice of the input space (the selected
deployment carries no route), and their content is that no link is produced
there at all — see "verify(model) ⇒ resolved" below.

## Why a single consumed axiom (no deep model here)

The one operation that changed is the *argument list of a call* to an unchanged
framework function (`reverse` gains `current_app=`). The changed behaviour is
therefore entirely a property of how `reverse` selects a URL namespace
instance from `current_app`, and of what it then finds inside that instance — an
UNCHANGED callee. Per SPEC_GUIDE §0.7 / §3 that callee is axiomatized
(A-consumed), not modeled deeply: deep-modeling `reverse` (URL pattern
compilation, namespace dict construction, `_reverse_with_prefix`'s pattern
substitution) would model the unchanged machinery, not the change. The axiom
captures only the selection rule the fix relies on plus the single bit of the
lookup that is observable in the result (did the selected instance carry the
identifier at all), and G-AX validates both against the real `reverse`. There is
no A-reference deep model.

## No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The changed operation (supply
`current_app`) is expressed exactly: it flips the axiom's `has_selector`
argument from the pre-patch `False` to `True`, so resolution is performed
against the current deployment instead of the default one — which decides both
WHICH prefix a produced link carries and WHETHER a link is produced at all.

## verify(model) ⇒ resolved

`related_link_target` verifies only if, whenever the current deployment's name is
non-empty, its result is `prefixes[current_idx]` if that deployment carries a
route for the identifier and is EMPTY if it does not (step 4 + 5, requiring
`has_selector=True`, name uniqueness, and the undoctored route vector); and,
whenever that name is empty, the same two outcomes read off the DEFAULT
deployment — which is what the real `reverse` does for a falsy selector. The four
guards are pairwise mutually exclusive and jointly total, so the result is pinned
on every admissible input; no input is left unconstrained, and neither of the
"no link" clauses is a licence to produce nothing elsewhere (the
`weak-always-empty` rival in `properties.py` is the control for that, and it is
rejected).

Note what verification does NOT claim: it does not claim resolution always
succeeds. Resolution is a partial function of the registry, and the spec states
its domain of definition rather than assuming it away — an identifier absent from
the deployment resolution lands in yields no link, exactly as the real composite's
`except NoReverseMatch: return str(remote_obj)` arm renders none. Both twins agree
there, so this costs no discriminating power; what it buys is that the spec is not
strictly stronger than the callee on the heterogeneous registries the gold
`test_patch` itself constructs.

By R (instance-name/prefix ↔ `PSeq[int]`, `admin_site.name` ↔
`names[current_idx]`, per-site route table ↔ `exposes`, `format_html` wrapping
preserves the prefix, the no-link exit ↔ the empty `PSeq`) the verified function
equals
`reverse(url_name, args=[quote(remote_obj.pk)], current_app=self.model_admin.admin_site.name)`
wrapped by `get_admin_url`'s own two exits, on the tested deployment; by G-AX the
real `reverse` meets the `resolve_prefix` axiom (A-consumed), including its two
no-url clauses; by G-CONF the whole modeled composite agrees with the real patched
`get_admin_url` on every generated input. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the one
audited callee — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity
(this document, G-EQ).
