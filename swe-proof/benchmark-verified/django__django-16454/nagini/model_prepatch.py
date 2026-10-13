"""Twin-artifact model for django__django-16454.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A command-line parser kind that improves its error reporting carries a
  per-parser flag selecting between two error styles (a programmatic style and
  a human-facing command-line style). When such a parser opens a nested group
  of sub-commands, the parsers built for those sub-commands MUST be configured
  to report errors in the SAME style as the parser that opened the group -- so
  that an error inside a sub-command is presented the same way as an error at
  the top level, rather than degrading to the raw programmatic style.

  Concretely, opening a sub-command group yields a builder. The desired
  behaviour:

    (1) When the builder is asked to construct sub-command parsers of the SAME
        error-aware kind (the default), every constructed sub-command parser
        inherits the opening parser's error-style flag EXACTLY -- whatever that
        flag's value (the command-line style, the programmatic style, or the
        unset default). The flag is genuinely propagated, not reset to the
        constructor default.

    (2) When the builder is asked to construct sub-command parsers of a plain,
        non-error-aware kind, no such flag is injected: those parsers do not
        carry the error-style flag at all (injecting it would be meaningless
        for a parser that does not accept it). This path is unaffected.

The opening parser, the sub-command builder, and a constructed sub-command
parser are minimal classes carrying only the touched fields. The error-style
flag is modelled as ``Optional[bool]`` (its three observable settings:
command-line ``True``, programmatic ``False``, unset ``None``). Whether a
requested sub-command parser kind is the error-aware kind is an unchanged
runtime subclass test, axiomatized as a pure deterministic predicate.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class OpeningParser:
    """The error-aware parser that opens a sub-command group (the parent)."""

    def __init__(self) -> None:
        Requires(MustTerminate(2))
        Ensures(Acc(self.error_style) and self.error_style is None)  # type: ignore
        self.error_style = None  # type: Optional[bool]


class SubCommandBuilder:
    """The builder returned when a sub-command group is opened. It records the
    construction policy every later-built sub-command parser obeys: whether to
    inject the inherited error-style flag, and which value to inject."""

    def __init__(self) -> None:
        Requires(MustTerminate(2))
        Ensures(Acc(self.injects_flag) and self.injects_flag is False)  # type: ignore
        Ensures(Acc(self.inherited_style) and self.inherited_style is None)  # type: ignore
        self.injects_flag = False  # type: bool
        self.inherited_style = None  # type: Optional[bool]


class SubCommandParser:
    """A parser built for one sub-command. ``carries_flag`` records whether it
    is the error-aware kind that accepts the flag at all; ``error_style`` is the
    flag value it was constructed with (meaningful only when carries_flag)."""

    def __init__(self) -> None:
        Requires(MustTerminate(2))
        Ensures(Acc(self.carries_flag) and self.carries_flag is False)  # type: ignore
        Ensures(Acc(self.error_style) and self.error_style is None)  # type: ignore
        self.carries_flag = False  # type: bool
        self.error_style = None  # type: Optional[bool]


# axioms-start
@Pure
@ContractOnly
def is_error_aware_kind(parser_class_token: int) -> bool:
    """Unchanged runtime classification deciding whether a requested
    sub-command parser kind belongs to the error-aware family. A pure,
    deterministic predicate of the requested-kind token (same kind always
    yields the same answer); no further behaviour is assumed.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def open_subcommand_group(parent: OpeningParser, builder: SubCommandBuilder,
                          parser_class_token: int) -> None:
    """Open a sub-command group on ``parent`` and configure ``builder`` with the
    construction policy that later-built sub-command parsers obey. When the
    requested sub-command parser kind is error-aware, the policy carries the
    opening parser's error-style flag onward to those parsers."""
    # pre-conditions-start
    Requires(Acc(parent.error_style, 1 / 2))
    Requires(Acc(builder.injects_flag))
    Requires(Acc(builder.inherited_style))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(parent.error_style, 1 / 2))
    Ensures(Acc(builder.injects_flag))
    Ensures(Acc(builder.inherited_style))
    # The builder injects the inherited flag EXACTLY when the requested
    # sub-command parser kind is the error-aware kind (else the plain path is
    # left untouched).
    Ensures(builder.injects_flag == is_error_aware_kind(parser_class_token))
    # When it injects, the value injected is the opening parser's flag verbatim
    # -- the genuine propagation, not the constructor default.
    Ensures(Implies(builder.injects_flag,
                    builder.inherited_style is parent.error_style))
    # When it does NOT inject (the plain path), no binding is recorded at all:
    # the builder's recorded style is left untouched, verbatim.
    Ensures(Implies(not builder.injects_flag,
                    builder.inherited_style is Old(builder.inherited_style)))
    # post-conditions-end
    # impl-start
    # Pre-patch (buggy) skeleton: opening a sub-command group does NOT configure
    # any flag propagation -- the inherited generic behaviour builds sub-command
    # parsers with the constructor default, so the inherited error-style flag is
    # never injected, regardless of the requested kind.
    builder.injects_flag = False
    # impl-end


def build_subcommand_parser(builder: SubCommandBuilder, child: SubCommandParser) -> None:
    """Build one sub-command parser from ``builder`` according to its recorded
    construction policy: an error-aware sub-command parser is constructed
    carrying the injected error-style flag; a plain one carries no such flag."""
    # pre-conditions-start
    Requires(Acc(builder.injects_flag, 1 / 2))
    Requires(Acc(builder.inherited_style, 1 / 2))
    Requires(Acc(child.carries_flag))
    Requires(Acc(child.error_style))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(builder.injects_flag, 1 / 2))
    Ensures(Acc(builder.inherited_style, 1 / 2))
    Ensures(Acc(child.carries_flag))
    Ensures(Acc(child.error_style))
    # The sub-command parser carries the flag exactly when the builder injects.
    Ensures(child.carries_flag == builder.injects_flag)
    # When it carries the flag, its value is precisely what the builder injected
    # (which the opening function set to the inherited style).
    Ensures(Implies(child.carries_flag,
                    child.error_style is builder.inherited_style))
    # When it does NOT carry the flag (a plain sub-command parser), no flag
    # value is written at all: the field keeps its prior value verbatim.
    Ensures(Implies(not child.carries_flag,
                    child.error_style is Old(child.error_style)))
    # post-conditions-end
    # impl-start
    if builder.injects_flag:
        child.carries_flag = True
        child.error_style = builder.inherited_style
    else:
        child.carries_flag = False
    # impl-end
