document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("taskModal");
    const searchInput = document.getElementById("taskSearch");
    const priorityFilter = document.getElementById("priorityFilter");
    const sortSelect = document.getElementById("sortTasks");
    const mobileMenuButton = document.querySelector(".mobile-menu-button");
    const sidebar = document.querySelector(".sidebar");

    /* =========================================================
       MODAL
    ========================================================= */

    function openModal() {
        if (!modal) return;
        modal.classList.add("is-open");
        modal.setAttribute("aria-hidden", "false");

        const taskInput = document.getElementById("task");
        if (taskInput) setTimeout(() => taskInput.focus(), 100);
    }

    function closeModal() {
        if (!modal) return;
        modal.classList.remove("is-open");
        modal.setAttribute("aria-hidden", "true");
    }

    document.querySelectorAll("[data-open-modal]").forEach((btn) => {
        btn.addEventListener("click", openModal);
    });

    document.querySelectorAll("[data-close-modal]").forEach((btn) => {
        btn.addEventListener("click", closeModal);
    });

    if (modal) {
        modal.addEventListener("click", (event) => {
            if (event.target === modal) closeModal();
        });
    }

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") closeModal();

        if (
            event.key === "/" &&
            document.activeElement &&
            !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName)
        ) {
            event.preventDefault();
            if (searchInput) searchInput.focus();
        }
    });

    /* =========================================================
       MOBILE SIDEBAR
    ========================================================= */

    if (mobileMenuButton && sidebar) {
        mobileMenuButton.addEventListener("click", (event) => {
            event.stopPropagation();
            sidebar.classList.toggle("open");
        });

        document.addEventListener("click", (event) => {
            if (
                sidebar.classList.contains("open") &&
                !sidebar.contains(event.target) &&
                event.target !== mobileMenuButton
            ) {
                sidebar.classList.remove("open");
            }
        });
    }

    /* =========================================================
       SEARCH / FILTER / SORT
    ========================================================= */

    function applyFilters() {
        const query = searchInput ? searchInput.value.toLowerCase().trim() : "";
        const priority = priorityFilter ? priorityFilter.value : "all";

        document.querySelectorAll(".task-item").forEach((task) => {
            const text = task.dataset.task || task.textContent.toLowerCase();
            const taskPriority = task.dataset.priority || "";

            const matchesSearch = !query || text.includes(query);
            const matchesPriority = priority === "all" || taskPriority === priority;

            task.style.display = matchesSearch && matchesPriority ? "" : "none";
        });
    }

    function applySort() {
        if (!sortSelect) return;
        const mode = sortSelect.value;
        const priorityRank = { high: 0, medium: 1, low: 2 };

        document.querySelectorAll(".task-list").forEach((list) => {
            const items = Array.from(list.querySelectorAll(".task-item"));
            if (items.length < 2) return;

            items.sort((a, b) => {
                if (mode === "priority") {
                    const pa = priorityRank[a.dataset.priority] ?? 3;
                    const pb = priorityRank[b.dataset.priority] ?? 3;
                    return pa - pb;
                }

                const ca = Date.parse(a.dataset.created || "") || 0;
                const cb = Date.parse(b.dataset.created || "") || 0;

                return mode === "oldest" ? ca - cb : cb - ca;
            });

            items.forEach((item) => list.appendChild(item));
        });
    }

    if (searchInput) searchInput.addEventListener("input", applyFilters);
    if (priorityFilter) priorityFilter.addEventListener("change", applyFilters);
    if (sortSelect) sortSelect.addEventListener("change", applySort);

    /* =========================================================
       TOAST
    ========================================================= */

    let toastContainer = document.querySelector(".toast-container");

    if (!toastContainer) {
        toastContainer = document.createElement("div");
        toastContainer.className = "toast-container";
        document.body.appendChild(toastContainer);
    }

    function showToast(message, isError = false) {
        const toast = document.createElement("div");
        toast.className = "toast" + (isError ? " toast-error" : "");
        toast.textContent = message;
        toastContainer.appendChild(toast);

        requestAnimationFrame(() => toast.classList.add("show"));

        setTimeout(() => {
            toast.classList.remove("show");
            setTimeout(() => toast.remove(), 250);
        }, 2500);
    }

    /* =========================================================
       API HELPER
    ========================================================= */

    async function apiRequest(url, options = {}) {
        const response = await fetch(url, {
            ...options,
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json",
                ...(options.headers || {}),
            },
        });

        if (!response.ok) {
            let message = "Request failed.";

            try {
                const data = await response.json();
                if (data.error) message = data.error;
            } catch (_) {
                // Keep default error message.
            }

            throw new Error(message);
        }

        return response.json();
    }

    function removeTaskWithAnimation(taskItem, onDone) {
        taskItem.style.height = `${taskItem.offsetHeight}px`;
        taskItem.style.overflow = "hidden";

        requestAnimationFrame(() => {
            taskItem.style.opacity = "0";
            taskItem.style.transform = "translateX(15px)";
            taskItem.style.height = "0";
            taskItem.style.margin = "0";
            taskItem.style.padding = "0";
        });

        setTimeout(() => {
            taskItem.remove();
            if (onDone) onDone();
        }, 250);
    }

    function resetTaskAnimation(taskItem) {
        taskItem.style.height = "";
        taskItem.style.overflow = "";
        taskItem.style.opacity = "";
        taskItem.style.transform = "";
        taskItem.style.margin = "";
        taskItem.style.padding = "";
    }

    /* =========================================================
       TASK ACTIONS (event delegation — cards have no forms)
    ========================================================= */

    document.addEventListener("click", async (event) => {
        const actionEl = event.target.closest("[data-action]");
        if (!actionEl) return;

        const taskItem = actionEl.closest(".task-item");
        if (!taskItem) return;

        const taskId = taskItem.dataset.taskId;
        if (!taskId) return;

        const action = actionEl.dataset.action;

        if (action === "toggle") {
            const wasCompleted = taskItem.classList.contains("completed");

            taskItem.classList.toggle("completed", !wasCompleted);
            actionEl.classList.toggle("checked", !wasCompleted);

            try {
                await apiRequest(`/api/tasks/${taskId}`, {
                    method: "PATCH",
                    body: JSON.stringify({ completed: !wasCompleted }),
                });
            } catch (error) {
                taskItem.classList.toggle("completed", wasCompleted);
                actionEl.classList.toggle("checked", wasCompleted);
                showToast(error.message, true);
            }

            return;
        }

        if (action === "skip") {
            try {
                await apiRequest(`/api/tasks/${taskId}`, {
                    method: "PATCH",
                    body: JSON.stringify({ skipped: true }),
                });

                removeTaskWithAnimation(taskItem, applyFilters);
            } catch (error) {
                showToast(error.message, true);
            }

            return;
        }

        if (action === "delete") {
            removeTaskWithAnimation(taskItem, applyFilters);

            try {
                await apiRequest(`/api/tasks/${taskId}`, { method: "DELETE" });
            } catch (error) {
                resetTaskAnimation(taskItem);
                showToast(error.message, true);
            }
        }
    });
});