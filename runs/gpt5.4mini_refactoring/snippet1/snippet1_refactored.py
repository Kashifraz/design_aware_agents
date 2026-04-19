def _get_project(self, request, project_id):
    """Fetch the project owned by the current user or return a 404 response."""
    try:
        return Project.objects.get(id=project_id, owner=request.user)
    except Project.DoesNotExist:
        return None


def _save_chart_config(self, request, project, partial):
    """Create or update chart config for a project."""
    try:
        chart_config = ChartConfig.objects.get(project=project)
        serializer = ChartConfigSerializer(
            chart_config,
            data=request.data,
            context={"request": request, "project": project},
            partial=partial,
        )
    except ChartConfig.DoesNotExist:
        serializer = ChartConfigSerializer(
            data=request.data,
            context={"request": request, "project": project},
            partial=partial,
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
    project = self._get_project(request, project_id)
    if project is None:
        return Response(
            {"detail": "Project not found or you don't have permission to access it."},
            status=status.HTTP_404_NOT_FOUND,
        )

    return self._save_chart_config(request, project, partial=False)


def patch(self, request, project_id):
    """
    Partially update chart configuration for a project.
    Creates a new configuration if it doesn't exist.
    """
    project = self._get_project(request, project_id)
    if project is None:
        return Response(
            {"detail": "Project not found or you don't have permission to access it."},
            status=status.HTTP_404_NOT_FOUND,
        )

    return self._save_chart_config(request, project, partial=True)