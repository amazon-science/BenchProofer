# P2 adversarial audit — sympy__sympy-23534

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -160,7 +160,7 @@
         # invariants-end
         nonneg_at(ToSeq(names), i)
         sub = expand_entry(cls, names[i])
-        grp = ToSeq(sub)  # type: PSeq[int]
+        grp = PSeq(cls)  # type: PSeq[int]  # FLAT one-per-entry
         old = res
         res = res + PSeq(grp)
         Assert(len(res) == i + 1)
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -148,7 +148,7 @@
     # impl-start
     res = PSeq()  # type: PSeq[PSeq[int]]
     i = 0
-    while i < len(names):
+    while i < len(names) - 1:
         # invariants-start
         Invariant(Acc(list_pred(names), 1 / 2))
         Invariant(all_nonneg(ToSeq(names)))
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -116,7 +116,7 @@
         Invariant(all_tag(ToSeq(out), cls))
         # invariants-end
         old = ToSeq(out)
-        out.append(cls)
+        out.append(cls + 1)  # WRONG tag
         Assert(ToSeq(out) == old + PSeq(cls))
         all_tag_concat(old, PSeq(cls), cls)
         i = i + 1
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -108,7 +108,7 @@
     # impl-start
     out = []  # type: List[int]
     i = 0
-    while i < n:
+    while i < n + 1:
         # invariants-start
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= n)
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -159,8 +159,25 @@
                 [[res[k]]])))
         # invariants-end
         nonneg_at(ToSeq(names), i)
-        sub = expand_entry(cls, names[i])
-        grp = ToSeq(sub)  # type: PSeq[int]
+        grp = PSeq()  # type: PSeq[int]  # ECHO: inline expansion, same result
+        j = 0
+        while j < names[i]:
+            Invariant(Acc(list_pred(names), 1 / 2))
+            Invariant(all_nonneg(ToSeq(names)))
+            Invariant(0 <= i and i < len(names))
+            Invariant(0 <= j and j <= names[i])
+            Invariant(len(grp) == j)
+            Invariant(all_tag(grp, cls))
+            Invariant(len(res) == i)
+            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(res),
+                    len(res[k]) == names[k] and all_tag(res[k], cls)),
+                    [[res[k]]])))
+            oldg = grp
+            grp = grp + PSeq(cls)
+            all_tag_concat(oldg, PSeq(cls), cls)
+            j = j + 1
+        Assert(len(grp) == names[i])
+        Assert(all_tag(grp, cls))
         old = res
         res = res + PSeq(grp)
         Assert(len(res) == i + 1)
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -162,7 +162,7 @@
         sub = expand_entry(cls, names[i])
         grp = ToSeq(sub)  # type: PSeq[int]
         old = res
-        res = res + PSeq(grp)
+        res = PSeq(grp) + res  # REVERSED order
         Assert(len(res) == i + 1)
         Assert(res[i] == grp)
         Assert(Forall(int, lambda k: (Implies(0 <= k and k < i, res[k] == old[k]), [[res[k]]])))
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -116,7 +116,10 @@
         Invariant(all_tag(ToSeq(out), cls))
         # invariants-end
         old = ToSeq(out)
-        out.append(cls)
+        if n > 1:
+            out.append(cls)
+        else:
+            out.append(DEFAULT_CLS())  # PARTIAL DOMAIN: wrong tag for small entries
         Assert(ToSeq(out) == old + PSeq(cls))
         all_tag_concat(old, PSeq(cls), cls)
         i = i + 1
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-23534.

Behaviour under specification (stated as desired behaviour, not as an edit):

  The factory that turns names into symbol-like objects accepts a requested
  output class. When it is given a *container* of entries (rather than a single
  delimited name string), it processes each entry of the container in turn and
  returns the results *grouped per entry*, in the same order: the k-th group of
  the output is the expansion of the k-th input entry, and the number of groups
  equals the number of entries. The requested output class must be honoured for
  *every* produced object: the class chosen by the caller propagates unchanged
  into the processing of each contained entry. No produced object may silently
  fall back to the factory's default class.

Each entry of the container expands to zero or more objects (an entry may
expand to several objects, e.g. a range entry; an empty range to none). The
per-entry multiplicity is a property of the entry and is preserved in its
group. The observable property tested here is the CLASS of each produced object
together with the grouped shape; the textual content of a name is irrelevant to
it, so a name is abstracted to an opaque token carrying only its expansion
multiplicity, and the touched field of a produced object is modelled as an
integer *class tag*. The default class is the tag DEFAULT_CLS; a caller may
request any other tag.

`expand_entry` carries the per-entry processing (which is not what differs
here); `symbols_on_sequence` is the container-handling that must forward the
requested class into every entry and keep one group per entry.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no consumed axioms: the per-entry expansion is modelled deeply below)
# axioms-end


# pure-start
@Pure
def DEFAULT_CLS() -> int:
    """The factory's default output-class tag (used when no class is
    requested)."""
    return 0


@Pure
def all_tag(xs: PSeq[int], t: int) -> bool:
    """True iff every element of xs equals the class tag t. Front-recursive so
    a single unfold is available per concatenation step."""
    if len(xs) == 0:
        return True
    return xs[0] == t and all_tag(xs.drop(1), t)


@Pure
def all_nonneg(xs: PSeq[int]) -> bool:
    """True iff every element of xs is non-negative. Each entry token carries
    its expansion multiplicity (number of objects it produces), which is
    non-negative. Front-recursive."""
    if len(xs) == 0:
        return True
    return xs[0] >= 0 and all_nonneg(xs.drop(1))
# pure-end


def all_tag_concat(a: PSeq[int], b: PSeq[int], t: int) -> None:
    """Proof helper: all_tag distributes over concatenation (front fold)."""
    Requires(all_tag(a, t) and all_tag(b, t))
    Ensures(all_tag(a + b, t))
    if len(a) == 0:
        Assert(a + b == b)
    else:
        Assert((a + b).drop(1) == a.drop(1) + b)
        all_tag_concat(a.drop(1), b, t)


def nonneg_at(xs: PSeq[int], i: int) -> None:
    """Proof helper: extract the i-th element's non-negativity from all_nonneg
    (front fold)."""
    Requires(all_nonneg(xs))
    Requires(0 <= i and i < len(xs))
    Ensures(xs[i] >= 0)
    if i == 0:
        pass
    else:
        Assert(xs.drop(1)[i - 1] == xs[i])
        nonneg_at(xs.drop(1), i - 1)


def expand_entry(cls: int, n: int) -> List[int]:
    """Process a single container entry under the requested class `cls`,
    producing the `n` objects for that entry (its multiplicity). Every produced
    object carries class tag `cls` (the class the caller requested flows into
    the per-entry processing). Models the single-name branch of the factory,
    whose class handling the container path must preserve."""
    # pre-conditions-start
    Requires(n >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The entry expands to exactly its multiplicity many objects (zero or more) ...
    Ensures(len(Result()) == n)
    # ... and every produced object carries exactly the requested class tag.
    Ensures(all_tag(ToSeq(Result()), cls))
    # post-conditions-end
    # impl-start
    out = []  # type: List[int]
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= n)
        Invariant(len(out) == i)
        Invariant(all_tag(ToSeq(out), cls))
        # invariants-end
        old = ToSeq(out)
        out.append(cls)
        Assert(ToSeq(out) == old + PSeq(cls))
        all_tag_concat(old, PSeq(cls), cls)
        i = i + 1
    return out
    # impl-end


def symbols_on_sequence(names: List[int], cls: int) -> PSeq[PSeq[int]]:
    # pre-conditions-start
    # `names` is the read-only container of entries; the factory does not
    # mutate it. Each entry token carries its expansion multiplicity (>= 0).
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(all_nonneg(ToSeq(names)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(names), 1 / 2))
    # Exactly one group per container entry, in order (the grouped shape the
    # caller deconstructs by indexing into the per-entry groups).
    Ensures(len(Result()) == len(names))
    # For every entry: its group has exactly the entry's multiplicity of
    # objects, AND every object in that group carries the requested class tag
    # `cls` -- never the factory default. The class fact is the property the
    # F2P test observes; the per-group multiplicity is the grouped structure it
    # deconstructs.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(Result()),
            len(Result()[k]) == names[k] and all_tag(Result()[k], cls)),
            [[Result()[k]]])))
    # post-conditions-end
    # impl-start
    res = PSeq()  # type: PSeq[PSeq[int]]
    i = 0
    while i < len(names):
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(all_nonneg(ToSeq(names)))
        Invariant(0 <= i and i <= len(names))
        Invariant(len(res) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(res),
                len(res[k]) == names[k] and all_tag(res[k], cls)),
                [[res[k]]])))
        # invariants-end
        nonneg_at(ToSeq(names), i)
        sub = expand_entry(cls, names[i])
        grp = ToSeq(sub)  # type: PSeq[int]
        old = res
        res = res + PSeq(grp)
        Assert(len(res) == i + 1)
        Assert(res[i] == grp)
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i, res[k] == old[k]), [[res[k]]])))
        i = i + 1
    return res
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity) for sympy__sympy-23534. Focus: A-legs + model/patch correspondence (R/I legs mechanically covered by G-CONF). Scratch: Env: (adversary+harness); scripts/nagini_verify.sh for direct verify.

BASELINE — positive_control.py (=model.py): `same-spec` rc=0; `nagini_verify.sh` -> 'Verification successful' (12.5s). prepatch.py (=model_prepatch.py; passes DEFAULT_CLS() into per-entry expansion, mirroring the missing cls=cls): same-spec rc=0 and FAILS verify at line 157 'Loop invariant might not be preserved ... all_tag(res[k], cls)'. => prepatch_reproduced=TRUE; the spec senses the bug on exactly the gold-edited line.

SPEC STRUCTURE: spec_view elides ONLY the impl regions of expand_entry and symbols_on_sequence; axioms(none)/pure(DEFAULT_CLS,all_tag,all_nonneg)/pre/post frozen byte-identical (all 7 attacks same-spec rc=0). The postconditions FULLY DETERMINE the abstract output: symbols_on_sequence must return exactly len(names) groups, group k = [cls]*names[k]; expand_entry must return exactly [cls]*n. Any verifying impl is therefore abstractly identical to the gold, whose faithful transcription is the single gold line `symbols(name, cls=cls, **args)`.

### ATTACK BATTERY (all same-spec rc=0; cmd: `python -m swebench_unified.adversary weakness nagini sympy__sympy-23534 <path>`):
- atk_1.py (flat one-per-entry, grp=PSeq(cls) ignoring multiplicity): weakness rc=2; verify FAILS at 157 loop invariant Forall(len(res[k])==names[k] & all_tag). Spec rejects flat impl. (partial/structural)
- atk_2.py (off-by-one: while i<len(names)-1, drops last group): weakness rc=2; verify FAILS postcondition len(Result())==len(names) at 138. (boundary/grouping-count)
- atk_3.py (wrong tag: out.append(cls+1)): weakness rc=2; verify FAILS Assert ToSeq(out)==old+PSeq(cls) at 120. (ungrounded-oracle/class-tag)
- atk_4.py (over-count: while i<n+1 in expand_entry): weakness rc=2; verify FAILS loop invariant i<=n at 114. (boundary/multiplicity)
- atk_6.py (reversed group order: res=PSeq(grp)+res): weakness rc=2; verify FAILS Assert res[i]==grp at 167. (control-flow-effect/order)
- atk_7.py (partial-domain: forward cls only when n>1 else DEFAULT_CLS()): weakness rc=2; verify FAILS Assert ToSeq(out)==old+PSeq(cls) at 123. (partial-domain)
- atk_5.py (ECHO CANDIDATE — inlines the per-entry expansion loop instead of calling expand_entry, still forwarding cls; outer invariant carried through the inner loop + bridging asserts len(grp)==names[i], all_tag(grp,cls)): STRUCTURALLY DIFFERENT from model.py yet VERIFIES ('Verification successful', 12.5s) and is same-spec => weakness rc=0 CANDIDATE.

MANDATORY RESOLVE STEP: materialized atk_5's faithful refined patch (atk_5_faithful.patch) = the gold edit, since atk_5 forwards cls per entry => abstractly identical to gold. RAN it through the official harness: run_resolve('sympy__sympy-23534', patch, timeout=1800, retries=1) -> RESOLVED=True, NOTE='resolved' (log: resolve_atk5.log). The verifying candidate RESOLVES => NOT a verify-but-not-resolve break. No spec weakness found.

REFINEMENT.md AUDIT: all legs R (R1 container->List[int], R2 cls->tag, R-group grouped result->PSeq[PSeq[int]], R-class all_tag), A-reference (expand_entry == real single-name branch, G-AX/axiom_check.py), or I (I1 iterate, I2 proof lemmas). NO kind-3: the genuinely-changed operation (which class flows into per-entry processing) is modeled EXPLICITLY as the cls arg threaded into expand_entry — first arg forwarded, mirroring cls=cls — not hidden behind a @ContractOnly axiom. The A-reference correspondence to the real callee is sound and load-bearing (grouped structure NOT abstracted; F2P [0][0] pinned by len(Result())==len(names) & len(Result()[k])==names[k]). Null-range soundness (exact multiplicity, never len>0) documented and G-AX-exercised. axiom_check.py itself needs sympy at base_commit (mechanized by G-AX; meta records pass-with-gold/fail-at-base) — not re-run here as it is the G-AX gate's job; I confirmed the correspondence by inspection + the prepatch discriminator + the resolving echo candidate.

VERDICT: SOUND. 7 same-spec attacks run (6 rejected by the spec at meaningful sites: multiplicity, grouping count, order, class tag, partial-domain; 1 verifying echo candidate whose materialized faithful patch RESOLVED=True). No verifying wrong-impl whose faithful patch fails to resolve was found; verify does not admit an incorrect impl here.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-23534.

Behaviour under specification (stated as desired behaviour, not as an edit):

  The factory that turns names into symbol-like objects accepts a requested
  output class. When it is given a *container* of entries (rather than a single
  delimited name string), it processes each entry of the container in turn and
  returns the results *grouped per entry*, in the same order: the k-th group of
  the output is the expansion of the k-th input entry, and the number of groups
  equals the number of entries. The requested output class must be honoured for
  *every* produced object: the class chosen by the caller propagates unchanged
  into the processing of each contained entry. No produced object may silently
  fall back to the factory's default class.

Each entry of the container expands to zero or more objects (an entry may
expand to several objects, e.g. a range entry; an empty range to none). The
per-entry multiplicity is a property of the entry and is preserved in its
group. The observable property tested here is the CLASS of each produced object
together with the grouped shape; the textual content of a name is irrelevant to
it, so a name is abstracted to an opaque token carrying only its expansion
multiplicity, and the touched field of a produced object is modelled as an
integer *class tag*. The default class is the tag DEFAULT_CLS; a caller may
request any other tag.

`expand_entry` carries the per-entry processing (which is not what differs
here); `symbols_on_sequence` is the container-handling that must forward the
requested class into every entry and keep one group per entry.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no consumed axioms: the per-entry expansion is modelled deeply below)
# axioms-end


# pure-start
@Pure
def DEFAULT_CLS() -> int:
    """The factory's default output-class tag (used when no class is
    requested)."""
    return 0


@Pure
def all_tag(xs: PSeq[int], t: int) -> bool:
    """True iff every element of xs equals the class tag t. Front-recursive so
    a single unfold is available per concatenation step."""
    if len(xs) == 0:
        return True
    return xs[0] == t and all_tag(xs.drop(1), t)


@Pure
def all_nonneg(xs: PSeq[int]) -> bool:
    """True iff every element of xs is non-negative. Each entry token carries
    its expansion multiplicity (number of objects it produces), which is
    non-negative. Front-recursive."""
    if len(xs) == 0:
        return True
    return xs[0] >= 0 and all_nonneg(xs.drop(1))
# pure-end


def all_tag_concat(a: PSeq[int], b: PSeq[int], t: int) -> None:
    """Proof helper: all_tag distributes over concatenation (front fold)."""
    Requires(all_tag(a, t) and all_tag(b, t))
    Ensures(all_tag(a + b, t))
    if len(a) == 0:
        Assert(a + b == b)
    else:
        Assert((a + b).drop(1) == a.drop(1) + b)
        all_tag_concat(a.drop(1), b, t)


def nonneg_at(xs: PSeq[int], i: int) -> None:
    """Proof helper: extract the i-th element's non-negativity from all_nonneg
    (front fold)."""
    Requires(all_nonneg(xs))
    Requires(0 <= i and i < len(xs))
    Ensures(xs[i] >= 0)
    if i == 0:
        pass
    else:
        Assert(xs.drop(1)[i - 1] == xs[i])
        nonneg_at(xs.drop(1), i - 1)


def expand_entry(cls: int, n: int) -> List[int]:
    """Process a single container entry under the requested class `cls`,
    producing the `n` objects for that entry (its multiplicity). Every produced
    object carries class tag `cls` (the class the caller requested flows into
    the per-entry processing). Models the single-name branch of the factory,
    whose class handling the container path must preserve."""
    # pre-conditions-start
    Requires(n >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The entry expands to exactly its multiplicity many objects (zero or more) ...
    Ensures(len(Result()) == n)
    # ... and every produced object carries exactly the requested class tag.
    Ensures(all_tag(ToSeq(Result()), cls))
    # post-conditions-end
    # impl-start
    out = []  # type: List[int]
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= n)
        Invariant(len(out) == i)
        Invariant(all_tag(ToSeq(out), cls))
        # invariants-end
        old = ToSeq(out)
        out.append(cls)
        Assert(ToSeq(out) == old + PSeq(cls))
        all_tag_concat(old, PSeq(cls), cls)
        i = i + 1
    return out
    # impl-end


def symbols_on_sequence(names: List[int], cls: int) -> PSeq[PSeq[int]]:
    # pre-conditions-start
    # `names` is the read-only container of entries; the factory does not
    # mutate it. Each entry token carries its expansion multiplicity (>= 0).
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(all_nonneg(ToSeq(names)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(names), 1 / 2))
    # Exactly one group per container entry, in order (the grouped shape the
    # caller deconstructs by indexing into the per-entry groups).
    Ensures(len(Result()) == len(names))
    # For every entry: its group has exactly the entry's multiplicity of
    # objects, AND every object in that group carries the requested class tag
    # `cls` -- never the factory default. The class fact is the property the
    # F2P test observes; the per-group multiplicity is the grouped structure it
    # deconstructs.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(Result()),
            len(Result()[k]) == names[k] and all_tag(Result()[k], cls)),
            [[Result()[k]]])))
    # post-conditions-end
    # impl-start
    res = PSeq()  # type: PSeq[PSeq[int]]
    i = 0
    while i < len(names):
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(all_nonneg(ToSeq(names)))
        Invariant(0 <= i and i <= len(names))
        Invariant(len(res) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(res),
                len(res[k]) == names[k] and all_tag(res[k], cls)),
                [[res[k]]])))
        # invariants-end
        nonneg_at(ToSeq(names), i)
        sub = expand_entry(cls, names[i])
        grp = ToSeq(sub)  # type: PSeq[int]
        old = res
        res = res + PSeq(grp)
        Assert(len(res) == i + 1)
        Assert(res[i] == grp)
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i, res[k] == old[k]), [[res[k]]])))
        i = i + 1
    return res
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity) for sympy__sympy-23534. Focus: A-legs + model/patch correspondence (R/I legs mechanically covered by G-CONF). Scratch: Env: (adversary+harness); scripts/nagini_verify.sh for direct verify.

BASELINE — positive_control.py (=model.py): `same-spec` rc=0; `nagini_verify.sh` -> 'Verification successful' (12.5s). prepatch.py (=model_prepatch.py; passes DEFAULT_CLS() into per-entry expansion, mirroring the missing cls=cls): same-spec rc=0 and FAILS verify at line 157 'Loop invariant might not be preserved ... all_tag(res[k], cls)'. => prepatch_reproduced=TRUE; the spec senses the bug on exactly the gold-edited line.

SPEC STRUCTURE: spec_view elides ONLY the impl regions of expand_entry and symbols_on_sequence; axioms(none)/pure(DEFAULT_CLS,all_tag,all_nonneg)/pre/post frozen byte-identical (all 7 attacks same-spec rc=0). The postconditions FULLY DETERMINE the abstract output: symbols_on_sequence must return exactly len(names) groups, group k = [cls]*names[k]; expand_entry must return exactly [cls]*n. Any verifying impl is therefore abstractly identical to the gold, whose faithful transcription is the single gold line `symbols(name, cls=cls, **args)`.

### ATTACK BATTERY (all same-spec rc=0; cmd: `python -m swebench_unified.adversary weakness nagini sympy__sympy-23534 <path>`):
- atk_1.py (flat one-per-entry, grp=PSeq(cls) ignoring multiplicity): weakness rc=2; verify FAILS at 157 loop invariant Forall(len(res[k])==names[k] & all_tag). Spec rejects flat impl. (partial/structural)
- atk_2.py (off-by-one: while i<len(names)-1, drops last group): weakness rc=2; verify FAILS postcondition len(Result())==len(names) at 138. (boundary/grouping-count)
- atk_3.py (wrong tag: out.append(cls+1)): weakness rc=2; verify FAILS Assert ToSeq(out)==old+PSeq(cls) at 120. (ungrounded-oracle/class-tag)
- atk_4.py (over-count: while i<n+1 in expand_entry): weakness rc=2; verify FAILS loop invariant i<=n at 114. (boundary/multiplicity)
- atk_6.py (reversed group order: res=PSeq(grp)+res): weakness rc=2; verify FAILS Assert res[i]==grp at 167. (control-flow-effect/order)
- atk_7.py (partial-domain: forward cls only when n>1 else DEFAULT_CLS()): weakness rc=2; verify FAILS Assert ToSeq(out)==old+PSeq(cls) at 123. (partial-domain)
- atk_5.py (ECHO CANDIDATE — inlines the per-entry expansion loop instead of calling expand_entry, still forwarding cls; outer invariant carried through the inner loop + bridging asserts len(grp)==names[i], all_tag(grp,cls)): STRUCTURALLY DIFFERENT from model.py yet VERIFIES ('Verification successful', 12.5s) and is same-spec => weakness rc=0 CANDIDATE.

MANDATORY RESOLVE STEP: materialized atk_5's faithful refined patch (atk_5_faithful.patch) = the gold edit, since atk_5 forwards cls per entry => abstractly identical to gold. RAN it through the official harness: run_resolve('sympy__sympy-23534', patch, timeout=1800, retries=1) -> RESOLVED=True, NOTE='resolved' (log: resolve_atk5.log). The verifying candidate RESOLVES => NOT a verify-but-not-resolve break. No spec weakness found.

REFINEMENT.md AUDIT: all legs R (R1 container->List[int], R2 cls->tag, R-group grouped result->PSeq[PSeq[int]], R-class all_tag), A-reference (expand_entry == real single-name branch, G-AX/axiom_check.py), or I (I1 iterate, I2 proof lemmas). NO kind-3: the genuinely-changed operation (which class flows into per-entry processing) is modeled EXPLICITLY as the cls arg threaded into expand_entry — first arg forwarded, mirroring cls=cls — not hidden behind a @ContractOnly axiom. The A-reference correspondence to the real callee is sound and load-bearing (grouped structure NOT abstracted; F2P [0][0] pinned by len(Result())==len(names) & len(Result()[k])==names[k]). Null-range soundness (exact multiplicity, never len>0) documented and G-AX-exercised. axiom_check.py itself needs sympy at base_commit (mechanized by G-AX; meta records pass-with-gold/fail-at-base) — not re-run here as it is the G-AX gate's job; I confirmed the correspondence by inspection + the prepatch discriminator + the resolving echo candidate.

VERDICT: SOUND. 7 same-spec attacks run (6 rejected by the spec at meaningful sites: multiplicity, grouping count, order, class tag, partial-domain; 1 verifying echo candidate whose materialized faithful patch RESOLVED=True). No verifying wrong-impl whose faithful patch fails to resolve was found; verify does not admit an incorrect impl here.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check (spec-too-strong / drift from real repo behavior): FAITHFUL — no diverging input found. Modeled function = container else: branch of sympy.core.symbol.symbols (symbols_on_sequence models the loop; expand_entry is an A-reference deep-model of the recursive single-name branch). Gold fix forwards cls=cls; confirmed base (buggy) and patched worktrees under /tmp match mapping.md exactly. Spec region byte-identical (same-spec toolkit exit 0). Postconditions: (a) len(Result())==len(names) one-group-per-entry, (b) len(Result()[k])==names[k] per-entry multiplicity, (c) all_tag(Result()[k], cls) every leaf carries requested class tag. Verification: bundle G-CONF passes 100,052 inputs across 4 classes (Symbol/Function/Dummy/Wild); bundle G-AX passes 10 boundary + 300 fuzz. I additionally ran an INDEPENDENT differential oracle reimplementing model semantics and probed edge cases the bundle under-covers — nested tuple entries, empty container (), letter-paren ranges x(:c), escaped-comma x(:1\,:2), comma entries a,b, numeric double-range :3:2, double-paren x((a:b)) — all agree with the real patched callee. Domain restriction (excludes unordered set containers via Requires ordered List[int]+all_nonneg) is documented in mapping.md and is a sound narrowing, not drift. Null-range multiplicity=0 handled exactly (never over-claims >0), matching real callee (symbols('x:c',seq=True)==()). Multiplicity correctly modeled as class-independent. No input where the model disagrees with the real repo.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (rep.passed=True, no hard failures). Only distinctive patched symbol is 'literal' (the enclosing def in the gold hunk); it does NOT appear anywhere in the spec view (no identifier embeds it, no comment names it). Spec view is byte-identical to model.py's projected spec/pre/post regions with impl elided.

Gold edit: `result.append(symbols(name, cls=cls, **args))` — forwarding cls into the container branch. Public problem_statement already discloses the entire discriminating behavior: with an extra layer of parentheses (a container/tuple e.g. ('q:2','u:2')), cls=Function is silently dropped and objects come back as Symbol; and the extra parens are needed to deconstruct output as separate tuples.

The spec view states only DESIRED behavior fully entailed by that public report: (a) the requested output class must propagate unchanged into every contained entry, never falling back to the default; (b) the result is grouped one-group-per-entry preserving per-entry multiplicity. It uses abstracted names (symbols_on_sequence, expand_entry, integer class tag, DEFAULT_CLS), never names the patched symbol `literal`, never names `symbols`, quotes no gold line, contains no diff markers/file path/module path, and no bug/fix narration. The only public repo token used (`cls`) appears verbatim in the problem_statement (cls=smp.Function).

The artifacts that DO reproduce the gold hunk verbatim (refinement.md, mapping.md, patch.diff) are auditor/derivation artifacts, NOT part of the solver-visible spec view, so they are out of scope for G-PANEL-3. No line of the spec view reveals the edit location or fix specifics beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
