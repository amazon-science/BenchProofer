import Mathlib
-- imports-end

-- axioms-start
-- No callee is consumed as an axiom: the version-ordering operation is the
-- behavior under specification, so it is modeled deeply in the `pure` region and
-- validated against the real library routine (G-AX A-reference), not axiomatized.
-- axioms-end

-- pure-start

/-- The blank code points tolerated around a version string; a leading/trailing
run of these is ignored when reading a version. -/
def blankChars : List Char :=
  [⟨0x9, by decide⟩, ⟨0xa, by decide⟩, ⟨0xb, by decide⟩, ⟨0xc, by decide⟩,
   ⟨0xd, by decide⟩, ⟨0x1c, by decide⟩, ⟨0x1d, by decide⟩, ⟨0x1e, by decide⟩,
   ⟨0x1f, by decide⟩, ⟨0x20, by decide⟩, ⟨0x85, by decide⟩, ⟨0xa0, by decide⟩,
   ⟨0x1680, by decide⟩, ⟨0x2000, by decide⟩, ⟨0x2001, by decide⟩,
   ⟨0x2002, by decide⟩, ⟨0x2003, by decide⟩, ⟨0x2004, by decide⟩,
   ⟨0x2005, by decide⟩, ⟨0x2006, by decide⟩, ⟨0x2007, by decide⟩,
   ⟨0x2008, by decide⟩, ⟨0x2009, by decide⟩, ⟨0x200a, by decide⟩,
   ⟨0x2028, by decide⟩, ⟨0x2029, by decide⟩, ⟨0x202f, by decide⟩,
   ⟨0x205f, by decide⟩, ⟨0x3000, by decide⟩]

def isBlank (c : Char) : Bool := blankChars.contains c

/-- Case folding used when reading a version: ASCII upper case maps to lower
case, and nothing else folds. The qualifier tags below are therefore matched
case-insensitively within ASCII (`RC` and `rc` name the same tag) and a code
point outside ASCII never spells a tag; see the admissibility note in the
`pre-conditions` region for why the claim is drawn at that boundary. -/
def foldChar (c : Char) : Char :=
  if 'A' ≤ c && c ≤ 'Z' then Char.ofNat (c.toNat + 32) else c

def isDigitC (c : Char) : Bool := '0' ≤ c && c ≤ '9'

/-- The separators that may appear between a version's parts. -/
def isSep (c : Char) : Bool := c == '.' || c == '-' || c == '_'

def isWordC (c : Char) : Bool := isDigitC c || ('a' ≤ c && c ≤ 'z')

/-- Split off the longest leading run of decimal digits. -/
def takeDigits : List Char → List Char × List Char
  | [] => ([], [])
  | c :: cs =>
      if isDigitC c then
        let (d, r) := takeDigits cs
        (c :: d, r)
      else ([], c :: cs)

def digitsToNat (ds : List Char) : Nat :=
  ds.foldl (fun acc c => acc * 10 + (c.toNat - 48)) 0

/-- One segment of a version's trailing build tag: either numeric or a word. -/
structure LocalSeg where
  isNum : Bool
  num   : Nat
  word  : String

/-- The ordering key of a version: its era, its numeric components, a flat
encoding of its qualifier tags, and its build-tag segments. Two versions compare
by comparing these keys in order. -/
structure VerKey where
  epoch     : Nat
  release   : List Nat
  suffix    : List Nat
  localSegs : List LocalSeg

/-- Lexicographic comparison of numeric component lists; a proper prefix is
smaller than its extension. -/
def natListCmp : List Nat → List Nat → Ordering
  | [], [] => .eq
  | [], _ :: _ => .lt
  | _ :: _, [] => .gt
  | x :: xs, y :: ys =>
      if x < y then .lt else if y < x then .gt else natListCmp xs ys

/-- Build-tag comparison: word segments order before numeric ones, words compare
alphabetically, numbers numerically, and a proper prefix is smaller. -/
def localCmp : List LocalSeg → List LocalSeg → Ordering
  | [], [] => .eq
  | [], _ :: _ => .lt
  | _ :: _, [] => .gt
  | a :: as, b :: bs =>
      if a.isNum == b.isNum then
        (if a.isNum then
           (if a.num < b.num then .lt else if b.num < a.num then .gt else localCmp as bs)
         else
           (if a.word < b.word then .lt else if b.word < a.word then .gt
            else localCmp as bs))
      else if a.isNum then .gt else .lt

/-- Compare two version keys: era, then numeric components, then qualifier
tags, then build tag. -/
def verCmp (a b : VerKey) : Ordering :=
  if a.epoch < b.epoch then .lt else if b.epoch < a.epoch then .gt
  else match natListCmp a.release b.release with
    | .lt => .lt
    | .gt => .gt
    | .eq => match natListCmp a.suffix b.suffix with
      | .lt => .lt
      | .gt => .gt
      | .eq => localCmp a.localSegs b.localSegs

/-- `a` is a strictly later version than `b`. -/
def verGt (a b : VerKey) : Bool := verCmp a b == .gt

def dropSep (s : List Char) : List Char :=
  match s with | c :: cs => if isSep c then cs else s | [] => s

/-- Read an optional separator, then one of `toks` (longest spelling first),
then an optional separator and an optional number. -/
def tryTok : List (String × Nat) → List Char → Option (Nat × Nat × List Char)
  | [], _ => none
  | (t, rank) :: rest, s =>
      let s1 := dropSep s
      if t.toList.isPrefixOf s1 then
        let (d, r) := takeDigits (dropSep (s1.drop t.length))
        some (rank, digitsToNat d, r)
      else tryTok rest s

/-- Spellings of the pre-qualifier tags, with the rank each denotes. -/
def preToks : List (String × Nat) :=
  [("alpha", 1), ("beta", 2), ("preview", 3), ("pre", 3), ("rc", 3),
   ("a", 1), ("b", 2), ("c", 3)]

/-- Spellings of the revision-qualifier tags. -/
def postToks : List (String × Nat) := [("post", 1), ("rev", 1), ("r", 1)]

/-- Drop trailing zero components, so `1`, `1.0` and `1.0.0` share a key. -/
def stripZeros (xs : List Nat) : List Nat :=
  (xs.reverse.dropWhile (· == 0)).reverse

def mkLocalSeg (cur : List Char) : LocalSeg :=
  if cur.all isDigitC then ⟨true, digitsToNat cur, ""⟩
  else ⟨false, 0, String.mk cur⟩

/-- Read the build tag: non-empty word/number segments separated by single
separators. -/
def localLoop : List Char → List Char → Option (List LocalSeg)
  | cur, [] => if cur.isEmpty then none else some [mkLocalSeg cur]
  | cur, c :: cs =>
      if isWordC c then localLoop (cur ++ [c]) cs
      else if isSep c then
        if cur.isEmpty then none
        else match localLoop [] cs with
          | none => none
          | some segs => some (mkLocalSeg cur :: segs)
      else none

/-- Read the `.`-separated numeric components after the first one. The `Nat`
argument only bounds the recursion (each step consumes at least two characters). -/
def relLoop : Nat → List Char → List Nat × List Char
  | 0, s => ([], s)
  | n + 1, s =>
      match s with
      | '.' :: cs =>
          let (d, r) := takeDigits cs
          if d.isEmpty then ([], s)
          else
            let (more, rest) := relLoop n r
            (digitsToNat d :: more, rest)
      | _ => ([], s)

/-- Assemble the ordering key from the pieces read off a version string. A
version with no pre-qualifier but a development tag ranks below every
pre-qualifier; one with neither ranks above them all. -/
def mkKey (epoch : Nat) (rel : List Nat) (preRank : Option Nat) (preNum : Nat)
    (postRank : Option Nat) (postNum : Nat) (devRank : Option Nat) (devNum : Nat)
    (segs : List LocalSeg) : VerKey :=
  let pr :=
    match preRank, postRank, devRank with
    | none, none, some _ => 0
    | none, _, _ => 4
    | some p, _, _ => p
  let pn := match preRank with | some _ => preNum | none => 0
  ⟨epoch, stripZeros rel,
   [pr, pn, (if postRank.isSome then 1 else 0), postNum,
    (if devRank.isSome then 0 else 1), devNum], segs⟩

/-- Read everything after the optional era marker: the numeric components, then
the optional pre-, revision- and development-qualifier tags, then the optional
build tag. `none` when the text is not a readable version. -/
def parseAfterEpoch (epoch : Nat) (s : List Char) : Option VerKey :=
  let (d, r0) := takeDigits s
  if d.isEmpty then none else
  let (rel, r1) := relLoop s.length r0
  let (preRank, preNum, r2) :=
    match tryTok preToks r1 with
    | some (rk, n, rr) => (some rk, n, rr)
    | none => (none, 0, r1)
  let (postRank, postNum, r3) :=
    match r2 with
    | '-' :: cs =>
        let (d2, rr) := takeDigits cs
        if d2.isEmpty then
          match tryTok postToks r2 with
          | some (rk, n, rr2) => (some rk, n, rr2)
          | none => (none, 0, r2)
        else (some 1, digitsToNat d2, rr)
    | _ =>
        match tryTok postToks r2 with
        | some (rk, n, rr) => (some rk, n, rr)
        | none => (none, 0, r2)
  let (devRank, devNum, r4) :=
    match tryTok [("dev", 0)] r3 with
    | some (_, n, rr) => (some 0, n, rr)
    | none => (none, 0, r3)
  match r4 with
  | '+' :: cs =>
      match localLoop [] cs with
      | none => none
      | some segs =>
          some (mkKey epoch (digitsToNat d :: rel) preRank preNum postRank postNum
            devRank devNum segs)
  | [] =>
      some (mkKey epoch (digitsToNat d :: rel) preRank preNum postRank postNum
        devRank devNum [])
  | _ => none

/-- Read a version string into its ordering key, or `none` when the text is not
a readable version. Surrounding blanks are ignored, letter case is folded, an
optional leading `v` is dropped, and an optional `<digits>!` era marker is read
first. -/
def parseVersion (raw : String) : Option VerKey :=
  let t := ((raw.toList.dropWhile isBlank).reverse.dropWhile isBlank).reverse
  let s0 := t.map foldChar
  let s1 := match s0 with | c :: cs => if c == 'v' then cs else s0 | [] => s0
  match s1.idxOf? '!' with
  | some k =>
      let e := s1.take k
      if !e.isEmpty && e.all isDigitC then
        parseAfterEpoch (digitsToNat e) (s1.drop (k + 1))
      else none
  | none => parseAfterEpoch 0 s1

/-- Plain lexicographic ordering on the raw strings (Unicode code-point order).
This is the comparison used when one operand is not a readable version. -/
def stringGt (a b : String) : Bool := decide (a > b)

/-- The minimum-version requirement is NOT met for a required string `req`
against a present `ver` exactly when: the present version is the sentinel
`"unknown version"`, or — comparing as versions when both are readable as
versions, else comparing the raw strings — the required version is strictly
greater than the present one. -/
def requirementUnmet (req ver : String) : Bool :=
  if ver == "unknown version" then true
  else
    match parseVersion req, parseVersion ver with
    | some a, some b => verGt a b
    | _, _ => stringGt req ver

/-- An entry is `(req, loaded?)`: `req` is the required minimum version string;
`loaded?` is `some v` when an extension providing version string `v` is present,
or `none` when no such extension is present (in which case the requirement
imposes no failure here). The entry triggers a failure iff a version is present
and does not meet the requirement. -/
def entryUnmet (e : String × Option String) : Bool :=
  match e.2 with
  | none => false
  | some ver => requirementUnmet e.1 ver

-- pure-end

-- pre-conditions-start

/-- `true` when every code point of `s` is an ASCII one. -/
def asciiStr (s : String) : Bool := s.toList.all (fun c => c.toNat < 128)

/-- `true` when both version strings an entry mentions are ASCII text (an entry
that mentions no present version only has to have an ASCII requirement). -/
def entryAscii (e : String × Option String) : Bool :=
  asciiStr e.1 && (match e.2 with | none => true | some v => asciiStr v)

/-- Admissibility: every version string an entry mentions is ASCII text.

The version grammar read above is an ASCII grammar, and every ASCII string is
admitted — including strings that are not readable versions at all (those are
ordered as raw text) and the sentinel that stands for an unreported version. The
restriction excludes exactly one class of input: a string carrying a code point
outside ASCII that a case-folding table maps onto an ASCII letter. Released
revisions of the routine being modeled disagree about those: some scope their
case-insensitive tag matching to ASCII and refuse such a string, others accept it
and read it as a tag whose spelling then also orders above the ASCII spelling of
the same tag — and the two readings give different verdicts on the same pair of
inputs. There is therefore no single faithful reading of that class, and the
claim below deliberately does not make one; on ASCII input the readings agree,
and that agreement is what is measured against the real routine. -/
def problem_pre_verifyExtensionVersions
    (entries : List (String × Option String)) : Prop :=
  ∀ e ∈ entries, entryAscii e = true

-- pre-conditions-end

-- post-conditions-start

/-- The result reports the position of the FIRST entry whose version requirement
is not met, or `none` when every present version meets its requirement.

  * `none`  ⟺ no entry is unmet;
  * `some k` ⟺ entry `k` is unmet and every earlier entry is met. -/
def problem_spec_verifyExtensionVersions
    (entries : List (String × Option String)) (result : Option Nat) : Prop :=
  match result with
  | none => ∀ e ∈ entries, entryUnmet e = false
  | some k =>
      (∃ e, entries[k]? = some e ∧ entryUnmet e = true) ∧
      (∀ j, j < k → ∀ e, entries[j]? = some e → entryUnmet e = false)

-- post-conditions-end

-- impl-start


def implementation_verifyExtensionVersions
    (entries : List (String × Option String)) : Option Nat := Id.run do
  let mut idx := 0
  for (req, loaded) in entries do
    match loaded with
    | none => pure ()
    | some ver =>
      let mut fulfilled := true
      if ver == "unknown version" then
        fulfilled := false
      else
        if stringGt req ver then fulfilled := false
      if !fulfilled then
        return some idx
    idx := idx + 1
  return none

-- impl-end

-- proof-start

theorem correct_verifyExtensionVersions :
    ∀ entries : List (String × Option String),
      problem_pre_verifyExtensionVersions entries →
      problem_spec_verifyExtensionVersions entries
        (implementation_verifyExtensionVersions entries) := by
  sorry

-- proof-end
