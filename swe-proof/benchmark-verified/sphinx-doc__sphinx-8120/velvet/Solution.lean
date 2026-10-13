import Velvet.Std
-- imports-end

-- Total-correctness semantics: the operation under spec is straight-line
-- (three list appends; no loops or recursion — it always returns), so the
-- contract also demands termination. Under partial semantics a diverging
-- body would vacuously satisfy every postcondition.
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (no consumed axioms: the method's output is pinned structurally and the
--  search-order resolver below is a deep model validated against the real
--  message-catalog loader by axiom_check.py / G-AX.)
-- axioms-end

-- pure-start
/- A localization search entry is identified by its directory path. The
   system-default entry (a sentinel carrying no path) is just another entry in
   the ordered search list. -/
abbrev Dir := String

/- The message-catalog loader's lookup semantics: directories are searched in
   list order and the FIRST entry that defines a message supplies it; later
   entries only fill in messages no earlier entry defined. Front-recursive so a
   single unfold is available per step. `cat d k` is the translation directory
   `d` provides for message `k` (`none` if it provides none). Provenance +
   executable soundness check: mapping.md / axiom_check.py (G-AX). -/
def resolve (cat : Dir → String → Option String) : List Dir → String → Option String
  | [],      _ => none
  | d :: ds, k => (cat d k).orElse (fun _ => resolve cat ds k)

@[grind] lemma resolve_nil (cat : Dir → String → Option String) (k : String) :
    resolve cat [] k = none := rfl
@[grind] lemma resolve_cons (cat : Dir → String → Option String)
    (d : Dir) (ds : List Dir) (k : String) :
    resolve cat (d :: ds) k = (cat d k).orElse (fun _ => resolve cat ds k) := rfl

/- Searching a concatenation searches the prefix first; the suffix is consulted
   only when the prefix defines nothing. -/
lemma resolve_append (cat : Dir → String → Option String)
    (xs ys : List Dir) (k : String) :
    resolve cat (xs ++ ys) k
      = (resolve cat xs k).orElse (fun _ => resolve cat ys k) := by
  induction xs with
  | nil => simp [resolve]
  | cons d ds ih =>
    simp only [List.cons_append, resolve]
    cases h : cat d k with
    | none => simp [ih]
    | some v => simp

/- Behavioral consequence of the search order produced below: a message that any
   user-provided entry defines (and that the system-default entry does not) is
   resolved to that user value — the trailing package entry can never shadow it.
   This is the abstract property the issue demands (user overrides take effect);
   it is generic over the catalog contents and holds for the exact ordering the
   method returns. -/
lemma resolve_user_precedence
    (cat : Dir → String → Option String) (repoDirs : List Dir)
    (sysNone packageLocale : Dir) (k : String)
    (hsys : cat sysNone k = none)
    (huser : (resolve cat repoDirs k).isSome) :
    resolve cat (sysNone :: (repoDirs ++ [packageLocale])) k
      = resolve cat repoDirs k := by
  rw [resolve_cons, hsys, resolve_append]
  cases h : resolve cat repoDirs k with
  | none => rw [h] at huser; simp at huser
  | some v => simp
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the ordered localization search list from: the system-default entry,
   the user-provided entries, and the bundled package entry. The order is what
   determines precedence (earlier wins, per `resolve`). -/
method buildLocaleDirs (repoDirs : List Dir) (sysNone : Dir) (packageLocale : Dir)
    return (out : List Dir)
  ensures out = sysNone :: (repoDirs ++ [packageLocale])
  do
    -- impl-start
    let mut localeDirs : List Dir := [sysNone]
    localeDirs := localeDirs ++ repoDirs
    localeDirs := localeDirs ++ [packageLocale]
    return localeDirs
    -- impl-end

prove_correct buildLocaleDirs by
  loom_solve
