from flask import request
from flask.json import jsonify

from flask_monitoringdashboard import blueprint
from flask_monitoringdashboard.core.custom_graph import scheduler
from flask_monitoringdashboard.core.telemetry import post_to_back_if_telemetry_enabled
from flask_monitoringdashboard.core.database_pruning import prune_database_older_than_weeks


@blueprint.route('/database_pruning/prune_on_demand', methods=['POST'])
def prune_database_on_demand():
    """
    Endpoint for pruning the database of Request and optionally CustomGraph data older than the specified number of weeks
    """
    data = request.json
    weeks = data.get('age_threshold_weeks')
    delete_custom_graphs = data.get('delete_custom_graphs')

    # Validation
    if not isinstance(weeks, int) or weeks < 0:
        return jsonify({'error': 'age_threshold_weeks must be a natural number'}), 400
    if not isinstance(delete_custom_graphs, bool):
        return jsonify({'error': 'delete_custom_graphs must be a boolean'}), 400

    # Prune database
    prune_database_older_than_weeks(weeks, delete_custom_graphs)

    # Post info to telemetry if enabled
    post_data = {'age_threshold_weeks': weeks, 'delete_custom_graphs': delete_custom_graphs}
    post_to_back_if_telemetry_enabled('DatabasePruning', **post_data)

    return jsonify({'message': 'Database pruning complete'}), 200


@blueprint.route('/database_pruning/get_pruning_schedule', methods=['GET'])
def get_pruning_schedule():
    job = scheduler.get_job('database_pruning_schedule')

    # Check if the job exists and return details
    if job:
        return jsonify({
            'year': str(job.trigger.fields[0]),
            'month': str(job.trigger.fields[1]),
            'day_of_the_month': str(job.trigger.fields[2]),
            'week': str(job.trigger.fields[3]),
            'day_of_the_week': str(job.trigger.fields[4]),
            'hour': str(job.trigger.fields[5]),
            'minute': str(job.trigger.fields[6]),
            'second': str(job.trigger.fields[7]),
            'weeks_to_keep': job.args[0],
            'delete_custom_graphs': job.args[1],
        })
    else:
        return jsonify({'error': 'No pruning schedule found'}), 404
