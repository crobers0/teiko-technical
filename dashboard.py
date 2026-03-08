from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
import pandas as pd
import sqlite3
import os

app = Flask(__name__)

DB_FILE = 'cell-count.db'


def get_db_connection():
    """Get a connection to the SQLite database"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Count total samples
    cursor.execute("SELECT COUNT(*) as count FROM samples")
    n_samples = cursor.fetchone()['count']
    
    # Count unique projects
    cursor.execute("SELECT COUNT(DISTINCT project) as count FROM subjects")
    projects = cursor.fetchone()['count']
    
    conn.close()
    return render_template('index.html', n_samples=n_samples, projects=projects)


@app.route('/data')
def data_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Map columns to their source tables
    col_to_table = {
        'sample': 's',
        'subject': 's',
        'sample_type': 's',
        'time_from_treatment_start': 's',
        'b_cell': 's',
        'cd8_t_cell': 's',
        'cd4_t_cell': 's',
        'nk_cell': 's',
        'monocyte': 's',
        'project': 'subj',
        'age': 'subj',
        'sex': 'subj'
    }
    
    # Get min/max ranges for numeric columns
    numeric_cols = ['time_from_treatment_start', 'age', 'b_cell', 'cd8_t_cell', 'cd4_t_cell', 'nk_cell', 'monocyte']
    
    # All columns we support filtering on
    column_names = list(col_to_table.keys())
    
    # Build filter definitions
    filters = []
    for col in column_names:
        table_alias = col_to_table[col]
        qualified_col = f"{table_alias}.{col}"
        
        if col in numeric_cols:
            query = f"SELECT MIN({qualified_col}), MAX({qualified_col}) FROM samples s LEFT JOIN subjects subj ON s.subject = subj.subject"
            cursor.execute(query)
            result = cursor.fetchone()
            real_min = result[0] if result[0] is not None else None
            real_max = result[1] if result[1] is not None else None
            col_min = request.args.get(f"{col}_min")
            col_max = request.args.get(f"{col}_max")
            filters.append({'name': col, 'type': 'number', 'min': real_min, 'max': real_max, 'value_min': col_min, 'value_max': col_max})
        else:
            # Check if column has few unique values
            query = f"SELECT DISTINCT {qualified_col} FROM samples s LEFT JOIN subjects subj ON s.subject = subj.subject WHERE {qualified_col} IS NOT NULL"
            cursor.execute(query)
            uniques = [row[0] for row in cursor.fetchall()]
            
            if 1 < len(uniques) <= 20:
                opts = sorted([str(u) for u in uniques])
                val = request.args.get(col)
                filters.append({'name': col, 'type': 'select', 'options': opts, 'value': val})
            else:
                val = request.args.get(col)
                filters.append({'name': col, 'type': 'text', 'value': val})
    
    # Build WHERE clause from filters
    where_clauses = []
    query_params = []
    
    for f in filters:
        col = f['name']
        table_alias = col_to_table[col]
        qualified_col = f"{table_alias}.{col}"
        
        if f['type'] == 'number':
            vmin = request.args.get(f"{col}_min")
            vmax = request.args.get(f"{col}_max")
            if vmin:
                try:
                    where_clauses.append(f"CAST({qualified_col} AS REAL) >= ?")
                    query_params.append(float(vmin))
                except Exception:
                    pass
            if vmax:
                try:
                    where_clauses.append(f"CAST({qualified_col} AS REAL) <= ?")
                    query_params.append(float(vmax))
                except Exception:
                    pass
        elif f['type'] == 'select':
            v = request.args.get(col)
            if v:
                where_clauses.append(f"{qualified_col} = ?")
                query_params.append(v)
        else:
            v = request.args.get(col)
            if v:
                where_clauses.append(f"{qualified_col} LIKE ?")
                query_params.append(f"%{v}%")
    
    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    # Get total count
    count_query = f"""
        SELECT COUNT(*) as count FROM samples s
        LEFT JOIN subjects subj ON s.subject = subj.subject
        WHERE {where_clause}
    """
    cursor.execute(count_query, query_params)
    total = cursor.fetchone()['count']
    
    # Get paginated data
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    
    data_query = f"""
        SELECT 
            s.sample,
            s.subject,
            s.sample_type,
            s.time_from_treatment_start,
            s.b_cell,
            s.cd8_t_cell,
            s.cd4_t_cell,
            s.nk_cell,
            s.monocyte,
            subj.project,
            subj.age,
            subj.sex
        FROM samples s
        LEFT JOIN subjects subj ON s.subject = subj.subject
        WHERE {where_clause}
        ORDER BY s.sample
        LIMIT ? OFFSET ?
    """
    
    cursor.execute(data_query, query_params + [limit, offset])
    rows = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    # Compute summary statistics from full filtered dataset
    summary_stats = {}
    if total > 0:
        # Get full filtered dataset for stats
        full_query = f"""
            SELECT DISTINCT
                s.sample,
                s.subject,
                subj.project,
                subj.sex,
                t.response
            FROM samples s
            LEFT JOIN subjects subj ON s.subject = subj.subject
            LEFT JOIN treatments t ON t.subject = s.subject
            WHERE {where_clause}
        """
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(full_query, query_params)
        full_rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        df_full = pd.DataFrame(full_rows)
        
        if not df_full.empty:
            # Samples per project
            if 'project' in df_full.columns:
                samples_per_project = df_full.groupby('project')['sample'].nunique().reset_index(name='n_samples')
                summary_stats['samples_per_project'] = samples_per_project.to_dict(orient='records')
            
            # Subjects by response
            if 'subject' in df_full.columns and 'response' in df_full.columns:
                subjects = df_full[['subject', 'response']].drop_duplicates(subset=['subject'])
                resp_counts = subjects['response'].value_counts(dropna=False).reset_index(name='n_subjects')
                resp_counts.columns = ['response', 'n_subjects']
                summary_stats['response_counts'] = resp_counts.to_dict(orient='records')
            
            # Subjects by sex
            if 'subject' in df_full.columns and 'sex' in df_full.columns:
                subj_sex = df_full[['subject', 'sex']].drop_duplicates(subset=['subject'])
                sex_counts = subj_sex['sex'].value_counts(dropna=False).reset_index(name='n_subjects')
                sex_counts.columns = ['sex', 'n_subjects']
                summary_stats['sex_counts'] = sex_counts.to_dict(orient='records')
    
    prev_offset = max(0, offset - limit)
    next_offset = offset + limit if offset + limit < total else offset
    return render_template('data_table.html', rows=rows, limit=limit, offset=offset, total=total, filters=filters, prev_offset=prev_offset, next_offset=next_offset, summary_stats=summary_stats)


@app.route('/api/samples')
def api_samples():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    q = request.args.get('q')
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    
    # Build query
    where_clause = ""
    params = []
    
    if q:
        where_clause = "WHERE s.sample LIKE ?"
        params = [f"%{q}%"]
    
    # Get total count
    count_query = f"SELECT COUNT(*) as count FROM samples s {where_clause}"
    cursor.execute(count_query, params)
    total = cursor.fetchone()['count']
    
    # Get paginated data
    data_query = f"""
        SELECT 
            s.sample,
            s.subject,
            s.sample_type,
            s.time_from_treatment_start,
            s.b_cell,
            s.cd8_t_cell,
            s.cd4_t_cell,
            s.nk_cell,
            s.monocyte
        FROM samples s
        {where_clause}
        ORDER BY s.sample
        LIMIT ? OFFSET ?
    """
    
    cursor.execute(data_query, params + [limit, offset])
    data = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({'total': total, 'rows': data})


@app.route('/visuals')
def visuals():
    candidates = ['response_boxplots.html']
    visuals = []
    for f in candidates:
        if os.path.exists(f):
            visuals.append({'name': f, 'url': url_for('visual_file', filename=f)})
    # Load stats for display on visuals page
    stats = None
    stats_path = 'response_stats.csv'
    if os.path.exists(stats_path):
        stats = pd.read_csv(stats_path).to_dict(orient='records')
    return render_template('visuals.html', visuals=visuals, stats=stats)


@app.route('/initial_analysis')
def initial_analysis():
    candidates = ['cell_frequencies_table.html']
    visuals = []
    for f in candidates:
        if os.path.exists(f):
            visuals.append({'name': f, 'url': url_for('visual_file', filename=f)})
    return render_template('initial_analysis.html', visuals=visuals)


@app.route('/visual_file/<path:filename>')
def visual_file(filename):
    # Serve generated HTML visualizations from project root
    return send_from_directory('.', filename)


@app.route('/subset_analysis')
def subset_analysis():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Query baseline PBMC samples from melanoma patients treated with miraclib
    base_query = """
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
    """
    
    # Load full dataset for stats computation
    cursor.execute(base_query + " ORDER BY subj.project, s.subject")
    full_rows = [dict(row) for row in cursor.fetchall()]
    df_full = pd.DataFrame(full_rows) if full_rows else pd.DataFrame()
    
    # Compute summary statistics from database
    summary_stats = {}
    if not df_full.empty:
        # Samples per project
        if 'project' in df_full.columns:
            samples_per_project = df_full.groupby('project')['sample'].nunique().reset_index(name='n_samples')
            summary_stats['samples_per_project'] = samples_per_project.to_dict(orient='records')
        
        # Subjects by response
        if 'subject' in df_full.columns and 'response' in df_full.columns:
            subjects = df_full[['subject', 'response']].drop_duplicates(subset=['subject'])
            resp_counts = subjects['response'].value_counts(dropna=False).reset_index(name='n_subjects')
            resp_counts.columns = ['response', 'n_subjects']
            summary_stats['response_counts'] = resp_counts.to_dict(orient='records')
        
        # Subjects by sex
        if 'subject' in df_full.columns and 'sex' in df_full.columns:
            subj_sex = df_full[['subject', 'sex']].drop_duplicates(subset=['subject'])
            sex_counts = subj_sex['sex'].value_counts(dropna=False).reset_index(name='n_subjects')
            sex_counts.columns = ['sex', 'n_subjects']
            summary_stats['sex_counts'] = sex_counts.to_dict(orient='records')
    
    # Get column names for filter definitions
    column_names = list(df_full.columns) if not df_full.empty else []
    
    # Build filter definitions
    filters = []
    numeric_cols = ['age']
    
    for col in column_names:
        if col in numeric_cols and not df_full.empty:
            real_min = float(df_full[col].min()) if col in df_full.columns else None
            real_max = float(df_full[col].max()) if col in df_full.columns else None
            col_min = request.args.get(f"{col}_min")
            col_max = request.args.get(f"{col}_max")
            filters.append({'name': col, 'type': 'number', 'min': real_min, 'max': real_max, 'value_min': col_min, 'value_max': col_max})
        else:
            if not df_full.empty and col in df_full.columns:
                uniques = df_full[col].dropna().astype(str).unique()
                if 1 < len(uniques) <= 20:
                    opts = sorted([str(u) for u in uniques])
                    val = request.args.get(col)
                    filters.append({'name': col, 'type': 'select', 'options': opts, 'value': val})
                else:
                    val = request.args.get(col)
                    filters.append({'name': col, 'type': 'text', 'value': val})
    
    # Apply filters from request args to dataframe
    df = df_full.copy()
    
    for f in filters:
        name = f['name']
        if f['type'] == 'number':
            vmin = request.args.get(f"{name}_min")
            vmax = request.args.get(f"{name}_max")
            if vmin:
                try:
                    df = df[pd.to_numeric(df[name], errors='coerce') >= float(vmin)]
                except Exception:
                    pass
            if vmax:
                try:
                    df = df[pd.to_numeric(df[name], errors='coerce') <= float(vmax)]
                except Exception:
                    pass
        elif f['type'] == 'select':
            v = request.args.get(name)
            if v:
                df = df[df[name].astype(str) == v]
        else:
            v = request.args.get(name)
            if v:
                df = df[df[name].astype(str).str.contains(v, case=False, na=False)]
    
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    total = len(df)
    rows = df.iloc[offset:offset+limit].to_dict(orient='records')
    prev_offset = max(0, offset - limit)
    next_offset = offset + limit if offset + limit < total else offset
    
    conn.close()
    
    return render_template('subset_analysis.html', rows=rows, limit=limit, offset=offset, total=total, filters=filters, prev_offset=prev_offset, next_offset=next_offset, summary_stats=summary_stats)


@app.route('/download/<path:filename>')
def download_file(filename):
    # Allow download of generated CSV/HTML files from project root
    if os.path.exists(filename):
        return send_from_directory('.', filename, as_attachment=True)
    return (f"File not found: {filename}", 404)


@app.route('/api/stats')
def api_stats():
    stats_path = 'response_stats.csv'
    if os.path.exists(stats_path):
        df = pd.read_csv(stats_path)
        return jsonify(df.to_dict(orient='records'))
    return jsonify({'error': 'response_stats.csv not found'}), 404


@app.route('/health')
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
