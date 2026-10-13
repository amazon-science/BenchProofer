"""Twin-artifact model for django__django-12193.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A boolean-style input widget prepares the attribute mapping that is handed to
  the shared rendering step. Whether the box is shown as selected is decided by
  a definite predicate on the supplied value: the value counts as selected unless
  it is one of the three "empty" sentinels (the boolean false, the absent value,
  or the empty text); every other value counts as selected.

  Two observations are pinned.

  (1) When the value counts as selected, the attribute mapping the rendering
      step receives carries the selection attribute set to true. Every other
      attribute already configured by the caller is carried through with its
      original value; the selection attribute is the only one established.

  (2) When the value does NOT count as selected, the attribute mapping the
      rendering step receives carries exactly the caller's attributes, with no
      selection attribute forced on.

  The consequence that matters: preparing the attribute mapping must NOT alter
  the caller's own mapping. The caller may reuse one mapping object to render a
  sequence of these widgets; if preparing the attributes for one selected value
  changed the caller's mapping, every later widget built from the same mapping
  would inherit the selection attribute even when its own value is not selected.
  The caller's mapping is therefore read-only here, and the prepared mapping is
  a fresh one.

Modelling choices (Nagini fragment):
  * An attribute mapping is a ``Dict[int, bool]`` from an attribute-name token
    to its flag value; only membership and per-key value are observed, so
    integer-keyed identity is the faithful carrier (mapping.md §2). The
    selection attribute name is the module-level constant ``attr_selected()``.
  * The supplied value is an ``int`` code; the selection predicate is modelled
    deeply (``counts_as_selected``) as the repo's definite "not one of the three
    empty sentinels" rule (mapping.md §2), rather than pinned to an opaque
    oracle.
  * The fresh-mapping merge ``{**caller, attr: flag}`` is a standard mapping
    construction the code composes; it is the single callee ``mapping_with``,
    whose standard semantics are validated against real Python out-of-band
    (axiom_check.py, G-AX). It always allocates a NEW mapping, so the caller's
    mapping is never the result and is never written.

The caller's attribute mapping is read-only, so it is held at HALF permission
(Required AND Ensured) and never written. No string indexing is used (Nagini
bans it). Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Dict, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@ContractOnly
def mapping_with(base: Dict[int, bool], key: int, flag: bool) -> Dict[int, bool]:
    """Standard mapping construction ``{**base, key: flag}`` (an unchanged
    language primitive the code composes): a FRESH mapping holding every key of
    ``base`` plus ``key``, with ``flag`` the value at ``key`` and ``base``'s
    value at every other key. The result is always a new object, distinct from
    ``base`` (so ``base`` is read-only). Provenance + executable soundness
    check: mapping.md / axiom_check.py (G-AX)."""
    Requires(Acc(dict_pred(base), 1 / 2))
    Requires(MustTerminate(2))
    Ensures(Acc(dict_pred(base), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # A fresh mapping: never the base object (base stays unmutated).
    Ensures(Result() is not base)
    # The named key is present with the supplied flag.
    Ensures(key in Result() and Result()[key] == flag)
    # Every other key of base is carried through with base's value ...
    Ensures(Forall(int, lambda k: (Implies(k != key and k in base,
                                           (k in Result()) and Result()[k] == base[k]))))
    # ... and the result holds no key outside base plus the named key.
    Ensures(Forall(int, lambda k: (Implies(k in Result(),
                                           k == key or k in base))))


@ContractOnly
def mapping_copy(base: Dict[int, bool]) -> Dict[int, bool]:
    """Standard mapping copy ``{**base}`` (an unchanged language primitive): a
    FRESH mapping holding exactly every key of ``base`` with its value, distinct
    from ``base``. Provenance + executable soundness check: mapping.md /
    axiom_check.py (G-AX)."""
    Requires(Acc(dict_pred(base), 1 / 2))
    Requires(MustTerminate(6))
    Ensures(Acc(dict_pred(base), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    Ensures(Result() is not base)
    Ensures(Forall(int, lambda k: (Implies(k in base,
                                           (k in Result()) and Result()[k] == base[k]))))
    Ensures(Forall(int, lambda k: (Implies(k in Result(),
                                           (k in base) and Result()[k] == base[k]))))
# axioms-end


# pure-start
@Pure
def attr_selected() -> int:
    # The attribute-name token for the selection flag the widget establishes.
    return 0


@Pure
def val_false() -> int:
    # Value code for the boolean-false sentinel (one of the three "empty"
    # values that count as NOT selected).
    return -1


@Pure
def val_absent() -> int:
    # Value code for the absent-value sentinel.
    return -2


@Pure
def val_empty_text() -> int:
    # Value code for the empty-text sentinel.
    return -3


@Pure
def counts_as_selected(value: int) -> bool:
    """The definite selection predicate: a value counts as selected unless it is
    one of the three empty sentinels (boolean false / absent / empty text)."""
    return not (value == val_false()
                or value == val_absent()
                or value == val_empty_text())
# pure-end


def prepare_attrs(value: int, attrs: Dict[int, bool]) -> Dict[int, bool]:
    # pre-conditions-start
    # The caller's attribute mapping is read-only here: HALF permission, never
    # written. (Held read-only so the operation cannot satisfy its postcondition
    # by overwriting the caller's mapping; the caller may reuse it for a
    # sequence of widgets and must observe it unchanged.)
    Requires(Acc(dict_pred(attrs), 1 / 2))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    # The caller's mapping is returned untouched at the same half permission.
    Ensures(Acc(dict_pred(attrs), 1 / 2))
    # A fresh, full-permission mapping is prepared for the rendering step.
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # The prepared mapping is a DIFFERENT object from the caller's mapping.
    Ensures(Result() is not attrs)
    # (1) When the value counts as selected, the prepared mapping carries the
    #     selection attribute set to true ...
    Ensures(Implies(counts_as_selected(value),
                    attr_selected() in Result() and Result()[attr_selected()] == True))
    # ... and every OTHER caller attribute is carried through with its value.
    Ensures(Implies(counts_as_selected(value),
        Forall(int, lambda k: (Implies(k != attr_selected() and k in attrs,
                                       (k in Result()) and Result()[k] == attrs[k])))))
    # ... and the prepared mapping introduces no key the caller did not have,
    #     other than the selection attribute itself.
    Ensures(Implies(counts_as_selected(value),
        Forall(int, lambda k: (Implies(k in Result(),
                                       k == attr_selected() or k in attrs)))))
    # (2) When the value does NOT count as selected, the prepared mapping holds
    #     exactly the caller's attributes (no selection attribute forced on):
    #     same keys, same values, in both directions.
    Ensures(Implies(not counts_as_selected(value),
        Forall(int, lambda k: (Implies(k in attrs,
                                       (k in Result()) and Result()[k] == attrs[k])))))
    Ensures(Implies(not counts_as_selected(value),
        Forall(int, lambda k: (Implies(k in Result(),
                                       (k in attrs) and Result()[k] == attrs[k])))))
    # post-conditions-end
    # impl-start
    # PRE-PATCH skeleton: the selection attribute is written into the caller's
    # OWN mapping in place, and that same mapping object is then handed on. This
    # mutates the caller's mapping (which the caller may reuse for a sequence of
    # widgets) and returns the very object passed in.
    if counts_as_selected(value):
        attrs[attr_selected()] = True
        return attrs
    return attrs
    # impl-end
