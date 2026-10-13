"""Twin-artifact model for django__django-11880.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Producing an independent duplicate of a form field must yield a field that is
  observably *sealed away* from the original: replacing or mutating one of the
  duplicate's mutable per-field collections must never be reflected on the
  original, and vice versa. Two such collections matter here.

  For EACH such collection the duplicate must carry a SEPARATE container object
  whose contents equal the original's at the moment of duplication:

    (1) the validator collection of the duplicate is a distinct list object
        holding the same validators, in order, as the original (this collection
        was already independent before this change), and

    (2) the per-field message overrides of the duplicate are likewise a
        distinct collection object holding the same overrides as the original.
        Because the collection is a distinct object, replacing or mutating one
        field's overrides leaves every other field's overrides untouched.

  The original field is read-only throughout duplication: its own collections
  are left exactly as they were, with the same contents.

A field is modelled as a minimal object exposing only the two touched mutable
collections. The per-field message overrides are a mapping from an override
code to an override value; the tested behaviour observes only (a) WHICH codes
are present and (b) the value bound to each, and crucially that the duplicate's
mapping is a SEPARATE object from the original's. So the mapping is carried by
two index-aligned `List[int]` — `msg_codes[k]` bound to `msg_values[k]` — and
the validators by a `List[int]` of validator identities. Object distinctness
("the duplicate owns its own collection") is carried by Nagini's separation:
the duplicate holds full permission to its own collections while the original
retains permission to its own, provable only when the two are distinct objects
(`is not`). No callee is axiomatized: the duplication is pure object/structure
logic, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms: the duplication is pure object/structure logic, modelled
# deeply (a distinct collection object with equal contents). The shallow-copy
# primitive the duplication builds on is validated against its real Python
# semantics out-of-band by axiom_check.py (G-AX) as an A-reference, not
# consumed here.
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


class Field:
    def __init__(self) -> None:
        # Terminates: no loops and no calls — exactly three attribute stores.
        # Level 2 leaves room BELOW deep_duplicate's level 6 (a caller's level must
        # strictly exceed its callee's) and above the list literals it builds.
        Requires(MustTerminate(2))
        Ensures(Acc(self.msg_codes) and Acc(list_pred(self.msg_codes)))  # type: ignore
        Ensures(len(self.msg_codes) == 0)  # type: ignore
        Ensures(Acc(self.msg_values) and Acc(list_pred(self.msg_values)))  # type: ignore
        Ensures(len(self.msg_values) == 0)  # type: ignore
        Ensures(Acc(self.validators) and Acc(list_pred(self.validators)))  # type: ignore
        Ensures(len(self.validators) == 0)  # type: ignore
        self.msg_codes = []  # type: List[int]
        self.msg_values = []  # type: List[int]
        self.validators = []  # type: List[int]


def deep_duplicate(self: Field) -> Field:
    # pre-conditions-start
    # The original field is read-only: its collections are required (and
    # ensured) only at fractional permission.
    Requires(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
    Requires(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
    Requires(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
    # The two arrays carrying the override mapping are index-aligned.
    Requires(len(self.msg_codes) == len(self.msg_values))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    # The original field is left exactly as it was: same overrides, same
    # validators, untouched (returned at the same fractional permission).
    Ensures(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
    Ensures(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
    Ensures(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
    Ensures(len(self.msg_codes) == Old(len(self.msg_codes)))
    Ensures(len(self.msg_values) == Old(len(self.msg_values)))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
                                            self.msg_codes[k] == Old(self.msg_codes[k])))))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
                                            self.msg_values[k] == Old(self.msg_values[k])))))
    Ensures(len(self.validators) == Old(len(self.validators)))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(self.validators),
                                            self.validators[k] == Old(self.validators[k])))))

    # The duplicate is a fully-owned object whose mutable collections are
    # DISTINCT container objects from the original's. The `is not` clauses are
    # the discriminating guarantee: a duplicate that shared either collection
    # with the original (so that mutating one reached the other) is rejected.
    Ensures(Acc(Result().msg_codes) and Acc(list_pred(Result().msg_codes)))
    Ensures(Acc(Result().msg_values) and Acc(list_pred(Result().msg_values)))
    Ensures(Result().msg_codes is not self.msg_codes)
    Ensures(Result().msg_values is not self.msg_values)
    Ensures(Acc(Result().validators) and Acc(list_pred(Result().validators)))
    Ensures(Result().validators is not self.validators)

    # The distinct collections hold the same contents as the original's at the
    # moment of duplication: the same override codes bound to the same values ...
    Ensures(len(Result().msg_codes) == len(self.msg_codes))
    Ensures(len(Result().msg_values) == len(self.msg_values))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
                                            Result().msg_codes[k] == self.msg_codes[k]))))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
                                            Result().msg_values[k] == self.msg_values[k]))))
    # ... and the same validators in the same order.
    Ensures(len(Result().validators) == len(self.validators))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(self.validators),
                                            Result().validators[k] == self.validators[k]))))
    # post-conditions-end
    # impl-start
    result = Field()

    # result.error_messages = self.error_messages.copy()  -- a fresh collection
    # holding the same overrides as the original (the added line).
    a = 0
    while a < len(self.msg_codes):
        # invariants-start
        Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
        Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
        Invariant(len(self.msg_codes) == len(self.msg_values))
        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
                                                  self.msg_values[k] == Old(self.msg_values[k])))))
        Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
        Invariant(result.msg_codes is not self.msg_codes)
        Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
        Invariant(result.msg_values is not self.msg_values)
        Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
        Invariant(len(result.validators) == 0)
        Invariant(0 <= a and a <= len(self.msg_codes))
        Invariant(len(result.msg_codes) == a)
        Invariant(len(result.msg_values) == a)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < a,
                                                  result.msg_codes[k] == self.msg_codes[k]))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < a,
                                                  result.msg_values[k] == self.msg_values[k]))))
        Invariant(MustTerminate(len(self.msg_codes) - a + 1))
        # invariants-end
        result.msg_codes.append(self.msg_codes[a])
        result.msg_values.append(self.msg_values[a])
        a = a + 1

    # result.validators = self.validators[:]  -- a fresh list holding the same
    # validators in order (this collection was already copied before the fix).
    b = 0
    while b < len(self.validators):
        # invariants-start
        Invariant(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
        Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
        Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
        Invariant(len(self.msg_codes) == len(self.msg_values))
        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
        Invariant(len(self.validators) == Old(len(self.validators)))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
                                                  self.msg_values[k] == Old(self.msg_values[k])))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.validators),
                                                  self.validators[k] == Old(self.validators[k])))))
        Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
        Invariant(result.validators is not self.validators)
        Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
        Invariant(result.msg_codes is not self.msg_codes)
        Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
        Invariant(result.msg_values is not self.msg_values)
        Invariant(len(result.msg_codes) == len(self.msg_codes))
        Invariant(len(result.msg_values) == len(self.msg_values))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
                                                  result.msg_codes[k] == self.msg_codes[k]))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
                                                  result.msg_values[k] == self.msg_values[k]))))
        Invariant(0 <= b and b <= len(self.validators))
        Invariant(len(result.validators) == b)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < b,
                                                  result.validators[k] == self.validators[k]))))
        Invariant(MustTerminate(len(self.validators) - b + 1))
        # invariants-end
        result.validators.append(self.validators[b])
        b = b + 1
    return result
    # impl-end
