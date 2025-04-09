# Implementation of a Hybrid Quantum-Classical System for Drug Discovery

## Description
This project focuses on developing a hybrid quantum-classical system that enhances drug-target interaction (DTI) prediction by leveraging quantum feature selection techniques (QAOA/VQE) alongside classical machine learning models (Neural Networks, SVM, Random Forest). The integration of quantum computing aims to improve computational efficiency and accuracy in feature selection for drug discovery.

---

## Objective
Develop a hybrid quantum-classical system for optimizing drug-target interaction prediction by:
- Utilizing Quantum Approximate Optimization Algorithm (QAOA) and Variational Quantum Eigensolver (VQE) for feature selection.
- Training classical machine learning models on quantum-selected features.
- Benchmarking quantum-enhanced feature selection against traditional techniques.

---

## Background
Predicting DTI plays a critical role in drug discovery, identifying potential drug candidates efficiently. Traditional computational methods rely on feature selection techniques that can be computationally expensive. Quantum computing offers an alternative by optimizing molecular feature selection, potentially leading to:
- Improved accuracy
- Enhanced computational efficiency
- Better representation of molecular descriptors

---

## Technical Approach
### 1. Data Preparation
- **Dataset Acquisition:** Utilize publicly available datasets such as PDBbind or DrugBank containing molecular descriptors and binding affinities.
- **Data Preprocessing:** Handle missing values, normalize numerical features, and encode categorical variables.
- **Feature Extraction:** Represent molecular structures numerically using descriptors such as:
  - Extended Connectivity Fingerprints (ECFP)
  - Mordred descriptors

### 2. Quantum Feature Selection (QAOA/VQE)
- **Problem Formulation:** Define feature selection as an optimization problem using a cost Hamiltonian:
  \[ H = w z z + b z \]
- **Ansatz Selection:** Utilize a parameterized quantum circuit optimized for QAOA or VQE.
- **Quantum Circuit Construction:** Implement circuits on quantum platforms, optimizing:
  - CX gate count
  - Circuit depth

### 3. Hybrid Model Integration
- **Classical-Quantum Hybrid Model:**
  - Use QAOA/VQE-selected features to train classical ML models (Neural Networks, Random Forest, SVM).
  - Compare quantum-selected features with traditional methods (PCA, LASSO, RFE).
- **Training and Optimization:**
  - Classical models trained using gradient descent.
  - Quantum models optimized via QAOA/VQE optimizers.

### 4. Model Evaluation and Validation
- **Performance Metrics:**
  - Accuracy
  - Precision
  - Recall
  - F1-score
- **Benchmarking:** Compare quantum-enhanced feature selection with classical methods based on:
  - Prediction accuracy
  - Feature selection efficiency
  - Computational complexity

---

## References
1. **J. K. Lim, D. G. Dickson, J. A. Black et al.**, "Hybrid Quantum-Classical System for Drug Discovery," National Library of Medicine, vol. 13, no. 8, pp. 1-10, Aug. 2022. [PMC9333455](https://pmc.ncbi.nlm.nih.gov/articles/PMC9333455/)
2. **Perdomo-Ortiz, N. Dickson, M. Drew-Brook, G. Rose, and A. Aspuru-Guzik**, "Finding Low-Energy Conformations of Lattice Protein Models by Quantum Annealing," Phys. Rev. Lett., vol. 111, no. 13, pp. 130505, Sep. 2013.
3. **K. S. Kumar, S. S. S. R. Depuru, and S. Arumugam**, "Drug Target Interaction Prediction Using Variational Quantum Classifier," 2022 IEEE International Conference on Quantum Computing and Engineering (QCE), Broomfield, CO, USA, 2022, pp. 1-8.

---

## Summary
This project explores the integration of quantum computing in drug discovery by combining quantum feature selection with classical machine learning models. By leveraging QAOA and VQE algorithms, the study aims to optimize molecular descriptor selection for improved drug-target interaction predictions. The project benchmarks quantum feature selection against classical techniques like PCA, RFE, and mutual information-based selection to evaluate efficiency, accuracy, and computational complexity.

Key focus areas include:
- **Feature selection efficiency**
- **Prediction accuracy**
- **Quantum circuit depth**
- **CX-gate count optimization**

The findings of this research will contribute to understanding quantum computing’s role in drug discovery and its potential for enhancing predictive modeling in drug repurposing efforts.

