# refinement.md — django__django-12273

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`assignPrimaryIdentity` `do` block and the `writeSlot`/`writtenSlots` direct
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — none in this bundle), or **I**
(identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the data-flow facts and this narrative are audited by **G-EQ** and
**G-AX**. Claim: any impl verifying against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The primary-identity setter — `_set_pk_val()` (`django/db/models/base.py:571`)

Gold hunk:
```
  def _set_pk_val(self, value):
+     for parent_link in self._meta.parents.values():
+         if parent_link and parent_link != self._meta.pk:
+             setattr(self, parent_link.target_field.attname, value)
      return setattr(self, self._meta.pk.attname, value)
```

| # | Solution.lean impl op (`assignPrimaryIdentity`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `attrs : Store` | the instance attribute store `self.__dict__` | R | `self.__dict__` keyed by attr-name ↔ `Nat → Option Int` (mapping.md §2). |
| A2 | param `slots : List Slot` | `self._meta.parents.values()` | R | ordered parent-link descriptors ↔ `List Slot`; each `(target_field.attname, parent_link == pk)` ↔ `(attr, isPrimary)` (mapping.md §1,§2). Read-only — not `mut`. |
| A3 | param `value : Option Int`, `pk : Nat` | the `value` arg and `self._meta.pk.attname` | R | `None ↔ none`, int id `n ↔ some n`; pk attname ↔ its `Nat` id (mapping.md §2). |
| A4 | the `while` loop over `slots`, each step `result := writeSlot result value l` | the `for parent_link in self._meta.parents.values(): if parent_link and parent_link != self._meta.pk: setattr(self, parent_link.target_field.attname, value)` loop | I | concrete, transliterated by G-CONF. `writeSlot` skips `isPrimary` slots (the `!= self._meta.pk` guard) and sets the cell `l.attr` to `value` (the `setattr(..., target_field.attname, value)`). The `parent_link and` falsiness check is a no-op on the tested models (mapping.md §3) → no slot. |
| A5 | the final `return (fun k => if k = pk then value else result k)` | `return setattr(self, self._meta.pk.attname, value)` | I | the dedicated primary write: the pk cell is set to `value` last, overriding any prior write to it (matching `setattr` to `self._meta.pk.attname` as the final statement). |

Discriminating content of the change — assigning the primary identity ALSO
propagates `value` to every non-primary inherited-identity cell — lives in the
loop A4 and is pinned by the postconditions:
* `ensures out pk = value` (A5 — held by both pre- and post-patch);
* `ensures ∀ l ∈ slots, l.isPrimary = false → out l.attr = value` (A4 — the
  propagation guarantee; the pre-patch omits the loop, so a non-primary cell
  keeps its old value `attrs l.attr ≠ value`);
* `ensures out = (fun k => if k = pk then value else writtenSlots attrs slots
  value k)` (the exact post-store).

`Solution_prepatch.lean` reproduces the pre-patch setter (writes only the pk
cell, no loop) and **fails** on `ensures_1` (the propagation clause) and
`ensures_3` (the functional equality) for any record carrying a non-primary
inherited identity slot (G-DIFF).

## B. No second site

The gold patch is a single hunk in one function. There is no second
independently-fixed behaviour, so there is exactly one `Solution_prepatch.lean`.

## C. No axioms, no kind-3 (inexpressible-changed-op) steps

Every step is R or I. There is **no consumed axiom and no deep-model reference**:
the only behaviour that changed — the set of attribute cells the setter writes —
is modeled **directly** by `writeSlot`/`writtenSlots` plus the final pk write
(every observable computed from the inputs `attrs`/`slots`/`value`/`pk`). The
builtin `setattr`/`getattr` and the structural descriptors `_meta.parents` /
`target_field.attname` / `_meta.pk.attname` are not foreign callees with hidden
behaviour: the first is a plain cell update, the latter are read-only inputs
captured by `slots`/`pk` (mapping.md §3). Nothing is borrowed from an oracle.

## D. verify(Solution) ⇒ resolved

`assignPrimaryIdentity` verifies only if (A5) the pk cell holds `value` and (A4)
every non-primary inherited-identity cell also holds `value`, with all other
cells unchanged (the exact-store `ensures`). By R (`self.__dict__ ↔ Store`,
`parents ↔ slots`, `None ↔ none`) the verified setter writes exactly the cell set
`{pk} ∪ {slot.attr : ¬slot.isPrimary}` to `value` — which is exactly the patched
`_set_pk_val`'s write set on the F2P models (mapping.md §3, confirmed by G-AX); by
G-CONF the R/I transliteration agrees with `patch.diff`'s behaviour on ≥10⁵
inputs. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement — and the gold patch resolves (G-RESOLVE). The
single trust point is refinement fidelity (this doc, G-EQ + G-CONF) and the
data-flow layout facts (G-AX); there are no axioms to trust.
