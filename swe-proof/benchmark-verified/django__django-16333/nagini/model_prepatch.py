"""Twin-artifact model for django__django-16333.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A user-creation routine persists a submitted form. Persisting a form happens
  in two parts: the primary record itself, and the form's deferred relational
  data (the many-to-many associations, whose persistence the underlying
  base-form save defers so it can be run after the primary record exists).

  When the routine is asked to persist immediately, BOTH parts must end up
  persisted once it returns:

    (1) the primary record is written, and

    (2) whenever a deferred relational save was set up for this form, that
        deferred save is run too, so the many-to-many associations are written.

  When the routine is NOT asked to persist immediately, nothing is written, but
  the deferred relational save is still set up so a later caller can run it.

  Those two guarantees hold whatever a caller did to the form before. Deferring
  is exactly what leaves a deferred relational save set up, so a caller that
  first asks for deferred persistence and afterwards asks for immediate
  persistence enters the routine on a form that ALREADY has one set up. That
  entry state is ordinary, and the routine owes the same thing on it: asked to
  persist immediately it must still write the primary record and must still
  leave the deferred relational data written for the form, exactly as when it is
  entered on a form nobody has persisted through yet. How the form arrived is
  not a reason for either part of the persistence to be missing.

  Both persistence steps act on the form's model RECORD OBJECT. That object is
  already available when the routine is entered -- the form holds it, having
  built it from the submitted data while validating -- so every step of the
  routine may act on it, and the object the routine hands back is that same
  one. The base-form save returns it; it is not what brings it into existence.

  Nothing the routine can say makes either part of the persistence true. The
  primary record counts as written only once the primary record write has
  actually been performed on the record object, and a deferred relational save
  counts as set up only once the base-form save has actually set one up.
  Whoever holds the form may READ those two facts but cannot set them: each
  changes only by performing the step that brings it about. The relational-data
  fact is grounded the same way, and more strongly still (below). So
  "persisted" here always means the persisting step ran -- never that the
  routine declared it so.

The form is modelled as a minimal object carrying only the persistence facts
the behaviour observes: whether the primary record has been written, whether a
deferred relational save was set up, and -- crucially -- whether the deferred
relational data has been written for THIS form. The first two are plain
booleans behind an abstraction predicate. The third is NOT a value an
implementation can compute or copy: it is an abstract per-form CAPABILITY
`relations_done(self)` -- an opaque predicate with no body. Because it has no
body, it cannot be folded into existence by fiat; because it names the specific
form `self`, a capability obtained for some OTHER form cannot stand in for it.
The ONLY producer of `relations_done(self)` is the deferred relational save's
contract: it grants the capability for the very form it ran on. So the
relational-data fact can become true for `self` ONLY by running the deferred
relational save on `self`. Three unchanged callees are axiomatized: the
base-form save (which sets up the deferred relational save and writes nothing),
the primary record write, and the deferred relational save itself. None of them
is the function under specification; each is the weakest contract the proof
needs. The deferred relational save additionally requires the primary record to
already exist, mirroring that the relational associations can be written only
once the record has a primary key -- and because the primary-record fact is
read-only to the routine, that condition is met only by having really performed
the record write, never by asserting it. The record object itself is tracked by
a second abstract per-form capability `record_available(self)`, which the form
already holds when the routine is entered: it identifies the one object every
persistence step acts on and that the routine hands back. Every step requires
it and every step preserves it, so it constrains no order -- the object is
there throughout -- it only records that all the steps and the returned value
concern that same object.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Form:
    """The form together with its model instance, folded into one object. The
    primary-record and deferred-save facts are held behind `form_pred` and are
    READ-ONLY to whoever holds it: the accessors below observe them, and no
    holder of the form has the write access needed to set either one. They move
    only when a step whose contract claims that effect is actually performed --
    the primary record write for the first, the base-form save for the second --
    so neither fact can be brought about by declaring it. The relational-data
    fact is grounded the same way and further still: it is not even a
    readable value but an abstract per-form capability
    `relations_done(self)`: a holder may carry it (in a postcondition) but can
    never bring it into existence by writing a field or folding a predicate, and
    a capability held for a DIFFERENT form does not discharge it for this one.
    Only the deferred relational save's contract grants `relations_done(self)`,
    so the relational-data fact for `self` can become true only by running the
    deferred relational save on `self`."""

    # pure-start
    @Predicate
    def form_pred(self) -> bool:
        # Abstraction over the observable persistence facts: the primary-record
        # and deferred-save booleans. Each is held at READ-ONLY permission, so a
        # holder of the form can observe both facts and set NEITHER: the only way
        # either becomes true is that the step which brings it about is actually
        # performed (the primary record write; the base-form save). This is what
        # makes "the primary record is written" mean the write happened rather
        # than that the routine said so -- and, because the deferred relational
        # save may run only once the record exists, it is also what stops that
        # ordering condition from being met by assertion instead of by the write.
        # The relational-data fact is NOT held here at all (it is the abstract
        # capability relations_done(self), produced solely by the deferred
        # relational save).
        return Acc(self.record_persisted, 1 / 2) and \
            Acc(self.deferred_save_ready, 1 / 2)

    @Pure
    def get_record(self) -> bool:
        Requires(Acc(self.form_pred(), 1 / 2))
        return Unfolding(Acc(self.form_pred(), 1 / 2), self.record_persisted)

    @Pure
    def get_ready(self) -> bool:
        Requires(Acc(self.form_pred(), 1 / 2))
        return Unfolding(Acc(self.form_pred(), 1 / 2), self.deferred_save_ready)
    # pure-end

    def __init__(self) -> None:
        Ensures(self.form_pred())                          # type: ignore
        Ensures(self.get_record() is False)                # type: ignore
        Ensures(self.get_ready() is False)                 # type: ignore
        self.record_persisted = False                      # type: bool
        self.deferred_save_ready = False                   # type: bool
        Fold(self.form_pred())


# axioms-start
@ContractOnly
@Predicate
def relations_done(self: Form) -> bool:
    # Abstract per-form capability: holding `relations_done(self)` means the
    # deferred relational data (the many-to-many associations) has been written
    # for THIS form. It is an opaque predicate with NO body. Consequences:
    # - an implementation cannot Fold it into existence (an abstract predicate
    #   has no body to fold), so the relational-data fact cannot be fabricated
    #   by fiat;
    # - it names the specific form `self`, so a capability obtained for some
    #   other (e.g. scratch) form is `relations_done(that_form)`, which does NOT
    #   discharge `relations_done(self)` -- it cannot be laundered across forms.
    # The SOLE producer is the deferred relational save's `Ensures` (it grants
    # the capability for the form it ran on). This is the directive-8 /
    # control-flow grounding of the relational-data fact: an unforgeable
    # capability token tied to the effect-producing step, not an answer-key
    # oracle on a result value and not a copyable field. Provenance + soundness
    # check: mapping.md / axiom_check.py.
    True


@ContractOnly
@Predicate
def record_available(self: Form) -> bool:
    # Abstract per-form capability naming this form's model RECORD OBJECT --
    # the object that the primary record write writes, that the deferred
    # relational save attaches the associations to, and that the routine hands
    # back. The form ALREADY HOLDS it on entry: it built that object from the
    # submitted data while validating, well before this routine runs, so there
    # is never a moment inside the routine at which the object is missing.
    # Accordingly every step requires it and every step preserves it, and the
    # routine both requires and returns it. It therefore forbids NO ordering of
    # the steps -- an implementation may act on the record object at any point --
    # it states only that one and the same object is what all of them, and the
    # returned value, are about. Like the relational-data capability it is an
    # opaque predicate with NO body and names the specific form `self`, so it
    # cannot be folded into existence and a capability held for some other form
    # does not stand in for it. Provenance: mapping.md / axiom_check.py.
    True


@ContractOnly
def base_form_save_deferred(self: Form) -> None:
    """The unchanged base-form save invoked in deferred mode: it hands back this
    form's model record object -- the object the form already holds, which it
    does not create -- and it sets up the deferred relational save for this
    form; it writes NOTHING (neither the primary record nor the relational
    data). It is the SOLE step whose contract claims the deferred relational
    save becomes set up, so `get_ready()` becomes true only by really running
    it. After it returns the deferred relational save is available to be run
    later. It does not grant the relational-data capability. Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(self.form_pred())
    Requires(record_available(self))
    Requires(MustTerminate(1))
    Ensures(self.form_pred())
    Ensures(record_available(self))
    Ensures(self.get_ready() is True)
    Ensures(self.get_record() == Old(self.get_record()))


@ContractOnly
def persist_record(self: Form) -> None:
    """The unchanged write of the primary record. It writes the form's record
    object (`record_available(self)`) and leaves that object in place. It is the
    SOLE step whose contract claims the primary record becomes written, so
    `get_record()` becomes true only by really performing this write. It writes
    the primary record only; it does NOT write the deferred relational data (it
    does not grant the relational-data capability) and does NOT alter the
    deferred-save availability. Provenance + soundness check: mapping.md /
    axiom_check.py.
    """
    Requires(self.form_pred())
    Requires(record_available(self))
    Requires(MustTerminate(1))
    Ensures(self.form_pred())
    Ensures(record_available(self))
    Ensures(self.get_record() is True)
    Ensures(self.get_ready() == Old(self.get_ready()))


@ContractOnly
def run_deferred_save(self: Form) -> None:
    """The unchanged deferred relational save. It writes the deferred relational
    data (the many-to-many associations) for this form -- it is the SOLE
    producer of the per-form relational-data capability `relations_done(self)`.
    It attaches the associations to the form's record object
    (`record_available(self)`) and leaves that object in place. It may be run
    only when a deferred relational save was really set up AND the primary
    record has really been written (the relational associations are attached to
    the record's primary key) -- and because both of those facts are read-only
    to the routine, this condition can be reached only by having performed
    those steps, not by claiming them. Provenance + soundness check: mapping.md /
    axiom_check.py.
    """
    Requires(self.form_pred())
    Requires(record_available(self))
    Requires(self.get_ready() is True)
    Requires(self.get_record() is True)
    Requires(MustTerminate(1))
    Ensures(self.form_pred())
    Ensures(record_available(self))
    Ensures(relations_done(self))
    Ensures(self.get_record() == Old(self.get_record()))
    Ensures(self.get_ready() == Old(self.get_ready()))
# axioms-end


# (the pure spec functions for this behaviour — the abstraction predicate
# form_pred and the accessors get_record/get_ready — live in the single `pure`
# region on the Form class above; the relational-data fact is the abstract
# capability relations_done declared in the axioms region.)


def save_form(self: Form, commit: bool) -> Form:
    # pre-conditions-start
    Requires(self.form_pred())
    # Entry state: the primary record has not been written yet -- this is the
    # routine that writes it, and it is what makes the record clauses below
    # claims about a write this routine performed.
    Requires(self.get_record() is False)
    # Whether a deferred relational save is ALREADY set up for the form on entry
    # is deliberately NOT constrained: both entry states are ordinary (deferring
    # is what leaves one set up, and the same form may afterwards be asked to
    # persist immediately), so every guarantee below is owed on both. In
    # particular the routine may not read the entry state as a licence to skip
    # either part of the persistence.
    # The form already holds its model record object when the routine is
    # entered -- it built that object from the submitted data while validating.
    # So the object every persistence step acts on, and that the routine hands
    # back, is available throughout; the routine is free to act on it whenever.
    Requires(record_available(self))
    # The routine performs a bounded amount of work and does NOT re-invoke
    # itself; this termination obligation pins that. It forbids discharging the
    # postcondition "for free" by echoing this routine's own contract: a self
    # call would have to take the very same obligation without a strictly
    # smaller measure and is rejected. So the relational-data guarantee can be
    # obtained only by actually running the deferred relational save on self,
    # never by re-deriving the contract from itself. The callees the routine
    # invokes carry a strictly smaller measure (1), so they are allowed.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(self.form_pred())
    Ensures(Result() is self)
    # The record object is handed back intact: every persistence step the
    # routine performs acts on the form's one record object, and that same
    # object is what the routine returns.
    Ensures(record_available(self))
    # A deferred relational save is always set up for the form.
    Ensures(self.get_ready() is True)
    # (1) Immediate persistence writes the primary record -- and this is a
    # claim about the write having happened, not a flag the routine may set: the
    # primary-record fact is read-only to the routine, so the only way to leave
    # it true is to have really performed the primary record write on the record
    # object. (It is also what the deferred relational save's own
    # already-written condition tests, so that condition too can be met only by
    # the real write.)
    Ensures(Implies(commit, self.get_record() is True))
    # (2) ... AND writes the deferred relational data (the discriminating
    # guarantee: committing must leave the relational associations persisted for
    # THIS form — dischargeable ONLY by running the deferred relational save on
    # self, since the relational-data fact is the abstract per-form capability
    # relations_done(self) and there is no other way to obtain it: it cannot be
    # folded by fiat and a capability for another form does not stand in for it).
    Ensures(Implies(commit, relations_done(self)))
    # Without immediate persistence nothing is written -- and, the fact being
    # read-only, an implementation that did perform the write cannot get back
    # under this clause by resetting the fact afterwards.
    Ensures(Implies(not commit, self.get_record() is False))
    # post-conditions-end
    # impl-start
    base_form_save_deferred(self)
    # (the password assignment of the routine has no tracked persistence effect)
    if commit:
        persist_record(self)
    return self
    # impl-end
