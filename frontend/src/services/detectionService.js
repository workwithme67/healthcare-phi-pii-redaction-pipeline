/**
 * detectionService.js
 * Axios wrappers for the Day 3 detection engine API endpoints.
 * Base URL: /api  (no v1 prefix, as per spec)
 */

import axios from 'axios';

const detectionClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL
    ? import.meta.env.VITE_API_URL.replace('/api/v1', '/api')
    : '/api',
  headers: { 'Content-Type': 'application/json' },
});

const detectionService = {
  /**
   * POST /api/detect
   * @param {string} text - Clinical note text to scan
   * @returns {{ success, entities, entity_count, processing_time_ms }}
   */
  detect: async (text) => {
    const response = await detectionClient.post('/detect', { text });
    return response.data;
  },

  /**
   * POST /api/redact
   * @param {string} text - Clinical note text to redact
   * @returns {{ success, redacted_text, entities, entity_count, processing_time_ms }}
   */
  redact: async (text) => {
    const response = await detectionClient.post('/redact', { text });
    return response.data;
  },

  /**
   * GET /api/statistics
   * @returns {{ total_notes_processed, total_entities_found, entity_counts_by_type, average_detection_time_ms }}
   */
  getStatistics: async () => {
    const response = await detectionClient.get('/statistics');
    return response.data;
  },
};

export default detectionService;
