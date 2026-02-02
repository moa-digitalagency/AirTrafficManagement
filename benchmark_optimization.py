import time
import sys
from unittest.mock import MagicMock

# Define latency
DB_LATENCY = 0.005 # 5ms per query

def run_benchmark():
    print("Preparing benchmark with simulated DB latency...")

    # Mock data
    flight_count = 100
    flights_data = [{'callsign': f'FLT{i}'} for i in range(flight_count)]

    # Mock Flight Model
    mock_flight_model = MagicMock()

    # Database storage simulation
    db_flights = {f'FLT{i}': MagicMock(callsign=f'FLT{i}') for i in range(flight_count)}

    # -- SLOW IMPLEMENTATION MOCK SETUP --
    # We use a factory to create a new mock for each call to ensure clean state if needed,
    # but here we just need side_effect to sleep.

    def slow_query_mock(callsign):
        time.sleep(DB_LATENCY) # Simulate DB trip
        # Return an object that has a first() method
        query_obj = MagicMock()
        query_obj.first.return_value = db_flights.get(callsign)
        return query_obj

    # mock_flight_model.query.filter_by(callsign=...) returns the query object
    mock_flight_model.query.filter_by.side_effect = lambda callsign=None: slow_query_mock(callsign)

    print(f"\nBenchmarking N+1 implementation with {flight_count} flights...")
    start_time = time.time()

    # The slow loop
    for flight_data in flights_data:
        flight = mock_flight_model.query.filter_by(
            callsign=flight_data.get('callsign')
        ).first()

    slow_duration = time.time() - start_time
    print(f"Slow Implementation Duration: {slow_duration:.4f}s")

    # -- FAST IMPLEMENTATION MOCK SETUP --

    def fast_query_mock(condition):
        time.sleep(DB_LATENCY) # Simulate DB trip (just one!)
        query_obj = MagicMock()
        query_obj.all.return_value = list(db_flights.values())
        return query_obj

    # Reset side effect for filter (used in fast implementation)
    mock_flight_model.query.filter.side_effect = fast_query_mock
    mock_flight_model.callsign.in_.return_value = "dummy_condition"

    print(f"\nBenchmarking Batched implementation with {flight_count} flights...")
    start_time = time.time()

    # The fast logic
    callsigns = [fd.get('callsign') for fd in flights_data if fd.get('callsign')]
    flights = mock_flight_model.query.filter(mock_flight_model.callsign.in_(callsigns)).all()
    flight_map = {f.callsign: f for f in flights}

    for flight_data in flights_data:
        flight = flight_map.get(flight_data.get('callsign'))

    fast_duration = time.time() - start_time
    print(f"Fast Implementation Duration: {fast_duration:.4f}s")

    if fast_duration > 0:
        print(f"Speedup: {slow_duration / fast_duration:.2f}x")

if __name__ == "__main__":
    run_benchmark()
