from django.conf import settings


# helper methods
def get_value(data_type, station_ids, station_id, target_date, day_offset, time_of_day=None):
    return settings.IEASYREPORTS_CONF.data_manager_class.get_metric_value_for_tag(
        data_type, station_ids, station_id, target_date, day_offset, time_of_day
    )


def get_trend(data_type, station_ids, station_id, target_date, time_of_day=None):
    return settings.IEASYREPORTS_CONF.data_manager_class.get_trend_value(
        data_type, station_ids, station_id, target_date, time_of_day
    )
