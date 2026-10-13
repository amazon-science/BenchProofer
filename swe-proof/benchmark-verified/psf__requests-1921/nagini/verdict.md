# P2 adversarial audit — psf__requests-1921

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1_selfcall_plain.py`, `atk_2_selfcall_measure_guarded.py`, `atk_3_spin_targeted.py`, `atk_4_prepatch.py`, `atk_5_partial_domain.py`, `atk_6_boundary_offbyone.py`, `atk_7_reversed_precedence.py`, `atk_8_none_as_absent.py`, `atk_9_overdrop.py`, `atk_10_mutate_session.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_11_echo_oracle.py`, `atk_12_pure_echo.py`, `atk_13_alias_mutate.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_selfcall_plain.py` → rejected (same spec, does not verify — good)

```diff
@@ -158,27 +158,17 @@
             k < len(session) and k < len(request),
             result[k] == combined(session[k], request[k])),
             [[result[k]]])))
-        # One key of the universe is settled per step, so the number of keys
-        # still to settle strictly decreases: this body's measure for the
-        # delivery obligation the contract states.
         Invariant(MustTerminate(n - i + 1))
         # invariants-end
         sv = session[i]
         rv = request[i]
-        # Precedence: the per-request value wins where the per-request
-        # collection carries the key, else the per-session value.
         if rv != absent():
             ev = rv
         else:
             ev = sv
-        Assert(ev == effective(sv, rv))
-        # Drop the key (absent) when its effective value is the unset value,
-        # regardless of which side contributed it; otherwise carry it through.
         if ev == none_val():
-            val = absent()
-        else:
-            val = ev
-        Assert(val == combined(sv, rv))
+            return effective_collection(session, request, n)
+        val = ev
         old_result = result
         result = result + [val]
         Assert(len(result) == len(old_result) + 1)
```

Attack 2 — `atk_2_selfcall_measure_guarded.py` → rejected (same spec, does not verify — good)

```diff
@@ -158,27 +158,20 @@
             k < len(session) and k < len(request),
             result[k] == combined(session[k], request[k])),
             [[result[k]]])))
-        # One key of the universe is settled per step, so the number of keys
-        # still to settle strictly decreases: this body's measure for the
-        # delivery obligation the contract states.
         Invariant(MustTerminate(n - i + 1))
         # invariants-end
         sv = session[i]
         rv = request[i]
-        # Precedence: the per-request value wins where the per-request
-        # collection carries the key, else the per-session value.
         if rv != absent():
             ev = rv
         else:
             ev = sv
-        Assert(ev == effective(sv, rv))
-        # Drop the key (absent) when its effective value is the unset value,
-        # regardless of which side contributed it; otherwise carry it through.
+        if ev == none_val() and i + 2 < n:
+            return effective_collection(session, request, n)
         if ev == none_val():
             val = absent()
         else:
             val = ev
-        Assert(val == combined(sv, rv))
         old_result = result
         result = result + [val]
         Assert(len(result) == len(old_result) + 1)
```

Attack 3 — `atk_3_spin_targeted.py` → rejected (same spec, does not verify — good)

```diff
@@ -158,27 +158,27 @@
             k < len(session) and k < len(request),
             result[k] == combined(session[k], request[k])),
             [[result[k]]])))
-        # One key of the universe is settled per step, so the number of keys
-        # still to settle strictly decreases: this body's measure for the
-        # delivery obligation the contract states.
         Invariant(MustTerminate(n - i + 1))
         # invariants-end
         sv = session[i]
         rv = request[i]
-        # Precedence: the per-request value wins where the per-request
-        # collection carries the key, else the per-session value.
         if rv != absent():
             ev = rv
         else:
             ev = sv
-        Assert(ev == effective(sv, rv))
-        # Drop the key (absent) when its effective value is the unset value,
-        # regardless of which side contributed it; otherwise carry it through.
         if ev == none_val():
+            spin = 0
+            while spin >= 0:
+                Invariant(Acc(list_pred(session), 1 / 2))
+                Invariant(Acc(list_pred(request), 1 / 2))
+                Invariant(Acc(list_pred(result)))
+                Invariant(0 <= i and i < n)
+                Invariant(n <= len(session) and n <= len(request))
+                Invariant(len(result) == i)
+                spin = spin + 1
             val = absent()
         else:
             val = ev
-        Assert(val == combined(sv, rv))
         old_result = result
         result = result + [val]
         Assert(len(result) == len(old_result) + 1)
```

Attack 4 — `atk_4_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -158,27 +158,18 @@
             k < len(session) and k < len(request),
             result[k] == combined(session[k], request[k])),
             [[result[k]]])))
-        # One key of the universe is settled per step, so the number of keys
-        # still to settle strictly decreases: this body's measure for the
-        # delivery obligation the contract states.
         Invariant(MustTerminate(n - i + 1))
         # invariants-end
         sv = session[i]
         rv = request[i]
-        # Precedence: the per-request value wins where the per-request
-        # collection carries the key, else the per-session value.
         if rv != absent():
             ev = rv
         else:
             ev = sv
-        Assert(ev == effective(sv, rv))
-        # Drop the key (absent) when its effective value is the unset value,
-        # regardless of which side contributed it; otherwise carry it through.
-        if ev == none_val():
+        if rv == none_val():
             val = absent()
         else:
             val = ev
-        Assert(val == combined(sv, rv))
         old_result = result
         result = result + [val]
         Assert(len(result) == len(old_result) + 1)
```

Attack 5 — `atk_5_partial_domain.py` → rejected (same spec, does not verify — good)

```diff
@@ -158,27 +158,18 @@
             k < len(session) and k < len(request),
             result[k] == combined(session[k], request[k])),
             [[result[k]]])))
-        # One key of the universe is settled per step, so the number of keys
-        # still to settle strictly decreases: this body's measure for the
-        # delivery obligation the contract states.
         Invariant(MustTerminate(n - i + 1))
         # invariants-end
         sv = session[i]
         rv = request[i]
-        # Precedence: the per-request value wins where the per-request
-        # collection carries the key, else the per-session value.
         if rv != absent():
             ev = rv
         else:
             ev = sv
-        Assert(ev == effective(sv, rv))
-        # Drop the key (absent) when its effective value is the unset value,
-        # regardless of which side contributed it; otherwise carry it through.
-        if ev == none_val():
+        if ev == none_val() and rv == absent():
             val = absent()
         else:
             val = ev
-        Assert(val == combined(sv, rv))
         old_result = result
         result = result + [val]
         Assert(len(result) == len(old_result) + 1)
```

Attack 6 — `atk_6_boundary_offbyone.py` → rejected (same spec, does not verify — good)

```diff
@@ -146,7 +146,7 @@
     # impl-start
     result = []  # type: List[int]
     i = 0
-    while i < n:
+    while i < n - 1:
         # invariants-start
         Invariant(Acc(list_pred(session), 1 / 2))
         Invariant(Acc(list_pred(request), 1 / 2))
@@ -158,27 +158,18 @@
             k < len(session) and k < len(request),
             result[k] == combined(session[k], request[k])),
             [[result[k]]])))
-        # One key of the universe is settled per step, so the number of keys
-        # still to settle strictly decreases: this body's measure for the
-        # delivery obligation the contract states.
         Invariant(MustTerminate(n - i + 1))
         # invariants-end
         sv = session[i]
         rv = request[i]
-        # Precedence: the per-request value wins where the per-request
-        # collection carries the key, else the per-session value.
         if rv != absent():
             ev = rv
         else:
             ev = sv
-        Assert(ev == effective(sv, rv))
-        # Drop the key (absent) when its effective value is the unset value,
-        # regardless of which side contributed it; otherwise carry it through.
         if ev == none_val():
             val = absent()
         else:
             val = ev
-        Assert(val == combined(sv, rv))
         old_result = result
         result = result + [val]
         Assert(len(result) == len(old_result) + 1)
@@ -186,5 +177,7 @@
         Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(old_result),
             result[k] == old_result[k]), [[result[k]]])))
         i = i + 1
+    if len(result) < n:
+        result = result + [absent()]
     return result
     # impl-end
```

Attack 7 — `atk_7_reversed_precedence.py` → rejected (same spec, does not verify — good)

```diff
@@ -158,27 +158,18 @@
             k < len(session) and k < len(request),
             result[k] == combined(session[k], request[k])),
             [[result[k]]])))
-        # One key of the universe is settled per step, so the number of keys
-        # still to settle strictly decreases: this body's measure for the
-        # delivery obligation the contract states.
         Invariant(MustTerminate(n - i + 1))
         # invariants-end
         sv = session[i]
         rv = request[i]
-        # Precedence: the per-request value wins where the per-request
-        # collection carries the key, else the per-session value.
-        if rv != absent():
+        if sv != absent():
+            ev = sv
+        else:
             ev = rv
-        else:
-            ev = sv
-        Assert(ev == effective(sv, rv))
-        # Drop the key (absent) when its effective value is the unset value,
-        # regardless of which side contributed it; otherwise carry it through.
         if ev == none_val():
             val = absent()
         else:
             val = ev
-        Assert(val == combined(sv, rv))
         old_result = result
         result = result + [val]
         Assert(len(result) == len(old_result) + 1)
```

Attack 8 — `atk_8_none_as_absent.py` → rejected (same spec, does not verify — good)

```diff
@@ -158,27 +158,18 @@
             k < len(session) and k < len(request),
             result[k] == combined(session[k], request[k])),
             [[result[k]]])))
-        # One key of the universe is settled per step, so the number of keys
-        # still to settle strictly decreases: this body's measure for the
-        # delivery obligation the contract states.
         Invariant(MustTerminate(n - i + 1))
         # invariants-end
         sv = session[i]
         rv = request[i]
-        # Precedence: the per-request value wins where the per-request
-        # collection carries the key, else the per-session value.
-        if rv != absent():
+        if rv != absent() and rv != none_val():
             ev = rv
         else:
             ev = sv
-        Assert(ev == effective(sv, rv))
-        # Drop the key (absent) when its effective value is the unset value,
-        # regardless of which side contributed it; otherwise carry it through.
         if ev == none_val():
             val = absent()
         else:
             val = ev
-        Assert(val == combined(sv, rv))
         old_result = result
         result = result + [val]
         Assert(len(result) == len(old_result) + 1)
```

Attack 9 — `atk_9_overdrop.py` → rejected (same spec, does not verify — good)

```diff
@@ -158,27 +158,18 @@
             k < len(session) and k < len(request),
             result[k] == combined(session[k], request[k])),
             [[result[k]]])))
-        # One key of the universe is settled per step, so the number of keys
-        # still to settle strictly decreases: this body's measure for the
-        # delivery obligation the contract states.
         Invariant(MustTerminate(n - i + 1))
         # invariants-end
         sv = session[i]
         rv = request[i]
-        # Precedence: the per-request value wins where the per-request
-        # collection carries the key, else the per-session value.
         if rv != absent():
             ev = rv
         else:
             ev = sv
-        Assert(ev == effective(sv, rv))
-        # Drop the key (absent) when its effective value is the unset value,
-        # regardless of which side contributed it; otherwise carry it through.
-        if ev == none_val():
+        if ev == none_val() or ev == 7:
             val = absent()
         else:
             val = ev
-        Assert(val == combined(sv, rv))
         old_result = result
         result = result + [val]
         Assert(len(result) == len(old_result) + 1)
```

Attack 10 — `atk_10_mutate_session.py` → rejected (same spec, does not verify — good)

```diff
@@ -158,27 +158,19 @@
             k < len(session) and k < len(request),
             result[k] == combined(session[k], request[k])),
             [[result[k]]])))
-        # One key of the universe is settled per step, so the number of keys
-        # still to settle strictly decreases: this body's measure for the
-        # delivery obligation the contract states.
         Invariant(MustTerminate(n - i + 1))
         # invariants-end
         sv = session[i]
         rv = request[i]
-        # Precedence: the per-request value wins where the per-request
-        # collection carries the key, else the per-session value.
         if rv != absent():
             ev = rv
         else:
             ev = sv
-        Assert(ev == effective(sv, rv))
-        # Drop the key (absent) when its effective value is the unset value,
-        # regardless of which side contributed it; otherwise carry it through.
+        session[i] = absent()
         if ev == none_val():
             val = absent()
         else:
             val = ev
-        Assert(val == combined(sv, rv))
         old_result = result
         result = result + [val]
         Assert(len(result) == len(old_result) + 1)
```

Attack 11 — `atk_11_echo_oracle.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -144,47 +144,68 @@
         [[Result()[k]]])))
     # post-conditions-end
     # impl-start
-    result = []  # type: List[int]
+    merged = []  # type: List[int]
     i = 0
     while i < n:
         # invariants-start
         Invariant(Acc(list_pred(session), 1 / 2))
         Invariant(Acc(list_pred(request), 1 / 2))
-        Invariant(Acc(list_pred(result)))
+        Invariant(Acc(list_pred(merged)))
         Invariant(0 <= i and i <= n)
         Invariant(n <= len(session) and n <= len(request))
-        Invariant(len(result) == i)
+        Invariant(len(merged) == i)
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and
             k < len(session) and k < len(request),
-            result[k] == combined(session[k], request[k])),
-            [[result[k]]])))
-        # One key of the universe is settled per step, so the number of keys
-        # still to settle strictly decreases: this body's measure for the
-        # delivery obligation the contract states.
+            merged[k] == effective(session[k], request[k])),
+            [[merged[k]]])))
         Invariant(MustTerminate(n - i + 1))
         # invariants-end
         sv = session[i]
         rv = request[i]
-        # Precedence: the per-request value wins where the per-request
-        # collection carries the key, else the per-session value.
         if rv != absent():
-            ev = rv
+            mv = rv
         else:
-            ev = sv
-        Assert(ev == effective(sv, rv))
-        # Drop the key (absent) when its effective value is the unset value,
-        # regardless of which side contributed it; otherwise carry it through.
-        if ev == none_val():
+            mv = sv
+        old_merged = merged
+        merged = merged + [mv]
+        Assert(len(merged) == len(old_merged) + 1)
+        Assert(merged[i] == mv)
+        Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(old_merged),
+            merged[k] == old_merged[k]), [[merged[k]]])))
+        i = i + 1
+    result = []  # type: List[int]
+    j = 0
+    while j < n:
+        # invariants-start
+        Invariant(Acc(list_pred(session), 1 / 2))
+        Invariant(Acc(list_pred(request), 1 / 2))
+        Invariant(Acc(list_pred(merged)))
+        Invariant(Acc(list_pred(result)))
+        Invariant(0 <= j and j <= n)
+        Invariant(n <= len(session) and n <= len(request))
+        Invariant(len(merged) == n)
+        Invariant(len(result) == j)
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < n and
+            k < len(session) and k < len(request),
+            merged[k] == effective(session[k], request[k])),
+            [[merged[k]]])))
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j and
+            k < len(session) and k < len(request),
+            result[k] == combined(session[k], request[k])),
+            [[result[k]]])))
+        Invariant(MustTerminate(n - j + 1))
+        # invariants-end
+        mv2 = merged[j]
+        if mv2 == none_val():
             val = absent()
         else:
-            val = ev
-        Assert(val == combined(sv, rv))
+            val = mv2
         old_result = result
         result = result + [val]
         Assert(len(result) == len(old_result) + 1)
-        Assert(result[i] == val)
+        Assert(result[j] == val)
         Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(old_result),
             result[k] == old_result[k]), [[result[k]]])))
-        i = i + 1
+        j = j + 1
     return result
     # impl-end
```

Attack 12 — `atk_12_pure_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -158,27 +158,9 @@
             k < len(session) and k < len(request),
             result[k] == combined(session[k], request[k])),
             [[result[k]]])))
-        # One key of the universe is settled per step, so the number of keys
-        # still to settle strictly decreases: this body's measure for the
-        # delivery obligation the contract states.
         Invariant(MustTerminate(n - i + 1))
         # invariants-end
-        sv = session[i]
-        rv = request[i]
-        # Precedence: the per-request value wins where the per-request
-        # collection carries the key, else the per-session value.
-        if rv != absent():
-            ev = rv
-        else:
-            ev = sv
-        Assert(ev == effective(sv, rv))
-        # Drop the key (absent) when its effective value is the unset value,
-        # regardless of which side contributed it; otherwise carry it through.
-        if ev == none_val():
-            val = absent()
-        else:
-            val = ev
-        Assert(val == combined(sv, rv))
+        val = combined(session[i], request[i])
         old_result = result
         result = result + [val]
         Assert(len(result) == len(old_result) + 1)
```

Attack 13 — `atk_13_alias_mutate.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -144,6 +144,44 @@
         [[Result()[k]]])))
     # post-conditions-end
     # impl-start
+    if session is request:
+        j = 0
+        while j < n:
+            # invariants-start
+            Invariant(Acc(list_pred(session)))
+            Invariant(session is request)
+            Invariant(0 <= j and j <= n)
+            Invariant(n <= len(session))
+            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
+                session[k] == absent()), [[session[k]]])))
+            Invariant(MustTerminate(n - j + 1))
+            # invariants-end
+            session[j] = absent()
+            j = j + 1
+        wiped = []  # type: List[int]
+        m = 0
+        while m < n:
+            # invariants-start
+            Invariant(Acc(list_pred(session)))
+            Invariant(Acc(list_pred(wiped)))
+            Invariant(session is request)
+            Invariant(0 <= m and m <= n)
+            Invariant(n <= len(session))
+            Invariant(len(wiped) == m)
+            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < n,
+                session[k] == absent()), [[session[k]]])))
+            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < m,
+                wiped[k] == absent()), [[wiped[k]]])))
+            Invariant(MustTerminate(n - m + 1))
+            # invariants-end
+            old_wiped = wiped
+            wiped = wiped + [absent()]
+            Assert(len(wiped) == len(old_wiped) + 1)
+            Assert(wiped[m] == absent())
+            Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(old_wiped),
+                wiped[k] == old_wiped[k]), [[wiped[k]]])))
+            m = m + 1
+        return wiped
     result = []  # type: List[int]
     i = 0
     while i < n:
@@ -158,27 +196,18 @@
             k < len(session) and k < len(request),
             result[k] == combined(session[k], request[k])),
             [[result[k]]])))
-        # One key of the universe is settled per step, so the number of keys
-        # still to settle strictly decreases: this body's measure for the
-        # delivery obligation the contract states.
         Invariant(MustTerminate(n - i + 1))
         # invariants-end
         sv = session[i]
         rv = request[i]
-        # Precedence: the per-request value wins where the per-request
-        # collection carries the key, else the per-session value.
         if rv != absent():
             ev = rv
         else:
             ev = sv
-        Assert(ev == effective(sv, rv))
-        # Drop the key (absent) when its effective value is the unset value,
-        # regardless of which side contributed it; otherwise carry it through.
         if ev == none_val():
             val = absent()
         else:
             val = ev
-        Assert(val == combined(sv, rv))
         old_result = result
         result = result + [val]
         Assert(len(result) == len(old_result) + 1)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for psf__requests-1921.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Two collections of per-key settings are combined into one effective
  collection for a single use. The per-request collection takes precedence over
  the standing per-session collection: where both provide a key, the
  per-request value wins; where only one provides it, that one is used.

  A key may be given the distinguished "unset" value to mean "do not carry this
  key into the effective collection at all". The behaviour that matters: a key
  whose EFFECTIVE value (after precedence) is the unset value must be ABSENT
  from the combined collection -- regardless of WHICH side contributed that
  unset value. In particular a key carried only by the standing per-session
  collection and given the unset value there (never mentioned by the per-request
  collection) must be dropped, not carried through still holding the unset
  value. Every key whose effective value is a real (non-unset) value is carried
  through with exactly that value.

  Consequently the combined collection contains no key mapping to the unset
  value: looking up any key either yields a real value or finds the key absent.

  Combining always COMPLETES: for every admissible pair of collections the
  combination delivers the collection described above after finitely many
  steps. A computation that never delivers one has not met the guarantees --
  they are claims about a result that is actually produced.

Modelling choices (Nagini fragment):
  * Each collection is modelled as a ``List[int]`` indexed by key position: the
    universe of keys is the index set ``0 .. n-1``, common to both inputs and
    the output, and position ``k`` carries the value held for key ``k``. Only
    membership ("is key k carried, and with what value") is observed, so integer
    identity is the faithful carrier (mapping.md S2); string keys are irrelevant
    to the tested behaviour and are banned from indexing in Nagini anyway.
  * Two distinguished values: ``ABSENT`` means "key not carried by this
    collection / dropped from the result", and ``NONE_VAL`` means "the explicit
    unset value a caller may store under a key". Any other (real) value is an
    ordinary setting. ``NONE_VAL`` is modelled as a value distinct from
    ``ABSENT`` precisely so that a key explicitly set to the unset value is
    distinguishable from a key that was simply never provided -- the
    distinction the behaviour under specification turns on.
  * The two inputs are read only (held at fractional permission, required and
    ensured); the output collection is freshly built and fully owned. No string
    indexing is used (Nagini bans it).
  * Delivery of a result is an obligation of the contract, not an assumption:
    the method carries ``MustTerminate``, so the postconditions are guarantees
    about a collection that is handed back. The decreasing measure that
    discharges it for THIS body lives in the (elided) impl region, so any other
    implementation supplies whatever measure its own control flow needs.

The behaviour is modelled deeply (the precedence merge and the unset-value drop
are spelled out in the impl region); there is no axiomatised callee. Markers
(machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# No axioms: combining two key/value collections with precedence and dropping
# keys whose effective value is the unset value is the behaviour under
# specification and is spelled out deeply in the impl region. There is no
# unchanged opaque callee to axiomatise.
# axioms-end

# pure-start
@Pure
def absent() -> int:
    # The distinguished value meaning "key not carried by this collection" (an
    # input position) / "key dropped from the combined collection" (an output
    # position): a lookup finds the key absent.
    return 0

@Pure
def none_val() -> int:
    # The distinguished explicit "unset" value a caller may store under a key.
    # A key whose effective value is this must be dropped from the result.
    return -1

@Pure
def effective(sv: int, rv: int) -> int:
    # The effective value for a key before the unset-drop: the per-request value
    # wins where the per-request collection carries the key (rv != absent()),
    # otherwise the standing per-session value is used.
    if rv != absent():
        return rv
    return sv

@Pure
def combined(sv: int, rv: int) -> int:
    # The value the combined collection holds for a key: the effective value,
    # except that an effective value equal to the unset value drops the key
    # (it becomes absent). This is the per-key behaviour the result must realise.
    if effective(sv, rv) == none_val():
        return absent()
    return effective(sv, rv)
# pure-end

def effective_collection(session: List[int], request: List[int],
                         n: int) -> List[int]:
    # pre-conditions-start
    # The two input collections are read only: fractional permission.
    Requires(Acc(list_pred(session), 1 / 2))
    Requires(Acc(list_pred(request), 1 / 2))
    # The shared key universe is positions 0 .. n-1.
    Requires(0 <= n and n <= len(session) and n <= len(request))
    # Combining is obliged to COMPLETE and hand back a collection: on every
    # admissible input the guarantees below are owed about a result that is
    # actually delivered, so a computation that never delivers one does not
    # satisfy them. (MustTerminate in a Requires transfers the obligation TO
    # this operation; it does not shrink the set of admissible inputs.)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # Inputs unchanged (returned at the same fractional permission).
    Ensures(Acc(list_pred(session), 1 / 2))
    Ensures(Acc(list_pred(request), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The combined collection spans the same key universe.
    Ensures(len(Result()) == n)
    # The key universe still fits inside both inputs (carried so the per-key
    # reads below are in bounds).
    Ensures(n <= len(session) and n <= len(request))
    # (1) Faithful precedence-merge-and-drop: position k of the result is the
    #     per-key combined value -- the per-request value where present else the
    #     per-session value, dropped to absent when that effective value is the
    #     unset value.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < n and
        k < len(session) and k < len(request),
        Result()[k] == combined(session[k], request[k])),
        [[Result()[k]]])))
    # (2) The headline guarantee: no key in the combined collection maps to the
    #     unset value -- every lookup yields a real value or finds the key
    #     absent. This is the clause a drop that only inspects the per-request
    #     side (leaving a session-side unset value in place) violates.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < n,
        Result()[k] != none_val()),
        [[Result()[k]]])))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(session), 1 / 2))
        Invariant(Acc(list_pred(request), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(n <= len(session) and n <= len(request))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and
            k < len(session) and k < len(request),
            result[k] == combined(session[k], request[k])),
            [[result[k]]])))
        # One key of the universe is settled per step, so the number of keys
        # still to settle strictly decreases: this body's measure for the
        # delivery obligation the contract states.
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        sv = session[i]
        rv = request[i]
        # Precedence: the per-request value wins where the per-request
        # collection carries the key, else the per-session value.
        if rv != absent():
            ev = rv
        else:
            ev = sv
        Assert(ev == effective(sv, rv))
        # Drop the key (absent) when its effective value is the unset value,
        # regardless of which side contributed it; otherwise carry it through.
        if ev == none_val():
            val = absent()
        else:
            val = ev
        Assert(val == combined(sv, rv))
        old_result = result
        result = result + [val]
        Assert(len(result) == len(old_result) + 1)
        Assert(result[i] == val)
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(old_result),
            result[k] == old_result[k]), [[result[k]]])))
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) adversarial audit of psf__requests-1921/nagini. VERDICT: SOUND. 13 same-spec attacks + positive control + 1 vacuity control, all machine-run; 3 CANDIDATES materialized as faithful patches and ALL THREE RESOLVED under the official harness. No verifying wrong impl found.

Every attack built by copying the frozen model.py to frozen_model.py and replacing ONLY the text between `# impl-start`/`# impl-end` (builders mk.py / mk2.py); axioms / @Pure / Requires / Ensures byte-identical. All 14 files confirmed `same-spec` = SAME.

### EXACT COMMANDS (repo root swe-proof; D=the scratch dir):
  python -m swebench_unified.adversary same-spec nagini psf__requests-1921 $D/<f>.py   [all -> SAME]
  python -m swebench_unified.adversary weakness  nagini psf__requests-1921 $D/<f>.py   [via $D/wk.sh <name>]
  bash scripts/nagini_verify.sh $D/atk_2_selfcall_measure_guarded.py                  [to capture the rejection reason]
  SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=benchmark-verified python $D/resolve.py $D/patch_atk_<N>.diff 3600   [calls harness.run_resolve]
Attack verifications were run 3-concurrent as background jobs (each Nagini check spawns JVM+Z3); every attack was fully verified and reported.

### PER-ATTACK RESULTS (path / weakness exit / resolve):
pos_control.py                     POSITIVE CONTROL -> CANDIDATE (verifies, 20.8s). The frozen gold impl verifies, so the MustTerminate obligation costs it nothing. atk_1_selfcall_plain.py            REJECTED (exit 2) -- NON-TERMINATION: unbounded self-call `return effective_collection(session, request, n)` on the key whose EFFECTIVE value is the unset value (the exact F2P shape). This is the PRIOR PASS'S counterexample, re-encoded from scratch: it NO LONGER VERIFIES. The MustTerminate repair landed and holds. atk_2_selfcall_measure_guarded.py  REJECTED (exit 2) -- NEW, sharper divergence probe the prior pass never tried: a MEASURE-RESPECTING guarded self-call (guard `ev == none_val() and i + 2 < n`, so the loop measure n-i+1 >= 4 strictly exceeds the callee's MustTerminate(2)).

Direct verify names the reason: "Obligation leak check failed. Callee effective_collection might not take all unsatisfied obligations from the caller." ($D/vfy_atk_2.log). So the obligation is not merely a measure-ordering accident -- Nagini closes the self-call channel regardless of the guard's measure. atk_3_spin_targeted.py             REJECTED (exit 2) -- NON-TERMINATION via a literal inner `while spin >= 0` spin on the F2P key shape (no MustTerminate invariant available for it). atk_4_prepatch.py                  REJECTED (exit 2) -- THE DOCUMENTED PREPATCH BUG re-encoded: drop keyed off `rv == none_val()` (per-request side only), so a session-only unset value survives holding none_val().

PREPATCH REPRODUCED = True. atk_5_partial_domain.py            REJECTED (exit 2) -- PARTIAL DOMAIN: drops only when the SESSION side supplied the unset value (`ev == none_val() and rv == absent()`), carrying a request-side unset value through as none_val(). atk_6_boundary_offbyone.py         REJECTED (exit 2) -- BOUNDARY: loops to n-1 and pads the last position with absent(), so the last key of the universe is never combined. atk_7_reversed_precedence.py       REJECTED (exit 2) -- the SESSION side wins instead of the request side. atk_8_none_as_absent.py            REJECTED (exit 2) -- treats the unset value as "absent" DURING the precedence merge (`rv != absent() and rv != none_val()`), so a request-side unset value fails to override a real session value.

A distinct wrong impl from atk_5: it corrupts `effective`, not the drop. atk_9_overdrop.py                  REJECTED (exit 2) -- OVER-DROP: also drops the perfectly real value 7. Confirms the spec pins the positive direction (real values carried through EXACTLY), not just the drop. atk_10_mutate_session.py           REJECTED (exit 2) -- CONTROL-FLOW EFFECT: writes `session[i] = absent()` on the read-only input. Correctly rejected on the 1/2 fractional permission (no write permission when the two args are distinct objects). atk_11_echo_oracle.py              CANDIDATE (exit 0) -> patch RESOLVED (resolved=True, completed=True, attempts=1, 6/6 F2P, 106/106 P2P, 0 P2F).

CORRECT restructuring in the gold's own shape (build the full precedence merge, then a SEPARATE sweep dropping every unset value). Correctly NOT a weakness -- the separating control. atk_12_pure_echo.py                CANDIDATE (exit 0) -> patch RESOLVED (resolved=True, completed=True, attempts=1, 6/6 F2P, 106/106 P2P). UNGROUNDED-ORACLE ECHO lane: the impl region is literally `val = combined(session[i], request[i])`, i.e. the @Pure spec function applied directly. It verifies, and BECAUSE the behaviour is modelled DEEPLY (no @ContractOnly axiom -- `combined` is spelled out in the pure region and G-AX validates it == the real op), the echo is a genuinely CORRECT impl, and its faithful patch resolves.

This is the key negative result for the A-reference: echoing the oracle here buys no unearned latitude, which is exactly what a deep model (as opposed to an assumed Ensures) should give. atk_13_alias_mutate.py             CANDIDATE (exit 0) -> patch RESOLVED (resolved=True, completed=True, attempts=1, 6/6 F2P, 106/106 P2P). See the ALIASING finding below -- real latitude in the spec, but not a G-EQ break.

**VACUITY CONTROL:** ctl_13_vacuity.py = atk_13 + `Assert(False)` at the top of the `session is request` branch -> DOES NOT VERIFY (exit 2), so atk_13's guarded path is FEASIBLE and it does not verify by way of an infeasible guard.

THE ONE REAL PIECE OF SPEC LATITUDE I FOUND (atk_13), and why it is NOT a break. The two inputs are held at `Acc(list_pred(session), 1/2)` and `Acc(list_pred(request), 1/2)`. When the caller passes the SAME object for both, those fractions SUM TO FULL permission, so a same-spec impl may WRITE the caller's collection; and postconditions (1)/(2) read `session[k]`/`request[k]` in the POST state with no `Old(...)`, so an impl that first zeroes the aliased input to all-absent() and then returns all-absent() is trivially self-consistent w.r.t. the post-state values while destroying the caller's data and returning garbage w.r.t. the PRE state. atk_13 does exactly that and VERIFIES.

I materialized the faithful patch ($D/patch_atk_13.diff: `if request_setting is session_setting: session_setting.clear(); return dict_class()`, plus the gold drop for the non-aliased path) and RAN IT: it RESOLVES, 6/6 F2P, 106/106 P2P. Measured why ($D/behav.py, against the real base_commit tree): the patch is 0/4369 divergent from GOLD on distinct objects, and diverges ONLY on the aliased call -- `merge_setting(d, d)` returns `{}` and wipes the caller's `d`, where gold returns `{'A': 5}` and leaves `d` intact. But NO repo call site ever aliases the two arguments: all eight sites (sessions.py:78, 291-293, 377-380) pass a per-request value and a distinct per-session attribute (`request.headers`/`self.headers`, `proxies`/`self.proxies`, ...).

So the admitted latitude is UNREACHABLE in the repo and cannot make a faithful patch fail. Worth recording as a soundness margin (a `Requires(session is not request)`, or stating (1)/(2) over `Old(...)`, would close it), but on the G-EQ criterion -- a verifying impl whose faithful patch does not resolve -- it is NOT a counterexample, and I am reporting the executed resolve result rather than speculating.

### REFINEMENT.MD LEG AUDIT (the A legs, as instructed; R/I legs are G-CONF's remit).
Leg-kind tally: 3x R + 1x A-reference (A3) + 0 A-consumed + 0 kind-3. Section B's "no kind-3" claim CONFIRMED: the one genuinely CHANGED operation (drop every key whose effective value is None) is modelled DEEPLY in the pure region and consumed by the verified loop; there is no @ContractOnly declaration anywhere in model.py, hence no assumed Ensures the proof leans on. atk_12 is the empirical confirmation that this deep modelling is not a hidden oracle: echoing `combined` directly yields a CORRECT impl whose patch resolves. A1 (R): `session, request: List[int]` over key positions <-> the two dicts. HOLDS.

The `Acc(...,1/2)` read-only framing matches the real callee (merge_setting mutates only its own `merged_setting`, never its arguments) -- with the aliasing caveat above, which is a margin in the MODEL's framing, not a mismatch with the repo. A2 (R): `effective(sv, rv) = rv if rv != absent() else sv` <-> `dict_class(to_key_val_list(session_setting)); .update(to_key_val_list(request_setting))`. HOLDS -- re-derived by EXECUTING the real `to_key_val_list` + `OrderedDict.update` from the base_commit tree ($D/aleg.py): request-wins on shared keys, and `merged_setting[k]` IS the effective value, so keying the drop off `merged_setting[k]` is keying it off `effective`, exactly as A3 claims.

A3 (A-REFERENCE, the sole out-of-band trust point): `combined` <-> the full dict-merge branch INCLUDING the gold drop. CORRESPONDENCE HOLDS, independently re-derived rather than taken from axiom_check.py. $D/aleg.py drives the REAL base_commit machinery with only the final drop line controlled, over the full 4-class grid {absent, unset, 1, 7} x lengths 0..3 = 4369 pairs: GOLD state vs the deep model `combined` = 0 disagreements; BUGGY (base_commit) state vs `combined` = 753 disagreements, concentrated in EXACTLY ONE per-key shape, (sv=unset, rv=absent) -> buggy keeps unset where the model requires absent. That is precisely the F2P shape (a session-side None header), so the observable genuinely discriminates fixed from buggy (G-DIFF).

I also CONFIRMED the load-bearing premise of axiom_check.py's two-state design: the ambient tree at base_commit does NOT contain the gold drop line, so refusing to trust the ambient drop is necessary, not decorative -- mapping.md S3.1's "PATCH-STATE control" claim is accurate. A4 (R): `result` (no position holding none_val()) <-> the returned dict (no key mapping to None); an absent position <-> the key absent. HOLDS; the F2P assertion is `'Accept-Encoding' not in prep.headers`, i.e. exactly key-absence.

Section C ("verify(model) => resolved"): the prior pass's recorded DEFECT here -- that C reasons purely extensionally and never discharges a termination/totality leg -- has been REPAIRED IN THE SPEC, and I confirmed the repair empirically: the frozen model now carries `Requires(MustTerminate(2))` at the METHOD level plus `Invariant(MustTerminate(n - i + 1))` on the loop, the gold impl still verifies (pos_control), and all THREE divergence encodings (plain self-call, measure-guarded self-call, literal inner spin) are now REJECTED. Residual DOCUMENTATION gap, not a soundness gap: refinement.md and mapping.md still never mention termination/totality anywhere (grep: 0 hits), so Section C's chain reads as extensional even though the frozen spec now obliges delivery. Recommend one sentence in Section C citing the method-level MustTerminate as the totality leg, so the document matches the artifact it maps. That is a docs nit; it changes no machine-checked outcome.

**No attack timed out or crashed:** every one of the 15 runs returned a definite exit 0 or exit 2 (no "inconclusive" summaries), and all three resolves returned completed=True on their FIRST attempt with zero PASS_TO_FAIL. The pipeline was demonstrably healthy in the same window that produced the three resolves.

**NOT A RUBBER STAMP:** 10 of 13 attacks were correctly REJECTED by the spec (the prepatch bug, a partial-domain drop, a corrupted precedence merge, a boundary off-by-one, reversed precedence, an over-drop, an illegal input write, and THREE distinct non-termination encodings including a measure-respecting one), and the 3 that verified are all behaviourally correct on every input the repo can actually reach -- each confirmed by an EXECUTED harness resolve, not by speculation. I attempted genuine falsification of the prior pass's finding and it no longer reproduces; the spec's repair is real.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1_selfcall_plain.py`, `atk_2_selfcall_measure_guarded.py`, `atk_3_spin_targeted.py`, `atk_4_prepatch.py`, `atk_5_partial_domain.py`, `atk_6_boundary_offbyone.py`, `atk_7_reversed_precedence.py`, `atk_8_none_as_absent.py`, `atk_9_overdrop.py`, `atk_10_mutate_session.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_11_echo_oracle.py`, `atk_12_pure_echo.py`, `atk_13_alias_mutate.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_selfcall_plain.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_selfcall_measure_guarded.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_spin_targeted.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_prepatch.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_partial_domain.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_boundary_offbyone.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_reversed_precedence.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_none_as_absent.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_overdrop.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_mutate_session.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_echo_oracle.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12_pure_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13_alias_mutate.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for psf__requests-1921.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Two collections of per-key settings are combined into one effective
  collection for a single use. The per-request collection takes precedence over
  the standing per-session collection: where both provide a key, the
  per-request value wins; where only one provides it, that one is used.

  A key may be given the distinguished "unset" value to mean "do not carry this
  key into the effective collection at all". The behaviour that matters: a key
  whose EFFECTIVE value (after precedence) is the unset value must be ABSENT
  from the combined collection -- regardless of WHICH side contributed that
  unset value. In particular a key carried only by the standing per-session
  collection and given the unset value there (never mentioned by the per-request
  collection) must be dropped, not carried through still holding the unset
  value. Every key whose effective value is a real (non-unset) value is carried
  through with exactly that value.

  Consequently the combined collection contains no key mapping to the unset
  value: looking up any key either yields a real value or finds the key absent.

  Combining always COMPLETES: for every admissible pair of collections the
  combination delivers the collection described above after finitely many
  steps. A computation that never delivers one has not met the guarantees --
  they are claims about a result that is actually produced.

Modelling choices (Nagini fragment):
  * Each collection is modelled as a ``List[int]`` indexed by key position: the
    universe of keys is the index set ``0 .. n-1``, common to both inputs and
    the output, and position ``k`` carries the value held for key ``k``. Only
    membership ("is key k carried, and with what value") is observed, so integer
    identity is the faithful carrier (mapping.md S2); string keys are irrelevant
    to the tested behaviour and are banned from indexing in Nagini anyway.
  * Two distinguished values: ``ABSENT`` means "key not carried by this
    collection / dropped from the result", and ``NONE_VAL`` means "the explicit
    unset value a caller may store under a key". Any other (real) value is an
    ordinary setting. ``NONE_VAL`` is modelled as a value distinct from
    ``ABSENT`` precisely so that a key explicitly set to the unset value is
    distinguishable from a key that was simply never provided -- the
    distinction the behaviour under specification turns on.
  * The two inputs are read only (held at fractional permission, required and
    ensured); the output collection is freshly built and fully owned. No string
    indexing is used (Nagini bans it).
  * Delivery of a result is an obligation of the contract, not an assumption:
    the method carries ``MustTerminate``, so the postconditions are guarantees
    about a collection that is handed back. The decreasing measure that
    discharges it for THIS body lives in the (elided) impl region, so any other
    implementation supplies whatever measure its own control flow needs.

The behaviour is modelled deeply (the precedence merge and the unset-value drop
are spelled out in the impl region); there is no axiomatised callee. Markers
(machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# No axioms: combining two key/value collections with precedence and dropping
# keys whose effective value is the unset value is the behaviour under
# specification and is spelled out deeply in the impl region. There is no
# unchanged opaque callee to axiomatise.
# axioms-end

# pure-start
@Pure
def absent() -> int:
    # The distinguished value meaning "key not carried by this collection" (an
    # input position) / "key dropped from the combined collection" (an output
    # position): a lookup finds the key absent.
    return 0

@Pure
def none_val() -> int:
    # The distinguished explicit "unset" value a caller may store under a key.
    # A key whose effective value is this must be dropped from the result.
    return -1

@Pure
def effective(sv: int, rv: int) -> int:
    # The effective value for a key before the unset-drop: the per-request value
    # wins where the per-request collection carries the key (rv != absent()),
    # otherwise the standing per-session value is used.
    if rv != absent():
        return rv
    return sv

@Pure
def combined(sv: int, rv: int) -> int:
    # The value the combined collection holds for a key: the effective value,
    # except that an effective value equal to the unset value drops the key
    # (it becomes absent). This is the per-key behaviour the result must realise.
    if effective(sv, rv) == none_val():
        return absent()
    return effective(sv, rv)
# pure-end

def effective_collection(session: List[int], request: List[int],
                         n: int) -> List[int]:
    # pre-conditions-start
    # The two input collections are read only: fractional permission.
    Requires(Acc(list_pred(session), 1 / 2))
    Requires(Acc(list_pred(request), 1 / 2))
    # The shared key universe is positions 0 .. n-1.
    Requires(0 <= n and n <= len(session) and n <= len(request))
    # Combining is obliged to COMPLETE and hand back a collection: on every
    # admissible input the guarantees below are owed about a result that is
    # actually delivered, so a computation that never delivers one does not
    # satisfy them. (MustTerminate in a Requires transfers the obligation TO
    # this operation; it does not shrink the set of admissible inputs.)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # Inputs unchanged (returned at the same fractional permission).
    Ensures(Acc(list_pred(session), 1 / 2))
    Ensures(Acc(list_pred(request), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The combined collection spans the same key universe.
    Ensures(len(Result()) == n)
    # The key universe still fits inside both inputs (carried so the per-key
    # reads below are in bounds).
    Ensures(n <= len(session) and n <= len(request))
    # (1) Faithful precedence-merge-and-drop: position k of the result is the
    #     per-key combined value -- the per-request value where present else the
    #     per-session value, dropped to absent when that effective value is the
    #     unset value.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < n and
        k < len(session) and k < len(request),
        Result()[k] == combined(session[k], request[k])),
        [[Result()[k]]])))
    # (2) The headline guarantee: no key in the combined collection maps to the
    #     unset value -- every lookup yields a real value or finds the key
    #     absent. This is the clause a drop that only inspects the per-request
    #     side (leaving a session-side unset value in place) violates.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < n,
        Result()[k] != none_val()),
        [[Result()[k]]])))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(session), 1 / 2))
        Invariant(Acc(list_pred(request), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(n <= len(session) and n <= len(request))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and
            k < len(session) and k < len(request),
            result[k] == combined(session[k], request[k])),
            [[result[k]]])))
        # One key of the universe is settled per step, so the number of keys
        # still to settle strictly decreases: this body's measure for the
        # delivery obligation the contract states.
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        sv = session[i]
        rv = request[i]
        # Precedence: the per-request value wins where the per-request
        # collection carries the key, else the per-session value.
        if rv != absent():
            ev = rv
        else:
            ev = sv
        Assert(ev == effective(sv, rv))
        # Drop the key (absent) when its effective value is the unset value,
        # regardless of which side contributed it; otherwise carry it through.
        if ev == none_val():
            val = absent()
        else:
            val = ev
        Assert(val == combined(sv, rv))
        old_result = result
        result = result + [val]
        Assert(len(result) == len(old_result) + 1)
        Assert(result[i] == val)
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(old_result),
            result[k] == old_result[k]), [[result[k]]])))
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) adversarial audit of psf__requests-1921/nagini. VERDICT: SOUND. 13 same-spec attacks + positive control + 1 vacuity control, all machine-run; 3 CANDIDATES materialized as faithful patches and ALL THREE RESOLVED under the official harness. No verifying wrong impl found.

Every attack built by copying the frozen model.py to frozen_model.py and replacing ONLY the text between `# impl-start`/`# impl-end` (builders mk.py / mk2.py); axioms / @Pure / Requires / Ensures byte-identical. All 14 files confirmed `same-spec` = SAME.

### EXACT COMMANDS (repo root swe-proof; D=the scratch dir):
  python -m swebench_unified.adversary same-spec nagini psf__requests-1921 $D/<f>.py   [all -> SAME]
  python -m swebench_unified.adversary weakness  nagini psf__requests-1921 $D/<f>.py   [via $D/wk.sh <name>]
  bash scripts/nagini_verify.sh $D/atk_2_selfcall_measure_guarded.py                  [to capture the rejection reason]
  SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=benchmark-verified python $D/resolve.py $D/patch_atk_<N>.diff 3600   [calls harness.run_resolve]
Attack verifications were run 3-concurrent as background jobs (each Nagini check spawns JVM+Z3); every attack was fully verified and reported.

### PER-ATTACK RESULTS (path / weakness exit / resolve):
pos_control.py                     POSITIVE CONTROL -> CANDIDATE (verifies, 20.8s). The frozen gold impl verifies, so the MustTerminate obligation costs it nothing. atk_1_selfcall_plain.py            REJECTED (exit 2) -- NON-TERMINATION: unbounded self-call `return effective_collection(session, request, n)` on the key whose EFFECTIVE value is the unset value (the exact F2P shape). This is the PRIOR PASS'S counterexample, re-encoded from scratch: it NO LONGER VERIFIES. The MustTerminate repair landed and holds. atk_2_selfcall_measure_guarded.py  REJECTED (exit 2) -- NEW, sharper divergence probe the prior pass never tried: a MEASURE-RESPECTING guarded self-call (guard `ev == none_val() and i + 2 < n`, so the loop measure n-i+1 >= 4 strictly exceeds the callee's MustTerminate(2)).

Direct verify names the reason: "Obligation leak check failed. Callee effective_collection might not take all unsatisfied obligations from the caller." ($D/vfy_atk_2.log). So the obligation is not merely a measure-ordering accident -- Nagini closes the self-call channel regardless of the guard's measure. atk_3_spin_targeted.py             REJECTED (exit 2) -- NON-TERMINATION via a literal inner `while spin >= 0` spin on the F2P key shape (no MustTerminate invariant available for it). atk_4_prepatch.py                  REJECTED (exit 2) -- THE DOCUMENTED PREPATCH BUG re-encoded: drop keyed off `rv == none_val()` (per-request side only), so a session-only unset value survives holding none_val().

PREPATCH REPRODUCED = True. atk_5_partial_domain.py            REJECTED (exit 2) -- PARTIAL DOMAIN: drops only when the SESSION side supplied the unset value (`ev == none_val() and rv == absent()`), carrying a request-side unset value through as none_val(). atk_6_boundary_offbyone.py         REJECTED (exit 2) -- BOUNDARY: loops to n-1 and pads the last position with absent(), so the last key of the universe is never combined. atk_7_reversed_precedence.py       REJECTED (exit 2) -- the SESSION side wins instead of the request side. atk_8_none_as_absent.py            REJECTED (exit 2) -- treats the unset value as "absent" DURING the precedence merge (`rv != absent() and rv != none_val()`), so a request-side unset value fails to override a real session value.

A distinct wrong impl from atk_5: it corrupts `effective`, not the drop. atk_9_overdrop.py                  REJECTED (exit 2) -- OVER-DROP: also drops the perfectly real value 7. Confirms the spec pins the positive direction (real values carried through EXACTLY), not just the drop. atk_10_mutate_session.py           REJECTED (exit 2) -- CONTROL-FLOW EFFECT: writes `session[i] = absent()` on the read-only input. Correctly rejected on the 1/2 fractional permission (no write permission when the two args are distinct objects). atk_11_echo_oracle.py              CANDIDATE (exit 0) -> patch RESOLVED (resolved=True, completed=True, attempts=1, 6/6 F2P, 106/106 P2P, 0 P2F).

CORRECT restructuring in the gold's own shape (build the full precedence merge, then a SEPARATE sweep dropping every unset value). Correctly NOT a weakness -- the separating control. atk_12_pure_echo.py                CANDIDATE (exit 0) -> patch RESOLVED (resolved=True, completed=True, attempts=1, 6/6 F2P, 106/106 P2P). UNGROUNDED-ORACLE ECHO lane: the impl region is literally `val = combined(session[i], request[i])`, i.e. the @Pure spec function applied directly. It verifies, and BECAUSE the behaviour is modelled DEEPLY (no @ContractOnly axiom -- `combined` is spelled out in the pure region and G-AX validates it == the real op), the echo is a genuinely CORRECT impl, and its faithful patch resolves.

This is the key negative result for the A-reference: echoing the oracle here buys no unearned latitude, which is exactly what a deep model (as opposed to an assumed Ensures) should give. atk_13_alias_mutate.py             CANDIDATE (exit 0) -> patch RESOLVED (resolved=True, completed=True, attempts=1, 6/6 F2P, 106/106 P2P). See the ALIASING finding below -- real latitude in the spec, but not a G-EQ break.

**VACUITY CONTROL:** ctl_13_vacuity.py = atk_13 + `Assert(False)` at the top of the `session is request` branch -> DOES NOT VERIFY (exit 2), so atk_13's guarded path is FEASIBLE and it does not verify by way of an infeasible guard.

THE ONE REAL PIECE OF SPEC LATITUDE I FOUND (atk_13), and why it is NOT a break. The two inputs are held at `Acc(list_pred(session), 1/2)` and `Acc(list_pred(request), 1/2)`. When the caller passes the SAME object for both, those fractions SUM TO FULL permission, so a same-spec impl may WRITE the caller's collection; and postconditions (1)/(2) read `session[k]`/`request[k]` in the POST state with no `Old(...)`, so an impl that first zeroes the aliased input to all-absent() and then returns all-absent() is trivially self-consistent w.r.t. the post-state values while destroying the caller's data and returning garbage w.r.t. the PRE state. atk_13 does exactly that and VERIFIES.

I materialized the faithful patch ($D/patch_atk_13.diff: `if request_setting is session_setting: session_setting.clear(); return dict_class()`, plus the gold drop for the non-aliased path) and RAN IT: it RESOLVES, 6/6 F2P, 106/106 P2P. Measured why ($D/behav.py, against the real base_commit tree): the patch is 0/4369 divergent from GOLD on distinct objects, and diverges ONLY on the aliased call -- `merge_setting(d, d)` returns `{}` and wipes the caller's `d`, where gold returns `{'A': 5}` and leaves `d` intact. But NO repo call site ever aliases the two arguments: all eight sites (sessions.py:78, 291-293, 377-380) pass a per-request value and a distinct per-session attribute (`request.headers`/`self.headers`, `proxies`/`self.proxies`, ...).

So the admitted latitude is UNREACHABLE in the repo and cannot make a faithful patch fail. Worth recording as a soundness margin (a `Requires(session is not request)`, or stating (1)/(2) over `Old(...)`, would close it), but on the G-EQ criterion -- a verifying impl whose faithful patch does not resolve -- it is NOT a counterexample, and I am reporting the executed resolve result rather than speculating.

### REFINEMENT.MD LEG AUDIT (the A legs, as instructed; R/I legs are G-CONF's remit).
Leg-kind tally: 3x R + 1x A-reference (A3) + 0 A-consumed + 0 kind-3. Section B's "no kind-3" claim CONFIRMED: the one genuinely CHANGED operation (drop every key whose effective value is None) is modelled DEEPLY in the pure region and consumed by the verified loop; there is no @ContractOnly declaration anywhere in model.py, hence no assumed Ensures the proof leans on. atk_12 is the empirical confirmation that this deep modelling is not a hidden oracle: echoing `combined` directly yields a CORRECT impl whose patch resolves. A1 (R): `session, request: List[int]` over key positions <-> the two dicts. HOLDS.

The `Acc(...,1/2)` read-only framing matches the real callee (merge_setting mutates only its own `merged_setting`, never its arguments) -- with the aliasing caveat above, which is a margin in the MODEL's framing, not a mismatch with the repo. A2 (R): `effective(sv, rv) = rv if rv != absent() else sv` <-> `dict_class(to_key_val_list(session_setting)); .update(to_key_val_list(request_setting))`. HOLDS -- re-derived by EXECUTING the real `to_key_val_list` + `OrderedDict.update` from the base_commit tree ($D/aleg.py): request-wins on shared keys, and `merged_setting[k]` IS the effective value, so keying the drop off `merged_setting[k]` is keying it off `effective`, exactly as A3 claims.

A3 (A-REFERENCE, the sole out-of-band trust point): `combined` <-> the full dict-merge branch INCLUDING the gold drop. CORRESPONDENCE HOLDS, independently re-derived rather than taken from axiom_check.py. $D/aleg.py drives the REAL base_commit machinery with only the final drop line controlled, over the full 4-class grid {absent, unset, 1, 7} x lengths 0..3 = 4369 pairs: GOLD state vs the deep model `combined` = 0 disagreements; BUGGY (base_commit) state vs `combined` = 753 disagreements, concentrated in EXACTLY ONE per-key shape, (sv=unset, rv=absent) -> buggy keeps unset where the model requires absent. That is precisely the F2P shape (a session-side None header), so the observable genuinely discriminates fixed from buggy (G-DIFF).

I also CONFIRMED the load-bearing premise of axiom_check.py's two-state design: the ambient tree at base_commit does NOT contain the gold drop line, so refusing to trust the ambient drop is necessary, not decorative -- mapping.md S3.1's "PATCH-STATE control" claim is accurate. A4 (R): `result` (no position holding none_val()) <-> the returned dict (no key mapping to None); an absent position <-> the key absent. HOLDS; the F2P assertion is `'Accept-Encoding' not in prep.headers`, i.e. exactly key-absence.

Section C ("verify(model) => resolved"): the prior pass's recorded DEFECT here -- that C reasons purely extensionally and never discharges a termination/totality leg -- has been REPAIRED IN THE SPEC, and I confirmed the repair empirically: the frozen model now carries `Requires(MustTerminate(2))` at the METHOD level plus `Invariant(MustTerminate(n - i + 1))` on the loop, the gold impl still verifies (pos_control), and all THREE divergence encodings (plain self-call, measure-guarded self-call, literal inner spin) are now REJECTED. Residual DOCUMENTATION gap, not a soundness gap: refinement.md and mapping.md still never mention termination/totality anywhere (grep: 0 hits), so Section C's chain reads as extensional even though the frozen spec now obliges delivery. Recommend one sentence in Section C citing the method-level MustTerminate as the totality leg, so the document matches the artifact it maps. That is a docs nit; it changes no machine-checked outcome.

**No attack timed out or crashed:** every one of the 15 runs returned a definite exit 0 or exit 2 (no "inconclusive" summaries), and all three resolves returned completed=True on their FIRST attempt with zero PASS_TO_FAIL. The pipeline was demonstrably healthy in the same window that produced the three resolves.

**NOT A RUBBER STAMP:** 10 of 13 attacks were correctly REJECTED by the spec (the prepatch bug, a partial-domain drop, a corrupted precedence merge, a boundary off-by-one, reversed precedence, an over-drop, an illegal input write, and THREE distinct non-termination encodings including a measure-respecting one), and the 3 that verified are all behaviourally correct on every input the repo can actually reach -- each confirmed by an EXECUTED harness resolve, not by speculation. I attempted genuine falsification of the prior pass's finding and it no longer reproduces; the spec's repair is real.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** REFERENCE DISCIPLINE. Bundle contains no patch.diff; I pulled the gold patch verbatim from data/swe_bench_verified/test.jsonl (one hunk: `merged_setting = dict((k,v) for (k,v) in merged_setting.items() if v is not None)` inserted at requests/sessions.py:62) and built the reference as a fresh worktree of the upstream repository at base_commit 3c88e520 with that patch APPLIED (). A second unpatched worktree (*) was used ONLY as the falsifiability control, never as the reference.

**SPEC REGION INTEGRITY.** `adversary same-spec nagini psf__requests-1921` on a byte-copy of model.py => exit 0 ("SAME"). `bash scripts/nagini_verify.sh model.py` => "Verification successful" (22.75s), so the spec I audited is the one that verifies. meta.json region_hashes read; axioms == [] (no consumed @ContractOnly axiom — the merge-and-drop is modelled deeply, so there is no axiom that could be over-strong in the usual way).

**WHAT THE SPEC CLAIMS.** Post(1) Result()[k] == combined(session[k], request[k]) for k in 0..n-1, where combined = (request wins where rv != absent(); effective value of none_val() drops to absent()). Post(2) Result()[k] != none_val(). Plus len(Result()) == n, inputs returned at the same 1/2 permission, and MustTerminate(2).

INDEPENDENT PROBE (did NOT reuse the bundle's conformance_check.py bridge). atk1921_indep.py: my own to_repo/from_repo, real string header keys instead of str(0..n-1), **insertion order randomly shuffled per case** (so no accidental reliance on OrderedDict ordering), and it checks the POSTCONDITIONS directly rather than the impl shadow — the distinction that matters for a too-strong-spec attack. 99,905 inputs (exhaustive class grid length 0..4 over {absent, unset, 1, 7} + 30,000 fuzz with n strictly below both list lengths). Zero divergences. It also asserts no key outside 0..n-1 appears in the real result, and separately that the real merged dict literally holds no None.

**REAL-CALL-SITE TYPES.** sessions.py:293 calls merge_setting(request.headers, self.headers, dict_class=CaseInsensitiveDict) — NOT the OrderedDict the bundle's gate uses. I re-ran the grid under all four combinations (plaindict/OrderedDict, CID/CID, plaindict/CID, CID/OrderedDict): 4,369 inputs each, all OK. So the spec is faithful at the shape the F2P test actually exercises, not just at the gate's shape.

**NEGATIVE REALS.** The precondition admits ANY int as a real value while only -1 is none_val(); a spec keyed on `< 0` rather than `== -1` would be over-strong here. Grid over {0, -1, -2, -7, -100, 1, 7, 3}, 266,305 inputs, length 0..3: OK. `combined` genuinely keys on identity with none_val(), matching `v is not None`.

EDGE / BRANCH PROBES, and why each is out of carrier rather than a divergence:
  * merge_setting(None, X) and merge_setting(X, None) early-return X unmerged (so a session-side None SURVIVES: merge_setting(None,{'a':None}) -> {'a':None}). NOT reachable from the model: absent() means "key not in the dict", and the bridge maps an all-absent list to an EMPTY dict, never to the Python argument None. Confirmed merge_setting({}, {'a':None}) -> {} — the empty-dict case does drop, and that is the case the carrier produces. mapping.md and conformance_check.py both state this explicitly.
  * non-Mapping bypass (merge_setting('x','y') -> 'x', merge_setting(None,True) -> True): unreachable, both bridge outputs are always real dicts.
  * FALSY-but-not-None values (0, False, '', (), 0.0) all SURVIVE the gold drop (`v is not None`, not truthiness). Consistent with the model: absent()==0 is a carrier sentinel for "key not in the dict", not a modelled real value, so no admissible List[int] asks the spec about a stored 0.
  * CID case-collision at the real call site: ses['Accept-Encoding']='gzip' + req['accept-encoding']=None drops under dict_class=CaseInsensitiveDict but survives under OrderedDict; and a PLAIN dict {'a':None,'A':None} into dict_class=CaseInsensitiveDict raises KeyError('a') in the pre-existing del loop. Both are pre-existing case-folding behavior of the untouched del loop, reachable only when two distinct keys collide under .lower(); the model's key universe is distinct positions 0..n-1 (mapping.md §2 bans string keys and states keys are distinct), so this is outside the carrier by construction, not a spec over-claim. I used case-distinct key names (Aa/Bb, not a/A) so this never masked a real divergence.
  * Input non-mutation and non-aliasing: over the grid under both dict classes, neither argument dict is mutated and the result is never the same object as either argument. This backs the Ensures(Acc(..., 1/2)) read-only claim.

OBSERVATION, NOT A DEFECT. The gold patch replaces `merged_setting` with a plain `dict(...)`, so at the headers call site merge_setting returns a plain dict rather than the CaseInsensitiveDict the dict_class argument requested — case-insensitive lookup on merge_setting's direct return is lost. I checked whether this is an unmodelled behavior change the spec papers over, and it is not observable downstream: PreparedRequest.prepare_headers re-wraps into CaseInsensitiveDict (models.py:394), prep.headers is CaseInsensitiveDict, and the case-insensitivity P2P test passes on gold (test_header_remove_is_case_insensitive + test_headers_on_session_with_None_are_not_sent: 2 passed). mapping.md §2 declares result ordering/representation unobserved, which covers this. Recording it as a known non-divergence.

FALSIFIABILITY CONTROL (the load-bearing check that my probe is not vacuous). Both my independent probes were re-run unchanged against the UNPATCHED base worktree and FAILED immediately: session=[-1], request=[0], n=1 gives real=[-1] (key 'Accept-Encoding' still mapping to None) vs combined=[0] — violating BOTH post(1) and post(2). Identical failure under all four dict-class combinations. My harness therefore has the discriminating power to have caught an unfaithful spec, and its green result on the patched reference is evidence.

**GATE REPRODUCTION.** I re-ran the bundle's own axiom_check.py and conformance_check.py inside MY worktree (only a collections.abc shim prepended for py3.10): G-CONF exit 0 (109,921 inputs, 0 disagreements) and G-AX exit 0. Notably G-AX self-applies the gold drop rather than trusting the ambient tree and runs an explicit BUGGY-state control, so it is not tautological against the base checkout. F2P scenario reproduced end-to-end on the patched worktree: 'Accept-Encoding' not in prep.headers -> True.

**END-TO-END SANITY ON THE ATTACK DIRECTION.** A faithfulness break requires the spec to be strictly stronger than the real callee somewhere in the admissible domain. Every candidate I found where the real function does something the spec forbids (None-argument passthrough, non-Mapping bypass, falsy survival, CID case collision) is provably unreachable through the declared bridge, and I verified reachability rather than assuming it. The one operation the patch changed is modelled deeply, not axiomatised, so there is no hidden axiom carrying the fix.

**CONCLUSION:** FAITHFUL. No diverging input exists in the modeled domain; the spec is neither stronger nor weaker than the real post-patch merge_setting on the inputs the carrier can express.

**REFERENCE DISCIPLINE.** Bundle contains no patch.diff; I pulled the gold patch verbatim from data/swe_bench_verified/test.jsonl (one hunk: `merged_setting = dict((k,v) for (k,v) in merged_setting.items() if v is not None)` inserted at requests/sessions.py:62) and built the reference as a fresh worktree of the upstream repository at base_commit 3c88e520 with that patch APPLIED (). A second unpatched worktree (*) was used ONLY as the falsifiability control, never as the reference.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gate: leakage / gold-reconstruction on the CONSUMER SPEC VIEW of psf__requests-1921 (nagini). Judged against the solver-visible problem_statement ONLY; hints_text deliberately excluded from the baseline.

**SPEC VIEW RECONSTRUCTED INDEPENDENTLY.** markers.spec_view(model.py, nagini) rendered directly (impl region collapses to '...  # implementation elided'); sha256 = b2159665300437234e8ff9cae6bdfb5f2cd0fa34daca4900a71f80587f30d126. The whole surface I judged = module docstring + imports + axioms region (a no-axioms note) + pure region (absent/none_val/effective/combined) + pre-conditions + post-conditions. Invariants and impl are NOT in the view (confirmed: the invariants/impl region hashes differ between my render and the file, i.e. they are elided). same-spec on an identical copy returns exit 0, and markers.same_spec(model.py, model_prepatch.py) is True, so the spec view is the same frozen artifact both the solver and the G-DIFF prepatch rival see - no second leak surface.

GOLD EDIT (the thing that must NOT be reconstructible). One added line in requests/sessions.py, inside merge_setting: 'merged_setting = dict((k, v) for (k, v) in merged_setting.items() if v is not None)', placed after the existing per-request del loop. Changed symbol set = {merge_setting}; changed file = requests/sessions.py.

L1 (gold line / diff markers). Normalized gold line 'merged_setting=dict((k,v)for(k,v)inmerged_setting.items()ifvisnotNone)' does not occur in the normalized view. Zero occurrences in the view of: merged, dict, items(), OrderedDict, to_key_val_list, update, del <expr>, filter, comprehension. No diff marker (@@, diff --git, '+++ ', '--- ', index) present.

L2 (localization). No 'requests/sessions.py', no 'requests.sessions', no base_commit hash, no line numbers, no 'merge_setting' (nor any identifier embedding it). Spec-view identifier set is fully abstract: Acc, Ensures, Forall, Implies, List, MustTerminate, Pure, Requires, Result, absent, combined, effective, effective_collection, int, k, len, list_pred, n, none_val, request, rv, session, sv. Note the repo's real parameter names (session_setting / request_setting / merged_setting) are NOT used; the view uses bare 'session'/'request', which are problem-statement vocabulary ('session', "the method's arguments"). No F2P test name, no 'httpbin', no 'prepare_request', no 'Accept-Encoding', no 'headers'.

L3 (narration). No banned narration token fires (bug/fix/patch/pre-patch/regression/previously/incorrectly/wrong/broken). Everything is phrased as desired behaviour of a result, not as an edit or a diagnosis. Independent leakage.screen() on the real instance row returns passed=True with zero hard failures and zero warnings - my manual read agrees rather than merely deferring to it.

HINTS-ONLY VOCABULARY (the documented #1 failure mode). Diffed the >=4-char word sets: hints-only words that do appear in the view are ['about','above','actually','before','behaviour','merge','request','unset','with'] - all generic English or PS-derived. 'merge' appears twice ('the precedence merge', 'Faithful precedence-merge-and-drop'); it names the abstract combine operation, not the repo function merge_setting, and merging session defaults with per-call arguments is exactly what the PS's cited docs describe. 'unset' is the model's own abstract term for the distinguished value; the PS itself establishes None-means-do-not-send. No hints-only DIAGNOSIS ('I think this is a bug in how we merge the headers before firing off a request') is echoed in mechanism form.

CLOSEST CALL, EXAMINED AND CLEARED. Two places restate the F2P scenario / rule out a wrong impl:

(a) docstring: 'a key carried only by the standing per-session collection and given the unset value there (never mentioned by the per-request collection) must be dropped, not carried through still holding the unset value.'

(b) post-condition (2) comment: 'This is the clause a drop that only inspects the per-request side (leaving a session-side unset value in place) violates.' Both are inside the public PS envelope. The PS states, publicly and in code: session.headers['Accept-Encoding'] = None yields 'Accept-Encoding: None' sent, while the same None in the method's arguments already suppresses the header. So 'per-request None already works / session-only None survives holding None' IS the public content, and (a) is a restatement of the demanded behaviour - required spec content, since dropping it would make the spec too weak.

(b) characterizes the REJECTED implementation, which is precisely the behaviour the PS reports as broken; it is a spec-strength justification, and the same 'this is the clause X violates' pattern is a house convention (django-11790:98, django-15569:151, sphinx-8459:124, django-14170:234). Decisively, (b) does not determine the edit. The gold fixes this by ADDING a trailing full-dict filter pass while leaving the per-request del loop intact; the spec view never says that, and the model's own elided impl uses a third shape entirely (a per-key inline branch on the effective value inside a forward fold). Nothing in the view distinguishes 'add a final pass' from 'widen the existing loop' from 'decide per key', and nothing points at merge_setting or sessions.py. Gold-reconstruction from the view alone is not possible beyond what the PS already hands over.

INSTANCE ID IN LINE 1. '\"\"\"Twin-artifact model for psf__requests-1921.' names the repo and issue number. This is corpus-wide convention (verified across benchmark-verified/*/nagini/model.py) and is the task's own identity - the consumer is already given the psf/requests worktree at base_commit and the problem statement. It reveals no edit content. Recorded as an observation, not a finding.

OUT-OF-SCOPE OBSERVATION (not this gate, no action taken). meta.json region_hashes for invariants/impl/pre-conditions/spec_view disagree with a fresh markers.region_hashes() render; the same disagreement holds for 36 of the first 40 verified bundles, so it is a corpus-wide hashing-convention artifact rather than drift in this bundle. It does not touch leakage: I judged the freshly rendered view, not a recorded hash. Also noted that meta records G-PANEL-1=fail (spec-strength lane) - orthogonal to leakage and not re-litigated here.

**CONCLUSION:** the spec view states the abstract desired behaviour (precedence merge; a key whose EFFECTIVE value is the unset value is absent from the result, whichever side supplied it) without quoting the gold line, naming the patched file/module/function, echoing a patched repo symbol in any identifier or comment, or narrating the fix mechanism. NO-LEAKAGE.

**Gate:** leakage / gold-reconstruction on the CONSUMER SPEC VIEW of psf__requests-1921 (nagini). Judged against the solver-visible problem_statement ONLY; hints_text deliberately excluded from the baseline.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
