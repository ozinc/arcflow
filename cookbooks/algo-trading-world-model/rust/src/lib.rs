//! Shared fixture for the Algo-Trading World Model Rust SDK example.
//!
//! Mirrors `_load.py` in the Python recipe — same 8 symbols, same 60
//! trading days of OHLCV, same fundamentals with the ENGY-02 day-35
//! restatement landmine, same two LLM-emitted sentiment sources, same
//! HMM regime beliefs. Every fact carries `_observation_class` +
//! `_confidence` + `_source`, so the same MATCH shapes spanning observed
//! / inferred / predicted work identically across the Python and Rust
//! versions.

use anyhow::Result;
use arcflow_sdk::ConcurrentStore;
use rand::{Rng, SeedableRng};
use rand_chacha::ChaCha8Rng;

pub const SYMBOLS: &[(&str, &str, f64)] = &[
    ("TECH-01", "Tech",    150.0),
    ("TECH-02", "Tech",    220.0),
    ("TECH-03", "Tech",     85.0),
    ("ENGY-01", "Energy",  110.0),
    ("ENGY-02", "Energy",   75.0),
    ("HLTH-01", "Health",  340.0),
    ("HLTH-02", "Health",  180.0),
    ("HLTH-03", "Health",   95.0),
];

pub const DAYS: u32 = 60;
pub const RESTATEMENT_DAY: u32 = 35;

/// Build the operational world model.
///
/// Returns a `ConcurrentStore`. Use `arcflow_sdk::open_concurrent()` for
/// the in-memory variant; for persistent on-disk storage with WAL-backed
/// `AS OF seq` replay across process restarts, swap in `JournaledStore`
/// at the call site (the bulk-load shape below works against both).
pub fn make_db() -> Result<ConcurrentStore> {
    let mut rng = ChaCha8Rng::seed_from_u64(7);
    let db = arcflow_sdk::open_concurrent();

    // --- Symbols + day-zero fundamentals (observed, bulk-loaded) ---------
    // Bulk-creates bypass the WAL — cold history we never replay
    // seq-by-seq. Decisions and revisions enter through execute() later
    // so the WAL stays a clean log of *what changed*.
    for (tkr, sec, init) in SYMBOLS {
        db.execute(&format!(
            "CREATE (:Symbol {{ \
                ticker: '{tkr}', sector: '{sec}', init_close: {init}, \
                _observation_class: 'observed', _confidence: 1.0, \
                _source: 'reference_data_v1' \
            }})"
        ))?;
    }

    for (tkr, _sec, _init) in SYMBOLS {
        let eps: f64 = round2(rng.gen_range(2.0..8.0));
        let book_value: f64 = round2(rng.gen_range(30.0..90.0));
        db.execute(&format!(
            "MATCH (s:Symbol {{ticker: '{tkr}'}}) \
             CREATE (s)-[:HAS_FUNDAMENTAL]->(:Fundamental {{ \
                ticker: '{tkr}', as_of_day: 0, eps: {eps}, \
                book_value: {book_value}, revision: 'original', \
                _observation_class: 'observed', _confidence: 1.0, \
                _source: 'fundamentals_filing_v1' \
             }})"
        ))?;
    }

    // --- OHLCV bars — 8 symbols × 60 days (observed) ---------------------
    for (tkr, sec, init_close) in SYMBOLS {
        let mut price = *init_close;
        for d in 0..DAYS {
            let shock: f64 = rng.gen_range(-1.0..1.0) * init_close * 0.012;
            price = (price + shock).max(1.0);
            let open = price * (1.0 + rng.gen_range(-0.003..0.003));
            let high = price.max(open) * (1.0 + rng.gen_range(0.0..0.005));
            let low  = price.min(open) * (1.0 - rng.gen_range(0.0..0.005));
            let volume: u64 = rng.gen_range(800_000..5_000_000);

            db.execute(&format!(
                "MATCH (s:Symbol {{ticker: '{tkr}'}}) \
                 CREATE (s)-[:HAS_BAR]->(:DailyBar {{ \
                    ticker: '{tkr}', sector: '{sec}', day_idx: {d}, \
                    open: {open:.3}, high: {high:.3}, low: {low:.3}, \
                    close: {price:.3}, volume: {volume}, \
                    _observation_class: 'observed', _confidence: 0.99, \
                    _source: 'tape_v1' \
                 }})"
            ))?;
        }
    }

    // --- News sentiment — two LLM sources (predicted) --------------------
    let sentiment: &[(&str, u32, f64, f64, &str, &str)] = &[
        ("TECH-01",  8,  0.42, 0.55, "earnings beat rumor",        "sentiment_llm_v1"),
        ("TECH-01", 22, -0.18, 0.40, "supply-chain article",       "sentiment_llm_v1"),
        ("TECH-03", 12,  0.61, 0.62, "product launch leak",        "sentiment_llm_v2"),
        ("ENGY-02", 30,  0.30, 0.45, "buyback chatter",            "sentiment_llm_v2"),
        ("ENGY-02", 38, -0.55, 0.70, "fraud investigation report", "sentiment_llm_v1"),
        ("HLTH-02", 44,  0.25, 0.50, "FDA decision speculation",   "sentiment_llm_v2"),
    ];
    for (tkr, day, score, conf, topic, src) in sentiment {
        db.execute(&format!(
            "MATCH (s:Symbol {{ticker: '{tkr}'}}) \
             CREATE (s)-[:MENTIONS]->(:NewsSentiment {{ \
                ticker: '{tkr}', day_idx: {day}, score: {score}, \
                _confidence: {conf}, _observation_class: 'predicted', \
                _source: '{src}', headline_topic: '{topic}' \
             }})"
        ))?;
    }

    // --- HMM regime beliefs (predicted) ----------------------------------
    let regimes = ["trending", "mean_reverting", "high_vol", "low_vol"];
    for (tkr, _sec, _init) in SYMBOLS {
        for d in [15u32, 30, 45, 55] {
            let regime = regimes[rng.gen_range(0..4)];
            let conf = round2(rng.gen_range(0.55..0.75));
            db.execute(&format!(
                "MATCH (s:Symbol {{ticker: '{tkr}'}}) \
                 CREATE (s)-[:REGIME_FOR]->(:RegimeBelief {{ \
                    ticker: '{tkr}', day_idx: {d}, regime: '{regime}', \
                    _observation_class: 'predicted', _confidence: {conf}, \
                    _source: 'regime_hmm_v1' \
                 }})"
            ))?;
        }
    }

    Ok(db)
}

pub fn print_stats(db: &ConcurrentStore) -> Result<()> {
    for (label, q) in [
        ("symbols",        "MATCH (s:Symbol) RETURN count(*) AS n"),
        ("fundamentals",   "MATCH (f:Fundamental) RETURN count(*) AS n"),
        ("bars",           "MATCH (b:DailyBar) RETURN count(*) AS n"),
        ("news",           "MATCH (n:NewsSentiment) RETURN count(*) AS n"),
        ("regime_beliefs", "MATCH (r:RegimeBelief) RETURN count(*) AS n"),
    ] {
        let result = db.execute(q)?;
        let n = result.rows.first()
            .and_then(|row| row.get("n"))
            .cloned()
            .unwrap_or_else(|| "0".to_string());
        println!("  {label:18}  {n}");
    }
    Ok(())
}

fn round2(x: f64) -> f64 {
    (x * 100.0).round() / 100.0
}
