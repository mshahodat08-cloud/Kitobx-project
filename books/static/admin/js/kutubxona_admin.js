(function(){
    var root=document.documentElement;
    var btn=document.querySelector('.kx-admin-theme');
    function getTheme(){var saved=localStorage.getItem('kitobx-admin-theme');if(saved==='dark'||saved==='light')return saved;return root.dataset.kxAdminTheme||'dark'}
    function setTheme(theme){root.dataset.kxAdminTheme=theme;localStorage.setItem('kitobx-admin-theme',theme);if(btn)btn.setAttribute('aria-pressed',String(theme==='dark'))}
    setTheme(getTheme());
    if(btn){btn.addEventListener('click',function(){setTheme(root.dataset.kxAdminTheme==='dark'?'light':'dark')})}

    var dataEl=document.getElementById('kx-admin-dashboard-data');
    if(!dataEl)return;
    var data={};
    try{data=JSON.parse(dataEl.textContent||'{}')}catch(e){return}
    var metrics=data.metrics||{};
    document.querySelectorAll('[data-kx-metric]').forEach(function(el){var key=el.getAttribute('data-kx-metric');el.textContent=metrics[key]!==undefined?metrics[key]:0});

    function css(name){return getComputedStyle(document.documentElement).getPropertyValue(name).trim()}
    function prep(canvas){if(!canvas)return null;var ctx=canvas.getContext('2d');var ratio=window.devicePixelRatio||1;var w=canvas.clientWidth||canvas.parentElement.clientWidth;var h=canvas.clientHeight||canvas.parentElement.clientHeight;canvas.width=w*ratio;canvas.height=h*ratio;ctx.setTransform(ratio,0,0,ratio,0,0);return {ctx:ctx,w:w,h:h}}
    function roundedRect(ctx,x,y,w,h,r){ctx.beginPath();ctx.moveTo(x+r,y);ctx.arcTo(x+w,y,x+w,y+h,r);ctx.arcTo(x+w,y+h,x,y+h,r);ctx.arcTo(x,y+h,x,y,r);ctx.arcTo(x,y,x+w,y,r);ctx.closePath()}
    function text(ctx,txt,x,y,color,size,weight,align){ctx.fillStyle=color;ctx.font=(weight||700)+' '+(size||12)+'px Inter, system-ui, sans-serif';ctx.textAlign=align||'left';ctx.fillText(String(txt),x,y)}

    function drawLine(){var c=document.getElementById('kx-growth-chart'),p=prep(c);if(!p)return;var ctx=p.ctx,w=p.w,h=p.h;var pad=34;var labels=(data.growth&&data.growth.labels)||[];var users=(data.growth&&data.growth.users)||[];var books=(data.growth&&data.growth.books)||[];var all=users.concat(books);var max=Math.max(1,Math.max.apply(null,all));ctx.clearRect(0,0,w,h);ctx.strokeStyle=css('--kx-border');ctx.lineWidth=1;for(var i=0;i<5;i++){var y=pad+(h-pad*2)*(i/4);ctx.beginPath();ctx.moveTo(pad,y);ctx.lineTo(w-pad,y);ctx.stroke()}function line(vals,color){ctx.strokeStyle=color;ctx.lineWidth=3;ctx.beginPath();vals.forEach(function(v,i){var x=pad+(w-pad*2)*(i/Math.max(1,vals.length-1));var y=h-pad-(h-pad*2)*(v/max);if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y)});ctx.stroke();vals.forEach(function(v,i){var x=pad+(w-pad*2)*(i/Math.max(1,vals.length-1));var y=h-pad-(h-pad*2)*(v/max);ctx.fillStyle=color;ctx.beginPath();ctx.arc(x,y,4,0,Math.PI*2);ctx.fill()})}line(users,css('--kx-accent'));line(books,css('--kx-accent-2'));labels.forEach(function(l,i){var x=pad+(w-pad*2)*(i/Math.max(1,labels.length-1));text(ctx,l,x,h-10,css('--kx-muted'),11,800,'center')});text(ctx,'Userlar',pad,18,css('--kx-accent'),12,900);text(ctx,'Kitoblar',pad+82,18,css('--kx-accent-2'),12,900)}

    function drawDonut(){var c=document.getElementById('kx-category-chart'),p=prep(c);if(!p)return;var ctx=p.ctx,w=p.w,h=p.h;var labels=(data.categories&&data.categories.labels)||[];var vals=(data.categories&&data.categories.values)||[];var total=vals.reduce(function(a,b){return a+b},0)||1;var cx=w/2,cy=h/2-8,r=Math.min(w,h)*.32,inner=r*.56;var start=-Math.PI/2;var colors=[css('--kx-accent'),css('--kx-accent-2'),'#9d4edd','#34d399','#fbbf24','#60a5fa'];ctx.clearRect(0,0,w,h);vals.forEach(function(v,i){var a=(v/total)*Math.PI*2;ctx.beginPath();ctx.moveTo(cx,cy);ctx.fillStyle=colors[i%colors.length];ctx.arc(cx,cy,r,start,start+a);ctx.closePath();ctx.fill();start+=a});ctx.globalCompositeOperation='destination-out';ctx.beginPath();ctx.arc(cx,cy,inner,0,Math.PI*2);ctx.fill();ctx.globalCompositeOperation='source-over';text(ctx,total,cx,cy+5,css('--kx-text'),28,950,'center');text(ctx,'kitob',cx,cy+26,css('--kx-muted'),12,800,'center');var y=h-50;labels.slice(0,4).forEach(function(l,i){var x=(i%2)*(w/2)+18;var yy=y+Math.floor(i/2)*22;ctx.fillStyle=colors[i%colors.length];ctx.fillRect(x,yy-9,10,10);text(ctx,l,x+16,yy,css('--kx-muted'),11,800)})}

    function drawBars(){var c=document.getElementById('kx-top-books-chart'),p=prep(c);if(!p)return;var ctx=p.ctx,w=p.w,h=p.h;var labels=(data.topBooks&&data.topBooks.labels)||[];var reads=(data.topBooks&&data.topBooks.reads)||[];var views=(data.topBooks&&data.topBooks.views)||[];var max=Math.max(1,Math.max.apply(null,reads.concat(views)));var padL=150,padR=30,rowH=(h-34)/Math.max(1,labels.length);ctx.clearRect(0,0,w,h);labels.forEach(function(l,i){var y=22+i*rowH;var readW=(w-padL-padR)*(reads[i]/max);var viewW=(w-padL-padR)*(views[i]/max);text(ctx,l.length>22?l.slice(0,21)+'…':l,12,y+12,css('--kx-muted'),11,850);roundedRect(ctx,padL,y,viewW,10,5);ctx.fillStyle='rgba(255,74,162,.18)';ctx.fill();roundedRect(ctx,padL,y+14,readW,10,5);ctx.fillStyle=css('--kx-accent');ctx.fill();text(ctx,(reads[i]||0)+' o\'qish',padL+Math.max(readW,8)+8,y+24,css('--kx-text'),11,850)});text(ctx,'Ko\'rishlar',padL,14,css('--kx-accent-2'),11,900);text(ctx,'O\'qishlar',padL+90,14,css('--kx-accent'),11,900)}

    function redraw(){drawLine();drawDonut();drawBars()}
    redraw();
    window.addEventListener('resize',function(){clearTimeout(window.__kxChartTimer);window.__kxChartTimer=setTimeout(redraw,120)});
})();
