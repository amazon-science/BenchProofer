import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- An opaque symbolic object: the set's own binder once it has left the binder
   slot, the object a substitution replaces once it has left that role, or the
   replacement once it has left its own. The operation never inspects internal
   structure — only which object reaches which slot of the rebuilt set matters —
   so it is left fully opaque (directive 7: the weakest sufficient contract is
   none). The bijection to the repository value space is in mapping.md §2 (G-AX /
   G-CONF use it). -/
axiom Obj : Type

/- An opaque filtering condition, a SORT OF ITS OWN rather than another `Obj`.
   The distinction is load-bearing rather than cosmetic: the set constructor is
   PARTIAL in this slot — handed something that is not a condition it signals an
   error instead of building a set — so "is a condition" belongs to the
   constructor's DOMAIN, not to a fact about its result (mapping.md §3.3). -/
axiom Cond : Type

/- An opaque set in the COMPONENT role: the set being filtered, or that set with
   a substitution pushed through it. A sort of its own for the same reason as
   `Cond` — the constructor is PARTIAL in its base slot and signals an error when
   handed something that is not a set (mapping.md §3.3). -/
axiom SetObj : Type

/- The set this operation PRODUCES: the rebuilt membership-style set. A sort of
   its own, distinct from the component sort `SetObj`, because the roles are
   distinct in the operation being modeled: it reads the set's stored components
   and delivers a newly built set, and it never feeds a set it has just built
   back into a component position. Keeping the two roles apart is what makes the
   substitution callee's receiver un-manufacturable here: every receiver this
   model can name is the stored base set or a substituted form of it, which is
   exactly the receiver the real operation substitutes into (mapping.md §3.4). -/
axiom BuiltSet : Type

/- The set's own binder: a plain single symbol, the kind of binder the set
   actually binds — as opposed to the legacy compound (multi-symbol /
   unsolved-system) binder form, on which substitution short-circuits and leaves
   the whole set untouched, and as opposed to a compound expression in the binder
   slot, on which the set constructor is itself only partially defined
   (mapping.md §2, §3.3). A sort of its own rather than a predicate over `Obj`,
   so that this domain restriction is carried by the binder's TYPE and the
   excluded forms cannot be named here at all. -/
axiom Binder : Type

/- The object a substitution REPLACES — the first of the two arguments the
   operation receives. A sort of its own, distinct from `New` and from `Obj`,
   because the two substitution arguments play distinct, asymmetric roles: the
   operation only ever replaces this one BY that one, at the two component slots,
   and never in the other direction and never with the set's own binder in this
   role. Sorting the two roles apart is what keeps the set of substitutions this
   model can name down to the single one the operation was handed (mapping.md
   §3.4). -/
axiom Old : Type

/- The object a substitution puts in the replaced object's place — the second of
   the two arguments the operation receives, a sort of its own for the same
   reason as `Old`. -/
axiom New : Type

/- The object the set's own binder is once it leaves the binder slot — how it is
   named when a substitution argument could refer to it. -/
axiom binderObj : Binder → Obj

/- The replaced object seen as an ordinary object — how it is named when it
   occupies a plain slot rather than its substitution role. -/
axiom oldObj : Old → Obj

/- The replacement seen as an ordinary object, for the same reason as `oldObj`. -/
axiom newObj : New → Obj

/- Push a substitution through a condition (the condition, then the object
   replaced, then its replacement). An UNCHANGED structural-substitution callee
   the operation delegates to; left fully opaque — the operation assumes nothing
   about the substituted condition beyond its still being a condition.

   This callee is PARTIAL, and that part of its partiality is not sortal: handed
   a replacement that the condition cannot be compared against, it signals an
   error instead of delivering a condition. That domain is carried by the
   precondition `CondSubDefined` below, and the sorts of the two substitution arguments keep
   the substitutions nameable here down to the one the operation was handed, so
   that the precondition covers every condition substitution this model can
   express (mapping.md §3.4). Provenance and executable soundness check:
   mapping.md §3.1 / axiom_check.py (G-AX). Tagged A-reference. -/
axiom substCond : Cond → Old → New → Cond

/- Push a substitution through a set: the SAME unchanged callee at the base-set
   slot, delivering a set in the same component role. Opaque, no `ensures`;
   PARTIAL in the same way as `substCond`, with `BaseSubDefined` for its domain.
   mapping.md §3.1, §3.4 / axiom_check.py (G-AX). Tagged A-reference. -/
axiom substSet : SetObj → Old → New → SetObj

/- The condition substitution is DEFINED — the domain of the condition-slot
   invocation of the substitution callee. Opaque: nothing about a condition is
   derivable from it, it only records that the callee delivers a condition here
   rather than signalling an error. It is a PRECONDITION of the operation and not
   an assumption about the callee's result, because the real operation has no
   answer either on inputs outside it: it propagates the error rather than
   returning a set (mapping.md §3.4). -/
axiom CondSubDefined : Cond → Old → New → Prop

/- The base-set substitution is DEFINED — the same domain fact at the base slot. -/
axiom BaseSubDefined : SetObj → Old → New → Prop

/- Build the membership-style set: the elements of the base set that the
   condition keeps, bound by the set's own binder. An UNCHANGED constructor the
   operation delegates to; left fully opaque — the operation never inspects the
   set it produces, it only chooses WHICH binder, condition and base set to hand
   it.

   The SORTS of the three slots are what model the SORTAL part of the
   constructor's PARTIALITY, and this is the reason they are three sorts rather
   than three `Obj`s. The constructor is not defined on arbitrary arguments:
   handed something that is not a condition, or something that is not a set as
   the base, or an object in the binder slot that the condition does not actually
   bind, it signals an error instead of returning a set (mapping.md §3.3).

   The sorts alone are not the whole domain, and the remainder is not sortal:
   every slot can hold the right kind of object and the constructor still signal
   an error, because building the set TESTS THE CONDITION AGAINST THE ELEMENTS of
   a finite base, and an element the condition cannot be compared against makes
   that test signal instead of answering (mapping.md §3.5). That part is carried
   by the precondition `BuildsDefined` below. Restricted to these three sorts AND
   to the arguments that precondition admits, the callee is TOTAL — measured
   against the real one by axiom_check.py — so every invocation this model can
   express is one the real constructor accepts, and an invocation it would refuse
   is UNWRITABLE here rather than merely unproven, including one whose result is
   discarded, which a total function of unsorted handles could never be observed
   to have made. Tagged A-reference. -/
axiom mkSet : Binder → Cond → SetObj → BuiltSet

/- Build the membership-style set keyed on a plain OBJECT rather than on the
   set's own binder: the object is bound over the membership test of that very
   object in the base set — the shape the problem statement's own transcript
   displays for `Out[75]`. A second invocation shape of the SAME unchanged
   constructor, and the only other one it is defined on: an arbitrary object is
   accepted in the binder slot exactly when the condition mentions it, and a
   membership test of the object against the set it is being bound over does
   mention it (which is also why the base set here is a single argument, used
   both as the set tested and as the set bound over — the constructor is NOT
   defined when those two differ). Restricted this way, and to the arguments the
   precondition below admits, it is TOTAL, measured against the real callee by
   axiom_check.py. mapping.md §3.3. Tagged A-reference. -/
axiom mkSetOnValue : Obj → SetObj → BuiltSet

/- The set-building callee is DEFINED at these arguments — the part of the
   constructor's domain that no sorting can express. Building the set tests the
   condition against the elements of a finite base, so an element the condition
   cannot be compared against makes the constructor signal an error even though
   each slot holds exactly the kind of object it asks for. Opaque: nothing about
   a set, a condition or a binder is derivable from it. A PRECONDITION rather
   than an assumption about a result, for the same reason as the two substitution
   definedness facts above — where the constructor signals, the real operation
   has no result either, it propagates the signal instead of delivering a set,
   and a contract read under total semantics may only promise a result where the
   real operation has one.

   It ranges over EVERY set-building invocation this model can name at these
   arguments — either shape, at the stored condition and base set and at their
   substituted forms, keyed on the binder or on either substitution argument —
   and not merely over the one the contract returns. That is what licenses
   treating the two building axioms as total functions of their sorts: with this
   precondition in force, every application the impl region can write, INCLUDING
   one whose result is discarded, denotes an invocation the real constructor
   accepts. axiom_check.py measures its coverage, the density of the domain it
   leaves, and the real refusals that force it (mapping.md §3.5). -/
axiom BuildsDefined : Binder → Cond → SetObj → Old → New → Prop
-- axioms-end

-- pure-start
/- The intended outcome of replacing a free symbol `old` — one that is NOT the
   set's own binder — by `new`, inside the set { boundSym | condition, over
   baseSet }:

   push the substitution through the condition and through the base set, then
   rebuild the same kind of set, keeping the set's ORIGINAL binder. The binder is
   internal to the set: it is never a substitution target, so substituting some
   other symbol must leave it in place, and the rebuilt set must still be bound
   by it. -/
noncomputable def evalSubsSpec (boundSym : Binder) (condition : Cond)
    (baseSet : SetObj) (old : Old) (new : New) : BuiltSet :=
  mkSet boundSym (substCond condition old new) (substSet baseSet old new)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Substitute `new` for the symbol `old` in a membership-style set
   { boundSym | condition, over baseSet }, in the case where `old` is a free
   symbol distinct from the set's own binder.

   `boundSym`, `condition`, `baseSet`, `old`, `new` are all read-only (none is
   `mut`). Desired behavior: the substitution is pushed through the condition and
   through the base set by the standard substitution helper, and the result is the
   set rebuilt from those two substituted components, still bound by the set's
   ORIGINAL binder. The binder is the set's own internal one; substituting a
   different, free symbol must never rename or replace it — even if the
   substituted condition happens to simplify (mapping.md §2).

   The binder's sort `Binder` carries the domain restriction to a plain single
   symbol: on the legacy compound-binder form the real operation short-circuits
   and returns the set untouched — an unchanged arm outside the modeled branch —
   and on a compound expression in the binder slot the set constructor is itself
   only partially defined, so that sub-domain is excluded too (mapping.md §2,
   §3.3).

   The three DEFINEDNESS preconditions carry the two delegated callees' own
   domains. Both are partial. The substitution helper, handed a replacement the
   component cannot be compared against, signals an error. The set builder, handed
   a base whose elements the condition cannot be compared against, signals as
   well — and that one is reached even when both substitutions succeed, since it
   is the builder's own test of the condition against those elements. In either
   case the real operation has no result at all: it propagates the error instead
   of delivering a set. Under total semantics the contract below promises a
   result, so it may only promise one where the real operation has one; the three
   preconditions are exactly that restriction, and axiom_check.py measures both
   that they hold on the case the problem statement exhibits and that they
   genuinely exclude inputs the callees signal on (mapping.md §3.4, §3.5). -/
noncomputable section
method evalSubsFree (boundSym : Binder) (condition : Cond) (baseSet : SetObj) (old : Old) (new : New) return (out : BuiltSet)
  require CondSubDefined condition old new
  require BaseSubDefined baseSet old new
  require BuildsDefined boundSym condition baseSet old new
  require oldObj old ≠ binderObj boundSym
  ensures out = evalSubsSpec boundSym condition baseSet old new
  do
    -- impl-start
    -- Push the substitution through the condition and the base set, then rebuild
    -- the set from those components, bound by the set's own original binder.
    let newCond := substCond condition old new
    let newBase := substSet baseSet old new
    return mkSet boundSym newCond newBase
    -- impl-end
end

prove_correct evalSubsFree by
  loom_solve
  simp_all [evalSubsSpec]
