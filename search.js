/*
 * This script implements a fully client‑side search and display of KHL
 * player statistics.  Instead of querying a backend API, it loads a
 * JSON file containing pre‑parsed statistics for a season and then
 * filters it in the browser as the user types.  This makes the mini
 * application easy to host on a static platform such as GitHub
 * Pages.  The dataset is loaded once per page load and reused for
 * both regular season and play‑off views (the same data is used for
 * demonstration purposes).  See players_2025_regular.json for the
 * source data.
 */

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

    // Preload player data.  The JSON file is located next to this script.
    const DATA_URL_REG = 'players_2025_regular.json';
    const DATA_URL_PO = 'players_2025_regular.json'; // reuse regular data for play‑off

    let dataRegular = [];
    let dataPlayoff = [];

    // Fetch the datasets; ignore errors silently.
    fetch(DATA_URL_REG)
        .then((resp) => resp.json())
        .then((json) => {
            dataRegular = json;
        })
        .catch((err) => {
            console.error('Failed to load regular season data:', err);
        });
    fetch(DATA_URL_PO)
        .then((resp) => resp.json())
        .then((json) => {
            dataPlayoff = json;
        })
        .catch((err) => {
            console.error('Failed to load play‑off data:', err);
        });

    // Populate season select with the last ~15 seasons.  This control
    // does not currently change the dataset but is retained for UI
    // completeness and future extension.
    function populateSeasons() {
        const currentYear = new Date().getFullYear();
        const latestEndYear = currentYear + 1;
        const start = latestEndYear - 1;
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

    // Normalize strings for comparison: lower‑case and collapse spaces
    function normalize(str) {
        return (str || '').toLowerCase().replace(/\s+/g, ' ').trim();
    }

    function searchPlayers(query, dataset) {
        const nq = normalize(query);
        return dataset.filter((p) => normalize(p.name).includes(nq));
    }

    function renderSuggestions(list) {
        suggestionsList.innerHTML = '';
        list.slice(0, 10).forEach((p) => {
            const li = document.createElement('li');
            li.textContent = `${p.name} (${p.team})`;
            li.dataset.name = p.name;
            suggestionsList.appendChild(li);
        });
    }

    function showPlayer(player) {
        suggestionsList.innerHTML = '';
        // Build HTML for the selected player's statistics.  Photo
        // placeholder is loaded from the static directory (same
        // directory as this script).  You can replace this with a
        // real image when available.
        const imgSrc = 'placeholder.png';
        const html = `
            <div class="player-header">
                <img src="${imgSrc}" alt="Фото игрока" class="player-photo">
                <div class="player-info">
                    <h2>${player.name}</h2>
                    <p><strong>Команда:</strong> ${player.team} (${player.team_abbr})</p>
                    <p><strong>Амплуа:</strong> ${player.position}</p>
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
                        <td>${player.games}</td>
                        <td>${player.goals}</td>
                        <td>${player.assists}</td>
                        <td>${player.points}</td>
                        <td>${player.plus_minus}</td>
                        <td>${player.penalty}</td>
                    </tr>
                </tbody>
            </table>
        `;
        resultDiv.innerHTML = html;
    }

    playerInput.addEventListener('input', () => {
        const query = playerInput.value.trim();
        clearTimeout(searchTimeout);
        if (!query) {
            suggestionsList.innerHTML = '';
            return;
        }
        searchTimeout = setTimeout(() => {
            const playoff = playoffToggle.checked;
            const dataset = playoff ? dataPlayoff : dataRegular;
            const hits = searchPlayers(query, dataset);
            renderSuggestions(hits);
        }, 200);
    });

    suggestionsList.addEventListener('click', (evt) => {
        if (evt.target.tagName.toLowerCase() === 'li') {
            const name = evt.target.dataset.name;
            playerInput.value = name;
            const playoff = playoffToggle.checked;
            const dataset = playoff ? dataPlayoff : dataRegular;
            const player = dataset.find((p) => p.name === name);
            if (player) {
                showPlayer(player);
            }
        }
    });

    document.addEventListener('click', (evt) => {
        if (!playerInput.contains(evt.target) && !suggestionsList.contains(evt.target)) {
            suggestionsList.innerHTML = '';
        }
    });

    searchButton.addEventListener('click', () => {
        const name = playerInput.value.trim();
        if (!name) {
            resultDiv.innerHTML = '<p>Введите фамилию и имя игрока.</p>';
            return;
        }
        const playoff = playoffToggle.checked;
        const dataset = playoff ? dataPlayoff : dataRegular;
        const player = dataset.find((p) => p.name === name);
        if (player) {
            showPlayer(player);
        } else {
            resultDiv.innerHTML = `<p>Игрок "${name}" не найден.</p>`;
        }
    });
});