"""Twin-artifact model for django__django-14534.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A per-choice subwidget container (one entry produced for each choice of a
  multi-choice form widget) exposes the identifier that a rendered <label>
  should point at. Every such container carries the rendering context that was
  computed for that one choice, which includes the attribute mapping that will
  be placed on the rendered control. When the form was configured to generate
  identifiers, that attribute mapping already holds the *fully-resolved*
  identifier for this choice (the configured prefix applied and the per-choice
  index appended); when the form was configured NOT to generate identifiers,
  the attribute mapping holds no identifier at all.

  The label-target identifier this container reports must be exactly the
  identifier recorded in that attribute mapping:

    * if the attribute mapping records an identifier, the reported value is
      that recorded identifier verbatim (so the configured prefix is honoured);
    * if the attribute mapping records no identifier, the reported value is the
      absent value (None) — no identifier is fabricated from the choice's name
      and position.

  The consequence that matters: the reported identifier never diverges from the
  identifier actually used when rendering the control. A fabricated value built
  only from the choice's name token and position is forbidden, because it
  ignores the configured prefix and invents an identifier where none exists.

Modelling choices (Nagini fragment):
  * Identifiers and name tokens are `int` tokens (opaque identity). The tested
    behaviour only observes WHICH identifier is reported and whether one is
    reported at all, so integer identity is the faithful carrier (mapping.md
    §2). The carrier `None` models the genuine absence of an identifier.
  * The rendering context of a single choice is a minimal class exposing only
    the touched fields: the attribute mapping `attrs` (`Dict[int, int]`, keyed
    by an opaque identifier-key token) plus the choice's `name` token and its
    position `index` (the two values a name/position fabrication would consume).
  * `'id'` (the attribute-mapping key under which the resolved identifier is
    recorded) is a single constant opaque `int` token, returned by `id_key()`.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import Optional, Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class ChoiceContext:
    def __init__(self, attrs: Dict[int, int], name: int, index: int) -> None:
        Requires(Acc(dict_pred(attrs), 1 / 2))
        Ensures(Acc(self.attrs) and self.attrs is attrs)        # type: ignore
        Ensures(Acc(self.name) and self.name == name)           # type: ignore
        Ensures(Acc(self.index) and self.index == index)        # type: ignore
        Ensures(Acc(dict_pred(attrs), 1 / 2))
        self.attrs = attrs
        self.name = name
        self.index = index


# axioms-start
# No consumed axioms. The reported identifier is the behaviour under
# specification and is modelled deeply (a direct lookup of the recorded
# identifier in the attribute mapping). Ordinary mapping membership/lookup is
# validated against real Python semantics out-of-band by axiom_check.py (G-AX)
# as an A-reference, not consumed here.
# axioms-end


# pure-start
@Pure
def id_key() -> int:
    """The opaque attribute-mapping key under which a resolved identifier is
    recorded (the literal string key 'id' in the repository; an int token
    here)."""
    return 1
# pure-end


def label_target_id(ctx: ChoiceContext) -> Optional[int]:
    # pre-conditions-start
    Requires(Acc(ctx.attrs, 1 / 2))
    Requires(Acc(dict_pred(ctx.attrs), 1 / 2))
    Requires(Acc(ctx.name, 1 / 2))
    Requires(Acc(ctx.index, 1 / 2))
    # The reported identifier must be produced in bounded time: a diverging
    # (never-returning) execution cannot discharge this obligation, so the
    # postconditions below are never satisfied vacuously.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(ctx.attrs, 1 / 2))
    Ensures(Acc(dict_pred(ctx.attrs), 1 / 2))
    Ensures(Acc(ctx.name, 1 / 2))
    Ensures(Acc(ctx.index, 1 / 2))
    # The attribute mapping is left exactly as it was found.
    Ensures(ctx.attrs is Old(ctx.attrs))
    # (1) When the attribute mapping records an identifier, the reported value
    #     is that recorded identifier verbatim.
    Ensures(Implies(id_key() in ctx.attrs, Result() is not None))
    Ensures(Implies(id_key() in ctx.attrs, Result() == ctx.attrs[id_key()]))
    # (2) When the attribute mapping records no identifier, no identifier is
    #     reported.
    Ensures(Implies(not (id_key() in ctx.attrs), Result() is None))
    # post-conditions-end
    # impl-start
    if id_key() in ctx.attrs:
        return ctx.attrs[id_key()]
    return None
    # impl-end
