from dynaconf import Dynaconf, Validator

settings = Dynaconf(
    envvar_prefix='squint_data',
    settings_files=['settings.toml', '.secret.toml'],
    validators=[
        Validator(
            'basic.project_name',
            'service.host',
            'service.port',
            'service_auth.token'
            'elasticsearch.version',
            'elasticsearch.host',
            'elasticsearch.port',
            'elasticsearch_auth.user',
            'elasticsearch_auth.password',
            'elasticsearch.max_bulk_size',
            'elasticsearch.timeout',
            'elasticsearch.index_prefix',
            "raw_table.type",
            "redis.host",
            "redis.port",
            "redis.tasks_list_name",
            "redis.distributed_list_name",
            "redis.finished_list_name",
            "redis_auth.password",
            "wide_table.domain_index",
            "wide_table.ip_index",
            "wide_table.organization_index"
        )
    ]
)