// Copyright (C) CVAT.ai Corporation
//
// SPDX-License-Identifier: MIT

import './styles.scss';

import 'chart.js/auto';
import React, { useEffect, useState } from 'react';
import { Bar } from 'react-chartjs-2';
import { Row, Col } from 'antd/lib/grid';
import Button from 'antd/lib/button';
import Empty from 'antd/lib/empty';
import Result from 'antd/lib/result';
import Title from 'antd/lib/typography/Title';

import { getCore } from 'cvat-core-wrapper';
import { InstanceType } from 'reducers';
import { useInstanceId } from 'utils/hooks';
import GoBackButton from 'components/common/go-back-button';
import CVATLoadingSpinner from 'components/common/loading-spinner';

const core = getCore();

interface LabelCount {
    id: number;
    name: string;
    color: string;
    shapes: number;
    tracks: number;
    tags: number;
    total: number;
}

interface AnnotationCounts {
    task_id: number;
    total: number;
    labels: LabelCount[];
}

function AnnotationCountsChart({ counts }: Readonly<{ counts: AnnotationCounts }>): JSX.Element {
    return (
        <div className='cvat-annotation-counts-chart'>
            <Bar
                data={{
                    labels: counts.labels.map((label) => label.name),
                    datasets: [{
                        label: 'Annotations',
                        data: counts.labels.map((label) => label.total),
                        backgroundColor: counts.labels.map((label) => label.color),
                    }],
                }}
                options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
                }}
            />
        </div>
    );
}

function AnnotationCountsPage(): JSX.Element {
    const taskId = useInstanceId(InstanceType.TASK);
    const [counts, setCounts] = useState<AnnotationCounts | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [fetching, setFetching] = useState(true);
    const [attempt, setAttempt] = useState(0);

    useEffect(() => {
        // the request may finish after the page is closed, its result must be ignored then
        let active = true;
        setFetching(true);
        setError(null);
        core.server.request<{ data: AnnotationCounts }>(`${core.config.backendAPI}/annotation_counts`, {
            method: 'GET',
            params: { task_id: taskId },
        }).then((response) => {
            if (active) {
                setCounts(response.data);
            }
        }).catch((requestError: unknown) => {
            if (active) {
                setError(requestError instanceof Error ? requestError.message : String(requestError));
            }
        }).finally(() => {
            if (active) {
                setFetching(false);
            }
        });

        return () => {
            active = false;
        };
    }, [taskId, attempt]);

    let content: JSX.Element | null = null;
    if (fetching) {
        content = <CVATLoadingSpinner />;
    } else if (error !== null) {
        content = (
            <Result
                status='error'
                title='Could not receive annotation counts'
                subTitle={error}
                extra={<Button onClick={() => setAttempt(attempt + 1)}>Retry</Button>}
            />
        );
    } else if (counts && counts.labels.length && counts.total) {
        content = <AnnotationCountsChart counts={counts} />;
    } else {
        content = <Empty description='No annotations in this task yet' />;
    }

    return (
        <div className='cvat-annotation-counts-page'>
            <Row justify='center'>
                <Col span={22} xl={18} xxl={14} className='cvat-task-top-bar'>
                    <GoBackButton />
                </Col>
            </Row>
            <Row justify='center' className='cvat-annotation-counts-inner-wrapper'>
                <Col span={22} xl={18} xxl={14} className='cvat-annotation-counts-inner'>
                    <Title level={4} className='cvat-text-color'>
                        {`Task #${taskId} annotation counts`}
                        {counts && !fetching && !error ? ` (total: ${counts.total})` : ''}
                    </Title>
                    {content}
                </Col>
            </Row>
        </div>
    );
}

export default React.memo(AnnotationCountsPage);
