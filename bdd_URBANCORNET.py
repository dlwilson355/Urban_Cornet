import sklearn
import pickle
import json

filename = "input.txt"
# this is temporary remove it
filename = r"data/fb82860d-eabc-a8d0-b341-facdff0ac0f1"

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


def compute_errors(y_pred, y_real):
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

    return total_error

# generate prediction probabilities
model = load_brain()
x, y = get_data_from_file(filename)
print(x)
print(y)
print(compute_errors(model.predict_proba(x), y))

