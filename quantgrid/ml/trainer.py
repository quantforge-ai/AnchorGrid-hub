"""
QuantGrid ML - Standardized Training Pipeline

Forces every contributor to use identical architecture settings (Rank 16, Alpha 32),
ensuring their "Lego brick" fits the "Lego castle."
"""

import os
import torch
from typing import Optional
from datasets import load_dataset
from loguru import logger

try:
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        TrainingArguments,
        BitsAndBytesConfig
    )
    from trl import SFTTrainer
    TRAINING_AVAILABLE = True
except ImportError:
    TRAINING_AVAILABLE = False
    logger.warning("Training dependencies not installed. Install with: pip install quantgrid[ml]")


class QuantGridTrainer:
    """
    Standardized Training Pipeline for QuantGrid Contributors.
    Enforces compatibility for the Hive Mind.
    
    This ensures ALL community adapters use identical LoRA settings,
    making them mergeable via linear averaging.
    """
    
    # STANDARDIZED SETTINGS (DO NOT CHANGE - Required for merging!)
    LORA_R = 16
    LORA_ALPHA = 32
    LORA_DROPOUT = 0.05
    TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj"]
    
    def __init__(self, base_model_id: str = "mistralai/Mistral-7B-v0.1"):
        if not TRAINING_AVAILABLE:
            raise ImportError(
                "Training dependencies required. Install with: pip install quantgrid[ml]"
            )
        
        self.base_model_id = base_model_id
        self.tokenizer = AutoTokenizer.from_pretrained(base_model_id)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Enforce 4-bit loading (Democratizes training to consumer GPUs)
        self.bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        
        logger.info(f"✅ QuantGrid Trainer initialized with {base_model_id}")
    
    def train(
        self,
        dataset_path: str,
        output_dir: str = "./adapter_output",
        num_epochs: int = 3,
        batch_size: int = 4,
        learning_rate: float = 2e-4
    ) -> str:
        """
        Train a LoRA adapter on a custom financial dataset.
        
        Args:
            dataset_path: Path to JSON dataset
            output_dir: Where to save the adapter
            num_epochs: Number of training epochs
            batch_size: Batch size per device
            learning_rate: Learning rate
            
        Returns:
            Path to saved adapter
        """
        logger.info(f"📉 Loading Base Model: {self.base_model_id}")
        
        # 1. Load base model with 4-bit quantization
        model = AutoModelForCausalLM.from_pretrained(
            self.base_model_id,
            quantization_config=self.bnb_config,
            device_map="auto",
            trust_remote_code=True,
        )
        model = prepare_model_for_kbit_training(model)
        
        # 2. ENFORCE STANDARD LORA CONFIG (The "Lego Connector")
        # These settings CANNOT be changed - required for merging!
        peft_config = LoraConfig(
            r=self.LORA_R,              # Rank (Must be 16)
            lora_alpha=self.LORA_ALPHA,  # Alpha (Must be 32)
            lora_dropout=self.LORA_DROPOUT,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=self.TARGET_MODULES,
        )
        
        model = get_peft_model(model, peft_config)
        model.print_trainable_parameters()
        
        # 3. Load dataset
        logger.info(f"📚 Loading Dataset: {dataset_path}")
        dataset = load_dataset("json", data_files=dataset_path, split="train")
        
        # 4. Training arguments
        args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=2,
            learning_rate=learning_rate,
            fp16=True,
            logging_steps=10,
            save_strategy="epoch",
            optim="adamw_8bit",  # Memory efficient optimizer
        )
        
        logger.info("🚀 Starting Standardized Training...")
        
        # 5. Train!
        trainer = SFTTrainer(
            model=model,
            train_dataset=dataset,
            peft_config=peft_config,
            dataset_text_field="text",  # Expects {"text": "Question... Answer..."}
            max_seq_length=2048,
            tokenizer=self.tokenizer,
            args=args,
        )
        
        trainer.train()
        
        # 6. Save
        logger.info(f"💾 Saving adapter to {output_dir}")
        trainer.save_model(output_dir)
        
        # 7. Save metadata
        metadata = {
            "base_model": self.base_model_id,
            "lora_r": self.LORA_R,
            "lora_alpha": self.LORA_ALPHA,
            "target_modules": self.TARGET_MODULES,
            "quantgrid_compatible": True,
        }
        
        import json
        with open(os.path.join(output_dir, "quantgrid_metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"✅ Training Complete! Adapter saved to {output_dir}")
        return output_dir


if __name__ == "__main__":
    # Example usage for a contributor
    trainer = QuantGridTrainer()
    trainer.train("my_sec_data.json", output_dir="./my_sec_adapter")
