"""Twin-artifact model for django__django-12125.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A type (a class object) used as a value is rendered into a fragment of
  importable source code that — when later evaluated — must recover the SAME
  class object. The class carries three pieces of text and one flag:

    * the dotted path of the module the class is defined in;
    * its SIMPLE innermost name (the leaf attribute name on whatever directly
      encloses it);
    * its FULLY-QUALIFIED name within the module — the dotted chain of every
      enclosing scope down to the leaf (for a class declared at module top
      level this equals the simple name; for a class nested inside another
      class it additionally carries the dotted prefix of every enclosing
      class);
    * a flag telling whether the defining module is the built-in namespace.

  When the class lives in the built-in namespace, the fragment is just its
  simple name and there is no accompanying import (built-in types are reachable
  without importing anything and are never declared inside an enclosing class).

  Otherwise the fragment is the module path, a dot, then the FULLY-QUALIFIED
  name — so that a class declared inside another class is rendered with the
  complete enclosing chain and the evaluated fragment reaches the very same
  nested attribute (NOT a non-existent top-level attribute that merely shares
  the leaf name). Reading the texts as Unicode code-point sequences:

        module ++ "." ++ qualified_name.

  The single accompanying import statement is then the import of that module,
  and ONLY that.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the pure sequence theory `PSeq[int]` carries the specification. The
two rendered forms are spelled out deeply as concatenations and validated ==
the real rendering output out-of-band by axiom_check.py (G-AX); nothing is
consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed @ContractOnly axiom. The whole rendering is the operation under
# change, so it is modelled DEEPLY in the `pure` region and the verified impl,
# and validated == the real rendering output by axiom_check.py / G-AX as
# A-references; nothing here is consumed as an axiom.)
# axioms-end


# pure-start
@Pure
def dotted_path(module: PSeq[int], qualified_name: PSeq[int]) -> PSeq[int]:
    """The non-built-in rendering, keyed by the FULLY-QUALIFIED name:
    module ++ '.' ++ qualified_name. '.' == U+002E == 46."""
    return module + PSeq(46) + qualified_name


@Pure
def import_line(module: PSeq[int]) -> PSeq[int]:
    """The one accompanying import statement: "import " followed by the module
    path. "import " == U+0069 6D 70 6F 72 74 20."""
    return PSeq(105, 109, 112, 111, 114, 116, 32) + module
# pure-end


def serialize_type(module: List[int], simple_name: List[int],
                   qualified_name: List[int], module_is_builtin: bool
                   ) -> Tuple[List[int], List[int]]:
    # pre-conditions-start
    # All three texts are read-only inputs (fractional permission). `simple_name`
    # is supplied as the leaf name; for a non-built-in class the rendering MUST
    # be keyed by `qualified_name`, NOT by `simple_name` (the two differ exactly
    # when the class is nested inside an enclosing class).
    Requires(Acc(list_pred(module), 1 / 2))
    Requires(Acc(list_pred(simple_name), 1 / 2))
    Requires(Acc(list_pred(qualified_name), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(module), 1 / 2))
    Ensures(Acc(list_pred(simple_name), 1 / 2))
    Ensures(Acc(list_pred(qualified_name), 1 / 2))
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    # Built-in namespace: the fragment is the simple name, with no import.
    Ensures(Implies(module_is_builtin,
                    ToSeq(Result()[0]) == ToSeq(simple_name)))
    Ensures(Implies(module_is_builtin, len(Result()[1]) == 0))
    # Otherwise: the fragment is module ++ '.' ++ FULLY-QUALIFIED name, grounded
    # in the `qualified_name` carrier (the complete enclosing chain), and the
    # accompanying import is exactly the import of the module.
    Ensures(Implies(not module_is_builtin,
                    ToSeq(Result()[0]) ==
                    dotted_path(ToSeq(module), ToSeq(qualified_name))))
    Ensures(Implies(not module_is_builtin,
                    ToSeq(Result()[1]) == import_line(ToSeq(module))))
    # post-conditions-end
    # impl-start
    if module_is_builtin:
        frag = []                            # type: List[int]
        frag = frag + simple_name            # the bare simple name
        imp = []                             # type: List[int]
        return (frag, imp)
    else:
        # frag = module + "." + qualified_name
        frag2 = []                           # type: List[int]
        frag2 = frag2 + module
        frag2 = frag2 + [46]                 # '.'
        frag2 = frag2 + qualified_name
        imp2 = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
        return (frag2, imp2)
    # impl-end
