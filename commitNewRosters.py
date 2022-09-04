import os

import scheduling


# This is intended as a preseason setup script for after teams have finalized their first lineup but before the sample of games begins.
# For every week after, the next roster will be committed when the previous simulation executes.
for league in os.listdir("leagues"):
    scheduling.commitNewRosters(league)
