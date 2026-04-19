def _save_chart_config(self, request, project_id, partial):
    """
    Shared implementation for full and partial chart configuration updates.
    """
    # Get the project and verify ownership
    try:
        project = Project.objects.get(id=project_id, owner=request.user)
    except Project.DoesNotExist:
        return Response(
            {"detail": "Project not found or you don't have permission to access it."},
            status=status.HTTP_404_NOT_FOUND,
        )

    context = {"request": request, "project": project}

    # Get or create chart config
    try:
        chart_config = ChartConfig.objects.get(project=project)
        serializer = ChartConfigSerializer(
            chart_config,
            data=request.data,
            context=context,
            partial=partial,
        )
    except ChartConfig.DoesNotExist:
        serializer = ChartConfigSerializer(
            data=request.data,
            context=context,
        )

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def put(self, request, project_id):
    """
    Update chart configuration for a project.
    Creates a new configuration if it doesn't exist.
    """
    return self._save_chart_config(request, project_id, partial=False)


def patch(self, request, project_id):
    """
    Partially update chart configuration for a project.
    Creates a new configuration if it doesn't exist.
    """
    return self._save_chart_config(request, project_id, partial=True)