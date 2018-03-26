import sys
import time
import ossaudiodev
from collections import deque

# dsp level that counts for a tick
COUNT_THRESHOLD = 135

# Number of samples over which we seek a tick.
# That is a duration equal to BUFFER_SIZE / speed (8 kHz).
BUFFER_SIZE     = 64      # 8 ms

# Geiger tube CPM to uSv/h factor.
CPM_TO_USVpH    = 0.00812 # J305

# Compute CPM using the last COUNTS_SIZE ticks.
# The larger the value, the more averaged the result.
COUNTS_SIZE     = 8

if len(sys.argv) == 2:
    dev   = sys.argv[1]
    graph = False
elif len(sys.argv) == 3 and sys.argv[1] == "graph":
    dev   = sys.argv[2]
    graph = True
else:
    print "usage: %s [graph] <dsp>" % (sys.argv[0])
    sys.exit(1)

if graph:
    print "# DATE CPM uSv/h"

dsp = ossaudiodev.open(dev, "r")

dsp.speed(8000)
dsp.channels(1)
dsp.setfmt(ossaudiodev.AFMT_U8)

counts = deque()
max_usvph = 0
min_usvph = 1e6
while True:
    samples = dsp.read(BUFFER_SIZE)
    samples = map(ord, samples)
    now = time.time()

    if max(samples) > COUNT_THRESHOLD:
        counts.append(now)

    if len(counts) > COUNTS_SIZE:
        first = counts.popleft()
        delta = now - first
        cpm   = 60. * (COUNTS_SIZE / delta)
        usvph = cpm * CPM_TO_USVpH

        date = time.strftime("%Y-%m-%d %H:%M:%S")

        if usvph > max_usvph:
            max_usvph = usvph
        if usvph < min_usvph:
            min_usvph = usvph

        if graph:
            print "%f %f %f" % (now, cpm, usvph)
            sys.stdout.flush()
        else:
            print "[%s] (average over %3.1f s) %3.3f CPM, %3.3f uSv/h (min=%3.3f, max=%3.3f) uSv/h" % (date, delta, cpm, usvph, min_usvph, max_usvph)

dsp.close()
