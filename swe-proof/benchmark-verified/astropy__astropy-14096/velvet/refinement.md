# refinement.md — astropy__astropy-14096

Operation-by-operation correspondence between `Solution.lean`'s
`lookupMissingAttribute` impl region and `patch.diff` (the gold patch replaces
the `# Fail` fallback of `SkyCoord.__getattr__` with a delegation to the genuine
attribute-resolution routine). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** / **A-reference**), or **I** (identical
concrete op). EVERY step is R, A, or I.

`patch.diff` is the gold patch **verbatim** (applies at base_commit, resolves —
G-RESOLVE).

## A. The miss-path fallback — `SkyCoord.__getattr__`

Gold hunk:
```python
-        # Fail
-        raise AttributeError(
-            f"'{self.__class__.__name__}' object has no attribute '{attr}'"
-        )
+        # Call __getattribute__; this will give correct exception.
+        return self.__getattribute__(attr)
```

| # | Solution.lean impl op (`lookupMissingAttribute`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `requested : Name`; `frameOutcome : Option Value` | the `attr` argument; the result of the UNCHANGED prefix `if "_sky_coord_frame" in self.__dict__: …` (lines 872-893) | **R** | `attr : str` ↔ `requested : Name` (identity-only, mapping.md §2). The unchanged prefix's effect is summarized by `frameOutcome`: `some v` ↔ the prefix returned `v`, `none` ↔ it fell through. The prefix is unchanged by the patch, so its outcome is taken as a given input, not re-derived. |
| A2 | `match frameOutcome with \| some v => Except.ok v` | the prefix's own `return …` paths (frame alias / frame attribute / delegation / transform) — UNCHANGED | **I** | identical concrete op: when the prefix produced a value, that value is the result. Both pre- and post-patch behave identically here; the patch touches only the fall-through. |
| A3 | `\| none => genuineOutcome` (return the genuine routine's outcome verbatim) | `return self.__getattribute__(attr)` (the added line) | **R** + free input | the CHANGED op, modeled deeply as "hand back the genuine attribute-resolution routine's outcome verbatim". `self.__getattribute__(attr)` is the UNCHANGED genuine resolver; its outcome (a value, or an `AttributeError` naming whatever attribute genuinely failed — possibly one OTHER than `attr`) is carried as the free input `genuineOutcome : Except AttrErr Value` (mapping.md §3). `Except.ok` ↔ returned value; `Except.error { subject }` ↔ raised `AttributeError` naming `subject`. The requested name is NOT consulted on this path — matching the patch, where `attr` no longer appears in any fabricated message. |
| A4 | (no node — absent in the fix) | the DELETED `raise AttributeError(f"'{cls}' …has no attribute '{attr}'")` | — | the removed buggy op. Its analogue in `Solution_prepatch.lean` is `none => Except.error { subject := requested }`: fabricate a failure renamed to the requested attribute. The frozen spec (A3) demands `genuineOutcome` on the miss path, so the prepatch fails exactly there (G-DIFF). |

No A (axiom) steps; no A-reference deep models. The single changed op (A3) is the
delegation, modeled deeply and tagged **R** + free input; the unchanged genuine
callee's outcome is a free input, not axiomatized or re-derived (its content is
irrelevant — the spec holds for every value it could take). No kind-3
(inexpressible-changed-op) steps.

## B. verify(Solution) ⇒ resolved; prepatch fails on the right clause

`lookupMissingAttribute` verifies only if `out = attrFallbackSpec …`, i.e.:
- when the prefix produced a value (`frameOutcome = some v`): `out = Except.ok v`
  (A2); and
- on a genuine miss (`frameOutcome = none`): `out = genuineOutcome` — the genuine
  attribute-resolution routine's outcome propagated verbatim (A3), NOT a failure
  renamed to `requested`.

By R (mapping.md §2) this is exactly the patched `__getattr__`: on a miss it
`return self.__getattribute__(attr)`, so a genuine inner `AttributeError`
(naming, e.g., `random_attr`) propagates unmasked. The F2P test
`test_subclass_property_exception_error` asserts
`pytest.raises(AttributeError, match="random_attr")` — the propagated failure
names the GENUINE attribute, i.e. `genuineOutcome`'s `subject`, not `requested`.
The PASS_TO_PASS suite requires the prefix value-paths (A2) and genuine
value-paths to be unperturbed — satisfied because A2/A3 return them verbatim.

The prepatch (`Solution_prepatch.lean`) fabricates the failure on the miss path:
`none => Except.error { subject := requested }`. The frozen spec demands
`genuineOutcome`, so `prove_correct` fails on exactly the discriminating clause
(verified: unsolved goal isolates the `none` branch,
`Except.error { subject := requested } = genuineOutcome`). For a genuine
property-getter miss `genuineOutcome = Except.error { subject := random_attr }`
while the prepatch yields `Except.error { subject := prop }` — exactly the masking
bug the issue reports.

## C. No kind-3 steps; G-CONF posture

Every step is R or I. The one operation that genuinely changed — the miss-path
result — is modeled deeply (A3) as returning the unchanged callee's outcome,
carried as a free input, not hidden behind an axiom about the function under
change. The impl region is therefore all-A-tagged (no input-dependent R/I
computation): see mapping.md §4. `meta.json conf_skip=true`;
`conformance_check.py` is a `status=skip` stub. Soundness is carried by G-VERIFY
(the spec forces the miss path to equal `genuineOutcome`) and G-DIFF (the
prepatch's fabricated failure fails that clause). G-AX is `skip` (no axioms — the
genuine resolver is a free input the spec asserts nothing about).
