"""Twin-artifact model for django__django-13807.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the constraint-integrity checker assembles a textual database command
  that names one or more identifiers supplied by the schema, each identifier it
  splices into the command text must be the backend's *delimited* form of that
  identifier, never the bare identifier. The delimited form wraps an
  undelimited identifier in the backend's quoting characters so that an
  identifier which collides with a reserved word of the command language is
  still parsed as a name. Two command shapes are specified:
    * a command naming a single identifier — the assembled text is a constant
      command prefix, then the delimited identifier, then a constant suffix;
    * a command naming three identifiers — the assembled text interleaves three
      constant fragments with the delimited form of each of the three
      identifiers, in order.
  The constant fragments are opaque to this specification: only their constancy
  and the requirement that every spliced identifier be delimited are
  load-bearing. (The fragments' concrete repository spelling is recorded in the
  private refinement/mapping notes, not in this consumer-visible view.)

Identifiers and the assembled command text are modelled as `List[int]` of
Unicode code points (Nagini bans `str` indexing); the specification is carried
by `PSeq[int]`.

The backend's identifier-delimiting routine is an unchanged callee; it is
axiomatized (`delimit`) as the weakest contract the proof needs: an undelimited
identifier `x` becomes `" x "` (delimiter, identifier, delimiter), and an
already-delimited identifier is returned unchanged. Its soundness against the
real routine is checked out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def delimit(name: PSeq[int]) -> PSeq[int]:
    """Backend identifier-delimiting routine (the unchanged callee), as a pure
    function of the identifier's code points.

    Weakest contract the proof needs:
      * if `name` is already delimited (begins and ends with the delimiter code
        point 34, the double quote, i.e. is non-empty with both ends equal to
        the delimiter), it is returned unchanged;
      * otherwise it is wrapped: delimiter, then `name`, then delimiter.
    The delimited form therefore starts and ends with the delimiter, and an
    undelimited identifier gains two delimiters.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Implies(len(name) >= 1 and name[0] == 34 and name[len(name) - 1] == 34,
                    Result() == name))
    Ensures(Implies(not (len(name) >= 1 and name[0] == 34 and name[len(name) - 1] == 34),
                    Result() == PSeq(34) + name + PSeq(34)))
    Ensures(len(Result()) >= 1)
    Ensures(Result()[0] == 34 and Result()[len(Result()) - 1] == 34)


@ContractOnly
def delimit_id(name: List[int]) -> List[int]:
    """Runtime counterpart of `delimit`: the actual backend call that returns
    the delimited identifier as a fresh code-point list. Its observable content
    is `delimit` of the input (the A-consumed axiom, same callee)."""
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == delimit(ToSeq(name)))
# axioms-end


# pure-start
@Pure
def single_table_prefix() -> PSeq[int]:
    # Constant command prefix preceding the single named table (constant code
    # points; ends with an opening parenthesis, closed by close_paren()).
    return PSeq(80, 82, 65, 71, 77, 65, 32,
                102, 111, 114, 101, 105, 103, 110, 95, 107, 101, 121, 95,
                99, 104, 101, 99, 107, 40)


@Pure
def close_paren() -> PSeq[int]:
    # Closing parenthesis terminating the single-table command.
    return PSeq(41)


@Pure
def three_id_head() -> PSeq[int]:
    # Opaque constant leading fragment of the three-identifier command. Its
    # concrete spelling is irrelevant to the specification (only constancy and
    # the delimiting of the surrounding identifiers are load-bearing); modelled
    # here as an opaque placeholder sentinel.
    return PSeq(1, 2)


@Pure
def three_id_sep() -> PSeq[int]:
    # Opaque constant separator between the first two named identifiers.
    return PSeq(3)


@Pure
def three_id_mid() -> PSeq[int]:
    # Opaque constant fragment between the second and third named identifiers.
    return PSeq(4, 5)
# pure-end


def build_single_table_command(table_name: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(table_name), 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(table_name), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The assembled command text is the constant prefix, the DELIMITED identifier,
    # and the closing delimiter -- not the bare identifier.
    Ensures(ToSeq(Result())
            == single_table_prefix() + delimit(ToSeq(table_name)) + close_paren())
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy): the bare identifier is spliced into the command text
    # without delimiting it.
    result = []  # type: List[int]
    result = result + [80, 82, 65, 71, 77, 65, 32,
                       102, 111, 114, 101, 105, 103, 110, 95, 107, 101, 121, 95,
                       99, 104, 101, 99, 107, 40]
    n = len(table_name)
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(table_name), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n and n == len(table_name))
        Invariant(ToSeq(result) == single_table_prefix() + ToSeq(table_name).take(i))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        result = result + [table_name[i]]
        i = i + 1
    result = result + [41]
    return result
    # impl-end


def build_three_id_command(ident_a: List[int],
                           ident_b: List[int],
                           ident_c: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(ident_a), 1 / 2))
    Requires(Acc(list_pred(ident_b), 1 / 2))
    Requires(Acc(list_pred(ident_c), 1 / 2))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(ident_a), 1 / 2))
    Ensures(Acc(list_pred(ident_b), 1 / 2))
    Ensures(Acc(list_pred(ident_c), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Each of the three spliced identifiers is its DELIMITED form, in order,
    # interleaved with the constant fragments.
    Ensures(ToSeq(Result())
            == three_id_head()
            + delimit(ToSeq(ident_a))
            + three_id_sep()
            + delimit(ToSeq(ident_b))
            + three_id_mid()
            + delimit(ToSeq(ident_c)))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy): the bare identifiers are spliced without delimiting.
    result = []  # type: List[int]
    result = result + [1, 2]
    na = len(ident_a)
    i = 0
    while i < na:
        # invariants-start
        Invariant(Acc(list_pred(ident_a), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= na and na == len(ident_a))
        Invariant(ToSeq(result)
                  == three_id_head() + ToSeq(ident_a).take(i))
        Invariant(MustTerminate(na - i + 1))
        # invariants-end
        result = result + [ident_a[i]]
        i = i + 1
    result = result + [3]
    nb = len(ident_b)
    j = 0
    while j < nb:
        # invariants-start
        Invariant(Acc(list_pred(ident_a), 1 / 2))
        Invariant(Acc(list_pred(ident_b), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= nb and nb == len(ident_b))
        Invariant(ToSeq(result)
                  == three_id_head() + ToSeq(ident_a)
                  + three_id_sep() + ToSeq(ident_b).take(j))
        Invariant(MustTerminate(nb - j + 1))
        # invariants-end
        result = result + [ident_b[j]]
        j = j + 1
    result = result + [4, 5]
    nc = len(ident_c)
    k = 0
    while k < nc:
        # invariants-start
        Invariant(Acc(list_pred(ident_a), 1 / 2))
        Invariant(Acc(list_pred(ident_b), 1 / 2))
        Invariant(Acc(list_pred(ident_c), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= k and k <= nc and nc == len(ident_c))
        Invariant(ToSeq(result)
                  == three_id_head() + ToSeq(ident_a)
                  + three_id_sep() + ToSeq(ident_b)
                  + three_id_mid() + ToSeq(ident_c).take(k))
        Invariant(MustTerminate(nc - k + 1))
        # invariants-end
        result = result + [ident_c[k]]
        k = k + 1
    return result
    # impl-end
