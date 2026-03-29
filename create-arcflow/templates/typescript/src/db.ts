import { openInMemory, open, type ArcflowDB } from 'arcflow'

// Switch to open('./data') for persistent storage
export function createDB(): ArcflowDB {
  return openInMemory()
}
