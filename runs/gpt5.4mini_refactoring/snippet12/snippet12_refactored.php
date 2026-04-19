private function generate_form_html($form, $atts = array()) {
    $form_id = 'form-plugin-' . $form->id;
    $form_title = !empty($atts['title']) ? $atts['title'] : $form->title;
    $form_description = !empty($atts['description']) ? $atts['description'] : $form->description;

    $fields = $this->get_form_fields($form);
    if (empty($fields)) {
        return '<p>' . __('No fields configured for this form.', 'form-plugin') . '</p>';
    }

    $captcha = $this->generate_math_captcha_data();

    $template_data = $this->database->get_form_template($form->id);
    $template_id = $template_data['template_id'];
    $customization = $template_data['customization'];

    $template_class = 'template-' . $template_id;
    $form_style = $this->build_form_style($customization);
    $button_style = $this->build_button_style($customization);

    $html = '<div class="form-plugin-container">';
    $html .= $this->render_form_header($form_title, $form_description);
    $html .= '<form id="' . esc_attr($form_id) . '" class="form-plugin-form ' . esc_attr($template_class) . '" method="post" action=""' . $form_style . '>';
    $html .= wp_nonce_field('form_plugin_submit_' . $form->id, 'form_plugin_nonce', true, false);
    $html .= '<input type="hidden" name="form_id" value="' . esc_attr($form->id) . '">';
    $html .= '<input type="hidden" name="captcha_answer" value="' . esc_attr($captcha['answer']) . '">';

    foreach ($fields as $field) {
        if (is_array($field)) {
            $html .= $this->render_field($field);
        }
    }

    $html .= $this->render_captcha_section($captcha);
    $html .= $this->render_submit_section($button_style);
    $html .= '<div class="form-plugin-messages" style="display: none;"></div>';
    $html .= '</form>';
    $html .= '</div>';

    return $html;
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

private function build_form_style($customization) {
    $styles = array();

    if (!empty($customization)) {
        if (isset($customization['background_color'])) {
            $styles[] = 'background-color: ' . esc_attr($customization['background_color']);
        }
        if (isset($customization['text_color'])) {
            $styles[] = 'color: ' . esc_attr($customization['text_color']);
        }
        if (isset($customization['border_color'])) {
            $styles[] = 'border-color: ' . esc_attr($customization['border_color']);
        }
    }

    return !empty($styles) ? ' style="' . implode('; ', $styles) . '"' : '';
}

private function build_button_style($customization) {
    if (isset($customization['button_color'])) {
        return ' style="background-color: ' . esc_attr($customization['button_color']) . '; border-color: ' . esc_attr($customization['button_color']) . ';"';
    }

    return '';
}

private function render_form_header($form_title, $form_description) {
    $html = '';

    if ($form_title) {
        $html .= '<h3 class="form-plugin-title">' . esc_html($form_title) . '</h3>';
    }

    if ($form_description) {
        $html .= '<div class="form-plugin-description">' . wp_kses_post($form_description) . '</div>';
    }

    return $html;
}

private function render_captcha_section($captcha) {
    $html = '<div class="form-group form-plugin-captcha">';
    $html .= '<label for="captcha_input" class="form-label">';
    $html .= sprintf(__('What is %d + %d?', 'form-plugin'), $captcha['num1'], $captcha['num2']);
    $html .= ' <span class="required">*</span>';
    $html .= '</label>';
    $html .= '<input type="number" id="captcha_input" name="captcha_input" class="form-control" required>';
    $html .= '<button type="button" class="btn btn-link btn-sm form-plugin-refresh-captcha">';
    $html .= __('Refresh', 'form-plugin');
    $html .= '</button>';
    $html .= '</div>';

    return $html;
}

private function render_submit_section($button_style) {
    $html = '<div class="form-group form-plugin-submit">';
    $html .= '<button type="submit" class="btn btn-primary form-plugin-submit-btn"' . $button_style . '>';
    $html .= __('Submit Form', 'form-plugin');
    $html .= '</button>';
    $html .= '</div>';

    return $html;
}