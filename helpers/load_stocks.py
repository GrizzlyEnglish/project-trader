def load_symbols(fileName = 'stocks.txt'):
    symbols = []
    with open(fileName) as file:
        for line in file:
            symbols.append(line.strip())
    return symbols