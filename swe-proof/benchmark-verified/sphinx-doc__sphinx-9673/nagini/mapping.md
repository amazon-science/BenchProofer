# mapping.md — sphinx-doc__sphinx-9673

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 5fb51fb1467dc5eea7505402c3c5d9b378d3b441`, states the type
abstraction, and gives the provenance of the (zero consumed) axioms.

Repo file under change: `sphinx/ext/autodoc/typehints.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `augment_return_typefield(field_kinds, return_annotated)` | `augment_descriptions_with_types(node, annotations)` — `sphinx/ext/autodoc/typehints.py:130` (the return-classification first loop, lines 137-155, and the rtype-emission block, lines 168-173) | the modeled changed function: decides whether a return-type field is emitted |
| `name_is_return_key(name, return_key_a, return_key_b)` | the `for name in annotations: if name == 'return': continue` guard in `augment_descriptions_with_types` — `sphinx/ext/autodoc/typehints.py:158-160` | the modeled second hunk: which annotated name is skipped when back-filling parameter types |
| `has_return_description(kinds)` | the first-loop branch `elif parts[0] in ('return', 'returns'): has_description.add('return')` (`typehints.py:152` post-patch) | pure spec: a return-description field exists under either spelling |
| `has_return_type(kinds)` | the first-loop branch `elif parts[0] == 'rtype': has_type.add('return')` (`typehints.py:154-155`) | pure spec: a return-type field exists |

The two gold hunks (the change the bundle senses), inside
`augment_descriptions_with_types`:

```
@@ line 152
-        elif parts[0] == 'return':
+        elif parts[0] in ('return', 'returns'):
             has_description.add('return')
@@ line 159 (the for-name back-fill loop)
-        if name == 'return':
+        if name in ('return', 'returns'):
             continue
```

The emission decision the model pins is the block at `typehints.py:168-173`:
```python
if 'return' in annotations:
    if 'return' in has_description and 'return' not in has_type:
        field = nodes.field(); ...   # the rtype field is appended
        node += field
```
i.e. an rtype field is appended exactly when a return annotation exists, the
return value has a textual description, and it has no declared type. The bug:
pre-patch only the SHORT spelling of a return-description field
(`:return:`, `parts[0] == 'return'`) was recognized; the plural spelling
(`:returns:`, the form an upstream docstring-style plugin emits internally) was
not, so `'return'` never entered `has_description` and the rtype field was
never appended even though the return was documented.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the list of existing description fields `node` (a `field_list` of `nodes.field`), each reduced by `re.split(' +', field[0].astext())[0]` to a leading token | `field_kinds: List[int]` of leading-token CODES, read-only | one list entry per field; the leading token is mapped: `'return'` ↦ 2, `'returns'` ↦ 3, `'rtype'` ↦ 4, and any other token (`'param'`, `'type'`, anything else) ↦ a value `∉ {2,3,4}` (modeled as 0/1/5 — it does not bear on the return decision). The first loop's set-membership `'return' ∈ has_description` ↔ `has_return_description(ToSeq(field_kinds))`; `'return' ∈ has_type` ↔ `has_return_type(ToSeq(field_kinds))`. |
| `'return' in annotations` (the return type hint exists) | `return_annotated: bool` | `record_typehints` stores the return annotation under the literal key `'return'` (`typehints.py:35`); its presence is the boolean. |
| the appended-or-not rtype `nodes.field()` | `bool` Result (True ⇔ a return-type field is appended) | the model abstracts the appended node to the decision that produces it; the F2P test observes the rendered "Return type:" section iff this is True. |
| the annotated name being classified in the back-fill loop, vs the two return spellings | `name`, `return_key_a`, `return_key_b`: `int` identifiers | string-equality ↔ int-equality (equal ints == equal strings); `'return'` ↦ `return_key_a`, `'returns'` ↦ `return_key_b`. |
| `str` field/token text | integer codes / identifiers | `str` indexing is banned in Nagini; the leading-token classification (`re.split` + first-token compare) is upstream of the modeled decision and is reduced to the code; equal tokens map to equal codes. |

`re.split(' +', ...)[0]` (the leading-token extraction) and the docutils node
construction are upstream/downstream plumbing the change does not touch; they
are reduced into the code abstraction and the boolean Result, not modeled.

## 3. Axiom provenance

NONE. There are no `@ContractOnly` axioms and no A-reference deep-model checks:
the entire changed behaviour — recognizing BOTH return-description spellings as
synonyms, and the resulting emission decision — is pure integer/sequence logic
modeled deeply by `has_return_description` / `has_return_type` and the two
contracted functions. No unchanged library callee is consumed inside any
`Ensures`. Consequently `axiom_check.py` performs no in-container callee
execution; it is a self-contained structural cross-check that the model's
decision matches a direct re-implementation of the patched
`augment_descriptions_with_types` return-classification + emission logic over
boundary + fuzz field-lists (see axiom_check.py header).

## G-CONF (differential conformance: model vs the REAL patched repo function)

`conformance_check.py` runs in-container with the gold patch applied.

**Shadow** — provenance `direct`: the two `# impl-start`/`# impl-end` regions of
`model.py` copied VERBATIM, with only the contract calls (`Requires`, `Ensures`,
`Invariant`, `Assert`, `Acc`) and the `# invariants-*` markers deleted. The two
`@Pure` helpers (`has_return_description` / `has_return_type`) are copied over
minus contracts and `PSeq`/`ToSeq` realized by an immutable-tuple shim; since
they appear only inside contracts, they are diffed as the *postcondition*
surface alongside the impl's loop form, so both legs must agree with the oracle.
No `@ContractOnly` callees exist in this bundle (§3), so nothing is assumed.

**Oracle** — CALLED, not transliterated: the real patched
`sphinx.ext.autodoc.typehints.augment_descriptions_with_types` (§1,
`typehints.py:130`). It returns `None` and mutates in place, so it is driven
through a freshly built docutils `field_list` and observed via the fields it
APPENDS: an appended `rtype` field ⇔ `augment_return_typefield` Result (the
`typehints.py:168-173` block); and, with the single field `param <NAME>` plus
annotations `{NAME: 'int'}`, absence of the appended `type <NAME>` field ⇔
`name_is_return_key(NAME)` (the `typehints.py:158-160` skip guard).

**Type bridge** — §2 inverted: code 2/3/4 ↦ a field name whose leading token is
`return`/`returns`/`rtype`; a code ∉{2,3,4} ↦ a field name whose leading-token
classification does not touch the `'return'` key of `has_description`/
`has_type`; `return_annotated` ↦ presence of the literal key `'return'` in the
annotation dict; `bool` Result ↦ an `rtype` field being appended; int name
identifiers ↦ name strings with `'return'`↦`return_key_a`,
`'returns'`↦`return_key_b`. Each code class has several concrete realizations
(e.g. `returns decremented number`, `rtype extra`, `param x y`, the Google-header
homograph `Returns`, `returned`, `''`), so no single canonical spelling is
privileged.

**Out-of-bridge boundary probe (recorded, non-gating).** Three degenerate field
names — `param return`, `param x return`, `type return` — have a leading token
outside {return, returns, rtype} yet their `' '.join`-derived name is literally
`'return'`, so they *do* touch the `'return'` key and are therefore NOT in the
code-∉{2,3,4} class the bridge defines. Rather than silently excluding them, the
script runs them as a labelled probe and prints/reports the resulting
divergences (3 of them) in its structured JSON line. They are unreachable from
any real Python signature (`return` is a keyword, so no parameter can bear that
name) and are the same known lossy-modeling boundary already adjudicated by
`G-PANEL-2` as FAITHFUL — not spec drift. The gating diff is the in-domain one.

**Inputs** — 123733 total, all `Requires`-satisfying (`Requires` is only the
read-only permission `Acc(list_pred(field_kinds), 1/2)`, which every finite int
list meets; the bridge is the real domain constraint):

* 21 boundary cases — empty field list, every singleton, both spellings, both
  orders with `rtype`, the exact F2P shape (a lone plural `:returns:` field +
  return annotation + no rtype ⇒ rtype emitted), the Google-header homograph,
  and each impl branch taken;
* 43690 EXHAUSTIVE cases — the modeled space is finite in the code classes (the
  decision depends on nothing but the multiset of classes), so every word over
  the 4-letter alphabet {2, 3, 4, other} of length ≤ 7 (21845 words) is
  enumerated in both settings of `return_annotated`. Exhaustive coverage of all
  ≤7-field classification patterns is a stronger check than 1e5 samples;
* 80000 seeded fuzz cases over the same space with up to 14 fields, randomized
  realization per class, and extra non-`return` annotation keys;
* 22 EXHAUSTIVE `name_is_return_key` cases over the finite name pool.

**Pinned seed: `SEED = 9673`** (module constant). Branch-hit counts are printed
in the JSON line as evidence each impl branch was exercised.

**Negative control** (run during construction, not shipped): substituting
`model_prepatch.py`'s impl regions (`c == 2` only; `name == return_key_a` only)
into the shadow makes the script exit 1 on the F2P boundary case
(`kinds=[3]`, `return_annotated=True`: shadow `False` vs oracle `True`), so the
check demonstrably refutes an unfaithful shadow rather than passing vacuously.
