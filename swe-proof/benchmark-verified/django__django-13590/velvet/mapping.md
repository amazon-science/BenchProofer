# mapping.md — django__django-13590

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 755dbf39fcdc491fe9b588358303e259c7750be4`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
records callee provenance.

Repo file under change: `django/db/models/sql/query.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reconstructSequence (s : SeqVal) (f : Int → Int)` | `Query.resolve_lookup_value(self, value, can_reuse, allow_joins)` — `django/db/models/sql/query.py:1072`; the modeled change is the `elif isinstance(value, (list, tuple)):` branch (body lines 1077–1083) | the modeled changed function, restricted to its list/tuple branch |
| `f : Int → Int` | the per-element call `self.resolve_lookup_value(sub_value, can_reuse, allow_joins)` applied to each member of the iterable (`query.py:1081`) | the independent per-member resolution; abstracted as a free total function (see §3) |
| `s.positionalCtor : Bool` | `hasattr(type_, '_make')` — whether `type(value)` is a namedtuple whose constructor takes its members positionally rather than as one iterable (`query.py` post-patch) | the type-capability the reconstruction must consult |
| `s.items : List Int` | the members of `value` (the `list`/`tuple`), in order | the sequence's contents |
| `resolvedSeq` *(deep model)* | the post-patch reconstruction `type_(*values)` / `type_(values)` of `value` from its per-element-resolved members (`query.py` post-patch) | pure spec: the reconstructed sequence; modeled deeply, NOT an axiom |
| `rebuildPositional` | `type_(*values)` — supply resolved members as separate positional args (the namedtuple path). PARTIAL on the real side: splatting members into a `list`/`tuple` constructor raises `TypeError` whenever there is at least one member (`list(*[2,3])` → "expected at most 1 argument"; `list(*[2])` → "int not iterable"); only the no-member splat degenerates to the empty call and succeeds. Modeled exactly: `.ok` iff `positionalCtor ∨ items = []`, else `.error .positionalNotAccepted`. | pure spec helper |
| `rebuildIterable` | `type_(values)` — pass the resolved-members iterator/iterable to the type constructor (the list/tuple path; the ONLY path pre-patch) | pure spec helper |

The pre-patch repo behaviour the change fixes (refinement audit only, not in the
consumer spec view): `return type(value)(<generator>)` (`query.py:1080–1083`),
which passes a single iterator to `type(value)` unconditionally — fine for
`list`/`tuple`, a `TypeError` for a namedtuple type (its `__new__` wants the
members positionally).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `value`, a `list`/`tuple`/namedtuple of resolvable members | `SeqVal` (`positionalCtor`, `items`) | a sequence is modeled by (a) whether its `type(value)` requires positional construction (`hasattr(type_, '_make')` ↔ `positionalCtor`) and (b) its members in order (`list(value)` ↔ `items`). Only these two observables are touched by the change. |
| a single resolvable member (the `sub_value`) | Lean `Int` | the member domain is modeled as `Int`; the change is parametric in the member type, so any infinite carrier with a total resolver is faithful (the change never inspects member identity). |
| `self.resolve_lookup_value(sub_value, …)` applied per member | `f : Int → Int` (free total function) | abstracts the independent per-member resolution. The change does NOT alter this call; both pre- and post-patch resolve each member then reconstruct. Modeling `f` as an arbitrary total function makes the spec quantify over ALL resolvers — strictly weaker than any concrete callee, so no contract/axiom is owed (directive 7). |
| `type(value)(*values)` (namedtuple) / `type(value)(values)` (list/tuple) | `rebuildPositional` / `rebuildIterable` | the reconstruction step; positional-vs-iterable selected by `positionalCtor`. Reconstruction preserves the type and the member order. |
| construction failure (`TypeError` from `type_(<iterator>)` on a namedtuple) | `Except.error RebuildErr.iterableNotAccepted` | the observable pre-patch failure for a positional type; post-patch it never occurs. |
| construction failure (`TypeError` from `type_(*values)` on a `list`/`tuple` with ≥1 member — splat gives the constructor N positional args where it takes one iterable) | `Except.error RebuildErr.positionalNotAccepted` | the observable failure of UNCONDITIONAL positional reconstruction on a non-positional type; the gold patch avoids it by guarding `type_(*values)` behind `hasattr(type_, '_make')`. On the gold path it never occurs. |

The non-list/tuple legs of `resolve_lookup_value` (the `hasattr(value,
'resolve_expression')` branch at `query.py:1073` and the final `return value`)
are UNCHANGED by the patch and OUTSIDE the modeled branch; they are not part of
the spec (the change touches only the `elif isinstance(value, (list, tuple))`
body).

## 3. Callee provenance

No consumed axioms; no deep-model reference to a concrete external callee.

- **`f` (per-member resolution).** The change resolves each member by recursively
  calling `resolve_lookup_value` — the very function under spec. We do NOT
  axiomatize it: it is modeled as an arbitrary total function `f : Int → Int`,
  and the postcondition (`items.map f`, type preserved, always-ok) holds for
  EVERY `f`. This is strictly weaker than any concrete behaviour of the real
  callee, so there is no over-claim to check (directive 7). The change is
  parametric in this resolution — pre- and post-patch apply the identical
  per-member resolution; only the reconstruction differs.

- **The reconstruction (`type_(*values)` vs `type_(values)`).** This is the
  CHANGED operation; it is modeled DEEPLY (`rebuildPositional` /
  `rebuildIterable` + the branch on `positionalCtor`), NOT behind an axiom about
  the function under change (directive 7). Its fidelity to the gold patch is
  audited mechanically by G-CONF (`conformance_check.py`).

There is therefore no `axiom_check.py` for this bundle (`meta.json gates.G-AX =
skip`, like django__django-11149).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13590`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `resolvedSeq` (the deep reconstruction model) to Python and runs
it against the gold-patched `Query.resolve_lookup_value` reconstruction
behaviour over `list`, `tuple`, and `namedtuple` carriers (the three sequence
types the change distinguishes), with members carried by an in-process resolver
`f`. The whole impl region is R/I (no A-tagged callee in the computed `out`), so
`conf_skip = false`.
