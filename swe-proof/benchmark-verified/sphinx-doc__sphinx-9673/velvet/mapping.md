# mapping.md — sphinx-doc__sphinx-9673

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 5fb51fb1467dc5eea7505402c3c5d9b378d3b441`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
callee provenance.

Repo file under change: `sphinx/ext/autodoc/typehints.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `augmentTypeFields (fields) (annotations)` | `augment_descriptions_with_types(node, annotations)` — `sphinx/ext/autodoc/typehints.py:130` | the modeled changed function |
| `classifyField` / `classifyFields` | the first `for field in fields:` classification loop — `typehints.py:136-155` | pure spec: leading-token classification of every existing info-field name |
| `emitStep` (the annotation fold body) | the `for name in annotations:` parameter-type back-fill loop — `typehints.py:157-165` | pure spec: emit a `type <name>` field per warranted annotation |
| `rtypeField` | the trailing `if 'return' in annotations: …` block — `typehints.py:167-174` | pure spec: the optional trailing `rtype` field |
| `buildFields` | the whole function body composed | pure spec: full sequence of appended fields |

No symbol is axiomatized: every step is a concrete structural transform over the
field-name tokens and the annotation table. There is no unchanged external callee
whose behaviour the spec must assume, so **no `axiom` and no deep-model
reference** appear, and G-AX is vacuous (no `axiom_check.py`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a docutils `field_list` node's existing field-name strings | `fields : List (List Tok)` | each field name string ↔ its tokens after `re.split(' +', name)`, each token a `Tok = List Char`; G-CONF builds the node and reads `field[0].astext()` back |
| the `annotations : Dict[str, str]` (insertion-ordered, py3.7+) | `annotations : List (Tok × Tok)` | `(key, type-string)` pairs in dict iteration order; key/value strings ↔ `List Char` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; total/exact on the characters used |
| `' '.join(parts[k:])` | `joinSp` = `List.intercalate [' ']` | space-join of remaining tokens ↔ `intercalate [' ']` |
| a newly appended `nodes.field` (name `'type x'`/`'rtype'`, body the annotation) | `Field.typeOf name body` / `Field.rtype body` | G-CONF normalizes each appended node to its rendered `('name', 'body')` pair and compares to the `Field` constructor's rendered form |
| `has_description` / `has_type` Python `set` | `Sets.hasDesc` / `Sets.hasType : List Tok` | membership-only; order/duplicates in the `List` are unobservable (only `.contains` is ever read), matching `set` semantics |

The result key `'return'` is the single canonical key both spellings collapse
onto: `returnKey = "return".toList`. The plural-spelling acceptance is encoded as
`p0 == returnTok || p0 == returnsTok` in `classifyField` and as the dual skip
`name == returnTok || name == returnsTok` in `emitStep`.

## 3. Callee provenance

**None.** `augment_descriptions_with_types` calls only `re.split`, `' '.join`,
`set.add`/`in`, and docutils node constructors — all modeled concretely by the
pure-region helpers (`classifyField`, `joinSp`, `Sets`, `Field`). The patch
changes only two literal comparisons (`== 'return'` → `in ('return','returns')`)
inside this function; it introduces no new callee and changes no callee's
contract. Hence there is no A-consumed axiom, no A-reference deep model, and
**no `axiom_check.py`** — G-AX is correctly skipped (gates.py: "no axiom_check.py
(no axioms in bundle)").

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`9673`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`classifyField`/`emitStep`/`rtypeField`/`buildFields` (all R/I-tagged ops) to
Python and runs the REAL patched `augment_descriptions_with_types` as the oracle,
observing the fields it appends to a freshly built `field_list`. `conf_skip =
false` (the impl region is pure R/I, no A-tagged callee).

**Bijection-domain canonicalization.** The fuzzer emits `annotations` as a raw
`(key, type-string)` pair-list, which can contain a repeated key. The dict↔assoc-list
bijection of §2 maps a Python `Dict[str, str]` (unique keys) to its insertion-ordered
pair-list; a pair-list with a duplicate key is therefore **outside the bijection's
image** — no real `dict` serializes to it, and the oracle's `ann = {}` build collapses
repeats to one key with the last value. Before comparing the two legs,
`canon_annotations()` projects each fuzzed table onto the dict domain (first-occurrence
key order, last value), so the differential test stays inside the declared refinement
domain. On the unique-key tables the bijection actually claims, this is the identity, so
it removes spurious out-of-domain disagreements (e.g. duplicate `'return'` keys, where
the spec's `lookupReturn` returns the first value and the oracle dict the last) without
weakening any modeled behavior.
