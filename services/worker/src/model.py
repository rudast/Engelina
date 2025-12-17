from typing import Any, Dict, List, Optional

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

from src.settings import Settings, get_settings
from src.utils import clamp_history


class AIWorkerModel:
    """
    Loads and holds the LLM + tokenizer once per process.
    Provides two generation modes:
      - reply: natural conversation text
      - feedback_raw: expects JSON text (may still fail -> parsed in service layer)
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.tokenizer = self._load_tokenizer()
        self.model = self._load_model()
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        if getattr(self.model.config, "pad_token_id", None) is None:
            self.model.config.pad_token_id = self.tokenizer.pad_token_id
    
    def _load_tokenizer(self):
        tok = AutoTokenizer.from_pretrained(
            self.settings.MODEL_ID,
            use_fast=True,
        )
        
        if tok.pad_token is None:
            tok.pad_token = tok.eos_token
        return tok

    def _load_model(self):
        model_id = self.settings.MODEL_ID

        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

        if self.settings.LOAD_IN_4BIT:
            if BitsAndBytesConfig is None:
                raise RuntimeError(
                    "BitsAndBytesConfig is not available."
                )
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=dtype,
            )

            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                quantization_config=bnb_config,
                device_map="auto",
                torch_dtype=dtype,
            )
            return model
        
    def _build_chat_text(self, messages: List[Dict[str, str]]):
        """
        Convert chat messages into model specific chat template text.
        """
        return self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        
    def _encode(self, chat_text: str) -> Dict[str, torch.Tensor]:
        """
        Encode text to tensors
        """
        inputs = self.tokenizer(chat_text, return_tensors="pt")
        return {k: v.to(self.model.device) for k, v in inputs.items()}
    @torch.no_grad()
    def _generate(
        self,
        inputs: Dict[str, torch.Tensor],
        *,
        max_new_tokens: int,
        temperature: float,
        top_p: float,
    ) -> torch.Tensor:
        """
        Call model.generate with given sampling parameters.
        """
        return self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            pad_token_id=self.tokenizer.pad_token_id,
        )
        
    def _decode_new_tokens(self, output_ids: torch.Tensor, input_len: int) -> str:
        """
        Decode only new tokens
        """
        gen_ids = output_ids[0][input_len:]
        return self.tokenizer.decode(
            gen_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True,
        ).strip()

    def generate_reply(
            self, 
            *, 
            system_prompt: str, 
            history: list[dict], 
            user_message: str
        ) -> str:
        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        chat_text = self._build_chat_text(messages)
        inputs = self._encode(chat_text)

        input_len = inputs["input_ids"].shape[1]
        out_ids = self._generate(
            inputs,
            max_new_tokens=self.settings.MAX_NEW_TOKENS_REPLY,
            temperature=self.settings.TEMPERATURE_REPLY,
            top_p=self.settings.TOP_P,
        )
        return self._decode_new_tokens(out_ids, input_len)


    def generate_feedback_raw(
        self,
        *,
        system_prompt: str,
        user_message: str,
    ) -> str:
        """
        Generate feedback output as raw text (expected to be JSON).
        """
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        chat_text = self._build_chat_text(messages)
        inputs = self._encode(chat_text)

        input_len = inputs["input_ids"].shape[1]
        out_ids = self._generate(
            inputs,
            max_new_tokens=self.settings.MAX_NEW_TOKENS_FEEDBACK,
            temperature=self.settings.TEMPERATURE_FEEDBACK,
            top_p=self.settings.TOP_P,
        )
        return self._decode_new_tokens(out_ids, input_len)