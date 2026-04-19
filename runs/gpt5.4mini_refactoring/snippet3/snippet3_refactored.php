/**
 * Verify AJAX request security and permissions.
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
 * Send standardized AJAX success response.
 */
private function send_ajax_success($result, $data = array()) {
    wp_send_json_success(array_merge(array(
        'message' => $result['message']
    ), $data));
}

/**
 * Send standardized AJAX error response.
 */
private function send_ajax_error($result) {
    wp_send_json_error(array(
        'message' => $result['message']
    ));
}

/**
 * AJAX: Delete form
 */
public function ajax_delete_form() {
    $this->validate_ajax_request();

    $form_id = intval($_POST['form_id']);
    $result = $this->form_builder->delete_form($form_id);

    if ($result['success']) {
        $this->send_ajax_success($result);
    } else {
        $this->send_ajax_error($result);
    }
}

/**
 * AJAX: Duplicate form
 */
public function ajax_duplicate_form() {
    $this->validate_ajax_request();

    $form_id = intval($_POST['form_id']);
    $result = $this->form_builder->duplicate_form($form_id);

    if ($result['success']) {
        $this->send_ajax_success($result, array(
            'new_form_id' => $result['new_form_id']
        ));
    } else {
        $this->send_ajax_error($result);
    }
}

/**
 * AJAX: Update form status
 */
public function ajax_update_status() {
    $this->validate_ajax_request();

    $form_id = intval($_POST['form_id']);
    $status = sanitize_text_field($_POST['status']);

    $result = $this->form_builder->update_form_status($form_id, $status);

    if ($result['success']) {
        $this->send_ajax_success($result);
    } else {
        $this->send_ajax_error($result);
    }
}

/**
 * AJAX: Get form data
 */
public function ajax_get_form() {
    $this->validate_ajax_request();

    $form_id = intval($_POST['form_id']);
    $result = $this->form_builder->get_form($form_id);

    if ($result['success']) {
        wp_send_json_success(array(
            'form' => $result['form']
        ));
    } else {
        $this->send_ajax_error($result);
    }
}