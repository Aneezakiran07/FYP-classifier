# Marks the classifier folder as a Python package
# It loads the env file once when the package is first imported
# This lets the default model settings read the environment before any submodule runs
# If python dotenv is not installed the load is skipped quietly

# the classifier package
# the environment file is loaded once here so default model settings see it before any submodule loads

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
