from polygon import RESTClient

import os
import pandas as pd

api_key = os.getenv("POLYGON_KEY")
client = RESTClient(api_key=api_key)

ticker = "AAPL"  # Example ticker
start_date = "2023-01-01"
end_date = "2023-01-31"
option_type = "call"  # or "put"

# Fetch the option contracts
options = client.list_options_contracts(ticker, contract_type=option_type, expiration_date_gte=start_date, expiration_date_lte=end_date)

# Convert to DataFrame
options_df = pd.DataFrame([option.__dict__ for option in options])

print("")