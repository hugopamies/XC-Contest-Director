import pandas as pd

def export_all_data_to_excel(filepath, rankings_data):
    with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
        for category, rows in rankings_data.items():
            if rows:
                df = pd.DataFrame(rows)
            else:
                df = pd.DataFrame(columns=["No data"])
            sheet_name = category[:31]  # Excel limit
            df.to_excel(writer, sheet_name=sheet_name, index=False)
