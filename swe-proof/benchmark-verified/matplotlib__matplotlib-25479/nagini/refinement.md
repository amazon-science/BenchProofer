# refinement.md — matplotlib__matplotlib-25479

The operation-by-operation correspondence between `model.py`'s implementations
(`colormaps_equal`, `register_named`, and the `Cmap` constructor that models
`copy()`) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** (the proof uses an axiom's `Ensures`),
**A-reference** (a deep model validated == the real callee by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE). It is a two-site change; the two sites
are independently fixed behaviours, each with its own failing prepatch model.

## A. The equality site — `Colormap.__eq__` (`lib/matplotlib/colors.py:776`)

Gold hunk:
```
-        if (not isinstance(other, Colormap) or self.name != other.name or
+        if (not isinstance(other, Colormap) or
                 self.colorbar_extend != other.colorbar_extend):
             return False
```
i.e. the `self.name != other.name` disjunct is removed; equality becomes
"is-a-Colormap AND equal colorbar_extend AND equal lookup tables".

Modeled by `colormaps_equal` (and the `seq_eq` deep model). Prepatch:
`model_prepatch_eq.py`.

| # | model.py impl op (`colormaps_equal`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `self, other : Cmap` | `self, other` Colormaps; the `not isinstance(other, Colormap)` guard | R + I | both operands typed as the modeled object; the `isinstance` guard for a `Colormap`-typed `other` is the identity-true case the F2P tests exercise (mapping.md §2). |
| A2 | `if self.colorbar_extend != other.colorbar_extend: return False` | `self.colorbar_extend != other.colorbar_extend` disjunct | R + I | identical comparison and early `False`. The refinement is in the carrier: this attribute ranges over SIX mutually distinguishable values (`False`, `True`, `'neither'`, `'min'`, `'max'`, `'both'` — see mapping.md §2), all publicly reachable, and with equal tables the real comparison separates all 15 distinct pairs. It is observed through `==`/`!=` only, so the model carries it as an `int` token under an injection over the whole domain; a two-valued carrier would merge four of the six values and predict equality where the real comparison reports inequality. |
| A3 | label NOT consulted (no `self.name`/`other.name` comparison gates the result) | the REMOVED `self.name != other.name` disjunct | I | the fix is exactly the absence of a label comparison; the model's postcondition `Result() == (colorbar_extend-equal AND seq_eq(lut,lut))` names no label term — the discriminating content of the change. |
| A4 | the lookup-table content comparison (`seq_eq(ToSeq(self.lut), ToSeq(other.lut))`, computed by the length-then-elementwise loop) | `np.array_equal(self._lut, other._lut)` | A-reference | the table comparison is modelled **deeply** (`seq_eq`, a front-recursive fold over the entries; no consumed axiom). G-AX validates that the real `Colormap.__eq__` agrees with the model predicate over boundary + 4000 fuzz pairs (mapping.md §3.1). |
| A5 | the ENTRY relation the fold applies, `entry_eq(x, y)` | the elementwise `==` that `np.array_equal` folds (`colors.py:785`), on `float64` rows | A-reference | `np.array_equal` at its default settings reduces to `bool((a1 == a2).all())`, so the relation supplied per entry is float `==`, not identity. An entry holding an indeterminate float value therefore compares unequal to EVERY entry, including one holding that same value: the relation is **not reflexive**, and a table carrying such an entry is equal to no table, not even to itself. `entry_eq` states exactly this (equal tokens AND determinate), which is what the real callee guarantees rather than what an idealised content-identity would. Reachable through public API (`with_extremes(bad=...)`, `set_bad`, a supplied colour row). G-AX asserts the non-reflexivity against the real callee directly; G-CONF shadows it on both the determinate and the indeterminate side. |

The discriminating content — *the label is irrelevant to equality* — lives in
A3: the model's postcondition omits any label term. `model_prepatch_eq.py`
re-introduces the pre-patch `if self.name != other.name: return False` and
**fails** the postcondition `Result() == (colorbar_extend-equal AND
seq_eq(lut,lut))` for a relabelled-but-content-equal pair (the bug; G-DIFF).

## B. The registration site — `ColormapRegistry.register` (`lib/matplotlib/cm.py:148`)

Gold hunk (added after `self._cmaps[name] = cmap.copy()`):
```
+        # Someone may set the extremes of a builtin colormap and want to register it
+        # with a different name for future lookups. The object would still have the
+        # builtin name, so we should update it to the registered name
+        if self._cmaps[name].name != name:
+            self._cmaps[name].name = name
```

Modeled by `register_named` (and the `Cmap` constructor modelling `copy()`).
Prepatch: `model_prepatch_register.py`.

| # | model.py impl op (`register_named`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `reg : Dict[int, Cmap]`, `name : int`, `cmap : Cmap` | `self._cmaps : dict[str, Colormap]`, the `name` keyword, the `cmap` argument | R | registry store as `Dict[int, Cmap]`; label as `int` token (mapping.md §2). |
| B2 | `snapshot = Cmap(cmap.name, cmap.colorbar_extend, cmap.lut)` (fresh object, copied content) | `cmap.copy()` | A-reference | the independent-snapshot primitive (`copy()` → `__copy__`, a fresh object with deep-copied `_lut`) is modelled deeply by the `Cmap` constructor (fresh object, fresh `lut` list with equal token contents, fresh flag token). What `copy()` guarantees is **bitwise** reproduction of the stored rows, which holds for an indeterminate entry too — a different question from the `==`-relation of A5, which is why the snapshot-fidelity oracles compare tables with `equal_nan=True` while the equality oracle leaves it at the default. G-AX validates `register` stores an independent snapshot (`returned is not cmap`) carrying the supplied content, over the whole flag domain and over indeterminate tables (mapping.md §3.2). |
| B3 | `snapshot.name = name` | `if self._cmaps[name].name != name: self._cmaps[name].name = name` | I | assigning the stored snapshot's label to the registration label. The model assigns unconditionally; the patch guards with `!= name` — observationally identical (assigning `name` when already `name` is a no-op), so the post-state `reg[name].name == name` is the same. The discriminating content of the change. |
| B4 | `reg[name] = snapshot` | `self._cmaps[name] = cmap.copy()` | I + R | storing the snapshot under the label key (R for the `int`-key store). The patch stores then relabels in place; the model relabels then stores — same post-state (`reg[name].name == name`, content preserved), since `name` is the unique reference written. |
| B5 | `cmap` left unmodified (read-only at fractional permission; `Ensures(cmap.name == Old(cmap.name))`) | `cmap` is only `.copy()`'d, never mutated | I | the supplied mapping is untouched; the relabel acts on the stored copy. The fractional-permission read-only contract forbids any verifying impl from mutating `cmap` to satisfy the postcondition. |
| B6 | registry frame clauses: `Forall k != name: (k in reg) == Old(k in reg)` and `Forall k != name, Old(k in reg): reg[k] is Old(reg[k])` | `register` writes exactly ONE store key: `self._cmaps[name] = cmap.copy()` (plus the in-place relabel of that same stored object); no other `_cmaps` entry is read-written | I | the real registration touches only the chosen label's slot — every other registered colormap keeps its membership and its exact bound object. These clauses pin that single-key-write shape: an implementation that additionally clobbers or drops any OTHER registry entry (e.g. rebinding a builtin like `plasma`/`viridis` to the new snapshot, which breaks the hidden `test_double_register_builtin_cmap` / `test_colormap_invalid` behaviour) cannot verify. |

The discriminating content — *the stored snapshot's own label is the
registration label, not the supplied label* — lives in B3:
`reg[name].name == name` holds even when `cmap.name != name`.
`model_prepatch_register.py` drops the `snapshot.name = name` step and **fails**
the postcondition `reg[name].name == name` (the bug; G-DIFF).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The two operations that genuinely
*changed* are modelled **deeply**:
* the label-free equality is spelled out as the postcondition predicate + the
  `seq_eq` fold over `entry_eq` (A3/A4/A5), with the real `__eq__` as the
  A-reference G-AX validates against — there is no consumed `__eq__` axiom. Both
  legs of that predicate state what the real callee guarantees rather than an
  idealised version of it: the flag over its full value domain (A2), and the
  entry relation with the non-reflexivity the float fold actually has (A5);
* the snapshot relabelling is the spelled-out `snapshot.name = name` + store
  (B3/B4), with `copy()` as the A-reference (B2).

There is **no consumed `@ContractOnly` axiom** in this bundle: both behaviours
are pure object/structure logic. The only kind-A entries are the three
A-references (`__eq__`'s table comparison via `np.array_equal`, the entry
relation that fold applies, and `copy()`), all validated by axiom_check.py /
G-AX, never consumed as axioms.

## D. verify(model) ⇒ resolved

`colormaps_equal` verifies only if its result is the label-free predicate
(`colorbar_extend`-equal over the full six-valued flag domain AND
entrywise-table-equal under the relation the real fold supplies, A2/A3/A4/A5); `register_named` verifies
only if the stored snapshot carries the registration label (B3) while leaving
the supplied mapping untouched (B5) and every OTHER registry entry exactly as
it was (B6 — no side-write to any label other than the chosen one). By the R-refinements (label ↔ `int` token,
lut ↔ `List[int]` content, registry ↔ `Dict`, `copy()` ↔ fresh `Cmap`) and the
three G-AX-checked A-references, the verified model equals the gold patch's two
hunks on the tested inputs. The gold patch resolves (G-RESOLVE). The single
trust point is axiom soundness of the three A-references (G-AX) and the
refinement fidelity of this document (G-EQ) — exactly PLAN §1.1; no consumed
axiom is relied on.
