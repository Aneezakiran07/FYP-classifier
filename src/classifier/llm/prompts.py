import os

# Examples live in a json file so they can be swapped without editing the prompts
FEW_SHOT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "few_shot.json")
MAX_EXAMPLE_CHARS = 500

# Bump a version whenever the text of that prompt changes
ROUTER_PROMPT_VERSION = "router-v1"
LOGIC_PROMPT_VERSION = "logic-v1"

# The seven logic tests in the fixed order of Table 5.1
# A test carries the name of the label it supports, and the pipeline picks the label
LOGIC_TESTS = (
    "null-safety-conflict",
    "type-incompatibility",
    "execution-perturbation",
    "overlap-contamination",
    "assignment-override",
    "confluent-interference",
    "business-logic-conflict",
)

# Labels shown to the router as the structural kind in few shot examples
STRUCTURAL_LABELS = (
    "same-change",
    "one-side-change",
    "whitespace-only",
    "reorder-only",
    "value-only-change",
    "disjoint-edits",
    "formatting",
    "documentation",
    "import-restructure",
    "rename",
)

PROMPT_A = """You judge ONE merge conflict region. Answer with JSON only, no prose.
You see the file path, the base version when it exists, both sides and parser evidence. The message says whether the base is present, empty or unavailable.
The AST evidence comes from a parser, trust it over your own reading.
Pick the kind:
- structural: same behavior, only the shape differs (formatting, comments, imports, a consistent rename, reordering of members inside an object, interface or class)
- semantic: the sides behave or type-check differently (conditions, values, arguments, calls, added or removed statements, reordered statements or arguments, and any change to a declared type such as an annotation, a union member or an interface member, even though types are erased at runtime)
- unknown: the evidence is not enough to tell
Two sides editing the same lines is never a reason.
Reply exactly: {"kind": "structural|semantic|unknown", "reason": "one short sentence"}
<<EXAMPLES>>"""


PROMPT_B = (
    # the model answers each test and never picks a winner or names a label
    """You answer seven logic tests about ONE semantic merge conflict. Answer with JSON only, no prose.
Answer every test on its own, in the order given, even after one is met. Do not pick a winner and do not name a final answer.
You see the file path, the base version when it exists, both sides and parser evidence. The message says whether the base is present, empty or unavailable. When it is present, use it to see which side changed what. When it is not, judge from the difference between the sides and do not guess the direction of change.

Terms. A target is one named thing that holds a value or a shape: a variable, a property, a key, a JSX attribute, a default parameter, or the declared type of any of these. A member is one distinct property, key, attribute or field of an entity. Tokens inside one string value, such as the words of a className, are not separate members.

"""
    # tests one to three come first so assignment override cannot pre-empt them
    """1. null-safety-conflict
   - one side adds, removes or guards a null marker (?., ??, a null check, | null, | undefined, or an optional ?) on a name, and the other side's changed code uses that name with no null handling, or
   - the only difference in a signature or declared type is nullability.
   Adding or removing any other union member is not a nullability change.
2. type-incompatibility
   Requires all three: one side changes a function or type signature beyond nullability; the other side's changed code uses that symbol in a way that depends on the old shape; no importer in another file is known (assume none, no dependency graph is available).
   A changed type annotation alone is not a type break. If the other side does not use the symbol, or both sides only change the same annotation, this test is not met.
3. execution-perturbation
   One side adds or changes a return, throw, break, continue or branch condition, and the other side's changed statements sit on the path it affects, so they sometimes never run. If the other side dereferences a value on a path the new guard does not cover, test 1 covers it and this test is not met.
"""
    # test four holds the second clause of the competing member rule so it outranks test five
    """4. overlap-contamination
   Both sides change the same entity (an object, class, interface, component or record) and one of these holds:
   - they change different members or operations of it, linked so the merged state is a hybrid neither side intended
   - they compete over one member and the sides also differ in at least one other member of that entity
   - one side renames a symbol and the other side makes a non-rename edit that still uses the old name
"""
    # test five names declared types and unions as targets because that is where the observed failures sat
    """5. assignment-override
   Both sides give the same single target different values or shapes, and the sides differ in nothing else. The changed part is an assignment, a declaration, a property, a default, or a declared type including a union. It is met even when the value is a business rule, such as two different discount constants. If each side adds a different member to the same union, both are competing over that one declared type.
"""
    # test six cannot be confirmed without context so the prompt forbids guessing a joint use
    """6. confluent-interference
   Each side changes a different entity, and a line that reads both entities together is visible in the text you were given. Do not assume such a line exists.
7. business-logic-conflict
   The residual test, met only when tests 1 to 6 are all not met. It includes a differing literal that sits directly in a condition, a return value or a call argument, different multi-statement or branching logic, and one side removing code the other side modified.
   A change confined to one target is never met here. Test 5 covers it.

"""
    # every test needs evidence so the validator and the trace have something to read
    """Evidence is required on every test. For a met test, quote the exact tokens from the text that satisfy it. For a test that is not met, say in under 15 words which part of the condition fails. If the text is too incomplete to judge a test, mark it not met and say so.
Reply exactly, with all seven tests in this order:
{"tests": [{"test_id": "null-safety-conflict", "met": false, "evidence": "..."}, {"test_id": "type-incompatibility", "met": false, "evidence": "..."}, {"test_id": "execution-perturbation", "met": false, "evidence": "..."}, {"test_id": "overlap-contamination", "met": false, "evidence": "..."}, {"test_id": "assignment-override", "met": false, "evidence": "..."}, {"test_id": "confluent-interference", "met": false, "evidence": "..."}, {"test_id": "business-logic-conflict", "met": false, "evidence": "..."}]}
Set met to true on every test whose whole condition holds.
<<EXAMPLES>>"""
)
