public function handle_form_submission() {
    $form_id = $this->get_post_form_id();

    if ($form_id === 0) {
        wp_send_json_error(array('message' => __('Invalid form ID.', 'form-plugin')));
    }

    if (!$this->verify_form_nonce($form_id)) {
        wp_send_json_error(array('message' => __('Security check failed.', 'form-plugin')));
    }

    $form = $this->database->get_form($form_id);

    if (!$form) {
        wp_send_json_error(array('message' => __('Form not found.', 'form-plugin')));
    }

    if (!$this->validate_captcha()) {
        wp_send_json_error(array('message' => __('Incorrect answer to the math problem.', 'form-plugin')));
    }

    $fields = $this->get_form_fields($form);
    $validation_result = $this->validate_and_build_submission_data($fields);

    if (!empty($validation_result['errors'])) {
        wp_send_json_error(array('message' => implode('<br>', $validation_result['errors'])));
    }

    $submission_id = $this->database->save_submission($form_id, $validation_result['submission_data']);

    if ($submission_id) {
        wp_send_json_success(array('message' => __('Form submitted successfully!', 'form-plugin')));
    } else {
        wp_send_json_error(array('message' => __('Failed to save submission.', 'form-plugin')));
    }
}

private function get_post_form_id() {
    return isset($_POST['form_id']) ? intval($_POST['form_id']) : 0;
}

private function verify_form_nonce($form_id) {
    $nonce = isset($_POST['form_plugin_nonce']) ? $_POST['form_plugin_nonce'] : '';
    $nonce_action = 'form_plugin_submit_' . $form_id;

    return wp_verify_nonce($nonce, $nonce_action);
}

private function validate_captcha() {
    $captcha_answer = intval($_POST['captcha_answer']);
    $captcha_input = intval($_POST['captcha_input']);

    return $captcha_input === $captcha_answer;
}

private function get_form_fields($form) {
    $fields = array();

    if (!empty($form->form_data) && is_array($form->form_data)) {
        if (isset($form->form_data['fields']) && is_array($form->form_data['fields'])) {
            $fields = $form->form_data['fields'];
        }
    }

    return $fields;
}

private function validate_and_build_submission_data($fields) {
    $submission_data = array();
    $errors = array();

    foreach ($fields as $field) {
        if (!is_array($field)) {
            continue;
        }

        $field_name = $field['id'];
        $field_value = isset($_POST[$field_name]) ? $_POST[$field_name] : '';

        if ($field['required'] && empty($field_value)) {
            $errors[] = sprintf(__('%s is required.', 'form-plugin'), $field['label']);
            continue;
        }

        if ($field['type'] === 'email' && !empty($field_value) && !is_email($field_value)) {
            $errors[] = sprintf(__('%s must be a valid email address.', 'form-plugin'), $field['label']);
            continue;
        }

        $submission_data[$field_name] = array(
            'label' => $field['label'],
            'value' => sanitize_text_field($field_value),
            'type'  => $field['type']
        );
    }

    return array(
        'submission_data' => $submission_data,
        'errors' => $errors
    );
}