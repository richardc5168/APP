(function(){
  var el=document.createElement('div');
  el.id='kbdHints';
  el.setAttribute('aria-label','鍵盤快捷鍵');
  el.innerHTML='<button id="kbdToggle" type="button" aria-expanded="false" style="background:none;border:none;color:#8b949e;cursor:pointer;font-size:.8rem;padding:4px 8px;">⌨ 快捷鍵</button><div id="kbdList" style="display:none;margin-top:4px;font-size:.78rem;color:#8b949e;line-height:1.6;">Tab → 切換選項<br>Enter → 送出答案<br>N → 下一題<br>H → 顯示提示</div>';
  el.style.cssText='position:fixed;bottom:60px;left:12px;z-index:9980;background:#161b22;border:1px solid #30363d;border-radius:8px;padding:6px 10px;max-width:160px;';
  document.body.appendChild(el);
  var btn=document.getElementById('kbdToggle');
  var list=document.getElementById('kbdList');
  btn.addEventListener('click',function(){
    var open=list.style.display!=='none';
    list.style.display=open?'none':'block';
    btn.setAttribute('aria-expanded',open?'false':'true');
  });
})();
