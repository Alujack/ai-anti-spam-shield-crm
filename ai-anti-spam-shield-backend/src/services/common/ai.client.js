const axios = require('axios');
const FormData = require('form-data');
const logger = require('../../utils/logger');

class AIClient {
  constructor() {
    this.baseUrl = process.env.AI_SERVICE_URL || 'http://localhost:8000';
    this.apiKey = process.env.AI_API_KEY;

    this.client = axios.create({
      baseURL: this.baseUrl,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        ...(this.apiKey && { 'X-API-Key': this.apiKey }),
      },
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => this.handleError(error)
    );
  }

  handleError(error) {
    if (error.code === 'ECONNREFUSED') {
      logger.error('AI service unavailable', { url: this.baseUrl });
      throw new Error('AI service unavailable');
    }

    if (error.code === 'ETIMEDOUT' || error.code === 'ECONNABORTED') {
      logger.error('AI service timeout');
      throw new Error('AI service timeout');
    }

    if (error.response) {
      const { status, data } = error.response;
      logger.error('AI service error', { status, data });
      throw new Error(data?.detail || `AI service error: ${status}`);
    }

    throw error;
  }

  /**
   * Predict spam for text message
   */
  async predictText(message, version = 'v1') {
    const endpoint = version === 'v2' ? '/predict-v2' : '/predict';

    logger.debug('Calling AI service for text prediction', {
      endpoint,
      messageLength: message.length,
    });

    const response = await this.client.post(endpoint, { message });
    return response.data;
  }

  /**
   * Predict spam for voice message
   */
  async predictVoice(audioBuffer, filename, mimeType, version = 'v1') {
    const endpoint = version === 'v2' ? '/predict-voice-v2' : '/predict-voice';

    const formData = new FormData();
    formData.append('audio', audioBuffer, {
      filename,
      contentType: mimeType,
    });

    logger.debug('Calling AI service for voice prediction', {
      endpoint,
      filename,
    });

    const response = await this.client.post(endpoint, formData, {
      headers: formData.getHeaders(),
      timeout: 60000, // Voice processing takes longer
    });

    return response.data;
  }

  /**
   * Predict phishing for text
   */
  async predictPhishing(text) {
    logger.debug('Calling AI service for phishing prediction', {
      textLength: text.length,
    });

    const response = await this.client.post('/predict-phishing', {
      text,
      scan_type: 'text',
    });

    return response.data;
  }

  /**
   * Scan URL for phishing
   */
  async scanUrl(url) {
    logger.debug('Calling AI service for URL scan', { url });

    const response = await this.client.post('/scan-url', { url });
    return response.data;
  }

  /**
   * Deep URL analysis (Phase 3)
   */
  async analyzeUrlDeep(url) {
    logger.debug('Calling AI service for deep URL analysis', { url });

    const response = await this.client.post('/analyze-url-deep', {
      url,
      include_screenshot: false,
    });

    return response.data;
  }

  /**
   * Health check
   */
  async healthCheck() {
    try {
      const response = await this.client.get('/health');
      return response.data;
    } catch (error) {
      return { status: 'unhealthy', error: error.message };
    }
  }
}

module.exports = new AIClient();
