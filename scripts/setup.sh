#!/bin/bash

# SmolLM2 Task→API Mapper Setup Script

echo "🚀 Setting up SmolLM2 Task→API Mapper..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/{raw,processed,datasets}
mkdir -p models/{checkpoints,trained}
mkdir -p logs

# Set up environment files
echo "⚙️ Setting up environment..."
if [ ! -f backend/.env ]; then
    cp backend/.env backend/.env.local
    echo "✅ Created backend/.env.local"
fi

# Build and start services
echo "🐳 Building Docker containers..."
docker compose build

echo "🚀 Starting services..."
docker compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Run database migrations
echo "🗃️ Running database migrations..."
docker compose exec backend python manage.py migrate

# Create superuser (optional)
echo "👤 Creating superuser..."
docker compose exec backend python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

echo "✅ Setup complete!"
echo ""
echo "🌐 Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   Admin Panel: http://localhost:8000/admin"
echo ""
echo "📚 Next steps:"
echo "   1. Upload an OpenAPI specification"
echo "   2. Generate synthetic training data"
echo "   3. Train a SmolLM2 model"
echo "   4. Evaluate and test in the playground"
echo ""
echo "🛠️ Useful commands:"
echo "   docker compose logs -f          # View logs"
echo "   docker compose down             # Stop services"
echo "   docker compose up -d            # Start services"