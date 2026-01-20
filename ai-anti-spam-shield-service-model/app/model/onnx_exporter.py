"""
Export trained models to ONNX format for fast inference
"""

import torch
import onnx
import onnxruntime as ort
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from typing import Tuple, Dict, Optional
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class ONNXExporter:
    """
    Export PyTorch transformer models to ONNX format

    Benefits of ONNX:
    - 2-10x faster inference
    - Smaller memory footprint
    - Cross-platform compatibility
    - No PyTorch dependency at runtime
    """

    def __init__(self, model_path: str, output_dir: str = "./onnx_models"):
        self.model_path = model_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Load model and tokenizer
        logger.info(f"Loading model from {model_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.eval()

    def export(
        self,
        output_name: str = "model.onnx",
        max_length: int = 128,
        opset_version: int = 14,
        optimize: bool = True,
    ) -> str:
        """
        Export model to ONNX format

        Args:
            output_name: Output filename
            max_length: Maximum sequence length
            opset_version: ONNX opset version
            optimize: Whether to optimize the model

        Returns:
            Path to exported model
        """
        output_path = os.path.join(self.output_dir, output_name)

        # Create dummy input
        dummy_text = "This is a sample text for export"
        dummy_input = self.tokenizer(
            dummy_text,
            return_tensors="pt",
            padding="max_length",
            truncation=True,
            max_length=max_length,
        )

        # Dynamic axes for variable batch size and sequence length
        dynamic_axes = {
            "input_ids": {0: "batch_size", 1: "sequence_length"},
            "attention_mask": {0: "batch_size", 1: "sequence_length"},
            "output": {0: "batch_size"},
        }

        logger.info(f"Exporting to ONNX (opset {opset_version})...")

        # Export
        torch.onnx.export(
            self.model,
            (dummy_input["input_ids"], dummy_input["attention_mask"]),
            output_path,
            input_names=["input_ids", "attention_mask"],
            output_names=["output"],
            dynamic_axes=dynamic_axes,
            opset_version=opset_version,
            do_constant_folding=True,
        )

        # Verify export
        logger.info("Verifying ONNX model...")
        onnx_model = onnx.load(output_path)
        onnx.checker.check_model(onnx_model)

        # Optimize if requested
        if optimize:
            output_path = self._optimize_model(output_path)

        # Save tokenizer alongside
        self.tokenizer.save_pretrained(self.output_dir)

        # Verify inference
        self._verify_inference(output_path, max_length)

        logger.info(f"Model exported to {output_path}")
        return output_path

    def _optimize_model(self, model_path: str) -> str:
        """Optimize ONNX model for inference"""
        try:
            from onnxruntime.transformers import optimizer

            optimized_path = model_path.replace(".onnx", "_optimized.onnx")

            logger.info("Optimizing ONNX model...")

            optimized_model = optimizer.optimize_model(
                model_path,
                model_type="bert",
                num_heads=12,  # DistilBERT has 12 heads
                hidden_size=768,  # DistilBERT hidden size
                optimization_options=None,
            )

            optimized_model.save_model_to_file(optimized_path)

            # Compare sizes
            original_size = os.path.getsize(model_path) / (1024 * 1024)
            optimized_size = os.path.getsize(optimized_path) / (1024 * 1024)
            logger.info(f"Size: {original_size:.1f}MB -> {optimized_size:.1f}MB")

            return optimized_path
        except ImportError:
            logger.warning("onnxruntime.transformers not available, skipping optimization")
            return model_path
        except Exception as e:
            logger.warning(f"Optimization failed: {e}, using unoptimized model")
            return model_path

    def _verify_inference(self, model_path: str, max_length: int):
        """Verify ONNX model produces correct output"""
        # Create ONNX session
        session = ort.InferenceSession(model_path)

        # Test inputs
        test_texts = [
            "Hello, how are you today?",
            "URGENT: You won $1000! Click here now!",
            "Your Amazon order has shipped",
        ]

        logger.info("Verifying inference...")

        for text in test_texts:
            # Tokenize
            inputs = self.tokenizer(
                text,
                return_tensors="np",
                padding="max_length",
                truncation=True,
                max_length=max_length,
            )

            # Run inference
            onnx_output = session.run(
                None,
                {
                    "input_ids": inputs["input_ids"],
                    "attention_mask": inputs["attention_mask"],
                }
            )[0]

            # Compare with PyTorch
            with torch.no_grad():
                torch_output = self.model(
                    torch.tensor(inputs["input_ids"]),
                    torch.tensor(inputs["attention_mask"]),
                ).logits.numpy()

            # Check similarity
            diff = np.abs(onnx_output - torch_output).max()
            logger.info(f"Max diff for '{text[:30]}...': {diff:.6f}")

            if diff > 0.01:
                logger.warning("Large difference detected!")

        logger.info("Inference verification complete")

    def benchmark(self, model_path: str, num_runs: int = 100) -> Dict:
        """Benchmark ONNX vs PyTorch inference speed"""
        import time

        session = ort.InferenceSession(model_path)

        # Prepare input
        test_text = "This is a sample text for benchmarking inference speed."
        inputs = self.tokenizer(
            test_text,
            return_tensors="np",
            padding="max_length",
            truncation=True,
            max_length=128,
        )

        # Warmup
        for _ in range(10):
            session.run(None, {
                "input_ids": inputs["input_ids"],
                "attention_mask": inputs["attention_mask"],
            })

        # ONNX benchmark
        start = time.time()
        for _ in range(num_runs):
            session.run(None, {
                "input_ids": inputs["input_ids"],
                "attention_mask": inputs["attention_mask"],
            })
        onnx_time = (time.time() - start) / num_runs * 1000  # ms

        # PyTorch benchmark
        torch_inputs = {
            "input_ids": torch.tensor(inputs["input_ids"]),
            "attention_mask": torch.tensor(inputs["attention_mask"]),
        }

        # Warmup
        for _ in range(10):
            with torch.no_grad():
                self.model(**torch_inputs)

        start = time.time()
        for _ in range(num_runs):
            with torch.no_grad():
                self.model(**torch_inputs)
        pytorch_time = (time.time() - start) / num_runs * 1000  # ms

        results = {
            "onnx_ms": round(onnx_time, 2),
            "pytorch_ms": round(pytorch_time, 2),
            "speedup": round(pytorch_time / onnx_time, 2),
        }

        logger.info(f"Benchmark results: {results}")
        return results


def export_all_models():
    """Export all trained models to ONNX"""
    model_types = ["sms", "phishing"]

    for model_type in model_types:
        model_path = f"./trained_models/{model_type}/best_model"

        if not os.path.exists(model_path):
            logger.warning(f"Model not found: {model_path}")
            continue

        logger.info(f"\n{'='*50}")
        logger.info(f"Exporting {model_type} model")
        logger.info('='*50)

        exporter = ONNXExporter(
            model_path=model_path,
            output_dir=f"./onnx_models/{model_type}",
        )

        output_path = exporter.export(
            output_name=f"{model_type}_model.onnx",
            optimize=True,
        )

        # Benchmark
        benchmark = exporter.benchmark(output_path)
        logger.info(f"Speedup: {benchmark['speedup']}x")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    export_all_models()
