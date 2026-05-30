# app/inference.py

import tensorflow as tf
import numpy as np
import shap
import warnings
warnings.filterwarnings('ignore')

class RobustScalingLayer(tf.keras.layers.Layer):
    def __init__(self, median, iqr, **kwargs):
        super().__init__(**kwargs)

        # 🔥 Handle Keras serialized numpy format
        if isinstance(median, dict) and "config" in median:
            median = median["config"]["value"]

        if isinstance(iqr, dict) and "config" in iqr:
            iqr = iqr["config"]["value"]

        # Convert to numpy float32
        self.median = np.array(median, dtype=np.float32)
        self.iqr = np.array(iqr, dtype=np.float32)

    def build(self, input_shape):
        self.median_tensor = tf.constant(self.median, dtype=tf.float32)
        self.iqr_tensor = tf.constant(self.iqr, dtype=tf.float32)

    def call(self, inputs):
        return (inputs - self.median_tensor) / (self.iqr_tensor + 1e-8)

    def get_config(self):
        config = super().get_config()
        config.update({
            "median": self.median.tolist(),
            "iqr": self.iqr.tolist(),
        })
        return config
    
mlp_model = tf.keras.models.load_model(
    "./models/mlp_model.keras",
    custom_objects={
        "RobustScalingLayer": RobustScalingLayer
    }
)

categorical_cols = ["proto", "service", "state"]

robust_features = [
    "sbytes", "dbytes",
    "stcpb", "dtcpb",
    "response_body_len",
    "sloss", "dloss"
]

standard_features = [
    "spkts", "dpkts",
    "swin", "dwin",
    "dmean",
    "ct_src_dport_ltm",
    "ct_dst_sport_ltm",
    "trans_depth",
    "ct_ftp_cmd",
    "ct_flw_http_mthd"
]

binary_features = [
    "is_ftp_login",
    "is_sm_ips_ports"
]

flow_features = [
    "dur", "rate", "sload", "dload",
    "sinpkt", "dinpkt",
    "sjit", "djit",
    "tcprtt", "synack", "ackdat"
]


def preprocess(input_json):

    x_dict = {
        "proto": np.array([input_json["proto"]], dtype=object),
        "service": np.array([input_json["service"]], dtype=object),
        "state": np.array([input_json["state"]], dtype=object),
        "attack_cat": np.array([input_json["attack_cat"]], dtype=object),

        "standard": np.array([[input_json[f] for f in standard_features]], dtype="float32"),
        "robust": np.array([[input_json[f] for f in robust_features]], dtype="float32"),
        "flow": np.array([[input_json[f] for f in flow_features]], dtype="float32"),
        "binary": np.array([[input_json[f] for f in binary_features]], dtype="float32"),
    }

    return x_dict


def predict_mlp(x_dict):
    pred = mlp_model.predict(x_dict, verbose=0)

    # If last layer is sigmoid
    return float(pred[0][0])


# SHAP Explainability Setup
# Load background data for SHAP (sample of training data for approximation)
try:
    SHAP_BACKGROUND_DATA = np.load("./models/shap_background.npy")
except:
    SHAP_BACKGROUND_DATA = None


def _get_all_features(x_dict):
    """Flatten all input features into a single array for SHAP."""
    features = []
    
    # Categorical features (proto, service, state, attack_cat)
    for key in ["proto", "service", "state", "attack_cat"]:
        if key in x_dict:
            features.append(x_dict[key][0])
    
    # Numerical features from standard, robust, flow, binary
    for key in ["standard", "robust", "flow", "binary"]:
        if key in x_dict:
            features.append(x_dict[key][0])
    
    return np.concatenate([
        x_dict.get("standard", np.array([[0]])).flatten(),
        x_dict.get("robust", np.array([[0]])).flatten(),
        x_dict.get("flow", np.array([[0]])).flatten(),
        x_dict.get("binary", np.array([[0]])).flatten()
    ])


def _create_shap_background():
    """Create a background dataset for SHAP from the saved background file."""
    if SHAP_BACKGROUND_DATA is not None:
        return SHAP_BACKGROUND_DATA
    
    # Fallback: use a small sample of zeros if no background available
    n_features = len(standard_features) + len(robust_features) + len(flow_features) + len(binary_features)
    return np.zeros((100, n_features), dtype=np.float32)


def _get_feature_names():
    """Get ordered list of all feature names for SHAP explanations."""
    return standard_features + robust_features + flow_features + binary_features


# Lazy-loaded SHAP explainer
_shap_explainer = None


def _get_shap_explainer():
    """Get or create the SHAP KernelExplainer (lazy initialization)."""
    global _shap_explainer
    
    if _shap_explainer is not None:
        return _shap_explainer
    
    # Create background data
    background = _create_shap_background()
    
    # Create a prediction wrapper function for SHAP
    def predict_fn(x):
        # x is a 2D array (samples x features)
        # Convert flat array back to dict format for the model
        n_standard = len(standard_features)
        n_robust = len(robust_features)
        n_flow = len(flow_features)
        n_binary = len(binary_features)
        
        x_dict = {
            "standard": x[:, :n_standard],
            "robust": x[:, n_standard:n_standard+n_robust],
            "flow": x[:, n_standard+n_robust:n_standard+n_robust+n_flow],
            "binary": x[:, n_standard+n_robust+n_flow:],
            # Use placeholder values for categorical (they won't be used much in linear approximation)
            "proto": np.array(["tcp"] * x.shape[0]),
            "service": np.array(["http"] * x.shape[0]),
            "state": np.array(["SF"] * x.shape[0]),
            "attack_cat": np.array(["Normal"] * x.shape[0]),
        }
        
        preds = mlp_model.predict(x_dict, verbose=0)
        return preds.flatten()
    
    # Create KernelExplainer with background data
    # Using a subset of background for faster computation
    bg_sample = background[:min(50, len(background))] if len(background) > 0 else np.zeros((10, background.shape[1]))
    _shap_explainer = shap.KernelExplainer(predict_fn, bg_sample)
    
    return _shap_explainer


def explain_mlp(x_dict, nsamples=100):
    """
    Generate SHAP explanations for an MLP prediction.
    
    This function computes SHAP (SHapley Additive exPlanations) values
    to explain the model's prediction for the given input.
    
    Parameters:
    -----------
    x_dict : dict
        Preprocessed input dictionary from preprocess() function.
        Should contain keys: 'standard', 'robust', 'flow', 'binary', 'proto', 'service', 'state', 'attack_cat'
    nsamples : int, optional
        Number of samples to use for SHAP value computation (default: 100).
        Higher values give more accurate explanations but take longer.
    
    Returns:
    --------
    dict
        A dictionary containing:
        - 'shap_values': numpy array of SHAP values for each feature
        - 'feature_names': list of feature names in order
        - 'feature_importance': dict mapping feature names to absolute mean SHAP values
        - 'prediction': the original model prediction score
        - 'base_value': the expected model output (mean of background predictions)
    
    Example:
    --------
    >>> from app.inference import preprocess, explain_mlp
    >>> flow_data = {...}  # your input data
    >>> x = preprocess(flow_data)
    >>> explanation = explain_mlp(x)
    >>> print(explanation['feature_importance'])  # Top features influencing the prediction
    """
    # Get the prediction first
    prediction = predict_mlp(x_dict)
    
    # Flatten the input features for SHAP
    x_flat = _get_all_features(x_dict).reshape(1, -1)
    
    # Get or create the explainer
    try:
        explainer = _get_shap_explainer()
        
        # Compute SHAP values using KernelExplainer
        shap_values = explainer.shap_values(x_flat, nsamples=nsamples)
        
        # Get feature names
        feature_names = _get_feature_names()
        
        # Calculate base value (expected prediction)
        base_value = explainer.expected_value
        if isinstance(base_value, (list, np.ndarray)):
            base_value = float(base_value[0]) if len(base_value) > 0 else 0.0
        else:
            base_value = float(base_value)
        
        # Calculate feature importance (mean absolute SHAP values)
        shap_array = np.array(shap_values[0]) if isinstance(shap_values, list) else shap_values[0]
        feature_importance = {
            name: float(abs(shap_array[i])) 
            for i, name in enumerate(feature_names)
        }
        
        # Sort by importance
        feature_importance = dict(
            sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        )
        
        return {
            "shap_values": shap_array.tolist(),
            "feature_names": feature_names,
            "feature_importance": feature_importance,
            "prediction": prediction,
            "base_value": base_value
        }
        
    except Exception as e:
        # If SHAP computation fails, return a fallback with error info
        return {
            "error": str(e),
            "prediction": prediction,
            "shap_values": None,
            "feature_names": _get_feature_names(),
            "feature_importance": {},
            "base_value": None
        }