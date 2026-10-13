import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The one callee these routines invoke without changing
-- (the low-level attribute-setter that records a cookie's flags) is modeled
-- DEEPLY by `mkCookie` in the `pure` region — an A-reference validated equal to
-- the real callee on its touched projections by axiom_check.py (G-AX), not an
-- axiom the proof consumes. Provenance: mapping.md §3.
-- axioms-end

-- pure-start
/- The observable content of a cleared cookie that this behavior concerns:
   WHICH cookie the clearing directive is filed against AND the name that
   directive actually goes out under, the body it hands over AND the form that
   body goes out in, the remaining lifetime it grants and the
   expiry moment it announces (absent = the attribute is left unset), the secure
   flag, the script-inaccessible flag, the cross-site policy value (absent =
   unset), the path, the domain (absent = unset), and the free-text note and
   protocol version a cookie may carry (absent = unset). mapping.md §2 gives the
   bijection to the repository cookie object's key, the name the entry itself
   carries, the pair of body forms it holds, and its
   `max-age` / `expires` / `secure` / `httponly` / `samesite` /
   `path` / `domain` / `comment` / `version` morsel attributes.

   A clearing directive is not merely a cookie assignment with the right flags.
   Two things beyond the flags are observed here, because both are what a
   recipient actually receives:

   * what it announces about the cookie's LIFETIME is the part a browser acts on
     when it drops the cookie, so the lifetime and expiry it carries are observed
     alongside the flags, and an entry that merely got the flags right is a
     different, observably weaker directive; and
   * what the response TRANSMITS for the cookie is a NAME and a body, as one
     pair, followed by the attributes that are set. BOTH halves of that pair are
     observed, and both are observed separately from where the entry is filed.
     The body goes out in the encoded form the cookie machinery puts it in — an
     emptied body travels as the quoted empty string, not as nothing at all. The
     name goes out as the name the entry ITSELF carries, which is a different
     observable from the one it is filed against: an entry can sit under the
     right cookie and still announce another name, or none, to the recipient, and
     what a browser acts on is the name announced. So two directives agreeing on
     every attribute and filed alike, but disagreeing on either half of what they
     put on the wire, are different directives. For the same reason the
     note and version attributes are observed even though a clearing directive
     never states either — a directive that quietly introduces one transmits an
     attribute the real one does not. -/
structure Cookie where
  name            : String
  transmittedName : String
  value           : String
  codedValue      : String
  maxAge          : Option Nat
  expires         : Option String
  secure          : Bool
  httpOnly        : Bool
  samesite        : Option String
  path            : String
  domain          : Option String
  comment         : Option String
  version         : Option String
deriving Inhabited, DecidableEq

/- A key in the reserved namespace that browsers only honor over a secure
   transport. mapping.md §1. -/
def hasSecurePrefix (key : String) : Bool :=
  key.startsWith "__Secure-" || key.startsWith "__Host-"

/- Whether a cross-site policy value names the unrestricted policy (case
   insensitive). Absent value ⇒ false. -/
def crossSiteUnrestricted (s : Option String) : Bool :=
  match s with
  | some v => v.toLower == "none"
  | none   => false

/- The secure flag a cleared cookie must carry: required either because the key
   sits in the secure-only namespace, or because the cross-site policy is the
   unrestricted one (which browsers reject over an insecure transport). This is
   the heart of the requested behavior; named so the postcondition states the
   relation abstractly. -/
def secureForClear (key : String) (samesite : Option String) : Bool :=
  hasSecurePrefix key || crossSiteUnrestricted samesite

/- The set of cross-site policy values the attribute-setter accepts without
   error; any other present value is rejected upstream. We model behavior only
   on this accepted domain (mapping.md §2, §3.1). -/
def acceptedPolicy : Option String → Prop
  | none   => True
  | some v => v.toLower = "lax" ∨ v.toLower = "none" ∨ v.toLower = "strict"

/- The characters a cookie name may be built from: letters, digits, and the
   punctuation the cookie syntax admits in a name. Anything else — a space, a
   quote, a separator, or any letter outside this alphabet — cannot appear in a
   name the attribute-setter will record. -/
def nameChar (c : Char) : Bool :=
  c.isDigit || c.isUpper || c.isLower || "!#$%&'*+-.^_`|~:".toList.contains c

/- The name, folded to lower case one character at a time, for the
   case-insensitive comparison the reserved-name test below performs. -/
def lowered (k : String) : List Char := k.toList.map Char.toLower

/- The names the attribute-setter keeps for a directive's OWN attributes rather
   than for a cookie: a name matching one of these, in any spelling, names an
   attribute and not a cookie. -/
def reservedAttributeName (k : String) : Bool :=
  [ "comment", "domain", "expires", "httponly", "max-age", "path",
    "samesite", "secure", "version" ].any (fun r => r.toList == lowered k)

/- A cookie name the low-level attribute-setter will actually record: a non-empty
   name built only from the characters a cookie name admits, and not one of the
   names reserved for a directive's own attributes. Handed anything else the
   setter records NOTHING and fails outright, so — for exactly the reason
   `acceptedPolicy` bounds the policy value — the behavior below is stated on the
   names it accepts. mapping.md §2, §3.1. -/
def recordableKey (k : String) : Bool :=
  !k.toList.isEmpty && k.toList.all nameChar && !reservedAttributeName k

/- A domain scope is either absent or actually names one. The empty text is not a
   scope: handed it, the setter records an attribute indistinguishable from an
   absent one, so absent and empty are not separate observables there and the
   behavior is stated where they are distinguishable. mapping.md §2. -/
def domainStated : Option String → Bool
  | none   => true
  | some d => !d.toList.isEmpty

/- The expiry moment a clearing directive announces: the start of the epoch,
   a moment already in the past, so a browser that honors the directive drops the
   cookie at once instead of keeping it. mapping.md §2. -/
def epochExpiry : String := "Thu, 01 Jan 1970 00:00:00 GMT"

/- The remaining lifetime a clearing directive grants the cookie: zero seconds.
   This and `epochExpiry` are jointly what makes an entry a CLEARING directive
   rather than an ordinary assignment of an empty cookie: a browser handed
   neither of them keeps the cookie for the rest of the session, so the cookie is
   not dropped at all. -/
def clearedMaxAge : Option Nat := some 0

/- The form an EMPTIED body travels in: the quoted empty string, two characters
   wide. The cookie machinery encodes a body before putting it on the wire, and
   an empty body does not encode to nothing — a directive that transmits nothing
   where this transmits the quoted empty string is a different directive on the
   wire. mapping.md §2. -/
def quotedEmptyBody : String := "\"\""

/- Deep model of the unchanged attribute-setter callee AS A CLEARING DIRECTIVE
   INVOKES IT, over the thirteen fields under observation: it records exactly the
   cookie it is addressed to, the secure flag, the cross-site policy value, the
   path and the domain handed to it (an absent policy/domain leaves that
   attribute unset, here `none`), and — because the directive exists to make the
   browser drop the cookie rather than to store one — an empty body, that body's
   transmitted form `quotedEmptyBody`, the spent lifetime `clearedMaxAge`, no
   script-inaccessible flag, the expiry moment `epochExpiry`, and neither a note
   nor a version of its own.

   It also names the cookie ON THE WIRE, and names it with the very cookie it is
   addressed to: handing a body over for a cookie is what SETTLES the name the
   resulting entry announces, so the announced name and the name the entry is
   filed under are the same name here, and an entry announcing anything else —
   another cookie's name, or no name at all — is not what this callee produces.
   That holds however the entry got there: a cookie that already had an entry on
   file has the announced name restated by the later hand-over, so it cannot be
   left standing at some earlier name.

   A-reference: axiom_check.py (G-AX) checks this
   equals the real callee on all thirteen fields over the accepted domain. -/
def mkCookie (name : String) (secure : Bool) (samesite : Option String)
    (path : String) (domain : Option String) : Cookie :=
  { name := name, transmittedName := name,
    value := "", codedValue := quotedEmptyBody,
    maxAge := clearedMaxAge, expires := some epochExpiry, secure := secure,
    httpOnly := false, samesite := samesite, path := path, domain := domain,
    comment := none, version := none }

/- The clearing directives a response has ON FILE: one entry per cookie it is
   telling the browser to drop. A clearing routine does not hand its directive
   back to its caller — it files it on the response, alongside whatever is
   already on file there — so what is on file BEFORE the call is part of the
   input, and what is on file after it is what the routine observably did.
   mapping.md §2. -/
abbrev Filed := List Cookie

/- Filing a directive for a cookie that ALREADY has one on file. The attributes a
   directive carries are recorded, never withdrawn: a cookie already marked
   secure-transport-only stays marked, one already marked script-inaccessible
   stays marked, a cookie already scoped to a domain keeps that scope, a lifetime
   already on file stands unless the later directive states one of its own, a
   cross-site policy already on file survives a later directive that names none,
   and a note or version already on file likewise stands — a clearing directive
   states neither, so neither is withdrawn by one. The body, its transmitted
   form, the name the entry announces on the wire, the expiry moment and the path
   are stated outright by every directive, so a later one replaces them: handing
   a body over for a cookie re-announces that cookie's name, so an entry that had
   been announcing some other name does not keep it. Only the values a later
   directive actually
   supplies replace what is on file. So filing a SPURIOUS extra directive for a
   cookie is observable rather than harmless — what it carries cannot be taken
   back. mapping.md §2. -/
def mergeDirective (old new : Cookie) : Cookie :=
  { name            := new.name,
    transmittedName := new.transmittedName,
    value           := new.value,
    codedValue := new.codedValue,
    maxAge     := match new.maxAge with
                  | some n => some n
                  | none   => old.maxAge,
    expires    := new.expires,
    secure     := old.secure || new.secure,
    httpOnly   := old.httpOnly || new.httpOnly,
    samesite   := match new.samesite with
                  | some v => some v
                  | none   => old.samesite,
    path       := new.path,
    domain     := match new.domain with
                  | some d => some d
                  | none   => old.domain,
    comment    := match new.comment with
                  | some c => some c
                  | none   => old.comment,
    version    := match new.version with
                  | some v => some v
                  | none   => old.version }

/- What is on file after ONE directive is filed: the entry for that cookie is
   replaced, where it already sits, by the merge of what was on file with what
   the directive carries; a cookie with nothing on file gains an entry of its
   own; and every OTHER cookie's entry is left exactly as it was. -/
def fileDirective (filed : Filed) (c : Cookie) : Filed :=
  if filed.any (fun d => d.name == c.name) then
    filed.map (fun d => if d.name == c.name then mergeDirective d c else d)
  else
    filed ++ [c]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The cookie-clearing routine, acting on a response that already has `filed`
   directives on it. It files ONE clearing directive and nothing else: addressed
   to the very cookie it was asked to clear — and announcing that same cookie on
   the wire — carrying the secure flag
   `secureForClear` calls for (from the key's namespace OR an unrestricted
   cross-site policy), the cross-site policy value, the path, and the domain —
   and, because the directive's whole purpose is to make the browser DROP that
   cookie, an empty body, that body's transmitted form, and the spent lifetime
   and past expiry moment that say so, with no note or version of its own. An
   entry carrying the right flags but no such lifetime would leave the cookie
   standing for the rest of the session, which is not a clearing directive at
   all; and an entry putting something else on the wire for either half of the
   name-and-body pair it announces, or adding
   an attribute of its own, transmits something other than what a cleared cookie
   transmits — a recipient told to drop some other name, or no name, does not
   drop this cookie however correctly the entry is filed. No other cookie's entry
   is disturbed, and no second directive is
   filed — an extra one would leave attributes on file that cannot be withdrawn. -/
method deleteCookie (filed : Filed) (key : String) (path : String)
    (domain : Option String) (samesite : Option String) return (out : Filed)
  require acceptedPolicy samesite
  require recordableKey key
  require domainStated domain
  ensures out = fileDirective filed
                  (mkCookie key (secureForClear key samesite) samesite path domain)
  do
    -- impl-start
    let secure := secureForClear key samesite
    let out := fileDirective filed (mkCookie key secure samesite path domain)
    return out
    -- impl-end

prove_correct deleteCookie by
  loom_solve <;> simp [mkCookie]

/- A message-storage backend clearing its cookie, on a response that already has
   `filed` directives on it: it files ONE directive, for its OWN cookie, carrying
   the configured cross-site policy and the flag that name and policy call for.
   Models the clear branch — the only branch the behavior touches; the cookie
   uses the default path and the configured domain flows unchanged. -/
method clearMessageCookie (filed : Filed) (cookieName : String)
    (domain : Option String) (configuredPolicy : Option String) return (out : Filed)
  require acceptedPolicy configuredPolicy
  require recordableKey cookieName
  require domainStated domain
  ensures out = fileDirective filed
                  (mkCookie cookieName
                    (secureForClear cookieName configuredPolicy)
                    configuredPolicy "/" domain)
  do
    -- impl-start
    let out ← deleteCookie filed cookieName "/" domain configuredPolicy
    return out
    -- impl-end

prove_correct clearMessageCookie by
  loom_solve

/- A session middleware clearing its cookie when the session empties, on a
   response that already has `filed` directives on it: it files ONE directive,
   for the session's OWN cookie, carrying the configured cross-site policy and
   the flag that name and policy call for. Models the clear branch only — the
   session name, path, and domain flow unchanged. -/
method clearSessionCookie (filed : Filed) (sessionName : String) (path : String)
    (domain : Option String) (configuredPolicy : Option String) return (out : Filed)
  require acceptedPolicy configuredPolicy
  require recordableKey sessionName
  require domainStated domain
  ensures out = fileDirective filed
                  (mkCookie sessionName
                    (secureForClear sessionName configuredPolicy)
                    configuredPolicy path domain)
  do
    -- impl-start
    let out ← deleteCookie filed sessionName path domain configuredPolicy
    return out
    -- impl-end

prove_correct clearSessionCookie by
  loom_solve
