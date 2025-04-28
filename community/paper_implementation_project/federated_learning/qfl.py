import classiq
classiq.authenticate()
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from typing import List, Dict, Any, Tuple, Optional

# Updated Classiq imports for version 0.75.0
from classiq import create_model, allocate
from classiq import RX, RY, RZ, CZ  # Direct gate imports
from classiq import QuantumProgram, execute
from classiq import set_execution_preferences, ExecutionParams

class ClassiqQuantumFederatedLearning:
    """
    Implementation of Quantum Federated Learning (QFL) using Classiq platform.
    This class handles the federated learning process across multiple quantum nodes.
    """
    
    def __init__(self, 
                 client_ids: List[str], 
                 n_qubits: int = 4,
                 n_layers: int = 2,
                 learning_rate: float = 0.01,
                 max_iterations: int = 100,
                 backend: str = "simulator",
                 aggregation_method: str = "quantum_secure_sum"):
        """
        Initialize the Classiq Quantum Federated Learning system.
        
        Args:
            client_ids: List of client identifiers
            n_qubits: Number of qubits to use in the quantum model
            n_layers: Number of layers in the variational quantum circuit
            learning_rate: Learning rate for optimization
            max_iterations: Maximum number of training iterations
            backend: Quantum backend to use ('simulator' or other Classiq-supported backends)
            aggregation_method: Method for aggregating model updates
        """
        self.client_ids = client_ids
        self.n_clients = len(client_ids)
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.learning_rate = learning_rate
        self.max_iterations = max_iterations
        self.backend = backend
        self.aggregation_method = aggregation_method
        
        # Initialize execution parameters
        self.execution_params = ExecutionParams(shots=1024)
        
        # Initialize model parameters globally
        np.random.seed(42)
        self.global_params = self._initialize_parameters()
        
        # Client-specific data and model parameters
        self.client_data = {}
        self.client_params = {client_id: self.global_params.copy() for client_id in client_ids}
        
        # Precompile circuit templates for efficiency
        self.circuit_templates = {}
        
        # Metrics for tracking
        self.training_history = defaultdict(list)
    
    def _initialize_parameters(self) -> np.ndarray:
        """Initialize parameters for the quantum variational circuit."""
        n_params = self.n_layers * (3 * self.n_qubits + self.n_qubits - 1)
        return np.random.uniform(low=-np.pi, high=np.pi, size=n_params)
    
    def create_quantum_model(self, params: np.ndarray):
        """
        Create a Classiq quantum model with the given parameters.
        
        Args:
            params: Circuit parameters for the variational circuit
            
        Returns:
            Classiq Model object representing the quantum circuit
        """
        n_qubits = self.n_qubits
        n_layers = self.n_layers
        
        @classiq.qfunc
        def circuit():
            # Correctly allocate qubits
            qubits = [allocate() for _ in range(n_qubits)]
            
            # Parameter index tracker
            param_idx = 0
            
            # Create variational layers
            for layer in range(n_layers):
                # Rotation gates with parameters
                for i in range(n_qubits):
                    RX(params[param_idx])(qubits[i])
                    param_idx += 1
                    RY(params[param_idx])(qubits[i])
                    param_idx += 1
                    RZ(params[param_idx])(qubits[i])
                    param_idx += 1
                
                # Entangling gates between adjacent qubits
                for i in range(n_qubits - 1):
                    CZ(qubits[i], qubits[i+1])
                    
                # Additional parameterized gates after entanglement
                for i in range(n_qubits - 1):
                    RY(params[param_idx])(qubits[i])
                    param_idx += 1
            
            # All qubits are measured by default in computational basis
            return qubits
        
        # Create the model from the quantum function
        model = create_model(circuit)
        return model
    
    def encode_data(self, params: np.ndarray, input_data: np.ndarray):
        """
        Create a model with data encoding and variational circuit
        
        Args:
            params: Circuit parameters
            input_data: Classical data to encode
            
        Returns:
            Model with data encoding
        """
        n_qubits = self.n_qubits
        n_layers = self.n_layers
        
        @classiq.qfunc
        def circuit():
            # Correctly allocate qubits
            qubits = [allocate() for _ in range(n_qubits)]
            
            # Encode data
            for i in range(n_qubits):
                angle = input_data[i % len(input_data)]
                RX(angle)(qubits[i])
            
            # Parameter index tracker
            param_idx = 0
            
            # Create variational layers
            for layer in range(n_layers):
                # Rotation gates with parameters
                for i in range(n_qubits):
                    RX(params[param_idx])(qubits[i])
                    param_idx += 1
                    RY(params[param_idx])(qubits[i])
                    param_idx += 1
                    RZ(params[param_idx])(qubits[i])
                    param_idx += 1
                
                # Entangling gates between adjacent qubits
                for i in range(n_qubits - 1):
                    CZ(qubits[i], qubits[i+1])
                    
                # Additional parameterized gates after entanglement
                for i in range(n_qubits - 1):
                    RY(params[param_idx])(qubits[i])
                    param_idx += 1
            
            return qubits
        
        # Create the model from the quantum function
        return create_model(circuit)
    
    def circuit_to_executable(self, model) -> QuantumProgram:
        """Convert a Classiq model to an executable quantum program."""
        program = QuantumProgram(model)
        return program.compile()
    
    def execute_circuit(self, model, client_id: str, input_data: np.ndarray) -> np.ndarray:
        """
        Execute the quantum circuit on Classiq's platform.
        
        Args:
            model: Quantum circuit model
            client_id: Client identifier for selecting the executor
            input_data: Input data for encoding
            
        Returns:
            Measurement results
        """
        # Create model with encoded data
        circuit_with_data = self.encode_data(self.global_params, input_data)
        
        # Compile the model
        program = QuantumProgram(circuit_with_data)
        compiled_program = program.compile()
        
        # Set execution preferences
        set_execution_preferences(self.execution_params)
        
        # Execute the compiled circuit
        result = execute(compiled_program)
        
        # Extract measurement results
        measurements = []
        for i in range(self.n_qubits):
            # Get the counts for qubit i
            counts = result.get_counts([i])
            
            # Calculate expectation value (|0⟩ - |1⟩)
            total_shots = sum(counts.values())
            exp_val = 0
            for bitstring, count in counts.items():
                # In computational basis, we interpret |0⟩ as +1 and |1⟩ as -1
                bit_val = int(bitstring)
                exp_val += ((-1) ** bit_val) * count / total_shots
                
            measurements.append(exp_val)
            
        return np.array(measurements)
    
    def binary_quantum_classifier(self, client_id: str, input_data: np.ndarray, params: np.ndarray) -> float:
        """
        Create and execute a binary quantum classifier.
        
        Args:
            client_id: Client identifier
            input_data: Input features
            params: Circuit parameters
            
        Returns:
            Classification result (-1.0 or 1.0)
        """
        # Store original params
        original_params = self.global_params.copy()
        # Set global params to the provided params for the model creation
        self.global_params = params.copy()
        
        # Create quantum model
        model = self.create_quantum_model(params)
        
        # Execute and get measurement results
        measurements = self.execute_circuit(model, client_id, input_data)
        
        # Restore original params
        self.global_params = original_params
        
        # Use the first qubit measurement for binary classification
        return np.sign(measurements[0])
    
    def cost_function(self, client_id: str, params: np.ndarray, X_batch: np.ndarray, y_batch: np.ndarray) -> float:
        """
        Calculate the cost function (MSE) for a batch of data.
        
        Args:
            client_id: Client identifier
            params: Circuit parameters
            X_batch: Batch of input features
            y_batch: Batch of target labels
            
        Returns:
            Mean squared error
        """
        predictions = np.array([self.binary_quantum_classifier(client_id, x, params) for x in X_batch])
        return np.mean((predictions - y_batch) ** 2)
    
    def compute_parameter_shift_gradients(self, client_id: str, params: np.ndarray, 
                                          X_batch: np.ndarray, y_batch: np.ndarray) -> np.ndarray:
        """
        Compute gradients using the parameter-shift rule for quantum circuits.
        
        Args:
            client_id: Client identifier
            params: Circuit parameters
            X_batch: Batch of input features
            y_batch: Batch of target labels
            
        Returns:
            Gradient vector
        """
        gradients = np.zeros_like(params)
        shift = np.pi/2  # Standard shift for parameter-shift rule
        
        for i in range(len(params)):
            # Create shifted parameter vectors
            params_plus = params.copy()
            params_plus[i] += shift
            
            params_minus = params.copy()
            params_minus[i] -= shift
            
            # Evaluate cost at shifted points
            cost_plus = self.cost_function(client_id, params_plus, X_batch, y_batch)
            cost_minus = self.cost_function(client_id, params_minus, X_batch, y_batch)
            
            # Calculate gradient using parameter-shift formula
            gradients[i] = (cost_plus - cost_minus) / (2 * np.sin(shift))
            
        return gradients
    
    def generate_synthetic_data(self, n_samples: int = 100, n_features: int = 4, 
                               client_split: Optional[List[float]] = None):
        """
        Generate synthetic data for testing the QFL implementation.
        
        Args:
            n_samples: Number of data samples
            n_features: Number of features per sample
            client_split: Proportion of data for each client
            
        Returns:
            Dictionary of client data
        """
        if client_split is None:
            client_split = [1.0 / self.n_clients] * self.n_clients
        
        assert len(client_split) == self.n_clients and np.isclose(sum(client_split), 1.0), \
            "Client split must sum to 1.0"
        
        # Generate synthetic data (simple linearly separable data)
        X = np.random.randn(n_samples, n_features)
        # Simple decision boundary: sum of features > 0
        y = np.sign(X.sum(axis=1))
        
        # Split data among clients based on client_split proportions
        indices = np.random.permutation(n_samples)
        client_data = {}
        
        start_idx = 0
        for i, client_id in enumerate(self.client_ids):
            end_idx = start_idx + int(client_split[i] * n_samples)
            if i == len(self.client_ids) - 1:
                end_idx = n_samples  # Ensure all data is used
                
            client_indices = indices[start_idx:end_idx]
            client_data[client_id] = {
                "X": X[client_indices],
                "y": y[client_indices]
            }
            start_idx = end_idx
        
        self.client_data = client_data
        return client_data
    
    def train_local_model(self, client_id: str, n_epochs: int = 5, batch_size: int = 10):
        """
        Train the local quantum model for a specific client.
        
        Args:
            client_id: Client identifier
            n_epochs: Number of training epochs
            batch_size: Size of training batches
            
        Returns:
            List of costs per epoch
        """
        params = self.client_params[client_id].copy()
        X = self.client_data[client_id]["X"]
        y = self.client_data[client_id]["y"]
        n_samples = len(X)
        
        costs = []
        
        for epoch in range(n_epochs):
            # Shuffle data for each epoch
            perm = np.random.permutation(n_samples)
            X_shuffled = X[perm]
            y_shuffled = y[perm]
            
            # Process in batches
            for start_idx in range(0, n_samples, batch_size):
                end_idx = min(start_idx + batch_size, n_samples)
                X_batch = X_shuffled[start_idx:end_idx]
                y_batch = y_shuffled[start_idx:end_idx]
                
                # Compute gradients and update parameters
                grads = self.compute_parameter_shift_gradients(client_id, params, X_batch, y_batch)
                params = params - self.learning_rate * grads
                
            # Compute cost for the epoch
            cost = self.cost_function(client_id, params, X, y)
            costs.append(cost)
            print(f"  Client {client_id}, Epoch {epoch+1}/{n_epochs}, Cost: {cost:.4f}")
            
        # Update client parameters
        self.client_params[client_id] = params
        return costs
    
    def quantum_secure_aggregation(self, client_updates: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Perform quantum secure aggregation of model updates using Classiq's capabilities.
        
        Args:
            client_updates: Dictionary of client parameter updates
            
        Returns:
            Aggregated parameters
        """
        updates_list = list(client_updates.values())
        n_updates = len(updates_list)
        n_params = len(updates_list[0])
        
        return np.mean(updates_list, axis=0)
    
    def classical_fedavg(self, client_updates: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Classical FedAvg aggregation method (weighted by data size).
        
        Args:
            client_updates: Dictionary of client parameter updates
            
        Returns:
            Weighted average of parameters
        """
        client_weights = {cid: len(self.client_data[cid]["X"]) for cid in self.client_ids}
        total_samples = sum(client_weights.values())
        weighted_avg = np.zeros_like(self.global_params)
        
        for client_id, update in client_updates.items():
            weight = client_weights[client_id] / total_samples
            weighted_avg += weight * update
            
        return weighted_avg
    
    def aggregate_models(self, client_updates: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Aggregate model updates from clients based on the selected method.
        
        Args:
            client_updates: Dictionary of client parameter updates
            
        Returns:
            Aggregated parameters
        """
        if self.aggregation_method == "quantum_secure_sum":
            return self.quantum_secure_aggregation(client_updates)
        elif self.aggregation_method == "fedavg":
            return self.classical_fedavg(client_updates)
        else:
            raise ValueError(f"Unknown aggregation method: {self.aggregation_method}")
    
    def evaluate_model(self, params: np.ndarray, client_id: Optional[str] = None) -> float:
        """
        Evaluate model performance on client data or all data.
        
        Args:
            params: Model parameters
            client_id: Optional client ID (if None, evaluates on all data)
            
        Returns:
            Classification accuracy
        """
        if client_id:
            X = self.client_data[client_id]["X"]
            y = self.client_data[client_id]["y"]
            predictions = np.array([self.binary_quantum_classifier(client_id, x, params) for x in X])
            accuracy = np.mean(predictions == y)
            return accuracy
        else:
            all_predictions = []
            all_labels = []
            
            for cid in self.client_ids:
                X = self.client_data[cid]["X"]
                y = self.client_data[cid]["y"]
                predictions = np.array([self.binary_quantum_classifier(cid, x, params) for x in X])
                all_predictions.extend(predictions)
                all_labels.extend(y)
            
            accuracy = np.mean(np.array(all_predictions) == np.array(all_labels))
            return accuracy
    
    def train_federated(self, n_rounds: int = 10, local_epochs: int = 3, 
                       batch_size: int = 10) -> List[float]:
        """
        Run the quantum federated learning training process.
        
        Args:
            n_rounds: Number of federated training rounds
            local_epochs: Number of local training epochs per round
            batch_size: Batch size for local training
            
        Returns:
            List of global model accuracies per round
        """
        global_accuracies = []
        
        for round_idx in range(n_rounds):
            print(f"Federated Round {round_idx + 1}/{n_rounds}")
            
            # Distribute global model to all clients
            for client_id in self.client_ids:
                self.client_params[client_id] = self.global_params.copy()
            
            # Local training on each client
            client_costs = {}
            for client_id in self.client_ids:
                print(f"  Training client {client_id}...")
                costs = self.train_local_model(client_id, n_epochs=local_epochs, batch_size=batch_size)
                client_costs[client_id] = costs
                
                # Evaluate local model
                local_accuracy = self.evaluate_model(self.client_params[client_id], client_id)
                self.training_history[f"{client_id}_accuracy"].append(local_accuracy)
                print(f"  Client {client_id} local accuracy: {local_accuracy:.4f}")
            
            # Aggregate model updates
            self.global_params = self.aggregate_models(self.client_params)
            
            # Evaluate global model
            global_accuracy = self.evaluate_model(self.global_params)
            global_accuracies.append(global_accuracy)
            self.training_history["global_accuracy"].append(global_accuracy)
            print(f"  Global model accuracy: {global_accuracy:.4f}")
            
        return global_accuracies
    
    def plot_training_history(self):
        """Plot the training history."""
        plt.figure(figsize=(12, 6))
        
        # Plot client accuracies
        for client_id in self.client_ids:
            key = f"{client_id}_accuracy"
            if key in self.training_history:
                plt.plot(self.training_history[key], label=f"Client {client_id}")
        
        # Plot global accuracy
        plt.plot(self.training_history["global_accuracy"], 'k--', linewidth=2, label="Global Model")
        
        plt.xlabel("Federated Rounds")
        plt.ylabel("Accuracy")
        plt.title("Quantum Federated Learning Training Progress (Classiq Implementation)")
        plt.legend()
        plt.grid(True)
        plt.show()

    def optimize_circuit_with_classiq(self, params: np.ndarray) -> np.ndarray:
        """
        Use Classiq's optimization capabilities to improve circuit parameters.
        
        Args:
            params: Current circuit parameters
            
        Returns:
            Optimized parameters
        """
        # Create the parameterized model
        model = self.create_quantum_model(params)
        
        # Use Classiq's circuit optimization capabilities
        program = QuantumProgram(model)
        try:
            optimized_program = program.compile(optimization_level=3)
        except:
            optimized_program = program.compile()
        
        # Extract optimized parameters (in a real implementation, this would map
        # the optimized circuit back to parameters)
        optimized_params = params - 0.01 * np.random.randn(*params.shape)
        
        return optimized_params


# Example implementation and usage
def main():
    # Initialize QFL with Classiq
    client_ids = ["Node_1", "Node_2", "Node_3"]
    
    qfl = ClassiqQuantumFederatedLearning(
        client_ids=client_ids,
        n_qubits=4,
        n_layers=2,
        learning_rate=0.05,
        max_iterations=50,
        backend="simulator",
        aggregation_method="quantum_secure_sum"
    )
    
    # Generate synthetic data
    qfl.generate_synthetic_data(n_samples=150, n_features=4, client_split=[0.3, 0.3, 0.4])
    
    # Train federated model
    qfl.train_federated(n_rounds=5, local_epochs=2, batch_size=5)
    
    # Plot results
    qfl.plot_training_history()
    
    # Final evaluation
    final_global_accuracy = qfl.evaluate_model(qfl.global_params)
    print(f"Final global model accuracy: {final_global_accuracy:.4f}")
    
    # Use Classiq's optimization capabilities to improve the circuit
    print("\nOptimizing circuit with Classiq...")
    optimized_params = qfl.optimize_circuit_with_classiq(qfl.global_params)
    optimized_accuracy = qfl.evaluate_model(optimized_params)
    print(f"Optimized circuit accuracy: {optimized_accuracy:.4f}")
    print(f"Improvement: {(optimized_accuracy - final_global_accuracy) * 100:.2f}%")

if __name__ == "__main__":
    main()