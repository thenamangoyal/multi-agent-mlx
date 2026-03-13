import numpy as np

# Set seed for reproducibility
np.random.seed(42)

# Generate data
X = np.random.randn(200, 2)
y = np.where((X[:, 0] + X[:, 1]) > 0, 1, 0).reshape(-1, 1)

# Initialize parameters
W = np.random.randn(2, 1) * 0.01
b = np.zeros((1, 1))

# Sigmoid function
def sigmoid(z):
    return 1 / (1 + np.exp(-z))

# Binary cross-entropy loss
def binary_cross_entropy(y_true, y_pred):
    epsilon = 1e-7
    y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
    return -np.mean(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))

# Training loop
learning_rate = 1.0
num_epochs = 1000

for epoch in range(num_epochs):
    # Forward pass
    Z = X @ W + b
    A = sigmoid(Z)
    
    # Compute loss
    loss = binary_cross_entropy(y, A)
    
    # Backward pass
    dZ = A - y
    dW = (1 / len(y)) * X.T @ dZ
    db = (1 / len(y)) * np.sum(dZ)
    
    # Update parameters
    W -= learning_rate * dW
    b -= learning_rate * db
    
    # Print every 200 epochs
    if (epoch + 1) % 200 == 0:
        print(f"Epoch {epoch + 1}: loss={loss:.4f}, acc={(np.mean((A > 0.5) == y) * 100):.1f}%")

# Final accuracy
final_accuracy = (np.mean((A > 0.5) == y) * 100)
print(f"Final accuracy: {final_accuracy:.1f}%")

# Save model data
np.savez('model_data.npz', W=W, b=b, X=X, y=y)
