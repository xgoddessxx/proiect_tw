// ==========================================
// 1. FETCH DATE REALE DIN FLASK API
// ==========================================
const API_BASE_URL = 'http://localhost:5000/api';

// Funcție helper pentru a transforma string-urile JSON din baza de date în obiecte JS
const parseJsonFields = (item) => {
    if (item.cast_json && typeof item.cast_json === 'string') {
        try { item.cast_json = JSON.parse(item.cast_json); } catch(e) { item.cast_json = []; }
    }
    if (item.team_json && typeof item.team_json === 'string') {
        try { item.team_json = JSON.parse(item.team_json); } catch(e) { item.team_json = []; }
    }
    return item;
};

const fetchShows = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/shows`);
        if (!response.ok) throw new Error('Eroare rețea');
        const shows = await response.json();
        return shows.map(parseJsonFields);
    } catch (error) {
        console.error("Eroare la preluarea spectacolelor:", error);
        return [];
    }
};

const fetchSchedule = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/schedule`);
        if (!response.ok) throw new Error('Eroare rețea');
        return await response.json();
    } catch (error) {
        console.error("Eroare la preluarea programului:", error);
        return [];
    }
};

const fetchShowById = async (id) => {
    try {
        const response = await fetch(`${API_BASE_URL}/shows/${id}`);
        if (!response.ok) throw new Error('Spectacol negăsit');
        const show = await response.json();
        return parseJsonFields(show);
    } catch (error) {
        console.error(`Eroare la spectacolul ${id}:`, error);
        return null;
    }
};

// ==========================================
// 2. VIEWS (Render Functions)
// ==========================================

const renderShowsList = (shows) => {
    if (!shows || shows.length === 0) return `<p>Niciun spectacol găsit.</p>`;
    return `
        <div class="grid">
            ${shows.map(show => {
                const posterUrl = show.poster_path && show.poster_path !== 'NotFound' 
                    ? show.poster_path 
                    : 'https://via.placeholder.com/300x400?text=Fără+Afiș';

                return `
                    <div class="card" onclick="navigateTo('/shows/${show.id}')">
                        <img src="${posterUrl}" alt="Afiș ${show.title}" onerror="this.src='https://via.placeholder.com/300x400?text=Fără+Afiș'">
                        <div class="card-content">
                            <h3 class="card-title">${show.title}</h3>
                            <div class="card-meta">
                                <p><strong>Autor:</strong> ${show.author || 'N/A'}</p>
                                <p><strong>Regizor:</strong> ${show.director || 'N/A'}</p>
                            </div>
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
};

const views = {
    "/": async () => {
        const shows = await fetchShows();
        return `
            <h2>Spectacole și reprezentații viitoare</h2>
            <br>
            ${renderShowsList(shows)}
        `;
    },
    
    "/shows": async () => {
        const shows = await fetchShows();
        return `
            <h2>Repertoriu Spectacole</h2>
            <br>
            ${renderShowsList(shows)}
        `;
    },
    
    "/shows/:id": async (params) => {
        const show = await fetchShowById(params.id);
        if (!show) return `<h2>Spectacolul nu a fost găsit.</h2>`;

        const schedule = await fetchSchedule();
        const futurePerformances = schedule.filter(p => p.show_id === show.id);
        const posterUrl = show.poster_path && show.poster_path !== 'NotFound' 
            ? show.poster_path 
            : 'https://via.placeholder.com/400x550?text=Fără+Afiș';

        return `
            <div class="show-detail">
                <img src="${posterUrl}" alt="Afiș ${show.title}" onerror="this.src='https://via.placeholder.com/400x550?text=Fără+Afiș'">
                <div class="show-info">
                    <h1>${show.title}</h1>
                    <p class="card-meta">${show.author || 'N/A'} | Regia: ${show.director || 'N/A'}</p>
                    <p><strong>Producție proprie? </strong> ${(show.productie_proprie ? 'DA' : 'NU')}</p>
                    <p><strong>Durată:</strong> ${(show.duration_minutes ? show.duration_minutes + ' min' : 'N/A')}</p>
                    <p><strong>Vârstă recomandată:</strong> ${show.age_recommendation || 'N/A'}</p>

                    <h3 class="section-title">Distribuție</h3>
                    <ul>
                        ${Array.isArray(show.cast_json) && show.cast_json.length > 0 
                            ? show.cast_json.map(c => `<li><strong>${c.name}</strong> ${c.character ? `- ${c.character}` : ''}</li>`).join('') 
                            : '<li>Fără informații</li>'}
                    </ul>

                    <h3 class="section-title">Echipă Artistică</h3>
                    <ul>
                        ${Array.isArray(show.team_json) && show.team_json.length > 0 
                            ? show.team_json.map(t => `<li><strong>${t.role || 'Rol'}:</strong> ${t.name}</li>`).join('') 
                            : '<li>Fără informații</li>'}
                    </ul>
                </div>
            </div>
            
            <h3 class="section-title">Reprezentații viitoare</h3>
            <ul class="schedule-list">
                ${futurePerformances.length ? futurePerformances.map(p => `
                    <li class="schedule-item">
                        <div>
                            <strong>${new Date(p.start_at).toLocaleString('ro-RO')}</strong>
                            <br><small>${p.venue || 'Sală principală'}</small>
                        </div>
                        <span style="color: var(--accent-color)">${p.status || ''}</span>
                    </li>
                `).join('') : '<p>Nu sunt programate reprezentații viitoare.</p>'}
            </ul>
        `;
    },

    "/schedule": async () => {
        let schedule = await fetchSchedule();
        schedule.sort((a, b) => new Date(a.start_at) - new Date(b.start_at));

        return `
            <h2>Program Reprezentații</h2>
            <br>
            <ul class="schedule-list">
                ${schedule.length ? schedule.map(p => `
                    <li class="schedule-item" style="cursor:pointer" onclick="navigateTo('/shows/${p.show_id}')">
                        <div>
                            <strong>${new Date(p.start_at).toLocaleString('ro-RO')}</strong>
                            <h4 style="color: var(--primary-color); margin: 0.2rem 0;">${p.show_title || 'Spectacol'}</h4>
                        </div>
                        <div style="text-align: right;">
                            <small>${p.venue || 'N/A'}</small><br>
                            <span style="font-size: 0.9rem; color: #666;">${p.status || ''}</span>
                        </div>
                    </li>
                `).join('') : '<p>Nu există programări momentan.</p>'}
            </ul>
        `;
    }
};

// ==========================================
// 3. ROUTER & CĂUTARE
// ==========================================

const pathToRegex = path => new RegExp("^" + path.replace(/\//g, "\\/").replace(/:\w+/g, "(.+)") + "$");
const getParams = match => {
    const values = match.result.slice(1);
    const keys = Array.from(match.route.path.matchAll(/:(\w+)/g)).map(result => result[1]);
    return Object.fromEntries(keys.map((key, i) => [key, values[i]]));
};

const router = async () => {
    const routes = Object.keys(views).map(path => ({ path, view: views[path] }));
    const potentialMatches = routes.map(route => ({ route, result: location.pathname.match(pathToRegex(route.path)) }));
    let match = potentialMatches.find(potentialMatch => potentialMatch.result !== null);

    if (!match) match = { route: routes[0], result: [location.pathname] }; 
    
    document.getElementById("app").innerHTML = `<p>Se încarcă...</p>`;
    document.getElementById("app").innerHTML = await match.route.view(getParams(match));
};

const navigateTo = url => {
    history.pushState(null, null, url);
    router();
};

window.addEventListener("popstate", router);

document.addEventListener("DOMContentLoaded", () => {
    document.body.addEventListener("click", e => {
        if (e.target.matches("[data-link]")) {
            e.preventDefault();
            navigateTo(e.target.href);
        }
    });
    router();
});

// Căutare după titlu
const searchInput = document.getElementById('searchInput');
if (searchInput) {
    searchInput.addEventListener('input', async (e) => {
        const query = e.target.value.toLowerCase();
        if (location.pathname === '/shows' || location.pathname === '/') {
            const shows = await fetchShows();
            const filtered = shows.filter(s => s.title && s.title.toLowerCase().includes(query));
            const gridContainer = document.querySelector('.grid');
            if (gridContainer && gridContainer.parentElement) {
                gridContainer.parentElement.innerHTML = `<h2>Rezultate căutare</h2><br>` + renderShowsList(filtered);
            }
        }
    });
}