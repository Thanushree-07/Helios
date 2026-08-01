class LlamaProvider:
    def generate(self,prompt:str)->str:
        return f"[LLama] You asked:{prompt}"