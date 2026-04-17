public function handle_form_submission() {
        // Get form ID
        $form_id = isset($_POST['form_id']) ? intval($_POST['form_id']) : 0;
        
        if ($form_id === 0) {
            wp_send_json_error(array('message' => __('Invalid form ID.', 'form-plugin')));
        }
        
        // Verify nonce
        $nonce = isset($_POST['form_plugin_nonce']) ? $_POST['form_plugin_nonce'] : '';
        $nonce_action = 'form_plugin_submit_' . $form_id;
        
        if (!wp_verify_nonce($nonce, $nonce_action)) {
            wp_send_json_error(array('message' => __('Security check failed.', 'form-plugin')));
        }
        
        // Get form data
        $form = $this->database->get_form($form_id);
        
        if (!$form) {
            wp_send_json_error(array('message' => __('Form not found.', 'form-plugin')));
        }
        
        // Validate captcha
        $captcha_answer = intval($_POST['captcha_answer']);
        $captcha_input = intval($_POST['captcha_input']);
        
        if ($captcha_input !== $captcha_answer) {
            wp_send_json_error(array('message' => __('Incorrect answer to the math problem.', 'form-plugin')));
        }
        
        // Get field configuration
        $fields = array();
        if (!empty($form->form_data) && is_array($form->form_data)) {
            if (isset($form->form_data['fields']) && is_array($form->form_data['fields'])) {
                $fields = $form->form_data['fields'];
            }
        }
        
        // Collect and validate form data
        $submission_data = array();
        $errors = array();
        
        foreach ($fields as $field) {
            if (!is_array($field)) continue;
            
            $field_name = $field['id'];
            $field_value = isset($_POST[$field_name]) ? $_POST[$field_name] : '';
            
            // Validate required fields
            if ($field['required'] && empty($field_value)) {
                $errors[] = sprintf(__('%s is required.', 'form-plugin'), $field['label']);
                continue;
            }
            
            // Validate email fields
            if ($field['type'] === 'email' && !empty($field_value) && !is_email($field_value)) {
                $errors[] = sprintf(__('%s must be a valid email address.', 'form-plugin'), $field['label']);
                continue;
            }
            
            $submission_data[$field_name] = array(
                'label' => $field['label'],
                'value' => sanitize_text_field($field_value),
                'type' => $field['type']
            );
        }
        
        // Return errors if any
        if (!empty($errors)) {
            wp_send_json_error(array('message' => implode('<br>', $errors)));
        }
        
        // Save submission
        $submission_id = $this->database->save_submission($form_id, $submission_data);
        
        if ($submission_id) {
            wp_send_json_success(array('message' => __('Form submitted successfully!', 'form-plugin')));
        } else {
            wp_send_json_error(array('message' => __('Failed to save submission.', 'form-plugin')));
        }
    }