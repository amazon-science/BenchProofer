# P2 adversarial audit — psf__requests-1766

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 15 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_0_prepatch.lean`, `atk_1_single_quote.lean`, `atk_2_no_tail_quote.lean`, `atk_3_swap_values.lean`, `atk_4_partial_domain.lean`, `atk_5_control_flow.lean`, `atk_7_nonterminating.lean`, `atk_8_uppercase_token.lean`, `atk_9_partial_base.lean`, `atk_10_doubled_quotes.lean`, `atk_11_effect_order.lean`, +3 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6_oracle_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl found. 14 same-spec attacks were machine-checked; exactly one (atk_6_oracle_echo, the ungrounded-oracle echo `return base ++ qopSegment ncvalue cnonce`) verifies, and it is NOT a wrong impl: qopSegment is a deep constant-character model of the gold format string, so its faithful refined patch IS the gold change at requests/auth.py:147. That patch was materialized and executed through the official harness and RESOLVED (6/6 FAIL_TO_PASS, 80/80 PASS_TO_PASS, 0 PASS_TO_FAIL). verify ⇒ resolved holds on every probe attempted.
```

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_0_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,9 +61,10 @@
   do
     -- impl-start
     let mut result : List Char := base
-    -- ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
+    -- Pre-image skeleton: the quality-of-protection value is emitted BARE
+    -- (', qop=auth, nc='), without the surrounding double quotes.
     result := result ++ [',', ' ', 'q', 'o', 'p', '=']
-    result := result ++ ['"', 'a', 'u', 't', 'h', '"']
+    result := result ++ ['a', 'u', 't', 'h']
     result := result ++ [',', ' ', 'n', 'c', '=']
     -- the count value, bare (no surrounding quotes)
     result := result ++ ncvalue
```

Attack 2 — `atk_1_single_quote.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,17 +61,14 @@
   do
     -- impl-start
     let mut result : List Char := base
-    -- ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
     result := result ++ [',', ' ', 'q', 'o', 'p', '=']
-    result := result ++ ['"', 'a', 'u', 't', 'h', '"']
+    -- WRONG: value wrapped in SINGLE quotes, so the header contains 'auth'
+    -- and NOT the double-quoted "auth" the F2P test greps for.
+    result := result ++ ['\'', 'a', 'u', 't', 'h', '\'']
     result := result ++ [',', ' ', 'n', 'c', '=']
-    -- the count value, bare (no surrounding quotes)
     result := result ++ ncvalue
-    -- ', cnonce="'
     result := result ++ [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '"']
-    -- the client-nonce value
     result := result ++ cnonce
-    -- closing double quote
     result := result ++ ['"']
     return result
     -- impl-end
```

Attack 3 — `atk_2_no_tail_quote.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,18 +61,14 @@
   do
     -- impl-start
     let mut result : List Char := base
-    -- ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
     result := result ++ [',', ' ', 'q', 'o', 'p', '=']
     result := result ++ ['"', 'a', 'u', 't', 'h', '"']
     result := result ++ [',', ' ', 'n', 'c', '=']
-    -- the count value, bare (no surrounding quotes)
     result := result ++ ncvalue
-    -- ', cnonce="'
     result := result ++ [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '"']
-    -- the client-nonce value
     result := result ++ cnonce
-    -- closing double quote
-    result := result ++ ['"']
+    -- WRONG (boundary): the closing double quote of the client-nonce value is
+    -- never appended, so the emitted credential is malformed.
     return result
     -- impl-end
 
```

Attack 4 — `atk_3_swap_values.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,17 +61,14 @@
   do
     -- impl-start
     let mut result : List Char := base
-    -- ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
     result := result ++ [',', ' ', 'q', 'o', 'p', '=']
     result := result ++ ['"', 'a', 'u', 't', 'h', '"']
     result := result ++ [',', ' ', 'n', 'c', '=']
-    -- the count value, bare (no surrounding quotes)
+    -- WRONG: the client-nonce is emitted where the count value belongs ...
+    result := result ++ cnonce
+    result := result ++ [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '"']
+    -- ... and the count value where the client-nonce belongs.
     result := result ++ ncvalue
-    -- ', cnonce="'
-    result := result ++ [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '"']
-    -- the client-nonce value
-    result := result ++ cnonce
-    -- closing double quote
     result := result ++ ['"']
     return result
     -- impl-end
```

Attack 5 — `atk_4_partial_domain.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,20 +60,16 @@
   ensures (directiveHead.take (6 + quotedValueToken.length)).drop 6 = quotedValueToken
   do
     -- impl-start
-    let mut result : List Char := base
-    -- ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
-    result := result ++ [',', ' ', 'q', 'o', 'p', '=']
-    result := result ++ ['"', 'a', 'u', 't', 'h', '"']
-    result := result ++ [',', ' ', 'n', 'c', '=']
-    -- the count value, bare (no surrounding quotes)
-    result := result ++ ncvalue
-    -- ', cnonce="'
-    result := result ++ [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '"']
-    -- the client-nonce value
-    result := result ++ cnonce
-    -- closing double quote
-    result := result ++ ['"']
-    return result
+    -- PARTIAL DOMAIN: agrees with the gold segment whenever both tokens are
+    -- non-empty (which is all the real caller ever passes: ncvalue is the
+    -- 8-char '%08x' count, cnonce the 16-char sha1 prefix), but emits the
+    -- BARE pre-patch value on the empty-token corner the tests never reach.
+    if ncvalue = [] || cnonce = [] then
+      return base ++ [',', ' ', 'q', 'o', 'p', '='] ++ ['a', 'u', 't', 'h']
+        ++ [',', ' ', 'n', 'c', '='] ++ ncvalue
+        ++ [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '"'] ++ cnonce ++ ['"']
+    else
+      return base ++ qopSegment ncvalue cnonce
     -- impl-end
 
 prove_correct appendQopDirective by
```

Attack 6 — `atk_5_control_flow.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,19 +60,17 @@
   ensures (directiveHead.take (6 + quotedValueToken.length)).drop 6 = quotedValueToken
   do
     -- impl-start
+    -- CONTROL-FLOW EFFECT: a length guard mis-decides whether the closing
+    -- quote is still owed. For a client-nonce of 8 characters or more -- which
+    -- is every real cnonce (a 16-char sha1 prefix) -- the closing quote is
+    -- skipped, truncating the credential.
     let mut result : List Char := base
-    -- ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
-    result := result ++ [',', ' ', 'q', 'o', 'p', '=']
-    result := result ++ ['"', 'a', 'u', 't', 'h', '"']
-    result := result ++ [',', ' ', 'n', 'c', '=']
-    -- the count value, bare (no surrounding quotes)
+    result := result ++ directiveHead
     result := result ++ ncvalue
-    -- ', cnonce="'
-    result := result ++ [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '"']
-    -- the client-nonce value
+    result := result ++ directiveMid
     result := result ++ cnonce
-    -- closing double quote
-    result := result ++ ['"']
+    if cnonce.length < 8 then
+      result := result ++ directiveTail
     return result
     -- impl-end
 
```

Attack 7 — `atk_6_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -60,20 +60,9 @@
   ensures (directiveHead.take (6 + quotedValueToken.length)).drop 6 = quotedValueToken
   do
     -- impl-start
-    let mut result : List Char := base
-    -- ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
-    result := result ++ [',', ' ', 'q', 'o', 'p', '=']
-    result := result ++ ['"', 'a', 'u', 't', 'h', '"']
-    result := result ++ [',', ' ', 'n', 'c', '=']
-    -- the count value, bare (no surrounding quotes)
-    result := result ++ ncvalue
-    -- ', cnonce="'
-    result := result ++ [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '"']
-    -- the client-nonce value
-    result := result ++ cnonce
-    -- closing double quote
-    result := result ++ ['"']
-    return result
+    -- UNGROUNDED ORACLE ECHO: no assembly at all; the impl simply replays the
+    -- postcondition's right-hand side verbatim.
+    return base ++ qopSegment ncvalue cnonce
     -- impl-end
 
 prove_correct appendQopDirective by
```

Attack 8 — `atk_7_nonterminating.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,20 +60,18 @@
   ensures (directiveHead.take (6 + quotedValueToken.length)).drop 6 = quotedValueToken
   do
     -- impl-start
-    let mut result : List Char := base
-    -- ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
-    result := result ++ [',', ' ', 'q', 'o', 'p', '=']
-    result := result ++ ['"', 'a', 'u', 't', 'h', '"']
-    result := result ++ [',', ' ', 'n', 'c', '=']
-    -- the count value, bare (no surrounding quotes)
-    result := result ++ ncvalue
-    -- ', cnonce="'
-    result := result ++ [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '"']
-    -- the client-nonce value
-    result := result ++ cnonce
-    -- closing double quote
-    result := result ++ ['"']
-    return result
+    -- VACUITY / TOTALITY PROBE: the guard `i < i + 1` is universally true and
+    -- the measure is constant, so this loop diverges on every input. Under
+    -- loom.semantics.termination = "total" it must be REJECTED; were it
+    -- accepted, every ensures clause would be vacuously satisfiable.
+    let mut i : Nat := 0
+    while i < i + 1
+      invariant True
+      done_with i < i
+      decreasing i
+    do
+      i := i + 1
+    return base ++ qopSegment ncvalue cnonce
     -- impl-end
 
 prove_correct appendQopDirective by
```

Attack 9 — `atk_8_uppercase_token.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,17 +61,14 @@
   do
     -- impl-start
     let mut result : List Char := base
-    -- ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
     result := result ++ [',', ' ', 'q', 'o', 'p', '=']
-    result := result ++ ['"', 'a', 'u', 't', 'h', '"']
+    -- WRONG: the value token is capitalised, so the byte-exact substring
+    -- '"auth"' the F2P test asserts is absent from the header.
+    result := result ++ ['"', 'A', 'u', 't', 'h', '"']
     result := result ++ [',', ' ', 'n', 'c', '=']
-    -- the count value, bare (no surrounding quotes)
     result := result ++ ncvalue
-    -- ', cnonce="'
     result := result ++ [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '"']
-    -- the client-nonce value
     result := result ++ cnonce
-    -- closing double quote
     result := result ++ ['"']
     return result
     -- impl-end
```

Attack 10 — `atk_9_partial_base.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,20 +60,17 @@
   ensures (directiveHead.take (6 + quotedValueToken.length)).drop 6 = quotedValueToken
   do
     -- impl-start
-    let mut result : List Char := base
-    -- ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
-    result := result ++ [',', ' ', 'q', 'o', 'p', '=']
-    result := result ++ ['"', 'a', 'u', 't', 'h', '"']
-    result := result ++ [',', ' ', 'n', 'c', '=']
-    -- the count value, bare (no surrounding quotes)
-    result := result ++ ncvalue
-    -- ', cnonce="'
-    result := result ++ [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '"']
-    -- the client-nonce value
-    result := result ++ cnonce
-    -- closing double quote
-    result := result ++ ['"']
-    return result
+    -- PARTIAL DOMAIN (base boundary): agrees with gold whenever `base` is
+    -- non-empty -- which is every call the real caller makes, since `base`
+    -- always already carries username="..."/realm="..."/nonce="..."/uri="..."
+    -- /response="..." -- but reverts to the BARE pre-patch value on the
+    -- empty-base corner no test can reach.
+    if base = [] then
+      return [',', ' ', 'q', 'o', 'p', '='] ++ ['a', 'u', 't', 'h']
+        ++ [',', ' ', 'n', 'c', '='] ++ ncvalue
+        ++ [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '"'] ++ cnonce ++ ['"']
+    else
+      return base ++ qopSegment ncvalue cnonce
     -- impl-end
 
 prove_correct appendQopDirective by
```

Attack 11 — `atk_10_doubled_quotes.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,17 +61,15 @@
   do
     -- impl-start
     let mut result : List Char := base
-    -- ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
     result := result ++ [',', ' ', 'q', 'o', 'p', '=']
-    result := result ++ ['"', 'a', 'u', 't', 'h', '"']
+    -- WRONG but F2P-SUBSTRING-SATISFYING: the value is wrapped in DOUBLED
+    -- double quotes, so the header still contains the substring '\"auth\"'
+    -- the F2P test greps for, while differing from the gold credential.
+    result := result ++ ['"', '"', 'a', 'u', 't', 'h', '"', '"']
     result := result ++ [',', ' ', 'n', 'c', '=']
-    -- the count value, bare (no surrounding quotes)
     result := result ++ ncvalue
-    -- ', cnonce="'
     result := result ++ [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '"']
-    -- the client-nonce value
     result := result ++ cnonce
-    -- closing double quote
     result := result ++ ['"']
     return result
     -- impl-end
```

Attack 12 — `atk_11_effect_order.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,18 +61,15 @@
   do
     -- impl-start
     let mut result : List Char := base
-    -- ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
-    result := result ++ [',', ' ', 'q', 'o', 'p', '=']
-    result := result ++ ['"', 'a', 'u', 't', 'h', '"']
-    result := result ++ [',', ' ', 'n', 'c', '=']
-    -- the count value, bare (no surrounding quotes)
+    -- CONTROL-FLOW / EFFECT-ORDER BUG: every literal piece and both value
+    -- tokens are appended exactly once (same characters, same count as gold),
+    -- but the count value is appended BEFORE the literal head, so the pieces
+    -- land in the wrong order.
     result := result ++ ncvalue
-    -- ', cnonce="'
-    result := result ++ [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '"']
-    -- the client-nonce value
+    result := result ++ directiveHead
+    result := result ++ directiveMid
     result := result ++ cnonce
-    -- closing double quote
-    result := result ++ ['"']
+    result := result ++ directiveTail
     return result
     -- impl-end
 
```

Attack 13 — `atk_12_wrong_token.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,17 +61,15 @@
   do
     -- impl-start
     let mut result : List Char := base
-    -- ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
     result := result ++ [',', ' ', 'q', 'o', 'p', '=']
-    result := result ++ ['"', 'a', 'u', 't', 'h', '"']
+    -- WRONG: correctly QUOTED, but the token inside is `auth-int`, a
+    -- protection level this client does not implement. Probes whether the
+    -- spec pins the token's content and not merely the surrounding quotes.
+    result := result ++ ['"', 'a', 'u', 't', 'h', '-', 'i', 'n', 't', '"']
     result := result ++ [',', ' ', 'n', 'c', '=']
-    -- the count value, bare (no surrounding quotes)
     result := result ++ ncvalue
-    -- ', cnonce="'
     result := result ++ [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '"']
-    -- the client-nonce value
     result := result ++ cnonce
-    -- closing double quote
     result := result ++ ['"']
     return result
     -- impl-end
```

Attack 14 — `atk_13_base_clobber.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,20 +60,10 @@
   ensures (directiveHead.take (6 + quotedValueToken.length)).drop 6 = quotedValueToken
   do
     -- impl-start
-    let mut result : List Char := base
-    -- ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
-    result := result ++ [',', ' ', 'q', 'o', 'p', '=']
-    result := result ++ ['"', 'a', 'u', 't', 'h', '"']
-    result := result ++ [',', ' ', 'n', 'c', '=']
-    -- the count value, bare (no surrounding quotes)
-    result := result ++ ncvalue
-    -- ', cnonce="'
-    result := result ++ [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '"']
-    -- the client-nonce value
-    result := result ++ cnonce
-    -- closing double quote
-    result := result ++ ['"']
-    return result
+    -- BOUNDARY: the appended suffix is byte-perfect gold, but the credential
+    -- already built by the caller is truncated by one character first --
+    -- modelling a `base = base[:-1] + suffix` slip at the assembly site.
+    return base.take (base.length - 1) ++ qopSegment ncvalue cnonce
     -- impl-end
 
 prove_correct appendQopDirective by
```

Attack 15 — `atk_14_partial_ncwidth.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,20 +60,16 @@
   ensures (directiveHead.take (6 + quotedValueToken.length)).drop 6 = quotedValueToken
   do
     -- impl-start
-    let mut result : List Char := base
-    -- ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
-    result := result ++ [',', ' ', 'q', 'o', 'p', '=']
-    result := result ++ ['"', 'a', 'u', 't', 'h', '"']
-    result := result ++ [',', ' ', 'n', 'c', '=']
-    -- the count value, bare (no surrounding quotes)
-    result := result ++ ncvalue
-    -- ', cnonce="'
-    result := result ++ [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '"']
-    -- the client-nonce value
-    result := result ++ cnonce
-    -- closing double quote
-    result := result ++ ['"']
-    return result
+    -- PARTIAL DOMAIN keyed on the count token's REAL width: the caller always
+    -- passes ncvalue = '%08x' % nonce_count, exactly 8 characters, so this
+    -- impl is byte-identical to gold on every input any test can produce,
+    -- while emitting the BARE pre-patch value on all other widths.
+    if ncvalue.length = 8 then
+      return base ++ qopSegment ncvalue cnonce
+    else
+      return base ++ [',', ' ', 'q', 'o', 'p', '='] ++ ['a', 'u', 't', 'h']
+        ++ [',', ' ', 'n', 'c', '='] ++ ncvalue
+        ++ [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '"'] ++ cnonce ++ ['"']
     -- impl-end
 
 prove_correct appendQopDirective by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (none — the protection-directive segment is assembled deeply from the
--  caller-supplied count/client-nonce sequences and constant character
--  literals; no opaque library callee is invoked on this path, so there is
--  nothing to axiomatize or G-AX-check.)
-- axioms-end

-- pure-start
/- The quality-of-protection value emitted as a QUOTED string: an opening
   double quote, the four characters of the token `auth`, and a closing double
   quote. This is the value form RFC 2617 mandates for the qop-options
   directive (a quoted string of tokens) rather than a bare token. -/
def quotedValueToken : List Char := ['"', 'a', 'u', 't', 'h', '"']

/- The literal head of the directive segment up to the count value:
   `, qop=` then the QUOTED value token then `, nc=`. -/
def directiveHead : List Char :=
  [',', ' ', 'q', 'o', 'p', '='] ++ quotedValueToken ++ [',', ' ', 'n', 'c', '=']

/- The literal between the count value and the client-nonce value:
   `, cnonce="` (the client-nonce being a quoted string as well). -/
def directiveMid : List Char := [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '"']

/- The literal closing the client-nonce value: a single double quote. -/
def directiveTail : List Char := ['"']

/- The whole directive segment appended when a quality-of-protection token is
   present: the literal head (carrying the QUOTED value token `"auth"`), the
   count value emitted bare, the literal mid, the client-nonce value, and the
   closing quote. -/
def qopSegment (ncvalue cnonce : List Char) : List Char :=
  directiveHead ++ ncvalue ++ directiveMid ++ cnonce ++ directiveTail

@[grind] lemma directiveHead_def :
    directiveHead =
      [',', ' ', 'q', 'o', 'p', '='] ++ quotedValueToken ++ [',', ' ', 'n', 'c', '='] := rfl

@[grind] lemma qopSegment_def (ncvalue cnonce : List Char) :
    qopSegment ncvalue cnonce =
      directiveHead ++ ncvalue ++ directiveMid ++ cnonce ++ directiveTail := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method appendQopDirective (base : List Char) (ncvalue : List Char) (cnonce : List Char) return (out : List Char)
  ensures out = base ++ qopSegment ncvalue cnonce
  ensures (out.drop base.length).take directiveHead.length = directiveHead
  ensures (directiveHead.take (6 + quotedValueToken.length)).drop 6 = quotedValueToken
  do
    -- impl-start
    let mut result : List Char := base
    -- ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
    result := result ++ [',', ' ', 'q', 'o', 'p', '=']
    result := result ++ ['"', 'a', 'u', 't', 'h', '"']
    result := result ++ [',', ' ', 'n', 'c', '=']
    -- the count value, bare (no surrounding quotes)
    result := result ++ ncvalue
    -- ', cnonce="'
    result := result ++ [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '"']
    -- the client-nonce value
    result := result ++ cnonce
    -- closing double quote
    result := result ++ ['"']
    return result
    -- impl-end

prove_correct appendQopDirective by
  loom_solve <;> simp_all [qopSegment, directiveHead, directiveMid, directiveTail, quotedValueToken]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for psf__requests-1766 / velvet. All work The prior pass's worktree had been reaped, so a fresh worktree was created at base_commit 847735553aeda6e6633f2b32e14ba14ba86887a4 from the upstream repository and used to read the real pre-patch site.

SAME-SPEC: all 15 files (14 attacks + positive control) return same_spec(...)=True against the frozen bundle Solution.lean via `python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open(<bundle>/Solution.lean).read(), open(<atk>).read(), b.language))"`. Only the impl region was ever edited.

POSITIVE CONTROL: pos_control.lean (= bundle Solution.lean verbatim). `bash scripts/lean_verify.sh pos_control.lean` -> exit 0 (verifies, no sorry). Spec is non-vacuous and satisfiable.

PREPATCH REPRODUCED: atk_0_prepatch.lean (bundle Solution_prepatch.lean, bare `auth`) -> exit 1, failing `ensures_2: (out.drop base.length).take directiveHead.length = directiveHead` and `ensures_3: out = base ++ qopSegment ncvalue cnonce` (both goals reduce to False). G-DIFF is real.

PER-ATTACK RESULTS (command in every case: `bash scripts/lean_verify.sh <path>`, run 4-at-a-time as concurrent background jobs; logs kept <name>.txt):
- atk_0_prepatch.lean — prepatch bare value — exit 1 (REJECTED, ensures_2+ensures_3 -> False)
- atk_1_single_quote.lean — value in SINGLE quotes 'auth' (kills the F2P '\"auth\"' grep) — exit 1 (REJECTED, ensures_2+3 -> False)
- atk_2_no_tail_quote.lean — BOUNDARY: closing double quote of cnonce never appended — exit 1 (REJECTED, ensures_3 -> False)
- atk_3_swap_values.lean — ncvalue/cnonce interpolated into each other's slots — exit 1 (REJECTED; goal shows the two concatenations side by side)
- atk_4_partial_domain.lean — PARTIAL DOMAIN: gold when both tokens non-empty (all real inputs), bare pre-patch value on the empty-token corner — exit 1 (REJECTED under hypothesis `if_pos : ncvalue = [] ∨ cnonce = []`)
- atk_5_control_flow.lean — CONTROL-FLOW EFFECT: length guard `if cnonce.length < 8` skips the closing quote for every real 16-char cnonce — exit 1 (REJECTED under `if_neg : 8 ≤ cnonce.length`)
- atk_6_oracle_echo.lean — UNGROUNDED-ORACLE ECHO: `return base ++ qopSegment ncvalue cnonce` — exit 0 (VERIFIES) -> faithful patch materialized and resolved, see below
- atk_7_nonterminating.lean — VACUITY/TOTALITY probe: guard `i < i + 1` with constant measure — exit 1 (REJECTED on `case decreasing_1: i`). Confirms loom.semantics.termination="total" is enforced; the postconditions are not vacuously satisfiable by divergence.
- atk_8_uppercase_token.lean — quoted but capitalised '\"Auth\"' — exit 1 (REJECTED, ensures_2+3 -> False)
- atk_9_partial_base.lean — PARTIAL DOMAIN at the base boundary: gold when base non-empty (every real call), bare value when base = [] — exit 1 (REJECTED under `if_pos : base = []`)
- atk_10_doubled_quotes.lean — '\"\"auth\"\"': still CONTAINS the F2P substring '\"auth\"' yet differs from gold — exit 1 (REJECTED, ensures_2+3 -> False). Shows the spec is strictly stronger than the F2P substring assertion.
- atk_11_effect_order.lean — EFFECT-ORDER: identical character multiset, ncvalue appended before directiveHead — exit 1 (REJECTED on ensures_2)
- atk_12_wrong_token.lean — correctly quoted but wrong token '\"auth-int\"' — exit 1 (REJECTED, ensures_2+3 -> False). Spec pins token content, not merely the quoting.
- atk_13_base_clobber.lean — BOUNDARY: byte-perfect gold suffix appended to a base truncated by one char — exit 1 (REJECTED on ensures_2)
- atk_14_partial_ncwidth.lean — PARTIAL DOMAIN keyed on the count token's real width (`ncvalue.length = 8`, the '%08x' width every test produces), bare pre-patch value elsewhere — exit 1 (REJECTED under `if_neg : ¬ncvalue.length = 8`)

Two earlier encodings had to be discarded and rewritten because they failed on MY Velvet syntax / loop-invariant automation rather than on the spec (an `Option ℕ` elaboration error, and a `not a triple: _inhabitedExprDummy` panic on a `while`-copy loop); those are not counted as attacks. The surviving atk_5 (branch-based) and atk_7 (termination) are genuine semantic rejections, and atk_11 supplies an independent effect/ordering probe. No attack file was left in an encoding-error state: every submitted rejection cites a real proof obligation.

MANDATORY RESOLVE RUN (protocol step 2). atk_6_oracle_echo is the only verifying impl, so its faithful refined patch was materialized (patch_atk_6.diff) and executed through the official harness: python -c "from swebench_unified.harness import run_resolve; r=run_resolve('psf__requests-1766', open('patch_atk_6.diff').read(), run_id='eqaudit-atk6-djsmxmx8', timeout=1800); print(r.resolved, r.completed, r.flaky, r.note)" OBSERVED: RESOLVED=True COMPLETED=True FLAKY=True NOTE='resolved on attempt 2/3 (flaky: earlier attempt failed or did not complete)'. Report: patch_successfully_applied=True, FAIL_TO_PASS 6/6 success (including test_DIGESTAUTH_QUOTES_QOP_VALUE) / 0 failure, PASS_TO_PASS 80/80 success / 0 failure, PASS_TO_FAIL empty.

The flaky flag is the harness's own network-retry bookkeeping (this instance's tests hit httpbin); the final verdict is resolved, and the 4 other F2P tests in this instance are known network-sensitive. GOLD CONTROL, run concurrently for comparison: run_resolve on the bundle's patch.diff, run_id='eqaudit-gold-djsmxmx8' -> RESOLVED=True COMPLETED=True FLAKY=False NOTE='resolved', identical 6/6 + 80/80 report. Confirms the harness environment was healthy for both runs, so atk_6's resolve is not an artifact of a lenient run. Both patches were also checked to apply cleanly at base_commit with `git apply --check` in the fresh worktree, and after applying patch_atk_6.diff line 147 reads exactly `base += ', qop="auth", nc=%s, cnonce="%s"' % (ncvalue, cnonce)` — the gold post-patch text.

REFINEMENT.MD AUDIT (protocol step 3). Legs A1-A6 are each tagged R, I, or R+I; section C explicitly claims no kind-3 and no axioms. Confirmed against the artifacts: the Solution.lean axioms region is empty (comment only), and meta.json records axioms=[] and deep_model_references=[]. There is therefore NO A-consumed and NO A-reference leg, so the A-leg correspondence obligation and axiom_check.py/G-AX are genuinely vacuous here — not silently skipped.

I checked the one substantive risk this creates: the changed operation could have been hidden behind an opaque callee, but it is not — the discriminating content lives in `quotedValueToken = ['\"','a','u','t','h','\"']` inside `directiveHead`, spelled out as concrete characters and consumed by two of the three postconditions, and %-formatting of a constant template with two %s substitutions is genuinely expressible as sequence concatenation over List Char. So the no-axiom claim is correct rather than an evasion, and there is no dead axiom.

Model↔patch correspondence verified by hand against the real repo at base_commit: pre-patch requests/auth.py:147 is `base += ', qop=auth, nc=%s, cnonce="%s"' % (ncvalue, cnonce)`, and gold rewrites only the value to `"auth"`. qopSegment = directiveHead ++ ncvalue ++ directiveMid ++ cnonce ++ directiveTail spells `, qop="auth", nc=` ++ ncvalue ++ `, cnonce="` ++ cnonce ++ `"` — byte-for-byte the post-patch format string with its two holes filled. Because ncvalue/cnonce are substituted VALUES and not format strings, no %-escaping artifact can diverge between model and callee. mapping.md's symbol table and the str↔List Char carrier bijection match the real code; modeled_functions points at requests/auth.py:146-147, the only functional hunk.

The one modelling gap is disclosed and I confirmed it is harmless: the gold patch's second hunk (requests/auth.py:108) only strips trailing whitespace from a blank line after `A2 = '%s:%s' % (method, path)`. I inspected that line with cat -A in the worktree — it is interior source whitespace inside no string literal, so it changes no emitted credential and no test can observe it. Section B declares it unmodeled; additional_change_sites=[] is consistent. Note that atk_6's faithful patch omits this hunk and still resolved, which empirically confirms the hunk is irrelevant to the oracle. Also worth recording: the postcondition is strictly stronger than the F2P test.

The test only asserts the substring '\"auth\"' is present, whereas `out = base ++ qopSegment ncvalue cnonce` pins the whole credential — which is why atk_10 (doubled quotes, F2P-substring-satisfying) is still rejected. The spec cannot be satisfied by an impl that merely smuggles the substring in.

CONCLUSION: 14 same-spec attacks executed (prepatch + 13 distinct wrong impls spanning partial-domain x3, boundary x2, control-flow/effect x3, ungrounded-oracle echo, vacuity/termination, and value-token variants), well past the >=5 requirement. Thirteen are rejected on genuine proof obligations; the single verifying impl is behaviourally the gold patch and its materialized faithful patch RESOLVED under the official harness alongside a clean gold control. No verify⇏correct witness found. Verdict SOUND (advisory; runner re-runs the artifacts).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 15 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_0_prepatch.lean`, `atk_1_single_quote.lean`, `atk_2_no_tail_quote.lean`, `atk_3_swap_values.lean`, `atk_4_partial_domain.lean`, `atk_5_control_flow.lean`, `atk_7_nonterminating.lean`, `atk_8_uppercase_token.lean`, `atk_9_partial_base.lean`, `atk_10_doubled_quotes.lean`, `atk_11_effect_order.lean`, +3 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6_oracle_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl found. 14 same-spec attacks were machine-checked; exactly one (atk_6_oracle_echo, the ungrounded-oracle echo `return base ++ qopSegment ncvalue cnonce`) verifies, and it is NOT a wrong impl: qopSegment is a deep constant-character model of the gold format string, so its faithful refined patch IS the gold change at requests/auth.py:147. That patch was materialized and executed through the official harness and RESOLVED (6/6 FAIL_TO_PASS, 80/80 PASS_TO_PASS, 0 PASS_TO_FAIL). verify ⇒ resolved holds on every probe attempted.
```

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 15 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_0_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_1_single_quote.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_2_no_tail_quote.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_3_swap_values.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_4_partial_domain.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_5_control_flow.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_6_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_7_nonterminating.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_8_uppercase_token.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_9_partial_base.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_10_doubled_quotes.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_11_effect_order.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_12_wrong_token.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_13_base_clobber.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_14_partial_ncwidth.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (none — the protection-directive segment is assembled deeply from the
--  caller-supplied count/client-nonce sequences and constant character
--  literals; no opaque library callee is invoked on this path, so there is
--  nothing to axiomatize or G-AX-check.)
-- axioms-end

-- pure-start
/- The quality-of-protection value emitted as a QUOTED string: an opening
   double quote, the four characters of the token `auth`, and a closing double
   quote. This is the value form RFC 2617 mandates for the qop-options
   directive (a quoted string of tokens) rather than a bare token. -/
def quotedValueToken : List Char := ['"', 'a', 'u', 't', 'h', '"']

/- The literal head of the directive segment up to the count value:
   `, qop=` then the QUOTED value token then `, nc=`. -/
def directiveHead : List Char :=
  [',', ' ', 'q', 'o', 'p', '='] ++ quotedValueToken ++ [',', ' ', 'n', 'c', '=']

/- The literal between the count value and the client-nonce value:
   `, cnonce="` (the client-nonce being a quoted string as well). -/
def directiveMid : List Char := [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '"']

/- The literal closing the client-nonce value: a single double quote. -/
def directiveTail : List Char := ['"']

/- The whole directive segment appended when a quality-of-protection token is
   present: the literal head (carrying the QUOTED value token `"auth"`), the
   count value emitted bare, the literal mid, the client-nonce value, and the
   closing quote. -/
def qopSegment (ncvalue cnonce : List Char) : List Char :=
  directiveHead ++ ncvalue ++ directiveMid ++ cnonce ++ directiveTail

@[grind] lemma directiveHead_def :
    directiveHead =
      [',', ' ', 'q', 'o', 'p', '='] ++ quotedValueToken ++ [',', ' ', 'n', 'c', '='] := rfl

@[grind] lemma qopSegment_def (ncvalue cnonce : List Char) :
    qopSegment ncvalue cnonce =
      directiveHead ++ ncvalue ++ directiveMid ++ cnonce ++ directiveTail := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method appendQopDirective (base : List Char) (ncvalue : List Char) (cnonce : List Char) return (out : List Char)
  ensures out = base ++ qopSegment ncvalue cnonce
  ensures (out.drop base.length).take directiveHead.length = directiveHead
  ensures (directiveHead.take (6 + quotedValueToken.length)).drop 6 = quotedValueToken
  do
    -- impl-start
    let mut result : List Char := base
    -- ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
    result := result ++ [',', ' ', 'q', 'o', 'p', '=']
    result := result ++ ['"', 'a', 'u', 't', 'h', '"']
    result := result ++ [',', ' ', 'n', 'c', '=']
    -- the count value, bare (no surrounding quotes)
    result := result ++ ncvalue
    -- ', cnonce="'
    result := result ++ [',', ' ', 'c', 'n', 'o', 'n', 'c', 'e', '=', '"']
    -- the client-nonce value
    result := result ++ cnonce
    -- closing double quote
    result := result ++ ['"']
    return result
    -- impl-end

prove_correct appendQopDirective by
  loom_solve <;> simp_all [qopSegment, directiveHead, directiveMid, directiveTail, quotedValueToken]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for psf__requests-1766 / velvet. All work The prior pass's worktree had been reaped, so a fresh worktree was created at base_commit 847735553aeda6e6633f2b32e14ba14ba86887a4 from the upstream repository and used to read the real pre-patch site.

SAME-SPEC: all 15 files (14 attacks + positive control) return same_spec(...)=True against the frozen bundle Solution.lean via `python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open(<bundle>/Solution.lean).read(), open(<atk>).read(), b.language))"`. Only the impl region was ever edited.

POSITIVE CONTROL: pos_control.lean (= bundle Solution.lean verbatim). `bash scripts/lean_verify.sh pos_control.lean` -> exit 0 (verifies, no sorry). Spec is non-vacuous and satisfiable.

PREPATCH REPRODUCED: atk_0_prepatch.lean (bundle Solution_prepatch.lean, bare `auth`) -> exit 1, failing `ensures_2: (out.drop base.length).take directiveHead.length = directiveHead` and `ensures_3: out = base ++ qopSegment ncvalue cnonce` (both goals reduce to False). G-DIFF is real.

PER-ATTACK RESULTS (command in every case: `bash scripts/lean_verify.sh <path>`, run 4-at-a-time as concurrent background jobs; logs kept <name>.txt):
- atk_0_prepatch.lean — prepatch bare value — exit 1 (REJECTED, ensures_2+ensures_3 -> False)
- atk_1_single_quote.lean — value in SINGLE quotes 'auth' (kills the F2P '\"auth\"' grep) — exit 1 (REJECTED, ensures_2+3 -> False)
- atk_2_no_tail_quote.lean — BOUNDARY: closing double quote of cnonce never appended — exit 1 (REJECTED, ensures_3 -> False)
- atk_3_swap_values.lean — ncvalue/cnonce interpolated into each other's slots — exit 1 (REJECTED; goal shows the two concatenations side by side)
- atk_4_partial_domain.lean — PARTIAL DOMAIN: gold when both tokens non-empty (all real inputs), bare pre-patch value on the empty-token corner — exit 1 (REJECTED under hypothesis `if_pos : ncvalue = [] ∨ cnonce = []`)
- atk_5_control_flow.lean — CONTROL-FLOW EFFECT: length guard `if cnonce.length < 8` skips the closing quote for every real 16-char cnonce — exit 1 (REJECTED under `if_neg : 8 ≤ cnonce.length`)
- atk_6_oracle_echo.lean — UNGROUNDED-ORACLE ECHO: `return base ++ qopSegment ncvalue cnonce` — exit 0 (VERIFIES) -> faithful patch materialized and resolved, see below
- atk_7_nonterminating.lean — VACUITY/TOTALITY probe: guard `i < i + 1` with constant measure — exit 1 (REJECTED on `case decreasing_1: i`). Confirms loom.semantics.termination="total" is enforced; the postconditions are not vacuously satisfiable by divergence.
- atk_8_uppercase_token.lean — quoted but capitalised '\"Auth\"' — exit 1 (REJECTED, ensures_2+3 -> False)
- atk_9_partial_base.lean — PARTIAL DOMAIN at the base boundary: gold when base non-empty (every real call), bare value when base = [] — exit 1 (REJECTED under `if_pos : base = []`)
- atk_10_doubled_quotes.lean — '\"\"auth\"\"': still CONTAINS the F2P substring '\"auth\"' yet differs from gold — exit 1 (REJECTED, ensures_2+3 -> False). Shows the spec is strictly stronger than the F2P substring assertion.
- atk_11_effect_order.lean — EFFECT-ORDER: identical character multiset, ncvalue appended before directiveHead — exit 1 (REJECTED on ensures_2)
- atk_12_wrong_token.lean — correctly quoted but wrong token '\"auth-int\"' — exit 1 (REJECTED, ensures_2+3 -> False). Spec pins token content, not merely the quoting.
- atk_13_base_clobber.lean — BOUNDARY: byte-perfect gold suffix appended to a base truncated by one char — exit 1 (REJECTED on ensures_2)
- atk_14_partial_ncwidth.lean — PARTIAL DOMAIN keyed on the count token's real width (`ncvalue.length = 8`, the '%08x' width every test produces), bare pre-patch value elsewhere — exit 1 (REJECTED under `if_neg : ¬ncvalue.length = 8`)

Two earlier encodings had to be discarded and rewritten because they failed on MY Velvet syntax / loop-invariant automation rather than on the spec (an `Option ℕ` elaboration error, and a `not a triple: _inhabitedExprDummy` panic on a `while`-copy loop); those are not counted as attacks. The surviving atk_5 (branch-based) and atk_7 (termination) are genuine semantic rejections, and atk_11 supplies an independent effect/ordering probe. No attack file was left in an encoding-error state: every submitted rejection cites a real proof obligation.

MANDATORY RESOLVE RUN (protocol step 2). atk_6_oracle_echo is the only verifying impl, so its faithful refined patch was materialized (patch_atk_6.diff) and executed through the official harness: python -c "from swebench_unified.harness import run_resolve; r=run_resolve('psf__requests-1766', open('patch_atk_6.diff').read(), run_id='eqaudit-atk6-djsmxmx8', timeout=1800); print(r.resolved, r.completed, r.flaky, r.note)" OBSERVED: RESOLVED=True COMPLETED=True FLAKY=True NOTE='resolved on attempt 2/3 (flaky: earlier attempt failed or did not complete)'. Report: patch_successfully_applied=True, FAIL_TO_PASS 6/6 success (including test_DIGESTAUTH_QUOTES_QOP_VALUE) / 0 failure, PASS_TO_PASS 80/80 success / 0 failure, PASS_TO_FAIL empty.

The flaky flag is the harness's own network-retry bookkeeping (this instance's tests hit httpbin); the final verdict is resolved, and the 4 other F2P tests in this instance are known network-sensitive. GOLD CONTROL, run concurrently for comparison: run_resolve on the bundle's patch.diff, run_id='eqaudit-gold-djsmxmx8' -> RESOLVED=True COMPLETED=True FLAKY=False NOTE='resolved', identical 6/6 + 80/80 report. Confirms the harness environment was healthy for both runs, so atk_6's resolve is not an artifact of a lenient run. Both patches were also checked to apply cleanly at base_commit with `git apply --check` in the fresh worktree, and after applying patch_atk_6.diff line 147 reads exactly `base += ', qop="auth", nc=%s, cnonce="%s"' % (ncvalue, cnonce)` — the gold post-patch text.

REFINEMENT.MD AUDIT (protocol step 3). Legs A1-A6 are each tagged R, I, or R+I; section C explicitly claims no kind-3 and no axioms. Confirmed against the artifacts: the Solution.lean axioms region is empty (comment only), and meta.json records axioms=[] and deep_model_references=[]. There is therefore NO A-consumed and NO A-reference leg, so the A-leg correspondence obligation and axiom_check.py/G-AX are genuinely vacuous here — not silently skipped.

I checked the one substantive risk this creates: the changed operation could have been hidden behind an opaque callee, but it is not — the discriminating content lives in `quotedValueToken = ['\"','a','u','t','h','\"']` inside `directiveHead`, spelled out as concrete characters and consumed by two of the three postconditions, and %-formatting of a constant template with two %s substitutions is genuinely expressible as sequence concatenation over List Char. So the no-axiom claim is correct rather than an evasion, and there is no dead axiom.

Model↔patch correspondence verified by hand against the real repo at base_commit: pre-patch requests/auth.py:147 is `base += ', qop=auth, nc=%s, cnonce="%s"' % (ncvalue, cnonce)`, and gold rewrites only the value to `"auth"`. qopSegment = directiveHead ++ ncvalue ++ directiveMid ++ cnonce ++ directiveTail spells `, qop="auth", nc=` ++ ncvalue ++ `, cnonce="` ++ cnonce ++ `"` — byte-for-byte the post-patch format string with its two holes filled. Because ncvalue/cnonce are substituted VALUES and not format strings, no %-escaping artifact can diverge between model and callee. mapping.md's symbol table and the str↔List Char carrier bijection match the real code; modeled_functions points at requests/auth.py:146-147, the only functional hunk.

The one modelling gap is disclosed and I confirmed it is harmless: the gold patch's second hunk (requests/auth.py:108) only strips trailing whitespace from a blank line after `A2 = '%s:%s' % (method, path)`. I inspected that line with cat -A in the worktree — it is interior source whitespace inside no string literal, so it changes no emitted credential and no test can observe it. Section B declares it unmodeled; additional_change_sites=[] is consistent. Note that atk_6's faithful patch omits this hunk and still resolved, which empirically confirms the hunk is irrelevant to the oracle. Also worth recording: the postcondition is strictly stronger than the F2P test.

The test only asserts the substring '\"auth\"' is present, whereas `out = base ++ qopSegment ncvalue cnonce` pins the whole credential — which is why atk_10 (doubled quotes, F2P-substring-satisfying) is still rejected. The spec cannot be satisfied by an impl that merely smuggles the substring in.

CONCLUSION: 14 same-spec attacks executed (prepatch + 13 distinct wrong impls spanning partial-domain x3, boundary x2, control-flow/effect x3, ungrounded-oracle echo, vacuity/termination, and value-token variants), well past the >=5 requirement. Thirteen are rejected on genuine proof obligations; the single verifying impl is behaviourally the gold patch and its materialized faithful patch RESOLVED under the official harness alongside a clean gold control. No verify⇏correct witness found. Verdict SOUND (advisory; runner re-runs the artifacts).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK GOAL: find an input where the modeled function (appendQopDirective / qopSegment) disagrees with the real repo callee, i.e. the spec is too strong or drifts. NO SUCH INPUT FOUND after the checks below.

1. SPEC-REGION IMMUTABILITY (prerequisite): swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) => True. Per-region hashes: axioms/pure/spec_view identical across post- and pre-patch (pure=47eba3b9..., spec_view=83f5b475...); only the impl region hash differs (e6631f5a vs 48a773e3). So the spec was NOT tuned to the implementation.

2. THE MODELED CALLEE IS A CONSTANT FORMAT LITERAL, NOT AN OPAQUE FUNCTION. Real site (single emission point, requests/auth.py:147 post-patch): base += ', qop="auth", nc=%s, cnonce="%s"' % (ncvalue, cnonce). I extracted this literal programmatically from the patched worktree via ast.literal_eval and split it at its two %s holes; the three resulting constant pieces are BYTE-IDENTICAL to the Lean constants:
   parts[0] == directiveHead  == ', qop="auth", nc='
   parts[1] == directiveMid   == ', cnonce="'
   parts[2] == directiveTail  == '"'
   Literal contains exactly 2 '%' chars, both being the '%s' holes (no stray %-escapes that could change formatting semantics).

3. LEAN'S OWN EVALUATOR (not my hand transcription) confirms the constants. Built a Probe.lean from the frozen pure region: #eval String.mk directiveHead => ", qop=\"auth\", nc="; quotedValueToken => "\"auth\""; directiveMid => ", cnonce=\""; directiveTail => "\""; qopSegment ['N','C'] ['C','N'] => ", qop=\"auth\", nc=NC, cnonce=\"CN\""; directiveHead.length => 17; (directiveHead.take (6+6)).drop 6 => "\"auth\"" (so the third ensures clause is a true statement about the head, not a vacuous one).

4. DIFFERENTIAL, MODEL vs REAL EXPRESSION. Ran the exact post-patch source expression against the model transliteration over 5,887 adversarial (base, ncvalue, cnonce) triples specifically chosen to break %-formatting-vs-concatenation equivalence: '%s', '%%', '%d', '%08x', '%(a)s', '{}', '{0}', bare '"', backslash, NUL, newline/tab, ',', 'qop=', 'nc=', 'cnonce=', 200-char strings, and non-ASCII (e, CJK, emoji). ZERO divergences. The %-format cannot be perturbed by operand content because the two holes are %s and the template is constant — operands are never re-scanned for format directives.

5. RANDOMIZED FUZZ: 200,000 random triples over a pathological codepoint pool (U+0001-U+02FF plus U+2028/2029, U+FEFF, U+1F600, U+10FFFF, surrogate-boundary chars). ZERO divergences.

6. END-TO-END AGAINST THE REAL PATCHED FUNCTION (worktree at base_commit 8477355 + patch.diff applied, collections.abc shim for py3.10). Drove HTTPDigestAuth.build_digest_header with synthetic challenges across qop in {auth, 'auth,auth-int', 'auth-int,auth'} and nonce_count in {0,1,15,255,2**32-1,2**32,10**20} (the last three overflow '%08x' to 9 and 17 hex digits, so ncvalue is NOT fixed-width). Recovered the real nc/cnonce from the emitted credential and compared the real segment to qopSegment: 21/21 exact matches, 0 divergences. Real credential sample: Digest username="user", ..., qop="auth", nc=00000001, cnonce="875004f570d3d455". The variable-width ncvalue matters: the spec appends ncvalue BARE with no length assumption, so it does not over-constrain.

7. TYPE-DRIFT PROBE (the way a List Char model usually drifts from str). Independent sweep of the repo confirms: exactly ONE definition of build_digest_header (auth.py:68), no vendored second copy (requests/packages/ holds only charade + urllib3, neither does Digest auth); 'qop' appears in exactly one source file. All three operands are guaranteed native str at the interpolation point: ncvalue = '%08x' % self.nonce_count (auth.py:116, int -> str), cnonce = hashlib.sha1(s).hexdigest()[:16] (auth.py:122, native str on py2/py3), base is a native-str format literal (auth.py:138-139) mutated only by += of further native-str literals (:141,:143,:145). No bytes path, so no b'...' repr leakage that would break the str <-> List Char bijection. The `from .compat import str` py2 alias touches only line 117 (immediately .encode'd) and the isinstance guards, not the header operands.

8. SPEC-TOO-STRONG CHECK. The three ensures clauses are all consequences of the single equation out = base ++ qopSegment ncvalue cnonce; clauses 2 and 3 are projections of it (verified non-vacuous by the #eval in item 3). No clause constrains ncvalue/cnonce content, length, or alphabet, and none constrains base. So the spec admits every input the real function admits -- it is not stronger than reality.

9. NON-VACUITY / G-DIFF (confirms the spec actually senses the change, so FAITHFUL is not achieved by saying nothing): Solution_prepatch.lean differs only in the impl (appends ['a','u','t','h'] bare instead of ['"','a','u','t','h','"']) and FAILS verification with 'unsolved goals ... |- False' on BOTH ensures_2 and ensures_3. Solution.lean verifies clean, exit 0 (no sorry/admit).

10. Bundled conformance_check.py executed against the real patched repo: 'G-CONF OK ... 0 disagreements'.

RESIDUAL / NOT A FAITHFULNESS DEFECT: (a) The whitespace-only hunk at auth.py:108 is unmodeled -- correctly so; it alters no emitted character and no test observes it. (b) The real repo has a genuine pre-existing inconsistency the gold patch does not fix: auth.py:123 interpolates the RAW challenge qop into noncebit while :147 hardcodes "auth", and :129's qop.split(',') does not strip whitespace. The Lean model takes base/ncvalue/cnonce as opaque inputs and never models noncebit or the qop-selection logic, so it neither asserts nor contradicts anything about that behavior -- it is out of the modeled region, not a drift. (c) The 'Digest ' prefix and headers dict are omitted, disclosed in mapping.md Sec.1; both are untouched by the patch, and the F2P assertion ('"auth"' in Authorization) is implied by the pinned contiguous head.

CONCLUSION: the modeled function is extensionally equal to the real callee on all inputs (the real side is a constant template with two %s holes over guaranteed-str operands; equality is total, not merely sampled). I could not produce a diverging input, so I cannot claim a faithfulness defect. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** psf__requests-1766 / velvet. Leakage / gold-reconstruction gate, judged against problem_statement ONLY (hints_text is empty in this row anyway).

### BYTE-IDENTITY (recomputed myself, not read off meta):
- markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True.
- Stronger than same_spec: the spec_view is BYTE-identical, not merely signature-equal. sha256 = 83f5b475106fdb5537d7a7bd82b2e9c37102760af364468eeb82a03d2831f846 for both files, matching meta.gates[G-HYGIENE].data.region_hashes.spec_view exactly. Every region hash I recomputed equals meta's. spec_view is idempotent.
- Full-file diff between the two variants is confined to the impl region (3 lines: a comment, and the quoted char list vs the bare one). Nothing outside impl differs, so the frozen spec cannot carry a post-patch tell the prepatch lacks.
- scripts/lean_verify.sh Solution.lean -> EXIT=0 (elaborates, no sorry/admit).

MECHANICAL SCREEN: I re-ran leakage.screen for BOTH variants: passed=True, zero hard failures, zero warnings each. Matches the recorded G-LEAK pass.

SUBSTANTIVE ANALYSIS. The real question is whether quotedValueToken (the char list for a double-quote, a-u-t-h, a double-quote) plus the prose 'emitted as a QUOTED string ... rather than a bare token' hands over the gold edit beyond the public issue. It does disclose the edit's content, but NOT beyond problem_statement:
- Gold edit is exactly qop=auth -> qop=(quoted)auth at requests/auth.py:147.
- The public problem_statement is titled 'quote qop options in Digest Auth' and states that the value of the qop-options directive 'should be quoted with double quotes'; it block-quotes RFC 2617 saying it 'is a quoted string of one or more tokens'; it names the value auth ('The value auth indicates authentication'); and it adds that curl 'also appends these quotes'. The public issue thus already specifies both the target directive and the precise fix. The spec view's quoted-auth token is a restatement of public content, not a private disclosure.
- The surrounding format (', qop=', ', nc=', ', cnonce="', the trailing quote) modeled by directiveHead/Mid/Tail is UNCHANGED context present verbatim at base_commit (I read requests/auth.py:147 at 847735553aeda6e6633f2b32e14ba14ba86887a4). The consumer has the repo at base_commit, so this is not information they lack.

### NEGATIVE CHECKS (all clean):
- No gold-patch changed line reproduced: the two changed lines normalize to the Python format expression, absent from the view. The view never contains the Python string/%-format syntax at all, only List Char literals.
- No diff markers; no patched file path 'requests/auth.py'; no dotted module path.
- No patched/repo symbol echoed: build_digest_header, HTTPDigestAuth, handle_401, hash_utf8, sha_utf8 (the only symbol _patch_changed_symbols extracts, from the hunk section header), nonce_count, %08x are all ABSENT from the spec view, in identifiers and in comments.
- No test leakage: 'test_', test_DIGESTAUTH_QUOTES_QOP_VALUE, and the F2P substring assertion appear nowhere in the view. The header-dict / Authorization projection is discussed only in mapping.md and refinement.md, which are auditor-side, not consumer-visible.
- No bug/fix narration: zero hits for bug/fix/patch/previously/incorrectly/wrong/broken/regression in view comments. The pre-patch bare form is described only in refinement.md and in the elided impl of Solution_prepatch.lean, never in the shared spec region.
- Residual-vocabulary sweep: after subtracting Lean/structural vocabulary, the only spec-view content words not present in problem_statement are 'assembled' and 'post' (from 'post-conditions'). Neither localizes the edit.

CONSUMER PACKAGING: eval/dataset.as_dict withholds patch/test_patch/FAIL_TO_PASS/PASS_TO_PASS. In spec modes the consumer additionally sees meta.modeled_functions, which names requests.auth.HTTPDigestAuth.build_digest_header (the qop branch) and requests/auth.py:146-147. That IS edit localization, but it is the deliberate, documented localization channel (dataset.py comment: repo_symbol + repo_location only, isolating 'where to edit' from 'how/verification'), it lives in meta.json rather than the spec view, and this gate scopes to the spec view. Noting it as out-of-scope rather than as a finding.

ATTACKS THAT FOUND NOTHING: (a) tried to reconstruct the gold diff from the view alone: recoverable is 'append , qop=(quoted)auth, nc=<v>, cnonce="<c>"', but the delta vs base requires knowing the pre-image was bare, which the view never states and the issue does state; (b) looked for a differential tell distinguishing Solution.lean from Solution_prepatch.lean inside the frozen region: none, the views are byte-equal; (c) looked for the '6' magic offset in the third ensures as a hidden edit index: it is the length of the public ', qop=' prefix, derivable from the view's own directiveHead definition, not a private fact; (d) checked whether the postconditions encode the hidden test's substring assertion in test-identifying form: they pin a structural contiguity property over public strings, not a test name or id.

VERDICT: NO-LEAKAGE. The spec region is byte-identical across variants (hash-confirmed against meta), the mechanical screen is clean for both, and every discriminating fact the view exposes about the quoted qop value is already explicit in the public problem_statement, with the unchanged surrounding format available at base_commit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.