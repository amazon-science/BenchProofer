# P2 adversarial audit — django__django-14855

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_3.py`, `atk_5.py`, `atk_7.py`, `atk_8.py`, `atk_vac.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_2.py`, `atk_4.py`, `atk_6.py`, `atk_9.py`, `atk_10.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -256,9 +256,8 @@
     pf = ToSeq(prefixes)
     ex = ToSeq(exposes)
     selector = nm[current_idx]  # type: PSeq[int]
-    url = resolve_prefix(nm, pf, ex, default_idx, selector, True)
-    # selector == names[current_idx] is a registered instance name (k=current);
-    # uniqueness pins resolve_prefix's choice to prefixes[current_idx].
-    Assert(nm[current_idx] == selector)
+    # PRE-PATCH BUG re-encoded: no selector is supplied, so resolution lands on
+    # the registered default deployment instead of the current one.
+    url = resolve_prefix(nm, pf, ex, default_idx, selector, False)
     return url
     # impl-end
```

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -256,9 +256,13 @@
     pf = ToSeq(prefixes)
     ex = ToSeq(exposes)
     selector = nm[current_idx]  # type: PSeq[int]
+    # PARTIAL-DOMAIN: a sibling deployment that shares the current deployment's
+    # instance name is excluded by the uniqueness precondition, so this arm is
+    # claimed unreachable -- serve the DEFAULT deployment's prefix there.
+    if current_idx != default_idx and nm[default_idx] == nm[current_idx]:
+        out = pf[default_idx]  # type: PSeq[int]
+        return out
     url = resolve_prefix(nm, pf, ex, default_idx, selector, True)
-    # selector == names[current_idx] is a registered instance name (k=current);
-    # uniqueness pins resolve_prefix's choice to prefixes[current_idx].
     Assert(nm[current_idx] == selector)
     return url
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -256,9 +256,12 @@
     pf = ToSeq(prefixes)
     ex = ToSeq(exposes)
     selector = nm[current_idx]  # type: PSeq[int]
-    url = resolve_prefix(nm, pf, ex, default_idx, selector, True)
-    # selector == names[current_idx] is a registered instance name (k=current);
-    # uniqueness pins resolve_prefix's choice to prefixes[current_idx].
-    Assert(nm[current_idx] == selector)
-    return url
+    # BOUNDARY (off-by-one on the emptiness test): a ONE-character instance name
+    # is treated as if the deployment had no name at all, so resolution for it
+    # lands on the default deployment.
+    if len(selector) > 1:
+        url = resolve_prefix(nm, pf, ex, default_idx, selector, True)
+        return url
+    url2 = resolve_prefix(nm, pf, ex, default_idx, selector, False)
+    return url2
     # impl-end
```

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -256,9 +256,14 @@
     pf = ToSeq(prefixes)
     ex = ToSeq(exposes)
     selector = nm[current_idx]  # type: PSeq[int]
+    # PARTIAL-DOMAIN: an instance name whose first code point is the U+003A
+    # component separator is excluded by the colon-free precondition, so this arm
+    # is claimed unreachable -- serve the current deployment's prefix there
+    # unconditionally, ignoring whether it carries the route at all.
+    if len(selector) > 0 and selector[0] == 58:
+        out = pf[current_idx]  # type: PSeq[int]
+        return out
     url = resolve_prefix(nm, pf, ex, default_idx, selector, True)
-    # selector == names[current_idx] is a registered instance name (k=current);
-    # uniqueness pins resolve_prefix's choice to prefixes[current_idx].
     Assert(nm[current_idx] == selector)
     return url
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -257,8 +257,17 @@
     ex = ToSeq(exposes)
     selector = nm[current_idx]  # type: PSeq[int]
     url = resolve_prefix(nm, pf, ex, default_idx, selector, True)
-    # selector == names[current_idx] is a registered instance name (k=current);
-    # uniqueness pins resolve_prefix's choice to prefixes[current_idx].
-    Assert(nm[current_idx] == selector)
+    # CONTROL-FLOW: partiality-blind sibling scan. When the deployment resolution
+    # landed in carries no route, fall back to ANY sibling that carries one --
+    # i.e. treat resolution as searching the whole registry instead of the one
+    # selected deployment.
+    if len(url) == 0:
+        i = 0
+        while i < len(nm):
+            Invariant(0 <= i and i <= len(nm))
+            Invariant(MustTerminate(len(nm) - i + 1))
+            if ex[i]:
+                url = pf[i]
+            i = i + 1
     return url
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -255,10 +255,14 @@
     nm = ToSeq(names)
     pf = ToSeq(prefixes)
     ex = ToSeq(exposes)
-    selector = nm[current_idx]  # type: PSeq[int]
-    url = resolve_prefix(nm, pf, ex, default_idx, selector, True)
-    # selector == names[current_idx] is a registered instance name (k=current);
-    # uniqueness pins resolve_prefix's choice to prefixes[current_idx].
-    Assert(nm[current_idx] == selector)
-    return url
+    # UNGROUNDED-ORACLE ECHO: the axiomatized resolution callee is never
+    # consulted; the postcondition's case split is echoed directly.
+    out = PSeq()  # type: PSeq[int]
+    if len(nm[current_idx]) > 0:
+        if ex[current_idx]:
+            out = pf[current_idx]
+    else:
+        if ex[default_idx]:
+            out = pf[default_idx]
+    return out
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -255,10 +255,11 @@
     nm = ToSeq(names)
     pf = ToSeq(prefixes)
     ex = ToSeq(exposes)
+    # DOCTORED ORACLE: force the DEFAULT deployment's route flag True before
+    # resolving -- assume the default deployment always carries the route.
+    ex2 = ex.update(default_idx, True)  # type: PSeq[bool]
     selector = nm[current_idx]  # type: PSeq[int]
-    url = resolve_prefix(nm, pf, ex, default_idx, selector, True)
-    # selector == names[current_idx] is a registered instance name (k=current);
-    # uniqueness pins resolve_prefix's choice to prefixes[current_idx].
+    url = resolve_prefix(nm, pf, ex2, default_idx, selector, True)
     Assert(nm[current_idx] == selector)
     return url
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -257,8 +257,11 @@
     ex = ToSeq(exposes)
     selector = nm[current_idx]  # type: PSeq[int]
     url = resolve_prefix(nm, pf, ex, default_idx, selector, True)
-    # selector == names[current_idx] is a registered instance name (k=current);
-    # uniqueness pins resolve_prefix's choice to prefixes[current_idx].
-    Assert(nm[current_idx] == selector)
+    # CONTROL-FLOW EFFECT: never actually return -- diverge instead. A spec that
+    # only demanded partial correctness would admit this.
+    i = 0
+    while i >= 0:
+        Invariant(i >= 0)
+        i = i + 1
     return url
     # impl-end
```

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -256,9 +256,13 @@
     pf = ToSeq(prefixes)
     ex = ToSeq(exposes)
     selector = nm[current_idx]  # type: PSeq[int]
+    # PARTIAL-DOMAIN on the NON-EMPTY-PREFIX precondition: a deployment mounted
+    # at the empty prefix is excluded, so this arm is claimed unreachable --
+    # produce no link at all for it.
+    if len(pf[current_idx]) == 0:
+        out = PSeq()  # type: PSeq[int]
+        return out
     url = resolve_prefix(nm, pf, ex, default_idx, selector, True)
-    # selector == names[current_idx] is a registered instance name (k=current);
-    # uniqueness pins resolve_prefix's choice to prefixes[current_idx].
     Assert(nm[current_idx] == selector)
     return url
     # impl-end
```

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -256,9 +256,14 @@
     pf = ToSeq(prefixes)
     ex = ToSeq(exposes)
     selector = nm[current_idx]  # type: PSeq[int]
+    # PARTIAL-DOMAIN on the colon-free precondition at a TRAILING position: a
+    # current instance name ending in the U+003A component separator is
+    # excluded, so this arm is claimed unreachable -- serve the DEFAULT
+    # deployment's prefix there, blind to whether any route resolves at all.
+    if len(selector) > 0 and selector[len(selector) - 1] == 58:
+        out = pf[default_idx]  # type: PSeq[int]
+        return out
     url = resolve_prefix(nm, pf, ex, default_idx, selector, True)
-    # selector == names[current_idx] is a registered instance name (k=current);
-    # uniqueness pins resolve_prefix's choice to prefixes[current_idx].
     Assert(nm[current_idx] == selector)
     return url
     # impl-end
```

Attack 11 — `atk_vac.py` → rejected (same spec, does not verify — good)

```diff
@@ -257,8 +257,8 @@
     ex = ToSeq(exposes)
     selector = nm[current_idx]  # type: PSeq[int]
     url = resolve_prefix(nm, pf, ex, default_idx, selector, True)
-    # selector == names[current_idx] is a registered instance name (k=current);
-    # uniqueness pins resolve_prefix's choice to prefixes[current_idx].
-    Assert(nm[current_idx] == selector)
+    # VACUITY CONTROL: must FAIL. If it verifies, the consumed axiom is
+    # inconsistent and every rejection above is a false negative.
+    Assert(False)
     return url
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-14855.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A change-form (or edit) page rendered for one of several sibling
  administration deployments displays a read-only related object as a link.
  Several such deployments are registered under one shared application
  identifier; each deployment carries its own instance identifier (its name),
  its own URL prefix, and its own set of routes. They are distinguished only
  by that instance name.

  The link built for the related object must point INTO the very deployment
  that is currently rendering the page: the URL prefix of the produced link is
  the prefix registered for the current deployment's instance name, NOT the
  prefix of whichever deployment happens to be the registered default. When
  the current deployment is the default one the two coincide, but for any
  non-default current deployment the link must carry that deployment's own
  prefix. One deployment cannot be pointed into this way: a deployment whose
  instance identifier is EMPTY supplies nothing to resolve relative to, so the
  resolution callee cannot tell it from "no deployment named at all" and
  resolution for it lands on the default deployment's prefix.

  Resolution is PARTIAL, and the page states that too. The view identifier
  being resolved names a route that each deployment either carries or does
  not: `exposes[k]` is whether deployment k carries a route for the identifier
  and argument at hand. Resolution consults ONLY the deployment it lands in
  (the current one, or the default one for an empty instance identifier), so
  when that deployment carries no such route nothing resolves, the page shows
  the related object with NO link at all, and the produced value therefore
  carries no prefix -- modelled as the EMPTY sequence. A registered
  deployment's own prefix always carries at least the resolution root, so it
  is never empty and the empty result is unambiguous.

The instance-name selection performed when turning a view identifier into a
concrete URL (choosing which sibling deployment's prefix to use, given the
name of the deployment to resolve relative to, and looking the identifier up
inside that deployment) is an unchanged framework callee; it is axiomatized
here (`resolve_prefix`) as the WEAKEST contract the proof needs: a NON-EMPTY
registered instance name selects that instance, while an absent selector --
and equally an empty one, which the callee cannot tell apart from an absent
one -- selects the default instance; the selected instance's prefix is the
result when that instance carries the route, and nothing is produced when it
does not. Its soundness against the real callee is checked out-of-band by
axiom_check.py (G-AX).

Strings (instance names, URL prefixes) are modelled as `PSeq[int]` of Unicode
code points (Nagini bans `str` indexing). The registry of sibling deployments
is a triple of parallel pure sequences (instance name, URL prefix, carries the
route).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
@Pure
@ContractOnly
def resolve_prefix(names: PSeq[PSeq[int]], prefixes: PSeq[PSeq[int]],
                   exposes: PSeq[bool], default_idx: int, selector: PSeq[int],
                   has_selector: bool) -> PSeq[int]:
    """Unchanged framework callee: turn a view identifier into a URL by
    choosing which sibling deployment's prefix to apply and looking the
    identifier up inside that deployment.

    `names`/`prefixes`/`exposes` are the parallel registry of the sibling
    deployments sharing one application identifier: instance name, URL prefix,
    and whether that deployment carries a route for the identifier and
    argument being resolved. `default_idx` is the registered default instance.
    `selector` (active only when `has_selector`) is the name of the deployment
    to resolve relative to.

    Contract (weakest the proof needs). Selection: a NON-EMPTY selector naming
    a registered instance selects that instance; no selector -- or an EMPTY
    one, which the callee cannot distinguish from no selector at all --
    selects the default instance. Production: the selected instance's prefix
    when that instance carries the route, and NOTHING (the empty sequence)
    when it does not.

    Partiality is a genuine part of the callee's behaviour, not a gap: the
    callee narrows to the selected instance FIRST and then looks the
    identifier up only there, so an identifier absent from that one instance
    yields no URL even when a sibling carries it. The callee signals that
    rather than returning, and the consumer's arm for the signal produces no
    link, so the composite produces no prefix; the empty sequence is that
    value. Since a registered deployment's prefix carries at least the
    resolution root (see the Requires below) it is never empty, so the empty
    result cannot be confused with any deployment's prefix.

    Emptiness of the SELECTOR is likewise behaviour, not a gap: the callee
    consults the selector only after testing it for emptiness, and an empty
    selector fails that test, so it never reaches the name matching and the
    default instance is selected. An empty selector is therefore IN this
    contract's domain and is governed by the no-selector clauses; it is not
    excluded.

    Domain restriction: the selector is matched only after the callee splits it
    on the U+003A (`:`) component separator and resolves component-wise, so the
    selector-naming clause holds only for separator-free selectors (a name that
    embeds the separator is split into components and is not matched whole). The
    consumer supplies a separator-free selector; selectors containing U+003A are
    outside this contract's domain.

    Domain restriction (the registry is a MAP, not an arbitrary pair of lists):
    the callee looks a deployment up BY its instance identifier, so a registry
    associates each identifier with at most one deployment and hence with at
    most one prefix. A registry that offered one identifier under two different
    prefixes describes no state this callee can be in -- it would demand two
    different results from one lookup -- so such registries are outside this
    contract's domain. Stating this is what keeps the clauses below jointly
    SATISFIABLE: with identifiers unique, a supplied selector matches at most
    one registered deployment, so at most one clause pins the result. Without
    it the contract would assert a single value equal to two distinct prefixes
    at once, which is a claim no total callee can meet -- an assumption strictly
    stronger than the callee, and one that would let anything at all be derived
    from it. The consumer resolves relative to a registry of distinguishable
    sibling deployments and so supplies an in-domain registry.

    Domain restriction (a registered deployment's prefix is non-empty): a URL
    the callee produces carries the resolution root before anything else, so
    the prefix a registered deployment contributes to it is at least that root
    and never the empty sequence. This is a fact about the callee's output, not
    an exclusion of any deployment: a deployment mounted at the root has the
    root itself as its prefix. It is what makes "produced nothing" (the empty
    sequence) distinguishable from every prefix the callee can produce.

    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(len(names) == len(prefixes))
    Requires(len(exposes) == len(names))
    Requires(0 <= default_idx and default_idx < len(names))
    # Domain: instance identifiers are unique within the registry -- the callee
    # resolves a deployment BY identifier, so one identifier cannot stand for two
    # deployments with different prefixes. This is what makes the Ensures clauses
    # below jointly satisfiable (a selector matches at most one k), so the
    # contract stays a claim about a real lookup rather than an inconsistent one.
    Requires(Forall2(int, int, lambda a, b: (
        Implies(0 <= a and a < len(names) and 0 <= b and b < len(names)
                and names[a] == names[b], a == b),
        [[names[a], names[b]]])))
    # Domain: every registered deployment's prefix is non-empty -- a produced URL
    # carries the resolution root before anything else. This is what makes the
    # empty sequence (produced nothing) distinct from every producible prefix.
    Requires(Forall(int, lambda k: (
        Implies(0 <= k and k < len(prefixes), len(prefixes[k]) > 0),
        [[prefixes[k]]])))
    # Domain: the selector carries no U+003A (58) component separator (the
    # callee splits the selector on it before matching, so a separator-bearing
    # selector is not matched as a whole name -> outside this contract).
    Requires(Forall(int, lambda i: (
        Implies(0 <= i and i < len(selector), selector[i] != 58),
        [[selector[i]]])))
    # No selector -- or an EMPTY selector, which the callee tests for and cannot
    # tell from an absent one -> the registered default instance is selected, and
    # its prefix is the result exactly when it carries the route.
    Ensures(Implies((not has_selector or len(selector) == 0)
                    and exposes[default_idx],
                    Result() == prefixes[default_idx]))
    Ensures(Implies((not has_selector or len(selector) == 0)
                    and not exposes[default_idx],
                    len(Result()) == 0))
    # A NON-EMPTY selector naming a registered instance -> that instance is
    # selected, and its prefix is the result exactly when it carries the route;
    # the identifier is looked up in that instance ALONE, so an instance without
    # the route produces nothing even if a sibling has it. Emptiness is excluded
    # here because the callee never reaches the name matching for an empty
    # selector (see the docstring): claiming the instance's own prefix for it
    # would be stronger than the callee.
    Ensures(Forall(int, lambda k: (
        Implies(has_selector and len(selector) > 0
                and 0 <= k and k < len(names)
                and names[k] == selector and exposes[k],
                Result() == prefixes[k]),
        [[names[k]]])))
    Ensures(Forall(int, lambda k: (
        Implies(has_selector and len(selector) > 0
                and 0 <= k and k < len(names)
                and names[k] == selector and not exposes[k],
                len(Result()) == 0),
        [[names[k]]])))
# axioms-end

# pure-start
# (no auxiliary pure helpers needed)
# pure-end

def related_link_target(names: List[PSeq[int]], prefixes: List[PSeq[int]],
                        exposes: List[bool], default_idx: int,
                        current_idx: int) -> PSeq[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(Acc(list_pred(prefixes), 1 / 2))
    Requires(Acc(list_pred(exposes), 1 / 2))
    Requires(len(names) == len(prefixes))
    Requires(len(exposes) == len(names))
    Requires(0 <= default_idx and default_idx < len(names))
    Requires(0 <= current_idx and current_idx < len(names))
    # Instance names are unique: siblings are distinguished by their name.
    Requires(Forall2(int, int, lambda a, b: (
        Implies(0 <= a and a < len(names) and 0 <= b and b < len(names)
                and ToSeq(names)[a] == ToSeq(names)[b], a == b),
        [[ToSeq(names)[a], ToSeq(names)[b]]])))
    # Every registered deployment's prefix is non-empty: a produced URL carries
    # the resolution root before anything else, so no deployment contributes the
    # empty sequence -- which is what a link-less page's value is.
    Requires(Forall(int, lambda k: (
        Implies(0 <= k and k < len(prefixes), len(ToSeq(prefixes)[k]) > 0),
        [[ToSeq(prefixes)[k]]])))
    # The current deployment's instance name carries no U+003A (58) component
    # separator: it is resolved as a whole instance name, not split into
    # components (the resolution callee splits its selector on this separator).
    Requires(Forall(int, lambda i: (
        Implies(0 <= i and i < len(ToSeq(names)[current_idx]),
                ToSeq(names)[current_idx][i] != 58),
        [[ToSeq(names)[current_idx][i]]])))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(names), 1 / 2))
    Ensures(Acc(list_pred(prefixes), 1 / 2))
    Ensures(Acc(list_pred(exposes), 1 / 2))
    Ensures(len(prefixes) == len(names))
    Ensures(len(exposes) == len(names))
    Ensures(0 <= current_idx and current_idx < len(prefixes))
    Ensures(0 <= default_idx and default_idx < len(prefixes))
    # The produced link carries the CURRENT deployment's prefix, whenever that
    # deployment has a non-empty instance identifier to be resolved relative to
    # AND carries a route for the identifier being resolved.
    Ensures(Implies(len(ToSeq(names)[current_idx]) > 0
                    and ToSeq(exposes)[current_idx],
                    Result() == ToSeq(prefixes)[current_idx]))
    # Resolution consults the current deployment ALONE, so a current deployment
    # that carries no such route produces no link and hence no prefix -- even
    # when a sibling deployment does carry one.
    Ensures(Implies(len(ToSeq(names)[current_idx]) > 0
                    and not ToSeq(exposes)[current_idx],
                    len(Result()) == 0))
    # A deployment with an EMPTY instance identifier supplies nothing to resolve
    # relative to, so resolution lands on the default deployment: its prefix
    # when that deployment carries the route, and no link otherwise. The four
    # guards are mutually exclusive and together total, so the returned value is
    # pinned on every admissible input.
    Ensures(Implies(len(ToSeq(names)[current_idx]) == 0
                    and ToSeq(exposes)[default_idx],
                    Result() == ToSeq(prefixes)[default_idx]))
    Ensures(Implies(len(ToSeq(names)[current_idx]) == 0
                    and not ToSeq(exposes)[default_idx],
                    len(Result()) == 0))
    # post-conditions-end
    # impl-start
    # POSITIVE CONTROL: structurally different but CORRECT -- every local is
    # inlined into the resolution call and the result returned directly.
    url = resolve_prefix(ToSeq(names), ToSeq(prefixes), ToSeq(exposes),
                         default_idx, ToSeq(names)[current_idx], True)
    Assert(ToSeq(names)[current_idx] == ToSeq(names)[current_idx])
    return url
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit of django__django-14855/nagini. 10 distinct wrong-impl attacks + positive control + vacuity control, all machine-checked in  Per instruction, focus on the A-legs (the single A-consumed axiom resolve_prefix <-> django.urls.reverse) and the model<->patch correspondence; R/I legs left to G-CONF.

**SAME-SPEC:** all 12 files pass `python -m swebench_unified.adversary same-spec nagini django__django-14855 <f>` with exit 0 (spec byte-identical; only the impl region edited).

### REJECTED SEMANTICALLY (`... adversary weakness nagini django__django-14855 <f>` -> exit 2; error text from `... adversary verify ...`):
- atk_1.py PREPATCH BUG re-encoded (resolve_prefix(..., has_selector=False)). Error: `Postcondition of related_link_target might not hold. Assertion Implies(((len(ToSeq(names)[current_idx]) > 0) and ToSeq(exposes)[current_idx]), (Result() == ToSeq(prefixes)[current_idx])) might not hold` (atk_1.py:233). G-DIFF discriminating clause confirmed live => prepatch_reproduced=true.
- atk_3.py BOUNDARY / off-by-one on the emptiness test: a ONE-character instance name treated as no name at all (len(selector) > 1 instead of > 0). Same non-empty-clause postcondition failure. The emptiness boundary is exactly at 0, not near it.
- atk_5.py CONTROL-FLOW EFFECT / partiality-blind sibling scan: when the selected deployment carries no route, fall back to ANY sibling that does (i.e. resolution searches the whole registry rather than the one selected deployment). Rejected on Q5b: `Implies(((len(...) > 0) and (not ToSeq(exposes)[current_idx])), (len(Result()) == 0)) might not hold`. This is the load-bearing check that the spec models resolution as narrowing-then-looking-up, matching reverse+NoReverseMatch.
- atk_7.py DOCTORED ORACLE: axiom called correctly except the route vector is doctored (ex.update(default_idx, True)) to assume the default deployment always carries the route. Rejected on the same Q5b clause -- a VALUE-level rejection, since update preserves length so every axiom Requires still holds.
- atk_vac.py VACUITY CONTROL: `Assert(False)` after the real call -> `Assert might fail. Assertion False might not hold`. So the consumed axiom's four Ensures are jointly SATISFIABLE (the uniqueness + non-empty-prefix domain Requires do their documented job); nothing is derivable from it, hence no rejection above is a false negative and no verification is vacuous.
- atk_8.py CONTROL-FLOW / divergence (`while i >= 0` after the correct call) -> `Obligation leak check failed. Loop might not take all unsatisfied obligations from the context`. Requires(MustTerminate(2)) at the METHOD level really does reject a diverging rival (loop invariants alone would not).

CANDIDATES (exit 0 = shares spec AND verifies) -- 5 of them. For EVERY one the faithful refined patch was MATERIALIZED and EXECUTED under the official Docker harness via run_resolve('django__django-14855', <patch>, run_id='sbu-geq-hg1bh1e2-<n>', timeout=3600). Rendering pipeline validated first: my `gold` rendering of the same edit site is BYTE-IDENTICAL to applying the bundle's own patch.diff (diff of the resulting helpers.py is empty), and it RESOLVED (resolved=True, completed=True, attempts=1, flaky=False, F2P success=[test_readonly_foreignkey_links_custom_admin_site], F2P failure=[], P2P failure=0) -- so a non-resolve below could not be blamed on my harness plumbing. All 6 patches were `git apply --check`'d at base_commit 475cffd1d64c in a throwaway worktree (since a failed apply would masquerade as a spec break) and re-parsed with ast after application.
- atk_2.py PARTIAL-DOMAIN on the UNIQUENESS Requires: dead branch keyed on a sibling sharing the current deployment's instance name; serve the fallback deployment there. Verifies 16.2s. Faithful patch = check `app_dict['admin'].count(current_app) > 1` and omit current_app in that case. resolve_atk_2.json: resolved=True, completed=True, attempts=1, flaky=False, F2P success=[custom_admin_site], no failures. NOT a break.
- atk_4.py PARTIAL-DOMAIN on the COLON-free Requires (LEADING separator): dead branch on names[current_idx][0]==58 serving prefixes[current_idx] route-blind. Verifies 14.4s. Faithful patch = `if current_app.startswith(':')` arm. resolve_atk_4.json: resolved=True, no failures. NOT a break.
- atk_6.py UNGROUNDED-ORACLE ECHO: the axiomatized callee is never consulted at all; the postcondition's four-way case split is echoed directly off nm/pf/ex. Verifies 14.3s. Faithful patch = name the instance namespace inline (`'<site_name>:<app>_<model>_change'`) with the plain lookup when the name is falsy. resolve_atk_6.json: resolved=True, no failures. NOT a break -- and this is the informative one: the echo is not actually ungrounded, because reaching prefixes[current_idx] for a non-empty name IS the fixed behaviour and the only route to it in the real code is a current-instance-scoped reverse; the echo is extensionally equal to gold.
- atk_9.py PARTIAL-DOMAIN on the NON-EMPTY-PREFIX Requires: dead branch producing no link when the current deployment's own mount prefix is empty. Verifies 14.8s. Faithful patch = probe the site's own mount and `return str(remote_obj)` if empty. resolve_atk_9.json: resolved=True, no failures. NOT a break.
- atk_10.py PARTIAL-DOMAIN on the COLON-free Requires (TRAILING separator): dead branch on a name ending in ':' serving the fallback's prefix route-blind. Verifies 15.0s. Faithful patch = `if current_app.endswith(':')` arm. resolve_atk_10.json: resolved=True, no failures. NOT a break.

WHY THE 4 DOMAIN DEAD-BRANCH RIVALS ARE NOT WEAKNESSES (independently established, not assumed): I measured the actual resolver state the F2P test builds. ROOT_URLCONF for ReadonlyTest is 'admin_views.urls' (@override_settings at tests/admin_views/tests.py:4987, no subclasses, no method-level override). app_dict['admin'] there has exactly 12 instance namespaces -- autocomplete_admin, has_permission_admin, admin10, admin9, admin-extra-context, admin7, admin6, namespaced_admin (test_admin/admin5/, from AdminSite(name="namespaced_admin") at tests/admin_views/admin.py:1134), admin4, admin3, admin2, admin.

Verified facts: (a) all 12 are PAIRWISE DISTINCT, no duplicate name -> atk_2's branch is dead on the tested input, and it is dead for a real reason: namespace_dict is a dict keyed by namespace (resolvers.py:421,546), so one identifier cannot carry two prefixes; (b) NO instance name contains ':' -> atk_4's and atk_10's branches are dead, and are additionally no-ops on real behaviour since reverse splits current_app on ':' before matching (base.py:44-45), so a colon-bearing selector already fails `current_ns in app_list`; (c) NO mount prefix is empty (every one is /test_admin/...; get_script_prefix() is '/') -> atk_9's branch is dead, matching the axiom's non-empty-prefix domain fact that a produced URL carries the resolution root.

So each dead branch is unreachable in the real callee's state space, which is precisely what makes these Requires domain restrictions rather than convenience assumptions -- the impl cannot observe the excluded case to misbehave in it. That the four preconditions are each individually probed and each rival still RESOLVED is positive evidence the axiom is at the right strength rather than lax.

A-LEG AUDIT (resolve_prefix <-> django.urls.reverse, the only A-consumed leg; no A-reference deep model exists here, correctly): read reverse at base_commit (django/urls/base.py:27-84) and confirmed each clause against source. `if current_ns and current_ns in app_list: ns = current_ns` -> the two has_selector Ensures (non-empty selector naming a registered instance selects it).

`elif ns not in app_list: ns = app_list[0]` together with `if current_app: ... else: current_path = None` -> the two no-selector Ensures; the absorption of an EMPTY selector into the no-selector clauses is faithful to the falsiness guard at base.py:41 (an empty current_app is falsy, so current_path is None and the name matching is never reached) -- not a gap, and the axiom correctly declines to claim the instance's own prefix there, which would be STRONGER than the callee. `*path, view = viewname.split(':')` / `current_app.split(':')` -> the colon-free Requires on selector.

Terminal `return resolver._reverse_with_prefix(view, prefix, *args, **kwargs)`, which RAISES NoReverseMatch, plus get_admin_url's `except NoReverseMatch: return str(remote_obj)` arm -> the two len(Result())==0 clauses; partiality is modeled after the narrowing, i.e. the identifier is looked up in the SELECTED instance alone, which is what atk_5 confirms is load-bearing. default_idx as an unfixed existential placeholder is sound: no attack could exploit the unfixed index.

**REFINEMENT.MD AUDIT:** 6 legs, tagged R (1,2,3,6), A-consumed (4), I+R (5). Every leg is R / A-consumed / A-reference / I -- NO kind-3 (unexpressible-changed-op) step, and that claim is accurate: the changed operation is the argument list of a call to an UNCHANGED callee, so A-consumed rather than a deep A-reference model is the right treatment per SPEC_GUIDE 0.7/3, and deep-modeling reverse would model the unchanged machinery instead of the change. Step 4's has_selector True/False flip is the genuine discriminating content and atk_1 confirms the spec senses it.

Step 5's stated correspondence (the Assert plus the uniqueness Requires instantiating the axiom's has_selector Foralls at k=current_idx, under the non-empty-selector guard) holds against base.py:41-58 as quoted, and its claim about an empty AdminSite.name falling back to the default is correct. Step 6's format_html wrapping is prefix-preserving and the NoReverseMatch exit really is the empty PSeq. Step 1/2's registry <-> app_dict['admin'] R-leg is consistent with the measured 12-instance F2P deployment (colon-free, distinct, non-empty prefixes), so the domain restrictions are satisfiable on the tested input rather than vacuously dodging it.

The 'verify(model) => resolved' section's totality claim checks out: the four guards split on (name empty?) x (selected deployment carries route?), pairwise exclusive and jointly total, so no input is left unconstrained -- and atk_5/atk_7 are the live controls that neither len(Result())==0 clause is a licence to produce nothing elsewhere.

**CONCLUSION:** 10 distinct wrong-impl attacks run to completion (5 rejected semantically, 5 verified), plus a vacuity control that fails as required and a positive control that verifies. Every one of the 5 verifying rivals had its faithful refined patch materialized and EXECUTED under the official Docker harness, and all 5 RESOLVED with the F2P test passing and zero P2P regressions -- so none exhibits verify-but-not-correct. No G-EQ weakness found: verdict SOUND (advisory; runner re-runs). Cleanup: the throwaway git worktree I created was removed and pruned; the pre-existing * worktrees listed by `git worktree list` are from unrelated passes and were left untouched.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_3.py`, `atk_5.py`, `atk_7.py`, `atk_8.py`, `atk_vac.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_2.py`, `atk_4.py`, `atk_6.py`, `atk_9.py`, `atk_10.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_vac.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-14855.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A change-form (or edit) page rendered for one of several sibling
  administration deployments displays a read-only related object as a link.
  Several such deployments are registered under one shared application
  identifier; each deployment carries its own instance identifier (its name),
  its own URL prefix, and its own set of routes. They are distinguished only
  by that instance name.

  The link built for the related object must point INTO the very deployment
  that is currently rendering the page: the URL prefix of the produced link is
  the prefix registered for the current deployment's instance name, NOT the
  prefix of whichever deployment happens to be the registered default. When
  the current deployment is the default one the two coincide, but for any
  non-default current deployment the link must carry that deployment's own
  prefix. One deployment cannot be pointed into this way: a deployment whose
  instance identifier is EMPTY supplies nothing to resolve relative to, so the
  resolution callee cannot tell it from "no deployment named at all" and
  resolution for it lands on the default deployment's prefix.

  Resolution is PARTIAL, and the page states that too. The view identifier
  being resolved names a route that each deployment either carries or does
  not: `exposes[k]` is whether deployment k carries a route for the identifier
  and argument at hand. Resolution consults ONLY the deployment it lands in
  (the current one, or the default one for an empty instance identifier), so
  when that deployment carries no such route nothing resolves, the page shows
  the related object with NO link at all, and the produced value therefore
  carries no prefix -- modelled as the EMPTY sequence. A registered
  deployment's own prefix always carries at least the resolution root, so it
  is never empty and the empty result is unambiguous.

The instance-name selection performed when turning a view identifier into a
concrete URL (choosing which sibling deployment's prefix to use, given the
name of the deployment to resolve relative to, and looking the identifier up
inside that deployment) is an unchanged framework callee; it is axiomatized
here (`resolve_prefix`) as the WEAKEST contract the proof needs: a NON-EMPTY
registered instance name selects that instance, while an absent selector --
and equally an empty one, which the callee cannot tell apart from an absent
one -- selects the default instance; the selected instance's prefix is the
result when that instance carries the route, and nothing is produced when it
does not. Its soundness against the real callee is checked out-of-band by
axiom_check.py (G-AX).

Strings (instance names, URL prefixes) are modelled as `PSeq[int]` of Unicode
code points (Nagini bans `str` indexing). The registry of sibling deployments
is a triple of parallel pure sequences (instance name, URL prefix, carries the
route).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
@Pure
@ContractOnly
def resolve_prefix(names: PSeq[PSeq[int]], prefixes: PSeq[PSeq[int]],
                   exposes: PSeq[bool], default_idx: int, selector: PSeq[int],
                   has_selector: bool) -> PSeq[int]:
    """Unchanged framework callee: turn a view identifier into a URL by
    choosing which sibling deployment's prefix to apply and looking the
    identifier up inside that deployment.

    `names`/`prefixes`/`exposes` are the parallel registry of the sibling
    deployments sharing one application identifier: instance name, URL prefix,
    and whether that deployment carries a route for the identifier and
    argument being resolved. `default_idx` is the registered default instance.
    `selector` (active only when `has_selector`) is the name of the deployment
    to resolve relative to.

    Contract (weakest the proof needs). Selection: a NON-EMPTY selector naming
    a registered instance selects that instance; no selector -- or an EMPTY
    one, which the callee cannot distinguish from no selector at all --
    selects the default instance. Production: the selected instance's prefix
    when that instance carries the route, and NOTHING (the empty sequence)
    when it does not.

    Partiality is a genuine part of the callee's behaviour, not a gap: the
    callee narrows to the selected instance FIRST and then looks the
    identifier up only there, so an identifier absent from that one instance
    yields no URL even when a sibling carries it. The callee signals that
    rather than returning, and the consumer's arm for the signal produces no
    link, so the composite produces no prefix; the empty sequence is that
    value. Since a registered deployment's prefix carries at least the
    resolution root (see the Requires below) it is never empty, so the empty
    result cannot be confused with any deployment's prefix.

    Emptiness of the SELECTOR is likewise behaviour, not a gap: the callee
    consults the selector only after testing it for emptiness, and an empty
    selector fails that test, so it never reaches the name matching and the
    default instance is selected. An empty selector is therefore IN this
    contract's domain and is governed by the no-selector clauses; it is not
    excluded.

    Domain restriction: the selector is matched only after the callee splits it
    on the U+003A (`:`) component separator and resolves component-wise, so the
    selector-naming clause holds only for separator-free selectors (a name that
    embeds the separator is split into components and is not matched whole). The
    consumer supplies a separator-free selector; selectors containing U+003A are
    outside this contract's domain.

    Domain restriction (the registry is a MAP, not an arbitrary pair of lists):
    the callee looks a deployment up BY its instance identifier, so a registry
    associates each identifier with at most one deployment and hence with at
    most one prefix. A registry that offered one identifier under two different
    prefixes describes no state this callee can be in -- it would demand two
    different results from one lookup -- so such registries are outside this
    contract's domain. Stating this is what keeps the clauses below jointly
    SATISFIABLE: with identifiers unique, a supplied selector matches at most
    one registered deployment, so at most one clause pins the result. Without
    it the contract would assert a single value equal to two distinct prefixes
    at once, which is a claim no total callee can meet -- an assumption strictly
    stronger than the callee, and one that would let anything at all be derived
    from it. The consumer resolves relative to a registry of distinguishable
    sibling deployments and so supplies an in-domain registry.

    Domain restriction (a registered deployment's prefix is non-empty): a URL
    the callee produces carries the resolution root before anything else, so
    the prefix a registered deployment contributes to it is at least that root
    and never the empty sequence. This is a fact about the callee's output, not
    an exclusion of any deployment: a deployment mounted at the root has the
    root itself as its prefix. It is what makes "produced nothing" (the empty
    sequence) distinguishable from every prefix the callee can produce.

    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(len(names) == len(prefixes))
    Requires(len(exposes) == len(names))
    Requires(0 <= default_idx and default_idx < len(names))
    # Domain: instance identifiers are unique within the registry -- the callee
    # resolves a deployment BY identifier, so one identifier cannot stand for two
    # deployments with different prefixes. This is what makes the Ensures clauses
    # below jointly satisfiable (a selector matches at most one k), so the
    # contract stays a claim about a real lookup rather than an inconsistent one.
    Requires(Forall2(int, int, lambda a, b: (
        Implies(0 <= a and a < len(names) and 0 <= b and b < len(names)
                and names[a] == names[b], a == b),
        [[names[a], names[b]]])))
    # Domain: every registered deployment's prefix is non-empty -- a produced URL
    # carries the resolution root before anything else. This is what makes the
    # empty sequence (produced nothing) distinct from every producible prefix.
    Requires(Forall(int, lambda k: (
        Implies(0 <= k and k < len(prefixes), len(prefixes[k]) > 0),
        [[prefixes[k]]])))
    # Domain: the selector carries no U+003A (58) component separator (the
    # callee splits the selector on it before matching, so a separator-bearing
    # selector is not matched as a whole name -> outside this contract).
    Requires(Forall(int, lambda i: (
        Implies(0 <= i and i < len(selector), selector[i] != 58),
        [[selector[i]]])))
    # No selector -- or an EMPTY selector, which the callee tests for and cannot
    # tell from an absent one -> the registered default instance is selected, and
    # its prefix is the result exactly when it carries the route.
    Ensures(Implies((not has_selector or len(selector) == 0)
                    and exposes[default_idx],
                    Result() == prefixes[default_idx]))
    Ensures(Implies((not has_selector or len(selector) == 0)
                    and not exposes[default_idx],
                    len(Result()) == 0))
    # A NON-EMPTY selector naming a registered instance -> that instance is
    # selected, and its prefix is the result exactly when it carries the route;
    # the identifier is looked up in that instance ALONE, so an instance without
    # the route produces nothing even if a sibling has it. Emptiness is excluded
    # here because the callee never reaches the name matching for an empty
    # selector (see the docstring): claiming the instance's own prefix for it
    # would be stronger than the callee.
    Ensures(Forall(int, lambda k: (
        Implies(has_selector and len(selector) > 0
                and 0 <= k and k < len(names)
                and names[k] == selector and exposes[k],
                Result() == prefixes[k]),
        [[names[k]]])))
    Ensures(Forall(int, lambda k: (
        Implies(has_selector and len(selector) > 0
                and 0 <= k and k < len(names)
                and names[k] == selector and not exposes[k],
                len(Result()) == 0),
        [[names[k]]])))
# axioms-end

# pure-start
# (no auxiliary pure helpers needed)
# pure-end

def related_link_target(names: List[PSeq[int]], prefixes: List[PSeq[int]],
                        exposes: List[bool], default_idx: int,
                        current_idx: int) -> PSeq[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(Acc(list_pred(prefixes), 1 / 2))
    Requires(Acc(list_pred(exposes), 1 / 2))
    Requires(len(names) == len(prefixes))
    Requires(len(exposes) == len(names))
    Requires(0 <= default_idx and default_idx < len(names))
    Requires(0 <= current_idx and current_idx < len(names))
    # Instance names are unique: siblings are distinguished by their name.
    Requires(Forall2(int, int, lambda a, b: (
        Implies(0 <= a and a < len(names) and 0 <= b and b < len(names)
                and ToSeq(names)[a] == ToSeq(names)[b], a == b),
        [[ToSeq(names)[a], ToSeq(names)[b]]])))
    # Every registered deployment's prefix is non-empty: a produced URL carries
    # the resolution root before anything else, so no deployment contributes the
    # empty sequence -- which is what a link-less page's value is.
    Requires(Forall(int, lambda k: (
        Implies(0 <= k and k < len(prefixes), len(ToSeq(prefixes)[k]) > 0),
        [[ToSeq(prefixes)[k]]])))
    # The current deployment's instance name carries no U+003A (58) component
    # separator: it is resolved as a whole instance name, not split into
    # components (the resolution callee splits its selector on this separator).
    Requires(Forall(int, lambda i: (
        Implies(0 <= i and i < len(ToSeq(names)[current_idx]),
                ToSeq(names)[current_idx][i] != 58),
        [[ToSeq(names)[current_idx][i]]])))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(names), 1 / 2))
    Ensures(Acc(list_pred(prefixes), 1 / 2))
    Ensures(Acc(list_pred(exposes), 1 / 2))
    Ensures(len(prefixes) == len(names))
    Ensures(len(exposes) == len(names))
    Ensures(0 <= current_idx and current_idx < len(prefixes))
    Ensures(0 <= default_idx and default_idx < len(prefixes))
    # The produced link carries the CURRENT deployment's prefix, whenever that
    # deployment has a non-empty instance identifier to be resolved relative to
    # AND carries a route for the identifier being resolved.
    Ensures(Implies(len(ToSeq(names)[current_idx]) > 0
                    and ToSeq(exposes)[current_idx],
                    Result() == ToSeq(prefixes)[current_idx]))
    # Resolution consults the current deployment ALONE, so a current deployment
    # that carries no such route produces no link and hence no prefix -- even
    # when a sibling deployment does carry one.
    Ensures(Implies(len(ToSeq(names)[current_idx]) > 0
                    and not ToSeq(exposes)[current_idx],
                    len(Result()) == 0))
    # A deployment with an EMPTY instance identifier supplies nothing to resolve
    # relative to, so resolution lands on the default deployment: its prefix
    # when that deployment carries the route, and no link otherwise. The four
    # guards are mutually exclusive and together total, so the returned value is
    # pinned on every admissible input.
    Ensures(Implies(len(ToSeq(names)[current_idx]) == 0
                    and ToSeq(exposes)[default_idx],
                    Result() == ToSeq(prefixes)[default_idx]))
    Ensures(Implies(len(ToSeq(names)[current_idx]) == 0
                    and not ToSeq(exposes)[default_idx],
                    len(Result()) == 0))
    # post-conditions-end
    # impl-start
    # POSITIVE CONTROL: structurally different but CORRECT -- every local is
    # inlined into the resolution call and the result returned directly.
    url = resolve_prefix(ToSeq(names), ToSeq(prefixes), ToSeq(exposes),
                         default_idx, ToSeq(names)[current_idx], True)
    Assert(ToSeq(names)[current_idx] == ToSeq(names)[current_idx])
    return url
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit of django__django-14855/nagini. 10 distinct wrong-impl attacks + positive control + vacuity control, all machine-checked in  Per instruction, focus on the A-legs (the single A-consumed axiom resolve_prefix <-> django.urls.reverse) and the model<->patch correspondence; R/I legs left to G-CONF.

**SAME-SPEC:** all 12 files pass `python -m swebench_unified.adversary same-spec nagini django__django-14855 <f>` with exit 0 (spec byte-identical; only the impl region edited).

### REJECTED SEMANTICALLY (`... adversary weakness nagini django__django-14855 <f>` -> exit 2; error text from `... adversary verify ...`):
- atk_1.py PREPATCH BUG re-encoded (resolve_prefix(..., has_selector=False)). Error: `Postcondition of related_link_target might not hold. Assertion Implies(((len(ToSeq(names)[current_idx]) > 0) and ToSeq(exposes)[current_idx]), (Result() == ToSeq(prefixes)[current_idx])) might not hold` (atk_1.py:233). G-DIFF discriminating clause confirmed live => prepatch_reproduced=true.
- atk_3.py BOUNDARY / off-by-one on the emptiness test: a ONE-character instance name treated as no name at all (len(selector) > 1 instead of > 0). Same non-empty-clause postcondition failure. The emptiness boundary is exactly at 0, not near it.
- atk_5.py CONTROL-FLOW EFFECT / partiality-blind sibling scan: when the selected deployment carries no route, fall back to ANY sibling that does (i.e. resolution searches the whole registry rather than the one selected deployment). Rejected on Q5b: `Implies(((len(...) > 0) and (not ToSeq(exposes)[current_idx])), (len(Result()) == 0)) might not hold`. This is the load-bearing check that the spec models resolution as narrowing-then-looking-up, matching reverse+NoReverseMatch.
- atk_7.py DOCTORED ORACLE: axiom called correctly except the route vector is doctored (ex.update(default_idx, True)) to assume the default deployment always carries the route. Rejected on the same Q5b clause -- a VALUE-level rejection, since update preserves length so every axiom Requires still holds.
- atk_vac.py VACUITY CONTROL: `Assert(False)` after the real call -> `Assert might fail. Assertion False might not hold`. So the consumed axiom's four Ensures are jointly SATISFIABLE (the uniqueness + non-empty-prefix domain Requires do their documented job); nothing is derivable from it, hence no rejection above is a false negative and no verification is vacuous.
- atk_8.py CONTROL-FLOW / divergence (`while i >= 0` after the correct call) -> `Obligation leak check failed. Loop might not take all unsatisfied obligations from the context`. Requires(MustTerminate(2)) at the METHOD level really does reject a diverging rival (loop invariants alone would not).

CANDIDATES (exit 0 = shares spec AND verifies) -- 5 of them. For EVERY one the faithful refined patch was MATERIALIZED and EXECUTED under the official Docker harness via run_resolve('django__django-14855', <patch>, run_id='sbu-geq-hg1bh1e2-<n>', timeout=3600). Rendering pipeline validated first: my `gold` rendering of the same edit site is BYTE-IDENTICAL to applying the bundle's own patch.diff (diff of the resulting helpers.py is empty), and it RESOLVED (resolved=True, completed=True, attempts=1, flaky=False, F2P success=[test_readonly_foreignkey_links_custom_admin_site], F2P failure=[], P2P failure=0) -- so a non-resolve below could not be blamed on my harness plumbing. All 6 patches were `git apply --check`'d at base_commit 475cffd1d64c in a throwaway worktree (since a failed apply would masquerade as a spec break) and re-parsed with ast after application.
- atk_2.py PARTIAL-DOMAIN on the UNIQUENESS Requires: dead branch keyed on a sibling sharing the current deployment's instance name; serve the fallback deployment there. Verifies 16.2s. Faithful patch = check `app_dict['admin'].count(current_app) > 1` and omit current_app in that case. resolve_atk_2.json: resolved=True, completed=True, attempts=1, flaky=False, F2P success=[custom_admin_site], no failures. NOT a break.
- atk_4.py PARTIAL-DOMAIN on the COLON-free Requires (LEADING separator): dead branch on names[current_idx][0]==58 serving prefixes[current_idx] route-blind. Verifies 14.4s. Faithful patch = `if current_app.startswith(':')` arm. resolve_atk_4.json: resolved=True, no failures. NOT a break.
- atk_6.py UNGROUNDED-ORACLE ECHO: the axiomatized callee is never consulted at all; the postcondition's four-way case split is echoed directly off nm/pf/ex. Verifies 14.3s. Faithful patch = name the instance namespace inline (`'<site_name>:<app>_<model>_change'`) with the plain lookup when the name is falsy. resolve_atk_6.json: resolved=True, no failures. NOT a break -- and this is the informative one: the echo is not actually ungrounded, because reaching prefixes[current_idx] for a non-empty name IS the fixed behaviour and the only route to it in the real code is a current-instance-scoped reverse; the echo is extensionally equal to gold.
- atk_9.py PARTIAL-DOMAIN on the NON-EMPTY-PREFIX Requires: dead branch producing no link when the current deployment's own mount prefix is empty. Verifies 14.8s. Faithful patch = probe the site's own mount and `return str(remote_obj)` if empty. resolve_atk_9.json: resolved=True, no failures. NOT a break.
- atk_10.py PARTIAL-DOMAIN on the COLON-free Requires (TRAILING separator): dead branch on a name ending in ':' serving the fallback's prefix route-blind. Verifies 15.0s. Faithful patch = `if current_app.endswith(':')` arm. resolve_atk_10.json: resolved=True, no failures. NOT a break.

WHY THE 4 DOMAIN DEAD-BRANCH RIVALS ARE NOT WEAKNESSES (independently established, not assumed): I measured the actual resolver state the F2P test builds. ROOT_URLCONF for ReadonlyTest is 'admin_views.urls' (@override_settings at tests/admin_views/tests.py:4987, no subclasses, no method-level override). app_dict['admin'] there has exactly 12 instance namespaces -- autocomplete_admin, has_permission_admin, admin10, admin9, admin-extra-context, admin7, admin6, namespaced_admin (test_admin/admin5/, from AdminSite(name="namespaced_admin") at tests/admin_views/admin.py:1134), admin4, admin3, admin2, admin.

Verified facts: (a) all 12 are PAIRWISE DISTINCT, no duplicate name -> atk_2's branch is dead on the tested input, and it is dead for a real reason: namespace_dict is a dict keyed by namespace (resolvers.py:421,546), so one identifier cannot carry two prefixes; (b) NO instance name contains ':' -> atk_4's and atk_10's branches are dead, and are additionally no-ops on real behaviour since reverse splits current_app on ':' before matching (base.py:44-45), so a colon-bearing selector already fails `current_ns in app_list`; (c) NO mount prefix is empty (every one is /test_admin/...; get_script_prefix() is '/') -> atk_9's branch is dead, matching the axiom's non-empty-prefix domain fact that a produced URL carries the resolution root.

So each dead branch is unreachable in the real callee's state space, which is precisely what makes these Requires domain restrictions rather than convenience assumptions -- the impl cannot observe the excluded case to misbehave in it. That the four preconditions are each individually probed and each rival still RESOLVED is positive evidence the axiom is at the right strength rather than lax.

A-LEG AUDIT (resolve_prefix <-> django.urls.reverse, the only A-consumed leg; no A-reference deep model exists here, correctly): read reverse at base_commit (django/urls/base.py:27-84) and confirmed each clause against source. `if current_ns and current_ns in app_list: ns = current_ns` -> the two has_selector Ensures (non-empty selector naming a registered instance selects it).

`elif ns not in app_list: ns = app_list[0]` together with `if current_app: ... else: current_path = None` -> the two no-selector Ensures; the absorption of an EMPTY selector into the no-selector clauses is faithful to the falsiness guard at base.py:41 (an empty current_app is falsy, so current_path is None and the name matching is never reached) -- not a gap, and the axiom correctly declines to claim the instance's own prefix there, which would be STRONGER than the callee. `*path, view = viewname.split(':')` / `current_app.split(':')` -> the colon-free Requires on selector.

Terminal `return resolver._reverse_with_prefix(view, prefix, *args, **kwargs)`, which RAISES NoReverseMatch, plus get_admin_url's `except NoReverseMatch: return str(remote_obj)` arm -> the two len(Result())==0 clauses; partiality is modeled after the narrowing, i.e. the identifier is looked up in the SELECTED instance alone, which is what atk_5 confirms is load-bearing. default_idx as an unfixed existential placeholder is sound: no attack could exploit the unfixed index.

**REFINEMENT.MD AUDIT:** 6 legs, tagged R (1,2,3,6), A-consumed (4), I+R (5). Every leg is R / A-consumed / A-reference / I -- NO kind-3 (unexpressible-changed-op) step, and that claim is accurate: the changed operation is the argument list of a call to an UNCHANGED callee, so A-consumed rather than a deep A-reference model is the right treatment per SPEC_GUIDE 0.7/3, and deep-modeling reverse would model the unchanged machinery instead of the change. Step 4's has_selector True/False flip is the genuine discriminating content and atk_1 confirms the spec senses it.

Step 5's stated correspondence (the Assert plus the uniqueness Requires instantiating the axiom's has_selector Foralls at k=current_idx, under the non-empty-selector guard) holds against base.py:41-58 as quoted, and its claim about an empty AdminSite.name falling back to the default is correct. Step 6's format_html wrapping is prefix-preserving and the NoReverseMatch exit really is the empty PSeq. Step 1/2's registry <-> app_dict['admin'] R-leg is consistent with the measured 12-instance F2P deployment (colon-free, distinct, non-empty prefixes), so the domain restrictions are satisfiable on the tested input rather than vacuously dodging it.

The 'verify(model) => resolved' section's totality claim checks out: the four guards split on (name empty?) x (selected deployment carries route?), pairwise exclusive and jointly total, so no input is left unconstrained -- and atk_5/atk_7 are the live controls that neither len(Result())==0 clause is a licence to produce nothing elsewhere.

**CONCLUSION:** 10 distinct wrong-impl attacks run to completion (5 rejected semantically, 5 verified), plus a vacuity control that fails as required and a positive control that verifies. Every one of the 5 verifying rivals had its faithful refined patch materialized and EXECUTED under the official Docker harness, and all 5 RESOLVED with the F2P test passing and zero P2P regressions -- so none exhibits verify-but-not-correct. No G-EQ weakness found: verdict SOUND (advisory; runner re-runs). Cleanup: the throwaway git worktree I created was removed and pruned; the pre-existing * worktrees listed by `git worktree list` are from unrelated passes and were left untouched.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** SETUP. Fresh worktree of django_django.git at base_commit 475cffd1d64c690cdad16ede4d5e81985738ceb4, with the gold hunk (reverse(...) gains current_app=self.model_admin.admin_site.name at helpers.py:212) applied by hand and re-read to confirm. Reference for the modeled function = that PATCHED worktree, per the brief; base commit used only for the unchanged callee django.urls.reverse (base.py:27-86), which the patch does not touch. Note the bundle has no patch.diff file (only meta.json's patch_diff prose stub) -- I reconstructed the hunk from refinement.md's quoted gold hunk and verified it applies exactly.

**SPEC INTEGRITY.** `adversary same-spec nagini django__django-14855 atk.py` on a byte copy of model.py => exit 0, "SAME -- attack shares the bundle's exact specification". `scripts/nagini_verify.sh model.py` => "Verification successful" (13.4s). Non-vacuity control: injecting Assert(False) into the impl region FAILS ("Assertion False might not hold"), so the axiom's Requires domain (unique names + non-empty prefixes + colon-free selector) is satisfiable and the proof is not deriving from an inconsistent assumption. Discriminating content confirmed: model_prepatch.py FAILS exactly on the non-empty-name route-carrying clause (Implies(len(names[cur])>0 and exposes[cur], Result()==prefixes[cur])) -- so the spec is not so weak it accepts the bug, which matters here because a too-weak spec is the cheap way to be trivially 'faithful'.

**WHAT I ATTACKED.** The spec is TOO STRONG iff on some Requires-satisfying input the four postcondition clauses (C1 nonempty-name+route -> prefixes[current]; C2 nonempty-name+no-route -> empty; C3 empty-name+default-route -> prefixes[default]; C4 empty-name+default-no-route -> empty) disagree with the real patched get_admin_url. I wrote four independent harnesses from scratch (NOT derived from conformance_check.py), driving the real patched AdminReadonlyField.get_admin_url on a duck-typed receiver against real Django URLconfs built from the exact 3-tuple AdminSite.urls returns ((get_urls(), 'admin', self.name), sites.py:303).

### MEASUREMENTS (all zero violations).
1. diff2.py -- 14,746 obs, cov {C1 4154, C2 9412, C3 425, C4 755}, 0 violations. Nasty instance names (admin, '', namespaced_admin, 'a:b', 'admin:', '::', '.', 'x.*', '(grp)', 'admin\\', unicode, tab/space-bearing), heterogeneous per-site route sets, pk shapes incl. '', 0, negatives, 'a/b', unicode, 10^12, converter-rejecting args.
2. diff4.py -- 16,375 obs, cov {C1 4015, C2 10948, C3 399, C4 1013}, 0 violations. Robust bridge: default_idx discovered from the live no-selector path via a shared-NAME/deployment-UNIQUE-PATH anchor route (so it works even when mounts collide or the default is colon-named); exposes[k] observed on a ONE-deployment non-namespaced URLconf mounted at k's real mount (no selection mechanism present, so the observation cannot depend on the mechanism under test); the served deployment identified from a unique '/d<k>/' path segment rather than by prefix-startswith. Structural shapes: two siblings at the SAME mount, a site mounted under a converter (tt/<int:tenant>/), root-mounted ('' mount), a sibling named exactly like the app namespace and non-first, an admin instance nested inside a foreign namespace, and a FOREIGN app declaring a colliding instance namespace both before and after the admin entries.
3. final.py -- 27,445 obs, cov {C1 7080, C2 18581, C3 589, C4 1195}, 0 violations, over BOTH script prefixes ('/' and '/pre/'), additionally seeding %-malformed mounts (p%20q/, p%d/, p%s/, p%%/, a%zb/) and unicode mounts.
4. ax.py -- direct re-check of the resolve_prefix AXIOM's four Ensures against real reverse, including the two no-selector legs the impl does not consume (an unsound axiom would let the proof derive anything): 8,956 obs, cov {A1 775, A2 2344, A3 1600, A4 4237}, 0 violations.
Total ~67.5k live observations against the real callee, every clause covered, no diverging input.

### CONFIRMED-CORRECT SUBTLETIES (I tried to break each and it held).
* Falsiness: AdminSite(name='') is legal (sites.py:36) and reverse guards on `if current_app:` (base.py:41), so an empty name resolves against the DEFAULT, not the current site. Measured: siblings {'' -> /e1/, 'other' -> /e2/} in both registration orders; with 'other' the default, cur='' lands on /e2/'s table, exactly clauses C3/C4. The spec models this instead of over-claiming prefixes[current] -- this is the single most tempting over-strengthening and the spec does NOT commit it.
* Colon: reverse does current_app.split(':') BEFORE matching, so a colon-named instance is unreachable whole-name. Confirmed at base_commit; the spec correctly EXCLUDES colon selectors via Requires rather than claiming prefixes[k]. My sweeps generated colon-named siblings as non-current entries (permitted) and skipped them as current (excluded), so the restriction is honestly scoped, not a blanket domain gutting.
* Partiality: reverse narrows to ONE instance and only then runs `_reverse_with_prefix`, so an identifier a SIBLING carries but the selected site does not raises NoReverseMatch and get_admin_url renders no link. C2 dominated my coverage (18,581 obs) and never once found the real code falling back to a sibling. The empty-PSeq carrier for 'no link' is unambiguous because every registered prefix carries at least the root -- I confirmed a root-mounted deployment ('' mount) yields prefix '/', length 1, so the carrier never collides.
* Non-first same-name-as-app-namespace sibling: with {'zzz' -> /z1/ (no route), 'admin' -> /z2/}, app_dict['admin']=['admin','zzz'] and the elif never fires, so 'admin' is the default -- the spec's existential default_idx (never fixing the physical index) survives this; a spec that hard-coded app_dict[app][0] would have broken here.

### TWO AXES I FOUND AND ADJUDICATED AS NOT DEFECTS (recorded so a later panelist need not redo them).
(a) Global-namespace shadowing. resolver.namespace_dict is GLOBAL while app_dict is per-app, so a foreign app declaring instance namespace 'sitea' EARLIER than the admin entry named 'sitea' hijacks it: measured app_dict={'admin':['siteb','sitea'],'otherapp':['sitea']} but namespace_dict={'sitea':'foreign/','siteb':'adm_b/'}, and current_app='sitea' returns /foreign/... not /adm_a/.... This breaks C1 only under a SOURCE reading of prefixes[k] (= the mount the admin entry was declared at).

Under the RESOLVER reading -- prefixes[k] = the prefix reverse associates with instance namespace names[k], i.e. namespace_dict[names[k]][0], which is what mapping.md §2 means by 'Django's resolver.app_dict[admin] instance list + their mount prefixes' and what the bundle's own harness observes via reverse('<name>:<view>') -- the real result MATCHES on all four sub-cases I tabulated (foreign-carries-route x foreign-first, 2x2, all ok). The resolver reading is the correct one: it is the state reverse is actually in, and in this configuration the admin deployment really is unreachable, which is why Django itself emits urls.W005 ('URL namespace isn't unique. You may not be able to reverse all URLs in this namespace', checks/urls.py:46) for exactly this URLconf. So this is a modeling-row ambiguity resolved consistently in the faithful direction, not a spec-too-strong defect. Recommend mapping.md §2 pin the phrase to namespace_dict for future readers.

(b) reverse can raise something other than NoReverseMatch. A %-malformed route/mount (p%20q/, a%zb/) makes `_reverse_with_prefix` raise ValueError/TypeError from candidate_pat % subs, and a custom converter whose to_url raises propagates arbitrarily; get_admin_url catches only NoReverseMatch, so the composite RAISES where the total model returns a PSeq. Not a defect: in those states the deployment cannot produce any URL at all, so prefixes[k]/exposes[k] have no image under mapping.md's bridge -- the registry describes no state the bridge maps (my final.py counted 3,535 such inputs separately as 'no-bridge-image' and never scored them as passes either, so this is an honest exclusion, not a swept-under-the-rug one). It is also entirely a property of the UNCHANGED framework machinery, identical pre- and post-patch, so it carries no discriminating content in either direction.

HARNESS SELF-CORRECTIONS (disclosed so the zero is credible). My first two runs reported 207 and 157 'violations'; both were MY bridge bugs, not spec defects: (i) prefixes[k] must be the produced-URL form of the mount, so a unicode mount 'unicode/' appears percent-encoded (/%C3%BCn%C3%AF/) in the href -- fixed with urllib quote; (ii) exposes[k] must be observed WITH the deployment's own mount included, since a parameterized mount (tt/<int:tenant>/) genuinely makes the identifier unresolvable with the given args -- fixed by mounting the one-deployment probe URLconf at the real mount. After both fixes every sweep is clean, and the fixes made the probe STRICTER (exact landing-deployment identity, not prefix-startswith), not laxer.

**CONCLUSION.** I could not construct any Requires-satisfying input on which model.py's postcondition disagrees with the real patched get_admin_url. The two clauses that would be the natural over-strengthenings (empty instance name -> current site's prefix; resolution is total) are precisely the two the bundle documents as previously-found and repaired, and both repairs hold up against the live callee. The spec is at or below the strength of the real behavior while still rejecting the pre-patch twin. VERDICT: FAITHFUL; no diverging input exists to cite.

**SETUP.** Fresh worktree of django_django.git at base_commit 475cffd1d64c690cdad16ede4d5e81985738ceb4, with the gold hunk (reverse(...) gains current_app=self.model_admin.admin_site.name at helpers.py:212) applied by hand and re-read to confirm. Reference for the modeled function = that PATCHED worktree, per the brief; base commit used only for the unchanged callee django.urls.reverse (base.py:27-86), which the patch does not touch. Note the bundle has no patch.diff file (only meta.json's patch_diff prose stub) -- I reconstructed the hunk from refinement.md's quoted gold hunk and verified it applies exactly.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** LANE: leakage / gold-reconstruction, django__django-14855 (nagini). Judged against problem_statement ONLY; hints_text excluded as baseline. Every number below is my own measurement on the CURRENT bundle.

**NO RELAXATION IS IN PLAY.** meta.json has no `relaxed_leakage` key (checked: key absent, value None) and there is no RELAXED_LEAKAGE.md in the bundle directory. So this is a plain full-strength leakage judgement, not a relaxation to re-derive. I also ran swebench_unified.leakage.reviewer_directed() over every .md/.py/.json in the bundle (model.py, refinement.md, mapping.md, meta.json, axiom_check.py, conformance_check.py, properties.py, verdict.md): ZERO reviewer-directed hits. Nothing in the bundle addresses me, prescribes a verdict, or defines a recording convention.

ONE FINDING TO REPORT UNDER THAT HEADING, THOUGH IT IS NOT A DIRECTIVE: meta.json carries a RETAINED G-PANEL-3 stanza with agent_verdict='NO-LEAKAGE' and a full prior note. Per my standing rule that retained attack labels carry the oracle verdict, I did not adopt it. It is also STALE: that stanza's sources hash is model.py=dc251f79d3c1acbc2d500dcc3638699c1455326255770cae4c8c628a72621876, while the on-disk model.py is efec6e321793c61714f365e62b444a515ba9d801faa8a1a480243a23081e500c. The prior note therefore judged a DIFFERENT file than the one I judged, and its side claim that region_hashes are stale is no longer true for the current file (see next paragraph). My verdict happens to agree with the retained label; the measurements are mine.

SPEC-VIEW PROVENANCE (byte-exact, current file). Regenerated the consumer view with swebench_unified.markers.spec_view(nagini tables) from the on-disk model.py. The single impl region collapses to '...  # implementation elided — supplied by the consumer'; axioms, pure, pre-conditions, post-conditions pass through. Freshly computed region_hashes MATCH meta.json's stanza on ALL SIX regions including spec_view=069812a686cb5abe18eb8ec30a024c8769e55479c53c150229336b6eb391f531, and model.py's sha256 matches the sources hash on the G-LEAK, G-AX, G-CONF, G-GOLD, G-HYGIENE and G-DIFF gate stanzas — the recorded gates ran on exactly this file. markers.same_spec(model.py, model_prepatch.py) is True, so the spec view I judged is the frozen twin-shared one. `bash scripts/nagini_verify.sh model.py` -> 'Verification successful' (exit 0, 13.05s), so the artifact I audited is live.

THE BASELINE ALREADY CONTAINS THE ENTIRE GOLD EDIT — VERIFIED BY NORMALIZED SUBSTRING TEST, NOT ASSERTED. I whitespace-normalized the problem_statement and tested containment of each gold-diff side. All True: the removed line 'url = reverse(url_name, args=[quote(remote_obj.pk)])' and the added form 'reverse(url_name, args=[quote(remote_obj.pk)], current_app=self.model_admin.admin_site.name)'. The problem_statement also names 'get_admin_url', 'readonly_fields', 'django.contrib.admin.helpers', the 'current_app keyword' pointer, and the /admin/ vs /custom-admin/ symptom. The dataset gold patch is exactly that one-call change to django/contrib/admin/helpers.py. There is no headroom for the spec view to be MORE informative than a verbatim copy of the diff. I did not stop there.

**MECHANICAL SCANS ON THE VIEW'S OWN TERMS.** (a) Repo-symbol scan for reverse, current_app, admin_site, model_admin, format_html, NoReverseMatch, url_name, quote, remote_obj, remote_field, AdminSite, ModelAdmin, readonly, ForeignKey, app_dict, app_list, get_admin_url, custom-admin, /admin, helpers.py, urlconf, namespace: ZERO substantive hits. The only matches are lexical false positives: 'contrib' inside the English 'contributes'/'contributes to' (lines 123, 208), 'django' only in the instance id on line 1 ('Twin-artifact model for django__django-14855' — the instance name, public), and 'admin' inside the English word 'administration' (line 6). No Django symbol appears. (b) Provenance-marker regex sweep for '\.py:\d+', 7-40-char hex runs, '#\d{4,6}', '@@', 'diff --git', 'ticket', 'commit': ZERO matches. (c) Independent gold-line reproduction check: every +/- line of the patch, whitespace-normalized, absent from the normalized view. (d) Independent re-run of swebench_unified.leakage.screen(model.py, nagini, gold_patch, problem_statement, test_patch): passed=True, 0 hard_failures, 0 warnings — consistent with gates.G-LEAK status=pass.

HINTS-VOCABULARY DIFF (the canonical failure mode for this lane). Diffed spec-view tokens (>=4 chars) against problem_statement: 300 novel tokens, all Nagini/contract machinery (Requires, Ensures, PSeq, ToSeq, MustTerminate, list_pred, Forall, Forall2, ContractOnly), bundle scaffolding (axioms, impl, elided, provenance, twin, mapping, axiom_check), or the de-Djangoized abstraction vocabulary (deployment, prefix, selector, registry, sibling, route, exposes). Intersecting the novel set with hints-ONLY vocabulary leaves 12 survivors — against, before, currently, first, input, looks, real, since, what, which, without, would — every one a function word. None of the hints' distinctive content (the b790883065... backport SHA, ticket #31181, release-blocker framing, 3.2.8) appears anywhere in the view.

THE ONLY CLAUSES WITH NO problem_statement ANTECEDENT — MACHINE-CHECKED. The empty-instance-name fallback (docstring lines 17-20, the axiom's no-selector Ensures pair, and the two post-conditions 'len(names[current_idx]) == 0 => Result() == prefixes[default_idx]' / '=> len(Result()) == 0') plus the U+003A separator-free domain Requires. Two independent checks clear both:

  (1) PROVENANCE IS THE UNCHANGED CALLEE AT base_commit, NOT THE DIFF. I built a git worktree at base_commit 475cffd1d64c690cdad16ede4d5e81985738ceb4 and read django/urls/base.py directly. The guard is literally 'if current_app:' — a FALSINESS test, so an empty AdminSite.name never reaches the 'if current_ns and current_ns in app_list' matching and falls through to the 'elif ns not in app_list' default arm; and 'current_path = current_app.split(":")' is the exact component split the U+003A domain restriction encodes. I also confirmed the base-commit helpers.py get_admin_url is the unpatched one-line reverse() call inside try/except NoReverseMatch: return str(remote_obj) — the two exits the spec's empty-sequence value models. Both facts are readable in UNCHANGED framework code at base_commit by any solver; neither is derivable only from the gold diff or hints.

  (2) THE CLAUSES CARRY ZERO DISCRIMINATING CONTENT — MEASURED, NOT ARGUED (this is the load-bearing test the lane asks for). I stripped the two empty-name post-conditions from model_prepatch.py (prepatch_noempty.py) and ran the pinned verifier: it STILL FAILS, exit 1, and fails on the OTHER clause — 'Postcondition of related_link_target might not hold. Assertion Implies(((len(ToSeq(names)[current_idx]) > 0) and ToSeq(exposes)[current_idx]), (Result() == ToSeq(prefixes)[current_idx])) might not hold.' So the NON-EMPTY-name clause alone rejects the pre-patch impl; the empty-name clauses do no discriminating work and cannot be reverse-engineered into the edit. They also name default_idx as a bare existential index without ever fixing WHICH sibling the framework falls back to (app_dict['admin'][0]), so they do not disclose the resolver's fallback rule either.

CORE GATES THE JUDGEMENT LEANS ON, RE-READ: G-LEAK pass (and re-run by me, passed=True), G-HYGIENE pass with region hashes I recomputed and matched, G-GOLD pass, G-DIFF pass (and independently reproduced above), G-VERIFY pass (reproduced: exit 0). G-PANEL-2 (faithfulness) is recorded FAIL — a spec-strength finding on heterogeneous sibling registries. That is a different lane and does not bear on leakage: an over-strong Ensures on an untested input class discloses nothing about the gold edit beyond a problem_statement that already quotes it. I flag it only so the record shows I saw it and did not let a sibling-lane failure color this one.

**CONCLUSION:** no gold-diff line reproduced, no patched path/module/symbol echoed, no diff or provenance markers, no bug/fix narration, no hints-only content, and the only clauses without a problem_statement antecedent are base_commit-readable properties of an unchanged callee that I MEASURED to carry no discriminating power. VERDICT: NO-LEAKAGE. No counterexample applies — this lane's deliverable is the reconstruction argument, not a verifying rival.

**HYGIENE:** all scratch under mktemp -d ( worktree, removed via `git worktree remove --force`) plus  for the prepatch probe; bundle read-only throughout and re-confirmed byte-identical after the audit (model.py sha256 still efec6e32...). No git stash, no tree-wide git operations.

**LANE:** leakage / gold-reconstruction, django__django-14855 (nagini). Judged against problem_statement ONLY; hints_text excluded as baseline. Every number below is my own measurement on the CURRENT bundle.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
