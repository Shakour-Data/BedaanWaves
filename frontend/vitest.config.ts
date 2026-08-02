import { defineConfig } from 'vitest/config'
import path from 'path'

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['**/*.test.ts', '**/*.test.tsx'],
    exclude: ['node_modules/', '.next/', 'dist/'],
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
    clearMocks: true,
    setupFiles: ['./src/tests/setup.ts'],
  },
})