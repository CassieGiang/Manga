const pages = [...document.querySelectorAll('#pages figure')];
const controls = document.querySelectorAll('.reader-controls');
const buttons = document.querySelectorAll('[data-step]');
const select = document.querySelector('#page-select');
const layout = document.querySelector('#layout');
const position = document.querySelector('#position');
let page = 0;
let scrolling = false;

pages.forEach((figure, index) => {
  select.add(new Option(figure.querySelector('figcaption').textContent, index));
});

function render() {
  const requested = pages.findIndex(figure => '#' + figure.id === location.hash);
  page = Math.max(requested, 0);
  pages.forEach((figure, index) => {
    figure.hidden = !scrolling && index !== page;
  });
  select.value = page;
  position.textContent = pages[page].querySelector('figcaption').textContent;
  buttons.forEach(button => {
    const target = page + Number(button.dataset.step);
    button.disabled = target < 0 || target >= pages.length;
  });
}

function show(number) {
  if (number < 0 || number >= pages.length) return;
  if (number !== page) history.pushState(null, '', '#' + pages[number].id);
  render();
  pages[page].scrollIntoView();
}

buttons.forEach(button => button.addEventListener('click', () => show(page + Number(button.dataset.step))));
select.addEventListener('change', () => show(Number(select.value)));
layout.addEventListener('click', () => {
  scrolling = !scrolling;
  layout.setAttribute('aria-pressed', String(scrolling));
  show(page);
});
window.addEventListener('hashchange', () => {
  render();
  pages[page].scrollIntoView();
});
window.addEventListener('keydown', event => {
  if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey || event.target.closest('input, select, textarea, [contenteditable]')) return;
  if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
    event.preventDefault();
    show(page + (event.key === 'ArrowRight' ? 1 : -1));
  }
});
render();
controls.forEach(control => { control.hidden = false; });
if (location.hash) pages[page].scrollIntoView();
