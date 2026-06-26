import axios from 'axios';

// In development, Vite proxies '/api' to 'http://localhost:8000/api'
const API_BASE = '/api';

const uploadClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const uploadService = {
  /**
   * Upload a raw text clinical note.
   * @param {string} noteText - The raw clinical note text.
   * @returns {Promise<object>} - Response with success state and note_id.
   */
  uploadText: async (noteText) => {
    const response = await uploadClient.post('/upload-text', { note: noteText });
    return response.data;
  },

  /**
   * Upload a TXT or PDF file.
   * @param {File} file - The file object to upload.
   * @param {function} onUploadProgress - Axios progress callback function.
   * @returns {Promise<object>} - Metadata of the uploaded file.
   */
  uploadFile: async (file, onUploadProgress) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await uploadClient.post('/upload-file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress, // For real-time progress bar
    });
    return response.data;
  },

  /**
   * List all uploaded clinical notes and files.
   * @returns {Promise<Array>} - List of uploads.
   */
  listUploads: async () => {
    const response = await uploadClient.get('/uploads');
    return response.data;
  },

  /**
   * Get full details of a specific upload (including content/text).
   * @param {string} id - The UUID of the upload.
   * @returns {Promise<object>} - Detailed upload object.
   */
  getUploadDetails: async (id) => {
    const response = await uploadClient.get(`/uploads/${id}`);
    return response.data;
  },

  /**
   * Delete a specific upload from database and disk.
   * @param {string} id - The UUID of the upload to delete.
   * @returns {Promise<object>} - Success confirmation.
   */
  deleteUpload: async (id) => {
    const response = await uploadClient.delete(`/uploads/${id}`);
    return response.data;
  },
};

export default uploadService;
