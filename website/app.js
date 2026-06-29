// --- MOBILE-FIRST INTERACTIVE ENGINE v2 (strict mode) ---
'use strict';

document.addEventListener('DOMContentLoaded', () => {

    // ==========================================
    // 1. MOBILE BURGER MENU OVERLAY
    // ==========================================
    const burgerBtn = document.querySelector('.mobile-nav-toggle');
    const mobileMenu = document.getElementById('mobile-menu');
    const menuLinks = document.querySelectorAll('.menu-link');

    if (burgerBtn && mobileMenu) {
        const toggleMenu = () => {
            burgerBtn.classList.toggle('active');
            mobileMenu.classList.toggle('active');
            if (mobileMenu.classList.contains('active')) {
                document.body.style.overflow = 'hidden';
            } else {
                document.body.style.overflow = '';
            }
        };
        burgerBtn.addEventListener('click', toggleMenu);
        menuLinks.forEach(link => {
            link.addEventListener('click', () => {
                burgerBtn.classList.remove('active');
                mobileMenu.classList.remove('active');
                document.body.style.overflow = '';
            });
        });
    }

    // ==========================================
    // 2. THE MATRIX DIGITAL RAIN (Optimized)
    // ==========================================
    const canvas = document.getElementById('matrix-canvas');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        let width = canvas.width = window.innerWidth;
        let height = canvas.height = window.innerHeight;
        const katakana = 'ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ';
        const alphabet = katakana.split('');
        const fontSize = 14;
        let columns = Math.floor(width / fontSize);
        let rainDrops = [];

        const initMatrix = () => {
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight;
            columns = Math.floor(width / fontSize);
            rainDrops = [];
            for (let x = 0; x < columns; x++) {
                rainDrops[x] = Math.random() * -100;
            }
        };
        initMatrix();
        window.addEventListener('resize', initMatrix);

        const drawMatrix = () => {
            const isMainPage = window.location.pathname.includes('main.html');
            const fadeOpacity = isMainPage ? 0.08 : 0.04; // Мягкий шлейф на основном сайте, плотный и длинный на визитке
            ctx.fillStyle = `rgba(5, 8, 15, ${fadeOpacity})`;
            ctx.fillRect(0, 0, width, height);
            ctx.font = fontSize + 'px monospace';
            
            // Check if current page is main landing to apply different opacity and highlights
            const opacity = isMainPage ? 0.38 : 0.95;
            const highlightChance = isMainPage ? 0.98 : 0.94; // Больше белых вспышек на главной (6% вместо 2%)

            for (let i = 0; i < rainDrops.length; i++) {
                const text = alphabet[Math.floor(Math.random() * alphabet.length)];
                const x = i * fontSize;
                const y = rainDrops[i] * fontSize;
                ctx.fillStyle = Math.random() > highlightChance ? '#ffffff' : `hsla(180, 100%, 50%, ${opacity})`;
                ctx.fillText(text, x, y);
                if (y > height && Math.random() > 0.975) rainDrops[i] = 0;
                rainDrops[i]++;
            }
        };

        let lastTime = 0;
        const fps = 25;
        const nextFrameMs = 1000 / fps;
        const animate = (timestamp) => {
            requestAnimationFrame(animate);
            const elapsed = timestamp - lastTime;
            if (elapsed > nextFrameMs) {
                lastTime = timestamp - (elapsed % nextFrameMs);
                drawMatrix();
            }
        };
        requestAnimationFrame(animate);
    }

    // ==========================================
    // 3. INTERACTIVE SERVICES ACCORDION
    // ==========================================
    const accordionItems = document.querySelectorAll('.accordion-item');
    accordionItems.forEach(item => {
        const header = item.querySelector('.accordion-header');
        const content = item.querySelector('.accordion-content');
        // Initialize all closed
        content.style.maxHeight = '0px';

        header.addEventListener('click', (e) => {
            e.stopPropagation();
            const isActive = item.classList.contains('active');

            // Close all items
            accordionItems.forEach(el => {
                el.classList.remove('active');
                el.querySelector('.accordion-content').style.maxHeight = '0px';
            });

            // Open clicked item if it was closed
            if (!isActive) {
                item.classList.add('active');
                content.style.maxHeight = '1000px';
            }
        });
    });



    // ==========================================
    // 4. FUNNEL CALCULATOR (2-step slider)
    // ==========================================
    const step1 = document.getElementById('calc-step-1');
    const step2 = document.getElementById('calc-step-2');
    const nextBtn = document.getElementById('btn-calc-next');
    const backBtn = document.getElementById('btn-calc-back');
    const dots = document.querySelectorAll('.step-dot');

    const leadsInput = document.getElementById('leads-input');
    const convMeetInput = document.getElementById('conv-meet-input');
    const convMeetVal = document.getElementById('conv-meet-val');
    const convDealInput = document.getElementById('conv-deal-input');
    const convDealVal = document.getElementById('conv-deal-val');
    const commissionInput = document.getElementById('commission-input');
    const leadsDisplay = document.getElementById('leads-display');
    const commissionDisplay = document.getElementById('commission-display');

    const resDealsCurrent = document.getElementById('res-deals-current');
    const resRevenueCurrent = document.getElementById('res-revenue-current');
    const resRevenueLost = document.getElementById('res-revenue-lost');
    const resRevenuePotential = document.getElementById('res-revenue-potential');

    function formatCurrency(amount) {
        if (amount >= 1000000) return (amount / 1000000).toFixed(1) + ' млн ₽';
        return Math.round(amount).toLocaleString('ru-RU') + ' ₽';
    }

    function calculateFunnel() {
        if (!leadsInput) return;
        const leads = parseFloat(leadsInput.value) || 0;
        const convMeet = parseFloat(convMeetInput.value) || 0;
        const convDeal = parseFloat(convDealInput.value) || 0;
        const commission = parseFloat(commissionInput.value) || 0;
        const lossPercent = 25;

        const dealsCurrent = leads * (convMeet / 100) * (convDeal / 100);
        const revenueCurrent = dealsCurrent * commission;
        const revenuePotential = revenueCurrent / (1 - lossPercent / 100);
        const revenueLost = revenuePotential - revenueCurrent;

        if (resDealsCurrent) resDealsCurrent.textContent = Math.round(dealsCurrent);
        if (resRevenueCurrent) resRevenueCurrent.textContent = formatCurrency(revenueCurrent);
        if (resRevenueLost) resRevenueLost.textContent = formatCurrency(revenueLost);
        if (resRevenuePotential) resRevenuePotential.textContent = formatCurrency(revenuePotential);
    }

    if (leadsInput) {
        leadsInput.addEventListener('input', (e) => {
            if (leadsDisplay) leadsDisplay.textContent = e.target.value;
            calculateFunnel();
        });
        commissionInput.addEventListener('input', (e) => {
            const val = parseInt(e.target.value);
            if (commissionDisplay) commissionDisplay.textContent = val.toLocaleString('ru-RU') + ' ₽';
            calculateFunnel();
        });
        convMeetInput.addEventListener('input', (e) => {
            if (convMeetVal) convMeetVal.textContent = e.target.value + '%';
            calculateFunnel();
        });
        convDealInput.addEventListener('input', (e) => {
            if (convDealVal) convDealVal.textContent = e.target.value + '%';
            calculateFunnel();
        });
        calculateFunnel();
    }

    if (nextBtn && backBtn && step1 && step2) {
        step2.style.transform = 'translateX(100%)';
        step2.style.opacity = '0';

        nextBtn.addEventListener('click', () => {
            calculateFunnel();
            step1.style.transform = 'translateX(-100%)';
            step1.style.opacity = '0';
            step2.style.transform = 'translateX(0)';
            step2.style.opacity = '1';
            step1.classList.remove('active');
            step2.classList.add('active');
            dots[0].classList.remove('active');
            dots[1].classList.add('active');
        });

        backBtn.addEventListener('click', () => {
            step1.style.transform = 'translateX(0)';
            step1.style.opacity = '1';
            step2.style.transform = 'translateX(100%)';
            step2.style.opacity = '0';
            step2.classList.remove('active');
            step1.classList.add('active');
            dots[1].classList.remove('active');
            dots[0].classList.add('active');
        });
    }

    // ==========================================
    // 5. QUIZ ENGINE
    // ==========================================
    const quizQuestions = document.querySelectorAll('.quiz-q');
    const quizProgressFill = document.getElementById('quiz-progress-fill');
    const quizQNum = document.getElementById('quiz-q-num');
    const quizQuestionsWrapper = document.getElementById('quiz-questions');
    const quizResult = document.getElementById('quiz-result');
    const quizResultEmoji = document.getElementById('quiz-result-emoji');
    const quizResultTitle = document.getElementById('quiz-result-title');
    const quizResultText = document.getElementById('quiz-result-text');
    const quizResultScore = document.getElementById('quiz-result-score');
    const quizRestart = document.getElementById('quiz-restart');

    if (quizQuestions.length > 0) {
        let currentQ = 0;
        let totalScore = 0;
        const total = quizQuestions.length;
        const quizResultTiers = [
            { minScore: 0, maxScore: 4, emoji: '🚕', title: 'Риэлтор-таксист', text: 'Ты возишь клиентов и ждёшь, когда они сами решат.' },
            { minScore: 5, maxScore: 9, emoji: '📈', title: 'Брокер на переходе', text: 'Ты думаешь как стратег, но система ещё не выстроена.' },
            { minScore: 10, maxScore: 14, emoji: '🚀', title: 'Системный брокер', text: 'Сильная позиция. Следующий уровень — масштаб и команда.' }
        ];

        const updateProgress = () => {
            const pct = (currentQ / total) * 100;
            if (quizProgressFill) quizProgressFill.style.width = pct + '%';
            if (quizQNum) quizQNum.textContent = Math.min(currentQ + 1, total);
        };

        const showQuestion = (idx) => {
            quizQuestions.forEach(q => q.classList.remove('active'));
            if (quizQuestions[idx]) quizQuestions[idx].classList.add('active');
            updateProgress();
        };

        const showQuizResult = () => {
            if (quizProgressFill) quizProgressFill.style.width = '100%';
            const tier = quizResultTiers.find(r => totalScore >= r.minScore && totalScore <= r.maxScore) || quizResultTiers[2];
            if (quizQuestionsWrapper) quizQuestionsWrapper.style.display = 'none';
            if (quizResult) quizResult.classList.remove('hidden');
            if (quizResultEmoji) quizResultEmoji.textContent = tier.emoji;
            if (quizResultTitle) quizResultTitle.textContent = tier.title;
            if (quizResultText) quizResultText.textContent = tier.text;
            if (quizResultScore) quizResultScore.textContent = totalScore;
        };

        const handleAnswer = (btn) => {
            totalScore += parseInt(btn.getAttribute('data-score'));
            btn.classList.add('selected');
            btn.closest('.quiz-q').querySelectorAll('.quiz-opt').forEach(b => b.style.pointerEvents = 'none');
            setTimeout(() => {
                currentQ++;
                currentQ < total ? showQuestion(currentQ) : showQuizResult();
            }, 380);
        };

        document.querySelectorAll('.quiz-opt').forEach(btn => btn.addEventListener('click', () => handleAnswer(btn)));
        if (quizRestart) quizRestart.addEventListener('click', () => {
            currentQ = 0; totalScore = 0;
            document.querySelectorAll('.quiz-opt').forEach(btn => { btn.classList.remove('selected'); btn.style.pointerEvents = ''; });
            if (quizQuestionsWrapper) quizQuestionsWrapper.style.display = '';
            if (quizResult) quizResult.classList.add('hidden');
            showQuestion(0);
        });
        showQuestion(0);
    }

    // ==========================================
    // 6. SCROLL TO TOP BUTTON
    // ==========================================
    const btnScrollTop = document.getElementById('btn-scroll-top');
    if (btnScrollTop) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 300) {
                btnScrollTop.classList.add('visible');
            } else {
                btnScrollTop.classList.remove('visible');
            }
        }, { passive: true });

        btnScrollTop.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // ==========================================
    // 7. SCROLL REVEAL ANIMATIONS
    // ==========================================
    // Exclude .accordion-item — they're inside max-height:0 containers so observer can't see them
    const revealElements = document.querySelectorAll(
        '.glass-card:not(.accordion-item), .section-header, .stat-item'
    );
    revealElements.forEach(el => el.classList.add('reveal'));
    const scrollReveal = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => { if (entry.isIntersecting) { entry.target.classList.add('active'); observer.unobserve(entry.target); } });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
    revealElements.forEach(el => scrollReveal.observe(el));

    // ==========================================
    // 7. DYNAMIC IMAGE GALLERY WITH LIGHTBOX
    // ==========================================
    const galleryGrid = document.getElementById('gallery-grid');
    const btnGalleryMore = document.getElementById('btn-gallery-more');
    const lightboxModal = document.getElementById('lightbox-modal');
    const lightboxImg = document.getElementById('lightbox-img');
    const lightboxClose = document.getElementById('lightbox-close');
    const lightboxPrev = document.getElementById('lightbox-prev');
    const lightboxNext = document.getElementById('lightbox-next');

    if (galleryGrid && lightboxModal) {
        const totalPhotos = 56;
        let currentPhotoIndex = 1;

        const createGalleryItem = (num) => {
            const item = document.createElement('div');
            item.className = 'gallery-item glass-card reveal';
            item.setAttribute('data-index', num);
            const img = document.createElement('img');
            img.src = `img/gallery/${num}.jpeg`;
            img.alt = `Событие ${num}`;
            img.loading = 'lazy';
            item.appendChild(img);
            return item;
        };

        // Load ALL photos immediately
        for (let i = 1; i <= totalPhotos; i++) {
            const item = createGalleryItem(i);
            galleryGrid.appendChild(item);
            scrollReveal.observe(item);
        }

        // Hide the "show more" button — all photos already loaded
        if (btnGalleryMore) btnGalleryMore.style.display = 'none';

        const openLightbox = (idx) => {
            currentPhotoIndex = idx;
            lightboxImg.src = `img/gallery/${currentPhotoIndex}.jpeg`;
            lightboxModal.classList.add('active');
            document.body.style.overflow = 'hidden';
        };
        const closeLightbox = () => { lightboxModal.classList.remove('active'); document.body.style.overflow = ''; };
        const showPrevPhoto = () => { currentPhotoIndex = currentPhotoIndex === 1 ? totalPhotos : currentPhotoIndex - 1; lightboxImg.src = `img/gallery/${currentPhotoIndex}.jpeg`; };
        const showNextPhoto = () => { currentPhotoIndex = currentPhotoIndex === totalPhotos ? 1 : currentPhotoIndex + 1; lightboxImg.src = `img/gallery/${currentPhotoIndex}.jpeg`; };

        galleryGrid.addEventListener('click', (e) => {
            const item = e.target.closest('.gallery-item');
            if (item) openLightbox(parseInt(item.getAttribute('data-index'), 10));
        });

        if (lightboxClose) lightboxClose.addEventListener('click', closeLightbox);
        if (lightboxPrev) lightboxPrev.addEventListener('click', showPrevPhoto);
        if (lightboxNext) lightboxNext.addEventListener('click', showNextPhoto);

        lightboxModal.addEventListener('click', (e) => {
            if (e.target === lightboxModal || (!e.target.closest('.lightbox-content') && !e.target.closest('.lightbox-nav'))) closeLightbox();
        });

        let touchStartX = 0;
        lightboxModal.addEventListener('touchstart', (e) => { touchStartX = e.changedTouches[0].screenX; }, { passive: true });
        lightboxModal.addEventListener('touchend', (e) => {
            const diff = e.changedTouches[0].screenX - touchStartX;
            if (Math.abs(diff) > 50) diff < 0 ? showNextPhoto() : showPrevPhoto();
        }, { passive: true });

        document.addEventListener('keydown', (e) => {
            if (!lightboxModal.classList.contains('active')) return;
            if (e.key === 'Escape') closeLightbox();
            if (e.key === 'ArrowLeft') showPrevPhoto();
            if (e.key === 'ArrowRight') showNextPhoto();
        });
    }
});
