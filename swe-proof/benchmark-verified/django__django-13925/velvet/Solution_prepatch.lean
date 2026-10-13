import Velvet.Std
-- imports-end

-- Total correctness: the modeled routine is a straight-line boolean guard that
-- always terminates, so a diverging implementation must NOT satisfy the spec.
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms and no axiomatized callees. Every input the decision reads
-- is a read-only boolean observation about the model and its environment
-- (modeled directly as a `Bool` parameter, mapping.md §2); none is an outside
-- routine whose return value the spec must contract. There is therefore no
-- `axiom` to validate against a real callee (meta.json G-AX skip).
-- axioms-end

-- pure-start
-- (No pure helpers needed — the decision is a single boolean expression.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A model self-diagnostic decides whether to emit an advisory that an
   auto-created primary key is being used while no primary-key type has been
   chosen. The advisory is appropriate ONLY for a model that genuinely lacks a
   primary key of its own: the system supplied one automatically, AND that
   automatic primary key is not merely the implicit key the model carries by
   virtue of inheriting from an ancestor model, AND no default primary-key type
   has been configured either project-wide or for the model's own application.

   Crucially, a model whose only "auto-created" primary key is the one it
   inherits from an ancestor has not failed to choose a primary-key type — the
   ancestor is the place that choice belongs, and the ancestor is diagnosed on
   its own. So when the automatic primary key is the inherited ancestor key, the
   advisory must be suppressed for this model even though its primary key is, in
   the narrow attribute sense, auto-created.

   All four observations are read-only classifications of the model and its
   settings (none is `mut`): the routine reads them and emits a single decision,
   mutating nothing (directive 5). Each is a `Bool` (mapping.md §2):
     `pkAutoCreated`            — the primary key was supplied automatically
                                   rather than declared on this model;
     `pkInheritedFromAncestor`  — that automatic primary key is the implicit key
                                   the model holds purely by inheriting from an
                                   ancestor model (not a fresh auto field);
     `defaultKeyTypeConfigured` — a project-wide default primary-key type is set;
     `appKeyTypeConfigured`     — the model's own application sets a default
                                   primary-key type.
   The advisory is emitted (`out = true`) exactly on the conjunction below. -/
method implicitPrimaryKeyAdvisory
    (pkAutoCreated : Bool) (pkInheritedFromAncestor : Bool)
    (defaultKeyTypeConfigured : Bool) (appKeyTypeConfigured : Bool)
    return (out : Bool)
  ensures out =
    (pkAutoCreated && !pkInheritedFromAncestor &&
     !defaultKeyTypeConfigured && !appKeyTypeConfigured)
  do
    -- impl-start
    -- Pre-image skeleton: the decision considered only whether the primary key
    -- was auto-supplied and whether a default primary-key type was configured;
    -- it did NOT exempt the implicit key inherited from an ancestor. This omits
    -- the `&& !pkInheritedFromAncestor` conjunct, so the advisory fires even for
    -- a model whose auto-created primary key is purely inherited. The frozen
    -- spec requires that conjunct, so prove_correct MUST fail whenever the
    -- inherited-key case would otherwise emit the advisory.
    return (pkAutoCreated &&
            !defaultKeyTypeConfigured && !appKeyTypeConfigured)
    -- impl-end

prove_correct implicitPrimaryKeyAdvisory by
  loom_solve
