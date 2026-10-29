# Copyright (C) CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

from rest_framework import routers

from .views import AnnotationCountsViewSet

router = routers.DefaultRouter(trailing_slash=False)
router.register("annotation_counts", AnnotationCountsViewSet, basename="annotation_counts")

urlpatterns = router.urls
