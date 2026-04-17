def validate_selected_columns(self, value):
        """
        Validate that selected columns exist in the schema and are compatible.
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("selected_columns must be an object.")

        # Check required fields
        if "x" not in value:
            raise serializers.ValidationError("selected_columns must include 'x' field.")
        if "y" not in value or not isinstance(value["y"], list) or len(value["y"]) == 0:
            raise serializers.ValidationError("selected_columns must include 'y' as a non-empty array.")

        # Validate x column
        x_column = value["x"]
        if not isinstance(x_column, str):
            raise serializers.ValidationError("'x' must be a string (column name).")

        # Validate y columns
        y_columns = value["y"]
        if not isinstance(y_columns, list):
            raise serializers.ValidationError("'y' must be an array of column names.")
        if not all(isinstance(col, str) for col in y_columns):
            raise serializers.ValidationError("All items in 'y' must be strings (column names).")

        # Validate optional fields
        if "groupBy" in value and value["groupBy"] is not None:
            if not isinstance(value["groupBy"], str):
                raise serializers.ValidationError("'groupBy' must be a string (column name) or null.")
        
        if "label" in value and value["label"] is not None:
            if not isinstance(value["label"], str):
                raise serializers.ValidationError("'label' must be a string (column name) or null.")

        return value