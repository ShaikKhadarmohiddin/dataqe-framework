class DataValidator:
    def __init__(self, source_value, target_value):
        self.source_value = source_value
        self.target_value = target_value

    def compare(self):
        if self.source_value == self.target_value:
            return "PASS"
        return "FAIL"

