# 4. Project migration from Hugo implementation to Python architecture

**Date**: 2026-03-16

## Status

Accepted

## Related ADRs

- Repo: [pathogens-portal](https://github.com/ScilifelabDataCentre/pathogens-portal), ADR: [0002 – Swedish Pathogens Portal 2.0 Architecture](https://github.com/ScilifelabDataCentre/pathogens-portal/blob/develop/doc/architecture/decisions/0002-pathogens-portal-2-0-architecture.md)

## Context

The original version of `swedish-pathogens-portal` was implemented using Hugo and maintained in repository [pathogens-portal](https://github.com/ScilifelabDataCentre/pathogens-portal).

The decision to move from a Hugo-based static implementation to a Python-based architecture was originally documented in [ADR-0002](https://github.com/ScilifelabDataCentre/pathogens-portal/blob/develop/doc/architecture/decisions/0002-pathogens-portal-2-0-architecture.md) in repository `pathogens-portal`.

As part of the 2.0 development effort, the Python implementation was created in a new repository (`swedish-pathogens-portal`). Because of this repository change, the original ADR is not present in this repository.

While the overall architectural direction remains consistent with the original ADR, several technical implementation details and supporting technologies were finalised during the development of the Python-based version.

## Decision

The project will continue with the Python-based architecture originally proposed in [ADR-0002](https://github.com/ScilifelabDataCentre/pathogens-portal/blob/develop/doc/architecture/decisions/0002-pathogens-portal-2-0-architecture.md) in repository `pathogens-portal`.

Repository `swedish-pathogens-portal` contains the implementation of version 2.0 and will serve as the primary location for future development and architectural decisions.

The following is the updated technology stack used in the Python implementation.

| Component    | Technology | Justification                                                                                                                                                                     |
| ------------ | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Web Framework** | Django     | Secure, robust, and feature-rich with built-in admin interface, powerful ORM, and comprehensive templating system. Well known to the team, battle-tested, and easy to maintain. |
| **Frontend Enhancement** | htmx    | Lightweight, modern approach to dynamic web interfaces. Enables AJAX, WebSocket, and real-time features without complex JavaScript frameworks. Integrates seamlessly with Django templates. |
| **Frontend Styling** | TailwindCSS  | Utility-first CSS framework enabling consistent and maintainable UI styling. |
| **UI Components** | DaisyUI |  Tailwind-based component library allowing rapid development of consistent interfaces. |
| **Database** | PostgreSQL | Reliable, performant, and supports advanced features such as full-text search and JSONB. Integrates seamlessly with Django ORM.                                            |

## Consequences

* Repository `swedish-pathogens-portal` becomes the primary location for the Python-based implementation.
* Future architecture decisions will be documented as ADRs in this repository (`swedish-pathogens-portal`).
* The original architectural decision and early project history remain documented in repository `pathogens-portal`.
* This ADR establishes traceability between the two repositories.
* The selected technology stack defines the baseline architecture for the Python-based system moving forward.
