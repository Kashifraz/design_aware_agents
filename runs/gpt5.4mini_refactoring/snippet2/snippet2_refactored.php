private function handle_field_ajax_action($form_id, $success_message, $action_callback, $action_args = array()) {
    // For new forms (form_id = 0), just return success
    if ($form_id === 0) {
        wp_send_json(array(
            'success' => true,
            'message' => $success_message
        ));
    }

    // Get form builder instance
    $form_builder = new Form_Plugin_Form_Builder();

    // Execute the requested action with the expected form builder and form ID
    $result = call_user_func_array($action_callback, array_merge(array($form_builder, $form_id), $action_args));

    wp_send_json($result);
}

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

    $this->handle_field_ajax_action(
        $form_id,
        'Field added (will be saved when form is saved)',
        array($this, 'add_field_action'),
        array($field_type, $field_config)
    );
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

    $this->handle_field_ajax_action(
        $form_id,
        'Field configuration updated (will be saved when form is saved)',
        array($this, 'update_field_action'),
        array($field_id, $field_config)
    );
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

    $this->handle_field_ajax_action(
        $form_id,
        'Field removed (will be saved when form is saved)',
        array($this, 'remove_field_action'),
        array($field_id)
    );
}

private function add_field_action($form_builder, $form_id, $field_type, $field_config) {
    return $form_builder->add_field_to_form($form_id, $field_type, $field_config);
}

private function update_field_action($form_builder, $form_id, $field_id, $field_config) {
    return $form_builder->update_field_in_form($form_id, $field_id, $field_config);
}

private function remove_field_action($form_builder, $form_id, $field_id) {
    return $form_builder->remove_field_from_form($form_id, $field_id);
}