import pandas as pd


def load_output():
    return pd.read_csv('dickssportgoods.csv')
    
def remove_last_entries_with_same_url():
    data = load_output()
    last_url = data['pcurl'].iloc[-1]
    data = data[data['pcurl'] != last_url]
    data.to_csv('dickssportgoods.csv', index=False)

