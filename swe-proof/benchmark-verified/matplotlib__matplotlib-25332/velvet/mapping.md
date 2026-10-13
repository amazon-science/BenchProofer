# mapping.md — matplotlib__matplotlib-25332

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 66ba515e671638971bd11a34cff12c107a437e0b`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
callee provenance.

Repo file under change: `lib/matplotlib/cbook.py` (class `Grouper`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `snapshot (mapping : List (Ref × List Ref))` | `Grouper.__getstate__(self)` — added by the patch at `lib/matplotlib/cbook.py:790` (the line after `__init__`, body line 791) | modeled changed function #1: the serialisable snapshot taken before the registry is written out |
| `rebuild (state : List (Ref × List Ref))` | `Grouper.__setstate__(self, state)` — added by the patch at `lib/matplotlib/cbook.py:797` | modeled changed function #2: the live table rebuilt when the registry is read back |
| `strongifyMap` / `strongifyEntry` / `strongify` | the dict comprehension `{k(): [v() for v in vs] for k, vs in self._mapping.items()}` inside `__getstate__` | pure spec: per-reference weak→strong conversion over every row, its representative key and every member of its group |
| `weakenMap` / `weakenEntry` / `weaken` | the dict comprehension `{weakref.ref(k): [*map(weakref.ref, vs)] for k, vs in self._mapping.items()}` inside `__setstate__` | pure spec: per-reference strong→weak conversion over every row |
| `Ref { target, weak }` | one entry of `self._mapping` viewed as a `(referent-identity, is-weakref?)` pair | the touched field of a `weakref.ref` / strong object: which object it points at, and whether it is a (non-serialisable) live weak reference or a (serialisable) plain strong one |

There are **no axioms and no A-reference deep-model callees** in this bundle:
both changed functions are modeled directly; neither calls an *unchanged*
foreign callee whose contract the proof must assume. `weakref.ref`/`obj()` are
not modeled as callees — they ARE the per-reference `weak`-flag flip the model
spells out (`strongify`/`weaken`). See §3.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1, `conformance_check.py`) uses to translate values
between the Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self._mapping : dict` — an *ordered* dict from a representative key to its group list | `List (Ref × List Ref)` | `list(d.items())` ↔ the `List` (insertion order preserved on both sides — `__getstate__`/`__setstate__` are order-preserving dict comprehensions, `strongifyMap`/`weakenMap` are order-preserving folds); `len(d)` ↔ `.length` |
| a `weakref.ref(x)` (live weak reference) | `Ref { target := id(x), weak := true }` | a weak reference ↔ a `Ref` with `weak = true`; its referent identity `id(x)` ↔ `target` |
| a dereferenced strong object `x` (as stored by `__getstate__`) | `Ref { target := id(x), weak := false }` | a strong reference ↔ a `Ref` with `weak = false`; `id(x)` ↔ `target` |
| object identity `id(x)` | `Int` (`target`) | distinct live objects ↔ distinct `target` values; the model tracks *which object* a reference points at, the only content `align_*` / the F2P pickle round-trip observes |

The model abstracts a `weakref.ref` / strong object down to *(which object,
weak-or-strong)* — the two facts the pickle round-trip turns on. The group
*structure* (disjoint sets) is carried verbatim as the `List (Ref × List Ref)`;
the per-row transform is independent of set-sharing, exactly as both dict
comprehensions are.

## 3. Callee provenance — none consumed, none deep-referenced

The changed operation in each function is a **per-reference flip** between the
weak and strong forms of a reference, applied to a row's representative and to
every member of its group. It is modeled **deeply** by `strongify`/`weaken`
(single reference), `strongifyEntry`/`weakenEntry` (one row), and
`strongifyMap`/`weakenMap` (the whole table) in the `pure` region — there is no
`axiom` and no A-reference. The Python primitives the patch uses for the flip
(`weakref.ref(·)` to go strong→weak, `·()` to go weak→strong) are not unchanged
foreign callees whose behaviour the proof assumes; they are the *content of the
change itself*, spelled out by the model. Hence:

- **No consumed axioms** (no `axiom` in `Solution.lean`).
- **No A-reference deep models** (no unchanged callee is deep-modeled).
- **G-AX is not applicable / skipped.** There is no `axiom_check.py`: G-AX runs
  the image at `base_commit`, where `Grouper` has **no** `__getstate__` /
  `__setstate__` (they are *added* by the patch), so there is no unchanged real
  callee to validate a contract against. The soundness of the deep models is
  instead established by G-CONF against the *patched* repo (§4), which is the
  appropriate gate for a deeply-modeled changed function (refinement.md §C/§D).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`25332`** so the
consumer-side verdict (§11.3) is reproducible. It runs **in the patched
container** (the harness git-applies `patch.diff` first, `apply_gold=True`):

- **ORACLE** — the real patched `Grouper.__getstate__` (for `snapshot`) and
  `Grouper.__setstate__` (for `rebuild`), exercised on randomly-constructed
  reference tables.
- **SHADOW** — the R/I transliteration of the impl regions: `strongifyMap`
  (snapshot) and `weakenMap` (rebuild), built over the `List (Ref × List Ref)`
  carrier via the §2 bijection.

It asserts the SHADOW equals the ORACLE — as *(target-identity, weak-flag)*
tuples per row — on every fuzzed table (≥10⁵ inputs). Exit 0 iff zero
disagreements. `conf_skip = false` (the impl regions are entirely R/I content).
Imports only stdlib (`weakref`, `random`) plus the repo's own
`matplotlib.cbook.Grouper`.
