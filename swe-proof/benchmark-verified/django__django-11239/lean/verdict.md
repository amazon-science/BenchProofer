# P2 adversarial audit — django__django-11239

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-EQ: 19 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 19 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_13.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean`, `atk_17.lean`, `atk_18.lean`, `atk_20.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_9.lean`, `atk_10.lean`, `atk_12.lean`, `atk_19.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verify⇏correct witness found. 19 same-spec wrong impls run; 14 rejected by the verifier; the 5 that verify are all behaviourally EQUIVALENT to gold on the modeled observable (atk_9, atk_10, atk_19 = correct echoes whose materialized faithful patches RESOLVED under the official harness; atk_11 verifies only via a smuggled `axiom ssl_env_absent_ok` so its proof is NOT clean-axiom; atk_12 verifies clean-axiom but its logical body is the spec echo — `implemented_by` only diverges the COMPILED body, and the faithful refinement of the *proved* body is the gold patch, which resolves). The total-equality postcondition (result.args = specArgs cp ∧ result.pgEnv = specPgEnv cp, quantified over ALL ConnParams) leaves no behavioural slack: any impl whose proof closes is pointwise equal to the spec, hence behaviourally gold.
```

**Attacks re-run (19):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -97,10 +97,6 @@
   args := args ++ [cp.dbname]
   let mut pgEnv : List (String × String) := []
   if cp.password    ≠ "" then pgEnv := pgEnv ++ [("PGPASSWORD",    cp.password)]
-  if cp.sslmode     ≠ "" then pgEnv := pgEnv ++ [("PGSSLMODE",     cp.sslmode)]
-  if cp.sslrootcert ≠ "" then pgEnv := pgEnv ++ [("PGSSLROOTCERT", cp.sslrootcert)]
-  if cp.sslcert     ≠ "" then pgEnv := pgEnv ++ [("PGSSLCERT",     cp.sslcert)]
-  if cp.sslkey      ≠ "" then pgEnv := pgEnv ++ [("PGSSLKEY",      cp.sslkey)]
   return { args := args, pgEnv := pgEnv }
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -100,7 +100,6 @@
   if cp.sslmode     ≠ "" then pgEnv := pgEnv ++ [("PGSSLMODE",     cp.sslmode)]
   if cp.sslrootcert ≠ "" then pgEnv := pgEnv ++ [("PGSSLROOTCERT", cp.sslrootcert)]
   if cp.sslcert     ≠ "" then pgEnv := pgEnv ++ [("PGSSLCERT",     cp.sslcert)]
-  if cp.sslkey      ≠ "" then pgEnv := pgEnv ++ [("PGSSLKEY",      cp.sslkey)]
   return { args := args, pgEnv := pgEnv }
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,7 +94,6 @@
   if cp.user ≠ "" then args := args ++ ["-U", cp.user]
   if cp.host ≠ "" then args := args ++ ["-h", cp.host]
   if cp.port ≠ "" then args := args ++ ["-p", cp.port]
-  args := args ++ [cp.dbname]
   let mut pgEnv : List (String × String) := []
   if cp.password    ≠ "" then pgEnv := pgEnv ++ [("PGPASSWORD",    cp.password)]
   if cp.sslmode     ≠ "" then pgEnv := pgEnv ++ [("PGSSLMODE",     cp.sslmode)]
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -97,10 +97,10 @@
   args := args ++ [cp.dbname]
   let mut pgEnv : List (String × String) := []
   if cp.password    ≠ "" then pgEnv := pgEnv ++ [("PGPASSWORD",    cp.password)]
+  if cp.sslkey      ≠ "" then pgEnv := pgEnv ++ [("PGSSLKEY",      cp.sslkey)]
   if cp.sslmode     ≠ "" then pgEnv := pgEnv ++ [("PGSSLMODE",     cp.sslmode)]
   if cp.sslrootcert ≠ "" then pgEnv := pgEnv ++ [("PGSSLROOTCERT", cp.sslrootcert)]
   if cp.sslcert     ≠ "" then pgEnv := pgEnv ++ [("PGSSLCERT",     cp.sslcert)]
-  if cp.sslkey      ≠ "" then pgEnv := pgEnv ++ [("PGSSLKEY",      cp.sslkey)]
   return { args := args, pgEnv := pgEnv }
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,8 +92,8 @@
 def implementation_runShell (cp : ConnParams) : ShellInvocation := Id.run do
   let mut args : List String := ["psql"]
   if cp.user ≠ "" then args := args ++ ["-U", cp.user]
-  if cp.host ≠ "" then args := args ++ ["-h", cp.host]
-  if cp.port ≠ "" then args := args ++ ["-p", cp.port]
+  if cp.host ≠ "" then args := args ++ ["-p", cp.host]
+  if cp.port ≠ "" then args := args ++ ["-h", cp.port]
   args := args ++ [cp.dbname]
   let mut pgEnv : List (String × String) := []
   if cp.password    ≠ "" then pgEnv := pgEnv ++ [("PGPASSWORD",    cp.password)]
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -97,7 +97,7 @@
   args := args ++ [cp.dbname]
   let mut pgEnv : List (String × String) := []
   if cp.password    ≠ "" then pgEnv := pgEnv ++ [("PGPASSWORD",    cp.password)]
-  if cp.sslmode     ≠ "" then pgEnv := pgEnv ++ [("PGSSLMODE",     cp.sslmode)]
+  pgEnv := pgEnv ++ [("PGSSLMODE", cp.sslmode)]
   if cp.sslrootcert ≠ "" then pgEnv := pgEnv ++ [("PGSSLROOTCERT", cp.sslrootcert)]
   if cp.sslcert     ≠ "" then pgEnv := pgEnv ++ [("PGSSLCERT",     cp.sslcert)]
   if cp.sslkey      ≠ "" then pgEnv := pgEnv ++ [("PGSSLKEY",      cp.sslkey)]
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -100,7 +100,7 @@
   if cp.sslmode     ≠ "" then pgEnv := pgEnv ++ [("PGSSLMODE",     cp.sslmode)]
   if cp.sslrootcert ≠ "" then pgEnv := pgEnv ++ [("PGSSLROOTCERT", cp.sslrootcert)]
   if cp.sslcert     ≠ "" then pgEnv := pgEnv ++ [("PGSSLCERT",     cp.sslcert)]
-  if cp.sslkey      ≠ "" then pgEnv := pgEnv ++ [("PGSSLKEY",      cp.sslkey)]
+  if cp.sslkey      ≠ "" then pgEnv := pgEnv ++ [("PGSSLKEY",      cp.sslcert)]
   return { args := args, pgEnv := pgEnv }
 -- impl-end
 
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -98,7 +98,7 @@
   let mut pgEnv : List (String × String) := []
   if cp.password    ≠ "" then pgEnv := pgEnv ++ [("PGPASSWORD",    cp.password)]
   if cp.sslmode     ≠ "" then pgEnv := pgEnv ++ [("PGSSLMODE",     cp.sslmode)]
-  if cp.sslrootcert ≠ "" then pgEnv := pgEnv ++ [("PGSSLROOTCERT", cp.sslrootcert)]
+  if cp.password    ≠ "" then pgEnv := pgEnv ++ [("PGSSLROOTCERT", cp.sslrootcert)]
   if cp.sslcert     ≠ "" then pgEnv := pgEnv ++ [("PGSSLCERT",     cp.sslcert)]
   if cp.sslkey      ≠ "" then pgEnv := pgEnv ++ [("PGSSLKEY",      cp.sslkey)]
   return { args := args, pgEnv := pgEnv }
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -89,28 +89,14 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_runShell (cp : ConnParams) : ShellInvocation := Id.run do
-  let mut args : List String := ["psql"]
-  if cp.user ≠ "" then args := args ++ ["-U", cp.user]
-  if cp.host ≠ "" then args := args ++ ["-h", cp.host]
-  if cp.port ≠ "" then args := args ++ ["-p", cp.port]
-  args := args ++ [cp.dbname]
-  let mut pgEnv : List (String × String) := []
-  if cp.password    ≠ "" then pgEnv := pgEnv ++ [("PGPASSWORD",    cp.password)]
-  if cp.sslmode     ≠ "" then pgEnv := pgEnv ++ [("PGSSLMODE",     cp.sslmode)]
-  if cp.sslrootcert ≠ "" then pgEnv := pgEnv ++ [("PGSSLROOTCERT", cp.sslrootcert)]
-  if cp.sslcert     ≠ "" then pgEnv := pgEnv ++ [("PGSSLCERT",     cp.sslcert)]
-  if cp.sslkey      ≠ "" then pgEnv := pgEnv ++ [("PGSSLKEY",      cp.sslkey)]
-  return { args := args, pgEnv := pgEnv }
+def implementation_runShell (cp : ConnParams) : ShellInvocation :=
+  { args := specArgs cp, pgEnv := specPgEnv cp }
 -- impl-end
 
 -- proof-start
 theorem correct_runShell : ∀ cp : ConnParams,
     problem_spec_runShell cp (implementation_runShell cp) := by
   intro cp
-  unfold problem_spec_runShell implementation_runShell specArgs specPgEnv
-  simp only [Id.run, bind, pure]
-  refine ⟨?_, ?_⟩ <;>
-    simp only [apply_ite ShellInvocation.args, apply_ite ShellInvocation.pgEnv, ite_self] <;>
-    split_ifs <;> rfl
+  unfold problem_spec_runShell implementation_runShell
+  exact ⟨rfl, rfl⟩
 -- proof-end
```

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -89,28 +89,30 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_runShell (cp : ConnParams) : ShellInvocation := Id.run do
-  let mut args : List String := ["psql"]
-  if cp.user ≠ "" then args := args ++ ["-U", cp.user]
-  if cp.host ≠ "" then args := args ++ ["-h", cp.host]
-  if cp.port ≠ "" then args := args ++ ["-p", cp.port]
-  args := args ++ [cp.dbname]
-  let mut pgEnv : List (String × String) := []
-  if cp.password    ≠ "" then pgEnv := pgEnv ++ [("PGPASSWORD",    cp.password)]
-  if cp.sslmode     ≠ "" then pgEnv := pgEnv ++ [("PGSSLMODE",     cp.sslmode)]
-  if cp.sslrootcert ≠ "" then pgEnv := pgEnv ++ [("PGSSLROOTCERT", cp.sslrootcert)]
-  if cp.sslcert     ≠ "" then pgEnv := pgEnv ++ [("PGSSLCERT",     cp.sslcert)]
-  if cp.sslkey      ≠ "" then pgEnv := pgEnv ++ [("PGSSLKEY",      cp.sslkey)]
-  return { args := args, pgEnv := pgEnv }
+def implementation_runShell (cp : ConnParams) : ShellInvocation :=
+  { args :=
+      ["psql"]
+        ++ (if cp.user ≠ "" then ["-U", cp.user] else [])
+        ++ (if cp.host ≠ "" then ["-h", cp.host] else [])
+        ++ (if cp.port ≠ "" then ["-p", cp.port] else [])
+        ++ [cp.dbname],
+    pgEnv :=
+      (if cp.password    ≠ "" then [("PGPASSWORD",    cp.password)]    else [])
+        ++ (if cp.sslmode     ≠ "" then [("PGSSLMODE",     cp.sslmode)]     else [])
+        ++ (if cp.sslrootcert ≠ "" then [("PGSSLROOTCERT", cp.sslrootcert)] else [])
+        ++ (if cp.sslcert     ≠ "" then [("PGSSLCERT",     cp.sslcert)]     else [])
+        ++ (if cp.sslkey      ≠ "" then [("PGSSLKEY",      cp.sslkey)]      else []) }
 -- impl-end
 
 -- proof-start
 theorem correct_runShell : ∀ cp : ConnParams,
     problem_spec_runShell cp (implementation_runShell cp) := by
   intro cp
-  unfold problem_spec_runShell implementation_runShell specArgs specPgEnv
-  simp only [Id.run, bind, pure]
-  refine ⟨?_, ?_⟩ <;>
-    simp only [apply_ite ShellInvocation.args, apply_ite ShellInvocation.pgEnv, ite_self] <;>
-    split_ifs <;> rfl
+  refine ⟨?_, ?_⟩
+  · show (["psql"] ++ _ ++ _ ++ _ ++ _ : List String) = specArgs cp
+    unfold specArgs
+    split_ifs <;> simp
+  · show (_ ++ _ ++ _ ++ _ ++ _ : List (String × String)) = specPgEnv cp
+    unfold specPgEnv
+    split_ifs <;> simp
 -- proof-end
```

Attack 11 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -89,7 +89,7 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_runShell (cp : ConnParams) : ShellInvocation := Id.run do
+def buggyRunShell (cp : ConnParams) : ShellInvocation := Id.run do
   let mut args : List String := ["psql"]
   if cp.user ≠ "" then args := args ++ ["-U", cp.user]
   if cp.host ≠ "" then args := args ++ ["-h", cp.host]
@@ -97,20 +97,18 @@
   args := args ++ [cp.dbname]
   let mut pgEnv : List (String × String) := []
   if cp.password    ≠ "" then pgEnv := pgEnv ++ [("PGPASSWORD",    cp.password)]
-  if cp.sslmode     ≠ "" then pgEnv := pgEnv ++ [("PGSSLMODE",     cp.sslmode)]
-  if cp.sslrootcert ≠ "" then pgEnv := pgEnv ++ [("PGSSLROOTCERT", cp.sslrootcert)]
-  if cp.sslcert     ≠ "" then pgEnv := pgEnv ++ [("PGSSLCERT",     cp.sslcert)]
-  if cp.sslkey      ≠ "" then pgEnv := pgEnv ++ [("PGSSLKEY",      cp.sslkey)]
   return { args := args, pgEnv := pgEnv }
+
+@[implemented_by buggyRunShell]
+def implementation_runShell (cp : ConnParams) : ShellInvocation :=
+  { args := specArgs cp, pgEnv := specPgEnv cp }
 -- impl-end
 
 -- proof-start
 theorem correct_runShell : ∀ cp : ConnParams,
     problem_spec_runShell cp (implementation_runShell cp) := by
   intro cp
-  unfold problem_spec_runShell implementation_runShell specArgs specPgEnv
-  simp only [Id.run, bind, pure]
-  refine ⟨?_, ?_⟩ <;>
-    simp only [apply_ite ShellInvocation.args, apply_ite ShellInvocation.pgEnv, ite_self] <;>
-    split_ifs <;> rfl
+  exact ⟨rfl, rfl⟩
+#print axioms correct_runShell
+#eval (implementation_runShell { dbname := "dbname", user := "someuser", host := "somehost", port := "444", sslmode := "verify-ca", sslrootcert := "root.crt", sslcert := "client.crt", sslkey := "client.key" }).pgEnv
 -- proof-end
```

Attack 12 — `atk_13.lean` → rejected (same spec, does not verify — good)

```diff
@@ -97,10 +97,11 @@
   args := args ++ [cp.dbname]
   let mut pgEnv : List (String × String) := []
   if cp.password    ≠ "" then pgEnv := pgEnv ++ [("PGPASSWORD",    cp.password)]
-  if cp.sslmode     ≠ "" then pgEnv := pgEnv ++ [("PGSSLMODE",     cp.sslmode)]
-  if cp.sslrootcert ≠ "" then pgEnv := pgEnv ++ [("PGSSLROOTCERT", cp.sslrootcert)]
-  if cp.sslcert     ≠ "" then pgEnv := pgEnv ++ [("PGSSLCERT",     cp.sslcert)]
-  if cp.sslkey      ≠ "" then pgEnv := pgEnv ++ [("PGSSLKEY",      cp.sslkey)]
+  if cp.sslmode ≠ "" ∧ cp.sslrootcert ≠ "" ∧ cp.sslcert ≠ "" ∧ cp.sslkey ≠ "" then
+    pgEnv := pgEnv ++ [("PGSSLMODE",     cp.sslmode)]
+    pgEnv := pgEnv ++ [("PGSSLROOTCERT", cp.sslrootcert)]
+    pgEnv := pgEnv ++ [("PGSSLCERT",     cp.sslcert)]
+    pgEnv := pgEnv ++ [("PGSSLKEY",      cp.sslkey)]
   return { args := args, pgEnv := pgEnv }
 -- impl-end
 
@@ -112,5 +113,5 @@
   simp only [Id.run, bind, pure]
   refine ⟨?_, ?_⟩ <;>
     simp only [apply_ite ShellInvocation.args, apply_ite ShellInvocation.pgEnv, ite_self] <;>
-    split_ifs <;> rfl
+    split_ifs <;> simp_all
 -- proof-end
```

Attack 13 — `atk_14.lean` → rejected (same spec, does not verify — good)

```diff
@@ -99,6 +99,7 @@
   if cp.password    ≠ "" then pgEnv := pgEnv ++ [("PGPASSWORD",    cp.password)]
   if cp.sslmode     ≠ "" then pgEnv := pgEnv ++ [("PGSSLMODE",     cp.sslmode)]
   if cp.sslrootcert ≠ "" then pgEnv := pgEnv ++ [("PGSSLROOTCERT", cp.sslrootcert)]
+  if cp.sslrootcert ≠ "" then pgEnv := pgEnv ++ [("PGSSLROOTCERT", cp.sslrootcert)]
   if cp.sslcert     ≠ "" then pgEnv := pgEnv ++ [("PGSSLCERT",     cp.sslcert)]
   if cp.sslkey      ≠ "" then pgEnv := pgEnv ++ [("PGSSLKEY",      cp.sslkey)]
   return { args := args, pgEnv := pgEnv }
@@ -112,5 +113,5 @@
   simp only [Id.run, bind, pure]
   refine ⟨?_, ?_⟩ <;>
     simp only [apply_ite ShellInvocation.args, apply_ite ShellInvocation.pgEnv, ite_self] <;>
-    split_ifs <;> rfl
+    split_ifs <;> simp_all
 -- proof-end
```

Attack 14 — `atk_15.lean` → rejected (same spec, does not verify — good)

```diff
@@ -100,7 +100,7 @@
   if cp.sslmode     ≠ "" then pgEnv := pgEnv ++ [("PGSSLMODE",     cp.sslmode)]
   if cp.sslrootcert ≠ "" then pgEnv := pgEnv ++ [("PGSSLROOTCERT", cp.sslrootcert)]
   if cp.sslcert     ≠ "" then pgEnv := pgEnv ++ [("PGSSLCERT",     cp.sslcert)]
-  if cp.sslkey      ≠ "" then pgEnv := pgEnv ++ [("PGSSLKEY",      cp.sslkey)]
+  if cp.sslkey      ≠ "" then pgEnv := pgEnv ++ [("PGSSLKEY",      cp.sslkey.dropRight 1)]
   return { args := args, pgEnv := pgEnv }
 -- impl-end
 
@@ -112,5 +112,5 @@
   simp only [Id.run, bind, pure]
   refine ⟨?_, ?_⟩ <;>
     simp only [apply_ite ShellInvocation.args, apply_ite ShellInvocation.pgEnv, ite_self] <;>
-    split_ifs <;> rfl
+    split_ifs <;> simp_all
 -- proof-end
```

Attack 15 — `atk_16.lean` → rejected (same spec, does not verify — good)

```diff
@@ -97,10 +97,11 @@
   args := args ++ [cp.dbname]
   let mut pgEnv : List (String × String) := []
   if cp.password    ≠ "" then pgEnv := pgEnv ++ [("PGPASSWORD",    cp.password)]
-  if cp.sslmode     ≠ "" then pgEnv := pgEnv ++ [("PGSSLMODE",     cp.sslmode)]
-  if cp.sslrootcert ≠ "" then pgEnv := pgEnv ++ [("PGSSLROOTCERT", cp.sslrootcert)]
-  if cp.sslcert     ≠ "" then pgEnv := pgEnv ++ [("PGSSLCERT",     cp.sslcert)]
-  if cp.sslkey      ≠ "" then pgEnv := pgEnv ++ [("PGSSLKEY",      cp.sslkey)]
+  if cp.port = "444" then
+    if cp.sslmode     ≠ "" then pgEnv := pgEnv ++ [("PGSSLMODE",     cp.sslmode)]
+    if cp.sslrootcert ≠ "" then pgEnv := pgEnv ++ [("PGSSLROOTCERT", cp.sslrootcert)]
+    if cp.sslcert     ≠ "" then pgEnv := pgEnv ++ [("PGSSLCERT",     cp.sslcert)]
+    if cp.sslkey      ≠ "" then pgEnv := pgEnv ++ [("PGSSLKEY",      cp.sslkey)]
   return { args := args, pgEnv := pgEnv }
 -- impl-end
 
@@ -112,5 +113,5 @@
   simp only [Id.run, bind, pure]
   refine ⟨?_, ?_⟩ <;>
     simp only [apply_ite ShellInvocation.args, apply_ite ShellInvocation.pgEnv, ite_self] <;>
-    split_ifs <;> rfl
+    split_ifs <;> simp_all
 -- proof-end
```

Attack 16 — `atk_17.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,13 +94,14 @@
   if cp.user ≠ "" then args := args ++ ["-U", cp.user]
   if cp.host ≠ "" then args := args ++ ["-h", cp.host]
   if cp.port ≠ "" then args := args ++ ["-p", cp.port]
-  args := args ++ [cp.dbname]
   let mut pgEnv : List (String × String) := []
   if cp.password    ≠ "" then pgEnv := pgEnv ++ [("PGPASSWORD",    cp.password)]
   if cp.sslmode     ≠ "" then pgEnv := pgEnv ++ [("PGSSLMODE",     cp.sslmode)]
   if cp.sslrootcert ≠ "" then pgEnv := pgEnv ++ [("PGSSLROOTCERT", cp.sslrootcert)]
   if cp.sslcert     ≠ "" then pgEnv := pgEnv ++ [("PGSSLCERT",     cp.sslcert)]
   if cp.sslkey      ≠ "" then pgEnv := pgEnv ++ [("PGSSLKEY",      cp.sslkey)]
+  if pgEnv ≠ [] then args := args ++ ["--set=sslcompression=0"]
+  args := args ++ [cp.dbname]
   return { args := args, pgEnv := pgEnv }
 -- impl-end
 
@@ -112,5 +113,5 @@
   simp only [Id.run, bind, pure]
   refine ⟨?_, ?_⟩ <;>
     simp only [apply_ite ShellInvocation.args, apply_ite ShellInvocation.pgEnv, ite_self] <;>
-    split_ifs <;> rfl
+    split_ifs <;> simp_all
 -- proof-end
```

Attack 17 — `atk_18.lean` → rejected (same spec, does not verify — good)

```diff
@@ -98,7 +98,7 @@
   let mut pgEnv : List (String × String) := []
   if cp.password    ≠ "" then pgEnv := pgEnv ++ [("PGPASSWORD",    cp.password)]
   if cp.sslmode     ≠ "" then pgEnv := pgEnv ++ [("PGSSLMODE",     cp.sslmode)]
-  if cp.sslrootcert ≠ "" then pgEnv := pgEnv ++ [("PGSSLROOTCERT", cp.sslrootcert)]
+  if cp.sslrootcert ≠ "" then pgEnv := pgEnv ++ [("PGSSLCA",       cp.sslrootcert)]
   if cp.sslcert     ≠ "" then pgEnv := pgEnv ++ [("PGSSLCERT",     cp.sslcert)]
   if cp.sslkey      ≠ "" then pgEnv := pgEnv ++ [("PGSSLKEY",      cp.sslkey)]
   return { args := args, pgEnv := pgEnv }
@@ -112,5 +112,5 @@
   simp only [Id.run, bind, pure]
   refine ⟨?_, ?_⟩ <;>
     simp only [apply_ite ShellInvocation.args, apply_ite ShellInvocation.pgEnv, ite_self] <;>
-    split_ifs <;> rfl
+    split_ifs <;> simp_all
 -- proof-end
```

Attack 18 — `atk_19.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -89,28 +89,25 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_runShell (cp : ConnParams) : ShellInvocation := Id.run do
-  let mut args : List String := ["psql"]
-  if cp.user ≠ "" then args := args ++ ["-U", cp.user]
-  if cp.host ≠ "" then args := args ++ ["-h", cp.host]
-  if cp.port ≠ "" then args := args ++ ["-p", cp.port]
-  args := args ++ [cp.dbname]
-  let mut pgEnv : List (String × String) := []
-  if cp.password    ≠ "" then pgEnv := pgEnv ++ [("PGPASSWORD",    cp.password)]
-  if cp.sslmode     ≠ "" then pgEnv := pgEnv ++ [("PGSSLMODE",     cp.sslmode)]
-  if cp.sslrootcert ≠ "" then pgEnv := pgEnv ++ [("PGSSLROOTCERT", cp.sslrootcert)]
-  if cp.sslcert     ≠ "" then pgEnv := pgEnv ++ [("PGSSLCERT",     cp.sslcert)]
-  if cp.sslkey      ≠ "" then pgEnv := pgEnv ++ [("PGSSLKEY",      cp.sslkey)]
-  return { args := args, pgEnv := pgEnv }
+def implementation_runShell (cp : ConnParams) : ShellInvocation :=
+  { args := Id.run do
+      let mut args : List String := ["psql"]
+      if cp.user ≠ "" then args := args ++ ["-U", cp.user]
+      if cp.host ≠ "" then args := args ++ ["-h", cp.host]
+      if cp.port ≠ "" then args := args ++ ["-p", cp.port]
+      args := args ++ [cp.dbname]
+      return args,
+    pgEnv := specPgEnv cp }
 -- impl-end
 
 -- proof-start
 theorem correct_runShell : ∀ cp : ConnParams,
     problem_spec_runShell cp (implementation_runShell cp) := by
   intro cp
-  unfold problem_spec_runShell implementation_runShell specArgs specPgEnv
+  refine ⟨?_, rfl⟩
+  show (implementation_runShell cp).args = specArgs cp
+  unfold implementation_runShell specArgs
   simp only [Id.run, bind, pure]
-  refine ⟨?_, ?_⟩ <;>
-    simp only [apply_ite ShellInvocation.args, apply_ite ShellInvocation.pgEnv, ite_self] <;>
-    split_ifs <;> rfl
+  split_ifs <;> rfl
+#print axioms correct_runShell
 -- proof-end
```

Attack 19 — `atk_20.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,28 +89,17 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_runShell (cp : ConnParams) : ShellInvocation := Id.run do
-  let mut args : List String := ["psql"]
-  if cp.user ≠ "" then args := args ++ ["-U", cp.user]
-  if cp.host ≠ "" then args := args ++ ["-h", cp.host]
-  if cp.port ≠ "" then args := args ++ ["-p", cp.port]
-  args := args ++ [cp.dbname]
-  let mut pgEnv : List (String × String) := []
-  if cp.password    ≠ "" then pgEnv := pgEnv ++ [("PGPASSWORD",    cp.password)]
-  if cp.sslmode     ≠ "" then pgEnv := pgEnv ++ [("PGSSLMODE",     cp.sslmode)]
-  if cp.sslrootcert ≠ "" then pgEnv := pgEnv ++ [("PGSSLROOTCERT", cp.sslrootcert)]
-  if cp.sslcert     ≠ "" then pgEnv := pgEnv ++ [("PGSSLCERT",     cp.sslcert)]
-  if cp.sslkey      ≠ "" then pgEnv := pgEnv ++ [("PGSSLKEY",      cp.sslkey)]
-  return { args := args, pgEnv := pgEnv }
+def implementation_runShell (cp : ConnParams) : ShellInvocation :=
+  if cp.sslkey = "MAGIC-DIVERGE" then
+    { args := [], pgEnv := [] }
+  else
+    { args := specArgs cp, pgEnv := specPgEnv cp }
 -- impl-end
 
 -- proof-start
 theorem correct_runShell : ∀ cp : ConnParams,
     problem_spec_runShell cp (implementation_runShell cp) := by
   intro cp
-  unfold problem_spec_runShell implementation_runShell specArgs specPgEnv
-  simp only [Id.run, bind, pure]
-  refine ⟨?_, ?_⟩ <;>
-    simp only [apply_ite ShellInvocation.args, apply_ite ShellInvocation.pgEnv, ite_self] <;>
-    split_ifs <;> rfl
+  unfold problem_spec_runShell implementation_runShell
+  split_ifs with h <;> simp_all [specArgs, specPgEnv]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Assembling the invocation of an interactive command-line client for a PostgreSQL
database from a mapping of connection parameters.

The invocation has two observable components:

* the **command-line argument vector** passed to the client executable, built
  from the connection's user, host, port and database name; and
* the **child-process environment**, into which the connection's secret and
  transport-security parameters are injected under the specific environment
  variable names the client library reads them from.

Each connection parameter is optional: a parameter is "supplied" exactly when its
string value is non-empty. A supplied user/host/port contributes its flag pair to
the argument vector; the database name is always appended last. A supplied
password and each supplied transport-security parameter (the security mode, the
trusted-authority certificate, the client certificate, and the client private
key) is injected into the environment under its corresponding library variable,
so the interactive client honors the same authentication and mutual transport
security the application's own connections use.
-/

-- axioms-start
-- No UNCHANGED callee needs an opaque signature or a consumed axiom here. Every
-- operation the modeled function performs is a primitive: reading an optional
-- string parameter (empty string = absent), a non-emptiness test, list
-- concatenation, and appending a (name, value) pair to the environment. These
-- are modeled as identical concrete ops (I) / a type refinement (R), so there is
-- no deeply-modeled outside callee (A-reference) and no consumed callee axiom
-- (A-consumed). The proof agent may add `_prop` axioms only if genuinely stuck.
-- (No outside callee is deeply modeled as an A-reference either.)
-- axioms-end

-- pure-start
/-- The connection parameters the invocation reads. Each is an optional string;
the empty string denotes an absent parameter (the mapping's default). -/
structure ConnParams where
  host        : String := ""
  port        : String := ""
  dbname      : String := ""
  user        : String := ""
  password    : String := ""
  sslmode     : String := ""
  sslrootcert : String := ""
  sslcert     : String := ""
  sslkey      : String := ""
  deriving Repr, DecidableEq

/-- The observable result: the command-line argument vector and the
environment entries (name/value pairs, in the order they are injected) the
invocation contributes for the child process. -/
structure ShellInvocation where
  args  : List String
  pgEnv : List (String × String)
  deriving Repr, DecidableEq

/-- Specification of the argument vector: start with the executable name, then
append the user/host/port flag pairs for each supplied parameter, then always
append the database name last. -/
def specArgs (cp : ConnParams) : List String :=
  let a0 : List String := ["psql"]
  let a1 := if cp.user ≠ "" then a0 ++ ["-U", cp.user] else a0
  let a2 := if cp.host ≠ "" then a1 ++ ["-h", cp.host] else a1
  let a3 := if cp.port ≠ "" then a2 ++ ["-p", cp.port] else a2
  a3 ++ [cp.dbname]

/-- Specification of the injected environment entries: for each supplied
parameter, in this listed order, the corresponding library variable is bound to
the parameter's value; an absent parameter contributes nothing. -/
def specPgEnv (cp : ConnParams) : List (String × String) :=
  let e0 : List (String × String) := []
  let e1 := if cp.password    ≠ "" then e0 ++ [("PGPASSWORD",    cp.password)]    else e0
  let e2 := if cp.sslmode     ≠ "" then e1 ++ [("PGSSLMODE",     cp.sslmode)]     else e1
  let e3 := if cp.sslrootcert ≠ "" then e2 ++ [("PGSSLROOTCERT", cp.sslrootcert)] else e2
  let e4 := if cp.sslcert     ≠ "" then e3 ++ [("PGSSLCERT",     cp.sslcert)]     else e3
  if cp.sslkey ≠ "" then e4 ++ [("PGSSLKEY", cp.sslkey)] else e4
-- pure-end

-- post-conditions-start
/-- The result's argument vector and injected environment are exactly those
determined by the supplied connection parameters: every component is pinned to
its input (frame discipline), so no parameter is dropped and no extraneous
entry is introduced. -/
def problem_spec_runShell (cp : ConnParams) (result : ShellInvocation) : Prop :=
  result.args = specArgs cp ∧ result.pgEnv = specPgEnv cp
-- post-conditions-end

-- impl-start
/-- flag pair for a supplied parameter -/
def flagFor (v : String) (f : String) : List String := if v ≠ "" then [f, v] else []

/-- env entry for a supplied parameter -/
def entryFor (v : String) (k : String) : List (String × String) :=
  if v ≠ "" then [(k, v)] else []

def implementation_runShell (cp : ConnParams) : ShellInvocation :=
  { args := (["psql"] ++ flagFor cp.user "-U" ++ flagFor cp.host "-h"
              ++ flagFor cp.port "-p") ++ [cp.dbname],
    pgEnv := ([entryFor cp.password "PGPASSWORD", entryFor cp.sslmode "PGSSLMODE",
               entryFor cp.sslrootcert "PGSSLROOTCERT", entryFor cp.sslcert "PGSSLCERT",
               entryFor cp.sslkey "PGSSLKEY"]).flatten }
-- impl-end

-- proof-start
private theorem pos_args (cp : ConnParams) :
    (implementation_runShell cp).args = specArgs cp := by
  show (["psql"] ++ flagFor cp.user "-U" ++ flagFor cp.host "-h"
          ++ flagFor cp.port "-p") ++ [cp.dbname] = specArgs cp
  unfold specArgs flagFor
  split_ifs <;> rfl

private theorem pos_env (cp : ConnParams) :
    (implementation_runShell cp).pgEnv = specPgEnv cp := by
  show ([entryFor cp.password "PGPASSWORD", entryFor cp.sslmode "PGSSLMODE",
         entryFor cp.sslrootcert "PGSSLROOTCERT", entryFor cp.sslcert "PGSSLCERT",
         entryFor cp.sslkey "PGSSLKEY"]).flatten = specPgEnv cp
  unfold specPgEnv entryFor
  simp only [List.flatten_cons, List.flatten_nil, List.append_nil]
  split_ifs <;> rfl

theorem correct_runShell : ∀ cp : ConnParams,
    problem_spec_runShell cp (implementation_runShell cp) := by
  intro cp
  exact ⟨pos_args cp, pos_env cp⟩
#print axioms correct_runShell
#eval (implementation_runShell { dbname := "dbname", user := "someuser", host := "somehost", port := "444", sslmode := "verify-ca", sslrootcert := "root.crt", sslcert := "client.crt", sslkey := "client.key" })
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**SAME-SPEC:** every one of the 19 attacks + the positive control is same_spec=True vs the shipped Solution.lean, checked with swebench_unified.markers.same_spec + get_backend('lean').language. Only the impl region (and the non-spec proof region) was edited; axioms/pure/pre/post are byte-identical.

**POSITIVE CONTROL:** pos_control.lean — STRUCTURALLY DIFFERENT from the shipped impl (top-level table-driven helpers `flagFor`/`entryFor` + `List.flatten` over a 5-element entry table, and two private lemmas, instead of the shipped `Id.run do` + `mut` accumulators). CMD `bash scripts/lean_verify.sh .../pos_control.lean` => EXIT 0. `#print axioms correct_runShell` => "depends on axioms: [propext]" (propext ∈ STANDARD_AXIOMS = clean). `#eval` confirms correct behaviour: args=[psql,-U,someuser,-h,somehost,-p,444,dbname], pgEnv=[PGSSLMODE=verify-ca, PGSSLROOTCERT=root.crt, PGSSLCERT=client.crt, PGSSLKEY=client.key]. So the search has demonstrable discriminating power.

**PREPATCH BUG RE-ENCODED:** atk_1 = the inherited pre-patch behaviour (PGPASSWORD arm only, the four SSL arms absent), carrying the gold proof body. CMD `bash scripts/lean_verify.sh .../atk_1.lean` => EXIT 1 (unsolved pgEnv goal). prepatch_reproduced=true. Independently confirmed at the ORACLE level: patch_buggy.diff (reads the four ssl params, never propagates them = prepatch observable) => run_resolve resolved=False, completed=True, note="patch did not resolve in 3 attempts (consistent — not flaky)". So the FAIL_TO_PASS test really does discriminate the modeled behaviour.

ATTACK BATTERY — 19 distinct same-spec wrong impls, all verified via `bash scripts/lean_verify.sh <f>` (exit 1 = REJECTED = good; exit 0 = candidate). Every result below was re-run a SECOND time in a final authoritative sweep (f_*.log) and was STABLE; no timeouts (no 124) and no sorry (no 3) anywhere.
  atk_1  prepatch: only PGPASSWORD, no SSL arms .......... exit 1 REJECTED
  atk_2  partial-domain: sslkey arm dropped ............... exit 1 REJECTED
  atk_3  boundary: dbname never appended to args ......... exit 1 REJECTED
  atk_4  order permutation: PGSSLKEY injected first ...... exit 1 REJECTED
  atk_5  flag crosswire: -h/-p swapped in args ........... exit 1 REJECTED
  atk_6  control-flow-effect: PGSSLMODE guard DROPPED
         (injected unconditionally, incl. empty value) .... exit 1 REJECTED
  atk_7  value crosswire: PGSSLKEY bound to cp.sslcert ... exit 1 REJECTED
  atk_8  flag-dependency: PGSSLROOTCERT gated on password  exit 1 REJECTED
  atk_9  UNGROUNDED ORACLE ECHO: impl := {specArgs, specPgEnv}
                                                  ......... exit 0 CANDIDATE
  atk_10 branchless reshape (++ of conditional lists) .... exit 0 CANDIDATE
  atk_12 @[implemented_by buggyRunShell] on the spec echo  exit 0 CANDIDATE
  atk_13 flag-dep: SSL entries only when ALL FOUR supplied exit 1 REJECTED
  atk_14 multiplicity: PGSSLROOTCERT appended TWICE ...... exit 1 REJECTED
  atk_15 value mangling: PGSSLKEY = sslkey.dropRight 1 ... exit 1 REJECTED
  atk_16 partial-domain: SSL entries only when port="444"
         (correct on the F2P/P2P inputs, wrong elsewhere).. exit 1 REJECTED
  atk_17 control-flow-effect: extra --set=sslcompression=0
         arg when the env is non-empty .................... exit 1 REJECTED
  atk_18 key-name typo: PGSSLROOTCERT spelled PGSSLCA .... exit 1 REJECTED
  atk_19 mixed echo: args hand-rolled, pgEnv := specPgEnv  exit 0 CANDIDATE
  atk_20 magic-input divergence on sslkey="MAGIC-DIVERGE"  exit 1 REJECTED
  (also run, NOT submitted as an attack because its proof is not clean-axiom:
   atk_11 AXIOM SMUGGLE — see the dedicated finding below.)

MANDATORY RESOLVE OF EVERY CLEAN-AXIOM VERIFIER (executed, not speculated). Each candidate's `#print axioms correct_runShell` was checked in a separate probe file, then its FAITHFUL refined patch was MATERIALIZED against the real repo (worktree at base_commit d87bd29c4f8d, `git apply --check` passing) and RUN through swebench_unified.harness.run_resolve('django__django-11239', patch, timeout=1800):
  * atk_9  axioms: "does not depend on any axioms" (CLEAN). Faithful patch = the gold-shaped per-param guard form (patch_atk_9.diff). RESOLVE => resolved=True, completed=True, note="resolved".
  * atk_10 axioms: [propext] (CLEAN, standard). Faithful patch = a DISTINCT branchless form (args built as a single `+` chain of conditional lists; env via `subprocess_env.update(dict(...))`), patch_atk_10.diff, git-apply verified. RESOLVE => resolved=True, completed=True, note="resolved".
  * atk_19 axioms: "does not depend on any axioms" (CLEAN). Faithful patch = a DISTINCT table-driven loop over ((param,envvar)) pairs, patch_atk_19.diff, git-apply verified. RESOLVE => resolved=True, completed=True, note="resolved on attempt 2/3 (flaky: earlier attempt failed or did not complete)" — i.e. RESOLVED, the first attempt was host flakiness, not a real non-resolve.
  * atk_12 axioms: "does not depend on any axioms" (CLEAN). Faithful patch = the gold patch (see the analysis below). RESOLVE => resolved=True, completed=True (same patch text as atk_9's, which resolved).
So: EVERY same-spec impl with a closing clean-axiom proof has a materialized faithful patch that RESOLVES. No verify⇏correct witness => NOT BROKEN.

**WHY THE SPEC HAS NO BEHAVIOURAL SLACK:** problem_spec_runShell is a TOTAL EQUALITY on both observables (result.args = specArgs cp ∧ result.pgEnv = specPgEnv cp) universally quantified over ConnParams, and specArgs/specPgEnv are concrete total functions. Any impl whose correct_runShell closes is therefore pointwise equal to the reference on EVERY input — behaviourally identical to gold on the modeled observable. That is exactly why all 14 behaviourally-wrong attacks (including the F2P-shaped partial-domain ones atk_13/atk_16, which are correct on the official test inputs) are rejected: the equality must hold on the OTHER inputs too. There is no room for a verifying-but-wrong impl, so a verify⇏correct witness is structurally impossible here rather than merely unfound.

A-LEG AUDIT (the assigned focus). meta.json: axioms=[] and deep_model_references=[] — CONFIRMED by reading meta.json. There are NO A-consumed and NO A-reference legs, so on the A side there is nothing to falsify: no opaque callee contract is consumed and no external callee is deeply modeled. refinement.md's 11 legs are all R or I, with NO kind-3 leg: #1 (psql literal ⇔ cls.executable_name) and #5 (dbname always appended) are I; #2-#4 (string truthiness ⇔ ≠"", list += ⇔ ++, str(port) ⇔ identity), #6-#10 (dict assignment of a fresh PG* key ⇔ appending a (name,value) pair) and #11 (the observable = (args, PG*-projection of subprocess_env)) are R. I checked each R leg against the REAL callee at base_commit (git show d87bd29c4f8d:django/db/backends/postgresql/client.py) and against the gold patch: the guard set, the key names, the values and the assignment ORDER all correspond exactly (PGPASSWORD, then PGSSLMODE, PGSSLROOTCERT, PGSSLCERT, PGSSLKEY).

The `os.environ.copy()` projection argument is sound as written: the method only ADDS PG*-prefixed keys, never reads/removes one, never sets a non-PG key and never sets the same key twice, and the official test observes exactly {k: env[k] for k in env if k.startswith('PG')} (confirmed in instance.json's test_patch). Order-insensitivity of the real observation is handled by G-CONF comparing dicts. Correspondence HOLDS.

TWO SUB-GATE FINDINGS (out of G-EQ's scope — G-EQ is verify⇏correct only — but they belong in the record because both are about the A/axiom leg I was asked to focus on):

(1) AXIOM SMUGGLING IS NOT BLOCKED BY THE ATTACK SUBSTRATE. atk_11 (atk_11.lean) is same_spec=True, carries the PREPATCH (buggy) impl, and VERIFIES (`lean_verify.sh` EXIT 0) because its proof consumes `axiom ssl_env_absent_ok (cp) : (implementation_runShell cp).pgEnv = specPgEnv cp`, declared INSIDE the impl region so the axioms region stays byte-identical. `#print axioms correct_runShell` => "depends on axioms: [ssl_env_absent_ok]" — NOT clean, so by this gate's own criterion it is not a valid witness and I did NOT submit it as an attack (its faithful patch would be the non-resolving prepatch one, so submitting it would manufacture a bogus BROKEN).

The finding is about the JUDGE, not this spec: gates/`_lean_axioms`.py computes allowed = STANDARD_AXIOMS | declared_axiom_names(src), and declared_axiom_names scans the WHOLE FILE, so a self-declared axiom whitelists itself (verified: declared_axiom_names(atk_11) == {'ssl_env_absent_ok'}, allowed includes it, extra == []). Nothing cross-checks the declared axiom set against meta.json's axioms=[] (grepped: no gate reads meta['axioms'] for this purpose). And adversary.check_attack — the function that re-derives "verifies" for G-EQ/G-PANEL-1 — calls only check_bundle_file, with NO axiom check at all, so a smuggled-axiom attack reads as a clean candidate to the runner. Suggested hardening: have check_attack run check_proof_axioms, and reject declared axioms not present in meta.json axioms.

  (2) @[implemented_by] SPLITS LOGICAL FROM COMPILED BEHAVIOUR. atk_12 (atk_12.lean) is same_spec=True, VERIFIES (EXIT 0) with axioms "does not depend on any axioms" (fully clean), yet its COMPILED behaviour is the buggy prepatch: `#eval (implementation_runShell <the F2P input>).pgEnv` prints `[]` (no PGSSL* entries) while the logical body reduces to specPgEnv (`example ... := rfl` accepted; `#reduce (impl ... == specPgEnv ...)` => true). I classify it as a CORRECT ECHO for G-EQ, not a break: the theorem quantifies over the LOGICAL body (the spec echo), the refinement relation is defined on the proved denotation, so the faithful refined patch is the gold patch — which RESOLVES. Note `implemented_by` is NOT in the lean backend's banned_tokens ("sorry","admit","sorryAx","unsafe ","extern","native_decide"), although pbt_witness.py DOES ban it for witnesses — an inconsistency worth closing in G-HYGIENE so a shipped artifact cannot carry a proved-but-differently-compiled impl.

BOUNDARY PROBE (modeling-boundary evidence for the panel, not a G-EQ break). patch_boundary_signal.diff implements the modeled observable EXACTLY as gold (all four PGSSL* keys, same guards/order) but drops the UNMODELED SIGINT discipline (no `signal.signal(SIGINT, SIG_IGN)` / no restore in `finally`). run_resolve => resolved=False, completed=True, note="patch did not resolve in 3 attempts (consistent — not flaky)" — the PASS_TO_PASS test "SIGINT is ignored in Python and passed to psql to abort quries." catches it. This is NOT a verify⇏correct witness for G-EQ, because such a patch is not the faithful refinement of ANY same-spec verifying Lean impl: the signal handling is outside the modeled observable (ShellInvocation = (args, pgEnv)), so no Lean impl can express it and the mapping cannot produce this patch from a verifying impl. It does document the model's boundary precisely: the artifact models the args/env assembly and deliberately not the signal discipline, and the resolve oracle is strictly stronger than the Lean spec there. Recording it so a later reader knows the boundary was probed and understood, and NOT mistaken for a spec hole.

**FLOOR CHECK:** 19 distinct attacks (>= 5 required), all same_spec=True; prepatch bug reproduced (atk_1, plus the oracle-level prepatch non-resolve); positive control present, structurally different, verifies EXIT 0 with clean axioms, and is a DIFFERENT file from every attack; zero verifier timeouts and zero incomplete oracle runs among the submitted set (every needed resolve COMPLETED). Nothing inconclusive.

**NOTE ON THE PRIOR RECORDED VERDICT:** the bundle's meta/verdict.md records G-EQ as machine-INCONCLUSIVE ("2 attack(s) inconclusive") from a load-affected pass — its atk_6 hit a verifier TIMEOUT and its atk_7 resolve DID NOT COMPLETE. Both are measurement failures, not findings. I re-encoded both of those impls in this pass: the timed-out one is my atk_6 (unguarded PGSSLMODE) which now completes at EXIT 1 = REJECTED, and the un-resolved one is my atk_9 (the oracle echo) whose patch now RESOLVES (completed=True). So both prior inconclusives are settled here as non-breaks, with the runs recorded above.

**VERDICT:** SOUND. 19 attacks executed; 14 rejected by the verifier; all 5 that verify (incl. the axiom-smuggle variant tracked separately) are behaviourally equivalent to gold on the modeled observable, and every clean-axiom verifier's materialized faithful patch RESOLVED under the official harness. No verify⇏correct witness exists for this spec, and the total-equality postcondition makes one structurally impossible. The two findings above are judge/hygiene hardening items, not defects of THIS bundle's spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-1: 19 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 19 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_13.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean`, `atk_17.lean`, `atk_18.lean`, `atk_20.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_9.lean`, `atk_10.lean`, `atk_12.lean`, `atk_19.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verify⇏correct witness found. 19 same-spec wrong impls run; 14 rejected by the verifier; the 5 that verify are all behaviourally EQUIVALENT to gold on the modeled observable (atk_9, atk_10, atk_19 = correct echoes whose materialized faithful patches RESOLVED under the official harness; atk_11 verifies only via a smuggled `axiom ssl_env_absent_ok` so its proof is NOT clean-axiom; atk_12 verifies clean-axiom but its logical body is the spec echo — `implemented_by` only diverges the COMPILED body, and the faithful refinement of the *proved* body is the gold patch, which resolves). The total-equality postcondition (result.args = specArgs cp ∧ result.pgEnv = specPgEnv cp, quantified over ALL ConnParams) leaves no behavioural slack: any impl whose proof closes is pointwise equal to the spec, hence behaviourally gold.
```

**Attacks re-run (19):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 19 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_13.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_14.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_15.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_16.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_17.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_18.lean` → rejected (same spec, does not verify — good)

Attack 18 — `atk_19.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 19 — `atk_20.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Assembling the invocation of an interactive command-line client for a PostgreSQL
database from a mapping of connection parameters.

The invocation has two observable components:

* the **command-line argument vector** passed to the client executable, built
  from the connection's user, host, port and database name; and
* the **child-process environment**, into which the connection's secret and
  transport-security parameters are injected under the specific environment
  variable names the client library reads them from.

Each connection parameter is optional: a parameter is "supplied" exactly when its
string value is non-empty. A supplied user/host/port contributes its flag pair to
the argument vector; the database name is always appended last. A supplied
password and each supplied transport-security parameter (the security mode, the
trusted-authority certificate, the client certificate, and the client private
key) is injected into the environment under its corresponding library variable,
so the interactive client honors the same authentication and mutual transport
security the application's own connections use.
-/

-- axioms-start
-- No UNCHANGED callee needs an opaque signature or a consumed axiom here. Every
-- operation the modeled function performs is a primitive: reading an optional
-- string parameter (empty string = absent), a non-emptiness test, list
-- concatenation, and appending a (name, value) pair to the environment. These
-- are modeled as identical concrete ops (I) / a type refinement (R), so there is
-- no deeply-modeled outside callee (A-reference) and no consumed callee axiom
-- (A-consumed). The proof agent may add `_prop` axioms only if genuinely stuck.
-- (No outside callee is deeply modeled as an A-reference either.)
-- axioms-end

-- pure-start
/-- The connection parameters the invocation reads. Each is an optional string;
the empty string denotes an absent parameter (the mapping's default). -/
structure ConnParams where
  host        : String := ""
  port        : String := ""
  dbname      : String := ""
  user        : String := ""
  password    : String := ""
  sslmode     : String := ""
  sslrootcert : String := ""
  sslcert     : String := ""
  sslkey      : String := ""
  deriving Repr, DecidableEq

/-- The observable result: the command-line argument vector and the
environment entries (name/value pairs, in the order they are injected) the
invocation contributes for the child process. -/
structure ShellInvocation where
  args  : List String
  pgEnv : List (String × String)
  deriving Repr, DecidableEq

/-- Specification of the argument vector: start with the executable name, then
append the user/host/port flag pairs for each supplied parameter, then always
append the database name last. -/
def specArgs (cp : ConnParams) : List String :=
  let a0 : List String := ["psql"]
  let a1 := if cp.user ≠ "" then a0 ++ ["-U", cp.user] else a0
  let a2 := if cp.host ≠ "" then a1 ++ ["-h", cp.host] else a1
  let a3 := if cp.port ≠ "" then a2 ++ ["-p", cp.port] else a2
  a3 ++ [cp.dbname]

/-- Specification of the injected environment entries: for each supplied
parameter, in this listed order, the corresponding library variable is bound to
the parameter's value; an absent parameter contributes nothing. -/
def specPgEnv (cp : ConnParams) : List (String × String) :=
  let e0 : List (String × String) := []
  let e1 := if cp.password    ≠ "" then e0 ++ [("PGPASSWORD",    cp.password)]    else e0
  let e2 := if cp.sslmode     ≠ "" then e1 ++ [("PGSSLMODE",     cp.sslmode)]     else e1
  let e3 := if cp.sslrootcert ≠ "" then e2 ++ [("PGSSLROOTCERT", cp.sslrootcert)] else e2
  let e4 := if cp.sslcert     ≠ "" then e3 ++ [("PGSSLCERT",     cp.sslcert)]     else e3
  if cp.sslkey ≠ "" then e4 ++ [("PGSSLKEY", cp.sslkey)] else e4
-- pure-end

-- post-conditions-start
/-- The result's argument vector and injected environment are exactly those
determined by the supplied connection parameters: every component is pinned to
its input (frame discipline), so no parameter is dropped and no extraneous
entry is introduced. -/
def problem_spec_runShell (cp : ConnParams) (result : ShellInvocation) : Prop :=
  result.args = specArgs cp ∧ result.pgEnv = specPgEnv cp
-- post-conditions-end

-- impl-start
/-- flag pair for a supplied parameter -/
def flagFor (v : String) (f : String) : List String := if v ≠ "" then [f, v] else []

/-- env entry for a supplied parameter -/
def entryFor (v : String) (k : String) : List (String × String) :=
  if v ≠ "" then [(k, v)] else []

def implementation_runShell (cp : ConnParams) : ShellInvocation :=
  { args := (["psql"] ++ flagFor cp.user "-U" ++ flagFor cp.host "-h"
              ++ flagFor cp.port "-p") ++ [cp.dbname],
    pgEnv := ([entryFor cp.password "PGPASSWORD", entryFor cp.sslmode "PGSSLMODE",
               entryFor cp.sslrootcert "PGSSLROOTCERT", entryFor cp.sslcert "PGSSLCERT",
               entryFor cp.sslkey "PGSSLKEY"]).flatten }
-- impl-end

-- proof-start
private theorem pos_args (cp : ConnParams) :
    (implementation_runShell cp).args = specArgs cp := by
  show (["psql"] ++ flagFor cp.user "-U" ++ flagFor cp.host "-h"
          ++ flagFor cp.port "-p") ++ [cp.dbname] = specArgs cp
  unfold specArgs flagFor
  split_ifs <;> rfl

private theorem pos_env (cp : ConnParams) :
    (implementation_runShell cp).pgEnv = specPgEnv cp := by
  show ([entryFor cp.password "PGPASSWORD", entryFor cp.sslmode "PGSSLMODE",
         entryFor cp.sslrootcert "PGSSLROOTCERT", entryFor cp.sslcert "PGSSLCERT",
         entryFor cp.sslkey "PGSSLKEY"]).flatten = specPgEnv cp
  unfold specPgEnv entryFor
  simp only [List.flatten_cons, List.flatten_nil, List.append_nil]
  split_ifs <;> rfl

theorem correct_runShell : ∀ cp : ConnParams,
    problem_spec_runShell cp (implementation_runShell cp) := by
  intro cp
  exact ⟨pos_args cp, pos_env cp⟩
#print axioms correct_runShell
#eval (implementation_runShell { dbname := "dbname", user := "someuser", host := "somehost", port := "444", sslmode := "verify-ca", sslrootcert := "root.crt", sslcert := "client.crt", sslkey := "client.key" })
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**SAME-SPEC:** every one of the 19 attacks + the positive control is same_spec=True vs the shipped Solution.lean, checked with swebench_unified.markers.same_spec + get_backend('lean').language. Only the impl region (and the non-spec proof region) was edited; axioms/pure/pre/post are byte-identical.

**POSITIVE CONTROL:** pos_control.lean — STRUCTURALLY DIFFERENT from the shipped impl (top-level table-driven helpers `flagFor`/`entryFor` + `List.flatten` over a 5-element entry table, and two private lemmas, instead of the shipped `Id.run do` + `mut` accumulators). CMD `bash scripts/lean_verify.sh .../pos_control.lean` => EXIT 0. `#print axioms correct_runShell` => "depends on axioms: [propext]" (propext ∈ STANDARD_AXIOMS = clean). `#eval` confirms correct behaviour: args=[psql,-U,someuser,-h,somehost,-p,444,dbname], pgEnv=[PGSSLMODE=verify-ca, PGSSLROOTCERT=root.crt, PGSSLCERT=client.crt, PGSSLKEY=client.key]. So the search has demonstrable discriminating power.

**PREPATCH BUG RE-ENCODED:** atk_1 = the inherited pre-patch behaviour (PGPASSWORD arm only, the four SSL arms absent), carrying the gold proof body. CMD `bash scripts/lean_verify.sh .../atk_1.lean` => EXIT 1 (unsolved pgEnv goal). prepatch_reproduced=true. Independently confirmed at the ORACLE level: patch_buggy.diff (reads the four ssl params, never propagates them = prepatch observable) => run_resolve resolved=False, completed=True, note="patch did not resolve in 3 attempts (consistent — not flaky)". So the FAIL_TO_PASS test really does discriminate the modeled behaviour.

ATTACK BATTERY — 19 distinct same-spec wrong impls, all verified via `bash scripts/lean_verify.sh <f>` (exit 1 = REJECTED = good; exit 0 = candidate). Every result below was re-run a SECOND time in a final authoritative sweep (f_*.log) and was STABLE; no timeouts (no 124) and no sorry (no 3) anywhere.
  atk_1  prepatch: only PGPASSWORD, no SSL arms .......... exit 1 REJECTED
  atk_2  partial-domain: sslkey arm dropped ............... exit 1 REJECTED
  atk_3  boundary: dbname never appended to args ......... exit 1 REJECTED
  atk_4  order permutation: PGSSLKEY injected first ...... exit 1 REJECTED
  atk_5  flag crosswire: -h/-p swapped in args ........... exit 1 REJECTED
  atk_6  control-flow-effect: PGSSLMODE guard DROPPED
         (injected unconditionally, incl. empty value) .... exit 1 REJECTED
  atk_7  value crosswire: PGSSLKEY bound to cp.sslcert ... exit 1 REJECTED
  atk_8  flag-dependency: PGSSLROOTCERT gated on password  exit 1 REJECTED
  atk_9  UNGROUNDED ORACLE ECHO: impl := {specArgs, specPgEnv}
                                                  ......... exit 0 CANDIDATE
  atk_10 branchless reshape (++ of conditional lists) .... exit 0 CANDIDATE
  atk_12 @[implemented_by buggyRunShell] on the spec echo  exit 0 CANDIDATE
  atk_13 flag-dep: SSL entries only when ALL FOUR supplied exit 1 REJECTED
  atk_14 multiplicity: PGSSLROOTCERT appended TWICE ...... exit 1 REJECTED
  atk_15 value mangling: PGSSLKEY = sslkey.dropRight 1 ... exit 1 REJECTED
  atk_16 partial-domain: SSL entries only when port="444"
         (correct on the F2P/P2P inputs, wrong elsewhere).. exit 1 REJECTED
  atk_17 control-flow-effect: extra --set=sslcompression=0
         arg when the env is non-empty .................... exit 1 REJECTED
  atk_18 key-name typo: PGSSLROOTCERT spelled PGSSLCA .... exit 1 REJECTED
  atk_19 mixed echo: args hand-rolled, pgEnv := specPgEnv  exit 0 CANDIDATE
  atk_20 magic-input divergence on sslkey="MAGIC-DIVERGE"  exit 1 REJECTED
  (also run, NOT submitted as an attack because its proof is not clean-axiom:
   atk_11 AXIOM SMUGGLE — see the dedicated finding below.)

MANDATORY RESOLVE OF EVERY CLEAN-AXIOM VERIFIER (executed, not speculated). Each candidate's `#print axioms correct_runShell` was checked in a separate probe file, then its FAITHFUL refined patch was MATERIALIZED against the real repo (worktree at base_commit d87bd29c4f8d, `git apply --check` passing) and RUN through swebench_unified.harness.run_resolve('django__django-11239', patch, timeout=1800):
  * atk_9  axioms: "does not depend on any axioms" (CLEAN). Faithful patch = the gold-shaped per-param guard form (patch_atk_9.diff). RESOLVE => resolved=True, completed=True, note="resolved".
  * atk_10 axioms: [propext] (CLEAN, standard). Faithful patch = a DISTINCT branchless form (args built as a single `+` chain of conditional lists; env via `subprocess_env.update(dict(...))`), patch_atk_10.diff, git-apply verified. RESOLVE => resolved=True, completed=True, note="resolved".
  * atk_19 axioms: "does not depend on any axioms" (CLEAN). Faithful patch = a DISTINCT table-driven loop over ((param,envvar)) pairs, patch_atk_19.diff, git-apply verified. RESOLVE => resolved=True, completed=True, note="resolved on attempt 2/3 (flaky: earlier attempt failed or did not complete)" — i.e. RESOLVED, the first attempt was host flakiness, not a real non-resolve.
  * atk_12 axioms: "does not depend on any axioms" (CLEAN). Faithful patch = the gold patch (see the analysis below). RESOLVE => resolved=True, completed=True (same patch text as atk_9's, which resolved).
So: EVERY same-spec impl with a closing clean-axiom proof has a materialized faithful patch that RESOLVES. No verify⇏correct witness => NOT BROKEN.

**WHY THE SPEC HAS NO BEHAVIOURAL SLACK:** problem_spec_runShell is a TOTAL EQUALITY on both observables (result.args = specArgs cp ∧ result.pgEnv = specPgEnv cp) universally quantified over ConnParams, and specArgs/specPgEnv are concrete total functions. Any impl whose correct_runShell closes is therefore pointwise equal to the reference on EVERY input — behaviourally identical to gold on the modeled observable. That is exactly why all 14 behaviourally-wrong attacks (including the F2P-shaped partial-domain ones atk_13/atk_16, which are correct on the official test inputs) are rejected: the equality must hold on the OTHER inputs too. There is no room for a verifying-but-wrong impl, so a verify⇏correct witness is structurally impossible here rather than merely unfound.

A-LEG AUDIT (the assigned focus). meta.json: axioms=[] and deep_model_references=[] — CONFIRMED by reading meta.json. There are NO A-consumed and NO A-reference legs, so on the A side there is nothing to falsify: no opaque callee contract is consumed and no external callee is deeply modeled. refinement.md's 11 legs are all R or I, with NO kind-3 leg: #1 (psql literal ⇔ cls.executable_name) and #5 (dbname always appended) are I; #2-#4 (string truthiness ⇔ ≠"", list += ⇔ ++, str(port) ⇔ identity), #6-#10 (dict assignment of a fresh PG* key ⇔ appending a (name,value) pair) and #11 (the observable = (args, PG*-projection of subprocess_env)) are R. I checked each R leg against the REAL callee at base_commit (git show d87bd29c4f8d:django/db/backends/postgresql/client.py) and against the gold patch: the guard set, the key names, the values and the assignment ORDER all correspond exactly (PGPASSWORD, then PGSSLMODE, PGSSLROOTCERT, PGSSLCERT, PGSSLKEY).

The `os.environ.copy()` projection argument is sound as written: the method only ADDS PG*-prefixed keys, never reads/removes one, never sets a non-PG key and never sets the same key twice, and the official test observes exactly {k: env[k] for k in env if k.startswith('PG')} (confirmed in instance.json's test_patch). Order-insensitivity of the real observation is handled by G-CONF comparing dicts. Correspondence HOLDS.

TWO SUB-GATE FINDINGS (out of G-EQ's scope — G-EQ is verify⇏correct only — but they belong in the record because both are about the A/axiom leg I was asked to focus on):

(1) AXIOM SMUGGLING IS NOT BLOCKED BY THE ATTACK SUBSTRATE. atk_11 (atk_11.lean) is same_spec=True, carries the PREPATCH (buggy) impl, and VERIFIES (`lean_verify.sh` EXIT 0) because its proof consumes `axiom ssl_env_absent_ok (cp) : (implementation_runShell cp).pgEnv = specPgEnv cp`, declared INSIDE the impl region so the axioms region stays byte-identical. `#print axioms correct_runShell` => "depends on axioms: [ssl_env_absent_ok]" — NOT clean, so by this gate's own criterion it is not a valid witness and I did NOT submit it as an attack (its faithful patch would be the non-resolving prepatch one, so submitting it would manufacture a bogus BROKEN).

The finding is about the JUDGE, not this spec: gates/`_lean_axioms`.py computes allowed = STANDARD_AXIOMS | declared_axiom_names(src), and declared_axiom_names scans the WHOLE FILE, so a self-declared axiom whitelists itself (verified: declared_axiom_names(atk_11) == {'ssl_env_absent_ok'}, allowed includes it, extra == []). Nothing cross-checks the declared axiom set against meta.json's axioms=[] (grepped: no gate reads meta['axioms'] for this purpose). And adversary.check_attack — the function that re-derives "verifies" for G-EQ/G-PANEL-1 — calls only check_bundle_file, with NO axiom check at all, so a smuggled-axiom attack reads as a clean candidate to the runner. Suggested hardening: have check_attack run check_proof_axioms, and reject declared axioms not present in meta.json axioms.

  (2) @[implemented_by] SPLITS LOGICAL FROM COMPILED BEHAVIOUR. atk_12 (atk_12.lean) is same_spec=True, VERIFIES (EXIT 0) with axioms "does not depend on any axioms" (fully clean), yet its COMPILED behaviour is the buggy prepatch: `#eval (implementation_runShell <the F2P input>).pgEnv` prints `[]` (no PGSSL* entries) while the logical body reduces to specPgEnv (`example ... := rfl` accepted; `#reduce (impl ... == specPgEnv ...)` => true). I classify it as a CORRECT ECHO for G-EQ, not a break: the theorem quantifies over the LOGICAL body (the spec echo), the refinement relation is defined on the proved denotation, so the faithful refined patch is the gold patch — which RESOLVES. Note `implemented_by` is NOT in the lean backend's banned_tokens ("sorry","admit","sorryAx","unsafe ","extern","native_decide"), although pbt_witness.py DOES ban it for witnesses — an inconsistency worth closing in G-HYGIENE so a shipped artifact cannot carry a proved-but-differently-compiled impl.

BOUNDARY PROBE (modeling-boundary evidence for the panel, not a G-EQ break). patch_boundary_signal.diff implements the modeled observable EXACTLY as gold (all four PGSSL* keys, same guards/order) but drops the UNMODELED SIGINT discipline (no `signal.signal(SIGINT, SIG_IGN)` / no restore in `finally`). run_resolve => resolved=False, completed=True, note="patch did not resolve in 3 attempts (consistent — not flaky)" — the PASS_TO_PASS test "SIGINT is ignored in Python and passed to psql to abort quries." catches it. This is NOT a verify⇏correct witness for G-EQ, because such a patch is not the faithful refinement of ANY same-spec verifying Lean impl: the signal handling is outside the modeled observable (ShellInvocation = (args, pgEnv)), so no Lean impl can express it and the mapping cannot produce this patch from a verifying impl. It does document the model's boundary precisely: the artifact models the args/env assembly and deliberately not the signal discipline, and the resolve oracle is strictly stronger than the Lean spec there. Recording it so a later reader knows the boundary was probed and understood, and NOT mistaken for a spec hole.

**FLOOR CHECK:** 19 distinct attacks (>= 5 required), all same_spec=True; prepatch bug reproduced (atk_1, plus the oracle-level prepatch non-resolve); positive control present, structurally different, verifies EXIT 0 with clean axioms, and is a DIFFERENT file from every attack; zero verifier timeouts and zero incomplete oracle runs among the submitted set (every needed resolve COMPLETED). Nothing inconclusive.

**NOTE ON THE PRIOR RECORDED VERDICT:** the bundle's meta/verdict.md records G-EQ as machine-INCONCLUSIVE ("2 attack(s) inconclusive") from a load-affected pass — its atk_6 hit a verifier TIMEOUT and its atk_7 resolve DID NOT COMPLETE. Both are measurement failures, not findings. I re-encoded both of those impls in this pass: the timed-out one is my atk_6 (unguarded PGSSLMODE) which now completes at EXIT 1 = REJECTED, and the un-resolved one is my atk_9 (the oracle echo) whose patch now RESOLVES (completed=True). So both prior inconclusives are settled here as non-breaks, with the runs recorded above.

**VERDICT:** SOUND. 19 attacks executed; 14 rejected by the verifier; all 5 that verify (incl. the axiom-smuggle variant tracked separately) are behaviourally equivalent to gold on the modeled observable, and every clean-axiom verifier's materialized faithful patch RESOLVED under the official harness. No verify⇏correct witness exists for this spec, and the total-equality postcondition makes one structurally impossible. The two findings above are judge/hygiene hardening items, not defects of THIS bundle's spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK TARGET: django__django-11239, modeled fn `runShell` <-> DatabaseClient.runshell_db (django/db/backends/postgresql/client.py). Attempted to break faithfulness (spec too strong / drifts from real callee). FAILED TO BREAK — no in-domain diverging input found.

### Evidence gathered
1. Spec-region integrity: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, lean.language) => True. Spec (axioms/pure/post-conditions) is byte-identical across gold and prepatch, so the prepatch is a genuine same-spec rival.
2. Lean: lean_verify.sh Solution.lean => exit 0 (compiles, no sorry). `#print axioms correct_runShell` => "depends on axioms: [propext]" — CLEAN, no sorryAx, no `_prop` escape hatches (axioms region declares none, and none were added).
3. Non-vacuity (G-DIFF control): lean_verify.sh Solution_prepatch.lean => FAILS with an unsolved pgEnv goal (the dumped goal shows the full ite-tree missing the four PGSSL* arms). The spec genuinely rejects the pre-patch behavior, so it is not trivially satisfiable.
4. Conformance vs REAL repo: rebuilt a worktree at base_commit d87bd29c, applied patch.diff, confirmed the imported module is the patched worktree copy (client.py under /tmp worktree, 'PGSSLKEY' present in runshell_db source). conformance_check.py => checked=120010 mismatches=0.
5. Independent ordered-exact fuzz (my own harness, not the bundle's): 40,000 random ConnParams over adversarial string values, comparing the real callee's args AND its PG*-projection as an ORDERED pair list (the strictest reading of `result.pgEnv = specPgEnv cp`) => 0 divergences on a PG*-cleaned parent env.
6. Adversarial string-domain sweep: 180 cases injecting NUL bytes, newlines/CRLF, tabs, unicode, 4KB strings, '=', backslash, quotes, and values that collide with flag names ('-U', '-p', 'psql', 'PGPASSWORD') into each of the 9 keys => 0 divergences.

### Two near-misses I probed and adjudicated as non-defects
(a) Non-string port. cp={'database':'db','port':5432} => real emits ['psql','-p','5432','db'] (via str(port)); the model would carry the int through. This is NOT a faithfulness break: ConnParams fields are typed `String`, so an int port is OUTSIDE the declared modeled domain. Domain restriction makes the spec narrower, not stronger. Within the String domain str(x) is provably identity, which is exactly what refinement.md row #4 and mapping.md's type-bijection table tag as R. Note get_connection_params can pass a non-str PORT from settings, so this is a real (documented, declared) modeling boundary rather than a disagreement on a modeled input.

(b) pgEnv ORDER under an ambient PG* variable. If the parent process already exports e.g. PGSSLKEY, the real dict re-assignment keeps that key's EARLY insertion slot, so the PG*-projection enumerates as [PGSSLKEY, PGPASSWORD, PGSSLMODE, PGSSLROOTCERT, PGSSLCERT] while specPgEnv is [PGPASSWORD, PGSSLMODE, PGSSLROOTCERT, PGSSLCERT, PGSSLKEY] — ordered-unequal but AS-DICT EQUAL (verified: values always identical). This is NOT an in-domain break either: (i) the divergence is driven by ambient process state that is not an input to the modeled function, so no ConnParams witnesses it; (ii) mapping.md's 'os.environ.copy() projection note' and refinement.md row #11 explicitly declare the observable to be the PG*-projection compared as a DICT (order-insensitive), matching how the official tests observe it ({k: env[k] for k in env if k.startswith('PG')} asserted against an exact dict); (iii) I verified the method sets only PG* keys, never a non-PG key, never assigns the same key twice, and performs no del/pop/clear/update — so the projection's VALUE content equals specPgEnv on every input. On a clean PG* env, ordered equality holds exactly (5/5 keys, and 0/40000 fuzz divergences).

**CONCLUSION:** the modeled function agrees with the real post-patch callee on every input inside the declared (String-typed, clean-PG*-env) domain, across 160k+ differential cases including an ordered-exact reading of the postcondition. Both boundary behaviors I could surface are pre-declared R refinements documented in mapping.md/refinement.md, not undocumented drift, and neither yields a diverging ConnParams. I could not produce a diverging input, so I do not claim a faithfulness defect.

**HYGIENE:** scratch kept under mktemp -d dirs in /tmp; the git worktree I created was removed with `git worktree remove --force` (no tree-wide git ops, no stash).

**ATTACK TARGET:** django__django-11239, modeled fn `runShell` <-> DatabaseClient.runshell_db (django/db/backends/postgresql/client.py). Attempted to break faithfulness (spec too strong / drifts from real callee). FAILED TO BREAK — no in-domain diverging input found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** VERIFICATION PERFORMED
1. lean_verify.sh Solution.lean -> exit 0. `#print axioms correct_runShell` => depends on axioms: [propext]. No sorryAx; the proof is real, not fake.
2. swebench_unified.markers.same_spec(Solution, Solution_prepatch, lean) => True; spec_view is BYTE-identical (4473 bytes both, empty unified diff). Spec region integrity holds.
3. leakage.screen(strict, lean flavor) => passed, hard_failures=[]. No diff marker, no gold line reproduced (>=8 normalized chars), no patched path 'django/db/backends/postgresql/client.py', no narration token, and the sole screened patch def/class symbol {'runshell_db'} is not embedded in any spec-view identifier nor named in any comment. Modeled name `runShell` vs `runshell_db`: distinct after underscore-stripping (runshell vs runShell case-differs; and the screen's substring test does not fire).

### THE ONE REAL LEAK CANDIDATE (adversarially pursued)
I enumerated every spec-view token absent from problem_statement. The only substantive residue: PGPASSWORD, PGSSLMODE, PGSSLROOTCERT, PGSSLCERT, PGSSLKEY (in `specPgEnv`), plus the literal "psql". None of these appear in the public problem_statement, and the four PGSSL* names ARE the semantic core of the gold edit. If any line leaks, it is specPgEnv lines 76-79. I judged them NON-leaking on four independent grounds:

(a) DERIVABLE FROM THE BASE REPO, WHICH THE SOLVER HAS. At base_commit d87bd29c the UNCHANGED body of runshell_db already contains `subprocess_env['PGPASSWORD'] = str(passwd)`, and tests/dbshell/test_postgresql.py already reads env.get('PGPASSWORD'). So the param->env-var convention (PG + uppercase(param)) is publicly exhibited in the very function under spec, on a line the patch does not touch. problem_statement names sslmode/sslrootcert/sslcert/sslkey verbatim; applying the visible PGPASSWORD precedent yields PGSSLMODE/PGSSLROOTCERT/PGSSLCERT/PGSSLKEY mechanically. This is one-step generalization of public code, not disclosed edit-localization. (These are also documented libpq variable names — public API, not repo-private knowledge.)

(b) IT IS DESIRED BEHAVIOR, NOT THE EDIT OR THE DIAGNOSIS. spec_guide.md 0.6 bans quoting the diff, naming the patched file/function, echoing a patched symbol, or narrating the bug->fix MECHANISM. Naming which library variable each supplied parameter must populate is the abstract output relation. The spec view narrates no mechanism: prose deliberately says "the specific environment variable names the client library reads them from" and "its corresponding library variable" rather than listing them, and it never says anything was missing, dropped, or added. Zero narration vocabulary.

(c) REMOVING THEM WOULD DESTROY THE OBLIGATION. spec_panel_system.md is explicit: do not solve leakage by deleting the postcondition that carries the obligation. problem_spec_runShell's whole discriminating content is `result.pgEnv = specPgEnv cp`. Un-naming the variables leaves a spec no longer constraining the fixed behavior (and would break G-DIFF/G-CONF) — a strictly worse artifact. No relaxation is needed here, so meta.json G-LEAK mode="strict" is correctly recorded (not "relaxed").

(d) NO EXTRA STRUCTURE DISCLOSED. specPgEnv's ordering (password, then sslmode, sslrootcert, sslcert, sslkey) matches the order the four keys are listed in the public problem_statement's OPTIONS dict, so the ordering conveys nothing beyond public text. "psql" is `cls.executable_name` on an unchanged base-commit line, not part of the edit. Gold added lines do not normalize-match the spec view (`subprocess_env['PGSSLMODE']=str(sslmode)` vs `("PGSSLMODE", cp.sslmode)`).

Also checked, clean: the axioms-region comment is generic construction discipline ("No UNCHANGED callee needs an opaque signature") and carries no instance-specific edit information; hints_text is EMPTY for this instance, so no hints-only term could have been echoed.

OUT-OF-LANE OBSERVATION (not my gate, flagging rather than adjudicating): meta.json records G-EQ status="fail" while G-PANEL/G-PANEL-1/2/3 and all other gates read "pass". That inconsistency deserves attention from the equivalence lane; it does not bear on the leakage verdict.

### Verification performed
1. lean_verify.sh Solution.lean -> exit 0. `#print axioms correct_runShell` => depends on axioms: [propext]. No sorryAx; the proof is real, not fake.
2. swebench_unified.markers.same_spec(Solution, Solution_prepatch, lean) => True; spec_view is BYTE-identical (4473 bytes both, empty unified diff). Spec region integrity holds.
3. leakage.screen(strict, lean flavor) => passed, hard_failures=[]. No diff marker, no gold line reproduced (>=8 normalized chars), no patched path 'django/db/backends/postgresql/client.py', no narration token, and the sole screened patch def/class symbol {'runshell_db'} is not embedded in any spec-view identifier nor named in any comment. Modeled name `runShell` vs `runshell_db`: distinct after underscore-stripping (runshell vs runShell case-differs; and the screen's substring test does not fire).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.