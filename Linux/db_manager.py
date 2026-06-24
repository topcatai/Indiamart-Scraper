import os
import sys
import sqlite3
import pandas as pd
import datetime
import config

# Global Windows console unicode encoding fix
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(errors='replace')

def get_db_connection():
    """Establishes and returns a connection to the SQLite database."""
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database and creates the leads table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            unique_key TEXT PRIMARY KEY,
            name TEXT,
            phone_number TEXT,
            email_id TEXT,
            gst TEXT,
            address_location TEXT,
            whatsapp_status TEXT,
            contact_type TEXT,
            requirement_details TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scraped_periods (
            start_date TEXT PRIMARY KEY,
            end_date TEXT,
            status TEXT,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS failed_contacts (
            unique_key TEXT PRIMARY KEY,
            card_name TEXT,
            card_text TEXT,
            failure_reason TEXT,
            failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            retry_count INTEGER DEFAULT 0,
            period_start TEXT,
            period_end TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT
        )
    """)
    conn.commit()
    
    # Migrate scraped_weeks -> scraped_periods if old table exists
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scraped_weeks'")
        if cursor.fetchone():
            print("[*] Migrating completed periods from scraped_weeks to scraped_periods...")
            cursor.execute("""
                INSERT OR IGNORE INTO scraped_periods (start_date, end_date, status, completed_at)
                SELECT start_date, end_date, status, completed_at FROM scraped_weeks
            """)
            cursor.execute("DROP TABLE scraped_weeks")
            conn.commit()
            print("[+] Migration completed successfully.")
    except Exception as e:
        print(f"[!] Database migration warning: {e}")

    
    # Check if columns exist and migrate
    cursor.execute("PRAGMA table_info(leads)")
    columns = [row['name'] for row in cursor.fetchall()]
    if 'chat_history' not in columns:
        print("[*] Migrating database: adding 'chat_history' column to leads table...")
        cursor.execute("ALTER TABLE leads ADD COLUMN chat_history TEXT")
        conn.commit()
    if 'lead_date' not in columns:
        print("[*] Migrating database: adding 'lead_date' column to leads table...")
        cursor.execute("ALTER TABLE leads ADD COLUMN lead_date TEXT")
        conn.commit()
        
    conn.close()
    print(f"[*] SQLite database initialized at: {os.path.abspath(config.DB_PATH)}")

def get_scraped_keys():
    """Retrieves a set of unique_keys that have already been scraped."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT unique_key FROM leads")
    rows = cursor.fetchall()
    conn.close()
    return {row['unique_key'] for row in rows}

def _clean_phone_suffix(phone):
    """Extracts the last 10 digits of a phone number for comparison."""
    if not phone:
        return None
    # Extract digits only
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) >= 10:
        return digits[-10:]
    return digits if digits else None

def insert_lead(lead_data):
    """
    Inserts a lead record into the database.
    Checks by last 10 digits of phone number to prevent duplicates.
    If the lead already exists, it ignores it and returns False.
    """
    # 1. Clean and check secondary phone deduplication
    incoming_phone = lead_data.get('phone_number', '')
    incoming_suffix = _clean_phone_suffix(incoming_phone)
    if incoming_suffix:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, phone_number FROM leads")
        rows = cursor.fetchall()
        for row in rows:
            existing_phone = row['phone_number']
            existing_suffix = _clean_phone_suffix(existing_phone)
            if existing_suffix and existing_suffix == incoming_suffix:
                print(f"[*] Secondary Duplicate Check: Skip inserting lead '{lead_data['name']}'. "
                      f"Phone suffix '{incoming_suffix}' already exists (as '{existing_phone}').")
                conn.close()
                return False
        conn.close()

    # 2. Proceed with database insert
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if lead_date exists in columns
    cursor.execute("PRAGMA table_info(leads)")
    cols = [row['name'] for row in cursor.fetchall()]
    
    # We use INSERT OR IGNORE to prevent duplicates and keep original scraped timestamps
    if 'lead_date' in cols:
        cursor.execute("""
            INSERT OR IGNORE INTO leads (
                unique_key, name, phone_number, email_id, gst, 
                address_location, whatsapp_status, contact_type, requirement_details, chat_history,
                lead_date, scraped_at, last_scraped_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lead_data['unique_key'],
            lead_data['name'],
            lead_data['phone_number'],
            lead_data['email_id'],
            lead_data['gst'],
            lead_data['address_location'],
            lead_data['whatsapp_status'],
            lead_data['contact_type'],
            lead_data['requirement_details'],
            lead_data.get('chat_history', ''),
            lead_data.get('lead_date', ''),
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
    else:
        cursor.execute("""
            INSERT OR IGNORE INTO leads (
                unique_key, name, phone_number, email_id, gst, 
                address_location, whatsapp_status, contact_type, requirement_details, chat_history,
                scraped_at, last_scraped_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lead_data['unique_key'],
            lead_data['name'],
            lead_data['phone_number'],
            lead_data['email_id'],
            lead_data['gst'],
            lead_data['address_location'],
            lead_data['whatsapp_status'],
            lead_data['contact_type'],
            lead_data['requirement_details'],
            lead_data.get('chat_history', ''),
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
    
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

def export_to_formats():
    """
    Queries the database and exports all leads to both CSV and Excel files.
    Includes exception handling in case the files are currently locked by the user.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(leads)")
    cols = [row['name'] for row in cursor.fetchall()]
    
    if 'lead_date' in cols:
        query = (
            "SELECT name, phone_number, email_id, gst, address_location, "
            "whatsapp_status, contact_type, requirement_details, chat_history, lead_date, scraped_at "
            "FROM leads ORDER BY scraped_at DESC"
        )
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return
            
        df.columns = [
            "Name", "Phone Number", "Email ID", "GST Number", 
            "Address / Location", "WhatsApp Status", "Contact Type", 
            "Requirement Details", "Chat History", "Lead Date (DD-MM-YYYY)", "Scraped Timestamp"
        ]
    else:
        query = (
            "SELECT name, phone_number, email_id, gst, address_location, "
            "whatsapp_status, contact_type, requirement_details, chat_history, scraped_at "
            "FROM leads ORDER BY scraped_at DESC"
        )
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return
            
        df.columns = [
            "Name", "Phone Number", "Email ID", "GST Number", 
            "Address / Location", "WhatsApp Status", "Contact Type", 
            "Requirement Details", "Chat History", "Scraped Timestamp"
        ]
    
    # Export to CSV
    try:
        df.to_csv(config.CSV_PATH, index=False, encoding='utf-8-sig')
        print(f"[+] Data exported to CSV: {os.path.abspath(config.CSV_PATH)}")
    except PermissionError:
        print(f"[!] Warning: Permission denied writing to {config.CSV_PATH}. Is it open in Excel?")
    except Exception as e:
        print(f"[!] Error exporting to CSV: {e}")
        
    # Export to Excel
    try:
        # Using openpyxl engine
        df.to_excel(config.EXCEL_PATH, index=False, sheet_name="IndiaMART Leads")
        print(f"[+] Data exported to Excel: {os.path.abspath(config.EXCEL_PATH)}")
    except PermissionError:
        print(f"[!] Warning: Permission denied writing to {config.EXCEL_PATH}. Is it open in Excel?")
    except Exception as e:
        print(f"[!] Error exporting to Excel: {e}")

def get_scraped_today_count():
    """Returns the total number of leads scraped on the current calendar day."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # We check leads where the date portion of scraped_at matches today's date
    cursor.execute("SELECT COUNT(*) FROM leads WHERE date(scraped_at) = date('now', 'localtime')")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def mark_period_completed(start_date, end_date):
    """Marks a calendar period as successfully scraped in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO scraped_periods (start_date, end_date, status, completed_at)
        VALUES (?, ?, 'completed', CURRENT_TIMESTAMP)
    """, (start_date, end_date))
    conn.commit()
    conn.close()
    print(f"[+] Marked period {start_date} to {end_date} as COMPLETED in database.")

def get_completed_periods():
    """Retrieves a set of start_dates of periods that have been completed."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT start_date FROM scraped_periods WHERE status = 'completed'")
    rows = cursor.fetchall()
    conn.close()
    return {row['start_date'] for row in rows}

def get_last_completed_period():
    """Retrieves the start date of the latest completed period."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(start_date) FROM scraped_periods WHERE status = 'completed'")
    val = cursor.fetchone()[0]
    conn.close()
    return val

def insert_failed_contact(unique_key, card_name, card_text, failure_reason, period_start, period_end):
    """Inserts or updates a failed contact record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO failed_contacts (unique_key, card_name, card_text, failure_reason, period_start, period_end)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(unique_key) DO UPDATE SET
            failure_reason = excluded.failure_reason,
            retry_count = retry_count + 1,
            failed_at = CURRENT_TIMESTAMP
    """, (unique_key, card_name, card_text, failure_reason, period_start, period_end))
    conn.commit()
    conn.close()

def get_failed_contacts():
    """Retrieves all failed contacts."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT unique_key, card_name, card_text, failure_reason, period_start, period_end, retry_count FROM failed_contacts ORDER BY failed_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def remove_failed_contact(unique_key):
    """Removes a failed contact from the failed_contacts table (e.g. after successful scrape)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM failed_contacts WHERE unique_key = ?", (unique_key,))
    conn.commit()
    conn.close()

def get_failed_count():
    """Returns the total number of failed contacts."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM failed_contacts")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_scraped_count():
    """Returns the total number of successfully scraped leads."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM leads")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def is_safety_accepted():
    """Checks if the user has accepted the pre-launch safety guidelines."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT setting_value FROM app_settings WHERE setting_key = 'safety_accepted'")
    row = cursor.fetchone()
    conn.close()
    return row is not None and row['setting_value'] == 'true'

def mark_safety_accepted():
    """Marks the pre-launch safety guidelines as accepted."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO app_settings (setting_key, setting_value)
        VALUES ('safety_accepted', 'true')
    """)
    conn.commit()
    conn.close()

def get_initial_start_date():
    """Retrieves the saved initial start date string (YYYY-MM-DD) if exists."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT setting_value FROM app_settings WHERE setting_key = 'initial_start_date'")
    row = cursor.fetchone()
    conn.close()
    return row['setting_value'] if row else None

def set_initial_start_date(start_date_str):
    """Saves the initial start date string (YYYY-MM-DD) to app_settings."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO app_settings (setting_key, setting_value)
        VALUES ('initial_start_date', ?)
    """, (start_date_str,))
    conn.commit()
    conn.close()

def get_max_lead_date():
    """
    Retrieves the maximum (most recent) lead date from the database.
    Parses 'DD-MM-YYYY' format and returns a datetime.date object, or None.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(leads)")
    cols = [row['name'] for row in cursor.fetchall()]
    if 'lead_date' not in cols:
        conn.close()
        return None
        
    cursor.execute("SELECT lead_date FROM leads WHERE lead_date IS NOT NULL AND lead_date != ''")
    rows = cursor.fetchall()
    conn.close()
    
    max_date = None
    for row in rows:
        date_str = row['lead_date']
        try:
            parts = date_str.split('-')
            if len(parts) == 3:
                d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                dt = datetime.date(y, m, d)
                if max_date is None or dt > max_date:
                    max_date = dt
        except Exception:
            continue
    return max_date



