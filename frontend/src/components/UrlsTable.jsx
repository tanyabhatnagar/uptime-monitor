import React, { useState } from "react";
import apiService from "../services/api";

/**
 * Renders the table of monitored URLs.
 * Shows status badges, latency charts, timestamps, and delete controls.
 * 
 * @param {Object} props
 * @param {Array} props.urls - List of URLs with their health metadata.
 * @param {Function} props.onDeleteSuccess - Callback triggered after deleting a URL.
 * @param {Function} props.onError - Callback triggered to display errors.
 */
export function UrlsTable({ urls, onDeleteSuccess, onError }) {
  const [deletingId, setDeletingId] = useState(null);

  const handleDelete = async (id, name, urlStr) => {
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

  if (!urls || urls.length === 0) {
    return (
      <div className="empty-state-card">
        <p className="empty-state-text">No URL monitors registered yet.</p>
        <p className="empty-state-subtext">Add a website URL in the form above to start monitoring.</p>
      </div>
    );
  }

  return (
    <div className="table-responsive-container">
      <table className="urls-data-table">
        <thead>
          <tr>
            <th>Monitored URL</th>
            <th className="text-center">Status</th>
            <th className="text-center">HTTP Status</th>
            <th className="text-right">Latest Latency</th>
            <th className="text-center">Last Checked</th>
            <th className="text-center">Actions</th>
          </tr>
        </thead>
        <tbody>
          {urls.map((row) => {
            const isDeleting = deletingId === row.id;
            let statusClass = "status-badge pending";
            let statusText = "PENDING";

            if (row.latest_is_up === true) {
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
                    <span className="url-display-name">{row.name || "Unnamed Monitor"}</span>
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
                <td className="text-right font-numeric">
                  {formatLatency(row.latest_response_time_ms)}
                </td>
                <td className="text-center font-numeric">
                  {formatTimestamp(row.latest_checked_at)}
                </td>
                <td className="text-center">
                  <button
                    className="delete-action-button"
                    onClick={() => handleDelete(row.id, row.name, row.url)}
                    disabled={isDeleting}
                    aria-label={`Delete monitor for ${row.name || row.url}`}
                  >
                    {isDeleting ? "Deleting..." : "Delete"}
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default UrlsTable;
