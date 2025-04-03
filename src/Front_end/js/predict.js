const API_BASE_URL = 'https://bankruptcy-pipeline.onrender.com';
const EXPECTED_FIELDS = [
    "retained_earnings_to_total_assets", 
    "total_debt_per_total_net_worth", 
    "borrowing_dependency",
    "persistent_eps_in_the_last_four_seasons",
    "continuous_net_profit_growth_rate",
    "net_profit_before_tax_per_paidin_capital",
    "equity_to_liability",
    "pretax_net_interest_rate",
    "degree_of_financial_leverage",
    "per_share_net_profit_before_tax",
    "liability_to_equity",
    "net_income_to_total_assets",
    "total_income_per_total_expense",
    "interest_expense_ratio",
    "interest_coverage_ratio"
];

function initializeFormFields() {
    const formGrid = document.getElementById("formGridContainer");
    formGrid.innerHTML = '';
    
    EXPECTED_FIELDS.forEach(field => {
        const div = document.createElement("div");
        div.className = "form-item";
        
        const label = document.createElement("label");
        label.htmlFor = field;
        label.textContent = field.replace(/_/g, " ") + ":";
        
        const input = document.createElement("input");
        input.type = "number";
        input.step = "0.0001";
        input.id = field;
        input.name = field;
        input.required = true;
        
        div.appendChild(label);
        div.appendChild(input);
        formGrid.appendChild(div);
    });
}

function toggleSpinner(spinnerId, show) {
    document.getElementById(spinnerId).style.display = show ? 'block' : 'none';
}

function showPredictionResult(prediction, probability) {
    const isHighRisk = prediction === 1;
    const resultContainer = document.getElementById("singlePredictionResult");
    const confidenceBar = document.getElementById("confidenceBar");
    const riskPercentage = document.getElementById("riskPercentage");
    const riskExplanation = document.getElementById("riskExplanation");
    
    // Set styling
    resultContainer.className = `result-container ${isHighRisk ? 'risk-high' : 'risk-low'}`;
    
    // Update confidence meter
    const confidencePercent = Math.round(probability * 100);
    confidenceBar.style.width = `${confidencePercent}%`;
    confidenceBar.style.backgroundColor = isHighRisk ? '#c62828' : '#2e7d32';
    
    // Set text content (your requested format)
    riskPercentage.textContent = isHighRisk
        ? `HIGH RISK (${confidencePercent}% chance of bankruptcy)`
        : `LOW RISK (${confidencePercent}% chance of bankruptcy)`;
    
    riskExplanation.textContent = isHighRisk
        ? "Immediate attention recommended"
        : "Your financial health appears stable";
    
    resultContainer.style.display = 'block';
}

async function handleBulkPrediction(e) {
    e.preventDefault();
    const fileInput = document.getElementById("dataset");
    
    if (!fileInput.files.length) {
        alert("Please select a file first");
        return;
    }

    toggleSpinner('bulkPredictionSpinner', true);
    const resultContainer = document.getElementById('bulkPredictionResult');
    resultContainer.style.display = 'none';
    resultContainer.innerHTML = '';

    try {
        const formData = new FormData();
        formData.append("file", fileInput.files[0]);

        const response = await fetch(`${API_BASE_URL}/predict-bulk/`, {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `Server error: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Check if results exist and is an array
        if (!result.results || !Array.isArray(result.results)) {
            throw new Error("Invalid response format from server");
        }
        
        const predictions = result.results;
        const highRiskCount = predictions.filter(p => p.prediction === 1).length;
        const total = predictions.length;
        const highRiskPercent = total > 0 ? Math.round(highRiskCount/total*100) : 0;
        
        // Create summary card
        const summaryHTML = `
            <div class="summary-card">
                <strong>Batch Summary:</strong> Processed ${total} records with 
                <span class="risk-badge ${highRiskCount ? 'badge-high' : 'badge-low'}">
                    ${highRiskCount} high risk (${highRiskPercent}%)
                </span>
            </div>
        `;
        
        // Create table header
        let tableHTML = `
            <table class="result-table">
                <thead>
                    <tr>
                        <th>Record #</th>
                        <th>Risk Level</th>
                        <th>Probability</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        // Add each prediction as a row
        predictions.forEach((pred, index) => {
            const isHighRisk = pred.prediction === 1;
            const confidencePercent = pred.probability !== undefined && pred.probability !== null 
                ? Math.round(pred.probability * 100) 
                : 'N/A';
            
            tableHTML += `
                <tr>
                    <td>${index + 1}</td>
                    <td><span class="risk-badge ${isHighRisk ? 'badge-high' : 'badge-low'}">
                        ${isHighRisk ? 'HIGH RISK' : 'LOW RISK'}
                    </span></td>
                    <td>${confidencePercent}%</td>
                </tr>
            `;
        });
        
        tableHTML += `</tbody></table>`;
        
        // Combine and display
        resultContainer.innerHTML = summaryHTML + tableHTML;
        resultContainer.style.display = 'block';
        
    } catch (error) {
        console.error("Bulk prediction error:", error);
        resultContainer.innerHTML = `
            <div class="risk-high" style="padding: 15px; text-align: left;">
                <strong>Error:</strong> ${error.message}
            </div>
        `;
        resultContainer.style.display = 'block';
    } finally {
        toggleSpinner('bulkPredictionSpinner', false);
    }
}

async function handleSinglePrediction(e) {
    e.preventDefault();
    
    toggleSpinner('singlePredictionSpinner', true);
    document.getElementById('singlePredictionResult').style.display = 'none';
    
    const formData = {};
    EXPECTED_FIELDS.forEach(field => {
        formData[field] = parseFloat(document.getElementById(field).value);
    });

    try {
        const response = await fetch(`${API_BASE_URL}/predict-single/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(formData)
        });

        if (!response.ok) throw new Error(`Server error: ${response.status}`);
        
        const result = await response.json();
        showPredictionResult(result.prediction, result.probability);
        
    } catch (error) {
        console.error("Prediction error:", error);
        alert(`Prediction failed: ${error.message}`);
    } finally {
        toggleSpinner('singlePredictionSpinner', false);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initializeFormFields();
    document.getElementById("singlePredictionForm").addEventListener("submit", handleSinglePrediction);
    document.getElementById("bulkPredictionForm").addEventListener("submit", handleBulkPrediction);
});