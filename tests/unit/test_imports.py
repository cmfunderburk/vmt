def test_import_frameworks():
    import importlib

    for mod in ["PyQt6", "pygame", "numpy"]:
        importlib.import_module(mod)


def test_package_version():
    from econsim import __version__

    assert isinstance(__version__, str)
    assert __version__
