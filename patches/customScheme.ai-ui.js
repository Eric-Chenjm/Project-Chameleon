"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.extensionAuthorities = void 0;
exports.registerCustomSchemes = registerCustomSchemes;
exports.registerCustomSchemeHandlers = registerCustomSchemeHandlers;
const electron_1 = require("electron");
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
    // 清除缓存以确保加载最新汉化包
    electron_1.session.defaultSession.clearCache().catch((err) => {
        console.error("Failed to clear session cache:", err);
    });
    // 核心：直接从用户数据目录加载预编译好的汉化 UI 包
    electron_1.protocol.handle('agy-ui', async () => {
        const path = require("path");
        const fsPromises = require("fs/promises");
        const appDataPath = electron_1.app.getPath('userData');
        const targetPath = path.join(appDataPath, 'zh_cn_ui_main.js');
        try {
            const content = await fsPromises.readFile(targetPath);
            console.log("Serving translated AI UI bundle:", targetPath);
            return new Response(content, {
                status: 200,
                headers: {
                    'Content-Type': 'application/javascript; charset=utf-8',
                    'Access-Control-Allow-Origin': '*',
                    'Cache-Control': 'no-store'
                }
            });
        } catch(e) {
            console.error("Failed to load zh_cn_ui_main.js, falling back to original:", e);
            return new Response('// Chameleon: translation file not found, app loads normally', {
                status: 200,
                headers: { 'Content-Type': 'application/javascript; charset=utf-8' }
            });
        }
    });
    // 非阻塞后台：云端字典自动更新（下次运行 smart_patch 时生效）
    setTimeout(() => {
        try {
            const https = require('https');
            const fs = require('fs');
            const path = require('path');
            const appDataPath = electron_1.app.getPath('userData');
            const url = 'https://raw.githubusercontent.com/Eric-Chenjm/Project-Chameleon/main/translations/chameleon_dict.json';
            https.get(url, (res) => {
                if (res.statusCode !== 200) return;
                let data = '';
                res.on('data', chunk => data += chunk);
                res.on('end', () => {
                    try {
                        JSON.parse(data);
                        fs.writeFileSync(path.join(appDataPath, 'chameleon_dict.json'), data, 'utf8');
                    } catch(e) {}
                });
            }).on('error', () => {});
        } catch(e) {}
    }, 3000);
    electron_1.session.defaultSession.webRequest.onBeforeRequest(
        { urls: ['https://127.0.0.1:*/main.js'] },
        (details, callback) => {
            callback({ redirectURL: 'agy-ui://bundle/main.js' });
        }
    );
}
