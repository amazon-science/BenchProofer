# P2 adversarial audit — django__django-12308

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.py` |

**Non-vacuity.** The positive control `control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. 12 same-spec attacks run to a real verifier verdict; 11 REJECTED. The single CANDIDATE (atk_5, ungrounded-oracle echo: serialize() then a second-buffer re-copy) had its faithful refined patch MATERIALIZED (patch_atk5.diff) and RUN through the official harness -- run_resolve('django__django-12308', patch, run_id='sbu-eq-s7chsrpu-atk5') -> resolved=True, completed=True. It RESOLVES, so per architecture.md §6 it is a behaviourally-correct alternative implementation (an echo of the reference), NOT a spec weakness, and does not fail the gate. No verify-but-wrong witness exists among these probes: verify=>correct is not broken for this bundle.
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -611,9 +611,6 @@
             j = j + 1
         return result
 
-    if encodable:
-        # the interchange encoding: the structural serialisation of the tree.
-        return serialize(value)
 
     # fallback: the general-purpose display text for this value, returned
     # unchanged (a fresh owned copy of it; no delimiters are added).
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -612,8 +612,12 @@
         return result
 
     if encodable:
-        # the interchange encoding: the structural serialisation of the tree.
-        return serialize(value)
+        # PARTIAL DOMAIN: only a STRING root goes through the encoder.
+        Unfold(Acc(j_pred(value), 1 / 2))
+        k = value.kind
+        Fold(Acc(j_pred(value), 1 / 2))
+        if k == 0:
+            return serialize(value)
 
     # fallback: the general-purpose display text for this value, returned
     # unchanged (a fresh owned copy of it; no delimiters are added).
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -451,7 +451,7 @@
     elif c == 13:
         result.append(92)
         result.append(114)
-    elif 32 <= c and c <= 126:
+    elif 32 <= c and c <= 127:
         result.append(c)
     elif 0 <= c and c <= 65535:
         result.append(92)
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -612,7 +612,15 @@
         return result
 
     if encodable:
-        # the interchange encoding: the structural serialisation of the tree.
+        spin = 0
+        while spin >= 0:
+            # invariants-start
+            Invariant(Acc(j_pred(value), 1 / 2))
+            Invariant(Acc(list_pred(empty), 1 / 2))
+            Invariant(Acc(list_pred(content), 1 / 2))
+            Invariant(spin >= 0)
+            # invariants-end
+            spin = spin + 1
         return serialize(value)
 
     # fallback: the general-purpose display text for this value, returned
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -612,8 +612,11 @@
         return result
 
     if encodable:
-        # the interchange encoding: the structural serialisation of the tree.
-        return serialize(value)
+        # ECHO: serialise, then hand back a re-copied buffer.
+        first = serialize(value)
+        out3 = []  # type: List[int]
+        append_all(out3, first)
+        return out3
 
     # fallback: the general-purpose display text for this value, returned
     # unchanged (a fresh owned copy of it; no delimiters are added).
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -407,7 +407,6 @@
     # tail: the rest of the sibling list, comma-and-space separated.
     if head.nxt is not None:
         result.append(44)
-        result.append(32)
         rest = serialize_list(head.nxt)
         append_all(result, rest)
     Fold(Acc(j_pred(head), 1 / 2))
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -619,16 +619,15 @@
     # unchanged (a fresh owned copy of it; no delimiters are added).
     out2 = []  # type: List[int]
     m = 0
-    while m < len(content):
+    while m < len(empty):
         # invariants-start
-        Invariant(Acc(list_pred(content), 1 / 2))
+        Invariant(Acc(list_pred(empty), 1 / 2))
         Invariant(Acc(list_pred(out2)))
-        Invariant(0 <= m and m <= len(content))
-        Invariant(ToSeq(out2) == ToSeq(content).take(m))
-        Invariant(MustTerminate(len(content) - m + 1))
+        Invariant(0 <= m and m <= len(empty))
+        Invariant(ToSeq(out2) == ToSeq(empty).take(m))
+        Invariant(MustTerminate(len(empty) - m + 1))
         # invariants-end
-        out2.append(content[m])
+        out2.append(empty[m])
         m = m + 1
-    Assert(ToSeq(content).take(len(content)) == ToSeq(content))
     return out2
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -454,12 +454,16 @@
     elif 32 <= c and c <= 126:
         result.append(c)
     elif 0 <= c and c <= 65535:
+        d0 = c // 4096
+        d1 = (c // 256) % 16
+        d2 = (c // 16) % 16
+        d3 = c % 16
         result.append(92)
         result.append(117)
-        result.append(hex_digit(c // 4096))
-        result.append(hex_digit((c // 256) % 16))
-        result.append(hex_digit((c // 16) % 16))
-        result.append(hex_digit(c % 16))
+        result.append(48 + d0 if d0 < 10 else 55 + d0)
+        result.append(48 + d1 if d1 < 10 else 55 + d1)
+        result.append(48 + d2 if d2 < 10 else 55 + d2)
+        result.append(48 + d3 if d3 < 10 else 55 + d3)
     elif 65536 <= c and c <= 1114111:
         hi = 55296 + (c - 65536) // 1024
         lo = 56320 + (c - 65536) % 1024
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -401,7 +401,6 @@
         append_escaped(result, head.text)
         result.append(34)
         result.append(58)
-        result.append(32)
         vbody = serialize_list(head.inner)
         append_all(result, vbody)
     # tail: the rest of the sibling list, comma-and-space separated.
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -596,6 +596,9 @@
                     ToSeq(Result()) == fallback_form(ToSeq(content))))
     # post-conditions-end
     # impl-start
+    if encodable:
+        return serialize(value)
+
     if not present:
         result = []  # type: List[int]
         j = 0
@@ -611,9 +614,6 @@
             j = j + 1
         return result
 
-    if encodable:
-        # the interchange encoding: the structural serialisation of the tree.
-        return serialize(value)
 
     # fallback: the general-purpose display text for this value, returned
     # unchanged (a fresh owned copy of it; no delimiters are added).
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -332,17 +332,17 @@
         return out
     if node.kind == 1:                          # ARRAY: [ elements ]
         body = serialize_list(node.inner)
-        result = [91]  # type: List[int]
+        result = [123]  # type: List[int]
         append_all(result, body)
-        result.append(93)
+        result.append(125)
         Fold(Acc(j_pred(node), 1 / 2))
         Assert(ToSeq(result) == node_body(node))
         return result
     if node.kind == 2:                          # OBJECT: { members }
         mbody = serialize_list(node.inner)
-        result2 = [123]  # type: List[int]
+        result2 = [91]  # type: List[int]
         append_all(result2, mbody)
-        result2.append(125)
+        result2.append(93)
         Fold(Acc(j_pred(node), 1 / 2))
         Assert(ToSeq(result2) == node_body(node))
         return result2
@@ -387,15 +387,15 @@
         append_escaped(result, head.text)
         result.append(34)
     elif head.kind == 1:                        # ARRAY: [ elements ]
-        result.append(91)
+        result.append(123)
         body = serialize_list(head.inner)
         append_all(result, body)
-        result.append(93)
+        result.append(125)
     elif head.kind == 2:                        # OBJECT: { members }
-        result.append(123)
+        result.append(91)
         mbody = serialize_list(head.inner)
         append_all(result, mbody)
-        result.append(125)
+        result.append(93)
     else:                                       # MEMBER: "key": value
         result.append(34)
         append_escaped(result, head.text)
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -324,9 +324,9 @@
     # impl-start
     Unfold(Acc(j_pred(node), 1 / 2))
     if node.kind == 0:                          # STRING: "text"
-        out = [34]  # type: List[int]
+        out = [39]  # type: List[int]
         append_escaped(out, node.text)
-        out.append(34)
+        out.append(39)
         Fold(Acc(j_pred(node), 1 / 2))
         Assert(ToSeq(out) == node_body(node))
         return out
@@ -347,9 +347,9 @@
         Assert(ToSeq(result2) == node_body(node))
         return result2
     # MEMBER: "key": value
-    result3 = [34]  # type: List[int]
+    result3 = [39]  # type: List[int]
     append_escaped(result3, node.text)
-    result3.append(34)
+    result3.append(39)
     result3.append(58)
     result3.append(32)
     vbody = serialize_list(node.inner)
@@ -383,9 +383,9 @@
     # head body, dispatched INLINE (mirrors ser_list / node_body), recursing
     # into serialize_list on the sub-nodes only -- all while `head` is unfolded.
     if head.kind == 0:                          # STRING: "text"
-        result.append(34)
+        result.append(39)
         append_escaped(result, head.text)
-        result.append(34)
+        result.append(39)
     elif head.kind == 1:                        # ARRAY: [ elements ]
         result.append(91)
         body = serialize_list(head.inner)
@@ -397,9 +397,9 @@
         append_all(result, mbody)
         result.append(125)
     else:                                       # MEMBER: "key": value
-        result.append(34)
+        result.append(39)
         append_escaped(result, head.text)
-        result.append(34)
+        result.append(39)
         result.append(58)
         result.append(32)
         vbody = serialize_list(head.inner)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `control.py`

```python
"""Twin-artifact model for django__django-12308.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A stored structured-data value rendered as text must be shown in its
  CANONICAL DATA-INTERCHANGE encoding, not in the host language's object
  printout. A structured value is a tree: a string token, an ordered array of
  values, or an object whose members are (string-key, value) pairs.

  The interchange encoding serialises that tree STRUCTURALLY:

    * a string token is delimited by the double-quote delimiter U+0022 ( " ),
      so the value  a  renders as  "a" ; INSIDE that pair the token's own code
      points are written in the interchange alphabet rather than spliced in
      raw -- the delimiter U+0022 and the escape character U+005C are each
      written as U+005C followed by themselves, the five control positions
      U+0008, U+0009, U+000A, U+000C, U+000D as U+005C followed by b, t, n, f,
      r, and every other code point outside the printable band
      U+0020..U+007E as the six-code-point form U+005C, U+0075 and four
      lowercase hexadecimal digits (a code point above U+FFFF as the pair of
      such forms for its two surrogate halves); the printable ones stand for
      themselves;
    * an array renders as its elements, comma-and-space separated, between
      square brackets:  [ e1, e2, ... ] ;
    * an object renders as its members, comma-and-space separated, between
      curly braces, each member a double-quoted key, a colon-space, then the
      member value:  { "k1": v1, "k2": v2, ... } .

  So the value  {a: {b: c}}  renders as  {"a": {"b": "c"}}  and the value
  [a, b]  renders as  ["a", "b"] : the structure is laid out exactly, with
  every string token and every key delimited by the double quote U+0022.

  Concretely, for a structured value `value`:

    - a value that is ABSENT -- nothing is stored for it at all -- renders as
      the supplied placeholder text. ABSENCE is not the same thing as
      EMPTINESS: a value that IS stored but is itself empty is not absent, and
      does NOT render as the placeholder;
    - a value that is routed through the interchange encoder, and that the
      encoder can express, renders as its canonical interchange encoding: the
      STRUCTURAL serialisation above (`interchange_form`);
    - EVERY other stored value -- one whose contents the encoder cannot
      express, and equally one that is itself empty and so is never routed
      through the encoder at all -- renders as the general-purpose display
      text supplied for that value (`fallback_form`), shown AS-IS: the
      renderer adds no delimiters of its own. Where that fallback text shows
      string tokens they already carry the host language's single-quote
      U+0027 delimiters internally.

  The discriminating guarantee is STRUCTURAL: a value the encoder can express is
  rendered as the full interchange serialisation of its tree (brackets, braces,
  key/colon layout, double-quote U+0022 delimiters), never as the general-purpose
  display text. A renderer that merely wraps the whole printed value in one pair
  of delimiters does NOT satisfy this: the array  [a, b]  must render as
  ["a", "b"] , not as a single wrapped token.

  Rendering is moreover a TOTAL operation. For every admissible structured
  value the renderer must actually PRODUCE the text described above and hand it
  back to whoever asked for it: the guarantees above are claims about a result
  that genuinely ARRIVES, not merely about the runs that happen to arrive.
  Displaying a stored value is a bounded walk of that value's own contents --
  every step of the walk moves onto a strictly smaller part of the value (into
  something it contains, or on to the next item beside it) and each character of
  a token is consumed once -- so the walk always runs out of value to visit and
  the display appears. A renderer that can walk forever on some admissible
  value, so that the display never appears at all, does NOT meet this
  specification, no matter how its never-reached exit is annotated.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); a structured value is modelled as a small recursive node tree
(`JNode`) in sibling/inner linked form. The interchange encoding is modelled
DEEPLY as a single self-recursive serialiser fold over that tree
(`interchange_form`). The general-purpose display fallback is a SEPARATE
renderer with its own dispatch (it lays a sequence out element-by-element
rather than printing it as one object), so the model does NOT re-derive its
text from the value: `fallback_form` is the identity on `content`, the text
THAT renderer produced for this value, which the renderer then hands back with
no delimiters of its own added. Both are validated == their real callees
out-of-band by axiom_check.py (G-AX) on the real structured values, never
consumed as axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. The two callees the rendered branch invokes are modelled
# DEEPLY: the interchange encoder as a single self-recursive serialiser fold
# over the value tree (interchange_form), and the general-purpose display
# renderer as the text it produced passed through unchanged (fallback_form =
# identity; the renderer adds no delimiters of its own). That renderer has its
# own per-shape dispatch, so its text is CARRIED in `content` rather than
# re-derived from the value here. They are validated == their real callees
# out-of-band by axiom_check.py (G-AX) as A-references on the real structured
# values, never consumed here.
# axioms-end


# pure-start
class JNode:
    """One node in a structured-value tree, in sibling/inner linked form.

    `kind`:
        0 = STRING token  -- contents in `text`;
        1 = ARRAY         -- elements are the sibling list at `inner`;
        2 = OBJECT        -- members are the sibling list at `inner`;
        3 = MEMBER        -- one object member: KEY in `text`, VALUE is the
                             single node at `inner` (the value node carries no
                             siblings, i.e. its own `nxt` is None).
    `text`: STRING contents (kind 0) or MEMBER key (kind 3).
    `inner`: head of the contained sibling list (ARRAY elements / OBJECT
             members) or the member value (kind 3); unused for a STRING.
    `nxt`: the next sibling in the current element / member list (None = last).
    """

    def __init__(self, kind: int, text: List[int], inner: 'Optional[JNode]',
                 nxt: 'Optional[JNode]') -> None:
        Requires(Acc(list_pred(text)))
        Requires(Implies(inner is not None, Acc(j_pred(inner))))
        Requires(Implies(nxt is not None, Acc(j_pred(nxt))))
        # Assembling one node is a single bounded step; measure 1 sits strictly
        # below every walk budget below, so a walk may build a node.
        Requires(MustTerminate(1))
        Ensures(Acc(j_pred(self)))
        # A value assembled with nothing inside it and nothing beside it is one
        # single part, so a walk of it has exactly one step to take.
        Ensures(Implies(inner is None and nxt is None, j_size(self) == 1))
        self.kind = kind
        self.text = text
        self.inner = inner
        self.nxt = nxt
        Fold(j_pred(self))


@Predicate
def j_pred(n: JNode) -> bool:
    return (Acc(n.kind) and Acc(n.text) and Acc(n.inner) and Acc(n.nxt) and
            list_pred(n.text) and
            Implies(n.inner is not None, j_pred(n.inner)) and
            Implies(n.nxt is not None, j_pred(n.nxt)))


@Pure
def empty_seq() -> PSeq[int]:
    return PSeq(0).take(0)


@Pure
def j_size(n: 'Optional[JNode]') -> int:
    """How much VALUE there is to walk at `n`: the number of parts the
    structured value (or the run of values beside it) is made of; 0 when there
    is nothing there. Every step a renderer takes moves onto something the
    current part contains, or on to the next part beside it, and both are
    strictly smaller by this count -- so this is the budget within which the
    display has to appear."""
    Requires(Implies(n is not None, Acc(j_pred(n), 1 / 4)))
    Ensures(Result() >= 0)
    Ensures(Implies(n is None, Result() == 0))
    Ensures(Implies(n is not None, Result() > 0))
    if n is None:
        return 0
    return Unfolding(Acc(j_pred(n), 1 / 4),
                     1 + j_size(n.inner) + j_size(n.nxt))


@Pure
def hex_digit(d: int) -> int:
    """The lowercase hexadecimal digit for 0 <= d < 16, as a code point."""
    return 48 + d if d < 10 else 87 + d


@Pure
def hex_form(c: int) -> PSeq[int]:
    """The six-code-point interchange form of one 16-bit unit: the escape
    character U+005C, the letter u (U+0075), then the unit's four lowercase
    hexadecimal digits, most significant first."""
    return (PSeq(92, 117) + PSeq(hex_digit(c // 4096))
            + PSeq(hex_digit((c // 256) % 16))
            + PSeq(hex_digit((c // 16) % 16)) + PSeq(hex_digit(c % 16)))


@Pure
def esc_char(c: int) -> PSeq[int]:
    """The interchange form of ONE code point of a string token or of a key.

    The interchange alphabet is not the host alphabet, so a token's code
    points are not spliced in raw between the delimiters: the delimiter U+0022
    and the escape character U+005C are each written as U+005C followed by
    themselves; the five control positions U+0008, U+0009, U+000A, U+000C and
    U+000D have their own two-code-point forms (U+005C followed by b, t, n, f
    and r); every other code point outside the printable band U+0020..U+007E
    is written in the six-code-point `hex_form`, and one above U+FFFF as the
    two hex forms of its surrogate halves. The printable code points stand for
    themselves. An int outside U+0000..U+10FFFF is no code point at all, so
    there is no character for it to stand for and it is left as it is."""
    if c == 34:
        return PSeq(92, 34)
    if c == 92:
        return PSeq(92, 92)
    if c == 8:
        return PSeq(92, 98)
    if c == 9:
        return PSeq(92, 116)
    if c == 10:
        return PSeq(92, 110)
    if c == 12:
        return PSeq(92, 102)
    if c == 13:
        return PSeq(92, 114)
    if 32 <= c and c <= 126:
        return PSeq(c)
    if 0 <= c and c <= 65535:
        return hex_form(c)
    if 65536 <= c and c <= 1114111:
        return (hex_form(55296 + (c - 65536) // 1024)
                + hex_form(56320 + (c - 65536) % 1024))
    return PSeq(c)


@Pure
def esc_seq(s: PSeq[int]) -> PSeq[int]:
    """The interchange form of a WHOLE token (or key): each of its code points
    replaced by that code point's own form, in order. The empty token has the
    empty form. This is what sits between the two U+0022 delimiters -- the
    token's code points do NOT pass through unchanged."""
    if len(s) == 0:
        return empty_seq()
    return esc_seq(s.take(len(s) - 1)) + esc_char(s[len(s) - 1])


@Pure
def node_body(head: JNode) -> PSeq[int]:
    """Interchange serialisation of the SINGLE node `head` (no sibling
    separator). Dispatched on kind; the contained sibling list is serialised by
    `ser_list` on `head.inner` (a strictly smaller predicate, so this recurses
    only downward through `Unfolding`)."""
    Requires(Acc(j_pred(head), 1 / 4))
    return Unfolding(
        Acc(j_pred(head), 1 / 4),
        # STRING: "text"
        PSeq(34) + esc_seq(ToSeq(head.text)) + PSeq(34) if head.kind == 0
        # ARRAY: [ elements ]
        else (PSeq(91) + ser_list(head.inner) + PSeq(93) if head.kind == 1
              # OBJECT: { members }
              else (PSeq(123) + ser_list(head.inner) + PSeq(125) if head.kind == 2
                    # MEMBER: "key": value
                    else PSeq(34) + esc_seq(ToSeq(head.text)) + PSeq(34)
                    + PSeq(58, 32) + ser_list(head.inner))))


@Pure
def ser_list(head: Optional[JNode]) -> PSeq[int]:
    """Interchange serialisation of the sibling list starting at `head`: each
    node's body, comma-and-space (44,32) separated, with no trailing separator.
    A member value node (kind 3's `inner`) carries no siblings, so `ser_list` on
    it yields exactly that value's body. The head's body is dispatched INLINE
    (same as `node_body`) so that ONE unfold of `j_pred(head)` covers both the
    head body and the tail; the only recursion is `ser_list` on the sub-nodes
    `head.inner` and `head.nxt` (strictly smaller predicates)."""
    Requires(Implies(head is not None, Acc(j_pred(head), 1 / 4)))
    if head is None:
        return empty_seq()
    return Unfolding(
        Acc(j_pred(head), 1 / 4),
        (PSeq(34) + esc_seq(ToSeq(head.text)) + PSeq(34) if head.kind == 0
         else (PSeq(91) + ser_list(head.inner) + PSeq(93) if head.kind == 1
               else (PSeq(123) + ser_list(head.inner) + PSeq(125) if head.kind == 2
                     else PSeq(34) + esc_seq(ToSeq(head.text)) + PSeq(34)
                     + PSeq(58, 32) + ser_list(head.inner)))) +
        (empty_seq() if head.nxt is None
         else PSeq(44, 32) + ser_list(head.nxt)))


@Pure
def interchange_form(node: Optional[JNode]) -> PSeq[int]:
    """Canonical interchange serialisation of a structured value (the deep
    model of `json.dumps`): the single-node serialisation of the tree rooted at
    `node` (the value carries no siblings at the top, so this is `node_body`)."""
    Requires(Implies(node is not None, Acc(j_pred(node), 1 / 4)))
    if node is None:
        return empty_seq()
    return node_body(node)


@Pure
def fallback_form(content: PSeq[int]) -> PSeq[int]:
    """The general-purpose display text for a value, UNCHANGED. Whenever the
    renderer does not route a stored value through the interchange encoder --
    because the encoder cannot express it, or because the value is itself empty
    and so is never offered to the encoder -- the display is whatever that
    general-purpose renderer produced for the value, handed back as-is with no
    delimiters added. That renderer dispatches on the value's own shape (a
    sequence is laid out element-by-element, not printed as a single object),
    so its text is CARRIED here in `content` rather than recomputed from the
    value tree; where it shows string tokens they are single-quote U+0027
    delimited, in contrast to the interchange encoding's structural
    double-quote U+0022."""
    return content
# pure-end


def serialize(node: JNode) -> List[int]:
    """Verified recursive serialiser: builds the interchange encoding of the
    single value `node` (the deep-model skeleton of the canonical interchange
    serialiser), each token and key laid down in its interchange form
    (`esc_seq`) between the U+0022 delimiters. Output pinned to
    `interchange_form` / `node_body`."""
    # pre-conditions-start
    Requires(Acc(j_pred(node), 1 / 2))
    # Total, not merely partial: the encoding must ARRIVE. The walk is bounded
    # by how much value there is to walk, so every descent must land on a
    # strictly smaller part of the value.
    Requires(MustTerminate(j_size(node) + 3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(j_pred(node), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == node_body(node))
    Ensures(ToSeq(Result()) == interchange_form(node))
    # post-conditions-end
    # impl-start
    Unfold(Acc(j_pred(node), 1 / 2))
    if node.kind == 0:                          # STRING: "text"
        out = [34]  # type: List[int]
        append_escaped(out, node.text)
        out.append(34)
        Fold(Acc(j_pred(node), 1 / 2))
        Assert(ToSeq(out) == node_body(node))
        return out
    if node.kind == 1:                          # ARRAY: [ elements ]
        body = serialize_list(node.inner)
        result = [91]  # type: List[int]
        append_all(result, body)
        result.append(93)
        Fold(Acc(j_pred(node), 1 / 2))
        Assert(ToSeq(result) == node_body(node))
        return result
    if node.kind == 2:                          # OBJECT: { members }
        mbody = serialize_list(node.inner)
        result2 = [123]  # type: List[int]
        append_all(result2, mbody)
        result2.append(125)
        Fold(Acc(j_pred(node), 1 / 2))
        Assert(ToSeq(result2) == node_body(node))
        return result2
    # MEMBER: "key": value
    result3 = [34]  # type: List[int]
    append_escaped(result3, node.text)
    result3.append(34)
    result3.append(58)
    result3.append(32)
    vbody = serialize_list(node.inner)
    append_all(result3, vbody)
    Fold(Acc(j_pred(node), 1 / 2))
    Assert(ToSeq(result3) == node_body(node))
    return result3
    # impl-end


def serialize_list(head: Optional[JNode]) -> List[int]:
    """Verified serialiser for a sibling list: each node's body, comma-and-space
    separated. Output pinned to `ser_list`."""
    # pre-conditions-start
    Requires(Implies(head is not None, Acc(j_pred(head), 1 / 2)))
    # Total, not merely partial: the encoding of the run of values must ARRIVE,
    # within the amount of value left to walk.
    Requires(MustTerminate(j_size(head) + 3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Implies(head is not None, Acc(j_pred(head), 1 / 2)))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == ser_list(head))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    if head is None:
        Assert(ToSeq(result) == ser_list(head))
        return result
    Unfold(Acc(j_pred(head), 1 / 2))
    # head body, dispatched INLINE (mirrors ser_list / node_body), recursing
    # into serialize_list on the sub-nodes only -- all while `head` is unfolded.
    if head.kind == 0:                          # STRING: "text"
        result.append(34)
        append_escaped(result, head.text)
        result.append(34)
    elif head.kind == 1:                        # ARRAY: [ elements ]
        result.append(91)
        body = serialize_list(head.inner)
        append_all(result, body)
        result.append(93)
    elif head.kind == 2:                        # OBJECT: { members }
        result.append(123)
        mbody = serialize_list(head.inner)
        append_all(result, mbody)
        result.append(125)
    else:                                       # MEMBER: "key": value
        result.append(34)
        append_escaped(result, head.text)
        result.append(34)
        result.append(58)
        result.append(32)
        vbody = serialize_list(head.inner)
        append_all(result, vbody)
    # tail: the rest of the sibling list, comma-and-space separated.
    if head.nxt is not None:
        result.append(44)
        result.append(32)
        rest = serialize_list(head.nxt)
        append_all(result, rest)
    Fold(Acc(j_pred(head), 1 / 2))
    Assert(ToSeq(result) == ser_list(head))
    return result
    # impl-end


def append_esc_char(result: List[int], c: int) -> None:
    """Append the interchange form of the single code point `c`. Output pinned
    to `esc_char`."""
    # pre-conditions-start
    Requires(Acc(list_pred(result)))
    # Total: one code point becomes a bounded, fixed-length form, so this
    # always finishes.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(result)))
    Ensures(ToSeq(result) == Old(ToSeq(result)) + esc_char(c))
    # post-conditions-end
    # impl-start
    if c == 34:
        result.append(92)
        result.append(34)
    elif c == 92:
        result.append(92)
        result.append(92)
    elif c == 8:
        result.append(92)
        result.append(98)
    elif c == 9:
        result.append(92)
        result.append(116)
    elif c == 10:
        result.append(92)
        result.append(110)
    elif c == 12:
        result.append(92)
        result.append(102)
    elif c == 13:
        result.append(92)
        result.append(114)
    elif 32 <= c and c <= 126:
        result.append(c)
    elif 0 <= c and c <= 65535:
        result.append(92)
        result.append(117)
        result.append(hex_digit(c // 4096))
        result.append(hex_digit((c // 256) % 16))
        result.append(hex_digit((c // 16) % 16))
        result.append(hex_digit(c % 16))
    elif 65536 <= c and c <= 1114111:
        hi = 55296 + (c - 65536) // 1024
        lo = 56320 + (c - 65536) % 1024
        result.append(92)
        result.append(117)
        result.append(hex_digit(hi // 4096))
        result.append(hex_digit((hi // 256) % 16))
        result.append(hex_digit((hi // 16) % 16))
        result.append(hex_digit(hi % 16))
        result.append(92)
        result.append(117)
        result.append(hex_digit(lo // 4096))
        result.append(hex_digit((lo // 256) % 16))
        result.append(hex_digit((lo // 16) % 16))
        result.append(hex_digit(lo % 16))
    else:
        result.append(c)
    # impl-end


def append_escaped(result: List[int], src: List[int]) -> None:
    """Append the interchange form of the token `src` (read-only): every code
    point of it replaced by that code point's own form. Output pinned to
    `esc_seq`."""
    # pre-conditions-start
    Requires(Acc(list_pred(result)))
    Requires(Acc(list_pred(src), 1 / 2))
    # Total: each code point of `src` is consumed once and turned into a
    # fixed-length form, so this always finishes.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(result)))
    Ensures(Acc(list_pred(src), 1 / 2))
    Ensures(ToSeq(result) == Old(ToSeq(result)) + esc_seq(ToSeq(src)))
    # post-conditions-end
    # impl-start
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(Acc(list_pred(src), 1 / 2))
        Invariant(0 <= i and i <= len(src))
        Invariant(ToSeq(result) == Old(ToSeq(result)) + esc_seq(ToSeq(src).take(i)))
        Invariant(MustTerminate(len(src) - i + 3))
        # invariants-end
        # one more code point extends the token's form by that code point's
        # own form: esc_seq of a prefix one longer.
        Assert(len(ToSeq(src).take(i + 1)) == i + 1)
        Assert(ToSeq(src).take(i + 1).take(i) == ToSeq(src).take(i))
        Assert(ToSeq(src).take(i + 1)[i] == ToSeq(src)[i])
        Assert(esc_seq(ToSeq(src).take(i + 1))
               == esc_seq(ToSeq(src).take(i)) + esc_char(ToSeq(src)[i]))
        append_esc_char(result, src[i])
        i = i + 1
    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
    # impl-end


def append_all(result: List[int], src: List[int]) -> None:
    """Append every element of `src` (read-only) onto `result`."""
    # pre-conditions-start
    Requires(Acc(list_pred(result)))
    Requires(Acc(list_pred(src), 1 / 2))
    # Total: each character of `src` is consumed once, so this always finishes.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(result)))
    Ensures(Acc(list_pred(src), 1 / 2))
    Ensures(ToSeq(result) == Old(ToSeq(result)) + ToSeq(src))
    # post-conditions-end
    # impl-start
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(Acc(list_pred(src), 1 / 2))
        Invariant(0 <= i and i <= len(src))
        Invariant(ToSeq(result) == Old(ToSeq(result)) + ToSeq(src).take(i))
        Invariant(MustTerminate(len(src) - i + 1))
        # invariants-end
        result.append(src[i])
        i = i + 1
    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
    # impl-end


def display_structured_value(value: JNode, empty: List[int], content: List[int],
                             present: bool, encodable: bool) -> List[int]:
    """The rendered dispatch. `value` is the structured value tree; `content`
    is the code points of the general-purpose display text produced for this
    value (used only on the fallback path); `empty` is the placeholder text.

    `present` is TRUE exactly when a value is stored at all, and is FALSE only
    when nothing is stored -- an empty stored value is still present.
    `encodable` is TRUE exactly when the value is both routed through the
    interchange encoder and expressible by it; a stored value that is empty is
    not routed through the encoder, so it takes the fallback arm, NOT the
    placeholder arm."""
    # pre-conditions-start
    # `value`, `empty`, `content` are inputs that are not mutated: fractional
    # permission only.
    Requires(Acc(j_pred(value), 1 / 2))
    Requires(Acc(list_pred(empty), 1 / 2))
    Requires(Acc(list_pred(content), 1 / 2))
    # Rendering is TOTAL: the display must ARRIVE, within a budget set by how
    # much value there is to walk. Every postcondition below is therefore a
    # claim about a result that is genuinely produced; a renderer that can walk
    # forever on an admissible value does not satisfy this contract.
    Requires(MustTerminate(j_size(value) + 4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(j_pred(value), 1 / 2))
    Ensures(Acc(list_pred(empty), 1 / 2))
    Ensures(Acc(list_pred(content), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A value that is not stored at all renders as the placeholder text,
    # unchanged. Being EMPTY is not being absent, so this arm does not claim
    # anything about an empty stored value.
    Ensures(Implies(not present, ToSeq(Result()) == ToSeq(empty)))
    # A stored value the encoder is given and can express renders as the
    # canonical interchange serialisation of its tree -- the STRUCTURAL
    # double-quote-delimited form. THIS is the discriminating clause: the
    # rendered output must be the full structural serialisation
    # (brackets/braces/keys/colons, U+0022 delimiters), never the
    # general-purpose display text.
    Ensures(Implies(present and encodable,
                    ToSeq(Result()) == interchange_form(value)))
    # EVERY other stored value -- not expressible by the encoder, or empty and
    # so never offered to it -- renders as the general-purpose display text
    # produced for that value, unchanged (no added delimiters).
    Ensures(Implies(present and not encodable,
                    ToSeq(Result()) == fallback_form(ToSeq(content))))
    # post-conditions-end
    # impl-start
    if not present:
        result = []  # type: List[int]
        j = 0
        while j < len(empty):
            # invariants-start
            Invariant(Acc(list_pred(empty), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= j and j <= len(empty))
            Invariant(ToSeq(result) == ToSeq(empty).take(j))
            Invariant(MustTerminate(len(empty) - j + 1))
            # invariants-end
            result.append(empty[j])
            j = j + 1
        return result

    if encodable:
        # the interchange encoding: the structural serialisation of the tree.
        return serialize(value)

    # fallback: the general-purpose display text for this value, returned
    # unchanged (a fresh owned copy of it; no delimiters are added).
    out2 = []  # type: List[int]
    m = 0
    while m < len(content):
        # invariants-start
        Invariant(Acc(list_pred(content), 1 / 2))
        Invariant(Acc(list_pred(out2)))
        Invariant(0 <= m and m <= len(content))
        Invariant(ToSeq(out2) == ToSeq(content).take(m))
        Invariant(MustTerminate(len(content) - m + 1))
        # invariants-end
        out2.append(content[m])
        m = m + 1
    Assert(ToSeq(content).take(len(content)) == ToSeq(content))
    return out2
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**ENVIRONMENT:** package is not installed in any env; ran everything as `PYTHONPATH=src SBU_BENCHMARK_DIR=benchmark-verified python -m swebench_unified.adversary...` from the repo root. Verifier caps raised (SBU_ATTACK_VERIFY_TIMEOUT=900 / SBN_VERIFY_TIMEOUT=900) so no verdict below is a host cap; attack verifications were run CONCURRENTLY 3 at a time (JVM+Z3 each) and every one returned a genuine verifier verdict, never exit -15/124.

**SAME-SPEC:** all 12 attacks + the positive control return exit 0 from `adversary same-spec` (spec view byte-identical). Every edit is confined to an `# impl-start`..`# impl-end` region; axioms/@Pure/Requires/Ensures untouched. Generator kept at gen.py (it asserts each anchor occurs exactly once, so no silent no-op edits).

**POSITIVE CONTROL:** control.py (= frozen model.py) -> CANDIDATE-COUNTEREXAMPLE i.e. shares spec AND VERIFIES (70.2s). The spec is satisfiable by the reference impl.

COMMAND FORM (all 12 + control): `python -m swebench_unified.adversary weakness nagini django__django-12308 atk_N.py`

### PER-ATTACK RESULT (path / defect class / observed):
* atk_1.py  PREPATCH BUG re-encoded: the whole `if encodable: return serialize(value)` arm deleted, so every present value takes the host printout (exactly the pre-patch display_for_field, which had no structured-data branch) -> exit 2, verification failed. prepatch_reproduced=True.
* atk_2.py  PARTIAL DOMAIN: only a STRING root (kind==0) is routed to the encoder; ARRAY/OBJECT roots fall to the printout. Would still satisfy the F2P 'a'->"a" case -> exit 2, verification failed.
* atk_3.py  BOUNDARY in the interchange alphabet: printable band widened to 32<=c<=127, so U+007F (DEL) is spliced raw instead of  -> exit 2, verification failed. esc_char's band is pinned exactly.
* atk_4.py  CONTROL-FLOW EFFECT / DIVERGENCE: the encodable arm spins forever (`while spin >= 0`) with fully-annotated loop invariants, so every postcondition is vacuously true of the runs that arrive (none do) -> exit 2, verification failed. The METHOD-level MustTerminate(j_size(value)+4) rejects it; the annotated exit is unreachable.
* atk_5.py  UNGROUNDED-ORACLE ECHO: serialize(value) then hand back a re-copied buffer via append_all -> exit 0, CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 66.9s). PROTOCOL DISCHARGED: faithful patch materialized (patch_atk5.diff, built by diffing against the real base-commit django/contrib/admin/utils.py extracted from the upstream repository at 2e0f04507b17362239ba49830d26fec504d46978) and RUN through the official harness -> resolved=True, completed=True. RESOLVES => echo, not a weakness.
* atk_6.py  SEPARATOR DRIFT: sibling separator is a bare comma, so ['a','b'] renders ["a","b"] not ["a", "b"] -> exit 2, verification failed.
* atk_7.py  EMPTINESS CONFLATED WITH ABSENCE: the non-encodable arm returns the PLACEHOLDER, so falsy stored values ([], {}, '', 0, False) render as the dash -> exit 2, verification failed. The absence!=emptiness clause is load-bearing.
* atk_8.py  TOKEN ALPHABET CASE: the \uXXXX escape emits UPPERCASE hex digits (55+d inlined instead of hex_digit's 87+d) on the BMP arm -> exit 2, verification failed.
* atk_9.py  MEMBER LAYOUT DRIFT: object-member separator loses its space ("k":v instead of "k": v) -> exit 2, verification failed.
* atk_10.py DISPATCH REORDER: the encoder is consulted BEFORE the absence test, so an absent-but-encodable input renders as the interchange form rather than the placeholder -> exit 2, verification failed.
* atk_11.py BRACKET SWAP (direct F2P divergence): ARRAY braced and OBJECT bracketed, applied consistently at BOTH dispatch sites (serialize and serialize_list), so ['a','b'] -> {"a", "b"} -> exit 2, verification failed.
* atk_12.py DELIMITER SWAP -- the single-vs-double-quote confusion the whole change is ABOUT: every string token and key laid down in the host's single quote U+0027 instead of the interchange U+0022 (all four delimiter sites), so 'a' -> 'a' not "a" -> exit 2, verification failed.

A-LEG AUDIT (the legs G-CONF cannot mechanically reach). BOTH A-references INDEPENDENTLY re-derived by me; I did not run or trust the bundle's own axiom_check.py for these conclusions.
* A7 interchange_form <-> JSONField.get_prep_value == json.dumps(value) (encoder=None): I hand-transliterated model.py's ENTIRE pure region (node_body/ser_list/esc_seq/esc_char/hex_form/hex_digit, incl. the MEMBER "key": value layout) into a7_audit.py and diffed it against the real json.dumps over: the 3 encodable F2P values; ALL 1,114,112 code points as a single-token value; ALL 1,114,112 as an object KEY inside a nested value; 24 boundary escape classes as token/key/nested; and 20,000 randomized nested dict/list/string values with tokens drawn from the full code point range. RESULT: 2,248,299 checks, ZERO divergences (RC=0). The escape fold is exact across the whole domain -- U+0022, U+005C, the five named controls, U+007F, the C1 band, lone surrogates, and the astral planes via surrogate-pair halves. There is NO unencoded token-alphabet restriction, and atk_3/atk_8/atk_12 confirm the spec actively REJECTS band-widening, hex-case and delimiter drift.
* A8 fallback_form <-> display_for_value: audited IN the pinned eval container (swebench/sweb.eval.x86_64.django_1776_django-12308) with the GOLD PATCH APPLIED, harness a8_audit.py, RC=0, 0 divergences. inspect.getsource confirmed the JSONField/get_prep_value branch is really present in the tree under test. Checked: all 4 F2P values + the added None line agree with the test's expected display; json.dumps genuinely raises TypeError on the tuple-keyed dict; the identity pass-through fallback_form(text)==text holds; `content` really carries display_for_value's OWN output and not str(value) -- 6/6 JOIN-ARM roots ([{('x','y'):'z'}], ['a',{('x','y'):'z'}], [b'raw'], [set()], the 1-tuple, [1,2,{('k',):'v'}]) have real text != str(value) AND display_for_field routes them to exactly that text; the falsy STORED values take the fallback not the placeholder ([]->'', ''->'', {}->'{}', 0->'0', False->'False', ()->'', 0.0->'0.0'); the U+0027-vs-U+0022 delimiter contrast holds; plus 30,000 full-alphabet non-encodable fuzz values against the REAL callee with 0 divergences. So mapping.md §3.2's claim is correct, and atk_7 shows the spec enforces the emptiness!=absence half of it.
* A4/A5 three-outcome refinement re-derived from the BASE tree directly (`git show 2e0f04507b17362239ba49830d26fec504d46978:django/contrib/admin/utils.py`): the `elif value is None` arm at line 389 sits BEFORE the FileField/JSONField `and value` guards, so a non-None falsy value that fails the truthiness guard cannot reach the placeholder and falls THROUGH to display_for_value at the final else. Three outcomes, matching the model's three arms. Correct as documented.

**REFINEMENT.MD LEG AUDIT:** 8 legs, A1-A5 = R, A6 = I + R, A7 = A-reference, A8 = A-reference. Tag census: 5 R, 1 I+R, 2 A-reference, 0 A-consumed, NO kind-3 (unexpressible-changed-op) leg. model.py contains 0 occurrences of @ContractOnly and 0 of Assume/Refute, and meta.json's axioms list is empty -- so §B's "no consumed axioms" claim is literally true and there is no dead or mislabelled axiom. Both A-legs' correspondence to the real callees holds as independently audited above. §C's verify=>resolved argument is sound given those two A-references plus the R/I legs.

**CONCLUSION:** 12 attacks run to genuine verifier verdicts, 11 rejected; the one verifying attack's materialized faithful patch RESOLVES under the official harness (executed, not speculated), so it is an echo. Positive control verifies. Both A-legs independently confirmed against the real callees (2,248,299 + 30,000+ checks, zero divergences). Verdict SOUND (advisory; the runner re-runs these artifacts).

OUT-OF-SCOPE FLAG for whoever regates: meta.json now records G-PANEL-2 status=pass, consistent with my findings -- the historical raw-splice/no-escape-fold defect is genuinely closed in the frozen model.py (my full-domain sweep plus atk_3/atk_8/atk_12 all confirm the esc_seq/esc_char fold is present and load-bearing).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.py` |

**Non-vacuity.** The positive control `control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. 12 same-spec attacks run to a real verifier verdict; 11 REJECTED. The single CANDIDATE (atk_5, ungrounded-oracle echo: serialize() then a second-buffer re-copy) had its faithful refined patch MATERIALIZED (patch_atk5.diff) and RUN through the official harness -- run_resolve('django__django-12308', patch, run_id='sbu-eq-s7chsrpu-atk5') -> resolved=True, completed=True. It RESOLVES, so per architecture.md §6 it is a behaviourally-correct alternative implementation (an echo of the reference), NOT a spec weakness, and does not fail the gate. No verify-but-wrong witness exists among these probes: verify=>correct is not broken for this bundle.
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 12 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `control.py`

```python
"""Twin-artifact model for django__django-12308.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A stored structured-data value rendered as text must be shown in its
  CANONICAL DATA-INTERCHANGE encoding, not in the host language's object
  printout. A structured value is a tree: a string token, an ordered array of
  values, or an object whose members are (string-key, value) pairs.

  The interchange encoding serialises that tree STRUCTURALLY:

    * a string token is delimited by the double-quote delimiter U+0022 ( " ),
      so the value  a  renders as  "a" ; INSIDE that pair the token's own code
      points are written in the interchange alphabet rather than spliced in
      raw -- the delimiter U+0022 and the escape character U+005C are each
      written as U+005C followed by themselves, the five control positions
      U+0008, U+0009, U+000A, U+000C, U+000D as U+005C followed by b, t, n, f,
      r, and every other code point outside the printable band
      U+0020..U+007E as the six-code-point form U+005C, U+0075 and four
      lowercase hexadecimal digits (a code point above U+FFFF as the pair of
      such forms for its two surrogate halves); the printable ones stand for
      themselves;
    * an array renders as its elements, comma-and-space separated, between
      square brackets:  [ e1, e2, ... ] ;
    * an object renders as its members, comma-and-space separated, between
      curly braces, each member a double-quoted key, a colon-space, then the
      member value:  { "k1": v1, "k2": v2, ... } .

  So the value  {a: {b: c}}  renders as  {"a": {"b": "c"}}  and the value
  [a, b]  renders as  ["a", "b"] : the structure is laid out exactly, with
  every string token and every key delimited by the double quote U+0022.

  Concretely, for a structured value `value`:

    - a value that is ABSENT -- nothing is stored for it at all -- renders as
      the supplied placeholder text. ABSENCE is not the same thing as
      EMPTINESS: a value that IS stored but is itself empty is not absent, and
      does NOT render as the placeholder;
    - a value that is routed through the interchange encoder, and that the
      encoder can express, renders as its canonical interchange encoding: the
      STRUCTURAL serialisation above (`interchange_form`);
    - EVERY other stored value -- one whose contents the encoder cannot
      express, and equally one that is itself empty and so is never routed
      through the encoder at all -- renders as the general-purpose display
      text supplied for that value (`fallback_form`), shown AS-IS: the
      renderer adds no delimiters of its own. Where that fallback text shows
      string tokens they already carry the host language's single-quote
      U+0027 delimiters internally.

  The discriminating guarantee is STRUCTURAL: a value the encoder can express is
  rendered as the full interchange serialisation of its tree (brackets, braces,
  key/colon layout, double-quote U+0022 delimiters), never as the general-purpose
  display text. A renderer that merely wraps the whole printed value in one pair
  of delimiters does NOT satisfy this: the array  [a, b]  must render as
  ["a", "b"] , not as a single wrapped token.

  Rendering is moreover a TOTAL operation. For every admissible structured
  value the renderer must actually PRODUCE the text described above and hand it
  back to whoever asked for it: the guarantees above are claims about a result
  that genuinely ARRIVES, not merely about the runs that happen to arrive.
  Displaying a stored value is a bounded walk of that value's own contents --
  every step of the walk moves onto a strictly smaller part of the value (into
  something it contains, or on to the next item beside it) and each character of
  a token is consumed once -- so the walk always runs out of value to visit and
  the display appears. A renderer that can walk forever on some admissible
  value, so that the display never appears at all, does NOT meet this
  specification, no matter how its never-reached exit is annotated.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); a structured value is modelled as a small recursive node tree
(`JNode`) in sibling/inner linked form. The interchange encoding is modelled
DEEPLY as a single self-recursive serialiser fold over that tree
(`interchange_form`). The general-purpose display fallback is a SEPARATE
renderer with its own dispatch (it lays a sequence out element-by-element
rather than printing it as one object), so the model does NOT re-derive its
text from the value: `fallback_form` is the identity on `content`, the text
THAT renderer produced for this value, which the renderer then hands back with
no delimiters of its own added. Both are validated == their real callees
out-of-band by axiom_check.py (G-AX) on the real structured values, never
consumed as axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. The two callees the rendered branch invokes are modelled
# DEEPLY: the interchange encoder as a single self-recursive serialiser fold
# over the value tree (interchange_form), and the general-purpose display
# renderer as the text it produced passed through unchanged (fallback_form =
# identity; the renderer adds no delimiters of its own). That renderer has its
# own per-shape dispatch, so its text is CARRIED in `content` rather than
# re-derived from the value here. They are validated == their real callees
# out-of-band by axiom_check.py (G-AX) as A-references on the real structured
# values, never consumed here.
# axioms-end


# pure-start
class JNode:
    """One node in a structured-value tree, in sibling/inner linked form.

    `kind`:
        0 = STRING token  -- contents in `text`;
        1 = ARRAY         -- elements are the sibling list at `inner`;
        2 = OBJECT        -- members are the sibling list at `inner`;
        3 = MEMBER        -- one object member: KEY in `text`, VALUE is the
                             single node at `inner` (the value node carries no
                             siblings, i.e. its own `nxt` is None).
    `text`: STRING contents (kind 0) or MEMBER key (kind 3).
    `inner`: head of the contained sibling list (ARRAY elements / OBJECT
             members) or the member value (kind 3); unused for a STRING.
    `nxt`: the next sibling in the current element / member list (None = last).
    """

    def __init__(self, kind: int, text: List[int], inner: 'Optional[JNode]',
                 nxt: 'Optional[JNode]') -> None:
        Requires(Acc(list_pred(text)))
        Requires(Implies(inner is not None, Acc(j_pred(inner))))
        Requires(Implies(nxt is not None, Acc(j_pred(nxt))))
        # Assembling one node is a single bounded step; measure 1 sits strictly
        # below every walk budget below, so a walk may build a node.
        Requires(MustTerminate(1))
        Ensures(Acc(j_pred(self)))
        # A value assembled with nothing inside it and nothing beside it is one
        # single part, so a walk of it has exactly one step to take.
        Ensures(Implies(inner is None and nxt is None, j_size(self) == 1))
        self.kind = kind
        self.text = text
        self.inner = inner
        self.nxt = nxt
        Fold(j_pred(self))


@Predicate
def j_pred(n: JNode) -> bool:
    return (Acc(n.kind) and Acc(n.text) and Acc(n.inner) and Acc(n.nxt) and
            list_pred(n.text) and
            Implies(n.inner is not None, j_pred(n.inner)) and
            Implies(n.nxt is not None, j_pred(n.nxt)))


@Pure
def empty_seq() -> PSeq[int]:
    return PSeq(0).take(0)


@Pure
def j_size(n: 'Optional[JNode]') -> int:
    """How much VALUE there is to walk at `n`: the number of parts the
    structured value (or the run of values beside it) is made of; 0 when there
    is nothing there. Every step a renderer takes moves onto something the
    current part contains, or on to the next part beside it, and both are
    strictly smaller by this count -- so this is the budget within which the
    display has to appear."""
    Requires(Implies(n is not None, Acc(j_pred(n), 1 / 4)))
    Ensures(Result() >= 0)
    Ensures(Implies(n is None, Result() == 0))
    Ensures(Implies(n is not None, Result() > 0))
    if n is None:
        return 0
    return Unfolding(Acc(j_pred(n), 1 / 4),
                     1 + j_size(n.inner) + j_size(n.nxt))


@Pure
def hex_digit(d: int) -> int:
    """The lowercase hexadecimal digit for 0 <= d < 16, as a code point."""
    return 48 + d if d < 10 else 87 + d


@Pure
def hex_form(c: int) -> PSeq[int]:
    """The six-code-point interchange form of one 16-bit unit: the escape
    character U+005C, the letter u (U+0075), then the unit's four lowercase
    hexadecimal digits, most significant first."""
    return (PSeq(92, 117) + PSeq(hex_digit(c // 4096))
            + PSeq(hex_digit((c // 256) % 16))
            + PSeq(hex_digit((c // 16) % 16)) + PSeq(hex_digit(c % 16)))


@Pure
def esc_char(c: int) -> PSeq[int]:
    """The interchange form of ONE code point of a string token or of a key.

    The interchange alphabet is not the host alphabet, so a token's code
    points are not spliced in raw between the delimiters: the delimiter U+0022
    and the escape character U+005C are each written as U+005C followed by
    themselves; the five control positions U+0008, U+0009, U+000A, U+000C and
    U+000D have their own two-code-point forms (U+005C followed by b, t, n, f
    and r); every other code point outside the printable band U+0020..U+007E
    is written in the six-code-point `hex_form`, and one above U+FFFF as the
    two hex forms of its surrogate halves. The printable code points stand for
    themselves. An int outside U+0000..U+10FFFF is no code point at all, so
    there is no character for it to stand for and it is left as it is."""
    if c == 34:
        return PSeq(92, 34)
    if c == 92:
        return PSeq(92, 92)
    if c == 8:
        return PSeq(92, 98)
    if c == 9:
        return PSeq(92, 116)
    if c == 10:
        return PSeq(92, 110)
    if c == 12:
        return PSeq(92, 102)
    if c == 13:
        return PSeq(92, 114)
    if 32 <= c and c <= 126:
        return PSeq(c)
    if 0 <= c and c <= 65535:
        return hex_form(c)
    if 65536 <= c and c <= 1114111:
        return (hex_form(55296 + (c - 65536) // 1024)
                + hex_form(56320 + (c - 65536) % 1024))
    return PSeq(c)


@Pure
def esc_seq(s: PSeq[int]) -> PSeq[int]:
    """The interchange form of a WHOLE token (or key): each of its code points
    replaced by that code point's own form, in order. The empty token has the
    empty form. This is what sits between the two U+0022 delimiters -- the
    token's code points do NOT pass through unchanged."""
    if len(s) == 0:
        return empty_seq()
    return esc_seq(s.take(len(s) - 1)) + esc_char(s[len(s) - 1])


@Pure
def node_body(head: JNode) -> PSeq[int]:
    """Interchange serialisation of the SINGLE node `head` (no sibling
    separator). Dispatched on kind; the contained sibling list is serialised by
    `ser_list` on `head.inner` (a strictly smaller predicate, so this recurses
    only downward through `Unfolding`)."""
    Requires(Acc(j_pred(head), 1 / 4))
    return Unfolding(
        Acc(j_pred(head), 1 / 4),
        # STRING: "text"
        PSeq(34) + esc_seq(ToSeq(head.text)) + PSeq(34) if head.kind == 0
        # ARRAY: [ elements ]
        else (PSeq(91) + ser_list(head.inner) + PSeq(93) if head.kind == 1
              # OBJECT: { members }
              else (PSeq(123) + ser_list(head.inner) + PSeq(125) if head.kind == 2
                    # MEMBER: "key": value
                    else PSeq(34) + esc_seq(ToSeq(head.text)) + PSeq(34)
                    + PSeq(58, 32) + ser_list(head.inner))))


@Pure
def ser_list(head: Optional[JNode]) -> PSeq[int]:
    """Interchange serialisation of the sibling list starting at `head`: each
    node's body, comma-and-space (44,32) separated, with no trailing separator.
    A member value node (kind 3's `inner`) carries no siblings, so `ser_list` on
    it yields exactly that value's body. The head's body is dispatched INLINE
    (same as `node_body`) so that ONE unfold of `j_pred(head)` covers both the
    head body and the tail; the only recursion is `ser_list` on the sub-nodes
    `head.inner` and `head.nxt` (strictly smaller predicates)."""
    Requires(Implies(head is not None, Acc(j_pred(head), 1 / 4)))
    if head is None:
        return empty_seq()
    return Unfolding(
        Acc(j_pred(head), 1 / 4),
        (PSeq(34) + esc_seq(ToSeq(head.text)) + PSeq(34) if head.kind == 0
         else (PSeq(91) + ser_list(head.inner) + PSeq(93) if head.kind == 1
               else (PSeq(123) + ser_list(head.inner) + PSeq(125) if head.kind == 2
                     else PSeq(34) + esc_seq(ToSeq(head.text)) + PSeq(34)
                     + PSeq(58, 32) + ser_list(head.inner)))) +
        (empty_seq() if head.nxt is None
         else PSeq(44, 32) + ser_list(head.nxt)))


@Pure
def interchange_form(node: Optional[JNode]) -> PSeq[int]:
    """Canonical interchange serialisation of a structured value (the deep
    model of `json.dumps`): the single-node serialisation of the tree rooted at
    `node` (the value carries no siblings at the top, so this is `node_body`)."""
    Requires(Implies(node is not None, Acc(j_pred(node), 1 / 4)))
    if node is None:
        return empty_seq()
    return node_body(node)


@Pure
def fallback_form(content: PSeq[int]) -> PSeq[int]:
    """The general-purpose display text for a value, UNCHANGED. Whenever the
    renderer does not route a stored value through the interchange encoder --
    because the encoder cannot express it, or because the value is itself empty
    and so is never offered to the encoder -- the display is whatever that
    general-purpose renderer produced for the value, handed back as-is with no
    delimiters added. That renderer dispatches on the value's own shape (a
    sequence is laid out element-by-element, not printed as a single object),
    so its text is CARRIED here in `content` rather than recomputed from the
    value tree; where it shows string tokens they are single-quote U+0027
    delimited, in contrast to the interchange encoding's structural
    double-quote U+0022."""
    return content
# pure-end


def serialize(node: JNode) -> List[int]:
    """Verified recursive serialiser: builds the interchange encoding of the
    single value `node` (the deep-model skeleton of the canonical interchange
    serialiser), each token and key laid down in its interchange form
    (`esc_seq`) between the U+0022 delimiters. Output pinned to
    `interchange_form` / `node_body`."""
    # pre-conditions-start
    Requires(Acc(j_pred(node), 1 / 2))
    # Total, not merely partial: the encoding must ARRIVE. The walk is bounded
    # by how much value there is to walk, so every descent must land on a
    # strictly smaller part of the value.
    Requires(MustTerminate(j_size(node) + 3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(j_pred(node), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == node_body(node))
    Ensures(ToSeq(Result()) == interchange_form(node))
    # post-conditions-end
    # impl-start
    Unfold(Acc(j_pred(node), 1 / 2))
    if node.kind == 0:                          # STRING: "text"
        out = [34]  # type: List[int]
        append_escaped(out, node.text)
        out.append(34)
        Fold(Acc(j_pred(node), 1 / 2))
        Assert(ToSeq(out) == node_body(node))
        return out
    if node.kind == 1:                          # ARRAY: [ elements ]
        body = serialize_list(node.inner)
        result = [91]  # type: List[int]
        append_all(result, body)
        result.append(93)
        Fold(Acc(j_pred(node), 1 / 2))
        Assert(ToSeq(result) == node_body(node))
        return result
    if node.kind == 2:                          # OBJECT: { members }
        mbody = serialize_list(node.inner)
        result2 = [123]  # type: List[int]
        append_all(result2, mbody)
        result2.append(125)
        Fold(Acc(j_pred(node), 1 / 2))
        Assert(ToSeq(result2) == node_body(node))
        return result2
    # MEMBER: "key": value
    result3 = [34]  # type: List[int]
    append_escaped(result3, node.text)
    result3.append(34)
    result3.append(58)
    result3.append(32)
    vbody = serialize_list(node.inner)
    append_all(result3, vbody)
    Fold(Acc(j_pred(node), 1 / 2))
    Assert(ToSeq(result3) == node_body(node))
    return result3
    # impl-end


def serialize_list(head: Optional[JNode]) -> List[int]:
    """Verified serialiser for a sibling list: each node's body, comma-and-space
    separated. Output pinned to `ser_list`."""
    # pre-conditions-start
    Requires(Implies(head is not None, Acc(j_pred(head), 1 / 2)))
    # Total, not merely partial: the encoding of the run of values must ARRIVE,
    # within the amount of value left to walk.
    Requires(MustTerminate(j_size(head) + 3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Implies(head is not None, Acc(j_pred(head), 1 / 2)))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == ser_list(head))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    if head is None:
        Assert(ToSeq(result) == ser_list(head))
        return result
    Unfold(Acc(j_pred(head), 1 / 2))
    # head body, dispatched INLINE (mirrors ser_list / node_body), recursing
    # into serialize_list on the sub-nodes only -- all while `head` is unfolded.
    if head.kind == 0:                          # STRING: "text"
        result.append(34)
        append_escaped(result, head.text)
        result.append(34)
    elif head.kind == 1:                        # ARRAY: [ elements ]
        result.append(91)
        body = serialize_list(head.inner)
        append_all(result, body)
        result.append(93)
    elif head.kind == 2:                        # OBJECT: { members }
        result.append(123)
        mbody = serialize_list(head.inner)
        append_all(result, mbody)
        result.append(125)
    else:                                       # MEMBER: "key": value
        result.append(34)
        append_escaped(result, head.text)
        result.append(34)
        result.append(58)
        result.append(32)
        vbody = serialize_list(head.inner)
        append_all(result, vbody)
    # tail: the rest of the sibling list, comma-and-space separated.
    if head.nxt is not None:
        result.append(44)
        result.append(32)
        rest = serialize_list(head.nxt)
        append_all(result, rest)
    Fold(Acc(j_pred(head), 1 / 2))
    Assert(ToSeq(result) == ser_list(head))
    return result
    # impl-end


def append_esc_char(result: List[int], c: int) -> None:
    """Append the interchange form of the single code point `c`. Output pinned
    to `esc_char`."""
    # pre-conditions-start
    Requires(Acc(list_pred(result)))
    # Total: one code point becomes a bounded, fixed-length form, so this
    # always finishes.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(result)))
    Ensures(ToSeq(result) == Old(ToSeq(result)) + esc_char(c))
    # post-conditions-end
    # impl-start
    if c == 34:
        result.append(92)
        result.append(34)
    elif c == 92:
        result.append(92)
        result.append(92)
    elif c == 8:
        result.append(92)
        result.append(98)
    elif c == 9:
        result.append(92)
        result.append(116)
    elif c == 10:
        result.append(92)
        result.append(110)
    elif c == 12:
        result.append(92)
        result.append(102)
    elif c == 13:
        result.append(92)
        result.append(114)
    elif 32 <= c and c <= 126:
        result.append(c)
    elif 0 <= c and c <= 65535:
        result.append(92)
        result.append(117)
        result.append(hex_digit(c // 4096))
        result.append(hex_digit((c // 256) % 16))
        result.append(hex_digit((c // 16) % 16))
        result.append(hex_digit(c % 16))
    elif 65536 <= c and c <= 1114111:
        hi = 55296 + (c - 65536) // 1024
        lo = 56320 + (c - 65536) % 1024
        result.append(92)
        result.append(117)
        result.append(hex_digit(hi // 4096))
        result.append(hex_digit((hi // 256) % 16))
        result.append(hex_digit((hi // 16) % 16))
        result.append(hex_digit(hi % 16))
        result.append(92)
        result.append(117)
        result.append(hex_digit(lo // 4096))
        result.append(hex_digit((lo // 256) % 16))
        result.append(hex_digit((lo // 16) % 16))
        result.append(hex_digit(lo % 16))
    else:
        result.append(c)
    # impl-end


def append_escaped(result: List[int], src: List[int]) -> None:
    """Append the interchange form of the token `src` (read-only): every code
    point of it replaced by that code point's own form. Output pinned to
    `esc_seq`."""
    # pre-conditions-start
    Requires(Acc(list_pred(result)))
    Requires(Acc(list_pred(src), 1 / 2))
    # Total: each code point of `src` is consumed once and turned into a
    # fixed-length form, so this always finishes.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(result)))
    Ensures(Acc(list_pred(src), 1 / 2))
    Ensures(ToSeq(result) == Old(ToSeq(result)) + esc_seq(ToSeq(src)))
    # post-conditions-end
    # impl-start
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(Acc(list_pred(src), 1 / 2))
        Invariant(0 <= i and i <= len(src))
        Invariant(ToSeq(result) == Old(ToSeq(result)) + esc_seq(ToSeq(src).take(i)))
        Invariant(MustTerminate(len(src) - i + 3))
        # invariants-end
        # one more code point extends the token's form by that code point's
        # own form: esc_seq of a prefix one longer.
        Assert(len(ToSeq(src).take(i + 1)) == i + 1)
        Assert(ToSeq(src).take(i + 1).take(i) == ToSeq(src).take(i))
        Assert(ToSeq(src).take(i + 1)[i] == ToSeq(src)[i])
        Assert(esc_seq(ToSeq(src).take(i + 1))
               == esc_seq(ToSeq(src).take(i)) + esc_char(ToSeq(src)[i]))
        append_esc_char(result, src[i])
        i = i + 1
    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
    # impl-end


def append_all(result: List[int], src: List[int]) -> None:
    """Append every element of `src` (read-only) onto `result`."""
    # pre-conditions-start
    Requires(Acc(list_pred(result)))
    Requires(Acc(list_pred(src), 1 / 2))
    # Total: each character of `src` is consumed once, so this always finishes.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(result)))
    Ensures(Acc(list_pred(src), 1 / 2))
    Ensures(ToSeq(result) == Old(ToSeq(result)) + ToSeq(src))
    # post-conditions-end
    # impl-start
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(Acc(list_pred(src), 1 / 2))
        Invariant(0 <= i and i <= len(src))
        Invariant(ToSeq(result) == Old(ToSeq(result)) + ToSeq(src).take(i))
        Invariant(MustTerminate(len(src) - i + 1))
        # invariants-end
        result.append(src[i])
        i = i + 1
    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
    # impl-end


def display_structured_value(value: JNode, empty: List[int], content: List[int],
                             present: bool, encodable: bool) -> List[int]:
    """The rendered dispatch. `value` is the structured value tree; `content`
    is the code points of the general-purpose display text produced for this
    value (used only on the fallback path); `empty` is the placeholder text.

    `present` is TRUE exactly when a value is stored at all, and is FALSE only
    when nothing is stored -- an empty stored value is still present.
    `encodable` is TRUE exactly when the value is both routed through the
    interchange encoder and expressible by it; a stored value that is empty is
    not routed through the encoder, so it takes the fallback arm, NOT the
    placeholder arm."""
    # pre-conditions-start
    # `value`, `empty`, `content` are inputs that are not mutated: fractional
    # permission only.
    Requires(Acc(j_pred(value), 1 / 2))
    Requires(Acc(list_pred(empty), 1 / 2))
    Requires(Acc(list_pred(content), 1 / 2))
    # Rendering is TOTAL: the display must ARRIVE, within a budget set by how
    # much value there is to walk. Every postcondition below is therefore a
    # claim about a result that is genuinely produced; a renderer that can walk
    # forever on an admissible value does not satisfy this contract.
    Requires(MustTerminate(j_size(value) + 4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(j_pred(value), 1 / 2))
    Ensures(Acc(list_pred(empty), 1 / 2))
    Ensures(Acc(list_pred(content), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A value that is not stored at all renders as the placeholder text,
    # unchanged. Being EMPTY is not being absent, so this arm does not claim
    # anything about an empty stored value.
    Ensures(Implies(not present, ToSeq(Result()) == ToSeq(empty)))
    # A stored value the encoder is given and can express renders as the
    # canonical interchange serialisation of its tree -- the STRUCTURAL
    # double-quote-delimited form. THIS is the discriminating clause: the
    # rendered output must be the full structural serialisation
    # (brackets/braces/keys/colons, U+0022 delimiters), never the
    # general-purpose display text.
    Ensures(Implies(present and encodable,
                    ToSeq(Result()) == interchange_form(value)))
    # EVERY other stored value -- not expressible by the encoder, or empty and
    # so never offered to it -- renders as the general-purpose display text
    # produced for that value, unchanged (no added delimiters).
    Ensures(Implies(present and not encodable,
                    ToSeq(Result()) == fallback_form(ToSeq(content))))
    # post-conditions-end
    # impl-start
    if not present:
        result = []  # type: List[int]
        j = 0
        while j < len(empty):
            # invariants-start
            Invariant(Acc(list_pred(empty), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= j and j <= len(empty))
            Invariant(ToSeq(result) == ToSeq(empty).take(j))
            Invariant(MustTerminate(len(empty) - j + 1))
            # invariants-end
            result.append(empty[j])
            j = j + 1
        return result

    if encodable:
        # the interchange encoding: the structural serialisation of the tree.
        return serialize(value)

    # fallback: the general-purpose display text for this value, returned
    # unchanged (a fresh owned copy of it; no delimiters are added).
    out2 = []  # type: List[int]
    m = 0
    while m < len(content):
        # invariants-start
        Invariant(Acc(list_pred(content), 1 / 2))
        Invariant(Acc(list_pred(out2)))
        Invariant(0 <= m and m <= len(content))
        Invariant(ToSeq(out2) == ToSeq(content).take(m))
        Invariant(MustTerminate(len(content) - m + 1))
        # invariants-end
        out2.append(content[m])
        m = m + 1
    Assert(ToSeq(content).take(len(content)) == ToSeq(content))
    return out2
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**ENVIRONMENT:** package is not installed in any env; ran everything as `PYTHONPATH=src SBU_BENCHMARK_DIR=benchmark-verified python -m swebench_unified.adversary...` from the repo root. Verifier caps raised (SBU_ATTACK_VERIFY_TIMEOUT=900 / SBN_VERIFY_TIMEOUT=900) so no verdict below is a host cap; attack verifications were run CONCURRENTLY 3 at a time (JVM+Z3 each) and every one returned a genuine verifier verdict, never exit -15/124.

**SAME-SPEC:** all 12 attacks + the positive control return exit 0 from `adversary same-spec` (spec view byte-identical). Every edit is confined to an `# impl-start`..`# impl-end` region; axioms/@Pure/Requires/Ensures untouched. Generator kept at gen.py (it asserts each anchor occurs exactly once, so no silent no-op edits).

**POSITIVE CONTROL:** control.py (= frozen model.py) -> CANDIDATE-COUNTEREXAMPLE i.e. shares spec AND VERIFIES (70.2s). The spec is satisfiable by the reference impl.

COMMAND FORM (all 12 + control): `python -m swebench_unified.adversary weakness nagini django__django-12308 atk_N.py`

### PER-ATTACK RESULT (path / defect class / observed):
* atk_1.py  PREPATCH BUG re-encoded: the whole `if encodable: return serialize(value)` arm deleted, so every present value takes the host printout (exactly the pre-patch display_for_field, which had no structured-data branch) -> exit 2, verification failed. prepatch_reproduced=True.
* atk_2.py  PARTIAL DOMAIN: only a STRING root (kind==0) is routed to the encoder; ARRAY/OBJECT roots fall to the printout. Would still satisfy the F2P 'a'->"a" case -> exit 2, verification failed.
* atk_3.py  BOUNDARY in the interchange alphabet: printable band widened to 32<=c<=127, so U+007F (DEL) is spliced raw instead of  -> exit 2, verification failed. esc_char's band is pinned exactly.
* atk_4.py  CONTROL-FLOW EFFECT / DIVERGENCE: the encodable arm spins forever (`while spin >= 0`) with fully-annotated loop invariants, so every postcondition is vacuously true of the runs that arrive (none do) -> exit 2, verification failed. The METHOD-level MustTerminate(j_size(value)+4) rejects it; the annotated exit is unreachable.
* atk_5.py  UNGROUNDED-ORACLE ECHO: serialize(value) then hand back a re-copied buffer via append_all -> exit 0, CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 66.9s). PROTOCOL DISCHARGED: faithful patch materialized (patch_atk5.diff, built by diffing against the real base-commit django/contrib/admin/utils.py extracted from the upstream repository at 2e0f04507b17362239ba49830d26fec504d46978) and RUN through the official harness -> resolved=True, completed=True. RESOLVES => echo, not a weakness.
* atk_6.py  SEPARATOR DRIFT: sibling separator is a bare comma, so ['a','b'] renders ["a","b"] not ["a", "b"] -> exit 2, verification failed.
* atk_7.py  EMPTINESS CONFLATED WITH ABSENCE: the non-encodable arm returns the PLACEHOLDER, so falsy stored values ([], {}, '', 0, False) render as the dash -> exit 2, verification failed. The absence!=emptiness clause is load-bearing.
* atk_8.py  TOKEN ALPHABET CASE: the \uXXXX escape emits UPPERCASE hex digits (55+d inlined instead of hex_digit's 87+d) on the BMP arm -> exit 2, verification failed.
* atk_9.py  MEMBER LAYOUT DRIFT: object-member separator loses its space ("k":v instead of "k": v) -> exit 2, verification failed.
* atk_10.py DISPATCH REORDER: the encoder is consulted BEFORE the absence test, so an absent-but-encodable input renders as the interchange form rather than the placeholder -> exit 2, verification failed.
* atk_11.py BRACKET SWAP (direct F2P divergence): ARRAY braced and OBJECT bracketed, applied consistently at BOTH dispatch sites (serialize and serialize_list), so ['a','b'] -> {"a", "b"} -> exit 2, verification failed.
* atk_12.py DELIMITER SWAP -- the single-vs-double-quote confusion the whole change is ABOUT: every string token and key laid down in the host's single quote U+0027 instead of the interchange U+0022 (all four delimiter sites), so 'a' -> 'a' not "a" -> exit 2, verification failed.

A-LEG AUDIT (the legs G-CONF cannot mechanically reach). BOTH A-references INDEPENDENTLY re-derived by me; I did not run or trust the bundle's own axiom_check.py for these conclusions.
* A7 interchange_form <-> JSONField.get_prep_value == json.dumps(value) (encoder=None): I hand-transliterated model.py's ENTIRE pure region (node_body/ser_list/esc_seq/esc_char/hex_form/hex_digit, incl. the MEMBER "key": value layout) into a7_audit.py and diffed it against the real json.dumps over: the 3 encodable F2P values; ALL 1,114,112 code points as a single-token value; ALL 1,114,112 as an object KEY inside a nested value; 24 boundary escape classes as token/key/nested; and 20,000 randomized nested dict/list/string values with tokens drawn from the full code point range. RESULT: 2,248,299 checks, ZERO divergences (RC=0). The escape fold is exact across the whole domain -- U+0022, U+005C, the five named controls, U+007F, the C1 band, lone surrogates, and the astral planes via surrogate-pair halves. There is NO unencoded token-alphabet restriction, and atk_3/atk_8/atk_12 confirm the spec actively REJECTS band-widening, hex-case and delimiter drift.
* A8 fallback_form <-> display_for_value: audited IN the pinned eval container (swebench/sweb.eval.x86_64.django_1776_django-12308) with the GOLD PATCH APPLIED, harness a8_audit.py, RC=0, 0 divergences. inspect.getsource confirmed the JSONField/get_prep_value branch is really present in the tree under test. Checked: all 4 F2P values + the added None line agree with the test's expected display; json.dumps genuinely raises TypeError on the tuple-keyed dict; the identity pass-through fallback_form(text)==text holds; `content` really carries display_for_value's OWN output and not str(value) -- 6/6 JOIN-ARM roots ([{('x','y'):'z'}], ['a',{('x','y'):'z'}], [b'raw'], [set()], the 1-tuple, [1,2,{('k',):'v'}]) have real text != str(value) AND display_for_field routes them to exactly that text; the falsy STORED values take the fallback not the placeholder ([]->'', ''->'', {}->'{}', 0->'0', False->'False', ()->'', 0.0->'0.0'); the U+0027-vs-U+0022 delimiter contrast holds; plus 30,000 full-alphabet non-encodable fuzz values against the REAL callee with 0 divergences. So mapping.md §3.2's claim is correct, and atk_7 shows the spec enforces the emptiness!=absence half of it.
* A4/A5 three-outcome refinement re-derived from the BASE tree directly (`git show 2e0f04507b17362239ba49830d26fec504d46978:django/contrib/admin/utils.py`): the `elif value is None` arm at line 389 sits BEFORE the FileField/JSONField `and value` guards, so a non-None falsy value that fails the truthiness guard cannot reach the placeholder and falls THROUGH to display_for_value at the final else. Three outcomes, matching the model's three arms. Correct as documented.

**REFINEMENT.MD LEG AUDIT:** 8 legs, A1-A5 = R, A6 = I + R, A7 = A-reference, A8 = A-reference. Tag census: 5 R, 1 I+R, 2 A-reference, 0 A-consumed, NO kind-3 (unexpressible-changed-op) leg. model.py contains 0 occurrences of @ContractOnly and 0 of Assume/Refute, and meta.json's axioms list is empty -- so §B's "no consumed axioms" claim is literally true and there is no dead or mislabelled axiom. Both A-legs' correspondence to the real callees holds as independently audited above. §C's verify=>resolved argument is sound given those two A-references plus the R/I legs.

**CONCLUSION:** 12 attacks run to genuine verifier verdicts, 11 rejected; the one verifying attack's materialized faithful patch RESOLVES under the official harness (executed, not speculated), so it is an echo. Positive control verifies. Both A-legs independently confirmed against the real callees (2,248,299 + 30,000+ checks, zero divergences). Verdict SOUND (advisory; the runner re-runs these artifacts).

OUT-OF-SCOPE FLAG for whoever regates: meta.json now records G-PANEL-2 status=pass, consistent with my findings -- the historical raw-splice/no-escape-fold defect is genuinely closed in the frozen model.py (my full-domain sweep plus atk_3/atk_8/atk_12 all confirm the esc_seq/esc_char fold is present and load-bearing).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK GOAL: show the spec is too strong / drifts from real post-patch repo behavior. Result: no diverging input found across ~2.4M differential checks. Reference used correctly = base_commit worktree WITH patch.diff APPLIED (confirmed `git diff` == meta.patch_diff gold patch verbatim; branch present at utils.py:401).

**METHOD:** I wrote an INDEPENDENT re-implementation of model.py's pure region (oracle.py) from the model text, deliberately NOT copied from axiom_check.py, so a shared bug in the bundle's own G-AX harness could not hide drift. I then transliterated display_structured_value's impl under mapping.md's abstraction (present == value is not None; encodable == bool(value) and json.dumps returns; content == real display_for_value(value, empty)) and diffed it against the REAL patched django.contrib.admin.utils.display_for_field driven with a default models.JSONField().

### EVIDENCE (all zero divergences):
1. esc_char/esc_seq/hex_form vs json.dumps: EXHAUSTIVE sweep of all 1,114,112 code points as a string token -> 0 divergences. Same sweep with each code point as an OBJECT KEY -> 0 divergences. Both re-run inside the pinned container (Python 3.6.13) as well as host 3.12, because json.dumps is the reference callee and the escape tables are version-sensitive -> 0 divergences in both.
2. Structural serialiser vs json.dumps: 60,000 randomized nested dict/list/string trees + 9 hand-built boundary shapes (empty string/array/object, nested-empty, astral key with surrogate-half value) -> 0.
3. END-TO-END vs REAL display_for_field: 150,000 adversarial fuzz values (token pool heavy on U+0022, U+005C, the five control escapes, U+007F, C1 band, U+2028/9, lone surrogates U+D800-U+DFFF, astral planes, depth<=6) on host -> 0; plus 60,000 fuzz + 23-value boundary corpus re-run INSIDE the pinned eval container with the gold patch applied -> 0.
4. Three-arm dispatch, the classic drift point, all confirmed against the real function:
   - placeholder arm fires ONLY for None (value=None -> empty_value_display).
   - falsy-but-stored in-domain values '' / [] / {} take the FALLBACK arm, NOT the placeholder and NOT the encoder. Real: '' -> '', [] -> '', {} -> '{}'. Note {} is the discriminating case: interchange_form would ALSO give '{}', so a spec that misrouted it would still pass; but '' and [] would render '""' and '[]' under the encoder and really render '' -- the model's `not encodable` routing is what matches. mapping.md's decision NOT to fold the `and value` truthiness guard into `present` is therefore faithful, not a convenience.
   - non-encodable arm: {('a','b'):'c'} -> json.dumps raises TypeError, real output "{('a', 'b'): 'c'}" == display_for_value output, identity pass-through holds.
5. JOIN-arm discriminator (the strongest available faithfulness test of fallback_form): on list-rooted non-encodables the real text differs from str(value). [{('x','y'):'z'}] real -> "{('x', 'y'): 'z'}" while str(value) -> "[{('x', 'y'): 'z'}]". Model (content = real display_for_value) MATCHES; a str(value) model would MISMATCH. So fallback_form=identity-on-carried-callee-output is faithful where the tempting simplification would not be.
6. json.dumps default-config dependencies the mapping records are real and correct: key INSERTION order preserved (all 24 permutations of 4 keys agree -> sort_keys=False), ', ' / ': ' separators, ensure_ascii=True lowercase \uXXXX. Confirmed field.encoder is None on models.JSONField().
7. Branch-ordering/MRO check: default JSONField is not an instance of BooleanField/DateTimeField/DateField/TimeField/DecimalField/IntegerField/FloatField/FileField and flatchoices == [] (falsy), so control genuinely reaches the new elif -- no earlier arm shadows it. This validates the model's restriction of display_for_field to the JSONField dispatch.
8. F2P exactness: all four test tuples reproduce, model == expected == real.

HARNESS CONTROL (proves these zeros have teeth, not a vacuous pass): injected five drift classes into my oracle and re-ran -- UPPERCASE hex digits CAUGHT, single-quote U+0027 delimiter CAUGHT (8/8), comma-without-space separator CAUGHT, raw token splice / no escaping CAUGHT, sort_keys=True CAUGHT. A too-strong or drifted encoding spec in any of these dimensions would have been detected.

### Too-strong claims I probed and rejected as defects
- MustTerminate / totality: the real json.dumps raises RecursionError at ~10,000 nesting depth (verified: OK through 5,000, RecursionError at 10,000). This is a host C-stack artifact of the concrete interpreter, not a behavior the spec misstates; the model's j_size budget is over finite JNode trees and the Nagini abstraction has no stack bound. Not drift.
- Circular references (v=[]; v.append(v)) make the real callee raise ValueError, which the patch's `except TypeError` does NOT catch. But a cyclic value is not representable by the inductive predicate j_pred (finite tree), so it is outside the modeled domain -- the spec makes no claim there. Not drift.
- Domain narrowness: JNode admits only str/list/dict, so ints/floats/bools/nulls inside structures (e.g. {'a': 1}) are unmodeled. That makes the spec NARROWER, i.e. weaker -- it is not a faithfulness break, and it is out of scope for this gate (would belong to a coverage/strength gate). All four F2P values are str/list/dict-rooted.
- str/dict SUBCLASS inputs behave identically to their bases (verified), so no isinstance-dispatch surprise.

**VERIFIER:** scripts/nagini_verify.sh on the bundle model.py -> "Verification successful" (48s), exit 0. Prover output carries only benign 'could not resolve expression... during axiomatisation' notes on j_pred/j_size (function-axiomatisation artifacts) and pattern warnings -- no unsound-path indication, and per my prior finding on vacuity I checked the guarded arms are feasible: all three arms are exercised by real inputs (None / 'a' / {('a','b'):'c'}), so the postconditions are not vacuously discharged.

CAVEAT (not a finding): markers.region_hashes recomputed by me disagrees with meta.json's recorded region_hashes for ALL seven regions -- but 11 of 12 unrelated nagini bundles show the same uniform disagreement under my invocation, so this is my own hashing-call artifact (stale or differently-normalized recorded digests), not evidence of spec tampering in this bundle. Flagging for the record only; it does not affect the faithfulness verdict, and I reviewed the model.py spec text actually present in the bundle.

**ATTACK GOAL:** show the spec is too strong / drifts from real post-patch repo behavior. Result: no diverging input found across ~2.4M differential checks. Reference used correctly = base_commit worktree WITH patch.diff APPLIED (confirmed `git diff` == meta.patch_diff gold patch verbatim; branch present at utils.py:401).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** LEAKAGE / GOLD-RECONSTRUCTION audit of django__django-12308 (nagini). Judged the spec view against the SOLVER-VISIBLE problem_statement only; hints_text (PR #12990, 'django.db.models.JSONField instance checks') deliberately NOT credited as public baseline.

**NO RELAXATION PRESENT.** I checked for the documented-relaxation path before anything else: meta.json has NO `relaxed_leakage` key (keys are additional_change_sites, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version) and there is no RELAXED_LEAKAGE.md in the bundle. So this is an ordinary non-relaxed cell and there was no unavoidability argument to re-derive or inherit.

ARTIFACT I JUDGED (generated, not read). I did not eyeball model.py; I built the consumer artifact with the harness itself: markers.spec_view(model.py, get_backend('nagini').language) -> spec_view.txt, 454 lines. Elision is complete: all 6 impl regions collapse to exactly one distinct body, `...  # implementation elided - supplied by the consumer` (6 placeholders, regexed every impl-start..impl-end span); no `Invariant(` text and no invariants marker survives the projection. markers.region_hashes gives spec_view=1ca6696f5072bd9b1e6678b19badbef13a834f2aa9b09e2846e6c05e38295f03, byte-equal to G-HYGIENE's recorded data.region_hashes for the same model.py digest (3fe84eb97f50...). markers.same_spec(model.py, model_prepatch.py)=True, and spec_view(model)==spec_view(prepatch) as strings, so the two differ only in the impl region.

MECHANICAL SCREEN + NEGATIVE CONTROL. leakage.screen(model.py, nagini, gold_patch, problem_statement, test_patch) from the frozen instance row: passed=True, hard_failures=[], warnings=[]. Screened gold symbol set is non-vacuous ({display_for_field}); changed file django/contrib/admin/utils.py. Two controls so the pass is not vacuous: (1) re-ran with problem_statement="" (pretend NOTHING is public) -> still zero hard failures, so nothing in the view is excused merely because the issue text mentions it; (2) injected the gold line `elif isinstance(field, models.JSONField) and value:` into the axioms region -> screen correctly FAILS with "L1: gold-patch line reproduced". The screen does fire; it simply has nothing to fire on here.

MANUAL RE-SCAN (screen is a floor, not the judgement). Absent from the spec view entirely: JSONField, get_prep_value, prepare_value, InvalidJSONInput, display_for_field, display_for_value, isinstance, TypeError, models., utils.py, admin, readonly, FileField, number_format, every diff marker, base_commit/2e0f0450. Only `django` hit is the instance id on docstring line 1. `json.dumps` appears once (line 280) as the named referent of interchange_form -- and json.dumps is explicitly public in the problem_statement. Narration vocabulary hits are all substrings (dispatch/dispatched, fixed-length) that fail the word-boundary rule; `read-only` is a permission remark. No bug/fix/previously/pre-patch narration. The prepatch model's explicit "PRE-PATCH BUG" comment lives inside the impl region and does NOT survive the projection (verified: 'PRE-PATCH' not in spec_view(model_prepatch)).

LOAD-BEARING TEST, RUN POSITIVELY. This is the measurement that decides whether the discriminating clause is a requirement or removable narration. scripts/nagini_verify.sh on gold model.py -> "Verification successful", exit 0 (57.6s). On model_prepatch.py -> exit 1, sole error: `pre.py:590:13:591:64: Postcondition of display_structured_value might not hold. Assertion Implies((present and encodable), (ToSeq(Result()) == interchange_form(value))) might not hold.` Then the decisive control: I stripped ONLY that clause from the prepatch model and re-verified -> exit 0, "Verification successful" (48.4s). So the clause is exactly the thing that rejects the pre-patch impl -- it is a load-bearing property of the OUTPUT, not a description of the edit.

**GOLD RECONSTRUCTION.** The spec view states desired behaviour: a three-arm dispatch over (present, encodable) with the encoding pinned to pure helpers. It never says WHERE a branch goes, WHICH field type triggers it, WHICH callee computes the encoding, nor that the mechanism is an isinstance test guarded by truthiness with a TypeError catch. Decisively, the public problem_statement is strictly MORE localizing than the spec view: it names django.contrib.admin.utils, display_for_field, JSONField, prepare_value, json.dumps, InvalidJSONInput, and gives the {"foo": "bar"} vs {'foo': 'bar'} contrast plus "which is not valid JSON". Every gold-edit specific is public already and absent from the view. The structural-vs-single-token clause (lines 50-55) and the empty-vs-absent clause (lines 35-38) are behavioural strengthenings derivable from "must be valid JSON", not edit localization.

ONE THING I CONSIDERED AND DISMISSED (recorded for the record). Spec-view lines 29-30/54-55 contain the byte-strings {"a": {"b": "c"}} and ["a", "b"], which coincide with three of the four F2P expected values. I do not treat this as leaking the gold EDIT: they are single-letter placeholder illustrations of the stated encoding rule, they follow mechanically from json.dumps (public in the problem_statement, which already supplies the canonical {"foo": "bar"} form), and the view does NOT carry the fourth and most discriminating F2P literal {('a', 'b'): 'c'} (the invalid-JSON/TypeError fallback case) -- verified absent -- nor the test name test_json_display_for_field, nor admin_utils/empty_value/subTest. So the view is not reproducing the hidden test table. This is at most a test-literal observation on a different facet, not gold-edit leakage.

**CORE GATES THIS LEANS ON.** G-HYGIENE pass (its region_hashes reproduce under my own computation), G-LEAK pass (reproduced independently, with a working negative control), G-GOLD/G-DIFF pass (reproduced directly: gold verifies, prepatch fails on the discriminating clause). All 16 recorded gates are pass.

**NOTHING IN THE BUNDLE ADDRESSED ME.** leakage.reviewer_directed() returns [] on model.py, mapping.md and refinement.md; grepping the authored docs for auditor/reviewer/panel/verdict/NO-LEAKAGE/submit_result finds nothing. The only NO-LEAKAGE strings in the tree are prior recorded audit notes inside meta.json/verdict.md (a previous run's own note echoed back), not instructions to me. No attempt was made to tell me how to record or which verdict is honest.

ADVISORY (not a leakage finding). meta.json's TOP-LEVEL region_hashes block is stale w.r.t. the shipped model.py -- recorded spec_view cc899822aed7... vs computed 1ca6696f5072..., and all six region hashes differ. I judged the view I generated from the shipped model.py, and G-HYGIENE's per-gate data.region_hashes (same model.py digest) agrees with me byte for byte; I found no reader of the top-level block in src/ or scripts/, so it appears non-load-bearing, but it should be refreshed.

**VERDICT:** NO-LEAKAGE. The spec view carries nothing about the gold edit beyond what the public problem_statement already discloses -- indeed considerably less.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
