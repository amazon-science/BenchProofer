import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The operation under
-- specification is the selection of a response content type from a guessed
-- (type, compression-encoding) pair; it is modeled DEEPLY (the concrete
-- encoding→type association plus the absent/empty fallback below) rather than
-- abstracted behind any callee. The routine that produces the guessed pair from
-- a name sits at the input boundary (it supplies the two arguments) and is not
-- part of the modeled computation. The proof agent may add `_prop` axioms only
-- if it gets stuck.
-- axioms-end

-- pure-start
/-- The content type associated with a known compression encoding. For every
recognized compression scheme this is the encoding's own dedicated media type
(so that the payload is described as the compressed archive it actually is,
rather than as the underlying file); any other encoding has no associated
override. Grounded entirely in the encoding string. -/
def encodingContentType (e : String) : Option String :=
  if e = "br" then some "application/x-brotli"
  else if e = "bzip2" then some "application/x-bzip"
  else if e = "compress" then some "application/x-compress"
  else if e = "gzip" then some "application/gzip"
  else if e = "xz" then some "application/x-xz"
  else none

/-- The final content type chosen for a guessed `(contentType, encoding)` pair.
When the encoding is a known compression scheme, its dedicated media type takes
precedence over the guessed type; otherwise the guessed type is used. In all
cases an absent or empty result is replaced by the generic binary media type.
Grounded entirely in the two input components. -/
def finalContentType (contentType encoding : Option String) : String :=
  let overridden : Option String :=
    match encoding with
    | none => contentType
    | some e =>
        match encodingContentType e with
        | some v => some v
        | none => contentType
  match overridden with
  | some s => if s.isEmpty then "application/octet-stream" else s
  | none => "application/octet-stream"
-- pure-end

-- post-conditions-start
/-- The resulting content type is exactly the type selected for the guessed
`(contentType, encoding)` pair: a known compression encoding's dedicated media
type overrides the guessed type, an unrecognized or absent encoding keeps the
guessed type, and an absent or empty selection falls back to the generic binary
media type. -/
def problem_spec_contentType
    (contentType encoding : Option String) (result : String) : Prop :=
  result = finalContentType contentType encoding
-- post-conditions-end

-- impl-start
/-- Pre-patch (buggy): only a subset of the compression encodings carry a
dedicated media type override. Several recognized compression schemes are
missing from the association, so for those a payload keeps the guessed type of
the underlying file instead of being described as the compressed archive it is. -/
def implementation_contentType (contentType encoding : Option String) : String := Id.run do
  let mut ct := contentType
  if let some e := encoding then
    if e = "bzip2" then ct := some "application/x-bzip"
    else if e = "gzip" then ct := some "application/gzip"
    else if e = "xz" then ct := some "application/x-xz"
  match ct with
  | some s => return (if s.isEmpty then "application/octet-stream" else s)
  | none => return "application/octet-stream"
-- impl-end

-- proof-start
theorem correct_contentType :
    ∀ (contentType encoding : Option String),
    problem_spec_contentType contentType encoding
      (implementation_contentType contentType encoding) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
