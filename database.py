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
                adv_engine TEXT,
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

    def insert_data(self, table_name, data):
        """Insert data into the table."""
        if not data:
            logger.warning("No data to insert")
            return 0

        insert_query = sql.SQL("""
            INSERT INTO {} (
                visit_id, watch_ids, visit_date, is_new_user, start_url, end_url,
                visit_duration, bounce, client_id, goals_id, goals_date_time,
                referer, device_category, operating_system_root,
                utm_campaign, utm_content, utm_medium,
                utm_source, utm_term, page_views, purchase_id,
                purchase_date_time, purchase_revenue, purchase_currency,
                purchase_product_quantity, products_purchase_id, products_id,
                products_name, products_category, region_city, impressions_url,
                impressions_date_time, impressions_product_id, adv_engine,
                referal_source, search_engine_root, search_phrase
            ) VALUES %s
        """).format(sql.Identifier(table_name))

        try:
            values = [
                (
                    row.get('ym:s:visitID'),
                    row.get('ym:s:watchIDs'),
                    row.get('ym:s:date'),
                    row.get('ym:s:isNewUser'),
                    row.get('ym:s:startURL'),
                    row.get('ym:s:endURL'),
                    row.get('ym:s:visitDuration'),
                    row.get('ym:s:bounce'),
                    row.get('ym:s:clientID'),
                    row.get('ym:s:goalsID'),
                    row.get('ym:s:goalsDateTime'),
                    row.get('ym:s:referer'),
                    row.get('ym:s:deviceCategory'),
                    row.get('ym:s:operatingSystemRoot'),
                    row.get('ym:s:UTMCampaign'),
                    row.get('ym:s:UTMContent'),
                    row.get('ym:s:UTMMedium'),
                    row.get('ym:s:UTMSource'),
                    row.get('ym:s:UTMTerm'),
                    row.get('ym:s:pageViews'),
                    row.get('ym:s:purchaseID'),
                    row.get('ym:s:purchaseDateTime'),
                    row.get('ym:s:purchaseRevenue'),
                    row.get('ym:s:purchaseCurrency'),
                    row.get('ym:s:purchaseProductQuantity'),
                    row.get('ym:s:productsPurchaseID'),
                    row.get('ym:s:productsID'),
                    row.get('ym:s:productsName'),
                    row.get('ym:s:productsCategory'),
                    row.get('ym:s:regionCity'),
                    row.get('ym:s:impressionsURL'),
                    row.get('ym:s:impressionsDateTime'),
                    row.get('ym:s:impressionsProductID'),
                    row.get('ym:s:AdvEngine'),
                    row.get('ym:s:ReferalSource'),
                    row.get('ym:s:SearchEngineRoot'),
                    row.get('ym:s:SearchPhrase')
                )
                for row in data
            ]

            extras.execute_values(self.cursor, insert_query, values)
            self.conn.commit()
            logger.info(f"Successfully inserted {len(data)} rows into '{table_name}'")
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
