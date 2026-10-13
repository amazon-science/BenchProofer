#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-16597.

There is NO consumed @ContractOnly axiom in model.py. The behaviour under
specification is the set-containment THEORY of the numeric-property knowledge
base (model.py `consistent_theory` + its thirty-one seed deducers). That
theory is modelled DEEPLY; this check validates the
deep model against the REAL fact-deduction engine (sympy's assumptions system,
the very code the gold patch edits) as an A-reference:

  (1) FAITHFULNESS at the witnessed queries (the F2P behaviours), asserted
      directly on the real engine and enumerated so no case can be silently
      skipped. The model instantiates the closure at THIRTY-ONE independent
      seeds, and every one of those seeds' full record is asserted here
      against the real engine, field by field:
        * five BOUNDED seeds (`even`, `odd`, `integer`, `rational`,
          `irrational`) each resolving `is_finite` to True — the per-seed
          obligation, so a rule set that bounds one favoured seed only is
          caught here as well as by Nagini;
        * one UNBOUNDED seed (S.Infinity / S.NegativeInfinity) resolving
          is_finite / is_rational / is_integer / is_even / is_odd /
          is_algebraic / is_transcendental / is_irrational / is_composite to
          False and is_noninteger to True;
        * four UNKNOWN-FRONTIER seeds (`rational=False`, `irrational=False`,
          `even=False`, `odd=False`) leaving `is_finite` None — the
          too-strong direction, so a rule set propagating non-membership
          backwards to boundedness is caught too;
        * the DEFINING-CONDITION seeds, which hand the engine exactly the
          statuses one equivalence needs on its right-hand side and require
          the membership it defines to come back resolved rather than
          Unknown: `real & !rational & bounded`, `real & transcendental`,
          `integer & !odd`, `algebraic & bounded`, `!nonnegative`,
          `real & !nonnegative`, `real & !positive`, `real & !negative`,
          `nonnegative & nonpositive` (the origin), `prime`,
          `!composite & positive & even`, and `nonzero`;
        * the ONE-SIDED seeds (`integer & nonnegative`,
          `integer & nonpositive`), whose sign statuses are asserted
          alongside their memberships.
      Every one of those records also asserts the NON-ZERO status ("definitely
      away from the origin"), which model.py pins in all thirty-one
      postconditions: see SEED_NONZERO below. Eight of the records there resolve
      it True (a strict sign, odd parity, or irrationality), the unbounded seed
      checked separately is a ninth (unboundedness on the real line), one record
      (the origin) resolves it False, and the remaining fourteen leave it
      Unknown, so a rule set reading it off the wrong relation is caught here as
      well as by Nagini.
      Deliberately NOT asserted: `is_finite` for the BARE seeds
      `algebraic=True` and `transcendental=True`. Both were measured to
      differ across independently-harness-verified correct alternatives, so
      pinning them would reject a correct implementation. The seed
      `algebraic=True, finite=True` IS asserted: handing boundedness over as
      an assumption makes the rest of that record invariant across those same
      alternatives, so it pins the containment `algebraic -> complex` without
      pinning one implementation's choice about boundedness.

  (2) THEORY soundness (the deep model == the real rule graph): for a large
      family of seed assumptions, build the real Symbol, read the relevant
      `is_*` properties into a trit record, and assert that record satisfies
      the SAME closure predicate `consistent_theory` encodes. The predicate is
      evaluated at the property/index level on BOTH sides (no value-membership
      proxy, no double mask): every implication clause of the model's theory is
      checked to hold in the real engine's deduced facts.

Imports the real `sympy` package (available in-container, the patched library);
exit 0 iff every obligation holds.
"""
import sys
import itertools


# --- the relevant property names (must match model.py KB fields) -------------
PROPS = [
    "integer", "rational", "real", "finite", "even", "odd",
    "algebraic", "transcendental", "irrational", "infinite",
    "complex", "noninteger", "prime", "composite",
    "imaginary", "positive", "negative", "nonpositive", "nonnegative",
    "hermitian", "antihermitian", "nonzero",
]


def trit(v):
    """sympy returns True / False / None for is_*; pass through unchanged."""
    assert v is True or v is False or v is None, "unexpected fact value %r" % (v,)
    return v


def read_kb(obj):
    """Read the relevant is_* properties of a real sympy object into a dict
    keyed by property name (the trit record the model's KB mirrors)."""
    return {p: trit(getattr(obj, "is_%s" % p)) for p in PROPS}


def theory_clauses(k):
    """Every implication clause of model.py `consistent_theory`, as
    (antecedent_bool, consequent_property, required_value) at the property
    level. Returns a list of (description, holds_bool)."""
    def F(p):  # the trit of property p in record k
        return k[p]

    clauses = [
        # integer -> rational ; !rational -> !integer
        ("integer=T -> rational=T", not (F("integer") is True) or F("rational") is True),
        ("rational=F -> integer=F", not (F("rational") is False) or F("integer") is False),
        # rational -> real ; rational -> algebraic ; rational -> finite
        ("rational=T -> real=T", not (F("rational") is True) or F("real") is True),
        ("rational=T -> algebraic=T", not (F("rational") is True) or F("algebraic") is True),
        ("rational=T -> finite=T", not (F("rational") is True) or F("finite") is True),
        # real -> complex
        ("real=T -> complex=T", not (F("real") is True) or F("complex") is True),
        # algebraic -> complex ; algebraic -> finite
        ("algebraic=T -> complex=T", not (F("algebraic") is True) or F("complex") is True),
        ("algebraic=T -> finite=T", not (F("algebraic") is True) or F("finite") is True),
        # even -> integer ; odd -> integer ; !integer -> !even ; !integer -> !odd
        ("even=T -> integer=T", not (F("even") is True) or F("integer") is True),
        ("odd=T -> integer=T", not (F("odd") is True) or F("integer") is True),
        ("integer=F -> even=F", not (F("integer") is False) or F("even") is False),
        ("integer=F -> odd=F", not (F("integer") is False) or F("odd") is False),
        # even == integer & !odd : even -> !odd
        ("even=T -> odd=F", not (F("even") is True) or F("odd") is False),
        # prime -> integer ; composite -> integer ; !integer -> !prime ; -> !composite
        ("prime=T -> integer=T", not (F("prime") is True) or F("integer") is True),
        ("composite=T -> integer=T", not (F("composite") is True) or F("integer") is True),
        ("integer=F -> prime=F", not (F("integer") is False) or F("prime") is False),
        ("integer=F -> composite=F", not (F("integer") is False) or F("composite") is False),
        # irrational -> real ; irrational -> !rational ; irrational -> finite
        ("irrational=T -> real=T", not (F("irrational") is True) or F("real") is True),
        ("irrational=T -> rational=F", not (F("irrational") is True) or F("rational") is False),
        ("irrational=T -> finite=T", not (F("irrational") is True) or F("finite") is True),
        # transcendental -> complex ; -> !algebraic ; -> finite
        ("transcendental=T -> complex=T", not (F("transcendental") is True) or F("complex") is True),
        ("transcendental=T -> algebraic=F", not (F("transcendental") is True) or F("algebraic") is False),
        ("transcendental=T -> finite=T", not (F("transcendental") is True) or F("finite") is True),
        # infinite -> !finite
        ("infinite=T -> finite=F", not (F("infinite") is True) or F("finite") is False),
        # !finite -> !rational, !algebraic, !irrational, !transcendental
        ("finite=F -> rational=F", not (F("finite") is False) or F("rational") is False),
        ("finite=F -> algebraic=F", not (F("finite") is False) or F("algebraic") is False),
        ("finite=F -> irrational=F", not (F("finite") is False) or F("irrational") is False),
        ("finite=F -> transcendental=F", not (F("finite") is False) or F("transcendental") is False),
        # noninteger == real & !integer (the True direction) + reverse exclusion
        ("real=T & integer=F -> noninteger=T",
         not (F("real") is True and F("integer") is False) or F("noninteger") is True),
        ("integer=T -> noninteger=F", not (F("integer") is True) or F("noninteger") is False),
        # DEFINING CONDITIONS, reverse direction: meeting a set's defining
        # conditions forces the membership rather than leaving it Unknown.
        # irrational == real & !rational & finite (the <- direction)
        ("real=T & rational=F & finite=T -> irrational=T",
         not (F("real") is True and F("rational") is False and F("finite") is True)
         or F("irrational") is True),
        # even == integer & !odd (the <- direction)
        ("integer=T & odd=F -> even=T",
         not (F("integer") is True and F("odd") is False) or F("even") is True),
        # odd -> !even ; algebraic -> !transcendental ; finite -> !infinite:
        # the remaining EXCLUSION directions of the membership theory.
        ("odd=T -> even=F", not (F("odd") is True) or F("even") is False),
        ("algebraic=T -> transcendental=F",
         not (F("algebraic") is True) or F("transcendental") is False),
        ("finite=T -> infinite=F", not (F("finite") is True) or F("infinite") is False),
        # ORIENTATION: the real line and the imaginary axis meet only at a
        # point no quantity below is pinned to, so realness and imaginariness
        # exclude each other.
        ("real=T -> imaginary=F", not (F("real") is True) or F("imaginary") is False),
        ("imaginary=T -> real=F", not (F("imaginary") is True) or F("real") is False),
        # SIGN REGIONS live on the real line, and non-realness empties them.
        ("positive=T -> real=T", not (F("positive") is True) or F("real") is True),
        ("negative=T -> real=T", not (F("negative") is True) or F("real") is True),
        ("nonpositive=T -> real=T", not (F("nonpositive") is True) or F("real") is True),
        ("nonnegative=T -> real=T", not (F("nonnegative") is True) or F("real") is True),
        ("real=F -> positive=F", not (F("real") is False) or F("positive") is False),
        ("real=F -> negative=F", not (F("real") is False) or F("negative") is False),
        ("real=F -> nonpositive=F", not (F("real") is False) or F("nonpositive") is False),
        ("real=F -> nonnegative=F", not (F("real") is False) or F("nonnegative") is False),
        # DEFINING CONDITIONS for the two weak sign regions: on the real line a
        # ruled-out strict sign settles the opposite bound rather than leaving
        # it Unknown.
        ("real=T & positive=F -> nonpositive=T",
         not (F("real") is True and F("positive") is False) or F("nonpositive") is True),
        ("real=T & negative=F -> nonnegative=T",
         not (F("real") is True and F("negative") is False) or F("nonnegative") is True),
        # EXCLUSION and CONTAINMENT among the sign regions.
        ("positive=T -> negative=F", not (F("positive") is True) or F("negative") is False),
        ("negative=T -> positive=F", not (F("negative") is True) or F("positive") is False),
        ("positive=T -> nonpositive=F",
         not (F("positive") is True) or F("nonpositive") is False),
        ("negative=T -> nonnegative=F",
         not (F("negative") is True) or F("nonnegative") is False),
        ("positive=T -> nonnegative=T",
         not (F("positive") is True) or F("nonnegative") is True),
        ("negative=T -> nonpositive=T",
         not (F("negative") is True) or F("nonpositive") is True),
        # both bounds by zero at once leaves the origin, which is not strict.
        ("nonpositive=T & nonnegative=T -> positive=F",
         not (F("nonpositive") is True and F("nonnegative") is True)
         or F("positive") is False),
        # the two distinguished whole-number classes lie strictly above zero.
        ("prime=T -> positive=T", not (F("prime") is True) or F("positive") is True),
        ("composite=T -> positive=T", not (F("composite") is True) or F("positive") is True),
        # SELF-ADJOINTNESS: lying on the real line / the imaginary axis settles
        # the corresponding adjoint status, and its refusal reflects back.
        ("real=T -> hermitian=T", not (F("real") is True) or F("hermitian") is True),
        ("imaginary=T -> antihermitian=T",
         not (F("imaginary") is True) or F("antihermitian") is True),
        ("hermitian=F -> real=F", not (F("hermitian") is False) or F("real") is False),
        ("antihermitian=F -> imaginary=F",
         not (F("antihermitian") is False) or F("imaginary") is False),
        # THE PUNCTURED REAL LINE. Being definitely away from the origin is a
        # statement about a REAL quantity, so it carries realness and is emptied
        # by non-realness; each strict sign entails it and each of the two
        # one-sided bounds by zero combines with it to give the strict sign back;
        # both bounds at once deny it; on the real line its denial IS the origin,
        # whose parity and both bounds follow; and odd parity, irrationality and
        # unboundedness on the real line each entail it.
        ("nonzero=T -> real=T", not (F("nonzero") is True) or F("real") is True),
        ("real=F -> nonzero=F", not (F("real") is False) or F("nonzero") is False),
        ("positive=T -> nonzero=T", not (F("positive") is True) or F("nonzero") is True),
        ("negative=T -> nonzero=T", not (F("negative") is True) or F("nonzero") is True),
        ("nonpositive=T & nonnegative=T -> nonzero=F",
         not (F("nonpositive") is True and F("nonnegative") is True)
         or F("nonzero") is False),
        ("nonzero=F & real=T -> even=T",
         not (F("nonzero") is False and F("real") is True) or F("even") is True),
        ("nonzero=F & real=T -> nonnegative=T",
         not (F("nonzero") is False and F("real") is True)
         or F("nonnegative") is True),
        ("nonzero=F & real=T -> nonpositive=T",
         not (F("nonzero") is False and F("real") is True)
         or F("nonpositive") is True),
        ("nonzero=T & nonpositive=T -> negative=T",
         not (F("nonzero") is True and F("nonpositive") is True)
         or F("negative") is True),
        ("nonzero=T & nonnegative=T -> positive=T",
         not (F("nonzero") is True and F("nonnegative") is True)
         or F("positive") is True),
        ("odd=T -> nonzero=T", not (F("odd") is True) or F("nonzero") is True),
        ("irrational=T -> nonzero=T",
         not (F("irrational") is True) or F("nonzero") is True),
        ("real=T & finite=F -> nonzero=T",
         not (F("real") is True and F("finite") is False) or F("nonzero") is True),
        # OFF THE REAL LINE. Failing to lie on the real line empties every
        # membership the line contains and every status defined on it.
        ("real=F -> integer=F", not (F("real") is False) or F("integer") is False),
        ("real=F -> rational=F", not (F("real") is False) or F("rational") is False),
        ("real=F -> irrational=F",
         not (F("real") is False) or F("irrational") is False),
        ("real=F -> noninteger=F",
         not (F("real") is False) or F("noninteger") is False),
        # A non-zero multiple of the imaginary unit lies off the real line, so
        # each of those denials reaches it, including its distance from zero.
        ("imaginary=T -> nonzero=F",
         not (F("imaginary") is True) or F("nonzero") is False),
        ("imaginary=T -> irrational=F",
         not (F("imaginary") is True) or F("irrational") is False),
        ("imaginary=T -> rational=F",
         not (F("imaginary") is True) or F("rational") is False),
        ("imaginary=T -> integer=F",
         not (F("imaginary") is True) or F("integer") is False),
        ("imaginary=T -> noninteger=F",
         not (F("imaginary") is True) or F("noninteger") is False),
        # On the real line the one quantity at no distance from the origin IS a
        # whole number, so denying both places the quantity off that line.
        ("nonzero=F & integer=F -> real=F",
         not (F("nonzero") is False and F("integer") is False)
         or F("real") is False),
        # UNBOUNDEDNESS denies each membership whose containment bounds a
        # quantity, and with the whole numbers go parity and both classes.
        ("finite=F -> integer=F", not (F("finite") is False) or F("integer") is False),
        ("finite=F -> even=F", not (F("finite") is False) or F("even") is False),
        ("finite=F -> odd=F", not (F("finite") is False) or F("odd") is False),
        ("finite=F -> prime=F", not (F("finite") is False) or F("prime") is False),
        ("finite=F -> composite=F",
         not (F("finite") is False) or F("composite") is False),
        # OUTSIDE THE COMPLEX NUMBERS. Every quantity of every set this theory
        # speaks about is complex, so failing to be complex places a quantity
        # outside all of them, on neither side of the algebraic divide and on
        # neither the real line nor the imaginary axis.
        ("complex=F -> real=F", not (F("complex") is False) or F("real") is False),
        ("complex=F -> imaginary=F",
         not (F("complex") is False) or F("imaginary") is False),
        ("complex=F -> algebraic=F",
         not (F("complex") is False) or F("algebraic") is False),
        ("complex=F -> transcendental=F",
         not (F("complex") is False) or F("transcendental") is False),
    ]
    return clauses


# --- the seeds the model instantiates the closure at, with the full record
#     the real patched engine deduces for each. Read off the
#     real engine, not reasoned: any disagreement here is a faithfulness defect.
#     The BARE seeds `algebraic=True` / `transcendental=True` are deliberately
#     absent (see the module docstring: their boundedness differs across correct
#     alternatives). `real=True, transcendental=True` IS asserted: adding
#     realness makes the whole record invariant across those same alternatives,
#     so it pins behaviour without pinning one implementation's choices.
SEED_RECORDS = [
    ("deduce_even", {'even': True},
     {'integer': True, 'rational': True, 'real': True, 'finite': True,
      'even': True, 'odd': False, 'algebraic': True, 'transcendental': False,
      'irrational': False, 'infinite': False, 'complex': True,
      'noninteger': False, 'prime': None, 'composite': None}),
    ("deduce_odd", {'odd': True},
     {'integer': True, 'rational': True, 'real': True, 'finite': True,
      'even': False, 'odd': True, 'algebraic': True, 'transcendental': False,
      'irrational': False, 'infinite': False, 'complex': True,
      'noninteger': False, 'prime': None, 'composite': None}),
    ("deduce_integer", {'integer': True},
     {'integer': True, 'rational': True, 'real': True, 'finite': True,
      'even': None, 'odd': None, 'algebraic': True, 'transcendental': False,
      'irrational': False, 'infinite': False, 'complex': True,
      'noninteger': False, 'prime': None, 'composite': None}),
    ("deduce_rational", {'rational': True},
     {'integer': None, 'rational': True, 'real': True, 'finite': True,
      'even': None, 'odd': None, 'algebraic': True, 'transcendental': False,
      'irrational': False, 'infinite': False, 'complex': True,
      'noninteger': None, 'prime': None, 'composite': None}),
    ("deduce_irrational", {'irrational': True},
     {'integer': False, 'rational': False, 'real': True, 'finite': True,
      'even': False, 'odd': False, 'algebraic': None, 'transcendental': None,
      'irrational': True, 'infinite': False, 'complex': True,
      'noninteger': True, 'prime': False, 'composite': False}),
    ("deduce_not_rational", {'rational': False},
     {'integer': False, 'rational': False, 'real': None, 'finite': None,
      'even': False, 'odd': False, 'algebraic': None, 'transcendental': None,
      'irrational': None, 'infinite': None, 'complex': None,
      'noninteger': None, 'prime': False, 'composite': False}),
    ("deduce_not_irrational", {'irrational': False},
     {'integer': None, 'rational': None, 'real': None, 'finite': None,
      'even': None, 'odd': None, 'algebraic': None, 'transcendental': None,
      'irrational': False, 'infinite': None, 'complex': None,
      'noninteger': None, 'prime': None, 'composite': None}),
    ("deduce_not_even", {'even': False},
     {'integer': None, 'rational': None, 'real': None, 'finite': None,
      'even': False, 'odd': None, 'algebraic': None, 'transcendental': None,
      'irrational': None, 'infinite': None, 'complex': None,
      'noninteger': None, 'prime': None, 'composite': None}),
    ("deduce_not_odd", {'odd': False},
     {'integer': None, 'rational': None, 'real': None, 'finite': None,
      'even': None, 'odd': False, 'algebraic': None, 'transcendental': None,
      'irrational': None, 'infinite': None, 'complex': None,
      'noninteger': None, 'prime': None, 'composite': None}),
    # --- the defining-condition seeds. Each hands the engine exactly the
    #     statuses one equivalence needs on its right-hand side; the membership
    #     it defines must come back resolved. Every field below was read off the
    #     real patched engine and is invariant across the correct alternatives
    #     surveyed, so none of it over-fits one implementation.
    ("deduce_real_nonrational_bounded",
     {'real': True, 'rational': False, 'finite': True},
     {'integer': False, 'rational': False, 'real': True, 'finite': True,
      'even': False, 'odd': False, 'algebraic': None, 'transcendental': None,
      'irrational': True, 'infinite': False, 'complex': True,
      'noninteger': True, 'prime': False, 'composite': False}),
    ("deduce_real_transcendental", {'real': True, 'transcendental': True},
     {'integer': False, 'rational': False, 'real': True, 'finite': True,
      'even': False, 'odd': False, 'algebraic': False, 'transcendental': True,
      'irrational': True, 'infinite': False, 'complex': True,
      'noninteger': True, 'prime': False, 'composite': False}),
    # --- the ONE-SIDED seeds: a whole number bounded below / above by zero.
    #     Their sign statuses are asserted alongside the memberships, so the
    #     model's sign pins are measured against the real engine too.
    ("deduce_integer_nonnegative", {'integer': True, 'nonnegative': True},
     {'integer': True, 'rational': True, 'real': True, 'finite': True,
      'even': None, 'odd': None, 'algebraic': True, 'transcendental': False,
      'irrational': False, 'infinite': False, 'complex': True,
      'noninteger': False, 'prime': None, 'composite': None,
      'positive': None, 'negative': False,
      'nonpositive': None, 'nonnegative': True}),
    ("deduce_integer_nonpositive", {'integer': True, 'nonpositive': True},
     {'integer': True, 'rational': True, 'real': True, 'finite': True,
      'even': None, 'odd': None, 'algebraic': True, 'transcendental': False,
      'irrational': False, 'infinite': False, 'complex': True,
      'noninteger': False, 'prime': False, 'composite': False,
      'positive': False, 'negative': None,
      'nonpositive': True, 'nonnegative': None}),
    ("deduce_integer_nonodd", {'integer': True, 'odd': False},
     {'integer': True, 'rational': True, 'real': True, 'finite': True,
      'even': True, 'odd': False, 'algebraic': True, 'transcendental': False,
      'irrational': False, 'infinite': False, 'complex': True,
      'noninteger': False, 'prime': None, 'composite': None}),
    # --- the nine seeds added so the pinned records instantiate the closure at
    #     every clause of the theory rather than at the membership clauses
    #     alone. Each was read off the real patched engine, and every field of
    #     each was measured invariant across the independently-graded correct
    #     alternatives surveyed, so none of it over-fits one implementation.
    #
    #     the CONTAINMENT witness for the algebraic sets: boundedness handed
    #     over as an assumption, so the record turns only on where the
    #     algebraic numbers sit inside the complex ones.
    ('deduce_algebraic_bounded', {'algebraic': True, 'finite': True},
     {'integer': None, 'rational': None, 'real': None, 'finite': True,
      'even': None, 'odd': None, 'algebraic': True, 'transcendental': False,
      'irrational': None, 'infinite': False, 'complex': True,
      'noninteger': None, 'prime': None, 'composite': None, 'imaginary': None,
      'positive': None, 'negative': None, 'nonpositive': None,
      'nonnegative': None, 'hermitian': None, 'antihermitian': None}),
    #
    #     the sign-region frontier: refusing the weak upper region rules out
    #     strict positivity and the two whole-number classes above zero, and
    #     settles nothing about realness.
    ('deduce_not_nonnegative', {'nonnegative': False},
     {'integer': None, 'rational': None, 'real': None, 'finite': None,
      'even': None, 'odd': None, 'algebraic': None, 'transcendental': None,
      'irrational': None, 'infinite': None, 'complex': None,
      'noninteger': None, 'prime': False, 'composite': False,
      'imaginary': None, 'positive': False, 'negative': None,
      'nonpositive': None, 'nonnegative': False, 'hermitian': None,
      'antihermitian': None}),
    #
    #     the same refusal ON the real line, where it resolves the sign
    #     completely: strictly below zero.
    ('deduce_real_not_nonnegative', {'real': True, 'nonnegative': False},
     {'integer': None, 'rational': None, 'real': True, 'finite': None,
      'even': None, 'odd': None, 'algebraic': None, 'transcendental': None,
      'irrational': None, 'infinite': None, 'complex': True,
      'noninteger': None, 'prime': False, 'composite': False,
      'imaginary': False, 'positive': False, 'negative': True,
      'nonpositive': True, 'nonnegative': False, 'hermitian': True,
      'antihermitian': None}),
    ('deduce_real_not_positive', {'real': True, 'positive': False},
     {'integer': None, 'rational': None, 'real': True, 'finite': None,
      'even': None, 'odd': None, 'algebraic': None, 'transcendental': None,
      'irrational': None, 'infinite': None, 'complex': True,
      'noninteger': None, 'prime': False, 'composite': False,
      'imaginary': False, 'positive': False, 'negative': None,
      'nonpositive': True, 'nonnegative': None, 'hermitian': True,
      'antihermitian': None}),
    ('deduce_real_not_negative', {'real': True, 'negative': False},
     {'integer': None, 'rational': None, 'real': True, 'finite': None,
      'even': None, 'odd': None, 'algebraic': None, 'transcendental': None,
      'irrational': None, 'infinite': None, 'complex': True,
      'noninteger': None, 'prime': None, 'composite': None,
      'imaginary': False, 'positive': None, 'negative': False,
      'nonpositive': None, 'nonnegative': True, 'hermitian': True,
      'antihermitian': None}),
    #
    #     both bounds by zero at once: the origin, a bounded whole number
    #     divisible by two whose whole membership table is settled.
    ('deduce_nonnegative_nonpositive',
     {'nonnegative': True, 'nonpositive': True},
     {'integer': True, 'rational': True, 'real': True, 'finite': True,
      'even': True, 'odd': False, 'algebraic': True, 'transcendental': False,
      'irrational': False, 'infinite': False, 'complex': True,
      'noninteger': False, 'prime': False, 'composite': False,
      'imaginary': False, 'positive': False, 'negative': False,
      'nonpositive': True, 'nonnegative': True, 'hermitian': True,
      'antihermitian': None}),
    #
    #     the two distinguished whole-number classes above zero, each
    #     excluding the other.
    ('deduce_prime', {'prime': True},
     {'integer': True, 'rational': True, 'real': True, 'finite': True,
      'even': None, 'odd': None, 'algebraic': True, 'transcendental': False,
      'irrational': False, 'infinite': False, 'complex': True,
      'noninteger': False, 'prime': True, 'composite': False,
      'imaginary': False, 'positive': True, 'negative': False,
      'nonpositive': False, 'nonnegative': True, 'hermitian': True,
      'antihermitian': None}),
    ('deduce_noncomposite_positive_even',
     {'composite': False, 'positive': True, 'even': True},
     {'integer': True, 'rational': True, 'real': True, 'finite': True,
      'even': True, 'odd': False, 'algebraic': True, 'transcendental': False,
      'irrational': False, 'infinite': False, 'complex': True,
      'noninteger': False, 'prime': True, 'composite': False,
      'imaginary': False, 'positive': True, 'negative': False,
      'nonpositive': False, 'nonnegative': True, 'hermitian': True,
      'antihermitian': None}),
    #
    #     the punctured real line: known-non-zero places the quantity on the
    #     real line, off the imaginary axis, self-adjoint.
    ('deduce_nonzero', {'nonzero': True},
     {'integer': None, 'rational': None, 'real': True, 'finite': None,
      'even': None, 'odd': None, 'algebraic': None, 'transcendental': None,
      'irrational': None, 'infinite': None, 'complex': True,
      'noninteger': None, 'prime': None, 'composite': None,
      'imaginary': False, 'positive': None, 'negative': None,
      'nonpositive': None, 'nonnegative': None, 'hermitian': True,
      'antihermitian': None, 'nonzero': True}),
    ('deduce_imaginary', {'imaginary': True},
     {'integer': False, 'rational': False, 'real': False, 'finite':
      None, 'even': False, 'odd': False, 'algebraic': None,
      'transcendental': None, 'irrational': False, 'infinite': None,
      'complex': True, 'noninteger': False, 'prime': False,
      'composite': False, 'imaginary': True, 'positive': False,
      'negative': False, 'nonpositive': False, 'nonnegative': False,
      'hermitian': None, 'antihermitian': True, 'nonzero': False}),
    ('deduce_imaginary_transcendental', {'imaginary': True, 'transcendental': True},
     {'integer': False, 'rational': False, 'real': False, 'finite':
      True, 'even': False, 'odd': False, 'algebraic': False,
      'transcendental': True, 'irrational': False, 'infinite':
      False, 'complex': True, 'noninteger': False, 'prime': False,
      'composite': False, 'imaginary': True, 'positive': False,
      'negative': False, 'nonpositive': False, 'nonnegative': False,
      'hermitian': None, 'antihermitian': True, 'nonzero': False}),
    ('deduce_unbounded', {'finite': False},
     {'integer': False, 'rational': False, 'real': None, 'finite':
      False, 'even': False, 'odd': False, 'algebraic': False,
      'transcendental': False, 'irrational': False, 'infinite':
      None, 'complex': None, 'noninteger': None, 'prime': False,
      'composite': False, 'imaginary': None, 'positive': None,
      'negative': None, 'nonpositive': None, 'nonnegative': None,
      'hermitian': None, 'antihermitian': None, 'nonzero': None}),
    ('deduce_nonreal_at_origin', {'integer': False, 'nonzero': False},
     {'integer': False, 'rational': False, 'real': False, 'finite':
      None, 'even': False, 'odd': False, 'algebraic': None,
      'transcendental': None, 'irrational': False, 'infinite': None,
      'complex': None, 'noninteger': False, 'prime': False,
      'composite': False, 'imaginary': None, 'positive': False,
      'negative': False, 'nonpositive': False, 'nonnegative': False,
      'hermitian': None, 'antihermitian': None, 'nonzero': False}),
    ('deduce_not_antihermitian', {'antihermitian': False},
     {'integer': None, 'rational': None, 'real': None, 'finite':
      None, 'even': None, 'odd': None, 'algebraic': None,
      'transcendental': None, 'irrational': None, 'infinite': None,
      'complex': None, 'noninteger': None, 'prime': None,
      'composite': None, 'imaginary': False, 'positive': None,
      'negative': None, 'nonpositive': None, 'nonnegative': None,
      'hermitian': None, 'antihermitian': False, 'nonzero': None}),
    ('deduce_commuting', {'commutative': True},
     {'integer': None, 'rational': None, 'real': None, 'finite':
      None, 'even': None, 'odd': None, 'algebraic': None,
      'transcendental': None, 'irrational': None, 'infinite':
      None, 'complex': None, 'noninteger': None, 'prime': None,
      'composite': None, 'imaginary': None, 'positive': None,
      'negative': None, 'nonpositive': None, 'nonnegative': None,
      'hermitian': None, 'antihermitian': None, 'nonzero': None}),
    ('deduce_noncommuting', {'commutative': False},
     {'integer': False, 'rational': False, 'real': False,
      'finite': None, 'even': False, 'odd': False, 'algebraic':
      False, 'transcendental': False, 'irrational': False,
      'infinite': None, 'complex': False, 'noninteger': False,
      'prime': False, 'composite': False, 'imaginary': False,
      'positive': False, 'negative': False, 'nonpositive': False,
      'nonnegative': False, 'hermitian': None, 'antihermitian':
      None, 'nonzero': False}),
]

# --- the non-zero status ("definitely away from the origin") of every seed
#     above, read off the real engine the same way and merged into the records.
#     It is kept as its own table because it is the one field that EVERY seed's
#     postcondition in model.py now pins: each value below was measured at the
#     modelled reference AND re-measured identically with the modelled change
#     absent, so it depends only on relations the reference theory already holds
#     and a pin on it cannot over-fit one implementation's choices. The records
#     resolving it True do so for three different reasons here (a strict sign,
#     odd parity, irrationality) and a fourth on the unbounded seed checked in
#     main() (unboundedness on the real line); the one record resolving it False
#     is the origin. Between them the merged records instantiate every clause of
#     the punctured real line on a record free to fail it.
SEED_NONZERO = {
    'deduce_even': None,
    'deduce_odd': True,
    'deduce_integer': None,
    'deduce_rational': None,
    'deduce_irrational': True,
    'deduce_not_rational': None,
    'deduce_not_irrational': None,
    'deduce_not_even': None,
    'deduce_not_odd': None,
    'deduce_real_nonrational_bounded': True,
    'deduce_real_transcendental': True,
    'deduce_integer_nonnegative': None,
    'deduce_integer_nonpositive': None,
    'deduce_integer_nonodd': None,
    'deduce_algebraic_bounded': None,
    'deduce_not_nonnegative': None,
    'deduce_real_not_nonnegative': True,
    'deduce_real_not_positive': None,
    'deduce_real_not_negative': None,
    'deduce_nonnegative_nonpositive': False,
    'deduce_prime': True,
    'deduce_noncomposite_positive_even': True,
    'deduce_nonzero': True,
    'deduce_imaginary': False,
    'deduce_imaginary_transcendental': False,
    'deduce_unbounded': None,
    'deduce_nonreal_at_origin': False,
    'deduce_not_antihermitian': None,
    'deduce_commuting': None,
    'deduce_noncommuting': False,
}
assert sorted(n for n, _s, _t in SEED_RECORDS) == sorted(SEED_NONZERO), (
    "SEED_NONZERO must cover exactly the seeds instantiated above")
for _name, _seed, _tbl in SEED_RECORDS:
    _want = SEED_NONZERO[_name]
    assert _tbl.get('nonzero', _want) is _want, (
        "SEED_NONZERO disagrees with an inline record on %s" % _name)
    _tbl['nonzero'] = _want


def assert_theory(obj, label):
    """Assert the real engine's deduced facts for `obj` are closed under the
    model's containment theory (clause by clause)."""
    k = read_kb(obj)
    for desc, holds in theory_clauses(k):
        assert holds, (
            "THEORY VIOLATION on %s: clause %r failed; deduced facts = %s"
            % (label, desc, {p: k[p] for p in PROPS}))


def main():
    from sympy import Symbol, S

    checked = 0

    # --- (1) FAITHFULNESS: the F2P-witnessed queries, enumerated -------------
    # behaviour 1: even -> finite, plus the full closed fact table the model's
    # deduce_even postconditions pin (every KB field)
    e = Symbol("e", even=True)
    assert e.is_even is True, "F2P even seed lost"
    assert e.is_finite is True, (
        "F2P FAIL (deduce_even): even=True must give is_finite True, got %r"
        % (e.is_finite,))
    checked += 1
    expected_even = {
        "even": True, "integer": True, "rational": True, "real": True,
        "algebraic": True, "finite": True, "complex": True,
        "odd": False, "noninteger": False, "transcendental": False,
        "irrational": False, "infinite": False, "prime": None,
        "composite": None,
        # parity alone does not move a quantity away from the origin: the origin
        # is itself an even whole number, so this stays Unknown here.
        "nonzero": None,
    }
    for prop, want in expected_even.items():
        got = getattr(e, "is_%s" % prop)
        assert got is want, (
            "F2P FAIL (deduce_even): Symbol(even=True).is_%s must be %r, got %r"
            % (prop, want, got))
        checked += 1

    # behaviour 2: unbounded real quantity (S.Infinity) -> set memberships False
    oo = S.Infinity
    expected_inf = {
        "infinite": True, "real": True, "finite": False,
        "rational": False, "integer": False, "even": False, "odd": False,
        "algebraic": False, "transcendental": False, "irrational": False,
        "composite": False, "noninteger": True,
        "complex": True, "prime": False,
        # growing beyond every bound on the real line puts a quantity away from
        # the origin, in either direction (-oo satisfies this too, below).
        "nonzero": True,
    }
    for prop, want in expected_inf.items():
        got = getattr(oo, "is_%s" % prop)
        assert got is want, (
            "F2P FAIL (deduce_infinite): S.Infinity.is_%s must be %r, got %r"
            % (prop, want, got))
        checked += 1
    # the negative-infinity witness behaves identically on these queries
    mm = S.NegativeInfinity
    for prop, want in expected_inf.items():
        if prop == "real":
            continue
        got = getattr(mm, "is_%s" % prop)
        assert got is want, (
            "F2P FAIL (deduce_infinite, -oo): is_%s must be %r, got %r"
            % (prop, want, got))
        checked += 1

    # behaviour 2b: SIGN NEUTRALITY of unboundedness. The two concrete
    # unbounded quantities above agree on every membership and DISAGREE on sign
    # (each carries its own direction as a declared assumption), so the relation
    # from unboundedness cannot decide a sign: a quantity known only to be
    # unbounded and real must leave every sign region Unknown -- not merely the
    # strict signs but both bounds by zero. This is the obligation the model's
    # unbounded seed states with `Ensures(Result().positive is None)` and its
    # three companions; a rule set deriving a sign here would contradict the
    # oppositely-unbounded quantity.
    assert oo.is_positive is True and mm.is_negative is True, (
        "the two unbounded witnesses must carry opposite signs")
    checked += 2
    u = Symbol("u", infinite=True, real=True)
    assert u.is_infinite is True and u.is_finite is False, (
        "SIGN FAIL: the unbounded real seed lost its own seed facts")
    for prop in ("positive", "negative", "nonpositive", "nonnegative"):
        got = getattr(u, "is_%s" % prop)
        assert got is None, (
            "SIGN FAIL (deduce_infinite): a quantity known only to be unbounded "
            "and real must leave is_%s Unknown, got %r" % (prop, got))
        checked += 1
    # ... while the NON-ZERO status is resolved by unboundedness on the real line
    # in both directions, with no sign known. This is the one place the pins
    # separate "away from the origin" from "of known sign": the model's unbounded
    # seed pins it True alongside the four Unknown sign statuses above.
    assert u.is_nonzero is True, (
        "PER-SEED FAIL (deduce_infinite): a quantity known to be unbounded and "
        "real must resolve is_nonzero True, got %r" % (u.is_nonzero,))
    checked += 1

    # behaviour 3: the PER-SEED obligation. Each of the seeds the model
    # instantiates the closure at must deduce exactly the recorded table on
    # the real engine — including the five bounded seeds resolving
    # is_finite to True (so a rule set that bounds only one of them fails here)
    # and the four frontier seeds leaving it None (so a rule set that resolves
    # boundedness everywhere fails here).
    for fname, seed, want_tbl in SEED_RECORDS:
        sym = Symbol("q", **seed)
        for prop, want in want_tbl.items():
            got = getattr(sym, "is_%s" % prop)
            assert got is want, (
                "PER-SEED FAIL (%s): Symbol(%s).is_%s must be %r, got %r"
                % (fname, seed, prop, want, got))
            checked += 1

    # --- (2) THEORY soundness: closure holds on a wide family of seeds -------
    # the special numeric singletons whose facts the F2P + P2P tests observe
    assert_theory(S.Infinity, "S.Infinity"); checked += 1
    assert_theory(S.NegativeInfinity, "S.NegativeInfinity"); checked += 1
    assert_theory(S.Zero, "S.Zero"); checked += 1
    assert_theory(S.One, "S.One"); checked += 1
    assert_theory(S.Half, "S.Half"); checked += 1
    assert_theory(S.Pi, "S.Pi"); checked += 1
    assert_theory(S.Exp1, "S.Exp1"); checked += 1
    assert_theory(S.ImaginaryUnit, "S.ImaginaryUnit"); checked += 1

    # symbolic seeds: every single assumption that the theory mentions, plus
    # consistent pairs. Inconsistent combinations raise; we skip only those
    # (a raise means the seed is not a satisfiable assumption set, not an F2P
    # case), but record that the F2P seeds above were exercised non-skipped.
    seed_facts = ["integer", "rational", "real", "finite", "even", "odd",
                  "algebraic", "transcendental", "irrational", "infinite",
                  "complex", "prime", "composite", "positive", "negative",
                  "imaginary", "nonpositive", "nonnegative", "nonzero",
                  "hermitian", "antihermitian"]
    singles = []
    for f in seed_facts:
        for val in (True, False):
            singles.append({f: val})
    pairs = []
    for a, b in itertools.combinations(seed_facts, 2):
        for va in (True, False):
            for vb in (True, False):
                pairs.append({a: va, b: vb})

    for seed in singles + pairs:
        try:
            sym = Symbol("s", **seed)
        except Exception:
            # inconsistent assumption set rejected at construction; not a
            # closure obligation
            continue
        assert_theory(sym, "Symbol(%s)" % seed)
        checked += 1

    print("G-AX OK: deep model `consistent_theory` + deducers validated against "
          "the REAL sympy assumptions engine on %d observations (F2P queries "
          "enumerated non-skipped; closure theory holds on all satisfiable "
          "single+pair seeds and the numeric singletons)." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
