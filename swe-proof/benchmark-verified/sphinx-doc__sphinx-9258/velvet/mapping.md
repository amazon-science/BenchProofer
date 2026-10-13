# mapping.md — sphinx-doc__sphinx-9258

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 06107f838c28ab6ca6bfc2cc208e15997fcb2146` (sphinx 4.1), states the
Lean↔Python type abstraction (the bijection G-CONF and G-AX use to bridge the
two value domains), and gives the provenance of the one axiom and the deep-model
reference.

Repo file under change: `sphinx/domains/python.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `splitUnionType (target : List Char)` | `PyXrefMixin.make_xrefs(self, rolename, domain, target, …)` — `sphinx/domains/python.py:304` (body 307-326) | the modeled changed function (the type-field tokenizer) |
| `Token` (`text : List Char`, `linked : Bool`) | one element of the `results` list `make_xrefs` returns — either a cross-reference node (`make_xref(...)`, `linked = true`) or a verbatim separator node (`contnode/innernode`, `linked = false`) | result node, projected at the split+classify boundary to (the raw `re.split` piece string, is-it-handed-to-`make_xref`) — see the `make_xref` row for the boundary |
| `splitTokens (pipeSep : Bool) (s : List Char)` *(deep model — A-reference)* | the `re.split(delims, target)` + `filter(None, …)` + per-piece `delims_re.match` classification (`python.py:307-326`) | pure spec: the full delimiter-split-and-classify pipeline; deep model of the unchanged `re` engine, parameterized by whether the bar separator is in the delimiter set; validated `splitTokens true == re.split(new_delims)` by axiom_check.py (G-AX), NOT consumed as an axiom |

There is **no consumed axiom** in this bundle (the `axioms` region is empty). The
per-token callee `make_xref` (`python.py:285`, called at `python.py:322`) is
**unchanged** by the patch and is handled as an **R-refinement**, not an axiom:
see §2 (`make_xref` row) and §3.2.

The single pre-patch→post-patch change the diff makes (refinement audit only, not
in the consumer spec view): the regex literal `delims` at `python.py:307` gains a
`\s*\|\s*` alternative.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the Lean
value domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `target` (Python `str`), and each `sub_target` piece | `List Char` | `s` (str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; str slice ↔ `List.take`/`List.drop`; empty str ↔ `[]` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| `re` `\s` character class | `isWS : Char → Bool` | `delims` is a `str` pattern, so `\s` matches the full Unicode whitespace set: the 29 code points U+0009–U+000D, U+001C–U+001F, U+0020, U+0085, U+00A0, U+1680, U+2000–U+200A, U+2028, U+2029, U+202F, U+205F, U+3000. `isWS c` enumerates exactly this set (so e.g. a no-break space around the bar, `int\xa0|\xa0str`, is part of the separator, as in the real engine). |
| `[\[\]\(\),]` character class | `isBracket : Char → Bool` | the five literals `[ ] ( ) ,`. |
| `results` list of docutils nodes | `List Token` | order-preserving. Each piece kept by `filter(None, …)` becomes one node; `delims_re.match(piece)` true ⇒ a verbatim separator node (`linked = false`); else a `make_xref` node (`linked = true`). The Token projection is taken at the split+classify boundary: (the raw piece string, is-it-handed-to-`make_xref`). The F2P test observes, per node, its text and whether it is a `pending_xref` (link) vs a `literal_emphasis` (separator); on the F2P type fields the linked pieces are plain member names (no `.`/`~` prefix), so there the node text equals the raw piece text. |
| `make_xref(...)` per-token call (R) | the `linked = true` token carries the sub-target piece string — the exact argument `make_xrefs` hands to `make_xref` — verbatim | **R-refinement at the call boundary, not an axiom.** The modeled observable stops at the `make_xrefs` split+classify boundary: `Token.text` is the sub-target string passed to `make_xref`, which is exactly the `re.split` piece, unmodified between the split and the call (re-checked by G-AX §3.2). `make_xref` itself (unchanged by the patch) is downstream presentation OUTSIDE the modeled boundary: it builds a `pending_xref` from that string, and for a sub-target with a leading `.`/`~` it applies its pre-existing short-name display handling, so the visible text/`reftarget` of such a node differ from the raw piece. That handling is byte-identical pre- and post-patch, so it carries no discriminating content for this fix; the spec pins the *splitting + classification*, which is what changed. On the F2P inputs (`int`, `str`) no such prefix occurs, so the rendered text/`reftarget` equal the piece verbatim there, which is how the Token stream is read against the test's observed nodes. |

Lean `List Char` indexing/slicing is total and sound; the carrier is `List Char`
because the operation is a per-character left-to-right scan.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `splitTokens` deep model ↔ `re.split` + classify (A-reference)

**Callee:** the CPython `re` engine, invoked as
`re.split(delims, target)` then `filter(None, …)` then `delims_re.match(piece)`,
where post-patch
`delims = r'(\s*[\[\]\(\),](?:\s*or\s)?\s*|\s+or\s+|\s*\|\s*|\.\.\.)'`.

The split is NOT axiomatized: `make_xrefs` calls the unchanged `re` library, and
the only thing that changed is the *delimiter pattern data*. The behavior of that
pattern is a deterministic maximal-munch scan, modeled **deeply** by
`splitTokens` / `stepLen` / `delimLen` (pure region). Because the capturing group
`(…)` makes `re.split` interleave content and delimiter pieces, and
`delims_re.match(piece)` re-tags each kept piece, the classification is exactly
the parity of `re.split`'s output (even index = content, odd = delimiter);
`splitTokens` reproduces this with `linked = (delimLen s == 0)`.

The pattern's four alternatives, tried left-to-right with greedy `\s*`:
- `\s*[\[\]\(\),](?:\s*or\s)?\s*` — a bracket/comma with optional ` or ` and
  surrounding whitespace (modeled in `delimLen`'s bracket branch);
- `\s+or\s+` — the word separator (`delimOr`);
- `\s*\|\s*` — the vertical-bar separator (`delimPipe`); **this alternative is the
  union-type separator the issue requests** (problem statement: `bytes | str`);
- `\.\.\.` — a literal ellipsis (`delimEllipsis`).

`splitTokens` advances by `stepLen`: a delimiter run when one matches at the
front (`delimLen > 0`), else the maximal content run up to the next delimiter
(`contentLen`). Validated `splitTokens == the real re.split-and-classify` by
axiom_check.py over boundary + 50 000 fuzz inputs (G-AX). This is an
**A-reference**, not a consumed axiom: the proof of `splitUnionType` unfolds
`splitTokens` directly; G-AX guards that the deep model equals the real `re`
behavior.

### 3.2 `make_xref` text-preservation (R-refinement, re-checked by G-AX)

**Callee:** `PyXrefMixin.make_xref(self, rolename, domain, sub_target, …)`
(`python.py:285`), unchanged by the patch. It is NOT axiomatized — it is an
R-refinement (§2) **at the call boundary**: each `linked = true` token carries,
verbatim, the sub-target piece string that `make_xrefs` hands to `make_xref` —
i.e. the `re.split` piece with no rewriting between the split and the call.
That call-argument identity is what G-AX §3.2 re-checks. What `make_xref` does
*after* the boundary (building the `pending_xref`, including its pre-existing
short-name display handling for sub-targets with a leading `.`/`~`, which
rewrites the visible text/`reftarget` of such a node) is downstream presentation
outside the modeled boundary and is byte-identical pre- and post-patch, so it
carries no discriminating content for this fix. The spec pins the part that
**changed** — the split + classification — and treats the boundary string as the
Token text. On the F2P type fields the linked pieces are plain member names
(no `.`/`~` prefix), so there the rendered node text/`reftarget` coincide with
the boundary string, which is how the Token stream is read against the test.

**Soundness check (G-AX):** `axiom_check.py` validates the load-bearing claim —
(a) the deep model `splitTokens true` equals the real `re.split(new_delims)` +
`filter(None,…)` + `delims_re.match` classification on the CPython `re` engine
(A-reference) — over boundary + 50 000 fuzz inputs, and (b) sanity-checks the
`make_xref` text-preservation R-claim by asserting that for each non-separator
piece the value `re.split` hands to `make_xref` is exactly the sub-target text
(no rewriting happens before the call). Imports only stdlib `re`. Exit 0 iff every
obligation holds.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`9258`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `splitTokens`/`stepLen`/`delimLen` (R/I-tagged ops) to Python and
compares the resulting (text, linked) token stream against `patch.diff`'s
behaviour — the patched `make_xrefs` run on the real `re` engine, reading each
emitted node's text and link-ness. The A-tagged callee `make_xref` is left as the
real repo callee (its node text), not the axiom model.
