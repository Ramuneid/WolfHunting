// The detailed map uses WGS 84 source coordinates, never SVG coordinates.
const terrainContainer=document.getElementById('detailed-map');
const terrainStatus=document.getElementById('map-status');
let terrainMap=null,terrainMarkers=null,leafletLoading=null,leafletStylesReady=false;
let terrainSelection=null,terrainSelectedCode=null;
const lithuaniaBounds=[[53.85,20.85],[56.5,26.85]];
function updateTerrainSelection(){
 const label=document.getElementById('map-selection');
 label.hidden=!pointsVisible||!active;
 label.textContent=active?'Pasirinkta savivaldybė: '+lookup.get(active).name:'';
 if(!terrainMap||!pointsVisible||terrainSelectedCode===active)return;
 if(terrainSelection){terrainSelection.remove();terrainSelection=null}
 terrainSelectedCode=null;
 if(!active)return;
 const feature=DATA.municipalityBoundaries.features.find(f=>f.properties.code===active);
 if(!feature)return;
 terrainSelection=L.geoJSON(feature,{interactive:false,style:{color:DATA.categoryColors[0],weight:3,opacity:1,fillColor:DATA.categoryColors[0],fillOpacity:.12}}).addTo(terrainMap);
 terrainSelectedCode=active;
}
function loadLeaflet(){
 if(window.L&&leafletStylesReady)return Promise.resolve();
 if(leafletLoading)return leafletLoading;
 leafletLoading=new Promise((resolve,reject)=>{
  const css=document.createElement('link');css.rel='stylesheet';css.href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';css.integrity='sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=';css.crossOrigin='anonymous';
  const script=document.createElement('script');script.src='https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';script.integrity='sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=';script.crossOrigin='anonymous';
  let styled=false,loaded=false,settled=false;
  const timer=setTimeout(()=>fail(),15000);
  function fail(){if(settled)return;settled=true;clearTimeout(timer);css.remove();script.remove();reject(new Error('Map library unavailable'))}
  function ready(){if(!styled||!loaded||settled)return;settled=true;leafletStylesReady=true;clearTimeout(timer);resolve()}
  css.onload=()=>{styled=true;ready()};script.onload=()=>{loaded=true;ready()};css.onerror=script.onerror=fail;
  document.head.append(css,script);
 }).catch(error=>{leafletLoading=null;throw error});
 return leafletLoading;
}
function updateTerrainMarkers(){
 if(!terrainMarkers||!pointsVisible)return;
 terrainMarkers.clearLayers();
 const groups=new Map();for(const p of filtered){const key=p.lon+','+p.lat;if(!groups.has(key))groups.set(key,[]);groups.get(key).push(p)}
 for(const entries of groups.values()){
  const p=entries[0],places=[...new Set(entries.map(e=>e.municipality))].join(', ');
  const marker=L.circleMarker([p.lat,p.lon],{radius:5,color:'#FFF8EC',weight:1,fillColor:'#D71920',fillOpacity:.85});
  const content=document.createElement('div');
  const dates=new Map();for(const entry of entries)dates.set(entry.date,(dates.get(entry.date)||0)+1);
  const lines=[places,'Sumedžiota vilkų šioje vietoje: '+fmt(entries.length),period(),'Koordinatės: '+p.lat+', '+p.lon,'Medžioklės data: '+[...dates].sort((a,b)=>a[0].localeCompare(b[0])).map(([date,n])=>date+(n>1?' ('+n+')':'')).join('; ')];
  lines.forEach((text,i)=>{const line=document.createElement(i===0?'strong':'div');line.textContent=text;content.append(line)});
  marker.bindPopup(content).addTo(terrainMarkers);
  const element=marker.getElement();if(element){element.setAttribute('tabindex','0');element.setAttribute('role','button');element.setAttribute('aria-label',places+': '+fmt(entries.length)+' vilkų. '+p.lat+', '+p.lon);element.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();marker.openPopup()}if(e.key==='Escape')marker.closePopup()})}
 }
}
async function syncMapMode(){
 const on=pointsVisible;
 document.getElementById('overview-map').toggleAttribute('hidden',on);
 document.getElementById('overview-legend').hidden=on;
 document.getElementById('point-key').hidden=!on;
 document.getElementById('reset-map-view').hidden=!on;
 terrainContainer.hidden=!on;terrainStatus.hidden=!on;
 updateTerrainSelection();
 if(!on){terrainMap?.closePopup();return}
 // file:// and opaque sandboxes cannot supply the HTTP Referer required by OSM.
 const webContext=/^https?:$/.test(location.protocol)||(location.protocol==='about:'&&/^https?:/.test(document.referrer));
 if(!webContext){terrainStatus.textContent='Detaliam žemėlapiui reikia interneto ir HTTP peržiūros. Atidarykite užrašinę per Jupyter arba paleiskite start_map.ps1 projekto aplanke.';return}
 terrainStatus.textContent='Įkeliamas detalus žemėlapis…';
 try{
  await loadLeaflet();if(!pointsVisible)return;
  if(!terrainMap){
   terrainMap=L.map(terrainContainer,{scrollWheelZoom:true,keyboard:true});
   const tiles=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,referrerPolicy:'strict-origin-when-cross-origin',attribution:'© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors'}).addTo(terrainMap);
   tiles.on('tileerror',()=>{terrainStatus.hidden=false;terrainStatus.textContent='Nepavyko įkelti dalies žemėlapio. Patikrinkite interneto ryšį. Taškų koordinatės nepakeistos.'});
   tiles.on('loading',()=>{terrainStatus.hidden=false;terrainStatus.textContent='Įkeliamas detalus žemėlapis…'});
   let tileErrors=false;tiles.on('loading',()=>{tileErrors=false});tiles.on('tileerror',()=>{tileErrors=true});tiles.on('load',()=>{if(!tileErrors)terrainStatus.hidden=true});
   terrainMarkers=L.layerGroup().addTo(terrainMap);
   terrainMap.fitBounds(lithuaniaBounds,{padding:[12,12]});
  }
  terrainMap.invalidateSize();updateTerrainMarkers();updateTerrainSelection();
  terrainStatus.textContent='Žemėlapis: OpenStreetMap. Reikalingas interneto ryšys.';
 }catch(error){if(pointsVisible){terrainStatus.hidden=false;terrainStatus.textContent='Nepavyko įkelti detalaus žemėlapio. Patikrinkite interneto ryšį. Išjunkite ir vėl įjunkite vietų rodymą, kad bandytumėte dar kartą.'}}
}
document.getElementById('reset-map-view').addEventListener('click',()=>terrainMap?.fitBounds(lithuaniaBounds,{padding:[12,12]}));
