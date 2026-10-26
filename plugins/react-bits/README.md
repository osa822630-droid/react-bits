# React Bits for Claude

This plugin helps Claude find React Bits components and use the published React
Bits registry when building a React interface. It works as a skill in Claude
chat; it does not require Claude Code, a local MCP server, an API key, or a
separately hosted service.

Ask, for example, "Use React Bits SplitText in a React landing page" or "Find a
React Bits animated background for my dashboard." The included catalog supports
search without network access. When the actual component source is needed, the
skill retrieves the selected public registry entry from this repository on
GitHub, or falls back to the official React Bits registry. The request contains
only the component identifier; it does not send the conversation or project
files. Network access and the available React runtime determine whether Claude
can fetch and run the component. If access is blocked, the skill supplies an
installation link or asks you to provide the source instead of guessing.

React Bits is by David Haz and contributors. Its components are subject to the
[repository license](https://github.com/osa822630-droid/react-bits/blob/main/LICENSE.md),
including the Commons Clause restrictions; this plugin does not change that
license. The catalog includes descriptions and dependency metadata, not copies
of component source.
