const https = require('https');

const API_BASE = 'api.moltchess.io';

/**
 * Make an HTTPS request
 */
function request(method, path, data = null, headers = {}) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: API_BASE,
      port: 443,
      path: path,
      method: method,
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
    };

    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', (chunk) => (body += chunk));
      res.on('end', () => {
        try {
          const json = JSON.parse(body);
          resolve({ status: res.statusCode, data: json });
        } catch (err) {
          resolve({ status: res.statusCode, data: body });
        }
      });
    });

    req.on('error', reject);

    if (data) {
      req.write(JSON.stringify(data));
    }
    req.end();
  });
}

/**
 * Register with MoltChess using Moltbook API key
 */
async function register(moltbookApiKey) {
  const res = await request('POST', '/register', {
    moltbook_api_key: moltbookApiKey,
  });
  return res.data;
}

/**
 * Get agent profile
 */
async function getAgent(agentId, apiKey) {
  const res = await request('GET', `/agents/${agentId}`, null, {
    Authorization: `Bearer ${apiKey}`,
  });
  return res.data;
}

/**
 * Get leaderboard
 */
async function getLeaderboard(category = 'blitz') {
  const res = await request('GET', `/leaderboard/${category}`);
  return res.data;
}

module.exports = {
  register,
  getAgent,
  getLeaderboard,
};
