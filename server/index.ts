import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const pythonApp = spawn('python', ['app.py'], {
  cwd: join(__dirname, '..'),
  stdio: 'inherit',
  env: {
    ...process.env,
    FLASK_ENV: 'development',
    FLASK_DEBUG: '1'
  }
});

pythonApp.on('error', (err) => {
  console.error('Failed to start Python Flask application:', err);
  process.exit(1);
});

pythonApp.on('close', (code) => {
  console.log(`Flask application exited with code ${code}`);
  process.exit(code || 0);
});

process.on('SIGINT', () => {
  pythonApp.kill('SIGINT');
});

process.on('SIGTERM', () => {
  pythonApp.kill('SIGTERM');
});
