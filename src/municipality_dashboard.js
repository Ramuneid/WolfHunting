/* Municipality charts use the same filtered source records as the map. */
const municipalCategories={
 gender:[['Patinas','Patinas'],['Patelė','Patelė'],['unknown','Nežinoma']],
 age:[['Vyresnis nei 1 metų amžiaus','Vyresni nei 1 m.'],['Jauniklis iki 1 metų amžiaus','Jaunikliai iki 1 m.'],['unknown','Nežinomas']],
 health:[['Sveikas','Sveikas'],['Nesveikas','Nesveikas']],
 packMember:[['Taip','Priklausė gaujai'],['Ne','Nepriklausė gaujai'],['unknown','Nežinoma']]
};
const municipalColors=DATA.categoryColors;
function chartNode(tag,attributes={},text){const node=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [key,value] of Object.entries(attributes))node.setAttribute(key,value);if(text!==undefined)node.textContent=text;return node}
function chartTooltip(mark,lines){
 function showChart(x,y){tip.replaceChildren();for(const [index,text] of lines.entries()){const line=document.createElement(index===0?'strong':'div');line.textContent=text;tip.append(line)}tip.hidden=false;const box=tip.getBoundingClientRect();tip.style.left=Math.max(8,Math.min(x+12,window.innerWidth-box.width-10))+'px';tip.style.top=Math.max(8,Math.min(y+12,window.innerHeight-box.height-10))+'px'}
 mark.setAttribute('tabindex','0');mark.setAttribute('role','img');mark.setAttribute('aria-label',lines.join('. '));
 mark.addEventListener('pointermove',e=>showChart(e.clientX,e.clientY));mark.addEventListener('pointerleave',hide);mark.addEventListener('focus',()=>{const b=mark.getBoundingClientRect();showChart(b.x,b.y)});mark.addEventListener('blur',hide);mark.addEventListener('keydown',e=>{if(e.key==='Escape')hide()});
}
function singleHuntingDate(records){return records.length===1?['Medžioklės data: '+records[0].date]:[]}
function municipalityCard(id,title){const card=document.createElement('article');card.className='municipality-card';card.dataset.chart=id;const h=document.createElement('h3');h.textContent=title;card.append(h);return card}
function chartLegend(card,items){const legend=document.createElement('div');legend.className='chart-legend';for(const item of items){const entry=document.createElement('span');const swatch=document.createElement('i');swatch.style.background=item.color;swatch.setAttribute('aria-hidden','true');entry.append(swatch,document.createTextNode(item.text));legend.append(entry)}card.append(legend)}
function addChartTable(card,domain,series,rows){const details=document.createElement('details');details.className='chart-data';const summary=document.createElement('summary');summary.textContent='Duomenų lentelė';details.append(summary);const table=document.createElement('table');const header=document.createElement('tr');for(const text of [domain,...series.map(s=>s.label)]){const cell=document.createElement('th');cell.textContent=text;header.append(cell)}const head=document.createElement('thead');head.append(header);table.append(head);const body=document.createElement('tbody');for(const row of rows){const tr=document.createElement('tr');for(const value of [row.label,...row.values]){const td=document.createElement('td');td.textContent=value;tr.append(td)}body.append(tr)}table.append(body);details.append(table);card.append(details)}
function municipalLine(id,title,records,dimension,category=null){
 const card=municipalityCard(id,title);
 const picked=filterValues(dimension);const keys=picked.length?picked.map(Number).sort((a,b)=>a-b):dimension==='year'?DATA.years:Array.from({length:12},(_,i)=>i+1);
 const shortMonths=['Saus.','Vas.','Kov.','Bal.','Geg.','Birž.','Liep.','Rgp.','Rgs.','Spa.','Lapkr.','Gruod.'];
 const series=category?municipalCategories[category].map(([key,label],i)=>({key,label,color:municipalColors[i]})):[{key:'total',label:'Sumedžiota vilkų',color:municipalColors[0]}];
 const rows=keys.map(key=>({key,label:dimension==='year'?String(key):shortMonths[key-1],values:series.map(s=>records.filter(r=>r[dimension]===key&&(!category||r[category]===s.key)).length)}));
 card.dataset.rows=JSON.stringify(rows);card.dataset.series=JSON.stringify(series);
 if(category)chartLegend(card,series.map(s=>({text:s.label,color:s.color})));
 if(category==='health'){const note=document.createElement('p');note.className='chart-note';note.textContent='Sveikata nežinoma: '+fmt(records.filter(r=>r.health==='unknown').length)+'.';card.append(note)}
 const svg=chartNode('svg',{viewBox:'0 0 600 320',role:'group','aria-label':title});
 const top=64,bottom=270,left=46,right=579,maximum=Math.max(1,...rows.flatMap(r=>r.values));
 const raw=maximum/4,unit=Math.pow(10,Math.floor(Math.log10(raw))),step=[1,2,5,10].map(v=>v*unit).find(v=>v>=raw),tickStep=Math.max(1,step),ymax=Math.ceil(maximum/tickStep)*tickStep;
 const x=i=>rows.length===1?(left+right)/2:left+(keys[i]-keys[0])*(right-left)/(keys.at(-1)-keys[0]);const y=n=>bottom-n/ymax*(bottom-top);
 for(let value=0;value<=ymax;value+=tickStep){svg.append(chartNode('line',{x1:left,x2:right,y1:y(value),y2:y(value),stroke:'#D8D5C4','stroke-width':1}));svg.append(chartNode('text',{x:left-9,y:y(value)+4,'text-anchor':'end',class:'chart-tick'},fmt(value)))}
 svg.append(chartNode('line',{x1:left,x2:right,y1:bottom,y2:bottom,stroke:'#4B574B'}));
 rows.forEach((row,i)=>{svg.append(chartNode('line',{x1:x(i),x2:x(i),y1:bottom,y2:bottom+5,stroke:'#4B574B'}));svg.append(chartNode('text',{x:x(i),y:bottom+24,'text-anchor':'middle',class:'chart-tick'},row.label))});
 series.forEach((s,index)=>{const path=rows.map((row,i)=>(i?'L':'M')+x(i)+','+y(row.values[index])).join('');svg.append(chartNode('path',{d:path,fill:'none',stroke:s.color,'stroke-width':2.5,'stroke-dasharray':index===2?'3 4':index===1?'8 3':'none'}));rows.forEach((row,i)=>{const value=row.values[index];const mark=chartNode('circle',{cx:x(i),cy:y(value),r:4,fill:index===1?'#F7F5E7':s.color,stroke:s.color,'stroke-width':2,'data-value':value,'data-series':s.key,'data-period':row.key});chartTooltip(mark,[lookup.get(active).name,dimension==='year'?row.key+' m.':months[row.key-1],s.label+': '+fmt(value),...singleHuntingDate(records.filter(r=>r[dimension]===row.key&&(!category||r[category]===s.key))),period()]);svg.append(mark);})});
 // Keep one visible value label per point, including coincident series values.
 rows.forEach((row,i)=>{let ceiling=bottom-10;const order=series.map((s,index)=>({s,index,value:row.values[index]})).sort((a,b)=>a.value-b.value||a.index-b.index);for(const {s,index,value} of order){const target=y(value)-12;const labelY=Math.min(target,ceiling);ceiling=labelY-18;if(target-labelY>3)svg.append(chartNode('line',{x1:x(i)+5,x2:x(i)+9,y1:y(value)-4,y2:labelY-4,stroke:s.color,'stroke-width':1,'pointer-events':'none'}));svg.append(chartNode('text',{x:x(i),y:labelY,'text-anchor':'middle',class:'chart-value','data-value-label':value,'data-series':s.key,'data-period':row.key,fill:s.color,stroke:'#FFFEF7','stroke-width':3,'paint-order':'stroke','stroke-linejoin':'round','pointer-events':'none'},fmt(value)))}});
 card.append(svg);if(!records.length){const empty=document.createElement('p');empty.className='chart-note';empty.textContent='Pagal pasirinktus filtrus įrašų nėra.';card.append(empty)}
 addChartTable(card,dimension==='year'?'Metai':'Mėnuo',series,rows);return card;
}
function municipalPie(id,title,records,category){
 const card=municipalityCard(id,title);const items=municipalCategories[category].map(([key,label],i)=>({key,label,color:municipalColors[i],value:records.filter(r=>r[category]===key).length}));const total=items.reduce((n,s)=>n+s.value,0);card.dataset.rows=JSON.stringify(items);card.dataset.denominator=total;
 const percent=n=>new Intl.NumberFormat('lt-LT',{minimumFractionDigits:1,maximumFractionDigits:1}).format(total?n/total*100:0)+' %';
 const svg=chartNode('svg',{viewBox:'0 0 600 360',role:'group','aria-label':title});let angle=-Math.PI/2;const cx=300,cy=180,radius=138,outside=[];
 const wrapLabel=text=>{const lines=[];let current='';for(const word of text.split(' ')){if(current&&(current+' '+word).length>14){lines.push(current);current=word}else current+=(current?' ':'')+word}if(current)lines.push(current);return lines};
 function writeLabel(lines,tx,ty,anchor,fill,placement,key){const label=chartNode('text',{x:tx,y:ty-(lines.length-1)*8,'text-anchor':anchor,class:'pie-label',fill,'pointer-events':'none','data-placement':placement,'data-category-label':key});lines.forEach((text,i)=>label.append(chartNode('tspan',{x:tx,dy:i?16:0},text)));svg.append(label)}
 for(const item of items){if(!item.value)continue;const fraction=item.value/total,start=angle,end=angle+fraction*Math.PI*2,middle=(start+end)/2;let mark;if(item.value===total){mark=chartNode('circle',{cx,cy,r:radius,fill:item.color})}else{const a=[cx+radius*Math.cos(start),cy+radius*Math.sin(start)],b=[cx+radius*Math.cos(end),cy+radius*Math.sin(end)];mark=chartNode('path',{d:`M${cx},${cy}L${a}A${radius},${radius} 0 ${fraction>.5?1:0} 1 ${b}Z`,fill:item.color,stroke:'#F7F5E7','stroke-width':2})}mark.dataset.value=item.value;mark.dataset.category=item.key;chartTooltip(mark,[lookup.get(active).name,item.label,fmt(item.value)+' ('+percent(item.value)+')',...singleHuntingDate(records.filter(r=>r[category]===item.key)),period()]);svg.append(mark);
 const lines=[...wrapLabel(item.label),fmt(item.value)+' · '+percent(item.value)],halfWidth=Math.max(...lines.map(t=>t.length))*3.7+7,halfHeight=lines.length*8+4;
 const fits=(tx,ty)=>{for(const dx of [-halfWidth,0,halfWidth])for(const dy of [-halfHeight,0,halfHeight]){const px=tx+dx-cx,py=ty+dy-cy;if(Math.hypot(px,py)>radius-12)return false;if(fraction<.99999){let a=Math.atan2(py,px);while(a<start)a+=Math.PI*2;if(a>end)return false}}return true};
 let position=null;for(const distance of item.value===total?[0]:[.49,.46,.54,.60,.66,.42]){const tx=cx+radius*distance*Math.cos(middle),ty=cy+radius*distance*Math.sin(middle);if(fits(tx,ty)){position=[tx,ty];break}}
 if(position)writeLabel(lines,...position,'middle',textColor(item.color),'inside',item.key);else outside.push({item,lines,middle,side:Math.cos(middle)>=0?1:-1,targetY:cy+(radius+12)*Math.sin(middle)});angle=end;}
 for(const side of [-1,1]){const group=outside.filter(e=>e.side===side).sort((a,b)=>a.targetY-b.targetY);let floor=35;for(const entry of group){entry.labelY=Math.max(floor,Math.min(325,entry.targetY));floor=entry.labelY+58}if(group.length&&group.at(-1).labelY>325){const shift=group.at(-1).labelY-325;for(const entry of group)entry.labelY-=shift}for(const {item,lines,middle,labelY} of group){const tx=side>0?cx+radius+18:cx-radius-18;const sx=cx+radius*Math.cos(middle),sy=cy+radius*Math.sin(middle),elbow=cx+(radius+9)*side;svg.append(chartNode('path',{d:`M${sx},${sy}L${elbow},${labelY}L${tx-side*5},${labelY}`,fill:'none',stroke:item.color,'stroke-width':1.2,'pointer-events':'none',class:'pie-connector'}));writeLabel(lines,tx,labelY,side>0?'start':'end','#4B574B','outside',item.key)}}
 if(!total)svg.append(chartNode('text',{x:cx,y:cy,'text-anchor':'middle',class:'chart-tick'},'Įrašų nėra'));
 card.append(svg);chartLegend(card,items.map(item=>({text:item.label+': '+fmt(item.value)+' ('+percent(item.value)+')',color:item.color})));
 const note=document.createElement('p');note.className='chart-note';note.textContent=category==='health'?'Žinoma sveikata: '+fmt(total)+'. Nežinoma: '+fmt(records.filter(r=>r.health==='unknown').length)+'.':'Iš viso: '+fmt(total)+'.';card.append(note);
 addChartTable(card,'Kategorija',[{label:'Vilkai'},{label:'Dalis'}],items.map(item=>({label:item.label,values:[item.value,percent(item.value)]})));return card;
}
function renderMunicipalityDashboard(){
 const dashboard=document.getElementById('municipality-dashboard');dashboard.hidden=!active;if(!active)return;
 const records=filtered.filter(r=>r.code===active);document.getElementById('dashboard-title').textContent=lookup.get(active).official_name;document.getElementById('dashboard-scope').textContent=period();document.getElementById('dashboard-total').textContent=fmt(records.length);
 const grid=document.getElementById('municipality-charts');grid.replaceChildren();
 grid.append(municipalLine('year-total','Sumedžiota vilkų pagal metus',records,'year'),municipalLine('month-total','Sumedžiota vilkų pagal mėnesius',records,'month'));
 for(const [key,title] of [['gender','Lytis'],['age','Amžius'],['health','Sveikata'],['packMember','Priklausymas gaujai']])grid.append(municipalPie('pie-'+key,title,records,key));
 for(const [key,title] of [['gender','Lytis pagal metus'],['health','Sveikata pagal metus'],['packMember','Priklausymas gaujai pagal metus']])grid.append(municipalLine('year-'+key,title,records,'year',key));
}

