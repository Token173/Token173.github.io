/* 纯前端站内搜索，无外部依赖 */
(function(){
  var input=document.getElementById('q'), box=document.getElementById('search-results'), idx=null;
  if(!input||!box) return;
  function load(){
    if(idx) return Promise.resolve(idx);
    return fetch('/assets/search-index.json').then(function(r){return r.json()}).then(function(d){idx=d;return d});
  }
  function render(q){
    load().then(function(items){
      var terms=q.toLowerCase().split(/\s+/).filter(Boolean);
      var hits=items.filter(function(it){
        var hay=(it.t+' '+it.d+' '+it.k+' '+it.c).toLowerCase();
        return terms.every(function(t){return hay.indexOf(t)>-1});
      }).slice(0,12);
      if(!hits.length){box.innerHTML='<div class="empty">没有匹配的内容，试试「倍率」「Claude Code」「model not found」</div>';return}
      box.innerHTML=hits.map(function(it){
        return '<a href="'+it.u+'">'+it.t+'<small>'+it.c+' · '+it.d.slice(0,46)+'</small></a>';
      }).join('');
    }).catch(function(){box.innerHTML='<div class="empty">索引加载失败</div>'});
  }
  var timer;
  input.addEventListener('input',function(){
    var q=this.value.trim(); clearTimeout(timer);
    if(!q){box.hidden=true;return}
    box.hidden=false;
    timer=setTimeout(function(){render(q)},120);
  });
  document.addEventListener('click',function(e){if(!e.target.closest('.search')) box.hidden=true});
  input.addEventListener('focus',function(){if(this.value.trim()) box.hidden=false});
  var params=new URLSearchParams(location.search).get('q');
  if(params){input.value=params;box.hidden=false;render(params)}
})();
