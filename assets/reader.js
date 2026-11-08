const pages = [...document.querySelectorAll('#pages figure')];
const controls = document.querySelectorAll('.reader-controls');
const buttons = document.querySelectorAll('[data-step]');
const select = document.querySelector('#page-select');
const layout = document.querySelector('#layout');
const position = document.querySelector('#position');
let page = 1;
let scrolling = false;

for (let number = 1; number <= pages.length; number += 1) {
  select.add(new Option(number + ' / ' + pages.length, number));
}

function render() {
  const requested = Number(location.hash.match(/^#page-(\d+)$/)?.[1]);
  page = requested >= 1 && requested <= pages.length ? requested : 1;
  pages.forEach((figure, index) => {
    figure.hidden = !scrolling && index + 1 !== page;
  });
  select.value = page;
  position.textContent = 'Page ' + page + ' of ' + pages.length;
  buttons.forEach(button => {
    const target = page + Number(button.dataset.step);
    button.disabled = target < 1 || target > pages.length;
  });
}

function show(number) {
  if (number < 1 || number > pages.length) return;
  if (number !== page) history.pushState(null, '', '#page-' + number);
  render();
  pages[page - 1].scrollIntoView();
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
  pages[page - 1].scrollIntoView();
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
if (location.hash) pages[page - 1].scrollIntoView();
