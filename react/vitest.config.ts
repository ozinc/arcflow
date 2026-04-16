import { defineConfig } from 'vitest/config'
import { resolve } from 'node:path'

export default defineConfig({
  resolve: {
    alias: {
      // arcflow package installs via file:../typescript; dist/index.js is the built CJS output
      arcflow: resolve(__dirname, 'node_modules/arcflow/dist/index.js'),
    },
  },
  test: {
    environment: 'happy-dom',
    globals: false,
  },
})
