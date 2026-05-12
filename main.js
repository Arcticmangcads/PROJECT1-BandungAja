const { app, BrowserWindow, Menu, shell } = require('electron');
const path = require('path');

// Disable GPU acceleration to avoid issues on some systems
app.disableHardwareAcceleration();

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    title: 'BandungAja - Jelajahi Bandung',
    icon: path.join(__dirname, 'asset', 'ICON-APP-BDGAJA.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      // Izinkan akses ke resource lokal dan CDN eksternal
      webSecurity: true,
    },
    backgroundColor: '#0a0f1e',
    show: false, // Tampil setelah siap agar tidak ada flash putih
  });

  // Load file HTML utama
  mainWindow.loadFile('frontend/index.html');

  // Tampilkan window setelah siap (menghindari flash kosong)
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Buka link eksternal di browser default, bukan di dalam app
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // Uncomment baris ini untuk membuka DevTools saat development:
  mainWindow.webContents.openDevTools();

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Hapus menu bar default (opsional - bisa di-comment jika ingin menu)
Menu.setApplicationMenu(null);
app.commandLine.appendSwitch('enable-gpu-rasterization');
app.commandLine.appendSwitch('enable-zero-copy');
app.whenReady().then(() => {
  createWindow();

  // Di macOS, buat window baru jika klik ikon dock saat semua window tertutup
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Keluar saat semua window ditutup (kecuali macOS)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
