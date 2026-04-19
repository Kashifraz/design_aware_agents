def validate_selected_columns(self, value):
    """
    Validate that selected columns exist in the schema and are compatible.
    """
    self._validate_selected_columns_type(value)
    self._validate_selected_columns_required_fields(value)
    self._validate_selected_columns_x(value["x"])
    self._validate_selected_columns_y(value["y"])
    self._validate_selected_columns_optional_field(value, "groupBy")
    self._validate_selected_columns_optional_field(value, "label")
    return value


def _validate_selected_columns_type(self, value):
    if not isinstance(value, dict):
        raise serializers.ValidationError("selected_columns must be an object.")


def _validate_selected_columns_required_fields(self, value):
    if "x" not in value:
        raise serializers.ValidationError("selected_columns must include 'x' field.")
    if "y" not in value or not isinstance(value["y"], list) or len(value["y"]) == 0:
        raise serializers.ValidationError("selected_columns must include 'y' as a non-empty array.")


def _validate_selected_columns_x(self, x_column):
    if not isinstance(x_column, str):
        raise serializers.ValidationError("'x' must be a string (column name).")


def _validate_selected_columns_y(self, y_columns):
    if not isinstance(y_columns, list):
        raise serializers.ValidationError("'y' must be an array of column names.")
    if not all(isinstance(col, str) for col in y_columns):
        raise serializers.ValidationError("All items in 'y' must be strings (column names).")


def _validate_selected_columns_optional_field(self, value, field_name):
    if field_name in value and value[field_name] is not None:
        if not isinstance(value[field_name], str):
            raise serializers.ValidationError(f"'{field_name}' must be a string (column name) or null.")