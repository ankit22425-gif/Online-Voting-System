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
    ELECTION_TYPES,
    ELECTION_SYMBOLS,
    get_active_election,
    create_election,
    add_candidate,
    get_candidates,
    delete_candidate,
    save_vote,
    get_total_votes,
    get_vote_counts,
    get_all_votes,
    conclude_election
)


# =====================================================
# APP
# =====================================================

app = Flask(__name__)

app.secret_key = "super_secret_key_2026"

init_db()


# =====================================================
# PATHS
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
# ADMIN LOGIN
# =====================================================

ADMIN_ID = "admin2026"
ADMIN_PASSWORD = "Vote@2026"


# =====================================================
# NO CACHE
# =====================================================

@app.after_request
def no_cache(response):

    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, "
        "max-age=0"
    )

    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


# =====================================================
# HOME
# =====================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =====================================================
# ADMIN LOGIN
# =====================================================

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

    election = get_active_election()

    candidates = []
    results = []

    total_votes = 0
    voters_list = []

    winner = None
    max_votes = 0
    leader_count = 0

    # -------------------------------------------------
    # ACTIVE ELECTION
    # -------------------------------------------------

    if election:

        election_id = election["id"]

        candidates = get_candidates(
            election_id
        )

        vote_counts = get_vote_counts(
            election_id
        )

        total_votes = get_total_votes(
            election_id
        )

        voters_list = get_all_votes(
            election_id
        )

        # ---------------------------------------------
        # RESULT DATA
        # ---------------------------------------------

        for candidate in candidates:

            votes = vote_counts.get(
                candidate["id"],
                0
            )

            if total_votes > 0:

                percentage = round(
                    (votes / total_votes) * 100,
                    1
                )

            else:

                percentage = 0

            results.append({

                "id": candidate["id"],

                "name": candidate["name"],

                "party": candidate["party"],

                "symbol": candidate["symbol"],

                "votes": votes,

                "percentage": percentage

            })

        # ---------------------------------------------
        # FIND LEADER
        # ---------------------------------------------

        if results and total_votes > 0:

            max_votes = max(
                item["votes"]
                for item in results
            )

            leaders = [
                item
                for item in results
                if item["votes"] == max_votes
            ]

            leader_count = len(
                leaders
            )

            # Winner only if single leader
            if leader_count == 1:

                winner = leaders[0]["name"]

    # =================================================
    # ELECTION HISTORY
    # =================================================

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            election_id,
            election_name,
            winner_name,
            total_votes,
            timestamp
        FROM election_history
        ORDER BY id DESC
    """)

    past_elections = cursor.fetchall()

    conn.close()

    # =================================================
    # RENDER
    # =================================================

    return render_template(

        "admin.html",

        election=election,

        election_types=ELECTION_TYPES,

        symbols=ELECTION_SYMBOLS,

        candidates=candidates,

        results=results,

        total_votes=total_votes,

        voters_list=voters_list,

        winner=winner,

        max_votes=max_votes,

        leader_count=leader_count,

        past_elections=past_elections
    )


# =====================================================
# CREATE / SELECT ELECTION
# =====================================================

@app.route(
    "/create_election",
    methods=["POST"]
)
def create_new_election():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )

    election_type = request.form.get(
        "election_type",
        ""
    ).strip()

    if not election_type:

        flash(
            "Please select an election.",
            "danger"
        )

        return redirect(
            url_for("admin")
        )

    success, result = create_election(
        election_type
    )

    if not success:

        flash(
            result,
            "danger"
        )

        return redirect(
            url_for("admin")
        )

    flash(
        "New election selected successfully.",
        "success"
    )

    return redirect(
        url_for("admin")
    )


# =====================================================
# ADD CANDIDATE
# =====================================================

@app.route(
    "/add_candidate",
    methods=["POST"]
)
def add_new_candidate():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )

    election = get_active_election()

    if not election:

        flash(
            "Please select an election first.",
            "danger"
        )

        return redirect(
            url_for("admin")
        )

    name = request.form.get(
        "candidate_name",
        ""
    ).strip()

    party = request.form.get(
        "party_name",
        ""
    ).strip()

    symbol = request.form.get(
        "symbol",
        ""
    ).strip()

    if not name or not party or not symbol:

        flash(
            "Please fill all candidate details.",
            "danger"
        )

        return redirect(
            url_for("admin")
        )

    success, message = add_candidate(

        election["id"],

        name,

        party,

        symbol
    )

    flash(
        message,
        "success" if success else "danger"
    )

    return redirect(
        url_for("admin")
    )


# =====================================================
# DELETE CANDIDATE
# =====================================================

@app.route(
    "/delete_candidate/<int:candidate_id>",
    methods=["POST"]
)
def remove_candidate(candidate_id):

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )

    success = delete_candidate(
        candidate_id
    )

    if success:

        flash(
            "Candidate removed.",
            "success"
        )

    else:

        flash(
            "Unable to remove candidate.",
            "danger"
        )

    return redirect(
        url_for("admin")
    )


# =====================================================
# VOTER LOGIN
# =====================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    election = get_active_election()

    if not election:

        flash(
            "No election is currently active.",
            "danger"
        )

        return redirect(
            url_for("home")
        )

    if request.method == "POST":

        voter_id = request.form.get(
            "voter_id",
            ""
        ).strip()

        # ---------------------------------------------
        # ALPHANUMERIC / STRING
        # ---------------------------------------------

        if not voter_id:

            flash(
                "Please enter Voter ID.",
                "danger"
            )

            return render_template(
                "login.html",
                election=election
            )

        # ---------------------------------------------
        # DUPLICATE VOTE CHECK
        # ---------------------------------------------

        conn = sqlite3.connect(DB_NAME)

        cursor = conn.cursor()

        cursor.execute("""
            SELECT id
            FROM votes
            WHERE voter_id = ?
              AND election_id = ?
        """, (
            voter_id,
            election["id"]
        ))

        already_voted = cursor.fetchone()

        conn.close()

        if already_voted:

            flash(
                "This Voter ID has already voted.",
                "danger"
            )

            return render_template(
                "login.html",
                election=election
            )

        session["voter"] = voter_id

        return redirect(
            url_for("vote")
        )

    return render_template(
        "login.html",
        election=election
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

    election = get_active_election()

    if not election:

        session.pop(
            "voter",
            None
        )

        flash(
            "No active election.",
            "danger"
        )

        return redirect(
            url_for("home")
        )

    candidates = get_candidates(
        election["id"]
    )

    if not candidates:

        flash(
            "Candidates have not been nominated yet.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    return render_template(

        "vote.html",

        election=election,

        candidates=candidates,

        voter=session["voter"]
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

        header, encoded_data = (
            live_image.split(",", 1)
        )

        if "image/jpeg" in header:

            extension = ".jpg"

        elif "image/png" in header:

            extension = ".png"

        else:

            return None

        image_bytes = base64.b64decode(
            encoded_data
        )

        if len(image_bytes) > 5 * 1024 * 1024:

            return None

        safe_voter = "".join(
            c
            for c in voter_id
            if c.isalnum()
        )

        if not safe_voter:

            safe_voter = "voter"

        filename = (

            f"{safe_voter}_"

            f"{datetime.now().strftime('%Y%m%d%H%M%S')}_"

            f"{uuid.uuid4().hex[:8]}"

            f"{extension}"

        )

        path = os.path.join(
            CAPTURE_FOLDER,
            filename
        )

        with open(
            path,
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

    if "voter" not in session:

        return redirect(
            url_for("login")
        )

    election = get_active_election()

    if not election:

        flash(
            "No active election.",
            "danger"
        )

        return redirect(
            url_for("home")
        )

    voter_id = session["voter"]

    candidate_id = request.form.get(
        "candidate_id",
        ""
    )

    live_image = request.form.get(
        "live_image",
        ""
    )

    # ---------------------------------------------
    # VALIDATE CANDIDATE ID
    # ---------------------------------------------

    try:

        candidate_id = int(
            candidate_id
        )

    except (ValueError, TypeError):

        flash(
            "Invalid candidate.",
            "danger"
        )

        return redirect(
            url_for("vote")
        )

    # ---------------------------------------------
    # GET CANDIDATE
    # ---------------------------------------------

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            name
        FROM candidates
        WHERE id = ?
          AND election_id = ?
    """, (
        candidate_id,
        election["id"]
    ))

    candidate = cursor.fetchone()

    conn.close()

    if not candidate:

        flash(
            "Invalid candidate.",
            "danger"
        )

        return redirect(
            url_for("vote")
        )

    # ---------------------------------------------
    # PHOTO
    # ---------------------------------------------

    photo_path = None

    if live_image:

        photo_path = save_live_photo(
            voter_id,
            live_image
        )

    # ---------------------------------------------
    # SAVE VOTE
    # ---------------------------------------------

    success, message = save_vote(

        election["id"],

        voter_id,

        candidate_id,

        candidate[1],

        photo_path
    )

    if not success:

        flash(
            message,
            "danger"
        )

        return redirect(
            url_for("vote")
        )

    session.pop(
        "voter",
        None
    )

    return render_template(
        "success.html"
    )


# =====================================================
# DECLARE RESULT
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

    election = get_active_election()

    if not election:

        flash(
            "No active election found.",
            "danger"
        )

        return redirect(
            url_for("admin")
        )

    election_id = election["id"]

    print(
        "======================================"
    )

    print(
        "DECLARE RESULT"
    )

    print(
        "Election:",
        election["election_name"]
    )

    print(
        "Election ID:",
        election_id
    )

    print(
        "======================================"
    )

    # =================================================
    # GET CURRENT RESULT BEFORE CONCLUDING
    # =================================================

    candidates = get_candidates(
        election_id
    )

    vote_counts = get_vote_counts(
        election_id
    )

    total_votes = get_total_votes(
        election_id
    )

    result_list = []

    for candidate in candidates:

        votes = vote_counts.get(
            candidate["id"],
            0
        )

        result_list.append({

            "id": candidate["id"],

            "name": candidate["name"],

            "party": candidate["party"],

            "symbol": candidate["symbol"],

            "votes": votes

        })

    # =================================================
    # FIND WINNER / TIE
    # =================================================

    winner = None

    winner_symbol = None

    winner_party = None

    is_tie = False

    max_votes = 0

    if result_list and total_votes > 0:

        max_votes = max(
            item["votes"]
            for item in result_list
        )

        leaders = [
            item
            for item in result_list
            if item["votes"] == max_votes
        ]

        if len(leaders) == 1:

            winner = leaders[0]["name"]

            winner_symbol = leaders[0]["symbol"]

            winner_party = leaders[0]["party"]

        else:

            is_tie = True

    # =================================================
    # CONCLUDE ELECTION
    # =================================================

    success, result = conclude_election(
        election_id
    )

    if not success:

        flash(
            f"Reset error: {result}",
            "danger"
        )

        return redirect(
            url_for("admin")
        )

    # =================================================
    # CELEBRATION DATA
    # =================================================

    if is_tie:

        celebration_title = "CURRENTLY TIED"

        celebration_message = (
            "No single winner can be declared."
        )

    elif winner:

        celebration_title = (
            f"CONGRATULATIONS!"
        )

        celebration_message = (
            f"Mr. {winner}"
        )

    else:

        celebration_title = (
            "ELECTION CONCLUDED"
        )

        celebration_message = (
            "No votes were cast."
        )

    # =================================================
    # STORE CELEBRATION DATA IN SESSION
    # =================================================

    session["celebration"] = {

        "title":
            celebration_title,

        "message":
            celebration_message,

        "winner":
            winner,

        "winner_symbol":
            winner_symbol,

        "winner_party":
            winner_party,

        "votes":
            max_votes,

        "total_votes":
            total_votes,

        "is_tie":
            is_tie

    }

    # =================================================
    # GO TO CELEBRATION SCREEN
    # =================================================

    return redirect(
        url_for("result_celebration")
    )


# =====================================================
# RESULT CELEBRATION
# =====================================================

@app.route(
    "/result-celebration"
)
def result_celebration():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )

    celebration = session.pop(
        "celebration",
        None
    )

    if not celebration:

        return redirect(
            url_for("admin")
        )

    return render_template(

        "result_celebration.html",

        result=celebration
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

    conn = sqlite3.connect(
        DB_NAME
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
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
# RUN
# =====================================================

if __name__ == "__main__":

    print("")
    print(
        "======================================"
    )

    print(
        "       ONLINE VOTING SYSTEM"
    )

    print(
        "======================================"
    )

    print(
        "DATABASE:",
        os.path.abspath(DB_NAME)
    )

    print(
        "ADMIN ID:",
        ADMIN_ID
    )

    print(
        "ADMIN PASSWORD:",
        ADMIN_PASSWORD
    )

    print(
        "======================================"
    )

    app.run(

        debug=True,

        host="127.0.0.1",

        port=5000

    )