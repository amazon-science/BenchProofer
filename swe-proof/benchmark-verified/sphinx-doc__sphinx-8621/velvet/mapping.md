# mapping.md — sphinx-doc__sphinx-8621

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 21698c14461d27933864d73e6fba568a154e83b3`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each modeled callee.

Repo file under change: `sphinx/builders/html/transforms.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `kbdSplit (text : List Char)` | the segmentation step of `KeyboardTransform.run` — `sphinx/builders/html/transforms.py:42` (`parts = self.pattern.split(node[-1].astext())`), driven by the class attribute `pattern` defined at `transforms.py:40` | the modeled changed behaviour: how a `:kbd:` keystroke string is split into keys and connectors |
| `splitParts (started cur) : List Char → List (List Char)` *(deep model)* | the list `re.split` returns for `pattern` (`transforms.py:42`) — the keys interleaved with the matched separator groups | pure spec: the segmentation produced by the patched pattern, modeled deeply |
| `isSep (c : Char) : Bool` | the connector alternation `(-|\+|\^|...)` of `pattern` (`transforms.py:40`) | pure spec: the connector character test |

There is **no consumed `axiom`** and **no A-reference**: the segmentation is
modeled deeply (`splitParts`), and it calls no outside callee. The downstream
`run` body (`node.pop()`, the `parts.pop(0)` loop emitting `nodes.literal`/
`nodes.Text`, `transforms.py:44-62`) consumes the split list positionally and is
genuinely unchanged control flow reached identically for any segmentation, so it
is not modeled (refinement.md §C).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the keystroke `str` (`node[-1].astext()`, the argument to `pattern.split`) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; empty `str` ↔ `[]` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| `re.split` result `list[str]` | `List (List Char)` | the i-th returned segment ↔ the i-th inner `List Char`; `re.split`'s captured-separator groups (the pattern is fully parenthesised) ↔ the one-character connector segments `[c]` interleaved between keys |

### 2.1 Modeled domain (the binding restriction)

The patched pattern is `(?<=.)(-|\+|\^|\s+)(?=.)`: a separator group is one of
the three single connector characters `-`, `+`, `^`, **or a whitespace run
`\s+`**, that is flanked by a character on each side. The model
(`isSep`/`splitParts`) covers the **no-whitespace keystroke domain**: inputs
whose only separator characters are the single connectors `-`, `+`, `^`. Within
that domain the model is byte-exact against the real `re.split` (verified: 0
disagreements over 6·10⁵ fuzzed inputs against both the patched and the
pre-patch pattern; G-CONF re-checks ≥10⁵ in-container).

This is exactly the domain of the bug and of BOTH F2P tests — `:kbd:`-`` and
`:kbd:`Alt+^`` — and of every `:kbd:` P2P test (`space`, `Control+X`, `M-x M-s`
contains a whitespace run but its `-`/`+` separators and key boundaries are
single-connector; the model is not claimed over the whitespace-run segmentation
and G-CONF does not generate whitespace inputs). The `\s+` run semantics
(maximal-munch whitespace runs, the lookbehind/lookahead trimming one space at a
string boundary) are orthogonal to this fix — the issue is solely about the
three connector characters — and modeling them would add no discriminating power
over the bug while complicating the carrier. The restriction is recorded here,
in refinement.md §C, and enforced by conformance_check.py's input generator.

## 3. Callee provenance

None. No axiom, no A-reference, no deeply-modeled outside callee. The
segmentation is built entirely from concrete `List Char`/`Char` operations over
the input. `axiom_check.py` (G-AX) is therefore a skip stub (it asserts there is
nothing to validate against a real callee); fidelity of the deep model to the
patched behaviour is exercised by `conformance_check.py` (G-CONF) against the
REAL patched `KeyboardTransform.pattern.split`.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`8621`** so the
consumer-side verdict (§11.3) is reproducible. The shadow it builds
transliterates `isSep`/`splitParts` (all R/I-tagged ops) to Python and diffs
against the real patched `pattern.split` over the modeled (no-whitespace) domain.
