# mapping.md — django__django-16877

## Symbol binding (file:line @ base_commit 98f6ada0e2058d67d91fb6c16482411ec2ca0967)

Modeled function: the `escapeseq` filter ADDED to
`django/template/defaultfilters.py` by the gold patch (inserted immediately after
`escape_filter` at `defaultfilters.py:440-444`):

```python
@register.filter(is_safe=True)
def escapeseq(value):
    return [conditional_escape(obj) for obj in value]
```

The per-element escaper `conditional_escape` is UNCHANGED by the patch,
`django/utils/html.py:82-94`:

```python
def conditional_escape(text):
    if isinstance(text, Promise):
        text = str(text)
    if hasattr(text, "__html__"):
        return text.__html__()
    else:
        return escape(text)
```

i.e. it returns content already marked safe (anything carrying `__html__`, e.g. a
`SafeString`) untouched, and otherwise HTML-escapes ordinary text via
`escape` (`html.py:18-27`).

Lean modeled function name: `escapeEach` (names the *behavior* — escaping each
element of a sequence individually — not a patched repo symbol; `escapeseq` /
`conditional_escape` are not echoed; see G-LEAK note below).

| Lean symbol | Python binding (file:line @ base_commit) |
|---|---|
| `escapeEach` (modeled behavior) | `escapeseq(value)`, the filter ADDED at `defaultfilters.py:447-453` (post-patch) |
| `value : List Elem` | `value` — the input sequence the filter iterates |
| `obj : Elem` | `obj` — one element of the sequence |
| `obj.isSafe : Bool` | whether `obj` is already marked safe-for-HTML (`hasattr(obj, "__html__")`, true for `SafeString`/`mark_safe(...)`) — the only structural attribute `conditional_escape` branches on |
| `obj.text : String` | the underlying text of `obj` (the `str` content) |
| `condEscape : Elem → String` (opaque, A-reference) | `conditional_escape(obj)`, `html.py:82-94` (UNCHANGED by the patch) |
| `result : List String` | the returned `list[str]` (each element a `str`/`SafeString`) |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)

| Python | Lean |
|---|---|
| the input sequence `value` (an iterable of strings, some marked safe) | `value : List Elem` |
| one element `obj`, observed via `hasattr(obj, "__html__")` and its `str` content | `Elem { isSafe : Bool, text : String }` |
| `obj` is a `SafeString`/`mark_safe(...)` value | `obj.isSafe = true` |
| `obj` is an ordinary `str` | `obj.isSafe = false`, `obj.text = obj` |
| `conditional_escape(obj)` (a `str`/`SafeString`) | `condEscape obj : String` |
| `[conditional_escape(obj) for obj in value]` (a `list[str]`) | `value.map condEscape : List String` |

### Modeling notes
- **`Elem` is the observation interface, not the full string object.** The
  per-element escaper `conditional_escape` inspects `obj` through exactly two
  observables: whether it carries `__html__` (already-safe), and its `str`
  content. `Elem` carries precisely those two fields (SPEC_GUIDE §2 "rich object →
  structure with only the touched fields"). `condEscape : Elem → String` is the
  faithful element-wise escaper over that interface.
- **`condEscape` is an A-reference, not a consumed axiom.** `conditional_escape`
  is an UNCHANGED callee the new filter applies to each element. The spec pins
  each result entry to `condEscape obj` (frame discipline: every entry is fixed,
  none left free) but the proof consumes NO property of `condEscape` (it closes by
  a loop-fold induction `implementation_escapeEach value = value.map condEscape`).
  So it is referenced (G-AX validates the model == real `conditional_escape`)
  rather than axiomatized. No `condEscape_prop` axiom is needed.
- **The added behavior is the element-wise map itself.** The patch's only new
  behavior is applying the existing per-element escaper to every element of a
  sequence, in order, returning the list. The spec pins length (one entry per
  element), order, and each entry's value (`value.map condEscape`).

### G-LEAK note
The solver-visible `problem_statement` is: "New template filter `escapeseq`…
provide a new template filter escapeseq which would be to escape what safeseq is
to safe… `{{ some_list|escapeseq|join:"," }}` where each item of some_list is
escaped before applying the join operation. This usage makes sense in a context
where autoescape is off." The terms *escape*, *filter*, *sequence/list*, *each
item escaped*, and *join* are public there. The Lean identifiers nonetheless
avoid echoing the patched repo symbols (`escapeseq`, `conditional_escape`); the
spec view names no file/line and does not narrate the edit (it states the desired
behavior — escape each element of a sequence individually — not "a filter was
added").

## G-CONF fuzz seed
Pinned seed: **16877** (also in `conformance_check.py`).
