# P2 adversarial audit — django__django-11276

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk1.py`, `atk2.py`, `atk3.py`, `atk5.py`, `atk6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk4.py` |

**Non-vacuity.** The positive control `pc.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

```diff
@@ -138,15 +138,11 @@
     result = []  # type: List[int]
     i = len(text)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(text), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(text))
         Invariant(ToSeq(result) == escaped_seq(ToSeq(text).drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i.
         Invariant(MustTerminate(i))
-        # invariants-end
         c = text[i - 1]
         Assert(ToSeq(text).drop(i - 1)[0] == c)
         Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
@@ -156,10 +152,6 @@
             result = [38, 108, 116, 59] + result
         elif c == 62:
             result = [38, 103, 116, 59] + result
-        elif c == 34:
-            result = [38, 113, 117, 111, 116, 59] + result
-        elif c == 39:
-            result = [38, 35, 120, 50, 55, 59] + result
         else:
             result = [c] + result
         i = i - 1
```

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

```diff
@@ -137,16 +137,12 @@
     # impl-start
     result = []  # type: List[int]
     i = len(text)
-    while i > 0:
-        # invariants-start
+    while i > 1:
         Invariant(Acc(list_pred(text), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(text))
         Invariant(ToSeq(result) == escaped_seq(ToSeq(text).drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i.
         Invariant(MustTerminate(i))
-        # invariants-end
         c = text[i - 1]
         Assert(ToSeq(text).drop(i - 1)[0] == c)
         Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
```

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

```diff
@@ -138,24 +138,20 @@
     result = []  # type: List[int]
     i = len(text)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(text), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(text))
         Invariant(ToSeq(result) == escaped_seq(ToSeq(text).drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i.
         Invariant(MustTerminate(i))
-        # invariants-end
         c = text[i - 1]
         Assert(ToSeq(text).drop(i - 1)[0] == c)
         Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
         if c == 38:
             result = [38, 97, 109, 112, 59] + result
         elif c == 60:
+            result = [38, 103, 116, 59] + result
+        elif c == 62:
             result = [38, 108, 116, 59] + result
-        elif c == 62:
-            result = [38, 103, 116, 59] + result
         elif c == 34:
             result = [38, 113, 117, 111, 116, 59] + result
         elif c == 39:
```

Attack 4 — `atk4.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -138,28 +138,24 @@
     result = []  # type: List[int]
     i = len(text)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(text), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(text))
         Invariant(ToSeq(result) == escaped_seq(ToSeq(text).drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i.
         Invariant(MustTerminate(i))
-        # invariants-end
         c = text[i - 1]
         Assert(ToSeq(text).drop(i - 1)[0] == c)
         Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
-        if c == 38:
-            result = [38, 97, 109, 112, 59] + result
+        if c == 39:
+            result = [38, 35, 120, 50, 55, 59] + result
+        elif c == 34:
+            result = [38, 113, 117, 111, 116, 59] + result
+        elif c == 62:
+            result = [38, 103, 116, 59] + result
         elif c == 60:
             result = [38, 108, 116, 59] + result
-        elif c == 62:
-            result = [38, 103, 116, 59] + result
-        elif c == 34:
-            result = [38, 113, 117, 111, 116, 59] + result
-        elif c == 39:
-            result = [38, 35, 120, 50, 55, 59] + result
+        elif c == 38:
+            result = [38, 97, 109, 112, 59] + result
         else:
             result = [c] + result
         i = i - 1
```

Attack 5 — `atk5.py` → rejected (same spec, does not verify — good)

```diff
@@ -138,15 +138,11 @@
     result = []  # type: List[int]
     i = len(text)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(text), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(text))
         Invariant(ToSeq(result) == escaped_seq(ToSeq(text).drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i.
         Invariant(MustTerminate(i))
-        # invariants-end
         c = text[i - 1]
         Assert(ToSeq(text).drop(i - 1)[0] == c)
         Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
@@ -156,8 +152,6 @@
             result = [38, 108, 116, 59] + result
         elif c == 62:
             result = [38, 103, 116, 59] + result
-        elif c == 34:
-            result = [38, 113, 117, 111, 116, 59] + result
         elif c == 39:
             result = [38, 35, 120, 50, 55, 59] + result
         else:
```

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

```diff
@@ -138,15 +138,11 @@
     result = []  # type: List[int]
     i = len(text)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(text), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(text))
         Invariant(ToSeq(result) == escaped_seq(ToSeq(text).drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i.
         Invariant(MustTerminate(i))
-        # invariants-end
         c = text[i - 1]
         Assert(ToSeq(text).drop(i - 1)[0] == c)
         Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
@@ -163,5 +159,9 @@
         else:
             result = [c] + result
         i = i - 1
+    j = 0
+    while j >= 0:
+        Invariant(MustTerminate(1))
+        j = j + 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.py`

```python
"""Twin-artifact model for django__django-11276.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) HTML-escaping of arbitrary text for safe inclusion in HTML markup.
      Each of the five HTML-significant code points is replaced by a constant
      entity sequence; every other code point passes through unchanged. The
      ampersand is handled first so that the ampersands inside the emitted
      entity sequences are NOT themselves re-escaped. The apostrophe (U+0027)
      is encoded as the numeric character reference `&#x27;`.

  (2) The community entity decoder used when re-deriving a raw URL from
      already-escaped link text is the exact inverse of the escaper on those
      five entity sequences: a token equal to `&#x27;` decodes back to the
      apostrophe U+0027 (and the legacy `&#39;` form decodes likewise), so the
      escape/decode round trip is the identity on every significant code point.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The pure sequence theory `PSeq[int]` carries the specification.

One stdlib callee is axiomatized (`entity_decode`, the urlize decoder); the
escaper itself is modelled deeply as a verified per-code-point substitution
(`escaped_seq`), whose equality to the real `html.escape` is checked
out-of-band by axiom_check.py (G-AX), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def entity_decode(tok: PSeq[int]) -> PSeq[int]:
    """Stdlib HTML entity decoder (the unchanged community callee), on the
    entity tokens this bundle relies on. Inverse of the escaper on the five
    emitted entities; also decodes the legacy decimal apostrophe `&#39;`.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Implies(tok == seq_amp(), Result() == PSeq(38)))
    Ensures(Implies(tok == seq_lt(), Result() == PSeq(60)))
    Ensures(Implies(tok == seq_gt(), Result() == PSeq(62)))
    Ensures(Implies(tok == seq_quot(), Result() == PSeq(34)))
    Ensures(Implies(tok == seq_apos_hex(), Result() == PSeq(39)))
    Ensures(Implies(tok == seq_apos_dec(), Result() == PSeq(39)))
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
def seq_apos_dec() -> PSeq[int]:
    # '&#39;'  (legacy decimal apostrophe entity)
    return PSeq(38, 35, 51, 57, 59)


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
    """The escape of a whole sequence: concatenate the per-code-point entity
    sequences. Front-recursive so a single unfold is available to callers."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return entity(s[0]) + escaped_seq(s.drop(1))
# pure-end


def escape_codepoints(text: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    # The escaped text must actually be delivered: this termination obligation
    # forbids implementations that would satisfy the value postcondition only
    # vacuously by never returning (the per-code-point substitution over a
    # finite input is bounded work).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The escaped output is the per-code-point entity substitution.
    Ensures(ToSeq(Result()) == escaped_seq(ToSeq(text)))
    # Escape/decode round trip is the identity on every significant code point,
    # the apostrophe carrying the discriminating `&#x27;` <-> U+0027 mapping.
    Ensures(entity_decode(entity(38)) == PSeq(38))
    Ensures(entity_decode(entity(60)) == PSeq(60))
    Ensures(entity_decode(entity(62)) == PSeq(62))
    Ensures(entity_decode(entity(34)) == PSeq(34))
    Ensures(entity_decode(entity(39)) == PSeq(39))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(result) == escaped_seq(ToSeq(text).drop(i)))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i.
        Invariant(MustTerminate(i))
        # invariants-end
        c = text[i - 1]
        Assert(ToSeq(text).drop(i - 1)[0] == c)
        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
        if c == 38:
            result = [38, 97, 109, 112, 59] + result
        elif c == 60:
            result = [38, 108, 116, 59] + result
        elif c == 62:
            result = [38, 103, 116, 59] + result
        elif c == 34:
            result = [38, 113, 117, 111, 116, 59] + result
        elif c == 39:
            result = [38, 35, 120, 50, 55, 59] + result
        else:
            result = [c] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit for django__django-11276 (nagini). Frozen spec pins the escaper output exactly: Ensures(ToSeq(Result()) == escaped_seq(ToSeq(text))) via the DEEP model escaped_seq/entity (A-reference, validated == html.escape by G-AX, NOT consumed as axiom), plus Requires(MustTerminate(2)) blocking vacuous/divergent proofs, plus round-trip clauses tying entity_decode (A-consumed axiom on html.unescape) to the escaper. Ran from project root with SBU_BENCHMARK_DIR=benchmark-verified, env swebench-lean.

PROTOCOL: 6 distinct same-spec wrong impls + prepatch encoded (impl region only edited; axioms/@Pure/Requires/Ensures byte-identical -> `same-spec` exit 0 for ALL 8 incl pc). Weakness verifications run concurrently in batches of <=3 (each spawns JVM+Z3).

### ATTACKS (cmd: `python -m swebench_unified.adversary weakness nagini django__django-11276 <path>`):
- atk1 partial-domain (drops " and ' escaping): exit 2 NOT-A-COUNTEREXAMPLE (fails value postcond).
- atk2 boundary/off-by-one (while i>1 skips first codepoint): exit 2.
- atk3 swapped mappings (< emits &gt;, > emits &lt;): exit 2.
- atk4 ECHO (behaviorally-correct escaper, branch order permuted): exit 0 CANDIDATE (verifies, 14.6s). => materialized faithful patch (= gold patch, since atk4 computes identical escape fn) at atk4_faithful.patch and RAN it: `run_resolve('django__django-11276', patch)` -> RESOLVED=True, COMPLETED=True. Echo does NOT break the spec (verify=>correct held). Not a weakness per resolved-echo policy.
- atk5 drop-quote-escape (" passes through, quote=False behaviour): exit 2.
- atk6 control-flow-effect (correct value then non-decreasing spin loop): exit 2 (fails MustTerminate obligation-leak check -> confirms termination obligation is live, not vacuous).

PREPATCH: model_prepatch.py reproduced (' -> &#39; = [38,35,51,57,59]); direct nagini_verify -> error at line 145: 'Loop invariant ToSeq(result)==escaped_seq(ToSeq(text).drop(i)) might not hold' -- the value postcondition senses the &#39; vs &#x27; change (G-DIFF). prepatch_reproduced=true.

POSITIVE CONTROL: pc.py (bundle model.py verbatim) verifies (nagini_verify.sh exit 0).

G-AX: axiom_check.py exit 0 -- deep model escaped_seq == real html.escape and entity_decode axiom == real html.unescape on 23 boundary + 20000 fuzz + 6 decode tokens. A-reference and A-consumed callee correspondence both hold.

REFINEMENT.MD AUDIT: all legs are R (A1 str<->List[int], A2 str() identity, A4 mark_safe identity) / A-reference (A3 escaped_seq deep model == html.escape, validated by G-AX not consumed) / A-consumed (B1 entity_decode axiom on html.unescape, B2 round-trip) / I. Section C explicitly certifies NO kind-3: the one changed op (escaper substitution) is modeled deeply as escaped_seq (A-reference), not hidden behind an axiom-about-the-changed-fn; the only consumed axiom covers the UNCHANGED stdlib html.unescape callee. Correspondence to real callees verified via G-AX above.

VERDICT: SOUND. >=5 attacks run (6 wrong impls + prepatch); the ONLY verifying candidate (atk4 echo) has a faithful patch that RESOLVES (executed harness run, not speculation). No verifying same-spec impl produces a non-resolving faithful patch => verify=>correct is not falsified. Spec is tight (full-output postcond + MustTerminate + round-trip).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk1.py`, `atk2.py`, `atk3.py`, `atk5.py`, `atk6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk4.py` |

**Non-vacuity.** The positive control `pc.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.py`

```python
"""Twin-artifact model for django__django-11276.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) HTML-escaping of arbitrary text for safe inclusion in HTML markup.
      Each of the five HTML-significant code points is replaced by a constant
      entity sequence; every other code point passes through unchanged. The
      ampersand is handled first so that the ampersands inside the emitted
      entity sequences are NOT themselves re-escaped. The apostrophe (U+0027)
      is encoded as the numeric character reference `&#x27;`.

  (2) The community entity decoder used when re-deriving a raw URL from
      already-escaped link text is the exact inverse of the escaper on those
      five entity sequences: a token equal to `&#x27;` decodes back to the
      apostrophe U+0027 (and the legacy `&#39;` form decodes likewise), so the
      escape/decode round trip is the identity on every significant code point.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The pure sequence theory `PSeq[int]` carries the specification.

One stdlib callee is axiomatized (`entity_decode`, the urlize decoder); the
escaper itself is modelled deeply as a verified per-code-point substitution
(`escaped_seq`), whose equality to the real `html.escape` is checked
out-of-band by axiom_check.py (G-AX), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def entity_decode(tok: PSeq[int]) -> PSeq[int]:
    """Stdlib HTML entity decoder (the unchanged community callee), on the
    entity tokens this bundle relies on. Inverse of the escaper on the five
    emitted entities; also decodes the legacy decimal apostrophe `&#39;`.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Implies(tok == seq_amp(), Result() == PSeq(38)))
    Ensures(Implies(tok == seq_lt(), Result() == PSeq(60)))
    Ensures(Implies(tok == seq_gt(), Result() == PSeq(62)))
    Ensures(Implies(tok == seq_quot(), Result() == PSeq(34)))
    Ensures(Implies(tok == seq_apos_hex(), Result() == PSeq(39)))
    Ensures(Implies(tok == seq_apos_dec(), Result() == PSeq(39)))
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
def seq_apos_dec() -> PSeq[int]:
    # '&#39;'  (legacy decimal apostrophe entity)
    return PSeq(38, 35, 51, 57, 59)


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
    """The escape of a whole sequence: concatenate the per-code-point entity
    sequences. Front-recursive so a single unfold is available to callers."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return entity(s[0]) + escaped_seq(s.drop(1))
# pure-end


def escape_codepoints(text: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    # The escaped text must actually be delivered: this termination obligation
    # forbids implementations that would satisfy the value postcondition only
    # vacuously by never returning (the per-code-point substitution over a
    # finite input is bounded work).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The escaped output is the per-code-point entity substitution.
    Ensures(ToSeq(Result()) == escaped_seq(ToSeq(text)))
    # Escape/decode round trip is the identity on every significant code point,
    # the apostrophe carrying the discriminating `&#x27;` <-> U+0027 mapping.
    Ensures(entity_decode(entity(38)) == PSeq(38))
    Ensures(entity_decode(entity(60)) == PSeq(60))
    Ensures(entity_decode(entity(62)) == PSeq(62))
    Ensures(entity_decode(entity(34)) == PSeq(34))
    Ensures(entity_decode(entity(39)) == PSeq(39))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(result) == escaped_seq(ToSeq(text).drop(i)))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i.
        Invariant(MustTerminate(i))
        # invariants-end
        c = text[i - 1]
        Assert(ToSeq(text).drop(i - 1)[0] == c)
        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
        if c == 38:
            result = [38, 97, 109, 112, 59] + result
        elif c == 60:
            result = [38, 108, 116, 59] + result
        elif c == 62:
            result = [38, 103, 116, 59] + result
        elif c == 34:
            result = [38, 113, 117, 111, 116, 59] + result
        elif c == 39:
            result = [38, 35, 120, 50, 55, 59] + result
        else:
            result = [c] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit for django__django-11276 (nagini). Frozen spec pins the escaper output exactly: Ensures(ToSeq(Result()) == escaped_seq(ToSeq(text))) via the DEEP model escaped_seq/entity (A-reference, validated == html.escape by G-AX, NOT consumed as axiom), plus Requires(MustTerminate(2)) blocking vacuous/divergent proofs, plus round-trip clauses tying entity_decode (A-consumed axiom on html.unescape) to the escaper. Ran from project root with SBU_BENCHMARK_DIR=benchmark-verified, env swebench-lean.

PROTOCOL: 6 distinct same-spec wrong impls + prepatch encoded (impl region only edited; axioms/@Pure/Requires/Ensures byte-identical -> `same-spec` exit 0 for ALL 8 incl pc). Weakness verifications run concurrently in batches of <=3 (each spawns JVM+Z3).

### ATTACKS (cmd: `python -m swebench_unified.adversary weakness nagini django__django-11276 <path>`):
- atk1 partial-domain (drops " and ' escaping): exit 2 NOT-A-COUNTEREXAMPLE (fails value postcond).
- atk2 boundary/off-by-one (while i>1 skips first codepoint): exit 2.
- atk3 swapped mappings (< emits &gt;, > emits &lt;): exit 2.
- atk4 ECHO (behaviorally-correct escaper, branch order permuted): exit 0 CANDIDATE (verifies, 14.6s). => materialized faithful patch (= gold patch, since atk4 computes identical escape fn) at atk4_faithful.patch and RAN it: `run_resolve('django__django-11276', patch)` -> RESOLVED=True, COMPLETED=True. Echo does NOT break the spec (verify=>correct held). Not a weakness per resolved-echo policy.
- atk5 drop-quote-escape (" passes through, quote=False behaviour): exit 2.
- atk6 control-flow-effect (correct value then non-decreasing spin loop): exit 2 (fails MustTerminate obligation-leak check -> confirms termination obligation is live, not vacuous).

PREPATCH: model_prepatch.py reproduced (' -> &#39; = [38,35,51,57,59]); direct nagini_verify -> error at line 145: 'Loop invariant ToSeq(result)==escaped_seq(ToSeq(text).drop(i)) might not hold' -- the value postcondition senses the &#39; vs &#x27; change (G-DIFF). prepatch_reproduced=true.

POSITIVE CONTROL: pc.py (bundle model.py verbatim) verifies (nagini_verify.sh exit 0).

G-AX: axiom_check.py exit 0 -- deep model escaped_seq == real html.escape and entity_decode axiom == real html.unescape on 23 boundary + 20000 fuzz + 6 decode tokens. A-reference and A-consumed callee correspondence both hold.

REFINEMENT.MD AUDIT: all legs are R (A1 str<->List[int], A2 str() identity, A4 mark_safe identity) / A-reference (A3 escaped_seq deep model == html.escape, validated by G-AX not consumed) / A-consumed (B1 entity_decode axiom on html.unescape, B2 round-trip) / I. Section C explicitly certifies NO kind-3: the one changed op (escaper substitution) is modeled deeply as escaped_seq (A-reference), not hidden behind an axiom-about-the-changed-fn; the only consumed axiom covers the UNCHANGED stdlib html.unescape callee. Correspondence to real callees verified via G-AX above.

VERDICT: SOUND. >=5 attacks run (6 wrong impls + prepatch); the ONLY verifying candidate (atk4 echo) has a faithful patch that RESOLVES (executed harness run, not speculation). No verifying same-spec impl produces a non-resolving faithful patch => verify=>correct is not falsified. Spec is tight (full-output postcond + MustTerminate + round-trip).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (same-spec verified via nagini_verify pass on frozen bundle model.py). Faithfulness of the two modeled callees confirmed by independent differential execution against the real stdlib: (1) deep model escaped_seq/entity vs REAL html.escape(quote=True) — exhaustive over every Unicode code point 0..0x10FFFF (excluding surrogates) plus 200,000 multi-char fuzz strings across the full range => 0 divergences; the per-code-point substitution (&->&amp;, <->&lt;, >->&gt;, "->&quot;, '->&#x27;, else identity), ampersand-first, exactly equals html.escape. (2) entity_decode axiom is @Pure @ContractOnly with implications for only the six emitted/legacy tokens (&amp;,&lt;,&gt;,&quot;,&#x27;,&#39;), i.e. a WEAKEST contract that cannot be too strong; all six match REAL html.unescape. No modeled function disagrees with the real repo callee on any input. model.py verifies in 13s. G-AX independently passes. NOTE: the recorded G-EQ=fail is a spec-TOO-WEAK verify-not-correct verdict (role 1 concern), not a faithfulness/drift/too-strong defect — orthogonal to this gate.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-LEAK lexical screen passes clean (leakage.screen: hard_failures=[], passed=True). Verified semantically against problem_statement ONLY (not hints_text).

Gold patch touches django/utils/html.py at two sites: (A) escape() body `mark_safe(str(text).translate(_html_escapes))` -> `mark_safe(html.escape(str(text)))`, dropping the local _html_escapes dict (' -> &#39;); (B) urlize's local `unescape` helper replaced by `html.unescape`. Changed def/class symbols: {escape, unescape, trim_url, trim_punctuation, is_email_simple}.

Spec-view leakage checks all clear:
- No gold-diff line reproduced: 'unescape', 'html.py', 'translate', '_html_escapes', 'mark_safe' are all ABSENT from the spec view.
- No patched file path / module path present.
- No patched repo symbol echoed in a localizing spec-view identifier: model uses abstracted names (escape_codepoints, entity_decode, escaped_seq, entity, seq_*). None embeds 'unescape'/'escape'(as def)/'trim_*'.
- No bug/fix/patch narration in comments/docstrings.

The single discriminating behavioural fact — apostrophe U+0027 -> `&#x27;` rather than `&#39;` — is EXPLICITLY PUBLIC in the problem_statement ('html.escape() converts ' to &#x27 rather than &#39'). Stating it in the spec is not a leak.

The site-B round-trip clause (spec view line 12/21: 'community entity decoder used when re-deriving a raw URL' / 'the urlize decoder') is NOT in the problem_statement, but it is expressed as an abstract BEHAVIOURAL invariant over an axiomatized callee (entity_decode), not as the edit: it quotes no diff line, names no file, and 'urlize' is a general Django feature name, not a patched def/class symbol the leak policy screens. It describes the required inverse property, not 'replace urlize's local unescape with stdlib html.unescape'. This does not reconstruct the gold edit beyond the public problem statement.

Conclusion: the spec view reveals a faithful behavioural specification whose only gold-discriminating content is already public; nothing localizes or reproduces the edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
