# mapping.md — django__django-12276

Binds `Solution.lean` symbols to the repo at
`base_commit = 53d8646f799de7f92ab9defe9dc56c6125448102`.

Repo file under change: `django/forms/widgets.py`. The gold patch MOVES
`use_required_attribute` up from `ClearableFileInput` (`widgets.py:454-455` @
base) to its parent `FileInput` (inserted after `widgets.py:388`), with body
`return super().use_required_attribute(initial) and not initial`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `useRequiredAttribute (hasInitial : Bool)` | `FileInput.use_required_attribute(self, initial)` — inserted into `class FileInput(Input)` (`django/forms/widgets.py:374`) by the patch; body `return super().use_required_attribute(initial) and not initial` | the modeled (patched) method |
| `hasInitial` | the truthiness of the `initial` argument (`bool(initial)`) | "an existing value is already present for the field" |
| `inheritedRequiredDecision hasInitial` | `super().use_required_attribute(initial)` — i.e. `Widget.use_required_attribute(self, initial)` (`django/forms/widgets.py:275-276`) | the UNCHANGED inherited base decision |
| `out` | the method's return value (`bool`) | whether to advertise the `required` attribute |

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| `initial` : arbitrary Python value, used only via `not initial` (truthiness) | `Bool` `hasInitial` | `initial` truthy ↔ `hasInitial = true`; falsey/`None`/empty ↔ `hasInitial = false`. `not initial` ↔ `!hasInitial`. |
| `super().use_required_attribute(initial)` : `bool` | `inheritedRequiredDecision hasInitial : Bool` | exact (`True ↔ true`, `False ↔ false`); modeled OPAQUE — see §3 |
| return value : `bool` | `out : Bool` | exact |
| `x and y` (both bool) | `x && y` | short-circuit conjunction (no side effects; equivalent to `&&`) |

The model abstracts the per-value `initial` to its truthiness `hasInitial`,
because the patched body uses `initial` ONLY through `not initial`. The F2P
tests exercise exactly the truthy/falsey boundary: `use_required_attribute(None)`
→ `True`, `use_required_attribute('resume.txt')` → `False`.

## 3. Callee provenance — the inherited base decision (A-consumed, OPAQUE)

`super().use_required_attribute(initial)` for a `FileInput` resolves to the
GRANDPARENT `Widget.use_required_attribute` (`django/forms/widgets.py:275-276`):

```python
def use_required_attribute(self, initial):
    return not self.is_hidden
```

So for any visible (non-hidden) file input the inherited decision is `True`
regardless of `initial`. **However**, the spec does NOT claim this value. The
inherited callee is modeled as a fully OPAQUE free function
`opaque inheritedRequiredDecision : Bool → Bool` with NO asserted contract about
its return value. The spec pins only the STRUCTURE of the fix:
`out = inheritedRequiredDecision hasInitial && !hasInitial`.

Rationale (SPEC_GUIDE §0.7 — weakest contract): leaving the inherited decision
opaque is the weakest possible contract. Any real inherited implementation
(`Widget`'s `not self.is_hidden`, or a more refined ancestor) satisfies it
vacuously, because nothing is asserted about its value. There is therefore
NOTHING for an axiom_check to validate — **no `axiom_check.py`; G-AX skips.**

## 4. G-CONF fuzz seed

`conformance_check.py` seeds with **12276**. The inherited decision is treated as
a FREE boolean input `base` (since it is opaque/A-consumed); the testable I leg
is the `&& !hasInitial` conjunct. SHADOW = `base and (not has_initial)`; ORACLE =
the patched body `super().use_required_attribute(initial) and not initial` with
`base` standing for the inherited decision and `not has_initial` for
`not initial`. Exercised over all 2^2 = 4 combinations plus seeded fuzz.
