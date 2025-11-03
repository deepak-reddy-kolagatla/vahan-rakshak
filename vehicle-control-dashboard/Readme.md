cd vehicle-control-dashboard

echo "Starting Django server on port 8000..."
python manage.py runserver 0.0.0.0:8000 &

echo "Starting Vehicle Simulator..."
python vehicle_simulator/simulator.py &

echo "Starting Daphne ASGI server on port 8001..."
daphne -p 8001 vehicle_simulator.asgi:application &
