# mapping.md — sphinx-doc__sphinx-7757

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 212fd67b9f0b4fae6a7c3501fdf1a9a5b2801329`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
records callee provenance.

Repo file under change: `sphinx/util/inspect.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `distributePositionalDefaults (p q : Nat) (defaults : List Int)` | `signature_from_str(signature)` — `sphinx/util/inspect.py:514` — specifically the **default-value distribution across the positional parameters** (`posonlyargs` + `args`) built in the body `sphinx/util/inspect.py:520-548` | the modeled changed behaviour |
| `distributed (n : Nat) (defaults : List Int)` | the desired per-position default vector: defaults right-aligned across all `n = p + q` positional parameters (the post-patch behaviour) | pure spec |
| `p` | `len(args.posonlyargs)` (the count of positional-only parameters; `0` when the AST has no `posonlyargs` attribute) — `sphinx/util/inspect.py:523-528` post-patch | leading positional group size |
| `q` | `len(args.args)` (the count of ordinary positional-or-keyword parameters) — `sphinx/util/inspect.py:530` | trailing positional group size |
| `defaults` | `list(args.defaults)` — the supplied default expressions, in declaration order — `sphinx/util/inspect.py:520` post-patch | supplied defaults |
| `out` | for each positional parameter, in order, its `Parameter.default` (`Parameter.empty` if none) on the returned `inspect.Signature` | result |

There is **no axiomatized callee** and **no deep-model reference** to an unchanged
external function: the modeled behaviour is pure positional data movement.
`ast_unparse(node)`, which renders an individual default expression to its source
string, is applied **identically and per-element** in both the pre- and post-patch
code; it does not participate in the distribution logic (which only decides *which*
positions receive *which* default), so it is a per-element identity under the type
refinement of §2 (R), not a callee that needs an axiom. See §3.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `len(args.posonlyargs)` (a count) | `p : Nat` | identity on `ℕ`; the absent-attribute case is `p = 0` |
| `len(args.args)` (a count) | `q : Nat` | identity on `ℕ` |
| the supplied default expressions `args.defaults`, each rendered by `ast_unparse` to a `str` | `defaults : List Int` | each **distinct rendered default string** ↔ a distinct `Int` tag; the distribution logic treats a default as an opaque payload it never inspects, so any injective tagging is faithful. `len(args.defaults)` ↔ `defaults.length`; order preserved. G-CONF uses the actual rendered strings as the carrier, which is exactly this bijection with the tag realized as the string. |
| a per-position default: `Parameter.empty` vs a rendered default string | `Option Int` | `Parameter.empty` ↔ `none`; a present default `s` ↔ `some (tag s)`; G-CONF compares the realized strings vs `Parameter.empty`. |
| the per-position default vector over the `p + q` positional params, in order | `List (Option Int)` of length `p + q` | element-wise via the two rows above; order = declaration order (positional-only first, then ordinary). |

The key language fact the spec encodes (post-patch behaviour, and the documented
Python rule for default arguments): the `d = len(defaults)` supplied defaults are
**right-aligned** across the whole positional list of `n = p + q` parameters — the
last `d` positions get the defaults in order; the leading `n - d` get
`Parameter.empty`. `require defaults.length ≤ p + q` is the always-true invariant
that a parser-produced signature has no more defaults than positional parameters.

## 3. Callee provenance (kind-A) — NONE

There are **no kind-A legs**: no `axiom`, no `:|` imperative-callee stub, no
deep-model reference to an unchanged callee. `axiom_check.py` (G-AX) therefore has
nothing to check and reports `status=skip, reason=no-axioms` (exit 0).

`ast_unparse` (the only external function the changed code calls per default
expression) is **not** axiomatized: it is applied element-wise and identically in
pre- and post-patch and is independent of the distribution. Under §2 it is the
identity carried by the `Int`-tag bijection (an R leg), validated mechanically by
G-CONF — which runs the **real** patched function (hence the real `ast_unparse`)
as its oracle.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`7757`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates the `distributed` right-alignment to Python over the real signature
AST (`p = len(posonlyargs)`, `q = len(args)`, `defaults = list(args.defaults)`
rendered) and diffs the per-position `Parameter.default` vector against the
**patched** `signature_from_str` (the real correctness oracle, G-RESOLVE). The impl
region is all R/I, so this is a non-skip (`conf_skip=false`) verdict.
