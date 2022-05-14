from dynaconf import Dynaconf, Validator

settings = Dynaconf(
    envvar_prefix='squint_data',
    settings_files=['settings.toml', '.secret.toml'],
    validators=[
        Validator(
            'basic.project_name',
            'service_auth.host',
            'service_auth.port',
            'service_auth.token'
            'elasticsearch_auth.version',
            'elasticsearch_auth.host',
            'elasticsearch_auth.port',
            'elasticsearch_auth.user',
            'elasticsearch_auth.password',
            'elasticsearch.max_bulk_size',
            'elasticsearch.timeout',
            'elasticsearch.index_prefix',
            "raw_table.type",
            "raw_table.value_name",
            "redis_auth.host",
            "redis_auth.port",
            "redis_auth.password",
            "redis.tasks_list_name",
            "redis.distributed_list_name",
            "redis.finished_list_name",
            "redis.aborted_list_name",
            "redis.max_try_num"
        )
    ]
)