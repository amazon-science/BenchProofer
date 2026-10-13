# P2 adversarial audit — scikit-learn__scikit-learn-14983

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pc2_shape.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The strongest candidate was atk_7 (atk_7.lean), the partial-domain exploit of the postcondition's OWN antecedent `argNames.all (fun k => onDomain (resolveVal ...)) = true ->`: it returns `reprString ...` on the guarded (7-bit) domain and the literal `"<<GEQ-ATTACK-OFF-DOMAIN>>"` off it. It VERIFIES (lean_verify exit 0) with clean axioms (propext only). Its faithful refined patch (mirroring the guard onto Python: `type(value) is str` => all(ord(c)<128), on-carrier only, deferring to the real rendering off-carrier) was materialized and RUN: run_resolve => completed=True, RESOLVED=TRUE, attempts=1, flaky=False, F2P 2/2, P2P 105/105. So the guard's slack is NOT test-observable at this instance (no F2P/P2P test passes a non-ASCII estimator param; test_split.py contains 0 non-ASCII bytes), and atk_7 is a correct-on-the-tested-domain echo rather than a verify=>correct break.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -185,14 +185,11 @@
     (attrs extra : List (String × PyVal)) (hasExtra : Bool) : String := Id.run do
   let mut parts : List String := []
   for key in argNames do
-    let v0 := lookupVal attrs key
-    let mut v := v0
-    if v0 == PyVal.null && hasExtra then
-      v := lookupVal extra key
+    -- PREPATCH: no fallback to the auxiliary parameter map.
+    let v := lookupVal attrs key
     parts := parts ++ [elideEntry (key ++ "=" ++ pyRepr v)]
   return className ++ "(" ++ layoutEntries className.length parts ++ ")"
 -- impl-end
-
 
 -- proof-start
 theorem correct_reprString :
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -184,15 +184,17 @@
 def implementation_reprString (className : String) (argNames : List String)
     (attrs extra : List (String × PyVal)) (hasExtra : Bool) : String := Id.run do
   let mut parts : List String := []
+  let mut isFirst : Bool := true
   for key in argNames do
     let v0 := lookupVal attrs key
     let mut v := v0
-    if v0 == PyVal.null && hasExtra then
+    -- PARTIAL DOMAIN: the auxiliary-map fallback only fires for the first key.
+    if v0 == PyVal.null && hasExtra && isFirst then
       v := lookupVal extra key
+    isFirst := false
     parts := parts ++ [elideEntry (key ++ "=" ++ pyRepr v)]
   return className ++ "(" ++ layoutEntries className.length parts ++ ")"
 -- impl-end
-
 
 -- proof-start
 theorem correct_reprString :
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -181,6 +181,10 @@
 -- post-conditions-end
 
 -- impl-start
+def elideEntryOffByOne (e : String) : String :=
+  -- BOUNDARY: >= 500 instead of > 500.
+  if e.length ≥ 500 then e.take 300 ++ "..." ++ e.drop (e.length - 100) else e
+
 def implementation_reprString (className : String) (argNames : List String)
     (attrs extra : List (String × PyVal)) (hasExtra : Bool) : String := Id.run do
   let mut parts : List String := []
@@ -189,10 +193,9 @@
     let mut v := v0
     if v0 == PyVal.null && hasExtra then
       v := lookupVal extra key
-    parts := parts ++ [elideEntry (key ++ "=" ++ pyRepr v)]
+    parts := parts ++ [elideEntryOffByOne (key ++ "=" ++ pyRepr v)]
   return className ++ "(" ++ layoutEntries className.length parts ++ ")"
 -- impl-end
-
 
 -- proof-start
 theorem correct_reprString :
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -181,6 +181,18 @@
 -- post-conditions-end
 
 -- impl-start
+def placeEntryOffByOne (offset : Nat) : String × Nat × Bool → String → String × Nat × Bool
+  | (acc, ln, true),  e => (acc ++ e, ln + e.length, false)
+  | (acc, ln, false), e =>
+      -- BOUNDARY: > 75 instead of >= 75.
+      if ln + e.length > 75 || e.toList.contains '\n' then
+        (acc ++ lineSep offset ++ e, (lineSep offset).length + e.length, false)
+      else
+        (acc ++ ", " ++ e, ln + 2 + e.length, false)
+
+def layoutEntriesOffByOne (offset : Nat) (es : List String) : String :=
+  rstripLines (es.foldl (placeEntryOffByOne offset) ("", offset, true)).1
+
 def implementation_reprString (className : String) (argNames : List String)
     (attrs extra : List (String × PyVal)) (hasExtra : Bool) : String := Id.run do
   let mut parts : List String := []
@@ -190,9 +202,8 @@
     if v0 == PyVal.null && hasExtra then
       v := lookupVal extra key
     parts := parts ++ [elideEntry (key ++ "=" ++ pyRepr v)]
-  return className ++ "(" ++ layoutEntries className.length parts ++ ")"
+  return className ++ "(" ++ layoutEntriesOffByOne className.length parts ++ ")"
 -- impl-end
-
 
 -- proof-start
 theorem correct_reprString :
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -181,6 +181,19 @@
 -- post-conditions-end
 
 -- impl-start
+def placeEntryBadRestart (offset : Nat) : String × Nat × Bool → String → String × Nat × Bool
+  | (acc, ln, true),  e => (acc ++ e, ln + e.length, false)
+  | (acc, ln, false), e =>
+      if ln + e.length ≥ 75 || e.toList.contains '\n' then
+        -- CONTROL-FLOW EFFECT: running width restarts from the class-name
+        -- offset instead of the separator's length.
+        (acc ++ lineSep offset ++ e, offset + e.length, false)
+      else
+        (acc ++ ", " ++ e, ln + 2 + e.length, false)
+
+def layoutEntriesBadRestart (offset : Nat) (es : List String) : String :=
+  rstripLines (es.foldl (placeEntryBadRestart offset) ("", offset, true)).1
+
 def implementation_reprString (className : String) (argNames : List String)
     (attrs extra : List (String × PyVal)) (hasExtra : Bool) : String := Id.run do
   let mut parts : List String := []
@@ -190,9 +203,8 @@
     if v0 == PyVal.null && hasExtra then
       v := lookupVal extra key
     parts := parts ++ [elideEntry (key ++ "=" ++ pyRepr v)]
-  return className ++ "(" ++ layoutEntries className.length parts ++ ")"
+  return className ++ "(" ++ layoutEntriesBadRestart className.length parts ++ ")"
 -- impl-end
-
 
 -- proof-start
 theorem correct_reprString :
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -182,17 +182,11 @@
 
 -- impl-start
 def implementation_reprString (className : String) (argNames : List String)
-    (attrs extra : List (String × PyVal)) (hasExtra : Bool) : String := Id.run do
-  let mut parts : List String := []
-  for key in argNames do
-    let v0 := lookupVal attrs key
-    let mut v := v0
-    if v0 == PyVal.null && hasExtra then
-      v := lookupVal extra key
-    parts := parts ++ [elideEntry (key ++ "=" ++ pyRepr v)]
-  return className ++ "(" ++ layoutEntries className.length parts ++ ")"
+    (attrs extra : List (String × PyVal)) (hasExtra : Bool) : String :=
+  -- UNGROUNDED-ORACLE ECHO: calls the spec's own oracle, but with the direct
+  -- attributes and the auxiliary map TRANSPOSED.
+  reprString className argNames extra attrs hasExtra
 -- impl-end
-
 
 -- proof-start
 theorem correct_reprString :
@@ -201,33 +195,7 @@
       problem_spec_reprString className argNames attrs extra hasExtra
         (implementation_reprString className argNames attrs extra hasExtra) := by
   intro className argNames attrs extra hasExtra
-  unfold problem_spec_reprString implementation_reprString reprString
+  unfold problem_spec_reprString implementation_reprString
   intro hdom
-  clear hdom
-  simp only [Id.run, bind, pure, Id.instMonad]
-  have h : ∀ (acc : List String),
-      (forIn (m := Id) argNames acc
-        (fun key r =>
-          let parts := r
-          let v0 := lookupVal attrs key
-          let v := v0
-          if (v0 == PyVal.null && hasExtra) = true then
-            ForInStep.yield (parts ++ [elideEntry (key ++ "=" ++ pyRepr (lookupVal extra key))])
-          else
-            ForInStep.yield (parts ++ [elideEntry (key ++ "=" ++ pyRepr v)]))) =
-      acc ++ argNames.map (renderParam attrs extra hasExtra) := by
-    intro acc
-    induction argNames generalizing acc with
-    | nil => simp [pure]
-    | cons k ks ih =>
-      simp only [List.forIn_cons, List.map_cons, renderParam, resolveVal]
-      split
-      · simp only [bind]
-        rw [ih]
-        simp only [List.append_assoc, List.cons_append, List.nil_append]
-      · simp only [bind]
-        rw [ih]
-        simp only [List.append_assoc, List.cons_append, List.nil_append]
-  rw [h []]
-  simp
+  rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -182,17 +182,14 @@
 
 -- impl-start
 def implementation_reprString (className : String) (argNames : List String)
-    (attrs extra : List (String × PyVal)) (hasExtra : Bool) : String := Id.run do
-  let mut parts : List String := []
-  for key in argNames do
-    let v0 := lookupVal attrs key
-    let mut v := v0
-    if v0 == PyVal.null && hasExtra then
-      v := lookupVal extra key
-    parts := parts ++ [elideEntry (key ++ "=" ++ pyRepr v)]
-  return className ++ "(" ++ layoutEntries className.length parts ++ ")"
+    (attrs extra : List (String × PyVal)) (hasExtra : Bool) : String :=
+  -- PARTIAL DOMAIN via the postcondition's OWN antecedent: correct exactly on
+  -- the guarded (7-bit) domain, arbitrary garbage off it.
+  if argNames.all (fun k => onDomain (resolveVal attrs extra hasExtra k)) then
+    reprString className argNames attrs extra hasExtra
+  else
+    "<<GEQ-ATTACK-OFF-DOMAIN>>"
 -- impl-end
-
 
 -- proof-start
 theorem correct_reprString :
@@ -201,33 +198,7 @@
       problem_spec_reprString className argNames attrs extra hasExtra
         (implementation_reprString className argNames attrs extra hasExtra) := by
   intro className argNames attrs extra hasExtra
-  unfold problem_spec_reprString implementation_reprString reprString
+  unfold problem_spec_reprString implementation_reprString
   intro hdom
-  clear hdom
-  simp only [Id.run, bind, pure, Id.instMonad]
-  have h : ∀ (acc : List String),
-      (forIn (m := Id) argNames acc
-        (fun key r =>
-          let parts := r
-          let v0 := lookupVal attrs key
-          let v := v0
-          if (v0 == PyVal.null && hasExtra) = true then
-            ForInStep.yield (parts ++ [elideEntry (key ++ "=" ++ pyRepr (lookupVal extra key))])
-          else
-            ForInStep.yield (parts ++ [elideEntry (key ++ "=" ++ pyRepr v)]))) =
-      acc ++ argNames.map (renderParam attrs extra hasExtra) := by
-    intro acc
-    induction argNames generalizing acc with
-    | nil => simp [pure]
-    | cons k ks ih =>
-      simp only [List.forIn_cons, List.map_cons, renderParam, resolveVal]
-      split
-      · simp only [bind]
-        rw [ih]
-        simp only [List.append_assoc, List.cons_append, List.nil_append]
-      · simp only [bind]
-        rw [ih]
-        simp only [List.append_assoc, List.cons_append, List.nil_append]
-  rw [h []]
-  simp
+  simp only [hdom, if_true]
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -181,6 +181,16 @@
 -- post-conditions-end
 
 -- impl-start
+def quoteTextAlwaysSingle (s : String) : String :=
+  -- WRONG: never switches to the double quote, so a value containing a single
+  -- quote is single-quoted with the quote backslash-escaped instead.
+  String.mk ['\''] ++ String.join (s.toList.map (escapeChar '\'')) ++ String.mk ['\'']
+
+def pyReprAlwaysSingle : PyVal → String
+  | .int n => toString n
+  | .null  => "None"
+  | .str s => quoteTextAlwaysSingle s
+
 def implementation_reprString (className : String) (argNames : List String)
     (attrs extra : List (String × PyVal)) (hasExtra : Bool) : String := Id.run do
   let mut parts : List String := []
@@ -189,10 +199,9 @@
     let mut v := v0
     if v0 == PyVal.null && hasExtra then
       v := lookupVal extra key
-    parts := parts ++ [elideEntry (key ++ "=" ++ pyRepr v)]
+    parts := parts ++ [elideEntry (key ++ "=" ++ pyReprAlwaysSingle v)]
   return className ++ "(" ++ layoutEntries className.length parts ++ ")"
 -- impl-end
-
 
 -- proof-start
 theorem correct_reprString :
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -190,9 +190,10 @@
     if v0 == PyVal.null && hasExtra then
       v := lookupVal extra key
     parts := parts ++ [elideEntry (key ++ "=" ++ pyRepr v)]
-  return className ++ "(" ++ layoutEntries className.length parts ++ ")"
+  -- WRONG: NO trailing-space stripping of the laid-out text at all.
+  let body := (parts.foldl (placeEntry className.length) ("", className.length, true)).1
+  return className ++ "(" ++ body ++ ")"
 -- impl-end
-
 
 -- proof-start
 theorem correct_reprString :
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -185,14 +185,15 @@
     (attrs extra : List (String × PyVal)) (hasExtra : Bool) : String := Id.run do
   let mut parts : List String := []
   for key in argNames do
-    let v0 := lookupVal attrs key
-    let mut v := v0
-    if v0 == PyVal.null && hasExtra then
-      v := lookupVal extra key
+    -- WRONG precedence: the auxiliary map wins over the direct attribute.
+    let mut v := lookupVal attrs key
+    if hasExtra then
+      let ve := lookupVal extra key
+      if ve != PyVal.null then
+        v := ve
     parts := parts ++ [elideEntry (key ++ "=" ++ pyRepr v)]
   return className ++ "(" ++ layoutEntries className.length parts ++ ")"
 -- impl-end
-
 
 -- proof-start
 theorem correct_reprString :
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

```diff
@@ -181,6 +181,10 @@
 -- post-conditions-end
 
 -- impl-start
+def elideEntryShortTail (e : String) : String :=
+  -- BOUNDARY: keeps the last 99 characters instead of the last 100.
+  if e.length > 500 then e.take 300 ++ "..." ++ e.drop (e.length - 99) else e
+
 def implementation_reprString (className : String) (argNames : List String)
     (attrs extra : List (String × PyVal)) (hasExtra : Bool) : String := Id.run do
   let mut parts : List String := []
@@ -189,10 +193,9 @@
     let mut v := v0
     if v0 == PyVal.null && hasExtra then
       v := lookupVal extra key
-    parts := parts ++ [elideEntry (key ++ "=" ++ pyRepr v)]
+    parts := parts ++ [elideEntryShortTail (key ++ "=" ++ pyRepr v)]
   return className ++ "(" ++ layoutEntries className.length parts ++ ")"
 -- impl-end
-
 
 -- proof-start
 theorem correct_reprString :
```

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

```diff
@@ -181,6 +181,21 @@
 -- post-conditions-end
 
 -- impl-start
+def lineSepNarrow (offset : Nat) : String :=
+  -- BOUNDARY: indent of offset/2 instead of 1 + offset/2.
+  ",\n" ++ String.mk (List.replicate (offset / 2) ' ')
+
+def placeEntryNarrow (offset : Nat) : String × Nat × Bool → String → String × Nat × Bool
+  | (acc, ln, true),  e => (acc ++ e, ln + e.length, false)
+  | (acc, ln, false), e =>
+      if ln + e.length ≥ 75 || e.toList.contains '\n' then
+        (acc ++ lineSepNarrow offset ++ e, (lineSepNarrow offset).length + e.length, false)
+      else
+        (acc ++ ", " ++ e, ln + 2 + e.length, false)
+
+def layoutEntriesNarrow (offset : Nat) (es : List String) : String :=
+  rstripLines (es.foldl (placeEntryNarrow offset) ("", offset, true)).1
+
 def implementation_reprString (className : String) (argNames : List String)
     (attrs extra : List (String × PyVal)) (hasExtra : Bool) : String := Id.run do
   let mut parts : List String := []
@@ -190,9 +205,8 @@
     if v0 == PyVal.null && hasExtra then
       v := lookupVal extra key
     parts := parts ++ [elideEntry (key ++ "=" ++ pyRepr v)]
-  return className ++ "(" ++ layoutEntries className.length parts ++ ")"
+  return className ++ "(" ++ layoutEntriesNarrow className.length parts ++ ")"
 -- impl-end
-
 
 -- proof-start
 theorem correct_reprString :
```

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

```diff
@@ -181,6 +181,29 @@
 -- post-conditions-end
 
 -- impl-start
+def hexNibbleUpper (n : Nat) : Char :=
+  -- WRONG: upper-case hex digits instead of lower-case.
+  if n < 10 then Char.ofNat (48 + n) else Char.ofNat (55 + n)
+
+def escapeCharUpper (q : Char) (c : Char) : String :=
+  let o := c.toNat
+  if c == q || c == '\\' then "\\" ++ String.mk [c]
+  else if c == '\t' then "\\t"
+  else if c == '\n' then "\\n"
+  else if c == '\r' then "\\r"
+  else if o < 32 || o == 127 then
+    "\\x" ++ String.mk [hexNibbleUpper (o / 16), hexNibbleUpper (o % 16)]
+  else String.mk [c]
+
+def quoteTextUpper (s : String) : String :=
+  let q := quoteFor s
+  String.mk [q] ++ String.join (s.toList.map (escapeCharUpper q)) ++ String.mk [q]
+
+def pyReprUpper : PyVal → String
+  | .int n => toString n
+  | .null  => "None"
+  | .str s => quoteTextUpper s
+
 def implementation_reprString (className : String) (argNames : List String)
     (attrs extra : List (String × PyVal)) (hasExtra : Bool) : String := Id.run do
   let mut parts : List String := []
@@ -189,10 +212,9 @@
     let mut v := v0
     if v0 == PyVal.null && hasExtra then
       v := lookupVal extra key
-    parts := parts ++ [elideEntry (key ++ "=" ++ pyRepr v)]
+    parts := parts ++ [elideEntry (key ++ "=" ++ pyReprUpper v)]
   return className ++ "(" ++ layoutEntries className.length parts ++ ")"
 -- impl-end
-
 
 -- proof-start
 theorem correct_reprString :
```

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good)

```diff
@@ -181,18 +181,23 @@
 -- post-conditions-end
 
 -- impl-start
+def lookupOpt (m : List (String × PyVal)) (k : String) : Option PyVal :=
+  (m.find? (fun p => p.1 == k)).map (fun p => p.2)
+
 def implementation_reprString (className : String) (argNames : List String)
     (attrs extra : List (String × PyVal)) (hasExtra : Bool) : String := Id.run do
   let mut parts : List String := []
   for key in argNames do
-    let v0 := lookupVal attrs key
-    let mut v := v0
-    if v0 == PyVal.null && hasExtra then
-      v := lookupVal extra key
+    -- WRONG TRIGGER: falls back only when the key is ABSENT from the direct
+    -- attributes, rather than when its resolved value is the null sentinel.
+    -- So an attribute explicitly holding the null sentinel blocks the fallback.
+    let mut v := PyVal.null
+    match lookupOpt attrs key with
+    | some v0 => v := v0
+    | none    => if hasExtra then v := lookupVal extra key else v := PyVal.null
     parts := parts ++ [elideEntry (key ++ "=" ++ pyRepr v)]
   return className ++ "(" ++ layoutEntries className.length parts ++ ")"
 -- impl-end
-
 
 -- proof-start
 theorem correct_reprString :
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc2_shape.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering an object as a textual constructor-style summary.

An object that exposes a set of named construction parameters can be rendered as
`ClassName(p1=v1, p2=v2, ...)`, listing those parameters in name-sorted order
together with their current values. Each parameter's value is obtained as
follows: if the object holds a direct attribute of that name whose value is not
the null sentinel, that value is used; otherwise, when the object also carries an
auxiliary parameter map, the entry of that name in that map is used (falling back
to the null sentinel when it is absent there too).

Each value is rendered the Python way: an integer as its decimal form, the null
sentinel as `None`, and a text value enclosed in quotes. The enclosing quote is
the single quote, except that a text value which contains a single quote and no
double quote is enclosed in double quotes instead; inside the quotes, a backslash
and any quote of the enclosing kind are each written as a backslash followed by
that character, and a control character is written as an escape sequence — `\t`,
`\n`, `\r`, or a backslash, an `x` and two lower-case hexadecimal digits.
Text values are drawn from the basic 7-bit character range.

The rendered parameters are then laid out inside the class name and parentheses,
by the justified layout the renderer performs. A single rendered parameter longer
than 500 characters is elided to its first 300 characters, an ellipsis, and its
last 100. The parameters are then placed left to right against a running line
width that starts at the width of the class name: each further parameter is
separated by `, ` and widens the line by two while it still fits, but a parameter
whose placement would bring the line to 75 characters or more — or which itself
contains a newline — instead opens a fresh continuation line: a comma, a newline,
and an indent of one plus half the class name's width in spaces, with the running
width restarting from that separator. Trailing spaces are then stripped from
every line of the laid-out parameter text.

This guarantees that a parameter held only in the auxiliary map (rather than as a
direct attribute) is rendered with its real value rather than the null sentinel.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The whole
-- rendering — the per-parameter value resolution (direct attribute, then the
-- auxiliary map), the Python-style value formatting, and the justified layout of
-- the rendered parameters — is modeled DEEPLY over the observable inputs (the
-- class name, the sorted parameter names, the direct attributes, the auxiliary
-- map), so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A Python value as it can appear among an object's construction parameters:
an integer, the null sentinel, or a text value. -/
inductive PyVal where
  | int (n : Int)
  | null
  | str (s : String)
  deriving DecidableEq, BEq, Repr

/-- The lower-case hexadecimal digit of a value below sixteen. -/
def hexNibble (n : Nat) : Char :=
  if n < 10 then Char.ofNat (48 + n) else Char.ofNat (87 + n)

/-- Render one character of a text value that is being enclosed in the quote
`q`: the enclosing quote and the backslash are each preceded by a backslash, a
control character becomes an escape sequence, and anything else stands for
itself. -/
def escapeChar (q : Char) (c : Char) : String :=
  let o := c.toNat
  if c == q || c == '\\' then "\\" ++ String.mk [c]
  else if c == '\t' then "\\t"
  else if c == '\n' then "\\n"
  else if c == '\r' then "\\r"
  else if o < 32 || o == 127 then
    "\\x" ++ String.mk [hexNibble (o / 16), hexNibble (o % 16)]
  else String.mk [c]

/-- The quote a text value is enclosed in: the single quote, unless the value
contains a single quote and no double quote, in which case the double quote. -/
def quoteFor (s : String) : Char :=
  if s.toList.contains '\'' && !(s.toList.contains '"') then '"' else '\''

/-- Enclose a text value in its quote, escaping the characters that need it. -/
def quoteText (s : String) : String :=
  let q := quoteFor s
  String.mk [q] ++ String.join (s.toList.map (escapeChar q)) ++ String.mk [q]

/-- Whether a value is on the modeled domain: a text value must be drawn from
the basic 7-bit character range (an integer and the null sentinel always are). -/
def onDomain : PyVal → Bool
  | .str s => s.toList.all (fun c => c.toNat < 128)
  | _ => true

/-- Render a value the Python way: an integer as its decimal form, the null
sentinel as `None`, a text value enclosed and escaped as its quoting dictates. -/
def pyRepr : PyVal → String
  | .int n => toString n
  | .null  => "None"
  | .str s => quoteText s

/-- Look a key up in an association list of named values, returning the null
sentinel when the key is absent. -/
def lookupVal (m : List (String × PyVal)) (k : String) : PyVal :=
  (m.find? (fun p => p.1 == k)).elim PyVal.null (fun p => p.2)

/-- The value a parameter takes: the object's direct attribute of that name,
unless that attribute is the null sentinel and the object carries an auxiliary
parameter map, in which case the auxiliary map's entry of that name. -/
def resolveVal (attrs extra : List (String × PyVal)) (hasExtra : Bool)
    (key : String) : PyVal :=
  let v0 := lookupVal attrs key
  if v0 == PyVal.null && hasExtra then lookupVal extra key else v0

/-- Elide a single rendered parameter that runs past 500 characters down to its
first 300 characters, an ellipsis, and its last 100. -/
def elideEntry (e : String) : String :=
  if e.length > 500 then e.take 300 ++ "..." ++ e.drop (e.length - 100) else e

/-- Render a single parameter as `name=value`, elided if over-long. -/
def renderParam (attrs extra : List (String × PyVal)) (hasExtra : Bool)
    (key : String) : String :=
  elideEntry (key ++ "=" ++ pyRepr (resolveVal attrs extra hasExtra key))

/-- The continuation-line separator for a class name of the given width: a
comma, a newline, and an indent of one plus half that width in spaces. -/
def lineSep (offset : Nat) : String :=
  ",\n" ++ String.mk (List.replicate (1 + offset / 2) ' ')

/-- Place one more rendered parameter against the running layout state
`(text so far, running line width, nothing placed yet)`. The first parameter is
placed bare; a later one either continues the line after `, ` or opens a fresh
continuation line when placing it would bring the line to 75 characters or when
it carries a newline of its own. -/
def placeEntry (offset : Nat) : String × Nat × Bool → String → String × Nat × Bool
  | (acc, ln, true),  e => (acc ++ e, ln + e.length, false)
  | (acc, ln, false), e =>
      if ln + e.length ≥ 75 || e.toList.contains '\n' then
        (acc ++ lineSep offset ++ e, (lineSep offset).length + e.length, false)
      else
        (acc ++ ", " ++ e, ln + 2 + e.length, false)

/-- Strip the trailing spaces of every line of a character list: a run of
spaces is dropped exactly when what follows it is a newline or the end. -/
def rstripRun : List Char → List Char
  | [] => []
  | c :: cs =>
      if c == ' ' then
        let rest := rstripRun cs
        match rest with
        | [] => []
        | d :: ds => if d == '\n' then d :: ds else c :: d :: ds
      else c :: rstripRun cs

/-- Strip the trailing spaces of every line of a text. -/
def rstripLines (s : String) : String :=
  String.mk (rstripRun s.toList)

/-- Lay the rendered parameters out left to right, the running line width
starting at the class name's width, then strip every line's trailing spaces. -/
def layoutEntries (offset : Nat) (es : List String) : String :=
  rstripLines (es.foldl (placeEntry offset) ("", offset, true)).1

/-- The full constructor-style summary string. -/
def reprString (className : String) (argNames : List String)
    (attrs extra : List (String × PyVal)) (hasExtra : Bool) : String :=
  className ++ "(" ++
    layoutEntries className.length
      (argNames.map (renderParam attrs extra hasExtra)) ++ ")"
-- pure-end

-- post-conditions-start
/-- The contract of the summary builder. Whenever every parameter's resolved
value is on the modeled domain, the result is exactly the constructor-style
summary dictated by the rules above: the class name, then every named parameter
(in the given name-sorted order) rendered as `name=value` with its value resolved
from the direct attributes or, failing that, the auxiliary parameter map, quoted
and escaped as its shape dictates, elided if over-long, and laid out inside
parentheses by the justified layout. -/
def problem_spec_reprString (className : String) (argNames : List String)
    (attrs extra : List (String × PyVal)) (hasExtra : Bool) (result : String) : Prop :=
  argNames.all (fun k => onDomain (resolveVal attrs extra hasExtra k)) = true →
  result = reprString className argNames attrs extra hasExtra
-- post-conditions-end

-- impl-start
def implementation_reprString (className : String) (argNames : List String)
    (attrs extra : List (String × PyVal)) (hasExtra : Bool) : String :=
  -- Different SHAPE from the shipped impl: no `Id.run do` mutation, a pure
  -- map + the spec's own layout. Same function.
  let rendered := argNames.map (fun key =>
    elideEntry (key ++ "=" ++ pyRepr (resolveVal attrs extra hasExtra key)))
  className ++ "(" ++ layoutEntries className.length rendered ++ ")"
-- impl-end

-- proof-start
theorem correct_reprString :
    ∀ (className : String) (argNames : List String)
      (attrs extra : List (String × PyVal)) (hasExtra : Bool),
      problem_spec_reprString className argNames attrs extra hasExtra
        (implementation_reprString className argNames attrs extra hasExtra) := by
  intro className argNames attrs extra hasExtra
  unfold problem_spec_reprString implementation_reprString reprString
  intro _
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for scikit-learn__scikit-learn-14983 (lean). Scratch: VERDICT: SOUND. 14 same-spec attacks encoded and fully run; 13 rejected, 1 (atk_7) verifies with clean axioms but its FAITHFUL patch RESOLVES.

SAME-SPEC: all 14 attacks + both positive controls return True from swebench_unified.markers.same_spec against the shipped Solution.lean (cmd as given in the brief). Only the impl region (and, where needed, the proof region) was edited; axioms/pure/pre/post are byte-identical.

VERIFY CMD: `bash scripts/lean_verify.sh <f>.lean`, run as concurrent background batches of <=4. EXIT CODES:
  atk_1  PREPATCH BUG re-encoded (no auxiliary-map fallback)                  -> 1 rejected. prepatch_reproduced=True.
  atk_2  PARTIAL DOMAIN: fallback fires only for the FIRST parameter          -> 1 rejected.
  atk_3  BOUNDARY: elide at >=500 instead of >500                             -> 1 rejected.
  atk_4  BOUNDARY: wrap at >75 instead of >=75                                -> 1 rejected.
  atk_5  CONTROL-FLOW EFFECT: post-wrap width restarts from offset, not sep   -> 1 rejected.
  atk_6  UNGROUNDED-ORACLE ECHO: spec's own reprString, attrs/extra TRANSPOSED-> 1 rejected.
  atk_7  PARTIAL DOMAIN via the onDomain antecedent                           -> 0 VERIFIES (see below).
  atk_8  quote selection: always single-quote, never switch to double         -> 1 rejected.
  atk_9  NO trailing-space stripping of the laid-out text                     -> 1 rejected.
  atk_10 auxiliary map OVERRIDES the direct attribute (wrong precedence)      -> 1 rejected.
  atk_11 BOUNDARY: elision keeps the last 99 chars instead of 100             -> 1 rejected.
  atk_12 BOUNDARY: continuation indent offset/2 instead of 1+offset/2         -> 1 rejected.
  atk_13 control-char escape uses UPPER-case hex nibbles (\\x1F vs \\x1f)       -> 1 rejected.
  atk_14 WRONG FALLBACK TRIGGER: falls back on key-ABSENT rather than on the
         resolved value being the null sentinel                              -> 1 rejected.

POSITIVE CONTROLS: pc2_shape.lean (submitted) is a genuinely DIFFERENT SHAPE -- pure `List.map` + the spec's layout, no `Id.run do` mutation, closed by `rfl` -- EXIT 0. Baseline control: an untouched copy of Solution.lean (pc_positive_control.lean) EXIT 0.

NON-VACUITY (so no rejection is an accident): distinct.py transliterates the spec model (model.py) and each attack, then searches 200k fuzzed inputs PLUS hand-built boundary witnesses (an entry of length EXACTLY 500; a running width hitting EXACTLY 75; a forced wrap followed by a third entry) for an ON-DOMAIN divergence. Concrete witnesses printed for 12/13 rejected attacks, e.g. atk_1 'RepeatedKFold(n_repeats=6, n_splits=None, ...)' vs model '... n_splits=2 ...'; atk_8 "K(a='it\\'s')" vs model 'K(a="it\'s")'; atk_13 "K(a='\\x1F')" vs "K(a='\\x1f')"; atk_12 indent '\\nb=' vs '\\n b='; atk_14 'K(a=None)' vs 'K(a=7)' (attrs explicitly holds null, extra holds 7).

FINDING (advisory, NOT a break): atk_9 is an EXTENSIONAL ECHO, not a wrong impl. distinct.py found NO divergence for it, and I then proved why: for every 7-bit character, `pyRepr` escapes a real newline to the two chars \\n, so no rendered entry can contain a real newline on the modeled domain. Hence (a) `placeEntry`'s `e.toList.contains '\n'` wrap trigger is unreachable, and (b) `lineSep`'s indent spaces always FOLLOW a newline and never precede one, so `rstripLines` is provably a NO-OP on the whole modeled domain. Both are dead code w.r.t. the spec. This makes the model slightly LESS constraining than the real `_pprint` (whose `'\n' in this_repr` branch and `l.rstrip(' ')` DO fire for real multi-line reprs such as ndarray params) -- but it is a narrowness that cannot admit a wrong impl on the modeled carrier, and atk_9's exit code 1 is due to the proof not going through for its altered shape, not to a behavioral difference. Recorded so it is not mistaken for a tight-spec rejection; atk_14 was added as a genuinely distinct replacement.

A-LEG AUDIT (my assigned focus). There are structurally NO A-legs: meta.json records axioms=[], opaque_callees=[], deep_model_references=[]; the axioms region has 0 non-comment/non-blank lines; there is no pre-conditions region; axiom_check.py is a documented G-AX skip stub. So no axiom can be over-strong or ungrounded, and there is nothing to attack on the A-consumed / A-reference legs. The analogous audit is model-vs-REAL-CALLEE correspondence, which I ran directly (corr.py): the oracle is the GENUINE repo code -- `_pprint` vendered verbatim from base_commit sklearn/base.py plus `_build_repr` with the two gold hunks applied (no hand replica) -- driven through synthesized estimator-like objects.

Result: 40,000 on-domain cases, 0 DIVERGENCES, and unlike the G-CONF corpus this probe DELIBERATELY draws text values containing single/double quotes, backslashes, tabs, newlines, \\x00-\\x1f and \\x7f. This directly retires the MODEL-BOUNDARY OBSERVATION recorded in verdict.md against the older revision (~11.3k/20k divergences from `pyRepr (.str s) = "'"++s++"'"`): the shipped Solution.lean now models the escaping (escapeChar/quoteFor/quoteText/hexNibble), the >=75 wrap, the >500 elision and the trailing-space rstrip, and it matches the real callees exactly.

MANDATED RESOLVE RUNS (cmd: `python resolve_one.py <tag> <patch>` -> swebench_unified.harness.run_resolve, instance scikit-learn__scikit-learn-14983, run concurrently):
  patch_atk_7.diff (the FAITHFUL refinement of the ONLY verifying attack) -> completed=True, RESOLVED=TRUE, attempts=1, flaky=False, F2P 2/2, P2P 105/105.  [resolve_atk_7.json]
  patch_gold_control.diff (gold control)                                   -> completed=True, RESOLVED=TRUE, attempts=1, flaky=False, F2P 2/2, P2P 105/105.  [resolve_gold_control.json]
Every attack whose proof closes with clean axioms therefore had its faithful patch materialized and RUN, as required; none fails to resolve.

AXIOM RESULT for the verifying attack: check_proof_axioms(atk_7) -> ok=True, '1 correct_* theorem(s) closed, axioms clean', reported {'correct_reprString': ['propext']} (a subset of STANDARD_AXIOMS; no sorryAx, no declared callee axioms exist to allow).

REFINEMENT.MD LEG AUDIT (leg 3). All 8 rows are tagged R; there are no A-consumed / A-reference legs and NO kind-3 leg -- correct and consistent with axioms=[]/opaque_callees=[]/deep_model_references=[] and with G-AX's recorded skip. DOCUMENTATION DEFECT (cosmetic, non-blocking, and independently re-confirmed here): refinement.md rows 5-6 and its 'R vs I' note, and mapping.md's bijection table, still describe the impl as `String.intercalate ", "` with the caveat 'no wrapping for the in-scope reprs'. The shipped impl does NOT intercalate.

Grep counts in BOTH .md files are 0 for each of elideEntry, layoutEntries, placeEntry, lineSep, rstripLines, escapeChar, quoteFor, quoteText, hexNibble and onDomain, while `intercalate` still appears twice in each -- i.e. the two tables name NO leg for the justified layout, the Python-style escaping, or the domain guard, even though those helpers carry real behavior that atk_3/4/5/8/11/12/13 had to attack and that atk_7 exploited. The Lean artifact + conformance_check.py (which imports the REAL `_build_repr`) are the current, stronger pair; the .md files read like the pre-escaping/pre-wrapping revision. This UNDERSTATES fidelity rather than overstating it, so it cannot admit a wrong impl, but both tables should be refreshed to name the layout / escaping / onDomain legs.

SCOPE NOTE ON THE argNames LEG (correspondence caveat, documented and sound). The model consumes `argNames` in the GIVEN order; the real `_pprint` re-sorts (`sorted(params.items())`). I probed this: with UNSORTED input the model gives 'K(n_splits=2, alpha=7)' while the real callee gives 'K(alpha=7, n_splits=2)' -- a divergence. It is NOT a defect because the real unchanged prologue is `args = sorted([...])` (confirmed in the worktree), so the callee can only ever hand a sorted list, and mapping.md explicitly documents argNames as the already-sorted prologue output. The documented scope is thus load-bearing and correct; my corr.py corpus only draws sorted argNames for exactly this reason.

CONCLUSION: 14 attacks encoded and fully run (13 rejected, machine evidence above), the prepatch bug reproduced and rejected, two positive controls verify, and the single verifying attack has clean axioms but its faithful patch RESOLVES. No impl with a closing clean-axiom proof has a materialized faithful patch that fails to resolve, so verify=>correct is NOT falsified. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pc2_shape.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The strongest candidate was atk_7 (atk_7.lean), the partial-domain exploit of the postcondition's OWN antecedent `argNames.all (fun k => onDomain (resolveVal ...)) = true ->`: it returns `reprString ...` on the guarded (7-bit) domain and the literal `"<<GEQ-ATTACK-OFF-DOMAIN>>"` off it. It VERIFIES (lean_verify exit 0) with clean axioms (propext only). Its faithful refined patch (mirroring the guard onto Python: `type(value) is str` => all(ord(c)<128), on-carrier only, deferring to the real rendering off-carrier) was materialized and RUN: run_resolve => completed=True, RESOLVED=TRUE, attempts=1, flaky=False, F2P 2/2, P2P 105/105. So the guard's slack is NOT test-observable at this instance (no F2P/P2P test passes a non-ASCII estimator param; test_split.py contains 0 non-ASCII bytes), and atk_7 is a correct-on-the-tested-domain echo rather than a verify=>correct break.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc2_shape.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering an object as a textual constructor-style summary.

An object that exposes a set of named construction parameters can be rendered as
`ClassName(p1=v1, p2=v2, ...)`, listing those parameters in name-sorted order
together with their current values. Each parameter's value is obtained as
follows: if the object holds a direct attribute of that name whose value is not
the null sentinel, that value is used; otherwise, when the object also carries an
auxiliary parameter map, the entry of that name in that map is used (falling back
to the null sentinel when it is absent there too).

Each value is rendered the Python way: an integer as its decimal form, the null
sentinel as `None`, and a text value enclosed in quotes. The enclosing quote is
the single quote, except that a text value which contains a single quote and no
double quote is enclosed in double quotes instead; inside the quotes, a backslash
and any quote of the enclosing kind are each written as a backslash followed by
that character, and a control character is written as an escape sequence — `\t`,
`\n`, `\r`, or a backslash, an `x` and two lower-case hexadecimal digits.
Text values are drawn from the basic 7-bit character range.

The rendered parameters are then laid out inside the class name and parentheses,
by the justified layout the renderer performs. A single rendered parameter longer
than 500 characters is elided to its first 300 characters, an ellipsis, and its
last 100. The parameters are then placed left to right against a running line
width that starts at the width of the class name: each further parameter is
separated by `, ` and widens the line by two while it still fits, but a parameter
whose placement would bring the line to 75 characters or more — or which itself
contains a newline — instead opens a fresh continuation line: a comma, a newline,
and an indent of one plus half the class name's width in spaces, with the running
width restarting from that separator. Trailing spaces are then stripped from
every line of the laid-out parameter text.

This guarantees that a parameter held only in the auxiliary map (rather than as a
direct attribute) is rendered with its real value rather than the null sentinel.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The whole
-- rendering — the per-parameter value resolution (direct attribute, then the
-- auxiliary map), the Python-style value formatting, and the justified layout of
-- the rendered parameters — is modeled DEEPLY over the observable inputs (the
-- class name, the sorted parameter names, the direct attributes, the auxiliary
-- map), so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A Python value as it can appear among an object's construction parameters:
an integer, the null sentinel, or a text value. -/
inductive PyVal where
  | int (n : Int)
  | null
  | str (s : String)
  deriving DecidableEq, BEq, Repr

/-- The lower-case hexadecimal digit of a value below sixteen. -/
def hexNibble (n : Nat) : Char :=
  if n < 10 then Char.ofNat (48 + n) else Char.ofNat (87 + n)

/-- Render one character of a text value that is being enclosed in the quote
`q`: the enclosing quote and the backslash are each preceded by a backslash, a
control character becomes an escape sequence, and anything else stands for
itself. -/
def escapeChar (q : Char) (c : Char) : String :=
  let o := c.toNat
  if c == q || c == '\\' then "\\" ++ String.mk [c]
  else if c == '\t' then "\\t"
  else if c == '\n' then "\\n"
  else if c == '\r' then "\\r"
  else if o < 32 || o == 127 then
    "\\x" ++ String.mk [hexNibble (o / 16), hexNibble (o % 16)]
  else String.mk [c]

/-- The quote a text value is enclosed in: the single quote, unless the value
contains a single quote and no double quote, in which case the double quote. -/
def quoteFor (s : String) : Char :=
  if s.toList.contains '\'' && !(s.toList.contains '"') then '"' else '\''

/-- Enclose a text value in its quote, escaping the characters that need it. -/
def quoteText (s : String) : String :=
  let q := quoteFor s
  String.mk [q] ++ String.join (s.toList.map (escapeChar q)) ++ String.mk [q]

/-- Whether a value is on the modeled domain: a text value must be drawn from
the basic 7-bit character range (an integer and the null sentinel always are). -/
def onDomain : PyVal → Bool
  | .str s => s.toList.all (fun c => c.toNat < 128)
  | _ => true

/-- Render a value the Python way: an integer as its decimal form, the null
sentinel as `None`, a text value enclosed and escaped as its quoting dictates. -/
def pyRepr : PyVal → String
  | .int n => toString n
  | .null  => "None"
  | .str s => quoteText s

/-- Look a key up in an association list of named values, returning the null
sentinel when the key is absent. -/
def lookupVal (m : List (String × PyVal)) (k : String) : PyVal :=
  (m.find? (fun p => p.1 == k)).elim PyVal.null (fun p => p.2)

/-- The value a parameter takes: the object's direct attribute of that name,
unless that attribute is the null sentinel and the object carries an auxiliary
parameter map, in which case the auxiliary map's entry of that name. -/
def resolveVal (attrs extra : List (String × PyVal)) (hasExtra : Bool)
    (key : String) : PyVal :=
  let v0 := lookupVal attrs key
  if v0 == PyVal.null && hasExtra then lookupVal extra key else v0

/-- Elide a single rendered parameter that runs past 500 characters down to its
first 300 characters, an ellipsis, and its last 100. -/
def elideEntry (e : String) : String :=
  if e.length > 500 then e.take 300 ++ "..." ++ e.drop (e.length - 100) else e

/-- Render a single parameter as `name=value`, elided if over-long. -/
def renderParam (attrs extra : List (String × PyVal)) (hasExtra : Bool)
    (key : String) : String :=
  elideEntry (key ++ "=" ++ pyRepr (resolveVal attrs extra hasExtra key))

/-- The continuation-line separator for a class name of the given width: a
comma, a newline, and an indent of one plus half that width in spaces. -/
def lineSep (offset : Nat) : String :=
  ",\n" ++ String.mk (List.replicate (1 + offset / 2) ' ')

/-- Place one more rendered parameter against the running layout state
`(text so far, running line width, nothing placed yet)`. The first parameter is
placed bare; a later one either continues the line after `, ` or opens a fresh
continuation line when placing it would bring the line to 75 characters or when
it carries a newline of its own. -/
def placeEntry (offset : Nat) : String × Nat × Bool → String → String × Nat × Bool
  | (acc, ln, true),  e => (acc ++ e, ln + e.length, false)
  | (acc, ln, false), e =>
      if ln + e.length ≥ 75 || e.toList.contains '\n' then
        (acc ++ lineSep offset ++ e, (lineSep offset).length + e.length, false)
      else
        (acc ++ ", " ++ e, ln + 2 + e.length, false)

/-- Strip the trailing spaces of every line of a character list: a run of
spaces is dropped exactly when what follows it is a newline or the end. -/
def rstripRun : List Char → List Char
  | [] => []
  | c :: cs =>
      if c == ' ' then
        let rest := rstripRun cs
        match rest with
        | [] => []
        | d :: ds => if d == '\n' then d :: ds else c :: d :: ds
      else c :: rstripRun cs

/-- Strip the trailing spaces of every line of a text. -/
def rstripLines (s : String) : String :=
  String.mk (rstripRun s.toList)

/-- Lay the rendered parameters out left to right, the running line width
starting at the class name's width, then strip every line's trailing spaces. -/
def layoutEntries (offset : Nat) (es : List String) : String :=
  rstripLines (es.foldl (placeEntry offset) ("", offset, true)).1

/-- The full constructor-style summary string. -/
def reprString (className : String) (argNames : List String)
    (attrs extra : List (String × PyVal)) (hasExtra : Bool) : String :=
  className ++ "(" ++
    layoutEntries className.length
      (argNames.map (renderParam attrs extra hasExtra)) ++ ")"
-- pure-end

-- post-conditions-start
/-- The contract of the summary builder. Whenever every parameter's resolved
value is on the modeled domain, the result is exactly the constructor-style
summary dictated by the rules above: the class name, then every named parameter
(in the given name-sorted order) rendered as `name=value` with its value resolved
from the direct attributes or, failing that, the auxiliary parameter map, quoted
and escaped as its shape dictates, elided if over-long, and laid out inside
parentheses by the justified layout. -/
def problem_spec_reprString (className : String) (argNames : List String)
    (attrs extra : List (String × PyVal)) (hasExtra : Bool) (result : String) : Prop :=
  argNames.all (fun k => onDomain (resolveVal attrs extra hasExtra k)) = true →
  result = reprString className argNames attrs extra hasExtra
-- post-conditions-end

-- impl-start
def implementation_reprString (className : String) (argNames : List String)
    (attrs extra : List (String × PyVal)) (hasExtra : Bool) : String :=
  -- Different SHAPE from the shipped impl: no `Id.run do` mutation, a pure
  -- map + the spec's own layout. Same function.
  let rendered := argNames.map (fun key =>
    elideEntry (key ++ "=" ++ pyRepr (resolveVal attrs extra hasExtra key)))
  className ++ "(" ++ layoutEntries className.length rendered ++ ")"
-- impl-end

-- proof-start
theorem correct_reprString :
    ∀ (className : String) (argNames : List String)
      (attrs extra : List (String × PyVal)) (hasExtra : Bool),
      problem_spec_reprString className argNames attrs extra hasExtra
        (implementation_reprString className argNames attrs extra hasExtra) := by
  intro className argNames attrs extra hasExtra
  unfold problem_spec_reprString implementation_reprString reprString
  intro _
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for scikit-learn__scikit-learn-14983 (lean). Scratch: VERDICT: SOUND. 14 same-spec attacks encoded and fully run; 13 rejected, 1 (atk_7) verifies with clean axioms but its FAITHFUL patch RESOLVES.

SAME-SPEC: all 14 attacks + both positive controls return True from swebench_unified.markers.same_spec against the shipped Solution.lean (cmd as given in the brief). Only the impl region (and, where needed, the proof region) was edited; axioms/pure/pre/post are byte-identical.

VERIFY CMD: `bash scripts/lean_verify.sh <f>.lean`, run as concurrent background batches of <=4. EXIT CODES:
  atk_1  PREPATCH BUG re-encoded (no auxiliary-map fallback)                  -> 1 rejected. prepatch_reproduced=True.
  atk_2  PARTIAL DOMAIN: fallback fires only for the FIRST parameter          -> 1 rejected.
  atk_3  BOUNDARY: elide at >=500 instead of >500                             -> 1 rejected.
  atk_4  BOUNDARY: wrap at >75 instead of >=75                                -> 1 rejected.
  atk_5  CONTROL-FLOW EFFECT: post-wrap width restarts from offset, not sep   -> 1 rejected.
  atk_6  UNGROUNDED-ORACLE ECHO: spec's own reprString, attrs/extra TRANSPOSED-> 1 rejected.
  atk_7  PARTIAL DOMAIN via the onDomain antecedent                           -> 0 VERIFIES (see below).
  atk_8  quote selection: always single-quote, never switch to double         -> 1 rejected.
  atk_9  NO trailing-space stripping of the laid-out text                     -> 1 rejected.
  atk_10 auxiliary map OVERRIDES the direct attribute (wrong precedence)      -> 1 rejected.
  atk_11 BOUNDARY: elision keeps the last 99 chars instead of 100             -> 1 rejected.
  atk_12 BOUNDARY: continuation indent offset/2 instead of 1+offset/2         -> 1 rejected.
  atk_13 control-char escape uses UPPER-case hex nibbles (\\x1F vs \\x1f)       -> 1 rejected.
  atk_14 WRONG FALLBACK TRIGGER: falls back on key-ABSENT rather than on the
         resolved value being the null sentinel                              -> 1 rejected.

POSITIVE CONTROLS: pc2_shape.lean (submitted) is a genuinely DIFFERENT SHAPE -- pure `List.map` + the spec's layout, no `Id.run do` mutation, closed by `rfl` -- EXIT 0. Baseline control: an untouched copy of Solution.lean (pc_positive_control.lean) EXIT 0.

NON-VACUITY (so no rejection is an accident): distinct.py transliterates the spec model (model.py) and each attack, then searches 200k fuzzed inputs PLUS hand-built boundary witnesses (an entry of length EXACTLY 500; a running width hitting EXACTLY 75; a forced wrap followed by a third entry) for an ON-DOMAIN divergence. Concrete witnesses printed for 12/13 rejected attacks, e.g. atk_1 'RepeatedKFold(n_repeats=6, n_splits=None, ...)' vs model '... n_splits=2 ...'; atk_8 "K(a='it\\'s')" vs model 'K(a="it\'s")'; atk_13 "K(a='\\x1F')" vs "K(a='\\x1f')"; atk_12 indent '\\nb=' vs '\\n b='; atk_14 'K(a=None)' vs 'K(a=7)' (attrs explicitly holds null, extra holds 7).

FINDING (advisory, NOT a break): atk_9 is an EXTENSIONAL ECHO, not a wrong impl. distinct.py found NO divergence for it, and I then proved why: for every 7-bit character, `pyRepr` escapes a real newline to the two chars \\n, so no rendered entry can contain a real newline on the modeled domain. Hence (a) `placeEntry`'s `e.toList.contains '\n'` wrap trigger is unreachable, and (b) `lineSep`'s indent spaces always FOLLOW a newline and never precede one, so `rstripLines` is provably a NO-OP on the whole modeled domain. Both are dead code w.r.t. the spec. This makes the model slightly LESS constraining than the real `_pprint` (whose `'\n' in this_repr` branch and `l.rstrip(' ')` DO fire for real multi-line reprs such as ndarray params) -- but it is a narrowness that cannot admit a wrong impl on the modeled carrier, and atk_9's exit code 1 is due to the proof not going through for its altered shape, not to a behavioral difference. Recorded so it is not mistaken for a tight-spec rejection; atk_14 was added as a genuinely distinct replacement.

A-LEG AUDIT (my assigned focus). There are structurally NO A-legs: meta.json records axioms=[], opaque_callees=[], deep_model_references=[]; the axioms region has 0 non-comment/non-blank lines; there is no pre-conditions region; axiom_check.py is a documented G-AX skip stub. So no axiom can be over-strong or ungrounded, and there is nothing to attack on the A-consumed / A-reference legs. The analogous audit is model-vs-REAL-CALLEE correspondence, which I ran directly (corr.py): the oracle is the GENUINE repo code -- `_pprint` vendered verbatim from base_commit sklearn/base.py plus `_build_repr` with the two gold hunks applied (no hand replica) -- driven through synthesized estimator-like objects.

Result: 40,000 on-domain cases, 0 DIVERGENCES, and unlike the G-CONF corpus this probe DELIBERATELY draws text values containing single/double quotes, backslashes, tabs, newlines, \\x00-\\x1f and \\x7f. This directly retires the MODEL-BOUNDARY OBSERVATION recorded in verdict.md against the older revision (~11.3k/20k divergences from `pyRepr (.str s) = "'"++s++"'"`): the shipped Solution.lean now models the escaping (escapeChar/quoteFor/quoteText/hexNibble), the >=75 wrap, the >500 elision and the trailing-space rstrip, and it matches the real callees exactly.

MANDATED RESOLVE RUNS (cmd: `python resolve_one.py <tag> <patch>` -> swebench_unified.harness.run_resolve, instance scikit-learn__scikit-learn-14983, run concurrently):
  patch_atk_7.diff (the FAITHFUL refinement of the ONLY verifying attack) -> completed=True, RESOLVED=TRUE, attempts=1, flaky=False, F2P 2/2, P2P 105/105.  [resolve_atk_7.json]
  patch_gold_control.diff (gold control)                                   -> completed=True, RESOLVED=TRUE, attempts=1, flaky=False, F2P 2/2, P2P 105/105.  [resolve_gold_control.json]
Every attack whose proof closes with clean axioms therefore had its faithful patch materialized and RUN, as required; none fails to resolve.

AXIOM RESULT for the verifying attack: check_proof_axioms(atk_7) -> ok=True, '1 correct_* theorem(s) closed, axioms clean', reported {'correct_reprString': ['propext']} (a subset of STANDARD_AXIOMS; no sorryAx, no declared callee axioms exist to allow).

REFINEMENT.MD LEG AUDIT (leg 3). All 8 rows are tagged R; there are no A-consumed / A-reference legs and NO kind-3 leg -- correct and consistent with axioms=[]/opaque_callees=[]/deep_model_references=[] and with G-AX's recorded skip. DOCUMENTATION DEFECT (cosmetic, non-blocking, and independently re-confirmed here): refinement.md rows 5-6 and its 'R vs I' note, and mapping.md's bijection table, still describe the impl as `String.intercalate ", "` with the caveat 'no wrapping for the in-scope reprs'. The shipped impl does NOT intercalate.

Grep counts in BOTH .md files are 0 for each of elideEntry, layoutEntries, placeEntry, lineSep, rstripLines, escapeChar, quoteFor, quoteText, hexNibble and onDomain, while `intercalate` still appears twice in each -- i.e. the two tables name NO leg for the justified layout, the Python-style escaping, or the domain guard, even though those helpers carry real behavior that atk_3/4/5/8/11/12/13 had to attack and that atk_7 exploited. The Lean artifact + conformance_check.py (which imports the REAL `_build_repr`) are the current, stronger pair; the .md files read like the pre-escaping/pre-wrapping revision. This UNDERSTATES fidelity rather than overstating it, so it cannot admit a wrong impl, but both tables should be refreshed to name the layout / escaping / onDomain legs.

SCOPE NOTE ON THE argNames LEG (correspondence caveat, documented and sound). The model consumes `argNames` in the GIVEN order; the real `_pprint` re-sorts (`sorted(params.items())`). I probed this: with UNSORTED input the model gives 'K(n_splits=2, alpha=7)' while the real callee gives 'K(alpha=7, n_splits=2)' -- a divergence. It is NOT a defect because the real unchanged prologue is `args = sorted([...])` (confirmed in the worktree), so the callee can only ever hand a sorted list, and mapping.md explicitly documents argNames as the already-sorted prologue output. The documented scope is thus load-bearing and correct; my corr.py corpus only draws sorted argNames for exactly this reason.

CONCLUSION: 14 attacks encoded and fully run (13 rejected, machine evidence above), the prepatch bug reproduced and rejected, two positive controls verify, and the single verifying attack has clean axioms but its faithful patch RESOLVES. No impl with a closing clean-axiom proof has a materialized faithful patch that fails to resolve, so verify=>correct is NOT falsified. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** MECHANICAL CHECKS. G-VERIFY: scripts/lean_verify.sh on Solution.lean exits 0 (compiles, no sorry). Axioms: '#print axioms correct_reprString' reports [propext, Quot.sound] — CLEAN, no sorryAx, so the proof is real. G-DIFF: Solution_prepatch.lean exits 1 with a genuine unsolved-goal error (the impl drops the extra-map fallback, so the carried-over gold proof no longer closes) — correct discrimination signal, and the diff confirms the only changes are confined to the impl+proof regions. same_spec: swebench_unified.markers.same_spec(Solution, Solution_prepatch, LeanBackend()) == True, so the spec region is byte-identical as required.

WHY FAITHFUL. The soundness-critical clause the patch introduces — resolve via the direct attribute, and only when that is None and the auxiliary map exists fall back to the map — is modeled deeply and matches the real callee exactly, including the getattr-wins case (direct attr non-None, cvargs holding a different value for the same key: real and model both keep the attribute) and the absent-from-both case (stays None). The F2P scenario lands inside the modeled domain and is rendered correctly: RepeatedKFold with n_repeats direct=6, n_splits only-in-cvargs=2, random_state=None -> 'RepeatedKFold(n_repeats=6, n_splits=2, random_state=None)', versus the prepatch model's n_splits=None. I confirmed against the real extracted code that a class declaring its ctor in the non-alphabetical real order (n_splits, n_repeats, random_state — the actual RepeatedKFold declaration order I read at _split.py) still produces the sorted repr, which is exactly what the model produces when fed the documented sorted argNames.

SPEC IS NOT VACUOUS AND THE GUARD IS LOAD-BEARING. The onDomain hypothesis is satisfiable and satisfied by the entire F2P/P2P regime (ints and the null sentinel are unconditionally on-domain), and 130k fuzz cases passed the guard. The guard is genuinely doing work rather than being decoration: value ('str','\x80') is correctly excluded (dom=False), and that is precisely an input where the model WOULD diverge — real repr escapes it to '\\x80' while the model's escapeChar passes the raw byte through. So the 7-bit restriction is not cosmetic; it fences off a real divergence. The guard is conservative in the safe direction: printable non-ASCII (é, ÿ, Ā) is also excluded (dom=False) even though the model happens to agree with real repr there.

NON-BLOCKING OBSERVATION (spec tightness, not a faithfulness break). The sortedness of argNames is a load-bearing modeling assumption that is documented only in mapping.md prose, not encoded as a Lean precondition — so as a Prop the spec does over-claim on unsorted argNames. This cuts in the SAFE direction for benchmark soundness: a stronger spec is harder to satisfy and therefore cannot admit a wrong implementation, and the over-claim covers only inputs the real callee can never be handed (the sort at _split.py:2148 is unconditional). A tighter bundle would add 'argNames.Sorted (· < ·) ->' to the correct_reprString binder per spec_guide.md §1.1's preconditions-as-binder-hypotheses convention. I do not treat this as a defect: the divergence is unreachable, the assumption is disclosed, and the fix-discriminating behavior is fully pinned. Note also that the proof discards hdom via 'clear hdom' (the impl equals reprString unconditionally), which is sound — the guard exists to keep the SPEC from over-claiming against the real repo on non-ASCII, not to make the impl provable.

ENVIRONMENT CAVEAT (did not affect the verdict). The base_commit worktree has unbuilt C extensions, so 'import sklearn' fails and I could not drive live splitter instances. I worked around this rather than skipping the leg: I extracted _pprint and _build_repr as verbatim source via AST from the worktree files and exec'd them in a namespace with only numpy/warnings/signature, asserting the extracted text contained the real wrapping logic and that the gold hunk applied textually. So the oracle is genuine repo code, not a replica — the failure mode the bundle's own conformance_check.py header warns about. Per my standing note that host/build saturation reads as a spec defect, I flag this as an environment limitation only; it did not weaken any check I ran.

Counterexample / evidence:

```
None that survives the modeled domain. I attacked the spec with a faithful Python transliteration of the whole Solution.lean spec chain (quoteFor/escapeChar/quoteText/pyRepr/resolveVal/elideEntry/lineSep/placeEntry/rstripRun/layoutEntries/reprString) diffed byte-for-byte against the REAL repo code extracted verbatim by AST from the base_commit worktree (sklearn/base.py::_pprint unmodified, sklearn/model_selection/_split.py::_build_repr with the gold hunk textually applied). Results, all zero disagreements on the modeled domain: (a) 130,000 randomized inputs across 6 seeds over a domain deliberately WIDER than G-CONF's (full 0-127 ASCII values, quote/backslash/control-heavy strings, empty and 20-char class names, huge/negative ints, keys absent from both maps) with 18,277 wrapped and 5,869 elided outputs, so both layout branches were genuinely exercised; (b) EXHAUSTIVE escaping: all 16,513 strings of length <=2 over the full 128-char ASCII alphabet, plus all length-3 and length-4 strings over the quote/backslash/control alphabet ('\"\\ a\t\n\r\x00\x1f\x7f\x0b) — quoteText(s) == Python repr(s) with 0 mismatches; (c) layout boundary sweep, className width 0..24 x first-entry width 0..89 x second-entry width, 13,500 cases, plus an 864-case 3-entry sweep — the >=75 wrap threshold, the 1+offset//2 indent parity, and the ',\n' separator all match exactly; (d) elision boundary exhaustive 480..540 chars — the >500 / take 300 / drop last 100 split matches exactly; (e) the per-line trailing-space rstrip leg matches on a wrapped layout ending in an empty-string value. Legs (b), (c), (d) and (e) are precisely the ones G-CONF cannot see, because its corpus draws only escape-free strings (so repr(s) == "'"+s+"'" by construction) — I confirmed the model is exact there anyway, which strengthens rather than refutes the bundle.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** ARTIFACT INTEGRITY (prerequisites, all pass):
- markers.same_spec(Solution.lean, Solution_prepatch.lean, lean) == True. Confirmed by diff: the ONLY divergence is inside impl-start/impl-end and proof-start/proof-end, both of which the spec-view projection elides. The prepatch impl comment ("Pre-patch behavior: ... renders as the null sentinel (`None`) rather than its real value") — which WOULD be flagged narration — is inside the elided impl region and therefore not consumer-visible. Verified by projecting spec_view() directly.
- scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry/admit).
- #print axioms correct_reprString -> [propext, Quot.sound]. No sorryAx; the proof is real, not fake.

MECHANICAL SCREEN: leakage.screen(Solution.lean, lean-tables, gold_patch, problem_statement) -> passed=True, zero hard failures, zero warnings. Judged against problem_statement ONLY; hints_text (which contains the literal gold diff for hunk 1) was NOT used as a screening excuse.

SUBSTANTIVE GOLD-RECONSTRUCTION TEST — I did not rely on the mechanical gate. Whitespace-normalized containment of every gold ADDED line against the spec view:
  'def __repr__(self):'                            -> absent
  'return _build_repr(self)'                       -> absent
  "if value is None and hasattr(self, 'cvargs'):"  -> absent
  'value = self.cvargs.get(key, None)'             -> absent
No gold line is recoverable.

SYMBOL SWEEP (case-insensitive, over the projected spec view): cvargs, _build_repr/build_repr, _RepeatedSplits/RepeatedSplits, RepeatedKFold, RepeatedStratifiedKFold, __repr__, _split.py, _split, model_selection, sklearn, getattr, hasattr, _pprint, get_params, estimator, DeprecationWarning, KFold — ALL absent. Sole hit for 'self.' was the substring in the prose 'itself. -/' (lexer false positive, not an identifier). _patch_changed_symbols yields {build_repr, get_n_splits, repr}; none appears in a spec-view identifier or comment.

F2P-VALUE SWEEP: n_splits, n_repeats, random_state, =5, =10, =2, =6 — all absent. The spec view names no concrete parameter and no expected repr value, so the F2P assertion strings cannot be read off it.

HUNK-1 (the __repr__ routing edit) is the part the problem_statement's "Actual Results" (the `<... object at 0x...>` form) points at, and it is the harder half of the localization. Concept sweep for rout*, inherit, subclass, default, 'object at', address, 'base class', dunder — all absent. The spec view gives the solver no help finding that `_RepeatedSplits` lacks `__repr__`; that localization work is fully preserved. This is strong evidence against gold reconstruction.

### JUDGMENT ON THE CLOSEST CALLS (the two lines a leak finding would have to rest on):
1. Docstring para 1: "...otherwise, when the object also carries an auxiliary parameter map, the entry of that name in that map is used". This IS the abstract behavioral content of gold hunk 2. But SPEC_GUIDE Lean §6 mandates exactly this treatment: "State the abstract desired behavior; never the edit or the diagnosis," with the guide's own worked example being "write 'a standard-library HTML entity decoder,' not html.unescape." Rendering `self.cvargs` as "an auxiliary parameter map" is the doctrine-sanctioned de-naming, not a leak. In modes 1/2 the spec view IS the contract of the corrected behavior; a spec forbidden from stating the behavior it specifies could not exist.
2. Docstring closing: "This guarantees that a parameter held only in the auxiliary map ... is rendered with its real value rather than the null sentinel." Examined specifically as candidate bug->fix MECHANISM narration and cleared: it is phrased forward-looking as a consequence of the specified contract ("This guarantees"), not as a defect report. It contains no _NARRATION vocabulary (no bug/fix/patch/previously/incorrectly/wrong/regression), asserts nothing about what the code used to do, and only restates the resolution rule already given in para 1. It is a property of the spec, not a diagnosis.

DILUTION, NOT CONCENTRATION: the bulk of the docstring (7-bit escaping, quote selection, 500-char elision to 300+ellipsis+100, the 75-column wrap and half-offset indent, per-line rstrip) specifies _pprint, which the gold patch does NOT touch. Describing unchanged callee behavior is not the edit, and it buries rather than highlights the one-clause fallback.

SCOPE DISCIPLINE: meta.json records G-PANEL-2 (faithfulness) = fail. That is a different attacker's finding on a different question; I deliberately did not import it into this verdict, and it does not bear on leakage. My lane is leakage/gold-reconstruction only.

CONCLUSION: no gold-diff line, no patched file/module path, no patched symbol in identifiers or prose, no bug->fix narration, no F2P parameter names or values, and hunk-1's localization entirely withheld. The spec view states abstract corrected behavior with every repo identifier de-named, per SPEC_GUIDE Lean §6. G-LEAK relaxation is neither claimed nor needed. NO-LEAKAGE.

- markers.same_spec(Solution.lean, Solution_prepatch.lean, lean) == True. Confirmed by diff: the ONLY divergence is inside impl-start/impl-end and proof-start/proof-end, both of which the spec-view projection elides. The prepatch impl comment ("Pre-patch behavior: ... renders as the null sentinel (`None`) rather than its real value") — which WOULD be flagged narration — is inside the elided impl region and therefore not consumer-visible. Verified by projecting spec_view() directly.
- scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry/admit).
- #print axioms correct_reprString -> [propext, Quot.sound]. No sorryAx; the proof is real, not fake.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.