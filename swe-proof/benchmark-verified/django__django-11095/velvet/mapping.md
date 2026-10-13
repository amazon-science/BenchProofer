# mapping.md — django__django-11095

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 7d49ad76562e8c0597a0eb66046ab423b12888d8`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of every callee folded into a free input.

Repo file under change: `django/contrib/admin/options.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `getInlines (declared : List InlineClass)` | NEW `ModelAdmin.get_inlines(self, request, obj)` — `django/contrib/admin/options.py:330` (post-patch) | the added selection hook; default returns `self.inlines` |
| `getInlineInstances (selected …) (declared …) (admissible …)` | `ModelAdmin.get_inline_instances(self, request, obj=None)` — `django/contrib/admin/options.py:585` (body line 587, the `for inline_class in …` loop at 588) | the modeled changed function (inline-instance builder) |
| `kept (admissible) (selected)` | the build loop body: instantiate each selected class and keep it iff the access-control disjunction holds | pure spec: the admissible sublist of the iterated sequence, in order |
| `InlineClass` | an entry of the iterated inline-class sequence (`self.inlines` element / hook return element) | opaque registration identity (only its identity/order is observable) |

The pre-patch repo line the change replaces (refinement audit only, not in the
consumer spec view): `for inline_class in self.inlines:`
(`django/contrib/admin/options.py:588` @ base_commit).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| the iterated sequence of inline classes (`self.inlines` tuple, or the hook return — a tuple/list of `InlineModelAdmin` subclasses) | `List InlineClass` | a Python class object ↔ an `InlineClass` with a distinct `id`; tuple/list order ↔ `List` order; `len` ↔ `.length`; empty ↔ `[]`. Only class identity & order are observed (the F2P test inspects `type(instances[i])` and list length). |
| `self.inlines` (the statically declared registration tuple) | `declared : List InlineClass` | the default hook return; the value iterated PRE-patch |
| `get_inlines(request, obj)` return (the per-request/per-object selection) | `selected : List InlineClass` | the value iterated POST-patch; equals `declared` when the hook is not overridden |
| the unchanged per-inline keep decision — `inline.has_view_or_change_permission(request, obj) or inline.has_add_permission(request, obj) or inline.has_delete_permission(request, obj)` (truthy request); always-keep for falsy request | `admissible : InlineClass → Bool` | a total free predicate "this inline survives the unchanged access-control disjunction for this request/obj". Unchanged by the patch; abstracted as a free input with no relied-on property. |
| `inline = inline_class(self.model, self.admin_site)` instantiation; `inline.max_num = 0` when add denied | identity on `InlineClass` (omitted) | unchanged by the patch; the instance's CLASS is what the F2P test observes, and `max_num` does not alter list membership. Identity on the carrier. |

`request` truthiness and `obj` are unchanged inputs that only parameterise
`admissible`; they are not separately modeled.

## 3. Callee provenance (all UNCHANGED — abstracted as free inputs, no G-AX)

The patch introduces no new behaviour in any callee; it only redirects the
iterated source from `self.inlines` to the new `get_inlines` hook. The callees
the loop body invokes —

  * `inline_class(self.model, self.admin_site)` (inline construction),
  * `inline.has_view_or_change_permission`, `inline.has_add_permission`,
    `inline.has_delete_permission` (the keep disjunction),
  * the `inline.max_num = 0` assignment,

— are **identical pre- and post-patch**. They select WHETHER an admitted
registration is kept, not WHICH registrations are iterated, so they are folded
into the free predicate `admissible` with **no relied-on property**. The new
`get_inlines` hook's default body (`return self.inlines`) is modeled exactly by
`getInlines`' `ensures out = declared`; an override is modeled by letting
`selected ≠ declared`. Because every callee is unchanged and no axiom pins any
of their behaviour, there is **nothing to validate against a real callee** —
G-AX is not applicable (no `axiom_check.py`; `meta.json gates.G-AX = skip`).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`11095`** so the
consumer-side verdict (§11.3) is reproducible. The SHADOW transliterates the
`kept` fold over `selected`; the ORACLE transliterates the patched
`get_inline_instances` build loop (iterating `selected`, the hook return) with
the unchanged per-inline keep decision folded into `admissible`. They are
differential-tested over the override scenarios the F2P test exercises (hook
returns `[]`, a sublist, a reordering, or classes outside `declared`) plus
seeded fuzz of the selection list and admissibility mask.
