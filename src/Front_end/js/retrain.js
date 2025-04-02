const API_BASE_URL = 'http://localhost:8000';
        
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
    document.getElementById(spinnerId).style.display = show ? 'block' : 'none';
}

function updateStatus(message, isError = false, isSuccess = false) {
    statusDiv.textContent = message;
    statusDiv.className = 'status';
    if (isError) statusDiv.classList.add('error');
    if (isSuccess) statusDiv.classList.add('success');
}

function formatMetric(value) {
    return value !== null && value !== undefined ? value.toFixed(4) : '-';
}

// Load current model metrics on page load
function loadCurrentMetrics() {
    // Display static metrics from notebook
    accuracyElem.textContent = formatMetric(staticMetrics.accuracy);
    precisionElem.textContent = formatMetric(staticMetrics.precision);
    recallElem.textContent = formatMetric(staticMetrics.recall);
    f1ScoreElem.textContent = formatMetric(staticMetrics.f1);
    
    updateStatus("Loaded default model metrics", false, true);
}

// Handle dataset upload (keep this exactly the same)
uploadForm.addEventListener("submit", async function(event) {
    event.preventDefault();
    const fileInput = document.getElementById("dataset-upload");
    
    if (!fileInput.files.length) {
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
            const errorData = await response.json();
            throw new Error(errorData.detail || "Upload failed");
        }
        
        const result = await response.json();
        updateStatus(`Successfully uploaded ${result.records_added} records. ${result.invalid_records} records were invalid.`, false, true);
        
        // Enable retrain button
        retrainBtn.disabled = false;
        
    } catch (error) {
        console.error("Upload error:", error);
        updateStatus(`Upload failed: ${error.message}`, true);
    } finally {
        toggleSpinner('upload-spinner', false);
    }
});

// Handle retrain button click (keep this the same)
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
            const errorData = await response.json();
            throw new Error(errorData.detail || "Retraining failed");
        }
        
        const result = await response.json();
        currentModelId = result.model_id;
        
        // Update new metrics display
        newAccuracyElem.textContent = formatMetric(result.metrics.accuracy);
        newPrecisionElem.textContent = formatMetric(result.metrics.precision);
        newRecallElem.textContent = formatMetric(result.metrics.recall);
        newF1ScoreElem.textContent = formatMetric(result.metrics.f1);
        
        // Enable save button
        saveBtn.disabled = false;
        
        updateStatus(result.message, false, true);
        
    } catch (error) {
        console.error("Retrain error:", error);
        updateStatus(`Retraining failed: ${error.message}`, true);
    } finally {
        toggleSpinner('retrain-spinner', false);
    }
});

// Handle save model button click (modified to update static metrics)
saveBtn.addEventListener("click", async function() {
    if (!currentModelId) {
        updateStatus("No model to save. Please retrain first.", true);
        return;
    }
    
    const saveStatus = document.getElementById("save-status");
    saveStatus.textContent = "Saving model...";
    saveStatus.style.color = "inherit";
    
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
            const errorData = await response.json();
            throw new Error(errorData.detail || "Save failed");
        }
        
        // Update our static metrics to match the new model
        staticMetrics.accuracy = parseFloat(newAccuracyElem.textContent);
        staticMetrics.precision = parseFloat(newPrecisionElem.textContent);
        staticMetrics.recall = parseFloat(newRecallElem.textContent);
        staticMetrics.f1 = parseFloat(newF1ScoreElem.textContent);
        
        // Update the current metrics display
        accuracyElem.textContent = newAccuracyElem.textContent;
        precisionElem.textContent = newPrecisionElem.textContent;
        recallElem.textContent = newRecallElem.textContent;
        f1ScoreElem.textContent = newF1ScoreElem.textContent;
        
        saveStatus.textContent = "Model saved successfully!";
        saveStatus.style.color = "#2e7d32";
        updateStatus("Model saved successfully! Current metrics updated.", false, true);
        
    } catch (error) {
        console.error("Save error:", error);
        saveStatus.textContent = `Save failed: ${error.message}`;
        saveStatus.style.color = "#c62828";
    }
});

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    loadCurrentMetrics();
});