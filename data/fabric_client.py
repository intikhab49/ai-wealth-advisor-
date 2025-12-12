"""Microsoft Fabric OneLake data client."""
import os
from typing import Optional, Dict, Any, List
import json


class FabricClient:
    """
    Client for interacting with Microsoft Fabric OneLake/Lakehouse.
    
    This is a template implementation. Enable full functionality by:
    1. Installing azure packages: pip install azure-identity azure-storage-file-datalake
    2. Configuring AZURE_TENANT_ID, AZURE_CLIENT_ID environment variables
    3. Setting up a Fabric workspace with Lakehouse
    """
    
    def __init__(
        self,
        workspace_id: Optional[str] = None,
        lakehouse_name: Optional[str] = None
    ):
        """
        Initialize Fabric client.
        
        Args:
            workspace_id: Microsoft Fabric workspace ID
            lakehouse_name: Name of the Lakehouse
        """
        self.workspace_id = workspace_id or os.getenv("FABRIC_WORKSPACE_ID")
        self.lakehouse_name = lakehouse_name or os.getenv("FABRIC_LAKEHOUSE_NAME")
        self.is_configured = bool(self.workspace_id and self.lakehouse_name)
        
        self._client = None
        self._file_system = None
        
        if self.is_configured:
            self._init_client()
    
    def _init_client(self):
        """Initialize Azure Data Lake client."""
        try:
            from azure.identity import DefaultAzureCredential
            from azure.storage.filedatalake import DataLakeServiceClient
            
            # OneLake endpoint
            account_url = f"https://onelake.dfs.fabric.microsoft.com"
            
            credential = DefaultAzureCredential()
            self._client = DataLakeServiceClient(
                account_url=account_url,
                credential=credential
            )
            
            # Get file system (Lakehouse)
            self._file_system = self._client.get_file_system_client(
                f"{self.workspace_id}/{self.lakehouse_name}"
            )
            
        except ImportError:
            print("Azure packages not installed. Install with: pip install azure-identity azure-storage-file-datalake")
            self.is_configured = False
        except Exception as e:
            print(f"Failed to initialize Fabric client: {e}")
            self.is_configured = False
    
    def read_json(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Read JSON file from OneLake.
        
        Args:
            path: Path in lakehouse (e.g., "Files/portfolios/user123.json")
        
        Returns:
            Parsed JSON data or None
        """
        if not self.is_configured or not self._file_system:
            return None
        
        try:
            file_client = self._file_system.get_file_client(path)
            download = file_client.download_file()
            content = download.readall().decode('utf-8')
            return json.loads(content)
        except Exception as e:
            print(f"Error reading from Fabric: {e}")
            return None
    
    def write_json(self, path: str, data: Dict[str, Any]) -> bool:
        """
        Write JSON data to OneLake.
        
        Args:
            path: Path in lakehouse
            data: Dictionary to write as JSON
        
        Returns:
            Success status
        """
        if not self.is_configured or not self._file_system:
            return False
        
        try:
            file_client = self._file_system.get_file_client(path)
            content = json.dumps(data, indent=2).encode('utf-8')
            file_client.upload_data(content, overwrite=True)
            return True
        except Exception as e:
            print(f"Error writing to Fabric: {e}")
            return False
    
    def list_files(self, directory: str = "Files") -> List[str]:
        """
        List files in a directory.
        
        Args:
            directory: Directory path in lakehouse
        
        Returns:
            List of file paths
        """
        if not self.is_configured or not self._file_system:
            return []
        
        try:
            paths = self._file_system.get_paths(path=directory)
            return [p.name for p in paths]
        except Exception as e:
            print(f"Error listing files: {e}")
            return []
    
    def save_portfolio(self, user_id: str, portfolio: Dict[str, Any]) -> bool:
        """Save user portfolio to Fabric."""
        path = f"Files/portfolios/{user_id}.json"
        return self.write_json(path, portfolio)
    
    def load_portfolio(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Load user portfolio from Fabric."""
        path = f"Files/portfolios/{user_id}.json"
        return self.read_json(path)
    
    def save_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Save user preferences to Fabric."""
        path = f"Files/preferences/{user_id}.json"
        return self.write_json(path, preferences)
    
    def load_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Load user preferences from Fabric."""
        path = f"Files/preferences/{user_id}.json"
        return self.read_json(path)


# Local file-based fallback when Fabric is not configured
class LocalStorageClient:
    """Fallback local storage when Fabric is not available."""
    
    def __init__(self, storage_dir: str = "./local_data"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
    
    def save_portfolio(self, user_id: str, portfolio: Dict[str, Any]) -> bool:
        path = os.path.join(self.storage_dir, f"portfolio_{user_id}.json")
        try:
            with open(path, 'w') as f:
                json.dump(portfolio, f, indent=2)
            return True
        except Exception:
            return False
    
    def load_portfolio(self, user_id: str) -> Optional[Dict[str, Any]]:
        path = os.path.join(self.storage_dir, f"portfolio_{user_id}.json")
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception:
            return None


def get_storage_client():
    """Get appropriate storage client based on configuration."""
    fabric = FabricClient()
    if fabric.is_configured:
        return fabric
    return LocalStorageClient()
