# the classifier package
# the environment file is loaded once here so default model settings see it before any submodule loads

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
