import Mathlib
-- imports-end

/-!
Producing the display markup for a reference to a related record shown on an
administrative detail page.

The reference is rendered by asking a URL-resolution step to turn a target route
name and the target record's identifier into a concrete URL:

  * the route name is assembled from the related model's grouping label and its
    model name;
  * the target record's identifier is supplied in already-encoded form;
  * crucially, the resolution is told WHICH administrative deployment is currently
    in effect, so that a non-default deployment yields URLs under its own prefix
    rather than the default one.

If the resolution step yields a URL, the result is a link-formatting step applied
to that URL and the record's display text. If the resolution step cannot produce a
URL, the result is just the record's display text.

The URL-resolution step and the link-formatting step are the SAME operations
regardless of context; here each is taken as an arbitrary function of its inputs,
so the behavior pinned below is exactly "the currently-effective deployment
identifier reaches the URL-resolution step, and its outcome is framed as a link or
falls back to plain display text."
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. Two downstream operations
-- are modeled as arbitrary function parameters:
--   * `resolveUrl : String → String → Option String → Option String` — the
--     URL-resolution step, a function of the route name, the encoded identifier,
--     and the optionally-supplied currently-effective deployment identifier;
--     `none` result models "no route could be produced".
--   * `formatLink : String → String → String` — the link-formatting step, a
--     function of a URL and the record's display text.
-- The modeled change is solely WHICH deployment identifier is handed to the
-- resolution step (the currently-effective one rather than none), so the result is
-- pinned for every possible resolver and link formatter. Hence the spec needs no
-- `opaque`/`axiom` callee contract.
-- axioms-end

-- pure-start
-- No standalone functional helper is required: the route name is a plain
-- concatenation of the grouping label and model name, and the result is the
-- link-or-fallback around the resolution step.
-- pure-end

-- post-conditions-start
/-- The display markup is fully pinned to the inputs:

  * the route name is exactly `"admin:" ++ appLabel ++ "_" ++ modelName ++
    "_change"`;
  * the resolution step is invoked with that route name, the encoded identifier,
    and the currently-effective deployment identifier (`some siteName` — NOT a
    missing identifier);
  * if it yields a URL, the result is the link-formatting step applied to that URL
    and the record's display text; otherwise the result is exactly the record's
    display text.

No output component is left free: the route name and the supplied deployment
identifier are pinned to their inputs, and each branch's result is pinned to the
corresponding step. -/
def problem_spec_getAdminUrl
    (resolveUrl : String → String → Option String → Option String)
    (formatLink : String → String → String)
    (appLabel modelName arg siteName remoteObjStr : String)
    (result : String) : Prop :=
  let urlName := "admin:" ++ appLabel ++ "_" ++ modelName ++ "_change"
  result =
    match resolveUrl urlName arg (some siteName) with
    | some url => formatLink url remoteObjStr
    | none => remoteObjStr
-- post-conditions-end

-- impl-start
def implementation_getAdminUrl
    (resolveUrl : String → String → Option String → Option String)
    (formatLink : String → String → String)
    (appLabel modelName arg siteName remoteObjStr : String) : String := Id.run do
  -- PRE-PATCH (buggy): the route name is assembled and resolved, but the
  -- resolution step is NOT told the currently-effective deployment identifier
  -- (it receives `none`), so a non-default deployment resolves under the default
  -- prefix instead of its own.
  let urlName := "admin:" ++ appLabel ++ "_" ++ modelName ++ "_change"
  match resolveUrl urlName arg none with
  | some url => return formatLink url remoteObjStr
  | none => return remoteObjStr
-- impl-end

-- proof-start
theorem correct_getAdminUrl :
    ∀ (resolveUrl : String → String → Option String → Option String)
      (formatLink : String → String → String)
      (appLabel modelName arg siteName remoteObjStr : String),
      problem_spec_getAdminUrl resolveUrl formatLink appLabel modelName arg siteName
          remoteObjStr
        (implementation_getAdminUrl resolveUrl formatLink appLabel modelName arg
          siteName remoteObjStr) := by
  intro resolveUrl formatLink appLabel modelName arg siteName remoteObjStr
  unfold problem_spec_getAdminUrl implementation_getAdminUrl
  cases resolveUrl ("admin:" ++ appLabel ++ "_" ++ modelName ++ "_change") arg (some siteName) <;> rfl
-- proof-end
