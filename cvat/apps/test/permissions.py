# Copyright (C) CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

from enum import StrEnum

from rest_framework.exceptions import ValidationError

from cvat.apps.engine.models import Task
from cvat.apps.engine.permissions import TaskPermission
from cvat.apps.iam.permissions import OpenPolicyAgentPermission
from cvat.utils import django_database as db_utils


class AnnotationCountsPermission(OpenPolicyAgentPermission):
    class Scopes(StrEnum):
        LIST = "list"

    @classmethod
    def create(cls, request, view, obj, iam_context):
        task_id = request.query_params.get("task_id")
        try:
            task_id = int(task_id)
        except (TypeError, ValueError):
            raise ValidationError("The 'task_id' query parameter must be an integer") from None

        task = db_utils.get_or_404(Task, task_id)

        # Access rights are the same as for viewing the task,
        # so this app doesn't define its own rules
        return [TaskPermission.create_scope_view(request, task)]

    @classmethod
    def _get_scopes(cls, request, view, obj):
        return [cls.Scopes.LIST]

    def get_resource(self):
        return None
