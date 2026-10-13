"""Twin-artifact model for sympy__sympy-22914.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A code printer renders a function-application expression to a target-language
  call.  The expression carries a function identity and an ordered sequence of
  already-rendered argument strings.  The printer consults a table of supported
  functions:

    * the binary/n-ary selection of the smaller of its arguments is a supported
      function whose target rendering is the lower-case three-letter call name
      `m`,`i`,`n` (U+006D U+0069 U+006E);
    * the selection of the larger of its arguments is a supported function whose
      target rendering is the call name `m`,`a`,`x` (U+006D U+0061 U+0078);
    * the absolute-value function is likewise supported, with target `a`,`b`,`s`.

  For any supported function the result is the target call name, an opening
  parenthesis `(`, the already-rendered arguments joined by a comma and a single
  space, and a closing parenthesis `)`.  A function that is NOT in the supported
  table is emitted EXACTLY as the unchanged surrounding printing machinery
  would emit it — nothing but the supported-call emission may change.  That
  machinery is pre-existing infrastructure; its output for this node arrives as
  the read-only input `fallback` and is returned unaltered.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the comma-joined argument text is carried as one pre-rendered code
point sequence `joined_args` (the unchanged sub-computation shared by every
supported function), and the unsupported-path text as the pre-rendered
sequence `fallback` (the unchanged non-call machinery's output, carried
read-only).  The function identity is abstracted by an integer name code.
Supported-function membership and each target name are modelled deeply
(`is_supported` / `target_name`), validated == the real printer table by
axiom_check.py (G-AX), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def name_min() -> int:
    return 1


@Pure
def name_max() -> int:
    return 2


@Pure
def name_abs() -> int:
    return 0


@Pure
def name_unknown() -> int:
    return 3


@Pure
def is_supported(name_code: int) -> bool:
    """The function identity is in the printer's supported-function table.
    The selection functions (min, max) and absolute value are supported; an
    arbitrary other function identity is not."""
    return name_code == 0 or name_code == 1 or name_code == 2


@Pure
def target_name(name_code: int) -> PSeq[int]:
    """The target-language call name rendered for a supported function."""
    if name_code == 0:
        return PSeq(97, 98, 115)        # 'abs'
    if name_code == 1:
        return PSeq(109, 105, 110)      # 'min'
    return PSeq(109, 97, 120)           # 'max'


@Pure
def call_render(name_code: int, joined_args: PSeq[int]) -> PSeq[int]:
    """The call rendering for a supported function: target name, '(', the
    comma-joined argument text, ')'."""
    return target_name(name_code) + PSeq(40) + joined_args + PSeq(41)
# pure-end


def print_function_call(name_code: int, joined_args: List[int],
                        fallback: List[int]) -> List[int]:
    # pre-conditions-start
    # `name_code` ranges over the function identities the dispatch distinguishes.
    Requires(0 <= name_code and name_code <= 3)
    Requires(Acc(list_pred(joined_args), 1 / 2))
    # `fallback` is the unchanged surrounding machinery's output for this node,
    # supplied READ-ONLY (the modeled dispatch may consult it, never alter it).
    Requires(Acc(list_pred(fallback), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(joined_args), 1 / 2))
    Ensures(Acc(list_pred(fallback), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A supported function renders as the target call name followed by the
    # parenthesised, comma-joined arguments.  In particular the smaller-of and
    # larger-of selection functions are supported (their targets are min / max),
    # so neither falls through to the non-call fallback.
    Ensures(Implies(is_supported(name_code),
                    ToSeq(Result()) == call_render(name_code, ToSeq(joined_args))))
    # The minimum/maximum selection functions specifically: the rendering begins
    # with the three-letter target call name and is the call form, not a
    # fallback or rewritten conditional expression.
    Ensures(Implies(name_code == name_min(),
                    ToSeq(Result()) == PSeq(109, 105, 110) + PSeq(40)
                    + ToSeq(joined_args) + PSeq(41)))
    Ensures(Implies(name_code == name_max(),
                    ToSeq(Result()) == PSeq(109, 97, 120) + PSeq(40)
                    + ToSeq(joined_args) + PSeq(41)))
    # A function outside the supported table is emitted EXACTLY as the
    # unchanged surrounding machinery emits it — nothing but the supported-call
    # emission may change.  This pins the unsupported path completely (the
    # result IS the machinery's output), so no divergent fallback behaviour is
    # admitted.
    Ensures(Implies(not is_supported(name_code),
                    ToSeq(Result()) == ToSeq(fallback)))
    # post-conditions-end
    # impl-start
    # Pre-patch dispatch: only the absolute-value function is in the supported
    # table; the selection functions are NOT, so they take the fallback.
    if name_code == 0:
        nm = [97, 98, 115]  # type: List[int]
        result = nm + [40] + joined_args + [41]  # type: List[int]
        return result
    # A function outside the (pre-patch) supported table — which then included
    # neither the minimum nor the maximum selection — keeps the unchanged
    # machinery's rendering.
    empty = []  # type: List[int]
    out = empty + fallback  # type: List[int]
    return out
    # impl-end
