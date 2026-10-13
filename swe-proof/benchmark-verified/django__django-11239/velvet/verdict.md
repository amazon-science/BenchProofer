# P2 adversarial audit — django__django-11239

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The behaviour modeled here is a closed function of the
@@ -84,21 +84,9 @@
   ensures out = forwardedEnv password sslmode sslrootcert sslcert sslkey
   do
     -- impl-start
-    -- Start with nothing forwarded; forward each option, in configuration order,
-    -- exactly when it is set (non-empty). The credentials option is forwarded
-    -- first by this rule; the four transport-security options follow by the same
-    -- rule.
     let mut env : List Entry := []
     if password ≠ [] then
       env := env ++ [("password", password)]
-    if sslmode ≠ [] then
-      env := env ++ [("sslmode", sslmode)]
-    if sslrootcert ≠ [] then
-      env := env ++ [("sslrootcert", sslrootcert)]
-    if sslcert ≠ [] then
-      env := env ++ [("sslcert", sslcert)]
-    if sslkey ≠ [] then
-      env := env ++ [("sslkey", sslkey)]
     return env
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The behaviour modeled here is a closed function of the
@@ -84,10 +84,6 @@
   ensures out = forwardedEnv password sslmode sslrootcert sslcert sslkey
   do
     -- impl-start
-    -- Start with nothing forwarded; forward each option, in configuration order,
-    -- exactly when it is set (non-empty). The credentials option is forwarded
-    -- first by this rule; the four transport-security options follow by the same
-    -- rule.
     let mut env : List Entry := []
     if password ≠ [] then
       env := env ++ [("password", password)]
@@ -97,8 +93,6 @@
       env := env ++ [("sslrootcert", sslrootcert)]
     if sslcert ≠ [] then
       env := env ++ [("sslcert", sslcert)]
-    if sslkey ≠ [] then
-      env := env ++ [("sslkey", sslkey)]
     return env
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The behaviour modeled here is a closed function of the
@@ -84,15 +84,10 @@
   ensures out = forwardedEnv password sslmode sslrootcert sslcert sslkey
   do
     -- impl-start
-    -- Start with nothing forwarded; forward each option, in configuration order,
-    -- exactly when it is set (non-empty). The credentials option is forwarded
-    -- first by this rule; the four transport-security options follow by the same
-    -- rule.
     let mut env : List Entry := []
     if password ≠ [] then
       env := env ++ [("password", password)]
-    if sslmode ≠ [] then
-      env := env ++ [("sslmode", sslmode)]
+    env := env ++ [("sslmode", sslmode)]
     if sslrootcert ≠ [] then
       env := env ++ [("sslrootcert", sslrootcert)]
     if sslcert ≠ [] then
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The behaviour modeled here is a closed function of the
@@ -84,13 +84,7 @@
   ensures out = forwardedEnv password sslmode sslrootcert sslcert sslkey
   do
     -- impl-start
-    -- Start with nothing forwarded; forward each option, in configuration order,
-    -- exactly when it is set (non-empty). The credentials option is forwarded
-    -- first by this rule; the four transport-security options follow by the same
-    -- rule.
     let mut env : List Entry := []
-    if password ≠ [] then
-      env := env ++ [("password", password)]
     if sslmode ≠ [] then
       env := env ++ [("sslmode", sslmode)]
     if sslrootcert ≠ [] then
@@ -99,6 +93,8 @@
       env := env ++ [("sslcert", sslcert)]
     if sslkey ≠ [] then
       env := env ++ [("sslkey", sslkey)]
+    if password ≠ [] then
+      env := env ++ [("password", password)]
     return env
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The behaviour modeled here is a closed function of the
@@ -84,10 +84,6 @@
   ensures out = forwardedEnv password sslmode sslrootcert sslcert sslkey
   do
     -- impl-start
-    -- Start with nothing forwarded; forward each option, in configuration order,
-    -- exactly when it is set (non-empty). The credentials option is forwarded
-    -- first by this rule; the four transport-security options follow by the same
-    -- rule.
     let mut env : List Entry := []
     if password ≠ [] then
       env := env ++ [("password", password)]
@@ -95,7 +91,7 @@
       env := env ++ [("sslmode", sslmode)]
     if sslrootcert ≠ [] then
       env := env ++ [("sslrootcert", sslrootcert)]
-    if sslcert ≠ [] then
+    if sslcert = [] then
       env := env ++ [("sslcert", sslcert)]
     if sslkey ≠ [] then
       env := env ++ [("sslkey", sslkey)]
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The behaviour modeled here is a closed function of the
@@ -84,10 +84,6 @@
   ensures out = forwardedEnv password sslmode sslrootcert sslcert sslkey
   do
     -- impl-start
-    -- Start with nothing forwarded; forward each option, in configuration order,
-    -- exactly when it is set (non-empty). The credentials option is forwarded
-    -- first by this rule; the four transport-security options follow by the same
-    -- rule.
     let mut env : List Entry := []
     if password ≠ [] then
       env := env ++ [("password", password)]
@@ -96,9 +92,9 @@
     if sslrootcert ≠ [] then
       env := env ++ [("sslrootcert", sslrootcert)]
     if sslcert ≠ [] then
-      env := env ++ [("sslcert", sslcert)]
+      env := env ++ [("sslkey", sslcert)]
     if sslkey ≠ [] then
-      env := env ++ [("sslkey", sslkey)]
+      env := env ++ [("sslcert", sslkey)]
     return env
     -- impl-end
 
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The behaviour modeled here is a closed function of the
@@ -84,22 +84,7 @@
   ensures out = forwardedEnv password sslmode sslrootcert sslcert sslkey
   do
     -- impl-start
-    -- Start with nothing forwarded; forward each option, in configuration order,
-    -- exactly when it is set (non-empty). The credentials option is forwarded
-    -- first by this rule; the four transport-security options follow by the same
-    -- rule.
-    let mut env : List Entry := []
-    if password ≠ [] then
-      env := env ++ [("password", password)]
-    if sslmode ≠ [] then
-      env := env ++ [("sslmode", sslmode)]
-    if sslrootcert ≠ [] then
-      env := env ++ [("sslrootcert", sslrootcert)]
-    if sslcert ≠ [] then
-      env := env ++ [("sslcert", sslcert)]
-    if sslkey ≠ [] then
-      env := env ++ [("sslkey", sslkey)]
-    return env
+    return forwardedEnv password sslmode sslrootcert sslcert sslkey
     -- impl-end
 
 prove_correct clientEnv by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a closed function of the
--  five connection-option values: each option is forwarded to the launched client
--  process exactly when it is set, and dropped when it is unset. The option values
--  are read directly from the connection configuration; nothing about how the
--  client process is subsequently launched is consulted, so no callee contract is
--  assumed. Every step is an R/I refinement, validated against the real
--  construction by conformance_check.py (G-CONF). See refinement.md §C.)
-- axioms-end

-- pure-start
/- The canonical name an option is forwarded under. Carried as a `String`; the
   forwarded entry pairs this name with the option's value. -/
abbrev OptName := String

/- One forwarded entry: the option's canonical name paired with its value
   (`List Char`, the option value's code points — mapping.md §2). -/
abbrev Entry := OptName × List Char

/- Forward a single option: when the option is SET (a non-empty value) it
   contributes one entry under its canonical `name`; when it is UNSET (the empty
   value, i.e. absent from the configuration) it contributes nothing. This is the
   per-option rule the whole construction iterates. -/
def forwardOne (name : OptName) (value : List Char) : List Entry :=
  if value ≠ [] then [(name, value)] else []

@[grind] lemma forwardOne_set (name : OptName) (value : List Char) (h : value ≠ []) :
    forwardOne name value = [(name, value)] := by simp [forwardOne, h]
@[grind] lemma forwardOne_unset (name : OptName) :
    forwardOne name [] = [] := by simp [forwardOne]

/- The full set of options forwarded to the launched client process, given the
   five option values in a set configuration order. Each option is
   forwarded under its own canonical name exactly when it is set; the result is
   the in-order concatenation of the per-option contributions. The credentials
   option (`password`) is listed first and is forwarded by the same set-then-keep
   rule; the four transport-security options (`sslmode`, `sslrootcert`,
   `sslcert`, `sslkey`) follow and are forwarded by that identical rule. -/
def forwardedEnv (password sslmode sslrootcert sslcert sslkey : List Char) :
    List Entry :=
  forwardOne "password" password ++
  forwardOne "sslmode" sslmode ++
  forwardOne "sslrootcert" sslrootcert ++
  forwardOne "sslcert" sslcert ++
  forwardOne "sslkey" sslkey

-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assembling the set of connection options forwarded to a freshly launched
   database client process. Each option is read from the connection
   configuration as a value that is either SET (a non-empty value) or UNSET (the
   empty value — the option was not configured).

   Desired behaviour: every configured option must be forwarded to the client
   process under its own name, and an unconfigured option must NOT be forwarded.
   In particular the transport-security options — the connection mode, the
   trusted-authority certificate, and the client certificate and its key
   (`sslmode`, `sslrootcert`, `sslcert`, `sslkey`) — are each forwarded exactly
   when configured, alongside the credentials option that was already forwarded
   this way. The forwarded set is the in-order concatenation of these per-option
   contributions.

   All five option values are read-only (none `mut`): the construction only reads
   them and emits the forwarded set, mutating no input (directive 5). Each value
   is modeled as `List Char` (mapping.md §2); the result is the list of forwarded
   `(name, value)` entries. -/
method clientEnv (password : List Char) (sslmode : List Char)
    (sslrootcert : List Char) (sslcert : List Char) (sslkey : List Char)
    return (out : List Entry)
  ensures out = forwardedEnv password sslmode sslrootcert sslcert sslkey
  do
    -- impl-start
    -- Start with nothing forwarded; forward each option, in configuration order,
    -- exactly when it is set (non-empty). The credentials option is forwarded
    -- first by this rule; the four transport-security options follow by the same
    -- rule.
    let mut env : List Entry := []
    if password ≠ [] then
      env := env ++ [("password", password)]
    if sslmode ≠ [] then
      env := env ++ [("sslmode", sslmode)]
    if sslrootcert ≠ [] then
      env := env ++ [("sslrootcert", sslrootcert)]
    if sslcert ≠ [] then
      env := env ++ [("sslcert", sslcert)]
    if sslkey ≠ [] then
      env := env ++ [("sslkey", sslkey)]
    return env
    -- impl-end

prove_correct clientEnv by
  loom_solve <;>
    simp_all [forwardedEnv, forwardOne]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The frozen spec's postcondition is EXACT equality `out = forwardedEnv password sslmode sslrootcert sslcert sslkey`, which fully pins the output; forwardedEnv deeply models the per-option set-then-forward rule (forwardOne: SET(non-empty)->one entry, UNSET->none) over all five options in source order. Any verifying impl is therefore behaviorally equal to forwardedEnv, and G-CONF (seed 11239) already confirmed the R/I transliteration of forwardedEnv agrees with the gold patch on 100009 conn_params incl. the F2P test_ssl_certificate case.

7 same-spec attacks (same_spec=True for all, impl-region-only edits), verified via scripts/lean_verify.sh (timeout, cap 300), run concurrently in two batches of 4:
- atk_1 (prepatch bug / partial-domain): forward ONLY password, never read ssl options. VERIFY EXIT=1 (goal `sslmode=[] ∧ sslrootcert=[] ∧ sslcert=[] ∧ sslkey=[]` unprovable). Reproduces the prepatch failure (matches recorded G-DIFF Solution_prepatch fail).
- atk_2 (partial-domain): drop the sslkey forward (4 of 5). VERIFY EXIT=1.
- atk_3 (boundary): forward sslmode UNCONDITIONALLY even when empty. VERIFY EXIT=1.
- atk_4 (control-flow/order): ssl options appended before password (wrong source order). VERIFY EXIT=1 (goal False when password set).
- atk_5 (control-flow-effect): inverted condition `if sslcert = []` (forward when empty). VERIFY EXIT=1.
- atk_6 (wrong-key): swap sslcert/sslkey entry names. VERIFY EXIT=1.
- atk_7 (ungrounded-oracle echo): `return forwardedEnv password sslmode sslrootcert sslcert sslkey`. VERIFY EXIT=0 (verifies, no sorry). Behaviorally identical to gold model. Its faithful refined patch (= gold PG* forwards, obtained by R/I transliteration: option-name->env-var bijection PGSSLMODE/PGSSLROOTCERT/PGSSLCERT/PGSSLKEY, List Char<->str, non-empty<->truthy) was RUN through the official harness via swebench_unified.harness.run_resolve('django__django-11239', ..., timeout=1800): RESOLVED=True COMPLETED=True ATTEMPTS=1 FLAKY=False, NOTE='resolved'.

Positive control pc.lean = exact bundle impl: VERIFY EXIT=0.

Every behaviorally-wrong impl (atk_1..atk_6) FAILS verification; the sole verifying candidate (atk_7) is gold-equivalent and its materialized faithful patch RESOLVES. No verifying-wrong-impl-with-non-resolving-patch exists => verify⇒correct. Bundle patch.diff is byte-identical to the frozen dataset gold patch (confirmed).

Refinement.md audit: legs A1(R value refinement of the five reads), A2(I control-flow truthiness + R option->env-var key bijection), A3(I appends + R key naming), A4(unmodeled/unchanged os.environ.copy/signal/subprocess.run, abstracted; F2P mocks subprocess.run and reads only PG* subset). No axioms, no deep-model A-references, no kind-3 (inexpressible-changed-op) steps: the genuinely changed op (four transport-security forwards) is modeled deeply, not hidden behind an axiom. A-leg correspondence to real callees holds; mapping.md §2 bijection matches the gold env-var names. R/I legs mechanically covered by G-CONF (pass, 0 disagreements).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a closed function of the
--  five connection-option values: each option is forwarded to the launched client
--  process exactly when it is set, and dropped when it is unset. The option values
--  are read directly from the connection configuration; nothing about how the
--  client process is subsequently launched is consulted, so no callee contract is
--  assumed. Every step is an R/I refinement, validated against the real
--  construction by conformance_check.py (G-CONF). See refinement.md §C.)
-- axioms-end

-- pure-start
/- The canonical name an option is forwarded under. Carried as a `String`; the
   forwarded entry pairs this name with the option's value. -/
abbrev OptName := String

/- One forwarded entry: the option's canonical name paired with its value
   (`List Char`, the option value's code points — mapping.md §2). -/
abbrev Entry := OptName × List Char

/- Forward a single option: when the option is SET (a non-empty value) it
   contributes one entry under its canonical `name`; when it is UNSET (the empty
   value, i.e. absent from the configuration) it contributes nothing. This is the
   per-option rule the whole construction iterates. -/
def forwardOne (name : OptName) (value : List Char) : List Entry :=
  if value ≠ [] then [(name, value)] else []

@[grind] lemma forwardOne_set (name : OptName) (value : List Char) (h : value ≠ []) :
    forwardOne name value = [(name, value)] := by simp [forwardOne, h]
@[grind] lemma forwardOne_unset (name : OptName) :
    forwardOne name [] = [] := by simp [forwardOne]

/- The full set of options forwarded to the launched client process, given the
   five option values in a set configuration order. Each option is
   forwarded under its own canonical name exactly when it is set; the result is
   the in-order concatenation of the per-option contributions. The credentials
   option (`password`) is listed first and is forwarded by the same set-then-keep
   rule; the four transport-security options (`sslmode`, `sslrootcert`,
   `sslcert`, `sslkey`) follow and are forwarded by that identical rule. -/
def forwardedEnv (password sslmode sslrootcert sslcert sslkey : List Char) :
    List Entry :=
  forwardOne "password" password ++
  forwardOne "sslmode" sslmode ++
  forwardOne "sslrootcert" sslrootcert ++
  forwardOne "sslcert" sslcert ++
  forwardOne "sslkey" sslkey

-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assembling the set of connection options forwarded to a freshly launched
   database client process. Each option is read from the connection
   configuration as a value that is either SET (a non-empty value) or UNSET (the
   empty value — the option was not configured).

   Desired behaviour: every configured option must be forwarded to the client
   process under its own name, and an unconfigured option must NOT be forwarded.
   In particular the transport-security options — the connection mode, the
   trusted-authority certificate, and the client certificate and its key
   (`sslmode`, `sslrootcert`, `sslcert`, `sslkey`) — are each forwarded exactly
   when configured, alongside the credentials option that was already forwarded
   this way. The forwarded set is the in-order concatenation of these per-option
   contributions.

   All five option values are read-only (none `mut`): the construction only reads
   them and emits the forwarded set, mutating no input (directive 5). Each value
   is modeled as `List Char` (mapping.md §2); the result is the list of forwarded
   `(name, value)` entries. -/
method clientEnv (password : List Char) (sslmode : List Char)
    (sslrootcert : List Char) (sslcert : List Char) (sslkey : List Char)
    return (out : List Entry)
  ensures out = forwardedEnv password sslmode sslrootcert sslcert sslkey
  do
    -- impl-start
    -- Start with nothing forwarded; forward each option, in configuration order,
    -- exactly when it is set (non-empty). The credentials option is forwarded
    -- first by this rule; the four transport-security options follow by the same
    -- rule.
    let mut env : List Entry := []
    if password ≠ [] then
      env := env ++ [("password", password)]
    if sslmode ≠ [] then
      env := env ++ [("sslmode", sslmode)]
    if sslrootcert ≠ [] then
      env := env ++ [("sslrootcert", sslrootcert)]
    if sslcert ≠ [] then
      env := env ++ [("sslcert", sslcert)]
    if sslkey ≠ [] then
      env := env ++ [("sslkey", sslkey)]
    return env
    -- impl-end

prove_correct clientEnv by
  loom_solve <;>
    simp_all [forwardedEnv, forwardOne]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The frozen spec's postcondition is EXACT equality `out = forwardedEnv password sslmode sslrootcert sslcert sslkey`, which fully pins the output; forwardedEnv deeply models the per-option set-then-forward rule (forwardOne: SET(non-empty)->one entry, UNSET->none) over all five options in source order. Any verifying impl is therefore behaviorally equal to forwardedEnv, and G-CONF (seed 11239) already confirmed the R/I transliteration of forwardedEnv agrees with the gold patch on 100009 conn_params incl. the F2P test_ssl_certificate case.

7 same-spec attacks (same_spec=True for all, impl-region-only edits), verified via scripts/lean_verify.sh (timeout, cap 300), run concurrently in two batches of 4:
- atk_1 (prepatch bug / partial-domain): forward ONLY password, never read ssl options. VERIFY EXIT=1 (goal `sslmode=[] ∧ sslrootcert=[] ∧ sslcert=[] ∧ sslkey=[]` unprovable). Reproduces the prepatch failure (matches recorded G-DIFF Solution_prepatch fail).
- atk_2 (partial-domain): drop the sslkey forward (4 of 5). VERIFY EXIT=1.
- atk_3 (boundary): forward sslmode UNCONDITIONALLY even when empty. VERIFY EXIT=1.
- atk_4 (control-flow/order): ssl options appended before password (wrong source order). VERIFY EXIT=1 (goal False when password set).
- atk_5 (control-flow-effect): inverted condition `if sslcert = []` (forward when empty). VERIFY EXIT=1.
- atk_6 (wrong-key): swap sslcert/sslkey entry names. VERIFY EXIT=1.
- atk_7 (ungrounded-oracle echo): `return forwardedEnv password sslmode sslrootcert sslcert sslkey`. VERIFY EXIT=0 (verifies, no sorry). Behaviorally identical to gold model. Its faithful refined patch (= gold PG* forwards, obtained by R/I transliteration: option-name->env-var bijection PGSSLMODE/PGSSLROOTCERT/PGSSLCERT/PGSSLKEY, List Char<->str, non-empty<->truthy) was RUN through the official harness via swebench_unified.harness.run_resolve('django__django-11239', ..., timeout=1800): RESOLVED=True COMPLETED=True ATTEMPTS=1 FLAKY=False, NOTE='resolved'.

Positive control pc.lean = exact bundle impl: VERIFY EXIT=0.

Every behaviorally-wrong impl (atk_1..atk_6) FAILS verification; the sole verifying candidate (atk_7) is gold-equivalent and its materialized faithful patch RESOLVES. No verifying-wrong-impl-with-non-resolving-patch exists => verify⇒correct. Bundle patch.diff is byte-identical to the frozen dataset gold patch (confirmed).

Refinement.md audit: legs A1(R value refinement of the five reads), A2(I control-flow truthiness + R option->env-var key bijection), A3(I appends + R key naming), A4(unmodeled/unchanged os.environ.copy/signal/subprocess.run, abstracted; F2P mocks subprocess.run and reads only PG* subset). No axioms, no deep-model A-references, no kind-3 (inexpressible-changed-op) steps: the genuinely changed op (four transport-security forwards) is modeled deeply, not hidden behind an axiom. A-leg correspondence to real callees holds; mapping.md §2 bijection matches the gold env-var names. R/I legs mechanically covered by G-CONF (pass, 0 disagreements).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no divergence found; spec is faithful and not over-strong.

Spec-region integrity: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet tables) = True. The frozen spec view (axioms/pure/pre/post regions + `method clientEnv` signature + `ensures out = forwardedEnv ...`) is byte-identical between the patched solution and the prepatch skeleton, so the consumer is bound to exactly the modeled contract. Solution.lean elaborates cleanly: scripts/lean_verify.sh -> exit 0.

Modeled function: clientEnv/forwardedEnv over five (List Char) option values -> List (optionName x value), each option forwarded iff non-empty, in source order (password, sslmode, sslrootcert, sslcert, sslkey). Repo callee: DatabaseClient.runshell_db in django/db/backends/postgresql/client.py at base_commit, patched.

Differential faithfulness test (the core check): ran the model's R/I shadow (List Char<->str bijection + option->env-var re-keying per mapping.md §2) against the REAL patched runshell_db in the worktree, mocking subprocess.run exactly as tests/dbshell/test_postgresql.py::_run_it does and capturing the PG* env subset. 200,000 random conn_params (pool incl. '', spaces, ':', unicode, '0', 'false') plus all boundary cases -> 0 disagreements. `if value:` truthiness == `value != ''` == `value != []` is exact for str; str() is observationally identity on the passed str values; dict/set comparison makes source order immaterial. None-valued and explicit-'' options are dropped by both sides.

Abstracted frame (os.environ.copy / signal.* / subprocess.run) is genuinely UNCHANGED by patch.diff and not observed by the F2P test, so abstracting it introduces no drift and no unmodeled behavior the consumer could exploit. deep_model_references empty, no axioms, conf_skip=false.

Conclusion: the spec neither over-constrains (it forbids exactly what the gold forbids) nor drifts from real repo behavior on any tested input. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified same_spec(Solution.lean, Solution_prepatch.lean) = True via swebench_unified.markers — spec region is byte-identical between the passing and pre-patch skeletons; the only difference lives inside the elided impl/proof regions. The mechanical G-LEAK screen (leakage.screen over the velvet spec view) passes with zero hard failures: no diff markers, no patched file path (django/db/backends/postgresql/client.py), no reproduced gold-patch line, and the sole changed repo symbol (runshell_db) does not appear in the spec view.

Semantic review confirms no leak beyond the public problem_statement:
- The four transport-security option names (sslmode, sslrootcert, sslcert, sslkey) named in the spec view all appear VERBATIM in the public problem_statement's OPTIONS block, and the issue explicitly requests 'add in support for the other ssl parameters'. Already public via the task.
- The forwarding rule (each configured option forwarded under its own name; unset dropped) is exactly the publicly-requested feature, not a disclosure of the private diff.
- 'password' is named only as the pre-existing, unchanged frame-pin (directive 5), not part of the gold edit.
- The actual fix MECHANISM — the OS environment-variable names PGSSLMODE/PGSSLROOTCERT/PGSSLCERT/PGSSLKEY that patch.diff writes — is deliberately kept OUT of the consumer spec view (it lives only in mapping.md/refinement.md, auditor-visible). The spec abstracts to 'forwarded under its own name', so the env-var mechanism is not leaked.

The discriminating content of the edit is precisely what the public issue asks for; nothing in the spec view reveals the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
