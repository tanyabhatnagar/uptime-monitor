# Uptime Monitor MVP

A clean, responsive, and robust end-to-end MVP Uptime Monitoring application. It allows users to register website URLs, automatically tests their availability and latency every minute in the background, and visualizes real-time metrics on a custom dashboard.

---

## 1. Technology Stack

### Backend
* **Python 3.12**
* **FastAPI**: Core ASGI framework for endpoints and documentation.
* **SQLAlchemy 2.0 & asyncpg**: Fully typed async database operations.
* **PostgreSQL**: Production relational database.
* **APScheduler**: In-process background scheduler running the concurrent ping task.
* **httpx**: Async HTTP client for requesting monitored targets.
* **Uvicorn**: Lightweight ASGI web server.

### Frontend
* **React + Vite**: Fast, modern frontend builds.
* **Axios**: Asynchronous client-side HTTP calls.
* **Custom Vanilla CSS (Glassmorphism)**: Tailored deep dark mode styling, ambient gradients, neon availability badges, and transitions.

### Containerization
* **Docker & Docker Compose**

---

## 2. Folder Structure

```
tetrix/
├── backend/
│   ├── app/
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── monitor.py       # Ping client & database writing logs
│   │   ├── __init__.py
│   │   ├── config.py            # Environment validation settings
│   │   ├── db.py                # Database pool connection & session getters
│   │   ├── main.py              # App bootstrapper & scheduler trigger
│   │   ├── models.py            # SQLAlchemy database tables mapping
│   │   ├── router.py            # HTTP API endpoint handlers
│   │   └── schemas.py           # Pydantic input/output schemas
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AddUrlForm.jsx   # Monitor creation forms
│   │   │   ├── ErrorAlert.jsx   # UI toast warnings
│   │   │   └── UrlsTable.jsx    # Table listing metrics & delete commands
│   │   ├── hooks/
│   │   │   └── useInterval.js   # Memory-leak free periodic polling hook
│   │   ├── services/
│   │   │   └── api.js           # Central Axios client exports
│   │   ├── App.jsx              # App orchestration and state
│   │   ├── index.css            # Custom CSS design system
│   │   └── main.jsx
│   ├── Dockerfile
│   ├── nginx.conf               # Nginx virtual host serving rules
│   └── package.json
├── docker-compose.yml
├── .env.example
└── .env
```

---

## 3. Installation & Usage (Docker Compose)

The application has been fully dockerized. You do not need to install local databases or python/node versions.

### Prerequisites
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

### Launching the Application
1. Clone or copy the project into a folder.
2. In the root directory, copy `.env.example` to `.env` (a pre-configured `.env` is already supplied for immediate use):
   ```bash
   cp .env.example .env
   ```
3. Boot the container services:
   ```bash
   docker compose up --build
   ```
   *This downloads the PostgreSQL database, builds the custom FastAPI and React Nginx images, sets up private virtual networking, and launches the application.*

4. **Access the Frontend**: Open your browser and navigate to **`http://localhost`**.
5. **Access the Backend API Docs**: Navigate to **`http://localhost:8000/docs`** to inspect the interactive Swagger UI.

---

## 4. Testing Instructions

You can verify the end-to-end monitoring system using the following test cases via the web dashboard (`http://localhost`):

### Test Case 1: Healthy URL
* **Input URL**: `https://example.com`
* **Input Name**: `Healthy Site`
* **Action**: Enter details and click **Add Monitor**.
* **Expected Output**:
  - The site is successfully added to the dashboard table.
  - Within seconds (due to startup trigger), the background task tests the URL.
  - The status changes from `PENDING` to a green **`UP`** badge.
  - Latency displays a positive number (e.g. `45.2 ms`).
  - HTTP Status displays **`200`**.
  - Last Checked displays the current timestamp.

### Test Case 2: Broken URL
* **Input URL**: `https://this-domain-does-not-exist-12345.com`
* **Input Name**: `Broken Site`
* **Action**: Enter details and click **Add Monitor**.
* **Expected Output**:
  - The site is registered and displays `PENDING`.
  - The scheduler pings the URL and catches a connection exception (DNS resolution error).
  - The status changes to a red **`DOWN`** badge.
  - Latency and HTTP Status displays `-` (null).
  - Last Checked updates to the current timestamp.
  - Hovering or inspecting history logs (`GET /history/{id}`) reveals the caught error: `Network failure: HostNotFoundError`.

---

## 5. Deployment Sketch (AWS Integration)

For moving this application from local containerization to an enterprise AWS deployment:

```
                  ┌────────────────────────┐
                  │     Users / Browsers   │
                  └───────────┬────────────┘
                              │ HTTPS
                              ▼
                  ┌────────────────────────┐
                  │    AWS CloudFront      │
                  └───────────┬────────────┘
                              │
            ┌─────────────────┴─────────────────┐
            │ Static Files (built)              │ API Requests
            ▼                                   ▼
  ┌──────────────────┐                ┌──────────────────┐
  │   Amazon S3      │                │ AWS Application  │
  │ (Static Hosting) │                │  Load Balancer   │
  └──────────────────┘                └─────────┬────────┘
                                                │
                                                ▼
                                      ┌──────────────────┐
                                      │  AWS ECS (Fargate│
                                      │ FastAPI Service  │
                                      └─────────┬────────┘
                                                │ Private Subnet
                                                ▼
                                      ┌──────────────────┐
                                      │    Amazon RDS    │
                                      │   (PostgreSQL)   │
                                      └──────────────────┘
```

1. **Frontend Hosting (React)**:
   - Run `npm run build` to output the production static files.
   - Deploy these files into an **Amazon S3** bucket configured for static web hosting.
   - Attach **AWS CloudFront** (CDN) in front of S3 to handle global distribution, edge caching, SSL/TLS certificates (via ACM), and secure `HTTPS` traffic.

2. **Backend API Hosting (FastAPI)**:
   - Push the backend Docker image to **AWS Elastic Container Registry (ECR)**.
   - Run the container within **AWS ECS (Elastic Container Service)** with **AWS Fargate** (serverless container compute).
   - Configure an **Application Load Balancer (ALB)** in front of the ECS service to handle TLS termination, request routing, and autoscaling.
   - The APScheduler runs in-process inside Fargate, eliminating external scheduling nodes.

3. **Database (PostgreSQL)**:
   - Provision an **Amazon RDS for PostgreSQL** database instance.
   - Place the database inside isolated private subnets of a VPC, allowing access only from the ECS container Security Groups.
   - Configure automatic daily snapshots, multi-AZ replication for high availability, and storage autoscaling.
