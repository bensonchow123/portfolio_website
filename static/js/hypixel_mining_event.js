document.addEventListener("DOMContentLoaded", () => {
    const API_URL = "https://api.soopy.dev/skyblock/chevents/get";
    const resultsContainer = document.getElementById("event-results");

    // Fetch and render events on page load
    fetchAndRenderEvents();

    // Set up auto-fetch every 30 seconds
    setInterval(fetchAndRenderEvents, 30000);

    async function fetchAndRenderEvents() {
        resultsContainer.innerHTML = "<p>Loading...</p>";

        try {
            const response = await fetch(API_URL);
            if (!response.ok) {
                throw new Error(`API call failed with status: ${response.status}`);
            }

            const data = await response.json();
            renderEvents(data);
        } catch (error) {
            console.error("Error fetching events:", error);
            resultsContainer.innerHTML = `<p class="red-text">Failed to fetch events. Please try again later.</p>`;
        }
    }

    function renderEvents(data) {
        const { running_events, total_lobbys, curr_time } = data.data;
        const requestTime = Math.floor(curr_time / 1000);

        const eventMarkup = Object.entries(running_events).map(([location, events]) => {
            if (!events || events.length === 0) {
                return `<h5>No events in ${location}</h5>`;
            }

            const eventsMarkup = events.map(event => {
                const eventName = event.event;
                const endsAt = Math.floor(event.ends_at / 1000);
                const isDouble = event.is_double ? "Yes" : "No";

                return `
                    <div class="card">
                        <div class="card-content">
                            <span class="card-title">${eventName}</span>
                            <p>Last lobby ends: <time>${new Date(endsAt * 1000).toLocaleString()}</time></p>
                            <p>Lobbies: ${event.lobby_count}</p>
                            <p>Double event: ${isDouble}</p>
                        </div>
                    </div>
                `;
            }).join("");

            return `
                <div class="section">
                    <h4>Events in ${location}</h4>
                    ${eventsMarkup}
                </div>
            `;
        }).join("");

        const totalLobbiesMarkup = `
            <h4>Total Lobbies</h4>
            <ul class="collection">
                ${Object.entries(total_lobbys).map(([loc, count]) => `
                    <li class="collection-item">${loc}: ${count}</li>
                `).join("")}
            </ul>
        `;

        resultsContainer.innerHTML = `
            <p>Last updated: <time>${new Date(requestTime * 1000).toLocaleString()}</time></p>
            ${eventMarkup}
            ${totalLobbiesMarkup}
        `;
    }
});