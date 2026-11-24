// Project Chameleon v3.0 — High-Performance Non-Destructive Localization Engine
(() => {
  if (typeof window === 'undefined' || typeof document === 'undefined') return;

  const FINGERPRINT = window.__chameleonRequestedFingerprint || '/* __CHAMELEON_FINGERPRINT__ */';
  if (
    window.__chameleonInstalled === true &&
    window.__chameleonObservedDoc === document &&
    window.__chameleonFingerprint === FINGERPRINT
  ) {
    return;
  }

  // 热更新或重注入时先安全清理旧版实例并恢复现场
  if (typeof window.__chameleonCleanup === 'function') {
    try { window.__chameleonCleanup(); } catch (_) {}
  }

  window.__chameleonInstalled = true;
  window.__chameleonObservedDoc = document;
  window.__chameleonFingerprint = FINGERPRINT;

  const dictionary = /* __CHAMELEON_DICTIONARY__ */ {};

  /* __CHAMELEON_RULES__ */

  // 预编译 O(1) 小写哈希词典
  const lowerDictionary = new Map();
  for (const k in dictionary) {
    if (Object.prototype.hasOwnProperty.call(dictionary, k)) {
      const lk = k.toLowerCase();
      if (!lowerDictionary.has(lk)) {
        lowerDictionary.set(lk, dictionary[k]);
      }
    }
  }

  // 支持用户自定义覆盖字典（可通过 CDP 启动器或本地文件注入 window.__chameleonCustomDict）
  const customDictionary = new Map();
  if (window.__chameleonCustomDict && typeof window.__chameleonCustomDict === 'object') {
    for (const [ck, cv] of Object.entries(window.__chameleonCustomDict)) {
      const key = String(ck || '').trim().toLowerCase();
      if (key) customDictionary.set(key, String(cv ?? '').trim());
    }
  }

  const MAX_STRING_CACHE = 8000;
  const stringCache = new Map();
  function cacheSet(key, val) {
    if (stringCache.has(key)) {
      stringCache.delete(key);
    } else if (stringCache.size >= MAX_STRING_CACHE) {
      const oldest = stringCache.keys().next().value;
      if (oldest !== undefined) stringCache.delete(oldest);
    }
    stringCache.set(key, val);
  }

  function replaceTrimmed(text, trimmed, fixed) {
    if (text === trimmed) return fixed;
    const idx = text.indexOf(trimmed);
    if (idx === -1) return fixed;
    return text.slice(0, idx) + fixed + text.slice(idx + trimmed.length);
  }

  const PREF_LANG_KEY = 'chameleonLangMode';
  const PREF_EN_LABELS_KEY = 'chameleonKeepEnglishLabels';
  const PREF_POS_KEY = 'chameleonTogglePos';

  const loadPref = (k) => {
    try { return window.localStorage ? window.localStorage.getItem(k) : null; } catch (_) { return null; }
  };
  const savePref = (k, v) => {
    try { if (window.localStorage) window.localStorage.setItem(k, v); } catch (_) {}
  };

  let currentLang = loadPref(PREF_LANG_KEY) === 'en' ? 'en' : 'zh';
  let englishLabelsMode = loadPref(PREF_EN_LABELS_KEY) === '1';
  let originalDocLang = null;

  // WeakMap 原文双轨记忆（跨实例挂在 window 上，便于热切换或更新时无损还原）
  const originals = window.__chameleonOriginals || (window.__chameleonOriginals = {
    texts: new WeakMap(),
    attrs: new WeakMap(),
  });
  let translatedNodes = new WeakSet();

  const SAFE_ATTRS = ['aria-label', 'placeholder', 'title', 'data-tooltip', 'alt'];

  function makeCtx() {
    return {
      dictionary,
      lowerDictionary,
      customDictionary,
      englishLabelsMode,
      stringCache,
      cacheSet,
      replaceTrimmed,
    };
  }

  function writeLeafText(node, nextVal) {
    const prev = node.nodeValue;
    const rec = originals.texts.get(node);
    if (rec && rec.zh === prev) {
      rec.zh = nextVal;
    } else {
      originals.texts.set(node, { orig: prev, zh: nextVal });
    }
    if (node.nodeValue !== nextVal) {
      node.nodeValue = nextVal;
    }
  }

  function writeAttr(el, attr, nextVal) {
    const prev = el.getAttribute(attr);
    let map = originals.attrs.get(el);
    if (!map) {
      map = new Map();
      originals.attrs.set(el, map);
    }
    const rec = map.get(attr);
    if (rec && rec.zh === prev) {
      rec.zh = nextVal;
    } else {
      map.set(attr, { orig: prev, zh: nextVal });
    }
    if (prev !== nextVal) {
      el.setAttribute(attr, nextVal);
    }
  }

  function restoreElementAndText(node) {
    if (node.nodeType === 3) {
      const rec = originals.texts.get(node);
      if (rec) {
        if (node.nodeValue === rec.zh) node.nodeValue = rec.orig;
        originals.texts.delete(node);
      }
      translatedNodes.delete(node);
    } else if (node.nodeType === 1) {
      const amap = originals.attrs.get(node);
      if (amap) {
        for (const [attr, rec] of amap.entries()) {
          if (node.getAttribute(attr) === rec.zh && rec.orig !== null) {
            node.setAttribute(attr, rec.orig);
          }
        }
        originals.attrs.delete(node);
      }
      if (node.shadowRoot) restoreSubtree(node.shadowRoot);
    }
  }

  function restoreSubtree(root) {
    if (!root) return;
    try {
      const walker = document.createTreeWalker(root, 1 | 4 /* SHOW_ELEMENT | SHOW_TEXT */);
      let cur = root;
      restoreElementAndText(cur);
      while ((cur = walker.nextNode())) {
        restoreElementAndText(cur);
      }
    } catch (_) {}
  }

  function translateAttributes(el, ctx) {
    if (!el || el.nodeType !== 1 || isImmuneElement(el)) {
      // 即使输入控件本身正文免疫，仍安全翻译 placeholder/aria-label/title 等提示属性（绝不碰 value）
      if (el && el.nodeType === 1 && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA')) {
        for (const attr of SAFE_ATTRS) {
          const val = el.getAttribute(attr);
          if (val) {
            const next = translateSingleText(val, ctx, node);
            if (next !== val) writeAttr(el, attr, next);
          }
        }
      }
      return;
    }
    for (const attr of SAFE_ATTRS) {
      const val = el.getAttribute(attr);
      if (val) {
        const next = translateSingleText(val, ctx);
        if (next !== val) writeAttr(el, attr, next);
      }
    }
  }

  function processSubtree(root) {
    if (!root || currentLang !== 'zh') return;
    if (root.nodeType === 3) {
      if (translatedNodes.has(root) || shouldSkipNode(root)) return;
      const val = root.nodeValue;
      if (!val || !/[a-zA-Z]/.test(val)) {
        if (val && val.trim()) translatedNodes.add(root);
        return;
      }
      const next = translateSingleText(val, makeCtx(), root);
      if (next !== val) {
        writeLeafText(root, next);
        translatedNodes.add(root);
      }
      return;
    }

    if (root.nodeType !== 1 && root.nodeType !== 9 && root.nodeType !== 11) return;
    if (root.nodeType === 1 && isImmuneElement(root)) {
      translateAttributes(root, makeCtx());
      return;
    }

    const ctx = makeCtx();
    try {
      if (root.nodeType === 1) translateAttributes(root, ctx);
      const walker = document.createTreeWalker(root, 1 | 4 /* SHOW_ELEMENT | SHOW_TEXT */);
      let node;
      while ((node = walker.nextNode())) {
        if (node.nodeType === 1) {
          if (node.id === 'chameleon-toggle-root') continue;
          translateAttributes(node, ctx);
          if (node.shadowRoot) {
            processSubtree(node.shadowRoot);
          }
        } else if (node.nodeType === 3) {
          if (translatedNodes.has(node) || shouldSkipNode(node)) continue;
          const val = node.nodeValue;
          if (!val || !/[a-zA-Z]/.test(val)) {
            if (val && val.trim()) translatedNodes.add(node);
            continue;
          }
          const next = translateSingleText(val, ctx, node);
          if (next !== val) {
            writeLeafText(node, next);
            translatedNodes.add(node);
          }
        }
      }
    } catch (_) {}
  }

  // ===== 微任务聚合与 DOM 树祖先包含剪枝调度器 =====
  let pendingNodes = new Set();
  let microtaskScheduled = false;
  let observer = null;
  let sweepTimers = [];
  let cancelled = false;

  function flushPending() {
    microtaskScheduled = false;
    if (cancelled || currentLang !== 'zh' || pendingNodes.size === 0) {
      pendingNodes.clear();
      return;
    }
    const batch = Array.from(pendingNodes);
    pendingNodes.clear();

    // 祖先包含剪枝：若任意父/祖先节点也在本批队列中，跳过子节点避免 O(N^2) 嵌套扫描
    const batchSet = new Set(batch);
    const roots = [];
    for (let i = 0; i < batch.length; i++) {
      const n = batch[i];
      if (!n || !n.isConnected) continue;
      let hasAncestor = false;
      let p = n.parentElement;
      while (p) {
        if (batchSet.has(p)) {
          hasAncestor = true;
          break;
        }
        p = p.parentElement;
      }
      if (!hasAncestor) roots.push(n);
    }

    for (let i = 0; i < roots.length; i++) {
      processSubtree(roots[i]);
    }
  }

  function scheduleNode(node) {
    if (!node || cancelled || currentLang !== 'zh') return;
    pendingNodes.add(node);
    if (!microtaskScheduled) {
      microtaskScheduled = true;
      queueMicrotask(flushPending);
    }
  }

  function applyLanguageMode(targetLang, rebuildReset = false) {
    currentLang = targetLang === 'en' ? 'en' : 'zh';
    savePref(PREF_LANG_KEY, currentLang);
    updateToggleLabel();

    if (currentLang === 'en') {
      restoreSubtree(document.body || document.documentElement);
      if (originalDocLang !== null) document.documentElement.lang = originalDocLang;
      return;
    }

    if (originalDocLang === null) {
      originalDocLang = document.documentElement.lang || 'en';
    }
    document.documentElement.lang = 'zh-CN';
    if (rebuildReset) {
      restoreSubtree(document.body || document.documentElement);
      translatedNodes = new WeakSet();
      stringCache.clear();
    }
    if (document.body) {
      processSubtree(document.body);
    }
  }

  // ===== 右下角轻量半透明「中/英」悬浮切换球 =====
  let toggleEl = null;
  let menuEl = null;
  let btnMain = null;

  function updateToggleLabel() {
    if (!btnMain) return;
    btnMain.textContent = currentLang === 'zh' ? '中' : 'EN';
    btnMain.title = `Project Chameleon (${FINGERPRINT})\n左键：切换中/英文\n右键/双击：设置菜单\n拖动：调整位置`;
  }

  function closeContextMenu() {
    if (menuEl && menuEl.parentNode) {
      menuEl.parentNode.removeChild(menuEl);
      menuEl = null;
    }
  }

  function openContextMenu() {
    closeContextMenu();
    if (!toggleEl || !document.body) return;
    menuEl = document.createElement('div');
    menuEl.dataset.chameleonIgnore = '1';
    menuEl.style.cssText = [
      'position:fixed',
      'z-index:2147483647',
      'min-width:190px',
      'padding:6px',
      'border-radius:10px',
      'background:rgba(28,28,32,0.96)',
      'color:#f3f4f6',
      'border:1px solid rgba(255,255,255,0.14)',
      'box-shadow:0 8px 24px rgba(0,0,0,0.45)',
      'font:12px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif',
      'backdrop-filter:blur(10px)',
      'user-select:none',
    ].join(';');

    const rect = toggleEl.getBoundingClientRect();
    menuEl.style.right = `${Math.max(8, window.innerWidth - rect.right)}px`;
    menuEl.style.bottom = `${Math.max(8, window.innerHeight - rect.top + 8)}px`;

    const mkItem = (label, onClick) => {
      const row = document.createElement('div');
      row.textContent = label;
      row.style.cssText = 'padding:6px 10px;border-radius:6px;cursor:pointer;display:flex;align-items:center;justify-content:space-between;';
      row.onmouseenter = () => { row.style.background = 'rgba(255,255,255,0.12)'; };
      row.onmouseleave = () => { row.style.background = 'transparent'; };
      row.onclick = (e) => {
        e.stopPropagation();
        onClick();
        closeContextMenu();
      };
      return row;
    };

    const header = document.createElement('div');
    header.textContent = `🦎 Chameleon · ${Object.keys(dictionary).length} 词条`;
    header.style.cssText = 'padding:4px 10px 6px;color:#9ca3af;font-size:11px;border-bottom:1px solid rgba(255,255,255,0.1);margin-bottom:4px;';
    menuEl.appendChild(header);

    menuEl.appendChild(
      mkItem(currentLang === 'zh' ? '切换为英文原版 (EN)' : '切换为简体中文 (中)', () => {
        applyLanguageMode(currentLang === 'zh' ? 'en' : 'zh');
      })
    );
    menuEl.appendChild(
      mkItem(`${englishLabelsMode ? '✓ ' : '○ '}专业选项名保留英文`, () => {
        englishLabelsMode = !englishLabelsMode;
        savePref(PREF_EN_LABELS_KEY, englishLabelsMode ? '1' : '0');
        if (currentLang === 'zh') applyLanguageMode('zh', true);
      })
    );
    menuEl.appendChild(
      mkItem('↻ 立即重新扫描整页', () => {
        if (currentLang === 'zh') applyLanguageMode('zh', true);
      })
    );

    document.body.appendChild(menuEl);
  }

  function mountToggleBall() {
    // 跳过极窄内嵌 iframe，仅在正常主视图窗口显示悬浮切换球
    if (!document.body || window.innerWidth < 260 || window.innerHeight < 200) return;
    if (document.getElementById('chameleon-toggle-root')) return;

    toggleEl = document.createElement('div');
    toggleEl.id = 'chameleon-toggle-root';
    toggleEl.dataset.chameleonIgnore = '1';
    toggleEl.style.cssText = [
      'position:fixed',
      'z-index:2147483646',
      'right:14px',
      'bottom:14px',
      'width:30px',
      'height:30px',
      'border-radius:999px',
      'background:rgba(32,34,40,0.68)',
      'color:#e5e7eb',
      'border:1px solid rgba(255,255,255,0.18)',
      'box-shadow:0 2px 10px rgba(0,0,0,0.28)',
      'display:flex',
      'align-items:center',
      'justify-content:center',
      'font:600 11px/1 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif',
      'cursor:pointer',
      'opacity:0.62',
      'transition:opacity .15s,transform .15s',
      'user-select:none',
      'backdrop-filter:blur(6px)',
    ].join(';');

    // 恢复上次拖动位置
    try {
      const savedPos = JSON.parse(loadPref(PREF_POS_KEY) || 'null');
      if (savedPos && Number.isFinite(savedPos.right) && Number.isFinite(savedPos.bottom)) {
        toggleEl.style.right = `${Math.min(Math.max(8, savedPos.right), Math.max(8, window.innerWidth - 42))}px`;
        toggleEl.style.bottom = `${Math.min(Math.max(8, savedPos.bottom), Math.max(8, window.innerHeight - 42))}px`;
      }
    } catch (_) {}

    btnMain = toggleEl;
    updateToggleLabel();

    toggleEl.onmouseenter = () => { toggleEl.style.opacity = '1'; toggleEl.style.transform = 'scale(1.06)'; };
    toggleEl.onmouseleave = () => { toggleEl.style.opacity = '0.62'; toggleEl.style.transform = 'scale(1)'; };

    let dragged = false;
    toggleEl.onmousedown = (e) => {
      if (e.button !== 0) return;
      dragged = false;
      const startX = e.clientX;
      const startY = e.clientY;
      const rect = toggleEl.getBoundingClientRect();
      const startRight = window.innerWidth - rect.right;
      const startBottom = window.innerHeight - rect.bottom;

      const onMove = (me) => {
        const dx = me.clientX - startX;
        const dy = me.clientY - startY;
        if (Math.abs(dx) > 4 || Math.abs(dy) > 4) dragged = true;
        if (!dragged) return;
        const nextR = Math.min(Math.max(8, startRight - dx), Math.max(8, window.innerWidth - 42));
        const nextB = Math.min(Math.max(8, startBottom - dy), Math.max(8, window.innerHeight - 42));
        toggleEl.style.right = `${nextR}px`;
        toggleEl.style.bottom = `${nextB}px`;
      };
      const onUp = () => {
        window.removeEventListener('mousemove', onMove);
        window.removeEventListener('mouseup', onUp);
        if (dragged) {
          savePref(PREF_POS_KEY, JSON.stringify({
            right: parseFloat(toggleEl.style.right),
            bottom: parseFloat(toggleEl.style.bottom),
          }));
        }
      };
      window.addEventListener('mousemove', onMove);
      window.addEventListener('mouseup', onUp);
    };

    toggleEl.onclick = (e) => {
      e.stopPropagation();
      if (dragged) return;
      closeContextMenu();
      applyLanguageMode(currentLang === 'zh' ? 'en' : 'zh');
    };
    toggleEl.ondblclick = (e) => {
      e.stopPropagation();
      openContextMenu();
    };
    toggleEl.oncontextmenu = (e) => {
      e.preventDefault();
      e.stopPropagation();
      openContextMenu();
    };

    document.body.appendChild(toggleEl);
  }

  const onStorageSync = (e) => {
    if (e.key === PREF_LANG_KEY && e.newValue) {
      applyLanguageMode(e.newValue);
    } else if (e.key === PREF_EN_LABELS_KEY) {
      englishLabelsMode = e.newValue === '1';
      if (currentLang === 'zh') applyLanguageMode('zh', true);
    }
  };

  const onDocClickClose = () => closeContextMenu();

  function start() {
    if (cancelled || !document.body) return;
    mountToggleBall();
    applyLanguageMode(currentLang);

    observer = new MutationObserver((mutations) => {
      if (cancelled || currentLang !== 'zh') return;
      for (let i = 0; i < mutations.length; i++) {
        const m = mutations[i];
        if (m.type === 'characterData') {
          translatedNodes.delete(m.target);
          scheduleNode(m.target);
        } else if (m.type === 'attributes') {
          if (m.target && !shouldSkipNode(m.target)) {
            translateAttributes(m.target, makeCtx());
          }
        } else if (m.type === 'childList' && m.addedNodes && m.addedNodes.length) {
          for (let j = 0; j < m.addedNodes.length; j++) {
            scheduleNode(m.addedNodes[j]);
          }
        }
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true,
      attributes: true,
      attributeFilter: SAFE_ATTRS,
    });

    // 多阶梯兜底扫描，捕获 Ctrl+R 或异步延迟加载的 React 分片
    for (const delay of [50, 200, 600, 1500, 3000]) {
      sweepTimers.push(setTimeout(() => {
        if (!cancelled && currentLang === 'zh' && document.body) {
          mountToggleBall();
          processSubtree(document.body);
        }
      }, delay));
    }

    window.addEventListener('storage', onStorageSync);
    window.addEventListener('click', onDocClickClose);
  }

  window.__chameleonSetLang = (lang) => applyLanguageMode(lang);
  window.__chameleonCleanup = () => {
    cancelled = true;
    if (observer) observer.disconnect();
    for (const t of sweepTimers) clearTimeout(t);
    sweepTimers = [];
    window.removeEventListener('DOMContentLoaded', start);
    window.removeEventListener('storage', onStorageSync);
    window.removeEventListener('click', onDocClickClose);
    closeContextMenu();
    if (toggleEl && toggleEl.parentNode) toggleEl.parentNode.removeChild(toggleEl);
    toggleEl = null;
    restoreSubtree(document.body || document.documentElement);
  };

  if (document.body) {
    start();
  } else {
    window.addEventListener('DOMContentLoaded', start);
  }
})();
