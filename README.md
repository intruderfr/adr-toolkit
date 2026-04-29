# adr-toolkit

A zero-dependency Python CLI for managing **Architecture Decision Records (ADRs)** in a repository, with Mermaid graph generation, status tracking, and automated index files.

ADRs are short markdown documents that capture architecturally significant decisions and the context around them. `adr-toolkit` makes them easy to create, supersede, navigate, and visualise.

## Why ADRs?

Every non-trivial system accumulates decisions: which database, which queue, why we picked Kafka over SQS, why auth lives in a separate service. Without a record, that context evaporates — and six months later someone re-litigates the same debate. ADRs solve this by writing the decision down where it lives next to the code.

`adr-toolkit` is a small, fast tool that handles the bookkeeping (numbering, indexing, supersession links, graph rendering) so engineers can focus on writing the decision itself.

## Features

- `adr init` — scaffold an `docs/adr/` directory with a starter ADR and template
- `adr new "Use PostgreSQL"` — create a new ADR, auto-numbered (`0001`, `0002`, ...) using either MADR or Nygard format
- `adr list` — list every ADR with its status (Proposed / Accepted / Superseded / Deprecated)
- `adr supersede 0003 0010` — mark ADR 0003 as superseded by ADR 0010 and update both files
- `adr index` — regenerate the `README.md` index inside the ADR directory
- `adr graph` — emit a Mermaid graph showing supersession relationships
- `adr show 0007` — print a single ADR to stdout
- Two built-in templates: **MADR** (Markdown ADR, the modern standard) and **Nygard** (the original Michael Nygard format)
- Zero runtime dependencies — pure standard library Python (3.9+)

## Install

```bash
pip install -e .
```

Or install from the repo directly:

```bash
pip install git+https://github.com/intruderfr/adr-toolkit.git
```

This installs an `adr` console script.

## Quick start

```bash
# Inside your project repo
adr init
adr new "Use PostgreSQL for primary OLTP database"
adr new "Adopt event-driven architecture for billing"
adr list
adr graph > docs/adr/graph.mmd
```

By default, all commands operate on `docs/adr/`. Use `--dir <path>` to point elsewhere, or set `ADR_DIR=...` in your environment.

## Choosing a format

| Format | When to use |
|--------|-------------|
| `madr` (default) | Most modern teams. Sections for Context, Decision Drivers, Considered Options, Decision Outcome, Consequences. |
| `nygard` | Classic, terse. Sections for Status, Context, Decision, Consequences. Good when you want minimum ceremony. |

Set the format on a per-call basis:

```bash
adr new "Use Redis for session cache" --format nygard
```

Or set it as the default by adding `format: nygard` to `docs/adr/.adrconfig`.

## Example session

```
$ adr init
Initialised ADR directory at docs/adr
Created docs/adr/0001-record-architecture-decisions.md (Accepted)

$ adr new "Use PostgreSQL for primary database"
Created docs/adr/0002-use-postgresql-for-primary-database.md (Proposed)

$ adr new "Use Kafka for event bus"
Created docs/adr/0003-use-kafka-for-event-bus.md (Proposed)

$ adr supersede 0003 0004
Hold on — 0004 doesn't exist yet. Create it first with `adr new`.

$ adr new "Use NATS JetStream for event bus"
Created docs/adr/0004-use-nats-jetstream-for-event-bus.md (Proposed)

$ adr supersede 0003 0004
Marked 0003 as superseded by 0004.

$ adr list
0001  Accepted     Record architecture decisions
0002  Proposed     Use PostgreSQL for primary database
0003  Superseded   Use Kafka for event bus  (by 0004)
0004  Proposed     Use NATS JetStream for event bus

$ adr graph
graph LR
    0001["0001 Record architecture decisions"]:::accepted
    0002["0002 Use PostgreSQL for primary database"]:::proposed
    0003["0003 Use Kafka for event bus"]:::superseded
    0004["0004 Use NATS JetStream for event bus"]:::proposed
    0003 -.->|superseded by| 0004
    classDef accepted fill:#bef5cb,stroke:#1a7f37
    classDef proposed fill:#fff8c5,stroke:#9a6700
    classDef superseded fill:#ffd8b5,stroke:#9a6700,stroke-dasharray:3
    classDef deprecated fill:#ffcecb,stroke:#cf222e
```

## File layout produced

```
docs/adr/
├── README.md                                       # auto-generated index
├── template-madr.md                                # template (do not delete)
├── 0001-record-architecture-decisions.md
├── 0002-use-postgresql-for-primary-database.md
├── 0003-use-kafka-for-event-bus.md
└── 0004-use-nats-jetstream-for-event-bus.md
```

## Why zero dependencies?

ADRs are infrastructure-level tooling — the tool that manages them should never be the reason a build breaks. Pure stdlib means no version drift, no transitive CVEs, no `pip resolver` heartburn.

## Development

```bash
git clone https://github.com/intruderfr/adr-toolkit.git
cd adr-toolkit
pip install -e .
python -m unittest discover -s tests -v
```

## License

MIT — see [LICENSE](LICENSE).

## Author

Built by **Aslam Ahamed** — Head of IT @ Prestige One Developments, Dubai.
[LinkedIn](https://www.linkedin.com/in/aslam-ahamed/) · [GitHub](https://github.com/intruderfr)
