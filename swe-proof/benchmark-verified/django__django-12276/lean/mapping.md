# mapping.md — django__django-12276

## Symbol binding (file:line @ base_commit 53d8646f799de7f92ab9defe9dc56c6125448102)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_useRequiredAttribute` / `problem_spec_useRequiredAttribute` | `FileInput.use_required_attribute` (the method ADDED by the patch) | `django/forms/widgets.py:374-388` (class `FileInput`); the new method is inserted after line 388 |
| `isHidden : Bool` | `self.is_hidden` | `django/forms/widgets.py:209-211` (`Widget.is_hidden` property) |
| `initialPresent : Bool` | truthiness of the `initial` argument (`bool(initial)`) | the `initial` parameter of `use_required_attribute(self, initial)` |
| (base rule, inlined) | `Widget.use_required_attribute(self, initial)` = `not self.is_hidden` | `django/forms/widgets.py:275-276` |

## What the function does (post-patch)

The patch adds `use_required_attribute` to `FileInput`:

```python
class FileInput(Input):
    input_type = 'file'
    ...
    def use_required_attribute(self, initial):
        return super().use_required_attribute(initial) and not initial
```

`super()` here is `Input` → `Widget`, whose `use_required_attribute` is:

```python
def use_required_attribute(self, initial):
    return not self.is_hidden
```

So the post-patch behavior of a file input is:

    use_required_attribute(initial) == (not self.is_hidden) and not initial

i.e. the element is marked required exactly when it is not hidden AND no (truthy)
initial value is present.

The patch ALSO removes the byte-identical `use_required_attribute` override from
`ClearableFileInput` (which subclasses `FileInput`). Since `ClearableFileInput`
now inherits the identical method from its new parent `FileInput`, its observable
behavior is UNCHANGED by the patch — the move is a pure refactor for that class.
The only newly-observable behavior is `FileInput.use_required_attribute`, which
the FAIL_TO_PASS tests pin:

- `test_fileinput.FileInputTest::test_use_required_attribute`:
  `widget.use_required_attribute(None)` is `True`;
  `widget.use_required_attribute('resume.txt')` is `False`.
- `test_forms.FormsTestCase::test_filefield_with_fileinput_required`: a
  `FileField(widget=FileInput)` renders with `required` when there is no initial,
  and without `required` when `initial={'file1': 'resume.txt'}`.

For a `FileInput`, `input_type == 'file'`, so `is_hidden` is `False`; the F2P
tests therefore exercise the `isHidden = false` slice, where the result reduces to
`not initial`. The spec keeps `isHidden` as a free input so the FULL base rule
(`not is_hidden`) is pinned, not just the `False` slice (frame discipline,
SPEC_GUIDE §0.5).

## Lean modeling

- `isHidden : Bool` ↔ `self.is_hidden` (a `bool` property). For `FileInput` it is
  always `False`, but it is modeled as a free Boolean so the unchanged base-rule
  component (`not is_hidden`) is pinned rather than left as a hole.
- `initialPresent : Bool` ↔ `bool(initial)`. Python's `and not initial` tests the
  truthiness of `initial` (a falsy `initial` — `None`, `''`, `False`, empty —
  does NOT suppress required; a truthy `initial` does). The Lean model abstracts
  `initial` to its truthiness, which is the only property the decision reads.
- `result : Bool` ↔ the method's `bool` return.
- The decision is modeled DEEPLY as the structural predicate
  `(!isHidden && !initialPresent)`; nothing is axiomatized.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `self.is_hidden` | `isHidden : Bool` | identity (`True ↔ true`) |
| `bool(initial)` | `initialPresent : Bool` | truthiness of `initial` |
| the method's `bool` return | `result : Bool` | identity |

## Callee provenance + flag dependencies

- **No consumed callee axiom and no A-reference.** The base rule
  (`super().use_required_attribute(initial)` = `not self.is_hidden`) is short and
  unchanged; it is inlined DEEPLY as the structural term `!isHidden` rather than
  axiomatized. SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled decision, and a
  dead axiom is forbidden by §0.7. So the `axioms` region is empty and **G-AX
  skips**.
- No flag dependencies: the decision reads only `self.is_hidden` and the
  truthiness of `initial`, both modeled as inputs.

## G-CONF fuzz seed

Pinned LCG seed: **12276** (see `conformance_check.py` `SEED`). The domain is the
finite product `Bool × Bool` (4 points); the fuzzer enumerates all four exhaustively
and additionally draws ≥1e5 random `(isHidden, initialPresent)` pairs, diffing the
R-shadow of `implementation_useRequiredAttribute` against an in-process replica of
the POST-PATCH decision `(not isHidden) and (not initialPresent)`.
