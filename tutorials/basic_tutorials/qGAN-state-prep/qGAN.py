# Imports
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import TensorDataset, DataLoader
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit.circuit.library import TwoLocal
from qiskit_aer.primitives import Sampler
from tqdm import tqdm
import matplotlib.pyplot as plt
from IPython.display import clear_output

class qGAN:
    """
    Complete optimized Quantum Generative Adversarial Network implementation
    with enhanced loss functions, parameter update methods, and improved training dynamics.
    
    Key improvements over the original:
    - Momentum-based parameter updates with adaptive learning rates
    - Enhanced discriminator loss with label smoothing and optional gradient penalty
    - Better regularization with improved KL divergence and entropy calculations
    - Spectral normalization support for discriminator stability
    - Comprehensive training monitoring and visualization
    """

    def __init__(
        self, model, samples, rotation_gate='ry', entangle_gate='cz', epochs=100, 
        num_samples=1000, n_qubits=6, k_layers=3, batch_size=32, gen_lr=2e-4, 
        disc_lr=1e-4, bounds=[-1.5, 1.5], sampler=Sampler(), device='cpu', 
        circuit=None, use_noise=True, gen_update_ratio=4, adaptive_lr=True, 
        wasserstein_loss=False, spectral_norm=True, gradient_penalty=0.1,
        momentum_beta=0.9, label_smoothing=True, patience=30
    ):
        # Original parameters
        self.num_samples = num_samples
        self.n_qubits = n_qubits
        self.k_layers = k_layers
        self.model = model
        self.samples = samples
        self.batch_size = batch_size
        self.gen_lr = gen_lr
        self.disc_lr = disc_lr
        self.bounds = bounds
        self.epochs = epochs
        self.sampler = sampler
        self.device = device
        self.ansatz_circuit = circuit
        self.rot_gate = rotation_gate
        self.ent_gate = entangle_gate
        self.use_noise = use_noise
        
        # Enhanced parameters
        self.gen_update_ratio = gen_update_ratio
        self.adaptive_lr = adaptive_lr
        self.wasserstein_loss = wasserstein_loss
        self.spectral_norm = spectral_norm
        self.gradient_penalty = gradient_penalty
        self.momentum_beta = momentum_beta
        self.label_smoothing = label_smoothing
        self.patience = patience

        # Internal variables
        self.epsilon = 1e-8
        self.QC_TEMPLATE = None
        self.NOISE_PARAMS = None
        self.ANSATZ_PARAMS = None
        self.theta = None
        self.num_params = None
        self.parameter_momentum = None
        
        # Training tracking
        self.gen_loss_history = []
        self.disc_loss_history = []
        self.best_kl_div = float('inf')
        self.patience_counter = 0
        
        # Data loader
        self.dataloader = DataLoader(TensorDataset(self.samples), batch_size=batch_size, shuffle=True)

    def build_parameterised_circuit(self):
        """Build the parameterized quantum circuit"""
        if self.use_noise:
            noise_params = ParameterVector("ζ", length=self.n_qubits)
        else:
            noise_params = []
        
        ansatz = self.ansatz_circuit if self.ansatz_circuit else self.build_default_ansatz()
        qc = QuantumCircuit(self.n_qubits)
        
        for i in range(self.n_qubits):
            if self.use_noise:
                qc.ry(noise_params[i], i)
        
        qc.compose(ansatz, inplace=True)
        qc.measure_all()
        return qc, list(noise_params), list(ansatz.parameters)

    def build_default_ansatz(self):
        """Build default TwoLocal ansatz"""
        return TwoLocal(self.n_qubits, self.rot_gate, self.ent_gate, reps=self.k_layers, entanglement='circular')

    def quantum_generator(self, noise_batch, theta):
        """Quantum generator using the parameterized circuit"""
        if self.QC_TEMPLATE is None:
            raise RuntimeError("qGAN model must be compiled before inference. Call `compile_model()`.")
        
        batch_size = noise_batch.shape[0]
        flat_theta = theta.detach().cpu().numpy()
        parameter_values = []
        
        if self.use_noise:
            noise_np = noise_batch.detach().cpu().numpy()
            lower, upper = self.bounds
            noise_angles = (noise_np + 1) / 2 * (upper - lower) + lower

        for i in range(batch_size):
            if self.use_noise:
                noise_vec = noise_angles[i][:len(self.NOISE_PARAMS)]
                param_vec = list(noise_vec) + list(flat_theta[:len(self.ANSATZ_PARAMS)])
            else:
                param_vec = list(flat_theta[:len(self.ANSATZ_PARAMS)])
            parameter_values.append(param_vec)

        results = self.sampler.run([self.QC_TEMPLATE] * batch_size, parameter_values=parameter_values, shots=2048).result()
        batch_outputs = []
        dim = 2 ** self.n_qubits
        
        for dist in results.quasi_dists:
            hist = np.zeros(dim)
            for bitstring, prob in dist.items():
                idx = int(bitstring, 2) if isinstance(bitstring, str) else int(bitstring)
                hist[idx] = prob
            batch_outputs.append(hist)

        batch_outputs = np.stack(batch_outputs, axis=0).astype(np.float32)
        return torch.tensor(batch_outputs, dtype=torch.float32, device=self.device)

    def _add_spectral_norm(self):
        """Add spectral normalization to discriminator layers"""
        try:
            from torch.nn.utils import spectral_norm
            for name, module in self.model.named_modules():
                if isinstance(module, nn.Linear):
                    self.model._modules[name.split('.')[-1]] = spectral_norm(module)
        except ImportError:
            print("Warning: Spectral normalization not available, skipping...")

    def _get_adaptive_learning_rate(self, model_type):
        """Compute adaptive learning rate based on loss history"""
        if model_type == 'generator':
            base_lr = self.gen_lr
            loss_history = self.gen_loss_history[-10:]
        else:
            base_lr = self.disc_lr
            loss_history = self.disc_loss_history[-10:]

        if len(loss_history) < 5:
            return base_lr

        recent_avg = np.mean(loss_history[-3:])
        older_avg = np.mean(loss_history[-7:-3]) if len(loss_history) >= 7 else recent_avg

        if recent_avg < older_avg * 0.95:  # Loss decreasing
            return min(base_lr * 1.05, base_lr * 1.5)
        elif recent_avg > older_avg * 1.05:  # Loss increasing
            return max(base_lr * 0.95, base_lr * 0.7)
        else:
            return base_lr

    def _compute_regularization_gradients(self, noise_batch):
        """Compute gradients for regularization terms (KL divergence and entropy)"""
        reg_grad = torch.zeros_like(self.theta)
        shift = np.pi / 4
        
        # Get current distributions
        fake_samples = self.quantum_generator(noise_batch, self.theta)
        fake_dist = fake_samples.mean(dim=0) + self.epsilon
        
        # Get real distribution for comparison
        try:
            real_samples = next(iter(self.dataloader))[0][:len(fake_samples)].to(self.device)
        except:
            # Fallback if dataloader is exhausted
            real_samples = self.samples[:len(fake_samples)].to(self.device)
        
        real_dist = real_samples.mean(dim=0) + self.epsilon
        
        # Normalize distributions
        fake_prob = fake_dist / fake_dist.sum()
        real_prob = real_dist / real_dist.sum()
        
        for i in range(min(self.num_params, 10)):  # Limit for computational efficiency
            # Parameter shifts
            theta_plus = self.theta.clone()
            theta_plus[i] += shift
            theta_minus = self.theta.clone()
            theta_minus[i] -= shift
            
            # Get shifted distributions
            fake_plus = self.quantum_generator(noise_batch, theta_plus).mean(dim=0) + self.epsilon
            fake_minus = self.quantum_generator(noise_batch, theta_minus).mean(dim=0) + self.epsilon
            
            fake_plus_prob = fake_plus / fake_plus.sum()
            fake_minus_prob = fake_minus / fake_minus.sum()
            
            # KL divergence gradients
            kl_plus = F.kl_div(fake_plus_prob.log(), real_prob, reduction='batchmean')
            kl_minus = F.kl_div(fake_minus_prob.log(), real_prob, reduction='batchmean')
            kl_grad = (kl_plus - kl_minus) / (2 * shift)
            
            # Entropy gradients (maximize entropy)
            entropy_plus = -(fake_plus_prob * fake_plus_prob.log()).sum()
            entropy_minus = -(fake_minus_prob * fake_minus_prob.log()).sum()
            entropy_grad = -(entropy_plus - entropy_minus) / (2 * shift)
            
            reg_grad[i] = 0.1 * kl_grad + 0.01 * entropy_grad
        
        return reg_grad

    def enhanced_generator_update(self, noise_batch):
        """Enhanced generator update with momentum and adaptive learning rate"""
        shift = np.pi / 2
        grad = torch.zeros_like(self.theta)
        batch_size = noise_batch.size(0)
        
        target_value = 0.9 if self.label_smoothing else 1.0
        ones = torch.full((batch_size, 1), target_value).to(self.device)

        with torch.no_grad():
            # Efficient gradient computation using parameter rule
            for i in range(self.num_params):
                theta_plus = self.theta.clone()
                theta_plus[i] += shift
                theta_minus = self.theta.clone()
                theta_minus[i] -= shift

                g_plus = self.quantum_generator(noise_batch, theta_plus)
                g_minus = self.quantum_generator(noise_batch, theta_minus)

                D_plus = self.model(g_plus)
                D_minus = self.model(g_minus)

                if self.wasserstein_loss:
                    loss_plus = -D_plus.mean()
                    loss_minus = -D_minus.mean()
                else:
                    loss_plus = F.binary_cross_entropy(D_plus, ones)
                    loss_minus = F.binary_cross_entropy(D_minus, ones)

                grad[i] = (loss_plus - loss_minus) / 2

            # Apply gradient clipping
            grad = torch.clamp(grad, -1.0, 1.0)
            
            # Add regularization gradients (less frequently for efficiency)
            if torch.rand(1).item() < 0.3:  # 30% of the time
                reg_grad = self._compute_regularization_gradients(noise_batch)
                grad += reg_grad

            # Apply momentum
            if self.parameter_momentum is not None:
                self.parameter_momentum = self.momentum_beta * self.parameter_momentum + (1 - self.momentum_beta) * grad
                effective_grad = self.parameter_momentum
            else:
                effective_grad = grad

            # Get adaptive learning rate
            adaptive_lr = self._get_adaptive_learning_rate('generator')
            
            # Update parameters
            self.theta -= adaptive_lr * effective_grad

    def enhanced_discriminator_loss(self, real_data, fake_data):
        """Enhanced discriminator loss with various improvements"""
        batch_size = real_data.size(0)
        
        if self.wasserstein_loss:
            # Wasserstein loss
            real_loss = -self.model(real_data).mean()
            fake_loss = self.model(fake_data).mean()
            
            # Gradient penalty for WGAN-GP
            alpha = torch.rand(batch_size, 1).to(self.device)
            interpolated = alpha * real_data + (1 - alpha) * fake_data
            interpolated.requires_grad_(True)
            
            disc_interpolated = self.model(interpolated)
            gradients = torch.autograd.grad(
                outputs=disc_interpolated, inputs=interpolated,
                grad_outputs=torch.ones_like(disc_interpolated),
                create_graph=True, retain_graph=True
            )[0]
            
            gradient_penalty = ((gradients.norm(2, dim=1) - 1) ** 2).mean()
            total_loss = real_loss + fake_loss + self.gradient_penalty * gradient_penalty
            
        else:
            # Enhanced BCE loss
            if self.label_smoothing:
                real_labels = torch.full((batch_size, 1), 0.9).to(self.device)
                fake_labels = torch.full((batch_size, 1), 0.1).to(self.device)
                
                # Add occasional label noise
                if torch.rand(1).item() < 0.05:
                    real_labels += torch.randn_like(real_labels) * 0.05
                    fake_labels += torch.randn_like(fake_labels) * 0.05
                    real_labels = torch.clamp(real_labels, 0.0, 1.0)
                    fake_labels = torch.clamp(fake_labels, 0.0, 1.0)
            else:
                real_labels = torch.ones((batch_size, 1)).to(self.device)
                fake_labels = torch.zeros((batch_size, 1)).to(self.device)
            
            real_loss = F.binary_cross_entropy(self.model(real_data), real_labels)
            fake_loss = F.binary_cross_entropy(self.model(fake_data), fake_labels)
            total_loss = real_loss + fake_loss
        
        return total_loss, real_loss.item(), fake_loss.item()

    def compile_model(self):
        """Compile the model - must be called before training"""
        self.QC_TEMPLATE, self.NOISE_PARAMS, self.ANSATZ_PARAMS = self.build_parameterised_circuit()
        self.theta = nn.Parameter(torch.rand(len(self.ANSATZ_PARAMS), dtype=torch.float32, requires_grad=True))
        self.theta = self.theta.to(self.device)
        self.num_params = len(self.ANSATZ_PARAMS)
        
        # Initialize momentum
        self.parameter_momentum = torch.zeros_like(self.theta)
        
        # Add spectral normalization if requested
        if self.spectral_norm:
            self._add_spectral_norm()

    def train(self):
        """Enhanced training loop with comprehensive monitoring and visualization"""
        if self.QC_TEMPLATE is None:
            raise RuntimeError("qGAN model must be compiled before training. Call `compile_model()`.")
            
        # Training tracking lists
        gen_losses, disc_losses, kl_divs, entropies, mode_coverages = [], [], [], [], []
        real_losses, fake_losses = [], []
        
        self.model.to(self.device)
        bins = 2 ** self.n_qubits
        
        # Optimizer
        dis_opt = optim.Adam(self.model.parameters(), lr=self.disc_lr, betas=(0.5, 0.999))
        
        # Learning rate scheduler
        if self.adaptive_lr:
            disc_scheduler = optim.lr_scheduler.ReduceLROnPlateau(
                dis_opt, mode='min', factor=0.8, patience=self.patience//2
            )

        print(f"Starting training for {self.epochs} epochs...")
        print(f"Configuration: {self.n_qubits} qubits, {self.k_layers} layers, batch size {self.batch_size}")
        print(f"Generator updates per discriminator update: {self.gen_update_ratio}")
        print(f"Using {'Wasserstein' if self.wasserstein_loss else 'BCE'} loss")
        
        for epoch in range(self.epochs):
            epoch_gen_losses = []
            epoch_disc_losses = []
            epoch_real_losses = []
            epoch_fake_losses = []
            
            for batch_idx, real_data_batch in enumerate(tqdm(self.dataloader, desc=f"Epoch {epoch+1}/{self.epochs}", leave=False)):
                real_data = real_data_batch[0].to(self.device)
                batch_size = real_data.size(0)
                
                # Generate fake data
                noise = torch.randn(batch_size, self.n_qubits).to(self.device)
                fake_data = self.quantum_generator(noise, self.theta).detach()
                
                # Train Discriminator
                dis_opt.zero_grad()
                disc_loss, real_loss_val, fake_loss_val = self.enhanced_discriminator_loss(real_data, fake_data)
                disc_loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 0.5)
                dis_opt.step()
                
                # Train Generator multiple times
                for _ in range(self.gen_update_ratio):
                    noise = torch.randn(batch_size, self.n_qubits).to(self.device)
                    self.enhanced_generator_update(noise)
                
                # Calculate generator loss for monitoring
                with torch.no_grad():
                    fake_data_for_loss = self.quantum_generator(noise, self.theta)
                    fake_preds = self.model(fake_data_for_loss)
                    if self.wasserstein_loss:
                        gen_loss = -fake_preds.mean()
                    else:
                        target_val = 0.9 if self.label_smoothing else 1.0
                        gen_loss = F.binary_cross_entropy(fake_preds, torch.full_like(fake_preds, target_val))
                
                epoch_gen_losses.append(gen_loss.item())
                epoch_disc_losses.append(disc_loss.item())
                epoch_real_losses.append(real_loss_val)
                epoch_fake_losses.append(fake_loss_val)
            
            # Calculate epoch averages
            avg_gen_loss = np.mean(epoch_gen_losses)
            avg_disc_loss = np.mean(epoch_disc_losses)
            avg_real_loss = np.mean(epoch_real_losses)
            avg_fake_loss = np.mean(epoch_fake_losses)
            
            # Update loss histories
            self.gen_loss_history.append(avg_gen_loss)
            self.disc_loss_history.append(avg_disc_loss)
            gen_losses.append(avg_gen_loss)
            disc_losses.append(avg_disc_loss)
            real_losses.append(avg_real_loss)
            fake_losses.append(avg_fake_loss)
            
            # Update learning rate scheduler
            if self.adaptive_lr:
                disc_scheduler.step(avg_disc_loss)
            
            # === Evaluation and Metrics ===
            with torch.no_grad():
                # Generate samples for evaluation
                noise = torch.randn(1000, self.n_qubits).to(self.device)
                fake_samples = self.quantum_generator(noise, self.theta)
                fake_flat = fake_samples.mean(dim=0)
                
                # Get real distribution
                real_flat = self.samples[:1000].mean(dim=0).to(self.device)
                
                # Normalize probabilities
                fake_prob = fake_flat / fake_flat.sum() + self.epsilon
                real_prob = real_flat / real_flat.sum() + self.epsilon
                
                # Calculate metrics
                kl = F.kl_div(fake_prob.log(), real_prob, reduction='batchmean')
                entropy = -torch.sum(fake_prob * fake_prob.log()).item()
                mode_coverage = (fake_prob > 1e-3).sum().item()
                
                kl_divs.append(kl.item())
                entropies.append(entropy)
                mode_coverages.append(mode_coverage)
                
                # Early stopping check
                if kl.item() < self.best_kl_div:
                    self.best_kl_div = kl.item()
                    self.patience_counter = 0
                else:
                    self.patience_counter += 1
            
            # === Enhanced Visualization ===
            if epoch % max(1, self.epochs // self.epochs) == 0 or epoch == self.epochs - 1: # Modify this line to change plotting count
                clear_output(wait=True)
                fig, axs = plt.subplots(2, 3, figsize=(18, 12))
                
                # Loss plots
                axs[0, 0].plot(gen_losses, label="Generator", color='blue', alpha=0.8)
                axs[0, 0].plot(disc_losses, label="Discriminator", color='red', alpha=0.8)
                axs[0, 0].set_title("Training Losses", fontsize=14)
                axs[0, 0].legend()
                axs[0, 0].grid(True, alpha=0.3)
                axs[0, 0].set_xlabel("Epoch")
                axs[0, 0].set_ylabel("Loss")
                
                # Discriminator component losses
                axs[0, 1].plot(real_losses, label="Real Loss", color='green', alpha=0.8)
                axs[0, 1].plot(fake_losses, label="Fake Loss", color='orange', alpha=0.8)
                axs[0, 1].set_title("Discriminator Component Losses", fontsize=14)
                axs[0, 1].legend()
                axs[0, 1].grid(True, alpha=0.3)
                axs[0, 1].set_xlabel("Epoch")
                axs[0, 1].set_ylabel("Loss")
                
                # KL Divergence
                axs[0, 2].plot(kl_divs, label="KL(G || R)", color='purple', linewidth=2)
                axs[0, 2].set_title("KL Divergence", fontsize=14)
                axs[0, 2].legend()
                axs[0, 2].grid(True, alpha=0.3)
                axs[0, 2].set_xlabel("Epoch")
                axs[0, 2].set_ylabel("KL Divergence")
                
                # Distribution comparison
                real_indices = np.random.choice(np.arange(bins), p=real_prob.cpu().numpy(), size=1000)
                fake_indices = np.random.choice(np.arange(bins), p=fake_prob.cpu().numpy(), size=1000)
                axs[1, 0].hist(real_indices, bins=min(bins, 50), alpha=0.6, label="Real", density=True, color='blue')
                axs[1, 0].hist(fake_indices, bins=min(bins, 50), alpha=0.6, label="Generated", density=True, color='red')
                axs[1, 0].set_title("Distribution Comparison", fontsize=14)
                axs[1, 0].legend()
                axs[1, 0].grid(True, alpha=0.3)
                axs[1, 0].set_xlabel("State")
                axs[1, 0].set_ylabel("Probability Density")
                
                # Entropy evolution
                axs[1, 1].plot(entropies, label="Entropy", color='green', linewidth=2)
                axs[1, 1].set_title("Generated Distribution Entropy", fontsize=14)
                axs[1, 1].legend()
                axs[1, 1].grid(True, alpha=0.3)
                axs[1, 1].set_xlabel("Epoch")
                axs[1, 1].set_ylabel("Entropy")
                
                # Mode coverage
                axs[1, 2].plot(mode_coverages, label=f"Coverage (max: {bins})", color='orange', linewidth=2)
                axs[1, 2].axhline(y=bins, color='red', linestyle='--', alpha=0.7, label='Maximum')
                axs[1, 2].set_title("Mode Coverage", fontsize=14)
                axs[1, 2].legend()
                axs[1, 2].grid(True, alpha=0.3)
                axs[1, 2].set_xlabel("Epoch")
                axs[1, 2].set_ylabel("Number of Modes")
                
                plt.tight_layout()
                plt.show()
            
            # Progress report
            print(f"Epoch [{epoch+1}/{self.epochs}]  "
                  f"D_loss: {avg_disc_loss:.4f}  G_loss: {avg_gen_loss:.4f}  "
                  f"KL: {kl.item():.4f}  Entropy: {entropy:.4f}  "
                  f"Coverage: {mode_coverage}/{bins}  "
                  f"Patience: {self.patience_counter}/{self.patience}")
            
            # Early stopping
            if self.patience_counter >= self.patience:
                print(f"Early stopping triggered at epoch {epoch+1}")
                break
        
        print("Training completed!")
        return {
            'gen_losses': gen_losses,
            'disc_losses': disc_losses,
            'kl_divergences': kl_divs,
            'entropies': entropies,
            'mode_coverages': mode_coverages,
            'final_kl': kl_divs[-1] if kl_divs else float('inf'),
            'best_kl': self.best_kl_div
        }

    @property
    def is_compiled(self):
        """Check if the model has been compiled"""
        return self.QC_TEMPLATE is not None
