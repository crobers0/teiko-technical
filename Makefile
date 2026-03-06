.PHONY: setup pipeline dashboard clean

setup:
	pip install -r requirements.txt
	@echo "Dependencies installed"

pipeline: setup
	python load_data.py
	python initial_analysis.py
	python statistical_analysis.py
	python subset_analysis.py

dashboard: setup
	python dashboard.py

clean:
	rm -f cell-count.db cell_frequencies.csv baseline_miraclib_melanoma_samples.csv cell_frequencies_table.html response_boxplots.html response_stats.csv
	@echo "Cleaned up generated files"
