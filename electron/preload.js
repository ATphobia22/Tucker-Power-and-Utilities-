const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('ptdt', {
  apiBase: 'http://127.0.0.1:8000',
  version: '33.0.0',
});
