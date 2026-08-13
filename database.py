import sqlite3

# Database Connection
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# =========================
# ADMIN TABLE
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS admin (
    admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
""")

# =========================
# VOTERS TABLE
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS voters (
    voter_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    mobile TEXT NOT NULL,
    age INTEGER NOT NULL,
    password TEXT NOT NULL,
    has_voted INTEGER DEFAULT 0
)
""")

# =========================
# CANDIDATES TABLE
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS candidates (
    candidate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_name TEXT NOT NULL,
    party_name TEXT NOT NULL,
    votes INTEGER DEFAULT 0
)
""")

# =========================
# VOTE HISTORY TABLE
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS vote_history (
    vote_id INTEGER PRIMARY KEY AUTOINCREMENT,
    voter_id INTEGER NOT NULL,
    candidate_id INTEGER NOT NULL,
    vote_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (voter_id) REFERENCES voters(voter_id),
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id)
)
""")

# =========================
# DEFAULT ADMIN
# =========================
cursor.execute("""
INSERT OR IGNORE INTO admin (username, password)
VALUES ('admin', 'admin123')
""")

# =========================
# DEFAULT CANDIDATES
# =========================
candidates = [
    ("Rahul Singh", "ljp Party"),
    ("Chirag Paswan", "BJP Party"),
    ("Kangna Rawat", "RSS Party"),
    ("Akhilesh Yadav", "Samajwadi Party"),
    ("Siya", "Other Party")
]

cursor.executemany("""
INSERT OR IGNORE INTO candidates (candidate_name, party_name)
VALUES (?, ?)
""", candidates)

# Save Changes
conn.commit()

print("==============================")
print("Online Voting Database Created")
print("==============================")
print("Tables Created Successfully")
print("Admin Username : admin")
print("Admin Password : admin123")
print("Database Name  : database.db")

# Close Connection
conn.close()