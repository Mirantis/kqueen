from flask_table import Table, Col, LinkCol


class DeleteCol(LinkCol):
    def __init__(self, *args, **kwargs):
        kwargs['column_html_attrs'] = {'class': 'action_column'}
        super(DeleteCol, self).__init__(*args, **kwargs)


class StatusCol(Col):
    def __init__(self, *args, **kwargs):
        kwargs['column_html_attrs'] = {'class': 'status_column'}
        super(StatusCol, self).__init__(*args, **kwargs)


class ClusterTable(Table):
    # Table meta
    classes = ['table']
    # Table fields
    name = LinkCol(
        'Name',
        'user_views.cluster_detail',
        attr_list=['name'],
        url_kwargs=dict(cluster_id='id')
    )
    # name = Col('Name')
    provisioner = Col('Provider')
    state = StatusCol('Status')
    delete = DeleteCol(
        'Delete',
        'user_views.cluster_delete',
        url_kwargs=dict(cluster_id='id')
    )


class ProvisionerTable(Table):
    # Table meta
    classes = ['table']
    # Table fields
    name = Col('Name')
    engine_name = Col('Engine')
    location = Col('Location')
    state = StatusCol('Status')
    delete = DeleteCol(
        'Delete',
        'user_views.provisioner_delete',
        url_kwargs=dict(provisioner_id='id')
    )
