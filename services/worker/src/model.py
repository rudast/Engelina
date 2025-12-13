# ai_worker/model.py

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)

HF_MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"


class AIWorkerModel:
    """
    Обёртка над Qwen2.5-7B-Instruct.
    Загружается в 4-битном квантовании под 8 ГБ VRAM.
    """

    def __init__(
        self,
        model_id: str = HF_MODEL_ID,
        max_new_tokens: int = 4096,
        reply_temperature: float = 0.6,
        feedback_temperature: float = 0.2,
        top_p: float = 0.9,
        device: str | None = None,
    ):
        self.model_id = model_id
        self.max_new_tokens = max_new_tokens
        self.reply_temperature = reply_temperature
        self.feedback_temperature = feedback_temperature
        self.top_p = top_p

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        self.tokenizer = self._load_tokenizer()
        self.model = self._load_model_4bit()

    def _load_tokenizer(self):
        tokenizer = AutoTokenizer.from_pretrained(
            self.model_id,
            use_fast=True,
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        return tokenizer

    def _load_model_4bit(self):
        """
        Пытаемся загрузить модель в 4-бит.
        Если не вышло (нет bitsandbytes / проблемы с CUDA) — падаем в fp16.
        """
        try:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
            )

            model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                quantization_config=bnb_config,
                device_map="auto",
                torch_dtype=torch.bfloat16,
            )

        except Exception as e:
            print("⚠️ Не удалось включить 4-битный режим, fallback на fp16. Ошибка:")
            print(e)

            model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                device_map="auto",
                torch_dtype=torch.float16,
            )

        model.config.pad_token_id = self.tokenizer.pad_token_id
        return model


    def generate_reply(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
    ) -> str:
        """
        messages — список в стиле:
        [
            {"role": "user", "content": "привет"},
            {"role": "assistant", "content": "привет! чем помочь?"}
        ]

        system_prompt — необязательное системное сообщение (роль "system").
        """

        chat_messages = [{"role": "system", "content": system_prompt}]
        chat_messages.extend(messages)

        text = self.tokenizer.apply_chat_template(
            chat_messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
        ).to(self.model.device)

        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                temperature=self.reply_temperature,
                top_p=self.top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
            )

        generated_ids = output_ids[0][inputs["input_ids"].shape[1]:]
        answer = self.tokenizer.decode(
            generated_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True,
        )
        return answer.strip()
    

    def generate_feedback(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
    ) -> str:

        chat_messages = [{"role": "system", "content": system_prompt}]
        chat_messages.extend(messages)
        text = self.tokenizer.apply_chat_template(
            chat_messages,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = self.tokenizer(
            text,
            return_tensors="pt"
        ).to(self.model.device)

        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                temperature=self.feedback_temperature,
                top_p=self.top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
            )
        generated_ids = output_ids[0][inputs["input_ids"].shape[1]:]
        answer = self.tokenizer.decode(
            generated_ids,
            skip_special_tokens=True,
        )
        return answer.strip
        
