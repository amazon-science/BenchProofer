# P2 adversarial audit — django__django-13297

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `base.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,15 +82,14 @@
 -- post-conditions-end
 
 -- impl-start
+def genericDeferredType : Nat := 0
+
 def implementation_wrapContextKwargs
     (urlKwargs : List (String × UrlValue)) : List (String × DeferredValue) := Id.run do
   let mut context := []
   for (key, value) in urlKwargs do
-    -- Bind this argument into its own deferred wrapper. The wrapper exposes the
-    -- underlying value's own type identity, resolves to that value, and carries
-    -- the notice keyed to this argument's name.
     let wrapper : DeferredValue := {
-      presentedType := value.pytype,
+      presentedType := genericDeferredType,
       resolved := value,
       noticeKey := key }
     context := context ++ [(key, wrapper)]
@@ -106,8 +105,8 @@
   have helper : ∀ (xs : List (String × UrlValue)) (acc : List (String × DeferredValue)),
       (forIn xs acc (fun x r => do
           pure PUnit.unit
-          pure (ForInStep.yield (r ++ [(x.1, { presentedType := x.2.pytype, resolved := x.2, noticeKey := x.1 })]))) : Id _)
-        = acc ++ xs.map (fun x => (x.1, ({ presentedType := x.2.pytype, resolved := x.2, noticeKey := x.1 } : DeferredValue))) := by
+          pure (ForInStep.yield (r ++ [(x.1, { presentedType := genericDeferredType, resolved := x.2, noticeKey := x.1 })]))) : Id _)
+        = acc ++ xs.map (fun x => (x.1, ({ presentedType := genericDeferredType, resolved := x.2, noticeKey := x.1 } : DeferredValue))) := by
     intro xs
     induction xs with
     | nil => intro acc; simp; rfl
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -86,11 +86,8 @@
     (urlKwargs : List (String × UrlValue)) : List (String × DeferredValue) := Id.run do
   let mut context := []
   for (key, value) in urlKwargs do
-    -- Bind this argument into its own deferred wrapper. The wrapper exposes the
-    -- underlying value's own type identity, resolves to that value, and carries
-    -- the notice keyed to this argument's name.
     let wrapper : DeferredValue := {
-      presentedType := value.pytype,
+      presentedType := value.data.length,
       resolved := value,
       noticeKey := key }
     context := context ++ [(key, wrapper)]
@@ -106,8 +103,8 @@
   have helper : ∀ (xs : List (String × UrlValue)) (acc : List (String × DeferredValue)),
       (forIn xs acc (fun x r => do
           pure PUnit.unit
-          pure (ForInStep.yield (r ++ [(x.1, { presentedType := x.2.pytype, resolved := x.2, noticeKey := x.1 })]))) : Id _)
-        = acc ++ xs.map (fun x => (x.1, ({ presentedType := x.2.pytype, resolved := x.2, noticeKey := x.1 } : DeferredValue))) := by
+          pure (ForInStep.yield (r ++ [(x.1, { presentedType := x.2.data.length, resolved := x.2, noticeKey := x.1 })]))) : Id _)
+        = acc ++ xs.map (fun x => (x.1, ({ presentedType := x.2.data.length, resolved := x.2, noticeKey := x.1 } : DeferredValue))) := by
     intro xs
     induction xs with
     | nil => intro acc; simp; rfl
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -86,14 +86,12 @@
     (urlKwargs : List (String × UrlValue)) : List (String × DeferredValue) := Id.run do
   let mut context := []
   for (key, value) in urlKwargs do
-    -- Bind this argument into its own deferred wrapper. The wrapper exposes the
-    -- underlying value's own type identity, resolves to that value, and carries
-    -- the notice keyed to this argument's name.
-    let wrapper : DeferredValue := {
-      presentedType := value.pytype,
-      resolved := value,
-      noticeKey := key }
-    context := context ++ [(key, wrapper)]
+    if value.data ≠ "" then
+      let wrapper : DeferredValue := {
+        presentedType := value.pytype,
+        resolved := value,
+        noticeKey := key }
+      context := context ++ [(key, wrapper)]
   return context
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -86,14 +86,11 @@
     (urlKwargs : List (String × UrlValue)) : List (String × DeferredValue) := Id.run do
   let mut context := []
   for (key, value) in urlKwargs do
-    -- Bind this argument into its own deferred wrapper. The wrapper exposes the
-    -- underlying value's own type identity, resolves to that value, and carries
-    -- the notice keyed to this argument's name.
     let wrapper : DeferredValue := {
       presentedType := value.pytype,
       resolved := value,
       noticeKey := key }
-    context := context ++ [(key, wrapper)]
+    context := [(key, wrapper)] ++ context
   return context
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -86,13 +86,10 @@
     (urlKwargs : List (String × UrlValue)) : List (String × DeferredValue) := Id.run do
   let mut context := []
   for (key, value) in urlKwargs do
-    -- Bind this argument into its own deferred wrapper. The wrapper exposes the
-    -- underlying value's own type identity, resolves to that value, and carries
-    -- the notice keyed to this argument's name.
     let wrapper : DeferredValue := {
       presentedType := value.pytype,
       resolved := value,
-      noticeKey := key }
+      noticeKey := key ++ "!" }
     context := context ++ [(key, wrapper)]
   return context
 -- impl-end
@@ -106,8 +103,8 @@
   have helper : ∀ (xs : List (String × UrlValue)) (acc : List (String × DeferredValue)),
       (forIn xs acc (fun x r => do
           pure PUnit.unit
-          pure (ForInStep.yield (r ++ [(x.1, { presentedType := x.2.pytype, resolved := x.2, noticeKey := x.1 })]))) : Id _)
-        = acc ++ xs.map (fun x => (x.1, ({ presentedType := x.2.pytype, resolved := x.2, noticeKey := x.1 } : DeferredValue))) := by
+          pure (ForInStep.yield (r ++ [(x.1, { presentedType := x.2.pytype, resolved := x.2, noticeKey := x.1 ++ "!" })]))) : Id _)
+        = acc ++ xs.map (fun x => (x.1, ({ presentedType := x.2.pytype, resolved := x.2, noticeKey := x.1 ++ "!" } : DeferredValue))) := by
     intro xs
     induction xs with
     | nil => intro acc; simp; rfl
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -86,12 +86,9 @@
     (urlKwargs : List (String × UrlValue)) : List (String × DeferredValue) := Id.run do
   let mut context := []
   for (key, value) in urlKwargs do
-    -- Bind this argument into its own deferred wrapper. The wrapper exposes the
-    -- underlying value's own type identity, resolves to that value, and carries
-    -- the notice keyed to this argument's name.
     let wrapper : DeferredValue := {
       presentedType := value.pytype,
-      resolved := value,
+      resolved := { pytype := value.pytype, data := "" },
       noticeKey := key }
     context := context ++ [(key, wrapper)]
   return context
@@ -106,8 +103,8 @@
   have helper : ∀ (xs : List (String × UrlValue)) (acc : List (String × DeferredValue)),
       (forIn xs acc (fun x r => do
           pure PUnit.unit
-          pure (ForInStep.yield (r ++ [(x.1, { presentedType := x.2.pytype, resolved := x.2, noticeKey := x.1 })]))) : Id _)
-        = acc ++ xs.map (fun x => (x.1, ({ presentedType := x.2.pytype, resolved := x.2, noticeKey := x.1 } : DeferredValue))) := by
+          pure (ForInStep.yield (r ++ [(x.1, { presentedType := x.2.pytype, resolved := { pytype := x.2.pytype, data := "" }, noticeKey := x.1 })]))) : Id _)
+        = acc ++ xs.map (fun x => (x.1, ({ presentedType := x.2.pytype, resolved := { pytype := x.2.pytype, data := "" }, noticeKey := x.1 } : DeferredValue))) := by
     intro xs
     induction xs with
     | nil => intro acc; simp; rfl
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -83,18 +83,9 @@
 
 -- impl-start
 def implementation_wrapContextKwargs
-    (urlKwargs : List (String × UrlValue)) : List (String × DeferredValue) := Id.run do
-  let mut context := []
-  for (key, value) in urlKwargs do
-    -- Bind this argument into its own deferred wrapper. The wrapper exposes the
-    -- underlying value's own type identity, resolves to that value, and carries
-    -- the notice keyed to this argument's name.
-    let wrapper : DeferredValue := {
-      presentedType := value.pytype,
-      resolved := value,
-      noticeKey := key }
-    context := context ++ [(key, wrapper)]
-  return context
+    (urlKwargs : List (String × UrlValue)) : List (String × DeferredValue) :=
+  urlKwargs.map (fun (key, value) =>
+    (key, { presentedType := value.pytype, resolved := value, noticeKey := key }))
 -- impl-end
 
 -- proof-start
@@ -103,24 +94,7 @@
       problem_spec_wrapContextKwargs urlKwargs
         (implementation_wrapContextKwargs urlKwargs) := by
   intro urlKwargs
-  have helper : ∀ (xs : List (String × UrlValue)) (acc : List (String × DeferredValue)),
-      (forIn xs acc (fun x r => do
-          pure PUnit.unit
-          pure (ForInStep.yield (r ++ [(x.1, { presentedType := x.2.pytype, resolved := x.2, noticeKey := x.1 })]))) : Id _)
-        = acc ++ xs.map (fun x => (x.1, ({ presentedType := x.2.pytype, resolved := x.2, noticeKey := x.1 } : DeferredValue))) := by
-    intro xs
-    induction xs with
-    | nil => intro acc; simp; rfl
-    | cons a as ih =>
-      intro acc
-      rw [List.forIn_cons]
-      simp only [bind] at ih ⊢
-      simp [ih, List.append_assoc]
-  unfold implementation_wrapContextKwargs
-  simp only [Id.run]
-  rw [helper]
-  simp only [List.nil_append]
-  unfold problem_spec_wrapContextKwargs
+  unfold implementation_wrapContextKwargs problem_spec_wrapContextKwargs
   induction urlKwargs with
   | nil => simp
   | cons a as ih =>
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `base.lean`

```lean
import Mathlib
-- imports-end

/-!
Deferring the URL keyword arguments that are handed to a template's context.

When a class-based template renderer receives the keyword arguments captured
from a URL route, those arguments are not placed into the template context
eagerly. Each one is wrapped in a DEFERRED value: the underlying value is only
produced the first time the wrapper is actually consumed, and producing it also
emits a one-time notice — keyed to that argument's name — announcing that
reaching these arguments through the context is being phased out.

A deferred wrapper must behave, to every downstream consumer, exactly like the
value it stands for. Concretely, for each captured argument the wrapper must:

  * resolve to precisely the original value (nothing added, nothing dropped);
  * carry the notice keyed to that same argument's name;
  * present the SAME type interface as the underlying value.

The last point is the one that matters in practice. A consumer that performs a
type-directed operation on the wrapper — passing it where a string, an integer,
etc. is expected — relies on the wrapper exposing the underlying value's type,
not some generic placeholder type. If the wrapper advertised only an opaque
deferred-object type, such a consumer would be handed something it cannot use.

The order of the captured arguments, and their names, are preserved exactly.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The act of
-- building a deferred wrapper is modeled structurally over the data each
-- captured argument carries (its name, its underlying value, and that value's
-- type identity); the resolved value and the keyed notice enter directly. Hence
-- no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- One captured URL keyword argument's underlying value, restricted to the two
observable facets a deferred wrapper must preserve:
* `pytype` — the type identity of the value (an injective tag over the distinct
  runtime types; only equality of type identities is observed);
* `data`   — the value's content. -/
structure UrlValue where
  pytype : Nat
  data : String
deriving DecidableEq, Repr

/-- A deferred wrapper standing in for one captured argument's value:
* `presentedType` — the type identity the wrapper exposes to consumers;
* `resolved`      — the value produced when the wrapper is consumed;
* `noticeKey`     — the argument name the emitted notice is keyed to. -/
structure DeferredValue where
  presentedType : Nat
  resolved : UrlValue
  noticeKey : String
deriving Repr

/-- The per-argument contract a deferred wrapper must meet, relating one input
`(name, value)` pair to its output `(name, wrapper)` pair: the name is carried
through, the wrapper resolves to exactly the original value, its notice is keyed
to that name, and — the decisive facet — the type it presents to consumers is
the underlying value's own type identity. -/
def wrapsValue (inp : String × UrlValue) (out : String × DeferredValue) : Prop :=
  out.1 = inp.1 ∧
  out.2.resolved = inp.2 ∧
  out.2.noticeKey = inp.1 ∧
  out.2.presentedType = inp.2.pytype
-- pure-end

-- post-conditions-start
/-- The collection of deferred wrappers is fully pinned to the captured
arguments: it has the same length, the same order, and the same names, and each
wrapper meets the per-argument contract (`wrapsValue`) against the argument in
the matching position. `List.Forall₂` simultaneously pins the length, the
positional pairing (hence the order), and the element-wise relation, so no
output entry is left free. -/
def problem_spec_wrapContextKwargs
    (urlKwargs : List (String × UrlValue))
    (result : List (String × DeferredValue)) : Prop :=
  List.Forall₂ wrapsValue urlKwargs result
-- post-conditions-end

-- impl-start
def implementation_wrapContextKwargs
    (urlKwargs : List (String × UrlValue)) : List (String × DeferredValue) := Id.run do
  let mut context := []
  for (key, value) in urlKwargs do
    -- Bind this argument into its own deferred wrapper. The wrapper exposes the
    -- underlying value's own type identity, resolves to that value, and carries
    -- the notice keyed to this argument's name.
    let wrapper : DeferredValue := {
      presentedType := value.pytype,
      resolved := value,
      noticeKey := key }
    context := context ++ [(key, wrapper)]
  return context
-- impl-end

-- proof-start
theorem correct_wrapContextKwargs :
    ∀ (urlKwargs : List (String × UrlValue)),
      problem_spec_wrapContextKwargs urlKwargs
        (implementation_wrapContextKwargs urlKwargs) := by
  intro urlKwargs
  have helper : ∀ (xs : List (String × UrlValue)) (acc : List (String × DeferredValue)),
      (forIn xs acc (fun x r => do
          pure PUnit.unit
          pure (ForInStep.yield (r ++ [(x.1, { presentedType := x.2.pytype, resolved := x.2, noticeKey := x.1 })]))) : Id _)
        = acc ++ xs.map (fun x => (x.1, ({ presentedType := x.2.pytype, resolved := x.2, noticeKey := x.1 } : DeferredValue))) := by
    intro xs
    induction xs with
    | nil => intro acc; simp; rfl
    | cons a as ih =>
      intro acc
      rw [List.forIn_cons]
      simp only [bind] at ih ⊢
      simp [ih, List.append_assoc]
  unfold implementation_wrapContextKwargs
  simp only [Id.run]
  rw [helper]
  simp only [List.nil_append]
  unfold problem_spec_wrapContextKwargs
  induction urlKwargs with
  | nil => simp
  | cons a as ih =>
    simp only [List.map_cons]
    apply List.Forall₂.cons _ ih
    refine ⟨rfl, rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit for django__django-13297 (lean). Spec: problem_spec_wrapContextKwargs = List.Forall2 wrapsValue, a TOTAL, fully-pinned postcondition that uniquely determines every output field (name, order, resolved value, noticeKey, presentedType) from every input element. Any behaviorally-divergent impl is therefore unprovable intrinsically, not just under my proof.

Same-spec: markers.same_spec True for all 7 attacks (spec regions byte-identical; only impl+proof edited).

Attacks (cmd: bash scripts/lean_verify.sh <f>):
- atk_1 PREPATCH BUG (presentedType:=genericDeferredType, fixed tag 0): exit 1 (error 128:27 Application type mismatch) — proof does NOT close. Reproduces the real prepatch bug (SimpleLazyObject generic type), matches G-DIFF.
- atk_2 ungrounded type source (presentedType:=value.data.length): exit 1 (error 126:27). Does not close.
- atk_3 partial domain (skip entries with empty data): exit 1 (rewrite failed 119:6). Does not close.
- atk_4 control-flow effect (reversed order via prepend): exit 1 (rewrite failed 118:6). Does not close.
- atk_5 boundary on names (noticeKey:=key++"!"): exit 1 (error 126:22). Does not close.
- atk_6 resolved value corrupted (data cleared to ""): exit 1 (error 126:17). Does not close.
- atk_7 ECHO / gold-equivalent (List.map form, presentedType=pytype, resolved=value, noticeKey=key): exit 0 VERIFIES. #print axioms correct_wrapContextKwargs = [propext] (CLEAN, no sorryAx).

Positive control base.lean (real Solution.lean impl): exit 0; #print axioms = [propext, Quot.sound] (CLEAN).

atk_7 is the ONLY wrong-impl that closes with clean axioms. It is behaviorally identical to gold, so its faithful refined patch IS the gold patch. Materialized as atk_7_patch.diff and run through the official harness: swebench_unified.harness.run_resolve('django__django-13297', patch, timeout=1800, retries=1) -> RESOLVED=True, COMPLETED=True, note='resolved'. Hence the echo does NOT break the spec (a resolving echo is not a weakness per current G-PANEL-1 policy). No verify-and-not-correct witness exists.

refinement.md audit: 7 legs. Ops #1,#2,#6 = R (dict<->ordered-list bijection); #4,#5,#7 = I; op #3 = A-reference (the changed proxy-builder lazy(f,type(v))(), deep-modeled as presentedType=value.pytype, NOT axiomatized). NO A-consumed leg (meta.json axioms=[], confirmed by clean proof axioms containing no callee-contract axiom). NO kind-3 legs. The single A-reference's correspondence to the real callee is validated by G-AX (axiom_check.py: post-patch lazy(access_value,type(value))() presents type(value) and resolves to value; pre-patch SimpleLazyObject presents the single generic type — genuinely distinguishable) -> meta.json G-AX status=pass, checked=8. Correspondence holds.

Verdict: SOUND. >=5 distinct wrong impls attacked; all behaviorally-wrong impls fail to verify; the only verifying-with-clean-axioms candidate is a gold-equivalent echo whose materialized faithful patch RESOLVES under run_resolve.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `base.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `base.lean`

```lean
import Mathlib
-- imports-end

/-!
Deferring the URL keyword arguments that are handed to a template's context.

When a class-based template renderer receives the keyword arguments captured
from a URL route, those arguments are not placed into the template context
eagerly. Each one is wrapped in a DEFERRED value: the underlying value is only
produced the first time the wrapper is actually consumed, and producing it also
emits a one-time notice — keyed to that argument's name — announcing that
reaching these arguments through the context is being phased out.

A deferred wrapper must behave, to every downstream consumer, exactly like the
value it stands for. Concretely, for each captured argument the wrapper must:

  * resolve to precisely the original value (nothing added, nothing dropped);
  * carry the notice keyed to that same argument's name;
  * present the SAME type interface as the underlying value.

The last point is the one that matters in practice. A consumer that performs a
type-directed operation on the wrapper — passing it where a string, an integer,
etc. is expected — relies on the wrapper exposing the underlying value's type,
not some generic placeholder type. If the wrapper advertised only an opaque
deferred-object type, such a consumer would be handed something it cannot use.

The order of the captured arguments, and their names, are preserved exactly.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The act of
-- building a deferred wrapper is modeled structurally over the data each
-- captured argument carries (its name, its underlying value, and that value's
-- type identity); the resolved value and the keyed notice enter directly. Hence
-- no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- One captured URL keyword argument's underlying value, restricted to the two
observable facets a deferred wrapper must preserve:
* `pytype` — the type identity of the value (an injective tag over the distinct
  runtime types; only equality of type identities is observed);
* `data`   — the value's content. -/
structure UrlValue where
  pytype : Nat
  data : String
deriving DecidableEq, Repr

/-- A deferred wrapper standing in for one captured argument's value:
* `presentedType` — the type identity the wrapper exposes to consumers;
* `resolved`      — the value produced when the wrapper is consumed;
* `noticeKey`     — the argument name the emitted notice is keyed to. -/
structure DeferredValue where
  presentedType : Nat
  resolved : UrlValue
  noticeKey : String
deriving Repr

/-- The per-argument contract a deferred wrapper must meet, relating one input
`(name, value)` pair to its output `(name, wrapper)` pair: the name is carried
through, the wrapper resolves to exactly the original value, its notice is keyed
to that name, and — the decisive facet — the type it presents to consumers is
the underlying value's own type identity. -/
def wrapsValue (inp : String × UrlValue) (out : String × DeferredValue) : Prop :=
  out.1 = inp.1 ∧
  out.2.resolved = inp.2 ∧
  out.2.noticeKey = inp.1 ∧
  out.2.presentedType = inp.2.pytype
-- pure-end

-- post-conditions-start
/-- The collection of deferred wrappers is fully pinned to the captured
arguments: it has the same length, the same order, and the same names, and each
wrapper meets the per-argument contract (`wrapsValue`) against the argument in
the matching position. `List.Forall₂` simultaneously pins the length, the
positional pairing (hence the order), and the element-wise relation, so no
output entry is left free. -/
def problem_spec_wrapContextKwargs
    (urlKwargs : List (String × UrlValue))
    (result : List (String × DeferredValue)) : Prop :=
  List.Forall₂ wrapsValue urlKwargs result
-- post-conditions-end

-- impl-start
def implementation_wrapContextKwargs
    (urlKwargs : List (String × UrlValue)) : List (String × DeferredValue) := Id.run do
  let mut context := []
  for (key, value) in urlKwargs do
    -- Bind this argument into its own deferred wrapper. The wrapper exposes the
    -- underlying value's own type identity, resolves to that value, and carries
    -- the notice keyed to this argument's name.
    let wrapper : DeferredValue := {
      presentedType := value.pytype,
      resolved := value,
      noticeKey := key }
    context := context ++ [(key, wrapper)]
  return context
-- impl-end

-- proof-start
theorem correct_wrapContextKwargs :
    ∀ (urlKwargs : List (String × UrlValue)),
      problem_spec_wrapContextKwargs urlKwargs
        (implementation_wrapContextKwargs urlKwargs) := by
  intro urlKwargs
  have helper : ∀ (xs : List (String × UrlValue)) (acc : List (String × DeferredValue)),
      (forIn xs acc (fun x r => do
          pure PUnit.unit
          pure (ForInStep.yield (r ++ [(x.1, { presentedType := x.2.pytype, resolved := x.2, noticeKey := x.1 })]))) : Id _)
        = acc ++ xs.map (fun x => (x.1, ({ presentedType := x.2.pytype, resolved := x.2, noticeKey := x.1 } : DeferredValue))) := by
    intro xs
    induction xs with
    | nil => intro acc; simp; rfl
    | cons a as ih =>
      intro acc
      rw [List.forIn_cons]
      simp only [bind] at ih ⊢
      simp [ih, List.append_assoc]
  unfold implementation_wrapContextKwargs
  simp only [Id.run]
  rw [helper]
  simp only [List.nil_append]
  unfold problem_spec_wrapContextKwargs
  induction urlKwargs with
  | nil => simp
  | cons a as ih =>
    simp only [List.map_cons]
    apply List.Forall₂.cons _ ih
    refine ⟨rfl, rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit for django__django-13297 (lean). Spec: problem_spec_wrapContextKwargs = List.Forall2 wrapsValue, a TOTAL, fully-pinned postcondition that uniquely determines every output field (name, order, resolved value, noticeKey, presentedType) from every input element. Any behaviorally-divergent impl is therefore unprovable intrinsically, not just under my proof.

Same-spec: markers.same_spec True for all 7 attacks (spec regions byte-identical; only impl+proof edited).

Attacks (cmd: bash scripts/lean_verify.sh <f>):
- atk_1 PREPATCH BUG (presentedType:=genericDeferredType, fixed tag 0): exit 1 (error 128:27 Application type mismatch) — proof does NOT close. Reproduces the real prepatch bug (SimpleLazyObject generic type), matches G-DIFF.
- atk_2 ungrounded type source (presentedType:=value.data.length): exit 1 (error 126:27). Does not close.
- atk_3 partial domain (skip entries with empty data): exit 1 (rewrite failed 119:6). Does not close.
- atk_4 control-flow effect (reversed order via prepend): exit 1 (rewrite failed 118:6). Does not close.
- atk_5 boundary on names (noticeKey:=key++"!"): exit 1 (error 126:22). Does not close.
- atk_6 resolved value corrupted (data cleared to ""): exit 1 (error 126:17). Does not close.
- atk_7 ECHO / gold-equivalent (List.map form, presentedType=pytype, resolved=value, noticeKey=key): exit 0 VERIFIES. #print axioms correct_wrapContextKwargs = [propext] (CLEAN, no sorryAx).

Positive control base.lean (real Solution.lean impl): exit 0; #print axioms = [propext, Quot.sound] (CLEAN).

atk_7 is the ONLY wrong-impl that closes with clean axioms. It is behaviorally identical to gold, so its faithful refined patch IS the gold patch. Materialized as atk_7_patch.diff and run through the official harness: swebench_unified.harness.run_resolve('django__django-13297', patch, timeout=1800, retries=1) -> RESOLVED=True, COMPLETED=True, note='resolved'. Hence the echo does NOT break the spec (a resolving echo is not a weakness per current G-PANEL-1 policy). No verify-and-not-correct witness exists.

refinement.md audit: 7 legs. Ops #1,#2,#6 = R (dict<->ordered-list bijection); #4,#5,#7 = I; op #3 = A-reference (the changed proxy-builder lazy(f,type(v))(), deep-modeled as presentedType=value.pytype, NOT axiomatized). NO A-consumed leg (meta.json axioms=[], confirmed by clean proof axioms containing no callee-contract axiom). NO kind-3 legs. The single A-reference's correspondence to the real callee is validated by G-AX (axiom_check.py: post-patch lazy(access_value,type(value))() presents type(value) and resolves to value; pre-patch SimpleLazyObject presents the single generic type — genuinely distinguishable) -> meta.json G-AX status=pass, checked=8. Correspondence holds.

Verdict: SOUND. >=5 distinct wrong impls attacked; all behaviorally-wrong impls fail to verify; the only verifying-with-clean-axioms candidate is a gold-equivalent echo whose materialized faithful patch RESOLVES under run_resolve.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit of django__django-13297 lean bundle.

Mechanical preflight (reproduced): scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry). #print axioms correct_wrapContextKwargs = [propext, Quot.sound] (CLEAN, no sorryAx -- proof is real). same_spec(Solution, Solution_prepatch, lean backend) = True (spec region byte-identical between twins). conformance_check.py drives 120009 fuzzed inputs, disagreements=0.

Gold patch (django/views/generic/base.py:_wrap_url_kwargs_with_deprecation_warning): replaces `@SimpleLazyObject` + `context_kwargs[key]=access_value` with `context_kwargs[key]=lazy(access_value, type(value))()`. Modeled function implementation_wrapContextKwargs maps each captured (key,value) to a DeferredValue {presentedType:=value.pytype, resolved:=value, noticeKey:=key}, appended in iteration order; spec problem_spec_wrapContextKwargs = List.Forall2 wrapsValue urlKwargs result, pinning length+order+per-element (key preserved, resolved=value, noticeKey=key, presentedType=value.pytype).

Per-facet check vs the real post-patch callee (reachable domain = real url_kwargs dict -> list, unique keys, insertion order):
- resolved=value: access_value() returns value verbatim -> FAITHFUL.
- noticeKey=key: notice '...Reference %s...' % key keyed to this kwarg name -> FAITHFUL.
- presentedType=value.pytype: lazy(f, type(value))() prepares its proxy from resultclasses=(type(value),), presenting the value's own runtime type (the decisive fix; pre-patch SimpleLazyObject exposes the generic type). G-AX validated over 8 checks -> FAITHFUL.
- order/length: dict .items() insertion order <-> List order via Forall2 -> FAITHFUL.

Abstraction soundness: pytype:Nat is an injective tag only ever compared for = / != (never structurally inspected); data:String is carried through, never inspected. The only place the modeled List domain is broader than reality is Lists with duplicate keys, which is unreachable (a real Python dict cannot have duplicate keys) and even there the impl faithfully mirrors the element-wise loop, so no divergence arises.

No diverging input exists on the reachable domain; the spec pins exactly the patched behavior without over-strengthening. G-PANEL-2 = FAITHFUL (pass).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-view authenticity confirmed: rendered _lean_spec_view sha256 = a85d2b1b60cd94c56656853df39bb059344f4c231dd74e4f269c37a131ba6796, byte-identical to meta.json region_hashes.spec_view; impl+proof regions collapse to placeholders. same_spec(post, prepatch)=True — spec region byte-identical across the pre/post pair. Comparison basis = public problem_statement (NOT hints_text).

Gold edit: swap per-kwarg wrapper from @SimpleLazyObject (generic deferred type) to lazy(access_value, type(value))() (proxy prepared from type(value), presenting the underlying value's own type). The public problem_statement ALREADY discloses the essence: the wrapper is a SimpleLazyObject, it crashes when filtering ('Error binding parameter 0 - probably unsupported type'), and explicit str(...) conversion fixes it — i.e. the presented TYPE is the defect. Requirement 'wrapper must present the underlying value's real type, not a generic deferred type' is directly derivable from the public statement.

Spec view leaks nothing beyond that: token screen confirms it names NONE of the gold-edit symbols (lazy, resultclasses, type(value), access_value, _wrap_url_kwargs_with_deprecation_warning all absent); modeled name wrapContextKwargs is neutral and shares no substring with patched defs; phrasing is abstract ('generic placeholder type' / 'opaque deferred-object type') and does not even name SimpleLazyObject (which problem_statement itself uses verbatim). It encodes the correct-behavior contract (presentedType = value.pytype via wrapsValue), which is exactly what a spec should encode and is inferable from the public crash/str()-fix report. The deprecation-notice/noticeKey facet is unchanged between pre/post patch (warning exists both sides), so it is orthogonal context that cannot leak the edit. No spec-view line names or diagnoses the specific gold mechanism. Concurs with recorded G-PANEL-3 (NO-LEAKAGE) and G-LEAK pass.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
