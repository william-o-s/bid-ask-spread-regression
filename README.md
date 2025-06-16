### How do I use this notebook?

Navigate to [the main notebook](emailed/regression_v2.ipynb).

There are 3 determinants of this notebook:
1. `regression_v2.ipynb` (the notebook itself): runs the statistical analysis, visualizations, and models
2. `download_company.py`: downloads company info from Yahoo Finance
3. The file with company symbols (e.g., `nano_usa.csv`): contains the stock symbols to be downloaded

FAQs
1. How do I change which companies are downloaded?
    - A: Download a set of stocks from the NASDAQ website. Refer to the cells below `reuse_results == False`
2. How do I change which company information is used?
    - A: Refer to the names of various info from the Apple sample.
3. How do I avoid re-downloading all company data from Yahoo Finance?
    - A: Set `reuse_results = True` in the cell under 'Inputs to this notebook'