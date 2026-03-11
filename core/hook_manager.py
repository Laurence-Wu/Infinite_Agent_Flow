import threading
from typing import Any, Callable, Dict, List


class HookManager:
    """
    Manages hooks and events for a multi-agent system.
    Provides a registration space for hooks and stores properties related to active agents/workflows.
    """

    def __init__(self):
        self._lock = threading.Lock()
        # Maps event_name -> list of callback functions
        self._hooks: Dict[str, List[Callable[..., Any]]] = {}

        # Centralized properties, e.g., active workflows across multiple agents
        self._properties: Dict[str, Any] = {
            "active_workflows": {},  # agent_id/workflow_id -> workflow_state
            "agents": {},  # agent_id -> agent_info
        }

    def register_hook(self, event_name: str, callback: Callable[..., Any]) -> None:
        """Register a callback for a specific event."""
        with self._lock:
            if event_name not in self._hooks:
                self._hooks[event_name] = []
            if callback not in self._hooks[event_name]:
                self._hooks[event_name].append(callback)

    def unregister_hook(self, event_name: str, callback: Callable[..., Any]) -> None:
        """Unregister a specific callback for an event."""
        with self._lock:
            if event_name in self._hooks and callback in self._hooks[event_name]:
                self._hooks[event_name].remove(callback)

    def trigger_hook(self, event_name: str, *args, **kwargs) -> None:
        """Trigger all callbacks registered for the given event."""
        # Make a copy of callbacks to prevent deadlocks or modifications during iteration
        with self._lock:
            callbacks = self._hooks.get(event_name, []).copy()

        for callback in callbacks:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                # Optionally log the error; keeping it simple for now
                pass

    def set_property(self, key: str, value: Any) -> None:
        """Set a global property in the hook manager."""
        with self._lock:
            self._properties[key] = value
        self.trigger_hook(f"property_changed_{key}", value=value)

    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a global property from the hook manager."""
        with self._lock:
            return self._properties.get(key, default)

    def update_agent_workflow(
        self, agent_id: str, workflow_data: Dict[str, Any]
    ) -> None:
        """
        Update the workflow information for a specific agent.
        This allows the web page to show information about all currently active workflows.
        """
        with self._lock:
            if "active_workflows" not in self._properties:
                self._properties["active_workflows"] = {}

            if agent_id not in self._properties["active_workflows"]:
                self._properties["active_workflows"][agent_id] = {}

            self._properties["active_workflows"][agent_id].update(workflow_data)

        self.trigger_hook(
            "on_workflow_updated", agent_id=agent_id, workflow_data=workflow_data
        )

    def get_all_active_workflows(self) -> Dict[str, Any]:
        """Return information about all currently active workflows."""
        with self._lock:
            return self._properties.get("active_workflows", {}).copy()
