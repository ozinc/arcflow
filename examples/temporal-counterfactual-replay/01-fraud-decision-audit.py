"""
Fraud decision audit — what did the world model show when the transfer was approved?

Pattern: a fraud-risk system approves a transfer based on the customer's
state at that moment. Days later, the customer disputes the transfer,
or new evidence emerges that the customer's account had been compromised.
The auditor needs to reconstruct EXACTLY what data the approval saw.

`AS OF seq <param>` returns the world model at any past WAL sequence —
deterministic, bit-for-bit replayable, forever.

Setup: an Account starts clean, then is updated as new fraud signals
arrive. The approval was recorded at seq N. Replay replays.
"""

import shutil
import tempfile

from arcflow import ArcFlow

def main():
    data_dir = tempfile.mkdtemp(prefix="arcflow-fraud-audit-")
    db = ArcFlow(data_dir)

    # Seq 1: Account opens.
    db.execute("""
        CREATE (a:Account {
            id: 'ACC-789',
            holder: 'Alice',
            risk_score: 0.10,
            verified: true
        })
    """)
    print("seq 1: account opened (risk_score=0.10, verified=true)")

    # Seq 2: Approval recorded — at this point in time, risk was 0.10.
    db.execute("""
        CREATE (t:Transfer {id: 'TX-001', amount: 50000, target: 'EXT-9942'})
        WITH t
        MATCH (a:Account {id: 'ACC-789'})
        CREATE (a)-[:AUTHORIZED]->(t)
    """)
    approval_seq = 2  # the seq the transfer was approved at
    print(f"seq {approval_seq}: transfer TX-001 approved against this state")

    # Seq 3: An anti-fraud signal arrives 4 hours later.
    db.execute("""
        MATCH (a:Account {id: 'ACC-789'})
        SET a.risk_score = 0.85
    """)
    print("seq 3: risk score elevated to 0.85 (post-approval signal)")

    # Seq 4: Account flagged for review.
    db.execute("""
        MATCH (a:Account {id: 'ACC-789'})
        SET a.verified = false
    """)
    print("seq 4: verification revoked")

    # The auditor's question: "What did the approval see?"
    print(f"\nAS OF seq {approval_seq} — state visible to the approval system:")
    for r in db.execute(
        "MATCH (a:Account {id: 'ACC-789'}) AS OF seq $s "
        "RETURN a.id AS id, a.risk_score AS risk, a.verified AS verified",
        params={"s": approval_seq},
    ):
        print(f"  {dict(r)}")

    print("\nCurrent state — what the system shows now:")
    for r in db.execute(
        "MATCH (a:Account {id: 'ACC-789'}) "
        "RETURN a.id AS id, a.risk_score AS risk, a.verified AS verified"
    ):
        print(f"  {dict(r)}")

    print("\nObservation: the approval saw risk=0.10, verified=true. The current")
    print("post-fact state shows risk=0.85, verified=false. The approval was made")
    print("on the data available at seq 2 — that's the auditable answer, forever.")

    db.close()
    shutil.rmtree(data_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
