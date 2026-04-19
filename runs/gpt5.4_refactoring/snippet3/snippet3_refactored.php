    /**
     * AJAX: Delete form
     */
    public function ajax_delete_form() {
        $this->validate_ajax_request();

        $form_id = $this->get_post_form_id();
        $result = $this->form_builder->delete_form($form_id);

        $this->send_ajax_result($result);
    }
    
    /**
     * AJAX: Duplicate form
     */
    public function ajax_duplicate_form() {
        $this->validate_ajax_request();

        $form_id = $this->get_post_form_id();
        $result = $this->form_builder->duplicate_form($form_id);

        if ($result['success']) {
            $this->send_ajax_success(array(
                'message' => $result['message'],
                'new_form_id' => $result['new_form_id']
            ));
        } else {
            $this->send_ajax_result($result);
        }
    }
    
    /**
     * AJAX: Update form status
     */
    public function ajax_update_status() {
        $this->validate_ajax_request();

        $form_id = $this->get_post_form_id();
        $status = sanitize_text_field($_POST['status']);

        $result = $this->form_builder->update_form_status($form_id, $status);

        $this->send_ajax_result($result);
    }
    
    /**
     * AJAX: Get form data
     */
    public function ajax_get_form() {
        $this->validate_ajax_request();

        $form_id = $this->get_post_form_id();
        $result = $this->form_builder->get_form($form_id);

        if ($result['success']) {
            $this->send_ajax_success(array(
                'form' => $result['form']
            ));
        } else {
            $this->send_ajax_result($result);
        }
    }

    /**
     * Validate common AJAX request requirements.
     */
    private function validate_ajax_request() {
        // Verify nonce
        if (!wp_verify_nonce($_POST['nonce'], 'form_plugin_nonce')) {
            wp_die(__('Security check failed.', 'form-plugin'));
        }

        // Check user capabilities
        if (!current_user_can('manage_options')) {
            wp_die(__('Insufficient permissions.', 'form-plugin'));
        }
    }

    /**
     * Get form ID from POST data.
     *
     * @return int
     */
    private function get_post_form_id() {
        return intval($_POST['form_id']);
    }

    /**
     * Send a standard AJAX result response.
     *
     * @param array $result
     */
    private function send_ajax_result($result) {
        if ($result['success']) {
            $this->send_ajax_success(array(
                'message' => $result['message']
            ));
        } else {
            wp_send_json_error(array(
                'message' => $result['message']
            ));
        }
    }

    /**
     * Send AJAX success response.
     *
     * @param array $data
     */
    private function send_ajax_success($data) {
        wp_send_json_success($data);
    }