import sqlite3
import pandas as pd

def get_melanoma_male_responders_avg():
    """Calculate average B cells for melanoma males responders at baseline"""
    conn = sqlite3.connect('cell-count.db')
    
    query = """
    SELECT AVG(s.b_cell) as avg_b_cell
    FROM samples s
    JOIN subjects subj ON s.subject = subj.subject
    JOIN treatments t ON t.subject = subj.subject
    JOIN conditions c ON c.subject = subj.subject
    WHERE c.condition = 'melanoma'
    AND subj.sex = 'M'
    AND t.response = 'yes'
    AND s.time_from_treatment_start = 0
    AND t.treatment = 'miraclib'
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    avg_b_cell = df['avg_b_cell'].values[0]
    
    if avg_b_cell is not None:
        result = f"{avg_b_cell:.2f}"
        print(f"Average B cells for melanoma males (responders, baseline): {result}")
        return result
    else:
        print("No data found matching the criteria")
        return None

if __name__ == "__main__":
    get_melanoma_male_responders_avg()

# result: 10276.79