const { exec } = require('child_process');
const path = require('path');

// 默认 bat 文件路径（用户可更改）
const DEFAULT_BAT_PATH = path.join(
  process.env.USERPROFILE || process.env.HOME,
  'AppData', 'Roaming', 'TRAE SOLO CN', 'ModularData',
  'ai-agent', 'work-mode-projects',
  '6aa6089a3439bafbf5f5375f', '启动.bat'
);

window.services = {
  // 获取已保存的 bat 路径
  getServerPath() {
    const doc = utools.db.get('bilibili-server-path');
    return doc ? doc.value : DEFAULT_BAT_PATH;
  },

  // 保存 bat 路径
  saveServerPath(p) {
    const existing = utools.db.get('bilibili-server-path');
    if (existing) {
      utools.db.put({ _id: existing._id, _rev: existing._rev, value: p });
    } else {
      utools.db.put({ _id: 'bilibili-server-path', value: p });
    }
  },

  // 弹出文件选择器选择 bat 文件
  selectBatFile() {
    const result = utools.showOpenDialog({
      title: '选择 启动.bat 文件',
      filters: [{ name: '批处理文件', extensions: ['bat'] }, { name: '所有文件', extensions: ['*'] }],
      properties: ['openFile'],
      defaultPath: DEFAULT_BAT_PATH,
    });
    if (result && result[0]) {
      window.services.saveServerPath(result[0]);
      return result[0];
    }
    return null;
  },

  // 启动 Python 服务器
  startServer() {
    const batPath = window.services.getServerPath();
    try {
      exec(`start "" "${batPath}"`, { windowsHide: true });
      return true;
    } catch (e) {
      console.error('启动失败:', e);
      return false;
    }
  },

  // 获取默认路径（用于显示）
  getDefaultPath() {
    return DEFAULT_BAT_PATH;
  },
};
