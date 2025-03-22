document.getElementById('searchForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    
    // Build properly encoded query string
    const params = [];
    formData.forEach((value, key) => {
        if (value.trim()) {
            console.log(key, value);
            console.log(encodeURIComponent(key), encodeURIComponent(value.trim()));
            params.push(
                `${encodeURIComponent(key)}=${encodeURIComponent(value.trim())}`
            );
        }
    });

    console.log('Params:', params);
    console.log(`/movies_search/find/?${params.join('&')}`);

    try {
        const response = await fetch(`/movies_search/find/?${params.join('&')}`);
        console.log('API Response:', response);
        const data = await response.json();
        console.log('Data:', data);
        
        if (data.Matching_Movies?.length > 0) {
            console.log('Received movies:', data.Matching_Movies);
            displayResults(data.Matching_Movies);
        } else {
            displayResults([]);
        }

    } catch (error) {
        console.error('Error:', error);
        displayResults([]);
    }
});

function displayResults(movies) {
    const resultsContainer = document.getElementById('results');
    resultsContainer.innerHTML = '';

    if (!movies || movies.length === 0) {
        resultsContainer.innerHTML = `
            <div class="no-results">
                <p>🎥 No movies found matching your search</p>
                <small>Try different keywords or filters</small>
            </div>
        `;
        return;
    }

    // Create table structure
    const table = document.createElement('table');
    table.className = 'movie-table';

    // Create table header
    const thead = document.createElement('thead');
    thead.innerHTML = `
        <tr>
            <th>Title</th>
            <th>Release Date</th>
            <th>Genres</th>
            <th>Rating</th>
            <th>Votes</th>
            <th>Language</th>
            <th>Production</th>
            <th>Runtime</th>
            <th>Budget</th>
            <th>Revenue</th>
            <th>Status</th>
            <th>Title Type</th>
            <th>Keywords</th>
            <th>Trailer Views</th>
            <th>Trailer Likes</th>
        </tr>
    `;
    table.appendChild(thead);

    // Create table body
    const tbody = document.createElement('tbody');
    movies.forEach(movie => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${movie.Title}</td>
            <td>${movie.Release_date}</td>
            <td>${movie.Genres}</td>
            <td>${movie.Rating} ⭐</td>
            <td>${movie.Votes?.toLocaleString() || 'N/A'}</td>
            <td>${movie.Original_Language?.toUpperCase() || 'N/A'}</td>
            <td>${movie.Production_Companies || 'N/A'}</td>
            <td>${movie.Runtime} min</td>
            <td>$${movie.Budget?.toLocaleString() || 'N/A'}</td>
            <td>$${movie.Revenue?.toLocaleString() || 'N/A'}</td>
            <td>${movie.Status || 'N/A'}</td>
            <td>${movie.Title_Type || 'N/A'}</td>
            <td>${movie.Keywords || 'N/A'}</td>
            <td>${movie.Trailer_Views?.toLocaleString() || 'N/A'}</td>
            <td>${movie.Trailer_Likes?.toLocaleString() || 'N/A'}</td>
        `;
        tbody.appendChild(row);
    });

    table.appendChild(tbody);
    resultsContainer.appendChild(table);
}
