import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The only non-trivial callee touched is the standard
--  string operation that returns the final segment of a delimited string; it is
--  modeled DEEPLY by `afterLastHash` in the pure region (an A-reference), and
--  validated against the real library call by axiom_check.py (G-AX). Nothing is
--  axiomatized away.)
-- axioms-end

-- pure-start
/- One reference appearing in a diagram. The link map keys a fully-qualified
   class name to the URL the class should point at. A reference carries:
   * `name`     — the class key used to look the entry up;
   * `target`   — an explicit destination URL, if the class is documented;
   * `anchor`   — an in-page fragment id, used when there is no explicit target;
   * `outside` — whether the reference resolves outside the current project. -/
structure DiagRef where
  name : List Char
  target : Option (List Char)
  anchor : Option (List Char)
  outside : Bool
deriving Inhabited

/- The final segment of a `#`-delimited string: everything after the last `#`,
   or the whole string when there is no `#`. (Take from the end up to the last
   `#`, then restore order.) Deep model of the standard "split on the last
   delimiter, keep the tail" operation; validated == the real call by G-AX. -/
def afterLastHash (s : List Char) : List Char :=
  (s.reverse.takeWhile (· ≠ '#')).reverse

/- The link map entry a single reference contributes (zero or one pair):

   * With an explicit `target`, the entry maps to that target URL **verbatim**
     — never adorned with a leading relative-path prefix. The key is the
     reference `name` for an in-project class, but for an outside reference the
     key is recovered from the final segment of the target URL (so the diagram's
     class name resolves to the outside destination).
   * Otherwise, with an `anchor`, the entry maps `name` to a fragment link;
     under the embedded-object (SVG) rendering the link is taken relative to the
     page it sits on (`page` is prepended), and is a bare fragment otherwise.
   * With neither, the reference contributes nothing. -/
def refEntry (isSvg : Bool) (page : List Char) (c : DiagRef) : List (List Char × List Char) :=
  match c.target with
  | some uri => [(if c.outside then afterLastHash uri else c.name, uri)]
  | none =>
    match c.anchor with
    | some aid => [(c.name, (if isSvg then page else []) ++ ('#' :: aid))]
    | none => []

/- The whole link map: concatenate, in order, the per-reference entries.
   Front-recursive so a single unfold is available per loop step (the backward
   fold pattern). -/
def linkMap (isSvg : Bool) (page : List Char) : List DiagRef → List (List Char × List Char)
  | []      => []
  | c :: cs => refEntry isSvg page c ++ linkMap isSvg page cs

@[grind] lemma linkMap_nil (isSvg : Bool) (page : List Char) :
    linkMap isSvg page [] = [] := rfl
@[grind] lemma linkMap_cons (isSvg : Bool) (page : List Char) (c : DiagRef) (cs : List DiagRef) :
    linkMap isSvg page (c :: cs) = refEntry isSvg page c ++ linkMap isSvg page cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the link map for a diagram: walk its references in order and collect
   each one's contributed entry. `refs`, `isSvg`, `page` are read-only
   (directive 5). -/
method buildLinkMap (refs : List DiagRef) (isSvg : Bool) (page : List Char)
    return (out : List (List Char × List Char))
  ensures out = linkMap isSvg page refs
  do
    -- impl-start
    -- PRE-IMAGE skeleton: for a fragment-only reference, the buggy build under
    -- SVG rendering prepends a relative "../" prefix in FRONT of the page path,
    -- yielding "../" ++ page ++ "#" ++ anchor. The frozen spec emits the
    -- fragment link relative to the page with NO "../" prefix, so
    -- `prove_correct` MUST fail on an `anchor = some _` reference under SVG.
    let mut acc : List (List Char × List Char) := []
    let mut i := refs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ refs.length
      invariant acc = linkMap isSvg page (refs.drop i)
      done_with i = 0
      decreasing i
    do
      let c := refs[i - 1]!
      let e : List (List Char × List Char) :=
        match c.target with
        | some uri => [(if c.outside then afterLastHash uri else c.name, uri)]
        | none =>
          match c.anchor with
          | some aid => [(c.name, (if isSvg then "../".toList ++ page else []) ++ ('#' :: aid))]
          | none => []
      acc := e ++ acc
      i := i - 1
    return acc
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `linkMap` peels one `refEntry`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma linkMap_drop_step (isSvg : Bool) (page : List Char) (xs : List DiagRef) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    linkMap isSvg page (xs.drop (i - 1))
      = refEntry isSvg page xs[i - 1]! ++ linkMap isSvg page (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, linkMap_cons]

prove_correct buildLinkMap by
  loom_solve
  rw [linkMap_drop_step isSvg page refs i (by omega) (by omega)]
  simp_all
