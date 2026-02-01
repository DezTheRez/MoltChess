const fs = require('fs');
const path = require('path');
const os = require('os');

const CONFIG_FILE = path.join(os.homedir(), '.moltchess.json');

/**
 * Load config from ~/.moltchess.json
 */
function loadConfig() {
  try {
    if (fs.existsSync(CONFIG_FILE)) {
      const data = fs.readFileSync(CONFIG_FILE, 'utf8');
      return JSON.parse(data);
    }
  } catch (err) {
    // Ignore errors, return null
  }
  return null;
}

/**
 * Save config to ~/.moltchess.json
 */
function saveConfig(config) {
  try {
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2));
    return true;
  } catch (err) {
    console.error('Failed to save config:', err.message);
    return false;
  }
}

/**
 * Check if already registered
 */
function isRegistered() {
  const config = loadConfig();
  return config && config.api_key;
}

/**
 * Get the config file path
 */
function getConfigPath() {
  return CONFIG_FILE;
}

module.exports = {
  loadConfig,
  saveConfig,
  isRegistered,
  getConfigPath,
};
