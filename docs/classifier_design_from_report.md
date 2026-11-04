# Classifier design extracted from the FYP report (source of truth)

Extracted from Deliverable 2. Section 5.2 is the full classifier design. The other parts cover the requirements, the resolver inputs and the record format.

## From Chapter 4: requirements FR-1 to FR-3
      • FR-1. Classify a conflict region. Given a conflict region with base, ours, and theirs text, the
        classifier shall assign exactly one label from the 23-label taxonomy; when no single label is sup-
        ported, assign unknown with a reason. A region past the per-file call ceiling, or whose model call
CHAPTER 4. SOFTWARE REQUIREMENT SPECIFICATIONS                                                          25

    fails, is recorded with no label and a status of capped or llm-error.

  • FR-2. Generate a candidate resolution. For a region labeled with a logic label other than
    business-logic-conflict (and other than confluent-interference, which is recorded as unknown while
    context lines are unavailable), the resolver shall produce one candidate merged text and store it
    with a hash and a resolution strategy, or record a status of abstained (the model declined to produce
    a candidate, or the region was escalated by design), skipped, or llm-error with a reason.

  • FR-3. Escalate business-logic conflicts. For a region with conflict markers that is labeled
    business-logic-conflict, the resolver shall record the region with status abstained and reason escalate-
    by-design, mark it for human review, and shall not produce a candidate.

  • FR-4. Run sandboxed tests. Given a candidate and a rebuilt repository tree, the verifier shall run

## From Chapter 5, section 5.2: Conflict Classification (includes Table 5.1, the 23 labels)
5.2     Conflict Classification

5.2.1   Taxonomy Structure

Some conflicts are trivial: both sides made the same edit, only whitespace changed, or only comments
differ. These do not need a language model. Sending them to an LLM costs more, slows the pipeline
down, and makes it unclear whether the model or the rule resolved the conflict. The classifier therefore
processes each region in stages. Deterministic checks run first, and the model is consulted only when
the rules cannot decide. If a check cannot be verified, the region proceeds to the next stage rather than
receiving a guessed label.

The classifier assigns each region exactly one label. The taxonomy contains 23 labels, grouped into
five families. Mechanical labels describe conflicts a rule can decide from text or tokens alone, such as
identical edits on both sides, whitespace-only changes, or edits that fall in different parts of the region.
Structural labels describe shape changes that should behave the same either way, such as reformatted
punctuation, reworded comments, or renamed local identifiers. Logic labels describe behavioral dis-
agreements, such as one side adding a null check that the other side omits, or both sides writing to
the same variable in different ways. Dependency labels describe module-level changes, such as a lock-
file conflict, or an exported function whose signature changed while other files still call it using the old
shape. The final label, unknown, applies when no single label is supported by the evidence, or the region
is out of scope. The full label set is shown in Table 5.1.

Some of these labels are not new. Mechanical labels correspond to the trivial-conflict patterns that tools
such as GitWand [18] already handle. This overlap is expected, because any tool that auto-resolves
mechanical conflicts will recognize the same cases. The structural, logic, and dependency labels were
defined for this taxonomy. Four of the seven logic labels are adapted from ConflictLens [3]. The
remaining three logic labels and the dependency labels have no cited source. They were defined for this
project, and the classifier evaluation in FYP-II will test them.

5.2.2   Classification Stages

The classifier proceeds in six stages. Stage 0 determines whether the region is in scope. Binary, gener-
ated, minified, snapshot and vendored files are out of scope and receive the unknown label immediately.
A file that is none of TypeScript, a lockfile, manifest or config file, or a prose file is also marked unknown
with reason out-of-scope. Stage 1 performs identity and base-relative checks: whether one side matches
the other byte for byte, whether exactly one side changed, and whether a whole file was deleted on one
side. Stage 2 performs shape checks covering whitespace, comments, formatting, renames, import order,
CHAPTER 5. PROPOSED APPROACH AND METHODOLOGY                                                            35

                   Table 5.1: The 23 labels of the conflict taxonomy, grouped by family.

    Family            Label                              Meaning
    Mechanical        same-change                        Both sides made the identical edit.
    Mechanical        one-side-change                    Only one side changed this block.
    Mechanical        whitespace-only                    Same tokens, different spacing.
    Mechanical        reorder-only                       Same items in a different order.
    Mechanical        value-only-change                  Only an infrastructure literal differs.
    Mechanical        disjoint-edits                     Both sides changed different, non-
                                                         interacting parts.
    Structural        formatting                         Only optional punctuation or style differs.
    Structural        documentation                      Only comments or prose differ.
    Structural        import-restructure                 Same imports, arranged differently.
    Structural        rename                             Consistent identifier rename, nothing else.
    Logic             null-safety-conflict               One side guards null, the other derefer-
                                                         ences.
    Logic             type-incompatibility               Signature change breaks how the other
                                                         side uses it.
    Logic             execution-perturbation             Control-flow change skips the other side’s
                                                         code.
    Logic             overlap-contamination              Same entity modified on both sides, hybrid
                                                         state.
    Logic             assignment-override                Both assign the same target, only one can
                                                         survive.
    Logic             confluent-interference             Different variables, used together later.
    Logic             business-logic-conflict            Residual class: competing intent or mod-
                                                         ify/delete.
    Dependency        lockfile                           Conflict inside a dependency lockfile.
    Dependency        package                            Conflict inside package.json.
    Dependency        config-schema                      Conflict inside declarative config.
    Dependency        import-path                        Same binding imported from two module
                                                         paths.
    Dependency        export-shape                       Exported signature changed, other files
                                                         import it.
    Unknown           unknown                            No single label is supported by the evi-
                                                         dence, or the region is out of scope.

and reordering. Stage 3 handles boundary cases: lockfile, manifest and config conflicts, infrastructure
value changes, import-path differences, edits that do not interact, and exported symbol changes. Stage
4 handles the regions that the rules could not decide. It calls the language model, and the region then
receives a logic label, receives a structural label once a deterministic check confirms the model’s hint,
or is labeled unknown. Stages 0 to 3 handle cases that can be classified deterministically. Only regions
that reach Stage 4 require LLM-based reasoning, after which Stage 5 finalizes the result.

The deterministic stages rely on an AST difference engine. The engine compares the two sides as
syntax trees and returns one of seven results: identical, whitespace only, comments only, formatting
only, identifier rename only, content changed, or not analyzed. Each result is paired with a set of guards.
CHAPTER 5. PROPOSED APPROACH AND METHODOLOGY                                                               36

A whitespace-only result is rejected if the two sides differ in how many return, throw, break, continue or
yield keywords end a line, because a newline in that position would change behavior. A comments-only
result is rejected if a directive comment such as a TypeScript suppression or an ESLint disable differs,
because those comments affect behavior despite their appearance. A result becomes a deterministic label
only if it passes its guards. A result that fails a guard is treated as content changed and passes to the next
stage.

5.2.3    LLM Layer and Deterministic Validators

Only regions the earlier stages could not decide reach the language model, and two prompts are used.
The first prompt functions as a router. It asks the model to classify the difference as structural, semantic,
or unknown. If the answer is structural, deterministic checks attempt to confirm one of the structural
labels. If they cannot, the region is labeled unknown with reason ambiguous. The second prompt is
used when the region is semantic. It presents the model with seven logic tests in fixed order. The model
answers each test with supporting evidence. The pipeline selects the first test the model marked as met,
and a deterministic validator confirms that selection. If the validator fails, the region is labeled unknown.
The model answers the tests but never assigns a label itself. To bound cost, each file has a ceiling on the
number of model calls. A region past the ceiling is not classified. It is recorded with no label and status
capped, counted separately, and not treated as unknown. A model call that fails, or returns an invalid
answer after the allowed retries, is recorded with no label and status llm-error.

Each region produces a single record. The record stores the assigned label, the stage that made the
decision, whether the decision came from a rule or the model, and the input state of the region. It also
keeps a complete trace of the tests performed on the region. This trace shows which tests passed, failed,
or were skipped, along with the reason for each result. The resolver consumes this record in the next

## From Chapter 5, section 5.3.2: what the resolver reads from the classifier record
5.3.2   The One-Call Contract

For each region, the resolver receives four things. The first is the region itself: the base version, the
ours version, and the theirs version. The second is the label the classifier assigned, along with a short
instruction that tells the model what kind of fix it should produce. For example, a null-safety conflict
gets the instruction to add the guard on the unprotected path. A type-incompatibility conflict gets the
instruction to align the types or the callers. A confluent-interference conflict would get the instruction
to re-check the joint use site, but only if context lines are added. The reconstructed data holds only the
CHAPTER 5. PROPOSED APPROACH AND METHODOLOGY                                                             38

conflict region with no surrounding lines. Until context lines are added, a confluent-interference region
is downgraded to unknown and does not reach the resolver. The model only receives the instruction
for the assigned label, which keeps the resolution focused on the expected type of fix. The third is the
classifier’s evidence. The reason, the test that confirmed the label, the changed names and the joint
use lines are passed when the classifier record has them. The classifier does not yet emit the test, the
changed names or the joint use lines. The fourth is the file path, which gives the model enough context
to understand what kind of file it is working on. About 22 percent of the regions in the dataset have
an empty or missing base. When the base is empty, both sides are pure additions, and the resolver tells

## From Chapter 6, section 6.5: the region record and its blocks
6.5      Domain Model/Class Diagram

This project has no object-oriented class hierarchy. The design is a data pipeline, and the domain model
is expressed as the four blocks that each stage adds to the region record, rather than as classes. Every
region has exactly one record, which each component adds its own block to. Figure 6.6 gives the low-
level view of the four blocks, the fields that flow between them, and the human reviewer who reads them.
The provenance stored with each block is described below.
CHAPTER 6. HIGH-LEVEL AND LOW-LEVEL DESIGN                                                             60

 Figure 6.6: Low-level view of the region record. Four blocks share one join key, each arrow shows what
                            the next stage reads, and the reviewer only reads.

The region record is produced by the reconstruction step and holds the raw conflict data. The classifier
block adds the assigned label, the stage that decided it, and a full decision trace. A decision trace is a
record of every test the region passed through inside the classifier and what the outcome of each test
was. The resolver block holds the candidate text, its hash, the resolution strategy, and any outside-edit
requirements. An outside edit is a change the model said was needed outside the region for the candidate
to stay consistent with the rest of the codebase. The verifier block holds the outcome, the reason, the
two verdicts, and the list of affected consumers.

The human reviewer reads these blocks rather than writes to them. The classifier block shows why
a region was labeled unknown. The resolver block shows why a region was escalated or marked for
CHAPTER 6. HIGH-LEVEL AND LOW-LEVEL DESIGN                                                                61

review, which means the classifier labeled it as a business-logic conflict, or the resolver set a review flag
for assignment-override, low confidence or an outside edit. The verifier block shows why a candidate
was flagged, which means it passed tests but the dependency analysis found something that needed a
second look. The reviewer does not write any block back, and the pipeline does not read any human
decision on the next run. The human is a terminal sink, meaning the flow of data ends there for the cases
the pipeline refuses to resolve on its own.

Every block also carries provenance, which is information about where the block came from. Each
block carries the version of the component that wrote it. The classifier and resolver blocks also carry the
model name and the prompt hash. This makes any row in any file fully traceable back to the exact code
and model version that produced it.

Each block is written once per run per key. Reruns overwrite that block for that key only, so a partial
rerun does not disturb records for other regions. If the model identifier changes between runs, the new
records carry the new identifier, and the evaluation can filter by it.

## Figure 6.3 in words (the diagram could not be extracted as text)
Conflict region and base state go into the rule stages with no LLM. Stage 0 scope check leads to out-of-scope unknown. Stage 1 identity and base checks lead to same-change or one-side-change. Stage 2 shape checks lead to whitespace-only, formatting, documentation, reorder-only, import-restructure and rename, and use the AST difference engine with 7 verdicts each with guards. Stage 3 boundary checks lead to lockfile, package, config-schema, import-path, export-shape, value-only-change and disjoint-edits. A region with no label goes to the LLM stage. Stage 4 runs two prompts, a router and then 7 logic tests, and a deterministic validator checks the answer. A logic label, or a structural label after a check, goes to Stage 5. Unknown also goes to Stage 5. Rule labels and unknown skip the LLM and go straight to Stage 5. Stage 5 finalizes the output and writes the classifier record with label, stage, source, base state and trace.
