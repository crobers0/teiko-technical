from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
import pandas as pd
import os

app = Flask(__name__)


def get_csv_df():
    csv_path = 'cell-count.csv'
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return pd.DataFrame()


@app.route('/')
def index():
    df = get_csv_df()
    n_samples = len(df)
    projects = int(df['project'].nunique()) if 'project' in df.columns else 0
    return render_template('index.html', n_samples=n_samples, projects=projects)


@app.route('/data')
def data_table():
    df = get_csv_df()
    q = request.args.get('q')
    if q and 'sample' in df.columns:
        df = df[df['sample'].astype(str).str.contains(q, case=False, na=False)]

    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    total = len(df)
    rows = df.iloc[offset:offset+limit].to_dict(orient='records')
    # build pagination urls
    prev_offset = max(0, offset - limit)
    next_offset = offset + limit if offset + limit < total else offset
    return render_template('data_table.html', rows=rows, limit=limit, offset=offset, total=total, q=q, prev_offset=prev_offset, next_offset=next_offset)


@app.route('/api/samples')
def api_samples():
    df = get_csv_df()
    q = request.args.get('q')
    if q and 'sample' in df.columns:
        df = df[df['sample'].astype(str).str.contains(q, case=False, na=False)]
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    data = df.iloc[offset:offset+limit].to_dict(orient='records')
    return jsonify({'total': len(df), 'rows': data})


@app.route('/visuals')
def visuals():
    candidates = ['cell_frequencies_table.html', 'response_boxplots.html']
    visuals = []
    for f in candidates:
        if os.path.exists(f):
            visuals.append({'name': f, 'url': url_for('visual_file', filename=f)})
    return render_template('visuals.html', visuals=visuals)


@app.route('/visual_file/<path:filename>')
def visual_file(filename):
    # Serve generated HTML visualizations from project root
    return send_from_directory('.', filename)


@app.route('/analytics')
def analytics():
    stats_path = 'response_stats.csv'
    stats = None
    if os.path.exists(stats_path):
        stats = pd.read_csv(stats_path).to_dict(orient='records')
    return render_template('analytics.html', stats=stats)


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
