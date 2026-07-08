import React, { useState } from "react";
import { LineChart, Line } from "recharts";
import apiService from "../services/api";

/**
 * Renders the table of monitored URLs with instant search, sorting,
 * manual health triggers, and sparkline charts.
 * 
 * @param {Object} props
 * @param {Array} props.urls - List of URLs with their health metadata.
 * @param {Function} props.onDeleteSuccess - Callback triggered after deleting/checking a URL.
 * @param {Function} props.onError - Callback triggered to display errors.
 * @param {boolean} props.loading - Indicates if the dashboard is loading.
 */
export function UrlsTable({ urls, onDeleteSuccess, onError, loading }) {
  const [deletingId, setDeletingId] = useState(null);
  const [checkingIds, setCheckingIds] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortField, setSortField] = useState("id");
  const [sortDirection, setSortDirection] = useState("asc");

  const handleDelete = async (e, id, name, urlStr) => {
    e.stopPropagation();
    const confirmDelete = window.confirm(
      `Are you sure you want to stop monitoring and delete "${name || urlStr}"?`
    );
    if (!confirmDelete) return;

    setDeletingId(id);
    onError(null);
    try {
      await apiService.deleteUrl(id);
      onDeleteSuccess();
    } catch (err) {
      if (err.response) {
        onError(err.response.data?.detail || "Failed to delete the URL.");
      } else {
        onError("Failed to communicate with the server to delete URL.");
      }
    } finally {
      setDeletingId(null);
    }
  };

  const handleManualCheck = async (e, id) => {
    e.stopPropagation();
    setCheckingIds((prev) => [...prev, id]);
    onError(null);
    try {
      await apiService.checkUrlNow(id);
      onDeleteSuccess();
    } catch (err) {
      console.error("Manual check trigger error:", err);
      if (err.response) {
        onError(err.response.data?.detail || "Failed to trigger immediate check.");
      } else {
        onError("Failed to communicate with the server for immediate check.");
      }
    } finally {
      setCheckingIds((prev) => prev.filter((cid) => cid !== id));
    }
  };

  const formatTimestamp = (isoString) => {
    if (!isoString) return "-";
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    } catch (e) {
      return "-";
    }
  };

  const formatLatency = (ms) => {
    if (ms === null || ms === undefined) return "-";
    return `${ms.toFixed(1)} ms`;
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  const renderSortIndicator = (field) => {
    if (sortField !== field) return null;
    return sortDirection === "asc" ? " ▲" : " ▼";
  };

  // 1. Filter URLs by search term (instant on frontend)
  const filteredUrls = (urls || []).filter((row) => {
    const term = searchTerm.trim().toLowerCase();
    if (!term) return true;
    const nameMatch = row.name && row.name.toLowerCase().includes(term);
    const urlMatch = row.url && row.url.toLowerCase().includes(term);
    return nameMatch || urlMatch;
  });

  // 2. Sort filtered list
  const sortedUrls = [...filteredUrls].sort((a, b) => {
    let valA = a[sortField];
    let valB = b[sortField];

    if (sortField === "url") {
      valA = (a.name || a.url).toLowerCase();
      valB = (b.name || b.url).toLowerCase();
    } else if (sortField === "latest_is_up") {
      valA = a.latest_is_up === true ? 1 : a.latest_is_up === false ? 0 : -1;
      valB = b.latest_is_up === true ? 1 : b.latest_is_up === false ? 0 : -1;
    } else if (sortField === "latest_response_time_ms") {
      valA = a.latest_response_time_ms !== null && a.latest_response_time_ms !== undefined ? a.latest_response_time_ms : -1;
      valB = b.latest_response_time_ms !== null && b.latest_response_time_ms !== undefined ? b.latest_response_time_ms : -1;
    } else if (sortField === "latest_checked_at") {
      valA = a.latest_checked_at ? new Date(a.latest_checked_at).getTime() : 0;
      valB = b.latest_checked_at ? new Date(b.latest_checked_at).getTime() : 0;
    }

    if (valA < valB) return sortDirection === "asc" ? -1 : 1;
    if (valA > valB) return sortDirection === "asc" ? 1 : -1;
    return 0;
  });

  // Renders the tiny sparkline chart for the latency trend column
  const renderSparkline = (recentChecks) => {
    if (!recentChecks || recentChecks.length === 0) {
      return <span className="text-muted">-</span>;
    }
    const chartData = recentChecks.map((c, i) => ({
      index: i,
      latency: c.response_time_ms || 0,
    }));

    return (
      <div style={{ width: "100px", height: "30px", margin: "0 auto" }}>
        <LineChart width={100} height={30} data={chartData}>
          <Line
            type="monotone"
            dataKey="latency"
            stroke="#6366f1"
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </div>
    );
  };

  // Render Skeletons during Loading state
  if (loading) {
    return (
      <div className="table-responsive-container">
        <table className="urls-data-table">
          <thead>
            <tr>
              <th>Monitored URL</th>
              <th className="text-center">Status</th>
              <th className="text-center">HTTP Status</th>
              <th className="text-center">Latency Trend</th>
              <th className="text-right">Latest Latency</th>
              <th className="text-center">Last Checked</th>
              <th className="text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            {[1, 2, 3, 4].map((n) => (
              <tr key={n} className="skeleton-row">
                <td>
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                    <div className="skeleton-bar" style={{ width: "45%" }}></div>
                    <div className="skeleton-bar" style={{ width: "75%" }}></div>
                  </div>
                </td>
                <td><div className="skeleton-bar" style={{ width: "65px", margin: "0 auto" }}></div></td>
                <td><div className="skeleton-bar" style={{ width: "35px", margin: "0 auto" }}></div></td>
                <td><div className="skeleton-bar" style={{ width: "90px", margin: "0 auto" }}></div></td>
                <td><div className="skeleton-bar" style={{ width: "55px", marginLeft: "auto" }}></div></td>
                <td><div className="skeleton-bar" style={{ width: "75px", margin: "0 auto" }}></div></td>
                <td><div className="skeleton-bar" style={{ width: "160px", margin: "0 auto" }}></div></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <div>
      {/* Instant Search Bar */}
      <div className="filter-search-container">
        <input
          type="text"
          className="search-input-field"
          placeholder="Search monitors by URL or friendly name..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* Empty States */}
      {!urls || urls.length === 0 ? (
        <div className="empty-state-card">
          <p className="empty-state-text">No URL monitors registered yet</p>
          <p className="empty-state-subtext">Add a website URL in the form above to start monitoring availability and response time.</p>
        </div>
      ) : sortedUrls.length === 0 ? (
        <div className="empty-state-card">
          <p className="empty-state-text">No matching monitors found</p>
          <p className="empty-state-subtext">Try refining your search text or add a new URL monitor.</p>
        </div>
      ) : (
        <div className="table-responsive-container">
          <table className="urls-data-table">
            <thead>
              <tr>
                <th className="sortable-header" onClick={() => handleSort("url")}>
                  Monitored URL{renderSortIndicator("url")}
                </th>
                <th className="text-center sortable-header" onClick={() => handleSort("latest_is_up")}>
                  Status{renderSortIndicator("latest_is_up")}
                </th>
                <th className="text-center">HTTP Status</th>
                <th className="text-center">Latency Trend (Last 10)</th>
                <th className="text-right sortable-header" onClick={() => handleSort("latest_response_time_ms")}>
                  Latest Latency{renderSortIndicator("latest_response_time_ms")}
                </th>
                <th className="text-center sortable-header" onClick={() => handleSort("latest_checked_at")}>
                  Last Checked{renderSortIndicator("latest_checked_at")}
                </th>
                <th className="text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              {sortedUrls.map((row) => {
                const isDeleting = deletingId === row.id;
                const isChecking = checkingIds.includes(row.id);
                
                let statusClass = "status-badge pending";
                let statusText = "PENDING";

                if (isChecking) {
                  statusClass = "status-badge checking";
                  statusText = "CHECKING";
                } else if (row.latest_is_up === true) {
                  statusClass = "status-badge up";
                  statusText = "UP";
                } else if (row.latest_is_up === false) {
                  statusClass = "status-badge down";
                  statusText = "DOWN";
                }

                return (
                  <tr key={row.id} className={isDeleting ? "row-deleting" : ""}>
                    <td>
                      <div className="url-info">
                        <span className="url-display-name">
                          {row.name || "Unnamed Monitor"}
                        </span>
                        <a
                          href={row.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="url-display-link"
                        >
                          {row.url}
                        </a>
                      </div>
                    </td>
                    <td className="text-center">
                      <span className={statusClass}>
                        <span className="status-dot"></span>
                        {statusText}
                      </span>
                    </td>
                    <td className="text-center">
                      <span className={`status-code ${row.latest_status_code ? "has-code" : "no-code"}`}>
                        {row.latest_status_code || "-"}
                      </span>
                    </td>
                    <td className="text-center">
                      {renderSparkline(row.recent_checks)}
                    </td>
                    <td className="text-right font-numeric">
                      {formatLatency(row.latest_response_time_ms)}
                    </td>
                    <td className="text-center font-numeric">
                      {formatTimestamp(row.latest_checked_at)}
                    </td>
                    <td className="text-center">
                      <div className="action-buttons-group">
                        <button
                          className="check-action-button"
                          onClick={(e) => handleManualCheck(e, row.id)}
                          disabled={isDeleting || isChecking}
                          aria-label={`Check now for ${row.name || row.url}`}
                        >
                          {isChecking ? "Checking..." : "Check Now"}
                        </button>
                        <button
                          className="delete-action-button"
                          onClick={(e) => handleDelete(e, row.id, row.name, row.url)}
                          disabled={isDeleting || isChecking}
                          aria-label={`Delete monitor for ${row.name || row.url}`}
                        >
                          {isDeleting ? "Deleting..." : "Delete"}
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default UrlsTable;
