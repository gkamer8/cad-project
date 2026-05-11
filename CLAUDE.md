# Code Quality and Standards

The coding philosophy you should aspire to is the following:

1. **Don't repeat yourself.** We want the code to be flexible so that new features can be added with a minimal amount of code.
2. **Every line of code should be run often during regular usage.** We want to eliminate long-tail errors that can be caused by hitting mostly unused codepaths. Before creating branching logic, ask whether it is truly necessary. This helps us avoid complexity and ensure the code is battle-tested. By "code paths" we mean lines of code: every branching statement is a risk.
3. **Prefer typed objects to hardcoded strings as keys.** Instead of using Python dictionaries all the time with arbitrary string keys, consider using Enum types or special objects that contain relevant information.
4. **Failures should be loud.** This is not to say that you should implement custom exceptions or write `raise` statements. Python will raise natural and meaningful exceptions without our needing to raise them explicitly. We want broken or incorrect code to create errors, not fail silently. We want as few "fallbacks" as possible. **In general, we do NOT WANT FALLBACKS.**
5. **"Backwards compatibility" is rarely important.** Much better to just use the updated API/pattern. We have complete control over our own backend, database, etc. If migrations are needed, we'll do them. Do not put in excessive code meant to support "backwards compatibility."
6. **KISS: Keep it simple, stupid.** Files should never be longer than 500 lines. We want clarity of thought and simplicity to radiate from the code.

Code should **not** be "defensive" in this codebase. "Defensive" code is usually bad code.

## Strongly disfavored

The following Python language features are STRONGLY DISFAVORED:

1. **Default arguments for functions.** We do not want "defaults" for every function. We do not want it to be possible for an accidental default value to sneak in because a function call was made with some missing argument.
2. **The `.get()` method on Python dictionaries.** If a dictionary doesn't have a key that it should have, that should fail loudly so that it can be addressed.
3. **Sleep functions.** Only on the rarest occasions are sleep functions acceptable. We don't want to paper-over race conditions by calling sleep.

## Banned without explicit permission

The following Python language features are BANNED except via explicit permission from the user for each instance of usage:

1. **`try`/`except` statements.** You may NOT use ANY `try`/`except` statements EVER without per-use permission from the user. We want failures to be loud so they are addressed. There is already logic in the code to gracefully handle errors for briefings and bring them to the user; that logic is useless if code doesn't throw errors when they should. Note that you may still use `try`/`finally` statements when necessary.
2. **`hasattr` / `setattr`.** Don't guess at what an object should have. Either it has it or it doesn't. Be sure by reading documentation or reasoning about the code.
3. **Dynamic imports.** Imports should ALWAYS be placed at the top of files — not inside functions. If this would cause a circular import, refactor the code so that it doesn't happen.

It is OK if some existing code does not meet the above standards; we just don't want to add to the mess.

## Notes on Git

Nn general, we want to keep commits light (so commit early and often). Put features in a feature branch and open a PR. When you're about done with a feature, give me a link to review, and merge when I say so.
