import Mathlib
-- imports-end

/-!
Letting the `source-read` transformation reach the text of an included file.

A documentation source file can pull in the contents of another file. The text
that is pulled in arrives as a list of physical lines; in addition to the
included content, the line list carries two trailing *marker* lines that the
surrounding machinery uses to track provenance and must be kept intact.

Independently, the build exposes a `source-read` hook: a registered
transformation that is offered the text of a source document and may rewrite it
before it is parsed. The desired behaviour is that, **when such a hook is
registered**, the text of an included file is also offered to that hook and the
(possibly rewritten) text is what gets parsed — included content must not bypass
the hook.

Concretely, when a hook is registered the inclusion proceeds as follows:

  * the trailing two marker lines are set aside; the remaining lines are joined
    back into a single block of text (the *body*);
  * the hook is offered that body, tagged with the document name derived from the
    included file's path;
  * the body the hook returns is split back into lines and the two marker lines
    are re-appended, and this is the line list that is finally parsed.

When no hook is registered the line list is parsed unchanged and no text is
offered to the hook. The marker lines are never themselves offered to the hook,
and are always preserved unchanged at the end of the result.
-/

-- axioms-start
/-- The document name derived from an included file's path. This derivation is
an existing, unchanged path-normalising step; only its result enters the
behaviour modeled here (it is the tag carried alongside the offered text), so it
is declared as an opaque carrier with no assumed properties. -/
opaque pathToDocname : String → String
-- axioms-end

-- pure-start
/-- Join a list of lines back into a single block of text, lines separated by a
newline (the inverse of the line split below). -/
def joinLines (lines : List String) : String :=
  String.intercalate "\n" lines

/-- The universal line-boundary characters recognised when splitting text into
physical lines: LF, CR, VT, FF, FS, GS, RS, NEL, LINE SEPARATOR and PARAGRAPH
SEPARATOR. (A CR immediately followed by LF counts as a single boundary; that
pair is handled by the splitter itself.) -/
def isLineBoundary (c : Char) : Bool :=
  c = '\n' || c = '\r' || c = '\x0b' || c = '\x0c' ||
  c = '\x1c' || c = '\x1d' || c = '\x1e' || c = '\x85' ||
  c = ' ' || c = ' '

/-- Core of the line split, over the character list: cut at every universal line
boundary (a CR immediately followed by LF is one boundary, not two); a boundary
that ends the text does not open a further (empty) line. `acc` holds the current
line's characters in reverse. -/
def splitLinesGo : List Char → List Char → List (List Char)
  | [], acc => [acc.reverse]
  | '\r' :: '\n' :: rest, acc =>
      if rest.isEmpty then [acc.reverse]
      else acc.reverse :: splitLinesGo rest []
  | c :: rest, acc =>
      if isLineBoundary c then
        if rest.isEmpty then [acc.reverse]
        else acc.reverse :: splitLinesGo rest []
      else
        splitLinesGo rest (c :: acc)

/-- Split a block of text into physical lines, matching the line-splitting used
when re-expanding the (possibly rewritten) text: the split cuts at every
universal line boundary (LF, CR, CRLF, VT, FF, FS, GS, RS, NEL, LINE SEPARATOR,
PARAGRAPH SEPARATOR); the empty text yields no lines; a trailing boundary does
not produce a spurious final empty line. -/
def splitLines (s : String) : List String :=
  if s = "" then []
  else (splitLinesGo s.toList []).map String.mk

/-- What the inclusion produces, as observed downstream:
* `emitted` — the payload offered to the `source-read` hook: the document name
  and the body text, or `none` when no hook is registered;
* `outputLines` — the physical line list that is finally parsed. -/
structure InsertOutcome where
  emitted : Option (String × String)
  outputLines : List String
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The inclusion result, pinned at both observable components.

When a hook is registered, the body is the included lines with the trailing two
marker lines removed and joined into text; that body (tagged with the document
name derived from `path`) is what is offered to the hook; and the parsed line
list is the hook's rewritten body re-split into lines with the two marker lines
re-appended unchanged. When no hook is registered, nothing is offered and the
line list is parsed exactly as received.

`srcRead` models the net effect of the registered `source-read` transformation
on a block of text. -/
def problem_spec_includedSource
    (hasListeners : Bool) (srcRead : String → String)
    (path : String) (lines : List String)
    (result : InsertOutcome) : Prop :=
  let body := joinLines (lines.take (lines.length - 2))
  let markers := lines.drop (lines.length - 2)
  (result.emitted =
      (if hasListeners then some (pathToDocname path, body) else none))
  ∧ (result.outputLines =
      (if hasListeners then splitLines (srcRead body) ++ markers else lines))
-- post-conditions-end

-- impl-start
def implementation_includedSource
    (hasListeners : Bool) (srcRead : String → String)
    (path : String) (lines : List String) : InsertOutcome := Id.run do
  -- Pre-patch behaviour: the inclusion does NOT hook into the `source-read`
  -- transformation. The included line list is parsed exactly as received and no
  -- text is ever offered to the hook — even when a hook is registered, the
  -- included content bypasses it.
  return { emitted := none, outputLines := lines }
-- impl-end

-- proof-start
theorem correct_includedSource :
    ∀ (hasListeners : Bool) (srcRead : String → String)
      (path : String) (lines : List String),
      problem_spec_includedSource hasListeners srcRead path lines
        (implementation_includedSource hasListeners srcRead path lines) := by
  -- Gold proof body carried over from Solution.lean: it closes the POST-patch
  -- impl but cannot typecheck against this buggy (no-interception) impl, so
  -- verification of the prepatch fails — exactly the G-DIFF signal.
  intro hasListeners srcRead path lines
  unfold problem_spec_includedSource implementation_includedSource
  cases hasListeners <;> exact ⟨rfl, rfl⟩
-- proof-end
