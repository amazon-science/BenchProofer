# P2 adversarial audit — sphinx-doc__sphinx-7590

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_swapguard.py`, `atk_c_nofold.py`, `atk_c_swap.py`, `atk_partial.py`, `atk_boundary.py`, `atk_oracle.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_swapguard.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -115,7 +114,6 @@
     # identifier's id-generator), whenever a trailing identifier is present
     Requires(Implies(len(ToSeq(ident)) > 0,
                      ToSeq(ident_id) == ident_mangle(ToSeq(ident))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(lit), 1 / 2))
@@ -138,15 +136,14 @@
                     ToSeq(Result()) == number_id_seq(ToSeq(lit))))
     # post-conditions-end
     # impl-start
-    if not suffixed and len(ident) > 0:
-        # user-defined literal: mangle as the call ident(literal),
-        # concatenating the prefix, the identifier id, the numeric id and the
-        # framing 'E's.
+    # ATTACK (control-flow-effect): FLIPPED guard — build the UDL mangling when
+    # the literal is SUFFIXED (should be ordinary number id) and the ordinary id
+    # when unsuffixed-with-identifier (should be UDL). Behaviourally swapped.
+    if suffixed and len(ident) > 0:
         result = [99, 108, 76, 95, 90, 108, 105] + ident_id \
             + [69, 76] + lit + [69, 69]  # type: List[int]
         return result
     else:
-        # ordinary numeric literal: its id is 'L' + text + 'E'
         out = [76] + lit + [69]  # type: List[int]
         return out
     # impl-end
@@ -159,7 +156,6 @@
     Requires(Acc(list_pred(trail), 1 / 2))
     # a numeric literal always has nonempty text
     Requires(len(lit) > 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(lit), 1 / 2))
```

Attack 2 — `atk_c_nofold.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -115,7 +114,6 @@
     # identifier's id-generator), whenever a trailing identifier is present
     Requires(Implies(len(ToSeq(ident)) > 0,
                      ToSeq(ident_id) == ident_mangle(ToSeq(ident))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(lit), 1 / 2))
@@ -159,7 +157,6 @@
     Requires(Acc(list_pred(trail), 1 / 2))
     # a numeric literal always has nonempty text
     Requires(len(lit) > 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(lit), 1 / 2))
@@ -179,12 +176,9 @@
                     ToSeq(Result()) == number_id_seq(ToSeq(lit))))
     # post-conditions-end
     # impl-start
-    if valid:
-        # the recognised numeric suffix is consumed into the literal text
-        out = [76] + lit + trail + [69]  # type: List[int]
-        return out
-    else:
-        # the trailing run is not a valid suffix: the literal text is just `lit`
-        plain = [76] + lit + [69]  # type: List[int]
-        return plain
+    # ATTACK (control-flow-effect on c_number_literal_id): NEVER fold the trail
+    # even when valid — always return the bare-literal id. Behaviourally wrong
+    # on the valid branch (should be L+lit+trail+E).
+    plain = [76] + lit + [69]  # type: List[int]
+    return plain
     # impl-end
```

Attack 3 — `atk_c_swap.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -115,7 +114,6 @@
     # identifier's id-generator), whenever a trailing identifier is present
     Requires(Implies(len(ToSeq(ident)) > 0,
                      ToSeq(ident_id) == ident_mangle(ToSeq(ident))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(lit), 1 / 2))
@@ -159,7 +157,6 @@
     Requires(Acc(list_pred(trail), 1 / 2))
     # a numeric literal always has nonempty text
     Requires(len(lit) > 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(lit), 1 / 2))
@@ -179,12 +176,13 @@
                     ToSeq(Result()) == number_id_seq(ToSeq(lit))))
     # post-conditions-end
     # impl-start
+    # ATTACK (boundary/swap on c_number_literal_id): fold the trail on the
+    # NOT-valid branch and keep it bare on the valid branch — the exact inverse
+    # of the spec (matches prepatch-style bug on the wrong side).
     if valid:
-        # the recognised numeric suffix is consumed into the literal text
+        plain = [76] + lit + [69]  # type: List[int]
+        return plain
+    else:
         out = [76] + lit + trail + [69]  # type: List[int]
         return out
-    else:
-        # the trailing run is not a valid suffix: the literal text is just `lit`
-        plain = [76] + lit + [69]  # type: List[int]
-        return plain
     # impl-end
```

Attack 4 — `atk_partial.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -115,7 +114,6 @@
     # identifier's id-generator), whenever a trailing identifier is present
     Requires(Implies(len(ToSeq(ident)) > 0,
                      ToSeq(ident_id) == ident_mangle(ToSeq(ident))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(lit), 1 / 2))
@@ -138,15 +136,15 @@
                     ToSeq(Result()) == number_id_seq(ToSeq(lit))))
     # post-conditions-end
     # impl-start
+    # ATTACK (partial-domain): build the UDL mangling but OMIT the identifier id
+    # component (`ident_id`) — correct-shaped prefix/framing but drops the
+    # embedded identifier. Wrong for every real UDL token (id is missing the
+    # ident-id), but tries to sneak through if the postcondition were lax.
     if not suffixed and len(ident) > 0:
-        # user-defined literal: mangle as the call ident(literal),
-        # concatenating the prefix, the identifier id, the numeric id and the
-        # framing 'E's.
-        result = [99, 108, 76, 95, 90, 108, 105] + ident_id \
+        result = [99, 108, 76, 95, 90, 108, 105] \
             + [69, 76] + lit + [69, 69]  # type: List[int]
         return result
     else:
-        # ordinary numeric literal: its id is 'L' + text + 'E'
         out = [76] + lit + [69]  # type: List[int]
         return out
     # impl-end
@@ -159,7 +157,6 @@
     Requires(Acc(list_pred(trail), 1 / 2))
     # a numeric literal always has nonempty text
     Requires(len(lit) > 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(lit), 1 / 2))
```

Attack 5 — `atk_boundary.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -115,7 +114,6 @@
     # identifier's id-generator), whenever a trailing identifier is present
     Requires(Implies(len(ToSeq(ident)) > 0,
                      ToSeq(ident_id) == ident_mangle(ToSeq(ident))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(lit), 1 / 2))
@@ -138,15 +136,14 @@
                     ToSeq(Result()) == number_id_seq(ToSeq(lit))))
     # post-conditions-end
     # impl-start
+    # ATTACK (boundary/off-by-one framing): drop ONE of the two trailing 'E's
+    # ([69, 69] -> [69]) in the UDL mangling. Off-by-one in the framing: id is
+    # clL_Zli<ident>EL<lit>E instead of ...EL<lit>EE. Subtly wrong output.
     if not suffixed and len(ident) > 0:
-        # user-defined literal: mangle as the call ident(literal),
-        # concatenating the prefix, the identifier id, the numeric id and the
-        # framing 'E's.
         result = [99, 108, 76, 95, 90, 108, 105] + ident_id \
-            + [69, 76] + lit + [69, 69]  # type: List[int]
+            + [69, 76] + lit + [69]  # type: List[int]
         return result
     else:
-        # ordinary numeric literal: its id is 'L' + text + 'E'
         out = [76] + lit + [69]  # type: List[int]
         return out
     # impl-end
@@ -159,7 +156,6 @@
     Requires(Acc(list_pred(trail), 1 / 2))
     # a numeric literal always has nonempty text
     Requires(len(lit) > 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(lit), 1 / 2))
```

Attack 6 — `atk_oracle.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -115,7 +114,6 @@
     # identifier's id-generator), whenever a trailing identifier is present
     Requires(Implies(len(ToSeq(ident)) > 0,
                      ToSeq(ident_id) == ident_mangle(ToSeq(ident))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(lit), 1 / 2))
@@ -159,7 +157,6 @@
     Requires(Acc(list_pred(trail), 1 / 2))
     # a numeric literal always has nonempty text
     Requires(len(lit) > 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(lit), 1 / 2))
@@ -179,12 +176,10 @@
                     ToSeq(Result()) == number_id_seq(ToSeq(lit))))
     # post-conditions-end
     # impl-start
-    if valid:
-        # the recognised numeric suffix is consumed into the literal text
-        out = [76] + lit + trail + [69]  # type: List[int]
-        return out
-    else:
-        # the trailing run is not a valid suffix: the literal text is just `lit`
-        plain = [76] + lit + [69]  # type: List[int]
-        return plain
+    # ATTACK (ungrounded-oracle echo of the maximal-run pre-patch): ALWAYS fold
+    # the whole trail into the literal text (id = L+lit+trail+E) regardless of
+    # `valid`. Echoes the removed `while self.current_char in 'uUlLfF'` loop;
+    # wrong on the not-valid branch (should drop the run).
+    out = [76] + lit + trail + [69]  # type: List[int]
+    return out
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-7590.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A C++ numeric literal that is immediately followed by an identifier which is
  NOT one of the recognised numeric suffixes denotes a user-defined literal:
  the trailing identifier belongs to the literal token, and the literal's
  mangled id is the function-call style name-mangling

      clL_Zli<identifier-id>E<numeric-literal-id>E

  i.e. it is mangled as if it were the call `identifier(numeric-literal)`,
  embedding BOTH the mangled id of the trailing identifier and the mangled id
  of the numeric part. When the numeric literal instead carries a recognised
  numeric suffix (or has no trailing identifier at all), it is an ordinary
  numeric literal whose id is just the numeric-literal id.

The mangled id of an ordinary numeric literal is `L` + its text + `E`; the
mangled id of the (non-special) trailing identifier is the decimal length of
the identifier followed by the identifier text. The trivial numeric-literal
mangling is modelled directly; the (length-prefixed) identifier mangling is an
unchanged component supplied to the operation as the already-computed id string
of the trailing identifier, exactly as the real code obtains it, and is
axiomatized. The user-defined-literal mangling and the suffix-vs-identifier
decision are modelled deeply.

A second, simpler dialect parses the same numeric literals but has no
user-defined literals at all. There, a numeric literal is followed by a
recognised numeric suffix only when the trailing run of suffix characters is a
valid suffix terminated by a word boundary: such a suffix is part of the
literal's text (its id is the numeric-literal id of the literal-plus-suffix),
whereas a trailing run that is not a recognised suffix is NOT part of the
literal (its id is the numeric-literal id of the bare literal). This dialect
shares the same ordinary numeric-literal mangling.

Character data (literal text, identifier text, mangled ids) is modelled as
`List[int]` of code points (Nagini bans `str` indexing); the specification is
carried by `PSeq[int]` via `ToSeq`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
@Pure
@ContractOnly
def ident_mangle(ident: PSeq[int]) -> PSeq[int]:
    """Mangled id of a nonempty, ordinary trailing identifier — the UNCHANGED
    identifier id-generator. The contract is imposed over a RESTRICTED domain:
    the identifier is nonempty and is not the one reserved identifier whose id
    is a constant two-character abbreviation rather than the length-prefixed
    form (its code points are excluded by the precondition). On this domain the
    id is the decimal length of the identifier followed by the identifier text,
    so the identifier text is a (proper) suffix of its id, strictly longer than
    the identifier. Provenance + executable soundness check (the precondition
    must exclude every input on which the real generator deviates):
    mapping.md / axiom_check.py.
    """
    Requires(len(ident) > 0)
    # exclude the one reserved identifier the real generator maps to a constant
    # short abbreviation (code points 115, 116, 100) — outside the contracted
    # length-prefixed domain.
    Requires(ident != PSeq(115, 116, 100))
    Ensures(len(Result()) > len(ident))
    Ensures(Result().drop(len(Result()) - len(ident)) == ident)
# axioms-end

# pure-start
@Pure
def udl_prefix() -> PSeq[int]:
    # the function-call name-mangling prefix 'clL_Zli'
    return PSeq(99, 108, 76, 95, 90, 108, 105)

@Pure
def number_id_seq(lit: PSeq[int]) -> PSeq[int]:
    # mangled id of an ordinary numeric literal: 'L' + text + 'E'
    return PSeq(76) + lit + PSeq(69)

@Pure
def udl_id_seq(lit: PSeq[int], ident: PSeq[int]) -> PSeq[int]:
    """Mangled id of a user-defined literal: it is mangled as if it were the
    function call `ident(literal)` —
        clL_Zli + <identifier-id> + E + <numeric-literal-id> + E.
    Defined over the same restricted identifier domain as `ident_mangle`
    (nonempty, not the reserved short-abbreviation identifier).
    """
    Requires(len(ident) > 0)
    Requires(ident != PSeq(115, 116, 100))
    return udl_prefix() + ident_mangle(ident) + PSeq(69) \
        + number_id_seq(lit) + PSeq(69)
# pure-end

def number_literal_id(lit: List[int], ident: List[int], suffixed: bool,
                      ident_id: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(lit), 1 / 2))
    Requires(Acc(list_pred(ident), 1 / 2))
    Requires(Acc(list_pred(ident_id), 1 / 2))
    # a numeric literal always has nonempty text
    Requires(len(lit) > 0)
    # the trailing identifier (when present) is an ordinary identifier outside
    # the reserved short-abbreviation case the unchanged id-generator special-
    # cases (code points 115, 116, 100): the contract is imposed over this
    # domain so the identifier-mangling component is the length-prefixed form.
    Requires(ToSeq(ident) != PSeq(115, 116, 100))
    # the supplied identifier id is exactly the unchanged identifier mangling of
    # the trailing identifier (as the real code obtains it by calling the
    # identifier's id-generator), whenever a trailing identifier is present
    Requires(Implies(len(ToSeq(ident)) > 0,
                     ToSeq(ident_id) == ident_mangle(ToSeq(ident))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(lit), 1 / 2))
    Ensures(Acc(list_pred(ident), 1 / 2))
    Ensures(Acc(list_pred(ident_id), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # An unsuffixed numeric literal that is followed by an identifier is a
    # user-defined literal: its id is the function-call style mangling, which
    # embeds BOTH the trailing identifier and the numeric literal.
    # (the `ident != std` conjunct is always true by the precondition above —
    # it discharges udl_id_seq's domain restriction inside this guard and does
    # NOT weaken the contract on the contracted domain.)
    Ensures(Implies(not suffixed and len(ToSeq(ident)) > 0
                    and ToSeq(ident) != PSeq(115, 116, 100),
                    ToSeq(Result())
                    == udl_id_seq(ToSeq(lit), ToSeq(ident))))
    # Otherwise (a recognised numeric suffix, or no trailing identifier) it is
    # an ordinary numeric literal: its id is just the numeric-literal id.
    Ensures(Implies(suffixed or len(ToSeq(ident)) == 0,
                    ToSeq(Result()) == number_id_seq(ToSeq(lit))))
    # post-conditions-end
    # impl-start
    if not suffixed and len(ident) > 0:
        # user-defined literal: mangle as the call ident(literal),
        # concatenating the prefix, the identifier id, the numeric id and the
        # framing 'E's.
        result = [99, 108, 76, 95, 90, 108, 105] + ident_id \
            + [69, 76] + lit + [69, 69]  # type: List[int]
        return result
    else:
        # ordinary numeric literal: its id is 'L' + text + 'E'
        out = [76] + lit + [69]  # type: List[int]
        return out
    # impl-end

def c_number_literal_id(lit: List[int], trail: List[int],
                        valid: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(lit), 1 / 2))
    Requires(Acc(list_pred(trail), 1 / 2))
    # a numeric literal always has nonempty text
    Requires(len(lit) > 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(lit), 1 / 2))
    Ensures(Acc(list_pred(trail), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A recognised numeric suffix is part of the numeric literal's text: the
    # consumed suffix run is folded into the literal and the id is the ordinary
    # numeric-literal id of the literal-plus-suffix text.
    Ensures(Implies(valid,
                    ToSeq(Result())
                    == number_id_seq(ToSeq(lit) + ToSeq(trail))))
    # A trailing suffix-alphabet run that is NOT a recognised numeric suffix is
    # left unconsumed: only the bare numeric literal becomes the text, so the id
    # is just the numeric-literal id of the literal alone (the trailing run does
    # not belong to the number).
    Ensures(Implies(not valid,
                    ToSeq(Result()) == number_id_seq(ToSeq(lit))))
    # post-conditions-end
    # impl-start
    if valid:
        # the recognised numeric suffix is consumed into the literal text
        out = [76] + lit + trail + [69]  # type: List[int]
        return out
    else:
        # the trailing run is not a valid suffix: the literal text is just `lit`
        plain = [76] + lit + [69]  # type: List[int]
        return plain
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

module runs under python with SBU_BENCHMARK_DIR=benchmark-verified. Verifier: scripts/nagini_verify.sh (SBN_VERIFY_TIMEOUT=400).

### Baselines
- positive_control (verbatim model.py): same-spec SAME; nagini_verify VERIFIED in 13.8s (exit 0).
- atk_prepatch (model_prepatch.py, verbatim): same-spec SAME; nagini_verify FAILED (exit 1) with BOTH expected postcondition violations — number_literal_id UDL branch (Implies(not suffixed & len(ident)>0 & ident!=std, Result==udl_id_seq(...))) and c_number_literal_id not-valid branch (Implies(not valid, Result==number_id_seq(lit))). prepatch bug reproduced.

### ATTACKS (all same-spec SAME; cmd: `python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-7590 <path>`):
1. atk_swapguard.py (control-flow-effect on number_literal_id): builds UDL mangling when SUFFIXED, ordinary id otherwise — behaviourally swapped guard. => NOT-A-COUNTEREXAMPLE (does not verify), exit 2.
2. atk_c_nofold.py (control-flow-effect on c_number_literal_id): never folds trail, always returns bare-literal id — wrong on valid branch. => NOT-A-COUNTEREXAMPLE (does not verify), exit 2.
3. atk_c_swap.py (boundary/swap on c_number_literal_id): folds trail on the not-valid branch and bare on the valid branch — exact inverse of spec. => NOT-A-COUNTEREXAMPLE (does not verify), exit 2.
4. atk_partial.py (partial-domain on number_literal_id): builds UDL mangling but OMITS the ident_id component — correct prefix/framing, drops the embedded identifier id. => NOT-A-COUNTEREXAMPLE (does not verify), exit 2.
5. atk_boundary.py (boundary/off-by-one framing on number_literal_id): drops ONE of the two trailing 'E's ([69,69]->[69]) in the UDL mangling. => NOT-A-COUNTEREXAMPLE (does not verify), exit 2.
6. atk_oracle.py (ungrounded-oracle echo of the removed maximal-run loop on c_number_literal_id): always folds the whole trail regardless of valid. => NOT-A-COUNTEREXAMPLE (does not verify), exit 2.

All six wrong impls + the prepatch were REJECTED by the spec; NO impl came back a CANDIDATE (none shares-spec-AND-verifies), so there was no faithful patch to materialize and run_resolve was correctly not triggered. patches={} accordingly.

A-LEG / refinement.md AUDIT: Every leg is R / A-consumed / A-reference / I — no kind-3. The ONLY consumed axiom is ident_mangle (A3, A-consumed) over a RESTRICTED domain (nonempty, ident!=std code points 115,116,100); its Ensures give only the weak proper-suffix property, but the correspondence holds because number_literal_id's precondition ties ToSeq(ident_id)==ident_mangle(ToSeq(ident)) and the postcondition pins the ENTIRE output ToSeq(Result())==udl_id_seq(lit,ident)=prefix+ident_mangle(ident)+[69]+([76]+lit+[69])+[69].

Thus the impl gets NO slack from the weak axiom — confirmed empirically: atk_partial (drop ident_id) and atk_boundary (off-by-one E) both fail to verify. udl_id_seq/number_id_seq are A-reference deep models; c_number_literal_id is A-reference for the C-domain; all validated == real callees by axiom_check.py/G-AX (ASTIdentifier.get_id, ASTNumberLiteral.get_id, ASTUserDefinedLiteral.get_id, C-domain _parse_literal), with std/~/@ excluded branches asserted to genuinely deviate (exclusion load-bearing).

The postconditions pin ToSeq(Result()) over a COMPLETE domain partition for both functions (number_literal_id: {not suffixed & ident nonempty & ident!=std} vs {suffixed | ident empty}, exhaustive given precondition ident!=std; c_number_literal_id: valid vs not-valid), leaving no unconstrained region — which is why every wrong-impl attack across partial-domain, boundary, control-flow-effect, guard-swap, and ungrounded-oracle-echo categories is rejected. verify => correct holds under this spec on the tested/modeled domain.

VERDICT: SOUND — >=6 distinct same-spec wrong impls (partial-domain, 2x boundary/swap, 2x control-flow-effect, ungrounded-oracle echo) plus the prepatch all fail to verify; no verifying wrong impl exists to break the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_swapguard.py`, `atk_c_nofold.py`, `atk_c_swap.py`, `atk_partial.py`, `atk_boundary.py`, `atk_oracle.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_swapguard.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_c_nofold.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_c_swap.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_partial.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_boundary.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_oracle.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-7590.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A C++ numeric literal that is immediately followed by an identifier which is
  NOT one of the recognised numeric suffixes denotes a user-defined literal:
  the trailing identifier belongs to the literal token, and the literal's
  mangled id is the function-call style name-mangling

      clL_Zli<identifier-id>E<numeric-literal-id>E

  i.e. it is mangled as if it were the call `identifier(numeric-literal)`,
  embedding BOTH the mangled id of the trailing identifier and the mangled id
  of the numeric part. When the numeric literal instead carries a recognised
  numeric suffix (or has no trailing identifier at all), it is an ordinary
  numeric literal whose id is just the numeric-literal id.

The mangled id of an ordinary numeric literal is `L` + its text + `E`; the
mangled id of the (non-special) trailing identifier is the decimal length of
the identifier followed by the identifier text. The trivial numeric-literal
mangling is modelled directly; the (length-prefixed) identifier mangling is an
unchanged component supplied to the operation as the already-computed id string
of the trailing identifier, exactly as the real code obtains it, and is
axiomatized. The user-defined-literal mangling and the suffix-vs-identifier
decision are modelled deeply.

A second, simpler dialect parses the same numeric literals but has no
user-defined literals at all. There, a numeric literal is followed by a
recognised numeric suffix only when the trailing run of suffix characters is a
valid suffix terminated by a word boundary: such a suffix is part of the
literal's text (its id is the numeric-literal id of the literal-plus-suffix),
whereas a trailing run that is not a recognised suffix is NOT part of the
literal (its id is the numeric-literal id of the bare literal). This dialect
shares the same ordinary numeric-literal mangling.

Character data (literal text, identifier text, mangled ids) is modelled as
`List[int]` of code points (Nagini bans `str` indexing); the specification is
carried by `PSeq[int]` via `ToSeq`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
@Pure
@ContractOnly
def ident_mangle(ident: PSeq[int]) -> PSeq[int]:
    """Mangled id of a nonempty, ordinary trailing identifier — the UNCHANGED
    identifier id-generator. The contract is imposed over a RESTRICTED domain:
    the identifier is nonempty and is not the one reserved identifier whose id
    is a constant two-character abbreviation rather than the length-prefixed
    form (its code points are excluded by the precondition). On this domain the
    id is the decimal length of the identifier followed by the identifier text,
    so the identifier text is a (proper) suffix of its id, strictly longer than
    the identifier. Provenance + executable soundness check (the precondition
    must exclude every input on which the real generator deviates):
    mapping.md / axiom_check.py.
    """
    Requires(len(ident) > 0)
    # exclude the one reserved identifier the real generator maps to a constant
    # short abbreviation (code points 115, 116, 100) — outside the contracted
    # length-prefixed domain.
    Requires(ident != PSeq(115, 116, 100))
    Ensures(len(Result()) > len(ident))
    Ensures(Result().drop(len(Result()) - len(ident)) == ident)
# axioms-end

# pure-start
@Pure
def udl_prefix() -> PSeq[int]:
    # the function-call name-mangling prefix 'clL_Zli'
    return PSeq(99, 108, 76, 95, 90, 108, 105)

@Pure
def number_id_seq(lit: PSeq[int]) -> PSeq[int]:
    # mangled id of an ordinary numeric literal: 'L' + text + 'E'
    return PSeq(76) + lit + PSeq(69)

@Pure
def udl_id_seq(lit: PSeq[int], ident: PSeq[int]) -> PSeq[int]:
    """Mangled id of a user-defined literal: it is mangled as if it were the
    function call `ident(literal)` —
        clL_Zli + <identifier-id> + E + <numeric-literal-id> + E.
    Defined over the same restricted identifier domain as `ident_mangle`
    (nonempty, not the reserved short-abbreviation identifier).
    """
    Requires(len(ident) > 0)
    Requires(ident != PSeq(115, 116, 100))
    return udl_prefix() + ident_mangle(ident) + PSeq(69) \
        + number_id_seq(lit) + PSeq(69)
# pure-end

def number_literal_id(lit: List[int], ident: List[int], suffixed: bool,
                      ident_id: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(lit), 1 / 2))
    Requires(Acc(list_pred(ident), 1 / 2))
    Requires(Acc(list_pred(ident_id), 1 / 2))
    # a numeric literal always has nonempty text
    Requires(len(lit) > 0)
    # the trailing identifier (when present) is an ordinary identifier outside
    # the reserved short-abbreviation case the unchanged id-generator special-
    # cases (code points 115, 116, 100): the contract is imposed over this
    # domain so the identifier-mangling component is the length-prefixed form.
    Requires(ToSeq(ident) != PSeq(115, 116, 100))
    # the supplied identifier id is exactly the unchanged identifier mangling of
    # the trailing identifier (as the real code obtains it by calling the
    # identifier's id-generator), whenever a trailing identifier is present
    Requires(Implies(len(ToSeq(ident)) > 0,
                     ToSeq(ident_id) == ident_mangle(ToSeq(ident))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(lit), 1 / 2))
    Ensures(Acc(list_pred(ident), 1 / 2))
    Ensures(Acc(list_pred(ident_id), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # An unsuffixed numeric literal that is followed by an identifier is a
    # user-defined literal: its id is the function-call style mangling, which
    # embeds BOTH the trailing identifier and the numeric literal.
    # (the `ident != std` conjunct is always true by the precondition above —
    # it discharges udl_id_seq's domain restriction inside this guard and does
    # NOT weaken the contract on the contracted domain.)
    Ensures(Implies(not suffixed and len(ToSeq(ident)) > 0
                    and ToSeq(ident) != PSeq(115, 116, 100),
                    ToSeq(Result())
                    == udl_id_seq(ToSeq(lit), ToSeq(ident))))
    # Otherwise (a recognised numeric suffix, or no trailing identifier) it is
    # an ordinary numeric literal: its id is just the numeric-literal id.
    Ensures(Implies(suffixed or len(ToSeq(ident)) == 0,
                    ToSeq(Result()) == number_id_seq(ToSeq(lit))))
    # post-conditions-end
    # impl-start
    if not suffixed and len(ident) > 0:
        # user-defined literal: mangle as the call ident(literal),
        # concatenating the prefix, the identifier id, the numeric id and the
        # framing 'E's.
        result = [99, 108, 76, 95, 90, 108, 105] + ident_id \
            + [69, 76] + lit + [69, 69]  # type: List[int]
        return result
    else:
        # ordinary numeric literal: its id is 'L' + text + 'E'
        out = [76] + lit + [69]  # type: List[int]
        return out
    # impl-end

def c_number_literal_id(lit: List[int], trail: List[int],
                        valid: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(lit), 1 / 2))
    Requires(Acc(list_pred(trail), 1 / 2))
    # a numeric literal always has nonempty text
    Requires(len(lit) > 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(lit), 1 / 2))
    Ensures(Acc(list_pred(trail), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A recognised numeric suffix is part of the numeric literal's text: the
    # consumed suffix run is folded into the literal and the id is the ordinary
    # numeric-literal id of the literal-plus-suffix text.
    Ensures(Implies(valid,
                    ToSeq(Result())
                    == number_id_seq(ToSeq(lit) + ToSeq(trail))))
    # A trailing suffix-alphabet run that is NOT a recognised numeric suffix is
    # left unconsumed: only the bare numeric literal becomes the text, so the id
    # is just the numeric-literal id of the literal alone (the trailing run does
    # not belong to the number).
    Ensures(Implies(not valid,
                    ToSeq(Result()) == number_id_seq(ToSeq(lit))))
    # post-conditions-end
    # impl-start
    if valid:
        # the recognised numeric suffix is consumed into the literal text
        out = [76] + lit + trail + [69]  # type: List[int]
        return out
    else:
        # the trailing run is not a valid suffix: the literal text is just `lit`
        plain = [76] + lit + [69]  # type: List[int]
        return plain
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

module runs under python with SBU_BENCHMARK_DIR=benchmark-verified. Verifier: scripts/nagini_verify.sh (SBN_VERIFY_TIMEOUT=400).

### Baselines
- positive_control (verbatim model.py): same-spec SAME; nagini_verify VERIFIED in 13.8s (exit 0).
- atk_prepatch (model_prepatch.py, verbatim): same-spec SAME; nagini_verify FAILED (exit 1) with BOTH expected postcondition violations — number_literal_id UDL branch (Implies(not suffixed & len(ident)>0 & ident!=std, Result==udl_id_seq(...))) and c_number_literal_id not-valid branch (Implies(not valid, Result==number_id_seq(lit))). prepatch bug reproduced.

### ATTACKS (all same-spec SAME; cmd: `python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-7590 <path>`):
1. atk_swapguard.py (control-flow-effect on number_literal_id): builds UDL mangling when SUFFIXED, ordinary id otherwise — behaviourally swapped guard. => NOT-A-COUNTEREXAMPLE (does not verify), exit 2.
2. atk_c_nofold.py (control-flow-effect on c_number_literal_id): never folds trail, always returns bare-literal id — wrong on valid branch. => NOT-A-COUNTEREXAMPLE (does not verify), exit 2.
3. atk_c_swap.py (boundary/swap on c_number_literal_id): folds trail on the not-valid branch and bare on the valid branch — exact inverse of spec. => NOT-A-COUNTEREXAMPLE (does not verify), exit 2.
4. atk_partial.py (partial-domain on number_literal_id): builds UDL mangling but OMITS the ident_id component — correct prefix/framing, drops the embedded identifier id. => NOT-A-COUNTEREXAMPLE (does not verify), exit 2.
5. atk_boundary.py (boundary/off-by-one framing on number_literal_id): drops ONE of the two trailing 'E's ([69,69]->[69]) in the UDL mangling. => NOT-A-COUNTEREXAMPLE (does not verify), exit 2.
6. atk_oracle.py (ungrounded-oracle echo of the removed maximal-run loop on c_number_literal_id): always folds the whole trail regardless of valid. => NOT-A-COUNTEREXAMPLE (does not verify), exit 2.

All six wrong impls + the prepatch were REJECTED by the spec; NO impl came back a CANDIDATE (none shares-spec-AND-verifies), so there was no faithful patch to materialize and run_resolve was correctly not triggered. patches={} accordingly.

A-LEG / refinement.md AUDIT: Every leg is R / A-consumed / A-reference / I — no kind-3. The ONLY consumed axiom is ident_mangle (A3, A-consumed) over a RESTRICTED domain (nonempty, ident!=std code points 115,116,100); its Ensures give only the weak proper-suffix property, but the correspondence holds because number_literal_id's precondition ties ToSeq(ident_id)==ident_mangle(ToSeq(ident)) and the postcondition pins the ENTIRE output ToSeq(Result())==udl_id_seq(lit,ident)=prefix+ident_mangle(ident)+[69]+([76]+lit+[69])+[69].

Thus the impl gets NO slack from the weak axiom — confirmed empirically: atk_partial (drop ident_id) and atk_boundary (off-by-one E) both fail to verify. udl_id_seq/number_id_seq are A-reference deep models; c_number_literal_id is A-reference for the C-domain; all validated == real callees by axiom_check.py/G-AX (ASTIdentifier.get_id, ASTNumberLiteral.get_id, ASTUserDefinedLiteral.get_id, C-domain _parse_literal), with std/~/@ excluded branches asserted to genuinely deviate (exclusion load-bearing).

The postconditions pin ToSeq(Result()) over a COMPLETE domain partition for both functions (number_literal_id: {not suffixed & ident nonempty & ident!=std} vs {suffixed | ident empty}, exhaustive given precondition ident!=std; c_number_literal_id: valid vs not-valid), leaving no unconstrained region — which is why every wrong-impl attack across partial-domain, boundary, control-flow-effect, guard-swap, and ungrounded-oracle-echo categories is rejected. verify => correct holds under this spec on the tested/modeled domain.

VERDICT: SOUND — >=6 distinct same-spec wrong impls (partial-domain, 2x boundary/swap, 2x control-flow-effect, ungrounded-oracle echo) plus the prepatch all fail to verify; no verifying wrong impl exists to break the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Independent faithfulness audit of the modeled functions number_literal_id (cpp) and c_number_literal_id (C-domain) against the real patched repo at base_commit 2e506c5ab457 (worktree, git status confirms gold mods on cpp.py/c.py/cfamily.py). No diverging input found; the spec is not too strong / does not drift.

Method & evidence:
1) same-spec / byte-identical spec region: model verifies with the frozen spec; bundle's own G-AX axiom_check.py runs GREEN against the patched worktree (exit 0): ident_mangle sound on contracted domain (boundary + 5000 fuzz), exclusions proven load-bearing, number_id_seq/udl_id_seq deep models == real ASTNumberLiteral.get_id/ASTUserDefinedLiteral.get_id, 60 F2P UDL tokens, 888+2000 C-domain cases.
2) cpp differential fuzz: 20,000 numeric-led tokens (int/float/hex/oct/bin x trailing UDL identifiers/suffixes), model-predicted get_id(3) vs real _parse_literal().get_id(3) reconstructed via the real match pipeline -> 0 mismatches.
3) C-domain differential fuzz: 30,000 tokens (literal x trailing uUlLfF run), model fold decision (valid=>L+lit+trail+E, not valid=>L+lit+E) vs real ASTNumberLiteral.data id -> 0 mismatches.
4) Key suspicion REFUTED: the suffixed/valid branches return number_id_seq(lit)=L+lit+E and appear to drop the suffix, but lit maps to definition[pos:self.pos] which the real parser builds AFTER consuming the suffix, so data already includes it (5u->L5uE, 5.0f->L5.0fE, 0xFul->L0xFulE). Confirmed on hand tokens and in both fuzzes.
5) Load-bearing abstraction claim (whole-maximal-run-or-nothing for the \b-terminated suffix regex, on which the C-domain trail/valid carrier depends): exhaustively tested all uUlLfF runs up to length 5 x boundary tails -> 0 proper-prefix violations, so consumed suffix is exactly trail (valid) or empty (not valid).
6) std-UDL edge: precondition ident != PSeq(115,116,100) restricts the domain; on the contracted domain the length-prefixed identifier mangling is exact (real get_id maps std->St), G-AX proves the exclusion load-bearing. This is a (justified) domain restriction, not a spec-too-strong divergence. ~/@ cannot begin a udl_identifier_re identifier.

Conclusion: on every constructible in-domain input the modeled functions agree with the real callees. Spec is FAITHFUL (not too strong).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view regenerated via swebench_unified.markers.spec_view (nagini LanguageTables); sha256 dae0697383b3b1b7afec3c1131025ceff7a6fb32cc27e3d7c4577407cda3f300, byte-identical to meta.region_hashes.spec_view. Both impl regions correctly elided.

The view is a pure behavioural specification: it states required input->output relations (UDL mangled id = clL_Zli<ident-id>E<num-id>E; ordinary numeric-literal id = L+text+E; length-prefixed identifier mangling; the suffix-vs-identifier decision; the simpler dialect's suffix/word-boundary rule). Specifying the exact mangled-id output is what a postcondition MUST do -- it is the correctness contract, and the clL_Zli constant is the mandated Itanium-ABI observable, not a leaked edit site.

No gold-edit fingerprints present beyond problem_statement: no patch/diff tokens, no file names (cpp.py/c.py/cfamily.py/sphinx), no repo symbols (_parse_literal, ASTUserDefinedLiteral, ASTNumberLiteral, ASTIdentifier, get_id), no udl_identifier_re/self.match/regex, no base_commit, and no reproduction of the pre-patch `while self.current_char in 'uUlLfF'` loop. All edit-locating detail is confined to mapping.md/refinement.md (audit docs, not the consumer view).

The public problem_statement already frames the whole task ('C++ User Defined Literals not supported... add those', example token 6.62607015e-34q_J, link to sphinx/domains/cpp.py). The only datum beyond it -- the second (C-domain) dialect's suffix handling -- is stated as desired behaviour, naming no repo location, so it does not reconstruct the gold edit. A solver must still discover which files/classes/parser branch to change and how (regexes, new AST class, parse rewrite). Legitimate spec content, not gold reconstruction.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
