const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pyBackendProcess = null;

function startPythonBackend() {
  const isPackaged = app.isPackaged;
  const backendPath = isPackaged
    ? path.join(process.resourcesPath, 'ptdt-backend', 'ptdt-backend.exe')
    : path.join(__dirname, '..', 'dist', 'ptdt-backend', 'ptdt-backend.exe');

  console.log(`Launching Sovereign Backend Sidecar from: ${backendPath}`);

  pyBackendProcess = spawn(backendPath, ['--port', '8000'], {
    cwd: path.dirname(backendPath),
  });

  pyBackendProcess.stdout.on('data', (data) => {
    console.log(`[Python Core]: ${data}`);
  });

  pyBackendProcess.stderr.on('data', (data) => {
    console.error(`[Python Core Error]: ${data}`);
  });

  pyBackendProcess.on('error', (err) => {
    console.error('Failed to start backend sidecar:', err.message);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1600,
    height: 1000,
    title: 'Point Township Digital Twin v33 — Sovereign Engineering System',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      webgl: true,
      experimentalFeatures: true,
    },
  });

  const startUrl =
    process.env.ELECTRON_START_URL ||
    `file://${path.join(__dirname, '../frontend/dist/index.html')}`;
  mainWindow.loadURL(startUrl);

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.on('ready', () => {
  startPythonBackend();
  setTimeout(createWindow, 2000);
});

app.on('window-all-closed', () => {
  if (pyBackendProcess) {
    pyBackendProcess.kill();
    pyBackendProcess = null;
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  if (pyBackendProcess) {
    pyBackendProcess.kill();
    pyBackendProcess = null;
  }
});
