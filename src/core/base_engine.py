from abc import ABC, abstractmethod
import pandas as pd
from typing import Union, List, Dict

class BaseEngine(ABC):
    """
    Abstract Base Class for all data extraction engines.
    """
    @abstractmethod
    def fetch(self, sql: str, **kwargs) -> Union[pd.DataFrame, List[Dict]]:
        """
        Execute SQL and return data.
        """
        pass
