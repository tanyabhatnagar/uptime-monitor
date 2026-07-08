import React, { useState, useEffect } from "react";
import apiService from "./services/api";
import useInterval from "./hooks/useInterval";
import AddUrlForm from "./components/AddUrlForm";
import UrlsTable from "./components/UrlsTable";
import ErrorAlert from "./components/ErrorAlert";
import SummaryCards from "./components/SummaryCards";

export function App() {
  const [urls, setUrls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isOffline, setIsOffline] = useState(false);

  // Core API query function
  const fetchUrls = async (isInitial = false) => {
    if (isInitial) setLoading(true);
    try {
      const data = await apiService.getUrls();
      setUrls(data);
      setIsOffline(false);
      setError(null); // Clear errors on a successful fetch
    } catch (err) {
      console.error("Error fetching URLs:", err);
      if (err.request && !err.response) {
        setIsOffline(true);
        setError("Backend server is offline or unreachable. Auto-refresh is paused.");
      } else {
        setError("Failed to fetch monitored URLs from database.");
      }
    } finally {
      if (isInitial) setLoading(false);
    }
  };

  // Fetch initial list on mount
  useEffect(() => {
    fetchUrls(true);
  }, []);

  // Poll the API every 10 seconds to update metrics dynamically
  useInterval(() => {
    fetchUrls(false);
  }, 10000);

  const handleRegistrationSuccess = () => {
    fetchUrls(false);
  };

  return (
    <div className="app-container">
      {/* App Header Bar */}
      <header className="app-header">
        <div className="brand-section">
          <span className="logo-icon" role="img" aria-label="Globe logo">🌐</span>
          <h1 className="app-title">Uptime Monitor Dashboard</h1>
        </div>
        <div className="auto-refresh-indicator">
          <span className="refresh-spinner-dot"></span>
          <span>{isOffline ? "Auto-refresh paused" : "Auto-refreshing every 10s"}</span>
        </div>
      </header>

      {/* Floating Error Alerts */}
      <ErrorAlert message={error} onClose={() => setError(null)} />

      {/* Persistent Offline Warning Banner */}
      {isOffline && (
        <div className="error-alert-container" style={{ animation: "none" }}>
          <div className="error-alert-content" style={{ borderStyle: "dashed" }}>
            <span className="error-alert-icon">🔌</span>
            <div className="error-alert-message">
              Connection lost. The backend monitoring server is currently offline. Metrics will update automatically once reconnected.
            </div>
          </div>
        </div>
      )}

      {/* Dashboard Summary Cards */}
      <SummaryCards urls={urls} />

      {/* Add URL registration form */}
      <AddUrlForm onSuccess={handleRegistrationSuccess} onError={setError} />

      {/* Main Table view of current monitors (supports Skeletons) */}
      <UrlsTable
        urls={urls}
        onDeleteSuccess={handleRegistrationSuccess}
        onError={setError}
        loading={loading}
      />
    </div>
  );
}

export default App;
