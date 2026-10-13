import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. A constituent carrier is modeled directly as the
--  bundle of observations this step reads and writes, and recording a projection
--  onto a carrier is modeled directly as the transformation it works on that
--  bundle. No unchanged callee's contract is consumed and no foreign callee is
--  deep-modeled, so there is nothing to axiomatize.)
-- axioms-end

-- pure-start
/- One constituent carrier of a compound request, as this step observes it.

   A carrier's SELECTION is what it will emit, and it has THREE parts that move
   together, because a carrier draws the things it can emit from three separate
   places and keeps a separate record of what it has selected from each:
   `columns`, the explicit list of its own model's columns it names;
   `sideSelected`, the side outputs -- outputs supplied by literal text carried
   alongside the model rather than computed from it -- that are currently part of
   that selection; and `auxSelected`, the auxiliary outputs computed for this
   carrier that are currently part of it.

   The remaining two observations describe the carrier's MODEL rather than its
   selection, and reconciling a projection never alters either of them:
   `auxAvailable` names every non-column output the carrier is ABLE to supply,
   whether or not its selection currently carries it, and `ownFields` names the
   columns the carrier's own model defines. Recording consults neither -- it reads
   the selection, not the model -- but both are pinned across the step, so a
   carrier's ability to answer a name cannot be quietly destroyed. -/
structure Carrier where
  columns : List String
  sideSelected : List String
  auxSelected : List String
  auxAvailable : List String
  ownFields : List String
deriving DecidableEq

/- Whether the outer request's projection must be pushed down onto a carrier:
   true exactly when the carrier does not yet name any explicit columns AND the
   outer request names explicit columns OF ITS OWN. A carrier that already names
   an explicit column list keeps it; an outer request that names no explicit
   columns of its own asks for no push-down, even when the compound projection it
   would contribute is itself non-empty. -/
def shouldProject (c : Carrier) (requested : List String) : Bool :=
  c.columns.isEmpty && !requested.isEmpty

/- Recording a pushed-down projection onto a carrier. This is ONE act that
   reshapes the carrier's whole selection, not an edit of its explicit column
   list alone, and what it reads to reshape it is the selection the carrier
   ALREADY carries rather than everything its model could be asked for.

   A NON-EMPTY projection is sorted into the three parts by consulting the
   carrier's two records of selected non-column outputs IN ORDER, side outputs
   FIRST and auxiliary outputs only afterwards. A projected name found among the
   carrier's selected side outputs is kept as a side output; a projected name not
   found there but found among its selected auxiliary outputs is kept as an
   auxiliary output; every OTHER projected name becomes part of its explicit
   column list. The precedence is observable, not a formality: a name the carrier
   happens to carry in BOTH records is kept only as a side output, and is dropped
   from its selected auxiliary outputs.

   Each of the two kept records is filtered down to the projected names, so it
   lists them in the CARRIER's own order and once each however the projection
   happens to list them, while the explicit column list is built from the
   projection and so keeps the PROJECTION's order and repetitions. A name the
   carrier's model could supply as a non-column output but which neither record
   currently carries is no part of the selection being read, so a projected name
   matching it lands in the explicit column list with the rest.

   An EMPTY projection is the other leg: it names nothing to keep, so BOTH
   records of selected non-column outputs are left exactly as they stand while
   the explicit column list becomes every column the carrier's own model defines.

   All three parts of the selection are overwritten together, so a carrier that
   has been recorded onto is not put back as it was by restoring only some of
   them. The carrier's model is untouched by either leg. -/
def recordOnto (c : Carrier) (projected : List String) : Carrier :=
  if projected.isEmpty then
    { c with columns := c.ownFields }
  else
    { c with
        columns := projected.filter
          (fun n => !c.sideSelected.contains n && !c.auxSelected.contains n),
        sideSelected := c.sideSelected.filter (fun n => projected.contains n),
        auxSelected := c.auxSelected.filter
          (fun n => projected.contains n && !c.sideSelected.contains n) }

/- The carrier this step must hand back: the carrier with the projection
   recorded onto it where the push-down applies, and otherwise the carrier
   exactly as it stands. -/
def workingCarrier (c : Carrier) (requested projected : List String) : Carrier :=
  if shouldProject c requested then recordOnto c projected else c

/- Whether a carrier can answer every name in a column list: each name is a
   column its own model defines, or one of the side outputs its selection already
   carries, or one of the auxiliary outputs its selection already carries. Both
   records of selected non-column outputs count here, and they count on equal
   terms -- the precedence between them decides only WHERE an answerable name is
   kept, never WHETHER it can be answered. A non-column output the carrier is able
   to supply but which neither record currently carries does NOT make a name
   answerable -- recording reads the selection, not the model, so `auxAvailable`
   is deliberately absent from this test -- and such a name is answerable only if
   the carrier's own model defines a column of that name. A carrier can only
   absorb a projection whose every name it can answer. -/
def answerable (c : Carrier) (names : List String) : Bool :=
  names.all (fun n =>
    c.ownFields.contains n || c.sideSelected.contains n || c.auxSelected.contains n)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- One step of assembling a compound result from several constituent carriers:
   reconcile a single shared constituent carrier with the projection the outer
   request wants every constituent to carry, and hand back the carrier this step
   will actually read columns from.

   The shared carrier is shared across repeated assemblies of the same compound
   request, so its whole selection must be treated as read-only state: this step
   reads it to decide what to project, but the carrier it hands back must be one
   whose selection it is free to reshape WITHOUT the shared carrier's own
   selection moving. Leaving the shared carrier's selection as it was on entry is
   precisely what leaves a later assembly of the same compound request free to
   project a different column list.

   `persistent` is the shared carrier (declared `mut` because the long-standing
   shape of this code reaches for it as the thing to reconcile). It MUST be
   returned unchanged, and `ensures persistent = persistentOld` pins EVERY
   observation of it — all three parts of its selection and both parts of its
   model description, not its explicit column list alone. Recording a projection
   onto a carrier overwrites all three selection parts at once, so a carrier that
   has absorbed a projection is not put back as it was by writing its explicit
   column list back afterwards, nor by restoring only one of its two records of
   selected non-column outputs.

   The two request observations are read-only and never altered: `requested` is
   the outer request's own explicit column list, which is what decides whether a
   push-down happens at all, and `projected` is the full column list the request
   pushes down.

   `recorded` says whether this step has recorded a pushed-down projection onto
   ANY constituent carrier; it is `mut` because the long-standing shape of this
   code performs that recording by reaching for the shared carrier itself.
   Together `ensures shouldProject persistentOld requested = false → recorded =
   recordedOld` and `ensures shouldProject persistentOld requested = true →
   recorded = true` say the recording happens EXACTLY on the push-down. Where the
   push-down does not apply, NO carrier is recorded onto. Where it does apply, the
   projection really is recorded onto the carrier this step hands back, rather
   than that carrier's selection merely being asserted of the result. How MANY
   times it is recorded is deliberately left free: that is not part of the
   observable behaviour.

   Each recorded name must resolve against the carrier as its selection stands,
   so this step is asked only about a push-down the carrier can answer — that is
   what the `require` states. A carrier that cannot answer a projected name — its
   own model defines no column of that name and NEITHER record of its selected
   non-column outputs carries that name — cannot absorb the projection at all, and
   this step makes no claim about that case. -/
method applyProjection (mut persistent : Carrier) (mut recorded : Bool)
    (requested : List String) (projected : List String)
    return (working : Carrier)
  require shouldProject persistent requested = true →
    answerable persistent projected = true
  ensures persistent = persistentOld
  ensures shouldProject persistentOld requested = false → recorded = recordedOld
  ensures shouldProject persistentOld requested = true → recorded = true
  ensures working = workingCarrier persistentOld requested projected
  do
    -- impl-start
    -- Take a private working carrier from the shared one, then (only where the
    -- push-down applies) record the projection onto THAT carrier, noting that a
    -- recording happened. The shared carrier is never written and never recorded
    -- onto, so it is returned exactly as received; where the push-down does not
    -- apply nothing is recorded anywhere.
    let mut working := persistent
    if shouldProject persistent requested then
      recorded := true
      working := recordOnto persistent projected
      return working
    else
      return working
    -- impl-end

prove_correct applyProjection by
  loom_solve
  all_goals simp_all [workingCarrier, shouldProject, recordOnto]
