import numpy as np

# Write the script to a file
write_file({
    "path": "script.py",
    "content": """import numpy as np

# Set seed for reproducibility
np.random.seed(42)

# Generate data
X = np.random.randn(200, 2)
y = np.where(X[:, 0] + X[:, 1] > 0, 1, 0).reshape(-1, 1)

# Initialize parameters
W = np.random.randn(2, 1) * 0.01
b = np.zeros((1, 1))
learning_rate = 1.0
m = X.shape[0]

# Sigmoid function
def sigmoid(z):
    return 1 / (1 + np.exp(-z))

# Forward pass
def forward(X, W, b):
    Z = X @ W + b
    A = sigmoid(Z)
    return A

# Binary cross-entropy loss
def loss(A, y):
    A = np.clip(A, 1e-7, 1 - 1e-7)
    return -np.mean(y * np.log(A) + (1 - y) * np.log(1 - A))

# Backward pass
def backward(X, A, y):
    dZ = A - y
    dW = (1 / m) * X.T @ dZ
    db = (1 / m) * np.sum(dZ)
    return dW, db

# Training loop
for epoch in range(1000):
    A = forward(X, W, b)
    l = loss(A, y)
    dW, db = backward(X, A, y)
    W -= learning_rate * dW
    b -= learning_rate * db
    
    if epoch % 200 == 0:
        acc = (np.round(A) == y).mean() * 100
        print(f"Epoch {epoch}: loss={l:.4f}, acc={acc:.1f}%")

# Final accuracy
acc = (np.round(A) == y).mean() * 100
print(f"Final accuracy: {acc:.1f}%")

# Save model data
np.savez("model_data.npz", W=W, b=b, X=X, y=y)
"""
})

# Explanation:
- The script generates 200 data points for binary classification.
- A single-layer neural network with a sigmoid activation function is built.
- The network is trained for 1000 epochs using gradient descent.
- The loss function used is binary cross-entropy.
- The script prints the loss and accuracy every 200 epochs.
- The final accuracy is printed at the end.
- The model parameters (W, b, X, y) are saved to "model_data.npz".
