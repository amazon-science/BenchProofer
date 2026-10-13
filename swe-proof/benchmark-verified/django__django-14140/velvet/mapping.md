# mapping.md — django__django-14140

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 45814af6197cfd8f4dc72ee43b90ecde305a1d5a`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each modeled construct.

Repo file under change: `django/db/models/query_utils.py` (the `Q.deconstruct`
method, body lines 84–90 @ base_commit).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `deconstructNode (children, connector, negated)` | `Q.deconstruct(self)` — `django/db/models/query_utils.py:80` (changed body :84–90) | the modeled changed function: decompose a logical filter node into `(path, args, kwargs)` |
| `deconstructed` *(deep model — R/I, not an axiom)* | the post-patch decomposition body (`args = tuple(self.children); kwargs = {}; if self.connector != self.default: kwargs['_connector'] = …; if self.negated: kwargs['_negated'] = True`) | pure spec: the reconstructable form `(args, connKw, negKw)` |
| `Child` | an element of `self.children` (`django/utils/tree.py:23`, populated by `Q.__init__` `query_utils.py:39`) | the three observable child shapes (see §2) |
| `Connector` | `self.connector` ∈ {`Q.AND`, `Q.OR`} with default `Q.default = AND` (`query_utils.py:33–35`) | the combinator |
| `Decon` | the `(args, kwargs)` pair returned (the `path` component is constant and orthogonal — see §2) | the decomposition payload |

The pre-patch construct the change removes (refinement audit only, not in the
consumer spec view): the single-child special case
`if len(self.children) == 1 and not isinstance(self.children[0], Q): child = self.children[0]; kwargs = {child[0]: child[1]}`
(`query_utils.py:85–88` @ base_commit).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

The table G-CONF (§4.1) uses to translate values between the Lean value domain
and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.children : list` | `List Child` | order-preserving; `len(children)` ↔ `.length`; `tuple(children)` is the same elements in order ↔ `args` identity (G-CONF checks `id` order). |
| a child that is a length-2 key/value pair, e.g. `('x', 1)` (produced by `Q(x=1)` via `sorted(kwargs.items())`, `query_utils.py:39`) | `Child.pair key val` | the only child shape the removed special case read via `child[0]/child[1]`; payload opaque (`String × Int` is a faithful witness carrier). |
| a child that is a nested `Q` node (`isinstance(child, Q)` is True) | `Child.node` | the special case explicitly excluded these (`not isinstance(child, Q)`); always positional. |
| a child that is an embedded boolean expression — a value with `conditional = True` that is neither a pair nor a `Q` (e.g. `Exists(...)`) | `Child.expr` | not subscriptable: the removed special case raised `TypeError` on a lone one; the desired behaviour carries it positionally. |
| `self.connector` (`'AND'`/`'OR'`), default `'AND'` | `Connector` (`conj`/`disj`) | `conj ↔ 'AND'` (default), `disj ↔ 'OR'`. |
| `self.negated : bool` | `Bool` | identity. |
| `args` (positional tuple), `kwargs['_connector']`, `kwargs['_negated']` | `Decon.args`, `Decon.connKw : Option Connector`, `Decon.negKw : Bool` | `_connector` present iff non-default ↔ `connKw = some`; `_negated` present-and-True ↔ `negKw = true`. |
| `kwargs` keyword key/value recording of a lone child | `Decon.pairKw : Option (String × Int)` | the removed special case set `kwargs = {child[0]: child[1]}`; desired behaviour: `pairKw = none` always. A G-CONF stray-kwarg would surface here. |
| the `path` string component (`'django.db.models.Q'`, `query_utils.py:81–83`) | (omitted) | a constant prefix independent of `children/connector/negated`; the change touches only `args/kwargs`. Orthogonal to the modeled behaviour (the F2P tests fix `args`/`kwargs`, not `path`, which the unchanged PASS_TO_PASS `test_deconstruct` path-assert already pins). |
| `TypeError` raised by the lone-non-pair special case | `Except DeconErr.notPair` (pre-patch only) | the crash the issue reports; the post-patch model is total (always `Except.ok`). |

## 3. Callee provenance (kind-A)

**None.** `deconstructNode` calls no unchanged callee whose behaviour the proof
must assume: the entire decomposition is local arithmetic over `children`,
`connector`, `negated` (list copy, two equality tests, two optional records),
modeled **deeply** by `deconstructed` (pure region). There is therefore **no
`axiom`** and **no G-AX obligation** (`axiom_check.py` is intentionally absent;
G-AX → skip, per gates.gate_ax). `tuple(...)`, `dict` literal construction, and
`!=` are concrete operations transliterated directly (I-tagged in refinement.md),
not axiomatized callees.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14140`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `deconstructed`/`deconstructNode` (R/I-tagged ops) to Python and
compares against the real patched `Q.deconstruct()` at base_commit, over the
full single-child boundary cross-product (`pair`/`node`/`expr` × `AND`/`OR` ×
`negated`) plus ≥10⁵ randomized multi-child nodes, checking args identity+order,
the absence of any keyword child recording, and the `_connector`/`_negated`
records. There are no A-tagged callees in the impl region.
