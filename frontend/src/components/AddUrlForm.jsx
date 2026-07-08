import React, { useState } from "react";
import apiService from "../services/api";

/**
 * Form component to register a new website for uptime monitoring.
 * Handles validation, loading states, and registers callbacks on success/error.
 * 
 * @param {Object} props
 * @param {Function} props.onSuccess - Callback triggered after successful registration.
 * @param {Function} props.onError - Callback triggered with error messages.
 */
export function AddUrlForm({ onSuccess, onError }) {
  const [url, setUrl] = useState("");
  const [name, setName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    onError(null); // Clear previous errors

    const targetUrl = url.trim();
    const targetName = name.trim() || null;

    // Client-side quick check
    if (!targetUrl.startsWith("http://") && !targetUrl.startsWith("https://")) {
      onError("URL must start with 'http://' or 'https://'");
      return;
    }

    setIsSubmitting(true);
    try {
      await apiService.addUrl(targetUrl, targetName);
      setUrl(""); // Reset form fields on success
      setName("");
      onSuccess(); // Request list reload from parent
    } catch (err) {
      if (err.response) {
        // Backend returned specific error (e.g. 400 Bad Request: URL already registered)
        const errMsg = err.response.data?.detail || "Failed to register URL.";
        onError(errMsg);
      } else if (err.request) {
        // Backend server is unreachable
        onError("Backend server is currently offline or unreachable.");
      } else {
        onError("An unexpected error occurred. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form className="add-url-form" onSubmit={handleSubmit}>
      <h2 className="form-title">Register Monitor</h2>
      <div className="form-row">
        <div className="input-group">
          <label htmlFor="url-input">Website URL *</label>
          <input
            id="url-input"
            type="text"
            placeholder="https://example.com"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={isSubmitting}
            required
            autoComplete="off"
          />
        </div>

        <div className="input-group">
          <label htmlFor="name-input">Friendly Name</label>
          <input
            id="name-input"
            type="text"
            placeholder="e.g. My Website"
            value={name}
            onChange={(e) => setName(e.target.value)}
            disabled={isSubmitting}
            autoComplete="off"
          />
        </div>

        <button type="submit" className="submit-button" disabled={isSubmitting}>
          {isSubmitting ? "Registering..." : "Add Monitor"}
        </button>
      </div>
      <p className="form-helper">Urls must include the protocol (http:// or https://).</p>
    </form>
  );
}

export default AddUrlForm;
