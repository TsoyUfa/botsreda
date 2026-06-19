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
        
        // Get user data (with fallback for desktop/browser debugging)
        this.userData = this.telegram.initDataUnsafe.user || { id: 5690724590, username: "test_navigator", first_name: "Тестовый" };
        
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
        
        // Custom warning/hint if it's a voice assignment
        if (assignment.type === 'voice') {
            assignmentContent.innerHTML = `
                <p><strong>Задание (Голосовое):</strong></p>
                <p>${assignment.description}</p>
                <div class="voice-hw-notice" style="background: rgba(255, 165, 0, 0.15); border-left: 4px solid orange; padding: 12px; border-radius: 6px; margin: 12px 0; font-size: 14px;">
                    🎙️ <b>Внимание:</b> Это голосовое задание. Его необходимо надиктовать голосовым сообщением непосредственно в чат нашего Telegram-бота.
                </div>
            `;
            
            const submitBtn = document.getElementById('submit-assignment');
            submitBtn.textContent = 'Записать голосовое в чате бота';
            submitBtn.disabled = false;
            submitBtn.style.backgroundColor = 'orange';
            submitBtn.onclick = () => {
                this.telegram.close(); // Close Web App to record voice in bot
            };
            return;
        }

        assignmentContent.innerHTML = `
            <p><strong>Задание (Текстовое):</strong></p>
            <p>${assignment.description}</p>
            <textarea id="hw-text-response" placeholder="Введите ваш отчет по заданию здесь..." style="width: 100%; height: 100px; padding: 8px; border-radius: 6px; border: 1px solid var(--tg-theme-hint-color); background: var(--tg-theme-bg-color); color: var(--tg-theme-text-color); margin-top: 8px; font-family: inherit; font-size: 14px; box-sizing: border-box; resize: vertical;"></textarea>
        `;
        
        // Show submit button only if assignment is not completed/pending review
        const submitBtn = document.getElementById('submit-assignment');
        const isCompleted = this.isAssignmentCompleted(assignment.id);
        
        if (isCompleted) {
            submitBtn.textContent = '✓ Задание сдано';
            submitBtn.disabled = true;
            submitBtn.style.backgroundColor = 'var(--success-color)';
            submitBtn.onclick = () => this.submitAssignment();
        } else if (this.progress && this.progress.status === 'awaiting_review') {
            submitBtn.textContent = '⏳ На проверке у куратора';
            submitBtn.disabled = true;
            submitBtn.style.backgroundColor = 'var(--tg-theme-hint-color)';
            submitBtn.onclick = () => this.submitAssignment();
        } else {
            submitBtn.textContent = 'Сдать задание';
            submitBtn.disabled = false;
            submitBtn.style.backgroundColor = '';
            submitBtn.onclick = () => this.submitAssignment();
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
        const textResponseField = document.getElementById('hw-text-response');
        const textContent = textResponseField ? textResponseField.value.trim() : '';

        if (!textContent) {
            this.telegram.showAlert('Пожалуйста, напишите ваш ответ перед отправкой!');
            return;
        }
        
        try {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Отправка...';
            
            const response = await this.apiRequest('/assignments/submit', {
                user_id: this.userData.id,
                block_number: this.progress.current_block || 1,
                text_content: textContent
            });
            
            if (response.success) {
                // Update UI
                submitBtn.textContent = '⏳ На проверке';
                submitBtn.disabled = true;
                submitBtn.style.backgroundColor = 'var(--tg-theme-hint-color)';
                if (textResponseField) textResponseField.disabled = true;
                
                // Update local progress
                this.progress.status = 'awaiting_review';
                
                // Show success message
                this.telegram.showAlert('Задание успешно отправлено куратору на проверку!');
            } else {
                this.telegram.showAlert('Ошибка при сдаче задания: ' + (response.error || 'неизвестная ошибка'));
                submitBtn.disabled = false;
                submitBtn.textContent = 'Сдать задание';
            }
        } catch (error) {
            console.error('Error submitting assignment:', error);
            this.telegram.showAlert('Ошибка при связи с сервером');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Сдать задание';
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
        } else if (active === 'profile') {
            navBtns[1].classList.add('active');
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
        } else {
            this.showMainScreen();
        }
    }

    handleViewportChange() {
        // Handle viewport changes if needed
    }

    async apiRequest(endpoint, data = {}) {
        // Dynamically discover base URL from query string to avoid hardcoding production URLs
        const urlParams = new URLSearchParams(window.location.search);
        let apiBaseUrl = urlParams.get('api_url');
        if (!apiBaseUrl) {
            apiBaseUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
                ? 'http://localhost:5000'
                : ''; // Relative fallback
        }
        
        if (apiBaseUrl.endsWith('/')) {
            apiBaseUrl = apiBaseUrl.slice(0, -1);
        }
        
        const url = `${apiBaseUrl}/api${endpoint}`;
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            return await response.json();
        } catch (error) {
            console.error(`API request error on ${endpoint}:`, error);
            return { success: false, error: error.message };
        }
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