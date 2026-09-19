
import time
with open("child_alive.txt", "w") as f: f.write("alive")
time.sleep(5)
with open("child_done.txt", "w") as f: f.write("done")
