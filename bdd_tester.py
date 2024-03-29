import pickle
import json
import os

BRAIN_SAVE_FILE_PATH = "jarvis_URBANCORNET.pkl"
DATA_DIR = "bad_labeled_data"


def load_files():
    files = [os.path.join(DATA_DIR, file_path) for file_path in os.listdir(DATA_DIR)]
    return files


def load_brain():

    classifier = pickle.load(open(BRAIN_SAVE_FILE_PATH, 'rb'))
    return classifier


def get_data_from_file(file_path):
    """Returns the data from the file in the directory."""

    x, y = [], []

    # iterate through the data files, open the file, and read and strip the lines
    with open(file_path, 'r', encoding="utf8") as f:
        for line in f.readlines():
            line = line.strip()

            # check if it is formatted as json and load it accordingly
            if line[0] == "{" and line[-1] == "}":
                data_dict = json.loads(line)
                text = data_dict["TXT"]
                label = data_dict["ACTION"]

            # otherwise parse the string
            else:
                splits = line.split(",")
                text = ",".join(splits[:-1])
                label = splits[-1]

            # append the text and label
            x.append(text)
            y.append(label)

    return x, y


def compute_errors(y_pred, y_real, proportion=4):
    # find a better solution
    order = ['GREET', 'JOKE', 'PIZZA', 'TIME', 'WEATHER']

    y_err = []
    for pred, real in zip(y_pred, y_real):
        non_error_index = order.index(real)

        total_error = 0
        for i in range(pred.shape[0]):
            if not i == non_error_index:
                total_error += pred[i]
        y_err.append(total_error)

    mean_err = sum(y_err) / len(y_err)

    q4 = sorted(y_err)[len(y_err) - len(y_err)//proportion:]
    q4_mean = sum(q4) / len(q4)

    return q4_mean

# generate prediction probabilities
files = load_files()
model = load_brain()
proportions_to_test = [1, 2, 3, 4, 5, 6, 7, 8]
margins = []

for proportion in proportions_to_test:
    prediction = ""
    correct = 0
    wrong = 0
    largest_good_error = 0
    smallest_bad_error = 1

    for filename in files:
        x, y = get_data_from_file(filename)
        error = compute_errors(model.predict_proba(x), y, proportion)
        # print(filename)
        # print(error)

        # make prediction
        if error > 0.7:
            prediction = "bad"
        else:
            prediction = "good"

        # check if correct
        if "BAD" in filename and prediction == "bad":
            correct += 1
        elif "BAD" not in filename and prediction == "good":
            correct += 1
        else:
            # print("Misidentified")
            wrong += 1

        # update the largest and smallest errors
        if "BAD" in filename and error < smallest_bad_error:
            smallest_bad_error = error
        elif "BAD" not in filename and error > largest_good_error:
            largest_good_error = error

    margins.append(smallest_bad_error - largest_good_error)

    print(f"\nResults with proportion {proportion} are as follows.")
    print(f"The largest good error was {largest_good_error} and the smallest bad error was {smallest_bad_error}.")
    print(f"Recommended cutoff is {(largest_good_error + smallest_bad_error) / 2}")
    print(f"Classified {correct} correctly and {wrong} wrong.")

print(f"The margins were {margins} for proportions {proportions_to_test}.")
print(f"The recommended proportion is {proportions_to_test[margins.index(max(margins))]}.")
