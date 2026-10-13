# P2 adversarial audit — psf__requests-5414

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -146,6 +146,6 @@
     # impl-start
     if not host_is_ascii:
         encode_label(encodable)
-    elif is_invalid_leading(host[0]):
+    elif host[0] == 42:
         raise InvalidLocator()
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -146,6 +146,6 @@
     # impl-start
     if not host_is_ascii:
         encode_label(encodable)
-    elif is_invalid_leading(host[0]):
+    elif host[0] == 46:
         raise InvalidLocator()
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -146,6 +146,4 @@
     # impl-start
     if not host_is_ascii:
         encode_label(encodable)
-    elif is_invalid_leading(host[0]):
-        raise InvalidLocator()
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -146,6 +146,6 @@
     # impl-start
     if not host_is_ascii:
         encode_label(encodable)
-    elif is_invalid_leading(host[0]):
+    else:
         raise InvalidLocator()
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -146,6 +146,6 @@
     # impl-start
     if not host_is_ascii:
         encode_label(encodable)
-    elif is_invalid_leading(host[0]):
+    elif host[0] == 42 or host[0] == 46 or host[0] == 45:
         raise InvalidLocator()
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -146,6 +146,6 @@
     # impl-start
     if not host_is_ascii:
         encode_label(encodable)
-    elif is_invalid_leading(host[0]):
-        raise InvalidLocator()
+    else:
+        encode_label(encodable)
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -144,8 +144,6 @@
                  or (not host_is_ascii and encodable is False)))
     # post-conditions-end
     # impl-start
-    if not host_is_ascii:
-        encode_label(encodable)
-    elif is_invalid_leading(host[0]):
+    if host_is_ascii and is_invalid_leading(host[0]):
         raise InvalidLocator()
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -144,8 +144,5 @@
                  or (not host_is_ascii and encodable is False)))
     # post-conditions-end
     # impl-start
-    if not host_is_ascii:
-        encode_label(encodable)
-    elif is_invalid_leading(host[0]):
-        raise InvalidLocator()
+    screen_host(host, host_is_ascii, encodable)
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -144,8 +144,6 @@
                  or (not host_is_ascii and encodable is False)))
     # post-conditions-end
     # impl-start
-    if not host_is_ascii:
-        encode_label(encodable)
-    elif is_invalid_leading(host[0]):
-        raise InvalidLocator()
+    while True:
+        pass
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -146,6 +146,6 @@
     # impl-start
     if not host_is_ascii:
         encode_label(encodable)
-    elif is_invalid_leading(host[0]):
+    elif is_invalid_leading(host[0]) and encodable:
         raise InvalidLocator()
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for psf__requests-5414.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Before a host label drawn from a locator is accepted, it is screened for a
  leading code point that cannot begin a valid label. A non-empty host whose
  first code point is code point 42 or code point 46 names an empty or otherwise
  ill-formed first label and must be reported as a rejection rather than allowed
  to return normally.

  This screen applies only to a host that is already expressible in the
  restricted (ASCII) form. A host that is NOT in that restricted form is handed
  instead to the unchanged internationalised-label encoder, whose only
  observable datum is whether the host carries an encodable label; that encoder
  reports a rejection (the SAME out-of-band signal) exactly when the label is
  not encodable, and otherwise returns normally. The leading-code-point screen
  is NOT applied to a non-restricted host.

  The behaviour pinned here is therefore, for a non-empty host:

    * restricted (ASCII) host: rejected  iff  the first code point is 42 or
                                              46; returns normally otherwise.
    * non-restricted host:     rejected  iff  the encoder cannot encode the
                                              label; returns normally otherwise.

The host is modelled as a ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing). Whether the host is in the restricted (ASCII) form, and
whether a non-restricted label is encodable, are the two single observable bits
of the unchanged callees (the predicate deciding the restricted form, and the
internationalised-label encoder); the latter is axiomatized as a contract-only
function. The rejection is a user-defined exception class (a builtin exception
in an ``Exsures`` crashes the Nagini translator).

The screen is a bounded, straight-line computation and MUST terminate (a
total-correctness obligation, carried as ``MustTerminate`` in the
precondition). Nagini is a partial-correctness verifier by default, so without
this obligation a non-terminating implementation (e.g. bare self-recursion or
an endless loop) satisfies every ``Ensures``/``Exsures`` vacuously; the real
host screen always answers (returns normally or signals the rejection) before
the surrounding preparation continues.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class InvalidLocator(Exception):
    """The rejection signalled when the host carries an invalid label. A
    user-defined stand-in for the locator error the desired behaviour requires
    (a builtin exception in an ``Exsures`` crashes the Nagini translator;
    mapping.md §2)."""
    pass

# axioms-start
@ContractOnly
def encode_label(encodable: bool) -> None:
    """The unchanged internationalised-label encoder, the callee a non-ASCII
    host is handed to instead of the leading-code-point screen. Its only
    observable datum is ``encodable``: whether the host's label can be encoded.
    It returns normally exactly when the label is encodable and signals a
    rejection (the same out-of-band rejection) exactly when it is not.
    Provenance + executable soundness check: mapping.md / axiom_check.py."""
    # pre-conditions-start
    # The real encoder is a bounded call that always answers (returns the
    # encoded host or raises; axiom_check.py shows it is total over those two
    # channels). The strictly smaller measure (1 < 2) lets the contracted
    # caller holding MustTerminate(2) invoke it without leaking its own
    # obligation.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # Normal completion is reachable EXACTLY on the encodable case.
    Ensures(encodable is True)
    # Rejection is signalled out of band EXACTLY on the not-encodable case.
    Exsures(InvalidLocator, encodable is False)
    # post-conditions-end
# axioms-end

# pure-start
# NOTE for auditors: the contract below pins the COMPLETE observable relation
# on the modeled domain — for every admissible input it determines whether
# the screen returns normally or signals the rejection, and the @Pure
# predicate here is TRANSPARENT (its body IS the whole membership test), not
# an opaque answer-key. Consequently any same-spec implementation that
# verifies is behaviourally EQUAL to the pinned behaviour on every admissible
# input: a restructured or branch-reordered equivalent (or one that tests the
# pure predicate directly) is a POSITIVE CONTROL, never a spec-too-weak
# counterexample — it belongs in positive_control, not in the attack list. A
# valid weakness attack must DIFFER from the pinned relation on some
# admissible input, and the contract then rejects it.
@Pure
def is_invalid_leading(c: int) -> bool:
    """A single leading code point cannot begin a valid label iff it is
    code point 42 or code point 46."""
    return c == 42 or c == 46
# pure-end

def screen_host(host: List[int], host_is_ascii: bool, encodable: bool) -> None:
    # pre-conditions-start
    # ``host`` is only READ (fractional permission, directive 5). The host is
    # non-empty (a host with no label is decided earlier, out of this slice).
    # ``host_is_ascii`` / ``encodable`` are the abstract world-state data of the
    # two unchanged callees: whether the host is in the restricted (ASCII) form,
    # and (when it is not) whether its label is encodable.
    Requires(Acc(list_pred(host), 1 / 2))
    Requires(len(host) > 0)
    # TERMINATION: the screen must actually ANSWER (return normally or signal
    # the rejection) — it is a bounded, straight-line decision over one host.
    # Nagini is a partial-correctness verifier by default, so without this
    # obligation a non-terminating implementation (bare self-recursion, an
    # endless loop) satisfies every Ensures/Exsures vacuously; the real host
    # screen always answers before the surrounding preparation continues.
    # The measure (2) strictly exceeds the encoder axiom's (1), so the impl
    # may call encode_label but may NOT re-invoke this routine itself — the
    # postcondition cannot be discharged by echoing this routine's own
    # contract.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The host is read-only: returned untouched at the same fractional
    # permission (so the screen cannot have mutated it, directive 5).
    Ensures(Acc(list_pred(host), 1 / 2))
    # Normal completion is reachable EXACTLY in two disjoint cases:
    #   (a) a restricted (ASCII) host whose first code point is neither 42
    #       nor 46;
    #   (b) a non-restricted host whose label is encodable.
    # In particular, a restricted (ASCII) host whose first code point is 46 can
    # NEVER return normally.
    Ensures(len(host) > 0)
    Ensures(Implies(host_is_ascii, len(host) > 0 and not is_invalid_leading(host[0])))
    Ensures(Implies(not host_is_ascii, encodable is True))
    # Rejection is signalled EXACTLY when a restricted (ASCII) host's first code
    # point is 42 or 46, OR a non-restricted host's label is not encodable. The
    # read-only host is re-established on the rejecting path as well.
    Exsures(InvalidLocator,
            Acc(list_pred(host), 1 / 2)
            and len(host) > 0
            and ((host_is_ascii and is_invalid_leading(host[0]))
                 or (not host_is_ascii and encodable is False)))
    # post-conditions-end
    # impl-start
    if not host_is_ascii:
        encode_label(encodable)
    elif is_invalid_leading(host[0]):
        raise InvalidLocator()
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 10 distinct same-spec wrong impls built by editing ONLY the impl region of model.py (axioms/@Pure/Requires/Ensures/Exsures byte-identical); all 11 (incl. positive control) confirmed same-spec (`adversary same-spec` exit 0). Positive control (gold impl verbatim) VERIFIES (nagini_verify.sh exit 0, 15.5s). Zero verifying wrong impls => no CANDIDATE => no faithful patch needed to be materialized/resolve-run (the resolve step triggers only for a verifying candidate). Attack classes + observed weakness result:
- atk_1 PREPATCH BUG (reject only 42/'*'): FAILED verify. Direct verify pins the exact clause: 'Postcondition of screen_host might not hold. Assertion Implies(host_is_ascii, ...not is_invalid_leading(host[0]))' — spec senses the '.'(46) widening (G-DIFF). PREPATCH REPRODUCED.
- atk_2 reject only 46/'.': FAILED (misses '*' case).
- atk_3 reject nothing on ASCII branch: FAILED (partial-domain / control-flow).
- atk_4 reject everything on ASCII branch (else raise): FAILED (over-rejection).
- atk_5 BOUNDARY reject 42/46/45('-'): FAILED (extra rejection of 45).
- atk_6 UNGROUNDED-ORACLE ECHO (call encode_label on ASCII else-branch): FAILED.
- atk_7 PARTIAL-DOMAIN (drop non-ASCII encode_label, always return normally): FAILED.
- atk_8 CONTROL-FLOW-EFFECT bare self-recursion: FAILED 'Obligation leak check failed. Callee screen_host might not take all unsatisfied obligations' (MustTerminate(2), §A.1).
- atk_9 endless `while True`: FAILED 'Obligation leak check failed. Loop might not take all unsatisfied obligations' (MustTerminate).
- atk_10 PARTIAL-DOMAIN guard (reject ASCII-invalid only when encodable): FAILED (encodable is free on ASCII path).

A-LEG / kind audit (refinement.md + meta.json): meta has exactly one axiom kind='A-consumed' (encode_label ↔ _get_idna_encoded_host / idna.encode(uts46=True)), checked by axiom_check.py (G-AX, ran green: 7 encodable + 5 not-encodable oracle hosts + 2000 non-ASCII fuzz, total over {encodable->str, not-encodable->UnicodeError}). deep_model_references=[] (no A-reference), additional_change_sites=[] (no kind-3). Every refinement leg is R / A-consumed / I: A1 (R type List[int]<->str, non-empty via len>0), A2 (R host_is_ascii + A-consumed encode_label for the UNCHANGED IDNA branch), A3 (R + I: the operation ACTUALLY changed by the patch — startswith(u'*')->startswith((u'*',u'.')) — is modeled DIRECTLY as host[0] in {42,46} via a TRANSPARENT @Pure is_invalid_leading, NOT hidden behind an axiom).

The A-consumed axiom is genuinely consumed by screen_host's non-ASCII Ensures/Exsures (no dead axiom); its correspondence to the real callee (returns str iff encodable, raises UnicodeError->InvalidURL iff not) holds per axiom_check.py. Spec is a COMPLETE transparent relational contract over (non-empty host x host_is_ascii x encodable): Ensures+Exsures fix exactly reject-or-return for every admissible input, so any verifying same-spec impl is behaviourally equal to gold. verify => correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for psf__requests-5414.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Before a host label drawn from a locator is accepted, it is screened for a
  leading code point that cannot begin a valid label. A non-empty host whose
  first code point is code point 42 or code point 46 names an empty or otherwise
  ill-formed first label and must be reported as a rejection rather than allowed
  to return normally.

  This screen applies only to a host that is already expressible in the
  restricted (ASCII) form. A host that is NOT in that restricted form is handed
  instead to the unchanged internationalised-label encoder, whose only
  observable datum is whether the host carries an encodable label; that encoder
  reports a rejection (the SAME out-of-band signal) exactly when the label is
  not encodable, and otherwise returns normally. The leading-code-point screen
  is NOT applied to a non-restricted host.

  The behaviour pinned here is therefore, for a non-empty host:

    * restricted (ASCII) host: rejected  iff  the first code point is 42 or
                                              46; returns normally otherwise.
    * non-restricted host:     rejected  iff  the encoder cannot encode the
                                              label; returns normally otherwise.

The host is modelled as a ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing). Whether the host is in the restricted (ASCII) form, and
whether a non-restricted label is encodable, are the two single observable bits
of the unchanged callees (the predicate deciding the restricted form, and the
internationalised-label encoder); the latter is axiomatized as a contract-only
function. The rejection is a user-defined exception class (a builtin exception
in an ``Exsures`` crashes the Nagini translator).

The screen is a bounded, straight-line computation and MUST terminate (a
total-correctness obligation, carried as ``MustTerminate`` in the
precondition). Nagini is a partial-correctness verifier by default, so without
this obligation a non-terminating implementation (e.g. bare self-recursion or
an endless loop) satisfies every ``Ensures``/``Exsures`` vacuously; the real
host screen always answers (returns normally or signals the rejection) before
the surrounding preparation continues.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class InvalidLocator(Exception):
    """The rejection signalled when the host carries an invalid label. A
    user-defined stand-in for the locator error the desired behaviour requires
    (a builtin exception in an ``Exsures`` crashes the Nagini translator;
    mapping.md §2)."""
    pass

# axioms-start
@ContractOnly
def encode_label(encodable: bool) -> None:
    """The unchanged internationalised-label encoder, the callee a non-ASCII
    host is handed to instead of the leading-code-point screen. Its only
    observable datum is ``encodable``: whether the host's label can be encoded.
    It returns normally exactly when the label is encodable and signals a
    rejection (the same out-of-band rejection) exactly when it is not.
    Provenance + executable soundness check: mapping.md / axiom_check.py."""
    # pre-conditions-start
    # The real encoder is a bounded call that always answers (returns the
    # encoded host or raises; axiom_check.py shows it is total over those two
    # channels). The strictly smaller measure (1 < 2) lets the contracted
    # caller holding MustTerminate(2) invoke it without leaking its own
    # obligation.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # Normal completion is reachable EXACTLY on the encodable case.
    Ensures(encodable is True)
    # Rejection is signalled out of band EXACTLY on the not-encodable case.
    Exsures(InvalidLocator, encodable is False)
    # post-conditions-end
# axioms-end

# pure-start
# NOTE for auditors: the contract below pins the COMPLETE observable relation
# on the modeled domain — for every admissible input it determines whether
# the screen returns normally or signals the rejection, and the @Pure
# predicate here is TRANSPARENT (its body IS the whole membership test), not
# an opaque answer-key. Consequently any same-spec implementation that
# verifies is behaviourally EQUAL to the pinned behaviour on every admissible
# input: a restructured or branch-reordered equivalent (or one that tests the
# pure predicate directly) is a POSITIVE CONTROL, never a spec-too-weak
# counterexample — it belongs in positive_control, not in the attack list. A
# valid weakness attack must DIFFER from the pinned relation on some
# admissible input, and the contract then rejects it.
@Pure
def is_invalid_leading(c: int) -> bool:
    """A single leading code point cannot begin a valid label iff it is
    code point 42 or code point 46."""
    return c == 42 or c == 46
# pure-end

def screen_host(host: List[int], host_is_ascii: bool, encodable: bool) -> None:
    # pre-conditions-start
    # ``host`` is only READ (fractional permission, directive 5). The host is
    # non-empty (a host with no label is decided earlier, out of this slice).
    # ``host_is_ascii`` / ``encodable`` are the abstract world-state data of the
    # two unchanged callees: whether the host is in the restricted (ASCII) form,
    # and (when it is not) whether its label is encodable.
    Requires(Acc(list_pred(host), 1 / 2))
    Requires(len(host) > 0)
    # TERMINATION: the screen must actually ANSWER (return normally or signal
    # the rejection) — it is a bounded, straight-line decision over one host.
    # Nagini is a partial-correctness verifier by default, so without this
    # obligation a non-terminating implementation (bare self-recursion, an
    # endless loop) satisfies every Ensures/Exsures vacuously; the real host
    # screen always answers before the surrounding preparation continues.
    # The measure (2) strictly exceeds the encoder axiom's (1), so the impl
    # may call encode_label but may NOT re-invoke this routine itself — the
    # postcondition cannot be discharged by echoing this routine's own
    # contract.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The host is read-only: returned untouched at the same fractional
    # permission (so the screen cannot have mutated it, directive 5).
    Ensures(Acc(list_pred(host), 1 / 2))
    # Normal completion is reachable EXACTLY in two disjoint cases:
    #   (a) a restricted (ASCII) host whose first code point is neither 42
    #       nor 46;
    #   (b) a non-restricted host whose label is encodable.
    # In particular, a restricted (ASCII) host whose first code point is 46 can
    # NEVER return normally.
    Ensures(len(host) > 0)
    Ensures(Implies(host_is_ascii, len(host) > 0 and not is_invalid_leading(host[0])))
    Ensures(Implies(not host_is_ascii, encodable is True))
    # Rejection is signalled EXACTLY when a restricted (ASCII) host's first code
    # point is 42 or 46, OR a non-restricted host's label is not encodable. The
    # read-only host is re-established on the rejecting path as well.
    Exsures(InvalidLocator,
            Acc(list_pred(host), 1 / 2)
            and len(host) > 0
            and ((host_is_ascii and is_invalid_leading(host[0]))
                 or (not host_is_ascii and encodable is False)))
    # post-conditions-end
    # impl-start
    if not host_is_ascii:
        encode_label(encodable)
    elif is_invalid_leading(host[0]):
        raise InvalidLocator()
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 10 distinct same-spec wrong impls built by editing ONLY the impl region of model.py (axioms/@Pure/Requires/Ensures/Exsures byte-identical); all 11 (incl. positive control) confirmed same-spec (`adversary same-spec` exit 0). Positive control (gold impl verbatim) VERIFIES (nagini_verify.sh exit 0, 15.5s). Zero verifying wrong impls => no CANDIDATE => no faithful patch needed to be materialized/resolve-run (the resolve step triggers only for a verifying candidate). Attack classes + observed weakness result:
- atk_1 PREPATCH BUG (reject only 42/'*'): FAILED verify. Direct verify pins the exact clause: 'Postcondition of screen_host might not hold. Assertion Implies(host_is_ascii, ...not is_invalid_leading(host[0]))' — spec senses the '.'(46) widening (G-DIFF). PREPATCH REPRODUCED.
- atk_2 reject only 46/'.': FAILED (misses '*' case).
- atk_3 reject nothing on ASCII branch: FAILED (partial-domain / control-flow).
- atk_4 reject everything on ASCII branch (else raise): FAILED (over-rejection).
- atk_5 BOUNDARY reject 42/46/45('-'): FAILED (extra rejection of 45).
- atk_6 UNGROUNDED-ORACLE ECHO (call encode_label on ASCII else-branch): FAILED.
- atk_7 PARTIAL-DOMAIN (drop non-ASCII encode_label, always return normally): FAILED.
- atk_8 CONTROL-FLOW-EFFECT bare self-recursion: FAILED 'Obligation leak check failed. Callee screen_host might not take all unsatisfied obligations' (MustTerminate(2), §A.1).
- atk_9 endless `while True`: FAILED 'Obligation leak check failed. Loop might not take all unsatisfied obligations' (MustTerminate).
- atk_10 PARTIAL-DOMAIN guard (reject ASCII-invalid only when encodable): FAILED (encodable is free on ASCII path).

A-LEG / kind audit (refinement.md + meta.json): meta has exactly one axiom kind='A-consumed' (encode_label ↔ _get_idna_encoded_host / idna.encode(uts46=True)), checked by axiom_check.py (G-AX, ran green: 7 encodable + 5 not-encodable oracle hosts + 2000 non-ASCII fuzz, total over {encodable->str, not-encodable->UnicodeError}). deep_model_references=[] (no A-reference), additional_change_sites=[] (no kind-3). Every refinement leg is R / A-consumed / I: A1 (R type List[int]<->str, non-empty via len>0), A2 (R host_is_ascii + A-consumed encode_label for the UNCHANGED IDNA branch), A3 (R + I: the operation ACTUALLY changed by the patch — startswith(u'*')->startswith((u'*',u'.')) — is modeled DIRECTLY as host[0] in {42,46} via a TRANSPARENT @Pure is_invalid_leading, NOT hidden behind an axiom).

The A-consumed axiom is genuinely consumed by screen_host's non-ASCII Ensures/Exsures (no dead axiom); its correspondence to the real callee (returns str iff encodable, raises UnicodeError->InvalidURL iff not) holds per axiom_check.py. Spec is a COMPLETE transparent relational contract over (non-empty host x host_is_ascii x encodable): Ensures+Exsures fix exactly reject-or-return for every admissible input, so any verifying same-spec impl is behaviourally equal to gold. verify => correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec faithfulness (G-PANEL-2) confirmed for psf__requests-5414 nagini. The modeled screen_host pins, for a non-empty host: (ASCII) reject iff host[0] in {42,46} (i.e. '*' or '.'); (non-ASCII) reject iff the label is not encodable (deferred to the real encoder). This matches the gold patch, which widens the ASCII leading-code-point rejection from host.startswith(u'*') to host.startswith((u'*', u'.')).

Evidence the model does NOT drift from or over-strengthen the real repo behavior:
1. Model verifies with pinned Nagini (13.3s, 'Verification successful').
2. Differential conformance against the REAL PATCHED repo: applied gold hunk to a fresh testbed (from base_commit worktree @ 39d0fdd9), ran the bundle's conformance_check.py (shadow = verbatim impl region; oracle = real requests.models.PreparedRequest.prepare_url host slice; @ContractOnly encode_label bound to the real _get_idna_encoded_host). Result: 'G-CONF OK ... 100042 inputs (42 boundary + 100000 fuzz, seed 5414), 0 disagreements.'
3. Independent hand-picked differential over the real patched prepare_url vs the model relation on 22 discriminating hosts (leading '.'/'*', empty labels '..'/'.a', mixed 'a*'/'*a', punycode 'xn--.de', and non-ASCII branch cases '.ü','*ü','ü','straße.de','☃.net'): model verdict == real repo verdict on every case, including the issue scenario '.example.com' (both reject) and confirming the leading-code-point screen is NOT applied on the non-ASCII branch (verdict there comes from the encoder).

Abstractions are legitimate: host_is_ascii is an R-refinement of unicode_is_ascii's verdict; encode_label is the A-consumed weakest contract of the UNCHANGED _get_idna_encoded_host (return-str/raise-UnicodeError), whose totality is checked by axiom_check.py. MustTerminate(2) is faithful (the real slice is bounded straight-line code that always answers), not an over-strengthening. No admissible input exists on which the modeled function disagrees with the real callee. Spec is not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: `host.startswith(u'*')` -> `host.startswith((u'*', u'.'))` — additionally reject an ASCII host whose first character is '.' (code point 46) as InvalidURL. The discriminating datum of the edit (a leading-'.' host must be rejected as InvalidURL) is already FULLY PUBLIC in problem_statement: the issue title is 'Getting http://.example.com raises UnicodeError', it gives the repro requests.get('http://.example.com'), and states Expected Result: 'InvalidUrl: URL has an invalid label.' So the spec view's 'reject iff first code point is 42 or 46' discloses nothing about the edit beyond the public statement — code point 46 ('.') is exactly the public expected behavior, and code point 42 ('*') is the PRE-EXISTING, unchanged rejection (surrounding context, not the gold edit).

Lexical screen (leakage.screen) run directly with the nagini backend on the projected spec view: PASSED with zero hard failures. Confirmed by inspection: (1) no diff markers; (2) no gold-patch changed line reproduced (>=8 char normalized) in the view; (3) patched file path requests/models.py appears ONLY in auditor-only mapping.md/refinement.md, never in the spec_view projection; (4) no patched repo symbols (prepare_url, _get_idna_encoded_host, unicode_is_ascii, startswith, InvalidURL) in the spec view — it uses only abstract carrier names (screen_host, is_invalid_leading, encode_label, InvalidLocator); (5) comments describe behavior/termination abstractly with no bug/fix narration.

meta G-LEAK status = pass (not relaxed); no RELAXED_LEAKAGE.md, relaxed_leakage flag unset — so this is a genuine clean pass, not a relaxation deferral. Nothing in the spec view reconstructs the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.