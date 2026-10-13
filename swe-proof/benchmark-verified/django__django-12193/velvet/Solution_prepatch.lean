import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The operation reads one observation of the input
--  value — whether this control should record the affirmative state flag — and
--  an attribute mapping supplied by the caller, then produces the attribute
--  mapping handed onward to the shared base renderer while leaving the caller's
--  mapping exactly as it was on entry. The observation is taken as a plain
--  boolean input and the mapping transformation is modeled directly, so no
--  unchanged callee's contract is consumed and no foreign callee is deep-modeled
--  — there is nothing to axiomatize. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- Install a key/value entry into an attribute mapping, replacing the value if
   the key is already present and otherwise appending it. Front-recursive so the
   value associated with a key is determined positionally by the first matching
   entry (mappings carry unique keys, mapping.md §2). -/
def setFlag : List (String × Bool) → String → Bool → List (String × Bool)
  | [],               k, v => [(k, v)]
  | (k', v') :: rest, k, v =>
      if k' = k then (k, v) :: rest else (k', v') :: setFlag rest k v

/- The attribute mapping a control hands onward when it has determined the
   affirmative state flag should be recorded: the caller's mapping with the
   "checked" entry set true (added if absent, overwritten if present). This is a
   FRESH mapping value; the caller's mapping is never altered by producing it. -/
def withChecked (attrs : List (String × Bool)) : List (String × Bool) :=
  setFlag attrs "checked" true
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the attribute mapping a checkbox-style control passes to the shared
   base renderer for one rendering.

   The caller owns the attribute mapping `attrs`; the same mapping value is
   reused across the repeated renderings of a multi-element control, so this
   operation must treat it as read-only state — it reads the mapping to derive
   the onward mapping but must leave the caller's mapping exactly as received.
   `attrs` is declared `mut` because the long-standing shape of this code reaches
   for the caller's mapping as the thing to augment, but its post-state is pinned
   to its entry value `attrsOld` (directive 5): the caller's mapping survives the
   operation unchanged, which is precisely what lets a later rendering of the
   same control start from a clean mapping rather than inherit a flag from an
   earlier element.

   `checked` (read-only) is the observation of whether this element's backing
   value makes the control affirmative; it is never altered. The returned
   `effective` mapping is the onward mapping: when the control is affirmative it
   is the caller's mapping with the "checked" entry recorded true; otherwise it
   is the caller's mapping verbatim. -/
method computeContextAttrs (mut attrs : List (String × Bool)) (checked : Bool)
    return (effective : List (String × Bool))
  ensures attrs = attrsOld
  ensures effective = if checked then withChecked attrsOld else attrsOld
  do
    -- impl-start
    -- (Pre-patch skeleton.) Record the affirmative flag by writing it directly
    -- onto the caller's mapping when the control is affirmative, then read the
    -- onward mapping back off it. The caller's mapping itself is written, so its
    -- entry value does not survive this operation unchanged.
    attrs := if checked then withChecked attrs else attrs
    return attrs
    -- impl-end

prove_correct computeContextAttrs by
  loom_solve
