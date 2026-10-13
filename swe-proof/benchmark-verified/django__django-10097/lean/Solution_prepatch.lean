import Mathlib
-- imports-end

/-!
Deciding whether the credentials portion of a URL — the `user` or
`user:password` segment that precedes the `@` in an authority — is well-formed.

A URL authority may optionally carry credentials. When present, that segment is
made of a *user* part and an optional *password* part separated by a single
colon. RFC 1738 §3.1 requires that, within these two parts, the delimiter
characters (`":"`, `"@"`, `"/"`) and whitespace never appear literally; they
must be percent-encoded to be carried. Hence the only characters admissible in
the user and password parts are those that are neither whitespace nor one of
those delimiters.

A credentials segment is therefore acceptable exactly when:

* it is non-empty;
* it does not begin with a colon (the user part must be present);
* it contains at most one colon (the single `user`/`password` separator);
* every remaining character is one of the admissible characters described above.

A single embedded colon acts purely as the user/password separator; the password
part it introduces may be empty. Any occurrence of whitespace, `"@"`, `"/"`, or a
second colon makes the segment inadmissible.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The character
-- admissibility test and the single-separator structure are modeled DEEPLY over
-- the observable input (the list of characters of the credentials segment), so
-- no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A character admissible inside the user or password part of a URL's
credentials: neither whitespace nor one of the reserved delimiters `:`, `@`, `/`.

Whitespace here means exactly the 29 code points matched by Python's `re` `\s`
class over Unicode `str` input (the validator receives arbitrary Unicode text):
the ASCII whitespace `\t` `\n` `\v` `\f` `\r` and space, the information
separators U+001C–U+001F, NEL (U+0085), NBSP (U+00A0), OGHAM SPACE MARK
(U+1680), the fixed-width spaces U+2000–U+200A, LINE/PARAGRAPH SEPARATOR
(U+2028/U+2029), NARROW NBSP (U+202F), MEDIUM MATHEMATICAL SPACE (U+205F) and
IDEOGRAPHIC SPACE (U+3000). Lean's `Char.isWhitespace` covers only four of
these, so the class is spelled out by code point to stay faithful to
`[^\s:@/]`. -/
def isUserinfoWhitespace (c : Char) : Bool :=
  let n := c.toNat
  (0x9 ≤ n && n ≤ 0xd) || n == 0x20 || (0x1c ≤ n && n ≤ 0x1f) ||
  n == 0x85 || n == 0xa0 || n == 0x1680 ||
  (0x2000 ≤ n && n ≤ 0x200a) || n == 0x2028 || n == 0x2029 ||
  n == 0x202f || n == 0x205f || n == 0x3000

def isUserinfoChar (c : Char) : Bool :=
  !isUserinfoWhitespace c && c != ':' && c != '@' && c != '/'

/-- Whether the credentials segment `s` (the characters before the authority's
`@`, with the `@` itself excluded) is well-formed: non-empty, not starting with
a colon, carrying at most one colon separator, and otherwise built only from
admissible characters. -/
def urlUserinfoValid (s : List Char) : Bool :=
  if s.isEmpty then false
  else if s.head? == some ':' then false
  else if !Nat.ble (s.count ':') 1 then false
  else if !(s.all (fun c => isUserinfoChar c || c == ':')) then false
  else true
-- pure-end

-- post-conditions-start
/-- The decision returned for a credentials segment is exactly the well-formedness
verdict dictated by the rule above. -/
def problem_spec_urlUserinfoValid (s : List Char) (result : Bool) : Prop :=
  result = urlUserinfoValid s
-- post-conditions-end

-- impl-start
def implementation_urlUserinfoValid (s : List Char) : Bool := Id.run do
  -- Pre-patch behaviour: the credentials segment was matched by `\\S+(?::\\S*)?`,
  -- i.e. any non-empty run of non-whitespace characters was accepted, with the
  -- reserved delimiters treated as ordinary characters.
  if s.isEmpty then return false
  if !(s.all (fun c => !isUserinfoWhitespace c)) then return false
  return true
-- impl-end

-- proof-start
theorem correct_urlUserinfoValid :
    ∀ (s : List Char),
      problem_spec_urlUserinfoValid s (implementation_urlUserinfoValid s) := by
  intro s
  rfl
-- proof-end
