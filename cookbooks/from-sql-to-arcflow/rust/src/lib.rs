//! Shared fixture for the From SQL to ArcFlow Rust SDK example.
//!
//! Same content as `_common.py` in the Python recipe: 10 persons, 6
//! orgs, 25 employment edges with `since` / `until` / `confidence`.
//! Loaded into BOTH DuckDB (tabular) and ArcFlow (graph) so each
//! step can run the same question in both engines and compare shape.

use anyhow::Result;
use arcflow_sdk::ConcurrentStore;
use duckdb::Connection;

pub struct Both {
    pub sql: Connection,
    pub graph: ConcurrentStore,
}

pub const PERSONS: &[(&str, &str)] = &[
    ("p1", "Alice"),
    ("p2", "Bob"),
    ("p3", "Carol"),
    ("p4", "Dan"),
    ("p5", "Eve"),
    ("p6", "Frank"),
    ("p7", "Grace"),
    ("p8", "Heidi"),
    ("p9", "Ivan"),
    ("p10", "Judy"),
];

pub const ORGS: &[(&str, &str, &str)] = &[
    ("o1", "BioCo",       "biotech"),
    ("o2", "NeuroLabs",   "biotech"),
    ("o3", "DataForge",   "software"),
    ("o4", "PixelStream", "media"),
    ("o5", "FinNexus",    "finance"),
    ("o6", "AeroDyn",     "aerospace"),
];

// (person_id, org_id, since, until_or_null, confidence)
pub const EMPLOYMENT: &[(&str, &str, &str, Option<&str>, f64)] = &[
    ("p1", "o1", "2018-01-01", Some("2020-12-31"), 0.97),
    ("p1", "o3", "2021-02-01", None,               0.95),
    ("p2", "o1", "2019-04-01", Some("2022-06-30"), 0.93),
    ("p2", "o2", "2022-08-01", None,               0.92),
    ("p3", "o3", "2017-03-01", Some("2020-08-31"), 0.88),
    ("p3", "o4", "2020-09-15", None,               0.91),
    ("p4", "o1", "2016-06-01", Some("2019-09-30"), 0.84),
    ("p4", "o5", "2019-10-15", None,               0.79),
    ("p5", "o2", "2018-11-01", Some("2021-04-30"), 0.96),
    ("p5", "o1", "2021-05-15", None,               0.94),
    ("p6", "o3", "2019-01-01", None,               0.81),
    ("p7", "o4", "2017-07-01", Some("2020-01-31"), 0.86),
    ("p7", "o6", "2020-02-15", None,               0.83),
    ("p8", "o5", "2018-04-01", None,               0.90),
    ("p9", "o2", "2020-03-01", None,               0.74),
    ("p10", "o6", "2017-11-01", Some("2021-12-31"), 0.78),
    ("p10", "o3", "2022-01-15", None,               0.85),
    ("p2", "o3", "2017-01-15", Some("2019-03-31"), 0.71),
    ("p4", "o4", "2014-08-01", Some("2016-05-31"), 0.68),
    ("p6", "o5", "2015-09-01", Some("2018-12-31"), 0.66),
    ("p3", "o2", "2014-06-01", Some("2017-02-28"), 0.72),
    ("p8", "o1", "2015-03-01", Some("2018-03-31"), 0.69),
    ("p9", "o4", "2016-10-01", Some("2020-02-28"), 0.81),
    ("p1", "o2", "2014-09-01", Some("2017-12-31"), 0.87),
    ("p5", "o3", "2015-01-01", Some("2018-10-31"), 0.89),
];

pub fn load_both() -> Result<Both> {
    let sql = Connection::open_in_memory()?;
    sql.execute_batch(
        "CREATE TABLE persons (id TEXT PRIMARY KEY, name TEXT); \
         CREATE TABLE orgs (id TEXT PRIMARY KEY, name TEXT, industry TEXT); \
         CREATE TABLE employment ( \
            person_id TEXT, org_id TEXT, since DATE, until DATE, confidence DOUBLE \
         );"
    )?;
    for (id, name) in PERSONS {
        sql.execute(
            "INSERT INTO persons VALUES (?, ?)",
            [*id, *name],
        )?;
    }
    for (id, name, industry) in ORGS {
        sql.execute(
            "INSERT INTO orgs VALUES (?, ?, ?)",
            [*id, *name, *industry],
        )?;
    }
    for (pid, oid, since, until, conf) in EMPLOYMENT {
        sql.execute(
            "INSERT INTO employment VALUES (?, ?, ?, ?, ?)",
            duckdb::params![pid, oid, since, until, conf],
        )?;
    }

    let graph = arcflow_sdk::open_concurrent();
    for (id, name) in PERSONS {
        graph.execute(&format!(
            "CREATE (:Person {{id: '{id}', name: '{name}'}})"
        ))?;
    }
    for (id, name, industry) in ORGS {
        graph.execute(&format!(
            "CREATE (:Org {{id: '{id}', name: '{name}', industry: '{industry}'}})"
        ))?;
    }
    for (pid, oid, since, until, conf) in EMPLOYMENT {
        let until_str = until.map(|u| format!("'{u}'")).unwrap_or_else(|| "null".to_string());
        graph.execute(&format!(
            "MATCH (p:Person {{id: '{pid}'}}), (o:Org {{id: '{oid}'}}) \
             CREATE (p)-[:WORKED_AT {{since: '{since}', until: {until_str}, confidence: {conf}}}]->(o)"
        ))?;
    }

    Ok(Both { sql, graph })
}
