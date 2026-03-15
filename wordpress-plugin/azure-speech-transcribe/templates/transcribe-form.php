<div class="ast-container">
    <div class="ast-card">
        <h2><?php _e('Audio Transcription', 'azure-speech-transcribe'); ?></h2>
        
        <!-- Password Section -->
        <div id="ast-password-section" class="ast-section">
            <label for="ast-password"><?php _e('Enter Password', 'azure-speech-transcribe'); ?></label>
            <input type="password" id="ast-password" class="ast-input" placeholder="<?php esc_attr_e('Password', 'azure-speech-transcribe'); ?>" />
            <button id="ast-validate-btn" class="ast-button ast-button-primary"><?php _e('Validate', 'azure-speech-transcribe'); ?></button>
            <div id="ast-password-error" class="ast-error"></div>
        </div>

        <!-- Upload Section (hidden initially) -->
        <div id="ast-upload-section" class="ast-section" style="display: none;">
            <div class="ast-upload-area" id="ast-upload-area">
                <input type="file" id="ast-file-input" accept=".wav,.m4a" style="display: none;" />
                <div class="ast-upload-content">
                    <svg class="ast-upload-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <p class="ast-upload-text"><?php _e('Drag and drop audio file here', 'azure-speech-transcribe'); ?></p>
                    <p class="ast-upload-subtext"><?php _e('or', 'azure-speech-transcribe'); ?></p>
                    <button type="button" id="ast-select-file-btn" class="ast-button ast-button-secondary"><?php _e('Select File', 'azure-speech-transcribe'); ?></button>
                    <p class="ast-upload-info"><?php _e('Supported formats: WAV, M4A', 'azure-speech-transcribe'); ?></p>
                </div>
                <div id="ast-selected-file" class="ast-selected-file" style="display: none;"></div>
            </div>

            <button id="ast-upload-btn" class="ast-button ast-button-primary" style="display: none;"><?php _e('Start Transcription', 'azure-speech-transcribe'); ?></button>

            <!-- Progress Section -->
            <div id="ast-progress-section" style="display: none;">
                <div class="ast-progress-bar">
                    <div id="ast-progress-fill" class="ast-progress-fill"></div>
                </div>
                <p id="ast-status-text" class="ast-status-text"></p>
            </div>

            <!-- Transcription Display -->
            <div id="ast-transcription-section" style="display: none;">
                <div class="ast-transcription-header">
                    <h3><?php _e('Transcription', 'azure-speech-transcribe'); ?></h3>
                    <div class="ast-actions">
                        <button id="ast-copy-btn" class="ast-button ast-button-small" title="<?php esc_attr_e('Copy to clipboard', 'azure-speech-transcribe'); ?>">
                            <?php _e('Copy', 'azure-speech-transcribe'); ?>
                        </button>
                        <button id="ast-download-btn" class="ast-button ast-button-small" style="display: none;">
                            <?php _e('Download', 'azure-speech-transcribe'); ?>
                        </button>
                    </div>
                </div>
                <textarea id="ast-transcription-text" class="ast-transcription-text" readonly></textarea>
            </div>

            <div id="ast-error-section" class="ast-error" style="display: none;"></div>
        </div>
    </div>
</div>
