import Mathlib
-- imports-end

/-!
Resolving a language code from the leading segment of a URL path.

A URL path may carry a language tag as its first path component. A well-formed
language tag is a primary subtag optionally followed by further subtags, each
introduced by a separator (`-` or `@`): per RFC 5646 a tag is a language
optionally followed by a script and a region (`language[-script][-region]`),
so up to two such trailing subtags are admissible. The candidate tag is the
maximal such prefix delimited by a `/` or the end of the path (the end-of-input
delimiter also admits one trailing line terminator); if the leading component
is not a well-formed tag the path carries no language code. A recognised
candidate is then mapped to the best supported language variant.

Modeled domain: the tag grammar is characterised concretely on paths over the
ASCII plane (every code point below 128); the langtag grammar and every
supported language code are ASCII. Outside ASCII the word-character
classification of the real matcher is library-specific, so on such paths the
result is pinned only to the (unspecified, deterministic) outcome of the real
routine, exposed by signature alone.
-/

-- axioms-start
/-- Map a candidate language tag to the supported language variant it selects,
or `none` when no supported variant matches. This is an unchanged library
routine, exposed here only by signature: it returns the candidate itself when it
names a supported variant, otherwise a more generic supported variant, otherwise
`none`. (Its "not found" outcome is modelled by `none` rather than an
exception.) -/
opaque resolveVariant : List Char → Option (List Char)

/-- The routine's outcome on a path that carries a code point outside the ASCII
plane. There the word-character classification of the real matcher is
library-specific, so the behaviour is exposed by signature only: an
unspecified, deterministic function of the path, with no properties asserted. -/
opaque nonAsciiOutcome : List Char → Option (List Char)
-- axioms-end

-- pure-start
/-- A "word" character of a language tag: an ASCII letter, an ASCII digit, or
the underscore. -/
def isWord (c : Char) : Bool := c.isAlpha || c.isDigit || c = '_'

/-- A subtag separator: a hyphen or an at-sign. -/
def isSep (c : Char) : Bool := c = '-' || c = '@'

/-- Greedily consume up to `n` trailing subtags from `cs`. Each subtag is a
separator immediately followed by a non-empty run of word characters. Returns
the consumed characters (separators included) together with the unconsumed
remainder. Consumption stops early if the next character is not a separator, or
if a separator is not followed by at least one word character. -/
def grabSubtags : Nat → List Char → (List Char × List Char)
  | 0, rest => ([], rest)
  | _ + 1, [] => ([], [])
  | n + 1, c :: rest =>
      if isSep c then
        match rest.span isWord with
        | (w, r) =>
            if w = [] then ([], c :: rest)
            else
              match grabSubtags n r with
              | (more, r2) => (c :: (w ++ more), r2)
      else ([], c :: rest)

/-- Extract the candidate language tag that prefixes `path`, allowing at most
`n` trailing subtags. The path must begin with `/`; the primary subtag is a
non-empty maximal run of word characters; up to `n` further subtags may follow;
and the candidate must be terminated by a `/` or the end of the path, where
the end-of-path delimiter also admits a single trailing line-terminator
(the end-of-input anchor convention of the host pattern language). Returns
`none` when no such prefix exists. -/
def langPrefixN (n : Nat) (path : List Char) : Option (List Char) :=
  match path with
  | '/' :: rest =>
      match rest.span isWord with
      | (seg0, r0) =>
          if seg0 = [] then none
          else
            match grabSubtags n r0 with
            | (subs, rrest) =>
                match rrest with
                | [] => some (seg0 ++ subs)
                | '/' :: _ => some (seg0 ++ subs)
                | ['\n'] => some (seg0 ++ subs)
                | _ => none
  | _ => none

/-- The admissible candidate language tag prefixing `path`: a primary subtag
optionally followed by up to two trailing subtags (script and region). -/
def langPrefix (path : List Char) : Option (List Char) := langPrefixN 2 path

/-- Whether every code point of the path lies in the ASCII plane (value below
128). -/
def allAscii (path : List Char) : Bool :=
  path.all (fun c => decide (c.toNat < 128))
-- pure-end

-- post-conditions-start
/-- The resolved language code for a URL path. For an all-ASCII path there is a
recognised supported variant exactly when the path begins with a well-formed
candidate tag (primary subtag plus up to two trailing subtags) whose value
resolves to a supported variant; the result is that variant, and `none`
whenever either the path has no admissible candidate prefix or the candidate
resolves to no supported variant. For a path carrying a code point outside the
ASCII plane the result is exactly the routine's outcome on it (the matcher's
word class there is library-specific, so that outcome is exposed by signature
only). -/
def problem_spec_langCodeFromPath
    (path : List Char) (result : Option (List Char)) : Prop :=
  result = (if allAscii path then
              match langPrefix path with
              | none => none
              | some lc => resolveVariant lc
            else nonAsciiOutcome path)
-- post-conditions-end

-- impl-start
def implementation_langCodeFromPath (path : List Char) : Option (List Char) :=
  Id.run do
    if allAscii path then
      match langPrefixN 1 path with
      | none => return none
      | some lc => return resolveVariant lc
    else
      return nonAsciiOutcome path
-- impl-end

-- proof-start
theorem correct_langCodeFromPath : ∀ (path : List Char),
    problem_spec_langCodeFromPath path (implementation_langCodeFromPath path) := by
  sorry   -- carries the gold proof intent; UNCLOSABLE against this impl (G-DIFF)
-- proof-end
