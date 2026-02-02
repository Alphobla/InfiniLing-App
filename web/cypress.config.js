const { defineConfig } = require('cypress')

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://localhost:5173',
    viewportWidth: 1280,
    viewportHeight: 720,
    defaultCommandTimeout: 10000,
    env: {
      apiUrl: 'http://localhost:8000'
    },
    setupNodeEvents(on, config) {
      // Node event listeners
    }
  }
})
