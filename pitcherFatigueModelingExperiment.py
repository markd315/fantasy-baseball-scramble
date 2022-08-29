from random import gauss
import pandas as pd
import numpy as np
desired_width = 320
pd.set_option('display.width', desired_width)
np.set_printoptions(linewidth=desired_width)


n = 10
orig = list(range(n))
occur = []
for _ in range(0,n):
    arr = []
    for _ in range(0,n):
        arr.append(0.0)
    occur.append(arr)

occur = np.array(occur)
cycles = 9000000
orderliness = 0.0041
for _ in range(cycles):
    x = sorted(orig, key=lambda i: gauss(i * orderliness, 1))
    occur[orig, x] += 1.0

occur *= np.array(100 / float(cycles))
tlbr = (occur[0][0] + occur[n-1][n-1]) / 2.0
trbl = (occur[0][n-1] + occur[n-1][0]) / 2.0
cToCPercent = (tlbr / trbl * 100.0) - 100.0
print(cToCPercent)
#4 and 6 is a 50% difference in corner to corner for n=20
#as I suspected, with a smaller array 19.5 and 20.7 is only a 5ish percent difference in corner to corner for n=5
#if I can find a way to hold the corner to corner change constant based on the orderliness by gathering some points and interpolating, maybe I can later find the expected increase in WHIP over facing batters again and do a pitch count / times thru order effect.
#let's say for now we want to create a 5% change in WHIP from the start to the end of a weekly dataset to model fatigue, since that may be achievable and about right.
#Corner to corner change should be strictly greater than this WHIP change due to the way good vs bad outcomes are distributed so shoot for 6-7%
# these effects are not even though. hr/9 tends to go up by as much as 25% from trip 1 to trip 3, wheras walks actually go DOWN 5%. K's go down 21%.
# maybe we can use an initial ordering of [k, bb, ipo, single, double, triple, hr] for the outcomes before applying this adjustment to account for that?

# n=3: 0.024 -> 5.89
# n=5 : 0.01 -> 5.89
# n=10
# TODO
# n=18 : 0.0025 -> 5.74
# n=35:
# n=50 : 0.00048 -> 5.71
# n=99 : 0.00023 -> 5.38 use 0.00024
