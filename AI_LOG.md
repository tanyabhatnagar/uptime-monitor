# AI Collaboration Log (AI_LOG)

This log details the AI tools, prompts, and architectural decisions made during the construction of the Uptime Monitor MVP application.

---

## 1. AI Assistant System Details

* **AI Agent Developer**: Antigravity, by Google DeepMind (Advanced Agentic Coding division).
* **Base Large Language Model**: Gemini 3.5 Flash.
* **Core Capabilities Employed**:
  - File manipulation and editing (`write_to_file`, `replace_file_content`).
  - Directory structural searches (`list_dir`, `grep_search`).
  - Local compilation and validation checks (`run_command`).
  - Multi-stage planning mode workflows (`implementation_plan.md`, `task.md`).

---

## 2. Representative Developer Prompts

### Phase 1: Architectural Design & Backend Foundation
> **Prompt**: *Design the entire architecture before writing code. Explain folder structures, DB models, APIs, and scheduler. Then generate the complete FastAPI foundation with database models, schemas, and endpoints: POST /urls, GET /urls, DELETE /urls/{id}, GET /history/{id}. Do not implement the scheduler yet. Explain every file.*

### Phase 2: Background Task Scheduler
> **Prompt**: *Implement the uptime monitoring background system. Use APScheduler to query active URLs and perform GET pings every 60 seconds with a 10s timeout using httpx. Log UP/DOWN states, response latency, and status codes. Update the GET /urls endpoint to return these values, utilizing clean service patterns. Do not overwrite check history.*

### Phase 3: Frontend Dashboard UI
> **Prompt**: *Build the dashboard using React, Vite, Axios, and custom CSS styling. Create a form to register URLs, an interactive table displaying status indicators, response times, and actions. Refresh metrics every 10 seconds without page reload. Build Axios services and handle errors.*

### Phase 4: Containerization & Submission
> **Prompt**: *Dockerize both apps. Configure a root docker-compose.yml file linking PostgreSQL, FastAPI, and Nginx. Implement healthy database constraints. Write final README.md and AI_LOG.md.*

---

## 3. Engineering Course Correction: SQL Query Optimization

### The Initial Naive Design
When designing the `GET /urls` endpoint (which displays all monitors along with their single most recent status metrics for the UI dashboard), the initial approach considered was querying the list of registered `Url` records, and then performing a secondary query in a loop (for each URL) to fetch its latest `HealthCheck` log.

* **Why this was less suitable**:
  - This is a classic **N+1 query problem**. If a user registers 1,000 URLs, rendering the main dashboard page triggers 1,001 database queries, resulting in high latency, CPU thrashing, and database connection exhaustion.
  - Doing this asynchronously in python would still block the DB pool.

### The Corrected Optimized Implementation
To resolve this, we optimized the database access layer in `backend/app/crud.py` by incorporating a SQL **window function** (`ROW_NUMBER()`) combined with a subquery join:

```python
subq = (
    select(
        models.HealthCheck.url_id,
        models.HealthCheck.is_up,
        models.HealthCheck.response_time_ms,
        models.HealthCheck.status_code,
        models.HealthCheck.checked_at,
        func.row_number().over(
            partition_by=models.HealthCheck.url_id,
            order_by=models.HealthCheck.checked_at.desc(),
        ).label("rn"),
    )
    .subquery()
)

stmt = (
    select(
        models.Url.id,
        models.Url.url,
        # ...
        subq.c.is_up.label("latest_is_up"),
        # ...
    )
    .outerjoin(subq, (models.Url.id == subq.c.url_id) & (subq.c.rn == 1))
)
```

* **Benefits of the corrected approach**:
  - **Single Query**: All URLs and their respective latest check statuses are retrieved in one single, high-performance database execution.
  - **Relational Integrity**: If a URL has no checks yet, the `outerjoin` naturally returns nulls, which maps directly to the UI's `PENDING` state.
  - **Database Level Execution**: Sorting and partitioning are handled natively by PostgreSQL, minimizing memory overhead in the python process.
