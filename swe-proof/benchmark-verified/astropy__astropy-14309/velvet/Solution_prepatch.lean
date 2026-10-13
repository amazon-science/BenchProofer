import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The distinguished failure that escapes the classifier when it consults a
   positional observation that is not present: a required entry of the trailing
   positional sequence is read while that sequence is empty. This is the failure
   shape the public problem statement reports as escaping from a path-only call.
   It is a genuine outcome of the operation, modeled explicitly so the spec can
   pin exactly when it does and does NOT occur. -/
inductive Crash where
  | indexOOB
  deriving DecidableEq
-- axioms-end

-- pure-start
/- The recognised filename extensions that mark a candidate of the format under
   classification (the lowercase suffixes the path test accepts). -/
def knownExts : List (List Char) :=
  [".fits".toList, ".fits.gz".toList, ".fit".toList,
   ".fit.gz".toList, ".fts".toList, ".fts.gz".toList]

/- Whether a path's code-point sequence ends, case-insensitively, in one of the
   recognised extensions: lowercase the path, then test it against each known
   suffix. Deep model (an A-reference, mapping.md §3.1) of the unchanged
   case-folding suffix test the path branch performs; validated == the real
   `.lower().endswith((...))` by axiom_check.py (G-AX). -/
def hasKnownExt (path : List Char) : Bool :=
  knownExts.any (fun ext => ext.isSuffixOf (path.map Char.toLower))

/- The intended outcome of the whole classification, as `Except Crash Bool`
   (`error` = the absent-observation failure escapes, `ok b` = a verdict `b` is
   returned):

     * if a readable stream observation is present, its signature verdict is
       returned verbatim;
     * otherwise, if a path is present, the verdict is the case-insensitive
       known-extension test of that path — returned UNCONDITIONALLY, whether the
       test holds or not (the desired behavior the public problem statement
       demands: a present path always yields a verdict and never falls through to
       inspecting a trailing positional observation);
     * otherwise (neither stream nor path present), the first trailing positional
       observation is the verdict — and if there is none, the absent-observation
       failure escapes.

   Only the third branch may fail; a present path can never make it fail. -/
def originSpec (stream : Option Bool) (path : Option (List Char))
    (extra : List Bool) : Except Crash Bool :=
  match stream with
  | some s => Except.ok s
  | none =>
    match path with
    | some p => Except.ok (hasKnownExt p)
    | none =>
      match extra with
      | []     => Except.error Crash.indexOOB
      | a :: _ => Except.ok a
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Classify whether an origin denotes a file of the format under recognition.

   Desired behavior: the classifier is consulted with, in order, a readable
   stream observation, a path, and a trailing sequence of positional
   observations. A present stream observation yields its signature verdict. When
   no stream is present but a PATH is, the classifier must return the path's
   case-insensitive known-extension verdict OUTRIGHT — for every path, matching
   or not — and must never proceed to read a trailing positional observation
   (the missing behavior the public problem statement reports: a path-only call
   on a non-matching name must return a plain `false`, not let an
   absent-observation failure escape). Only when NEITHER a stream nor a path is
   present is the first trailing positional observation consulted; if that
   sequence is empty the absent-observation failure escapes.

   `stream`, `path`, and `extra` are read-only (none is `mut`): the classifier
   computes a verdict and mutates no input (directive 5). The stream's signature
   comparison is collapsed to its boolean observation and each positional
   argument to its boolean class-membership observation (mapping.md §2). -/
method classifyFitsOrigin (stream : Option Bool) (path : Option (List Char))
    (extra : List Bool) return (out : Except Crash Bool)
  ensures out = originSpec stream path extra
  do
    -- impl-start
    -- Pre-image skeleton: when a path is present its known-extension test only
    -- short-circuits to a positive verdict; a NON-matching path falls THROUGH to
    -- read the first trailing positional observation (and the absent-observation
    -- failure escapes when the sequence is empty). The frozen spec requires a
    -- present path to yield its verdict outright, so prove_correct MUST fail.
    let result : Except Crash Bool :=
      match stream with
      | some s => Except.ok s
      | none =>
        match path with
        | some p =>
            if hasKnownExt p then Except.ok true
            else
              match extra with
              | []     => Except.error Crash.indexOOB
              | a :: _ => Except.ok a
        | none =>
          match extra with
          | []     => Except.error Crash.indexOOB
          | a :: _ => Except.ok a
    return result
    -- impl-end

prove_correct classifyFitsOrigin by
  loom_solve
  simp_all [originSpec]
