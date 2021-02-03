import os
import time

num_faults = 10

projects = [
    ("Lang", 1, 65),
    ("Chart", 1, 26),
    ("Time", 1, 27),
    ("Math", 1, 106),
    ("Closure", 1, 133)
]

deprecated = [
    ("Lang", 2), ("Time", 21), ("Closure", 63), ("Closure", 93)
]

for project, first_version, last_version in projects:
  versions = ["{}b".format(i) for i in range(first_version, last_version + 1) if (project, i) not in deprecated]

  for j in range(len(versions)-num_faults+1):
      if j < num_faults:
        for k in range(2, num_faults):
          os.system("python3.6 create_multi.py {} {}".format(project, " ".join(versions[j:j+k])))
          time.sleep(3)
      os.system("python3.6 create_multi.py {} {}".format(project, " ".join(versions[j:j+num_faults])))
      time.sleep(3)
