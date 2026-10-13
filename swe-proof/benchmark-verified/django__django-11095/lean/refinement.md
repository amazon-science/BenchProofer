# refinement.md — django__django-11095

Maps every operation in `implementation_getInlineInstances` to its `patch.diff`
counterpart in `ModelAdmin.get_inline_instances`
(`django/contrib/admin/options.py`). Tags: **R** type-refinement,
**A-consumed** proof uses a callee axiom, **A-reference** deep-modeled changed op
validated == real callee, **I** identical concrete op.

## Patch (post-patch `get_inline_instances` + the new hook)
```python
def get_inlines(self, request, obj):
    """Hook for specifying custom inlines."""
    return self.inlines

def get_inline_instances(self, request, obj=None):
    inline_instances = []
    for inline_class in self.get_inlines(request, obj):     # was: self.inlines
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
The single behavioral change is the iteration source: `self.inlines` →
`self.get_inlines(request, obj)`. The new `get_inlines` default returns
`self.inlines`, but it exists to be overridden, so its output (`hookInlines`) may
differ from the static attribute (`selfInlines`). The rest of the loop is
verbatim-unchanged.

## Hook function (`implementation_getInlines`)
The patch also ADDS the hook `get_inlines(self, request, obj): return self.inlines`.
Modeled as `implementation_getInlines selfInlines := Id.run do return selfInlines`,
pinned by `problem_spec_getInlines : result = selfInlines`.

| # | Lean op (`implementation_getInlines`) | patch.diff op | tag | note |
|---|---|---|---|---|
| H1 | `return selfInlines` | `return self.inlines` | I | the default hook body returns the static attribute unchanged. |

This captures the newly-added default; its OUTPUT is what feeds
`getInlineInstances` as `hookInlines` (which may differ from `selfInlines` once
the hook is overridden — the discriminator the F2P test exercises).

## Operation correspondence (`implementation_getInlineInstances`)
| # | Lean op (`implementation_getInlineInstances`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut inlineInstances : List InlineInstance := []` | `inline_instances = []` | I | accumulator starts empty. |
| 2 | `for inlineClass in hookInlines do` | `for inline_class in self.get_inlines(request, obj):` | R | the selected-inline-class list. `self.get_inlines(request, obj)` output ↔ `hookInlines : List Inline` (mapping.md). This is THE changed line: post-patch iterates the hook output, not `self.inlines`. |
| 3 | `let mut inst := { id := inlineClass.id, maxNumZeroed := false }` | `inline = inline_class(self.model, self.admin_site)` | R | instantiate the class; the editor's identity ↔ `inlineClass.id`; `max_num` not yet zeroed. The constructor is an unchanged callee whose only modeled output is the instance identity (data). |
| 4 | `if hasRequest then` | `if request:` | R | `bool(request)` (request present) ↔ `hasRequest : Bool`. |
| 5 | `if !(inlineClass.hasViewOrChange \|\| inlineClass.hasAdd \|\| inlineClass.hasDelete) then continue` | `if not (inline.has_view_or_change_permission(...) or inline.has_add_permission(...) or inline.has_delete_permission(...)): continue` | R | three permission-predicate outcomes ↔ the three `Inline` booleans (data, mapping.md); `not (a or b or c)` ↔ `!(a \|\| b \|\| c)`; `continue` ↔ early `continue`. |
| 6 | `if !inlineClass.hasAdd then inst := { inst with maxNumZeroed := true }` | `if not inline.has_add_permission(...): inline.max_num = 0` | R | zeroing the per-editor max-rows when the viewer may not add ↔ setting `maxNumZeroed := true`. |
| 7 | `inlineInstances := inlineInstances ++ [inst]` | `inline_instances.append(inline)` | I | append the editor in order. |
| 8 | `return inlineInstances` | `return inline_instances` | I | return the ordered list. |

Every op is R or I; **no A row** (no axiom consumed, no deep-model reference of
an unchanged callee — the permission predicates and the constructor enter as
data per mapping.md; the hook output enters as `hookInlines`). Therefore
`meta.json axioms = []`, `deep_model_references = []`, and `axiom_check.py` is a
skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow against `patch.diff` behavior over ≥10^5 fuzzed inputs.
`conf_skip = false`.

## Prepatch = the real bug
Pre-patch, the loop iterates `self.inlines` (the static attribute) directly:
`for inline_class in self.inlines:`. The prepatch impl
(`implementation_getInlineInstances … := for inlineClass in selfInlines do …`,
identical otherwise) is exactly this: it builds editors from `selfInlines`,
ignoring the hook output `hookInlines`. It therefore cannot satisfy
`problem_spec_getInlineInstances` (which pins the result to be built from
`hookInlines`) whenever the hook output differs from the static attribute —
precisely the case the FAIL_TO_PASS test
`test_get_inline_instances_override_get_inlines` exercises: an admin overrides
`get_inlines` to return `[]` (or a one-element slice of `self.inlines`) while
`self.inlines` has two entries, and asserts `get_inline_instances` reflects the
hook output. The carried gold proof fails to typecheck against the buggy impl
(G-DIFF).
