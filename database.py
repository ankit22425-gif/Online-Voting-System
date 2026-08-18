import sqlite3
import os
from datetime import datetime


# =====================================================
# DATABASE
# =====================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "database.db")


# =====================================================
# CONNECTION
# =====================================================

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# =====================================================
# ELECTION TYPES
# =====================================================

ELECTION_TYPES = [
    "RAJYA SABHA ELECTION",
    "LOK SABHA ELECTION",
    "GRAM PANCHAYAT ELECTION"
]


# =====================================================
# 15 SYMBOLS
# =====================================================

ELECTION_SYMBOLS = [
    "🌸",
    "🚩",
    "✋",
    "🪷",
    "🐘",
    "🦁",
    "🌾",
    "⭐",
    "🛞",
    "🪔",
    "🍃",
    "☀️",
    "🚲",
    "🎯",
    "🕊️"
]


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
    # ELECTIONS
    # -------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS elections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            election_type TEXT NOT NULL,
            election_name TEXT NOT NULL,
            status TEXT DEFAULT 'ACTIVE',
            created_at TEXT NOT NULL
        )
    """)

    # -------------------------------------------------
    # CANDIDATES
    # -------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            election_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            party TEXT NOT NULL,
            symbol TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(election_id, name),
            UNIQUE(election_id, symbol),
            FOREIGN KEY(election_id)
                REFERENCES elections(id)
                ON DELETE CASCADE
        )
    """)

    # -------------------------------------------------
    # CURRENT VOTES
    # -------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            election_id INTEGER NOT NULL,
            voter_id TEXT UNIQUE NOT NULL,
            candidate_id INTEGER NOT NULL,
            candidate_name TEXT NOT NULL,
            face_data TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY(election_id)
                REFERENCES elections(id),
            FOREIGN KEY(candidate_id)
                REFERENCES candidates(id)
        )
    """)

    # -------------------------------------------------
    # ELECTION HISTORY
    # -------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS election_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            election_id INTEGER,
            election_name TEXT,
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
            election_name TEXT,
            voter_id TEXT,
            candidate_name TEXT,
            party TEXT,
            symbol TEXT,
            face_data TEXT,
            timestamp TEXT
        )
    """)

    conn.commit()
    conn.close()

    print("======================================")
    print("DATABASE INITIALIZED")
    print("DATABASE:", DB_NAME)
    print("======================================")


# =====================================================
# CREATE ELECTION
# =====================================================

def create_election(election_type):

    election_type = election_type.strip()

    if election_type not in ELECTION_TYPES:
        return False, "Invalid election type."

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        # Close any previous active election
        cursor.execute("""
            UPDATE elections
            SET status = 'COMPLETED'
            WHERE status = 'ACTIVE'
        """)

        year = datetime.now().year

        election_name = f"{election_type} {year}"

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        cursor.execute("""
            INSERT INTO elections
            (
                election_type,
                election_name,
                status,
                created_at
            )
            VALUES (?, ?, 'ACTIVE', ?)
        """, (
            election_type,
            election_name,
            timestamp
        ))

        election_id = cursor.lastrowid

        conn.commit()

        return True, election_id

    except Exception as error:

        conn.rollback()

        return False, str(error)

    finally:

        conn.close()


# =====================================================
# GET ACTIVE ELECTION
# =====================================================

def get_active_election():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM elections
        WHERE status = 'ACTIVE'
        ORDER BY id DESC
        LIMIT 1
    """)

    election = cursor.fetchone()

    conn.close()

    return election


# =====================================================
# GET ELECTION BY ID
# =====================================================

def get_election(election_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM elections
        WHERE id = ?
    """, (election_id,))

    election = cursor.fetchone()

    conn.close()

    return election


# =====================================================
# ADD CANDIDATE
# =====================================================

def add_candidate(
    election_id,
    name,
    party,
    symbol
):

    name = name.strip()
    party = party.strip()
    symbol = symbol.strip()

    if not name:
        return False, "Candidate name is required."

    if not party:
        return False, "Party name is required."

    if not symbol:
        return False, "Election symbol is required."

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        # -------------------------------------------------
        # CHECK CANDIDATE LIMIT
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM candidates
            WHERE election_id = ?
        """, (election_id,))

        count = cursor.fetchone()[0]

        if count >= 15:

            return (
                False,
                "Maximum 15 candidates allowed."
            )

        # -------------------------------------------------
        # CHECK SYMBOL
        # -------------------------------------------------

        if symbol not in ELECTION_SYMBOLS:

            return (
                False,
                "Please select a valid election symbol."
            )

        # -------------------------------------------------
        # CHECK DUPLICATE SYMBOL
        # -------------------------------------------------

        cursor.execute("""
            SELECT id
            FROM candidates
            WHERE election_id = ?
              AND symbol = ?
        """, (
            election_id,
            symbol
        ))

        if cursor.fetchone():

            return (
                False,
                "This election symbol is already used."
            )

        # -------------------------------------------------
        # INSERT
        # -------------------------------------------------

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        cursor.execute("""
            INSERT INTO candidates
            (
                election_id,
                name,
                party,
                symbol,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            election_id,
            name,
            party,
            symbol,
            timestamp
        ))

        conn.commit()

        return True, "Candidate added successfully."

    except sqlite3.IntegrityError:

        conn.rollback()

        return (
            False,
            "Candidate name already exists for this election."
        )

    except Exception as error:

        conn.rollback()

        return False, str(error)

    finally:

        conn.close()


# =====================================================
# GET CANDIDATES
# =====================================================

def get_candidates(election_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            election_id,
            name,
            party,
            symbol,
            created_at
        FROM candidates
        WHERE election_id = ?
        ORDER BY id ASC
    """, (election_id,))

    rows = cursor.fetchall()

    conn.close()

    return rows


# =====================================================
# DELETE CANDIDATE
# =====================================================

def delete_candidate(candidate_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            DELETE FROM candidates
            WHERE id = ?
        """, (candidate_id,))

        conn.commit()

        return True

    except Exception:

        conn.rollback()

        return False

    finally:

        conn.close()


# =====================================================
# REGISTER VOTER
# =====================================================

def register_voter(voter_id):

    voter_id = voter_id.strip()

    if not voter_id:
        return False

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT OR IGNORE INTO voters
            (
                voter_id,
                has_voted
            )
            VALUES (?, 0)
        """, (voter_id,))

        conn.commit()

        return True

    except Exception:

        conn.rollback()

        return False

    finally:

        conn.close()


# =====================================================
# GET VOTER
# =====================================================

def get_voter(voter_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM voters
        WHERE voter_id = ?
    """, (voter_id,))

    voter = cursor.fetchone()

    conn.close()

    return voter


# =====================================================
# CHECK ALREADY VOTED
# =====================================================

def has_voted(voter_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM votes
        WHERE voter_id = ?
    """, (voter_id,))

    result = cursor.fetchone()

    conn.close()

    return result is not None


# =====================================================
# SAVE VOTE
# =====================================================

def save_vote(
    election_id,
    voter_id,
    candidate_id,
    candidate_name,
    face_data
):

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        # -------------------------------------------------
        # DUPLICATE VOTE
        # -------------------------------------------------

        cursor.execute("""
            SELECT id
            FROM votes
            WHERE voter_id = ?
        """, (voter_id,))

        if cursor.fetchone():

            return (
                False,
                "This Voter ID has already voted."
            )

        # -------------------------------------------------
        # VERIFY CANDIDATE
        # -------------------------------------------------

        cursor.execute("""
            SELECT id
            FROM candidates
            WHERE id = ?
              AND election_id = ?
        """, (
            candidate_id,
            election_id
        ))

        if not cursor.fetchone():

            return (
                False,
                "Invalid candidate."
            )

        # -------------------------------------------------
        # REGISTER VOTER
        # -------------------------------------------------

        cursor.execute("""
            INSERT OR IGNORE INTO voters
            (
                voter_id,
                has_voted
            )
            VALUES (?, 0)
        """, (voter_id,))

        # -------------------------------------------------
        # TIMESTAMP
        # -------------------------------------------------

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # -------------------------------------------------
        # SAVE VOTE
        # -------------------------------------------------

        cursor.execute("""
            INSERT INTO votes
            (
                election_id,
                voter_id,
                candidate_id,
                candidate_name,
                face_data,
                timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            election_id,
            voter_id,
            candidate_id,
            candidate_name,
            face_data,
            timestamp
        ))

        # -------------------------------------------------
        # MARK VOTER
        # -------------------------------------------------

        cursor.execute("""
            UPDATE voters
            SET has_voted = 1
            WHERE voter_id = ?
        """, (voter_id,))

        conn.commit()

        return (
            True,
            "Vote successfully cast!"
        )

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

def get_total_votes(election_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM votes
        WHERE election_id = ?
    """, (election_id,))

    total = cursor.fetchone()[0]

    conn.close()

    return total


# =====================================================
# VOTE COUNTS
# =====================================================

def get_vote_counts(election_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            candidate_id,
            candidate_name,
            COUNT(*) AS total
        FROM votes
        WHERE election_id = ?
        GROUP BY candidate_id, candidate_name
    """, (election_id,))

    rows = cursor.fetchall()

    conn.close()

    return {
        row["candidate_id"]: row["total"]
        for row in rows
    }


# =====================================================
# ALL CURRENT VOTES
# =====================================================

def get_all_votes(election_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            votes.id,
            votes.voter_id,
            votes.candidate_id,
            votes.candidate_name,
            candidates.party,
            candidates.symbol,
            votes.face_data,
            votes.timestamp
        FROM votes
        LEFT JOIN candidates
            ON votes.candidate_id = candidates.id
        WHERE votes.election_id = ?
        ORDER BY votes.id DESC
    """, (election_id,))

    rows = cursor.fetchall()

    conn.close()

    return rows


# =====================================================
# COMPLETE ELECTION RESET / DECLARE RESULT
# =====================================================

def conclude_election(election_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        # -------------------------------------------------
        # ELECTION
        # -------------------------------------------------

        cursor.execute("""
            SELECT election_name
            FROM elections
            WHERE id = ?
        """, (election_id,))

        election = cursor.fetchone()

        if not election:

            return False, "Election not found."

        election_name = election["election_name"]

        # -------------------------------------------------
        # TOTAL
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM votes
            WHERE election_id = ?
        """, (election_id,))

        total_votes = cursor.fetchone()[0]

        # -------------------------------------------------
        # RESULT
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                candidate_name,
                COUNT(*) AS total
            FROM votes
            WHERE election_id = ?
            GROUP BY candidate_id, candidate_name
            ORDER BY total DESC
        """, (election_id,))

        result_rows = cursor.fetchall()

        if result_rows:

            highest = result_rows[0]["total"]

            leaders = [
                row["candidate_name"]
                for row in result_rows
                if row["total"] == highest
            ]

            if len(leaders) == 1:
                winner_name = leaders[0]
            else:
                winner_name = (
                    "Tie: " +
                    ", ".join(leaders)
                )

        else:

            winner_name = "No Votes Cast"

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # -------------------------------------------------
        # SAVE ELECTION HISTORY
        # -------------------------------------------------

        cursor.execute("""
            INSERT INTO election_history
            (
                election_id,
                election_name,
                winner_name,
                total_votes,
                timestamp
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            election_id,
            election_name,
            winner_name,
            total_votes,
            timestamp
        ))

        # -------------------------------------------------
        # ARCHIVE VOTES
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                votes.voter_id,
                votes.candidate_name,
                candidates.party,
                candidates.symbol,
                votes.face_data,
                votes.timestamp
            FROM votes
            LEFT JOIN candidates
                ON votes.candidate_id = candidates.id
            WHERE votes.election_id = ?
        """, (election_id,))

        old_votes = cursor.fetchall()

        for vote in old_votes:

            cursor.execute("""
                INSERT INTO votes_history
                (
                    election_id,
                    election_name,
                    voter_id,
                    candidate_name,
                    party,
                    symbol,
                    face_data,
                    timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                election_id,
                election_name,
                vote["voter_id"],
                vote["candidate_name"],
                vote["party"],
                vote["symbol"],
                vote["face_data"],
                vote["timestamp"]
            ))

        # -------------------------------------------------
        # DELETE CURRENT VOTES
        # -------------------------------------------------

        cursor.execute("""
            DELETE FROM votes
            WHERE election_id = ?
        """, (election_id,))

        # -------------------------------------------------
        # RESET VOTERS
        # -------------------------------------------------

        cursor.execute("""
            UPDATE voters
            SET has_voted = 0
        """)

        # -------------------------------------------------
        # COMPLETE OLD ELECTION
        # -------------------------------------------------

        cursor.execute("""
            UPDATE elections
            SET status = 'COMPLETED'
            WHERE id = ?
        """, (election_id,))

        # -------------------------------------------------
        # CREATE NEW ELECTION
        # -------------------------------------------------

        new_type = election_name

        if "RAJYA SABHA" in new_type:
            new_type = "RAJYA SABHA ELECTION"

        elif "LOK SABHA" in new_type:
            new_type = "LOK SABHA ELECTION"

        elif "GRAM PANCHAYAT" in new_type:
            new_type = "GRAM PANCHAYAT ELECTION"

        else:
            new_type = "LOK SABHA ELECTION"

        new_year = datetime.now().year

        new_name = f"{new_type} {new_year}"

        cursor.execute("""
            INSERT INTO elections
            (
                election_type,
                election_name,
                status,
                created_at
            )
            VALUES (?, ?, 'ACTIVE', ?)
        """, (
            new_type,
            new_name,
            timestamp
        ))

        new_election_id = cursor.lastrowid

        conn.commit()

        return True, {
            "winner": winner_name,
            "total_votes": total_votes,
            "new_election_id": new_election_id
        }

    except Exception as error:

        conn.rollback()

        return False, str(error)

    finally:

        conn.close()


# =====================================================
# ELECTION HISTORY
# =====================================================

def get_election_history():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM election_history
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    init_db()

    print("Database ready.")