# P2 adversarial audit — sphinx-doc__sphinx-9461

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -225,9 +225,6 @@
     if has_abstract:
         result = result + [97, 98, 115, 116, 114, 97, 99, 116]
         result = result + [32]
-    if has_classlevel:
-        result = result + [99, 108, 97, 115, 115]
-        result = result + [32]
     result = result + [112, 114, 111, 112, 101, 114, 116, 121]
     result = result + [32]
     return result
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -256,9 +256,6 @@
     if is_property:
         establish_documented(member_id)
         return True
-    if is_classlevel_property:
-        establish_documented(member_id)
-        return True
     return False
     # impl-end
 
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -320,7 +320,7 @@
     Ensures(Implies(Result(), retained_in_class_walk(member_id)))
     # post-conditions-end
     # impl-start
-    text_resolves = has_descriptive_text
+    text_resolves = has_descriptive_text and not is_classlevel_property
     if text_resolves:
         establish_retained(member_id)
         return True
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -287,11 +287,7 @@
     # impl-start
     result = []  # type: List[int]
     if is_abstract:
-        result = result + [32, 32, 32, 58, 97, 98, 115, 116, 114, 97, 99, 116,
-                           109, 101, 116, 104, 111, 100, 58]
-    if is_classlevel_property:
-        result = result + [32, 32, 32, 58, 99, 108, 97, 115, 115,
-                           109, 101, 116, 104, 111, 100, 58]
+        result = result + [32, 32, 32, 58, 97, 98, 115, 116, 114, 97, 99, 116, 109, 101, 116, 104, 111, 100, 58]
     return result
     # impl-end
 
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -222,11 +222,11 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
+    if has_classlevel:
+        result = result + [99, 108, 97, 115, 115]
+        result = result + [32]
     if has_abstract:
         result = result + [97, 98, 115, 116, 114, 97, 99, 116]
-        result = result + [32]
-    if has_classlevel:
-        result = result + [99, 108, 97, 115, 115]
         result = result + [32]
     result = result + [112, 114, 111, 112, 101, 114, 116, 121]
     result = result + [32]
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -253,11 +253,7 @@
     Ensures(Implies(Result(), documented_as_property(member_id)))
     # post-conditions-end
     # impl-start
-    if is_property:
-        establish_documented(member_id)
-        return True
-    if is_classlevel_property:
-        establish_documented(member_id)
+    if is_property or is_classlevel_property:
         return True
     return False
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -352,10 +352,8 @@
     # impl-start
     result = []  # type: List[int]
     if is_abstract:
-        result = result + [32, 32, 32, 58, 97, 98, 115, 116, 114, 97, 99, 116,
-                           109, 101, 116, 104, 111, 100, 58]
-    if is_classlevel_property:
-        result = result + [32, 32, 32, 58, 99, 108, 97, 115, 115,
-                           109, 101, 116, 104, 111, 100, 58]
+        result = result + [32, 32, 32, 58, 97, 98, 115, 116, 114, 97, 99, 116, 109, 101, 116, 104, 111, 100, 58]
+    if is_abstract:
+        result = result + [32, 32, 32, 58, 99, 108, 97, 115, 115, 109, 101, 116, 104, 111, 100, 58]
     return result
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -320,11 +320,8 @@
     Ensures(Implies(Result(), retained_in_class_walk(member_id)))
     # post-conditions-end
     # impl-start
-    text_resolves = has_descriptive_text
-    if text_resolves:
-        establish_retained(member_id)
-        return True
-    return False
+    establish_retained(member_id)
+    return True
     # impl-end
 
 
```

Attack 9 — `atk_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -221,15 +221,11 @@
     Ensures(ToSeq(Result()) == expected_prefix(has_abstract, has_classlevel))
     # post-conditions-end
     # impl-start
-    result = []  # type: List[int]
+    result = [112, 114, 111, 112, 101, 114, 116, 121, 32]  # type: List[int]  # 'property '
+    if has_classlevel:
+        result = [99, 108, 97, 115, 115, 32] + result  # prepend 'class '
     if has_abstract:
-        result = result + [97, 98, 115, 116, 114, 97, 99, 116]
-        result = result + [32]
-    if has_classlevel:
-        result = result + [99, 108, 97, 115, 115]
-        result = result + [32]
-    result = result + [112, 114, 111, 112, 101, 114, 116, 121]
-    result = result + [32]
+        result = [97, 98, 115, 116, 114, 97, 99, 116, 32] + result  # prepend 'abstract '
     return result
     # impl-end
 
@@ -253,10 +249,8 @@
     Ensures(Implies(Result(), documented_as_property(member_id)))
     # post-conditions-end
     # impl-start
-    if is_property:
-        establish_documented(member_id)
-        return True
-    if is_classlevel_property:
+    qualifies = is_property or is_classlevel_property
+    if qualifies:
         establish_documented(member_id)
         return True
     return False
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-9461.

Two desired behaviours are specified (stated as desired behaviour, not as an
edit). Both concern how a property whose binding is at the class level is
rendered.

== Behaviour 1: the qualifier prefix ==

  A property description carries a textual qualifier prefix assembled from a
  predetermined ordered vocabulary of role words, each word emitted in canonical
  order and followed by a single separating space (so the whole prefix ends with
  a trailing space). The word `property` is ALWAYS present and is the LAST word.
  Two optional qualifiers may precede it, in this canonical order:

    1. the abstractness qualifier `abstract`, present iff the description is
       marked abstract;
    2. the class-level qualifier `class`, present iff the description is marked
       as bound at the class level.

  Thus the prefix for an ordinary property is `property `; an abstract
  property is `abstract property `; a class-level property is `class property `;
  a property that is both is `abstract class property `. The class-level
  qualifier must contribute its own word even when the abstractness qualifier
  is absent.

== Behaviour 2: discovery and option-line emission ==

  When a member of a class is examined for automatic documentation, a member
  qualifies for documentation as a property when it is a property, AND ALSO when
  it is a class-level property (a property whose access is bound at the class
  level). A member that is neither does not qualify. Only a member that
  qualifies has documentation emitted for it at all.

  For a member that qualifies, an ordered block of option lines is emitted. The
  abstractness option line is emitted iff the member is marked abstract; the
  class-level option line is emitted iff the member is a class-level property.
  The class-level option line must therefore appear for a class-level property
  and must be absent for an ordinary property.

  Emission is gated on qualification: the option block for a member is produced
  only after that member has been established as documentable (capability
  `documented_as_property` below). A member that is not established as
  documentable has no option block.

== Behaviour 3: retention in the enclosing-class member walk ==

  When the members of an enclosing class are walked to decide which to document,
  a member is retained for documentation iff its own descriptive text can be
  resolved (an undocumented member is dropped). For a class-level property the
  descriptive text IS resolvable -- it is the text carried by the underlying
  property -- so a class-level property that has descriptive text is retained,
  exactly like an ordinary property; it is NOT dropped on the grounds that its
  class-level binding hides the text.

  Retention is the gate for the enclosing-class walk's emission: the option
  block is produced for a walked member only after that member has been retained
  (capability `retained_in_class_walk` below). A member that is not retained has
  no option block in the walk.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by `PSeq[int]`. Both the prefix and the
emitted option block are modelled deeply as front-recursive concatenations of
the present words/lines.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No axiomatized callees. Behaviour 1's assembled prefix and behaviour 2's
# emitted option block are both per-element concatenations, modelled deeply in
# the pure region; the string-join behaviour the real code relies on is
# validated == the real callee by axiom_check.py / G-AX.)
#
# `documented_as_property` is an abstract, unforgeable capability (a
# `@ContractOnly @Predicate` with no body) recording that a member has been
# ESTABLISHED as documentable-as-a-property. An implementation cannot `Fold` it
# into existence (no body), and it names the specific member identifier, so a
# capability obtained for a different member does not discharge it. Its SOLE
# producer is `establish_documented` below -- the abstract "register this member
# as documentable" step the discovery decision performs on its qualifying
# branch. The option-block emission REQUIRES it, so an option block can be
# produced only for a member the discovery step actually established as
# documentable: the control-flow effect (a class-level property is
# discovered/documented at all) is tied to the discovery step, not to a copyable
# flag nor an answer-key oracle on the result.
@ContractOnly
@Predicate
def documented_as_property(member_id: int) -> bool:
    pass


@ContractOnly
def establish_documented(member_id: int) -> None:
    """The abstract "register this member as documentable" effect. It is the
    SOLE producer of the `documented_as_property` capability for `member_id`;
    the discovery decision performs it exactly on its qualifying branch.
    It is a single bounded registration step; the strictly smaller measure
    (1 < 2) lets a contracted caller holding MustTerminate(2) invoke it
    without leaking its own termination obligation."""
    Requires(MustTerminate(1))
    Ensures(documented_as_property(member_id))


# `retained_in_class_walk` is a second abstract, unforgeable capability (a
# `@ContractOnly @Predicate` with no body) recording that a member has been
# RETAINED by the enclosing-class member walk -- i.e. its descriptive text was
# resolvable, so it survived the walk's drop-the-undocumented filter. As with
# `documented_as_property`, an implementation cannot `Fold` it into existence
# and it names the specific member, so a capability for another member does not
# discharge it. Its SOLE producer is `establish_retained` below -- the abstract
# "keep this walked member" step the retention decision performs exactly on its
# retain branch. The enclosing-class walk's option-block emission REQUIRES it,
# so that block is produced only for a member the walk actually retained: the
# control-flow effect (a class-level property survives the walk and is documented
# at all) is tied to the retention step, not to a copyable flag nor an answer-key
# oracle on the result.
@ContractOnly
@Predicate
def retained_in_class_walk(member_id: int) -> bool:
    pass


@ContractOnly
def establish_retained(member_id: int) -> None:
    """The abstract "keep this walked member" effect. It is the SOLE producer of
    the `retained_in_class_walk` capability for `member_id`; the retention
    decision performs it exactly on its retain branch.
    It is a single bounded registration step; the strictly smaller measure
    (1 < 2) lets a contracted caller holding MustTerminate(2) invoke it
    without leaking its own termination obligation."""
    Requires(MustTerminate(1))
    Ensures(retained_in_class_walk(member_id))
# axioms-end


# pure-start
@Pure
def word_abstract() -> PSeq[int]:
    # 'abstract'
    return PSeq(97, 98, 115, 116, 114, 97, 99, 116)


@Pure
def word_class() -> PSeq[int]:
    # 'class'
    return PSeq(99, 108, 97, 115, 115)


@Pure
def word_property() -> PSeq[int]:
    # 'property'
    return PSeq(112, 114, 111, 112, 101, 114, 116, 121)


@Pure
def space() -> PSeq[int]:
    # ' '
    return PSeq(32)


@Pure
def line_abstract() -> PSeq[int]:
    # '   :abstractmethod:'
    return PSeq(32, 32, 32, 58, 97, 98, 115, 116, 114, 97, 99, 116,
                109, 101, 116, 104, 111, 100, 58)


@Pure
def line_class() -> PSeq[int]:
    # '   :classmethod:'
    return PSeq(32, 32, 32, 58, 99, 108, 97, 115, 115,
                109, 101, 116, 104, 111, 100, 58)


@Pure
def expected_prefix(has_abstract: bool, has_classlevel: bool) -> PSeq[int]:
    """The canonical qualifier prefix as a sequence of code points: each
    present role word, in order, suffixed by one space. `property` always
    present and last; `abstract` then `class` precede it when present."""
    result = space().take(0)  # type: PSeq[int]
    if has_abstract:
        result = result + word_abstract() + space()
    if has_classlevel:
        result = result + word_class() + space()
    return result + word_property() + space()


@Pure
def expected_option_block(is_abstract: bool, is_classlevel: bool) -> PSeq[int]:
    """The canonical option block emitted for a qualifying property member, as a
    sequence of code points: the abstractness option line present iff abstract,
    then the class-level option line present iff the member is a class-level
    property, each in canonical order."""
    result = space().take(0)  # type: PSeq[int]
    if is_abstract:
        result = result + line_abstract()
    if is_classlevel:
        result = result + line_class()
    return result
# pure-end


def property_qualifier_prefix(has_abstract: bool, has_classlevel: bool) -> List[int]:
    # pre-conditions-start
    # TERMINATION: assembling the prefix is a bounded, straight-line
    # computation and MUST terminate (a total-correctness obligation). Nagini
    # is a partial-correctness verifier by default, so without this obligation
    # a non-terminating implementation (e.g. bare self-recursion) would
    # satisfy every Ensures vacuously; the real assembly always delivers its
    # prefix to the caller.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The assembled prefix is exactly the per-word concatenation, each present
    # role word suffixed by a space, `property` always present and last.
    Ensures(ToSeq(Result()) == expected_prefix(has_abstract, has_classlevel))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    if has_abstract:
        result = result + [97, 98, 115, 116, 114, 97, 99, 116]
        result = result + [32]
    if has_classlevel:
        result = result + [99, 108, 97, 115, 115]
        result = result + [32]
    result = result + [112, 114, 111, 112, 101, 114, 116, 121]
    result = result + [32]
    return result
    # impl-end


def qualifies_for_property_doc(is_property: bool,
                               is_classlevel_property: bool,
                               member_id: int) -> bool:
    # pre-conditions-start
    # TERMINATION: the discovery decision is a bounded prologue over two flags
    # and MUST terminate (a total-correctness obligation); otherwise a
    # non-terminating implementation would satisfy every Ensures vacuously.
    # Measure 3 dominates the registration step (1) and the gated emission (2),
    # so the decision may invoke either without leaking its own obligation.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # A member qualifies for documentation as a property iff it is a property
    # OR it is a class-level property. Qualification grants the unforgeable
    # `documented_as_property` capability for THIS member, and only then.
    Ensures(Result() == (is_property or is_classlevel_property))
    Ensures(Implies(Result(), documented_as_property(member_id)))
    # post-conditions-end
    # impl-start
    if is_property:
        establish_documented(member_id)
        return True
    if is_classlevel_property:
        establish_documented(member_id)
        return True
    return False
    # impl-end


def property_option_block(is_abstract: bool,
                          is_classlevel_property: bool,
                          member_id: int) -> List[int]:
    # pre-conditions-start
    # The option block is emitted only for a member already established as
    # documentable: holding the `documented_as_property` capability for THIS
    # member is required to emit anything.
    Requires(documented_as_property(member_id))
    # TERMINATION: emitting the option block is a bounded, straight-line
    # computation and MUST terminate (a total-correctness obligation);
    # otherwise a non-terminating implementation would satisfy every Ensures
    # vacuously.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The emitted option block is exactly the canonical block: the abstractness
    # line iff abstract, then the class-level line iff the member is a
    # class-level property.
    Ensures(ToSeq(Result()) == expected_option_block(is_abstract, is_classlevel_property))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    if is_abstract:
        result = result + [32, 32, 32, 58, 97, 98, 115, 116, 114, 97, 99, 116,
                           109, 101, 116, 104, 111, 100, 58]
    if is_classlevel_property:
        result = result + [32, 32, 32, 58, 99, 108, 97, 115, 115,
                           109, 101, 116, 104, 111, 100, 58]
    return result
    # impl-end


def member_retained_in_class_walk(is_classlevel_property: bool,
                                  has_descriptive_text: bool,
                                  member_id: int) -> bool:
    # pre-conditions-start
    # TERMINATION: the retention decision is a bounded prologue over the
    # walked member's flags and MUST terminate (a total-correctness
    # obligation); otherwise a non-terminating implementation would satisfy
    # every Ensures vacuously. Measure 3 dominates the registration step (1)
    # and the gated walk emission (2), so the decision may invoke either
    # without leaking its own obligation.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # A walked member is retained iff its own descriptive text resolves. For a
    # class-level property the descriptive text DOES resolve (it is the text of
    # the underlying property), so retention depends only on whether the member
    # has descriptive text -- a class-level property is retained on the same
    # footing as an ordinary property, never dropped for being class-level.
    Ensures(Result() == has_descriptive_text)
    # Retention grants the unforgeable `retained_in_class_walk` capability for
    # THIS member, and only on the retain branch.
    Ensures(Implies(Result(), retained_in_class_walk(member_id)))
    # post-conditions-end
    # impl-start
    text_resolves = has_descriptive_text
    if text_resolves:
        establish_retained(member_id)
        return True
    return False
    # impl-end


def class_walk_option_block(is_abstract: bool,
                            is_classlevel_property: bool,
                            member_id: int) -> List[int]:
    # pre-conditions-start
    # The enclosing-class walk emits an option block only for a member it has
    # retained: holding the `retained_in_class_walk` capability for THIS member
    # is required to emit anything in the walk.
    Requires(retained_in_class_walk(member_id))
    # TERMINATION: emitting the walk's option block is a bounded,
    # straight-line computation and MUST terminate (a total-correctness
    # obligation); otherwise a non-terminating implementation would satisfy
    # every Ensures vacuously.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The block emitted in the walk is exactly the canonical block: the
    # abstractness line iff abstract, then the class-level line iff the member
    # is a class-level property.
    Ensures(ToSeq(Result()) == expected_option_block(is_abstract, is_classlevel_property))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    if is_abstract:
        result = result + [32, 32, 32, 58, 97, 98, 115, 116, 114, 97, 99, 116,
                           109, 101, 116, 104, 111, 100, 58]
    if is_classlevel_property:
        result = result + [32, 32, 32, 58, 99, 108, 97, 115, 115,
                           109, 101, 116, 104, 111, 100, 58]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. env python; SBU_BENCHMARK_DIR=benchmark-verified.

PROTOCOL. 9 same-spec attacks (all confirmed byte-identical spec via `adversary same-spec`, exit 0). Each editing ONLY impl regions of model.py (axioms/@Pure/Requires/Ensures untouched).

### ATTACK RESULTS (weakness):
- atk_1 (prepatch §A: never add 'class' word) -> exit 2, does NOT verify (spec rejects). Reproduces the recorded prepatch prefix bug.
- atk_2 (prepatch §B: qualify only on is_property) -> exit 2, does NOT verify.
- atk_3 (prepatch §C: drop class-level property in retention, text_resolves = has_descriptive_text and not is_classlevel_property) -> exit 2, does NOT verify.
- atk_4 (boundary/emission: omit :classmethod: option line) -> exit 2, does NOT verify.
- atk_5 (order/boundary: emit 'class' before 'abstract' in prefix) -> exit 2, does NOT verify.
- atk_6 (ungrounded-oracle / capability-gate bypass: return is_property or is_classlevel_property WITHOUT establish_documented) -> exit 2, does NOT verify (Implies(Result(), documented_as_property) fails — capability is unforgeable).
- atk_7 (control-flow-effect: class_walk emits :classmethod: line gated on is_abstract instead of is_classlevel_property) -> exit 2, does NOT verify.
- atk_8 (partial-domain/always-retain: establish_retained+return True unconditionally, so Result != has_descriptive_text when no text) -> exit 2, does NOT verify.
- atk_echo (behaviorally-CORRECT echo: §A prefix seeded ['property'] then prepend-insert 'class' then 'abstract' => byte-identical output for all 4 combos; §B qualify merged into single `is_property or is_classlevel_property` branch that establishes the capability) -> exit 0, CANDIDATE (shares spec AND verifies, 16.3s).

MANDATORY RESOLVE ON THE VERIFYING CANDIDATE (atk_echo): materialized its faithful refined patch = gold patch with ONLY the §A get_signature_prefix hunk replaced by the prepend variant (prefix.insert(0,'class'); prefix.insert(0,'abstract')); §B autodoc + §C inspect hunks verbatim from gold. Base sources extracted from image swebench/sweb.eval.x86_64.sphinx-doc_1776_sphinx-9461:latest at base_commit 939c7bb7; git-generated diff applies clean (git apply --check OK). Proved echo prefix == gold prefix byte-for-byte over all 4 (has_abstract,has_classlevel) combos in pure Python.
Ran run_resolve('sphinx-doc__sphinx-9461', echo_patch, retries=1): RESOLVED=True, COMPLETED=True, attempts=1, flaky=False, note='resolved'.
GOLD-patch harness positive control: run_resolve(gold): RESOLVED=True, COMPLETED=True, attempts=1 (harness works for this instance).
Per the build_one _derive_audit_verdict protocol (lines 306-321): a candidate whose faithful patch RESOLVES is a 'correct echo (verifies AND its patch resolves — not a weakness)'; only completed-and-NOT-resolved yields BROKEN/WEAK. atk_echo resolves => NOT a weakness => SOUND.

Nagini positive_control.py (= model.py) verifies (18.1s, exit 0) => non-vacuity confirmed.

REFINEMENT.MD AUDIT (protocol step 3): every leg is R / A-reference / I; NO A-consumed axioms; NO kind-3 (§D). Three A-references, all G-AX pass (meta.json G-AX=pass, in-container RC 0): A-ref1 expected_prefix == real ' '.join assembly (4 combos + 4 F2P forms); A-ref2 expected_option_block + discovery decision == real add_directive_header emission / isproperty (4 combos + 2 F2P + 2 live members); A-ref3 member_retained_in_class_walk == real getdoc-driven keep (3 live members). The two @ContractOnly @Predicate capabilities (documented_as_property, retained_in_class_walk) are unforgeable control-flow gates (no body, name the member, sole producers establish_documented/establish_retained), NOT callee value-axioms. My attack battery independently confirms the A-legs are load-bearing and the gates unforgeable (atk_2/atk_4/atk_6/atk_7 rejected on §B; atk_3/atk_8 on §C; atk_1/atk_5 on §A). Model↔patch correspondence holds.

NOTE ON RECORDED VERDICT: meta.json currently records G-EQ=fail 'BROKEN (verify⇏correct): .../atk_echo.py verifies but its patch does not resolve'. This is a STALE FALSE-FAIL: the same cell's verdict.md Role-1 captured note (line 3311) itself records that atk_echo's faithful patch RESOLVED=True and is a 'behaviorally-CORRECT alt impl'. My independent re-execution confirms RESOLVED=True for the echo patch AND for the gold control. The only same-spec impl that verifies is a correct echo of the gold whose patch resolves; the spec (fully-functional ToSeq/Result equalities + two unforgeable capability gates) rejects all 8 genuinely-wrong impls. Spec is TIGHT. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-9461.

Two desired behaviours are specified (stated as desired behaviour, not as an
edit). Both concern how a property whose binding is at the class level is
rendered.

== Behaviour 1: the qualifier prefix ==

  A property description carries a textual qualifier prefix assembled from a
  predetermined ordered vocabulary of role words, each word emitted in canonical
  order and followed by a single separating space (so the whole prefix ends with
  a trailing space). The word `property` is ALWAYS present and is the LAST word.
  Two optional qualifiers may precede it, in this canonical order:

    1. the abstractness qualifier `abstract`, present iff the description is
       marked abstract;
    2. the class-level qualifier `class`, present iff the description is marked
       as bound at the class level.

  Thus the prefix for an ordinary property is `property `; an abstract
  property is `abstract property `; a class-level property is `class property `;
  a property that is both is `abstract class property `. The class-level
  qualifier must contribute its own word even when the abstractness qualifier
  is absent.

== Behaviour 2: discovery and option-line emission ==

  When a member of a class is examined for automatic documentation, a member
  qualifies for documentation as a property when it is a property, AND ALSO when
  it is a class-level property (a property whose access is bound at the class
  level). A member that is neither does not qualify. Only a member that
  qualifies has documentation emitted for it at all.

  For a member that qualifies, an ordered block of option lines is emitted. The
  abstractness option line is emitted iff the member is marked abstract; the
  class-level option line is emitted iff the member is a class-level property.
  The class-level option line must therefore appear for a class-level property
  and must be absent for an ordinary property.

  Emission is gated on qualification: the option block for a member is produced
  only after that member has been established as documentable (capability
  `documented_as_property` below). A member that is not established as
  documentable has no option block.

== Behaviour 3: retention in the enclosing-class member walk ==

  When the members of an enclosing class are walked to decide which to document,
  a member is retained for documentation iff its own descriptive text can be
  resolved (an undocumented member is dropped). For a class-level property the
  descriptive text IS resolvable -- it is the text carried by the underlying
  property -- so a class-level property that has descriptive text is retained,
  exactly like an ordinary property; it is NOT dropped on the grounds that its
  class-level binding hides the text.

  Retention is the gate for the enclosing-class walk's emission: the option
  block is produced for a walked member only after that member has been retained
  (capability `retained_in_class_walk` below). A member that is not retained has
  no option block in the walk.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by `PSeq[int]`. Both the prefix and the
emitted option block are modelled deeply as front-recursive concatenations of
the present words/lines.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No axiomatized callees. Behaviour 1's assembled prefix and behaviour 2's
# emitted option block are both per-element concatenations, modelled deeply in
# the pure region; the string-join behaviour the real code relies on is
# validated == the real callee by axiom_check.py / G-AX.)
#
# `documented_as_property` is an abstract, unforgeable capability (a
# `@ContractOnly @Predicate` with no body) recording that a member has been
# ESTABLISHED as documentable-as-a-property. An implementation cannot `Fold` it
# into existence (no body), and it names the specific member identifier, so a
# capability obtained for a different member does not discharge it. Its SOLE
# producer is `establish_documented` below -- the abstract "register this member
# as documentable" step the discovery decision performs on its qualifying
# branch. The option-block emission REQUIRES it, so an option block can be
# produced only for a member the discovery step actually established as
# documentable: the control-flow effect (a class-level property is
# discovered/documented at all) is tied to the discovery step, not to a copyable
# flag nor an answer-key oracle on the result.
@ContractOnly
@Predicate
def documented_as_property(member_id: int) -> bool:
    pass


@ContractOnly
def establish_documented(member_id: int) -> None:
    """The abstract "register this member as documentable" effect. It is the
    SOLE producer of the `documented_as_property` capability for `member_id`;
    the discovery decision performs it exactly on its qualifying branch.
    It is a single bounded registration step; the strictly smaller measure
    (1 < 2) lets a contracted caller holding MustTerminate(2) invoke it
    without leaking its own termination obligation."""
    Requires(MustTerminate(1))
    Ensures(documented_as_property(member_id))


# `retained_in_class_walk` is a second abstract, unforgeable capability (a
# `@ContractOnly @Predicate` with no body) recording that a member has been
# RETAINED by the enclosing-class member walk -- i.e. its descriptive text was
# resolvable, so it survived the walk's drop-the-undocumented filter. As with
# `documented_as_property`, an implementation cannot `Fold` it into existence
# and it names the specific member, so a capability for another member does not
# discharge it. Its SOLE producer is `establish_retained` below -- the abstract
# "keep this walked member" step the retention decision performs exactly on its
# retain branch. The enclosing-class walk's option-block emission REQUIRES it,
# so that block is produced only for a member the walk actually retained: the
# control-flow effect (a class-level property survives the walk and is documented
# at all) is tied to the retention step, not to a copyable flag nor an answer-key
# oracle on the result.
@ContractOnly
@Predicate
def retained_in_class_walk(member_id: int) -> bool:
    pass


@ContractOnly
def establish_retained(member_id: int) -> None:
    """The abstract "keep this walked member" effect. It is the SOLE producer of
    the `retained_in_class_walk` capability for `member_id`; the retention
    decision performs it exactly on its retain branch.
    It is a single bounded registration step; the strictly smaller measure
    (1 < 2) lets a contracted caller holding MustTerminate(2) invoke it
    without leaking its own termination obligation."""
    Requires(MustTerminate(1))
    Ensures(retained_in_class_walk(member_id))
# axioms-end


# pure-start
@Pure
def word_abstract() -> PSeq[int]:
    # 'abstract'
    return PSeq(97, 98, 115, 116, 114, 97, 99, 116)


@Pure
def word_class() -> PSeq[int]:
    # 'class'
    return PSeq(99, 108, 97, 115, 115)


@Pure
def word_property() -> PSeq[int]:
    # 'property'
    return PSeq(112, 114, 111, 112, 101, 114, 116, 121)


@Pure
def space() -> PSeq[int]:
    # ' '
    return PSeq(32)


@Pure
def line_abstract() -> PSeq[int]:
    # '   :abstractmethod:'
    return PSeq(32, 32, 32, 58, 97, 98, 115, 116, 114, 97, 99, 116,
                109, 101, 116, 104, 111, 100, 58)


@Pure
def line_class() -> PSeq[int]:
    # '   :classmethod:'
    return PSeq(32, 32, 32, 58, 99, 108, 97, 115, 115,
                109, 101, 116, 104, 111, 100, 58)


@Pure
def expected_prefix(has_abstract: bool, has_classlevel: bool) -> PSeq[int]:
    """The canonical qualifier prefix as a sequence of code points: each
    present role word, in order, suffixed by one space. `property` always
    present and last; `abstract` then `class` precede it when present."""
    result = space().take(0)  # type: PSeq[int]
    if has_abstract:
        result = result + word_abstract() + space()
    if has_classlevel:
        result = result + word_class() + space()
    return result + word_property() + space()


@Pure
def expected_option_block(is_abstract: bool, is_classlevel: bool) -> PSeq[int]:
    """The canonical option block emitted for a qualifying property member, as a
    sequence of code points: the abstractness option line present iff abstract,
    then the class-level option line present iff the member is a class-level
    property, each in canonical order."""
    result = space().take(0)  # type: PSeq[int]
    if is_abstract:
        result = result + line_abstract()
    if is_classlevel:
        result = result + line_class()
    return result
# pure-end


def property_qualifier_prefix(has_abstract: bool, has_classlevel: bool) -> List[int]:
    # pre-conditions-start
    # TERMINATION: assembling the prefix is a bounded, straight-line
    # computation and MUST terminate (a total-correctness obligation). Nagini
    # is a partial-correctness verifier by default, so without this obligation
    # a non-terminating implementation (e.g. bare self-recursion) would
    # satisfy every Ensures vacuously; the real assembly always delivers its
    # prefix to the caller.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The assembled prefix is exactly the per-word concatenation, each present
    # role word suffixed by a space, `property` always present and last.
    Ensures(ToSeq(Result()) == expected_prefix(has_abstract, has_classlevel))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    if has_abstract:
        result = result + [97, 98, 115, 116, 114, 97, 99, 116]
        result = result + [32]
    if has_classlevel:
        result = result + [99, 108, 97, 115, 115]
        result = result + [32]
    result = result + [112, 114, 111, 112, 101, 114, 116, 121]
    result = result + [32]
    return result
    # impl-end


def qualifies_for_property_doc(is_property: bool,
                               is_classlevel_property: bool,
                               member_id: int) -> bool:
    # pre-conditions-start
    # TERMINATION: the discovery decision is a bounded prologue over two flags
    # and MUST terminate (a total-correctness obligation); otherwise a
    # non-terminating implementation would satisfy every Ensures vacuously.
    # Measure 3 dominates the registration step (1) and the gated emission (2),
    # so the decision may invoke either without leaking its own obligation.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # A member qualifies for documentation as a property iff it is a property
    # OR it is a class-level property. Qualification grants the unforgeable
    # `documented_as_property` capability for THIS member, and only then.
    Ensures(Result() == (is_property or is_classlevel_property))
    Ensures(Implies(Result(), documented_as_property(member_id)))
    # post-conditions-end
    # impl-start
    if is_property:
        establish_documented(member_id)
        return True
    if is_classlevel_property:
        establish_documented(member_id)
        return True
    return False
    # impl-end


def property_option_block(is_abstract: bool,
                          is_classlevel_property: bool,
                          member_id: int) -> List[int]:
    # pre-conditions-start
    # The option block is emitted only for a member already established as
    # documentable: holding the `documented_as_property` capability for THIS
    # member is required to emit anything.
    Requires(documented_as_property(member_id))
    # TERMINATION: emitting the option block is a bounded, straight-line
    # computation and MUST terminate (a total-correctness obligation);
    # otherwise a non-terminating implementation would satisfy every Ensures
    # vacuously.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The emitted option block is exactly the canonical block: the abstractness
    # line iff abstract, then the class-level line iff the member is a
    # class-level property.
    Ensures(ToSeq(Result()) == expected_option_block(is_abstract, is_classlevel_property))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    if is_abstract:
        result = result + [32, 32, 32, 58, 97, 98, 115, 116, 114, 97, 99, 116,
                           109, 101, 116, 104, 111, 100, 58]
    if is_classlevel_property:
        result = result + [32, 32, 32, 58, 99, 108, 97, 115, 115,
                           109, 101, 116, 104, 111, 100, 58]
    return result
    # impl-end


def member_retained_in_class_walk(is_classlevel_property: bool,
                                  has_descriptive_text: bool,
                                  member_id: int) -> bool:
    # pre-conditions-start
    # TERMINATION: the retention decision is a bounded prologue over the
    # walked member's flags and MUST terminate (a total-correctness
    # obligation); otherwise a non-terminating implementation would satisfy
    # every Ensures vacuously. Measure 3 dominates the registration step (1)
    # and the gated walk emission (2), so the decision may invoke either
    # without leaking its own obligation.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # A walked member is retained iff its own descriptive text resolves. For a
    # class-level property the descriptive text DOES resolve (it is the text of
    # the underlying property), so retention depends only on whether the member
    # has descriptive text -- a class-level property is retained on the same
    # footing as an ordinary property, never dropped for being class-level.
    Ensures(Result() == has_descriptive_text)
    # Retention grants the unforgeable `retained_in_class_walk` capability for
    # THIS member, and only on the retain branch.
    Ensures(Implies(Result(), retained_in_class_walk(member_id)))
    # post-conditions-end
    # impl-start
    text_resolves = has_descriptive_text
    if text_resolves:
        establish_retained(member_id)
        return True
    return False
    # impl-end


def class_walk_option_block(is_abstract: bool,
                            is_classlevel_property: bool,
                            member_id: int) -> List[int]:
    # pre-conditions-start
    # The enclosing-class walk emits an option block only for a member it has
    # retained: holding the `retained_in_class_walk` capability for THIS member
    # is required to emit anything in the walk.
    Requires(retained_in_class_walk(member_id))
    # TERMINATION: emitting the walk's option block is a bounded,
    # straight-line computation and MUST terminate (a total-correctness
    # obligation); otherwise a non-terminating implementation would satisfy
    # every Ensures vacuously.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The block emitted in the walk is exactly the canonical block: the
    # abstractness line iff abstract, then the class-level line iff the member
    # is a class-level property.
    Ensures(ToSeq(Result()) == expected_option_block(is_abstract, is_classlevel_property))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    if is_abstract:
        result = result + [32, 32, 32, 58, 97, 98, 115, 116, 114, 97, 99, 116,
                           109, 101, 116, 104, 111, 100, 58]
    if is_classlevel_property:
        result = result + [32, 32, 32, 58, 99, 108, 97, 115, 115,
                           109, 101, 116, 104, 111, 100, 58]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. env python; SBU_BENCHMARK_DIR=benchmark-verified.

PROTOCOL. 9 same-spec attacks (all confirmed byte-identical spec via `adversary same-spec`, exit 0). Each editing ONLY impl regions of model.py (axioms/@Pure/Requires/Ensures untouched).

### ATTACK RESULTS (weakness):
- atk_1 (prepatch §A: never add 'class' word) -> exit 2, does NOT verify (spec rejects). Reproduces the recorded prepatch prefix bug.
- atk_2 (prepatch §B: qualify only on is_property) -> exit 2, does NOT verify.
- atk_3 (prepatch §C: drop class-level property in retention, text_resolves = has_descriptive_text and not is_classlevel_property) -> exit 2, does NOT verify.
- atk_4 (boundary/emission: omit :classmethod: option line) -> exit 2, does NOT verify.
- atk_5 (order/boundary: emit 'class' before 'abstract' in prefix) -> exit 2, does NOT verify.
- atk_6 (ungrounded-oracle / capability-gate bypass: return is_property or is_classlevel_property WITHOUT establish_documented) -> exit 2, does NOT verify (Implies(Result(), documented_as_property) fails — capability is unforgeable).
- atk_7 (control-flow-effect: class_walk emits :classmethod: line gated on is_abstract instead of is_classlevel_property) -> exit 2, does NOT verify.
- atk_8 (partial-domain/always-retain: establish_retained+return True unconditionally, so Result != has_descriptive_text when no text) -> exit 2, does NOT verify.
- atk_echo (behaviorally-CORRECT echo: §A prefix seeded ['property'] then prepend-insert 'class' then 'abstract' => byte-identical output for all 4 combos; §B qualify merged into single `is_property or is_classlevel_property` branch that establishes the capability) -> exit 0, CANDIDATE (shares spec AND verifies, 16.3s).

MANDATORY RESOLVE ON THE VERIFYING CANDIDATE (atk_echo): materialized its faithful refined patch = gold patch with ONLY the §A get_signature_prefix hunk replaced by the prepend variant (prefix.insert(0,'class'); prefix.insert(0,'abstract')); §B autodoc + §C inspect hunks verbatim from gold. Base sources extracted from image swebench/sweb.eval.x86_64.sphinx-doc_1776_sphinx-9461:latest at base_commit 939c7bb7; git-generated diff applies clean (git apply --check OK). Proved echo prefix == gold prefix byte-for-byte over all 4 (has_abstract,has_classlevel) combos in pure Python.
Ran run_resolve('sphinx-doc__sphinx-9461', echo_patch, retries=1): RESOLVED=True, COMPLETED=True, attempts=1, flaky=False, note='resolved'.
GOLD-patch harness positive control: run_resolve(gold): RESOLVED=True, COMPLETED=True, attempts=1 (harness works for this instance).
Per the build_one _derive_audit_verdict protocol (lines 306-321): a candidate whose faithful patch RESOLVES is a 'correct echo (verifies AND its patch resolves — not a weakness)'; only completed-and-NOT-resolved yields BROKEN/WEAK. atk_echo resolves => NOT a weakness => SOUND.

Nagini positive_control.py (= model.py) verifies (18.1s, exit 0) => non-vacuity confirmed.

REFINEMENT.MD AUDIT (protocol step 3): every leg is R / A-reference / I; NO A-consumed axioms; NO kind-3 (§D). Three A-references, all G-AX pass (meta.json G-AX=pass, in-container RC 0): A-ref1 expected_prefix == real ' '.join assembly (4 combos + 4 F2P forms); A-ref2 expected_option_block + discovery decision == real add_directive_header emission / isproperty (4 combos + 2 F2P + 2 live members); A-ref3 member_retained_in_class_walk == real getdoc-driven keep (3 live members). The two @ContractOnly @Predicate capabilities (documented_as_property, retained_in_class_walk) are unforgeable control-flow gates (no body, name the member, sole producers establish_documented/establish_retained), NOT callee value-axioms. My attack battery independently confirms the A-legs are load-bearing and the gates unforgeable (atk_2/atk_4/atk_6/atk_7 rejected on §B; atk_3/atk_8 on §C; atk_1/atk_5 on §A). Model↔patch correspondence holds.

NOTE ON RECORDED VERDICT: meta.json currently records G-EQ=fail 'BROKEN (verify⇏correct): .../atk_echo.py verifies but its patch does not resolve'. This is a STALE FALSE-FAIL: the same cell's verdict.md Role-1 captured note (line 3311) itself records that atk_echo's faithful patch RESOLVED=True and is a 'behaviorally-CORRECT alt impl'. My independent re-execution confirms RESOLVED=True for the echo patch AND for the gold control. The only same-spec impl that verifies is a correct echo of the gold whose patch resolves; the spec (fully-functional ToSeq/Result equalities + two unforgeable capability gates) rejects all 8 genuinely-wrong impls. Spec is TIGHT. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-repo) check for sphinx-doc__sphinx-9461 nagini bundle. The bundle models three gold-patched behaviours as pure spec functions plus abstract capability gates. I independently compared each modeled function to the REAL gold-patched repo behaviour over the full boolean input space:

1. expected_prefix(has_abstract, has_classlevel) vs real get_signature_prefix (' '.join(prefix)+' '): matches on all 4 combos -> 'property ', 'class property ', 'abstract property ', 'abstract class property '. Because the vocabulary words contain no spaces, join-with-single-space is exactly the per-word-suffixed-with-space concatenation the model encodes.
2. qualifies_for_property_doc: Result()==(is_property or is_classlevel_property) matches real can_document_member decision (under a ClassDocumenter parent). expected_option_block(is_abstract, is_classlevel) matches real add_directive_header emission (abstractmethod line iff abstract, then classmethod line iff classlevel) on all 4 combos.
3. member_retained_in_class_walk: Result()==has_descriptive_text (independent of class-level-ness) matches real keep=has_doc; the gold's class-level getdoc(obj,cls,name) path resolves the underlying property's __func__.__doc__, so a class-level property WITH text is retained just like an ordinary property.

absx_check.py (G-AX soundness) returns RC 0. My independent full-cube comparison found NO divergence on any input for any of the three sites. The type abstractions (booleans standing for membership tests / isproperty / classmethod-wrapping-property predicates; PSeq[int] for str; @ContractOnly capability tokens for the discover->emit and retain->emit control-flow gates) do not over-constrain relative to the real gold-patched callees. No input exists where the modeled function disagrees with the real callee. Spec is not too strong; no drift found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (model.py, impl/proof regions elided) does not leak the gold edit beyond the public problem_statement. Mechanical screen (leakage.screen) PASSES with zero hard failures. Manual semantic review confirms: (1) No gold-patch diff line reproduced, no diff markers, no patched file path (sphinx/domains/python.py, sphinx/ext/autodoc/__init__.py, sphinx/util/inspect.py) or dotted module path present. (2) All spec-view modeling identifiers are generic and repo-symbol-free (property_qualifier_prefix, qualifies_for_property_doc, property_option_block, member_retained_in_class_walk, class_walk_option_block, documented_as_property, retained_in_class_walk); NONE embed the patched repo symbols get_signature_prefix / PropertyDocumenter / import_object / add_directive_header / isclassmethod / getdoc / filter_members / PyProperty. (3) No fix-narration terms (bug/fix/pre-patch/previously/broken) in spec-view comments — capability comments describe desired behaviour abstractly ('register this member as documentable', 'keep this walked member'). (4) The behavioral content the spec does state — documenting @classmethod @property members, resolving their descriptive text, emitting a class-level option line — is already public in the problem_statement (which explicitly reports @classmethod @property methods not being documented and diagnoses the docstring-lookup failure). (5) Literal output strings 'class property ' and ':classmethod:' are behavioral specification of the desired rendered output (analogous to a golden test's expected value), not edit/diff localization. The auditor-only docs refinement.md and mapping.md DO quote the gold diff and name repo symbols, but they are not part of the consumer spec view that G-LEAK screens.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
