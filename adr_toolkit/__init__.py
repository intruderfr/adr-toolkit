"""adr-toolkit: zero-dependency CLI for managing Architecture Decision Records.

The package is split into focused modules:

* ``templates``  — built-in MADR and Nygard templates, configuration handling
* ``parser``     — read existing ADR files and surface metadata (number, title,
                   status, supersession links) without any external dependencies
* ``index``      — render the ``README.md`` index for an ADR directory
* ``graph``      — emit a Mermaid graph showing supersession relationships
* ``cli``        — the ``adr`` console script
"""

__version__ = "0.1.0"
__all__ = ["__version__"]
