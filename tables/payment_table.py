def create_payment_table(connection):
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            payment_id TEXT NOT NULL UNIQUE,

            order_id TEXT NOT NULL,

            user_id TEXT NOT NULL,

            transaction_id TEXT UNIQUE,

            gateway_order_id TEXT,

            gateway_payment_id TEXT,

            gateway_signature TEXT,

            idempotency_key TEXT UNIQUE,

            payment_gateway TEXT,

            payment_method TEXT NOT NULL DEFAULT 'cod'
                CHECK (
                    payment_method IN (
                        'cod',
                        'upi',
                        'card',
                        'net_banking',
                        'wallet',
                        'emi',
                        'other'
                    )
                ),

            payment_status TEXT NOT NULL DEFAULT 'pending'
                CHECK (
                    payment_status IN (
                        'pending',
                        'processing',
                        'authorized',
                        'captured',
                        'failed',
                        'cancelled',
                        'expired',
                        'refunded',
                        'partially_refunded'
                    )
                ),

            amount REAL NOT NULL DEFAULT 0,

            currency TEXT NOT NULL DEFAULT 'INR',

            gateway_fee REAL NOT NULL DEFAULT 0,

            tax_amount REAL NOT NULL DEFAULT 0,

            net_amount REAL NOT NULL DEFAULT 0,

            refund_amount REAL NOT NULL DEFAULT 0,

            refund_status TEXT NOT NULL DEFAULT 'none'
                CHECK (
                    refund_status IN (
                        'none',
                        'pending',
                        'processing',
                        'partial',
                        'completed',
                        'failed'
                    )
                ),

            refund_transaction_id TEXT,

            refunded_at TEXT,

            failure_code TEXT,

            failure_message TEXT,

            payment_attempts INTEGER NOT NULL DEFAULT 0,

            verification_status TEXT NOT NULL DEFAULT 'pending'
                CHECK (
                    verification_status IN (
                        'pending',
                        'verified',
                        'failed'
                    )
                ),

            verified_at TEXT,

            webhook_received INTEGER NOT NULL DEFAULT 0,

            webhook_event_id TEXT UNIQUE,

            webhook_received_at TEXT,

            payment_metadata TEXT,

            ip_address TEXT,

            user_agent TEXT,

            initiated_at TEXT NOT NULL,

            completed_at TEXT,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL,

            deleted_at TEXT,

            FOREIGN KEY (order_id)
                REFERENCES orders(order_id)
                ON DELETE RESTRICT
                ON UPDATE CASCADE,

            FOREIGN KEY (user_id)
                REFERENCES users(user_id)
                ON DELETE RESTRICT
                ON UPDATE CASCADE
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_payment_id
        ON payments(payment_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_order_id
        ON payments(order_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_user_id
        ON payments(user_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_transaction_id
        ON payments(transaction_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_gateway_order_id
        ON payments(gateway_order_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_gateway_payment_id
        ON payments(gateway_payment_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_gateway
        ON payments(payment_gateway)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_method
        ON payments(payment_method)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_status
        ON payments(payment_status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_refund_status
        ON payments(refund_status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_verification_status
        ON payments(verification_status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_webhook_event_id
        ON payments(webhook_event_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_created_at
        ON payments(created_at)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_updated_at
        ON payments(updated_at)
    """)

    connection.commit()

