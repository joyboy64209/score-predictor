const { app, BrowserWindow } = require('electron');
const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const { spawn } = require('child_process');
const fs = require('fs');
const http = require('http');
const path = require('path');

const BACKEND_URL = process.env.MATCH_PREDICTOR_BACKEND_URL || 'http://localhost:3001';

function getFrontendDistPath() {
  if (app.isPackaged) {
    return path.join(app.getAppPath(), 'frontend', 'dist');
  }

  return path.join(__dirname, '..', 'frontend', 'dist');
}

async function startLocalServer() {
  const distPath = getFrontendDistPath();
  const server = express();

  server.use(
    '/api',
    createProxyMiddleware({
      target: BACKEND_URL,
      changeOrigin: true,
      secure: false,
      ws: true,
      logLevel: 'silent',
    }),
  );

  server.use(express.static(distPath));
  server.get('*', (_req, res) => res.sendFile(path.join(distPath, 'index.html')));

  return await new Promise((resolve) => {
    const listener = server.listen(0, '127.0.0.1', () => {
      resolve({ server, port: listener.address().port });
    });
  });
}

function projectRoot() {
  if (fs.existsSync(path.join(process.cwd(), 'backend')) && fs.existsSync(path.join(process.cwd(), 'ml'))) {
    return process.cwd();
  }

  return path.resolve(path.dirname(process.execPath), '..', '..');
}

function portReady(url) {
  return new Promise((resolve) => {
    const request = http.get(url, { timeout: 1500 }, (response) => {
      response.resume();
      resolve(response.statusCode !== undefined && response.statusCode < 500);
    });

    request.on('error', () => resolve(false));
    request.on('timeout', () => {
      request.destroy();
      resolve(false);
    });
  });
}

function launchDetached(command, args, cwd) {
  const child = spawn(command, args, {
    cwd,
    detached: true,
    stdio: 'ignore',
    shell: process.platform === 'win32',
  });

  child.unref();
}

async function ensureServicesRunning() {
  const root = projectRoot();
  const backendDir = path.join(root, 'backend');
  const mlDir = path.join(root, 'ml');

  if (fs.existsSync(backendDir)) {
    const backendReady = await portReady('http://127.0.0.1:3001/api/leagues');
    if (!backendReady) {
      launchDetached('npm', ['run', 'start:dev'], backendDir);
    }
  }

  if (fs.existsSync(mlDir)) {
    const mlReady = await portReady('http://127.0.0.1:8000/health');
    if (!mlReady) {
      const pythonExecutable = path.join(mlDir, '.venv', 'Scripts', 'python.exe');
      if (fs.existsSync(pythonExecutable)) {
        launchDetached(pythonExecutable, ['-m', 'uvicorn', 'app.main:app', '--port', '8000'], mlDir);
      }
    }
  }
}

function createWindow(port) {
  const win = new BrowserWindow({
    width: 1400,
    height: 950,
    minWidth: 1100,
    minHeight: 760,
    backgroundColor: '#f8fafc',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  win.loadURL(`http://127.0.0.1:${port}`);
}

let localServer;

app.whenReady().then(async () => {
  await ensureServicesRunning();
  const started = await startLocalServer();
  localServer = started.server;
  createWindow(started.port);

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow(started.port);
    }
  });
});

app.on('window-all-closed', () => {
  if (localServer) {
    localServer.close();
  }

  if (process.platform !== 'darwin') {
    app.quit();
  }
});