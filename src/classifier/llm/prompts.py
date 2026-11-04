import os

# Examples live in a json file so they can be swapped without editing the prompts
FEW_SHOT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "few_shot.json")
MAX_EXAMPLE_CHARS = 500

# The seven logic subtypes from the frozen taxonomy. These are the only
# labels the LLM is allowed to emit for semantic conflicts, plus "unknown"
# via prompt A. All other labels (mechanical/*, structural/*, dependency/*)
# are decided by the rule layer before the model is ever called.
SUBTYPES = (
    "logic/null-safety-conflict",
    "logic/type-incompatibility",
    "logic/execution-perturbation",
    "logic/overlap-contamination",
    "logic/assignment-override",
    "logic/confluent-interference",
    "logic/business-logic-conflict",
)

# Labels whose resolution is safe by construction, meaning the merged code
# behaves the same as at least one side. Used by the prompt builder to
# route few shot examples into prompt A as the "structural" kind.
STRUCTURAL_LABELS = (
    "mechanical/same-change",
    "mechanical/one-side-change",
    "mechanical/whitespace-only",
    "mechanical/reorder-only",
    "mechanical/value-only-change",
    "mechanical/disjoint-edits",
    "structural/formatting",
    "structural/documentation",
    "structural/import-restructure",
    "structural/rename",
)

PROMPT_A = """You judge ONE merge conflict region. Answer with JSON only, no prose.
The AST evidence comes from a parser, trust it over your own reading.
Pick the kind:
- structural: same behavior, only the shape differs (formatting, comments, imports, a consistent rename, reordering of members inside an object, interface or class)
- semantic: the sides behave or type-check differently (conditions, values, arguments, calls, added or removed statements, reordered statements or arguments, and any change to a declared type such as an annotation, a union member or an interface member, even though types are erased at runtime)
- unknown: the evidence is not enough to tell
Two sides editing the same lines is never a reason.
Reply exactly: {"kind": "structural|semantic|unknown", "reason": "one short sentence"}
<<EXAMPLES>>"""


PROMPT_B = (
    # the first section states the input limits the taxonomy requires us to disclose
    """You name the subtype of ONE semantic merge conflict. Answer with JSON only, no prose.
You see only the two sides, the file path and parser evidence. You do not see the original version, so you cannot know which side introduced each change. Judge from the difference between the sides alone.

Run tests 1 to 7 in order. The first test whose whole condition is met decides the answer. Do not skip ahead because a later subtype sounds more natural.

Terms. A target is one named thing that holds a value or a shape: a variable, a property, a key, a JSX attribute, a default parameter, or the declared type of any of these. A member is one distinct property, key, attribute or field of an entity. Tokens inside one string value, such as the words of a className, are not separate members.

"""
    # tests one to three follow the taxonomy order so assignment override cannot pre-empt them
    """1. logic/null-safety-conflict
   - one side adds, removes or guards a null marker (?., ??, a null check, | null, | undefined, or an optional ?) on a name, and the other side's changed code uses that name with no null handling, or
   - the only difference in a signature or declared type is nullability.
   Adding or removing any other union member is not a nullability change.
2. logic/type-incompatibility
   Requires all three: one side changes a function or type signature beyond nullability; the other side's changed code uses that symbol in a way that depends on the old shape; no importer in another file is known (assume none, no dependency graph is available).
   A changed type annotation alone is not a type break. If the other side does not use the symbol, or both sides only change the same annotation, this test fails.
3. logic/execution-perturbation
   One side adds or changes a return, throw, break, continue or branch condition, and the other side's changed statements sit on the path it affects, so they sometimes never run. If the other side dereferences a value on a path the new guard does not cover, that is test 1 instead.
"""
    # test four holds the second clause of the competing member rule so it outranks test five
    """4. logic/overlap-contamination
   Both sides change the same entity (an object, class, interface, component or record) and one of these holds:
   - they change different members or operations of it, linked so the merged state is a hybrid neither side intended
   - they compete over one member and the sides also differ in at least one other member of that entity
   - one side renames a symbol and the other side makes a non-rename edit that still uses the old name
"""
    # test five names declared types and unions as targets because that is where the observed failures sat
    """5. logic/assignment-override
   Both sides give the same single target different values or shapes, and the sides differ in nothing else. The changed part is an assignment, a declaration, a property, a default, or a declared type including a union. Use it even when the value is a business rule, such as two different discount constants. If each side adds a different member to the same union, both are competing over that one declared type.
"""
    # test six cannot be confirmed without context so the prompt forbids guessing a joint use
    """6. logic/confluent-interference
   Each side changes a different entity, and a line that reads both entities together is visible in the text you were given. Do not assume such a line exists.
7. logic/business-logic-conflict
   The residual class, only after tests 1 to 6 fail. It includes a differing literal that sits directly in a condition, a return value or a call argument, different multi-statement or branching logic, and one side removing code the other side modified.
   A change confined to one target is never this class. Test 5 covers it.

"""
    # null and other are kept because classify.py maps them but their meaning is now narrow
    """Answer null only if the text is too incomplete to judge. Answer other only if the sides differ in layout, comments, naming or import arrangement and not in behavior.
Quote the differing tokens as evidence. Use low confidence when unsure.
Reply exactly: {"subtype": "...", "confidence": "high|medium|low", "evidence": "quoted tokens"}
<<EXAMPLES>>"""
)