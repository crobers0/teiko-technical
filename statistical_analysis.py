import sqlite3
import pandas as pd
import plotly.express as px
import scipy.stats as stats


def compare_responders(db_file='cell-count.db', output_html='response_boxplots.html', output_csv='response_stats.csv'):
    """Compare relative frequencies between responders and non-responders for miraclib-treated melanoma PBMC samples.

    Produces an interactive boxplot HTML and a CSV with test statistics (Mann-Whitney U, Bonferroni-corrected p-values).
    """
    conn = sqlite3.connect(db_file)

    query = """
    SELECT
        s.sample,
        s.b_cell,
        s.cd8_t_cell,
        s.cd4_t_cell,
        s.nk_cell,
        s.monocyte,
        subj.subject,
        t.response
    FROM samples s
    JOIN subjects subj ON s.subject = subj.subject
    JOIN treatments t ON t.subject = subj.subject AND t.treatment = 'miraclib'
    JOIN conditions c ON c.subject = subj.subject AND c.condition = 'melanoma'
    WHERE s.sample_type = 'PBMC'
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        print('No matching samples found for miraclib-treated melanoma PBMC.')
        return

    populations = ['b_cell', 'cd8_t_cell', 'cd4_t_cell', 'nk_cell', 'monocyte']

    # compute total and percentages
    df['total_count'] = df[populations].sum(axis=1)
    for pop in populations:
        df[pop + '_pct'] = df[pop] / df['total_count'] * 100

    # melt to long format
    long_rows = []
    for _, row in df.iterrows():
        for pop in populations:
            long_rows.append({
                'sample': row['sample'],
                'subject': row['subject'],
                'population': pop,
                'percentage': row[pop + '_pct'],
                'response': row['response']
            })

    long_df = pd.DataFrame(long_rows)

    # Keep only responders and non-responders
    long_df = long_df[long_df['response'].isin(['yes', 'no'])]

    # Boxplot
    fig = px.box(long_df, x='response', y='percentage', color='response', facet_col='population', points='all', title='Responder vs Non-responder: Cell Population % (miraclib, melanoma, PBMC)')
    fig.update_layout(showlegend=False, width=1200)
    fig.write_html(output_html, include_plotlyjs='cdn')
    print(f"Boxplots saved to {output_html}")

    # Statistical tests (Mann-Whitney U) per population
    results = []
    pops = long_df['population'].unique()
    for pop in pops:
        grp = long_df[long_df['population'] == pop]
        resp_vals = grp[grp['response'] == 'yes']['percentage'].dropna().values
        nonresp_vals = grp[grp['response'] == 'no']['percentage'].dropna().values

        if len(resp_vals) < 2 or len(nonresp_vals) < 2:
            p = None
            stat = None
        else:
            try:
                stat, p = stats.mannwhitneyu(resp_vals, nonresp_vals, alternative='two-sided')
            except Exception:
                stat, p = (None, None)

        results.append({'population': pop, 'statistic': stat, 'p_value': p, 'n_resp': len(resp_vals), 'n_nonresp': len(nonresp_vals)})

    res_df = pd.DataFrame(results)

    # Bonferroni correction
    n_tests = len(res_df)
    res_df['p_corrected'] = res_df['p_value'].apply(lambda pv: min(pv * n_tests, 1.0) if pd.notnull(pv) else None)
    res_df['significant'] = res_df['p_corrected'].apply(lambda pv: (pv is not None and pv < 0.05))

    res_df.to_csv(output_csv, index=False)
    print(f"Statistics saved to {output_csv}")

    # Print summary
    print('\nPopulation significance summary:')
    for _, r in res_df.iterrows():
        pop = r['population']
        p = r['p_value']
        pc = r['p_corrected']
        sig = r['significant']
        print(f"- {pop}: p={p}, p_corrected={pc}, significant={sig}")

    return long_df, res_df


if __name__ == '__main__':
    compare_responders()
