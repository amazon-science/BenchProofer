# mapping.md — sphinx-doc__sphinx-9367

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 6918e69600810a4664e53653d6ff0290c3c4a788`, states the type
abstraction (the Lean↔Python bijection G-CONF and G-AX use to bridge values),
and records callee provenance.

Repo file under change: `sphinx/pycode/ast.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `renderSequence (elts : List (List Char))` | `_UnparseVisitor.visit_Tuple(self, node)` — `sphinx/pycode/ast.py:215` (body lines 216–219 at base) | the modeled changed method (source renderer for a parenthesized comma-separated sequence) |
| `renderTuple (elts : List (List Char))` | the body of `visit_Tuple` post-patch (`ast.py:216–223`) | pure spec: the rendering as a function of member count |
| `elts : List (List Char)` | `[self.visit(e) for e in node.elts]` — the already-rendered text of each member | the operation's inputs (see §3) |

The per-member rendering `self.visit(e)` is performed by the surrounding
recursive `_UnparseVisitor.visit` dispatch, which the patch does **NOT** change.
It is therefore abstracted as opaque already-rendered member text (the input
`elts`); there is no callee whose contract the proof consumes (§3).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the rendered text `self.visit(e)` of one member (a Python `str`) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; empty `str` ↔ `[]` |
| the member list `[self.visit(e) for e in node.elts]` (a Python `list[str]`) | `List (List Char)` | element-wise the row above; `len(elts)` ↔ `elts.length`; preserves order |
| `node.elts` (the tuple's AST children) | implicit — only its rendered images and its length are observed | `len(node.elts) == 0/1/≥2` ↔ `elts` is `[] / [e] / a :: b :: rest`; the renderer reads members only through `self.visit`, so only the rendered images matter |
| `"(%s,)" % m`, string concat `"(" + … + ")"`, `", ".join(parts)` | `List Char` `++` and `List.intercalate ", ".toList` | Python `str` `+`/`%`/`str.join` ↔ Lean `List Char` `++`/`List.intercalate`; the literal `", "` ↔ `", ".toList` (two chars: comma, space) |
| the returned rendered `str` | `List Char` | as the first row |

`str` is modeled as `List Char` because the operation is per-character text
assembly (wrapping + joining); Lean `List Char` indexing/concat is total and
sound.

`str.join` ↔ `List.intercalate`: for `parts` of length ≥ 1,
`SEP.join(parts) == intercalate SEP parts` (separator placed between adjacent
elements, none at the ends). This holds for the `else` branch (≥ 2 members) and,
vacuously, for any non-empty `parts`; the 0- and 1-member cases are handled by
their own branches and never reach the join.

## 3. Callee provenance

**No axiomatized callees; no deep-model references.** The only sub-computation
`visit_Tuple` performs is `self.visit(e)` on each child — the unchanged recursive
renderer. The patched behavior is a pure function of (a) how many members there
are and (b) those members' already-rendered text; it never inspects member
content and never depends on any property of `self.visit`. So `self.visit(e)`'s
output is taken as an arbitrary opaque input (`elts : List (List Char)`), exactly
as an arbitrary consumer-supplied function would be — the spec assumes nothing
about it. Hence:

- there is **no `axiom`** (A-consumed): the proof consumes no callee contract;
- there is **no deep-model reference** (A-reference): nothing unchanged is
  re-modeled and validated against a real callee — the member renderings are
  passed through verbatim.

Consequently `axiom_check.py` (G-AX) has no callee obligation to discharge; it is
shipped as an explicit no-op that documents the absence and exits 0.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`9367`** so the
consumer-side verdict is reproducible. The R/I shadow transliterates the entire
impl region (the count-based branch + wrap/join, all R/I-tagged) to Python and
diffs it against `patch.diff`'s behaviour — the real patched
`_UnparseVisitor.visit_Tuple` — over the rendered member images. There is no
A-tagged callee to leave as a real call (§3), so the shadow is pure R/I.
