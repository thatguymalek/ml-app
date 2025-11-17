import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import pytest
import numpy as np
from src.data_loader import load_iris_data
from src.model import IrisClassifier

class TestIrisClassifier:
    def setup_method(self):
        """Setup method that runs before each test"""
        self.X_train, self.X_test, self.y_train, self.y_test = load_iris_data(test_size=0.3, random_state=42)
        self.classifier = IrisClassifier()

    def test_model_initialization(self):
        """Test that model initializes correctly"""
        assert not self.classifier.is_trained
        assert self.classifier.model is not None

    def test_model_training(self):
        """Test model training functionality"""
        self.classifier.train(self.X_train, self.y_train)
        assert self.classifier.is_trained

    def test_model_prediction(self):
        """Test model prediction functionality"""
        self.classifier.train(self.X_train, self.y_train)
        predictions = self.classifier.predict(self.X_test[:5])
        assert len(predictions) == 5
        assert all(isinstance(pred, (np.int32, np.int64, int)) for pred in predictions)

    def test_model_evaluation(self):
        """Test model evaluation functionality"""
        self.classifier.train(self.X_train, self.y_train)
        accuracy, report = self.classifier.evaluate(self.X_test, self.y_test)

        assert 0 <= accuracy <= 1
        assert isinstance(report, str)
        assert "precision" in report.lower()

    def test_model_save_load(self, tmp_path):
        """Test model saving and loading"""
        self.classifier.train(self.X_train, self.y_train)

        # Save model
        save_path = tmp_path / "test_model.pkl"
        self.classifier.save_model(str(save_path))
        assert save_path.exists()

        # Load model
        new_classifier = IrisClassifier()
        new_classifier.load_model(str(save_path))
        assert new_classifier.is_trained

        # Verify predictions match
        original_pred = self.classifier.predict(self.X_test[:5])
        loaded_pred = new_classifier.predict(self.X_test[:5])
        assert np.array_equal(original_pred, loaded_pred)

    # --- NEW TEST 1 ---
    def test_predict_before_training(self):
        """Test that predicting before training raises an error"""
        assert not self.classifier.is_trained
        # A good implementation should raise an error (e.g., ValueError,
        # AttributeError, or sklearn's NotFittedError) if predict is called before train.
        with pytest.raises((ValueError, AttributeError, Exception)):
            self.classifier.predict(self.X_test)

    # --- NEW TEST 2 ---
    def test_predict_invalid_shape(self):
        """Test prediction with data of incorrect feature shape"""
        self.classifier.train(self.X_train, self.y_train)
        assert self.classifier.is_trained
        
        # Create data with 5 features instead of the expected 4
        invalid_data = np.array([[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]])
        
        # The underlying scikit-learn model should raise a ValueError
        with pytest.raises(ValueError):
            self.classifier.predict(invalid_data)

    # --- NEW TEST 3 ---
    def test_training_mismatched_shapes(self):
        """Test training with mismatched X and y shapes"""
        # X has 105 samples, y has 10 samples
        with pytest.raises(ValueError):
            self.classifier.train(self.X_train, self.y_test[:10])


def test_data_loading():
    """Test data loading functionality and data types"""
    X_train, X_test, y_train, y_test = load_iris_data()

    assert X_train.shape[1] == 4  # 4 features
    assert X_test.shape[1] == 4   # 4 features
    assert len(np.unique(y_train)) <= 3 # Train split might not have all 3 classes
    assert len(np.unique(y_test)) <= 3  # Test split might not have all 3 classes
    assert len(np.unique(np.concatenate((y_train, y_test)))) == 3 # Together they must
    assert len(X_train) + len(X_test) == 150  # Total samples
    assert len(y_train) + len(y_test) == 150  # Total samples
    assert len(X_train) == len(y_train)
    assert len(X_test) == len(y_test)
    
    # --- NEW DATA-FORMAT TESTS ---
    assert np.issubdtype(X_train.dtype, np.floating)
    assert np.issubdtype(X_test.dtype, np.floating)
    assert np.issubdtype(y_train.dtype, np.integer)
    assert np.issubdtype(y_test.dtype, np.integer)

# --- NEW TEST 4 ---
def test_data_loading_reproducible():
    """Test that random_state ensures reproducible data splitting"""
    X_train1, X_test1, y_train1, y_test1 = load_iris_data(random_state=42)
    X_train2, X_test2, y_train2, y_test2 = load_iris_data(random_state=42)
    
    assert np.array_equal(X_train1, X_train2)
    assert np.array_equal(X_test1, X_test2)
    assert np.array_equal(y_train1, y_train2)
    assert np.array_equal(y_test1, y_test2)

# --- NEW TEST 5 ---
def test_data_loading_test_size():
    """Test the test_size parameter in data loading"""
    test_fraction = 0.4
    # Total iris samples = 150
    # Note: Stratified split can cause +/- 1 differences, but with 150/50/50/50
    # and a 0.4 split, it should be exact: 0.4 * 150 = 60 test, 0.6 * 150 = 90 train
    expected_test_size = 60
    expected_train_size = 90
    
    X_train, X_test, y_train, y_test = load_iris_data(test_size=test_fraction, random_state=1)
    
    assert len(X_train) == expected_train_size
    assert len(y_train) == expected_train_size
    assert len(X_test) == expected_test_size
    assert len(y_test) == expected_test_size