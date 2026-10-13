"""Twin-artifact model for sympy__sympy-13852.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) A two-argument special function f(s, z) recognises a finite set of
      argument patterns and, for each recognised pattern, returns a closed-form
      value (an exact expression) instead of leaving the call unevaluated.
      Recognition is a PRIORITY CASCADE over the argument pair: some patterns are
      keyed on z alone and are checked first (so they win for any s); a further
      group is keyed on a particular s together with one of several distinguished
      z values; and two more patterns are keyed on s alone. A pattern matched
      earlier in the cascade takes priority over a later one when both could
      apply (e.g. a z-keyed pattern wins over an s-keyed pattern at the same
      argument). Any pair matching no pattern produces no closed form: the call
      stays unevaluated.

      Each recognised pattern must produce the closed-form value the function
      ACTUALLY takes there (validated against the real function by
      axiom_check.py / G-AX). Returning a different closed form for a recognised
      pattern, or leaving a recognised pattern unevaluated, does not meet the
      contract; neither does producing a closed form at an unrecognised pattern
      (the cascade must not over-fire).

  (2) The series-expansion of the same function at one distinguished value of s
      is an elementary closed form in (1 - z) carrying NO polar/branch factor on
      z. (The series-expansion at other s, an unchanged branch, is left to its
      existing behaviour and is not pinned here.)

Symbolic arguments and symbolic results are modelled as discrete tags / codes
(Nagini has no symbolic-algebra type): the matched argument pattern is an integer
tag, and the produced closed form is an integer code (the codes are opaque
distinct identifiers for the distinct closed forms — they carry no mathematical
meaning inside Nagini). A concrete per-pattern map (`closed_form_for`,
`expansion_code`) carries WHICH code each recognised pattern produces; that the
code-named closed form numerically EQUALS the real function at the pattern is the
out-of-band obligation checked by axiom_check.py (G-AX), not a consumed axiom.
The dispatch priority and the pattern -> code correspondence are what is verified
here.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# Closed-form result codes: opaque distinct identifiers, one per distinct closed
# form the cascade can produce. CF_UNEVAL marks "no closed form" (the call stays
# unevaluated). The remaining codes are pairwise distinct; their mathematical
# content is validated out-of-band (axiom_check.py / G-AX), not in Nagini.
CF_UNEVAL = 0       # no closed form: the call stays unevaluated
CF_ZA = 1           # closed form for the first z-keyed pattern    (z = z_a)
CF_ZB = 2           # closed form for the second z-keyed pattern   (z = z_b)
CF_ZC = 3           # closed form for the third z-keyed pattern    (z = z_c)
CF_P1 = 4           # closed form at the distinguished s, z = z_1
CF_P2 = 5           # closed form at the distinguished s, z = z_2
CF_P3 = 6           # closed form at the distinguished s, z = z_3
CF_P4 = 7           # closed form at the distinguished s, z = z_4
CF_P5 = 8           # closed form at the distinguished s, z = z_5
CF_P6 = 9           # closed form at the distinguished s, z = z_6
CF_SA = 10          # closed form for the first s-keyed pattern
CF_SB = 11          # closed form for the second s-keyed pattern

# Argument-pattern tags for the z component.
Z_A = 1             # z = z_a (first z-keyed value)
Z_B = 2             # z = z_b (second z-keyed value)
Z_C = 3             # z = z_c (third z-keyed value)
Z_1 = 4             # z = z_1 (first distinguished-s special argument)
Z_2 = 5             # z = z_2
Z_3 = 6             # z = z_3
Z_4 = 7             # z = z_4
Z_5 = 8             # z = z_5
Z_6 = 9             # z = z_6
Z_OTHER = 0         # any other z

# Distinguished s-predicate values the cascade branches on.
S_SPECIAL = 2       # the s value carrying the six special-z closed forms
S_KEY_A = 0         # the s value of the first s-keyed pattern
S_KEY_B = -1        # the s value of the second s-keyed pattern
S_EXPAND = 1        # the s value whose series-expansion is pinned in (2)

# Series-expansion codes for the distinguished-s expansion.
EXP_PLAIN = 1       # elementary closed form in (1 - z): NO polar/branch factor
EXP_POLAR = 2       # carries a polar/branch factor on z


# axioms-start
# (no consumed @ContractOnly axioms: the recognition cascade and the
# pattern -> closed-form correspondence are concrete control flow modelled
# directly. WHICH closed form is correct for each pattern is validated against
# the real function out-of-band by axiom_check.py / G-AX -- an A-reference, not
# a consumed axiom; see refinement.md.)
# axioms-end


# pure-start
@Pure
def closed_form_for(s: int, z_tag: int) -> int:
    """The closed-form code the function takes at argument pattern (s, z_tag),
    as a priority cascade. The z-keyed clauses are matched first (for any s),
    then the six distinguished-s special arguments, then the two s-keyed
    clauses; an unrecognised pattern yields no closed form (CF_UNEVAL).

    This map is concrete: it states only WHICH code each recognised pattern
    produces. That the produced closed form EQUALS the real function at the
    pattern is the G-AX obligation (axiom_check.py)."""
    Requires(0 <= z_tag and z_tag <= 9)
    # Priority 1: the z-keyed clauses, matched for any s.
    if z_tag == Z_A:
        return CF_ZA
    if z_tag == Z_B:
        return CF_ZB
    if z_tag == Z_C:
        return CF_ZC
    # Priority 2: the six special arguments at the distinguished s.
    if s == S_SPECIAL:
        if z_tag == Z_1:
            return CF_P1
        if z_tag == Z_2:
            return CF_P2
        if z_tag == Z_3:
            return CF_P3
        if z_tag == Z_4:
            return CF_P4
        if z_tag == Z_5:
            return CF_P5
        if z_tag == Z_6:
            return CF_P6
        return CF_UNEVAL
    # Priority 3: the two s-keyed closed forms.
    if s == S_KEY_A:
        return CF_SA
    if s == S_KEY_B:
        return CF_SB
    return CF_UNEVAL


@Pure
def expansion_code(s: int) -> int:
    """The series-expansion closed-form code at the distinguished s: the
    elementary closed form in (1 - z) with no polar/branch factor on z."""
    Requires(s == S_EXPAND)
    return EXP_PLAIN
# pure-end


def recognize_closed_form(s: int, z_tag: int) -> int:
    # pre-conditions-start
    Requires(0 <= z_tag and z_tag <= 9)
    # TERMINATION: the dispatch is a bounded, loop-free equality cascade — the
    # real function's value-dispatch always ANSWERS (returns a closed form or
    # falls through so the call stays unevaluated). Nagini is a
    # partial-correctness verifier by default; without this obligation a
    # non-terminating implementation (e.g. an infinite loop before an
    # unreachable return) satisfies every value Ensures vacuously. A diverging
    # dispatch would hang every construction of the function, so it does not
    # meet the contract.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The result is exactly the closed-form code the recognition cascade picks
    # for the argument pattern: the z-keyed clauses win first (for any s), then
    # the distinguished-s special arguments, then the two s-keyed clauses; an
    # unrecognised pattern stays unevaluated. Pinning the full cascade forces
    # both the recognised closed forms AND their priority relative to the
    # z-keyed clauses.
    Ensures(Result() == closed_form_for(s, z_tag))
    # Each recognised pattern must produce an ACTUAL closed form (not stay
    # unevaluated): the third z-keyed clause, the special-s arguments, and the
    # two s-keyed clauses.
    Ensures(Implies(z_tag == Z_C, Result() == CF_ZC))
    Ensures(Implies(s == S_SPECIAL and z_tag == Z_1, Result() == CF_P1))
    Ensures(Implies(s == S_SPECIAL and z_tag == Z_2, Result() == CF_P2))
    Ensures(Implies(s == S_KEY_A and z_tag == Z_OTHER, Result() == CF_SA))
    Ensures(Implies(s == S_KEY_B and z_tag == Z_OTHER, Result() == CF_SB))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (behaviour 1): only the z-keyed clauses are recognised; the
    # special-s arguments and the two s-keyed clauses stay unevaluated. This
    # fails the postcondition that those recognised patterns produce a closed
    # form.
    if z_tag == Z_A:
        return CF_ZA
    if z_tag == Z_B:
        return CF_ZB
    if z_tag == Z_C:
        return CF_ZC
    return CF_UNEVAL
    # impl-end


def series_expansion_at_one(s: int) -> int:
    # pre-conditions-start
    Requires(s == S_EXPAND)
    # TERMINATION: the distinguished-s expansion branch is a single return —
    # the real series-expansion always answers. Same partial-correctness hole
    # as recognize_closed_form: without the obligation a diverging impl passes
    # every Ensures vacuously.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The distinguished-s series-expansion is the elementary closed form in
    # (1 - z): NO polar/branch factor on z.
    Ensures(Result() == expansion_code(s))
    Ensures(Result() == EXP_PLAIN)
    Ensures(Result() != EXP_POLAR)
    # post-conditions-end
    # impl-start
    return EXP_PLAIN
    # impl-end
