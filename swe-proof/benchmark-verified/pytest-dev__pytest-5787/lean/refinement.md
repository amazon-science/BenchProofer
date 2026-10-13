# refinement.md — pytest-dev__pytest-5787

Operation-by-operation correspondence between the two `implementation_*`
functions (Solution.lean impl regions) and `patch.diff` (the POST-PATCH
`_report_to_json` / `_report_kwargs_from_json` in `src/_pytest/reports.py`).
Tags: **R** type refinement, **A-consumed** proof uses an axiom, **A-reference**
deep model validated == real callee, **I** identical concrete op.

## Modeled unit 1 — `implementation_serialize` ↔ `serialize_longrepr` (inside `_report_to_json`)

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `match lr with \| .single tb cr secs => …` | the non-`ExceptionChainRepr` branch of `serialize_longrepr` (`else: result["chain"] = None`) | R |
| 2 | single case returns `{ crash := cr, traceback := tb, sections := secs, chain := none }` | `result = {"reprcrash": serialize_repr_crash(reprcrash), "reprtraceback": serialize_repr_traceback(reprtraceback), "sections": rep.longrepr.sections}; result["chain"] = None` | R |
| 3 | `\| .chained chain secs => let outer := outerOf chain` | `isinstance(rep.longrepr, ExceptionChainRepr)`; outermost crash/tb come from `rep.longrepr.reprcrash`/`reprtraceback` (= `chain[-1][1]`/`chain[-1][0]`) | R |
| 4 | `let mut serChain := []; for link in chain do serChain := serChain ++ [packLink link]` | `result["chain"] = []; for repr_traceback, repr_crash, description in rep.longrepr.chain: result["chain"].append((serialize_repr_traceback(...), serialize_repr_crash(...), description))` | R |
| 5 | `return { crash := outer.2, traceback := outer.1, sections := secs, chain := some serChain }` | the assembled `result` dict with `reprcrash`/`reprtraceback`/`sections`/`chain` | R |
| 5a | `packLink l = l` (each link's traceback/crash/description copied through) | `serialize_repr_traceback` / `serialize_repr_crash` / the `description` pass-through — UNCHANGED by the patch | I |

## Modeled unit 2 — `implementation_deserialize` ↔ `_report_kwargs_from_json`

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 6 | `match s.chain with \| some (l :: ls) => …` | `if reportdict["longrepr"]["chain"]:` (truthy ⇒ non-empty link list) | R |
| 7 | `let mut deChain := []; for link in (l :: ls) do deChain := deChain ++ [unpackLink link]` | `chain = []; for repr_traceback_data, repr_crash_data, description in reportdict["longrepr"]["chain"]: chain.append((deserialize_repr_traceback(...), deserialize_repr_crash(...), description))` | R |
| 8 | `return .chained deChain s.sections` | `exception_info = ExceptionChainRepr(chain)` (+ `addsection` over the carried sections) | R |
| 9 | `\| _ => return .single s.traceback s.crash s.sections` | `else: exception_info = ReprExceptionInfo(reprtraceback, reprcrash)` (the no-chain / `chain is None` branch) | R |
| 9a | `unpackLink l = l` (each link's traceback/crash/description rebuilt from its copied fields) | `deserialize_repr_traceback` / `deserialize_repr_crash` / the `description` pass-through — UNCHANGED by the patch | I |

## Notes

- **Every step is R or I — no A.** No unchanged outside callee is *consumed* by
  either spec: the per-frame entry copy (`serialize_repr_entry` /
  `deserialize_repr_entry`), which the fix leaves behaviorally identical, is
  modeled as the identity `packLink`/`unpackLink` over the abstracted entry
  payload (`Entry`/`Link` carry exactly the fields copied through). SPEC_GUIDE §3
  forbids axiomatizing a deeply-modeled op. The `axioms` region is empty;
  **G-AX skips**.
- **The fix itself** is steps 3–5 (serialize) and 6–8 (deserialize): pre-patch,
  serialization recorded NO chain (`disassembled_report` produced only
  `reprcrash`/`reprtraceback`/`sections`) and deserialization ALWAYS rebuilt a
  single `ReprExceptionInfo`. So a chained representation round-tripped to a
  single exception (only its outermost link survived). Post-patch,
  `serialize_longrepr` records `result["chain"]` for an `ExceptionChainRepr` and
  `_report_kwargs_from_json` rebuilds an `ExceptionChainRepr(chain)` whenever the
  link list is present and non-empty. The two prepatch impls encode exactly these
  two independently-observable regressions:
  - `Solution_prepatch_1.lean`: serialize emits `chain := none` for a chain
    (drops the links) → its carried gold proof's `rw [ser_loop …]` fails (G-DIFF).
  - `Solution_prepatch_2.lean`: deserialize always returns `.single …` (ignores
    the links) → its carried gold proof's `rw [de_loop …]` fails (G-DIFF).
- **R vs I.** The Python objects (`ExceptionChainRepr`/`ReprExceptionInfo`,
  the builtin dict, the `ReprTraceback`/`ReprFileLocation` objects, the
  `(tb, crash, description)` tuples) are refined to the `Longrepr` /
  `SerializedLongrepr` / `Traceback` / `FileLoc` / `Link` carriers per the
  mapping.md bijection — hence **R**. The link-payload copy itself is unchanged
  and modeled as the identity, hence **I** (steps 5a, 9a).
- **Frame discipline (§0.5).** Both specs are exact equalities to the deeply
  modeled reference (`result = serializeLongrepr lr`, `result = deserializeLongrepr s`),
  so every output component — outermost crash/traceback, the section list, and
  the chain (presence + order + per-link contents) — is pinned to its input. No
  output component is left unconstrained.
- **G-CONF** mechanically refutes the R/I legs: a faithful in-process replica of
  the post-patch serialize/deserialize round-trip (modeled at the same data
  abstraction) is diffed against the impl shadow over ≥1e5 fuzzed inputs,
  including the round-trip composition `deserialize ∘ serialize`, which is the
  property the issue demands. No A legs.
