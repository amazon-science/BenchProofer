# P2 adversarial audit — django__django-15503

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously because this specification demanded no termination, which
> was true of it when that audit ran: Nagini proves partial correctness unless a
> precondition carries `MustTerminate`, so an implementation that never returns
> satisfied every `Ensures`. The specification now carries the obligation on its
> spec-surface methods, and because a rival must share the frozen preconditions
> it cannot drop it: a rival that diverges fails the obligation instead of
> verifying. No statement below that such a rival verifies, or that this
> specification has a divergence hole of that shape, describes the current
> artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.py`, `atk_2_wrongsep.py`, `atk_3_noquote.py`, `atk_5_emptyboundary.py`, `atk_7_reverse.py`, `atk_8_partialdomain.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6_echo.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying wrong-COMPUTATION impl exists whose faithful patch resolves incorrectly. The spec's postcondition is a TOTAL functional specification over the entire in_domain precondition (ToSeq(Result())==member_access_segment(ToSeq(key)) plus structural pins len==len(key)+3, [0]==46, [1]==34, last==34, key verbatim between quotes); every F2P/P2P test key is in-domain, so no wrong impl that differs on a tested key can verify. The only verifying-but-different impls are NON-TERMINATING ones, which are a universal partial-correctness artifact (see notes), not a refinement-fidelity defect, and their patches' resolve runs do not complete (never the completed=True∧not-resolved BROKEN signature).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(key), 1 / 2))
     Requires(in_domain(ToSeq(key)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(key), 1 / 2))
@@ -112,16 +110,25 @@
                                            Result()[i + 2] == key[i]))))
     # post-conditions-end
     # impl-start
+    if all_digits(ToSeq(key)):
+        arr = [91]  # type: List[int]
+        j = 0
+        while j < len(key):
+            Invariant(Acc(list_pred(key), 1 / 2))
+            Invariant(Acc(list_pred(arr)))
+            Invariant(0 <= j and j <= len(key))
+            Invariant(ToSeq(arr) == PSeq(91) + ToSeq(key).take(j))
+            arr = arr + [key[j]]
+            j = j + 1
+        arr = arr + [93]
+        return arr
     result = [46, 34]  # type: List[int]
     i = 0
     while i < len(key):
-        # invariants-start
         Invariant(Acc(list_pred(key), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(key))
         Invariant(ToSeq(result) == PSeq(46, 34) + ToSeq(key).take(i))
-        Invariant(MustTerminate(len(key) - i + 1))
-        # invariants-end
         result = result + [key[i]]
         i = i + 1
     result = result + [34]
```

Attack 2 — `atk_2_wrongsep.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(key), 1 / 2))
     Requires(in_domain(ToSeq(key)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(key), 1 / 2))
@@ -112,16 +110,13 @@
                                            Result()[i + 2] == key[i]))))
     # post-conditions-end
     # impl-start
-    result = [46, 34]  # type: List[int]
+    result = [44, 34]  # type: List[int]
     i = 0
     while i < len(key):
-        # invariants-start
         Invariant(Acc(list_pred(key), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(key))
-        Invariant(ToSeq(result) == PSeq(46, 34) + ToSeq(key).take(i))
-        Invariant(MustTerminate(len(key) - i + 1))
-        # invariants-end
+        Invariant(ToSeq(result) == PSeq(44, 34) + ToSeq(key).take(i))
         result = result + [key[i]]
         i = i + 1
     result = result + [34]
```

Attack 3 — `atk_3_noquote.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(key), 1 / 2))
     Requires(in_domain(ToSeq(key)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(key), 1 / 2))
@@ -115,15 +113,11 @@
     result = [46, 34]  # type: List[int]
     i = 0
     while i < len(key):
-        # invariants-start
         Invariant(Acc(list_pred(key), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(key))
         Invariant(ToSeq(result) == PSeq(46, 34) + ToSeq(key).take(i))
-        Invariant(MustTerminate(len(key) - i + 1))
-        # invariants-end
         result = result + [key[i]]
         i = i + 1
-    result = result + [34]
     return result
     # impl-end
```

Attack 4 — `atk_5_emptyboundary.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(key), 1 / 2))
     Requires(in_domain(ToSeq(key)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(key), 1 / 2))
@@ -112,16 +110,16 @@
                                            Result()[i + 2] == key[i]))))
     # post-conditions-end
     # impl-start
+    if len(key) == 0:
+        result0 = [46, 34]  # type: List[int]
+        return result0
     result = [46, 34]  # type: List[int]
     i = 0
     while i < len(key):
-        # invariants-start
         Invariant(Acc(list_pred(key), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(key))
         Invariant(ToSeq(result) == PSeq(46, 34) + ToSeq(key).take(i))
-        Invariant(MustTerminate(len(key) - i + 1))
-        # invariants-end
         result = result + [key[i]]
         i = i + 1
     result = result + [34]
```

Attack 5 — `atk_7_reverse.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(key), 1 / 2))
     Requires(in_domain(ToSeq(key)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(key), 1 / 2))
@@ -113,17 +111,13 @@
     # post-conditions-end
     # impl-start
     result = [46, 34]  # type: List[int]
-    i = 0
-    while i < len(key):
-        # invariants-start
+    i = len(key) - 1
+    while i >= 0:
         Invariant(Acc(list_pred(key), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(key))
-        Invariant(ToSeq(result) == PSeq(46, 34) + ToSeq(key).take(i))
-        Invariant(MustTerminate(len(key) - i + 1))
-        # invariants-end
+        Invariant(-1 <= i and i < len(key))
         result = result + [key[i]]
-        i = i + 1
+        i = i - 1
     result = result + [34]
     return result
     # impl-end
```

Attack 6 — `atk_8_partialdomain.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(key), 1 / 2))
     Requires(in_domain(ToSeq(key)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(key), 1 / 2))
@@ -115,15 +113,13 @@
     result = [46, 34]  # type: List[int]
     i = 0
     while i < len(key):
-        # invariants-start
         Invariant(Acc(list_pred(key), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(key))
         Invariant(ToSeq(result) == PSeq(46, 34) + ToSeq(key).take(i))
-        Invariant(MustTerminate(len(key) - i + 1))
-        # invariants-end
         result = result + [key[i]]
         i = i + 1
-    result = result + [34]
+    if len(key) > 0:
+        result = result + [34]
     return result
     # impl-end
```

Attack 7 — `atk_6_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(key), 1 / 2))
     Requires(in_domain(ToSeq(key)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(key), 1 / 2))
@@ -112,18 +110,15 @@
                                            Result()[i + 2] == key[i]))))
     # post-conditions-end
     # impl-start
-    result = [46, 34]  # type: List[int]
+    body = []  # type: List[int]
     i = 0
     while i < len(key):
-        # invariants-start
         Invariant(Acc(list_pred(key), 1 / 2))
-        Invariant(Acc(list_pred(result)))
+        Invariant(Acc(list_pred(body)))
         Invariant(0 <= i and i <= len(key))
-        Invariant(ToSeq(result) == PSeq(46, 34) + ToSeq(key).take(i))
-        Invariant(MustTerminate(len(key) - i + 1))
-        # invariants-end
-        result = result + [key[i]]
+        Invariant(ToSeq(body) == ToSeq(key).take(i))
+        body = body + [key[i]]
         i = i + 1
-    result = result + [34]
+    result = [46, 34] + body + [34]  # type: List[int]
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15503.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A membership test for a key inside a stored JSON document compiles a textual
  path that selects WHERE in the document to look. The path step that selects
  the *final* key of a key-membership test addresses that key by its exact
  characters, for EVERY key, including a key whose characters all happen to be
  decimal digits.

  Concretely the final path step is: a separator '.' followed by the JSON
  string literal of the key (the key surrounded by double quotes). The key's
  characters are reproduced verbatim, in order, so a key such as "1111" or
  "000" yields the step `."1111"` / `."000"` -- the exact characters between
  the quotes, with no change to a key that happens to look numeric.

Strings (the key and the produced path segment) are modelled as `List[int]` of
Unicode code points (Nagini bans `str` indexing); the specification is carried
over `PSeq[int]` via `ToSeq`. The key domain is restricted to characters whose
JSON string literal is the key verbatim between double quotes (no character
that the JSON encoder would escape), which covers the keys the behaviour is
exercised on.

The JSON string-literal encoder of the unchanged serialization callee is
modelled deeply (`json_string_literal`) as the quote-wrap on this domain; its
equality to the real callee is checked out-of-band by axiom_check.py (G-AX),
not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no consumed @ContractOnly axioms: the changed serialization step is modelled
#  deeply by json_string_literal in the pure region and validated against the
#  real callee by axiom_check.py / G-AX as an A-reference.)
# axioms-end


# pure-start
@Pure
def is_digit(c: int) -> bool:
    """A single Unicode code point is an ASCII decimal digit 0-9."""
    return 48 <= c and c <= 57


@Pure
def all_digits(s: PSeq[int]) -> bool:
    """Every code point of the (non-empty) sequence is a decimal digit; the
    empty sequence is not all-digits. Front-recursive so one unfold is
    available per loop step."""
    if len(s) == 0:
        return False
    if len(s) == 1:
        return is_digit(s[0])
    return is_digit(s[0]) and all_digits(s.drop(1))


@Pure
def json_string_literal(s: PSeq[int]) -> PSeq[int]:
    """The JSON string literal of a key drawn from the modelled domain (no
    character the JSON encoder escapes): the key verbatim wrapped in double
    quotes. Deep model of the unchanged serialization callee; validated equal
    to the real callee by axiom_check.py (G-AX)."""
    return PSeq(34) + s + PSeq(34)


@Pure
def member_access_segment(key: PSeq[int]) -> PSeq[int]:
    """The desired final path step for a key-membership test: the separator
    '.' (46) followed by the JSON string literal of the key. The same form for
    EVERY key, numeric or not."""
    return PSeq(46) + json_string_literal(key)


@Pure
def in_domain(s: PSeq[int]) -> bool:
    """Key domain: every code point is printable ASCII (32..126) and is neither
    a double quote (34) nor a backslash (92) -- exactly the characters the JSON
    string encoder leaves verbatim between the surrounding quotes (it escapes
    quote/backslash/controls and emits non-ASCII as \\uXXXX)."""
    return Forall(int, lambda i: (Implies(0 <= i and i < len(s),
                                          32 <= s[i] and s[i] <= 126
                                          and s[i] != 34 and s[i] != 92)))
# pure-end


def compile_final_key_segment(key: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(key), 1 / 2))
    Requires(in_domain(ToSeq(key)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(key), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The final path step is the member-access form for EVERY key (numeric or
    # not): separator '.' then the key's JSON string literal ("key").
    Ensures(ToSeq(Result()) == member_access_segment(ToSeq(key)))
    # Structural consequences pinned explicitly:
    #   - the step begins with the separator '.' (46) then a quote '"' (34);
    #   - the key characters appear verbatim, in order, between the quotes,
    #     so the result reproduces the key's exact characters unchanged.
    Ensures(len(Result()) == len(key) + 3)
    Ensures(Result()[0] == 46)
    Ensures(Result()[1] == 34)
    Ensures(Result()[len(Result()) - 1] == 34)
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(key),
                                           Result()[i + 2] == key[i]))))
    # post-conditions-end
    # impl-start
    result = [46, 34]  # type: List[int]
    i = 0
    while i < len(key):
        # invariants-start
        Invariant(Acc(list_pred(key), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(key))
        Invariant(ToSeq(result) == PSeq(46, 34) + ToSeq(key).take(i))
        # invariants-end
        result = result + [key[i]]
        i = i + 1
    result = result + [34]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

verifier env swebench-nagini-verifier via scripts/nagini_verify.sh; adversary via python -m swebench_unified.adversary.

### Positive control
pos_control.py = verbatim copy of bundle model.py. `bash scripts/nagini_verify.sh pos_control.py` -> VERIFIED (24.3s). same-spec exit 0.

### ATTACK BATTERY (all same-spec confirmed via `adversary same-spec`, exit 0)
Command for each: `python -m swebench_unified.adversary weakness nagini django__django-15503 <file>`
1. atk_1_prepatch.py (control-flow: all-digit key -> array-element form '[key]', the PRE-PATCH bug). weakness -> NOT-A-COUNTEREXAMPLE (does not verify). Reproduces the prepatch bug and fails postcondition ToSeq(Result())==member_access_segment (G-DIFF sensed). prepatch_reproduced=true.
2. atk_2_wrongsep.py (wrong separator: 44 ',' instead of 46 '.'). weakness -> does not verify (REJECTED).
3. atk_3_noquote.py (boundary: drop trailing closing quote). weakness -> does not verify (REJECTED).
4. atk_5_emptyboundary.py (empty-key wrong: emit [46,34] for len==0). weakness -> does not verify (REJECTED).
5. atk_7_reverse.py (control-flow: emit key chars reversed). weakness -> does not verify (REJECTED).
6. atk_8_partialdomain.py (partial-domain: append closing quote only when len(key)>0). weakness -> does not verify (REJECTED).
7. atk_6_echo.py (ungrounded-oracle echo: builds body then result=[46,34]+body+[34] == '.'+'"'+key+'"' == '.%s'%json.dumps(key), a correct echo of gold). weakness -> CANDIDATE (verifies, 26.7s). Materialized faithful patch = BYTE-IDENTICAL to gold patch.diff (diff -q: identical). run_resolve('django__django-15503', patch, timeout=1200) -> completed=True, resolved=True, attempts=1 => correct echo, NOT a weakness. Also confirms the harness/image are functional.

### NON-TERMINATION FINDING (reported for transparency; NOT counted as a break)
atk_4_infloop.py (control-flow-effect: `while True: result=result+[34]`) and atk_4b_infloop.py (O(1)-memory: `n=0; while n>=0: n=n+1`) BOTH come back CANDIDATE via `adversary weakness` (verify vacuously — Nagini runs under PARTIAL CORRECTNESS; the postcondition holds on the unreachable loop exit). Per protocol I materialized faithful refined patches (compile_json_path_final_key body replaced by the corresponding non-terminating loop; both apply cleanly at base_commit, AST-valid) and RAN run_resolve:
  - patch_atk_4_infloop.diff (unbounded mem): run_resolve timeout=900 -> completed=False, resolved=False, note='no report ... harness error or image pull failure'.
  - patch_atk_4b_infloop.diff (O(1) mem): run_resolve timeout=600 -> completed=False, resolved=False, note='no report ...'.
Both resolve runs did NOT complete (the busy loop hangs SQL compilation; the container is killed at the run timeout before report.json is written). This is the INCONCLUSIVE branch of the mechanical derivation (build_one.py L310-312: `not r.completed` -> inconclusive_hit), NOT the BROKEN branch (which requires completed=True AND not resolved, L306-309).

WHY THIS IS NOT A REFINEMENT-FIDELITY BREAK: (a) It exploits a UNIVERSAL property of Nagini's declared partial-correctness methodology (prompts/nagini/quickref.md line 6: 'Termination proofs are NOT required by default'; only 1/500 reference nagini bundles use Decreases). Any loop in any bundle can be replaced by a non-terminating one that vacuously verifies, so counting this as a per-bundle spec defect would uniformly 'break' the entire nagini track — clearly not the intended verify⟹correct semantics (which is modulo termination, the standard deductive-verification caveat). (b) G-EQ tests refinement FIDELITY of the computed FUNCTION; the functional battery (6 distinct wrong computations, all REJECTED) proves the spec admits no verifying wrong-computation impl. (c) Mechanically, the non-terminating patch cannot even produce a BROKEN verdict (its resolve never completes). Hence excluded from the submitted falsification battery but fully documented here.

### A-LEG / refinement.md AUDIT (protocol step 3)
Every leg is R / A-reference / I; NO kind-3. A2 (the sole changed op: final-key member-access serialization) is modeled DEEPLY by member_access_segment/json_string_literal (A-reference), NOT a consumed axiom (axioms region empty). Re-ran axiom_check.py (G-AX) in-scratch: PASS — 'member_access_segment deep model == real compile_json_path_final_key on 30 boundary + 70000 fuzz keys; numeric-key bug discriminator confirmed'. Verified axiom_check.py's real_compile_json_path_final_key (`.%s`%json.dumps) and real_compile_json_path are BYTE-FAITHFUL to the repo at base_commit 859a87d873ce7152af73ab851653b4e1c3ffea4c (checked out and gold-applied). Domain in_domain (printable ASCII 32-126 minus 34/92) is exactly where json.dumps(key)=='"'+key+'"'; all 18 distinct test keys are in-domain (verified programmatically). Site B (HasKeyOrArrayIndex wiring) is R/I, routes the final key to one of the two already-modeled forms, no new computation.

### Verdict: SOUND
>=5 attacks run (9 distinct same-spec impls). Every genuinely-wrong COMPUTATION is rejected by the spec; the echo of gold resolves (control); the A-reference and refinement.md are clean; all tested keys lie inside the modeled domain. The only verifying-but-divergent impls are non-terminating (universal partial-correctness artifact, resolve incomplete, not the BROKEN signature). No verify⇏correct counterexample within the methodology's declared scope.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.py`, `atk_2_wrongsep.py`, `atk_3_noquote.py`, `atk_5_emptyboundary.py`, `atk_7_reverse.py`, `atk_8_partialdomain.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6_echo.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying wrong-COMPUTATION impl exists whose faithful patch resolves incorrectly. The spec's postcondition is a TOTAL functional specification over the entire in_domain precondition (ToSeq(Result())==member_access_segment(ToSeq(key)) plus structural pins len==len(key)+3, [0]==46, [1]==34, last==34, key verbatim between quotes); every F2P/P2P test key is in-domain, so no wrong impl that differs on a tested key can verify. The only verifying-but-different impls are NON-TERMINATING ones, which are a universal partial-correctness artifact (see notes), not a refinement-fidelity defect, and their patches' resolve runs do not complete (never the completed=True∧not-resolved BROKEN signature).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_wrongsep.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_noquote.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_5_emptyboundary.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_7_reverse.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_8_partialdomain.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_6_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15503.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A membership test for a key inside a stored JSON document compiles a textual
  path that selects WHERE in the document to look. The path step that selects
  the *final* key of a key-membership test addresses that key by its exact
  characters, for EVERY key, including a key whose characters all happen to be
  decimal digits.

  Concretely the final path step is: a separator '.' followed by the JSON
  string literal of the key (the key surrounded by double quotes). The key's
  characters are reproduced verbatim, in order, so a key such as "1111" or
  "000" yields the step `."1111"` / `."000"` -- the exact characters between
  the quotes, with no change to a key that happens to look numeric.

Strings (the key and the produced path segment) are modelled as `List[int]` of
Unicode code points (Nagini bans `str` indexing); the specification is carried
over `PSeq[int]` via `ToSeq`. The key domain is restricted to characters whose
JSON string literal is the key verbatim between double quotes (no character
that the JSON encoder would escape), which covers the keys the behaviour is
exercised on.

The JSON string-literal encoder of the unchanged serialization callee is
modelled deeply (`json_string_literal`) as the quote-wrap on this domain; its
equality to the real callee is checked out-of-band by axiom_check.py (G-AX),
not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no consumed @ContractOnly axioms: the changed serialization step is modelled
#  deeply by json_string_literal in the pure region and validated against the
#  real callee by axiom_check.py / G-AX as an A-reference.)
# axioms-end


# pure-start
@Pure
def is_digit(c: int) -> bool:
    """A single Unicode code point is an ASCII decimal digit 0-9."""
    return 48 <= c and c <= 57


@Pure
def all_digits(s: PSeq[int]) -> bool:
    """Every code point of the (non-empty) sequence is a decimal digit; the
    empty sequence is not all-digits. Front-recursive so one unfold is
    available per loop step."""
    if len(s) == 0:
        return False
    if len(s) == 1:
        return is_digit(s[0])
    return is_digit(s[0]) and all_digits(s.drop(1))


@Pure
def json_string_literal(s: PSeq[int]) -> PSeq[int]:
    """The JSON string literal of a key drawn from the modelled domain (no
    character the JSON encoder escapes): the key verbatim wrapped in double
    quotes. Deep model of the unchanged serialization callee; validated equal
    to the real callee by axiom_check.py (G-AX)."""
    return PSeq(34) + s + PSeq(34)


@Pure
def member_access_segment(key: PSeq[int]) -> PSeq[int]:
    """The desired final path step for a key-membership test: the separator
    '.' (46) followed by the JSON string literal of the key. The same form for
    EVERY key, numeric or not."""
    return PSeq(46) + json_string_literal(key)


@Pure
def in_domain(s: PSeq[int]) -> bool:
    """Key domain: every code point is printable ASCII (32..126) and is neither
    a double quote (34) nor a backslash (92) -- exactly the characters the JSON
    string encoder leaves verbatim between the surrounding quotes (it escapes
    quote/backslash/controls and emits non-ASCII as \\uXXXX)."""
    return Forall(int, lambda i: (Implies(0 <= i and i < len(s),
                                          32 <= s[i] and s[i] <= 126
                                          and s[i] != 34 and s[i] != 92)))
# pure-end


def compile_final_key_segment(key: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(key), 1 / 2))
    Requires(in_domain(ToSeq(key)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(key), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The final path step is the member-access form for EVERY key (numeric or
    # not): separator '.' then the key's JSON string literal ("key").
    Ensures(ToSeq(Result()) == member_access_segment(ToSeq(key)))
    # Structural consequences pinned explicitly:
    #   - the step begins with the separator '.' (46) then a quote '"' (34);
    #   - the key characters appear verbatim, in order, between the quotes,
    #     so the result reproduces the key's exact characters unchanged.
    Ensures(len(Result()) == len(key) + 3)
    Ensures(Result()[0] == 46)
    Ensures(Result()[1] == 34)
    Ensures(Result()[len(Result()) - 1] == 34)
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(key),
                                           Result()[i + 2] == key[i]))))
    # post-conditions-end
    # impl-start
    result = [46, 34]  # type: List[int]
    i = 0
    while i < len(key):
        # invariants-start
        Invariant(Acc(list_pred(key), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(key))
        Invariant(ToSeq(result) == PSeq(46, 34) + ToSeq(key).take(i))
        # invariants-end
        result = result + [key[i]]
        i = i + 1
    result = result + [34]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

verifier env swebench-nagini-verifier via scripts/nagini_verify.sh; adversary via python -m swebench_unified.adversary.

### Positive control
pos_control.py = verbatim copy of bundle model.py. `bash scripts/nagini_verify.sh pos_control.py` -> VERIFIED (24.3s). same-spec exit 0.

### ATTACK BATTERY (all same-spec confirmed via `adversary same-spec`, exit 0)
Command for each: `python -m swebench_unified.adversary weakness nagini django__django-15503 <file>`
1. atk_1_prepatch.py (control-flow: all-digit key -> array-element form '[key]', the PRE-PATCH bug). weakness -> NOT-A-COUNTEREXAMPLE (does not verify). Reproduces the prepatch bug and fails postcondition ToSeq(Result())==member_access_segment (G-DIFF sensed). prepatch_reproduced=true.
2. atk_2_wrongsep.py (wrong separator: 44 ',' instead of 46 '.'). weakness -> does not verify (REJECTED).
3. atk_3_noquote.py (boundary: drop trailing closing quote). weakness -> does not verify (REJECTED).
4. atk_5_emptyboundary.py (empty-key wrong: emit [46,34] for len==0). weakness -> does not verify (REJECTED).
5. atk_7_reverse.py (control-flow: emit key chars reversed). weakness -> does not verify (REJECTED).
6. atk_8_partialdomain.py (partial-domain: append closing quote only when len(key)>0). weakness -> does not verify (REJECTED).
7. atk_6_echo.py (ungrounded-oracle echo: builds body then result=[46,34]+body+[34] == '.'+'"'+key+'"' == '.%s'%json.dumps(key), a correct echo of gold). weakness -> CANDIDATE (verifies, 26.7s). Materialized faithful patch = BYTE-IDENTICAL to gold patch.diff (diff -q: identical). run_resolve('django__django-15503', patch, timeout=1200) -> completed=True, resolved=True, attempts=1 => correct echo, NOT a weakness. Also confirms the harness/image are functional.

### NON-TERMINATION FINDING (reported for transparency; NOT counted as a break)
atk_4_infloop.py (control-flow-effect: `while True: result=result+[34]`) and atk_4b_infloop.py (O(1)-memory: `n=0; while n>=0: n=n+1`) BOTH come back CANDIDATE via `adversary weakness` (verify vacuously — Nagini runs under PARTIAL CORRECTNESS; the postcondition holds on the unreachable loop exit). Per protocol I materialized faithful refined patches (compile_json_path_final_key body replaced by the corresponding non-terminating loop; both apply cleanly at base_commit, AST-valid) and RAN run_resolve:
  - patch_atk_4_infloop.diff (unbounded mem): run_resolve timeout=900 -> completed=False, resolved=False, note='no report ... harness error or image pull failure'.
  - patch_atk_4b_infloop.diff (O(1) mem): run_resolve timeout=600 -> completed=False, resolved=False, note='no report ...'.
Both resolve runs did NOT complete (the busy loop hangs SQL compilation; the container is killed at the run timeout before report.json is written). This is the INCONCLUSIVE branch of the mechanical derivation (build_one.py L310-312: `not r.completed` -> inconclusive_hit), NOT the BROKEN branch (which requires completed=True AND not resolved, L306-309).

WHY THIS IS NOT A REFINEMENT-FIDELITY BREAK: (a) It exploits a UNIVERSAL property of Nagini's declared partial-correctness methodology (prompts/nagini/quickref.md line 6: 'Termination proofs are NOT required by default'; only 1/500 reference nagini bundles use Decreases). Any loop in any bundle can be replaced by a non-terminating one that vacuously verifies, so counting this as a per-bundle spec defect would uniformly 'break' the entire nagini track — clearly not the intended verify⟹correct semantics (which is modulo termination, the standard deductive-verification caveat). (b) G-EQ tests refinement FIDELITY of the computed FUNCTION; the functional battery (6 distinct wrong computations, all REJECTED) proves the spec admits no verifying wrong-computation impl. (c) Mechanically, the non-terminating patch cannot even produce a BROKEN verdict (its resolve never completes). Hence excluded from the submitted falsification battery but fully documented here.

### A-LEG / refinement.md AUDIT (protocol step 3)
Every leg is R / A-reference / I; NO kind-3. A2 (the sole changed op: final-key member-access serialization) is modeled DEEPLY by member_access_segment/json_string_literal (A-reference), NOT a consumed axiom (axioms region empty). Re-ran axiom_check.py (G-AX) in-scratch: PASS — 'member_access_segment deep model == real compile_json_path_final_key on 30 boundary + 70000 fuzz keys; numeric-key bug discriminator confirmed'. Verified axiom_check.py's real_compile_json_path_final_key (`.%s`%json.dumps) and real_compile_json_path are BYTE-FAITHFUL to the repo at base_commit 859a87d873ce7152af73ab851653b4e1c3ffea4c (checked out and gold-applied). Domain in_domain (printable ASCII 32-126 minus 34/92) is exactly where json.dumps(key)=='"'+key+'"'; all 18 distinct test keys are in-domain (verified programmatically). Site B (HasKeyOrArrayIndex wiring) is R/I, routes the final key to one of the two already-modeled forms, no new computation.

### Verdict: SOUND
>=5 attacks run (9 distinct same-spec impls). Every genuinely-wrong COMPUTATION is rejected by the spec; the echo of gold resolves (control); the A-reference and refinement.md are clean; all tested keys lie inside the modeled domain. The only verifying-but-divergent impls are non-terminating (universal partial-correctness artifact, resolve incomplete, not the BROKEN signature). No verify⇏correct counterexample within the methodology's declared scope.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The spec models the fixed callee `compile_json_path_final_key(key) = '.' + json.dumps(key)` deeply as `member_access_segment(key) = '.' + '"' + key + '"'`, restricted to in_domain keys (printable ASCII 32..126, excluding quote 34 and backslash 92). I verified faithfulness on that domain three ways: (1) exhaustive single-char check over 32..126 minus {34,92} — 0 mismatches; (2) 1,000,000 random multi-char keys (len 0..25) over the domain — 0 divergences between the model and real `'.%s' % json.dumps(k)`; (3) the bundle's axiom_check.py (G-AX) passes (30 boundary + 70000 fuzz keys, incl. all-digit stress). The domain restriction is legitimate and non-hiding: it is exactly the region where json.dumps leaves the key verbatim between quotes (it escapes quote/backslash/controls and emits non-ASCII as \uXXXX, none of which occur in-domain), and it covers the F2P numeric-key discriminator ('000'->."000", '1111'->."1111"). Structural postconditions (len=len(key)+3, [0]==46, [1]==34, last==34, key verbatim between quotes) all match the real callee. model.py verifies (Nagini, 19s). No input in the specified domain where the modeled function disagrees with the real repo callee. Spec is not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (swebench_unified.leakage.screen over the spec_view of model.py, python flavor) passes with zero hard failures. Manual gold-reconstruction review of the spec view (module docstring + axioms/pure/pre/post regions; impl elided) confirms NO leakage beyond the public problem_statement:

(1) No patched repo symbol echoed. Changed symbols {compile_json_path_final_key, HasKeyOrArrayIndex, as_sql, as_sqlite, as_oracle, HasAnyKeys} — none appear in spec-view identifiers or comments. The modelled symbols (compile_final_key_segment, member_access_segment, json_string_literal, in_domain, all_digits, is_digit) are generic and do not localize the edit.
(2) No gold-patch line reproduced. The gold body '.%s" % json.dumps(key_transform)' and 'json.dumps' do NOT appear in the spec view (they live only in mapping.md/refinement.md, which are audit docs, not the spec surface). Nothing >=8 chars from a changed line collides.
(3) No diff markers, no patched file path (django/db/models/fields/json.py absent), no module path.
(4) No bug/fix narration (bug/fixed/previously/incorrectly/wrong/pre-patch etc. all absent from spec-view comments).
(5) Pre-patch array-index branch and the HasKeyOrArrayIndex subclass-wiring are discussed only in refinement.md/mapping.md/model_prepatch.py — outside the spec view.

What the spec view DOES state is the target behavior: the final JSON-path step for a key is '.' + '"key"' (member-access form) for EVERY key including all-digit keys like '1111'/'000'. The public problem_statement already discloses the symptom precisely — has_key with numeric key '1111' fails on SQLite/MySQL/Oracle but works on Postgres. Making that publicly-stated symptom precise as a postcondition (the desired output must reproduce the key's exact characters, no array-index conversion) is the intrinsic, legitimate function of a formal spec; it does not narrate the edit, name the mechanism (array-paths, which is a hints_text-only term correctly NOT echoed), or reconstruct the gold. The all-digit examples '1111'/'000' mirror the '1111' example already in problem_statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
