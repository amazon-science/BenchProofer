# refinement.md — sphinx-doc__sphinx-8721

Maps every operation in `implementation_collectModulePages` to its `patch.diff`
counterpart in `collect_pages` (sphinx/ext/viewcode.py:181). Tags:
**R** type-refinement, **A-consumed** proof uses a callee axiom, **A-reference**
op left as the real repo callee in G-CONF (not axiomatized), **I** identical
concrete op, **out-of-model** a gold co-change deliberately outside the modeled
contract (carried by `patch.diff`, not restated by the spec).

## Patch (post-patch `collect_pages`, decision prologue)
```python
def collect_pages(app):
    env = app.builder.env
    if not hasattr(env, '_viewcode_modules'):
        return                                              # existing guard
    if app.builder.name == "singlehtml":                    # NEW  (i)
        return
    if app.builder.name.startswith("epub") and not env.config.viewcode_enable_epub:   # NEW (ii)
        return
    highlighter = app.builder.highlighter
    ...                                                     # UNCHANGED: build & yield module pages
    yield (pagename, context, 'page.html')
    ...
    yield (index_pagename, context, 'page.html')
```

`collect_pages` is a generator; its observable behavior is the sequence of
`(pagename, context, template)` triples it yields. Each early `return` makes the
generator yield NOTHING. The page-construction work below the guards is unchanged
and reads neither the builder name nor the config value.

## Modeling decision, and the declared boundary

The observable behavior is "the prepared page sequence is published" vs "nothing
is published", decided by:

- `hasModules` ↔ `hasattr(env, '_viewcode_modules')` — was any module data
  collected (pre-existing guard);
- `builderName` ↔ `app.builder.name` — the active output format;
- `enableEpub` ↔ `env.config.viewcode_enable_epub` — is the companion-pages
  feature wanted for the electronic-book family;
- `generatedPages` ↔ the sequence this output format publishes for this build
  when the electronic-book preference does not withhold it (mapping.md §2).

**Scope.** The model specifies the electronic-book decision (ii) — the one the
public `problem_statement` describes and the only one any F2P/P2P test exercises.
The single-file co-change (i) is an **out-of-model** co-change: `patch.diff`
carries it verbatim, so the correctness oracle (G-RESOLVE, `verify ⇒ resolved`)
is unaffected, but the spec does not restate it as a separate clause.

Per mapping.md §1 this costs the model no faithfulness. Because `generatedPages`
is bound to the preference-independent published sequence, and guard (i) sits
UPSTREAM of the preference (it fires whatever the preference's value), that
carrier is the EMPTY sequence at the single-file format. So the model's
fall-through leg already predicts the empty result the real post-patch function
actually yields there, rather than predicting a publish the repo does not
perform. G-CONF measures this over the whole domain with NO output-format name
excluded (mapping.md §4).

## Operation correspondence
| # | Lean op (`implementation_collectModulePages`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `if !hasModules then return []` | `if not hasattr(env, '_viewcode_modules'): return` | R | `hasattr(...) : bool ↔ hasModules : Bool`; generator yields nothing ↔ `[]`. Pre-existing guard, carried unchanged. |
| — | *(no modeled op)* | `if app.builder.name == "singlehtml": return` (NEW, (i)) | out-of-model | absent from the public statement and from every shipped test; carried verbatim by `patch.diff`. Its EFFECT is nonetheless predicted by op 3, because the `generatedPages` carrier is empty at that format (mapping.md §1/§2). |
| 2 | `if builderName.startsWith "epub" && !enableEpub then return []` | `if app.builder.name.startswith("epub") and not env.config.viewcode_enable_epub: return` (NEW, (ii)) | R | `str.startswith ↔ String.startsWith`; `not viewcode_enable_epub ↔ !enableEpub`; `and ↔ &&`; early return ↔ `[]`. The tested discriminator, and the sole withholding reason the contract licenses. |
| 3 | `return generatedPages` | fall through to the unchanged page-construction body, yielding the sequence it produces | A-reference | the UNCHANGED downstream work; universally quantified in the spec and bound to the real post-patch fall-through in G-CONF via the mapping.md §2 bridge. No property consumed ⇒ NOT A-consumed, no `opaque`/`axiom` decl. |

## R legs ⇒ G-CONF

Ops 1 and 2 (the guards, R) are the discriminating control flow. Op 3 is the
A-reference: `conformance_check.py` obtains `generatedPages` from the real
patched function with the preference forced ON, then checks the shadow's decision
against the real function's ACTUAL output at the real preference value.
`conf_skip = false`.

The bridge's two premises — **(A)** off the electronic-book family the preference
does not affect the published sequence, **(B)** on that family a preference-ON run
publishes the FULL sequence — are MEASURED inside `conformance_check.py`
(`check_bridge_facts`), so a bundle whose bridge assumption silently stopped
holding fails the gate instead of passing vacuously. Premise (B) is what keeps
op 2 load-bearing: the electronic-book decision is not pre-computed inside the
carrier, so the spec must still make it. A negative control confirms this
operationally — a shadow with op 2 REMOVED disagrees with the real callee
(measured: 6 disagreements), so the carrier cannot be used to smuggle in the
answer.

## No A-consumed row

The proof consumes no property of any callee (`generatedPages` is universally
quantified; the guards are pure boolean/string decisions resolved by `simp`), so
`meta.json axioms = []`. Op 3 is recorded as an A-reference solely to document
the G-CONF binding; there is no `opaque`/`axiom` declaration in `Solution.lean`
and `axiom_check.py` is a skip stub.

## F2P alignment

`test_viewcode_epub_default` builds with the `epub` builder at the default
`viewcode_enable_epub=False` and asserts `_modules/spam/mod1.xhtml` is NOT
created — nothing is published. `test_viewcode_epub_enabled` sets it `True` and
asserts the page IS created. `test_linkcode` / `test_local_source_files` build
plain html and assert the pages exist. Op 2's clause
(`startsWith "epub" && !enableEpub ⇒ []`) pins the first; the total equality's
fall-through leg (`⇒ generatedPages`, in full) pins the other three, and is also
what blocks a suppress-everything or truncate-the-sequence implementation.

The prepatch impl has no electronic-book guard (once `hasModules`, it always
returns `generatedPages`), so it cannot satisfy the discriminating clause and
`Solution_prepatch.lean` FAILS the shared spec — the fix's behaviour is what the
spec pins. `patch.diff` (gold verbatim, both guards) makes the harness resolve.
