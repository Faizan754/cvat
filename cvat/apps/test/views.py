# Copyright (C) CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.response import Response

from cvat.apps.engine.models import Task

from .counts import count_annotations_per_label
from .permissions import AnnotationCountsPermission
from .serializers import AnnotationCountsSerializer


@extend_schema(tags=["annotation_counts"])
class AnnotationCountsViewSet(viewsets.ViewSet):
    serializer_class = None
    iam_permission_class = AnnotationCountsPermission
    iam_supports_organization_params = False

    @extend_schema(
        summary="Get the number of annotations per label in a task",
        parameters=[
            OpenApiParameter(
                "task_id",
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                required=True,
                description="The task to count annotations in",
            ),
        ],
        responses={"200": AnnotationCountsSerializer},
    )
    def list(self, request):
        # The task exists here: the permission class has already checked it
        task = Task.objects.select_related("data").get(id=int(request.query_params["task_id"]))
        return Response(count_annotations_per_label(task))
