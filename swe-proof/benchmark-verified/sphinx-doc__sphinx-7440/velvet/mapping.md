# mapping.md — sphinx-doc__sphinx-7440

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 9bb204dcabe6ba0fc422bf4a45ad0c79c680d90b`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the modeled callee.

Repo file under change: `sphinx/domains/std.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `registerGlossaryName (termText : List Char)` | the cross-reference-key computation in `make_glossary_term(env, textnodes, index_key, source, lineno, …)` — `sphinx/domains/std.py:278` (key handed to the registry at body line 308) | the modeled changed behaviour: the key under which a glossary term is registered |
| `registeredKey (termText : List Char)` *(deep model — A-reference)* | the project object registry's record/enumerate round-trip: `StandardDomain.note_object('term', name, …)` (`std.py:649`) storing into `self.objects[('term', name)]`, then `StandardDomain.get_objects()` (`std.py:964`) yielding `(name, name, 'term', …)` — `name` echoed verbatim at `std.py:975` | pure spec: the key recorded and later reported for a term; deep model of the unchanged registry, validated `registeredKey == real round-trip` by axiom_check.py (G-AX), NOT consumed as an axiom |

The pre-patch repo expression the change removes (refinement audit only, not in
the consumer spec view): the `.lower()` applied to the term text before it is
handed to `note_object` (`std.py:308` pre-patch). A second gold hunk drops the
`lowercase=True` flag from the term cross-reference role (`std.py:568`); see
refinement.md §B — it is F2P-test-neutral.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `str` (the term text `termtext`, and the registry key/name it becomes) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; empty `str` ↔ `[]` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| `str.lower()` (the removed normalization, pre-patch only) | `List.map Char.toLower` | per-code-point ASCII/Unicode lowercase fold; used only in `Solution_prepatch.lean` to reproduce the pre-patch key |

`termtext` is produced by `term.astext()` (`std.py:283`), a plain text
serialization of the term's child nodes; the test inputs (`term1`, `TERM2`,
`term3`, `term4`) are simple word strings. The carrier is `List Char` because the
distinguishing operation is per-code-point case folding.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `registeredKey` deep model ↔ the object-registry round-trip (A-reference)
**Callee:** `StandardDomain.note_object` followed by `StandardDomain.get_objects`
(`sphinx/domains/std.py`, unchanged by the gold patch). `make_glossary_term`
computes a key and calls `std.note_object('term', <key>, node_id, …)`; the F2P
test reads the registered objects back via `get_objects()`.

The changed behaviour is modeled **deeply** by `registeredKey` (in the `pure`
region); there is **no consumed `noteObject` axiom**. The registry's relevant
contract is: the name passed to `note_object` is stored under that exact key and
later **yielded verbatim** by `get_objects` —

```python
def note_object(self, objtype, name, labelid, location=None):
    ...
    self.objects[objtype, name] = (self.env.docname, labelid)   # keyed by `name` as given

def get_objects(self):
    ...
    for (type, name), info in self.objects.items():
        yield (name, name, type, info[0], info[1], ...)          # `name` echoed unchanged
```

So the key under which a term becomes observable in `get_objects()` is exactly
the string `make_glossary_term` chose — no case folding or other normalization is
performed by the registry. Post-patch `make_glossary_term` chooses `termtext`
itself (the term text as written), so the observable key equals the term text
**verbatim, case preserved** — which is what `registeredKey` (the identity on the
term text) encodes. The pre-patch code chose `termtext.lower()`, recording the
term under its lower-cased form; this is the single behavioural change F2P
`tests/test_domain_std.py::test_glossary` observes (an uppercase term `TERM2`
must register and report as `TERM2`, not `term2`).

**Soundness check (G-AX):** `axiom_check.py` constructs a real `StandardDomain`
against a stub environment, calls the real `note_object('term', name, …)` and
then the real `get_objects()`, over boundary names (empty, single chars, mixed
case, the four F2P term names, names with separators/digits/unicode) plus
randomized fuzz, and asserts the registry yields each registered `name` back
unchanged — i.e. that the registry is identity-on-name (`registeredKey == name`).
Imports only `sphinx` (the repo under test) + stdlib. Exit 0 iff sound.

### 3.2 The dropped `lowercase=True` xref-role flag (not modeled; F2P-neutral)
The second gold hunk removes `lowercase=True` from the `'term'` entry of
`StandardDomain.roles` (`std.py:568`). That flag governs how a `:term:`
cross-**reference** target is normalized at resolution time
(`XRefRole.create_xref_node`, `sphinx/roles.py:146`). No F2P/`test_glossary`
assertion resolves a term reference, so this hunk is observationally neutral for
the resolved/unresolved verdict; it is the necessary companion that keeps
case-sensitive lookups consistent end-to-end. Recorded here for the refinement
audit (refinement.md §B); it contributes no spec clause and no axiom.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`7440`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates the impl op (`registeredKey termText` = the verbatim key) to
Python and drives it through the **real, gold-patched** `make_glossary_term`
end-to-end, reading the recorded key back via the real `get_objects()`; it
asserts the recorded key equals the term text verbatim over ≥10⁵ fuzzed term
strings. The registry round-trip is exercised with the real repo component (the
A-reference is run as the real callee, not the model).
