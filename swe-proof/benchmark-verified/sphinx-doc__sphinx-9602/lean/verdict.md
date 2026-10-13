# P2 adversarial audit — sphinx-doc__sphinx-9602

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1_prepatch.lean`, `atk_2_headblind.lean`, `atk_3_toobroad.lean`, `atk_4_toonarrow.lean`, `atk_5_empty_abbrev.lean`, `atk_10_firstonly.lean`, `atk_11_headtext.lean`, `atk_12_emptyparen_text.lean`, `atk_14_sepwrong.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_6_okhead_drop.lean`, `atk_7_oklit_drop.lean`, `atk_8_oracle_echo.lean`, `atk_9_restructured.lean`, `atk_13_oklit_barestr.lean`, `atk_15_okhead_text.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -227,16 +227,10 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The head renders as a navigable cross-reference; the bracketed argument list
-is built by `valSeq` with the head-determined argument constructor, where each
-constant value's display text is its canonical source form (`reprVal`). Under
-the enumeration head the argument nodes are plain display text, so a value such
-as a boolean or an integer carries no class reference; under any other dotted
-head they stay cross-references. -/
+/-- PREPATCH: the argument values are routed through the cross-reference path for EVERY head (the pre-fix top-level loop turned every non-blank inline Text into a cross-reference). -/
 def implementation_literalTypeNodes
     (head : List Char) (values : List LitVal) : List DocNode :=
-  let inner := valSeq (argNodeCtor head) reprVal values
-  wrap head inner
+  wrap head (valSeq DocNode.xref reprVal values)
 -- impl-end
 
 -- proof-start
@@ -248,4 +242,5 @@
   unfold problem_spec_literalTypeNodes implementation_literalTypeNodes expandLiteral
   intro _ _
   rfl
+#print axioms correct_literalTypeNodes
 -- proof-end
```

Attack 2 — `atk_2_headblind.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -227,16 +227,10 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The head renders as a navigable cross-reference; the bracketed argument list
-is built by `valSeq` with the head-determined argument constructor, where each
-constant value's display text is its canonical source form (`reprVal`). Under
-the enumeration head the argument nodes are plain display text, so a value such
-as a boolean or an integer carries no class reference; under any other dotted
-head they stay cross-references. -/
+/-- HEAD-BLIND: the argument values are plain display text for EVERY parametrised head; the head is never read to decide the argument node class. This is the counterexample a prior audit pass recorded against an earlier (head-as-precondition) spec. -/
 def implementation_literalTypeNodes
     (head : List Char) (values : List LitVal) : List DocNode :=
-  let inner := valSeq (argNodeCtor head) reprVal values
-  wrap head inner
+  wrap head (valSeq DocNode.text reprVal values)
 -- impl-end
 
 -- proof-start
@@ -248,4 +242,5 @@
   unfold problem_spec_literalTypeNodes implementation_literalTypeNodes expandLiteral
   intro _ _
   rfl
+#print axioms correct_literalTypeNodes
 -- proof-end
```

Attack 3 — `atk_3_toobroad.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -227,16 +227,11 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The head renders as a navigable cross-reference; the bracketed argument list
-is built by `valSeq` with the head-determined argument constructor, where each
-constant value's display text is its canonical source form (`reprVal`). Under
-the enumeration head the argument nodes are plain display text, so a value such
-as a boolean or an integer carries no class reference; under any other dotted
-head they stay cross-references. -/
+/-- TOO BROAD head selection: plain text whenever the head merely ENDS with `Literal`, so `MyLiteral[...]` / `pkg.NotALiteral[...]` also lose their cross-references. -/
 def implementation_literalTypeNodes
     (head : List Char) (values : List LitVal) : List DocNode :=
-  let inner := valSeq (argNodeCtor head) reprVal values
-  wrap head inner
+  wrap head (valSeq (if (head.reverse.take 7).reverse == "Literal".toList
+                     then DocNode.text else DocNode.xref) reprVal values)
 -- impl-end
 
 -- proof-start
@@ -248,4 +243,5 @@
   unfold problem_spec_literalTypeNodes implementation_literalTypeNodes expandLiteral
   intro _ _
   rfl
+#print axioms correct_literalTypeNodes
 -- proof-end
```

Attack 4 — `atk_4_toonarrow.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -227,16 +227,11 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The head renders as a navigable cross-reference; the bracketed argument list
-is built by `valSeq` with the head-determined argument constructor, where each
-constant value's display text is its canonical source form (`reprVal`). Under
-the enumeration head the argument nodes are plain display text, so a value such
-as a boolean or an integer carries no class reference; under any other dotted
-head they stay cross-references. -/
+/-- TOO NARROW head selection: only the bare `Literal` spelling suppresses the cross-reference; `typing.Literal[...]` still renders its values as class references. -/
 def implementation_literalTypeNodes
     (head : List Char) (values : List LitVal) : List DocNode :=
-  let inner := valSeq (argNodeCtor head) reprVal values
-  wrap head inner
+  wrap head (valSeq (if head == "Literal".toList then DocNode.text else DocNode.xref)
+               reprVal values)
 -- impl-end
 
 -- proof-start
@@ -248,4 +243,5 @@
   unfold problem_spec_literalTypeNodes implementation_literalTypeNodes expandLiteral
   intro _ _
   rfl
+#print axioms correct_literalTypeNodes
 -- proof-end
```

Attack 5 — `atk_5_empty_abbrev.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -227,16 +227,11 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The head renders as a navigable cross-reference; the bracketed argument list
-is built by `valSeq` with the head-determined argument constructor, where each
-constant value's display text is its canonical source form (`reprVal`). Under
-the enumeration head the argument nodes are plain display text, so a value such
-as a boolean or an integer carries no class reference; under any other dotted
-head they stay cross-references. -/
+/-- BOUNDARY on the zero-argument spelling: on an EMPTY argument list the brackets are dropped altogether and only the head cross-reference is emitted. This is the impl a PRIOR audit pass used to break the earlier spec, which carried a `values != []` hypothesis; re-encoded here against the CURRENT (repaired) spec. -/
 def implementation_literalTypeNodes
     (head : List Char) (values : List LitVal) : List DocNode :=
-  let inner := valSeq (argNodeCtor head) reprVal values
-  wrap head inner
+  if values.isEmpty then [DocNode.xref head]
+  else wrap head (valSeq (argNodeCtor head) reprVal values)
 -- impl-end
 
 -- proof-start
@@ -247,5 +242,8 @@
   intro head values
   unfold problem_spec_literalTypeNodes implementation_literalTypeNodes expandLiteral
   intro _ _
-  rfl
+  cases values with
+  | nil => rfl
+  | cons v vs => rfl
+#print axioms correct_literalTypeNodes
 -- proof-end
```

Attack 6 — `atk_6_okhead_drop.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -227,16 +227,13 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The head renders as a navigable cross-reference; the bracketed argument list
-is built by `valSeq` with the head-determined argument constructor, where each
-constant value's display text is its canonical source form (`reprVal`). Under
-the enumeration head the argument nodes are plain display text, so a value such
-as a boolean or an integer carries no class reference; under any other dotted
-head they stay cross-references. -/
+/-- PARTIAL DOMAIN (okHead), maximally destructive off-domain: while the head is a dotted ASCII Python name the gold rendering is used; for ANY other head string (a non-ASCII identifier such as `Unicode`-lettered names, or a reserved-word head) the brackets and the whole argument list are DROPPED and the head is emitted as plain display text. The `okHead` hypothesis leaves that region entirely free. -/
 def implementation_literalTypeNodes
     (head : List Char) (values : List LitVal) : List DocNode :=
-  let inner := valSeq (argNodeCtor head) reprVal values
-  wrap head inner
+  if okHead head then
+    wrap head (valSeq (argNodeCtor head) reprVal values)
+  else
+    [DocNode.text head]
 -- impl-end
 
 -- proof-start
@@ -246,6 +243,7 @@
         (implementation_literalTypeNodes head values) := by
   intro head values
   unfold problem_spec_literalTypeNodes implementation_literalTypeNodes expandLiteral
-  intro _ _
-  rfl
+  intro h1 _
+  simp [h1]
+#print axioms correct_literalTypeNodes
 -- proof-end
```

Attack 7 — `atk_7_oklit_drop.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -227,16 +227,13 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The head renders as a navigable cross-reference; the bracketed argument list
-is built by `valSeq` with the head-determined argument constructor, where each
-constant value's display text is its canonical source form (`reprVal`). Under
-the enumeration head the argument nodes are plain display text, so a value such
-as a boolean or an integer carries no class reference; under any other dotted
-head they stay cross-references. -/
+/-- PARTIAL DOMAIN (okLit), maximally destructive off-domain: while every argument is on the modeled value domain the gold rendering is used; as soon as ANY argument is off it (a negative integer, or a string that is not "simple") the brackets and every argument node are DROPPED and only the head cross-reference is emitted. -/
 def implementation_literalTypeNodes
     (head : List Char) (values : List LitVal) : List DocNode :=
-  let inner := valSeq (argNodeCtor head) reprVal values
-  wrap head inner
+  if values.all okLit then
+    wrap head (valSeq (argNodeCtor head) reprVal values)
+  else
+    [DocNode.xref head]
 -- impl-end
 
 -- proof-start
@@ -246,6 +243,7 @@
         (implementation_literalTypeNodes head values) := by
   intro head values
   unfold problem_spec_literalTypeNodes implementation_literalTypeNodes expandLiteral
-  intro _ _
-  rfl
+  intro _ h2
+  simp [h2]
+#print axioms correct_literalTypeNodes
 -- proof-end
```

Attack 8 — `atk_8_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -227,16 +227,10 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The head renders as a navigable cross-reference; the bracketed argument list
-is built by `valSeq` with the head-determined argument constructor, where each
-constant value's display text is its canonical source form (`reprVal`). Under
-the enumeration head the argument nodes are plain display text, so a value such
-as a boolean or an integer carries no class reference; under any other dotted
-head they stay cross-references. -/
+/-- UNGROUNDED-ORACLE ECHO: the implementation is literally the spec deep model, carrying no independent content. -/
 def implementation_literalTypeNodes
     (head : List Char) (values : List LitVal) : List DocNode :=
-  let inner := valSeq (argNodeCtor head) reprVal values
-  wrap head inner
+  expandLiteral head values
 -- impl-end
 
 -- proof-start
@@ -248,4 +242,5 @@
   unfold problem_spec_literalTypeNodes implementation_literalTypeNodes expandLiteral
   intro _ _
   rfl
+#print axioms correct_literalTypeNodes
 -- proof-end
```

Attack 9 — `atk_9_restructured.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -227,19 +227,36 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The head renders as a navigable cross-reference; the bracketed argument list
-is built by `valSeq` with the head-determined argument constructor, where each
-constant value's display text is its canonical source form (`reprVal`). Under
-the enumeration head the argument nodes are plain display text, so a value such
-as a boolean or an integer carries no class reference; under any other dotted
-head they stay cross-references. -/
+/-- RESTRUCTURED control flow: instead of `valSeq`'s front recursion the inner
+sequence is built by a "first, then (separator, value)" recursion, the argument
+constructor is re-derived from the head at every step, and the zero-argument
+region is spelled out at the call site. -/
+def tailNodes (mk : List Char → DocNode) : List LitVal → List DocNode
+  | []      => []
+  | v :: vs => DocNode.punct ", ".toList :: mk (reprVal v) :: tailNodes mk vs
+
+def innerFrom (head : List Char) : List LitVal → List DocNode
+  | []      => [DocNode.punct "(".toList, DocNode.punct ")".toList]
+  | v :: vs => argNodeCtor head (reprVal v) :: tailNodes (argNodeCtor head) vs
+
 def implementation_literalTypeNodes
     (head : List Char) (values : List LitVal) : List DocNode :=
-  let inner := valSeq (argNodeCtor head) reprVal values
-  wrap head inner
+  DocNode.xref head :: DocNode.punct "[".toList
+    :: (innerFrom head values ++ [DocNode.punct "]".toList])
 -- impl-end
 
 -- proof-start
+theorem inner_eq (head : List Char) : ∀ (v : LitVal) (vs : List LitVal),
+    innerFrom head (v :: vs) = valSeq (argNodeCtor head) reprVal (v :: vs)
+  | _, []      => rfl
+  | _, w :: ws => by
+      show argNodeCtor head (reprVal _) :: DocNode.punct ", ".toList
+             :: (argNodeCtor head (reprVal w) :: tailNodes (argNodeCtor head) ws)
+         = argNodeCtor head (reprVal _) :: DocNode.punct ", ".toList
+             :: valSeq (argNodeCtor head) reprVal (w :: ws)
+      rw [← inner_eq head w ws]
+      rfl
+
 theorem correct_literalTypeNodes :
     ∀ (head : List Char) (values : List LitVal),
       problem_spec_literalTypeNodes head values
@@ -247,5 +264,13 @@
   intro head values
   unfold problem_spec_literalTypeNodes implementation_literalTypeNodes expandLiteral
   intro _ _
-  rfl
+  cases values with
+  | nil => rfl
+  | cons v vs =>
+      show DocNode.xref head :: DocNode.punct "[".toList
+             :: (innerFrom head (v :: vs) ++ [DocNode.punct "]".toList])
+         = wrap head (valSeq (argNodeCtor head) reprVal (v :: vs))
+      unfold wrap
+      rw [inner_eq head v vs]
+#print axioms correct_literalTypeNodes
 -- proof-end
```

Attack 10 — `atk_10_firstonly.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -227,16 +227,21 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The head renders as a navigable cross-reference; the bracketed argument list
-is built by `valSeq` with the head-determined argument constructor, where each
-constant value's display text is its canonical source form (`reprVal`). Under
-the enumeration head the argument nodes are plain display text, so a value such
-as a boolean or an integer carries no class reference; under any other dotted
-head they stay cross-references. -/
+/-- CONTROL-FLOW EFFECT: the head-selected constructor is applied only to the
+FIRST argument; every later argument keeps the cross-reference path (the shape
+you get by breaking out of hunk 2's wrapping loop after one iteration). -/
+def restXref : List LitVal → List DocNode
+  | []      => [DocNode.punct "(".toList, DocNode.punct ")".toList]
+  | [v]     => [DocNode.xref (reprVal v)]
+  | v :: vs => DocNode.xref (reprVal v) :: DocNode.punct ", ".toList :: restXref vs
+
 def implementation_literalTypeNodes
     (head : List Char) (values : List LitVal) : List DocNode :=
-  let inner := valSeq (argNodeCtor head) reprVal values
-  wrap head inner
+  match values with
+  | []      => wrap head (valSeq (argNodeCtor head) reprVal [])
+  | [v]     => wrap head [argNodeCtor head (reprVal v)]
+  | v :: vs => wrap head (argNodeCtor head (reprVal v) :: DocNode.punct ", ".toList
+                           :: restXref vs)
 -- impl-end
 
 -- proof-start
@@ -248,4 +253,5 @@
   unfold problem_spec_literalTypeNodes implementation_literalTypeNodes expandLiteral
   intro _ _
   rfl
+#print axioms correct_literalTypeNodes
 -- proof-end
```

Attack 11 — `atk_11_headtext.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -227,16 +227,11 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The head renders as a navigable cross-reference; the bracketed argument list
-is built by `valSeq` with the head-determined argument constructor, where each
-constant value's display text is its canonical source form (`reprVal`). Under
-the enumeration head the argument nodes are plain display text, so a value such
-as a boolean or an integer carries no class reference; under any other dotted
-head they stay cross-references. -/
+/-- The head is emitted as PLAIN TEXT rather than a navigable cross-reference; arguments correct. -/
 def implementation_literalTypeNodes
     (head : List Char) (values : List LitVal) : List DocNode :=
-  let inner := valSeq (argNodeCtor head) reprVal values
-  wrap head inner
+  DocNode.text head :: DocNode.punct "[".toList
+    :: (valSeq (argNodeCtor head) reprVal values ++ [DocNode.punct "]".toList])
 -- impl-end
 
 -- proof-start
@@ -248,4 +243,5 @@
   unfold problem_spec_literalTypeNodes implementation_literalTypeNodes expandLiteral
   intro _ _
   rfl
+#print axioms correct_literalTypeNodes
 -- proof-end
```

Attack 12 — `atk_12_emptyparen_text.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -227,16 +227,12 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The head renders as a navigable cross-reference; the bracketed argument list
-is built by `valSeq` with the head-determined argument constructor, where each
-constant value's display text is its canonical source form (`reprVal`). Under
-the enumeration head the argument nodes are plain display text, so a value such
-as a boolean or an integer carries no class reference; under any other dotted
-head they stay cross-references. -/
+/-- BOUNDARY node-class: the zero-argument spelling`s parenthesis pair is emitted as plain display TEXT rather than structural punctuation (everything else gold). -/
 def implementation_literalTypeNodes
     (head : List Char) (values : List LitVal) : List DocNode :=
-  let inner := valSeq (argNodeCtor head) reprVal values
-  wrap head inner
+  if values.isEmpty then
+    wrap head [DocNode.text "(".toList, DocNode.text ")".toList]
+  else wrap head (valSeq (argNodeCtor head) reprVal values)
 -- impl-end
 
 -- proof-start
@@ -247,5 +243,8 @@
   intro head values
   unfold problem_spec_literalTypeNodes implementation_literalTypeNodes expandLiteral
   intro _ _
-  rfl
+  cases values with
+  | nil => rfl
+  | cons v vs => rfl
+#print axioms correct_literalTypeNodes
 -- proof-end
```

Attack 13 — `atk_13_oklit_barestr.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -227,16 +227,20 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The head renders as a navigable cross-reference; the bracketed argument list
-is built by `valSeq` with the head-determined argument constructor, where each
-constant value's display text is its canonical source form (`reprVal`). Under
-the enumeration head the argument nodes are plain display text, so a value such
-as a boolean or an integer carries no class reference; under any other dotted
-head they stay cross-references. -/
+/-- PARTIAL DOMAIN (okLit, string leg): the canonical source form is used only
+while every argument is on the `okLit` domain; off it, string arguments are
+rendered BARE — the prepatch `nodes.Text(node.value)` reading, with no
+delimiters. -/
+def bareStr : LitVal → List Char
+  | .str s => s
+  | v      => reprVal v
+
 def implementation_literalTypeNodes
     (head : List Char) (values : List LitVal) : List DocNode :=
-  let inner := valSeq (argNodeCtor head) reprVal values
-  wrap head inner
+  if values.all okLit then
+    wrap head (valSeq (argNodeCtor head) reprVal values)
+  else
+    wrap head (valSeq (argNodeCtor head) bareStr values)
 -- impl-end
 
 -- proof-start
@@ -246,6 +250,7 @@
         (implementation_literalTypeNodes head values) := by
   intro head values
   unfold problem_spec_literalTypeNodes implementation_literalTypeNodes expandLiteral
-  intro _ _
-  rfl
+  intro _ h2
+  simp [h2]
+#print axioms correct_literalTypeNodes
 -- proof-end
```

Attack 14 — `atk_14_sepwrong.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -227,16 +227,16 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The head renders as a navigable cross-reference; the bracketed argument list
-is built by `valSeq` with the head-determined argument constructor, where each
-constant value's display text is its canonical source form (`reprVal`). Under
-the enumeration head the argument nodes are plain display text, so a value such
-as a boolean or an integer carries no class reference; under any other dotted
-head they stay cross-references. -/
+/-- I-leg: the argument separator is a bare comma `","` rather than the
+comma-plus-space `", "` the renderer emits. -/
+def valSeqTight (mk : List Char → DocNode) : List LitVal → List DocNode
+  | []      => [DocNode.punct "(".toList, DocNode.punct ")".toList]
+  | [v]     => [mk (reprVal v)]
+  | v :: vs => mk (reprVal v) :: DocNode.punct ",".toList :: valSeqTight mk vs
+
 def implementation_literalTypeNodes
     (head : List Char) (values : List LitVal) : List DocNode :=
-  let inner := valSeq (argNodeCtor head) reprVal values
-  wrap head inner
+  wrap head (valSeqTight (argNodeCtor head) values)
 -- impl-end
 
 -- proof-start
@@ -248,4 +248,5 @@
   unfold problem_spec_literalTypeNodes implementation_literalTypeNodes expandLiteral
   intro _ _
   rfl
+#print axioms correct_literalTypeNodes
 -- proof-end
```

Attack 15 — `atk_15_okhead_text.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -227,16 +227,13 @@
 -- post-conditions-end
 
 -- impl-start
-/-- The head renders as a navigable cross-reference; the bracketed argument list
-is built by `valSeq` with the head-determined argument constructor, where each
-constant value's display text is its canonical source form (`reprVal`). Under
-the enumeration head the argument nodes are plain display text, so a value such
-as a boolean or an integer carries no class reference; under any other dotted
-head they stay cross-references. -/
+/-- PARTIAL DOMAIN (okHead), subtle off-domain deviation: while the head is a dotted ASCII Python name the gold rendering is used; for any other head string the arguments are forced to PLAIN TEXT (so a non-ASCII-named container`s constant arguments silently lose their cross-references). -/
 def implementation_literalTypeNodes
     (head : List Char) (values : List LitVal) : List DocNode :=
-  let inner := valSeq (argNodeCtor head) reprVal values
-  wrap head inner
+  if okHead head then
+    wrap head (valSeq (argNodeCtor head) reprVal values)
+  else
+    wrap head (valSeq DocNode.text reprVal values)
 -- impl-end
 
 -- proof-start
@@ -246,6 +243,7 @@
         (implementation_literalTypeNodes head values) := by
   intro head values
   unfold problem_spec_literalTypeNodes implementation_literalTypeNodes expandLiteral
-  intro _ _
-  rfl
+  intro h1 _
+  simp [h1]
+#print axioms correct_literalTypeNodes
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -248,4 +248,5 @@
   unfold problem_spec_literalTypeNodes implementation_literalTypeNodes expandLiteral
   intro _ _
   rfl
+#print axioms correct_literalTypeNodes
 -- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) on sphinx-doc__sphinx-9602 (Lean). VERDICT: SOUND. 15 same-spec attacks + positive control + a non-vacuity probe, all machine-checked; 6 verifying attacks had faithful patches materialized and RUN through run_resolve.

HEADLINE: the break recorded by the PRIOR G-EQ pass IS REPAIRED, and I re-encoded it to prove that mechanically rather than take the record's word. The prior break was atk_6_empty_boundary: the old spec carried a THIRD hypothesis `values ≠ []`, which freed the zero-argument spelling `Tuple[()]` — a reachable annotation asserted child-by-child by the graded P2P row tests/test_domain_py.py::test_parse_annotation. The current Solution.lean (sha256 7710300753046...) has (a) DROPPED that hypothesis — the postcondition is now exactly `okHead head = true → values.all okLit = true → result = expandLiteral head values`, two hypotheses only — and (b) extended the deep model so `valSeq`'s empty arm emits `[punct "(", punct ")"]`, which is what the real renderer emits for `head[()]`. Both halves of the repair were needed (dropping the hypothesis alone would have made the gold impl itself fail) and both are present.

SAME-SPEC: swebench_unified.markers.same_spec(gold, attack, lean) == True for all 15 attacks + pos_control + probe_nonvacuity (axioms/pure/pre/post byte-identical; only impl+proof edited).

POSITIVE CONTROL: pos_control.lean (= bundle Solution.lean + `#print axioms`) -> `bash scripts/lean_verify.sh <path>` exit 0, "does not depend on any axioms". The verifier is live, so the exit-1s below are real refutations.

PREPATCH REPRODUCED: True. atk_1_prepatch.lean routes the arguments through DocNode.xref for every head (the pre-fix path) -> exit 1, and the residual goal is substantive: `wrap head (valSeq DocNode.xref reprVal values) = wrap head (valSeq (argNodeCtor head) reprVal values)`. Rejected on the merits, not by a weak tactic.

NON-VACUITY PROBE (probe_nonvacuity.lean, exit 0, no axioms): `by decide` witnesses that okHead holds for Literal / typing.Literal / List / Tuple / Callable / Optional; isLitHead true for the two enumeration heads and false for List; okLit holds for the F2P value lists; okHead false for "True" and ""; okLit false for [int (-1)] and [str "a'b"]. Critically it also proves `expandLiteral "Tuple".toList [] = [xref Tuple, punct [, punct (, punct ), punct ]]` — i.e. the empty-argument case is now genuinely PINNED by the frozen postcondition, exactly the 5-node sequence tests/test_domain_py.py:297-302 asserts. That is the prior break's hole, closed and checked.

COMMAND for every attack: `bash scripts/lean_verify.sh <name>.lean`, then `#print axioms correct_literalTypeNodes` (appended in-file). Run concurrently, 4 background jobs at a time.

### REJECTED BY THE SPEC (exit 1, sorryAx — 9)
1 atk_1_prepatch          exit 1  prepatch: arguments always xref (see above). 2 atk_2_headblind         exit 1  HEAD-BLIND: arguments always plain text; goal left `valSeq DocNode.text ... = valSeq (argNodeCtor head) ...`. This was a counterexample against an EARLIER head-as-precondition spec; the current head-in-postcondition spec kills it. 3 atk_3_toobroad          exit 1  head selection too broad (any head ENDING in "Literal": MyLiteral, _Literal). 4 atk_4_toonarrow         exit 1  head selection too narrow (bare `Literal` only; typing.Literal regresses). 5 atk_5_empty_abbrev      exit 1  *** THE PRIOR PASS'S BREAK, RE-ENCODED: `if values.isEmpty then [DocNode.xref head] else <gold>`. Under the OLD spec this closed and its patch failed P2P.

Under the CURRENT spec it is REJECTED, residual goal `if [].isEmpty = true then [DocNode.xref head] else wrap head (valSeq ... []) = wrap head (valSeq ... [])` in `case nil`. The repair is confirmed mechanically. *** 6 atk_10_firstonly        exit 1  control-flow effect: head-selected ctor applied only to the FIRST argument, later arguments stay xref. 7 atk_11_headtext         exit 1  head emitted as plain text instead of a cross-reference. 8 atk_12_emptyparen_text  exit 1  boundary node-CLASS: the zero-argument paren pair emitted as Text rather than punctuation. Rejected in `case nil` — the empty arm pins the class, not just the arity. 9 atk_14_sepwrong         exit 1  I-leg: separator `","` instead of `", "`.

### Verified with clean axioms -> FAITHFUL patch materialized and resolved (6)
Clean = "does not depend on any axioms" or only `propext` (in backends/lean.py STANDARD_AXIOMS = propext, Classical.choice, Quot.sound). Every patch = the gold patch's three hunks VERBATIM plus the attack's modeled deviation transliterated through mapping.md §2 (str<->List Char, ast.Constant<->LitVal, Text/pending_xref/desc_sig_punctuation carriers).

  atk_8_oracle_echo      exit 0  axioms NONE     -> resolved=TRUE  completed=True applied=True F2P 1/1, P2P 45/45.  impl := expandLiteral; patch IS the gold patch. Correct echo, not a weakness.
  atk_9_restructured     exit 0  axioms NONE     -> resolved=TRUE  completed=True applied=True F2P 1/1, P2P 45/45.  restructured recursion (first-then-(sep,value)), extensionally equal incl. the empty arm.
  atk_6_okhead_drop      exit 0  axioms propext  -> resolved=TRUE  completed=True applied=True F2P 1/1, P2P 45/45.  partial domain on okHead, MAXIMALLY destructive off-domain (brackets + whole argument list dropped, head as plain Text).
  atk_15_okhead_text     exit 0  axioms propext  -> resolved=TRUE  completed=True applied=True F2P 1/1, P2P 45/45.  partial domain on okHead, subtle (off-domain forces arguments to plain text).
  atk_7_oklit_drop       exit 0  axioms propext  -> resolved=TRUE  completed=True applied=True F2P 1/1, P2P 45/45.  partial domain on okLit, MAXIMALLY destructive off-domain (brackets + every argument node dropped).
  atk_13_oklit_barestr   exit 0  axioms propext  -> resolved=TRUE  completed=True applied=True F2P 1/1, P2P 45/45.  partial domain on okLit string leg (off-domain strings rendered BARE, the prepatch reading).

All 6 reported completed=True and patch_successfully_applied=True, so no verdict rests on an inconclusive oracle run and _patch_not_a_faithful_refinement does not apply anywhere. NO attack with a closing clean-axiom proof has a non-resolving patch => no verify⇏ correct witness.

PATCH-FIDELITY PRE-CHECK (so the resolves are meaningful, not vacuous): before spending oracle runs I diffed each patched tree's real `_parse_annotation` node fingerprints (class, astext) against the gold patched tree. atk_8/atk_9 are byte-equivalent in behaviour on all 22 probes (correct echoes, as intended). atk_6/atk_15 deviate exactly on off-okHead heads ('Ünicodé[True]', 'True[0]') and nowhere else. atk_7/atk_13 deviate exactly on off-okLit constants (Literal["a'b"], Literal['a\\b'], Literal['a\nb'], Literal['tab\there'], List['a\\b']) and nowhere else. So each deviation is LIVE in the shipped tree and the resolve is a real test of it — the P2P suite simply never reaches those regions.

WHY THE TWO SURVIVING PRECONDITIONS ARE SAFE (measured, not assumed). I enumerated every subscripted annotation in the graded test file by AST (static_reach.py): heads used are exactly {Callable, List, Optional, Tuple} — ALL satisfy okHead, so the okHead off-domain region is unreachable by the graded suite. Only two graded rows land in the modeled all-constant-arguments shape at all: `List[None]` (the preserved argument-as-xref facet) and `Tuple[()]` (the zero-argument spelling) — and both are now PINNED by the postcondition, which is why atk_5 and atk_12 die. For okLit: a negative integer is an ast.UnaryOp, not an ast.Constant, so `Literal[-1]` is not even in the modeled LitVal domain (the real function throws SyntaxError and returns a single node — confirmed on the patched tree); non-simple strings never appear in a graded annotation. So both remaining hypotheses restrict only genuinely-unobserved behaviour, in contrast to the removed `values ≠ []`, which did not.

### refinement.md AUDIT (legs; the A-legs re-validated independently)
Leg tags: rows 1 (R), 1b (I — changed control-flow op, modeled on BOTH branches), 2 (R), 2b (I), 3 (I + A-reference), 4 (I + A-reference), 5 (R). Every leg is R / A-reference / I; NO kind-3 (inexpressible-changed-op) row. The axioms region declares no consumed axiom and meta.json has axioms: [], opaque_callees: [], conf_skip: false — consistent with the file's own claim that the changed callee is modeled deeply rather than hidden behind an axiom.
I re-validated all three A-legs with my OWN harness (aleg.py), not the bundle's checkers:
 * §3.1 reprVal == builtin `repr` on the okLit domain: 40,022 on-domain constants (boundary + fuzz, incl. 10**40, empty/spaced/punctuation strings, 300-char) — 0 mismatches. `repr` is genuinely UNCHANGED (the patch adds only the CALL), so G-AX validating at base_commit is legitimate.
 * §3.2 head node == `type_to_xref` carrier, run at BASE_COMMIT (unchanged callee): 8 heads, every one a pending_xref with astext == reftarget == head. Sound.
 * §3.3 expandLiteral == the CHANGED `_parse_annotation`: independent shadow hand-transcribed from Solution.lean, diffed node-for-node (class + text) against the real patched tree over 60,900 in-domain annotations — 38 heads straddling the guard (both enumeration names, containers, dotted paths, near-misses literal/LITERAL/LiteralX/Literals/MyLiteral/Literal2/_Literal/Literal_/llteral, typing.Literal.X, X.typing.Literal, soft keywords match/case/type/_/print, a 200-char segment) x adversarial value lists INCLUDING THE EMPTY LIST on both sides of the guard — 0 disagreements. Correctly validated with the gold patch applied (base_commit is the wrong oracle for the function under change). Note my sweep deliberately draws `values = []`, which the bundle's own conformance_check.py generator now also yields (its boundary rows include Tuple[], Literal[], typing.Literal[]) — the prior pass's observation that G-CONF never drew the empty list no longer holds.
The model<->patch correspondence therefore holds on its stated domain, and the domain no longer excludes anything the graded suite reads.

ARTIFACTS: atk_*.lean (15), pos_control.lean, probe_nonvacuity.lean, build.py (generator), mkpatch.py (patch materializer), atk_*.diff (6 faithful patches), work_atk_*/ (patched trees), wt_gold/ (base_commit) + wt_patched/ (base+gold patch), probe.py + fidelity.py + fid2.py (node-fingerprint probers), static_reach.py (graded-suite domain reachability), aleg.py (independent A-leg validation), resolve.py + rlog_*.txt (official harness verdicts), <name>.log/.exit (lean_verify output incl. #print axioms).

ADVISORY: no defect found. One optional hardening — refinement.md's Discriminators section still describes the zero-argument spelling as a facet an impl "may abbreviate", phrased as a risk; now that the postcondition pins it (and atk_5/atk_12 confirm), that bullet could be reworded to say it is pinned. Cosmetic only; it does not affect any leg's correctness.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1_prepatch.lean`, `atk_2_headblind.lean`, `atk_3_toobroad.lean`, `atk_4_toonarrow.lean`, `atk_5_empty_abbrev.lean`, `atk_10_firstonly.lean`, `atk_11_headtext.lean`, `atk_12_emptyparen_text.lean`, `atk_14_sepwrong.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_6_okhead_drop.lean`, `atk_7_oklit_drop.lean`, `atk_8_oracle_echo.lean`, `atk_9_restructured.lean`, `atk_13_oklit_barestr.lean`, `atk_15_okhead_text.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 15 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_headblind.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_toobroad.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_toonarrow.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_empty_abbrev.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_okhead_drop.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7_oklit_drop.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9_restructured.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10_firstonly.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_headtext.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_emptyparen_text.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_oklit_barestr.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_14_sepwrong.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15_okhead_text.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -248,4 +248,5 @@
   unfold problem_spec_literalTypeNodes implementation_literalTypeNodes expandLiteral
   intro _ _
   rfl
+#print axioms correct_literalTypeNodes
 -- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) on sphinx-doc__sphinx-9602 (Lean). VERDICT: SOUND. 15 same-spec attacks + positive control + a non-vacuity probe, all machine-checked; 6 verifying attacks had faithful patches materialized and RUN through run_resolve.

HEADLINE: the break recorded by the PRIOR G-EQ pass IS REPAIRED, and I re-encoded it to prove that mechanically rather than take the record's word. The prior break was atk_6_empty_boundary: the old spec carried a THIRD hypothesis `values ≠ []`, which freed the zero-argument spelling `Tuple[()]` — a reachable annotation asserted child-by-child by the graded P2P row tests/test_domain_py.py::test_parse_annotation. The current Solution.lean (sha256 7710300753046...) has (a) DROPPED that hypothesis — the postcondition is now exactly `okHead head = true → values.all okLit = true → result = expandLiteral head values`, two hypotheses only — and (b) extended the deep model so `valSeq`'s empty arm emits `[punct "(", punct ")"]`, which is what the real renderer emits for `head[()]`. Both halves of the repair were needed (dropping the hypothesis alone would have made the gold impl itself fail) and both are present.

SAME-SPEC: swebench_unified.markers.same_spec(gold, attack, lean) == True for all 15 attacks + pos_control + probe_nonvacuity (axioms/pure/pre/post byte-identical; only impl+proof edited).

POSITIVE CONTROL: pos_control.lean (= bundle Solution.lean + `#print axioms`) -> `bash scripts/lean_verify.sh <path>` exit 0, "does not depend on any axioms". The verifier is live, so the exit-1s below are real refutations.

PREPATCH REPRODUCED: True. atk_1_prepatch.lean routes the arguments through DocNode.xref for every head (the pre-fix path) -> exit 1, and the residual goal is substantive: `wrap head (valSeq DocNode.xref reprVal values) = wrap head (valSeq (argNodeCtor head) reprVal values)`. Rejected on the merits, not by a weak tactic.

NON-VACUITY PROBE (probe_nonvacuity.lean, exit 0, no axioms): `by decide` witnesses that okHead holds for Literal / typing.Literal / List / Tuple / Callable / Optional; isLitHead true for the two enumeration heads and false for List; okLit holds for the F2P value lists; okHead false for "True" and ""; okLit false for [int (-1)] and [str "a'b"]. Critically it also proves `expandLiteral "Tuple".toList [] = [xref Tuple, punct [, punct (, punct ), punct ]]` — i.e. the empty-argument case is now genuinely PINNED by the frozen postcondition, exactly the 5-node sequence tests/test_domain_py.py:297-302 asserts. That is the prior break's hole, closed and checked.

COMMAND for every attack: `bash scripts/lean_verify.sh <name>.lean`, then `#print axioms correct_literalTypeNodes` (appended in-file). Run concurrently, 4 background jobs at a time.

### REJECTED BY THE SPEC (exit 1, sorryAx — 9)
1 atk_1_prepatch          exit 1  prepatch: arguments always xref (see above). 2 atk_2_headblind         exit 1  HEAD-BLIND: arguments always plain text; goal left `valSeq DocNode.text ... = valSeq (argNodeCtor head) ...`. This was a counterexample against an EARLIER head-as-precondition spec; the current head-in-postcondition spec kills it. 3 atk_3_toobroad          exit 1  head selection too broad (any head ENDING in "Literal": MyLiteral, _Literal). 4 atk_4_toonarrow         exit 1  head selection too narrow (bare `Literal` only; typing.Literal regresses). 5 atk_5_empty_abbrev      exit 1  *** THE PRIOR PASS'S BREAK, RE-ENCODED: `if values.isEmpty then [DocNode.xref head] else <gold>`. Under the OLD spec this closed and its patch failed P2P.

Under the CURRENT spec it is REJECTED, residual goal `if [].isEmpty = true then [DocNode.xref head] else wrap head (valSeq ... []) = wrap head (valSeq ... [])` in `case nil`. The repair is confirmed mechanically. *** 6 atk_10_firstonly        exit 1  control-flow effect: head-selected ctor applied only to the FIRST argument, later arguments stay xref. 7 atk_11_headtext         exit 1  head emitted as plain text instead of a cross-reference. 8 atk_12_emptyparen_text  exit 1  boundary node-CLASS: the zero-argument paren pair emitted as Text rather than punctuation. Rejected in `case nil` — the empty arm pins the class, not just the arity. 9 atk_14_sepwrong         exit 1  I-leg: separator `","` instead of `", "`.

### Verified with clean axioms -> FAITHFUL patch materialized and resolved (6)
Clean = "does not depend on any axioms" or only `propext` (in backends/lean.py STANDARD_AXIOMS = propext, Classical.choice, Quot.sound). Every patch = the gold patch's three hunks VERBATIM plus the attack's modeled deviation transliterated through mapping.md §2 (str<->List Char, ast.Constant<->LitVal, Text/pending_xref/desc_sig_punctuation carriers).

  atk_8_oracle_echo      exit 0  axioms NONE     -> resolved=TRUE  completed=True applied=True F2P 1/1, P2P 45/45.  impl := expandLiteral; patch IS the gold patch. Correct echo, not a weakness.
  atk_9_restructured     exit 0  axioms NONE     -> resolved=TRUE  completed=True applied=True F2P 1/1, P2P 45/45.  restructured recursion (first-then-(sep,value)), extensionally equal incl. the empty arm.
  atk_6_okhead_drop      exit 0  axioms propext  -> resolved=TRUE  completed=True applied=True F2P 1/1, P2P 45/45.  partial domain on okHead, MAXIMALLY destructive off-domain (brackets + whole argument list dropped, head as plain Text).
  atk_15_okhead_text     exit 0  axioms propext  -> resolved=TRUE  completed=True applied=True F2P 1/1, P2P 45/45.  partial domain on okHead, subtle (off-domain forces arguments to plain text).
  atk_7_oklit_drop       exit 0  axioms propext  -> resolved=TRUE  completed=True applied=True F2P 1/1, P2P 45/45.  partial domain on okLit, MAXIMALLY destructive off-domain (brackets + every argument node dropped).
  atk_13_oklit_barestr   exit 0  axioms propext  -> resolved=TRUE  completed=True applied=True F2P 1/1, P2P 45/45.  partial domain on okLit string leg (off-domain strings rendered BARE, the prepatch reading).

All 6 reported completed=True and patch_successfully_applied=True, so no verdict rests on an inconclusive oracle run and _patch_not_a_faithful_refinement does not apply anywhere. NO attack with a closing clean-axiom proof has a non-resolving patch => no verify⇏ correct witness.

PATCH-FIDELITY PRE-CHECK (so the resolves are meaningful, not vacuous): before spending oracle runs I diffed each patched tree's real `_parse_annotation` node fingerprints (class, astext) against the gold patched tree. atk_8/atk_9 are byte-equivalent in behaviour on all 22 probes (correct echoes, as intended). atk_6/atk_15 deviate exactly on off-okHead heads ('Ünicodé[True]', 'True[0]') and nowhere else. atk_7/atk_13 deviate exactly on off-okLit constants (Literal["a'b"], Literal['a\\b'], Literal['a\nb'], Literal['tab\there'], List['a\\b']) and nowhere else. So each deviation is LIVE in the shipped tree and the resolve is a real test of it — the P2P suite simply never reaches those regions.

WHY THE TWO SURVIVING PRECONDITIONS ARE SAFE (measured, not assumed). I enumerated every subscripted annotation in the graded test file by AST (static_reach.py): heads used are exactly {Callable, List, Optional, Tuple} — ALL satisfy okHead, so the okHead off-domain region is unreachable by the graded suite. Only two graded rows land in the modeled all-constant-arguments shape at all: `List[None]` (the preserved argument-as-xref facet) and `Tuple[()]` (the zero-argument spelling) — and both are now PINNED by the postcondition, which is why atk_5 and atk_12 die. For okLit: a negative integer is an ast.UnaryOp, not an ast.Constant, so `Literal[-1]` is not even in the modeled LitVal domain (the real function throws SyntaxError and returns a single node — confirmed on the patched tree); non-simple strings never appear in a graded annotation. So both remaining hypotheses restrict only genuinely-unobserved behaviour, in contrast to the removed `values ≠ []`, which did not.

### refinement.md AUDIT (legs; the A-legs re-validated independently)
Leg tags: rows 1 (R), 1b (I — changed control-flow op, modeled on BOTH branches), 2 (R), 2b (I), 3 (I + A-reference), 4 (I + A-reference), 5 (R). Every leg is R / A-reference / I; NO kind-3 (inexpressible-changed-op) row. The axioms region declares no consumed axiom and meta.json has axioms: [], opaque_callees: [], conf_skip: false — consistent with the file's own claim that the changed callee is modeled deeply rather than hidden behind an axiom.
I re-validated all three A-legs with my OWN harness (aleg.py), not the bundle's checkers:
 * §3.1 reprVal == builtin `repr` on the okLit domain: 40,022 on-domain constants (boundary + fuzz, incl. 10**40, empty/spaced/punctuation strings, 300-char) — 0 mismatches. `repr` is genuinely UNCHANGED (the patch adds only the CALL), so G-AX validating at base_commit is legitimate.
 * §3.2 head node == `type_to_xref` carrier, run at BASE_COMMIT (unchanged callee): 8 heads, every one a pending_xref with astext == reftarget == head. Sound.
 * §3.3 expandLiteral == the CHANGED `_parse_annotation`: independent shadow hand-transcribed from Solution.lean, diffed node-for-node (class + text) against the real patched tree over 60,900 in-domain annotations — 38 heads straddling the guard (both enumeration names, containers, dotted paths, near-misses literal/LITERAL/LiteralX/Literals/MyLiteral/Literal2/_Literal/Literal_/llteral, typing.Literal.X, X.typing.Literal, soft keywords match/case/type/_/print, a 200-char segment) x adversarial value lists INCLUDING THE EMPTY LIST on both sides of the guard — 0 disagreements. Correctly validated with the gold patch applied (base_commit is the wrong oracle for the function under change). Note my sweep deliberately draws `values = []`, which the bundle's own conformance_check.py generator now also yields (its boundary rows include Tuple[], Literal[], typing.Literal[]) — the prior pass's observation that G-CONF never drew the empty list no longer holds.
The model<->patch correspondence therefore holds on its stated domain, and the domain no longer excludes anything the graded suite reads.

ARTIFACTS: atk_*.lean (15), pos_control.lean, probe_nonvacuity.lean, build.py (generator), mkpatch.py (patch materializer), atk_*.diff (6 faithful patches), work_atk_*/ (patched trees), wt_gold/ (base_commit) + wt_patched/ (base+gold patch), probe.py + fidelity.py + fid2.py (node-fingerprint probers), static_reach.py (graded-suite domain reachability), aleg.py (independent A-leg validation), resolve.py + rlog_*.txt (official harness verdicts), <name>.log/.exit (lean_verify output incl. #print axioms).

ADVISORY: no defect found. One optional hardening — refinement.md's Discriminators section still describes the zero-argument spelling as a facet an impl "may abbreviate", phrased as a risk; now that the postcondition pins it (and atk_5/atk_12 confirm), that bullet could be reworded to say it is pinned. Cosmetic only; it does not affect any leg's correctness.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**ATTACK:** faithfulness-break (spec too strong / drifts from real repo). Result: NO divergence found. Verdict FAITHFUL.

### SETUP (per instructions, reference = base_commit worktree with patch.diff APPLIED):
- Fresh worktree at base_commit 6c38f68dae221e8cfc70c137974b8b88bd3baaab from the upstream repository; `git apply patch.diff` -> clean. Modeled callee = sphinx/domains/python.py::`_parse_annotation` (ast.Subscript branch + top-level rewrite loop).
- Second, separate BASE worktree kept as a sensitivity control.

### HARNESS FIDELITY (guard against transliteration bugs faking/hiding a divergence):
- I hand-transliterated the ENTIRE spec region (headSegments/okHeadSeg/okHead/isHeadStart|TailChar/pyReservedWords/isSimpleStrChar/okLit/reprVal/isLitHead/argNodeCtor/valSeq/wrap/expandLiteral) into Python, then CROSS-VALIDATED it against the real Lean by #eval on 40+ probes (spliced spec region + #eval, exit 0). Lean and my Python model agreed on every probe: okHead accepts 'match'/'type'/`'_'` and rejects ''/'.'/'a.'/'.a'/'a..b'/'while'/'`__peg_parser__`'/'9a'/'a-b'/'Unicode'/'a b'; headSegments ''->[''], 'a..'->['a','',''].
- pyReservedWords == keyword.kwlist exactly (0 missing both directions) plus '`__peg_parser__`'. Confirmed the character-spelled ['w','h','i','l','e'] entry denotes "while" as the docstring claims.

### DIFFERENTIAL EVIDENCE (model vs REAL patched `_parse_annotation`, node-for-node class+text):
- ~1,225 targeted + 29,993 seeded-fuzz in-domain annotations: 0 disagreements.
- EXHAUSTIVE head sweep: all length-1 and length-2 heads over [A-Za-z0-9_.], length-3 over 'aZ9_.', every keyword.kwlist + softkwlist + dir(builtins), plus enumeration near-misses (literal, LITERAL, Literals, Literal_, x.Literal, typing.literal, t.Literal, typing_extensions.Literal, Literal.Literal). 3,602 heads admitted by okHead, 14,408 checks: 0 disagreements. Crucially, every head okHead ADMITS really does parse as a parametrised type (no SyntaxError 1-node fallback) -> the precondition does not over-admit.
- EXHAUSTIVE string-value sweep: every printable-ASCII simple char singly, tripled, and embedded ('a'+c+'b'), plus '...','None','True','0','[]','()','#x','a, b',' ','  ','   ','x'*300: 1,196 checks, 0 disagreements. The blank-string rows are the sharp ones (base's `node.strip()` guard) and the patched repo matches the model.
- INT + ARITY sweep: ints 0..299 and 10^1..10^59; argument counts 0..39 for each of int/str/null/bool: 2,076 checks, 0 disagreements.
- HIGH-VOLUME 3-config fuzz: 59,987 annotations x 3 env configs, 0 disagreements.
Total ~150k in-domain inputs, zero divergence.

ZERO-ARGUMENT SHAPE (the spec's most aggressive claim, and the likeliest over-strengthening): valSeq _ _ [] pins `head[()]` to xref head, '[', '(', ')', ']'. Verified against the REAL patched repo for Tuple[()], Literal[()], and 3,602 admitted heads. mapping.md's reasoning is correct: the pair is desc_sig_punctuation, so hunk 2's Text-only rewrite cannot reach it, making the region head-independent. Spec is exact here, not too strong.

ENV-CONFIG DEPENDENCE (probed as a possible drift): under python_use_unqualified_type_names=True my astext() fingerprint showed 12/12 mismatches ('LiteralLiteral'). I ran this to ground and it is MY fingerprint's artifact, NOT a spec defect: with that config type_to_xref emits two pending_xref_condition children, so astext() concatenates both spellings. mapping.md §2 explicitly names the reference target as the observed field; on the reftarget fingerprint all 4 config variants (cfg False/True x empty/populated ref_context) agree 0-bad, including in the 60k fuzz. Not reported as a finding.

**F2P/P2P ANCHOR:** replicated the test_patch assertions verbatim. For Literal[True, False], typing.Literal[0, 1, 'abc'] (F2P) and List[None], Tuple[()] (graded P2P), model == real == upstream expected node list, all True. (pytest itself errors on an unrelated sphinxcontrib extension-loading fixture problem in this env, so I asserted the node lists directly rather than record an environment fault as a spec verdict.)

SENSITIVITY CONTROL (proves the harness can actually see a divergence): the SAME harness against the BASE worktree yields 860/1,225 disagreements -- constants rendered as xref instead of text and without repr() delimiters. Per the briefing this base delta is exactly the patch's intended change and is NOT a faithfulness defect; I record it only to show a non-vacuous oracle.

**ARTIFACT CHECKS:** scripts/lean_verify.sh Solution.lean -> exit 0; `#print axioms correct_literalTypeNodes` -> "does not depend on any axioms" (no sorryAx, proof is real). Retained control Solution_prepatch.lean -> exit 1, failing precisely on `DocNode.xref (reprVal v) = DocNode.text (reprVal v)`, i.e. the spec genuinely rejects the pre-change reading and is not vacuous. markers.same_spec(Solution, Solution_prepatch) = True; axioms/pure/post-conditions/spec_view region hashes all identical, only impl+proof differ -- spec region byte-identical as required.
- Bundle's own gates reproduced independently: G-CONF 100,023 inputs 0 disagreements (exit 0); G-AX reprVal==repr on 18 boundary + 20,000 fuzz constants, type_to_xref carrier faithful (exit 0).

**WHY THE SPEC IS NOT TOO STRONG:** the postcondition is a bare implication gated on okHead and values.all okLit, and on that entire domain it equals real patched behavior on every input tested. Its strong-looking clauses are all matched by reality: the head-dependent argument class is a real observable on both branches (hunk 2's false leg is load-bearing for List[None]), and the []-case is a real reachable shape. Narrowings (int >= 0, simple strings only) restrict the domain rather than over-constrain the callee, and both are honestly declared as preconditions with mapping.md justification. No input found where the modeled function disagrees with the real callee; therefore no diverging_input can be cited and I do not claim a defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

MEASURED, not inherited. No relaxation applies to THIS bundle: lean/meta.json has NO `relaxed_leakage` key and there is no lean/RELAXED_LEAKAGE.md. The RELAXED_LEAKAGE.md in this instance tree belongs to the SIBLING nagini/ bundle (nagini/meta.json relaxed_leakage=true, G-LEAK status 'relaxed' for its 'B1 quoting' facet). Per gates/leak.py the relaxed branch keys off the bundle's OWN root, so lean/ is judged on ordinary rule-6 grounds; I did that. (That sibling file does not address or instruct this panel -- it argues a mismatch and stops -- so no reviewer-directed finding against it; it is out of scope regardless.)

**WHAT I RAN.** (1) same_spec: markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) == True -- spec region byte-identical across twins. (2) Mechanical screen: leakage.screen(src, LeanBackend, patch, problem_statement) -> passed=True, hard_failures=[], warnings=[]. (3) Gold verifies: scripts/lean_verify.sh Solution.lean exit 0; appended `#print axioms correct_literalTypeNodes` -> "does not depend on any axioms" (no sorryAx, proof is real). (4) Read the exact consumer artifact via markers.spec_view (impl+proof elided) rather than the raw file.

SPEC-VIEW SUBSTRING PROBES (all False in the rendered spec view): '`_parse_annotation`', 'unparse' (the only distinctive patched symbol per leakage.`_patch_changed_symbols`), 'python.py', 'domains', 'sphinx'/'Sphinx', 'repr(', 'type_to_xref', 'pending_xref', 'desc_sig', 'ast.', 'Subscript', 'isinstance'. Narration regex `_NARRATION_RE` over the spec view returns the EMPTY set. Patched file is sphinx/domains/python.py (leakage.`_patch_changed_files`) and appears nowhere. The two lexical hits are innocuous English: 'nodes.' ends a prose sentence, 'Constant' begins one ('Constant strings outside this domain...').

STALE PRIOR FINDING, NOW REPAIRED -- the reason I did not simply echo the record. meta.json carries gates.G-PANEL-3 = LEAKAGE/fail, but it is stamped against Solution.lean sha256 f384d6f7b986..., while the current file is 771030075304.... That finding cited docstring line 6, then reading 'as `_parse_annotation` does for a subscripted type in Sphinx's Python domain' -- genuine edit-localization (module + exact private function, neither in problem_statement). `git log -p` confirms commit fd0d1cb07 rewrote that line to the behavior-only 'as a documentation renderer does for a subscripted type.' I re-probed the current text: the function name and module are gone. The recorded LEAKAGE no longer describes the artifact.

THE LIVE FACET I ADJUDICATED (string quoting, gold hunk 1's repr). This is the one facet not visible in problem_statement: PS uses ONLY boolean Literals (Literal[True]/[False], where repr==str, quoting invisible); "'abc'" appears only in the hidden F2P test_parse_annotation_Literal; hints_text is empty. I confirmed the pin is LOAD-BEARING rather than narration: substituting the r2 rival (string shown as bare chars, `| .str s => s`) into the impl against the FROZEN spec fails -- lean_verify exit 1, `rfl` reports `valSeq ... render` not defeq to `valSeq ... reprVal`. So the clause cannot be stripped without admitting an impl that fails the F2P assertion; removing it would break verify=>correct.

I judge it NO-LEAKAGE because it is stated as TARGET OUTPUT BEHAVIOR under a source-fidelity principle ('the argument exactly as it stands in the annotation', 'its quoted literal as written') and never as the edit: no patched symbol, no `repr`, no diff line, no mechanism. Rule 6 forbids naming the edit/diagnosis, not specifying behavior precisely; PS's own 'Literal[True] should be present in the type annotation' anchors the render-what-is-written framing. Sibling velvet passed this gate on the same facet with strictly MORE explicit wording ('the surrounding quotes ARE part of the displayed text').

OUT-OF-SCOPE OBSERVATIONS (not leakage, flagged for the freshness/soundness lanes): several gate stamps are pinned to the superseded hash f384d6f7 -- G-AX, G-CONF, G-EQ(fail/BROKEN), G-PANEL-1(BROKEN), G-PANEL-2. That matters because the repair commit materially changed the spec: `valSeq`'s empty arm went from `[]` to `[punct "(", punct ")"]` and the postcondition dropped its `values != []` hypothesis. G-CONF's 100020-input stamp (and G-AX) therefore predate the zero-argument/empty-tuple behavior they are cited as validating, and its own docstring still says it fuzzes a 'non-empty list' of values. G-VERIFY/G-DIFF/G-GOLD/G-MUT/G-PBT/G-LEAK are current (771030075304). mapping.md and refinement.md name repo symbols and base_commit freely, but they are audit docs outside markers.spec_view, so they are not part of the consumer view this gate screens.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
