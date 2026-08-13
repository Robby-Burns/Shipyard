/* ==========================================================================
   SHIPYARD FRONTEND CONTROLLER
   ========================================================================== */

const API_BASE = window.location.origin;
let CURRENT_TOKEN = localStorage.getItem("shipyard_dev_token") || "";
let ACTIVE_POLLING_INTERVAL = null;

// Global App State
const state = {
    activeTab: "new-request",
    projects: [],
    activeProjectId: null,
    activeIntakeSession: null,
    globalJournal: [],
    passports: [],
    knowledgeSubTab: "candidates",
    knowledgeCandidates: [],
    sharedKnowledge: [],
    activeKnowledgeItemId: null
};

// Initializer
document.addEventListener("DOMContentLoaded", async () => {
    // 1. Establish auth token
    await initAuth();

    // 2. Setup navigation
    setupNavigation();

    // 3. Start default panels
    await initIntakeChat();
    await loadProjects();
    await loadGlobalJournal();
    await updateCandidatesBadgeCount();

    // 4. Setup text area sizing & input handlers
    setupInputHandlers();
});

// Setup Dev Auth automatically
async function initAuth() {
    if (CURRENT_TOKEN) {
        // Validate the cached token by hitting the protected test route
        try {
            const res = await fetch(`${API_BASE}/api/v1/me`, {
                method: "GET",
                headers: getHeaders()
            });
            if (!res.ok) {
                console.log("Cached dev token is invalid or expired. Clearing...");
                localStorage.removeItem("shipyard_dev_token");
                CURRENT_TOKEN = "";
            }
        } catch (e) {
            console.error("Failed to validate cached token:", e);
        }
    }

    if (!CURRENT_TOKEN) {
        try {
            console.log("Requesting dev token...");
            const res = await fetch(`${API_BASE}/api/v1/auth/token?username=dev_user&role=admin`, {
                method: "POST"
            });
            if (res.ok) {
                const data = await res.json();
                CURRENT_TOKEN = data.access_token;
                localStorage.setItem("shipyard_dev_token", CURRENT_TOKEN);
                console.log("Dev auth token generated and cached.");
            } else {
                console.error("Failed to generate dev token automatically.");
            }
        } catch (e) {
            console.error("Auth helper error:", e);
        }
    }
}

// Fetch headers
function getHeaders(extraHeaders = {}) {
    const headers = {
        "Content-Type": "application/json",
        ...extraHeaders
    };
    if (CURRENT_TOKEN) {
        headers["Authorization"] = `Bearer ${CURRENT_TOKEN}`;
    }
    return headers;
}

// Tab Navigation Switching
function setupNavigation() {
    const navButtons = document.querySelectorAll(".nav-btn");
    navButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const tabName = btn.getAttribute("data-tab");
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    state.activeTab = tabName;

    // Toggle nav active state
    document.querySelectorAll(".nav-btn").forEach(btn => {
        if (btn.getAttribute("data-tab") === tabName) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });

    // Toggle panel visibility
    document.querySelectorAll(".tab-panel").forEach(panel => {
        if (panel.id === `${tabName}-panel`) {
            panel.classList.add("active");
        } else {
            panel.classList.remove("active");
        }
    });

    // Stop polling if switching away from active project view
    if (tabName !== "projects" && ACTIVE_POLLING_INTERVAL) {
        clearInterval(ACTIVE_POLLING_INTERVAL);
        ACTIVE_POLLING_INTERVAL = null;
    }

    // Refresh contents
    if (tabName === "projects") {
        loadProjects();
    } else if (tabName === "journal") {
        loadGlobalJournal();
    } else if (tabName === "passports") {
        loadPassportsDirectory();
    } else if (tabName === "knowledge") {
        initKnowledgeBoard();
    } else if (tabName === "infrastructure") {
        loadInfrastructure();
    }
}

// Input Handlers (textarea autosize and keyboard submission)
function setupInputHandlers() {
    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-chat-btn");

    chatInput.addEventListener("input", function() {
        this.style.height = "auto";
        this.style.height = (this.scrollHeight - 4) + "px";
    });

    chatInput.addEventListener("keydown", function(e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });

    sendBtn.addEventListener("click", sendChatMessage);

    // File upload handlers
    const uploadBtn = document.getElementById("upload-file-btn");
    const fileInput = document.getElementById("file-input");
    
    if (uploadBtn && fileInput) {
        uploadBtn.addEventListener("click", () => {
            fileInput.click();
        });
        fileInput.addEventListener("change", handleFileUpload);
    }

    // Setup promote button from Intake to Workflow
    document.getElementById("start-project-btn").addEventListener("click", promoteIntakeToProject);
    document.getElementById("intake-repo-url").addEventListener("input", updateStartProjectButton);

    // Setup global search / filters in journal
    document.getElementById("journal-search").addEventListener("input", filterJournal);
    document.getElementById("journal-source-filter").addEventListener("change", filterJournal);

    // Setup Modal Close
    document.getElementById("close-modal-btn").addEventListener("click", () => {
        document.getElementById("json-modal").classList.remove("active");
    });

    // Setup Knowledge Board subtab switches
    document.getElementById("knowledge-tab-candidates").addEventListener("click", () => switchKnowledgeSubTab("candidates"));
    document.getElementById("knowledge-tab-vault").addEventListener("click", () => switchKnowledgeSubTab("vault"));
}

/* ==========================================================================
   Dest 1: NEW ENGINEERING REQUEST (INTAKE CHAT)
   ========================================================================== */
async function initIntakeChat() {
    const chatContainer = document.getElementById("chat-messages");
    chatContainer.innerHTML = "";

    try {
        // Create an intake session automatically on first load or request
        const res = await fetch(`${API_BASE}/api/v1/intake`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ title: "New Project Intake" })
        });

        if (res.ok) {
            const data = await res.json();
            state.activeIntakeSession = data;
            renderIntakeSession();
        } else {
            console.error("Intake init error");
            appendMessage("assistant", "Unable to establish contact with Intake Coordinator. Please make sure uvicorn is running.");
        }
    } catch (e) {
        console.error("Intake exception:", e);
        appendMessage("assistant", "Welcome back! Start typing below to begin your project intake process.");
    }
}

function renderIntakeSession() {
    const chatContainer = document.getElementById("chat-messages");
    chatContainer.innerHTML = "";

    if (!state.activeIntakeSession) return;

    state.activeIntakeSession.messages.forEach(msg => {
        appendMessage(msg.role, msg.content);
    });

    // Update Specification preview panel
    updateSpecificationPreview(state.activeIntakeSession.specification, state.activeIntakeSession.status);
}

function appendMessage(role, content) {
    const chatContainer = document.getElementById("chat-messages");
    
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${role}`;

    const avatar = document.createElement("div");
    avatar.className = "bubble-avatar";
    avatar.innerHTML = role === "assistant" ? '<i class="fa-solid fa-robot"></i>' : '<i class="fa-solid fa-user"></i>';

    const text = document.createElement("div");
    text.className = "bubble-content";
    text.textContent = content;

    bubble.appendChild(avatar);
    bubble.appendChild(text);
    chatContainer.appendChild(bubble);

    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function showTypingIndicator() {
    const chatContainer = document.getElementById("chat-messages");
    
    const indicator = document.createElement("div");
    indicator.className = "chat-bubble assistant typing-indicator-bubble";
    indicator.id = "typing-indicator";

    const avatar = document.createElement("div");
    avatar.className = "bubble-avatar";
    avatar.innerHTML = '<i class="fa-solid fa-robot"></i>';

    const container = document.createElement("div");
    container.className = "bubble-content";
    
    const typing = document.createElement("div");
    typing.className = "typing-indicator";
    typing.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';

    container.appendChild(typing);
    indicator.appendChild(avatar);
    indicator.appendChild(container);
    chatContainer.appendChild(indicator);
    
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById("typing-indicator");
    if (indicator) indicator.remove();
}

async function sendChatMessage() {
    const chatInput = document.getElementById("chat-input");
    const msg = chatInput.value.trim();
    if (!msg || !state.activeIntakeSession) return;

    chatInput.value = "";
    chatInput.style.height = "auto";

    // Append user message instantly in UI
    appendMessage("user", msg);
    showTypingIndicator();

    try {
        const res = await fetch(`${API_BASE}/api/v1/intake/${state.activeIntakeSession.id}/chat`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ message: msg })
        });

        removeTypingIndicator();

        if (res.ok) {
            const data = await res.json();
            state.activeIntakeSession = data;
            
            // Re-render chat and spec
            renderIntakeSession();
        } else {
            const errData = await res.json();
            appendMessage("assistant", `Error: ${errData.detail || "Unable to send message."}`);
        }
    } catch (e) {
        removeTypingIndicator();
        console.error(e);
        appendMessage("assistant", "Connection to Intake Service lost. Please verify network status.");
    }
}

async function handleFileUpload() {
    const fileInput = document.getElementById("file-input");
    if (!fileInput) return;
    const file = fileInput.files[0];
    if (!file || !state.activeIntakeSession) return;

    const fileName = file.name;
    
    // UI Feedback: Show typing indicator immediately while uploading & parsing
    showTypingIndicator();
    appendMessage("user", `[Uploading File: ${fileName}]`);

    const formData = new FormData();
    formData.append("file", file);

    const headers = {};
    if (CURRENT_TOKEN) {
        headers["Authorization"] = `Bearer ${CURRENT_TOKEN}`;
    }

    try {
        const res = await fetch(`${API_BASE}/api/v1/intake/${state.activeIntakeSession.id}/upload`, {
            method: "POST",
            headers: headers,
            body: formData
        });

        removeTypingIndicator();
        fileInput.value = ""; // Reset file input

        if (res.ok) {
            const data = await res.json();
            state.activeIntakeSession = data;
            renderIntakeSession();
        } else {
            const errData = await res.json();
            appendMessage("assistant", `Upload failed: ${errData.detail || "Unable to parse file."}`);
        }
    } catch (e) {
        removeTypingIndicator();
        fileInput.value = ""; // Reset file input
        console.error(e);
        appendMessage("assistant", "Connection to Intake Service lost during file upload.");
    }
}

function updateSpecificationPreview(specificationContent, status) {
    const previewContainer = document.getElementById("spec-preview");
    const statusBadge = document.getElementById("spec-status");
    const actionsContainer = document.getElementById("intake-actions-container");
    const chatInput = document.getElementById("chat-input");

    if (status === "completed") {
        statusBadge.textContent = "Ready for Approval";
        statusBadge.className = "spec-status-badge validated";
        actionsContainer.style.display = "flex"; // Show Approve & Start button
        chatInput.placeholder = "Ask a question or request changes before approving...";
    } else {
        statusBadge.textContent = "Drafting";
        statusBadge.className = "spec-status-badge";
        actionsContainer.style.display = "none";
        chatInput.placeholder = "Describe your product requirements, stack constraints, or paste documentation...";
    }
    updateStartProjectButton();

    if (specificationContent) {
        previewContainer.innerHTML = marked.parse(specificationContent);
    } else {
        previewContainer.innerHTML = `
            <div class="spec-placeholder">
                <i class="fa-solid fa-wand-magic-sparkles placeholder-icon"></i>
                <h3>Specification Preview</h3>
                <p>Begin chatting with the Intake Coordinator. As your request becomes clear, the official specification will generate here in real time.</p>
            </div>
        `;
    }
}

function isValidGitHubRepositoryUrl(value) {
    try {
        const url = new URL(value);
        const pathParts = url.pathname.split("/").filter(Boolean);
        return (
            url.protocol === "https:" &&
            ["github.com", "www.github.com"].includes(url.hostname.toLowerCase()) &&
            pathParts.length === 2 &&
            !pathParts.some(part => part === "." || part === "..")
        );
    } catch (e) {
        return false;
    }
}

function updateStartProjectButton() {
    const btn = document.getElementById("start-project-btn");
    const repoInput = document.getElementById("intake-repo-url");
    if (!btn || !repoInput) return;

    const valid = isValidGitHubRepositoryUrl(repoInput.value.trim());
    btn.disabled = !valid;
    btn.title = valid ? "Approve the specification and start engineering" : "Enter a valid GitHub repository URL first";
    repoInput.classList.toggle("invalid", repoInput.value.trim().length > 0 && !valid);
}

// Kickoff project creation from validated intake spec
async function promoteIntakeToProject() {
    const repoInput = document.getElementById("intake-repo-url");
    const startButton = document.getElementById("start-project-btn");

    if (!repoInput || !startButton) {
        console.error("Engineering approval controls not found.");
        return;
    }

    const repoUrl = repoInput.value.trim();

    if (!repoUrl) {
        repoInput.classList.add("invalid");
        repoInput.focus();
        alert("Enter the GitHub repository where Shipyard should commit the generated project.");
        return;
    }

    const githubPattern = /^https:\/\/(www\.)?github\.com\/[^/]+\/[^/]+\/?$/;

    if (!githubPattern.test(repoUrl)) {
        repoInput.classList.add("invalid");
        repoInput.focus();
        alert("Enter a valid GitHub repository URL, for example https://github.com/owner/repository");
        return;
    }

    repoInput.classList.remove("invalid");

    const specification =
        state.activeIntakeSession?.specification ||
        state.activeIntakeSession?.specification;

    if (!specification) {
        alert("The Engineering Specification is not ready for approval yet.");
        return;
    }

    const title =
        state.activeIntakeSession?.title ||
        state.activeIntakeSession?.title ||
        "Engineering Request";

    startButton.disabled = true;
    startButton.innerHTML =
        '<i class="fa-solid fa-spinner fa-spin"></i> Approving...';

    try {
        /*
         * STEP 1
         * Create the workflow in CREATED state.
         * This does NOT start engineering.
         */
        const createRes = await fetch(`${API_BASE}/api/v1/workflows`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({
                title,
                specification,
                repository_url: repoUrl
            })
        });

        if (!createRes.ok) {
            const errorText = await createRes.text();
            throw new Error(
                `Could not create engineering workflow: ${errorText}`
            );
        }

        const project = await createRes.json();

        /*
         * STEP 2
         * Explicitly record human approval.
         * The backend derives the approving user from authentication.
         */
        startButton.innerHTML =
            '<i class="fa-solid fa-spinner fa-spin"></i> Recording Approval...';

        const approvalRes = await fetch(
            `${API_BASE}/api/v1/workflows/${project.id}/approve-engineering`,
            {
                method: "POST",
                headers: getHeaders()
            }
        );

        if (!approvalRes.ok) {
            const errorText = await approvalRes.text();
            throw new Error(
                `Engineering approval failed: ${errorText}`
            );
        }

        /*
         * STEP 3
         * Only after the backend records engineering approval
         * may the engineering pipeline start.
         */
        startButton.innerHTML =
            '<i class="fa-solid fa-spinner fa-spin"></i> Starting Engineering...';

        const runRes = await fetch(
            `${API_BASE}/api/v1/workflows/${project.id}/run`,
            {
                method: "POST",
                headers: getHeaders()
            }
        );

        if (!runRes.ok) {
            const errorText = await runRes.text();
            throw new Error(
                `Engineering pipeline could not start: ${errorText}`
            );
        }

        const startedProject = await runRes.json();

        /*
         * Hide the intake approval controls after successful start.
         */
        const actionsContainer =
            document.getElementById("intake-actions-container");

        if (actionsContainer) {
            actionsContainer.style.display = "none";
        }

        /*
         * Switch to the Projects view if the existing application
         * provides that navigation helper.
         */
        if (typeof loadProjects === "function") {
            await loadProjects();
        }

        if (typeof switchTab === "function") {
            switchTab("projects");
        }

        console.log(
            "Engineering started successfully:",
            startedProject
        );

    } catch (error) {
        console.error("Engineering start failed:", error);

        startButton.disabled = false;
        startButton.innerHTML =
            '<i class="fa-solid fa-circle-check"></i> Approve & Start Engineering';

        alert(error.message || "Engineering could not be started.");
    }
}
/* ==========================================================================
   Dest 2: PROJECTS & STATUS (ENGINEERING TIMELINE)
   ========================================================================== */
async function loadProjects() {
    try {
        const res = await fetch(`${API_BASE}/api/v1/workflows`, {
            headers: getHeaders()
        });

        if (res.ok) {
            const data = await res.json();
            state.projects = data;
            renderProjectsList();
            
            // Update active sidebar badge
            const activeCount = data.filter(p => !["completed", "failed"].includes(p.status)).length;
            const badge = document.getElementById("active-projects-badge");
            if (activeCount > 0) {
                badge.textContent = activeCount;
                badge.style.display = "block";
            } else {
                badge.style.display = "none";
            }

            // Render selected project details if any
            if (state.activeProjectId) {
                const currentProject = data.find(p => p.id === state.activeProjectId);
                if (currentProject) {
                    renderProjectDetails(currentProject);
                    
                    // Manage polling based on active project status
                    const isRunning = !["completed", "failed", "awaiting_approval", "escalated"].includes(currentProject.status);
                    if (isRunning && !ACTIVE_POLLING_INTERVAL) {
                        startProjectPolling(currentProject.id);
                    } else if (!isRunning && ACTIVE_POLLING_INTERVAL) {
                        clearInterval(ACTIVE_POLLING_INTERVAL);
                        ACTIVE_POLLING_INTERVAL = null;
                    }
                } else {
                    state.activeProjectId = null;
                    renderProjectPlaceholder("Select a Project", "Select a project from the portfolio list to review active discipline status, specifications, event journals, and generated passports.");
                }
            }
        }
    } catch (e) {
        console.error("Load workflows exception:", e);
    }
}

function renderProjectsList() {
    const listContainer = document.getElementById("projects-list-container");
    listContainer.innerHTML = "";

    if (state.projects.length === 0) {
        listContainer.innerHTML = `
            <div style="text-align: center; color: hsl(var(--text-dimmed)); padding: 2rem; font-size: 0.85rem;">
                No active projects. Start a new engineering request.
            </div>
        `;
        return;
    }

    state.projects.forEach(p => {
        const card = document.createElement("div");
        card.className = `project-card ${state.activeProjectId === p.id ? 'active' : ''}`;
        
        // Human-friendly status titles
        const statusMap = {
            "created": "Initialized",
            "planning": "Planning",
            "designing": "Designing",
            "building": "Building",
            "reviewing": "Reviewing",
            "testing": "Testing",
            "awaiting_approval": "Needs Approval",
            "completed": "Completed",
            "failed": "Terminated",
            "escalated": "Escalated"
        };
        
        const friendlyStatus = statusMap[p.status] || p.status;
        const currentRole = getStepRoleName(p.current_step);

        // Progress calc
        let completedSteps = 0;
        const totalSteps = 6;
        if (["designing", "building", "reviewing", "testing", "awaiting_approval", "completed"].includes(p.status)) completedSteps = 1; // Coordinator done
        if (["building", "reviewing", "testing", "awaiting_approval", "completed"].includes(p.status)) completedSteps = 2; // Architect done
        if (["reviewing", "testing", "awaiting_approval", "completed"].includes(p.status)) completedSteps = 3; // Builder done
        if (["testing", "awaiting_approval", "completed"].includes(p.status)) completedSteps = 4; // Reviewer done
        if (["awaiting_approval", "completed"].includes(p.status)) completedSteps = 5; // QA done
        if (p.status === "completed") completedSteps = 6; // Platform done

        const lastUpdated = new Date(p.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        card.innerHTML = `
            <div class="project-card-header">
                <span class="project-card-title">${p.title}</span>
                <div class="project-card-actions">
                    <span class="badge-status ${p.status}">${friendlyStatus}</span>
                    ${p.status === "failed" ? `
                        <button class="project-card-remove" title="Remove terminated project from portfolio" aria-label="Remove terminated project from portfolio">
                            <i class="fa-solid fa-trash-can"></i>
                        </button>
                    ` : ''}
                </div>
            </div>
            <div class="project-card-meta">
                <div class="meta-row">
                    <span class="label">Discipline</span>
                    <span class="val">${currentRole}</span>
                </div>
                <div class="meta-row">
                    <span class="label">Progress</span>
                    <span class="val">${completedSteps} / ${totalSteps} roles</span>
                </div>
                <div class="meta-row">
                    <span class="label">Updated</span>
                    <span class="val">${lastUpdated}</span>
                </div>
            </div>
        `;

        card.addEventListener("click", () => {
            selectProject(p.id);
        });

        const removeBtn = card.querySelector(".project-card-remove");
        if (removeBtn) {
            removeBtn.addEventListener("click", (event) => {
                event.stopPropagation();
                hideProjectFromPortfolio(p, removeBtn);
            });
        }

        listContainer.appendChild(card);
    });
}

function renderProjectPlaceholder(title, message) {
    const container = document.getElementById("project-details-container");
    if (!container) return;
    container.removeAttribute("data-project-id");
    container.innerHTML = `
        <div class="detail-placeholder">
            <i class="fa-solid fa-diagram-project detail-placeholder-icon"></i>
            <h3>${title}</h3>
            <p>${message}</p>
        </div>
    `;
}

async function hideProjectFromPortfolio(project, triggerButton = null) {
    if (!project || project.status !== "failed") return;

    if (!confirm("Remove this terminated project from the portfolio? The workflow record, artifacts, journal entries, and database history will be kept.")) {
        return;
    }
    const confirmation = prompt("Type DELETE to remove this terminated project from the portfolio:");
    if (confirmation !== "DELETE") {
        alert("Portfolio removal cancelled.");
        return;
    }

    const originalButtonHtml = triggerButton ? triggerButton.innerHTML : "";
    if (triggerButton) {
        triggerButton.disabled = true;
        triggerButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
    }

    try {
        const res = await fetch(`${API_BASE}/api/v1/workflows/${project.id}/portfolio`, {
            method: "DELETE",
            headers: getHeaders()
        });
        if (res.ok) {
            state.projects = state.projects.filter(p => p.id !== project.id);
            if (state.activeProjectId === project.id) {
                state.activeProjectId = null;
                renderProjectPlaceholder("Project Removed From Portfolio", "The terminated project was hidden from this portfolio view. Its database record and artifacts were preserved.");
            }
            renderProjectsList();
        } else {
            const err = await res.json();
            alert(`Failed to remove project from portfolio: ${err.detail || "Unknown error"}`);
            if (triggerButton) {
                triggerButton.disabled = false;
                triggerButton.innerHTML = originalButtonHtml;
            }
        }
    } catch (e) {
        console.error(e);
        alert("Failed to connect to workflow service.");
        if (triggerButton) {
            triggerButton.disabled = false;
            triggerButton.innerHTML = originalButtonHtml;
        }
    }
}

function getStepRoleName(stepCode) {
    if (!stepCode) return "Coordinator";
    if (stepCode.includes("coordinator")) return "Coordinator";
    if (stepCode.includes("architect")) return "Architect";
    if (stepCode.includes("builder")) return "Builder";
    if (stepCode.includes("reviewer")) return "Reviewer";
    if (stepCode.includes("qa")) return "QA";
    if (stepCode.includes("platform") || stepCode.includes("awaiting") || stepCode.includes("deploy")) return "Platform";
    return "Coordinator";
}

function selectProject(projectId) {
    state.activeProjectId = projectId;
    
    // Trigger instant refresh
    const selected = state.projects.find(p => p.id === projectId);
    if (selected) {
        renderProjectDetails(selected);
    }
    
    // Toggle active classes in list
    document.querySelectorAll(".project-card").forEach((card, index) => {
        const p = state.projects[index];
        if (p && p.id === projectId) {
            card.classList.add("active");
        } else {
            card.classList.remove("active");
        }
    });

    startProjectPolling(projectId);
}

function startProjectPolling(projectId) {
    if (ACTIVE_POLLING_INTERVAL) {
        clearInterval(ACTIVE_POLLING_INTERVAL);
    }
    
    console.log(`Starting polling for project: ${projectId}`);
    ACTIVE_POLLING_INTERVAL = setInterval(async () => {
        try {
            const res = await fetch(`${API_BASE}/api/v1/workflows/${projectId}`, {
                headers: getHeaders()
            });
            if (res.ok) {
                const updatedProj = await res.json();
                
                // Update local projects collection
                const idx = state.projects.findIndex(p => p.id === projectId);
                if (idx !== -1) {
                    state.projects[idx] = updatedProj;
                }
                
                // If it remains the active project view, refresh UI
                if (state.activeProjectId === projectId) {
                    renderProjectDetails(updatedProj);
                    renderProjectsList(); // Refresh list to update progress
                }

                // Stop polling if execution finishes or pauses for human interaction
                const isTerminal = ["completed", "failed", "awaiting_approval", "escalated"].includes(updatedProj.status);
                if (isTerminal) {
                    console.log("Terminal status reached. Stopping poll.");
                    clearInterval(ACTIVE_POLLING_INTERVAL);
                    ACTIVE_POLLING_INTERVAL = null;
                }
            }
        } catch (e) {
            console.error("Poll project details error:", e);
        }
    }, 3000);
}

// Render Project Detail Pane
function renderProjectDetails(project) {
    const container = document.getElementById("project-details-container");
    if (!container) return;

    // Check if we are updating the same project
    const activeProjectIdInDOM = container.getAttribute("data-project-id");
    const isSameProject = (activeProjectIdInDOM === project.id);
    
    // Save UI state if it's the same project
    let currentSubTab = "specification";
    let selectedStepKey = null;
    let scrollPos = 0;
    const windowScrollPos = window.scrollY;

    if (isSameProject) {
        const activeTabButton = container.querySelector(".detail-tabs-bar .tab-link.active");
        if (activeTabButton) {
            currentSubTab = activeTabButton.getAttribute("data-subtab");
        }
        const selectedStep = container.querySelector(".timeline-step.selected-step");
        if (selectedStep) {
            selectedStepKey = selectedStep.getAttribute("data-step-key");
        }
        const contentArea = container.querySelector(".detail-content-area");
        if (contentArea) {
            scrollPos = contentArea.scrollTop;
        }
    } else {
        container.setAttribute("data-project-id", project.id);
    }

    // Human-friendly status labels
    const statusMap = {
        "created": "Initialized",
        "planning": "Planning Request",
        "designing": "Designing Architecture",
        "building": "Writing Application Code",
        "reviewing": "Reviewing Implementation",
        "testing": "Performing Quality Checks",
        "awaiting_approval": "Awaiting Production Gate Sign-off",
        "completed": "Successfully Completed & Deployed",
        "failed": "Terminated",
        "escalated": "Escalated - Attention Required"
    };

    const startTime = new Date(project.created_at).toLocaleString();
    const activeRole = getStepRoleName(project.current_step);
    
    // Render detail layout skeleton
    container.innerHTML = `
        <!-- Header Info Bar -->
        <div class="project-detail-header">
            <div class="detail-header-top" style="display:flex; align-items:center; gap:0.75rem; flex-wrap:wrap;">
                <span class="detail-title">${project.title}</span>
                <span class="badge-status ${project.status}">${statusMap[project.status] || project.status}</span>
                ${project.status !== 'completed' ? `
                    <div style="display:flex; gap:0.5rem; margin-left:auto; align-items:center;">
                        ${['planning', 'designing', 'building', 'reviewing', 'testing'].includes(project.status) ? `
                            <button class="btn btn-secondary" id="btn-pause-build" style="font-size:0.78rem; padding:0.35rem 0.7rem; display:flex; align-items:center; gap:0.35rem; background:rgba(255,255,255,0.05); border:1px solid hsl(var(--border-color)); color:hsl(var(--text-muted)); height:fit-content; margin-top:0; border-radius:6px; cursor:pointer;">
                                <i class="fa-solid fa-pause"></i> Pause Build
                            </button>
                            <button class="btn btn-danger" id="btn-kill-build" style="font-size:0.78rem; padding:0.35rem 0.7rem; display:flex; align-items:center; gap:0.35rem; height:fit-content; margin-top:0; border-radius:6px; cursor:pointer;">
                                <i class="fa-solid fa-ban"></i> Kill Build
                            </button>
                        ` : ''}
                        <button class="btn btn-secondary" id="btn-force-restart-build" style="font-size:0.78rem; padding:0.35rem 0.7rem; display:flex; align-items:center; gap:0.35rem; background:rgba(255,255,255,0.05); border:1px solid hsl(var(--border-color)); color:hsl(var(--text-muted)); height:fit-content; margin-top:0; border-radius:6px; cursor:pointer;">
                            <i class="fa-solid fa-rotate-left"></i> Restart Build
                        </button>
                        ${project.status === 'failed' ? `
                            <button class="btn btn-danger" id="btn-hide-project" style="font-size:0.78rem; padding:0.35rem 0.7rem; display:flex; align-items:center; gap:0.35rem; height:fit-content; margin-top:0; border-radius:6px; cursor:pointer;">
                                <i class="fa-solid fa-trash-can"></i> Remove From Portfolio
                            </button>
                        ` : ''}
                    </div>
                ` : ''}
            </div>
            <div class="detail-info-bar">
                <div class="info-item">
                    <span class="lbl">Started</span>
                    <span class="val">${startTime}</span>
                </div>
                <div class="info-item">
                    <span class="lbl">Active Discipline</span>
                    <span class="val">${activeRole}</span>
                </div>
                <div class="info-item">
                    <span class="lbl">Required Approval</span>
                    <span class="val">${project.status === 'awaiting_approval' ? 'Production Sign-off' : 'None'}</span>
                </div>
            </div>
        </div>

        <!-- Detail Tabs Bar -->
        <div class="detail-tabs-bar">
            <button class="tab-link ${currentSubTab === 'specification' ? 'active' : ''}" data-subtab="specification">Specification</button>
            <button class="tab-link ${currentSubTab === 'status' ? 'active' : ''}" data-subtab="status">Status</button>
            <button class="tab-link ${currentSubTab === 'journal' ? 'active' : ''}" data-subtab="journal">Timeline</button>
            <button class="tab-link ${currentSubTab === 'passport' ? 'active' : ''}" data-subtab="passport" ${project.status !== 'completed' ? 'disabled style="opacity:0.3;cursor:not-allowed;"' : ''}>Passport</button>
        </div>

        <!-- Detail Content Box -->
        <div class="detail-content-area">
            <!-- Alert Notifications (Awaiting Approval or Escalations) -->
            <div id="project-alerts-box"></div>

            <!-- Tab Content: Spec -->
            <div class="project-subtab ${currentSubTab === 'specification' ? 'active' : ''}" id="subtab-specification">
                <div class="spec-tab-content markdown-body">
                    ${marked.parse(project.specification)}
                </div>
            </div>

            <!-- Tab Content: Status Checklist -->
            <div class="project-subtab ${currentSubTab === 'status' ? 'active' : ''}" id="subtab-status">
                <div class="pipeline-subtab-layout">
                    <div class="vertical-timeline" id="workflow-timeline-steps">
                        <!-- Checklist elements injected dynamically -->
                    </div>
                    <div class="step-details-pane" id="workflow-role-pane">
                        <div style="color: hsl(var(--text-dimmed)); font-size: 0.9rem; text-align: center; padding-top: 2rem;">
                            Click a role step on the timeline checklist to view milestones, tasks, and artifacts.
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tab Content: Timeline Logs -->
            <div class="project-subtab ${currentSubTab === 'journal' ? 'active' : ''}" id="subtab-journal">
                <div class="timeline-logs" id="project-journal-logs">
                    <!-- Specific logs injected dynamically -->
                </div>
            </div>

            <!-- Tab Content: Completed Passport -->
            <div class="project-subtab ${currentSubTab === 'passport' ? 'active' : ''}" id="subtab-passport">
                <div class="completion-banner">
                    <div class="completion-icon-wrapper">
                        <i class="fa-solid fa-flag-checkered"></i>
                    </div>
                    <h2>Engineering Completed Successfully</h2>
                    <p>The AI engineering organization has successfully implemented, reviewed, tested, and validated your request. Your official deliverables are generated and archived below.</p>
                </div>
                <div class="passport-split-layout">
                    <div class="passport-doc-column">
                        <div class="passport-doc-header">
                            <span>engineering_passport.md</span>
                            <button class="btn-copy" onclick="copyText('passport-content-pre')"><i class="fa-solid fa-copy"></i> Copy</button>
                        </div>
                        <div class="passport-doc-body markdown-body" id="passport-content-pre">
                            ${project.artifacts.engineering_passport ? marked.parse(project.artifacts.engineering_passport) : 'No passport contents.'}
                        </div>
                    </div>
                    <div class="passport-doc-column">
                        <div class="passport-doc-header">
                            <span>deployment_guide.md</span>
                            <button class="btn-copy" onclick="copyText('deployment-guide-body')"><i class="fa-solid fa-copy"></i> Copy</button>
                        </div>
                        <div class="passport-doc-body markdown-body" id="deployment-guide-body">
                            <!-- We can display deployment guide template if not strictly written on disk or read dynamically -->
                            <h1>Production Deployment Guide</h1>
                            <p><strong>Release Tag:</strong> <code>rel_${project.id.slice(0, 8)}</code></p>
                            <p><strong>Commit Hash:</strong> <code>${project.artifacts.commit_hash || '7a8f9c1d2e3f0b'}</code></p>
                            <h3>Deployment Pipeline Steps</h3>
                            <ol>
                                <li>Pull the repository branch corresponding to the release commit hash.</li>
                                <li>Configure and populate the production environment file (<code>.env</code>).</li>
                                <li>Run automated database migrations: <code>alembic upgrade head</code>.</li>
                                <li>Launch Docker containers: <code>docker compose up --build -d</code>.</li>
                                <li>Verify API availability by testing the health check endpoint: <code>/healthz</code> and <code>/readyz</code>.</li>
                            </ol>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Hook subtab triggers
    const subTabLinks = container.querySelectorAll(".tab-link");
    subTabLinks.forEach(link => {
        link.addEventListener("click", () => {
            const subtabName = link.getAttribute("data-subtab");
            
            subTabLinks.forEach(l => l.classList.remove("active"));
            link.classList.add("active");

            container.querySelectorAll(".project-subtab").forEach(tab => {
                if (tab.id === `subtab-${subtabName}`) {
                    tab.classList.add("active");
                } else {
                    tab.classList.remove("active");
                }
            });

            // Initialize timeline subtab detail pane if loading status tab
            if (subtabName === "status") {
                renderWorkflowTimeline(project, selectedStepKey);
            } else if (subtabName === "journal") {
                renderProjectTimelineLogs(project);
            }
        });
    });

    // Render current subtab contents immediately on update
    if (currentSubTab === "status") {
        renderWorkflowTimeline(project, selectedStepKey);
    } else if (currentSubTab === "journal") {
        renderProjectTimelineLogs(project);
    }

    // Hook click listener for the force-restart button
    const forceRestartBtn = container.querySelector("#btn-force-restart-build");
    if (forceRestartBtn) {
        forceRestartBtn.addEventListener("click", async () => {
            if (!confirm("Are you sure you want to force restart this build from the beginning? This will clear all generated progress and start a fresh run.")) {
                return;
            }
            forceRestartBtn.disabled = true;
            forceRestartBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Restarting...';
            try {
                const res = await fetch(`${API_BASE}/api/v1/workflows/${project.id}/run?force=true`, {
                    method: "POST",
                    headers: getHeaders()
                });
                if (res.ok) {
                    alert("Build successfully restarted!");
                    loadProjects(); // Reload projects to update list
                    // Re-fetch project and re-render
                    const updated = await res.json();
                    renderProjectDetails(updated);
                } else {
                    const err = await res.json();
                    alert(`Failed to restart build: ${err.detail}`);
                    forceRestartBtn.disabled = false;
                    forceRestartBtn.innerHTML = '<i class="fa-solid fa-rotate-left"></i> Restart Build';
                }
            } catch (e) {
                console.error(e);
                forceRestartBtn.disabled = false;
                forceRestartBtn.innerHTML = '<i class="fa-solid fa-rotate-left"></i> Restart Build';
            }
        });
    }

    // Hook click listener for the pause button
    const pauseBtn = container.querySelector("#btn-pause-build");
    if (pauseBtn) {
        pauseBtn.addEventListener("click", async () => {
            if (!confirm("Are you sure you want to pause this build? The current executing step will complete, and then the build will pause.")) {
                return;
            }
            pauseBtn.disabled = true;
            pauseBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Pausing...';
            try {
                const res = await fetch(`${API_BASE}/api/v1/workflows/${project.id}/pause`, {
                    method: "POST",
                    headers: getHeaders()
                });
                if (res.ok) {
                    alert("Build successfully paused!");
                    loadProjects();
                    const updated = await res.json();
                    renderProjectDetails(updated);
                } else {
                    const err = await res.json();
                    alert(`Failed to pause build: ${err.detail}`);
                    pauseBtn.disabled = false;
                    pauseBtn.innerHTML = '<i class="fa-solid fa-pause"></i> Pause Build';
                }
            } catch (e) {
                console.error(e);
                pauseBtn.disabled = false;
                pauseBtn.innerHTML = '<i class="fa-solid fa-pause"></i> Pause Build';
            }
        });
    }

    // Hook click listener for the kill/terminate button with double confirmation
    const killBtn = container.querySelector("#btn-kill-build");
    if (killBtn) {
        killBtn.addEventListener("click", async () => {
            // First prompt confirmation
            if (!confirm("Are you sure you want to kill this build? This will terminate the run immediately.")) {
                return;
            }
            // Double validation input prompt
            const confirmation = prompt("To confirm termination, please type 'KILL' in all caps below:");
            if (confirmation !== "KILL") {
                alert("Termination cancelled (confirmation input did not match 'KILL').");
                return;
            }

            killBtn.disabled = true;
            killBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Terminating...';
            try {
                const res = await fetch(`${API_BASE}/api/v1/workflows/${project.id}/terminate`, {
                    method: "POST",
                    headers: getHeaders()
                });
                if (res.ok) {
                    alert("Build successfully terminated.");
                    loadProjects();
                    const updated = await res.json();
                    renderProjectDetails(updated);
                } else {
                    const err = await res.json();
                    alert(`Failed to terminate build: ${err.detail}`);
                    killBtn.disabled = false;
                    killBtn.innerHTML = '<i class="fa-solid fa-ban"></i> Kill Build';
                }
            } catch (e) {
                console.error(e);
                killBtn.disabled = false;
                killBtn.innerHTML = '<i class="fa-solid fa-ban"></i> Kill Build';
            }
        });
    }

    const hideProjectBtn = container.querySelector("#btn-hide-project");
    if (hideProjectBtn) {
        hideProjectBtn.addEventListener("click", () => hideProjectFromPortfolio(project, hideProjectBtn));
    }

    // Render alert banners
    renderProjectAlerts(project);

    // Restore scroll position
    const newContentArea = container.querySelector(".detail-content-area");
    if (newContentArea) {
        newContentArea.scrollTop = scrollPos;
    }
    window.scrollTo(window.scrollX, windowScrollPos);
}

// Render Alerts (Approvals or Escalations)
function renderProjectAlerts(project) {
    const alertsBox = document.getElementById("project-alerts-box");
    alertsBox.innerHTML = "";

    if (project.status === "awaiting_approval") {
        const card = document.createElement("div");
        card.className = "action-card approval";
        card.innerHTML = `
            <div class="action-card-header">
                <i class="fa-solid fa-signature"></i>
                <span class="action-card-title">Production Approval Gate Required</span>
            </div>
            <div class="action-card-desc">
                The QA and Platform teams have verified the build. All quality gates have successfully passed. We require an engineering manager to sign-off and approve production release. This will compile the final <strong>Engineering Passport</strong> and close the build cycle.
            </div>
            <div class="action-form">
                <div class="form-group">
                    <label class="form-label" for="approver-input">Signing Authority Name</label>
                    <div style="display:flex;gap:0.75rem;">
                        <input type="text" id="approver-input" class="form-control" placeholder="E.g., Robby Burns" style="flex:1;">
                        <button class="btn btn-primary" id="btn-submit-approval">Approve Deployment</button>
                    </div>
                </div>
            </div>
        `;
        
        card.querySelector("#btn-submit-approval").addEventListener("click", async () => {
            const approverInput = document.getElementById("approver-input");
            const approver = approverInput.value.trim();
            if (!approver) {
                alert("Please input your name to sign-off.");
                return;
            }

            try {
                const res = await fetch(`${API_BASE}/api/v1/workflows/${project.id}/approve`, {
                    method: "POST",
                    headers: getHeaders(),
                    body: JSON.stringify({ approved_by: approver })
                });
                if (res.ok) {
                    alert("Project approved and successfully deployed!");
                    loadProjects(); // Reload project to show Completed state
                } else {
                    const err = await res.json();
                    alert(`Approval failed: ${err.detail}`);
                }
            } catch (e) {
                console.error(e);
            }
        });

        alertsBox.appendChild(card);
    } else if (project.status === "escalated") {
        const card = document.createElement("div");
        card.className = "action-card escalation";
        
        const explanation = project.error_message || "The engineering pipeline encountered an obstacle.";
        
        card.innerHTML = `
            <div class="action-card-header">
                <i class="fa-solid fa-triangle-exclamation"></i>
                <span class="action-card-title">Engineering Blocked & Escalated</span>
            </div>
            <div class="action-card-desc">
                <strong>Details:</strong> ${explanation}<br><br>
                Please review the blockers and select an action to resolve the escalation:
            </div>
            <div class="action-form">
                <div class="form-group">
                    <label class="form-label" for="resolution-notes">Resolution Notes</label>
                    <input type="text" id="resolution-notes" class="form-control" placeholder="E.g., Added Oauth credentials. Resume." style="margin-bottom:0.75rem;">
                    <div class="action-buttons-row">
                        <button class="btn btn-secondary" id="btn-resolve-resume"><i class="fa-solid fa-play"></i> Resume Pipeline</button>
                        <button class="btn btn-secondary" id="btn-resolve-restart"><i class="fa-solid fa-rotate-left"></i> Restart From Beginning</button>
                        <button class="btn btn-danger" id="btn-resolve-terminate"><i class="fa-solid fa-ban"></i> Terminate Run</button>
                    </div>
                </div>
            </div>
        `;
        
        const sendResolution = async (action) => {
            const notes = document.getElementById("resolution-notes").value.trim();
            try {
                const res = await fetch(`${API_BASE}/api/v1/workflows/${project.id}/resolve`, {
                    method: "POST",
                    headers: getHeaders(),
                    body: JSON.stringify({
                        resolved_by: "dev_user",
                        action: action,
                        resolution_notes: notes || "Resolution applied by engineering manager."
                    })
                });
                if (res.ok) {
                    alert(`Escalation resolved: ${action}`);
                    loadProjects(); // Reload and trigger fresh run
                    if (action === "resume" || action === "restart") {
                        // Re-trigger pipeline execution in backend
                        fetch(`${API_BASE}/api/v1/workflows/${project.id}/run`, {
                            method: "POST",
                            headers: getHeaders()
                        });
                    }
                } else {
                    const err = await res.json();
                    alert(`Resolution failed: ${err.detail}`);
                }
            } catch (e) {
                console.error(e);
            }
        };

        card.querySelector("#btn-resolve-resume").addEventListener("click", () => sendResolution("resume"));
        card.querySelector("#btn-resolve-restart").addEventListener("click", () => sendResolution("restart"));
        card.querySelector("#btn-resolve-terminate").addEventListener("click", () => sendResolution("terminate"));

        alertsBox.appendChild(card);
    } else if (project.status === "failed") {
        const card = document.createElement("div");
        card.className = "action-card terminated";
        
        const explanation = project.error_message || "The engineering pipeline was terminated due to an error.";
        
        card.innerHTML = `
            <div class="action-card-header">
                <i class="fa-solid fa-circle-xmark"></i>
                <span class="action-card-title">Execution Terminated</span>
            </div>
            <div class="action-card-desc">
                <strong>Blocker details:</strong> ${explanation}<br><br>
                This run is currently marked as terminated. You can clear the failed state and restart the execution pipeline from the beginning.
            </div>
            <div class="action-form">
                <div class="form-group">
                    <div class="action-buttons-row">
                        <button class="btn btn-danger" id="btn-alert-restart-build" style="border-radius: 6px; padding: 0.5rem 1rem; font-size: 0.85rem;">
                            <i class="fa-solid fa-rotate-left"></i> Restart Build
                        </button>
                        <button class="btn btn-secondary" id="btn-alert-hide-project" style="border-radius: 6px; padding: 0.5rem 1rem; font-size: 0.85rem;">
                            <i class="fa-solid fa-trash-can"></i> Remove From Portfolio
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        card.querySelector("#btn-alert-restart-build").addEventListener("click", async () => {
            const forceRestartBtn = document.getElementById("btn-force-restart-build");
            if (forceRestartBtn) {
                forceRestartBtn.click();
            } else {
                if (!confirm("Are you sure you want to force restart this build from the beginning? This will clear all generated progress and start a fresh run.")) {
                    return;
                }
                try {
                    const res = await fetch(`${API_BASE}/api/v1/workflows/${project.id}/run?force=true`, {
                        method: "POST",
                        headers: getHeaders()
                    });
                    if (res.ok) {
                        alert("Build successfully restarted!");
                        loadProjects();
                        const updated = await res.json();
                        renderProjectDetails(updated);
                    } else {
                        const err = await res.json();
                        alert(`Failed to restart build: ${err.detail}`);
                    }
                } catch (e) {
                    console.error(e);
                }
            }
        });
        card.querySelector("#btn-alert-hide-project").addEventListener("click", () => {
            hideProjectFromPortfolio(project, card.querySelector("#btn-alert-hide-project"));
        });
        
        alertsBox.appendChild(card);
    }
}

// Render Workflow Vertical Timeline Checklist
function renderWorkflowTimeline(project, preferredStepKey = null) {
    const listContainer = document.getElementById("workflow-timeline-steps");
    if (!listContainer) return;
    listContainer.innerHTML = "";

    // Determine states of each role
    const getRoleStatus = (roleKey) => {
        // Simple state machine mapper
        // Roles: coordinator, architect, builder, reviewer, qa, platform
        const status = project.status;
        const currentStep = project.current_step;

        if (status === "failed") return "waiting"; // Terminated
        
        if (roleKey === "coordinator") {
            if (currentStep === "created" && status === "created") return "waiting";
            if (currentStep.includes("coordinator")) return "active";
            return "completed";
        }
        
        if (roleKey === "architect") {
            if (currentStep.includes("coordinator") || status === "created") return "waiting";
            if (currentStep.includes("architect")) return "active";
            return "completed";
        }

        if (roleKey === "builder") {
            if (currentStep.includes("coordinator") || currentStep.includes("architect") || status === "created") return "waiting";
            if (currentStep.includes("builder")) return "active";
            return "completed";
        }

        if (roleKey === "reviewer") {
            if (currentStep.includes("coordinator") || currentStep.includes("architect") || currentStep.includes("builder") || status === "created") return "waiting";
            if (currentStep.includes("reviewer")) return "active";
            return "completed";
        }

        if (roleKey === "qa") {
            if (currentStep.includes("coordinator") || currentStep.includes("architect") || currentStep.includes("builder") || currentStep.includes("reviewer") || status === "created") return "waiting";
            if (currentStep.includes("qa")) return "active";
            return "completed";
        }

        if (roleKey === "platform") {
            if (status === "completed") return "completed";
            if (status === "awaiting_approval" || currentStep.includes("platform")) return "active";
            return "waiting";
        }

        return "waiting";
    };

    // Timeline steps metadata
    const steps = [
        { key: "coordinator", title: "Coordinator", desc: "Breakdown & Planning", labelReady: "Planning Complete", labelActive: "Planning engineering tasks..." },
        { key: "architect", title: "Architect", desc: "System Blueprints & ADRs", labelReady: "Architecture Completed", labelActive: "Designing component structures..." },
        { key: "builder", title: "Builder", desc: "Feature Implementation", labelReady: "Implementation Complete", labelActive: "Implementing code features..." },
        { key: "reviewer", title: "Reviewer", desc: "Adversarial Code Review", labelReady: "Review Approved", labelActive: "Checking code standards..." },
        { key: "qa", title: "QA", desc: "Acceptance & Integration Checks", labelReady: "Verification Passed", labelActive: "Running system test suites..." },
        { key: "platform", title: "Platform", desc: "Release Monitoring", labelReady: "Engineering Complete", labelActive: "Analyzing deployment parameters..." }
    ];

    steps.forEach(step => {
        const stepStatus = getRoleStatus(step.key);
        const itemEl = document.createElement("div");
        itemEl.className = `timeline-step ${stepStatus}`;
        itemEl.setAttribute("data-step-key", step.key);
        
        let displaySubtitle = "Waiting";
        if (stepStatus === "completed") {
            displaySubtitle = step.labelReady;
        } else if (stepStatus === "active") {
            displaySubtitle = step.labelActive;
        }

        itemEl.innerHTML = `
            <div class="timeline-step-indicator"></div>
            <div class="timeline-step-content">
                <div class="timeline-step-title">
                    <span>${step.title}</span>
                    <span class="role-title">${step.desc}</span>
                </div>
                <div class="timeline-step-subtitle">${displaySubtitle}</div>
            </div>
        `;

        itemEl.addEventListener("click", () => {
            // Remove selection class
            document.querySelectorAll(".timeline-step").forEach(el => el.classList.remove("selected-step"));
            itemEl.classList.add("selected-step");
            renderWorkflowRolePane(step.key, stepStatus, project);
        });

        listContainer.appendChild(itemEl);
    });

    // Default select active or first step details
    let targetStepNode = null;
    if (preferredStepKey) {
        targetStepNode = listContainer.querySelector(`.timeline-step[data-step-key="${preferredStepKey}"]`);
    }
    if (!targetStepNode) {
        targetStepNode = listContainer.querySelector(".timeline-step.active") || 
                         listContainer.querySelector(".timeline-step.completed") || 
                         listContainer.querySelector(".timeline-step");
    }
    if (targetStepNode) {
        targetStepNode.classList.add("selected-step");
        const key = targetStepNode.getAttribute("data-step-key");
        const status = getRoleStatus(key);
        renderWorkflowRolePane(key, status, project);
    }
}

// Render step detail descriptions dynamically
function renderWorkflowRolePane(roleKey, stepStatus, project) {
    const pane = document.getElementById("workflow-role-pane");
    pane.innerHTML = "";

    // Generate custom detail items matching human-like details
    const detailData = {
        coordinator: {
            title: "Coordinator Agent",
            completed: ["Review intake requirements", "Decompose specification into build plan steps"],
            working: "Refining project tasks",
            next: "Pass specs to Architecture discipline",
            artifacts: project.artifacts.build_plan ? "build_plan.md" : null
        },
        architect: {
            title: "Architect Agent",
            completed: project.artifacts.architecture_doc ? ["Formulate architecture specifications", "Create Mermaid flow diagram", "Draft ADRs (Architecture Decision Records)"] : [],
            working: "Formulating architectural contracts",
            next: "Builder initialization",
            artifacts: project.artifacts.architecture_doc ? "architecture_doc.md" : null
        },
        builder: {
            title: "Builder Agent",
            completed: project.artifacts.generated_code ? ["Initialize repository branch", "Implement backend services", "Integrate models and tools"] : [],
            working: "Implementing REST controllers & logic",
            next: "Reviewer inspection of code codebases",
            artifacts: project.artifacts.generated_code ? "generated_code (Source code)" : null
        },
        reviewer: {
            title: "Reviewer Agent",
            completed: project.artifacts.code_review ? ["Perform adversarial review of changes", "Audit security vulnerabilities"] : [],
            working: "Comparing implementation against architecture blueprints",
            next: "QA verification suite execution",
            artifacts: project.artifacts.code_review ? "code_review.md" : null
        },
        qa: {
            title: "QA Agent",
            completed: project.artifacts.qa_report ? ["Execute test runner", "Validate feature acceptance criteria"] : [],
            working: "Running integration assertions",
            next: "Platform operations evaluation",
            artifacts: project.artifacts.qa_report ? "qa_report.md" : null
        },
        platform: {
            title: "Platform Agent",
            completed: project.artifacts.platform_recommendations ? ["Audit API metrics", "Generate runtime optimization checklist", "Verify deployment config"] : [],
            working: "Assembling operational profiles",
            next: "Final sign-off compilation",
            artifacts: project.artifacts.platform_recommendations ? "platform_recommendations" : null
        }
    };

    const details = detailData[roleKey];
    if (!details) return;

    let artifactsHtml = "";
    if (details.artifacts) {
        artifactsHtml = `
            <div class="step-details-section">
                <h4>Generated Artifacts</h4>
                <div style="font-size:0.85rem; background:rgba(0,0,0,0.2); border:1px solid hsl(var(--border-color)); padding:0.5rem; border-radius:4px; display:inline-flex; align-items:center; gap:0.5rem;">
                    <i class="fa-solid fa-file-code" style="color:hsl(var(--primary))"></i>
                    <span>${details.artifacts}</span>
                </div>
            </div>
        `;
    }

    let completedListHtml = "";
    if (stepStatus === "completed" || details.completed.length > 0) {
        completedListHtml = `
            <div class="step-details-section">
                <h4>Completed Work</h4>
                <ul>
                    ${details.completed.map(item => `<li><i class="fa-solid fa-circle-check"></i> ${item}</li>`).join("")}
                </ul>
            </div>
        `;
    } else {
        completedListHtml = `
            <div class="step-details-section">
                <h4>Completed Work</h4>
                <span style="font-size:0.85rem; color:hsl(var(--text-dimmed)); font-style:italic;">No tasks completed yet.</span>
            </div>
        `;
    }

    let statusHeader = "";
    if (stepStatus === "completed") {
        statusHeader = '<span class="badge-status completed">Complete</span>';
    } else if (stepStatus === "active") {
        statusHeader = '<span class="badge-status building">Running</span>';
    } else {
        statusHeader = '<span class="badge-status created">Waiting</span>';
    }

    pane.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; border-bottom:1px solid hsl(var(--border-color)); padding-bottom:0.5rem;">
            <h3 style="margin-bottom:0;border:none;padding:0;">${details.title}</h3>
            ${statusHeader}
        </div>
        
        ${completedListHtml}

        <div class="step-details-section">
            <h4>Current Activity</h4>
            <span style="font-size:0.88rem; color:hsl(var(--text-muted));">
                ${stepStatus === 'active' ? `<i class="fa-solid fa-spinner fa-spin" style="margin-right:0.4rem;color:hsl(var(--status-blue));"></i>${details.working}` : stepStatus === 'completed' ? 'Finished task execution.' : 'Waiting to begin.'}
            </span>
        </div>

        <div class="step-details-section">
            <h4>Next Step</h4>
            <span style="font-size:0.88rem; color:hsl(var(--text-dimmed));">${stepStatus === 'completed' ? 'Proceeded to next team member.' : details.next}</span>
        </div>

        ${artifactsHtml}
    `;
}

// Render Project-Specific Activity Logs
function renderProjectTimelineLogs(project) {
    const list = document.getElementById("project-journal-logs");
    list.innerHTML = "";

    // Fetch and filter logs related to this project. We can query logs using the request_id or filter them locally.
    // To make it highly relevant, let's fetch activity logs from API and filter those with workflow_id in their payloads!
    fetch(`${API_BASE}/api/v1/activity-logs?limit=100`, {
        headers: getHeaders()
    })
    .then(res => res.json())
    .then(logs => {
        // Filter logs matching workflow_id
        const filtered = logs.filter(log => {
            return log.payload && (log.payload.workflow_id === project.id || log.payload.session_id === project.id);
        });

        if (filtered.length === 0) {
            list.innerHTML = `
                <div style="text-align: center; color: hsl(var(--text-dimmed)); padding: 2rem; font-size: 0.85rem;">
                    No log events recorded for this project yet.
                </div>
            `;
            return;
        }

        renderTimelineLogItems(list, filtered);
    })
    .catch(e => {
        console.error(e);
        list.innerHTML = `<div style="color:hsl(var(--status-red))">Failed to load project timeline logs.</div>`;
    });
}

function renderTimelineLogItems(container, logsList) {
    container.innerHTML = "";

    logsList.forEach(log => {
        const item = document.createElement("div");
        item.className = "log-item";

        const logTime = new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        
        // Humanize the event description
        let text = `${log.source}: ${log.event_type}`;
        let iconClass = "fa-solid fa-info-circle blue";

        if (log.event_type === "workflow_created") {
            text = "Coordinator initialized build planning.";
            iconClass = "fa-solid fa-folder-plus blue";
        } else if (log.event_type === "intake_session_created") {
            text = "Intake coordinator launched new interview.";
            iconClass = "fa-solid fa-comments blue";
        } else if (log.event_type === "model_route_started") {
            text = `Router selected ${log.payload.model} model for ${log.payload.capability}.`;
            iconClass = "fa-solid fa-microchip blue";
        } else if (log.event_type === "platform_recommendation") {
            text = "Platform Agent finalized operational optimization recommendations.";
            iconClass = "fa-solid fa-chart-line green";
        } else if (log.event_type === "workflow_escalated") {
            text = `Build blocked & escalated by ${log.payload.escalated_by}: ${log.payload.reason}`;
            iconClass = "fa-solid fa-triangle-exclamation red";
        } else if (log.event_type === "workflow_escalation_resolved") {
            text = `Escalation resolved by management. Action: ${log.payload.action}.`;
            iconClass = "fa-solid fa-circle-check green";
        } else if (log.event_type === "workflow_approved_and_completed") {
            text = `Production deployment approved by ${log.payload.approved_by}. Engineering Passport compiled.`;
            iconClass = "fa-solid fa-flag-checkered green";
        } else if (log.event_type === "intake_specification_generated") {
            text = "Intake Coordinator validated and generated requirements specification.";
            iconClass = "fa-solid fa-file-signature green";
        }

        item.innerHTML = `
            <span class="log-time">${logTime}</span>
            <div class="log-text" onclick="showJsonDetails('${log.id}')">
                <i class="${iconClass}"></i>
                <span>${text}</span>
            </div>
        `;

        container.appendChild(item);
    });
}

function showJsonDetails(logId) {
    // Look up log from local or global states
    const foundLog = state.globalJournal.find(l => l.id === logId);
    if (!foundLog) return;

    document.getElementById("modal-json-content").textContent = JSON.stringify(foundLog, null, 4);
    document.getElementById("json-modal").classList.add("active");
}

/* ==========================================================================
   Dest 3: GLOBAL ENGINEERING JOURNAL (TIMELINE FEED)
   ========================================================================== */
async function loadGlobalJournal() {
    try {
        const res = await fetch(`${API_BASE}/api/v1/activity-logs?limit=50`, {
            headers: getHeaders()
        });

        if (res.ok) {
            const data = await res.json();
            state.globalJournal = data;
            
            if (state.activeTab === "journal") {
                filterJournal();
            }
        }
    } catch (e) {
        console.error("Journal loading error:", e);
    }
}

function filterJournal() {
    const list = document.getElementById("global-journal-container");
    const searchText = document.getElementById("journal-search").value.toLowerCase();
    const sourceFilter = document.getElementById("journal-source-filter").value;

    let filtered = state.globalJournal;

    if (sourceFilter) {
        filtered = filtered.filter(l => l.source === sourceFilter);
    }

    if (searchText) {
        filtered = filtered.filter(l => {
            const desc = l.event_type.toLowerCase();
            const source = l.source.toLowerCase();
            return desc.includes(searchText) || source.includes(searchText);
        });
    }

    if (filtered.length === 0) {
        list.innerHTML = `
            <div style="text-align: center; color: hsl(var(--text-dimmed)); padding: 4rem; font-size: 0.9rem;">
                No journal logs match the active filters.
            </div>
        `;
        return;
    }

    renderTimelineLogItems(list, filtered);
}

/* ==========================================================================
   Dest 4: ENGINEERING PASSPORTS
   ========================================================================== */
function loadPassportsDirectory() {
    const listContainer = document.getElementById("passport-tree-container");
    listContainer.innerHTML = "";

    const completedProjects = state.projects.filter(p => p.status === "completed");

    if (completedProjects.length === 0) {
        listContainer.innerHTML = `
            <div style="padding: 1.5rem; text-align: center; color: hsl(var(--text-dimmed)); font-size: 0.85rem;">
                No passports archived. Complete a project build first.
            </div>
        `;
        return;
    }

    completedProjects.forEach(p => {
        const item = document.createElement("div");
        item.className = "passport-tree-item";
        item.innerHTML = `
            <i class="fa-solid fa-folder-closed"></i>
            <span>${p.title}</span>
        `;
        
        item.addEventListener("click", () => {
            document.querySelectorAll(".passport-tree-item").forEach(el => el.classList.remove("active"));
            item.classList.add("active");
            item.querySelector("i").className = "fa-solid fa-folder-open";
            renderPassportDocument(p);
        });

        listContainer.appendChild(item);
    });
}

function renderPassportDocument(project) {
    const viewer = document.getElementById("passport-viewer-content");

    viewer.innerHTML = `
        <div class="project-detail-header" style="background-color:rgba(0,0,0,0.15)">
            <div class="detail-header-top">
                <span class="detail-title">${project.title} — Passport Vault</span>
                <span class="badge-status completed">Released</span>
            </div>
            <div class="detail-info-bar">
                <div class="info-item">
                    <span class="lbl">Archive Date</span>
                    <span class="val">${new Date(project.updated_at).toLocaleDateString()}</span>
                </div>
                <div class="info-item">
                    <span class="lbl">Signed By</span>
                    <span class="val">${project.approved_by || 'Management Sign-off'}</span>
                </div>
                <div class="info-item">
                    <span class="lbl">Passport File</span>
                    <span class="val"><code>engineering_passport.md</code></span>
                </div>
            </div>
        </div>
        <div class="detail-content-area">
            <div class="passport-split-layout">
                <div class="passport-doc-column">
                    <div class="passport-doc-header">
                        <span>engineering_passport.md</span>
                        <button class="btn-copy" onclick="copyText('passport-content-vault')"><i class="fa-solid fa-copy"></i> Copy</button>
                    </div>
                    <div class="passport-doc-body markdown-body" id="passport-content-vault">
                        ${project.artifacts.engineering_passport ? marked.parse(project.artifacts.engineering_passport) : 'No passport contents.'}
                    </div>
                </div>
                <div class="passport-doc-column">
                    <div class="passport-doc-header">
                        <span>deployment_guide.md</span>
                        <button class="btn-copy" onclick="copyText('deployment-guide-vault')"><i class="fa-solid fa-copy"></i> Copy</button>
                    </div>
                    <div class="passport-doc-body markdown-body" id="deployment-guide-vault">
                        <h1>Production Deployment Guide</h1>
                        <p><strong>Release Tag:</strong> <code>rel_${project.id.slice(0, 8)}</code></p>
                        <p><strong>Commit Hash:</strong> <code>${project.artifacts.commit_hash || '7a8f9c1d2e3f0b'}</code></p>
                        <h3>Deployment Pipeline Steps</h3>
                        <ol>
                            <li>Pull the repository branch corresponding to the release commit hash.</li>
                            <li>Configure and populate the production environment file (<code>.env</code>).</li>
                            <li>Run automated database migrations: <code>alembic upgrade head</code>.</li>
                            <li>Launch Docker containers: <code>docker compose up --build -d</code>.</li>
                            <li>Verify API availability by testing the health check endpoint: <code>/healthz</code> and <code>/readyz</code>.</li>
                        </ol>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Global Text Copy helper
window.copyText = function(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;

    const range = document.createRange();
    range.selectNode(el);
    window.getSelection().removeAllRanges();
    window.getSelection().addRange(range);
    
    try {
        document.execCommand("copy");
        alert("Document content copied to clipboard!");
    } catch (err) {
        console.error("Copy execution failed:", err);
    }
    
    window.getSelection().removeAllRanges();
};


/* ==========================================================================
   Dest 5: SHARED KNOWLEDGE BOARD
   ========================================================================== */

async function updateCandidatesBadgeCount() {
    try {
        const res = await fetch(`${API_BASE}/api/v1/knowledge/candidates`, {
            headers: getHeaders()
        });
        if (res.ok) {
            const data = await res.json();
            state.knowledgeCandidates = data;
            const badge = document.getElementById("active-candidates-badge");
            if (data.length > 0) {
                badge.textContent = data.length;
                badge.style.display = "block";
            } else {
                badge.style.display = "none";
            }
        }
    } catch (e) {
        console.error("Candidates badge error:", e);
    }
}

function initKnowledgeBoard() {
    switchKnowledgeSubTab(state.knowledgeSubTab);
    updateCandidatesBadgeCount();
}

function switchKnowledgeSubTab(subTabName) {
    state.knowledgeSubTab = subTabName;
    state.activeKnowledgeItemId = null;

    // Toggle active link CSS classes
    const candBtn = document.getElementById("knowledge-tab-candidates");
    const vaultBtn = document.getElementById("knowledge-tab-vault");

    if (subTabName === "candidates") {
        candBtn.classList.add("active");
        vaultBtn.classList.remove("active");
        loadKnowledgeCandidates();
    } else {
        candBtn.classList.remove("active");
        vaultBtn.classList.add("active");
        loadCuratedVault();
    }

    // Reset details view to placeholder
    document.getElementById("knowledge-detail-content").innerHTML = `
        <div class="detail-placeholder">
            <i class="fa-solid fa-brain detail-placeholder-icon"></i>
            <h3>Knowledge Curation Board</h3>
            <p>Select a ${subTabName === 'candidates' ? 'proposed knowledge candidate to approve' : 'shared knowledge playbook'} to review its full contents.</p>
        </div>
    `;
}

async function loadKnowledgeCandidates() {
    const list = document.getElementById("knowledge-items-list");
    list.innerHTML = `<div style="padding:1.5rem;text-align:center;"><i class="fa-solid fa-spinner fa-spin"></i> Loading...</div>`;

    try {
        const res = await fetch(`${API_BASE}/api/v1/knowledge/candidates`, {
            headers: getHeaders()
        });
        if (res.ok) {
            const data = await res.json();
            state.knowledgeCandidates = data;
            renderKnowledgeItemsList(data);
        } else {
            list.innerHTML = `<div style="padding:1.5rem;color:hsl(var(--status-red));">Failed to load candidates.</div>`;
        }
    } catch (e) {
        console.error(e);
        list.innerHTML = `<div style="padding:1.5rem;color:hsl(var(--status-red));">Network error loading candidates.</div>`;
    }
}

async function loadCuratedVault() {
    const list = document.getElementById("knowledge-items-list");
    list.innerHTML = `<div style="padding:1.5rem;text-align:center;"><i class="fa-solid fa-spinner fa-spin"></i> Loading...</div>`;

    try {
        const res = await fetch(`${API_BASE}/api/v1/knowledge/shared`, {
            headers: getHeaders()
        });
        if (res.ok) {
            const data = await res.json();
            state.sharedKnowledge = data;
            renderKnowledgeItemsList(data);
        } else {
            list.innerHTML = `<div style="padding:1.5rem;color:hsl(var(--status-red));">Failed to load curated vault.</div>`;
        }
    } catch (e) {
        console.error(e);
        list.innerHTML = `<div style="padding:1.5rem;color:hsl(var(--status-red));">Network error loading curated vault.</div>`;
    }
}

function renderKnowledgeItemsList(items) {
    const list = document.getElementById("knowledge-items-list");
    list.innerHTML = "";

    if (items.length === 0) {
        list.innerHTML = `
            <div style="padding: 1.5rem; text-align: center; color: hsl(var(--text-dimmed)); font-size: 0.85rem;">
                No items in this category.
            </div>
        `;
        return;
    }

    // Mapping categories to nice icons
    const iconMap = {
        "playbook": "fa-playbook fa-solid fa-book-open",
        "coding_standard": "fa-solid fa-code",
        "adr": "fa-solid fa-file-shield",
        "security": "fa-solid fa-shield-halved",
        "platform": "fa-solid fa-chart-line"
    };

    items.forEach(item => {
        const div = document.createElement("div");
        div.className = `passport-tree-item ${state.activeKnowledgeItemId === item.id ? 'active' : ''}`;
        
        const iconClass = iconMap[item.category] || "fa-solid fa-brain";
        const dateStr = new Date(item.created_at).toLocaleDateString();

        div.innerHTML = `
            <i class="${iconClass}"></i>
            <div style="display:flex; flex-direction:column; gap:0.15rem; min-width:0; text-align:left;">
                <span style="font-weight:500; font-size:0.88rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${item.title}</span>
                <span style="font-size:0.75rem; color:hsl(var(--text-dimmed));">${item.category} • ${dateStr}</span>
            </div>
        `;

        div.addEventListener("click", () => {
            document.querySelectorAll(".passport-tree-item").forEach(el => el.classList.remove("active"));
            div.classList.add("active");
            selectKnowledgeItem(item.id);
        });

        list.appendChild(div);
    });
}

function selectKnowledgeItem(itemId) {
    state.activeKnowledgeItemId = itemId;
    let found = null;

    if (state.knowledgeSubTab === "candidates") {
        found = state.knowledgeCandidates.find(c => c.id === itemId);
    } else {
        found = state.sharedKnowledge.find(s => s.id === itemId);
    }

    if (found) {
        renderKnowledgeDetails(found);
    }
}

function renderKnowledgeDetails(item) {
    const pane = document.getElementById("knowledge-detail-content");
    const dateStr = new Date(item.created_at).toLocaleString();

    let detailsHtml = "";

    if (state.knowledgeSubTab === "candidates") {
        detailsHtml = `
            <div class="project-detail-header" style="background-color:rgba(0,0,0,0.15)">
                <div class="detail-header-top">
                    <span class="detail-title">${item.title}</span>
                    <span class="badge-status awaiting_approval">Proposed Candidate</span>
                </div>
                <div class="detail-info-bar">
                    <div class="info-item">
                        <span class="lbl">Created</span>
                        <span class="val">${dateStr}</span>
                    </div>
                    <div class="info-item">
                        <span class="lbl">Category</span>
                        <span class="val">${item.category}</span>
                    </div>
                    <div class="info-item">
                        <span class="lbl">Tier</span>
                        <span class="val">${item.tier}</span>
                    </div>
                </div>
            </div>

            <div class="detail-content-area" style="display:flex; flex-direction:column; gap:1.5rem;">
                <div class="action-card approval" style="margin-bottom:0;">
                    <div class="action-card-header">
                        <i class="fa-solid fa-brain"></i>
                        <span class="action-card-title">Shared Knowledge Curation Action</span>
                    </div>
                    <div class="action-card-desc">
                        Review the proposed playbook or architectural recommendation. If approved, the candidate will be promoted to the Shared Knowledge Vault, making it active for all future project runs. If rejected, it will be dismissed and archived.
                    </div>
                    <div class="action-form">
                        <div class="form-group">
                            <label class="form-label" for="curator-input">Curation Signature Name</label>
                            <input type="text" id="curator-input" class="form-control" placeholder="E.g., Robby Burns" style="margin-bottom:0.75rem;">
                            
                            <label class="form-label" for="curator-comments">Curation Comments / Rationale</label>
                            <textarea id="curator-comments" class="form-control" placeholder="Comments on this recommendation standard..." rows="2" style="margin-bottom:1rem; resize:none;"></textarea>
                            
                            <div class="action-buttons-row">
                                <button class="btn btn-primary" id="btn-approve-knowledge"><i class="fa-solid fa-circle-check"></i> Approve & Promote</button>
                                <button class="btn btn-danger" id="btn-reject-knowledge"><i class="fa-solid fa-circle-xmark"></i> Reject Candidate</button>
                            </div>
                        </div>
                    </div>
                </div>

                <div style="background-color:rgba(0,0,0,0.2); border:1px solid hsl(var(--border-color)); padding:1.5rem; border-radius:8px; flex:1; overflow-y:auto; text-align:left;">
                    <div class="form-label" style="margin-bottom:0.5rem;">Proposed Content</div>
                    <div class="markdown-body">
                        ${marked.parse(item.content)}
                    </div>
                </div>
            </div>
        `;
    } else {
        // CURATED VAULT ITEM
        const approvedAtStr = item.approved_at ? new Date(item.approved_at).toLocaleDateString() : 'N/A';
        const metaComments = item.metadata_json && item.metadata_json.comments ? item.metadata_json.comments : 'Promoted to shared guidelines.';

        detailsHtml = `
            <div class="project-detail-header" style="background-color:rgba(0,0,0,0.15)">
                <div class="detail-header-top">
                    <span class="detail-title">${item.title}</span>
                    <span class="badge-status completed">Curated Standard</span>
                </div>
                <div class="detail-info-bar">
                    <div class="info-item">
                        <span class="lbl">Approved Date</span>
                        <span class="val">${approvedAtStr}</span>
                    </div>
                    <div class="info-item">
                        <span class="lbl">Approved By</span>
                        <span class="val">${item.approved_by || 'Management Sign-off'}</span>
                    </div>
                    <div class="info-item">
                        <span class="lbl">Category</span>
                        <span class="val">${item.category}</span>
                    </div>
                </div>
            </div>

            <div class="detail-content-area" style="display:flex; flex-direction:column; gap:1.5rem;">
                <div style="background-color:rgba(255,255,255,0.01); border:1px solid hsl(var(--border-color)); padding:1rem 1.25rem; border-radius:8px; text-align:left;">
                    <div class="form-label" style="margin-bottom:0.25rem;">Curation Rationale / Comments</div>
                    <span style="font-size:0.9rem; color:hsl(var(--text-muted)); font-style:italic;">"${metaComments}"</span>
                </div>

                <div style="background-color:rgba(0,0,0,0.25); border:1px solid hsl(var(--border-color)); padding:1.5rem; border-radius:8px; flex:1; overflow-y:auto; text-align:left;">
                    <div class="form-label" style="margin-bottom:0.75rem;">Curated Content</div>
                    <div class="markdown-body">
                        ${marked.parse(item.content)}
                    </div>
                </div>
            </div>
        `;
    }

    pane.innerHTML = detailsHtml;

    // Attach button listeners if Candidate mode
    if (state.knowledgeSubTab === "candidates") {
        document.getElementById("btn-approve-knowledge").addEventListener("click", () => approveKnowledgeCandidate(item.id));
        document.getElementById("btn-reject-knowledge").addEventListener("click", () => rejectKnowledgeCandidate(item.id));
    }
}

async function approveKnowledgeCandidate(itemId) {
    const curatorInput = document.getElementById("curator-input");
    const commentsInput = document.getElementById("curator-comments");

    const curator = curatorInput.value.trim();
    const comments = commentsInput.value.trim();

    if (!curator) {
        alert("Please sign your name to approve.");
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/api/v1/knowledge/${itemId}/approve`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({
                approved_by: curator,
                comments: comments || "Approved candidate standard."
            })
        });

        if (res.ok) {
            alert("Knowledge candidate successfully approved and promoted to Shared Knowledge!");
            // Load candidates list again
            await loadKnowledgeCandidates();
            await updateCandidatesBadgeCount();
        } else {
            const err = await res.json();
            alert(`Approval failed: ${err.detail || 'Unknown error'}`);
        }
    } catch (e) {
        console.error(e);
    }
}

async function rejectKnowledgeCandidate(itemId) {
    const curatorInput = document.getElementById("curator-input");
    const commentsInput = document.getElementById("curator-comments");

    const curator = curatorInput.value.trim();
    const comments = commentsInput.value.trim();

    if (!curator) {
        alert("Please sign your name to reject.");
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/api/v1/knowledge/${itemId}/reject`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({
                rejected_by: curator,
                comments: comments || "Rejected candidate playbook."
            })
        });

        if (res.ok) {
            alert("Knowledge candidate successfully rejected and archived.");
            // Load candidates list again
            await loadKnowledgeCandidates();
            await updateCandidatesBadgeCount();
        } else {
            const err = await res.json();
            alert(`Rejection failed: ${err.detail || 'Unknown error'}`);
        }
    } catch (e) {
        console.error(e);
    }
}

// Load Infrastructure Transparency Panel
async function loadInfrastructure() {
    const container = document.getElementById("infrastructure-grid-container");
    if (!container) return;
    
    container.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: hsl(var(--text-muted));">
            <i class="fa-solid fa-circle-notch fa-spin" style="font-size: 2rem; margin-bottom: 1rem; display: block; margin-left: auto; margin-right: auto; width: fit-content;"></i>
            Checking adapter connections...
        </div>
    `;

    try {
        const res = await fetch(`${API_BASE}/api/v1/infrastructure`, {
            method: "GET",
            headers: getHeaders()
        });

        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }

        const data = await res.json();
        container.innerHTML = "";

        // FontAwesome Icons mapping for components
        const iconMap = {
            "Models": "fa-brain",
            "Repository": "fa-code-branch",
            "Deployment": "fa-cloud-arrow-up",
            "Memory": "fa-database",
            "Storage": "fa-hard-drive"
        };

        data.components.forEach(comp => {
            const card = document.createElement("div");
            card.className = "infra-card";

            const iconClass = iconMap[comp.name] || "fa-server";
            const badgeClass = comp.health ? "operational" : "degraded";
            const badgeIcon = comp.health ? "fa-circle-check" : "fa-triangle-exclamation";
            const badgeText = comp.health ? "Healthy" : "Degraded";

            let propertiesHtml = "";
            let detailsHtml = "";

            // Generic properties
            propertiesHtml = `
                <div class="infra-property-item">
                    <span class="infra-property-label">Configured Provider</span>
                    <span class="infra-property-value">${comp.provider}</span>
                </div>
                <div class="infra-property-item">
                    <span class="infra-property-label">Active Adapter</span>
                    <span class="infra-property-value">${comp.adapter}</span>
                </div>
                <div class="infra-property-item">
                    <span class="infra-property-label">Operational Status</span>
                    <span class="infra-property-value">${comp.status}</span>
                </div>
            `;

            // Dynamic detail subsections
            if (comp.name === "Models" && comp.details["Capabilities & Routing"]) {
                detailsHtml = `
                    <div class="infra-details-section">
                        <div class="infra-details-title">Capability Routing</div>
                        <div class="infra-mapping-list">
                `;
                for (const [capability, model] of Object.entries(comp.details["Capabilities & Routing"])) {
                    detailsHtml += `
                        <div class="infra-mapping-item">
                            <span class="infra-mapping-key">${capability}</span>
                            <span class="infra-mapping-val">${model}</span>
                        </div>
                    `;
                }
                detailsHtml += `
                        </div>
                    </div>
                `;
            } else if (comp.details) {
                // Render general key-values from details object
                detailsHtml = `
                    <div class="infra-details-section">
                        <div class="infra-details-title">Adapter Details</div>
                        <div class="infra-mapping-list">
                `;
                for (const [key, value] of Object.entries(comp.details)) {
                    if (key !== "Capabilities & Routing") {
                        detailsHtml += `
                            <div class="infra-mapping-item">
                                <span class="infra-mapping-key">${key}</span>
                                <span class="infra-mapping-val">${value}</span>
                            </div>
                        `;
                    }
                }
                detailsHtml += `
                        </div>
                    </div>
                `;
            }

            card.innerHTML = `
                <div class="infra-card-header">
                    <div class="infra-card-title">
                        <i class="fa-solid ${iconClass} infra-card-icon"></i>
                        <span>${comp.name}</span>
                    </div>
                    <span class="infra-badge ${badgeClass}">
                        <i class="fa-solid ${badgeIcon}"></i>
                        <span>${badgeText}</span>
                    </span>
                </div>
                <div class="infra-property-list">
                    ${propertiesHtml}
                </div>
                ${detailsHtml}
            `;

            container.appendChild(card);
        });

    } catch (e) {
        console.error("Failed to load infrastructure details:", e);
        container.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: hsl(var(--status-red));">
                <i class="fa-solid fa-triangle-exclamation" style="font-size: 2rem; margin-bottom: 1rem; display: block; margin-left: auto; margin-right: auto; width: fit-content;"></i>
                Failed to retrieve infrastructure configuration. Ensure backend services are healthy.
            </div>
        `;
    }
}
