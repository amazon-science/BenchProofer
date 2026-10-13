# mapping.md — django__django-11095

## Symbol binding (file:line @ base_commit 7d49ad7656)
Modeled function: `ModelAdmin.get_inline_instances`,
`django/contrib/admin/options.py:586-599` @ base_commit. The gold patch (a)
adds a new overridable hook `ModelAdmin.get_inlines(self, request, obj)` at
`options.py:330-332` whose default body returns `self.inlines`, and (b) changes
the single iteration line of `get_inline_instances` from

```python
for inline_class in self.inlines:
```
to
```python
for inline_class in self.get_inlines(request, obj):
```

The observable fixed behavior: `get_inline_instances` now builds its instances
from the list returned by the (overridable) hook, NOT from the static
`self.inlines` attribute. The remainder of the loop — instantiate each class,
and (when a request is present) drop classes the viewer may neither view/change,
add, nor delete, and zero the per-form maximum for classes the viewer may not add
— is unchanged.

Lean modeled function name: `getInlineInstances`.

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `getInlineInstances` (modeled loop) | `ModelAdmin.get_inline_instances`, `options.py:586-599` (post-patch `:590-603`) |
| `hasRequest` | truthiness of the `request` argument (`if request:`), `options.py:589` |
| `selfInlines` | `self.inlines` (the static attribute) — pre-patch iteration source, `options.py:588` (pre) |
| `hookInlines` | `self.get_inlines(request, obj)` (the new hook's output) — post-patch iteration source, `options.py:588` (post); default hook body returns `self.inlines` (`options.py:330-332` added) |
| `Inline.id` | identity of an `inline_class` (which class object) |
| `Inline.hasViewOrChange` | `inline.has_view_or_change_permission(request, obj)`, `options.py:591-592` |
| `Inline.hasAdd` | `inline.has_add_permission(request, obj)`, `options.py:593,595` |
| `Inline.hasDelete` | `inline.has_delete_permission(request, obj)`, `options.py:593` |
| `InlineInstance.id` | the appended `inline` instance's class identity |
| `InlineInstance.maxNumZeroed` | whether `inline.max_num = 0` was applied (`not inline.has_add_permission(...)`), `options.py:595-596` |
| result | `inline_instances` (the returned list of inline instances, in order) |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `bool(request)` (request is not None) | `hasRequest : Bool` |
| `self.inlines` — an ordered sequence of inline classes | `selfInlines : List Inline` |
| `self.get_inlines(request, obj)` — an ordered sequence of inline classes | `hookInlines : List Inline` |
| an inline class + the three boolean permission outcomes of its instance | `Inline` structure (`id`, `hasViewOrChange`, `hasAdd`, `hasDelete`) |
| an appended `inline` instance + whether its `max_num` was zeroed | `InlineInstance` structure (`id`, `maxNumZeroed`) |
| `inline_instances` (ordered) | `result : List InlineInstance` |

### Modeling note — permission outcomes as data
The three permission predicates (`has_view_or_change_permission`,
`has_add_permission`, `has_delete_permission`) are unchanged callees. Their
observable outcomes for a given `(request, obj)` enter as the three booleans
carried by each `Inline`. They are NOT axiomatized: the loop consumes their
results as data, and the filtering/`max_num`-zeroing logic that uses them is
modeled deeply (R/I), so there is no consumed callee axiom and no A-reference.

### Modeling note — the hook output as data
`get_inlines(request, obj)` is the newly-added indirection. Its output for the
given `(request, obj)` is supplied as `hookInlines`. The default hook returns
`self.inlines`, but the whole purpose of the hook is to be overridden so it may
differ from `self.inlines`; that is precisely the discriminator. Both the static
attribute (`selfInlines`) and the hook output (`hookInlines`) are therefore
distinct inputs: the fix iterates `hookInlines`, the pre-patch bug iterates
`selfInlines`.

## Callee provenance + flag deps
- No unchanged callee is consumed as an axiom; none is an A-reference. The
  permission predicates enter as the three `Inline` booleans (data); the hook
  output enters as `hookInlines` (data). `axiom_check.py` is a skip stub.
- Flag dependency: the per-class filtering/`max_num` logic fires only when
  `request` is truthy (`hasRequest = true`). When `hasRequest = false`, every
  class is instantiated and appended unmodified.

## G-LEAK
The solver-visible `problem_statement` itself names `get_inlines`,
`get_inline_instances`, `inlines`, `ModelAdmin`, `request`, and `obj`, so these
are public vocabulary. The spec view describes the abstract behavior ("the list
of inline classes selected for this request/object", permission filtering) and
does not quote any gold-diff line nor narrate the bug→fix mechanism. The
permission-callee names (`has_add_permission`, `max_num`, etc.) are described
behaviorally, not by symbol.

## Pinned G-CONF fuzz seed
`11095`.
