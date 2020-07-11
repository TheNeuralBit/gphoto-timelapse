import json


class JsonState(object):
    def __init__(self, fname):
        self._fname = fname

    def __enter__(self):
        try:
            fp = open(self._fname, "r")
        except IOError:
            self._state = {}
        else:
            with open(self._fname, "r") as fp:
                self._state = json.load(fp)

        return self._state

    def __exit__(self, exc_type, exc_value, traceback):
        with open(self._fname, "w") as fp:
            json.dump(self._state, fp)
