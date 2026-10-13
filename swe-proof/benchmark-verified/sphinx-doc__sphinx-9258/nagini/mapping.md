# mapping.md — sphinx-doc__sphinx-9258

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 06107f838c28ab6ca6bfc2cc208e15997fcb2146`, states the type
abstraction, and gives the provenance of the deep-model reference (the real
tokeniser the deep model is validated against by G-AX).

Repo file under change: `sphinx/domains/python.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `render_nodes(target)` | `PyXrefMixin.make_xrefs(self, rolename, domain, target, ...)` — `sphinx/domains/python.py:304` (body lines 307-324) | **the primary obligation**: the modeled changed function, pinning the WHOLE ordered node stream — node count, per-node kind, per-node exact carried text — on EVERY specification, no domain restriction |
| `rendered(s, i)` *(deep model — A-reference)* | the `re.split(delims, target)` + `filter(None, ...)` + per-piece `delims_re.match(...)` split/classify/render (`python.py:307-324`), with each produced node's text being the `sub_target` handed to `innernode(sub_target, sub_target)` (`util/docfields.py:70`, reached from `python.py:319`) or to `make_xref` (`python.py:321`) | pure spec: the node stream, laid out as `<the node's code points> <kind marker>` per node (−1 cross-reference, −2 literal separator) closed by −3 |
| `next_sep(s, i)` | the position of the leftmost delimiter match `re.split` finds at or after `i` (the whole alternation of `python.py:307`, not just the added bar) | pure spec: where the next separator token starts; the text before it is one cross-reference piece |
| `sep_end(s, i)` | the extent of that delimiter match — the four alternatives of `python.py:307` in the regex's own left-to-right preference order (`\s*[\[\]\(\),](?:\s*or\s)?\s*`, `\s+or\s+`, the added `\s*\|\s*`, `\.\.\.`) | pure spec: one past the separator token that starts at `i`, or −1 if none does |
| `next_sep_idx` / `sep_end_idx` / `copy_span` | the executable counterparts of `next_sep` / `sep_end` and the per-node text copy | verified impl machinery |
| `split_render(target)` | the same `PyXrefMixin.make_xrefs` (`python.py:304`) | **retained, strictly weaker** kind-only reading: the `List[bool]` node-kind sequence, stated for EVERY specification with no domain restriction; kept because *one link per named type, one literal per separator* is the most direct reading of the change |
| `marks(s, i)` *(deep model — A-reference)* | the same split/classify (`python.py:307-324`), read for each produced node's KIND only — `bool(delims_re.match(piece))` at `python.py:318` | pure spec: the rendered-node *kind* sequence over the full delimiter vocabulary; the kind projection of `rendered`, exact on EVERY input |
| `kinds(s, i)` *(retained bar-only reading — A-reference)* | the `re.split(delims, target)` + `filter(None, ...)` + per-piece `delims_re.match(...)` classification (`python.py:307-324`) restricted to specifications whose only separator is the bar | pure spec: the strictly-alternating kind sequence of a bar-only split. Exact on the `well_formed` shape and NOT elsewhere, so it is no longer any function's postcondition; it survives as the validated bar-structure reading (G-AX §3.1) |
| `first_bar(s, i)` | the position of the vertical-bar delimiter inside `re.split` (the `\s*\|\s*` alternative the patch adds at `python.py:307`) | pure spec: the next bar split point |
| `seg_text(s, i, j)` / `strip_left` / `strip_right` | the per-segment text handed to `make_xref(sub_target)` (`python.py:321`) after the `\s*\|\s*` delimiter has consumed the surrounding whitespace | pure spec: the trimmed type name of a bar-separated segment (a retained reading of the name, not part of the modeled output — the node's carried text is the UNTRIMMED span, pinned by `rendered`) |
| `well_formed(s, i)` / `no_other_sep(s, i)` | (no repo symbol) the bar-only SHAPE: every bar-separated segment names a non-empty type AND the vertical bar is the only separator the regex finds (no `[ ] ( ) , ...` and no whitespace-bounded `or`) | pure spec: the predicate marking where the bar-only `kinds` reading is an exact, strictly-alternating tokenisation. **Not a precondition of any modeled function** — both obligations are domain-free |
| `slice_trim` / `first_bar_idx` | the executable counterparts of `seg_text` / `first_bar` (impl helpers) | verified impl machinery |

The single changed line at `python.py:307`:
```
- delims = r'(\s*[\[\]\(\),](?:\s*or\s)?\s*|\s+or\s+|\.\.\.)'
+ delims = r'(\s*[\[\]\(\),](?:\s*or\s)?\s*|\s+or\s+|\s*\|\s*|\.\.\.)'
```
adds `\s*\|\s*` to the delimiter alternation, so the vertical bar (with optional
surrounding whitespace) becomes a split point and each bar-separated type name
is rendered as its own cross-reference.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the `target` argument) | `List[int]` of Unicode code points | `target[k]` ↔ `ord(target[k])`; `len` ↔ `len`; `'|'` ↔ `124`; `' '` ↔ `32` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materialises the list as a `PSeq`; `take`/`drop`/`len`/`[i]` mirror slice/`len`/index |
| `List[Node]` (the rendered output) — PRIMARY | `List[int]` node *stream* | the node list is written out node by node in emission order as `<the code points of that node's text> <kind marker>`, marker −1 for a `pending_xref` cross-reference (the `make_xref(sub_target)` branch, `python.py:321`) and −2 for the literal separator (the `contnode or innernode(sub_target, sub_target)` branch, `python.py:319`), the whole stream closed by −3. Code points are non-negative, so no marker can be read as carried text: the stream is an INJECTIVE encoding of the node list, and one sequence equality therefore pins node count, per-node kind AND per-node exact text. Nothing is abstracted away. |
| `List[Node]` (the rendered output) — retained weaker view | `List[bool]` of node *kinds* | the k-th rendered node ↔ `Result()[k]`: `True` for a `pending_xref` cross-reference, `False` for the literal separator. This view abstracts the node CONTENT to its kind; it is a projection of the stream above and is kept for the directness of its *one link per named type* reading. Stated on the same full input domain as the stream. |
| `re.split` + `filter(None,...)` + `delims_re.match` + the per-node text | the deep `rendered` fold (full delimiter vocabulary via `next_sep`/`sep_end`) | exact on EVERY input, no domain (G-AX §3.2, G-CONF) |
| `re.split` + `filter(None,...)` + `delims_re.match`, kinds only | the deep `marks` fold (same vocabulary via `next_sep`/`sep_end`) | exact on EVERY input, no domain (§3.3, G-CONF) |
| `re.split` + `filter(None,...)` + `delims_re.match` | the `kinds` fold (raw-bar split, strict alternation) | exact on the bar-only `well_formed` shape and there only (G-AX, §3.1); a retained reading, not an obligation |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`; the
specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Deep-model reference (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `kinds` bar-only reading ↔ the real `re.split`/`re.match` tokeniser
**Callee:** the stdlib `re` module, with the delimiter pattern the gold patch
installs (`python.py:307`). There is **no consumed `@ContractOnly` axiom**: the
changed tokenisation is modeled DEEPLY by the `@Pure` folds in the `pure` region.
`kinds` (with `first_bar`) is the *bar-only* one of those readings, validated
**== the real tokeniser** out-of-band by axiom_check.py (G-AX) exactly where it is
exact. It states the strict alternation a bar-separated union renders to, and it
is **no postcondition**: the kind obligation `split_render` carries is the
domain-free `marks` of §3.3, because `kinds` is *false* of the real function
outside the shape below (`'list[int] | None'` renders 6 nodes; `kinds` describes
3), so stating it everywhere would over-claim rather than repair.

The patched `make_xrefs` does, for each non-empty split piece:
`is_separator = bool(delims_re.match(piece))`, rendering a literal node for a
separator piece and a cross-reference for every other piece. The regex splits on
ANY of its delimiters — `[ ] ( ) ,`, the whitespace-bounded `or`, the added
`\s*\|\s*` bar, and `...` — and `filter(None,...)` drops empty pieces. The
bar-only `kinds` model therefore equals the real tokeniser only on a shape that
excludes the other delimiters AND empty segments. That shape is the two-clause
**`well_formed`**:
- (a) every bar-separated segment names a non-empty type (no leading/trailing/
  consecutive bars whose empty pieces `filter(None,...)` would drop); AND
- (b) **`no_other_sep`**: the spec contains none of the other delimiter triggers
  (`[ ] ( ) ,`, a `...` run, a whitespace-bounded `or`), so the vertical bar is
  the only boundary the regex finds.

On this shape the regex split on `\s*\|\s*` followed by `filter(None,...)`
produces exactly the strictly-alternating piece sequence *name, bar-run, name,
bar-run, …*, with each bar-run classified as a separator and each name as a
cross-reference. That is precisely `kinds(s, 0) = [True, False, True, …]` of
length `2*bars + 1`. The realistic shape of a *union*-type field — e.g.
`int | str`, `bytes | str | None`, `mod.Class | other.Class` — has it.

Off that shape (leading/trailing bars, consecutive bars, empty segments, OR any of
the other delimiters `[ ] ( ) , or ...` — e.g. `List[int]`, `Tuple[str, ...]`,
`Dict[str, str]`, `str or int`) the regex finds extra split points and/or
`filter(None,...)` drops empty pieces, so the bar-only alternation is not the real
kind sequence, and `kinds` is therefore not asserted of those inputs anywhere. It
is not the shape of the claim, either: `well_formed` gates NO obligation. What
those inputs render to is stated in full by `rendered` (§3.2) and, for the kinds
alone, by `marks` (§3.3) — both of which are exact on all of them. Clause (b) was
ADDED after the first audit found the original one-clause version unsound (it
admitted bracket/comma/ellipsis/`or` specs on which the bar-only reading disagreed
with the real tokeniser), so today `well_formed` marks exactly the region where
`kinds` may be relied on.

**Soundness check (G-AX):** `axiom_check.py` reproduces the patched delimiter
regex verbatim and runs the real `re.split`/`re.match` over the FULL delimiter
alphabet `{type-name chars, whitespace incl. non-ASCII, |, [ ] ( ) , . o r}` —
deliberately INCLUDING every other delimiter so the fuzz actually exercises the
`well_formed` boundary rather than a hand-picked bar-only subset. For the
bar-only reading it checks 22 in-shape boundary inputs + 42 off-shape boundary
inputs (asserting `well_formed` correctly REJECTS each, e.g.
`Tuple[str, ...]`, `Dict[str, str]`, `str or int`) + 60 000 in-shape fuzz strings
(146 531 further draws correctly skipped as off-shape) + 15 343 in-shape
structured specs (44 657 skipped), asserting `model_kinds == real_kinds` on every
in-shape input (0 mismatches). It imports only the standard-library `re` module
(the exact module the patched code calls). Exit 0 iff sound; confirmed RC=0 in the
pinned eval container with the gold patch applied.

### 3.2 `rendered` deep model ↔ the real node stream (no domain)
**Callee:** the same stdlib `re` module plus the one text-carrying call each
produced node makes. There is again **no consumed `@ContractOnly` axiom**: the
node stream is modeled DEEPLY by the `@Pure` folds `rendered` / `next_sep` /
`sep_end`.

`sep_end(s, i)` reproduces the delimiter alternation of `python.py:307` *as an
alternation, in the regex's own preference order* — the bracket/comma group with
its optional `or` first, then the whitespace-bounded `or`, then the added
`\s*\|\s*`, then `...` — so the model recognises EVERY separator the real regex
finds, not only the bar. `next_sep` is therefore the leftmost delimiter match, and
`rendered` walks the string exactly as `re.split` + `filter(None, ...)` do:
- the stretch before a delimiter, when non-empty, is one cross-reference carrying
  those characters VERBATIM (this is the `sub_target` the real code passes to
  `make_xref`, `python.py:321`);
- the delimiter match itself is one literal separator carrying its own characters,
  padding included (the `sub_target` passed to `innernode(sub_target, sub_target)`
  at `python.py:319`, i.e. `Field.make_xref`'s `contnode or innernode(target,
  target)`, `util/docfields.py:70`);
- an empty stretch emits NO node — the model's counterpart of `filter(None, ...)`.

Because every separator is in the vocabulary, **this obligation carries no domain
precondition**: bracket, comma, `or`, ellipsis, adjacent separators, and any
mixture of them with the bar are all inside the claim. That is the difference that
matters against §3.1: a kind reading stated only where the bar is the sole
separator would leave the rendered output on every other shape unconstrained, so
`kinds` is kept as a reading and `marks` (§3.3) is what the kind obligation says.

**Soundness check (G-AX):** the same `axiom_check.py` run asserts the `rendered`
stream — node count, per-node kind, and per-node exact text — equals the real
`re.split`/`re.match` tokenisation on **all 266 595 generated inputs with NO
domain restriction**, 0 mismatches.

### 3.3 `marks` deep model ↔ the real node KIND sequence (no domain)
**Callee:** the same stdlib `re` module. `marks` is `rendered`'s case analysis with
the carried text dropped: same `next_sep`/`sep_end` vocabulary, same three exits,
emitting `True` for a stretch of type-name text and `False` for a separator token.
It is therefore the kind projection of §3.2's node stream, and it is what
`split_render` must return: `Ensures(ToSeq(Result()) == marks(ToSeq(target), 0))`,
for EVERY specification.

Why it is true of the real patched function: the delimiter alternation
(`python.py:307`) is a **capturing** group, so `re.split` returns each delimiter as
its own piece; `filter(None, ...)` (`python.py:314`) drops only empty pieces; and
each surviving piece becomes exactly one node whose kind is decided by
`if delims_re.match(sub_target)` (`python.py:318`) — literal separator at 319,
cross-reference at 321. `marks` is precisely that predicate sequence, so one
equality pins the node COUNT and that no separator is ever rendered as a link —
i.e. *one link per named type* — on bracket, comma, `or` and ellipsis
specifications as well as bar ones.

**Soundness check (G-CONF):** `conformance_check.py` compares `split_render`'s
verbatim impl shadow against the real patched function's node kinds on every input
it draws, with NO filter, and additionally asserts the kind sequence IS the
projection of the node stream on each of them (a kind sequence that drifted from
the stream the same file pins would be a contradiction inside one model). Counts
under §G-CONF below.

## G-CONF — differential conformance (model vs the REAL patched function)

**Script:** `conformance_check.py`. **Pinned seed: `SEED = 92580`.**

**Shadow (provenance `direct`).** The model IS Python, so the shadow is the
`# impl-start`/`# impl-end` regions of `render_nodes`, `next_sep_idx`,
`sep_end_idx`, `strip_left_idx`, `copy_span`, `split_render`, `first_bar_idx` and
`slice_trim` copied VERBATIM with only the contract calls (`Requires`, `Ensures`,
`Invariant`, `Assert`, `Acc`, `Old`) and the `# invariants-start`/`-end` blocks
deleted — no transliteration, no renaming, no restructuring. The loop shapes, the
`while True` + `break`, the `j >= n` tests, the `+ 0` index readings and the append
order are byte-for-byte the model's; the single edit stripping forces is an
explicit `pass` in the four `else:` branches (two in `render_nodes`, two in
`split_render`) that hold nothing but an `Assert`. Both top-level impls still call
their real helpers (`render_nodes` and `split_render` → `next_sep_idx` →
`sep_end_idx` → `strip_left_idx`, plus `copy_span`), so every helper impl region is
exercised rather than inlined away; `first_bar_idx` and `slice_trim` — the
bar-position and trimmed-segment helpers, which the kind scan does not use — are
called directly once per input and checked against `first_bar` / `seg_text`. The 12
`@Pure` helpers the regions and their postconditions depend on (`is_space`,
`first_bar`, `kinds`, `strip_left`, `strip_right`, `seg_text`, `no_other_sep`,
`well_formed`, `sep_end`, `next_sep`, `rendered`, `marks`) are copied verbatim
minus contracts as well, and are used for the self-consistency assertions
`render_nodes(cps) == rendered(cps, 0)` and `split_render(cps) == marks(cps, 0)`,
which trip if any shadow was mis-copied.
`PSeq` is an immutable-tuple shim (`take`/`drop`/`+`/`len`/`[]`/`==`); `ToSeq`
materialises one. No `@ContractOnly` callee exists in this bundle (`axioms: []`),
so nothing is assumed rather than exercised.

**Oracle (CALLED, not transliterated).** The real patched
`sphinx.domains.python.PyXrefMixin.make_xrefs` (`sphinx/domains/python.py:304`,
changed line 307 — §1), driven through a real `PyField`. The gate applies
`patch.diff` to /testbed first; the script applies no diff and hardcodes no
regex. Startup guards assert `PyField.make_xrefs is PyXrefMixin.make_xrefs` and
that `\s*\|\s*` is present in `inspect.getsource`, so a failed patch-apply
cannot read as a green run. (The velvet/lean siblings transliterate the
tokeniser because Lean cannot call it; here `re.split`/`re.match` are reached by
calling the real method. Only the `BuildEnvironment` argument is stubbed, and it
is consumed solely by the `make_xref` callee — strictly after the split/classify
logic under specification has fixed every node kind.)

**Type bridge (§2 inverted).** Forward `str -> List[int]`: `[ord(ch) for ch in
target]`.

Backward, node KIND: node k is a cross-reference iff
`isinstance(node, addnodes.pending_xref)` (the `make_xref` branch,
`python.py:321`), else the literal separator (the `delims_re.match` branch,
`python.py:319`).

Backward, node TEXT — this is what makes the payload OBSERVED rather than assumed.
The real function takes the factory each node's text is built from as an ARGUMENT
(`innernode`) and calls it exactly once per produced node with that node's own
piece of the input: in the separator branch directly (`python.py:319`), in the
cross-reference branch through `Field.make_xref`'s
`refnode += contnode or innernode(target, target)` (`util/docfields.py:70`). The
check passes a RECORDING stand-in as `innernode` and reads the k-th node's text
off the k-th call; `len(calls) == len(nodes)` is asserted on EVERY input, so
"exactly once per node, in order" is measured, not assumed. The stand-in returns
the same `emphasis` node the default factory would and the logic under
specification never inspects the result, so it cannot perturb what is measured.
Independently, `node.astext()` is compared to the recorded text on every node;
they coincide except in the one documented case the check states exactly rather
than tolerating — when a cross-reference piece starts with `.` or `~` the
`make_xref` CALLEE rewrites the DISPLAYED text to `piece[1:]` /
`piece.split('.')[-1]` (`python.py:293-301`). The modeled observable is each
node's piece of the input (the tokenisation, which is what the change decides),
with that downstream display rewrite pinned as a known exact function of the
piece.

A node list is encoded into the model's carrier as each node's code points
followed by −1 (cross-reference) or −2 (literal separator), closed by −3. Code
points are non-negative, so the encoding is injective: one model sequence means
exactly one node list.

**Inputs — 254 104, seed 92580.** 32 boundary + 4 000 structured union specs
+ 100 000 bar-only-shape fuzz + 150 072 full-domain (unfiltered) inputs. Fuzz is
drawn over the FULL delimiter alphabet *including the non-ASCII whitespace the real
`\s` class matches* (TAB, NL, VT, FF, U+001C, NEL, NBSP, EM/IDEOGRAPHIC SPACE,
NNBSP, U+2028); the full-domain stratum adds the shapes `well_formed` rejects —
brackets, commas, `or`, `...`, bare/leading/trailing/doubled bars,
whitespace-only segments, the empty string, and `.`/`~`-prefixed targets. 28
off-shape boundary inputs are asserted REJECTED by `well_formed`, so that
predicate is shown to discriminate rather than admit everything. **No input is
filtered out of either comparison** — neither obligation has a domain clause.

**Observables — both drive the exit code, both on the whole input set.**
- PRIMARY: the whole node STREAM pinned by `render_nodes`'s postcondition
  `ToSeq(Result()) == rendered(ToSeq(target), 0)` — node count, per-node kind AND
  per-node exact carried text — checked on **all 254 104 inputs with NO domain
  filter**, of which **115 700 carry a non-bar separator**.
- The node-KIND sequence pinned by `split_render`'s postcondition
  `ToSeq(Result()) == marks(ToSeq(target), 0)` — node count and per-node kind —
  checked on **all 254 104 inputs with NO domain filter**, the same 115 700
  non-bar-separator inputs included, plus an assertion on every input that the
  kind sequence IS the kind projection of the node stream.

Nothing is recorded as a merely-secondary observable. An earlier version of this
script measured the cross-reference payload (`slice_trim`/`seg_text`) but let it
print WITHOUT affecting the exit code, because the payload was then outside the
modeled output; the divergences it printed were real (the trimmed segment is not
the text the real node carries). The payload is now INSIDE the modeled output via
the node stream, and the model of it is the untrimmed span, so it is measured as a
first-class observable. The old `seg_text`-equals-carried-text comparison is
deliberately GONE rather than downgraded, because that equality is false and the
node stream states the true relation instead; `seg_text` survives as the retained
trimmed-name reading, checked against its executable counterpart `slice_trim`.

**Branch coverage (measured, not asserted).** All four `render_nodes` branches
taken: 134 497 inputs with a separator, 214 227 ending in text, 39 877 ending at
a separator, 62 169 with an empty leading/adjacent piece (the `filter(None, ...)`
case where no cross-reference is emitted). All four `split_render` branches taken:
214 227 ending in a cross-reference, 39 877 ending at a separator or empty,
100 362 emitting text before a separator, 34 135 emitting a separator with no text
in front of it.

### Verdict: **G-CONF = pass — 0 disagreements on all 254 104 inputs**

Wall time 90.2 s against the gate's 1800 s container cap, measured by running this
script in the pinned eval image with `patch.diff` applied, exactly as the gate runs
it. `model.py` was not edited to reach this and no input domain was narrowed to
route around a disagreement; the two divergence classes an earlier revision
recorded (a whitespace-bounded `or` escaping `no_other_sep`, and non-ASCII
whitespace beside a bar) were closed at the source by making `is_space` the FULL
whitespace set — the same predicate the real `\s` class matches — and both are now
covered densely by the unicode-whitespace fuzz alphabet above rather than excluded
from it. The `meta.json` G-CONF stamp predates the domain-free kind obligation and
is due a re-run; the counts above are from the run described in this paragraph.
