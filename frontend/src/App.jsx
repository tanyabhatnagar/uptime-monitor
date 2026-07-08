import React, { useState, useEffect } from "react";
import apiService from "./services/api";
import useInterval from "./hooks/useInterval";
import AddUrlForm from "./components/AddUrlForm";
import UrlsTable from "./components/UrlsTable";
import ErrorAlert from "./components/ErrorAlert";

export function App() {
  const [urls, setUrls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Core API query function
  const fetchUrls = async (isInitial = false) => {
    if (isInitial) setLoading(true);
    try {
      const data = await apiService.getUrls();
      setUrls(data);
      setError(null); // Clear errors on a successful fetch
    } catch (err) {
      console.error("Error fetching URLs:", err);
      if (err.request && !err.response) {
        setError("Backend server is offline or unreachable. Checks are paused.");
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
          <span>Auto-refreshing every 10s</span>
        </div>
      </header>

      {/* Floating Error Alerts */}
      <ErrorAlert message={error} onClose={() => setError(null)} />

      {/* Add URL registration form */}
      <AddUrlForm onSuccess={handleRegistrationSuccess} onError={setError} />

      {/* Main Table view of current monitors */}
      {loading ? (
        <div className="loading-view">
          <div className="spinner-icon"></div>
          <p>Loading active monitors...</p>
        </div>
      ) : (
        <UrlsTable
          urls={urls}
          onDeleteSuccess={handleRegistrationSuccess}
          onError={setError}
        />
      )}
    </div>
  );
}

export default App;
