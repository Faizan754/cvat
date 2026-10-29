# Copyright (C) CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

from rest_framework import serializers


class LabelAnnotationCountSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    color = serializers.CharField()
    shapes = serializers.IntegerField()
    tracks = serializers.IntegerField()
    tags = serializers.IntegerField()
    total = serializers.IntegerField()


class AnnotationCountsSerializer(serializers.Serializer):
    task_id = serializers.IntegerField()
    total = serializers.IntegerField()
    labels = LabelAnnotationCountSerializer(many=True)
