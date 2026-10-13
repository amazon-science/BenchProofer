# refinement.md — django__django-15572

The operation-by-operation correspondence between `model.py`'s implementation
(`collect_direct_locations` / `collect_provider_locations`, with the deep pure
models `is_present` / `join_base` / `selected_*` and the live `beneath_framework`
axiom) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses the axiom, and **A-reference**, where a deep model is validated ==
the real callee by axiom_check.py / G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

The gold patch makes one change at each of the two collection sites inside
`get_template_directories()` (`django/template/autoreload.py`): it inserts a
truthiness guard on the raw entry before that entry's location is joined and
collected.

## A. Site #1 — directly-declared entries (`collect_direct_locations`)

Gold hunk (`django/template/autoreload.py:20`):
```
- items.update(cwd / to_path(dir) for dir in backend.engine.dirs)
+ items.update(cwd / to_path(dir) for dir in backend.engine.dirs if dir)
```

| # | model.py impl op (`collect_direct_locations`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `entries: List[int]` | `for dir in backend.engine.dirs` | R | a directory entry `str`/`Path` ↔ an `int` token; the change observes only truthiness (mapping.md §2). |
| A2 | `d != 0` (the `if d != 0` guard) | `if dir` (the added guard) | R | `entry != 0` ↔ `bool(dir)`: the empty entry `""` is the only falsy DIRS value, modeled by the reserved token `0`; every present entry is truthy (mapping.md §2; validated by axiom_check.py: `bool("")` False, non-empty/`Path` truthy). |
| A3 | `join_base(d) == d` appended to `result` | `cwd / to_path(dir)` added to `items` | R / A-reference | the join is modeled deeply by `join_base`: the empty entry collapses to the base token `0` (the load-bearing universal `cwd / to_path("") == cwd`), and a present entry carries its own non-base token. G-AX validates the empty-entry collapse universally, and present-entry distinctness on the configured/tested entries (mapping.md §3.2). NOTE (scope): "present entry ⟹ distinct location" is asserted only on the tested entries, NOT as a universal over truthy strings — dot-paths (`"."`, `"./."`, `Path(".")`) are truthy yet collapse onto `cwd`; no tested input is a bare dot, and the refinement does not rely on the false universal. |
| A4 | order-preserving `List[int]` accumulation; postcondition `ToSeq(Result()) == selected_direct(ToSeq(entries))` | `items.update(<genexpr>)` into the result `set` | R | a `set` is order/duplicate-insensitive; the change only alters *which entries contribute*. Agreement on the emitted subsequence ⇒ agreement on the resulting set (mapping.md §2). |

## B. Site #2 — auxiliary-provider entries (`collect_provider_locations`)

Gold hunk (`django/template/autoreload.py:25-29`):
```
  items.update(
      cwd / to_path(directory)
      for directory in loader.get_dirs()
-     if not is_django_path(directory)
+     if directory and not is_django_path(directory)
  )
```

| # | model.py impl op (`collect_provider_locations`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `entries: List[int]` | `for directory in loader.get_dirs()` | R | as A1. |
| B2 | `d != 0` (the added conjunct of the guard) | `directory and ...` (the added conjunct) | R | as A2: `entry != 0` ↔ `bool(directory)`. This is the *only* operation the gold adds at this site. |
| B3 | `not beneath_framework(d)` (the pre-existing conjunct) | `not is_django_path(directory)` (the pre-existing filter) | A-consumed | `beneath_framework` axiomatizes the unchanged callee `is_django_path` (`django/utils/autoreload.py:54-56`). The proof consumes only that it is a *deterministic Boolean of the entry* (the axiom carries no value `Ensures`); G-AX confirms exactly that on the real callee (mapping.md §3.1). |
| B4 | `join_base(d)` appended; postcondition `ToSeq(Result()) == selected_provider(ToSeq(entries))` | `cwd / to_path(directory)` into `items` | R / A-reference | as A3/A4 (incl. the A3 scope note: present-entry distinctness is validated on the tested entries, not as a universal over truthy strings). |

The discriminating content of the change at BOTH sites is the truthiness guard
on the raw entry (A2 / B2). `model_prepatch.py` reverts BOTH guards (the full
pre-patch skeleton); `model_prepatch_direct.py` reverts only site #1 and
`model_prepatch_provider.py` reverts only site #2. Each fails its own site's
postcondition invariant (`ToSeq(result) == selected_direct/​provider(...)`) — the
spec independently senses each fixed behaviour (G-DIFF). On an entry list
containing the empty entry (token `0`), the unguarded impl appends
`join_base(0) == 0` (the base location) where the spec emits nothing, so the
invariant breaks — exactly the F2P scenario `DIRS: [""]`.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, A-reference, or I. The one operation that
genuinely *changed* — the truthiness guard on the entry before it contributes a
joined location — is modeled **deeply** (the `is_present` / `selected_*` filter
consumed in the two collect functions), not hidden behind an axiom about the
function under change. The only consumed axiom, `beneath_framework`
(**A-consumed**, site #2), covers the **unchanged** callee `is_django_path` that
the second site's pre-existing filter invokes; it constrains nothing the gold
changed. The empty-entry collapse `cwd / to_path("") == cwd` is the
**A-reference** that G-AX validates the deep `join_base` model against.

## D. verify(model) ⇒ resolved

`collect_direct_locations` / `collect_provider_locations` verify only if their
output equals the filtered-then-mapped subsequence that drops the empty entry
(A2/A3, B2/B4) — i.e. only if an empty entry contributes nothing while every
present entry contributes its joined location (which, on the configured/tested
entries, is a location distinct from the base — see the A3 scope note; this is
not claimed of arbitrary truthy dot-paths). By R (entry `str`/`Path` ↔
`int` token via truthiness; the `set` ↔ ordered subsequence; `cwd / to_path`
↔ `join_base`) the verified collectors equal the two gold comprehensions on the
tested inputs; by G-AX the deep `join_base`/`is_present` model matches the real
`pathlib`/`to_path` collapse behaviour — the empty-entry collapse
`cwd / to_path("") == cwd` validated universally, present-entry distinctness on
the configured/tested entries (A-reference; not claimed of arbitrary truthy
dot-paths) — and the real `is_django_path` meets the `beneath_framework` axiom it
stands in for (A-consumed). The F2P test asserts `get_template_directories() == set()` for
`DIRS: [""]`: the empty entry now contributes nothing, so the result is empty —
exactly what the verified spec pins. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and audited
callees — and the gold patch resolves (G-RESOLVE). The trust points are exactly
the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity (this
document, G-EQ).
