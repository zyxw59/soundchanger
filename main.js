function addMenu() {
  n = numPairs;
  form = document.getElementById('pairs');
  div = document.getElementById('pair-' + n);
  div2 = div.cloneNode(true);
  div2.id = 'pair-' + (n + 1);
  s = div2.childNodes[0]
  e = div2.childNodes[1]
  s.id = 'start-' + (n + 1);
  s.name = s.id;
  e.id = 'end-' + (n + 1);
  e.name = e.id;
  form.appendChild(div2);
  numPairs++;
}

function removeMenu() {
  if (numPairs > 0) {
    form = document.getElementById('pairs');
    form.removeChild(form.lastChild);
    numPairs--;
  }
}

function insert(value) {
  word = document.getElementById('word')
  if (word.selectionStart || word.selectionStart == '0') {
    var s = word.selectionStart;
    var e = word.selectionEnd;
    word.value = word.value.substring(0, startPos) + value +  word.value.substring(endPos, word.value.length);
  } else {
    word.value += value;
  }
}