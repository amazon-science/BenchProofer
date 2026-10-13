import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees consumed in the proof. The description algebra in the
--  `pure` region is a deep model — how an index set is ASSEMBLED out of the
--  index domain and the listed factors, plus the indices such an assembly picks
--  out — validated against the real repo callees by G-AX, see refinement.md /
--  mapping.md.)
-- axioms-end

-- pure-start
/- A factor of one of the two components, carried as the factor ITSELF — a
   handle that bears its own identity — and NOT as the collection of values it
   takes.

   That distinction is part of the observable answer. Which value a factor takes
   at an index is READ OFF the factor, by `valueOf` below, and that reading does
   NOT determine the factor: two DIFFERENT factors can take the same value at
   every single index — `(n - 1)(n + 1)` and `n² - 1` do, and so do
   `n² - n/2 - 1/2` and `(n - 1)(2n + 1)/2`. Wherever an index set is described
   BY a factor rather than
   by naming indices, the description names THAT factor, so a description built
   from another factor of equal value everywhere holds exactly the same indices
   and is a DIFFERENT description. `Factor` therefore exposes nothing but its
   identity: the values are reached only through `valueOf`, so no factor can be
   manufactured out of the values any factor takes, and only the factors handed
   in can appear in an answer, each of them as handed in. -/
structure Factor where
  /- what tells one factor from another. -/
  ident : Nat
deriving DecidableEq

/- The value a factor takes at an index: `valueOf g k = some q` when the factor
   `g` takes the rational value `q` at index `k`, and `valueOf g k = none` at an
   index where it takes no rational value at all — an index that makes the
   factor's own denominator vanish, for instance. Factors are NOT assumed
   integer-valued: at index `0` a factor `n + 1/2` takes the value `1/2`, and at
   index `0` a factor `1/n - 1` takes no value. The reading is a function OF a
   factor, which is what makes the values a consequence of the factor rather
   than the factor a consequence of its values. -/

/- The set of indices at which a single factor vanishes: the `n` whose value
   there is `some 0`. An index at which the factor takes no rational value is
   not one of them — a factor with no value there is not a factor equal to zero
   there. -/
def vanishingSet (valueOf : Factor → Int → Option Rat) (g : Factor) : Set Int :=
  {n | valueOf g n = some 0}

/- The set of indices at which ANY factor in a list vanishes: `n` such that some
   `g` in the list has `valueOf g n = some 0`. This is the union, over the listed
   factors, of their individual vanishing sets. -/
def anyVanishes (valueOf : Factor → Int → Option Rat) (gs : List Factor) : Set Int :=
  {n | ∃ g, g ∈ gs ∧ n ∈ vanishingSet valueOf g}

/- HOW an index set is assembled, not merely WHICH indices it holds.

   The answer this routine produces is handed back to its caller as an index-set
   DESCRIPTION and is what the caller then reports: for the family of the issue
   the answer asked for is the two-element enumeration `{-1, 1}`, and an equally
   true description of the same two indices — "the integers at which
   `(n - 1)(n + 1)` vanishes" — is a different answer, because it names no
   index. So the assembly is part of the observable result: two descriptions
   holding the same indices, put together differently, are DIFFERENT results.

   That applies to the index domain the assembly starts from just as much as to
   the rest of the tree, which is why the domain enters a description as the
   ATOM `given` and not as a set of indices. `given` stands for the domain
   handed in, ITSELF; no description of the same indices can be put in its
   place. Narrowing the domain by a condition that in fact excludes nothing —
   keeping, say, only the indices that either do or do not make some factor
   vanish — describes exactly the domain's own indices and is still a DIFFERENT
   description of them, hence a different answer. It applies to the FACTORS a
   description is built out of in exactly the same way: a description carries
   the factors themselves, so putting in a factor's place another factor of
   equal value at every index describes exactly the same indices and is again a
   different answer.

   * `given`          — the index domain handed in, exactly as handed in.
   * `noIndices`      — a description holding no index at all.
   * `zerosOfAny gs`  — one contribution per LISTED factor, collected together:
                        the indices at which any one of `gs` vanishes, each
                        factor of the list resolved on its own and taken as
                        handed in. A list of several factors is NOT
                        interchangeable with a single factor vanishing at the
                        same indices — resolving the factors one at a time is
                        what names the individual indices; a factor is NOT
                        interchangeable with another factor of equal value
                        everywhere, since the description carries the factor and
                        not its values; and the empty list contributes nothing.
   * `meet a b`       — the indices held by both descriptions.
   * `apart a b`      — the indices held by the first and not by the second.
   * `either a b`     — the indices held by the one description or the other.
   * `otherIndices a` — the indices the description does not hold.

   `noIndices`, `either` and `otherIndices` are here so that the OTHER ways of
   describing a collection of indices — a description enlarged and then cut back
   down, a domain masked by a condition that excludes nothing, a leg taken apart
   from nothing — are all expressible descriptions, and the answer clause below
   says which single description is asked for rather than accepting whichever
   assembly happens to hold the right indices. -/
inductive IndexReport where
  | given
  | noIndices
  | zerosOfAny (gs : List Factor)
  | meet (a b : IndexReport)
  | apart (a b : IndexReport)
  | either (a b : IndexReport)
  | otherIndices (a : IndexReport)

/- The indices a description picks out, given the index domain it was assembled
   over and the reading of its factors' values, so that a description can also
   be read as a plain set of indices. -/
def reported (domain : Set Int) (valueOf : Factor → Int → Option Rat) :
    IndexReport → Set Int
  | .given => domain
  | .noIndices => (∅ : Set Int)
  | .zerosOfAny gs => anyVanishes valueOf gs
  | .meet a b => reported domain valueOf a ∩ reported domain valueOf b
  | .apart a b => reported domain valueOf a \ reported domain valueOf b
  | .either a b => reported domain valueOf a ∪ reported domain valueOf b
  | .otherIndices a => (reported domain valueOf a)ᶜ

/- WHAT THE ROUTINE IS TOLD ABOUT THE IMAGINARY PART, which is what settles
   whether there is anything to keep the index domain down to at all.

   The imaginary part is settled — zero, or not zero — before any index set is
   put together, and only two of the outcomes of that settling reach an assembly
   at all. They reach it in different shapes, and the shape is an INPUT: it is
   read off the imaginary part alone, never chosen by the answer.

   * `zeroThroughout` — the imaginary part is settled to be zero, at every index
                        at once. Every member of the family is then already
                        real, so NO factor of it is resolved and no list of its
                        factors is even formed: there is nothing to keep the
                        domain down to, and the assembly starts from the index
                        domain itself.
   * `factors gs`     — the imaginary part is not settled either way, and it is
                        handed over as the list `gs` of the factors it splits
                        into, to be resolved one at a time. The family's value
                        is real at an index exactly when one of `gs` vanishes
                        there.

   The two shapes call for DIFFERENT assemblies and not merely for different
   indices, which is why the shape has to be told and cannot be recovered from
   the indices: an answer for `zeroThroughout` holds no keep node at all, while
   an answer for `factors gs` holds one, and that difference survives even where
   the two hold exactly the same indices — a factor list that vanishes at every
   index of the domain keeps the domain down to the whole of itself, and a
   description that keeps a domain down to all of itself is still not the
   description that never narrowed it. -/
inductive ImaginaryPart where
  | zeroThroughout
  | factors (gs : List Factor)

/- The keep leg of the assembly: what the index domain has been narrowed to by
   the time the undefined indices are taken apart from it.

   Where the imaginary part is settled to be zero throughout there is nothing to
   narrow by, and the leg is the index domain ITSELF — the atom `given`, with no
   node standing over it. Where the imaginary part is handed over as factors, the
   leg is that same domain KEPT DOWN TO (`meet`) the per-factor zero-index
   collection of those factors, resolved one factor at a time and each taken as
   handed in. -/
def keptToReal : ImaginaryPart → IndexReport
  | .zeroThroughout => .given
  | .factors gs => .meet .given (.zerosOfAny gs)

/- The indices of the domain at which the family's value is real, read as a
   plain set of indices: every index of the domain where the imaginary part is
   settled to be zero throughout, and the domain's indices at which one of the
   handed-over factors vanishes where it is not. -/
def realIndices (domain : Set Int) (valueOf : Factor → Int → Option Rat) :
    ImaginaryPart → Set Int
  | .zeroThroughout => domain
  | .factors gs => domain ∩ anyVanishes valueOf gs
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Restrict an integer-indexed family of complex values to the indices whose
   value is real and well-defined, and describe that restriction to the caller.

   An index `n` ranging over `domain` produces a complex value with a real part
   and an imaginary part, each a rational function of `n`. The value is a REAL
   member of the family exactly when

     * the imaginary part is zero at `n`  (so the value is real), and
     * the value is defined at `n`        (no denominator of the family
                                            expression is zero there).

   `imaginaryPart` is what the routine has been told about the imaginary part
   (`ImaginaryPart` above): either that it is settled to be zero at every index
   at once, in which case no factor of it is resolved and none is even listed, or
   the list of factors it splits into, the imaginary part being zero at `n`
   exactly when one of them is. `denominators` are the denominator factors
   whose vanishing makes the value undefined
   (`anyVanishes valueOf denominators`); and `valueOf` reads the value any
   factor takes at an index. The surviving indices are therefore those of
   `domain` at which the value is real (`realIndices`) that avoid every
   denominator's zero set.

   The answer is that restriction AS ASSEMBLED from the pieces handed in, and
   the assembly follows the two shapes the imaginary part can arrive in
   (`keptToReal`), because the two are put together differently:

     * settled zero throughout — the index domain ITSELF (`given`), taken APART
       FROM (`apart`) the per-factor zero-index collection of `denominators`.
       NOTHING is kept down to and no keep node is built, since no factor of the
       imaginary part is resolved: an answer that narrows the domain here — even
       by a collection that in fact excludes no index, such as one whose factors
       vanish everywhere — is a different description of the same indices and is
       not the description asked for.
     * handed over as factors — the index domain ITSELF (`given`), KEPT DOWN TO
       (`meet`) the per-factor zero-index collection of those factors, and then
       taken APART FROM (`apart`) the per-factor zero-index collection of
       `denominators`.

   Nothing else stands between the domain and the keep: an assembly that first
   re-describes the domain — masking it with a condition that excludes no index,
   splitting it and putting the pieces back together, taking it apart from a
   description holding no index — answers with a description that holds the same
   indices and is not the description asked for. Both collections resolve their
   list ONE FACTOR AT A TIME, in the order given, which is what turns a factored
   imaginary part into named indices rather than an unresolved condition, and
   both collections hold the factors THEMSELVES, as handed in: a collection whose
   factors have been put in place of by others of equal value at every index
   likewise describes the same indices and is not the collection asked for. Each
   of the two lists is used for its own role only. Keeping every index whose
   imaginary part is nonzero — failing to keep the domain down to the zero
   indices where the imaginary part is handed over as factors — would let
   non-real members through, which is exactly the discrepancy the issue reports;
   describing the same indices by some other assembly answers a different
   question than the one asked, as the issue's expected `{-1, 1}` shows.

   `domain`, `imaginaryPart`, `denominators`, `valueOf` are read-only (none is
   `mut`): the routine computes the description and mutates no input
   (directive 5). The index domain is modeled as `Set Int`, a factor as a
   handle bearing its own identity whose value at an index is read by `valueOf`
   (`none` where it has no rational value), what is known of the imaginary part
   as the two-shape `ImaginaryPart`, and the assembled answer as an
   `IndexReport` whose `reported domain valueOf` indices are the surviving ones
   (mapping.md §2). -/
method restrictToRealValues (domain : Set Int) (imaginaryPart : ImaginaryPart)
    (denominators : List Factor) (valueOf : Factor → Int → Option Rat)
    return (out : IndexReport)
  ensures out = .apart (keptToReal imaginaryPart) (.zerosOfAny denominators)
  ensures reported domain valueOf out
      = realIndices domain valueOf imaginaryPart
          \ anyVanishes valueOf denominators
  do
    -- impl-start
    -- Take the index domain apart from the indices at which the value is
    -- undefined (a denominator vanishes), resolving those factors one at a time.
    let mut acc : IndexReport := .given
    acc := .apart acc (.zerosOfAny denominators)
    return acc
    -- impl-end

prove_correct restrictToRealValues by
  loom_solve <;> cases imaginaryPart <;>
    simp [reported, keptToReal, realIndices]
