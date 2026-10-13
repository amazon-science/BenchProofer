# P2 adversarial audit — django__django-11532

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py`, `atk_10.py`, `atk_11.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_16.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_2.py`, `atk_3.py`, `atk_7.py`, `atk_9.py`, `atk_12.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -199,5 +199,20 @@
             and not valid_label(ToSeq(platform_name)))
     # post-conditions-end
     # impl-start
-    return ascii_compatible_domain(platform_name)
+    result = []  # type: List[int]
+    j = 0
+    n = len(platform_name)
+    while j < n:
+        # invariants-start
+        Invariant(Acc(list_pred(platform_name), 1 / 2))
+        Invariant(Acc(list_pred(result)))
+        Invariant(0 <= j and j <= n and n == len(platform_name))
+        Invariant(ToSeq(result) == ToSeq(platform_name).take(j))
+        Invariant(MustTerminate(n - j + 1))
+        # invariants-end
+        result = result + [platform_name[j]]
+        Assert(ToSeq(platform_name).take(j) + PSeq(platform_name[j]) == ToSeq(platform_name).take(j + 1))
+        j = j + 1
+    Assert(ToSeq(platform_name).take(n) == ToSeq(platform_name))
+    return result
     # impl-end
```

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -168,6 +168,11 @@
             and not valid_label(ToSeq(domain)))
     # post-conditions-end
     # impl-start
+    if len(domain) == 2 and domain[0] == 28450 and domain[1] == 23383:
+        Assert(ToSeq(domain) == seq_host_witness())
+        res = [120, 110, 45, 45, 112, 56, 115, 57, 51, 55, 98]  # type: List[int]
+        Assert(ToSeq(res) == seq_ace_witness())
+        return res
     return ace_encode(domain)
     # impl-end
 
```

Attack 3 — `atk_3.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -199,5 +199,5 @@
             and not valid_label(ToSeq(platform_name)))
     # post-conditions-end
     # impl-start
-    return ascii_compatible_domain(platform_name)
+    return ace_encode(platform_name)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -168,6 +168,11 @@
             and not valid_label(ToSeq(domain)))
     # post-conditions-end
     # impl-start
+    if len(domain) == 2 and domain[0] == 28450 and domain[1] == 23383:
+        Assert(ToSeq(domain) == seq_host_witness())
+        res = [120, 110, 45, 45, 112, 56, 115, 57, 51, 55, 99]  # type: List[int]
+        Assert(ToSeq(res) == seq_ace_witness())
+        return res
     return ace_encode(domain)
     # impl-end
 
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -168,7 +168,11 @@
             and not valid_label(ToSeq(domain)))
     # post-conditions-end
     # impl-start
-    return ace_encode(domain)
+    try:
+        return ace_encode(domain)
+    except LabelNotEncodable:
+        res = []  # type: List[int]
+        return res
     # impl-end
 
 
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -168,6 +168,8 @@
             and not valid_label(ToSeq(domain)))
     # post-conditions-end
     # impl-start
+    if len(domain) == 0:
+        raise LabelNotEncodable()
     return ace_encode(domain)
     # impl-end
 
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -168,7 +168,10 @@
             and not valid_label(ToSeq(domain)))
     # post-conditions-end
     # impl-start
-    return ace_encode(domain)
+    try:
+        return ace_encode(domain)
+    except LabelNotEncodable:
+        raise LabelNotEncodable()
     # impl-end
 
 
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -199,5 +199,6 @@
             and not valid_label(ToSeq(platform_name)))
     # post-conditions-end
     # impl-start
-    return ascii_compatible_domain(platform_name)
+    res = ascii_compatible_domain(platform_name)
+    return res + [0]
     # impl-end
```

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -199,5 +199,6 @@
             and not valid_label(ToSeq(platform_name)))
     # post-conditions-end
     # impl-start
+    tmp = ascii_compatible_domain(platform_name)
     return ascii_compatible_domain(platform_name)
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -168,6 +168,9 @@
             and not valid_label(ToSeq(domain)))
     # post-conditions-end
     # impl-start
+    if len(domain) == 4 and domain[0] == 97 and domain[1] == 46 and domain[2] == 46 and domain[3] == 98:
+        res = [97, 46, 46, 98]  # type: List[int]
+        return res
     return ace_encode(domain)
     # impl-end
 
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -168,7 +168,7 @@
             and not valid_label(ToSeq(domain)))
     # post-conditions-end
     # impl-start
-    return ace_encode(domain)
+    raise LabelNotEncodable()
     # impl-end
 
 
```

Attack 12 — `atk_12.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -199,5 +199,10 @@
             and not valid_label(ToSeq(platform_name)))
     # post-conditions-end
     # impl-start
+    if len(platform_name) == 2 and platform_name[0] == 28450 and platform_name[1] == 23383:
+        Assert(ToSeq(platform_name) == seq_host_witness())
+        res = [120, 110, 45, 45, 112, 56, 115, 57, 51, 55, 98]  # type: List[int]
+        Assert(ToSeq(res) == seq_ace_witness())
+        return res
     return ascii_compatible_domain(platform_name)
     # impl-end
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -199,5 +199,22 @@
             and not valid_label(ToSeq(platform_name)))
     # post-conditions-end
     # impl-start
-    return ascii_compatible_domain(platform_name)
+    res = ascii_compatible_domain(platform_name)
+    n = len(res)
+    if n == 0:
+        return res
+    out = []  # type: List[int]
+    j = 0
+    while j < n - 1:
+        # invariants-start
+        Invariant(Acc(list_pred(res)))
+        Invariant(Acc(list_pred(out)))
+        Invariant(0 <= j and j <= n - 1 and n == len(res))
+        Invariant(ToSeq(out) == ToSeq(res).take(j))
+        Invariant(MustTerminate(n - j + 1))
+        # invariants-end
+        out = out + [res[j]]
+        Assert(ToSeq(res).take(j) + PSeq(res[j]) == ToSeq(res).take(j + 1))
+        j = j + 1
+    return out
     # impl-end
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -168,6 +168,9 @@
             and not valid_label(ToSeq(domain)))
     # post-conditions-end
     # impl-start
+    if len(domain) == 0:
+        res = [120]  # type: List[int]
+        return res
     return ace_encode(domain)
     # impl-end
 
```

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -199,5 +199,6 @@
             and not valid_label(ToSeq(platform_name)))
     # post-conditions-end
     # impl-start
+    Assert(False)
     return ascii_compatible_domain(platform_name)
     # impl-end
```

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -199,5 +199,12 @@
             and not valid_label(ToSeq(platform_name)))
     # post-conditions-end
     # impl-start
+    j = 0
+    while j >= 0:
+        # invariants-start
+        Invariant(Acc(list_pred(platform_name), 1 / 2))
+        Invariant(j >= 0)
+        # invariants-end
+        j = j + 1
     return ascii_compatible_domain(platform_name)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** 16 same-spec attacks run (all confirmed byte-identical spec view via `adversary same-spec`), 5 came back CANDIDATE, and ALL FIVE had their faithful refined patches materialized against a real git worktree at base_commit a5308514fb4bc5086c9a16a8a24a945eeebb073c and RUN through the official harness (swebench_unified.harness.run_resolve). Every one RESOLVED (completed=true, attempts=1, flaky=false, F2P 1/1 pass, P2P 148/148 pass). No verifying wrong impl produced a non-resolving patch, so verify=>correct is not contradicted.

IMPORTANT CONTEXT — THIS SPEC WAS REPAIRED SINCE THE LAST AUDIT. meta.json still records G-EQ=fail / G-PANEL-1=fail from 2026-08-15T05:13 against model.py digest 7c1906968348d581... The CURRENT frozen model.py digest is 0d431996fe0bae705cbd3c8c159fff5b43b5346b44a7aa5094f83f6ae7a1debd. The repair added the totality partition (normal-return `Ensures(valid_label(ToSeq(domain)))` + complementary `Exsures(LabelNotEncodable,... and not valid_label(...))`) to ace_encode/ascii_compatible_domain/cached_host_name. I re-encoded the prior pass's named counterexample class against the NEW spec and it is now REJECTED (see atk_5/atk_10 below), i.e. the recorded fail is STALE and the hole it described is closed. Recommend re-stamping G-EQ / G-PANEL-1 against the current digest.

**PER-ATTACK RESULTS.** Command for each: `python -m swebench_unified.adversary weakness nagini django__django-11532 <path>` (run 3-at-a-time as background jobs; each also pre-screened with `adversary same-spec`, all SAME). Resolve command for each candidate: run_resolve('django__django-11532', <patch>) via do_resolve.py.

- atk_1.py — PREPATCH BUG re-encoded (cached_host_name returns a verbatim copy of platform_name; the raw socket.getfqdn() with NO ACE transform, per model_prepatch.py). weakness exit 2 = NOT-A-COUNTEREXAMPLE, does not verify. => prepatch_reproduced=TRUE; the spec senses the real bug (G-DIFF corroborated).
- atk_2.py — UNGROUNDED-ORACLE ECHO at site A: hard-codes the witness ACE for the witness label, bypassing ace_encode. exit 0 = CANDIDATE. Patch materialized (punycode gains `if domain == '漢字': return 'xn--p8s937b'`) => RESOLVED, F2P 1/1, P2P 148/148. Not a weakness: the hard-coded constant is the TRUE ACE, so it is behaviourally equal to gold; atk_4 proves the value is genuinely pinned rather than free.
- atk_3.py — COMPOSITION BYPASS at site B: cached_host_name calls ace_encode directly, skipping the modeled ascii_compatible_domain. exit 0 = CANDIDATE. Patch materialized (get_fqdn inlines `socket.getfqdn().encode('idna').decode('ascii')`, no punycode import) => RESOLVED, F2P 1/1, P2P 148/148. Not a weakness: it inlines the identical callee expression the helper contains — this is exactly the refactor direction refinement.md C describes.
- atk_4.py — WRONG-CONSTANT control for atk_2: same shape but returns 'xn--p8s937c' (last code point 98->99). exit 2 = does not verify. => the witness axiom really PINS the ACE value to the real transform; the spec is not satisfiable by an arbitrary ASCII constant (directive 8 holds).
- atk_5.py — SWALLOW THE OUT-OF-BAND CONDITION (the prior pass's break class): `try: return ace_encode(domain) except LabelNotEncodable: return []` — answers a label with no ACE with a substitute value. exit 2 = does not verify. *** This is the exact hole that made the OLD spec BROKEN; the repaired `Ensures(valid_label(ToSeq(domain)))` now rejects it. ***
- atk_6.py — OVER-SIGNAL: withholds a value from the empty label, which the real codec DOES answer (''->''). exit 2 = does not verify (the Exsures' `not valid_label(...)` is unprovable). => the other half of the partition bites too; both divergence directions are refuted.
- atk_7.py — CONTROL-FLOW RESHAPE of the out-of-band path: catch LabelNotEncodable and re-raise a FRESH one. exit 0 = CANDIDATE. I took the MOST adversarial faithful reading available, exploiting refinement.md A3's explicit claim that "nothing in the spec pins its identity, message, or any other incidental detail": the patch defines a NEW `class LabelNotEncodable(Exception)` in encoding.py and has punycode raise THAT instead of letting UnicodeError through, which genuinely changes what the four live `except UnicodeError:` arms (validators.py x2, html.py x2) catch. Materialized and run => RESOLVED anyway, F2P 1/1, P2P 148/148. So A3's disclosure is honest for THIS test set, but see RESIDUAL RISK below.
- atk_8.py — BOUNDARY: appends code point 0 to the ACE (still all-ASCII, so all_ascii cannot catch it). exit 2 = does not verify. => ace_seq-equality, not just all_ascii, is load-bearing.
- atk_9.py — CONTROL-FLOW EFFECT: evaluates the transform twice at site B. exit 0 = CANDIDATE. Patch materialized (a discarded `punycode(socket.getfqdn())` before the assignment) => RESOLVED, F2P 1/1, P2P 148/148. Correctly a non-weakness: the transform is pure, so a duplicate evaluation is observationally the identity — and mapping.md 2 already declares the memoization value-identity.
- atk_10.py — PARTIAL DOMAIN / dead-branch probe, the closest re-encoding of the OLD atk_11: hard-codes a value for the label 'a..b' (97,46,46,98), which is PURE ASCII yet REJECTED by the real codec (label empty or too long), so answering it with a value is genuinely wrong. exit 2 = does not verify. *** The old spec's dead-in-model raise path is now LIVE: valid_label no longer appears as a precondition on the impl face, so the impl cannot assume 'a..b' is encodable. ***
- atk_11.py — TOTAL OVER-SIGNAL: `raise LabelNotEncodable()` unconditionally, never answering any label. exit 2 = does not verify. => the spec forbids a transform that is uniformly out-of-band (the witness makes valid_label non-empty).
- atk_12.py — UNGROUNDED-ORACLE ECHO at site B (the site-A echo's mirror): get_fqdn special-cases the witness platform name. exit 0 = CANDIDATE. Patch materialized => RESOLVED, F2P 1/1, P2P 148/148. Same disposition as atk_2 — the echoed constant is the true ACE.
- atk_13.py — TRUNCATION boundary: returns the ACE minus its last code point (still all-ASCII). exit 2 = does not verify. => length/content is pinned by ace_seq-equality.
- atk_14.py — PARTIAL DOMAIN via ungrounded guard at site A: answers the EMPTY label with [120] ('x') although the real codec answers ''->''. exit 2 = does not verify.
- atk_15.py — VACUITY / INCONSISTENCY CONTROL: `Assert(False)` before the gold body. exit 2 = does not verify. *** Critical: the axiom set (valid_label / ace_seq / ace_encode + the complementary Ensures/Exsures pair) is CONSISTENT, so none of the 5 CANDIDATE verifications above is a vacuous pass. ***
- atk_16.py — DIVERGENCE: an infinite `while j >= 0` loop before the gold body. exit 2 = does not verify. => MustTerminate(10) at the method level really rejects a diverging rival.

**POSITIVE CONTROL:** positive_control.py is byte-identical to the frozen model.py (verified by diff), i.e. the gold impl verbatim. `adversary weakness` reports it shares the spec AND verifies in 17.8s. So the spec is satisfiable by the correct implementation — the 11 rejections above are the spec discriminating, not a spec nothing can satisfy.

EXTRA MAP-SCOPE CONTROL (atk_min.patch, resolved=True). The refinement map models ONLY sites A (punycode) and B (get_fqdn) and declares C's four call-site swaps behaviour-identical/unmodeled. To test whether that scope claim is honest I built the MINIMAL patch the map licenses — the new punycode helper plus the one-line get_fqdn change, leaving message.py / validators.py / html.py at base_commit — and ran it through the harness: RESOLVED (F2P 1/1, P2P 148/148). So refinement.md C's "no independently-observable fixed behaviour at these sites" is confirmed BY THE ORACLE, not merely asserted. This is the strongest available evidence that the modeled scope suffices.

### A-LEG AUDIT (the legs G-CONF does not mechanically cover).
1. Leg tags: all six legs are R (A1), A-consumed (A2), I control-flow (A3), R + A-reference-of-input (B1), I call + A-consumed (B2), I control-flow (B3). No kind-3; section D's claim holds. There is no axiom about the function UNDER CHANGE — punycode and get_fqdn are modeled (impl regions with real bodies), and the only axiomatized thing is the unchanged stdlib callee. deep_model_references in meta.json is [] and consistently so: all_ascii is a deep pure model but it is defined (front-recursive fold), not axiomatized.
2. Axiom<->callee correspondence, re-derived INDEPENDENTLY of axiom_check.py (my own probe, 60019 labels over an ASCII+non-ASCII+edge alphabet incl. '', 'a'*63, 'a'*64, 'a..b', '.b', soft hyphen, ZWSP, 'example.com.'): 56107 value-yielding / 3913 out-of-band, both non-empty; ZERO violations of (a) `Ensures(all_ascii(Result()))` on every value-yielding label, (b) the witness pin U+6F22 U+5B57 -> 'xn--p8s937b', (c) valid_label's witness clause, (d) determinism/exhaustiveness of the two-outcome partition. The bundle's own axiom_check.py also exits 0 (24 boundary + 40000 fuzz; 27169 value-yielding / 12855 out-of-band).
3. mapping.md 3.1's soundness ARGUMENT is independently correct: the final `.decode('ascii')` raises unless every byte is <128, so any value that returns at all is all-ASCII. The all-ASCII Ensures is therefore not merely fuzz-supported but structurally necessary — the strongest form this A-leg can take.
4. Type-refinement legs (R) spot-checked live: '漢字'->'xn--p8s937b', 'example'->'example', 'EXAMPLE'->'EXAMPLE' (case preserved), 'muenchen with umlaut'->'xn--mnchen-3ya', 'xn--p8s937b' idempotent — consistent with the str <-> List[int] code-point carrier and with modeling socket.getfqdn's RETURN as the input (the F2P mocks exactly that return).

RESIDUAL RISK (advisory, NOT a break — every candidate patch resolved, so this does not meet the BROKEN bar). Two disclosed-but-real scope limits, both already argued in refinement.md and both invisible to this instance's 1 F2P + 148 P2P:

(a) EXCEPTION IDENTITY (atk_7). refinement.md A3 says the spec pins only WHICH outcome occurred, not the exception's type. But four live sites catch `except UnicodeError` specifically (validators.py 2 arms, html.py 2 arms), so a refinement that signals a non-UnicodeError out of punycode — which the spec permits and which I materialized and confirmed still resolves — would change those arms' control flow. No test in this set drives an ill-formed IDN label into them.

(b) Section C's "pure callee extraction" wording is imprecise for ONE of the four swaps. I measured it: at sanitize_address the gold DELETES the `try: domain.encode('ascii') except UnicodeEncodeError:` guard, so pre-swap vs post-swap diverge on ASCII-but-ill-formed labels — 'a..b', '.b', 'a'*64 all returned verbatim before and raise UnicodeError after. The other three swaps are true extractions (the try/except is preserved verbatim around the call). The doc's own C paragraph and A3 do disclose the totality/control-flow reasoning, and this behaviour change is arguably the intended hardening, but calling all four "pure callee extractions... introduces no new observable behaviour" overstates it for message.py. Documentation precision, not a spec hole — no F2P/P2P test reaches it (test_sanitize_address_invalid raises ValueError during Address parsing, independent of the codec).

**COMPLETENESS.** 16 attacks encoded and fully verified (>= 5 floor met with 11 rejections + 5 candidates), prepatch bug reproduced and rejected, positive control verifies, vacuity and divergence controls both reject, all 5 candidate patches materialized and resolve-checked to completion (no timeouts, no infra failures, no inconclusive runs), plus one extra map-scope resolve. Nothing was left speculative. Scratch: (atk_N.py, atk_N.weakness.txt, atk_N.patch, atk_N.resolve.json, atk_min.patch, positive_control.py, model_frozen.py). The git worktree used to author the patches was removed after use.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py`, `atk_10.py`, `atk_11.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_16.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_2.py`, `atk_3.py`, `atk_7.py`, `atk_9.py`, `atk_12.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 16 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** 16 same-spec attacks run (all confirmed byte-identical spec view via `adversary same-spec`), 5 came back CANDIDATE, and ALL FIVE had their faithful refined patches materialized against a real git worktree at base_commit a5308514fb4bc5086c9a16a8a24a945eeebb073c and RUN through the official harness (swebench_unified.harness.run_resolve). Every one RESOLVED (completed=true, attempts=1, flaky=false, F2P 1/1 pass, P2P 148/148 pass). No verifying wrong impl produced a non-resolving patch, so verify=>correct is not contradicted.

IMPORTANT CONTEXT — THIS SPEC WAS REPAIRED SINCE THE LAST AUDIT. meta.json still records G-EQ=fail / G-PANEL-1=fail from 2026-08-15T05:13 against model.py digest 7c1906968348d581... The CURRENT frozen model.py digest is 0d431996fe0bae705cbd3c8c159fff5b43b5346b44a7aa5094f83f6ae7a1debd. The repair added the totality partition (normal-return `Ensures(valid_label(ToSeq(domain)))` + complementary `Exsures(LabelNotEncodable,... and not valid_label(...))`) to ace_encode/ascii_compatible_domain/cached_host_name. I re-encoded the prior pass's named counterexample class against the NEW spec and it is now REJECTED (see atk_5/atk_10 below), i.e. the recorded fail is STALE and the hole it described is closed. Recommend re-stamping G-EQ / G-PANEL-1 against the current digest.

**PER-ATTACK RESULTS.** Command for each: `python -m swebench_unified.adversary weakness nagini django__django-11532 <path>` (run 3-at-a-time as background jobs; each also pre-screened with `adversary same-spec`, all SAME). Resolve command for each candidate: run_resolve('django__django-11532', <patch>) via do_resolve.py.

- atk_1.py — PREPATCH BUG re-encoded (cached_host_name returns a verbatim copy of platform_name; the raw socket.getfqdn() with NO ACE transform, per model_prepatch.py). weakness exit 2 = NOT-A-COUNTEREXAMPLE, does not verify. => prepatch_reproduced=TRUE; the spec senses the real bug (G-DIFF corroborated).
- atk_2.py — UNGROUNDED-ORACLE ECHO at site A: hard-codes the witness ACE for the witness label, bypassing ace_encode. exit 0 = CANDIDATE. Patch materialized (punycode gains `if domain == '漢字': return 'xn--p8s937b'`) => RESOLVED, F2P 1/1, P2P 148/148. Not a weakness: the hard-coded constant is the TRUE ACE, so it is behaviourally equal to gold; atk_4 proves the value is genuinely pinned rather than free.
- atk_3.py — COMPOSITION BYPASS at site B: cached_host_name calls ace_encode directly, skipping the modeled ascii_compatible_domain. exit 0 = CANDIDATE. Patch materialized (get_fqdn inlines `socket.getfqdn().encode('idna').decode('ascii')`, no punycode import) => RESOLVED, F2P 1/1, P2P 148/148. Not a weakness: it inlines the identical callee expression the helper contains — this is exactly the refactor direction refinement.md C describes.
- atk_4.py — WRONG-CONSTANT control for atk_2: same shape but returns 'xn--p8s937c' (last code point 98->99). exit 2 = does not verify. => the witness axiom really PINS the ACE value to the real transform; the spec is not satisfiable by an arbitrary ASCII constant (directive 8 holds).
- atk_5.py — SWALLOW THE OUT-OF-BAND CONDITION (the prior pass's break class): `try: return ace_encode(domain) except LabelNotEncodable: return []` — answers a label with no ACE with a substitute value. exit 2 = does not verify. *** This is the exact hole that made the OLD spec BROKEN; the repaired `Ensures(valid_label(ToSeq(domain)))` now rejects it. ***
- atk_6.py — OVER-SIGNAL: withholds a value from the empty label, which the real codec DOES answer (''->''). exit 2 = does not verify (the Exsures' `not valid_label(...)` is unprovable). => the other half of the partition bites too; both divergence directions are refuted.
- atk_7.py — CONTROL-FLOW RESHAPE of the out-of-band path: catch LabelNotEncodable and re-raise a FRESH one. exit 0 = CANDIDATE. I took the MOST adversarial faithful reading available, exploiting refinement.md A3's explicit claim that "nothing in the spec pins its identity, message, or any other incidental detail": the patch defines a NEW `class LabelNotEncodable(Exception)` in encoding.py and has punycode raise THAT instead of letting UnicodeError through, which genuinely changes what the four live `except UnicodeError:` arms (validators.py x2, html.py x2) catch. Materialized and run => RESOLVED anyway, F2P 1/1, P2P 148/148. So A3's disclosure is honest for THIS test set, but see RESIDUAL RISK below.
- atk_8.py — BOUNDARY: appends code point 0 to the ACE (still all-ASCII, so all_ascii cannot catch it). exit 2 = does not verify. => ace_seq-equality, not just all_ascii, is load-bearing.
- atk_9.py — CONTROL-FLOW EFFECT: evaluates the transform twice at site B. exit 0 = CANDIDATE. Patch materialized (a discarded `punycode(socket.getfqdn())` before the assignment) => RESOLVED, F2P 1/1, P2P 148/148. Correctly a non-weakness: the transform is pure, so a duplicate evaluation is observationally the identity — and mapping.md 2 already declares the memoization value-identity.
- atk_10.py — PARTIAL DOMAIN / dead-branch probe, the closest re-encoding of the OLD atk_11: hard-codes a value for the label 'a..b' (97,46,46,98), which is PURE ASCII yet REJECTED by the real codec (label empty or too long), so answering it with a value is genuinely wrong. exit 2 = does not verify. *** The old spec's dead-in-model raise path is now LIVE: valid_label no longer appears as a precondition on the impl face, so the impl cannot assume 'a..b' is encodable. ***
- atk_11.py — TOTAL OVER-SIGNAL: `raise LabelNotEncodable()` unconditionally, never answering any label. exit 2 = does not verify. => the spec forbids a transform that is uniformly out-of-band (the witness makes valid_label non-empty).
- atk_12.py — UNGROUNDED-ORACLE ECHO at site B (the site-A echo's mirror): get_fqdn special-cases the witness platform name. exit 0 = CANDIDATE. Patch materialized => RESOLVED, F2P 1/1, P2P 148/148. Same disposition as atk_2 — the echoed constant is the true ACE.
- atk_13.py — TRUNCATION boundary: returns the ACE minus its last code point (still all-ASCII). exit 2 = does not verify. => length/content is pinned by ace_seq-equality.
- atk_14.py — PARTIAL DOMAIN via ungrounded guard at site A: answers the EMPTY label with [120] ('x') although the real codec answers ''->''. exit 2 = does not verify.
- atk_15.py — VACUITY / INCONSISTENCY CONTROL: `Assert(False)` before the gold body. exit 2 = does not verify. *** Critical: the axiom set (valid_label / ace_seq / ace_encode + the complementary Ensures/Exsures pair) is CONSISTENT, so none of the 5 CANDIDATE verifications above is a vacuous pass. ***
- atk_16.py — DIVERGENCE: an infinite `while j >= 0` loop before the gold body. exit 2 = does not verify. => MustTerminate(10) at the method level really rejects a diverging rival.

**POSITIVE CONTROL:** positive_control.py is byte-identical to the frozen model.py (verified by diff), i.e. the gold impl verbatim. `adversary weakness` reports it shares the spec AND verifies in 17.8s. So the spec is satisfiable by the correct implementation — the 11 rejections above are the spec discriminating, not a spec nothing can satisfy.

EXTRA MAP-SCOPE CONTROL (atk_min.patch, resolved=True). The refinement map models ONLY sites A (punycode) and B (get_fqdn) and declares C's four call-site swaps behaviour-identical/unmodeled. To test whether that scope claim is honest I built the MINIMAL patch the map licenses — the new punycode helper plus the one-line get_fqdn change, leaving message.py / validators.py / html.py at base_commit — and ran it through the harness: RESOLVED (F2P 1/1, P2P 148/148). So refinement.md C's "no independently-observable fixed behaviour at these sites" is confirmed BY THE ORACLE, not merely asserted. This is the strongest available evidence that the modeled scope suffices.

### A-LEG AUDIT (the legs G-CONF does not mechanically cover).
1. Leg tags: all six legs are R (A1), A-consumed (A2), I control-flow (A3), R + A-reference-of-input (B1), I call + A-consumed (B2), I control-flow (B3). No kind-3; section D's claim holds. There is no axiom about the function UNDER CHANGE — punycode and get_fqdn are modeled (impl regions with real bodies), and the only axiomatized thing is the unchanged stdlib callee. deep_model_references in meta.json is [] and consistently so: all_ascii is a deep pure model but it is defined (front-recursive fold), not axiomatized.
2. Axiom<->callee correspondence, re-derived INDEPENDENTLY of axiom_check.py (my own probe, 60019 labels over an ASCII+non-ASCII+edge alphabet incl. '', 'a'*63, 'a'*64, 'a..b', '.b', soft hyphen, ZWSP, 'example.com.'): 56107 value-yielding / 3913 out-of-band, both non-empty; ZERO violations of (a) `Ensures(all_ascii(Result()))` on every value-yielding label, (b) the witness pin U+6F22 U+5B57 -> 'xn--p8s937b', (c) valid_label's witness clause, (d) determinism/exhaustiveness of the two-outcome partition. The bundle's own axiom_check.py also exits 0 (24 boundary + 40000 fuzz; 27169 value-yielding / 12855 out-of-band).
3. mapping.md 3.1's soundness ARGUMENT is independently correct: the final `.decode('ascii')` raises unless every byte is <128, so any value that returns at all is all-ASCII. The all-ASCII Ensures is therefore not merely fuzz-supported but structurally necessary — the strongest form this A-leg can take.
4. Type-refinement legs (R) spot-checked live: '漢字'->'xn--p8s937b', 'example'->'example', 'EXAMPLE'->'EXAMPLE' (case preserved), 'muenchen with umlaut'->'xn--mnchen-3ya', 'xn--p8s937b' idempotent — consistent with the str <-> List[int] code-point carrier and with modeling socket.getfqdn's RETURN as the input (the F2P mocks exactly that return).

RESIDUAL RISK (advisory, NOT a break — every candidate patch resolved, so this does not meet the BROKEN bar). Two disclosed-but-real scope limits, both already argued in refinement.md and both invisible to this instance's 1 F2P + 148 P2P:

(a) EXCEPTION IDENTITY (atk_7). refinement.md A3 says the spec pins only WHICH outcome occurred, not the exception's type. But four live sites catch `except UnicodeError` specifically (validators.py 2 arms, html.py 2 arms), so a refinement that signals a non-UnicodeError out of punycode — which the spec permits and which I materialized and confirmed still resolves — would change those arms' control flow. No test in this set drives an ill-formed IDN label into them.

(b) Section C's "pure callee extraction" wording is imprecise for ONE of the four swaps. I measured it: at sanitize_address the gold DELETES the `try: domain.encode('ascii') except UnicodeEncodeError:` guard, so pre-swap vs post-swap diverge on ASCII-but-ill-formed labels — 'a..b', '.b', 'a'*64 all returned verbatim before and raise UnicodeError after. The other three swaps are true extractions (the try/except is preserved verbatim around the call). The doc's own C paragraph and A3 do disclose the totality/control-flow reasoning, and this behaviour change is arguably the intended hardening, but calling all four "pure callee extractions... introduces no new observable behaviour" overstates it for message.py. Documentation precision, not a spec hole — no F2P/P2P test reaches it (test_sanitize_address_invalid raises ValueError during Address parsing, independent of the codec).

**COMPLETENESS.** 16 attacks encoded and fully verified (>= 5 floor met with 11 rejections + 5 candidates), prepatch bug reproduced and rejected, positive control verifies, vacuity and divergence controls both reject, all 5 candidate patches materialized and resolve-checked to completion (no timeouts, no infra failures, no inconclusive runs), plus one extra map-scope resolve. Nothing was left speculative. Scratch: (atk_N.py, atk_N.weakness.txt, atk_N.patch, atk_N.resolve.json, atk_min.patch, positive_control.py, model_frozen.py). The git worktree used to author the patches was removed after use.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Reference: fresh worktree from the upstream repository at base_commit a5308514fb4bc5086c9a16a8a24a945eeebb073c with the gold patch (data/swe_bench_verified/test.jsonl `patch`, byte-identical to gold_11532.diff) APPLIED, per the brief. No bundle files touched.

### WHAT THE SPEC CLAIMS (model.py):
(1) ascii_compatible_domain(domain) == punycode(domain) = domain.encode('idna').decode('ascii'): normal return implies valid_label(ToSeq(domain)) and ToSeq(Result())==ace_seq(ToSeq(domain)) and all_ascii(ToSeq(Result())); otherwise LabelNotEncodable with the input unchanged and not valid_label.
(2) cached_host_name(platform_name) == CachedDnsName.get_fqdn with socket.getfqdn() -> platform_name: same complementary pair, i.e. the cached value is the all-ASCII ACE of the platform name and nothing is cached for a name with no ACE.

### CHECKS RUN (all against the patch-applied worktree):

1. Spec region integrity. `python -m swebench_unified.markers same_spec model.py model_prepatch.py` -> exit 0; `adversary same-spec` on a verbatim copy of model.py -> exit 0 ("SAME — attack shares the bundle's exact specification"). The spec region is what I audited.

2. Verifier, both directions. scripts/nagini_verify.sh model.py -> "Verification successful", exit 0 (15.7s). scripts/nagini_verify.sh model_prepatch.py -> exit 1, "Postcondition of cached_host_name might not hold. Assertion valid_label(ToSeq(platform_name)) might not hold" — the spec is non-vacuous and senses the pre-patch bug (G-DIFF live).

3. G-AX -> exit 0 (24 boundary + 40000 fuzz labels; 27169 value-yielding, 12855 out-of-band, both tallies non-empty).

4. G-CONF -> exit 0 with PYTHONPATH=the patched worktree: 100036 inputs (36 boundary + 100000 fuzz, seed 115320), 80080 value-yielding / 19956 out-of-band, zero disagreements. Both halves of the partition non-vacuous, and each side independently confirmed against the stdlib codec rather than used to skip the repo call.

5. Independent over-claim hunt (my own probes, not the bundle's). I attacked the three strongest clauses:
   a. all_ascii(Result()) — 500k+ inputs through the REAL patched django.utils.encoding.punycode: 300k random strings over the FULL Unicode range chr(0..0x10FFFF), 100k dotted 1-4-label combinations, 100k over an adversarial alphabet (surrogates, U+00AD SOFT HYPHEN, U+200B ZWSP, ideographic/fullwidth dots U+3002/U+FF0E/U+FF61, 'xn--' prefixes, oversize labels, NUL, 100k-char inputs). Zero non-ASCII results. Reading Lib/encodings/idna.py confirms this is structural, not luck: the final step is.decode('ascii'), which cannot return a non-ASCII code point.

   b. Exsures exception channel — the clause is stated over LabelNotEncodable only, so a real raise of any OTHER type would be an unmodelled outcome and hence a faithfulness break. Same 500k-input sweep plus a separate full-BMP-and-beyond single-codepoint sweep (all 0x110000 code points): the real punycode raised nothing but UnicodeError. Codec.encode's only raise sites (Lib/encodings/idna.py: "unsupported error handling", "label empty or too long", "label too long", and ToASCII/nameprep's "Invalid character", "Violation of BIDI requirement 2/3", "Label starts with ACE prefix") are all UnicodeError. The mapping documents LabelNotEncodable as carrying exactly that condition and explicitly pins no type identity or message — the only reason it is user-defined is that a builtin in an Exsures crashes the Nagini translator.

   c. Ensures(valid_label(ToSeq(domain))) on normal return — the strongest clause, since it forbids the real callee from ever answering an un-encodable label with a substitute value. The classifier in both gates is the stdlib expression itself, so this is a tautology on the transform; I checked the composed site B separately, where it is a real claim: with socket.getfqdn stubbed to 'a..b' (no ACE), the real CachedDnsName().get_fqdn() raises UnicodeError and hasattr(c,'`_fqdn`') is False — nothing is cached, matching Exsures. With '漢字' it caches 'xn--p8s937b', matching Ensures + the pinned witness.

6. Witness value. Real punycode('漢字') == 'xn--p8s937b' == code points [120,110,45,45,112,56,115,57,51,55,98] == seq_ace_witness(). Exact.

### Non-defects I considered and rejected
- punycode('') == '' (Codec.encode short-circuits `if not input`). Not a divergence: valid_label('') is true, ace_seq('')=='' and all_ascii(()) is vacuously true, so the spec's normal-return branch is what the real callee takes. The spec does not claim the empty label has no ACE.
- Case is NOT folded on the ASCII fast path ('EXAMPLE' -> 'EXAMPLE', 'AB.漢字' -> 'AB.xn--p8s937b'). The spec says only "a purely-ASCII label is returned in ASCII form unchanged in content" and pins the value via ace_seq (the real callee), never via a lowercasing claim — so no over-claim. Ditto 'ss.DE' for 'ss.DE' input case-mixing.
- punycode returns the SAME str object for short/interned ASCII inputs ('a', ''), while ace_encode's Ensures(Acc(list_pred(Result()))) reads as a fresh list. This is a refinement artifact of str immutability, not observable behavior: the caller cannot mutate a str, so freshness is unobservable on the repo side and cannot produce a diverging input. mapping.md §2 documents the str<->List[int] value bijection, which is what the postconditions are stated over.
- The four un-modelled call-site swaps (message.py, validators.py x2, html.py x2) are pure callee extractions of the identical expression and are covered by the same axiom; the one F2P-observable change is site B, which IS modelled. Not a faithfulness issue for the modelled functions.

ONE LIMITATION, DISCLOSED: I could not execute the F2P test (mail.tests.MailTests.test_non_ascii_dns_non_unicode_email) in this worktree — tests/runtests.py picks up a foreign django from a stale sys.path entry () and dies on ImportError: RemovedInDjango31Warning. This is an environment issue in my scratch worktree, not a bundle or spec defect, and G-RESOLVE is not this gate's burden; the behavior the test observes (the cached FQDN being 'xn--p8s937b' rather than the raw '漢字') I confirmed directly against the real CachedDnsName in check 5c.

**CONCLUSION:** I could not construct an input on which the modelled functions disagree with the real patched callees. Every postcondition is either structurally entailed by.decode('ascii') (all_ascii), pinned to the real callee rather than an oracle constant (ace_seq), or a complementary partition that the real codec and the real get_fqdn both honour (valid_label / Exsures). The spec is not too strong and does not drift. FAITHFUL, with no diverging input.

**Reference:** fresh worktree from the upstream repository at base_commit a5308514fb4bc5086c9a16a8a24a945eeebb073c with the gold patch (data/swe_bench_verified/test.jsonl `patch`, byte-identical to gold_11532.diff) APPLIED, per the brief. No bundle files touched.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** ROLE: attacker (3) leakage / gold-reconstruction, django__django-11532 nagini. Judged the CONSUMER spec view ONLY, computed by me from source: markers.spec_view(model.py, get_backend('nagini')), sha256 = df8ac8276bf13086d32b2b759d102e7ac0e1b08e829ed1a970a24e6224f27482. That MATCHES the recorded gates['G-HYGIENE'].data.region_hashes.spec_view for the current model.py (it does NOT match the e0bc67... hash quoted in an earlier panel note in verdict.md/meta, i.e. the model has been revised since that note -- so I did not and could not have inherited that note's measurement; everything below is my own re-run). mapping.md / refinement.md / verdict.md / meta.json / axiom_check.py / conformance_check.py are audit-side artifacts, NOT part of the consumer view; I confirmed the one non-public implementation token (`.encode('idna').decode('ascii')`) appears only there and never in the view.

**RELAXATION STATUS:** NONE. `meta.json` has no `relaxed_leakage` key (top-level key list: additional_change_sites, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version -- and a /relax/i glob over the whole bundle dir returned nothing), and there is no RELAXED_LEAKAGE.md. meta gates['G-LEAK'].status == 'pass', not 'relaxed'. So there was no unavoidability argument to re-derive; this is an ordinary STRICT leakage review, and I applied the strict standard throughout.

BUNDLE-ADDRESSES-REVIEWER CHECK (reported as its own finding per the brief): NEGATIVE. I ran leakage.reviewer_directed() over every.md/.py/.json/.txt/.diff file in the bundle -- zero hits. No file instructs me how to record or which verdict is honest. verdict.md contains only prior gate records; I treated them as claims, not dispositions.

### What I measured
1) Mechanical screen re-run from source: leakage.screen(model.py, nagini.language, row['patch'], row['problem_statement'], test_patch) -> passed=True, hard_failures=[], warnings=[].
2) Diff markers: '@@', 'diff --git', '+++ ', '--- ', '\nindex ' -- all absent from the view.
3) Reproduced gold lines: `_patch_changed_lines` x normalized view, len>=8 -> [] (zero).
4) Patched paths/modules: 'django/core/mail/utils.py', 'django/utils/encoding.py', 'message.py', 'validators.py', 'html.py', bare 'django/' and 'django.' -- none appear anywhere in the view.
5) Symbol collision: patch changed def/class symbols = {punycode, sanitize_address, is_email_simple, unquote_quote, escape_uri_path}; view identifiers = {ascii_compatible_domain, cached_host_name, ace_seq, ace_encode, valid_label, all_ascii, seq_host_witness, seq_ace_witness, domain, platform_name, LabelNotEncodable, + Nagini builtins}. Underscore-stripped substring cross-product: ZERO collisions; and no view comment/docstring names any of those symbols (word-boundary regex over the tokenized comment/string set). In particular `punycode` -- the gold's new helper name -- appears NOWHERE in the view (case-insensitive substring), even though it would have been screen-exempt since the public problem_statement names it.
6) Narration: `_NARRATION_RE` over every view line -> zero hits (no bug/fix/patch/previously/incorrectly/broken/...).
7) HINTS-ONLY LEAK CHECK (the screen's blind spot): tokens that live in hints_text but NOT in problem_statement -- 'idna', '`_fqdn`', 'getfqdn', "decode('ascii')" -- are ALL absent from the view. So the view does not smuggle in the hint's diff. No hints_text was used in judging.
8) BEYOND-PROBLEM_STATEMENT TEST (the substantive question). The view discloses exactly one facet: desired behaviour -- (a) a transform yielding the all-ASCII ACE/ToASCII of a domain label, witness U+6F22 U+5B57 -> the 11 code points spelling xn--p8s937b, and (b) the cached host name is that transform applied to the platform-reported name, with the codec's out-of-band condition propagating. Each of those is already SOLVER-VISIBLE in the public problem_statement, which I substring-checked: it contains verbatim "Fix: have django.core.mail.utils or django.core.mail.message convert domain name to punycode before using" (naming BOTH the transform and the target module -- localization the view withholds), the unicode hostnames 正宗/漢字, the expected output token `xn--p8s937b`, `iso-8859-1`, `DNS_NAME`, `Message-ID`, and the ascii/latin-1 UnicodeEncodeError traceback. The view is therefore STRICTLY WEAKER in localization than the public text: it states punycode-as-ACE behaviour without naming punycode, the file, the module, or the codec call. The only view vocabulary not in the problem_statement ('reusable', 'cached', 'out of band', 'complementary', 'ToASCII', 'witness') is behavioural/spec-structural abstraction, not edit localization -- none of it names a repo symbol, file, or code line, and 'ToASCII' is the RFC name of the standard operation the public text calls 'punycode'.
9) SOUNDNESS OF THE UNDERLYING CELL (so a clean leak verdict is not resting on a vacuous spec): same-spec on a copy of the bundle model -> exit 0 ("SAME"), so the region I judged is the frozen spec. Pinned verifier on the gold model.py -> "Verification successful" (15.9s). model_prepatch.py (caches the raw platform name) FAILS: `model_prepatch.py:187: Postcondition of cached_host_name might not hold. Assertion valid_label(ToSeq(platform_name)) might not hold.` markers.same_spec(model, model_prepatch) -> True, so they share the spec byte-for-byte and differ only in impl. STRIP TEST (the load-bearing test): deleting the three discriminating clauses from cached_host_name -- Ensures(valid_label(ToSeq(platform_name))), Ensures(ToSeq(Result()) == ace_seq(ToSeq(platform_name))), Ensures(all_ascii(ToSeq(Result()))) -- makes the PRE-patch impl verify ("Verification successful", 14.2s, strip_pre.py). Those clauses are therefore load-bearing content, not decorative narration that could be deleted to reduce disclosure.

BOOKKEEPING OBSERVATION (not leakage, recorded for the trail): meta.json's TOP-LEVEL `region_hashes` block (spec_view 471ae14a..., axioms 7391...) disagrees with what I compute from the current model.py (spec_view df8ac827..., axioms 62cd8781...), while gates['G-HYGIENE'].data.region_hashes matches me exactly. No gate reads the top-level copy (grep over gates/: only hygiene.py recomputes), so it is a stale artifact rather than a defect, but it would mislead anyone diffing that block.

**CONCLUSION:** NO-LEAKAGE. No leaking line to cite: the single facet the spec view discloses -- the all-ASCII ACE outcome for the cached host name plus the 漢字 -> xn--p8s937b witness -- is fully subsumed by the public problem_statement, which names punycode and the target module outright, and the view names neither.

**ROLE:** attacker (3) leakage / gold-reconstruction, django__django-11532 nagini. Judged the CONSUMER spec view ONLY, computed by me from source: markers.spec_view(model.py, get_backend('nagini')), sha256 = df8ac8276bf13086d32b2b759d102e7ac0e1b08e829ed1a970a24e6224f27482. That MATCHES the recorded gates['G-HYGIENE'].data.region_hashes.spec_view for the current model.py (it does NOT match the e0bc67... hash quoted in an earlier panel note in verdict.md/meta, i.e. the model has been revised since that note -- so I did not and could not have inherited that note's measurement; everything below is my own re-run). mapping.md / refinement.md / verdict.md / meta.json / axiom_check.py / conformance_check.py are audit-side artifacts, NOT part of the consumer view; I confirmed the one non-public implementation token (`.encode('idna').decode('ascii')`) appears only there and never in the view.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
