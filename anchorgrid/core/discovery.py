"""
AnchorGrid Discovery Protocol

Proof-of-Integrity Discovery (PoID) - The Bouncer for Agent Networks

Unlike AgentGrid (open network), AnchorGrid requires cryptographic proof
of Anchor compliance before agents can join.
"""

from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger


class AgentInfo:
    """Information about a registered agent"""
    
    def __init__(
        self,
        agent_id: str,
        capabilities: List[str],
        anchor_score: int,
        policy: str,
        cert_hash: str,
        expires_at: datetime
    ):
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.anchor_score = anchor_score
        self.policy = policy
        self.cert_hash = cert_hash
        self.registered_at = datetime.now()
        self.expires_at = expires_at
        self.status = "active"
    
    def is_expired(self) -> bool:
        """Check if Anchor certificate has expired"""
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> dict:
        """Serialize to dictionary"""
        return {
            "agent_id": self.agent_id,
            "capabilities": self.capabilities,
            "anchor_score": self.anchor_score,
            "policy": self.policy,
            "cert_hash": self.cert_hash,
            "registered_at": self.registered_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "status": self.status
        }


class RegistrationError(Exception):
    """Raised when agent registration fails verification"""
    pass


class DiscoveryProtocol:
    """
    Governed Agent Discovery with Anchor Verification
    
    The Killer Feature: Unlike AgentGrid, agents must prove
    Anchor compliance before they can even join the network.
    """
    
    def __init__(self):
        self.peers: Dict[str, AgentInfo] = {}
        logger.info("🔍 Discovery Protocol initialized (PoID enabled)")
    
    def register_agent(
        self,
        agent_id: str,
        capabilities: List[str],
        anchor_cert: dict,
        policy: str
    ) -> AgentInfo:
        """
        Register agent with Anchor verification
        
        Args:
            agent_id: Unique identifier for agent
            capabilities: List of capabilities (e.g., ["finance", "analysis"])
            anchor_cert: Anchor compliance certificate (dict with score, hash, expires)
            policy: Policy name (e.g., "finos-financial", "owasp-agentic")
        
        Returns:
            AgentInfo: Registered agent information
        
        Raises:
            RegistrationError: If verification fails
        """
        logger.info(f"📋 Registration request from: {agent_id}")
        
        # THE BOUNCER: Verify Anchor certificate
        # (In Phase 4.2, this will call actual Anchor verification)
        # For now, we do basic validation
        
        if not anchor_cert:
            raise RegistrationError("No Anchor certificate provided")
        
        # Extract certificate fields
        score = anchor_cert.get("score", 0)
        cert_hash = anchor_cert.get("hash", "")
        expires_str = anchor_cert.get("expires", "")
        
        # Validate score
        if score < 95:
            raise RegistrationError(
                f"Trust score too low: {score}% (minimum: 95%)"
            )
        
        # Parse expiration
        try:
            expires_at = datetime.fromisoformat(expires_str)
        except ValueError:
            raise RegistrationError("Invalid certificate expiration date")
        
        # Check expiration
        if datetime.now() > expires_at:
            raise RegistrationError("Certificate expired")
        
        # Check if agent already registered
        if agent_id in self.peers:
            logger.warning(f"⚠️  Agent {agent_id} already registered, updating...")
            del self.peers[agent_id]
        
        # Create agent info
        agent_info = AgentInfo(
            agent_id=agent_id,
            capabilities=capabilities,
            anchor_score=score,
            policy=policy,
            cert_hash=cert_hash,
            expires_at=expires_at
        )
        
        # Add to peer list
        self.peers[agent_id] = agent_info
        
        logger.info(
            f"✅ Registered: {agent_id} "
            f"(score: {score}%, policy: {policy})"
        )
        
        return agent_info
    
    def discover(
        self,
        capability: Optional[str] = None,
        min_score: int = 95,
        policy: Optional[str] = None
    ) -> List[AgentInfo]:
        """
        Discover agents by capability, trust score, and policy
        
        Args:
            capability: Required capability (e.g., "finance")
            min_score: Minimum Anchor score (default: 95%)
            policy: Required policy (e.g., "finos-financial")
        
        Returns:
            List of matching agent info objects
        """
        results = []
        
        for agent_info in self.peers.values():
            # Skip expired agents
            if agent_info.is_expired():
                continue
            
            # Filter by capability
            if capability and capability not in agent_info.capabilities:
                continue
            
            # Filter by minimum score
            if agent_info.anchor_score < min_score:
                continue
            
            # Filter by policy
            if policy and agent_info.policy != policy:
                continue
            
            results.append(agent_info)
        
        logger.info(
            f"🔍 Discovery: {len(results)} agents found "
            f"(capability={capability}, min_score={min_score})"
        )
        
        return results
    
    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Get agent info by ID"""
        return self.peers.get(agent_id)
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Remove agent from network"""
        if agent_id in self.peers:
            del self.peers[agent_id]
            logger.info(f"🗑️  Unregistered: {agent_id}")
            return True
        return False
    
    def cleanup_expired(self) -> int:
        """Remove expired agents, return count"""
        expired = [
            agent_id for agent_id, info in self.peers.items()
            if info.is_expired()
        ]
        
        for agent_id in expired:
            del self.peers[agent_id]
        
        if expired:
            logger.info(f"🗑️  Cleaned up {len(expired)} expired agents")
        
        return len(expired)
    
    def list_all(self) -> List[AgentInfo]:
        """List all registered agents"""
        return list(self.peers.values())


# Singleton instance
discovery = DiscoveryProtocol()
