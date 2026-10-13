# mapping.md — astropy__astropy-14096

Symbol binding, type bijection, callee provenance, and the G-CONF posture for
this bundle. Spec derived COLD from `problem_statement` + gold `patch` + the real
source at `base_commit` (`spec_provenance: cold`).

## 1. The change

Single changed function: `SkyCoord.__getattr__`
(`astropy/coordinates/sky_coordinate.py:869-899` @ base_commit
`1a4462d72eb03f30dc83a879b1dd57aac8b2c18b`).

Gold hunk (the ONLY changed op — the final "# Fail" fallback of `__getattr__`):
```python
-        # Fail
-        raise AttributeError(
-            f"'{self.__class__.__name__}' object has no attribute '{attr}'"
-        )
+        # Call __getattribute__; this will give correct exception.
+        return self.__getattribute__(attr)
```

Behaviour. `__getattr__` is Python's last-resort hook, invoked only AFTER normal
attribute resolution has already failed for `attr`. The function body first runs
an UNCHANGED prefix (the `if "_sky_coord_frame" in self.__dict__:` block, lines
872-893): frame-name aliases, frame attributes, frame delegation, and
transform-to-frame interpretation. If that prefix produces a value it is
returned (unchanged). If it does not, control reaches the fallback at line 897.

- **Pre-patch (buggy):** the fallback FABRICATES a fresh
  `AttributeError("'{cls}' object has no attribute '{attr}'")` naming the
  ORIGINALLY-REQUESTED `attr`. When `attr` is itself a property/descriptor whose
  getter accessed some OTHER missing attribute (e.g. `prop` accessing
  `random_attr`), the genuine inner `AttributeError(random_attr)` that triggered
  `__getattr__` is discarded and MASKED by a message naming `prop`.
- **Post-patch (fix):** the fallback delegates to `self.__getattribute__(attr)` —
  the genuine attribute-resolution routine — and returns/propagates ITS outcome
  verbatim. Re-resolving `attr` re-runs the property getter, which fails again on
  `random_attr`, and that genuine `AttributeError(random_attr)` propagates
  unmasked. The originally-requested name is no longer consulted to build the
  result.

The F2P test `test_subclass_property_exception_error` asserts
`pytest.raises(AttributeError, match="random_attr")` — i.e. the propagated
failure must name the genuine inner attribute, not the requested property.

## 2. The Lean ↔ Python type bijection (used by G-CONF / G-AX posture)

| Lean (Solution.lean) | Python reality | bijection |
|---|---|---|
| `Name := Nat` | an attribute name (a `str`) | identity on identity: only WHICH attribute a failure refers to is observed, never its spelling. `requested` ↔ the `attr` argument; the `subject` of a failure ↔ the attribute named in the raised `AttributeError`'s message. |
| `Value := Nat` | a successfully resolved attribute value (any Python object) | opaque; only "a value was produced" is observed, never content. |
| `AttrErr { subject : Name }` | an `AttributeError`, observed by WHICH attribute it names | `subject` ↔ the attribute the message reports missing. `pytest.raises(match=...)` observes exactly this. |
| `Except AttrErr Value` | the outcome of an attribute access: a value, or an `AttributeError` | `Except.ok` ↔ a returned value; `Except.error e` ↔ a raised `AttributeError` naming `e.subject`. |
| `frameOutcome : Option Value` | outcome of the UNCHANGED prefix (lines 872-893): `some v` ↔ the prefix returned `v`; `none` ↔ the prefix fell through to the fallback. | the prefix is unchanged by the patch, so its result is a given. |
| `genuineOutcome : Except AttrErr Value` | the outcome `self.__getattribute__(attr)` would yield — the genuine attribute-resolution routine's result (a value, or the genuine `AttributeError` it reports, which may name an attribute OTHER than `attr`). | UNCHANGED callee; free input (§3). |

`lookupMissingAttribute(requested, frameOutcome, genuineOutcome)` models
`__getattr__(self, attr)` restricted to its observable outcome: a prefix value,
else the genuine routine's verbatim outcome.

## 3. Callee provenance

- **`self.__getattribute__(attr)`** — the genuine attribute-resolution routine
  (CPython `object.__getattribute__`, the type's default). UNCHANGED by the
  patch; it is what the patch newly delegates TO. Its outcome is carried as the
  read-only free input `genuineOutcome`. The spec makes NO claim about it and
  holds for every value it could take, so there is no axiom and no G-AX
  obligation (nothing is asserted about a real callee). The CHANGED op — which
  outcome the miss path returns — is modeled deeply in the `pure`/`impl` regions.
- **The unchanged prefix** (frame-name alias / `frame_attributes` /
  `_sky_coord_frame` delegation / `frame_transform_graph.lookup_name` +
  `transform_to`) — UNCHANGED context; its result is the free input
  `frameOutcome`. No flag dependencies.

No consumed axioms; no A-reference deep models. (See refinement.md A1-A4.)

## 4. G-CONF posture — conf_skip = true

The impl region is all-A-tagged (no R/I computation to differential-test): the
only changed op is "on a genuine miss, return the genuine routine's outcome
instead of a fabricated one", and that outcome is the FREE INPUT `genuineOutcome`
(an unchanged callee), so its R/I shadow is a constant pass-through with no
input-dependent computation to refute. The discriminating observable — the
IDENTITY of the propagated `AttributeError` (`random_attr` vs `prop`) —
materializes only against a live Python object model: a real subclass with a
property whose getter accesses a missing attribute, resolved through CPython's
descriptor + `__getattr__` machinery. There is no DB/interpreter-free,
input-dependent transliteration this gate can fuzz over ≥1e5 inputs.

Per SPEC_GUIDE §0 / WORKER_PROMPT: set `meta.json conf_skip=true` and ship a
`status=skip` conformance stub (precedent: django__django-11451, where the
changed op's only discriminating observable is likewise carried by a free input /
side effect on a live runtime). Soundness of the modeled behaviour is carried by
G-VERIFY (the spec provably forces the miss path to equal `genuineOutcome`) and
G-DIFF (the prepatch, which fabricates `Except.error { subject := requested }`,
fails exactly the miss-path clause). G-AX is `skip` (no axioms).

## 5. G-CONF fuzz seed

Pinned seed: **14096** (recorded for parity with non-skipped bundles; the
conformance check is a skip stub, so the seed is not exercised).
