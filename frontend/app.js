// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// State
let currentDocuments = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadDocuments();
});

function setupEventListeners() {
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
    
    // Upload
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#667eea';
    });
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '#ccc';
    });
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        handleFiles(e.dataTransfer.files);
    });
    
    fileInput.addEventListener('change', (e) => handleFiles(e.target.files));
    
    // Q&A
    document.getElementById('ask-btn').addEventListener('click', askQuestion);
    document.getElementById('question-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            askQuestion();
        }
    });
    
    // Summary
    document.getElementById('summarize-btn').addEventListener('click', generateSummary);
    
    // Quiz
    document.getElementById('generate-quiz-btn').addEventListener('click', generateQuiz);
}

function switchTab(tabId) {
    // Update buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabId);
    });
    
    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `${tabId}-tab`);
    });
}

async function handleFiles(files) {
    for (const file of files) {
        await uploadFile(file);
    }
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    showUploadProgress(file.name);
    
    try {
        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            addUploadedFileToList(result);
            await loadDocuments();
            showNotification(`✅ ${file.name} uploaded successfully!`, 'success');
        } else {
            throw new Error('Upload failed');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showNotification(`❌ Failed to upload ${file.name}`, 'error');
    }
}

function showUploadProgress(filename) {
    const list = document.getElementById('upload-list');
    const item = document.createElement('div');
    item.className = 'upload-item';
    item.id = `upload-${filename}`;
    item.innerHTML = `
        <span>${filename}</span>
        <div class="loading"></div>
    `;
    list.appendChild(item);
}

function addUploadedFileToList(fileInfo) {
    const list = document.getElementById('upload-list');
    const existingItem = document.getElementById(`upload-${fileInfo.filename}`);
    if (existingItem) {
        existingItem.innerHTML = `
            <span>${fileInfo.filename}</span>
            <span style="color: green;">✓ ${fileInfo.chunk_count} chunks</span>
        `;
        setTimeout(() => existingItem.remove(), 3000);
    }
}

async function askQuestion() {
    const questionInput = document.getElementById('question-input');
    const question = questionInput.value.trim();
    
    if (!question) return;
    
    // Add user message
    addMessage(question, 'user');
    questionInput.value = '';
    
    // Show loading
    const loadingMsg = addMessage('Thinking...', 'assistant', true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: question, top_k: 5 })
        });
        
        if (response.ok) {
            const data = await response.json();
            removeLoadingMessage(loadingMsg);
            addMessage(data.answer, 'assistant', false, data.sources);
        } else {
            throw new Error('Query failed');
        }
    } catch (error) {
        console.error('Query error:', error);
        removeLoadingMessage(loadingMsg);
        addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
    }
}

function addMessage(content, sender, isLoading = false, sources = null) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const time = new Date().toLocaleTimeString();
    
    let sourcesHtml = '';
    if (sources && sources.length > 0) {
        sourcesHtml = `
            <div class="sources">
                <strong>📚 Sources:</strong><br>
                ${sources.map(s => `• ${s.document_name} (confidence: ${(s.similarity_score * 100).toFixed(0)}%)`).join('<br>')}
            </div>
        `;
    }
    
    messageDiv.innerHTML = `
        <div class="message-content">
            ${isLoading ? '<div class="loading"></div>' : content}
            ${sourcesHtml}
        </div>
        <div class="message-time">${time}</div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    return messageDiv;
}

function removeLoadingMessage(messageDiv) {
    if (messageDiv) messageDiv.remove();
}

async function generateSummary() {
    const style = document.getElementById('summary-style').value;
    const resultDiv = document.getElementById('summary-result');
    
    resultDiv.innerHTML = '<div class="loading"></div> Generating summary...';
    
    try {
        const response = await fetch(`${API_BASE_URL}/summarize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ style: style, max_length: 500 })
        });
        
        if (response.ok) {
            const data = await response.json();
            resultDiv.innerHTML = `
                <div class="summary-text">
                    <h3>📄 Summary</h3>
                    <p>${data.summary}</p>
                </div>
                <div class="key-points">
                    <h4>🔑 Key Points</h4>
                    <ul>
                        ${data.key_points.map(point => `<li>${point}</li>`).join('')}
                    </ul>
                </div>
            `;
        } else {
            throw new Error('Summary generation failed');
        }
    } catch (error) {
        console.error('Summary error:', error);
        resultDiv.innerHTML = '<p style="color: red;">Failed to generate summary. Please ensure a document is uploaded.</p>';
    }
}

async function generateQuiz() {
    const numQuestions = document.getElementById('quiz-questions').value;
    const difficulty = document.getElementById('quiz-difficulty').value;
    const quizContainer = document.getElementById('quiz-container');
    
    quizContainer.innerHTML = '<div class="loading"></div> Generating quiz...';
    
    try {
        const response = await fetch(`${API_BASE_URL}/quiz`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                num_questions: parseInt(numQuestions), 
                difficulty: difficulty,
                question_types: ["multiple_choice", "true_false"]
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            displayQuiz(data.questions);
        } else {
            throw new Error('Quiz generation failed');
        }
    } catch (error) {
        console.error('Quiz error:', error);
        quizContainer.innerHTML = '<p style="color: red;">Failed to generate quiz. Please ensure a document is uploaded.</p>';
    }
}

function displayQuiz(questions) {
    const quizContainer = document.getElementById('quiz-container');
    quizContainer.innerHTML = '<h3>📝 Quiz Time!</h3>';
    
    questions.forEach((q, idx) => {
        const questionDiv = document.createElement('div');
        questionDiv.className = 'quiz-question';
        questionDiv.dataset.questionId = idx;
        questionDiv.dataset.correctAnswer = q.correct_answer;
        
        let optionsHtml = '';
        if (q.question_type === 'multiple_choice' && q.options) {
            optionsHtml = '<div class="quiz-options">';
            q.options.forEach(opt => {
                optionsHtml += `
                    <div class="quiz-option" onclick="selectOption(this, '${opt.replace(/'/g, "\\'")}')">
                        ${opt}
                    </div>
                `;
            });
            optionsHtml += '</div>';
        } else if (q.question_type === 'true_false') {
            optionsHtml = `
                <div class="quiz-options">
                    <div class="quiz-option" onclick="selectOption(this, 'True')">True</div>
                    <div class="quiz-option" onclick="selectOption(this, 'False')">False</div>
                </div>
            `;
        }
        
        questionDiv.innerHTML = `
            <h4>${idx + 1}. ${q.question}</h4>
            ${optionsHtml}
            <div class="quiz-feedback"></div>
            <div class="quiz-explanation" style="display:none; margin-top:10px; padding:10px; background:#e0e0e0; border-radius:5px;">
                <strong>Explanation:</strong> ${q.explanation}
            </div>
        `;
        
        quizContainer.appendChild(questionDiv);
    });
    
    // Add submit button
    const submitBtn = document.createElement('button');
    submitBtn.className = 'btn btn-primary';
    submitBtn.textContent = 'Submit Quiz';
    submitBtn.style.marginTop = '20px';
    submitBtn.onclick = submitQuiz;
    quizContainer.appendChild(submitBtn);
}

function selectOption(element, answer) {
    const questionDiv = element.closest('.quiz-question');
    // Remove selected class from all options in this question
    questionDiv.querySelectorAll('.quiz-option').forEach(opt => {
        opt.classList.remove('selected');
    });
    element.classList.add('selected');
    questionDiv.dataset.selectedAnswer = answer;
}

function submitQuiz() {
    const questions = document.querySelectorAll('.quiz-question');
    let score = 0;
    
    questions.forEach(question => {
        const selected = question.dataset.selectedAnswer;
        const correct = question.dataset.correctAnswer;
        const feedbackDiv = question.querySelector('.quiz-feedback');
        const explanationDiv = question.querySelector('.quiz-explanation');
        
        if (selected === correct) {
            score++;
            feedbackDiv.innerHTML = '✅ Correct!';
            feedbackDiv.className = 'quiz-feedback correct';
        } else if (selected) {
            feedbackDiv.innerHTML = `❌ Incorrect. Correct answer: ${correct}`;
            feedbackDiv.className = 'quiz-feedback incorrect';
            explanationDiv.style.display = 'block';
        } else {
            feedbackDiv.innerHTML = '⚠️ Not answered.';
            feedbackDiv.className = 'quiz-feedback incorrect';
        }
    });
    
    showNotification(`🎉 Quiz completed! Score: ${score}/${questions.length}`, 'success');
}

async function loadDocuments() {
    try {
        const response = await fetch(`${API_BASE_URL}/documents`);
        if (response.ok) {
            currentDocuments = await response.json();
            updateDocumentList();
        }
    } catch (error) {
        console.error('Load documents error:', error);
    }
}

function updateDocumentList() {
    const listDiv = document.getElementById('upload-list');
    if (currentDocuments.length > 0) {
        listDiv.innerHTML = '<h4>📄 Uploaded Documents:</h4>';
        currentDocuments.forEach(doc => {
            listDiv.innerHTML += `
                <div class="upload-item">
                    <span>${doc.filename}</span>
                    <span>${doc.chunk_count} chunks • ID: ${doc.id.substring(0, 8)}</span>
                </div>
            `;
        });
    }
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        background: ${type === 'success' ? '#48bb78' : '#f56565'};
        color: white;
        border-radius: 8px;
        z-index: 1000;
        animation: slideIn 0.3s;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => notification.remove(), 3000);
}