const { app, BrowserWindow, Menu, shell, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

app.disableHardwareAcceleration();

let mainWindow;
let backendProcess = null;

// Tentukan path backend executable
function getBackendPath() {
  const isDev = !app.isPackaged;
  if (isDev) {
    // Saat development, jalankan langsung pakai uvicorn
    return null;
  }
  const platform = process.platform;
  const exeName = platform === 'win32' ? 'bandungaja-server.exe' : 'bandungaja-server';
  return path.join(process.resourcesPath, 'backend', exeName);
}

// Jalankan backend
function startBackend() {
  const isDev = !app.isPackaged;

  if (isDev) {
    // Development: backend dijalankan manual, tidak perlu spawn
    console.log('Mode development: jalankan backend manual dengan uvicorn');
    return;
  }

  const backendPath = getBackendPath();
  console.log('Menjalankan backend:', backendPath);

  backendProcess = spawn(backendPath, [], {
    cwd: path.dirname(backendPath),
    detached: false,
    stdio: 'ignore',
  });

  backendProcess.on('error', (err) => {
    console.error('Gagal menjalankan backend:', err);
    dialog.showErrorBox('Error', 'Gagal menjalankan server backend.\n' + err.message);
  });

  backendProcess.on('exit', (code) => {
    console.log('Backend keluar dengan kode:', code);
  });
}

// Poll sampai backend siap
function waitForBackend(retries = 30) {
  return new Promise((resolve, reject) => {
    const check = (remaining) => {
      if (remaining <= 0) {
        reject(new Error('Backend tidak merespons setelah 30 detik'));
        return;
      }
      http.get('http://127.0.0.1:8000/', (res) => {
        if (res.statusCode === 200) {
          resolve();
        } else {
          setTimeout(() => check(remaining - 1), 1000);
        }
      }).on('error', () => {
        setTimeout(() => check(remaining - 1), 1000);
      });
    };
    check(retries);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    title: 'BandungAja - Jelajahi Bandung',
    icon: path.join(__dirname, 'frontend', 'asset', 'ICON-APP-BDGAJA.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false,
    },
    backgroundColor: '#0a0f1e',
    show: false,
  });

  mainWindow.loadFile('frontend/index.html');

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // Uncomment untuk DevTools:
  // mainWindow.webContents.openDevTools();

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Loading window saat backend belum siap
function createLoadingWindow() {
  const loading = new BrowserWindow({
    width: 400,
    height: 300,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    webPreferences: { nodeIntegration: false },
    backgroundColor: '#0a0f1e',
  });

  loading.loadURL(`data:text/html,
    <html>
    <body style="margin:0;background:#0a0f1e;display:flex;flex-direction:column;
      align-items:center;justify-content:center;height:100vh;
      font-family:sans-serif;color:white;">
      <div style="font-size:32px;margin-bottom:16px">🎯</div>
      <div style="font-size:20px;font-weight:700;margin-bottom:8px">BandungAja</div>
      <div style="font-size:13px;color:#888">Memulai server, harap tunggu...</div>
    </body>
    </html>
  `);

  return loading;
}

Menu.setApplicationMenu(null);
app.commandLine.appendSwitch('enable-gpu-rasterization');
app.commandLine.appendSwitch('enable-zero-copy');

app.whenReady().then(async () => {
  startBackend();

  const loading = createLoadingWindow();

  try {
    await waitForBackend();
    loading.close();
    createWindow();
  } catch (err) {
    loading.close();
    dialog.showErrorBox(
      'Gagal Memulai',
      'Server backend tidak merespons.\nPastikan tidak ada aplikasi lain yang memakai port 8000.'
    );
    app.quit();
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  // Matikan backend saat app ditutup
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});