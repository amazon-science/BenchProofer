# mapping.md — sphinx-doc__sphinx-9281

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 8ec06e9a1bd862cd713b9db748e039ccc7b3e15b`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
provenance of the one deeply-modeled behaviour. There are **no consumed
axioms** in this bundle.

Repo file under change: `sphinx/util/inspect.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `objectDescription (obj : Obj)` | `object_description(object)` — `sphinx/util/inspect.py:433` (the dispatch body, lines 435–467 pre-patch) | the modeled changed function (value → display text) |
| `Obj` (inductive) | the *kind* of the value passed to `object_description` | spec carrier: the display-relevant shape of the rendered value (mapping.md §2) |
| `describe (o : Obj)` *(deep model — R/I, not an axiom)* | the patched `object_description` dispatch (`sphinx/util/inspect.py:433` post-patch) | pure spec: the desired rendering; deep model of the changed function, validated == the real renderer by `conformance_check.py` (G-CONF), NOT consumed as an axiom |

The pre-patch behaviour the change corrects (refinement audit only, not in the
consumer spec view): a member of an enumerated type fell through every
type-dispatch branch to the generic `repr()`-based fallback
(`sphinx/util/inspect.py:460-467`), yielding the verbose
`<ClassName.Member: value>` form instead of the concise `ClassName.Member`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the real repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| a value `object` that is a member of an enumerated type | `Obj.enumValue className memberName genericText` | `className` ↔ `object.__class__.__name__` (Python str ↔ Lean `String`); `memberName` ↔ `object.name`; `genericText` ↔ the generic fallback the value would otherwise get (carried but **not** observed on this leg — see below) |
| any other value `object` | `Obj.plain genericText` | `genericText` ↔ `object_description`'s pre-existing result for that value: the recursive container rendering (`dict`/`set`/`frozenset`) or the `repr()`/memory-address-strip/newline-replace fallback (`inspect.py:435-467`) |
| `object_description`'s returned `str` | Lean `String` | identity on character content; F2P `test_object_description_enum` compares the returned string exactly |
| Python `str` concatenation `"%s.%s" % (cn, mn)` | `cn ++ "." ++ mn` | `%s.%s` with two string substitutions ↔ `++ "." ++` (no `repr`/escaping applied to either operand — both are plain identifier strings) |

The model is an inductive `Obj` rather than a Python object because the only
distinction the changed behaviour draws is **"is this a member of an enumerated
type, or not"** — and, on the enumerated branch, the two strings that compose
the new label. Everything else about the value is folded into the opaque
`genericText` field, exactly the part of the behaviour the change leaves
untouched.

## 3. Behaviour provenance (deep model — checked by G-CONF)

### 3.1 `describe` deep model ↔ patched `object_description` (R/I)
**Operation under change:** `sphinx.util.inspect.object_description`. The
changed rendering is modeled **deeply** by `describe` (with `Obj`) in the `pure`
region; there is **no axiom** the proof consumes.

The patched dispatch (gold) is:

```python
def object_description(object):
    if isinstance(object, dict):     ...   # unchanged container leg
    elif isinstance(object, set):    ...   # unchanged container leg
    elif isinstance(object, frozenset): ... # unchanged container leg
    elif isinstance(object, enum.Enum):
        return "%s.%s" % (object.__class__.__name__, object.name)   # NEW
    try:
        s = repr(object)             ...   # unchanged generic fallback
    s = memory_address_re.sub('', s)
    return s.replace('\n', ' ')
```

Two facts make the inductive abstraction faithful:

1. **The container/fallback legs are unchanged.** The gold hunk only (a) turns
   the three sequential `if` checks into `elif` and (b) inserts the
   `enum.Enum` branch before the generic fallback. The `if`→`elif` rewrite is
   behaviour-neutral: `dict`, `set`, `frozenset`, and `enum.Enum` are mutually
   exclusive types, so at most one branch was ever taken; chaining them with
   `elif` cannot change which one fires. Hence the rendering of any value that
   is NOT a member of an enumerated type is byte-for-byte its pre-patch
   rendering — the `Obj.plain genericText` leg, where `genericText` is precisely
   that pre-existing result.
2. **The enumerated branch is the per-value structured label.** A member of an
   enumerated type renders as `"%s.%s" % (class name, member name)` — captured
   exactly by `Obj.enumValue className memberName _ ↦ className ++ "." ++
   memberName`. A bare enum member is not a `dict`/`set`/`frozenset`, so under
   both the old and new code it reaches this point; only the new branch changes
   its output. (An enum member nested *inside* a sortable container is rendered
   by the recursive call, which the G-CONF shadow reproduces — see below.)

**Soundness check (G-CONF):** `conformance_check.py` reproduces the unchanged
generic renderer (containers + repr/strip/newline) independently and the changed
enumerated branch, then differential-tests the whole `describe` shadow against
the real patched `object_description` over boundary cases (every member of four
sample enumerated types, the issue's own `ValueA = 10` example, container
boundaries, enum members nested in lists/dicts/sets) plus 100 000 randomized
fuzz values (scalars, nested containers, custom objects with address-bearing
reprs, and enum members). Imports only stdlib + the in-container `sphinx`. Exit
0 iff zero disagreements.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`9281`** so the
consumer-side verdict (§11.3) is reproducible. The shadow it builds
transliterates `describe`/`objectDescription` (all R/I-tagged ops) to Python;
there are no A-tagged callees to leave as a real callee (no axioms in this
bundle).
