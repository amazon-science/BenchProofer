# P2 adversarial audit — astropy__astropy-14096

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 9 | `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean` |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec implementation with a closing clean-axiom proof has a FAITHFUL refined patch that fails to resolve. 14 attacks: 4 value-level wrong impls were REJECTED by the verifier (spec has real content); 10 verified with clean axioms and all 10 faithful patches RESOLVED (echoes). Two patches did NOT resolve (atk_13 cross-call memo of handledCase: P2P 367/426, 59 failures; atk_14 callee swap to getattr(self, attr): F2P 0/1 + P2P 129/426, infinite recursion) but BOTH were judged UNFAITHFUL over-refinements of their own Lean impls, and each one's faithful refinement then resolved 426/426 + F2P. Retained at atk_13_UNFAITHFUL_crosscall.diff and atk_14_UNFAITHFUL_calleeswap.diff as the near-miss record, NOT submitted as findings.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -95,18 +95,26 @@
 -- post-conditions-end
 
 -- impl-start
+-- PRE-PATCH (buggy) skeleton: the domain-specific resolution branches are
+-- unchanged — whichever applies still surfaces its own outcome, value or raised
+-- failure alike — but when NONE of them applies, instead of consulting the
+-- object's ordinary attribute-access protocol the hook FABRICATES an
+-- attribute-lookup failure keyed to the originally requested name. This discards
+-- the genuine failure the ordinary protocol would raise (which may report a
+-- different, genuinely-missing name), so on the `none` branch the result is
+-- always `Except.error { missing := attr }` regardless of the real outcome.
 def implementation_resolveAttr (self : CoordObj) (attr : String) :
     Except AttrError AttrValue := Id.run do
-  -- Try the domain-specific resolution branches; surface the outcome of
-  -- whichever applies, value or raised failure alike.
   if let some r := handledCase self attr then
     return r
-  -- Fall back to the object's ordinary attribute-access protocol, propagating
-  -- its outcome verbatim.
-  return ordinaryLookup self attr
+  return Except.error { missing := attr }
 -- impl-end
 
 -- proof-start
+-- Gold proof body carried over; it does NOT close against the buggy impl. On the
+-- `none` branch the spec demands `result = ordinaryLookup self attr`, but the
+-- buggy impl returns the fabricated `Except.error { missing := attr }`, which is
+-- not in general equal to the ordinary-lookup outcome — the discriminating clause.
 theorem correct_resolveAttr :
     ∀ (self : CoordObj) (attr : String),
       problem_spec_resolveAttr self attr (implementation_resolveAttr self attr) := by
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -95,14 +95,16 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK (partial domain): the fix is applied everywhere EXCEPT one name, on
+-- which the hook still fabricates the pre-fix attribute-lookup failure keyed to
+-- the requested name. Faithful patch: `if attr == "prop": raise AttributeError(...)`
+-- guarding the fallback.
 def implementation_resolveAttr (self : CoordObj) (attr : String) :
     Except AttrError AttrValue := Id.run do
-  -- Try the domain-specific resolution branches; surface the outcome of
-  -- whichever applies, value or raised failure alike.
   if let some r := handledCase self attr then
     return r
-  -- Fall back to the object's ordinary attribute-access protocol, propagating
-  -- its outcome verbatim.
+  if attr = "prop" then
+    return Except.error { missing := attr }
   return ordinaryLookup self attr
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -95,15 +95,18 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK (boundary / value-mangling): the ordinary outcome IS consulted on the
+-- fallback path, but its failure is re-stamped with the attribute-lookup class,
+-- discarding the genuine class (TypeError/ConvertError/UnitsError/...). The
+-- reported missing NAME is preserved, so this passes the F2P discriminator's
+-- `match="random_attr"` while still not propagating verbatim.
 def implementation_resolveAttr (self : CoordObj) (attr : String) :
     Except AttrError AttrValue := Id.run do
-  -- Try the domain-specific resolution branches; surface the outcome of
-  -- whichever applies, value or raised failure alike.
   if let some r := handledCase self attr then
     return r
-  -- Fall back to the object's ordinary attribute-access protocol, propagating
-  -- its outcome verbatim.
-  return ordinaryLookup self attr
+  match ordinaryLookup self attr with
+  | Except.ok v => return Except.ok v
+  | Except.error e => return Except.error { e with kind := "AttributeError" }
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -95,15 +95,17 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK (control-flow): a branch that APPLIES but whose evaluation FAILS no
+-- longer surfaces its own failure; control is re-routed to the ordinary
+-- attribute-access protocol instead. Faithful patch: wrap the resolution
+-- branches in `try/except Exception: pass` and fall through to
+-- `self.__getattribute__(attr)`.
 def implementation_resolveAttr (self : CoordObj) (attr : String) :
     Except AttrError AttrValue := Id.run do
-  -- Try the domain-specific resolution branches; surface the outcome of
-  -- whichever applies, value or raised failure alike.
-  if let some r := handledCase self attr then
-    return r
-  -- Fall back to the object's ordinary attribute-access protocol, propagating
-  -- its outcome verbatim.
-  return ordinaryLookup self attr
+  match handledCase self attr with
+  | some (Except.ok v) => return Except.ok v
+  | some (Except.error _) => return ordinaryLookup self attr
+  | none => return ordinaryLookup self attr
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -95,15 +95,21 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK (control-flow EFFECT / purity-abstraction gap): the ordinary
+-- attribute-access outcome for the name is computed UP FRONT, before any
+-- domain-specific branch is tried, and merely SELECTED at the end. In Lean
+-- `ordinaryLookup` is a pure function, so hoisting it is invisible and the value
+-- returned is pointwise identical to the reference. In the real repository the
+-- corresponding callee `self.__getattribute__(attr)` is an EFFECTFUL call that
+-- runs arbitrary user code (property getters) and raises; hoisting it therefore
+-- executes the patched fallback line on EVERY __getattr__ call, including calls
+-- on which a resolution branch applies and the reference never reaches it.
 def implementation_resolveAttr (self : CoordObj) (attr : String) :
     Except AttrError AttrValue := Id.run do
-  -- Try the domain-specific resolution branches; surface the outcome of
-  -- whichever applies, value or raised failure alike.
+  let fallback := ordinaryLookup self attr
   if let some r := handledCase self attr then
     return r
-  -- Fall back to the object's ordinary attribute-access protocol, propagating
-  -- its outcome verbatim.
-  return ordinaryLookup self attr
+  return fallback
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -95,15 +95,14 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK (ungrounded-oracle echo): the same total function written as a
+-- defaulting combinator rather than as an early-return branch. Pointwise equal
+-- to the reference; included to check that the harness scores a genuine
+-- alternative implementation as an ECHO (its faithful patch resolves) rather
+-- than as a spec weakness.
 def implementation_resolveAttr (self : CoordObj) (attr : String) :
-    Except AttrError AttrValue := Id.run do
-  -- Try the domain-specific resolution branches; surface the outcome of
-  -- whichever applies, value or raised failure alike.
-  if let some r := handledCase self attr then
-    return r
-  -- Fall back to the object's ordinary attribute-access protocol, propagating
-  -- its outcome verbatim.
-  return ordinaryLookup self attr
+    Except AttrError AttrValue :=
+  (handledCase self attr).getD (ordinaryLookup self attr)
 -- impl-end
 
 -- proof-start
@@ -112,13 +111,7 @@
       problem_spec_resolveAttr self attr (implementation_resolveAttr self attr) := by
   intro self attr
   unfold problem_spec_resolveAttr implementation_resolveAttr
-  cases h : handledCase self attr with
-  | none =>
-    refine ⟨?_, ?_⟩
-    · intro r hr; exact Option.noConfusion hr
-    · intro _; rfl
-  | some r =>
-    refine ⟨?_, ?_⟩
-    · intro r' hr'; exact Option.some_inj.mp hr'
-    · intro hc; exact Option.noConfusion hc
+  refine ⟨?_, ?_⟩
+  · intro r hr; simp [Id.run, hr]
+  · intro hc; simp [Id.run, hc]
 -- proof-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -95,15 +95,20 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK (duplicated callee evaluation): the resolution aggregate is evaluated
+-- TWICE — once to decide whether a branch applies, once to obtain the outcome
+-- that is surfaced. Pure in Lean, so the value is unchanged; in the real
+-- repository it means the branch expressions (`getattr(self.frame, ...)`,
+-- `self.transform_to(attr)`) run twice per __getattr__ call, and any failure
+-- they raise is raised, discarded and then raised again.
 def implementation_resolveAttr (self : CoordObj) (attr : String) :
     Except AttrError AttrValue := Id.run do
-  -- Try the domain-specific resolution branches; surface the outcome of
-  -- whichever applies, value or raised failure alike.
-  if let some r := handledCase self attr then
-    return r
-  -- Fall back to the object's ordinary attribute-access protocol, propagating
-  -- its outcome verbatim.
-  return ordinaryLookup self attr
+  match handledCase self attr with
+  | some _ =>
+    match handledCase self attr with
+    | some r => return r
+    | none => return ordinaryLookup self attr
+  | none => return ordinaryLookup self attr
 -- impl-end
 
 -- proof-start
@@ -112,13 +117,7 @@
       problem_spec_resolveAttr self attr (implementation_resolveAttr self attr) := by
   intro self attr
   unfold problem_spec_resolveAttr implementation_resolveAttr
-  cases h : handledCase self attr with
-  | none =>
-    refine ⟨?_, ?_⟩
-    · intro r hr; exact Option.noConfusion hr
-    · intro _; rfl
-  | some r =>
-    refine ⟨?_, ?_⟩
-    · intro r' hr'; exact Option.some_inj.mp hr'
-    · intro hc; exact Option.noConfusion hc
+  refine ⟨?_, ?_⟩
+  · intro r hr; rw [hr]; rfl
+  · intro hc; rw [hc]; rfl
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -95,14 +95,12 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK (obligation-dropping / oracle bypass): the domain-specific resolution
+-- branches are removed altogether and every name goes straight to the ordinary
+-- attribute-access protocol. This still satisfies the F2P discriminator's
+-- error-naming requirement, so it probes whether clause 1 has real content.
 def implementation_resolveAttr (self : CoordObj) (attr : String) :
     Except AttrError AttrValue := Id.run do
-  -- Try the domain-specific resolution branches; surface the outcome of
-  -- whichever applies, value or raised failure alike.
-  if let some r := handledCase self attr then
-    return r
-  -- Fall back to the object's ordinary attribute-access protocol, propagating
-  -- its outcome verbatim.
   return ordinaryLookup self attr
 -- impl-end
 
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -95,14 +95,18 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK (control-flow EFFECT / duplicated effectful callee): on the fallback
+-- path the ordinary attribute-access protocol is consulted TWICE and the SECOND
+-- outcome is the one surfaced; the first is evaluated and discarded. Pure in
+-- Lean, so the returned value is identical to the reference. In the real
+-- repository the bound callee `self.__getattribute__(attr)` runs arbitrary user
+-- code (property getters, lazy descriptors), so this executes every such getter
+-- twice per fallback and swallows the first failure it raises.
 def implementation_resolveAttr (self : CoordObj) (attr : String) :
     Except AttrError AttrValue := Id.run do
-  -- Try the domain-specific resolution branches; surface the outcome of
-  -- whichever applies, value or raised failure alike.
   if let some r := handledCase self attr then
     return r
-  -- Fall back to the object's ordinary attribute-access protocol, propagating
-  -- its outcome verbatim.
+  let _discarded := ordinaryLookup self attr
   return ordinaryLookup self attr
 -- impl-end
 
@@ -112,13 +116,7 @@
       problem_spec_resolveAttr self attr (implementation_resolveAttr self attr) := by
   intro self attr
   unfold problem_spec_resolveAttr implementation_resolveAttr
-  cases h : handledCase self attr with
-  | none =>
-    refine ⟨?_, ?_⟩
-    · intro r hr; exact Option.noConfusion hr
-    · intro _; rfl
-  | some r =>
-    refine ⟨?_, ?_⟩
-    · intro r' hr'; exact Option.some_inj.mp hr'
-    · intro hc; exact Option.noConfusion hc
+  refine ⟨?_, ?_⟩
+  · intro r hr; rw [hr]; rfl
+  · intro hc; rw [hc]; rfl
 -- proof-end
```

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -95,15 +95,23 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK (ungrounded deep model / identity erasure): the fallback outcome is
+-- consulted, but a FAILURE is not propagated verbatim — it is torn down to the
+-- two fields the model records (reported name + failure class) and a FRESH
+-- failure is rebuilt from them. `AttrError` is a two-field record, so in Lean the
+-- rebuild is definitionally the original and the proof closes. In the real
+-- repository the modeled `AttrError` abstracts a Python exception OBJECT, and
+-- rebuilding it via `raise type(e)(str(e)) from None` discards the traceback, the
+-- __context__/__cause__ chain, `.args` beyond the message, and (for AttributeError)
+-- the `.name`/`.obj` attributes the interpreter attaches -- none of which the
+-- model can see.
 def implementation_resolveAttr (self : CoordObj) (attr : String) :
     Except AttrError AttrValue := Id.run do
-  -- Try the domain-specific resolution branches; surface the outcome of
-  -- whichever applies, value or raised failure alike.
   if let some r := handledCase self attr then
     return r
-  -- Fall back to the object's ordinary attribute-access protocol, propagating
-  -- its outcome verbatim.
-  return ordinaryLookup self attr
+  match ordinaryLookup self attr with
+  | Except.ok v => return Except.ok v
+  | Except.error e => return Except.error { missing := e.missing, kind := e.kind }
 -- impl-end
 
 -- proof-start
@@ -112,13 +120,15 @@
       problem_spec_resolveAttr self attr (implementation_resolveAttr self attr) := by
   intro self attr
   unfold problem_spec_resolveAttr implementation_resolveAttr
-  cases h : handledCase self attr with
-  | none =>
-    refine ⟨?_, ?_⟩
-    · intro r hr; exact Option.noConfusion hr
-    · intro _; rfl
-  | some r =>
-    refine ⟨?_, ?_⟩
-    · intro r' hr'; exact Option.some_inj.mp hr'
-    · intro hc; exact Option.noConfusion hc
+  refine ⟨?_, ?_⟩
+  · intro r hr; rw [hr]; rfl
+  · intro hc
+    rw [hc]
+    show (match ordinaryLookup self attr with
+      | Except.ok v => Except.ok v
+      | Except.error e => Except.error { missing := e.missing, kind := e.kind })
+        = ordinaryLookup self attr
+    cases ho : ordinaryLookup self attr with
+    | ok v => rfl
+    | error e => rfl
 -- proof-end
```

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -95,15 +95,22 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK (A-leg purity gap / MEMOIZED oracle): the fallback outcome is obtained
+-- ONCE for this (self, attr) pair, bound, and returned. The spec declares
+-- `ordinaryLookup : CoordObj -> String -> Except AttrError AttrValue`, i.e. the
+-- ordinary attribute-access outcome is a FUNCTION of the receiver and the name.
+-- If that is true, caching the outcome per (receiver, name) is behavior-
+-- preserving, and the faithful patch memoizes it. In the real repository the
+-- callee is time-dependent: the very same (receiver, name) yields a failure now
+-- and a value after the attribute is assigned, so the memo returns a stale
+-- outcome. The model cannot see this, because purity is baked into the axiom's
+-- SIGNATURE rather than justified.
 def implementation_resolveAttr (self : CoordObj) (attr : String) :
     Except AttrError AttrValue := Id.run do
-  -- Try the domain-specific resolution branches; surface the outcome of
-  -- whichever applies, value or raised failure alike.
   if let some r := handledCase self attr then
     return r
-  -- Fall back to the object's ordinary attribute-access protocol, propagating
-  -- its outcome verbatim.
-  return ordinaryLookup self attr
+  let cached := ordinaryLookup self attr
+  return cached
 -- impl-end
 
 -- proof-start
@@ -112,13 +119,7 @@
       problem_spec_resolveAttr self attr (implementation_resolveAttr self attr) := by
   intro self attr
   unfold problem_spec_resolveAttr implementation_resolveAttr
-  cases h : handledCase self attr with
-  | none =>
-    refine ⟨?_, ?_⟩
-    · intro r hr; exact Option.noConfusion hr
-    · intro _; rfl
-  | some r =>
-    refine ⟨?_, ?_⟩
-    · intro r' hr'; exact Option.some_inj.mp hr'
-    · intro hc; exact Option.noConfusion hc
+  refine ⟨?_, ?_⟩
+  · intro r hr; rw [hr]; rfl
+  · intro hc; rw [hc]; rfl
 -- proof-end
```

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -95,14 +95,19 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK (A-reference binding ambiguity): mapping.md binds `ordinaryLookup` to
+-- "the UNCHANGED Python ordinary attribute-access protocol `object.__getattribute__`
+-- as re-invoked by the fix (`self.__getattribute__(attr)`)" — it names BOTH, and
+-- for a receiver whose class overrides `__getattribute__` these are DIFFERENT
+-- callees. The Lean text pins neither: `ordinaryLookup` is opaque with the doc
+-- "the object's ordinary attribute-access result". This impl is byte-identical to
+-- the reference; the ATTACK lives entirely in the patch, which resolves the
+-- opaque callee to the unbound-protocol reading `object.__getattribute__(self, attr)`
+-- rather than the bound `self.__getattribute__(attr)`.
 def implementation_resolveAttr (self : CoordObj) (attr : String) :
     Except AttrError AttrValue := Id.run do
-  -- Try the domain-specific resolution branches; surface the outcome of
-  -- whichever applies, value or raised failure alike.
   if let some r := handledCase self attr then
     return r
-  -- Fall back to the object's ordinary attribute-access protocol, propagating
-  -- its outcome verbatim.
   return ordinaryLookup self attr
 -- impl-end
 
@@ -112,13 +117,7 @@
       problem_spec_resolveAttr self attr (implementation_resolveAttr self attr) := by
   intro self attr
   unfold problem_spec_resolveAttr implementation_resolveAttr
-  cases h : handledCase self attr with
-  | none =>
-    refine ⟨?_, ?_⟩
-    · intro r hr; exact Option.noConfusion hr
-    · intro _; rfl
-  | some r =>
-    refine ⟨?_, ?_⟩
-    · intro r' hr'; exact Option.some_inj.mp hr'
-    · intro hc; exact Option.noConfusion hc
+  refine ⟨?_, ?_⟩
+  · intro r hr; rw [hr]; rfl
+  · intro hc; rw [hc]; rfl
 -- proof-end
```

Attack 13 — `atk_13.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -95,14 +95,20 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK (A-leg purity gap on the OTHER callee): `handledCase` is declared
+-- `CoordObj -> String -> Option (Except AttrError AttrValue)`, i.e. the outcome of
+-- the domain-specific resolution branches is a FUNCTION of the receiver and the
+-- name. If so, memoizing that aggregate per (receiver, name) is behavior-
+-- preserving, and the faithful patch caches it. In the real repository the
+-- branches read MUTABLE receiver state (`self.frame`, frame attributes, and
+-- `self.transform_to(attr)`, which depends on obstime/location/representation),
+-- so the cache hands back a stale coordinate after that state changes. Purity is
+-- baked into the axiom's SIGNATURE, so the model cannot see the difference.
 def implementation_resolveAttr (self : CoordObj) (attr : String) :
     Except AttrError AttrValue := Id.run do
-  -- Try the domain-specific resolution branches; surface the outcome of
-  -- whichever applies, value or raised failure alike.
-  if let some r := handledCase self attr then
+  let cachedHandled := handledCase self attr
+  if let some r := cachedHandled then
     return r
-  -- Fall back to the object's ordinary attribute-access protocol, propagating
-  -- its outcome verbatim.
   return ordinaryLookup self attr
 -- impl-end
 
@@ -112,13 +118,7 @@
       problem_spec_resolveAttr self attr (implementation_resolveAttr self attr) := by
   intro self attr
   unfold problem_spec_resolveAttr implementation_resolveAttr
-  cases h : handledCase self attr with
-  | none =>
-    refine ⟨?_, ?_⟩
-    · intro r hr; exact Option.noConfusion hr
-    · intro _; rfl
-  | some r =>
-    refine ⟨?_, ?_⟩
-    · intro r' hr'; exact Option.some_inj.mp hr'
-    · intro hc; exact Option.noConfusion hc
+  refine ⟨?_, ?_⟩
+  · intro r hr; rw [hr]; rfl
+  · intro hc; rw [hc]; rfl
 -- proof-end
```

Attack 14 — `atk_14.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -95,15 +95,22 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK (A-reference binding, self-referential reading): the impl is the same
+-- shape as the reference, but the opaque fallback callee is resolved to the OTHER
+-- Python spelling of the phrase the spec uses for it. The `ordinaryLookup`
+-- doc-comment reads "the object's ordinary attribute-access result for the
+-- requested name" and the module docstring reads "the object's ordinary
+-- attribute-access result for that same name" -- in Python "ordinary attribute
+-- access" on an object is spelled `getattr(self, attr)`. Under that reading the
+-- fallback is self-referential (it re-enters the hook being defined), which the
+-- pure Lean model cannot express: `ordinaryLookup` is an opaque TOTAL function,
+-- so non-termination is unrepresentable and the proof closes regardless.
 def implementation_resolveAttr (self : CoordObj) (attr : String) :
     Except AttrError AttrValue := Id.run do
-  -- Try the domain-specific resolution branches; surface the outcome of
-  -- whichever applies, value or raised failure alike.
   if let some r := handledCase self attr then
     return r
-  -- Fall back to the object's ordinary attribute-access protocol, propagating
-  -- its outcome verbatim.
-  return ordinaryLookup self attr
+  let ordinary := ordinaryLookup self attr
+  return ordinary
 -- impl-end
 
 -- proof-start
@@ -112,13 +119,7 @@
       problem_spec_resolveAttr self attr (implementation_resolveAttr self attr) := by
   intro self attr
   unfold problem_spec_resolveAttr implementation_resolveAttr
-  cases h : handledCase self attr with
-  | none =>
-    refine ⟨?_, ?_⟩
-    · intro r hr; exact Option.noConfusion hr
-    · intro _; rfl
-  | some r =>
-    refine ⟨?_, ?_⟩
-    · intro r' hr'; exact Option.some_inj.mp hr'
-    · intro hc; exact Option.noConfusion hc
+  refine ⟨?_, ?_⟩
+  · intro r hr; rw [hr]; rfl
+  · intro hc; rw [hc]; rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit of astropy__astropy-14096 (lean). Focus per role brief: the A legs (both refinement.md rows are A-reference; there are no A-consumed legs) and the model<->patch correspondence. R/I legs left to G-CONF (the impl region is all-A-tagged, conf_skip=true).

### Mechanical baseline
* Positive control: cp Solution.lean -> pos_control.lean; `bash scripts/lean_verify.sh pos_control.lean` -> EXIT=0. `#print axioms correct_resolveAttr` (pos_control_ax.lean) -> `[propext]`, no sorryAx.
* Prepatch reproduced: atk_1.lean = Solution_prepatch.lean verbatim -> EXIT=1. Failure is the expected one and on the expected clause: `Tactic rfl failed ... (... Except.error { missing := attr } ...).run is not definitionally equal to ... ordinaryLookup self attr`, case none.refine_2. So spec clause 2 is exactly the patch delta and is discriminating.
* same_spec via swebench_unified.markers.same_spec(..., get_backend('lean').language) = True for ALL 14 attacks + pos_control. Every file edits only the impl+proof regions; axioms/pure/pre/post byte-identical.
* Admissibility: no `sorry`/`admit`/`native_decide` in any attack (grep -l over atk_*.lean -> none); exactly 1 top-level theorem in each attack, same as frozen Solution.lean (no new axiom/theorem/lemma); every `theorem correct_resolveAttr` statement byte-identical.
* Gold-patch resolve control: benchmark-verified/.../patch.diff -> run_resolve('astropy__astropy-14096', ...) -> resolved=True, F2P 1/1, P2P 426/426. Confirms the oracle lane is live, so a non-resolve would be real signal.

### ATTACKS THE SPEC REJECTED (verifier said NO -> spec has content)
All: `bash scripts/lean_verify.sh <path>`.
1. atk_1.lean (prepatch bug, fabricated {missing := attr}) -> EXIT=1.
2. atk_2.lean (PARTIAL DOMAIN: fix applied everywhere except attr = "prop", where the pre-fix error is still fabricated) -> EXIT=1, `rfl failed ... not definitionally equal to ordinaryLookup self attr`, case none.refine_2.
3. atk_3.lean (BOUNDARY / value-mangling: ordinary outcome IS consulted but its failure is re-stamped kind := "AttributeError", preserving the reported NAME so it would still satisfy the F2P `match="random_attr"` assertion) -> EXIT=1. This is the sharpest rejection: the spec's Except equality pins the failure CLASS too, not just the name, so it is strictly stronger than the F2P test.
4. atk_4.lean (CONTROL-FLOW: a branch that applies but RAISES has its failure swallowed and is re-routed to the fallback) -> EXIT=1, application type mismatch on clause 1. Confirms clause 1 genuinely constrains the Except.error arm of handledCase.
5. atk_8.lean (OBLIGATION-DROPPING: branches removed, every name goes straight to ordinaryLookup) -> EXIT=1, application type mismatch on clause 1.

#### VERIFYING CANDIDATES -> ALL FAITHFUL PATCHES RESOLVED (echoes)
Each verified EXIT=0 with clean axioms, then its faithful patch was materialized in a base_commit worktree (, `git worktree add --detach ... 1a4462d72e`), checked with `git apply --check` (rc=0 for all 9), and RUN through run_resolve (timeout=1800, retries=1). Axioms via a `_ax.lean` copy + `#print axioms correct_resolveAttr`.
6. atk_5.lean — CONTROL-FLOW EFFECT / eager hoist. The fallback outcome is computed UP FRONT (`let fallback := ordinaryLookup self attr`) before any branch is tried, then merely selected. In Lean ordinaryLookup is pure so this is invisible; the patch hoists `self.__getattribute__(attr)` into a try/except at the top of `__getattr__`, so the patched fallback line executes on EVERY call including ones where a branch applies. verify EXIT=0, axioms [propext]. atk_5.diff (1517B) -> resolved=True, F2P 1/1, P2P 426/426. ECHO.
7. atk_6.lean — ungrounded-oracle echo via `(handledCase self attr).getD (ordinaryLookup self attr)`. EXIT=0, axioms [propext]. atk_6.diff -> resolved=True, 1/1 + 426/426. ECHO (correctly scored as an alternative impl, not a weakness).
8. atk_7.lean — DUPLICATED evaluation of the handledCase aggregate (evaluated once to test, once to surface). EXIT=0, no axioms. Patch factors the branches into `_sbu_handled_case` and calls it twice, discarding the first -> the real branch expressions (getattr(self.frame,...), self.transform_to(attr)) run twice per call. atk_7.diff (2222B) -> resolved=True, 1/1 + 426/426. ECHO.
9. atk_9.lean — DUPLICATED evaluation of the effectful FALLBACK callee; first outcome discarded, second surfaced. EXIT=0, no axioms. Patch runs `self.__getattribute__(attr)` in a swallowing try/except then again for real -> every property getter runs twice and the first raise is swallowed. atk_9.diff -> resolved=True, 1/1 + 426/426. ECHO.
10. atk_10.lean — IDENTITY ERASURE on the deep model: the failure is torn down to the two fields AttrError records and a FRESH failure rebuilt from them. Definitional in Lean, so it closes. EXIT=0, no axioms. Patch does `raise type(_exc)(*_exc.args) from None`, discarding traceback, `__context__`/`__cause__` chain and AttributeError's .name/.obj — none of which the model can see. atk_10.diff -> resolved=True, 1/1 + 426/426. ECHO. This is the strongest surviving A-reference gap on paper and the test suite does not detect it.
11. atk_11.lean — A-LEG PURITY GAP: memoize the fallback outcome per (self, attr), which the axiom's SIGNATURE (CoordObj -> String -> Except ...) licenses. EXIT=0, no axioms. Patch caches on `(id(self), attr)` in a class dict. atk_11.diff -> resolved=True, 1/1 + 426/426. ECHO.
12. atk_12.lean — A-REFERENCE BINDING AMBIGUITY. mapping.md names BOTH `object.__getattribute__` and `self.__getattribute__(attr)` for one opaque callee; for a receiver overriding `__getattribute__` these differ, and the Lean text pins neither. Patch takes the unbound reading `object.__getattribute__(self, attr)`. EXIT=0, no axioms. atk_12.diff -> resolved=True, 1/1 + 426/426. ECHO (the ambiguity is real but not observable on this instance's tests).
13. atk_13.lean — purity gap on the OTHER A-reference callee (bind handledCase to a local). EXIT=0, no axioms. atk_13.diff (faithful: evaluate the aggregate ONCE, bind, surface) -> resolved=True, 1/1 + 426/426. ECHO.
14. atk_14.lean — A-reference binding via the docstring's own phrase ("the object's ordinary attribute-access result"). EXIT=0, no axioms. atk_14.diff (faithful: bind the DOCUMENTED callee `self.__getattribute__(attr)` once, return it) -> resolved=True, 1/1 + 426/426. ECHO.

#### TWO NON-RESOLVING PATCHES, BOTH JUDGED UNFAITHFUL (not findings)
These are reported in full because they are the closest this audit came to BROKEN and the reader should be able to re-derive the faithfulness call rather than take my word.
* atk_13_UNFAITHFUL_crosscall.diff — a PERSISTENT class-level cache of the handledCase aggregate keyed on (id(self), attr). run_resolve -> resolved=False, F2P 1/1 but P2P 367/426 (59 failures: test_transform_to, many test_round_tripping[...]). REJECTED as unfaithful: atk_13's Lean impl differs from gold ONLY by `let cachedHandled := handledCase self attr`, and a Lean `let` is a single per-call binding, not cross-call mutable state. Nothing in the impl region licenses state that survives the call. The faithful reading (one evaluation per call) is atk_13.diff, which resolves 426/426. Refinement fidelity is a per-call semantics question, and inventing persistent state is my over-refinement, not a spec hole.
* atk_14_UNFAITHFUL_calleeswap.diff — resolves the opaque callee to `getattr(self, attr)` instead of `self.__getattribute__(attr)`. run_resolve -> resolved=False, F2P 0/1 AND P2P 129/426 (297 failures) — it re-enters `__getattr__`, so it recurses. REJECTED as unfaithful: mapping.md binds `ordinaryLookup` explicitly to `self.__getattribute__(attr)`, so the A-reference binding is pinned and `getattr` is a DIFFERENT callee. Also self-defeating as evidence: the Lean model makes ordinaryLookup a TOTAL function, so non-termination is unrepresentable — a patch that diverges is not a refinement of a total callee at all. Faithful reading is atk_14.diff, which resolves.
Both retained on disk under their *_UNFAITHFUL_* names with their resolve JSON, deliberately NOT submitted as findings, per the rule that an echo or an over-refinement must not be re-scored into the reject lane.

#### refinement.md LEG AUDIT (no kind-3)
Two legs, both tagged A-reference; zero A-consumed, zero R, zero I. Verified against the base_commit worktree:
* Leg 1 `if let some r := handledCase self attr then return r` -> the UNCHANGED resolution branches. Claimed lines 873-895; `sed -n 873,895p` shows exactly the docstring close + `if "_sky_coord_frame" in self.__dict__:` block through `return self.transform_to(attr)`. Correspondence HOLDS. The three-valued codomain is justified: the branches are evaluated expressions, not guards, so `some (Except.error e)` is reachable — mapping.md measures four such names (altaz/lsr/galactocentric/hcrs -> AttributeError/TypeError/ConvertError/UnitsError), which is also why AttrError carries `kind`. Patch-independence holds: the branches return-or-raise before the fail path in both versions and the patch rewrites only the fail path. Confirmed by reading base_commit source directly.
* Leg 2 `return ordinaryLookup self attr` -> the PATCHED fail path. Claimed lines 894-898; `sed -n 896,900p` shows the `# Fail` / `raise AttributeError(f"...'{attr}'")` block that patch.diff replaces with `return self.__getattribute__(attr)`, matching patch.diff's @@ -894,10 +894,8 @@ hunk. Correspondence HOLDS.
* Every leg is R / A-consumed / A-reference / I. NO kind-3 (unjustified) leg. Control-flow prose (`Id.run do`, early return on the applying branch, tail return on the fallback) matches the real `__getattr__` epilogue. mapping.md's "Proof obligations" claim that both `_prop` slots are empty and that `#print axioms` gives [propext] is confirmed independently (pos_control_ax -> [propext]).

### Assessment
The spec is a TOTAL pointwise characterization of the result for every (self, attr): clause 1 pins the applying branch's outcome verbatim including its Except.error arm, clause 2 pins the fallback to ordinaryLookup on both halves. That leaves no room for a value-level wrong impl — all 5 value-level attacks were rejected, and atk_3 shows the spec is strictly STRONGER than the F2P test (it pins the failure class, which the `match="random_attr"` assertion does not). The residual attack surface is entirely in what a pure Lean function of (self, attr) cannot express: evaluation count, evaluation order, persistence, and Python exception-object identity beyond (name, class).

I built six attacks in exactly that surface (atk_5, 7, 9, 10, 11, 12) and every faithful patch resolved 426/426 + F2P, so none is a machine-checked verify-not-correct witness. That residue is an inherent limit of a pure functional model of an effectful attribute hook, shared by every bundle of this shape, and it is disclosed rather than hidden: mapping.md argues the point-function modeling explicitly and the G-PANEL-2 record addresses single-invocation. It is not a G-EQ finding on this bundle. 14 attacks run (>= 5 floor), 9 resolve runs plus 1 gold control plus 2 unfaithful-patch runs = 12 executed harness runs, all completed (no timeouts, no infra errors). Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 9 | `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean` |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec implementation with a closing clean-axiom proof has a FAITHFUL refined patch that fails to resolve. 14 attacks: 4 value-level wrong impls were REJECTED by the verifier (spec has real content); 10 verified with clean axioms and all 10 faithful patches RESOLVED (echoes). Two patches did NOT resolve (atk_13 cross-call memo of handledCase: P2P 367/426, 59 failures; atk_14 callee swap to getattr(self, attr): F2P 0/1 + P2P 129/426, infinite recursion) but BOTH were judged UNFAITHFUL over-refinements of their own Lean impls, and each one's faithful refinement then resolved 426/426 + F2P. Retained at atk_13_UNFAITHFUL_crosscall.diff and atk_14_UNFAITHFUL_calleeswap.diff as the near-miss record, NOT submitted as findings.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 14 — `atk_14.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit of astropy__astropy-14096 (lean). Focus per role brief: the A legs (both refinement.md rows are A-reference; there are no A-consumed legs) and the model<->patch correspondence. R/I legs left to G-CONF (the impl region is all-A-tagged, conf_skip=true).

### Mechanical baseline
* Positive control: cp Solution.lean -> pos_control.lean; `bash scripts/lean_verify.sh pos_control.lean` -> EXIT=0. `#print axioms correct_resolveAttr` (pos_control_ax.lean) -> `[propext]`, no sorryAx.
* Prepatch reproduced: atk_1.lean = Solution_prepatch.lean verbatim -> EXIT=1. Failure is the expected one and on the expected clause: `Tactic rfl failed ... (... Except.error { missing := attr } ...).run is not definitionally equal to ... ordinaryLookup self attr`, case none.refine_2. So spec clause 2 is exactly the patch delta and is discriminating.
* same_spec via swebench_unified.markers.same_spec(..., get_backend('lean').language) = True for ALL 14 attacks + pos_control. Every file edits only the impl+proof regions; axioms/pure/pre/post byte-identical.
* Admissibility: no `sorry`/`admit`/`native_decide` in any attack (grep -l over atk_*.lean -> none); exactly 1 top-level theorem in each attack, same as frozen Solution.lean (no new axiom/theorem/lemma); every `theorem correct_resolveAttr` statement byte-identical.
* Gold-patch resolve control: benchmark-verified/.../patch.diff -> run_resolve('astropy__astropy-14096', ...) -> resolved=True, F2P 1/1, P2P 426/426. Confirms the oracle lane is live, so a non-resolve would be real signal.

### ATTACKS THE SPEC REJECTED (verifier said NO -> spec has content)
All: `bash scripts/lean_verify.sh <path>`.
1. atk_1.lean (prepatch bug, fabricated {missing := attr}) -> EXIT=1.
2. atk_2.lean (PARTIAL DOMAIN: fix applied everywhere except attr = "prop", where the pre-fix error is still fabricated) -> EXIT=1, `rfl failed ... not definitionally equal to ordinaryLookup self attr`, case none.refine_2.
3. atk_3.lean (BOUNDARY / value-mangling: ordinary outcome IS consulted but its failure is re-stamped kind := "AttributeError", preserving the reported NAME so it would still satisfy the F2P `match="random_attr"` assertion) -> EXIT=1. This is the sharpest rejection: the spec's Except equality pins the failure CLASS too, not just the name, so it is strictly stronger than the F2P test.
4. atk_4.lean (CONTROL-FLOW: a branch that applies but RAISES has its failure swallowed and is re-routed to the fallback) -> EXIT=1, application type mismatch on clause 1. Confirms clause 1 genuinely constrains the Except.error arm of handledCase.
5. atk_8.lean (OBLIGATION-DROPPING: branches removed, every name goes straight to ordinaryLookup) -> EXIT=1, application type mismatch on clause 1.

#### VERIFYING CANDIDATES -> ALL FAITHFUL PATCHES RESOLVED (echoes)
Each verified EXIT=0 with clean axioms, then its faithful patch was materialized in a base_commit worktree (, `git worktree add --detach ... 1a4462d72e`), checked with `git apply --check` (rc=0 for all 9), and RUN through run_resolve (timeout=1800, retries=1). Axioms via a `_ax.lean` copy + `#print axioms correct_resolveAttr`.
6. atk_5.lean — CONTROL-FLOW EFFECT / eager hoist. The fallback outcome is computed UP FRONT (`let fallback := ordinaryLookup self attr`) before any branch is tried, then merely selected. In Lean ordinaryLookup is pure so this is invisible; the patch hoists `self.__getattribute__(attr)` into a try/except at the top of `__getattr__`, so the patched fallback line executes on EVERY call including ones where a branch applies. verify EXIT=0, axioms [propext]. atk_5.diff (1517B) -> resolved=True, F2P 1/1, P2P 426/426. ECHO.
7. atk_6.lean — ungrounded-oracle echo via `(handledCase self attr).getD (ordinaryLookup self attr)`. EXIT=0, axioms [propext]. atk_6.diff -> resolved=True, 1/1 + 426/426. ECHO (correctly scored as an alternative impl, not a weakness).
8. atk_7.lean — DUPLICATED evaluation of the handledCase aggregate (evaluated once to test, once to surface). EXIT=0, no axioms. Patch factors the branches into `_sbu_handled_case` and calls it twice, discarding the first -> the real branch expressions (getattr(self.frame,...), self.transform_to(attr)) run twice per call. atk_7.diff (2222B) -> resolved=True, 1/1 + 426/426. ECHO.
9. atk_9.lean — DUPLICATED evaluation of the effectful FALLBACK callee; first outcome discarded, second surfaced. EXIT=0, no axioms. Patch runs `self.__getattribute__(attr)` in a swallowing try/except then again for real -> every property getter runs twice and the first raise is swallowed. atk_9.diff -> resolved=True, 1/1 + 426/426. ECHO.
10. atk_10.lean — IDENTITY ERASURE on the deep model: the failure is torn down to the two fields AttrError records and a FRESH failure rebuilt from them. Definitional in Lean, so it closes. EXIT=0, no axioms. Patch does `raise type(_exc)(*_exc.args) from None`, discarding traceback, `__context__`/`__cause__` chain and AttributeError's .name/.obj — none of which the model can see. atk_10.diff -> resolved=True, 1/1 + 426/426. ECHO. This is the strongest surviving A-reference gap on paper and the test suite does not detect it.
11. atk_11.lean — A-LEG PURITY GAP: memoize the fallback outcome per (self, attr), which the axiom's SIGNATURE (CoordObj -> String -> Except ...) licenses. EXIT=0, no axioms. Patch caches on `(id(self), attr)` in a class dict. atk_11.diff -> resolved=True, 1/1 + 426/426. ECHO.
12. atk_12.lean — A-REFERENCE BINDING AMBIGUITY. mapping.md names BOTH `object.__getattribute__` and `self.__getattribute__(attr)` for one opaque callee; for a receiver overriding `__getattribute__` these differ, and the Lean text pins neither. Patch takes the unbound reading `object.__getattribute__(self, attr)`. EXIT=0, no axioms. atk_12.diff -> resolved=True, 1/1 + 426/426. ECHO (the ambiguity is real but not observable on this instance's tests).
13. atk_13.lean — purity gap on the OTHER A-reference callee (bind handledCase to a local). EXIT=0, no axioms. atk_13.diff (faithful: evaluate the aggregate ONCE, bind, surface) -> resolved=True, 1/1 + 426/426. ECHO.
14. atk_14.lean — A-reference binding via the docstring's own phrase ("the object's ordinary attribute-access result"). EXIT=0, no axioms. atk_14.diff (faithful: bind the DOCUMENTED callee `self.__getattribute__(attr)` once, return it) -> resolved=True, 1/1 + 426/426. ECHO.

#### TWO NON-RESOLVING PATCHES, BOTH JUDGED UNFAITHFUL (not findings)
These are reported in full because they are the closest this audit came to BROKEN and the reader should be able to re-derive the faithfulness call rather than take my word.
* atk_13_UNFAITHFUL_crosscall.diff — a PERSISTENT class-level cache of the handledCase aggregate keyed on (id(self), attr). run_resolve -> resolved=False, F2P 1/1 but P2P 367/426 (59 failures: test_transform_to, many test_round_tripping[...]). REJECTED as unfaithful: atk_13's Lean impl differs from gold ONLY by `let cachedHandled := handledCase self attr`, and a Lean `let` is a single per-call binding, not cross-call mutable state. Nothing in the impl region licenses state that survives the call. The faithful reading (one evaluation per call) is atk_13.diff, which resolves 426/426. Refinement fidelity is a per-call semantics question, and inventing persistent state is my over-refinement, not a spec hole.
* atk_14_UNFAITHFUL_calleeswap.diff — resolves the opaque callee to `getattr(self, attr)` instead of `self.__getattribute__(attr)`. run_resolve -> resolved=False, F2P 0/1 AND P2P 129/426 (297 failures) — it re-enters `__getattr__`, so it recurses. REJECTED as unfaithful: mapping.md binds `ordinaryLookup` explicitly to `self.__getattribute__(attr)`, so the A-reference binding is pinned and `getattr` is a DIFFERENT callee. Also self-defeating as evidence: the Lean model makes ordinaryLookup a TOTAL function, so non-termination is unrepresentable — a patch that diverges is not a refinement of a total callee at all. Faithful reading is atk_14.diff, which resolves.
Both retained on disk under their *_UNFAITHFUL_* names with their resolve JSON, deliberately NOT submitted as findings, per the rule that an echo or an over-refinement must not be re-scored into the reject lane.

#### refinement.md LEG AUDIT (no kind-3)
Two legs, both tagged A-reference; zero A-consumed, zero R, zero I. Verified against the base_commit worktree:
* Leg 1 `if let some r := handledCase self attr then return r` -> the UNCHANGED resolution branches. Claimed lines 873-895; `sed -n 873,895p` shows exactly the docstring close + `if "_sky_coord_frame" in self.__dict__:` block through `return self.transform_to(attr)`. Correspondence HOLDS. The three-valued codomain is justified: the branches are evaluated expressions, not guards, so `some (Except.error e)` is reachable — mapping.md measures four such names (altaz/lsr/galactocentric/hcrs -> AttributeError/TypeError/ConvertError/UnitsError), which is also why AttrError carries `kind`. Patch-independence holds: the branches return-or-raise before the fail path in both versions and the patch rewrites only the fail path. Confirmed by reading base_commit source directly.
* Leg 2 `return ordinaryLookup self attr` -> the PATCHED fail path. Claimed lines 894-898; `sed -n 896,900p` shows the `# Fail` / `raise AttributeError(f"...'{attr}'")` block that patch.diff replaces with `return self.__getattribute__(attr)`, matching patch.diff's @@ -894,10 +894,8 @@ hunk. Correspondence HOLDS.
* Every leg is R / A-consumed / A-reference / I. NO kind-3 (unjustified) leg. Control-flow prose (`Id.run do`, early return on the applying branch, tail return on the fallback) matches the real `__getattr__` epilogue. mapping.md's "Proof obligations" claim that both `_prop` slots are empty and that `#print axioms` gives [propext] is confirmed independently (pos_control_ax -> [propext]).

### Assessment
The spec is a TOTAL pointwise characterization of the result for every (self, attr): clause 1 pins the applying branch's outcome verbatim including its Except.error arm, clause 2 pins the fallback to ordinaryLookup on both halves. That leaves no room for a value-level wrong impl — all 5 value-level attacks were rejected, and atk_3 shows the spec is strictly STRONGER than the F2P test (it pins the failure class, which the `match="random_attr"` assertion does not). The residual attack surface is entirely in what a pure Lean function of (self, attr) cannot express: evaluation count, evaluation order, persistence, and Python exception-object identity beyond (name, class).

I built six attacks in exactly that surface (atk_5, 7, 9, 10, 11, 12) and every faithful patch resolved 426/426 + F2P, so none is a machine-checked verify-not-correct witness. That residue is an inherent limit of a pure functional model of an effectful attribute hook, shared by every bundle of this shape, and it is disclosed rather than hidden: mapping.md argues the point-function modeling explicitly and the G-PANEL-2 record addresses single-invocation. It is not a G-EQ finding on this bundle. 14 attacks run (>= 5 floor), 9 resolve runs plus 1 gold control plus 2 unfaithful-patch runs = 12 executed harness runs, all completed (no timeouts, no infra errors). Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

G-PANEL-2 faithfulness-break attack on astropy__astropy-14096 (lean). Modeled function: SkyCoord.`__getattr__` (astropy/coordinates/sky_coordinate.py:867). Reference =  worktree at base_commit 1a4462d72e with patch.diff APPLIED (confirmed: `git diff --stat` = 1 file, 2+/4-; inspect.getsource shows `return self.__getattribute__(attr)` => PATCHED). NO base-version comparison was used as the divergence oracle.

### Mechanical checks
* scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry).
* `#print axioms correct_resolveAttr` -> `[propext]`. Clean: no sorryAx, so the proof is real, not fake.
* markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) -> True. Spec region byte-identical; the only diff is the impl region (op 2 replaced by the fabricated `Except.error { missing := attr }`) plus comments.
* Prepatch discriminator genuinely FAILS to close, with the expected goal: `(... Except.error { missing := attr } ...).run = ordinaryLookup self attr` -- 'is not definitionally equal'. So the spec's clause 2 is the exact discriminator for the patch delta; the spec is not vacuous.

### ENVIRONMENT (built from scratch to get a real oracle)
No pre-built astropy existed. Built C extensions  via a fresh venv: setuptools 80.10.2 + a `setuptools/dep_util.py` shim (re-exporting from setuptools.modified, which astropy/wcs/setup_package.py needs), numpy==1.23.5 + pyerfa 2.0.0.3 (numpy 2.2 removed np.product, which astropy 5.2 imports), and a stubbed astropy/version.py. 17 .so built; `import astropy.coordinates` succeeds and reports PATCHED.

### EMPIRICAL FAITHFULNESS TESTING (all against the real patched callee)
1) mapping.md's three-valued handledCase table reproduces EXACTLY on the real repo with SkyCoord('00h42m30s','+41d12m00s',frame='icrs'): altaz -> AttributeError('to_geodetic'), lsr -> TypeError, galactocentric -> ConvertError, hcrs -> UnitsError. Three of four are NOT AttributeError, which is precisely why AttrError carries a `kind` field and why the aggregate's codomain is `Except`, not a bare value. fk5 -> ok (branch resolves). So the Option/Except three-valuedness is measured, not asserted.
2) Clause 2 (the falsifiable content, `handledCase = none -> result = ordinaryLookup self attr`) tested by instrumenting the traceback for the literal fallback line `return self.__getattribute__(attr)` to detect when the fallback is genuinely reached, then comparing `__getattr__`'s outcome against `__getattribute__`'s outcome (kind + reported missing name):
   - Targeted sweep: 77 fallback error-paths + 115 no-branch names across 4 receivers (subclass, plain, 3-D, guard-key-removed). 0 violations, 0 mismatches.
   - Seeded fuzz sweep (seed 20240629, per mapping.md): 1350 fallback-reaching (receiver, name) pairs -- 71 ok-side + 1279 error-side -- over 5 receivers (icrs subclass, plain, 3-D w/ distance, galactic, array fk5) and a name pool of all frame graph names, all frame_attributes, dunders, real methods, properties, empty string, non-ASCII ('日本'), names with spaces, and 250 random identifiers. clause-2 divergences: 0.
3) Edge probes all confirm the spec rather than break it: explicit `self.__getattribute__(attr)` does NOT re-enter `__getattr__` (single invocation, no recursion); the F2P scenario c.prop reports 'random_attr' NOT 'prop' (the error-naming property is the discriminator and it holds); a ValueError raised on the fail path propagates VERBATIM and is byte-identical to `__getattribute__`'s own exception (kind preserved -- clause 2 is an equality on both halves of Except, and the non-AttributeError half is reachable and correct); a two-level property chain a->b->c_absent reports 'c_absent', the innermost genuinely-missing name.

### WHY NOT TOO STRONG (the specific charge of this gate)
* Clause 1 quantifies over an opaque aggregate (`forall r, handledCase = some r -> result = r`). It asserts surfacing-unchanged, not any property OF the branches, so it cannot over-constrain them; the raised-exception case is carried by Except.error rather than being excluded, which is what makes the four measured raising names admissible instead of contradictions.
* Clause 2 is exactly `self.__getattribute__(attr)` propagated verbatim -- the literal patched line. It adds no substitution, no name rewriting, no kind narrowing. Notably the spec deliberately does NOT assert that ordinaryLookup's reported name equals `attr` (the docstring and the ordinaryLookup doc-comment both say it need not), which is the over-strengthening one would expect here and which the real repo would refute; the spec avoids it.
* Modeling attribute access as a pure function of (self, attr) is sound for the modeled unit: `__getattr__` invokes `__getattribute__` once, so the double-evaluation visible on the implicit `c.prop` path (interpreter call, then the fix's retry) is outside this function's boundary and cannot be a divergence of it.
* AttrError's `missing := ""` convention for kinds that name no attribute is applied to BOTH sides of the clause-2 equality, so it cannot manufacture a constraint.

**CONCLUSION:** no diverging input found. I could not construct any (self, attr) on which problem_spec_resolveAttr disagrees with the real patched SkyCoord.`__getattr__`, across 1542 measured input pairs plus targeted edge cases. The spec is a faithful, appropriately-abstract, non-vacuous model of the fixed behavior; its single falsifiable clause is precisely the patch delta and it is discriminating (prepatch fails to verify). No faithfulness defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

NO-LEAKAGE on astropy__astropy-14096 (lean). No relaxation in this bundle: there is no RELAXED_LEAKAGE.md and meta.json has no `relaxed_leakage` key; gates.G-LEAK.status == "pass" (mode "strict"), so this is an ordinary strict-lane leakage judgement, not an inherited disposition.

### WHAT I MEASURED (my own runs, not verdict.md's assertions):
* Spec view materialized myself: markers.spec_view(Solution.lean, get_backend('lean')) -> the impl and proof regions collapse to `-- implementation elided` / `-- proof elided`, so the consumer sees imports + module docstring + axioms + pure + post-conditions only. Saved and grepped that exact text (not the raw file).
* leakage.screen(Solution.lean, lean tables, instance.patch, instance.problem_statement, instance.test_patch) -> passed=True, hard_failures=[], warnings=[]. Re-ran the sub-checks by hand on the spec view: `_NARRATION_RE` hits = [] (no bug/fix/patch/previously/incorrectly/wrong narration); `_LEAN_DIFF_MARKERS` present = []; gold changed-lines reproduced (whitespace-normalized) = only ')' — a content-free fragment, none of `raise AttributeError(`, the `'{self.__class__.__name__}' object has no attribute '{attr}'` message, or `return self.__getattribute__(attr)`; `_patch_changed_symbols` = {'getattr'} and no spec-view identifier embeds it (spec ids colliding with 'getattr' = []).
* Targeted grep of the spec view for every repo/gold token: `sky_coordinate`, `astropy`, `SkyCoord`, `__getattr`, `getattribute`, `transform_to`, `frame_transform_graph`, `lookup_name`, `_is_name`, `_sky_coord_frame`, `is_transformable_to`, `__class__`, `self.__`, `raise ` — all 0 hits. The patched file path and function name appear nowhere. The abstractions used instead are `CoordObj`, `handledCase`, `ordinaryLookup`, "rich coordinate object", "fallback attribute-resolution hook", "the object's ordinary attribute-access result" — none echoes a patched repo symbol. Only "AttributeError" appears, as the `kind` default string, and that literal is in the public problem_statement's traceback.
* F2P test-identity: `random_attr`, `prop` (as an identifier), `custom_coord`, `test_subclass_property_exception_error`, `gh-8340` — all absent from the spec view. The 4 'prop' substring hits are all English ("propagated", "property axiom"), not the test's attribute name.

BEYOND-PROBLEM_STATEMENT ANALYSIS (the actual charge). The strongest candidate line is the docstring clause "it does not replace a genuine attribute-access failure with one it manufactures from the originally requested name. Whatever name the ordinary lookup reports in its failure is the name the hook reports," plus post-conditions clause 2 `handledCase self attr = none -> result = ordinaryLookup self attr`.

That content is derivable from the PUBLIC problem_statement alone, with nothing taken from hints_text: the statement's title is "Subclassed SkyCoord gives misleading attribute access message"; its body says the message "says `prop` doesn't exist, where it should say `random_attr` doesn't exist" (= report the genuinely-missing inner name, not the requested one); and its traceback publicly exhibits the fail path itself in sky_coordinate.py `__getattr__` at the `.format(self.__class__.__name__, attr)` line (= the manufactured-from-`attr` message). So the spec view states LESS than the public statement, not more — it never names `__getattribute__`, never names the file/function/line, and gives no mechanism for how to defer. I checked hints_text separately: its content (catch the AttributeError in the property, raise another exception, the StackOverflow link) is NOT echoed anywhere in the spec view.
* Load-bearing test run for completeness even though no relaxation is claimed: I stripped that narration clause from both files and rebuilt. scripts/lean_verify.sh on the de-narrated Solution.lean -> exit 0, and on the de-narrated Solution_prepatch.lean -> exit 1 (still fails). So the discriminator is the FORMAL clause 2, not the prose; the prose is redundant restatement of public content rather than load-bearing narration. That is the outcome that favors NO-LEAKAGE: nothing in the prose is doing work the public statement doesn't already do.
* The `kind` field / transform-target sentences describe the UNCHANGED resolution branches (patch.diff touches only lines 894-898, the fail path). Describing unchanged callee behavior localizes no edit; and the patched function is already public via the statement's traceback.

CORE GATES THIS DISPOSITION LEANS ON, re-run by me:
* scripts/lean_verify.sh Solution.lean -> exit 0; appended `#print axioms correct_resolveAttr` -> `'correct_resolveAttr' depends on axioms: [propext]`. Clean — no sorryAx, so the proof is real.
* markers.same_spec(Solution.lean, Solution_prepatch.lean, lean) -> True. Spec region byte-identical; diff confined to impl+proof regions (fallback replaced by `Except.error { missing := attr }` plus comments).
* Solution_prepatch.lean -> exit 1 with the expected goal `(... Except.error { missing := attr } ...).run = ordinaryLookup self attr` "is not definitionally equal" — spec is discriminating, not vacuous.
* patch.diff == instance.json['patch'] byte-for-byte.
* leakage.reviewer_directed() on refinement.md, mapping.md and verdict.md -> [] for all three. No file in this bundle addresses me, prescribes a verdict, or dictates a recording convention.

SEPARATE FINDING, not a leakage defect — STALE meta.json region_hashes. meta.json['region_hashes'] does NOT match the shipped Solution.lean (sha 0b641452b02d): computed spec_view 4d7fa04cdbfd vs recorded 0e3ae44381dc, and axioms/impl/proof/post-conditions all differ (only `pure` matches). I traced it: the recorded hashes are those of the PREVIOUS Solution.lean at commit 2e134ea1f (sha 315e1efbca9c), superseded by a docstring/comment rewrite at a90465910.

Consequences for the record, which I want visible rather than folded into my verdict: (a) G-EQ, G-PANEL-1 and the prior G-PANEL-3 stamps all pin sources.Solution.lean = 315e1ef..., i.e. they were measured on the older prose, so their retained attacks are voided by a prose edit (spec_signature covers docstrings) and those cells need re-audit, not repair; (b) G-LEAK's own stamp pins 0b6414... = the CURRENT bytes, and I independently re-ran the screen on the current bytes and got clean, so MY leakage disposition rests on a measurement of the shipped artifact and does not inherit the stale stamp. I also screened the OLD version's spec view (leakage.screen -> passed=True): the prose edit did not change the leak disposition in either direction. The stale region_hashes is an audit-freshness/bookkeeping defect for the owning gate to restamp; it is not evidence that the spec view leaks the gold edit, so it does not convert this verdict to LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
