document.addEventListener('DOMContentLoaded', () => {
    // Initialize Telegram Web App if available
    if (window.Telegram && Telegram.WebApp) {
        Telegram.WebApp.ready();
        Telegram.WebApp.expand();
    }

    const playerInput = document.getElementById('player-input');
    const suggestionsList = document.getElementById('suggestions');
    const seasonSelect = document.getElementById('season-select');
    const playoffToggle = document.getElementById('playoff-toggle');
    const searchButton = document.getElementById('search-button');
    const resultDiv = document.getElementById('result');

    // Populate season select with the last ~15 seasons
    function populateSeasons() {
        const currentYear = new Date().getFullYear();
        // KHL seasons start in August/September and end next spring
        const latestEndYear = currentYear + 1;
        const start = latestEndYear - 1;
        // Generate seasons for the last 15 years
        for (let i = 0; i < 15; i++) {
            const endYear = latestEndYear - i;
            const startYear = endYear - 1;
            const seasonStr = `${startYear}/${endYear}`;
            const option = document.createElement('option');
            option.value = seasonStr;
            option.textContent = seasonStr;
            seasonSelect.appendChild(option);
        }
        seasonSelect.value = `${start}/${latestEndYear}`;
    }

    populateSeasons();

    let searchTimeout = null;

    playerInput.addEventListener('input', () => {
        const query = playerInput.value.trim();
        clearTimeout(searchTimeout);
        if (!query) {
            suggestionsList.innerHTML = '';
            return;
        }
        // Delay search slightly to reduce requests
        searchTimeout = setTimeout(() => {
            fetchSuggestions(query);
        }, 300);
    });

    function fetchSuggestions(query) {
        const season = seasonSelect.value;
        const playoff = playoffToggle.checked;
        const url = `/api/search?q=${encodeURIComponent(query)}&season=${encodeURIComponent(season)}&playoff=${playoff}`;
        fetch(url)
            .then(resp => resp.json())
            .then(data => {
                suggestionsList.innerHTML = '';
                const players = data.players || [];
                players.forEach(p => {
                    const li = document.createElement('li');
                    li.textContent = `${p.name} (${p.team})`;
                    li.dataset.name = p.name;
                    suggestionsList.appendChild(li);
                });
            })
            .catch(err => {
                console.error('Autocomplete fetch error', err);
            });
    }

    suggestionsList.addEventListener('click', (evt) => {
        if (evt.target.tagName.toLowerCase() === 'li') {
            const name = evt.target.dataset.name;
            playerInput.value = name;
            suggestionsList.innerHTML = '';
        }
    });

    // Hide suggestions when clicking outside
    document.addEventListener('click', (evt) => {
        if (!playerInput.contains(evt.target) && !suggestionsList.contains(evt.target)) {
            suggestionsList.innerHTML = '';
        }
    });

    searchButton.addEventListener('click', () => {
        const name = playerInput.value.trim();
        const season = seasonSelect.value;
        const playoff = playoffToggle.checked;
        if (!name) {
            resultDiv.innerHTML = '<p>Введите фамилию и имя игрока.</p>';
            return;
        }
        const url = `/api/stats?player=${encodeURIComponent(name)}&season=${encodeURIComponent(season)}&playoff=${playoff}`;
        resultDiv.innerHTML = '<p>Загрузка...</p>';
        fetch(url)
            .then(resp => resp.json())
            .then(data => {
                if (data.error) {
                    resultDiv.innerHTML = `<p>${data.error}</p>`;
                } else {
                    renderStats(data.stats);
                }
            })
            .catch(err => {
                console.error('Stats fetch error', err);
                resultDiv.innerHTML = '<p>Ошибка загрузки данных.</p>';
            });
    });

    function renderStats(stats) {
        // stats: {name, team, team_abbr, position, points, goals, assists, games, plus_minus, penalty}
        const imgSrc = `/static/placeholder.png`;
        const html = `
            <div class="player-header">
                <img src="${imgSrc}" alt="Фото игрока" class="player-photo">
                <div class="player-info">
                    <h2>${stats.name}</h2>
                    <p><strong>Команда:</strong> ${stats.team} (${stats.team_abbr})</p>
                    <p><strong>Амплуа:</strong> ${stats.position}</p>
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Игры</th>
                        <th>Голы</th>
                        <th>Передачи</th>
                        <th>Очки</th>
                        <th>+/-</th>
                        <th>Штраф</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>${stats.games}</td>
                        <td>${stats.goals}</td>
                        <td>${stats.assists}</td>
                        <td>${stats.points}</td>
                        <td>${stats.plus_minus}</td>
                        <td>${stats.penalty}</td>
                    </tr>
                </tbody>
            </table>
        `;
        resultDiv.innerHTML = html;
    }
});