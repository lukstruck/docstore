This is docstore, a semantic search tool for python documentation.

Use the semantic search tool extensively. Only use the normal search tool and grep when you know very specifically what you need to search for.
Use the sequential thinking tool extensively, especially when making decisions about architecture.

Follow the implementation plan. 
ALWAYS pick the next important open task and implement it. 
ALWAYS update the implementation plan file, before and after you have made a change.
ALWAYS update the current state file.
Split big changes into changes that touch 2 files at most.
Commit after each change.
Before implementing, extensively search the repository.
NEVER circumvent errors. 
NEVER ignore errors and warnings, even if they don't come from your change. 
ALWAYS implement the proper solution and fix.
ALWAYS write a functionality test before writing the implementation (TDD). 
TDD cycle: Write failing test → Implement minimal code  Test passes → Commit.
Do not test trivial things.
Infrastructure code (database sessions, base models, config) doesn't need separate unit tests - it's covered by feature tests.
Test business logic: services, API endpoints, validation rules.
Only mock IO.
Name methods, classes, modules, variables after WHAT they do or stand for, not HOW they work.
ALWAYS comment methods, classes, modules with valuable context, if the name itself is not sufficient. 
NEVER just say "changed this to that", this is not helpful. If the reason for a change is interesting, i.e. because it fixes a bug that was non trivial, then document it.
ALWAYS comment architectural decisions where they make sense and give valuable context in the code.
Whenever a refactor would make the change easier, do so. Use commonly known patterns and refactoring frequently.
ALWAYS prefer the commands recommended by git status or similar over git reset.
NEVER run blocking commands like server starts. Test in other ways, like pytest.
If you see a mismatch between components, or components and docs, or docs and docs, ask me what to do.
Whenever you postpone a task, ALWAYS make a note in the implementation plan and current state BEFORE actually implementing, that you are postponing those steps to later. Ensure that no steps are missed due to lackluster progress documentation.
Before using a library, make sure that you have fetched and looked at the current docs of that library with context7.

Use the semantic search tool extensively. Only use the normal search tool and grep when you know very specifically what you need to search for.
