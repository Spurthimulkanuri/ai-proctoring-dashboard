// main.js
const { app, BrowserWindow, globalShortcut } = require('electron');

function createWindow () {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    fullscreen: true,
    kiosk: true, // 💡 Prevents exiting fullscreen (no Alt+F4)
    webPreferences: {
     nodeIntegration: true,
     contextIsolation: false,
     webSecurity: false,  // ⛳️ allow webcam/mic in Electron
     allowRunningInsecureContent: true,
    media: {
     audio: true,
     video: true
   } }
  });

  win.loadURL('http://localhost:5000'); // Your Flask exam server
  win.setMenuBarVisibility(false); // Disable menu bar
}

app.whenReady().then(() => {
  createWindow();

  // 🚫 Disable system shortcuts like reload, devtools
  globalShortcut.register('CommandOrControl+R', () => {});
  globalShortcut.register('F5', () => {});
  globalShortcut.register('CommandOrControl+Shift+I', () => {});
  globalShortcut.register('Alt+Tab', () => {}); // may not work on all OS

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  // Do not quit on close (force logout)
});

