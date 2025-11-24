# Farm Management System - FastAPI Backend

## Setup Instructions

### 1. Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### 2. Installation

```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Running the Server

```bash
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

### 4. API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 5. Environment Variables (Production)

Create a `.env` file in the backend directory:

```env
SECRET_KEY=your-super-secret-jwt-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=your-database-connection-string
CORS_ORIGINS=http://localhost:5173,https://yourdomain.com
```

### 6. Database Setup

This backend currently uses in-memory mock data. To use a real database:

1. Install database driver (e.g., `pip install psycopg2-binary` for PostgreSQL)
2. Update the connection string in `.env`
3. Create database models using SQLAlchemy or your preferred ORM
4. Run migrations

### 7. API Endpoints

#### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user

#### Dashboard
- `GET /api/dashboard/stats` - Get dashboard statistics
- `GET /api/dashboard/recent-activities` - Get recent activities

#### Livestock
- `GET /api/livestock/` - List all livestock
- `POST /api/livestock/` - Add new livestock
- `GET /api/livestock/{id}` - Get livestock details
- `PUT /api/livestock/{id}` - Update livestock
- `DELETE /api/livestock/{id}` - Delete livestock

#### Crops
- `GET /api/crops/` - List all crops
- `POST /api/crops/` - Add new crop
- `GET /api/crops/{id}` - Get crop details
- `PUT /api/crops/{id}` - Update crop
- `DELETE /api/crops/{id}` - Delete crop

#### Inventory
- `GET /api/inventory/` - List inventory items
- `POST /api/inventory/` - Add inventory item
- `GET /api/inventory/{id}` - Get item details
- `PUT /api/inventory/{id}` - Update item
- `DELETE /api/inventory/{id}` - Delete item

#### Finance
- `GET /api/finance/transactions` - List transactions
- `POST /api/finance/transactions` - Add transaction
- `GET /api/finance/summary` - Get financial summary

#### Workers
- `GET /api/workers/` - List workers
- `POST /api/workers/` - Add worker
- `GET /api/workers/{id}` - Get worker details
- `PUT /api/workers/{id}` - Update worker
- `DELETE /api/workers/{id}` - Delete worker

#### Notifications
- `GET /api/notifications/` - List notifications
- `POST /api/notifications/` - Create notification
- `PUT /api/notifications/{id}/read` - Mark as read

#### Reports
- `GET /api/reports/livestock` - Livestock report
- `GET /api/reports/crops` - Crops report
- `GET /api/reports/financial` - Financial report
- `GET /api/reports/inventory` - Inventory report

### 8. Security Notes

⚠️ **Important for Production:**

1. Change the `SECRET_KEY` in `routers/auth.py`
2. Update CORS origins to match your frontend domain
3. Use environment variables for all sensitive data
4. Implement proper database with user authentication
5. Add rate limiting
6. Enable HTTPS
7. Implement proper logging
8. Add input validation and sanitization
9. Use secure password hashing (already implemented with bcrypt)

### 9. Connecting Frontend

Update your React frontend API base URL to point to this backend:

```typescript
const API_BASE_URL = 'http://localhost:8000/api';
```

### 10. Deployment

Popular deployment options:
- **Railway**: Simple deployment with automatic scaling
- **Render**: Free tier available
- **DigitalOcean App Platform**: Managed platform
- **AWS EC2/ECS**: Full control
- **Heroku**: Easy deployment (has free tier)

Example Railway deployment:
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

## Project Structure

```
backend/
├── main.py                 # FastAPI app entry point
├── requirements.txt        # Python dependencies
├── routers/               # API route handlers
│   ├── auth.py
│   ├── dashboard.py
│   ├── livestock.py
│   ├── crops.py
│   ├── inventory.py
│   ├── finance.py
│   ├── workers.py
│   ├── notifications.py
│   └── reports.py
└── README.md
```

## Next Steps

1. Replace mock data with real database
2. Implement proper user authentication with database
3. Add JWT token refresh mechanism
4. Implement role-based access control (RBAC)
5. Add file upload for images
6. Implement WebSocket for real-time notifications
7. Add proper error handling and logging
8. Write unit and integration tests
9. Add API versioning
10. Implement caching for frequently accessed data
