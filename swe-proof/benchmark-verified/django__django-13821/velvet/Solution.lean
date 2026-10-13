import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references to unchanged callees. The
   operations this slice relies on — lexicographic comparison of the version
   tuple and assembly of the diagnostic message — are language primitives,
   modeled directly in the `pure` region (concrete I-ops) and refinement-checked
   against the real behaviour by conformance_check.py (G-CONF), mapping.md §3. -/
-- axioms-end

-- pure-start
/- Lexicographic strict order on version tuples, modeled as natural-number
   sequences. Mirrors the total ordering of the runtime version-info tuple:
   compare component by component; a shorter tuple that is a prefix of a longer
   one ranks below it (e.g. `[3, 9]` precedes `[3, 9, 0]`). Front-recursive so a
   single unfold is available per comparison step. -/
def lexLt : List Nat → List Nat → Bool
  | [],      []      => false
  | [],      _ :: _  => true
  | _ :: _,  []      => false
  | a :: xs, b :: ys =>
      if a < b then true
      else if b < a then false
      else lexLt xs ys

/- The minimum version the database must report. -/
def requiredVersion : List Nat := [3, 9, 0]

/- The diagnostic the operation surfaces when the reported version is below the
   minimum: it states the required version and echoes the version actually
   found. -/
def errorMessage (versionStr : List Char) : List Char :=
  "SQLite 3.9.0 or later is required (found ".toList ++ versionStr ++ ").".toList

/- The intended outcome: when the reported version sorts below the required
   minimum, the check fails with the diagnostic; otherwise it succeeds with no
   value. -/
def checkSpec (info : List Nat) (versionStr : List Char) : Except (List Char) Unit :=
  if lexLt info requiredVersion then Except.error (errorMessage versionStr)
  else Except.ok ()

@[simp, grind] lemma requiredVersion_eq : requiredVersion = [3, 9, 0] := rfl

@[grind] lemma checkSpec_def (info : List Nat) (versionStr : List Char) :
    checkSpec info versionStr =
      (if lexLt info requiredVersion then Except.error (errorMessage versionStr)
       else Except.ok ()) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method verifyVersion (info : List Nat) (versionStr : List Char)
    return (out : Except (List Char) Unit)
  ensures out = checkSpec info versionStr
  do
    -- impl-start
    -- Fail with the diagnostic exactly when the reported version sorts below the
    -- required minimum; otherwise succeed.
    let tooOld : Bool := lexLt info [3, 9, 0]
    let out : Except (List Char) Unit :=
      if tooOld then Except.error (errorMessage versionStr) else Except.ok ()
    return out
    -- impl-end

prove_correct verifyVersion by
  loom_solve
