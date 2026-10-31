from datetime import datetime, timezone

from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    event_id       uuid PRIMARY KEY,
    time           timestamptz NOT NULL,
    node_id        text NOT NULL,
    sensor_id      text NOT NULL,
    sensor_type    text NOT NULL,
    schema_version smallint NOT NULL,
    bearing_deg    real,
    confidence     real,
    status         jsonb NOT NULL,
    metrics        jsonb NOT NULL
);
CREATE INDEX IF NOT EXISTS events_sensor_time_idx ON events (sensor_id, time DESC);
CREATE INDEX IF NOT EXISTS events_time_idx ON events (time);
"""

# An empty connection string makes libpq read PGHOST, PGUSER, PGPASSWORD,
# PGDATABASE and PGPORT from the environment.
pool = ConnectionPool("", min_size=1, max_size=4, open=False)


def init_db() -> None:
    pool.open(wait=True, timeout=30)
    with pool.connection() as conn:
        conn.execute(SCHEMA)


def store_event(event) -> None:
    data = event.model_dump(mode="json")
    with pool.connection() as conn:
        conn.execute(
            """
            INSERT INTO events (event_id, time, node_id, sensor_id, sensor_type,
                                schema_version, bearing_deg, confidence, status, metrics)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                data["event_id"],
                datetime.fromtimestamp(data["timestamp_epoch_ms"] / 1000, tz=timezone.utc),
                data["node_id"],
                data["sensor_id"],
                data["sensor_type"],
                data["schema_version"],
                data["direction"]["bearing_deg"],
                data["direction"]["confidence"],
                Jsonb(data["status"]),
                Jsonb(data["metrics"]),
            ),
        )