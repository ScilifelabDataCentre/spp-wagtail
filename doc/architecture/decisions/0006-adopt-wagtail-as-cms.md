# 6. Adopt Wagtail as Content Management System

**Date**: 2026-03-18

## Status

Accepted

## Related ADRs

- [0002 – Project migration from Hugo implementation to Python architecture](0002-project-migration-from-hugo-to-python.md)

## Context

As the Swedish Pathogens Portal transitioned from a static Hugo site to a Python/Django architecture (ADR-0002), we rebuilt the whole portal from scratch during a first phase aiming at releasing an MVP.
However, because content and code follow different release cycles, the need to decouple the page content from the codebase quickly became apparent.
The portal team requires a system that supports their need for a structured content management workflow:

- **Content review prior to publication:** editorial approval before changes go live
- **Version history:** the ability to audit and revert content changes
- **Content openness:** making portal content as open, transparent and reusable as possible
- **Visualisation preview:** the ability to preview pages before they are published

Two candidate approaches were evaluated:

1. **Wagtail:** a Django-native CMS that runs as an integrated part of the web application
2. **GitHub-based workflow:** managing content as markdown files in a Git repository, with GitHub Actions to drive publication

### Wagtail

Wagtail is a CMS built on top of Django. It provides an editorial interface, a page revision system, a media library, and draft/preview functionality out of the box. Because it is Django-native, it does not introduce a separate runtime service.

**Advantages:**
- Native editorial workflow: content can be drafted, submitted for review, and approved before publication
- Built-in revision history per page, allowing auditing and rollback of content changes
- Centralised media library: images and documents are uploaded once and reused across the site, avoiding duplication
- Page preview: editors can preview unpublished drafts in context, including pages with embedded visualisations
- Django alignment: officially supported CMS built on Django, integrates with the existing ORM, templating system, and deployment pipeline without additional external services

**Disadvantages:**
- Content is stored in the database and is not publicly open by default
- The team has no prior experience with Wagtail, introducing a learning curve

### GitHub-based workflow

Content would be authored and reviewed via pull requests in a GitHub repository, with automation publishing content to the portal on merge.

**Advantages:**
- Content is open by default and familiar to scientific communities and developers
- GitHub's pull request model provides a well-understood review mechanism

**Disadvantages:**
- No visualisation preview: contributors cannot see how content will render on the site before it is published
- Images must be stored and managed in the repository, resulting in duplication whenever the same image is used in multiple parts of the site
- The integration layer between GitHub and the Django application would require significant custom automation that is fragile and likely to accumulate complexity over time
- Releases and versioning for citation would require additional tooling and process definition

## Decision

After a testing phase, we decided to adopt **Wagtail** as the content management system for the Swedish Pathogens Portal.

Wagtail directly satisfies the most critical editorial requirements (review workflow, revision history, media library, and preview) while remaining fully integrated with the existing Django codebase. The GitHub-based alternative fails to provide preview and introduces architectural complexity that outweighs its openness advantage.

## Consequences

**Positive:**
- Editorial workflow is supported natively: content can be drafted, reviewed, and approved before publication
- Every page revision is recorded, providing full version history and the ability to revert changes
- A single media library prevents duplicate image uploads across different sections of the site
- Preview support enables editors to verify how pages render before they go live
- No additional external service is required because Wagtail runs within the existing Django application

**Negative:**
- Content stored in the Wagtail database is not publicly open by default
- The team has no existing Wagtail experience, requiring time to learn the framework and its conventions
- The codebase must undergo an extensive migration to adapt it to Wagtail

**Mitigation:**
- Because we are only in a soft-released MVP stage, we decided to rewrite the codebase in a Wagtail-first fashion instead of migrating it so we can carefully craft the different components needed from scratch
- Periodic structured dumps of portal content to a public GitHub repository will address the openness requirement. The dump format should be machine-readable (e.g. JSON or CSV) to support open data use cases
- GitHub releases on the content dump repository (triggered by structural changes such as navigation updates or new site sections rather than individual content edits) will enable version-based citation via Zenodo
- Clear contribution guidelines must accompany the GitHub dump repository to communicate that it is a read-only export and that direct pull requests to modify content via the dump repository will not be accepted
