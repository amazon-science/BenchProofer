# mapping.md — django__django-11095

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 7d49ad76562e8c0597a0eb66046ab423b12888d8`, states the type
abstraction, and gives the provenance of the deep-model reference (the real
callees the deep model is validated against by G-AX).

Repo file under change: `django/contrib/admin/options.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `select_applicable_editors(self, request, obj)` | the new hook `ModelAdmin.get_inlines(self, request, obj)` — inserted at `django/contrib/admin/options.py:331` (after `get_fieldsets`, before `get_ordering`), body `return self.inlines` | the modeled new selection hook (its default report) |
| `materialize_editors(self, request, obj)` | `ModelAdmin.get_inline_instances(self, request, obj=None)` — `django/contrib/admin/options.py:583` (the loop header at line 585) | the modeled changed function (materialises live editor objects) |
| `AdminView` | `ModelAdmin` (`django/contrib/admin/options.py:528`) | a minimal class carrying only the touched collections |
| `self.configured` | `self.inlines` (the configured inline-editor classes; `options.py:546`) | the configured collection of editor classes |
| `self.reported` | the value returned by `self.get_inlines(request, obj)` — i.e. what the (possibly overridden) hook reports for the current context | the hook's report, the SOURCE the post-patch loop iterates (`for inline_class in self.get_inlines(request, obj)`) |
| `self.granted` | per-reported-class permission decision: `inline.has_view_or_change_permission(request, obj) or inline.has_add_permission(request, obj) or inline.has_delete_permission(request, obj)` (`options.py:588-590`) | the per-entry "access context grants this editor" flag (the unchanged permission filter) |
| `kept(reported, granted)` | the subsequence of the iterated source kept by the permission filter (`continue` drops a class whose context grants nothing; `options.py:591`) | pure spec: the report filtered by the permission flags |
| `Result()` (the `List[int]` returned) | `inline_instances` — the list of constructed inline editor objects (`options.py:584,592,594`) | the materialised editors; each editor's class identity ↔ the reported identifier it was built from |

The gold patch (two hunks):
1. **adds** the hook `get_inlines(self, request, obj)` (`return self.inlines`) —
   modeled by `select_applicable_editors`, whose postcondition pins the default
   report to the configured collection (`ToSeq(Result()) == ToSeq(self.configured)`).
2. **changes** the materialisation loop header from
   `for inline_class in self.inlines:` to
   `for inline_class in self.get_inlines(request, obj):` — modeled by sourcing
   `materialize_editors` from `self.reported` (the hook's report) instead of
   `self.configured`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `ModelAdmin` instance | `AdminView` instance | a minimal class carrying only the three touched collections |
| an inline editor **class** (e.g. a `GenericTabularInline` subclass) | an `int` class identifier | distinct classes ↔ distinct ints; the F2P test observes only class identity (`type(instance) == inline_class`), so an `int` tag is a faithful carrier of "which editor class" |
| `self.inlines` (a tuple/list of inline classes) | `self.configured : List[int]` | element `k` ↔ the `k`-th configured class id; `len` / order preserved |
| `self.get_inlines(request, obj)` result (a tuple/list of inline classes) | `self.reported : List[int]` | element `k` ↔ the `k`-th reported class id; this is the hook's return value (default = `self.inlines`; an override returns a subset/other list). Modeled as a field so the override is observable: the materialisation reads `reported`, not `configured`. |
| the per-class permission decision (the `or` of the three `has_*_permission` calls) | `self.granted : List[int]` index-aligned with `reported` (`!= 0` ⇔ access granted) | granted[k] ≠ 0 ⇔ the context grants editor k (kept); = 0 ⇔ dropped (`continue`). For the F2P MockSuperUser every flag is set, so nothing is dropped. |
| `inline_class(self.model, self.admin_site)` constructing an instance, then `inline.max_num = 0` when add-permission is absent | the kept class identifier appended to `Result()` | the test observes class identity, in order, of the kept editors; instance construction is the identity on "which class", and the `max_num` tweak does not change class identity (refinement.md, step B4). |
| `request` (an `HttpRequest`) / `obj` (a model instance or `None`) | `request : int` / `obj : Optional[int]` | opaque tags not inspected by the modeled behaviour; the access decision they drive is carried abstractly by `granted` |
| `inline_instances` (list of editor objects) | `Result() : List[int]` of class ids | element `k` ↔ class identity of the `k`-th materialised editor |

`str`/dynamic dispatch is not modeled; the carrier is `List[int]` of class
identifiers throughout, with the specification phrased over `PSeq[int]` via
`ToSeq`.

## 3. Deep-model reference (A-reference — checked by G-AX / axiom_check.py)

**No `@ContractOnly` axiom is consumed.** Both operations are modeled deeply
(pure collection/control-flow logic): the default hook copies the configured
collection, and the materialisation iterates the hook's report, keeping the
permission-granted entries. The deep model is validated == the real callees
out-of-band by `axiom_check.py` (G-AX).

### 3.1 `select_applicable_editors` ↔ `ModelAdmin.get_inlines` (A-reference)
**Callee:** the new `ModelAdmin.get_inlines(self, request, obj)` whose body is
`return self.inlines` (`options.py:331-333` post-patch). The deep model pins its
default report to the configured collection in order
(`ToSeq(Result()) == ToSeq(self.configured)`). G-AX asserts
`list(admin.get_inlines(request, None)) == list(admin.inlines)` for a default
`ModelAdmin`.

### 3.2 `materialize_editors` ↔ `ModelAdmin.get_inline_instances` (A-reference)
**Callee:** `ModelAdmin.get_inline_instances(self, request, obj=None)`
(`options.py:583-594`). Post-patch source:

```python
def get_inline_instances(self, request, obj=None):
    inline_instances = []
    for inline_class in self.get_inlines(request, obj):   # <- the change
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

The loop iterates the **hook's report** (`self.get_inlines(request, obj)`), one
constructed editor per reported class, dropping (`continue`) a class whose
context grants none of the three permissions, and otherwise appending it (the
`max_num = 0` tweak does not affect class identity). This is exactly
`kept(reported, granted)`: the report filtered by the per-entry permission flag.
The discriminating change is the iteration SOURCE — the hook's report, not
`self.inlines`. G-AX asserts, for an `EpisodeAdmin` overriding `get_inlines` to
return narrowed subsets (the F2P scenario, with a MockSuperUser granting every
permission), that `[type(i) for i in admin.get_inline_instances(request)]`
equals exactly the hook's report, in order — and that this report differs from
the configured `inlines` (so the test genuinely exercises the override the
pre-patch code would ignore).

**Soundness check (G-AX):** `axiom_check.py` configures Django with an in-memory
sqlite database and a minimal generic-inline model set (the structural twin of
the test's `Episode`/`Media`/`GenericTabularInline`), then drives the real
`get_inlines` / `get_inline_instances` on the default admin and on the F2P
override scenario (empty / `[:1]` / `[1:2]` reports). Every observation matches
the deep model. It registers only apps that ship in the official image
(`contenttypes`/`auth`/`admin`; the test-model twins use
`app_label="contenttypes"`), so `django.setup()` succeeds with no bundle-local
package. It imports only Django itself (the module the patch lives in); nothing
test-private. Exit 0 iff sound, and emits `G-AX OK: … N observations`. A SKIP
(return 0) fires ONLY when `import django` itself raises `ImportError` (the
check run outside the container); a configuration/setup error is NOT swallowed
— it raises and the check exits non-zero. The orchestrator runs it in-container
with the gold patch applied (the base image has no `get_inlines`, so without
gold the check fails loud rather than passing vacuously).
The check is flag-independent: `get_inlines` / `get_inline_instances` behave
identically across backends; G-AX exercises the default `sqlite3` backend the
harness uses.
