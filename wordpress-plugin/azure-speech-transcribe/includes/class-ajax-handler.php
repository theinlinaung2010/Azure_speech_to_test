<?php

if (!defined('ABSPATH')) {
    exit;
}

class AST_Ajax_Handler {
    private static $instance = null;

    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    private function __construct() {
        add_action('wp_ajax_ast_validate_password', array($this, 'validate_password'));
        add_action('wp_ajax_nopriv_ast_validate_password', array($this, 'validate_password'));
    }

    public function validate_password() {
        check_ajax_referer('ast_nonce', 'nonce');

        $password = isset($_POST['password']) ? sanitize_text_field($_POST['password']) : '';
        $stored_password = get_option('ast_password', '');

        // Rate limiting
        $ip = $this->get_client_ip();
        $transient_key = 'ast_rate_limit_' . md5($ip);
        $attempts = get_transient($transient_key);

        if ($attempts !== false && $attempts >= 5) {
            wp_send_json_error(array(
                'message' => __('Too many attempts. Please try again later.', 'azure-speech-transcribe')
            ));
            wp_die();
        }

        if ($password === $stored_password) {
            // Clear rate limit on success
            delete_transient($transient_key);
            
            wp_send_json_success(array(
                'message' => __('Password validated', 'azure-speech-transcribe')
            ));
        } else {
            // Increment attempts
            $new_attempts = ($attempts === false) ? 1 : $attempts + 1;
            set_transient($transient_key, $new_attempts, 300); // 5 minutes
            
            wp_send_json_error(array(
                'message' => __('Invalid password', 'azure-speech-transcribe')
            ));
        }

        wp_die();
    }

    private function get_client_ip() {
        $ip = '';
        if (!empty($_SERVER['HTTP_CLIENT_IP'])) {
            $ip = $_SERVER['HTTP_CLIENT_IP'];
        } elseif (!empty($_SERVER['HTTP_X_FORWARDED_FOR'])) {
            $ip = $_SERVER['HTTP_X_FORWARDED_FOR'];
        } else {
            $ip = $_SERVER['REMOTE_ADDR'];
        }
        return sanitize_text_field($ip);
    }
}
