// Telegram Web App Main JavaScript
class WebApp {
    constructor() {
        this.telegram = window.Telegram.WebApp;
        this.currentScreen = 'loading';
        this.userData = {};
        this.modulesData = [];
        this.lessonsData = {};
        this.progress = {};
        
        this.init();
    }

    async init() {
        // Initialize Telegram Web App
        this.telegram.expand();
        this.telegram.ready();
        
        // Get user data
        this.userData = this.telegram.initDataUnsafe.user;
        
        // Initialize the app
        await this.loadUserData();
        this.showMainScreen();
        this.loadModules();
        this.updateStats();
        
        // Setup event listeners
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Handle back button
        this.telegram.BackButton.onClick(() => {
            this.handleBackButton();
        });
        
        // Handle viewport changes
        this.telegram.onEvent('viewportChanged', () => {
            this.handleViewportChange();
        });
    }

    async loadUserData() {
        try {
            // Get user data from backend
            const response = await this.apiRequest('/user/data', {
                user_id: this.userData.id,
                username: this.userData.username,
                first_name: this.userData.first_name
            });
            
            if (response.success) {
                this.progress = response.progress || {};
                this.userData = { ...this.userData, ...response.user_info };
            } else {
                console.error('Failed to load user data');
            }
        } catch (error) {
            console.error('Error loading user data:', error);
        }
    }

    async loadModules() {
        try {
            const response = await this.apiRequest('/modules/list');
            
            if (response.success) {
                this.modulesData = response.modules;
                this.renderModules();
            } else {
                console.error('Failed to load modules');
            }
        } catch (error) {
            console.error('Error loading modules:', error);
        }
    }

    renderModules() {
        const modulesList = document.getElementById('modules-list');
        modulesList.innerHTML = '';
        
        this.modulesData.forEach((module, index) => {
            const moduleCard = this.createModuleCard(module, index + 1);
            modulesList.appendChild(moduleCard);
        });
    }

    createModuleCard(module, moduleNumber) {
        const card = document.createElement('div');
        card.className = 'module-card';
        card.onclick = () => this.showModule(module.id, moduleNumber);
        
        const moduleProgress = this.progress[module.id] || { lessons_completed: 0, total_lessons: 0 };
        const isCompleted = moduleProgress.lessons_completed === moduleProgress.total_lessons;
        
        card.innerHTML = `
            <div class="module-header-info">
                <span class="module-number">Блок ${moduleNumber}</span>
                ${isCompleted ? '<span style="color: var(--success-color);">✓</span>' : ''}
            </div>
            <h3 class="module-title">${module.title}</h3>
            <div class="module-stats">
                <span class="module-stat">📚 ${moduleProgress.lessons_completed}/${moduleProgress.total_lessons}</span>
                <span class="module-stat">⏱️ ${module.estimated_time || '30 мин'}</span>
            </div>
        `;
        
        return card;
    }

    async showModule(moduleId, moduleNumber) {
        this.currentScreen = 'module';
        this.hideAllScreens();
        document.getElementById('module-screen').style.display = 'flex';
        
        // Update header
        const module = this.modulesData.find(m => m.id == moduleId);
        document.getElementById('module-title').textContent = module.title;
        
        // Load lessons for this module
        await this.loadModuleLessons(moduleId);
        
        // Show back button
        this.telegram.BackButton.show();
    }

    async loadModuleLessons(moduleId) {
        try {
            const response = await this.apiRequest('/modules/lessons', { module_id: moduleId });
            
            if (response.success) {
                this.lessonsData[moduleId] = response.lessons;
                this.renderModuleLessons(moduleId);
            } else {
                console.error('Failed to load module lessons');
            }
        } catch (error) {
            console.error('Error loading module lessons:', error);
        }
    }

    renderModuleLessons(moduleId) {
        const lessonsList = document.getElementById('lessons-list');
        lessonsList.innerHTML = '';
        
        const lessons = this.lessonsData[moduleId] || [];
        const moduleProgress = this.progress[moduleId] || { completed_lessons: [] };
        
        lessons.forEach((lesson, index) => {
            const lessonCard = this.createLessonCard(lesson, index + 1, moduleProgress);
            lessonsList.appendChild(lessonCard);
        });
        
        // Update progress in header
        const completed = moduleProgress.completed_lessons ? moduleProgress.completed_lessons.length : 0;
        document.getElementById('module-progress-text').textContent = `${completed}/${lessons.length}`;
    }

    createLessonCard(lesson, lessonNumber, moduleProgress) {
        const card = document.createElement('div');
        card.className = 'lesson-card';
        card.onclick = () => this.showLesson(lesson.id, lessonNumber);
        
        const isCompleted = moduleProgress.completed_lessons && 
                           moduleProgress.completed_lessons.includes(lesson.id);
        
        card.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-weight: 600;">Урок ${lessonNumber}</span>
                ${isCompleted ? '<span style="color: var(--success-color);">✓</span>' : '<span style="color: var(--tg-theme-hint-color);">○</span>'}
            </div>
            <h4 style="font-size: 14px; margin-bottom: 4px;">${lesson.title}</h4>
            <div style="display: flex; gap: 12px; font-size: 12px; color: var(--tg-theme-hint-color);">
                <span>⏱️ ${lesson.duration || '15 мин'}</span>
                ${lesson.has_video ? '<span>🎥 Видео</span>' : ''}
                ${lesson.has_files ? '<span>📄 Материалы</span>' : ''}
            </div>
        `;
        
        return card;
    }

    async showLesson(lessonId, lessonNumber) {
        this.currentScreen = 'lesson';
        this.hideAllScreens();
        document.getElementById('lesson-screen').style.display = 'flex';
        
        try {
            const response = await this.apiRequest('/lessons/content', { lesson_id: lessonId });
            
            if (response.success) {
                const lesson = response.lesson;
                
                // Update header
                document.getElementById('lesson-title').textContent = `Урок ${lessonNumber}`;
                
                // Clear previous content
                document.getElementById('text-content').innerHTML = '';
                document.getElementById('files-container').style.display = 'none';
                document.getElementById('video-container').style.display = 'none';
                
                // Render lesson content
                if (lesson.video_url) {
                    this.renderVideo(lesson.video_url);
                }
                
                if (lesson.text_content) {
                    this.renderTextContent(lesson.text_content);
                }
                
                if (lesson.files && lesson.files.length > 0) {
                    this.renderFiles(lesson.files);
                }
                
                if (lesson.assignment) {
                    this.renderAssignment(lesson.assignment);
                }
            } else {
                console.error('Failed to load lesson content');
            }
        } catch (error) {
            console.error('Error loading lesson content:', error);
        }
        
        this.telegram.BackButton.show();
    }

    renderVideo(videoUrl) {
        const videoContainer = document.getElementById('video-container');
        const videoIframe = document.getElementById('video-iframe');
        
        // Handle different video platforms
        if (videoUrl.includes('youtube.com') || videoUrl.includes('youtu.be')) {
            videoIframe.src = this.getYouTubeEmbedUrl(videoUrl);
        } else if (videoUrl.includes('vk.com')) {
            videoIframe.src = this.getVKEmbedUrl(videoUrl);
        } else if (videoUrl.includes('kinescope.io')) {
            videoIframe.src = this.getKinescopeEmbedUrl(videoUrl);
        } else {
            // Direct video file
            videoIframe.src = videoUrl;
        }
        
        videoContainer.style.display = 'block';
    }

    getYouTubeEmbedUrl(url) {
        const videoId = this.extractYouTubeVideoId(url);
        return `https://www.youtube.com/embed/${videoId}`;
    }

    getVKEmbedUrl(url) {
        const videoId = this.extractVKVideoId(url);
        return `https://vk.com/video_ext.php?${videoId}`;
    }

    getKinescopeEmbedUrl(url) {
        const videoId = this.extractKinescopeVideoId(url);
        return `https://kinescope.io/embed/${videoId}`;
    }

    extractYouTubeVideoId(url) {
        const regex = /(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)/;
        const match = url.match(regex);
        return match ? match[1] : '';
    }

    extractVKVideoId(url) {
        const regex = /video(-?\d+)_(\d+)/;
        const match = url.match(regex);
        return match ? `oid=${match[1]}&id=${match[2]}` : '';
    }

    extractKinescopeVideoId(url) {
        const regex = /kinescope\.io\/(?:embed\/)?([^\/\s]+)/;
        const match = url.match(regex);
        return match ? match[1] : '';
    }

    renderTextContent(textContent) {
        const textContainer = document.getElementById('text-content');
        textContainer.innerHTML = textContent;
    }

    renderFiles(files) {
        const filesContainer = document.getElementById('files-container');
        const filesList = document.getElementById('files-list');
        
        filesList.innerHTML = '';
        
        files.forEach(file => {
            const fileItem = document.createElement('a');
            fileItem.className = 'file-item';
            fileItem.href = file.url;
            fileItem.target = '_blank';
            fileItem.innerHTML = `
                <span class="file-icon">${this.getFileIcon(file.type)}</span>
                <div class="file-info">
                    <div class="file-name">${file.name}</div>
                    <div class="file-size">${file.size || 'PDF файл'}</div>
                </div>
            `;
            filesList.appendChild(fileItem);
        });
        
        filesContainer.style.display = 'block';
    }

    getFileIcon(fileType) {
        const icons = {
            'pdf': '📄',
            'doc': '📝',
            'docx': '📝',
            'xls': '📊',
            'xlsx': '📊',
            'ppt': '📽️',
            'pptx': '📽️'
        };
        return icons[fileType.toLowerCase()] || '📎';
    }

    renderAssignment(assignment) {
        const assignmentContent = document.getElementById('assignment-content');
        assignmentContent.innerHTML = `
            <p><strong>Задание:</strong></p>
            <p>${assignment.description}</p>
        `;
        
        // Show submit button only if assignment is not completed
        const submitBtn = document.getElementById('submit-assignment');
        const isCompleted = this.isAssignmentCompleted(assignment.id);
        
        if (isCompleted) {
            submitBtn.textContent = '✓ Задание сдано';
            submitBtn.disabled = true;
            submitBtn.style.backgroundColor = 'var(--success-color)';
        } else {
            submitBtn.textContent = 'Сдать задание';
            submitBtn.disabled = false;
            submitBtn.style.backgroundColor = '';
        }
        
        // Store assignment ID for submission
        submitBtn.dataset.assignmentId = assignment.id;
    }

    isAssignmentCompleted(assignmentId) {
        // Check if this assignment is already completed
        const userAssignments = this.progress.completed_assignments || [];
        return userAssignments.includes(assignmentId);
    }

    async submitAssignment() {
        const submitBtn = document.getElementById('submit-assignment');
        const assignmentId = submitBtn.dataset.assignmentId;
        
        try {
            const response = await this.apiRequest('/assignments/submit', {
                assignment_id: assignmentId,
                user_id: this.userData.id
            });
            
            if (response.success) {
                // Update UI
                submitBtn.textContent = '✓ Задание сдано';
                submitBtn.disabled = true;
                submitBtn.style.backgroundColor = 'var(--success-color)';
                
                // Update local progress
                if (!this.progress.completed_assignments) {
                    this.progress.completed_assignments = [];
                }
                this.progress.completed_assignments.push(assignmentId);
                
                // Show success message
                this.telegram.showAlert('Задание успешно сдано!');
            } else {
                this.telegram.showAlert('Ошибка при сдаче задания');
            }
        } catch (error) {
            console.error('Error submitting assignment:', error);
            this.telegram.showAlert('Ошибка при сдаче задания');
        }
    }

    showMainScreen() {
        this.currentScreen = 'main';
        this.hideAllScreens();
        document.getElementById('main-screen').style.display = 'flex';
        
        // Update navigation
        this.updateNavigation('main');
        
        // Hide back button on main screen
        this.telegram.BackButton.hide();
        
        // Update stats
        this.updateStats();
    }

    showProfile() {
        this.currentScreen = 'profile';
        this.hideAllScreens();
        document.getElementById('profile-screen').style.display = 'flex';
        
        // Update navigation
        this.updateNavigation('profile');
        
        // Show back button
        this.telegram.BackButton.show();
        
        // Load profile data
        this.loadProfileData();
    }

    async loadProfileData() {
        try {
            const response = await this.apiRequest('/user/stats', {
                user_id: this.userData.id
            });
            
            if (response.success) {
                this.updateProfileStats(response.stats);
                this.updateAchievements(response.achievements);
            } else {
                console.error('Failed to load profile data');
            }
        } catch (error) {
            console.error('Error loading profile data:', error);
        }
    }

    updateProfileStats(stats) {
        document.getElementById('profile-modules-completed').textContent = stats.modules_completed;
        document.getElementById('profile-lessons-completed').textContent = stats.lessons_completed;
        document.getElementById('profile-study-hours').textContent = stats.study_hours;
        document.getElementById('profile-assignments-completed').textContent = stats.assignments_completed;
    }

    updateAchievements(achievements) {
        const achievementsList = document.getElementById('achievements-list');
        achievementsList.innerHTML = '';
        
        achievements.forEach(achievement => {
            const achievementCard = document.createElement('div');
            achievementCard.className = `achievement ${achievement.unlocked ? 'unlocked' : ''}`;
            achievementCard.innerHTML = `
                <div class="achievement-icon">${achievement.icon}</div>
                <div class="achievement-name">${achievement.name}</div>
            `;
            achievementsList.appendChild(achievementCard);
        });
    }

    updateStats() {
        // Calculate total progress
        let totalLessons = 0;
        let completedLessons = 0;
        let totalStudyTime = 0;
        
        this.modulesData.forEach(module => {
            const moduleProgress = this.progress[module.id] || {};
            totalLessons += moduleProgress.total_lessons || 0;
            completedLessons += moduleProgress.lessons_completed || 0;
            totalStudyTime += moduleProgress.study_time || 0;
        });
        
        // Update progress bar
        const progressPercent = totalLessons > 0 ? (completedLessons / totalLessons) * 100 : 0;
        document.getElementById('progress-fill').style.width = `${progressPercent}%`;
        document.getElementById('progress-percent').textContent = `${Math.round(progressPercent)}%`;
        
        // Update user info
        if (this.userData.first_name) {
            document.getElementById('user-name').textContent = this.userData.first_name;
        }
        document.getElementById('user-progress').textContent = `Пройдено ${completedLessons} из ${totalLessons} уроков`;
        
        // Update stats
        document.getElementById('total-lessons').textContent = totalLessons;
        document.getElementById('completed-lessons').textContent = completedLessons;
        document.getElementById('study-time').textContent = `${Math.round(totalStudyTime / 60)}ч`;
        
        // Update user avatar
        if (this.userData.photo_url) {
            document.getElementById('user-avatar').src = this.userData.photo_url;
        }
    }

    updateNavigation(active) {
        const navBtns = document.querySelectorAll('.nav-btn');
        navBtns.forEach(btn => btn.classList.remove('active'));
        
        if (active === 'main') {
            navBtns[0].classList.add('active');
        } else if (active === 'crm') {
            navBtns[1].classList.add('active');
        } else if (active === 'profile') {
            navBtns[2].classList.add('active');
        }
    }

    hideAllScreens() {
        const screens = document.querySelectorAll('.screen');
        screens.forEach(screen => screen.style.display = 'none');
    }

    handleBackButton() {
        if (this.currentScreen === 'lesson') {
            this.showModule();
        } else if (this.currentScreen === 'module') {
            this.showMainScreen();
        } else if (this.currentScreen === 'profile') {
            this.showMainScreen();
        } else if (this.currentScreen === 'crm') {
            this.showMainScreen();
        } else {
            this.showMainScreen();
        }
    }

    handleViewportChange() {
        // Handle viewport changes if needed
    }

    async apiRequest(endpoint, data = {}) {
        const baseUrl = window.location.origin;
        try {
            const response = await fetch(`${baseUrl}/api${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ...data,
                    initData: window.Telegram?.WebApp?.initData || ""
                })
            });
            if (response.ok) {
                return await response.json();
            }
        } catch (e) {
            console.warn("Live API request failed, using local mock data:", e);
        }
        
        // For demo purposes, simulate response
        if (endpoint === '/modules/list') {
            return {
                success: true,
                modules: [
                    {
                        id: 1,
                        title: 'Блок 1. Роль Навигатора и Золотое Правило',
                        estimated_time: '45 мин'
                    },
                    {
                        id: 2,
                        title: 'Блок 2. JTBD-Диагностика и Боли Клиента',
                        estimated_time: '60 мин'
                    }
                    // Add more modules as needed
                ]
            };
        }
        
        if (endpoint === '/modules/lessons') {
            return {
                success: true,
                lessons: [
                    {
                        id: 1,
                        title: 'Введение в роль Навигатора',
                        duration: '15 мин',
                        has_video: true,
                        has_files: true,
                        video_url: 'https://example.com/video1',
                        text_content: '<h4>Что такое Навигатор?</h4><p>Навигатор — это не просто риелтор...</p>',
                        files: [
                            {
                                name: 'Чек-лист Навигатора.pdf',
                                type: 'pdf',
                                url: 'https://docs.google.com/document/d/...'
                            }
                        ],
                        assignment: {
                            id: 1,
                            description: 'Просмотрите видео и подготовьте краткий конспект основных принципов работы Навигатора.'
                        }
                    },
                    {
                        id: 2,
                        title: 'Золотое Правило взаимодействия',
                        duration: '20 мин',
                        has_video: false,
                        has_files: true,
                        text_content: '<h4>Золотое Правило</h4><p>Не врать, не приукрашивать, не подлизываться...</p>',
                        files: [
                            {
                                name: 'Принципы работы.docx',
                                type: 'docx',
                                url: 'https://docs.google.com/document/d/...'
                            }
                        ],
                        assignment: {
                            id: 2,
                            description: 'Опишите 3 ситуации из вашей практики, где вы применили бы Золотое Правило.'
                        }
                    }
                ]
            };
        }
        
        // For other endpoints, return empty success response
        return {
            success: true,
            data: {}
        };
    }

    goBack() {
        this.handleBackButton();
    }

    goBackToModule() {
        this.currentScreen = 'module';
        this.hideAllScreens();
        document.getElementById('module-screen').style.display = 'flex';
    }

    markLessonCompleted() {
        this.telegram.showAlert('Отметить урок как завершенный?');
    }

    showCRM() {
        this.currentScreen = 'crm';
        this.hideAllScreens();
        document.getElementById('crm-screen').style.display = 'flex';
        this.updateNavigation('crm');
        this.telegram.BackButton.show();
        
        // Load CRM data
        this.loadCRMData();
        
        // Initial calc run
        this.currentCalcTab = this.currentCalcTab || 'standard';
        this.runCrmCalc();
    }

    async loadCRMData() {
        try {
            // Load leads
            const leadsResponse = await this.apiRequest('/crm/leads', { user_id: this.userData.id });
            const leads = leadsResponse.success ? leadsResponse.leads : [];

            // Load deals
            const dealsResponse = await this.apiRequest('/crm/deals', { user_id: this.userData.id });
            const deals = dealsResponse.success ? dealsResponse.deals : [];

            // Load active tasks
            const tasksResponse = await this.apiRequest('/crm/tasks', { user_id: this.userData.id });
            const tasks = tasksResponse.success ? tasksResponse.tasks : [];

            this.renderCRM(leads, deals, tasks);
        } catch (error) {
            console.error('Error loading CRM data:', error);
        }
    }

    renderCRM(leads, deals, tasks) {
        // Calculate metrics
        let totalVolume = 0;
        let totalCommission = 0;
        const stagesCount = {
            'Qualification': 0,
            'Financial Engineering': 0,
            'Presentation': 0,
            'Booking': 0,
            'Signing': 0,
            'Active Escrow Hold': 0,
            'Exit': 0
        };

        deals.forEach(deal => {
            totalVolume += deal.final_price || 0;
            totalCommission += deal.expected_commission || 0;
            
            // Increment stage count
            const stage = deal.stage;
            if (stagesCount[stage] !== undefined) {
                stagesCount[stage]++;
            } else {
                stagesCount['Qualification']++; // fallback
            }
        });

        // Format numbers for display
        document.getElementById('crm-total-volume').textContent = this.formatCurrency(totalVolume);
        document.getElementById('crm-expected-commission').textContent = this.formatCurrency(totalCommission);

        // Render pipeline
        const pipelineFlow = document.getElementById('crm-pipeline-flow');
        pipelineFlow.innerHTML = '';
        
        const stageLabels = {
            'Qualification': 'Квал',
            'Financial Engineering': 'ФинИнж',
            'Presentation': 'Презент',
            'Booking': 'Бронь',
            'Signing': 'Подпись',
            'Active Escrow Hold': 'Эскроу',
            'Exit': 'Выход'
        };

        Object.keys(stagesCount).forEach(stage => {
            const count = stagesCount[stage];
            const stageDiv = document.createElement('div');
            stageDiv.className = `pipeline-stage ${count > 0 ? 'active' : ''}`;
            stageDiv.innerHTML = `
                <div class="stage-bubble">${count}</div>
                <div class="stage-label">${stageLabels[stage]}</div>
            `;
            pipelineFlow.appendChild(stageDiv);
        });

        // Render today's tasks
        const todayTasks = document.getElementById('crm-today-tasks');
        todayTasks.innerHTML = '';
        const pendingTasks = tasks.filter(t => t.status === 'pending');
        
        if (pendingTasks.length === 0) {
            todayTasks.innerHTML = '<li class="empty-task">Задач нет</li>';
        } else {
            pendingTasks.forEach(task => {
                const li = document.createElement('li');
                li.className = 'task-item';
                li.innerHTML = `
                    <div style="font-weight: 600;">${task.client_name}: ${task.task_type === 'next_action' ? 'След. шаг' : 'Задача'}</div>
                    <div style="font-size:11px; margin-top:2px;">${task.description}</div>
                    <div style="font-size: 10px; color: #94A3B8; margin-top:4px;">До: ${task.due_date}</div>
                    <button onclick="completeCrmTask(${task.id})" style="margin-top:6px; font-size:10px; background:#10B981; border:none; color:white; padding:2px 6px; border-radius:4px; cursor:pointer;">✓ Выполнено</button>
                `;
                todayTasks.appendChild(li);
            });
        }

        // Render investor alerts (SLA checks, etc.)
        const investorAlerts = document.getElementById('crm-investor-alerts');
        investorAlerts.innerHTML = '';
        let alerts = [];

        deals.forEach(deal => {
            if (deal.stage === 'Signing' && !deal.escrow_account_opened) {
                alerts.push({
                    type: 'escrow',
                    text: `Сделка с ${deal.client_name} (ЖК ${deal.jk_name || 'Новостройка'}): не открыт эскроу-счет! Срок до ${deal.escrow_deadline || 'ближайших дней'}.`
                });
            }
            if (deal.scheme_type === 'tranche' && deal.second_tranche_date) {
                alerts.push({
                    type: 'tranche',
                    text: `2-й транш по ${deal.client_name}: плановая дата ${deal.second_tranche_date}.`
                });
            }
        });

        if (alerts.length === 0) {
            investorAlerts.innerHTML = '<li class="empty-alert">Алертов нет</li>';
        } else {
            alerts.forEach(alert => {
                const li = document.createElement('li');
                li.className = 'alert-item';
                li.textContent = alert.text;
                investorAlerts.appendChild(li);
            });
        }

        // Update OKR Progress
        const okrIncome = 250000;
        const okrTarget = 500000;
        const okrPercent = Math.min(Math.round((okrIncome / okrTarget) * 100), 100);
        
        const progressBar = document.getElementById('okr-progress-bar');
        if (progressBar) {
            progressBar.style.setProperty('--percent', `${okrPercent}%`);
        }
        const progressText = document.getElementById('okr-progress-text');
        if (progressText) {
            progressText.textContent = `${okrPercent}%`;
        }
        const incomeText = document.getElementById('okr-income');
        if (incomeText) {
            incomeText.textContent = `${Math.round(okrIncome / 1000)}к`;
        }
    }

    formatCurrency(value) {
        if (!value) return '0 ₽';
        return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(value);
    }

    openAddLeadModal() {
        document.getElementById('add-lead-modal').style.display = 'flex';
    }

    closeAddLeadModal() {
        document.getElementById('add-lead-modal').style.display = 'none';
    }

    async submitNewLead() {
        const name = document.getElementById('modal-lead-name').value.trim();
        const phone = document.getElementById('modal-lead-phone').value.trim();
        const isInvestor = document.getElementById('modal-lead-investor').checked;
        const budget = parseFloat(document.getElementById('modal-lead-budget').value) || 0;
        const pv = parseFloat(document.getElementById('modal-lead-pv').value) || 0;
        const pm = parseFloat(document.getElementById('modal-lead-pm').value) || 0;

        if (!name) {
            this.telegram.showAlert('Введите ФИО клиента!');
            return;
        }

        try {
            const response = await this.apiRequest('/crm/leads', {
                user_id: this.userData.id,
                client_name: name,
                phone: phone,
                is_investor: isInvestor,
                budget_limit: budget,
                down_payment: pv,
                comfort_monthly_payment: pm
            });

            if (response.success) {
                // Automatically create a deal for this lead
                await this.apiRequest('/crm/deals', {
                    lead_id: response.lead_id,
                    stage: 'Qualification',
                    base_price: budget,
                    final_price: budget,
                    scheme_type: 'standard',
                    expected_commission: budget * 0.03
                });

                this.telegram.showAlert('Лид успешно добавлен!');
                this.closeAddLeadModal();
                this.loadCRMData();
            } else {
                this.telegram.showAlert('Ошибка создания лида.');
            }
        } catch (error) {
            console.error('Error adding lead:', error);
            this.telegram.showAlert('Ошибка добавления лида.');
        }
    }

    async runCrmCalc() {
        const price = parseFloat(document.getElementById('calc-price-input').value) * 1000000 || 8000000;
        const pv = parseFloat(document.getElementById('calc-pv-input').value) * 1000000 || 1600000;
        const tab = this.currentCalcTab || 'standard';

        try {
            const response = await this.apiRequest('/calculator/calculate', {
                price: price,
                down_payment: pv
            });

            if (response.success) {
                const results = response.results;
                const output = document.getElementById('calc-results-output');
                
                if (tab === 'standard') {
                    const data = results.standard;
                    output.innerHTML = `
                        <div class="calc-result-row"><span>Кредит:</span><span class="calc-result-val">${this.formatCurrency(data.loan_amount)}</span></div>
                        <div class="calc-result-row"><span>Ставка:</span><span class="calc-result-val">${data.rate}%</span></div>
                        <div class="calc-result-row"><span>Платеж/мес:</span><span class="calc-result-val" style="color:#B45309;">${this.formatCurrency(data.monthly_payment)}</span></div>
                    `;
                } else if (tab === 'subsidized') {
                    const data = results.subsidized;
                    output.innerHTML = `
                        <div class="calc-result-row"><span>Цена с удорожанием:</span><span class="calc-result-val">${this.formatCurrency(data.price_subsidized)}</span></div>
                        <div class="calc-result-row"><span>Платеж/мес:</span><span class="calc-result-val" style="color:#10B981;">${this.formatCurrency(data.monthly_payment)}</span></div>
                        <div class="calc-result-row"><span>Окупаемость удорожания:</span><span class="calc-result-val">${data.break_even_years} лет</span></div>
                    `;
                } else if (tab === 'tranche') {
                    const data = results.tranche;
                    output.innerHTML = `
                        <div class="calc-result-row"><span>Платеж до сдачи (1-й транш):</span><span class="calc-result-val" style="color:#10B981;">${this.formatCurrency(data.payment_phase_1)}</span></div>
                        <div class="calc-result-row"><span>Платеж после сдачи:</span><span class="calc-result-val">${this.formatCurrency(data.payment_phase_2)}</span></div>
                        <div class="calc-result-row"><span>Прибыль с депозита за 2 года:</span><span class="calc-result-val" style="color:#10B981;">+${this.formatCurrency(data.deposit_profit_estimation)}</span></div>
                    `;
                }
            }
        } catch (error) {
            console.error('Error in CRM calculator:', error);
        }
    }

    selectCalcTab(tab) {
        this.currentCalcTab = tab;
        document.getElementById('calc-btn-standard').classList.remove('active');
        document.getElementById('calc-btn-subsidized').classList.remove('active');
        document.getElementById('calc-btn-tranche').classList.remove('active');
        document.getElementById(`calc-btn-${tab}`).classList.add('active');
        this.runCrmCalc();
    }

    async completeCrmTask(taskId) {
        try {
            const response = await this.apiRequest('/crm/tasks/complete', { task_id: taskId });
            if (response.success) {
                this.telegram.showAlert('Задача выполнена!');
                this.loadCRMData();
            }
        } catch (error) {
            console.error('Error completing task:', error);
        }
    }
}

// Initialize app when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.webApp = new WebApp();
});

// Global functions for HTML onclick handlers
function goBack() {
    window.webApp.goBack();
}

function goBackToModule() {
    window.webApp.goBackToModule();
}

function markLessonCompleted() {
    window.webApp.markLessonCompleted();
}

function submitAssignment() {
    window.webApp.submitAssignment();
}

function showMainScreen() {
    window.webApp.showMainScreen();
}

function showProfile() {
    window.webApp.showProfile();
}

function showCRM() {
    window.webApp.showCRM();
}

function openAddLeadModal() {
    window.webApp.openAddLeadModal();
}

function closeAddLeadModal() {
    window.webApp.closeAddLeadModal();
}

function submitNewLead() {
    window.webApp.submitNewLead();
}

function runCrmCalc() {
    window.webApp.runCrmCalc();
}

function selectCalcTab(tab) {
    window.webApp.selectCalcTab(tab);
}

function completeCrmTask(taskId) {
    window.webApp.completeCrmTask(taskId);
}