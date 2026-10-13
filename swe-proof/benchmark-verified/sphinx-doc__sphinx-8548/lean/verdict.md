# P2 adversarial audit — sphinx-doc__sphinx-8548

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1_prepatch.lean`, `atk_2_owner_target.lean`, `atk_3_partial_head_only.lean`, `atk_4_boundary_drop_last.lean`, `atk_5_swapped_blocks.lean`, `atk_6_no_nskey_guard.lean`, `atk_7_empty_doc.lean`, `atk_8_reverse_chain.lean`, `atk_9_nskey_as_owner.lean`, `atk_10_last_wins.lean`, `atk_11_head_nskey_partial_fix.lean`, +1 more |

**Non-vacuity.** The positive control `ctl_foldl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec admissible wrong implementation verifies, so no attack patch was required by the protocol (patches={}). I nevertheless executed 8 real run_resolve runs against the official harness to test the model<->patch correspondence, which is where the only residual verify=/=>correct surface lives; all 8 completed and none produced a break. The nearest thing to a counterexample is the HISTORICAL owner-only rival (ClassAttribute(subject,...) inside the fixed per-class loop), which broke the PREVIOUS owner-less revision of this spec: re-encoded as atk_2_owner_target.lean it is now REJECTED (exit 1, semantic refutation closes), and its materialized patch is confirmed genuinely incorrect by the oracle (resolved=False, PASS_TO_PASS test_instance_variable fails). Verifier and oracle agree on it, which is the direction soundness requires.
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -154,9 +154,13 @@
     for name in cls.annNames do
       if name ∉ members.map MemberEntry.name then
         members := members ++ [⟨name, none, some cls.classKey⟩]
-    for entry in cls.attrDocs do
-      if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then
-        members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.classKey⟩]
+  match mro with
+  | [] => pure ()
+  | target :: _ =>
+    for entry in target.attrDocs do
+      if entry.fst = target.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then
+        members := members ++
+          [⟨entry.snd.fst, some entry.snd.snd, some target.classKey⟩]
   return members
 -- impl-end
 
```

Attack 2 — `atk_2_owner_target.lean` → rejected (same spec, does not verify — good)

```diff
@@ -149,6 +149,7 @@
 def implementation_gatherMemberDocs
     (mro : List ClassInfo) (initial : List MemberEntry) :
     List MemberEntry := Id.run do
+  let target : Option String := (mro.head?).map ClassInfo.classKey
   let mut members := initial
   for cls in mro do
     for name in cls.annNames do
@@ -156,7 +157,7 @@
         members := members ++ [⟨name, none, some cls.classKey⟩]
     for entry in cls.attrDocs do
       if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then
-        members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.classKey⟩]
+        members := members ++ [⟨entry.snd.fst, some entry.snd.snd, target⟩]
   return members
 -- impl-end
 
```

Attack 3 — `atk_3_partial_head_only.lean` → rejected (same spec, does not verify — good)

```diff
@@ -150,7 +150,7 @@
     (mro : List ClassInfo) (initial : List MemberEntry) :
     List MemberEntry := Id.run do
   let mut members := initial
-  for cls in mro do
+  for cls in mro.take 1 do
     for name in cls.annNames do
       if name ∉ members.map MemberEntry.name then
         members := members ++ [⟨name, none, some cls.classKey⟩]
```

Attack 4 — `atk_4_boundary_drop_last.lean` → rejected (same spec, does not verify — good)

```diff
@@ -150,7 +150,7 @@
     (mro : List ClassInfo) (initial : List MemberEntry) :
     List MemberEntry := Id.run do
   let mut members := initial
-  for cls in mro do
+  for cls in mro.take (mro.length - 1) do
     for name in cls.annNames do
       if name ∉ members.map MemberEntry.name then
         members := members ++ [⟨name, none, some cls.classKey⟩]
```

Attack 5 — `atk_5_swapped_blocks.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,12 +151,12 @@
     List MemberEntry := Id.run do
   let mut members := initial
   for cls in mro do
+    for entry in cls.attrDocs do
+      if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then
+        members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.classKey⟩]
     for name in cls.annNames do
       if name ∉ members.map MemberEntry.name then
         members := members ++ [⟨name, none, some cls.classKey⟩]
-    for entry in cls.attrDocs do
-      if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then
-        members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.classKey⟩]
   return members
 -- impl-end
 
```

Attack 6 — `atk_6_no_nskey_guard.lean` → rejected (same spec, does not verify — good)

```diff
@@ -155,7 +155,7 @@
       if name ∉ members.map MemberEntry.name then
         members := members ++ [⟨name, none, some cls.classKey⟩]
     for entry in cls.attrDocs do
-      if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then
+      if entry.snd.fst ∉ members.map MemberEntry.name then
         members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.classKey⟩]
   return members
 -- impl-end
```

Attack 7 — `atk_7_empty_doc.lean` → rejected (same spec, does not verify — good)

```diff
@@ -153,7 +153,7 @@
   for cls in mro do
     for name in cls.annNames do
       if name ∉ members.map MemberEntry.name then
-        members := members ++ [⟨name, none, some cls.classKey⟩]
+        members := members ++ [⟨name, some "", some cls.classKey⟩]
     for entry in cls.attrDocs do
       if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then
         members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.classKey⟩]
```

Attack 8 — `atk_8_reverse_chain.lean` → rejected (same spec, does not verify — good)

```diff
@@ -150,7 +150,7 @@
     (mro : List ClassInfo) (initial : List MemberEntry) :
     List MemberEntry := Id.run do
   let mut members := initial
-  for cls in mro do
+  for cls in mro.reverse do
     for name in cls.annNames do
       if name ∉ members.map MemberEntry.name then
         members := members ++ [⟨name, none, some cls.classKey⟩]
```

Attack 9 — `atk_9_nskey_as_owner.lean` → rejected (same spec, does not verify — good)

```diff
@@ -153,10 +153,10 @@
   for cls in mro do
     for name in cls.annNames do
       if name ∉ members.map MemberEntry.name then
-        members := members ++ [⟨name, none, some cls.classKey⟩]
+        members := members ++ [⟨name, none, some cls.nsKey⟩]
     for entry in cls.attrDocs do
       if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then
-        members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.classKey⟩]
+        members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.nsKey⟩]
   return members
 -- impl-end
 
```

Attack 10 — `atk_10_last_wins.lean` → rejected (same spec, does not verify — good)

```diff
@@ -155,7 +155,7 @@
       if name ∉ members.map MemberEntry.name then
         members := members ++ [⟨name, none, some cls.classKey⟩]
     for entry in cls.attrDocs do
-      if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then
+      if entry.fst = cls.nsKey then
         members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.classKey⟩]
   return members
 -- impl-end
```

Attack 11 — `atk_11_head_nskey_partial_fix.lean` → rejected (same spec, does not verify — good)

```diff
@@ -149,13 +149,14 @@
 def implementation_gatherMemberDocs
     (mro : List ClassInfo) (initial : List MemberEntry) :
     List MemberEntry := Id.run do
+  let targetNs : Option String := (mro.head?).map ClassInfo.nsKey
   let mut members := initial
   for cls in mro do
     for name in cls.annNames do
       if name ∉ members.map MemberEntry.name then
         members := members ++ [⟨name, none, some cls.classKey⟩]
     for entry in cls.attrDocs do
-      if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then
+      if some entry.fst = targetNs ∧ entry.snd.fst ∉ members.map MemberEntry.name then
         members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.classKey⟩]
   return members
 -- impl-end
```

Attack 12 — `atk_12_abort_on_empty.lean` → rejected (same spec, does not verify — good)

```diff
@@ -154,6 +154,8 @@
     for name in cls.annNames do
       if name ∉ members.map MemberEntry.name then
         members := members ++ [⟨name, none, some cls.classKey⟩]
+    if cls.attrDocs = [] then
+      break
     for entry in cls.attrDocs do
       if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then
         members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.classKey⟩]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctl_foldl.lean`

```lean
import Mathlib
-- imports-end

/-!
Collecting a class's documented member attributes across its inheritance chain.

A class's documentation lists, among other things, its *member attributes*: names
that stand for per-instance data rather than for a value held by the class itself.
Two sources contribute them. A class body may *declare* such a member by
annotating it (`attr : int`), which supplies a name but no documentation at all.
A class body may also *document* one by attaching a comment-style docstring to an
assignment (`self.attr = …  #: doc`); the analysis of the module that defines the
class records every such attribute under a search key pairing a *namespace* — the
qualified name of the class the attribute belongs to — with the attribute name.

To document a class we walk its inheritance chain, the class itself first and then
its base classes in order. For each class on the chain we consult, in this order,
that class's own annotation-declared names and then the attributes recorded under
*that* class's own namespace; either kind is added to the member table only if a
member of that name is not already present. Because the chain is walked
most-derived first under this first-occurrence-wins rule, a name introduced only
by a base class is still picked up — this is what lets an *inherited* attribute
appear in a derived class's documentation — while a name that a class nearer the
front of the chain also supplies keeps that nearer occurrence.

Consulting each class's two sources together, one class at a time, is what settles
the case where a name is declared by one class on the chain and documented by
another: the class nearer the front of the chain wins, with whichever of the two
kinds it supplies. A bare declaration therefore does not pre-empt documentation
recorded for a class ahead of it on the chain.

Collecting a member is not only a decision about *whether* the name belongs in the
table. Each entry also records **which class supplied it**, and for either kind of
source that class is the one being visited when the entry was made: the class whose
own annotation declared the name, or the class whose own namespace the recorded
attribute matched — never the class the documentation was requested for. That
recorded class is observable and load-bearing: a reader of the table asks it which
members a class supplies *itself*, as against the ones it only takes over from an
ancestor, so attributing an ancestor's member to the class being documented is a
different table even when the names and documentation are identical. A class's own
namespace *key* and its *identity* are two different data: the key is the name an
entry must be recorded under to belong to the class, while the identity is the
class itself, and two classes on one chain may share a qualified name and still be
different classes.

We start from `initial`, the member table the earlier collection passes already
populated, and return the table after the chain walk. The table is an association
list, in insertion order, from member name to its documentation and the class that
supplied it: the documentation is `none` for a member that was only declared and
`some doc` for one whose docstring was recorded, and the supplying class is `none`
for a member the earlier passes attributed to no class at all.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. Each chain member's identity,
-- namespace key, annotation-declared names and recorded documented attributes are
-- INPUTS to the modeled function (`ClassInfo.classKey` / `ClassInfo.nsKey` /
-- `ClassInfo.annNames` / `ClassInfo.attrDocs`), and the inheritance chain is an
-- input as well; the collection behavior itself is modeled deeply in the `pure`
-- region. Hence no `opaque`/`axiom` declarations.
-- axioms-end

-- pure-start
/-- One class on the inheritance chain, as far as this collection pass is
concerned: its own identity, its own namespace key, the names it declares by
annotation alone, and the documented attributes recorded for the module that
defines it. Each documented attribute is a triple `(entry namespace, attribute
name, docstring)`. -/
structure ClassInfo where
  /-- The class's own identity, distinct from every other class on the chain. This
  is what a member the class supplies records as its supplier. -/
  classKey : String
  /-- The class's own namespace key (its qualified name): the namespace a recorded
  attribute must carry to belong to this class. -/
  nsKey    : String
  /-- The names this class declares by annotation alone. Such a member carries a
  name but no documentation. -/
  annNames : List String
  /-- The documented attributes recorded for this class's module: triples of
  `(entry namespace, attribute name, docstring)`. -/
  attrDocs : List (String × String × String)
deriving Repr, Inhabited

/-- One entry of the member table. -/
structure MemberEntry where
  /-- The member's name. The table is filed under this name and the entry carries
  it: one datum, not two. -/
  name  : String
  /-- The member's documentation: `none` for a member that was only declared,
  `some doc` for one whose docstring was recorded. -/
  doc   : Option String
  /-- The identity of the class that supplied this member, `none` for a member no
  class is recorded for. -/
  owner : Option String
deriving Repr, DecidableEq, Inhabited

/-- Fold one class's annotation-declared names into the member table. Such a name
is added iff no member of that name is already present (first occurrence wins),
with no documentation and with this class recorded as its supplier. -/
def addAnnotations (owner : String) :
    List String → List MemberEntry → List MemberEntry
  | [], members => members
  | name :: rest, members =>
      addAnnotations owner rest
        (if name ∉ members.map MemberEntry.name then
           members ++ [⟨name, none, some owner⟩]
         else members)

/-- Fold one class's documented attributes into the member table. An attribute is
added iff its recorded namespace is exactly this class's own namespace key and no
member of that name is already present (first occurrence wins), with its docstring
and with this class recorded as its supplier. -/
def addEntries (nsKey owner : String) :
    List (String × String × String) → List MemberEntry → List MemberEntry
  | [], members => members
  | entry :: rest, members =>
      addEntries nsKey owner rest
        (if entry.fst = nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then
           members ++ [⟨entry.snd.fst, some entry.snd.snd, some owner⟩]
         else members)

/-- Walk the inheritance chain, most-derived first, folding each class's two
sources into the member table one class at a time: that class's
annotation-declared names first, then the attributes recorded under its own
namespace. Each entry either fold makes records the class being visited as the
member's supplier. -/
def gatherMemberDocs : List ClassInfo → List MemberEntry → List MemberEntry
  | [], members => members
  | cls :: rest, members =>
      gatherMemberDocs rest
        (addEntries cls.nsKey cls.classKey cls.attrDocs
          (addAnnotations cls.classKey cls.annNames members))
-- pure-end

-- post-conditions-start
/-- The member table after the inheritance-chain walk. `mro` is the chain
(most-derived first) and `initial` is the table the earlier passes already
populated. The result is exactly the table obtained by walking the whole chain,
adding for each class in turn its annotation-declared names and then its own
recorded documented attributes — each with the visited class recorded as its
supplier — under a first-occurrence-wins rule. -/
def problem_spec_gatherMemberDocs
    (mro : List ClassInfo) (initial : List MemberEntry)
    (result : List MemberEntry) : Prop :=
  result = gatherMemberDocs mro initial
-- post-conditions-end

-- impl-start
def implementation_gatherMemberDocs
    (mro : List ClassInfo) (initial : List MemberEntry) :
    List MemberEntry :=
  mro.foldl
    (fun members cls =>
      cls.attrDocs.foldl
        (fun ms e =>
          if e.fst = cls.nsKey ∧ e.snd.fst ∉ ms.map MemberEntry.name then
            ms ++ [⟨e.snd.fst, some e.snd.snd, some cls.classKey⟩]
          else ms)
        (cls.annNames.foldl
          (fun ms n =>
            if n ∉ ms.map MemberEntry.name then
              ms ++ [⟨n, none, some cls.classKey⟩]
            else ms)
          members))
    initial
-- impl-end

-- proof-start
/-- The `foldl` over a class's annotation-declared names is `addAnnotations`. -/
theorem ctl_ann (owner : String) (names : List String) :
    ∀ (members : List MemberEntry),
      names.foldl (fun ms n =>
        if n ∉ ms.map MemberEntry.name then ms ++ [⟨n, none, some owner⟩] else ms)
        members = addAnnotations owner names members := by
  induction names with
  | nil => intro members; rfl
  | cons a as ih =>
    intro members
    simp only [List.foldl_cons, addAnnotations, ih]

/-- The `foldl` over a class's documented attributes is `addEntries`. -/
theorem ctl_entries (nsKey owner : String)
    (entries : List (String × String × String)) :
    ∀ (members : List MemberEntry),
      entries.foldl (fun ms e =>
        if e.fst = nsKey ∧ e.snd.fst ∉ ms.map MemberEntry.name then
          ms ++ [⟨e.snd.fst, some e.snd.snd, some owner⟩] else ms)
        members = addEntries nsKey owner entries members := by
  induction entries with
  | nil => intro members; rfl
  | cons a as ih =>
    intro members
    simp only [List.foldl_cons, addEntries, ih]

/-- One chain step of the `foldl` is one step of `gatherMemberDocs`'s body. -/
theorem ctl_step (cls : ClassInfo) (members : List MemberEntry) :
    cls.attrDocs.foldl
      (fun ms e =>
        if e.fst = cls.nsKey ∧ e.snd.fst ∉ ms.map MemberEntry.name then
          ms ++ [⟨e.snd.fst, some e.snd.snd, some cls.classKey⟩] else ms)
      (cls.annNames.foldl
        (fun ms n =>
          if n ∉ ms.map MemberEntry.name then
            ms ++ [⟨n, none, some cls.classKey⟩] else ms) members)
    = addEntries cls.nsKey cls.classKey cls.attrDocs
        (addAnnotations cls.classKey cls.annNames members) := by
  rw [ctl_ann, ctl_entries]

/-- The `foldl` over the chain is `gatherMemberDocs`. -/
theorem ctl_chain (mro : List ClassInfo) :
    ∀ (members : List MemberEntry),
      mro.foldl (fun ms cls =>
        cls.attrDocs.foldl
          (fun ms e =>
            if e.fst = cls.nsKey ∧ e.snd.fst ∉ ms.map MemberEntry.name then
              ms ++ [⟨e.snd.fst, some e.snd.snd, some cls.classKey⟩] else ms)
          (cls.annNames.foldl
            (fun ms n =>
              if n ∉ ms.map MemberEntry.name then
                ms ++ [⟨n, none, some cls.classKey⟩] else ms) ms))
        members = gatherMemberDocs mro members := by
  induction mro with
  | nil => intro members; rfl
  | cons a as ih =>
    intro members
    rw [List.foldl_cons, ctl_step, ih, gatherMemberDocs]

theorem correct_gatherMemberDocs :
    ∀ (mro : List ClassInfo) (initial : List MemberEntry),
      problem_spec_gatherMemberDocs mro initial
        (implementation_gatherMemberDocs mro initial) := by
  intro mro initial
  unfold problem_spec_gatherMemberDocs implementation_gatherMemberDocs
  exact ctl_chain mro initial
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC + ADMISSIBILITY: all 12 attacks + ctl_foldl.lean return same_spec=True against frozen Solution.lean (sha256 9d65cefc0478387974c4076ffffbd79ee1a257df527343096a38dc66dc940f28) and unsound_evasions=[] (admissible: no new axiom, no sorry/admit/native_decide, obligation statement byte-identical). Checked with swebench_unified.markers.same_spec + swebench_unified.variant_scope.unsound_evasions.

**COMMAND FOR EVERY LEAN FILE:** `bash scripts/lean_verify.sh <path>` from swe-proof, run 4-at-a-time as concurrent background jobs (runbatch.sh).

ATTACKS - ALL 12 REJECTED (exit 1): 1 atk_1_prepatch.lean - THE PREPATCH BUG re-encoded: annotation pass over the whole chain first, then the docstring pass for the HEAD namespace only, credited to the target. exit 1. 2 atk_2_owner_target.lean - the historical break: fixed loop shape, every documented attribute credited to the TARGET class. exit 1 (NOW rejected = the owner repair working).

3 atk_3_partial_head_only.lean - PARTIAL DOMAIN: mro.take 1. exit 1. 4 atk_4_boundary_drop_last.lean - BOUNDARY: mro.take (length-1). exit 1. 5 atk_5_swapped_blocks.lean - CONTROL-FLOW EFFECT: docstring block before annotation block per class. exit 1. 6 atk_6_no_nskey_guard.lean - UNGROUNDED ORACLE: drops entry.fst = cls.nsKey, collects foreign-namespace entries. exit 1. 7 atk_7_empty_doc.lean - DOC BOUNDARY: annotation member recorded some "" instead of none. exit 1. 8 atk_8_reverse_chain.lean - CHAIN DIRECTION: mro.reverse (least-derived first). exit 1. 9 atk_9_nskey_as_owner.lean - IDENTITY/KEY CONFLATION: records nsKey (`__qualname__`) as owner instead of classKey identity. exit 1. 10 atk_10_last_wins.lean - drops the key-absence guard in the docstring pass (last-wins). exit 1. 11 atk_11_head_nskey_partial_fix.lean - REALISTIC PARTIAL FIX: structural half applied, predicate still keys on the TARGET namespace. exit 1. 12 atk_12_abort_on_empty.lean - ERROR-PATH: a class with no attrDocs aborts the walk, where the real except (AttributeError, PycodeError): pass continues. exit 1.

REJECTIONS ARE SEMANTIC, NOT TACTIC-BRITTLE. lean_verify reports only 'Type mismatch' at the carried `exact outer_helper` for each, which alone shows just that the gold tactic stopped matching. So for EVERY attack I built <name>`__REFUTE`.lean replacing the proof region with `example: not (problem_spec... (implementation...)):= by unfold...; decide`. ALL 12 REFUTE FILES EXIT 0 - each impl is PROVABLY wrong on a concrete witness, so no proof of correct_gatherMemberDocs can exist for it. Witnesses: atk_1/2/3/4/9/11/12 [<B,Bar,[],[]>,<F,Foo,[],[(Foo,attr1,doc)]>]; atk_5/7 [<C,Cls,[x],[(Cls,x,dx)]>]; atk_6 [<G,Gee,[],[(Other,z,dz)]>] foreign ns; atk_8/10 [<D,Der,[],[(Der,x,dx)]>,<E,Bse,[],[(Bse,x,bx)]>].

**POSITIVE CONTROL:** ctl_foldl.lean exit 0 - structurally RESHAPED but extensionally correct (List.foldl over the chain and over each source instead of the mutable for-loop), reproved with three NEW lemmas (ctl_ann / ctl_entries / ctl_step / ctl_chain). Not a copy of the gold tactic: the gold `exact outer_helper` cannot close it. My first attempt failed (exit 1, ih not applicable to the advanced accumulator) and I repaired the induction rather than weakening the control.

**AXIOMS:** #print axioms correct_gatherMemberDocs - axcheck_gold.lean => [propext, Quot.sound]; axcheck_ctl.lean => [propext]. Both exit 0. Clean: no sorryAx, no custom axiom.

A-LEG AUDIT (the leg I was told to concentrate on). The axioms region declares NO axiom/opaque at all - grep for '^\s*(axiom|opaque)' over Solution.lean returns ZERO matches, and G-AX is a skip stub. So there are NO A-consumed and NO A-reference legs to validate; the A-leg surface is empty by construction, and the #print axioms result independently confirms no assumption leaked in. refinement.md's 13 rows tally 5 R + 8 I with ZERO kind-3 and zero untagged rows ('A-consumed'/'A-reference' appear only in the legend at lines 4-6). Every leg is R or I.

WHY THE LEAN-SIDE ATTACK SPACE IS PROVABLY EMPTY - and where I therefore spent the real effort. The postcondition is EXACT functional equality on TOTAL inputs: `result = gatherMemberDocs mro initial`, with no pre-conditions region at all (region_names has 'pre-conditions' but Solution.lean declares none, so nothing can be made vacuous). Any impl that verifies is therefore extensionally THE gold function pointwise - no wrong impl can verify, which is exactly what all 12 rejections + 12 semantic refutations demonstrate. I confirmed the shape reaches the degenerate case too: echo_oracle.lean (impl:= gatherMemberDocs mro initial, proof `rfl`) verifies exit 0, and is correctly an ECHO (extensionally gold), not a weakness. Consequently the ONLY residual verify=/=>correct surface is the MODEL<->PATCH CORRESPONDENCE: a patch whose faithful Lean model is byte-identical to gold's (because it changes only something the carrier projects away or folds into an INPUT) would verify with gold's own proof, yet might not resolve. I attacked that surface directly with 8 EXECUTED run_resolve runs.

### EXECUTED RESOLVE RUNS (official harness, swebench_unified.harness.run_resolve; all completed=True):
  GOLD (control)              resolved=True  F2P 1/1 P2P 5/5  <- oracle is FIT on this instance
  V1_value_None_docbranch     resolved=True  F2P 1/1 P2P 5/5
  V2_value_None_annbranch     resolved=True  F2P 1/1 P2P 5/5
  V4_value_is_string          resolved=True  F2P 1/1 P2P 5/5
  V5_modname_from_subject     resolved=True  F2P 1/1 P2P 5/5
  V6_qualname_to_name         resolved=True  F2P 1/1 P2P 5/5
  V7_keep_analyzer_param      resolved=True  F2P 1/1 P2P 5/5
  ATK2_owner_target           resolved=False F2P 1/1 P2P 4/5, fails test_instance_variable  <- discriminating power
Patches at patch_<name>.diff, each built as a REAL `git diff` off base_commit inside the instance container (so hunk counts are guaranteed correct - my first hand-edited V7 diff had broken hunk headers and I discarded it rather than ship an unapplicable patch). JSON reports at resolve_<name>.json.

Each V* variant keeps the faithful Lean model BYTE-IDENTICAL to gold's, so each verifies unchanged; all six RESOLVE, i.e. they are correct echoes and correctly NOT submitted as attacks. Two deserve explicit note because they are the strongest correspondence probes:
  - V6 (`__qualname__` -> `__name__`, refinement.md row 2 / the nsKey R-leg) is a GENUINE behavioral divergence, not a no-op: measured in-container on a nested class, attr_docs is keyed ('Outer.Inner','n'), gold collects n with docstring 'inner n doc\n', V6 collects NOTHING. The carrier cannot distinguish them because nsKey is an INPUT. It still resolves, so the F2P/P2P suite does not reach nested classes - the model is STRICTER than the tests require, never weaker. mapping.md already pins nsKey to `__qualname__` and G-CONF drives a shared-`__qualname__` shape, so the modeling boundary is documented, not accidental.
  - V7 (keep the `analyzer` parameter and the original `__init__`.py call site) resolves: the signature change is genuinely inert, matching the carrier not modeling it.
The projected-away ClassAttribute.value field was attacked in BOTH writes (V1 docstring branch, V2 annotation branch, V4 a real non-INSTANCEATTR string that flips `member is INSTANCEATTR` downstream at `__init__`.py:696): all three resolve 6/6, so refinement.md's 'value is frame' claim HOLDS BY MEASUREMENT rather than by assertion.

ONE VARIANT DID FAIL, AND IT CONFIRMS THE SPEC RATHER THAN BREAKING IT: dropping PycodeError from the except clause (V8) fails 5 of 6 tests in-container. Its faithful model is NOT gold's - an unanalyzable module aborts the walk instead of contributing attrDocs=[] - and that is precisely atk_12_abort_on_empty.lean, which the spec REJECTS (exit 1, refutation exit 0). So the one behavioral break I found in this dimension is already caught by the spec. I did not submit it as an attack patch because its attack file does not verify.

**PREPATCH REPRODUCED:** yes - atk_1_prepatch.lean re-encodes the base-commit shape (from Solution_prepatch.lean's impl region, whose pure/spec regions I diffed as identical to gold's) and is rejected exit 1, with atk_1_prepatch__REFUTE.lean exit 0 proving it semantically wrong on the FAIL_TO_PASS shape [<B,Bar,[],[]>,<F,Foo,[],[(Foo,attr1,doc)]>] - the inherited attribute the real bug drops.

**CONCLUSION:** 12 distinct admissible attacks across all requested families (prepatch, owner-only, partial-domain, boundary, two control-flow-effect, ungrounded-oracle, doc-boundary, chain-direction, identity/key conflation, last-wins, realistic-partial-fix, error-path) ALL rejected with machine-checked SEMANTIC refutations; positive control verifies with clean axioms; zero A-legs and zero kind-3 legs, confirmed by grep and by #print axioms; the model<->patch correspondence probed with 8 completed official resolve runs including a fit control that resolves and a rival that does not. No implementation with a closing clean-axiom proof has a faithful patch that fails to resolve. verify => correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1_prepatch.lean`, `atk_2_owner_target.lean`, `atk_3_partial_head_only.lean`, `atk_4_boundary_drop_last.lean`, `atk_5_swapped_blocks.lean`, `atk_6_no_nskey_guard.lean`, `atk_7_empty_doc.lean`, `atk_8_reverse_chain.lean`, `atk_9_nskey_as_owner.lean`, `atk_10_last_wins.lean`, `atk_11_head_nskey_partial_fix.lean`, +1 more |

**Non-vacuity.** The positive control `ctl_foldl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec admissible wrong implementation verifies, so no attack patch was required by the protocol (patches={}). I nevertheless executed 8 real run_resolve runs against the official harness to test the model<->patch correspondence, which is where the only residual verify=/=>correct surface lives; all 8 completed and none produced a break. The nearest thing to a counterexample is the HISTORICAL owner-only rival (ClassAttribute(subject,...) inside the fixed per-class loop), which broke the PREVIOUS owner-less revision of this spec: re-encoded as atk_2_owner_target.lean it is now REJECTED (exit 1, semantic refutation closes), and its materialized patch is confirmed genuinely incorrect by the oracle (resolved=False, PASS_TO_PASS test_instance_variable fails). Verifier and oracle agree on it, which is the direction soundness requires.
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 12 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_owner_target.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_partial_head_only.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_boundary_drop_last.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_swapped_blocks.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_no_nskey_guard.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_empty_doc.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_reverse_chain.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_nskey_as_owner.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_last_wins.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_head_nskey_partial_fix.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_abort_on_empty.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctl_foldl.lean`

```lean
import Mathlib
-- imports-end

/-!
Collecting a class's documented member attributes across its inheritance chain.

A class's documentation lists, among other things, its *member attributes*: names
that stand for per-instance data rather than for a value held by the class itself.
Two sources contribute them. A class body may *declare* such a member by
annotating it (`attr : int`), which supplies a name but no documentation at all.
A class body may also *document* one by attaching a comment-style docstring to an
assignment (`self.attr = …  #: doc`); the analysis of the module that defines the
class records every such attribute under a search key pairing a *namespace* — the
qualified name of the class the attribute belongs to — with the attribute name.

To document a class we walk its inheritance chain, the class itself first and then
its base classes in order. For each class on the chain we consult, in this order,
that class's own annotation-declared names and then the attributes recorded under
*that* class's own namespace; either kind is added to the member table only if a
member of that name is not already present. Because the chain is walked
most-derived first under this first-occurrence-wins rule, a name introduced only
by a base class is still picked up — this is what lets an *inherited* attribute
appear in a derived class's documentation — while a name that a class nearer the
front of the chain also supplies keeps that nearer occurrence.

Consulting each class's two sources together, one class at a time, is what settles
the case where a name is declared by one class on the chain and documented by
another: the class nearer the front of the chain wins, with whichever of the two
kinds it supplies. A bare declaration therefore does not pre-empt documentation
recorded for a class ahead of it on the chain.

Collecting a member is not only a decision about *whether* the name belongs in the
table. Each entry also records **which class supplied it**, and for either kind of
source that class is the one being visited when the entry was made: the class whose
own annotation declared the name, or the class whose own namespace the recorded
attribute matched — never the class the documentation was requested for. That
recorded class is observable and load-bearing: a reader of the table asks it which
members a class supplies *itself*, as against the ones it only takes over from an
ancestor, so attributing an ancestor's member to the class being documented is a
different table even when the names and documentation are identical. A class's own
namespace *key* and its *identity* are two different data: the key is the name an
entry must be recorded under to belong to the class, while the identity is the
class itself, and two classes on one chain may share a qualified name and still be
different classes.

We start from `initial`, the member table the earlier collection passes already
populated, and return the table after the chain walk. The table is an association
list, in insertion order, from member name to its documentation and the class that
supplied it: the documentation is `none` for a member that was only declared and
`some doc` for one whose docstring was recorded, and the supplying class is `none`
for a member the earlier passes attributed to no class at all.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. Each chain member's identity,
-- namespace key, annotation-declared names and recorded documented attributes are
-- INPUTS to the modeled function (`ClassInfo.classKey` / `ClassInfo.nsKey` /
-- `ClassInfo.annNames` / `ClassInfo.attrDocs`), and the inheritance chain is an
-- input as well; the collection behavior itself is modeled deeply in the `pure`
-- region. Hence no `opaque`/`axiom` declarations.
-- axioms-end

-- pure-start
/-- One class on the inheritance chain, as far as this collection pass is
concerned: its own identity, its own namespace key, the names it declares by
annotation alone, and the documented attributes recorded for the module that
defines it. Each documented attribute is a triple `(entry namespace, attribute
name, docstring)`. -/
structure ClassInfo where
  /-- The class's own identity, distinct from every other class on the chain. This
  is what a member the class supplies records as its supplier. -/
  classKey : String
  /-- The class's own namespace key (its qualified name): the namespace a recorded
  attribute must carry to belong to this class. -/
  nsKey    : String
  /-- The names this class declares by annotation alone. Such a member carries a
  name but no documentation. -/
  annNames : List String
  /-- The documented attributes recorded for this class's module: triples of
  `(entry namespace, attribute name, docstring)`. -/
  attrDocs : List (String × String × String)
deriving Repr, Inhabited

/-- One entry of the member table. -/
structure MemberEntry where
  /-- The member's name. The table is filed under this name and the entry carries
  it: one datum, not two. -/
  name  : String
  /-- The member's documentation: `none` for a member that was only declared,
  `some doc` for one whose docstring was recorded. -/
  doc   : Option String
  /-- The identity of the class that supplied this member, `none` for a member no
  class is recorded for. -/
  owner : Option String
deriving Repr, DecidableEq, Inhabited

/-- Fold one class's annotation-declared names into the member table. Such a name
is added iff no member of that name is already present (first occurrence wins),
with no documentation and with this class recorded as its supplier. -/
def addAnnotations (owner : String) :
    List String → List MemberEntry → List MemberEntry
  | [], members => members
  | name :: rest, members =>
      addAnnotations owner rest
        (if name ∉ members.map MemberEntry.name then
           members ++ [⟨name, none, some owner⟩]
         else members)

/-- Fold one class's documented attributes into the member table. An attribute is
added iff its recorded namespace is exactly this class's own namespace key and no
member of that name is already present (first occurrence wins), with its docstring
and with this class recorded as its supplier. -/
def addEntries (nsKey owner : String) :
    List (String × String × String) → List MemberEntry → List MemberEntry
  | [], members => members
  | entry :: rest, members =>
      addEntries nsKey owner rest
        (if entry.fst = nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then
           members ++ [⟨entry.snd.fst, some entry.snd.snd, some owner⟩]
         else members)

/-- Walk the inheritance chain, most-derived first, folding each class's two
sources into the member table one class at a time: that class's
annotation-declared names first, then the attributes recorded under its own
namespace. Each entry either fold makes records the class being visited as the
member's supplier. -/
def gatherMemberDocs : List ClassInfo → List MemberEntry → List MemberEntry
  | [], members => members
  | cls :: rest, members =>
      gatherMemberDocs rest
        (addEntries cls.nsKey cls.classKey cls.attrDocs
          (addAnnotations cls.classKey cls.annNames members))
-- pure-end

-- post-conditions-start
/-- The member table after the inheritance-chain walk. `mro` is the chain
(most-derived first) and `initial` is the table the earlier passes already
populated. The result is exactly the table obtained by walking the whole chain,
adding for each class in turn its annotation-declared names and then its own
recorded documented attributes — each with the visited class recorded as its
supplier — under a first-occurrence-wins rule. -/
def problem_spec_gatherMemberDocs
    (mro : List ClassInfo) (initial : List MemberEntry)
    (result : List MemberEntry) : Prop :=
  result = gatherMemberDocs mro initial
-- post-conditions-end

-- impl-start
def implementation_gatherMemberDocs
    (mro : List ClassInfo) (initial : List MemberEntry) :
    List MemberEntry :=
  mro.foldl
    (fun members cls =>
      cls.attrDocs.foldl
        (fun ms e =>
          if e.fst = cls.nsKey ∧ e.snd.fst ∉ ms.map MemberEntry.name then
            ms ++ [⟨e.snd.fst, some e.snd.snd, some cls.classKey⟩]
          else ms)
        (cls.annNames.foldl
          (fun ms n =>
            if n ∉ ms.map MemberEntry.name then
              ms ++ [⟨n, none, some cls.classKey⟩]
            else ms)
          members))
    initial
-- impl-end

-- proof-start
/-- The `foldl` over a class's annotation-declared names is `addAnnotations`. -/
theorem ctl_ann (owner : String) (names : List String) :
    ∀ (members : List MemberEntry),
      names.foldl (fun ms n =>
        if n ∉ ms.map MemberEntry.name then ms ++ [⟨n, none, some owner⟩] else ms)
        members = addAnnotations owner names members := by
  induction names with
  | nil => intro members; rfl
  | cons a as ih =>
    intro members
    simp only [List.foldl_cons, addAnnotations, ih]

/-- The `foldl` over a class's documented attributes is `addEntries`. -/
theorem ctl_entries (nsKey owner : String)
    (entries : List (String × String × String)) :
    ∀ (members : List MemberEntry),
      entries.foldl (fun ms e =>
        if e.fst = nsKey ∧ e.snd.fst ∉ ms.map MemberEntry.name then
          ms ++ [⟨e.snd.fst, some e.snd.snd, some owner⟩] else ms)
        members = addEntries nsKey owner entries members := by
  induction entries with
  | nil => intro members; rfl
  | cons a as ih =>
    intro members
    simp only [List.foldl_cons, addEntries, ih]

/-- One chain step of the `foldl` is one step of `gatherMemberDocs`'s body. -/
theorem ctl_step (cls : ClassInfo) (members : List MemberEntry) :
    cls.attrDocs.foldl
      (fun ms e =>
        if e.fst = cls.nsKey ∧ e.snd.fst ∉ ms.map MemberEntry.name then
          ms ++ [⟨e.snd.fst, some e.snd.snd, some cls.classKey⟩] else ms)
      (cls.annNames.foldl
        (fun ms n =>
          if n ∉ ms.map MemberEntry.name then
            ms ++ [⟨n, none, some cls.classKey⟩] else ms) members)
    = addEntries cls.nsKey cls.classKey cls.attrDocs
        (addAnnotations cls.classKey cls.annNames members) := by
  rw [ctl_ann, ctl_entries]

/-- The `foldl` over the chain is `gatherMemberDocs`. -/
theorem ctl_chain (mro : List ClassInfo) :
    ∀ (members : List MemberEntry),
      mro.foldl (fun ms cls =>
        cls.attrDocs.foldl
          (fun ms e =>
            if e.fst = cls.nsKey ∧ e.snd.fst ∉ ms.map MemberEntry.name then
              ms ++ [⟨e.snd.fst, some e.snd.snd, some cls.classKey⟩] else ms)
          (cls.annNames.foldl
            (fun ms n =>
              if n ∉ ms.map MemberEntry.name then
                ms ++ [⟨n, none, some cls.classKey⟩] else ms) ms))
        members = gatherMemberDocs mro members := by
  induction mro with
  | nil => intro members; rfl
  | cons a as ih =>
    intro members
    rw [List.foldl_cons, ctl_step, ih, gatherMemberDocs]

theorem correct_gatherMemberDocs :
    ∀ (mro : List ClassInfo) (initial : List MemberEntry),
      problem_spec_gatherMemberDocs mro initial
        (implementation_gatherMemberDocs mro initial) := by
  intro mro initial
  unfold problem_spec_gatherMemberDocs implementation_gatherMemberDocs
  exact ctl_chain mro initial
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC + ADMISSIBILITY: all 12 attacks + ctl_foldl.lean return same_spec=True against frozen Solution.lean (sha256 9d65cefc0478387974c4076ffffbd79ee1a257df527343096a38dc66dc940f28) and unsound_evasions=[] (admissible: no new axiom, no sorry/admit/native_decide, obligation statement byte-identical). Checked with swebench_unified.markers.same_spec + swebench_unified.variant_scope.unsound_evasions.

**COMMAND FOR EVERY LEAN FILE:** `bash scripts/lean_verify.sh <path>` from swe-proof, run 4-at-a-time as concurrent background jobs (runbatch.sh).

ATTACKS - ALL 12 REJECTED (exit 1): 1 atk_1_prepatch.lean - THE PREPATCH BUG re-encoded: annotation pass over the whole chain first, then the docstring pass for the HEAD namespace only, credited to the target. exit 1. 2 atk_2_owner_target.lean - the historical break: fixed loop shape, every documented attribute credited to the TARGET class. exit 1 (NOW rejected = the owner repair working).

3 atk_3_partial_head_only.lean - PARTIAL DOMAIN: mro.take 1. exit 1. 4 atk_4_boundary_drop_last.lean - BOUNDARY: mro.take (length-1). exit 1. 5 atk_5_swapped_blocks.lean - CONTROL-FLOW EFFECT: docstring block before annotation block per class. exit 1. 6 atk_6_no_nskey_guard.lean - UNGROUNDED ORACLE: drops entry.fst = cls.nsKey, collects foreign-namespace entries. exit 1. 7 atk_7_empty_doc.lean - DOC BOUNDARY: annotation member recorded some "" instead of none. exit 1. 8 atk_8_reverse_chain.lean - CHAIN DIRECTION: mro.reverse (least-derived first). exit 1. 9 atk_9_nskey_as_owner.lean - IDENTITY/KEY CONFLATION: records nsKey (`__qualname__`) as owner instead of classKey identity. exit 1. 10 atk_10_last_wins.lean - drops the key-absence guard in the docstring pass (last-wins). exit 1. 11 atk_11_head_nskey_partial_fix.lean - REALISTIC PARTIAL FIX: structural half applied, predicate still keys on the TARGET namespace. exit 1. 12 atk_12_abort_on_empty.lean - ERROR-PATH: a class with no attrDocs aborts the walk, where the real except (AttributeError, PycodeError): pass continues. exit 1.

REJECTIONS ARE SEMANTIC, NOT TACTIC-BRITTLE. lean_verify reports only 'Type mismatch' at the carried `exact outer_helper` for each, which alone shows just that the gold tactic stopped matching. So for EVERY attack I built <name>`__REFUTE`.lean replacing the proof region with `example: not (problem_spec... (implementation...)):= by unfold...; decide`. ALL 12 REFUTE FILES EXIT 0 - each impl is PROVABLY wrong on a concrete witness, so no proof of correct_gatherMemberDocs can exist for it. Witnesses: atk_1/2/3/4/9/11/12 [<B,Bar,[],[]>,<F,Foo,[],[(Foo,attr1,doc)]>]; atk_5/7 [<C,Cls,[x],[(Cls,x,dx)]>]; atk_6 [<G,Gee,[],[(Other,z,dz)]>] foreign ns; atk_8/10 [<D,Der,[],[(Der,x,dx)]>,<E,Bse,[],[(Bse,x,bx)]>].

**POSITIVE CONTROL:** ctl_foldl.lean exit 0 - structurally RESHAPED but extensionally correct (List.foldl over the chain and over each source instead of the mutable for-loop), reproved with three NEW lemmas (ctl_ann / ctl_entries / ctl_step / ctl_chain). Not a copy of the gold tactic: the gold `exact outer_helper` cannot close it. My first attempt failed (exit 1, ih not applicable to the advanced accumulator) and I repaired the induction rather than weakening the control.

**AXIOMS:** #print axioms correct_gatherMemberDocs - axcheck_gold.lean => [propext, Quot.sound]; axcheck_ctl.lean => [propext]. Both exit 0. Clean: no sorryAx, no custom axiom.

A-LEG AUDIT (the leg I was told to concentrate on). The axioms region declares NO axiom/opaque at all - grep for '^\s*(axiom|opaque)' over Solution.lean returns ZERO matches, and G-AX is a skip stub. So there are NO A-consumed and NO A-reference legs to validate; the A-leg surface is empty by construction, and the #print axioms result independently confirms no assumption leaked in. refinement.md's 13 rows tally 5 R + 8 I with ZERO kind-3 and zero untagged rows ('A-consumed'/'A-reference' appear only in the legend at lines 4-6). Every leg is R or I.

WHY THE LEAN-SIDE ATTACK SPACE IS PROVABLY EMPTY - and where I therefore spent the real effort. The postcondition is EXACT functional equality on TOTAL inputs: `result = gatherMemberDocs mro initial`, with no pre-conditions region at all (region_names has 'pre-conditions' but Solution.lean declares none, so nothing can be made vacuous). Any impl that verifies is therefore extensionally THE gold function pointwise - no wrong impl can verify, which is exactly what all 12 rejections + 12 semantic refutations demonstrate. I confirmed the shape reaches the degenerate case too: echo_oracle.lean (impl:= gatherMemberDocs mro initial, proof `rfl`) verifies exit 0, and is correctly an ECHO (extensionally gold), not a weakness. Consequently the ONLY residual verify=/=>correct surface is the MODEL<->PATCH CORRESPONDENCE: a patch whose faithful Lean model is byte-identical to gold's (because it changes only something the carrier projects away or folds into an INPUT) would verify with gold's own proof, yet might not resolve. I attacked that surface directly with 8 EXECUTED run_resolve runs.

### EXECUTED RESOLVE RUNS (official harness, swebench_unified.harness.run_resolve; all completed=True):
  GOLD (control)              resolved=True  F2P 1/1 P2P 5/5  <- oracle is FIT on this instance
  V1_value_None_docbranch     resolved=True  F2P 1/1 P2P 5/5
  V2_value_None_annbranch     resolved=True  F2P 1/1 P2P 5/5
  V4_value_is_string          resolved=True  F2P 1/1 P2P 5/5
  V5_modname_from_subject     resolved=True  F2P 1/1 P2P 5/5
  V6_qualname_to_name         resolved=True  F2P 1/1 P2P 5/5
  V7_keep_analyzer_param      resolved=True  F2P 1/1 P2P 5/5
  ATK2_owner_target           resolved=False F2P 1/1 P2P 4/5, fails test_instance_variable  <- discriminating power
Patches at patch_<name>.diff, each built as a REAL `git diff` off base_commit inside the instance container (so hunk counts are guaranteed correct - my first hand-edited V7 diff had broken hunk headers and I discarded it rather than ship an unapplicable patch). JSON reports at resolve_<name>.json.

Each V* variant keeps the faithful Lean model BYTE-IDENTICAL to gold's, so each verifies unchanged; all six RESOLVE, i.e. they are correct echoes and correctly NOT submitted as attacks. Two deserve explicit note because they are the strongest correspondence probes:
  - V6 (`__qualname__` -> `__name__`, refinement.md row 2 / the nsKey R-leg) is a GENUINE behavioral divergence, not a no-op: measured in-container on a nested class, attr_docs is keyed ('Outer.Inner','n'), gold collects n with docstring 'inner n doc\n', V6 collects NOTHING. The carrier cannot distinguish them because nsKey is an INPUT. It still resolves, so the F2P/P2P suite does not reach nested classes - the model is STRICTER than the tests require, never weaker. mapping.md already pins nsKey to `__qualname__` and G-CONF drives a shared-`__qualname__` shape, so the modeling boundary is documented, not accidental.
  - V7 (keep the `analyzer` parameter and the original `__init__`.py call site) resolves: the signature change is genuinely inert, matching the carrier not modeling it.
The projected-away ClassAttribute.value field was attacked in BOTH writes (V1 docstring branch, V2 annotation branch, V4 a real non-INSTANCEATTR string that flips `member is INSTANCEATTR` downstream at `__init__`.py:696): all three resolve 6/6, so refinement.md's 'value is frame' claim HOLDS BY MEASUREMENT rather than by assertion.

ONE VARIANT DID FAIL, AND IT CONFIRMS THE SPEC RATHER THAN BREAKING IT: dropping PycodeError from the except clause (V8) fails 5 of 6 tests in-container. Its faithful model is NOT gold's - an unanalyzable module aborts the walk instead of contributing attrDocs=[] - and that is precisely atk_12_abort_on_empty.lean, which the spec REJECTS (exit 1, refutation exit 0). So the one behavioral break I found in this dimension is already caught by the spec. I did not submit it as an attack patch because its attack file does not verify.

**PREPATCH REPRODUCED:** yes - atk_1_prepatch.lean re-encodes the base-commit shape (from Solution_prepatch.lean's impl region, whose pure/spec regions I diffed as identical to gold's) and is rejected exit 1, with atk_1_prepatch__REFUTE.lean exit 0 proving it semantically wrong on the FAIL_TO_PASS shape [<B,Bar,[],[]>,<F,Foo,[],[(Foo,attr1,doc)]>] - the inherited attribute the real bug drops.

**CONCLUSION:** 12 distinct admissible attacks across all requested families (prepatch, owner-only, partial-domain, boundary, two control-flow-effect, ungrounded-oracle, doc-boundary, chain-direction, identity/key conflation, last-wins, realistic-partial-fix, error-path) ALL rejected with machine-checked SEMANTIC refutations; positive control verifies with clean axioms; zero A-legs and zero kind-3 legs, confirmed by grep and by #print axioms; the model<->patch correspondence probed with 8 completed official resolve runs including a fit control that resolves and a rival that does not. No implementation with a closing clean-axiom proof has a faithful patch that fails to resolve. verify => correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-2 (faithfulness-break) on sphinx-doc__sphinx-8548 / Solution.lean `gatherMemberDocs`. No divergence found between the modeled function and the real post-patch callee. Verdict FAITHFUL.

**REFERENCE DISCIPLINE.** Reference =  at base_commit dd1615c59 with patch.diff APPLIED (verified: `git diff` content-identical to patch.diff modulo hunk-header context labels; sphinx 3.4.0 imported from the worktree, confirmed via sphinx.`__file__`). I did NOT treat the patch delta (attr pass moved inside the getmro loop; `ns == qualname` per class; `ClassAttribute(cls,...)` instead of `(subject,...)`) as drift.

INDEPENDENT ORACLE (not the bundled conformance_check.py). The bundled harness REPLAYS the pre-loop passes to synthesize `initial`, which shares the model's assumptions. I instead neutralized `getmro` in the live function's globals so the REAL get_class_members computes its own pre-loop table; `initial` is therefore the real seed and the fragment's own output is the only delta. Model transcribed literally from Solution.lean (addAnnotations / addEntries / gatherMemberDocs), with Lean `none` vs `some ""` kept distinct and owner bridged by id(cls).

### SELF-CAUGHT HARNESS BUGS (both fixed; the pre-fix passes were vacuous and are discarded):
1. sphinx.ext.autodoc.importer is RE-EXECUTED during import (circular import via.mock), so `IMP.__dict__` is NOT the live get_class_members' globals — patching IMP.getmro was a silent no-op and `initial` already contained attr1/attr2/attr3, making every comparison vacuously true. Fixed by binding to GCM.`__globals__` plus an assert that the neutralization fired. Post-fix |initial|=28 vs |real|=31 on the F2P case, i.e. genuinely non-vacuous.
2. Reading cls.`__annotations__` MUTATES the class (CPython auto-creates it), changing dir() and hence the pre-loop table; this manufactured a spurious `__annotations__` divergence. Fixed by touching every chain class before measuring.

**EVIDENCE.** (a) Lean: scripts/lean_verify.sh exit 0; `#print axioms correct_gatherMemberDocs` = [propext, Quot.sound] — no sorryAx, no custom axiom; axioms region is legitimately empty (all per-class data are INPUTS). (b) markers.same_spec(Solution, Solution_prepatch, LeanBackend) = True — spec region byte-identical.

(c) Targeted cases, all MATCH with 42 real fragment writes: F2P test_inherited_instance_variable shape (Bar(Foo)); forward interleave (Base annotates x, Derived documents it); REVERSE interleave (Derived annotates p, Base documents it -> doc=None owner=Der); mid-chain annotation vs derived docstring (L0/L1/L2); diamond A/B/C/D/E (z resolves to owner=B via MRO); cross-module `__qualname__` COLLISION (Span(Shared_B, Shared_A) — two distinct classes, same qualname, different modules — each consults its own module+qualname correctly); nested Outer.Inner qualname vs bare Inner; private-name mangling incl. the falsy-drop (unmangle(Q,'`_P__secret`') -> None dropped); empty `#:` yielding some "".

(d) Exotic reference paths all MATCH: dict subclass, OrderedDict, int, io.BytesIO, enum.Enum, object, type, exec-defined class with no source (PycodeError), and a metaclass whose `__module__` access raises (safe_getattr AttributeError path). (e) Fuzz: 7,699 generated hierarchies (12 seeds) driven through the real callee with 20,167 genuine fragment writes — 0 disagreements. harness_errors are import-time MRO TypeErrors from random base sampling, not comparison failures.

DISCRIMINATION (positive controls — a green oracle proves nothing if it cannot fail). Mutating the model refutes it on real inputs: prepatch head_only (5/5 cases), prepatch-style flattened annotation pass (2/5, incl. the interleave witness), no_doc (5/5), and crucially target_owner — crediting entries to the target class instead of `cls` — refuted on 4/5. So the owner clause the refinement calls load-bearing is genuinely observable through my oracle and is not over-specification.

**FRAME.** `ClassAttribute.value` is the sole omitted field; across all fragment-added members observed it was invariably INSTANCEATTR, so the fragment never chooses it — a genuine frame. `owner = none` (real, from the pre-loop dir() pass emitting ClassAttribute(None,...)) and doc `some ""` are both reachable, so the carrier is not an artifact.

**CONCLUSION.** The postcondition is exact equality to a total deterministic fold (no vacuity, no unconstrained output component), and it agrees with the real post-patch callee on every input I could construct. No diverging input exists to report; the spec is not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker-3 (leakage / gold-reconstruction), instance sphinx-doc__sphinx-8548, lean bundle. Independently re-derived; did not inherit the recorded G-LEAK/G-PANEL-3 pass.

**NO RELAXATION PRESENT.** Checked explicitly: no RELAXED_LEAKAGE.md anywhere under the instance dir (find -iname '*RELAX*' empty), meta.json has no relaxed_leakage key, and gates.G-LEAK.status == "pass" (not "relaxed"). So this was judged as a plain leakage question, not a relaxation-worth question. No file in the bundle addresses the reviewer: swept refinement.md and mapping.md for reviewer-directed/verdict-steering text ("you must submit", "the honest verdict", "dear auditor/panel", "attacker") -- zero hits; leakage.reviewer_directed(Solution.lean) also returned []. Nothing to report on that axis.

SPEC REGION INTEGRITY (measured). Recomputed via src/swebench_unified/markers: spec_view(Solution.lean) sha256 = 33260e9b5a9d05ea3d8930d794f86f234bd55a0bd7f688a55c0123a54edba0c4, byte-equal to meta.json region_hashes.spec_view; all five region hashes (axioms/pure/post-conditions/impl/proof) reproduce meta.json exactly. same_spec(Solution.lean, Solution_prepatch.lean) = True, and diff of the two projected spec views is EMPTY (byte-identical) -- the twin differs only in the elided impl, so the spec view I judged is the one both variants share. Confirmed the projection actually elides: spec view is 154 lines, impl-start/proof-start bodies replaced by the elision placeholders, zero occurrences of Id.run/forIn/theorem.

MECHANICAL SCREEN (re-run myself, not read off meta). leakage.screen(Solution.lean, lean tables, gold patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. Patch changed symbols = ['add_directive_header','get_class_members']; neither appears as a spec-view identifier or in any spec-view comment. Hand greps over the projected view for the fix's distinctive repo vocabulary all came back empty: getmro, ModuleAnalyzer, for_module, PycodeError, safe_getattr, getannotations, `__qualname__`, `__module__`, INSTANCEATTR, ClassAttribute, attrgetter, unmangle, objpath, subject, analyzer, autodoc, sphinx, importer, attr_docs. No diff markers, no patched file path (sphinx/ext/autodoc/importer.py, sphinx/ext/autodoc/`__init__`.py) and no dotted module path. No temporal fix-narration vocabulary (bug/fix/patch/previously/regression/incorrectly/wrong/broken/instead of/used to/no longer). Test-side: `_test_param_ids` empty; none of the four test fn names (incl. FAIL_TO_PASS test_inherited_instance_variable) is echoed.

**WHY THE COVERED FACET IS PUBLIC.** The problem_statement is unusually explicit and by itself names the discriminator: "autodoc searches for a cached docstring using (namespace, attrname) as search-key, but doesn't check for baseclass-namespace," under the title "inherited-members won't work for inherited attributes (data members)." So the spec view's core commitment -- walk the inheritance chain most-derived-first and, for each class, consult the attributes recorded under THAT class's own namespace key -- is a restatement of public text, not a leak. Likewise (namespace, attrname) being the search key makes the abstract field name attrDocs public; separately, attr_docs appears on BOTH removed and added patch lines (pre-existing, not edit-localizing) and is a dict attribute, not a def/class the patch introduces (`_patch_new_symbols` = []).

THE TWO CLAUSES BEYOND THE PROSE, AND WHY THEY ARE NOT LEAKAGE.

(1) The loop-fusion/interleaving clause ("consulting each class's two sources together, one class at a time... a bare declaration does not pre-empt documentation recorded for a class ahead of it on the chain") and

(2) the owner clause (each entry records the VISITED class, "never the class the documentation was requested for"). Both are load-bearing: I confirmed the prepatch twin genuinely fails -- scripts/lean_verify.sh Solution_prepatch.lean exits 1 with a semantic type mismatch between the two loop shapes (two-pass, target-namespace-only vs fused per-class), so these clauses are what make the spec discriminate rather than decoration. But discriminating is what a spec owes (that is panel-1's axis); leakage under this framework's standard is edit-reconstruction: reproduced diff line, diff marker, patched path, repo-symbol echo, or bug/fix narration.

Both clauses are stated as forward requirements on the modeled function over abstract inputs, with no temporal before/after contrast and no repo anchoring. Decisively, the gold edit's most distinctive mechanical content is ABSENT from the spec view: that get_class_members drops its analyzer parameter, that it calls ModuleAnalyzer.for_module(cls.`__module__`)/analyze() per class, that it matches ns == cls.`__qualname__`, and that the whole thing is guarded by (AttributeError, PycodeError). The spec deliberately abstracts all of that into per-ClassInfo INPUTS (nsKey/classKey/annNames/attrDocs), so a reader cannot recover the diff shape, the file, or the signature change from the view.

Treating "the spec pins gold behavior more precisely than the prose issue" as leakage would condemn every bundle in the benchmark and empty the gate; the relaxation mechanism exists for the narrower case where prose and gold DISAGREE, which is not this instance (they agree).

SUPPORTING GATE SOUNDNESS (ran, not inherited). scripts/lean_verify.sh Solution.lean exit 0; injected #print axioms correct_gatherMemberDocs -> 'depends on axioms: [propext, Quot.sound]' -- no sorryAx, so the carried proof is real and G-GOLD/G-VERIFY are sound. scripts/lean_verify.sh Solution_prepatch.lean exit 1 (G-DIFF sound). axioms region declares no axiom/opaque, consistent with G-AX's documented skip.

**VERDICT:** NO-LEAKAGE. The spec view leaks nothing beyond the publicly stated (namespace, attrname)/baseclass-namespace facet, and the fix's mechanism is abstracted out of the view entirely.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.