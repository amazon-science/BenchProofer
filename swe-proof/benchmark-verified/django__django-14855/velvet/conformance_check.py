#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-14855 — SKIPPED.

WHY conf_skip=true:

The modeled `do` block (`getAdminUrl`) is, after the type bijection,

    match resolveAddress viewName pk (some appName) with
    | some a => Rendered.link a objLabel
    | none   => Rendered.plain objLabel

`resolveAddress` is the consumed axiom modeling the *unchanged* address
resolver `django.urls.base.reverse(..., current_app=...)` — tagged
**A-consumed** in refinement.md (§A, row A4). The impl region therefore contains
NO R/I (type-refinement or identical-concrete) input-dependent computation to
differential-test:

  * The single behaviourally-meaningful op is the A-consumed `reverse` call;
    the surrounding `match` is fixed display dispatch (the two shapes `render`
    defines — `format_html('<a href="{}">{}</a>', url, obj)` vs `str(obj)`),
    which carry no input-dependent R/I content a Python shadow could fuzz over
    the real repo type.
  * The observable the change governs — the *namespaced* URL emitted into the
    rendered admin page (`/custom-admin/...` vs `/admin/...`) — materializes only
    by serving a real admin page against a real URL configuration with two admin
    sites. That IS what the F2P test
    `test_readonly_foreignkey_links_custom_admin_site` does end-to-end; it is
    not a pure, DB-free R/I shadow this gate can fuzz over >=1e5 inputs. The
    behavioural soundness of the `reverse` contract (that `current_app` is a
    genuine determinant of the resolved URL) is already exercised by G-AX
    (axiom_check.py), over a real namespaced URL configuration.

Per SPEC_GUIDE section 3 / WORKER_PROMPT: when the impl region is all-A-tagged
(here, the single A-consumed `resolveAddress` call plus fixed display dispatch),
set meta.json conf_skip=true and ship this status=skip stub. The A leg is
covered by G-AX (axiom_check.py); spec-strength by G-VERIFY (the spec provably
forces `out = render (resolveAddress viewName pk (some appName)) objLabel`); and
discrimination by G-DIFF (the prepatch resolves within `none` — the ambient
default — and fails exactly that clause). See mapping.md section 4 and
refinement.md section C.
"""
import sys


def main():
    print("G-CONF status=skip: django__django-14855 — the modeled do-block is a "
          "single A-consumed call to resolveAddress (= the unchanged django "
          "url-resolution callee `reverse`, with the page's application context "
          "threaded in) followed by fixed display dispatch; the impl region is "
          "all-A-tagged with no input-dependent R/I shadow to differential-test. "
          "conf_skip=true. Soundness covered by G-AX + G-VERIFY + G-DIFF.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
