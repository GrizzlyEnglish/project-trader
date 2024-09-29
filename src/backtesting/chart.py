import matplotlib.pyplot as plt

def chart_with_signals(data, call_signal, put_signal, title, x_label, y_label, fig_number):
    x = data[:, 0]
    y = data[:, 1]

    f1 = plt.figure(fig_number)
    # Create a plot
    plt.plot(x, y)

    for xc in call_signal:
        plt.axvline(x=xc, color='g', linestyle='--')

    for xc in put_signal:
        plt.axvline(x=xc, color='r', linestyle='--')

    # Add labels and title
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)