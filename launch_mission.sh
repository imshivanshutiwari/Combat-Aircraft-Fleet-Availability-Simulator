
#!/bin/bash
# 🚀 MISSION-READY OPS CENTER LAUNCH SCRIPT (Linux/macOS)

echo "--- FLEET OPS CENTER: UNIVERSAL MASTER DEPLOYMENT ---"
echo "Initializing containerized environment..."

# Check for Docker
if ! [ -x "$(command -v docker)" ]; then
  echo '❌ ERROR: Docker is not installed.' >&2
  exit 1
fi

# Build and Start
echo "Building Mission-Ready Image (this may take a few minutes)..."
docker-compose up --build -d

if [ $? -eq 0 ]; then
  echo "✅ DEPLOYMENT SUCCESSFUL!"
  echo "Dashboard available at: http://localhost:8501"
  echo "ZMQ Bridge active at: tcp://localhost:5555"
  echo "Use 'docker-compose down' to terminate mission."
else
  echo "❌ DEPLOYMENT FAILED. Check Docker logs for details."
fi
