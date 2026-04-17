public function ajax_add_field() {
        // Verify nonce
        if (!wp_verify_nonce($_POST['nonce'], 'form_plugin_nonce')) {
            wp_die('Security check failed');
        }
        
        // Check user capabilities
        if (!current_user_can('manage_options')) {
            wp_die('Insufficient permissions');
        }
        
        $form_id = intval($_POST['form_id']);
        $field_type = sanitize_text_field($_POST['field_type']);
        $field_config = $_POST['field_config'];
        
        // For new forms (form_id = 0), just return success
        if ($form_id === 0) {
            wp_send_json(array(
                'success' => true,
                'message' => 'Field added (will be saved when form is saved)'
            ));
        }
        
        // Get form builder instance
        $form_builder = new Form_Plugin_Form_Builder();
        
        // Add field to form
        $result = $form_builder->add_field_to_form($form_id, $field_type, $field_config);
        
        wp_send_json($result);
    }
    
    /**
     * AJAX handler for updating field in form
     */
    public function ajax_update_field() {
        // Verify nonce
        if (!wp_verify_nonce($_POST['nonce'], 'form_plugin_nonce')) {
            wp_die('Security check failed');
        }
        
        // Check user capabilities
        if (!current_user_can('manage_options')) {
            wp_die('Insufficient permissions');
        }
        
        $form_id = intval($_POST['form_id']);
        $field_id = sanitize_text_field($_POST['field_id']);
        $field_config = $_POST['field_config'];
        
        // For new forms (form_id = 0), just return success
        if ($form_id === 0) {
            wp_send_json(array(
                'success' => true,
                'message' => 'Field configuration updated (will be saved when form is saved)'
            ));
        }
        
        // Get form builder instance
        $form_builder = new Form_Plugin_Form_Builder();
        
        // Update field in form
        $result = $form_builder->update_field_in_form($form_id, $field_id, $field_config);
        
        wp_send_json($result);
    }
    
    /**
     * AJAX handler for removing field from form
     */
    public function ajax_remove_field() {
        // Verify nonce
        if (!wp_verify_nonce($_POST['nonce'], 'form_plugin_nonce')) {
            wp_die('Security check failed');
        }
        
        // Check user capabilities
        if (!current_user_can('manage_options')) {
            wp_die('Insufficient permissions');
        }
        
        $form_id = intval($_POST['form_id']);
        $field_id = sanitize_text_field($_POST['field_id']);
        
        // For new forms (form_id = 0), just return success
        if ($form_id === 0) {
            wp_send_json(array(
                'success' => true,
                'message' => 'Field removed (will be saved when form is saved)'
            ));
        }
        
        // Get form builder instance
        $form_builder = new Form_Plugin_Form_Builder();
        
        // Remove field from form
        $result = $form_builder->remove_field_from_form($form_id, $field_id);
        
        wp_send_json($result);
    }