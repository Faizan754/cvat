# Copyright (C) CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

from django.db.models import Count

from cvat.apps.engine.models import (
    JobType,
    LabeledImage,
    LabeledShape,
    LabeledTrack,
    Task,
    ValidationMode,
)


def count_annotations_per_label(task: Task) -> dict:
    # Same job selection as the task export (dataset_manager/task.py TaskAnnotation):
    # consensus replicas are never counted, GT jobs only in the GT pool mode.
    job_types = [JobType.ANNOTATION]
    if task.data and task.data.validation_mode == ValidationMode.GT_POOL:
        job_types.append(JobType.GROUND_TRUTH)

    job_filter = {"job__segment__task_id": task.id, "job__type__in": job_types}

    # One GROUP BY label_id query per annotation table. Skeleton elements
    # (parent is set) are left out, so a skeleton counts as one object.
    def counts_by_label(model, **extra_filter) -> dict[int, int]:
        rows = (
            model.objects.filter(**job_filter, **extra_filter)
            .values("label_id")
            .annotate(count=Count("id"))
            .order_by()
        )
        return {row["label_id"]: row["count"] for row in rows}

    shapes = counts_by_label(LabeledShape, parent__isnull=True)
    tracks = counts_by_label(LabeledTrack, parent__isnull=True)
    tags = counts_by_label(LabeledImage)

    labels = []
    for label in task.get_labels().order_by("id"):
        label_counts = {
            "shapes": shapes.get(label.id, 0),
            "tracks": tracks.get(label.id, 0),
            "tags": tags.get(label.id, 0),
        }
        labels.append(
            {
                "id": label.id,
                "name": label.name,
                "color": label.color,
                **label_counts,
                "total": sum(label_counts.values()),
            }
        )

    return {
        "task_id": task.id,
        "total": sum(label["total"] for label in labels),
        "labels": labels,
    }
