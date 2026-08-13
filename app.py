from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super_secret_key"

# Rajya Sabha Candidates List
CANDIDATES = [
    {"id": 1, "name": "Rahul Singh", "party": "BJP Party", "symbol": "🌸"},
    {"id": 2, "name": "Chirag Paswan", "party": "RSS Party", "symbol": "🚩"},
    {"id": 3, "name": "Akhilesh Yadav", "party": "Samajwadi Party", "symbol": "🚲"},
    {"id": 4, "name": "Siya", "party": "Other Party", "symbol": "✋"}
]

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Current Active Votes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voter_id TEXT UNIQUE NOT NULL,
            candidate_name TEXT NOT NULL,
            face_data TEXT
        )
    ''')
    # Archived History Tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS election_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            election_id INTEGER,
            winner_name TEXT,
            total_votes INTEGER,
            timestamp TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            election_id INTEGER,
            voter_id TEXT,
            candidate_name TEXT,
            face_data TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        voter_id = request.form.get("voter_id", "").strip()
        if voter_id:
            session["voter"] = voter_id
            return redirect(url_for("vote"))
    return render_template("login.html")

@app.route("/vote")
def vote():
    if "voter" not in session:
        return redirect(url_for("login"))
    
    voter_id = session["voter"]
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT candidate_name FROM votes WHERE voter_id = ?", (voter_id,))
    already_voted = cursor.fetchone()
    conn.close()

    return render_template("vote.html", candidates=CANDIDATES, voter=voter_id, already_voted=already_voted)

@app.route("/cast_vote", methods=["POST"])
def cast_vote():
    if "voter" not in session:
        return redirect(url_for("login"))

    voter_id = session["voter"]
    candidate_name = request.form.get("candidate_name")
    live_image = request.form.get("live_image")

    if not live_image:
        flash("Error: Live face verification required! Camera allow karein.", "danger")
        return redirect(url_for("vote"))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO votes (voter_id, candidate_name, face_data) VALUES (?, ?, ?)", 
                       (voter_id, candidate_name, live_image))
        conn.commit()
        
        # Session clear karo taaki purana login yahan khatam ho jaye
        session.clear()
        
        return render_template("success.html")
    except sqlite3.IntegrityError:
        # Session clear karo agar duplicate vote ki koshish hui ho
        session.clear()
        flash("Error: Is Voter ID se pehle hi vote cast kiya ja chuka hai! Please Naye ID se Login karein.", "danger")
        return redirect(url_for("login"))
    finally:
        conn.close()
@app.route("/admin")
def admin():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT candidate_name, COUNT(*) FROM votes GROUP BY candidate_name")
    vote_counts = dict(cursor.fetchall())
    
    cursor.execute("SELECT COUNT(*) FROM votes")
    total_votes = cursor.fetchone()[0]
    
    cursor.execute("SELECT voter_id, candidate_name, id FROM votes ORDER BY id DESC")
    voters_list = cursor.fetchall()

    # Fetch Past Elections History
    cursor.execute("SELECT id, winner_name, total_votes, timestamp FROM election_history ORDER BY id DESC")
    past_elections = cursor.fetchall()

    conn.close()

    results = []
    winner = None
    max_votes = -1

    for c in CANDIDATES:
        count = vote_counts.get(c["name"], 0)
        percentage = round((count / total_votes * 100), 1) if total_votes > 0 else 0
        results.append({
            "name": c["name"],
            "party": c["party"],
            "symbol": c["symbol"],
            "votes": count,
            "percentage": percentage
        })
        if count > max_votes and count > 0:
            max_votes = count
            winner = c["name"]

    return render_template("admin.html", 
                           results=results, 
                           total_votes=total_votes, 
                           voters_list=voters_list, 
                           winner=winner,
                           past_elections=past_elections)

@app.route("/reset_election", methods=["POST"])
def reset_election():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Total votes & Winner check
    cursor.execute("SELECT candidate_name, COUNT(*) as cnt FROM votes GROUP BY candidate_name ORDER BY cnt DESC LIMIT 1")
    winner_row = cursor.fetchone()
    winner_name = winner_row[0] if winner_row else "No Votes Cast"

    cursor.execute("SELECT COUNT(*) FROM votes")
    total_votes = cursor.fetchone()[0]

    # Insert into Election History
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO election_history (winner_name, total_votes, timestamp) VALUES (?, ?, ?)",
                   (winner_name, total_votes, timestamp))
    election_id = cursor.lastrowid

    # Archive all votes into votes_history
    cursor.execute("INSERT INTO votes_history (election_id, voter_id, candidate_name, face_data) SELECT ?, voter_id, candidate_name, face_data FROM votes", (election_id,))

    # Clear current votes table for Next Election
    cursor.execute("DELETE FROM votes")

    conn.commit()
    conn.close()

    flash(f"Success: Election Concluded! Winner: {winner_name}. Purana record history me bhej diya gaya hai aur naya election shuru ho chuka hai.", "success")
    return redirect(url_for("admin"))

@app.route("/logout")
def logout():
    session.pop("voter", None)
    return redirect(url_for("home"))
@app.route("/historical-archive")
def historical_archive():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Fetch Past Elections History
    cursor.execute("SELECT id, winner_name, total_votes, timestamp FROM election_history ORDER BY id DESC")
    past_elections = cursor.fetchall()
    
    conn.close()
    return render_template("historical_archive.html", past_elections=past_elections)

if __name__ == "__main__":
    app.run(debug=True)