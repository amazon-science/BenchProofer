import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a closed function of
--  its inputs. A model-administration validator inspects one configuration
--  entry and decides whether to report a problem and, if so, with what
--  descriptive text. The four runtime observations the decision depends on —
--  whether the entry is itself an invokable object, whether it names an
--  attribute of the administrator, whether it names an attribute of the
--  administered model class, and whether the model's field registry recognises
--  the name — are abstracted to the four boolean inputs of the method; the four
--  pieces of text quoted by the diagnostic (the entry's label, the entry's
--  name, the administrator's type name, and the model's label) are abstracted
--  to four `List Char` inputs. Each boolean is an R-refinement of a real
--  observation (callable / hasattr(admin) / hasattr(model) / field-registry
--  lookup), validated against the real objects by conformance_check.py
--  (G-CONF). Nothing is consumed as an axiom — see refinement.md §C and
--  mapping.md §3.)
-- axioms-end

-- pure-start
/- The exact diagnostic text produced for an entry that resolves to nothing
   usable on the administered model. It quotes, in order, the entry's label,
   the entry's name, the administrator's type name, and the administered
   model's label. The shape — naming the entry between the label and the
   "is not a callable …" clause — is the unified phrasing the public task
   description asks for (other configuration entries already report the name
   this way). The four quoted pieces are free inputs; only their arrangement
   into the message is specified here. -/
@[grind] def itemDiagnostic (label name adminName modelLabel : List Char) : List Char :=
  "The value of '".toList ++ label
    ++ "' refers to '".toList ++ name
    ++ "', which is not a callable, an attribute of '".toList ++ adminName
    ++ "', or an attribute of '".toList ++ modelLabel
    ++ "'.".toList

/- The report for one configuration entry: `none` when the entry is acceptable
   (no diagnostic), or `some msg` carrying the diagnostic text when it is not.

   Reading order, mirroring how the validator examines the entry:

   1. An invokable entry (`isCallable`) is acceptable.
   2. Otherwise, an entry naming an attribute of the administrator
      (`hasAttrAdmin`) is acceptable.
   3. Otherwise, an entry naming an attribute of the administered model class
      (`hasAttrModel`) is acceptable.
   4. Otherwise the entry must be a known field of the model. If the field
      registry does not recognise the name (`fieldUnknown`) the entry is
      unresolvable and is reported with `itemDiagnostic`; if the registry does
      recognise it, the entry is acceptable.

   The diagnostic's quoted pieces are exactly `label`, `name`, `adminName`,
   `modelLabel`. -/
@[grind] def readonlyItemReport
    (isCallable hasAttrAdmin hasAttrModel fieldUnknown : Bool)
    (label name adminName modelLabel : List Char) : Option (List Char) :=
  if isCallable then none
  else if hasAttrAdmin then none
  else if hasAttrModel then none
  else if fieldUnknown then some (itemDiagnostic label name adminName modelLabel)
  else none
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Validate one entry of a model administrator's read-only configuration and
   decide how it is reported: acceptable (`none`), or a diagnostic carrying the
   text built by `itemDiagnostic` (`some msg`).

   Desired behaviour (the abstract contract; see `readonlyItemReport`): an
   invokable entry, an entry naming an attribute of the administrator, or an
   entry naming an attribute of the administered model class, is acceptable.
   Otherwise the entry must be a field recognised by the model's field
   registry; when the registry does not recognise the name the entry is
   reported, and the diagnostic quotes the entry's label, the entry's name, the
   administrator's type name, and the model's label — in that order.

   All eight inputs are read-only observations (none declared `mut`): the
   routine inspects them and returns the report for the entry; it mutates
   nothing (directive 5). The result is pinned exactly by `readonlyItemReport`. -/
method readonlyItemCheck
    (isCallable : Bool) (hasAttrAdmin : Bool) (hasAttrModel : Bool) (fieldUnknown : Bool)
    (label : List Char) (name : List Char) (adminName : List Char) (modelLabel : List Char)
    return (out : Option (List Char))
  ensures out = readonlyItemReport isCallable hasAttrAdmin hasAttrModel fieldUnknown
                                   label name adminName modelLabel
  do
    -- impl-start
    -- An invokable entry, or one naming an attribute of the administrator or of
    -- the administered model class, is acceptable outright. Otherwise the entry
    -- must be recognised by the model's field registry; when it is not, report
    -- it with the diagnostic text quoting label, name, administrator type, and
    -- model label, in that order.
    let result : Option (List Char) :=
      if isCallable then none
      else if hasAttrAdmin then none
      else if hasAttrModel then none
      else if fieldUnknown then
        some ("The value of '".toList ++ label
          ++ "' refers to '".toList ++ name
          ++ "', which is not a callable, an attribute of '".toList ++ adminName
          ++ "', or an attribute of '".toList ++ modelLabel
          ++ "'.".toList)
      else none
    return result
    -- impl-end

prove_correct readonlyItemCheck by
  loom_solve
