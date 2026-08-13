import sqlite3


# =========================
# ADMIN LOGIN
# =========================
def admin_login():

    print("\n==============================")
    print("       ADMIN LOGIN")
    print("==============================")

    username = input("Enter Username: ")
    password = input("Enter Password: ")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM admin WHERE username = ? AND password = ?",
        (username, password)
    )

    admin = cursor.fetchone()

    conn.close()

    if admin:
        print("\nLogin Successful!")
        return True
    else:
        print("\nInvalid Username or Password!")
        return False


# =========================
# ADMIN DASHBOARD
# =========================
def admin_dashboard():

    while True:

        print("\n================================")
        print("        ADMIN DASHBOARD")
        print("================================")

        print("1. Manage Candidates")
        print("2. View Voters")
        print("3. View Vote History")
        print("4. View Election Results")
        print("5. Logout")

        choice = input("\nEnter your choice: ")

        if choice == "1":
            print("\nManage Candidates Selected")

        elif choice == "2":
            print("\nView Voters Selected")

        elif choice == "3":
            print("\nView Vote History Selected")

        elif choice == "4":
            print("\nView Election Results Selected")

        elif choice == "5":
            print("\nAdmin Logged Out.")
            break

        else:
            print("\nInvalid Choice! Please try again.")


# =========================
# MAIN PROGRAM
# =========================
if admin_login():
    admin_dashboard()