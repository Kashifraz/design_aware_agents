        /**
     * AJAX: Delete form
     */
    public function ajax_delete_form() {
        // Verify nonce
        if (!wp_verify_nonce($_POST['nonce'], 'form_plugin_nonce')) {
            wp_die(__('Security check failed.', 'form-plugin'));
        }
        
        // Check user capabilities
        if (!current_user_can('manage_options')) {
            wp_die(__('Insufficient permissions.', 'form-plugin'));
        }
        
        $form_id = intval($_POST['form_id']);
        $result = $this->form_builder->delete_form($form_id);
        
        if ($result['success']) {
            wp_send_json_success(array(
                'message' => $result['message']
            ));
        } else {
            wp_send_json_error(array(
                'message' => $result['message']
            ));
        }
    }
    
    /**
     * AJAX: Duplicate form
     */
    public function ajax_duplicate_form() {
        // Verify nonce
        if (!wp_verify_nonce($_POST['nonce'], 'form_plugin_nonce')) {
            wp_die(__('Security check failed.', 'form-plugin'));
        }
        
        // Check user capabilities
        if (!current_user_can('manage_options')) {
            wp_die(__('Insufficient permissions.', 'form-plugin'));
        }
        
        $form_id = intval($_POST['form_id']);
        $result = $this->form_builder->duplicate_form($form_id);
        
        if ($result['success']) {
            wp_send_json_success(array(
                'message' => $result['message'],
                'new_form_id' => $result['new_form_id']
            ));
        } else {
            wp_send_json_error(array(
                'message' => $result['message']
            ));
        }
    }
    
    /**
     * AJAX: Update form status
     */
    public function ajax_update_status() {
        // Verify nonce
        if (!wp_verify_nonce($_POST['nonce'], 'form_plugin_nonce')) {
            wp_die(__('Security check failed.', 'form-plugin'));
        }
        
        // Check user capabilities
        if (!current_user_can('manage_options')) {
            wp_die(__('Insufficient permissions.', 'form-plugin'));
        }
        
        $form_id = intval($_POST['form_id']);
        $status = sanitize_text_field($_POST['status']);
        
        $result = $this->form_builder->update_form_status($form_id, $status);
        
        if ($result['success']) {
            wp_send_json_success(array(
                'message' => $result['message']
            ));
        } else {
            wp_send_json_error(array(
                'message' => $result['message']
            ));
        }
    }
    
    /**
     * AJAX: Get form data
     */
    public function ajax_get_form() {
        // Verify nonce
        if (!wp_verify_nonce($_POST['nonce'], 'form_plugin_nonce')) {
            wp_die(__('Security check failed.', 'form-plugin'));
        }
        
        // Check user capabilities
        if (!current_user_can('manage_options')) {
            wp_die(__('Insufficient permissions.', 'form-plugin'));
        }
        
        $form_id = intval($_POST['form_id']);
        $result = $this->form_builder->get_form($form_id);
        
        if ($result['success']) {
            wp_send_json_success(array(
                'form' => $result['form']
            ));
        } else {
            wp_send_json_error(array(
                'message' => $result['message']
            ));
        }
    }
    