def validate_selected_columns(self, value):
    """
    Validate that selected columns exist in the schema and are compatible.
    """
    self._validate_selected_columns_object(value)
    self._validate_required_selected_columns_fields(value)
    self._validate_x_column(value["x"])
    self._validate_y_columns(value["y"])
    self._validate_optional_string_field(value, "groupBy")
    self._validate_optional_string_field(value, "label")
    return value


def _validate_selected_columns_object(self, value):
    if not isinstance(value, dict):
        raise serializers.ValidationError("selected_columns must be an object.")


def _validate_required_selected_columns_fields(self, value):
    if "x" not in value:
        raise serializers.ValidationError("selected_columns must include 'x' field.")
    if "y" not in value or not isinstance(value["y"], list) or len(value["y"]) == 0:
        raise serializers.ValidationError("selected_columns must include 'y' as a non-empty array.")


def _validate_x_column(self, x_column):
    if not isinstance(x_column, str):
        raise serializers.ValidationError("'x' must be a string (column name).")


def _validate_y_columns(self, y_columns):
    if not isinstance(y_columns, list):
        raise serializers.ValidationError("'y' must be an array of column names.")
    if not all(isinstance(col, str) for col in y_columns):
        raise serializers.ValidationError("All items in 'y' must be strings (column names).")


def _validate_optional_string_field(self, value, field_name):
    if field_name in value and value[field_name] is not None:
        if not isinstance(value[field_name], str):
            raise serializers.ValidationError(
                f"'{field_name}' must be a string (column name) or null."
            )