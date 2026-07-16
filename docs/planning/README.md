# Rubberneck Project Planning

This directory is the project's working memory. It records what we intend to
build, how we decide a feature is complete, and what we learn along the way.

## Documents

- [ROADMAP.md](ROADMAP.md) defines feature blocks and acceptance criteria.
- [TODO.md](TODO.md) is the active, checkbox-based work queue.
- [DECISIONS.md](DECISIONS.md) records architectural and product decisions.
- [DIARY.md](DIARY.md) is a chronological record of meaningful development.

## Working Agreement

1. Select the next feature block from `ROADMAP.md`.
2. Add or refine its implementation tasks in `TODO.md` before coding.
3. Treat every acceptance criterion as required unless the plan is explicitly
   revised.
4. Record decisions that constrain future work in `DECISIONS.md`.
5. Add a short diary entry after a meaningful feature, investigation, or
   change in direction.
6. Mark a feature block complete only after its tests pass and all acceptance
   criteria are satisfied.

## Status Vocabulary

- **Planned**: scoped but not started.
- **In progress**: actively being implemented.
- **Blocked**: cannot progress without a decision or external change.
- **Complete**: acceptance criteria are satisfied and verified.
- **Deferred**: intentionally postponed with a reason recorded.
