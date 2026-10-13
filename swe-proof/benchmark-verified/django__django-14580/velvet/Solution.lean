import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. This operation renders a runtime type as a source-code
   reference together with the import statements that reference requires. Every
   branch is a straight-line decision on fields already in hand (the type's
   identity among the canonical special types, and its module / qualified /
   short name strings); there is no unchanged callee whose contract the proof
   consumes, hence no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The observable slice of a runtime type that the rendering depends on:
     * `isBaseModelType` — the type is the framework base-model class, which is
                           referenced in source as `models.Model`;
     * `isNoneType`      — the type is the canonical none-valued type, referenced
                           as `type(None)`;
     * `moduleName`      — the name of the module the type is defined in;
     * `qualName`        — the type's dotted (qualified) name within its module;
     * `simpleName`      — the type's bare name.
   The two identity flags pick out two distinct canonical singleton types, so at
   most one of them holds (mapping.md §2). -/
structure TypeInfo where
  isBaseModelType : Bool
  isNoneType : Bool
  moduleName : String
  qualName : String
  simpleName : String
deriving DecidableEq

/- The source-code reference for a type, paired with the import statements that
   reference needs to be valid Python.

   The decision is ordered exactly as the source classifies a type:
   1. the framework base-model class renders as the literal reference
      `models.Model`, and that reference is only valid when accompanied by the
      import `from django.db import models` — so this case MUST carry that
      import (this is the desired behaviour the issue demands: a rendered
      `models.Model` reference whose import is dropped produces invalid Python
      that fails with a name error);
   2. the canonical none-valued type renders as `type(None)`, a built-in
      expression needing no import;
   3. a type defined in the built-in namespace renders by its bare name and
      needs no import;
   4. any other type renders as `module.qualified_name` and needs the matching
      `import module` statement. -/
def typeRef (t : TypeInfo) : String × List String :=
  if t.isBaseModelType then ("models.Model", ["from django.db import models"])
  else if t.isNoneType then ("type(None)", [])
  else if t.moduleName = "builtins" then (t.simpleName, [])
  else (t.moduleName ++ "." ++ t.qualName, ["import " ++ t.moduleName])
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a runtime type as a source reference plus the imports that reference
   requires. The base-model class must render with its import present, so that
   the emitted reference is valid standalone Python. -/
method renderTypeRef (t : TypeInfo) return (out : String × List String)
  ensures out = typeRef t
  do
    -- impl-start
    if t.isBaseModelType then
      return ("models.Model", ["from django.db import models"])
    else
      if t.isNoneType then
        return ("type(None)", [])
      else
        if t.moduleName = "builtins" then
          return (t.simpleName, [])
        else
          return (t.moduleName ++ "." ++ t.qualName, ["import " ++ t.moduleName])
    -- impl-end

prove_correct renderTypeRef by
  loom_solve <;> simp_all [typeRef]
