"""Twin-artifact model for django__django-11999.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a model class is being assembled and one of its fields offers a
  predetermined set of selectable values, the class is given a generated
  accessor that
  returns the human-readable label for the field's stored value. The accessor
  is published on the class under a name derived from the field's name (the
  conventional ``get_<field>_display`` accessor name).

  The behaviour that matters: the generated accessor must be installed ONLY
  when the class does not already provide an accessor under that name.

    * If the class already defines its own accessor of that name -- for
      instance a hand-written method the author wrote to compute a custom
      display value -- that existing accessor MUST be preserved and the
      generated one MUST NOT overwrite it.
    * If no accessor of that name exists yet, the generated one is installed.

  Either way, after assembly an accessor of that name is present on the class,
  and the operation concerns ONLY the accessor name: no other attribute is
  added, removed, or rebound — every other name keeps exactly the membership
  and bound value it had before assembly.

  The accessor-installation step is also a BOUNDED step of class assembly: it
  always runs to completion in finitely many steps and hands control back, so
  the class finishes being assembled and becomes usable. Every claim above is a
  claim about an operation that finishes; an assembly step that never hands
  control back does not realise this behaviour, however it may look on the
  attribute namespace.

These are the two observable behaviours of the single guarded-installation
operation. They are modelled as two functions sharing one byte-identical
installation skeleton, each under the clean precondition that distinguishes
its case (``preserve_existing_accessor``: the name is already provided;
``install_missing_accessor``: the name is not yet provided).

Modelling choices (Nagini fragment):
  * The class attribute namespace is a ``Dict[int, int]`` from an
    attribute-name token to a method-identity token: the value records WHICH
    callable is bound under that name. Only membership (does the class provide
    that name) and per-name identity (which callable is bound) are observed, so
    integer identity is the faithful carrier (mapping.md §2).
  * The accessor name derived from the field is a parameter (an attribute-name
    token). The generated accessor's identity is the module-level constant
    ``generated_accessor()``; an author-defined accessor is any other identity.
  * Presence of the accessor name as a key models "the class already provides
    that name" (the resolvability test); absence models "no such name yet".

The class namespace is genuinely mutated in place (an accessor may be added to
it), so it is held at full permission and its exact post-state is stated. No
string indexing is used (Nagini bans it). Boundedness of the step is stated as a
termination obligation, so the accessor claims are total rather than conditional
on the step happening to finish. The behaviour is modelled deeply (the guarded
installation is spelled out in the impl region); there is no axiomatised callee.
Markers (machine-parsed) delimit the spec / proof / impl regions; per-function
regions repeat, one set per modelled function.
"""
from typing import Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No axioms: the guarded accessor installation is the behaviour under
# specification and is spelled out deeply in the impl region. There is no
# unchanged opaque callee to axiomatise.
# axioms-end


# pure-start
@Pure
def generated_accessor() -> int:
    # The method-identity token of the generated display accessor that
    # assembly would install for a field offering selectable values.
    return 0


@Pure
def other_name() -> int:
    # A representative pre-existing, unrelated class-attribute name (some other
    # method or attribute the class already carries). It witnesses that the
    # operation leaves attributes other than the accessor name untouched.
    return 1
# pure-end


def preserve_existing_accessor(cls: Dict[int, int], accessor_name: int) -> None:
    # pre-conditions-start
    # The class attribute namespace is mutated in place; full permission.
    Requires(dict_pred(cls))
    # This case: the class ALREADY provides an accessor of this name (the
    # author wrote one, or it was inherited).
    Requires(accessor_name in cls)
    # A representative unrelated attribute is already present on the class.
    Requires(other_name() in cls)
    Requires(other_name() != accessor_name)
    # The step is BOUNDED: it runs to completion in finitely many steps and
    # hands control back, so class assembly finishes and the class becomes
    # usable. This makes the accessor claims below TOTAL — they are claims about
    # a step that finishes, not claims held only of runs that happen to reach
    # the end. The budget (2) is what the single guarded namespace write costs.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(dict_pred(cls))
    # The accessor of this name remains present ...
    Ensures(accessor_name in cls)
    # ... and the accessor bound under this name is exactly the one that was
    # already there: the generated accessor is not installed over it. This is
    # the clause that lets an author-defined accessor of the same name stand.
    Ensures(cls[accessor_name] == Old(cls[accessor_name]))
    # A representative unrelated attribute keeps its exact bound identity: the
    # operation does not disturb a name other than the accessor name.
    Ensures(other_name() in cls)
    Ensures(cls[other_name()] == Old(cls[other_name()]))
    # Whole-namespace frame: in this case the operation performs NO write at
    # all, so no name's membership changes and every name that was present
    # keeps its exact bound identity. (Explicit triggers keep the quantifiers
    # tractable for the verifier.)
    Ensures(Forall(int, lambda k: ((k in cls) == Old(k in cls), [[k in cls]])))
    Ensures(Forall(int, lambda k: (Implies(k in cls and Old(k in cls), cls[k] == Old(cls[k])), [[cls[k]]])))
    # post-conditions-end
    # impl-start
    if accessor_name not in cls:
        cls[accessor_name] = generated_accessor()
    # impl-end


def install_missing_accessor(cls: Dict[int, int], accessor_name: int) -> None:
    # pre-conditions-start
    # The class attribute namespace is mutated in place; full permission.
    Requires(dict_pred(cls))
    # This case: the class does NOT yet provide an accessor of this name.
    Requires(accessor_name not in cls)
    # A representative unrelated attribute is already present on the class.
    Requires(other_name() in cls)
    Requires(other_name() != accessor_name)
    # The step is BOUNDED: it runs to completion in finitely many steps and
    # hands control back, so class assembly finishes and the class becomes
    # usable. This makes the accessor claims below TOTAL — they are claims about
    # a step that finishes, not claims held only of runs that happen to reach
    # the end. The budget (2) is what the single guarded namespace write costs.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(dict_pred(cls))
    # The generated accessor is now installed and present under this name.
    Ensures(accessor_name in cls)
    Ensures(cls[accessor_name] == generated_accessor())
    # A representative unrelated attribute keeps its exact bound identity: the
    # operation does not disturb a name other than the accessor name.
    Ensures(other_name() in cls)
    Ensures(cls[other_name()] == Old(cls[other_name()]))
    # Whole-namespace frame: the operation writes AT MOST the accessor name.
    # Membership changes for the accessor name only, and every OTHER name that
    # was present keeps its exact bound identity. (Explicit triggers keep the
    # quantifiers tractable for the verifier.)
    Ensures(Forall(int, lambda k: (Implies(k != accessor_name, (k in cls) == Old(k in cls)), [[k in cls]])))
    Ensures(Forall(int, lambda k: (Implies(k != accessor_name and k in cls and Old(k in cls), cls[k] == Old(cls[k])), [[cls[k]]])))
    # post-conditions-end
    # impl-start
    if accessor_name not in cls:
        cls[accessor_name] = generated_accessor()
    # impl-end
