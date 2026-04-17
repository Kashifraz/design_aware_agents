def validate_style(self, value):
        """
        Validate style configuration.
        """
        if value is None:
            return {}
        
        if not isinstance(value, dict):
            raise serializers.ValidationError("style must be an object.")
        
        # Validate title
        if "title" in value and value["title"] is not None:
            if not isinstance(value["title"], str):
                raise serializers.ValidationError("'title' must be a string.")
            if len(value["title"]) > 200:
                raise serializers.ValidationError("'title' must be 200 characters or less.")
        
        # Validate subtitle
        if "subtitle" in value and value["subtitle"] is not None:
            if not isinstance(value["subtitle"], str):
                raise serializers.ValidationError("'subtitle' must be a string.")
            if len(value["subtitle"]) > 200:
                raise serializers.ValidationError("'subtitle' must be 200 characters or less.")
        
        # Validate axis labels
        if "xAxisLabel" in value and value["xAxisLabel"] is not None:
            if not isinstance(value["xAxisLabel"], str):
                raise serializers.ValidationError("'xAxisLabel' must be a string.")
            if len(value["xAxisLabel"]) > 100:
                raise serializers.ValidationError("'xAxisLabel' must be 100 characters or less.")
        
        if "yAxisLabel" in value and value["yAxisLabel"] is not None:
            if not isinstance(value["yAxisLabel"], str):
                raise serializers.ValidationError("'yAxisLabel' must be a string.")
            if len(value["yAxisLabel"]) > 100:
                raise serializers.ValidationError("'yAxisLabel' must be 100 characters or less.")
        
        # Validate colors
        if "colors" in value and value["colors"] is not None:
            if not isinstance(value["colors"], list):
                raise serializers.ValidationError("'colors' must be an array.")
            if len(value["colors"]) > 20:
                raise serializers.ValidationError("'colors' array must have 20 or fewer items.")
            # Validate each color is a valid hex color or named color
            import re
            hex_pattern = re.compile(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')
            for color in value["colors"]:
                if not isinstance(color, str):
                    raise serializers.ValidationError("All colors must be strings.")
                if not (hex_pattern.match(color) or color in ['red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink', 'black', 'white', 'gray', 'grey']):
                    raise serializers.ValidationError(f"Invalid color format: '{color}'. Use hex (#RRGGBB) or named colors.")
        
        # Validate legend position
        if "legendPosition" in value and value["legendPosition"] is not None:
            valid_positions = ["top", "bottom", "left", "right"]
            if value["legendPosition"] not in valid_positions:
                raise serializers.ValidationError(f"'legendPosition' must be one of: {', '.join(valid_positions)}")
        
        # Validate boolean fields
        boolean_fields = ["gridlines", "tooltips", "dataLabels"]
        for field in boolean_fields:
            if field in value and value[field] is not None:
                if not isinstance(value[field], bool):
                    raise serializers.ValidationError(f"'{field}' must be a boolean.")
        
        return value