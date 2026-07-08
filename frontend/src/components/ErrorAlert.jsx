import React from "react";

/**
 * Renders a visually clean, floating glassmorphism alert banner when an error occurs.
 * 
 * @param {Object} props
 * @param {string} props.message - Error notification text.
 * @param {Function} props.onClose - Action callback when dismiss is clicked.
 */
export function ErrorAlert({ message, onClose }) {
  if (!message) return null;

  return (
    <div className="error-alert-container">
      <div className="error-alert-content">
        <span className="error-alert-icon">⚠️</span>
        <div className="error-alert-message">{message}</div>
        <button className="error-alert-close" onClick={onClose} aria-label="Close error message">
          &times;
        </button>
      </div>
    </div>
  );
}

export default ErrorAlert;
