# mapping.md — pytest-dev__pytest-5787

## Instance
- repo: pytest-dev/pytest
- base_commit: `955e54221008aba577ecbaefa15679f6777d3bf8`
- changed file: `src/_pytest/reports.py`
- spec_provenance: cold (derived only from problem_statement + gold patch + repo source at base_commit)

## What the fix does (behavioral summary)
A failure representation attached to a report (`report.longrepr`) can be either a
single-exception representation (carrying one traceback + one crash location) or a
*chained* representation (carrying an ordered list of `(traceback, crash, description)`
links — the analogue of Python's "The above exception was the direct cause …" /
"During handling of the above exception …" output).

A report can be turned into builtin-only data ("serialized") and reconstructed
("deserialized"). At base_commit the serialize step never recorded the chain links
and the deserialize step always rebuilt a single-exception representation, so a
chained representation collapsed to its outermost link after a round-trip. The fix
records the chain on serialize and rebuilds a chained representation from it on
deserialize, so the full chain survives the round-trip.

## Symbol binding (file:line @ base_commit)
| Lean symbol | Python symbol | file:line @ base_commit | provenance |
|---|---|---|---|
| `serializeFailureRepr` / `implementation_serialize` | the longrepr-serialization branch (`disassembled_report` → rewritten as `serialize_longrepr` inside `_report_to_json`) | `src/_pytest/reports.py:164-185` (old `disassembled_report`); gold replaces with `_report_to_json`/`serialize_longrepr` (patch hunk @ 339+) | changed; deeply modeled |
| `deserializeFailureRepr` / `implementation_deserialize` | the longrepr-deserialization branch of `BaseReport._from_json` (gold extracts `_report_kwargs_from_json`) | `src/_pytest/reports.py:214-260` | changed; deeply modeled |
| `serializeTraceback` / `deserializeTraceback` | `serialize_repr_traceback` / `deserialize_repr_traceback` (entry-payload copy; UNCHANGED across the fix) | gold `_report_to_json`/`_report_kwargs_from_json` inner helpers | unchanged sub-op (I) |
| `Longrepr.single` | `ReprExceptionInfo(reprtraceback, reprcrash)` + sections | `_code/code.py:901-909` | type model |
| `Longrepr.chained` | `ExceptionChainRepr(chain)` + sections; `reprtraceback`/`reprcrash` = `chain[-1][0]`/`chain[-1][1]` | `_code/code.py:883-898` | type model |
| `SerLongrepr` | the dict produced for `d["longrepr"]` (`reprcrash`, `reprtraceback`, `sections`, `chain`) | gold `serialize_longrepr` | type model |
| `FileLoc` | `ReprFileLocation(path, lineno, message)` | `_code/code.py:990-1004` | type model |
| `Traceback` | `ReprTraceback(reprentries, extraline, style)` | `_code/code.py:912-918` | type model |
| `Entry` | `ReprEntry` / `ReprEntryNative` per-frame payload (`type` tag + copied dict) | `_code/code.py:946-987` | type model (payload copied through unchanged) |

## Lean ↔ Python type bijection (used by G-CONF / G-AX)
- `str` → Lean `String`.
- `int` (lineno) → Lean `Int`.
- a `(name, content, sep)` section tuple → `String × String × String`.
- `Optional[str]` (e.g. `extraline`, a chain link's `description`) → `Option String`.
- `ReprFileLocation` → `FileLoc { path, lineno, message }`.
- `ReprTraceback` → `Traceback { reprentries : List Entry, extraline : Option String, style : String }`.
- a per-frame entry (`ReprEntry`/`ReprEntryNative`) → `Entry { tag, lines, style }`, where
  `tag` is the kind name and `lines`/`style` stand for the entry payload that the
  (de)serialization copies through unchanged.
- a chain link `(ReprTraceback, ReprFileLocation, Optional[str])` → `Traceback × FileLoc × Option String`.
- `report.longrepr` (the toterminal-able, reprtraceback/reprcrash-bearing case) →
  `Longrepr` (`single` ↔ `ReprExceptionInfo`, `chained` ↔ `ExceptionChainRepr`).
- the serialized `d["longrepr"]` dict → `SerLongrepr`; its `"chain"` key is `none`
  when absent / `null`, `some links` otherwise.

## Callee provenance + flag deps
- No UNCHANGED outside callee is consumed by either spec. The serialize/deserialize
  logic, including the entry-payload copy (`serialize_repr_entry`/`deserialize_repr_entry`,
  which the fix leaves behaviorally identical), is modeled deeply. No `opaque`/`axiom`
  callee contract is needed → `axiom_check.py` is a skip stub (G-AX skip).
- The discriminator is purely the presence of the chain: `ExceptionChainRepr` carries a
  non-empty `chain`; `ReprExceptionInfo` carries none. `serialize_longrepr` branches on
  `isinstance(rep.longrepr, ExceptionChainRepr)`; `_report_kwargs_from_json` branches on
  `reportdict["longrepr"]["chain"]` truthiness.
- The outer report-dict framing in `_report_to_json` (`__dict__.copy()`, path→str,
  `result`→None) is unchanged by the fix and is outside the modeled unit.

## Modeling scope + reachability notes
- **`outerOf = getLast?` is source-backed.** `ExceptionChainRepr.__init__`
  (`_code/code.py:889-890`) sets `self.reprtraceback = chain[-1][0]` and
  `self.reprcrash = chain[-1][1]` — the outermost (newest) exception is the LAST
  link. `serialize_longrepr` reads those very fields for the serialized
  `reprtraceback`/`reprcrash`, so the model's `outerOf chain = chain.getLast?` is
  the faithful refinement.
- **`.chained []` is unreachable in real code.** That same `chain[-1]` access in
  `ExceptionChainRepr.__init__` would raise `IndexError` on an empty chain, so a
  real `ExceptionChainRepr` always carries ≥ 1 link. The Lean type nonetheless
  admits `.chained []`; both modeled functions totalize it deterministically
  (`serialize (.chained []) = {…, chain := some []}`, and `deserialize {…, chain
  := some []} = .single …` — matching Python truthiness `if …["chain"]:`). This
  is a benign over-approximation of the domain, not a soundness hole: each
  `correct_*` theorem holds for ALL inputs, and G-CONF checks both `none` and
  `some []` consistently across oracle and shadow.
- **Per-link entry payload is abstracted (scope).** The fix does NOT touch the
  per-frame entry copy (`serialize_repr_entry`/`deserialize_repr_entry`), so this
  bundle models a link's traceback/crash/description as data carried through
  unchanged (`packLink`/`unpackLink` = identity over the abstracted `Link`). The
  verified delta is the CHAIN structure (presence + order + per-link payload
  preservation), which is exactly the issue (#5786). Nested frame-encoding
  regressions are out of scope by construction (refinement.md steps 5a/9a, tag I).

## G-CONF fuzz seed
- pinned seed: `5787` (recorded in meta.json `verifier_pins.conf_seed`).
