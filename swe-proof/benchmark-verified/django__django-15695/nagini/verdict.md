# P2 adversarial audit — django__django-15695

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1.py`, `atk_2.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_16.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_3.py`, `atk_4.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -248,8 +248,9 @@
         )
     )
     # impl-start
-    # The FIX: don't alter when the current name already equals the target.
-    if old_index.name == new_name:
-        return
+    # ATTACK 1 (PREPATCH BUG re-encoded): no guard at all -- engage the
+    # schema primitive unconditionally, exactly as the pre-patch
+    # database_forwards called schema_editor.rename_index(...) with no
+    # no-op check. MUST be rejected (rename X -> X).
     issue_rename(t_pre, editor, old_index, new_name)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -248,8 +248,12 @@
         )
     )
     # impl-start
-    # The FIX: don't alter when the current name already equals the target.
+    # ATTACK 2 (ungrounded-oracle echo): gold decision, but on the differing
+    # branch never engage the primitive -- just WRITE the observability record
+    # the spec's value clauses read. Refines to "report the alteration without
+    # ever asking the backend". MUST be rejected (no token at t_renamed).
     if old_index.name == new_name:
         return
-    issue_rename(t_pre, editor, old_index, new_name)
+    editor.rename_issued = True
+    editor.renamed_to = new_name
     # impl-end
```

Attack 3 — `atk_3.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -248,8 +248,11 @@
         )
     )
     # impl-start
-    # The FIX: don't alter when the current name already equals the target.
+    # ATTACK 3 (PROXY SUBJECT -- prior-pass named counterexample re-encoded):
+    # gold decision, but engage the primitive about a FRESH index object that
+    # merely carries the same current name, not the one the caller handed in.
     if old_index.name == new_name:
         return
-    issue_rename(t_pre, editor, old_index, new_name)
+    proxy = ExistingIndex(old_index.name)
+    issue_rename(t_pre, editor, proxy, new_name)
     # impl-end
```

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -248,8 +248,16 @@
         )
     )
     # impl-start
-    # The FIX: don't alter when the current name already equals the target.
+    # ATTACK 4 (TRANSIENT LAUNDER -- prior-pass named counterexample
+    # re-encoded): on the equal-names branch move the observability record to
+    # the target and then restore it, so the "record left as found" clause is
+    # met by save/restore rather than by never touching it.
     if old_index.name == new_name:
+        saved_to = editor.renamed_to
+        editor.rename_issued = True
+        editor.renamed_to = new_name
+        editor.rename_issued = False
+        editor.renamed_to = saved_to
         return
     issue_rename(t_pre, editor, old_index, new_name)
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -248,8 +248,8 @@
         )
     )
     # impl-start
-    # The FIX: don't alter when the current name already equals the target.
-    if old_index.name == new_name:
-        return
-    issue_rename(t_pre, editor, old_index, new_name)
+    # ATTACK 5 (PARTIAL DOMAIN): never engage the primitive at all. Correct
+    # only on the equal-names sub-domain; on the differing-names sub-domain the
+    # index is never renamed. MUST be rejected.
+    return
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -248,8 +248,13 @@
         )
     )
     # impl-start
-    # The FIX: don't alter when the current name already equals the target.
+    # ATTACK 6 (BOUNDARY / sentinel carve-out): gold decision, except also
+    # decline whenever the target identifier is the sentinel 0 that mapping.md
+    # declares is never a real name -- an ungrounded carve-out on the carrier's
+    # boundary value. MUST be rejected.
     if old_index.name == new_name:
+        return
+    if new_name == 0:
         return
     issue_rename(t_pre, editor, old_index, new_name)
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -248,8 +248,12 @@
         )
     )
     # impl-start
-    # The FIX: don't alter when the current name already equals the target.
+    # ATTACK 7 (CONTROL-FLOW-EFFECT / MULTIPLICITY): gold decision, but engage
+    # the primitive TWICE on the differing branch. Every reported value is
+    # bit-for-bit gold's; only the NUMBER of backend renames differs. MUST be
+    # rejected (there is one licence).
     if old_index.name == new_name:
         return
     issue_rename(t_pre, editor, old_index, new_name)
+    issue_rename(t_pre, editor, old_index, new_name)
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -248,8 +248,16 @@
         )
     )
     # impl-start
-    # The FIX: don't alter when the current name already equals the target.
+    # ATTACK 8 (NOVEL -- PRIVATE-EDITOR RECORD on the no-op branch): gold
+    # decision, but on the equal-names branch procure an editor of the step's
+    # own and write a full rename record onto it before returning. The
+    # caller's editor and the licence are untouched, so the no-op clauses are
+    # all satisfied -- probing whether the spec's "COMPLETE no-op" is only
+    # about the editor handed in.
     if old_index.name == new_name:
+        private = SchemaEditor()
+        private.rename_issued = True
+        private.renamed_to = new_name
         return
     issue_rename(t_pre, editor, old_index, new_name)
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -248,8 +248,15 @@
         )
     )
     # impl-start
-    # The FIX: don't alter when the current name already equals the target.
+    # ATTACK 9 (NOVEL companion to 8 -- LAUNDERED EDITOR, engaged): gold
+    # decision, but on the differing branch engage the primitive through an
+    # editor the step procured for itself, whose work the caller never sees,
+    # and then report success on the caller's editor. MUST be rejected (the
+    # licence names the editor handed in).
     if old_index.name == new_name:
         return
-    issue_rename(t_pre, editor, old_index, new_name)
+    private = SchemaEditor()
+    issue_rename(t_pre, private, old_index, new_name)
+    editor.rename_issued = True
+    editor.renamed_to = new_name
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -248,8 +248,15 @@
         )
     )
     # impl-start
-    # The FIX: don't alter when the current name already equals the target.
+    # ATTACK 10 (NON-TERMINATION): honest no-op on the equal branch, but an
+    # unbounded loop instead of the rename on the differing branch. Under
+    # partial correctness every Ensures holds vacuously; the migration hangs.
+    # MUST be rejected by MustTerminate.
     if old_index.name == new_name:
         return
+    i = 0
+    while i >= 0:
+        Invariant(i >= 0)
+        i = i + 1
     issue_rename(t_pre, editor, old_index, new_name)
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -248,8 +248,11 @@
         )
     )
     # impl-start
-    # The FIX: don't alter when the current name already equals the target.
+    # ATTACK 11 (VACUITY CONTROL, equal-names branch): Assert(False) there.
+    # MUST FAIL to verify -- otherwise the branch is unreachable and every
+    # no-op obligation on it is vacuous.
     if old_index.name == new_name:
+        Assert(False)
         return
     issue_rename(t_pre, editor, old_index, new_name)
     # impl-end
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -248,8 +248,11 @@
         )
     )
     # impl-start
-    # The FIX: don't alter when the current name already equals the target.
+    # ATTACK 12 (VACUITY CONTROL, differing-names branch): Assert(False)
+    # there. MUST FAIL to verify -- otherwise the engagement obligations are
+    # vacuous.
     if old_index.name == new_name:
         return
+    Assert(False)
     issue_rename(t_pre, editor, old_index, new_name)
     # impl-end
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -248,7 +248,13 @@
         )
     )
     # impl-start
-    # The FIX: don't alter when the current name already equals the target.
+    # ATTACK 13 (NOVEL -- UNGROUNDED DISCRIMINATOR): decide on a field the
+    # precondition leaves UNCONSTRAINED. The spec pins editor.rename_issued is
+    # False on entry but says nothing about editor.renamed_to, so a step is free
+    # to branch on it. Refines to a guard on a quantity the gold patch never
+    # consults. MUST be rejected.
+    if old_index.name == editor.renamed_to:
+        return
     if old_index.name == new_name:
         return
     issue_rename(t_pre, editor, old_index, new_name)
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

```diff
@@ -248,8 +248,17 @@
         )
     )
     # impl-start
-    # The FIX: don't alter when the current name already equals the target.
+    # ATTACK 14 (NOVEL -- MULTIPLICITY via a TERMINATING bounded loop): gold
+    # decision, then engage inside a loop that provably terminates, so the
+    # MustTerminate obligation alone cannot reject it and only the single
+    # licence can. Two backend renames; identical reported values. MUST be
+    # rejected.
     if old_index.name == new_name:
         return
-    issue_rename(t_pre, editor, old_index, new_name)
+    i = 0
+    while i < 2:
+        Invariant(i >= 0 and i <= 2)
+        Invariant(MustTerminate(2 - i))
+        issue_rename(t_pre, editor, old_index, new_name)
+        i = i + 1
     # impl-end
```

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

```diff
@@ -248,8 +248,10 @@
         )
     )
     # impl-start
-    # The FIX: don't alter when the current name already equals the target.
-    if old_index.name == new_name:
+    # ATTACK 15 (INVERTED GUARD): engage the primitive exactly when the names
+    # are EQUAL and decline when they differ -- the precise negation of the
+    # gold decision. MUST be rejected.
+    if old_index.name != new_name:
         return
     issue_rename(t_pre, editor, old_index, new_name)
     # impl-end
```

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good)

```diff
@@ -248,8 +248,14 @@
         )
     )
     # impl-start
-    # The FIX: don't alter when the current name already equals the target.
+    # ATTACK 16 (PARTIAL DOMAIN on an ORDER slice): engage only on the part of
+    # the differing-names domain where the current identifier happens to be the
+    # smaller one. mapping.md abstracts names to ints under EQUALITY only, so
+    # the ordering is ungrounded and this slice is a wrong impl. MUST be
+    # rejected.
     if old_index.name == new_name:
+        return
+    if old_index.name > new_name:
         return
     issue_rename(t_pre, editor, old_index, new_name)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15695.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A schema-altering step is asked to give an existing database index a target
  name. The existing index already carries some current name, and the step
  reaches the underlying schema primitive that performs renames. The step must
  be IDEMPOTENT with respect to that name:

    (1) if the current name of the existing index already equals the target
        name, the step performs NO alteration at all -- it never engages the
        schema primitive (re-applying the step on an index that is already at
        the target name is a no-op, so it cannot fail by asking the backend to
        rename an index to a name that is already in use);

    (2) otherwise (the current name differs from the target name) the step
        engages the schema primitive EXACTLY ONCE, asking it for precisely the
        one rename that names the index by the target name.

  The step is handed the schema editor that carries the primitive and the
  existing index whose name is to change, and those are the ones that must be
  asked about: the alteration is made through the editor the caller supplied,
  never through some other one the step procures for itself and whose work the
  caller never sees, and it renames THAT index -- the engagement names the name
  that index currently carries as the one being moved, so a step cannot satisfy
  this by asking for the rename of some other index it made up.

  Engaging the schema primitive is an EFFECT on the database, not a value the
  step returns, and it is NOT recoverable from any answer the step reports about
  itself. Two steps can report identical answers while having asked the backend
  for a different number of renames, or for renames to different names, or for
  none at all. HOW MANY times the primitive is engaged, and WHICH target each
  engagement names, is therefore part of the behaviour specified here and not an
  implementation's free choice: a step that reaches the target name by way of
  some other name first, or that asks a second time, or that asks about some
  other index or through some other editor, or that reports the alteration
  without ever asking, is not this behaviour however it describes itself
  afterwards. In particular the no-alteration case of (1) is a COMPLETE
  no-op: nothing whatsoever is asked of the schema primitive, so the record of
  what it was last asked to rename to is left exactly as the step found it -- it
  is not enough to perform the alteration and then merely report that no rename
  happened.

  That obligation is carried the standard way effects are carried here. An
  engagement of the primitive is an operation (`rename_index_io`) parameterised
  by the schema editor it engages and by the pair of names it asks for -- the
  name the existing index currently carries and the target name. A step receives
  a token at a place together with the licence naming the engagements permitted
  there; an engagement spends licence and token and yields the token at the place
  the licence names; and the step must end holding a token at the place its
  behaviour requires. Every step is licensed for exactly ONE engagement, naming
  exactly the editor it was handed, the name its index currently carries, and the
  target name -- on every input it accepts, including the equal-name one. So the
  engagement cannot be skipped and its effect reported anyway (the token is
  obtainable only by making it), cannot ask for any other name (the licence names
  the target), and cannot happen twice (there is one licence and a step cannot
  mint one). In the equal-name case the step is not relieved of the capability,
  it is required to DECLINE it: it must end still holding the very token it
  arrived with, at the place it arrived at, together with that licence still
  UNSPENT -- which is exactly the observation that nothing was asked of the
  primitive, and is not something a step that engaged the primitive can produce.

  What the step must NOT claim is what the alteration achieves in the database:
  the schema primitive is capability-gated and may legitimately decline to emit
  anything for some index kinds on some backends. The behaviour specified here is
  the DECISION and the ASK -- whether, how often, and with which target the
  primitive is engaged -- never the backend's own success at carrying it out.

The existing index is modelled as a minimal class carrying only its touched
field -- its current name, abstracted to an integer identifier (names are only
ever compared for equality here, never indexed into). That field is READ-ONLY to
the step: the step decides whether to ask for a rename, it does not itself move
the index's name, so it holds only a share sufficient to read it and cannot
manufacture the primitive's outcome by writing it. A small editor object records
what the primitive was asked for, so the decision is observable as a value too.

Total correctness: deciding whether to rename is bounded, loop-free work that
must actually complete and hand control back to the migration executor. Nagini
checks partial correctness by default -- a diverging body would satisfy every
postcondition vacuously -- so every function carries a ``MustTerminate``
obligation (with strictly decreasing measures for callees) to reject
non-terminating implementations.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.io_contracts import *
from nagini_contracts.obligations import MustTerminate

class ExistingIndex:
    def __init__(self, name: int) -> None:
        # Terminates: field initialisation is straight-line work; measure 1
        # lets any caller holding MustTerminate(2) construct a value without
        # leaking its own obligation.
        Requires(MustTerminate(1))
        Ensures(Acc(self.name) and self.name == name)  # type: ignore
        self.name = name

class SchemaEditor:
    def __init__(self) -> None:
        # Terminates: field initialisation is straight-line work (measure 1).
        Requires(MustTerminate(1))
        Ensures(Acc(self.rename_issued) and self.rename_issued is False)  # type: ignore
        Ensures(Acc(self.renamed_to) and self.renamed_to == 0)  # type: ignore
        self.rename_issued = False  # type: bool
        self.renamed_to = 0  # type: int

# axioms-start
@IOOperation
def rename_index_io(t_pre: Place, editor: SchemaEditor, source: int, target: int,
                    t_post: Place = Result()) -> bool:
    """The observable EFFECT of the step: the schema primitive carried by
    `editor` is engaged ONCE and asked to rename the index currently called
    `source` to `target`, carrying the step from place `t_pre` to place `t_post`.
    It models the ASK itself -- that an engagement HAPPENED, WHICH schema editor
    was asked, and WHICH pair of names it named -- not what the backend then
    manages to do, which is capability-gated and none of this step's business.
    A step holds one instance of this operation per engagement it is permitted to
    make and an engagement spends one; a step cannot mint an instance, so how many
    engagements are made and which names each one asks about are settled by the
    step's contract instead of chosen by its implementation. An engagement
    terminates."""
    Terminates(True)

@ContractOnly
def issue_rename(t_pre: Place, editor: SchemaEditor, old_index: ExistingIndex,
                 new_name: int) -> None:
    """Engage the unchanged backend rename primitive, asking it to name the
    existing index `new_name`, and record on the editor that it was asked and
    what for. Models the unchanged primitive's INVOCATION: it claims nothing
    about what the backend achieves in the database (that is capability-gated),
    only that the ask happened with that target. Engaging is an effect, so this
    spends one licence to ask for exactly the rename of this index's current name
    to `new_name` plus the token that reaches it, leaving the token at the place
    that licence names: it is callable only where the caller's own contract
    licenses an engagement naming that editor and that pair of names.
    (mapping.md)"""
    IOExists1(Place)(
        lambda t_post: (
        # The index's current name is only READ here: the primitive, not this
        # model, is what moves a name in the database.
        Requires(Acc(old_index.name, 1 / 2)),
        Requires(Acc(editor.rename_issued) and Acc(editor.renamed_to)),
        # The backend rename primitive may only be engaged when the existing
        # index's current name actually differs from the target: asking the
        # backend to rename an index to a name that is already in use is
        # forbidden (it would fail). The caller therefore MUST establish this
        # before engaging -- so engaging in the equal-names case is a
        # verification error, not an effect that can be performed and then
        # papered over by resetting an observability flag.
        Requires(old_index.name != new_name),
        Requires(token(t_pre, 2) and
                 rename_index_io(t_pre, editor, old_index.name, new_name, t_post)),
        Requires(MustTerminate(2)),
        Ensures(token(t_post)),
        Ensures(Acc(old_index.name, 1 / 2)),
        Ensures(Acc(editor.rename_issued) and Acc(editor.renamed_to)),
        Ensures(editor.rename_issued is True),
        Ensures(editor.renamed_to == new_name),
        )
    )
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end

def rename_existing_index(t_pre: Place, editor: SchemaEditor,
                          old_index: ExistingIndex, new_name: int) -> None:
    IOExists1(Place)(
        lambda t_renamed: (
        # pre-conditions-start
        # TERMINATION: deciding whether to rename is a bounded, loop-free step
        # that MUST actually complete and hand control back to the migration
        # executor (total correctness). Under partial-correctness semantics a
        # diverging body (e.g. an endless loop before the rename decision)
        # satisfies every Ensures clause only vacuously yet never returns; the
        # real step always returns. This obligation rejects any such
        # implementation.
        Requires(MustTerminate(3)),
        # The index's current name is READ-ONLY to the step (a share, not full
        # permission): the step's job is to decide whether to ask for a rename,
        # not to move the name itself. So it can neither manufacture the
        # primitive's outcome by writing the name, nor step outside the
        # primitive's domain restriction by moving the name first and asking
        # afterwards.
        Requires(Acc(old_index.name, 1 / 2)),
        Requires(Acc(editor.rename_issued) and Acc(editor.renamed_to)),
        Requires(editor.rename_issued is False),
        # The step arrives holding a token and a licence for exactly ONE
        # engagement of the schema primitive: through the editor it was handed,
        # about the index it was handed (named by the name that index currently
        # carries), asking for exactly the target name. The licence is given on
        # EVERY input the step accepts -- the equal-name case is not privileged by
        # withholding the capability, it is required to decline to use one it
        # holds. That single licence is the whole effect budget: no second
        # engagement, none through another editor, and none naming any other pair
        # of names is available to any implementation, whatever it reports.
        Requires(token(t_pre, 3) and
                 rename_index_io(t_pre, editor, old_index.name, new_name,
                                 t_renamed)),
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(old_index.name, 1 / 2)),
        Ensures(Acc(editor.rename_issued) and Acc(editor.renamed_to)),
        # (2) The licensed engagement HAS BEEN MADE, exactly once: the step ends
        # holding a token at the place that single licence names, which is
        # reachable only by engaging the primitive through the editor it was
        # handed, about the index it was handed, asking for exactly the target
        # name -- and which cannot be reached twice, because no second licence
        # exists. So the alteration is never reported unasked, the ask that
        # happened named that pair of names and no other, and the index is never
        # routed to the target by way of some other name.
        Ensures(Implies(Old(old_index.name) != new_name, token(t_renamed))),
        # (1) The no-alteration case is a COMPLETE no-op: the step ends still
        # holding the very token it arrived with, at the very place it arrived at,
        # with its measure intact, AND the engagement licence STILL UNSPENT. It
        # held the capability to engage the primitive and declined to use it, so
        # nothing whatsoever was asked of the schema primitive -- not once, and
        # about no pair of names. This is the clause a report cannot satisfy: an
        # unspent licence is not something an implementation can still be holding
        # after having spent it, however it describes what it did.
        Ensures(Implies(Old(old_index.name) == new_name,
                        token(t_pre, 3) and
                        rename_index_io(t_pre, editor, Old(old_index.name),
                                        new_name, t_renamed))),
        # (1)+(2) restated as the value the editor records: the primitive was
        # asked for a rename iff the current name differed from the target.
        Ensures(editor.rename_issued == (Old(old_index.name) != new_name)),
        # When (and only when) the primitive was asked, it was asked for exactly
        # the target name.
        Ensures(Implies(editor.rename_issued, editor.renamed_to == new_name)),
        # (1) from the other side -- when nothing was asked, the record of what
        # the primitive was last asked to rename to is left exactly as the step
        # found it. An implementation that asks the primitive anyway and only
        # reports "no rename happened" afterwards has still touched the schema,
        # and does not satisfy this.
        Ensures(Implies(not editor.rename_issued,
                        editor.renamed_to == Old(editor.renamed_to))),
        # post-conditions-end
        )
    )
    # impl-start
    # POSITIVE CONTROL: correct but restructured (negated guard). Engage only
    # on the differing-names branch; the equal-names branch falls through with
    # the licence unspent. Behaviourally identical to gold. MUST verify.
    if old_index.name != new_name:
        issue_rename(t_pre, editor, old_index, new_name)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ ADVERSARIAL AUDIT (refinement fidelity) — django__django-15695 / nagini. VERDICT: SOUND (advisory). 16 same-spec wrong-impl attacks + 1 positive control run; all 3 CANDIDATEs had faithful refined patches MATERIALIZED and EXECUTED through the official Docker harness, and ALL 3 RESOLVE. No verify-but-wrong impl found.

COMMANDS (from repo root swe-proof), attacks launched 3-at-a-time as background jobs:
  python -m swebench_unified.adversary same-spec nagini django__django-15695 <D>/atk_N.py   -> SAME (all 16 + pos_control)
  python -m swebench_unified.adversary weakness  nagini django__django-15695 <D>/atk_N.py   (0=CANDIDATE, 2=rejected)
  bash scripts/nagini_verify.sh benchmark-verified/django__django-15695/nagini/model_prepatch.py
  run_resolve('django__django-15695', <patch>) via swebench_unified.harness (Docker, docker) — driver <D>/resolve.py

### PER-ATTACK RESULTS (observed weakness exit code):
atk_1.py  PREPATCH BUG (no guard; engage unconditionally) -> exit 2, does not verify. REJECTED. atk_2.py  UNGROUNDED-ORACLE ECHO (gold guard; on the differ branch merely WRITE editor.rename_issued=True/renamed_to=new_name instead of engaging) -> exit 2. REJECTED — the IO token at the licensed place is unreachable by a self-report. atk_3.py  PROXY SUBJECT (prior pass's named counterexample re-encoded: engage about a fresh ExistingIndex(old_index.name), not the object handed in) -> exit 0 CANDIDATE (verifies 18.6s). PATCH MATERIALIZED + RESOLVED. atk_4.py  TRANSIENT LAUNDER (prior pass's other named counterexample: on the equal branch save/set-to-target/restore rename_issued+renamed_to, so 'record left as found' holds by save/restore) -> exit 0 CANDIDATE (verifies 19.3s).

PATCH MATERIALIZED + RESOLVED. atk_5.py  PARTIAL DOMAIN (always `return`; correct only on the equal-names sub-domain) -> exit 2. REJECTED. atk_6.py  BOUNDARY / sentinel carve-out (also decline whenever new_name == 0, the identifier mapping.md declares is never a real name) -> exit 2. REJECTED. atk_7.py  CONTROL-FLOW-EFFECT / MULTIPLICITY (gold guard, issue_rename TWICE; reported values bit-for-bit gold's, only the COUNT differs) -> exit 2. REJECTED — the second engagement has no licence. atk_8.py  NOVEL PRIVATE-EDITOR RECORD on the no-op branch (on the equal branch procure a SchemaEditor() of the step's own and write a full rename record onto it before returning; caller's editor + licence untouched) -> exit 0 CANDIDATE (verifies 17.1s).

PATCH MATERIALIZED + RESOLVED. atk_9.py  NOVEL LAUNDERED EDITOR, engaged (engage through a private editor whose work the caller never sees, then report success on the caller's) -> exit 2. REJECTED — the licence names the editor handed in. atk_10.py NON-TERMINATION (honest no-op on equal; unbounded `while i >= 0` in place of the rename on the differ branch — vacuous under partial correctness) -> exit 2. REJECTED by MustTerminate. atk_11.py VACUITY CONTROL, equal-names branch: Assert(False) -> exit 2 (FAILS) => branch IS reachable; the no-op obligations are not vacuous. atk_12.py VACUITY CONTROL, differing-names branch: Assert(False) -> exit 2 (FAILS) => that branch is reachable too.

Both controls behave as required (per the guarded-self-call-goes-vacuous hazard). atk_13.py NOVEL UNGROUNDED DISCRIMINATOR (branch on `old_index.name == editor.renamed_to`; the precondition pins rename_issued is False but leaves renamed_to UNCONSTRAINED) -> exit 2. REJECTED. atk_14.py NOVEL MULTIPLICITY via a TERMINATING bounded loop (engage inside `while i < 2` with Invariant(MustTerminate(2-i)) so MustTerminate alone cannot reject it) -> exit 2. REJECTED — the single licence caps the count regardless of control flow. atk_15.py INVERTED GUARD (engage exactly when the names are EQUAL) -> exit 2. REJECTED. atk_16.py PARTIAL DOMAIN on an ORDER slice (engage only where old_index.name < new_name; names are equality-compared only per mapping.md §2, so ordering is ungrounded) -> exit 2. REJECTED. pos_control.py CORRECT-but-restructured (negated guard `if old_index.name != new_name: issue_rename(...)`) -> exit 0, VERIFIES in 19.9s. Spec is not too strong.

**PREPATCH REPRODUCED:** yes. `bash scripts/nagini_verify.sh .../model_prepatch.py` -> exit 1, 'Verification failed / model_prepatch.py:252:5:252:53: error: The precondition of method issue_rename might not hold. Assertion (old_index.name != new_name) might not hold.' Matches meta.json prepatch_models.fails_on (that field cites :113, stale w.r.t. the current 252-line model — cosmetic).

MANDATORY RESOLVE RUNS FOR EVERY CANDIDATE (the load-bearing evidence). Worktree at base_commit 647480166bfe7532e8c471fef0146e3a17e6c0c9 (<D>/wt, git worktree from the upstream repository); all three `git apply --check` APPLY:
  atk_3 -> <D>/patch_atk_3.diff. Refinement: gold guard + `schema_editor.rename_index(model, old_index.clone(), new_index)` (Index.clone() re-deconstructs, preserving name and fields — the faithful reading of `proxy = ExistingIndex(old_index.name)` under mapping.md §2, where ExistingIndex carries ONLY the name).
     EXECUTED: RESOLVED=True COMPLETED=True note='resolved'; patch_successfully_applied=true; F2P success=['test_rename_index_unnamed_index'], failure=[]; P2P failure=[]. Log <D>/resolve_atk_3.txt.
     Why it resolves rather than breaking the spec: rename_index reads only old_index.name (schema.py:496-504 -> `_rename_index_sql`(model, old_index.name, new_index.name)); the can_rename_index=False fallback (sqlite, the F2P backend) calls remove_index(model, old_index), which consumes only .name/.fields via Index.remove_sql -> `_delete_index_sql`(model, self.name). A clone carrying the same name and fields is observationally identical, so this is a genuine same-behaviour rival: the licence binds the SOURCE NAME, which is all mapping.md §2 abstracts. Not a hole.
  atk_4 -> <D>/patch_atk_4.diff. Refinement: gold early return preceded by save / set-to-target / restore of the step's own record of what a rename would have asked for (the model's rename_issued/renamed_to carriers, as sbu_* attributes on the editor; no rename_index call, so the primitive is never engaged on that branch).
     EXECUTED: RESOLVED=True COMPLETED=True note='resolved'; F2P success=['test_rename_index_unnamed_index'], failure=[]; P2P failure=[]. Log <D>/resolve_atk_4.txt.
     Why it resolves: the carriers are the model's own observability record, not repo state any test reads; the SQL-emitting primitive is still never engaged on the equal-names path, so assertNumQueries(0) and the F2P re-apply are unaffected. The 'record kept' clause is indeed satisfiable by save/restore rather than only by non-interference — a modelling looseness with NO behavioural consequence, because the completeness of the no-op is carried by the UNSPENT-LICENCE clause (Ensures(Implies(Old(old_index.name)==new_name, token(t_pre,3) and rename_index_io(...)))), not by the resettable record. That architecture is what makes atk_1/atk_2/atk_7 fail.
  atk_8 -> <D>/patch_atk_8.diff. Refinement: gold decision, but on the equal-names branch procure `schema_editor.connection.schema_editor(collect_sql=True)` and record the rename onto that private object, then return.
     EXECUTED: RESOLVED=True COMPLETED=True note='resolved'; patch_successfully_applied=true; F2P success=['test_rename_index_unnamed_index'], failure=[]; P2P failure=[]. Log <D>/resolve_atk_8.txt.
     Why it resolves: constructing an editor emits no SQL and the private one is never entered as a context manager / never executes, so the caller's editor still emits zero statements on the no-op path. The spec's 'COMPLETE no-op' is scoped to the editor the caller supplied — which is exactly the right scope, since only that editor's statements are observable to the migration executor and to assertNumQueries(0).

### REFINEMENT.MD LEG AUDIT (§5 kinds; every leg R / A-consumed / A-reference / I — NO kind-3):
A1 `old_index: ExistingIndex` + `.name` -> the join-point old_index from either branch: **R**. VERIFIED against the real source at base_commit: both producers (models.py:956-959 `models.Index(fields=self.old_fields, name=matching_index_name[0])`, and :961-962 `from_model_state.get_index_by_name(self.old_name)`) yield an object whose .name is the current DB name; the guard at the join reasons only about that field. Correspondence holds. A2 `new_name: int` -> `self.new_name`: **R**. VERIFIED: ModelState.get_index_by_name (state.py:955-959) returns the index whose `.name == name`, so new_index.name == self.new_name and one int carrier legitimately stands for both. Equality-only abstraction is consistent with the impl (names never indexed/sliced).

A3 `if old_index.name == new_name: return` -> the gold guard: **I**. VERIFIED byte-for-byte against patch.diff: `# Don't alter when the index name is not changed. / if old_index.name == self.new_name: / return` inserted between :962 and :964, i.e. BEFORE the new_index lookup and before rename_index. The single added hunk; the model impl is the same equality-compare-and-early-return. A4 `issue_rename` -> `BaseDatabaseSchemaEditor.rename_index`: **A-reference**. VERIFIED the callee text at base_commit is byte-identical to the block mapping.md §3.1 quotes (schema.py:496-504; diffed against <D>/callee_actual.txt). meta.json axioms == [] and deep_model_references records exactly this one A-reference; model.py has exactly ONE @ContractOnly (issue_rename).

Its Ensures ARE used by the proof, so 'A-reference validated out-of-band by G-AX' is the accurate label only because the axiomatized callee is the UNCHANGED one — the function under change (the guard) is NOT axiomatized, it is the I-tagged step. axiom_check.py drives the real primitive on sqlite to ground both facts the deep model pins (rename moves old->new; creating a name already present raises). No kind-3 leg exists.

ADDITIONAL PROBE — guard PLACEMENT is load-bearing but NOT model-visible (advisory, does NOT break G-EQ): <D>/patch_probe_after_lookup.diff moves the gold guard to AFTER `new_index = to_model_state.get_index_by_name(self.new_name)`, keeping the identical model-level decision (engage the primitive iff the names differ). EXECUTED: run_resolve -> RESOLVED=False COMPLETED=True note='patch did not resolve in 3 attempts (consistent — not flaky)'; patch_successfully_applied=true; F2P failure=['test_rename_index_unnamed_index']. Log <D>/resolve_probe.txt.

Mechanism: on the F2P re-apply the call is `database_forwards(app_label, editor, new_state, project_state)`, so to_state = project_state — the ORIGINAL state, to which state_forwards never added an index named 'new_pony_test_idx' in the old_fields (unnamed) case. get_index_by_name therefore raises ValueError. Gold returns BEFORE that lookup; the probe reaches it and crashes. Why this is NOT a G-EQ break: it is a repo-level statement-ORDER variant, not a same-spec model impl.

The model has no carrier for the to_state/new_index lookup at all (mapping.md §2 collapses self.new_name and new_index.name into one int parameter), so NO edit confined to model.py's impl region can express this variant — every model impl that verifies decides the engagement from parameters already in hand and cannot resurrect the lookup. Confirmed empirically: the 16 same-spec attacks include every shape the carriers admit, and none is this one.

The correspondence is preserved by refinement.md A3/§B, which pin the guard's position ('returns BEFORE new_index is looked up and before schema_editor.rename_index(...) is reached (models.py:966)') — i.e. the placement is discharged by the refinement MAP rather than by the spec, which is the legitimate division of labour for a detail the abstraction elides. Flagging it because it is the one place where a reader trusting the model alone would under-constrain the transliteration: a future refinement.md edit that dropped the 'before the new_index lookup' wording would silently license a non-resolving patch.

DOC DRIFT (advisory, NOT a G-EQ break — no leg's correspondence fails and no verifying impl misbehaves; each drift makes the doc claim the spec is STRONGER than it is, never weaker, so none can license an unsound impl):
  1. refinement.md:113 and :115 cite `Ensures(old_index.name == new_name)` as a clause 'pinning the post-state in both cases', and §D repeats 'leaving the index at the target name in both cases'. NO SUCH CLAUSE EXISTS in model.py (grep: 0 hits among the Ensures) — and correctly so: the docstring's own scope note explains rename_index is capability-gated, and old_index.name is held at a 1/2 read-only share precisely so the step cannot manufacture the primitive's outcome (which is what makes a domain-escape attack fail). mapping.md §2/§3.1 and meta.json deep_model_references likewise still describe issue_rename as effecting `old_index.name = new_name`, which the actual axiom does not do.
  2. refinement.md:116-117 states 'Requires(MustTerminate(2)) on rename_existing_index (with the strictly smaller MustTerminate(1) on issue_rename …)'. Actual measures in model.py: 3 on rename_existing_index, 2 on issue_rename, 1 on the constructors. The ordering argument is intact (strictly decreasing); only the numerals are stale.
  3. refinement.md §B cites the atk_2/atk_6 counterexample numbering of an EARLIER audit pass, which no longer matches this pass's file numbering — harmless provenance prose, but it reads as a stable reference and is not one.
  4. meta.json prepatch_models.fails_on cites model_prepatch.py:113; the observed error is at :252. Same clause and message, stale line number.
  Recommend a refinement.md/mapping.md prose refresh so §B/§D quote clauses that exist and the measures match.

**BASIS FOR SOUND:** 16 distinct wrong-impl families run (prepatch bug; ungrounded-oracle echo; partial-domain x3 incl. an order slice; boundary/sentinel; control-flow-effect/multiplicity x2 incl. a terminating-loop variant that MustTerminate alone cannot reject; non-termination; laundered-editor x2; proxy/transient-launder x2; ungrounded discriminator; inverted guard) — 13 of 16 REJECTED by the frozen spec; all 3 CANDIDATEs had faithful patches materialized and EXECUTED through the official Docker harness and ALL 3 RESOLVED; the positive control verifies (spec not too strong); both vacuity controls FAIL (both branches reachable, obligations non-vacuous); the prepatch bug is reproduced with the documented failing clause; all 4 refinement.md legs are R/I/A-reference with verified correspondence to the real callees at base_commit and no kind-3 leg. No evidence of verify=>correct being violated.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1.py`, `atk_2.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_16.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_3.py`, `atk_4.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 16 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15695.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A schema-altering step is asked to give an existing database index a target
  name. The existing index already carries some current name, and the step
  reaches the underlying schema primitive that performs renames. The step must
  be IDEMPOTENT with respect to that name:

    (1) if the current name of the existing index already equals the target
        name, the step performs NO alteration at all -- it never engages the
        schema primitive (re-applying the step on an index that is already at
        the target name is a no-op, so it cannot fail by asking the backend to
        rename an index to a name that is already in use);

    (2) otherwise (the current name differs from the target name) the step
        engages the schema primitive EXACTLY ONCE, asking it for precisely the
        one rename that names the index by the target name.

  The step is handed the schema editor that carries the primitive and the
  existing index whose name is to change, and those are the ones that must be
  asked about: the alteration is made through the editor the caller supplied,
  never through some other one the step procures for itself and whose work the
  caller never sees, and it renames THAT index -- the engagement names the name
  that index currently carries as the one being moved, so a step cannot satisfy
  this by asking for the rename of some other index it made up.

  Engaging the schema primitive is an EFFECT on the database, not a value the
  step returns, and it is NOT recoverable from any answer the step reports about
  itself. Two steps can report identical answers while having asked the backend
  for a different number of renames, or for renames to different names, or for
  none at all. HOW MANY times the primitive is engaged, and WHICH target each
  engagement names, is therefore part of the behaviour specified here and not an
  implementation's free choice: a step that reaches the target name by way of
  some other name first, or that asks a second time, or that asks about some
  other index or through some other editor, or that reports the alteration
  without ever asking, is not this behaviour however it describes itself
  afterwards. In particular the no-alteration case of (1) is a COMPLETE
  no-op: nothing whatsoever is asked of the schema primitive, so the record of
  what it was last asked to rename to is left exactly as the step found it -- it
  is not enough to perform the alteration and then merely report that no rename
  happened.

  That obligation is carried the standard way effects are carried here. An
  engagement of the primitive is an operation (`rename_index_io`) parameterised
  by the schema editor it engages and by the pair of names it asks for -- the
  name the existing index currently carries and the target name. A step receives
  a token at a place together with the licence naming the engagements permitted
  there; an engagement spends licence and token and yields the token at the place
  the licence names; and the step must end holding a token at the place its
  behaviour requires. Every step is licensed for exactly ONE engagement, naming
  exactly the editor it was handed, the name its index currently carries, and the
  target name -- on every input it accepts, including the equal-name one. So the
  engagement cannot be skipped and its effect reported anyway (the token is
  obtainable only by making it), cannot ask for any other name (the licence names
  the target), and cannot happen twice (there is one licence and a step cannot
  mint one). In the equal-name case the step is not relieved of the capability,
  it is required to DECLINE it: it must end still holding the very token it
  arrived with, at the place it arrived at, together with that licence still
  UNSPENT -- which is exactly the observation that nothing was asked of the
  primitive, and is not something a step that engaged the primitive can produce.

  What the step must NOT claim is what the alteration achieves in the database:
  the schema primitive is capability-gated and may legitimately decline to emit
  anything for some index kinds on some backends. The behaviour specified here is
  the DECISION and the ASK -- whether, how often, and with which target the
  primitive is engaged -- never the backend's own success at carrying it out.

The existing index is modelled as a minimal class carrying only its touched
field -- its current name, abstracted to an integer identifier (names are only
ever compared for equality here, never indexed into). That field is READ-ONLY to
the step: the step decides whether to ask for a rename, it does not itself move
the index's name, so it holds only a share sufficient to read it and cannot
manufacture the primitive's outcome by writing it. A small editor object records
what the primitive was asked for, so the decision is observable as a value too.

Total correctness: deciding whether to rename is bounded, loop-free work that
must actually complete and hand control back to the migration executor. Nagini
checks partial correctness by default -- a diverging body would satisfy every
postcondition vacuously -- so every function carries a ``MustTerminate``
obligation (with strictly decreasing measures for callees) to reject
non-terminating implementations.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.io_contracts import *
from nagini_contracts.obligations import MustTerminate

class ExistingIndex:
    def __init__(self, name: int) -> None:
        # Terminates: field initialisation is straight-line work; measure 1
        # lets any caller holding MustTerminate(2) construct a value without
        # leaking its own obligation.
        Requires(MustTerminate(1))
        Ensures(Acc(self.name) and self.name == name)  # type: ignore
        self.name = name

class SchemaEditor:
    def __init__(self) -> None:
        # Terminates: field initialisation is straight-line work (measure 1).
        Requires(MustTerminate(1))
        Ensures(Acc(self.rename_issued) and self.rename_issued is False)  # type: ignore
        Ensures(Acc(self.renamed_to) and self.renamed_to == 0)  # type: ignore
        self.rename_issued = False  # type: bool
        self.renamed_to = 0  # type: int

# axioms-start
@IOOperation
def rename_index_io(t_pre: Place, editor: SchemaEditor, source: int, target: int,
                    t_post: Place = Result()) -> bool:
    """The observable EFFECT of the step: the schema primitive carried by
    `editor` is engaged ONCE and asked to rename the index currently called
    `source` to `target`, carrying the step from place `t_pre` to place `t_post`.
    It models the ASK itself -- that an engagement HAPPENED, WHICH schema editor
    was asked, and WHICH pair of names it named -- not what the backend then
    manages to do, which is capability-gated and none of this step's business.
    A step holds one instance of this operation per engagement it is permitted to
    make and an engagement spends one; a step cannot mint an instance, so how many
    engagements are made and which names each one asks about are settled by the
    step's contract instead of chosen by its implementation. An engagement
    terminates."""
    Terminates(True)

@ContractOnly
def issue_rename(t_pre: Place, editor: SchemaEditor, old_index: ExistingIndex,
                 new_name: int) -> None:
    """Engage the unchanged backend rename primitive, asking it to name the
    existing index `new_name`, and record on the editor that it was asked and
    what for. Models the unchanged primitive's INVOCATION: it claims nothing
    about what the backend achieves in the database (that is capability-gated),
    only that the ask happened with that target. Engaging is an effect, so this
    spends one licence to ask for exactly the rename of this index's current name
    to `new_name` plus the token that reaches it, leaving the token at the place
    that licence names: it is callable only where the caller's own contract
    licenses an engagement naming that editor and that pair of names.
    (mapping.md)"""
    IOExists1(Place)(
        lambda t_post: (
        # The index's current name is only READ here: the primitive, not this
        # model, is what moves a name in the database.
        Requires(Acc(old_index.name, 1 / 2)),
        Requires(Acc(editor.rename_issued) and Acc(editor.renamed_to)),
        # The backend rename primitive may only be engaged when the existing
        # index's current name actually differs from the target: asking the
        # backend to rename an index to a name that is already in use is
        # forbidden (it would fail). The caller therefore MUST establish this
        # before engaging -- so engaging in the equal-names case is a
        # verification error, not an effect that can be performed and then
        # papered over by resetting an observability flag.
        Requires(old_index.name != new_name),
        Requires(token(t_pre, 2) and
                 rename_index_io(t_pre, editor, old_index.name, new_name, t_post)),
        Requires(MustTerminate(2)),
        Ensures(token(t_post)),
        Ensures(Acc(old_index.name, 1 / 2)),
        Ensures(Acc(editor.rename_issued) and Acc(editor.renamed_to)),
        Ensures(editor.rename_issued is True),
        Ensures(editor.renamed_to == new_name),
        )
    )
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end

def rename_existing_index(t_pre: Place, editor: SchemaEditor,
                          old_index: ExistingIndex, new_name: int) -> None:
    IOExists1(Place)(
        lambda t_renamed: (
        # pre-conditions-start
        # TERMINATION: deciding whether to rename is a bounded, loop-free step
        # that MUST actually complete and hand control back to the migration
        # executor (total correctness). Under partial-correctness semantics a
        # diverging body (e.g. an endless loop before the rename decision)
        # satisfies every Ensures clause only vacuously yet never returns; the
        # real step always returns. This obligation rejects any such
        # implementation.
        Requires(MustTerminate(3)),
        # The index's current name is READ-ONLY to the step (a share, not full
        # permission): the step's job is to decide whether to ask for a rename,
        # not to move the name itself. So it can neither manufacture the
        # primitive's outcome by writing the name, nor step outside the
        # primitive's domain restriction by moving the name first and asking
        # afterwards.
        Requires(Acc(old_index.name, 1 / 2)),
        Requires(Acc(editor.rename_issued) and Acc(editor.renamed_to)),
        Requires(editor.rename_issued is False),
        # The step arrives holding a token and a licence for exactly ONE
        # engagement of the schema primitive: through the editor it was handed,
        # about the index it was handed (named by the name that index currently
        # carries), asking for exactly the target name. The licence is given on
        # EVERY input the step accepts -- the equal-name case is not privileged by
        # withholding the capability, it is required to decline to use one it
        # holds. That single licence is the whole effect budget: no second
        # engagement, none through another editor, and none naming any other pair
        # of names is available to any implementation, whatever it reports.
        Requires(token(t_pre, 3) and
                 rename_index_io(t_pre, editor, old_index.name, new_name,
                                 t_renamed)),
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(old_index.name, 1 / 2)),
        Ensures(Acc(editor.rename_issued) and Acc(editor.renamed_to)),
        # (2) The licensed engagement HAS BEEN MADE, exactly once: the step ends
        # holding a token at the place that single licence names, which is
        # reachable only by engaging the primitive through the editor it was
        # handed, about the index it was handed, asking for exactly the target
        # name -- and which cannot be reached twice, because no second licence
        # exists. So the alteration is never reported unasked, the ask that
        # happened named that pair of names and no other, and the index is never
        # routed to the target by way of some other name.
        Ensures(Implies(Old(old_index.name) != new_name, token(t_renamed))),
        # (1) The no-alteration case is a COMPLETE no-op: the step ends still
        # holding the very token it arrived with, at the very place it arrived at,
        # with its measure intact, AND the engagement licence STILL UNSPENT. It
        # held the capability to engage the primitive and declined to use it, so
        # nothing whatsoever was asked of the schema primitive -- not once, and
        # about no pair of names. This is the clause a report cannot satisfy: an
        # unspent licence is not something an implementation can still be holding
        # after having spent it, however it describes what it did.
        Ensures(Implies(Old(old_index.name) == new_name,
                        token(t_pre, 3) and
                        rename_index_io(t_pre, editor, Old(old_index.name),
                                        new_name, t_renamed))),
        # (1)+(2) restated as the value the editor records: the primitive was
        # asked for a rename iff the current name differed from the target.
        Ensures(editor.rename_issued == (Old(old_index.name) != new_name)),
        # When (and only when) the primitive was asked, it was asked for exactly
        # the target name.
        Ensures(Implies(editor.rename_issued, editor.renamed_to == new_name)),
        # (1) from the other side -- when nothing was asked, the record of what
        # the primitive was last asked to rename to is left exactly as the step
        # found it. An implementation that asks the primitive anyway and only
        # reports "no rename happened" afterwards has still touched the schema,
        # and does not satisfy this.
        Ensures(Implies(not editor.rename_issued,
                        editor.renamed_to == Old(editor.renamed_to))),
        # post-conditions-end
        )
    )
    # impl-start
    # POSITIVE CONTROL: correct but restructured (negated guard). Engage only
    # on the differing-names branch; the equal-names branch falls through with
    # the licence unspent. Behaviourally identical to gold. MUST verify.
    if old_index.name != new_name:
        issue_rename(t_pre, editor, old_index, new_name)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ ADVERSARIAL AUDIT (refinement fidelity) — django__django-15695 / nagini. VERDICT: SOUND (advisory). 16 same-spec wrong-impl attacks + 1 positive control run; all 3 CANDIDATEs had faithful refined patches MATERIALIZED and EXECUTED through the official Docker harness, and ALL 3 RESOLVE. No verify-but-wrong impl found.

COMMANDS (from repo root swe-proof), attacks launched 3-at-a-time as background jobs:
  python -m swebench_unified.adversary same-spec nagini django__django-15695 <D>/atk_N.py   -> SAME (all 16 + pos_control)
  python -m swebench_unified.adversary weakness  nagini django__django-15695 <D>/atk_N.py   (0=CANDIDATE, 2=rejected)
  bash scripts/nagini_verify.sh benchmark-verified/django__django-15695/nagini/model_prepatch.py
  run_resolve('django__django-15695', <patch>) via swebench_unified.harness (Docker, docker) — driver <D>/resolve.py

### PER-ATTACK RESULTS (observed weakness exit code):
atk_1.py  PREPATCH BUG (no guard; engage unconditionally) -> exit 2, does not verify. REJECTED. atk_2.py  UNGROUNDED-ORACLE ECHO (gold guard; on the differ branch merely WRITE editor.rename_issued=True/renamed_to=new_name instead of engaging) -> exit 2. REJECTED — the IO token at the licensed place is unreachable by a self-report. atk_3.py  PROXY SUBJECT (prior pass's named counterexample re-encoded: engage about a fresh ExistingIndex(old_index.name), not the object handed in) -> exit 0 CANDIDATE (verifies 18.6s). PATCH MATERIALIZED + RESOLVED. atk_4.py  TRANSIENT LAUNDER (prior pass's other named counterexample: on the equal branch save/set-to-target/restore rename_issued+renamed_to, so 'record left as found' holds by save/restore) -> exit 0 CANDIDATE (verifies 19.3s).

PATCH MATERIALIZED + RESOLVED. atk_5.py  PARTIAL DOMAIN (always `return`; correct only on the equal-names sub-domain) -> exit 2. REJECTED. atk_6.py  BOUNDARY / sentinel carve-out (also decline whenever new_name == 0, the identifier mapping.md declares is never a real name) -> exit 2. REJECTED. atk_7.py  CONTROL-FLOW-EFFECT / MULTIPLICITY (gold guard, issue_rename TWICE; reported values bit-for-bit gold's, only the COUNT differs) -> exit 2. REJECTED — the second engagement has no licence. atk_8.py  NOVEL PRIVATE-EDITOR RECORD on the no-op branch (on the equal branch procure a SchemaEditor() of the step's own and write a full rename record onto it before returning; caller's editor + licence untouched) -> exit 0 CANDIDATE (verifies 17.1s).

PATCH MATERIALIZED + RESOLVED. atk_9.py  NOVEL LAUNDERED EDITOR, engaged (engage through a private editor whose work the caller never sees, then report success on the caller's) -> exit 2. REJECTED — the licence names the editor handed in. atk_10.py NON-TERMINATION (honest no-op on equal; unbounded `while i >= 0` in place of the rename on the differ branch — vacuous under partial correctness) -> exit 2. REJECTED by MustTerminate. atk_11.py VACUITY CONTROL, equal-names branch: Assert(False) -> exit 2 (FAILS) => branch IS reachable; the no-op obligations are not vacuous. atk_12.py VACUITY CONTROL, differing-names branch: Assert(False) -> exit 2 (FAILS) => that branch is reachable too.

Both controls behave as required (per the guarded-self-call-goes-vacuous hazard). atk_13.py NOVEL UNGROUNDED DISCRIMINATOR (branch on `old_index.name == editor.renamed_to`; the precondition pins rename_issued is False but leaves renamed_to UNCONSTRAINED) -> exit 2. REJECTED. atk_14.py NOVEL MULTIPLICITY via a TERMINATING bounded loop (engage inside `while i < 2` with Invariant(MustTerminate(2-i)) so MustTerminate alone cannot reject it) -> exit 2. REJECTED — the single licence caps the count regardless of control flow. atk_15.py INVERTED GUARD (engage exactly when the names are EQUAL) -> exit 2. REJECTED. atk_16.py PARTIAL DOMAIN on an ORDER slice (engage only where old_index.name < new_name; names are equality-compared only per mapping.md §2, so ordering is ungrounded) -> exit 2. REJECTED. pos_control.py CORRECT-but-restructured (negated guard `if old_index.name != new_name: issue_rename(...)`) -> exit 0, VERIFIES in 19.9s. Spec is not too strong.

**PREPATCH REPRODUCED:** yes. `bash scripts/nagini_verify.sh .../model_prepatch.py` -> exit 1, 'Verification failed / model_prepatch.py:252:5:252:53: error: The precondition of method issue_rename might not hold. Assertion (old_index.name != new_name) might not hold.' Matches meta.json prepatch_models.fails_on (that field cites :113, stale w.r.t. the current 252-line model — cosmetic).

MANDATORY RESOLVE RUNS FOR EVERY CANDIDATE (the load-bearing evidence). Worktree at base_commit 647480166bfe7532e8c471fef0146e3a17e6c0c9 (<D>/wt, git worktree from the upstream repository); all three `git apply --check` APPLY:
  atk_3 -> <D>/patch_atk_3.diff. Refinement: gold guard + `schema_editor.rename_index(model, old_index.clone(), new_index)` (Index.clone() re-deconstructs, preserving name and fields — the faithful reading of `proxy = ExistingIndex(old_index.name)` under mapping.md §2, where ExistingIndex carries ONLY the name).
     EXECUTED: RESOLVED=True COMPLETED=True note='resolved'; patch_successfully_applied=true; F2P success=['test_rename_index_unnamed_index'], failure=[]; P2P failure=[]. Log <D>/resolve_atk_3.txt.
     Why it resolves rather than breaking the spec: rename_index reads only old_index.name (schema.py:496-504 -> `_rename_index_sql`(model, old_index.name, new_index.name)); the can_rename_index=False fallback (sqlite, the F2P backend) calls remove_index(model, old_index), which consumes only .name/.fields via Index.remove_sql -> `_delete_index_sql`(model, self.name). A clone carrying the same name and fields is observationally identical, so this is a genuine same-behaviour rival: the licence binds the SOURCE NAME, which is all mapping.md §2 abstracts. Not a hole.
  atk_4 -> <D>/patch_atk_4.diff. Refinement: gold early return preceded by save / set-to-target / restore of the step's own record of what a rename would have asked for (the model's rename_issued/renamed_to carriers, as sbu_* attributes on the editor; no rename_index call, so the primitive is never engaged on that branch).
     EXECUTED: RESOLVED=True COMPLETED=True note='resolved'; F2P success=['test_rename_index_unnamed_index'], failure=[]; P2P failure=[]. Log <D>/resolve_atk_4.txt.
     Why it resolves: the carriers are the model's own observability record, not repo state any test reads; the SQL-emitting primitive is still never engaged on the equal-names path, so assertNumQueries(0) and the F2P re-apply are unaffected. The 'record kept' clause is indeed satisfiable by save/restore rather than only by non-interference — a modelling looseness with NO behavioural consequence, because the completeness of the no-op is carried by the UNSPENT-LICENCE clause (Ensures(Implies(Old(old_index.name)==new_name, token(t_pre,3) and rename_index_io(...)))), not by the resettable record. That architecture is what makes atk_1/atk_2/atk_7 fail.
  atk_8 -> <D>/patch_atk_8.diff. Refinement: gold decision, but on the equal-names branch procure `schema_editor.connection.schema_editor(collect_sql=True)` and record the rename onto that private object, then return.
     EXECUTED: RESOLVED=True COMPLETED=True note='resolved'; patch_successfully_applied=true; F2P success=['test_rename_index_unnamed_index'], failure=[]; P2P failure=[]. Log <D>/resolve_atk_8.txt.
     Why it resolves: constructing an editor emits no SQL and the private one is never entered as a context manager / never executes, so the caller's editor still emits zero statements on the no-op path. The spec's 'COMPLETE no-op' is scoped to the editor the caller supplied — which is exactly the right scope, since only that editor's statements are observable to the migration executor and to assertNumQueries(0).

### REFINEMENT.MD LEG AUDIT (§5 kinds; every leg R / A-consumed / A-reference / I — NO kind-3):
A1 `old_index: ExistingIndex` + `.name` -> the join-point old_index from either branch: **R**. VERIFIED against the real source at base_commit: both producers (models.py:956-959 `models.Index(fields=self.old_fields, name=matching_index_name[0])`, and :961-962 `from_model_state.get_index_by_name(self.old_name)`) yield an object whose .name is the current DB name; the guard at the join reasons only about that field. Correspondence holds. A2 `new_name: int` -> `self.new_name`: **R**. VERIFIED: ModelState.get_index_by_name (state.py:955-959) returns the index whose `.name == name`, so new_index.name == self.new_name and one int carrier legitimately stands for both. Equality-only abstraction is consistent with the impl (names never indexed/sliced).

A3 `if old_index.name == new_name: return` -> the gold guard: **I**. VERIFIED byte-for-byte against patch.diff: `# Don't alter when the index name is not changed. / if old_index.name == self.new_name: / return` inserted between :962 and :964, i.e. BEFORE the new_index lookup and before rename_index. The single added hunk; the model impl is the same equality-compare-and-early-return. A4 `issue_rename` -> `BaseDatabaseSchemaEditor.rename_index`: **A-reference**. VERIFIED the callee text at base_commit is byte-identical to the block mapping.md §3.1 quotes (schema.py:496-504; diffed against <D>/callee_actual.txt). meta.json axioms == [] and deep_model_references records exactly this one A-reference; model.py has exactly ONE @ContractOnly (issue_rename).

Its Ensures ARE used by the proof, so 'A-reference validated out-of-band by G-AX' is the accurate label only because the axiomatized callee is the UNCHANGED one — the function under change (the guard) is NOT axiomatized, it is the I-tagged step. axiom_check.py drives the real primitive on sqlite to ground both facts the deep model pins (rename moves old->new; creating a name already present raises). No kind-3 leg exists.

ADDITIONAL PROBE — guard PLACEMENT is load-bearing but NOT model-visible (advisory, does NOT break G-EQ): <D>/patch_probe_after_lookup.diff moves the gold guard to AFTER `new_index = to_model_state.get_index_by_name(self.new_name)`, keeping the identical model-level decision (engage the primitive iff the names differ). EXECUTED: run_resolve -> RESOLVED=False COMPLETED=True note='patch did not resolve in 3 attempts (consistent — not flaky)'; patch_successfully_applied=true; F2P failure=['test_rename_index_unnamed_index']. Log <D>/resolve_probe.txt.

Mechanism: on the F2P re-apply the call is `database_forwards(app_label, editor, new_state, project_state)`, so to_state = project_state — the ORIGINAL state, to which state_forwards never added an index named 'new_pony_test_idx' in the old_fields (unnamed) case. get_index_by_name therefore raises ValueError. Gold returns BEFORE that lookup; the probe reaches it and crashes. Why this is NOT a G-EQ break: it is a repo-level statement-ORDER variant, not a same-spec model impl.

The model has no carrier for the to_state/new_index lookup at all (mapping.md §2 collapses self.new_name and new_index.name into one int parameter), so NO edit confined to model.py's impl region can express this variant — every model impl that verifies decides the engagement from parameters already in hand and cannot resurrect the lookup. Confirmed empirically: the 16 same-spec attacks include every shape the carriers admit, and none is this one.

The correspondence is preserved by refinement.md A3/§B, which pin the guard's position ('returns BEFORE new_index is looked up and before schema_editor.rename_index(...) is reached (models.py:966)') — i.e. the placement is discharged by the refinement MAP rather than by the spec, which is the legitimate division of labour for a detail the abstraction elides. Flagging it because it is the one place where a reader trusting the model alone would under-constrain the transliteration: a future refinement.md edit that dropped the 'before the new_index lookup' wording would silently license a non-resolving patch.

DOC DRIFT (advisory, NOT a G-EQ break — no leg's correspondence fails and no verifying impl misbehaves; each drift makes the doc claim the spec is STRONGER than it is, never weaker, so none can license an unsound impl):
  1. refinement.md:113 and :115 cite `Ensures(old_index.name == new_name)` as a clause 'pinning the post-state in both cases', and §D repeats 'leaving the index at the target name in both cases'. NO SUCH CLAUSE EXISTS in model.py (grep: 0 hits among the Ensures) — and correctly so: the docstring's own scope note explains rename_index is capability-gated, and old_index.name is held at a 1/2 read-only share precisely so the step cannot manufacture the primitive's outcome (which is what makes a domain-escape attack fail). mapping.md §2/§3.1 and meta.json deep_model_references likewise still describe issue_rename as effecting `old_index.name = new_name`, which the actual axiom does not do.
  2. refinement.md:116-117 states 'Requires(MustTerminate(2)) on rename_existing_index (with the strictly smaller MustTerminate(1) on issue_rename …)'. Actual measures in model.py: 3 on rename_existing_index, 2 on issue_rename, 1 on the constructors. The ordering argument is intact (strictly decreasing); only the numerals are stale.
  3. refinement.md §B cites the atk_2/atk_6 counterexample numbering of an EARLIER audit pass, which no longer matches this pass's file numbering — harmless provenance prose, but it reads as a stable reference and is not one.
  4. meta.json prepatch_models.fails_on cites model_prepatch.py:113; the observed error is at :252. Same clause and message, stale line number.
  Recommend a refinement.md/mapping.md prose refresh so §B/§D quote clauses that exist and the measures match.

**BASIS FOR SOUND:** 16 distinct wrong-impl families run (prepatch bug; ungrounded-oracle echo; partial-domain x3 incl. an order slice; boundary/sentinel; control-flow-effect/multiplicity x2 incl. a terminating-loop variant that MustTerminate alone cannot reject; non-termination; laundered-editor x2; proxy/transient-launder x2; ungrounded discriminator; inverted guard) — 13 of 16 REJECTED by the frozen spec; all 3 CANDIDATEs had faithful patches materialized and EXECUTED through the official Docker harness and ALL 3 RESOLVED; the positive control verifies (spec not too strong); both vacuity controls FAIL (both branches reachable, obligations non-vacuous); the prepatch bug is reproduced with the documented failing clause; all 4 refinement.md legs are R/I/A-reference with verified correspondence to the real callees at base_commit and no kind-3 leg. No evidence of verify=>correct being violated.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** VERDICT: FAITHFUL — no input found on which the modeled function disagrees with the real callee. Reference used correctly: patch.diff APPLIED worktree () for rename_existing_index; base_commit worktree (, 647480166b) for the untouched callee rename_index.

INTEGRITY / MACHINE CHECKS RUN
- same-spec (identity copy of model.py): exit 0, 'SAME — attack shares the bundle's exact specification'. Spec region byte-identical baseline established.
- nagini_verify.sh model.py: 'Verification successful' (17.75s).
- nagini_verify.sh model_prepatch.py: FAILS at model_prepatch.py:252 — 'The precondition of method issue_rename might not hold. Assertion (old_index.name != new_name) might not hold.' Matches meta.json prepatch_models exactly (G-DIFF intact).
- axiom_check.py against patched tree: exit 0, 5 observations.
- conformance_check.py against the REAL patched RenameIndex.database_forwards: exit 0, 100024 inputs, 0 disagreements; leg A 100000 with BOTH old_index producers non-vacuous (named equal/differ 20270/29879, unnamed equal/differ 20161/29690), leg B 7 real-sqlite drives incl. the F2P re-apply no-op, leg C 17 bridge checks, seed=15695. This is the direct faithfulness evidence for my lane: the modeled function's observable behavior (rename_issued / renamed_to) matches the real patched callee on 100k inputs.
- F2P ground truth confirmed at base: applied the gold test hunk of 11310e9abb to the base worktree; test_rename_index_unnamed_index ERRORs with 'ValueError: No index named new_pony_test_idx on model Pony' at models.py:965. Bug is real and the spec senses it.

### Attack I mounted and why it does not establish unfaithfulness
I targeted the load-bearing tightening Requires(old_index.name != new_name) on issue_rename, hypothesizing it is too strong (forbids an operation the real callee permits).

(1) Probed the real base-commit BaseDatabaseSchemaEditor.rename_index with old_index.name == new_index.name on sqlite: it SUCCEEDS. Emitted SQL is 'DROP INDEX "idx_a"; CREATE INDEX "idx_a" ON "contenttypes_thing" ("val")'; ran twice, index intact, no exception. can_rename_index=False on sqlite (base default False; True only on postgresql/oracle/mysql-conditional).

(2) Built the rival repo patch that engages the primitive on the equal-names branch (schema_editor.rename_index(model, old_index, old_index) then return) — precisely what the spec's precondition forbids. It PASSES the F2P test and the full migrations suite (667 tests, OK, skipped=1) on sqlite. Worktree restored to clean base afterwards.
So on the can_rename_index=False fallback the forbidden operation is benign, and the spec is strictly stricter than sqlite alone requires.
HOWEVER this is NOT a drift from real repo behavior: on the can_rename_index=True path the primitive emits 'ALTER INDEX "x" RENAME TO "x"' (verified via `_rename_index_sql`), and the instance's own problem_statement records exactly that failure — 'django.db.utils.ProgrammingError: relation "new_pony_test_idx" already exists' on PostgreSQL. The precondition is therefore faithful to the real callee on the backend whose behavior motivated the patch, and the gold patch is itself backend-independent (it skips the rename on every backend). A rival that renames X->X is only accidentally safe on sqlite; its faithful refinement reintroduces the reported PG crash. I decline to score this as UNFAITHFUL.

(3) Diagnostic on whether the precondition is the only thing sensing the bug: stripped ONLY that Requires from model_prepatch.py and re-verified — still FAILS, at the complete-no-op postcondition ('insufficient permission to access rename_index_io(t_pre, editor, Old(old_index.name), new_name, t_renamed)'). The IO-token clause rejects the pre-patch independently, so the spec's bug-sensing does not rest solely on the clause I attacked.

### DOCUMENTATION DEFECTS FOUND (evidence/prose drift, NOT behavioral divergence — reported for repair, they do not change the verdict)
(a) refinement.md:113-114 cites 'Ensures(old_index.name == new_name)' as a clause that 'pins the post-state in both cases', and mapping.md:40 says issue_rename 'effects old_index.name = new_name'. THAT CLAUSE DOES NOT EXIST in model.py (grep count 0). issue_rename holds only Acc(old_index.name, 1/2) — a read share — so it cannot write the name at all. refinement.md §D's 'leaving the index at the target name in both cases' describes a post-state the frozen spec never pins. Whether that under-pinning admits a bad impl is lane 1's question; for my lane it means the docs OVERSTATE the spec rather than the spec overstating the repo.

(b) axiom_check.py part (2) is a non-sequitur on the backend it actually runs. It tests that add_index of an already-present name raises (confirmed: OperationalError) and concludes that rename_index with equal names 'is exactly the operation that must be skipped'. But rename_index on the can_rename_index=False path does remove_index FIRST then add_index, so the name is free by the time add_index runs — I measured (a) duplicate add_index RAISES and (b) rename_index(X->X) SUCCEEDS in the same session. The check's premise does not establish its conclusion; the real justification is the PG ALTER INDEX path, which axiom_check never exercises. mapping.md §3.1 states the PG rationale correctly, so this is a weak-evidence defect in the G-AX script, not a false spec claim.

(c) Minor: refinement.md §B claims MustTerminate(2) on rename_existing_index and MustTerminate(1) on issue_rename; model.py actually carries MustTerminate(3) and MustTerminate(2) respectively (measures still strictly decreasing, so the termination argument stands).

**CONCLUSION:** the modeled function agrees with the real patched database_forwards on all 100024 conformance inputs including both old_index producers and the real sqlite backend; the one over-restriction I could construct (equal-names rename) is faithful to the real callee on PostgreSQL where the reported crash occurs. No diverging input. Recommend repairing (a) the phantom Ensures(old_index.name == new_name) citation in refinement.md/mapping.md, (b) axiom_check.py part (2) so it exercises the ALTER INDEX X->X path or drops the unsupported inference, and (c) the MustTerminate measures in refinement.md.

**VERDICT:** FAITHFUL — no input found on which the modeled function disagrees with the real callee. Reference used correctly: patch.diff APPLIED worktree () for rename_existing_index; base_commit worktree (, 647480166b) for the untouched callee rename_index.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE + ARTIFACT IDENTITY (measured live from bundle bytes, nothing inherited). Judged artifact = markers.spec_view(model.py, get_backend('nagini').language). live model.py sha256 = f3b93697e54e9b2e792b6f3ab4ffc3b438a9af0974d4199d79da504ab0bcc457 (== meta gates.G-LEAK.sources / G-HYGIENE.sources / G-VERIFY.sources, so those stamps describe the bytes I screened). live spec_view sha256 = 7954eb605841214f7ec98bac111154d1bb63ad1d0504e0bb3b7a6bf9a252db99 == meta G-HYGIENE.data.region_hashes.spec_view. spec_view idempotent (spec_view(spec_view(x))==spec_view(x)). same_spec(model.py, model_prepatch.py)=True and `adversary same-spec nagini django__django-15695` exits 0 on both an identity copy of model.py AND on model_prepatch.py -- so the judged region is byte-identical across the twins and nothing inside it distinguishes post- from pre-patch. Judged against the solver-visible problem_statement ONLY; hints_text used solely as an exclusion oracle.

NO RELAXATION IS IN PLAY -- I checked rather than assumed. No RELAXED_LEAKAGE.md anywhere under the instance dir (os.path.exists == False); 'relaxed_leakage' not in meta.json (top-level keys are additional_change_sites, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version); meta gates.G-LEAK.status == 'pass', mode 'strict', not 'relaxed'. So there is no unavoidability argument to re-derive and no disposition to weigh -- I judged at the STRICT bar.

**OFFICIAL SCREEN RE-RUN INDEPENDENTLY:** leakage.screen(model.py, nagini language, gold_patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[].

L1 (gold lines / diff markers). The gold hunk adds exactly three lines: "# Don't alter when the index name is not changed.", 'if old_index.name == self.new_name:', 'return'. Whitespace-normalized, neither substantive line is present in the view; I also applied a LOOSER match than the official screen (stripping the 'self.' qualifier so a de-qualified transliteration 'ifold_index.name==new_name:' would hit) -- still absent. Only the content-free 'return' collides, carrying zero localization. The narrating impl comment 'The FIX: don't alter when the current name already equals the target.' and the guard body live entirely inside impl-start/impl-end and are GONE from the view (replaced by the ELISION sentinel 'implementation elided -- supplied by the consumer'); 'FIX'/'fix' occurs zero times in the view, though 'FIX' IS present in the full model.py -- i.e. the elision, not authorial restraint, is what removes it, and I confirmed the elision actually fires. No diff marker ('@@', 'diff --git', '+++ ', '--- ', '\nindex ') in the view.

L2 (paths). 'django/db/migrations/operations/models.py' absent; dotted module form absent; no line numbers from the mapping (960/962/966/934, 'models.py:934', '960-966' all absent).

L3/L4 (symbols, hints-only vocabulary). `_patch_changed_symbols`(gold) = {'database_forwards'} -- absent from the view. Also absent: RenameIndex, schema_editor, get_index_by_name, from_state, to_state, app_label, model_name_lower, `_constraint_names`, matching_index, ProjectState, unique_together, max_name_length, `_create_index_name`, 'auto-generated', 'noop', 'ticket', '27064'. F2P test identity absent: 'pony', 'new_pony', 'test_idx', 'assertNumQueries', 'test_rename'. I diffed the view's 4+-char word set against (hints_text \ problem_statement): the only survivors are English function words plus 'implementation'/'impl'/'schemaeditor' -- none a diagnosis or a hints-only discriminator ('SchemaEditor' here is the model's own carrier class for the editor object, not the hints' SchemaEditor.`_create_index_name`, which is absent). Narration scan (`_NARRATION_RE`) over the view: ZERO hits (the sole hit in full model.py, 'FIX', is inside the elided impl). No 'guard', 'early return', 'branch', 'join', 'forward', 'backward', 'Postgre' in the view.

DE-NARRATION CONTROL (the load-bearing test, run rather than argued). Built denarrated_gold.py: model.py with the module docstring, every function/class docstring and every non-marker comment mechanically stripped -- i.e. the formal contracts alone, no prose. `bash scripts/nagini_verify.sh` exit 0. Then the same de-narrated file with ONLY the impl region reverted to the pre-patch unguarded body (denarrated_pre.py): exit 1, 'The precondition of method issue_rename might not hold. Assertion (old_index.name != new_name) might not hold.' So the discrimination between gold and pre-patch is carried ENTIRELY by the Requires/Ensures (issue_rename's domain restriction old_index.name != new_name, plus the unspent-licence no-op clause), and NONE of the removed prose is load-bearing. The prose is therefore removable without weakening the spec -- and having read it, it also does not name the edit: it states the abstract obligation (idempotence w.r.t. the target name; complete no-op vs. engage-exactly-once) rather than 'add an early return at the branch join'. Baseline controls: unmodified model.py verifies (exit 0), model_prepatch.py fails (exit 1), matching G-GOLD/G-DIFF.

**DERIVABILITY FROM THE PUBLIC PS.** The discriminator the spec names -- 'if the existing index's current name already equals the target, ask the backend for nothing' -- is derivable from problem_statement alone, so it is not a leak 'beyond' it. The PS carries: the title 'RenameIndex() crashes when unnamed index is moving backward and forward'; the added test body re-applying database_forwards and then asserting assertIndexNameExists(table_name, "new_pony_test_idx"); and the failure 'ProgrammingError: relation "new_pony_test_idx" already exists'. A solver reading only that derives that on re-application the index is ALREADY at the target name and the step must not ask the backend to rename it there again.

The one borderline term is 'IDEMPOTENT' in the docstring, which is lexically hints-only ('idempotency' appears in hints_text, not in PS) -- but it is a restatement of what PS exhibits verbatim ('# Re-apply renaming.' followed by an assertion that the index survives), not a hints-only mechanism or symbol, and it names a property rather than the edit. I am not treating it as a leak. The view's identifiers old_index/new_name echo variable names that are PRE-EXISTING context at the modeled function (models.py:961-965), not fix-introduced names, and mode 1/2 grant edit localization by design, so they add nothing the consumer lacks.

**NO FILE ADDRESSES THE REVIEWER.** leakage.reviewer_directed() -> [] on model.py, model_prepatch.py, mapping.md, refinement.md, axiom_check.py, conformance_check.py, properties.py, meta.json. I additionally grepped every bundle file for panel/reviewer/auditor/attacker/G-PANEL/G-LEAK/NO-LEAKAGE/submit_result/verdict/'should record'/honest: the only hits are retrospective descriptions of which gate a clause answers (refinement.md:99 'closes the audited G-EQ / G-PANEL-1 counterexample'; properties.py test-case prose using 'honest no-op' as a shape label) plus meta.json's own recorded gate stamps. None instructs me how to record or which verdict is honest, so there is no steering finding to report.

OUT-OF-SCOPE OBSERVATION (recorded, not my verdict). meta.json modeled_functions[0].role quotes the gold guard verbatim ("the gold no-op guard 'if old_index.name == self.new_name: return' is added at the join of the two old_index-computing branches"), and mapping.md reproduces the whole gold hunk in a fenced block. Neither is part of the spec view, so neither bears on this gate, and I confirmed by BUILDING the real mode-1 prompt (eval.prompts.initial_user on dataset.build_task(adapter,'django__django-15695',1)) that the agent-visible text renders only 'Modeled function(s): rename_existing_index (<-> ...RenameIndex.database_forwards), issue_rename (<-> ...BaseDatabaseSchemaEditor.rename_index)' -- the guard string, 'no-op guard', 'join of the two', carrier_type and the line numbers are all absent from the prompt. They DO land in the persisted task.json, because dataset.as_dict emits the full modeled_functions dicts while its docstring claims 'only agent-allowed fields'; that is a harness record-hygiene note for the gold-mapping files, not spec-view leakage, and assert_no_leak's WITHHELD_FIELDS check is unaffected.

**VERDICT:** the spec view reproduces no gold line, names no patched path/symbol/line, carries no bug->fix narration and no hints-only discriminator; its discriminating content is formal contracts that are independently derivable from the public problem_statement, and the de-narration control proves the prose is not load-bearing. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
