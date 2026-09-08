import assert from 'node:assert/strict';
import test from 'node:test';
import { pressKey } from '../scripts/browser_harness.mjs';

for (const [name, identity, text] of [
  ['Tab', { key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9 }],
  ['Enter', { key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13 }, '\r'],
  ['Escape', { key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 }],
  ['Space', { key: ' ', code: 'Space', windowsVirtualKeyCode: 32 }, ' '],
]) {
  test(`${name} sends its DOM identity and text only on keyDown`, async () => {
    const calls = [];
    await pressKey(async (method, params) => { calls.push([method, params]); }, name);
    assert.deepEqual(calls, [
      ['Input.dispatchKeyEvent', { type: 'keyDown', ...identity, modifiers: 0,
        ...(text === undefined ? {} : { text }) }],
      ['Input.dispatchKeyEvent', { type: 'keyUp', ...identity, modifiers: 0 }],
    ]);
    for (const [, params] of calls) assert.equal(Object.hasOwn(params, 'nativeVirtualKeyCode'), false);
    assert.equal(Object.hasOwn(calls[1][1], 'text'), false);
  });
}

test('Shift uses the CDP bit 8 on both events and does not persist across presses', async () => {
  const calls = [];
  const page = async (method, params) => { calls.push(params); };
  await pressKey(page, 'Tab', { shift: true });
  await pressKey(page, 'Tab', { shift: false });
  await pressKey(page, 'Tab');
  assert.deepEqual(calls.map(params => params.modifiers), [8, 8, 0, 0, 0, 0]);
  assert.ok(calls.every(params => params.key === 'Tab' && params.code === 'Tab'));
});

test('keyUp waits until the keyDown command completes', async () => {
  const calls = [];
  let release;
  const pending = pressKey((method, params) => {
    calls.push(params.type);
    if (params.type === 'keyDown') return new Promise(resolve => { release = resolve; });
  }, 'Enter');
  assert.deepEqual(calls, ['keyDown']);
  release();
  await pending;
  assert.deepEqual(calls, ['keyDown', 'keyUp']);
});

test('unsupported keys and options are rejected before any CDP call', async () => {
  const calls = [];
  const page = async (...args) => { calls.push(args); };
  for (const key of ['ArrowDown', 'F1', 'enter', ' ', '', 'toString', '__proto__', 13, null, undefined]) {
    await assert.rejects(pressKey(page, key), /supports only Tab, Enter, Escape, and Space/);
  }
  for (const options of [
    null, false, 8, [], new Date(), { shift: 1 }, { shift: 'true' }, { shift: undefined },
    { ctrl: true }, { alt: true }, { meta: true }, { modifiers: 1 },
    { nativeVirtualKeyCode: 13 }, { windowsVirtualKeyCode: 13 }, { text: '\r' },
    { shift: true, typo: false }, { [Symbol('shift')]: true }, Object.create({ shift: true }),
    Object.defineProperty({}, 'hidden', { value: true }),
  ]) {
    await assert.rejects(pressKey(page, 'Tab', options), /only a boolean shift/);
  }
  assert.deepEqual(calls, []);
});

test('a rejected keyDown propagates without sending another key event', async () => {
  const calls = [];
  const failure = new Error('CDP transport unavailable');
  await assert.rejects(pressKey(async (method, params) => {
    calls.push(params.type);
    throw failure;
  }, 'Escape'), error => error === failure);
  assert.deepEqual(calls, ['keyDown']);
});
