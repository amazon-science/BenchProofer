import Mathlib
-- imports-end

/-!
Turning a test failure's representation into plain builtin data and back, so it
can be carried across process boundaries without losing structure.

A failure representation attached to a report is one of two shapes:

* a *single* exception — one rendered traceback together with one crash location;
* a *chain* of linked exceptions — an ordered list of links, each a rendered
  traceback, a crash location, and an optional connective line shown between
  successive links (the kind of text that introduces a follow-on exception).

Both shapes also carry an ordered list of titled sections. For a chain, the
outermost traceback and crash location are exactly those of its last link.

Two operations are modeled:

* *serialization* converts a failure representation into a builtin-data form
  carrying the outermost crash location and traceback, the sections, and — when
  the representation is a chain — the full ordered list of its links. A single
  exception records no link list.
* *deserialization* rebuilds a failure representation from that builtin-data
  form: when a non-empty list of links is present it reconstructs the whole
  chain (so every linked exception is recovered, in order, with its connective
  text); otherwise it reconstructs a single exception from the outermost
  traceback and crash location. The sections are carried through unchanged.

Together these guarantee that converting a chain to builtin data and back yields
the same chain — every link preserved — rather than collapsing it to only its
outermost exception.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The shape of a
-- failure representation, the recording of its chain of links, and the
-- reconstruction of that chain are all modeled DEEPLY over the observable data
-- (the links, the sections, the outermost traceback/crash), so no
-- `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A source-location reference: a path, a line number, and a message. -/
structure FileLoc where
  path : String
  lineno : Int
  message : String
deriving DecidableEq, Repr, Inhabited

/-- One rendered traceback: its per-frame entry lines, an optional trailing
line, and a style tag. -/
structure Traceback where
  entries : List String
  extraline : Option String
  style : String
deriving DecidableEq, Repr, Inhabited

/-- One link of an exception chain: a traceback, its crash location, and an
optional connective description shown ahead of the next link. -/
abbrev Link := Traceback × FileLoc × Option String

/-- A failure representation: either a single exception (one traceback and one
crash location) or a chain of linked exceptions. Both carry an ordered list of
titled sections `(name, content, separator)`. -/
inductive Longrepr where
  | single (traceback : Traceback) (crash : FileLoc)
           (sections : List (String × String × String))
  | chained (chain : List Link)
            (sections : List (String × String × String))
deriving Repr, Inhabited

/-- The builtin-data form of a failure representation: the outermost crash
location and traceback, the sections, and an optional list of links (absent for
a single exception, present for a chain). -/
structure SerializedLongrepr where
  crash : FileLoc
  traceback : Traceback
  sections : List (String × String × String)
  chain : Option (List Link)
deriving Repr, Inhabited

/-- Repackaging a single chain link into / out of builtin form preserves its
modeled fields. -/
def packLink (l : Link) : Link := l
def unpackLink (l : Link) : Link := l

/-- The outermost (last) link's traceback and crash location. -/
def outerOf (chain : List Link) : Traceback × FileLoc :=
  match chain.getLast? with
  | some (tb, cr, _) => (tb, cr)
  | none => (default, default)

/-- Serialization: a single exception records no link list; a chain records the
full ordered list of its links and exposes its last link's traceback/crash as
the outermost ones. -/
def serializeLongrepr (lr : Longrepr) : SerializedLongrepr :=
  match lr with
  | .single tb cr secs =>
      { crash := cr, traceback := tb, sections := secs, chain := none }
  | .chained chain secs =>
      let outer := outerOf chain
      { crash := outer.2, traceback := outer.1, sections := secs,
        chain := some (chain.map packLink) }

/-- Deserialization: a non-empty link list rebuilds the whole chain; otherwise a
single exception is rebuilt from the outermost traceback and crash location. The
sections are carried through unchanged. -/
def deserializeLongrepr (s : SerializedLongrepr) : Longrepr :=
  match s.chain with
  | some (l :: ls) => .chained ((l :: ls).map unpackLink) s.sections
  | _ => .single s.traceback s.crash s.sections
-- pure-end

-- post-conditions-start
/-- Serialization produces exactly the builtin-data form dictated by the rule
above. -/
def problem_spec_serialize (lr : Longrepr) (result : SerializedLongrepr) : Prop :=
  result = serializeLongrepr lr
-- post-conditions-end

-- impl-start
def implementation_serialize (lr : Longrepr) : SerializedLongrepr := Id.run do
  match lr with
  | .single tb cr secs =>
      return { crash := cr, traceback := tb, sections := secs, chain := none }
  | .chained chain secs =>
      let outer := outerOf chain
      let mut serChain : List Link := []
      for link in chain do
        serChain := serChain ++ [packLink link]
      return { crash := outer.2, traceback := outer.1, sections := secs,
               chain := some serChain }
-- impl-end

-- post-conditions-start
/-- Deserialization produces exactly the failure representation dictated by the
rule above. -/
def problem_spec_deserialize (s : SerializedLongrepr) (result : Longrepr) : Prop :=
  result = deserializeLongrepr s
-- post-conditions-end

-- impl-start
def implementation_deserialize (s : SerializedLongrepr) : Longrepr := Id.run do
  match s.chain with
  | some (l :: ls) =>
      let mut deChain : List Link := []
      for link in (l :: ls) do
        deChain := deChain ++ [unpackLink link]
      return .chained deChain s.sections
  | _ =>
      return .single s.traceback s.crash s.sections
-- impl-end

-- proof-start
theorem correct_serialize :
    ∀ (lr : Longrepr), problem_spec_serialize lr (implementation_serialize lr) := by
  intro lr
  cases lr with
  | single => rfl
  | chained chain secs =>
      show _ = serializeLongrepr _
      simp [implementation_serialize, serializeLongrepr]
      induction chain with
      | nil => rfl
      | cons a t ih => simp [ih]

-- proof-end

-- proof-start
theorem correct_deserialize :
    ∀ (s : SerializedLongrepr), problem_spec_deserialize s (implementation_deserialize s) := by
  intro s
  have key : ∀ (l : List Link), (List.map (fun x => [unpackLink x]) l).flatten = List.map unpackLink l := by
    intro l; induction l with
    | nil => simp
    | cons a t ih => simp [ih]
  unfold problem_spec_deserialize implementation_deserialize deserializeLongrepr
  split <;> simp [key]

-- proof-end
