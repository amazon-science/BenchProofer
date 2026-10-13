# P2 adversarial audit — django__django-11815

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1_payload_keyed.py`, `atk_2_diverge.py`, `atk_3b_guarded_diverge.py`, `atk_4_selfcall.py`, `atk_5_frame_mutate.py`, `atk_6_leading_digit.py`, `atk_9_payload_empty.py`, `atk_14_empty_ident.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_7_quote_out_of_domain.py`, `atk_8b_backslash_escape.py`, `atk_10_import_out_of_domain.py`, `atk_12_nonascii_lead.py`, `atk_13_payload_read.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_payload_keyed.py` → rejected (same spec, does not verify — good)

```diff
@@ -143,16 +143,14 @@
     Ensures(ToSeq(Result()[1]) == import_line(ToSeq(module)))
     # post-conditions-end
     # impl-start
-    # frag = module + "." + class_name + "[" + "'" + identifier + "'" + "]"
+    # PRE-PATCH: keyed by the mutable payload, Class(value) form.
     frag = []  # type: List[int]
     frag = frag + module
     frag = frag + [46]                       # '.'
     frag = frag + class_name
-    frag = frag + [91]                       # '['
-    frag = frag + [39]                       # "'"
-    frag = frag + identifier
-    frag = frag + [39]                       # "'"
-    frag = frag + [93]                       # ']'
-    imp = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
+    frag = frag + [40]                       # '('
+    frag = frag + payload
+    frag = frag + [41]                       # ')'
+    imp = [105, 109, 112, 111, 114, 116, 32] + module
     return (frag, imp)
     # impl-end
```

Attack 2 — `atk_2_diverge.py` → rejected (same spec, does not verify — good)

```diff
@@ -143,16 +143,20 @@
     Ensures(ToSeq(Result()[1]) == import_line(ToSeq(module)))
     # post-conditions-end
     # impl-start
-    # frag = module + "." + class_name + "[" + "'" + identifier + "'" + "]"
+    # DIVERGE before the gold construction (partial-correctness probe).
+    i = 0
+    while i >= 0:
+        Invariant(i >= 0)
+        i = i + 1
     frag = []  # type: List[int]
     frag = frag + module
-    frag = frag + [46]                       # '.'
+    frag = frag + [46]
     frag = frag + class_name
-    frag = frag + [91]                       # '['
-    frag = frag + [39]                       # "'"
+    frag = frag + [91]
+    frag = frag + [39]
     frag = frag + identifier
-    frag = frag + [39]                       # "'"
-    frag = frag + [93]                       # ']'
-    imp = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
+    frag = frag + [39]
+    frag = frag + [93]
+    imp = [105, 109, 112, 111, 114, 116, 32] + module
     return (frag, imp)
     # impl-end
```

Attack 3 — `atk_3b_guarded_diverge.py` → rejected (same spec, does not verify — good)

```diff
@@ -143,16 +143,15 @@
     Ensures(ToSeq(Result()[1]) == import_line(ToSeq(module)))
     # post-conditions-end
     # impl-start
-    # frag = module + "." + class_name + "[" + "'" + identifier + "'" + "]"
-    frag = []  # type: List[int]
-    frag = frag + module
-    frag = frag + [46]                       # '.'
-    frag = frag + class_name
-    frag = frag + [91]                       # '['
-    frag = frag + [39]                       # "'"
-    frag = frag + identifier
-    frag = frag + [39]                       # "'"
-    frag = frag + [93]                       # ']'
-    imp = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
+    # CONTROL-FLOW EFFECT: diverge ONLY for an F2P-reachable name ('A' == 65).
+    # Tests whether MustTerminate(2) reaches inside a guarded branch.
+    if len(identifier) > 0 and identifier[0] == 65:
+        i = 0
+        while i >= 0:
+            Invariant(i >= 0)
+            i = i + 1
+    frag = (module + [46] + class_name + [91] + [39]
+            + identifier + [39] + [93])  # type: List[int]
+    imp = [105, 109, 112, 111, 114, 116, 32] + module  # type: List[int]
     return (frag, imp)
     # impl-end
```

Attack 4 — `atk_4_selfcall.py` → rejected (same spec, does not verify — good)

```diff
@@ -143,16 +143,12 @@
     Ensures(ToSeq(Result()[1]) == import_line(ToSeq(module)))
     # post-conditions-end
     # impl-start
-    # frag = module + "." + class_name + "[" + "'" + identifier + "'" + "]"
-    frag = []  # type: List[int]
-    frag = frag + module
-    frag = frag + [46]                       # '.'
-    frag = frag + class_name
-    frag = frag + [91]                       # '['
-    frag = frag + [39]                       # "'"
-    frag = frag + identifier
-    frag = frag + [39]                       # "'"
-    frag = frag + [93]                       # ']'
-    imp = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
+    # Recursive self-call under a FEASIBLE guard (non-empty module).
+    if len(module) > 0:
+        r = serialize_member(module, class_name, identifier, payload)
+        return r
+    frag = (module + [46] + class_name + [91] + [39]
+            + identifier + [39] + [93])  # type: List[int]
+    imp = [105, 109, 112, 111, 114, 116, 32] + module  # type: List[int]
     return (frag, imp)
     # impl-end
```

Attack 5 — `atk_5_frame_mutate.py` → rejected (same spec, does not verify — good)

```diff
@@ -143,16 +143,10 @@
     Ensures(ToSeq(Result()[1]) == import_line(ToSeq(module)))
     # post-conditions-end
     # impl-start
-    # frag = module + "." + class_name + "[" + "'" + identifier + "'" + "]"
-    frag = []  # type: List[int]
-    frag = frag + module
-    frag = frag + [46]                       # '.'
-    frag = frag + class_name
-    frag = frag + [91]                       # '['
-    frag = frag + [39]                       # "'"
-    frag = frag + identifier
-    frag = frag + [39]                       # "'"
-    frag = frag + [93]                       # ']'
-    imp = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
+    # Gold outputs, but MUTATE the read-only `payload` input.
+    frag = (module + [46] + class_name + [91] + [39]
+            + identifier + [39] + [93])  # type: List[int]
+    imp = [105, 109, 112, 111, 114, 116, 32] + module  # type: List[int]
+    payload.append(46)
     return (frag, imp)
     # impl-end
```

Attack 6 — `atk_6_leading_digit.py` → rejected (same spec, does not verify — good)

```diff
@@ -143,16 +143,11 @@
     Ensures(ToSeq(Result()[1]) == import_line(ToSeq(module)))
     # post-conditions-end
     # impl-start
-    # frag = module + "." + class_name + "[" + "'" + identifier + "'" + "]"
-    frag = []  # type: List[int]
-    frag = frag + module
-    frag = frag + [46]                       # '.'
-    frag = frag + class_name
-    frag = frag + [91]                       # '['
-    frag = frag + [39]                       # "'"
-    frag = frag + identifier
-    frag = frag + [39]                       # "'"
-    frag = frag + [93]                       # ']'
-    imp = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
+    # Junk on a leading-DIGIT identifier — still inside the precondition.
+    if len(identifier) > 0 and 48 <= identifier[0] and identifier[0] <= 57:
+        return ([46], [46])
+    frag = (module + [46] + class_name + [91] + [39]
+            + identifier + [39] + [93])  # type: List[int]
+    imp = [105, 109, 112, 111, 114, 116, 32] + module  # type: List[int]
     return (frag, imp)
     # impl-end
```

Attack 7 — `atk_7_quote_out_of_domain.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

```diff
@@ -143,16 +143,11 @@
     Ensures(ToSeq(Result()[1]) == import_line(ToSeq(module)))
     # post-conditions-end
     # impl-start
-    # frag = module + "." + class_name + "[" + "'" + identifier + "'" + "]"
-    frag = []  # type: List[int]
-    frag = frag + module
-    frag = frag + [46]                       # '.'
-    frag = frag + class_name
-    frag = frag + [91]                       # '['
-    frag = frag + [39]                       # "'"
-    frag = frag + identifier
-    frag = frag + [39]                       # "'"
-    frag = frag + [93]                       # ']'
-    imp = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
+    # PARTIAL DOMAIN: junk when the name starts with a quote (out of domain).
+    if len(identifier) > 0 and identifier[0] == 39:
+        return ([46], [46])
+    frag = (module + [46] + class_name + [91] + [39]
+            + identifier + [39] + [93])  # type: List[int]
+    imp = [105, 109, 112, 111, 114, 116, 32] + module  # type: List[int]
     return (frag, imp)
     # impl-end
```

Attack 8 — `atk_8b_backslash_escape.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

```diff
@@ -143,16 +143,13 @@
     Ensures(ToSeq(Result()[1]) == import_line(ToSeq(module)))
     # post-conditions-end
     # impl-start
-    # frag = module + "." + class_name + "[" + "'" + identifier + "'" + "]"
-    frag = []  # type: List[int]
-    frag = frag + module
-    frag = frag + [46]                       # '.'
-    frag = frag + class_name
-    frag = frag + [91]                       # '['
-    frag = frag + [39]                       # "'"
-    frag = frag + identifier
-    frag = frag + [39]                       # "'"
-    frag = frag + [93]                       # ']'
-    imp = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
+    # A-REFERENCE probe: emit the REAL %r escaping for a backslash-carrying
+    # name (out of the precondition's alphabet), not the model's naive wrap.
+    extra = []  # type: List[int]
+    if len(identifier) > 0 and identifier[0] == 92:
+        extra = [92]
+    frag = (module + [46] + class_name + [91] + [39] + extra
+            + identifier + [39] + [93])  # type: List[int]
+    imp = [105, 109, 112, 111, 114, 116, 32] + module  # type: List[int]
     return (frag, imp)
     # impl-end
```

Attack 9 — `atk_9_payload_empty.py` → rejected (same spec, does not verify — good)

```diff
@@ -143,16 +143,11 @@
     Ensures(ToSeq(Result()[1]) == import_line(ToSeq(module)))
     # post-conditions-end
     # impl-start
-    # frag = module + "." + class_name + "[" + "'" + identifier + "'" + "]"
-    frag = []  # type: List[int]
-    frag = frag + module
-    frag = frag + [46]                       # '.'
-    frag = frag + class_name
-    frag = frag + [91]                       # '['
-    frag = frag + [39]                       # "'"
-    frag = frag + identifier
-    frag = frag + [39]                       # "'"
-    frag = frag + [93]                       # ']'
-    imp = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
+    # Junk when the payload is empty — payload is unconstrained, so in-domain.
+    if len(payload) == 0:
+        return ([46], [46])
+    frag = (module + [46] + class_name + [91] + [39]
+            + identifier + [39] + [93])  # type: List[int]
+    imp = [105, 109, 112, 111, 114, 116, 32] + module  # type: List[int]
     return (frag, imp)
     # impl-end
```

Attack 10 — `atk_10_import_out_of_domain.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -143,16 +143,11 @@
     Ensures(ToSeq(Result()[1]) == import_line(ToSeq(module)))
     # post-conditions-end
     # impl-start
-    # frag = module + "." + class_name + "[" + "'" + identifier + "'" + "]"
-    frag = []  # type: List[int]
-    frag = frag + module
-    frag = frag + [46]                       # '.'
-    frag = frag + class_name
-    frag = frag + [91]                       # '['
-    frag = frag + [39]                       # "'"
-    frag = frag + identifier
-    frag = frag + [39]                       # "'"
-    frag = frag + [93]                       # ']'
-    imp = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
+    # Second import line, only for an out-of-domain (quote-leading) name.
+    frag = (module + [46] + class_name + [91] + [39]
+            + identifier + [39] + [93])  # type: List[int]
+    imp = [105, 109, 112, 111, 114, 116, 32] + module  # type: List[int]
+    if len(identifier) > 0 and identifier[0] == 39:
+        imp = imp + [10] + [105, 109, 112, 111, 114, 116, 32] + identifier
     return (frag, imp)
     # impl-end
```

Attack 11 — `atk_12_nonascii_lead.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -143,16 +143,14 @@
     Ensures(ToSeq(Result()[1]) == import_line(ToSeq(module)))
     # post-conditions-end
     # impl-start
-    # frag = module + "." + class_name + "[" + "'" + identifier + "'" + "]"
-    frag = []  # type: List[int]
-    frag = frag + module
-    frag = frag + [46]                       # '.'
-    frag = frag + class_name
-    frag = frag + [91]                       # '['
-    frag = frag + [39]                       # "'"
-    frag = frag + identifier
-    frag = frag + [39]                       # "'"
-    frag = frag + [93]                       # ']'
-    imp = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
+    # DOMAIN probe, LOOP-FREE: junk for a leading NON-ASCII code point. Such a
+    # name is excluded by plain_token_char yet is a legal class-body attribute
+    # name in Python 3 (`class E(enum.Enum): cafe' = 1` with an accented e), so
+    # it does NOT need the enum functional API to be reachable.
+    if len(identifier) > 0 and identifier[0] > 127:
+        return ([46], [46])
+    frag = (module + [46] + class_name + [91] + [39]
+            + identifier + [39] + [93])  # type: List[int]
+    imp = [105, 109, 112, 111, 114, 116, 32] + module  # type: List[int]
     return (frag, imp)
     # impl-end
```

Attack 12 — `atk_13_payload_read.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -143,16 +143,15 @@
     Ensures(ToSeq(Result()[1]) == import_line(ToSeq(module)))
     # post-conditions-end
     # impl-start
-    # frag = module + "." + class_name + "[" + "'" + identifier + "'" + "]"
-    frag = []  # type: List[int]
-    frag = frag + module
-    frag = frag + [46]                       # '.'
-    frag = frag + class_name
-    frag = frag + [91]                       # '['
-    frag = frag + [39]                       # "'"
-    frag = frag + identifier
-    frag = frag + [39]                       # "'"
-    frag = frag + [93]                       # ']'
-    imp = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
+    # A-LEG / CORRESPONDENCE probe: READ the mutable payload and discard the
+    # reading. Legal under Acc(list_pred(payload), 1/2); the outputs stay
+    # byte-identical to gold. Faithfully refined, obtaining a renderable form of
+    # self.value.value re-introduces the serializer_factory(...).serialize()
+    # call the gold patch DELETES — a side-effecting callee that can raise.
+    n = len(payload)
+    Assert(n >= 0)
+    frag = (module + [46] + class_name + [91] + [39]
+            + identifier + [39] + [93])  # type: List[int]
+    imp = [105, 109, 112, 111, 114, 116, 32] + module  # type: List[int]
     return (frag, imp)
     # impl-end
```

Attack 13 — `atk_14_empty_ident.py` → rejected (same spec, does not verify — good)

```diff
@@ -143,16 +143,12 @@
     Ensures(ToSeq(Result()[1]) == import_line(ToSeq(module)))
     # post-conditions-end
     # impl-start
-    # frag = module + "." + class_name + "[" + "'" + identifier + "'" + "]"
-    frag = []  # type: List[int]
-    frag = frag + module
-    frag = frag + [46]                       # '.'
-    frag = frag + class_name
-    frag = frag + [91]                       # '['
-    frag = frag + [39]                       # "'"
-    frag = frag + identifier
-    frag = frag + [39]                       # "'"
-    frag = frag + [93]                       # ']'
-    imp = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
+    # BOUNDARY, strictly IN domain: the EMPTY identifier satisfies the Forall
+    # precondition vacuously, so the spec claims the gold rendering for it.
+    if len(identifier) == 0:
+        return ([46], [46])
+    frag = (module + [46] + class_name + [91] + [39]
+            + identifier + [39] + [93])  # type: List[int]
+    imp = [105, 109, 112, 111, 114, 116, 32] + module  # type: List[int]
     return (frag, imp)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11815.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single enumeration member, used as a default value, is rendered into a
  fragment of importable source code that — when later evaluated — must recover
  the SAME member. The member carries four pieces of text: the dotted module
  path it lives in, the simple class name of its enumeration, its STABLE
  declared identifier (the attribute name under which the member is defined on
  the class), and a renderable form of the mutable payload it currently holds.

  The rendered fragment must reconstruct the member by its STABLE identifier:
  it is the module path, a dot, the class name, then the identifier — quoted as
  a single-quoted string literal — enclosed in subscription brackets. Reading
  the texts as Unicode code-point sequences, the result is

        module ++ "." ++ class_name ++ "[" ++ "'" ++ identifier ++ "'" ++ "]".

  It must NOT be built from the member's mutable payload, because that payload
  may be re-rendered differently later (for example after human-language
  translation of a deferred string) and would then no longer identify any
  member. The single accompanying import statement is the import of the
  member's module, and ONLY that — no further imports derived from rendering
  the payload.

  Rendering is a bounded, straight-line computation: the operation MUST
  terminate and return its two texts (a total-correctness obligation, carried
  as MustTerminate in the precondition).

  Domain: the stable identifier is REQUIRED to be drawn from the simple
  identifier alphabet (ASCII letters, ASCII digits, underscore). Attribute
  names declared in a class body always satisfy this, and on this alphabet
  the single-quote wrap below is exactly the token's canonical rendered form
  (no escaping, no delimiter switch). The specification makes no claim for
  names outside this alphabet (e.g. a name carrying a quote or a backslash,
  constructible only through dynamic construction APIs), whose canonical
  rendering may switch quote style or insert escapes.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the pure sequence theory `PSeq[int]` carries the specification. The
quoting of a stable identifier into a single-quoted string literal is the
unchanged repr of a simple identifier token and is modelled deeply as a wrap in
U+0027 quotes, validated == the real callee out-of-band by axiom_check.py
(G-AX); it is not consumed as an axiom. The modeled input domain is scoped to
match: a precondition states that every code point of the stable identifier is
an ASCII letter, digit, or underscore — the shape an attribute name always has,
and exactly the domain on which the single-quote wrap IS the real rendering
(no escaping, no delimiter switch). Texts outside that domain are outside the
modeled slice.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (No consumed @ContractOnly axiom. The one unchanged stdlib operation the
# fragment relies on — wrapping a stable identifier in a single-quoted string
# literal, i.e. repr of a simple identifier token — is modelled DEEPLY by
# `quoted` below and validated == the real callee by axiom_check.py / G-AX as
# an A-reference; it is not consumed as an axiom.)
# axioms-end

# pure-start
@Pure
def plain_token_char(c: int) -> bool:
    """Code point of a plain attribute-name token: an ASCII letter, digit, or
    underscore. On tokens made only of these code points, the single-quote
    wrap `quoted` below is exactly the rendered string-literal form of the
    token (no character needs escaping and no delimiter switch occurs)."""
    return (c == 95                                # '_'
            or (48 <= c and c <= 57)               # '0'..'9'
            or (65 <= c and c <= 90)               # 'A'..'Z'
            or (97 <= c and c <= 122))             # 'a'..'z'

@Pure
def quoted(tok: PSeq[int]) -> PSeq[int]:
    """A simple identifier token rendered as a single-quoted string literal:
    a U+0027 quote, the token code points, a closing U+0027 quote. Deep model
    of repr applied to a plain identifier (no quote/backslash/control chars)."""
    return PSeq(39) + tok + PSeq(39)

@Pure
def rendered(module: PSeq[int], class_name: PSeq[int],
             identifier: PSeq[int]) -> PSeq[int]:
    """The reference fragment, keyed by the stable identifier:
    module ++ '.' ++ class_name ++ '[' ++ "'identifier'" ++ ']'."""
    return (module + PSeq(46) + class_name + PSeq(91)
            + quoted(identifier) + PSeq(93))

@Pure
def import_line(module: PSeq[int]) -> PSeq[int]:
    """The one accompanying import statement: "import " followed by the module
    path. "import " == U+0069 6D 70 6F 72 74 20."""
    return PSeq(105, 109, 112, 111, 114, 116, 32) + module
# pure-end

def serialize_member(module: List[int], class_name: List[int],
                     identifier: List[int], payload: List[int]
                     ) -> Tuple[List[int], List[int]]:
    # pre-conditions-start
    # All four texts are read-only inputs (fractional permission). `payload` is
    # the renderable mutable-payload form; it is supplied but MUST NOT shape
    # either output (the point: key by the stable identifier, not the payload).
    Requires(Acc(list_pred(module), 1 / 2))
    Requires(Acc(list_pred(class_name), 1 / 2))
    Requires(Acc(list_pred(identifier), 1 / 2))
    Requires(Acc(list_pred(payload), 1 / 2))
    # Domain scoping: the stable identifier is a plain attribute-name token —
    # every code point an ASCII letter, digit, or underscore. That is the only
    # shape a declared attribute name can take, and it is exactly the domain
    # on which the single-quote wrap `quoted` equals the real rendering of the
    # token as a string literal. Texts with a quote, backslash, or control
    # character are outside the modeled slice.
    Requires(Forall(int, lambda k: (Implies(
        0 <= k and k < len(identifier),
        plain_token_char(identifier[k])))))
    # The rendering is a bounded amount of straight-line work and MUST
    # terminate (a total-correctness obligation). An implementation that
    # diverges before returning would satisfy the value postconditions only
    # vacuously and would never deliver the rendered fragment to its caller.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(module), 1 / 2))
    Ensures(Acc(list_pred(class_name), 1 / 2))
    Ensures(Acc(list_pred(identifier), 1 / 2))
    Ensures(Acc(list_pred(payload), 1 / 2))
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    # The fragment reconstructs the member by its STABLE identifier, grounded in
    # the module / class_name / identifier carriers (not the payload).
    Ensures(ToSeq(Result()[0]) ==
            rendered(ToSeq(module), ToSeq(class_name), ToSeq(identifier)))
    # The accompanying import statement is exactly the import of the module.
    Ensures(ToSeq(Result()[1]) == import_line(ToSeq(module)))
    # post-conditions-end
    # impl-start
    # Correct impl, RESHAPED: one concatenation expression, staged tuple local.
    imp = [105, 109, 112, 111, 114, 116, 32] + module  # type: List[int]
    frag = (module + [46] + class_name + [91] + [39]
            + identifier + [39] + [93])  # type: List[int]
    out = (frag, imp)  # type: Tuple[List[int], List[int]]
    return out
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, django__django-11815 / nagini. 13 same-spec attacks (all `same_spec=True`, all `unsound_evasions=none`), positive control verifies, prepatch bug reproduced and REJECTED. 5 attacks verified; ALL 5 faithful refined patches were MATERIALIZED AND RUN through the official harness (run_resolve) and ALL 5 RESOLVED. No verify-does-not-resolve witness found => SOUND.

**ENV:** cd swe-proof; PYTHONPATH=src SBU_BENCHMARK_DIR=benchmark-verified SBU_BENCHMARK=swe_bench_verified; PY=~/anaconda3/envs/swebench-nagini/bin/python. Attack cmd: python -m swebench_unified.adversary weakness nagini django__django-11815 <path>. Resolve cmd: python resolve_one.py <patch.diff> <tag> (calls swebench_unified.harness.run_resolve). Verifications run 3-concurrent as background jobs; logs in.

### ORACLE HEALTH (both controls run, so the 5 'resolved' verdicts are meaningful):
- patch__gold_control.diff (gold hunk regenerated by my own generator) -> RESOLVED, F2P both success, attempts=1.
- patch_NEGCTL_atk_1_payload_keyed.diff (faithful refinement of the REJECTED prepatch attack, post-patch-shaped) -> NOT RESOLVED, 'patch did not resolve in 3 attempts (consistent - not flaky)', F2P failure=[test_serialize_class_based_validators, test_serialize_enums]. So the oracle discriminates on exactly this change.

### PER-ATTACK RESULTS (path / observed):
1. atk_1_payload_keyed.py - PREPATCH BUG re-encoded (Class(value) from `payload`). exit 2 NOT-A-COUNTEREXAMPLE. Rejected for the RIGHT reason: 'Postcondition... (ToSeq(Result()[0]) == rendered(...)) might not hold' (250.9s).
2. atk_2_diverge.py - nontermination ahead of gold construction. exit 2. 'Obligation leak check failed. Loop might not take all unsatisfied obligations from the context' -> MustTerminate(2) (A5) is genuinely load-bearing.
3. atk_3b_guarded_diverge.py - divergence GUARDED on an F2P-reachable name ('A'==65). exit 2. Same obligation-leak rejection INSIDE a branch, so A5 reaches guarded control flow. (v1 atk_3_raise.py was discarded: it died on 'Not supported: Unsupported builtin function', a TRANSLATION error = rejection for the wrong reason, not evidence.)
4. atk_4_selfcall.py - unbounded recursion behind a FEASIBLE guard (len(module)>0; the guarded-self-call-goes-vacuous trap). exit 2. 'Callee serialize_member might not take all unsatisfied obligations from the caller' - so the guard was feasible and the rejection is real, not vacuous.
5. atk_5_frame_mutate.py - gold outputs + write into read-only `payload`. exit 2. 'precondition of method append might not hold. There might be insufficient permission' - the fractional-permission frame is load-bearing.
6. atk_6_leading_digit.py - junk on a LEADING-DIGIT name (plain_token_char admits it, a real attribute name never is). exit 2, postcondition violated -> the precondition is not silently narrower than it reads.
7. atk_7_quote_out_of_domain.py - junk when name starts with U+0027 (excluded by plain_token_char). CANDIDATE (31.8s). Faithful patch RESOLVED (F2P both success, attempts=1).
8. atk_8b_backslash_escape.py - A-REFERENCE probe: refines `quoted` to the REAL %r escaping (backslash-leading name) rather than the model's naive wrap. CANDIDATE (39.4s). Faithful patch RESOLVED. (v1 atk_8 discarded: 'Name "frag" already defined' = translation error, wrong reason.)
9. atk_9_payload_empty.py - junk when `payload` is empty; `payload` carries NO precondition so this is in-domain. exit 2, postcondition violated -> 'output does not depend on the mutable payload' is genuinely pinned.
10. atk_10_import_out_of_domain.py - IMPORT leg: second import line appended, only for an out-of-domain name. CANDIDATE (25.9s). Faithful patch RESOLVED.
11. atk_12_nonascii_lead.py - junk for a leading NON-ASCII code point. CANDIDATE (31.7s). Faithful patch RESOLVED. (Loop-free re-encoding; atk_11/atk_11b were discarded as wrong-reason rejections - 'precondition of function len... insufficient permission' then a postcondition failure caused by MY loop invariant's weakness, not the spec.)
12. atk_13_payload_read.py - SHARPEST A-leg/correspondence probe. refinement.md A1 asserts the post-patch impl 'reads [payload] not at all'; mapping.md §1 binds `payload` to 'a renderable form of self.value.value', which in the REAL code can only be OBTAINED by serializer_factory(self.value.value).serialize() - the very call the gold patch DELETES. Model impl merely READS payload (legal under Acc(...,1/2)) with gold-identical outputs; CANDIDATE (34.5s). Its faithful patch re-instates the deleted side-effecting callee and RESOLVED (F2P both success). So the A1 correspondence is loose in prose but not exploitable: the reinstated call is side-effect-free on every F2P-reachable value.
13. atk_14_empty_ident.py - EMPTY identifier (satisfies the Forall vacuously, so strictly in-domain). exit 2, postcondition violated.

REFINEMENT.MD AUDIT (leg kinds): A1 R, A2 A-reference, A3 A-reference, A4 R, A5 I, A6 R. NO kind-3 (unexpressible-changed-op) leg. Confirmed mechanically that the axioms region has ZERO non-comment lines and that model.py's single '@ContractOnly' occurrence is inside a comment (line 59), i.e. there is genuinely NO consumed axiom - the changed rendering is modelled DEEPLY in the pure region, which is the strongest available posture for the A legs.

A-LEG CORRESPONDENCE, INDEPENDENTLY RE-DERIVED (audit_arefs.py, exit 0 - I did NOT reuse the bundle's axiom_check.py, which is itself under audit; I transcribed the gold format strings from patch.diff and called real CPython repr/enum):
- **A2/A3:** 4176 (module, class_name, in-domain name) triples - exhaustive to length 3 over a boundary-complete alphabet plus the real F2P names - agree code-point-for-code-point with '%s.%s[%r]' and {'import %s' % module}; import set cardinality is 1 in every case.
- A2 through the REAL enum machinery: TextEnum/BinaryEnum/IntEnum members and re.RegexFlag(16) -> "re.RegexFlag['DOTALL']", {'import re'} (the F2P validator case) all match.
- A6(i): 0 in-alphabet names where quoted != %r. Every quoted-vs-%r divergence I could construct (a'b, a\\b, a\nb, ', \\, NUL) lies STRICTLY OUTSIDE the precondition, so the spec claims nothing false on its domain.
- The bundle's own axiom_check.py re-run: exit 0.

ONE DOCUMENTATION INACCURACY (not a soundness defect, no repair required): refinement.md A6 and mapping.md §1 justify the plain_token_char precondition by asserting out-of-alphabet names are 'constructible only through dynamic construction APIs, never via a class-body declaration'. That reachability claim is FALSE as written - Python 3 attribute names may be any Unicode identifier, so `class E(enum.Enum): café = 1` is a legal class-body declaration whose member name is outside the ASCII alphabet (demonstrated in audit_arefs.py A6(ii)). It is NOT exploitable: on such names CPython repr still emits the bare single-quote wrap, so `quoted` is CORRECT there and the precondition merely narrows conservatively rather than hiding a divergence - and I confirmed mechanically that a wrong impl keyed on that excluded input (atk_12) still yields a RESOLVING patch. The prose overstates the unreachability argument; the underlying domain scoping is sound.

**WHY NO BREAK EXISTS.** The spec pins the WHOLE output sequence via two closed-form deep models over the inputs, so no ungrounded-oracle echo is available (an impl returning rendered(...) literally IS the gold rendering). The remaining freedom is confined to inputs outside the precondition (quote/backslash/non-ASCII-leading names) and to reading the unconstrained `payload`. Those inputs are unreachable from the F2P/P2P suites - every member name the tests produce is a plain ASCII identifier ('A','B','DOTALL') - so any impl differing from gold ONLY there is behaviourally gold on everything the oracle observes, which is exactly what the 5 executed resolves confirm empirically rather than by argument.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1_payload_keyed.py`, `atk_2_diverge.py`, `atk_3b_guarded_diverge.py`, `atk_4_selfcall.py`, `atk_5_frame_mutate.py`, `atk_6_leading_digit.py`, `atk_9_payload_empty.py`, `atk_14_empty_ident.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_7_quote_out_of_domain.py`, `atk_8b_backslash_escape.py`, `atk_10_import_out_of_domain.py`, `atk_12_nonascii_lead.py`, `atk_13_payload_read.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_payload_keyed.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_diverge.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3b_guarded_diverge.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_selfcall.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_frame_mutate.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_leading_digit.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_quote_out_of_domain.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 8 — `atk_8b_backslash_escape.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 9 — `atk_9_payload_empty.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_import_out_of_domain.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_12_nonascii_lead.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_13_payload_read.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_14_empty_ident.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11815.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single enumeration member, used as a default value, is rendered into a
  fragment of importable source code that — when later evaluated — must recover
  the SAME member. The member carries four pieces of text: the dotted module
  path it lives in, the simple class name of its enumeration, its STABLE
  declared identifier (the attribute name under which the member is defined on
  the class), and a renderable form of the mutable payload it currently holds.

  The rendered fragment must reconstruct the member by its STABLE identifier:
  it is the module path, a dot, the class name, then the identifier — quoted as
  a single-quoted string literal — enclosed in subscription brackets. Reading
  the texts as Unicode code-point sequences, the result is

        module ++ "." ++ class_name ++ "[" ++ "'" ++ identifier ++ "'" ++ "]".

  It must NOT be built from the member's mutable payload, because that payload
  may be re-rendered differently later (for example after human-language
  translation of a deferred string) and would then no longer identify any
  member. The single accompanying import statement is the import of the
  member's module, and ONLY that — no further imports derived from rendering
  the payload.

  Rendering is a bounded, straight-line computation: the operation MUST
  terminate and return its two texts (a total-correctness obligation, carried
  as MustTerminate in the precondition).

  Domain: the stable identifier is REQUIRED to be drawn from the simple
  identifier alphabet (ASCII letters, ASCII digits, underscore). Attribute
  names declared in a class body always satisfy this, and on this alphabet
  the single-quote wrap below is exactly the token's canonical rendered form
  (no escaping, no delimiter switch). The specification makes no claim for
  names outside this alphabet (e.g. a name carrying a quote or a backslash,
  constructible only through dynamic construction APIs), whose canonical
  rendering may switch quote style or insert escapes.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the pure sequence theory `PSeq[int]` carries the specification. The
quoting of a stable identifier into a single-quoted string literal is the
unchanged repr of a simple identifier token and is modelled deeply as a wrap in
U+0027 quotes, validated == the real callee out-of-band by axiom_check.py
(G-AX); it is not consumed as an axiom. The modeled input domain is scoped to
match: a precondition states that every code point of the stable identifier is
an ASCII letter, digit, or underscore — the shape an attribute name always has,
and exactly the domain on which the single-quote wrap IS the real rendering
(no escaping, no delimiter switch). Texts outside that domain are outside the
modeled slice.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (No consumed @ContractOnly axiom. The one unchanged stdlib operation the
# fragment relies on — wrapping a stable identifier in a single-quoted string
# literal, i.e. repr of a simple identifier token — is modelled DEEPLY by
# `quoted` below and validated == the real callee by axiom_check.py / G-AX as
# an A-reference; it is not consumed as an axiom.)
# axioms-end

# pure-start
@Pure
def plain_token_char(c: int) -> bool:
    """Code point of a plain attribute-name token: an ASCII letter, digit, or
    underscore. On tokens made only of these code points, the single-quote
    wrap `quoted` below is exactly the rendered string-literal form of the
    token (no character needs escaping and no delimiter switch occurs)."""
    return (c == 95                                # '_'
            or (48 <= c and c <= 57)               # '0'..'9'
            or (65 <= c and c <= 90)               # 'A'..'Z'
            or (97 <= c and c <= 122))             # 'a'..'z'

@Pure
def quoted(tok: PSeq[int]) -> PSeq[int]:
    """A simple identifier token rendered as a single-quoted string literal:
    a U+0027 quote, the token code points, a closing U+0027 quote. Deep model
    of repr applied to a plain identifier (no quote/backslash/control chars)."""
    return PSeq(39) + tok + PSeq(39)

@Pure
def rendered(module: PSeq[int], class_name: PSeq[int],
             identifier: PSeq[int]) -> PSeq[int]:
    """The reference fragment, keyed by the stable identifier:
    module ++ '.' ++ class_name ++ '[' ++ "'identifier'" ++ ']'."""
    return (module + PSeq(46) + class_name + PSeq(91)
            + quoted(identifier) + PSeq(93))

@Pure
def import_line(module: PSeq[int]) -> PSeq[int]:
    """The one accompanying import statement: "import " followed by the module
    path. "import " == U+0069 6D 70 6F 72 74 20."""
    return PSeq(105, 109, 112, 111, 114, 116, 32) + module
# pure-end

def serialize_member(module: List[int], class_name: List[int],
                     identifier: List[int], payload: List[int]
                     ) -> Tuple[List[int], List[int]]:
    # pre-conditions-start
    # All four texts are read-only inputs (fractional permission). `payload` is
    # the renderable mutable-payload form; it is supplied but MUST NOT shape
    # either output (the point: key by the stable identifier, not the payload).
    Requires(Acc(list_pred(module), 1 / 2))
    Requires(Acc(list_pred(class_name), 1 / 2))
    Requires(Acc(list_pred(identifier), 1 / 2))
    Requires(Acc(list_pred(payload), 1 / 2))
    # Domain scoping: the stable identifier is a plain attribute-name token —
    # every code point an ASCII letter, digit, or underscore. That is the only
    # shape a declared attribute name can take, and it is exactly the domain
    # on which the single-quote wrap `quoted` equals the real rendering of the
    # token as a string literal. Texts with a quote, backslash, or control
    # character are outside the modeled slice.
    Requires(Forall(int, lambda k: (Implies(
        0 <= k and k < len(identifier),
        plain_token_char(identifier[k])))))
    # The rendering is a bounded amount of straight-line work and MUST
    # terminate (a total-correctness obligation). An implementation that
    # diverges before returning would satisfy the value postconditions only
    # vacuously and would never deliver the rendered fragment to its caller.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(module), 1 / 2))
    Ensures(Acc(list_pred(class_name), 1 / 2))
    Ensures(Acc(list_pred(identifier), 1 / 2))
    Ensures(Acc(list_pred(payload), 1 / 2))
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    # The fragment reconstructs the member by its STABLE identifier, grounded in
    # the module / class_name / identifier carriers (not the payload).
    Ensures(ToSeq(Result()[0]) ==
            rendered(ToSeq(module), ToSeq(class_name), ToSeq(identifier)))
    # The accompanying import statement is exactly the import of the module.
    Ensures(ToSeq(Result()[1]) == import_line(ToSeq(module)))
    # post-conditions-end
    # impl-start
    # Correct impl, RESHAPED: one concatenation expression, staged tuple local.
    imp = [105, 109, 112, 111, 114, 116, 32] + module  # type: List[int]
    frag = (module + [46] + class_name + [91] + [39]
            + identifier + [39] + [93])  # type: List[int]
    out = (frag, imp)  # type: Tuple[List[int], List[int]]
    return out
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, django__django-11815 / nagini. 13 same-spec attacks (all `same_spec=True`, all `unsound_evasions=none`), positive control verifies, prepatch bug reproduced and REJECTED. 5 attacks verified; ALL 5 faithful refined patches were MATERIALIZED AND RUN through the official harness (run_resolve) and ALL 5 RESOLVED. No verify-does-not-resolve witness found => SOUND.

**ENV:** cd swe-proof; PYTHONPATH=src SBU_BENCHMARK_DIR=benchmark-verified SBU_BENCHMARK=swe_bench_verified; PY=~/anaconda3/envs/swebench-nagini/bin/python. Attack cmd: python -m swebench_unified.adversary weakness nagini django__django-11815 <path>. Resolve cmd: python resolve_one.py <patch.diff> <tag> (calls swebench_unified.harness.run_resolve). Verifications run 3-concurrent as background jobs; logs in.

### ORACLE HEALTH (both controls run, so the 5 'resolved' verdicts are meaningful):
- patch__gold_control.diff (gold hunk regenerated by my own generator) -> RESOLVED, F2P both success, attempts=1.
- patch_NEGCTL_atk_1_payload_keyed.diff (faithful refinement of the REJECTED prepatch attack, post-patch-shaped) -> NOT RESOLVED, 'patch did not resolve in 3 attempts (consistent - not flaky)', F2P failure=[test_serialize_class_based_validators, test_serialize_enums]. So the oracle discriminates on exactly this change.

### PER-ATTACK RESULTS (path / observed):
1. atk_1_payload_keyed.py - PREPATCH BUG re-encoded (Class(value) from `payload`). exit 2 NOT-A-COUNTEREXAMPLE. Rejected for the RIGHT reason: 'Postcondition... (ToSeq(Result()[0]) == rendered(...)) might not hold' (250.9s).
2. atk_2_diverge.py - nontermination ahead of gold construction. exit 2. 'Obligation leak check failed. Loop might not take all unsatisfied obligations from the context' -> MustTerminate(2) (A5) is genuinely load-bearing.
3. atk_3b_guarded_diverge.py - divergence GUARDED on an F2P-reachable name ('A'==65). exit 2. Same obligation-leak rejection INSIDE a branch, so A5 reaches guarded control flow. (v1 atk_3_raise.py was discarded: it died on 'Not supported: Unsupported builtin function', a TRANSLATION error = rejection for the wrong reason, not evidence.)
4. atk_4_selfcall.py - unbounded recursion behind a FEASIBLE guard (len(module)>0; the guarded-self-call-goes-vacuous trap). exit 2. 'Callee serialize_member might not take all unsatisfied obligations from the caller' - so the guard was feasible and the rejection is real, not vacuous.
5. atk_5_frame_mutate.py - gold outputs + write into read-only `payload`. exit 2. 'precondition of method append might not hold. There might be insufficient permission' - the fractional-permission frame is load-bearing.
6. atk_6_leading_digit.py - junk on a LEADING-DIGIT name (plain_token_char admits it, a real attribute name never is). exit 2, postcondition violated -> the precondition is not silently narrower than it reads.
7. atk_7_quote_out_of_domain.py - junk when name starts with U+0027 (excluded by plain_token_char). CANDIDATE (31.8s). Faithful patch RESOLVED (F2P both success, attempts=1).
8. atk_8b_backslash_escape.py - A-REFERENCE probe: refines `quoted` to the REAL %r escaping (backslash-leading name) rather than the model's naive wrap. CANDIDATE (39.4s). Faithful patch RESOLVED. (v1 atk_8 discarded: 'Name "frag" already defined' = translation error, wrong reason.)
9. atk_9_payload_empty.py - junk when `payload` is empty; `payload` carries NO precondition so this is in-domain. exit 2, postcondition violated -> 'output does not depend on the mutable payload' is genuinely pinned.
10. atk_10_import_out_of_domain.py - IMPORT leg: second import line appended, only for an out-of-domain name. CANDIDATE (25.9s). Faithful patch RESOLVED.
11. atk_12_nonascii_lead.py - junk for a leading NON-ASCII code point. CANDIDATE (31.7s). Faithful patch RESOLVED. (Loop-free re-encoding; atk_11/atk_11b were discarded as wrong-reason rejections - 'precondition of function len... insufficient permission' then a postcondition failure caused by MY loop invariant's weakness, not the spec.)
12. atk_13_payload_read.py - SHARPEST A-leg/correspondence probe. refinement.md A1 asserts the post-patch impl 'reads [payload] not at all'; mapping.md §1 binds `payload` to 'a renderable form of self.value.value', which in the REAL code can only be OBTAINED by serializer_factory(self.value.value).serialize() - the very call the gold patch DELETES. Model impl merely READS payload (legal under Acc(...,1/2)) with gold-identical outputs; CANDIDATE (34.5s). Its faithful patch re-instates the deleted side-effecting callee and RESOLVED (F2P both success). So the A1 correspondence is loose in prose but not exploitable: the reinstated call is side-effect-free on every F2P-reachable value.
13. atk_14_empty_ident.py - EMPTY identifier (satisfies the Forall vacuously, so strictly in-domain). exit 2, postcondition violated.

REFINEMENT.MD AUDIT (leg kinds): A1 R, A2 A-reference, A3 A-reference, A4 R, A5 I, A6 R. NO kind-3 (unexpressible-changed-op) leg. Confirmed mechanically that the axioms region has ZERO non-comment lines and that model.py's single '@ContractOnly' occurrence is inside a comment (line 59), i.e. there is genuinely NO consumed axiom - the changed rendering is modelled DEEPLY in the pure region, which is the strongest available posture for the A legs.

A-LEG CORRESPONDENCE, INDEPENDENTLY RE-DERIVED (audit_arefs.py, exit 0 - I did NOT reuse the bundle's axiom_check.py, which is itself under audit; I transcribed the gold format strings from patch.diff and called real CPython repr/enum):
- **A2/A3:** 4176 (module, class_name, in-domain name) triples - exhaustive to length 3 over a boundary-complete alphabet plus the real F2P names - agree code-point-for-code-point with '%s.%s[%r]' and {'import %s' % module}; import set cardinality is 1 in every case.
- A2 through the REAL enum machinery: TextEnum/BinaryEnum/IntEnum members and re.RegexFlag(16) -> "re.RegexFlag['DOTALL']", {'import re'} (the F2P validator case) all match.
- A6(i): 0 in-alphabet names where quoted != %r. Every quoted-vs-%r divergence I could construct (a'b, a\\b, a\nb, ', \\, NUL) lies STRICTLY OUTSIDE the precondition, so the spec claims nothing false on its domain.
- The bundle's own axiom_check.py re-run: exit 0.

ONE DOCUMENTATION INACCURACY (not a soundness defect, no repair required): refinement.md A6 and mapping.md §1 justify the plain_token_char precondition by asserting out-of-alphabet names are 'constructible only through dynamic construction APIs, never via a class-body declaration'. That reachability claim is FALSE as written - Python 3 attribute names may be any Unicode identifier, so `class E(enum.Enum): café = 1` is a legal class-body declaration whose member name is outside the ASCII alphabet (demonstrated in audit_arefs.py A6(ii)). It is NOT exploitable: on such names CPython repr still emits the bare single-quote wrap, so `quoted` is CORRECT there and the precondition merely narrows conservatively rather than hiding a divergence - and I confirmed mechanically that a wrong impl keyed on that excluded input (atk_12) still yields a RESOLVING patch. The prose overstates the unreachability argument; the underlying domain scoping is sound.

**WHY NO BREAK EXISTS.** The spec pins the WHOLE output sequence via two closed-form deep models over the inputs, so no ungrounded-oracle echo is available (an impl returning rendered(...) literally IS the gold rendering). The remaining freedom is confined to inputs outside the precondition (quote/backslash/non-ASCII-leading names) and to reading the unconstrained `payload`. Those inputs are unreachable from the F2P/P2P suites - every member name the tests produce is a plain ASCII identifier ('A','B','DOTALL') - so any impl differing from gold ONLY there is behaviourally gold on everything the oracle observes, which is exactly what the 5 executed resolves confirm empirically rather than by argument.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Reference = /tmp worktree at base_commit e02f67ef2d with patch.diff APPLIED. Post-patch callee: EnumSerializer.serialize() -> ('%s.%s[%r]' % (module, enum_class.`__name__`, self.value.name), {'import %s' % module}).

### Positive controls run
- scripts/nagini_verify.sh on model.py: 'Verification successful', 28.75s, exit 0. So the spec is not vacuous/unverifiable.
- model_prepatch.py (identical spec regions, by-payload impl): FAILS with 'Postcondition... (ToSeq(Result()[0]) == rendered(...)) might not hold', 138.1s, exit 1 => spec senses the change (G-DIFF live, not just claimed).
- Spec regions axioms/pure/pre-conditions/post-conditions byte-identical between model.py and model_prepatch.py (only impl differs). adversary same-spec on an unmodified copy: exit 0 ('SAME'). Region plumbing confirmed.
- axiom_check.py: exit 0 (20003 names incl. F2P A/B/DOTALL + re.RegexFlag + synthesized enums).
- conformance_check.py against the PATCHED repo (py3.10 venv, asgiref present): exit 0, 100395 inputs, 0 disagreements.
- F2P sanity on the BASE (unpatched) copy: both target tests fail with re.RegexFlag(16) vs ['DOTALL'] => the patched form is what the oracle demands, so the modeled behavior is the post-patch behavior.

INDEPENDENT DIVERGENCE HUNT (atk2_diff.py, my own harness, real enum classes rather than the bundle's carrier shim): 31073 inputs, 0 divergences. Angles tried and all matching:

(1) Raw %s splices for module/class_name: '%s.%s[...]' is structurally module ++ '.' ++ class_name ++ '[' for ANY content, so I hammered module/class_name with content the model leaves unconstrained -- empty, '.', 'mod[x]', "we'ird", 'dq"uote', 'back\\slash', literal '%s'/'%r'/'%%' (format-injection attempt: %-formatting does not re-scan substituted text, so no divergence), '{}', spaces, tab, newline, NUL, RTL override, 300-char, non-ASCII e/bullet/emoji/ideographic-space. All equal rendered(). This is where a too-strong spec would most plausibly break, and it does not.

(2) identifier via %r modeled as quoted(tok) = "'" ++ tok ++ "'": EXHAUSTIVE over the precondition alphabet [A-Za-z0-9_] for lengths 0,1,2 plus a length-3 stride -- 39754 tokens, 0 mismatches vs CPython '%r'. On that alphabet repr provably picks single quotes and escapes nothing, so quoted IS the real rendering. Also swept those tokens as REAL member names and via 30000 random-name fuzz.

(3) import set: real post-patch set is always the singleton literal {'import %s' % module}; arity 1 and element == import_line(module) on every input. The pre-patch '*v_imports' union is gone, so no extra element can appear -- checked with payloads (bare object(), lambda, nested dict/list/tuple) that the PRE-patch path would have recursed into or crashed on; post-patch reads payload not at all, matching the model's 'payload must not shape either output'.

DOMAIN SCOPING IS A NARROWING, NOT AN OVER-CLAIM. I confirmed the two shapes that DO break quoted == %r are genuinely outside the precondition, i.e. the spec correctly declines to claim them rather than mis-describing them:
- Functional-API name with a quote: enum.Enum('E', {"a'b": 1}) really serializes to '`__main__`.E["a\'b"]' (repr switches delimiter) != quoted("a'b"). Excluded by Requires(Forall... plain_token_char), since ' is code point 39. A class-body declaration cannot produce this name, so no reachable input is dropped.
- str-subclass name overriding `__repr__` (enum.Enum('E', {RLie('A'): 1}) -> '`__main__`.E[RLIED]'): the name's code points are still [65] so it is IN the code-point precondition, yet the real output diverges. I judged this NOT a faithfulness defect: it is outside the R-refinement in mapping.md section 2, which binds the carrier to str (a class-body attribute name is always exactly builtins.str -- verified: type(F.A.name) is str, type(F.`__module__`) is str, type(F.`__name__`) is str). Reaching it requires handing a repr-lying str subclass to the functional API, the same dynamic-construction channel the refinement already scopes out; it is not caller-reachable from a declared enumeration and no F2P input approaches it. Noting it as the sharpest boundary I found, not as a counterexample.
- Composite flag on py3.10: re.RegexFlag(16|32).name is None -> 're.RegexFlag[None]'. name is not a str at all, so it fails the str refinement outright; also outside the modeled slice, and the F2P case uses the single flag re.S whose name is 'DOTALL'.

MustTerminate(2) only strengthens the contract (partial -> total correctness) and cannot manufacture a claim about the callee; the real body is a single straight-line format expression that always returns, so the obligation is satisfied by the gold code. I could construct NO input inside the modeled domain (str carriers, identifier over [A-Za-z0-9_]) on which the modeled function disagrees with the real patched callee. No diverging input => UNFAITHFUL-too-strong NOT established.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** NO-LEAKAGE. No relaxation in play: meta.json has NO `relaxed_leakage` key ([k for k in meta if 'relax' in k.lower()] == []) and there is no RELAXED_LEAKAGE.md in the bundle, so this is an ordinary strict leakage judgement, not an inherited disposition. I also ran leakage.reviewer_directed() over every file in the bundle (model.py, model_prepatch.py, refinement.md, mapping.md, properties.py, axiom_check.py, conformance_check.py, meta.json, verdict.md, pbt_result.json): zero hits. No bundle file addresses me or tells me which verdict to record.

### WHAT I MEASURED (my own runs, not the recorded stamps):
1. Spec view derived myself: markers.spec_view(model.py, nagini backend) -> sha256 4fb2383a932500f1c634b6f72366aec7ece820981b77fc32f4e5c8cfbafbceba, and markers.region_hashes agrees with gates.G-HYGIENE.data.region_hashes exactly. unified diff model.py vs spec view: the ONLY elided content is the 12-line straight-line concatenation impl (frag = module+[46]+class_name+[91]+[39]+identifier+[39]+[93]; imp = 'import '+module), which is already fully entailed by the two value postconditions. Nothing else is hidden, so nothing else can be leaked by the elision.
2. G-LEAK re-run by me, not read off meta.json: leakage.screen(model.py, nagini, patch.diff, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. Note this is the screen against the SOLVER-VISIBLE problem_statement only (the module correctly excludes hints_text).
3. Token sweep of the spec view for repo/gold vocabulary: 0 hits for serializer, EnumSerializer, serializer_factory, self.value, %r, `__name__`, `__module__`, v_imports, v_string, migration, Status, GOOD, CharField, gettext, patch, gold, fix, bug, prepatch, pre-patch, regression, 'instead of'. The 1 'diff' hit is the substring in 'differently'; the 3 'repr' hits and 2 'enum' hits are generic behavioural prose ('repr of a simple identifier token', 'enumeration member'), naming no patched symbol. 'django' appears once, only in the instance-id line of the docstring title (django__django-11815), which is the instance name the consumer is handed anyway.
4. Gold model verifies and G-AX passes on my runs: nagini_verify.sh model.py -> 'Verification successful' in 40.9s, EXIT=0; python3 axiom_check.py -> EXIT=0 ('quoted/rendered/import_line deep models == real repr + real post-patch enum serializer over 20003 member names'). So the disposition does not lean on an unsound core.

**DISCRIMINATOR IS PUBLIC.** The facet the spec senses is name-vs-payload keying. I confirmed this by running the pre-patch variant myself: nagini_verify.sh model_prepatch.py -> FAILS in 166.2s with exactly one error, 'Postcondition of serialize_member might not hold. Assertion (ToSeq(Result()[0]) == rendered(ToSeq(module), ToSeq(class_name), ToSeq(identifier))) might not hold.' The failing clause is the STRING postcondition and nothing else. That discriminator is verbatim public in problem_statement, which states both the name-not-value diagnosis ('uses the value of the Enum object instead of the its name... Shouldn't the code... uses the name of the Status Enum GOOD, not the value of it, since it is changeable?') AND the exact single-quoted bracket-subscript target expression ('It should be: ("status", models.CharField(default=Status['GOOD'], max_length=128))'). The translation rationale in the spec view mirrors the public gettext_lazy / ValueError narrative. So every clause that does discriminating work sits at or below problem_statement disclosure level.

THE ONE CLAUSE PS IS SILENT ON, AND WHY IT IS NOT A LEAK. Spec view line 22-24: 'The single accompanying import statement is the import of the member's module, and ONLY that -- no further imports derived from rendering the payload.' problem_statement says nothing about imports, and notably the hints_text diff KEEPS *v_imports, so 'ONLY that' is gold-internal. I tested it two ways instead of arguing it:

  (a) Load-bearing for soundness: I built a same-spec attack keeping the gold string but tampering the import output (imp = 'import '+module+payload). markers.same_spec -> True; adversary weakness -> 'NOT-A-COUNTEREXAMPLE: attack does not verify (verification failed) -- the spec rejected this impl', EXIT=2. And the F2P test patch asserts the import set EXACTLY ({'import migrations.test_writer'}), so an impl emitting an extra import fails F2P. Dropping that postcondition to dodge the disclosure would therefore make the spec admit a verifying impl that does not resolve -- i.e. it is required for verify=>resolve, not optional narration.

  (b) Non-discriminating on every reachable input: I ran the real pre-patch serializer in a worktree at base_commit ( at e02f67ef2d) and measured the payload-derived import set for each F2P member: TextEnum.A, TextTranslatedEnum.A, BinaryEnum.A, IntEnum.B, re.RegexFlag.DOTALL all give v_imports == set() (payloads are plain str/bytes/int, routed to BaseSimpleSerializer which returns (repr(v), set())). So pre-patch {'import %s'%module, *v_imports} == post-patch {'import %s'%module} on every tested input: the clause holds identically on BOTH sides of the edit and hands the solver no bit that tells them which side to write. Separately, 'import <module>' is pre-existing UNCHANGED code visible in the base_commit source the solver already reads (serializer.py:124).

AUDITOR SCAFFOLDING, NOT DISCLOSURE. MustTerminate(2) and the plain_token_char domain-scoping precondition have no counterpart in the gold patch at all (the gold has no identifier guard and no termination annotation), so they cannot disclose it; per refinement.md A5/A6 they exist to close a diverge-before-return hole and to stop the spec over-claiming repr on names carrying a quote/backslash. Disclosing them narrows the spec's domain -- it does not hand over an edit.

OBSERVATION (bookkeeping, not a leakage finding): meta.json's TOP-LEVEL region_hashes block is stale relative to the file -- its pre-conditions (adc70167...), pure (5a854926...) and spec_view (62be1c10...) disagree with what I computed from model.py, while gates.G-HYGIENE.data.region_hashes matches my computation byte-for-byte. The stale block looks to predate the MustTerminate + plain_token_char repair. This does not weaken the leakage disposition (G-LEAK/G-HYGIENE were stamped one second apart at the same code_version on the CURRENT spec view hash, and I re-ran the screen on the current file myself), but the top-level block should be re-stamped.

Facet re-confirmed: the name-vs-payload keying discriminator, which is public in problem_statement; the only PS-silent clause (singleton import set) is soundness-required and provably non-discriminating on all F2P-reachable inputs. No spec-view line discloses the gold edit beyond the public problem_statement.

**NO-LEAKAGE.** No relaxation in play: meta.json has NO `relaxed_leakage` key ([k for k in meta if 'relax' in k.lower()] == []) and there is no RELAXED_LEAKAGE.md in the bundle, so this is an ordinary strict leakage judgement, not an inherited disposition. I also ran leakage.reviewer_directed() over every file in the bundle (model.py, model_prepatch.py, refinement.md, mapping.md, properties.py, axiom_check.py, conformance_check.py, meta.json, verdict.md, pbt_result.json): zero hits. No bundle file addresses me or tells me which verdict to record.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
