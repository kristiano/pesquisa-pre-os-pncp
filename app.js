document.addEventListener('DOMContentLoaded', () => {
    const apiKeyInput = document.getElementById('apiKeyInput');
    const searchInput = document.getElementById('searchInput');
    const searchBtn = document.getElementById('searchBtn');
    const searchBoxContainer = document.getElementById('searchBoxContainer');
    
    const loader = document.getElementById('loader');
    const resultsContainer = document.getElementById('resultsContainer');
    const tableBody = document.getElementById('tableBody');
    
    // Stats Elements
    const valMedia = document.getElementById('valMedia');
    const valMediana = document.getElementById('valMediana');
    const valCV = document.getElementById('valCV');
    const txtRecomendacao = document.getElementById('txtRecomendacao');
    const cvCard = valCV.parentElement;

    // Habilita a barra de busca apenas se a API Key for preenchida
    apiKeyInput.addEventListener('input', () => {
        if (apiKeyInput.value.trim().length > 5) {
            searchInput.disabled = false;
            searchBtn.disabled = false;
            searchBoxContainer.classList.remove('disabled-box');
        } else {
            searchInput.disabled = true;
            searchBtn.disabled = true;
            searchBoxContainer.classList.add('disabled-box');
        }
    });

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
    };

    const searchPrices = async () => {
        const query = searchInput.value.trim();
        const apiKey = apiKeyInput.value.trim();
        if (!query || !apiKey) return;

        // UI Reset
        resultsContainer.classList.add('hidden');
        loader.classList.remove('hidden');
        tableBody.innerHTML = '';

        try {
            const response = await fetch('/api/pesquisa', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    objeto: query, 
                    quantidade_itens: 15,
                    llm_api_key: apiKey // Enviamos a chave informada pelo usuário para o Backend
                })
            });

            if (!response.ok) throw new Error('Falha na requisição');
            const data = await response.json();
            
            renderResults(data);

        } catch (error) {
            console.error(error);
            alert('Erro ao buscar dados ou chave de API inválida.');
        } finally {
            loader.classList.add('hidden');
        }
    };

    const renderResults = (data) => {
        if (!data.registros || data.registros.length === 0) {
            alert('Nenhum resultado encontrado.');
            return;
        }

        const stats = data.estatisticas;
        
        // Update Stats
        valMedia.textContent = formatCurrency(stats.media);
        valMediana.textContent = formatCurrency(stats.mediana);
        valCV.textContent = stats.cv_percentual.toFixed(1).replace('.', ',') + '%';
        txtRecomendacao.innerHTML = `<strong>Recomendação (IN 65/2021):</strong> ${stats.criterio_sugerido}`;

        if (!stats.cesta_homogenea) {
            valCV.classList.add('text-danger');
            cvCard.classList.add('cv-high');
        } else {
            valCV.classList.remove('text-danger');
            cvCard.classList.remove('cv-high');
        }

        // Render Table
        data.registros.forEach(item => {
            const isOutlier = stats.outliers_detectados && stats.outliers_detectados.some(o => o.valor === item.valor);
            const tr = document.createElement('tr');
            if (isOutlier) tr.classList.add('outlier-row');

            tr.innerHTML = `
                <td>
                    <div style="margin-bottom: 4px;">${item.objeto.substring(0, 80)}${item.objeto.length > 80 ? '...' : ''}</div>
                    ${isOutlier ? '<span style="color:var(--danger); font-size:0.75rem;">(Descartado - Outlier)</span>' : ''}
                </td>
                <td class="td-value">${formatCurrency(item.valor)}</td>
                <td class="td-source">${item.fonte}</td>
                <td class="td-source">${item.data_acesso}</td>
                <td><a href="${item.link}" target="_blank" class="btn-link">Ver no PNCP</a></td>
            `;
            tableBody.appendChild(tr);
        });

        resultsContainer.classList.remove('hidden');
    };

    searchBtn.addEventListener('click', searchPrices);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !searchInput.disabled) searchPrices();
    });
});
