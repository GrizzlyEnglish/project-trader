def load_symbol_information(fileName):
    symbols = []
    with open(fileName) as file:
        for line in file:
            arr = line.strip().split(',')
            symbols.append({
                'symbol': arr[0],
                'time_window': int(arr[1]),
                'day_diff': int(arr[2]),
                'look_back': int(arr[3]),
                'look_forward': int(arr[4]),
            })
    return symbols