<?php

if (!defined('ABSPATH')) {
    exit;
}

class AST_Shortcode {
    private static $instance = null;

    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    private function __construct() {
        add_shortcode('azure_transcribe', array($this, 'render_shortcode'));
        add_action('wp_enqueue_scripts', array($this, 'enqueue_assets'));
    }

    public function enqueue_assets() {
        if (has_shortcode(get_post()->post_content ?? '', 'azure_transcribe')) {
            wp_enqueue_style(
                'ast-styles',
                AST_PLUGIN_URL . 'assets/css/transcribe.css',
                array(),
                AST_VERSION
            );

            wp_enqueue_script(
                'ast-script',
                AST_PLUGIN_URL . 'assets/js/transcribe.js',
                array('jquery'),
                AST_VERSION,
                true
            );

            wp_localize_script('ast-script', 'astData', array(
                'ajaxUrl' => admin_url('admin-ajax.php'),
                'nonce' => wp_create_nonce('ast_nonce'),
                'apiUrl' => get_option('ast_api_url', 'http://localhost:5000'),
                'maxFileSize' => (int)get_option('ast_max_file_size', 50) * 1024 * 1024,
                'strings' => array(
                    'passwordRequired' => __('Password is required', 'azure-speech-transcribe'),
                    'fileRequired' => __('Please select a file', 'azure-speech-transcribe'),
                    'invalidFileType' => __('Invalid file type. Only WAV and M4A files allowed', 'azure-speech-transcribe'),
                    'fileTooLarge' => __('File is too large', 'azure-speech-transcribe'),
                    'uploadError' => __('Upload failed. Please try again', 'azure-speech-transcribe'),
                    'connectionError' => __('Connection error. Please check your internet connection', 'azure-speech-transcribe'),
                    'copiedToClipboard' => __('Copied to clipboard!', 'azure-speech-transcribe'),
                )
            ));
        }
    }

    public function render_shortcode($atts) {
        ob_start();
        include AST_PLUGIN_DIR . 'templates/transcribe-form.php';
        return ob_get_clean();
    }
}
