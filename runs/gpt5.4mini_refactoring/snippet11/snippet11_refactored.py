def patch(self, request, project_id):
    """
    Apply edits to the data.
    Body: { "edits": { "row_index": { "column_name": "new_value" } } }
    """
    # Get the project and verify ownership
    try:
        project = Project.objects.get(id=project_id, owner=request.user)
    except Project.DoesNotExist:
        return Response(
            {"detail": "Project not found or you don't have permission to access it."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Get the data table
    data_table = DataTable.objects.filter(project=project).first()
    if not data_table:
        return Response(
            {"detail": "No data table found for this project. Please upload and parse a file first."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Validate request data
    edits = request.data.get("edits", {})
    if not isinstance(edits, dict):
        return Response(
            {"detail": "Edits must be an object with row indices as keys."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate edits against schema and data
    schema = data_table.get_schema()
    data = data_table.get_data_with_edits()

    if data is None:
        return Response(
            {"detail": "Full data not available for editing."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    validated_edits, validation_errors = self._validate_edits(edits, schema, data)

    if validation_errors:
        return Response(
            {
                "detail": "Validation failed.",
                "errors": validation_errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Apply edits
    try:
        current_edits = data_table.get_edited_data()
        current_edits.update(validated_edits)
        data_table.edited_data_json = current_edits
        data_table.save()

        return Response(
            {
                "detail": f"Successfully applied {len(validated_edits)} row edits.",
                "applied_edits": validated_edits,
            }
        )

    except Exception as e:
        return Response(
            {"detail": f"Failed to save edits: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

def _validate_edits(self, edits, schema, data):
    validation_errors = []
    validated_edits = {}

    for row_index_str, row_edits in edits.items():
        try:
            row_index = int(row_index_str)
        except ValueError:
            validation_errors.append(f"Invalid row index: {row_index_str}")
            continue

        if not (0 <= row_index < len(data)):
            validation_errors.append(f"Row index {row_index} out of range.")
            continue

        if not isinstance(row_edits, dict):
            validation_errors.append(f"Row {row_index}: edits must be an object.")
            continue

        validated_row_edits = {}

        for column_name, new_value in row_edits.items():
            if column_name not in schema:
                validation_errors.append(f"Row {row_index}: unknown column '{column_name}'.")
                continue

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
                    continue

            validated_row_edits[column_name] = new_value

        if validated_row_edits:
            validated_edits[str(row_index)] = validated_row_edits

    return validated_edits, validation_errors