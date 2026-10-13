# P2 adversarial audit — django__django-16877

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -173,8 +173,8 @@
     Ensures(Implies(not item.is_safe, Result().chars == escaped_seq(item.chars)))
     # post-conditions-end
     # impl-start
-    if item.is_safe:
-        return Elem(item.chars, True)
+    # ATTACK 1 (prepatch double-escape): escape EVERY item unconditionally,
+    # ignoring the already-safe flag -> re-escapes safe items (double escaping).
     return Elem(escape_codepoints(item.chars), True)
     # impl-end
 
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -173,9 +173,9 @@
     Ensures(Implies(not item.is_safe, Result().chars == escaped_seq(item.chars)))
     # post-conditions-end
     # impl-start
-    if item.is_safe:
-        return Elem(item.chars, True)
-    return Elem(escape_codepoints(item.chars), True)
+    # ATTACK 2 (safeseq mistake): merely MARK each item safe without escaping
+    # its content -> an unsafe item keeps its raw HTML-significant characters.
+    return Elem(item.chars, True)
     # impl-end
 
 
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -205,9 +205,10 @@
             Result()[k].chars == escaped_seq(value[k].chars)))))
     # post-conditions-end
     # impl-start
+    # ATTACK 3 (boundary / off-by-one): stop one short, dropping the last item.
     result = []  # type: List[Elem]
     i = 0
-    while i < len(value):
+    while i < len(value) - 1:
         # invariants-start
         Invariant(Acc(list_pred(value), 1 / 2))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(value),
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -141,19 +141,9 @@
     Ensures(Result() == escaped_seq(text))
     # post-conditions-end
     # impl-start
-    result = PSeq(0).take(0)  # type: PSeq[int]
-    i = len(text)
-    while i > 0:
-        # invariants-start
-        Invariant(0 <= i and i <= len(text))
-        Invariant(result == escaped_seq(text.drop(i)))
-        # invariants-end
-        c = text[i - 1]
-        Assert(text.drop(i - 1)[0] == c)
-        Assert(text.drop(i - 1).drop(1) == text.drop(i))
-        result = entity(c) + result
-        i = i - 1
-    return result
+    # ATTACK 4 (control-flow-effect / identity escape): return the text
+    # unchanged instead of the per-code-point substitution.
+    return text
     # impl-end
 
 
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -173,9 +173,11 @@
     Ensures(Implies(not item.is_safe, Result().chars == escaped_seq(item.chars)))
     # post-conditions-end
     # impl-start
+    # ATTACK 5 (swapped branch): escape when the item IS safe and pass through
+    # when it is NOT -- inverts the conditional.
     if item.is_safe:
-        return Elem(item.chars, True)
-    return Elem(escape_codepoints(item.chars), True)
+        return Elem(escape_codepoints(item.chars), True)
+    return Elem(item.chars, True)
     # impl-end
 
 
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -223,7 +223,9 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and not value[k].is_safe,
                   result[k].chars == escaped_seq(value[k].chars)))))
         # invariants-end
-        result.append(escape_when_unsafe_item(value[i]))
+        # ATTACK 6 (wrong-index / ungrounded map): always transform value[0]
+        # instead of value[i] -- breaks per-index alignment for i>0.
+        result.append(escape_when_unsafe_item(value[0]))
         i = i + 1
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -173,9 +173,11 @@
     Ensures(Implies(not item.is_safe, Result().chars == escaped_seq(item.chars)))
     # post-conditions-end
     # impl-start
-    if item.is_safe:
-        return Elem(item.chars, True)
-    return Elem(escape_codepoints(item.chars), True)
+    # ATTACK 7 (correct echo, reordered branch): logically identical to gold --
+    # escape when NOT already safe, else pass through. Should verify AND resolve.
+    if not item.is_safe:
+        return Elem(escape_codepoints(item.chars), True)
+    return Elem(item.chars, True)
     # impl-end
 
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-16877.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A "per-element marking" transform for a SEQUENCE of textual items. Given an
  ordered sequence of items, it produces an ordered sequence of the SAME length,
  aligned one-to-one with the input, where the i-th output item is the
  *escape-when-needed* form of the i-th input item:

    (1) An item that has NOT yet been marked as safe for HTML output has each of
        the five HTML-significant code points replaced by its constant entity
        sequence (the ampersand handled first so the ampersands inside emitted
        entities are not themselves re-escaped; the apostrophe U+0027 encoded as
        `&#x27;`), and every other code point passes through unchanged. Such an
        item is escaped exactly once.

    (2) An item that has ALREADY been marked as safe for HTML output is left
        byte-for-byte unchanged -- it is NOT escaped again (no double escaping).

  Every output item is marked safe for HTML output, and the output sequence has
  exactly as many items as the input, in the same order. This makes the result
  independent of any surrounding auto-escaping context: each item already
  carries its final HTML form.

An item is modelled as a minimal object exposing only the two touched aspects:
its character content (`chars`, the Unicode code points; Nagini bans `str`
indexing, so strings are sequences of code points carried by `PSeq[int]`) and
whether it has already been marked safe for HTML output (`is_safe`). The
sequence of items is a `List[Elem]`.

The per-item escape-when-needed transform is modelled as its own contracted
function (`escape_when_unsafe_item`); the sequence transform (`escape_each`)
calls it and uses its contract directly (it is under specification, not an
axiom). The HTML escape of an item's content is modelled DEEPLY as a verified
per-code-point substitution (`escaped_seq`), whose equality to the real stdlib
escaper is checked out-of-band by axiom_check.py (G-AX), not consumed as an
axiom. No callee is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class Elem:
    """One item of the sequence. Carries only the two touched aspects: the
    character content (`chars`) and whether the item has already been marked
    safe for HTML output (`is_safe`)."""

    def __init__(self, chars: PSeq[int], is_safe: bool) -> None:
        # pre-conditions-start
        Requires(True)
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.chars) and Acc(self.is_safe))  # type: ignore
        Ensures(self.chars == chars)
        Ensures(self.is_safe == is_safe)
        # post-conditions-end
        # impl-start
        self.chars = chars      # type: PSeq[int]
        self.is_safe = is_safe  # type: bool
        # impl-end


# axioms-start
# (no axioms: the per-item escape-when-needed transform is modelled deeply -- the
# HTML escape of an item's content is the spelled-out per-code-point fold
# `escaped_seq`, validated == the real stdlib escaper out-of-band by axiom_check.py
# (G-AX); the safe-passthrough branch is the identity on the content; and the
# sequence transform uses the per-item function's contract, not an axiom.)
# axioms-end


# pure-start
@Pure
def seq_amp() -> PSeq[int]:
    # '&amp;'
    return PSeq(38, 97, 109, 112, 59)


@Pure
def seq_lt() -> PSeq[int]:
    # '&lt;'
    return PSeq(38, 108, 116, 59)


@Pure
def seq_gt() -> PSeq[int]:
    # '&gt;'
    return PSeq(38, 103, 116, 59)


@Pure
def seq_quot() -> PSeq[int]:
    # '&quot;'
    return PSeq(38, 113, 117, 111, 116, 59)


@Pure
def seq_apos_hex() -> PSeq[int]:
    # '&#x27;'  (the apostrophe entity required of the escaper)
    return PSeq(38, 35, 120, 50, 55, 59)


@Pure
def entity(c: int) -> PSeq[int]:
    """Entity sequence emitted for a single code point: the five significant
    ones expand, every other code point maps to itself."""
    if c == 38:        # '&'
        return seq_amp()
    if c == 60:        # '<'
        return seq_lt()
    if c == 62:        # '>'
        return seq_gt()
    if c == 34:        # '"'
        return seq_quot()
    if c == 39:        # "'"  -> &#x27;
        return seq_apos_hex()
    return PSeq(c)


@Pure
def escaped_seq(s: PSeq[int]) -> PSeq[int]:
    """The HTML escape of a whole sequence: concatenate the per-code-point
    entity sequences. Front-recursive so a single unfold is available to
    callers."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return entity(s[0]) + escaped_seq(s.drop(1))
# pure-end


def escape_codepoints(text: PSeq[int]) -> PSeq[int]:
    """The HTML escape of an item's character content: the per-code-point entity
    substitution (deep model of the real stdlib escaper; A-reference, G-AX)."""
    # pre-conditions-start
    Requires(True)
    # pre-conditions-end
    # post-conditions-start
    # The escaped output is the per-code-point entity substitution.
    Ensures(Result() == escaped_seq(text))
    # post-conditions-end
    # impl-start
    result = PSeq(0).take(0)  # type: PSeq[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(text))
        Invariant(result == escaped_seq(text.drop(i)))
        # invariants-end
        c = text[i - 1]
        Assert(text.drop(i - 1)[0] == c)
        Assert(text.drop(i - 1).drop(1) == text.drop(i))
        result = entity(c) + result
        i = i - 1
    return result
    # impl-end


def escape_when_unsafe_item(item: Elem) -> Elem:
    # pre-conditions-start
    Requires(Acc(item.chars, 1 / 4) and Acc(item.is_safe, 1 / 4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(item.chars, 1 / 4) and Acc(item.is_safe, 1 / 4))
    Ensures(Acc(Result().chars) and Acc(Result().is_safe))
    # The produced item is marked safe for HTML output.
    Ensures(Result().is_safe)
    # (2) An already-safe item is left byte-for-byte unchanged (no re-escaping).
    Ensures(Implies(item.is_safe, Result().chars == item.chars))
    # (1) An item not yet marked safe is escaped exactly once: its content is the
    # per-code-point entity substitution.
    Ensures(Implies(not item.is_safe, Result().chars == escaped_seq(item.chars)))
    # post-conditions-end
    # impl-start
    if item.is_safe:
        return Elem(item.chars, True)
    return Elem(escape_codepoints(item.chars), True)
    # impl-end


def escape_each(value: List[Elem]) -> List[Elem]:
    # pre-conditions-start
    Requires(Acc(list_pred(value), 1 / 2))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(value),
             Acc(value[k].chars, 1 / 4) and Acc(value[k].is_safe, 1 / 4)))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 2))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(value),
            Acc(value[k].chars, 1 / 4) and Acc(value[k].is_safe, 1 / 4)))))
    Ensures(Acc(list_pred(Result())))
    # The result is aligned one-to-one with the input, IN ORDER, same length.
    Ensures(len(Result()) == len(value))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(value),
            Acc(Result()[k].chars) and Acc(Result()[k].is_safe)))))
    # Every output item is marked safe ...
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(value),
            Result()[k].is_safe))))
    # ... an already-safe input item passes through unchanged ...
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(value) and value[k].is_safe,
            Result()[k].chars == value[k].chars))))
    # ... a not-yet-safe input item is escaped exactly once.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(value) and not value[k].is_safe,
            Result()[k].chars == escaped_seq(value[k].chars)))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[Elem]
    i = 0
    while i < len(value):
        # invariants-start
        Invariant(Acc(list_pred(value), 1 / 2))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(value),
                  Acc(value[k].chars, 1 / 4) and Acc(value[k].is_safe, 1 / 4)))))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(value))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                  Acc(result[k].chars) and Acc(result[k].is_safe)))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i, result[k].is_safe))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and value[k].is_safe,
                  result[k].chars == value[k].chars))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and not value[k].is_safe,
                  result[k].chars == escaped_seq(value[k].chars)))))
        # invariants-end
        result.append(escape_when_unsafe_item(value[i]))
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity) audit, django__django-16877 nagini. VERDICT: SOUND.

SPEC SHAPE: escape_each(List[Elem]) + escape_when_unsafe_item(Elem) + deep pure fold escaped_seq/entity. Postconditions FULLY pin every output item per index: (i) len(Result)==len(value); (ii) per-index Acc + is_safe==True for every output; (iii) already-safe input -> Result[k].chars==value[k].chars (no re-escape); (iv) not-safe input -> Result[k].chars==escaped_seq(value[k].chars) (escape exactly once, ampersand-first, ' -> &#x27;). This is a per-index TOTAL functional spec: any verifying impl is forced to the gold output on the modeled domain, leaving no room for a verifying-but-wrong impl.

ATTACKS (all built by copying model.py, editing ONLY impl regions; all confirmed same-spec via `adversary same-spec` exit 0; cmd `python -m swebench_unified.adversary weakness nagini django__django-16877 <path>`):
- atk_1.py (prepatch double-escape: escape unconditionally, ignore is_safe): NOT-A-COUNTEREXAMPLE, does not verify (fails Implies(item.is_safe, Result.chars==item.chars)). Reproduces gold prepatch bug.
- atk_2.py (safeseq mistake: mark safe, no escape): NOT-A-COUNTEREXAMPLE, does not verify (fails not-safe escape clause).
- atk_3.py (boundary/off-by-one: while i < len(value)-1, drops last item): NOT-A-COUNTEREXAMPLE, does not verify (fails len(Result)==len(value)).
- atk_4.py (control-flow-effect: escape_codepoints returns text unchanged): NOT-A-COUNTEREXAMPLE, does not verify (fails escape_codepoints Ensures Result==escaped_seq(text)).
- atk_5.py (swapped branch: escape safe items, pass through unsafe): NOT-A-COUNTEREXAMPLE, does not verify (fails both is_safe passthrough and not-safe escape clauses).
- atk_6.py (wrong-index/ungrounded map: always transform value[0]): NOT-A-COUNTEREXAMPLE, does not verify (fails per-index alignment for i>0).
- atk_7.py (correct echo, reordered branch `if not item.is_safe`): CANDIDATE-COUNTEREXAMPLE, shares spec AND verifies (42.2s). PROTOCOL: materialized faithful refined patch (= gold escapeseq body [conditional_escape(obj) for obj in value], the ONLY new op; the reorder is inside the modeled conditional_escape, an existing repo fn) and RAN it through the official harness: swebench_unified.harness.run_resolve('django__django-16877', patch, timeout=1800) => RESOLVED=True, COMPLETED=True, note='resolved', attempts=1. Candidate is CORRECT -> does NOT break the spec (verify=>correct holds here).

POSITIVE CONTROL: pos_control.py (== model.py) VERIFIED in 30.4s (adversary verify exit 0).

A-LEG / MODEL<->PATCH CORRESPONDENCE AUDIT (my focus):
- refinement.md legs: A1=R (value:List[Elem] <-> iterable), A2=I (append-loop <-> list comprehension), A3=I (per-item call), B1=R (is_safe passthrough <-> conditional_escape __html__ branch, identity on content), B2=A-reference (unsafe escape modeled deeply by escaped_seq/entity, NO consumed axiom). No kind-3 steps, no consumed @ContractOnly axiom.
- A-reference (B2) correspondence VALIDATED: ran axiom_check.py (G-AX) => exit 0, 'escaped_seq deep model == real html.escape and matches conditional_escape on both branches over 23 boundary + 20000 fuzz inputs'. Deep fold entity/escaped_seq matches the real CPython html.escape(quote=True) reached via conditional_escape->escape->SafeString(html.escape(str(text))). ampersand-first ensures no re-escape; ' -> &#x27; correct. Safe branch (__html__ passthrough) also cross-checked. Mapping.md bindings (escapeseq@defaultfilters.py:444, conditional_escape@html.py:82, html.escape) are accurate against base_commit 98f6ada0e2058d67d91fb6c16482411ec2ca0967.

COMPLETENESS: 7 distinct wrong-impl families exercised (partial-domain/mark-only, prepatch double-escape, boundary off-by-one, control-flow-effect identity, swapped branch, wrong-index, plus correct echo). 6 wrong impls all REJECTED by the spec (do not verify); the 1 verifying candidate RESOLVES. No verifier timeouts or inconclusive runs (grep confirmed). All commands and outputs captured *.out, poscontrol.out, atk_7.patch.diff.

CONCLUSION: No same-spec, Nagini-verifying implementation exists whose faithful refined patch fails to resolve. The spec's per-index total postconditions admit exactly the gold behavior on the modeled domain. verify=>correct upheld. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-16877.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A "per-element marking" transform for a SEQUENCE of textual items. Given an
  ordered sequence of items, it produces an ordered sequence of the SAME length,
  aligned one-to-one with the input, where the i-th output item is the
  *escape-when-needed* form of the i-th input item:

    (1) An item that has NOT yet been marked as safe for HTML output has each of
        the five HTML-significant code points replaced by its constant entity
        sequence (the ampersand handled first so the ampersands inside emitted
        entities are not themselves re-escaped; the apostrophe U+0027 encoded as
        `&#x27;`), and every other code point passes through unchanged. Such an
        item is escaped exactly once.

    (2) An item that has ALREADY been marked as safe for HTML output is left
        byte-for-byte unchanged -- it is NOT escaped again (no double escaping).

  Every output item is marked safe for HTML output, and the output sequence has
  exactly as many items as the input, in the same order. This makes the result
  independent of any surrounding auto-escaping context: each item already
  carries its final HTML form.

An item is modelled as a minimal object exposing only the two touched aspects:
its character content (`chars`, the Unicode code points; Nagini bans `str`
indexing, so strings are sequences of code points carried by `PSeq[int]`) and
whether it has already been marked safe for HTML output (`is_safe`). The
sequence of items is a `List[Elem]`.

The per-item escape-when-needed transform is modelled as its own contracted
function (`escape_when_unsafe_item`); the sequence transform (`escape_each`)
calls it and uses its contract directly (it is under specification, not an
axiom). The HTML escape of an item's content is modelled DEEPLY as a verified
per-code-point substitution (`escaped_seq`), whose equality to the real stdlib
escaper is checked out-of-band by axiom_check.py (G-AX), not consumed as an
axiom. No callee is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class Elem:
    """One item of the sequence. Carries only the two touched aspects: the
    character content (`chars`) and whether the item has already been marked
    safe for HTML output (`is_safe`)."""

    def __init__(self, chars: PSeq[int], is_safe: bool) -> None:
        # pre-conditions-start
        Requires(True)
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.chars) and Acc(self.is_safe))  # type: ignore
        Ensures(self.chars == chars)
        Ensures(self.is_safe == is_safe)
        # post-conditions-end
        # impl-start
        self.chars = chars      # type: PSeq[int]
        self.is_safe = is_safe  # type: bool
        # impl-end


# axioms-start
# (no axioms: the per-item escape-when-needed transform is modelled deeply -- the
# HTML escape of an item's content is the spelled-out per-code-point fold
# `escaped_seq`, validated == the real stdlib escaper out-of-band by axiom_check.py
# (G-AX); the safe-passthrough branch is the identity on the content; and the
# sequence transform uses the per-item function's contract, not an axiom.)
# axioms-end


# pure-start
@Pure
def seq_amp() -> PSeq[int]:
    # '&amp;'
    return PSeq(38, 97, 109, 112, 59)


@Pure
def seq_lt() -> PSeq[int]:
    # '&lt;'
    return PSeq(38, 108, 116, 59)


@Pure
def seq_gt() -> PSeq[int]:
    # '&gt;'
    return PSeq(38, 103, 116, 59)


@Pure
def seq_quot() -> PSeq[int]:
    # '&quot;'
    return PSeq(38, 113, 117, 111, 116, 59)


@Pure
def seq_apos_hex() -> PSeq[int]:
    # '&#x27;'  (the apostrophe entity required of the escaper)
    return PSeq(38, 35, 120, 50, 55, 59)


@Pure
def entity(c: int) -> PSeq[int]:
    """Entity sequence emitted for a single code point: the five significant
    ones expand, every other code point maps to itself."""
    if c == 38:        # '&'
        return seq_amp()
    if c == 60:        # '<'
        return seq_lt()
    if c == 62:        # '>'
        return seq_gt()
    if c == 34:        # '"'
        return seq_quot()
    if c == 39:        # "'"  -> &#x27;
        return seq_apos_hex()
    return PSeq(c)


@Pure
def escaped_seq(s: PSeq[int]) -> PSeq[int]:
    """The HTML escape of a whole sequence: concatenate the per-code-point
    entity sequences. Front-recursive so a single unfold is available to
    callers."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return entity(s[0]) + escaped_seq(s.drop(1))
# pure-end


def escape_codepoints(text: PSeq[int]) -> PSeq[int]:
    """The HTML escape of an item's character content: the per-code-point entity
    substitution (deep model of the real stdlib escaper; A-reference, G-AX)."""
    # pre-conditions-start
    Requires(True)
    # pre-conditions-end
    # post-conditions-start
    # The escaped output is the per-code-point entity substitution.
    Ensures(Result() == escaped_seq(text))
    # post-conditions-end
    # impl-start
    result = PSeq(0).take(0)  # type: PSeq[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(text))
        Invariant(result == escaped_seq(text.drop(i)))
        # invariants-end
        c = text[i - 1]
        Assert(text.drop(i - 1)[0] == c)
        Assert(text.drop(i - 1).drop(1) == text.drop(i))
        result = entity(c) + result
        i = i - 1
    return result
    # impl-end


def escape_when_unsafe_item(item: Elem) -> Elem:
    # pre-conditions-start
    Requires(Acc(item.chars, 1 / 4) and Acc(item.is_safe, 1 / 4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(item.chars, 1 / 4) and Acc(item.is_safe, 1 / 4))
    Ensures(Acc(Result().chars) and Acc(Result().is_safe))
    # The produced item is marked safe for HTML output.
    Ensures(Result().is_safe)
    # (2) An already-safe item is left byte-for-byte unchanged (no re-escaping).
    Ensures(Implies(item.is_safe, Result().chars == item.chars))
    # (1) An item not yet marked safe is escaped exactly once: its content is the
    # per-code-point entity substitution.
    Ensures(Implies(not item.is_safe, Result().chars == escaped_seq(item.chars)))
    # post-conditions-end
    # impl-start
    if item.is_safe:
        return Elem(item.chars, True)
    return Elem(escape_codepoints(item.chars), True)
    # impl-end


def escape_each(value: List[Elem]) -> List[Elem]:
    # pre-conditions-start
    Requires(Acc(list_pred(value), 1 / 2))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(value),
             Acc(value[k].chars, 1 / 4) and Acc(value[k].is_safe, 1 / 4)))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 2))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(value),
            Acc(value[k].chars, 1 / 4) and Acc(value[k].is_safe, 1 / 4)))))
    Ensures(Acc(list_pred(Result())))
    # The result is aligned one-to-one with the input, IN ORDER, same length.
    Ensures(len(Result()) == len(value))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(value),
            Acc(Result()[k].chars) and Acc(Result()[k].is_safe)))))
    # Every output item is marked safe ...
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(value),
            Result()[k].is_safe))))
    # ... an already-safe input item passes through unchanged ...
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(value) and value[k].is_safe,
            Result()[k].chars == value[k].chars))))
    # ... a not-yet-safe input item is escaped exactly once.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(value) and not value[k].is_safe,
            Result()[k].chars == escaped_seq(value[k].chars)))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[Elem]
    i = 0
    while i < len(value):
        # invariants-start
        Invariant(Acc(list_pred(value), 1 / 2))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(value),
                  Acc(value[k].chars, 1 / 4) and Acc(value[k].is_safe, 1 / 4)))))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(value))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                  Acc(result[k].chars) and Acc(result[k].is_safe)))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i, result[k].is_safe))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and value[k].is_safe,
                  result[k].chars == value[k].chars))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and not value[k].is_safe,
                  result[k].chars == escaped_seq(value[k].chars)))))
        # invariants-end
        result.append(escape_when_unsafe_item(value[i]))
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity) audit, django__django-16877 nagini. VERDICT: SOUND.

SPEC SHAPE: escape_each(List[Elem]) + escape_when_unsafe_item(Elem) + deep pure fold escaped_seq/entity. Postconditions FULLY pin every output item per index: (i) len(Result)==len(value); (ii) per-index Acc + is_safe==True for every output; (iii) already-safe input -> Result[k].chars==value[k].chars (no re-escape); (iv) not-safe input -> Result[k].chars==escaped_seq(value[k].chars) (escape exactly once, ampersand-first, ' -> &#x27;). This is a per-index TOTAL functional spec: any verifying impl is forced to the gold output on the modeled domain, leaving no room for a verifying-but-wrong impl.

ATTACKS (all built by copying model.py, editing ONLY impl regions; all confirmed same-spec via `adversary same-spec` exit 0; cmd `python -m swebench_unified.adversary weakness nagini django__django-16877 <path>`):
- atk_1.py (prepatch double-escape: escape unconditionally, ignore is_safe): NOT-A-COUNTEREXAMPLE, does not verify (fails Implies(item.is_safe, Result.chars==item.chars)). Reproduces gold prepatch bug.
- atk_2.py (safeseq mistake: mark safe, no escape): NOT-A-COUNTEREXAMPLE, does not verify (fails not-safe escape clause).
- atk_3.py (boundary/off-by-one: while i < len(value)-1, drops last item): NOT-A-COUNTEREXAMPLE, does not verify (fails len(Result)==len(value)).
- atk_4.py (control-flow-effect: escape_codepoints returns text unchanged): NOT-A-COUNTEREXAMPLE, does not verify (fails escape_codepoints Ensures Result==escaped_seq(text)).
- atk_5.py (swapped branch: escape safe items, pass through unsafe): NOT-A-COUNTEREXAMPLE, does not verify (fails both is_safe passthrough and not-safe escape clauses).
- atk_6.py (wrong-index/ungrounded map: always transform value[0]): NOT-A-COUNTEREXAMPLE, does not verify (fails per-index alignment for i>0).
- atk_7.py (correct echo, reordered branch `if not item.is_safe`): CANDIDATE-COUNTEREXAMPLE, shares spec AND verifies (42.2s). PROTOCOL: materialized faithful refined patch (= gold escapeseq body [conditional_escape(obj) for obj in value], the ONLY new op; the reorder is inside the modeled conditional_escape, an existing repo fn) and RAN it through the official harness: swebench_unified.harness.run_resolve('django__django-16877', patch, timeout=1800) => RESOLVED=True, COMPLETED=True, note='resolved', attempts=1. Candidate is CORRECT -> does NOT break the spec (verify=>correct holds here).

POSITIVE CONTROL: pos_control.py (== model.py) VERIFIED in 30.4s (adversary verify exit 0).

A-LEG / MODEL<->PATCH CORRESPONDENCE AUDIT (my focus):
- refinement.md legs: A1=R (value:List[Elem] <-> iterable), A2=I (append-loop <-> list comprehension), A3=I (per-item call), B1=R (is_safe passthrough <-> conditional_escape __html__ branch, identity on content), B2=A-reference (unsafe escape modeled deeply by escaped_seq/entity, NO consumed axiom). No kind-3 steps, no consumed @ContractOnly axiom.
- A-reference (B2) correspondence VALIDATED: ran axiom_check.py (G-AX) => exit 0, 'escaped_seq deep model == real html.escape and matches conditional_escape on both branches over 23 boundary + 20000 fuzz inputs'. Deep fold entity/escaped_seq matches the real CPython html.escape(quote=True) reached via conditional_escape->escape->SafeString(html.escape(str(text))). ampersand-first ensures no re-escape; ' -> &#x27; correct. Safe branch (__html__ passthrough) also cross-checked. Mapping.md bindings (escapeseq@defaultfilters.py:444, conditional_escape@html.py:82, html.escape) are accurate against base_commit 98f6ada0e2058d67d91fb6c16482411ec2ca0967.

COMPLETENESS: 7 distinct wrong-impl families exercised (partial-domain/mark-only, prepatch double-escape, boundary off-by-one, control-flow-effect identity, swapped branch, wrong-index, plus correct echo). 6 wrong impls all REJECTED by the spec (do not verify); the 1 verifying candidate RESOLVES. No verifier timeouts or inconclusive runs (grep confirmed). All commands and outputs captured *.out, poscontrol.out, atk_7.patch.diff.

CONCLUSION: No same-spec, Nagini-verifying implementation exists whose faithful refined patch fails to resolve. The spec's per-index total postconditions admit exactly the gold behavior on the modeled domain. verify=>correct upheld. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of django__django-16877 nagini bundle. Result: FAITHFUL — no diverging input found between the modeled function and the real repo callee.

Real repo (base 98f6ada0e2058d67d91fb6c16482411ec2ca0967): gold patch is PURELY ADDITIVE — escapeseq(value) = [conditional_escape(obj) for obj in value] added to django/template/defaultfilters.py after escape_filter (line 448). conditional_escape (django/utils/html.py:82): if isinstance(text, Promise): text=str(text); if hasattr(text,'__html__'): return text.__html__() (already-safe passthrough, unchanged); else: return escape(text)=SafeString(html.escape(str(text))). html.escape default quote=True: & -> &amp; (FIRST), < -> &lt;, > -> &gt;, " -> &quot;, ' -> &#x27;, else identity.

Spec (escape_each + escape_when_unsafe_item + deep escaped_seq/entity) postconditions assert EXACTLY: (i) len(Result)==len(value) + per-index order alignment (matches order-sensitive list comprehension followed by join); (ii) already-safe input item content unchanged AND stays safe (matches __html__ branch); (iii) not-safe input item content == escaped_seq per-code-point substitution (& -> &amp;, < -> &lt;, > -> &gt;, " -> &quot;, ' -> &#x27;, ampersand-first, else identity) (matches escape() path); (iv) every output is_safe. Neither stronger nor weaker than the real callee on the abstraction domain.

Type refinement is sound: str content <-> PSeq[int] code points; is_safe <-> has __html__ / SafeData; SafeString/mark_safe/str() are identities on observable content (F2P tests compare rendered text after join).

Machine-checked evidence:
- scripts/nagini_verify.sh on frozen model.py: exit 0 (Verification successful, 44.9s) — positive control verifies.
- Independent differential: deep model escaped_seq (ENT map, ampersand-first) vs REAL html.escape over 200,000 randomized inputs spanning code points 0-300 plus all five specials and non-ASCII (é, 你): 0 divergences.
- Direct cross-check of the REAL escapeseq (django.setup) output against the three spec clauses on plain, mark_safe, mixed, and empty inputs: all match — passthrough for safe items, per-code-point escape for unsafe, order/length preserved, every output SafeData.
- G-AX (axiom_check.py) recorded exit 0 (escaped_seq == real html.escape and matches conditional_escape both branches over 23 boundary + 20000 fuzz). G-CONF: 100031 checked, 0 disagreements (seed 16877).

No consumed axiom; single kind-A construct is the A-reference deep escape model, validated out-of-band. No input exists where the modeled function disagrees with the real escapeseq/conditional_escape. Spec is faithful; it does not drift and is not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged the solver-visible spec view (spec_view projection of model.py: leading docstring + Elem/pure/entity/escaped_seq/escape_codepoints/escape_when_unsafe_item/escape_each contracts, with impl regions elided). mapping.md and refinement.md quote the gold verbatim but are AUDITOR-facing, not part of the spec view G-PANEL-3 screens.

Mechanical G-LEAK screen PASSES (rep.passed=True, 0 hard failures): no diff markers, no reproduced gold line (the gold body `[conditional_escape(obj) for obj in value]` does not appear), no patched file path `django/template/defaultfilters.py`, no patched symbol (`escapeseq`, `escape_filter`) embedded in any spec-view identifier or comment, no bug/fix narration. Bundle is not relaxed (no RELAXED_LEAKAGE.md / relaxed_leakage flag). hints_text is empty, so no hints-only leak is possible.

Semantic check vs public problem_statement: the task already discloses (a) a NEW template filter `escapeseq` that is the escape-counterpart to `safeseq`, (b) usage `{{ some_list|escapeseq|join:"," }}`, and (c) that 'each item of some_list is escaped before applying the join', in an autoescape-off context. The spec view describes exactly this behavior at an abstract level: a per-element, order-preserving, length-preserving escape-when-needed transform over a sequence of textual items. That is the public task, not a reconstruction beyond it.

The extra detail in the spec view (five HTML entities, `&`-first ordering, apostrophe -> `&#x27;`, no-double-escape for already-safe items) is the standard definition of HTML escaping / conditional_escape semantics from the CPython stdlib and Django's existing html utils, not gold-edit-specific content. The gold patch itself does NOT spell out any of these entities; it merely calls the pre-existing `conditional_escape`. The model names are generic (escape_each / escape_when_unsafe_item / escape_codepoints), disclosing neither the patched file nor the added symbol. The spec view thus localizes no edit beyond what the problem_statement already makes public.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
