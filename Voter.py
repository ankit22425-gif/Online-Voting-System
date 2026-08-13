import sqlite3

DB_NAME = "database.db"


# ---------------- SHOW CANDIDATES ----------------
def show_candidates():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM candidates")
    candidates = cursor.fetchall()

    conn.close()

    if not candidates:
        print("\nNo candidates found.")
        return

    print("\n----- Candidates -----")

    for candidate in candidates:
        print(
            f"ID: {candidate[0]} | "
            f"Name: {candidate[1]} | "
            f"Party: {candidate[2]}"
        )


# ---------------- CAST VOTE ----------------
def vote():
    voter_id = input("\nEnter your Voter ID: ").strip()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Check voter
    cursor.execute(
        "SELECT * FROM voters WHERE voter_id = ?",
        (voter_id,)
    )

    voter = cursor.fetchone()

    if not voter:
        print("\n❌ Voter not found!")
        conn.close()
        return

    print(f"\nWelcome, {voter[1]}!")

    # Check already voted
    cursor.execute(
        "SELECT * FROM votes WHERE voter_id = ?",
        (voter_id,)
    )

    if cursor.fetchone():
        print("\n⚠️ You have already voted!")
        conn.close()
        return

    # Show candidates
    cursor.execute("SELECT * FROM candidates")
    candidates = cursor.fetchall()

    if not candidates:
        print("\nNo candidates available.")
        conn.close()
        return

    print("\n----- Candidates -----")

    for candidate in candidates:
        print(
            f"ID: {candidate[0]} | "
            f"Name: {candidate[1]} | "
            f"Party: {candidate[2]}"
        )

    # Candidate selection
    try:
        candidate_id = int(input("\nEnter Candidate ID: "))
    except ValueError:
        print("\n❌ Please enter a valid number.")
        conn.close()
        return

    # Check candidate
    cursor.execute(
        "SELECT * FROM candidates WHERE id = ?",
        (candidate_id,)
    )

    candidate = cursor.fetchone()

    if not candidate:
        print("\n❌ Invalid Candidate ID!")
        conn.close()
        return

    # Confirm vote
    print("\nYou selected:")
    print("Candidate:", candidate[1])
    print("Party:", candidate[2])

    confirm = input("\nConfirm your vote? (yes/no): ").lower().strip()

    if confirm != "yes":
        print("\nVote cancelled.")
        conn.close()
        return

    # Insert vote
    cursor.execute(
        "INSERT INTO votes (voter_id, candidate_id) VALUES (?, ?)",
        (voter_id, candidate_id)
    )

    conn.commit()
    conn.close()

    print("\n✅ Vote submitted successfully!")


# ---------------- VOTE HISTORY ----------------
def vote_history():
    voter_id = input("\nEnter your Voter ID: ").strip()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Check voter
    cursor.execute(
        "SELECT * FROM voters WHERE voter_id = ?",
        (voter_id,)
    )

    voter = cursor.fetchone()

    if not voter:
        print("\n❌ Voter not found!")
        conn.close()
        return

    # Get voting history
    cursor.execute("""
        SELECT votes.voter_id,
               candidates.name,
               candidates.party
        FROM votes
        JOIN candidates
        ON votes.candidate_id = candidates.id
        WHERE votes.voter_id = ?
    """, (voter_id,))

    history = cursor.fetchone()

    conn.close()

    if not history:
        print("\nNo voting history found.")
        return

    print("\n======================")
    print("      VOTE HISTORY")
    print("======================")

    print("Voter ID :", history[0])
    print("Candidate:", history[1])
    print("Party    :", history[2])

    print("\n✅ You have already cast your vote.")


# ---------------- MAIN MENU ----------------
def main():

    while True:

        print("\n======================")
        print("      VOTER PANEL")
        print("======================")

        print("1. Show Candidates")
        print("2. Cast Vote")
        print("3. Vote History")
        print("4. Exit")

        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            show_candidates()

        elif choice == "2":
            vote()

        elif choice == "3":
            vote_history()

        elif choice == "4":
            print("\nThank you for using Voting System!")
            break

        else:
            print("\n❌ Invalid choice! Please try again.")


# ---------------- START PROGRAM ----------------
if __name__ == "__main__":
    main()