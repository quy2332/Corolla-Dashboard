import csv

with open("data/corolla_obd_replay_10hz.csv", newline="") as f:
    reader = csv.DictReader(f)

    for i, row in enumerate(reader):
        print(row)

        if i >= 10:
            break
