<?php

if (!defined('ABSPATH')) {
    exit;
}

class AST_Admin_Settings {
    private static $instance = null;

    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    private function __construct() {
        add_action('admin_menu', array($this, 'add_admin_menu'));
        add_action('admin_init', array($this, 'register_settings'));
    }

    public function add_admin_menu() {
        add_options_page(
            __('Azure Speech Transcribe Settings', 'azure-speech-transcribe'),
            __('Azure Speech Transcribe', 'azure-speech-transcribe'),
            'manage_options',
            'azure-speech-transcribe',
            array($this, 'render_settings_page')
        );
    }

    public function register_settings() {
        register_setting('ast_settings', 'ast_password');
        register_setting('ast_settings', 'ast_api_url');
        register_setting('ast_settings', 'ast_max_file_size');

        add_settings_section(
            'ast_main_section',
            __('Main Settings', 'azure-speech-transcribe'),
            null,
            'azure-speech-transcribe'
        );

        add_settings_field(
            'ast_password',
            __('Access Password', 'azure-speech-transcribe'),
            array($this, 'render_password_field'),
            'azure-speech-transcribe',
            'ast_main_section'
        );

        add_settings_field(
            'ast_api_url',
            __('Flask API URL', 'azure-speech-transcribe'),
            array($this, 'render_api_url_field'),
            'azure-speech-transcribe',
            'ast_main_section'
        );

        add_settings_field(
            'ast_max_file_size',
            __('Max File Size (MB)', 'azure-speech-transcribe'),
            array($this, 'render_max_file_size_field'),
            'azure-speech-transcribe',
            'ast_main_section'
        );
    }

    public function render_settings_page() {
        if (!current_user_can('manage_options')) {
            return;
        }

        if (isset($_GET['settings-updated'])) {
            add_settings_error('ast_messages', 'ast_message', __('Settings Saved', 'azure-speech-transcribe'), 'updated');
        }

        settings_errors('ast_messages');
        ?>
        <div class="wrap">
            <h1><?php echo esc_html(get_admin_page_title()); ?></h1>
            <form action="options.php" method="post">
                <?php
                settings_fields('ast_settings');
                do_settings_sections('azure-speech-transcribe');
                submit_button(__('Save Settings', 'azure-speech-transcribe'));
                ?>
            </form>
        </div>
        <?php
    }

    public function render_password_field() {
        $password = get_option('ast_password', '');
        ?>
        <input type="text" name="ast_password" value="<?php echo esc_attr($password); ?>" class="regular-text" />
        <p class="description"><?php _e('Password required to access the transcription form', 'azure-speech-transcribe'); ?></p>
        <?php
    }

    public function render_api_url_field() {
        $api_url = get_option('ast_api_url', 'http://localhost:5000');
        ?>
        <input type="url" name="ast_api_url" value="<?php echo esc_attr($api_url); ?>" class="regular-text" />
        <p class="description"><?php _e('URL of the Flask API server (e.g., http://localhost:5000)', 'azure-speech-transcribe'); ?></p>
        <?php
    }

    public function render_max_file_size_field() {
        $max_size = get_option('ast_max_file_size', 50);
        ?>
        <input type="number" name="ast_max_file_size" value="<?php echo esc_attr($max_size); ?>" min="1" max="500" />
        <p class="description"><?php _e('Maximum file size in megabytes', 'azure-speech-transcribe'); ?></p>
        <?php
    }
}
