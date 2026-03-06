import sqlite3
import pandas as pd
import plotly.graph_objects as go

def analyze_cell_frequencies(db_file='cell-count.db'):
    """
    Analyze the relative frequency of each cell type in each sample.
    
    For each sample, calculates:
    - total_count: sum of all cell populations
    - percentage: relative frequency of each population
    
    Returns a DataFrame with columns:
    sample, total_count, population, count, percentage
    """
    conn = sqlite3.connect(db_file)
    
    # Query all samples with cell counts
    query = """
    SELECT 
        sample,
        b_cell,
        cd8_t_cell,
        cd4_t_cell,
        nk_cell,
        monocyte
    FROM samples
    ORDER BY sample
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Define cell populations
    populations = ['b_cell', 'cd8_t_cell', 'cd4_t_cell', 'nk_cell', 'monocyte']
    
    # Calculate total count for each sample
    df['total_count'] = df[populations].sum(axis=1)
    
    # Transform to long format with one row per sample-population combination
    results = []
    for _, row in df.iterrows():
        sample = row['sample']
        total_count = row['total_count']
        
        for population in populations:
            count = row[population]
            percentage = (count / total_count * 100) if total_count > 0 else 0
            
            results.append({
                'sample': sample,
                'total_count': int(total_count),
                'population': population,
                'count': int(count),
                'percentage': round(percentage, 2)
            })
    
    result_df = pd.DataFrame(results)
    return result_df

if __name__ == "__main__":
    # Analyze and display cell frequencies
    frequency_df = analyze_cell_frequencies()
    
    # results
    print("Cell Type Frequency Analysis")
    print("-" * 80)
    print(frequency_df.to_string(index=False))
    
    # Save to CSV
    frequency_df.to_csv('cell_frequencies.csv', index=False)
    print("\nResults saved to cell_frequencies.csv")

    # table graphic
    def render_table(df, html_file='cell_frequencies_table.html'):
        # consistent ordering
        df_sorted = df.sort_values(['sample', 'population'])

        header = ['sample', 'total_count', 'population', 'count', 'percentage']
        values = [
            df_sorted['sample'].astype(str).tolist(),
            df_sorted['total_count'].astype(str).tolist(),
            df_sorted['population'].astype(str).tolist(),
            df_sorted['count'].astype(str).tolist(),
            df_sorted['percentage'].astype(str).tolist()
        ]

        fig = go.Figure(data=[go.Table(
            header=dict(values=header, font=dict(size=12)),
            cells=dict(values=values, align='left')
        )])

        fig.update_layout(title_text='Cell Population Frequencies per Sample', title_x=0.5, width=1100)

        fig.write_html(html_file, include_plotlyjs='cdn')
        print(f"\nTable saved to {html_file}")

    render_table(frequency_df)
