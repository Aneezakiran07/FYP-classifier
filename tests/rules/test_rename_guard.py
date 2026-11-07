# Tests for the name checks behind the rename guard in ast_gate
# is_declared_in_region must accept array destructuring, catch parameters and type aliases
# It must reject object destructuring and a bare type inside an import list
# is_named_export must find named exports and ignore default exports and plain declarations

# tests for the name checks behind the rename guard

from classifier.rules.ast_gate import is_declared_in_region, is_named_export


def test_array_destructuring_counts_as_a_declaration():
    text = "const [connected, setConnected] = useState(false);"
    assert is_declared_in_region("connected", text)
    assert is_declared_in_region("setConnected", text)


def test_object_destructuring_does_not_count():
    assert not is_declared_in_region("imageUrl", "const { imageUrl } = data;")


def test_catch_parameter_counts_as_a_declaration():
    assert is_declared_in_region("_e", "} catch (_e) {")


def test_bare_type_in_an_import_list_is_not_a_declaration():
    assert not is_declared_in_region("InvitedScore", "  type InvitedScore,")


def test_type_alias_is_a_declaration():
    assert is_declared_in_region("Score", "type Score = number;")
    assert is_declared_in_region("Box", "type Box<T> = { value: T };")


def test_named_exports_are_detected():
    assert is_named_export("isDirectory", "export function isDirectory(p: string) {")
    assert is_named_export("limit", "export const limit = 3;")
    assert is_named_export("a", "export { a, b };")


def test_default_export_is_not_a_named_export():
    assert not is_named_export("HeaderNavbar", "export default function HeaderNavbar() {")


def test_plain_declaration_is_not_a_named_export():
    assert not is_named_export("total", "const total = 1;")