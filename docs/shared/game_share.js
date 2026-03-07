/* Game Score Share Buttons — self-contained IIFE
   Adds share buttons (LINE, copy) to the victory modal and game-over banner.
   iOS-safe: no arrow functions, no optional chaining.
   Requires: #victoryModal, #gBanner existing in the page. */
(function(){
  var css = document.createElement('style');
  css.textContent = [
    '.game-share-row{display:flex;gap:8px;justify-content:center;margin-top:12px;flex-wrap:wrap}',
    '.game-share-btn{border:none;border-radius:8px;padding:8px 16px;font-size:.82rem;',
    'font-weight:700;cursor:pointer;display:inline-flex;align-items:center;gap:4px}',
    '.gs-line{background:#06C755;color:#fff}',
    '.gs-copy{background:#21262d;color:#c9d1d9;border:1px solid #30363d}'
  ].join('');
  document.head.appendChild(css);

  function makeShareRow(getText) {
    var row = document.createElement('div');
    row.className = 'game-share-row';

    var lineBtn = document.createElement('button');
    lineBtn.className = 'game-share-btn gs-line';
    lineBtn.textContent = 'LINE \u5206\u4eab';
    lineBtn.addEventListener('click', function(){
      var msg = getText() + '\n' + location.href;
      window.open('https://social-plugins.line.me/lineit/share?url=' + encodeURIComponent(location.href) + '&text=' + encodeURIComponent(msg), '_blank', 'width=500,height=600');
    });

    var copyBtn = document.createElement('button');
    copyBtn.className = 'game-share-btn gs-copy';
    copyBtn.textContent = '\uD83D\uDCCB \u8907\u88FD\u6210\u7E3E';
    copyBtn.addEventListener('click', function(){
      var msg = getText() + '\n' + location.href;
      if (navigator.clipboard) {
        navigator.clipboard.writeText(msg).then(function(){
          copyBtn.textContent = '\u2705 \u5DF2\u8907\u88FD';
          setTimeout(function(){ copyBtn.textContent = '\uD83D\uDCCB \u8907\u88FD\u6210\u7E3E'; }, 2000);
        });
      }
    });

    row.appendChild(lineBtn);
    row.appendChild(copyBtn);
    return row;
  }

  /* Add share buttons to victory modal */
  var vm = document.getElementById('victoryModal');
  if (vm) {
    var vc = vm.querySelector('.victory-content');
    if (vc) {
      var closeBtn = vm.querySelector('#btnVictoryClose');
      var shareRow = makeShareRow(function(){
        var region = document.getElementById('victoryRegion');
        var rn = region ? region.textContent : '';
        return '\uD83C\uDFF0 \u6211\u5728 AI \u6578\u5B78\u5E1D\u570B\u5F81\u670D\u4E86 ' + rn + '\uFF01';
      });
      if (closeBtn) {
        vc.insertBefore(shareRow, closeBtn);
      } else {
        vc.appendChild(shareRow);
      }
    }
  }

  /* Add share buttons to game-over banner via MutationObserver */
  var gb = document.getElementById('gBanner');
  if (gb && window.MutationObserver) {
    var shareAdded = false;
    new MutationObserver(function(mutations){
      for (var i = 0; i < mutations.length; i++) {
        var t = gb.textContent || '';
        if (t.indexOf('\u7D50\u675F') !== -1 && t.indexOf('\u5206\u6578') !== -1 && !shareAdded) {
          shareAdded = true;
          var row = makeShareRow(function(){
            var txt = gb.textContent || '';
            return '\uD83C\uDFC6 ' + txt.replace(/\n/g, ' ').trim();
          });
          gb.appendChild(row);
          /* Reset flag after 3s so it works on next game */
          setTimeout(function(){ shareAdded = false; }, 3000);
        }
      }
    }).observe(gb, { childList: true, characterData: true, subtree: true });
  }
})();
