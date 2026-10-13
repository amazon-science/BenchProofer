# refinement.md — sphinx-doc__sphinx-9602

The operation-by-operation correspondence between `model.py`'s implementation
(`render_literal_value`, `resolve_subscript`, and the deep pure folds
`wrap_seq` / `resolve_seq`) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A-consumed** (proof uses an axiom's
`Ensures`), **A-reference** (a deep model validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

The gold patch is three hunks inside the one function `_parse_annotation`
(and its nested `unparse`) in `sphinx/domains/python.py`:

* **Hunk 1** (`ast.Constant` branch): `nodes.Text(node.value)` →
  `nodes.Text(repr(node.value))`.
* **Hunk 2** (`ast.Subscript` branch): wrap each `nodes.Text` body node in a
  `nodes.literal` when the subscript head is `Literal`/`typing.Literal`.
* **Hunk 3** (final resolution loop): a `nodes.literal` node → its child
  (plain text); a non-blank `nodes.Text` node → `type_to_xref(...)`.

There are **no A-consumed axioms**: every changed operation is modelled deeply.

## A. Behaviour B1 — `render_literal_value` ↔ Hunk 1

Gold hunk:
```
-                return [nodes.Text(node.value)]
+                return [nodes.Text(repr(node.value))]
```

| # | model.py impl op (`render_literal_value`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `value: List[int]`, `is_str: bool` | `node.value` (a `str`/`bool`/`int`) | R | `str` ↔ `List[int]` code points; `is_str` abstracts `isinstance(node.value, str)` (mapping.md §2). |
| A2 | `is_str` branch: `[39] + value + [39]` | `repr(node.value)` when the value is a string | A-reference | the changed operation is modelled **deeply**: on the simple printable-ASCII string domain `repr` adds a leading + trailing apostrophe (U+0027 = code point 39) and nothing else. This equality is **domain-restricted**: `repr(s) == "'" + s + "'"` holds iff every code point of `s` is printable ASCII (0x20..0x7e) and is neither an apostrophe (39) nor a reverse solidus (92) — otherwise `repr` escapes or switches to double quotes. **model.py encodes exactly that domain as a `Requires`** on the `is_str` case (`Implies(is_str, Forall j: 32<=value[j]<=126 and value[j]!=39 and value[j]!=92)`); the equality is only claimed on `Requires`-satisfying inputs. G-AX runs the real `repr` on string values **drawn from precisely that domain** (asserting the precondition it fuzzes under, with a negative control just outside it) and on bool / int / float values, asserting equality with this model (mapping.md §3.1). The proof consumes no axiom for `repr`. |
| A3 | `not is_str` branch: returns the value's textual form unchanged | `repr(node.value)` when the value is a `bool`/`int` | A-reference + R | `repr(v) == str(v)` for `bool`/`int`, so the rendered *content* is the value's plain textual form; the patch's real change for non-strings is the *type* passed to `nodes.Text` (now always a real `str`), captured by the `is_str = False` branch returning `value`. (Non-string values carry no `Requires` restriction — only the string case needs the simple-quote domain.) G-AX checks `render_literal_value == repr` on bools/ints too (mapping.md §3.1). |

The discriminating content of B1 — a textual value renders **with** its
surrounding quotes — lives in `Ensures(Implies(is_str, ToSeq(Result()) ==
quote() + ToSeq(value) + quote()))`. `model_prepatch_2.py` reverts Hunk 1
(returns `value` unquoted even when `is_str`) and **fails** exactly that
postcondition (G-DIFF). This is what makes the F2P assertion `"'abc'"` (not
`"abc"`) pass.

## B. Behaviour B2 — `resolve_subscript` ↔ Hunks 2 + 3

Gold hunks:
```
            result.append(addnodes.desc_sig_punctuation('', ']'))
+
+            # Wrap the Text nodes inside brackets by literal node if the subscript is a Literal
+            if result[0] in ('Literal', 'typing.Literal'):
+                for i, subnode in enumerate(result[1:], start=1):
+                    if isinstance(subnode, nodes.Text):
+                        result[i] = nodes.literal('', '', subnode)
             return result
...
         for i, node in enumerate(result):
-            if isinstance(node, nodes.Text) and node.strip():
+            if isinstance(node, nodes.literal):
+                result[i] = node[0]
+            elif isinstance(node, nodes.Text) and node.strip():
                 result[i] = type_to_xref(str(node), env)
```

`resolve_subscript` models the **body** of the subscript — the enumerated
arguments and their separators between the brackets. (The subscript head,
`result[0]`, and the bracket punctuation are unchanged by this behaviour: the
head is a non-blank text node that both pre- and post-patch resolve to a
cross-reference, matching the F2P expectation that `Literal` is a
`pending_xref`. axiom_check.py replays the full head-included gold pipeline to
confirm the head→XREF invariance.)

| # | model.py impl op (`resolve_subscript`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `kinds: List[int]` (each ∈ {1,2,3,4}), `is_literal: bool` | the `result` list of nodes + the `result[0] in ('Literal','typing.Literal')` test | R | each docutils node ↔ a kind code (mapping.md §2); `is_literal` abstracts the head-text Literal test. |
| B2 | wrap loop: `if is_literal and k == 1: wrapped=[4]+...` (`wrap1`/`wrap_seq`) | Hunk 2 loop: `if isinstance(subnode, nodes.Text): result[i]=nodes.literal('', '', subnode)` (only when head is Literal) | A-reference | the changed wrap is modelled **deeply** by the verified loop + the pure fold `wrap_seq`: a body text node (NAME, kind 1) in a Literal subscript becomes a wrapped node (LIT, kind 4); everything else is unchanged. G-AX checks `wrap1` == the gold body wrap on every kind and `is_literal` value (mapping.md §3.2). |
| B3 | resolve loop: `if w==4: [1]; elif w==1: [3]; else [w]` (`resolve1`/`resolve_seq`) | Hunk 3 loop: `if isinstance(node, nodes.literal): result[i]=node[0]; elif isinstance(node, nodes.Text) and node.strip(): result[i]=type_to_xref(...)` | A-reference + I | LIT (4) → NAME (1) is the `node[0]` unwrap (plain text); NAME (1) → XREF (3) is the `type_to_xref` cross-reference; PUNCT/XREF pass through (the `else`). G-AX checks `resolve1` == the gold resolve body on every kind (mapping.md §3.2). The control flow (the three-way `if/elif/else`) is **identical**. |
| B4 | composition: `resolve_subscript == resolve_seq ∘ wrap_seq` (two sequential loops, faithful to Hunk 2 then Hunk 3) | Hunk 2 mutates `result` in place, then Hunk 3 iterates the mutated `result` | I | the two patched loops run in order on the same list; the model runs the wrap loop then the resolve loop on its output — the same data flow. |

The discriminating content of B2 — an enumerated value stays plain text rather
than becoming a cross-reference — lives in
`Ensures(ToSeq(Result()) == resolve_seq(wrap_seq(ToSeq(kinds), is_literal)))`:
for `is_literal=True` a NAME body node is wrapped (4) then unwrapped (1), so it
is **not** a XREF (3); for `is_literal=False` a NAME stays NAME and resolves to
XREF (3). `model_prepatch.py` reverts Hunk 2 (never wraps), so a NAME body node
resolves to a XREF even in a Literal subscript, and it **fails** that
postcondition (G-DIFF) — exactly the nitpick bug (an enumerated value treated
as a missing class).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The two operations that genuinely
changed — the `repr` rendering of a constant and the per-node kind decision of
the resolver — are modelled **deeply** (the quoting in `render_literal_value`;
the `wrap_seq`/`resolve_seq` folds + the two verified loops in
`resolve_subscript`), not hidden behind axioms about the function under change.
There is **no consumed `@ContractOnly` axiom** in the bundle. The unchanged
callees `repr` and `type_to_xref` appear only as **A-references** that G-AX
validates the deep models against.

## D. verify(model) ⇒ resolved

`render_literal_value` verifies only if a string value is rendered with
surrounding quotes (A2/A3); `resolve_subscript` verifies only if a Literal
body value resolves to plain text and a non-Literal body value resolves to a
cross-reference (B2/B3). By R (str ↔ List[int]; node ↔ kind code; `is_str` /
`is_literal` abstractions) the verified models equal the gold patch's three
hunks on the tested inputs; by G-AX the deep models equal the real callees
(`repr`, `type_to_xref`) and the end-to-end node-kind sequence the gold
`_parse_annotation` produces matches on the two F2P annotations. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and audited callees — and the gold patch resolves (G-RESOLVE).
The trust points are exactly the two of PLAN §1.1: deep-model soundness (G-AX)
and refinement fidelity (this document, G-EQ).

Both modeled functions additionally carry a `MustTerminate` obligation in
their preconditions (with strictly decreasing loop measures discharging it):
Nagini is a partial-correctness verifier by default, so without the
obligation an implementation that diverges on some admitted input would
satisfy the value postconditions vacuously. The real repo operations (a
single expression evaluation and two bounded scans over a finite node list)
always return, so the obligation is a faithful total-correctness statement,
not an over-tightening.
