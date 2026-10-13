# mapping.md — sympy__sympy-12481

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = c807dfe7569692cad24f02a08477b70c1679a4dd`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each modeled callee.

Repo file under change: `sympy/combinatorics/permutations.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildExplicitForm (entries) (grouped)` | `Permutation.__new__` — `permutations.py:801`, body `:884–929` | the modeled changed function, over BOTH readings of its argument (see §3) |
| `grouped` | `is_cycle = args and is_sequence(args[0])` — `:886` | which reading the argument is taken in; a FREE Bool here, exactly as `is_cycle` is a computed value there, not an assumption |
| `entries` | `args` after `args = list(args[0])` (`:884`) and the per-reading coercion `:887–888` (grouped) / `:889–890` (flat) | the argument list; `List (List Nat)` carries both readings (see §2) |
| `entries.flatten` | `temp = flatten(args)` — `sympy/utilities/iterables.py:22`, called at `:897`; and `aform = list(args)` at `:919` | flatten the argument to one list of points; for a list of lists this is concatenation (I) |
| `pointsDistinct (temp)` | `not has_dups(temp)` — `has_dups` at `sympy/utilities/iterables.py:1651`, called at `:898` | the repeated-point test on the flattened argument, in positive form; UNCHANGED callee, transliterated concretely (I) |
| `rangeCovered (temp)` | `any(i not in temp for i in range(len(temp)))` over `temp = set(temp)` — `:904`, `:906–907` | the coverage test, in positive form: no gap below the count of DISTINCT points. `l.dedup.length` ↔ `len(set(temp))` |
| `explicitForm (l)` | the conjunction of the two screens above, i.e. the condition under which `:919`'s `aform = list(args)` is reached at all | pure spec: `l` already IS an explicit list form — each point below its own count named exactly once |
| `arrayForm (entries)` *(deep model — A-reference)* | the composition block `c = Cycle(); for ci in args: c = c(*ci); aform = c.list()` — `:911–917`, i.e. `Cycle.__call__` (`:316`) + `Cycle.list` (`:344`) | pure spec: the explicit array form of the groups composed left-to-right; UNCHANGED by the patch; validated `arrayForm == real composition` by axiom_check.py (G-AX) |
| `composePoint` / `cycleStep` / `succInCycle` | the per-point action of `Cycle.__call__`'s dict wiring (`:306–342`) | pure helpers that spell out the composite mapping deep model |
| `eachValid entries` *(the one precondition, guarded by `grouped = true`)* | the invariant established before `:897` on the grouped reading: each group is a list of unique ints (`Cycle.__init__` raises `All elements must be unique in a cycle.`, `:451`) and the whole argument names at least one point (`Cycle.list` raises `must give size for empty Cycle`, `:371`) | frames the grouped reading only; the flat reading is UNFRAMED (§3) |
| `Except.error ()` | any `raise ValueError(...)` reached from this body (`:900`, `:903`, `:908`) | refusal; the Unit payload abstracts the message text (§2) |

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the Lean
value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `args` on the GROUPED reading = a list of lists of non-negative ints (`:887–888`: `args = [[int(i) for i in c] for c in args]`) | `entries : List (List Nat)` with `grouped = true` | the `j`-th group `args[j]` ↔ `entries[j]`; `int ≥ 0` ↔ `Nat`; `len` ↔ `.length`; `[]` ↔ `[]` |
| `args` on the FLAT reading = a list of non-negative ints (`:889–890`: `args = [int(i) for i in args]`) | `entries : List (List Nat)` with `grouped = false`, read through `entries.flatten` | the flat point list `args` ↔ `entries.flatten`. ANY `entries` with the same flatten denotes the same real argument; the canonical representative is the one-group encoding `[args]`, which is what conformance_check.py feeds the oracle. Sound because both consumers of the flat argument — the two screens at `:897–909` and the returned `aform = list(args)` at `:919` — depend on the flattened points ALONE, so a fiber of `entries` is behaviourally indistinguishable |
| `is_cycle` (`:886`) — computed from the argument's shape | `grouped : Bool` | `True` ↔ `true`, `False` ↔ `false`. FREE: both values are in the contracted domain, and the model does not assume which one holds |
| the constructed permutation's `_array_form` (`:927`), a `list[int]` | `List Nat` inside `Except.ok` | `aform[i]` ↔ `result.ok[i]`; both are 0-based images of `i` |
| `raise ValueError(...)` (`:900`, `:903`, `:908`) | `Except.error ()` | any raised `ValueError` from this body ↔ `.error ()`; successful construction ↔ `.ok aform`. The unit payload abstracts the message text, which no test observes: the retained assertions are `raises(ValueError, lambda: ...)` and the added one is an equality between constructed permutations |

`Nat` (vs `Int`) is faithful on both readings: each element is coerced with
`int(i)` and a negative point is rejected upstream — by `Cycle.__init__`
(`negative integers are not allowed in a cycle.`, `:449`) on the grouped reading,
and by the coverage screen on the flat one (a negative entry makes some `i` in
`range(len(temp))` absent, so `:908` raises). So the points reaching either answer
are always `≥ 0`.

## 3. Scope of the modeled function — BOTH readings

The patch changes exactly one screen:

```
         temp = flatten(args)
-        if has_dups(temp):
-            if is_cycle:  raise ValueError('there were repeated elements; ...')
-            else:         raise ValueError('there were repeated elements.')
+        if has_dups(temp) and not is_cycle:
+            raise ValueError('there were repeated elements.')
         temp = set(temp)
```

Behavioral delta: a point repeated in the flattened argument used to be refused
under either reading; it is now refused only under the FLAT reading, and the
grouped reading composes the groups instead. The delta is therefore a statement
about the RELATION between the two readings, and a model that fixes the reading
cannot express it: with `grouped` pinned to `true` by a precondition, the added
`and not is_cycle` conjunct is dead, and an implementation that refuses nothing at
all on the flat reading satisfies the contract while failing the official test
(`raises(ValueError, lambda: Permutation([1, 1, 0]))` is RETAINED by the test
patch). So `grouped` is a free Bool here and the contract pins both readings:

* `grouped = true` → the result is `Except.ok (arrayForm entries)`: success is
  demanded (no refusal for a shared point) and the value is the left-to-right
  composite. Frames: `eachValid entries`.
* `grouped = false` → the result is `Except.ok entries.flatten` when
  `explicitForm entries.flatten` holds, and `Except.error ()` when it does not.
  No frame at all: every flat argument is specified.

`eachValid entries` (`entries.flatten ≠ [] ∧ ∀ c ∈ entries, c.Nodup`) is the
weakest frame that keeps the grouped reading inside the modeled body: a group
repeating a point internally raises earlier in the unchanged `Cycle.__init__`
(`:451`), and an argument naming no point at all raises in the unchanged
`Cycle.list` (`:371`). Both are unchanged by the patch. Note it does NOT require
each group to be non-empty: `Permutation([[0, 1], []])` really does construct
`[1, 0]` (the empty group is the identity factor), so requiring non-emptiness
would have excluded live inputs. Measured on the patched repo; asserted by
axiom_check.py's boundary set.

DECLARED FRAME (outside the model): the `size=` keyword and the extension at
`:920–924`. `Permutation.__new__` takes `size` as a keyword argument; the model
has no counterpart binder and so describes the `size is None` behaviour, which is
what every assertion in the F2P/P2P set that reaches this body exercises except
`raises(ValueError, lambda: Permutation([4, 5], size=10))` — and that one is
refused by the coverage screen at `:906–909`, BEFORE `size` is consulted, so the
model's `grouped = false → explicitForm [4,5] = false → Except.error ()` covers
it. The `size` extension is unreachable-before-refusal there and unchanged by the
patch everywhere else.

## 4. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 4.1 `arrayForm` deep model ↔ the `Cycle()`-composition block (A-reference)

**Callee:** the UNCHANGED block `c = Cycle(); for ci in args: c = c(*ci);
aform = c.list()` (`:911–917`), i.e. `Cycle.__call__` composing groups
left-to-right then `Cycle.list()` rendering the array form. The patch does not
touch it. It is modeled **deeply** by `arrayForm`/`composePoint`; there is **no
consumed axiom**. `Cycle.__call__` processes its dict right-to-left per call but
the *fold over groups* `c = c(*ci)` applies groups left-to-right, which is what
`composePoint` (head group first) encodes — confirmed against real sympy on the
boundary + fuzz set.

**Soundness check (G-AX):** `axiom_check.py` runs the real UNCHANGED composition
block **directly** on boundary cases (disjoint, non-disjoint, singletons, nested
overlaps, empty groups beside non-empty ones, points that skip 0, the
discriminator `[[0,1],[0,2]]`) plus 20 000 randomized fuzz inputs of valid grouped
form, asserting `arrayForm(entries) == aform`. stdlib + sympy only. Exit 0 iff
sound.

**Why the real callee is invoked directly, NOT via `Permutation([...])`
(directive 7):** the A-reference models an *unchanged* callee, so it must be
validated against that callee directly. `Permutation([list(c) for c in entries])`
would route through `Permutation.__new__` — the FUNCTION UNDER CHANGE — whose
*pre-patch* screen raises `ValueError` on exactly the shared-point inputs this
patch legalizes. G-AX runs against the BASE (pre-patch) repo, so that route
falsely fails on the discriminating witness. The `Cycle()`-composition block is
untouched by the patch and yields the same array form on base and patched repos,
so checking it directly is both sound and stable.

### 4.2 The flat reading consumes no callee

`aform = list(args)` (`:919`) is a copy of the already-flat argument, tagged I
against `entries.flatten`. There is nothing for G-AX to validate there, and
axiom_check.py does not mention it.

## 5. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds `random.Random` with **`12481`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
both screens, the deep model `arrayForm` (`composePoint`/`cycleStep`), and the
flat reading's identity answer to Python, and diffs the resulting
`(error | ok list)` against the gold-patched constructor's behavior (raises ↔
error; `.array_form` ↔ ok list) over 50 000 fuzzed Requires-satisfying grouped
arguments PLUS 50 000 unconstrained flat arguments (10⁵ overall, both readings).
The oracle call follows the repo's own dispatch: a list of lists for the grouped
reading, a flat list of ints for the other, so `is_cycle` at `:886` computes the
reading under test rather than being asserted.
