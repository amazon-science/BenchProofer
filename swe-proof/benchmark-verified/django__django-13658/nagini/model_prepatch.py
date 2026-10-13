"""Twin-artifact model for django__django-13658.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A command-line utility records, at construction time, the program name it was
  invoked under. That program name is derived from the FIRST element of the
  argument vector the utility was handed: its trailing path component (basename),
  with one well-known exception -- when that trailing component is the module
  bootstrap name ``__main__.py`` the program name is the canonical module
  invocation ``python -m django`` instead.

  When the utility later builds the argument parser used to pre-scan the
  options that select settings, that parser's reported program name MUST be the
  program name the utility already computed from its OWN argument vector. It
  must NOT be re-derived from the ambient/process-wide argument vector, which
  may name a different program (or be unusable) in an embedded caller that hands
  the utility an explicit argument vector. In other words: the parser's program
  name is a function of the utility's own first argument alone, and is invariant
  under whatever the process-wide argument vector happens to hold.

Strings are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); the specification is phrased over ``PSeq[int]`` via ``ToSeq``.
The utility carries two independent program-name sources: the basename of its
OWN first argument and the basename of the ambient/process-wide first argument.
The desired program name is modelled deeply by the pure function
``program_name`` (the trailing-component-with-bootstrap-exception rule), grounded
in the utility's own first argument; no callee is axiomatized -- the source
selection that the change is about is spelled out, not hidden behind an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The program-name rule -- a first-argument basename, with
# the bootstrap basename mapping to the module-invocation name -- is modelled
# deeply by the pure function `program_name` over the utility's own
# first-argument code points; it is validated against its real library
# semantics out-of-band by axiom_check.py (G-AX) as an A-reference, not
# consumed here.
# axioms-end


# pure-start
@Pure
def bootstrap_name() -> PSeq[int]:
    # The module-bootstrap basename '__main__.py'.
    return PSeq(95, 95, 109, 97, 105, 110, 95, 95, 46, 112, 121)


@Pure
def module_invocation() -> PSeq[int]:
    # The canonical module invocation name 'python -m django'.
    return PSeq(112, 121, 116, 104, 111, 110, 32, 45, 109, 32,
                100, 106, 97, 110, 103, 111)


@Pure
def program_name(basename: PSeq[int]) -> PSeq[int]:
    """The program name derived from a first-argument basename: the basename
    itself, except the bootstrap basename maps to the module-invocation name."""
    if basename == bootstrap_name():
        return module_invocation()
    return basename
# pure-end


class Parser:
    def __init__(self) -> None:
        Ensures(Acc(self.prog) and Acc(list_pred(self.prog)))  # type: ignore
        Ensures(len(self.prog) == 0)  # type: ignore
        self.prog = []  # type: List[int]


class Utility:
    def __init__(self) -> None:
        Ensures(Acc(self.argv0_basename) and Acc(list_pred(self.argv0_basename)))  # type: ignore
        Ensures(Acc(self.sys_argv0_basename) and Acc(list_pred(self.sys_argv0_basename)))  # type: ignore
        self.argv0_basename = []  # type: List[int]
        self.sys_argv0_basename = []  # type: List[int]


def build_settings_parser(self: Utility) -> Parser:
    # pre-conditions-start
    # Both program-name sources are read-only inputs (fractional permission):
    # the basename of the utility's OWN first argument, and the basename of the
    # ambient/process-wide first argument. They are allowed to disagree.
    Requires(Acc(self.argv0_basename, 1 / 2) and Acc(list_pred(self.argv0_basename), 1 / 2))
    Requires(Acc(self.sys_argv0_basename, 1 / 2) and Acc(list_pred(self.sys_argv0_basename), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    # The two sources are returned untouched at the same fractional permission.
    Ensures(Acc(self.argv0_basename, 1 / 2) and Acc(list_pred(self.argv0_basename), 1 / 2))
    Ensures(Acc(self.sys_argv0_basename, 1 / 2) and Acc(list_pred(self.sys_argv0_basename), 1 / 2))
    Ensures(ToSeq(self.argv0_basename) == Old(ToSeq(self.argv0_basename)))
    Ensures(ToSeq(self.sys_argv0_basename) == Old(ToSeq(self.sys_argv0_basename)))

    # The parser is a fresh, fully-owned object.
    Ensures(Acc(Result().prog) and Acc(list_pred(Result().prog)))
    Ensures(Result() is not self)

    # The parser's program name is the program name derived from the utility's
    # OWN first argument -- the basename, with the bootstrap-name exception.
    # This is grounded in `self.argv0_basename`, never the ambient source, so a
    # builder that derived `prog` from `self.sys_argv0_basename` is rejected
    # whenever the two sources disagree.
    Ensures(ToSeq(Result().prog) == program_name(ToSeq(self.argv0_basename)))
    # post-conditions-end
    # impl-start
    parser = Parser()

    # PRE-PATCH: the parser is built with no explicit program name, so its
    # program name defaults to the basename of the AMBIENT/process-wide first
    # argument (`self.sys_argv0_basename`) rather than the utility's own.
    i = 0
    while i < len(self.sys_argv0_basename):
        # invariants-start
        Invariant(Acc(self.sys_argv0_basename, 1 / 2) and Acc(list_pred(self.sys_argv0_basename), 1 / 2))
        Invariant(ToSeq(self.sys_argv0_basename) == Old(ToSeq(self.sys_argv0_basename)))
        Invariant(Acc(parser.prog) and Acc(list_pred(parser.prog)))
        Invariant(parser is not self)
        Invariant(0 <= i and i <= len(self.sys_argv0_basename))
        Invariant(len(parser.prog) == i)
        Invariant(ToSeq(parser.prog) == ToSeq(self.sys_argv0_basename).take(i))
        # invariants-end
        parser.prog.append(self.sys_argv0_basename[i])
        i = i + 1
    Assert(ToSeq(self.sys_argv0_basename).take(len(self.sys_argv0_basename)) == ToSeq(self.sys_argv0_basename))
    Assert(ToSeq(parser.prog) == ToSeq(self.sys_argv0_basename))
    return parser
    # impl-end
