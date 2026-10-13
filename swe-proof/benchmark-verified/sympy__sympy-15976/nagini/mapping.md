# mapping.md — sympy__sympy-15976

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 701441853569d370506514083b995d11f9a130bd`, states the type
abstraction, and gives the provenance of the unchanged callee the model
validates against (an A-reference checked by G-AX, not a consumed axiom).

Repo file under change: `sympy/printing/mathml.py` (the presentation printer).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `print_symbol(name, has_subs, has_supers, subs_multi, supers_multi, bold)` | `MathMLPresentationPrinter._print_Symbol(self, sym, style='plain')` — `sympy/printing/mathml.py:745` | the modeled changed function (presentation-MathML symbol renderer) |
| `MNode` (abstract markup element: `tag`, `ctags`, `bold`) | the `xml.dom.minidom` elements created by `self.dom.createElement(...)` in `_print_Symbol` (`mi`/`msub`/`msup`/`msubsup`/`mrow`) | the produced DOM element, abstracted to what a consumer observes |
| `root_tag_for(has_subs, has_supers)` | the four-way `if len(supers)==0 / len(subs)==0` element-kind choice (`mathml.py:782-801`) | pure spec: the ROOT element kind |
| `child_tags_for(...)` / `sub_group_tag(multi)` / `sup_group_tag(multi)` | the children appended to the chosen element, with `join(items)` returning `mrow` for `len(items)>1` else `mi` (`mathml.py:751-766,782-801`) | pure spec: the ROOT's direct element children, in order, each identified by the ROLE it fills (base name / subscript group / superscript group) as well as its element kind |
| *(decomposition flags)* `has_subs/has_supers/subs_multi/supers_multi` | `split_super_sub(sym.name)` → `(name, supers, subs)` — `sympy/printing/conventions.py:14` (UNCHANGED) | the unchanged name-decomposition callee, abstracted to the emptiness/multiplicity of its two lists |

The pre-patch repo behaviour the change removes (for the refinement audit, not
referenced from the consumer spec view): the line `x = self.dom.createElement('mi')`
at the *top* of `_print_Symbol` (`mathml.py:746`) and the four
`x.appendChild(<structural element>)` calls (`mathml.py:784,789,795,801`), which
wrapped every produced tree in an outer `<mi>`. The bold attribute, set at the
top in the pre-patch (`mathml.py:748-749`), is moved to the end onto the chosen
root (`# Set bold font?` hunk).

`_print_MatrixSymbol` (`mathml.py:804`) and `_print_RandomSymbol`
(`mathml.py:807`) both delegate to `_print_Symbol`, so the same fix covers them
(P2P `test_print_matrix_symbol` exercises the bold-on-root path).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a `xml.dom.minidom` Element | `MNode` with `tag` (int code), `ctags` (ROLE-and-kind codes of direct ELEMENT children), `bold` (mathvariant marker) | `element.nodeName` ↔ `_TAG_NAME[tag]` for the ROOT (`mi`=1, `msub`=2, `msup`=3, `msubsup`=4); each direct element child maps to a code naming the ROLE it fills together with its element kind: the `mi` child whose `#text` is the base name ↔ `TAG_MNAME`=6; the subscript group ↔ `TAG_SUB_ONE`=7 (one part, nodeName `mi`) or `TAG_SUB_ROW`=8 (several parts, nodeName `mrow`); the superscript group ↔ `TAG_SUP_ONE`=9 / `TAG_SUP_ROW`=10 likewise. A consumer observes each child's own rendered content and the slot it occupies, so children in different roles are NOT interchangeable even when they share a nodeName — in particular the subscript and superscript slots of `msubsup` remain distinguishable when both groups have the same multiplicity and hence the same element kind. Checked POSITIONALLY against the real child's content (§3.2). `element.getAttribute('mathvariant')=='bold'` ↔ `bold` |
| the base name's `#text` content node | (not an element child) | a bare identifier holds its name as a `#text` node; that text content is the node's value, not an element child, so it is NOT part of `ctags` (an empty element-child list for the bare-identifier kind) |
| `sym.name : str` | `name : List[int]` (read-only, fractional permission) | the textual symbol name; the renderer reads it only through `split_super_sub`, whose result this model abstracts to the four boolean flags, so the name's code points themselves never enter the structural choice |
| `split_super_sub(sym.name)` result lists `supers`, `subs` | flags `has_subs=len(subs)>0`, `has_supers=len(supers)>0`, `subs_multi=len(subs)>1`, `supers_multi=len(supers)>1` | the only facets of the decomposition the structural choice and `join` read; WHICH list a group slot renders is carried by that slot's role code, not by these flags |
| `style == 'bold'` parameter | `bold : bool` | bold styling requested (the `mat_symbol_style` setting routes here for matrix symbols) |

`str` indexing/iteration is banned in Nagini; the name is carried as `List[int]`
but is read-only here (the decomposition is abstracted to the flags), so it is
required and ensured at `Acc(list_pred(name), 1/2)` (directive 5).

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `split_super_sub` (unchanged decomposition helper) — A-reference
**Callee:** `sympy.printing.conventions.split_super_sub(text)`
(`conventions.py:14`). UNCHANGED across the fix. It splits a symbol name into
`(name, supers, subs)`; a trailing run of digits on the base name is treated as
a subscript (`_name_with_digits_p`, `conventions.py:11,66-69`) — this is exactly
why `x2` acquires a subscript and hits the bug. The model abstracts only the
emptiness and multiplicity of `supers`/`subs` (the four flags). There is no
`@ContractOnly` axiom: the flags are taken as inputs and the structural logic is
modelled deeply; G-AX runs the real helper to derive the flags for each tested
name.

### 3.2 The fixed `_print_Symbol` builder == the model deep structure — A-reference
The changed structural construction is modelled DEEPLY (`root_tag_for`,
`child_tags_for`, `sub_group_tag`/`sup_group_tag`, and the verified `print_symbol` builder); there is
no consumed axiom. `axiom_check.py` (G-AX) installs the post-fix
`_print_Symbol` body (the gold-patch builder) onto the real
`MathMLPresentationPrinter` and asserts, for every FAIL_TO_PASS symbol name plus
4000 fuzz names, that the produced DOM element's `nodeName` equals
`root_tag_for(...)` and its element-child `nodeName` sequence equals
`child_tags_for(...)` (under §2's tag↔nodeName map), with the four flags derived
from the REAL `split_super_sub`. Wherever the model places `TAG_MNAME` it also
asserts the real child at that position is the identifier carrying the
(translated) base-name text, and wherever it places a script-group code it
asserts the real child at that position renders exactly the part list that code
names (the subscripts for a `SUB` code, the superscripts for a `SUP` code) —
§2's role-identity refinement, pinning both the base-name identifier's POSITION
and WHICH of the two script lists occupies each group slot. That content check is
what discriminates the two script slots, which share an element kind whenever the
lists have equal multiplicity. It also asserts the no-extra-`<mi>` invariant
(the root is never an identifier element when sub/superscripts are present) and
that the bold marker lands on the produced root. Imports only `sympy` (the repo
under test) and the stdlib. Exit 0 iff every observation matches the model.

The single behavioural change the F2P `test_presentation_symbol` observes:
post-fix the produced tree's ROOT is the structural element itself
(`msub`/`msup`/`msubsup`) — NOT an `<mi>` wrapping that structural element. The
issue is that Safari renders the spurious `<mi><msub>…</msub></mi>` as invisible;
removing the wrapper is the fix.

## G-CONF (differential conformance)

`conformance_check.py` refutes the R/I refinement leg: the SHADOW is the
`# impl-start`/`# impl-end` region of `model.py` copied verbatim with only the
contract calls stripped (plus its dependencies: the `MNode` constructor body,
the `@Pure` accessors `node_tag`/`node_ctags`/`node_bold` with `Unfolding`
reduced to the field read, and the `@Pure` helpers `sub_group_tag` / `sup_group_tag`; `PSeq`/`ToSeq` realized by an
immutable-tuple shim). `root_tag_for`/`child_tags_for` are not shadowed — they
appear only inside `Ensures`, so they are contract text, not impl. There are no
`@ContractOnly` callees (§ "axioms-start" is empty).

**Oracle (called, not transliterated):**
`MathMLPresentationPrinter._print_Symbol` (§1, `sympy/printing/mathml.py:745`),
imported from the gold-patched `/testbed` and invoked per input; the printer
needs no context beyond its own `minidom.Document`. The four decomposition
flags are derived by calling the real unchanged
`sympy.printing.conventions.split_super_sub` (§3.1), never re-implemented.

**Bridge (§2, inverted):** model `name : List[int]` → `str` → `Symbol(name)`;
`bold` → `style='bold'|'plain'`. Back: `element.nodeName == _TAG_NAME[tag]`;
`ctags[i]` vs the nodeName of the i-th direct ELEMENT child (a bare
identifier's `#text` base name is not an element child, so the `TAG_MI` kind
observes an empty child list); `getAttribute('mathvariant')=='bold'` vs `bold`.
§2's role-identity refinement is checked POSITIONALLY: wherever `ctags` says
`TAG_MNAME`, the real child must be an `mi` whose text is the translated base
name, and wherever it says a script-group code the real child must render that
code's part list (positional, not a text→kind map, because a name like `x_x` has
a subscript `mi` whose text also equals the base name).

**Inputs:** the observable's abstract domain is FINITE — `(subs, supers)` are
each in {absent, one part, several parts} and `bold` in {F,T}, i.e. 3·3·2 = 18
classes — so phase 1 ENUMERATES all 18 exhaustively with witness names (the
enumeration is self-checked: each witness's class is confirmed via the real
`split_super_sub`, and the phase aborts as an error if fewer than 9/9 script
classes are covered), together with the F2P shapes of
`test_presentation_symbol` (`x`, `x^2`, `x__2`, `x_2`, `x^3_2`, `x__3_2`,
`x_2_a`, `x^2^a`), the trailing-digit issue names (`x1`, `x2`, `x23`), the P2P
bold matrix symbol (`A`), greek bases, and degenerate names (`""`, `x_`, `x__`,
`_x`, `^`). Phase 2 fuzzes the remaining unbounded model input (the name's code
points) over the same domain to reach the count. Every input satisfies the only
`Requires` (`Acc(list_pred(name), 1/2)` — any name).

**Total inputs:** 100 060 (60 boundary + 100 000 fuzz). **Pinned seed:** `15976`
(module constant `SEED`). Exit 0 iff zero disagreements; a disagreement prints
the name, style, real decomposition, and both observations, and exits 1.

Refutation capability was mutation-checked (results not carried by the gate):
run against the PRE-patch `_print_Symbol` it fails on the extra `<mi>` wrapper;
swapping the shadow's sub/super child order fails on child kind; dropping the
bold assignment fails on marker placement.
