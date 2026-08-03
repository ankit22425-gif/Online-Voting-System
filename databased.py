import sqlite3

# Database Connection
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# ==========================
# Admin Table
# ==========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS admin (
    admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
""")

# ==========================
# Voters Table
# ==========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS voters (
    voter_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    mobile TEXT UNIQUE NOT NULL,
    age INTEGER NOT NULL,
    password TEXT NOT NULL,
    has_voted INTEGER DEFAULT 0
)
""")

# ==========================
# Candidates Table
# ==========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS candidates (
    candidate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_name TEXT NOT NULL,
    party_name TEXT NOT NULL,
    votes INTEGER DEFAULT 0
)
""")

# ==========================
# Vote History Table
# ==========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS vote_history (
    vote_id INTEGER PRIMARY KEY AUTOINCREMENT,
    voter_id INTEGER,
    candidate_id INTEGER,
    vote_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(voter_id) REFERENCES voters(voter_id),
    FOREIGN KEY(candidate_id) REFERENCES candidates(candidate_id)
)
""")

# ==========================
# Default Admin
# ==========================
cursor.execute("""
INSERT OR IGNORE INTO admin(username,password)
VALUES('admin','admin123')
""")

# ==========================
# Default Candidates
# ==========================
cursor.execute("""
INSERT OR IGNORE INTO candidates(candidate_name,party_name)
VALUES
('Rahul Singh','ABC Party')
""")

cursor.execute("""
INSERT OR IGNORE INTO candidates(candidate_name,party_name)
VALUES
('Priya Sharma','XYZ Party')
""")

cursor.execute("""
INSERT OR IGNORE INTO candidates(candidate_name,party_name)
VALUES
('Aman Verma','PQR Party')
""")
# ==========================
# Vote History Table
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS vote_history(
    vote_id INTEGER PRIMARY KEY AUTOINCREMENT,
    voter_id INTEGER NOT NULL,
    candidate_id INTEGER NOT NULL,
    vote_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(voter_id) REFERENCES voters(voter_id),
    FOREIGN KEY(candidate_id) REFERENCES candidates(candidate_id)
)
""")

# Save Changes
conn.commit()

print("===================================")
print(" Online Voting Database Created ")
print("===================================")
print("Tables Created Successfully")
print("Admin Username : admin")
print("Admin Password : admin123")
print("Database Name  : database.db")

# Close Connection
conn.close()