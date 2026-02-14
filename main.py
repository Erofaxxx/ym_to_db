"""Main program to load Yandex Metrika data to PostgreSQL database."""

import sys
import logging
from config import Config
from database import DatabaseManager
from yandex_metrika import YandexMetrikaClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ym_to_db.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Yandex Metrika fields to export
# Note: DirectPlatform, DirectConditionType, TrafficSource, and AdvEngine are not available for visits source
FIELDS = [
    'ym:s:visitID',
    'ym:s:watchIDs',
    'ym:s:date',
    'ym:s:isNewUser',
    'ym:s:startURL',
    'ym:s:endURL',
    'ym:s:visitDuration',
    'ym:s:bounce',
    'ym:s:clientID',
    'ym:s:goalsID',
    'ym:s:goalsDateTime',
    'ym:s:referer',
    'ym:s:deviceCategory',
    'ym:s:operatingSystemRoot',
    'ym:s:UTMCampaign',
    'ym:s:UTMContent',
    'ym:s:UTMMedium',
    'ym:s:UTMSource',
    'ym:s:UTMTerm',
    'ym:s:pageViews',
    'ym:s:purchaseID',
    'ym:s:purchaseDateTime',
    'ym:s:purchaseRevenue',
    'ym:s:purchaseCurrency',
    'ym:s:purchaseProductQuantity',
    'ym:s:productsPurchaseID',
    'ym:s:productsID',
    'ym:s:productsName',
    'ym:s:productsCategory',
    'ym:s:regionCity',
    'ym:s:impressionsURL',
    'ym:s:impressionsDateTime',
    'ym:s:impressionsProductID',
    'ym:s:ReferalSource',
    'ym:s:SearchEngineRoot',
    'ym:s:SearchPhrase'
]


def main():
    """Main function to execute the data loading process."""
    logger.info("Starting Yandex Metrika to PostgreSQL data loader")

    try:
        # Validate configuration
        logger.info("Validating configuration...")
        Config.validate()
        logger.info("Configuration validated successfully")

        # Initialize Yandex Metrika client
        logger.info("Initializing Yandex Metrika client...")
        ym_client = YandexMetrikaClient(Config.YM_TOKEN, Config.YM_COUNTER_ID)

        # Initialize database manager
        logger.info("Initializing database connection...")
        db_manager = DatabaseManager(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            dbname=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )

        # Connect to database
        db_manager.connect()

        # Test connection
        logger.info("Testing database connection...")
        version = db_manager.test_connection()
        logger.info(f"Connected to: {version}")

        # Create table if not exists
        logger.info(f"Creating table '{Config.TABLE_NAME}' if not exists...")
        db_manager.create_table(Config.TABLE_NAME)

        # Export data from Yandex Metrika
        logger.info(f"Exporting data from Yandex Metrika (from {Config.START_DATE} to {Config.END_DATE})...")
        data, valid_fields = ym_client.export_visits_data(
            date1=Config.START_DATE,
            date2=Config.END_DATE,
            fields=FIELDS
        )

        if not data:
            logger.warning("No data retrieved from Yandex Metrika")
            return

        logger.info(f"Retrieved {len(data)} rows from Yandex Metrika with {len(valid_fields)} fields")

        # Insert data into database
        logger.info("Inserting data into database...")
        rows_inserted = db_manager.insert_data(Config.TABLE_NAME, data, valid_fields)
        logger.info(f"Successfully inserted {rows_inserted} rows into database")

        # Close database connection
        db_manager.close()

        logger.info("Data loading completed successfully!")

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please check your .env file and ensure all required variables are set")
        sys.exit(1)
    except ConnectionError as e:
        logger.error(f"Connection error: {e}")
        logger.error("Please check your network connection and credentials")
        sys.exit(1)
    except TimeoutError as e:
        logger.error(f"Timeout error: {e}")
        logger.error("The request took too long to process. Try reducing the date range")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
