def get_connector(config: dict):

    db_type = config.get("database_type")

    if db_type == "mysql":
        from .mysql_connector import MySQLConnector
        mysql_cfg = config["mysql"]

        # Check if k8_db_details is provided for Kubernetes deployment
        if "k8_db_details" in mysql_cfg:
            return MySQLConnector(k8_db_details=mysql_cfg["k8_db_details"])
        else:
            return MySQLConnector(
                host=mysql_cfg["host"],
                port=mysql_cfg.get("port", 3306),
                user=mysql_cfg["user"],
                password=mysql_cfg["password"],
                database=mysql_cfg["database"]
            )

    elif db_type == "gcpbq":
        from .bigquery_connector import BigQueryConnector
        gcp_cfg = config.get("gcp", {})
        return BigQueryConnector(gcp_cfg)

    else:
        raise ValueError(f"Unsupported database type: {db_type}")

