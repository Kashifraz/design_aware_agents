 def put(self, request, project_id):
        """
        Update chart configuration for a project.
        Creates a new configuration if it doesn't exist.
        """
        # Get the project and verify ownership
        try:
            project = Project.objects.get(id=project_id, owner=request.user)
        except Project.DoesNotExist:
            return Response(
                {"detail": "Project not found or you don't have permission to access it."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get or create chart config
        try:
            chart_config = ChartConfig.objects.get(project=project)
            serializer = ChartConfigSerializer(
                chart_config,
                data=request.data,
                context={"request": request, "project": project},
                partial=False  # PUT requires all fields
            )
        except ChartConfig.DoesNotExist:
            # Create new config
            serializer = ChartConfigSerializer(
                data=request.data,
                context={"request": request, "project": project}
            )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, project_id):
        """
        Partially update chart configuration for a project.
        Creates a new configuration if it doesn't exist.
        """
        # Get the project and verify ownership
        try:
            project = Project.objects.get(id=project_id, owner=request.user)
        except Project.DoesNotExist:
            return Response(
                {"detail": "Project not found or you don't have permission to access it."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get or create chart config
        try:
            chart_config = ChartConfig.objects.get(project=project)
            serializer = ChartConfigSerializer(
                chart_config,
                data=request.data,
                context={"request": request, "project": project},
                partial=True  # PATCH allows partial updates
            )
        except ChartConfig.DoesNotExist:
            # Create new config with provided data
            serializer = ChartConfigSerializer(
                data=request.data,
                context={"request": request, "project": project}
            )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)