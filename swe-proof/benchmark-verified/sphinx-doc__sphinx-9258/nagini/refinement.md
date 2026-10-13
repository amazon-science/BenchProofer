# refinement.md — sphinx-doc__sphinx-9258

The operation-by-operation correspondence between `model.py`'s implementations
(the `render_nodes` impl region with its verified helpers `next_sep_idx` /
`sep_end_idx` / `strip_left_idx` / `copy_span` and the deep `rendered` /
`next_sep` / `sep_end` models; and the retained, strictly weaker `split_render`
impl region, which scans with the same `next_sep_idx` / `sep_end_idx` helpers
against the deep `marks` model) and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — split into **A-consumed**, where the proof uses an axiom's `Ensures`,
and **A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit` and is the real correctness oracle, G-RESOLVE).

## A0. The PRIMARY obligation — the whole node stream (`render_nodes`)

Same site, read at full strength. `make_xrefs` does not return kinds; it returns
NODES, and each node carries a piece of the input:

```
delims = r'(\s*[\[\]\(\),](?:\s*or\s)?\s*|\s+or\s+|\s*\|\s*|\.\.\.)'   # line 307
delims_re = re.compile(delims)
sub_targets = re.split(delims, target)                                  # 309
results = []
for sub_target in filter(None, sub_targets):                            # 314
    if delims_re.match(sub_target):
        results.append(contnode or innernode(sub_target, sub_target))    # 319  literal
    else:
        results.append(self.make_xref(rolename, domain, sub_target, ...))# 321  xref
return results                                                          # 324
```

| # | model.py impl op (`render_nodes`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| P1 | parameter `target: List[int]`; no domain `Requires` beyond the read permission and `MustTerminate(5)` | `target: str` argument of `make_xrefs`, which the real code accepts unconditionally | R | `str` ↔ `List[int]` code points (mapping.md §2). The absence of a domain clause is deliberate: the real function has no precondition, so a spec that adds one leaves the excluded shapes free. |
| P2 | `j = next_sep_idx(target, i)` — the leftmost position at or after `i` where a separator token starts (postcondition `== next_sep(...)`) | the position of the leftmost match of the WHOLE delimiter alternation that `re.split` finds at or after `i` | A-reference | modeled deeply: `sep_end` reproduces the four alternatives of line 307 in the regex's own preference order, so `next_sep` is the leftmost delimiter match — every separator the regex splits on, not just the added bar. Validated == the real `re.split`/`re.match` by G-AX on all 266 595 inputs, no domain; NOT a consumed axiom. |
| P3 | `e = sep_end_idx(target, j)` (postcondition `== sep_end(...)`, with `j < e <= n`) | the extent of that delimiter match — the text `re.split` hands back as the separator piece | A-reference | same deep model. The `\s*` padding on the bracket/comma and bar alternatives, and the mandatory whitespace of `\s+or\s+`, are consumed into the token exactly as `strip_left` consumes it, so the separator piece carries its padding — which is what the real node carries. |
| P4 | `copy_span(out, target, i, j)` then `out.append(-1)` when `j > i`; nothing when `j == i` | `results.append(self.make_xref(..., sub_target, ...))` for a non-delimiter piece (line 321); `filter(None, sub_targets)` (line 314) dropping the empty piece when a delimiter starts right at `i` | R + I | one cross-reference node per non-empty stretch between separators, carrying `target[i:j]` VERBATIM — the exact `sub_target` string the real code passes to `make_xref`, padding included, nothing trimmed. `filter(None, ...)` is modeled by emitting no node when the stretch is empty. |
| P5 | `copy_span(out, target, j, e)` then `out.append(-2)` | `results.append(contnode or innernode(sub_target, sub_target))` for a delimiter piece (line 319), i.e. `Field.make_xref`'s `contnode or innernode(target, target)` (`util/docfields.py:70`) | R + I | one literal separator node per delimiter match, carrying `target[j:e]` verbatim — the separator's own characters with their padding. |
| P6 | on the last pass: `copy_span(out, target, i, n)` + `out.append(-1)` when text remains, nothing when it does not; then `out.append(-3)` | the final iteration of the `for` loop plus `return results` (line 324) | R + I | the trailing stretch is one cross-reference when non-empty (`filter(None, ...)` again when it is not); `-3` closes the stream. |
| P7 | `Ensures(ToSeq(Result()) == rendered(ToSeq(target), 0))` | `results` returned (`List[Node]`) | R | the node list is encoded as `<the node's code points> <kind marker>` per node, markers −1/−2, closed by −3 (mapping.md §2). Code points are non-negative, so the encoding is INJECTIVE: this one equality pins the node COUNT, each node's KIND and each node's EXACT TEXT. |
| P8 | `Requires(MustTerminate(5))` and `Invariant(MustTerminate(n - i + 1))` | the `for` loop over a finite `sub_targets` list | I | total correctness: without it every `Ensures` is claimed only of runs that return, and a renderer that never returns satisfies the postcondition vacuously. Level 5 is strictly above every callee (`next_sep_idx` 4, `sep_end_idx` 3, `strip_left_idx` 2, `copy_span` 2). |

**What P7 forbids that the kind-only reading (§A) did not.** The kind sequence
fixes only *how many* nodes there are and *which sort* each is. The stream fixes
their contents, so all of the following now fail to verify — each of them a real
patch someone could write:
- one cross-reference over the whole string (the pre-patch defect) — that stream
  carries the bar and its padding INSIDE a cross-reference instead of in a
  literal node of its own;
- the right nodes with trimmed payloads (`" int"` rendered as `"int"`), which is
  what a tokeniser that strips each piece produces and is NOT what `re.split`
  hands to `make_xref`;
- the right nodes with the separator text dropped, re-padded, or normalised;
- a node stream that is gold on bar-only specifications and arbitrary on
  bracket/comma/`or`/ellipsis ones — the region a bar-only domain clause would
  leave free, which is why neither obligation carries one (see §B);
- the same characters redistributed over a different NUMBER of nodes (one
  cross-reference per character, or two nodes whose texts concatenate to one
  gold node's text), which still renders every named type but is not one link
  per named type.

All five are in the falsification battery (`properties.py`, the `uniqueness`
lane) and all are rejected; the battery's own soundness and admissibility lanes
verify, so the obligation is not merely unsatisfiable-and-therefore-strong.

## A. The RETAINED weaker reading — node kinds only (`split_render`)

Same site (`PyXrefMixin.make_xrefs`, `sphinx/domains/python.py:304`), read at the
strength of the node-KIND sequence alone, and — like §A0 — on the WHOLE input
domain. It is a projection of §A0 and is kept because *one link per named type,
one literal per separator* is the most direct reading of the change; it is not what
carries the payload obligation.

Gold hunk (`python.py:307`):
```
- delims = r'(\s*[\[\]\(\),](?:\s*or\s)?\s*|\s+or\s+|\.\.\.)'
+ delims = r'(\s*[\[\]\(\),](?:\s*or\s)?\s*|\s+or\s+|\s*\|\s*|\.\.\.)'
  delims_re = re.compile(delims)
  sub_targets = re.split(delims, target)
  ...
  for sub_target in filter(None, sub_targets):
      if delims_re.match(sub_target):
          results.append(contnode or innernode(sub_target, sub_target))   # literal separator
      else:
          results.append(self.make_xref(rolename, domain, sub_target, ...))  # cross-reference
```

| # | model.py impl op (`split_render`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `target: List[int]`; no domain `Requires` beyond the read permission and `MustTerminate(5)` | `target: str` argument of `make_xrefs`, accepted unconditionally | R | `str` ↔ `List[int]` code points (mapping.md §2). The absence of a domain clause is deliberate and load-bearing: a kind sequence is required of every specification, so no shape's kinds are left free (see §B). |
| A2 | `j = next_sep_idx(target, i)` — the leftmost position at or after `i` where a separator token starts (postcondition `== next_sep(...)`) | the leftmost match of the WHOLE delimiter alternation (`python.py:307`) that `re.split` finds at or after `i` | A-reference | the changed split operation is modeled **deeply**, over the full vocabulary: `sep_end` reproduces the four alternatives of line 307 in the regex's own preference order, so the bar the patch adds is one boundary among the pre-existing ones rather than the only one recognised. Validated == the real `re.split`/`re.match` by G-AX on all 266 595 inputs, no domain; NOT a consumed axiom. |
| A3 | `e = sep_end_idx(target, j)` (postcondition `== sep_end(...)`, with `j < e <= n`), then `i = e` | the extent of that delimiter match — the piece `re.split` hands back as the separator — and the scan resuming after it | A-reference | same deep model as P3. Because `e > j` the scan advances by at least one code point per pass, which is what makes the loop's `MustTerminate(n - i + 1)` bound decrease. |
| A4 | `result.append(True)` when `j > i`; nothing when `j == i` | `results.append(self.make_xref(..., sub_target, ...))` for a non-delimiter piece (`python.py:321`); `filter(None, sub_targets)` (314) dropping the empty piece when a delimiter starts right at `i` | R + I | one cross-reference node per non-empty stretch between separators, abstracted to its kind. `filter(None, ...)` is modeled by emitting no kind when the stretch is empty — the case a bar-only reading cannot express (`"a[b]"`, `"...|..."`). |
| A5 | `result.append(False)` for the separator token | `results.append(contnode or innernode(sub_target, sub_target))` for a delimiter piece (`python.py:319`) | R + I | one literal separator node per delimiter match, abstracted to its kind: a separator is NEVER rendered as a cross-reference. |
| A6 | on the last pass: `result.append(True)` when text remains (`i < n`), nothing when it does not | the final iteration of the `for` loop plus `return results` (324) | R + I | the trailing stretch is one cross-reference when non-empty; a specification that ends at a separator, or is empty, contributes nothing further. The empty kind sequence is `PSeq(True).drop(1)`. |
| A7 | `Ensures(ToSeq(Result()) == marks(ToSeq(target), 0))` | `results` returned (`List[Node]`), read for kinds | R + A-reference | `marks` is `rendered`'s case analysis with the carried text dropped (mapping.md §3.3), so this equality pins the node COUNT and each node's KIND for EVERY specification — one link per named type, one literal per separator. Validated == the real function's node kinds by G-CONF on all 254 104 inputs with no filter, 0 disagreements, 115 700 of them carrying a non-bar separator. |
| A8 | `Requires(MustTerminate(5))` and `Invariant(MustTerminate(n - i + 1))` | the `for` loop over a finite `sub_targets` list | I | total correctness: without it the postcondition is claimed only of runs that return. Level 5 is strictly above every callee (`next_sep_idx` 4, `sep_end_idx` 3, `strip_left_idx` 2). |

`first_bar` / `kinds` / `seg_text` / `slice_trim` / `first_bar_idx` are the RETAINED
bar-only readings (mapping.md §3.1, §B below). They are validated pure functions
and executable helpers, exercised by G-AX and G-CONF, but they are **not part of
any obligation**: the kind claim is A7's `marks`, and the payload claim is P7's
`rendered`. The type-name text a segment contributes is stated exactly — untrimmed,
padding included — by P4, so nothing about the payload rests on the trimmed
reading.

The discriminating content of the change — the vertical bar becomes a split
point, so a bar-separated spec yields one cross-reference per type rather than a
single one — lives in `sep_end` recognising the bar (code point `124`, with its
`\s*` padding) as a boundary, and in `marks` counting the resulting nodes. The
pre-patch delimiter set did NOT include the bar; `model_prepatch.py` reproduces
that (the bar is never a split point, so a bar-only spec is one stretch → a single
cross-reference `[True]`) and **fails** the postcondition
`ToSeq(Result()) == marks(ToSeq(target), 0)` for any bar-containing input (e.g. the
F2P `int | str`, where `marks == [True, False, True]`). That is exactly the spec
sensing the change (G-DIFF).

## B. The `well_formed` bar-only shape — a retained reading, NOT a domain

**`well_formed` restricts nothing. Neither obligation carries a domain clause.**
§A0 (`render_nodes`) and §A (`split_render`) are both claimed of every
specification — bracket, comma, `or`, ellipsis, adjacent separators and any mixture
of them with the bar included — because `sep_end` recognises every separator the
real regex splits on and both `rendered` and `marks` are total folds over that
vocabulary. G-CONF measures both obligations on 115 700 inputs that fall outside
the bar-only shape, 0 disagreements.

That matters because a precondition is an ASSUMPTION: on the inputs it excludes
the verifier discharges nothing, so a spec that gated its kind sequence on
`well_formed` would say nothing about the kinds of `"List[int] | None"`,
`"int, str"` or `"a[b]"` — exactly the shapes the PASS_TO_PASS tests
`tests/test_domain_py.py::test_domain_py_xrefs` and `::test_info_field_list`
observe — and a branch guarded on `not no_other_sep(...)` would be dead for the
verifier and live at runtime. `split_render` therefore carries `marks`, which is
stated everywhere, and `well_formed` survives only as the predicate that marks
where the bar-only `kinds` reading is exact.

Nor could `kinds` simply be de-gated: it is FALSE of the real patched function off
that shape (for `"list[int] | None"` the real code makes 6 nodes and `kinds`
describes 3), so asserting it everywhere would replace a too-weak clause with an
unfaithful one. That is why the kind obligation is a different fold, `marks`
(mapping.md §3.3), and not `kinds` with the guard deleted.

What follows is why the bar-only reading is exact only on that shape.

The `kinds` model treats the vertical bar as the ONLY separator. The real
`make_xrefs` regex, however, also splits on the other (pre-existing, unchanged)
delimiters — `[ ] ( ) ,`, the whitespace-bounded word `or`, and `...` — and its
`filter(None,...)` drops empty pieces. So the bar-only reading equals the real
tokeniser only on a shape that excludes BOTH failure sources. `well_formed`
therefore has two clauses:

1. **every bar-separated segment names a non-empty type** (no leading/trailing/
   consecutive bars such as `"|"`, `"a||b"`, `" | "` — `filter(None,...)` would
   drop empty pieces and break strict alternation); and
2. **`no_other_sep`** — the spec contains none of the other delimiter triggers
   (`[ ] ( ) ,`, a `...` run, a whitespace-bounded `or`), so the bar is the only
   boundary the regex finds.

Both clauses are necessary for that exactness. An earlier revision of this bundle
had only clause 1, and used it as a precondition; that was unsound, because specs
like `"List[int]"`, `"Tuple[str, ...]"`, `"Dict[str, str]"`, and `"str or int"`
satisfy clause 1 yet the real tokeniser splits them on the
bracket/comma/ellipsis/`or` delimiters — e.g. `"Dict[str, str]"` → real
`[True,False,True,False,True,False]` but bar-only reading `[True]`. With clause 2
(`no_other_sep`) added, `well_formed` marks exactly the region where the raw-bar
split with strict alternation equals the regex split + `filter(None,...)` +
per-piece `delims_re.match`.

That region is the realistic shape of a *union*-type field (the feature the issue
requests) and contains the F2P input `int | str` and specs like `bytes | str |
None` and `mod.Class | other.Class`. Nothing about it is a *domain* refinement any
more, because it is not a precondition: it is a validated reading, and the
obligations quantify over every input. There is likewise no
unexpressible-changed-op (kind-3) step — the changed tokenisation is expressed
deeply, in full, by `sep_end`/`next_sep`/`rendered`/`marks`. G-AX
(`axiom_check.py`) fuzzes over the FULL delimiter alphabet
`{ name chars, space, |, [ ] ( ) , . o r }` — not a hand-picked bar-only subset —
so it probes the `well_formed` boundary rather than assuming it: it confirms 0
mismatch of the bar-only reading on the in-shape inputs it reaches (15 in-shape
boundary + 10 off-shape boundary correctly rejected + 60 000 fuzz reaching the
bar-only shape, with the ~314 000 off-shape draws correctly skipped by
`well_formed`, + ~20 770 in-shape structured specs), and 0 mismatch of `rendered`
on all 266 595 inputs with no filter at all. Specs exercising the other delimiters
are outside the bar-only reading but INSIDE both obligations, and G-CONF measures
them there; the patch does not change `make_xrefs`'s behaviour on them (it only
adds the `\s*\|\s*` alternative), which is precisely what a domain-free
obligation lets the spec state about them.

## C. No kind-3 (unexpressible-changed-op) steps; no consumed axiom

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — recognising the bar as a delimiter and splitting on it — is modeled
**deeply** (`sep_end`/`next_sep` + the `rendered` fold + the verified
`render_nodes` loop, and in the weaker reading the same `sep_end`/`next_sep` +
the `marks` fold + the `split_render` loop),
not hidden behind an axiom about the function under change. There is **no
consumed `@ContractOnly` axiom**: the only callee relationships are the
**A-reference** ones — `rendered` / `marks` (and the retained bar-only `kinds`) ↔
the real `re.split`/`re.match` tokeniser — which G-AX and G-CONF validate the deep
models against (they are NOT consumed in the proof; the proof is self-contained
over the deep models).

## D. verify(model) ⇒ resolved

`render_nodes` verifies only if its output stream equals `rendered(ToSeq(target),
0)` (P7), i.e. — decoding the injective encoding of mapping.md §2 — the node list
whose k-th node has the kind and carries exactly the characters the patched
`make_xrefs` gives its k-th node, for EVERY specification. By R (str ↔ List[int];
Node ↔ `<code points> <kind marker>`) this is the node list the patched function
returns; by G-AX the deep model `rendered` equals the real
`re.split`/`re.match`/`innernode` node stream on all 266 595 generated inputs with
no domain restriction (A-reference), and G-CONF re-measures that equality against
the REAL called function on 254 104 inputs, 0 disagreements. Any impl satisfying
this obligation therefore renders, on every input, the node list gold renders — in
particular one cross-reference per named type interleaved with literal separators
carrying the separator text verbatim — and the gold patch resolves (G-RESOLVE).
The F2P assertion (two `pending_xref` children carrying exactly `int` and `str`,
with `" | "` a literal between them) is a decoded instance of P7 at
`target = "int | str"`.

The weaker §A obligation adds no strength to that argument; it restates the same
conclusion in terms of kinds, on the same full input domain, and is kept for the
directness of that reading:

`split_render` verifies only if its output kind sequence equals
`marks(ToSeq(target), 0)` (A7), i.e. one cross-reference per stretch of type-name
text interleaved with one literal per separator token, for EVERY specification. By
R (str ↔ List[int]; Node ↔ node-kind) this is the kind sequence the patched
`make_xrefs` produces; `marks` is the kind projection of `rendered`, which G-AX
validates == the real node stream on all 266 595 inputs with no domain restriction,
and G-CONF measures the kind sequence itself against the REAL called function on
all 254 104 inputs with no filter — 0 disagreements, 115 700 of them carrying a
non-bar separator — while additionally asserting on every input that the kind
sequence IS that projection (A-reference). Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the audited
deep model — and the gold patch resolves (G-RESOLVE).

The F2P input `int | str` gives `marks == [True,False,True]`, so a verifying impl
renders `int` and `str` as separate cross-references with the padded bar a literal
between them. The P2P-relevant specs `Tuple[str, ...]` / `Dict[str, str]` /
`List[int]` (exercised by `test_info_field_list`) are claimed too, with the kind
sequences the real patched function produces on them — e.g.
`"list[int] | None"` → `[True,False,True,False,False,True]`, six nodes, not the
three a bar-only reading would describe. That is what forbids an impl which is gold
on bar-only specifications and free elsewhere: there is no shape whose kinds the
spec leaves unstated, and no clause under which a branch guarded on
`not no_other_sep(...)` is dead for the verifier but live at runtime. The trust
points are exactly the two of PLAN §1.1: the deep-model soundness (G-AX over the
full delimiter alphabet, G-CONF against the called function) and refinement
fidelity (this document, G-EQ); there is no consumed-axiom trust point.
