---
name: react-bits
description: Find and use React Bits animated React components, backgrounds, text effects, and UI elements in an app or a Claude artifact.
---

# React Bits

Use this skill when the user asks to find, explain, or build with React Bits.
It is designed for Claude chat as well as other Claude surfaces. The bundled
`assets/catalog.json` is an offline index of this repository's public component
registry; the component source itself is not bundled.

## Find a component

1. Determine the desired effect and the target environment. Infer JavaScript
   vs TypeScript and CSS vs Tailwind from the user's project if possible. When
   it is unspecified, use `JS-CSS` as the starting point; ask only when the
   choice is important. Translate an Arabic or other non-English request into
   useful English search terms when searching the English catalog.
2. Search `assets/catalog.json` or use the bundled Python 3 helper. Paths are
   relative to this `SKILL.md`; in chat the whole skill folder is available in
   the code-execution environment. `${CLAUDE_SKILL_DIR}` is substituted on
   surfaces that support it; otherwise use the actual skill folder path.

   ```sh
   python3 "${CLAUDE_SKILL_DIR}/scripts/react_bits.py" search "text reveal"
   python3 "${CLAUDE_SKILL_DIR}/scripts/react_bits.py" info SplitText --variant JS-CSS
   ```

   Valid variants are `JS-CSS`, `JS-TW`, `TS-CSS`, and `TS-TW`. The `info`
   command shows the actual available variants, documentation, file paths,
   dependencies, and registry links for the selected component. Do not invent
   a component, variant, dependency, or prop. If there is no match, say so and
   suggest the closest catalog entries.

## Obtain and use the actual source

When code is needed, use the helper below. It fetches only the named public
registry entry, first from this repository's `main` branch on GitHub and then,
if necessary, from the official React Bits registry. The output identifies the
source URL and includes the registry JSON with its files and dependencies.
Nothing from the conversation or project is sent by the helper.

```sh
python3 "${CLAUDE_SKILL_DIR}/scripts/react_bits.py" fetch SplitText --variant JS-CSS
```

Read the returned `registry.files`, `dependencies`, and
`registryDependencies`. Copy or adapt all required files together, preserve
stylesheet imports and any required assets, and base example props on the
actual component source or documentation. The `info` command's install link
is another option for the user's local React project. Do not claim to have
installed files or tested a preview unless you actually did so.

If code execution or network access is unavailable, use the offline index to
recommend components, provide the documentation/registry link or exact install
command from `info`, and ask the user to paste or upload the component's
registry JSON/source when exact code is needed. Do not fabricate source code.

For Next.js or another server-rendered app, preserve the client boundary and
handle browser-only APIs on the client. For Claude artifacts, check whether
required libraries, CSS, assets, and browser APIs are supported in that runtime;
explain any limitation rather than promising an executable preview. Respect
reduced-motion preferences and accessibility where practical. React Bits is
subject to the repository's MIT + Commons Clause license; link to
https://github.com/osa822630-droid/react-bits/blob/main/LICENSE.md when the
user needs licensing details.
