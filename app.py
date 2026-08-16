from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

import sqlite3
import os
import base64
import uuid
from datetime import datetime

from database import (
    DB_NAME,
    init_db,
    save_vote,
    get_total_votes,
    get_vote_counts,
    get_all_votes
)


# =====================================================
# FLASK APP
# =====================================================

app = Flask(__name__)

app.secret_key = "super_secret_key_2026"


# =====================================================
# INITIALIZE DATABASE
# =====================================================

init_db()


# =====================================================
# PHOTO FOLDER
# =====================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

CAPTURE_FOLDER = os.path.join(
    BASE_DIR,
    "static",
    "captures"
)

os.makedirs(
    CAPTURE_FOLDER,
    exist_ok=True
)


# =====================================================
# CANDIDATES
# =====================================================

CANDIDATES = [

    {
        "id": 1,
        "name": "Raman Singh",
        "party": "BJP Party",
        "symbol": "🌸"
    },

    {
        "id": 2,
        "name": "Anshu Paswan",
        "party": "RSS Party",
        "symbol": "🚩"
    },

    {
        "id": 3,
        "name": "Rama Yadav",
        "party": "Samajwadi Party",
        "symbol": "✂️"
    },

    {
        "id": 4,
        "name": "Sagar",
        "party": "Other Party",
        "symbol": "✊"
    }

]


# =====================================================
# HOME
# =====================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =====================================================
# LOGIN
# =====================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        voter_id = request.form.get(
            "voter_id",
            ""
        ).strip()

        # ---------------------------------------------
        # EMPTY ID
        # ---------------------------------------------

        if not voter_id:

            flash(
                "Please enter Voter ID.",
                "danger"
            )

            return render_template(
                "login.html"
            )

        # ---------------------------------------------
        # CHECK CURRENT VOTE
        # ---------------------------------------------

        conn = sqlite3.connect(DB_NAME)

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id
            FROM votes
            WHERE voter_id = ?
            """,
            (voter_id,)
        )

        already_voted = cursor.fetchone()

        conn.close()

        if already_voted:

            flash(
                "Is Voter ID se already vote cast ho chuka hai!",
                "danger"
            )

            return render_template(
                "login.html"
            )

        # ---------------------------------------------
        # ACCEPT ANY VOTER ID
        # ---------------------------------------------

        session["voter"] = voter_id

        return redirect(
            url_for("vote")
        )

    return render_template(
        "login.html"
    )


# =====================================================
# VOTE PAGE
# =====================================================

@app.route("/vote")
def vote():

    if "voter" not in session:

        return redirect(
            url_for("login")
        )

    voter_id = session["voter"]

    # ---------------------------------------------
    # DUPLICATE CHECK
    # ---------------------------------------------

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM votes
        WHERE voter_id = ?
        """,
        (voter_id,)
    )

    already_voted = cursor.fetchone()

    conn.close()

    if already_voted:

        session.pop(
            "voter",
            None
        )

        flash(
            "Aap already vote kar chuke hain.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "vote.html",
        candidates=CANDIDATES,
        voter=voter_id
    )


# =====================================================
# SAVE LIVE PHOTO
# =====================================================

def save_live_photo(
    voter_id,
    live_image
):

    try:

        if not live_image:
            return None

        if "," not in live_image:
            return None

        header, encoded_data = live_image.split(
            ",",
            1
        )

        # ---------------------------------------------
        # IMAGE TYPE
        # ---------------------------------------------

        if "image/jpeg" in header:

            extension = ".jpg"

        elif "image/png" in header:

            extension = ".png"

        else:

            return None

        # ---------------------------------------------
        # DECODE
        # ---------------------------------------------

        image_bytes = base64.b64decode(
            encoded_data
        )

        # ---------------------------------------------
        # SIZE LIMIT
        # ---------------------------------------------

        if len(image_bytes) > 5 * 1024 * 1024:

            return None

        # ---------------------------------------------
        # SAFE VOTER ID
        # ---------------------------------------------

        safe_voter = "".join(
            c
            for c in voter_id
            if c.isalnum()
        )

        if not safe_voter:

            safe_voter = "voter"

        # ---------------------------------------------
        # FILE NAME
        # ---------------------------------------------

        filename = (
            f"{safe_voter}_"
            f"{datetime.now().strftime('%Y%m%d%H%M%S')}_"
            f"{uuid.uuid4().hex[:8]}"
            f"{extension}"
        )

        file_path = os.path.join(
            CAPTURE_FOLDER,
            filename
        )

        # ---------------------------------------------
        # SAVE
        # ---------------------------------------------

        with open(
            file_path,
            "wb"
        ) as file:

            file.write(
                image_bytes
            )

        return os.path.join(
            "static",
            "captures",
            filename
        ).replace(
            "\\",
            "/"
        )

    except Exception as error:

        print(
            "PHOTO ERROR:",
            error
        )

        return None


# =====================================================
# CAST VOTE
# =====================================================

@app.route(
    "/cast_vote",
    methods=["POST"]
)
def cast_vote():

    # ---------------------------------------------
    # LOGIN CHECK
    # ---------------------------------------------

    if "voter" not in session:

        flash(
            "Please login first.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    voter_id = session["voter"]

    # ---------------------------------------------
    # FORM DATA
    # ---------------------------------------------

    candidate_name = request.form.get(
        "candidate_name",
        ""
    ).strip()

    live_image = request.form.get(
        "live_image",
        ""
    )

    print("VOTER ID:", voter_id)
    print("CANDIDATE:", candidate_name)
    print(
        "PHOTO RECEIVED:",
        bool(live_image)
    )

    # ---------------------------------------------
    # CANDIDATE VALIDATION
    # ---------------------------------------------

    valid_candidate = any(
        candidate["name"] == candidate_name
        for candidate in CANDIDATES
    )

    if not valid_candidate:

        flash(
            "Please select a candidate.",
            "danger"
        )

        return redirect(
            url_for("vote")
        )

    # ---------------------------------------------
    # PHOTO REQUIRED
    # ---------------------------------------------

    if not live_image:

        flash(
            "Please capture your live photo first.",
            "danger"
        )

        return redirect(
            url_for("vote")
        )

    # ---------------------------------------------
    # SAVE PHOTO
    # ---------------------------------------------

    photo_path = save_live_photo(
        voter_id,
        live_image
    )

    if not photo_path:

        flash(
            "Photo save nahi ho payi. Dobara capture karein.",
            "danger"
        )

        return redirect(
            url_for("vote")
        )

    # ---------------------------------------------
    # SAVE VOTE
    # ---------------------------------------------

    success, message = save_vote(
        voter_id,
        candidate_name,
        photo_path
    )

    if not success:

        print(
            "VOTE DATABASE ERROR:",
            message
        )

        flash(
            message,
            "danger"
        )

        return redirect(
            url_for("vote")
        )

    # ---------------------------------------------
    # CLEAR SESSION
    # ---------------------------------------------

    session.pop(
        "voter",
        None
    )

    print(
        "VOTE SAVED SUCCESSFULLY"
    )

    print(
        "TOTAL VOTES:",
        get_total_votes()
    )

    flash(
        "Vote successfully cast!",
        "success"
    )

    return render_template(
        "success.html"
    )


# =====================================================
# ADMIN LOGIN
# =====================================================

ADMIN_ID = "admin2026"

ADMIN_PASSWORD = "Vote@2026"


@app.route(
    "/admin-login",
    methods=["GET", "POST"]
)
def admin_login():

    if request.method == "POST":

        admin_id = request.form.get(
            "admin_id",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if (
            admin_id == ADMIN_ID
            and password == ADMIN_PASSWORD
        ):

            session["admin_logged_in"] = True

            return redirect(
                url_for("admin")
            )

        flash(
            "Invalid Admin ID or Password.",
            "danger"
        )

    return render_template(
        "admin_login.html"
    )


# =====================================================
# ADMIN DASHBOARD
# =====================================================

@app.route("/admin")
def admin():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )

    # ---------------------------------------------
    # CURRENT VOTES
    # ---------------------------------------------

    total_votes = get_total_votes()

    vote_counts = get_vote_counts()

    voters_list = get_all_votes()

    # ---------------------------------------------
    # HISTORY
    # ---------------------------------------------

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            winner_name,
            total_votes,
            timestamp
        FROM election_history
        ORDER BY id DESC
    """)

    past_elections = cursor.fetchall()

    conn.close()

    # ---------------------------------------------
    # RESULTS
    # ---------------------------------------------

    results = []

    winner = None

    max_votes = 0

    for candidate in CANDIDATES:

        count = vote_counts.get(
            candidate["name"],
            0
        )

        percentage = (

            round(
                count / total_votes * 100,
                1
            )

            if total_votes > 0

            else 0
        )

        results.append({

            "name":
                candidate["name"],

            "party":
                candidate["party"],

            "symbol":
                candidate["symbol"],

            "votes":
                count,

            "percentage":
                percentage

        })

        if count > max_votes:

            max_votes = count

            winner = candidate["name"]

    return render_template(
        "admin.html",
        results=results,
        total_votes=total_votes,
        voters_list=voters_list,
        winner=winner,
        past_elections=past_elections
    )


# =====================================================
# RESET / DECLARE RESULT
# =====================================================

@app.route(
    "/reset_election",
    methods=["POST"]
)
def reset_election():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    try:

        # ---------------------------------------------
        # WINNER
        # ---------------------------------------------

        cursor.execute("""
            SELECT
                candidate_name,
                COUNT(*) AS total
            FROM votes
            GROUP BY candidate_name
            ORDER BY total DESC
            LIMIT 1
        """)

        winner_row = cursor.fetchone()

        if winner_row:

            winner_name = winner_row[0]

        else:

            winner_name = "No Votes Cast"

        # ---------------------------------------------
        # TOTAL
        # ---------------------------------------------

        cursor.execute(
            "SELECT COUNT(*) FROM votes"
        )

        total_votes = cursor.fetchone()[0]

        # ---------------------------------------------
        # TIME
        # ---------------------------------------------

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # ---------------------------------------------
        # SAVE ELECTION HISTORY
        # ---------------------------------------------

        cursor.execute("""
            INSERT INTO election_history
            (
                winner_name,
                total_votes,
                timestamp
            )
            VALUES (?, ?, ?)
        """, (
            winner_name,
            total_votes,
            timestamp
        ))

        election_id = cursor.lastrowid

        # ---------------------------------------------
        # ARCHIVE VOTES
        # ---------------------------------------------

        cursor.execute("""
            SELECT
                voter_id,
                candidate_name,
                face_data,
                timestamp
            FROM votes
        """)

        old_votes = cursor.fetchall()

        for vote in old_votes:

            cursor.execute("""
                INSERT INTO votes_history
                (
                    election_id,
                    voter_id,
                    candidate_name,
                    face_data,
                    timestamp
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                election_id,
                vote[0],
                vote[1],
                vote[2],
                vote[3]
            ))

        # ---------------------------------------------
        # DELETE CURRENT VOTES
        # ---------------------------------------------

        cursor.execute(
            "DELETE FROM votes"
        )

        # ---------------------------------------------
        # RESET VOTERS
        # ---------------------------------------------

        cursor.execute("""
            UPDATE voters
            SET has_voted = 0
        """)

        conn.commit()

        flash(
            f"Election Concluded! Winner: {winner_name}. "
            f"Total Votes: {total_votes}. "
            "New election started.",
            "success"
        )

    except Exception as error:

        conn.rollback()

        print(
            "RESET ERROR:",
            error
        )

        flash(
            f"Reset error: {error}",
            "danger"
        )

    finally:

        conn.close()

    return redirect(
        url_for("admin")
    )


# =====================================================
# HISTORICAL ARCHIVE
# =====================================================

@app.route(
    "/historical-archive"
)
def historical_archive():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            winner_name,
            total_votes,
            timestamp
        FROM election_history
        ORDER BY id DESC
    """)

    past_elections = cursor.fetchall()

    conn.close()

    return render_template(
        "historical_archive.html",
        past_elections=past_elections
    )


# =====================================================
# LOGOUT
# =====================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# =====================================================
# RUN APPLICATION
# =====================================================

if __name__ == "__main__":

    print("")
    print("======================================")
    print("       ONLINE VOTING SYSTEM")
    print("======================================")
    print("DATABASE:", DB_NAME)
    print("ADMIN ID:", ADMIN_ID)
    print("ADMIN PASSWORD:", ADMIN_PASSWORD)
    print("======================================")

    app.run(
        debug=True
    )