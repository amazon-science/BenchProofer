import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The two URL percent-encoders this construction relies on
   are unchanged community helpers; rather than axiomatize them (they are not
   what this specification pins, and would not be code-generable inside the
   executable body), their outputs are refined directly into the input carrier
   (`encodedPath` / `encodedQuery` are the already-encoded character sequences).
   The bijection is stated in mapping.md §2 and validated executably by
   axiom_check.py (G-AX). -/
-- axioms-end

-- pure-start
/- The redirect destination that guarantees a trailing slash while preserving an
   existing query string, assembled from the encoded request path and the
   encoded query string:

     * the encoded path, then
     * a single '/' appended exactly when the path does not already end in one,
       then
     * when a query string is present, that query preserved after a '?'
       separator.

   This is a deep model of the standard request-destination builder (an
   unchanged community helper); `redirectTarget == that builder` is validated by
   axiom_check.py (G-AX), so it is an A-reference, not a consumed axiom. The
   preservation of the query-string component is the behaviour this
   specification pins. -/
def redirectTarget (encodedPath : List Char) (encodedQuery : List Char) : List Char :=
  encodedPath
    ++ (if encodedPath.getLast? = some '/' then ([] : List Char) else ['/'])
    ++ (if encodedQuery = [] then ([] : List Char) else '?' :: encodedQuery)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method appendSlashRedirect (encodedPath : List Char) (encodedQuery : List Char)
    return (out : List Char)
  ensures out = redirectTarget encodedPath encodedQuery
  do
    -- impl-start
    let slash : List Char :=
      if encodedPath.getLast? = some '/' then ([] : List Char) else ['/']
    let query : List Char :=
      if encodedQuery = [] then ([] : List Char) else '?' :: encodedQuery
    let result := encodedPath ++ slash ++ query
    return result
    -- impl-end

prove_correct appendSlashRedirect by
  loom_solve
  simp [redirectTarget]
