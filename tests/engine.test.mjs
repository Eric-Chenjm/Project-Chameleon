import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const ROOT = path.resolve(import.meta.dirname, '..');
const rules = require(path.join(ROOT, 'src', 'runtime', 'rules.js'));

function loadMergedDict() {
  const dictDir = path.join(ROOT, 'src', 'dict');
  const merged = {};
  for (const fn of fs.readdirSync(dictDir).sort()) {
    if (!fn.endsWith('.json')) continue;
    Object.assign(merged, JSON.parse(fs.readFileSync(path.join(dictDir, fn), 'utf8')));
  }
  return merged;
}

function makeCtx(overrides = {}) {
  const dictionary = loadMergedDict();
  const lowerDictionary = new Map();
  for (const [k, v] of Object.entries(dictionary)) {
    const lk = k.toLowerCase();
    if (!lowerDictionary.has(lk)) lowerDictionary.set(lk, v);
  }
  const stringCache = new Map();
  return {
    dictionary,
    lowerDictionary,
    customDictionary: new Map(),
    englishLabelsMode: false,
    stringCache,
    cacheSet: (k, v) => stringCache.set(k, v),
    replaceTrimmed: (text, trimmed, fixed) => {
      if (text === trimmed) return fixed;
      const idx = text.indexOf(trimmed);
      return idx === -1 ? fixed : text.slice(0, idx) + fixed + text.slice(idx + trimmed.length);
    },
    ...overrides,
  };
}

test('v3.0 词典与动态规则：核心设置项与 2.34.0 高频文案翻译正确且首尾空格保留', () => {
  const ctx = makeCtx();
  assert.equal(rules.translateSingleText('  General  ', ctx), '  常规设置  ');
  assert.equal(rules.translateSingleText('Environments', ctx), '环境配置');
  assert.equal(rules.translateSingleText('Extra High', ctx), '极高');
  assert.equal(rules.translateSingleText('Thinking effort', ctx), '推理深度');
  assert.equal(rules.translateSingleText('Inbox Mode', ctx), '收件箱模式');
  assert.equal(rules.translateSingleText('Resets in 2d 5h', ctx), '2 天 5 小时后重置');
  assert.equal(rules.translateSingleText('Resets in <1m', ctx), '不到 1 分钟后重置');
  assert.equal(rules.translateSingleText('Thought for 14s', ctx), '已深度思考 14 秒');
  assert.equal(rules.translateSingleText('Proceed • 3', ctx), '继续执行 • 3');
});

test('v3.0 权限安全守卫：完整保留命令、路径和 $ 特殊字符且保持幂等', () => {
  const ctx = makeCtx();
  const cmdTarget = "echo $HOME && rm -rf /tmp/$'test'";
  const input = `Yes, and always allow '${cmdTarget}' in this conversation`;
  const once = rules.translateSingleText(input, ctx);
  assert.equal(once, `允许，并在当前会话中始终允许 '${cmdTarget}'`);
  // 二次调用绝对幂等，不能破坏已翻译内容或 $ 符号
  assert.equal(rules.translateSingleText(once, ctx), once);

  const allowInput = 'Allow https://example.com/$path?a=1&b=2?';
  const allowOnce = rules.translateSingleText(allowInput, ctx);
  assert.equal(allowOnce, '是否允许 https://example.com/$path?a=1&b=2？');
  assert.equal(rules.translateSingleText(allowOnce, ctx), allowOnce);
});

test('v3.0 专业选项保留英文开关与文件/协议短路免疫', () => {
  const ctxEn = makeCtx({ englishLabelsMode: true });
  assert.equal(rules.translateSingleText('Extra High', ctxEn), 'Extra High');
  assert.equal(rules.translateSingleText('Request Review', ctxEn), 'Request Review');
  // 非预设项依然正常翻译
  assert.equal(rules.translateSingleText('Thinking effort', ctxEn), '推理深度');

  // 路径与 URL 免疫
  const ctxZh = makeCtx();
  assert.equal(rules.translateSingleText('https://github.com/test/repo', ctxZh), 'https://github.com/test/repo');
  assert.equal(rules.translateSingleText('C:\\Users\\demo\\General', ctxZh), 'C:\\Users\\demo\\General');
  assert.equal(rules.translateSingleText('plugin://swarm--swarm_board-1234/', ctxZh), 'plugin://swarm--swarm_board-1234/');
});

test('dist/chameleon-overlay.js 编译产物存在且可在沙箱上下文无报错解析', () => {
  const overlayPath = path.join(ROOT, 'dist', 'chameleon-overlay.js');
  assert.ok(fs.existsSync(overlayPath), 'dist/chameleon-overlay.js 应当已编译生成');
  const code = fs.readFileSync(overlayPath, 'utf8');
  assert.doesNotThrow(() => new vm.Script(code, { filename: 'chameleon-overlay.js' }));
});
