def create_user_table(connection):
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id TEXT NOT NULL UNIQUE,

            name TEXT NOT NULL,
            username TEXT UNIQUE,

            email TEXT NOT NULL UNIQUE,
            phone_number TEXT UNIQUE,

            password_hash TEXT NOT NULL,

            profile_image TEXT,

            date_of_birth TEXT,
            gender TEXT,

            is_email_verified INTEGER NOT NULL DEFAULT 0,
            is_phone_verified INTEGER NOT NULL DEFAULT 0,

            account_status TEXT NOT NULL DEFAULT 'active'
                CHECK (
                    account_status IN (
                        'active',
                        'inactive',
                        'blocked',
                        'suspended',
                        'deleted'
                    )
                ),

            is_admin INTEGER NOT NULL DEFAULT 0,
            is_seller INTEGER NOT NULL DEFAULT 0,

            login_attempts INTEGER NOT NULL DEFAULT 0,
            last_login_at TEXT,
            last_login_ip TEXT,

            password_changed_at TEXT,

            email_verification_token TEXT,
            email_verification_expiry TEXT,

            phone_verification_code TEXT,
            phone_verification_expiry TEXT,

            password_reset_token TEXT,
            password_reset_expiry TEXT,

            two_factor_enabled INTEGER NOT NULL DEFAULT 0,

            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,

            deleted_at TEXT
        )
    """)

    # Fast lookup indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_user_id
        ON users(user_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_email
        ON users(email)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_phone
        ON users(phone_number)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_username
        ON users(username)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_status
        ON users(account_status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_created_at
        ON users(created_at)
    """)

    connection.commit()

