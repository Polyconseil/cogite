try:
    from importlib import metadata
except ImportError:
    # Python<3.8: use importlib-metadata package
    import importlib_metadata as metadata  # type: ignore[no-redef]

VERSION = metadata.version('cogite')
