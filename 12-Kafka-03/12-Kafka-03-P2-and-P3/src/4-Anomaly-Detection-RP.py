import os
import random
import time
from quixstreams import Application
from quixstreams.models import TopicConfig

class TemperatureEventGenerator:
    """
    Generates temperature readings for three different machines.

    Machine ID's 0, 1 are functioning normally, 2 is malfunctioning.
    """

    probabilities_normal = {
        40: [0, 0, 100],
        50: [20, 30, 50],
        60: [30, 40, 30],
        70: [40, 50, 10],
        80: [80, 10, 10],
        90: [100, 0, 0],
    }

    probabilities_issue = {
        40: [0, 0, 100],
        50: [0, 10, 90],
        60: [5, 15, 80],
        70: [5, 20, 75],
        80: [5, 20, 75],
        90: [10, 20, 70],
    }

    def __init__(self):
        self.machine_temps = {0: 66, 1: 58, 2: 62}
        self.machine_types = {
            0: self.probabilities_normal,
            1: self.probabilities_normal,
            2: self.probabilities_issue,
        }

    def update_machine_temp(self, machine_id):
        """
        Updates the temperature for a machine by -1, 0, or 1 based on its current temp.
        """
        current_temp = self.machine_temps[machine_id]
        temp_key = (current_temp // 10) * 10

        # Ensure that temp_key is within the defined probabilities
        if temp_key not in self.machine_types[machine_id]:
            temp_key = max(key for key in self.machine_types[machine_id] if key <= current_temp)

        self.machine_temps[machine_id] += random.choices(
            [-1, 0, 1],
            self.machine_types[machine_id][temp_key],
        )[0]

        # Reset temperature if it goes below 0
        if self.machine_temps[machine_id] < 0:
            self.machine_temps[machine_id] = 0

    def generate_event(self):
        """
        Generate a temperature reading event for a Machine ID.
        """
        machine_id = random.randint(0, 2)  # Randomly select a machine
        self.update_machine_temp(machine_id)
        event_out = {
            "key": str(machine_id),
            "value": {
                "Temperature_C": self.machine_temps[machine_id],
                "Timestamp": time.time_ns(),
            },
        }
        return event_out


_app = Application(broker_address=os.environ.get("BROKER_ADDRESS", "localhost:9092,localhost:9094,localhost:9096"))
topic = _app.topic(name="temperature_readings",
        config=TopicConfig(
        num_partitions=3,
        replication_factor=3,
    ))
event_generator = TemperatureEventGenerator()

if __name__ == "__main__":
    with _app.get_producer() as producer:
        while True:
            event = event_generator.generate_event()
            event = topic.serialize(**event)
            print(f"producing event for MID {event.key}, {event.value}")
            producer.produce(key=event.key, value=event.value, topic=topic.name)
            time.sleep(1)  