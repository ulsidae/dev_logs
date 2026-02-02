import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import math


# Prime Number?
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True


# initialize
x, y = [0], [0]
dx, dy = 1, 0
step = 1
current = 1

fig, ax = plt.subplots()
line, = ax.plot([], [], 'b-')
texts = []


# adjust screen
def adjust_limits():
    margin = 5
    ax.set_xlim(min(x) - margin, max(x) + margin)
    ax.set_ylim(min(y) - margin, max(y) + margin)


def update(frame):
    global dx, dy, current, texts

    current += 1

    if is_prime(current):
        dx, dy = -dy, dx  # turn left

    x.append(x[-1] + dx * step)
    y.append(y[-1] + dy * step)

    # line update
    line.set_data(x, y)

    # print Prime Number
    if is_prime(current):
        txt = ax.text(x[-1], y[-1], str(current), fontsize=8, color='red')
        texts.append(txt)

    adjust_limits()
    return [line] + texts


ani = FuncAnimation(fig, update, frames=1000, interval=50, blit=False)
plt.show()
