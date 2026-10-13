"""Twin-artifact model for django__django-13449.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A windowed expression renders, on a backend that needs numeric values cast,
  as a fragment of the shape `<inner> OVER (<window>)`. When the windowed
  expression's declared output is the fixed-precision decimal type, the numeric
  cast that the backend requires must enclose the WHOLE windowed fragment, not
  the inner operand:

        CAST( <inner> OVER (<window>) AS NUMERIC)

  and the inner operand must be rendered WITHOUT its own decimal cast (its
  decimal-ness is absorbed by the outer cast, so the operand is rendered as a
  plain floating-point value). When the windowed expression's declared output
  is not the decimal type, NO outer cast is added and the inner operand renders
  by its OWN declared type: it carries its own numeric cast iff its own
  declared output is the decimal type (the two declared outputs can differ,
  e.g. a non-decimal windowed output over a decimal-typed operand), so the
  fragment is `<operand-rendered-by-its-own-type> OVER (<window>)`.

  The discriminating property: the OUTER cast wrapper, when present, surrounds
  the entire `... OVER (...)` clause -- never just the operand -- and it is
  present exactly when the windowed output is the decimal type. For a decimal
  windowed output, a wrapper enclosing the operand alone (leaving
  `CAST(<inner> AS NUMERIC) OVER ...`) is excluded.

SQL fragments are modelled as `List[int]` / `PSeq[int]` token sequences (Nagini
bans `str` indexing). The boolean `decimal_out` abstracts "the windowed
expression's declared output is the fixed-precision decimal type"; the boolean
`operand_decimal` abstracts the same property of the INNER operand's own
declared output. The inner operand's own rendering on this backend
(cast-or-not by its own declared type) is the unchanged callee, axiomatized as
`compile_operand`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# pure-start
@Pure
def kw_over() -> PSeq[int]:
    # the token sequence ' OVER (' (space O V E R space open-paren)
    return PSeq(32, 79, 86, 69, 82, 32, 40)


@Pure
def kw_over_close() -> PSeq[int]:
    # the closing ')'
    return PSeq(41)


@Pure
def cast_open() -> PSeq[int]:
    # 'CAST('
    return PSeq(67, 65, 83, 84, 40)


@Pure
def cast_close() -> PSeq[int]:
    # ' AS NUMERIC)'
    return PSeq(32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41)


@Pure
def cast_numeric(x: PSeq[int]) -> PSeq[int]:
    """Wrap a fragment in the numeric cast: CAST(<x> AS NUMERIC)."""
    return cast_open() + x + cast_close()


@Pure
def over_clause(inner: PSeq[int], window: PSeq[int]) -> PSeq[int]:
    """The windowed fragment without any cast: <inner> OVER (<window>)."""
    return inner + kw_over() + window + kw_over_close()
# pure-end


# axioms-start
@Pure
@ContractOnly
def compile_operand(operand: PSeq[int], operand_is_decimal: bool) -> PSeq[int]:
    """Rendering of the inner operand on the cast-requiring backend (the
    UNCHANGED callee that compiles a source expression). If the operand's own
    declared output is the decimal type it is wrapped in the numeric cast;
    otherwise it is rendered verbatim. The decimal-output branch of the
    windowed rendering consumes only the NON-decimal case (it forces the
    operand to a floating-point output first, so the operand comes back
    un-cast); the non-decimal-output branch consumes the case matching the
    operand's own declared type.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Implies(not operand_is_decimal, Result() == operand))
    Ensures(Implies(operand_is_decimal, Result() == cast_numeric(operand)))
# axioms-end


def render_windowed_with_numeric_cast(operand: List[int], window: List[int],
                                      decimal_out: bool,
                                      operand_decimal: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(operand), 1 / 2))
    Requires(Acc(list_pred(window), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(operand), 1 / 2))
    Ensures(Acc(list_pred(window), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # When the windowed output is the decimal type, the numeric cast encloses
    # the ENTIRE `<inner> OVER (<window>)` fragment, and the inner operand is
    # rendered WITHOUT its own cast (its output forced to floating point
    # first, regardless of the operand's own declared type).
    Ensures(Implies(
        decimal_out,
        ToSeq(Result()) == cast_numeric(
            over_clause(compile_operand(ToSeq(operand), False),
                        ToSeq(window)))))
    # When the windowed output is not the decimal type, there is no OUTER
    # cast; the operand renders by its OWN declared type (cast iff the
    # operand's own declared output is the decimal type).
    Ensures(Implies(
        not decimal_out,
        ToSeq(Result()) == over_clause(
            compile_operand(ToSeq(operand), operand_decimal),
            ToSeq(window))))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy) skeleton: the windowed expression has no special
    # rendering on this backend, so the inner operand ALWAYS carries its own
    # cast when its own output is the decimal type, and nothing ever wraps
    # the windowed fragment. For a decimal windowed output over a decimal
    # operand the result is `CAST(<inner> AS NUMERIC) OVER (<window>)` -- the
    # cast closes around the operand alone, the structurally-wrong placement.
    raw = list(operand)  # type: List[int]
    inner = raw  # type: List[int]
    if operand_decimal:
        inner = [67, 65, 83, 84, 40] + raw + \
            [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
        Assert(ToSeq(inner) == compile_operand(ToSeq(operand), True))
    else:
        Assert(ToSeq(inner) == compile_operand(ToSeq(operand), False))
    result = inner + [32, 79, 86, 69, 82, 32, 40] + window + [41]
    return result
    # impl-end
