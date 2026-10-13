import Mathlib
-- imports-end

-- axioms-start
-- No unchanged-callee axioms are consumed: the two primitives a deletion and its
-- configured call sites go through -- the cookie write, and the marking that records
-- which request fields a response's content depends on -- are modeled DEEPLY as the
-- pure helpers `setCookie` and `varyMarked` below (A-references, validated against
-- the real callees by G-AX), not axiomatized.
-- axioms-end

-- pure-start

/-- EVERY component one stored cookie carries: the two components the container
RENDERS the entry under, and the ten attributes it can hold. The entry a write leaves
behind is therefore observed in full rather than through a projection of it -- a
component the model omitted would be one a write could stamp unobserved, and every
component a stored cookie carries is rendered into what the client is sent.

`key` is the name the entry is RENDERED under and `codedValue` is the payload it is
RENDERED with: the container emits `key=codedValue` ahead of every attribute. Neither
is the same thing as the name the container FILES the entry under -- that is the
container's own index, and an entry can be filed under one name and rendered under
another -- and `codedValue` is not the same thing as `value`, the payload the entry
reads back: the rendered payload is the reading-back payload ENCODED, so an entry can
read back an empty payload while rendering a non-empty one.

`value` is the payload as read back; `expires`, `path`, `domain`, `samesite`,
`comment` and `version` use the empty string for "attribute unset"; `maxAge` is `none`
for an entry that records no lifetime at all and `some n` for one that records a
lifetime of `n`, which are different entries and are rendered differently; `secure` and
`httpOnly` are flags that stay off unless set. -/
structure Cookie where
  key        : String
  value      : String
  codedValue : String
  maxAge     : Option Nat
  expires    : String
  path       : String
  domain     : String
  secure     : Bool
  httpOnly   : Bool
  samesite   : String
  comment    : String
  version    : String
deriving Repr, DecidableEq

/-- The entry a name gets when a container first stores a cookie under it: every
attribute at the container's own default, and in particular no recorded lifetime. The
rendered name and the rendered payload are the two components a write ALWAYS stamps and
NEVER merges -- every write re-stamps the entry's name, payload and rendered payload
together -- so this default entry is never consulted for them, and the empty strings
here are placeholders no write can read. -/
def defaultCookie : Cookie :=
  { key := "", value := "", codedValue := "", maxAge := none, expires := "",
    path := "", domain := "", secure := false, httpOnly := false, samesite := "",
    comment := "", version := "" }

/-- A response's cookie container: the cookie stored under each name, or `none` for a
name the response stores no cookie under. The container -- not one cookie in isolation
-- is what a cookie write is observed through, because the whole effect of a write is
on the container the response is left holding. So the container records WHICH name was
written, WHAT that entry ended up holding, and what happened to the names beside it;
and two writes to one name are observed at the state the second of them left. -/
abbrev CookieJar := String → Option Cookie

/-- Everything about a response that a routine acting on it can be observed to change:
the cookies it carries, the request fields its content is declared to depend on (the
empty list for a response that declares none), the value of every other header field it
carries (the empty string for a field it does not carry), its status, and its body. The
whole response is carried, not just the cookies, so that what a routine did NOT do to
it is observable too: a routine's effect on a response includes the headers, status and
body it left alone. -/
structure Response where
  cookies : CookieJar
  varies  : List String
  headers : String → String
  status  : Nat
  body    : String

/-- A response carrying no cookies, declaring no dependency, carrying no header field,
with the ordinary status and an empty body. -/
def emptyResponse : Response :=
  { cookies := fun _ => none, varies := [], headers := fun _ => "",
    status := 200, body := "" }

/-- What the entry named `key` already holds, or the container's default entry when the
container holds no cookie under that name. -/
def storedOrDefault (jar : CookieJar) (key : String) : Cookie :=
  (jar key).getD defaultCookie

/-- Where a `maxAge` argument lands: a write records a lifetime only when one is
supplied at all, and otherwise leaves the entry the lifetime it already carried. So an
entry no write ever supplied a lifetime for records none, which is NOT the same entry
as one a write recorded the lifetime zero on -- the two are rendered differently, one
stating a lifetime and one stating nothing. -/
def maxAgeAfter (jar : CookieJar) (key : String) (maxAge : Option Nat) : Option Nat :=
  match maxAge with
  | some n => some n
  | none   => (storedOrDefault jar key).maxAge

/-- Where a `domain` argument lands: a write records a domain only when one is supplied
at all, and otherwise leaves the entry the domain it already carried. -/
def domainAfter (jar : CookieJar) (key : String) (domain : Option String) : String :=
  domain.getD (storedOrDefault jar key).domain

/-- Where a `samesite` argument lands: a write records a policy only when that policy
is truthy (supplied and non-empty), and otherwise leaves the entry the policy it
already carried. -/
def samesiteAfter (jar : CookieJar) (key : String) (samesite : Option String) : String :=
  match samesite with
  | some s => if s = "" then (storedOrDefault jar key).samesite else s
  | none   => (storedOrDefault jar key).samesite

/-- Where a `secure` argument lands: a write can only ADD the marking, never clear one
the entry already carried, because the marking is written only when it is asked for. -/
def secureAfter (jar : CookieJar) (key : String) (flag : Bool) : Bool :=
  flag || (storedOrDefault jar key).secure

/-- Where an `httpOnly` argument lands: as with `secure`, a write can only add the
marking and never clear one the entry already carried. -/
def httpOnlyAfter (jar : CookieJar) (key : String) (flag : Bool) : Bool :=
  flag || (storedOrDefault jar key).httpOnly

/-- The characters the container admits literally. This is ONE alphabet serving two
purposes: it is the alphabet a name a cookie may be stored under is built from, and it
is also the alphabet a payload must lie entirely within to be rendered as itself rather
than quoted. -/
def cookieNameChar (c : Char) : Bool :=
  c.isAlphanum || c ∈ ['!', '#', '$', '%', '&', '\'', '*', '+', '-', '.', '^',
                       '_', '`', '|', '~', ':']

/-- The characters the container renders literally INSIDE a quoted payload: the admitted
alphabet, plus the printable punctuation it does not escape. -/
def cookieUnescapedChar (c : Char) : Bool :=
  cookieNameChar c ||
    c ∈ [' ', '(', ')', '/', '<', '=', '>', '?', '@', '[', ']', '{', '}']

/-- One octal digit, as the character the container writes it as. -/
def octalDigit (n : Nat) : Char := Char.ofNat (48 + n % 8)

/-- The escape the container writes a byte it will not render literally as: a backslash
and exactly three octal digits. -/
def octalEscape (n : Nat) : String :=
  String.mk ['\\', octalDigit (n / 64), octalDigit (n / 8), octalDigit n]

/-- How one character of a payload is rendered inside a quoted payload: the quote mark
and the backslash -- the two characters that would otherwise end or hijack the quoting
-- are backslash-escaped; anything in the unescaped alphabet is rendered as itself;
every other BYTE is written as its three-digit octal escape; and a character beyond the
byte range has no escape at all and is rendered as itself. -/
def quoteChar (c : Char) : String :=
  if c = '"' then "\\\""
  else if c = '\\' then "\\\\"
  else if cookieUnescapedChar c || 256 ≤ c.toNat then c.toString
  else octalEscape c.toNat

/-- How a payload is ENCODED into the payload the entry is rendered with. A payload that
is non-empty and lies entirely within the admitted alphabet is rendered as itself;
anything else is rendered QUOTED, with each character escaped as above. The EMPTY
payload is not an admitted payload, so it is rendered as the two-character quoted empty
payload `""` -- which is NOT the empty string. That is exactly the payload a deletion
writes, so a deletion's entry reads back nothing and renders `""`, and the two are
different bytes: an entry whose rendered payload were the empty string, or anything
else, would put a different line on the wire. -/
def valueEncode (v : String) : String :=
  if v != "" && v.data.all cookieNameChar then v
  else "\"" ++ String.join (v.data.map quoteChar) ++ "\""

/-- Writing a cookie: afterwards the container's entry named `key` -- and no other
entry -- is RENDERED under that same name and with the supplied payload's encoding,
carries the supplied payload, expiry stamp and path, records the supplied lifetime,
domain, policy and markings under the rules above, and keeps the two attributes a write
has no argument for (`comment`, `version`) exactly as the entry already had them,
because a write updates the entry in place rather than replacing it. The three
components a write STAMPS rather than merges are the rendered name, the payload and the
rendered payload: the write files the entry under the name it was given AND re-stamps
the entry's own name to it, so after a write the index and the rendered name agree --
which is a fact about the write, not a coincidence of the model, and it is why an impl
that moves either one apart from the other is writing something this primitive cannot
produce. Nothing else about the response moves: a cookie write is not a header, status or
body write. This is the behavioral model of the cookie-writing primitive a deletion goes
through, for a call that supplies an explicit expiry stamp. -/
def setCookie (resp : Response) (key value : String) (maxAge : Option Nat)
    (expires path : String) (domain : Option String) (secure httpOnly : Bool)
    (samesite : Option String) : Response :=
  { resp with
    cookies := fun k =>
      if k = key then
        some { key        := key
               value      := value
               codedValue := valueEncode value
               maxAge     := maxAgeAfter resp.cookies key maxAge
               expires    := expires
               path       := path
               domain     := domainAfter resp.cookies key domain
               secure     := secureAfter resp.cookies key secure
               httpOnly   := httpOnlyAfter resp.cookies key httpOnly
               samesite   := samesiteAfter resp.cookies key samesite
               comment    := (storedOrDefault resp.cookies key).comment
               version    := (storedOrDefault resp.cookies key).version }
      else resp.cookies k }

/-- Where a declared dependency lands: each field named is appended, in the order
given and after the fields already declared, unless a field of that name (compared
without regard to case) is declared already; and a declaration that includes the
wildcard collapses to the wildcard alone. -/
def variesAfter (declared fields : List String) : List String :=
  let addition := fields.filter (fun h => h.toLower ∉ declared.map String.toLower)
  let combined := declared ++ addition
  if "*" ∈ combined then ["*"] else combined

/-- Declaring that a response's content depends on the given request fields, leaving
its cookies, its other header fields, its status and its body alone. -/
def varyMarked (resp : Response) (fields : List String) : Response :=
  { resp with varies := variesAfter resp.varies fields }

/-- A `samesite` argument is well-formed when it is absent, empty, or one of the three
accepted policy values (case-insensitive). On any other value the cookie primitive
rejects the call outright. -/
def samesiteValid (s : Option String) : Prop :=
  match s with
  | none   => True
  | some v => v = "" ∨ v.toLower = "lax" ∨ v.toLower = "none" ∨ v.toLower = "strict"

/-- The names a cookie container keeps for the attributes themselves, and therefore
cannot store a cookie under. -/
def reservedCookieNames : List String :=
  ["expires", "path", "comment", "domain", "max-age", "secure", "httponly",
   "version", "samesite"]

/-- A name a container will store a cookie under: non-empty, not one of the names it
reserves for the attributes, and built only from characters a cookie name admits. On
any other name the container refuses the write outright, so no cookie comes of it at
all. -/
def keyAccepted (key : String) : Prop :=
  key ≠ "" ∧ key.toLower ∉ reservedCookieNames ∧ key.data.all cookieNameChar

/-- The standard expiry stamp that marks a cookie as already expired. -/
def epochExpires : String := "Thu, 01 Jan 1970 00:00:00 GMT"

/-- Whether a deletion must mark the cookie `secure`: either the name uses a prefix
that browsers only honor over secure transport, or the cookie is being deleted with a
cross-site (`none`) policy, which browsers likewise ignore unless secure. -/
def deleteSecure (key : String) (samesite : Option String) : Bool :=
  key.startsWith "__Secure-" || key.startsWith "__Host-" ||
    (match samesite with
     | some s => s != "" && s.toLower == "none"
     | none   => false)

/-- What a deletion does to a response's cookie container. Exactly one entry is
written: the entry the caller named, not one derived from that name, and no second
entry beside it -- every name the response already carried a cookie under is left
holding exactly what it held. The entry that is written is RENDERED under the name the
caller asked to delete -- the name it is FILED under and the name it is RENDERED under
are two components and BOTH are the caller's name, so an entry filed correctly and
rendered under some other spelling is not a deletion of the cookie the caller named --
and it is RENDERED with the encoding of the empty payload, which is the quoted empty
payload and not the empty string. It ends up carrying no payload; RECORDING the lifetime
zero, which is an entry stating a lifetime rather than one stating none; stamped as
already expired; under the requested `path`; under the requested `domain` whenever one is
requested at all; carrying the requested `samesite` policy whenever that policy is
truthy; marked `secure` exactly when the name's prefix or a cross-site policy requires
it; adding no `httpOnly` marking of its own; and carrying, unchanged, the two attributes
a deletion has no way to supply -- so a deletion cannot annotate the entry it deletes
with anything of its own. -/
def deletesCookie (resp : Response) (key path : String)
    (domain samesite : Option String) (jar : CookieJar) : Prop :=
  (∃ c, jar key = some c ∧
      c.key = key ∧
      c.value = "" ∧
      c.codedValue = valueEncode "" ∧
      c.maxAge = some 0 ∧
      c.expires = epochExpires ∧
      c.path = path ∧
      c.domain = domainAfter resp.cookies key domain ∧
      c.samesite = samesiteAfter resp.cookies key samesite ∧
      c.secure = secureAfter resp.cookies key (deleteSecure key samesite) ∧
      c.httpOnly = httpOnlyAfter resp.cookies key false ∧
      c.comment = (storedOrDefault resp.cookies key).comment ∧
      c.version = (storedOrDefault resp.cookies key).version) ∧
  (∀ k, k ≠ key → jar k = resp.cookies k)
-- pure-end

-- post-conditions-start

/-- Deleting a cookie has exactly the container effect above and NO other effect on the
response: the resulting response is the one handed in with its cookie container
replaced and everything else -- the declared dependencies, every header field, the
status and the body -- left standing as it was. The frame is stated by rebuilding the
response rather than by listing the components that must not move, so a component this
model carries is framed whether or not this clause names it. -/
def problem_spec_deleteCookie (resp : Response) (key path : String)
    (domain samesite : Option String) (result : Response) : Prop :=
  deletesCookie resp key path domain samesite result.cookies ∧
  result = { resp with cookies := result.cookies }
-- post-conditions-end

-- impl-start
def implementation_deleteCookie (resp : Response) (key path : String)
    (domain samesite : Option String) : Response := Id.run do
  let secure := deleteSecure key samesite
  return setCookie resp key "" (some 0) epochExpires path domain secure false samesite
-- impl-end

-- proof-start
theorem correct_deleteCookie :
    ∀ (resp : Response) (key path : String) (domain samesite : Option String),
      keyAccepted key → samesiteValid samesite →
      problem_spec_deleteCookie resp key path domain samesite
        (implementation_deleteCookie resp key path domain samesite) := by
  intro resp key path domain samesite _ _
  unfold problem_spec_deleteCookie deletesCookie
  refine ⟨⟨?_, ?_⟩, ?_⟩
  · simp [implementation_deleteCookie, setCookie, httpOnlyAfter, maxAgeAfter]
  · intro k hk
    simp [implementation_deleteCookie, setCookie, hk]
  · simp [implementation_deleteCookie, setCookie]
-- proof-end

-- post-conditions-start

/-- When the messages cookie carries no payload it is deleted -- the payload cookie
itself, under the name it is stored beside -- and the deletion carries the configured
cross-site policy: the response the routine is left holding satisfies exactly the
deletion contract for `(cookieName, "/", domain, sessionSamesite)`, including its
frame, so nothing else about the response moves either. -/
def problem_spec_messagesDelete (resp : Response) (cookieName : String)
    (domain sessionSamesite : Option String) (result : Response) : Prop :=
  problem_spec_deleteCookie resp cookieName "/" domain sessionSamesite result
-- post-conditions-end

-- impl-start
def implementation_messagesDelete (resp : Response) (cookieName : String)
    (domain sessionSamesite : Option String) : Response := Id.run do
  return implementation_deleteCookie resp cookieName "/" domain sessionSamesite
-- impl-end

-- proof-start
theorem correct_messagesDelete :
    ∀ (resp : Response) (cookieName : String) (domain sessionSamesite : Option String),
      keyAccepted cookieName → samesiteValid sessionSamesite →
      problem_spec_messagesDelete resp cookieName domain sessionSamesite
        (implementation_messagesDelete resp cookieName domain sessionSamesite) := by
  intro resp cookieName domain sessionSamesite hkey hvalid
  unfold problem_spec_messagesDelete implementation_messagesDelete
  exact correct_deleteCookie resp cookieName "/" domain sessionSamesite hkey hvalid
-- proof-end

-- post-conditions-start

/-- When a session ends, its cookie is deleted -- the session cookie itself, under the
configured name -- and the deletion carries the configured cross-site policy: the
container the response is left holding satisfies exactly the deletion contract for
`(name, sessionPath, domain, sessionSamesite)`. Ending a session ALSO leaves the
response declaring that its content depends on the request's own cookies, because
whether the session cookie is being cleared is exactly what it depends on; and nothing
else about the response moves -- every header field beside that declaration, the status
and the body are left standing as they were. -/
def problem_spec_sessionDelete (resp : Response) (name sessionPath : String)
    (domain sessionSamesite : Option String) (result : Response) : Prop :=
  deletesCookie resp name sessionPath domain sessionSamesite result.cookies ∧
  result = { resp with cookies := result.cookies,
                       varies := variesAfter resp.varies ["Cookie"] }
-- post-conditions-end

-- impl-start
def implementation_sessionDelete (resp : Response) (name sessionPath : String)
    (domain sessionSamesite : Option String) : Response := Id.run do
  let deleted := implementation_deleteCookie resp name sessionPath domain sessionSamesite
  return varyMarked deleted ["Cookie"]
-- impl-end

-- proof-start
theorem correct_sessionDelete :
    ∀ (resp : Response) (name sessionPath : String) (domain sessionSamesite : Option String),
      keyAccepted name → samesiteValid sessionSamesite →
      problem_spec_sessionDelete resp name sessionPath domain sessionSamesite
        (implementation_sessionDelete resp name sessionPath domain sessionSamesite) := by
  intro resp name sessionPath domain sessionSamesite hkey hvalid
  have hd := correct_deleteCookie resp name sessionPath domain sessionSamesite hkey hvalid
  unfold problem_spec_deleteCookie at hd
  unfold problem_spec_sessionDelete implementation_sessionDelete
  refine ⟨?_, ?_⟩
  · simpa [varyMarked] using hd.1
  · simp [varyMarked, implementation_deleteCookie, setCookie]
-- proof-end
