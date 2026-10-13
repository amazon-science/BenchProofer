# P2 adversarial audit — sphinx-doc__sphinx-9591

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -361,11 +361,10 @@
     # post-conditions-end
     # impl-start
     if present:
-        parsed = rendered_nodes(typ)  # type: AnnotationGroup
-        kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
-        texts = PSeq(sep_text()) + parsed.text  # type: PSeq[PSeq[int]]
-        bares = PSeq(True) + parsed.is_bare_text  # type: PSeq[bool]
-        holds = PSeq(False) + parsed.holds_one_bare_text  # type: PSeq[bool]
-        return AnnotationGroup(kinds, texts, bares, holds, True)
+        one_kind = PSeq(False)  # type: PSeq[bool]
+        one_text = PSeq(sep_text() + ToSeq(typ))  # type: PSeq[PSeq[int]]
+        one_bare = PSeq(True)  # type: PSeq[bool]
+        one_holds = PSeq(False)  # type: PSeq[bool]
+        return AnnotationGroup(one_kind, one_text, one_bare, one_holds, True)
     return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -364,8 +364,8 @@
         parsed = rendered_nodes(typ)  # type: AnnotationGroup
         kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
         texts = PSeq(sep_text()) + parsed.text  # type: PSeq[PSeq[int]]
-        bares = PSeq(True) + parsed.is_bare_text  # type: PSeq[bool]
-        holds = PSeq(False) + parsed.holds_one_bare_text  # type: PSeq[bool]
+        bares = PSeq(False) + parsed.is_bare_text  # type: PSeq[bool]
+        holds = PSeq(True) + parsed.holds_one_bare_text  # type: PSeq[bool]
         return AnnotationGroup(kinds, texts, bares, holds, True)
     return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -365,7 +365,7 @@
         kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
         texts = PSeq(sep_text()) + parsed.text  # type: PSeq[PSeq[int]]
         bares = PSeq(True) + parsed.is_bare_text  # type: PSeq[bool]
-        holds = PSeq(False) + parsed.holds_one_bare_text  # type: PSeq[bool]
+        holds = PSeq(False) + parsed.is_bare_text  # type: PSeq[bool]
         return AnnotationGroup(kinds, texts, bares, holds, True)
     return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -366,6 +366,6 @@
         texts = PSeq(sep_text()) + parsed.text  # type: PSeq[PSeq[int]]
         bares = PSeq(True) + parsed.is_bare_text  # type: PSeq[bool]
         holds = PSeq(False) + parsed.holds_one_bare_text  # type: PSeq[bool]
-        return AnnotationGroup(kinds, texts, bares, holds, True)
+        return AnnotationGroup(kinds, texts, bares, holds, False)
     return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -361,11 +361,10 @@
     # post-conditions-end
     # impl-start
     if present:
-        parsed = rendered_nodes(typ)  # type: AnnotationGroup
-        kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
-        texts = PSeq(sep_text()) + parsed.text  # type: PSeq[PSeq[int]]
-        bares = PSeq(True) + parsed.is_bare_text  # type: PSeq[bool]
-        holds = PSeq(False) + parsed.holds_one_bare_text  # type: PSeq[bool]
+        kinds = PSeq(False) + annotation_kinds(ToSeq(typ))  # type: PSeq[bool]
+        texts = PSeq(sep_text()) + annotation_texts(ToSeq(typ))  # type: PSeq[PSeq[int]]
+        bares = PSeq(True) + annotation_bare_text(ToSeq(typ))  # type: PSeq[bool]
+        holds = PSeq(False) + annotation_holds_one_bare_text(ToSeq(typ))  # type: PSeq[bool]
         return AnnotationGroup(kinds, texts, bares, holds, True)
     return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -361,7 +361,11 @@
     # post-conditions-end
     # impl-start
     if present:
-        parsed = rendered_nodes(typ)  # type: AnnotationGroup
+        try:
+            parsed = rendered_nodes(typ)  # type: AnnotationGroup
+        except AnnotationRejected:
+            return AnnotationGroup(no_kinds(), no_texts(), no_kinds(),
+                                   no_kinds(), False)
         kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
         texts = PSeq(sep_text()) + parsed.text  # type: PSeq[PSeq[int]]
         bares = PSeq(True) + parsed.is_bare_text  # type: PSeq[bool]
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -361,6 +361,8 @@
     # post-conditions-end
     # impl-start
     if present:
+        if not is_simple_name(ToSeq(typ)):
+            raise AnnotationRejected()
         parsed = rendered_nodes(typ)  # type: AnnotationGroup
         kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
         texts = PSeq(sep_text()) + parsed.text  # type: PSeq[PSeq[int]]
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -361,6 +361,13 @@
     # post-conditions-end
     # impl-start
     if present:
+        if is_simple_name(ToSeq(typ)):
+            fab_kinds = PSeq(False, True)  # type: PSeq[bool]
+            fab_texts = PSeq(sep_text(), ToSeq(typ))  # type: PSeq[PSeq[int]]
+            fab_bares = PSeq(True, False)  # type: PSeq[bool]
+            fab_holds = PSeq(False, True)  # type: PSeq[bool]
+            return AnnotationGroup(fab_kinds, fab_texts, fab_bares, fab_holds,
+                                   True)
         parsed = rendered_nodes(typ)  # type: AnnotationGroup
         kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
         texts = PSeq(sep_text()) + parsed.text  # type: PSeq[PSeq[int]]
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -362,10 +362,7 @@
     # impl-start
     if present:
         parsed = rendered_nodes(typ)  # type: AnnotationGroup
-        kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
-        texts = PSeq(sep_text()) + parsed.text  # type: PSeq[PSeq[int]]
-        bares = PSeq(True) + parsed.is_bare_text  # type: PSeq[bool]
-        holds = PSeq(False) + parsed.holds_one_bare_text  # type: PSeq[bool]
-        return AnnotationGroup(kinds, texts, bares, holds, True)
+        return AnnotationGroup(parsed.is_xref, parsed.text, parsed.is_bare_text,
+                               parsed.holds_one_bare_text, True)
     return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -361,11 +361,6 @@
     # post-conditions-end
     # impl-start
     if present:
-        parsed = rendered_nodes(typ)  # type: AnnotationGroup
-        kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
-        texts = PSeq(sep_text()) + parsed.text  # type: PSeq[PSeq[int]]
-        bares = PSeq(True) + parsed.is_bare_text  # type: PSeq[bool]
-        holds = PSeq(False) + parsed.holds_one_bare_text  # type: PSeq[bool]
-        return AnnotationGroup(kinds, texts, bares, holds, True)
+        return handle_property_annotation(present, typ)
     return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -367,5 +367,5 @@
         bares = PSeq(True) + parsed.is_bare_text  # type: PSeq[bool]
         holds = PSeq(False) + parsed.holds_one_bare_text  # type: PSeq[bool]
         return AnnotationGroup(kinds, texts, bares, holds, True)
-    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)
+    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), True)
     # impl-end
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -362,10 +362,10 @@
     # impl-start
     if present:
         parsed = rendered_nodes(typ)  # type: AnnotationGroup
-        kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
-        texts = PSeq(sep_text()) + parsed.text  # type: PSeq[PSeq[int]]
-        bares = PSeq(True) + parsed.is_bare_text  # type: PSeq[bool]
-        holds = PSeq(False) + parsed.holds_one_bare_text  # type: PSeq[bool]
+        kinds = parsed.is_xref + PSeq(False)  # type: PSeq[bool]
+        texts = parsed.text + PSeq(sep_text())  # type: PSeq[PSeq[int]]
+        bares = parsed.is_bare_text + PSeq(True)  # type: PSeq[bool]
+        holds = parsed.holds_one_bare_text + PSeq(False)  # type: PSeq[bool]
         return AnnotationGroup(kinds, texts, bares, holds, True)
     return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-9591.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a documented object carries a declared type annotation, the rendered
  annotation group placed after the object name is built so that a type name it
  mentions becomes a CROSS-REFERENCE node (a node that links to the documented
  type) rather than inert literal text. Concretely, the annotation group is the
  literal separator text ": " emitted as its own plain-text node, followed by
  the nodes produced by parsing the annotation string with the shared annotation
  parser. A declared type that is a simple type name parses to exactly one node,
  and that node is a cross-reference carrying the name, so such an annotation
  renders as the separator followed by a single cross-reference. An object that
  declares no type annotation contributes no annotation group at all.

  What KIND of node each child of the group is, is part of the rendered result
  and not merely which characters it carries. Three kinds of child occur: a BARE
  TEXT node, which is nothing but the characters it renders and carries no inline
  markup role of its own; a CROSS-REFERENCE; and any other marked-up inline node,
  rendered punctuation among them. The separator child is a BARE TEXT node.
  Rendered punctuation carrying those same two characters is a DIFFERENT child —
  it is equally not a cross-reference, yet a consumer that reads the group's
  children apart by kind, as consumers of a rendered signature do, sees a bare
  text child and a marked-up one as two different renderings — so emitting it in
  the separator's place does not satisfy the requirement above. The children
  after the separator are exactly the parser's own nodes, each at the kind the
  parser gave it: the operation splices them and re-kinds none of them, and
  passes each through unaltered — it does not rebuild one, re-wrap one, or edit
  what any of them holds inside.

  A marked-up child is not only a kind, it also has an INSIDE: the run or runs of
  inline content it holds and draws its rendered text from. That too is part of
  the rendered result. A cross-reference whose whole label is one bare text run
  is a different rendering from one whose label is itself further marked up or
  split across several runs, even when the two spell the same characters, because
  a consumer reading the label apart from the node that carries it finds one run
  in the first and not in the second. A simple type name's cross-reference holds
  exactly one bare text run, the name; the separator child holds no inner node at
  all, being itself the run it renders.

  The group is furthermore an ANNOTATION node — the node kind a rendered
  signature uses to hold a declared annotation — and exactly one such node is
  contributed when an annotation is declared. Which node holds the children is
  the emitting operation's own choice, not the parser's, so it is pinned here:
  putting the same children inside some other inline wrapper contributes a
  different thing to the signature and does not satisfy the requirement above.

  The shared annotation parser is PARTIAL: it ACCEPTS most annotation strings
  and REJECTS some, and on a rejected string it yields no node list at all.
  Delegating to it therefore means inheriting that: when the declared annotation
  is one the parser rejects, no annotation group is rendered and the rejection
  propagates to the caller rather than being absorbed into some substitute
  rendering. A simple type name is always accepted, so the cross-referencing
  guarantee above is unconditional on that class.

The annotation string is modelled as `List[int]` of Unicode code points (Nagini
bans `str` indexing). The rendered annotation group is modelled as the four
parallel sequences the group's children induce plus one flag on the group node
itself: `is_xref[k]` is True iff child `k` is a cross-reference, `is_bare_text[k]`
is True iff child `k` is a bare text node, `holds_one_bare_text[k]` is True iff
child `k` holds exactly one inner node and that node is a bare text node,
`text[k]` is child `k`'s rendered text as `PSeq[int]`, and `is_annotation_node`
says the children are held in an annotation node. The kind flags are independent
observations of one child — a marked-up inline node that is not a cross-reference
reads False in both, and a bare text child holds no inner node so it reads False
in the third — so the sequences together distinguish kinds and insides that the
texts alone do not. The shared annotation parser is an unchanged callee: the
strings it accepts are axiomatized as `accepted`, its rendered output as the four
sequences `annotation_kinds` / `annotation_bare_text` /
`annotation_holds_one_bare_text` / `annotation_texts`, and its value level as
`rendered_nodes`; all are properties of the real parser's node list validated
out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class AnnotationRejected(Exception):
    """The shared annotation parser REJECTS the declared annotation string: it
    yields no rendered node list for it, so no annotation group exists to
    produce. Modelled as a user-defined exception because a builtin one in an
    `Exsures` crashes the Nagini translator (mapping.md §2)."""

class AnnotationGroup:
    """The rendered annotation group: the sequences its children induce, and the
    kind of the node holding them.

    `is_xref[k]` is True iff child `k` is a cross-reference (a link to a
    documented object) and False for any other inline node (a bare text run,
    rendered punctuation). `is_bare_text[k]` is True iff child `k` is a BARE TEXT
    node — a child that is nothing but the characters it renders, carrying no
    inline markup role of its own — and False for every marked-up inline node,
    cross-references and rendered punctuation alike. `holds_one_bare_text[k]` is
    True iff child `k` holds exactly ONE inner node and that node is a bare text
    node: its whole rendered text comes from a single plain run held inside it.
    It is False for a bare text child (which holds no inner node, being itself
    the run it renders) and False for a marked-up child whose label is split
    across several runs or is itself further marked up. Reading the flags
    together therefore says which kind child `k` is and what it holds, and a
    child's text says nothing about either: a bare text run and a
    rendered-punctuation node may carry exactly the same characters and are still
    different children, as are two cross-references spelling the same name with
    different insides. `text[k]` is child `k`'s rendered text as a sequence of
    Unicode code points. The four sequences have equal length: one entry per
    child, in rendered order. `is_annotation_node` is True iff the children are
    held in an annotation node — the node kind a rendered signature uses for a
    declared annotation — and False when no such node is contributed at all.
    """

    def __init__(self, is_xref: PSeq[bool], text: PSeq[PSeq[int]],
                 is_bare_text: PSeq[bool], holds_one_bare_text: PSeq[bool],
                 is_annotation_node: bool) -> None:
        Requires(MustTerminate(1))
        self.is_xref = is_xref  # type: PSeq[bool]
        self.text = text  # type: PSeq[PSeq[int]]
        self.is_bare_text = is_bare_text  # type: PSeq[bool]
        self.holds_one_bare_text = holds_one_bare_text  # type: PSeq[bool]
        self.is_annotation_node = is_annotation_node  # type: bool
        Ensures(Acc(self.is_xref) and Acc(self.text) and Acc(self.is_bare_text)
                and Acc(self.holds_one_bare_text)
                and Acc(self.is_annotation_node))
        Ensures(self.is_xref == is_xref and self.text == text
                and self.is_bare_text == is_bare_text
                and self.holds_one_bare_text == holds_one_bare_text
                and self.is_annotation_node == is_annotation_node)

# pure-start
@Pure
def sep_text() -> PSeq[int]:
    # ": "  (the U+003A U+0020 separator emitted before a type annotation)
    return PSeq(58, 32)

@Pure
def no_kinds() -> PSeq[bool]:
    """The empty sequence of cross-reference flags: no children at all."""
    return PSeq(False).drop(1)

@Pure
def no_texts() -> PSeq[PSeq[int]]:
    """The empty sequence of child texts: no children at all."""
    return PSeq(sep_text()).drop(1)

@Pure
def is_name_start(c: int) -> bool:
    # A-Z, a-z, _ : the code points a simple type name may begin with.
    return (65 <= c and c <= 90) or (97 <= c and c <= 122) or c == 95

@Pure
def is_name_char(c: int) -> bool:
    # a name-start code point or a digit 0-9.
    return is_name_start(c) or (48 <= c and c <= 57)

@Pure
def is_simple_name(s: PSeq[int]) -> bool:
    """A simple type name: a non-empty run of name characters that does not
    begin with a digit (e.g. the documented class a property's type names)."""
    return len(s) > 0 and is_name_start(s[0]) and Forall(int, lambda k: (
        Implies(0 <= k and k < len(s), is_name_char(s[k])), [[s[k]]]))
# pure-end

# axioms-start
@Pure
@ContractOnly
def accepted(s: PSeq[int]) -> bool:
    """The shared annotation parser's DOMAIN: True iff it accepts `s` and so
    yields a rendered node list for it. The parser is PARTIAL — some strings it
    rejects outright, yielding no node list — so `annotation_kinds` /
    `annotation_texts` are defined only where this holds. Relied-on fact: a
    SIMPLE type name is always accepted. Unchanged callee; provenance +
    executable soundness in mapping.md / axiom_check.py.
    """
    Ensures(Implies(is_simple_name(s), Result()))

@Pure
@ContractOnly
def annotation_kinds(s: PSeq[int]) -> PSeq[bool]:
    """The shared annotation parser's rendered output on an ACCEPTED string,
    cross-reference flags: entry `k` is True iff the parser's `k`-th node is a
    cross-reference. An accepted string with no content yields no nodes.
    Relied-on fact: a SIMPLE type name renders to exactly one node and that node
    IS a cross-reference. Unchanged callee the rendering delegates to;
    provenance + executable soundness in mapping.md / axiom_check.py.
    """
    Requires(accepted(s))
    Ensures(Implies(is_simple_name(s), Result() == PSeq(True)))

@Pure
@ContractOnly
def annotation_bare_text(s: PSeq[int]) -> PSeq[bool]:
    """The same parser output's other kind flags: entry `k` is True iff the
    parser's `k`-th node is a BARE TEXT node rather than a marked-up inline one.
    One entry per node, so its length agrees with `annotation_kinds`. Relied-on
    fact: a SIMPLE type name's single node is NOT a bare text node — it is the
    cross-reference `annotation_kinds` reports, and a cross-reference carries an
    inline markup role, so it reads False here. That is the same single
    measurement `annotation_kinds`' simple-name fact rests on, read on the other
    flag, so this axiom asserts nothing about the parser beyond what
    axiom_check.py already observes of it: one node, and that node a
    cross-reference. Unchanged callee; provenance in mapping.md / axiom_check.py.
    """
    Requires(accepted(s))
    Ensures(len(Result()) == len(annotation_kinds(s)))
    Ensures(Implies(is_simple_name(s), Result() == PSeq(False)))

@Pure
@ContractOnly
def annotation_holds_one_bare_text(s: PSeq[int]) -> PSeq[bool]:
    """The same parser output read one level in: entry `k` is True iff the
    parser's `k`-th node holds exactly ONE inner node and that node is a bare
    text node — its whole rendered text comes from a single plain run inside it.
    One entry per node, so its length agrees with `annotation_kinds`. Relied-on
    fact: a SIMPLE type name's single node holds exactly one bare text run,
    namely the name itself, so it reads True here. That is the same node
    `annotation_kinds` / `annotation_texts` report on, read on what it holds
    rather than on its kind or its characters, and it is what makes a
    cross-reference whose label is one plain run distinguishable from one
    spelling the same name with a different inside. Unchanged callee; provenance
    in mapping.md / axiom_check.py.
    """
    Requires(accepted(s))
    Ensures(len(Result()) == len(annotation_kinds(s)))
    Ensures(Implies(is_simple_name(s), Result() == PSeq(True)))

@Pure
@ContractOnly
def annotation_texts(s: PSeq[int]) -> PSeq[PSeq[int]]:
    """The same parser output's rendered texts: entry `k` is the `k`-th node's
    text. One entry per node, so its length agrees with `annotation_kinds`.
    Relied-on fact: a SIMPLE type name's single node carries that name as its
    text. Unchanged callee; provenance in mapping.md / axiom_check.py.
    """
    Requires(accepted(s))
    Ensures(len(Result()) == len(annotation_kinds(s)))
    Ensures(Implies(is_simple_name(s), Result() == PSeq(s)))

@ContractOnly
def rendered_nodes(typ: List[int]) -> AnnotationGroup:
    """Runtime form of the shared annotation parser, at the value level: handed
    an ACCEPTED string it yields that string's rendered node list (the value of
    `annotation_kinds` / `annotation_bare_text` /
    `annotation_holds_one_bare_text` / `annotation_texts`); handed one
    it REJECTS it yields no
    node list and signals `AnnotationRejected` instead. Which strings it accepts
    is not something the caller decides — returning normally is itself the
    witness that the argument was accepted. The nodes it yields come out at the
    kinds it gave them and with the insides it gave them: those flags are read
    off that very node list, so a caller that splices them can pass them along
    unaltered but has no node of its own at those positions to substitute. Its
    result carries no `is_annotation_node` claim: a bare node list is not held in
    anything, and which node holds the spliced children is the CALLER's choice,
    which is why the operation below must pin it. Unchanged callee; provenance +
    executable soundness in mapping.md / axiom_check.py.
    """
    Requires(Acc(list_pred(typ), 1 / 2))
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(typ), 1 / 2))
    Ensures(Acc(Result().is_xref) and Acc(Result().text)
            and Acc(Result().is_bare_text)
            and Acc(Result().holds_one_bare_text)
            and Acc(Result().is_annotation_node))
    Ensures(accepted(ToSeq(typ)))
    Ensures(Result().is_xref == annotation_kinds(ToSeq(typ)))
    Ensures(Result().text == annotation_texts(ToSeq(typ)))
    Ensures(Result().is_bare_text == annotation_bare_text(ToSeq(typ)))
    Ensures(Result().holds_one_bare_text
            == annotation_holds_one_bare_text(ToSeq(typ)))
    Exsures(AnnotationRejected,
            Acc(list_pred(typ), 1 / 2) and not accepted(ToSeq(typ)))
# axioms-end

def handle_property_annotation(present: bool, typ: List[int]) -> AnnotationGroup:
    # `present` is True iff a non-empty type annotation was declared (the
    # operation's guard); `typ` carries that annotation's code points.
    # pre-conditions-start
    Requires(Acc(list_pred(typ), 1 / 2))
    Requires(Implies(present, len(typ) > 0))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(typ), 1 / 2))
    Ensures(Acc(Result().is_xref) and Acc(Result().text)
            and Acc(Result().is_bare_text)
            and Acc(Result().holds_one_bare_text)
            and Acc(Result().is_annotation_node))
    # One entry per rendered child.
    Ensures(len(Result().is_xref) == len(Result().text))
    Ensures(len(Result().is_bare_text) == len(Result().is_xref))
    Ensures(len(Result().holds_one_bare_text) == len(Result().is_xref))
    # No declared annotation -> no annotation group is produced.
    Ensures(Implies(not present, len(Result().is_xref) == 0))
    # A declared annotation contributes exactly one ANNOTATION node holding the
    # children below, and a declared-nothing contributes no such node. WHICH node
    # holds them is this operation's own choice, never the parser's, so putting
    # the same children inside any other inline wrapper is a different
    # contribution to the rendered signature and does not discharge this.
    Ensures(Result().is_annotation_node == present)
    # RETURNING A GROUP AT ALL means the annotation was one the shared parser
    # ACCEPTS: the rendering is delegated to that parser, so its domain is the
    # domain on which a group exists. (This clause also makes the ones below
    # well-defined, since `annotation_kinds` / `annotation_bare_text` /
    # `annotation_holds_one_bare_text` / `annotation_texts` are only defined on
    # an accepted string; it must therefore precede them.)
    Ensures(Implies(present, accepted(ToSeq(typ))))
    # A declared annotation produces, in order: the literal ": " separator as a
    # plain-text node, then the nodes the annotation parser renders.
    Ensures(Implies(present,
                    Result().is_xref == PSeq(False) + annotation_kinds(ToSeq(typ))))
    Ensures(Implies(present,
                    Result().text == PSeq(sep_text()) + annotation_texts(ToSeq(typ))))
    # The KIND of each of those children, not just its text: the separator is a
    # BARE TEXT child — carrying the separator's characters as rendered
    # punctuation, or as any other marked-up inline node, is a different child and
    # does not discharge this — and each child after it keeps the kind the
    # annotation parser gave it, the splice re-kinding none of them.
    Ensures(Implies(present,
                    Result().is_bare_text
                    == PSeq(True) + annotation_bare_text(ToSeq(typ))))
    # And what each child HOLDS, one level in: the separator holds no inner node,
    # being itself the run it renders, while every child after it keeps the inside
    # the annotation parser gave it — so rebuilding one of the parser's nodes with
    # the same kind and the same characters but a different inside (its label
    # split across several runs, or wrapped in further markup) is a different
    # child and does not discharge this either.
    Ensures(Implies(present,
                    Result().holds_one_bare_text
                    == PSeq(False) + annotation_holds_one_bare_text(ToSeq(typ))))
    # A declared SIMPLE type name is therefore rendered through a CROSS-REFERENCE
    # node, never as a single inert text run: the group is the separator, a bare
    # text child holding no inner node, followed by exactly one cross-reference
    # carrying the type name as one bare text run inside it.
    Ensures(Implies(present and is_simple_name(ToSeq(typ)),
                    Result().is_xref == PSeq(False, True)
                    and Result().text == PSeq(sep_text(), ToSeq(typ))
                    and Result().is_bare_text == PSeq(True, False)
                    and Result().holds_one_bare_text == PSeq(False, True)))
    # An annotation the shared parser REJECTS yields no annotation group: the
    # rejection propagates, unabsorbed, and the declared annotation is left
    # untouched. Together with the clause above this is exhaustive: on a declared
    # annotation the operation returns the delegated group where the parser
    # accepts and signals where it rejects, and nothing else on either side.
    Exsures(AnnotationRejected,
            Acc(list_pred(typ), 1 / 2)
            and present and not accepted(ToSeq(typ)))
    # post-conditions-end
    # impl-start
    if present:
        parsed = rendered_nodes(typ)  # type: AnnotationGroup
        holds = PSeq(False) + parsed.holds_one_bare_text  # type: PSeq[bool]
        bares = PSeq(True) + parsed.is_bare_text  # type: PSeq[bool]
        texts = PSeq(sep_text()) + parsed.text  # type: PSeq[PSeq[int]]
        kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
        grp = AnnotationGroup(kinds, texts, bares, holds, True)
        Assert(Implies(is_simple_name(ToSeq(typ)),
                       grp.is_xref == PSeq(False, True)
                       and grp.is_bare_text == PSeq(True, False)
                       and grp.holds_one_bare_text == PSeq(False, True)))
        Assert(grp.is_annotation_node)
        return grp
    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) adversarial audit of the Nagini bundle for sphinx-doc__sphinx-9591. VERDICT: SOUND (advisory). 12 same-spec wrong impls encoded and run; 11 REJECTED by the spec, 1 CANDIDATE (atk_8) whose faithful refined patch RESOLVES under the official harness in TWO independent refinements -- i.e. a correct echo of gold, not a verify=>correct break. Positive control verifies. Scratch dir: 

Every attack was built by copying the frozen model.py and editing ONLY the impl-start/impl-end region; `adversary same-spec` returned EXIT=0 (byte-identical spec signature) on all 12 plus the positive control, so axioms/@Pure/Requires/Ensures are untouched throughout.

### COMMANDS (from the repo root; per-attack N):
  python -m swebench_unified.adversary same-spec nagini sphinx-doc__sphinx-9591 $S/atk_N.py
  python -m swebench_unified.adversary weakness  nagini sphinx-doc__sphinx-9591 $S/atk_N.py
  bash scripts/nagini_verify.sh $S/pos_control.py
Run 3-at-a-time as concurrent background jobs (each Nagini check spawns JVM+Z3); this changed only the schedule, and every attack was fully verified.

### PER-ATTACK RESULTS (all `weakness`, exit code as shown):
| atk_1.py  | PRE-PATCH BUG re-encoded: one inert annotation child, text sep_text()+ToSeq(typ), built without consulting the parser. Impl region is byte-identical to the bundle's own model_prepatch.py impl (verified by diff). | EXIT=2 NOT-A-COUNTEREXAMPLE. Rejection reason read off the verifier: `atk_1.py:320:13: Postcondition ... Assertion Implies(present, accepted(ToSeq(typ))) might not hold` -- the domain clause, because it never delegates. G-DIFF holds. | | atk_2.py  | SEPARATOR AS RENDERED PUNCTUATION -- the counterexample a PRIOR pass named (verdict.md Role 1 recorded this as atk_6: verified, and its patch did NOT resolve).

Re-encoded against the CURRENT frozen spec: kinds/texts byte-identical to gold, only child 0's two kind axes flipped to desc_sig_punctuation's image (bares False, holds True). | EXIT=2 NOT-A-COUNTEREXAMPLE -- spec REJECTS. This is the headline finding: the recorded hole is genuinely CLOSED by the added is_bare_text / holds_one_bare_text axes, not merely re-described. | | atk_3.py  | REWRITE THE XREF'S INSIDE: tail inside-axis reported as the tail kind-axis (`holds = PSeq(False) + parsed.is_bare_text`) -- a cross-reference relabelled across two runs / re-wrapped.

Same kind, same text, different inside. | EXIT=2 NOT-A-COUNTEREXAMPLE -- spec REJECTS (C11). | | atk_4.py  | WRAPPER SWAP: exactly the gold children at gold kinds/insides, held in something that is NOT an annotation node (is_annotation_node=False).

Differs from gold in one bit. | EXIT=2 NOT-A-COUNTEREXAMPLE -- spec REJECTS (is_annotation_node == present). | | atk_5.py  | UNGROUNDED-ORACLE ECHO: never call rendered_nodes; read all four axiom sequences directly off annotation_kinds/`_texts`/`_bare_text`/`_holds_one_bare_text`, so acceptance is ASSERTED rather than witnessed. | EXIT=2 NOT-A-COUNTEREXAMPLE -- spec REJECTS; the Exsures/accepted arm genuinely forces value-level delegation. | | atk_6.py  | CONTROL-FLOW EFFECT / ABSORB THE REFUSAL: delegate, but catch AnnotationRejected and contribute nothing instead of propagating it. | EXIT=2 NOT-A-COUNTEREXAMPLE -- spec REJECTS (the Exsures arm is not optional). | | atk_7.py  | PARTIAL DOMAIN: render the simple-name class, raise AnnotationRejected for every other declared annotation (which the real parser accepts). | EXIT=2 NOT-A-COUNTEREXAMPLE -- spec REJECTS; C9 may only be taken where the parser genuinely refuses. | | atk_8.py  | PARSER BYPASS / FABRICATION on the simple-name class: when is_simple_name(ToSeq(typ)), never consult the shared parser -- hand-build PSeq(False,True)/PSeq(sep_text(),ToSeq(typ))/PSeq(True,False)/PSeq(False,True) from the argument; route other shapes through the axioms.

Aimed squarely at the A-leg (refinement.md A4's delegation claim). | EXIT=0 CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (22.6s). => resolve-checked, see below. | | atk_9.py  | BOUNDARY: separator child dropped entirely; the parser's nodes spliced straight onto the annotation node. | EXIT=2 NOT-A-COUNTEREXAMPLE -- spec REJECTS. | | atk_10.py | NON-TERMINATION: tail-recurse on the same arguments, so the rendering never happens. Probes whether method-level MustTerminate(6) really rejects a diverging rival. | EXIT=2 NOT-A-COUNTEREXAMPLE -- spec REJECTS. | | atk_11.py | EMPTY ANNOTATION NODE WHEN NOTHING IS DECLARED: gold present-arm, but the absent arm contributes an empty annotation node (flag True).

The other end of is_annotation_node == present from atk_4. | EXIT=2 NOT-A-COUNTEREXAMPLE -- spec REJECTS. | | atk_12.py | ORDER SWAP: parser children first, separator appended LAST. Every child's kind/inside/text is individually gold; only the rendered ORDER is wrong. | EXIT=2 NOT-A-COUNTEREXAMPLE -- spec REJECTS (positional concatenation). |

MANDATORY RESOLVE STEP FOR THE ONE CANDIDATE (atk_8). I materialized TWO distinct faithful refinements rather than one, because the carrier's silence about node ATTRIBUTES is the sharpest available attack on A4, and I wanted the harness -- not my judgment -- to settle it. Both were generated mechanically in a throwaway git worktree at base_commit 9ed054279 and confirmed with `git apply --check` before running:

(a) $S/patch_atk_8a.diff -- the natural refinement: `if re.fullmatch('[A-Za-z_][A-Za-z0-9_]*', typ): annotations = [type_to_xref(typ, self.env)] else: annotations = _parse_annotation(typ, self.env)`, then the gold `desc_annotation(typ, '', nodes.Text(': '), *annotations)`. (submitted in `patches`)

(b) $S/patch_atk_8b.diff -- the ADVERSARIAL pre-image: the same bypass, but the node is `pending_xref('', nodes.Text(typ))`, built WITHOUT the refdomain/reftype/reftarget resolution attributes. This lands on the identical carrier value on all FIVE observables the model records (is_xref True, text == name, is_bare_text False, holds_one_bare_text True, is_annotation_node True), since mapping.md records a child's KIND, TEXT and INSIDE and nothing about reftarget -- so it is a legitimate pre-image of gold's abstract value and a real probe of whether the spec's silence there is exploitable.

Both run through the official harness (swebench_unified.harness.run_resolve, driver $S/resolve.py): atk_8a: {"completed": true, "resolved": TRUE, "attempts": 2, "flaky": true}  FAIL_TO_PASS 1/1 success, PASS_TO_PASS 44/44 success, 0 failures atk_8b: {"completed": true, "resolved": TRUE, "attempts": 1, "flaky": false} FAIL_TO_PASS 1/1 success, PASS_TO_PASS 44/44 success, 0 failures GOLD CONTROL, same host/session: {"completed": true, "resolved": TRUE, "attempts": 2, "flaky": true} So atk_8 is a CORRECT ECHO on both refinements, not a verify=>correct break. Note the flakiness bookkeeping deliberately: 8a and the GOLD control were each `flaky: true` (resolved on attempt 2/3) while 8b resolved first try -- the host was running many concurrent resolves.

WHY atk_8 IS NOT A DEFECT (and why it is still worth recording). Its bypass is only reachable where accepted()'s strong arm plus the four simple-name arms already pin the answer to exactly what the real parser produces -- and G-AX measures those arms TRUE of the real `_parse_annotation` (never refused a simple name over 23 names + 3392 exhaustive length-1/2 ASCII identifiers + 5000 fuzz strings, both config settings). So on that class the fabricated group and the delegated group are the same rendering, and the harness confirms it twice over. The residual observation, which is a documentation point rather than a hole: the spec pins the RESULT on the simple-name class but does not pin DELEGATION itself there, so refinement.md A4's prose ("the caller has no node of its own at those positions") is stronger than what the contracts force on that one class. Since the axiom arm it leans on is measurably true of the real callee, no verifying impl can diverge from gold there. This matches the collateral finding already recorded in verdict.md, and my harness runs now settle the question it left open ("likely still resolves") as a measured RESOLVES on two refinements.

A-LEG / refinement.md AUDIT (my assigned focus; R and I legs are G-CONF's).
 * Leg inventory: A1 R, A2 I, A3 R, A4 A-consumed, A5 R, A6 R. No kind-3 (unexpressible-changed-op) leg, and no A-reference deep model in this bundle -- consistent with SS.B's claim. Every axiom is genuinely consumed: I confirmed by construction that removing delegation (atk_5) breaks the domain clause and that each of the four sequence arms is separately load-bearing (atk_2 breaks only the bare-text axis, atk_3 only the holds-one axis, atk_12 only the order, atk_4/atk_11 only the wrapper flag). No dead axiom.
 * A4 correspondence to the real callee CHECKED against sphinx/domains/python.py:110 at base_commit, not just against the prose. `_parse_annotation`'s post-loop replaces each non-blank nodes.Text with type_to_xref(...) -> pending_xref, leaving desc_sig_punctuation alone; so for a simple name (ast.Name -> [nodes.Text(id)]) the list is exactly one pending_xref whose sole child is nodes.Text(name). That is precisely annotation_kinds==PSeq(True) / annotation_bare_text==PSeq(False) / annotation_holds_one_bare_text==PSeq(True) / annotation_texts==PSeq(s). Width-only claims outside that class are right, since compound shapes emit punctuation nodes the loop skips. axiom_check.py's observation functions match mapping.md's binding table symbol-for-symbol (is_xref = isinstance pending_xref; is_bare_text = isinstance nodes.Text; holds_one = len(children)==1 and isinstance(children[0], nodes.Text)), and it asserts the non-degeneracy (no node True on both axes) rather than assuming it.
 * The config dependency is disclosed correctly and is not a hidden hole: under python_use_unqualified_type_names=True the xref's label is two pending_xref_condition children, so texts/holds-one would read differently -- but mapping.md S3.1 records the default as binding, axiom_check sweeps BOTH settings, and I confirmed the ONLY repo test exercising a property `:type:` is the F2P test_pyproperty (default config, `:type: str`); no testroot declares a py:property with a type, and the two use_unqualified P2P tests cover py:class/py:function params instead. Both those P2P tests passed on all three resolve runs.
 * A3's injectivity claim (the one the prior revision got wrong) now holds as stated: nodes.Text(': ') -> (False, True, False) vs desc_sig_punctuation('', ': ') -> (False, False, True) are distinct carrier values, and atk_2 -- the exact rendering that previously slipped through -- is now rejected. A5's wrapper leg is independently pinned (atk_4/atk_11 both rejected), which matters because `_parse_annotation` returns a bare List[Node] and so cannot constrain the wrapper.

**FLOOR:** 12 admissible same-spec attacks (>=5 required), prepatch bug reproduced as atk_1 with its impl region byte-identical to model_prepatch.py, positive control $S/pos_control.py (structurally different correct impl: locals built in reverse order plus framing Asserts) VERIFIES in 19.7s -- so the spec is not vacuously strong. No verifier timeouts, no crashes, no incomplete resolve runs; every attack reached a real verdict and the one candidate reached a real harness verdict. Nothing INCONCLUSIVE.

**Cleanup:** the temporary git worktree used to generate/validate the diffs was removed and pruned; the source repo tree is untouched (no stash, no checkout of the shared tree).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 12 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-9591.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a documented object carries a declared type annotation, the rendered
  annotation group placed after the object name is built so that a type name it
  mentions becomes a CROSS-REFERENCE node (a node that links to the documented
  type) rather than inert literal text. Concretely, the annotation group is the
  literal separator text ": " emitted as its own plain-text node, followed by
  the nodes produced by parsing the annotation string with the shared annotation
  parser. A declared type that is a simple type name parses to exactly one node,
  and that node is a cross-reference carrying the name, so such an annotation
  renders as the separator followed by a single cross-reference. An object that
  declares no type annotation contributes no annotation group at all.

  What KIND of node each child of the group is, is part of the rendered result
  and not merely which characters it carries. Three kinds of child occur: a BARE
  TEXT node, which is nothing but the characters it renders and carries no inline
  markup role of its own; a CROSS-REFERENCE; and any other marked-up inline node,
  rendered punctuation among them. The separator child is a BARE TEXT node.
  Rendered punctuation carrying those same two characters is a DIFFERENT child —
  it is equally not a cross-reference, yet a consumer that reads the group's
  children apart by kind, as consumers of a rendered signature do, sees a bare
  text child and a marked-up one as two different renderings — so emitting it in
  the separator's place does not satisfy the requirement above. The children
  after the separator are exactly the parser's own nodes, each at the kind the
  parser gave it: the operation splices them and re-kinds none of them, and
  passes each through unaltered — it does not rebuild one, re-wrap one, or edit
  what any of them holds inside.

  A marked-up child is not only a kind, it also has an INSIDE: the run or runs of
  inline content it holds and draws its rendered text from. That too is part of
  the rendered result. A cross-reference whose whole label is one bare text run
  is a different rendering from one whose label is itself further marked up or
  split across several runs, even when the two spell the same characters, because
  a consumer reading the label apart from the node that carries it finds one run
  in the first and not in the second. A simple type name's cross-reference holds
  exactly one bare text run, the name; the separator child holds no inner node at
  all, being itself the run it renders.

  The group is furthermore an ANNOTATION node — the node kind a rendered
  signature uses to hold a declared annotation — and exactly one such node is
  contributed when an annotation is declared. Which node holds the children is
  the emitting operation's own choice, not the parser's, so it is pinned here:
  putting the same children inside some other inline wrapper contributes a
  different thing to the signature and does not satisfy the requirement above.

  The shared annotation parser is PARTIAL: it ACCEPTS most annotation strings
  and REJECTS some, and on a rejected string it yields no node list at all.
  Delegating to it therefore means inheriting that: when the declared annotation
  is one the parser rejects, no annotation group is rendered and the rejection
  propagates to the caller rather than being absorbed into some substitute
  rendering. A simple type name is always accepted, so the cross-referencing
  guarantee above is unconditional on that class.

The annotation string is modelled as `List[int]` of Unicode code points (Nagini
bans `str` indexing). The rendered annotation group is modelled as the four
parallel sequences the group's children induce plus one flag on the group node
itself: `is_xref[k]` is True iff child `k` is a cross-reference, `is_bare_text[k]`
is True iff child `k` is a bare text node, `holds_one_bare_text[k]` is True iff
child `k` holds exactly one inner node and that node is a bare text node,
`text[k]` is child `k`'s rendered text as `PSeq[int]`, and `is_annotation_node`
says the children are held in an annotation node. The kind flags are independent
observations of one child — a marked-up inline node that is not a cross-reference
reads False in both, and a bare text child holds no inner node so it reads False
in the third — so the sequences together distinguish kinds and insides that the
texts alone do not. The shared annotation parser is an unchanged callee: the
strings it accepts are axiomatized as `accepted`, its rendered output as the four
sequences `annotation_kinds` / `annotation_bare_text` /
`annotation_holds_one_bare_text` / `annotation_texts`, and its value level as
`rendered_nodes`; all are properties of the real parser's node list validated
out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class AnnotationRejected(Exception):
    """The shared annotation parser REJECTS the declared annotation string: it
    yields no rendered node list for it, so no annotation group exists to
    produce. Modelled as a user-defined exception because a builtin one in an
    `Exsures` crashes the Nagini translator (mapping.md §2)."""

class AnnotationGroup:
    """The rendered annotation group: the sequences its children induce, and the
    kind of the node holding them.

    `is_xref[k]` is True iff child `k` is a cross-reference (a link to a
    documented object) and False for any other inline node (a bare text run,
    rendered punctuation). `is_bare_text[k]` is True iff child `k` is a BARE TEXT
    node — a child that is nothing but the characters it renders, carrying no
    inline markup role of its own — and False for every marked-up inline node,
    cross-references and rendered punctuation alike. `holds_one_bare_text[k]` is
    True iff child `k` holds exactly ONE inner node and that node is a bare text
    node: its whole rendered text comes from a single plain run held inside it.
    It is False for a bare text child (which holds no inner node, being itself
    the run it renders) and False for a marked-up child whose label is split
    across several runs or is itself further marked up. Reading the flags
    together therefore says which kind child `k` is and what it holds, and a
    child's text says nothing about either: a bare text run and a
    rendered-punctuation node may carry exactly the same characters and are still
    different children, as are two cross-references spelling the same name with
    different insides. `text[k]` is child `k`'s rendered text as a sequence of
    Unicode code points. The four sequences have equal length: one entry per
    child, in rendered order. `is_annotation_node` is True iff the children are
    held in an annotation node — the node kind a rendered signature uses for a
    declared annotation — and False when no such node is contributed at all.
    """

    def __init__(self, is_xref: PSeq[bool], text: PSeq[PSeq[int]],
                 is_bare_text: PSeq[bool], holds_one_bare_text: PSeq[bool],
                 is_annotation_node: bool) -> None:
        Requires(MustTerminate(1))
        self.is_xref = is_xref  # type: PSeq[bool]
        self.text = text  # type: PSeq[PSeq[int]]
        self.is_bare_text = is_bare_text  # type: PSeq[bool]
        self.holds_one_bare_text = holds_one_bare_text  # type: PSeq[bool]
        self.is_annotation_node = is_annotation_node  # type: bool
        Ensures(Acc(self.is_xref) and Acc(self.text) and Acc(self.is_bare_text)
                and Acc(self.holds_one_bare_text)
                and Acc(self.is_annotation_node))
        Ensures(self.is_xref == is_xref and self.text == text
                and self.is_bare_text == is_bare_text
                and self.holds_one_bare_text == holds_one_bare_text
                and self.is_annotation_node == is_annotation_node)

# pure-start
@Pure
def sep_text() -> PSeq[int]:
    # ": "  (the U+003A U+0020 separator emitted before a type annotation)
    return PSeq(58, 32)

@Pure
def no_kinds() -> PSeq[bool]:
    """The empty sequence of cross-reference flags: no children at all."""
    return PSeq(False).drop(1)

@Pure
def no_texts() -> PSeq[PSeq[int]]:
    """The empty sequence of child texts: no children at all."""
    return PSeq(sep_text()).drop(1)

@Pure
def is_name_start(c: int) -> bool:
    # A-Z, a-z, _ : the code points a simple type name may begin with.
    return (65 <= c and c <= 90) or (97 <= c and c <= 122) or c == 95

@Pure
def is_name_char(c: int) -> bool:
    # a name-start code point or a digit 0-9.
    return is_name_start(c) or (48 <= c and c <= 57)

@Pure
def is_simple_name(s: PSeq[int]) -> bool:
    """A simple type name: a non-empty run of name characters that does not
    begin with a digit (e.g. the documented class a property's type names)."""
    return len(s) > 0 and is_name_start(s[0]) and Forall(int, lambda k: (
        Implies(0 <= k and k < len(s), is_name_char(s[k])), [[s[k]]]))
# pure-end

# axioms-start
@Pure
@ContractOnly
def accepted(s: PSeq[int]) -> bool:
    """The shared annotation parser's DOMAIN: True iff it accepts `s` and so
    yields a rendered node list for it. The parser is PARTIAL — some strings it
    rejects outright, yielding no node list — so `annotation_kinds` /
    `annotation_texts` are defined only where this holds. Relied-on fact: a
    SIMPLE type name is always accepted. Unchanged callee; provenance +
    executable soundness in mapping.md / axiom_check.py.
    """
    Ensures(Implies(is_simple_name(s), Result()))

@Pure
@ContractOnly
def annotation_kinds(s: PSeq[int]) -> PSeq[bool]:
    """The shared annotation parser's rendered output on an ACCEPTED string,
    cross-reference flags: entry `k` is True iff the parser's `k`-th node is a
    cross-reference. An accepted string with no content yields no nodes.
    Relied-on fact: a SIMPLE type name renders to exactly one node and that node
    IS a cross-reference. Unchanged callee the rendering delegates to;
    provenance + executable soundness in mapping.md / axiom_check.py.
    """
    Requires(accepted(s))
    Ensures(Implies(is_simple_name(s), Result() == PSeq(True)))

@Pure
@ContractOnly
def annotation_bare_text(s: PSeq[int]) -> PSeq[bool]:
    """The same parser output's other kind flags: entry `k` is True iff the
    parser's `k`-th node is a BARE TEXT node rather than a marked-up inline one.
    One entry per node, so its length agrees with `annotation_kinds`. Relied-on
    fact: a SIMPLE type name's single node is NOT a bare text node — it is the
    cross-reference `annotation_kinds` reports, and a cross-reference carries an
    inline markup role, so it reads False here. That is the same single
    measurement `annotation_kinds`' simple-name fact rests on, read on the other
    flag, so this axiom asserts nothing about the parser beyond what
    axiom_check.py already observes of it: one node, and that node a
    cross-reference. Unchanged callee; provenance in mapping.md / axiom_check.py.
    """
    Requires(accepted(s))
    Ensures(len(Result()) == len(annotation_kinds(s)))
    Ensures(Implies(is_simple_name(s), Result() == PSeq(False)))

@Pure
@ContractOnly
def annotation_holds_one_bare_text(s: PSeq[int]) -> PSeq[bool]:
    """The same parser output read one level in: entry `k` is True iff the
    parser's `k`-th node holds exactly ONE inner node and that node is a bare
    text node — its whole rendered text comes from a single plain run inside it.
    One entry per node, so its length agrees with `annotation_kinds`. Relied-on
    fact: a SIMPLE type name's single node holds exactly one bare text run,
    namely the name itself, so it reads True here. That is the same node
    `annotation_kinds` / `annotation_texts` report on, read on what it holds
    rather than on its kind or its characters, and it is what makes a
    cross-reference whose label is one plain run distinguishable from one
    spelling the same name with a different inside. Unchanged callee; provenance
    in mapping.md / axiom_check.py.
    """
    Requires(accepted(s))
    Ensures(len(Result()) == len(annotation_kinds(s)))
    Ensures(Implies(is_simple_name(s), Result() == PSeq(True)))

@Pure
@ContractOnly
def annotation_texts(s: PSeq[int]) -> PSeq[PSeq[int]]:
    """The same parser output's rendered texts: entry `k` is the `k`-th node's
    text. One entry per node, so its length agrees with `annotation_kinds`.
    Relied-on fact: a SIMPLE type name's single node carries that name as its
    text. Unchanged callee; provenance in mapping.md / axiom_check.py.
    """
    Requires(accepted(s))
    Ensures(len(Result()) == len(annotation_kinds(s)))
    Ensures(Implies(is_simple_name(s), Result() == PSeq(s)))

@ContractOnly
def rendered_nodes(typ: List[int]) -> AnnotationGroup:
    """Runtime form of the shared annotation parser, at the value level: handed
    an ACCEPTED string it yields that string's rendered node list (the value of
    `annotation_kinds` / `annotation_bare_text` /
    `annotation_holds_one_bare_text` / `annotation_texts`); handed one
    it REJECTS it yields no
    node list and signals `AnnotationRejected` instead. Which strings it accepts
    is not something the caller decides — returning normally is itself the
    witness that the argument was accepted. The nodes it yields come out at the
    kinds it gave them and with the insides it gave them: those flags are read
    off that very node list, so a caller that splices them can pass them along
    unaltered but has no node of its own at those positions to substitute. Its
    result carries no `is_annotation_node` claim: a bare node list is not held in
    anything, and which node holds the spliced children is the CALLER's choice,
    which is why the operation below must pin it. Unchanged callee; provenance +
    executable soundness in mapping.md / axiom_check.py.
    """
    Requires(Acc(list_pred(typ), 1 / 2))
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(typ), 1 / 2))
    Ensures(Acc(Result().is_xref) and Acc(Result().text)
            and Acc(Result().is_bare_text)
            and Acc(Result().holds_one_bare_text)
            and Acc(Result().is_annotation_node))
    Ensures(accepted(ToSeq(typ)))
    Ensures(Result().is_xref == annotation_kinds(ToSeq(typ)))
    Ensures(Result().text == annotation_texts(ToSeq(typ)))
    Ensures(Result().is_bare_text == annotation_bare_text(ToSeq(typ)))
    Ensures(Result().holds_one_bare_text
            == annotation_holds_one_bare_text(ToSeq(typ)))
    Exsures(AnnotationRejected,
            Acc(list_pred(typ), 1 / 2) and not accepted(ToSeq(typ)))
# axioms-end

def handle_property_annotation(present: bool, typ: List[int]) -> AnnotationGroup:
    # `present` is True iff a non-empty type annotation was declared (the
    # operation's guard); `typ` carries that annotation's code points.
    # pre-conditions-start
    Requires(Acc(list_pred(typ), 1 / 2))
    Requires(Implies(present, len(typ) > 0))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(typ), 1 / 2))
    Ensures(Acc(Result().is_xref) and Acc(Result().text)
            and Acc(Result().is_bare_text)
            and Acc(Result().holds_one_bare_text)
            and Acc(Result().is_annotation_node))
    # One entry per rendered child.
    Ensures(len(Result().is_xref) == len(Result().text))
    Ensures(len(Result().is_bare_text) == len(Result().is_xref))
    Ensures(len(Result().holds_one_bare_text) == len(Result().is_xref))
    # No declared annotation -> no annotation group is produced.
    Ensures(Implies(not present, len(Result().is_xref) == 0))
    # A declared annotation contributes exactly one ANNOTATION node holding the
    # children below, and a declared-nothing contributes no such node. WHICH node
    # holds them is this operation's own choice, never the parser's, so putting
    # the same children inside any other inline wrapper is a different
    # contribution to the rendered signature and does not discharge this.
    Ensures(Result().is_annotation_node == present)
    # RETURNING A GROUP AT ALL means the annotation was one the shared parser
    # ACCEPTS: the rendering is delegated to that parser, so its domain is the
    # domain on which a group exists. (This clause also makes the ones below
    # well-defined, since `annotation_kinds` / `annotation_bare_text` /
    # `annotation_holds_one_bare_text` / `annotation_texts` are only defined on
    # an accepted string; it must therefore precede them.)
    Ensures(Implies(present, accepted(ToSeq(typ))))
    # A declared annotation produces, in order: the literal ": " separator as a
    # plain-text node, then the nodes the annotation parser renders.
    Ensures(Implies(present,
                    Result().is_xref == PSeq(False) + annotation_kinds(ToSeq(typ))))
    Ensures(Implies(present,
                    Result().text == PSeq(sep_text()) + annotation_texts(ToSeq(typ))))
    # The KIND of each of those children, not just its text: the separator is a
    # BARE TEXT child — carrying the separator's characters as rendered
    # punctuation, or as any other marked-up inline node, is a different child and
    # does not discharge this — and each child after it keeps the kind the
    # annotation parser gave it, the splice re-kinding none of them.
    Ensures(Implies(present,
                    Result().is_bare_text
                    == PSeq(True) + annotation_bare_text(ToSeq(typ))))
    # And what each child HOLDS, one level in: the separator holds no inner node,
    # being itself the run it renders, while every child after it keeps the inside
    # the annotation parser gave it — so rebuilding one of the parser's nodes with
    # the same kind and the same characters but a different inside (its label
    # split across several runs, or wrapped in further markup) is a different
    # child and does not discharge this either.
    Ensures(Implies(present,
                    Result().holds_one_bare_text
                    == PSeq(False) + annotation_holds_one_bare_text(ToSeq(typ))))
    # A declared SIMPLE type name is therefore rendered through a CROSS-REFERENCE
    # node, never as a single inert text run: the group is the separator, a bare
    # text child holding no inner node, followed by exactly one cross-reference
    # carrying the type name as one bare text run inside it.
    Ensures(Implies(present and is_simple_name(ToSeq(typ)),
                    Result().is_xref == PSeq(False, True)
                    and Result().text == PSeq(sep_text(), ToSeq(typ))
                    and Result().is_bare_text == PSeq(True, False)
                    and Result().holds_one_bare_text == PSeq(False, True)))
    # An annotation the shared parser REJECTS yields no annotation group: the
    # rejection propagates, unabsorbed, and the declared annotation is left
    # untouched. Together with the clause above this is exhaustive: on a declared
    # annotation the operation returns the delegated group where the parser
    # accepts and signals where it rejects, and nothing else on either side.
    Exsures(AnnotationRejected,
            Acc(list_pred(typ), 1 / 2)
            and present and not accepted(ToSeq(typ)))
    # post-conditions-end
    # impl-start
    if present:
        parsed = rendered_nodes(typ)  # type: AnnotationGroup
        holds = PSeq(False) + parsed.holds_one_bare_text  # type: PSeq[bool]
        bares = PSeq(True) + parsed.is_bare_text  # type: PSeq[bool]
        texts = PSeq(sep_text()) + parsed.text  # type: PSeq[PSeq[int]]
        kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
        grp = AnnotationGroup(kinds, texts, bares, holds, True)
        Assert(Implies(is_simple_name(ToSeq(typ)),
                       grp.is_xref == PSeq(False, True)
                       and grp.is_bare_text == PSeq(True, False)
                       and grp.holds_one_bare_text == PSeq(False, True)))
        Assert(grp.is_annotation_node)
        return grp
    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) adversarial audit of the Nagini bundle for sphinx-doc__sphinx-9591. VERDICT: SOUND (advisory). 12 same-spec wrong impls encoded and run; 11 REJECTED by the spec, 1 CANDIDATE (atk_8) whose faithful refined patch RESOLVES under the official harness in TWO independent refinements -- i.e. a correct echo of gold, not a verify=>correct break. Positive control verifies. Scratch dir: 

Every attack was built by copying the frozen model.py and editing ONLY the impl-start/impl-end region; `adversary same-spec` returned EXIT=0 (byte-identical spec signature) on all 12 plus the positive control, so axioms/@Pure/Requires/Ensures are untouched throughout.

### COMMANDS (from the repo root; per-attack N):
  python -m swebench_unified.adversary same-spec nagini sphinx-doc__sphinx-9591 $S/atk_N.py
  python -m swebench_unified.adversary weakness  nagini sphinx-doc__sphinx-9591 $S/atk_N.py
  bash scripts/nagini_verify.sh $S/pos_control.py
Run 3-at-a-time as concurrent background jobs (each Nagini check spawns JVM+Z3); this changed only the schedule, and every attack was fully verified.

### PER-ATTACK RESULTS (all `weakness`, exit code as shown):
| atk_1.py  | PRE-PATCH BUG re-encoded: one inert annotation child, text sep_text()+ToSeq(typ), built without consulting the parser. Impl region is byte-identical to the bundle's own model_prepatch.py impl (verified by diff). | EXIT=2 NOT-A-COUNTEREXAMPLE. Rejection reason read off the verifier: `atk_1.py:320:13: Postcondition ... Assertion Implies(present, accepted(ToSeq(typ))) might not hold` -- the domain clause, because it never delegates. G-DIFF holds. | | atk_2.py  | SEPARATOR AS RENDERED PUNCTUATION -- the counterexample a PRIOR pass named (verdict.md Role 1 recorded this as atk_6: verified, and its patch did NOT resolve).

Re-encoded against the CURRENT frozen spec: kinds/texts byte-identical to gold, only child 0's two kind axes flipped to desc_sig_punctuation's image (bares False, holds True). | EXIT=2 NOT-A-COUNTEREXAMPLE -- spec REJECTS. This is the headline finding: the recorded hole is genuinely CLOSED by the added is_bare_text / holds_one_bare_text axes, not merely re-described. | | atk_3.py  | REWRITE THE XREF'S INSIDE: tail inside-axis reported as the tail kind-axis (`holds = PSeq(False) + parsed.is_bare_text`) -- a cross-reference relabelled across two runs / re-wrapped.

Same kind, same text, different inside. | EXIT=2 NOT-A-COUNTEREXAMPLE -- spec REJECTS (C11). | | atk_4.py  | WRAPPER SWAP: exactly the gold children at gold kinds/insides, held in something that is NOT an annotation node (is_annotation_node=False).

Differs from gold in one bit. | EXIT=2 NOT-A-COUNTEREXAMPLE -- spec REJECTS (is_annotation_node == present). | | atk_5.py  | UNGROUNDED-ORACLE ECHO: never call rendered_nodes; read all four axiom sequences directly off annotation_kinds/`_texts`/`_bare_text`/`_holds_one_bare_text`, so acceptance is ASSERTED rather than witnessed. | EXIT=2 NOT-A-COUNTEREXAMPLE -- spec REJECTS; the Exsures/accepted arm genuinely forces value-level delegation. | | atk_6.py  | CONTROL-FLOW EFFECT / ABSORB THE REFUSAL: delegate, but catch AnnotationRejected and contribute nothing instead of propagating it. | EXIT=2 NOT-A-COUNTEREXAMPLE -- spec REJECTS (the Exsures arm is not optional). | | atk_7.py  | PARTIAL DOMAIN: render the simple-name class, raise AnnotationRejected for every other declared annotation (which the real parser accepts). | EXIT=2 NOT-A-COUNTEREXAMPLE -- spec REJECTS; C9 may only be taken where the parser genuinely refuses. | | atk_8.py  | PARSER BYPASS / FABRICATION on the simple-name class: when is_simple_name(ToSeq(typ)), never consult the shared parser -- hand-build PSeq(False,True)/PSeq(sep_text(),ToSeq(typ))/PSeq(True,False)/PSeq(False,True) from the argument; route other shapes through the axioms.

Aimed squarely at the A-leg (refinement.md A4's delegation claim). | EXIT=0 CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (22.6s). => resolve-checked, see below. | | atk_9.py  | BOUNDARY: separator child dropped entirely; the parser's nodes spliced straight onto the annotation node. | EXIT=2 NOT-A-COUNTEREXAMPLE -- spec REJECTS. | | atk_10.py | NON-TERMINATION: tail-recurse on the same arguments, so the rendering never happens. Probes whether method-level MustTerminate(6) really rejects a diverging rival. | EXIT=2 NOT-A-COUNTEREXAMPLE -- spec REJECTS. | | atk_11.py | EMPTY ANNOTATION NODE WHEN NOTHING IS DECLARED: gold present-arm, but the absent arm contributes an empty annotation node (flag True).

The other end of is_annotation_node == present from atk_4. | EXIT=2 NOT-A-COUNTEREXAMPLE -- spec REJECTS. | | atk_12.py | ORDER SWAP: parser children first, separator appended LAST. Every child's kind/inside/text is individually gold; only the rendered ORDER is wrong. | EXIT=2 NOT-A-COUNTEREXAMPLE -- spec REJECTS (positional concatenation). |

MANDATORY RESOLVE STEP FOR THE ONE CANDIDATE (atk_8). I materialized TWO distinct faithful refinements rather than one, because the carrier's silence about node ATTRIBUTES is the sharpest available attack on A4, and I wanted the harness -- not my judgment -- to settle it. Both were generated mechanically in a throwaway git worktree at base_commit 9ed054279 and confirmed with `git apply --check` before running:

(a) $S/patch_atk_8a.diff -- the natural refinement: `if re.fullmatch('[A-Za-z_][A-Za-z0-9_]*', typ): annotations = [type_to_xref(typ, self.env)] else: annotations = _parse_annotation(typ, self.env)`, then the gold `desc_annotation(typ, '', nodes.Text(': '), *annotations)`. (submitted in `patches`)

(b) $S/patch_atk_8b.diff -- the ADVERSARIAL pre-image: the same bypass, but the node is `pending_xref('', nodes.Text(typ))`, built WITHOUT the refdomain/reftype/reftarget resolution attributes. This lands on the identical carrier value on all FIVE observables the model records (is_xref True, text == name, is_bare_text False, holds_one_bare_text True, is_annotation_node True), since mapping.md records a child's KIND, TEXT and INSIDE and nothing about reftarget -- so it is a legitimate pre-image of gold's abstract value and a real probe of whether the spec's silence there is exploitable.

Both run through the official harness (swebench_unified.harness.run_resolve, driver $S/resolve.py): atk_8a: {"completed": true, "resolved": TRUE, "attempts": 2, "flaky": true}  FAIL_TO_PASS 1/1 success, PASS_TO_PASS 44/44 success, 0 failures atk_8b: {"completed": true, "resolved": TRUE, "attempts": 1, "flaky": false} FAIL_TO_PASS 1/1 success, PASS_TO_PASS 44/44 success, 0 failures GOLD CONTROL, same host/session: {"completed": true, "resolved": TRUE, "attempts": 2, "flaky": true} So atk_8 is a CORRECT ECHO on both refinements, not a verify=>correct break. Note the flakiness bookkeeping deliberately: 8a and the GOLD control were each `flaky: true` (resolved on attempt 2/3) while 8b resolved first try -- the host was running many concurrent resolves.

WHY atk_8 IS NOT A DEFECT (and why it is still worth recording). Its bypass is only reachable where accepted()'s strong arm plus the four simple-name arms already pin the answer to exactly what the real parser produces -- and G-AX measures those arms TRUE of the real `_parse_annotation` (never refused a simple name over 23 names + 3392 exhaustive length-1/2 ASCII identifiers + 5000 fuzz strings, both config settings). So on that class the fabricated group and the delegated group are the same rendering, and the harness confirms it twice over. The residual observation, which is a documentation point rather than a hole: the spec pins the RESULT on the simple-name class but does not pin DELEGATION itself there, so refinement.md A4's prose ("the caller has no node of its own at those positions") is stronger than what the contracts force on that one class. Since the axiom arm it leans on is measurably true of the real callee, no verifying impl can diverge from gold there. This matches the collateral finding already recorded in verdict.md, and my harness runs now settle the question it left open ("likely still resolves") as a measured RESOLVES on two refinements.

A-LEG / refinement.md AUDIT (my assigned focus; R and I legs are G-CONF's).
 * Leg inventory: A1 R, A2 I, A3 R, A4 A-consumed, A5 R, A6 R. No kind-3 (unexpressible-changed-op) leg, and no A-reference deep model in this bundle -- consistent with SS.B's claim. Every axiom is genuinely consumed: I confirmed by construction that removing delegation (atk_5) breaks the domain clause and that each of the four sequence arms is separately load-bearing (atk_2 breaks only the bare-text axis, atk_3 only the holds-one axis, atk_12 only the order, atk_4/atk_11 only the wrapper flag). No dead axiom.
 * A4 correspondence to the real callee CHECKED against sphinx/domains/python.py:110 at base_commit, not just against the prose. `_parse_annotation`'s post-loop replaces each non-blank nodes.Text with type_to_xref(...) -> pending_xref, leaving desc_sig_punctuation alone; so for a simple name (ast.Name -> [nodes.Text(id)]) the list is exactly one pending_xref whose sole child is nodes.Text(name). That is precisely annotation_kinds==PSeq(True) / annotation_bare_text==PSeq(False) / annotation_holds_one_bare_text==PSeq(True) / annotation_texts==PSeq(s). Width-only claims outside that class are right, since compound shapes emit punctuation nodes the loop skips. axiom_check.py's observation functions match mapping.md's binding table symbol-for-symbol (is_xref = isinstance pending_xref; is_bare_text = isinstance nodes.Text; holds_one = len(children)==1 and isinstance(children[0], nodes.Text)), and it asserts the non-degeneracy (no node True on both axes) rather than assuming it.
 * The config dependency is disclosed correctly and is not a hidden hole: under python_use_unqualified_type_names=True the xref's label is two pending_xref_condition children, so texts/holds-one would read differently -- but mapping.md S3.1 records the default as binding, axiom_check sweeps BOTH settings, and I confirmed the ONLY repo test exercising a property `:type:` is the F2P test_pyproperty (default config, `:type: str`); no testroot declares a py:property with a type, and the two use_unqualified P2P tests cover py:class/py:function params instead. Both those P2P tests passed on all three resolve runs.
 * A3's injectivity claim (the one the prior revision got wrong) now holds as stated: nodes.Text(': ') -> (False, True, False) vs desc_sig_punctuation('', ': ') -> (False, False, True) are distinct carrier values, and atk_2 -- the exact rendering that previously slipped through -- is now rejected. A5's wrapper leg is independently pinned (atk_4/atk_11 both rejected), which matters because `_parse_annotation` returns a bare List[Node] and so cannot constrain the wrapper.

**FLOOR:** 12 admissible same-spec attacks (>=5 required), prepatch bug reproduced as atk_1 with its impl region byte-identical to model_prepatch.py, positive control $S/pos_control.py (structurally different correct impl: locals built in reverse order plus framing Asserts) VERIFIES in 19.7s -- so the spec is not vacuously strong. No verifier timeouts, no crashes, no incomplete resolve runs; every attack reached a real verdict and the one candidate reached a real harness verdict. Nothing INCONCLUSIVE.

**Cleanup:** the temporary git worktree used to generate/validate the diffs was removed and pruned; the source repo tree is untouched (no stash, no checkout of the shared tree).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK ANGLE: spec-too-strong / drift from real repo behaviour. Reference used was the base_commit worktree with patch.diff APPLIED, per the brief -- I did NOT score the patch delta itself as divergence.

Where I pressed hardest, and why the spec survived:

1. **WIDTH.** The obvious too-strong shape would be a fixed two-child claim. The spec does not make one: its general clauses are elementwise splices of the parser's whole node list (PSeq(False) + annotation_kinds(typ), etc.), and the two-child claim is confined to the is_simple_name guard. I confirmed the real widths range 0..8 and the elementwise clauses hold at every one of them. mapping.md and refinement.md both document that an earlier revision DID have a fixed-width-two carrier and recorded 35,161 disagreements -- the current shape is the repair, and the List[int] witness is still in the boundary list, so the domain was not narrowed to reach the pass.

2. **PARTIALITY.** accepted() is a genuine partial-domain axiom, not a totality dodge: the parser really does refuse bytes-literal annotations (nodes.Text.`__new__` rejects bytes; the except SyntaxError fallback at :185 does not catch TypeError, so it escapes), :type: is directives.unchanged so those are ordinary admitted inputs, and the real caller has no handler -- so the Exsures 'refusal propagates unabsorbed' is what the repo does. I verified refusal coincidence on ~140k inputs and found no one-sided case. Crucially the refused class was ADDED to the domain, not excluded from it (6,040 of G-CONF's inputs), which is the opposite of a too-strong-spec-hidden-by-a-narrow-Requires.

3. **THE FOUR CHILD AXES.** These are the axes most at risk of being over-specified beyond what the real code guarantees. Each is measurably non-degenerate on real output (bare-text 106133/197605, holds-one 197605/106133, is_annotation_node 91977/2017), each maps to one distinction assert_node actually draws (wrapper class before any child; nodes.Text matched by str-equality where no Element can match; [pending_xref, "str"] requiring exactly one child), and each holds on the real code everywhere I probed. They are not gold-plating: they are the injectivity repair for a documented real hole where a desc_sig_punctuation(': ') separator verified against the old spec and failed the test.

4. THE ONE HONEST CAVEAT (recorded, not concealed, and not a defect). Two of the four simple-name clauses -- text == name and holds_one_bare_text == True -- are true only under python_use_unqualified_type_names = False. I reproduced the non-default behaviour directly: 'str' -> (True, 'strstr', False, False), and my whole harness re-run under that flag produces 5,838 failures confined to exactly two kinds, axiom-simple-name and simple-name-arm, with the general elementwise clauses, the Exsures arm and is_annotation_node all still holding. So the config sensitivity is precisely the two clauses mapping.md §3.1 flags in advance and no others -- the disclosure is accurate rather than approximate. I judge this NOT unfaithful because config is not in the modelled signature, the binding config is the F2P app's default, and both mapping.md and refinement.md state the dependency and the reason (pending_xref_condition pairs) before any gate rests on it. A reviewer wanting to tighten this could parameterise the axioms by the flag, but that would model a callee the patch does not touch more finely than the changed site consumes.

5. OUT-OF-ABSTRACTION NOISE I deliberately did not score. super().handle_signature raises ValueError on malformed sig; sig is not a parameter of handle_property_annotation and the modelled site is the annotation block at :862-864 only. Reporting that as a diverging input would be condemning the abstraction boundary, not a spec defect.

**ENVIRONMENT NOTE:** the host python is 3.10 with docutils 0.23 installed, which is outside sphinx 4.2's '<0.18' pin; I installed docutils 0.17.1  and put it first on PYTHONPATH. Without that pin the observations would not be the ones the F2P app makes, so any 'divergence' measured against docutils 0.23 would have been an environment artefact rather than a spec finding. All work confined to /tmp; the bundle was read only, never modified.

**CONCLUSION:** no diverging input exists that I could find under ~350k targeted and exhaustive observations plus full independent reproduction of both bundle gates and the prepatch control. The spec is not too strong: it delegates where the real code delegates, is partial where the real callee is partial, and pins the two-child shape only on the class where it is genuinely true. FAITHFUL.

Counterexample / evidence:

```
NONE. I constructed four independent adversarial harnesses in /tmp (not the bundle's generator or seed) that evaluate the model's POSTCONDITION CLAUSES directly against the real patched PyProperty.handle_signature, and the AXIOM Ensures directly against the real _parse_annotation, in a worktree at base_commit 9ed054279 with patch.diff APPLIED (the correct reference per the brief) plus docutils 0.17.1 to honour sphinx's 'docutils>=0.14,<0.18' pin.

(1) f2_9591_diff.py -- ~100,100 inputs (boundary list + exhaustive short identifiers + all keywords + 60,000 punctuation-rich fuzz + 40,000 well-formed-ish compound annotations), each scored on every clause: Exsures arm coincidence (caller refuses iff parser refuses), is_annotation_node == present, absent -> width 0, the four elementwise splice clauses (children == [(False,': ',True,False)] + parser's own observations), and the simple-name two-child arm. RESULT: 0 failures.

(2) f2_9591_exh.py -- EXHAUSTIVE over every ASCII simple name of length 1..3 (full 53x63x63 cross product) plus every keyword/soft keyword and lengths up to 1000: 213,780 names, each checked against BOTH the axiom simple-name arms (exactly one node, a pending_xref, not bare text, holding exactly one bare text run spelling the name) and the model's postcondition simple-name arm. RESULT: 0 axiom-arm violations, 0 postcondition-arm violations. accepted()'s strong arm (is_simple_name -> accepted) never refuted.

(3) f2_9591_edge.py -- three targeted spec-too-strong hunts. (a) Is accepted(s) really a function of s alone, as the model types it? 40,014 inputs under both config settings: the refusal set differs on 0/40,014, so modelling the domain config-independently is sound. (b) Can the real method raise with present==False (which the Exsures, requiring 'present and not accepted', would then be too strong for)? super().handle_signature raises ValueError on 16 malformed SIGNATURES ('', 'a b c', 'prop1(' ...) -- but sig is not a parameter of the modelled function; the modelled site is the type-annotation block alone (mapping.md §1 binds it to lines 862-864), and refinement.md A1 scopes it that way, so this is outside the abstraction rather than a divergence. (c) Node count: the real code contributes exactly one desc_annotation whenever typ is truthy and zero otherwise, matching is_annotation_node == present.

(4) f2_9591_deep.py -- 100 hostile shapes: nesting to depth 1600 (RecursionError territory), 'int | int' x1600, unicode identifiers that ast accepts as Name but is_simple_name rejects (ünï, α, 日本語, ẞ, İ, ideographic space), annotations up to 20,000 chars, lone surrogates, NUL, \v \f \r, zero-width space. Every case checked for caller/parser refusal coincidence and elementwise child agreement. RESULT: 0 failures -- notably no shape where the caller refuses while the parser accepts or vice versa, which is what the Exsures arm rests on.

CROSS-CHECKS of the bundle's own claims, re-run by me in my own worktree rather than trusted from verdict.md: G-AX (axiom_check.py) exits 0 and reproduces its recorded string verbatim, including the 12-member refused class ('b"x"' -> TypeError, 'a\x00b' -> ValueError, '"\ud800"' -> UnicodeEncodeError) and the 1320 nodes reading False on BOTH child axes that keep them from collapsing into one. G-CONF (conformance_check.py) exits 0: 100,034 inputs, 0 disagreements, width histogram {0:2017, 1:58, 2:61936, 3:14, 4:17, 5:12920, 6:7079, 7:7000, 8:2953} and 6,040 both-refused, matching mapping.md exactly. nagini_verify.sh on model.py: 'Verification successful' (34.29s). G-DIFF control: nagini_verify.sh on model_prepatch.py FAILS on 'Implies(present, accepted(ToSeq(typ)))' -- so the spec is not vacuous and genuinely senses the patch. Impl region is byte-identical to the G-CONF shadow modulo the PSeq type-comment erasure the shim forces.
```

**ATTACK ANGLE:** spec-too-strong / drift from real repo behaviour. Reference used was the base_commit worktree with patch.diff APPLIED, per the brief -- I did NOT score the patch delta itself as divergence.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE. Judged the consumer-visible spec view only = markers.spec_view(model.py, nagini) — 364 lines, sha256 54b48fb0e2f6e71b91c8a6585e4c2c2bf0bc8d6320b0577becb1b4edb24ce7fc, impl region elided to `...  # implementation elided`. Confirmed via src/swebench_unified/eval/prompts.py::`_spec_block` that consumers receive only spec_view + modeled_functions, so refinement.md / mapping.md / meta.json are out of scope (read as controls only). parse_regions errors == []; spans pure/axioms/pre/post/impl well-formed; spec_view idempotent. same-spec on a byte-identical copy -> exit 0 ("SAME"), confirming my spec-view derivation matches the authoritative tool. hints_text is EMPTY ('' verbatim) for this instance, so the hints-only-vocabulary leak mode is structurally unavailable; leakage judged against problem_statement alone as required.

NO RELAXATION IS CLAIMED, AND I DID NOT INHERIT ONE. There is no RELAXED_LEAKAGE.md in the bundle and no meta.json `relaxed_leakage` key ('relaxed_leakage' in meta == False); gates.G-LEAK.status == "pass", not "relaxed". So this is judged as an ordinary no-leakage review, not a relaxation review. I checked separately whether anything in the bundle addresses the panel or tells me how to record: grep for attacker/G-PANEL/panel/auditor/reviewer/submit/NO-LEAKAGE over model.py, refinement.md, mapping.md returns nothing. No file in the bundle instructs me toward a verdict — nothing to report on that head.

CORE GATES REPRODUCED MYSELF (not taken on trust), all in /tmp.
- nagini_verify.sh model.py -> "Verification successful" (23.8s).
- model_prepatch.py -> "Verification failed": Implies(present, accepted(ToSeq(typ))) might not hold. So the spec genuinely discriminates gold from pre-patch (G-DIFF/G-GOLD real).
- axiom_check.py inside the instance image (swebench/sweb.eval.x86_64.sphinx-doc_1776_sphinx-9591) -> exit 0. NOTE my first run outside the image failed with ModuleNotFoundError: sphinx — that was my harness error, not a gate failure.
- conformance_check.py -> exit 0, 100,034 inputs, 0 disagreements, 6,040 both-refused, widths 0-8. IMPORTANT: my first run reported 98,017 disagreements because I had not applied patch.diff to /testbed first; the oracle was then emitting the glued pre-patch ': a.b.C'. With `git apply patch.diff` + PYTHONPATH=/testbed the gate passes. I record the false alarm so nobody mistakes it for a G-CONF break.

**MECHANICAL SCREEN:** leakage.screen(model.py, nagini, gold_patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. Consistent with gates.G-LEAK.

### Independent adversarial checks
1. Gold-line reconstruction: for each of the 3 changed gold lines, longest whitespace-normalized shared run with the view is 12 chars = '`_annotation`(', which comes from the spec's own `def handle_property_annotation(` / `annotation_kinds(` identifiers, not from the diff. No gold line reproduced verbatim.
2. Repo-symbol probes ALL ZERO: `_parse_annotation`, desc_annotation, addnodes, signode, pending_xref, PyProperty, handle_signature, type_to_xref, nodes.Text, desc_sig_punctuation, options.get, self.env, BuildEnvironment, docutils, reftarget, desc_signature, desc_name, directives, PyVariable, PyAttribute, doctree, assert_node, test_pyproperty, 'domains/python', 'sphinx.'. Patched path sphinx/domains/python.py and dotted module absent. No file:line refs; no bare 8xx line-number tokens (regex over (?<![\w.])8[0-9][0-9] -> []). Patch changed-symbol set is exactly {handle_signature}; the spec's `handle_property_annotation` shares only the generic verb 'handle', and 'property'/'annotation' are both PUBLIC in the PS ("property's type annotation").
3. Test-patch echo: pending_xref / desc_annotation / prop1 / assert_node / doctree all ABSENT from the view. The F2P expected doctree is not transcribed.
4. Systematic vocabulary intersection (not guess-driven): tokens >=4 chars in the view that also occur in the real patched python.py but NOT in problem_statement = 83, all ordinary contract English ('parser','children','separator','inline','label','group','node/nodes','text','literal'). Only 2 also occur in the gold diff — 'nodes' and 'text' — each as generic prose, never as a repo identifier or edit locator.
5. Narration sweep over 30 terms (bug/fix/patch/pre-patch/previously/glued/concatenat/no longer/used to/was rendered/currently/the old/defect/issue/...): ZERO hits. Only 'rather than' (4x, contrastive contract prose) and 'inert' (2x). The view states target behavior, never the prior defect or a diagnosis.

THE ONE BORDERLINE ITEM, AND WHY IT IS NOT LEAKAGE. The view does disclose mechanism: the group is ': ' as its OWN bare-text node followed by the shared annotation parser's nodes spliced through unaltered, held in an annotation node. That is close to an abstract transcription of the gold edit, so I tested it two ways rather than asserting it.

(a) DERIVABILITY FROM PUBLIC INPUTS — this is the decisive measurement, and it is stronger than the prior panel recorded. In the PRE-PATCH worktree at base_commit 9ed05427 I searched sphinx/domains/python.py for the gold's ADDED lines and found BOTH of them present VERBATIM at two sibling sites: lines 664-665 (PyVariable) and 825-826 (PyAttribute) are exactly `annotations = _parse_annotation(typ, self.env)` / `signode += addnodes.desc_annotation(typ, '', nodes.Text(': '), *annotations)`, predating base_commit (blame: "Fix #7928: py domain: failed to resolve a type annotation for the attribute"). The gold edit is therefore a copy of an existing in-repo idiom onto the property site, and any solver with bash — which every eval mode has — recovers the exact mechanism from the public repo plus a PS that already says "cross-references don't work in property's type annotations" and "I expected the documented type ... to be cross-referenced". The spec view discloses strictly less than `grep -n desc_annotation sphinx/domains/python.py` does. It cannot leak what the public repo hands over verbatim.

(b) LOAD-BEARING TEST. I built a de-narrated variant with the 6 mechanism clauses removed (the accepted() delegation clause, the four elementwise splice clauses, and the operation's Exsures partiality arm) and grafted the PRE-PATCH impl into it: stripped_prepatch.py still FAILS verification — the surviving simple-name clause (is_xref == PSeq(False,True) etc.) rejects it on its own. So the mechanism clauses are NOT the sole discriminator, i.e. they are not a smuggled-in edit recipe doing work no behavioral clause could. They remain justified on faithfulness grounds I re-measured: G-AX shows the real `_parse_annotation` is PARTIAL (313/5000 fuzz refusals, 12 refusal classes) and G-CONF shows real widths 0-8, so a spec that did not delegate to the parser and inherit its partiality would over-claim behavior the real code lacks. And `desc_annotation` (the is_annotation_node wrapper) appears on BOTH sides of the diff, so pinning it localizes nothing.

INCIDENTAL, OUT-OF-GATE (artifact integrity, not leakage). (i) Top-level meta.json `region_hashes` is STALE: all 6 entries disagree with values recomputed from the shipped model.py, while gates['G-HYGIENE'].data.region_hashes matches my recomputation exactly on all 6. The shipped model.py (sha 4c965f84...) is the gated artifact; only the stale top-level copy is inconsistent. Worth a maintainer fix. (ii) The G-PANEL* and G-EQ records were checked against an OLDER model.py (sources.model.py = c4bf81d7..., 2026-08-14) while every 2026-08-15 gate cites 4c965f84...; G-PANEL-1/G-EQ are recorded `fail` against that older artifact. That stale panel disposition is not mine to resolve, but it means the recorded G-PANEL-1 spec-weakness fail has not been re-run against the current spec — flagging for the weakness lane, not this one.

**PROCESS NOTE.** An early scan of mine read a fixed-name specview.txt that another process on this shared host had overwritten with an unrelated matrix model (identifiers Mat/ShapeMismatch/concat_right), which briefly produced a bogus 'no repo symbols' reading. I re-derived the view into a private mktemp -d and re-ran every check against a sha-pinned copy; all numbers above are from that verified copy.

**VERDICT:** NO-LEAKAGE. The view names no file, function, symbol, line, or diff fragment; narrates no bug->fix; echoes no hints (there are none) and no test-patch expectation. Its one mechanism disclosure is both faithfulness-forced and already public verbatim at two sibling call sites in the pre-patch repo.

**SCOPE.** Judged the consumer-visible spec view only = markers.spec_view(model.py, nagini) — 364 lines, sha256 54b48fb0e2f6e71b91c8a6585e4c2c2bf0bc8d6320b0577becb1b4edb24ce7fc, impl region elided to `...  # implementation elided`. Confirmed via src/swebench_unified/eval/prompts.py::`_spec_block` that consumers receive only spec_view + modeled_functions, so refinement.md / mapping.md / meta.json are out of scope (read as controls only). parse_regions errors == []; spans pure/axioms/pre/post/impl well-formed; spec_view idempotent. same-spec on a byte-identical copy -> exit 0 ("SAME"), confirming my spec-view derivation matches the authoritative tool. hints_text is EMPTY ('' verbatim) for this instance, so the hints-only-vocabulary leak mode is structurally unavailable; leakage judged against problem_statement alone as required.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
