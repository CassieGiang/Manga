// Character sheet tools: find in sheet, open/close all, open a section linked by #id.
const secs = [...document.querySelectorAll('details.sec')];
const filter = document.querySelector('#filter');
const count = document.querySelector('#count');

function openHash() {
  const target = location.hash && document.querySelector(location.hash);
  if (target && target.matches('details')) target.open = true;
}
window.addEventListener('hashchange', openHash);
openHash();

document.querySelectorAll('[data-all]').forEach(button => button.addEventListener('click', () => {
  secs.forEach(sec => { sec.open = button.dataset.all === '1'; });
}));

function unmark(root) {
  root.querySelectorAll('mark').forEach(m => m.replaceWith(...m.childNodes));
  root.normalize();
}

function markText(root, query) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const hits = [];
  for (let node; (node = walker.nextNode());) {
    if (node.nodeValue.toLowerCase().includes(query)) hits.push(node);
  }
  hits.forEach(node => {
    const parts = node.nodeValue.split(new RegExp('(' + query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'i'));
    const frag = document.createDocumentFragment();
    parts.forEach((part, i) => frag.append(i % 2 ? Object.assign(document.createElement('mark'), { textContent: part }) : part));
    node.replaceWith(frag);
  });
  return hits.length;
}

let timer;
if (filter) filter.addEventListener('input', () => {
  clearTimeout(timer);
  timer = setTimeout(() => {
    const query = filter.value.trim().toLowerCase();
    let shown = 0;
    secs.forEach(sec => {
      unmark(sec);
      if (!query) { sec.classList.remove('hide'); return; }
      const found = query.length > 1 && markText(sec, query) > 0;
      sec.classList.toggle('hide', !found);
      if (found) { sec.open = true; shown++; }
    });
    count.textContent = query ? shown + ' of ' + secs.length + ' sections' : '';
  }, 200);
});
