# Package marker for the rules side of the classifier, which covers Stages 0 to 3
# It holds no code of its own and only makes the rules folder importable
# The real work lives in ast_diff, ast_gate, validators and the patterns subpackage
# Rules never call a model, so everything under this folder is deterministic

# rules side of the classifier for stages 0 to 3
# owned by Fatima
# this package must never import the llm package
