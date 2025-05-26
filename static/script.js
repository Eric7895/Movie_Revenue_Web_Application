// Parameter search - extract key value pairs
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

// Upload feature
document.getElementById('uploadForm').addEventListener('submit', async (e) => {e.preventDefault(); // Prevent default form submission

    const fileInput = document.getElementById('fileInput');
    if (!fileInput.files.length) {
        console.log("No file selected");
        return;
    }

    console.log("File selected:", fileInput.files[0].name);

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        console.log("Sending upload request...");
        const response = await fetch('/movies/upload/', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        console.log("Response received:", result);

        if (result.added === 0 && result.skipped === 0) {
            document.getElementById('uploadMessage').innerText = "No movies added";
        }
        else {
            document.getElementById('uploadMessage').innerText = 
            `Upload successful: ${result.added} added, ${result.skipped} skipped`;}
        
    } catch (error) {
        console.error("Upload failed:", error);
        document.getElementById('uploadMessage').innerText = "Upload failed";
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

const predictForm = document.getElementById('predictForm');
if (predictForm) {
  predictForm.addEventListener('submit', async (e) => {e.preventDefault();
    const model = document.getElementById('modelSelect').value;
    const msgBox = document.getElementById('pred_message');
    msgBox.textContent = '';

    if (!model) { msgBox.textContent = 'Select a model first'; return; }

    try {
      const res = await fetch(`/predict/${model}`, { method: 'POST' });
      const data = await res.json();
      msgBox.textContent = res.ok ? data.message : `Error: ${data.detail}`;
    } catch (err) {
      console.error(err);
      msgBox.textContent = 'Prediction failed (see console)';
    }
  });
}
