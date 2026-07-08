"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.extensionAuthorities = void 0;
exports.registerCustomSchemes = registerCustomSchemes;
exports.registerCustomSchemeHandlers = registerCustomSchemeHandlers;
const electron_1 = require("electron");
// A map of extension authority -> original URL (http://localhost:<port>)
// The authority is usually a hash of unique extension identifiers
// like extension ID + port + project ID. An extension running on localhost:<port>
// is then exposed on plugin://<authority>.
exports.extensionAuthorities = new Map();
function registerCustomSchemes() {
    electron_1.protocol.registerSchemesAsPrivileged([
        {
            scheme: 'plugin',
            privileges: {
                standard: true,
                secure: true,
                supportFetchAPI: true,
                corsEnabled: true,
                allowServiceWorkers: true,
                codeCache: true,
            },
        },
        {
            scheme: 'agy-ui',
            privileges: {
                standard: true,
                secure: true,
                supportFetchAPI: true,
                corsEnabled: true,
                codeCache: true,
            },
        },
    ]);
}
function registerCustomSchemeHandlers() {
    // Handle custom scheme for UI extensions
    electron_1.protocol.handle('plugin', async (request) => {
        const url = new URL(request.url);
        const authority = url.hostname;
        const originalHost = exports.extensionAuthorities.get(authority);
        if (!originalHost) {
            return new Response(null, { status: 404 });
        }
        const targetUrl = new URL(url.pathname + url.search, originalHost);
        try {
            const fetchOptions = {
                method: request.method,
                headers: request.headers,
                body: request.body,
            };
            if (request.body) {
                // Required by Electron's net.fetch when the body is a stream
                fetchOptions.duplex = 'half';
            }
            const response = await electron_1.net.fetch(targetUrl.toString(), fetchOptions);
            return response;
        }
        catch (err) {
            console.error(`Failed to proxy request to ${targetUrl}:`, err);
            return new Response(null, { status: 500 });
        }
    });
    // Optional AI UI localization. Only /main.js is replaced; every other
    // request goes directly to the local language server.
    electron_1.session.defaultSession.clearCache().catch((err) => {
        console.error("Failed to clear session cache before AI UI localization:", err);
    });
    electron_1.protocol.handle('agy-ui', async () => {
        const path = require("path");
        const fsPromises = require("fs/promises");
        const https = require("https");
        const appDataPath = electron_1.app.getPath('userData');
        const mainPath = path.join(appDataPath, 'original_ui_main.js');
        const dictPath = path.join(appDataPath, 'chameleon_dict.json');
        
        let content = '';
        let dict = { translations: {}, dynamicDict: {} };
        
        try {
            content = await fsPromises.readFile(mainPath, 'utf8');
        } catch(e) {
            console.error("Missing original_ui_main.js", e);
            return new Response("Missing original_ui_main.js", { status: 404 });
        }
        
        try {
            const dictRaw = await fsPromises.readFile(dictPath, 'utf8');
            dict = JSON.parse(dictRaw);
        } catch(e) {
            console.error("Failed to read chameleon_dict.json, proceeding with no translation", e);
        }
        
        // --- 1. Literal replacement ---
        function applySafeLiteralReplacement(text, originalLiteral, translatedLiteral) {
            const sourceValue = originalLiteral.slice(1, -1);
            const targetValue = translatedLiteral.slice(1, -1);
            
            const toSingleQuoted = (val) => "'" + val.replace(/\\/g, '\\\\').replace(/'/g, "\\'") + "'";
            const doubleQuoted = (val) => '"' + val + '"';
            const innerDoubleEscaped = (val) => '"' + val.replace(/\\/g, '\\\\').replace(/"/g, '\\"') + '"';
            
            let res = text.split(toSingleQuoted(sourceValue)).join(toSingleQuoted(targetValue));
            res = res.split(doubleQuoted(sourceValue)).join(doubleQuoted(targetValue));
            res = res.split(innerDoubleEscaped(sourceValue)).join(innerDoubleEscaped(targetValue));
            return res;
        }

        const translations = dict.translations || {};
        for (const [original, translated] of Object.entries(translations)) {
            if (/^["'].*["']$/.test(original) && /^["'].*["']$/.test(translated)) {
                content = applySafeLiteralReplacement(content, original, translated);
            } else {
                if (content.includes(original)) {
                    content = content.split(original).join(translated);
                } else {
                    const altOriginal = original.replace(/"/g, "'");
                    const altTranslated = translated.replace(/"/g, "'");
                    if (content.includes(altOriginal)) {
                        content = content.split(altOriginal).join(altTranslated);
                    }
                }
            }
        }
        
        // --- 2. Append MutationObserver script ---
        const dom_translator_js = `
// 注入动态 DOM 汉化引擎 (针对 React 深度封装无法静态替换的长句与危险短词)
(function() {
  const dynamicDict = ${JSON.stringify(dict.dynamicDict || {})};
  const translateText = (text) => {
      let t = text.trim();
      if (dynamicDict[t]) return text.replace(t, dynamicDict[t]);
      if (t.startsWith("Advanced Settings")) return text.replace("Advanced Settings", "高级设置");
      if (t.startsWith("Your Plan: ")) return text.replace("Your Plan: ", "当前套餐: ");
      if (t.includes("The browser subagent can be invoked by typing /browser in the conversation input box")) {
          return "才能正常运行。可以在对话输入框中输入 /browser 来调用浏览器子智能体。";
      }
      if (t.includes("will use your AI credits to fulfill model requests once you're out of model quota")) {
          return "开启后，当模型配额耗尽时，Antigravity 将使用您的 AI 额度处理模型请求。它将始终优先使用模型配额。";
      }
      if (t.includes("Within each group, models share a weekly limit and a 5-hour limit")) {
          return "在每个组中，模型共享周限额和 5 小时限额。配额消耗与 Token 成本成正比。因此，任务越短或使用更划算的模型，限额持续的时间就越长。5 小时限额有助于在所有用户之间公平分配容量，而您的周限额则直接与您的套餐等级挂钩。";
      }
      if (t.includes("You have used some of your weekly limit")) {
          return text.replace("You have used some of your weekly limit, it will fully refresh in", "您已使用了部分周限额，将在").replace("days,", "天").replace("hours.", "小时后完全刷新。");
      }
      if (t.includes("You have used some of your 5-hour limit")) {
          return text.replace("You have used some of your 5-hour limit, it will fully refresh in", "您已使用了部分 5 小时限额，将在").replace("hours,", "小时").replace("minutes.", "分钟后完全刷新。");
      }
      if (/^Show \\\\d+ breakdowns?$/.test(t)) {
          return text.replace(/^Show (\\\\d+) breakdowns?$/, "显示 $1 项明细");
      }
      return text;
  };
  const translatedNodes = new WeakSet();
  const walkNode = (node) => {
    if (translatedNodes.has(node)) return;
    translatedNodes.add(node);
    if (node.nodeType === 3) {
       const newText = translateText(node.textContent);
       if (newText !== node.textContent) node.textContent = newText;
    } else if (node.nodeType === 1) {
       if (node.nodeName !== 'SCRIPT' && node.nodeName !== 'STYLE') {
           node.childNodes.forEach(walkNode);
       }
    }
  };
  const initTranslator = () => {
      walkNode(document.body);
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          mutation.addedNodes.forEach(walkNode);
          if (mutation.type === 'characterData') {
             const newText = translateText(mutation.target.textContent);
             if (newText !== mutation.target.textContent) mutation.target.textContent = newText;
          }
        });
      });
      observer.observe(document.body, { childList: true, subtree: true, characterData: true });
  };
  if (document.body) initTranslator();
  else window.addEventListener('DOMContentLoaded', initTranslator);
})();
`;
        content += "\\n" + dom_translator_js;
        
        // --- 3. Non-blocking Background Fetch & Sweep ---
        setTimeout(() => {
            backgroundTasks(appDataPath, dict.dynamicDict || {}).catch(e => console.error("Background tasks failed:", e));
        }, 1000);

        console.log("Serving translated AI UI bundle dynamically.");
        return new Response(content, {
            status: 200,
            headers: {
                'Content-Type': 'application/javascript; charset=utf-8',
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'no-store'
            }
        });
    });

    async function backgroundTasks(appDataPath, dynamicDict) {
        const fsPromises = require('fs/promises');
        const path = require('path');
        const https = require('https');
        const os = require('os');
        
        // 1. Auto-update chameleon_dict.json
        const url = 'https://raw.githubusercontent.com/Eric-Chenjm/Project-Chameleon/main/translations/chameleon_dict.json';
        https.get(url, (res) => {
            let data = '';
            if (res.statusCode !== 200) return;
            res.on('data', chunk => data += chunk);
            res.on('end', async () => {
                try {
                    JSON.parse(data);
                    await fsPromises.writeFile(path.join(appDataPath, 'chameleon_dict.json'), data, 'utf8');
                } catch(e) {}
            });
        }).on('error', () => {});

        // 2. Non-blocking background sweep of skills and plugins
        try {
            const homeDir = os.homedir();
            const configDir = path.join(homeDir, '.gemini', 'config');
            const skillsDir = path.join(configDir, 'skills');
            const pluginsDir = path.join(configDir, 'plugins');
            const pending = [];
            
            async function scanDir(dir) {
                try {
                    const entries = await fsPromises.readdir(dir, { withFileTypes: true });
                    for (let entry of entries) {
                        if (entry.isDirectory()) {
                            const skillMdPath = path.join(dir, entry.name, 'SKILL.md');
                            try {
                                const content = await fsPromises.readFile(skillMdPath, 'utf8');
                                const descMatch = content.match(/description:\s*(.+)/);
                                if (descMatch) {
                                    let desc = descMatch[1].trim();
                                    if (desc.startsWith('"') && desc.endsWith('"')) {
                                        desc = desc.slice(1, -1);
                                    } else if (desc.startsWith("'") && desc.endsWith("'")) {
                                        desc = desc.slice(1, -1);
                                    }
                                    if (!dynamicDict[desc]) {
                                        pending.push(desc);
                                    }
                                }
                            } catch(e) {}
                            await scanDir(path.join(dir, entry.name));
                        }
                    }
                } catch(e) {}
            }
            await scanDir(skillsDir);
            await scanDir(pluginsDir);
            
            if (pending.length > 0) {
                await fsPromises.writeFile(
                    path.join(appDataPath, 'pending_translate.json'),
                    JSON.stringify([...new Set(pending)], null, 2),
                    'utf8'
                );
            }
        } catch(e) {}
    }

    electron_1.session.defaultSession.webRequest.onBeforeRequest(
        { urls: ['https://127.0.0.1:*/main.js'] },
        (details, callback) => {
            callback({ redirectURL: 'agy-ui://bundle/main.js' });
        }
    );
}
