import Mathlib
-- imports-end

-- axioms-start
-- UNCHANGED callees used by the modeled step, kept opaque (signatures only).
-- Their concrete values are irrelevant to the modeled behavior: the offset is a
-- pass-through of these computations and they appear identically in the spec and
-- the implementation. No `_prop` property is consumed by the proof; the proof
-- agent may add one only if stuck.
--
-- `percentile`: the q-th percentile of a list of scores.
--
-- NOTE what is deliberately NOT declared here, and why. Turning a payload into
-- the model's per-sample anomaly scores is a TRAVERSAL of the fitted model: real
-- work, performed a definite number of times, and counted from outside by the
-- chunking tests. So it is modeled as an EFFECT rather than as a function
-- anything may apply, and its ONLY counterpart in this model is a
-- `Fitting.traverse` node (see `Fitting` below, and mapping.md). Were it a
-- callable `List Float -> List Float`, a program could perform a traversal and
-- discard the result; a discarded pure application is erased by definitional
-- equality, so NO predicate over the program could see the work, and the
-- traversal record would be under-reportable while looking exact. The work has
-- to be inexpressible, not merely unequal.
opaque percentile : List Float → Float → Float

/-- The numeric content of a carrier as the estimator's admissibility check hands
it on. Establishing that a carrier is admissible is not a pure inspection: the
check re-presents the payload in the uniform numeric form the fitted model
operates in, so the content available for scoring afterwards is that re-presented
content and not the caller's own object. Nothing is claimed here about what the
re-presentation computes; only that scoring downstream of a check sees its
result. -/
opaque checked : List Float → List Float

/-- Re-presenting content that is already in the model's numeric form leaves it
alone: the presentation is settled by the first check, so checking again adds
nothing to the content. -/
axiom checked_idem : ∀ v, checked (checked v) = checked v

/-- The estimator's own verdict on a configured threshold level, from the
parameter validation it performs BEFORE it looks at a carrier at all. Kept
opaque, and Bool-valued rather than an interval on `Float`, for two reasons.
Faithfulness: the admitted levels are settled by the estimator's declared parameter
constraint, so the verdict is exactly a function of the level, and reproducing the
constraint's endpoints here would restate a callee instead of referring to it.
And usability as a hypothesis: `Float` comparison is not decidable by
computation, so an interval would make even `0.25` a level nothing could show
admitted, whereas an opaque verdict can be ASSUMED for a level and then grounded
against the real parameter validation — the same footing as the re-presentation
callee above. See refinement.md and axiom_check.py's parameter-domain leg for
what the real verdict is measured to be, and mapping.md for the level grid. -/
opaque levelAdmitted : Float → Bool
-- axioms-end

-- pure-start
/-- The STORAGE FORM a data carrier's numeric content is presented in. Dense
content is laid out in full; content presented sparsely records only the entries
it has to, and the estimator recognises TWO sparse layouts — one indexed by row
and one indexed by column. They are different presentations of the same numbers
and they are not interchangeable to it.

THREE values and not two, because the fitted model's scoring path is partial on
the LAYOUT and not merely on sparseness: it traverses dense content and
row-indexed sparse content, and refuses column-indexed sparse content outright.
A model carrying one "is it sparse" bit gives the layout that path consumes and
the layout it refuses a single image, and then it cannot say WHICH of the two an
admissibility check hands on — which is the entire content of the sparse
parameter such a check carries, and the one property of the crossing value the
scoring path actually requires. -/
inductive Form where
  | dense
  | sparseByRow
  | sparseByColumn
  deriving DecidableEq

/-- Whether the fitted model's scoring path can traverse content presented in
this form: it consumes dense content and row-indexed sparse content, and refuses
column-indexed sparse content. -/
def Form.traversable : Form → Bool
  | .dense => true
  | .sparseByRow => true
  | .sparseByColumn => false

/-- The form an admissibility check hands content back in, given the form the
content arrived in and the ONE sparse layout that check is prepared to accept.
Content that arrives dense is handed back dense. Sparse content is ADMITTED and
handed back sparse — in the layout the check accepts, whichever sparse layout it
arrived in, so a check is exactly where one sparse layout becomes the other. The
accepted layout is a PARAMETER because it is a property of the check and not of
the estimator: the estimator performs its admissibility check in more than one
place and the places do not agree on it, so a model that pinned one layout for all
of them could not describe what any particular crossing hands on. -/
def Form.reshaped (arrived accepted : Form) : Form :=
  match arrived with
  | .dense => Form.dense
  | _ => accepted

/-- A data carrier presented to the estimator. `values` is the numeric content;
`nFeatures` is the carrier's feature width; `hasFeatureNames` records whether the
carrier arrives with feature-name metadata OF THE KIND THE ESTIMATOR RECORDS —
i.e. metadata the estimator will keep on file and later compare against (the
analogue of a labelled table whose labels it admits as names), as opposed to a
bare numeric carrier or one whose labels it declines to treat as names.
`form` records the carrier's STORAGE FORM (see `Form`): whether the content
arrives laid out in full or in one of the estimator's two sparse layouts, and
which of the two.
`namesInspectable` records whether the estimator will ANSWER the naming question
about this carrier at all: it inspects a carrier's labels to decide whether they
are names it can record, and a carrier whose labels are of mixed kinds is one it
declines to inspect — it turns such a carrier away instead of reporting a
feature-name status for it. So `hasFeatureNames` is the answer and
`namesInspectable` is whether there is one.
`contentAdmissible` records whether the estimator's admissibility check accepts
this carrier's CONTENT at all: the check re-presents content it accepts, but some
content it refuses outright instead of re-presenting — content with no rows to
describe, content with no columns to describe, and numeric content that is not
finite. Such a carrier is turned away, at fitting time and at scoring time alike.

The storage form is carried because it is not a presentational detail here: an
admissibility check ADMITS a sparse carrier and hands it back still sparse, in
the sparse layout that check accepts, and the fitted model's scoring path
consumes only one of the two layouts. Two carriers of identical numeric content
in different layouts are therefore not interchangeable to the fitted model, and a
model that gave them one image would describe a run that does not happen. That is
why the form is three-valued rather than a sparseness bit: the layout a check
hands on is the property the scoring path turns on, so collapsing the two sparse
layouts would leave the one thing that decides whether the crossing value can be
scored at all outside the model entirely.

The inspectability flag is carried for the same kind of reason. Deciding whether a
carrier bears recordable feature names is not a total operation: presented with
labels of mixed kinds the estimator raises rather than answering, at fitting time
and at scoring time alike, whatever it holds on record. A model in which every
carrier had a feature-name status would give such a carrier the status of one the
estimator quietly accepts, and would then describe behaviour that never
happens.

The content flag is the third of these, and it is not the same distinction as
either of the others: re-presenting content is a PARTIAL operation, and the
carriers it is undefined on are not distinguished by their width, their storage
form, or their labels. A carrier the check refuses on content grounds leaves
nothing behind at fitting time — no threshold, no record, no fitted estimator —
and is turned away at scoring time, so a model that gave it the image of a
carrier whose content is merely re-presented would describe a run that does not
happen. Its content is nevertheless a `List Float` like any other: this is a fact
about what the check accepts, not about what can be written down. -/
structure InputData where
  values : List Float
  nFeatures : Nat
  hasFeatureNames : Bool
  form : Form
  namesInspectable : Bool
  contentAdmissible : Bool

/-- The description of admissible input that a fitted estimator holds on record
and enforces against every carrier handed to it afterwards: the feature width it
accepts, and whether it expects feature-name metadata. -/
structure Reference where
  nFeatures : Nat
  hasFeatureNames : Bool
  deriving DecidableEq

/-- What is observable when a carrier is handed to an already-fitted estimator:
`refused` — the carrier is turned away as inadmissible; `warned` — a
feature-name-consistency warning is emitted; `refAfter` — the record the
estimator holds once the call is over; `handedOn` — the CARRIER the entry point
passes to the fitted model for scoring, on the calls where it does not turn the
carrier away; and `returned` — the per-sample anomaly scores the call gives BACK
to its caller, on those same calls.

`returned` is an observable, and it is the most direct one there is. Presenting a
carrier to a fitted estimator is a QUESTION, and the per-sample anomaly scores
the call answers with are the entire point of asking: every further verdict the
fitted estimator offers about that carrier is computed from them, so an answer
that is re-presented on the way out carries every one of those verdicts with it.
What such a call COSTS and what it ANSWERS are two separate observables and not
one. A call that performs every admissibility check correctly, reports every
diagnostic and every record correctly, hands the fitted model exactly the right
carrier, and spends on it exactly the traversals presenting one carrier costs,
has still not been pinned down at all until the answer it hands back is: it can
depart from the one thing the caller asked for while agreeing with every
observation that can be made around it. It is carried as an observable of the
call for the same reason the cost is, and the reason is symmetric — the cost is
what the call SPENDS and the answer is what the call PRODUCES, and a description
that pins only the first describes a call nobody would make.

`handedOn` is an observable and not a detail: the entry point is where a carrier
crosses from the caller's own presentation into the one the fitted model operates
in, and an entry point that performs its admissibility CHECKS and then forwards
the caller's object unchanged is indistinguishable from a correct one by every
diagnostic and every record — while the fitted model is handed content it cannot
score.

It is the whole carrier and not merely its content, because what the entry point
hands on is the estimator's OWN presentation of the data, and a presentation
describes itself: a carrier that still advertises the caller's labels, or that
describes content the estimator would not itself have admitted, leaves the fitted
model holding something the admissibility step it just went through could not
have produced — and no diagnostic, no record and no payload equality can see
that. -/
structure ScoreOutcome where
  refused : Bool
  warned : Bool
  refAfter : Reference
  handedOn : InputData
  returned : List Float := []

/-- An INTERPRETATION of the scoring effect: what the fitted model yields as the
per-sample anomaly scores of a payload (bigger is less abnormal). The four
readers below take one as a parameter and the specification holds for EVERY one
of them, which is what pins a threshold to the scores a program's own traversal
produced: a threshold that agrees with the traversed scores under every
interpretation cannot have been obtained any other way. It is never something a
modeled program can apply — a program is handed an interpretation's output by a
`traverse` continuation or it has no scores at all. -/
abbrev Scoring := List Float → List Float

/-- Scoring a carrier through the fitted estimator's public entry point AS THE
PROGRAM IT RUNS, not merely as what it reports.

Traversing the fitted model to turn a payload into per-sample anomaly scores is
the same real, counted work here as it is during fitting: presenting a carrier to
a fitted estimator costs a definite number of traversals, and that number is
observable from outside. So this call is modeled the same way fitting is — as the
program it executes:

* `done o` — the call is over, reporting `o`, having traversed the fitted model no
  further;
* `traverse v k` — the call performs ONE traversal of the fitted model over the
  payload `v`, and continues as `k` applied to the anomaly scores that traversal
  yields.

Modeling the call as a plain function from the carrier to what it reports is
exactly what would leave this work outside the model. An entry point that
traverses the fitted model once, twice or ten times before reporting has ONE
image under such a model, so it could perform every admissibility check
correctly, report every diagnostic, every record and every crossing carrier
correctly, and still spend traversals of the fitted model that nothing in the
model can see — while what it costs to present a carrier to a fitted estimator is
observable, and is not the estimator's own to choose. As with fitting, the work is
made INEXPRESSIBLE rather than merely unequal: a count reported in a field can be
written with one number while the call performs another, whereas traversals read
off the program's STRUCTURE can be neither over- nor under-reported. -/
inductive Scored where
  | done : ScoreOutcome → Scored
  | traverse : List Float → (List Float → Scored) → Scored

/-- What the call finally reports, obtained by running it under an interpretation
`sc` of the scoring effect: each traversal it performs hands its continuation the
anomaly scores `sc` gives the payload traversed. -/
def Scored.outcome (sc : Scoring) : Scored → ScoreOutcome
  | .done o => o
  | .traverse v k => (k (sc v)).outcome sc

/-- The payloads the call traverses the fitted model over, in the order it
traverses them. Its length is how many traversals presenting one carrier to the
fitted estimator spends. -/
def Scored.traversals (sc : Scoring) : Scored → List (List Float)
  | .done _ => []
  | .traverse v k => v :: (k (sc v)).traversals sc

/-- The values fitting leaves behind: the threshold `offset` chosen during
fitting, `warned` — whether fitting emitted a feature-name-consistency warning,
`reference` — the record of admissible input the estimator holds once fitting
returns, and `scoreLater` — the PROGRAM the fitted estimator runs when a further
carrier is scored through its public entry point, which is what makes both what
that call reports and what it costs observable. -/
structure FitResult where
  offset : Float
  warned : Bool
  reference : Reference
  scoreLater : InputData → Scored

/-- Fitting AS THE PROGRAM IT RUNS, not merely as the values it returns.

Turning a payload into the model's per-sample anomaly scores is a TRAVERSAL of
the fitted model: real work, performed a definite number of times, and observable
as such from outside (the chunking tests count it). A record of the work done
cannot be an output field, because an output field is something the
implementation WRITES: it can report one traversal while performing two, or none
while performing one, and no predicate over the returned values can tell. So
fitting is modeled as the program it executes rather than as its result:

* `done r` — fitting finishes, yielding `r`, having traversed the fitted model no
  further;
* `traverse v k` — fitting performs ONE traversal of the fitted model over the
  payload `v`, and continues as `k` applied to the anomaly scores that traversal
  yields.

`traverse` is the only way for the program to reach anomaly scores, and this is
enforced by SCOPE rather than asserted: no scoring function is declared anywhere
in this model, so a program has nothing to apply. Anomaly scores exist only as
the argument a `traverse` node hands its continuation, and the readers of both
modeled programs take the interpretation of that effect as a PARAMETER. A
`traverse` node is
therefore the only place a traversal can occur, the traversals a program performs
are read off its structure (`Fitting.traversals`), and they are neither over- nor
under-reportable by the program itself. -/
inductive Fitting where
  | done : FitResult → Fitting
  | traverse : List Float → (List Float → Fitting) → Fitting

/-- The values the program finally yields, obtained by running it under an
interpretation `sc` of the scoring effect: each traversal it performs hands its
continuation the anomaly scores `sc` gives the payload traversed. -/
def Fitting.result (sc : Scoring) : Fitting → FitResult
  | .done r => r
  | .traverse v k => (k (sc v)).result sc

/-- The payloads the program traverses the fitted model over, in the order it
traverses them. Its length is how many traversals fitting spends. -/
def Fitting.traversals (sc : Scoring) : Fitting → List (List Float)
  | .done _ => []
  | .traverse v k => v :: (k (sc v)).traversals sc

/-- Whether fitting RUNS TO A RESULT on this carrier and configuration, i.e.
whether the description below is a description of anything at all.

Fitting reaches the scoring path only when a threshold level is configured, and
the scoring path it uses there is the one that performs NO admissibility pass of
its own — it consumes the content the fit-time check handed on, in the form that
check handed it on. That form is where a sparse carrier parts company from a dense
one: the fit-time check accepts the COLUMN-indexed sparse layout, so it hands
every sparse carrier back in that layout, and the scoring path does not traverse
it. So a sparse carrier with a configured threshold does not produce a threshold,
whichever sparse layout it arrived in: fitting gets as far as attempting the
traversal and gets no further. Where no threshold is configured the question does
not arise — nothing is traversed at all — and dense content is handed back dense
and is consumable, so those are exactly the cases fitting completes.

This is a statement about the modeled run, not a licence: it withholds the two
claims that would describe values a completed run leaves behind, and withholds
nothing else. -/
def fitCompletes (x : InputData) (contaminationAuto : Bool) : Bool :=
  contaminationAuto || (Form.reshaped x.form Form.sparseByColumn).traversable
-- pure-end

-- post-conditions-start
/-- Everything below is required of fitting a carrier whose labels the estimator
will INSPECT (`namesInspectable`) and whose content its admissibility check
ACCEPTS (`contentAdmissible`). Those are preconditions and not clauses, because
inspecting the carrier's labels and then re-presenting its content are the first
two things fitting does with it and neither is a total operation: presented with
labels of mixed kinds the estimator raises at the first step instead of
answering, and presented with content the check refuses it raises at the second,
so either way such a fit leaves no threshold, no record and no fitted estimator
to describe. Nothing here is claimed about those carriers. What the estimator
does with such a carrier AFTERWARDS is claimed, because that is observable: see
the two refusal requirements below.

Everything below is likewise required only of a run whose configured threshold
LEVEL the estimator admits (`levelAdmitted`), and that precondition comes FIRST
because the estimator validates its configured parameters before it looks at a
carrier at all. A level the validation refuses stops the run where it stands:
nothing is traversed, no threshold is chosen, no record is established, and what
is left is not a fitted estimator — so there is no run here for any clause below
to describe, and unlike an unusable carrier there is no AFTERWARDS to claim
either, because an estimator that was never fitted turns every carrier away for
that reason alone. This precondition binds only where a level is configured: with
`contaminationAuto` the validation never looks at a level, so a run that carries
an arbitrary one alongside it is described below in full.

Fitting determines an `offset` threshold and must do so without emitting a
feature-name-consistency warning (`warned = false`). When no contamination
threshold is configured (`contaminationAuto`) the offset is the constant `-0.5`;
otherwise — on the carriers where fitting runs to a result at all
(`fitCompletes`) — the offset is the configured percentile of the model's anomaly
scores of the training data, and the content those scores are taken over is the
training payload as the estimator's admissibility check hands it on, not the
caller's own object.

Fitting also establishes the estimator's record of admissible input, and it
takes that record from the training carrier alone: the width and the
feature-name status of the data the estimator was fitted on.

That record is what the fitted estimator enforces from then on, so scoring a
further carrier through the public entry point is observable and pinned: a
carrier whose width disagrees with the training width is turned away, a
feature-name-consistency warning is emitted exactly when its feature-name status
disagrees with the training carrier's, and the record the estimator holds is the
one fitting established — scoring a carrier never re-describes what the
estimator accepts. And a carrier the entry point does NOT turn away is handed to
the fitted model in the content the admissibility check re-presents, not in the
caller's own presentation: the public entry point keeps its check, so everything
that reaches the fitted model through it has been through that check. What
crosses is moreover the estimator's own presentation of that carrier and not the
caller's description of it, and the whole of that presentation is pinned: the
same width, no feature-name metadata of its own, a description the admissibility
step would itself admit — labels that step will inspect, content it accepts — and
the STORAGE FORM that step hands content back in. That form is pinned to the one
the scoring path on the far side of the crossing can actually traverse: the
public entry point's check accepts the ROW-indexed sparse layout, so dense
content crosses dense and sparse content crosses row-indexed, whichever sparse
layout the caller presented. This is the property of the crossing value the
scoring path requires, and requiring only that the form still be sparse would
leave it unsaid: an entry point can perform every admissibility check correctly,
report every diagnostic and every record correctly, convert the content
correctly, and hand the fitted model that content in the sparse layout its own
scoring path refuses — a value the model cannot score, reached through a call that
looks right in every other respect. That is what separates a presentation from a
re-labelled original, and an entry point that checked its argument and then
handed the model a carrier its own check could not have produced would satisfy
every diagnostic, every record and the payload equality alike. A carrier
whose labels the estimator will not inspect is turned away outright — that is
required, not left open, and it is required whatever the carrier's width and
whatever the estimator holds on record; the warning requirement is the one that
does not reach such a carrier, because the inspection it would have to report on
is the step that turned the carrier away. A carrier whose content the check
refuses is turned away outright too, on the same terms and for the same reason —
the re-presentation it would have to perform is where the carrier is refused. The
warning requirement DOES reach that carrier, and is required of it: the naming
question is settled before the content is re-presented, so a diagnostic about the
carrier's feature-name status is surfaced even on a call that then turns it away.

Agreeing widths are NOT claimed to be sufficient for acceptance: a carrier may
be inadmissible for reasons this description does not carry. Specifically, the
ground this description deliberately leaves open is NAME IDENTITY: when the
estimator holds names on record AND the carrier handed to it bears names of its
own, those two sets of names may disagree, and a disagreement is a ground for
refusal that this model — which records only whether names are present, never
which — cannot see. That is the only ground for refusal left open here; the other
ground beyond width, labels the estimator declines to inspect, is not left open
but required above. Wherever
a name comparison cannot
arise, admission IS claimed: if the estimator holds no names on record, or the
carrier brings none, then the naming question is settled by the warning above
and nothing further, so a carrier whose labels the estimator will inspect, whose
content the check accepts and whose width is the training width is admitted. That
is claimed of every such carrier and not merely of the ones whose content the
check leaves as it finds it: re-presenting content is what the entry point is for,
so content the check accepts and rewrites is admitted exactly like content it
accepts and leaves alone. The
absence of feature-name metadata on either side is never itself a ground for
refusal, and nothing here is satisfied by an estimator that turns away a carrier
it merely has a naming complaint about. The training carrier itself is covered
on the same terms — fitting already re-presented it — so an estimator fitted
on a nameless carrier still admits that carrier afterwards.

A carrier the entry point does not turn away is also ANSWERED, and the answer is
pinned too: what the call gives back to its caller is the per-sample anomaly
scores that its own traversal of the fitted model yielded for the content it
handed on, and nothing further is done to them on the way out. A carrier the
entry point turns away is answered with no scores at all, on the same terms and
for the same reason its refusal costs no traversal: such a call does not reach
the fitted model, so it has nothing to report per sample and reports nothing.
That is the whole of the answer — the scores of that one traversal, as that
traversal yielded them, neither re-ordered nor rescaled nor otherwise
re-presented. This is the most
directly observable thing about the call and the last one left unsaid by
everything above: an entry point can check its argument correctly, report every
diagnostic and every record correctly, hand the fitted model exactly the carrier
it should, spend on it exactly the traversals presenting one carrier costs, and
then answer the caller with something other than what it found — and every
requirement above is satisfied by such a call, while every verdict the fitted
estimator goes on to offer about that carrier is computed from the answer and so
departs with it. What the call SPENDS and what the call ANSWERS are two
observables, and pinning only the first describes a call nobody would make.

Presenting a carrier to the fitted estimator through that entry point COSTS
something, and what it costs is pinned as well as what it reports. Scoring a
carrier the entry point accepts is exactly one traversal of the fitted model, and
it is a traversal over the content the entry point handed on rather than over the
caller's own object; a carrier the entry point turns away is never scored at all,
so such a call traverses the fitted model not once. That is the whole of what the
call spends: an entry point that arrives at the same report by traversing the
fitted model twice, or that traverses it before deciding whether to turn the
carrier away, is doing work that presenting one carrier does not cost — work that
is counted from outside, and that is not the estimator's to spend freely. This is
required of every carrier, including the ones the description above leaves free to
be refused on grounds it cannot see: whichever way such a call goes, its cost
follows from the report it reaches.

Finally, choosing the threshold is WORK too, and that work is likewise pinned,
not merely its report: the program fitting runs traverses the fitted model over
exactly the training payload as the admissibility check handed it on, exactly
once, when a threshold level is configured — and performs no traversal whatsoever
on the branch where the offset is the constant.

Both of those last two requirements — the derived threshold and the traversal
record — are requirements on a run that PRODUCES a threshold, so they are asked
only of the carriers on which fitting runs to a result (`fitCompletes`, whose
docstring says which those are and why). On a sparse carrier with a configured
threshold level fitting does not get that far, and this description says nothing
about the offset such a run would have chosen or the traversals it would have
performed; what it does still require there is everything an aborted run is
nevertheless observed to do — that it surface no feature-name diagnostic, that the
record of admissible input it established be the training carrier's, and that
the estimator's public scoring entry point behave as described afterwards.

All of the above is required of fitting under EVERY interpretation of the scoring
effect: this description never appeals to what the anomaly scores actually are.
That is what ties the offset to the program's own traversal — an offset that is
the configured percentile of the traversed payload's scores no matter how scores
are computed cannot have come from anywhere else — and it is why a traversal
cannot be spent off the record: a fitting program has no scoring function in
scope, so the only scores it can reach are the ones its own `traverse` nodes hand
it. -/
def problem_spec_fit (xOrig : InputData) (contaminationAuto : Bool)
    (contamination : Float) (fitting : Fitting) : Prop :=
  (contaminationAuto = false → levelAdmitted contamination = true) →
  xOrig.namesInspectable = true →
  xOrig.contentAdmissible = true →
  ∀ sc : Scoring,
  (fitting.result sc).warned = false
  ∧ (contaminationAuto → (fitting.result sc).offset = -0.5)
  ∧ (fitCompletes xOrig contaminationAuto = true → ¬ contaminationAuto →
       (fitting.result sc).offset
         = percentile (sc (checked xOrig.values)) (100.0 * contamination))
  ∧ (fitting.result sc).reference =
      { nFeatures := xOrig.nFeatures, hasFeatureNames := xOrig.hasFeatureNames }
  ∧ (∀ z : InputData,
       ((z.nFeatures != xOrig.nFeatures) →
          (((fitting.result sc).scoreLater z).outcome sc).refused = true)
       ∧ (z.namesInspectable = true →
            (((fitting.result sc).scoreLater z).outcome sc).warned
              = (xOrig.hasFeatureNames != z.hasFeatureNames))
       ∧ (((fitting.result sc).scoreLater z).outcome sc).refAfter
            = (fitting.result sc).reference
       ∧ ((((fitting.result sc).scoreLater z).outcome sc).refused = false →
            (((fitting.result sc).scoreLater z).outcome sc).handedOn =
              { values := checked z.values, nFeatures := z.nFeatures,
                hasFeatureNames := false,
                form := Form.reshaped z.form Form.sparseByRow,
                namesInspectable := true, contentAdmissible := true })
       ∧ (z.namesInspectable = false →
            (((fitting.result sc).scoreLater z).outcome sc).refused = true)
       ∧ (z.contentAdmissible = false →
            (((fitting.result sc).scoreLater z).outcome sc).refused = true)
       ∧ ((fitting.result sc).scoreLater z).traversals sc
            = (bif (((fitting.result sc).scoreLater z).outcome sc).refused
               then [] else [checked z.values])
       ∧ (((fitting.result sc).scoreLater z).outcome sc).returned
            = (bif (((fitting.result sc).scoreLater z).outcome sc).refused
               then [] else sc (checked z.values)))
  ∧ (xOrig.hasFeatureNames = false →
       (((fitting.result sc).scoreLater xOrig).outcome sc).refused = false)
  ∧ (∀ z : InputData, z.contentAdmissible = true →
       z.nFeatures = xOrig.nFeatures →
       (xOrig.hasFeatureNames = false ∨ z.hasFeatureNames = false) →
       z.namesInspectable = true →
       (((fitting.result sc).scoreLater z).outcome sc).refused = false)
  ∧ (fitCompletes xOrig contaminationAuto = true →
       fitting.traversals sc
         = (bif contaminationAuto then [] else [checked xOrig.values]))
-- post-conditions-end

-- impl-start
/-- What the input-validation step yields: the normalized data carrier, the
record the estimator holds afterwards, and the two diagnostics. -/
structure Validation where
  carrier : InputData
  refAfter : Reference
  refused : Bool
  warned : Bool

/-- The record held by an estimator that has not described its admissible input
yet. The initial validation of the training data is a reset, which replaces it. -/
def unrecorded : Reference := { nFeatures := 0, hasFeatureNames := false }

/-- Model of the input-validation step, against a `ref` the estimator currently
holds and for the ONE sparse layout this particular step accepts (`accepted`). It
re-presents the data carrier's payload in the model's numeric form and strips its
metadata (so the result no longer carries feature-name metadata), and it hands the
STORAGE form back reshaped: dense content stays dense, and sparse content is
admitted and handed back sparse in the layout this step accepts — which is why
fitting's own scoring path cannot always consume what the step it uses returns. A
reset (`reset = true`) RE-DESCRIBES the admissible input from the supplied
carrier and checks nothing, so it neither refuses nor warns. A consistency
re-check (`reset = false`) leaves the record alone and checks the carrier against
it: it refuses a carrier whose width disagrees with the record, and it warns when
the carrier's feature-name status disagrees with the record — i.e. either the
record expects feature names but the supplied carrier has none, or the record
expects none but the carrier has them.

A re-check begins by INSPECTING the carrier's labels, and that step is where a
carrier whose labels are of mixed kinds is turned away: the step raises instead of
reporting a status, so such a carrier is refused whatever its width, and no
feature-name diagnostic is reported for it either. Re-presenting the content comes
next, and that step is where a carrier whose content the check does not accept is
turned away — after the labels have been reported on, so such a carrier is refused
whatever its width but its feature-name diagnostic still stands. What the step
hands back is the estimator's own numeric presentation, whose labels are never of
mixed kinds and whose content it has just accepted, so the carrier it returns is
always inspectable and always admissible. -/
def validateInput (x : InputData) (reset : Bool) (ref : Reference)
    (accepted : Form) : Validation :=
  { carrier := { values := checked x.values, nFeatures := x.nFeatures,
                 hasFeatureNames := false,
                 form := Form.reshaped x.form accepted,
                 namesInspectable := true, contentAdmissible := true },
    refAfter := bif reset then
                  { nFeatures := x.nFeatures, hasFeatureNames := x.hasFeatureNames }
                else ref,
    refused := (!reset) && (!x.namesInspectable || !x.contentAdmissible
                             || (x.nFeatures != ref.nFeatures)),
    warned := (!reset) && x.namesInspectable
                && (ref.hasFeatureNames != x.hasFeatureNames) }

/-- What the public scoring entry point of an estimator holding `ref` REPORTS
about a carrier handed to it: it validates that carrier as a consistency
re-check, accepting the ROW-indexed sparse layout — the one the fitted model it
forwards to can traverse — and what it hands on to the fitted model is what that
validation returned. -/
def scoreReport (ref : Reference) (z : InputData) : ScoreOutcome :=
  let v := validateInput z false ref Form.sparseByRow
  { refused := v.refused, warned := v.warned, refAfter := v.refAfter,
    handedOn := v.carrier }

/-- The public scoring entry point AS THE PROGRAM IT RUNS. It reaches the report
above, and the traversals it spends follow from that report and from nothing
else: a carrier the report turns away is never scored, so on that lane the
program is done where the carrier was refused; a carrier the report accepts is
scored, and that is one traversal of the fitted model over the content the report
hands on — the program's only one. What the call ANSWERS with follows from that
same traversal: the scores it yielded are what the call gives back, carried out
of the continuation exactly as they arrived in it. A carrier that was turned away
is answered with nothing, because such a call does not return to its caller at
all. -/
def scoreEntry (ref : Reference) (z : InputData) : Scored :=
  let r := scoreReport ref z
  bif r.refused then Scored.done { r with returned := [] }
    else Scored.traverse r.handedOn.values
           (fun scores => Scored.done { r with returned := scores })

def implementation_fit (xOrig : InputData) (contaminationAuto : Bool)
    (contamination : Float) : Fitting :=
  -- initial validation of the training data: a reset, which describes the
  -- admissible input from the training carrier and raises no diagnostic
  let v0 := validateInput xOrig true unrecorded Form.sparseByColumn
  let x := v0.carrier
  let ref := v0.refAfter
  if contaminationAuto then
    -- 0.5 plays a special role; we take the opposite, and the constant needs no
    -- traversal of the fitted model at all: the program is done here
    Fitting.done { offset := -0.5, warned := false, reference := ref,
                   scoreLater := scoreEntry ref }
  else
    -- contamination threshold configured: derive the offset from the model's
    -- anomaly scores of the (already-checked) training data, WITHOUT a second
    -- admissibility pass — so no feature-name-consistency warning is emitted and
    -- the record established from the training carrier stands. Reaching those
    -- scores is one traversal of the fitted model and the program's only one.
    Fitting.traverse x.values fun scores =>
      let off := percentile scores (100.0 * contamination)
      Fitting.done { offset := off, warned := false, reference := ref,
                     scoreLater := scoreEntry ref }
-- impl-end

-- proof-start
theorem correct_fit : ∀ (xOrig : InputData) (contaminationAuto : Bool)
    (contamination : Float),
    problem_spec_fit xOrig contaminationAuto contamination
      (implementation_fit xOrig contaminationAuto contamination) := by
  intro xOrig contaminationAuto contamination
  -- what presenting a carrier to an estimator through the modeled entry point
  -- reports, what it answers with, and what it costs, all read off the program
  -- that entry point runs
  have hout : ∀ (sc : Scoring) (ref : Reference) (z : InputData),
      ((scoreEntry ref z).outcome sc).refused = (scoreReport ref z).refused
      ∧ ((scoreEntry ref z).outcome sc).warned = (scoreReport ref z).warned
      ∧ ((scoreEntry ref z).outcome sc).refAfter = (scoreReport ref z).refAfter
      ∧ ((scoreEntry ref z).outcome sc).handedOn = (scoreReport ref z).handedOn
      ∧ ((scoreEntry ref z).outcome sc).returned
          = (bif (scoreReport ref z).refused then []
             else sc (scoreReport ref z).handedOn.values)
      ∧ (scoreEntry ref z).traversals sc
          = (bif (scoreReport ref z).refused then []
             else [(scoreReport ref z).handedOn.values]) := by
    intro sc ref z
    unfold scoreEntry
    cases h : (scoreReport ref z).refused <;>
      simp [Scored.outcome, Scored.traversals, h]
  unfold problem_spec_fit implementation_fit
  intro _hlvl hins hcon sc
  cases contaminationAuto <;>
    refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
    simp only [Bool.false_eq_true, if_false, if_true, Fitting.result,
               Fitting.traversals, (hout sc _ _).1, (hout sc _ _).2.1,
               (hout sc _ _).2.2.1, (hout sc _ _).2.2.2.1,
               (hout sc _ _).2.2.2.2.2,
               scoreReport, validateInput, unrecorded,
               cond_true, cond_false, Bool.not_true,
               Bool.false_and, hins, hcon] <;>
    first
      | rfl
      | (intro z hc hw hn hi; simp [hi, hc, hw])
      | (intro z; and_intros <;> intros <;>
         first
           | (clear hout; simp_all; done)
           | (rw [(hout sc _ z).2.2.2.2.1]
              simp [scoreReport, validateInput]))
      | (intro h; first
          | exact h.elim
          | exact trivial
          | exact bne_self_eq_false _
          | exact absurd trivial h
          | rfl
          | (simp))
-- proof-end
