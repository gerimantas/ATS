# ATS Database Setup Instructions

## Overview
This document provides step-by-step instructions for setting up TimescaleDB using Docker for the ATS system on Windows 11.

## Prerequisites
- Windows 11
- ATS environment setup completed (Task 1)
- Administrator privileges for Docker installation

**Note**: You do NOT need to install PostgreSQL separately - Docker container includes everything needed.

## Step 1: Install TimescaleDB using Docker

### 1.1 Install Docker Desktop
1. Go to [https://docs.docker.com/get-started/get-docker/](https://docs.docker.com/get-started/get-docker/)
2. Download Docker Desktop for Windows
3. Run the installer and follow the installation wizard
4. Restart your computer if prompted
5. Verify Docker is running by opening Command Prompt and running: `docker --version`

### 1.2 Install TimescaleDB Docker Container
1. Open Command Prompt or PowerShell
2. Pull the TimescaleDB Docker image:
   ```cmd
   docker pull timescale/timescaledb-ha:pg17
   ```
3. Run the TimescaleDB container:
   ```cmd
   docker run -d --name timescaledb -p 5432:5432 -e POSTGRES_PASSWORD=your_secure_password_here timescale/timescaledb-ha:pg17
   ```
   **Note**: Replace `your_secure_password_here` with a strong password

**Important**: We're not using volume mapping (`-v`) to avoid Windows permission issues. Data will be stored inside the container. For production use, consider using Docker volumes or named volumes instead.

### 1.3 Verify TimescaleDB Installation
1. Connect to the database using Docker (no separate psql installation needed):
   ```cmd
   docker exec -it timescaledb psql -U postgres
   ```
2. Check installed extensions:
   ```sql
   \dx
   ```
3. You should see TimescaleDB and TimescaleDB Toolkit listed
4. Exit psql with `\q`

**Note**: All database tools (psql, PostgreSQL, TimescaleDB) are included in the Docker container.

## Step 2: Create ATS Database and User

### 2.1 Create Environment File
1. In your ATS project directory, copy `.env.example` to `.env`
2. Edit `.env` and set your database connection details:
   ```
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=ats_db
   DB_USER=ats_user
   DB_PASSWORD=your_secure_password_here
   ```
   **Note**: Use the same password you set when creating the Docker container

### 2.2 Connect to TimescaleDB Container
1. Connect to the running TimescaleDB container:
   ```cmd
   docker exec -it timescaledb psql -U postgres
   ```
2. You should see the PostgreSQL prompt: `postgres=#`

### 2.3 Create ATS Database and User
Run these SQL commands in the PostgreSQL prompt:

```sql
-- Create dedicated user for ATS
CREATE USER ats_user WITH PASSWORD 'your_secure_password_here';

-- Create database
CREATE DATABASE ats_db OWNER ats_user;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ats_db TO ats_user;

-- Connect to ats_db database
\c ats_db

-- Enable TimescaleDB extension (should already be available)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO ats_user;
GRANT CREATE ON SCHEMA public TO ats_user;

-- Exit psql
\q
```

### 2.4 Run Database Setup Script (Optional)
1. Open Command Prompt in your ATS project directory
2. Activate the virtual environment:
   ```cmd
   ats_env\Scripts\activate
   ```
3. Run the database setup script:
   ```cmd
   python src/database/setup.py
   ```
4. The script should connect to your Docker-based TimescaleDB instance

## Step 3: Verify Setup

### 3.1 Test Database Connection
1. Run the database test:
   ```cmd
   python tests/test_database.py
   ```
2. All tests should pass

### 3.2 Test with Setup Script
1. Run the setup verification:
   ```cmd
   python src/database/setup.py
   ```
2. Should show successful connection and TimescaleDB availability

## Step 4: Configure Windows Firewall (Optional)

If you plan to access the database from other machines:

1. Open Windows Defender Firewall with Advanced Security
2. Create a new Inbound Rule:
   - Rule Type: Port
   - Protocol: TCP
   - Port: 5432
   - Action: Allow the connection
   - Profile: Select appropriate profiles
   - Name: TimescaleDB Docker

## Troubleshooting

### Common Issues

1. **Docker container not running**
   - Check if Docker Desktop is running
   - Verify container status: `docker ps`
   - Restart container: `docker restart timescaledb`

2. **Connection refused**
   - Ensure Docker container is running: `docker ps`
   - Check if port 5432 is available: `netstat -an | findstr 5432`
   - Verify container logs: `docker logs timescaledb`

3. **TimescaleDB extension not found**
   - TimescaleDB should be pre-installed in the Docker image
   - Connect to container and check: `docker exec -it timescaledb psql -U postgres -c "\dx"`
   - If missing, recreate container with correct image

4. **Permission denied**
   - Ensure user has correct privileges (check Step 2.3)
   - Verify database ownership
   - Check schema permissions

5. **Windows Permission Issues (Volume Mapping)**
   - **Error**: `initdb: error: could not change permissions of directory "/pgdata": Operation not permitted`
   - **Solution**: Remove volume mapping from docker run command
   - **Alternative**: Use Docker named volumes instead of bind mounts:
     ```cmd
     docker volume create timescaledb-data
     docker run -d --name timescaledb -p 5432:5432 -v timescaledb-data:/var/lib/postgresql/data -e POSTGRES_PASSWORD=your_password timescale/timescaledb-ha:pg17
     ```

6. **Container Exits Immediately**
   - Check logs: `docker logs timescaledb`
   - Common cause: Permission issues with mounted directories
   - Solution: Run without volume mapping or use named volumes

### Docker Commands

- **Check container status**: `docker ps -a`
- **View container logs**: `docker logs timescaledb`
- **Stop container**: `docker stop timescaledb`
- **Start container**: `docker start timescaledb`
- **Remove container**: `docker rm timescaledb`
- **Connect to container**: `docker exec -it timescaledb psql -U postgres`

### Log Files
- Docker container logs: `docker logs timescaledb`
- ATS logs: `logs/` directory in project

## Next Steps

After successful database setup:
1. Proceed to Task 3: CEX Data Integration
2. Continue with remaining ATS implementation tasks

## Support

For issues:
1. Check PostgreSQL documentation: [https://www.postgresql.org/docs/](https://www.postgresql.org/docs/)
2. Check TimescaleDB documentation: [https://docs.timescale.com/](https://docs.timescale.com/)
3. Review ATS logs in the `logs/` directory
