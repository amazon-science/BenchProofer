import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The resolution depends on three values that
--  are observed from the environment, never mutated by this routine, and are
--  supplied to the model as read-only inputs:
--    * an explicit override location (present iff the caller pinned one);
--    * the resolved home directory of the current user;
--    * the platform-designated per-application cache directory for this tool.
--  The third is the value the post-state behaviour selects in the default case;
--  it is modeled as the input `cacheDir` (an A-reference: its binding to the
--  real directory-resolution callee is validated == that callee by
--  axiom_check.py / G-AX, and left as the real callee by conformance_check.py /
--  G-CONF). Nothing about its internal computation is assumed, so there is no
--  axiom to consume.)
-- axioms-end

-- pure-start
/- The location where this tool keeps its persistent per-user data, decided
   from the observed environment:

     * if an explicit override location was supplied, that location is used
       verbatim;
     * otherwise, if the user's home directory could not be resolved (it is
       still the literal `~`), the relative legacy directory `.pylint.d` in the
       current working directory is used;
     * otherwise the platform-designated per-application cache directory for
       this tool is used.

   The result is determined structurally by the three observed inputs (no opaque
   oracle): `override`, the resolved home `userHome`, and the designated cache
   directory `cacheDir`. -/
def resolveHome (override : Option (List Char)) (userHome : List Char)
    (cacheDir : List Char) : List Char :=
  match override with
  | some loc => loc
  | none     => if userHome = "~".toList then ".pylint.d".toList else cacheDir

@[grind] lemma resolveHome_override (loc : List Char) (userHome cacheDir : List Char) :
    resolveHome (some loc) userHome cacheDir = loc := rfl

@[grind] lemma resolveHome_default (userHome cacheDir : List Char)
    (h : userHome ≠ "~".toList) :
    resolveHome none userHome cacheDir = cacheDir := by
  simp only [resolveHome, if_neg h]

@[grind] lemma resolveHome_tilde (cacheDir : List Char) :
    resolveHome none "~".toList cacheDir = ".pylint.d".toList := by
  simp [resolveHome]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide the directory in which this tool stores its persistent per-user data.

   The decision is read off the observed environment and nothing it inspects is
   modified (directive 5 — every parameter is read-only):

     * an explicitly pinned override location is honoured verbatim;
     * with no override, if the user's home directory is unresolved (still the
       literal `~`), the legacy relative directory `.pylint.d` is used;
     * with no override and a resolved home, the platform-designated
       per-application cache directory for this tool is used — keeping the
       user's home directory uncluttered.

   `cacheDir` is the per-application cache directory the platform's standard
   directory resolution designates for this tool. -/
method resolveDataHome (override : Option (List Char)) (userHome : List Char)
    (cacheDir : List Char) return (out : List Char)
  ensures out = resolveHome override userHome cacheDir
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct resolveDataHome by
  -- proof elided — supplied by the consumer
