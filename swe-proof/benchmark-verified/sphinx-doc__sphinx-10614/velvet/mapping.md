# mapping.md — sphinx-doc__sphinx-10614

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = ac2b7599d212af7d04649959ce6926c63c3133fa`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each callee.

Repo file under change: `sphinx/ext/inheritance_diagram.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildLinkMap (refs) (isSvg) (page)` | the `urls = {}; for child in pending_xrefs: …` link-map construction inside `html_visit_inheritance_diagram` — `sphinx/ext/inheritance_diagram.py:411-423` | the modeled changed code: builds the class-name → URL map |
| `DiagRef` (structure) | one `child` of `node` (an `addnodes.pending_xref`), via `child.get('reftitle')`, `child.get('refuri')`, `child.get('refid')`, `child.get('internal', True)` | the four touched node attributes |
| `refs : List DiagRef` | `pending_xrefs = cast(Iterable[addnodes.pending_xref], node)` (`:412`) | the iterated children |
| `isSvg : Bool` | `graphviz_output_format == 'SVG'` where `graphviz_output_format = self.builder.env.config.graphviz_output_format.upper()` (`:409`) | the SVG-rendering flag |
| `page : List Char` | `current_filename = self.builder.current_docname + self.builder.out_suffix` (`:410`) | current page path, used in fragment links |
| `afterLastHash (s)` *(deep model — A-reference)* | `str.rsplit('#', 1)[-1]` — `child['refuri'].rsplit('#', 1)[-1]` (`:417` post-patch) | pure spec: final `#`-segment of the target URL; deep model of the stdlib `rsplit`, validated `afterLastHash == rsplit('#',1)[-1]` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `refEntry`, `linkMap` | the per-`child` branch body that assigns `urls[key] = url` (`:414-423` post-patch) | pure spec: the zero/one map entry a child contributes, and the whole map |

The `DiagRef` fields bind to node attributes as:

| `DiagRef` field | repo expression | meaning |
|---|---|---|
| `name` | `child['reftitle']` | the fully-qualified class name (map key for in-project refs) |
| `target` | `child.get('refuri')` → `Option` (`some` iff `refuri is not None`) | explicit destination URL |
| `anchor` | `child.get('refid')` → `Option` (`some` iff `refuri is None and refid is not None`) | in-page fragment id |
| `external` | `not child.get('internal', True)` | true iff the ref resolves outside the project (intersphinx) |

The pre-patch behaviours the change removes (refinement audit only, not in the
consumer spec view): the `"../" + child.get('refuri')` SVG target prefix
(`:416`), keying the target entry unconditionally on `child['reftitle']`
(`:416,418`), and the `'../' + current_filename + '#' + …` SVG fragment prefix
(`:421`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a Python `str` (`reftitle`, `refuri`, `refid`, `current_filename`, and the produced URL strings) | `List Char` | `s` (Python str) ↔ `s` as `List Char` (codepoint list); `len(s)` ↔ `l.length`; `str` concat (`"a" + "b"`, `'#' + x`) ↔ `List` `++`; empty `str` ↔ `[]` |
| `child.get('refuri')` / `child.get('refid')` — `str` or `None` | `Option (List Char)` | `None` ↔ `none`; a `str` ↔ `some s` |
| `child.get('internal', True)` (bool) and `graphviz_output_format == 'SVG'` (bool) | `Bool` | direct |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; total on the BMP |
| the `urls` dict, observed as the set of `key → url` writes in iteration order | `List (List Char × List Char)` | each `urls[k] = v` ↔ a `(k, v)` pair appended in order. Because each diagram key (`reftitle`, or the recovered external key) is distinct across the children of one diagram (one xref per displayed class), the association list and the dict carry the same map; G-CONF compares the resulting dict, so duplicate-key shadowing — if any — is observed identically on both sides. |

Iteration order: the gold `for child in pending_xrefs` and the model's left-to-
right `linkMap`/`buildLinkMap` fold visit children in the same order.

`else if` is BANNED in Velvet; the gold's `if refuri … elif refid …` plus the
inner `if internal … else` / `if SVG … else` ladders are modeled with nested
`match`/`if` in `refEntry` (no `else if`).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `afterLastHash` deep model ↔ `str.rsplit('#', 1)[-1]` (A-reference)
**Callee:** Python `str.rsplit('#', 1)[-1]` — the new post-patch line
`refname = child['refuri'].rsplit('#', 1)[-1]` (`:417`). `rsplit('#', 1)` splits
on the LAST `'#'` into at most two pieces; `[-1]` takes the tail. Equivalently:
the substring after the last `'#'`, or the whole string when there is no `'#'`.
`afterLastHash` models this deeply (`(s.reverse.takeWhile (· ≠ '#')).reverse`):
take characters from the end until a `'#'` is hit, then restore order — exactly
the maximal `'#'`-free suffix. There is **no consumed `rsplit` axiom**; G-AX
validates the deep model against the real call.

**Soundness check (G-AX):** `axiom_check.py` runs the real
`s.rsplit('#', 1)[-1]` on boundary inputs (no `#`, one `#`, multiple `#`,
leading/trailing/empty pieces, the F2P-shaped `foo.html#subdir.other.Bob`) plus
randomized fuzz, asserting `afterLastHash(s) == s.rsplit('#', 1)[-1]`. Imports
nothing repo-specific. Exit 0 iff sound.

### 3.2 No consumed axioms
The only other operations — dict assignment, string concatenation `'#' + refid`,
`"../" + …` (removed), `current_docname + out_suffix` — are concrete `List`/
`Char` ops modeled directly (I/R), not axiomatized. The `axioms` region is empty.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`10614`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`refEntry`/`linkMap` (R/I-tagged ops, including the deep `afterLastHash`) to
Python and diffs the resulting `urls` dict against the gold-patched
`html_visit_inheritance_diagram` link-map construction (transliterated verbatim
from the patched source — see conformance_check.py for why the real renderer is
not invoked) over fuzzed children lists. The `external` key-recovery and the
prefix-removal are exercised on both SVG and non-SVG configurations.
