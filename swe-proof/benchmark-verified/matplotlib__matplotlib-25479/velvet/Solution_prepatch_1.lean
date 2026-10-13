import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms and no deep-model reference. Two independent behaviours are
-- modeled here, each as a pure decision over a colormap's own observable fields:
-- (1) which name a colormap carries once it has been stored under a chosen
-- registration name, and (2) when two colormaps are considered the same value.
-- Both are total functions of the structure's fields (name, the extend style,
-- and the color lookup table); there is no foreign callee whose contract the
-- proof assumes and none that is deep-modeled. See refinement.md §C / mapping.md
-- §3 (there is no `axiom` declaration and no A-reference).
-- axioms-end

-- pure-start
/- The observable state of a colormap that the modeled behaviours depend on:
   the human-readable `name` it advertises, the `extendStyle` flag that records
   whether its out-of-range ends are drawn specially, and the `lookupTable` of
   per-sample colour rows it resolves values through (each row a fixed-width
   tuple of integer colour components). Only the fields the modeled behaviours
   read or write are carried; everything else about a colormap is irrelevant
   here and omitted (mapping.md §2). -/
structure Colormap where
  name : String
  extendStyle : Bool
  lookupTable : List (List Int)
deriving DecidableEq, Inhabited, Repr

/- Value-equality of two colormaps: they advertise the same out-of-range
   end-style AND resolve values through the same colour lookup table. A
   colormap's advertised name is metadata that does NOT participate — two
   colormaps that differ only in name still resolve every value identically and
   are therefore the same colormap value. -/
def colormapEqSpec (a b : Colormap) : Bool :=
  decide (a.extendStyle = b.extendStyle) && decide (a.lookupTable = b.lookupTable)
-- pure-end

-- pre-conditions-start
-- (no module-level preconditions; the inputs are always supplied)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the inline `ensures` clauses on the methods below)
-- post-conditions-end

/- The colormap that ends up stored under a chosen registration name.

   Desired behaviour: a colormap may be stored for future lookup under a name
   chosen at storage time that differs from the name the colormap object itself
   advertises. The stored colormap must advertise the name it was stored under —
   otherwise a later lookup that consults the stored colormap's own advertised
   name would disagree with the name it is reachable by. Storing is otherwise
   content-preserving: it keeps the colormap's end-style and colour lookup table
   exactly. `cmap` is the colormap being stored; it is a read-only input (not
   `mut`) and is never altered in place (directive 5) — the result is the stored
   colormap. `name` is the chosen registration name. -/
method registeredColormap (cmap : Colormap) (name : String) return (out : Colormap)
  ensures out.name = name
  ensures out.extendStyle = cmap.extendStyle
  ensures out.lookupTable = cmap.lookupTable
  do
    -- impl-start
    -- Pre-patch skeleton (buggy): the colormap is stored as-is, KEEPING the name
    -- it already advertises rather than adopting the chosen registration name.
    -- When the colormap advertises a name other than the registration name, the
    -- stored colormap's advertised name disagrees with the name it is reachable
    -- by. The frozen spec requires `out.name = name`, so prove_correct MUST fail.
    let stored := cmap
    return stored
    -- impl-end

prove_correct registeredColormap by
  loom_solve

/- Whether two colormaps are the same colormap value (see `colormapEqSpec`).
   Both colormaps are read-only inputs. Desired behaviour: the verdict turns on
   the end-style and the colour lookup table only; the advertised names are
   ignored, so a colormap and a renamed duplicate of it compare equal. -/
method colormapsEqual (a : Colormap) (b : Colormap) return (out : Bool)
  ensures out = colormapEqSpec a b
  do
    -- impl-start
    -- The same colormap value iff the end-styles agree and the colour lookup
    -- tables agree; the advertised names do not enter the comparison.
    return (decide (a.extendStyle = b.extendStyle) && decide (a.lookupTable = b.lookupTable))
    -- impl-end

prove_correct colormapsEqual by
  loom_solve
  simp_all [colormapEqSpec]
