from flask_table import Table, Col, LinkCol


class ActionCol(Col):
    def __init__(self, *args, **kwargs):
        kwargs['column_html_attrs'] = {'class': 'action_column'}
        super(ActionCol, self).__init__(*args, **kwargs)


class StatusCol(Col):
    def __init__(self, *args, **kwargs):
        kwargs['column_html_attrs'] = {'class': 'status_column'}
        super(StatusCol, self).__init__(*args, **kwargs)


class ClusterTable(Table):
    # Table meta
    classes = ['table']
    # Table fields
    name = Col('Name')
    provisioner = Col('Provider')
    state = StatusCol('Status')
    actions = ActionCol('Actions')

class ProvisionerTable(Table):
    # Table meta
    classes = ['table']
    # Table fields
    name = Col('Name')
    engine_name = Col('Engine')
    location = Col('Location')
    state = StatusCol('Status')
    actions = ActionCol('Actions')

