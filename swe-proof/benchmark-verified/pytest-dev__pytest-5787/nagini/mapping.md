# mapping.md — pytest-dev__pytest-5787

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 955e54221008aba577ecbaefa15679f6777d3bf8`, states the type
abstraction, and gives the provenance of the (single, A-reference) callee the
deep model is validated against.

Repo file under change: `src/_pytest/reports.py` (with supporting classes in
`src/_pytest/_code/code.py`).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `serialize_chain(chain)` | `BaseReport._to_json` — `src/_pytest/reports.py:154` (the nested `disassembled_report`, body lines 164-202; post-patch the module-level `_report_to_json`) | modeled changed function: reduce a failure representation to a transport form |
| `deserialize_chain(transport)` | `BaseReport._from_json` — `src/_pytest/reports.py:204` (body lines 214-262; post-patch the module-level `_report_kwargs_from_json`) | modeled changed function: reconstruct a failure representation from its transport form |
| `copy_link(link)` *(deep model — A-reference)* | the per-link structural copy each step applies to one chain element: serialize does `reprtraceback.__dict__.copy()` / `reprcrash.__dict__.copy()` and the per-entry `__dict__.copy()` (`reports.py:165-185`, post-patch `serialize_repr_traceback`/`serialize_repr_crash`/`serialize_repr_entry`); deserialize rebuilds the matching `ReprTraceback`/`ReprFileLocation`/`ReprEntry` (`reports.py:223-256`, post-patch `deserialize_repr_*`) | pure spec: the content-preserving copy of one link; modeled deeply as the identity on a link token, validated == the real per-link (de)serializer by axiom_check.py (G-AX), NOT consumed as an axiom |

The chain object itself is `_pytest._code.code.ExceptionChainRepr`
(`src/_pytest/_code/code.py:883`), whose `.chain` is a list of
`(reprtraceback, reprcrash, description)` tuples — one per stage of a chained
exception. The degenerate single-stage failure is `ReprExceptionInfo`
(`code.py:901`), modeled as a chain of length one. The newest (outermost) link
is `chain[-1]`; `ExceptionChainRepr.__init__` copies it into
`self.reprtraceback`/`self.reprcrash` (`code.py:889-890`) — which is exactly the
only link the pre-patch transport form preserved.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `ExceptionChainRepr.chain` — a `list` of links `(reprtraceback, reprcrash, description)` | `List[int]` of opaque link tokens | `chain[k]` (a link tuple) ↔ `chain[k]` (an `int` token); `len(chain)` ↔ `len(chain)`; list order ↔ list order |
| one link's contents (`reprtraceback`, `reprcrash`, `description`) | one `int` token | the per-link structural copy is content-preserving (an unchanged `__dict__.copy()` / re-`__init__`), so the abstraction collapses a link to a single value preserved by `copy_link` (identity). What is under specification is the COUNT and ORDER of links, which the token carrier preserves faithfully. |
| `result["chain"]` list emitted by serialization / `chain` argument rebuilt by deserialization | `List[int]` returned | the transport form is itself a list of per-link encodings; the model returns the list of (copied) link tokens |
| the degenerate `ReprExceptionInfo` (no chain) | the length-1 chain | `Requires(len(chain) >= 1)`; a single-stage failure is the chain `[link]` |

`str` indexing/iteration is banned in Nagini and is irrelevant here: the per-
link text content is an unchanged copy; only the chain's length and ordering
are the behaviour under test. The specification is phrased over `PSeq[int]` via
`ToSeq`.

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `copy_link` / the serialize+deserialize loops ↔ the real (de)serializers

**Callee:** the post-patch `_report_to_json` / `_report_kwargs_from_json`
(`src/_pytest/reports.py`, post-patch lines 344-485). The changed serialize/
deserialize behaviour is modeled **deeply** by the verified loops in
`serialize_chain` / `deserialize_chain` (each emits/reproduces every link of its
input, in order) plus the content-preserving `copy_link`; there is **no
`@ContractOnly` axiom** the proof consumes. The deep model is validated equal to
the real callees out-of-band by axiom_check.py (G-AX).

The behaviour the deep model encodes, from the real source:

- **serialize (`_report_to_json` → `serialize_longrepr`):** when the failure is
  an `ExceptionChainRepr`, it builds `result["chain"]` by iterating
  `rep.longrepr.chain` and emitting, for EACH link,
  `(serialize_repr_traceback(tb), serialize_repr_crash(crash), description)` —
  i.e. every link, in order. Otherwise `result["chain"] = None` (the degenerate
  single-stage form). The per-link serializers are unchanged `__dict__.copy()`
  operations (content-preserving) ⇒ `copy_link` is the identity.
- **deserialize (`_report_kwargs_from_json`):** when `reportdict["longrepr"]
  ["chain"]` is truthy, it iterates that list and rebuilds EACH link via
  `(deserialize_repr_traceback(tb), deserialize_repr_crash(crash),
  description)`, then constructs `ExceptionChainRepr(chain)` — the full chain.
  Otherwise it constructs `ReprExceptionInfo(reprtraceback, reprcrash)` (the
  single-stage form). The per-link deserializers reconstruct the same content
  ⇒ `copy_link` is the identity and `deserialize ∘ serialize` is identity on the
  whole chain.

The single behavioural change the F2P tests observe is precisely that the
transport form now carries the WHOLE `chain` (length ≥ 2 for a genuinely
multi-stage failure) and reconstruction rebuilds it as an `ExceptionChainRepr`
of the same length — rather than collapsing to the outermost link `chain[-1]`
(the pre-patch `disassembled_report` serialized only `rep.longrepr.reprtraceback`
/`reprcrash`, and `_from_json` rebuilt only a single `ReprExceptionInfo`).

**Soundness check (G-AX):** `axiom_check.py` drives the REAL patched pytest as a
subprocess on real chained-exception reports — for both `TestReport` (call
phase) and `CollectReport` (import-time), chained with and without an explicit
`from` cause — runs the real `report._to_json()` / `report_class._from_json(...)`
round trip, and asserts the reconstructed `longrepr` is an `ExceptionChainRepr`
whose `chain` has the SAME length (≥ 2) and the SAME per-index traceback text +
description as the original (a structural equality at the link-count/order level
— NO double mask), plus that sections survive and the reconstructed object
renders. It imports nothing repo-private beyond `pytest`/`_pytest` (the package
the gold patch changes). Exit 0 iff sound.
