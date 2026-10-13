import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms: the composite mapping is modeled deeply below and
--  validated against the real library routine by G-AX as an A-reference.)
-- axioms-end

-- pure-start
/- The image of a point under one elementary mapping written as a list
   `(a, b, c, …)`: each listed element is sent to the next one, the last wraps
   back to the first, and points not listed map to themselves. `first` carries
   the head so the final element can close the loop. -/
def succInCycle (first : Nat) : List Nat → Nat → Nat
  | [], x => x
  | [a], x => if x = a then first else x
  | a :: b :: rest, x => if x = a then b else succInCycle first (b :: rest) x

/- One elementary mapping applied to a single point. -/
def cycleStep (cyc : List Nat) (x : Nat) : Nat :=
  match cyc with
  | [] => x
  | a :: _ => succInCycle a cyc x

/- The composite of a sequence of elementary mappings, applied in left-to-right
   order: the leftmost mapping acts first, then the next, and so on. Overlapping
   mappings are allowed — they simply compose. -/
def composePoint : List (List Nat) → Nat → Nat
  | [], x => x
  | c :: cs, x => composePoint cs (cycleStep c x)

/- The largest element mentioned anywhere in the data. -/
def maxElem : List (List Nat) → Nat
  | [] => 0
  | c :: cs => Nat.max (c.foldr Nat.max 0) (maxElem cs)

/- Length of the resulting explicit list: one past the largest mentioned point,
   so every point that can move has a slot. -/
def listSize (cycles : List (List Nat)) : Nat := maxElem cycles + 1

/- The explicit list form of the composite mapping: position `i` holds the image
   of `i` under the left-to-right composite. This is the deep model of the whole
   (unchanged) composition routine — an A-reference validated by G-AX. -/
def arrayForm (cycles : List (List Nat)) : List Nat :=
  (List.range (listSize cycles)).map (composePoint cycles)

/- Whether a flat list of points mentions each of its points at most once. -/
def pointsDistinct (l : List Nat) : Bool := decide l.Nodup

/- Whether a flat list of points leaves no gap below the count of the distinct
   points it mentions: every `i` under that count occurs in it. -/
def rangeCovered (l : List Nat) : Bool :=
  (List.range l.dedup.length).all (fun i => l.contains i)

/- Whether a flat list of `n` points is already an explicit list form in its own
   right: it must place each of the points `0 … n-1` exactly once, which is
   `pointsDistinct` together with `rangeCovered`. -/
def explicitForm (l : List Nat) : Bool := pointsDistinct l && rangeCovered l

/- Well-formedness of the grouped reading: at least one point is named
   somewhere, and no group names a point twice (the unchanged precondition the
   grouped reading must already meet). A group that names nothing is allowed as
   long as some other group names something. -/
def eachValid (cycles : List (List Nat)) : Prop :=
  cycles.flatten ≠ [] ∧ ∀ c ∈ cycles, c.Nodup
-- pure-end

-- pre-conditions-start
-- pre-conditions-end
-- post-conditions-start
-- post-conditions-end

/- Produce the explicit list form of a rearrangement of the points `0, 1, …`
   from an argument that may be written in either of two ways, selected by
   `grouped`.

   * `grouped = true` — `entries` is a list of groups. Each group names points
     carried onto one another in the order written, the last returning to the
     head, and the groups act one after another from left to right. Groups are
     free to name points in common. The answer is the explicit list form of the
     resulting rearrangement: position `i` holds the image of `i`.
   * `grouped = false` — the argument is the one flat list `entries.flatten`,
     which already is an explicit list form and is handed back unchanged; but
     only when it really is one, i.e. it places each of the points below its own
     length exactly once. A flat list that does not name a rearrangement at all
     is refused instead.

   `Except.error ()` models refusal; `Except.ok` carries the explicit list. -/
method buildExplicitForm (entries : List (List Nat)) (grouped : Bool)
    return (result : Except Unit (List Nat))
  require grouped = true → eachValid entries
  ensures grouped = true → result = Except.ok (arrayForm entries)
  ensures grouped = false → explicitForm entries.flatten = true →
    result = Except.ok entries.flatten
  ensures grouped = false → explicitForm entries.flatten = false →
    result = Except.error ()
  do
    -- impl-start
    let temp := entries.flatten
    if !pointsDistinct temp && !grouped then
      return Except.error ()
    else
      if !grouped && !rangeCovered temp then
        return Except.error ()
      else
        if grouped then
          return Except.ok (arrayForm entries)
        else
          return Except.ok temp
    -- impl-end

prove_correct buildExplicitForm by
  loom_solve
  all_goals simp_all [explicitForm]
