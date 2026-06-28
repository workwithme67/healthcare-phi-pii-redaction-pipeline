/**
 * aiDetectionService.js
 * Day 4 — AI-Powered PHI/PII Detection API Service
 *
 * Provides functions for:
 *   - detectAI(text)        → POST /api/detect-ai
 *   - compareDetection(text) → POST /api/compare
 */

import axios from 'axios';

// Use the same base URL configuration as the main api.js
const AI_API_BASE = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL.replace('/v1', '')
  : '/api';

const aiApiClient = axios.create({
  baseURL: AI_API_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 60_000, // 60s — NLP models can be slow on cold start
});

const aiDetectionService = {
  /**
   * Run Presidio + spaCy AI pipeline on the given text.
   * @param {string} text - Clinical note or freeform text.
   * @returns {Promise<import('./types').AIDetectResponse>}
   */
  detectAI: async (text) => {
    const response = await aiApiClient.post('/detect-ai', { text });
    return response.data;
  },

  /**
   * Run all three engines (Regex, Presidio, spaCy) and return comparison stats.
   * @param {string} text - Text to compare detection engines on.
   * @returns {Promise<import('./types').CompareResponse>}
   */
  compareDetection: async (text) => {
    const response = await aiApiClient.post('/compare', { text });
    return response.data;
  },
};

export default aiDetectionService;
