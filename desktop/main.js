const { app, BrowserWindow } = require('electron');
const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
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