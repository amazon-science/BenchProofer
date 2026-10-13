import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle. The behavior under spec is
   a pure recognition cascade over the discrete argument pattern of a
   two-parameter special function: which closed form (if any) the function takes
   at a recognised pattern, and which series form its expansion takes at one
   distinguished parameter value. Every observable is computed from the inputs by
   a concrete dispatch; nothing is borrowed from an oracle. There is therefore no
   consumed axiom (mapping.md §3). That each abstract closed-form code names the
   value the real function actually takes at its pattern is an out-of-band
   obligation validated executably (axiom_check.py / G-AX), not assumed here. -/
-- axioms-end

-- pure-start
/- Closed-form result codes: opaque, pairwise-distinct identifiers, one per
   distinct closed form the recognition cascade can produce. `cfUneval` marks
   "no closed form" — the call stays unevaluated. The codes carry no arithmetic
   meaning inside the spec; that each names the value the real function takes at
   its pattern is the G-AX obligation (mapping.md / axiom_check.py). -/
def cfUneval : Int := 0   -- no closed form: the call stays unevaluated
def cfZa : Int := 1       -- first z-keyed pattern    (z = z_a)
def cfZb : Int := 2       -- second z-keyed pattern   (z = z_b)
def cfZc : Int := 3       -- third z-keyed pattern    (z = z_c)
def cfP1 : Int := 4       -- distinguished s, z = z_1
def cfP2 : Int := 5       -- distinguished s, z = z_2
def cfP3 : Int := 6       -- distinguished s, z = z_3
def cfP4 : Int := 7       -- distinguished s, z = z_4
def cfP5 : Int := 8       -- distinguished s, z = z_5
def cfP6 : Int := 9       -- distinguished s, z = z_6
def cfSa : Int := 10      -- first s-keyed pattern
def cfSb : Int := 11      -- second s-keyed pattern

/- Argument-pattern tags for the z component: the finite quotient of z by the
   nine equality tests the cascade branches on. `zOther` is any other z. -/
def zA : Int := 1
def zB : Int := 2
def zC : Int := 3
def z1 : Int := 4
def z2 : Int := 5
def z3 : Int := 6
def z4 : Int := 7
def z5 : Int := 8
def z6 : Int := 9
def zOther : Int := 0

/- Distinguished s-predicate values the cascade branches on. -/
def sSpecial : Int := 2   -- s value carrying the six special-z closed forms
def sKeyA : Int := 0      -- s value of the first s-keyed pattern
def sKeyB : Int := -1     -- s value of the second s-keyed pattern
def sExpand : Int := 1    -- s value whose series-expansion is pinned below

/- Series-expansion codes for the distinguished s. -/
def expPlain : Int := 1   -- elementary closed form in (1 - z): NO branch factor
def expPolar : Int := 2   -- carries a polar/branch factor on z

/- The closed-form code the function takes at argument pattern `(s, zTag)`,
   as a PRIORITY CASCADE. The three z-keyed clauses are matched first (for ANY
   s); then, at the distinguished `sSpecial`, the six special arguments; then the
   two s-keyed clauses. An unrecognised pattern yields no closed form
   (`cfUneval`). This map is concrete — it states only WHICH code each recognised
   pattern produces; the priority order (z-keyed before s-keyed) is part of the
   characterization. That the produced closed form equals the real function at
   the pattern is the G-AX obligation. -/
def closedFormFor (s : Int) (zTag : Int) : Int :=
  -- Priority 1: the z-keyed clauses, matched for any s.
  if zTag = zA then cfZa
  else if zTag = zB then cfZb
  else if zTag = zC then cfZc
  -- Priority 2: the six special arguments at the distinguished s.
  else if s = sSpecial then
    (if zTag = z1 then cfP1
     else if zTag = z2 then cfP2
     else if zTag = z3 then cfP3
     else if zTag = z4 then cfP4
     else if zTag = z5 then cfP5
     else if zTag = z6 then cfP6
     else cfUneval)
  -- Priority 3: the two s-keyed clauses.
  else if s = sKeyA then cfSa
  else if s = sKeyB then cfSb
  else cfUneval

/- The series-expansion closed-form code at the distinguished s: the elementary
   closed form in (1 - z) with NO polar/branch factor on z. -/
def expansionCode : Int := expPlain
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Recognise the closed form of a two-parameter special function at an argument
   pattern. The pattern is the discrete quotient of the symbolic arguments: `s`
   is the discrete parameter (only its values `sSpecial`, `sKeyA`, `sKeyB` are
   distinguished), and `zTag` is the finite quotient of the second argument by
   the nine recognised values (else `zOther`).

   The desired behaviour is a priority cascade: some patterns are keyed on the
   second argument alone and win first (for any `s`); a further group is keyed on
   the distinguished `s` together with one of several special second-argument
   values; and two more patterns are keyed on `s` alone. A pattern matched
   earlier wins over a later one at the same argument. Any pattern matching
   nothing produces `cfUneval` — the call stays unevaluated; the cascade must not
   over-fire. The result is exactly the cascade's choice, so it must produce a
   genuine closed form (not `cfUneval`) for every recognised pattern.

   `s`, `zTag` are read-only: the method computes and returns a code and never
   mutates its inputs. -/
method recognizeClosedForm (s : Int) (zTag : Int) return (out : Int)
  ensures out = closedFormFor s zTag
  ensures zTag = zC → out = cfZc
  ensures (s = sSpecial ∧ zTag = z1) → out = cfP1
  ensures (s = sSpecial ∧ zTag = z2) → out = cfP2
  ensures (s = sKeyA ∧ zTag = zOther) → out = cfSa
  ensures (s = sKeyB ∧ zTag = zOther) → out = cfSb
  ensures (zTag = zA ∧ s = sKeyA) → out = cfZa
  do
    -- impl-start
    -- Pre-image skeleton: only the three z-keyed clauses are recognised; every
    -- other argument pattern — including the distinguished-s special arguments
    -- and the two s-keyed patterns — is left unevaluated. The frozen spec
    -- requires the full cascade (closedFormFor), which produces genuine closed
    -- forms there, so prove_correct MUST fail.
    let result : Int :=
      if zTag = zA then cfZa
      else if zTag = zB then cfZb
      else if zTag = zC then cfZc
      else cfUneval
    return result
    -- impl-end

prove_correct recognizeClosedForm by
  loom_solve <;>
    simp_all [closedFormFor, zA, zB, zC, z1, z2, z3, z4, z5, z6, zOther,
      sSpecial, sKeyA, sKeyB, cfUneval, cfZa, cfZb, cfZc,
      cfP1, cfP2, cfP3, cfP4, cfP5, cfP6, cfSa, cfSb]

/- The series-expansion of the same function at the distinguished parameter
   `sExpand`. The desired behaviour: the expansion is the elementary closed form
   in `(1 - z)` carrying NO polar/branch factor on the second argument
   (`expPlain`), never the polar-factored form (`expPolar`). `s` is read-only. -/
method seriesExpansionAtOne (s : Int) return (out : Int)
  require s = sExpand
  ensures out = expansionCode
  ensures out = expPlain
  ensures out ≠ expPolar
  do
    -- impl-start
    return expPlain
    -- impl-end

prove_correct seriesExpansionAtOne by
  loom_solve <;> simp_all [expansionCode, expPlain, expPolar]
