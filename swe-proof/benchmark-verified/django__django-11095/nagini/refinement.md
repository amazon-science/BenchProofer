# refinement.md — django__django-11095

The operation-by-operation correspondence between `model.py`'s implementation
(the `select_applicable_editors` and `materialize_editors` impl regions, plus the
deep `kept` model) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — split into **A-consumed**,
where the proof uses an axiom's `Ensures`, and **A-reference**, where a deep
model is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

This patch touches two cooperating functions, modeled as two contracted
functions (per-function pre/post/invariant/impl marker regions repeat); the
`axioms` and `pure` regions are single module-level singletons.

## A. The new selection hook — `ModelAdmin.get_inlines` (`options.py:331`, added)

Gold hunk 1 (added):
```python
+    def get_inlines(self, request, obj):
+        """Hook for specifying custom inlines."""
+        return self.inlines
```

| # | model.py impl op (`select_applicable_editors`) | patch.diff op (gold) | tag | justification |
|---|---|---|---|---|
| A1 | parameter `self: AdminView`, fields `self.configured` | the `ModelAdmin self` and `self.inlines` | R | the configured collection of inline classes ↔ `List[int]` of class ids (mapping.md §2). |
| A2 | the loop copying `self.configured` element-for-element into `result` so `ToSeq(result) == ToSeq(self.configured)` | `return self.inlines` | R | the model spells out the copy as a verified loop (Nagini cannot return a list aliasing a field at full permission while keeping the read-only postcondition); the result is the configured collection unchanged, in order — `return self.inlines` IS that collection, in order (mapping.md §2, §3.1). The default report is the configured collection. The deep model is validated == the real `get_inlines` by G-AX (A-reference, §3.1). |

`select_applicable_editors`'s contract pins the **default** report to
`ToSeq(self.configured)`: the hook neither drops, adds, nor reorders any
configured entry. This is the property the F2P test's non-overridden default
relies on (the configured order is preserved into the materialised editors).

## B. The materialisation change — `ModelAdmin.get_inline_instances` (`options.py:585`)

Gold hunk 2 (the one-line source change):
```python
     def get_inline_instances(self, request, obj=None):
         inline_instances = []
-        for inline_class in self.inlines:
+        for inline_class in self.get_inlines(request, obj):
             inline = inline_class(self.model, self.admin_site)
             if request:
                 if not (inline.has_view_or_change_permission(request, obj) or
                         inline.has_add_permission(request, obj) or
                         inline.has_delete_permission(request, obj)):
                     continue
                 ...
```

| # | model.py impl op (`materialize_editors`) | patch.diff op (gold) | tag | justification |
|---|---|---|---|---|
| B1 | iterate over `self.reported` | `for inline_class in self.get_inlines(request, obj)` | R + A-reference | THE FIX. `self.reported` is the value the (possibly overridden) hook returns — `self.get_inlines(request, obj)` (mapping.md §1, §2). Iterating the hook's report (not `self.configured`) is the changed operation. The hook's report is modeled as a field so the override is observable; the deep model is validated == the real `get_inline_instances` by G-AX (A-reference, §3.2). Pre-patch iterated `self.inlines` (= `self.configured`); see §C. |
| B2 | `cls = self.reported[j-1]` (reading the reported class id) | `inline = inline_class(self.model, self.admin_site)` | R | constructing the editor object from its class; the construction is the identity on "which class" — the test observes `type(inline) == inline_class` (mapping.md §2). |
| B3 | `if self.granted[j-1] != 0: result = [cls] + result` (keep when the context grants the entry; otherwise drop) | the `if request: if not (has_view_or_change_permission or has_add_permission or has_delete_permission): continue` guard, then `inline_instances.append(inline)` | R | the per-class permission decision (the `or` of the three `has_*_permission` calls) ↔ the aligned flag `granted` (mapping.md §1, §2); `continue` ↔ skipping the append; appending the kept class ↔ `[cls] + result`. The unchanged permission filter. For the F2P MockSuperUser every flag is set ⇒ nothing dropped. |
| B4 | (no node) | `if not inline.has_add_permission(request, obj): inline.max_num = 0` | R | the `max_num` tweak adjusts a kept editor's form count; it does NOT change the editor's class identity, the only property the F2P test observes (`type(...)`). Modeled as the identity on the kept class id (mapping.md §2). Unchanged by this patch. |
| B5 | `return result` | `return inline_instances` | R | the list of kept class ids ↔ the list of kept editor objects, in order (mapping.md §2). |

`materialize_editors`'s contract pins the result to
`kept(ToSeq(self.reported), ToSeq(self.granted))`: the materialised editors are
built from the **hook's report**, filtered by the permission flags, in order.

## C. Where the spec senses the bug (G-DIFF)

`model_prepatch.py` is the pre-patch skeleton: its `materialize_editors` impl
iterates `self.configured` (the configured collection) directly, exactly as the
pre-patch loop iterated `self.inlines` — never consulting the hook's report. The
spec region is byte-identical (G-DIFF `same_spec`). With the frozen spec it
**fails** verification on the postcondition
`ToSeq(Result()) == kept(ToSeq(self.reported), ToSeq(self.granted))`
(`model_prepatch.py:130`), because when the context's report `self.reported`
differs from the configured collection `self.configured` (the override case),
the materialisation built from `configured` is not the report-derived `kept(...)`.

That is precisely the behaviour the F2P test
`test_get_inline_instances_override_get_inlines` observes: an `EpisodeAdmin`
overriding `get_inlines` to return `self.inlines[:1]` / `self.inlines[1:2]` /
`[]` must yield `get_inline_instances` whose editors are of exactly the reported
classes — the pre-patch code, iterating `self.inlines`, would build both
configured editors regardless of the override. One independently-fixed behaviour
(the materialisation source), so one `model_prepatch.py`. The added hook
(`select_applicable_editors`) is the default `return self.inlines`; its own
behaviour is exercised by the deep-model A-reference (G-AX §3.1) and consumed by
`materialize_editors` via `self.reported` — no separate failing prepatch is
needed for it, since with no override its report equals the configured
collection (no differential), and the differential the patch creates lives
entirely in the materialisation source (site B).

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The two operations that genuinely
*changed* — adding the hook (returns the configured collection) and re-sourcing
the materialisation from that hook's report — are modeled **deeply** (the copy
loop in `select_applicable_editors`; iterating `self.reported` in
`materialize_editors`), then validated == the real callees by G-AX
(A-reference, mapping.md §3.1/§3.2). There is **no consumed `@ContractOnly`
axiom**: no unchanged library callee's contract is relied upon. We never
axiomatize the functions under change.

## E. verify(model) ⇒ resolved

`select_applicable_editors` verifies only if it returns the configured collection
unchanged in order (A2); `materialize_editors` verifies only if it materialises
from the hook's report `self.reported` (B1) — the FIX — keeping the
permission-granted entries in order (B3). By R (inline classes ↔ int ids;
`self.inlines` ↔ `configured`; `self.get_inlines(request, obj)` ↔ `reported`;
the permission `or` ↔ `granted`; constructed editor / `max_num` tweak ↔ the kept
class id) the verified materialisation equals the gold
`for inline_class in self.get_inlines(request, obj): … append(inline)` on the
tested inputs. By G-AX the real `get_inlines` reports the configured collection
(A-reference §3.1) and the real `get_inline_instances` builds editors from that
report (A-reference §3.2). Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement and the audited callees —
and the gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: deep-model fidelity to the real callees (G-AX) and refinement
fidelity (this document, G-EQ).
