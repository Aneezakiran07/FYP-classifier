# Package entry for the llm side of the classifier, used only at Stage 4
# It re exports route and run_logic_tests from classify_llm so pipeline.py can import them directly
# route asks the router prompt whether a region is structural, semantic or unknown
# run_logic_tests asks the seven logic tests prompt and returns one answer per test

# llm side of the classifier for stage 4
# owned by Aneeza
# this package must never import the rules package

from classifier.llm.classify_llm import route, run_logic_tests
