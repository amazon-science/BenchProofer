"""properties.py — G-PBT falsification battery for django__django-16333 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — the one region the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct commitForm`` obligation
survives with a byte-identical statement) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE. One contracted method over a mutable minimal carrier for a
creation form's commit step:

  commitForm (mut st : FormState) (commit : Bool) return (u : Unit)
    require st.dataValidated = true                                     -- (P1)
    require st.stepRefused = false                                      -- (P2)
    ensures st.passwordApplied = true                                   -- (C1)
    ensures st.deferredSaveReady = true                                 -- (C2)
    ensures commit = true  → stOld.objectWriteAccepted = true →
              st.objectPersisted = true                                 -- (C3)
    ensures commit = true  → stOld.objectWriteAccepted = true →
              st.credentialChanges = stOld.credentialChanges + 1        -- (C9)
    ensures commit = true  → stOld.objectWriteAccepted = true →
              st.credentialPending = false                              -- (C10)
    ensures commit = true  → stOld.objectWriteAccepted = true →
              stOld.relatedWriteAccepted = true →
              st.relatedPersisted = true                                -- (C4)
    ensures commit = true  → stOld.objectWriteAccepted = false →
              st.objectPersisted = stOld.objectPersisted                -- (C13)
    ensures commit = true  → stOld.objectWriteAccepted = false →
              st.credentialChanges = stOld.credentialChanges            -- (C14)
    ensures commit = true  → stOld.objectWriteAccepted = false →
              st.credentialPending = true                               -- (C15)
    ensures commit = true  →
              (stOld.objectWriteAccepted && stOld.relatedWriteAccepted)
                = false → st.relatedPersisted = stOld.relatedPersisted  -- (C16)
    ensures commit = false → st.objectPersisted = stOld.objectPersisted -- (C5)
    ensures commit = false → st.relatedPersisted = stOld.relatedPersisted -- (C6)
    ensures commit = false →
              st.credentialChanges = stOld.credentialChanges            -- (C11)
    ensures commit = false → st.credentialPending = true                -- (C12)
    ensures commit = true  → st.stepRefused =
              !(stOld.objectWriteAccepted && stOld.relatedWriteAccepted) -- (C7)
    ensures commit = false → st.stepRefused = false                     -- (C17)
    ensures st.objectWriteAccepted  = stOld.objectWriteAccepted         -- (C18)
    ensures st.relatedWriteAccepted = stOld.relatedWriteAccepted        -- (C19)
    ensures st.dataValidated = stOld.dataValidated                       -- (C8)

``FormState`` carries the ten observable facts a commit step can read or touch
— nine ``Bool`` and one ``Nat`` counter: whether the bound data passed the
form's own validation (``dataValidated``), whether the secret credential has been
written onto the in-memory object (``passwordApplied``), whether the object
itself has been stored (``objectPersisted``), whether its related
collection-valued form data has been stored (``relatedPersisted``), whether the
deferred related-data save capability has been prepared (``deferredSaveReady``),
whether a written credential's CHANGE is still OUTSTANDING — written but not yet
announced to the surrounding system (``credentialPending``), HOW MANY TIMES that
announcement has been made (``credentialChanges : Nat``), whether storage ACCEPTS
the object write the step would make (``objectWriteAccepted``) and whether it
accepts the related collection-valued write (``relatedWriteAccepted``) — two
read-only facts about the state the step is asked in, because storage enforces
its own integrity rules over and above the form's validation and may decline
either write independently — and whether the step asked for an operation that is
DECLINED in the state it was asked in, so it ended in an error and wrote nothing
further (``stepRefused``). The two ``require`` clauses admit exactly the entry
states a caller of this step reaches — validated data, no error outstanding — and
every other component is free, so the post-image must hold for BOTH values of
``commit``, for all one hundred and twenty-eight combinations of the seven
unconstrained booleans, and for EVERY value of the unconstrained counter.

The two acceptance components are what make the contract FAITHFUL rather than
idealised. The real related-data write is a database write, and a database
enforces constraints the form's own validation does not see, so a step whose data
validated can still be DECLINED by storage. A contract that claimed the step
always completes would be claiming a property the real callee does not have. So
the acceptance facts are carried explicitly, each arm states what the callee
guarantees on it, and (C7) is an IFF rather than a bare ``false``: the step is
refused EXACTLY when storage declined a write it asked for. That is strictly more
obligation than the bare version, not less — it forbids being refused when both
writes are accepted AND forbids dodging a declined write by declining to ask.

NINETEEN independent top-level clauses, each load-bearing:
  (C1) the credential is always written (both commit modes).
  (C2) the deferred related-data capability is always prepared (both modes).
  (C3) committing stores the object, WHEN storage accepts the object write.
  (C4) committing ALSO stores the related collection-valued data, when storage
       accepts both writes — the DISCRIMINATING clause the failing test observes:
       pre-change the commit branch stored the object but silently dropped the
       related data.
  (C5) not committing leaves the object's stored-state unchanged (mut-frame:
       post = pre; directive-5).
  (C6) not committing leaves the related-data stored-state unchanged (mut-frame).
  (C7) the step is refused EXACTLY when storage declined a write it asked for.
       A committing step asks for the object write, and having stored the object
       asks for the related write, so it runs to completion precisely when
       storage accepts both. This is an IFF, so it does two jobs: read left to
       right it is the RUNS-TO-COMPLETION claim, which makes the ORDER of the two
       persistence writes observable (storage attaches related data only to an
       object it has already stored, so ``persistRelated`` declines otherwise, and
       data that did not validate is refused outright, so ``prepareDeferred``
       declines); read right to left it forbids a body from DODGING a write
       storage would decline by simply not asking for it, which a bare
       ``stepRefused = false`` could not express.
  (C8) the form's own validation outcome is read-only (mut-frame), so a body
       cannot manufacture C7 by declaring the data invalid or, conversely, by
       re-validating it.
  (C13/C14/C15) a DECLINED object write writes nothing: the object's stored-state
       and the announcement count are untouched and the credential's change is
       left outstanding. These are what stop the refused arm from being a licence
       to do anything — a body cannot half-store on the arm where storage said no.
  (C16) likewise the related data is untouched whenever either write is declined.
  (C17) a non-committing step asks storage for nothing, so it ALWAYS completes;
       the refusal in C7 is the committing arm's alone.
  (C18/C19) what storage will accept is a fact about the state, not something the
       step writes (mut-frame). Without these a body could satisfy C7's right-hand
       side by revising the acceptance facts instead of by doing the work — the
       acceptance-flag analogue of C8.
  (C9) committing announces the credential change EXACTLY ONCE — one more time
       than the step was entered with, no matter how many times the step writes
       the credential or stores the object. This is the clause that makes the
       ORDER of the credential write and the object write observable, and the
       MULTIPLICITY of the object write observable with it: the announcement is
       made by the object write, and only for a credential whose change is still
       outstanding, so a body that stores before it writes the credential
       announces the wrong change (or none), and a body that writes the
       credential again after storing and then stores again announces twice.
  (C10) committing leaves NO credential change outstanding: the credential the
       step wrote is the one it announced, so nothing is left for a later step to
       announce a second time.
  (C11) not committing announces NOTHING: a step that was not asked to store
       must not notify the surrounding system that the credential changed.
  (C12) not committing leaves the written credential's change OUTSTANDING, so the
       next committing step announces it — this is what makes C1's "the
       credential is always written" a claim about the credential THIS step was
       given rather than one already on the object.

WHY (C7) IS NOT A RESTATEMENT OF THE BODY. C7 is a claim about the post-state's
``stepRefused`` component, and the two partial transformers are what give it
content: a body may call them in any order it likes, and C7 is false exactly
when it calls one in a state that transformer declines. So C7 pins the ORDER of
the persistence writes without naming an order — the property "asks nothing that
is refused" holds of every correct sequencing and fails on every reordering that
attaches related data to an object that is not yet stored.

WHY (C9) IS NOT A RESTATEMENT OF THE BODY EITHER, and why it needs a COUNTER.
C9 is a claim about the post-state's ``credentialChanges`` component relative to
the pre-state's, and what gives it content is that the credential write and the
object write are NOT independent: the write of the credential leaves its change
outstanding (``credentialPending``) and the object write consumes exactly one
outstanding change, announcing it. So the pair is neither idempotent nor
commutative, and C9 is false exactly when a body drives the pair the wrong number
of times or in the wrong order — again without naming an order. A ``Bool``
"announced" flag could not express this: the wrong bodies announce ONCE TOO OFTEN
rather than never, so the discriminating fact is a count and not a latch. G-AX
observes that count on the real callees (axiom_check.py drives three
trajectories: one credential then one store announces once, two credentials with
two stores announce twice, one credential with two stores announces once), so the
counter is a measured property of the repository's own callees, not a modelling
convenience.

ADVERSARIAL READ of the sibling classes on this carrier:
  * FRAME / PERMISSION-MUTATION — the sibling's mandatory fiat family
    (``atk_fold`` / ``atk_unfold_poke`` / ``atk_echo_transfer``) tries to earn a
    body-less capability ``relations_done(self)`` by folding it, poking the
    observable fields, or transferring a scratch instance's capability — all
    rejected by the permission/abstraction-predicate system for insufficient
    permission. Lean/Velvet are referentially transparent: there is no heap, no
    fractional permission, and no body-less capability predicate. The
    discriminating fact ``relatedPersisted`` is a plain ``Bool`` field of the
    carrier. So "conjure the capability" (fold) collapses to: a body that fails
    to set ``relatedPersisted`` on the commit arm — which clause (C4) catches
    directly, and which IS ``weak-prepatch-no-related`` /
    ``weak-dead-guard-skips-related``. Poking the fields to the RIGHT values is
    not an attack here at all but a correct implementation (measured: it
    verifies), because on this carrier the observable fields ARE the specified
    state — the permission wall the sibling needs exists only because its
    capability is not a field. The transfer rival, however, IS expressible and
    IS wrong: doing the work against a throwaway state that is not the subject
    is shipped as ``weak-scratch-state-transfer`` (the port had recorded it as
    inexpressible; the audit retracted that and landed it).
  * PARTIAL-DOMAIN — APPLIES: a body correct on one arm but diverging on the
    other. The near-miss dead-guard skips the related-data save under a guard
    that is provably false after the object write; the unconditional rivals
    write on the commit=false arm. Each is refuted at a concrete point on the
    sub-domain where it goes wrong.
  * SELF-ECHO / OBLIGATION-LEAK — VACUOUS. The sibling's ``atk_selfrecurse``
    re-derives the contract from the function-under-spec via self-recursion,
    caught by nagini's MustTerminate obligation-leak check. ``commitForm``'s
    ``do`` block is a straight-line skeleton with no recursion available to it in
    the modeled fragment; there is no self-call to write and no obligation-leak
    analogue on this carrier. Dropped, not fabricated.
  * ORDERING — APPLIES, and is now DEFENDED. The sibling rejects running the
    deferred save BEFORE the object write, because storage attaches related rows
    only to an object whose primary key already exists. An earlier revision of
    this carrier could not see that: ``persistRelated`` was a TOTAL setter that
    wrote its component from any state, so a reordered body discharged every
    clause and verified (measured, exit 0) even though its faithful counterpart
    raises instead of persisting and does not resolve. That was a hole in the
    contract, not a benign collapse of the class, and it is closed by modelling
    the two callees at the fidelity their real counterparts have: they are
    PARTIAL, declining (``stepRefused``) when asked in a state they do not
    accept, and (C7) obliges the step to run to completion. The reordered rival
    is now refutable and is shipped as ``weak-related-before-object``, with the
    C7-only ``weak-refused-step-noncommit`` and the C8-only
    ``weak-clear-validation-flag`` guarding the two ways a body could try to
    satisfy C7 without doing the work.
    A SECOND ordering axis was found the same way and closed the same way, by an
    independent reviewer's rival rather than by argument. ``stepRefused`` sees the
    order of the two PERSISTENCE writes, because one of them declines. It cannot
    see the order of the CREDENTIAL write against the object write, because
    neither declines: both were modelled as idempotent, commuting boolean
    setters, so the carrier recorded only WHETHER each had fired. In the
    repository they are neither. Writing the credential leaves its change
    outstanding and the object write ANNOUNCES that change — once, to the
    surrounding system, and the notification's multiplicity is observable and is
    pinned at exactly one by a test the change must not regress. A rival that
    stored the object, saved the related data, then wrote the credential and
    stored AGAIN discharged every clause of the earlier revision (measured: exit
    0) while its faithful counterpart announces the change TWICE and does not
    resolve. That was a second ``verify`` does-not-imply ``resolve`` break of the
    same shape as the first — an unmodelled observable, not a benign
    abstraction — and it is closed the same way: the pair is modelled at the
    fidelity it has (``applyCredential`` leaves ``credentialPending``,
    ``persistObject`` consumes it and increments ``credentialChanges``), and C9 to
    C12 pin the count and the outstanding flag on both arms. SEVEN rivals on this
    axis are shipped below: ``weak-resave-after-credential`` (the rival the
    reviewer landed), ``weak-credential-after-object``, ``weak-double-announce``,
    ``weak-skip-object-when-already-persisted``,
    ``weak-leave-pending-on-commit``, ``weak-announce-on-noncommit`` (C11 alone)
    and ``weak-count-pinned-to-one`` (which pins C9's RELATIVE reading).
    They were authored in DISTINCT attack families so that the block is not seven
    spellings of one idea: over-approximation (``weak-double-announce``: announce
    more changes than exist), partial-domain guard (``weak-skip-object-when-
    already-persisted``: right on the F2P-shaped input, wrong off it), boundary
    token swap (``weak-credential-after-object``: the same three calls with two
    adjacent statements exchanged), oracle echo (``weak-count-pinned-to-one``:
    write the value the postcondition expects instead of letting the callees
    produce it), and two that attack the freedom the repair itself leaves —
    ``weak-announce-on-noncommit`` and ``weak-leave-pending-on-commit`` exploit
    that C9/C11 constrain the count only RELATIVE to entry and only per arm, by
    moving the announcement onto the still-standing arm and by arming one for the
    CALLER to make.
    FIVE of the seven are expressible on the earlier carrier, and all five VERIFY
    against the earlier eight-clause revision — measured, exit 0 each — while all
    seven are refuted here, measured, exit 1 each, on the C9/C10/C11 goals. So the
    four added clauses are strictly MORE obligation over the same admitted domain,
    not a restatement of the eight. The remaining two rivals name the new
    components directly and have no counterpart on the earlier carrier. Over-fit
    in the other direction is guarded too:
    ``pos-control-double-store-single-announce`` stores the object twice with no
    second credential write, announces once, and MUST verify (measured: it does) —
    its faithful counterpart is the reviewer's own atk_11, recorded RESOLVED
    87/87, so a contract that had pinned "one object write" instead of "one
    announcement" would have rejected a resolving implementation.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``if`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so
each reject rival reaches it through Velvet's own tester machinery:
``commitFormTester st commit = false`` says the extracted program's observable
(the mutated ``st``'s eight components) violates the method's postcondition at
that concrete starting state and commit request. Checked in a file whose
``prove_correct`` block has been stripped, so no tactic script can mask the
verdict. ``FormState`` derives ``Inhabited`` and its nine ``Bool`` fields and
one ``Nat`` counter all have decidable equality, so every witness closes by
``decide``. Each witness binds nothing (literal starting state + literal
commit), so there are no hypotheses to be inconsistent — no consistency probe
applies.

The derived tester is ``if decide (pre st) then (match exec with res r =>
decide (post ...) | _ => false) else true`` (Velvet ``Syntax.lean``
``derive_tester_for``), so a witness state that failed the precondition would
make the tester ``true`` and could not refute anything. Every reject witness
below is therefore built by ``_st``, which pins the two required components
(``dataValidated := true``, ``stepRefused := false``) and varies the other eight:
each witness is a point INSIDE the admitted domain, and the refutation it
records is the postcondition's, never the precondition's.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries axiom-
soundness / containment probes over the real Django callees
(``BaseModelForm.save(commit=False)`` / ``Model.save()`` / ``save_m2m``); that is
G-AX's job (axiom_check.py / mapping.md) and the G-PBT gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-16333"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body, everything strictly
# ---- between the method's `-- impl-start` / `-- impl-end`. Every variant
# ---- replaces exactly this text, so each edit lies wholly inside the one
# ---- impl region and same_spec holds by construction (both facts asserted at
# ---- load by _swap).
_GOLD_IMPL = (
    "    st := prepareDeferred st\n"
    "    st := applyCredential st\n"
    "    if commit then\n"
    "      st := persistObject st\n"
    "      if st.deferredSaveReady then\n"
    "        st := persistRelated st\n"
    "      else\n"
    "        st := st\n"
    "    else\n"
    "      st := st\n"
    "    return"
)

assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted; update _GOLD_IMPL"


def _impl(body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _GOLD_IMPL, body)


# ---- witness preamble. Reaches the method contract through Velvet's tester
# ---- machinery; checked in a file whose `prove_correct` block is stripped. The
# ---- method returns `Unit` and takes a mutable starting state `st` plus the
# ---- value parameter `commit`, so the tester takes (st, commit) and reports
# ---- whether the resulting observable satisfies the postcondition. FormState's
# ---- nine flag fields are `Bool` and its announcement counter is `Nat`, whose
# ---- equalities `decide` settles directly.
def _tester(body):
    return ("extract_program_for commitForm\n"
            "prove_precondition_decidable_for commitForm\n"
            "prove_postcondition_decidable_for commitForm\n"
            "derive_tester_for commitForm\n\n" + body)


def _st(pw, obj, rel, df, cp=False, cc=0, oa=True, ra=True):
    """A concrete starting state INSIDE the admitted domain.

    The two required components are pinned (`dataValidated := true`,
    `stepRefused := false`) because the derived tester short-circuits to `true`
    when the precondition fails, so a witness outside the domain would refute
    nothing. The eight free components are the arguments, and the reject cases
    below vary each of them: the flags over {true, false} and the announcement
    counter `cc` over several concrete naturals (the clauses that read it are
    relative — `= stOld.credentialChanges + 1` — so a witness must show they are
    not accidentally satisfied at 0 alone).

    `oa` / `ra` are the two storage-acceptance facts. They default to True — the
    accepting state, where every clause conditioned on acceptance is live — so a
    rival that is wrong on the ordinary accepted trajectory is still refuted at a
    witness that says nothing about declines. Witnesses that set either to False
    are the ones that exercise the declined arms (C13-C16) and the right-to-left
    reading of C7, and they are used by the rivals that attack exactly those."""
    b = lambda x: "true" if x else "false"
    return ("{ dataValidated := true, passwordApplied := %s, "
            "objectPersisted := %s, relatedPersisted := %s, "
            "deferredSaveReady := %s, credentialPending := %s, "
            "credentialChanges := %d, objectWriteAccepted := %s, "
            "relatedWriteAccepted := %s, stepRefused := false }"
            % (b(pw), b(obj), b(rel), b(df), b(cp), cc, b(oa), b(ra)))


def _witness(st, commit):
    c = "true" if commit else "false"
    return _tester(
        f"example : commitFormTester {st} {c} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else the post-image is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-guard-dropped",
        "kind": "soundness",
        "expect": "verify",
        # The inner guard is provably true after `prepareDeferred` sets the
        # deferred capability, so on the commit arm running the related-data
        # save UNCONDITIONALLY is observationally identical to the frozen body.
        # A control-shape reshape (drop the always-true guard); the value flow
        # is unchanged, so the frozen proof still discharges the byte-identical
        # obligation (verified out-of-band with a real build).
        "module": _impl(
            "    st := prepareDeferred st\n"
            "    st := applyCredential st\n"
            "    if commit then\n"
            "      st := persistObject st\n"
            "      st := persistRelated st\n"
            "    else\n"
            "      st := st\n"
            "    return"),
        "rationale": (
            "structurally different CORRECT impl: the deferred capability is "
            "always prepared, so the inner guard is provably true on the commit "
            "arm and dropping it runs the related-data save unconditionally — "
            "behaviourally identical to the frozen body. All eight clauses "
            "(C1 credential, C2 capability, C3 object-on-commit, C4 related-on-"
            "commit, C5/C6 mut-frame on non-commit, C7 runs-to-completion — the "
            "related-data save is still asked for only AFTER the object write, "
            "so it is never declined — C8 validation frame) still discharge. "
            "Ports the "
            "nagini pos-control-guard-dropped; if it fails => SPEC-TOO-STRONG "
            "(over-fit to the guarded code shape). SCOPE OF THE EVIDENCE (audit "
            "correction): this reshape is DEFINITIONALLY EQUAL to the frozen "
            "body — measured, `rfl` closes the equation between the two state "
            "transformers, because the dropped guard reduces on a component the "
            "preceding setter pins to `true`. So its verifying is a weak "
            "control: it shows the spec does not reject the collapsed "
            "conditional, but it cannot detect over-fitting that survives "
            "defeq. pos-control-record-literal is the control that can."),
    },
    {
        "id": "pos-control-record-literal",
        "kind": "soundness",
        "expect": "verify",
        # A CORRECT impl whose shape is not reachable from the frozen body by
        # reduction: no branch in the statement sequence at all. The whole
        # post-state is one record literal whose object/related components are
        # `if`-EXPRESSIONS on `commit`, so the obligation must be discharged by
        # real case analysis on `commit` rather than by unfolding the four
        # setters. Added by the audit: the other two positives are
        # DEFINITIONALLY EQUAL to the frozen body (measured: `rfl` closes the
        # equation between each of their state transformers and the frozen one),
        # so neither forces the proof pipeline to do any work the frozen shape
        # did not already do. For this body `rfl` does NOT close that equation
        # (measured), so it is the battery's only load-bearing soundness control.
        "module": _impl(
            "    st := { dataValidated := st.dataValidated,\n"
            "            passwordApplied := true,\n"
            "            objectPersisted := (if commit && st.objectWriteAccepted\n"
            "                                then true else st.objectPersisted),\n"
            "            relatedPersisted := (if commit && st.objectWriteAccepted\n"
            "                                    && st.relatedWriteAccepted\n"
            "                                 then true else st.relatedPersisted),\n"
            "            deferredSaveReady := true,\n"
            "            credentialPending := (if commit && st.objectWriteAccepted\n"
            "                                  then false else true),\n"
            "            credentialChanges := (if commit && st.objectWriteAccepted\n"
            "                                  then st.credentialChanges + 1\n"
            "                                  else st.credentialChanges),\n"
            "            objectWriteAccepted := st.objectWriteAccepted,\n"
            "            relatedWriteAccepted := st.relatedWriteAccepted,\n"
            "            stepRefused := (if commit\n"
            "                            then !(st.objectWriteAccepted\n"
            "                                     && st.relatedWriteAccepted)\n"
            "                            else false) }\n"
            "    return"),
        "rationale": (
            "structurally different CORRECT impl that is NOT definitionally "
            "equal to the frozen body: the branch is pushed inside a single "
            "record literal as `if`-expressions on `commit`, so the statement "
            "sequence is branch-free and the obligation is discharged by case "
            "analysis on `commit` instead of by reducing the four setters. It "
            "reaches the same final state on every arm: C1/C2 are pinned "
            "unconditionally, C3/C4/C9/C10 hold on the commit arm WHEN THE "
            "OBJECT WRITE IS ACCEPTED (the announcement counter is raised by "
            "exactly one relative to the pre-state's and the outstanding change "
            "is cleared), C13/C14/C15/C16 hold on the commit arm when it is "
            "DECLINED because each `if` then falls to the else branch that "
            "copies the pre-value and leaves the change outstanding, "
            "C5/C6/C11/C12 hold because the non-commit arm copies the pre-values "
            "of the two persistence components and of the counter verbatim and "
            "leaves the change outstanding, C7 holds because the refusal "
            "component is written to exactly the negated conjunction of the two "
            "acceptance facts on the commit arm and to `false` off it, C18/C19 "
            "hold because the literal copies the two acceptance facts rather "
            "than revising them, and C8 holds because the "
            "literal carries the validation outcome across from the "
            "pre-state, copied rather than recomputed. It "
            "is also the control that shows C7 is not over-fit to the frozen "
            "call sequence: this body calls NONE of the four transformers, so "
            "it cannot 'ask' for anything, and C7 must be discharged from the "
            "frame rather than from the order of any calls. Measured with a "
            "real build: "
            "verifies (exit 0), while `rfl` does not equate this transformer to "
            "the frozen one — unlike pos-control-guard-dropped and "
            "pos-control-setter-reorder, which are both defeq collapses. If it "
            "failed => SPEC-TOO-STRONG (over-fit to the branch-in-statement "
            "shape)."),
    },
    {
        "id": "pos-control-setter-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reorder the two frame-independent prefix setters (write the credential
        # before preparing the deferred capability). They touch disjoint fields,
        # so the final state is identical; a control-shape reshape only.
        "module": _impl(
            "    st := applyCredential st\n"
            "    st := prepareDeferred st\n"
            "    if commit then\n"
            "      st := persistObject st\n"
            "      if st.deferredSaveReady then\n"
            "        st := persistRelated st\n"
            "      else\n"
            "        st := st\n"
            "    else\n"
            "      st := st\n"
            "    return"),
        "rationale": (
            "correct reshape: the two prefix setters touch disjoint fields "
            "(passwordApplied vs deferredSaveReady), so writing the credential "
            "before preparing the deferred capability reaches the identical "
            "final state. All eight clauses still discharge and the frozen proof "
            "closes as-is; demonstrates the spec is not over-fit to the "
            "syntactic order of the two frame-independent setters (else "
            "SPEC-TOO-STRONG). SCOPE OF THE EVIDENCE (audit correction): like "
            "pos-control-guard-dropped this reshape is DEFINITIONALLY EQUAL to "
            "the frozen body — measured, `rfl` closes the equation between the "
            "two transformers, since two record updates on disjoint fields "
            "commute by reduction. A weak control for the same reason; kept "
            "because setter-order over-fitting is a real failure mode worth a "
            "cheap probe, but the load-bearing positive is "
            "pos-control-record-literal."),
    },
    {
        "id": "pos-control-double-store-single-announce",
        "kind": "soundness",
        "expect": "verify",
        # The control that keeps (C9) from being an over-constraint. It stores the
        # object TWICE on the commit arm with no second credential write in
        # between, so the announcement is made once and only once: the second
        # store finds no outstanding change. A contract that pinned "exactly one
        # object write" instead of "exactly one announcement" would reject this,
        # and it would be WRONG to: the real double-store IS a resolving
        # implementation (measured — see the rationale). This is the positive that
        # separates the two readings.
        "module": _impl(
            "    st := prepareDeferred st\n"
            "    st := applyCredential st\n"
            "    if commit then\n"
            "      st := persistObject st\n"
            "      if st.deferredSaveReady then\n"
            "        st := persistRelated st\n"
            "      else\n"
            "        st := st\n"
            "      st := persistObject st\n"
            "      if st.deferredSaveReady then\n"
            "        st := persistRelated st\n"
            "      else\n"
            "        st := st\n"
            "    else\n"
            "      st := st\n"
            "    return"),
        "rationale": (
            "structurally different CORRECT impl: both persistence steps are run "
            "twice on the commit arm, with no credential write between the two "
            "object stores. "
            "The announcement is therefore made exactly ONCE — the first store "
            "consumes the outstanding change and the second finds none — so "
            "C9/C10 hold alongside C1-C8. Its faithful counterpart calls "
            "`user.save()` a second time after the related-data save; "
            "`django/contrib/auth/base_user.py:74-78` announces only when "
            "`_password is not None` and clears it at the first announcement, so "
            "the second store announces nothing and the notification count stays "
            "at the 1 that `tests/auth_tests/test_forms.py:113-127` asserts. That "
            "counterpart is MEASURED to resolve (it is the audit panel's atk_11, "
            "recorded RESOLVED, and it is the discriminator that separates it "
            "from the atk_12 break). So this case is the guard against the "
            "obvious over-fit of the counter clause: if it FAILED, C9 would have "
            "been written as 'store the object at most once' rather than "
            "'announce the credential change exactly once', and the spec would "
            "reject a resolving implementation => SPEC-TOO-STRONG. What carries "
            "the case is not a reshape that reduces away: the second store is a "
            "real extra application of the announcing transformer, and its "
            "harmlessness comes from the state the first one left (no "
            "outstanding change, so nothing to announce) rather than from the "
            "clause being blind to how many stores happen. Measured with a real "
            "build: verifies, exit 0."),
    },

    # =====================================================================
    # ADMISSIBILITY — the F2P-shaped input must be INSIDE the admitted domain,
    # and the eight-clause post-image must be jointly SATISFIABLE there by a
    # gold-shaped computation. The F2P shape is a commit=true call on a form
    # whose bound data validated and which has not errored, with nothing yet
    # persisted: (P1) and (P2) hold at that point and the other four components
    # are unconstrained, so it is admitted. The frozen impl discharging all
    # eight ensures IS the satisfiability witness. MUST verify, else
    # SPEC-UNSATISFIABLE (or, if the precondition had excluded the F2P shape,
    # SPEC-VACUOUS).
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,  # frozen impl; same_spec trivially, must verify
        "rationale": (
            "the two `require` clauses admit exactly the states a caller of this "
            "step reaches — the data validated and no error outstanding — which "
            "is precisely the F2P shape (commit=true on a fresh validated form, "
            "nothing persisted). Both requirements are DISCHARGED by the caller "
            "in the real flow rather than assumed away: the step is only reached "
            "after validation succeeds, and it is the first thing that runs, so "
            "no earlier operation can have been declined. The gold impl "
            "discharging all eight ensures on that domain is the witness that "
            "the post-image is jointly satisfiable, and in particular that C7 "
            "(runs to completion) is co-satisfiable with C3/C4 rather than "
            "excluding them. Re-aimed from the nagini admiss-commit-true, whose "
            "read-only-precondition half has no counterpart on this "
            "referentially-transparent carrier. Else SPEC-UNSATISFIABLE."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete starting state + commit value, and the refinement argument that
    # its faithful real counterpart would NOT resolve the failing test. The
    # witnesses vary `commit` over {true, false} and each of the four stOld
    # fields over {true, false}, so no binder is pinned across the battery.
    # =====================================================================
    {
        "id": "weak-prepatch-no-related",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-change body: the commit branch stores the object but never
        # runs the related-data save. Correct on C1/C2/C3/C5/C6; violates C4.
        "module": _impl(
            "    st := prepareDeferred st\n"
            "    st := applyCredential st\n"
            "    if commit then\n"
            "      st := persistObject st\n"
            "    else\n"
            "      st := st\n"
            "    return"),
        "refinement": (
            "this is the verbatim pre-change commit branch: the object is "
            "stored but the related collection-valued data is never persisted. "
            "Its faithful counterpart is the unpatched repo; on a commit=true "
            "save the related through-rows are never written, so the failing "
            "test's assertion that the selected related objects are present "
            "FAILS. It is the exact defect the fix corrects and would NOT "
            "resolve."),
        "rationale": (
            "REJECT from clause (C4) `commit = true → st.relatedPersisted = "
            "true`: on the commit arm the body never sets relatedPersisted, so "
            "the post-image demands it be true where the body leaves it false. "
            "Clauses C1/C2/C3/C5/C6 are kept correct, isolating C4. Refuted at "
            "an all-false start, commit=true. If it verified => SPEC-TOO-WEAK "
            "(admits the bug)."),
        "witness": _witness(_st(0, 0, 0, 0), True),
    },
    {
        "id": "weak-dead-guard-skips-related",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss: guard the related-data save on `objectPersisted = false`,
        # which is provably false right after the object write, so the save is
        # dead code and the related data is never persisted. Same effect as
        # prepatch, distinct code shape and distinct witness point.
        "module": _impl(
            "    st := prepareDeferred st\n"
            "    st := applyCredential st\n"
            "    if commit then\n"
            "      st := persistObject st\n"
            "      if st.objectPersisted = false then\n"
            "        st := persistRelated st\n"
            "      else\n"
            "        st := st\n"
            "    else\n"
            "      st := st\n"
            "    return"),
        "refinement": (
            "after the object is stored, `objectPersisted` is true, so the "
            "`objectPersisted = false` guard never fires and the related-data "
            "save is dead code — behaviourally identical to the pre-change body. "
            "On a commit=true save the related through-rows are never written, "
            "so the failing test FAILS. A faithful dead-guard patch does NOT "
            "resolve."),
        "rationale": (
            "REJECT from clause (C4): the related-data save is statically "
            "reachable but its guard is provably false after the object write, "
            "so on the commit arm relatedPersisted stays false where the "
            "post-image demands true. Refuted at start (pw,obj,rel,df)="
            "(T,T,F,T), commit=true — a DISTINCT point from weak-prepatch (which "
            "would also mis-behave on an all-false start, so this point varies "
            "the stOld binders). If it verified => SPEC-TOO-WEAK."),
        "witness": _witness(_st(1, 1, 0, 1), True),
    },
    {
        "id": "weak-drop-object",
        "kind": "uniqueness",
        "expect": "reject",
        # Commit branch stores the related data but omits the object write.
        # Isolates C3.
        "module": _impl(
            "    st := prepareDeferred st\n"
            "    st := applyCredential st\n"
            "    if commit then\n"
            "      if st.deferredSaveReady then\n"
            "        st := persistRelated st\n"
            "      else\n"
            "        st := st\n"
            "    else\n"
            "      st := st\n"
            "    return"),
        "refinement": (
            "the object itself is never stored on commit — a faithful "
            "counterpart writes the related data against an object that was "
            "never persisted, so the primary row is missing and the failing "
            "test (which reads the persisted object and its related data back) "
            "FAILS. A patch that skips storing the object does NOT resolve."),
        "rationale": (
            "REJECT from clause (C3) `commit = true → st.objectPersisted = "
            "true`: on the commit arm the body never sets objectPersisted. "
            "Refuted at start (F,F,F,T), commit=true. Distinct clause and "
            "distinct point from the C4 rivals. If it verified => "
            "SPEC-TOO-WEAK."),
        "witness": _witness(_st(0, 0, 0, 1), True),
    },
    {
        "id": "weak-drop-credential",
        "kind": "uniqueness",
        "expect": "reject",
        # Omit the credential write entirely. Isolates C1 (holds on both commit
        # modes, so a commit=true witness suffices).
        "module": _impl(
            "    st := prepareDeferred st\n"
            "    if commit then\n"
            "      st := persistObject st\n"
            "      if st.deferredSaveReady then\n"
            "        st := persistRelated st\n"
            "      else\n"
            "        st := st\n"
            "    else\n"
            "      st := st\n"
            "    return"),
        "refinement": (
            "the secret credential is never written onto the in-memory object, "
            "so a faithful counterpart persists an object whose credential does "
            "not verify — the created account cannot authenticate. The suite "
            "asserts the credential is applied; this would NOT resolve."),
        "rationale": (
            "REJECT from clause (C1) `st.passwordApplied = true`: the body "
            "removes the credential write, so passwordApplied stays false on "
            "every path. Refuted at start (F,F,T,F), commit=true — the "
            "relatedPersisted field is started TRUE here (unlike the other "
            "commit=true rivals) so the stOld.relatedPersisted binder is "
            "exercised. If it verified => SPEC-TOO-WEAK."),
        "witness": _witness(_st(0, 0, 1, 0), True),
    },
    {
        "id": "weak-drop-deferred-prep",
        "kind": "uniqueness",
        "expect": "reject",
        # Omit preparing the deferred capability. Isolates C2 (holds on both
        # commit modes); refuted on the commit=false arm.
        "module": _impl(
            "    st := applyCredential st\n"
            "    if commit then\n"
            "      st := persistObject st\n"
            "      if st.deferredSaveReady then\n"
            "        st := persistRelated st\n"
            "      else\n"
            "        st := st\n"
            "    else\n"
            "      st := st\n"
            "    return"),
        "refinement": (
            "the deferred related-data save capability is never prepared, so a "
            "faithful counterpart has no handle to drive the related-data write "
            "through on commit (and none is installed for a later manual "
            "commit-false flow). The post-image pins the capability as always "
            "prepared; this would NOT resolve."),
        "rationale": (
            "REJECT from clause (C2) `st.deferredSaveReady = true`: the body "
            "removes the capability preparation, so deferredSaveReady stays "
            "false on every path. Refuted at start (T,F,F,F), commit=FALSE — "
            "exercising C2 on the non-commit arm and varying commit and the "
            "passwordApplied binder. If it verified => SPEC-TOO-WEAK."),
        "witness": _witness(_st(1, 0, 0, 0), False),
    },
    {
        "id": "weak-guard-before-prepare",
        "kind": "uniqueness",
        "expect": "reject",
        # Added by the audit. The commit branch keeps BOTH persistence calls and
        # the real guard, but the deferred capability is prepared only AFTER the
        # branch, so the guard reads the PRE-STATE component instead of the
        # prepared one. On a starting state whose capability component is false
        # the guard does not fire and the related data is never stored, while C2
        # still holds because the preparation does eventually run. This is the
        # only rival that attacks C4 at a point where the guard's hypothesis is
        # false rather than where the guard is dead or absent.
        "module": _impl(
            "    st := applyCredential st\n"
            "    if commit then\n"
            "      st := persistObject st\n"
            "      if st.deferredSaveReady then\n"
            "        st := persistRelated st\n"
            "      else\n"
            "        st := st\n"
            "    else\n"
            "      st := st\n"
            "    st := prepareDeferred st\n"
            "    return"),
        "refinement": (
            "the deferred related-data capability is prepared only after the "
            "commit branch has already run, so the branch's guard consults the "
            "state as it was on entry. A faithful counterpart tests for the "
            "capability before anything has installed it: on a commit=true call "
            "the guard is false, the related collection-valued data is never "
            "written, and the failing test's assertion that the selected "
            "related objects are present FAILS. Reordering the preparation "
            "after the branch does NOT resolve."),
        "rationale": (
            "REJECT from clause (C4) `commit = true → st.relatedPersisted = "
            "true`: the guard is evaluated before the capability component has "
            "been set, so on a starting state with that component false the "
            "related-data save is skipped while the post-image demands it. C2 "
            "still holds (the preparation runs on every path), which is what "
            "isolates C4 here. Refuted at start (T,T,F,F), commit=true — a "
            "point no other rival uses, and the only one where the guard's own "
            "hypothesis is what fails. Measured with real builds: the rival "
            "does not verify (the obligation leaves "
            "`stOld.relatedPersisted = true` unsolved under hypothesis "
            "`stOld.deferredSaveReady = false`), the witness elaborates against "
            "it (exit 0), and against the frozen solution `decide` proves the "
            "same claim FALSE (exit 1). If it verified => SPEC-TOO-WEAK."),
        "witness": _witness(_st(1, 1, 0, 0), True),
    },
    {
        "id": "weak-scratch-state-transfer",
        "kind": "uniqueness",
        "expect": "reject",
        # Recovered by the audit from the nagini weak-cross-instance-transfer,
        # which the port had recorded as inexpressible here. It is expressible:
        # FormState is an ordinary value and the impl region admits a local
        # binding, so the persistence work can be done on a THROWAWAY second
        # state and only the object component copied back onto the subject. The
        # related-data fact is thereby "earned" somewhere that does not count.
        "module": _impl(
            "    st := prepareDeferred st\n"
            "    st := applyCredential st\n"
            "    if commit then\n"
            "      let scratch := persistRelated (persistObject st)\n"
            "      st := { st with objectPersisted := scratch.objectPersisted }\n"
            "    else\n"
            "      st := st\n"
            "    return"),
        "refinement": (
            "the related collection-valued data is written against a throwaway "
            "copy of the state rather than the object the caller is committing, "
            "and only the object's own stored-flag is carried back. A faithful "
            "counterpart drives the related-data write through a different "
            "target, so the submitted object's related rows are never written: "
            "the failing test reads the committed object's related objects back "
            "and FAILS. Doing the work on the wrong target does NOT resolve."),
        "rationale": (
            "REJECT from clause (C4) `commit = true → st.relatedPersisted = "
            "true`: the related-data write lands on a local scratch value that "
            "is then discarded, so the subject state's relatedPersisted stays "
            "at its pre-value while the post-image demands true. C3 is kept "
            "correct (the object component is copied back), isolating C4 on a "
            "shape distinct from every other C4 rival — the persistence call is "
            "actually EXECUTED here, just against the wrong target, which is "
            "the point the nagini sibling's capability-transfer attack made. "
            "Refuted at start (T,F,F,F), commit=true. Measured with real "
            "builds: the rival does not verify (`stOld.relatedPersisted = true` "
            "unsolved), the witness elaborates against it (exit 0), and "
            "`decide` proves the claim FALSE against the frozen solution "
            "(exit 1). If it verified => SPEC-TOO-WEAK."),
        "witness": _witness(_st(1, 0, 0, 0), True),
    },
    {
        "id": "weak-clear-on-noncommit",
        "kind": "uniqueness",
        "expect": "reject",
        # Added by the audit. The mut-frame clauses C5/C6 are equalities, so they
        # are violated in TWO directions; the unconditional rivals only ever
        # drive a component false -> true. This one drives both components
        # true -> false on the non-commit arm, which no existing witness reaches
        # (every commit=false witness in the ported set starts the component it
        # checks at false, where a clear is invisible).
        "module": _impl(
            "    st := prepareDeferred st\n"
            "    st := applyCredential st\n"
            "    if commit then\n"
            "      st := persistObject st\n"
            "      if st.deferredSaveReady then\n"
            "        st := persistRelated st\n"
            "      else\n"
            "        st := st\n"
            "    else\n"
            "      st := { st with objectPersisted := false, relatedPersisted := false }\n"
            "    return"),
        "refinement": (
            "on a non-committing call the body actively resets both persistence "
            "components to not-stored. A faithful counterpart hands back an "
            "object it reports as unstored even when the caller had already "
            "stored it and its related data — a non-committing call is supposed "
            "to leave storage alone in BOTH directions, so callers that commit "
            "first and then re-run a non-committing call observe their "
            "persisted state disappear. It does NOT resolve, and it breaks the "
            "non-committing contract the wider suite relies on."),
        "rationale": (
            "REJECT from BOTH mut-frame clauses (C5) and (C6): they are "
            "equalities `post = pre`, and this body drives each component "
            "true -> false on the non-commit arm. The ported unconditional "
            "rivals only ever violate the frame false -> true, so this is the "
            "first case to exercise the opposite direction — and it is a real "
            "gap, since every existing commit=false witness starts the "
            "component it checks at false, where a clear leaves no trace. "
            "Refuted at start (F,T,T,T), commit=FALSE: both components start "
            "TRUE and end false. Measured with real builds: the rival does not "
            "verify (both frame goals unsolved), the witness elaborates against "
            "it (exit 0), and `decide` proves the claim FALSE against the "
            "frozen solution (exit 1). If it verified => SPEC-TOO-WEAK."),
        "witness": _witness(_st(0, 1, 1, 1), False),
    },
    {
        "id": "weak-unconditional-object",
        "kind": "uniqueness",
        "expect": "reject",
        # Store the object regardless of `commit`, so commit=false still writes
        # it. Isolates C5 (the object mut-frame on the non-commit arm).
        "module": _impl(
            "    st := prepareDeferred st\n"
            "    st := applyCredential st\n"
            "    st := persistObject st\n"
            "    if commit then\n"
            "      if st.deferredSaveReady then\n"
            "        st := persistRelated st\n"
            "      else\n"
            "        st := st\n"
            "    else\n"
            "      st := st\n"
            "    return"),
        "refinement": (
            "storing the object on commit=false contradicts the documented "
            "commit=false contract (build but do not persist, returning the "
            "unsaved instance). Callers that rely on commit=false NOT touching "
            "storage would break; a faithful always-store patch does NOT "
            "preserve the non-commit behaviour."),
        "rationale": (
            "REJECT from clause (C5) `commit = false → st.objectPersisted = "
            "stOld.objectPersisted`: the body stores the object unconditionally, "
            "so for commit=false objectPersisted flips from its pre-value to "
            "true. Refuted at start (F,F,T,T), commit=FALSE: pre objectPersisted "
            "is false, post is true, violating the frame. If it verified => "
            "SPEC-TOO-WEAK."),
        "witness": _witness(_st(0, 0, 1, 1), False),
    },
    {
        "id": "weak-unconditional-related",
        "kind": "uniqueness",
        "expect": "reject",
        # Store the related data on the non-commit arm too. Isolates C6 (the
        # related-data mut-frame on the non-commit arm).
        "module": _impl(
            "    st := prepareDeferred st\n"
            "    st := applyCredential st\n"
            "    if commit then\n"
            "      st := persistObject st\n"
            "      if st.deferredSaveReady then\n"
            "        st := persistRelated st\n"
            "      else\n"
            "        st := st\n"
            "    else\n"
            "      st := persistRelated st\n"
            "    return"),
        "refinement": (
            "persisting the related collection-valued data on commit=false "
            "writes related through-rows for an object that was deliberately "
            "NOT stored — orphaned associations against a missing/uncommitted "
            "row. A faithful patch that stores related data on the non-commit "
            "path breaks the deferred-save contract and does NOT resolve."),
        "rationale": (
            "REJECT from clause (C6) `commit = false → st.relatedPersisted = "
            "stOld.relatedPersisted`: the else arm stores the related data, so "
            "for commit=false relatedPersisted flips from its pre-value to true. "
            "Refuted at start (F,T,F,F), commit=FALSE: pre relatedPersisted is "
            "false, post is true, violating the frame — and objectPersisted "
            "started TRUE here, exercising that binder. If it verified => "
            "SPEC-TOO-WEAK."),
        "witness": _witness(_st(0, 1, 0, 0), False),
    },
    {
        "id": "weak-related-before-object",
        "kind": "uniqueness",
        "expect": "reject",
        # The ORDERING rival. The commit branch performs BOTH persistence steps,
        # with the real guard, but asks for the related-data save FIRST — before
        # the object it belongs to has been stored. Storage attaches related data
        # only to an object it has already stored, so that step is declined and
        # the whole commit ends in an error having written nothing.
        "module": _impl(
            "    st := prepareDeferred st\n"
            "    st := applyCredential st\n"
            "    if commit then\n"
            "      if st.deferredSaveReady then\n"
            "        st := persistRelated st\n"
            "      else\n"
            "        st := st\n"
            "      st := persistObject st\n"
            "    else\n"
            "      st := st\n"
            "    return"),
        "refinement": (
            "the related collection-valued data is written before the object it "
            "belongs to exists in storage. A faithful counterpart drives the "
            "deferred related-data write against an object with no primary key, "
            "which storage refuses: the call raises instead of persisting, so "
            "neither the object nor its related rows are written and the failing "
            "test — which saves a creation form with related data selected and "
            "then reads the created object's related objects back — FAILS. It "
            "does NOT resolve. This is the rival the earlier revision of this "
            "contract ADMITTED (measured then: exit 0), and it is the reason the "
            "two partial callees are now modelled at the fidelity their real "
            "counterparts have."),
        "rationale": (
            "REJECT from clauses (C7), (C3) and (C4): asked to attach related "
            "data to an object that is not yet stored, `persistRelated` declines "
            "and the step ends refused, after which nothing further is written — "
            "so the post-state has stepRefused true where C7 demands false, and "
            "both persistence components false where C3/C4 demand true. The "
            "ORDER is what is wrong here and nothing else: the same two calls in "
            "the other order are the frozen body, and the guard is kept "
            "faithful. Refuted at start (pw,obj,rel,df)=(T,F,F,T), commit=true — "
            "a point no other case uses, chosen with the object NOT yet stored "
            "(which is what makes the first call declinable) and the deferred "
            "capability already prepared (so the guard cannot be blamed). If it "
            "verified => SPEC-TOO-WEAK, and specifically the ordering hole."),
        "witness": _witness(_st(1, 0, 0, 1), True),
    },
    {
        "id": "weak-refused-step-noncommit",
        "kind": "uniqueness",
        "expect": "reject",
        # C7 ALONE. On the non-committing arm the body drives the related-data
        # save immediately, against an object it has deliberately not stored.
        # The step is declined, so no related row is written — the observable
        # write is absent, exactly as a raising call leaves it — but the call
        # ends in an error. Every other clause, including both mut-frames, still
        # holds at the witness point, so C7 is the only clause that can refute
        # it: this is the case that proves C7 is load-bearing on its own rather
        # than a spelling of C3/C4.
        "module": _impl(
            "    st := prepareDeferred st\n"
            "    st := applyCredential st\n"
            "    if commit then\n"
            "      st := persistObject st\n"
            "      if st.deferredSaveReady then\n"
            "        st := persistRelated st\n"
            "      else\n"
            "        st := st\n"
            "    else\n"
            "      let attempted := persistRelated st\n"
            "      st := { st with stepRefused := attempted.stepRefused }\n"
            "    return"),
        "refinement": (
            "on a non-committing call the body drives the deferred related-data "
            "write straight away, against an object that call is explicitly NOT "
            "storing. A faithful counterpart calls the related-data save on an "
            "instance with no primary key: storage refuses before writing "
            "anything, so no related rows appear (which is why the write is "
            "discarded here) and the error propagates out of a call whose whole "
            "contract is to build the object and hand it back unsaved. Callers "
            "of the non-committing flow get an exception instead of the object, "
            "so the suite's non-committing tests break. It does NOT resolve."),
        "rationale": (
            "REJECT from clause (C7) `st.stepRefused = false` and from NOTHING "
            "ELSE at this point: C1/C2 are satisfied, C3/C4 are vacuous on the "
            "commit=false arm, both mut-frames C5/C6 hold because the declined "
            "step wrote no component, and C8 holds. Refuted at start "
            "(pw,obj,rel,df)=(F,F,F,T), commit=FALSE — the object must be "
            "unstored for the attempted step to be declinable, and this exact "
            "point is used by no other case. Contrast weak-unconditional-related, "
            "which performs the same call but KEEPS its write and is therefore "
            "refuted by the C6 frame instead; the two cases separate 'wrote "
            "something it must not write' from 'ended in an error'. If it "
            "verified => SPEC-TOO-WEAK: C7 would be discharged by any body that "
            "asks storage for something it declines, and the ordering hole would "
            "still be open through this path."),
        "witness": _witness(_st(0, 0, 0, 1), False),
    },
    {
        "id": "weak-clear-validation-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # C8 ALONE. Does all the persistence work correctly and then reports the
        # form's bound data as never having validated. Without C8 a body could
        # satisfy C7 by declaring the data invalid (which is what makes the
        # partial callees decline) instead of by asking only for operations that
        # are accepted, so C8 is what stops C7 being launderable.
        "module": _impl(
            "    st := prepareDeferred st\n"
            "    st := applyCredential st\n"
            "    if commit then\n"
            "      st := persistObject st\n"
            "      if st.deferredSaveReady then\n"
            "        st := persistRelated st\n"
            "      else\n"
            "        st := st\n"
            "    else\n"
            "      st := st\n"
            "    st := { st with dataValidated := false }\n"
            "    return"),
        "refinement": (
            "the step persists everything correctly and then leaves the form "
            "reporting that its bound data did not validate. A faithful "
            "counterpart resets the form's validation outcome on the way out, so "
            "a caller that inspects the form after saving sees a form that is "
            "suddenly invalid, and any second operation on it — including "
            "re-running the save the deferred flow depends on — refuses. The "
            "form's own validation result is not this step's to change; a patch "
            "that clears it does NOT preserve the behaviour the suite relies "
            "on."),
        "rationale": (
            "REJECT from clause (C8) `st.dataValidated = stOld.dataValidated` "
            "and from nothing else: every other clause is satisfied (the "
            "persistence work is the frozen body's, and the step is never "
            "declined). Refuted at start (pw,obj,rel,df)=(F,T,T,F), commit=true "
            "— a point no other case uses, and one where both persistence "
            "components START true so that no C3/C4/C5/C6 obligation can be "
            "what fails. C8 is not decorative: it is what forbids the cheap "
            "route to C7, namely declaring the data invalid so that the callees "
            "decline for a reason of the body's own making. If it verified => "
            "SPEC-TOO-WEAK (the validation outcome would be writable)."),
        "witness": _witness(_st(0, 1, 1, 0), True),
    },

    # =====================================================================
    # THE ANNOUNCEMENT-MULTIPLICITY RIVALS (C9-C12). Every case below is a body
    # whose object/related persistence is CORRECT — it satisfies all eight of
    # C1-C8 at its witness point — and which gets the credential-change
    # announcement wrong: it announces twice, or not at all, or on the
    # non-committing arm, or leaves the change outstanding for someone else's
    # save to announce. Each is refuted only by the four counter clauses, so this
    # block is what makes them load-bearing rather than decorative.
    # =====================================================================
    {
        "id": "weak-resave-after-credential",
        "kind": "uniqueness",
        "expect": "reject",
        # The rival the audit panel landed against the previous revision of this
        # contract, verbatim. The commit arm stores the object, saves the related
        # data, then writes the credential AGAIN and stores AGAIN. Every one of
        # C1-C8 holds; on an entry state that already carries an outstanding
        # credential change — which is exactly the state the second of two
        # consecutive form saves is entered in — the announcement is made TWICE.
        "module": _impl(
            "    st := prepareDeferred st\n"
            "    if commit then\n"
            "      st := persistObject st\n"
            "      if st.deferredSaveReady then\n"
            "        st := persistRelated st\n"
            "      else\n"
            "        st := st\n"
            "      st := applyCredential st\n"
            "      st := persistObject st\n"
            "    else\n"
            "      st := applyCredential st\n"
            "    return"),
        "refinement": (
            "the faithful counterpart writes the credential again after the "
            "object and related data are stored and then stores the object a "
            "second time: `user.save(); self.save_m2m(); "
            "user.set_password(...); user.save()`. "
            "`django/contrib/auth/base_user.py:106-108` arms the outstanding-"
            "change latch on every credential write and "
            "`django/contrib/auth/base_user.py:74-78` announces once per store "
            "that finds it armed, so a call entered with a change already "
            "outstanding (the first, non-committing save left one: "
            "`tests/auth_tests/test_forms.py:123-124`) announces at the first "
            "store and again at the second. "
            "`tests/auth_tests/test_forms.py:125-126` asserts the count is 1 "
            "after the committing save; it is 2, so that test FAILS. MEASURED: "
            "this exact patch was run under the official harness three "
            "consecutive times — FAIL_TO_PASS 1/1 but PASS_TO_PASS 86/87 with "
            "test_success (auth_tests.test_forms.UserCreationFormTest) failing — "
            "while the bundle's own patch resolves 87/87 in the same window. It "
            "does NOT resolve."),
        "rationale": (
            "REJECT from clause (C9) `commit = true → st.credentialChanges = "
            "stOld.credentialChanges + 1`: the body's two object writes each "
            "follow a credential write, so the announcement count rises by two. "
            "Refuted at start (pw,obj,rel,df)=(F,F,F,F) with credentialPending "
            "TRUE and the counter at 0, commit=true — the outstanding-change "
            "entry is load-bearing and no other case uses it: at "
            "credentialPending = false this body announces exactly once and is "
            "indistinguishable from gold in this model, which is precisely why "
            "the previous revision of the contract admitted it. Measured with "
            "real builds: the rival does not verify (the C9 obligation leaves "
            "`stOld.credentialPending = false` unsolved), the witness elaborates "
            "against it (exit 0), and `decide` proves the claim FALSE against the "
            "frozen solution (exit 1). If it verified => SPEC-TOO-WEAK, and "
            "specifically the announcement-multiplicity hole."),
        "witness": _witness(_st(0, 0, 0, 0, cp=True, cc=0), True),
    },
    {
        "id": "weak-credential-after-object",
        "kind": "uniqueness",
        "expect": "reject",
        # BOUNDARY TOKEN SWAP on the credential axis: the same three calls the
        # frozen body makes, with the credential write moved to AFTER the object
        # write. Nothing is announced at all (the store finds no outstanding
        # change) and the step ends with one still outstanding.
        "module": _impl(
            "    st := prepareDeferred st\n"
            "    if commit then\n"
            "      st := persistObject st\n"
            "      if st.deferredSaveReady then\n"
            "        st := persistRelated st\n"
            "      else\n"
            "        st := st\n"
            "      st := applyCredential st\n"
            "    else\n"
            "      st := applyCredential st\n"
            "    return"),
        "refinement": (
            "the faithful counterpart is the patched `save` with its two first "
            "statements swapped: `user.save(); self.save_m2m(); "
            "user.set_password(self.cleaned_data['password1'])`. The stored row "
            "is then written from an instance whose credential has not been set "
            "yet, so the created account's stored credential is the empty one "
            "the form built (`django/contrib/auth/forms.py:139-141` is where the "
            "real order is fixed), and the change is never announced because "
            "`django/contrib/auth/base_user.py:74-78` only announces at a store "
            "and no store follows this write. "
            "`tests/auth_tests/test_forms.py:125-126` asserts the count is 1 "
            "after the committing save; it is 0, so that test FAILS. It does NOT "
            "resolve."),
        "rationale": (
            "REJECT from clauses (C9) and (C10): the only store happens before "
            "any credential write on this path, so the count does not move where "
            "C9 demands `stOld.credentialChanges + 1`, and the step ends with the "
            "change still outstanding where C10 demands none. C1-C8 all hold — "
            "the credential IS written, both persistence steps run, in an order "
            "storage accepts. Refuted at start (F,F,F,F) with credentialPending "
            "false and the counter at THREE, commit=true: the nonzero starting "
            "count is deliberate, since C9 is a RELATIVE claim and a battery that "
            "only ever started the counter at 0 could not tell `+ 1` from `= 1`. "
            "If it verified => SPEC-TOO-WEAK (the credential write could drift "
            "after the store that is supposed to announce it)."),
        "witness": _witness(_st(0, 0, 0, 0, cp=False, cc=3), True),
    },
    {
        "id": "weak-double-announce",
        "kind": "uniqueness",
        "expect": "reject",
        # OVER-APPROXIMATION: announce more than the one change. The frozen body
        # plus a second (credential write, store) pair, so the count rises by two
        # from ANY entry state — including a clean one, unlike
        # weak-resave-after-credential, which needs an outstanding change.
        "module": _impl(
            "    st := prepareDeferred st\n"
            "    st := applyCredential st\n"
            "    if commit then\n"
            "      st := persistObject st\n"
            "      if st.deferredSaveReady then\n"
            "        st := persistRelated st\n"
            "      else\n"
            "        st := st\n"
            "      st := applyCredential st\n"
            "      st := persistObject st\n"
            "    else\n"
            "      st := st\n"
            "    return"),
        "refinement": (
            "the faithful counterpart re-applies the credential and re-stores "
            "after the related-data save: `user.set_password(...); user.save(); "
            "self.save_m2m(); user.set_password(...); user.save()`. Each store "
            "follows a fresh credential write, so "
            "`django/contrib/auth/base_user.py:74-78` announces twice from a "
            "clean start. `tests/auth_tests/test_forms.py:125-126` asserts 1, so "
            "test_success FAILS; every subscriber to the credential-change "
            "notification also runs twice for one submitted form. It does NOT "
            "resolve."),
        "rationale": (
            "REJECT from clause (C9) alone: the count rises by two where C9 "
            "demands one. C10 holds (the last store clears the change), C1-C8 "
            "hold. Refuted at start (T,F,T,T) with credentialPending false and "
            "the counter at ONE, commit=true — a clean entry (no outstanding "
            "change) and a nonzero starting count, so this case shows the clause "
            "bites without the latched-entry hypothesis "
            "weak-resave-after-credential needs, and at a counter value no other "
            "case uses. If it verified => SPEC-TOO-WEAK."),
        "witness": _witness(_st(1, 0, 1, 1, cp=False, cc=1), True),
    },
    {
        "id": "weak-skip-object-when-already-persisted",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN GUARD: store the object only when it is not stored
        # already. On the F2P-shaped input (fresh object) this is the frozen body
        # exactly, so the guard is invisible there; on an entry whose object is
        # already stored the step announces nothing and leaves the change
        # outstanding while still satisfying C3 (the object IS stored) and C4.
        # MEASURED: under the eight-clause revision of this contract this body
        # VERIFIES (exit 0); it is one of the three shapes the repair newly
        # refutes.
        "module": _impl(
            "    st := prepareDeferred st\n"
            "    st := applyCredential st\n"
            "    if commit then\n"
            "      if st.objectPersisted then\n"
            "        st := st\n"
            "      else\n"
            "        st := persistObject st\n"
            "      if st.deferredSaveReady then\n"
            "        st := persistRelated st\n"
            "      else\n"
            "        st := st\n"
            "    else\n"
            "      st := st\n"
            "    return"),
        "refinement": (
            "the faithful counterpart guards the store on the object being new: "
            "`user.set_password(...); if user.pk is None: user.save(); "
            "self.save_m2m()`. For a caller that stored the object itself first "
            "(the documented `save(commit=False)` flow of "
            "`django/forms/models.py:526-548`: build it, store it manually, then "
            "ask the form to finish) the credential this step was asked to apply "
            "is never written to storage and its change is never announced, "
            "because `django/contrib/auth/base_user.py:74-78` announces only from "
            "inside a store. The step reports success while the new credential "
            "exists only in memory: the account keeps its old credential and "
            "every subscriber to the change notification is skipped. It does NOT "
            "resolve that flow, and the divergence is invisible to the "
            "FAIL_TO_PASS test alone, which is what makes it worth pinning."),
        "rationale": (
            "REJECT from clauses (C9) and (C10): on an entry whose object is "
            "already stored the guard skips the only announcing step, so the "
            "count does not move and the change stays outstanding. C3 still holds "
            "(`objectPersisted` is already true), C4 holds (the related-data save "
            "is asked for with the capability prepared and the object stored), and "
            "C1/C2/C5-C8 hold — so C9/C10 are the ONLY clauses that can refute "
            "it. Refuted at start (F,T,F,F) with credentialPending false and the "
            "counter at TWO, commit=true. MEASURED: this body verifies against "
            "the eight-clause revision and is refuted here, which is the direct "
            "evidence that the added clauses strengthened the contract rather "
            "than restated it. If it verified => SPEC-TOO-WEAK (a store could be "
            "skipped whenever the object happens to exist)."),
        "witness": _witness(_st(0, 1, 0, 0, cp=False, cc=2), True),
    },
    {
        "id": "weak-announce-on-noncommit",
        "kind": "uniqueness",
        "expect": "reject",
        # C11 ALONE, and the case that exploits the freedom the counter clauses
        # leave: they pin the count RELATIVE to the entry state, so a body could
        # try to make its announcement on the arm whose count is supposed to stand
        # still. The write is deliberately restricted to the counter — the store
        # itself is discarded — so both mut-frames C5/C6 and the outstanding-
        # change clause C12 still hold and nothing but C11 can refute it.
        "module": _impl(
            "    st := prepareDeferred st\n"
            "    st := applyCredential st\n"
            "    if commit then\n"
            "      st := persistObject st\n"
            "      if st.deferredSaveReady then\n"
            "        st := persistRelated st\n"
            "      else\n"
            "        st := st\n"
            "    else\n"
            "      let announced := persistObject st\n"
            "      st := { st with credentialChanges := announced.credentialChanges }\n"
            "    return"),
        "refinement": (
            "on the non-committing arm the faithful counterpart announces the "
            "credential change without leaving anything stored — it drives the "
            "object write and discards its storage effect (a store inside a "
            "transaction it then rolls back: the notification of "
            "`django/contrib/auth/base_user.py:74-78` is an in-process callback "
            "and is NOT rolled back), or notifies "
            "`password_validation.password_changed` directly. "
            "`tests/auth_tests/test_forms.py:123-124` asserts the count is ZERO "
            "after `form.save(commit=False)`, so test_success FAILS on its first "
            "assertion, and every subscriber to the notification runs for a "
            "credential change that was never stored. It does NOT resolve. (The "
            "closest real counterpart also loses the outstanding change, so it "
            "violates C12 as well; the rival is narrowed to the counter so that "
            "C11 is measured on its own.)"),
        "rationale": (
            "REJECT from clause (C11) `commit = false → st.credentialChanges = "
            "stOld.credentialChanges` and from NOTHING ELSE at this point: C1/C2 "
            "hold, C3/C4/C9/C10 are vacuous on the commit=false arm, both "
            "mut-frames C5/C6 hold because the store's effect is discarded, C12 "
            "holds because the change is left outstanding, and C7/C8 hold. "
            "Refuted at start (T,T,T,T) with credentialPending false and the "
            "counter at 0, commit=FALSE — the all-true flag point is used by no "
            "other case, and starting the counter at 0 is what makes the single "
            "announcement visible as 1 != 0. If it verified => SPEC-TOO-WEAK: the "
            "non-committing call could notify the world about a credential change "
            "it did not store."),
        "witness": _witness(_st(1, 1, 1, 1, cp=False, cc=0), False),
    },
    {
        "id": "weak-count-pinned-to-one",
        "kind": "uniqueness",
        "expect": "reject",
        # ORACLE ECHO on the counter, and the ABSOLUTE-vs-RELATIVE rival: rather
        # than let the announcement fall out of the callees, the body ECHOES the
        # value the postcondition is expected to show, writing the literal 1 into
        # the count after doing the frozen body's work. At an entry whose count is
        # 0 the echo is indistinguishable from what C9 demands, so this rival is
        # refutable ONLY at a nonzero starting count — which is exactly why C9 is
        # written relative to `stOld.credentialChanges` and why the battery varies
        # the entry count.
        "module": _impl(
            "    st := prepareDeferred st\n"
            "    st := applyCredential st\n"
            "    if commit then\n"
            "      st := persistObject st\n"
            "      if st.deferredSaveReady then\n"
            "        st := persistRelated st\n"
            "      else\n"
            "        st := st\n"
            "      st := { st with credentialChanges := 1 }\n"
            "    else\n"
            "      st := st\n"
            "    return"),
        "refinement": (
            "the faithful counterpart makes the announcement at most once per "
            "process rather than once per credential change — a store that "
            "suppresses the notification when one has already been sent (a "
            "'notify once' cache around "
            "`django/contrib/auth/password_validation.password_changed`). The "
            "second credential change of any run is then never announced: a "
            "caller that creates two accounts, or changes a credential after "
            "creating one, gets no notification for the second, so the "
            "validators' `password_changed` hooks (password history, reuse "
            "policies) silently stop running. `tests/auth_tests/test_forms.py:"
            "113-127` asserts the count RISES to 1 on the committing save of a "
            "freshly counted run, which this satisfies, and that is the point: "
            "the divergence is at the second change, so a contract that pinned "
            "the absolute value 1 instead of the relative + 1 would admit it. It "
            "does NOT preserve the notification behaviour the validator suite "
            "relies on."),
        "rationale": (
            "REJECT from clause (C9), read as the RELATIVE claim it is: the body "
            "lands the absolute literal 1, which equals `stOld.credentialChanges "
            "+ 1` only when the entry count is 0. Refuted at start (F,F,F,F) with "
            "credentialPending false and the counter at TWO, commit=true, where "
            "C9 demands 3 and the body lands 1. C10 holds (the store cleared the "
            "change) and C1-C8 hold, so C9 alone refutes it. This case is the "
            "control on the battery's own binder coverage: every other counter "
            "rival would also be refuted with the counter pinned at 0, and this "
            "one would NOT — so it is the evidence that varying the counter is "
            "meaningful rather than decorative. If it verified => SPEC-TOO-WEAK "
            "(the clause would only constrain the first announcement of a run)."),
        "witness": _witness(_st(0, 0, 0, 0, cp=False, cc=2), True),
    },
    {
        "id": "weak-leave-pending-on-commit",
        "kind": "uniqueness",
        "expect": "reject",
        # C10 ALONE. The frozen body, plus one more credential write AFTER the
        # store. The count is right for this call (the extra write is not followed
        # by a store), but the step hands back an object carrying an outstanding
        # credential change — which the NEXT store will announce, turning someone
        # else's save into a second announcement of this call's change.
        "module": _impl(
            "    st := prepareDeferred st\n"
            "    st := applyCredential st\n"
            "    if commit then\n"
            "      st := persistObject st\n"
            "      if st.deferredSaveReady then\n"
            "        st := persistRelated st\n"
            "      else\n"
            "        st := st\n"
            "      st := applyCredential st\n"
            "    else\n"
            "      st := st\n"
            "    return"),
        "refinement": (
            "the faithful counterpart writes the credential once more on the way "
            "out: `user.set_password(...); user.save(); self.save_m2m(); "
            "user.set_password(self.cleaned_data['password1'])`. "
            "`django/contrib/auth/base_user.py:106-108` re-arms the outstanding-"
            "change latch, and nothing clears it before the object is handed "
            "back, so the very next store of that object — the caller's own "
            "`user.save()`, or a second `form.save()` — announces this call's "
            "change a second time (`django/contrib/auth/base_user.py:74-78`). "
            "That is the same defect shape as the resave rival, displaced onto "
            "the caller: `tests/auth_tests/test_forms.py:125-126` counts 1 for "
            "the committing save itself, and the extra announcement lands on "
            "whatever stores the returned object next. It leaves the object in a "
            "state the patched code never leaves it in, and it does NOT preserve "
            "the once-per-change notification behaviour."),
        "rationale": (
            "REJECT from clause (C10) `commit = true → st.credentialPending = "
            "false` and from nothing else: C9 holds (the trailing credential "
            "write is followed by no store, so this call still announces exactly "
            "once), both persistence clauses hold, C1/C2/C7/C8 hold, and the "
            "commit=false clauses are vacuous. Refuted at start (F,F,T,F) with "
            "credentialPending TRUE and the counter at FOUR, commit=true — the "
            "largest counter value in the battery and the second use of a latched "
            "entry, at a flag point no other case uses. C10 is not implied by C9: "
            "at this point the count is exactly right, and what is wrong is the "
            "outstanding change the step leaves behind. If it verified => "
            "SPEC-TOO-WEAK (a committing save could arm an announcement for "
            "someone else to make)."),
        "witness": _witness(_st(0, 0, 1, 0, cp=True, cc=4), True),
    },
]


# ---------------------------------------------------------------------------
# NAGINI → VELVET ACCOUNTING.
#
# The nagini sibling contracts one function (`save_form`) over a
# permission-bearing heap Form whose discriminating fact is a body-less
# @ContractOnly capability predicate `relations_done(self)`, granted solely by a
# callee's Ensures. This bundle models the same commit step over the
# purely-functional carrier `FormState` (eight components: four persistence /
# preparation facts, the form's validation outcome, whether the step ended in a
# declined operation, whether a written credential's change is still outstanding,
# and HOW MANY TIMES that change has been announced) and pins TWELVE clauses
# under TWO requirements. Every nagini SPEC case is accounted for below.
#
#   nagini case                      -> here
#   ---------------------------------------------------------------------
#   pos-control-guard-dropped        -> pos-control-guard-dropped     PORTED (defeq)
#   admiss-commit-true               -> admiss-gold-total             RE-AIMED
#   weak-prepatch-no-deferred        -> weak-prepatch-no-related      PORTED
#   weak-dead-guard-skips-deferred   -> weak-dead-guard-skips-related PORTED
#   weak-fiat-fold                   -> (none)                        COLLAPSES->C4
#   weak-unfold-poke-fields          -> (none)                        SPLITS (see below)
#   weak-cross-instance-transfer     -> weak-scratch-state-transfer   PORTED (audit)
#   weak-self-echo-recursion         -> (none)                        INEXPRESSIBLE
#   weak-deferred-before-record      -> weak-related-before-object     PORTED (repair)
#   weak-unconditional-persist       -> weak-unconditional-object     PORTED (+related)
#   (no direct sibling)              -> weak-drop-object              ADDED (C3)
#   (no direct sibling)              -> weak-drop-credential          ADDED (C1)
#   (no direct sibling)              -> weak-drop-deferred-prep       ADDED (C2)
#   (no direct sibling)              -> weak-unconditional-related    ADDED (C6)
#   (no sibling; reshape control)    -> pos-control-setter-reorder    ADDED (defeq)
#   (no sibling; audit)              -> pos-control-record-literal    ADDED (non-defeq)
#   (no sibling; audit)              -> weak-guard-before-prepare     ADDED (C4)
#   (no sibling; audit)              -> weak-clear-on-noncommit       ADDED (C5/C6 down)
#   (no sibling; repair)             -> weak-refused-step-noncommit   ADDED (C7 alone)
#   (no sibling; repair)             -> weak-clear-validation-flag    ADDED (C8 alone)
#   (no sibling; panel)              -> weak-resave-after-credential  ADDED (C9)
#   (no sibling; panel)              -> weak-credential-after-object  ADDED (C9/C10)
#   (no sibling; panel)              -> weak-double-announce          ADDED (C9)
#   (no sibling; panel)              -> weak-skip-object-when-already-persisted
#                                                                     ADDED (C9/C10)
#   (no sibling; panel)              -> weak-announce-on-noncommit    ADDED (C11 alone)
#   (no sibling; panel)              -> weak-count-pinned-to-one      ADDED (C9 relative)
#   (no sibling; panel)              -> weak-leave-pending-on-commit  ADDED (C10 alone)
#   (no sibling; panel)              -> pos-control-double-store-single-announce
#                                                                     ADDED (C9 not over-fit)
#   AXIOM_TESTS (2)                  -> (none)                        DROPPED (G-AX)
#
# 25 velvet SPEC cases: 4 soundness, 1 admissibility, 20 uniqueness.
#
# THE ANNOUNCEMENT-MULTIPLICITY BLOCK (the eight cases marked `panel`) exists
#   because the audit panel landed a machine-confirmed `verify` does-not-imply
#   `resolve` break against the eight-clause revision of this contract: a rival
#   that stores the object, saves the related data, then writes the credential
#   again and stores again VERIFIED there, and its faithful patch regressed
#   PASS_TO_PASS test_success (auth_tests.test_forms.UserCreationFormTest) on
#   three consecutive official-harness runs while the bundle's own patch resolved
#   87/87. The missing observable was the credential-change ANNOUNCEMENT: real
#   `AbstractBaseUser.save` (django/contrib/auth/base_user.py:74-78) notifies
#   `password_changed` once per store that finds the `_password` latch armed by a
#   preceding `set_password` (django/contrib/auth/base_user.py:106-108), and
#   tests/auth_tests/test_forms.py:113-127 pins the resulting COUNT at 0 after
#   `save(commit=False)` and 1 after `save()`. The carrier now has both halves of
#   that mechanism (`credentialPending` for the armed latch, `credentialChanges`
#   for the notification count), the four clauses C9-C12 pin them, and the block
#   below attacks each of the four. Nothing was excluded to make this work: no
#   `require` was added or narrowed, no clause was deleted, and the four new
#   clauses only ADD obligations on the domain the two original requirements
#   already admitted.
#
# PORTED (pos-control-guard-dropped): the always-true-guard-dropped correct
#   reshape ports directly; the frozen proof closes the collapsed conditional.
# RE-AIMED (admiss-commit-true -> admiss-gold-total): the nagini case established
#   the read-only precondition on the F2P-shaped commit=true fresh-form input.
#   This method has no heap permission, so that half of the probe is vacuous;
#   re-aimed at (a) the F2P shape lying INSIDE the admitted domain — the two
#   requirements are exactly "the data validated" and "nothing has been declined
#   yet", both true at the point the step is entered — and (b) post-image joint
#   satisfiability there, witnessed by the frozen impl discharging all eight
#   ensures.
# PORTED (weak-prepatch-no-deferred / weak-dead-guard-skips-deferred): the
#   pre-change body (store object, never save related data) and the always-false
#   dead-guard variant carry across intact, each now backed by a machine-checked
#   witness at a distinct starting state.
# COLLAPSES->C4, with one correction (weak-fiat-fold, weak-unfold-poke-fields):
#   on nagini these fabricate the body-less capability `relations_done(self)` by
#   folding it or by poking the observable fields, rejected by the
#   permission/abstraction system. This carrier has no body-less capability and
#   no permission wall, so a fiat rival that sets `relatedPersisted` to false-y
#   effect is exactly "commit without setting relatedPersisted" —
#   weak-prepatch-no-related / weak-dead-guard-skips-related, already shipped.
#   AUDIT CORRECTION to the "collapses" claim: the FULL field-poke does not
#   collapse onto a reject case at all. A body that writes the components
#   directly, calling NONE of the four state transformers, VERIFIES (measured,
#   exit 0) — correctly so, because on this carrier the observable fields ARE
#   the specified state, so poking them to the right values is a genuinely
#   correct (if pointless) implementation, not a forgery. The permission wall
#   nagini needs exists because its capability is NOT a field; here it is. So
#   the class splits: a poke that lands the right values is a correct impl (no
#   reject case is possible or wanted — it is shipped as the positive control
#   pos-control-record-literal), and a poke that lands the wrong ones is already
#   covered by the C1-C8 rivals. The two components the repair added were probed
#   for the same laundering channel, with real builds rather than an argument:
#   a body that asks for a declined step and then pokes `stepRefused := false`
#   does NOT verify, because clearing the flag does not undo the writes the
#   declined step did not perform — the persistence components are still at their
#   pre-values, so C3/C4 fail (measured on two shapes: clearing after the branch,
#   and clearing mid-branch before the object write). A body that clears the flag
#   AND then does the work in an order storage accepts satisfies every clause, and
#   correctly so: its faithful counterpart catches the storage error, then stores
#   the object and its related data, which is a resolving implementation, not a
#   counterexample. Poking `dataValidated` to make the callees decline for a
#   reason of the body's own making is refuted by C8
#   (weak-clear-validation-flag). The genuinely non-collapsing member of the
#   family — do the real work against a state that is not the subject — is
#   recovered and shipped as weak-scratch-state-transfer.
# PORTED (weak-cross-instance-transfer -> weak-scratch-state-transfer): the port
#   originally recorded this as VACUOUS on the grounds that "no term denotes a
#   scratch instance" on this carrier. That is WRONG, and the audit landed the
#   rival: `FormState` is an ordinary value type and the impl region admits
#   `let scratch := ...`, so a throwaway second state IS denotable. The rival
#   does the persistence work on that scratch state and copies back only the
#   object component, which is exactly the nagini attack's shape (earn the fact
#   somewhere it does not count, then hope it discharges the clause for the
#   subject) and it is refutable here. Shipped below with a machine-checked
#   witness; the original "inexpressible" reason is retracted.
# INEXPRESSIBLE (weak-self-echo-recursion): the nagini rival re-derives the
#   contract from the function under specification via self-recursion, caught by
#   the MustTerminate obligation-leak check. The audit tried to land it here
#   rather than taking the port's word: a `do` block whose body calls
#   `commitForm` itself does not elaborate at all, failing at DEFINITION time
#   with "fail to show termination for commitForm ... no parameters suitable for
#   structural recursion" plus a follow-on `unfold` failure. That is not the
#   spec refusing a wrong impl, it is the fragment refusing to admit the term as
#   a definition, so there is no rival to attach a witness to — the case is
#   genuinely inexpressible here rather than merely hard. Confirmed by build,
#   not assumed.
# PORTED, after the spec hole it exposed was closed (weak-deferred-before-record
#   -> weak-related-before-object): the nagini ordering rival runs the deferred
#   related-data save BEFORE the object write, and nagini rejects it because
#   storage attaches related rows only to an object that already exists. An
#   earlier revision of this carrier ADMITTED it (measured then: exit 0, real
#   build), because the two callees were modelled as TOTAL setters and the
#   clauses pinned only each component's final value — so nothing in the contract
#   could see the order the writes happened in, while the repository can: the
#   faithful reordered patch raises instead of persisting and does NOT resolve.
#   That was a genuine `verify` does-not-imply `resolve` break in the contract,
#   and the port's original reason for dropping the case ("NOT wrong on this
#   backend's carrier", i.e. benignly collapsed by the abstraction) is retracted.
#   It is closed by raising the FIDELITY of the model rather than by naming the
#   rival: the two callees whose real counterparts are partial are now partial
#   here too (they decline, setting `stepRefused`, when asked in a state they do
#   not accept), and (C7) obliges the step to run to completion. The delta the
#   patch introduced is thereby observable, the rival is refutable, and it is
#   shipped above with a machine-checked witness at (T,F,F,T)/commit=true. Two
#   further cases guard the ways a body could try to satisfy C7 without doing the
#   work (weak-refused-step-noncommit for C7 alone, weak-clear-validation-flag
#   for C8 alone), and the laundering channel — clear the refusal flag after a
#   declined step — was probed with real builds and does not verify, because
#   clearing the flag does not perform the writes the declined step skipped.
# PORTED (weak-unconditional-persist -> weak-unconditional-object): storing the
#   object regardless of `commit` violates the object mut-frame (C5). The nagini
#   sibling had one unconditional-persist rival (record only, since
#   relations_done was capability-gated). This carrier splits the two mut-frame
#   clauses, so the related-data counterpart (C6) is added as
#   weak-unconditional-related.
# ADDED (weak-drop-object C3, weak-drop-credential C1, weak-drop-deferred-prep C2,
#   weak-unconditional-related C6, weak-refused-step-noncommit C7,
#   weak-clear-validation-flag C8, pos-control-setter-reorder): this bundle's
#   FormState carrier exposes each modelled fact as an independent clause,
#   several of which nagini folded into its @Pure accessors / capability
#   predicate. Each added rival attacks one clause left otherwise undefended by a
#   ported case, and the added positive is a second structurally-different
#   correct control. All are real divergences with machine-checked witnesses (or,
#   for the positive, a real verifying build), not fabricated wrongness.
# DROPPED (AXIOM_TESTS): the nagini file's axiom-soundness / containment probes
#   over the real Django callees are G-AX's job (axiom_check.py / mapping.md); the
#   G-PBT gate ignores AXIOM_TESTS regardless.
#
# CLAUSE / BINDER / POINT COVERAGE. All TWELVE independent top-level clauses are
#   attacked by some rival, and each clause's DIRECTIONS of failure are now
#   separated:
#     C1 (credential)            weak-drop-credential
#     C2 (deferred capability)   weak-drop-deferred-prep
#     C3 (object on commit)      weak-drop-object,
#                                weak-related-before-object (also C4/C7)
#     C4 (related on commit)     weak-prepatch-no-related (call absent),
#                                weak-dead-guard-skips-related (guard dead),
#                                weak-guard-before-prepare (guard hypothesis
#                                  false at the point it is read),
#                                weak-scratch-state-transfer (call executed, but
#                                  against a state that is not the subject),
#                                weak-related-before-object (call executed, but
#                                  before the object it attaches to exists)
#     C5 (object mut-frame)      weak-unconditional-object  (false -> true),
#                                weak-clear-on-noncommit    (true  -> false)
#     C6 (related mut-frame)     weak-unconditional-related (false -> true),
#                                weak-clear-on-noncommit    (true  -> false)
#     C7 (runs to completion)    weak-related-before-object (declined because the
#                                  object is not stored yet; C3/C4 fail too),
#                                weak-refused-step-noncommit (declined, and the
#                                  ONLY clause that fails at its point)
#     C8 (validation frame)      weak-clear-validation-flag (the only clause that
#                                  fails at its point)
#     C9 (one announcement on     weak-resave-after-credential (two announcements,
#         commit, RELATIVE to       and ONLY from a latched entry state),
#         the entry count)          weak-double-announce (two from a clean entry),
#                                 weak-credential-after-object (none: the write
#                                   lands after the only store; also C10),
#                                 weak-skip-object-when-already-persisted (none:
#                                   the announcing step is guarded away on a
#                                   sub-domain; also C10),
#                                 weak-count-pinned-to-one (lands the ABSOLUTE 1,
#                                   which is refutable only at a nonzero entry
#                                   count — the case that pins the relativity)
#     C10 (no outstanding change  weak-leave-pending-on-commit (the only clause
#          left after commit)       that fails at its point),
#                                 weak-credential-after-object,
#                                 weak-skip-object-when-already-persisted
#     C11 (counter mut-frame on   weak-announce-on-noncommit (the only clause that
#          non-commit)              fails at its point)
#     C12 (change left            (no rival needed beyond the positives: every
#          outstanding on           reject rival that reaches the non-commit arm
#          non-commit)              keeps it, and the clause is what forbids a
#                                   body from consuming the change without
#                                   storing — measured: the C11 rival's closest
#                                   real counterpart violates C12 as well)
#   and all twelve are defended by the four positive controls and the
#   admissibility case. FIVE of the reject cases are deliberately SINGLE-CLAUSE
#   refutations (weak-refused-step-noncommit C7, weak-clear-validation-flag C8,
#   weak-double-announce and weak-count-pinned-to-one C9, weak-announce-on-
#   noncommit C11, weak-leave-pending-on-commit C10), which is what makes those
#   clauses load-bearing rather than implied by their neighbours: at each of
#   those points every other clause is satisfied.
#   Of the positives only pos-control-record-literal is
#   NOT definitionally equal to the frozen body (measured with `rfl`), so it is
#   the one that actually tests for over-fitting on the eight original clauses;
#   the guard-dropped and setter-reorder controls are cheap defeq controls and are
#   labelled as such in their rationales. It is also the control that shows C7 is
#   not over-fit to a call ORDER: it makes no calls at all, and still discharges
#   C7 from the frame. pos-control-double-store-single-announce is the fourth
#   positive and the one that keeps C9 from being an over-constraint; unlike the
#   record-literal control it drives the real transformers, and it must verify
#   because its faithful counterpart is measured to resolve.
#   The input binders are the value parameter `commit` and the eight components of
#   `stOld`, of which two are pinned by the precondition (so a witness lies
#   inside the admitted domain) and six are free. Across the twenty reject
#   witnesses (twenty DISTINCT (starting state, commit) pairs):
#     commit                  varied over {true, false}         (14 true, 6 false)
#     stOld.passwordApplied   varied over {true, false}
#     stOld.objectPersisted   varied over {true, false}
#     stOld.relatedPersisted  varied over {true, false}
#     stOld.deferredSaveReady varied over {true, false}
#     stOld.credentialPending varied over {true, false}         (2 true, 18 false)
#     stOld.credentialChanges varied over {0, 1, 2, 3, 4}
#   so no free binder is pinned across the battery, and the variation is
#   MEANINGFUL rather than several spellings of one point: weak-guard-before-
#   prepare needs stOld.deferredSaveReady = false to bite at all,
#   weak-clear-on-noncommit needs both persistence components to start TRUE,
#   weak-related-before-object and weak-refused-step-noncommit both need
#   stOld.objectPersisted = FALSE (that is what makes the related-data step
#   declinable), weak-clear-validation-flag needs both persistence components
#   TRUE so that no persistence clause can be what fails,
#   weak-resave-after-credential needs stOld.credentialPending = TRUE (at a clean
#   entry it announces exactly once and is indistinguishable from gold — the
#   verifier says so: its refutation leaves `stOld.credentialPending = false`
#   unsolved), and weak-count-pinned-to-one needs stOld.credentialChanges != 0
#   (its refutation leaves `stOld.credentialChanges = 0` unsolved) — no other
#   case's point substitutes for any of them. Each witness binds nothing (literal
#   starting state + literal commit), so no consistency probe applies.
#
# WITNESS MECHANICS: the postcondition is decidable (nine Bool components and one
#   Nat counter, compared against literals and against `stOld`'s own values), so
#   each reject case reaches the method contract through `commitFormTester st
#   commit = false := by decide`, checked in a file whose `prove_correct` block is
#   stripped. Each witness must also lie inside the admitted domain, because the
#   derived tester is `if decide (pre) then ... else true`: `_st` pins the two
#   required components, so every reject verdict below is the postcondition's and
#   never the precondition's. All TWENTY checked with scripts/lean_verify.sh (via
#   the G-PBT gate, which runs both builds per case): each witness ELABORATES
#   against its rival (exit 0) and FAILS against the
#   frozen solution (exit 1). The gold-side failure was read, not just counted:
#   in every case it is `Tactic 'decide' proved that the proposition ... is
#   false` — a semantic refutation of the concrete claim, naming the very
#   starting state the witness discriminates at. None is a stuck reduction, an
#   unknown identifier, a type error or a timeout, so no case is exposed to the
#   `_STUCK_REDUCTION` / witness-scope defects the gate screens for. All four
#   positives and the admissibility case build under the frozen proof unchanged.
#   The rival-side refutations were also read rather than counted; for the four
#   counter clauses the unsolved goal names the discriminating hypothesis
#   directly:
#     weak-resave-after-credential   C9  ⊢ stOld.credentialPending = false
#     weak-credential-after-object   C10 ⊢ False, C9 ⊢ stOld.credentialPending = true
#     weak-double-announce           C9  ⊢ False
#     weak-skip-object-when-...      C10 ⊢ False, C9 ⊢ False
#     weak-announce-on-noncommit     C11 ⊢ False
#     weak-count-pinned-to-one       C9  ⊢ stOld.credentialChanges = 0
#     weak-leave-pending-on-commit   C10 ⊢ False
AXIOM_TESTS = []
