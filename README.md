# Health Dashboard

A comprehensive personal health tracking dashboard that imports data from Apple Health and displays metrics, trends, sleep analysis, and insights.

## Features

- 📊 **Dashboard** - Overview of daily health metrics (steps, calories, sleep, heart rate)
- 📈 **Metrics** - Detailed view of all health metrics with charts
- 🏃 **Workouts** - Track and view workout history
- 😴 **Sleep** - Sleep analysis with stage breakdowns (Deep, REM, Light)
- 📉 **Trends** - 30-day health trends and analysis
- 💡 **Insights** - AI-generated health insights and recommendations
- 📤 **Import** - Import data from Apple Health export

## Tech Stack

- **Frontend**: React + TypeScript + Vite + Tailwind CSS + Recharts
- **Backend**: FastAPI + Python + SQLAlchemy
- **Database**: PostgreSQL
- **Cache**: Redis
- **Deployment**: Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git

### Installation

1. **Clone the repository**
```bash
   git clone https://github.com/YOUR_USERNAME/health-dashboard.git
   cd health-dashboard
```

2. **Create environment file**
```bash
   cp .env.example .env
```

3. **Edit .env with your settings**
```bash
   nano .env
```
   
   Generate a secret key:
```bash
   openssl rand -hex 32
```

4. **Start the application**
```bash
   docker compose up -d
```

5. **Access the dashboard**
   - Open http://localhost:3000 in your browser
   - Create an account and start importing your health data

### Importing Apple Health Data

1. On your iPhone, go to **Health App** → **Profile** → **Export All Health Data**
2. Transfer the `export.zip` file to your computer
3. In the dashboard, go to **Import Data** and upload the zip file

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_USER` | PostgreSQL username | `healthuser` |
| `POSTGRES_PASSWORD` | PostgreSQL password | **Required** |
| `POSTGRES_DB` | Database name | `healthdashboard` |
| `REDIS_PASSWORD` | Redis password | **Required** |
| `SECRET_KEY` | JWT secret key | **Required** |
| `ENVIRONMENT` | Environment mode | `production` |
| `DEBUG` | Enable debug mode | `false` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |

### Unit Preferences

- Weight and body mass are displayed in **pounds (lbs)**
- Body fat is displayed as **percentage (%)**
- Sleep duration is displayed as **hours:minutes (h:mm)**

## Development

### Running locally without Docker

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## License

MIT License
