"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.extensionAuthorities = void 0;
exports.registerCustomSchemes = registerCustomSchemes;
exports.handleFaviconProtocolRequest = handleFaviconProtocolRequest;
exports.registerCustomSchemeHandlers = registerCustomSchemeHandlers;
const electron_1 = require("electron");
const faviconStore_1 = require("./faviconStore");
const redirects_1 = require("./redirects");
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
            // Serves cached favicon bytes to the Hub renderer's <img> tags only, so
            // no fetch, CORS, or service-worker privileges.
            scheme: faviconStore_1.FAVICON_SCHEME,
            privileges: { standard: true, secure: true },
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
/**
 * Handles `agy-favicon://<token>/` by looking the token up in the favicon
 * store. Never fetches: unknown tokens and any other path are 404.
 */
function handleFaviconProtocolRequest(request) {
    if (request.method !== 'GET') {
        return new Response(null, { status: 405 });
    }
    let url;
    try {
        url = new URL(request.url);
    }
    catch {
        return new Response(null, { status: 404 });
    }
    const favicon = url.pathname === '/' ? (0, faviconStore_1.lookupFaviconToken)(url.hostname) : undefined;
    if (!favicon) {
        return new Response(null, { status: 404 });
    }
    return new Response(new Uint8Array(favicon.bytes), {
        status: 200,
        headers: {
            'Content-Type': favicon.mime,
            'X-Content-Type-Options': 'nosniff',
            // A top-level load of an SVG favicon must not run as a document.
            'Content-Security-Policy': "default-src 'none'; sandbox",
            'Cache-Control': 'no-store',
        },
    });
}
function hasValidUiBundle(fs, bundlePath) {
    if (!bundlePath) {
        return false;
    }
    try {
        const stat = fs.statSync(bundlePath);
        return stat.isFile() && stat.size > 0;
    }
    catch {
        return false;
    }
}
function registerCustomSchemeHandlers() {
    const fs = require("fs");
    const fsPromises = require("fs/promises");
    const path = require("path");
    let appDataPath = '';
    try {
        appDataPath = electron_1.app && typeof electron_1.app.getPath === 'function'
            ? electron_1.app.getPath('userData')
            : '';
    }
    catch (e) {
        console.error("Failed to get userData path:", e);
    }
    const uiBundlePath = appDataPath ? path.join(appDataPath, 'zh_cn_ui_main.js') : '';

    // 1. 保留 2.32.2 原生 plugin:// 处理器（含 sidecar 同源校验与重定向保护）
    try {
        electron_1.protocol.handle('plugin', async (request) => {
            let targetUrlForLog = request?.url || '<unknown>';
            try {
                const url = new URL(request.url);
                const authority = url.hostname;
                const originalHost = exports.extensionAuthorities.get(authority);
                if (!originalHost) {
                    return new Response(null, { status: 404 });
                }
                // Origin plus path: resolving a path like "//host/x" against the sidecar
                // URL would switch to another host.
                const sidecar = new URL(originalHost);
                const targetUrl = new URL(`${sidecar.origin}${url.pathname}${url.search}`);
                targetUrlForLog = targetUrl.href;
                if (targetUrl.host !== sidecar.host) {
                    return new Response(null, { status: 404 });
                }
                // With the main process's network and cookies. A redirect goes back to
                // the frame if it stays on the sidecar's origin (redirects.ts).
                const response = await (0, redirects_1.fetchWithoutFollowing)(targetUrl.href, request);
                return (0, redirects_1.pluginResponse)(response, targetUrl, url);
            }
            catch (err) {
                console.error(`Failed to proxy request to ${targetUrlForLog}:`, err);
                return new Response(null, { status: 500 });
            }
        });
    }
    catch (e) {
        console.error("Failed to register plugin handler:", e);
    }

    // 2. 保留 2.32.2 原生 agy-favicon:// 处理器（仅绑定默认 session）
    try {
        electron_1.protocol.handle(faviconStore_1.FAVICON_SCHEME, handleFaviconProtocolRequest);
    }
    catch (e) {
        console.error("Failed to register agy-favicon handler:", e);
    }

    // 3. 清除默认 session 缓存以确保更新后的汉化包立即生效
    try {
        if (electron_1.session && electron_1.session.defaultSession && typeof electron_1.session.defaultSession.clearCache === 'function') {
            Promise.resolve(electron_1.session.defaultSession.clearCache()).catch((err) => {
                console.error("Failed to clear session cache:", err);
            });
        }
    }
    catch (e) {
        console.error("Failed to invoke clearCache:", e);
    }

    // 4. 通过 agy-ui:// 提供预编译的本地汉化 UI 包
    try {
        electron_1.protocol.handle('agy-ui', async () => {
            if (uiBundlePath) {
                try {
                    const content = await fsPromises.readFile(uiBundlePath);
                    if (content && content.length > 0) {
                        console.log("Serving translated AI UI bundle:", uiBundlePath);
                        return new Response(content, {
                            status: 200,
                            headers: {
                                'Content-Type': 'application/javascript; charset=utf-8',
                                'Access-Control-Allow-Origin': '*',
                                'Cache-Control': 'no-store',
                            },
                        });
                    }
                    console.error("zh_cn_ui_main.js is empty:", uiBundlePath);
                }
                catch (e) {
                    console.error("Failed to load zh_cn_ui_main.js:", e);
                }
            }
            return new Response('// Chameleon fallback', {
                status: 200,
                headers: {
                    'Content-Type': 'application/javascript; charset=utf-8',
                    'Cache-Control': 'no-store',
                },
            });
        });
    }
    catch (e) {
        console.error("Failed to register agy-ui handler:", e);
    }

    // 5. 非阻塞后台同步 chameleon_dict.json（带超时、响应流回收与大小上限防护）
    try {
        const syncTimer = setTimeout(() => {
            try {
                if (!appDataPath) {
                    return;
                }
                const https = require('https');
                const dictUrl = 'https://raw.githubusercontent.com/Eric-Chenjm/Project-Chameleon/main/translations/chameleon_dict.json';
                const maxBytes = 10 * 1024 * 1024;
                const req = https.get(dictUrl, { timeout: 10000 }, (res) => {
                    if (res && typeof res.on === 'function') {
                        res.on('error', () => {});
                    }
                    if (res.statusCode !== 200) {
                        if (typeof res.resume === 'function') {
                            res.resume();
                        }
                        return;
                    }
                    if (typeof res.setEncoding === 'function') {
                        res.setEncoding('utf8');
                    }
                    let data = '';
                    let aborted = false;
                    res.on('data', (chunk) => {
                        if (aborted) {
                            return;
                        }
                        data += chunk;
                        if (data.length > maxBytes) {
                            aborted = true;
                            if (typeof req.destroy === 'function') {
                                req.destroy();
                            }
                        }
                    });
                    res.on('end', () => {
                        if (aborted || !data) {
                            return;
                        }
                        try {
                            JSON.parse(data);
                            const dictPath = path.join(appDataPath, 'chameleon_dict.json');
                            void fsPromises.writeFile(dictPath, data, 'utf8').catch(() => {});
                        }
                        catch (e) {}
                    });
                });
                if (req && typeof req.on === 'function') {
                    req.on('timeout', () => {
                        if (typeof req.destroy === 'function') {
                            req.destroy();
                        }
                    });
                    req.on('error', () => {});
                }
            }
            catch (e) {}
        }, 5000);
        if (syncTimer && typeof syncTimer.unref === 'function') {
            syncTimer.unref();
        }
    }
    catch (e) {}

    // 6. 仅当路径精确为 /main.js 且 zh_cn_ui_main.js 有效非空时，重定向至 agy-ui://bundle/main.js；否则放行官方原版
    try {
        if (electron_1.session && electron_1.session.defaultSession && electron_1.session.defaultSession.webRequest &&
            typeof electron_1.session.defaultSession.webRequest.onBeforeRequest === 'function') {
            electron_1.session.defaultSession.webRequest.onBeforeRequest(
                { urls: ['https://127.0.0.1:*/main.js*', 'https://127.0.0.1:*/main.js?*'] },
                (details, callback) => {
                    try {
                        const reqUrl = new URL(details.url);
                        if (reqUrl.pathname === '/main.js' && hasValidUiBundle(fs, uiBundlePath)) {
                            callback({ redirectURL: 'agy-ui://bundle/main.js' });
                            return;
                        }
                    }
                    catch (e) {
                        // 解析失败或文件异常时回退直通，确保不引发白屏
                    }
                    callback({});
                }
            );
        }
    }
    catch (e) {
        console.error("Failed to set onBeforeRequest redirect:", e);
    }
}