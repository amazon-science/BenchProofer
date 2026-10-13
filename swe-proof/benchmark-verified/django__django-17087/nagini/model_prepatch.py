"""Twin-artifact model for django__django-17087.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A callable that is bound to a class object (a class-level method reached
  through that class) is rendered into a fragment of importable source code
  that — when later evaluated — must recover the SAME callable. The data the
  rendering reads is three pieces of text:

    * the dotted path of the module the owning class is defined in;
    * the callable's own attribute name on that class;
    * two names for the owning class itself —
        - its SIMPLE innermost name (the leaf attribute name on whatever
          directly encloses the class), and
        - its FULLY-QUALIFIED name within the module: the dotted chain of every
          enclosing scope down to the leaf. For a class declared at module top
          level this equals the simple name; for a class declared inside
          another class it additionally carries the dotted prefix of every
          enclosing class.

  The rendered fragment must address the callable through the COMPLETE
  enclosing chain of its owning class, so that a callable owned by a class
  nested inside another class is reached at its real position (NOT at a
  non-existent top-level attribute that merely shares the owning class's leaf
  name). Reading the texts as Unicode code-point sequences, the fragment is

        module ++ "." ++ class_fully_qualified_name ++ "." ++ method_name,

  keyed on the owning class's FULLY-QUALIFIED name. The single accompanying
  import statement is the import of that module, and ONLY that.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the pure sequence theory `PSeq[int]` carries the specification. The
rendered fragment and the import line are spelled out deeply as concatenations
and validated == the real rendering output out-of-band by axiom_check.py
(G-AX); nothing is consumed as an axiom.

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
def member_path(module: PSeq[int], class_qualified_name: PSeq[int],
                method_name: PSeq[int]) -> PSeq[int]:
    """The rendered fragment, keyed by the owning class's FULLY-QUALIFIED name:
    module ++ '.' ++ class_qualified_name ++ '.' ++ method_name.
    '.' == U+002E == 46."""
    return module + PSeq(46) + class_qualified_name + PSeq(46) + method_name


@Pure
def import_line(module: PSeq[int]) -> PSeq[int]:
    """The one accompanying import statement: "import " followed by the module
    path. "import " == U+0069 6D 70 6F 72 74 20."""
    return PSeq(105, 109, 112, 111, 114, 116, 32) + module
# pure-end


def render_class_member_reference(module: List[int],
                                  class_simple_name: List[int],
                                  class_qualified_name: List[int],
                                  method_name: List[int]
                                  ) -> Tuple[List[int], List[int]]:
    # pre-conditions-start
    # All four texts are read-only inputs (fractional permission). The owning
    # class is supplied with BOTH its simple leaf name and its fully-qualified
    # name; the fragment MUST be keyed by `class_qualified_name`, NOT by
    # `class_simple_name` (the two differ exactly when the owning class is
    # nested inside an enclosing class).
    Requires(Acc(list_pred(module), 1 / 2))
    Requires(Acc(list_pred(class_simple_name), 1 / 2))
    Requires(Acc(list_pred(class_qualified_name), 1 / 2))
    Requires(Acc(list_pred(method_name), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(module), 1 / 2))
    Ensures(Acc(list_pred(class_simple_name), 1 / 2))
    Ensures(Acc(list_pred(class_qualified_name), 1 / 2))
    Ensures(Acc(list_pred(method_name), 1 / 2))
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    # The fragment is module ++ '.' ++ FULLY-QUALIFIED class name ++ '.' ++
    # method name, grounded in the `class_qualified_name` carrier (the complete
    # enclosing chain). The accompanying import is exactly the import of the
    # module.
    Ensures(ToSeq(Result()[0]) ==
            member_path(ToSeq(module), ToSeq(class_qualified_name),
                        ToSeq(method_name)))
    Ensures(ToSeq(Result()[1]) == import_line(ToSeq(module)))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy): the fragment is keyed on the owning class's SIMPLE leaf
    # name instead of its fully-qualified name, so a class nested inside an
    # enclosing class is rendered at a non-existent top-level attribute.
    # frag = module + "." + class_simple_name + "." + method_name
    frag = []                                # type: List[int]
    frag = frag + module
    frag = frag + [46]                       # '.'
    frag = frag + class_simple_name
    frag = frag + [46]                       # '.'
    frag = frag + method_name
    imp = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
    return (frag, imp)
    # impl-end
