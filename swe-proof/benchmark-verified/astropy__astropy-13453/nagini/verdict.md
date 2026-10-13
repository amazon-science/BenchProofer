# P2 adversarial audit — astropy__astropy-13453

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -109,7 +109,7 @@
             result[k] == resolved_format(names[k], prior_formats[k], formats)))))
         # invariants-end
         name = names[i]
-        if name in formats:
+        if i > 0 and name in formats:
             result.append(formats[name])
         else:
             result.append(prior_formats[i])
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -110,7 +110,7 @@
         # invariants-end
         name = names[i]
         if name in formats:
-            result.append(formats[name])
+            result.append(prior_formats[i])
         else:
             result.append(prior_formats[i])
         i = i + 1
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -110,7 +110,7 @@
         # invariants-end
         name = names[i]
         if name in formats:
-            result.append(formats[name])
+            result.append(name)
         else:
             result.append(prior_formats[i])
         i = i + 1
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -109,8 +109,8 @@
             result[k] == resolved_format(names[k], prior_formats[k], formats)))))
         # invariants-end
         name = names[i]
-        if name in formats:
-            result.append(formats[name])
+        if prior_formats[i] in formats:
+            result.append(formats[prior_formats[i]])
         else:
             result.append(prior_formats[i])
         i = i + 1
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -109,7 +109,7 @@
             result[k] == resolved_format(names[k], prior_formats[k], formats)))))
         # invariants-end
         name = names[i]
-        if name in formats:
+        if i < len(names) - 1 and name in formats:
             result.append(formats[name])
         else:
             result.append(prior_formats[i])
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -112,7 +112,7 @@
         if name in formats:
             result.append(formats[name])
         else:
-            result.append(prior_formats[i])
+            result.append(prior_formats[len(prior_formats) - 1 - i])
         i = i + 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for astropy__astropy-13453.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A tabular writer prepares a list of output columns for rendering. The caller
  may supply a per-name formatting mapping: a dictionary from a column's name to
  the format specification that column should be rendered with. The preparation
  step resolves, for every output column, the format specification that will
  govern how that column's values are turned into text:

    * if the column's name appears as a key in the supplied mapping, the
      resolved format for that column is the value the mapping records for that
      name;
    * otherwise the column keeps the format specification it already carried.

  The consequence that matters: when a column's name is present in the supplied
  mapping, the rendered values of that column must honour the supplied
  specification rather than the column's pre-existing one. A column whose name
  is absent from the mapping is left untouched.

Modelling choices (Nagini fragment):
  * Column names are `int` keys (opaque identity tokens); format
    specifications are `int` tokens (opaque identity of a format spec). The
    tested behaviour only observes WHICH spec each column ends up bound to, so
    integer identity is the faithful carrier (mapping.md §2).
  * The set of output columns is two parallel `List[int]`: `names[i]` and the
    pre-existing `prior_formats[i]` of column `i`.
  * The supplied mapping is a `Dict[int, int]` from name to format token.
  * The result is a `List[int]`: the resolved format token of each column,
    index-aligned with the inputs.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import List, Dict
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The format-resolution logic is the behaviour under
# specification and is modelled deeply (resolved_format / the loop). The
# per-name dictionary membership/lookup it composes is ordinary mapping
# semantics, validated against real Python semantics out-of-band by
# axiom_check.py (G-AX) as an A-reference, not consumed here.
# axioms-end


# pure-start
@Pure
def resolved_format(name: int, prior: int, formats: Dict[int, int]) -> int:
    """The format token column `name` ends up bound to.

    `prior` is the format specification the column already carried. If the
    supplied mapping records the column's name, the recorded value is used;
    otherwise the prior specification is kept.
    """
    Requires(Acc(dict_pred(formats), 1 / 4))
    if name in formats:
        return formats[name]
    return prior
# pure-end


def resolve_column_formats(names: List[int], prior_formats: List[int],
                           formats: Dict[int, int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(Acc(list_pred(prior_formats), 1 / 2))
    Requires(Acc(dict_pred(formats), 1 / 2))
    # The two parallel column arrays are index-aligned.
    Requires(len(names) == len(prior_formats))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(names), 1 / 2))
    Ensures(Acc(list_pred(prior_formats), 1 / 2))
    Ensures(Acc(dict_pred(formats), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is one resolved format token per column, in order.
    Ensures(len(Result()) == len(names))
    # Element i is the resolved format of column i: the supplied mapping's
    # value when the column's name is present, the prior format otherwise.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(names)
        and i < len(prior_formats),
        Result()[i] == resolved_format(names[i], prior_formats[i], formats)))))
    # The discriminating behaviour: a column whose name is in the mapping is
    # bound to exactly the supplied specification ...
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(names)
        and (names[i] in formats),
        Result()[i] == formats[names[i]]))))
    # ... and a column whose name is absent keeps its prior specification.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(names)
        and i < len(prior_formats) and not (names[i] in formats),
        Result()[i] == prior_formats[i]))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(names):
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(Acc(list_pred(prior_formats), 1 / 2))
        Invariant(Acc(dict_pred(formats), 1 / 2))
        Invariant(len(names) == len(prior_formats))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(names))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i
            and k < len(prior_formats),
            result[k] == resolved_format(names[k], prior_formats[k], formats)))))
        # invariants-end
        name = names[i]
        if name in formats:
            result.append(formats[name])
        else:
            result.append(prior_formats[i])
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Instance astropy__astropy-13453 (nagini). Spec models the writer's per-column format resolution: resolve_column_formats returns, per column, formats[names[i]] when names[i] in formats, else prior_formats[i]. The postcondition FULLY PINS the output: len(Result())==len(names) plus three Forall postconds (element==resolved_format; present-name==formats[names[i]]; absent-name==prior_formats[i]) combined with precondition len(names)==len(prior_formats) determine every index. No degrees of freedom remain for a verifying wrong impl.

BASELINE (adversary weakness, nagini_verify via JVM+Z3): positive_control.py (=gold model.py) => CANDIDATE, verifies (exit 0, 25.3s). prepatch.py (=model_prepatch.py, always appends prior_formats[i]) => NOT-A-COUNTEREXAMPLE, verification FAILED (exit 2) => prepatch bug reproduced (spec senses the change / G-DIFF).

Every attack returned exit 2 (does NOT verify => spec rejected):
atk_1 partial-domain: skip first column (i>0 guard on present branch) — fails present-name postcond at i=0. REJECTED.
atk_2 control-flow-effect: mapping never consulted (both branches append prior) — prepatch-equivalent distinct spelling. REJECTED.
atk_3 ungrounded-oracle echo: on present branch append the NAME token instead of formats[name]. REJECTED.
atk_4 wrong-membership-key: test/lookup on prior_formats[i] instead of the name token. REJECTED.
atk_5 boundary: skip LAST column (i<len(names)-1 guard on present branch). REJECTED.
atk_6 off-by-one prior index: absent branch appends prior_formats[len-1-i]. REJECTED.
No verifying wrong impl was found, so no faithful-patch materialization / run_resolve was triggered (protocol requires resolve only for verifying CANDIDATES; positive_control is the gold-equivalent correct impl and is not a wrong impl).

A-LEG / refinement.md AUDIT: legs A1=R, A2=R, A3=A-reference, A4=R. NO A-consumed axiom, NO kind-3 leg (matches §B). A3 correspondence: model resolved_format/loop <-> BaseData._set_col_formats (astropy/io/ascii/core.py:934-938). Ran axiom_check.py (copied to scratch, `python axiom_check_copy.py`, exit 0): deep model == faithful reference on 12 boundary + 50000 fuzz token-level cases, AND == the GENUINE astropy _set_col_formats on 2000 real int+float Column compatible-domain cases, PLUS 200 positive raise-boundary probes (float col + int-only spec => validating Column.format setter raises at assignment) — guarded-equality partiality documented and positively exercised, not hidden. Model<->patch correspondence holds: gold patch adds self.data.cols=cols + self.data._set_col_formats() (the exact modeled resolution the pre-patch HTML writer skipped).

Env: project root, PY=python, SBU_BENCHMARK_DIR=benchmark-verified. 6 attacks run and all fail to verify; positive control verifies; prepatch reproduced; A-legs audited. => SOUND (verify => correct not falsified).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for astropy__astropy-13453.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A tabular writer prepares a list of output columns for rendering. The caller
  may supply a per-name formatting mapping: a dictionary from a column's name to
  the format specification that column should be rendered with. The preparation
  step resolves, for every output column, the format specification that will
  govern how that column's values are turned into text:

    * if the column's name appears as a key in the supplied mapping, the
      resolved format for that column is the value the mapping records for that
      name;
    * otherwise the column keeps the format specification it already carried.

  The consequence that matters: when a column's name is present in the supplied
  mapping, the rendered values of that column must honour the supplied
  specification rather than the column's pre-existing one. A column whose name
  is absent from the mapping is left untouched.

Modelling choices (Nagini fragment):
  * Column names are `int` keys (opaque identity tokens); format
    specifications are `int` tokens (opaque identity of a format spec). The
    tested behaviour only observes WHICH spec each column ends up bound to, so
    integer identity is the faithful carrier (mapping.md §2).
  * The set of output columns is two parallel `List[int]`: `names[i]` and the
    pre-existing `prior_formats[i]` of column `i`.
  * The supplied mapping is a `Dict[int, int]` from name to format token.
  * The result is a `List[int]`: the resolved format token of each column,
    index-aligned with the inputs.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import List, Dict
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The format-resolution logic is the behaviour under
# specification and is modelled deeply (resolved_format / the loop). The
# per-name dictionary membership/lookup it composes is ordinary mapping
# semantics, validated against real Python semantics out-of-band by
# axiom_check.py (G-AX) as an A-reference, not consumed here.
# axioms-end


# pure-start
@Pure
def resolved_format(name: int, prior: int, formats: Dict[int, int]) -> int:
    """The format token column `name` ends up bound to.

    `prior` is the format specification the column already carried. If the
    supplied mapping records the column's name, the recorded value is used;
    otherwise the prior specification is kept.
    """
    Requires(Acc(dict_pred(formats), 1 / 4))
    if name in formats:
        return formats[name]
    return prior
# pure-end


def resolve_column_formats(names: List[int], prior_formats: List[int],
                           formats: Dict[int, int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(Acc(list_pred(prior_formats), 1 / 2))
    Requires(Acc(dict_pred(formats), 1 / 2))
    # The two parallel column arrays are index-aligned.
    Requires(len(names) == len(prior_formats))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(names), 1 / 2))
    Ensures(Acc(list_pred(prior_formats), 1 / 2))
    Ensures(Acc(dict_pred(formats), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is one resolved format token per column, in order.
    Ensures(len(Result()) == len(names))
    # Element i is the resolved format of column i: the supplied mapping's
    # value when the column's name is present, the prior format otherwise.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(names)
        and i < len(prior_formats),
        Result()[i] == resolved_format(names[i], prior_formats[i], formats)))))
    # The discriminating behaviour: a column whose name is in the mapping is
    # bound to exactly the supplied specification ...
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(names)
        and (names[i] in formats),
        Result()[i] == formats[names[i]]))))
    # ... and a column whose name is absent keeps its prior specification.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(names)
        and i < len(prior_formats) and not (names[i] in formats),
        Result()[i] == prior_formats[i]))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(names):
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(Acc(list_pred(prior_formats), 1 / 2))
        Invariant(Acc(dict_pred(formats), 1 / 2))
        Invariant(len(names) == len(prior_formats))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(names))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i
            and k < len(prior_formats),
            result[k] == resolved_format(names[k], prior_formats[k], formats)))))
        # invariants-end
        name = names[i]
        if name in formats:
            result.append(formats[name])
        else:
            result.append(prior_formats[i])
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Instance astropy__astropy-13453 (nagini). Spec models the writer's per-column format resolution: resolve_column_formats returns, per column, formats[names[i]] when names[i] in formats, else prior_formats[i]. The postcondition FULLY PINS the output: len(Result())==len(names) plus three Forall postconds (element==resolved_format; present-name==formats[names[i]]; absent-name==prior_formats[i]) combined with precondition len(names)==len(prior_formats) determine every index. No degrees of freedom remain for a verifying wrong impl.

BASELINE (adversary weakness, nagini_verify via JVM+Z3): positive_control.py (=gold model.py) => CANDIDATE, verifies (exit 0, 25.3s). prepatch.py (=model_prepatch.py, always appends prior_formats[i]) => NOT-A-COUNTEREXAMPLE, verification FAILED (exit 2) => prepatch bug reproduced (spec senses the change / G-DIFF).

Every attack returned exit 2 (does NOT verify => spec rejected):
atk_1 partial-domain: skip first column (i>0 guard on present branch) — fails present-name postcond at i=0. REJECTED.
atk_2 control-flow-effect: mapping never consulted (both branches append prior) — prepatch-equivalent distinct spelling. REJECTED.
atk_3 ungrounded-oracle echo: on present branch append the NAME token instead of formats[name]. REJECTED.
atk_4 wrong-membership-key: test/lookup on prior_formats[i] instead of the name token. REJECTED.
atk_5 boundary: skip LAST column (i<len(names)-1 guard on present branch). REJECTED.
atk_6 off-by-one prior index: absent branch appends prior_formats[len-1-i]. REJECTED.
No verifying wrong impl was found, so no faithful-patch materialization / run_resolve was triggered (protocol requires resolve only for verifying CANDIDATES; positive_control is the gold-equivalent correct impl and is not a wrong impl).

A-LEG / refinement.md AUDIT: legs A1=R, A2=R, A3=A-reference, A4=R. NO A-consumed axiom, NO kind-3 leg (matches §B). A3 correspondence: model resolved_format/loop <-> BaseData._set_col_formats (astropy/io/ascii/core.py:934-938). Ran axiom_check.py (copied to scratch, `python axiom_check_copy.py`, exit 0): deep model == faithful reference on 12 boundary + 50000 fuzz token-level cases, AND == the GENUINE astropy _set_col_formats on 2000 real int+float Column compatible-domain cases, PLUS 200 positive raise-boundary probes (float col + int-only spec => validating Column.format setter raises at assignment) — guarded-equality partiality documented and positively exercised, not hidden. Model<->patch correspondence holds: gold patch adds self.data.cols=cols + self.data._set_col_formats() (the exact modeled resolution the pre-patch HTML writer skipped).

Env: project root, PY=python, SBU_BENCHMARK_DIR=benchmark-verified. 6 attacks run and all fail to verify; positive control verifies; prepatch reproduced; A-legs audited. => SOUND (verify => correct not falsified).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous checks performed: (1) same-spec on an identical copy of model.py exits 0 (SAME — shares the bundle's exact spec region). (2) scripts/nagini_verify.sh on model.py: Verification successful (22.5s) — the spec is satisfiable/consistent. (3) Real repo at base_commit 19cc804717 confirmed: astropy/io/ascii/core.py:934-938 BaseData._set_col_formats is `for col in self.cols: if col.info.name in self.formats: col.info.format = self.formats[col.info.name]` — byte-for-byte the resolution the model computes (formats[name] when present, else prior). (4) axiom_check.py G-AX stdlib path passes (12 boundary + 50000 fuzz inputs, model == faithful reimplementation of core.py:934-938); the genuine-astropy path is guarded by ImportError and was skipped locally (erfa missing on host verifier env), which is the documented behaviour — it runs in the eval container. FAITHFULNESS conclusion: the spec's three postconditions pin exactly the real per-column resolution over the abstraction (name/spec as int identity tokens, in-place info.format mutation modeled as an index-aligned result list). The abstraction is sound: the resolution never inspects name/spec content, only identity/membership. The single documented partiality (dtype-incompatible spec -> real callee raises) is a downstream validating-setter EFFECT outside the modeled resolution decision and outside the tested domain, and is disclosed + positively probed rather than concealed. This is not a spec-too-strong drift: no verifying same-spec implementation could resolve while diverging from gold on the tested inputs. Spec is faithful.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = model.py with impl region elided (verified via markers.spec_view). Mechanical G-LEAK screen passes (no hard failures). Manual leakage review confirms nothing reconstructs the gold edit beyond the PUBLIC problem_statement:

- No diff markers, no patched file path (html.py / core.py), no patched module path in the spec view.
- No spec-view identifier or comment names any patched repo symbol. The gold patch touches HTML.write / adds `self.data.cols = cols` and `self.data._set_col_formats()`; changed symbols like `_set_col_formats`, `str_vals`, `cols` do not appear as spec-view identifiers or in comments. Spec-view symbols are generic (`resolve_column_formats`, `resolved_format`, `names`, `prior_formats`, `formats`) — none embeds a patched def/class name.
- No gold-patch changed line is reproduced (the impl is elided to `...`; the visible region is only pre/post-conditions + the pure resolved_format decision, all over opaque int tokens).
- No bug/fix narration terms in comments.

The behavior the spec states (a column's format = supplied mapping value if its name is present, else its prior format; present-name columns must honour the supplied spec) is exactly what the public problem_statement already demands ('I expect the HTML table output to respect the formatting given by the formats argument'; it works for CSV/rst but is ignored for HTML). The spec discloses no localization (which file/function/line to edit) beyond that publicly-stated requirement. The refinement.md/mapping.md docs (which DO name html.py/core.py/_set_col_formats) are NOT part of the consumer spec view and are not screened by G-PANEL-3. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
