private function array_to_csv_row($array) {
        $csv_row = '';
        $first = true;
        
        foreach ($array as $value) {
            if (!$first) {
                $csv_row .= ',';
            }
            
            // Escape value if it contains comma, quote, or newline
            $value = str_replace('"', '""', $value);
            if (strpos($value, ',') !== false || strpos($value, '"') !== false || strpos($value, "\n") !== false) {
                $value = '"' . $value . '"';
            }
            
            $csv_row .= $value;
            $first = false;
        }
        
        return $csv_row;
    }