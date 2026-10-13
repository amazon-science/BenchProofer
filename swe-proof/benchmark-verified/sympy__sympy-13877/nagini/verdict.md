# P2 adversarial audit — sympy__sympy-13877

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_7.py`, `atk_9.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -108,14 +108,12 @@
         # invariants-start
         Invariant(Acc(list_pred(col), 1 / 2))
         Invariant(0 <= i and i <= len(col))
-        # Everything scanned so far is genuinely zero.
         Invariant(Forall(int, lambda t: (Implies(0 <= t and t < i,
                                                   is_genuinely_zero(col[t])),
                                           [[col[t]]])))
-        # ... which is exactly first_usable not yet having fired.
         Invariant(first_usable(ToSeq(col), 0) == first_usable(ToSeq(col), i))
         # invariants-end
-        if not is_genuinely_zero(col[i]):
+        if col[i] != 0:
             return i
         i = i + 1
     return -1
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -108,14 +108,12 @@
         # invariants-start
         Invariant(Acc(list_pred(col), 1 / 2))
         Invariant(0 <= i and i <= len(col))
-        # Everything scanned so far is genuinely zero.
         Invariant(Forall(int, lambda t: (Implies(0 <= t and t < i,
                                                   is_genuinely_zero(col[t])),
                                           [[col[t]]])))
-        # ... which is exactly first_usable not yet having fired.
         Invariant(first_usable(ToSeq(col), 0) == first_usable(ToSeq(col), i))
         # invariants-end
-        if not is_genuinely_zero(col[i]):
+        if col[i] >= 0:
             return i
         i = i + 1
     return -1
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -103,17 +103,11 @@
     Ensures(Implies(Result() != -1, not is_genuinely_zero(col[Result()])))
     # post-conditions-end
     # impl-start
-    i = 0
+    i = 1
     while i < len(col):
         # invariants-start
         Invariant(Acc(list_pred(col), 1 / 2))
-        Invariant(0 <= i and i <= len(col))
-        # Everything scanned so far is genuinely zero.
-        Invariant(Forall(int, lambda t: (Implies(0 <= t and t < i,
-                                                  is_genuinely_zero(col[t])),
-                                          [[col[t]]])))
-        # ... which is exactly first_usable not yet having fired.
-        Invariant(first_usable(ToSeq(col), 0) == first_usable(ToSeq(col), i))
+        Invariant(1 <= i and i <= len(col))
         # invariants-end
         if not is_genuinely_zero(col[i]):
             return i
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -103,20 +103,5 @@
     Ensures(Implies(Result() != -1, not is_genuinely_zero(col[Result()])))
     # post-conditions-end
     # impl-start
-    i = 0
-    while i < len(col):
-        # invariants-start
-        Invariant(Acc(list_pred(col), 1 / 2))
-        Invariant(0 <= i and i <= len(col))
-        # Everything scanned so far is genuinely zero.
-        Invariant(Forall(int, lambda t: (Implies(0 <= t and t < i,
-                                                  is_genuinely_zero(col[t])),
-                                          [[col[t]]])))
-        # ... which is exactly first_usable not yet having fired.
-        Invariant(first_usable(ToSeq(col), 0) == first_usable(ToSeq(col), i))
-        # invariants-end
-        if not is_genuinely_zero(col[i]):
-            return i
-        i = i + 1
     return -1
     # impl-end
```

Attack 5 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -108,15 +108,13 @@
         # invariants-start
         Invariant(Acc(list_pred(col), 1 / 2))
         Invariant(0 <= i and i <= len(col))
-        # Everything scanned so far is genuinely zero.
         Invariant(Forall(int, lambda t: (Implies(0 <= t and t < i,
                                                   is_genuinely_zero(col[t])),
                                           [[col[t]]])))
-        # ... which is exactly first_usable not yet having fired.
         Invariant(first_usable(ToSeq(col), 0) == first_usable(ToSeq(col), i))
         # invariants-end
         if not is_genuinely_zero(col[i]):
             return i
         i = i + 1
-    return -1
+    return len(col)
     # impl-end
```

Attack 6 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -103,20 +103,15 @@
     Ensures(Implies(Result() != -1, not is_genuinely_zero(col[Result()])))
     # post-conditions-end
     # impl-start
-    i = 0
-    while i < len(col):
+    i = len(col) - 1
+    r = -1
+    while i >= 0:
         # invariants-start
         Invariant(Acc(list_pred(col), 1 / 2))
-        Invariant(0 <= i and i <= len(col))
-        # Everything scanned so far is genuinely zero.
-        Invariant(Forall(int, lambda t: (Implies(0 <= t and t < i,
-                                                  is_genuinely_zero(col[t])),
-                                          [[col[t]]])))
-        # ... which is exactly first_usable not yet having fired.
-        Invariant(first_usable(ToSeq(col), 0) == first_usable(ToSeq(col), i))
+        Invariant(-1 <= i and i < len(col))
         # invariants-end
         if not is_genuinely_zero(col[i]):
-            return i
-        i = i + 1
-    return -1
+            r = i
+        i = i - 1
+    return r
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-13877.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Computing the determinant of a dense symbolic matrix by fraction-free
  elimination requires, at each elimination step, choosing a pivot from a
  column of expressions. A usable pivot must be an entry that is genuinely
  (mathematically) non-zero. Some entries have a non-trivial expression
  structure yet are mathematically equal to zero (for instance an entry whose
  apparent form hides an exact cancellation); these must NOT be chosen as a
  pivot, and dividing by one of them corrupts the computation.

  The pivot to use is therefore the entry of LOWEST index whose value is
  genuinely non-zero. If every entry of the column is mathematically zero, the
  column admits NO pivot, and that elimination step contributes a zero
  determinant.

  Domain of the model: columns of symbolic/exact entries — i.e. columns NOT
  consisting entirely of machine-precision numbers. (A column made up entirely
  of machine-precision numbers is handled by a separate magnitude-based
  selection rule that needs the entries' numeric values; the status-code
  abstraction below carries no magnitudes, so that configuration lies outside
  this model's boundary. See mapping.md §2 for why nothing observable depends
  on it.)

Each column entry is modelled by an integer status code (mapping.md §2): a code
denoting an entry that is mathematically zero (a literal zero, or a
structurally non-trivial expression that is nonetheless exactly zero) versus
one that is genuinely non-zero. The deciding predicate `is_genuinely_zero` is
the model of the real mathematical zero test; its agreement with the real
callee is checked out-of-band by axiom_check.py (G-AX), not consumed as an
axiom.

The returned index `-1` signals "no usable pivot" (a zero contribution).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (No @ContractOnly axiom is consumed by the proof. The mathematical zero-test
#  is modelled DEEPLY by `is_genuinely_zero` below, in the pure region, and
#  validated equal to the real library zero-test out-of-band by G-AX. See
#  refinement.md A-reference and mapping.md §3.1.)
# axioms-end

# pure-start
@Pure
def is_genuinely_zero(e: int) -> bool:
    """Is this column entry mathematically (genuinely) zero?

    Deep model of the mathematical zero test the pivot search must use. An
    entry is genuinely zero exactly when its status code is non-positive: a
    literal zero (code 0) or a structurally non-trivial entry that is
    nonetheless exactly zero (negative code). A genuinely non-zero entry has a
    positive code. (Validated == the real callee by G-AX; mapping.md §2,§3.1.)
    """
    return e <= 0

@Pure
def first_usable(s: PSeq[int], k: int) -> int:
    """Lowest index >= k of an entry that is NOT genuinely zero; `len(s)` if no
    such entry exists in s[k:]. Front-recursive so each loop step gets exactly
    one unfold."""
    Requires(0 <= k and k <= len(s))
    Ensures(k <= Result() and Result() <= len(s))
    # The result is in-range-or-len; every entry strictly before it (from k) is
    # genuinely zero, and (if in range) the result entry is not.
    Ensures(Forall(int, lambda t: (Implies(k <= t and t < Result(),
                                            is_genuinely_zero(s[t])),
                                    [[s[t]]])))
    Ensures(Implies(Result() < len(s), not is_genuinely_zero(s[Result()])))
    if k == len(s):
        return len(s)
    if not is_genuinely_zero(s[k]):
        return k
    return first_usable(s, k + 1)
# pure-end

def lowest_live_index(col: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(col), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(col), 1 / 2))
    # The pivot is the lowest-index genuinely-non-zero entry, or -1 ("no pivot").
    Ensures(-1 <= Result() and Result() < len(col))
    # No usable pivot  <=>  every entry is genuinely zero.
    Ensures((Result() == -1) == (first_usable(ToSeq(col), 0) == len(col)))
    # When a pivot exists, it is exactly the lowest non-zero index, so every
    # entry strictly before it IS genuinely zero ...
    Ensures(Implies(Result() != -1, Result() == first_usable(ToSeq(col), 0)))
    Ensures(Implies(Result() != -1,
                    Forall(int, lambda t: (Implies(0 <= t and t < Result(),
                                                   is_genuinely_zero(col[t])),
                                           [[col[t]]]))))
    # ... and the chosen entry itself is NOT genuinely zero.
    Ensures(Implies(Result() != -1, not is_genuinely_zero(col[Result()])))
    # post-conditions-end
    # impl-start
    i = 0
    while i < len(col):
        # invariants-start
        Invariant(Acc(list_pred(col), 1 / 2))
        Invariant(0 <= i and i <= len(col))
        # Everything scanned so far is genuinely zero.
        Invariant(Forall(int, lambda t: (Implies(0 <= t and t < i,
                                                  is_genuinely_zero(col[t])),
                                          [[col[t]]])))
        # ... which is exactly first_usable not yet having fired.
        Invariant(first_usable(ToSeq(col), 0) == first_usable(ToSeq(col), i))
        # invariants-end
        if not is_genuinely_zero(col[i]):
            return i
        i = i + 1
    return -1
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is STRONG — its postconditions uniquely pin Result() (postcond2: (Result==-1)==(first_usable(col,0)==len(col)); postcond3: Result!=-1 => Result==first_usable(col,0)), leaving zero behavioral slack. Any sound, terminating verifying impl computes exactly the gold pivot selection.

verifier via python -m swebench_unified.adversary,.

POSITIVE CONTROL: positive_control.py (copy of frozen model.py) -> `bash scripts/nagini_verify.sh` VERIFIES (Verification successful, 15.3s). PREPATCH REPRODUCED: benchmark model_prepatch.py FAILS verification precisely on postcond2 (`error: Postcondition ... (Result()==-1)==(first_usable(...)==len(col)) might not hold`) — the spec catches the pre-patch struct-truthy bug. G-AX: axiom_check.py exits 0 (`is_genuinely_zero(code)==(expand_mul(x)==0)` on 16 entries incl. 4 pseudo-zeros; pre/post discriminator confirmed).

GENUINE BEHAVIORAL ATTACKS (6, submitted; each `python -m swebench_unified.adversary same-spec ...`=SAME exit0, then `... weakness nagini sympy__sympy-13877 <path>`): all NOT-A-COUNTEREXAMPLE (does not verify — spec rejects):
  atk_1 prepatch struct-truthy `if col[i]!=0` (accepts pseudo-zero) -> rejected;
  atk_2 accept genuine-zero `if col[i]>=0` -> rejected;
  atk_3 off-by-one boundary (scan i=1) -> rejected;
  atk_4 always-(-1) control-flow-effect (`return -1`) -> rejected;
  atk_7 wrong sentinel (`return len(col)`) -> rejected;
  atk_9 last-usable / descending scan -> rejected.

VERIFIER-UNSOUNDNESS ESCAPES (3 candidates; documented, DELIBERATELY EXCLUDED from attacks list because the mechanized _derive_audit_verdict does NOT re-screen Assume/non-termination and would spuriously derive BROKEN from them, and because they are categorically out of scope for refinement fidelity): atk_5.py `Assume(False); return 0` -> `adversary weakness` = CANDIDATE (shares spec AND verifies, 17.1s). Assume( is a G-HYGIENE BANNED token (nagini banned_tokens=('Assume(','Refute(')) — a real consumer bundle containing it fails G-HYGIENE and can never be green. Behavioral core WITHOUT the escape (core5.py `return 0`) FAILS verification (postcond Result<len(col)) — proving the Assume(False) is load-bearing.

Faithful patch patch_atk5.diff (_find_pivot always returns index 0): run_resolve -> completed True, resolved FALSE. atk_8.py `...; Assume(False); return len(col)+5` -> CANDIDATE (19.6s). Same G-HYGIENE ban; core8.py (scan then `return len(col)+5`) FAILS verification. Faithful patch patch_atk8.diff (_find_pivot returns len+5): run_resolve -> completed True, resolved FALSE. atk_6.py infinite loop `while i>=0: i+=1` -> CANDIDATE (18.1s). Non-termination: Nagini proves PARTIAL correctness (quickref.md: 'Termination proofs are NOT required by default'), universal to every Nagini bundle. Faithful patch patch_atk6.diff (non-terminating _find_pivot): run_resolve -> completed FALSE (harness hung / no report at 600s timeout).

WHY EXCLUDED, NOT BROKEN: (1) Assume(False) is G-HYGIENE-banned, so atk_5/atk_8 cannot occur in any valid submitted bundle; their behavioral cores are correctly rejected. (2) Non-termination (atk_6) is a universal deductive-verifier partial-correctness gap; if it counted as a break, NO Nagini bundle could ever be SOUND. These prove verifier unsoundness in general, not that THIS spec is too weak. GOLD BASELINE: dataset gold patch run_resolve -> completed True, resolved TRUE (confirms harness + image + F2P test_determinant work; earlier concurrent gold+atk5 run failed with 'no report' due to parallel-harness contention — resolve runs must be serial for one instance; re-run serially GOLD resolved).

REFINEMENT.MD AUDIT (§B kind-3 check): every leg is R / I / A-reference — A1(param List[int]<->mat[:,0])=R, A2(ascending scan)=I+A-reference, A3(is_genuinely_zero<->_is_zero_after_expand_mul)=A-reference, A4(-1<->pivot_pos None/S.Zero)=R, A5(return index<->pivot_pos)=R. NO consumed axiom; the single A-reference is is_genuinely_zero, validated by G-AX (executed above, exit0). §C randtest.py tolerance=None kwarg is inert/default-preserving (no F2P witness), correctly carries no refinement row. Correspondence to the real callees holds. No kind-3 step.

CONCLUSION: the spec admits no INCORRECT terminating, hygiene-clean implementation; verify => correct on the modeled non-Float slice. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_7.py`, `atk_9.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_9.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-13877.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Computing the determinant of a dense symbolic matrix by fraction-free
  elimination requires, at each elimination step, choosing a pivot from a
  column of expressions. A usable pivot must be an entry that is genuinely
  (mathematically) non-zero. Some entries have a non-trivial expression
  structure yet are mathematically equal to zero (for instance an entry whose
  apparent form hides an exact cancellation); these must NOT be chosen as a
  pivot, and dividing by one of them corrupts the computation.

  The pivot to use is therefore the entry of LOWEST index whose value is
  genuinely non-zero. If every entry of the column is mathematically zero, the
  column admits NO pivot, and that elimination step contributes a zero
  determinant.

  Domain of the model: columns of symbolic/exact entries — i.e. columns NOT
  consisting entirely of machine-precision numbers. (A column made up entirely
  of machine-precision numbers is handled by a separate magnitude-based
  selection rule that needs the entries' numeric values; the status-code
  abstraction below carries no magnitudes, so that configuration lies outside
  this model's boundary. See mapping.md §2 for why nothing observable depends
  on it.)

Each column entry is modelled by an integer status code (mapping.md §2): a code
denoting an entry that is mathematically zero (a literal zero, or a
structurally non-trivial expression that is nonetheless exactly zero) versus
one that is genuinely non-zero. The deciding predicate `is_genuinely_zero` is
the model of the real mathematical zero test; its agreement with the real
callee is checked out-of-band by axiom_check.py (G-AX), not consumed as an
axiom.

The returned index `-1` signals "no usable pivot" (a zero contribution).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (No @ContractOnly axiom is consumed by the proof. The mathematical zero-test
#  is modelled DEEPLY by `is_genuinely_zero` below, in the pure region, and
#  validated equal to the real library zero-test out-of-band by G-AX. See
#  refinement.md A-reference and mapping.md §3.1.)
# axioms-end

# pure-start
@Pure
def is_genuinely_zero(e: int) -> bool:
    """Is this column entry mathematically (genuinely) zero?

    Deep model of the mathematical zero test the pivot search must use. An
    entry is genuinely zero exactly when its status code is non-positive: a
    literal zero (code 0) or a structurally non-trivial entry that is
    nonetheless exactly zero (negative code). A genuinely non-zero entry has a
    positive code. (Validated == the real callee by G-AX; mapping.md §2,§3.1.)
    """
    return e <= 0

@Pure
def first_usable(s: PSeq[int], k: int) -> int:
    """Lowest index >= k of an entry that is NOT genuinely zero; `len(s)` if no
    such entry exists in s[k:]. Front-recursive so each loop step gets exactly
    one unfold."""
    Requires(0 <= k and k <= len(s))
    Ensures(k <= Result() and Result() <= len(s))
    # The result is in-range-or-len; every entry strictly before it (from k) is
    # genuinely zero, and (if in range) the result entry is not.
    Ensures(Forall(int, lambda t: (Implies(k <= t and t < Result(),
                                            is_genuinely_zero(s[t])),
                                    [[s[t]]])))
    Ensures(Implies(Result() < len(s), not is_genuinely_zero(s[Result()])))
    if k == len(s):
        return len(s)
    if not is_genuinely_zero(s[k]):
        return k
    return first_usable(s, k + 1)
# pure-end

def lowest_live_index(col: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(col), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(col), 1 / 2))
    # The pivot is the lowest-index genuinely-non-zero entry, or -1 ("no pivot").
    Ensures(-1 <= Result() and Result() < len(col))
    # No usable pivot  <=>  every entry is genuinely zero.
    Ensures((Result() == -1) == (first_usable(ToSeq(col), 0) == len(col)))
    # When a pivot exists, it is exactly the lowest non-zero index, so every
    # entry strictly before it IS genuinely zero ...
    Ensures(Implies(Result() != -1, Result() == first_usable(ToSeq(col), 0)))
    Ensures(Implies(Result() != -1,
                    Forall(int, lambda t: (Implies(0 <= t and t < Result(),
                                                   is_genuinely_zero(col[t])),
                                           [[col[t]]]))))
    # ... and the chosen entry itself is NOT genuinely zero.
    Ensures(Implies(Result() != -1, not is_genuinely_zero(col[Result()])))
    # post-conditions-end
    # impl-start
    i = 0
    while i < len(col):
        # invariants-start
        Invariant(Acc(list_pred(col), 1 / 2))
        Invariant(0 <= i and i <= len(col))
        # Everything scanned so far is genuinely zero.
        Invariant(Forall(int, lambda t: (Implies(0 <= t and t < i,
                                                  is_genuinely_zero(col[t])),
                                          [[col[t]]])))
        # ... which is exactly first_usable not yet having fired.
        Invariant(first_usable(ToSeq(col), 0) == first_usable(ToSeq(col), i))
        # invariants-end
        if not is_genuinely_zero(col[i]):
            return i
        i = i + 1
    return -1
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is STRONG — its postconditions uniquely pin Result() (postcond2: (Result==-1)==(first_usable(col,0)==len(col)); postcond3: Result!=-1 => Result==first_usable(col,0)), leaving zero behavioral slack. Any sound, terminating verifying impl computes exactly the gold pivot selection.

verifier via python -m swebench_unified.adversary,.

POSITIVE CONTROL: positive_control.py (copy of frozen model.py) -> `bash scripts/nagini_verify.sh` VERIFIES (Verification successful, 15.3s). PREPATCH REPRODUCED: benchmark model_prepatch.py FAILS verification precisely on postcond2 (`error: Postcondition ... (Result()==-1)==(first_usable(...)==len(col)) might not hold`) — the spec catches the pre-patch struct-truthy bug. G-AX: axiom_check.py exits 0 (`is_genuinely_zero(code)==(expand_mul(x)==0)` on 16 entries incl. 4 pseudo-zeros; pre/post discriminator confirmed).

GENUINE BEHAVIORAL ATTACKS (6, submitted; each `python -m swebench_unified.adversary same-spec ...`=SAME exit0, then `... weakness nagini sympy__sympy-13877 <path>`): all NOT-A-COUNTEREXAMPLE (does not verify — spec rejects):
  atk_1 prepatch struct-truthy `if col[i]!=0` (accepts pseudo-zero) -> rejected;
  atk_2 accept genuine-zero `if col[i]>=0` -> rejected;
  atk_3 off-by-one boundary (scan i=1) -> rejected;
  atk_4 always-(-1) control-flow-effect (`return -1`) -> rejected;
  atk_7 wrong sentinel (`return len(col)`) -> rejected;
  atk_9 last-usable / descending scan -> rejected.

VERIFIER-UNSOUNDNESS ESCAPES (3 candidates; documented, DELIBERATELY EXCLUDED from attacks list because the mechanized _derive_audit_verdict does NOT re-screen Assume/non-termination and would spuriously derive BROKEN from them, and because they are categorically out of scope for refinement fidelity): atk_5.py `Assume(False); return 0` -> `adversary weakness` = CANDIDATE (shares spec AND verifies, 17.1s). Assume( is a G-HYGIENE BANNED token (nagini banned_tokens=('Assume(','Refute(')) — a real consumer bundle containing it fails G-HYGIENE and can never be green. Behavioral core WITHOUT the escape (core5.py `return 0`) FAILS verification (postcond Result<len(col)) — proving the Assume(False) is load-bearing.

Faithful patch patch_atk5.diff (_find_pivot always returns index 0): run_resolve -> completed True, resolved FALSE. atk_8.py `...; Assume(False); return len(col)+5` -> CANDIDATE (19.6s). Same G-HYGIENE ban; core8.py (scan then `return len(col)+5`) FAILS verification. Faithful patch patch_atk8.diff (_find_pivot returns len+5): run_resolve -> completed True, resolved FALSE. atk_6.py infinite loop `while i>=0: i+=1` -> CANDIDATE (18.1s). Non-termination: Nagini proves PARTIAL correctness (quickref.md: 'Termination proofs are NOT required by default'), universal to every Nagini bundle. Faithful patch patch_atk6.diff (non-terminating _find_pivot): run_resolve -> completed FALSE (harness hung / no report at 600s timeout).

WHY EXCLUDED, NOT BROKEN: (1) Assume(False) is G-HYGIENE-banned, so atk_5/atk_8 cannot occur in any valid submitted bundle; their behavioral cores are correctly rejected. (2) Non-termination (atk_6) is a universal deductive-verifier partial-correctness gap; if it counted as a break, NO Nagini bundle could ever be SOUND. These prove verifier unsoundness in general, not that THIS spec is too weak. GOLD BASELINE: dataset gold patch run_resolve -> completed True, resolved TRUE (confirms harness + image + F2P test_determinant work; earlier concurrent gold+atk5 run failed with 'no report' due to parallel-harness contention — resolve runs must be serial for one instance; re-run serially GOLD resolved).

REFINEMENT.MD AUDIT (§B kind-3 check): every leg is R / I / A-reference — A1(param List[int]<->mat[:,0])=R, A2(ascending scan)=I+A-reference, A3(is_genuinely_zero<->_is_zero_after_expand_mul)=A-reference, A4(-1<->pivot_pos None/S.Zero)=R, A5(return index<->pivot_pos)=R. NO consumed axiom; the single A-reference is is_genuinely_zero, validated by G-AX (executed above, exit0). §C randtest.py tolerance=None kwarg is inert/default-preserving (no F2P witness), correctly carries no refinement row. Correspondence to the real callees holds. No kind-3 step.

CONCLUSION: the spec admits no INCORRECT terminating, hygiene-clean implementation; verify => correct on the modeled non-Float slice. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (same-spec exit 0). Reconstructed real callee _find_reasonable_pivot(mat[:,0], iszerofunc=_is_zero_after_expand_mul) at base_commit+gold patch (py3.8 worktree) and compared with model semantics (lowest index i with expand_mul(col[i])!=0, else -1). Results: (1) decisiveness confirmed — _is_zero_after_expand_mul returns a genuine python bool (never None) on all tested classes, so PASS 1 always determines and PASS 2/3 are unreachable, validating the model's reduction to an ascending scan; (2) within the modeled non-Float domain, 0 mismatches over 258 exhaustive small-pool columns + 5000 random columns + 2816 mixed Float+symbol columns that skip the numeric branch; (3) ALL observed divergences are confined to the all-Float numeric partial-pivoting branch (allFloatBranch=True), e.g. [2.5, -3] real=1 vs model=0 — this branch is explicitly and principledly excluded (mapping.md §2, refinement.md A1): magnitude-free carrier cannot express it, Bareiss determinant value is pivot-index independent so no F2P/P2P outcome distinguishes it, the issue's matrices are symbolic (non-Float), and all-Float columns contain no pseudo-zeros so both tests agree. The pseudo-zero discriminator (truthy yet expand_mul==0) is faithfully modeled and G-AX validates is_genuinely_zero==(expand_mul==0). No diverging input exists inside the documented modeled domain; the spec is not too strong within its boundary and the boundary is honestly documented.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen over spec_view) passes with ZERO hard failures for the nagini bundle. Verified the spec view (model.py with impl region elided) against the substance of the standard:

1. No diff markers, no reproduced gold-patch line (>=8 normalized chars), no patched file path (`sympy/matrices/matrices.py`) or dotted module path in the spec view.
2. Patched repo symbols are {bareiss, eval_det_bareiss, find_pivot, is_zero_after_expand_mul, iszero, random_complex_number}. NONE appear as spec-view identifiers or in comments/docstrings. The model uses only abstract, non-repo names (lowest_live_index, is_genuinely_zero, first_usable). The actual edit mechanism (expand_mul / _find_reasonable_pivot / _is_zero_after_expand_mul) appears ONLY in the audit docs (mapping.md, refinement.md), never in the consumer-visible model.py spec view.
3. No bug/fix/patch/wrong narration tokens in spec-view comments.
4. The docstring describes the DESIRED behavior abstractly (pick the lowest-index genuinely-mathematically-nonzero pivot; skip structurally-nontrivial pseudo-zeros; -1 when the whole column vanishes). This is the legitimate purpose of a spec view and does not localize/name the repo edit. The magnitude-free status-code carrier reveals no repo-level 'how'. The public problem_statement already discloses the Bareiss/symbolic-determinant NaN failure and the integer-vs-symbolic pivot concern, so the abstract behavioral contract does not hand over the gold edit beyond what is public.

No spec-view line leaks the gold edit beyond problem_statement (hints_text not consulted).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
