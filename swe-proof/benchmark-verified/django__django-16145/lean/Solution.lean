import Mathlib
-- imports-end

/-!
Presenting a development server's bind host in its start-up banner URL.

When a lightweight development server announces the address it is listening on,
it must render the bind host as a piece of a clickable `protocol://host:port/`
URL. Two presentation rules apply to the host component:

  * a raw IPv6 literal must be wrapped in square brackets, so that it composes
    into a valid URL authority (`[host]`);
  * the unspecified-address shorthand `"0"` — which denotes binding on every
    available interface — must be shown in its canonical dotted form
    `"0.0.0.0"`, the form a web browser will actually follow.

Every other host is presented verbatim. The bracket rule takes precedence: a raw
IPv6 literal is always bracketed regardless of its textual content.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification: the displayed
-- host is a closed expression over the resolved bind host and the raw-IPv6 flag,
-- using only string equality, concatenation, and two literals. No `opaque`/
-- `axiom` callee contract is needed.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed.)
-- pure-end

-- post-conditions-start
/-- The displayed host is pinned for every combination of inputs (directive 5:
no case is left unconstrained). `rawIpv6` records whether the resolved host is a
raw IPv6 literal; `addr` is the resolved bind host. A raw IPv6 literal is
bracketed; otherwise the shorthand `"0"` becomes `"0.0.0.0"` and any other host
is shown unchanged. -/
def problem_spec_displayAddr (rawIpv6 : Bool) (addr : String) (result : String) : Prop :=
  (rawIpv6 = true → result = "[" ++ addr ++ "]") ∧
  (rawIpv6 = false → addr = "0" → result = "0.0.0.0") ∧
  (rawIpv6 = false → addr ≠ "0" → result = addr)
-- post-conditions-end

-- impl-start
def implementation_displayAddr (rawIpv6 : Bool) (addr : String) : String := Id.run do
  if rawIpv6 then
    return "[" ++ addr ++ "]"
  else if addr = "0" then
    return "0.0.0.0"
  else
    return addr
-- impl-end

-- proof-start
theorem correct_displayAddr : ∀ (rawIpv6 : Bool) (addr : String),
    problem_spec_displayAddr rawIpv6 addr (implementation_displayAddr rawIpv6 addr) := by
  intro rawIpv6 addr
  unfold problem_spec_displayAddr implementation_displayAddr
  refine ⟨?_, ?_, ?_⟩
  · intro h
    subst h
    rfl
  · intro h haddr
    subst h
    subst haddr
    rfl
  · intro h haddr
    subst h
    simp only [Id.run, Bool.false_eq_true, if_false, if_neg haddr]
    rfl
-- proof-end
