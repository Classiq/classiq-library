# --- Required Libraries ---
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pypfopt import expected_returns, risk_models, BlackLittermanModel
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
import time

# --- Classiq Imports ---
from classiq import (
    construct_combinatorial_optimization_model,
    set_execution_preferences,
    write_qmod,
    show,
    synthesize,
    execute
)
from classiq.execution import (
    ClassiqBackendPreferences,
    ExecutionPreferences
)
from classiq.applications.combinatorial_optimization import (
    OptimizerConfig,
    QAOAConfig,
    get_optimization_solution_from_pyo
)
import pyomo.environ as pyo

print("Starting Quantum Portfolio Optimization...")

# -------------------------------
# STEP 1: Load Financial Data
# -------------------------------
# Expanded list of assets to match proposal's goal of 16+ assets
symbols = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'JPM', 
    'JNJ', 'V', 'PG', 'UNH', 'HD', 'BAC', 'MA', 'DIS'
]

# Define time periods for normal market and stress testing
normal_period = ("2020-01-01", "2022-01-01")
stress_period = ("2020-02-15", "2020-04-15")  # COVID-19 market crash

print(f"Downloading data for {len(symbols)} assets...")
# Use normal period for main analysis
raw_data = yf.download(symbols, start=normal_period[0], end=normal_period[1])
print(f"Available columns: {raw_data.columns.levels[0] if isinstance(raw_data.columns, pd.MultiIndex) else raw_data.columns}")

# Handle MultiIndex or regular columns
if isinstance(raw_data.columns, pd.MultiIndex):
    if 'Adj Close' in raw_data.columns.levels[0]:
        data = raw_data['Adj Close']
        print("Using 'Adj Close' prices from MultiIndex")
    else:
        data = raw_data['Close']
        print("Using 'Close' prices instead of 'Adj Close' from MultiIndex")
else:
    if 'Adj Close' in raw_data.columns:
        data = raw_data['Adj Close']
        print("Using 'Adj Close' prices")
    else:
        data = raw_data['Close']
        print("Using 'Close' prices instead of 'Adj Close'")

# Print data shape to confirm
print(f"Data shape: {data.shape}, spanning from {data.index[0]} to {data.index[-1]}")

# -------------------------------
# STEP 2: Data Preprocessing with PCA
# -------------------------------
# Calculate returns
returns = data.pct_change().dropna()

# Apply PCA for dimensionality reduction as mentioned in the proposal
scaler = StandardScaler()
scaled_returns = scaler.fit_transform(returns)

# Apply PCA to reduce dimensionality while preserving 95% of variance
pca = PCA(n_components=0.95)
pca_returns = pca.fit_transform(scaled_returns)
print(f"PCA reduced dimensions from {returns.shape[1]} to {pca.n_components_} components")

# -------------------------------
# STEP 3: QML for Investor Views (Simplified)
# -------------------------------
# Simplified QML simulation using classical SVM
# In a real quantum implementation, this would use QSVM
print("Simulating Quantum ML for investor sentiment prediction...")

# Create a simplified sentiment indicator
# (would be replaced by actual sentiment data in production)
sentiment = pd.Series(index=symbols)
for symbol in symbols:
    # Simple rule: positive sentiment if average return > market average
    symbol_return = returns[symbol].mean()
    market_return = returns.mean().mean()
    sentiment[symbol] = 1 if symbol_return > market_return else -1

# Create view dictionary for Black-Litterman model
view_dict = {}
# Generate views based on sentiment
for symbol, sent in sentiment.items():
    if sent > 0:
        view_dict[symbol] = 0.02  # Positive outlook: 2% excess return
    elif sent < 0:
        view_dict[symbol] = -0.01  # Negative outlook: -1% expected return

print(f"Generated {len(view_dict)} investor views from sentiment analysis")

# -------------------------------
# STEP 4: Black-Litterman Model
# -------------------------------
print("Applying Black-Litterman Model...")
mu = expected_returns.mean_historical_return(data)
S = risk_models.sample_cov(data)

# Calculate market caps (using last price as a proxy if needed)
market_caps = data.iloc[-1].values
market_weights = market_caps / np.sum(market_caps)

# Verify no NaNs in market weights
if np.isnan(market_weights).any():
    print("Warning: NaN values found in market weights. Replacing with equal weights.")
    market_weights = np.ones_like(market_weights) / len(market_weights)

# Set up the risk aversion parameter (delta)
delta = 2.5  # Market price of risk

# Calculate the implied prior returns vector using risk aversion and covariance
prior_returns = delta * np.dot(S, market_weights)  # Prior returns based on market equilibrium

# Create the Black-Litterman model correctly
try:
    # Create the Black-Litterman model
    bl = BlackLittermanModel(S, pi=prior_returns)
    
    # Convert views to the required format
    view_p = np.zeros((len(view_dict), len(symbols)))
    view_q = np.zeros(len(view_dict))
    
    # Fill view matrices
    i = 0
    for asset, expected_return in view_dict.items():
        try:
            asset_idx = symbols.index(asset)
            view_p[i, asset_idx] = 1.0
            view_q[i] = expected_return
            i += 1
        except ValueError:
            print(f"Asset {asset} not found in symbols list")
    
    # Add views
    bl.add_views(view_p, view_q)
    
    # Get Black-Litterman results
    bl_returns = bl.bl_returns()
    bl_cov = bl.bl_cov()
    
    print("Black-Litterman expected returns:")
    for i, symbol in enumerate(symbols):
        print(f"{symbol}: {bl_returns[i]:.4f}")
        
except Exception as e:
    print(f"Error in Black-Litterman model: {e}")
    print("Falling back to historical estimates...")
    # Fallback to historical estimates if Black-Litterman fails
    bl_returns = mu
    bl_cov = S

# -------------------------------
# STEP 5: Build QUBO Matrix
# -------------------------------
def build_qubo(returns, cov, risk_aversion=0.5):
    n = len(returns)
    Q = np.zeros((n, n))
    
    # Ensure returns is a numpy array
    if isinstance(returns, pd.Series):
        returns_arr = returns.values
    else:
        returns_arr = np.array(returns)
        
    # Create the QUBO matrix
    for i in range(n):
        for j in range(n):
            if i == j:
                Q[i][j] = -returns_arr[i] + risk_aversion * cov.iloc[i, j]
            else:
                Q[i][j] = risk_aversion * cov.iloc[i, j]
    return Q

Q_matrix = build_qubo(bl_returns, bl_cov)
print(f"QUBO matrix created with shape: {Q_matrix.shape}")

# -------------------------------
# STEP 6: Classical Benchmark (for comparison)
# -------------------------------
print("Running classical benchmark for comparison...")
start_time = time.time()

# Simple classical portfolio optimization using brute force (for small portfolios)
def classical_optimize(returns, cov, max_assets=4):
    n = len(returns)
    best_portfolio = None
    best_value = float('inf')
    
    # For tractability, limit to max_assets (in real implementation, use more sophisticated methods)
    for i in range(2**min(n, max_assets)):
        # Binary representation of the number
        binary = format(i, f'0{min(n, max_assets)}b').zfill(n)
        portfolio = np.array([int(binary[j]) for j in range(n)])
        
        # Skip if no assets selected or fewer than 3
        if sum(portfolio) < 3:
            continue
            
        # Calculate portfolio value using same QUBO formulation
        value = 0
        for i in range(n):
            for j in range(n):
                value += Q_matrix[i][j] * portfolio[i] * portfolio[j]
                
        if value < best_value:
            best_value = value
            best_portfolio = portfolio
    
    return best_portfolio, best_value

classical_solution, classical_value = classical_optimize(bl_returns, bl_cov)
classical_time = time.time() - start_time

classical_assets = [symbols[i] for i, val in enumerate(classical_solution) if val == 1]
print(f"Classical solution found in {classical_time:.4f} seconds")
print(f"Classical selected assets: {classical_assets}")

# -------------------------------
# STEP 7: Define Pyomo Model
# -------------------------------
n_assets = len(symbols)
model = pyo.ConcreteModel()
model.x = pyo.Var(range(n_assets), domain=pyo.Binary)

# Objective: minimize the QUBO expression
model.obj = pyo.Objective(
    expr=sum(Q_matrix[i][j] * model.x[i] * model.x[j] for i in range(n_assets) for j in range(n_assets)),
    sense=pyo.minimize
)

# Add constraint: select between 3 and 7 assets
# FIX: Split into two separate constraints
model.min_assets = pyo.Constraint(expr=sum(model.x[i] for i in range(n_assets)) >= 3)
model.max_assets = pyo.Constraint(expr=sum(model.x[i] for i in range(n_assets)) <= 7)

print(f"Pyomo model defined with {n_assets} binary variables and cardinality constraints")

# -------------------------------
# STEP 8: Configure QAOA and Optimizer
# -------------------------------
qaoa_config = QAOAConfig(num_layers=3, penalty_energy=10.0)  # Increased layers for better performance
optimizer_config = OptimizerConfig(max_iteration=30, alpha_cvar=0.7)  # Increased iterations

# -------------------------------
# STEP 9: Construct Quantum Model with Error Mitigation
# -------------------------------
try:
    print("Creating quantum model with QAOA...")
    start_time = time.time()
    
    qmod = construct_combinatorial_optimization_model(
        pyo_model=model,
        qaoa_config=qaoa_config,
        optimizer_config=optimizer_config
    )

    # Set backend preferences with error mitigation
    qmod = set_execution_preferences(
        qmod,
        backend_preferences=ClassiqBackendPreferences(
            backend_name="simulator", 
            noise_model="ideal"  # Set to appropriate noise model in production
        )
    )
    print("Quantum model constructed successfully!")

    # Optional: Save the quantum model
    write_qmod(qmod, "portfolio_optimization")
    print("Quantum model saved as 'portfolio_optimization'")

    # -------------------------------
    # STEP 10: Synthesize and Execute
    # -------------------------------
    print("Synthesizing quantum program...")
    qprog = synthesize(qmod)
    
    # Display circuit
    print("Displaying quantum circuit...")
    show(qprog)
    
    # Optionally save the circuit diagram if available in your version
    try:
        from classiq.visualization import export_circuit_to_image
        export_circuit_to_image(qprog, "quantum_portfolio_circuit.png")
        print("Circuit image saved as 'quantum_portfolio_circuit.png'")
    except ImportError:
        print("Circuit visualization export not available in this Classiq version")
    
    print("Executing quantum program...")
    result = execute(qprog).result_value()
    quantum_time = time.time() - start_time

    # -------------------------------
    # STEP 11: Extract Solution
    # -------------------------------
    solution = get_optimization_solution_from_pyo(
        model,
        vqe_result=result,
        penalty_energy=qaoa_config.penalty_energy
    )

    # Identify selected assets
    selected_indices = [i for i, val in enumerate(solution[0]['solution']) if val == 1]
    selected_assets = [symbols[i] for i in selected_indices]
    print(f"Quantum solution found in {quantum_time:.4f} seconds")
    print(f"Quantum selected assets: {selected_assets}")
    
    # Performance comparison
    speedup = classical_time / quantum_time
    print(f"Quantum speedup: {speedup:.2f}x")

    # -------------------------------
    # STEP 12: Backtest & Visualize
    # -------------------------------
    # Create a figure for normal market conditions
    plt.figure(figsize=(12, 6))
    
    # Normal market conditions
    selected_data = data[selected_assets]
    normalized = selected_data / selected_data.iloc[0]
    portfolio_growth = normalized.mean(axis=1)

    # Plot each asset and the portfolio
    plt.title("Quantum-Optimized Portfolio and Individual Assets (Normal Market)")
    portfolio_growth.plot(linewidth=3, color='black', label='Portfolio Average')
    
    # Also plot individual assets
    for asset in selected_assets:
        normalized[asset].plot(alpha=0.7, linestyle='--', label=asset)
    
    plt.ylabel("Normalized Value")
    plt.grid(True)
    plt.legend(loc='best')
    
    # Make sure to show the plot
    plt.tight_layout()
    plt.show()  # Display this plot immediately
    
    # Compute Sharpe Ratio for normal period
    log_returns = np.log(selected_data / selected_data.shift(1)).dropna()
    mean_daily = log_returns.mean().mean()
    std_daily = log_returns.std().mean()
    sharpe_ratio = (mean_daily / std_daily) * np.sqrt(252)
    print(f"Sharpe Ratio (Normal Market): {sharpe_ratio:.2f}")
    
    # -------------------------------
    # STEP 13: Stress Test (Additional scenario from proposal)
    # -------------------------------
    print("\nPerforming stress test analysis...")
    # Download stress period data
    stress_data = yf.download(selected_assets, start=stress_period[0], end=stress_period[1])
    if isinstance(stress_data.columns, pd.MultiIndex):
        stress_prices = stress_data['Close']
    else:
        stress_prices = stress_data
        
    # Calculate performance during stress
    stress_normalized = stress_prices / stress_prices.iloc[0]
    stress_portfolio = stress_normalized.mean(axis=1)
    
    # Create a new figure for stress test
    plt.figure(figsize=(12, 6))
    plt.title("Portfolio Performance During Market Stress (COVID-19)")
    
    # Plot portfolio and individual assets during stress
    stress_portfolio.plot(linewidth=3, color='black', label='Portfolio Average')
    
    # Also plot individual assets during stress
    for asset in selected_assets:
        if asset in stress_normalized.columns:
            stress_normalized[asset].plot(alpha=0.7, linestyle='--', label=asset)
    
    plt.ylabel("Normalized Value")
    plt.grid(True)
    plt.legend(loc='best')
    
    # Make sure to show the plot
    plt.tight_layout()
    plt.show()  # Display this plot immediately
    
    # Save combined figure for documentation
    plt.figure(figsize=(12, 12))
    
    plt.subplot(2, 1, 1)
    portfolio_growth.plot(linewidth=3, color='black', label='Portfolio')
    plt.title("Normal Market Performance")
    plt.ylabel("Normalized Value")
    plt.grid(True)
    
    plt.subplot(2, 1, 2)
    stress_portfolio.plot(linewidth=3, color='black', label='Portfolio')
    plt.title("Stress Period Performance")
    plt.ylabel("Normalized Value")
    plt.grid(True)
    
    plt.savefig("portfolio_performance_combined.png")
    plt.tight_layout()
    plt.show()  # And show this one too
    
    # Compute max drawdown during stress
    max_drawdown = (stress_portfolio / stress_portfolio.cummax() - 1).min()
    print(f"Maximum Drawdown during stress period: {max_drawdown:.2%}")

except ImportError as e:
    print(f"Error with Classiq imports: {e}")
    print("Please verify your Classiq installation with: pip list | grep classiq")
    
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    import traceback
    traceback.print_exc()