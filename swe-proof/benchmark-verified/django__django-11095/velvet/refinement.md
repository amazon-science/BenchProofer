# refinement.md — django__django-11095

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the methods `getInlines` and `getInlineInstances`, plus the pure `kept` fold)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement;
state the bijection), **A-consumed** / **A-reference** (none in this bundle), or
**I** (identical concrete op). EVERY step is R or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The new selection hook — `get_inlines`

Gold hunk (added method):
```
+    def get_inlines(self, request, obj):
+        """Hook for specifying custom inlines."""
+        return self.inlines
```

| # | Solution.lean impl op (`getInlines`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `declared : List InlineClass` | `self.inlines` | R | the statically declared registration tuple ↔ `List InlineClass` (mapping.md §2). |
| A2 | `return declared` (`ensures out = declared`) | `return self.inlines` | I | the default hook body is the identity on the declared set. A subclass override is modeled by letting the *caller* pass `selected ≠ declared` (B-level), not by changing this default. |

## B. The changed build loop — `get_inline_instances`

Gold hunk (the iterated-source change):
```
 def get_inline_instances(self, request, obj=None):
     inline_instances = []
-    for inline_class in self.inlines:
+    for inline_class in self.get_inlines(request, obj):
         inline = inline_class(self.model, self.admin_site)
         if request:
             if not (inline.has_view_or_change_permission(request, obj) or
                     inline.has_add_permission(request, obj) or
                     inline.has_delete_permission(request, obj)):
                 continue
             if not inline.has_add_permission(request, obj):
                 inline.max_num = 0
         inline_instances.append(inline)
     return inline_instances
```

| # | Solution.lean impl op (`getInlineInstances` / `kept`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | param `selected : List InlineClass` | the iterated sequence `self.get_inlines(request, obj)` | R | the hook return ↔ `List InlineClass` (mapping.md §2). This is the value the loop iterates **post-patch**; the change is precisely that this is the hook return, not the static `self.inlines`. |
| B2 | param `declared : List InlineClass` | `self.inlines` (the default the hook returns) | R | carried so the spec can state the default-hook identity (`getInlines`); the post-patch loop does NOT iterate `declared` directly — modeled as read-only and unused by `getInlineInstances`' result (it equals `selected` only when the hook is not overridden). |
| B3 | param `admissible : InlineClass → Bool` | `inline.has_view_or_change_permission(...) or inline.has_add_permission(...) or inline.has_delete_permission(...)` (truthy request) | R | the unchanged per-inline keep disjunction ↔ a total free `InlineClass → Bool` (mapping.md §2/§3). Abstracted as a free input — unchanged by the patch. |
| B4 | `result = kept admissible selected`, computed by the backward `while` fold | the `for inline_class in selected: … if keep: inline_instances.append(inline)` loop | I | `kept` IS the in-order keep-sublist the loop builds, modeled deeply; the fold ops (`admissible c`, `++`, the loop) are concrete and transliterated by G-CONF. The instantiation `inline_class(...)` and the `max_num = 0` mutation are unchanged and observationally invisible to the returned list's class membership (mapping.md §2), so they carry no node. |

## C. The discriminating content — what the spec senses

The change: pre-patch, `get_inline_instances` iterates the **statically declared**
set `self.inlines` directly; post-patch it iterates `self.get_inlines(request,
obj)` — an overridable hook whose default is `self.inlines` but which a subclass
may override to return a *different* selection based on the request or object.

The frozen spec pins the result to `kept admissible selected` — the keep-sublist
of the **selected** (hook) sequence. `Solution_prepatch.lean` reproduces the
pre-patch skeleton (the build loop iterates `declared` instead of `selected`) and
**fails** verification on exactly the clause `result = kept admissible selected`
with `result = kept admissible declared` in hand (G-DIFF, confirmed unsolved goal
`ensures_1: result = kept admissible selected`). The two states diverge precisely
when the hook is overridden so `selected ≠ declared` — e.g. the F2P test's
`get_inlines` returning `[]`, `self.inlines[:1]`, or `self.inlines[1:2]`, while
`self.inlines = (AlternateInline, MediaInline)`. With the MockSuperUser request
(`has_perm` always True ⇒ `admissible` always True) the result equals `selected`
verbatim, so the pre-patch loop (iterating `declared`) yields the full declared
tuple where the post-patch must yield the hook's selection — exactly what
`test_get_inline_instances_override_get_inlines` observes.

## D. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely changed — the SOURCE the
build loop iterates (`self.inlines` → `self.get_inlines(request, obj)`) — is
modeled **deeply** (the `kept` fold over the `selected` parameter, B1/B4),
not hidden behind an axiom about a function under change. There are **no consumed
axioms and no A-references**: every callee in the loop body (`inline_class(...)`,
`has_view_or_change_permission`, `has_add_permission`, `has_delete_permission`,
the `max_num` assignment) is UNCHANGED by the patch and is abstracted as a free
input with no relied-on property (mapping.md §3), so nothing requires G-AX
validation.

## E. verify(Solution) ⇒ resolved

`getInlineInstances` verifies only if its result equals the exact modeled
decision: `kept admissible selected` (B4) — the keep-sublist of the **hook's
selection**, not the static declared set. By R (the `List InlineClass` /
`InlineClass → Bool` bijections, mapping.md §2) the verified builder equals the
gold-patched `get_inline_instances` on every input, and `getInlines`' `ensures
out = declared` matches the new hook's default body (A2). By G-CONF the R/I
transliteration of the fold + hook agrees with the patched `options.py` build
loop on ≥10⁵ checks (seed 11095, 0 disagreements), including the override
scenarios the F2P test exercises. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE). The sole trust point is refinement fidelity (this
doc, G-EQ + G-CONF); there are no axioms (G-AX skips).
