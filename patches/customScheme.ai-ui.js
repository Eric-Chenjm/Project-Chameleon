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
    let appDataPath = '';
    try {
        appDataPath = electron_1.app ? electron_1.app.getPath('userData') : '';
    } catch (e) {
        console.error("Failed to get userData path:", e);
    }

    try {
        electron_1.protocol.handle('plugin', async (request) => {
            try {
                const url = new URL(request.url);
                const authority = url.hostname;
                const originalHost = exports.extensionAuthorities.get(authority);
                if (!originalHost) {
                    return new Response(null, { status: 404 });
                }
                const targetUrl = new URL(url.pathname + url.search, originalHost);
                const fetchOptions = {
                    method: request.method,
                    headers: request.headers,
                    body: request.body,
                };
                if (request.body) {
                    fetchOptions.duplex = 'half';
                }
                return await electron_1.net.fetch(targetUrl.toString(), fetchOptions);
            } catch (err) {
                console.error(`Failed to proxy request:`, err);
                return new Response(null, { status: 500 });
            }
        });
    } catch (e) {
        console.error("Failed to register plugin handler:", e);
    }

    // 清除缓存以确保加载最新汉化包
    try {
        if (electron_1.session && electron_1.session.defaultSession) {
            electron_1.session.defaultSession.clearCache().catch((err) => {
                console.error("Failed to clear session cache:", err);
            });
        }
    } catch (e) {}

    // 核心：直接从用户数据目录加载预编译好的汉化 UI 包
    try {
        electron_1.protocol.handle('agy-ui', async () => {
            const path = require("path");
            const fsPromises = require("fs/promises");
            const targetPath = appDataPath ? path.join(appDataPath, 'zh_cn_ui_main.js') : '';
            if (targetPath) {
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
                    console.error("Failed to load zh_cn_ui_main.js:", e);
                }
            }
            return new Response('// Chameleon fallback', {
                status: 200,
                headers: { 'Content-Type': 'application/javascript; charset=utf-8' }
            });
        });
    } catch (e) {
        console.error("Failed to register agy-ui handler:", e);
    }

    // 非阻塞后台：云端字典自动更新
    try {
        setTimeout(() => {
            try {
                if (!appDataPath) return;
                const https = require('https');
                const fs = require('fs');
                const path = require('path');
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
        }, 5000);
    } catch (e) {}

    try {
        if (electron_1.session && electron_1.session.defaultSession && electron_1.session.defaultSession.webRequest) {
            electron_1.session.defaultSession.webRequest.onBeforeRequest(
                { urls: ['https://127.0.0.1:*/main.js'] },
                (details, callback) => {
                    try {
                        callback({ redirectURL: 'agy-ui://bundle/main.js' });
                    } catch (e) {
                        callback({});
                    }
                }
            );
        }
    } catch (e) {
        console.error("Failed to set onBeforeRequest redirect:", e);
    }
}
