"""Database operations for PostgreSQL."""

import psycopg2
from psycopg2 import sql, extras
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages PostgreSQL database connections and operations."""

    def __init__(self, host, port, dbname, user, password):
        """Initialize database manager with connection parameters."""
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self.conn = None
        self.cursor = None

    def connect(self):
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                sslmode='disable'
            )
            self.cursor = self.conn.cursor()
            logger.info("Successfully connected to PostgreSQL database")
            return True
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def close(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def create_table(self, table_name):
        """Create table for Yandex Metrika visits data."""
        create_table_query = sql.SQL("""
            CREATE TABLE IF NOT EXISTS {} (
                id SERIAL PRIMARY KEY,
                visit_id BIGINT,
                watch_ids TEXT,
                visit_date DATE,
                is_new_user INTEGER,
                start_url TEXT,
                end_url TEXT,
                visit_duration INTEGER,
                bounce INTEGER,
                client_id BIGINT,
                goals_id TEXT,
                goals_date_time TEXT,
                referer TEXT,
                device_category TEXT,
                operating_system_root TEXT,
                utm_campaign TEXT,
                utm_content TEXT,
                utm_medium TEXT,
                utm_source TEXT,
                utm_term TEXT,
                page_views INTEGER,
                purchase_id TEXT,
                purchase_date_time TEXT,
                purchase_revenue NUMERIC,
                purchase_currency TEXT,
                purchase_product_quantity INTEGER,
                products_purchase_id TEXT,
                products_id TEXT,
                products_name TEXT,
                products_category TEXT,
                region_city TEXT,
                impressions_url TEXT,
                impressions_date_time TEXT,
                impressions_product_id TEXT,
                referal_source TEXT,
                search_engine_root TEXT,
                search_phrase TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """).format(sql.Identifier(table_name))

        try:
            self.cursor.execute(create_table_query)
            self.conn.commit()
            logger.info(f"Table '{table_name}' created successfully")
        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Failed to create table: {e}")
            raise

    def insert_data(self, table_name, data, valid_fields=None):
        """Insert data into the table.

        Args:
            table_name: Name of the table to insert into
            data: List of dictionaries containing the data
            valid_fields: Optional list of valid field names from Yandex Metrika.
                         If provided, only these fields will be inserted.
        """
        if not data:
            logger.warning("No data to insert")
            return 0

        # If valid_fields is provided, use only those fields
        # Otherwise, use all fields from the first row
        if valid_fields:
            fields_to_insert = valid_fields
        else:
            # Fallback to using all fields from first row
            fields_to_insert = list(data[0].keys())

        # Map Yandex Metrika field names to database column names
        field_mapping = {
            'ym:s:visitID': 'visit_id',
            'ym:s:watchIDs': 'watch_ids',
            'ym:s:date': 'visit_date',
            'ym:s:isNewUser': 'is_new_user',
            'ym:s:startURL': 'start_url',
            'ym:s:endURL': 'end_url',
            'ym:s:visitDuration': 'visit_duration',
            'ym:s:bounce': 'bounce',
            'ym:s:clientID': 'client_id',
            'ym:s:goalsID': 'goals_id',
            'ym:s:goalsDateTime': 'goals_date_time',
            'ym:s:referer': 'referer',
            'ym:s:deviceCategory': 'device_category',
            'ym:s:operatingSystemRoot': 'operating_system_root',
            'ym:s:UTMCampaign': 'utm_campaign',
            'ym:s:UTMContent': 'utm_content',
            'ym:s:UTMMedium': 'utm_medium',
            'ym:s:UTMSource': 'utm_source',
            'ym:s:UTMTerm': 'utm_term',
            'ym:s:pageViews': 'page_views',
            'ym:s:purchaseID': 'purchase_id',
            'ym:s:purchaseDateTime': 'purchase_date_time',
            'ym:s:purchaseRevenue': 'purchase_revenue',
            'ym:s:purchaseCurrency': 'purchase_currency',
            'ym:s:purchaseProductQuantity': 'purchase_product_quantity',
            'ym:s:productsPurchaseID': 'products_purchase_id',
            'ym:s:productsID': 'products_id',
            'ym:s:productsName': 'products_name',
            'ym:s:productsCategory': 'products_category',
            'ym:s:regionCity': 'region_city',
            'ym:s:impressionsURL': 'impressions_url',
            'ym:s:impressionsDateTime': 'impressions_date_time',
            'ym:s:impressionsProductID': 'impressions_product_id',
            'ym:s:ReferalSource': 'referal_source',
            'ym:s:SearchEngineRoot': 'search_engine_root',
            'ym:s:SearchPhrase': 'search_phrase'
        }

        # Get database column names for valid fields
        db_columns = []
        for field in fields_to_insert:
            if field in field_mapping:
                db_columns.append(field_mapping[field])

        if not db_columns:
            logger.error("No valid columns to insert")
            return 0

        # Build dynamic insert query
        columns_str = ', '.join(db_columns)
        insert_query = sql.SQL("""
            INSERT INTO {} ({})
            VALUES %s
        """).format(sql.Identifier(table_name), sql.SQL(columns_str))

        try:
            # Build values list dynamically based on valid fields
            values = []
            for row in data:
                row_values = tuple(row.get(field) for field in fields_to_insert)
                values.append(row_values)

            extras.execute_values(self.cursor, insert_query, values)
            self.conn.commit()
            logger.info(f"Successfully inserted {len(data)} rows into '{table_name}' with {len(db_columns)} columns")
            return len(data)
        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Failed to insert data: {e}")
            raise

    def test_connection(self):
        """Test database connection and return PostgreSQL version."""
        try:
            self.cursor.execute('SELECT version()')
            version = self.cursor.fetchone()
            logger.info(f"PostgreSQL version: {version[0]}")
            return version[0]
        except psycopg2.Error as e:
            logger.error(f"Failed to test connection: {e}")
            raise
