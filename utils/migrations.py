from datetime import datetime
import sqlite3

def migrate_journal_entries_add_entry_datetime(self):
    # 1. Add the column if it doesn't exist
    try:
        self.cursor.execute("ALTER TABLE journal_entries ADD COLUMN entry_datetime DATETIME")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # 2. Backfill the column for existing rows
    self.cursor.execute("SELECT rowid, entry_date, entry_time FROM journal_entries WHERE entry_datetime IS NULL OR entry_datetime = ''")
    rows = self.cursor.fetchall()
    for rowid, entry_date, entry_time in rows:
        try:
            # Parse and format as ISO datetime
            dt = datetime.strptime(f"{entry_date} {entry_time}", "%Y-%m-%d %I:%M%p")
            dt_str = dt.isoformat(sep=' ')
        except Exception:
            dt_str = None
        if dt_str:
            self.cursor.execute(
                "UPDATE journal_entries SET entry_datetime = ? WHERE rowid = ?",
                (dt_str, rowid)
            )
    self.conn.commit()