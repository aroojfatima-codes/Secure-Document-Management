__all__ = ["App"]


def __getattr__(name: str):
    if name == "App":
        from gui.app import App
        return App
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
