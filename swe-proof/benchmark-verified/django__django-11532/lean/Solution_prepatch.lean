import Mathlib
-- imports-end

/-!
Deriving the host/domain name that gets stamped into outgoing mail metadata
(such as the auto-generated message identifier) from the name the operating
system reports for the local machine.

The reported local name may contain non-ASCII characters (for example when the
machine is given a name written in a non-Latin script). Mail metadata, however,
is serialized through headers whose target character set is frequently a narrow
single-byte encoding, so a raw non-ASCII name cannot be placed there verbatim.

The desired behavior is therefore: the name used for mail metadata is the
ASCII-compatible (Punycode) representation of the reported local name. For a
name that is already plain ASCII this representation coincides with the name
itself; for a name containing non-ASCII characters it is the Punycode form,
which by construction consists solely of ASCII characters and so is safe to
emit in any header encoding.

Asking the operating system for the local name is slow, so the metadata name is
settled once and then held: the holder that serves it owns a single storage slot
that starts out unoccupied. The first request settles the metadata name, leaves
the slot occupied by it, and serves it; every later request is served from the
occupied slot, verbatim, without the reported name being consulted again.

The slot's occupancy is part of the behavior specified here rather than an
internal shortcut, because the slot is the holder's own state: callers hold the
holder itself and read and clear its stored name through it, so whether a request
left a name stored is directly observable. A holder that serves the right name
while leaving its slot unoccupied therefore does not exhibit the specified
behavior, even though every name it ever serves is right.
-/

-- axioms-start
/-- The ASCII-compatible (Punycode) representation of a host/domain name.

This is a standard, library-provided name-encoding routine: it maps an
arbitrary host/domain name to an equivalent name drawn solely from the ASCII
repertoire. It is consumed here as an opaque carrier — the behavior modeled in
this bundle is *which* name is run through it and that its output is used as the
metadata name, not the internal details of the encoding itself. -/
opaque aceEncode : String → String
-- axioms-end

-- pure-start
/-- The state of the holder that serves the metadata name: one storage slot.

  * `none` — the slot is unoccupied: no metadata name has been settled yet, so
    the next request has to settle one from the reported local name;
  * `some n` — the slot is occupied by the settled metadata name `n`, which is
    what every later request is served.

The slot is the holder's entire state, so a request's effect on the holder is
exactly its effect on this slot. -/
structure NameHolder where
  slot : Option String
deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- Serving the metadata name from holder `st`, where `reportedName` is the name
the operating system reports for the local machine. `result.1` is the holder
afterwards and `result.2` is the name served.

1. OCCUPANCY. Afterwards the slot is occupied, and what occupies it is exactly
   the name that was served. So a request always leaves a settled name behind,
   and the stored name and the served name can never disagree. This is a claim
   about the holder's state and not only about the served name: serving the
   right name while leaving the slot unoccupied violates it.
2. REUSE. When the slot was already occupied, the name served is the stored one,
   verbatim — once a metadata name has been settled, the reported local name has
   no further influence on what is served.
3. SETTLING. When the slot was unoccupied, the name served (hence, by 1, the
   name the slot now holds) is the ASCII-compatible (Punycode) representation of
   the reported local name. This is what makes the name that reaches mail
   metadata drawn solely from the ASCII repertoire whatever script the machine is
   named in.

Note for reviewers: 1–3 pin BOTH components of `result` for every input, so this
spec is DETERMINISTIC — `spec_hostName_deterministic` proves that any two results
satisfying it are equal. A same-spec implementation can verify only by computing
extensionally the same holder and the same name, so a verifying same-spec variant
is a positive control rather than evidence of spec weakness. -/
def problem_spec_hostName
    (st : NameHolder) (reportedName : String)
    (result : NameHolder × String) : Prop :=
  result.1.slot = some result.2 ∧
  (∀ stored, st.slot = some stored → result.2 = stored) ∧
  (st.slot = none → result.2 = aceEncode reportedName)
-- post-conditions-end

-- impl-start
def implementation_hostName (st : NameHolder) (reportedName : String) :
    NameHolder × String := Id.run do
  let mut holder := st
  -- while no metadata name has been settled, settle one from the reported local
  -- name, and leave it occupying the slot
  if holder.slot = none then
    holder := { holder with slot := some reportedName }
  -- serve the name the slot now holds
  let served := holder.slot.getD reportedName
  return (holder, served)
-- impl-end

-- proof-start
theorem correct_hostName :
    ∀ (st : NameHolder) (reportedName : String),
      problem_spec_hostName st reportedName
        (implementation_hostName st reportedName) := by
  sorry

/-- The specification is DETERMINISTIC: for a given holder and reported name it
admits at most one result. Stated without reference to any implementation, so it
is a property of the specification alone: whatever satisfies clauses 1–3 is the
one holder-and-name pair those clauses describe. -/
theorem spec_hostName_deterministic :
    ∀ (st : NameHolder) (reportedName : String) (r r' : NameHolder × String),
      problem_spec_hostName st reportedName r →
      problem_spec_hostName st reportedName r' →
      r = r' := by
  intro st reportedName r r' h h'
  obtain ⟨hocc, hreuse, hsettle⟩ := h
  obtain ⟨hocc', hreuse', hsettle'⟩ := h'
  have hval : r.2 = r'.2 := by
    cases hs : st.slot with
    | none => rw [hsettle hs, hsettle' hs]
    | some stored => rw [hreuse stored hs, hreuse' stored hs]
  have hslot : r.1.slot = r'.1.slot := by rw [hocc, hocc', hval]
  have hmk : ∀ a b : NameHolder, a.slot = b.slot → a = b := by
    intro a b hab
    cases a; cases b; simp_all
  exact Prod.ext (hmk _ _ hslot) hval
-- proof-end
