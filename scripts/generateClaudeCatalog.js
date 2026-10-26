/* eslint-env node */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { componentMetadata, VARIANTS } from '../src/constants/Information.js';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const output = path.join(root, 'plugins/react-bits/skills/react-bits/assets/catalog.json');

// Keep only searchable metadata in the plugin. The registry remains the source
// of component code, and is fetched on demand rather than redistributed here.
export function buildClaudeCatalog() {
  const components = Object.values(componentMetadata)
    .filter(component => !component.hidden)
    .sort((a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : 0))
    .map(component => {
      const variants = {};
      for (const variant of component.variants || VARIANTS) {
        const filename = path.join(root, 'public/r', `${component.name}-${variant}.json`);
        if (!fs.existsSync(filename)) {
          throw new Error(`Missing registry entry ${filename}. Run npm run registry:build first.`);
        }
        const item = JSON.parse(fs.readFileSync(filename, 'utf8'));
        if (item.name !== `${component.name}-${variant}` || !Array.isArray(item.files) || !item.files.length) {
          throw new Error(`Invalid registry entry: ${filename}`);
        }
        variants[variant] = {
          files: item.files.map(({ path: filePath, type, target }) => ({
            path: filePath,
            ...(type ? { type } : {}),
            ...(target ? { target } : {})
          })),
          dependencies: item.dependencies || [],
          registryDependencies: item.registryDependencies || []
        };
      }
      return {
        name: component.name,
        category: component.category,
        description: component.description || '',
        docsUrl: component.docsUrl,
        variants
      };
    });
  return { schemaVersion: 1, components };
}

export function claudeCatalogText() {
  const catalog = buildClaudeCatalog();
  // Keep one component per line so generated updates are compact and diffable.
  return [
    '{',
    `  "schemaVersion": ${catalog.schemaVersion},`,
    '  "components": [',
    ...catalog.components.map(
      (component, index) => `    ${JSON.stringify(component)}${index < catalog.components.length - 1 ? ',' : ''}`
    ),
    '  ]',
    '}',
    ''
  ].join('\n');
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const content = claudeCatalogText();
  if (process.argv.includes('--check')) {
    if (!fs.existsSync(output) || fs.readFileSync(output, 'utf8') !== content) {
      console.error('Claude catalog is out of date. Run npm run claude:catalog.');
      process.exitCode = 1;
    } else {
      console.log('Claude catalog is up to date.');
    }
  } else {
    fs.mkdirSync(path.dirname(output), { recursive: true });
    fs.writeFileSync(output, content);
    console.log(`Wrote ${path.relative(root, output)}`);
  }
}
