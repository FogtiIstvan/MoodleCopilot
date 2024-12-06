import json
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

class LanguageModule:
    def __init__(self, lang):
        
        with open(f'lang/{lang}.json') as f:
            self.lang = json.load(f)
                    
        class Question(BaseModel):
            questiontext: str = Field(description=self.lang['questiontext_desc'])
            thought1: str = Field(description=self.lang['thought'])
            score1: str = Field(description=self.lang['score'])
            thought2: str = Field(description=self.lang['thought'])
            score2: str = Field(description=self.lang['score'])
            thought3: str = Field(description=self.lang['thought'])
            score3: str = Field(description=self.lang['score'])
            thought4: str = Field(description=self.lang['thought'])
            score4: str = Field(description=self.lang['score'])
        
        class QuestionList(BaseModel):
            questions: list[Question]

        class Evaluation(BaseModel):
            feedback: str = Field(description=self.lang['feedback_sum'])
            score: int = Field(description=self.lang['score_sum'])
            
        class AtomicEvaluation(BaseModel):
            argument: str = Field(description=self.lang['argument_atomic'])
            score: bool = Field(description=self.lang['score_atomic'])
        
        self.QuestionList = QuestionList
        self.Evaluation = Evaluation
        self.AtomicEvaluation = AtomicEvaluation  
        
        self.generation_examples = self.lang['generation_examples']
        self.generate_human_prompt = self.lang['generate_human_prompt']
        
        self.eval_human_prompt = self.lang['eval_human_prompt']
        self.eval_atomic_human_prompt = self.lang['eval_atomic_human_prompt']                
        self.summaries_human_prompt = self.lang['summaries_human_prompt']
        
        self.summarise_eval_system_prompt = self.lang['summarise_eval_system_prompt']

        self.example_scheme_generator = ChatPromptTemplate.from_messages(
            [
                ("assistant", self.lang['example_scheme_generate_assistant']),
            ]
        )         

        self.example_scheme_evaluate = ChatPromptTemplate.from_messages(
            [
                ("human", self.lang['example_scheme_evaluate_human']),
                ("assistant", self.lang['example_scheme_evaluate_assistant']),
            ]
        )
                                                            
    def eval_system_prompt(self, questiontext, escaped_context):
        
        print("escaped context: ", escaped_context)
        context = ""
        if escaped_context is not None:
            context = self.lang["eval_system_prompt_context"] + str(escaped_context)
        
        questiontext = self.lang["questiontext"] + ": " + questiontext
        
        eval_system_prompt = self.lang["eval_system_prompt"] + questiontext + " " + context
                                        
        return eval_system_prompt + self.lang["evaluater_format_instructions"]
    
    def generate_system_prompt(self, prompt, escaped_context):
        
        context = ""
        if escaped_context is not None:
            context = self.lang["generator_context"] + escaped_context

        gen_system_prompt = self.lang["gen_system_prompt_1"] + prompt + self.lang["gen_system_prompt_2"]  + str(context) + self.lang["gen_system_prompt_3"] 

        print("gen_system_prompt: ", gen_system_prompt)
        return gen_system_prompt 
    
    def atomic_eval_system_prompt(self, questiontext, escaped_context=None):
        
        context = ""
        if escaped_context is not None:
            context = self.lang["eval_system_prompt_context"] + str(escaped_context)
        
        system_prompt = self.lang["eval_crit_prompt"] + " " + context
        
        system_prompt = system_prompt + self.lang["eval_format_instructions"]
        
        print("system_prompt: ", system_prompt)

        return system_prompt
                 
mintaválasz = "A C++ referenciák és a C Pointerek is lehetővé teszik a változókra való hivatkozást, azonban különböző módokon.A C++ referenciák nagyobb rugalmasságot biztosítanak, mivel lehetővé teszik a memória közvetlen manipulálását, de nagyobb a hibalehetőség is."