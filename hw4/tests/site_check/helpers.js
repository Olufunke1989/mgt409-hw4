window.__w = ms => new Promise(r => setTimeout(r, ms));
window.__ask = async (text) => {
  if (!document.querySelector('.chat-panel')) { document.querySelector('.chat-launcher').click(); await __w(700); }
  const ta = document.getElementById('chat-text');
  Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set.call(ta, text);
  ta.dispatchEvent(new Event('input', { bubbles: true }));
  await __w(150);
  document.querySelector('.chat-input button[type=submit]').click();
  const n0 = document.querySelectorAll('.bubble-assistant').length;
  for (let i = 0; i < 240; i++) { await __w(500); if (!document.querySelector('.typing') && document.querySelectorAll('.bubble-assistant').length > n0) break; }
  await __w(1500);
  const b = [...document.querySelectorAll('.bubble-assistant')].pop();
  return b.innerText;
};
true;
