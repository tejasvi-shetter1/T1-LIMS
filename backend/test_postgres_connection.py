# Create file: test_postgres_connection.py in backend folder
import psycopg2

# Test different password formats
test_passwords = [
    "Aimlsn@2025",      # Original password
    "Aimlsn%402025",    # URL encoded (single %)
    "Aimlsn%%402025",   # Double URL encoded
    "",                 # Empty password
    "postgres",         # Default
    "admin"             # Common default
]

for pwd in test_passwords:
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432", 
            database="postgres",  # Try default postgres database first
            user="postgres",
            password=pwd
        )
        print(f"✅ SUCCESS! Correct password is: '{pwd}'")
        conn.close()
        break
    except Exception as e:
        print(f"❌ Failed with password: '{pwd}' - {str(e)[:50]}")

print("\nIf none worked, try the pg_hba.conf fix below...")
