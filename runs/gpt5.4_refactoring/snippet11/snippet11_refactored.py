def patch(self, request, project_id):
    """
    Apply edits to the data.
    Body: { "edits": { "row_index": { "column_name": "new_value" } } }
    """
    # Get the project and verify ownership
    try:
        project = self._get_project(project_id, request.user)
    except Project.DoesNotExist:
        return Response(
            {"detail": "Project not found or you don't have permission to access it."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Get the data table
    data_table = self._get_data_table(project)
    if not data_table:
        return Response(
            {"detail": "No data table found for this project. Please upload and parse a file first."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Validate request data
    edits = request.data.get("edits", {})
    if not self._is_valid_edits_payload(edits):
        return Response(
            {"detail": "Edits must be an object with row indices as keys."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate edits against schema and data
    schema = data_table.get_schema()
    data = data_table.get_data_with_edits()
    validation_errors = []

    if data is None:
        return Response(
            {"detail": "Full data not available for editing."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    validated_edits = self._build_validated_edits(edits, schema, data, validation_errors)

    if validation_errors:
        return Response(
            {
                "detail": "Validation failed.",
                "errors": validation_errors
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Apply edits
    try:
        self._save_edits(data_table, validated_edits)
        return Response({
            "detail": f"Successfully applied {len(validated_edits)} row edits.",
            "applied_edits": validated_edits
        })

    except Exception as e:
        return Response(
            {"detail": f"Failed to save edits: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _get_project(self, project_id, user):
    return Project.objects.get(id=project_id, owner=user)


def _get_data_table(self, project):
    return DataTable.objects.filter(project=project).first()


def _is_valid_edits_payload(self, edits):
    return isinstance(edits, dict)


def _build_validated_edits(self, edits, schema, data, validation_errors):
    validated_edits = {}

    for row_index_str, row_edits in edits.items():
        validated_row = self._validate_row_edits(
            row_index_str, row_edits, schema, data, validation_errors
        )
        if validated_row is not None:
            row_index, validated_row_edits = validated_row
            if validated_row_edits:
                validated_edits[str(row_index)] = validated_row_edits

    return validated_edits


def _validate_row_edits(self, row_index_str, row_edits, schema, data, validation_errors):
    try:
        row_index = int(row_index_str)
    except ValueError:
        validation_errors.append(f"Invalid row index: {row_index_str}")
        return None

    if not (0 <= row_index < len(data)):
        validation_errors.append(f"Row index {row_index} out of range.")
        return None

    if not isinstance(row_edits, dict):
        validation_errors.append(f"Row {row_index}: edits must be an object.")
        return None

    validated_row_edits = {}

    for column_name, new_value in row_edits.items():
        validated_cell = self._validate_cell_edit(
            row_index, column_name, new_value, schema, validation_errors
        )
        if validated_cell is not None:
            validated_row_edits[column_name] = validated_cell

    return row_index, validated_row_edits


def _validate_cell_edit(self, row_index, column_name, new_value, schema, validation_errors):
    if column_name not in schema:
        validation_errors.append(f"Row {row_index}: unknown column '{column_name}'.")
        return None

    expected_type = schema[column_name]

    # Type validation
    if new_value is not None:
        try:
            # Convert and validate type
            if expected_type == "number":
                if isinstance(new_value, str):
                    new_value = float(new_value)
                elif not isinstance(new_value, (int, float)):
                    raise ValueError
            elif expected_type == "boolean":
                if isinstance(new_value, str):
                    new_value = new_value.lower() in ["true", "1", "yes"]
                elif not isinstance(new_value, bool):
                    raise ValueError
            elif expected_type == "string":
                new_value = str(new_value)
            # For date, we'll accept string representation for now
        except (ValueError, TypeError):
            validation_errors.append(
                f"Row {row_index}, column '{column_name}': invalid value '{new_value}' for type '{expected_type}'."
            )
            return None

    return new_value


def _save_edits(self, data_table, validated_edits):
    current_edits = data_table.get_edited_data()
    current_edits.update(validated_edits)
    data_table.edited_data_json = current_edits
    data_table.save()