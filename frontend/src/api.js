/**
 * API client for the FastAPI backend.
 *
 * All AI features funnel through `POST /home` with:
 *   - intent  (string)
 *   - prompt  (string)
 *   - file    (optional File)
 *
 * Supported intents:
 *   text_gen | summarize | image_create | image_editor | speech_generation | music_generation
 */

const API_BASE = 'http://localhost:8000';

/**
 * Send a prompt to the backend.
 * @param {string} intent - The intent type
 * @param {string} prompt - The user prompt
 * @param {File|null} file - Optional file attachment
 * @returns {Promise<object>} - The JSON response
 */
export async function sendPrompt(intent, prompt, file = null) {
  const formData = new FormData();
  formData.append('intent', intent);
  formData.append('prompt', prompt);
  if (file) {
    formData.append('file', file);
  }

  const response = await fetch(`${API_BASE}/home`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Request failed with status ${response.status}`);
  }

  return response.json();
}

/**
 * Get a URL to a generated file on the backend.
 * @param {string} filePath - The absolute file path from the backend response
 * @returns {string} - The URL to fetch the file
 */
export function getFileUrl(filePath) {
  const filename = filePath.split('/').pop();
  return `${API_BASE}/files/${filename}`;
}
