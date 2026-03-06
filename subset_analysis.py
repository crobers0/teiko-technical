import sqlite3
import pandas as pd

"""
Subset queries: identify baseline (time_from_treatment_start=0) PBMC samples
from melanoma patients treated with miraclib.

Outputs:
- CSV of matching samples `baseline_miraclib_melanoma_samples.csv`
- Prints summaries: samples per project, responder/non-responder subject counts, male/female subject counts
"""

def query_baseline_samples(db_file='cell-count.db'):
    conn = sqlite3.connect(db_file)

    query = """
    SELECT DISTINCT
        s.sample,
        s.subject,
        subj.project,
        subj.age,
        subj.sex,
        t.treatment,
        t.response
    FROM samples s
    JOIN subjects subj ON s.subject = subj.subject
    JOIN treatments t ON t.subject = subj.subject AND t.treatment = 'miraclib'
    JOIN conditions c ON c.subject = subj.subject AND c.condition = 'melanoma'
    WHERE s.sample_type = 'PBMC' AND s.time_from_treatment_start = 0
    ORDER BY subj.project, s.subject
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    # Save results
    out_csv = 'baseline_miraclib_melanoma_samples.csv'
    df.to_csv(out_csv, index=False)

    print(f"\nFound {len(df)} baseline PBMC samples from melanoma patients treated with miraclib")
    print(f"Saved matching samples to {out_csv}")

    # How many samples from each project
    samples_per_project = df.groupby('project')['sample'].nunique().reset_index(name='n_samples')
    print('\nSamples per project:')
    print(samples_per_project.to_string(index=False))

    # How many subjects were responders/non-responders (unique subjects)
    subjects = df[['subject', 'response']].drop_duplicates(subset=['subject'])
    resp_counts = subjects['response'].value_counts(dropna=False).rename_axis('response').reset_index(name='n_subjects')
    print('\nSubjects by response:')
    print(resp_counts.to_string(index=False))

    # How many subjects were males/females
    subj_sex = df[['subject', 'sex']].drop_duplicates(subset=['subject'])
    sex_counts = subj_sex['sex'].value_counts(dropna=False).rename_axis('sex').reset_index(name='n_subjects')
    print('\nSubjects by sex:')
    print(sex_counts.to_string(index=False))

    return df, samples_per_project, resp_counts, sex_counts


if __name__ == '__main__':
    query_baseline_samples()
