import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No axiomatized callees and no deep-model reference to a library callee.

   The operation that renders one source-level annotation into its display type
   string — resolving any configured type aliases and formatting the result — is
   an UNCHANGED sub-step. It is taken as a FREE INPUT `renderType` (a function of
   the configured alias map and the source annotation), so the spec makes no
   behavioural claim about it and holds for EVERY value of it. What this bundle
   pins is that the recorded type string for each name is produced by applying
   that renderer to the CONFIGURED alias map (not to an empty one) — modeled
   DEEPLY below. Nothing here needs validation against a real callee, so there is
   no module-level `axiom` and G-AX has nothing to check. -/
-- axioms-end

-- pure-start
/- The configured alias map: an ordered association of alias names to their
   replacement targets (mapping.md §2). Opaque to the spec — consulted only by
   the free renderer. -/
abbrev Aliases := List (List Char × List Char)

/- A source-level annotation and a rendered display type string are both carried
   as `List Char` (mapping.md §2). -/
abbrev SourceType := List Char
abbrev TypeStr := List Char

/- One signature entry: a name and, optionally, its source annotation. A `none`
   annotation marks an unannotated name. -/
structure Param where
  name  : List Char
  annot : Option SourceType
deriving DecidableEq, Inhabited

/- The recorded contribution of a single name: an unannotated name contributes
   nothing; an annotated one contributes the pair binding its name to the type
   string the renderer produces for its annotation. -/
def paramEntry (render : SourceType → TypeStr) (p : Param) :
    List (List Char × TypeStr) :=
  match p.annot with
  | some a => [(p.name, render a)]
  | none   => []

/- The recorded mapping for a whole sequence of names: concatenate the
   per-name contributions in order. Front-recursive so a single unfold is
   available per loop step (the backward-fold pattern). -/
def recordedTypes (render : SourceType → TypeStr) :
    List Param → List (List Char × TypeStr)
  | []      => []
  | p :: ps => paramEntry render p ++ recordedTypes render ps

@[grind] lemma recordedTypes_nil (render : SourceType → TypeStr) :
    recordedTypes render [] = [] := rfl
@[grind] lemma recordedTypes_cons (render : SourceType → TypeStr)
    (p : Param) (ps : List Param) :
    recordedTypes render (p :: ps) = paramEntry render p ++ recordedTypes render ps := rfl

/- The recorded contribution of the return annotation (under the constant
   `return` key), appended last: present iff a return annotation exists. -/
def returnEntry (render : SourceType → TypeStr) (ret : Option SourceType) :
    List (List Char × TypeStr) :=
  match ret with
  | some a => [("return".toList, render a)]
  | none   => []
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Record the display type string of every annotated name in a callable's
   signature, plus its return annotation, into an ordered mapping.

   The renderer `renderType` turns a source annotation into a display string,
   given an alias map to resolve. The desired behaviour: each recorded string is
   the renderer applied to the CONFIGURED alias map `aliases` — so configured
   aliases take effect — for the names that carry an annotation, in order, with
   the return annotation recorded last. `params`, `retAnnot`, `aliases`, and the
   renderer `renderType` are read-only (directive 5). -/
method recordParamTypes (params : List Param) (retAnnot : Option SourceType)
    (aliases : Aliases) (renderType : Aliases → SourceType → TypeStr)
    return (out : List (List Char × TypeStr))
  ensures out =
    recordedTypes (renderType aliases) params ++ returnEntry (renderType aliases) retAnnot
  do
    -- impl-start
    let mut result : List (List Char × TypeStr) := returnEntry (renderType aliases) retAnnot
    let mut i := params.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ params.length
      invariant result =
        recordedTypes (renderType aliases) (params.drop i)
          ++ returnEntry (renderType aliases) retAnnot
      done_with i = 0
      decreasing i
    do
      let p := params[i - 1]!
      result := paramEntry (renderType aliases) p ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the name at `i-1`
   on the front, so `recordedTypes` peels one `paramEntry`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma recordedTypes_drop_step (render : SourceType → TypeStr) (ps : List Param) (i : Nat)
    (hi : 0 < i) (hle : i ≤ ps.length) :
    recordedTypes render (ps.drop (i - 1))
      = paramEntry render ps[i - 1]! ++ recordedTypes render (ps.drop i) := by
  have hlt : i - 1 < ps.length := by omega
  have hcons : ps.drop (i - 1) = ps[i - 1]! :: ps.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, recordedTypes_cons]

prove_correct recordParamTypes by
  loom_solve
  rw [recordedTypes_drop_step (renderType aliases) params i (by omega) (by omega)]
  simp_all
