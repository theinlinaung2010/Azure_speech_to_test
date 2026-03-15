<?php
/**
 * Plugin Name: Azure Speech Transcribe
 * Plugin URI: https://example.com/azure-speech-transcribe
 * Description: Password-protected audio file transcription using Azure Speech-to-Text with real-time streaming
 * Version: 1.0.0
 * Author: Your Name
 * License: GPL v2 or later
 */

if (!defined('ABSPATH')) {
    exit;
}

define('AST_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('AST_PLUGIN_URL', plugin_dir_url(__FILE__));
define('AST_VERSION', '1.0.0');

// Include required files
require_once AST_PLUGIN_DIR . 'includes/class-admin-settings.php';
require_once AST_PLUGIN_DIR . 'includes/class-shortcode.php';
require_once AST_PLUGIN_DIR . 'includes/class-ajax-handler.php';

class Azure_Speech_Transcribe {
    private static $instance = null;

    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    private function __construct() {
        add_action('plugins_loaded', array($this, 'init'));
        register_activation_hook(__FILE__, array($this, 'activate'));
        register_deactivation_hook(__FILE__, array($this, 'deactivate'));
    }

    public function init() {
        // Initialize admin settings
        if (is_admin()) {
            AST_Admin_Settings::get_instance();
        }

        // Initialize shortcode
        AST_Shortcode::get_instance();

        // Initialize AJAX handlers
        AST_Ajax_Handler::get_instance();

        // Load text domain for translations
        load_plugin_textdomain('azure-speech-transcribe', false, dirname(plugin_basename(__FILE__)) . '/languages');
    }

    public function activate() {
        // Set default options
        if (!get_option('ast_password')) {
            update_option('ast_password', wp_generate_password(12, false));
        }
        if (!get_option('ast_api_url')) {
            update_option('ast_api_url', 'http://localhost:5000');
        }
        if (!get_option('ast_max_file_size')) {
            update_option('ast_max_file_size', 50); // MB
        }
    }

    public function deactivate() {
        // Cleanup if needed
    }
}

// Initialize the plugin
Azure_Speech_Transcribe::get_instance();
