import time
import pandas as pd
import numpy as np
import gspread
import re
from gspread.exceptions import APIError
from google.oauth2.service_account import Credentials
from gspread.worksheet import ValueRange


class GSheetImporter:
    """
    A class to authenticate with Google Sheets API using a service account
    and load worksheet data into a Pandas DataFrame with automatic backoff logic.
    """
    DEFAULT_SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]

    def __init__(
        self, 
        sheet_id: str, 
        sheet_name: str, 
        credentials_path: str, 
        scopes: list = None,
        max_retries: int = 10,
        initial_wait: float = 0.1,
        backoff_factor: float = 2.0
    ):
        """
        Parameters:
            sheet_id (str): The unique ID from the Google Sheet URL.
            sheet_name (str): The specific tab/worksheet name.
            credentials_path (str): Path to the service account JSON file.
            scopes (list, optional): Custom OAuth scopes if defaults need overriding.
            max_retries (int): Maximum number of retry attempts for quota limits.
            initial_wait (float): Base delay (seconds) before the first retry.
            backoff_factor (float): Multiplier applied to delay after each retry.
        """
        self.sheet_id = sheet_id
        self.sheet_name = sheet_name
        self.credentials_path = credentials_path
        self.scopes = scopes or self.DEFAULT_SCOPES
        
        # Retry Configuration
        self.max_retries = max_retries
        self.initial_wait = initial_wait
        self.backoff_factor = backoff_factor
        
        # DataFrame attribute initialized to None
        self.df: pd.DataFrame | None = None
        
        self.client = self._authenticate()
        

    def _authenticate(self) -> gspread.Client:
        """Private method to handle Google API authentication."""
        creds = Credentials.from_service_account_file(
            self.credentials_path, 
            scopes=self.scopes
        )
        return gspread.authorize(creds)

    def _execute_with_retry(self, func, *args, **kwargs):
        """Helper method to handle exponential backoff on API rate limit/quota errors."""
        wait_time = self.initial_wait
        for attempt in range(1, self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except APIError as e:
                # Check for rate limit or quota exceeded status codes (e.g., 429)
                is_quota_error = e.response is not None and e.response.status_code == 429
                
                if is_quota_error and attempt < self.max_retries:
                    print(
                        f"Quota reached (429). Retrying in {wait_time:.1f} seconds... "
                        f"(Attempt {attempt}/{self.max_retries})"
                    )
                    time.sleep(wait_time)
                    wait_time *= self.backoff_factor
                else:
                    raise e

    def get_dataframe(self, expected_columns: list = None) -> pd.DataFrame:
        """
        Fetches worksheet data with retry logic and converts it to a Pandas DataFrame.
        
        Parameters:
            expected_columns (list, optional): Columns to be returned. All 
            missing values if a column doesn't exist.
            
        Returns:
            pd.DataFrame: Loaded contents of the sheet.
        """
        # Wrap API calls in retry execution logic
        spreadsheet = self._execute_with_retry(self.client.open_by_key, self.sheet_id)
        worksheet = self._execute_with_retry(spreadsheet.worksheet, self.sheet_name)
        records = self._execute_with_retry(worksheet.get_all_records)
        
        df = pd.DataFrame(records)

        if expected_columns:
            for col in expected_columns:
                if col not in df.columns:
                    df[col] = None
            out = df[expected_columns].copy()
        else:
            out = df
            
        self.df = out
        return self.df
    
    def get_all_values(self) -> ValueRange | list[list[any]]:
        """
        Fetches worksheet data with retry logic and converts it to a 2D list.
                    
        Returns:
            ValueRange or 2D List: Loaded contents of the sheet.
        """
        # Wrap API calls in retry execution logic
        spreadsheet = self._execute_with_retry(self.client.open_by_key, self.sheet_id)
        worksheet = self._execute_with_retry(spreadsheet.worksheet, self.sheet_name)
        self.all_values = self._execute_with_retry(worksheet.get_all_values)
        
        return self.all_values
    
    def to_num(self, num_cols: list[str]) -> pd.DataFrame:
        """
        Performs data cleaning operations on specified columns of self.df.
        
        Raises:
            UnboundLocalError/AttributeError if to_dataframe() hasn't been called.
            KeyError if any requested column is missing.
        """
        # Exception handling if called before to_dataframe()
        if self.df is None:
            raise RuntimeError(
                "DataFrame has not been loaded yet. Call 'to_dataframe()' "
                "before running operations on columns."
            )

        # Ensure requested columns exist in self.df
        missing_cols = [col for col in num_cols if col not in self.df.columns]
        if missing_cols:
            raise KeyError(f"The following columns were not found in the DataFrame: {missing_cols}")

        # Example processing tasks: trim whitespace, fill NAs, and cast text to lowercase
        self.df[num_cols] = self.df[num_cols].fillna('0')
        self.df[num_cols] = self.df[num_cols].replace('', np.nan)
        for c in num_cols:
            self.df[c] = self.df[c].apply(lambda x: float(re.sub(r"\(", "-", re.sub(r"[,\)]", "", str(x)))))

        return self.df