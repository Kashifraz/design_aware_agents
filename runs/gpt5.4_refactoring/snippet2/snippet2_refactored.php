public function ajax_add_field() {
        $this->verify_ajax_request();
        
        $form_id = intval($_POST['form_id']);
        $field_type = sanitize_text_field($_POST['field_type']);
        $field_config = $_POST['field_config'];
        
        if ($this->is_new_form($form_id)) {
            $this->send_new_form_response('Field added (will be saved when form is saved)');
            return;
        }
        
        $form_builder = $this->create_form_builder();
        $result = $form_builder->add_field_to_form($form_id, $field_type, $field_config);
        
        wp_send_json($result);
    }
    
    /**
     * AJAX handler for updating field in form
     */
    public function ajax_update_field() {
        $this->verify_ajax_request();
        
        $form_id = intval($_POST['form_id']);
        $field_id = sanitize_text_field($_POST['field_id']);
        $field_config = $_POST['field_config'];
        
        if ($this->is_new_form($form_id)) {
            $this->send_new_form_response('Field configuration updated (will be saved when form is saved)');
            return;
        }
        
        $form_builder = $this->create_form_builder();
        $result = $form_builder->update_field_in_form($form_id, $field_id, $field_config);
        
        wp_send_json($result);
    }
    
    /**
     * AJAX handler for removing field from form
     */
    public function ajax_remove_field() {
        $this->verify_ajax_request();
        
        $form_id = intval($_POST['form_id']);
        $field_id = sanitize_text_field($_POST['field_id']);
        
        if ($this->is_new_form($form_id)) {
            $this->send_new_form_response('Field removed (will be saved when form is saved)');
            return;
        }
        
        $form_builder = $this->create_form_builder();
        $result = $form_builder->remove_field_from_form($form_id, $field_id);
        
        wp_send_json($result);
    }

    private function verify_ajax_request() {
        // Verify nonce
        if (!wp_verify_nonce($_POST['nonce'], 'form_plugin_nonce')) {
            wp_die('Security check failed');
        }
        
        // Check user capabilities
        if (!current_user_can('manage_options')) {
            wp_die('Insufficient permissions');
        }
    }

    private function is_new_form($form_id) {
        return $form_id === 0;
    }

    private function send_new_form_response($message) {
        wp_send_json(array(
            'success' => true,
            'message' => $message
        ));
    }

    private function create_form_builder() {
        return new Form_Plugin_Form_Builder();
    }