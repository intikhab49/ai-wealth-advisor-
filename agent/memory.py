"""ChromaDB conversation memory for personalized recommendations."""
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import json


@dataclass
class ConversationMessage:
    """A single conversation message."""
    role: str  # user, assistant
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class FinancialMemory:
    """
    Manages conversation history and user preferences using ChromaDB.
    Provides long-term memory for personalized financial recommendations.
    """
    
    def __init__(self, user_id: str = "default", persist_directory: str = "./chroma_db"):
        """
        Initialize memory for a specific user.
        
        Args:
            user_id: Unique identifier for the user
            persist_directory: Directory to persist ChromaDB data
        """
        self.user_id = user_id
        self.persist_directory = persist_directory
        self.conversation_history: List[ConversationMessage] = []
        self.user_preferences: Dict[str, Any] = {}
        self.portfolio_data: Optional[Dict[str, Any]] = None
        
        # Initialize ChromaDB
        self._init_chromadb()
    
    def _init_chromadb(self):
        """Initialize ChromaDB client and collections."""
        try:
            import chromadb
            from chromadb.config import Settings
            
            os.makedirs(self.persist_directory, exist_ok=True)
            
            self.client = chromadb.Client(Settings(
                persist_directory=self.persist_directory,
                anonymized_telemetry=False
            ))
            
            # Collection for conversation history
            self.conversations = self.client.get_or_create_collection(
                name=f"conversations_{self.user_id}",
                metadata={"description": "Conversation history for financial advice"}
            )
            
            # Collection for user preferences
            self.preferences = self.client.get_or_create_collection(
                name=f"preferences_{self.user_id}",
                metadata={"description": "User financial preferences and profile"}
            )
            
            # Load existing preferences
            self._load_preferences()
            
        except ImportError:
            print("ChromaDB not installed. Using in-memory storage only.")
            self.client = None
            self.conversations = None
            self.preferences = None
    
    def _load_preferences(self):
        """Load user preferences from ChromaDB."""
        if not self.preferences:
            return
        
        try:
            results = self.preferences.get(
                where={"user_id": self.user_id},
                limit=1
            )
            if results and results["documents"]:
                self.user_preferences = json.loads(results["documents"][0])
        except Exception:
            pass
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """
        Add a message to conversation history.
        
        Args:
            role: 'user' or 'assistant'
            content: Message content
            metadata: Optional metadata (e.g., tools used, portfolio analyzed)
        """
        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.conversation_history.append(message)
        
        # Store in ChromaDB for long-term retrieval
        if self.conversations:
            try:
                self.conversations.add(
                    documents=[content],
                    metadatas=[{
                        "role": role,
                        "user_id": self.user_id,
                        **(metadata or {})
                    }],
                    ids=[f"{self.user_id}_{len(self.conversation_history)}"]
                )
            except Exception:
                pass
    
    def get_recent_messages(self, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation messages for context."""
        recent = self.conversation_history[-limit:]
        return [{"role": m.role, "content": m.content} for m in recent]
    
    def get_context_for_query(self, query: str, limit: int = 5) -> str:
        """
        Retrieve relevant context for a query using semantic search.
        
        Args:
            query: User's current query
            limit: Number of relevant messages to retrieve
        
        Returns:
            Concatenated relevant context
        """
        if not self.conversations:
            return ""
        
        try:
            results = self.conversations.query(
                query_texts=[query],
                n_results=limit
            )
            
            if results and results["documents"]:
                context_parts = []
                for doc, metadata in zip(results["documents"][0], results["metadatas"][0]):
                    role = metadata.get("role", "unknown")
                    context_parts.append(f"[{role}]: {doc[:500]}")
                return "\n".join(context_parts)
        except Exception:
            pass
        
        return ""
    
    def save_preferences(self, preferences: Dict[str, Any]):
        """
        Save user financial preferences.
        
        Args:
            preferences: Dictionary with keys like:
                - risk_tolerance
                - investment_goals
                - time_horizon
                - income
                - age
        """
        self.user_preferences.update(preferences)
        
        if self.preferences:
            try:
                # Upsert preferences
                self.preferences.upsert(
                    documents=[json.dumps(self.user_preferences)],
                    metadatas=[{"user_id": self.user_id}],
                    ids=[f"prefs_{self.user_id}"]
                )
            except Exception:
                pass
    
    def get_preferences(self) -> Dict[str, Any]:
        """Get user's saved preferences."""
        return self.user_preferences
    
    def save_portfolio(self, portfolio: Dict[str, Any]):
        """Save user's portfolio data for reference."""
        self.portfolio_data = portfolio
    
    def get_portfolio(self) -> Optional[Dict[str, Any]]:
        """Get user's saved portfolio."""
        return self.portfolio_data
    
    def clear_history(self):
        """Clear conversation history (but keep preferences)."""
        self.conversation_history = []
        if self.conversations:
            try:
                # Delete all documents for this user
                all_ids = self.conversations.get(
                    where={"user_id": self.user_id}
                )
                if all_ids and all_ids["ids"]:
                    self.conversations.delete(ids=all_ids["ids"])
            except Exception:
                pass
    
    def get_memory_summary(self) -> str:
        """Get a summary of what the memory knows about the user."""
        summary_parts = []
        
        if self.user_preferences:
            summary_parts.append("**User Profile:**")
            for key, value in self.user_preferences.items():
                summary_parts.append(f"- {key.replace('_', ' ').title()}: {value}")
        
        if self.portfolio_data:
            total_value = sum(
                float(h.get("value", 0)) 
                for h in self.portfolio_data.get("holdings", [])
            )
            summary_parts.append(f"\n**Portfolio Value:** ${total_value:,.2f}")
        
        summary_parts.append(f"\n**Conversation History:** {len(self.conversation_history)} messages")
        
        return "\n".join(summary_parts) if summary_parts else "No user data stored yet."
