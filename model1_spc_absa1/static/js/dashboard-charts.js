document.addEventListener('DOMContentLoaded', function() {
    let sentimentChartInstance = null;
    let aspectChartInstance = null;
    let timeSeriesChartInstance = null;

    const timeGroupingSelect = document.getElementById('timeGroupingSelect');
    if (timeGroupingSelect) {
        timeGroupingSelect.addEventListener('change', fetchDashboardData);
    }

    function fetchDashboardData() {
        // Ambil parameter tanggal dari URL saat ini
        const urlParams = new URLSearchParams(window.location.search);
        const startDate = urlParams.get('start_date') || '';
        const endDate = urlParams.get('end_date') || '';
        const timeGrouping = timeGroupingSelect ? timeGroupingSelect.value : 'harian';
        
        // Ambil batch_id langsung dari select box agar load pertama kali (default backend) tetap terbaca JS
        const batchSelect = document.getElementById('batch_id');
        const batchId = batchSelect ? batchSelect.value : (urlParams.get('batch_id') || '');

        let apiUrl = `/api/dashboard-data?time_grouping=${timeGrouping}`;
        if (startDate) apiUrl += `&start_date=${startDate}`;
        if (endDate) apiUrl += `&end_date=${endDate}`;
        if (batchId !== null && batchId !== undefined) {
            apiUrl += `&batch_id=${encodeURIComponent(batchId)}`;
        }

        // Ambil data dari backend API
        fetch(apiUrl)
            .then(response => response.json())
            .then(data => {
                // Sesuaikan mapping data dengan struktur JSON dari backend API
                const chartsData = data.charts || data;
                
                initSentimentChart(chartsData.sentiment_distribution);
                initAspectChart(chartsData.aspect_sentiment);
                initTimeSeriesChart(chartsData.time_series);
                
                // Fallback pencarian kata kunci di 2 struktur JSON berbeda
                const keywords = (data.insights && data.insights.top_keywords) || (chartsData && chartsData.top_keywords);
                if (keywords) {
                    initKeywordInsights(keywords);
                } else {
                    initKeywordInsights({}); // Tampilkan placeholder jika benar-benar kosong
                }
            })
            .catch(error => console.error('Error fetching dashboard data:', error));
    }

    fetchDashboardData(); // Panggil saat halaman dimuat

    /**
     * Inisialisasi Donut chart untuk distribusi sentimen global.
     * @param {object} sentimentData - Objek data dengan jumlah Positif, Negatif, Netral.
     */
    function initSentimentChart(sentimentData) {
        const sentimentCtx = document.getElementById('sentimentChart').getContext('2d');
        if (sentimentChartInstance) sentimentChartInstance.destroy();
        sentimentChartInstance = new Chart(sentimentCtx, {
            type: 'doughnut',
            data: {
                labels: ['Positif', 'Negatif', 'Netral'],
                datasets: [{
                    data: [
                        sentimentData.Positif || 0,
                        sentimentData.Negatif || 0,
                        sentimentData.Netral || 0
                    ],
                    backgroundColor: ['#10b981', '#ef4444', '#9ca3af'],
                    borderWidth: 0,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    /**
     * Inisialisasi Bar chart untuk analisis sentimen berbasis aspek.
     * @param {object} aspectData - Objek data yang memetakan aspek ke jumlah sentimen.
     */
    function initAspectChart(aspectData) {
        const aspectCtx = document.getElementById('aspectChart').getContext('2d');
        const labels = Object.keys(aspectData);
        const positiveData = labels.map(label => aspectData[label].Positif || 0);
        const negativeData = labels.map(label => aspectData[label].Negatif || 0);
        const neutralData = labels.map(label => aspectData[label].Netral || 0);

        // Hitung persentase untuk stacked bar chart
        const positivePercentages = [];
        const negativePercentages = [];
        const neutralPercentages = [];
        for (let i = 0; i < labels.length; i++) {
            const total = positiveData[i] + negativeData[i] + neutralData[i];
            if (total > 0) {
                positivePercentages.push((positiveData[i] / total) * 100);
                negativePercentages.push((negativeData[i] / total) * 100);
                neutralPercentages.push((neutralData[i] / total) * 100);
            } else {
                positivePercentages.push(0);
                negativePercentages.push(0);
                neutralPercentages.push(0);
            }
        }

        if (aspectChartInstance) aspectChartInstance.destroy();
        aspectChartInstance = new Chart(aspectCtx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Positif',
                    data: positivePercentages,
                    backgroundColor: '#10b981',
                    borderRadius: 6,
                    barPercentage: 0.4,
                    categoryPercentage: 0.8
                }, {
                    label: 'Negatif',
                    data: negativePercentages,
                    backgroundColor: '#ef4444',
                    borderRadius: 6,
                    barPercentage: 0.4,
                    categoryPercentage: 0.8
                }, {
                    label: 'Netral',
                    data: neutralPercentages,
                    backgroundColor: '#9ca3af',
                    borderRadius: 6,
                    barPercentage: 0.4,
                    categoryPercentage: 0.8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { stacked: true, grid: { display: false } },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        max: 100,
                        ticks: { callback: value => value + '%' }
                    }
                },
                plugins: { legend: { display: false } }
            }
        });
    }

    /**
     * Inisialisasi Line chart untuk tren sentimen dari waktu ke waktu.
     * @param {object} timeSeriesData - Objek data yang memetakan bulan ke jumlah sentimen.
     */
    function initTimeSeriesChart(timeSeriesData) {
        const timeCtx = document.getElementById('timeSeriesChart').getContext('2d');
        
        // Fungsi bantu untuk mengubah format mentah dari database jadi lebih mudah dibaca
        function formatChartLabel(label) {
            const monthNames = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agt", "Sep", "Okt", "Nov", "Des"];
            
            // 1. Format Mingguan: YYYY-Wxx (contoh: 2023-W42 -> 15 - 21 Okt 2023)
            const weekMatch = label.match(/^(\d{4})-W(\d{2})$/);
            if (weekMatch) {
                const year = parseInt(weekMatch[1]);
                const week = parseInt(weekMatch[2]);
                
                const d = new Date(year, 0, 1);
                const firstSundayOffset = d.getDay() === 0 ? 0 : 7 - d.getDay();
                const startOfWeek = new Date(year, 0, 1);
                if (week > 0) {
                    startOfWeek.setDate(1 + firstSundayOffset + (week - 1) * 7);
                }
                
                const endOfWeek = new Date(startOfWeek);
                endOfWeek.setDate(endOfWeek.getDate() + 6);
                
                if (startOfWeek.getMonth() === endOfWeek.getMonth()) {
                    return `${startOfWeek.getDate()} - ${endOfWeek.getDate()} ${monthNames[startOfWeek.getMonth()]} ${year}`;
                } else {
                    return `${startOfWeek.getDate()} ${monthNames[startOfWeek.getMonth()]} - ${endOfWeek.getDate()} ${monthNames[endOfWeek.getMonth()]} ${year}`;
                }
            }
            
            // 2. Format Bulanan: YYYY-MM (contoh: 2023-10 -> Okt 2023)
            const monthMatch = label.match(/^(\d{4})-(\d{2})$/);
            if (monthMatch) return `${monthNames[parseInt(monthMatch[2]) - 1]} ${monthMatch[1]}`;
            
            // 3. Format Harian: YYYY-MM-DD (contoh: 2023-10-16 -> 16 Okt 2023)
            const dayMatch = label.match(/^(\d{4})-(\d{2})-(\d{2})$/);
            if (dayMatch) return `${parseInt(dayMatch[3], 10)} ${monthNames[parseInt(dayMatch[2], 10) - 1]} ${dayMatch[1]}`;
            
            return label; // Tahunan (YYYY) dikembalikan apa adanya
        }

        const rawLabels = Object.keys(timeSeriesData).sort(); // Urutkan data mentah secara kronologis
        const positiveData = rawLabels.map(label => timeSeriesData[label].Positif || 0);
        const negativeData = rawLabels.map(label => timeSeriesData[label].Negatif || 0);
        const neutralData = rawLabels.map(label => timeSeriesData[label].Netral || 0);
        
        const displayLabels = rawLabels.map(formatChartLabel); // Konversi ke teks yang nyaman dibaca

        // Hitung persentase untuk grafik tren
        const positivePercentages = [];
        const negativePercentages = [];
        const neutralPercentages = [];
        for (let i = 0; i < rawLabels.length; i++) {
            const total = positiveData[i] + negativeData[i] + neutralData[i];
            if (total > 0) {
                positivePercentages.push((positiveData[i] / total) * 100);
                negativePercentages.push((negativeData[i] / total) * 100);
                neutralPercentages.push((neutralData[i] / total) * 100);
            } else {
                positivePercentages.push(0);
                negativePercentages.push(0);
                neutralPercentages.push(0);
            }
        }

        if (timeSeriesChartInstance) timeSeriesChartInstance.destroy();
        timeSeriesChartInstance = new Chart(timeCtx, {
            type: 'line',
            data: {
                labels: displayLabels,
                datasets: [{
                    label: 'Positif',
                    data: positivePercentages,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    fill: true,
                    borderWidth: 3
                }, {
                    label: 'Negatif',
                    data: negativePercentages,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4,
                    fill: true,
                    borderWidth: 3
                }, {
                    label: 'Netral',
                    data: neutralPercentages,
                    borderColor: '#9ca3af',
                    backgroundColor: 'rgba(156, 163, 175, 0.1)',
                    tension: 0.4,
                    fill: true,
                    borderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: { callback: value => value + '%' }
                    }
                },
                plugins: { legend: { position: 'top' } }
            }
        });
    }

    /**
     * Inisialisasi Card Insight untuk kata kunci dominan.
     * @param {object} keywordData - Top keywords data grouped by Aspect and Sentiment.
     */
    function initKeywordInsights(keywordData) {
        const container = document.getElementById('keywordInsightsContainer');
        if (!container) return;
        container.innerHTML = '';

        if (!keywordData || Object.keys(keywordData).length === 0) {
            container.innerHTML = '<div class="col-12 text-center text-muted py-4"><i class="fas fa-folder-open mb-2 fs-3 opacity-50"></i><br>Belum ada data kata kunci yang cukup pada periode ini.</div>';
            return;
        }

        let hasContent = false;
        for (const [aspect, sentiments] of Object.entries(keywordData)) {
            // Hanya tampilkan jika ada keyword positif atau negatif
            if (!sentiments['Positif'] && !sentiments['Negatif']) continue;

            let html = `<div class="col-md-6 col-lg-4">
                <div class="border rounded p-3 h-100 bg-white shadow-sm">
                    <h6 class="fw-bold border-bottom pb-2 mb-3 text-dark"><i class="fas fa-tag text-primary me-2"></i>Aspek: ${aspect}</h6>`;

            if (sentiments['Positif'] && sentiments['Positif'].length > 0) {
                html += `<div class="mb-3">
                            <span class="d-block text-success fw-semibold mb-2" style="font-size: 0.8rem;">Faktor Positif:</span>
                            <div class="d-flex flex-wrap gap-1">`;
                sentiments['Positif'].forEach(kw => {
                    html += `<span class="badge bg-success bg-opacity-10 text-success border border-success-subtle px-2 py-1">${kw.word}</span>`;
                });
                html += `</div></div>`;
            }

            if (sentiments['Negatif'] && sentiments['Negatif'].length > 0) {
                html += `<div class="mb-2">
                            <span class="d-block text-danger fw-semibold mb-2" style="font-size: 0.8rem;">Faktor Negatif:</span>
                            <div class="d-flex flex-wrap gap-1">`;
                sentiments['Negatif'].forEach(kw => {
                    html += `<span class="badge bg-danger bg-opacity-10 text-danger border border-danger-subtle px-2 py-1">${kw.word}</span>`;
                });
                html += `</div></div>`;
            }

            html += `</div></div>`;
            container.innerHTML += html;
            hasContent = true;
        }
        
        if (!hasContent) {
            container.innerHTML = '<div class="col-12 text-center text-muted py-4"><i class="fas fa-folder-open mb-2 fs-3 opacity-50"></i><br>Belum ada data kata kunci yang cukup pada periode ini.</div>';
        }
    }
});