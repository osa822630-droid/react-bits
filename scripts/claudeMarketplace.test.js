/* eslint-env node */
import assert from 'node:assert/strict';
import { existsSync, lstatSync, readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { componentMetadata, VARIANTS } from '../src/constants/Information.js';
import { claudeCatalogText } from './generateClaudeCatalog.js';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const readJson = file => JSON.parse(readFileSync(path.join(root, file), 'utf8'));
const marketplace = readJson('.claude-plugin/marketplace.json');
const pluginRoot = path.join(root, 'plugins/react-bits');
const plugin = readJson('plugins/react-bits/.claude-plugin/plugin.json');
const skillRoot = path.join(pluginRoot, 'skills/react-bits');
const skill = readFileSync(path.join(skillRoot, 'SKILL.md'), 'utf8');
const catalogPath = path.join(skillRoot, 'assets/catalog.json');
const catalog = JSON.parse(readFileSync(catalogPath, 'utf8'));

function pluginFiles(directory) {
  return readdirSync(directory).flatMap(name => {
    if (name === '__pycache__') return [];
    const file = path.join(directory, name);
    const info = lstatSync(file);
    assert.equal(info.isSymbolicLink(), false, `Plugin cannot contain a symlink: ${file}`);
    return info.isDirectory() ? pluginFiles(file) : [{ file, size: info.size }];
  });
}

test('repository is a Claude marketplace with a real, self-contained plugin source', () => {
  assert.match(marketplace.name, /^[a-z0-9]+(?:-[a-z0-9]+)*$/);
  assert.ok(marketplace.owner.name);
  assert.equal(marketplace.plugins.length, 1);
  const entry = marketplace.plugins[0];
  assert.equal(entry.source, './plugins/react-bits');
  assert.equal(entry.name, plugin.name);
  assert.equal(entry.version, plugin.version);
  assert.match(plugin.name, /^[a-z0-9]+(?:-[a-z0-9]+)*$/);
  assert.ok(plugin.displayName && plugin.description && plugin.author.name);
  assert.ok(existsSync(path.join(pluginRoot, 'LICENSE')));
  assert.ok(existsSync(path.join(pluginRoot, 'README.md')));
  assert.ok(!existsSync(path.join(pluginRoot, 'bin')), 'A top-level bin directory is not allowed in Claude chat');
  const files = pluginFiles(pluginRoot);
  assert.ok(files.length < 5000);
  assert.ok(files.reduce((total, file) => total + file.size, 0) < 200_000_000);
});

test('the skill is discoverable in web chat and its referenced resources are packaged inside it', () => {
  const frontmatter = skill.match(/^---\n([\s\S]+?)\n---\n/);
  assert.ok(frontmatter, 'SKILL.md must start with frontmatter');
  assert.match(frontmatter[1], /^name: react-bits$/m);
  const description = frontmatter[1].match(/^description: (.+)$/m)?.[1];
  assert.ok(description && description.length <= 200);
  assert.match(description, /React Bits/);
  assert.ok(existsSync(catalogPath));
  assert.ok(existsSync(path.join(skillRoot, 'scripts/react_bits.py')));
  assert.match(skill, /assets\/catalog\.json/);
  assert.match(skill, /scripts\/react_bits\.py/);
  assert.doesNotMatch(skill, /npx .*mcp init/);
});

test('bundled catalog is reproducible and tracks every visible component and variant', () => {
  assert.equal(readFileSync(catalogPath, 'utf8'), claudeCatalogText(), 'Run npm run claude:catalog');
  assert.equal(catalog.schemaVersion, 1);
  const visible = Object.values(componentMetadata).filter(component => !component.hidden);
  assert.equal(catalog.components.length, visible.length);
  assert.equal(new Set(catalog.components.map(component => component.name)).size, visible.length);
  for (const component of visible) {
    const item = catalog.components.find(candidate => candidate.name === component.name);
    assert.ok(item, `Missing ${component.name}`);
    assert.equal(item.category, component.category);
    assert.equal(item.description, component.description || '');
    assert.equal(item.docsUrl, component.docsUrl);
    assert.deepEqual(Object.keys(item.variants), component.variants || VARIANTS);
    for (const [variant, details] of Object.entries(item.variants)) {
      const registry = readJson(`public/r/${component.name}-${variant}.json`);
      assert.deepEqual(details.dependencies, registry.dependencies || []);
      assert.deepEqual(details.registryDependencies, registry.registryDependencies || []);
      assert.deepEqual(
        details.files.map(file => file.path),
        registry.files.map(file => file.path)
      );
      assert.ok(
        details.files.every(file => !Object.hasOwn(file, 'content')),
        'Source code should not be bundled'
      );
    }
  }
});

test('catalog includes dependency information for JavaScript, TypeScript and CSS examples', () => {
  const splitText = catalog.components.find(component => component.name === 'SplitText');
  const liquidEther = catalog.components.find(component => component.name === 'LiquidEther');
  const profileCard = catalog.components.find(component => component.name === 'ProfileCard');
  assert.ok(splitText.variants['JS-CSS'].dependencies.some(dep => dep.startsWith('gsap@')));
  assert.ok(liquidEther.variants['JS-CSS'].files.some(file => file.path.endsWith('.css')));
  assert.ok(profileCard.variants['TS-TW'].files.some(file => file.path.endsWith('.tsx')));
  assert.ok(profileCard.variants['TS-TW'].dependencies.some(dep => dep.startsWith('@hugeicons/react@')));
});

test('web instructions use this repository and include the separate plugin installation step', () => {
  const readme = readFileSync(path.join(root, 'README.md'), 'utf8');
  const guide = readFileSync(path.join(root, 'docs/claude-web.ar.md'), 'utf8');
  for (const text of [readme, guide]) {
    assert.match(text, /osa822630-droid\/react-bits/);
    assert.match(text, /Add marketplace/);
    assert.match(text, /Discover/);
  }
});
