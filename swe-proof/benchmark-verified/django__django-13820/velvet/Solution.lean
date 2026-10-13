import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references to unchanged callees. The
   operations this slice relies on — testing whether an imported module carries a
   concrete file location, exposes an ordinary search path, and whether that
   search path is an ordinary list — are language-level attribute observations,
   modeled directly here as the three boolean inputs (concrete I-ops) and
   refinement-checked against the real behaviour by conformance_check.py
   (G-CONF), mapping.md §3. -/
-- axioms-end

-- pure-start
/- Whether a candidate module's on-disk migrations directory should be scanned
   and its migrations loaded.

   The inputs describe the module by three observations:
   * `hasFile`     — it advertises a concrete file location;
   * `hasPath`     — it exposes a package search path (i.e. it is a package, not
                     a plain module);
   * `pathIsList`  — that search path is an ordinary list.

   A module contributes on-disk migrations exactly when it is a package
   (`hasPath`) that is not an implicit namespace package. The implicit namespace
   case — and the ONLY case excluded among packages — is the one that advertises
   no concrete file location AND whose search path is not an ordinary list
   (`!hasFile && !pathIsList`). In particular a package that omits a file
   location yet still uses an ordinary list search path is scanned like any other
   package. -/
def loadable (hasFile hasPath pathIsList : Bool) : Bool :=
  hasPath && (hasFile || pathIsList)

@[simp, grind] lemma loadable_def (hasFile hasPath pathIsList : Bool) :
    loadable hasFile hasPath pathIsList = (hasPath && (hasFile || pathIsList)) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method migrationsModuleLoadable (hasFile : Bool) (hasPath : Bool) (pathIsList : Bool)
    return (out : Bool)
  ensures out = loadable hasFile hasPath pathIsList
  do
    -- impl-start
    -- A module that is not a package contributes nothing; a package that
    -- advertises no concrete file location and whose search path is not an
    -- ordinary list is an implicit namespace package and is also skipped; every
    -- other package is scanned.
    let notPackage : Bool := !hasPath
    let isNamespace : Bool := (!hasFile) && (!pathIsList)
    let out : Bool :=
      if notPackage then false
      else
        if isNamespace then false
        else true
    return out
    -- impl-end

prove_correct migrationsModuleLoadable by
  loom_solve
