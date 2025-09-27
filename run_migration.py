#!/usr/bin/env python3
"""
Database migration runner for ATS
"""
from src.database.connection import get_database_url
from sqlalchemy import create_engine, text
import sys

def run_migration():
    try:
        engine = create_engine(get_database_url())
        with engine.connect() as conn:
            # Read and execute migration
            with open('src/database/migrations/002_add_cex_symbol_column.sql', 'r') as f:
                migration_sql = f.read()

            print('Running migration: Add cex_symbol column...')
            conn.execute(text(migration_sql))
            conn.commit()
            print('✓ Migration completed successfully')

            # Verify the column was added
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'signals' AND column_name = 'cex_symbol'"))
            if result.fetchone():
                print('✓ cex_symbol column verified')
                return True
            else:
                print('✗ cex_symbol column not found')
                return False

    except Exception as e:
        print(f'✗ Migration failed: {e}')
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)