document.addEventListener('DOMContentLoaded', () => {
    const API_BASE = ''; // Same host

    // Application State
    let voicesList = [];
    let selectedFile = null;
    let activeAudioUrl = null;
    let isPlaying = false;
    let modelStatusPoll = null;
    let editVoiceId = null;
    let isSeeding = false;

    // DOM Elements
    const htmlElement = document.documentElement;
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const moonIcon = themeToggleBtn.querySelector('.moon-icon');
    const sunIcon = themeToggleBtn.querySelector('.sun-icon');

    // Tab buttons
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    // Onboarding Elements
    const onboardingBanner = document.getElementById('onboarding-banner');
    const closeBannerBtn = document.getElementById('close-banner-btn');
    const quickstartBox = document.getElementById('quickstart-box');
    const quickstartSeedBtn = document.getElementById('quickstart-seed-btn');
    const quickstartGoCloneBtn = document.getElementById('quickstart-go-clone-btn');
    const voiceCountBadge = document.getElementById('voice-count-badge');

    // Model Loading Banner
    const modelLoadingCard = document.getElementById('model-loading-card');
    const modelProgressFill = document.getElementById('model-progress-fill');
    const modelProgressPct = document.getElementById('model-progress-pct');

    // TTS Generator Form Elements
    const textInput = document.getElementById('text-input');
    const charCounter = document.getElementById('char-counter');
    const clearTextBtn = document.getElementById('clear-text-btn');
    const langSelect = document.getElementById('lang-select');
    const voiceSelect = document.getElementById('voice-select');
    
    // Sliders
    const speedRange = document.getElementById('speed-range');
    const speedVal = document.getElementById('speed-val');
    const speedTrack = document.getElementById('speed-track-fill');

    const pitchRange = document.getElementById('pitch-range');
    const pitchVal = document.getElementById('pitch-val');
    const pitchTrack = document.getElementById('pitch-track-fill');

    const volumeRange = document.getElementById('volume-range');
    const volumeVal = document.getElementById('volume-val');
    const volumeTrack = document.getElementById('volume-track-fill');

    const formatMp3 = document.getElementById('format-mp3');
    const formatWav = document.getElementById('format-wav');
    let selectedFormat = 'mp3';

    const trimSilenceCheck = document.getElementById('trim-silence-check');
    const normalizeCheck = document.getElementById('normalize-check');
    const generateBtn = document.getElementById('generate-btn');
    const generateBtnText = document.getElementById('generate-btn-text');

    // Audio Player
    const playerCard = document.getElementById('player-card');
    const noAudioState = document.getElementById('no-audio-state');
    const activePlayerState = document.getElementById('active-player-state');
    const playerPulse = document.getElementById('player-pulse');
    const waveformVisualizer = document.getElementById('waveform-visualizer');
    
    const audioElement = document.getElementById('audio-element');
    const playPauseBtn = document.getElementById('play-pause-btn');
    const playSvg = playPauseBtn.querySelector('.play-svg');
    const pauseSvg = playPauseBtn.querySelector('.pause-svg');

    const timelineSlider = document.getElementById('timeline-slider');
    const timelineFill = document.getElementById('timeline-fill');
    const currentTimeLabel = document.getElementById('current-time');
    const durationTimeLabel = document.getElementById('duration-time');
    const downloadAudioBtn = document.getElementById('download-audio-btn');

    // Voice Studio
    const ethicsConsent = document.getElementById('ethics-consent');
    const cloneName = document.getElementById('clone-name');
    const cloneLang = document.getElementById('clone-lang');
    const cloneLabel = document.getElementById('clone-label');
    const audioDropZone = document.getElementById('audio-drop-zone');
    const audioFileInput = document.getElementById('audio-file-input');
    const dropFileInfo = document.getElementById('drop-file-info');
    const cloneSubmitBtn = document.getElementById('clone-submit-btn');

    // Analysis results card
    const analysisResultsCard = document.getElementById('analysis-results-card');
    const profileTone = document.getElementById('profile-tone');
    const profilePace = document.getElementById('profile-pace');
    const profileAccent = document.getElementById('profile-accent');
    const profileStyle = document.getElementById('profile-style');

    // Library & History Grid
    const seedSampleBtn = document.getElementById('seed-sample-btn');
    const voicesGrid = document.getElementById('voices-grid');
    const historyTableBody = document.getElementById('history-table-body');

    // Edit Modal
    const editVoiceModal = document.getElementById('edit-voice-modal');
    const editVoiceName = document.getElementById('edit-voice-name');
    const editVoiceLabel = document.getElementById('edit-voice-label');
    const modalCancelBtn = document.getElementById('modal-cancel-btn');
    const modalSaveBtn = document.getElementById('modal-save-btn');

    // Footer Indicators
    const serverStatusDot = document.getElementById('server-status-dot');
    const serverStatusText = document.getElementById('server-status-text');
    const modelEngineBadge = document.getElementById('model-engine-badge');
    const ffmpegBadge = document.getElementById('ffmpeg-badge');

    // Language Flags mapping
    const flags = {
        en: '🇺🇸', ur: '🇵🇰', ar: '🇸🇦', hi: '🇮🇳', es: '🇪🇸',
        fr: '🇫🇷', de: '🇩🇪', ru: '🇷🇺', tr: '🇹🇷', it: '🇮🇹',
        pt: '🇧🇷', zh: '🇨🇳', ja: '🇯🇵', ko: '🇰🇷', pl: '🇵🇱',
        nl: '🇳🇱', cs: '🇨🇿'
    };

    // ----------------------------------------------------
    // Theme Manager
    // ----------------------------------------------------
    const savedTheme = localStorage.getItem('theme') || 'dark';
    htmlElement.setAttribute('data-theme', savedTheme);
    updateThemeIcons(savedTheme);

    themeToggleBtn.addEventListener('click', () => {
        const currentTheme = htmlElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        htmlElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcons(newTheme);
    });

    function updateThemeIcons(theme) {
        if (theme === 'dark') {
            moonIcon.style.display = 'block';
            sunIcon.style.display = 'none';
        } else {
            moonIcon.style.display = 'none';
            sunIcon.style.display = 'block';
        }
    }

    // ----------------------------------------------------
    // Tabs Navigation
    // ----------------------------------------------------
    function switchTab(tabId) {
        tabBtns.forEach(b => {
            if (b.dataset.tab === tabId) {
                b.classList.add('active');
            } else {
                b.classList.remove('active');
            }
        });
        tabContents.forEach(c => {
            if (c.id === tabId) {
                c.classList.add('active');
            } else {
                c.classList.remove('active');
            }
        });
    }

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            switchTab(btn.dataset.tab);
        });
    });

    // ----------------------------------------------------
    // Slider Controllers
    // ----------------------------------------------------
    function initSlider(slider, badge, track) {
        function update() {
            const min = parseFloat(slider.min);
            const max = parseFloat(slider.max);
            const val = parseFloat(slider.value);
            badge.textContent = `${val.toFixed(1)}x`;
            const percent = ((val - min) / (max - min)) * 100;
            track.style.width = `${percent}%`;
        }
        slider.addEventListener('input', update);
        update(); // Init call
    }

    initSlider(speedRange, speedVal, speedTrack);
    initSlider(pitchRange, pitchVal, pitchTrack);
    initSlider(volumeRange, volumeVal, volumeTrack);

    formatMp3.addEventListener('click', () => {
        formatMp3.classList.add('active');
        formatWav.classList.remove('active');
        selectedFormat = 'mp3';
    });

    formatWav.addEventListener('click', () => {
        formatWav.classList.add('active');
        formatMp3.classList.remove('active');
        selectedFormat = 'wav';
    });

    textInput.addEventListener('input', () => {
        const len = textInput.value.length;
        charCounter.textContent = `${len} / 1000 characters`;
    });

    clearTextBtn.addEventListener('click', () => {
        textInput.value = '';
        charCounter.textContent = '0 / 1000 characters';
        textInput.focus();
    });

    // ----------------------------------------------------
    // Drag & Drop (Voice Studio)
    // ----------------------------------------------------
    ethicsConsent.addEventListener('change', () => {
        toggleStudioSubmitBtn();
    });

    cloneName.addEventListener('input', () => {
        toggleStudioSubmitBtn();
    });

    function toggleStudioSubmitBtn() {
        const hasConsent = ethicsConsent.checked;
        const hasName = cloneName.value.trim().length > 0;
        const hasFile = selectedFile !== null;
        cloneSubmitBtn.disabled = !(hasConsent && hasName && hasFile);
    }

    audioDropZone.addEventListener('click', () => {
        audioFileInput.click();
    });

    audioFileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleSelectedFile(e.target.files[0]);
        }
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        audioDropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            audioDropZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        audioDropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            audioDropZone.classList.remove('dragover');
        }, false);
    });

    audioDropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleSelectedFile(files[0]);
        }
    });

    function handleSelectedFile(file) {
        const type = file.type;
        const validTypes = ['audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/x-wav'];
        if (!validTypes.includes(type) && !file.name.endsWith('.wav') && !file.name.endsWith('.mp3')) {
            showToast('Unsupported file type. Please upload WAV or MP3 audio.', 'error');
            return;
        }
        selectedFile = file;
        dropFileInfo.textContent = `${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`;
        toggleStudioSubmitBtn();
    }

    // ----------------------------------------------------
    // REST APIs & Health Status Polling
    // ----------------------------------------------------
    async function checkModelStatus() {
        try {
            const res = await fetch(`${API_BASE}/api/model-status`);
            if (!res.ok) throw new Error('API down');
            
            const data = await res.json();
            
            // Server Connection
            serverStatusDot.className = 'status-dot online';
            serverStatusText.textContent = 'Voice Engine Server Online';

            // FFmpeg Status
            if (data.ffmpeg_installed) {
                ffmpegBadge.textContent = 'FFmpeg Enabled';
                ffmpegBadge.className = 'badge success';
            } else {
                ffmpegBadge.textContent = 'FFmpeg Missing (WAV Only)';
                ffmpegBadge.className = 'badge warning';
                formatWav.click(); // Force WAV toggle
            }

            // Model Loading Status
            if (data.status === 'ready') {
                modelEngineBadge.textContent = 'XTTS v2 Engine Ready';
                modelEngineBadge.className = 'badge success';
                modelLoadingCard.style.display = 'none';
                generateBtn.disabled = false;
                generateBtn.classList.remove('loading');
                generateBtnText.textContent = 'Generate Speech';
                
                if (modelStatusPoll) {
                    clearInterval(modelStatusPoll);
                    modelStatusPoll = null;
                }
            } else if (data.status === 'loading') {
                const percentage = data.percentage !== undefined ? data.percentage : 0;
                const downloaded = data.downloaded_mb !== undefined ? data.downloaded_mb : 0;
                const total = data.total_mb !== undefined ? data.total_mb : 0;
                
                modelEngineBadge.textContent = `Downloading: ${downloaded}MB / ${total}MB (${percentage}%)`;
                modelEngineBadge.className = 'badge warning';
                
                // Show beautiful Loading Card
                modelLoadingCard.style.display = 'flex';
                modelProgressFill.style.width = `${percentage}%`;
                modelProgressPct.textContent = `${percentage}%`;
                
                generateBtn.disabled = true;
                generateBtn.classList.add('loading');
                generateBtnText.textContent = `Downloading (${percentage}%)`;
                
                // Start polling if not already started
                if (!modelStatusPoll) {
                    modelStatusPoll = setInterval(checkModelStatus, 2000);
                }
            } else if (data.status === 'failed') {
                modelEngineBadge.textContent = 'XTTS v2 Init Failed';
                modelEngineBadge.className = 'badge warning';
                modelLoadingCard.style.display = 'none';
                showToast(`Voice model failed to initialize: ${data.error}`, 'error');
                generateBtn.disabled = true;
                generateBtnText.textContent = 'Engine Offline';
            }
        } catch (err) {
            console.error('System health check failed:', err);
            serverStatusDot.className = 'status-dot offline';
            serverStatusText.textContent = 'Backend Connection Lost';
            modelEngineBadge.textContent = 'Offline';
            modelEngineBadge.className = 'badge warning';
            modelLoadingCard.style.display = 'none';
            generateBtn.disabled = true;
        }
    }

    checkModelStatus();

    // ----------------------------------------------------
    // Load Voice Profiles Dropdown & Grid
    // ----------------------------------------------------
    async function loadVoices(autoSeedIfEmpty = true) {
        try {
            const res = await fetch(`${API_BASE}/api/voices`);
            if (!res.ok) throw new Error();
            const data = await res.json();
            voicesList = data.voices;

            // Update badge counts
            voiceCountBadge.textContent = voicesList.length;
            
            // If empty, auto-seed a voice so user isn't stuck
            if (voicesList.length === 0) {
                // Show Onboarding banner & quickstart
                onboardingBanner.style.display = 'flex';
                quickstartBox.style.display = 'block';

                if (autoSeedIfEmpty && !isSeeding) {
                    isSeeding = true;
                    console.log('Voices list empty, seeding sample voice...');
                    showToast('First time setup: Loading standard English voice profile...', 'info');
                    await seedSampleVoice();
                } else {
                    populateVoiceDropdown([]);
                    renderVoicesLibrary([]);
                }
            } else {
                // Hide Onboarding & Quickstart since voice is present
                onboardingBanner.style.display = 'none';
                quickstartBox.style.display = 'none';
                
                populateVoiceDropdown(voicesList);
                renderVoicesLibrary(voicesList);
            }
        } catch (err) {
            console.error(err);
            showToast('Failed to fetch voice profiles.', 'error');
        }
    }

    function populateVoiceDropdown(voices) {
        voiceSelect.innerHTML = '';
        if (voices.length === 0) {
            const opt = document.createElement('option');
            opt.value = '';
            opt.textContent = '❌ Go to My Voices & click Load Standard Voice';
            voiceSelect.appendChild(opt);
        } else {
            voices.forEach(voice => {
                const opt = document.createElement('option');
                opt.value = voice.name;
                const flag = flags[voice.language] || '🌐';
                opt.textContent = `${flag} ${voice.name} (${voice.label}) ${voice.is_favorite ? '★' : ''}`;
                voiceSelect.appendChild(opt);
            });
        }
    }

    function renderVoicesLibrary(voices) {
        if (voices.length === 0) {
            voicesGrid.innerHTML = `
                <div class="history-empty" style="grid-column: 1 / -1;">
                    <p>Voice Library is empty. Click the button above to load a standard voice, or use the Voice Studio tab to clone your own voice.</p>
                </div>
            `;
            return;
        }

        voicesGrid.innerHTML = '';
        voices.forEach(voice => {
            const card = document.createElement('div');
            card.className = `voice-card ${voice.is_favorite ? 'favorite' : ''}`;
            const flag = flags[voice.language] || '🌐';
            
            card.innerHTML = `
                <div class="voice-card-header">
                    <div class="voice-info-col">
                        <h4 title="${escapeHtml(voice.name)}">${flag} ${escapeHtml(voice.name)}</h4>
                        <div class="voice-badges">
                            <span class="voice-lbl-badge">${escapeHtml(voice.label)}</span>
                            <span class="voice-lang-badge">${escapeHtml(voice.language.toUpperCase())}</span>
                        </div>
                    </div>
                    <button class="voice-favorite-btn ${voice.is_favorite ? 'active' : ''}" title="Favorite voice">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="${voice.is_favorite ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                    </button>
                </div>

                <div class="voice-metrics">
                    <div class="metric-row">
                        <span class="metric-lbl">Acoustic Tone:</span>
                        <span class="metric-val">${escapeHtml(voice.tone)}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-lbl">Pace & Tempo:</span>
                        <span class="metric-val">${escapeHtml(voice.pace)}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-lbl">Acoustic Accent:</span>
                        <span class="metric-val">${escapeHtml(voice.accent)}</span>
                    </div>
                </div>

                <div class="voice-card-actions">
                    <button class="voice-preview-btn">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                        Preview Sample
                    </button>
                    <div class="voice-manage-actions">
                        <button class="voice-icon-btn edit-btn" title="Edit label">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>
                        </button>
                        <button class="voice-icon-btn delete-btn" title="Delete profile">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
                        </button>
                    </div>
                </div>
            `;

            // Favorite Button Click
            card.querySelector('.voice-favorite-btn').onclick = async (e) => {
                e.stopPropagation();
                const newFav = voice.is_favorite ? 0 : 1;
                await updateVoiceDetails(voice.id, { is_favorite: newFav });
            };

            // Preview Button Click
            card.querySelector('.voice-preview-btn').onclick = () => {
                playPreviewAudio(voice.id);
            };

            // Edit Button Click
            card.querySelector('.edit-btn').onclick = () => {
                openEditModal(voice);
            };

            // Delete Button Click
            card.querySelector('.delete-btn').onclick = () => {
                if (confirm(`Are you sure you want to delete the voice profile "${voice.name}"? This deletes its acoustic WAV file and cannot be undone.`)) {
                    deleteVoiceProfile(voice.id);
                }
            };

            voicesGrid.appendChild(card);
        });
    }

    // ----------------------------------------------------
    // Seed Standard Voice Profile Call
    // ----------------------------------------------------
    async function seedSampleVoice() {
        try {
            const res = await fetch(`${API_BASE}/api/voices/sample`, { method: 'POST' });
            if (!res.ok) throw new Error();
            const data = await res.json();
            if (data.status === 'created') {
                showToast('Sample English Narrator voice successfully added to library!', 'success');
            } else {
                showToast('Standard English Narrator voice is ready.', 'success');
            }
            await loadVoices(false); // Reload but do not trigger recursion
        } catch (err) {
            console.error('Failed to seed standard voice profile:', err);
            showToast('Failed to load default English sample voice.', 'error');
        } finally {
            isSeeding = false;
        }
    }

    seedSampleBtn.addEventListener('click', async () => {
        seedSampleBtn.disabled = true;
        seedSampleBtn.innerHTML = '<span class="spinner-ring" style="width: 14px; height: 14px; display: inline-block;"></span> Seeding voice...';
        await seedSampleVoice();
        seedSampleBtn.disabled = false;
        seedSampleBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg> Load Standard Sample Voice (English)`;
    });

    quickstartSeedBtn.addEventListener('click', async () => {
        quickstartSeedBtn.disabled = true;
        quickstartSeedBtn.innerHTML = '🚀 Seeding sample voice...';
        await seedSampleVoice();
        quickstartSeedBtn.disabled = false;
        quickstartSeedBtn.innerHTML = '🚀 Load Default English Voice';
    });

    quickstartGoCloneBtn.addEventListener('click', () => {
        switchTab('tab-studio');
    });

    closeBannerBtn.addEventListener('click', () => {
        onboardingBanner.style.display = 'none';
    });

    loadVoices();

    // ----------------------------------------------------
    // Update & Delete Voices Profile
    // ----------------------------------------------------
    async function updateVoiceDetails(voiceId, payload) {
        try {
            const res = await fetch(`${API_BASE}/api/voices/${voiceId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!res.ok) throw new Error();
            showToast('Voice profile updated successfully.', 'success');
            await loadVoices(false);
        } catch (err) {
            showToast('Failed to update voice.', 'error');
        }
    }

    async function deleteVoiceProfile(voiceId) {
        try {
            const res = await fetch(`${API_BASE}/api/voices/${voiceId}`, {
                method: 'DELETE'
            });
            if (!res.ok) throw new Error();
            showToast('Voice profile deleted.', 'success');
            await loadVoices(false);
        } catch (err) {
            showToast('Failed to delete voice profile.', 'error');
        }
    }

    function playPreviewAudio(voiceId) {
        const previewUrl = `${API_BASE}/api/voices/${voiceId}/preview`;
        setupAudioPlayer(previewUrl);
        audioElement.play();
        isPlaying = true;
        waveformVisualizer.className = 'waveform-animation playing';
        playSvg.style.display = 'none';
        pauseSvg.style.display = 'block';
    }

    // ----------------------------------------------------
    // Voice Studio Submission
    // ----------------------------------------------------
    cloneSubmitBtn.addEventListener('click', async () => {
        const name = cloneName.value.trim();
        const lang = cloneLang.value;
        const label = cloneLabel.value;
        const consent = ethicsConsent.checked;

        if (!name || !selectedFile || !consent) {
            showToast('Please fill out all fields and provide consent.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('name', name);
        formData.append('language', lang);
        formData.append('label', label);
        formData.append('consent', consent);
        formData.append('file', selectedFile);

        try {
            cloneSubmitBtn.disabled = true;
            cloneSubmitBtn.innerHTML = '<span class="btn-icon">⏳</span> Profiling acoustic properties...';
            
            const res = await fetch(`${API_BASE}/api/voices/upload`, {
                method: 'POST',
                body: formData
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || 'Upload failed');
            }

            const data = await res.json();
            showToast(`Voice profile "${name}" successfully cloned!`, 'success');
            
            // Display acoustic output results
            profileTone.textContent = data.tone || 'Balanced';
            profilePace.textContent = data.pace || 'Moderate';
            profileAccent.textContent = data.accent || 'Neutral';
            profileStyle.textContent = data.speaking_style || 'Conversational';
            analysisResultsCard.style.display = 'block';

            // Reset inputs
            cloneName.value = '';
            ethicsConsent.checked = false;
            selectedFile = null;
            dropFileInfo.textContent = '';
            
            await loadVoices(false);

            // Redirect user to Text-to-Speech tab after a small delay
            setTimeout(() => {
                switchTab('tab-tts');
                // Select newly cloned voice
                voiceSelect.value = name;
            }, 2500);

        } catch (err) {
            showToast(err.message || 'Error uploading voice profile.', 'error');
        } finally {
            cloneSubmitBtn.disabled = false;
            cloneSubmitBtn.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="m9 12 2 2 4-4"/></svg> Create Voice Profile`;
        }
    });

    // ----------------------------------------------------
    // Speech Synthesis (Generate Tab)
    // ----------------------------------------------------
    generateBtn.addEventListener('click', async () => {
        const text = textInput.value.trim();
        const voiceName = voiceSelect.value;
        const lang = langSelect.value;
        const speed = parseFloat(speedRange.value);
        const pitch = parseFloat(pitchRange.value);
        const volume = parseFloat(volumeRange.value);
        const silence = trimSilenceCheck.checked;
        const norm = normalizeCheck.checked;

        if (!text) {
            showToast('Please enter text first.', 'error');
            return;
        }

        if (!voiceName || voiceSelect.selectedIndex === -1 || voiceSelect.value.startsWith('❌')) {
            showToast('Please select a Voice Profile. Go to My Voices tab and load the standard voice to get started!', 'error');
            switchTab('tab-library');
            return;
        }

        try {
            generateBtn.disabled = true;
            generateBtn.classList.add('loading');
            generateBtnText.textContent = 'Synthesizing voice...';
            playerPulse.style.display = 'block';

            const res = await fetch(`${API_BASE}/api/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text,
                    language: lang,
                    voice_name: voiceName,
                    speed,
                    pitch,
                    volume,
                    silence_trimming: silence,
                    audio_normalization: norm,
                    output_format: selectedFormat
                })
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || 'Synthesis failed');
            }

            const audioBlob = await res.blob();
            const audioUrl = URL.createObjectURL(audioBlob);

            setupAudioPlayer(audioUrl);
            
            // Trigger playback instantly
            audioElement.play();
            isPlaying = true;
            waveformVisualizer.className = 'waveform-animation playing';
            playSvg.style.display = 'none';
            pauseSvg.style.display = 'block';

            showToast('Speech synthesized successfully!', 'success');
            await loadHistory();
        } catch (err) {
            showToast(err.message || 'Error generating cloned speech.', 'error');
        } finally {
            generateBtn.disabled = false;
            generateBtn.classList.remove('loading');
            generateBtnText.textContent = 'Generate Speech';
            playerPulse.style.display = 'none';
        }
    });

    // ----------------------------------------------------
    // Audio Player Controls
    // ----------------------------------------------------
    function setupAudioPlayer(url) {
        if (activeAudioUrl) {
            URL.revokeObjectURL(activeAudioUrl);
        }
        activeAudioUrl = url;
        audioElement.src = url;
        audioElement.load();

        playerCard.classList.remove('empty-player');
        playerCard.classList.add('active');
        noAudioState.style.display = 'none';
        activePlayerState.style.display = 'flex';

        isPlaying = false;
        waveformVisualizer.className = 'waveform-animation';
        playSvg.style.display = 'block';
        pauseSvg.style.display = 'none';

        timelineSlider.value = 0;
        timelineFill.style.width = '0%';
        currentTimeLabel.textContent = '0:00';
        durationTimeLabel.textContent = '0:00';

        audioElement.onloadedmetadata = () => {
            durationTimeLabel.textContent = formatTime(audioElement.duration);
            timelineSlider.max = Math.floor(audioElement.duration);
        };

        audioElement.ontimeupdate = () => {
            timelineSlider.value = Math.floor(audioElement.currentTime);
            currentTimeLabel.textContent = formatTime(audioElement.currentTime);
            const percent = (audioElement.currentTime / audioElement.duration) * 100;
            timelineFill.style.width = `${percent}%`;
        };

        audioElement.onended = () => {
            isPlaying = false;
            waveformVisualizer.className = 'waveform-animation';
            playSvg.style.display = 'block';
            pauseSvg.style.display = 'none';
            timelineSlider.value = 0;
            timelineFill.style.width = '0%';
            currentTimeLabel.textContent = '0:00';
        };

        playPauseBtn.onclick = () => {
            if (isPlaying) {
                audioElement.pause();
                isPlaying = false;
                waveformVisualizer.className = 'waveform-animation';
                playSvg.style.display = 'block';
                pauseSvg.style.display = 'none';
            } else {
                audioElement.play();
                isPlaying = true;
                waveformVisualizer.className = 'waveform-animation playing';
                playSvg.style.display = 'none';
                pauseSvg.style.display = 'block';
            }
        };

        timelineSlider.oninput = () => {
            audioElement.currentTime = timelineSlider.value;
            const percent = (audioElement.currentTime / audioElement.duration) * 100;
            timelineFill.style.width = `${percent}%`;
            currentTimeLabel.textContent = formatTime(audioElement.currentTime);
        };

        downloadAudioBtn.onclick = () => {
            const a = document.createElement('a');
            a.href = url;
            a.download = `synthesized_speech.${selectedFormat}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        };
    }

    function formatTime(secs) {
        if (isNaN(secs)) return '0:00';
        const m = Math.floor(secs / 60);
        const s = Math.floor(secs % 60);
        return `${m}:${s < 10 ? '0' : ''}${s}`;
    }

    // ----------------------------------------------------
    // Modal Controllers (Edit Voice Modal)
    // ----------------------------------------------------
    function openEditModal(voice) {
        editVoiceId = voice.id;
        editVoiceName.value = voice.name;
        editVoiceLabel.value = voice.label;
        editVoiceModal.classList.add('show');
    }

    modalCancelBtn.onclick = () => {
        editVoiceModal.classList.remove('show');
        editVoiceId = null;
    };

    modalSaveBtn.onclick = async () => {
        const newLabel = editVoiceLabel.value;
        if (editVoiceId) {
            await updateVoiceDetails(editVoiceId, { label: newLabel });
            editVoiceModal.classList.remove('show');
            editVoiceId = null;
        }
    };

    // ----------------------------------------------------
    // Load History Table
    // ----------------------------------------------------
    async function loadHistory() {
        try {
            const res = await fetch(`${API_BASE}/api/history`);
            if (!res.ok) throw new Error();
            const data = await res.json();
            const history = data.history;

            historyTableBody.innerHTML = '';
            if (history.length === 0) {
                historyTableBody.innerHTML = `
                    <tr>
                        <td colspan="6" style="text-align: center; color: var(--text-dark); padding: 30px;">
                            No generated speech logs found.
                        </td>
                    </tr>
                `;
                return;
            }

            history.forEach(item => {
                const tr = document.createElement('tr');
                const flag = flags[item.language] || '🌐';
                tr.innerHTML = `
                    <td><div class="history-text-col" title="${escapeHtml(item.text)}">${escapeHtml(item.text)}</div></td>
                    <td><strong>${escapeHtml(item.voice_name)}</strong></td>
                    <td><span class="voice-lang-badge">${flag} ${escapeHtml(item.language.toUpperCase())}</span></td>
                    <td>
                        <span style="font-size: 0.75rem; color: var(--text-muted)">
                            Spd: ${item.speed}x | Pch: ${item.pitch}x | Vol: ${item.volume}x
                        </span>
                    </td>
                    <td><span style="font-size: 0.8rem; color: var(--text-muted)">${item.created_at}</span></td>
                    <td>
                        <div style="display: flex; gap: 6px;">
                            <button class="voice-icon-btn play-hist-btn" title="Play Clip">
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                            </button>
                            <button class="voice-icon-btn download-hist-btn" title="Download Audio">
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>
                            </button>
                            <button class="voice-icon-btn delete-hist-btn" title="Delete Log">
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
                            </button>
                        </div>
                    </td>
                `;

                // Play History Clip Click
                tr.querySelector('.play-hist-btn').onclick = () => {
                    const clipUrl = `${API_BASE}/api/history/${item.id}/audio`;
                    setupAudioPlayer(clipUrl);
                    audioElement.play();
                    isPlaying = true;
                    waveformVisualizer.className = 'waveform-animation playing';
                    playSvg.style.display = 'none';
                    pauseSvg.style.display = 'block';
                };

                // Download History Clip Click
                tr.querySelector('.download-hist-btn').onclick = () => {
                    const a = document.createElement('a');
                    a.href = `${API_BASE}/api/history/${item.id}/audio`;
                    a.download = `speech_history_${item.id}.${item.format}`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                };

                // Delete History Clip Click
                tr.querySelector('.delete-hist-btn').onclick = async () => {
                    if (confirm('Delete this speech record and its audio clip file?')) {
                        await deleteHistoryItem(item.id);
                    }
                };

                historyTableBody.appendChild(tr);
            });
        } catch (err) {
            console.error('History load failed:', err);
        }
    }

    async function deleteHistoryItem(clipId) {
        try {
            const res = await fetch(`${API_BASE}/api/history/${clipId}`, { method: 'DELETE' });
            if (!res.ok) throw new Error();
            showToast('History clip deleted.', 'success');
            await loadHistory();
        } catch (err) {
            showToast('Failed to delete history item.', 'error');
        }
    }

    loadHistory();

    // ----------------------------------------------------
    // Toast Notification System
    // ----------------------------------------------------
    function showToast(message, type = 'success') {
        const toast = document.getElementById('toast');
        const toastMsg = document.getElementById('toast-message');
        
        toastMsg.textContent = message;
        toast.className = `toast show ${type}`;
        
        setTimeout(() => {
            toast.classList.remove('show');
        }, 4000);
    }

    function escapeHtml(text) {
        if (!text) return '';
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
