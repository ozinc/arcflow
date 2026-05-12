//! Shared loader for the Fraud Graph Traversal Rust SDK example.
//!
//! Reads the same `../data/transfers.parquet` fixture the Python recipe
//! generates and builds the same `Account` + `Transfer` schema:
//!
//! ```text
//! (:Account {account_id})
//! (:Transfer {transfer_id, amount, ts})
//! (:Account)-[:SENT]->(:Transfer)-[:TO]->(:Account)
//! ```
//!
//! Each transfer is its own node — multiple transfers between the same
//! pair coexist as distinct events. Repetition is the AML signal.

use anyhow::{Context, Result};
use arcflow_sdk::ConcurrentStore;
use arrow::record_batch::RecordBatch;
use parquet::arrow::arrow_reader::ParquetRecordBatchReaderBuilder;
use std::fs::File;
use std::path::Path;

pub fn load(parquet_path: &Path) -> Result<(ConcurrentStore, usize)> {
    let file = File::open(parquet_path)
        .with_context(|| format!("opening {}", parquet_path.display()))?;
    let builder = ParquetRecordBatchReaderBuilder::try_new(file)?;
    let reader = builder.build()?;
    let db = arcflow_sdk::open_concurrent();

    let mut total_rows = 0;
    let mut accounts_seen = std::collections::HashSet::new();

    for batch in reader {
        let batch: RecordBatch = batch?;
        // Expecting columns: transfer_id, src, dst, amount, ts
        let n = batch.num_rows();
        total_rows += n;

        let src_col = column_string(&batch, "src")?;
        let dst_col = column_string(&batch, "dst")?;
        let amt_col = column_f64(&batch, "amount")?;
        let id_col  = column_string(&batch, "transfer_id")?;
        let ts_col  = column_string(&batch, "ts")?;

        for i in 0..n {
            let src = src_col[i].as_str();
            let dst = dst_col[i].as_str();
            let amt = amt_col[i];
            let id  = id_col[i].as_str();
            let ts  = ts_col[i].as_str();

            // MERGE accounts on first sight (using HashSet for client-side
            // dedup; on the server side a unique-constraint or MERGE would
            // be the production choice).
            if accounts_seen.insert(src.to_string()) {
                db.execute(&format!("CREATE (:Account {{account_id: '{src}'}})"))?;
            }
            if accounts_seen.insert(dst.to_string()) {
                db.execute(&format!("CREATE (:Account {{account_id: '{dst}'}})"))?;
            }

            db.execute(&format!(
                "MATCH (a:Account {{account_id: '{src}'}}), \
                       (b:Account {{account_id: '{dst}'}}) \
                 CREATE (a)-[:SENT]->(:Transfer {{ \
                    transfer_id: '{id}', amount: {amt}, ts: '{ts}' \
                 }})-[:TO]->(b)",
            ))?;
        }
    }

    Ok((db, total_rows))
}

fn column_string(batch: &RecordBatch, name: &str) -> Result<Vec<String>> {
    let col = batch.column_by_name(name)
        .with_context(|| format!("column {name} missing"))?;
    let arr = col.as_any()
        .downcast_ref::<arrow::array::StringArray>()
        .with_context(|| format!("column {name} not a string"))?;
    Ok((0..arr.len()).map(|i| arr.value(i).to_string()).collect())
}

fn column_f64(batch: &RecordBatch, name: &str) -> Result<Vec<f64>> {
    let col = batch.column_by_name(name)
        .with_context(|| format!("column {name} missing"))?;
    let arr = col.as_any()
        .downcast_ref::<arrow::array::Float64Array>()
        .with_context(|| format!("column {name} not f64"))?;
    Ok((0..arr.len()).map(|i| arr.value(i)).collect())
}
