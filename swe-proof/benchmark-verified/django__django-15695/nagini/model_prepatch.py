"""Twin-artifact model for django__django-15695.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A schema-altering step is asked to give an existing database index a target
  name. The existing index already carries some current name, and the step
  reaches the underlying schema primitive that performs renames. The step must
  be IDEMPOTENT with respect to that name:

    (1) if the current name of the existing index already equals the target
        name, the step performs NO alteration at all -- it never engages the
        schema primitive (re-applying the step on an index that is already at
        the target name is a no-op, so it cannot fail by asking the backend to
        rename an index to a name that is already in use);

    (2) otherwise (the current name differs from the target name) the step
        engages the schema primitive EXACTLY ONCE, asking it for precisely the
        one rename that names the index by the target name.

  The step is handed the schema editor that carries the primitive and the
  existing index whose name is to change, and those are the ones that must be
  asked about: the alteration is made through the editor the caller supplied,
  never through some other one the step procures for itself and whose work the
  caller never sees, and it renames THAT index -- the engagement names the name
  that index currently carries as the one being moved, so a step cannot satisfy
  this by asking for the rename of some other index it made up.

  Engaging the schema primitive is an EFFECT on the database, not a value the
  step returns, and it is NOT recoverable from any answer the step reports about
  itself. Two steps can report identical answers while having asked the backend
  for a different number of renames, or for renames to different names, or for
  none at all. HOW MANY times the primitive is engaged, and WHICH target each
  engagement names, is therefore part of the behaviour specified here and not an
  implementation's free choice: a step that reaches the target name by way of
  some other name first, or that asks a second time, or that asks about some
  other index or through some other editor, or that reports the alteration
  without ever asking, is not this behaviour however it describes itself
  afterwards. In particular the no-alteration case of (1) is a COMPLETE
  no-op: nothing whatsoever is asked of the schema primitive, so the record of
  what it was last asked to rename to is left exactly as the step found it -- it
  is not enough to perform the alteration and then merely report that no rename
  happened.

  That obligation is carried the standard way effects are carried here. An
  engagement of the primitive is an operation (`rename_index_io`) parameterised
  by the schema editor it engages and by the pair of names it asks for -- the
  name the existing index currently carries and the target name. A step receives
  a token at a place together with the licence naming the engagements permitted
  there; an engagement spends licence and token and yields the token at the place
  the licence names; and the step must end holding a token at the place its
  behaviour requires. Every step is licensed for exactly ONE engagement, naming
  exactly the editor it was handed, the name its index currently carries, and the
  target name -- on every input it accepts, including the equal-name one. So the
  engagement cannot be skipped and its effect reported anyway (the token is
  obtainable only by making it), cannot ask for any other name (the licence names
  the target), and cannot happen twice (there is one licence and a step cannot
  mint one). In the equal-name case the step is not relieved of the capability,
  it is required to DECLINE it: it must end still holding the very token it
  arrived with, at the place it arrived at, together with that licence still
  UNSPENT -- which is exactly the observation that nothing was asked of the
  primitive, and is not something a step that engaged the primitive can produce.

  What the step must NOT claim is what the alteration achieves in the database:
  the schema primitive is capability-gated and may legitimately decline to emit
  anything for some index kinds on some backends. The behaviour specified here is
  the DECISION and the ASK -- whether, how often, and with which target the
  primitive is engaged -- never the backend's own success at carrying it out.

The existing index is modelled as a minimal class carrying only its touched
field -- its current name, abstracted to an integer identifier (names are only
ever compared for equality here, never indexed into). That field is READ-ONLY to
the step: the step decides whether to ask for a rename, it does not itself move
the index's name, so it holds only a share sufficient to read it and cannot
manufacture the primitive's outcome by writing it. A small editor object records
what the primitive was asked for, so the decision is observable as a value too.

Total correctness: deciding whether to rename is bounded, loop-free work that
must actually complete and hand control back to the migration executor. Nagini
checks partial correctness by default -- a diverging body would satisfy every
postcondition vacuously -- so every function carries a ``MustTerminate``
obligation (with strictly decreasing measures for callees) to reject
non-terminating implementations.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.io_contracts import *
from nagini_contracts.obligations import MustTerminate


class ExistingIndex:
    def __init__(self, name: int) -> None:
        # Terminates: field initialisation is straight-line work; measure 1
        # lets any caller holding MustTerminate(2) construct a value without
        # leaking its own obligation.
        Requires(MustTerminate(1))
        Ensures(Acc(self.name) and self.name == name)  # type: ignore
        self.name = name


class SchemaEditor:
    def __init__(self) -> None:
        # Terminates: field initialisation is straight-line work (measure 1).
        Requires(MustTerminate(1))
        Ensures(Acc(self.rename_issued) and self.rename_issued is False)  # type: ignore
        Ensures(Acc(self.renamed_to) and self.renamed_to == 0)  # type: ignore
        self.rename_issued = False  # type: bool
        self.renamed_to = 0  # type: int


# axioms-start
@IOOperation
def rename_index_io(t_pre: Place, editor: SchemaEditor, source: int, target: int,
                    t_post: Place = Result()) -> bool:
    """The observable EFFECT of the step: the schema primitive carried by
    `editor` is engaged ONCE and asked to rename the index currently called
    `source` to `target`, carrying the step from place `t_pre` to place `t_post`.
    It models the ASK itself -- that an engagement HAPPENED, WHICH schema editor
    was asked, and WHICH pair of names it named -- not what the backend then
    manages to do, which is capability-gated and none of this step's business.
    A step holds one instance of this operation per engagement it is permitted to
    make and an engagement spends one; a step cannot mint an instance, so how many
    engagements are made and which names each one asks about are settled by the
    step's contract instead of chosen by its implementation. An engagement
    terminates."""
    Terminates(True)


@ContractOnly
def issue_rename(t_pre: Place, editor: SchemaEditor, old_index: ExistingIndex,
                 new_name: int) -> None:
    """Engage the unchanged backend rename primitive, asking it to name the
    existing index `new_name`, and record on the editor that it was asked and
    what for. Models the unchanged primitive's INVOCATION: it claims nothing
    about what the backend achieves in the database (that is capability-gated),
    only that the ask happened with that target. Engaging is an effect, so this
    spends one licence to ask for exactly the rename of this index's current name
    to `new_name` plus the token that reaches it, leaving the token at the place
    that licence names: it is callable only where the caller's own contract
    licenses an engagement naming that editor and that pair of names.
    (mapping.md)"""
    IOExists1(Place)(
        lambda t_post: (
        # The index's current name is only READ here: the primitive, not this
        # model, is what moves a name in the database.
        Requires(Acc(old_index.name, 1 / 2)),
        Requires(Acc(editor.rename_issued) and Acc(editor.renamed_to)),
        # The backend rename primitive may only be engaged when the existing
        # index's current name actually differs from the target: asking the
        # backend to rename an index to a name that is already in use is
        # forbidden (it would fail). The caller therefore MUST establish this
        # before engaging -- so engaging in the equal-names case is a
        # verification error, not an effect that can be performed and then
        # papered over by resetting an observability flag.
        Requires(old_index.name != new_name),
        Requires(token(t_pre, 2) and
                 rename_index_io(t_pre, editor, old_index.name, new_name, t_post)),
        Requires(MustTerminate(2)),
        Ensures(token(t_post)),
        Ensures(Acc(old_index.name, 1 / 2)),
        Ensures(Acc(editor.rename_issued) and Acc(editor.renamed_to)),
        Ensures(editor.rename_issued is True),
        Ensures(editor.renamed_to == new_name),
        )
    )
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def rename_existing_index(t_pre: Place, editor: SchemaEditor,
                          old_index: ExistingIndex, new_name: int) -> None:
    IOExists1(Place)(
        lambda t_renamed: (
        # pre-conditions-start
        # TERMINATION: deciding whether to rename is a bounded, loop-free step
        # that MUST actually complete and hand control back to the migration
        # executor (total correctness). Under partial-correctness semantics a
        # diverging body (e.g. an endless loop before the rename decision)
        # satisfies every Ensures clause only vacuously yet never returns; the
        # real step always returns. This obligation rejects any such
        # implementation.
        Requires(MustTerminate(3)),
        # The index's current name is READ-ONLY to the step (a share, not full
        # permission): the step's job is to decide whether to ask for a rename,
        # not to move the name itself. So it can neither manufacture the
        # primitive's outcome by writing the name, nor step outside the
        # primitive's domain restriction by moving the name first and asking
        # afterwards.
        Requires(Acc(old_index.name, 1 / 2)),
        Requires(Acc(editor.rename_issued) and Acc(editor.renamed_to)),
        Requires(editor.rename_issued is False),
        # The step arrives holding a token and a licence for exactly ONE
        # engagement of the schema primitive: through the editor it was handed,
        # about the index it was handed (named by the name that index currently
        # carries), asking for exactly the target name. The licence is given on
        # EVERY input the step accepts -- the equal-name case is not privileged by
        # withholding the capability, it is required to decline to use one it
        # holds. That single licence is the whole effect budget: no second
        # engagement, none through another editor, and none naming any other pair
        # of names is available to any implementation, whatever it reports.
        Requires(token(t_pre, 3) and
                 rename_index_io(t_pre, editor, old_index.name, new_name,
                                 t_renamed)),
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(old_index.name, 1 / 2)),
        Ensures(Acc(editor.rename_issued) and Acc(editor.renamed_to)),
        # (2) The licensed engagement HAS BEEN MADE, exactly once: the step ends
        # holding a token at the place that single licence names, which is
        # reachable only by engaging the primitive through the editor it was
        # handed, about the index it was handed, asking for exactly the target
        # name -- and which cannot be reached twice, because no second licence
        # exists. So the alteration is never reported unasked, the ask that
        # happened named that pair of names and no other, and the index is never
        # routed to the target by way of some other name.
        Ensures(Implies(Old(old_index.name) != new_name, token(t_renamed))),
        # (1) The no-alteration case is a COMPLETE no-op: the step ends still
        # holding the very token it arrived with, at the very place it arrived at,
        # with its measure intact, AND the engagement licence STILL UNSPENT. It
        # held the capability to engage the primitive and declined to use it, so
        # nothing whatsoever was asked of the schema primitive -- not once, and
        # about no pair of names. This is the clause a report cannot satisfy: an
        # unspent licence is not something an implementation can still be holding
        # after having spent it, however it describes what it did.
        Ensures(Implies(Old(old_index.name) == new_name,
                        token(t_pre, 3) and
                        rename_index_io(t_pre, editor, Old(old_index.name),
                                        new_name, t_renamed))),
        # (1)+(2) restated as the value the editor records: the primitive was
        # asked for a rename iff the current name differed from the target.
        Ensures(editor.rename_issued == (Old(old_index.name) != new_name)),
        # When (and only when) the primitive was asked, it was asked for exactly
        # the target name.
        Ensures(Implies(editor.rename_issued, editor.renamed_to == new_name)),
        # (1) from the other side -- when nothing was asked, the record of what
        # the primitive was last asked to rename to is left exactly as the step
        # found it. An implementation that asks the primitive anyway and only
        # reports "no rename happened" afterwards has still touched the schema,
        # and does not satisfy this.
        Ensures(Implies(not editor.rename_issued,
                        editor.renamed_to == Old(editor.renamed_to))),
        # post-conditions-end
        )
    )
    # impl-start
    # Pre-patch skeleton: the rename is issued UNCONDITIONALLY.
    issue_rename(t_pre, editor, old_index, new_name)
    # impl-end
