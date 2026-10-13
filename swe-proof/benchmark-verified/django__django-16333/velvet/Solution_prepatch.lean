import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/- Abstract model of a creation form's commit step.

   We model the observable state of the form and of its target object:

     * `dataValidated`     — the bound data passed the form's own validation;
     * `passwordApplied`   — the secret credential has been written onto the
       in-memory object before any persistence;
     * `objectPersisted`   — the object itself has been written to storage;
     * `relatedPersisted`  — the object's related (collection-valued) form data
       has been written to storage;
     * `deferredSaveReady`  — a deferred "save the related data" capability has
       been prepared (so it can be invoked once the object exists);
     * `credentialPending` — a credential has been written onto the in-memory
       object but its change has NOT yet been announced.  Writing the credential
       leaves the change outstanding; the object write is what announces it, and
       it announces at most the one change that is outstanding, clearing it;
     * `credentialChanges` — HOW MANY TIMES the credential change has been
       announced.  Announcing a credential change is an outward notification,
       not a private write, so its MULTIPLICITY is observable: a step that
       announces the same change twice is a different step from one that
       announces it once;
     * `objectWriteAccepted`  — whether storage ACCEPTS the object write this
       step would make.  Storage enforces its own integrity rules over and above
       the form's validation, so a write the form considers well-formed may still
       be declined; this component carries that fact about the state the step is
       asked in.  It is read-only: no step of the commit sequence changes it;
     * `relatedWriteAccepted` — likewise, whether storage ACCEPTS the related
       collection-valued write this step would make.  The two are independent:
       storage may take the object and decline its related data.  Also read-only;
     * `stepRefused`       — the step asked for an operation that is declined in
       the state it was asked in, so it ended in an error, writing nothing
       further.

   The desired behaviour (the public issue): when the caller asks to commit, a
   creation form must persist BOTH the object and all of its related
   collection-valued form data — exactly as the generic form base class does.
   A non-committing call performs neither persistence and merely prepares the
   deferred capability, leaving the credential written with its change still
   outstanding and nothing announced.  A committing call announces that one
   credential change EXACTLY ONCE — so the credential must be written before the
   object write that announces it, and no second object write may follow another
   credential write.

   Both persistence writes are asked of storage, which may decline either one.
   A committing step therefore RUNS TO COMPLETION exactly when storage accepts
   the writes it is asked for, and ends in an error exactly when storage declines
   one of them — writing nothing beyond what the accepted writes already wrote.
   The step may not dodge a declined write by declining to ask: asked to commit,
   it asks for the object write, and having stored the object it asks for the
   related write.  A non-committing step asks for neither, so it always runs to
   completion; and data that did not validate is refused outright, so a step that
   asks to build on it is declined and persists nothing at all.  Storage attaches
   related data only to an object it has already stored, and the deferred
   capability can only be driven once it has been prepared. -/

-- axioms-start
-- (none consumed: the four callees are modeled deeply as A-reference state
--  transformers in the `pure` region; G-AX validates each against its real
--  repository callee.)
-- axioms-end

-- pure-start
/- The observable state of the form and of its target object. -/
structure FormState where
  dataValidated        : Bool
  passwordApplied      : Bool
  objectPersisted      : Bool
  relatedPersisted     : Bool
  deferredSaveReady    : Bool
  credentialPending    : Bool
  credentialChanges    : Nat
  objectWriteAccepted  : Bool
  relatedWriteAccepted : Bool
  stepRefused          : Bool
deriving Inhabited

/- Prepare the deferred related-data save capability without committing the
   object (the effect of asking the generic base to build, but not store, the
   object).  Data that did not validate is declined instead, writing nothing.
   Deep model of an unchanged callee — A-reference (mapping.md §3.1). -/
def prepareDeferred (s : FormState) : FormState :=
  if s.stepRefused then s
  else if s.dataValidated then { s with deferredSaveReady := true }
  else { s with stepRefused := true }

/- Write the secret credential onto the in-memory object.  Nothing is persisted
   and nothing is announced: the write leaves the credential change OUTSTANDING,
   for the object write to announce.  Deep model of an unchanged callee —
   A-reference (mapping.md §3.2). -/
def applyCredential (s : FormState) : FormState :=
  if s.stepRefused then s
  else { s with passwordApplied := true, credentialPending := true }

/- Persist the object itself to storage.  Storage may DECLINE the write, in
   which case the step ends in an error having stored nothing and announced
   nothing — the credential's change stays outstanding.  An accepted write also
   ANNOUNCES an outstanding credential change — exactly one, and only if one is
   outstanding — and clears it, so the announcement count rises once per
   credential write that an accepted persist follows, and not at all for one that
   follows none.  Deep model of an unchanged callee — A-reference
   (mapping.md §3.3). -/
def persistObject (s : FormState) : FormState :=
  if s.stepRefused then s
  else if s.objectWriteAccepted then
    { s with objectPersisted   := true,
             credentialPending := false,
             credentialChanges := s.credentialChanges + s.credentialPending.toNat }
  else { s with stepRefused := true }

/- Persist the object's related collection-valued data to storage, by driving
   the deferred related-data save capability.  THREE things are required of the
   state it is asked in, and it declines — writing no related data — when any of
   them fails.  It is a DEFERRED capability, so it can only be driven through
   once it has actually been prepared; there is nothing to invoke before that.
   Storage attaches related data only to an object it has already stored, so
   asked to attach it to one that is not yet stored it declines.  And the write
   is still a write, which storage enforces its own integrity rules over: asked
   for one storage declines, it declines too.  When it does write, it writes only
   related data: it neither stores the object nor announces a credential change.
   Deep model of an unchanged callee — A-reference (mapping.md §3.4). -/
def persistRelated (s : FormState) : FormState :=
  if s.stepRefused then s
  else if s.deferredSaveReady && s.objectPersisted && s.relatedWriteAccepted then
    { s with relatedPersisted := true }
  else { s with stepRefused := true }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Commit step of a creation form.  `st` carries the form's own and its target
   object's observable state; `commit` is the caller's request to store
   immediately. -/
method commitForm (mut st : FormState) (commit : Bool) return (u : Unit)
  -- the step is entered on data that validated, with no error outstanding
  require st.dataValidated = true
  require st.stepRefused = false
  -- the credential is always applied, and the deferred capability is always prepared
  ensures st.passwordApplied = true
  ensures st.deferredSaveReady = true
  -- committing asks storage for the object write; when storage accepts it, the
  -- object is stored and the credential change is announced EXACTLY ONCE,
  -- leaving none outstanding: the credential is written before the object write
  -- that announces it, and no further object write follows a further credential
  -- write
  ensures commit = true  → stOld.objectWriteAccepted = true →
            st.objectPersisted = true
  ensures commit = true  → stOld.objectWriteAccepted = true →
            st.credentialChanges = stOld.credentialChanges + 1
  ensures commit = true  → stOld.objectWriteAccepted = true →
            st.credentialPending = false
  -- committing ALSO asks storage for the related write, once the object is
  -- stored; when storage accepts both, the related data is stored too
  ensures commit = true  → stOld.objectWriteAccepted = true →
            stOld.relatedWriteAccepted = true → st.relatedPersisted = true
  -- a write storage DECLINES writes nothing: the object's stored-state and the
  -- announcement are untouched and the credential's change stays outstanding
  ensures commit = true  → stOld.objectWriteAccepted = false →
            st.objectPersisted = stOld.objectPersisted
  ensures commit = true  → stOld.objectWriteAccepted = false →
            st.credentialChanges = stOld.credentialChanges
  ensures commit = true  → stOld.objectWriteAccepted = false →
            st.credentialPending = true
  ensures commit = true  →
            (stOld.objectWriteAccepted && stOld.relatedWriteAccepted) = false →
            st.relatedPersisted = stOld.relatedPersisted
  -- not committing persists neither (explicit mut-frame: post = pre)
  ensures commit = false → st.objectPersisted = stOld.objectPersisted
  ensures commit = false → st.relatedPersisted = stOld.relatedPersisted
  -- not committing announces nothing, and leaves the written credential's
  -- change outstanding for a later committing step to announce
  ensures commit = false → st.credentialChanges = stOld.credentialChanges
  ensures commit = false → st.credentialPending = true
  -- the step ends in an error EXACTLY when storage declined a write it asked
  -- for.  A committing step asks for the object write, and having stored the
  -- object asks for the related write, so it runs to completion precisely when
  -- storage accepts both — it may neither be declined while both are accepted
  -- (every operation it asks for must be one accepted in the state it is asked
  -- in) nor dodge a declined write by declining to ask for it
  ensures commit = true  →
            st.stepRefused = !(stOld.objectWriteAccepted && stOld.relatedWriteAccepted)
  -- a non-committing step asks storage for nothing, so it always completes
  ensures commit = false → st.stepRefused = false
  -- what storage will accept is a fact about the state, not something the step
  -- writes (explicit mut-frame), so a step cannot excuse itself by revising it
  ensures st.objectWriteAccepted  = stOld.objectWriteAccepted
  ensures st.relatedWriteAccepted = stOld.relatedWriteAccepted
  -- the form's own validation outcome is read-only (explicit mut-frame)
  ensures st.dataValidated = stOld.dataValidated
  do
    -- impl-start
    -- PRE-PATCH skeleton: on commit the object is persisted but the related
    -- collection-valued data is NOT (the deferred capability is built but never
    -- invoked). The frozen spec requires `commit = true → relatedPersisted`, so
    -- prove_correct MUST fail on that clause.
    st := prepareDeferred st
    st := applyCredential st
    if commit then
      st := persistObject st
    else
      st := st
    return
    -- impl-end

prove_correct commitForm by
  loom_solve <;>
    (try cases hoa : stOld.objectWriteAccepted) <;>
    (try cases hra : stOld.relatedWriteAccepted) <;>
      simp_all [prepareDeferred, applyCredential, persistObject, persistRelated]
