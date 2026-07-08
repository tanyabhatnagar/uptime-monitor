# AI Collaboration Log (AI_LOG.md)

This log documents how I collaborated with my AI coding assistant, Antigravity (running Gemini 3.5 Flash), to design, build, and troubleshoot this Uptime Monitor MVP.

---

## 1. The AI Tech Stack
* **AI Tool**: Antigravity IDE Agent / Terminal Pair Programmer
* **Underlying Model**: Gemini 3.5 Flash
* **Usage Strategy**: I used the AI agent as a senior software architect for the planning phase, and then as a fast-typing compiler-verified pair programmer to build the boilerplates, API models, React components, and custom CSS layout.

---

## 2. Prompts That Shipped It

Here are the raw prompts I fed the assistant at each stage:

### Phase 1: Architecture & API Foundation
> *"Design the entire architecture before writing code. Explain the directory layout, the database schemas for URLs and health checks, the relationships, and the API endpoints (POST /urls, GET /urls, DELETE /urls/{id}, GET /history/{id}). Keep it as a strict MVP. Do not implement the scheduler yet."*

### Phase 2: Live Ping Scheduling
> *"Implement the background scheduler. Use APScheduler to query active database monitors and ping them every 60 seconds with a 10s timeout using httpx. If it succeeds, log it as UP (with status code). If it times out or throws connection errors, log it as DOWN. Do not overwrite previous checks; save all logs in the database. Update GET /urls so it resolves the latest status metrics using database joins."*

### Phase 3: Frontend Dashboard
> *"Build the frontend dashboard using React, Vite, Axios, and clean styling. Write a form to register URLs (with client-side http/https validation), an interactive data table displaying latency, HTTP status, and last checked time, and a delete action. Set up a 10-second polling interval using a custom React hook to refresh the table metrics dynamically without page reloads. Catch backend connection failures or duplicate URL registration errors."*

### Phase 4: Containerization
> *"Dockerize both applications. Configure a root docker-compose.yml file spinning up PostgreSQL, the FastAPI backend, and Nginx. Link the containers so database migrations run automatically on startup. Write a README with setup commands, testing steps, and a deployment sketch."*

---

## 3. Real-World Course Corrections (The "Peek Behind the Curtain")

During implementation, we encountered two significant issues where the AI's initial code needed human debugging and redirection:

### Course Correction 1: Optimizing the Dashboard List Query (N+1 Query Issue)
* **What happened**: When the AI generated the first version of the list endpoint (`GET /urls`), it queried the `urls` table, and then iterated over each URL inside a loop to pull its most recent check from the `health_checks` table.
* **Why it was bad**: This is a classic N+1 query pattern. With dozens of monitored sites, loading the dashboard would query the database dozens of times, thrashing the connection pool.
* **How we fixed it**: I had the AI rewrite the database query in `crud.py` to use a SQL **window function** (`ROW_NUMBER() OVER (PARTITION BY url_id ORDER BY checked_at DESC)`) combined with an `outerjoin`. This lets us retrieve all URLs along with their single most recent status in a single database roundtrip, handling new monitors (with zero checks) gracefully.

### Course Correction 2: Resolving DNS Port 53 Blocks in Docker Desktop (macOS)
* **What happened**: After spinning up the docker containers using `docker compose up`, I added a monitor for `https://example.com`, but the site immediately showed as `DOWN` with no HTTP status code. I checked the container logs and saw:
  `Network error checking URL https://example.com: [Errno -5] No address associated with hostname`
* **Why it was bad**: Docker Desktop on macOS has a known issue where container name resolution proxying fails over standard UDP Port 53 if local firewalls, VPNs, or router settings intercept UDP packets. 
* **How we fixed it**: We ran socket diagnostics inside the container and found that raw TCP traffic to the internet was working fine, but standard DNS resolution was blocked. Instead of forcing manual settings on the host machine, we wrote a global **DNS-over-HTTPS (DoH) monkeypatch** at the very top of `backend/app/main.py` that intercepts Python's `socket.getaddrinfo`. It resolves external domains by querying Google's secure DNS-over-HTTPS API (`https://8.8.8.8/resolve`) over standard **HTTPS (Port 443)**, and caches IPs locally.
* **Low-Level Refactoring**: During testing of the monkeypatch, we noticed it threw a `TypeError: inet_aton() argument 1 must be str, not bytes` because low-level async libraries (`anyio` / `asyncio`) pass hostnames as `bytes` strings. We resolved this by standardizing the type checking to decode `bytes` variables to string at the entrypoint of the custom resolver:
  ```python
  if isinstance(host, bytes):
      host = host.decode("utf-8")
  ```
  After compiling and rebuilding the containers, the scheduler began resolving public hostnames immediately and successfully reported `example.com` as **`UP`** with status **`200 OK`**.
