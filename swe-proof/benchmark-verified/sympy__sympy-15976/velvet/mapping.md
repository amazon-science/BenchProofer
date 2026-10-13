# mapping.md — sympy__sympy-15976

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 701441853569d370506514083b995d11f9a130bd`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

Repo file under change: `sympy/printing/mathml.py` — the presentation-MathML
printer's per-variable node-assembly routine.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildSymbolNode (name) (subs) (sups) (bold)` | `MathMLPresentationPrinter._print_Symbol(self, sym, style='plain')` — `sympy/printing/mathml.py:745` | the modeled changed function: assemble the single presentation node representing one printed variable. |
| `buildSymbol` (pure region) | the node-assembly body of `_print_Symbol` (`mathml.py:783-801`, post-image) | pure spec: which node represents the variable, given which scripts are present, and where the bold attribute lands. |
| `Node` (`text` / `elem`) | a `xml.dom.minidom` Element / Text node, restricted to the observables the acceptance tests read | the printer returns such a node; tests inspect `.nodeName`, `.childNodes`, `.nodeValue`, and the `mathvariant` attribute. |
| `name` (`List Char`) | `name` — the translated base name from `split_super_sub(sym.name)` (`mathml.py:775-778`) | read-only input; the base name, already unicode-translated by unchanged infrastructure. |
| `subs` (`Option Node`) | `join(subs)` when `len(subs) > 0`, else absent (`mathml.py:783,786,795`) | read-only input: the already-rendered subscript node, present iff the variable carries subscripts. |
| `sups` (`Option Node`) | `join(supers)` when `len(supers) > 0`, else absent (`mathml.py:783,790,795`) | read-only input: the already-rendered superscript node, present iff the variable carries superscripts. |
| `bold` (`Bool`) | `style == 'bold'` (`mathml.py:748` pre / `:799` post) | read-only input: whether the `mathvariant="bold"` attribute is requested. |
| `mname` | `mname = self.dom.createElement('mi'); mname.appendChild(createTextNode(name))` (`mathml.py:775-776`) | the base-name identifier element, spelled out so the result is grounded in `name`. |

The pre-image symbols the change moves/removes (refinement audit only, not in the
consumer spec view): the up-front `x = self.dom.createElement('mi')` and its
early `if style == 'bold': x.setAttribute('mathvariant','bold')`
(`mathml.py:746-749`), and the four `x.appendChild(<container>)` placements
(`mathml.py:784-801` pre-image) that nested the script container inside `x`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a minidom node (Element or Text) | `Node` (`.elem tag bold children` / `.text value`) | `node.nodeName` ↔ `Node.tag` (an Element's tag string; the sentinel `"#text"` for a Text node); `node.childNodes` ↔ the `children` list, in order; a Text node's `.nodeValue` ↔ its `value`; the presence of `mathvariant="bold"` ↔ `Node.isBold = true`. Only these observables (the ones the F2P/P2P tests read) are modeled. |
| an element/attribute string (`'mi'`, `'msub'`, …, a base name) | `List Char` | Python `str` ↔ `s.toList`-shaped `List Char`; per code point on the BMP this is total and exact. |
| `len(subs) == 0` / `len(subs) > 0` (`mathml.py:782,789`) | `subs = none` / `subs = some _` | the subscript node is present in the model iff the variable carries ≥1 subscript piece; ditto `sups`/`supers`. The model abstracts a non-empty script list to its single already-rendered node (the value `join(...)` returns), because the assembly under change only ever references that one node. |
| `style == 'bold'` | `bold : Bool` | the only `style` value that changes node shape is `'bold'`; every other value (`'plain'`, the default) is `bold = false`. |

`join(items)` (`mathml.py:751-769`) and `split_super_sub` (`conventions.py`,
imported at `mathml.py:10`) are **unchanged infrastructure**: the patch does not
touch them. Their outputs (`name`, the subscript node, the superscript node) are
supplied to the modeled routine as inputs; the model owes them no contract and
introduces no axiom for them.

## 3. Callee provenance (kind-A) — NONE

There are **no axiomatized callees and no deep-model references** in this bundle.
The single changed function is modeled deeply: the node-assembly decision
(`buildSymbol`) is spelled out in the `pure` region and computed entirely from
the inputs `name`, `subs`, `sups`, `bold`. The pieces it consumes
(`split_super_sub`'s decomposition, `join`'s per-list rendering) are unchanged
upstream infrastructure handed in as inputs, not callees whose behavior the proof
relies on. Hence there is **no `axiom` declaration**, no A-consumed contract, and
no A-reference deep model; `axiom_check.py` is omitted and G-AX is `skip`
(gates.py: no `axiom_check.py` ⇒ `G-AX skip`).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15976`** so the
consumer-side verdict is reproducible. It runs **in-container with the gold
patch applied** and drives the real patched
`MathMLPresentationPrinter._print_Symbol` over symbol names spanning every
script combination (none / sub-only / sup-only / both, single- and
multi-piece scripts, plain and bold), reading back the observable
`(top tag, bold flag, child tags)` triple; the SHADOW is the modeled
`buildSymbol` fed the SAME base name and the SAME presence/absence of each
script node recovered from the real render. The only thing under test is the
top-node-shape decision the patch changes (R/I leg). Exit 0 iff zero
disagreements.
