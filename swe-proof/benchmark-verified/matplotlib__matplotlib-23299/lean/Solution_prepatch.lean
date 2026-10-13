import Mathlib
-- imports-end

/-!
Temporarily overriding a global configuration mapping, then restoring it.

A scoped configuration manager snapshots a global settings mapping on entry,
lets a body of code run (which may freely change the values stored in the
mapping), and on exit puts the previously-recorded values back. The mapping is a
collection of named string-valued settings with a stable set of keys; one of
those keys, `"backend"`, names the active rendering backend.

The restore must reinstate every recorded setting EXCEPT the rendering backend:
the value chosen for `"backend"` while the body was running is left in place,
because the backend selection is meant to outlive the scoped override. All other
settings revert to the values they held when the manager was entered.

We model the manager's net effect on the mapping as a pure function of two
observations: the mapping captured on entry (`orig`) and the mapping present when
the body has finished (`final`). The restored mapping keeps `final`'s value for
`"backend"` and `orig`'s value for every other key.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The restore's
-- per-key behavior (which keys revert and which is kept) is modeled DEEPLY over
-- the observable mapping values, so no `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- A settings mapping: named string-valued entries with (in practice) unique
keys and a stable key set. -/
abbrev Settings := List (String × String)

/-- Overwrite the value at key `k` with `v`, keeping position; append if absent.
This is the per-key effect of overlaying one mapping onto another. -/
def assocSet : Settings → String → String → Settings
  | [],            k, v => [(k, v)]
  | (k', v') :: r, k, v => if k' = k then (k, v) :: r else (k', v') :: assocSet r k v

/-- Overlay every entry of `upd` onto `cur` (cur's entries are overwritten by
upd's; the result follows cur's order, with absent keys appended). -/
def dictUpdate (cur upd : Settings) : Settings :=
  upd.foldl (fun acc kv => assocSet acc kv.1 kv.2) cur

/-- Drop every entry whose key equals `k`. -/
def assocErase (m : Settings) (k : String) : Settings :=
  m.filter (fun kv => kv.1 != k)

/-- The net effect of the scoped manager's restore on the mapping: overlay the
entry snapshot onto the post-body mapping, but with the `"backend"` entry removed
from the snapshot first so the backend chosen inside the scope survives. -/
def applyRestore (orig final : Settings) : Settings :=
  dictUpdate final (assocErase orig "backend")
-- pure-end

-- post-conditions-start
/-- The restored mapping is exactly the post-body mapping with every recorded
setting reinstated EXCEPT the rendering backend, whose post-body value is kept. -/
def problem_spec_restoreSettings (orig final : Settings) (result : Settings) : Prop :=
  result = applyRestore orig final
-- post-conditions-end

-- impl-start
def implementation_restoreSettings (orig final : Settings) : Settings := Id.run do
  -- Pre-patch (buggy) restore: the entry snapshot is overlaid onto the post-body
  -- mapping in full, including the `"backend"` entry, so the backend value
  -- chosen while the body was running is overwritten by the entry value.
  let mut snapshot := orig
  return dictUpdate final snapshot
-- impl-end

-- proof-start
theorem correct_restoreSettings : ∀ (orig final : Settings),
    problem_spec_restoreSettings orig final
      (implementation_restoreSettings orig final) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
