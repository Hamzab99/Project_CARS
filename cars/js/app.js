const API_URL = window.location.origin;
let vehicles=[], selectedVehicle=null, map=null, routeLayer=null, markersLayer=null;
let allCities=[];

// Initialisation carte
function initMap(){
    map=L.map('map').setView([46.8,2.5],6);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap contributors'}).addTo(map);
    routeLayer=L.layerGroup().addTo(map);
    markersLayer=L.layerGroup().addTo(map);
}

// Charger villes
async function loadCities(){
    try{
        const response=await fetch(`${API_URL}/api/cities`);
        const data=await response.json();
        allCities=data.cities;

        const dep=document.getElementById('departure');
        const dest=document.getElementById('destination');

        // Grandes villes (>100k) par défaut
        allCities.filter(c=>c.population>=100000).forEach(city=>{
            dep.appendChild(new Option(city.name, city.name.toLowerCase()));
            dest.appendChild(new Option(city.name, city.name.toLowerCase()));
        });
    }catch(e){showError('Erreur lors du chargement des villes');}
}

// Recherche ville
function enableCitySearch(){
    const depBtn=document.getElementById('search-departure-btn');
    const destBtn=document.getElementById('search-destination-btn');
    const depInput=document.getElementById('search-departure');
    const destInput=document.getElementById('search-destination');

    depBtn.onclick=()=>{ depInput.style.display='block'; depInput.focus(); };
    destBtn.onclick=()=>{ destInput.style.display='block'; destInput.focus(); };

    depInput.addEventListener('input',()=>filterCity(depInput,'departure'));
    destInput.addEventListener('input',()=>filterCity(destInput,'destination'));
}

function filterCity(input,selectId){
    const val=input.value.toLowerCase();
    const select=document.getElementById(selectId);
    select.innerHTML='<option value="">-- Choisir une ville --</option>';
    allCities.filter(c=>c.name.toLowerCase().includes(val)).forEach(city=>{
        select.appendChild(new Option(city.name, city.name.toLowerCase()));
    });
}

// Charger véhicules
async function loadVehicles(){
    try{
        const resp=await fetch(`${API_URL}/api/vehicles`);
        const data=await resp.json();
        vehicles=data.vehicles;
        displayVehicles(vehicles);
    }catch(e){
        showError('Erreur lors du chargement des véhicules');
        document.getElementById('vehicles-list').innerHTML='<p style="color:red;">Impossible de charger les véhicules</p>';
    }
}

function displayVehicles(list){
    const container=document.getElementById('vehicles-list');
    container.innerHTML='';
    if(list.length===0){container.innerHTML='<p>Aucun véhicule disponible</p>'; return;}
    list.forEach(v=>{
        const card=document.createElement('div');
        card.className='vehicle-card';
        card.onclick=()=>selectVehicle(v, card);
        card.innerHTML=`
            <div class="vehicle-name">${v.name}</div>
            <div class="vehicle-specs">
                <div class="spec">⚡ ${v.autonomy} km</div>
                <div class="spec">🔋 ${v.battery} kWh</div>
                <div class="spec">⏱️ ${v.chargeTime}h charge</div>
                <div class="spec">👥 ${v.seats||5} places</div>
            </div>`;
        container.appendChild(card);
    });
}

function selectVehicle(vehicle,card){
    selectedVehicle=vehicle;
    document.querySelectorAll('.vehicle-card').forEach(c=>c.classList.remove('selected'));
    card.classList.add('selected');
    checkFormValid();
}

function checkFormValid(){
    const dep=document.getElementById('departure').value;
    const dest=document.getElementById('destination').value;
    document.getElementById('plan-btn').disabled=!(dep && dest && selectedVehicle);
}

async function planTrip(){
    const dep=document.getElementById('departure').value;
    const dest=document.getElementById('destination').value;
    if(dep===dest){showError('Les villes de départ et d\'arrivée doivent être différentes'); return;}

    const btn=document.getElementById('plan-btn');
    btn.disabled=true; btn.textContent='⏳ Calcul en cours...';
    document.getElementById('error').classList.remove('active');
    document.getElementById('results').classList.remove('active');

    try{
        const resp=await fetch(`${API_URL}/api/plan-trip`,{
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({vehicle_id:selectedVehicle.id,departure:dep,destination:dest})
        });
        const data=await resp.json();
        if(data.success){
            displayResults(data.trip);
            displayRouteOnMap(data.trip);
        }else showError(data.error||'Erreur lors de la planification');
    }catch(e){showError('Erreur de connexion au serveur');}
    finally{btn.disabled=false; btn.textContent='🗺️ Planifier le voyage';}
}

function displayResults(trip){
    const container=document.getElementById('results');
    let stationsHTML='';
    if(trip.chargingStations && trip.chargingStations.length>0){
        stationsHTML=`<div class="stations-list"><h4>⚡ Stations de recharge</h4>`+
            trip.chargingStations.map((s,i)=>`<div class="station-item">
            <div class="station-name">📍 ${s.name}</div>
            <div class="station-details">
            ${s.address||''}<br>${s.city||''}<br>
            ⚡ Puissance: ${s.power} | 🔌 ${s.connector_type||'Type 2'} | 📏 À ${s.distance_from_start} km
            </div></div>`).join('')+'</div>';
    }else{
        stationsHTML=`<div class="info-box" style="background:#e8f5e9;color:#2e7d32;">✅ Votre véhicule peut effectuer ce trajet sans recharge.</div>`;
    }
    container.innerHTML=`<div class="trip-summary">
        <h3>📊 Résumé du trajet</h3>
        <div class="trip-stats">
        <div class="stat"><div class="stat-value">${trip.distance}</div><div class="stat-label">km</div></div>
        <div class="stat"><div class="stat-value">${trip.numberOfStops}</div><div class="stat-label">arrêt(s)</div></div>
        <div class="stat"><div class="stat-value">${trip.time.driving}</div><div class="stat-label">h conduite</div></div>
        <div class="stat"><div class="stat-value">${trip.time.total}</div><div class="stat-label">h total</div></div>
        </div></div>`+stationsHTML;
    container.classList.add('active');
}

function displayRouteOnMap(trip){
    routeLayer.clearLayers(); markersLayer.clearLayers();
    const depCoords=trip.departure.coordinates;
    const destCoords=trip.destination.coordinates;

    const startIcon=L.divIcon({className:'custom-marker',html:'<div style="background:#4caf50;color:white;padding:8px 12px;border-radius:20px;font-weight:bold;box-shadow:0 2px 8px rgba(0,0,0,0.3);">🏁 Départ</div>',iconSize:[100,40]});
    L.marker([depCoords.lat,depCoords.lon],{icon:startIcon}).addTo(markersLayer).bindPopup(`<b>${trip.departure.city}</b><br>Point de départ`);

    const endIcon=L.divIcon({className:'custom-marker',html:'<div style="background:#f44336;color:white;padding:8px 12px;border-radius:20px;font-weight:bold;box-shadow:0 2px 8px rgba(0,0,0,0.3);">🎯 Arrivée</div>`,iconSize:[100,40]});
    L.marker([destCoords.lat,destCoords.lon],{icon:endIcon}).addTo(markersLayer).bindPopup(`<b>${trip.destination.city}</b><br>Destination`);

    L.polyline([[depCoords.lat,depCoords.lon],[destCoords.lat,destCoords.lon]],{color:'#667eea',weight:4,opacity:0.7}).addTo(routeLayer);

    if(trip.chargingStations) trip.chargingStations.forEach((s,i)=>{
        const stationIcon=L.divIcon({className:'custom-marker',html:`<div class="station-marker">⚡ Station ${i+1}</div>`,iconSize:[120,40]});
        L.marker([s.lat,s.lon],{icon:stationIcon}).addTo(markersLayer).bindPopup(`<b>${s.name}</b><br>${s.address}<br><strong>Puissance:</strong> ${s.power}<br><strong>Distance du départ:</strong> ${s.distance_from_start} km`);
    });

    const bounds=L.latLngBounds([[depCoords.lat,depCoords.lon],[destCoords.lat,destCoords.lon]]);
    map.fitBounds(bounds,{padding:[50,50]});
}

function showError(msg){
    const errorDiv=document.getElementById('error');
    errorDiv.textContent=msg;
    errorDiv.classList.add('active');
    setTimeout(()=>errorDiv.classList.remove('active'),5000);
}

// Init
document.addEventListener('DOMContentLoaded',()=>{
    initMap();
    loadCities();
    loadVehicles();
    enableCitySearch();
    document.getElementById('departure').addEventListener('change',checkFormValid);
    document.getElementById('destination').addEventListener('change',checkFormValid);
    document.getElementById('plan-btn').addEventListener('click',planTrip);
});
