// IMDb Movie Rating Dashboard JavaScript

let allMovies = [];
let filteredMovies = [];
let decadeChartInstance = null;
let currentView = 'grid'; // 'grid' or 'table'

document.addEventListener("DOMContentLoaded", () => {
    initApp();
    setupEventListeners();
});

async function initApp() {
    await fetchMovies();
    await fetchStats();
}

// Fetch Movies from Flask REST API
async function fetchMovies() {
    try {
        const response = await fetch("/api/movies");
        const data = await response.json();
        if (data.status === "success") {
            allMovies = data.movies;
            applyFilters();
        }
    } catch (err) {
        showToast("Error loading movies from server.", "error");
    }
}

// Fetch Statistics & Render Chart
async function fetchStats() {
    try {
        const response = await fetch("/api/stats");
        const data = await response.json();
        if (data.status === "success") {
            const stats = data.stats;
            document.getElementById("statTotalMovies").textContent = stats.total_movies;
            document.getElementById("statTopMovie").textContent = stats.top_movie;
            document.getElementById("statAvgRating").textContent = stats.avg_rating.toFixed(1);

            const decadeKeys = Object.keys(stats.decades || {});
            if (decadeKeys.length > 0) {
                const topDecade = decadeKeys.reduce((a, b) => stats.decades[a] > stats.decades[b] ? a : b);
                document.getElementById("statTopDecade").textContent = topDecade;
            }

            renderDecadeChart(stats.decades);
        }
    } catch (err) {
        console.error("Error fetching stats:", err);
    }
}

// Render Chart.js Decade Distribution
function renderDecadeChart(decadesData) {
    const ctx = document.getElementById("decadeChart").getContext("2d");
    const labels = Object.keys(decadesData || {});
    const counts = Object.values(decadesData || {});

    if (decadeChartInstance) {
        decadeChartInstance.destroy();
    }

    decadeChartInstance = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Number of Movies",
                data: counts,
                backgroundColor: "rgba(245, 197, 24, 0.7)",
                borderColor: "#f5c518",
                borderWidth: 1.5,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "#18181f",
                    titleColor: "#f5c518",
                    bodyColor: "#ffffff",
                    borderColor: "rgba(255,255,255,0.1)",
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    grid: { color: "rgba(255,255,255,0.05)" },
                    ticks: { color: "#a0a0ab", font: { family: "Outfit" } }
                },
                y: {
                    grid: { color: "rgba(255,255,255,0.05)" },
                    ticks: { color: "#a0a0ab", font: { family: "Outfit" }, precision: 0 }
                }
            }
        }
    });
}

// Event Listeners Setup
function setupEventListeners() {
    // Search input
    document.getElementById("searchInput").addEventListener("input", applyFilters);

    // Filters & Sort
    document.getElementById("ratingFilter").addEventListener("change", applyFilters);
    document.getElementById("sortBy").addEventListener("change", applyFilters);

    // View Toggles
    document.getElementById("gridViewBtn").addEventListener("click", () => switchView('grid'));
    document.getElementById("tableViewBtn").addEventListener("click", () => switchView('table'));

    // Trigger Scraper Button
    document.getElementById("scrapeBtn").addEventListener("click", handleRunScraper);

    // CSV Modal Handlers
    const uploadModal = document.getElementById("uploadModal");
    document.getElementById("uploadModalBtn").addEventListener("click", () => uploadModal.classList.remove("hidden"));
    document.getElementById("closeModalBtn").addEventListener("click", () => uploadModal.classList.add("hidden"));

    // File Drag & Drop
    const dropZone = document.getElementById("dropZone");
    const fileInput = document.getElementById("csvFileInput");
    const fileNameDisplay = document.getElementById("fileNameDisplay");

    dropZone.addEventListener("click", () => fileInput.click());
    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("dragover");
    });
    dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        if (e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            fileNameDisplay.textContent = e.dataTransfer.files[0].name;
        }
    });
    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
            fileNameDisplay.textContent = fileInput.files[0].name;
        }
    });

    // Form Submit
    document.getElementById("uploadForm").addEventListener("submit", handleCSVUpload);
}

// Switch between Grid and Table View
function switchView(view) {
    currentView = view;
    const gridBtn = document.getElementById("gridViewBtn");
    const tableBtn = document.getElementById("tableViewBtn");
    const gridView = document.getElementById("moviesGrid");
    const tableWrapper = document.getElementById("moviesTableWrapper");

    if (view === 'grid') {
        gridBtn.classList.add("active");
        tableBtn.classList.remove("active");
        gridView.classList.remove("hidden");
        tableWrapper.classList.add("hidden");
    } else {
        tableBtn.classList.add("active");
        gridBtn.classList.remove("active");
        tableWrapper.classList.remove("hidden");
        gridView.classList.add("hidden");
    }
}

// Filter and Sort Movies
function applyFilters() {
    const searchTerm = document.getElementById("searchInput").value.toLowerCase().trim();
    const minRating = parseFloat(document.getElementById("ratingFilter").value) || 0;
    const sortBy = document.getElementById("sortBy").value;

    filteredMovies = allMovies.filter(movie => {
        const titleMatch = movie.Title.toLowerCase().includes(searchTerm);
        const yearMatch = String(movie["Release Year"]).includes(searchTerm);
        const ratingMatch = parseFloat(movie["IMDb Rating"]) >= minRating;
        return (titleMatch || yearMatch) && ratingMatch;
    });

    // Sorting
    filteredMovies.sort((a, b) => {
        if (sortBy === "rank-asc") {
            return (parseInt(a.Rank) || 999) - (parseInt(b.Rank) || 999);
        } else if (sortBy === "rating-desc") {
            return (parseFloat(b["IMDb Rating"]) || 0) - (parseFloat(a["IMDb Rating"]) || 0);
        } else if (sortBy === "year-desc") {
            return (parseInt(b["Release Year"]) || 0) - (parseInt(a["Release Year"]) || 0);
        } else if (sortBy === "title-asc") {
            return a.Title.localeCompare(b.Title);
        }
        return 0;
    });

    renderMovies();
}

// Render Movies UI
function renderMovies() {
    const gridView = document.getElementById("moviesGrid");
    const tableBody = document.getElementById("moviesTableBody");
    const noResults = document.getElementById("noResults");

    if (filteredMovies.length === 0) {
        gridView.innerHTML = "";
        tableBody.innerHTML = "";
        noResults.classList.remove("hidden");
        return;
    }

    noResults.classList.add("hidden");

    // Render Grid Cards
    gridView.innerHTML = filteredMovies.map(m => `
        <div class="movie-card">
            <div class="poster-wrapper">
                <span class="rank-badge">#${m.Rank}</span>
                <span class="rating-badge"><i class="fa-solid fa-star"></i> ${m["IMDb Rating"]}</span>
                <img class="poster-img" src="${m["Poster Image"] || 'https://via.placeholder.com/380x562?text=No+Poster'}" alt="${m.Title}" loading="lazy" onerror="this.src='https://via.placeholder.com/380x562?text=IMDb+Movie'">
            </div>
            <div class="movie-details">
                <h3 class="movie-title" title="${m.Title}">${m.Title}</h3>
                <div class="movie-meta">
                    <span><i class="fa-regular fa-calendar"></i> ${m["Release Year"]}</span>
                    <span><i class="fa-regular fa-thumbs-up"></i> ${m.Votes || 'N/A'}</span>
                </div>
                <a href="${m["IMDb Link"]}" target="_blank" rel="noopener noreferrer" class="imdb-link-btn">
                    <i class="fa-solid fa-up-right-from-square"></i> View on IMDb
                </a>
            </div>
        </div>
    `).join("");

    // Render Table Rows
    tableBody.innerHTML = filteredMovies.map(m => `
        <tr>
            <td class="table-rank">#${m.Rank}</td>
            <td><img class="table-poster" src="${m["Poster Image"] || 'https://via.placeholder.com/44x60?text=Movie'}" alt="${m.Title}" loading="lazy"></td>
            <td class="table-title">${m.Title}</td>
            <td>${m["Release Year"]}</td>
            <td class="table-rating"><i class="fa-solid fa-star"></i> ${m["IMDb Rating"]}</td>
            <td>${m.Votes || 'N/A'}</td>
            <td>
                <a href="${m["IMDb Link"]}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary btn-sm" style="font-size:0.8rem; padding:0.35rem 0.65rem;">
                    <i class="fa-solid fa-arrow-up-right-from-square"></i> IMDb
                </a>
            </td>
        </tr>
    `).join("");
}

// Trigger Live Scraping
async function handleRunScraper() {
    const loadingOverlay = document.getElementById("loadingOverlay");
    loadingOverlay.classList.remove("hidden");

    try {
        const response = await fetch("/api/scrape", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ use_selenium: false })
        });
        const data = await response.json();
        if (data.status === "success") {
            allMovies = data.movies;
            applyFilters();
            await fetchStats();
            showToast(`Scrape complete! Loaded ${data.count} movies.`, "success");
        } else {
            showToast("Scrape encountered an issue.", "error");
        }
    } catch (err) {
        showToast("Failed to run scraper.", "error");
    } finally {
        loadingOverlay.classList.add("hidden");
    }
}

// Handle Custom CSV File Upload
async function handleCSVUpload(e) {
    e.preventDefault();
    const fileInput = document.getElementById("csvFileInput");
    if (!fileInput.files || fileInput.files.length === 0) {
        showToast("Please select a CSV file first.", "error");
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    try {
        const response = await fetch("/api/upload-csv", {
            method: "POST",
            body: formData
        });
        const data = await response.json();
        if (data.status === "success") {
            allMovies = data.movies;
            applyFilters();
            await fetchStats();
            document.getElementById("uploadModal").classList.add("hidden");
            showToast(data.message, "success");
        } else {
            showToast(data.message || "CSV Upload failed.", "error");
        }
    } catch (err) {
        showToast("Error uploading CSV file.", "error");
    }
}

// Toast Notifications
function showToast(message, type = "success") {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <i class="fa-solid ${type === 'success' ? 'fa-circle-check' : 'fa-triangle-exclamation'}"></i>
        <span>${message}</span>
    `;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}
