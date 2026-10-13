# mapping.md — pytest-dev__pytest-5787

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 955e54221008aba577ecbaefa15679f6777d3bf8`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
callee provenance / flag dependencies.

Repo file under change: `src/_pytest/reports.py` (class `BaseReport`'s
serialization helpers).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `serializeReport (r : TraceReport)` | `BaseReport._to_json` — `src/_pytest/reports.py:154` (post-patch the body delegates to the module function `_report_to_json`, `reports.py:+ _report_to_json`) | the modeled changed function (report → builtin dict) |
| `deserializeReport (s : Serialized)` | `BaseReport._from_json` — `src/_pytest/reports.py:205` (post-patch delegates to `_report_kwargs_from_json`) | the modeled changed function (builtin dict → report kwargs) |
| `roundTripReport (r : TraceReport)` | the composite `report_class._from_json(report._to_json())` lifecycle the F2P test exercises (`testing/test_reports.py::TestReportSerialization::test_chained_exceptions`) | the composite behavior the fix is about: deserialize ∘ serialize |
| `TraceReport` | the report's `longrepr` rendered object: a `ReprExceptionInfo` (single exception) or an `ExceptionChainRepr` (chain) — `_pytest/_code/code.py:901` / `:883` | the rendered exception representation that must survive serialization |
| `TraceReport.simple` | a `ReprExceptionInfo` longrepr (`reprtraceback`, `reprcrash`, `sections`) | a single, unchained exception representation |
| `TraceReport.chained` | an `ExceptionChainRepr` longrepr (`chain` = ordered list of `(reprtraceback, reprcrash, description)`, plus `sections`) | a chained exception representation; `chain` is the ordered list of links |
| `Link` | one element `(reprtraceback, reprcrash, description)` of `ExceptionChainRepr.chain` — `code.py:884` | one link of the chain |
| `Serialized` | the builtin-only dict `_to_json` returns under `d["longrepr"]` (keys `reprtraceback`, `reprcrash`, `sections`, and post-patch `chain`) | the serialized form |
| `encode` / `decode` | pure deep models of the two serialization code-paths (see §3) | deep models, NOT axiomatized callees |

The post-patch repo symbols the fix introduces (refinement audit only, not in
the consumer spec view): the module functions `_report_to_json` /
`_report_kwargs_from_json`, and the `"chain"` key serialized by
`serialize_longrepr` / consumed by `_report_kwargs_from_json` when the longrepr
is an `ExceptionChainRepr`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

The table G-CONF (§4.1) uses to translate values between the Lean value domain
and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| the `longrepr` rendered object | `TraceReport` | `ReprExceptionInfo` ↔ `TraceReport.simple`; `ExceptionChainRepr` ↔ `TraceReport.chained` (the two `isinstance` shapes the serializer distinguishes) |
| a single chain element `(reprtraceback, reprcrash, description)` | `Link` | `reprtraceback` (its rendered text) ↔ `Link.text`; `reprcrash` (its one-line summary) ↔ `Link.summary`; `description` (the connecting phrase, `str` or `None`) ↔ `Link.desc : Option String` |
| the rendered text of one exception (`ReprTraceback` of native/long entries) | `Nat` token `Link.text` | the per-link traceback codec (`serialize_repr_traceback` / `deserialize_repr_traceback`) is **unchanged** and carries this content **verbatim** through the round-trip; modeled as an opaque preserved token (an R refinement — the round trip is the identity on it) |
| the one-line summary (`ReprFileLocation` of `reprcrash`) | `Nat` token `Link.summary` | likewise carried verbatim by the unchanged `serialize_repr_crash` / `deserialize_repr_crash` codec; opaque preserved token (R) |
| a supplementary block `(name, content, sep)` from `addsection` | `Extra = String × String × String` | stored under `d["longrepr"]["sections"]` and restored by `addsection(*section)`; preserved verbatim (R) |
| the builtin dict `d["longrepr"]` | `Serialized` | `reprtraceback`/`reprcrash` ↔ `text`/`summary` tokens; `sections` ↔ `extras`; post-patch `chain` key: `None` ↔ `Serialized.chain = none`, the serialized link list ↔ `some links` |
| `isinstance(rep.longrepr, ExceptionChainRepr)` test | the `r` `match`'s `.chained` arm | a longrepr is `chained` iff it is an `ExceptionChainRepr` |

Modeling note — **top-level text/summary of a chain.** A real `ExceptionChainRepr`
sets `self.reprtraceback = chain[-1][0]` and `self.reprcrash = chain[-1][1]`
(`code.py:889-890`) — the outermost (last) link. `encode (.chained ls xs)`
mirrors this exactly: its top-level `text`/`summary` are `ls.getLast?`'s, while
the **full** `chain := some ls` is what `decode` rebuilds from. This is the crux
of the fix: pre-patch, only the top-level (outermost) `reprtraceback`/`reprcrash`
were serialized and a `ReprExceptionInfo` was rebuilt, collapsing the chain to
one exception; post-patch the whole `chain` is serialized and an
`ExceptionChainRepr` is rebuilt. G-CONF fuzzes multi-link chains to pin this.

## 3. Callee provenance (deep models — NOT axioms)

This fix changes no foreign callee; it rewires the report's own serialization
data-flow (it lifts two methods into module functions and adds `chain`
handling). Accordingly there are **no consumed axioms and no deep-model
references to a foreign callee** (`axioms` region is empty; `meta.json axioms =
[]`, `deep_model_references = []`). `encode` and `decode` are *deep models of the
two code paths the patch edits*, not of unchanged callees:

- `encode` models `_report_to_json`'s longrepr block (`reports.py` post-patch
  `serialize_longrepr`): for an `ExceptionChainRepr` it serializes the full
  `chain` list (`result["chain"] = [...]`) and the top-level
  `reprtraceback`/`reprcrash` (which equal `chain[-1]`); for a non-chain longrepr
  it sets `result["chain"] = None`. The `.chained` arm storing `some ls` is the
  gold-added chain serialization.
- `decode` models `_report_kwargs_from_json`'s longrepr block: if
  `reportdict["longrepr"]["chain"]` is present it rebuilds an
  `ExceptionChainRepr(chain)` (the full chain); otherwise a `ReprExceptionInfo`.
  The `some ls => .chained ls` arm is the gold-added
  `exception_info = ExceptionChainRepr(chain)` branch.

The per-link traceback/crash/section codecs (`serialize_repr_*` /
`deserialize_repr_*`) are **unchanged** by the patch and carry their content
verbatim through the round trip; they are modeled as the R-refinement
"content-preserving token" (§2), not as axioms — there is nothing about their
behavior the proof depends on beyond round-trip identity, which G-CONF exercises
end-to-end against the real codecs.

Because `encode`/`decode` model the **changed** operations, they are exercised
end-to-end by G-CONF against the patched real `_report_to_json` /
`_report_kwargs_from_json` (§4 below), not by an axiom check. There is no
`axiom_check.py` in this bundle (G-AX skips: no axioms).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`5787`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds is the
transliteration of `encode`/`decode`/`roundTripReport` (all R/I-tagged ops, no
A-tagged callee in the computed output) to Python; it builds a real `longrepr`
(`ReprExceptionInfo` / `ExceptionChainRepr` with native traceback entries
carrying token content), runs the patched real `_report_to_json` then
`_report_kwargs_from_json`, and compares the reconstructed longrepr against the
shadow `decode ∘ encode`. Inputs span: a single exception (simple), a 2-link
chain (the exact F2P shape, #5786), a 3-link chain (the problem_statement's
worked examples), a single-link chain, and randomized mixtures with/without
supplementary blocks.
