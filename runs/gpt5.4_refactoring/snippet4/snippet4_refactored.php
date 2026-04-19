private function array_to_csv_row($array) {
    $csv_row = '';
    $first = true;

    foreach ($array as $value) {
        if (!$first) {
            $csv_row .= ',';
        }

        $csv_row .= $this->format_csv_value($value);
        $first = false;
    }

    return $csv_row;
}

private function format_csv_value($value) {
    $escapedValue = $this->escape_csv_quotes($value);

    if ($this->requires_csv_quotes($escapedValue)) {
        return '"' . $escapedValue . '"';
    }

    return $escapedValue;
}

private function escape_csv_quotes($value) {
    return str_replace('"', '""', $value);
}

private function requires_csv_quotes($value) {
    return strpos($value, ',') !== false
        || strpos($value, '"') !== false
        || strpos($value, "\n") !== false;
}