# mapping.md — django__django-12193

## Symbol binding (file:line @ base_commit 3fb7c12158a2402f0f80824f6778112071235803)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_buildInputContext` / `problem_spec_buildInputContext` / `correct_buildInputContext` | `CheckboxInput.get_context(self, name, value, attrs)` | `django/forms/widgets.py:521-525` |
| `dictSet` | in-place key assignment `d[k] = v` / spread `{**d, 'k': v}` on a `dict` | n/a (semantics of Python `dict`) |
| `mergeDict base extra` | `Widget.build_attrs(self, base_attrs, extra_attrs)` → `{**base_attrs, **(extra_attrs or {})}` | `django/forms/widgets.py:247-249` (`build_attrs`) — called by `Widget.get_context` (super) at `224-235` |
| `extraAfter checkTest attrs` | the `attrs` value handed to `super().get_context(...)` | `widgets.py:521-525` |

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | notes |
|---|---|---|
| `bool` result of `self.check_test(value)` | `checkTest : Bool` | the predicate result is supplied as an input (unchanged callee; see below) |
| `self.attrs` (the widget's own attribute dict) | `base : List (String × Bool)` | association list; key = attribute name, value-payload = Bool |
| caller-supplied `attrs` arg (a `dict` or `None`) | `attrs : Option (List (String × Bool))` | `None ↔ none`, `{...} ↔ some [...]` |
| Python `dict` | `List (String × Bool)` | insertion-ordered assoc list; last write wins per key (`dictSet`) |
| the produced `context['widget']['attrs']` | `result.contextAttrs : List (String × Bool)` | only the touched field of the context is modeled (§3) |
| the caller's `attrs` object **as observed after the call** | `result.callerAttrs : Option (List (String × Bool))` | models Python aliasing: a `dict` passed by reference is observed by the caller after the call |

### Why a Bool payload suffices (faithfulness)
Every observed value in the FAIL_TO_PASS / PASS_TO_PASS tests inspects the
attribute mapping only via the `'checked'` key and the *presence* of keys
(`test_get_context_does_not_mutate_attrs` uses `{'checked': False}`;
`test_checkbox_get_context_attrs` inspects `[{'checked': True}, {}]`). Tracking
each attribute name with a Boolean payload faithfully captures all observed
behavior; string-valued attributes are never differentiated by the tests.

### Modeling the caller-visible `attrs` (the aliasing point)
Lean is referentially transparent, so the in-place dict mutation that this fix
removes cannot arise spontaneously. The Python caller passes a `dict` *by
reference*; whether that object is observed mutated after the call is the entire
behavioral difference. We therefore expose the caller-visible attribute object as
an explicit output component `result.callerAttrs`. The post-patch (correct) code
rebinds its local name to a fresh dict, so the caller's object is untouched
(`callerAttrs = attrs`). The pre-patch code mutates the shared object in place, so
the caller observes the `'checked'` write (`callerAttrs ≠ attrs`).

## Callee provenance + flag deps
- `self.check_test(value)` — UNCHANGED callee; the patch does not touch it. Its
  Boolean result is modeled as the input `checkTest`. No opaque/axiom needed.
- `build_attrs` / `Widget.get_context` (super) — UNCHANGED callees; their
  `{**base, **extra}` merge is modeled deeply as `mergeDict` (A-reference, no
  consumed axiom). No flag dependencies.

## G-CONF fuzz seed
`conf_seed = 20240627` (pinned in meta.json).
