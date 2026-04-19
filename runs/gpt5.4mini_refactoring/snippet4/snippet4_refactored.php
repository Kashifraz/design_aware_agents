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
    // Escape value if it contains comma, quote, or newline
    $value = str_replace('"', '""', $value);
    
    if (strpos($value, ',') !== false || strpos($value, '"') !== false || strpos($value, "\n") !== false) {
        $value = '"' . $value . '"';
    }
    
    return $value;
}