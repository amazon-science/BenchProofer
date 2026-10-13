# P2 adversarial audit — django__django-14771

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None: no same-spec wrong impl closes. The spec problem_spec_reloaderArgv is a TOTAL FUNCTIONAL EQUALITY pinning result to the unique closed form ([exe]++warn.map warnArg) ++ (if isCpython then xopts.map xoptArg else []) ++ argv. By funext any impl closing correct_ is extensionally equal to gold on ALL inputs, hence behaviorally identical and must resolve. There is no closing-but-unresolving refinement, so no faithful patch was materialized/resolve-run (nothing to run). Machine-checked disproofs prove each attacked impl diverges at a concrete witness: dis_1 (prepatch, drops -Xutf8) reduces to ¬ ['py','m']=['py','-Xutf8','m']; dis_2 (ungated -X, adds -Xk when isCpython=false); dis_3 (reversed xopt order); dis_4 (-X block after argv); dis_5 (valued -X drops =value) — all exit 0.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,24 +70,15 @@
 def implementation_reloaderArgv
     (executable : String) (warnoptions : List String) (isCpython : Bool)
     (xoptions : List (String × XVal)) (argv : List String) : List String := Id.run do
-  -- Start from the executable and append one `-W` token per warning option.
+  -- drop -X block entirely (prepatch bug)
   let mut args := [executable]
   for o in warnoptions do
     args := args ++ [warnArg o]
-  -- On the CPython implementation, forward every active `-X` interpreter option.
-  if isCpython then
-    for kv in xoptions do
-      args := args ++ [xoptArg kv]
-  -- On the common relaunch path the original invocation arguments are appended
-  -- unchanged.
   args := args ++ argv
   return args
 -- impl-end
 
 -- proof-start
-/-- A `for x in xs do acc := acc ++ [f x]` loop (over a `List`, in `Id`) builds
-exactly `init ++ xs.map f`. Generalized over the accumulator so the induction
-goes through. -/
 theorem forIn_yield_append {α β : Type} (xs : List α) (init : List β) (f : α → β) :
     (forIn xs init (fun x r => ForInStep.yield (r ++ [f x])) : Id (List β))
       = init ++ xs.map f := by
@@ -109,5 +100,7 @@
   simp only [Id.run, bind, pure]
   cases isCpython <;>
     simp only [forIn_yield_append, Bool.false_eq_true, if_true, if_false,
-      List.append_assoc, List.singleton_append, List.nil_append]
+      List.append_assoc, List.singleton_append, List.nil_append, List.map_reverse,
+      List.reverse_cons, List.reverse_nil] <;>
+    simp_all [List.append_assoc] <;> rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,36 +69,10 @@
 -- impl-start
 def implementation_reloaderArgv
     (executable : String) (warnoptions : List String) (isCpython : Bool)
-    (xoptions : List (String × XVal)) (argv : List String) : List String := Id.run do
-  -- Start from the executable and append one `-W` token per warning option.
-  let mut args := [executable]
-  for o in warnoptions do
-    args := args ++ [warnArg o]
-  -- On the CPython implementation, forward every active `-X` interpreter option.
-  if isCpython then
-    for kv in xoptions do
-      args := args ++ [xoptArg kv]
-  -- On the common relaunch path the original invocation arguments are appended
-  -- unchanged.
-  args := args ++ argv
-  return args
+    (xoptions : List (String × XVal)) (argv : List String) : List String := ([executable] ++ warnoptions.map warnArg) ++ xoptions.map xoptArg ++ argv
 -- impl-end
 
 -- proof-start
-/-- A `for x in xs do acc := acc ++ [f x]` loop (over a `List`, in `Id`) builds
-exactly `init ++ xs.map f`. Generalized over the accumulator so the induction
-goes through. -/
-theorem forIn_yield_append {α β : Type} (xs : List α) (init : List β) (f : α → β) :
-    (forIn xs init (fun x r => ForInStep.yield (r ++ [f x])) : Id (List β))
-      = init ++ xs.map f := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    show (forIn as (init ++ [f a]) (fun x r => ForInStep.yield (r ++ [f x])) : Id (List β)) = _
-    rw [ih]
-    simp [List.map_cons]
-
 theorem correct_reloaderArgv :
     ∀ (executable : String) (warnoptions : List String) (isCpython : Bool)
       (xoptions : List (String × XVal)) (argv : List String),
@@ -109,5 +83,7 @@
   simp only [Id.run, bind, pure]
   cases isCpython <;>
     simp only [forIn_yield_append, Bool.false_eq_true, if_true, if_false,
-      List.append_assoc, List.singleton_append, List.nil_append]
+      List.append_assoc, List.singleton_append, List.nil_append, List.map_reverse,
+      List.reverse_cons, List.reverse_nil] <;>
+    simp_all [List.append_assoc] <;> rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,36 +69,10 @@
 -- impl-start
 def implementation_reloaderArgv
     (executable : String) (warnoptions : List String) (isCpython : Bool)
-    (xoptions : List (String × XVal)) (argv : List String) : List String := Id.run do
-  -- Start from the executable and append one `-W` token per warning option.
-  let mut args := [executable]
-  for o in warnoptions do
-    args := args ++ [warnArg o]
-  -- On the CPython implementation, forward every active `-X` interpreter option.
-  if isCpython then
-    for kv in xoptions do
-      args := args ++ [xoptArg kv]
-  -- On the common relaunch path the original invocation arguments are appended
-  -- unchanged.
-  args := args ++ argv
-  return args
+    (xoptions : List (String × XVal)) (argv : List String) : List String := ([executable] ++ warnoptions.map warnArg) ++ (if isCpython then xoptions.reverse.map xoptArg else []) ++ argv
 -- impl-end
 
 -- proof-start
-/-- A `for x in xs do acc := acc ++ [f x]` loop (over a `List`, in `Id`) builds
-exactly `init ++ xs.map f`. Generalized over the accumulator so the induction
-goes through. -/
-theorem forIn_yield_append {α β : Type} (xs : List α) (init : List β) (f : α → β) :
-    (forIn xs init (fun x r => ForInStep.yield (r ++ [f x])) : Id (List β))
-      = init ++ xs.map f := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    show (forIn as (init ++ [f a]) (fun x r => ForInStep.yield (r ++ [f x])) : Id (List β)) = _
-    rw [ih]
-    simp [List.map_cons]
-
 theorem correct_reloaderArgv :
     ∀ (executable : String) (warnoptions : List String) (isCpython : Bool)
       (xoptions : List (String × XVal)) (argv : List String),
@@ -109,5 +83,7 @@
   simp only [Id.run, bind, pure]
   cases isCpython <;>
     simp only [forIn_yield_append, Bool.false_eq_true, if_true, if_false,
-      List.append_assoc, List.singleton_append, List.nil_append]
+      List.append_assoc, List.singleton_append, List.nil_append, List.map_reverse,
+      List.reverse_cons, List.reverse_nil] <;>
+    simp_all [List.append_assoc] <;> rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,36 +69,10 @@
 -- impl-start
 def implementation_reloaderArgv
     (executable : String) (warnoptions : List String) (isCpython : Bool)
-    (xoptions : List (String × XVal)) (argv : List String) : List String := Id.run do
-  -- Start from the executable and append one `-W` token per warning option.
-  let mut args := [executable]
-  for o in warnoptions do
-    args := args ++ [warnArg o]
-  -- On the CPython implementation, forward every active `-X` interpreter option.
-  if isCpython then
-    for kv in xoptions do
-      args := args ++ [xoptArg kv]
-  -- On the common relaunch path the original invocation arguments are appended
-  -- unchanged.
-  args := args ++ argv
-  return args
+    (xoptions : List (String × XVal)) (argv : List String) : List String := ([executable] ++ warnoptions.map warnArg) ++ argv ++ (if isCpython then xoptions.map xoptArg else [])
 -- impl-end
 
 -- proof-start
-/-- A `for x in xs do acc := acc ++ [f x]` loop (over a `List`, in `Id`) builds
-exactly `init ++ xs.map f`. Generalized over the accumulator so the induction
-goes through. -/
-theorem forIn_yield_append {α β : Type} (xs : List α) (init : List β) (f : α → β) :
-    (forIn xs init (fun x r => ForInStep.yield (r ++ [f x])) : Id (List β))
-      = init ++ xs.map f := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    show (forIn as (init ++ [f a]) (fun x r => ForInStep.yield (r ++ [f x])) : Id (List β)) = _
-    rw [ih]
-    simp [List.map_cons]
-
 theorem correct_reloaderArgv :
     ∀ (executable : String) (warnoptions : List String) (isCpython : Bool)
       (xoptions : List (String × XVal)) (argv : List String),
@@ -109,5 +83,7 @@
   simp only [Id.run, bind, pure]
   cases isCpython <;>
     simp only [forIn_yield_append, Bool.false_eq_true, if_true, if_false,
-      List.append_assoc, List.singleton_append, List.nil_append]
+      List.append_assoc, List.singleton_append, List.nil_append, List.map_reverse,
+      List.reverse_cons, List.reverse_nil] <;>
+    simp_all [List.append_assoc] <;> rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,36 +69,10 @@
 -- impl-start
 def implementation_reloaderArgv
     (executable : String) (warnoptions : List String) (isCpython : Bool)
-    (xoptions : List (String × XVal)) (argv : List String) : List String := Id.run do
-  -- Start from the executable and append one `-W` token per warning option.
-  let mut args := [executable]
-  for o in warnoptions do
-    args := args ++ [warnArg o]
-  -- On the CPython implementation, forward every active `-X` interpreter option.
-  if isCpython then
-    for kv in xoptions do
-      args := args ++ [xoptArg kv]
-  -- On the common relaunch path the original invocation arguments are appended
-  -- unchanged.
-  args := args ++ argv
-  return args
+    (xoptions : List (String × XVal)) (argv : List String) : List String := ([executable] ++ warnoptions.map warnArg) ++ (if isCpython then xoptions.map (fun kv => "-X" ++ kv.1) else []) ++ argv
 -- impl-end
 
 -- proof-start
-/-- A `for x in xs do acc := acc ++ [f x]` loop (over a `List`, in `Id`) builds
-exactly `init ++ xs.map f`. Generalized over the accumulator so the induction
-goes through. -/
-theorem forIn_yield_append {α β : Type} (xs : List α) (init : List β) (f : α → β) :
-    (forIn xs init (fun x r => ForInStep.yield (r ++ [f x])) : Id (List β))
-      = init ++ xs.map f := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    show (forIn as (init ++ [f a]) (fun x r => ForInStep.yield (r ++ [f x])) : Id (List β)) = _
-    rw [ih]
-    simp [List.map_cons]
-
 theorem correct_reloaderArgv :
     ∀ (executable : String) (warnoptions : List String) (isCpython : Bool)
       (xoptions : List (String × XVal)) (argv : List String),
@@ -109,5 +83,7 @@
   simp only [Id.run, bind, pure]
   cases isCpython <;>
     simp only [forIn_yield_append, Bool.false_eq_true, if_true, if_false,
-      List.append_assoc, List.singleton_append, List.nil_append]
+      List.append_assoc, List.singleton_append, List.nil_append, List.map_reverse,
+      List.reverse_cons, List.reverse_nil] <;>
+    simp_all [List.append_assoc] <;> rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,36 +69,10 @@
 -- impl-start
 def implementation_reloaderArgv
     (executable : String) (warnoptions : List String) (isCpython : Bool)
-    (xoptions : List (String × XVal)) (argv : List String) : List String := Id.run do
-  -- Start from the executable and append one `-W` token per warning option.
-  let mut args := [executable]
-  for o in warnoptions do
-    args := args ++ [warnArg o]
-  -- On the CPython implementation, forward every active `-X` interpreter option.
-  if isCpython then
-    for kv in xoptions do
-      args := args ++ [xoptArg kv]
-  -- On the common relaunch path the original invocation arguments are appended
-  -- unchanged.
-  args := args ++ argv
-  return args
+    (xoptions : List (String × XVal)) (argv : List String) : List String := (warnoptions.map warnArg) ++ (if isCpython then xoptions.map xoptArg else []) ++ argv
 -- impl-end
 
 -- proof-start
-/-- A `for x in xs do acc := acc ++ [f x]` loop (over a `List`, in `Id`) builds
-exactly `init ++ xs.map f`. Generalized over the accumulator so the induction
-goes through. -/
-theorem forIn_yield_append {α β : Type} (xs : List α) (init : List β) (f : α → β) :
-    (forIn xs init (fun x r => ForInStep.yield (r ++ [f x])) : Id (List β))
-      = init ++ xs.map f := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    show (forIn as (init ++ [f a]) (fun x r => ForInStep.yield (r ++ [f x])) : Id (List β)) = _
-    rw [ih]
-    simp [List.map_cons]
-
 theorem correct_reloaderArgv :
     ∀ (executable : String) (warnoptions : List String) (isCpython : Bool)
       (xoptions : List (String × XVal)) (argv : List String),
@@ -109,5 +83,7 @@
   simp only [Id.run, bind, pure]
   cases isCpython <;>
     simp only [forIn_yield_append, Bool.false_eq_true, if_true, if_false,
-      List.append_assoc, List.singleton_append, List.nil_append]
+      List.append_assoc, List.singleton_append, List.nil_append, List.map_reverse,
+      List.reverse_cons, List.reverse_nil] <;>
+    simp_all [List.append_assoc] <;> rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,36 +69,10 @@
 -- impl-start
 def implementation_reloaderArgv
     (executable : String) (warnoptions : List String) (isCpython : Bool)
-    (xoptions : List (String × XVal)) (argv : List String) : List String := Id.run do
-  -- Start from the executable and append one `-W` token per warning option.
-  let mut args := [executable]
-  for o in warnoptions do
-    args := args ++ [warnArg o]
-  -- On the CPython implementation, forward every active `-X` interpreter option.
-  if isCpython then
-    for kv in xoptions do
-      args := args ++ [xoptArg kv]
-  -- On the common relaunch path the original invocation arguments are appended
-  -- unchanged.
-  args := args ++ argv
-  return args
+    (xoptions : List (String × XVal)) (argv : List String) : List String := [executable] ++ (if isCpython then xoptions.map xoptArg else []) ++ argv
 -- impl-end
 
 -- proof-start
-/-- A `for x in xs do acc := acc ++ [f x]` loop (over a `List`, in `Id`) builds
-exactly `init ++ xs.map f`. Generalized over the accumulator so the induction
-goes through. -/
-theorem forIn_yield_append {α β : Type} (xs : List α) (init : List β) (f : α → β) :
-    (forIn xs init (fun x r => ForInStep.yield (r ++ [f x])) : Id (List β))
-      = init ++ xs.map f := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    show (forIn as (init ++ [f a]) (fun x r => ForInStep.yield (r ++ [f x])) : Id (List β)) = _
-    rw [ih]
-    simp [List.map_cons]
-
 theorem correct_reloaderArgv :
     ∀ (executable : String) (warnoptions : List String) (isCpython : Bool)
       (xoptions : List (String × XVal)) (argv : List String),
@@ -109,5 +83,7 @@
   simp only [Id.run, bind, pure]
   cases isCpython <;>
     simp only [forIn_yield_append, Bool.false_eq_true, if_true, if_false,
-      List.append_assoc, List.singleton_append, List.nil_append]
+      List.append_assoc, List.singleton_append, List.nil_append, List.map_reverse,
+      List.reverse_cons, List.reverse_nil] <;>
+    simp_all [List.append_assoc] <;> rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Building the argument vector used to relaunch the Python interpreter for the
development auto-reloader's child process.

When the auto-reloader spawns the reloaded server, it reconstructs the command
line the interpreter was originally invoked with. The vector starts with the
interpreter executable, followed by one `-W<opt>` entry for every active warning
option. On the CPython implementation it must additionally forward every active
interpreter `-X` option, so that settings such as `-Xutf8` survive across a
reload; each such option becomes either a bare `-X<key>` (for a flag-style option
whose value is the sentinel "on") or `-X<key>=<value>` (for a valued option).
Finally the original invocation arguments are appended unchanged.

The resulting vector is therefore, in order:

  * the executable,
  * the `-W` warning entries (one per warning option, in order),
  * on CPython only, the `-X` interpreter entries (one per option, in order),
  * the original invocation arguments.

On a non-CPython implementation the `-X` block is omitted entirely.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The way each warning
-- option and each interpreter option is rendered into a command-line token is
-- spelled out directly as the pure helpers below (string formatting only); there
-- is no opaque repo callee whose property the proof must assume.
-- axioms-end

-- pure-start
/-- The value carried by an interpreter `-X` option: either a flag-style option
whose value is the sentinel "on" (rendered as a bare `-X<key>`), or a valued
option carrying a string (rendered as `-X<key>=<value>`). -/
inductive XVal where
  | flag          -- value is the "on" sentinel
  | val (s : String)

/-- Render one warning option `o` as the command-line token `-W<o>`. -/
def warnArg (o : String) : String := "-W" ++ o

/-- Render one interpreter option `(key, v)` as a command-line token: a bare
`-X<key>` for a flag-style option, or `-X<key>=<value>` for a valued one. -/
def xoptArg (kv : String × XVal) : String :=
  match kv.2 with
  | XVal.flag   => "-X" ++ kv.1
  | XVal.val v  => "-X" ++ kv.1 ++ "=" ++ v
-- pure-end

-- post-conditions-start
/-- The relaunch argument vector is fully pinned to the inputs: it is the
executable, then the warning tokens (one per warning option, in order), then —
only on the CPython implementation — the interpreter `-X` tokens (one per option,
in order), then the original invocation arguments, all concatenated in that
order. Every output component is determined by an input; nothing is left free. -/
def problem_spec_reloaderArgv
    (executable : String) (warnoptions : List String) (isCpython : Bool)
    (xoptions : List (String × XVal)) (argv : List String)
    (result : List String) : Prop :=
  result =
    ([executable] ++ warnoptions.map warnArg)
      ++ (if isCpython then xoptions.map xoptArg else [])
      ++ argv
-- post-conditions-end

-- impl-start
def implementation_reloaderArgv
    (executable : String) (warnoptions : List String) (isCpython : Bool)
    (xoptions : List (String × XVal)) (argv : List String) : List String := Id.run do
  -- Start from the executable and append one `-W` token per warning option.
  let mut args := [executable]
  for o in warnoptions do
    args := args ++ [warnArg o]
  -- On the CPython implementation, forward every active `-X` interpreter option.
  if isCpython then
    for kv in xoptions do
      args := args ++ [xoptArg kv]
  -- On the common relaunch path the original invocation arguments are appended
  -- unchanged.
  args := args ++ argv
  return args
-- impl-end

-- proof-start
/-- A `for x in xs do acc := acc ++ [f x]` loop (over a `List`, in `Id`) builds
exactly `init ++ xs.map f`. Generalized over the accumulator so the induction
goes through. -/
theorem forIn_yield_append {α β : Type} (xs : List α) (init : List β) (f : α → β) :
    (forIn xs init (fun x r => ForInStep.yield (r ++ [f x])) : Id (List β))
      = init ++ xs.map f := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    show (forIn as (init ++ [f a]) (fun x r => ForInStep.yield (r ++ [f x])) : Id (List β)) = _
    rw [ih]
    simp [List.map_cons]

theorem correct_reloaderArgv :
    ∀ (executable : String) (warnoptions : List String) (isCpython : Bool)
      (xoptions : List (String × XVal)) (argv : List String),
      problem_spec_reloaderArgv executable warnoptions isCpython xoptions argv
        (implementation_reloaderArgv executable warnoptions isCpython xoptions argv) := by
  intro executable warnoptions isCpython xoptions argv
  unfold problem_spec_reloaderArgv implementation_reloaderArgv
  simp only [Id.run, bind, pure]
  cases isCpython <;>
    simp only [forIn_yield_append, Bool.false_eq_true, if_true, if_false,
      List.append_assoc, List.singleton_append, List.nil_append]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

env python. same_spec confirmed True (byte-identical spec view) for all 7 attacks via swebench_unified.markers.same_spec + get_backend('lean'). Both impl AND proof regions are elided by same_spec (lean has a 'proof' region), so attacks freely rewrite impl+proof and stay same-spec — the strongest adversarial surface. 

### COMMANDS/RESULTS (bash scripts/lean_verify.sh <f>):
- pos_control.lean exit=0 (gold verifies, no sorry).
- atk_1 (prepatch: Id.run loop, drops -X entirely) exit=1.
- atk_2 (ungated: -X forwarded even when isCpython=false) exit=1.
- atk_3 (xoptions.reverse.map — wrong order) exit=1.
- atk_4 (-X block appended AFTER argv) exit=1.
- atk_5 (boundary: renders every -X as bare -X<key>, dropping =value) exit=1.
- atk_6 (control-flow: omits [executable] head) exit=1.
- atk_7 (partial-domain: omits warn.map warnArg tokens) exit=1.
All 7 exit=1 (genuine proof failure; none sorry(3)/timeout(124)). Attacks run concurrently in two ≤4 background batches.

GENUINE-WRONGNESS PROOF (diagnostic, not submitted attacks): dis_1..dis_5 each prove ¬ problem_spec … (impl …) at a concrete witness, all exit=0 — confirming failures are behavioral divergence from the uniquely-pinned spec output, NOT weak-tactic artifacts.

A-LEG AUDIT (refinement.md): axioms region is EMPTY. All 6 legs are R or I (no A-consumed, no A-reference, no kind-3). No opaque callee and no `axiom <callee>_prop` in Solution.lean; token rendering is spelled deeply as pure helpers warnArg/xoptArg, rest is plain list construction. axiom_check.py is a legitimate G-AX skip stub. A-leg correspondence concern is vacuous (nothing axiomatized). Gold recorded #print axioms = [propext, Quot.sound] (clean, no sorryAx). R/I fidelity is G-CONF's job (conformance_check.py differential-tests vs the real patched get_child_arguments).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None: no same-spec wrong impl closes. The spec problem_spec_reloaderArgv is a TOTAL FUNCTIONAL EQUALITY pinning result to the unique closed form ([exe]++warn.map warnArg) ++ (if isCpython then xopts.map xoptArg else []) ++ argv. By funext any impl closing correct_ is extensionally equal to gold on ALL inputs, hence behaviorally identical and must resolve. There is no closing-but-unresolving refinement, so no faithful patch was materialized/resolve-run (nothing to run). Machine-checked disproofs prove each attacked impl diverges at a concrete witness: dis_1 (prepatch, drops -Xutf8) reduces to ¬ ['py','m']=['py','-Xutf8','m']; dis_2 (ungated -X, adds -Xk when isCpython=false); dis_3 (reversed xopt order); dis_4 (-X block after argv); dis_5 (valued -X drops =value) — all exit 0.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Building the argument vector used to relaunch the Python interpreter for the
development auto-reloader's child process.

When the auto-reloader spawns the reloaded server, it reconstructs the command
line the interpreter was originally invoked with. The vector starts with the
interpreter executable, followed by one `-W<opt>` entry for every active warning
option. On the CPython implementation it must additionally forward every active
interpreter `-X` option, so that settings such as `-Xutf8` survive across a
reload; each such option becomes either a bare `-X<key>` (for a flag-style option
whose value is the sentinel "on") or `-X<key>=<value>` (for a valued option).
Finally the original invocation arguments are appended unchanged.

The resulting vector is therefore, in order:

  * the executable,
  * the `-W` warning entries (one per warning option, in order),
  * on CPython only, the `-X` interpreter entries (one per option, in order),
  * the original invocation arguments.

On a non-CPython implementation the `-X` block is omitted entirely.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The way each warning
-- option and each interpreter option is rendered into a command-line token is
-- spelled out directly as the pure helpers below (string formatting only); there
-- is no opaque repo callee whose property the proof must assume.
-- axioms-end

-- pure-start
/-- The value carried by an interpreter `-X` option: either a flag-style option
whose value is the sentinel "on" (rendered as a bare `-X<key>`), or a valued
option carrying a string (rendered as `-X<key>=<value>`). -/
inductive XVal where
  | flag          -- value is the "on" sentinel
  | val (s : String)

/-- Render one warning option `o` as the command-line token `-W<o>`. -/
def warnArg (o : String) : String := "-W" ++ o

/-- Render one interpreter option `(key, v)` as a command-line token: a bare
`-X<key>` for a flag-style option, or `-X<key>=<value>` for a valued one. -/
def xoptArg (kv : String × XVal) : String :=
  match kv.2 with
  | XVal.flag   => "-X" ++ kv.1
  | XVal.val v  => "-X" ++ kv.1 ++ "=" ++ v
-- pure-end

-- post-conditions-start
/-- The relaunch argument vector is fully pinned to the inputs: it is the
executable, then the warning tokens (one per warning option, in order), then —
only on the CPython implementation — the interpreter `-X` tokens (one per option,
in order), then the original invocation arguments, all concatenated in that
order. Every output component is determined by an input; nothing is left free. -/
def problem_spec_reloaderArgv
    (executable : String) (warnoptions : List String) (isCpython : Bool)
    (xoptions : List (String × XVal)) (argv : List String)
    (result : List String) : Prop :=
  result =
    ([executable] ++ warnoptions.map warnArg)
      ++ (if isCpython then xoptions.map xoptArg else [])
      ++ argv
-- post-conditions-end

-- impl-start
def implementation_reloaderArgv
    (executable : String) (warnoptions : List String) (isCpython : Bool)
    (xoptions : List (String × XVal)) (argv : List String) : List String := Id.run do
  -- Start from the executable and append one `-W` token per warning option.
  let mut args := [executable]
  for o in warnoptions do
    args := args ++ [warnArg o]
  -- On the CPython implementation, forward every active `-X` interpreter option.
  if isCpython then
    for kv in xoptions do
      args := args ++ [xoptArg kv]
  -- On the common relaunch path the original invocation arguments are appended
  -- unchanged.
  args := args ++ argv
  return args
-- impl-end

-- proof-start
/-- A `for x in xs do acc := acc ++ [f x]` loop (over a `List`, in `Id`) builds
exactly `init ++ xs.map f`. Generalized over the accumulator so the induction
goes through. -/
theorem forIn_yield_append {α β : Type} (xs : List α) (init : List β) (f : α → β) :
    (forIn xs init (fun x r => ForInStep.yield (r ++ [f x])) : Id (List β))
      = init ++ xs.map f := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    show (forIn as (init ++ [f a]) (fun x r => ForInStep.yield (r ++ [f x])) : Id (List β)) = _
    rw [ih]
    simp [List.map_cons]

theorem correct_reloaderArgv :
    ∀ (executable : String) (warnoptions : List String) (isCpython : Bool)
      (xoptions : List (String × XVal)) (argv : List String),
      problem_spec_reloaderArgv executable warnoptions isCpython xoptions argv
        (implementation_reloaderArgv executable warnoptions isCpython xoptions argv) := by
  intro executable warnoptions isCpython xoptions argv
  unfold problem_spec_reloaderArgv implementation_reloaderArgv
  simp only [Id.run, bind, pure]
  cases isCpython <;>
    simp only [forIn_yield_append, Bool.false_eq_true, if_true, if_false,
      List.append_assoc, List.singleton_append, List.nil_append]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

env python. same_spec confirmed True (byte-identical spec view) for all 7 attacks via swebench_unified.markers.same_spec + get_backend('lean'). Both impl AND proof regions are elided by same_spec (lean has a 'proof' region), so attacks freely rewrite impl+proof and stay same-spec — the strongest adversarial surface. 

### COMMANDS/RESULTS (bash scripts/lean_verify.sh <f>):
- pos_control.lean exit=0 (gold verifies, no sorry).
- atk_1 (prepatch: Id.run loop, drops -X entirely) exit=1.
- atk_2 (ungated: -X forwarded even when isCpython=false) exit=1.
- atk_3 (xoptions.reverse.map — wrong order) exit=1.
- atk_4 (-X block appended AFTER argv) exit=1.
- atk_5 (boundary: renders every -X as bare -X<key>, dropping =value) exit=1.
- atk_6 (control-flow: omits [executable] head) exit=1.
- atk_7 (partial-domain: omits warn.map warnArg tokens) exit=1.
All 7 exit=1 (genuine proof failure; none sorry(3)/timeout(124)). Attacks run concurrently in two ≤4 background batches.

GENUINE-WRONGNESS PROOF (diagnostic, not submitted attacks): dis_1..dis_5 each prove ¬ problem_spec … (impl …) at a concrete witness, all exit=0 — confirming failures are behavioral divergence from the uniquely-pinned spec output, NOT weak-tactic artifacts.

A-LEG AUDIT (refinement.md): axioms region is EMPTY. All 6 legs are R or I (no A-consumed, no A-reference, no kind-3). No opaque callee and no `axiom <callee>_prop` in Solution.lean; token rendering is spelled deeply as pure helpers warnArg/xoptArg, rest is plain list construction. axiom_check.py is a legitimate G-AX skip stub. A-leg correspondence concern is vacuous (nothing axiomatized). Gold recorded #print axioms = [propext, Quot.sound] (clean, no sorryAx). R/I fidelity is G-CONF's job (conformance_check.py differential-tests vs the real patched get_child_arguments).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of problem_spec_reloaderArgv vs the real post-patch django.utils.autoreload.get_child_arguments (base_commit 4884a87e, worktree). (1) Spec region byte-identical between Solution.lean and Solution_prepatch.lean: swebench_unified.markers.same_spec(...,lean)=True; prepatch differs only in impl/proof (elided from spec view). (2) Solution.lean compiles (lean_verify.sh exit 0) and proof is genuine: #print axioms correct_reloaderArgv = [propext, Quot.sound], no sorryAx. (3) Spec formula ([executable] ++ warnoptions.map warnArg) ++ (if isCpython then xoptions.map xoptArg else []) ++ argv matches the real function's modeled else-path op-for-op: executable head, one -W<o> per warnoption in order, CPython-gated -X<key>/-X<key>=<value> per sys._xoptions item in order, then sys.argv. warnArg="-W"++o == '-W%s'%o; xoptArg flag/val == f'-X{key}' / f'-X{key}={value}'; XVal.flag<->value is True, XVal.val s<->str value. Empirical: ran conformance_check.py against patched over 100000 fuzzed inputs (executable, warnoptions, impl in {cpython,pypy,jython,graalpy}, xoptions flag/valued/empty, argv) -> 'G-CONF OK: 100000 inputs, 0 disagreements'. (5) Modeling boundary is narrowing not overstating: spec covers only the common relaunch path (__spec__ None + script exists); the -m and exe-fallback branches are unchanged by the fix and out of scope, so the spec is not too strong. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (0 hard failures); spec_view hash e2a7b285… matches frozen meta region_hashes.spec_view. Semantic review vs the PUBLIC problem_statement only (title 'Auto-reloader should pass -X options (for cpython implementation)', demo of -Xutf8 lost across reload, cites sys._xoptions docs): the entire behavioral content of the gold edit — forward interpreter -X options on CPython — is already public. Spec view discloses nothing beyond it: (a) no gold-diff line, diff marker, or patched path (django/utils/autoreload.py absent); (b) patched symbol get_child_arguments never embedded in any spec identifier (reloaderArgv/warnArg/xoptArg/XVal) nor named in any comment; (c) the -Xkey vs -Xkey=value distinction is derivable directly from the sys._xoptions doc URL cited in the problem statement, not a leak; (d) no narration terms (bug/fix/previously) — doc describes only target behavior; the -W/executable/argv framing is pre-existing surrounding code, not the edit. Faithful spec; disclosed content is coextensive with the public task.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
