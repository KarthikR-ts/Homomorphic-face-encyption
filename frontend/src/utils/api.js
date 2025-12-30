/**
 * API Configuration for Homomorphic Face Encryption Frontend
 * 
 * This module handles API URL configuration across different environments:
 * - Development: Uses Vite proxy (relative URLs)
 * - Production: Uses VITE_API_URL environment variable
 */

// Get the API base URL from environment variables
// In production, this should be set to the backend Railway service URL
const getApiBaseUrl = () => {
  // In production build, use the environment variable
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }

  // In development, use relative URLs (handled by Vite proxy)
  // or fallback to localhost
  if (import.meta.env.DEV) {
    return '';  // Empty string means relative URLs
  }

  // Production fallback - use relative URLs assuming same-origin or nginx proxy
  return '';
};

export const API_BASE_URL = getApiBaseUrl();

/**
 * Make an API request with proper URL handling
 * @param {string} endpoint - The API endpoint (e.g., '/api/auth/token')
 * @param {RequestInit} options - Fetch options
 * @returns {Promise<Response>}
 */
export const apiRequest = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;

  // Add default headers
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  return fetch(url, {
    ...options,
    headers,
  });
};

/**
 * Make an authenticated API request
 * @param {string} endpoint - The API endpoint
 * @param {string} token - JWT token
 * @param {RequestInit} options - Fetch options
 * @returns {Promise<Response>}
 */
export const authenticatedRequest = async (endpoint, token, options = {}) => {
  return apiRequest(endpoint, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
    },
  });
};

export default {
  API_BASE_URL,
  apiRequest,
  authenticatedRequest,
};
