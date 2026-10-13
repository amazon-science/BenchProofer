import Mathlib
-- imports-end

/-!
Building the target URL a browser is sent to when it requests an existing
resource but omits the trailing slash that the resource canonically carries.

The redirect target is assembled from the requested path together with the
query string that accompanied the original request, in three pieces:

  * the requested path, run through a standard percent-encoder for URI paths so
    that any characters outside the safe ASCII path range are escaped;
  * a single trailing slash, added only when the path does not already end in
    one (so a path that is already slash-terminated is not given a second);
  * the original query string, re-attached verbatim after a `?` separator and
    run through a standard URI query encoder — but only when a non-empty query
    string was present; when there was none, nothing is appended.

The essential property is that the query string is preserved across the
redirect: a request carrying `?...` is sent to a target that still carries the
same `?...`, rather than to a target with the query component discarded.
-/

-- axioms-start
-- Two unchanged standard URI encoders are reused while assembling the target
-- URL; their internal behavior is irrelevant to the assembly logic, so they
-- enter as opaque leaf operations (deep-model references, validated to equal
-- the real encoders by the executable callee check). The first escapes a path
-- string into the safe URI-path character range; the second encodes a query
-- string into the safe URI-query range. No property of either is consumed by
-- the proof: they appear identically in the specification and the
-- implementation, so the correctness statement holds for ANY such encoders.
opaque escapePathComponent : String → String
opaque encodeQueryString : String → String
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The redirect target is fully pinned to the two inputs (the requested path
and the accompanying query string). It is exactly the concatenation of:

  * the percent-escaped path,
  * a trailing slash when the path is not already slash-terminated (otherwise
    the empty string), and
  * the re-encoded query string introduced by `?` when a non-empty query string
    was present (otherwise the empty string).

Every component of the result is determined by the inputs — no part is left
free — and the query string, when present, is necessarily carried into the
target. -/
def problem_spec_redirectTargetWithTrailingSlash
    (path queryString : String) (result : String) : Prop :=
  result =
    escapePathComponent path
      ++ (if path.endsWith "/" then "" else "/")
      ++ (if queryString = "" then "" else "?" ++ encodeQueryString queryString)
-- post-conditions-end

-- impl-start
def implementation_redirectTargetWithTrailingSlash
    (path queryString : String) : String := Id.run do
  let escapedPath := escapePathComponent path
  let trailingSlash := if path.endsWith "/" then "" else "/"
  let querySuffix := if queryString = "" then "" else "?" ++ encodeQueryString queryString
  return escapedPath ++ trailingSlash ++ querySuffix
-- impl-end

-- proof-start
theorem correct_redirectTargetWithTrailingSlash :
    ∀ (path queryString : String),
      problem_spec_redirectTargetWithTrailingSlash path queryString
        (implementation_redirectTargetWithTrailingSlash path queryString) := by
  intro path queryString
  unfold problem_spec_redirectTargetWithTrailingSlash implementation_redirectTargetWithTrailingSlash
  rfl
-- proof-end
