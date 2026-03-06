import csv
import sqlite3
import sys

def load_schema(conn, schema_file):
    """Load and execute the SQL schema from schema.sql"""
    with open(schema_file, 'r') as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    print(f"Schema loaded from {schema_file}")

def load_csv_to_db(csv_file, db_file, schema_file):
    """Load CSV data into SQLite database"""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Load schema
    load_schema(conn, schema_file)
    
    # Load CSV data
    subjects_inserted = 0
    conditions_inserted = 0
    treatments_inserted = 0
    samples_inserted = 0
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Insert into subjects (skip if already exists)
            try:
                cursor.execute(
                    "INSERT INTO subjects (subject, project, age, sex) VALUES (?, ?, ?, ?)",
                    (row['subject'], row['project'], int(row['age']), row['sex'])
                )
                subjects_inserted += 1
            except sqlite3.IntegrityError:
                # Subject already exists, skip
                pass
            
            # Insert into conditions (skip if already exists)
            try:
                cursor.execute(
                    "INSERT INTO conditions (subject, condition) VALUES (?, ?)",
                    (row['subject'], row['condition'])
                )
                conditions_inserted += 1
            except sqlite3.IntegrityError:
                # Condition already exists for this subject, skip
                pass
            
            # Insert into treatments (skip if already exists)
            try:
                response = row['response'] if row['response'] else None
                cursor.execute(
                    "INSERT INTO treatments (subject, treatment, response) VALUES (?, ?, ?)",
                    (row['subject'], row['treatment'], response)
                )
                treatments_inserted += 1
            except sqlite3.IntegrityError:
                # Treatment already exists for this subject, skip
                pass
            
            # Insert into samples (no duplicates expected)
            try:
                cursor.execute(
                    "INSERT INTO samples (sample, subject, sample_type, time_from_treatment_start, b_cell, cd8_t_cell, cd4_t_cell, nk_cell, monocyte) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        row['sample'], row['subject'], row['sample_type'],
                        int(row['time_from_treatment_start']),
                        int(row['b_cell']), int(row['cd8_t_cell']), int(row['cd4_t_cell']),
                        int(row['nk_cell']), int(row['monocyte'])
                    )
                )
                samples_inserted += 1
            except sqlite3.IntegrityError as e:
                print(f"Warning: Failed to insert sample {row['sample']}: {e}")
    
    conn.commit()
    conn.close()
    
    # Print summary
    print(f"\nData loaded from {csv_file}")
    print(f"  Subjects: {subjects_inserted} inserted")
    print(f"  Conditions: {conditions_inserted} inserted")
    print(f"  Treatments: {treatments_inserted} inserted")
    print(f"  Samples: {samples_inserted} inserted")
    print(f"\nDatabase created: {db_file}")

if __name__ == "__main__":
    csv_file = "cell-count.csv"
    db_file = "cell-count.db"
    schema_file = "schema.sql"
    
    try:
        load_csv_to_db(csv_file, db_file, schema_file)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
