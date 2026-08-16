import sqlite3
import os
from datetime import datetime

# =====================================================
# DATABASE PATH
# =====================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "database.db")


# =====================================================
# DATABASE CONNECTION
# =====================================================

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# =====================================================
# INITIALIZE DATABASE
# =====================================================

def init_db():

    conn = get_db_connection()
    cursor = conn.cursor()

    # -------------------------------------------------
    # VOTERS
    # -------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voter_id TEXT UNIQUE NOT NULL,
            has_voted INTEGER DEFAULT 0
        )
    """)

    # -------------------------------------------------
    # CANDIDATES
    # -------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            party TEXT NOT NULL
        )
    """)

    # -------------------------------------------------
    # CURRENT ELECTION VOTES
    # -------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voter_id TEXT UNIQUE NOT NULL,
            candidate_name TEXT NOT NULL,
            face_data TEXT,
            timestamp TEXT NOT NULL
        )
    """)

    # -------------------------------------------------
    # ELECTION HISTORY
    # -------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS election_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            winner_name TEXT,
            total_votes INTEGER,
            timestamp TEXT
        )
    """)

    # -------------------------------------------------
    # OLD VOTES HISTORY
    # -------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS votes_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            election_id INTEGER,
            voter_id TEXT,
            candidate_name TEXT,
            face_data TEXT,
            timestamp TEXT
        )
    """)

    # -------------------------------------------------
    # ADD CANDIDATES
    # -------------------------------------------------

    candidates = [
        ("Raman Singh", "BJP Party"),
        ("Anshu Paswan", "RSS Party"),
        ("Rama Yadav", "Samajwadi Party"),
        ("Sagar", "Other Party")
    ]

    for name, party in candidates:

        cursor.execute(
            """
            INSERT OR IGNORE INTO candidates
            (name, party)
            VALUES (?, ?)
            """,
            (name, party)
        )

    conn.commit()
    conn.close()

    print("======================================")
    print("DATABASE INITIALIZED")
    print("DATABASE:", DB_NAME)
    print("======================================")


# =====================================================
# REGISTER / CREATE TEST VOTER
# =====================================================

def register_voter(voter_id):

    voter_id = voter_id.strip()

    if not voter_id:
        return False

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            INSERT OR IGNORE INTO voters
            (voter_id, has_voted)
            VALUES (?, 0)
            """,
            (voter_id,)
        )

        conn.commit()

        return True

    finally:

        conn.close()


# =====================================================
# CHECK VOTER
# =====================================================

def get_voter(voter_id):

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM voters
        WHERE voter_id = ?
        """,
        (voter_id,)
    )

    voter = cursor.fetchone()

    conn.close()

    return voter


# =====================================================
# CHECK ALREADY VOTED
# =====================================================

def has_voted(voter_id):

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM votes
        WHERE voter_id = ?
        """,
        (voter_id,)
    )

    result = cursor.fetchone()

    conn.close()

    return result is not None


# =====================================================
# SAVE VOTE
# =====================================================

def save_vote(
    voter_id,
    candidate_name,
    face_data
):

    conn = get_db_connection()

    cursor = conn.cursor()

    try:

        # ---------------------------------------------
        # DUPLICATE CHECK
        # ---------------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM votes
            WHERE voter_id = ?
            """,
            (voter_id,)
        )

        if cursor.fetchone():

            conn.close()

            return False, "This Voter ID has already voted."

        # ---------------------------------------------
        # REGISTER VOTER IF NOT EXISTS
        # ---------------------------------------------

        cursor.execute(
            """
            INSERT OR IGNORE INTO voters
            (voter_id, has_voted)
            VALUES (?, 0)
            """,
            (voter_id,)
        )

        # ---------------------------------------------
        # INSERT VOTE
        # ---------------------------------------------

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        cursor.execute(
            """
            INSERT INTO votes
            (
                voter_id,
                candidate_name,
                face_data,
                timestamp
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                voter_id,
                candidate_name,
                face_data,
                timestamp
            )
        )

        # ---------------------------------------------
        # MARK VOTER AS VOTED
        # ---------------------------------------------

        cursor.execute(
            """
            UPDATE voters
            SET has_voted = 1
            WHERE voter_id = ?
            """,
            (voter_id,)
        )

        conn.commit()

        return True, "Vote successfully cast!"

    except sqlite3.IntegrityError as error:

        conn.rollback()

        return False, str(error)

    except Exception as error:

        conn.rollback()

        return False, str(error)

    finally:

        conn.close()


# =====================================================
# TOTAL VOTES
# =====================================================

def get_total_votes():

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM votes"
    )

    total = cursor.fetchone()[0]

    conn.close()

    return total


# =====================================================
# CANDIDATE VOTE COUNTS
# =====================================================

def get_vote_counts():

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            candidate_name,
            COUNT(*) AS total
        FROM votes
        GROUP BY candidate_name
    """)

    rows = cursor.fetchall()

    conn.close()

    return {
        row["candidate_name"]: row["total"]
        for row in rows
    }


# =====================================================
# ALL CURRENT VOTES
# =====================================================

def get_all_votes():

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            voter_id,
            candidate_name,
            face_data,
            timestamp
        FROM votes
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


# =====================================================
# RESET VOTER STATUS
# =====================================================

def reset_voters():

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("""
        UPDATE voters
        SET has_voted = 0
    """)

    conn.commit()
    conn.close()


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    init_db()

    print(
        "Current votes:",
        get_total_votes()
    )