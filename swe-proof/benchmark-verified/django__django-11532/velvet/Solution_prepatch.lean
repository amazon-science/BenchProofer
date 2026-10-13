import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The ASCII-compatible (punycode/RFC-3490) encoding of a domain name, as a pure
   function on code points. The only property the caller relies on is captured by
   `aceEncode_ascii`: the encoded domain is ASCII — every code point is below 128
   — so it is safe to place in a header that may later be rendered with a
   single-byte charset. We deliberately pin nothing about the exact encoded
   value; the weakest sufficient contract is the ASCII guarantee (mapping.md §3,
   directive 7). Provenance + executable soundness check: mapping.md / axiom_check.py
   (G-AX). -/
axiom aceEncode : List Char → List Char
axiom aceEncode_ascii : ∀ (d : List Char), ∀ c ∈ aceEncode d, c.val.toNat < 128
-- axioms-end

-- pure-start
/- The non-deterministic choice of the codec's result is well-posed: for any
   target value `v`, the set of values equal to `v` is non-empty (`v` itself).
   This supplies the constructive existence witness so the `:|` choice elaborates.
   It does NOT weaken verification: under demonic choice the postcondition must
   still hold for every value the predicate allows, here exactly `aceEncode host`. -/
noncomputable instance findableEqList (v : List Char) (n : Lean.Name) :
    Findable (fun e : List Char => typeWithName (e = v) n) where
  find := fun _ => some v
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A cached host name, made safe for use inside message headers.

   The desired behavior: the host name obtained from the environment is returned
   in its ASCII-compatible (punycode) encoding rather than verbatim. The result
   is exactly that encoding of the input (`out = aceEncode host`), and it is
   guaranteed to be ASCII — every code point is below 128 — so it can be embedded
   in a header that is subsequently rendered with a single-byte (non-Unicode)
   charset without failing.

   `host` is the read-only input host name (not `mut`): the routine consumes it
   and never alters it (directive 5). The host name is modeled as a `List Char`
   (a per-code-point string); ASCII-safety is the per-code-point predicate
   `c.val.toNat < 128` (mapping.md §2). -/
noncomputable section
method punycodeDomain (host : List Char) return (out : List Char)
  ensures out = aceEncode host
  ensures ∀ c ∈ out, c.val.toNat < 128
  do
    -- impl-start
    -- Pre-image skeleton: the host name is returned verbatim, without ASCII
    -- normalization. A non-ASCII host then violates the ASCII postcondition
    -- (and is not the codec's output), so prove_correct MUST fail (G-DIFF).
    let out := host
    return out
    -- impl-end
end

prove_correct punycodeDomain by
  loom_solve
  all_goals (intro c hc; exact aceEncode_ascii host c (by simp_all))
