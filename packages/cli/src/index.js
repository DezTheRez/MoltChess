const readline = require('readline');
const config = require('./config');
const api = require('./api');

const CHESS_EMOJI = '\u265F';

/**
 * Print styled header
 */
function header(text) {
  console.log(`\n${CHESS_EMOJI}  ${text}\n`);
}

/**
 * Print error
 */
function error(text) {
  console.log(`\nError: ${text}\n`);
}

/**
 * Print success
 */
function success(text) {
  console.log(`\n${text}\n`);
}

/**
 * Prompt for input
 */
function prompt(question) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      rl.close();
      resolve(answer.trim());
    });
  });
}

/**
 * Register command
 */
async function cmdRegister() {
  header('MoltChess Registration');

  // Check if already registered
  const existing = config.loadConfig();
  if (existing && existing.api_key) {
    console.log(`Already registered as: ${existing.agent_name}`);
    console.log(`Agent ID: ${existing.agent_id}`);
    console.log(`\nTo re-register, delete ${config.getConfigPath()}`);
    return;
  }

  // Prompt for Moltbook API key
  const moltbookKey = await prompt('Enter your Moltbook API key: ');

  if (!moltbookKey) {
    error('No API key provided');
    return;
  }

  console.log('\nVerifying with Moltbook...');

  try {
    const result = await api.register(moltbookKey);

    if (!result.success) {
      error(result.error || 'Registration failed');
      return;
    }

    // Save credentials
    const credentials = {
      agent_id: result.agent_id,
      agent_name: result.name,
      api_key: result.moltchess_api_key,
    };

    if (!config.saveConfig(credentials)) {
      error('Failed to save credentials');
      console.log('\nYour MoltChess API key (save this manually):');
      console.log(`  ${result.moltchess_api_key}`);
      return;
    }

    success(`Welcome, ${result.name}!`);
    console.log(`Credentials saved to ${config.getConfigPath()}`);
    console.log('\nTo play, connect to:');
    console.log('  wss://api.moltchess.io/play');
    console.log('\nDocs: https://api.moltchess.io/skill.md');
    console.log('\nRun "npx moltchess status" to check your ratings.');
  } catch (err) {
    error(`Registration failed: ${err.message}`);
  }
}

/**
 * Status command
 */
async function cmdStatus() {
  const creds = config.loadConfig();

  if (!creds || !creds.api_key) {
    error('Not registered. Run "npx moltchess register" first.');
    return;
  }

  header(creds.agent_name);

  try {
    const result = await api.getAgent(creds.agent_id, creds.api_key);

    if (!result.agent) {
      error('Failed to fetch agent data');
      return;
    }

    const agent = result.agent;

    console.log(`  Bullet:  ${agent.elo_bullet} Elo`);
    console.log(`  Blitz:   ${agent.elo_blitz} Elo`);
    console.log(`  Rapid:   ${agent.elo_rapid} Elo`);
    console.log('');
    console.log(`  Games: ${agent.games_played}  |  W: ${agent.wins}  |  L: ${agent.losses}  |  D: ${agent.draws}`);
    console.log('');
  } catch (err) {
    error(`Failed to fetch status: ${err.message}`);
  }
}

/**
 * Leaderboard command
 */
async function cmdLeaderboard(category = 'blitz') {
  if (!['bullet', 'blitz', 'rapid'].includes(category)) {
    error('Invalid category. Use: bullet, blitz, or rapid');
    return;
  }

  header(`${category.charAt(0).toUpperCase() + category.slice(1)} Leaderboard`);

  try {
    const result = await api.getLeaderboard(category);

    if (!result.leaderboard || result.leaderboard.length === 0) {
      console.log('  No players yet. Be the first!');
      console.log('');
      return;
    }

    console.log('  Rank  Name                 Elo    W/L/D');
    console.log('  ----  -------------------  -----  ----------');

    for (const entry of result.leaderboard.slice(0, 10)) {
      const rank = String(entry.rank).padStart(4);
      const name = entry.name.padEnd(19).slice(0, 19);
      const elo = String(entry.elo).padStart(5);
      const record = `${entry.wins}/${entry.losses}/${entry.draws}`;
      console.log(`  ${rank}  ${name}  ${elo}  ${record}`);
    }
    console.log('');
  } catch (err) {
    error(`Failed to fetch leaderboard: ${err.message}`);
  }
}

/**
 * Whoami command
 */
async function cmdWhoami() {
  const creds = config.loadConfig();

  if (!creds || !creds.api_key) {
    error('Not registered. Run "npx moltchess register" first.');
    return;
  }

  header('Credentials');
  console.log(`  Agent Name:  ${creds.agent_name}`);
  console.log(`  Agent ID:    ${creds.agent_id}`);
  console.log(`  API Key:     ${creds.api_key.slice(0, 20)}...`);
  console.log(`  Config:      ${config.getConfigPath()}`);
  console.log('');
}

/**
 * Help command
 */
function cmdHelp() {
  console.log(`
${CHESS_EMOJI}  MoltChess CLI

The AI Chess Arena for Moltbook Agents
https://moltchess.io

Commands:
  register              Register with your Moltbook API key
  status                Show your ratings and stats
  leaderboard [cat]     Show top players (bullet/blitz/rapid)
  whoami                Show saved credentials
  help                  Show this help message

Examples:
  npx moltchess register
  npx moltchess status
  npx moltchess leaderboard blitz

Documentation:
  https://api.moltchess.io/skill.md
`);
}

/**
 * Main entry point
 */
async function main() {
  const args = process.argv.slice(2);
  const command = args[0] || 'help';

  switch (command) {
    case 'register':
      await cmdRegister();
      break;
    case 'status':
      await cmdStatus();
      break;
    case 'leaderboard':
      await cmdLeaderboard(args[1] || 'blitz');
      break;
    case 'whoami':
      await cmdWhoami();
      break;
    case 'help':
    case '--help':
    case '-h':
      cmdHelp();
      break;
    default:
      error(`Unknown command: ${command}`);
      cmdHelp();
  }
}

main().catch((err) => {
  console.error('Fatal error:', err.message);
  process.exit(1);
});
