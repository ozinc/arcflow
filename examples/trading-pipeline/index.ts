// ArcFlow SDK — Trading Pipeline Example
// Demonstrates batch ingestion, sector aggregation, and live views.

import { openInMemory } from 'arcflow'

const db = openInMemory()

// ── Load market data ──
console.log('Loading market data...')
db.batchMutate([
  "CREATE (n:DailyBar {symbol: 'AAPL', date: '2024-06-10', close: 190.0, volume: 51000000, sector: 'Tech'})",
  "CREATE (n:DailyBar {symbol: 'AAPL', date: '2024-06-11', close: 191.5, volume: 48000000, sector: 'Tech'})",
  "CREATE (n:DailyBar {symbol: 'AAPL', date: '2024-06-12', close: 192.5, volume: 54000000, sector: 'Tech'})",
  "CREATE (n:DailyBar {symbol: 'AAPL', date: '2024-06-13', close: 193.0, volume: 46000000, sector: 'Tech'})",
  "CREATE (n:DailyBar {symbol: 'AAPL', date: '2024-06-14', close: 195.0, volume: 52000000, sector: 'Tech'})",
  "CREATE (n:DailyBar {symbol: 'MSFT', date: '2024-06-10', close: 435.0, volume: 21000000, sector: 'Tech'})",
  "CREATE (n:DailyBar {symbol: 'MSFT', date: '2024-06-11', close: 437.2, volume: 19000000, sector: 'Tech'})",
  "CREATE (n:DailyBar {symbol: 'MSFT', date: '2024-06-12', close: 441.2, volume: 22000000, sector: 'Tech'})",
  "CREATE (n:DailyBar {symbol: 'MSFT', date: '2024-06-13', close: 439.8, volume: 20000000, sector: 'Tech'})",
  "CREATE (n:DailyBar {symbol: 'MSFT', date: '2024-06-14', close: 442.0, volume: 18000000, sector: 'Tech'})",
  "CREATE (n:DailyBar {symbol: 'JPM', date: '2024-06-10', close: 198.5, volume: 12000000, sector: 'Finance'})",
  "CREATE (n:DailyBar {symbol: 'JPM', date: '2024-06-11', close: 199.0, volume: 11000000, sector: 'Finance'})",
  "CREATE (n:DailyBar {symbol: 'JPM', date: '2024-06-12', close: 201.3, volume: 13000000, sector: 'Finance'})",
  "CREATE (n:DailyBar {symbol: 'JPM', date: '2024-06-13', close: 200.1, volume: 10000000, sector: 'Finance'})",
  "CREATE (n:DailyBar {symbol: 'JPM', date: '2024-06-14', close: 202.5, volume: 14000000, sector: 'Finance'})",
])

const stats = db.stats()
console.log(`Loaded ${stats.nodes} bars\n`)

// ── Sector aggregation ──
console.log('Sector aggregation:')
const sectors = db.query(
  "MATCH (n:DailyBar) RETURN n.sector, count(*) AS cnt, avg(n.close) AS avgClose",
)
for (const row of sectors.rows) {
  console.log(`  ${row.get('sector')}: ${row.get('cnt')} bars, avg close $${row.get('avgClose')}`)
}

// ── Point query ──
console.log('\nAAPL on 2024-06-14:')
const point = db.query(
  "MATCH (n:DailyBar) WHERE n.symbol = $sym AND n.date = $date RETURN n.close, n.volume",
  { sym: 'AAPL', date: '2024-06-14' },
)
if (point.rowCount > 0) {
  console.log(`  Close: $${point.rows[0].get('close')}, Volume: ${point.rows[0].get('volume')}`)
}

// ── Per-symbol statistics ──
console.log('\nPer-symbol statistics:')
const symbols = db.query(
  "MATCH (n:DailyBar) RETURN n.symbol, count(*) AS days, avg(n.close) AS avgClose, avg(n.volume) AS avgVol",
)
for (const row of symbols.rows) {
  console.log(
    `  ${row.get('symbol')}: ${row.get('days')} days, avg $${row.get('avgClose')}, avg vol ${row.get('avgVol')}`,
  )
}

// ── Live view ──
console.log('\nCreating live view...')
db.mutate(
  "CREATE LIVE VIEW sector_stats AS MATCH (n:DailyBar) RETURN n.sector, count(*), avg(n.close)",
)

// New data arrives
console.log('New bar arrives: AAPL 2024-06-15 close=$197.0')
db.mutate(
  "CREATE (n:DailyBar {symbol: 'AAPL', date: '2024-06-15', close: 197.0, volume: 50000000, sector: 'Tech'})",
)

// Live view updated automatically
const updated = db.query("MATCH (n:DailyBar) WHERE n.sector = 'Tech' RETURN count(*) AS cnt")
console.log(`Tech sector now has ${updated.rows[0].get('cnt')} bars (was 10, now 11)`)

db.close()
console.log('\nDone!')
