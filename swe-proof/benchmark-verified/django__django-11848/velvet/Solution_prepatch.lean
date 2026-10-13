import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The reference point — the current calendar year — is
--  taken as a free input the operation reads from its environment, so NOTHING
--  is assumed about it: the contract must hold for every value it could take.
--  The abbreviated-year resolution is plain integer arithmetic, modeled in full
--  below; no outside callee contract is consumed.)
-- axioms-end

-- pure-start
/- Resolving a two-digit calendar year to a full year, relative to a reference
   year.

   A timestamp written with only the last two digits names some year whose last
   two digits are `yy`. It is resolved into the full year that has those last
   two digits and lies within the half-century window ending fifty years after
   the reference year: any candidate that would otherwise sit more than fifty
   years after the reference year is read as the most recent earlier year with
   the same last two digits (rolled back one century).

   `cc` is the reference year's own last two digits and `century` its hundreds
   part. The candidate in the reference century is `yy + century`; when that
   candidate's offset from the reference's last two digits exceeds fifty it is
   pulled back one full century. -/
def resolvedFullYear (yy cur : Int) : Int :=
  let cc := cur % 100
  let century := cur - cc
  if yy - cc > 50 then yy + century - 100 else yy + century
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve a two-digit calendar year `yy` (0..99) into a full year, using the
   current calendar year `cur` as the reference point.

   `yy` and `cur` are read-only inputs (neither is `mut`; nothing is mutated —
   directive 5). The result:

   * has the same last two digits as `yy` (it differs from `yy` by a whole
     number of centuries);
   * lies in the window `(cur - 100, cur + 50]` — i.e. it is never read as more
     than fifty years after the reference year, rolling over into the past
     instead;

   and is exactly the candidate selected by the resolution above. The
   discriminating inputs are those whose in-century candidate `yy + century`
   would land more than fifty years after the reference: there the result must
   roll back a century, rather than follow any constant last-two-digits
   threshold independent of the reference year. -/
method resolveAbbreviatedYear (yy : Int) (cur : Int) return (out : Int)
  require 0 ≤ yy ∧ yy ≤ 99
  require 0 ≤ cur
  ensures out = resolvedFullYear yy cur
  ensures (out - yy) % 100 = 0
  ensures cur - 100 < out ∧ out ≤ cur + 50
  do
    -- impl-start
    -- Pre-image skeleton: the abbreviated year is resolved against a FIXED
    -- two-digit cutoff (below seventy ⇒ the 2000s, otherwise the 1900s),
    -- ignoring the reference year `cur` entirely. The frozen spec requires
    -- out = resolvedFullYear yy cur (which rolls relative to `cur`), so
    -- prove_correct MUST fail.
    let out := if yy < 70 then yy + 2000 else yy + 1900
    return out
    -- impl-end

prove_correct resolveAbbreviatedYear by
  loom_solve
  all_goals simp only [resolvedFullYear]
