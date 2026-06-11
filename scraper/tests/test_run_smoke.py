import importlib


def test_run_module_exposes_main():
    mod = importlib.import_module("run")
    assert hasattr(mod, "main")
