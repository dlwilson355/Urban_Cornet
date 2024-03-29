import sklearn
import pickle
import json
import os


filename = "input.txt"


def load_brain():
    BRAIN_SAVE_FILE_PATH = "jarvis_URBANCORNET.pkl"
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


def compute_errors(y_pred, y_real, classes):
    classes = list(classes)
    y_err = []
    for pred, real in zip(y_pred, y_real):
        non_error_index = classes.index(real)

        total_error = 0
        for i in range(pred.shape[0]):
            if not i == non_error_index:
                total_error += pred[i]
        y_err.append(total_error)

    q4 = sorted(y_err)[len(y_err) - len(y_err)//5:]
    q4_mean = sum(q4) / len(q4)

    return q4_mean

# perform computations
model = load_brain()
x, y = get_data_from_file(filename)
error = compute_errors(model.predict_proba(x), y, model.classes_)

# make prediction
if error < 0.7814674354224296:
    print("good")
else:
    print("bad")
