"""Twin-artifact model for sympy__sympy-21379.

Behaviour under specification (an abstract behavioural contract, not an edit):

  An operation finishes by producing a single value built from a scalar (call it
  the factor) together with its two operands. The factor comes from a helper that
  is defined for most inputs but, for some inputs, has no defined answer and
  reports that by raising. The operation classifies its input by an integer code
  selecting exactly one of three cases the contract distinguishes.

  The behaviour pinned here, in terms of the value the operation returns:

    (1) The operation ALWAYS completes for every input it is given: it does not
        let the helper's raise escape to its own caller.

    (2) For the input the helper cannot answer (code 2), the value is built from
        the identity factor (1) and the two operands exactly as given: neither
        operand is transformed.

    (3) For an input the helper can answer (code 0 or 1), the value is built from
        the factor the helper returns and the two operands. If that factor is the
        identity (1), the operands enter the value unchanged; if it is something
        other than the identity, each operand is FIRST passed through the
        transform helper (parameterised by the factor) and the value is built
        from those transformed operands. (An implementation that builds the value
        from the untransformed operands when the factor is not the identity does
        NOT satisfy the contract.)

The two operands are rich objects abstracted by integer value carriers; the
input is abstracted by an integer code selecting the case. The factor the helper
returns, the transformed operand value, and the built result are all OPAQUE axiom
values (so every part of the postcondition is grounded in the modeled
computation rather than a literal an implementation could echo; SPEC_GUIDE §8).
The helper's "no defined answer" is reported by a user-defined exception (a
builtin exception in an ``Exsures`` crashes the Nagini translator; mapping.md §2).

The operation is a bounded, straight-line computation: it MUST terminate and
actually DELIVER its value to the caller (a total-correctness obligation,
carried as ``MustTerminate`` in the precondition). Nagini is a
partial-correctness verifier by default, so without this obligation an
implementation that diverges before returning (e.g. an unbounded loop inserted
ahead of the factor-producing call) would satisfy every value postcondition
vacuously yet would hang the operation — and the reported scenario — forever.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class FactorUnavailable(Exception):
    """Signals that the helper has no defined answer for the given input (code 2)
    and reports it by raising. A user-defined exception stands in because a
    builtin exception in an ``Exsures`` crashes the Nagini translator
    (mapping.md §2)."""


# axioms-start
@Pure
@ContractOnly
def common_factor(code: int) -> int:
    """The factor the helper yields, as a value (the cases it can answer, codes 0
    and 1). For code 1 it is the identity (1); for code 0 it is something other
    than the identity (!= 1). The exact non-identity value is OPAQUE (unpinned),
    so a caller can obtain it only by invoking the helper, never by fabricating a
    literal (SPEC_GUIDE §8). Weakest contract the proof needs; provenance +
    soundness check in mapping.md / axiom_check.py.
    """
    Requires(code == 0 or code == 1)
    Ensures(Implies(code == 1, Result() == 1))
    Ensures(Implies(code == 0, Result() != 1))


@ContractOnly
def common_factor_compute(code: int) -> int:
    """The helper as actually CALLED: it returns the factor for the cases it can
    answer (codes 0, 1) but, for the input it cannot answer (code 2), raises
    ``FactorUnavailable``. Its normal return equals ``common_factor(code)``.
    Non-pure (it may raise), so it is used only in the implementation, never
    inside an ``Ensures``.
    """
    Requires(0 <= code and code <= 2)
    # The real helper is a bounded computation: the single call always finishes
    # (normally or by raising). The strictly smaller measure (1 < 2) lets the
    # contracted caller holding MustTerminate(2) invoke it without leaking its
    # own termination obligation.
    Requires(MustTerminate(1))
    Ensures(code != 2)
    Ensures(Result() == common_factor(code))
    Exsures(FactorUnavailable, code == 2)


@Pure
@ContractOnly
def divide_out(value: int, factor: int) -> int:
    """The transform helper: maps one operand to a new value, parameterised by
    the factor. Pure; the exact result is OPAQUE — nothing constrains it to equal
    the input, so an implementation can produce ``divide_out(value, factor)``
    only by actually invoking the helper, never by leaving the operand untouched
    (SPEC_GUIDE §8). Applied only when ``factor != 1``.
    """
    Requires(factor != 1)


@Pure
@ContractOnly
def build_result(factor: int, p: int, q: int) -> int:
    """The result-construction step: the operation's returned value is built from
    the factor together with the two (possibly transformed) operands. OPAQUE —
    two applications are equal only when their three arguments are provably
    equal, so the value observably depends on whether each operand was
    transformed (SPEC_GUIDE §8).
    """
    Ensures(True)
# axioms-end


# pure-start
# (no derived pure spec helpers: the operand-shape branch is concrete integer
# control flow over the axiomatized callees above.)
# pure-end


def reduce_extract_common_factor(code: int, p: int, q: int) -> int:
    # pre-conditions-start
    # The input is classified into exactly one of three cases: a factor other
    # than the identity (0), the identity factor (1), or the case the helper
    # cannot answer (2).
    Requires(0 <= code and code <= 2)
    # Total correctness: the operation is a bounded, straight-line computation
    # over the helpers and MUST terminate and deliver its value (measure 2
    # leaves room for the factor-producing sub-call's own MustTerminate(1)
    # obligation). Nagini is a partial-correctness verifier by default, so
    # without this obligation an implementation that diverges before returning
    # (e.g. an unbounded loop ahead of the factor-producing call) satisfies
    # every value postcondition vacuously yet would hang the operation — and
    # the reported scenario — forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # (1) The operation ALWAYS completes — it never lets the helper's raise
    #     escape to its caller. There is NO Exsures, so the spec requires the
    #     method to raise no exception on any input.
    #
    # (2) For the input the helper cannot answer the value is built from the
    #     identity factor and the two operands exactly as given (neither operand
    #     is transformed).
    Ensures(Implies(code == 2, Result() == build_result(1, p, q)))
    # (3a) For an answerable input whose factor is NOT the identity, the factor is
    #      the helper's own (opaque) output and EACH operand is first passed
    #      through the transform helper before the value is built. Because
    #      divide_out is opaque, this is dischargeable only by an implementation
    #      that actually performs the transform — an implementation that builds
    #      the value from the untransformed operands cannot prove
    #      p == divide_out(p, ...) and so does NOT verify.
    Ensures(Implies(code != 2 and common_factor(code) != 1,
                    Result() == build_result(
                        common_factor(code),
                        divide_out(p, common_factor(code)),
                        divide_out(q, common_factor(code)))))
    # (3b) For an answerable input whose factor IS the identity, that factor is
    #      the helper's own (identity) output and the operands enter the value
    #      unchanged.
    Ensures(Implies(code != 2 and common_factor(code) == 1,
                    Result() == build_result(common_factor(code), p, q)))
    # post-conditions-end
    # impl-start
    # pr, qr are the operands as they enter the result: unchanged unless the
    # factor is not the identity, in which case each is passed through the
    # transform helper. The parameters p, q are read-only and keep their original
    # value, so the postcondition's witnesses divide_out(p, ...) / divide_out(q,
    # ...) refer to the operands as given (directive 5: read-only inputs are not
    # mutated).
    pr = p
    qr = q
    try:
        # The single factor-producing call. Its raising facet
        # (common_factor_compute) raises for the unanswerable input (code 2); for
        # an answerable input it returns the factor, whose value is the helper's
        # own pure-facet output common_factor(code). On normal completion this
        # establishes code in {0, 1}, so the value facet is well-defined and the
        # factor G is exactly common_factor(code).
        G = common_factor_compute(code)
        Assert(G == common_factor(code))
        Assert(code == 0 or code == 1)
        G = common_factor(code)
        if G != 1:
            # factor is not the identity: pass each operand through the transform
            # helper, then build the value from the transformed operands. Because
            # G is common_factor(code) and divide_out is opaque, the transformed
            # operands are exactly the postcondition's witnesses (clause 3a) — an
            # implementation that skips this step cannot discharge them.
            pr = divide_out(p, G)
            qr = divide_out(q, G)
        # On normal completion the operands were transformed exactly when
        # common_factor(code) != 1: the build arguments match clause (3a)/(3b).
        return build_result(G, pr, qr)
    except FactorUnavailable:
        # the unanswerable input: keep the identity factor; the operands enter
        # the value unchanged. The raise occurs only for code 2
        # (common_factor_compute's Exsures guard), so this handler runs only
        # there; pr, qr are still their original p, q (never reassigned).
        return build_result(1, pr, qr)
    # impl-end
