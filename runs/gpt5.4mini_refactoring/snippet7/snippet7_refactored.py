def validate_style(self, value):
    """
    Validate style configuration.
    """
    if value is None:
        return {}

    if not isinstance(value, dict):
        raise serializers.ValidationError("style must be an object.")

    self._validate_style_string_field(value, "title", 200)
    self._validate_style_string_field(value, "subtitle", 200)
    self._validate_style_string_field(value, "xAxisLabel", 100)
    self._validate_style_string_field(value, "yAxisLabel", 100)
    self._validate_style_colors(value)
    self._validate_style_legend_position(value)
    self._validate_style_boolean_fields(value, ["gridlines", "tooltips", "dataLabels"])

    return value


def _validate_style_string_field(self, value, field_name, max_length):
    if field_name in value and value[field_name] is not None:
        if not isinstance(value[field_name], str):
            raise serializers.ValidationError(f"'{field_name}' must be a string.")
        if len(value[field_name]) > max_length:
            raise serializers.ValidationError(
                f"'{field_name}' must be {max_length} characters or less."
            )


def _validate_style_colors(self, value):
    if "colors" in value and value["colors"] is not None:
        if not isinstance(value["colors"], list):
            raise serializers.ValidationError("'colors' must be an array.")
        if len(value["colors"]) > 20:
            raise serializers.ValidationError("'colors' array must have 20 or fewer items.")

        import re

        hex_pattern = re.compile(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')
        valid_named_colors = [
            "red", "blue", "green", "yellow", "orange",
            "purple", "pink", "black", "white", "gray", "grey"
        ]

        for color in value["colors"]:
            if not isinstance(color, str):
                raise serializers.ValidationError("All colors must be strings.")
            if not (hex_pattern.match(color) or color in valid_named_colors):
                raise serializers.ValidationError(
                    f"Invalid color format: '{color}'. Use hex (#RRGGBB) or named colors."
                )


def _validate_style_legend_position(self, value):
    if "legendPosition" in value and value["legendPosition"] is not None:
        valid_positions = ["top", "bottom", "left", "right"]
        if value["legendPosition"] not in valid_positions:
            raise serializers.ValidationError(
                f"'legendPosition' must be one of: {', '.join(valid_positions)}"
            )


def _validate_style_boolean_fields(self, value, boolean_fields):
    for field in boolean_fields:
        if field in value and value[field] is not None:
            if not isinstance(value[field], bool):
                raise serializers.ValidationError(f"'{field}' must be a boolean.")