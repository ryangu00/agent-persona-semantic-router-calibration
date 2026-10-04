# Credits and provenance

The routing engine is [aurelio-labs/semantic-router](https://github.com/aurelio-labs/semantic-router), version 0.1.15, recorded as MIT in the source record. The deployment used Qwen3-Embedding 0.6B through Ollama. The public reference scorer is a transparent reimplementation of the documented scoring rule; the optional backend calls the library without modifying its source.

The historical persona pool combined an English collection and its Chinese translation/adaptation. Both upstream READMEs stated MIT when checked for the source record on 2026-10-03. This cookbook did not independently fetch their license files, copyright lines, or current repository state.

| Upstream | Supplied pin | Pin date | Publication prerequisite |
|---|---|---|---|
| English persona collection | `783f6a72bf` | 2026-04-12 | Owner-qualified repository URL was not supplied |
| Chinese translation/adaptation | `13b8800f6f` | 2026-05-18 | Owner-qualified repository URL was not supplied |

The original source scripts refer to repository basenames `agency-agents` and `agency-agents-zh`, but do not identify their owners. These are not enough to construct verified repository or commit links. The two URLs and corresponding project credits must be supplied before publication; they have not been guessed.

No upstream persona text, private index, derived phrasing artifact, private evaluation text, or recorded vector cache is distributed here. All fixture persona text and requests are original synthetic material. The three twin pairs use English aliases to demonstrate accept-set behavior while keeping the repository English-only; they do not establish translation quality.

The historical upstream-license claim is deliberately dated. Any future redistribution of upstream text requires reading the actual license files and preserving their copyright notices.
