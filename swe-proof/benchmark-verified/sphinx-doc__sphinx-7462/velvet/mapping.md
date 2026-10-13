# mapping.md — sphinx-doc__sphinx-7462

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = b3e26a6c851133b82b50f4b68b53692076574d13`, states the type
abstraction (the Lean↔Python bijection G-CONF and G-AX use to bridge values),
and records callee provenance.

Repo files under change: `sphinx/domains/python.py`, `sphinx/pycode/ast.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `renderSequenceTokens (elts : List (List (List Char)))` | the `ast.Tuple` branch of the nested `unparse` in `_parse_annotation` — `sphinx/domains/python.py:116` (body lines 117–122 at base) | modeled changed function #1: assembles the **display-token list** for a comma-separated sequence |
| `renderSequenceText (elts : List (List Char))` | the `ast.Tuple` branch of `unparse` — `sphinx/pycode/ast.py:116` (body line 117 at base) | modeled changed function #2: assembles the **source-text rendering** of a comma-separated sequence |
| `seqTokens (elts : List (List (List Char)))` | the post-patch body of the `ast.Tuple` branch in `python.py` | pure spec: the token list as a function of member count |
| `seqText (elts : List (List Char))` | the post-patch body of the `ast.Tuple` branch in `ast.py` | pure spec: the source text as a function of member count |

The per-member renderings (`unparse(elem)` in `python.py`, `unparse(e)` in
`ast.py`) are produced by the surrounding recursive renderer, which **neither
patch changes**. They are therefore abstracted as opaque already-rendered member
images (the inputs `elts`); there is no callee whose contract the proof consumes
(§3).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

### 2.1 Function #1 — `renderSequenceTokens` (`python.py`, a node list)

| repo reality | Lean carrier | bijection |
|---|---|---|
| one rendered display node (`nodes.Text` / `pending_xref` / `desc_sig_punctuation`) | `List Char` (its text content) | a node `n` ↔ `n.astext()`-shaped `List Char`; the node's *type* is fixed by the producer (member nodes come from the unchanged renderer; the separators/parens this op emits are `desc_sig_punctuation`, §2.3) |
| one member's rendering `unparse(elem)` (a `List[Node]`) | `List (List Char)` (a list of node texts) | element-wise the row above; preserves order and node count |
| the member list (`unparse` over `node.elts`) | `List (List (List Char))` | element-wise the row above; `len(node.elts)` ↔ `elts.length`; empty tuple ↔ `[]` |
| the returned `List[Node]` | `List (List Char)` (the flattened token list, one entry per node) | element-wise the node row; cardinality preserved (so a 2-node `( )` empty rendering is two entries, never one) |
| the separator node `desc_sig_punctuation('', ', ')` | the single token `", ".toList` placed *between* members | `desc_sig_punctuation('', ', ')` ↔ `[',', ' ']` |
| the empty-pair nodes `desc_sig_punctuation('', '(')`, `desc_sig_punctuation('', ')')` | the two tokens `"(".toList`, `")".toList` | each ↔ its one-char text |

### 2.2 Function #2 — `renderSequenceText` (`ast.py`, a string)

| repo reality | Lean carrier | bijection |
|---|---|---|
| one member's rendering `unparse(e)` (a Python `str`) | `List Char` | `s` ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; empty `str` ↔ `[]` |
| the member list (`unparse` over `node.elts`) | `List (List Char)` | element-wise the row above; `len(node.elts)` ↔ `elts.length`; empty tuple ↔ `[]` |
| `", ".join(parts)`, `"()"` | `List.intercalate ", ".toList` and `"()".toList` | `str.join` ↔ `List.intercalate` (separator between adjacent members, none at the ends; valid for ≥ 1 part); the literal `", "` ↔ `[',', ' ']`; `"()"` ↔ `['(', ')']` |
| the returned `str` | `List Char` | as the member row |

### 2.3 Why the member images are opaque inputs

Both branches read each member only through the unchanged recursive renderer and
never inspect the member's content; the patched behavior is a pure function of
(a) how many members there are and (b) those members' rendered images. So each
member image is taken as an arbitrary opaque input, exactly as a consumer-supplied
value — the spec assumes nothing about it. The only nodes the operation *creates*
are the separators and the empty-pair punctuation, all `desc_sig_punctuation`;
G-CONF confirms their type against the real patched code.

`str.join` ↔ `List.intercalate`: for `parts` of length ≥ 1,
`SEP.join(parts) == intercalate SEP parts` (separator between adjacent elements,
none at the ends). The 0-member case is handled by its own branch and never
reaches the join.

## 3. Callee provenance

**No axiomatized callees; no deep-model references.** The only sub-computation
either branch performs is the recursive render of each child — the unchanged
renderer. Its output is taken as an arbitrary opaque input (`elts`), so:

- there is **no `axiom`** (A-consumed): the proof consumes no callee contract;
- there is **no deep-model reference** (A-reference): nothing unchanged is
  re-modeled and validated against a real callee — the member images pass through
  verbatim.

Consequently `axiom_check.py` (G-AX) has no callee obligation to discharge; it is
shipped as an explicit no-op that documents the absence and exits 0.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`7462`** so the
consumer-side verdict is reproducible. It runs two differential checks, one per
modeled function:

- **#1** transliterates `seqTokens`/`renderSequenceTokens` and diffs it against
  the real patched `_parse_annotation` (driven on top-level comma-separated
  annotations, including the empty `"()"`), comparing the resulting nodes by
  `(node_class_name, astext)`. Member images are obtained from the same real
  `_parse_annotation` on each member's source, so the shadow reuses the genuine
  recursive renderer and isolates only the changed tuple-assembly.
  **Domain restriction:** the modeled operation assembles already-rendered member
  images, so its domain is exactly the tuples whose members the surrounding
  renderer can render. The inner `unparse` of `_parse_annotation` at `base_commit`
  supports only Attribute/Index/List/Module/Name/Subscript/Tuple nodes; a member
  parsing to anything else (e.g. an `ast.Constant` like `None`/`True`/`1`/`...`)
  raises `SyntaxError` inside the tuple loop, aborting the modeled `ast.Tuple`
  branch entirely so `_parse_annotation` returns its UNCHANGED outer fallback
  `[make_xref(annotation)]` (one `pending_xref` over the whole source). Such
  inputs are outside the modeled operation's domain and are excluded two ways:
  the member atom pool contains only renderer-supported sources, and `check_site1`
  structurally skips any input whose oracle is that single-`pending_xref` fallback.
  The empty-tuple case `"()"` and every renderer-supported member still reach the
  real tuple branch and are checked. (Site #2's `ast.unparse` DOES handle
  `Constant`, so #2 needs no such restriction.)
- **#2** transliterates `seqText`/`renderSequenceText` and diffs it against the
  real patched `sphinx.pycode.ast.unparse` on fuzzed `ast.Tuple` nodes, with
  member images taken from the same `unparse` (as in the sibling instance).

Both shadows are pure R/I (no A-tagged callee to leave as a real call, §3).
