"""Twin-artifact model for django__django-14580.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A serializer renders a Python type into a pair: a textual reference to that
  type, and the SET OF IMPORT DIRECTIVES that the generated code must include
  for that textual reference to resolve. A small built-in table of
  distinguished types is consulted first: each distinguished row pairs its
  rendered text with the set of import directives that rendered text needs. The
  serializer scans the table and, on the first row whose distinguished type is
  the value being rendered, returns that row's text together with the
  materialised set of that row's directives.

  The guarantee under specification: the returned import set is exactly the set
  of directives the matched row carries — never a smaller set. In particular,
  a distinguished type whose textual rendering is a dotted name rooted at an
  external namespace MUST carry, and the serializer MUST surface, the directive
  that brings that namespace into scope; otherwise the generated code
  referencing the rendered name would not resolve. A distinguished type whose
  rendering refers to no external namespace carries an empty directive set.

  Concretely the first distinguished type renders a base-class reference of the
  form `<namespace>.<Name>` rooted at an external namespace; serializing it must
  therefore yield exactly one directive — the statement that imports that
  namespace — so the rendered name is in scope wherever the serialized text is
  emitted.

Types are opaque, modelled by integer identity tags; textual renderings and
import directives are sequences of Unicode code points (`List[int]`, since
Nagini bans `str` indexing). The built-in table is constructed inside the
function exactly as the serializer constructs it, then scanned. No callee is
axiomatized: the table construction, the scan, and the materialisation of a
row's directive set are pure structural logic, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms: the table construction, the first-match scan, and the
# materialisation of a row's import-directive set are pure structural logic,
# modelled deeply. The set-literal construction the real serializer performs
# (`set(imports)`) is validated against its real Python semantics out-of-band
# by axiom_check.py (G-AX) as an A-reference, not consumed here.
# axioms-end


# pure-start
@Pure
def base_ref_tag() -> int:
    """Identity tag of the first distinguished type (the base-class reference
    rooted at an external namespace)."""
    return 1


@Pure
def other_ref_tag() -> int:
    """Identity tag of the second distinguished type (a rendering that refers
    to no external namespace and so requires no import)."""
    return 2


@Pure
def base_ref_text() -> PSeq[int]:
    """The textual rendering of the first distinguished type: the dotted
    base-class reference `models.Model`."""
    # 'models.Model'
    return PSeq(109, 111, 100, 101, 108, 115, 46, 77, 111, 100, 101, 108)


@Pure
def other_ref_text() -> PSeq[int]:
    """The textual rendering of the second distinguished type: `type(None)`."""
    # 'type(None)'
    return PSeq(116, 121, 112, 101, 40, 78, 111, 110, 101, 41)


@Pure
def base_ref_directive() -> PSeq[int]:
    """The single import directive the first distinguished type's rendering
    requires: the statement that brings the external namespace its dotted
    reference is rooted at into scope."""
    # 'from django.db import models'
    return PSeq(102, 114, 111, 109, 32, 100, 106, 97, 110, 103, 111, 46, 100,
                98, 32, 105, 109, 112, 111, 114, 116, 32, 109, 111, 100, 101,
                108, 115)


@Pure
def other_ref_directive_empty() -> PSeq[int]:
    """The (empty) import directive set carried by the second distinguished
    type: its rendering refers to no external namespace, so no import."""
    return PSeq(0).take(0)
# pure-end


class Serialized:
    """The serializer's output: a textual rendering plus the set of import
    directives that rendering requires (a directive set with at most one
    element here, carried as the directive's code points; empty list = no
    directive)."""

    def __init__(self) -> None:
        Requires(MustTerminate(2))
        Ensures(Acc(self.text) and Acc(list_pred(self.text)))  # type: ignore
        Ensures(len(self.text) == 0)  # type: ignore
        Ensures(Acc(self.imports) and Acc(list_pred(self.imports)))  # type: ignore
        Ensures(len(self.imports) == 0)  # type: ignore
        self.text = []  # type: List[int]
        self.imports = []  # type: List[int]


def serialize_type(value_tag: int) -> Serialized:
    # pre-conditions-start
    # The value being rendered takes the distinguished path: it is one of the
    # two built-in special types (non-special values take the unmodelled
    # module-based path).
    Requires(value_tag == base_ref_tag() or value_tag == other_ref_tag())
    # The two distinguished types are distinct.
    Requires(base_ref_tag() != other_ref_tag())
    # TERMINATION (total correctness): the table scan and the two
    # materialisation loops are bounded work, so serialize_type must actually
    # DELIVER the pair. Without this obligation Nagini checks only partial
    # correctness and a body that never reaches the return satisfies every
    # Ensures vacuously.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # The result is a fully-owned pair object.
    Ensures(Acc(Result().text) and Acc(list_pred(Result().text)))
    Ensures(Acc(Result().imports) and Acc(list_pred(Result().imports)))
    # Rendering the first distinguished type (the dotted base-class reference)
    # yields its text AND the single import directive that brings its namespace
    # into scope. This is the discriminating guarantee: the directive set is
    # non-empty and equals the namespace-import statement, so generated code
    # referencing the rendered name resolves.
    Ensures(Implies(value_tag == base_ref_tag(),
                    ToSeq(Result().text) == base_ref_text()
                    and ToSeq(Result().imports) == base_ref_directive()))
    # Rendering the second distinguished type yields its text and NO directive
    # (its rendering refers to no external namespace).
    Ensures(Implies(value_tag == other_ref_tag(),
                    ToSeq(Result().text) == other_ref_text()
                    and len(Result().imports) == 0))
    # post-conditions-end
    # impl-start
    # Build the table of distinguished types exactly as the serializer does:
    # row 0 is the base-class reference (text + EMPTY directive set), row 1 is
    # the no-import reference (text + empty directive set).
    tags = [base_ref_tag(), other_ref_tag()]  # type: List[int]
    texts = [base_ref_text(), other_ref_text()]  # type: List[PSeq[int]]
    directives = [other_ref_directive_empty(), other_ref_directive_empty()]  # type: List[PSeq[int]]

    result = Serialized()
    i = 0
    while i < len(tags):
        # invariants-start
        Invariant(Acc(list_pred(tags), 1 / 2))
        Invariant(Acc(list_pred(texts), 1 / 2))
        Invariant(Acc(list_pred(directives), 1 / 2))
        Invariant(len(tags) == 2 and len(texts) == 2 and len(directives) == 2)
        Invariant(tags[0] == base_ref_tag() and tags[1] == other_ref_tag())
        Invariant(texts[0] == base_ref_text() and texts[1] == other_ref_text())
        Invariant(len(directives[0]) == 0)
        Invariant(len(directives[1]) == 0)
        Invariant(0 <= i and i <= len(tags))
        Invariant(value_tag == base_ref_tag() or value_tag == other_ref_tag())
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                 tags[k] != value_tag))))
        Invariant(Acc(result.text) and Acc(list_pred(result.text)))
        Invariant(Acc(result.imports) and Acc(list_pred(result.imports)))
        # TERMINATION: at most len(tags) - i remaining passes (i grows by one
        # each pass and len(tags) is invariantly 2), so the bound strictly
        # decreases; the + 1 keeps it positive on the last pass. It does NOT
        # mention the inner counters j / m, which restart per outer pass.
        Invariant(MustTerminate(len(tags) - i + 1))
        # invariants-end
        if tags[i] == value_tag:
            t = texts[i]  # type: PSeq[int]
            d = directives[i]  # type: PSeq[int]
            text_out = []  # type: List[int]
            j = 0
            while j < len(t):
                # invariants-start
                Invariant(Acc(list_pred(texts), 1 / 2))
                Invariant(Acc(list_pred(directives), 1 / 2))
                Invariant(len(texts) == 2 and len(directives) == 2)
                Invariant(0 <= i and i < len(texts))
                Invariant(t is texts[i])
                Invariant(Acc(list_pred(text_out)))
                Invariant(0 <= j and j <= len(t))
                Invariant(len(text_out) == j)
                Invariant(ToSeq(text_out) == t.take(j))
                # TERMINATION: t is a snapshot of texts[i] fixed for this whole
                # inner run, so len(t) is constant; j grows by one per pass and
                # j <= len(t), so len(t) - j + 1 strictly decreases and stays
                # positive WITHIN the single outer pass that entered this loop.
                Invariant(MustTerminate(len(t) - j + 1))
                # invariants-end
                text_out.append(t[j])
                j = j + 1
            Assert(t.take(len(t)) == t)
            Assert(ToSeq(text_out) == t)
            d = directives[i]
            imports_out = []  # type: List[int]
            m = 0
            while m < len(d):
                # invariants-start
                Invariant(Acc(list_pred(directives), 1 / 2))
                Invariant(len(directives) == 2)
                Invariant(0 <= i and i < len(directives))
                Invariant(d is directives[i])
                Invariant(Acc(list_pred(imports_out)))
                Invariant(0 <= m and m <= len(d))
                Invariant(len(imports_out) == m)
                Invariant(ToSeq(imports_out) == d.take(m))
                # TERMINATION: d is a snapshot of directives[i] fixed for this
                # whole inner run, so len(d) is constant; m grows by one per
                # pass and m <= len(d), so len(d) - m + 1 strictly decreases and
                # stays positive WITHIN the single outer pass.
                Invariant(MustTerminate(len(d) - m + 1))
                # invariants-end
                imports_out.append(d[m])
                m = m + 1
            Assert(d.take(len(d)) == d)
            Assert(ToSeq(imports_out) == d)
            result.text = text_out
            result.imports = imports_out
            # The matched row's columns are exactly the result's contents.
            Assert(ToSeq(result.text) == texts[i])
            Assert(ToSeq(result.imports) == directives[i])
            return result
        i = i + 1
    # Unreachable: value_tag is one of the two table tags, so the scan above
    # matches one row.
    Assert(False)
    return result
    # impl-end
