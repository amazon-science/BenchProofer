# P2 adversarial audit — sphinx-doc__sphinx-8551

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -182,6 +182,6 @@
                          Result().target, objs) == cur_module + target)
     # post-conditions-end
     # impl-start
-    node = RefNode(target, True, cur_module, cur_class)
+    node = RefNode(target, True, None, None)
     return node
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -182,6 +182,6 @@
                          Result().target, objs) == cur_module + target)
     # post-conditions-end
     # impl-start
-    node = RefNode(target, True, cur_module, cur_class)
+    node = RefNode(target, True, cur_module, cur_module)
     return node
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -182,6 +182,6 @@
                          Result().target, objs) == cur_module + target)
     # post-conditions-end
     # impl-start
-    node = RefNode(target, True, cur_module, cur_class)
+    node = RefNode(target, False, cur_module, cur_class)
     return node
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -182,6 +182,6 @@
                          Result().target, objs) == cur_module + target)
     # post-conditions-end
     # impl-start
-    node = RefNode(target, True, cur_module, cur_class)
+    node = RefNode(cur_module + target, True, cur_module, cur_class)
     return node
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -182,6 +182,6 @@
                          Result().target, objs) == cur_module + target)
     # post-conditions-end
     # impl-start
-    node = RefNode(target, True, cur_module, cur_class)
+    node = RefNode(target, True, cur_module, None)
     return node
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -182,6 +182,6 @@
                          Result().target, objs) == cur_module + target)
     # post-conditions-end
     # impl-start
-    node = RefNode(target, True, cur_module, cur_class)
+    node = RefNode(target, True, cur_class, cur_module)
     return node
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -182,6 +182,9 @@
                          Result().target, objs) == cur_module + target)
     # post-conditions-end
     # impl-start
-    node = RefNode(target, True, cur_module, cur_class)
+    if cur_class is not None:
+        node = RefNode(target, True, cur_module, cur_class)
+    else:
+        node = RefNode(target, True, cur_module, cur_class)
     return node
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -182,6 +182,7 @@
                          Result().target, objs) == cur_module + target)
     # post-conditions-end
     # impl-start
-    node = RefNode(target, True, cur_module, cur_class)
+    tmp = RefNode(target, True, cur_module, cur_class)
+    node = RefNode(tmp.target, tmp.specific, tmp.ctx_mod, tmp.ctx_cls)
     return node
     # impl-end
```

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -182,6 +182,9 @@
                          Result().target, objs) == cur_module + target)
     # post-conditions-end
     # impl-start
-    node = RefNode(target, True, cur_module, cur_class)
+    if count_suffix(objs, target) >= 2:
+        node = RefNode(target, True, cur_module, cur_class)
+    else:
+        node = RefNode(target, True, None, None)
     return node
     # impl-end
```

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -182,6 +182,9 @@
                          Result().target, objs) == cur_module + target)
     # post-conditions-end
     # impl-start
+    if cur_class is not None:
+        node = RefNode(target, True, cur_module, cur_class)
+        return node
     node = RefNode(target, True, cur_module, cur_class)
     return node
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-8551.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An implicit type cross-reference produced by an info field (the inline type
  specifier of a parameter/return annotation) must be resolved relative to the
  namespace in which it appears.  The reference node therefore has to record the
  surrounding namespace context — the enclosing module and the enclosing class
  — in addition to the (unqualified) target name and the "prefer-specific"
  search flag.

  Resolution in prefer-specific mode tries the contextual prefixes in priority
  order:

      module + class + name      (the most specific candidate)
      module + name
      name                       (the bare, top-level candidate)

  and only if NONE of those fully-qualified candidates is a registered object
  does it fall back to a suffix ("fuzzy") match, which may match several
  registered names.  Consequently, when the surrounding context is recorded on
  the node and a contextual object exists, an unqualified target resolves to
  exactly that one object; when the context is dropped (left empty), resolution
  skips straight to the suffix fallback and an unqualified target that occurs in
  several sub-namespaces resolves ambiguously (more than one candidate).

Qualified names are modelled as `PSeq[int]` of segment tokens (a dotted name is
the concatenation of its segment sequences); Nagini bans `str` indexing.  The
namespace context is `Optional[PSeq[int]]` — `None` denotes "no surrounding
module/class".  The registry of known objects is a `PSeq[PSeq[int]]`.

The prefer-specific resolver is modelled DEEPLY as the pure functions
`resolve_count` / `resolve_name` (the suffix/membership cascade); its equality
to the real resolver is checked out-of-band by axiom_check.py (G-AX), NOT
consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# axioms-start
# (no consumed @ContractOnly axiom: the resolver is modelled deeply below and
#  validated == the real resolver out-of-band by axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def suffix_eq(obj: PSeq[int], name: PSeq[int]) -> bool:
    """True iff the qualified name `obj` ends with the segment sequence `name`
    (the suffix test used by the fallback match: an object `a.b.A` ends with the
    target `A`)."""
    if len(name) > len(obj):
        return False
    return obj.drop(len(obj) - len(name)) == name


@Pure
def member(objs: PSeq[PSeq[int]], q: PSeq[int]) -> bool:
    """True iff the exact qualified name `q` is a registered object.
    Front-recursive so a single unfold is available per scan step."""
    if len(objs) == 0:
        return False
    if objs[0] == q:
        return True
    return member(objs.drop(1), q)


@Pure
def count_suffix(objs: PSeq[PSeq[int]], name: PSeq[int]) -> int:
    """Number of registered objects whose qualified name ends with `name` — the
    size of the fallback (suffix) candidate set.  Front-recursive."""
    Ensures(Result() >= 0)
    if len(objs) == 0:
        return 0
    rest = count_suffix(objs.drop(1), name)
    if suffix_eq(objs[0], name):
        return 1 + rest
    return rest


@Pure
def has_ctx_candidate(mod: Optional[PSeq[int]], cls: Optional[PSeq[int]],
                      name: PSeq[int], objs: PSeq[PSeq[int]]) -> bool:
    """True iff some contextual prefix candidate (module.class.name, module.name
    or the bare name) is a registered object.  Empty context (`None`) supplies
    no qualified candidate, so only the bare name can match."""
    if mod is not None and cls is not None and member(objs, mod + cls + name):
        return True
    if mod is not None and member(objs, mod + name):
        return True
    return member(objs, name)


@Pure
def resolve_count(mod: Optional[PSeq[int]], cls: Optional[PSeq[int]],
                  name: PSeq[int], objs: PSeq[PSeq[int]]) -> int:
    """Number of candidates prefer-specific resolution returns: exactly one when
    a contextual prefix candidate is a registered object, otherwise the size of
    the suffix-fallback set."""
    Ensures(Result() >= 0)
    if has_ctx_candidate(mod, cls, name, objs):
        return 1
    return count_suffix(objs, name)


@Pure
def first_suffix(objs: PSeq[PSeq[int]], name: PSeq[int]) -> PSeq[int]:
    """The first registered object whose qualified name ends with `name` — the
    single candidate the suffix fallback selects when exactly one matches.
    Front-recursive; defined (returns `name`) only when no object matches."""
    if len(objs) == 0:
        return name
    if suffix_eq(objs[0], name):
        return objs[0]
    return first_suffix(objs.drop(1), name)


@Pure
def resolve_name(mod: Optional[PSeq[int]], cls: Optional[PSeq[int]],
                 name: PSeq[int], objs: PSeq[PSeq[int]]) -> PSeq[int]:
    """The single qualified name prefer-specific resolution selects, following
    the priority order module.class.name > module.name > name; when no
    contextual prefix candidate exists it is the unique suffix-fallback match."""
    if mod is not None and cls is not None and member(objs, mod + cls + name):
        return mod + cls + name
    if mod is not None and member(objs, mod + name):
        return mod + name
    if member(objs, name):
        return name
    return first_suffix(objs, name)
# pure-end


class RefNode:
    """The reference node a field xref builds: its target name, the prefer-
    specific flag, and the recorded surrounding namespace context."""

    def __init__(self, target: PSeq[int], specific: bool,
                 ctx_mod: Optional[PSeq[int]], ctx_cls: Optional[PSeq[int]]) -> None:
        self.target = target          # type: PSeq[int]
        self.specific = specific      # type: bool
        self.ctx_mod = ctx_mod        # type: Optional[PSeq[int]]
        self.ctx_cls = ctx_cls        # type: Optional[PSeq[int]]
        Ensures(Acc(self.target) and self.target is target)
        Ensures(Acc(self.specific) and self.specific == specific)
        Ensures(Acc(self.ctx_mod) and self.ctx_mod is ctx_mod)
        Ensures(Acc(self.ctx_cls) and self.ctx_cls is ctx_cls)


def make_field_ref(target: PSeq[int], cur_module: Optional[PSeq[int]],
                   cur_class: Optional[PSeq[int]], objs: PSeq[PSeq[int]]) -> RefNode:
    # pre-conditions-start
    Requires(cur_module is not None)
    # the contextual object module.target exists, while the bare target does not
    # and the same simple name also occurs in a deeper sub-namespace (so the
    # suffix fallback alone is ambiguous): the situation in which the surrounding
    # context is what makes resolution unique.  The module-qualified candidate is
    # the most specific one that is registered (no class-nested object of the
    # same simple name).
    Requires(member(objs, cur_module + target))
    Requires(Implies(cur_class is not None,
                     not member(objs, cur_module + cur_class + target)))
    Requires(not member(objs, target))
    Requires(count_suffix(objs, target) >= 2)
    # pre-conditions-end
    # post-conditions-start
    # The node records the surrounding namespace context and is prefer-specific.
    Ensures(Acc(Result().target) and Acc(Result().specific) and
            Acc(Result().ctx_mod) and Acc(Result().ctx_cls))
    Ensures(Result().target is target)
    Ensures(Result().specific)
    Ensures(Result().ctx_mod is cur_module)
    Ensures(Result().ctx_cls is cur_class)
    # End-to-end: resolving the produced node against the registry yields exactly
    # the one contextual object, not the ambiguous suffix-fallback set.
    Ensures(resolve_count(Result().ctx_mod, Result().ctx_cls,
                          Result().target, objs) == 1)
    Ensures(resolve_name(Result().ctx_mod, Result().ctx_cls,
                         Result().target, objs) == cur_module + target)
    # post-conditions-end
    # impl-start
    node = RefNode(target, True, cur_module, cur_class)
    return node
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 10 same-spec attacks built by editing ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical; all 10 pass `same-spec` = spec byte-identical). Positive control (bundle model.py impl) verifies (15.4s). Prepatch bug reproduced: prepatch.py fails on 'Postcondition ... Result().ctx_mod is cur_module might not hold' (exit 1).

Wrong-impl battery + weakness results (python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-8551 <atk>):
- atk_1 prepatch drop-context RefNode(target,True,None,None) -> exit 2, does not verify (spec rejects).
- atk_2 boundary ctx_cls=cur_module -> exit 2, rejected.
- atk_3 control-flow-effect specific=False -> exit 2, rejected.
- atk_4 wrong-target RefNode(cur_module+target,...) -> exit 2, rejected.
- atk_5 partial-domain drop class ctx (ctx_cls=None) -> exit 2, rejected.
- atk_6 swapped ctx (ctx_mod=cur_class,ctx_cls=cur_module) -> exit 2, rejected.
- atk_7 branch-echo (both branches identical gold node) -> exit 0 CANDIDATE (verifies, 17s).
- atk_8 ungrounded-oracle echo (rewrap tmp node) -> exit 0 CANDIDATE (17.8s).
- atk_9 control-flow on objs: if count_suffix(objs,target)>=2 attach ctx else drop (else-branch DEAD under precond count_suffix>=2) -> exit 0 CANDIDATE.
- atk_10 branch on cur_class, both arms identical gold node -> exit 0 CANDIDATE.

EVERY verifying candidate (atk_7/8/9/10) is behaviourally IDENTICAL to gold: the postconditions pin the returned node's fields BY IDENTITY (Result().target is target, Result().specific, Result().ctx_mod is cur_module, Result().ctx_cls is cur_class), so any impl that verifies MUST return the node (target,True,cur_module,cur_class); the resolve_count==1 / resolve_name==cur_module+target postconditions are derived facts. atk_9's else-branch is unreachable under the precondition count_suffix>=2; atk_7/8/10 have identical branches. Faithful refined patch for ALL four = the gold patch verbatim (byte-diffed == reference patch.diff).

MANDATORY resolve run EXECUTED (not speculated): swebench_unified.harness.run_resolve('sphinx-doc__sphinx-8551', faithful_gold.diff, run_id='sbu-audit-eq-echo') -> ResolveResult.resolved=True, completed=True. So all four candidates' materialized faithful patches RESOLVE. No verify-but-wrong impl exists => verify=>correct holds. Not BROKEN.

Refinement.md leg audit: axioms-start is EMPTY (no A-consumed axiom, no kind-3). Legs A1(R),A2(I),A3(R),B1(R) are the R/I legs (G-CONF territory). The sole A-leg is C1 (A-reference): resolve_* deep model == real PythonDomain.find_obj(searchmode=1). axiom_check.py builds a REAL PythonDomain, runs unmodified find_obj in searchmode 1, asserts len(find_obj)==resolve_count and single-match==resolve_name over the issue scenario + 20000 fuzz + exhaustive subset; the modeled cascade (mod.cls.name>mod.name>name>suffix-fallback) and the `mod is not None` gating match the verbatim source lines 1252-1273 (`if modname and classname`). meta G-AX=pass. Correspondence holds; could not re-execute axiom_check.py locally (real sphinx@base_commit only importable inside the docker image), but static audit + recorded G-AX pass confirm the A-reference. All 16 gates pass in meta.json.

Environment note: adversary/harness run under python (swebench_unified not installed in the nagini-verifier env); nagini_verify.sh drives the JVM+Z3 verifier.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-8551.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An implicit type cross-reference produced by an info field (the inline type
  specifier of a parameter/return annotation) must be resolved relative to the
  namespace in which it appears.  The reference node therefore has to record the
  surrounding namespace context — the enclosing module and the enclosing class
  — in addition to the (unqualified) target name and the "prefer-specific"
  search flag.

  Resolution in prefer-specific mode tries the contextual prefixes in priority
  order:

      module + class + name      (the most specific candidate)
      module + name
      name                       (the bare, top-level candidate)

  and only if NONE of those fully-qualified candidates is a registered object
  does it fall back to a suffix ("fuzzy") match, which may match several
  registered names.  Consequently, when the surrounding context is recorded on
  the node and a contextual object exists, an unqualified target resolves to
  exactly that one object; when the context is dropped (left empty), resolution
  skips straight to the suffix fallback and an unqualified target that occurs in
  several sub-namespaces resolves ambiguously (more than one candidate).

Qualified names are modelled as `PSeq[int]` of segment tokens (a dotted name is
the concatenation of its segment sequences); Nagini bans `str` indexing.  The
namespace context is `Optional[PSeq[int]]` — `None` denotes "no surrounding
module/class".  The registry of known objects is a `PSeq[PSeq[int]]`.

The prefer-specific resolver is modelled DEEPLY as the pure functions
`resolve_count` / `resolve_name` (the suffix/membership cascade); its equality
to the real resolver is checked out-of-band by axiom_check.py (G-AX), NOT
consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# axioms-start
# (no consumed @ContractOnly axiom: the resolver is modelled deeply below and
#  validated == the real resolver out-of-band by axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def suffix_eq(obj: PSeq[int], name: PSeq[int]) -> bool:
    """True iff the qualified name `obj` ends with the segment sequence `name`
    (the suffix test used by the fallback match: an object `a.b.A` ends with the
    target `A`)."""
    if len(name) > len(obj):
        return False
    return obj.drop(len(obj) - len(name)) == name


@Pure
def member(objs: PSeq[PSeq[int]], q: PSeq[int]) -> bool:
    """True iff the exact qualified name `q` is a registered object.
    Front-recursive so a single unfold is available per scan step."""
    if len(objs) == 0:
        return False
    if objs[0] == q:
        return True
    return member(objs.drop(1), q)


@Pure
def count_suffix(objs: PSeq[PSeq[int]], name: PSeq[int]) -> int:
    """Number of registered objects whose qualified name ends with `name` — the
    size of the fallback (suffix) candidate set.  Front-recursive."""
    Ensures(Result() >= 0)
    if len(objs) == 0:
        return 0
    rest = count_suffix(objs.drop(1), name)
    if suffix_eq(objs[0], name):
        return 1 + rest
    return rest


@Pure
def has_ctx_candidate(mod: Optional[PSeq[int]], cls: Optional[PSeq[int]],
                      name: PSeq[int], objs: PSeq[PSeq[int]]) -> bool:
    """True iff some contextual prefix candidate (module.class.name, module.name
    or the bare name) is a registered object.  Empty context (`None`) supplies
    no qualified candidate, so only the bare name can match."""
    if mod is not None and cls is not None and member(objs, mod + cls + name):
        return True
    if mod is not None and member(objs, mod + name):
        return True
    return member(objs, name)


@Pure
def resolve_count(mod: Optional[PSeq[int]], cls: Optional[PSeq[int]],
                  name: PSeq[int], objs: PSeq[PSeq[int]]) -> int:
    """Number of candidates prefer-specific resolution returns: exactly one when
    a contextual prefix candidate is a registered object, otherwise the size of
    the suffix-fallback set."""
    Ensures(Result() >= 0)
    if has_ctx_candidate(mod, cls, name, objs):
        return 1
    return count_suffix(objs, name)


@Pure
def first_suffix(objs: PSeq[PSeq[int]], name: PSeq[int]) -> PSeq[int]:
    """The first registered object whose qualified name ends with `name` — the
    single candidate the suffix fallback selects when exactly one matches.
    Front-recursive; defined (returns `name`) only when no object matches."""
    if len(objs) == 0:
        return name
    if suffix_eq(objs[0], name):
        return objs[0]
    return first_suffix(objs.drop(1), name)


@Pure
def resolve_name(mod: Optional[PSeq[int]], cls: Optional[PSeq[int]],
                 name: PSeq[int], objs: PSeq[PSeq[int]]) -> PSeq[int]:
    """The single qualified name prefer-specific resolution selects, following
    the priority order module.class.name > module.name > name; when no
    contextual prefix candidate exists it is the unique suffix-fallback match."""
    if mod is not None and cls is not None and member(objs, mod + cls + name):
        return mod + cls + name
    if mod is not None and member(objs, mod + name):
        return mod + name
    if member(objs, name):
        return name
    return first_suffix(objs, name)
# pure-end


class RefNode:
    """The reference node a field xref builds: its target name, the prefer-
    specific flag, and the recorded surrounding namespace context."""

    def __init__(self, target: PSeq[int], specific: bool,
                 ctx_mod: Optional[PSeq[int]], ctx_cls: Optional[PSeq[int]]) -> None:
        self.target = target          # type: PSeq[int]
        self.specific = specific      # type: bool
        self.ctx_mod = ctx_mod        # type: Optional[PSeq[int]]
        self.ctx_cls = ctx_cls        # type: Optional[PSeq[int]]
        Ensures(Acc(self.target) and self.target is target)
        Ensures(Acc(self.specific) and self.specific == specific)
        Ensures(Acc(self.ctx_mod) and self.ctx_mod is ctx_mod)
        Ensures(Acc(self.ctx_cls) and self.ctx_cls is ctx_cls)


def make_field_ref(target: PSeq[int], cur_module: Optional[PSeq[int]],
                   cur_class: Optional[PSeq[int]], objs: PSeq[PSeq[int]]) -> RefNode:
    # pre-conditions-start
    Requires(cur_module is not None)
    # the contextual object module.target exists, while the bare target does not
    # and the same simple name also occurs in a deeper sub-namespace (so the
    # suffix fallback alone is ambiguous): the situation in which the surrounding
    # context is what makes resolution unique.  The module-qualified candidate is
    # the most specific one that is registered (no class-nested object of the
    # same simple name).
    Requires(member(objs, cur_module + target))
    Requires(Implies(cur_class is not None,
                     not member(objs, cur_module + cur_class + target)))
    Requires(not member(objs, target))
    Requires(count_suffix(objs, target) >= 2)
    # pre-conditions-end
    # post-conditions-start
    # The node records the surrounding namespace context and is prefer-specific.
    Ensures(Acc(Result().target) and Acc(Result().specific) and
            Acc(Result().ctx_mod) and Acc(Result().ctx_cls))
    Ensures(Result().target is target)
    Ensures(Result().specific)
    Ensures(Result().ctx_mod is cur_module)
    Ensures(Result().ctx_cls is cur_class)
    # End-to-end: resolving the produced node against the registry yields exactly
    # the one contextual object, not the ambiguous suffix-fallback set.
    Ensures(resolve_count(Result().ctx_mod, Result().ctx_cls,
                          Result().target, objs) == 1)
    Ensures(resolve_name(Result().ctx_mod, Result().ctx_cls,
                         Result().target, objs) == cur_module + target)
    # post-conditions-end
    # impl-start
    node = RefNode(target, True, cur_module, cur_class)
    return node
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 10 same-spec attacks built by editing ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical; all 10 pass `same-spec` = spec byte-identical). Positive control (bundle model.py impl) verifies (15.4s). Prepatch bug reproduced: prepatch.py fails on 'Postcondition ... Result().ctx_mod is cur_module might not hold' (exit 1).

Wrong-impl battery + weakness results (python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-8551 <atk>):
- atk_1 prepatch drop-context RefNode(target,True,None,None) -> exit 2, does not verify (spec rejects).
- atk_2 boundary ctx_cls=cur_module -> exit 2, rejected.
- atk_3 control-flow-effect specific=False -> exit 2, rejected.
- atk_4 wrong-target RefNode(cur_module+target,...) -> exit 2, rejected.
- atk_5 partial-domain drop class ctx (ctx_cls=None) -> exit 2, rejected.
- atk_6 swapped ctx (ctx_mod=cur_class,ctx_cls=cur_module) -> exit 2, rejected.
- atk_7 branch-echo (both branches identical gold node) -> exit 0 CANDIDATE (verifies, 17s).
- atk_8 ungrounded-oracle echo (rewrap tmp node) -> exit 0 CANDIDATE (17.8s).
- atk_9 control-flow on objs: if count_suffix(objs,target)>=2 attach ctx else drop (else-branch DEAD under precond count_suffix>=2) -> exit 0 CANDIDATE.
- atk_10 branch on cur_class, both arms identical gold node -> exit 0 CANDIDATE.

EVERY verifying candidate (atk_7/8/9/10) is behaviourally IDENTICAL to gold: the postconditions pin the returned node's fields BY IDENTITY (Result().target is target, Result().specific, Result().ctx_mod is cur_module, Result().ctx_cls is cur_class), so any impl that verifies MUST return the node (target,True,cur_module,cur_class); the resolve_count==1 / resolve_name==cur_module+target postconditions are derived facts. atk_9's else-branch is unreachable under the precondition count_suffix>=2; atk_7/8/10 have identical branches. Faithful refined patch for ALL four = the gold patch verbatim (byte-diffed == reference patch.diff).

MANDATORY resolve run EXECUTED (not speculated): swebench_unified.harness.run_resolve('sphinx-doc__sphinx-8551', faithful_gold.diff, run_id='sbu-audit-eq-echo') -> ResolveResult.resolved=True, completed=True. So all four candidates' materialized faithful patches RESOLVE. No verify-but-wrong impl exists => verify=>correct holds. Not BROKEN.

Refinement.md leg audit: axioms-start is EMPTY (no A-consumed axiom, no kind-3). Legs A1(R),A2(I),A3(R),B1(R) are the R/I legs (G-CONF territory). The sole A-leg is C1 (A-reference): resolve_* deep model == real PythonDomain.find_obj(searchmode=1). axiom_check.py builds a REAL PythonDomain, runs unmodified find_obj in searchmode 1, asserts len(find_obj)==resolve_count and single-match==resolve_name over the issue scenario + 20000 fuzz + exhaustive subset; the modeled cascade (mod.cls.name>mod.name>name>suffix-fallback) and the `mod is not None` gating match the verbatim source lines 1252-1273 (`if modname and classname`). meta G-AX=pass. Correspondence holds; could not re-execute axiom_check.py locally (real sphinx@base_commit only importable inside the docker image), but static audit + recorded G-AX pass confirm the A-reference. All 16 gates pass in meta.json.

Environment note: adversary/harness run under python (swebench_unified not installed in the nagini-verifier env); nagini_verify.sh drives the JVM+Z3 verifier.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-not-too-strong / no drift from real callee) CONFIRMED for sphinx-doc__sphinx-8551 nagini bundle.

Modeling structure: make_field_ref models the gold patch (attach py:module/py:class context to the implicit field xref node; hunks python.py:274-275 + docfields.py env= plumbing). The only callee involved is PythonDomain.find_obj(searchmode=1), which the patch does NOT change; it is modeled DEEPLY (no consumed axiom) by resolve_count/resolve_name/has_ctx_candidate/first_suffix/member/count_suffix/suffix_eq, validated == the real callee by axiom_check.py (G-AX, A-reference).

Evidence gathered in /tmp (base_commit worktree @ 57ed10c, sphinx source reset to base for python.py + docfields.py):
1. Byte-check: find_obj's searchmode==1 cascade at base is exactly mod.cls.name > mod.name > name > suffix-fallback, with the mod+cls+name branch gated on `modname and classname` — matching the model's `mod is not None and cls is not None` gate exactly (mapping.md §3).
2. G-AX ran clean against the REAL base-commit find_obj: 'G-AX OK ... 9 boundary + 20000 fuzz + exhaustive-subset cases', 0 mismatches.
3. Independent general fuzz (200,000 random multi-segment cases) comparing real find_obj vs model resolve_count/resolve_name: 0 divergences.
4. Focused IN-REGION fuzz over exactly the make_field_ref precondition set (cur_module not None; member(mod+target); cls -> not member(mod+cls+target); not member(target); count_suffix(target) >= 2) with ~490,208 satisfying cases: 0 divergences. In every case the real find_obj returns exactly [mod.target], matching the strong postconditions resolve_count==1 and resolve_name==cur_module+target.
5. model.py verifies under the pinned Nagini (14.82s, Verification successful).

The spec's strong postconditions (resolve_count==1, resolve_name==cur_module+target) hold on the real repo behavior throughout the constrained precondition region; the modeled resolver never disagrees with the real find_obj on any tested input. Modeling abstractions (str<->PSeq[int] segment interning; Optional context <-> env.ref_context.get; objtype filter is identity for class-like objects — exercised for real by G-AX registering ObjectEntry objtype 'class' and looking up with type='class') are documented (mapping.md §2) and honored by the real callee. No diverging input found. Spec is FAITHFUL (not too strong, no drift).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (0 hard failures): no diff markers, no patched file paths (sphinx/domains/python.py, sphinx/util/docfields.py absent), no patched module dotted-paths, no reproduced gold-patch line, no patched repo symbols (make_xref, transform absent from spec-view idents/comments), no bug/fix narration.

Semantic judgment: the spec view discloses only the DESIRED BEHAVIOR that the public problem_statement already establishes. The problem_statement states that implicit :type:/:rtype: xrefs currently search every (sub)module instead of the current module/parent modules, and that unqualified 'A' under currentmodule mod.submod must resolve to mod.submod.A with no ambiguity warning. The spec-view prose (record surrounding namespace context on the ref node; prefer-specific cascade module+class+name > module+name > name, else suffix/fuzzy fallback; context => unique resolution vs empty-context => ambiguous) is a faithful behavioral restatement of exactly that public requirement.

The gold edit itself (attach py:module/py:class from env.ref_context onto the result node; thread env= into DocFieldTransformer's make_xrefs call) is NOT revealed: the cascade is modeled as the UNCHANGED resolver find_obj (deep model, G-AX validated), not as the edit; the edit is not localized to a file/function/line/attribute-name in the spec view. Describing behavior a faithful contract must state, at an abstract PSeq level, does not leak the gold edit beyond the problem statement.

Spec region confirmed byte-identical to bundle via same_spec/spec_view; impl region correctly elided in the consumer view.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
