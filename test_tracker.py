from helpers import tracker

for i in range(100):
    tracker.track('QQQ', 0.01 + (i / 100))

tracker.clear('QQQ')

print(tracker.get('QQQ'))

hst = tracker.get('SPY')

if hst.empty:
    print("No spy")