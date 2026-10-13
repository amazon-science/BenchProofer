# Requirements: Engine.render_to_string() must honor the engine's autoescape setting

## Introduction

The Django template `Engine` (`django/template/engine.py`) accepts an
`autoescape` configuration flag in its constructor (default `True`). This flag
is meant to control whether interpolated template values are HTML-escaped when
that engine renders output.

`Engine.render_to_string(template_name, context=None)` loads the named template
(or the first loadable template from a list) and renders it. When the caller
supplies plain context data (a mapping or `None`) rather than a ready-made
rendering `Context`, `render_to_string` builds a fresh `Context` for that data
before rendering. The problem: this freshly-built `Context` is created without
passing the engine's configured `autoescape` attribute, so it falls back to the
`Context` default of `autoescape=True`. Consequently an engine constructed with
`autoescape=False` was ignored on this code path — plain-data renders were
always autoescaped, contradicting the engine's own configuration.

The goal is to make `Engine.render_to_string` propagate the engine's
`autoescape` setting into the `Context` it builds for plain data, while leaving
untouched the existing behavior when the caller already supplies a `Context`.
Downstream, the per-value escaping decision is made by
`render_value_in_context` (`django/template/base.py`), which escapes an
interpolated value when the active context's `autoescape` is true and emits it
as a plain string otherwise; literal template text is unaffected either way.

## Requirement 1: Propagate the engine's autoescape setting to plain-data renders

**User story:** As a developer who configures a template `Engine` with
`autoescape=False`, I want `render_to_string` to honor that setting when I pass
plain context data, so that interpolated values are emitted without HTML
escaping as I configured.

**Acceptance criteria**

1. WHEN `Engine.render_to_string` is called on an engine whose `autoescape`
   attribute is `False` and the caller supplies plain context data (a mapping
   or `None`, i.e. not a `Context` instance), THEN `render_to_string` SHALL
   render the template with autoescaping disabled, so that an interpolated
   value containing HTML-significant characters (such as `<`, `>`, `&`, `"`,
   `'`) appears in the output exactly as given, without being converted to HTML
   entities.
2. WHEN `Engine.render_to_string` is called on an engine whose `autoescape`
   attribute is `True` and the caller supplies plain context data, THEN
   `render_to_string` SHALL render the template with autoescaping enabled, so
   that an interpolated value containing HTML-significant characters is
   HTML-escaped in the output.
3. The system SHALL, when building a rendering context for plain context data
   inside `render_to_string`, use the engine's configured `autoescape` value as
   that context's autoescape setting rather than the context default.
4. WHEN plain context data is rendered, THEN `render_to_string` SHALL leave all
   literal (non-interpolated) template text unchanged in the output regardless
   of the autoescape setting, so that only interpolated values are affected by
   escaping.

## Requirement 2: Preserve rendering behavior when a Context is supplied

**User story:** As a developer who passes an already-constructed `Context` to
`render_to_string`, I want that context used as-is, so that its own autoescape
setting continues to govern rendering and existing behavior is not changed.

**Acceptance criteria**

1. IF the object passed as `context` to `Engine.render_to_string` is already a
   `Context` instance, THEN `render_to_string` SHALL render using that supplied
   context directly and SHALL NOT rewrap it or override its autoescape setting.
2. WHEN a ready-made `Context` is supplied, THEN the escaping of interpolated
   values SHALL be governed by that supplied context's own autoescape setting,
   independent of the engine's `autoescape` attribute.
3. The system SHALL keep the default `render_to_string` behavior for an engine
   with the default `autoescape=True` and plain context data: interpolated
   values are HTML-escaped and literal text is emitted unchanged.

## Requirement 3: Preserve unrelated Engine behavior

**User story:** As a maintainer, I want template selection, loader
configuration, and default-engine lookup to remain unchanged, so that adding the
autoescape propagation does not regress other `Engine` functionality.

**Acceptance criteria**

1. WHEN `render_to_string` receives a list or tuple of template names, THEN it
   SHALL render the first template that can be loaded, preserving the existing
   selection order and template-not-found behavior.
2. The system SHALL preserve the existing template loader configuration and
   resolution behavior, including loader ordering and cached-loader precedence,
   so that the template resolved for a given name is unchanged.
3. The system SHALL preserve template origin information for loaded templates.
4. The system SHALL preserve `Engine.get_default()` behavior, returning the
   first configured Django templates engine when exactly one or several are
   configured, and raising the configured error when none are configured.
