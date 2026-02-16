# QML

This folder presents a collection of Quantum Machine Learning (QML) algorithms
implemented within hybrid quantum–classical frameworks. The examples demonstrate how
parameterized quantum circuits can be integrated with classical optimization and
deep-learning tools to perform classification, generative modeling, and data compression tasks.
Each implementation highlights both the algorithmic principles and the practical workflow,
including state preparation, circuit design, training procedures, and performance evaluation.

- **Hybrid Quantum Neural Networks (QNN)** A hybrid quantum-classical algorithm, incorporating quantum layers into the structure of
  a classical neural network. A state preparation maps classical states in the quantum Hilbert state, following quantum layers are
  implemented by parameterized quantum circuits, providing different expressibility relative to the classical networks.
  Considering a specific example function we construct, train, and verify the hybrid classical-quantum neural network, building
  upon the deep-learning PyTorch module.
- **Quantum Generative Adversarial Networks (GANs)** - A quantum analogue of a classical learning algorithm that generates new
  data which mimics the training set data. The original model is trained by an adversarial optimization in a two-player minmax game,
  utilizing a gradient-based learning. In the quantum algorithm, the classical neural networks are replaced by quantum neural networks.
- **Quantum Support Vector Machine (QSVM)** - Quantum version of the classical machine learning algorithm, classifying
  data points between into two distinct categories. Employing the dual problem formulation, the classification is dictated by a
  defined feature map and the
  kernel matrix. In the quantum algorithm, the feature map is implemented by a quantum circuit and the elements of the
  kernel matrix are evaluated by quantum measurements. The performance of various quantum feature maps are analyzed,
  for both a simplex and complex data sets.
- **Quantum autoencoder** - A quantum program is trained to reduce the memory required to encode data
  with a given structure. The example demonstrates how to use the encoder for anomaly detection.
  Two training approaches for the quantum autoencoder are presented, leveraging Classiq’s integration with PyTorch.
