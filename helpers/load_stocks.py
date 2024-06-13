def load_symbols():
    symbols = []
    with open('stocks.txt') as file:
        for line in file:
            symbols.append(line.strip())
    return symbols