import React from "react";

/**
 * Component to render summary cards at the top of the Uptime Monitor Dashboard.
 * 
 * @param {Object} props
 * @param {Array} props.urls - List of all monitored URLs.
 */
export function SummaryCards({ urls }) {
  const total = urls.length;
  
  const healthy = urls.filter((u) => u.latest_is_up === true).length;
  
  const down = urls.filter((u) => u.latest_is_up === false).length;
  
  // Calculate average response time of URLs that are UP and have valid latency values
  const latencyUrls = urls.filter(
    (u) => u.latest_is_up === true && u.latest_response_time_ms !== null && u.latest_response_time_ms !== undefined
  );
  const avgResponseTime =
    latencyUrls.length > 0
      ? latencyUrls.reduce((acc, curr) => acc + curr.latest_response_time_ms, 0) / latencyUrls.length
      : 0;

  return (
    <div className="summary-cards-container">
      {/* Total Card */}
      <div className="summary-card total">
        <div className="card-header">
          <span className="card-title">Total Monitored</span>
          <span className="card-icon">📊</span>
        </div>
        <div className="card-value font-numeric">{total}</div>
        <div className="card-subtext">Registered endpoints</div>
      </div>

      {/* Healthy Card */}
      <div className="summary-card healthy">
        <div className="card-header">
          <span className="card-title">Healthy</span>
          <span className="card-icon">🟢</span>
        </div>
        <div className="card-value font-numeric">{healthy}</div>
        <div className="card-subtext">
          {total > 0 ? `${((healthy / total) * 100).toFixed(0)}% of total` : "No monitors"}
        </div>
      </div>

      {/* Down Card */}
      <div className="summary-card down">
        <div className="card-header">
          <span className="card-title">Down</span>
          <span className="card-icon">🔴</span>
        </div>
        <div className="card-value font-numeric">{down}</div>
        <div className="card-subtext">
          {down > 0 ? "Requires attention" : "All systems operational"}
        </div>
      </div>

      {/* Latency Card */}
      <div className="summary-card latency">
        <div className="card-header">
          <span className="card-title">Avg Latency</span>
          <span className="card-icon">⚡</span>
        </div>
        <div className="card-value font-numeric">
          {avgResponseTime > 0 ? `${avgResponseTime.toFixed(1)} ms` : "-"}
        </div>
        <div className="card-subtext">For active green routes</div>
      </div>
    </div>
  );
}

export default SummaryCards;
