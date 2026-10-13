# P2 adversarial audit — django__django-13195

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 20 admissible attacks re-run of 20 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 20 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_11.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_16.py`, `atk_17.py`, `atk_18.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_9.py`, `atk_10.py`, `atk_12.py`, `atk_19.py`, `atk_20.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying same-spec impl was found whose faithful refined patch fails to resolve. Five impls VERIFY (atk_9 total setter bypass, atk_10 narrow bypass on the no-policy slice, atk_12 reach stripped on the falsey slice, atk_19 degraded oracle recognising the unrestricted policy by its first code point, atk_20 store misdirected to a scratch cookie with the caller's record written in place); all five had their faithful patches materialized, git-apply-checked at base_commit, and RUN through run_resolve: all five RESOLVED (completed=True, F2P 5/5, P2P 382/382, no PASS_TO_FAIL). They are genuinely-correct alternative implementations, not spec weaknesses. atk_19 is correct because under the frozen precondition Implies(len(policy)>0, is_known_policy(policy)) the only recognised tokens are none/lax/strict, so "first code point is n/N" and "is none, case-insensitively" coincide; a 9600-input gold-vs-candidate Set-Cookie header differential confirms 0/9600 divergences. atk_20 is correct because the spec is stated over what the EMITTED cookie carries, not over which callee was invoked; its 960/9600 divergences lie entirely inside the region mapping.md §2 DECLARES as the falsey-preimage abstraction (path='' / domain='' over a pre-existing seeded record), and no repo call site or graded test reaches it (all sites pass the '/' default or settings.SESSION_COOKIE_PATH / SESSION_COOKIE_DOMAIN).
```

**Attacks re-run (20):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -501,6 +501,10 @@
                     ToSeq(cookie.policy) == Old(ToSeq(cookie.policy))))
     # post-conditions-end
     # impl-start
-    secure = has_security_prefix(key) or is_none_ci(policy)
-    store_cookie(cookie, path, domain, secure, policy)
+    # ATTACK 1 (the prepatch bug, both legs): transport-secure from the
+    # reserved name prefix ALONE, and the cross-site policy value dropped
+    # instead of being forwarded onto the emitted expiry cookie.
+    secure = has_security_prefix(key)
+    dropped = []  # type: List[int]
+    store_cookie(cookie, path, domain, secure, dropped)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -501,6 +501,8 @@
                     ToSeq(cookie.policy) == Old(ToSeq(cookie.policy))))
     # post-conditions-end
     # impl-start
-    secure = has_security_prefix(key) or is_none_ci(policy)
+    # ATTACK 2 (uniqueness, secure leg only): forwarding is correct, but the
+    # unrestricted-policy disjunct is gone from the secure decision.
+    secure = has_security_prefix(key)
     store_cookie(cookie, path, domain, secure, policy)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -501,6 +501,8 @@
                     ToSeq(cookie.policy) == Old(ToSeq(cookie.policy))))
     # post-conditions-end
     # impl-start
-    secure = has_security_prefix(key) or is_none_ci(policy)
+    # ATTACK 3 (boundary / connective): conjunction instead of disjunction --
+    # secure only when the name carries a prefix AND the policy is 'none'.
+    secure = has_security_prefix(key) and is_none_ci(policy)
     store_cookie(cookie, path, domain, secure, policy)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -501,6 +501,11 @@
                     ToSeq(cookie.policy) == Old(ToSeq(cookie.policy))))
     # post-conditions-end
     # impl-start
-    secure = has_security_prefix(key) or is_none_ci(policy)
+    # ATTACK 4 (boundary, ASCII case fold dropped): the unrestricted policy is
+    # recognised only in its all-lower-case spelling, so 'None' / 'NONE' /
+    # 'nOnE' do not make the emitted expiry cookie transport-secure.
+    exact_none = (len(policy) == 4 and policy[0] == 110 and
+                  policy[1] == 111 and policy[2] == 110 and policy[3] == 101)
+    secure = has_security_prefix(key) or exact_none
     store_cookie(cookie, path, domain, secure, policy)
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -501,6 +501,10 @@
                     ToSeq(cookie.policy) == Old(ToSeq(cookie.policy))))
     # post-conditions-end
     # impl-start
-    secure = has_security_prefix(key) or is_none_ci(policy)
+    # ATTACK 5 (over-broad oracle): the emitted cookie is marked
+    # transport-secure for ANY recognised cross-site policy, not only the
+    # unrestricted one -- so a relaxed/restrictive expiry gains Secure it must
+    # not carry (and the flag can never be taken back off).
+    secure = has_security_prefix(key) or is_known_policy(policy)
     store_cookie(cookie, path, domain, secure, policy)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -501,6 +501,15 @@
                     ToSeq(cookie.policy) == Old(ToSeq(cookie.policy))))
     # post-conditions-end
     # impl-start
-    secure = has_security_prefix(key) or is_none_ci(policy)
-    store_cookie(cookie, path, domain, secure, policy)
+    # ATTACK 6 (partial domain + forged lifetime): where a cross-site policy
+    # value was supplied the routine goes through the attribute store, and
+    # where none was it stamps the already-elapsed lifetime and the flag
+    # directly instead -- emitting a cookie that reaches nowhere.
+    if len(policy) > 0:
+        secure = has_security_prefix(key) or is_none_ci(policy)
+        store_cookie(cookie, path, domain, secure, policy)
+    else:
+        cookie.expired = True
+        if has_security_prefix(key):
+            cookie.secure = True
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -501,6 +501,11 @@
                     ToSeq(cookie.policy) == Old(ToSeq(cookie.policy))))
     # post-conditions-end
     # impl-start
+    # ATTACK 7 (control-flow effect on the reach): the emitted expiry always
+    # applies to the site root and belongs to no particular host, whatever
+    # reach the caller asked for.
     secure = has_security_prefix(key) or is_none_ci(policy)
-    store_cookie(cookie, path, domain, secure, policy)
+    root = [47]  # type: List[int]
+    nohost = []  # type: List[int]
+    store_cookie(cookie, root, nohost, secure, policy)
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -501,6 +501,8 @@
                     ToSeq(cookie.policy) == Old(ToSeq(cookie.policy))))
     # post-conditions-end
     # impl-start
+    # ATTACK 8 (reach transposed): the request path is recorded as the host and
+    # the host as the request path.
     secure = has_security_prefix(key) or is_none_ci(policy)
-    store_cookie(cookie, path, domain, secure, policy)
+    store_cookie(cookie, domain, path, secure, policy)
     # impl-end
```

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -501,6 +501,50 @@
                     ToSeq(cookie.policy) == Old(ToSeq(cookie.policy))))
     # post-conditions-end
     # impl-start
-    secure = has_security_prefix(key) or is_none_ci(policy)
-    store_cookie(cookie, path, domain, secure, policy)
+    # ATTACK 9 (total setter bypass): the emitted cookie's whole footprint is
+    # written in place -- the already-elapsed lifetime and the transport-secure
+    # flag assigned directly, the policy and both reach values copied element
+    # by element -- with no invocation of the attribute store at all.
+    cookie.expired = True
+    if has_security_prefix(key) or is_none_ci(policy):
+        cookie.secure = True
+    if len(policy) > 0:
+        cpol = []  # type: List[int]
+        i_cpol = 0
+        while i_cpol < len(policy):
+            Invariant(Acc(list_pred(cpol)))
+            Invariant(Acc(list_pred(policy), 1 / 4))
+            Invariant(0 <= i_cpol and i_cpol <= len(policy))
+            Invariant(ToSeq(cpol) == ToSeq(policy).take(i_cpol))
+            Invariant(MustTerminate(len(policy) - i_cpol + 1))
+            cpol.append(policy[i_cpol])
+            i_cpol = i_cpol + 1
+        cookie.has_policy = True
+        cookie.policy = cpol
+    if len(path) > 0:
+        cpat = []  # type: List[int]
+        i_cpat = 0
+        while i_cpat < len(path):
+            Invariant(Acc(list_pred(cpat)))
+            Invariant(Acc(list_pred(path), 1 / 4))
+            Invariant(0 <= i_cpat and i_cpat <= len(path))
+            Invariant(ToSeq(cpat) == ToSeq(path).take(i_cpat))
+            Invariant(MustTerminate(len(path) - i_cpat + 1))
+            cpat.append(path[i_cpat])
+            i_cpat = i_cpat + 1
+        cookie.has_path = True
+        cookie.path = cpat
+    if len(domain) > 0:
+        cdom = []  # type: List[int]
+        i_cdom = 0
+        while i_cdom < len(domain):
+            Invariant(Acc(list_pred(cdom)))
+            Invariant(Acc(list_pred(domain), 1 / 4))
+            Invariant(0 <= i_cdom and i_cdom <= len(domain))
+            Invariant(ToSeq(cdom) == ToSeq(domain).take(i_cdom))
+            Invariant(MustTerminate(len(domain) - i_cdom + 1))
+            cdom.append(domain[i_cdom])
+            i_cdom = i_cdom + 1
+        cookie.has_domain = True
+        cookie.domain = cdom
     # impl-end
```

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -501,6 +501,40 @@
                     ToSeq(cookie.policy) == Old(ToSeq(cookie.policy))))
     # post-conditions-end
     # impl-start
-    secure = has_security_prefix(key) or is_none_ci(policy)
-    store_cookie(cookie, path, domain, secure, policy)
+    # ATTACK 10 (narrow setter bypass, reach preserved): the attribute store is
+    # invoked only where a cross-site policy value was supplied; on the plain
+    # default-expiry slice the whole footprint is written in place instead.
+    if len(policy) > 0:
+        secure = has_security_prefix(key) or is_none_ci(policy)
+        store_cookie(cookie, path, domain, secure, policy)
+    else:
+        cookie.expired = True
+        if has_security_prefix(key):
+            cookie.secure = True
+        if len(path) > 0:
+            cpat = []  # type: List[int]
+            i_cpat = 0
+            while i_cpat < len(path):
+                Invariant(Acc(list_pred(cpat)))
+                Invariant(Acc(list_pred(path), 1 / 4))
+                Invariant(0 <= i_cpat and i_cpat <= len(path))
+                Invariant(ToSeq(cpat) == ToSeq(path).take(i_cpat))
+                Invariant(MustTerminate(len(path) - i_cpat + 1))
+                cpat.append(path[i_cpat])
+                i_cpat = i_cpat + 1
+            cookie.has_path = True
+            cookie.path = cpat
+        if len(domain) > 0:
+            cdom = []  # type: List[int]
+            i_cdom = 0
+            while i_cdom < len(domain):
+                Invariant(Acc(list_pred(cdom)))
+                Invariant(Acc(list_pred(domain), 1 / 4))
+                Invariant(0 <= i_cdom and i_cdom <= len(domain))
+                Invariant(ToSeq(cdom) == ToSeq(domain).take(i_cdom))
+                Invariant(MustTerminate(len(domain) - i_cdom + 1))
+                cdom.append(domain[i_cdom])
+                i_cdom = i_cdom + 1
+            cookie.has_domain = True
+            cookie.domain = cdom
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -501,6 +501,14 @@
                     ToSeq(cookie.policy) == Old(ToSeq(cookie.policy))))
     # post-conditions-end
     # impl-start
+    # ATTACK 11 (control-flow effect): on the reserved-security-prefix slice the
+    # routine never gets round to emitting anything -- it spins forever instead
+    # of handing the browser an expiry.
+    if has_security_prefix(key):
+        i = 0
+        while i >= 0:
+            Invariant(i >= 0)
+            i = i + 1
     secure = has_security_prefix(key) or is_none_ci(policy)
     store_cookie(cookie, path, domain, secure, policy)
     # impl-end
```

Attack 12 — `atk_12.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -501,6 +501,17 @@
                     ToSeq(cookie.policy) == Old(ToSeq(cookie.policy))))
     # post-conditions-end
     # impl-start
+    # ATTACK 12 (falsey-preimage slack): asked for no path / no host, the
+    # routine actively strips whatever reach the record already carried
+    # instead of leaving it alone.
     secure = has_security_prefix(key) or is_none_ci(policy)
     store_cookie(cookie, path, domain, secure, policy)
+    if len(path) == 0:
+        cookie.has_path = False
+        empty_p = []  # type: List[int]
+        cookie.path = empty_p
+    if len(domain) == 0:
+        cookie.has_domain = False
+        empty_d = []  # type: List[int]
+        cookie.domain = empty_d
     # impl-end
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -501,6 +501,9 @@
                     ToSeq(cookie.policy) == Old(ToSeq(cookie.policy))))
     # post-conditions-end
     # impl-start
-    secure = has_security_prefix(key) or is_none_ci(policy)
+    # ATTACK 13 (partial domain on the name): only the first of the two
+    # reserved security-prefix forms makes the emitted expiry cookie
+    # transport-secure; a name carrying the other one does not.
+    secure = starts_with(key, secure_prefix()) or is_none_ci(policy)
     store_cookie(cookie, path, domain, secure, policy)
     # impl-end
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -501,6 +501,13 @@
                     ToSeq(cookie.policy) == Old(ToSeq(cookie.policy))))
     # post-conditions-end
     # impl-start
+    # ATTACK 14 (partial domain on the forwarding): the cross-site policy value
+    # is forwarded onto the emitted expiry cookie only when it is the
+    # unrestricted policy; a relaxed or restrictive value is dropped.
     secure = has_security_prefix(key) or is_none_ci(policy)
-    store_cookie(cookie, path, domain, secure, policy)
+    if is_none_ci(policy):
+        store_cookie(cookie, path, domain, secure, policy)
+    else:
+        dropped = []  # type: List[int]
+        store_cookie(cookie, path, domain, secure, dropped)
     # impl-end
```

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -501,6 +501,8 @@
                     ToSeq(cookie.policy) == Old(ToSeq(cookie.policy))))
     # post-conditions-end
     # impl-start
-    secure = has_security_prefix(key) or is_none_ci(policy)
-    store_cookie(cookie, path, domain, secure, policy)
+    # ATTACK 15 (over-broad flag, ungrounded): every emitted expiry cookie is
+    # marked transport-secure, on no ground at all -- and nothing can take the
+    # flag back off.
+    store_cookie(cookie, path, domain, True, policy)
     # impl-end
```

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -501,6 +501,9 @@
                     ToSeq(cookie.policy) == Old(ToSeq(cookie.policy))))
     # post-conditions-end
     # impl-start
-    secure = has_security_prefix(key) or is_none_ci(policy)
+    # ATTACK 16 (oracle echo, transposed arguments): the transport-secure
+    # decision echoes the spec's own predicate but reads the cross-site policy
+    # value where the name belongs and the name where the value belongs.
+    secure = expiry_secure(policy, key)
     store_cookie(cookie, path, domain, secure, policy)
     # impl-end
```

Attack 17 — `atk_17.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -501,6 +501,11 @@
                     ToSeq(cookie.policy) == Old(ToSeq(cookie.policy))))
     # post-conditions-end
     # impl-start
+    # ATTACK 17 (falsey-preimage slack on the policy): asked for no cross-site
+    # policy value, the routine strips whatever policy attribute the record
+    # already carried instead of leaving it exactly as it stood.
     secure = has_security_prefix(key) or is_none_ci(policy)
     store_cookie(cookie, path, domain, secure, policy)
+    if len(policy) == 0:
+        cookie.has_policy = False
     # impl-end
```

Attack 18 — `atk_18.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -501,6 +501,13 @@
                     ToSeq(cookie.policy) == Old(ToSeq(cookie.policy))))
     # post-conditions-end
     # impl-start
+    # ATTACK 18 (partial domain over the reach): the emitted expiry carries the
+    # host it was asked for only when a cross-site policy value was supplied;
+    # on the plain default-expiry slice it belongs to no particular host.
     secure = has_security_prefix(key) or is_none_ci(policy)
-    store_cookie(cookie, path, domain, secure, policy)
+    if len(policy) > 0:
+        store_cookie(cookie, path, domain, secure, policy)
+    else:
+        nohost = []  # type: List[int]
+        store_cookie(cookie, path, nohost, secure, policy)
     # impl-end
```

Attack 19 — `atk_19.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -501,6 +501,11 @@
                     ToSeq(cookie.policy) == Old(ToSeq(cookie.policy))))
     # post-conditions-end
     # impl-start
-    secure = has_security_prefix(key) or is_none_ci(policy)
+    # ATTACK 19 (boundary, degraded oracle): the unrestricted policy is
+    # recognised by its FIRST code point alone instead of the whole four-code-
+    # point spelling, so any policy value beginning with 'n' or 'N' marks the
+    # emitted expiry cookie transport-secure.
+    starts_n = len(policy) > 0 and lower_cp(policy[0]) == 110
+    secure = has_security_prefix(key) or starts_n
     store_cookie(cookie, path, domain, secure, policy)
     # impl-end
```

Attack 20 — `atk_20.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -501,6 +501,23 @@
                     ToSeq(cookie.policy) == Old(ToSeq(cookie.policy))))
     # post-conditions-end
     # impl-start
+    # ATTACK 20 (store misdirected): the attribute store is invoked, but on a
+    # fresh morsel of the routine's own, and the cookie the caller holds gets
+    # its footprint written in place -- with the already-elapsed lifetime simply
+    # asserted rather than stamped by the recorder.
+    scratch = Cookie()
     secure = has_security_prefix(key) or is_none_ci(policy)
-    store_cookie(cookie, path, domain, secure, policy)
+    store_cookie(scratch, path, domain, secure, policy)
+    cookie.expired = True
+    if secure:
+        cookie.secure = True
+    if len(policy) > 0:
+        cookie.has_policy = True
+        cookie.policy = scratch.policy
+    if len(path) > 0:
+        cookie.has_path = True
+        cookie.path = scratch.path
+    if len(domain) > 0:
+        cookie.has_domain = True
+        cookie.domain = scratch.domain
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCOPE:** adversarial G-EQ (refinement fidelity) on live model.py sha256 9da3179acda20a9747db449493565bb1206f922e29b489bbe1502fee797489f1. Every attack built by copying the shipping model.py and editing ONLY the impl region; adversary confirmed same_spec=True and unsound_evasions=[] on all 20. Positive control (byte-identical copy) verifies: exit 0, 40.64s.

### COMMANDS (from repo root swe-proof, run in background batches of <=3 per the parallelism instruction):
  python -m swebench_unified.adversary weakness nagini django__django-13195 <n>.py   [n=1..20]
  python resolve.py atk_<n>   [n=9,10,12,19,20]  -> run_resolve('django__django-13195', patch, timeout=2400, retries=3)
  git apply --check -p1 patch_atk_<n>.diff in a base_commit (156a2138db20abc89933121e4ff2ee2ce56a173a) worktree -> OK for all 5

### PER-ATTACK RESULTS (raw text in .../out/atk_<n>.txt):
  atk_1  prepatch, both legs dropped            -> REJECTED, exactly on model.py:491 "cookie.secure == (Old(cookie.secure) or expiry_secure(key, policy))"  => prepatch_reproduced=TRUE
  atk_2  'none' disjunct dropped                -> REJECTED
  atk_3  AND instead of OR                      -> REJECTED
  atk_4  case-sensitive 'none' (boundary)       -> REJECTED
  atk_5  any known policy => secure (over-wide) -> REJECTED
  atk_6  partial domain + forged expiry, reach lost -> REJECTED
  atk_7  hardcoded root reach                   -> REJECTED
  atk_8  reach arguments transposed             -> REJECTED
  atk_9  total setter bypass, record rebuilt    -> CANDIDATE (140.5s) -> patch_atk_9.diff  RESOLVED (F2P 5/5, P2P 382/382)
  atk_10 bypass only on the no-policy slice     -> CANDIDATE (75.8s)  -> patch_atk_10.diff RESOLVED (5/5, 382/382)
  atk_11 control-flow effect: diverging loop on the reserved-prefix slice -> REJECTED (MustTerminate(10) refutes it; confirms the memory note that loop invariants alone do not)
  atk_12 reach stripped on the falsey slice     -> CANDIDATE (40.4s)  -> patch_atk_12.diff RESOLVED (5/5, 382/382)
  atk_13 only `__Secure`- prefix (partial domain) -> REJECTED
  atk_14 forward only the 'none' policy         -> REJECTED
  atk_15 always secure                          -> REJECTED
  atk_16 ungrounded-oracle echo, transposed args expiry_secure(policy, key) -> REJECTED
  atk_17 pre-existing policy stripped (cumulativity) -> REJECTED
  atk_18 host dropped on the no-policy slice    -> REJECTED
  atk_19 degraded oracle: first code point n/N  -> CANDIDATE (41.1s)  -> patch_atk_19.diff RESOLVED (5/5, 382/382)
  atk_20 store misdirected to a scratch cookie  -> CANDIDATE (75.4s)  -> patch_atk_20.diff RESOLVED (5/5, 382/382)
  14 REJECTED / 5 CANDIDATE-and-RESOLVED / 1 (original atk_11 shape) gave a Nagini "Translation failed" no-verdict and was NOT counted as a rejection; it was replaced by the expressible diverging-loop form above, which was run to a real verdict.

HARNESS-FLAKE HANDLING (important, and not a spec signal): the first atk_19 resolve returned completed=False with docker.errors.ImageNotFound (404 on an image sha) - a fleet-race environment failure. Per the host-saturation/environment rule I did NOT read that as a non-resolve; I re-ran with retries=3 and both atk_19 and atk_20 resolved on attempt 2/4 (flaky=True, completed=True). No CANDIDATE verdict rests on an incomplete run.

STALE-RECORD DRIFT (reported, not inherited): meta.json stamps G-EQ and G-PANEL-1 on f8de1fe7dcce... while G-VERIFY/G-AX/G-CONF/G-GOLD/G-HYGIENE/G-MUT/G-PBT/G-DIFF are all stamped on the live 9da3179acda2; 5 of 6 region_hashes (axioms, pre-conditions, post-conditions, impl, spec_view) DRIFT, only `pure` matches. Concretely, the prior verdict.md claims the setter-bypass family was repaired by "the unforgeable `recorded` capability (an abstract @ContractOnly @Predicate ...) plus Ensures(recorded(cookie))" - that predicate DOES NOT EXIST in the shipping model.py (`recorded` appears only in prose at lines 51/56/147/150/197/203/279/395; there is no @Predicate at all). I therefore re-encoded the whole bypass family from scratch rather than inheriting its disposition, and cleared it by EXECUTION: atk_9/atk_10/atk_12/atk_20 all verify and all resolve. The load formerly attributed to `recorded` is in fact carried by the A6 reach postconditions, and refinement.md §C is right to say so - it explicitly declares that a reimplemented recorder verifies by design (pos-control-reimplemented-recorder). This is a records/freshness defect for G-PANEL, not a refinement-fidelity defect.

A-LEG AUDIT (the legs the role was told to concentrate on; my own differential, alegs.py, run under the repo interpreter python, independent of axiom_check.py):
  - A-reference (deep model expiry_secure/has_security_prefix/is_none_ci + forwarding + reach vs the REAL post-patch delete_cookie): 0 divergences over 5268 cases.
  - A-consumed (store_cookie's Ensures vs the real UNCHANGED set_cookie at this call site, incl. every cumulative clause measured over a morsel that ALREADY carries a record, not only a fresh one): 0 divergences over 3468 cases. Corroborated structurally: http.cookies.BaseCookie.`__set` does `M = self.get(key, Morsel())` then `M.set(...)`, i.e. it REUSES the held morsel - which is exactly what makes the axiom's cumulative `Ensures(cookie.secure == (Old(cookie.secure) or secure))` and the empty-value installs-nothing clauses sound rather than over-claiming.
  - A-domain (is_storable_name == records-vs-raises for both routines; is_known_policy == the setter's accept set): 0 divergences over 4327 names. Confirms A1's D-refinement really carves the raise regions, so the excluded region costs nothing.
  - Only ONE @ContractOnly exists in model.py, `store_cookie`, standing for the UNCHANGED callee set_cookie. refinement.md §C's load-bearing claim "there is no delete_cookie @ContractOnly" is CONFIRMED against the source: the changed logic (the 'none' disjunct and the forwarding) is modelled deeply, not axiomatized. No Assume / no sorry / no Fold-based evasion in the shipping model.

**REFINEMENT.MD LEG TAXONOMY:** 7 tagged legs, all in the allowed set - A1=R, A2=R+I, A3=R+I, A4=I (under A2+A3), A5=A-consumed, A6=I (under A5), B1=I. NO kind-3 (unexpressible-changed-op) leg. Both discriminating changes have a stated differential witness that fails on the intended clause (secure disjunct -> model_prepatch/2 on the secure clause; forwarding -> model_prepatch_3 on the has_policy clause), and my atk_1 independently reproduces the prepatch failing at model.py:491. A6's "reach must not be traded away" argument is corroborated by my atk_6/atk_7/atk_8, all of which the spec rejects.

INDEPENDENT CORROBORATION OF THE CANDIDATES (9600-input gold-vs-candidate emitted-header differential, sweep.py, over names x policies x reach preimages x pre-existing records; each candidate patch applied in its own base_commit worktree probe<n>): atk_19 0/9600 divergences (behaviourally identical to gold). atk_9 960, atk_10 160, atk_12 1536, atk_20 960 - and every one of those divergences is confined to the falsey-preimage region (path='' / None, domain='') over a pre-existing seeded record that mapping.md §2 DECLARES as the abstraction ("the weakest clause true of BOTH falsey preimages"). Reachability of that region was checked, not assumed: grep of the base tree shows the only delete_cookie call sites are tests/responses/test_cookie.py (no path/domain kwargs), sessions/middleware.py (settings.SESSION_COOKIE_PATH='/', SESSION_COOKIE_DOMAIN=None) and messages/storage/cookie.py (SESSION_COOKIE_DOMAIN) - nothing passes an empty-string reach, so the divergence region is unreachable from both the graded set and the two wiring sites.

**VERDICT RATIONALE:** >=5 attacks run (20 run, all machine-checked), the prepatch bug reproduced and rejected on the expected clause, every CANDIDATE's faithful patch materialized, apply-checked and EXECUTED through the official harness, and none of them fails to resolve. So no verify-not-correct witness exists at this attack depth => SOUND (advisory). One caveat for the panel, outside my gate: the G-EQ/G-PANEL-1 stamps and the verdict.md narrative describe bytes that are not what ships, so the RECORD needs refreshing even though the SPEC holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 20 admissible attacks re-run of 20 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 20 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_11.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_16.py`, `atk_17.py`, `atk_18.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_9.py`, `atk_10.py`, `atk_12.py`, `atk_19.py`, `atk_20.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying same-spec impl was found whose faithful refined patch fails to resolve. Five impls VERIFY (atk_9 total setter bypass, atk_10 narrow bypass on the no-policy slice, atk_12 reach stripped on the falsey slice, atk_19 degraded oracle recognising the unrestricted policy by its first code point, atk_20 store misdirected to a scratch cookie with the caller's record written in place); all five had their faithful patches materialized, git-apply-checked at base_commit, and RUN through run_resolve: all five RESOLVED (completed=True, F2P 5/5, P2P 382/382, no PASS_TO_FAIL). They are genuinely-correct alternative implementations, not spec weaknesses. atk_19 is correct because under the frozen precondition Implies(len(policy)>0, is_known_policy(policy)) the only recognised tokens are none/lax/strict, so "first code point is n/N" and "is none, case-insensitively" coincide; a 9600-input gold-vs-candidate Set-Cookie header differential confirms 0/9600 divergences. atk_20 is correct because the spec is stated over what the EMITTED cookie carries, not over which callee was invoked; its 960/9600 divergences lie entirely inside the region mapping.md §2 DECLARES as the falsey-preimage abstraction (path='' / domain='' over a pre-existing seeded record), and no repo call site or graded test reaches it (all sites pass the '/' default or settings.SESSION_COOKIE_PATH / SESSION_COOKIE_DOMAIN).
```

**Attacks re-run (20):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 20 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good)

Attack 17 — `atk_17.py` → rejected (same spec, does not verify — good)

Attack 18 — `atk_18.py` → rejected (same spec, does not verify — good)

Attack 19 — `atk_19.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 20 — `atk_20.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCOPE:** adversarial G-EQ (refinement fidelity) on live model.py sha256 9da3179acda20a9747db449493565bb1206f922e29b489bbe1502fee797489f1. Every attack built by copying the shipping model.py and editing ONLY the impl region; adversary confirmed same_spec=True and unsound_evasions=[] on all 20. Positive control (byte-identical copy) verifies: exit 0, 40.64s.

### COMMANDS (from repo root swe-proof, run in background batches of <=3 per the parallelism instruction):
  python -m swebench_unified.adversary weakness nagini django__django-13195 <n>.py   [n=1..20]
  python resolve.py atk_<n>   [n=9,10,12,19,20]  -> run_resolve('django__django-13195', patch, timeout=2400, retries=3)
  git apply --check -p1 patch_atk_<n>.diff in a base_commit (156a2138db20abc89933121e4ff2ee2ce56a173a) worktree -> OK for all 5

### PER-ATTACK RESULTS (raw text in .../out/atk_<n>.txt):
  atk_1  prepatch, both legs dropped            -> REJECTED, exactly on model.py:491 "cookie.secure == (Old(cookie.secure) or expiry_secure(key, policy))"  => prepatch_reproduced=TRUE
  atk_2  'none' disjunct dropped                -> REJECTED
  atk_3  AND instead of OR                      -> REJECTED
  atk_4  case-sensitive 'none' (boundary)       -> REJECTED
  atk_5  any known policy => secure (over-wide) -> REJECTED
  atk_6  partial domain + forged expiry, reach lost -> REJECTED
  atk_7  hardcoded root reach                   -> REJECTED
  atk_8  reach arguments transposed             -> REJECTED
  atk_9  total setter bypass, record rebuilt    -> CANDIDATE (140.5s) -> patch_atk_9.diff  RESOLVED (F2P 5/5, P2P 382/382)
  atk_10 bypass only on the no-policy slice     -> CANDIDATE (75.8s)  -> patch_atk_10.diff RESOLVED (5/5, 382/382)
  atk_11 control-flow effect: diverging loop on the reserved-prefix slice -> REJECTED (MustTerminate(10) refutes it; confirms the memory note that loop invariants alone do not)
  atk_12 reach stripped on the falsey slice     -> CANDIDATE (40.4s)  -> patch_atk_12.diff RESOLVED (5/5, 382/382)
  atk_13 only `__Secure`- prefix (partial domain) -> REJECTED
  atk_14 forward only the 'none' policy         -> REJECTED
  atk_15 always secure                          -> REJECTED
  atk_16 ungrounded-oracle echo, transposed args expiry_secure(policy, key) -> REJECTED
  atk_17 pre-existing policy stripped (cumulativity) -> REJECTED
  atk_18 host dropped on the no-policy slice    -> REJECTED
  atk_19 degraded oracle: first code point n/N  -> CANDIDATE (41.1s)  -> patch_atk_19.diff RESOLVED (5/5, 382/382)
  atk_20 store misdirected to a scratch cookie  -> CANDIDATE (75.4s)  -> patch_atk_20.diff RESOLVED (5/5, 382/382)
  14 REJECTED / 5 CANDIDATE-and-RESOLVED / 1 (original atk_11 shape) gave a Nagini "Translation failed" no-verdict and was NOT counted as a rejection; it was replaced by the expressible diverging-loop form above, which was run to a real verdict.

HARNESS-FLAKE HANDLING (important, and not a spec signal): the first atk_19 resolve returned completed=False with docker.errors.ImageNotFound (404 on an image sha) - a fleet-race environment failure. Per the host-saturation/environment rule I did NOT read that as a non-resolve; I re-ran with retries=3 and both atk_19 and atk_20 resolved on attempt 2/4 (flaky=True, completed=True). No CANDIDATE verdict rests on an incomplete run.

STALE-RECORD DRIFT (reported, not inherited): meta.json stamps G-EQ and G-PANEL-1 on f8de1fe7dcce... while G-VERIFY/G-AX/G-CONF/G-GOLD/G-HYGIENE/G-MUT/G-PBT/G-DIFF are all stamped on the live 9da3179acda2; 5 of 6 region_hashes (axioms, pre-conditions, post-conditions, impl, spec_view) DRIFT, only `pure` matches. Concretely, the prior verdict.md claims the setter-bypass family was repaired by "the unforgeable `recorded` capability (an abstract @ContractOnly @Predicate ...) plus Ensures(recorded(cookie))" - that predicate DOES NOT EXIST in the shipping model.py (`recorded` appears only in prose at lines 51/56/147/150/197/203/279/395; there is no @Predicate at all). I therefore re-encoded the whole bypass family from scratch rather than inheriting its disposition, and cleared it by EXECUTION: atk_9/atk_10/atk_12/atk_20 all verify and all resolve. The load formerly attributed to `recorded` is in fact carried by the A6 reach postconditions, and refinement.md §C is right to say so - it explicitly declares that a reimplemented recorder verifies by design (pos-control-reimplemented-recorder). This is a records/freshness defect for G-PANEL, not a refinement-fidelity defect.

A-LEG AUDIT (the legs the role was told to concentrate on; my own differential, alegs.py, run under the repo interpreter python, independent of axiom_check.py):
  - A-reference (deep model expiry_secure/has_security_prefix/is_none_ci + forwarding + reach vs the REAL post-patch delete_cookie): 0 divergences over 5268 cases.
  - A-consumed (store_cookie's Ensures vs the real UNCHANGED set_cookie at this call site, incl. every cumulative clause measured over a morsel that ALREADY carries a record, not only a fresh one): 0 divergences over 3468 cases. Corroborated structurally: http.cookies.BaseCookie.`__set` does `M = self.get(key, Morsel())` then `M.set(...)`, i.e. it REUSES the held morsel - which is exactly what makes the axiom's cumulative `Ensures(cookie.secure == (Old(cookie.secure) or secure))` and the empty-value installs-nothing clauses sound rather than over-claiming.
  - A-domain (is_storable_name == records-vs-raises for both routines; is_known_policy == the setter's accept set): 0 divergences over 4327 names. Confirms A1's D-refinement really carves the raise regions, so the excluded region costs nothing.
  - Only ONE @ContractOnly exists in model.py, `store_cookie`, standing for the UNCHANGED callee set_cookie. refinement.md §C's load-bearing claim "there is no delete_cookie @ContractOnly" is CONFIRMED against the source: the changed logic (the 'none' disjunct and the forwarding) is modelled deeply, not axiomatized. No Assume / no sorry / no Fold-based evasion in the shipping model.

**REFINEMENT.MD LEG TAXONOMY:** 7 tagged legs, all in the allowed set - A1=R, A2=R+I, A3=R+I, A4=I (under A2+A3), A5=A-consumed, A6=I (under A5), B1=I. NO kind-3 (unexpressible-changed-op) leg. Both discriminating changes have a stated differential witness that fails on the intended clause (secure disjunct -> model_prepatch/2 on the secure clause; forwarding -> model_prepatch_3 on the has_policy clause), and my atk_1 independently reproduces the prepatch failing at model.py:491. A6's "reach must not be traded away" argument is corroborated by my atk_6/atk_7/atk_8, all of which the spec rejects.

INDEPENDENT CORROBORATION OF THE CANDIDATES (9600-input gold-vs-candidate emitted-header differential, sweep.py, over names x policies x reach preimages x pre-existing records; each candidate patch applied in its own base_commit worktree probe<n>): atk_19 0/9600 divergences (behaviourally identical to gold). atk_9 960, atk_10 160, atk_12 1536, atk_20 960 - and every one of those divergences is confined to the falsey-preimage region (path='' / None, domain='') over a pre-existing seeded record that mapping.md §2 DECLARES as the abstraction ("the weakest clause true of BOTH falsey preimages"). Reachability of that region was checked, not assumed: grep of the base tree shows the only delete_cookie call sites are tests/responses/test_cookie.py (no path/domain kwargs), sessions/middleware.py (settings.SESSION_COOKIE_PATH='/', SESSION_COOKIE_DOMAIN=None) and messages/storage/cookie.py (SESSION_COOKIE_DOMAIN) - nothing passes an empty-string reach, so the divergence region is unreachable from both the graded set and the two wiring sites.

**VERDICT RATIONALE:** >=5 attacks run (20 run, all machine-checked), the prepatch bug reproduced and rejected on the expected clause, every CANDIDATE's faithful patch materialized, apply-checked and EXECUTED through the official harness, and none of them fails to resolve. So no verify-not-correct witness exists at this attack depth => SOUND (advisory). One caveat for the panel, outside my gate: the G-EQ/G-PANEL-1 stamps and the verdict.md narrative describe bytes that are not what ships, so the RECORD needs refreshing even though the SPEC holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**ATTACK:** faithfulness-break — is the spec too strong / does the modeled function disagree with the real callee on some input? Reference = base_commit worktree with patch.diff APPLIED (gold patch reconstructed from inst_13195.json, 2611 bytes, applies clean at 156a2138db). Result: NO divergence found; spec is faithful.

**SETUP.** Fresh worktree * at 156a2138db + gold patch. CRITICAL environment finding: I first ran the differential on the HOST python (3.12.3) and got 117,966 apparent violations — a 'RAISED-IN-DOMAIN' hit where delete_cookie('c', path='/a\tb') raises CookieError from `_has_control_character` in Lib/http/cookies.py:305, an input the model admits (path/domain carry NO Requires). That would have been a genuine spec-too-strong finding. It is an ARTIFACT: `_has_control_character` does not exist in the graded interpreter. The graded image swebench/sweb.eval.x86_64.django_1776_django-13195 runs Python 3.6.13 (conda testbed, /testbed), where hasattr(http.cookies,'`_has_control_character`') is False and every control-char path/domain ('\t', '/a\tb', '/a\nb', '/a\x00b', '/a\x7fb', domain 'a\tb') RECORDS VERBATIM and returns. I discarded the host result and re-ran everything IN the graded container. Reporting the host hit would have been a false UNFAITHFUL off the wrong interpreter.

**METHOD.** Transcribed model.py's spec verbatim into Python (lower_cp / is_none_ci / is_relaxed_ci / is_restrictive_ci / is_known_policy / starts_with / has_security_prefix / is_name_char / all_name_chars / equals_ci / is_reserved_name / is_storable_name / expiry_secure) and projected the real Morsel at response.cookies[key] onto the model Cookie (expired = expires=='Thu, 01 Jan 1970 00:00:00 GMT' AND max-age==0 AND value=='' ; secure ; has_path/path ; has_domain/domain ; has_policy/policy), then checked EVERY Ensures of model.py's delete_cookie against the real patched routine.

### IN-CONTAINER RESULTS (all zero):
1. DOMAIN agreement, names: is_storable_name(key) == real returns-vs-raises over the boundary name list, the full 0x00-0x10f codepoint sweep in 4 shapes, non-ASCII incl. U+212A KELVIN / U+0130 / U+0131, the 9 reserved names x 5 casings, empty name, + 30,000 seeded fuzz names => 0 mismatches. So Requires(is_storable_name) carves out EXACTLY the refusal region — it is not over-restrictive (no admitted name raises) and not under-restrictive.
2. DOMAIN agreement, policy: Implies(len>0, is_known_policy) == returns-vs-raises over all case permutations of none/lax/strict, boundary junk ('bogus','none ',' none','nonee','non','néne','NONEK','noıe','İone') + 6,000 fuzz => 0 mismatches.
3. Reach args are genuinely UNRESTRICTED in the graded env, matching the spec's deliberate absence of a path/domain Requires: separators, spaces, quotes, commas, semicolons, non-ASCII AND control chars all record verbatim on 3.6.13.
4. **POSTCONDITION SWEEP:** 388,800 in-domain cases (565,920 correctly excluded), names x policies x paths x domains x 18 pre-existing-record shapes => 0 violations of any clause.
5. **WIDE FUZZ:** 200,000 in-domain random tuples (incl. \x00/\t/non-ASCII reach values and random pre-states) => 0 violations.
6. Old(...) CUMULATIVE clauses — the sharpest risk, since they are vacuous on a fresh morsel — exercised against pre-states built through the SAME real setter (path='/old', path='', path=None, domain='.old.com', domain='', secure=True/False, samesite=Lax/Strict/None, combined, +httponly/max_age/value). secure==(Old(secure) or expiry_secure), has_policy==(Old(has_policy) or len>0), policy-untouched-when-empty, and both installs-nothing-of-its-own reach clauses all hold => 0 violations.
7. **UNICODE CASE FOLD:** exhaustive scan of all 0x110000 codepoints under the container's unicodedata — ZERO non-ASCII codepoints whose str.lower() lands in any substring of 'none' (or 'lax'/'strict'), and no multi-char lowercase expansions either. So model.py's ASCII-only lower_cp is EXACTLY the real str.lower() for these comparisons; the classic Kelvin-sign/dotted-I attack on an ASCII-only fold does not exist here.
8. OMITTED-path form (what the graded tests hit most): 180 cases confirm mapping.md §2's asymmetry claim is right — omitted path defaults to '/', a preimage of the SITE ROOT and NOT of the empty list (unlike omitted samesite/domain, which default to None). The spec's rendering of the omitted arg as path='/' agrees with the real routine; 0 violations.

NON-VACUITY CONTROL (guards against rubber-stamping a spec that is trivially satisfiable): monkeypatched the PRE-patch body back in and re-ran. The spec REJECTS it — 1,416 violations on exactly the clauses the patch changes: 'secure' (missing the 'none' disjunct), 'has_policy' and 'policy-value' (missing the samesite forwarding), and NOT on the reach/expired clauses. That matches refinement.md's A6 claim about where the differential twins fail, and confirms the spec is too strong nowhere and too weak nothing-here.

VERIFIER + ORACLE: scripts/nagini_verify.sh on the bundle model.py => 'Verification successful' (30.42s, exit 0), so the checked artifact is the one I audited. Gold patch + test_patch in the graded image => responses.test_cookie 'Ran 13 tests / OK', F2P satisfied, so the reference I compared against is the resolving one.

**JUDGEMENT.** The two decisions the change introduces are modeled DEEPLY (expiry_secure spelled out, forwarding pinned by the has_policy/value clauses) with no @ContractOnly on delete_cookie, so the spec cannot hide the changed behavior behind an axiom. The only consumed axiom, store_cookie, stands in for the UNCHANGED set_cookie and I independently re-measured its Ensures against the real setter invoked exactly as the expiry site invokes it: 69,120 cases (incl. pre-existing-record blocks for the Old-form clauses) => 0 violations. Both Requires are domain restrictions that provably coincide with the real routine's raise-vs-return boundary rather than excluding any input the change is about. No diverging input exists on the graded interpreter; the single candidate I found was a host-interpreter artifact and is documented above so it is not re-litigated.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

NO RELAXATION IN THIS BUNDLE, established independently, so there is no unavoidability argument to re-derive and no disposition to inherit; judged as an ordinary faithful spec. meta.json has NO `relaxed_leakage` key (top-level keys: additional_change_sites, ax_apply_gold, ax_apply_gold_note, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version); `find . .. -maxdepth 2 -iname 'RELAX*'` over the bundle and the instance dir returns nothing; gates.G-LEAK.status == "pass" (not "relaxed"). The only 'relaxed_leakage'/'RELAXED_LEAKAGE' strings anywhere in the instance are INSIDE prior G-PANEL-3 ledger notes in meta.json/verdict.md that themselves assert the absence -- i.e. the phrase is quoted, not claimed.

**NO FILE ADDRESSES THE PANEL.** leakage.reviewer_directed() returns CLEAN ([]) on all 12 bundle files (model.py, model_prepatch{,`_2`,`_3`}.py, mapping.md, refinement.md, meta.json, properties.py, axiom_check.py, conformance_check.py, pbt_result.json, verdict.md). A targeted grep for verdict-prescribing phrasing ('you must/should record', 'the correct/honest verdict', 'do not report/flag', 'attacker 3', 'next reviewer') over every .py/.md/.json in the bundle returns nothing outside first-person prior-panel prose. The 'G-PANEL' strings live in meta.json/verdict.md as gate ledger entries only; nothing prescribes a verdict or tells me how to record. So no finding of that kind.

**ARTIFACT SCOPE.** Confirmed from src/swebench_unified/eval/dataset.py + eval/adapter.py that the consumer-visible artifact in modes 1/2 is EvalTask.spec_view == markers.spec_view(model.py) only; mapping.md / refinement.md / patch.diff / meta.json are auditor-side and are never shipped, so refinement.md's verbatim gold hunk and mapping.md's 'django/http/response.py:213' rows are out of scope for this gate (they would be leaks if shipped; they are not).

FRESHNESS -- I DID NOT INHERIT THE PRIOR PASS. Live model.py sha256 = 9da3179acda20a97... The recorded G-PANEL-3 and G-PANEL-2 passes were stamped against f8de1fe7dcce..., and G-EQ/G-PANEL-1 against f8de1fe7dcce too, so the previous NO-LEAKAGE was NOT a measurement of the bytes now shipping. meta.json['region_hashes'] is likewise STALE: axioms, impl, pre-conditions, post-conditions and spec_view all DRIFT against markers.region_hashes(live) (live spec_view 40f3d9c7a0bb..., meta a2fa2d7edec9...); only 'pure' MATCHES. G-LEAK/G-AX/G-CONF/G-HYGIENE/G-INTEGRITY/G-GOLD/G-VERIFY were re-run on live 9da3179a. Everything below is my own measurement on the live bytes.

### WHAT I RAN (live model.py 9da3179a, projected to spec_view.txt, 505 lines):
(1) leakage.screen(live model.py, nagini backend, gold patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. The screen has teeth on THIS instance: six controls injected into the same call, each caught -- patched path ('# see django/http/response.py' -> L2), pre-patch gold line ("secure = key.startswith(('`__Secure`-', '`__Host`-'))" -> L1), the gold's ADDED rationale comment ('# Browsers can ignore the Set-Cookie header if the cookie doesn't use' -> L1), a gold ADDED line ("expires='Thu, 01 Jan 1970 00:00:00 GMT', samesite=samesite," -> L1), narration ('fixes'/'buggy'/'previously' -> L3), diff marker ('@@' -> L1).

(2) Elision is real: ELISION_IMPL present; neither impl line ('secure = has_security_prefix(key) or is_none_ci(policy)', 'store_cookie(cookie, path, domain, secure, policy)') appears in the view.

(3) Manual sweep of the projected view: none of the three patched paths (django/http/response.py, django/contrib/sessions/middleware.py, django/contrib/messages/storage/cookie.py) NOR any bare basename (response.py / middleware.py / cookie.py) appears; no diff marker ('@@', 'diff --git', '+++ ', '--- ', '\nindex ') appears; no patched-side symbol appears (SESSION_COOKIE_SAMESITE / `_DOMAIN` / `_SECURE`, settings., HttpResponseBase, set_signed_cookie, `_update_cookie`, process_response, patch_vary_headers, samesite=, max_age all absent); whitespace-normalized comparison of EVERY added/removed gold line (threshold len>=4, below the screen's 8) against the normalized view yields ZERO collisions. No 'session'/'messages'/'middleware' wording, so the two call-site change locations are not hinted either.

(4) DISCRIMINATOR DERIVATION FROM problem_statement ALONE (hints_text excluded; hints are the single sentence 'we should add the samesite argument to delete_cookie() and preserve it', and the view is clean even of that vocabulary since everything it names is independently in the PS).

Each discriminator the view states is present in the PS, verified by literal substring match: forwarding the policy verbatim = PS title "HttpResponse.delete_cookie() should preserve cookie's samesite"; secure-when-policy-is-'none' = PS prose "Chrome and Firefox will soon begin ignoring Set-Cookie headers with Samesite=None that aren't marked 'Secure'"; the two reserved prefixes = PS prose "only setting 'Secure' if the cookie's key begins with 'Secure' or 'Host'" AND the literal key.startswith(('`__Secure`-', '`__Host`-')) inside the PS's own pasted code block; case-insensitive 'none' = the PS's quoted Firefox warning spells it lowercase (attribute set to "none"); the already-elapsed lifetime + reach carried by Cookie.expired / has_path / has_domain = the PS pastes the real header 'expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; Path=/' verbatim; the unchanged setter store_cookie builds on = the PS's code block calls self.set_cookie(; even the samesite kwarg wiring ('samesite=settings.SESSION_COOKIE_SAMESITE,') and the pre-patch signature ("def delete_cookie(self, key, path='/', domain=None)") are literally in the PS's own testing snippet.

The identifier `delete_cookie` echoes a patched repo symbol and is excused only because it is in the PS -- I confirmed that excuse does real work by re-running screen() with problem_statement withheld, which then FAILS: "L2/L5: spec-view identifier 'delete_cookie' embeds patched repo symbol 'delete_cookie' (not in problem statement)".

(5) THE ONE NON-PS TOKEN, RUN DOWN. is_relaxed_ci / is_restrictive_ci / is_known_policy name the 'lax' and 'strict' tokens; 'lax' is in the PS (the pasted live header 'SameSite=Lax') but 'strict' is NOT. This is not a leak: in a base_commit worktree (the upstream repository @ 156a2138db, /tmp) set_cookie at django/http/response.py:199-202 already validates samesite.lower() not in ('lax','none','strict') PRE-patch, and the gold diff contains none of "'lax', 'none', 'strict'", 'def set_cookie', '`_reserved`' or '`_LegalChars`' -- so the token triple is UNCHANGED-callee behaviour. It is consumed in the view only as Requires(Implies(len(policy) > 0, is_known_policy(policy))), a domain restriction saying where an emitted cookie is observable at all, never as a ground for either decision. Same for is_storable_name / is_name_char / the nine reserved names (stdlib http.cookies Morsel.`_reserved` + `_LegalChars`, with django/http/cookie.py's setdefault('samesite')): untouched by the patch, so they describe territory the edit does not enter and cannot localize it.

(6) Positive control that the artifact I screened is the shipping one: scripts/nagini_verify.sh on live model.py -> 'Verification successful' in 30.4s, exit 0; adversary same-spec on an unmodified copy -> exit 0 ('SAME').

**CONCLUSION:** every discriminator the spec view names is derivable from the public problem_statement, and nothing in it points at the edit beyond that -- no path, no symbol, no gold line, no diff marker, no bug->fix narration. NO-LEAKAGE.

RECORD-HYGIENE FINDING (reported; does not change my verdict, which rests on my own measurement of live 9da3179a): meta.json['region_hashes'] and the G-PANEL-1/-2/-3 + G-EQ stamps all reference f8de1fe7dcce, an OLDER model.py. The stamps should be refreshed so the freshness record matches the bytes shipping. Note also that this is the SECOND consecutive drift of this kind on this cell (the prior G-PANEL-3 note reports the same finding against 1c4bdc5be1e5 while itself being stamped on f8de1fe7dcce), which suggests the spec is being edited between panel runs faster than the stamps are refreshed.

STYLISTIC NOTE (not a leak, no line submitted): the docstring line 'The two decisions the change introduces -- forwarding the policy value and deriving the secure flag from the "none" policy' frames content as a change rather than purely as desired behaviour, and lines 24/26/458 similarly say 'the pre-existing default expiry behaviour is preserved'. None trips a narration token and the substance of each is exactly the PS's two asks plus the PS's pasted header, so a consumer learns nothing the issue text does not already state; but rephrasing them as pure behavioural statements would remove the edit-shaped framing.

**OTHER GATES:** all 16 recorded gates read pass in the live meta.json (G-AX, G-CONF, G-DIFF, G-EQ, G-GOLD, G-HYGIENE, G-INTEGRITY, G-LEAK, G-MUT, G-PANEL, G-PANEL-1/-2/-3, G-PBT, G-RESOLVE, G-VERIFY). With no relaxation here, my verdict leans on none of them -- it rests on the screen, the controls, the manual sweep and the PS derivation above, all run on the live bytes.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
