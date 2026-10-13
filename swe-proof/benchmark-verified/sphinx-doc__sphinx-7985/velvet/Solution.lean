import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The two facts the verdict depends on besides the link
   text itself — whether a file with that name is present under the source tree,
   and whether the link text matches any of the configured skip patterns — are
   unchanged community components, observed only as the boolean inputs
   `fileExists` and `anyIgnore` (their results are method inputs, so no axiom is
   needed, mapping.md §3). The one callee whose behaviour is modeled is the
   scheme detector `hasUriScheme`, modeled DEEPLY (an A-reference, validated ==
   the real callee by axiom_check.py / G-AX), not assumed behind an axiom. -/
-- axioms-end

-- pure-start
/- The verdicts a non-network link can receive. `unchecked` skips it without
   contacting anything; `working` marks a target that resolves and `missing`
   marks one that does not; `ignored` is a deliberately-skipped match;
   `localLink` is the legacy blanket verdict that recorded a non-network link
   without ever resolving it. -/
inductive Status
  | unchecked
  | working
  | ignored
  | missing
  | localLink
deriving DecidableEq, Repr

/- The length of the maximal run of ASCII lowercase letters at the front of a
   string. Front-recursive so it reduces one code point at a time. -/
def lowerRun : List Char → Nat
  | []      => 0
  | c :: cs => if 'a' ≤ c ∧ c ≤ 'z' then 1 + lowerRun cs else 0

/- Whether the link text opens with an explicit access-method marker: one or
   more ASCII lowercase letters immediately followed by the `://` separator
   (e.g. an `ftp://…` address). Deep model (A-reference) of the access-method
   detector; validated == the real detector by axiom_check.py (G-AX). -/
def hasUriScheme (uri : List Char) : Bool :=
  decide (lowerRun uri ≥ 1) && List.isPrefixOf "://".toList (uri.drop (lowerRun uri))

/- Whether the link text is one that is skipped without any resolution attempt:
   it is empty, an in-page fragment reference, or a mail address. Concrete
   transliteration of the leading-marker test (identical op). -/
def isUnchecked (uri : List Char) : Bool :=
  uri.isEmpty || List.isPrefixOf "#".toList uri || List.isPrefixOf "mailto:".toList uri

/- Whether the link text is a web address handled by the network branch.
   Concrete transliteration of the leading-marker test (identical op). -/
def isHttp (uri : List Char) : Bool :=
  List.isPrefixOf "http:".toList uri || List.isPrefixOf "https:".toList uri

/- The verdict for a non-network link, as a function of the link text and the
   two environment observations (`fileExists`: a file of that name is present
   under the source tree; `anyIgnore`: the text matches a configured skip
   pattern). Desired behaviour: a skip-without-resolution link is `unchecked`;
   a link carrying an explicit unsupported access-method marker is also
   `unchecked`; otherwise the link names a local target that MUST be resolved —
   present file ⇒ `working`, else a configured skip ⇒ `ignored`, else the target
   is absent ⇒ `missing`. A non-network link is therefore never left as the
   blanket `localLink` verdict. -/
def classify (uri : List Char) (fileExists anyIgnore : Bool) : Status :=
  if isUnchecked uri then Status.unchecked
  else
    (if hasUriScheme uri then Status.unchecked
     else
       (if fileExists then Status.working
        else
          (if anyIgnore then Status.ignored
           else Status.missing)))
-- pure-end

-- pre-conditions-start
-- (one block per modeled method; this method's only precondition scopes it to
--  the non-network branch — the network branch is handled elsewhere.)
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Classify a non-network link. `uri` is the link text; `fileExists` records
   whether a file of that name is present under the source tree; `anyIgnore`
   records whether the text matches any configured skip pattern. The desired
   behaviour is `classify`: skip-without-resolution and explicit unsupported
   access-method links are `unchecked`; every other (local) target is resolved
   to `working`/`ignored`/`missing` rather than being recorded under the blanket
   non-resolving verdict. `uri`, `fileExists`, `anyIgnore` are read-only: the
   method returns a fresh verdict and never mutates its inputs (directive 5). -/
method classifyLocalLink (uri : List Char) (fileExists : Bool) (anyIgnore : Bool)
    return (out : Status)
  require isHttp uri = false
  ensures out = classify uri fileExists anyIgnore
  do
    -- impl-start
    -- A skip-without-resolution link is left unchecked; a link opening with an
    -- explicit unsupported access-method marker is likewise unchecked; any other
    -- link names a local target and is resolved — present file ⇒ working, else a
    -- configured skip ⇒ ignored, else the target is absent ⇒ missing.
    let out : Status :=
      if isUnchecked uri then Status.unchecked
      else
        (if hasUriScheme uri then Status.unchecked
         else
           (if fileExists then Status.working
            else
              (if anyIgnore then Status.ignored
               else Status.missing)))
    return out
    -- impl-end

prove_correct classifyLocalLink by
  loom_solve
  simp only [classify]
