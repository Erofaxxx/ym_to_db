"""Yandex Metrika API client for data export."""

import requests
import time
import logging
import re
import json

logger = logging.getLogger(__name__)


class YandexMetrikaClient:
    """Client for Yandex Metrika API."""

    API_BASE_URL = "https://api-metrika.yandex.net/management/v1"
    LOGSAPI_BASE_URL = "https://api-metrika.yandex.net/management/v1/counter/{counter_id}/logrequests"

    def __init__(self, token, counter_id):
        """Initialize Yandex Metrika client."""
        self.token = token
        self.counter_id = counter_id
        self.headers = {
            'Authorization': f'OAuth {token}',
            'Content-Type': 'application/json'
        }

    def create_log_request(self, date1, date2, fields):
        """Create a log request for visits data.

        Automatically detects and filters out invalid fields by retrying on error.
        """
        url = self.LOGSAPI_BASE_URL.format(counter_id=self.counter_id)

        valid_fields = list(fields)  # Make a copy
        invalid_fields = []

        while True:
            params = {
                'date1': date1,
                'date2': date2,
                'fields': ','.join(valid_fields),
                'source': 'visits'
            }

            try:
                response = requests.post(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                request_id = data['log_request']['request_id']

                if invalid_fields:
                    logger.warning(f"Filtered out {len(invalid_fields)} invalid fields: {', '.join(invalid_fields)}")

                logger.info(f"Created log request with ID: {request_id} using {len(valid_fields)} fields")
                return request_id, valid_fields

            except requests.exceptions.HTTPError as e:
                if e.response is not None and e.response.status_code == 400:
                    try:
                        error_data = e.response.json()
                        error_message = error_data.get('message', '')

                        # Try to extract the invalid field name from error message
                        # Format: "Unknown field in the request: ym:s:FieldName for the source visits"
                        match = re.search(r'Unknown field in the request: (ym:s:\w+)', error_message)

                        if match:
                            invalid_field = match.group(1)
                            if invalid_field in valid_fields:
                                logger.warning(f"Field '{invalid_field}' is not supported for visits source, removing it")
                                valid_fields.remove(invalid_field)
                                invalid_fields.append(invalid_field)
                                continue  # Retry with updated field list
                    except (json.JSONDecodeError, KeyError):
                        pass

                # If we can't parse the error or it's not a field error, raise it
                logger.error(f"Failed to create log request: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"Response: {e.response.text}")
                raise
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to create log request: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"Response: {e.response.text}")
                raise

    def check_request_status(self, request_id):
        """Check the status of a log request."""
        url = f"{self.LOGSAPI_BASE_URL.format(counter_id=self.counter_id)}/{request_id}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            status = data['log_request']['status']
            logger.info(f"Request {request_id} status: {status}")
            return status
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to check request status: {e}")
            raise

    def wait_for_request(self, request_id, max_wait_time=600, check_interval=10):
        """Wait for log request to be processed."""
        start_time = time.time()

        while True:
            if time.time() - start_time > max_wait_time:
                raise TimeoutError(f"Request {request_id} did not complete within {max_wait_time} seconds")

            status = self.check_request_status(request_id)

            if status == 'processed':
                logger.info(f"Request {request_id} processed successfully")
                return True
            elif status == 'processing_failed' or status == 'canceled':
                raise Exception(f"Request {request_id} failed with status: {status}")

            logger.info(f"Waiting for request {request_id} to complete... (status: {status})")
            time.sleep(check_interval)

    def get_request_info(self, request_id):
        """Get information about a processed log request."""
        url = f"{self.LOGSAPI_BASE_URL.format(counter_id=self.counter_id)}/{request_id}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data['log_request']
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get request info: {e}")
            raise

    def download_data(self, request_id, part_number=0):
        """Download data from a processed log request."""
        url = f"{self.LOGSAPI_BASE_URL.format(counter_id=self.counter_id)}/{request_id}/part/{part_number}/download"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            # Parse TSV data
            lines = response.text.strip().split('\n')
            if not lines:
                return []

            # First line is header
            headers = lines[0].split('\t')

            # Parse data rows
            data = []
            for line in lines[1:]:
                values = line.split('\t')
                row = dict(zip(headers, values))
                data.append(row)

            logger.info(f"Downloaded {len(data)} rows from part {part_number}")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download data: {e}")
            raise

    def export_visits_data(self, date1, date2, fields):
        """Export visits data for the specified date range.

        Returns tuple of (data, valid_fields) where valid_fields contains
        only the fields that were successfully exported.
        """
        logger.info(f"Starting data export from {date1} to {date2}")

        # Create log request (now returns valid fields)
        request_id, valid_fields = self.create_log_request(date1, date2, fields)

        # Wait for processing
        self.wait_for_request(request_id)

        # Get request info to check for parts
        request_info = self.get_request_info(request_id)
        parts = request_info.get('parts', [])

        if not parts:
            logger.warning("No data parts available")
            return [], valid_fields

        # Download all parts
        all_data = []
        for part in parts:
            part_number = part['part_number']
            data = self.download_data(request_id, part_number)
            all_data.extend(data)

        logger.info(f"Total rows exported: {len(all_data)}")
        return all_data, valid_fields
