# benchproofer:begin axioms
# Collapsing `.` and `..` out of a path is the standard library's job, and this task
# is not about how it does it, so the specification models it: the definition below
# stands for `posixpath.normpath` over relative paths, which is the only kind the
# implementation ever hands it. `axioms.py` is what puts the two side by side.
# benchproofer:models posixpath.normpath
def normpath(path):
    parts = []
    for segment in path.split("/"):
        if segment in ("", "."):
            continue
        if segment == ".." and parts and parts[-1] != "..":
            parts.pop()
            continue
        parts.append(segment)
    return "/".join(parts) or "."
# benchproofer:end axioms


# benchproofer:begin helpers
from hypothesis import given, strategies as st

SEGMENTS = st.sampled_from(("a", "b", "css", "app.css", "logs", ".", "..", ""))
RELATIVES = st.lists(SEGMENTS, max_size=6).map("/".join)
ROOTS = st.sampled_from(("static", "var/data"))


def resolve(root, relative):
    """Where a request for `relative` under `root` lands, per the modeled normalizer."""
    return normpath(root + "/" + relative)


def under(root, path):
    """True when `path` names `root` itself or something inside it, segment by segment."""
    base = root.split("/")
    return path.split("/")[: len(base)] == base
# benchproofer:end helpers


# benchproofer:begin impl
def impl(root, relative):
    if relative.startswith("/"):
        return None
    landing = normpath(root + "/" + relative)
    base = root.split("/")
    if landing.split("/")[: len(base)] != base:
        return None
    return landing
# benchproofer:end impl


# benchproofer:begin spec
@given(ROOTS, RELATIVES)
def property_an_accepted_path_is_normalized(root, relative):
    result = impl(root, relative)
    if result is not None:
        assert all(part not in ("", ".", "..") for part in result.split("/"))


@given(ROOTS, RELATIVES)
def property_an_accepted_path_is_under_the_root(root, relative):
    result = impl(root, relative)
    if result is not None:
        assert under(root, result)


@given(ROOTS, RELATIVES)
def property_an_accepted_path_is_where_the_request_points(root, relative):
    result = impl(root, relative)
    if result is not None:
        assert result == resolve(root, relative)


@given(ROOTS, RELATIVES)
def property_a_request_is_refused_only_when_it_escapes(root, relative):
    escapes = relative.startswith("/") or not under(root, resolve(root, relative))
    assert (impl(root, relative) is None) == escapes
# benchproofer:end spec
