import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The resolver that maps a candidate locale tag to the configured language it
   stands for. Given the tag carried by a URL path (and whether the lookup is
   strict), it returns the listed language code to activate, or `none` when no
   configured language matches. Its behaviour depends only on the ambient set of
   configured languages and is unaffected by this change; it is modeled as an
   opaque function of (candidate tag, strict flag) — the weakest possible
   contract (no asserted property). Provenance + the per-configuration
   functional-determinism justification: mapping.md / axiom_check.py (G-AX). -/
axiom listedLanguage : List Char → Bool → Option (List Char)
-- axioms-end

-- pure-start
/- A "word" character of a locale tag: an ASCII letter or digit, or underscore. -/
def isWordChar (c : Char) : Bool := c.isAlphanum || c == '_'

/- A subtag separator: the two delimiters a locale tag uses between its
   subtags. -/
def isSubtagSep (c : Char) : Bool := c == '-' || c == '@'

/- A single left-to-right scan over a URL path, recognising the leading locale
   tag it carries.

   * `status` : 0 while still scanning; 1 once the tag is locked in by a
                trailing path separator; 2 once the prefix is rejected; 3 once a
                trailing line-terminator has tentatively closed the tag — this
                only stands if that terminator is the very last character of the
                path (any further character turns it into a rejection);
   * `phase`  : 0 expecting the opening path separator; 1 needing the first
                word character of the primary subtag; 2 inside a word run;
                3 just past a subtag separator, needing a word character;
   * `acc`    : the locale tag accumulated so far (the recognised characters);
   * `segs`   : how many *additional* subtags (beyond the primary one) have been
                accepted. -/
structure LS where
  status : Nat
  phase  : Nat
  acc    : List Char
  segs   : Nat
deriving Inhabited, DecidableEq

/- The scan before any character is consumed. -/
def initLS : LS := ⟨0, 0, [], 0⟩

/- One step of the scan. A locale tag is a primary subtag optionally followed by
   further subtags — each an extra separator plus word run — and a path tag may
   carry up to `maxSegs` such additional subtags (for a language this is its
   script and region, per the public RFC 5646 langtag grammar). The tag is
   recognised only when a path separator, the end of the path, or a single
   trailing line-terminator follows it; reaching the additional-subtag limit and
   then seeing another separator (with no closing path separator) rejects the
   prefix, as does any non-word, non-separator character or a dangling separator.

   A line-terminator seen at the end of a word run closes the tag only
   tentatively (`status 3`): a path that ends right there carries the tag, but
   any further character after that terminator turns the prefix into a rejection
   (the terminator was not actually the last character of the path). -/
def lstep (maxSegs : Nat) (st : LS) (c : Char) : LS :=
  if st.status = 1 ∨ st.status = 2 then st
  else if st.status = 3 then { st with status := 2 }
  else if st.phase = 0 then
    if c = '/' then { st with phase := 1 } else { st with status := 2 }
  else if st.phase = 1 then
    if isWordChar c then { st with phase := 2, acc := st.acc ++ [c] }
    else { st with status := 2 }
  else if st.phase = 2 then
    if isWordChar c then { st with acc := st.acc ++ [c] }
    else if isSubtagSep c then
      if st.segs < maxSegs then { st with phase := 3, acc := st.acc ++ [c] }
      else { st with status := 2 }
    else if c = '/' then { st with status := 1 }
    else if c = '\n' then { st with status := 3 }
    else { st with status := 2 }
  else
    if isWordChar c then { st with phase := 2, acc := st.acc ++ [c], segs := st.segs + 1 }
    else { st with status := 2 }

/- Read the recognised locale tag off a finished scan: a tag locked in by a
   trailing path separator, a word run that ran to the end of the path, or a tag
   closed by a single trailing line-terminator that was the last character
   (`status 3`), is the accumulated characters; any rejected or never-started
   scan yields none. -/
def ldecode (st : LS) : Option (List Char) :=
  if st.status = 1 then some st.acc
  else if st.status = 2 then none
  else if st.status = 3 then some st.acc
  else if st.phase = 2 then some st.acc
  else none

/- The leading locale tag a URL path carries, allowing up to `maxSegs`
   additional subtags after the primary one: fold `lstep` over the path, then
   decode. `none` when the path has no recognisable locale tag. -/
def leadingLocaleTag (maxSegs : Nat) (path : List Char) : Option (List Char) :=
  ldecode (path.foldl (lstep maxSegs) initLS)

/- The language a URL path resolves to: take the leading locale tag the path
   carries (allowing the primary subtag plus up to two additional subtags — a
   script and a region — per the public langtag grammar), then resolve that tag
   to a configured language. A path with no recognisable locale tag, or whose
   tag resolves to no configured language, yields none. -/
noncomputable def pathLanguage (path : List Char) (strict : Bool) : Option (List Char) :=
  match leadingLocaleTag 2 path with
  | none    => none
  | some lc => listedLanguage lc strict
-- pure-end

/- The non-deterministic resolver choice below is well-posed: for any target
   value `v` the set of values equal to `v` is non-empty (`v` itself). This
   supplies the constructive existence witness so the `:|` choice elaborates. It
   does NOT weaken verification: under demonic choice the postcondition must
   still hold for every value the predicate allows — here exactly the named
   resolver result. -/
noncomputable instance findableEqOpt (v : Option (List Char)) (n : Lean.Name) :
    Findable (fun e : Option (List Char) => typeWithName (e = v) n) where
  find := fun _ => some v
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl

/- Folding over a one-longer prefix is the fold over the prefix followed by one
   more step on the newly-exposed element — the single fact the loop body leaves
   for `loom_solve`. -/
lemma foldl_take_succ {α β : Type} [Inhabited α] (f : β → α → β) (b : β)
    (l : List α) (i : Nat) (hi : i < l.length) :
    (l.take (i + 1)).foldl f b = f ((l.take i).foldl f b) l[i]! := by
  have happ : l.take (i + 1) = l.take i ++ [l[i]!] := by
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi, Option.getD_some]
    exact List.take_succ_eq_append_getElem hi
  rw [happ, List.foldl_append, List.foldl_cons, List.foldl_nil]

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve a URL path to the language code that should be activated for it.

   The path is scanned for the locale tag it begins with — a primary subtag
   followed by up to two further '-'/'@'-separated subtags (the script and
   region a locale may carry, per the public RFC 5646 langtag grammar) — and
   that tag is resolved to a configured language. A path carrying no recognised
   locale tag, or whose tag matches no configured language, resolves to none.

   Modeled domain: the path ranges over the ASCII plane (every code point
   < 128). The langtag grammar, every configured language code, and every
   graded input are ASCII; outside ASCII the word-character classification of
   the real matcher is library-specific and is not claimed (mapping.md §2,
   §3.1 domain note).

   Both inputs are read-only — neither `path` nor `strict` is declared `mut`
   (directive 5): the scan only reads the path characters and the strict flag,
   and the resolver reads the recognised tag. -/
noncomputable section
method resolvePathLanguage (path : List Char) (strict : Bool)
    return (out : Option (List Char))
  require ∀ c ∈ path, c.toNat < 128
  ensures out = pathLanguage path strict
  do
    -- impl-start
    -- Pre-image skeleton: the scan admits only ONE additional subtag after the
    -- primary one (`lstep 1`), so a tag carrying both a script and a region
    -- (two additional subtags) is rejected. The frozen spec requires the scan
    -- to admit up to two (`leadingLocaleTag 2`), so prove_correct MUST fail.
    let mut st := initLS
    let mut i := 0
    while i < path.length
      -- invariants-start
      invariant 0 ≤ i ∧ i ≤ path.length
      invariant st = (path.take i).foldl (lstep 1) initLS
      done_with i = path.length
      decreasing path.length - i
      -- invariants-end
    do
      st := lstep 1 st path[i]!
      i := i + 1
    let tag := ldecode st
    let result :| result = (match tag with
      | none    => none
      | some lc => listedLanguage lc strict)
    return result
    -- impl-end
end

prove_correct resolvePathLanguage by
  loom_solve
  · rw [foldl_take_succ (lstep 1) initLS path i (by omega), ← invariant_2]
  · simp_all [pathLanguage, leadingLocaleTag, List.take_length]
