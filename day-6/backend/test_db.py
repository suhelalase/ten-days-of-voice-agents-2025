import sqlite3
import random
from datetime import datetime, timedelta


# ===========================================================
# 1. CREATE DATABASE + TABLES + INSERT RANDOM DATA
# ===========================================================

def create_fraud_database():
    conn = sqlite3.connect("fraud_bank.db")
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        account_number TEXT UNIQUE,
        mother_name TEXT,
        mother_fav_color TEXT
    );
    """)

    # Create transactions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        location TEXT,
        timestamp TEXT,
        is_flagged INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    """)

    # Sample user data
    users = [
        ("Rahul Kumar", "1234567890", "Sunita", "Blue"),
        ("Amit Verma", "2345678901", "Kavita", "Red"),
        ("Sneha Patil", "3456789012", "Meena", "Green"),
        ("Priya Sharma", "4567890123", "Lata", "Yellow"),
        ("Vivek Singh", "5678901234", "Rekha", "Purple")
    ]

    cursor.executemany("""
    INSERT OR IGNORE INTO users (name, account_number, mother_name, mother_fav_color)
    VALUES (?, ?, ?, ?)
    """, users)

    locations = [
        "Mumbai", "Delhi", "Bangalore", "Hyderabad",
        "Pune", "Chennai", "Kolkata", "Ahmedabad",
        "Jaipur", "Noida"
    ]

    # Add 5 random transactions per user
    for user_id in range(1, 6):
        for _ in range(5):
            amount = random.randint(800, 95000)
            location = random.choice(locations)

            days_ago = random.randint(1, 45)
            hours = random.randint(0, 23)
            minutes = random.randint(0, 59)

            time_obj = datetime.now() - timedelta(days=days_ago, hours=hours, minutes=minutes)
            timestamp = time_obj.strftime("%Y-%m-%d %H:%M:%S")

            is_flagged = random.choice([0, 0, 0, 1])  # 25% fraud

            cursor.execute("""
            INSERT INTO transactions (user_id, amount, location, timestamp, is_flagged)
            VALUES (?, ?, ?, ?, ?)
            """, (user_id, amount, location, timestamp, is_flagged))

    conn.commit()
    conn.close()
    print("✔ fraud_bank.db created with users + random transactions.")


# ===========================================================
# 2. VERIFY USER IDENTITY (Mother Name + Favorite Color)
# ===========================================================

def verify_user(account_number, mother_name, favorite_color):
    conn = sqlite3.connect("fraud_bank.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id
        FROM users
        WHERE account_number=? 
        AND lower(mother_name)=lower(?)
        AND lower(mother_fav_color)=lower(?)
    """, (account_number, mother_name, favorite_color))

    result = cursor.fetchone()
    conn.close()

    if result:
        return True, result[0]
    return False, None


# ===========================================================
# 3. FETCH FLAGGED TRANSACTIONS
# ===========================================================

def get_flagged_transactions(account_number):
    conn = sqlite3.connect("fraud_bank.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT t.amount, t.location, t.timestamp, t.is_flagged
        FROM transactions t
        JOIN users u ON u.user_id = t.user_id
        WHERE u.account_number = ? AND t.is_flagged = 1
    """, (account_number,))

    results = cursor.fetchall()
    conn.close()

    return results


# ===========================================================
# 4. MARK TRANSACTION AS FRAUD OR VALID
# ===========================================================

def update_transaction_status(transaction_id, fraud_status):
    conn = sqlite3.connect("fraud_bank.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE transactions
        SET is_flagged = ?
        WHERE id = ?
    """, (fraud_status, transaction_id))

    conn.commit()
    conn.close()

    return True


# ===========================================================
# 5. RUN THIS FILE DIRECTLY TO GENERATE DATABASE
# ===========================================================

if __name__ == "__main__":
    print("Creating fraud detection database...")
    create_fraud_database()
    print("✔ Database ready.")
