const API_BASE_URL = 'https://bankruptcy-pipeline.onrender.com';
        
// Static metrics from your notebook
const staticMetrics = {
    accuracy: 0.9663,
    precision: 0.4643,
    recall: 0.2955,
    f1: 0.3611
};

// DOM elements
const uploadForm = document.getElementById("upload-form");
const retrainBtn = document.getElementById("retrain-btn");
const saveBtn = document.getElementById("save-model-btn");
const statusDiv = document.getElementById("status");

// Metrics elements
const accuracyElem = document.getElementById("accuracy");
const precisionElem = document.getElementById("precision");
const recallElem = document.getElementById("recall");
const f1ScoreElem = document.getElementById("f1-score");

const newAccuracyElem = document.getElementById("new-accuracy");
const newPrecisionElem = document.getElementById("new-precision");
const newRecallElem = document.getElementById("new-recall");
const newF1ScoreElem = document.getElementById("new-f1-score");

// State
let currentModelId = null;

// Helper functions
function toggleSpinner(spinnerId, show) {
    const spinner = document.getElementById(spinnerId);
    if (spinner) {
        spinner.style.display = show ? 'block' : 'none';
    }
}

function updateStatus(message, isError = false, isSuccess = false) {
    if (statusDiv) {
        statusDiv.textContent = message;
        statusDiv.className = 'status';
        if (isError) statusDiv.classList.add('error');
        if (isSuccess) statusDiv.classList.add('success');
    }
}

function formatMetric(value) {
    return value !== null && value !== undefined ? value.toFixed(4) : '-';
}

// Load current model metrics on page load
function loadCurrentMetrics() {
    // Display static metrics from notebook
    if (accuracyElem) accuracyElem.textContent = formatMetric(staticMetrics.accuracy);
    if (precisionElem) precisionElem.textContent = formatMetric(staticMetrics.precision);
    if (recallElem) recallElem.textContent = formatMetric(staticMetrics.recall);
    if (f1ScoreElem) f1ScoreElem.textContent = formatMetric(staticMetrics.f1);
    
    updateStatus("Loaded default model metrics", false, true);
}

// Handle dataset upload
uploadForm.addEventListener("submit", async function(event) {
    event.preventDefault();
    const fileInput = document.getElementById("dataset-upload");
    
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        updateStatus("Please select a file first", true);
        return;
    }
    
    toggleSpinner('upload-spinner', true);
    updateStatus("Uploading dataset...");
    
    try {
        const formData = new FormData();
        formData.append("file", fileInput.files[0]);
        
        const response = await fetch(`${API_BASE_URL}/upload-training-data/`, {
            method: "POST",
            body: formData
        });
        
        if (!response.ok) {
            let errorDetail = "Upload failed";
            try {
                const errorData = await response.json();
                errorDetail = errorData.detail || errorData.message || errorDetail;
            } catch (e) {
                console.error("Error parsing error response:", e);
            }
            throw new Error(errorDetail);
        }
        
        const result = await response.json();
        updateStatus(`Successfully uploaded ${result.records_added} records. ${result.invalid_records} records were invalid.`, false, true);
        
        // Enable retrain button
        if (retrainBtn) retrainBtn.disabled = false;
        
    } catch (error) {
        console.error("Upload error:", error);
        updateStatus(`Upload failed: ${error.message}`, true);
    } finally {
        toggleSpinner('upload-spinner', false);
    }
});

// Handle retrain button click
retrainBtn.addEventListener("click", async function() {
    toggleSpinner('retrain-spinner', true);
    updateStatus("Retraining model... This may take a few moments.");
    
    try {
        const response = await fetch(`${API_BASE_URL}/retrain/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            }
        });
        
        if (!response.ok) {
            let errorDetail = "Retraining failed";
            try {
                const errorData = await response.json();
                errorDetail = errorData.detail || errorData.message || errorDetail;
            } catch (e) {
                console.error("Error parsing error response:", e);
            }
            throw new Error(errorDetail);
        }
        
        const result = await response.json();
        currentModelId = result.model_id;
        
        // Update new metrics display
        if (newAccuracyElem) newAccuracyElem.textContent = formatMetric(result.metrics.accuracy);
        if (newPrecisionElem) newPrecisionElem.textContent = formatMetric(result.metrics.precision);
        if (newRecallElem) newRecallElem.textContent = formatMetric(result.metrics.recall);
        if (newF1ScoreElem) newF1ScoreElem.textContent = formatMetric(result.metrics.f1);
        
        // Enable save button
        if (saveBtn) saveBtn.disabled = false;
        
        updateStatus(result.message || "Model retrained successfully!", false, true);
        
    } catch (error) {
        console.error("Retrain error:", error);
        updateStatus(`Retraining failed: ${error.message}`, true);
    } finally {
        toggleSpinner('retrain-spinner', false);
    }
});

// Handle save model button click
saveBtn.addEventListener("click", async function() {
    if (!currentModelId) {
        updateStatus("No model to save. Please retrain first.", true);
        return;
    }
    
    const saveStatus = document.getElementById("save-status");
    if (saveStatus) {
        saveStatus.textContent = "Saving model...";
        saveStatus.style.color = "inherit";
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/save-model/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                model_id: currentModelId
            })
        });
        
        if (!response.ok) {
            let errorDetail = "Save failed";
            try {
                const errorData = await response.json();
                errorDetail = errorData.detail || errorData.message || errorDetail;
            } catch (e) {
                console.error("Error parsing error response:", e);
            }
            throw new Error(errorDetail);
        }
        
        const result = await response.json();
        
        // Update our static metrics to match the new model
        staticMetrics.accuracy = parseFloat(newAccuracyElem.textContent) || staticMetrics.accuracy;
        staticMetrics.precision = parseFloat(newPrecisionElem.textContent) || staticMetrics.precision;
        staticMetrics.recall = parseFloat(newRecallElem.textContent) || staticMetrics.recall;
        staticMetrics.f1 = parseFloat(newF1ScoreElem.textContent) || staticMetrics.f1;
        
        // Update the current metrics display
        if (accuracyElem) accuracyElem.textContent = formatMetric(staticMetrics.accuracy);
        if (precisionElem) precisionElem.textContent = formatMetric(staticMetrics.precision);
        if (recallElem) recallElem.textContent = formatMetric(staticMetrics.recall);
        if (f1ScoreElem) f1ScoreElem.textContent = formatMetric(staticMetrics.f1);
        
        if (saveStatus) {
            saveStatus.textContent = result.message || "Model saved successfully!";
            saveStatus.style.color = "#2e7d32";
        }
        updateStatus("Model saved successfully! Current metrics updated.", false, true);
        
    } catch (error) {
        console.error("Save error:", error);
        if (saveStatus) {
            saveStatus.textContent = `Save failed: ${error.message}`;
            saveStatus.style.color = "#c62828";
        }
    }
});

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    loadCurrentMetrics();
});