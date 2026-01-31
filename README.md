# 🏥 Health Dashboard

A comprehensive personal health tracking dashboard that imports data from Apple Health and displays metrics, trends, sleep analysis, and actionable insights.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue?logo=typescript)
![React](https://img.shields.io/badge/React-18-blue?logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?logo=fastapi)
![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📸 OverView

| Dashboard | Metrics | Sleep Analysis |
|-----------|---------|----------------|
| Daily overview with steps, calories, sleep, and heart rate | Detailed charts for all health metrics | Sleep stages breakdown (Deep, REM, Light) |

---

## ✨ Features

### 📊 Dashboard
- **Daily Overview** - Steps, active calories, sleep duration, resting heart rate
- **Goal Progress** - Visual progress bars for daily targets
- **Streaks** - Track consecutive days of meeting goals
- **Weekly Averages** - Rolling 7-day averages for key metrics

### 📈 Metrics Explorer
- **25+ Health Metrics** - Weight, BMI, body fat, heart rate, HRV, blood oxygen, and more
- **Interactive Charts** - 30-day trend visualization with tooltips
- **Smart Units** - Automatic conversion (kg→lbs, decimal→percentage)
- **Statistics** - Current, average, minimum, and maximum values

### 😴 Sleep Analysis
- **Sleep Stages** - Deep, REM, Light, and Awake time breakdown
- **Duration Tracking** - Total time in bed vs actual sleep
- **Sleep Score** - Quality rating based on multiple factors
- **14-Day History** - Stacked bar charts showing sleep composition

### 🏃 Workouts
- **Activity Tracking** - Walking, running, cycling, and more
- **Workout History** - Duration, distance, and calories burned
- **Statistics** - Total workouts, minutes, and distance

### 📉 Trends & Analysis
- **30-Day Health Report** - Overall, activity, sleep, and recovery scores
- **Metric Trends** - Percentage changes with direction indicators
- **Smart Recommendations** - Personalized suggestions based on your data

### 💡 Health Insights
- **AI-Generated Insights** - Automatic detection of patterns and anomalies
- **Categorized Alerts** - Positive trends, warnings, and recommendations
- **Actionable Advice** - Specific suggestions to improve your health

### 📤 Data Import
- **Apple Health Export** - Import your complete health history
- **Automatic Parsing** - Extracts all supported metrics and workouts
- **Incremental Updates** - Import new data without duplicates

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Recharts |
| **Backend** | Python 3.11, FastAPI, SQLAlchemy, Pydantic |
| **Database** | PostgreSQL 15 |
| **Cache** | Redis 7 |
| **Deployment** | Docker, Docker Compose, GitHub Container Registry |

---

## 🚀 Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed
- [Git](https://git-scm.com/downloads) installed
- A [GitHub Personal Access Token](https://github.com/settings/tokens) with `read:packages` scope

### Option 1: Deploy with Pre-built Images (Recommended)

This method pulls pre-built Docker images from GitHub Container Registry.
```bash
# 1. Create directory
mkdir -p /opt/stacks/health-dashboard
cd /opt/stacks/health-dashboard

# 2. Download required files
curl -O https://raw.githubusercontent.com/IcarusCore/health-dashboard/main/docker-compose.prod.yml
curl -O https://raw.githubusercontent.com/IcarusCore/health-dashboard/main/.env.example
curl -O https://raw.githubusercontent.com/IcarusCore/health-dashboard/main/init.sql

# 3. Create and configure environment file
cp .env.example .env
nano .env  # Edit with your secure passwords

# 4. Generate a secure secret key
openssl rand -hex 32  # Copy this to SECRET_KEY in .env

# 5. Login to GitHub Container Registry
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# 6. Start the application
docker compose -f docker-compose.prod.yml up -d

# 7. Check status
docker compose -f docker-compose.prod.yml ps
```

### Option 2: Build from Source

This method clones the repository and builds images locally.
```bash
# 1. Clone the repository
git clone https://github.com/IcarusCore/health-dashboard.git
cd health-dashboard

# 2. Create and configure environment file
cp .env.example .env
nano .env  # Edit with your secure passwords

# 3. Generate a secure secret key
openssl rand -hex 32  # Copy this to SECRET_KEY in .env

# 4. Build and start
docker compose up -d --build

# 5. Check status
docker compose ps
```

### Access the Dashboard

Open your browser and navigate to:
- **Local**: http://localhost:3000
- **Remote**: http://YOUR_SERVER_IP:3000

Create an account and start importing your health data!

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:
```env
# Database Configuration
POSTGRES_USER=healthuser
POSTGRES_PASSWORD=your_secure_database_password
POSTGRES_DB=healthdashboard

# Redis Configuration  
REDIS_PASSWORD=your_secure_redis_password

# Backend Security (REQUIRED)
SECRET_KEY=generate_with_openssl_rand_hex_32
ENVIRONMENT=production
DEBUG=false

# CORS Origins (add your domain/IP)
CORS_ORIGINS=http://localhost:3000,http://your-server-ip:3000
```

### Environment Variable Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `POSTGRES_USER` | PostgreSQL username | No | `healthuser` |
| `POSTGRES_PASSWORD` | PostgreSQL password | **Yes** | - |
| `POSTGRES_DB` | Database name | No | `healthdashboard` |
| `REDIS_PASSWORD` | Redis password | **Yes** | - |
| `SECRET_KEY` | JWT signing key (32+ chars) | **Yes** | - |
| `ENVIRONMENT` | Runtime environment | No | `production` |
| `DEBUG` | Enable debug mode | No | `false` |
| `CORS_ORIGINS` | Allowed CORS origins | No | `http://localhost:3000` |

### Generate Secure Passwords
```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate database password
openssl rand -base64 24

# Generate Redis password
openssl rand -base64 24
```

---

## 📱 Importing Apple Health Data

### Step 1: Export from iPhone

1. Open the **Health** app on your iPhone
2. Tap your **profile picture** (top right)
3. Scroll down and tap **Export All Health Data**
4. Wait for the export to complete (may take several minutes)
5. Save or share the `export.zip` file

### Step 2: Transfer to Computer

- **AirDrop**: Send directly to your Mac
- **iCloud/Email**: Upload and download on your computer
- **Cable**: Connect iPhone and copy the file

### Step 3: Import to Dashboard

1. Log in to your Health Dashboard
2. Navigate to **Import Data** in the sidebar
3. Click **Choose File** and select your `export.zip`
4. Click **Upload and Import**
5. Wait for processing (large files may take a few minutes)

### Supported Data Types

| Category | Metrics |
|----------|---------|
| **Activity** | Steps, Active Energy, Basal Energy, Walking Distance, Exercise Minutes, Flights Climbed |
| **Vitals** | Heart Rate, Resting Heart Rate, HRV, Blood Oxygen, Respiratory Rate |
| **Body** | Weight, BMI, Body Fat Percentage, Lean Body Mass |
| **Sleep** | Sleep Duration, Sleep Stages (Deep, REM, Light, Awake) |
| **Nutrition** | Calories, Protein, Carbs, Fat, Fiber, Sugar |
| **Workouts** | All workout types with duration, distance, and calories |

---

## 🔧 Management Commands

### Container Management
```bash
# Start all services
docker compose -f docker-compose.prod.yml up -d

# Stop all services
docker compose -f docker-compose.prod.yml down

# View logs
docker compose -f docker-compose.prod.yml logs -f

# View specific service logs
docker compose -f docker-compose.prod.yml logs -f backend

# Restart a service
docker compose -f docker-compose.prod.yml restart backend

# Check service status
docker compose -f docker-compose.prod.yml ps
```

### Database Management
```bash
# Access PostgreSQL shell
docker compose -f docker-compose.prod.yml exec postgres psql -U healthuser -d healthdashboard

# Backup database
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U healthuser healthdashboard > backup.sql

# Restore database
docker compose -f docker-compose.prod.yml exec -T postgres psql -U healthuser healthdashboard < backup.sql
```

### Updating to Latest Version
```bash
# Pull latest images
docker compose -f docker-compose.prod.yml pull

# Restart with new images
docker compose -f docker-compose.prod.yml up -d

# Clean up old images
docker image prune -f
```

---

## 🏗️ Project Structure
```
health-dashboard/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/        # API endpoints
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   └── main.py            # Application entry
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── components/        # Reusable components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API client
│   │   ├── hooks/             # Custom hooks
│   │   └── utils/             # Utility functions
│   ├── Dockerfile
│   └── package.json
│
├── .github/
│   └── workflows/
│       └── docker-publish.yml # CI/CD pipeline
│
├── docker-compose.yml          # Local development
├── docker-compose.prod.yml     # Production deployment
├── .env.example                # Environment template
├── init.sql                    # Database initialization
└── README.md
```

---

## 🌐 API Documentation

Once running, access the interactive API documentation:

- **Swagger UI**: http://localhost:3000/api/docs
- **ReDoc**: http://localhost:3000/api/redoc

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Create new account |
| `POST` | `/api/v1/auth/login` | Authenticate user |
| `GET` | `/api/v1/dashboard/overview` | Get dashboard data |
| `GET` | `/api/v1/measurements/timeseries/{metric}` | Get metric history |
| `POST` | `/api/v1/imports/apple-health` | Import Apple Health data |
| `GET` | `/api/v1/sleep/sessions` | Get sleep sessions |
| `GET` | `/api/v1/workouts` | Get workout history |
| `GET` | `/api/v1/insights` | Get health insights |

---

## 🐛 Troubleshooting

### Common Issues

**Container won't start**
```bash
# Check logs for errors
docker compose -f docker-compose.prod.yml logs backend

# Verify environment variables
docker compose -f docker-compose.prod.yml config
```

**Database connection failed**
```bash
# Ensure postgres is healthy
docker compose -f docker-compose.prod.yml ps

# Check postgres logs
docker compose -f docker-compose.prod.yml logs postgres
```

**Can't pull images from ghcr.io**
```bash
# Re-authenticate with GitHub
echo "YOUR_TOKEN" | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# Verify token has read:packages scope
```

**Import fails or times out**
- Large Apple Health exports (>100MB) may take several minutes
- Check backend logs for specific errors
- Ensure adequate disk space and memory

### Reset Everything
```bash
# Stop and remove all containers, volumes, and networks
docker compose -f docker-compose.prod.yml down -v

# Start fresh
docker compose -f docker-compose.prod.yml up -d
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Apple Health](https://www.apple.com/ios/health/) for the comprehensive health data export
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent Python web framework
- [Recharts](https://recharts.org/) for beautiful React charts
- [Tailwind CSS](https://tailwindcss.com/) for utility-first styling

---

<p align="center">
  Made with ❤️ for better health tracking
</p>

