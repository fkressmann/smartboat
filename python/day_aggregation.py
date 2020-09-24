import time


class DayAggregation:
    def __init__(self, metric):
        self.metric = metric
        self.last_reading = 0
        self.last_reading_time = time.time()
        self.aggregated_value = 0
        self.previous_value = 0

    def add_last_reading(self):
        self.aggregated_value += (self.last_reading * self.get_time_delta())

    def update(self, system_state, new_values):
        if system_state:
            self.add_last_reading()
            self.last_reading = new_values[self.metric]
            self.last_reading_time = time.time()

    def get_time_delta(self):
        return (time.time() - self.last_reading_time) / 3600

    def send_if_changed(self, send_to_openhab):
        rounded_aggregated = round(self.aggregated_value)
        if rounded_aggregated != self.previous_value:
            self.previous_value = rounded_aggregated
            print(f"Sending aggregated value {rounded_aggregated} to item {self.get_item_name()}")
            send_to_openhab(self.get_item_name(), rounded_aggregated)

    def get_item_name(self):
        return self.metric + "H"

    def persist_and_reset(self, cursor):
        self.add_last_reading()
        # noinspection SqlResolve
        cursor.execute(f"INSERT INTO {self.metric} (time, value) VALUES (NOW(),%s)", (self.aggregated_value,))
        self.last_reading = 0
        self.aggregated_value = 0