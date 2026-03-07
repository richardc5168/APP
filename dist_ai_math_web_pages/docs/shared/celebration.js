(function(){
  var style=document.createElement('style');
  style.textContent='.cele-overlay{position:fixed;top:0;left:0;width:100%;height:100%;z-index:9998;pointer-events:none;display:none}.cele-overlay.show{display:block}.cele-msg{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%) scale(0);z-index:9999;background:#161b22;border:2px solid #58a6ff;border-radius:16px;padding:32px 40px;text-align:center;pointer-events:auto;transition:transform .4s cubic-bezier(.34,1.56,.64,1);box-shadow:0 8px 40px rgba(88,166,255,.25)}.cele-overlay.show .cele-msg{transform:translate(-50%,-50%) scale(1)}.cele-emoji{font-size:3rem;margin-bottom:8px}.cele-title{color:#fff;font-size:1.3rem;font-weight:800;margin-bottom:4px}.cele-sub{color:#8b949e;font-size:.9rem;margin-bottom:16px}.cele-btn{background:#58a6ff;color:#fff;border:none;border-radius:8px;padding:10px 24px;font-size:.9rem;font-weight:600;cursor:pointer}.cele-btn:hover{opacity:.85}.cele-confetti{position:absolute;width:8px;height:8px;border-radius:2px;animation:confettiFall 1.5s ease-out forwards}@keyframes confettiFall{0%{opacity:1;transform:translateY(0) rotate(0)}100%{opacity:0;transform:translateY(100vh) rotate(720deg)}}';
  document.head.appendChild(style);

  window._showCelebration = function(accuracy, total) {
    var overlay = document.createElement('div');
    overlay.className = 'cele-overlay';
    var emoji = accuracy >= 80 ? '🎉' : accuracy >= 60 ? '👏' : '💪';
    var title = accuracy >= 80 ? '太棒了！' : accuracy >= 60 ? '做得好！' : '繼續加油！';
    overlay.innerHTML = '<div class="cele-msg"><div class="cele-emoji">' + emoji + '</div><div class="cele-title">' + title + '</div><div class="cele-sub">正確率 ' + accuracy + '%（共 ' + total + ' 題）</div><button class="cele-btn" type="button">繼續練習</button></div>';
    document.body.appendChild(overlay);

    var colors = ['#58a6ff','#3fb950','#f0883e','#fbbf24','#a371f7','#f47067'];
    for (var i = 0; i < 30; i++) {
      var c = document.createElement('div');
      c.className = 'cele-confetti';
      c.style.left = (Math.random() * 100) + '%';
      c.style.top = '-10px';
      c.style.background = colors[Math.floor(Math.random() * colors.length)];
      c.style.animationDelay = (Math.random() * 0.8) + 's';
      c.style.width = (4 + Math.random() * 8) + 'px';
      c.style.height = (4 + Math.random() * 8) + 'px';
      overlay.appendChild(c);
    }

    setTimeout(function(){ overlay.classList.add('show'); }, 50);
    overlay.querySelector('.cele-btn').addEventListener('click', function(){
      overlay.classList.remove('show');
      setTimeout(function(){ overlay.remove(); }, 400);
    });
  };
})();
