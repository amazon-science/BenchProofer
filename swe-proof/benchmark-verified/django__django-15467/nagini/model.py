"""Twin-artifact model for django__django-15467.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A form field is built for a relation that is rendered as a set of radio
  choices. Such a field carries an "empty choice" label -- the token shown for
  the not-selected option. The keyword arguments collected for building the
  field form a mapping; one distinguished key holds that empty-choice label.
  Two facts about the relation matter: whether it permits the empty selection
  (the "permits-empty" flag), and whether the caller has ALREADY supplied an
  empty-choice label in the keyword mapping.

  The required outcome for the empty-choice label entry of the mapping:

    * when the relation does NOT permit the empty selection, the entry is the
      ABSENT sentinel (no empty choice is offered), regardless of anything the
      caller supplied;

    * when the relation DOES permit the empty selection, a caller-supplied
      label is RESPECTED: if the keyword mapping already carries the
      empty-choice key, its existing value is kept verbatim (even when that
      value is a falsy/blank token); only when the key is absent is the
      built-in default empty-choice label used.

  The behaviour that matters: with a relation that permits the empty selection
  and a caller-supplied empty-choice label, the result is the caller's label,
  NOT the built-in default. Presence of the key -- not the truthiness of its
  value -- is what makes the caller's value win.

Modelling choices (Nagini fragment):
  * The keyword mapping is a ``Dict[int, int]``: the distinguished empty-choice
    key is a constant integer token, and a label is a constant integer code (the
    absent sentinel, the built-in default, and any caller label being distinct
    integer codes). Only key membership and per-key value are observed, so an
    integer-valued carrier faithfully abstracts the real string-keyed mapping
    of arbitrary label values (mapping.md §2). Membership models "the caller
    supplied the key"; the stored value is read back verbatim -- the absent
    sentinel is a legitimate stored value distinct from "key absent".
  * The mapping is genuinely written (the empty-choice entry is assigned), so
    it is held at FULL permission and its post-state at the empty-choice key is
    pinned exactly.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axiomatised callees: the modelled behaviour is a pure mapping update
#  spelled out deeply in the impl region.)
# axioms-end


# pure-start
@Pure
def empty_label_key() -> int:
    # The distinguished mapping key holding the empty-choice label.
    return 1


@Pure
def absent_label() -> int:
    # The sentinel stored when no empty choice is offered (the relation does
    # not permit the empty selection). Distinct from every real label.
    return 0


@Pure
def default_label() -> int:
    # The built-in default empty-choice label, used only when the relation
    # permits the empty selection and the caller supplied no label. Distinct
    # from the absent sentinel.
    return 2
# pure-end


def set_radio_empty_label(permits_empty: bool, kwargs: Dict[int, int]) -> int:
    # pre-conditions-start
    # The mapping is written (the empty-choice entry is assigned), so FULL
    # permission is required.
    Requires(dict_pred(kwargs))
    Requires(kwargs is not None)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(dict_pred(kwargs))
    Ensures(kwargs is not None)
    # The empty-choice key is present in the resulting mapping, and the
    # returned value is exactly that entry.
    Ensures(empty_label_key() in kwargs)
    Ensures(kwargs[empty_label_key()] == Result())
    # When the relation does NOT permit the empty selection, the empty-choice
    # entry is the absent sentinel -- nothing the caller supplied survives.
    Ensures(Implies(not permits_empty, Result() == absent_label()))
    # When the relation DOES permit the empty selection and the caller ALREADY
    # supplied the empty-choice key, that existing value is kept verbatim
    # (membership wins, regardless of the value's truthiness -- e.g. it may be
    # the absent sentinel as a deliberate caller choice).
    Ensures(Implies(permits_empty and Old(empty_label_key() in kwargs),
                    Result() == Old(kwargs[empty_label_key()])))
    # When the relation DOES permit the empty selection and the caller supplied
    # NO empty-choice key, the built-in default empty-choice label is used.
    Ensures(Implies(permits_empty and not Old(empty_label_key() in kwargs),
                    Result() == default_label()))
    # FRAME: the whole mapping is forwarded downstream to build the field, so
    # every entry is observable. Every key OTHER than the empty-choice key must
    # be left untouched: no other key appears or disappears, and each surviving
    # entry keeps its value verbatim.
    Ensures(Forall(int, lambda k: Implies(
        k != empty_label_key(),
        ((k in kwargs) == Old(k in kwargs)) and
        Implies(Old(k in kwargs), kwargs[k] == Old(kwargs[k])))))
    # post-conditions-end
    # impl-start
    if permits_empty:
        if empty_label_key() in kwargs:
            value = kwargs[empty_label_key()]
        else:
            value = default_label()
    else:
        value = absent_label()
    kwargs[empty_label_key()] = value
    return value
    # impl-end
