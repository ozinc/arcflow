#!/usr/bin/env node
import { mkdirSync, writeFileSync, readFileSync, cpSync, existsSync, readdirSync, statSync, renameSync } from 'node:fs'
import { join, resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))

const args = process.argv.slice(2)
let template = 'typescript'
const positional = []
for (let i = 0; i < args.length; i++) {
  const a = args[i]
  if (a === '--template' || a === '-t') {
    template = args[++i]
  } else if (a.startsWith('--template=')) {
    template = a.slice('--template='.length)
  } else if (a === '--help' || a === '-h') {
    printHelpAndExit(0)
  } else {
    positional.push(a)
  }
}

const VALID_TEMPLATES = ['typescript', 'python']
if (!VALID_TEMPLATES.includes(template)) {
  console.error(`\n  Error: unknown template "${template}". Valid: ${VALID_TEMPLATES.join(', ')}.\n`)
  process.exit(1)
}

const projectName = positional[0] || 'arcflow-project'
const projectDir = resolve(projectName)

if (existsSync(projectDir)) {
  console.error(`\n  Error: Directory "${projectName}" already exists.\n`)
  process.exit(1)
}

const templateDir = join(__dirname, 'templates', template)
if (!existsSync(templateDir)) {
  console.error(`\n  Error: template "${template}" not found at ${templateDir}.\n`)
  process.exit(1)
}

console.log(`\n  Creating ArcFlow ${template} project in ${projectDir}...\n`)

cpSync(templateDir, projectDir, { recursive: true })

// Python: hyphenated project name → underscored package (importable) name.
// Template ships the package under src/__PACKAGE_NAME__/; rename the directory
// to the real package name, then substitute {{PROJECT_NAME}} / {{PACKAGE_NAME}}
// across every text file.
const packageName = projectName.replace(/-/g, '_').replace(/[^a-zA-Z0-9_]/g, '_')

if (template === 'python') {
  const placeholderDir = join(projectDir, 'src', '__PACKAGE_NAME__')
  const realDir = join(projectDir, 'src', packageName)
  if (existsSync(placeholderDir)) {
    renameSync(placeholderDir, realDir)
  }
}

substituteInTree(projectDir, {
  '{{PROJECT_NAME}}': projectName,
  '{{PACKAGE_NAME}}': packageName,
})

console.log('  Done! Next steps:\n')
console.log(`    cd ${projectName}`)
if (template === 'python') {
  console.log('    python -m venv .venv')
  console.log('    source .venv/bin/activate')
  console.log('    pip install -e .[dev]')
  console.log(`    python -m ${packageName}.main\n`)
} else {
  console.log('    npm install')
  console.log('    npx tsx src/index.ts\n')
}
console.log('  Docs: https://github.com/ozinc/arcflow')
console.log('  MCP:  npx arcflow-mcp\n')

function substituteInTree(dir, replacements) {
  for (const entry of readdirSync(dir)) {
    const path = join(dir, entry)
    const st = statSync(path)
    if (st.isDirectory()) {
      substituteInTree(path, replacements)
      continue
    }
    if (!st.isFile()) continue
    let content
    try {
      content = readFileSync(path, 'utf-8')
    } catch {
      continue // binary file
    }
    let next = content
    for (const [needle, value] of Object.entries(replacements)) {
      next = next.split(needle).join(value)
    }
    if (next !== content) writeFileSync(path, next)
  }
}

function printHelpAndExit(code) {
  console.log(`
  create-arcflow — scaffold an ArcFlow project

  Usage:
    npm create arcflow@latest <project-name> [-- --template <python|typescript>]

  Templates:
    typescript  (default) — Node + 'arcflow' npm package, Vitest, tsx
    python                — venv + oz-arcflow, PyArrow + Polars zero-copy, pytest

  Examples:
    npm create arcflow@latest my-app
    npm create arcflow@latest my-pipeline -- --template python
`)
  process.exit(code)
}
