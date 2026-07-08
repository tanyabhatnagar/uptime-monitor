import axios from "axios";

// Read API URL from environment variables or default to localhost:8000
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 10000, // 10-second client-side timeout matching backend limit
});

export const apiService = {
  /**
   * Fetches all monitored URLs alongside their latest health checks.
   */
  async getUrls() {
    const response = await apiClient.get("/urls");
    return response.data;
  },

  /**
   * Registers a new URL.
   * @param {string} url - The target URL (must include http/https protocol).
   * @param {string|null} name - Optional label description.
   */
  async addUrl(url, name) {
    const response = await apiClient.post("/urls", { url, name });
    return response.data;
  },

  /**
   * Deletes a URL and cancels its background monitoring thread.
   * @param {number} id - Target URL database key.
   */
  async deleteUrl(id) {
    const response = await apiClient.delete(`/urls/${id}`);
    return response.data;
  },

  /**
   * Retrieves up to 100 recent health checks for a single monitor.
   * @param {number} id - Target URL database key.
   */
  async getUrlHistory(id) {
    const response = await apiClient.get(`/history/${id}`);
    return response.data;
  },
};

export default apiService;
