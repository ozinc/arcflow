#!/usr/bin/env node
import { mkdirSync, writeFileSync, readFileSync, cpSync, existsSync } from 'node:fs'
import { join, resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const projectName = process.argv[2] || 'arcflow-project'
const projectDir = resolve(projectName)

if (existsSync(projectDir)) {
  console.error(`\n  Error: Directory "${projectName}" already exists.\n`)
  process.exit(1)
}

console.log(`\n  Creating ArcFlow project in ${projectDir}...\n`)

cpSync(join(__dirname, 'templates', 'typescript'), projectDir, { recursive: true })

// Replace placeholder in package.json
const pkgPath = join(projectDir, 'package.json')
let pkgContent = readFileSync(pkgPath, 'utf-8')
pkgContent = pkgContent.replace(/\{\{PROJECT_NAME\}\}/g, projectName)
writeFileSync(pkgPath, pkgContent)

console.log('  Done! Next steps:\n')
console.log(`    cd ${projectName}`)
console.log('    npm install')
console.log('    npx tsx src/index.ts\n')
console.log('  Docs: https://github.com/ozinc/arcflow')
console.log('  MCP:  npx arcflow-mcp\n')
