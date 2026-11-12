# Tests for the validators using small made up regions
# They check quoted evidence must appear in the region, layout is ignored, base text and AST change names count and invented quotes fail
# They check that each logic test check passes and fails on the right regions, including JSX children, return types and nested backticks
# They check that confluent interference and unknown test ids always fail and that a structural hint is never confirmed yet

# tests for the validators with small made up regions

from types import SimpleNamespace

import pytest

from classifier.rules.validators import (
    check_assignment_override,
    check_overlap_contamination,
    confirm_structural,
    evidence_is_real,
    validate_logic_test,
)


def make_region(ours="", theirs="", base=""):
    return SimpleNamespace(file_path="src/a.ts", ours_text=ours, theirs_text=theirs, base_text=base)


def make_tsx_region(ours="", theirs="", base=""):
    return SimpleNamespace(file_path="src/a.tsx", ours_text=ours, theirs_text=theirs, base_text=base)


def test_quote_found_in_ours_is_real():
    region = make_region(ours="const a = 1;")
    assert evidence_is_real(region, "OURS: `const a = 1;`")


def test_layout_difference_does_not_matter():
    region = make_region(ours="foo(a,\n  b)")
    assert evidence_is_real(region, "`foo(a, b)`")


def test_quote_found_only_in_base_is_real():
    region = make_region(base="import X from 'x';")
    assert evidence_is_real(region, "BASE: `import X from 'x';`")


def test_ast_change_name_is_accepted():
    assert evidence_is_real(make_region(ours="a"), "AST: `code_removed`")


def test_invented_quote_fails():
    assert not evidence_is_real(make_region(ours="const a = 1;"), "`const b = 2;`")


def test_evidence_with_no_quote_fails():
    assert not evidence_is_real(make_region(ours="const a = 1;"), "nothing changed")


def test_every_piece_must_match():
    region = make_region(ours="const a = 1;")
    assert not evidence_is_real(region, "`const a = 1;` and `invented line`")


def test_double_quotes_are_used_when_there_are_no_backticks():
    assert evidence_is_real(make_region(ours="const a = 1;"), 'OURS: "const a = 1;"')


def test_business_logic_passes_when_sides_differ():
    region = make_region(ours="a = 1", theirs="a = 2")
    assert validate_logic_test(region, "business-logic-conflict", "OURS: `a = 1`")


def test_business_logic_fails_when_sides_differ_only_in_spacing():
    region = make_region(ours="a = 1", theirs="a=1")
    assert not validate_logic_test(region, "business-logic-conflict", "`a = 1`")


def test_unknown_test_id_fails():
    region = make_region(ours="a = 1", theirs="a = 2")
    assert not validate_logic_test(region, "not-a-test", "`a = 1`")


def test_confluent_interference_always_fails():
    region = make_region(ours="a = 1", theirs="a = 2")
    assert not validate_logic_test(region, "confluent-interference", "`a = 1`")


def test_null_safety_passes_when_one_side_adds_a_guard():
    region = make_region(ours="const v = user.name;", theirs="const v = user?.name;")
    assert validate_logic_test(region, "null-safety-conflict", "THEIRS: `user?.name`")


def test_null_safety_fails_with_no_null_marker_difference():
    region = make_region(ours="x = 1;", theirs="y = 2;")
    assert not validate_logic_test(region, "null-safety-conflict", "`x = 1;`")


def test_execution_perturbation_passes_when_a_branch_is_added():
    region = make_region(ours="doIt();", theirs="if (ok) { doIt(); }")
    assert validate_logic_test(region, "execution-perturbation", "THEIRS: `if (ok)`")


def test_execution_perturbation_fails_with_same_control_flow():
    region = make_region(ours="a = 1;", theirs="a = 2;")
    assert not validate_logic_test(region, "execution-perturbation", "`a = 1;`")


def test_execution_perturbation_passes_when_a_condition_changes_with_the_same_counts():
    region = make_region(ours="if (a) { return 1; }", theirs="if (b) { return 1; }")
    assert validate_logic_test(region, "execution-perturbation", "`if (a)`")


def test_execution_perturbation_ignores_a_comment_change():
    region = make_region(ours="return 1; // old", theirs="return 1; // new")
    assert not validate_logic_test(region, "execution-perturbation", "`return 1;`")


def test_type_incompatibility_passes_when_a_signature_changes():
    region = make_region(ours="function f(a: string) {", theirs="function f(a: number) {")
    assert validate_logic_test(region, "type-incompatibility", "`function f(a: number) {`")


def test_type_alias_line_counts_as_a_signature():
    region = make_region(ours="type Box = { a: string };", theirs="type Box = { a: number };")
    assert validate_logic_test(region, "type-incompatibility", "`type Box = { a: number };`")


def test_type_incompatibility_fails_when_no_signature_line_changes():
    region = make_region(ours="const a = 1;", theirs="const a = 2;")
    assert not validate_logic_test(region, "type-incompatibility", "`const a = 1;`")


def test_overlap_passes_when_both_sides_change_the_same_name():
    region = make_region(
        ours="const config = { a: 1 };", theirs="const config = { b: 2 };", base="const config = {};"
    )
    assert check_overlap_contamination(region)


def test_overlap_fails_when_changed_lines_share_no_name():
    region = make_region(ours="const alpha = 1;", theirs="const beta = 2;")
    assert not check_overlap_contamination(region)


def test_assignment_override_passes_when_one_target_gets_two_values():
    region = make_region(ours='className="a"', theirs='className="b"')
    assert check_assignment_override(region)


def test_assignment_override_passes_when_a_list_differs_after_the_first_item():
    region = make_region(ours='ignores: ["a", "b", "c"]', theirs='ignores: ["a", "c"]')
    assert check_assignment_override(region)


def test_assignment_override_fails_when_values_match():
    region = make_region(ours='className="a"', theirs='className="a"')
    assert not check_assignment_override(region)


def test_assignment_override_fails_when_targets_differ():
    region = make_region(ours="a = 1", theirs="b = 1")
    assert not check_assignment_override(region)


def test_structural_hint_is_never_confirmed_yet():
    assert confirm_structural(make_region("a", "b"), "whitespace_only") is None

def test_assignment_override_passes_when_a_jsx_child_gets_two_expressions():
    # Dev region 23, the same text slot holds currentYear on one side and a new date call on the other
    region = make_tsx_region(
        ours="          © {currentYear} Sentiment Hound. All rights reserved.",
        theirs="          © {new Date().getFullYear()} Sentiment Hound. All rights reserved.",
        base="          © 2020 mantine.dev. All rights reserved.",
    )
    assert check_assignment_override(region)


def test_assignment_override_fails_when_the_text_around_a_jsx_child_differs():
    # Different surrounding text means the two expressions are not in the same slot
    region = make_tsx_region(ours="<p>Hello {name}</p>", theirs="<p>Goodbye {user.name}</p>")
    assert not check_assignment_override(region)


def test_assignment_override_fails_when_a_jsx_child_is_the_same():
    region = make_tsx_region(ours="<p>Hello {name}</p>", theirs="<p>Hello {name}</p>")
    assert not check_assignment_override(region)


def test_assignment_override_passes_when_a_return_type_annotation_differs():
    # Dev region 25, the same method gets two different return type annotations
    region = make_region(
        ours="  private calculateNetworkMetrics(issues: PerformanceIssue[]): { requestCount: number; bundleImpact: number; cacheability: number } {",
        theirs="  private calculateNetworkMetrics(issues: PerformanceIssue[]): { requestCount: number; bundleSize: number; latencyRisk: number } {",
        base="  private calculateNetworkMetrics(issues: PerformanceIssue[]): any {",
    )
    assert check_assignment_override(region)


def test_assignment_override_passes_when_an_arrow_function_return_type_differs():
    region = make_region(ours="const load = async (): Promise<User> => {",
                         theirs="const load = async (): Promise<Account> => {")
    assert check_assignment_override(region)


def test_assignment_override_fails_when_return_types_belong_to_different_functions():
    # The parameters have different names so only the return type check is tested here
    region = make_region(ours="function load(a: string): User {", theirs="function save(b: string): Account {")
    assert not check_assignment_override(region)


def test_assignment_override_fails_when_a_return_type_is_the_same():
    region = make_region(ours="function load(): User {", theirs="function load():  User {")
    assert not check_assignment_override(region)


def test_a_quote_holding_a_template_string_is_read_whole():
    # Dev region 12, backticks inside the quoted code must not end the quote early
    region = make_region(
        ours="if (isBrotli) {\n  uploadPathUnix = `${filePathUnix}.br`\n}",
        theirs="const filePathWithExtension = compressed ? `${filePathUnixSafe}.br` : filePathUnixSafe",
    )
    evidence = ("ours sets `uploadPathUnix = `${filePathUnix}.br`` inside `if (isBrotli) {`, "
                "theirs uses `compressed ? `${filePathUnixSafe}.br` : filePathUnixSafe`")
    assert evidence_is_real(region, evidence)


def test_an_invented_quote_still_fails_next_to_a_template_string():
    region = make_region(ours="uploadPathUnix = `${filePathUnix}.br`")
    assert not evidence_is_real(region, "ours sets `uploadPathUnix = `${filePathUnix}.br`` and `invented line`")


def test_prose_between_two_quotes_is_never_read_as_a_quote():
    # Two plain quotes with a word between them that is not in the region
    region = make_region(ours="const a = 1;", theirs="const a = 2;")
    assert evidence_is_real(region, "ours `const a = 1;` against theirs `const a = 2;`")


@pytest.mark.parametrize("ours, theirs", [
    ("if (a) { foo() }", "if (a) { bar() }"),
    ("class A { run() { go() } }", "class A { run() { stop() } }"),
    ("items.map(x => { run(x) })", "items.map(x => { stop(x) })"),
    ("else { a() }", "else { b() }"),
])
def test_a_code_block_is_not_a_jsx_child(ours, theirs):
    # A brace after a condition, an arrow or a keyword opens code, not a JSX child
    assert not check_assignment_override(make_tsx_region(ours=ours, theirs=theirs))


def test_a_jsx_child_counts_only_in_a_jsx_file():
    region = make_region(ours="<p>Hello {name}</p>", theirs="<p>Hello {user.name}</p>")
    assert not check_assignment_override(region)


def test_a_line_that_is_only_a_brace_is_not_a_jsx_slot():
    # Two lines that are only a brace expression hold no shared text, so they are not one target
    region = make_tsx_region(ours="      {isOpen && <Modal />}", theirs="      {user.name}")
    assert not check_assignment_override(region)


def test_a_template_substitution_on_its_own_line_is_not_a_jsx_child():
    # A dollar brace inside a multi line template string is a substitution, not a JSX child
    ours = "  const cls = `\n    ${borderClass}\n    p-2\n  `;"
    theirs = "  const cls = `\n    ${squareColor}\n    p-2\n  `;"
    assert not check_assignment_override(make_tsx_region(ours=ours, theirs=theirs))


def test_a_brace_inside_a_multi_line_template_string_is_not_a_jsx_child():
    # Markup text inside a template string is part of the string, not a JSX child, even without a dollar sign
    ours = "  const html = `\n    <p>{name}</p>\n  `;"
    theirs = "  const html = `\n    <p>{title}</p>\n  `;"
    assert not check_assignment_override(make_tsx_region(ours=ours, theirs=theirs))


def test_a_jsx_child_inside_a_tag_still_counts():
    # A brace between tags still has shared text around it, so it stays one target
    region = make_tsx_region(ours="      <span>{count}</span>", theirs="      <span>{total}</span>")
    assert check_assignment_override(region)


def test_an_ellipsis_at_the_end_of_a_quote_is_a_gap():
    # The model shortens a long line with three dots, the part before them must still be real
    region = make_region(ours="return res.status(200).json({ ok: true });")
    assert evidence_is_real(region, "OURS: `return res.status(200)...`")


def test_an_ellipsis_inside_a_quote_needs_every_part_in_order_on_one_side():
    region = make_region(ours="{sent ? (<Thanks />) : (<Form onSubmit={send} />)}")
    assert evidence_is_real(region, "`sent ? (...) : (...)`")


def test_parts_around_an_ellipsis_in_the_wrong_order_fail():
    region = make_region(ours="first(); second();")
    assert not evidence_is_real(region, "`second()...first()`")


def test_parts_around_an_ellipsis_split_across_the_two_sides_fail():
    # Every part must come from the same side, or two unrelated pieces could be glued together
    region = make_region(ours="alpha();", theirs="omega();")
    assert not evidence_is_real(region, "`alpha()...omega()`")


def test_an_invented_part_next_to_an_ellipsis_fails():
    region = make_region(ours="return res.status(200).json(data);")
    assert not evidence_is_real(region, "`return res.status(500)...`")


def test_an_ellipsis_with_only_tiny_parts_proves_nothing():
    region = make_region(ours="f(a) + g(b)")
    assert not evidence_is_real(region, "`(...)`")


def test_single_quotes_are_read_when_there_are_no_backticks_or_double_quotes():
    region = make_region(ours="const limit = 10;")
    assert evidence_is_real(region, "OURS sets 'const limit = 10'")


def test_curly_quotes_are_read_when_there_are_no_other_quotes():
    region = make_region(ours="const limit = 10;")
    assert evidence_is_real(region, "OURS sets “const limit = 10”")


def test_an_invented_single_quote_still_fails():
    region = make_region(ours="const limit = 10;")
    assert not evidence_is_real(region, "OURS sets 'const limit = 99'")


def test_single_quotes_are_ignored_when_double_quotes_are_present():
    # Double quotes keep priority, so a short real single quote cannot rescue an invented double quote
    region = make_region(ours="const limit = 10;")
    assert not evidence_is_real(region, "\"invented text\" and 'const limit = 10'")


def test_a_quote_with_spread_syntax_is_still_real():
    # Three dots in real spread syntax read as a gap, and the parts around them are still real and in order
    region = make_region(ours="const merged = { ...defaults, ...options };")
    assert evidence_is_real(region, "`{ ...defaults, ...options }`")


def test_a_lone_jsx_child_under_the_same_opening_line_is_one_target():
    # A child on its own line inside the same tag is one slot with two expressions
    ours = '        <p className="subtitle">\n          {t("database.subtitle")}\n        </p>'
    theirs = '        <p className="subtitle">\n          {t("database.headerSubtitle")}\n        </p>'
    assert check_assignment_override(make_tsx_region(ours=ours, theirs=theirs))


def test_a_lone_jsx_child_under_different_opening_lines_is_not_one_target():
    ours = "        <header>\n          {isOpen && <Modal />}\n        </header>"
    theirs = "        <footer>\n          {user.name}\n        </footer>"
    assert not check_assignment_override(make_tsx_region(ours=ours, theirs=theirs))


def test_a_one_line_jsx_child_whose_base_is_a_lone_child_is_one_target():
    # The base held a lone child in the same place, so both sides changed the same child
    region = make_tsx_region(
        ours="        {children || <div>Nenhum conteudo disponivel</div>}",
        theirs="        {child}",
        base="        {children}",
    )
    assert check_assignment_override(region)


def test_a_one_line_jsx_child_with_an_empty_base_is_not_one_target():
    # Both sides only added a line, so nothing shows the two children sit in the same place
    region = make_tsx_region(ours="      {isOpen && <Modal />}", theirs="      {user.name}", base="")
    assert not check_assignment_override(region)


def test_a_one_line_jsx_child_over_real_base_text_is_one_target():
    # Both sides replaced the same base text with a translation call, with different keys
    region = make_tsx_region(
        ours="              {t('database.subtitle')}",
        theirs="              {t('database.headerSubtitle')}",
        base="              Jelajahi koleksi lengkap brand, parfum, dan perfumer Indonesia\n              dengan informasi detail dan ulasan dari komunitas",
    )
    assert check_assignment_override(region)


def test_two_lone_jsx_children_inside_longer_sides_need_the_same_line_above():
    # Aneeza's case inside a longer region, the lone lines sit under different lines so they are not one target
    ours = "      <Header />\n      {isOpen && <Modal />}"
    theirs = "      <Footer />\n      {user.name}"
    assert not check_assignment_override(make_tsx_region(ours=ours, theirs=theirs, base="      <Header />"))
